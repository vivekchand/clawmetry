"""Assistant streaming contracts, using controlled transports rather than model calls.

AC-ASSIST-005.2 Real text deltas and stage updates exclude hidden reasoning.
AC-ASSIST-005.3 Only successfully completed turns enter conversation history.
AC-ASSIST-005.4 Cancellation, broken transports and bounded resource cleanup.
"""
from contextlib import contextmanager
import io
import json
import os
from pathlib import Path
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.error import HTTPError, URLError

import pytest
from flask import Flask

from clawmetry import assistant_service as assistant
from tests.assistant_test_support import daemon_adapter
from clawmetry import assistant_managed as managed
from clawmetry import assistant_providers as providers
from clawmetry import assistant_stream as stream


PLAN = {"queries": [{"title": "Sessions", "sql": "SELECT count(*) AS n FROM sessions",
                     "visual": True, "chart_type": "number", "y": "n"}]}


def unpack(chunk):
    text = chunk.decode() if isinstance(chunk, bytes) else chunk
    if text.startswith(":"):
        return "heartbeat", None
    event, data = text.strip().split("\n", 1)
    return event.removeprefix("event: "), json.loads(data.removeprefix("data: "))


@pytest.fixture
def chat(monkeypatch, daemon_adapter):
    app = Flask(__name__)
    app.register_blueprint(assistant.bp_assistant)
    monkeypatch.setattr(assistant, "_egress_suppressed", lambda: False)
    monkeypatch.setattr(assistant, "_planner_system", lambda window: assistant._PLAN)
    monkeypatch.setattr(assistant, "_provider", lambda *a: ("anthropic", "sk-ant-test-credential"))
    saved = []

    def store(method, **kwargs):
        if method == "query_assistant_sql":
            return {"rows": [{"n": 3}]}
        if method == "query_assistant_conversation":
            return {"title": "Earlier question", "messages": [{"role": "user", "content": "Earlier"}]}
        if method == "save_assistant_conversation":
            saved.append(kwargs)
            return True
        raise AssertionError(method)

    monkeypatch.setattr(assistant, "_store", store)
    return app, app.test_client(), saved


def native(monkeypatch, *, chunks=("Three ", "sessions."), failure=None):
    def generate(mode, credential, system, prompt, **kwargs):
        if system.startswith(assistant._PLAN):
            return json.dumps(PLAN)
        for chunk in chunks:
            kwargs["control"].check()
            kwargs["on_text"](chunk)
        if failure:
            raise failure
        return "".join(chunks)
    monkeypatch.setattr(providers, "generate", generate)


def test_deltas_arrive_before_provider_completion_and_history_commit(chat, monkeypatch):
    _app, client, saved = chat
    finish = threading.Event()
    ended = threading.Event()

    def generate(mode, credential, system, prompt, **kwargs):
        if system.startswith(assistant._PLAN):
            return json.dumps(PLAN)
        kwargs["on_text"]("Three ")
        assert finish.wait(3)
        kwargs["on_text"]("sessions.")
        ended.set()
        return "Three sessions."

    monkeypatch.setattr(providers, "generate", generate)
    response = client.post("/api/assistant/chat", json={"message": "Count", "stream": True}, buffered=False)
    assert response.mimetype == "text/event-stream"
    assert response.headers["X-Accel-Buffering"] == "no"
    assert "no-store" in response.headers["Cache-Control"]
    iterator = iter(response.response)
    events = []
    try:
        while not events or events[-1][0] != "delta":
            events.append(unpack(next(iterator)))
        assert events[-1] == ("delta", {"text": "Three "})
        assert not ended.is_set()
        assert saved == []
        assert [kind for kind, _ in events] == ["status"] * 4 + ["delta"]
        finish.set()
        events.extend(map(unpack, iterator))
        assert [kind for kind, _ in events].count("done") == 1
        assert events[-1][0] == "done"
        done = events[-1][1]
        assert set(done) == {"answer", "panels", "sources", "scope", "provider", "conversation_id"}
        assert "".join(value["text"] for kind, value in events if kind == "delta") == done["answer"]
        assert saved[0]["messages"][-1]["content"] == done["answer"]
        assert len(saved) == 1
        assert done["sources"][0]["rows"] == 1
        assert not assistant._conversations_in_flight
    finally:
        finish.set()
        response.close()


