"""E2E smoke: OTLP trace ingest pipeline (POST /v1/traces -> /api/spans).

Verifies the full pipeline introduced in commit #4785 (2026-08-12):

  1. POST a synthetic OTLP JSON trace (hex traceId/spanId, no protobuf) to
     /v1/traces.
  2. Verify HTTP 200 -- the stdlib OTLP/JSON decoder must accept the payload.
  3. Poll /api/spans for up to 10s for the synthetic trace to appear -- proves
     _process_otlp_traces wrote to the DuckDB ``spans`` table and /api/spans
     returns it.

No Playwright required. Run against the golden-path server:

    CLAWMETRY_URL=http://localhost:8920 CLAWMETRY_TOKEN=ci-golden-token \\
    pytest tests/test_e2e_otlp_ingest.py -v

Or against any running dashboard:

    OPENCLAW_GATEWAY_TOKEN=ci-test-token python dashboard.py --port 8900 &
    CLAWMETRY_URL=http://localhost:8900 CLAWMETRY_TOKEN=ci-test-token \\
    pytest tests/test_e2e_otlp_ingest.py -v
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

import pytest

BASE_URL = os.environ.get("CLAWMETRY_URL", "http://localhost:8900")
TOKEN = os.environ.get("CLAWMETRY_TOKEN", "ci-test-token")

# Unique hex IDs so this test's span is distinguishable from any ambient data.
_TRACE_ID = "e2e00000000000000000000000000001"
_SPAN_ID = "e2e0000000000001"

# Minimal valid OTLP JSON payload (OTLP/HTTP+JSON spec).
# Uses hex-encoded traceId/spanId and nanosecond timestamps as strings,
# matching the format the stdlib decoder in #4785 expects.
_OTLP_PAYLOAD: dict = {
    "resourceSpans": [
        {
            "resource": {
                "attributes": [
                    {
                        "key": "service.name",
                        "value": {"stringValue": "clawmetry-e2e-otlp-smoke"},
                    }
                ]
            },
            "scopeSpans": [
                {
                    "scope": {"name": "e2e-smoke", "version": "1.0.0"},
                    "spans": [
                        {
                            "traceId": _TRACE_ID,
                            "spanId": _SPAN_ID,
                            "name": "e2e-otlp-smoke-span",
                            "kind": 1,
                            "startTimeUnixNano": "1000000000000000000",
                            "endTimeUnixNano": "2000000000000000000",
                            "status": {"code": 0},
                            "attributes": [
                                {
                                    "key": "e2e.smoke",
                                    "value": {"boolValue": True},
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ]
}


def _auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }


def _get(path: str) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


class TestOtlpIngest:
    """OTLP trace ingest pipeline: POST /v1/traces -> DuckDB -> /api/spans.

    Acceptance test for criterion: the OTLP receiver works out of the box
    (stdlib JSON decoder, no protobuf dep) as shipped in commit #4785.
    """

    def test_otlp_post_returns_200(self):
        """POST /v1/traces with valid OTLP JSON must return HTTP 200.

        A non-200 here means one of:
          (a) The OTLP receiver endpoint is not registered (/v1/traces route
              missing or blueprint not registered in dashboard.py).
          (b) The stdlib OTLP/JSON decoder raised OtlpProtobufUnavailable
              or a parse error (regression in clawmetry/otlp_json.py).
          (c) The auth check rejected the bearer token (token mismatch
              between OPENCLAW_GATEWAY_TOKEN and CLAWMETRY_TOKEN).
        """
        data = json.dumps(_OTLP_PAYLOAD).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/v1/traces",
            data=data,
            headers=_auth_headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status
        except urllib.error.HTTPError as exc:
            status = exc.code
        assert status == 200, (
            f"/v1/traces returned HTTP {status}, expected 200. "
            f"Ensure the OTLP receiver is enabled and "
            f"OPENCLAW_GATEWAY_TOKEN={TOKEN!r} matches the running server."
        )

    def test_otlp_span_appears_in_api_spans(self):
        """After POST /v1/traces the synthetic span must appear in /api/spans.

        Polls for up to 10s to accommodate the async ingest path: the
        dashboard ingests OTLP spans in the sync thread, which may not
        complete synchronously with the HTTP response to /v1/traces.

        A timeout here means one of:
          (a) _process_otlp_traces did not call clawmetry.local_store.put_span
              (DuckDB write never happened).
          (b) /api/spans does not query the ``spans`` table, or the daemon
              proxy is returning an empty list instead of the DuckDB data.
          (c) The ingest happened but the span was filtered out (e.g. by a
              session_id filter that excluded spans with no session context).
        """
        # First, post the trace (tolerate prior test run already posting it).
        data = json.dumps(_OTLP_PAYLOAD).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/v1/traces",
            data=data,
            headers=_auth_headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except urllib.error.HTTPError:
            pass  # POST failure is already caught by test_otlp_post_returns_200

        # Poll /api/spans for up to 10s.
        deadline = time.monotonic() + 10.0
        found = False
        last_body: object = None
        while time.monotonic() < deadline:
            try:
                body = _get("/api/spans")
                last_body = body
                spans = body.get("spans", []) if isinstance(body, dict) else []
                for span in spans:
                    # Match on trace_id field (the store normalises to lowercase hex).
                    if str(span.get("trace_id", "")).lower() == _TRACE_ID.lower():
                        found = True
                        break
            except Exception:
                pass
            if found:
                break
            time.sleep(0.5)

        assert found, (
            f"Synthetic span (trace_id={_TRACE_ID!r}) not found in /api/spans "
            f"after 10s. Last /api/spans body keys: "
            f"{list(last_body) if isinstance(last_body, dict) else type(last_body).__name__}. "
            f"Possible causes:\n"
            f"  (1) _process_otlp_traces did not write to DuckDB ``spans`` table;\n"
            f"  (2) /api/spans queries a different table or filters out\n"
            f"      spans that have no session_id;\n"
            f"  (3) the ingest is async and 10s was not enough (unlikely on CI).\n"
            f"Ensure the dashboard started with OPENCLAW_GATEWAY_TOKEN={TOKEN!r}."
        )
