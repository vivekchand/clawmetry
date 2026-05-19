"""Tests for the structured BUDGET_EXCEEDED abort signal (G3 of #1708).

Pins three guarantees:
  1. Healthy budget: no abort header leaks onto normal responses.
  2. Exhausted budget: JSON body carries ``code: BUDGET_EXCEEDED`` +
     ``should_abort: true``.
  3. Exhausted budget: response header carries
     ``X-Clawmetry-Budget-Status: exceeded``.
"""

import json
from unittest.mock import patch

import pytest


@pytest.fixture
def client(tmp_path):
    import clawmetry.proxy
    from clawmetry.proxy import (
        create_proxy_app,
        ProxyConfig,
        BudgetConfig,
        LoopDetectionConfig,
        ProxyDB,
    )

    config = ProxyConfig(
        port=14101,
        budget=BudgetConfig(daily_usd=5.0, monthly_usd=100.0, action="block"),
        loop_detection=LoopDetectionConfig(enabled=False, max_similar=3, window_seconds=300),
    )
    db_path = tmp_path / "abort.db"
    original_init = ProxyDB.__init__

    def patched_init(self, db_path=None):
        original_init(self, db_path or clawmetry.proxy.PROXY_DB_FILE)

    with (
        patch.object(clawmetry.proxy, "PROXY_DB_FILE", db_path),
        patch.object(ProxyDB, "__init__", patched_init),
    ):
        app = create_proxy_app(config)
    app.config["TESTING"] = True
    c = app.test_client()
    c._db_path = db_path
    return c


def _exhaust_budget(db_path):
    from clawmetry.proxy import ProxyDB
    ProxyDB(db_path=db_path).record_usage(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        input_tokens=1000,
        output_tokens=500,
        cost_usd=10.0,
    )


def _post_messages(client):
    return client.post(
        "/v1/messages",
        data=json.dumps({
            "model": "claude-3-5-sonnet-20241022",
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 100,
        }),
        content_type="application/json",
        headers={"x-api-key": "test-key"},
    )


class TestBudgetAbort:
    def test_budget_not_exhausted_no_abort_envelope(self, client):
        # /proxy/status shares the BudgetEnforcer with the proxy path;
        # an empty exceeded flag here proves the abort path was NOT taken.
        resp = client.get("/proxy/status")
        assert resp.status_code == 200
        assert resp.get_json()["budget"]["daily_remaining"] == 5.0
        assert resp.headers.get("X-Clawmetry-Budget-Status") != "exceeded"

    def test_budget_exhausted_response_body_carries_abort_code(self, client):
        _exhaust_budget(client._db_path)
        resp = _post_messages(client)
        assert resp.status_code == 429
        body = resp.get_json()
        # Legacy 429 envelope preserved (don't break non-budget rate limits).
        assert body["type"] == "error"
        assert body["error"]["type"] == "budget_exceeded"
        # New abort envelope (G3 of #1708).
        assert body["code"] == "BUDGET_EXCEEDED"
        assert body["should_abort"] is True
        assert body["retry_after_seconds"] is None
        assert body["spent_today"] >= 5.0
        assert body["budget_today"] == 5.0
        assert "Halting agent" in body["message"]
        # No em-dashes in user-facing copy.
        assert "—" not in body["message"]

    def test_budget_exhausted_response_header_carries_abort_flag(self, client):
        _exhaust_budget(client._db_path)
        resp = _post_messages(client)
        assert resp.status_code == 429
        assert resp.headers.get("X-Clawmetry-Budget-Status") == "exceeded"
