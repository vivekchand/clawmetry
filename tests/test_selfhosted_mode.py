"""ClawMetry Enterprise self-hosted mode (SELF_HOSTED=true).

Covers: the flag, token/admin auth helpers, the ingest blueprint speaking the
daemon's wire protocol against SQLite, audit export, and the cloud-only
phone-homes short-circuiting when the endpoint is repointed.
"""
import base64
import json

import pytest

flask = pytest.importorskip("flask")

from clawmetry import endpoints, selfhosted  # noqa: E402
from routes import selfhosted_ingest as shi  # noqa: E402

TOKEN = "cm_test_token_1"
ADMIN_AUTH = "Basic " + base64.b64encode(b"admin:pw").decode()


@pytest.fixture
def sh_app(monkeypatch, tmp_path):
    monkeypatch.setenv("SELF_HOSTED", "true")
    monkeypatch.setenv("CLAWMETRY_API_TOKENS", f"{TOKEN}, cm_second_token")
    monkeypatch.setenv("CLAWMETRY_ADMIN_USER", "admin")
    monkeypatch.setenv("CLAWMETRY_ADMIN_PASSWORD", "pw")
    monkeypatch.delenv("CLAWMETRY_SELF_HOSTED_E2E", raising=False)
    monkeypatch.setenv("CLAWMETRY_SELF_HOSTED_DB", str(tmp_path / "selfhosted.db"))
    shi._reset_for_tests()
    app = flask.Flask(__name__)
    app.register_blueprint(shi.bp_selfhosted)
    return app.test_client()


# ── Flag + auth helpers ─────────────────────────────────────────────────────


def test_self_hosted_flag_values(monkeypatch):
    monkeypatch.delenv("SELF_HOSTED", raising=False)
    monkeypatch.delenv("CLAWMETRY_SELF_HOSTED", raising=False)
    assert selfhosted.is_self_hosted() is False
    for value in ("1", "true", "TRUE", "yes", "on"):
        monkeypatch.setenv("SELF_HOSTED", value)
        assert selfhosted.is_self_hosted() is True
    monkeypatch.setenv("SELF_HOSTED", "0")
    assert selfhosted.is_self_hosted() is False
    monkeypatch.delenv("SELF_HOSTED")
    monkeypatch.setenv("CLAWMETRY_SELF_HOSTED", "true")
    assert selfhosted.is_self_hosted() is True


