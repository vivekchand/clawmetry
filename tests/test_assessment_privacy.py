"""Mandatory local assessment boundary, inspected at the transport callback.

AC-DEC-004.2: test_identifiers_in_every_payload_location_and_numeric_values; test_secret_shapes_never_reach_transport
AC-DEC-004.3: test_equality_within_request_and_isolation_between_sessions
AC-DEC-004.4: test_bad_payloads_send_nothing; test_detector_failure_and_timeout_send_nothing; test_opt_out_cannot_bypass
AC-DEC-004.7: test_policy_requires_explicit_supported_coverage
AC-DEC-005.2: test_restore_is_scoped_field_limited_single_pass_and_escaped
AC-DEC-005.3: test_idle_ttl_actually_clears_map_and_close_forbids_reuse; test_session_cannot_be_serialized
AC-DEC-005.5: test_existing_irreversible_redaction_is_never_guessed

Fixtures prove the pure component, not provider, runtime, or cloud integration.
"""
import copy
import gc
import json
import pickle
import re
import threading
import time
import weakref
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

import pytest

from clawmetry import assessment_privacy as privacy
from clawmetry import endpoints, redaction


class SpyTransport:
    def __init__(self):
        self.sent = []

    def __call__(self, encoded, *, timeout):
        assert type(encoded) is bytes
        assert 0 < timeout <= 30
        self.sent.append(encoded)
        return b"response"


