"""TRR-08: local proxy authenticates privately and installs only confirmed grants.

AC-GUX-TRR-001.7
"""
import io
import json
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest
from flask import Flask

from routes import trial
from clawmetry import license as lic


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.delenv('CLOUD_MODE', raising=False)
    monkeypatch.setattr(lic, 'LICENSE_PATH', str(tmp_path / 'license.key'))
    monkeypatch.setattr(trial, '_local_api_key', lambda: 'cm_private_test')
    app = Flask(__name__)
    app.register_blueprint(trial.bp_trial)
    return app.test_client()


def upstream(monkeypatch, payload):
    calls = []
    def respond(req, timeout):
        calls.append(req)
        return io.BytesIO(json.dumps(payload).encode())
    monkeypatch.setattr(trial.urllib.request, 'urlopen', respond)
    return calls


def test_eligibility_does_not_claim_or_expose_credentials(client, monkeypatch):
    calls = upstream(monkeypatch, {'eligible': True, 'free_days': 60, 'key': 'never_expose'})
    response = client.get('/api/trial/extension')
    assert response.status_code == 200
    assert response.json == {'eligible': True, 'free_days': 60}
    assert response.headers['Cache-Control'] == 'no-store'
    assert calls[0].method == 'GET' and calls[0].data is None
    assert calls[0].get_header('X-api-key') == 'cm_private_test'


def test_local_claim_activates_before_confirming(client, monkeypatch):
    from clawmetry import entitlements as ent
    calls = upstream(monkeypatch, {'ok': True, 'key': 'signed', 'grant_state': 'applied', 'trial_end': '2027-01-05T08:00:00Z'})
    monkeypatch.setattr(ent, 'get_entitlement', lambda **kw: SimpleNamespace(tier='trial', expired=True))
    activated = []
    monkeypatch.setattr(lic, 'activate', lambda key, **kw: (activated.append((key, kw)) or True, 'ok'))
    response = client.post('/api/trial/extension', json={'reason': 'price', 'feedback': 'Need more value'})
    assert response.status_code == 200 and response.json['grant_state'] == 'applied'
    assert 'key' not in response.json
    assert activated == [('signed', {'actor': 'trial-recovery'})]
    assert json.loads(calls[0].data)['feedback'] == 'Need more value'


def test_paid_license_wins_while_request_in_flight(client, monkeypatch):
    from clawmetry import entitlements as ent
    upstream(monkeypatch, {'ok': True, 'key': 'trial', 'grant_state': 'applied'})
    monkeypatch.setattr(ent, 'get_entitlement', lambda **kw: SimpleNamespace(tier='pro', expired=False))
    monkeypatch.setattr(lic, 'activate', lambda *a, **kw: pytest.fail('paid license was replaced'))
    assert client.post('/api/trial/extension', json={}).status_code == 200


def test_reserved_grant_can_retry_failed_local_activation(client, monkeypatch):
    from clawmetry import entitlements as ent
    upstream(monkeypatch, {'ok': True, 'key': 'trial', 'grant_state': 'applied'})
    monkeypatch.setattr(ent, 'get_entitlement', lambda **kw: SimpleNamespace(tier='trial', expired=True))
    monkeypatch.setattr(lic, 'activate', lambda *a, **kw: (False, 'disk full'))
    response = client.post('/api/trial/extension', json={})
    assert response.status_code == 502 and 'reserved' in response.json['error']
    assert 'key' not in response.json


@pytest.mark.parametrize('body', [[], {'email': 'other@example.com'}, {'days': 600}, {'tier': 'pro'}, {'feedback': 'x'*501}, {'reason': []}])
def test_identity_and_benefit_are_server_owned(client, monkeypatch, body):
    monkeypatch.setattr(trial.urllib.request, 'urlopen', lambda *a, **kw: pytest.fail('invalid request forwarded'))
    assert client.post('/api/trial/extension', json=body).status_code == 400