@pytest.mark.parametrize("flag", [None, False, "true", 1])
def test_only_boolean_true_selects_streaming(chat, monkeypatch, flag):
    _app, client, saved = chat
    calls = []
    def generated(*args, **kwargs):
        calls.append(kwargs)
        assert kwargs.get("on_text") is None
        return json.dumps({"answer": "JSON answer", "queries": []})
    monkeypatch.setattr(providers, "generate", generated)
    payload = {"message": "Hello"}
    if flag is not None:
        payload["stream"] = flag
    result = client.post("/api/assistant/chat", json=payload)
    assert result.is_json and result.status_code == 200
    assert result.get_json()["answer"] == "JSON answer"
    assert len(saved) == 1 and len(calls) == 1


def test_no_query_stream_uses_real_synthesis_without_emitting_planner_json(chat, monkeypatch):
    _app, client, saved = chat
    calls = []

    def generate(mode, credential, system, prompt, **kwargs):
        calls.append((system, prompt))
        if system == assistant._PLAN:
            return json.dumps({"answer": "PRIVATE PLANNER DRAFT", "queries": []})
        kwargs["on_text"]("Hello! ")
        kwargs["on_text"]("Ask about your agents.")
        return "Hello! Ask about your agents."

    monkeypatch.setattr(providers, "generate", generate)
    response = client.post("/api/assistant/chat", json={"message": "Hello", "stream": True})
    events = list(map(unpack, response.response))
    assert len(calls) == 2 and calls[-1][0] == assistant._SYNTHESIS
    assert "untrusted" in calls[-1][1] and "Evidence:\n[]" in calls[-1][1]
    assert any(kind == "delta" for kind, _ in events)
    assert "PRIVATE PLANNER" not in json.dumps(events) + json.dumps(saved)
    assert events[-1][1]["answer"] == "Hello! Ask about your agents."
    assert events[-1][1]["sources"] == []


@pytest.mark.parametrize("streaming", [False, True])
@pytest.mark.parametrize("code,word", [(401, "API key"), (403, "permissions"), (402, "usage limit"), (429, "billing"), (503, "unavailable")])
def test_api_errors_are_actionable_without_raw_details(chat, monkeypatch, streaming, code, word):
    _app, client, saved = chat

    def fail(*args, **kwargs):
        raise HTTPError("https://api.anthropic.com/v1/messages", code, "PRIVATE DETAILS", {}, io.BytesIO(b"HIDDEN"))

    monkeypatch.setattr(providers, "http_response", fail)
    monkeypatch.setattr(assistant.urllib.request, "urlopen", fail)
    response = client.post("/api/assistant/chat", json={"message": "Count", "stream": streaming})
    if streaming:
        events = list(map(unpack, response.response))
        assert events[-1][0] == "error"
        body = events[-1][1]
    else:
        assert response.status_code == 502
        body = response.get_json()
    assert word in body["error"]
    assert "PRIVATE" not in json.dumps(body) and "HIDDEN" not in json.dumps(body)
    assert saved == []


def test_api_network_error_has_fixed_connection_guidance(chat, monkeypatch):
    _app, client, saved = chat

    def fail(*args, **kwargs):
        raise URLError("PRIVATE PROXY CREDENTIAL")

    monkeypatch.setattr(providers, "http_response", fail)
    response = client.post("/api/assistant/chat", json={"message": "Count", "stream": True})
    events = list(map(unpack, response.response))
    assert events[-1][0] == "error" and "connection" in events[-1][1]["error"]
    assert "PRIVATE" not in json.dumps(events) and not saved


@pytest.mark.parametrize("failure", [stream.BrokenStream(), ValueError("private reasoning sk-ant-secret"), TimeoutError()])
def test_partial_failure_is_explicit_and_never_persisted(chat, monkeypatch, failure):
    _app, client, saved = chat
    native(monkeypatch, chunks=("Partial ",), failure=failure)
    result = client.post("/api/assistant/chat", json={"message": "Count", "stream": True})
    events = list(map(unpack, result.response))
    assert any(kind == "delta" for kind, _ in events)
    assert events[-1][0] == "error"
    assert not any(kind == "done" for kind, _ in events)
    assert "private" not in json.dumps(events)
    if isinstance(failure, stream.BrokenStream):
        assert "connection ended" in events[-1][1]["error"]
    assert saved == []
    result.close()
    assert not assistant._conversations_in_flight


def test_persistence_failure_sends_error_instead_of_done(chat, monkeypatch):
    _app, client, saved = chat
    native(monkeypatch)
    original = assistant._store
    monkeypatch.setattr(assistant, "_store", lambda method, **kw: None if method == "save_assistant_conversation" else original(method, **kw))
    response = client.post("/api/assistant/chat", json={"message": "Count", "stream": True})
    events = list(map(unpack, response.response))
    assert events[-1][0] == "error" and "saved" in events[-1][1]["error"]
    assert "done" not in [kind for kind, _ in events]
    assert saved == []
    response.close()


