"""`clawmetry status` resolves and shows the linked account email.

Fastest way to catch the "my node is on the wrong account" trap: see which
account the node's api_key is linked to. Best-effort + offline-safe.
"""
import json

import clawmetry.cli as cli


class _Resp:
    def __init__(self, body):
        self._b = body

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_resolves_email_and_plan(monkeypatch):
    import urllib.request as ur
    monkeypatch.setattr(ur, "urlopen", lambda url, timeout=0: _Resp(
        json.dumps({"email": "vivekchand.kd@gmail.com", "plan": "cloud_pro"}).encode()))
    email, plan = cli._resolve_account_email("cm_abcdef0123456789")
    assert email == "vivekchand.kd@gmail.com"
    assert plan == "cloud_pro"


def test_non_cm_key_is_skipped_no_network(monkeypatch):
    import urllib.request as ur

    def _boom(*a, **k):
        raise AssertionError("must not hit the network for a non-cm_ key")
    monkeypatch.setattr(ur, "urlopen", _boom)
    assert cli._resolve_account_email("not-a-key") == (None, None)
    assert cli._resolve_account_email("") == (None, None)


def test_offline_is_graceful(monkeypatch):
    import urllib.request as ur
    monkeypatch.setattr(ur, "urlopen",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("offline")))
    assert cli._resolve_account_email("cm_xyz0123456789") == (None, None)


def test_respects_app_base_env(monkeypatch):
    import urllib.request as ur
    seen = {}

    def _cap(url, timeout=0):
        seen["url"] = url
        return _Resp(b"{}")
    monkeypatch.setenv("CLAWMETRY_APP_BASE", "https://staging.example.com")
    monkeypatch.setattr(ur, "urlopen", _cap)
    cli._resolve_account_email("cm_abc0123456789")
    assert seen["url"].startswith("https://staging.example.com/api/cloud/account?token=")
