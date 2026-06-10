"""Regression: clawmetry.sync._post must tolerate an empty / 204 response body.

The cloud /ingest/cache endpoint answers ("", 204) after storing a result
(process_control kill/pause/resume, cron_killall, dives_query, ...). Before
the fix, ``_post`` did ``json.loads(resp.read())`` unconditionally, so every
successful post-back raised ``json.JSONDecodeError`` ("Expecting value: line 1
column 1") which the action handlers logged as a spurious "cache post failed"
warning. The write had actually succeeded.

This test drives ``_post`` against a fake urlopen returning an empty body and
asserts it returns ``{}`` instead of raising.
"""
import io
import json
import urllib.request

import pytest

from clawmetry import sync


class _FakeResp:
    def __init__(self, body: bytes):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.mark.parametrize("body", [b"", b"   ", b"\n"])
def test_post_tolerates_empty_body(monkeypatch, body):
    monkeypatch.setattr(sync, "INGEST_URL", "https://ingest.example.com")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=0: _FakeResp(body))
    # Must not raise; an empty body means "stored, nothing to return" -> {}.
    out = sync._post("/ingest/cache", {"node_id": "n1", "blob": "x"}, "cm_test")
    assert out == {}


def test_post_still_parses_json_body(monkeypatch):
    monkeypatch.setattr(sync, "INGEST_URL", "https://ingest.example.com")
    payload = {"ok": True, "sync_allowed": True}
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda req, timeout=0: _FakeResp(json.dumps(payload).encode())
    )
    out = sync._post("/ingest/heartbeat", {"node_id": "n1"}, "cm_test")
    assert out["ok"] is True and out["sync_allowed"] is True