@pytest.mark.parametrize("consume_first", [False, True])
def test_close_local_response_cancels_daemon_job(chat, monkeypatch, consume_first):
    app, _client, saved = chat
    def blocked(*args, **kwargs):
        while True:
            kwargs['control'].check()
            threading.Event().wait(.01)
    monkeypatch.setattr(providers, 'generate', blocked)
    with app.test_request_context(json={'message':'Count','stream':True,'conversation_id':'old'}):
        response=assistant.assistant_chat()
    if consume_first:
        assert unpack(next(iter(response.response)))[0]=='status'
    response.close(); response.close()
    for _ in range(100):
        if not assistant._conversations_in_flight:break
        threading.Event().wait(.01)
    assert not assistant._conversations_in_flight
    assert assistant._gate.acquire(False) and assistant._gate.acquire(False)
    assistant._gate.release(); assistant._gate.release()
    assert not saved


def test_cancel_during_plan_keeps_worker_bounded_until_it_exits(chat, monkeypatch):
    _app, client, saved = chat
    started, finish, exited = threading.Event(), threading.Event(), threading.Event()
    jobs = []

    def generate(*args, **kwargs):
        jobs.append(kwargs["control"])
        started.set()
        try:
            assert finish.wait(3)
            return json.dumps({"answer": "Stale answer", "queries": []})
        finally:
            exited.set()

    monkeypatch.setattr(providers, "generate", generate)
    monkeypatch.setattr(stream, "HEARTBEAT_SECONDS", 0.01)
    response = client.post("/api/assistant/chat", json={"message": "Count", "stream": True, "conversation_id": "old"})
    iterator = iter(response.response)
    try:
        assert unpack(next(iterator))[0] == "status"
        assert unpack(next(iterator))[0] == "status"
        assert started.wait(1)
        assert unpack(next(iterator))[0] == "heartbeat"
        response.close()
        assert jobs[0].cancelled.is_set()
        assert "old" in assistant._conversations_in_flight
        assert assistant._gate.acquire(False)
        assert not assistant._gate.acquire(False)
        assistant._gate.release()
        collision = client.post("/api/assistant/chat", json={"message": "Followup", "conversation_id": "old", "stream": True})
        assert collision.status_code == 409
    finally:
        finish.set()
        response.close()
    assert exited.wait(1)
    jobs[0].worker.join(1)
    assert not jobs[0].worker.is_alive()
    for _ in range(100):
        if not assistant._conversations_in_flight:break
        threading.Event().wait(.01)
    assert not assistant._conversations_in_flight
    assert saved == []


def test_stream_admission_and_preflight_errors_remain_json(chat, monkeypatch):
    _app, client, _saved = chat
    def blocked(*args, **kwargs):
        while True:
            kwargs['control'].check()
            threading.Event().wait(.01)
    monkeypatch.setattr(providers, 'generate', blocked)
    one = client.post("/api/assistant/chat", json={"message": "One", "stream": True})
    two = client.post("/api/assistant/chat", json={"message": "Two", "stream": True})
    try:
        overflow = client.post("/api/assistant/chat", json={"message": "Three", "stream": True})
        assert overflow.status_code == 429 and overflow.is_json
    finally:
        one.close()
        two.close()
    for _ in range(100):
        if not assistant._conversations_in_flight:break
        threading.Event().wait(.01)
    monkeypatch.setattr(assistant, "_egress_suppressed", lambda: True)
    monkeypatch.setattr(assistant, "_provider", lambda *a: pytest.fail("offline called provider"))
    offline = client.post("/api/assistant/chat", json={"message": "Count", "stream": True})
    assert offline.status_code == 503 and offline.is_json


def test_worker_start_failure_releases_admission(chat, monkeypatch):
    _app, client, saved = chat
    original = threading.Thread.start

    def fail_worker(self):
        if self.name == "assistant-stream":
            raise RuntimeError("private start failure")
        return original(self)

    monkeypatch.setattr(threading.Thread, "start", fail_worker)
    response = client.post("/api/assistant/chat", json={"message": "Count", "stream": True})
    events = list(map(unpack, response.response))
    assert [kind for kind, _ in events] == ["status", "error"]
    assert not assistant._conversations_in_flight
    assert saved == []


