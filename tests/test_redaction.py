"""Tests for clawmetry/redaction.py — defense-in-depth secret scrubbing
applied at the daemon ingest chokepoint. Issue #2197.
"""
from __future__ import annotations

import importlib

import pytest

from clawmetry import redaction


@pytest.fixture(autouse=True)
def _enabled(monkeypatch):
    # Redaction reads the env var at call time; make sure it's on for tests.
    monkeypatch.delenv("CLAWMETRY_REDACT", raising=False)
    yield


def test_openai_and_anthropic_keys_fingerprinted():
    out = redaction.redact_text("key is sk-ant-abcdefghijklmnopqrstuvwx and sk-ABCDEFGHIJKLMNOP01")
    assert "sk-ant-abcdefghijklmnopqrstuvwx" not in out
    assert "sk-ABCDEFGHIJKLMNOP01" not in out
    assert out.count("[REDACTED:") == 2


def test_bearer_token_redacted():
    out = redaction.redact_text("Authorization: Bearer eyJabc123.def456.ghi789xyz")
    assert "eyJabc123.def456.ghi789xyz" not in out
    assert "Bearer [REDACTED:" in out


def test_keyval_password_redacted():
    out = redaction.redact_text('password=hunter2supersecret api_key: AbC123xyz789Qq')
    assert "hunter2supersecret" not in out
    assert "AbC123xyz789Qq" not in out


def test_provider_tokens_redacted():
    samples = {
        "AKIAIOSFODNN7EXAMPLE": "AWS",
        "ghp_1234567890abcdefghijklmnopqrstuvwxyz": "GitHub",
        "xoxb-12345-abcdefXYZ": "Slack",
    }
    for tok in samples:
        out = redaction.redact_text(f"token here: {tok} end")
        assert tok not in out, f"{samples[tok]} token leaked"


def test_private_key_block_redacted():
    pem = "-----BEGIN RSA PRIVATE KEY-----\nMIIabc...\n-----END RSA PRIVATE KEY-----"
    out = redaction.redact_text(f"here:\n{pem}\ndone")
    assert "MIIabc" not in out
    assert "[REDACTED:private-key]" in out


def test_same_secret_same_fingerprint():
    a = redaction.redact_text("sk-ABCDEFGHIJKLMNOP01")
    b = redaction.redact_text("sk-ABCDEFGHIJKLMNOP01")
    assert a == b and "[REDACTED:" in a


def test_structured_sensitive_key_value_redacted():
    ev = redaction.redact_event({
        "id": "e1", "node_id": "n1", "event_type": "tool", "ts": "t",
        "data": {"args": {"api_key": "plainvalue123456", "url": "https://ok.com"}},
    })
    assert ev["data"]["args"]["api_key"] != "plainvalue123456"
    assert ev["data"]["args"]["api_key"].startswith("[REDACTED:")
    # Non-sensitive sibling untouched.
    assert ev["data"]["args"]["url"] == "https://ok.com"


def test_structural_and_count_fields_untouched():
    ev = redaction.redact_event({
        "id": "e1", "node_id": "n1", "event_type": "model.completed", "ts": "t",
        "model": "claude-opus-4-7", "token_count": 1234,
        "data": {"token_count": 99, "max_tokens": 4096},
    })
    assert ev["model"] == "claude-opus-4-7"
    assert ev["token_count"] == 1234
    assert ev["data"]["token_count"] == 99  # count, not a secret
    assert ev["data"]["max_tokens"] == 4096


def test_disabled_via_env(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_REDACT", "0")
    raw = "sk-ABCDEFGHIJKLMNOP01"
    assert redaction.redact_text(raw) == raw
    ev = {"id": "e", "node_id": "n", "event_type": "t", "ts": "x",
          "data": {"api_key": "plainvalue123456"}}
    assert redaction.redact_event(ev)["data"]["api_key"] == "plainvalue123456"


def test_never_crashes_on_bad_input():
    assert redaction.redact_text("") == ""
    assert redaction.redact_event({"id": 1}) == {"id": 1}
    # non-dict passthrough
    assert redaction.redact_event(None) is None  # type: ignore[arg-type]


def test_ingest_redacts_at_chokepoint(tmp_path, monkeypatch):
    """LocalStore.ingest() must scrub secrets before the event is queued for
    persistence. We inspect the in-memory ring (not a query round-trip) so the
    assertion holds regardless of whether a real sync daemon is running and
    serving query_events from its own store."""
    import sys
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    # High batch so ingest() does NOT auto-flush — the event stays in the ring.
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "100000")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "3600")
    monkeypatch.delenv("CLAWMETRY_REDACT", raising=False)
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Raw class (not get_store(), which may return a daemon proxy) so we can
    # inspect the in-memory ring directly.
    store = ls.LocalStore()
    try:
        store.ingest({
            "id": "evt-redact-1", "node_id": "n1", "session_id": "redact-test",
            "event_type": "tool.call", "ts": "2026-05-27T00:00:00Z",
            "data": {"args": {"authorization": "Bearer secrettoken12345abc"},
                     "text": "my key sk-ABCDEFGHIJKLMNOP01 leaked"},
        })
        queued = repr(list(store._ring))
        assert "secrettoken12345abc" not in queued
        assert "sk-ABCDEFGHIJKLMNOP01" not in queued
        assert "[REDACTED:" in queued
        # Structural identifier preserved (used for indexing/dedup).
        assert "evt-redact-1" in queued
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass
