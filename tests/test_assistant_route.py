"""Contract tests for the read-only assistant route.

The provider and local store are mocked deliberately.  These tests exercise the
HTTP contract and the route's data handling without making model calls or
depending on a developer's credentials or DuckDB contents.
"""

import json
from pathlib import Path

import pytest
from flask import Flask

from clawmetry import assistant_service as assistant
from tests.assistant_test_support import daemon_adapter


def test_dashboard_registers_the_assistant_blueprint():
    dashboard_source = (Path(__file__).parents[1] / "dashboard.py").read_text()

    assert "bp_assistant" in dashboard_source
    assert "app.register_blueprint(bp_assistant)" in dashboard_source


def test_assistant_store_methods_are_available_through_the_daemon_contract():
    from clawmetry.local_store import LocalStore
    from routes.local_query import _DAEMON_METHODS

    expected = {
        "query_assistant_sql",
        "query_assistant_conversations",
        "query_assistant_conversation",
        "save_assistant_conversation",
    }

    assert expected <= _DAEMON_METHODS
    assert all(callable(getattr(LocalStore, name, None)) for name in expected)


@pytest.fixture()
def client(daemon_adapter):
    app = Flask(__name__)
    app.register_blueprint(assistant.bp_assistant)
    with assistant._conversation_lock:
        assistant._conversations_in_flight.clear()
    try:
        yield app.test_client()
    finally:
        with assistant._conversation_lock:
            assistant._conversations_in_flight.clear()


def _provider(monkeypatch, mode="anthropic", credential="sk-ant-test-secret"):
    calls = []

    def fake_provider(requested="auto", api_key=None):
        calls.append((requested, api_key))
        return mode, api_key or credential

    monkeypatch.setattr(assistant, "_provider", fake_provider)
    return calls


def _generator(monkeypatch, plans, *, answer="Grounded answer"):
    calls = []
    remaining = iter(plans if isinstance(plans, list) else [plans])

    def fake_generate(mode, credential, system, prompt):
        calls.append({
            "mode": mode,
            "credential": credential,
            "system": system,
            "prompt": prompt,
        })
        if system.startswith(assistant._PLAN):
            return json.dumps(next(remaining))
        if system == assistant._SYNTHESIS:
            return answer
        raise AssertionError("unexpected assistant prompt")

    monkeypatch.setattr(assistant, "_stream_generate", lambda control, mode, credential, system, prompt, **kw: fake_generate(mode, credential, system, prompt))
    return calls


def _chat_store(monkeypatch, *, results=None, conversation=None, save=True):
    calls = []
    saved = []
    results = results or {}

    def fake_store(method, **kwargs):
        calls.append((method, kwargs))
        if method == "query_assistant_sql":
            sql = kwargs["sql"]
            if sql == "SELECT COUNT(*) AS sessions FROM sessions":
                return {"rows": [{"sessions": 3}], "truncated": False}
            return results.get(sql, {"rows": [], "truncated": False})
        if method == "query_assistant_conversation":
            return conversation
        if method == "save_assistant_conversation":
            saved.append(kwargs)
            return save
        raise AssertionError(method)

    monkeypatch.setattr(assistant, "_store", fake_store)
    return calls, saved


@pytest.mark.parametrize(
    ("payload", "status"),
    [
        (None, 400),
        ({}, 400),
        ({"message": ""}, 400),
        ({"message": "x" * 4001}, 400),
        ({"message": "hello", "provider": "unknown"}, 400),
        ({"message": "hello", "api_key": "too short"}, 400),
        ({"message": "hello", "conversation_id": "bad/id"}, 400),
    ],
)
def test_chat_rejects_malformed_requests(client, monkeypatch, payload, status):
    _provider(monkeypatch)
    if payload is None:
        response = client.post(
            "/api/assistant/chat",
            data="not-json",
            content_type="application/json",
        )
    else:
        response = client.post("/api/assistant/chat", json=payload)

    assert response.status_code == status
    assert response.get_json()["error"]


def test_chat_requires_credentials_before_using_the_store(client, monkeypatch):
    provider_calls = _provider(monkeypatch, mode=None, credential=None)

    def fail_store(*args, **kwargs):
        raise AssertionError("the store must not be touched without credentials")

    monkeypatch.setattr(assistant, "_store", fail_store)
    response = client.post("/api/assistant/chat", json={"message": "How much did I spend?"})

    assert response.status_code == 412
    assert "credential" in response.get_json()["error"].lower() or "key" in response.get_json()["error"].lower()
    assert provider_calls == [("auto", None)]


