#!/usr/bin/env python3
"""Pin the self-hosted Compose deployment to a verified image digest.

    python3 scripts/pin_selfhosted_compose.py pin --version 0.12.900 \\
        --digest sha256:<64 hex>
    python3 scripts/pin_selfhosted_compose.py check

``pin`` rewrites the ``clawmetry`` service in deploy/self-hosted/docker-compose.yml
to ``image: ghcr.io/vivekchand/clawmetry:<version>@sha256:<digest>`` and removes
its ``build:`` block. It is run by .github/workflows/container-image.yml only
after the image has been pulled anonymously, signature-checked and restarted
with an event intact, so a digest in that file means a verified image exists.

``check`` fails when the Compose file names the published image by a tag alone
(a tag can move under a running deployment), or names it while also keeping a
``build:`` block (Compose would quietly build from source whenever the pull
fails, and the operator would be running an unsigned image without knowing).

The edit is line-based on purpose: the Compose file is mostly comments an
operator reads, and a YAML round-trip would delete every one of them.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_COMPOSE = os.path.join(REPO_ROOT, "deploy", "self-hosted", "docker-compose.yml")

IMAGE_REPO = "ghcr.io/vivekchand/clawmetry"
SERVICE = "clawmetry"

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
PINNED_RE = re.compile(
    r"^" + re.escape(IMAGE_REPO) + r":[0-9]+\.[0-9]+\.[0-9]+@sha256:[0-9a-f]{64}$"
)


class PinError(ValueError):
    pass


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _is_content(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def _service_span(lines: list) -> tuple:
    """(start, end) line indexes of the service block, header excluded."""
    services_at = None
    for i, line in enumerate(lines):
        if _indent(line) == 0 and line.rstrip() == "services:":
            services_at = i
            break
    if services_at is None:
        raise PinError("no top-level `services:` key")
    header = None
    for i in range(services_at + 1, len(lines)):
        line = lines[i]
        if _is_content(line) and _indent(line) == 0:
            break
        if _is_content(line) and line.strip() == f"{SERVICE}:":
            header = i
            break
    if header is None:
        raise PinError(f"no `{SERVICE}` service under `services:`")
    own = _indent(lines[header])
    end = len(lines)
    for i in range(header + 1, len(lines)):
        if _is_content(lines[i]) and _indent(lines[i]) <= own:
            end = i
            break
    return header, end


def _keys(lines: list, start: int, end: int) -> dict:
    """Direct child keys of the service: name -> (line index, block end)."""
    child = None
    for i in range(start + 1, end):
        if _is_content(lines[i]):
            child = _indent(lines[i])
            break
    out = {}
    if child is None:
        return out
    for i in range(start + 1, end):
        line = lines[i]
        if not _is_content(line) or _indent(line) != child:
            continue
        m = re.match(r"^\s*([A-Za-z0-9_-]+):", line)
        if not m:
            continue
        block_end = end
        for j in range(i + 1, end):
            if _is_content(lines[j]) and _indent(lines[j]) <= child:
                block_end = j
                break
        # Trailing comment lines belong to whatever comes next, not this key.
        while block_end - 1 > i and not _is_content(lines[block_end - 1]):
            block_end -= 1
        out[m.group(1)] = (i, block_end)
    return out


def _image_value(line: str) -> str:
    value = line.split(":", 1)[1].split(" #", 1)[0].strip()
    return value.strip("\"'")


def pin(text: str, version: str, digest: str) -> str:
    if not VERSION_RE.match(version or ""):
        raise PinError(f"not a release version: {version!r}")
    if not DIGEST_RE.match(digest or ""):
        raise PinError(f"not a sha256 digest: {digest!r}")
    lines = text.splitlines(keepends=True)
    start, end = _service_span(lines)
    keys = _keys(lines, start, end)
    child_indent = " " * (_indent(lines[start]) + 2)
    if "image" in keys:
        child_indent = " " * _indent(lines[keys["image"][0]])
    elif "build" in keys:
        child_indent = " " * _indent(lines[keys["build"][0]])
    image_line = f"{child_indent}image: {IMAGE_REPO}:{version}@{digest}\n"

    drop = set()
    if "build" in keys:
        b_start, b_end = keys["build"]
        drop.update(range(b_start, b_end))
    out = []
    placed = False
    for i, line in enumerate(lines):
        if i in drop:
            if not placed and "image" not in keys:
                out.append(image_line)
                placed = True
            continue
        if "image" in keys and i == keys["image"][0]:
            out.append(image_line)
            placed = True
            continue
        out.append(line)
        if i == start and "image" not in keys and "build" not in keys:
            out.append(image_line)
            placed = True
    return "".join(out)


def check(text: str) -> list:
    problems = []
    lines = text.splitlines(keepends=True)
    try:
        start, end = _service_span(lines)
    except PinError as exc:
        return [str(exc)]
    keys = _keys(lines, start, end)
    image = _image_value(lines[keys["image"][0]]) if "image" in keys else ""
    if image.startswith(IMAGE_REPO):
        if not PINNED_RE.match(image):
            problems.append(
                f"`{image}` names the published image without a version and "
                "sha256 digest; a tag can move under a running deployment"
            )
        if "build" in keys:
            problems.append(
                "the service names the published image AND keeps a `build:` "
                "block, so a failed pull would silently run an unsigned source "
                "build; remove `build:` (docker-compose.build.yml is the "
                "explicit source-build path)"
            )
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--compose", default=DEFAULT_COMPOSE)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_pin = sub.add_parser("pin", help="pin the service to version@digest")
    p_pin.add_argument("--version", required=True)
    p_pin.add_argument("--digest", required=True)
    sub.add_parser("check", help="fail on a tag-only or build-shadowed image")
    args = parser.parse_args(argv)

    with open(args.compose, encoding="utf-8") as fh:
        text = fh.read()
    if args.cmd == "pin":
        try:
            new = pin(text, args.version, args.digest)
        except PinError as exc:
            print(f"refusing to pin: {exc}", file=sys.stderr)
            return 2
        problems = check(new)
        if problems:
            print("pin produced an invalid file:", *problems, sep="\n  ", file=sys.stderr)
            return 1
        with open(args.compose, "w", encoding="utf-8") as fh:
            fh.write(new)
        print(f"pinned {args.compose} to {IMAGE_REPO}:{args.version}@{args.digest}")
        return 0
    problems = check(text)
    for problem in problems:
        print(f"{args.compose}: {problem}", file=sys.stderr)
    if not problems:
        print(f"{args.compose}: ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