def test_request_deadline_cancels_full_queue_and_releases_worker(chat, monkeypatch):
    _app, client, saved = chat
    monkeypatch.setattr(stream, "REQUEST_SECONDS", 0.1)
    monkeypatch.setattr(stream, "QUEUE_SIZE", 1)
    def endless(mode, credential, system, prompt, **kwargs):
        if system.startswith(assistant._PLAN):return json.dumps(PLAN)
        while True:
            kwargs['control'].check()
            kwargs['on_text']('word ')
            threading.Event().wait(.001)
    monkeypatch.setattr(providers,'generate',endless)
    response = client.post("/api/assistant/chat", json={"message": "Count", "stream": True})
    iterator = iter(response.response)
    assert unpack(next(iterator))[0] == "status"
    # The daemon continues consuming when HTTP pauses. The independent
    # deadline must still cancel generation without another browser read.
    threading.Event().wait(0.2)
    events = list(map(unpack, iterator))
    assert events[-1][0] == "error" and "too long" in events[-1][1]["error"]
    response.close()
    assert not assistant._conversations_in_flight and saved == []


def test_committed_daemon_result_survives_http_disconnect(chat, monkeypatch, daemon_adapter):
    # ADR-007: once the daemon's atomic commit crossed its live-lease barrier,
    # a browser disconnect cannot turn the completed answer into a lost turn.
    _app, client, saved = chat
    native(monkeypatch)
    response=client.post('/api/assistant/chat',json={'message':'Count','stream':True})
    for _ in range(100):
        if saved and all(j.terminal for j in daemon_adapter.jobs.values()):break
        threading.Event().wait(.01)
    response.close()
    assert len(saved)==1
    assert saved[0]['messages'][-1]['content']=='Three sessions.'


@pytest.mark.parametrize("raw", [
    "Safe sk-ant-abcdefghijklmnopqrstuvwxyz more.",
    "Safe ghp_abcdefghijklmnopqrstuvwxyz more.",
    "Safe github_pat_abcdefghijklmnopqrstuvwxyz more.",
    "Safe (bEaReR \n  abc.def-ghi) more.",
    "Grüße Bearer abc.def-ghi",
])
def test_redaction_is_safe_at_every_chunk_boundary(raw):
    for cut in range(len(raw) + 1):
        scrubber = stream.StreamScrubber(assistant._scrub)
        output = scrubber.feed(raw[:cut]) + scrubber.feed(raw[cut:]) + scrubber.feed("", final=True)
        assert output == assistant._scrub(raw), (cut, output)
    scrubber = stream.StreamScrubber(assistant._scrub)
    assert "".join(scrubber.feed(char) for char in raw) + scrubber.feed("", final=True) == assistant._scrub(raw)


def test_redaction_holds_long_secret_and_caps_the_final_answer():
    scrubber = stream.StreamScrubber(assistant._scrub)
    assert scrubber.feed("Safe sk-" + "x" * 7000) == "Safe "
    assert scrubber.feed(" ") == "[redacted] "
    raw = "word " * 1500
    scrubber = stream.StreamScrubber(assistant._scrub)
    assert "".join(scrubber.feed(part) for part in [raw[:4999], raw[4999:]]) + scrubber.feed("", final=True) == assistant._scrub(raw)
    with pytest.raises(stream.BrokenStream):
        stream.StreamScrubber(assistant._scrub).feed("x" * (stream.MAX_TEXT + 1))


def provider_events(texts, *, reason="end_turn"):
    yield {"type": "message_start", "message": {"role": "assistant"}}
    yield {"type": "content_block_start", "index": 0, "content_block": {"type": "thinking", "thinking": "HIDDEN"}}
    yield {"type": "content_block_delta", "index": 0, "delta": {"type": "thinking_delta", "thinking": "HIDDEN"}}
    yield {"type": "content_block_delta", "index": 0, "delta": {"type": "signature_delta", "signature": "HIDDEN"}}
    yield {"type": "content_block_stop", "index": 0}
    yield {"type": "content_block_start", "index": 1, "content_block": {"type": "text", "text": ""}}
    for text in texts:
        yield {"type": "content_block_delta", "index": 1, "delta": {"type": "text_delta", "text": text}}
    yield {"type": "content_block_stop", "index": 1}
    yield {"type": "message_delta", "delta": {"stop_reason": reason}}
    yield {"type": "message_stop"}


class APIResponse(io.BytesIO):
    def getheader(self, name, default=""):
        return "text/event-stream; charset=utf-8"


def wire(events):
    return "".join("event: ignored\r\ndata: " + json.dumps(item) + "\r\n\r\n" for item in events).encode()


