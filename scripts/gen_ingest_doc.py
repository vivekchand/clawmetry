#!/usr/bin/env python3
"""Generate docs/INGEST.md from clawmetry/ingest_contract.py.

The committed doc is generator output, never hand-edited prose. The drift
test (tests/test_ingest_contract_drift.py) re-renders and fails when the
committed file differs -- the same arrangement as the query contract on
the read side.

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
    AUTH_MODES,
    CONTENT_ENCODINGS,
    CONTENT_TYPES,
    CONTRACT_VERSION,
    GENAI_NOT_READ,
    GENAI_READ,
    HEADER_ENV,
    HEADER_KEY,
    HEADER_RUNTIME,
    HEADERS,
    MAX_BODY_BYTES,
    MAX_EVENTS_PER_BATCH,
    RESPONSES,
    SURFACES,
)

DOC_PATH = ROOT / "docs" / "INGEST.md"


def render() -> str:
    mb = MAX_BODY_BYTES // (1024 * 1024)
    out: list = []
    a = out.append

    a(f"# Sending data to ClawMetry ({CONTRACT_VERSION})")
    a("")
    a("> GENERATED FILE, do not edit by hand. Source of truth:")
    a("> `clawmetry/ingest_contract.py`. Regenerate with")
    a("> `python3 scripts/gen_ingest_doc.py` (CI fails on drift).")
    a("")
    a("Most people never read this page. ClawMetry detects the agents on")
    a("the machine it runs on and starts observing them with no")
    a("configuration at all.")
    a("")
    a("This page is for the other case: an agent that is **not** on that")
    a("machine — running in CI, in a container, in a serverless function,")
    a("inside a hosted product, or on somebody else's laptop. Those push to")
    a("ClawMetry instead of being detected by it.")
    a("")

    a("## Authentication")
    a("")
    a("| Mode | When | How |")
    a("|---|---|---|")
    for m in AUTH_MODES:
        a(f"| {m['name']} | {m['when']} | {m['how']} |")
    a("")
    a("An ingest key can **only push**. It grants no read scope, so a key")
    a("left in a CI runner cannot read a prompt, a cost or a session back")
    a("out. It is never given a CORS header and cannot be created with a")
    a("browser origin: ingest is server-to-server.")
    a("")

    a("## Endpoints")
    a("")
    a("| Method | Path | Accepts | |")
    a("|---|---|---|---|")
    for s in SURFACES:
        a(f"| `{s['method']}` | `{s['path']}` | {s['accepts']} | {s['doc']} |")
    a("")

    a("## Encodings")
    a("")
    a("| `Content-Type` | |")
    a("|---|---|")
    for ct, doc in CONTENT_TYPES:
        a(f"| `{ct}` | {doc} |")
    a("")
    a("| `Content-Encoding` | |")
    a("|---|---|")
    for ce, doc in CONTENT_ENCODINGS:
        a(f"| `{ce}` | {doc} |")
    a("")

    a("## Headers")
    a("")
    a("| Header | Required | |")
    a("|---|---|---|")
    for h in HEADERS:
        a(f"| `{h['name']}` | {h['required']} | {h['doc']} |")
    a("")
    a(f"`{HEADER_RUNTIME}` and `{HEADER_ENV}` are resolved once per request")
    a("and applied to every event in it. They are written into the resource")
    a("attributes the mappers already read, so a header is exactly as")
    a("powerful as the equivalent exporter setting — and the header wins,")
    a("because it is the one you set per request.")
    a("")
    a("There is one grouping axis above runtime, on purpose. A")
    a("dataset/collection/tag taxonomy is what a log platform needs when it")
    a("has thousands of unrelated sources. This is not that.")
    a("")

    a("## Limits")
    a("")
    a("| | |")
    a("|---|---|")
    a(f"| Body | {mb} MB |")
    a(f"| Events per batch | {MAX_EVENTS_PER_BATCH} |")
    a("")

    a("## Responses")
    a("")
    a("Every response carries a sentence in its body, not only a code.")
    a("These get read inside an agent's terminal output with no")
    a("documentation open.")
    a("")
    a("| Code | Means |")
    a("|---|---|")
    for code, doc in RESPONSES:
        a(f"| `{code}` | {doc} |")
    a("")

    a("## Example")
    a("")
    a("```bash")
    a("clawmetry key create --name ci --scope write:ingest")
    a("")
    a("curl -X POST http://localhost:8900/v1/traces \\")
    a(f"  -H \"{HEADER_KEY}: $CLAWMETRY_KEY\" \\")
    a(f"  -H '{HEADER_RUNTIME}: my-engine' \\")
    a(f"  -H '{HEADER_ENV}: production' \\")
    a("  -H 'Content-Type: application/json' \\")
    a("  --data-binary @spans.json")
    a("```")
    a("")

    a("## GenAI attributes")
    a("")
    a("ClawMetry reads the OpenTelemetry GenAI semantic conventions, so an")
    a("app instrumented with any conforming library needs no")
    a("ClawMetry-specific SDK.")
    a("")
    a("### Read")
    a("")
    a("| Attribute | |")
    a("|---|---|")
    for attr, doc in GENAI_READ:
        a(f"| `{attr}` | {doc} |")
    a("")
    a("### Not read")
    a("")
    a("Listed because a reference that only says what works is not one you")
    a("can plan against.")
    a("")
    a("| Attribute | |")
    a("|---|---|")
    for attr, doc in GENAI_NOT_READ:
        a(f"| `{attr}` | {doc} |")
    a("")

    a("## What ClawMetry does not accept")
    a("")
    a("There is no endpoint that takes syslog, CEF, GELF, Apache logs or")
    a("raw text. ClawMetry's inputs are typed on arrival, and a parser")
    a("layer would exist only to accept data this product has nothing to")
    a("say about. If you want general log ingestion, use a log platform —")
    a("and point it at ClawMetry's own export, which speaks OTLP.")
    a("")

    return "\n".join(out)


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
