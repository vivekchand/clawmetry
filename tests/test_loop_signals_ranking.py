"""``/api/loop-signals`` ranks by what a signal costs to ignore.

Before this, the Brain loop badge listed signals newest-first, so a two-cent
"continued after a failed command" could sit above a session that had burned
$170 while looping, and the OSS single-row teaser showed whichever signal was
most recent rather than the one worth acting on.

Pinned here:

* ordering is money, then severity, then recency;
* the OSS Pro-cap keeps the COSTLIEST row, not the newest;
* the money and the plain-words headline are flattened out of the ``details``
  blob, so a renderer cannot silently forget to parse it;
* rows with no cost data still order sensibly and never invent a number.

The store is faked at ``_ls_call``: this is a test of the route's ranking, and
the DuckDB round-trip is covered in ``tests/test_detectors_behavioural.py``.
"""
from __future__ import annotations

import json

import pytest
from flask import Flask

import routes.health as health_mod
from routes.health import bp_health


@pytest.fixture
def client(monkeypatch):
    # Pro by default so the row cap does not hide the ordering under test.
    monkeypatch.setattr(health_mod, "_ls_call", lambda *a, **k: [])
    app = Flask(__name__)
    app.register_blueprint(bp_health)
    return app.test_client()


def _signal(sid, kind, severity, at_risk, count=8, last_seen="2026-06-11T10:00:00",
            basis="burn_rate", as_string=False):
    details = {"source": "daemon_detector", "kind": kind,
               "message": f"{kind} happened", "detail": "why it happened",
               "evidence": {"tool_calls": count},
               "spend_at_risk_usd": at_risk, "spend_basis": basis}
    return {"session_id": sid, "signature": f"daemon_detect_{kind}",
            "repeat_count": count, "severity": severity,
            "first_seen": last_seen, "last_seen": last_seen,
            "agent_type": "claude_code",
            "details": json.dumps(details) if as_string else details}


def _serve(monkeypatch, rows, is_pro=True):
    monkeypatch.setattr(health_mod, "_ls_call",
                        lambda method, **kw: rows if method == "query_recent_loop_signals" else None)
    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: is_pro)


def test_costliest_signal_sorts_first(monkeypatch, client):
    """Acceptance criteria proven here:

    AC-OBS-CEA-020.4
    """
    rows = [
        _signal("cheap", "action_discrepancy", "info", 0.02,
                last_seen="2026-06-11T12:00:00"),          # newest
        _signal("expensive", "stuck_loop", "warning", 171.0,
                last_seen="2026-06-11T09:00:00"),          # oldest
    ]
    _serve(monkeypatch, rows)
    body = json.loads(client.get("/api/loop-signals").data)
    assert [s["session_id"] for s in body["signals"]] == ["expensive", "cheap"]
    assert body["spend_at_risk_usd"] == pytest.approx(171.02)


def test_severity_breaks_the_tie_when_no_cost_is_known(monkeypatch, client):
    """Acceptance criteria proven here:

    AC-OBS-CEA-020.4
    """
    rows = [_signal("info-one", "action_discrepancy", "info", 0),
            _signal("warn-one", "stuck_loop", "warning", 0),
            _signal("crit-one", "privilege_change", "critical", 0)]
    _serve(monkeypatch, rows)
    body = json.loads(client.get("/api/loop-signals").data)
    assert [s["session_id"] for s in body["signals"]][0] == "crit-one"
    assert body["spend_at_risk_usd"] == 0


def test_oss_teaser_row_is_the_costliest_not_the_newest(monkeypatch, client):
    """Acceptance criteria proven here:

    AC-OBS-CEA-020.6
    """
    rows = [_signal("cheap-new", "stuck_loop", "warning", 0.05,
                    last_seen="2026-06-11T12:00:00"),
            _signal("expensive-old", "no_progress", "warning", 42.0,
                    last_seen="2026-06-11T08:00:00")]
    _serve(monkeypatch, rows, is_pro=False)
    body = json.loads(client.get("/api/loop-signals").data)
    assert body["capped_pro_gated"] is True
    assert body["count"] == 1
    assert body["total_count"] == 2
    assert body["signals"][0]["session_id"] == "expensive-old"


def test_money_and_headline_are_flattened_for_the_renderer(monkeypatch, client):
    """Acceptance criteria proven here:

    AC-OBS-CEA-020.2
    """
    _serve(monkeypatch, [_signal("s1", "credential_access", "critical", 3.5)])
    row = json.loads(client.get("/api/loop-signals").data)["signals"][0]
    assert row["kind"] == "credential_access"
    assert row["title"] == "credential_access happened"
    assert row["spend_at_risk_usd"] == 3.5
    assert row["spend_basis"] == "burn_rate"


def test_details_arriving_as_a_json_string_are_still_read(monkeypatch, client):
    # The daemon proxy and the cloud relay can hand back the BLOB as text.
    _serve(monkeypatch, [_signal("s1", "stuck_loop", "warning", 9.0, as_string=True)])
    row = json.loads(client.get("/api/loop-signals").data)["signals"][0]
    assert row["spend_at_risk_usd"] == 9.0
    assert row["kind"] == "stuck_loop"


def test_proxy_signals_without_details_survive(monkeypatch, client):
    """Acceptance criteria proven here:

    AC-OBS-CEA-020.3
    """
    # clawmetry/proxy.py's LoopDetector writes rows with a different details
    # shape (and sometimes none). They must rank last, not crash.
    _serve(monkeypatch, [{"session_id": "proxy", "signature": "hash:abc",
                          "repeat_count": 12, "severity": "warning",
                          "first_seen": "x", "last_seen": "x",
                          "agent_type": "openclaw", "details": None},
                         _signal("detector", "stuck_loop", "warning", 5.0)])
    body = json.loads(client.get("/api/loop-signals").data)
    assert body["signals"][0]["session_id"] == "detector"
    proxy_row = body["signals"][1]
    # A signal nobody could price is NOT a $0.00 signal. It used to serialise
    # as 0.0, which renders as a free incident sitting at the bottom of a list
    # sorted by money; it is now null and carries an unknown basis, so the
    # badge says "no basis" where the dollars would have been.
    assert proxy_row["spend_at_risk_usd"] is None
    assert proxy_row["spend_basis"] == "unknown"
    assert proxy_row["provenance"]["spend_at_risk_usd"]["basis"] == "unknown"
    assert proxy_row["provenance"]["spend_at_risk_usd"]["reason"]
    assert proxy_row["title"] == ""


def test_store_outage_returns_an_empty_list_not_an_error(monkeypatch, client):
    monkeypatch.setattr(health_mod, "_ls_call", lambda *a, **k: None)
    resp = client.get("/api/loop-signals")
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body["signals"] == []
    assert body["spend_at_risk_usd"] == 0