def test_native_api_route_filters_reasoning_and_scrubs_real_text_events(chat, monkeypatch):
    _app, client, saved = chat
    requests, responses = [], []

    @contextmanager
    def open_response(url, **kwargs):
        payload = json.loads(kwargs["payload"])
        requests.append(payload)
        texts = [json.dumps(PLAN)] if payload["system"] == assistant._PLAN else ["Safe sk-", "ant-abcdefghijklmnopqrstuvwxyz", " result."]
        response = APIResponse(wire(provider_events(texts)))
        responses.append(response)
        with response:
            yield response

    monkeypatch.setattr(providers, "http_response", open_response)
    response = client.post("/api/assistant/chat", json={"message": "Count", "stream": True})
    events = list(map(unpack, response.response))
    assert events[-1][0] == "done"
    assert events[-1][1]["answer"] == "Safe [redacted] result."
    assert all(item["stream"] is True for item in requests)
    assert "HIDDEN" not in json.dumps(events) + json.dumps(saved)
    assert "abcdefghijklmnopqrstuvwxyz" not in json.dumps(events) + json.dumps(saved)
    assert all(response.closed for response in responses)


@pytest.mark.parametrize("damage", ["eof", "error", "invalid_json", "token_limit", "wrong_block", "oversized"])
def test_api_broken_or_incomplete_transport_never_succeeds(monkeypatch, damage):
    events = list(provider_events(["Partial "]))
    if damage == "eof":
        events.pop()
    elif damage == "error":
        events[-1] = {"type": "error", "error": {"message": "HIDDEN"}}
    elif damage == "token_limit":
        events[-2]["delta"]["stop_reason"] = "max_tokens"
    elif damage == "wrong_block":
        events[2]["delta"] = {"type": "text_delta", "text": "HIDDEN"}
    body = wire(events)
    if damage == "invalid_json":
        body = b"data: {invalid}\n\n"
    elif damage == "oversized":
        body = b"data: " + b"x" * stream.MAX_LINE + b"\n\n"
    response = APIResponse(body)

    @contextmanager
    def open_response(*a, **kw):
        with response:
            yield response

    monkeypatch.setattr(providers, "http_response", open_response)
    with pytest.raises(stream.BrokenStream):
        list(providers.api_text("key", "system", "prompt", "model", stream.StreamJob(lambda: None)))
    assert response.closed


def test_managed_stream_keeps_authenticated_envelope_and_has_no_fake_deltas(chat, monkeypatch):
    _app, client, saved = chat
    monkeypatch.setattr(assistant, "_provider", lambda *a: ("managed", "configured"))
    calls = []

    def request(path, **kwargs):
        assert kwargs["control"] is not None
        assert kwargs["idempotency"] is True
        payload = kwargs["payload"]
        calls.append(payload)
        answer = json.dumps(PLAN) if payload["system"] == assistant._PLAN else "Managed answer."
        private = managed.X25519PrivateKey.generate()
        public = managed.X25519PublicKey.from_public_bytes(managed._decode_b64(payload["response_public_key"]))
        key = managed.HKDF(algorithm=managed.hashes.SHA256(), length=32, salt=None, info=managed.ENVELOPE_INFO).derive(private.exchange(public))
        nonce = os.urandom(12)
        return {"envelope": {"v": 1, "alg": managed.ENVELOPE_ALGORITHM,
                "ephemeral_public_key": managed._b64(private.public_key().public_bytes(managed.serialization.Encoding.Raw, managed.serialization.PublicFormat.Raw)),
                "nonce": managed._b64(nonce), "ciphertext": managed._b64(managed.AESGCM(key).encrypt(nonce, json.dumps({"text": answer}).encode(), managed.ENVELOPE_AAD))}}

    monkeypatch.setattr(managed, "_json_request", request)
    response = client.post("/api/assistant/chat", json={"message": "Count", "stream": True})
    events = list(map(unpack, response.response))
    assert events[-1][0] == "done" and events[-1][1]["answer"] == "Managed answer."
    assert set(kind for kind, _ in events) == {"status", "done"}
    assert len(calls) == 2 and len(saved) == 1
    assert calls[0]["response_public_key"] != calls[1]["response_public_key"]


@pytest.mark.parametrize("result", [{"text": "PRIVATE"}, {"envelope": {"v": 2}}])
def test_invalid_managed_envelope_is_terminal_error(chat, monkeypatch, result):
    _app, client, saved = chat
    monkeypatch.setattr(assistant, "_provider", lambda *a: ("managed", "configured"))
    monkeypatch.setattr(managed, "_json_request", lambda *a, **k: result)
    response = client.post("/api/assistant/chat", json={"message": "Count", "stream": True})
    events = list(map(unpack, response.response))
    assert events[-1][0] == "error" and not saved
    assert "PRIVATE" not in json.dumps(events)


