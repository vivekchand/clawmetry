#!/usr/bin/env python3
"""Generate docs/INGEST.md from clawmetry/ingest_contract.py.

The committed doc is generator output, never hand-edited prose. The
drift CI test (tests/test_ingest_doc_drift.py) re-renders and fails
when the committed file differs from what this script emits.

Usage:
    python3 scripts/gen_ingest_doc.py            # rewrite the doc
    python3 scripts/gen_ingest_doc.py --check    # exit 1 on drift
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from clawmetry.ingest_contract import (  # noqa: E402
    CONTRACT_VERSION,
    GEN_AI_ATTRS_NOT_READ,
    GEN_AI_ATTRS_READ,
    OTLP_CONTENT_TYPES,
    OTLP_ENCODINGS,
    OTLP_ENDPOINTS,
    OTLP_MAX_DECOMPRESSED_ENVVAR,
    OTLP_MAX_DECOMPRESSED_MB,
    OTLP_RESPONSE_CODES,
    RUN_ENDPOINTS,
    RUN_RESPONSE_CODES,
)

DOC_PATH = ROOT / "docs" / "INGEST.md"

_HEADER = f"""\
# ClawMetry Ingest Contract ({CONTRACT_VERSION})

> GENERATED FILE — do not edit by hand. Source of truth:
> `clawmetry/ingest_contract.py`. Regenerate with
> `python3 scripts/gen_ingest_doc.py` (CI fails on drift).

Two surfaces accept inbound data: the **OTLP receiver** (standard
OpenTelemetry HTTP) and the **run/event ingest API** (structured
run/step records for custom runtimes). Both bind on the same port as
the dashboard (default `127.0.0.1:8900`).

## Evolution rule