@pytest.fixture(autouse=True)
def local_environment(monkeypatch):
    for name in ("CLAWMETRY_OFFLINE", "SELF_HOSTED", "CLAWMETRY_SELF_HOSTED",
                 "CLAWMETRY_ENDPOINT", "CLAWMETRY_INGEST_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(endpoints, "_config_endpoint", lambda: "")


@pytest.fixture
def sessions():
    created = []

    def create(scope="account_one", **limits):
        session = privacy.MaskingSession(scope, privacy.PrivacyPolicy(tuple(privacy.SUPPORTED_CATEGORIES), **limits))
        created.append(session)
        return session

    yield create
    for session in created:
        session.close()


def send(session, payload, spy=None):
    spy = spy or SpyTransport()
    gate = privacy.ConsentGate(session._scope)
    generation = gate.grant(session.policy, "processor-policy-v1")
    session.mask(payload)
    gate.dispatch(session, generation, "processor-policy-v1", spy)
    return json.loads(spy.sent[-1]), spy


def reject(session, payload, code):
    spy = SpyTransport()
    with pytest.raises(privacy.PrivacyError) as exc:
        send(session, payload, spy)
    assert exc.value.code == code
    assert spy.sent == []
    assert session._values == {} and session._tokens == {}


def aadhaar():
    prefix = "49994999499"
    return next(prefix + digit for digit in "0123456789" if redaction.aadhaar_valid(prefix + digit))


def test_identifiers_in_every_payload_location_and_numeric_values(sessions):
    identifiers = ["alice@example.test", "+44 20 7946 0958", "4111-1111-1111-1111",
                   "GB82 WEST 1234 5698 7654 32", "123-45-6789", "AB 12 34 56 C",
                   aadhaar(), "111222333"]
    payload = {"state": [{item: item} for item in identifiers], "questions": identifiers,
               "criteria": {"rubric": "check " + " ; ".join(identifiers)},
               "metadata": {"id": "alice@example.test", "path": "/tmp/alice@example.test/error"},
               "numeric": [4111111111111111, int(aadhaar()), 111222333, 111222333.0],
               "facts": {"score": 0.5, "attempts": 2, "ok": True, "optional": None}}
    out, spy = send(sessions(), payload)
    wire = spy.sent[0].decode()
    for identifier in identifiers + ["4111111111111111"]:
        assert identifier not in wire
    assert out["metadata"]["id"].startswith("[CMPII:")
    assert all(type(value) is str and value.startswith("[CMPII:") for value in out["numeric"])
    assert out["facts"] == payload["facts"]
    assert payload["questions"][0] == "alice@example.test"


def test_equality_within_request_and_isolation_between_sessions(sessions):
    payload = {"alice@example.test": "alice@example.test", "nested": ["alice@example.test"]}
    first, _ = send(sessions(), payload)
    second, _ = send(sessions(), payload)
    other, _ = send(sessions("account_two"), payload)
    key = next(key for key in first if key != "nested")
    assert first[key] == key == first["nested"][0]
    assert len({first["nested"][0], second["nested"][0], other["nested"][0]}) == 3


@pytest.mark.parametrize("secret", [
    "apikey_" + "a" * 32 + "_" + "b" * 64,
    "sk-ant-" + "A" * 24,
    "ghp_" + "A" * 40,
    "Bearer user-token-with-punctuation=",
    "Basic dXNlcjpwYXNzd29yZA==",
    "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signaturevalue",
    "-----BEGIN PRIVATE KEY-----\nFAKE-ONLY-TEST-CONTENT\n-----END PRIVATE KEY-----",
    'password="punctuation !@#$ and spaces alice@example.test"',
    "secret='more ! punctuation with spaces'",
    "password=punctuation;and rest of value",
    "https://user:password%21@example.test/path",
    "Cookie: sid=abc123; private=other-value",
    "Set-Cookie: session=abc; HttpOnly",
    "X-API-Key: short-value",
])
def test_secret_shapes_never_reach_transport(sessions, secret):
    session = sessions()
    out, spy = send(session, {"state": secret, "metadata": [secret]})
    assert privacy.SECRET_REMOVED in spy.sent[0].decode()
    assert secret not in spy.sent[0].decode()
    assert session._values == {}
    assert "[CMPII:" not in out["state"]


@pytest.mark.parametrize("value", ["x", 42, False, None, ["short", {"nested": "alice@example.test"}],
                                    {"deep": [123, "sensitive-even-without-key-shape"]}])
def test_structured_secret_values_are_wholly_withheld(sessions, value):
    out, _ = send(sessions(), {"http.request.header.authorization": value,
                              "X-API-Key": value, "Cookie": value, "client_secret": value})
    assert set(out.values()) == {privacy.SECRET_REMOVED}


def test_secret_prepass_prevents_restoring_a_secret_repeated_elsewhere(sessions):
    session = sessions()
    out, spy = send(session, {"note": "alice@example.test and 111222333",
                             "credentials": {"email": "alice@example.test", "pin": 111222333}})
    assert session._values == {}
    assert b"alice@example.test" not in spy.sent[0] and b"111222333" not in spy.sent[0]
    assert session.restore(out["note"], scope="account_one", field="explanation") == out["note"]


def test_short_secret_overlapping_identifier_withholds_the_whole_identifier(sessions):
    session = sessions()
    _, spy = send(session, {"password": "44", "contact": "+44 20 7946 0958"})
    assert b"7946" not in spy.sent[0]
    assert not session._values


def test_opt_out_cannot_bypass(sessions, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_REDACT", "0")
    monkeypatch.setenv("CLAWMETRY_REDACT_PII", "0")
    monkeypatch.setattr(redaction, "_pii_config", lambda: {key: False for key in redaction.PII_CATEGORIES})
    monkeypatch.setattr(redaction, "redact_text", lambda text: text)
    monkeypatch.setattr(redaction, "scrub_payload", lambda text, **kw: (text, []))
    _, spy = send(sessions(), {"state": "alice@example.test", "api_key": "short"})
    assert b"alice@example.test" not in spy.sent[0] and b"short" not in spy.sent[0]


@pytest.mark.parametrize("categories,language", [((), "en"), (("names",), "en"), (("address",), "en"),
                                                   (("context",), "en"), (("unicode_email",), "en"),
                                                   (("email",), "zh"), (("email",), "nl")])
def test_policy_requires_explicit_supported_coverage(categories, language):
    with pytest.raises(privacy.PrivacyError, match="unsupported_coverage"):
        privacy.PrivacyPolicy(categories, language=language)


def test_all_identifier_detectors_run_even_when_required_subset_is_small():
    with privacy.MaskingSession("account_one", privacy.PrivacyPolicy(("email",))) as session:
        _, spy = send(session, {"card": 4111111111111111})
    assert b"4111111111111111" not in spy.sent[0]


@pytest.mark.parametrize("payload,code", [
    ({"state": "Jos\u00e9@example.test"}, "unsupported_text"),
    ({"[CMPII:forged]": 1}, "reserved_placeholder"),
    ({1: "value"}, "invalid_key"), ({"state": b"raw"}, "invalid_payload_type"),
    ({"state": (1, 2)}, "invalid_payload_type"),
    ({"state": float("nan")}, "invalid_number"),
    ({"state": float("inf")}, "invalid_number"),
    ({"state": 10 ** 10000}, "invalid_number"),
    ({"state": "-----BEGIN PRIVATE KEY-----truncated"}, "incomplete_secret"),
    ({"state": 'password="truncated secret with spaces'}, "incomplete_secret"),
])
def test_bad_payloads_send_nothing(sessions, payload, code):
    reject(sessions(), payload, code)


def test_unknown_objects_are_rejected_without_stringification(sessions):
    class Trap:
        def __str__(self): raise AssertionError("must not stringify")
        def __repr__(self): raise AssertionError("must not render")
    reject(sessions(), {"state": Trap()}, "invalid_payload_type")


def test_cycles_depth_nodes_and_byte_expansion_are_bounded(sessions):
    cycle = []
    cycle.append(cycle)
    reject(sessions(), cycle, "cyclic_payload")
    reject(sessions(max_depth=2), [[[[]]]], "structure_limit")
    reject(sessions(max_nodes=3), [1, 2, 3], "structure_limit")
    reject(sessions(max_bytes=100), {"state": "x" * 101}, "payload_too_large")
    reject(sessions(max_bytes=100), ["a@example.test", "b@example.test"], "payload_too_large")
    reject(sessions(max_identifiers=1), ["a@example.test", "b@example.test"], "identifier_limit")


def test_masked_keys_must_not_collide(sessions):
    reject(sessions(), {"password": "first-value", "api_key": "second-value",
                        "first-value": 1, "second-value": 2}, "masked_key_collision")


def test_detector_failure_and_timeout_send_nothing(sessions, monkeypatch):
    def broken(value):
        raise RuntimeError("must-never-be-disclosed")
    monkeypatch.setattr(redaction, "card_valid", broken)
    reject(sessions(), "4111111111111111", "masking_failed")

    def slow(value):
        time.sleep(0.02)
        return True
    monkeypatch.setattr(redaction, "card_valid", slow)
    reject(sessions(scan_timeout_seconds=0.005), "4111111111111111", "scan_timeout")


def test_token_collision_fails_and_clears_partial_map(sessions, monkeypatch):
    session = sessions()
    monkeypatch.setattr(privacy.secrets, "token_hex", lambda n: "a" * 32)
    reject(session, ["a@example.test", "b@example.test"], "token_collision")


def test_restore_is_scoped_field_limited_single_pass_and_escaped(sessions):
    session = sessions()
    out, _ = send(session, {"state": "alice@example.test"})
    token = out["state"]
    foreign, _ = send(sessions("account_two"), {"state": "other@example.test"})
    forged = token[:-2] + ("a" if token[-2] != "a" else "b") + "]"
    result = session.restore('<script> "' + token + '" & ' + token + " " + foreign["state"] + " " + forged,
                             scope="account_one", field="explanation")
    assert result.startswith("&lt;script&gt; &quot;alice@example.test&quot; &amp; alice@example.test")
    assert foreign["state"] in result and forged in result
    for field in ("score", "label", "probability", "metadata"):
        with pytest.raises(privacy.PrivacyError, match="restoration_field_forbidden"):
            session.restore(token, scope="account_one", field=field)
    with pytest.raises(privacy.PrivacyError, match="scope_mismatch"):
        session.restore(token, scope="account_two", field="explanation")
    assert "alice@example.test" not in session.restore(token.replace("[", "&#91;"), scope="account_one", field="explanation")


def test_existing_irreversible_redaction_is_never_guessed(sessions):
    session = sessions()
    text = "[email] [national_id] [REDACTED:deadbeef] [WITHHELD:secret]"
    out, _ = send(session, {"state": text})
    assert session.restore(out["state"], scope="account_one", field="explanation") == text
    assert session._values == {}


def test_idle_ttl_actually_clears_map_and_close_forbids_reuse(sessions):
    session = sessions(map_ttl_seconds=0.04)
    out, _ = send(session, {"state": "alice@example.test"})
    assert session._values
    time.sleep(0.12)
    assert session._values == {} and session._tokens == {} and session._masked is None
    assert session.restore(out["state"], scope="account_one", field="explanation") == out["state"]
    with pytest.raises(privacy.PrivacyError, match="session_expired"):
        session.mask({"state": "new"})
    other = sessions()
    other.mask("alice@example.test")
    other.close()
    assert not other._values and not other._tokens


def test_session_cannot_be_serialized(sessions):
    session = sessions()
    session.mask("alice@example.test")
    assert not hasattr(session, "__dict__")
    assert "alice" not in repr(session)
    for serialize in (pickle.dumps, copy.copy, copy.deepcopy):
        with pytest.raises(privacy.PrivacyError, match="serialization_forbidden"):
            serialize(session)
    with pytest.raises(TypeError):
        asdict(session)
    with pytest.raises(TypeError):
        json.dumps(session)


def test_timer_does_not_keep_abandoned_session_alive():
    session = privacy.MaskingSession("account_one", privacy.PrivacyPolicy(("email",)))
    session.mask("alice@example.test")
    reference = weakref.ref(session)
    del session
    gc.collect()
    assert reference() is None


def test_secret_literals_are_not_retained_in_regex_cache(sessions):
    sentinel = "unusual-private-test-password-value"
    session = sessions()
    send(session, {"password": sentinel, "state": sentinel})
    session.close()
    assert all(sentinel not in str(key) for key in re._cache)


def test_dispatch_requires_current_scope_policy_processor_and_generation(sessions):
    session = sessions()
    session.mask("alice@example.test")
    gate, spy = privacy.ConsentGate("account_one"), SpyTransport()
    with pytest.raises(privacy.PrivacyError, match="consent_required"):
        gate.dispatch(session, 0, "processor-v1", spy)
    generation = gate.grant(session.policy, "processor-v1")
    with pytest.raises(privacy.PrivacyError, match="consent_required"):
        gate.dispatch(session, generation, "processor-v2", spy)
    other = sessions("account_two")
    other.mask("alice@example.test")
    with pytest.raises(privacy.PrivacyError, match="scope_mismatch"):
        gate.dispatch(other, generation, "processor-v1", spy)
    gate.grant(privacy.PrivacyPolicy(("email",)), "processor-v1")
    with pytest.raises(privacy.PrivacyError, match="consent_required"):
        gate.dispatch(session, generation, "processor-v1", spy)
    assert spy.sent == [] and gate.dispatch_count == 0


def test_retries_use_same_immutable_masked_bytes_and_revocation_blocks(sessions):
    session = sessions()
    payload = {"state": "alice@example.test", "counter": 1}
    session.mask(payload)
    payload["state"] = "new-raw@example.test"
    gate, spy = privacy.ConsentGate("account_one"), SpyTransport()
    generation = gate.grant(session.policy, "processor-v1")
    gate.dispatch(session, generation, "processor-v1", spy)
    gate.dispatch(session, generation, "processor-v1", spy)
    assert spy.sent[0] == spy.sent[1] and b"new-raw" not in spy.sent[0]
    gate.revoke()
    with pytest.raises(privacy.PrivacyError, match="consent_required"):
        gate.dispatch(session, generation, "processor-v1", spy)
    assert len(spy.sent) == gate.dispatch_count == 2
    with pytest.raises(privacy.PrivacyError, match="session_already_masked"):
        session.mask({"state": "replacement"})


@pytest.mark.parametrize("name,value", [("CLAWMETRY_OFFLINE", "1"), ("SELF_HOSTED", "true"),
                                        ("CLAWMETRY_SELF_HOSTED", "1"),
                                        ("CLAWMETRY_ENDPOINT", "https://private.example.test"),
                                        ("CLAWMETRY_INGEST_URL", "https://private.example.test")])
def test_egress_is_rechecked_before_every_attempt(sessions, monkeypatch, name, value):
    session = sessions()
    session.mask("alice@example.test")
    gate, spy = privacy.ConsentGate("account_one"), SpyTransport()
    generation = gate.grant(session.policy, "processor-v1")
    gate.dispatch(session, generation, "processor-v1", spy)
    monkeypatch.setenv(name, value)
    with pytest.raises(privacy.PrivacyError, match="egress_suppressed"):
        gate.dispatch(session, generation, "processor-v1", spy)
    assert len(spy.sent) == 1


@pytest.mark.parametrize("identifier", [
    "a" * (320 - len("@example.test")) + "@example.test", "+44 20 7946 0958",
    "GB82 WEST 1234 5698 7654 32", "BE68 5390 0754 7034", "BE68539007547034", "4111 1111 1111 1111",
    "AB 12 34 56 C", "ab 12 34 56 c", "be68539007547034", "gB82 WeSt 1234 5698 7654 32",
    "123-45-6789", "111222333", aadhaar(),
])
def test_identifier_windows_preserve_full_values_across_boundaries(sessions, identifier):
    for offset in range(512, 1024):
        with sessions() as session:
            prefix = ("x " * ((offset + 1) // 2))[:offset]
            if prefix and prefix[-1] != " ":
                prefix = prefix[:-1] + " "
            payload = {"state": prefix + identifier + " NEXT", "again": identifier}
            out, spy = send(session, payload)
            token = out["again"]
            assert identifier.encode() not in spy.sent[0]
            assert out["state"] == prefix + token + " NEXT", offset
            assert session.restore(token, scope="account_one", field="explanation") == identifier


def test_overlong_candidate_fails_instead_of_leaking_a_partial_email(sessions):
    reject(sessions(), {"state": "a" * 310 + "@example.test"}, "text_span_limit")
    reject(sessions(), {"state": " " * 4097}, "text_span_limit")


@pytest.mark.parametrize("field", ["connectionString", "headers[Authorization]", "headers[X-API-Key]",
                                    "headers[Set-Cookie]", "apiKey", "clientSecret",
                                    "aws_secret_access_key", "http.request.header.x_openai_api_key"])
def test_secret_header_and_camel_case_aliases_are_wholly_withheld(sessions, field):
    out, spy = send(sessions(), {field: ["alice@example.test", 123, "short!"]})
    assert list(out.values()) == [privacy.SECRET_REMOVED]
    assert b"alice" not in spy.sent[0] and b"short" not in spy.sent[0]


def test_full_provider_secret_alphabet_is_irreversible(sessions):
    values = ["sk-proj-" + "a" * 20 + "_" + "b" * 20,
              "sk-" + "c" * 20 + "-" + "d" * 20 + "-",
              "sk-ant-" + "e" * 20 + "_" + "f" * 20 + "-"]
    session = sessions()
    out, _ = send(session, {"state": values})
    assert out["state"] == [privacy.SECRET_REMOVED] * len(values)
    assert session._values == {}


def test_actual_adversarial_regex_inputs_are_bounded_in_subprocess():
    # A real subprocess deadline catches a detector that never yields to the
    # cooperative clock check, independently of mocked detector/clock tests.
    import subprocess
    import sys
    script = r'''
import time
from clawmetry import redaction
from clawmetry.assessment_privacy import MaskingSession, PrivacyPolicy, PrivacyError
cases = [
    "%" * 60000,
    "-----BEGIN PRIVATE KEY-----\n" * 2100,
    "+111111111111111111111111 " * 2200,
    ("% " * 2000),
    "-----BEGIN PRIVATE KEY-----\n" * 120,
    "+111111111111111111111111 " * 160,
]
started = time.monotonic()
for value in cases:
    with MaskingSession("test", PrivacyPolicy(("email",), scan_timeout_seconds=.01)) as session:
        try:
            session.mask({"state": value})
        except PrivacyError:
            pass
assert time.monotonic() - started < .8
started = time.monotonic()
assert redaction._EMAIL.search("%" * 60000) is None
assert list(redaction._PRIVATE_KEY.finditer("-----BEGIN PRIVATE KEY-----\n" * 2100)) == []
assert time.monotonic() - started < .5
'''
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, timeout=3, check=False)
    assert result.returncode == 0, result.stderr.decode()


@pytest.mark.parametrize("value", ["4111111111111111 12", "4111 1111 1111 1111 7",
                                    "+44 20 7946 0958 1234"])
def test_ambiguous_numeric_tail_sends_no_partial_identifier(sessions, value):
    reject(sessions(), {"state": value}, "ambiguous_identifier")


def test_unbroken_invalid_number_is_not_reinterpreted_as_valid_card_prefix(sessions):
    value = "411111111111111112"
    assert not redaction.card_valid(value)
    assert not redaction.card_candidate_ambiguous(value)
    out, _ = send(sessions(), {"state": value})
    assert out["state"] == value




def test_egress_failure_and_transport_errors_expose_only_controlled_codes(sessions, monkeypatch):
    session = sessions()
    session.mask("alice@example.test")
    gate, spy = privacy.ConsentGate("account_one"), SpyTransport()
    generation = gate.grant(session.policy, "processor-v1")
    def broken(): raise RuntimeError("private-error-detail")
    monkeypatch.setattr(endpoints, "egress_suppressed", broken)
    with pytest.raises(privacy.PrivacyError, match="^egress_unavailable$"):
        gate.dispatch(session, generation, "processor-v1", spy)
    assert spy.sent == []
    monkeypatch.setattr(endpoints, "egress_suppressed", lambda: False)
    def failed(encoded, timeout): raise RuntimeError("private-error-detail")
    with pytest.raises(privacy.PrivacyError, match="^transport_failed$"):
        gate.dispatch(session, generation, "processor-v1", failed)
    assert gate.dispatch_count == 1


def test_revoke_ack_waits_for_started_send_then_blocks_queued_retry(sessions):
    session = sessions()
    session.mask("alice@example.test")
    gate, spy = privacy.ConsentGate("account_one"), SpyTransport()
    generation = gate.grant(session.policy, "processor-v1")
    entered, finish, revoked = threading.Event(), threading.Event(), threading.Event()
    def transport(encoded, timeout):
        spy(encoded, timeout=timeout)
        entered.set()
        assert finish.wait(1)
    def revoke():
        gate.revoke()
        revoked.set()
    with ThreadPoolExecutor(max_workers=2) as executor:
        sent = executor.submit(gate.dispatch, session, generation, "processor-v1", transport)
        assert entered.wait(1)
        revocation = executor.submit(revoke)
        assert not revoked.wait(0.04)
        finish.set()
        sent.result()
        revocation.result()
    with pytest.raises(privacy.PrivacyError, match="consent_required"):
        gate.dispatch(session, generation, "processor-v1", spy)
    assert len(spy.sent) == 1 and revoked.is_set()


def test_waiting_dispatch_rechecks_expiry_and_lock_deadline(sessions):
    session, waiting = sessions(), sessions(map_ttl_seconds=0.05)
    session.mask("alice@example.test")
    waiting.mask("other@example.test")
    gate, spy = privacy.ConsentGate("account_one"), SpyTransport()
    generation = gate.grant(session.policy, "processor-v1")
    entered, finish = threading.Event(), threading.Event()
    def transport(encoded, timeout):
        entered.set()
        assert finish.wait(1)
        spy(encoded, timeout=timeout)
    with ThreadPoolExecutor(max_workers=2) as executor:
        sending = executor.submit(gate.dispatch, session, generation, "processor-v1", transport)
        assert entered.wait(1)
        with pytest.raises(privacy.PrivacyError, match="dispatch_timeout"):
            gate.dispatch(session, generation, "processor-v1", spy, timeout_seconds=0.01)
        time.sleep(0.07)
        finish.set()
        sending.result()
    other_gate = privacy.ConsentGate("account_one")
    other_generation = other_gate.grant(waiting.policy, "processor-v1")
    with pytest.raises(privacy.PrivacyError, match="session_expired"):
        other_gate.dispatch(waiting, other_generation, "processor-v1", spy)
    assert len(spy.sent) == 1