def test_chat_reports_store_unavailable(client, monkeypatch):
    _provider(monkeypatch)
    _generator(monkeypatch, {"answer": "unused", "queries": []})
    monkeypatch.setattr(assistant, "_store", lambda *args, **kwargs: None)

    response = client.post("/api/assistant/chat", json={"message": "Show my sessions"})

    assert response.status_code == 503
    assert "local data store" in response.get_json()["error"].lower()


def test_conversation_read_distinguishes_store_failure_from_missing(client, monkeypatch):
    monkeypatch.setattr(assistant, "_store", lambda *args, **kwargs: None)

    response = client.get("/api/assistant/conversations/missing")

    assert response.status_code == 503
    assert "store" in response.get_json()["error"].lower()


def test_chat_returns_contract_and_preserves_sql_error_vs_empty_result(client, monkeypatch):
    _provider(monkeypatch)
    generate_calls = _generator(
        monkeypatch,
        {
            "answer": "There is no row for the first query.",
            "queries": [
                {"title": "Empty result", "sql": "SELECT empty", "visual": True, "chart_type": "table"},
                {"title": "Failed query", "sql": "SELECT broken", "visual": True, "chart_type": "table"},
            ],
        },
    )
    calls, saved = _chat_store(
        monkeypatch,
        results={
            "SELECT empty": {"rows": [], "truncated": False},
            "SELECT broken": {"rows": [], "error": "syntax error", "truncated": True},
        },
    )

    response = client.post("/api/assistant/chat", json={"message": "Compare these queries"})
    body = response.get_json()

    assert response.status_code == 200
    assert {"answer", "panels", "sources", "conversation_id"} <= body.keys()
    assert len(body["panels"]) == 2
    assert body["panels"][0]["rows"] == []
    assert "error" not in body["panels"][0] or body["panels"][0]["error"] is None
    assert body["panels"][1]["error"] == "syntax error"
    assert [{k: source[k] for k in ("label", "rows", "error", "truncated")} for source in body["sources"]] == [
        {"label": "[1] Empty result", "rows": 0, "error": None, "truncated": False},
        {"label": "[2] Failed query", "rows": 0, "error": "syntax error", "truncated": True},
    ]
    assert len(saved) == 1
    assert [call[0] for call in calls if call[0] != "dives_table_columns"] == [
        "query_assistant_sql",
        "query_assistant_sql",
        "query_assistant_sql",
        "save_assistant_conversation",
    ]
    assert len(generate_calls) == 2
    assert "syntax error" in generate_calls[-1]["prompt"]


def test_chat_normalizes_mixed_panel_shapes_without_executing_invalid_items(client, monkeypatch):
    _provider(monkeypatch)
    generations = _generator(
        monkeypatch,
        {
            "answer": "Mixed panels",
            "queries": [
                {
                    "title": "Valid chart",
                    "sql": "SELECT day, tokens FROM usage",
                    "visual": True,
                    "chart_type": "bar",
                    "x": "day",
                    "y": "tokens",
                },
                {
                    "title": "Bad chart shape",
                    "sql": "SELECT value FROM metrics",
                    "visual": True,
                    "chart_type": "scatter",
                    "x": "missing",
                    "y": "also_missing",
                },
                {"title": "Evidence only", "sql": "SELECT value FROM metrics LIMIT 1", "visual": False},
                "malformed query item",
                {"title": "Must be capped", "sql": "SELECT should_not_run", "visual": True},
            ],
        },
    )
    calls, _ = _chat_store(
        monkeypatch,
        results={
            "SELECT day, tokens FROM usage": {"rows": [{"day": "today", "tokens": 7}]},
            "SELECT value FROM metrics": {"rows": [{"value": 2}]},
            "SELECT value FROM metrics LIMIT 1": {"rows": [{"value": 2}]},
        },
    )

    response = client.post("/api/assistant/chat", json={"message": "Build mixed panels"})
    body = response.get_json()

    assert response.status_code == 200
    assert len(body["sources"]) == 3
    assert len(body["panels"]) == 2
    assert body["panels"][0]["chart_spec"] == {
        "chart_type": "bar",
        "x": "day",
        "y": "tokens",
        "title": "Valid chart",
    }
    assert body["panels"][1]["chart_spec"]["chart_type"] == "table"
    assert body["panels"][1]["chart_spec"]["x"] is None
    assert body["panels"][1]["chart_spec"]["y"] is None
    executed_sql = [kwargs["sql"] for method, kwargs in calls if method == "query_assistant_sql"]
    assert "SELECT should_not_run" not in executed_sql
    evidence = json.loads(generations[-1]["prompt"])["evidence"]
    assert [item["visual"] for item in evidence] == [True, True, False]
    assert "never call them a visual" in generations[-1]["system"]