def cli_stub(tmp_path, monkeypatch, *, sleep=False, success=True):
    script = tmp_path / "fake_claude.py"
    events = [{"type": "stream_event", "event": event} for event in provider_events(["Visible ", "answer."])]
    events.insert(-1, {"type": "assistant", "message": {"content": [{"type": "thinking", "thinking": "HIDDEN"}]}})
    if success:
        events.append({"type": "result", "subtype": "success", "result": "Visible answer.", "is_error": False})
    script.write_text("import json, time\nevents = json.loads(" + repr(json.dumps(events)) + ")\nfor event in events:\n print(json.dumps(event), flush=True)\n" + ("time.sleep(60)\n" if sleep else ""))
    original = providers.subprocess.Popen
    seen = {}

    def popen(argv, **kwargs):
        seen.update(argv=argv, cwd=kwargs["cwd"], env=kwargs["env"])
        seen["prompt"] = kwargs["stdin"].read().decode()
        kwargs["stdin"].seek(0)
        seen["proc"] = original([sys.executable, str(script)] + argv[1:], **kwargs)
        return seen["proc"]

    monkeypatch.setattr(providers.subprocess, "Popen", popen)
    return seen


def test_cli_real_subprocess_deltas_isolation_and_reaping(tmp_path, monkeypatch):
    seen = cli_stub(tmp_path, monkeypatch)
    control = stream.StreamJob(lambda: None)
    output = list(providers.cli_text("/resolved/claude", "system", "--unsafe question", control))
    assert output == ["Visible ", "answer."]
    assert seen["argv"][0] == "/resolved/claude"
    assert seen["prompt"] == "--unsafe question" and "--unsafe question" not in seen["argv"]
    for flag in ("--safe-mode", "--verbose", "--include-partial-messages", "--strict-mcp-config", "--disable-slash-commands", "--no-session-persistence"):
        assert flag in seen["argv"]
    assert "--bare" not in seen["argv"]
    assert seen["argv"][seen["argv"].index("--tools") + 1] == ""
    assert seen["argv"][seen["argv"].index("--setting-sources") + 1] == ""
    assert seen["argv"][seen["argv"].index("--output-format") + 1] == "stream-json"
    assert "CLAUDECODE" not in seen["env"]
    assert seen["proc"].poll() == 0 and seen["proc"].stdout.closed
    assert not Path(seen["cwd"]).exists()


@pytest.mark.parametrize("timeout", [False, True])
def test_cli_cancel_or_deadline_kills_blocked_process_and_cleans_tempdir(tmp_path, monkeypatch, timeout):
    seen = cli_stub(tmp_path, monkeypatch, sleep=True)
    control = stream.StreamJob(lambda: None)
    iterator = providers.cli_text("claude", "system", "prompt", control)
    assert next(iterator) == "Visible "
    control.abort(timeout=timeout)
    with pytest.raises(TimeoutError if timeout else stream.Cancelled):
        list(iterator)
    assert seen["proc"].poll() is not None and seen["proc"].stdout.closed
    assert not Path(seen["cwd"]).exists()


def test_cli_requires_success_result_not_just_text_and_exit_zero(tmp_path, monkeypatch):
    seen = cli_stub(tmp_path, monkeypatch, success=False)
    with pytest.raises(stream.BrokenStream):
        list(providers.cli_text("claude", "system", "prompt", stream.StreamJob(lambda: None)))
    assert seen["proc"].poll() == 0 and seen["proc"].stdout.closed


