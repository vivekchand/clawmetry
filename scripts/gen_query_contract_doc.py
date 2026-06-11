#!/usr/bin/env python3
"""Generate docs/QUERY_CONTRACT.md from clawmetry/query_contract.py.

The committed doc is generator output, never hand-edited prose. The
drift CI test (tests/test_query_contract_drift.py) re-renders and fails
when the committed file differs from what this script emits.

Usage:
    python3 scripts/gen_query_contract_doc.py            # rewrite the doc
    python3 scripts/gen_query_contract_doc.py --check    # exit 1 on drift
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from clawmetry.query_contract import (  # noqa: E402
    CONTRACT_VERSION,
    QUERY_CONTRACT,
    STATUS_LIVE,
)

DOC_PATH = ROOT / "docs" / "QUERY_CONTRACT.md"

_HEADER = f"""# ClawMetry Query Contract ({CONTRACT_VERSION})

> GENERATED FILE, do not edit by hand. Source of truth:
> `clawmetry/query_contract.py`. Regenerate with
> `python3 scripts/gen_query_contract_doc.py` (CI fails on drift).

The node query surface served by `routes/local_query.py` (`/api/local/*`
plus the daemon proxy and the cloud relay) is declared in
`clawmetry/query_contract.py`. This document is generated from that
registry; CI fails when they disagree.

## Evolution rule

Inside `{CONTRACT_VERSION}` evolution is **additive only**: new methods and new
optional args may be added. Renaming or removing a method, an arg, or a
response field requires bumping the contract to `q/2`. A `planned`
method is a declared target that is not served yet; shipping it means
flipping its registry entry to `live` in the same change (the drift
test enforces both directions).

## Trust classes

* `plaintext`: aggregate counters or metadata the server may see in
  cleartext (heartbeat piggyback). Never raw content.
* `e2e`: session/content-bearing payloads. These only ever leave the
  machine AES-256-GCM encrypted via the sync daemon snapshot path and
  must never appear on a plaintext push list.

## Non-goals

* No per-model data in the device-facing `glance` method. Devices get
  top-line counters only; model breakdowns live in `models`.

## Methods
"""


def _fmt_arg(name: str, spec: dict) -> str:
    bits = []
    if spec.get("required"):
        bits.append("required")
    if "default" in spec:
        bits.append(f"default {spec['default']}")
    if "lo" in spec and "hi" in spec:
        bits.append(f"range {spec['lo']}..{spec['hi']}")
    return f"`{name}`" + (f" ({', '.join(bits)})" if bits else "")


def render() -> str:
    lines = [_HEADER]
    lines.append("| Method | Status | Trust | Backing | Args | Description |")
    lines.append("| - | - | - | - | - | - |")
    for name in sorted(QUERY_CONTRACT, key=lambda n: (QUERY_CONTRACT[n]["status"] != STATUS_LIVE, n)):
        spec = QUERY_CONTRACT[name]
        args = ", ".join(_fmt_arg(a, s) for a, s in spec["args"].items()) or "(none)"
        lines.append(
            f"| `{name}` | {spec['status']} | {spec['trust']} | "
            f"`{spec['backing']}` | {args} | {spec['doc']} |"
        )
    lines.append("")
    live = [n for n, s in QUERY_CONTRACT.items() if s["status"] == STATUS_LIVE]
    planned = [n for n, s in QUERY_CONTRACT.items() if s["status"] != STATUS_LIVE]
    lines.append(f"Live methods: {len(live)}. Planned methods: {len(planned)}.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    text = render()
    if "--check" in sys.argv[1:]:
        current = DOC_PATH.read_text() if DOC_PATH.exists() else ""
        if current != text:
            sys.stderr.write(
                "docs/QUERY_CONTRACT.md is stale. "
                "Run: python3 scripts/gen_query_contract_doc.py\n"
            )
            return 1
        print("docs/QUERY_CONTRACT.md is up to date.")
        return 0
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(text)
    print(f"wrote {DOC_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