def test_followup_uses_saved_history_and_returns_same_conversation(client, monkeypatch):
    _provider(monkeypatch)
    generate_calls = _generator(
        monkeypatch,
        [
            {"answer": "First answer", "queries": []},
            {"answer": "Follow-up answer", "queries": []},
        ],
    )
    stored_record = None
    saves = []

    def fake_store(method, **kwargs):
        nonlocal stored_record
        if method == "query_assistant_sql":
            return {"rows": [{"sessions": 1}], "truncated": False}
        if method == "query_assistant_conversation":
            return stored_record
        if method == "save_assistant_conversation":
            saves.append(kwargs)
            stored_record = {
                "conversation_id": kwargs["conversation_id"],
                "title": kwargs["title"],
                "messages": kwargs["messages"],
            }
            return True
        raise AssertionError(method)

    monkeypatch.setattr(assistant, "_store", fake_store)
    first = client.post("/api/assistant/chat", json={"message": "How many sessions?"})
    cid = first.get_json()["conversation_id"]
    second = client.post(
        "/api/assistant/chat",
        json={"message": "Which runtime had the most?", "conversation_id": cid},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.get_json()["conversation_id"] == cid
    assert "How many sessions?" in generate_calls[1]["prompt"]
    assert "First answer" in generate_calls[1]["prompt"]
    assert len(saves) == 2
    assert saves[1]["title"] == "How many sessions?"
    assert [m["role"] for m in saves[1]["messages"]] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]


def test_byok_key_is_used_but_never_returned_or_saved(client, monkeypatch):
    secret = "sk-ant-super-secret-value"
    provider_calls = _provider(monkeypatch)
    generate_calls = _generator(monkeypatch, {"answer": "Safe answer", "queries": []})
    _, saved = _chat_store(monkeypatch)

    response = client.post(
        "/api/assistant/chat",
        json={"message": "Summarize usage", "provider": "anthropic", "api_key": secret},
    )

    assert response.status_code == 200
    assert provider_calls == [("anthropic", secret)]
    assert secret not in json.dumps(response.get_json())
    assert secret not in json.dumps(saved)
    assert secret not in json.dumps([call["prompt"] for call in generate_calls])


def test_claude_harness_provider_is_supported_without_api_key(client, monkeypatch):
    provider_calls = _provider(monkeypatch, mode="claude_cli", credential="/usr/local/bin/claude")
    generate_calls = _generator(monkeypatch, {"answer": "Harness answer", "queries": []})
    _chat_store(monkeypatch)

    response = client.post(
        "/api/assistant/chat",
        json={"message": "Summarize setup", "provider": "claude_cli"},
    )

    assert response.status_code == 200
    assert response.get_json()["provider"] == "claude_cli"
    assert provider_calls == [("claude_cli", None)]
    assert generate_calls[0]["mode"] == "claude_cli"


def test_persistence_failure_is_visible_and_does_not_return_success(client, monkeypatch):
    _provider(monkeypatch)
    _generator(monkeypatch, {"answer": "Generated but not saved", "queries": []})
    calls, _ = _chat_store(monkeypatch, save=None)

    response = client.post("/api/assistant/chat", json={"message": "Save this answer"})

    assert response.status_code == 503
    assert "saved" in response.get_json()["error"].lower()
    assert calls[-1][0] == "save_assistant_conversation"


def test_concurrent_same_conversation_is_rejected(client, monkeypatch):
    _provider(monkeypatch)
    cid = "conversation-in-flight"
    with assistant._conversation_lock:
        assistant._conversations_in_flight.add(cid)

    response = client.post(
        "/api/assistant/chat",
        json={"message": "Do not race this", "conversation_id": cid},
    )

    assert response.status_code == 409
    assert "follow-up" in response.get_json()["error"].lower()


def test_status_exposes_provider_state_without_credentials(client, monkeypatch):
    _chat_store(monkeypatch)
    _provider(monkeypatch, mode=None, credential=None)
    monkeypatch.setattr(assistant, "find_claude_cli", lambda: None)

    response = client.get("/api/assistant/status")
    body = response.get_json()

    assert response.status_code == 200
    assert body["available"] is False
    assert body["provider"] is None
    serialized = json.dumps(body).lower()
    assert "api_key" not in serialized
    assert "credential" not in serialized
    assert body["managed"].get("balance_cents") is None
    assert body["managed"].get("starter_allowance_cents") is None


def test_managed_status_shows_only_verified_credit_balance(client, monkeypatch):
    _chat_store(monkeypatch)
    _provider(monkeypatch, mode='managed', credential='configured')
    monkeypatch.setattr(assistant.managed, 'configured', lambda: True)
    monkeypatch.setattr(assistant, '_managed_status', lambda window, **kw: {
        'available': True, 'balance_cents': 321, 'starter_allowance_cents': 500,
    })
    body = client.get('/api/assistant/status').get_json()
    assert body['managed']['balance_cents'] == 321
    assert body['managed']['starter_allowance_cents'] == 500
    assert body['managed']['checkout_available'] is True
    assert body['provider'] == 'managed'


