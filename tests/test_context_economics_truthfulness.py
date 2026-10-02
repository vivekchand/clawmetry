from flask import Flask

from routes import context_economics


def _client(monkeypatch, payload):
    monkeypatch.setattr(context_economics, "_ls_call", lambda *args, **kwargs: payload)
    app = Flask(__name__)
    app.register_blueprint(context_economics.bp_context_economics)
    return app.test_client()


def test_unmeasured_compaction_is_not_reported_as_zero(monkeypatch):
    client = _client(monkeypatch, {
        "utilization": [],
        "compactions": [{
            "session_id": "s1",
            "trigger": "proactive",
            "tokens_before": None,
            "tokens_after": None,
            "reclaimed": None,
            "measurement_status": "unavailable",
        }],
        "overflow_sessions": [],
    })

    response = client.get("/api/context-economics")
    body = response.get_json()

    assert response.status_code == 200
    assert body["compactions"][0]["measurement_status"] == "unavailable"
    assert body["compactions"][0]["reclaimed"] is None
    assert body["summary"]["reclaimed_data_available"] is False


def test_reclaimed_summary_uses_only_observed_measurements(monkeypatch):
    client = _client(monkeypatch, {
        "utilization": [],
        "compactions": [
            {"session_id": "s1", "trigger": "proactive", "reclaimed": 120,
             "measurement_status": "observed"},
            {"session_id": "s2", "trigger": "proactive", "reclaimed": None,
             "measurement_status": "unavailable"},
        ],
        "overflow_sessions": [],
    })

    body = client.get("/api/context-economics").get_json()

    assert body["summary"]["total_reclaimed"] == 120
    assert body["summary"]["reclaimed_known_count"] == 1
    assert body["summary"]["reclaimed_data_available"] is True