@pytest.fixture
def windows_api(monkeypatch):
    import ctypes

    kernel = SimpleNamespace(**{name: Mock(return_value=value) for name, value in {
        "CreateJobObjectW": 0x100000001, "SetInformationJobObject": 1,
        "AssignProcessToJobObject": 1, "CloseHandle": 1,
        "GetProcessId": 42, "CreateToolhelp32Snapshot": 0x300000001,
        "Thread32First": 1, "Thread32Next": 0, "OpenThread": 0x400000001,
        "GetProcessIdOfThread": 42, "WaitForSingleObject": 258, "ResumeThread": 1,
    }.items()})

    def first(snapshot, entry_pointer):
        entry_pointer._obj.owner_pid = 42
        entry_pointer._obj.thread_id = 123
        return 1

    kernel.Thread32First.side_effect = first
    monkeypatch.setattr(ctypes, "WinDLL", lambda name, **kw: kernel, raising=False)
    monkeypatch.setattr(providers, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(providers.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200, raising=False)
    return kernel


def test_windows_cancel_releases_reader_after_launcher_exit_without_pid_lookup(windows_api, monkeypatch):
    """AC-ASSIST-005.4 An exited launcher cannot strand a stream/admission slot."""
    kernel = windows_api
    descendant_exit, reading, released = threading.Event(), threading.Event(), threading.Event()
    windows_job = providers._WindowsJob()
    proc = SimpleNamespace(pid=42, _handle=0x200000001, poll=Mock(return_value=0), kill=Mock())
    windows_job.assign_and_resume(proc)
    kernel.CloseHandle.reset_mock()  # snapshot and thread handles were closed
    proc._assistant_job = windows_job
    kernel.CloseHandle.side_effect = lambda handle: descendant_exit.set() or 1
    monkeypatch.setattr(providers.subprocess, "run", lambda *a, **kw: pytest.fail("PID-based taskkill could target a reused PID"))
    control = stream.StreamJob(released.set)

    def work(job):
        with job.resource(lambda: providers._kill_process(proc)):
            reading.set()
            # Models the pipe writer held by a descendant after launcher exit.
            assert descendant_exit.wait(3)
            job.check()

    control.start(work)
    try:
        assert reading.wait(1)
        control.close()
        assert released.wait(1), "launcher exit stranded the worker and admission slot"
        assert descendant_exit.is_set()
        control.worker.join(1)
        assert not control.worker.is_alive()
        providers._kill_process(proc)  # repeated cleanup must be harmless
        kernel.CloseHandle.assert_called_once_with(0x100000001)
        kernel.AssignProcessToJobObject.assert_called_once_with(0x100000001, 0x200000001)
        proc.kill.assert_not_called()
        proc.poll.assert_not_called()  # launcher liveness is not the ownership test
    finally:
        descendant_exit.set()
        control.close()
        control.worker.join(2)
        windows_job.close()


@pytest.mark.parametrize("failure", [None, "assign", "resume", "spawn", "configure", "thread_reused", "process_exited"])
def test_windows_spawn_contains_before_resume_and_cleans_failure(windows_api, monkeypatch, failure):
    import ctypes
    kernel = windows_api
    calls = []
    proc = SimpleNamespace(_handle=0x200000001, poll=Mock(return_value=None),
                           kill=Mock(), wait=Mock(), stdout=io.BytesIO())

    def spawn(argv, **kwargs):
        assert kwargs["creationflags"] == 0x204  # new group + CREATE_SUSPENDED
        assert kwargs["start_new_session"] is False
        calls.append("suspended")
        if failure == "spawn":
            raise OSError("spawn failed")
        return proc

    def assign(job_handle, process_handle):
        assert process_handle == proc._handle
        calls.append("assigned")
        return 0 if failure == "assign" else 1

    def resume(thread_handle):
        assert calls == ["suspended", "assigned"]
        assert thread_handle == 0x400000001
        calls.append("resumed")
        return 0xffffffff if failure == "resume" else 1

    kernel.AssignProcessToJobObject.side_effect = assign
    kernel.ResumeThread.side_effect = resume
    if failure == "configure":
        kernel.SetInformationJobObject.return_value = 0
    if failure == "thread_reused":
        kernel.GetProcessIdOfThread.return_value = 999
    if failure == "process_exited":
        kernel.WaitForSingleObject.return_value = 0
    monkeypatch.setattr(providers.subprocess, "Popen", spawn)
    if failure:
        with pytest.raises(OSError):
            providers._spawn_cli(["claude"])
        assert [call.args[0] for call in kernel.CloseHandle.call_args_list].count(0x100000001) == 1
        if failure in ("assign", "resume", "thread_reused", "process_exited"):
            assert proc.stdout.closed
            proc.kill.assert_called_once()
            proc.wait.assert_called_once_with(timeout=2)
        if failure != "resume":
            kernel.ResumeThread.assert_not_called()
    else:
        assert providers._spawn_cli(["claude"]) is proc
        assert calls == ["suspended", "assigned", "resumed"]
        assert kernel.CreateJobObjectW.restype is ctypes.c_void_p
        assert kernel.ResumeThread.argtypes == [ctypes.c_void_p]
        kernel.GetProcessId.assert_called_once_with(proc._handle)
        kernel.OpenThread.assert_called_once_with(0x802, False, 123)
        proc._assistant_job.close()
        assert [call.args[0] for call in kernel.CloseHandle.call_args_list] == [0x400000001, 0x300000001, 0x100000001]


@pytest.mark.skipif(os.name != "nt", reason="exercises native Windows jobs and inherited pipe handles")
@pytest.mark.parametrize("timeout", [False, True])
def test_windows_native_cancel_after_launcher_exit_kills_stdout_descendant(tmp_path, monkeypatch, timeout):
    """AC-ASSIST-005.4 Native CI: a real orphaned pipe writer must die on cancel."""
    import ctypes as c

    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [c.c_uint32, c.c_int, c.c_uint32]
    kernel.OpenProcess.restype = c.c_void_p
    kernel.WaitForSingleObject.argtypes = [c.c_void_p, c.c_uint32]
    kernel.WaitForSingleObject.restype = c.c_uint32
    kernel.CloseHandle.argtypes = [c.c_void_p]
    kernel.CloseHandle.restype = c.c_int
    pid_file = tmp_path / "descendant.pid"
    script = tmp_path / "launcher.py"
    events = [{"type": "stream_event", "event": event} for event in provider_events(["Visible "])]
    script.write_text(
        "import subprocess, sys, json\nfrom pathlib import Path\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], "
        "stdin=subprocess.DEVNULL, stdout=sys.stdout, stderr=subprocess.DEVNULL)\n"
        "Path(" + repr(str(pid_file)) + ").write_text(str(child.pid))\n"
        "for event in json.loads(" + repr(json.dumps(events)) + "):\n"
        " print(json.dumps(event), flush=True)\n"
        # The launcher exits while child keeps the exact stdout pipe open.
    )
    original = providers.subprocess.Popen
    processes = []

    def spawn(argv, **kwargs):
        proc = original([sys.executable, str(script)], **kwargs)
        processes.append(proc)
        return proc

    monkeypatch.setattr(providers.subprocess, "Popen", spawn)
    visible, released = threading.Event(), threading.Event()
    control = stream.StreamJob(released.set)

    def work(job):
        for text in providers.cli_text("claude", "system", "prompt", job):
            visible.set()

    child_handle = None
    control.start(work)
    try:
        assert visible.wait(10), "suspended launcher did not resume and emit text"
        assert processes[0].wait(timeout=5) == 0
        assert not control.finished.is_set(), "descendant did not retain the pipe"
        child_handle = kernel.OpenProcess(0x100000, False, int(pid_file.read_text()))
        assert child_handle
        assert kernel.WaitForSingleObject(child_handle, 0) == 258
        control.abort(timeout=timeout)
        control.close()
        assert released.wait(5), "cancel did not release the worker/admission slot"
        assert kernel.WaitForSingleObject(child_handle, 5000) == 0
        control.worker.join(2)
        assert not control.worker.is_alive()
        assert processes[0].stdout.closed
    finally:
        control.close()
        for proc in processes:
            providers._kill_process(proc)
            proc.wait(timeout=5)
        control.worker.join(5)
        if child_handle:
            kernel.CloseHandle(child_handle)


@pytest.mark.parametrize("send_headers", [False, True])
def test_http_cancel_interrupts_real_blocked_socket(send_headers):
    reached, finish, exited = threading.Event(), threading.Event(), threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers["Content-Length"]))
            if send_headers:
                self.send_response(200)
                self.end_headers()
            reached.set()
            finish.wait(3)

        def log_message(self, *a):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    control = stream.StreamJob(lambda: None)
    errors = []

    def request():
        try:
            with stream.http_response(f"http://127.0.0.1:{server.server_port}/", payload=b"{}", headers={}, control=control) as response:
                response.read()
        except Exception as exc:
            errors.append(exc)
        finally:
            exited.set()

    worker = threading.Thread(target=request)
    worker.start()
    try:
        assert reached.wait(2)
        control.abort()
        assert exited.wait(1), "cancel did not wake blocked provider read"
        assert errors
    finally:
        finish.set()
        server.shutdown()
        server.server_close()
        worker.join(2)
        server_thread.join(2)
    assert not worker.is_alive()


def test_streaming_transport_preserves_environment_proxy_discovery(monkeypatch):
    seen = []

    class Proxy(BaseHTTPRequestHandler):
        def do_POST(self):
            seen.append((self.path, self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(200)
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"ok")

        def log_message(self, *a):
            pass

    proxy = ThreadingHTTPServer(("127.0.0.1", 0), Proxy)
    worker = threading.Thread(target=proxy.serve_forever, daemon=True)
    worker.start()
    monkeypatch.setenv("http_proxy", f"http://127.0.0.1:{proxy.server_port}")
    monkeypatch.setenv("no_proxy", "")
    monkeypatch.delenv("NO_PROXY", raising=False)
    try:
        with stream.http_response("http://provider.invalid/messages", payload=b"{}", headers={}, control=stream.StreamJob(lambda: None)) as response:
            assert response.read() == b"ok"
        assert seen == [("http://provider.invalid/messages", b"{}")]
    finally:
        proxy.shutdown()
        proxy.server_close()
        worker.join(2)
