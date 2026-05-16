"""MOAT E2E: cloud-sync roundtrip (OSS-side half, mock cloud) — issue #1456.

DuckDB → _build_brain_cache_pushes (encrypt) → mock cloud POST
/ingest/heartbeat (store ciphertext) → mock cloud GET /api/cloud/brain
(serve blob back) → decrypt_payload (client-side) → original payload.

Companion to test_moat_send_message_e2e.py (LOCAL half). The real-cloud
fixture is the next PR; envelope shape + cache key + AES-256-GCM contract
tested here are what the cloud side must agree with.

Memory respects: project_local_compute_cloud_display (no plaintext on the
wire); feedback_synthetic_tests_missed_real_event_shape (v3 fixture shape).
"""
from __future__ import annotations

import http.server
import importlib
import json
import os
import socket
import sys
import threading
import time
import uuid
from urllib.parse import quote, unquote
import urllib.request

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


class _CloudState:
    """In-memory dict keyed by ``cache_push.key`` → ciphertext blob."""

    def __init__(self) -> None:
        self.cache: dict[str, str] = {}
        self.last_request_payload: dict | None = None


class _MockCloudHandler(http.server.BaseHTTPRequestHandler):
    state: _CloudState  # set on the class per-test

    def log_message(self, *_a, **_kw) -> None:  # noqa: D401
        return

    def _json(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            payload = {}
        self.state.last_request_payload = payload
        if self.path == "/ingest/heartbeat":
            for entry in payload.get("cache_pushes") or []:
                k, b = entry.get("key"), entry.get("blob")
                if k and isinstance(b, str):
                    self.state.cache[k] = b
            return self._json(200, {"sync_allowed": True, "pending_queries": []})
        if self.path == "/ingest/events":
            node = payload.get("node_id") or "unknown"
            if isinstance(payload.get("blob"), str):
                self.state.cache[f"events:{node}:latest"] = payload["blob"]
            return self._json(200, {"ok": True})
        return self._json(404, {"error": f"unknown path {self.path}"})

    def do_GET(self) -> None:  # noqa: N802
        # /api/cloud/brain?key=brain:<owner_hash>:<node_id>:recent
        if self.path.startswith("/api/cloud/brain"):
            qs = self.path.split("?", 1)[1] if "?" in self.path else ""
            key = next(
                (unquote(p[4:]) for p in qs.split("&") if p.startswith("key=")),
                "",
            )
            blob = self.state.cache.get(key)
            if blob is None:
                return self._json(404, {"error": "cache miss", "key": key})
            return self._json(200, {
                "blob": blob, "key": key,
                "_source": "cache", "_shape": "brain_history",
            })
        return self._json(404, {"error": f"unknown path {self.path}"})


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Hermetic DuckDB + reloaded sync module + running mock cloud server."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)

    # v3 OpenClaw shape (event_type=message + message.usage block) per
    # feedback_synthetic_tests_missed_real_event_shape.md.
    store = ls.get_store()
    for i in range(5):
        ts = f"2026-05-13T12:{i:02d}:00+00:00"
        store.ingest({
            "id":          str(uuid.uuid4()),
            "node_id":     "agent+moat-cloud-roundtrip",
            "agent_id":    "main",
            "session_id":  "sess-cloud-roundtrip",
            "event_type":  "message",
            "ts":          ts,
            "data": {
                "type": "message", "timestamp": ts,
                "message": {
                    "role":    "assistant",
                    "content": [{"type": "text", "text": f"hello cloud {i}"}],
                    "model":   "claude-opus-4-7",
                    "usage":   {"input_tokens": 10, "output_tokens": 5},
                },
            },
            "cost_usd":    0.0012,
            "token_count": 15,
            "model":       "claude-opus-4-7",
        })
    for _ in range(80):
        if store.health()["ring_depth"] == 0:
            break
        time.sleep(0.05)

    cloud_state = _CloudState()
    _MockCloudHandler.state = cloud_state
    port = _free_port()
    httpd = http.server.HTTPServer(("127.0.0.1", port), _MockCloudHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    monkeypatch.setattr(s, "INGEST_URL", f"http://127.0.0.1:{port}", raising=False)

    config = {
        "node_id":         "node-roundtrip",
        "api_key":         "cm_test_roundtrip_token",
        "encryption_key":  s.generate_encryption_key(),
    }

    yield {
        "sync": s, "ls": ls, "store": store, "config": config,
        "cloud": cloud_state, "port": port,
    }

    httpd.shutdown()
    httpd.server_close()
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_envelope_shape_matches_documented_contract(env):
    """{key, ttl_s, blob} is the cross-repo contract with cloud. Any rename
    here silently drops every push on the floor without erroring."""
    s = env["sync"]
    pushes = s._build_brain_cache_pushes(env["config"])

    assert len(pushes) == 1, f"expected one cache_push, got {len(pushes)}"
    entry = pushes[0]
    assert set(entry) == {"key", "ttl_s", "blob"}, (
        f"envelope keys drifted; got {sorted(entry)}"
    )

    expected_owner = s._owner_hash_for_token(env["config"]["api_key"])
    assert entry["key"] == f"brain:{expected_owner}:node-roundtrip:recent"
    assert entry["ttl_s"] == s.BRAIN_CACHE_TTL_SEC
    assert isinstance(entry["blob"], str) and len(entry["blob"]) > 0
    # No plaintext leaks in the ciphertext.
    assert "hello cloud" not in entry["blob"]
    assert "claude-opus-4-7" not in entry["blob"]


def test_mock_cloud_receives_and_stores_ciphertext(env):
    """Heartbeat post: daemon sends, cloud stores blob under documented
    cache key. Asserts the cloud sees ONLY ciphertext on the wire."""
    s = env["sync"]
    assert s.send_heartbeat(env["config"]) is True

    payload = env["cloud"].last_request_payload
    assert payload is not None, "mock cloud never received the heartbeat"
    pushes = payload.get("cache_pushes") or []
    assert len(pushes) == 1, (
        f"heartbeat didn't attach cache_pushes; keys={list(payload)}"
    )

    wire = json.dumps(payload)
    assert "hello cloud" not in wire, "plaintext leaked onto the wire"
    assert "input_tokens" not in wire, "plaintext usage leaked onto the wire"

    owner = s._owner_hash_for_token(env["config"]["api_key"])
    cache_key = f"brain:{owner}:node-roundtrip:recent"
    assert cache_key in env["cloud"].cache
    assert env["cloud"].cache[cache_key] == pushes[0]["blob"]


def test_stored_ciphertext_decrypts_to_original_events(env):
    """Blob the cloud cached decrypts back to brain-history shape. If the
    cipher, nonce length, or base64 encoding drifts, this assert fires."""
    s = env["sync"]
    pushes = s._build_brain_cache_pushes(env["config"])
    decrypted = s.decrypt_payload(pushes[0]["blob"], env["config"]["encryption_key"])

    assert decrypted["_shape"] == "brain_history"
    assert decrypted["_source"] == "local_store"
    assert decrypted["count"] == 5
    assert len(decrypted["events"]) == 5

    # v3 shape intact (not pre-flattened).
    ev0 = decrypted["events"][0]
    assert ev0.get("type") == "message"
    assert ev0.get("message", {}).get("role") == "assistant"
    assert ev0.get("message", {}).get("model") == "claude-opus-4-7"
    text_blocks = [
        b for b in ev0.get("message", {}).get("content", [])
        if b.get("type") == "text"
    ]
    assert text_blocks and "hello cloud" in text_blocks[0]["text"]


def test_cloud_brain_endpoint_serves_blob_back(env):
    """Dashboard fetch path: /api/cloud/brain returns ciphertext for the
    browser to unwrap. Response shape matches unwrapListAsync expectations."""
    s = env["sync"]
    assert s.send_heartbeat(env["config"]) is True

    owner = s._owner_hash_for_token(env["config"]["api_key"])
    key = f"brain:{owner}:node-roundtrip:recent"
    url = f"http://127.0.0.1:{env['port']}/api/cloud/brain?key={quote(key)}"
    with urllib.request.urlopen(url, timeout=5) as resp:
        body = json.loads(resp.read())

    assert body["_source"] == "cache"
    assert body["_shape"] == "brain_history"
    assert isinstance(body["blob"], str) and len(body["blob"]) > 0
    # Served blob === stored blob (no re-encoding mishap).
    assert body["blob"] == env["cloud"].cache[key]


def test_dashboard_client_decrypt_reproduces_original(env):
    """Final leg: served ciphertext, decrypted with the user's key (the
    dashboard JS reads it from localStorage as cm-enc-key-<node_id>),
    reproduces the original dict byte-for-byte. AES-256-GCM (nonce||ct,
    base64url) is the contract shared between sync.decrypt_payload (Py)
    and window.decryptBlob (cloud JS); drift on either side flips red."""
    s = env["sync"]

    pushes_pre = s._build_brain_cache_pushes(env["config"])
    expected_dict = s.decrypt_payload(
        pushes_pre[0]["blob"], env["config"]["encryption_key"]
    )
    assert s.send_heartbeat(env["config"]) is True

    owner = s._owner_hash_for_token(env["config"]["api_key"])
    url = (
        f"http://127.0.0.1:{env['port']}/api/cloud/brain"
        f"?key={quote(f'brain:{owner}:node-roundtrip:recent')}"
    )
    with urllib.request.urlopen(url, timeout=5) as resp:
        served = json.loads(resp.read())

    actual_dict = s.decrypt_payload(
        served["blob"], env["config"]["encryption_key"]
    )

    assert actual_dict == expected_dict, (
        "client-side decrypt produced a different dict than the daemon "
        "originally encrypted; AES-GCM contract has drifted"
    )
    # And the payload is fully renderable (the issue #1456 regression class:
    # cipher-OK-but-empty-dict silently kills cloud Brain).
    assert actual_dict["count"] == 5
    assert len(actual_dict["events"]) == 5
    assert actual_dict["_shape"] == "brain_history"
