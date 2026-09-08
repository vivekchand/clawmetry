#!/usr/bin/env python3
"""Verify every vendored third-party asset against its recorded provenance.

Two levels of assurance, both driven by scripts/vendor.lock.json:

1. **Hash pin (always).** The sha256 of each file in
   ``clawmetry/static/vendor/`` must match the lockfile. This catches a local
   edit, a corrupted file, or a commit that swaps the bytes.
2. **Registry byte-comparison (when a version is recorded).** Re-download the
   npm registry tarball for the pinned package+version and byte-compare the
   named file. This is the stronger claim: the code we serve is *provably* the
   published release, not something that merely hashes consistently because it
   was tampered with before the hash was recorded.

Why bother: the dashboard renders agent transcripts, so anything executing in
that page can read them. Vendoring removes the CDN from the trust boundary;
this script keeps the vendored copy honest afterwards. It is the evidence
behind the "no third-party code paths" line in a vendor security review.

Usage:
    python3 scripts/verify_vendor.py             # hash check + registry compare
    python3 scripts/verify_vendor.py --offline   # hash check only (air-gapped CI)
    python3 scripts/verify_vendor.py --update    # rewrite hashes from files on disk
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import ssl
import sys
import tarfile
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR_DIR = os.path.join(REPO, "clawmetry", "static", "vendor")
LOCK_PATH = os.path.join(REPO, "scripts", "vendor.lock.json")
REGISTRY = "https://registry.npmjs.org"


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _fetch_from_registry(package: str, version: str, member: str) -> bytes | None:
    """Download the published tarball and return one file's bytes."""
    # Scoped packages (@scope/name) put the tarball under the unscoped name.
    tail = package.split("/")[-1]
    url = f"{REGISTRY}/{package}/-/{tail}-{version}.tgz"
    try:
        with urllib.request.urlopen(url, timeout=60, context=_ssl_context()) as resp:
            blob = resp.read()
    except Exception as exc:
        print(f"       registry fetch failed ({exc}) — skipping byte-comparison")
        return None
    try:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
            extracted = tar.extractfile(member)
            return extracted.read() if extracted else None
    except (tarfile.TarError, KeyError) as exc:
        print(f"       tarball member {member!r} unreadable ({exc})")
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true", help="hash check only, no network")
    ap.add_argument("--update", action="store_true", help="rewrite hashes from disk")
    args = ap.parse_args()

    with open(LOCK_PATH, encoding="utf-8") as fh:
        lock = json.load(fh)
    entries = lock["files"]

    if args.update:
        for name, meta in entries.items():
            path = os.path.join(VENDOR_DIR, name)
            if os.path.isfile(path):
                meta["sha256"] = _sha256(path)
                print(f"updated  {name}  {meta['sha256']}")
        with open(LOCK_PATH, "w", encoding="utf-8") as fh:
            json.dump(lock, fh, indent=2)
            fh.write("\n")
        return 0

    failures: list[str] = []

    # Anything on disk but absent from the lockfile is unreviewed code.
    on_disk = {f for f in os.listdir(VENDOR_DIR) if f.endswith((".js", ".css"))}
    for extra in sorted(on_disk - set(entries)):
        failures.append(f"{extra}: present in vendor/ but not in vendor.lock.json (unreviewed)")

    for name, meta in entries.items():
        path = os.path.join(VENDOR_DIR, name)
        if not os.path.isfile(path):
            failures.append(f"{name}: listed in lockfile but missing from vendor/")
            continue

        actual = _sha256(path)
        expected = meta.get("sha256")
        if actual != expected:
            failures.append(
                f"{name}: sha256 mismatch\n"
                f"       expected {expected}\n"
                f"       actual   {actual}"
            )
            continue

        version = meta.get("version")
        member = meta.get("path_in_tarball")
        if args.offline or not version or not member:
            reason = "offline" if args.offline else "no version pinned"
            print(f"ok       {name}  (hash pinned; registry compare skipped — {reason})")
            continue

        published = _fetch_from_registry(meta["package"], version, member)
        if published is None:
            print(f"ok       {name}  (hash pinned; registry compare unavailable)")
            continue

        with open(path, "rb") as fh:
            ours = fh.read()
        if ours != published:
            failures.append(
                f"{name}: differs from published {meta['package']}@{version} "
                f"({member}) — {len(ours)} bytes local vs {len(published)} published"
            )
        else:
            print(f"ok       {name}  == {meta['package']}@{version} (byte-identical to registry)")

    if failures:
        print("\nVendored asset verification FAILED:\n")
        for f in failures:
            print(f"  {f}")
        print("\nIf you intentionally changed a vendored file, update scripts/vendor.lock.json")
        print("(and record the package + version so provenance stays checkable).")
        return 1

    print(f"\nok  {len(entries)} vendored asset(s) verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
