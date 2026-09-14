#!/usr/bin/env python3
"""Verify a ClawMetry self-hosted server image the way a stranger would.

    # What the release pipeline runs against a published image, per architecture:
    python3 scripts/verify_selfhosted_image.py --anonymous \\
        --image ghcr.io/vivekchand/clawmetry@sha256:<digest>

    # What the pull_request leg runs against an image built from the branch:
    python3 scripts/verify_selfhosted_image.py --skip-signature \\
        --image clawmetry-selfhosted:pr

Checks, in order, each failing with the reason named:

1. ``--anonymous``: the registry hands out an anonymous pull token and serves
   the manifest with it, then ``docker pull`` succeeds with an EMPTY Docker
   config, so no stored login can make a private package look public. A new
   GHCR package is private until its owner flips it once; this is the check
   that notices.
2. The pulled image is for the architecture this machine runs.
3. Unless ``--skip-signature``: ``cosign verify`` against the publishing
   workflow's identity, and ``cosign verify-attestation --type spdxjson`` on the
   platform manifest (the SBOM is attested per platform).
4. No Pro plugin inside: no ``clawmetry-pro`` distribution, no ``clawmetry_pro``
   module. The public image carries only the open-source package.
5. Persistence, from OUTSIDE the container: start it on a fresh volume, send a
   non-sensitive event through the node ingest API, restart the container, and
   confirm the audit export still returns the event, the fleet page still
   lists the node, and the export still refuses a caller with no credentials.

Every request in step 5 reaches the container through a published port, so the
server sees a non-loopback address. That is deliberate: it is exactly what an
operator's request looks like, and it is the condition under which the admin
APIs used to answer 401 regardless of credentials.

Needs ``docker``; ``cosign`` unless ``--skip-signature``. Standard library only.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import platform
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

DEFAULT_IDENTITY = (
    "https://github.com/vivekchand/clawmetry/.github/workflows/"
    "container-image.yml@refs/heads/main"
)
OIDC_ISSUER = "https://token.actions.githubusercontent.com"
PACKAGE_SETTINGS = (
    "https://github.com/users/vivekchand/packages/container/clawmetry/settings"
)
USER_AGENT = "clawmetry-image-verifier/1"

_INDEX_TYPES = (
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
)
_ARCH = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}


class VerifyError(Exception):
    pass


def _say(msg: str) -> None:
    print(f"==> {msg}", flush=True)


def host_arch() -> str:
    return _ARCH.get(platform.machine().lower(), platform.machine().lower())


# ── image references ────────────────────────────────────────────────────────


def split_ref(ref: str) -> tuple:
    """``registry/repo[:tag][@digest]`` -> (registry, repo, tag, digest)."""
    digest = ""
    if "@" in ref:
        ref, digest = ref.split("@", 1)
    first, _, rest = ref.partition("/")
    if not rest or ("." not in first and ":" not in first and first != "localhost"):
        return "", ref, "", digest
    repo, tag = rest, ""
    if ":" in rest.rsplit("/", 1)[-1]:
        repo, tag = rest.rsplit(":", 1)
    return first, repo, tag, digest


def classify_pull_failure(output: str) -> str:
    """Turn `docker pull` stderr into the reason an operator can act on."""
    low = (output or "").lower()
    if any(s in low for s in ("denied", "unauthorized", "authentication required")):
        return (
            "the registry refused an anonymous pull. If the package was just "
            f"created it is still private: make it public at {PACKAGE_SETTINGS}"
        )
    if "no matching manifest" in low:
        return f"the image has no manifest for {host_arch()}"
    if "manifest unknown" in low or "not found" in low:
        return "no image exists at that reference (wrong tag or digest?)"
    return "docker pull failed: " + (output or "").strip()[-400:]


def anonymous_env() -> dict:
    """Environment whose docker/cosign calls carry no registry credentials."""
    env = dict(os.environ)
    cfg = tempfile.mkdtemp(prefix="cm-anon-docker-")
    with open(os.path.join(cfg, "config.json"), "w", encoding="utf-8") as fh:
        fh.write("{}")
    env["DOCKER_CONFIG"] = cfg
    for key in (
        "REGISTRY_AUTH_FILE",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "COSIGN_PASSWORD",
        "SIGSTORE_ID_TOKEN",
        "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
        "ACTIONS_ID_TOKEN_REQUEST_URL",
    ):
        env.pop(key, None)
    return env


def _get(url: str, headers=None, timeout: int = 20) -> tuple:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def probe_anonymous(ref: str) -> dict:
    """Fetch the manifest with an anonymous token; returns the parsed manifest."""
    registry, repo, tag, digest = split_ref(ref)
    if registry != "ghcr.io":
        raise VerifyError(f"anonymous probe only knows ghcr.io, got {registry or 'no registry'}")
    status, body = _get(
        f"https://ghcr.io/token?scope=repository:{repo}:pull&service=ghcr.io"
    )
    token = ""
    if status == 200:
        try:
            token = json.loads(body).get("token", "")
        except ValueError:
            token = ""
    if not token:
        raise VerifyError(
            f"ghcr.io would not issue an anonymous pull token for {repo} "
            f"(HTTP {status}). A private package looks exactly like this: make it "
            f"public at {PACKAGE_SETTINGS}"
        )
    status, body = _get(
        f"https://ghcr.io/v2/{repo}/manifests/{digest or tag or 'latest'}",
        headers={"Authorization": f"Bearer {token}", "Accept": ", ".join(_INDEX_TYPES)},
    )
    if status != 200:
        raise VerifyError(
            f"anonymous manifest fetch for {ref} answered HTTP {status}: "
            + body[:200].decode("utf-8", "replace")
        )
    return json.loads(body)


def platform_digest(manifest: dict, arch: str) -> str:
    """The per-platform manifest digest inside an image index, or ''."""
    for entry in manifest.get("manifests") or []:
        plat = entry.get("platform") or {}
        if plat.get("os") == "linux" and plat.get("architecture") == arch:
            return entry.get("digest", "")
    return ""


# ── subprocess plumbing ─────────────────────────────────────────────────────


def _run(cmd: list, env=None, check: bool = True, timeout: int = 900):
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout)
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[-800:]
        raise VerifyError(f"`{' '.join(cmd[:3])} ...` exited {proc.returncode}: {detail}")
    return proc


# ── HTTP checks against a running server (unit-tested without docker) ──────


def _http(method: str, url: str, headers=None, body=None, timeout: int = 15) -> tuple:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    hdrs = {"User-Agent": USER_AGENT, **(headers or {})}
    if data is not None:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as exc:
        return 0, str(exc)


def _basic(user: str, password: str) -> dict:
    raw = f"{user}:{password}".encode("utf-8")
    return {"Authorization": "Basic " + base64.b64encode(raw).decode("ascii")}


def wait_ready(base: str, admin: tuple, timeout: float = 180.0) -> None:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        status, text = _http("GET", f"{base}/selfhosted", headers=_basic(*admin), timeout=5)
        if status == 200:
            return
        last = f"HTTP {status} {text[:120]}"
        time.sleep(2)
    raise VerifyError(f"server at {base} never became ready ({last})")


def send_event(base: str, token: str, node_id: str, event_id: str) -> None:
    key = {"X-Api-Key": token}
    status, text = _http(
        "POST",
        f"{base}/ingest/heartbeat",
        headers=key,
        body={"node_id": node_id, "platform": "image-verification", "version": "verify"},
    )
    if status != 200:
        raise VerifyError(f"heartbeat refused: HTTP {status} {text[:200]}")
    event = {
        "id": event_id,
        "event_type": "image_verification",
        "agent_type": "verification",
        "ts": datetime.now(timezone.utc).isoformat(),
        "data": {"note": "non-sensitive event sent by verify_selfhosted_image.py"},
    }
    status, text = _http(
        "POST", f"{base}/ingest/events", headers=key,
        body={"node_id": node_id, "events": [event]},
    )
    if status != 200 or '"ok":true' not in text.replace(" ", ""):
        raise VerifyError(f"event ingest refused: HTTP {status} {text[:200]}")


def assert_persisted(base: str, admin: tuple, node_id: str, event_id: str) -> None:
    status, text = _http("GET", f"{base}/api/export/events", headers=_basic(*admin))
    if status != 200:
        raise VerifyError(
            f"audit export answered HTTP {status} to valid admin credentials: {text[:200]}"
        )
    ids = set()
    for line in text.splitlines():
        try:
            ids.add(json.loads(line).get("id"))
        except ValueError:
            continue
    if event_id not in ids:
        raise VerifyError(f"event {event_id} is not in the audit export after the restart")

    status, text = _http("GET", f"{base}/api/selfhosted/status", headers=_basic(*admin))
    if status != 200:
        raise VerifyError(f"status answered HTTP {status} to valid admin credentials")
    if int((json.loads(text).get("counts") or {}).get("events") or 0) < 1:
        raise VerifyError("status reports no stored events after the restart")

    status, text = _http("GET", f"{base}/selfhosted", headers=_basic(*admin))
    if status != 200 or node_id not in text:
        raise VerifyError(f"fleet page does not list node {node_id} (HTTP {status})")

    status, _ = _http("GET", f"{base}/api/export/events")
    if status not in (401, 403):
        raise VerifyError(f"audit export answered HTTP {status} to a caller with no credentials")


# ── docker-backed checks ────────────────────────────────────────────────────


def check_arch(image: str, want: str, env: dict) -> None:
    got = _run(["docker", "image", "inspect", "--format", "{{.Architecture}}", image], env=env)
    got_arch = got.stdout.strip()
    if got_arch != want:
        raise VerifyError(f"image architecture is {got_arch!r}, expected {want!r}")


_NO_PRO = (
    "import importlib.metadata as m, importlib.util as u, json, sys\n"
    "names = sorted({(d.metadata['Name'] or '').lower() for d in m.distributions()})\n"
    "pro = [n for n in names if n.replace('_', '-').startswith('clawmetry-pro')]\n"
    "mod = u.find_spec('clawmetry_pro') is not None\n"
    "print(json.dumps({'clawmetry': m.version('clawmetry'), 'pro_dists': pro, 'pro_module': mod}))\n"
    "sys.exit(1 if pro or mod else 0)\n"
)


def check_contents(image: str, expect_version: str, env: dict) -> None:
    proc = _run(
        ["docker", "run", "--rm", "--entrypoint", "python3", image, "-c", _NO_PRO],
        env=env, check=False, timeout=300,
    )
    try:
        report = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise VerifyError(f"could not inspect image contents: {proc.stderr.strip()[-400:]}")
    if proc.returncode != 0:
        raise VerifyError(f"the image contains the Pro plugin: {report}")
    if expect_version and report.get("clawmetry") != expect_version:
        raise VerifyError(
            f"image carries clawmetry {report.get('clawmetry')}, expected {expect_version}"
        )
    _say(f"contents ok: clawmetry {report.get('clawmetry')}, no Pro plugin")


def check_persistence(image: str, env: dict, timeout: float) -> None:
    suffix = secrets.token_hex(6)
    name = volume = f"cm-image-verify-{suffix}"
    token = f"cm_verify_{secrets.token_hex(16)}"
    admin = ("verify-admin", secrets.token_hex(16))
    node_id = f"image-verify-node-{suffix}"
    event_id = f"image-verify-event-{suffix}"
    ok = False
    try:
        _run(["docker", "volume", "create", volume], env=env)
        _run(
            [
                "docker", "run", "-d", "--name", name,
                "-p", "127.0.0.1::8900",
                "-e", "SELF_HOSTED=true",
                "-e", f"CLAWMETRY_API_TOKENS={token}",
                "-e", f"CLAWMETRY_ADMIN_USER={admin[0]}",
                "-e", f"CLAWMETRY_ADMIN_PASSWORD={admin[1]}",
                "-v", f"{volume}:/root/.clawmetry",
                image,
            ],
            env=env,
        )
        mapped = _run(["docker", "port", name, "8900/tcp"], env=env).stdout.split()[0]
        base = "http://127.0.0.1:" + mapped.rsplit(":", 1)[1]
        wait_ready(base, admin, timeout)
        send_event(base, token, node_id, event_id)
        _say("event accepted; restarting the container")
        _run(["docker", "restart", name], env=env)
        mapped = _run(["docker", "port", name, "8900/tcp"], env=env).stdout.split()[0]
        base = "http://127.0.0.1:" + mapped.rsplit(":", 1)[1]
        wait_ready(base, admin, timeout)
        assert_persisted(base, admin, node_id, event_id)
        ok = True
        _say("persistence ok: event and node survived a restart; export refuses no credentials")
    finally:
        if not ok:
            logs = _run(["docker", "logs", "--tail", "80", name], env=env, check=False)
            print((logs.stdout or "") + (logs.stderr or ""), file=sys.stderr)
        _run(["docker", "rm", "-f", name], env=env, check=False)
        _run(["docker", "volume", "rm", "-f", volume], env=env, check=False)


def check_signature(image: str, identity: str, arch: str, manifest: dict, env: dict) -> None:
    if not shutil.which("cosign"):
        raise VerifyError("cosign is not installed; pass --skip-signature only for an unpublished build")
    base = ["--certificate-identity", identity, "--certificate-oidc-issuer", OIDC_ISSUER]
    _run(["cosign", "verify", *base, image], env=env)
    _say("signature ok")
    registry, repo, _, _ = split_ref(image)
    pdigest = platform_digest(manifest, arch) if manifest else ""
    if not pdigest:
        raise VerifyError(f"no linux/{arch} manifest in the image index, so no SBOM to verify")
    _run(
        ["cosign", "verify-attestation", "--type", "spdxjson", *base,
         f"{registry}/{repo}@{pdigest}"],
        env=env,
    )
    _say(f"SBOM attestation ok for linux/{arch}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--image", required=True)
    parser.add_argument("--anonymous", action="store_true",
                        help="probe the registry and pull with no credentials")
    parser.add_argument("--skip-signature", action="store_true",
                        help="for an unpublished build: nothing to verify against")
    parser.add_argument("--expect-arch", default=host_arch())
    parser.add_argument("--expect-version", default="")
    parser.add_argument("--identity", default=DEFAULT_IDENTITY,
                        help="certificate identity the signature must carry")
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args(argv)

    env = anonymous_env() if args.anonymous else dict(os.environ)
    try:
        if not shutil.which("docker"):
            raise VerifyError("docker is not installed")
        manifest = {}
        if args.anonymous:
            _say(f"anonymous registry probe: {args.image}")
            manifest = probe_anonymous(args.image)
            _say("docker pull with an empty Docker config")
            pulled = _run(["docker", "pull", args.image], env=env, check=False)
            if pulled.returncode != 0:
                raise VerifyError(classify_pull_failure(pulled.stderr + pulled.stdout))
        check_arch(args.image, args.expect_arch, env)
        _say(f"architecture ok: {args.expect_arch}")
        if not args.skip_signature:
            if not manifest:
                manifest = probe_anonymous(args.image)
            check_signature(args.image, args.identity, args.expect_arch, manifest, env)
        check_contents(args.image, args.expect_version, env)
        check_persistence(args.image, env, args.timeout)
    except (VerifyError, subprocess.TimeoutExpired) as exc:
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::error title=Self-hosted image verification failed::{exc}")
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: {args.image}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
