#!/usr/bin/env python3
"""Fail the build if any served page references a third-party origin.

The rule
--------
A ClawMetry page must render fully with zero egress. Not "mostly" — zero.
Three things depend on it:

* **Air-gapped installs.** ClawMetry Enterprise self-hosted is sold on "your
  data never leaves your network". A ``<script src="https://cdn...">`` makes
  that false: the page either blocks or renders broken.
* **Supply chain.** A remote script tag is arbitrary third-party code with DOM
  access, executing in a page that renders agent transcripts. A CDN
  compromise is a ClawMetry compromise. Subresource Integrity does not save
  you here — jsDelivr's own minifier endpoint explicitly documents that SRI
  cannot be used with its dynamically generated files.
* **Vendor review.** "Which external services does the dashboard contact?" is
  question one. "None, and CI enforces it" is a much better answer than a
  list.

What this checks
----------------
Every HTML-bearing file we serve is scanned for absolute ``http(s)://``
references in tags that cause a *fetch* — script/link/img/iframe/video and
CSS ``url()``. Hyperlinks (``<a href>``) are fine: they are navigation the
user chooses, not a load the page performs.

Usage:  python3 scripts/verify_no_external_assets.py
"""
from __future__ import annotations

import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files that embed or serve markup. dashboard.py holds the big HTML string
# templates; the rest are real templates and static assets.
SCAN_FILES = [
    "dashboard.py",
    "dashboard_claudecode.py",
]
SCAN_DIRS = [
    ("clawmetry/templates", (".html",)),
    ("clawmetry/static/css", (".css",)),
    ("clawmetry/static/js", (".js",)),
    ("clawmetry/static/v2/dist", (".html",)),
    ("frontend", (".html",)),
]

# Directories never scanned: third-party bundles we vendor deliberately (their
# own source-map/homepage comments are not fetches) and build detritus.
SKIP_DIRS = {"node_modules", "dist/assets", "clawmetry/static/vendor", ".git"}

# Fetch-causing constructs. Deliberately does NOT match <a href="https://...">.
PATTERNS = [
    # <script src="https://...">, <img src=...>, <iframe src=...>
    re.compile(r"""<\s*(?:script|img|iframe|video|audio|source|embed)\b[^>]*?\bsrc\s*=\s*["']?(https?://[^"'\s>]+)""", re.I),
    # <link href="https://..."> — stylesheets, preconnect, prefetch, icons
    re.compile(r"""<\s*link\b[^>]*?\bhref\s*=\s*["']?(https?://[^"'\s>]+)""", re.I),
    # CSS url(https://...) — @font-face src, background-image
    re.compile(r"""url\(\s*["']?(https?://[^"')\s]+)""", re.I),
    # @import "https://..."
    re.compile(r"""@import\s+(?:url\()?["'](https?://[^"']+)""", re.I),
]

# Narrow, reviewed exceptions. Keep this list empty if at all possible; every
# entry is a page that cannot render offline. Format: (path_suffix, substring).
ALLOWED: list[tuple[str, str]] = []


def _is_allowed(path: str, url: str) -> bool:
    return any(path.endswith(p) and frag in url for p, frag in ALLOWED)


def _iter_files():
    for rel in SCAN_FILES:
        full = os.path.join(REPO, rel)
        if os.path.isfile(full):
            yield rel, full
    for rel_dir, exts in SCAN_DIRS:
        root_dir = os.path.join(REPO, rel_dir)
        for dirpath, dirnames, filenames in os.walk(root_dir):
            rel_path = os.path.relpath(dirpath, REPO)
            if any(skip in rel_path.replace(os.sep, "/") for skip in SKIP_DIRS):
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if name.endswith(exts):
                    full = os.path.join(dirpath, name)
                    yield os.path.relpath(full, REPO), full


def main() -> int:
    violations = []
    scanned = 0
    for rel, full in _iter_files():
        scanned += 1
        try:
            with open(full, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for pattern in PATTERNS:
                for match in pattern.finditer(line):
                    url = match.group(1)
                    if _is_allowed(rel, url):
                        continue
                    violations.append((rel, lineno, url))

    if violations:
        print("External asset references found — a served page would contact a third party.\n")
        for rel, lineno, url in violations:
            print(f"  {rel}:{lineno}")
            print(f"      {url}\n")
        print(f"{len(violations)} violation(s) across {scanned} scanned files.\n")
        print("Fix: vendor the asset instead.")
        print("  - Fonts:      add the family to scripts/vendor_fonts.py, then run it")
        print("  - JS/CSS libs: download the npm tarball into clawmetry/static/vendor/,")
        print("                 register it in scripts/verify_vendor.py, reference via url_for")
        return 1

    print(f"ok  no external asset references ({scanned} files scanned)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