def test_check_api_key(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_API_TOKENS", "cm_a, cm_b")
    assert selfhosted.check_api_key("cm_a")
    assert selfhosted.check_api_key("cm_b")
    assert not selfhosted.check_api_key("cm_c")
    assert not selfhosted.check_api_key("")
    monkeypatch.delenv("CLAWMETRY_API_TOKENS")
    assert not selfhosted.check_api_key("cm_a")


def test_admin_basic_auth(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ADMIN_USER", "admin")
    monkeypatch.setenv("CLAWMETRY_ADMIN_PASSWORD", "pw")
    good = "Basic " + base64.b64encode(b"admin:pw").decode()
    bad = "Basic " + base64.b64encode(b"admin:nope").decode()
    assert selfhosted.check_admin_basic_auth(good)
    assert not selfhosted.check_admin_basic_auth(bad)
    assert not selfhosted.check_admin_basic_auth(None)
    monkeypatch.delenv("CLAWMETRY_ADMIN_PASSWORD")
    # No creds configured -> nothing authenticates (no default password).
    assert not selfhosted.check_admin_basic_auth(good)


# ── Ingest protocol ─────────────────────────────────────────────────────────


def test_auth_endpoint(sh_app):
    r = sh_app.post("/auth", json={"api_key": "cm_wrong", "hostname": "box1"})
    assert r.status_code == 401
    r = sh_app.post("/auth", json={"api_key": TOKEN, "hostname": "box1"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["ok"] is True
    assert body["plan"] == "enterprise"
    assert body["e2e"] is False  # plaintext-inside-VPC is the default


def test_auth_e2e_flag(sh_app, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_SELF_HOSTED_E2E", "1")
    r = sh_app.post("/auth", json={"api_key": TOKEN, "hostname": "box1"})
    assert r.get_json()["e2e"] is True


def test_register_disabled(sh_app):
    r = sh_app.post("/api/register", json={"hostname": "x"})
    assert r.status_code == 403
    assert r.get_json()["error"] == "registration_disabled"


def test_heartbeat_roundtrip_with_relay(sh_app):
    headers = {"X-Api-Key": TOKEN}
    # Queue a relay query for node-1 (admin API).
    r = sh_app.post(
        "/api/selfhosted/subscribe",
        json={"node_id": "node-1", "shape": "events", "cache_key": "k1", "args": {}},
        headers={"Authorization": ADMIN_AUTH},
    )
    assert r.status_code == 200

    hb = {
        "node_id": "node-1",
        "platform": "Linux",
        "version": "0.12.601",
        "cache_pushes": [{"key": "brain:x:node-1:recent", "ttl_s": 60, "blob": "abc"}],
    }
    r = sh_app.post("/ingest/heartbeat", json=hb, headers=headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body["sync_allowed"] is True
    assert body["plan"] == "enterprise"
    assert body["pending_queries"] == [{"shape": "events", "cache_key": "k1", "args": {}}]

    # Queue drained — second heartbeat gets nothing.
    r = sh_app.post("/ingest/heartbeat", json=hb, headers=headers)
    assert r.get_json()["pending_queries"] == []

    # The cache push is readable back.
    r = sh_app.get(
        "/api/cloud/cache/brain:x:node-1:recent",
        headers={"Authorization": ADMIN_AUTH},
    )
    assert r.status_code == 200
    assert r.get_json()["blob"] == "abc"

    # Node registered.
    r = sh_app.get("/api/selfhosted/nodes", headers={"Authorization": ADMIN_AUTH})
    nodes = r.get_json()["nodes"]
    assert len(nodes) == 1 and nodes[0]["node_id"] == "node-1"
    assert nodes[0]["version"] == "0.12.601"


def test_heartbeat_requires_token(sh_app):
    r = sh_app.post("/ingest/heartbeat", json={"node_id": "n"})
    assert r.status_code == 401


def test_events_plaintext_extracted_encrypted_opaque(sh_app):
    headers = {"X-Api-Key": TOKEN}
    plain = {
        "node_id": "node-1",
        "session_file": "s.jsonl",
        "events": [
            {
                "id": "ev1",
                "session_id": "sess-1",
                "event_type": "tool.call",
                "ts": "2026-07-30T10:00:00+00:00",
                "agent_type": "openclaw",
                "data": {"name": "Bash", "input": {"command": "ls"}},
                "token_count": 12,
            }
        ],
    }
    assert sh_app.post("/ingest/events", json=plain, headers=headers).status_code == 200

    encrypted = {"node_id": "node-1", "encrypted": True, "blob": "ZmFrZQ=="}
    assert (
        sh_app.post("/ingest/events", json=encrypted, headers=headers).status_code
        == 200
    )

    # Export sees exactly the one plaintext event.
    r = sh_app.get("/api/export/events", headers={"Authorization": ADMIN_AUTH})
    lines = [json.loads(ln) for ln in r.get_data(as_text=True).splitlines() if ln]
    assert len(lines) == 1
    assert lines[0]["id"] == "ev1"
    assert lines[0]["event_type"] == "tool.call"
    assert lines[0]["data"] == {"name": "Bash", "input": {"command": "ls"}}


def test_export_time_range_and_csv_and_auth(sh_app):
    headers = {"X-Api-Key": TOKEN}
    for i, ts in enumerate(
        ["2026-07-01T00:00:00", "2026-07-15T00:00:00", "2026-07-31T00:00:00"]
    ):
        sh_app.post(
            "/ingest/events",
            json={
                "node_id": "n",
                "events": [
                    {"id": f"e{i}", "session_id": "s", "event_type": "message", "ts": ts}
                ],
            },
            headers=headers,
        )

    # Unauthenticated -> 401.
    assert sh_app.get("/api/export/events").status_code == 401
    # Node token is also accepted for export.
    r = sh_app.get("/api/export/events?from=2026-07-10&to=2026-07-20", headers=headers)
    lines = [json.loads(ln) for ln in r.get_data(as_text=True).splitlines() if ln]
    assert [ln["id"] for ln in lines] == ["e1"]

    r = sh_app.get(
        "/api/export/events?format=csv", headers={"Authorization": ADMIN_AUTH}
    )
    rows = r.get_data(as_text=True).splitlines()
    assert rows[0].startswith("id,node_id,agent_type")
    assert len(rows) == 4  # header + 3 events


def test_sessions_upsert_and_status(sh_app):
    headers = {"X-Api-Key": TOKEN}
    sess = {"session_id": "s1", "status": "active", "total_tokens": 10}
    payload = {"node_id": "n1", "sessions": [sess]}
    assert sh_app.post("/ingest/sessions", json=payload, headers=headers).status_code == 200
    sess["total_tokens"] = 20
    assert sh_app.post("/ingest/sessions", json=payload, headers=headers).status_code == 200

    r = sh_app.get("/api/selfhosted/status", headers={"Authorization": ADMIN_AUTH})
    counts = r.get_json()["counts"]
    assert counts["sessions"] == 1  # upsert, not append
    assert counts["ingest_log"] == 2  # immutable log keeps both


def test_approvals_flow(sh_app):
    bearer = {"Authorization": f"Bearer {TOKEN}"}
    r = sh_app.post(
        "/api/approvals/request", json={"id": "ap1", "node_id": "n"}, headers=bearer
    )
    assert r.status_code == 200
    assert sh_app.get("/api/approvals/ap1", headers=bearer).get_json()["status"] == "pending"
    r = sh_app.post(
        "/api/selfhosted/approvals/ap1/decision",
        json={"status": "approved"},
        headers={"Authorization": ADMIN_AUTH},
    )
    assert r.status_code == 200
    assert sh_app.get("/api/approvals/ap1", headers=bearer).get_json()["status"] == "approved"


# ── Cloud-only phone-homes gate on custom endpoint ──────────────────────────


def test_anon_analytics_skipped_on_custom_endpoint(monkeypatch, tmp_path):
    from routes import meta as meta_mod

    calls = []

    class _FakeUrllib:
        @staticmethod
        def Request(*a, **k):
            return object()

        @staticmethod
        def urlopen(*a, **k):
            calls.append(a)

            class _R:
                def close(self):
                    pass

            return _R()

    import urllib.request as _real_ur

    monkeypatch.setattr(_real_ur, "Request", _FakeUrllib.Request)
    monkeypatch.setattr(_real_ur, "urlopen", _FakeUrllib.urlopen)
    monkeypatch.setattr(endpoints, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(endpoints, "_cfg_cache", None)

    monkeypatch.setenv("CLAWMETRY_ENDPOINT", "https://corp.example")
    meta_mod._anon_forward_cloud({"k": "v"})
    assert calls == []  # short-circuited before any network call

    monkeypatch.delenv("CLAWMETRY_ENDPOINT")
    meta_mod._anon_forward_cloud({"k": "v"})
    assert len(calls) == 1  # managed cloud still forwards


def test_telemetry_skipped_on_custom_endpoint(monkeypatch, tmp_path):
    from clawmetry import telemetry as tel

    monkeypatch.setattr(endpoints, "CONFIG_PATH", str(tmp_path / "config.json"))
    monkeypatch.setattr(endpoints, "_cfg_cache", None)
    monkeypatch.delenv("CLAWMETRY_TELEMETRY_URL", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)

    # Custom endpoint -> telemetry URL resolves to "" -> both send workers
    # bail before posting anything.
    monkeypatch.setenv("CLAWMETRY_ENDPOINT", "https://corp.example")
    assert tel._resolve_telemetry_url() == ""

    # Managed cloud -> default URL.
    monkeypatch.delenv("CLAWMETRY_ENDPOINT")
    assert tel._resolve_telemetry_url() == tel.TELEMETRY_URL_DEFAULT

    # Explicit re-point always wins, even with a custom endpoint.
    monkeypatch.setenv("CLAWMETRY_ENDPOINT", "https://corp.example")
    monkeypatch.setenv("CLAWMETRY_TELEMETRY_URL", "https://tel.corp.example")
    assert tel._resolve_telemetry_url() == "https://tel.corp.example"


# ── Fleet page v1 ───────────────────────────────────────────────────────────


def test_fleet_page_requires_admin(sh_app):
    assert sh_app.get("/selfhosted").status_code == 401


def test_fleet_page_empty_state(sh_app):
    r = sh_app.get("/selfhosted", headers={"Authorization": ADMIN_AUTH})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "No nodes yet" in body
    assert "clawmetry connect" in body


def test_fleet_page_lists_heartbeating_node(sh_app):
    hb = {"node_id": "fleet-node-1", "platform": "Linux", "version": "0.12.606"}
    assert (
        sh_app.post("/ingest/heartbeat", json=hb, headers={"X-Api-Key": TOKEN}).status_code
        == 200
    )
    r = sh_app.get("/selfhosted", headers={"Authorization": ADMIN_AUTH})
    body = r.get_data(as_text=True)
    assert "fleet-node-1" in body
    assert "0.12.606" in body
    assert "online" in body  # heartbeat just happened -> liveness green
    # HTML escaping sanity: node ids render inside <code>, not raw script.
    assert "<script" not in body.lower()
