"""The self-hosted server image is published signed, verified from outside, and pinned by digest.

Refs vivekchand/clawmetry#5948. Before this, deploy/self-hosted/docker-compose.yml
built the image from a source checkout: there was nothing to pull, nothing
signed, no SBOM, and no way to tie a running container to a release.

The publishing itself can only run on a release, so these tests hold the
WIRING in place: that is how the desktop-artifacts dispatch broke silently
once (an HTTP 403 swallowed by a non-blocking step). The image-level behaviour
is exercised for real by the pull_request leg of container-image.yml, which
builds the branch image on amd64 and arm64 and runs
scripts/verify_selfhosted_image.py against it; the HTTP half of that script is
exercised against a live server in tests/test_selfhosted_container_auth.py.

Declared criteria (Factory requirement "Self-Hosted Server Image: Signed,
Pullable, Verified After Release"):

AC-OBS-SHI-001.1 -- release dispatches the image build after the PyPI upload;
  both architectures, from the published wheel, provenance checked first:
  ``test_release_dispatches_image_after_pypi_upload``,
  ``test_publish_builds_both_architectures_from_the_published_wheel``.
AC-OBS-SHI-001.2 -- keyless signature, per-platform SBOM attestation, build
  provenance: ``test_publish_signs_and_attests``.
AC-OBS-SHI-001.3 -- only the open-source wheel, never the Pro plugin:
  ``test_image_installs_only_the_published_wheel``.
AC-OBS-SHI-002.1 -- anonymous pull per architecture, failing with the reason:
  ``test_verify_job_pulls_with_no_credentials_on_each_architecture``,
  ``test_anonymous_environment_carries_no_registry_credentials``,
  ``test_a_refused_pull_names_the_private_package``.
AC-OBS-SHI-002.3 -- the pull request leg builds and checks the branch image:
  ``test_pull_request_leg_builds_and_verifies_the_branch_image``.
AC-OBS-SHI-003.1 -- digest pin only after verification, never a bare tag:
  ``test_pin_runs_only_after_verification``,
  ``test_pin_replaces_the_source_build_with_version_and_digest``,
  ``test_check_rejects_a_tag_only_or_build_shadowed_image``.
AC-OBS-SHI-003.2 -- the guide says how to verify, update, roll back, back up,
  what auth really is, and what is not available:
  ``test_self_hosting_guide_covers_verification_operations_and_limits``.
"""
from __future__ import annotations

import importlib.util
import os
import re

import pytest
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS = os.path.join(REPO_ROOT, ".github", "workflows")
SELF_HOSTED = os.path.join(REPO_ROOT, "deploy", "self-hosted")
DIGEST = "sha256:" + "ab" * 32