Inside `{CONTRACT_VERSION}` evolution is **additive only**: new endpoints,
content-types, and attributes may be added. Removing or renaming one
requires bumping the contract to `ingest/2`.
"""


def _render_otlp() -> list[str]:
    lines = ["## OTLP receiver", ""]
    lines.append(
        "Point any OpenTelemetry-instrumented app at the dashboard port:\n"
        "```\n"
        "OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900\n"
        "OTEL_EXPORTER_OTLP_PROTOCOL=http/json\n"
        "```"
    )
    lines.append("")

    lines.append("### Endpoints")
    lines.append("")
    lines.append("| Method | Path | Description |")
    lines.append("| - | - | - |")
    for path, spec in OTLP_ENDPOINTS.items():
        methods = ", ".join(f"`{m}`" for m in spec["methods"])
        lines.append(f"| {methods} | `{path}` | {spec['doc']} |")
    lines.append("")

    lines.append("### Accepted content types")
    lines.append("")
    lines.append("| `Content-Type` | Description |")
    lines.append("| - | - |")
    for ct, doc in OTLP_CONTENT_TYPES.items():
        lines.append(f"| `{ct}` | {doc} |")
    lines.append("")

    enc_str = ", ".join(f"`{e}`" for e in OTLP_ENCODINGS)
    lines.append(f"**`Content-Encoding`:** {enc_str}.")
    lines.append("")

    lines.append("### Size limits")
    lines.append("")
    lines.append(
        f"Decompressed body cap: **{OTLP_MAX_DECOMPRESSED_MB} MB** "
        f"(override: `{OTLP_MAX_DECOMPRESSED_ENVVAR}`)."
    )
    lines.append(
        "Anything larger is rejected with HTTP 400 before the body is parsed."
    )
    lines.append("")

    lines.append("### Response codes")
    lines.append("")
    lines.append("| Code | Meaning |")
    lines.append("| - | - |")
    for code, doc in sorted(OTLP_RESPONSE_CODES.items()):
        lines.append(f"| `{code}` | {doc} |")
    lines.append("")

    return lines


def _render_gen_ai() -> list[str]:
    lines = ["### `gen_ai.*` attributes read", ""]
    lines.append(
        "Spans and log records are mapped by `dashboard.py::_otel_to_row`. "
        "Every attribute below is tried in order; the first non-empty value wins."
    )
    lines.append("")
    lines.append("| Primary attribute | Fallbacks | Description |")
    lines.append("| - | - | - |")
    for attr, (doc, fallbacks) in GEN_AI_ATTRS_READ.items():
        fb = ", ".join(f"`{f}`" for f in fallbacks) if fallbacks else "—"
        lines.append(f"| `{attr}` | {fb} | {doc} |")
    lines.append("")

    not_read_str = ", ".join(f"`{a}`" for a in GEN_AI_ATTRS_NOT_READ)
    lines.append(
        f"Attributes that appear in GenAI semconv but are **not yet consumed**: "
        f"{not_read_str}."
    )
    lines.append("")
    return lines


def _render_run_api() -> list[str]:
    lines = ["## Run / event ingest API", ""]
    lines.append(
        "Push structured run and event records from any agent runtime. "
        "The write endpoints are a **Pro feature** (OSS returns HTTP 402). "
        "`GET /api/v1/runtimes` is free on all tiers."
    )
    lines.append("")

    lines.append("### Endpoints")
    lines.append("")
    lines.append("| Method | Path | Tier | Description |")
    lines.append("| - | - | - | - |")
    for route, spec in RUN_ENDPOINTS.items():
        method, path = route.split(" ", 1)
        tier = spec["tier"].capitalize()
        lines.append(f"| `{method}` | `{path}` | {tier} | {spec['doc']} |")
    lines.append("")

    lines.append("### Auth")
    lines.append("")
    lines.append(
        "Two modes; the dashboard picks based on environment:\n\n"
        "1. **Localhost-only (default):** if `CLAWMETRY_INGEST_TOKEN` is unset, "
        "only loopback (`127.0.0.1` / `::1`) requests are accepted.\n"
        "2. **Token header:** set `CLAWMETRY_INGEST_TOKEN=<secret>`; clients "
        "must send `X-ClawMetry-Token: <secret>`. The comparison is constant-time."
    )
    lines.append("")

    lines.append("### Response codes")
    lines.append("")
    lines.append("| Code | Meaning |")
    lines.append("| - | - |")
    for code, doc in sorted(RUN_RESPONSE_CODES.items()):
        lines.append(f"| `{code}` | {doc} |")
    lines.append("")

    lines.append("### Quickstart")
    lines.append("")
    lines.append("```bash")
    lines.append("# Start a run")
    lines.append("curl -s http://localhost:8900/api/v1/runs \\")
    lines.append("  -H 'content-type: application/json' \\")
    lines.append("  -d '{\"runtime\": \"my_engine\", \"metadata\": {\"build\": \"abc123\"}}'")
    lines.append("# -> {\"ok\": true, \"run_id\": \"run_a1b2c3d4...\", \"runtime\": \"my_engine\"}")
    lines.append("")
    lines.append("# Push an event")
    lines.append("curl -s http://localhost:8900/api/v1/runs/run_a1b2c3d4/events \\")
    lines.append("  -H 'content-type: application/json' \\")
    lines.append("  -d '{\"event\": {\"id\": \"evt_1\", \"event_type\": \"model.completed\", \\")
    lines.append("    \"model\": \"claude-sonnet-5\", \"data\": {\"input_tokens\": 1240, \"output_tokens\": 312}}}'")
    lines.append("")
    lines.append("# Close the run")
    lines.append("curl -s http://localhost:8900/api/v1/runs/run_a1b2c3d4/end \\")
    lines.append("  -H 'content-type: application/json' -d '{}'")
    lines.append("```")
    lines.append("")

    return lines


def render() -> str:
    lines: list[str] = [_HEADER]
    lines.extend(_render_otlp())
    lines.extend(_render_gen_ai())
    lines.extend(_render_run_api())
    return "\n".join(lines)


def main() -> int:
    text = render()
    if "--check" in sys.argv[1:]:
        current = DOC_PATH.read_text() if DOC_PATH.exists() else ""
        if current != text:
            sys.stderr.write(
                "docs/INGEST.md is stale. "
                "Run: python3 scripts/gen_ingest_doc.py\n"
            )
            return 1
        print("docs/INGEST.md is up to date.")
        return 0
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(text)
    print(f"wrote {DOC_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
