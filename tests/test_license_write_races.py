"""TRR-07/08: paid and extended licenses survive independent process writers.

AC-GUX-TRR-001.8
"""
import multiprocessing
import os
import time
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from clawmetry import license as lic


@pytest.fixture
def keys(monkeypatch, tmp_path):
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    monkeypatch.setattr(lic, '_PUBLIC_KEY_PEM', public)
    path = str(tmp_path / 'license.key')
    def token(tier, days):
        return lic._encode_token({'sub':'test@example.com', 'tier':tier, 'nodes':1, 'iat':int(time.time()), 'exp':int(time.time()) + days*86400}, private)
    return path, public, token


def _writer(public, path, key, ready, start, outcomes):
    from clawmetry import license as worker
    worker._PUBLIC_KEY_PEM = public
    ready.put(True)
    start.wait(10)
    try:
        outcomes.put(('ok', worker._store_license_key(key, path=path)))
    except Exception as exc:
        outcomes.put(('error', type(exc).__name__))


@pytest.mark.parametrize('first', ['trial', 'pro'])
@pytest.mark.parametrize('tier', ['pro', 'starter', 'enterprise', 'selfhosted_pro', 'future_paid'])
def test_paid_key_wins_in_both_sequential_orders(keys, first, tier):
    path, _, token = keys
    paid, trial = token(tier, 365), token('trial', 60)
    lic._store_license_key(paid if first == 'pro' else trial, path=path)
    lic._store_license_key(trial if first == 'pro' else paid, path=path)
    assert Path(path).read_text().strip() == paid
    if os.name == 'posix':
        assert os.stat(path).st_mode & 0o777 == 0o600


def test_stale_trial_cannot_shorten_extension(keys):
    path, _, token = keys
    extended = token('trial', 60)
    lic._store_license_key(extended, path=path)
    assert not lic._store_license_key(token('trial', 1), path=path)
    assert Path(path).read_text().strip() == extended


def test_invalid_or_expired_heartbeat_cannot_replace_key(keys):
    path, _, token = keys
    paid = token('pro', 365)
    lic._store_license_key(paid, path=path)
    for invalid in ('CLAW1.bad.signature', token('trial', -1)):
        with pytest.raises(ValueError):
            lic._store_license_key(invalid, path=path)
    assert Path(path).read_text().strip() == paid


@pytest.mark.parametrize('iteration', range(2))
def test_paid_wins_concurrent_process_activation_and_heartbeat(keys, iteration):
    path, public, token = keys
    paid, trial = token('pro', 365), token('trial', 60)
    ctx = multiprocessing.get_context('spawn')
    ready, outcomes, start = ctx.Queue(), ctx.Queue(), ctx.Event()
    processes = [ctx.Process(target=_writer, args=(public,path,key,ready,start,outcomes)) for key in (paid,trial)]
    try:
        with lic._license_write_lock(path):
            for process in processes:
                process.start()
            for _ in processes:
                assert ready.get(timeout=15)
            start.set()
        for process in processes:
            process.join(15)
            assert process.exitcode == 0
        assert all(outcomes.get(timeout=2)[0] == 'ok' for _ in processes)
        assert Path(path).read_text().strip() == paid
        assert not list(Path(path).parent.glob('.license-*'))
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(5)


def test_heartbeat_uses_shared_writer_preserving_paid_key(keys, monkeypatch):
    import clawmetry.sync as sync
    path, _, token = keys
    paid = token('pro', 365)
    Path(path).write_text(paid + '\n')
    original = sync.os.path.expanduser
    monkeypatch.setattr(sync.os.path, 'expanduser', lambda value: path if value == '~/.clawmetry/license.key' else original(value))
    sync._maybe_install_license_from_heartbeat({'license_key': token('trial',60)})
    assert Path(path).read_text().strip() == paid


def test_verified_license_repairs_a_corrupt_binary_file(keys):
    path, _, token = keys
    Path(path).write_bytes(b'\xff\x00\xfe')
    paid = token('pro', 365)
    assert lic._store_license_key(paid, path=path)
    assert Path(path).read_text().strip() == paid