def test_topup_requires_explicit_post_and_only_creates_checkout(client, monkeypatch):
    calls = []
    monkeypatch.setattr(assistant.managed, 'configured', lambda: True)
    monkeypatch.setattr(assistant.managed, 'checkout', lambda amount, **kw: calls.append(amount) or 'https://checkout.stripe.com/test')
    assert client.get('/api/assistant/credits/checkout').status_code == 405
    assert client.post('/api/assistant/credits/checkout', json={'amount_cents': 5000}).status_code == 400
    assert calls == []
    response = client.post('/api/assistant/credits/checkout', json={'amount_cents': 500})
    assert response.status_code == 200
    assert response.get_json()['url'].startswith('https://checkout.stripe.com/')
    assert calls == [500]


def test_empty_managed_credits_return_actionable_error(client, monkeypatch):
    _provider(monkeypatch, mode='managed', credential='configured')
    _chat_store(monkeypatch)

    def exhausted(*args):
        raise assistant.managed.ManagedAssistantCreditsError('credits unavailable')

    monkeypatch.setattr(assistant, '_stream_generate', lambda *a, **kw: exhausted())
    response = client.post('/api/assistant/chat', json={'message': 'Show my cost', 'provider': 'managed'})
    assert response.status_code == 402
    assert 'Top up' in response.get_json()['error']


@pytest.mark.parametrize("flag", ["CLAWMETRY_OFFLINE", "SELF_HOSTED", "CLAWMETRY_SELF_HOSTED"])
def test_private_modes_never_contact_assistant_providers(client, monkeypatch, flag):
    monkeypatch.setenv(flag, "1")
    _chat_store(monkeypatch)
    def forbidden(*args, **kwargs):
        pytest.fail("suppressed deployment contacted a provider")
    monkeypatch.setattr(assistant, "_provider", forbidden)
    monkeypatch.setattr(assistant.managed, "status", forbidden)
    monkeypatch.setattr(assistant.managed, "checkout", forbidden)
    state = client.get("/api/assistant/status").get_json()
    assert state["egress_suppressed"] is True
    assert state["available"] is False
    assert not any(p["available"] for p in state["providers"])
    assert client.post("/api/assistant/chat", json={"message": "test"}).status_code == 503
    assert client.post("/api/assistant/credits/checkout", json={"amount_cents": 500}).status_code == 503


def test_missing_local_data_is_explicit_without_managed_requests(client, monkeypatch):
    monkeypatch.setattr(assistant, "_store", lambda *a, **kw: None)
    def forbidden(*args, **kwargs):
        pytest.fail("missing local data still contacted a provider")
    monkeypatch.setattr(assistant, "_provider", forbidden)
    monkeypatch.setattr(assistant.managed, "status", forbidden)
    state = client.get("/api/assistant/status").get_json()
    assert state["data_available"] is False
    assert state["available"] is False
    assert "local" in state["message"].lower()


@pytest.mark.parametrize('failure', [ValueError, assistant.managed.ManagedAssistantError])
def test_generation_errors_do_not_echo_internal_exception_details(client, monkeypatch, failure):
    _provider(monkeypatch)
    _chat_store(monkeypatch)
    def fail(*args):
        raise failure('private-path /tmp/private-key sk-ant-secret')
    monkeypatch.setattr(assistant, '_stream_generate', lambda *a, **kw: fail())
    response = client.post('/api/assistant/chat', json={'message': 'Show usage'})
    assert response.status_code == 502
    assert 'private' not in response.get_data(as_text=True)
    assert 'sk-ant-secret' not in response.get_data(as_text=True)


def test_harness_executable_is_resolved_locally_and_question_uses_stdin(monkeypatch):
    from types import SimpleNamespace
    seen = {}
    monkeypatch.setattr(assistant, 'find_claude_cli', lambda: '/opt/claude')
    def run(argv, **kwargs):
        seen.update(argv=argv, **kwargs)
        return SimpleNamespace(returncode=0, stdout='{"result":"answer"}')
    monkeypatch.setattr(assistant.subprocess, 'run', run)
    question = '--dangerously-skip-permissions; untrusted question'
    assert assistant._generate('claude_cli', '/untrusted/credential', 'safe system', question) == 'answer'
    assert seen['argv'][0] == '/opt/claude'
    assert '/untrusted/credential' not in seen['argv']
    assert question not in seen['argv'] and seen['input'] == question
    assert '--safe-mode' in seen['argv'] and '--strict-mcp-config' in seen['argv']
    assert seen['argv'][seen['argv'].index('--tools') + 1] == ''