def _load_script(name: str):
    path = os.path.join(REPO_ROOT, "scripts", f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pin_mod = _load_script("pin_selfhosted_compose")
verify_mod = _load_script("verify_selfhosted_image")


def _read(*parts: str) -> str:
    with open(os.path.join(REPO_ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def _workflow(name: str) -> dict:
    return yaml.safe_load(_read(".github", "workflows", name))


@pytest.fixture(scope="module")
def image_wf() -> dict:
    return _workflow("container-image.yml")


def _steps(job: dict) -> list:
    return job.get("steps") or []


def _index(steps: list, predicate) -> int:
    for i, step in enumerate(steps):
        if predicate(step):
            return i
    return -1


def _uses(step: dict, action: str) -> bool:
    return str(step.get("uses", "")).startswith(action + "@")


def _runs(step: dict, needle: str) -> bool:
    return needle in str(step.get("run", ""))


def _matrix_arches(job: dict) -> dict:
    include = (job.get("strategy") or {}).get("matrix", {}).get("include") or []
    return {row["arch"]: row["runner"] for row in include}


# ── publish ─────────────────────────────────────────────────────────────────


def test_release_dispatches_image_after_pypi_upload() -> None:
    steps = _steps(_workflow("release-on-merge.yml")["jobs"]["release"])
    upload = _index(steps, lambda s: s.get("name") == "Publish to PyPI")
    dispatch = _index(steps, lambda s: _runs(s, "gh workflow run container-image.yml"))
    assert upload >= 0, "release-on-merge.yml lost its PyPI upload step; update this guard"
    assert dispatch > upload, (
        "release-on-merge.yml must dispatch container-image.yml AFTER the PyPI "
        "upload: the image is built from the published wheel, and a tag pushed "
        "with GITHUB_TOKEN never triggers another workflow on its own."
    )
    assert re.search(r"container-image\.yml[\s\S]*?-f version=", steps[dispatch]["run"]), (
        "the dispatch must pass the version it just published"
    )


def test_publish_builds_both_architectures_from_the_published_wheel(image_wf) -> None:
    job = image_wf["jobs"]["publish"]
    steps = _steps(job)
    build = _index(steps, lambda s: _uses(s, "docker/build-push-action"))
    download = _index(steps, lambda s: _runs(s, "pip download") and _runs(s, "clawmetry=="))
    provenance = _index(steps, lambda s: _runs(s, "gh attestation verify"))
    assert build >= 0, "publish job no longer builds with docker/build-push-action"
    assert 0 <= download < provenance < build, (
        "the image must be built from the wheel PyPI serves, and only after that "
        "wheel's build provenance verified"
    )
    with_ = steps[build]["with"]
    platforms = {p.strip() for p in str(with_["platforms"]).split(",")}
    assert {"linux/amd64", "linux/arm64"} <= platforms
    assert with_["push"] is True
    assert with_["context"] == "deploy/self-hosted"
    assert with_["file"] == "deploy/self-hosted/Dockerfile.release"
    assert "ghcr.io/vivekchand/clawmetry" == image_wf["env"]["IMAGE"]
    trigger = image_wf.get("on") or image_wf.get(True)
    assert "version" in trigger["workflow_dispatch"]["inputs"]


def test_publish_signs_and_attests(image_wf) -> None:
    job = image_wf["jobs"]["publish"]
    steps = _steps(job)
    perms = job.get("permissions") or {}
    assert perms.get("id-token") == "write", "keyless signing needs the OIDC token"
    assert perms.get("packages") == "write"
    assert perms.get("attestations") == "write"
    sign = _index(steps, lambda s: re.search(r"cosign sign --yes --recursive \"\$\{IMAGE\}@\$\{DIGEST\}\"", str(s.get("run", ""))))
    assert sign >= 0, "the index and every platform manifest must be signed by digest"
    sbom = _index(steps, lambda s: _runs(s, "cosign attest --yes --type spdxjson"))
    assert sbom > sign, "an SPDX SBOM must be attested to each platform digest"
    assert "amd64" in steps[sbom]["run"] and "arm64" in steps[sbom]["run"]
    prov = _index(steps, lambda s: _uses(s, "actions/attest-build-provenance"))
    assert prov >= 0
    assert steps[prov]["with"].get("push-to-registry") is True
    assert "steps.build.outputs.digest" in str(steps[prov]["with"].get("subject-digest"))


def test_image_installs_only_the_published_wheel() -> None:
    text = _read("deploy", "self-hosted", "Dockerfile.release")
    code = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    copies = [ln for ln in code if ln.split()[0].upper() in ("COPY", "ADD")]
    assert copies == ["COPY dist/ /tmp/dist/"], (
        f"the release image may copy only the wheel directory, found {copies}: "
        "copying repo source would ship something other than the published artifact"
    )
    body = "\n".join(code).lower()
    for forbidden in ("clawmetry_pro", "clawmetry-pro", "wheels/", "license/download"):
        assert forbidden not in body, f"Dockerfile.release references {forbidden!r}"
    assert 'pip install --no-cache-dir "$1[otel]"' in text
    assert "CLAWMETRY_AUTO_UPDATE=0" in text, (
        "a signed image must not pip-install a different version into itself"
    )
    assert "clawmetry_pro" in verify_mod._NO_PRO, (
        "verify_selfhosted_image.py must fail on a Pro module inside the image"
    )


# ── verify ──────────────────────────────────────────────────────────────────


def test_verify_job_pulls_with_no_credentials_on_each_architecture(image_wf) -> None:
    job = image_wf["jobs"]["verify"]
    assert job["needs"] == "publish"
    assert job.get("permissions") == {"contents": "read"}, (
        "the verify job must hold no package scope: it checks what a stranger sees"
    )
    assert not any(_uses(s, "docker/login-action") for s in _steps(job))
    arches = _matrix_arches(job)
    assert set(arches) == {"amd64", "arm64"}
    assert "arm" in arches["arm64"], "arm64 must run on a native arm runner"
    run = next(s["run"] for s in _steps(job) if _runs(s, "verify_selfhosted_image.py"))
    for flag in ("--anonymous", '--image "${IMAGE}@${DIGEST}"', "--expect-arch", "--expect-version"):
        assert flag in run
    assert "--skip-signature" not in run


def test_anonymous_environment_carries_no_registry_credentials(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghs_should_not_leak")
    monkeypatch.setenv("DOCKER_CONFIG", "/home/runner/.docker")
    env = verify_mod.anonymous_env()
    assert "GITHUB_TOKEN" not in env
    assert env["DOCKER_CONFIG"] != "/home/runner/.docker"
    with open(os.path.join(env["DOCKER_CONFIG"], "config.json"), encoding="utf-8") as fh:
        assert fh.read().strip() == "{}"


def test_a_refused_pull_names_the_private_package() -> None:
    msg = verify_mod.classify_pull_failure(
        "Error response from daemon: denied: requested access to the resource is denied"
    )
    assert "public" in msg and "packages/container/clawmetry" in msg
    assert "wrong tag or digest" in verify_mod.classify_pull_failure("manifest unknown")
    assert verify_mod.split_ref(f"ghcr.io/vivekchand/clawmetry:1.2.3@{DIGEST}") == (
        "ghcr.io", "vivekchand/clawmetry", "1.2.3", DIGEST,
    )
    index = {"manifests": [
        {"digest": "sha256:a", "platform": {"os": "linux", "architecture": "amd64"}},
        {"digest": "sha256:b", "platform": {"os": "linux", "architecture": "arm64"}},
    ]}
    assert verify_mod.platform_digest(index, "arm64") == "sha256:b"


def test_pull_request_leg_builds_and_verifies_the_branch_image(image_wf) -> None:
    trigger = image_wf.get("on") or image_wf.get(True)
    paths = set(trigger["pull_request"]["paths"])
    for needed in (
        "deploy/self-hosted/**",
        "scripts/verify_selfhosted_image.py",
        ".github/workflows/container-image.yml",
    ):
        assert needed in paths, f"a change to {needed} must rebuild and re-verify the image"
    job = image_wf["jobs"]["pr-image"]
    assert set(_matrix_arches(job)) == {"amd64", "arm64"}
    steps = _steps(job)
    wheel = _index(steps, lambda s: _runs(s, "python3 -m build --wheel"))
    build = _index(steps, lambda s: _runs(s, "Dockerfile.release"))
    verify = _index(steps, lambda s: _runs(s, "verify_selfhosted_image.py"))
    assert 0 <= wheel < build < verify
    assert "--skip-signature" in steps[verify]["run"]
    assert "--anonymous" not in steps[verify]["run"]


# ── pin ─────────────────────────────────────────────────────────────────────


def test_pin_runs_only_after_verification(image_wf) -> None:
    job = image_wf["jobs"]["pin"]
    assert set(job["needs"]) == {"publish", "verify"}
    run = next(s["run"] for s in _steps(job) if _runs(s, "pin_selfhosted_compose.py"))
    assert run.index("pin_selfhosted_compose.py pin") < run.index("pin_selfhosted_compose.py check")
    assert "factory.8090.ai/project/" in run, "the pin pull request must cite its product record"


def test_pin_replaces_the_source_build_with_version_and_digest() -> None:
    original = _read("deploy", "self-hosted", "docker-compose.yml")
    pinned = pin_mod.pin(original, "0.12.900", DIGEST)
    service = yaml.safe_load(pinned)["services"]["clawmetry"]
    before = yaml.safe_load(original)["services"]["clawmetry"]
    assert service["image"] == f"ghcr.io/vivekchand/clawmetry:0.12.900@{DIGEST}"
    assert "build" not in service
    assert {k: v for k, v in service.items() if k != "image"} == {
        k: v for k, v in before.items() if k not in ("image", "build")
    }, "pinning must change the image and nothing else about the service"
    assert pinned.count("\n#") == original.count("\n#"), "operator comments must survive"
    assert pin_mod.check(pinned) == []

    repinned = pin_mod.pin(pinned, "0.12.901", "sha256:" + "cd" * 32)
    assert yaml.safe_load(repinned)["services"]["clawmetry"]["image"].endswith(
        "0.12.901@sha256:" + "cd" * 32
    )
    assert repinned.count("image:") == 1

    with pytest.raises(pin_mod.PinError):
        pin_mod.pin(original, "0.12.900", "sha256:short")
    with pytest.raises(pin_mod.PinError):
        pin_mod.pin(original, "latest", DIGEST)


def test_check_rejects_a_tag_only_or_build_shadowed_image() -> None:
    current = _read("deploy", "self-hosted", "docker-compose.yml")
    assert pin_mod.check(current) == [], "the shipped Compose file must pass its own check"
    tag_only = current.replace(
        "image: clawmetry-selfhosted:latest", "image: ghcr.io/vivekchand/clawmetry:latest"
    )
    problems = pin_mod.check(tag_only)
    assert any("digest" in p for p in problems)
    assert any("build" in p for p in problems), (
        "a published image next to a build: block would silently fall back to "
        "an unsigned source build"
    )
    assert pin_mod.main(["--compose", os.path.join(SELF_HOSTED, "docker-compose.yml"), "check"]) == 0


# ── documentation ───────────────────────────────────────────────────────────


def _section(md: str, heading: str) -> str:
    start = md.index(heading)
    nxt = md.find("\n## ", start + len(heading))
    return md[start: nxt if nxt != -1 else len(md)]


def test_self_hosting_guide_covers_verification_operations_and_limits() -> None:
    md = _read("docs", "self-hosting.md")
    verify = _section(md, "## Check the image before you run it")
    for needle in (
        "cosign verify ",
        "cosign verify-attestation --type spdxjson",
        "container-image.yml@refs/heads/main",
        "gh attestation verify",
        "scripts/verify_selfhosted_image.py --anonymous",
    ):
        assert needle in verify, f"verification section is missing {needle!r}"
    ops = _section(md, "## Update and roll back")
    assert "@sha256:" in ops and "roll back" in ops.lower()
    backup = _section(md, "## Back up and restore")
    assert "backup" in backup and "restore" in backup.lower()
    auth = _section(md, "## Authentication and transport, as shipped")
    for needle in ("CLAWMETRY_API_TOKENS", "HTTP Basic", "plain HTTP"):
        assert needle in auth
    limits = _section(md, "## Not available yet")
    for needle in ("Entra ID", "OIDC", "Azure Container Apps", "ECS", "Helm", "air-gapped"):
        assert needle in limits, f"{needle} must be stated as not available, not implied"
    assert "—" not in md, "no em-dashes in user-facing docs (FLYWHEEL.md)"
