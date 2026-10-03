import json
import os
from urllib.error import HTTPError

import pytest

from clawmetry import assistant_managed as managed


def test_unconfigured_is_truthful(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_BUILDER_API_KEY", raising=False)
    assert managed.configured() is False
    assert managed.status() == {
        "configured": False,
        "available": False,
        "endpoint_ready": False,
        "capability_advertised": False,
        "balance_cents": None,
    }


def test_complete_uses_server_key_and_contract(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_BUILDER_API_KEY", "cmak_test_only")
    monkeypatch.setenv("CLAWMETRY_BUILDER_BASE_URL", "http://builder.test")
    seen = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            server_key = managed.X25519PrivateKey.generate()
            public = managed.X25519PublicKey.from_public_bytes(managed._decode_b64(seen["body"]["response_public_key"]))
            key = managed.HKDF(algorithm=managed.hashes.SHA256(), length=32, salt=None, info=managed.ENVELOPE_INFO).derive(server_key.exchange(public))
            nonce = os.urandom(12)
            envelope = {"v": 1, "alg": managed.ENVELOPE_ALGORITHM,
                        "ephemeral_public_key": managed._b64(server_key.public_key().public_bytes(managed.serialization.Encoding.Raw, managed.serialization.PublicFormat.Raw)),
                        "nonce": managed._b64(nonce),
                        "ciphertext": managed._b64(managed.AESGCM(key).encrypt(nonce, b'{"text":"grounded answer"}', managed.ENVELOPE_AAD))}
            return json.dumps({"envelope": envelope, "usage": {}, "balance": 421}).encode()

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        seen["headers"] = dict(req.headers)
        seen["body"] = json.loads(req.data.decode())
        assert timeout == 60
        return Response()

    monkeypatch.setattr(managed.request, "urlopen", fake_urlopen)
    assert managed.complete("system", "question") == "grounded answer"
    assert seen["url"] == "http://builder.test/api/assistant/complete"
    assert len(managed._decode_b64(seen["body"].pop("response_public_key"))) == 32
    assert seen["body"] == {"system": "system", "prompt": "question", "max_tokens": 2400}
    assert seen["headers"]["Authorization"] == "Bearer cmak_test_only"
    assert seen["headers"]["Idempotency-key"]


def test_status_only_reports_ledger_starter_grant(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_BUILDER_API_KEY", "cmak_test_only")
    monkeypatch.setattr(
        managed,
        "_json_request",
        lambda path, **kwargs: {
            "/api/config": {"managed_assistant": {
                "complete": "/api/assistant/complete",
                "status": "/api/assistant/status",
                "max_tokens": 2400,
            }},
            "/api/assistant/status": {
                "endpoint_ready": True, "available": True,
                "balance": 700, "starter_allowance_cents": 500,
            },
        }[path],
    )
    assert managed.status() == {
        "configured": True,
        "available": True,
        "endpoint_ready": True,
        "capability_advertised": True,
        "balance_cents": 700,
        "starter_allowance_cents": 500,
    }


def test_balance_does_not_claim_available_before_endpoint_deploy(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_BUILDER_API_KEY", "cmak_test_only")

    def fake(path, **kwargs):
        if path == "/api/config":
            return {"managed_assistant": {
                "complete": "/api/assistant/complete",
                "status": "/api/assistant/status",
                "max_tokens": 2400,
            }}
        if path == "/api/assistant/status":
            raise managed.ManagedAssistantUnavailable("managed assistant unavailable")
        if path == "/api/billing":
            return {"balance_cents": 500, "entries": []}
        raise AssertionError(path)

    monkeypatch.setattr(managed, "_json_request", fake)
    assert managed.status() == {
        "configured": True,
        "available": False,
        "endpoint_ready": False,
        "capability_advertised": True,
        "balance_cents": 500,
    }


def test_checkout_returns_existing_url(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_BUILDER_API_KEY", "cmak_test_only")
    seen = {}

    def fake(path, **kwargs):
        seen.update(kwargs)
        return {"url": "https://checkout.stripe.test/session"}

    monkeypatch.setattr(managed, "_json_request", fake)
    assert managed.checkout() == "https://checkout.stripe.test/session"
    assert seen["method"] == "POST"
    assert seen["payload"] == {"amount_cents": 500, "currency": "usd"}


def test_errors_never_include_response_body_or_key(monkeypatch):
    key = "cmak_secret_should_not_escape"
    monkeypatch.setenv("CLAWMETRY_BUILDER_API_KEY", key)

    def fail(*args, **kwargs):
        raise HTTPError(
            "https://builder.test/api/assistant/complete", 500, "failure",
            {}, None,
        )

    monkeypatch.setattr(managed.request, "urlopen", fail)
    with pytest.raises(managed.ManagedAssistantUnavailable) as exc:
        managed.complete("system", "question")
    assert key not in str(exc.value)
    assert "failure" not in str(exc.value)


def test_plaintext_managed_response_is_rejected(monkeypatch):
    monkeypatch.setattr(managed, "_json_request", lambda *a, **kw: {"text": "private answer"})
    with pytest.raises(managed.ManagedAssistantUnavailable):
        managed.complete("system", "question")


def test_missing_crypto_does_not_prevent_dashboard_import():
    import subprocess
    import sys
    code = """
import sys
sys.modules['cryptography'] = None
from clawmetry import assistant_managed as managed
assert managed._CRYPTO_AVAILABLE is False
try:
    managed.complete('system', 'prompt')
except managed.ManagedAssistantUnavailable:
    pass
else:
    raise AssertionError('managed transport must never fall back to plaintext')
import routes.assistant
"""
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)