def test_cross_site_and_cloud_proxy_rejected(client, monkeypatch):
    assert client.post('/api/trial/extension', json={}, headers={'Origin': 'https://other.example'}).status_code == 403
    assert client.get('/api/trial/extension', headers={'Sec-Fetch-Site': 'cross-site'}).status_code == 403
    monkeypatch.setenv('CLOUD_MODE', '1')
    assert client.get('/api/trial/extension').status_code == 409


@pytest.mark.parametrize('machine_key', ['', 'cm_machine_unlinked', 'cm_revoked'])
def test_installed_trial_owns_recovery_despite_unlinked_machine_key(client, monkeypatch, machine_key):
    import time
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    monkeypatch.setattr(lic, '_PUBLIC_KEY_PEM', public)
    token = lic._encode_token({'sub':'human@example.com','tier':'trial','nodes':1,'jti':'lic_test','exp':int(time.time())-86400}, private)
    monkeypatch.setattr(trial, '_local_api_key', lambda: machine_key)
    with open(lic.LICENSE_PATH, 'w') as fh:
        fh.write(token)
    calls = upstream(monkeypatch, {'eligible': True})
    assert client.get('/api/trial/extension').status_code == 200
    assert calls[0].get_header('Authorization') == 'Bearer ' + token
    assert calls[0].get_header('X-api-key') is None


def test_network_and_upstream_errors_are_actionable(client, monkeypatch):
    def unavailable(*a, **kw):
        raise HTTPError('https://service.example', 403, 'raw secret', {}, None)
    monkeypatch.setattr(trial.urllib.request, 'urlopen', unavailable)
    response = client.get('/api/trial/extension')
    assert response.status_code == 401 and 'Sign in' in response.json['error']
    assert 'secret' not in response.json['error']
    monkeypatch.setattr(trial.urllib.request, 'urlopen', lambda *a, **kw: io.BytesIO(b'[]'))
    assert client.get('/api/trial/extension').status_code == 502


def test_applied_without_a_key_is_not_a_local_confirmation(client, monkeypatch):
    upstream(monkeypatch, {'ok': True, 'grant_state': 'applied'})
    response = client.post('/api/trial/extension', json={})
    assert response.status_code == 502 and 'reserved' in response.json['error']


def test_invalid_trial_file_uses_account_key_without_forwarding_forgery(client, monkeypatch):
    with open(lic.LICENSE_PATH, 'w') as fh:
        fh.write('CLAW1.forged.signature')
    calls = upstream(monkeypatch, {'eligible': False})
    assert client.get('/api/trial/extension').status_code == 200
    assert calls[0].get_header('X-api-key') == 'cm_private_test'
    assert calls[0].get_header('Authorization') is None


def test_binary_license_file_falls_back_to_account_key(client, monkeypatch):
    with open(lic.LICENSE_PATH, 'wb') as fh:
        fh.write(b'\xff\x00\xfe')
    calls = upstream(monkeypatch, {'eligible': False})
    assert client.get('/api/trial/extension').status_code == 200
    assert calls[0].get_header('X-api-key') == 'cm_private_test'


@pytest.mark.parametrize('base', ['file:///private/tmp', 'ftp://example.com', 'http://example.com', 'https://user:secret@example.com', 'https://example.com?other=1', 'https://[broken'])
def test_proxy_refuses_non_network_or_insecure_trial_service(client, monkeypatch, base):
    monkeypatch.setattr(lic, '_cloud_base', lambda: base)
    monkeypatch.setattr(trial.urllib.request, 'urlopen', lambda *a, **kw: pytest.fail('invalid service fetched'))
    assert client.get('/api/trial/extension').status_code == 502


def test_loopback_http_test_service_remains_supported(client, monkeypatch):
    monkeypatch.setattr(lic, '_cloud_base', lambda: 'http://127.0.0.1:8999')
    upstream(monkeypatch, {'eligible': False})
    assert client.get('/api/trial/extension').status_code == 200
