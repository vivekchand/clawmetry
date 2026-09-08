"""Regressions for the 2026-08-19 desktop report: a Pro account was shown
the runtime upgrade modal, and sync.log filled with 400s from the daemon
proxy.

Two independent root causes, both covered here:

1. ``_ProxyStore.__getattr__`` forwarded calls to the daemon as kwargs only
   and silently DROPPED every positional argument, so the daemon answered
   ``400 missing required argument`` and callers read that as an empty
   result.
2. Entitlement resolution falls back to OSS-free while a linked account's
   plan is still being fetched (the daemon writes ``cloud_plan.json`` a few
   seconds after boot). That verdict means "unknown", not "free", and
   locking on it paywalled a paying user.
"""

import json
import os

import pytest


# ── 1. proxy positional-argument binding ─────────────────────────────────────

@pytest.fixture()
def proxy_bind():
    from clawmetry.local_store import _proxy_call_kwargs
    return _proxy_call_kwargs


def test_positional_arg_is_bound_not_dropped(proxy_bind):
    """The exact call that 400'd: sessions.py's direct-store fallback passes
    the id list positionally."""
    assert proxy_bind("query_session_authority_counts", (["a", "b"],), {}) == {
        "session_ids": ["a", "b"]
    }


def test_keyword_call_still_passes_through(proxy_bind):
    assert proxy_bind("query_session_authority_counts", (), {"session_ids": ["a"]}) == {
        "session_ids": ["a"]
    }


def test_positional_write_is_bound(proxy_bind):
    """approvals.py calls ``store.ingest_approval({...})`` positionally."""
    assert proxy_bind("ingest_approval", ({"id": "x"},), {}) == {
        "approval": {"id": "x"}
    }


def test_unknown_method_reports_unbindable(proxy_bind):
    assert proxy_bind("no_such_method_at_all", (1,), {}) is None


def test_keyword_only_signature_is_not_faked(proxy_bind):
    """query_events is keyword-only; a positional call is a real TypeError on
    a direct store too, so the proxy must not invent a binding."""
    assert proxy_bind("query_events", ("tool_call",), {}) is None


def test_private_methods_are_never_proxied(monkeypatch):
    """``_fetch`` is deliberately off the daemon allowlist (arbitrary SQL over
    RPC). Forwarding it only produced a 400 the caller swallowed, so it must
    not even reach the transport."""
    import routes.local_query as lq
    from clawmetry.local_store import _ProxyStore

    # A raised assertion would be swallowed by _forward's except-clause, so
    # record the attempt instead of throwing.
    sent = []

    def _record(method_name, *a, **k):
        sent.append(method_name)

    monkeypatch.setattr(lq, "local_store_via_daemon", _record)
    monkeypatch.setattr(lq, "local_store_call_via_daemon", _record, raising=False)
    assert _ProxyStore()._fetch("SELECT 1") is None
    assert sent == [], f"_fetch must not be sent to the daemon (sent {sent})"


def test_dunder_probe_does_not_resolve_to_a_call():
    """Returning a callable for ``__deepcopy__`` & friends makes the proxy
    lie about protocols it does not implement."""
    from clawmetry.local_store import _ProxyStore
    with pytest.raises(AttributeError):
        _ProxyStore().__deepcopy__


# ── 2. entitlement "pending" ────────────────────────────────────────────────

@pytest.fixture()
def ent(tmp_path, monkeypatch):
    from clawmetry import entitlements as _ent
    monkeypatch.setattr(_ent, "_LICENSE_PATH", str(tmp_path / "license.key"))
    monkeypatch.setattr(_ent, "_CLOUD_PLAN_CACHE", str(tmp_path / "cloud_plan.json"))
    monkeypatch.setattr(_ent, "_CONNECT_CONFIG_PATH", str(tmp_path / "config.json"))
    return _ent, tmp_path


def _link_account(tmp_path):
    (tmp_path / "config.json").write_text(
        json.dumps({"api_key": "cm_test", "account_email": "a@b.c"})
    )


def test_pending_true_while_linked_account_has_no_plan_yet(ent):
    """The boot window: connected, but cloud_plan.json has not landed."""
    _ent, tmp_path = ent
    _link_account(tmp_path)
    assert _ent.plan_pending() is True


def test_pending_false_once_the_plan_lands(ent):
    _ent, tmp_path = ent
    _link_account(tmp_path)
    (tmp_path / "cloud_plan.json").write_text(
        json.dumps({"plan": "cloud_pro", "node_limit": 1, "expiry": None})
    )
    assert _ent.plan_pending() is False


def test_pending_false_on_an_unlinked_machine(ent):
    """No account at all: OSS-free is the true answer, not an unknown one."""
    _ent, _tmp = ent
    assert _ent.plan_pending() is False


def test_pending_false_when_config_has_no_api_key(ent):
    _ent, tmp_path = ent
    (tmp_path / "config.json").write_text(json.dumps({"account_email": "a@b.c"}))
    assert _ent.plan_pending() is False


def test_oss_fallback_really_would_lock_paid_runtimes(ent):
    """Guards the premise: without a plan we resolve to OSS, whose runtime
    set excludes claude_code. That is why 'pending' has to exist."""
    _ent, tmp_path = ent
    _link_account(tmp_path)
    resolved = _ent.get_entitlement(force=True)
    assert resolved.tier == "oss"
    assert "claude_code" not in (resolved.runtimes or [])
    assert _ent.plan_pending() is True


# ── 3. policy-reload logging is change-triggered ────────────────────────────

def test_unchanged_policy_reload_does_not_log_info(tmp_path, monkeypatch, caplog):
    """1,382 identical INFO lines in one sync.log buried real errors."""
    import logging
    from clawmetry import approvals

    policy_file = tmp_path / "policies.yml"
    policy_file.write_text("# contents are parsed by the stubbed loader\n")
    policies = [{"name": "p1", "tool": "Bash", "action": "require_approval"}]
    monkeypatch.setattr(approvals, "POLICIES_PATH", policy_file)
    monkeypatch.setattr(approvals, "_load_yaml", lambda _raw: policies)
    monkeypatch.setattr(approvals, "_last_policy_signature", None)

    with caplog.at_level(logging.INFO, logger=approvals.log.name):
        approvals.load_policies()
        first = len([r for r in caplog.records if r.levelno == logging.INFO])
        approvals.load_policies()
        approvals.load_policies()
        total = len([r for r in caplog.records if r.levelno == logging.INFO])

    assert first == 1, "the first load should announce itself"
    assert total == 1, "identical reloads must stay quiet"


# ── 4. the flag actually reaches the wire ───────────────────────────────────

@pytest.fixture
def api_client(monkeypatch, tmp_path):
    """Flask test client for bp_entitlement over a clean HOME.

    Both HOME and USERPROFILE are set because ``os.path.expanduser`` on
    Windows honours only USERPROFILE (see #3850).
    """
    import importlib

    from flask import Flask

    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()

    from routes.entitlement import bp_entitlement

    app = Flask(__name__)
    app.register_blueprint(bp_entitlement)
    (tmp_path / ".clawmetry").mkdir(parents=True, exist_ok=True)
    return app.test_client(), tmp_path / ".clawmetry"


def test_api_runtimes_reports_pending_for_a_linked_account(api_client):
    """The boot window the desktop app hit: connected, plan not fetched yet."""
    client, cfgdir = api_client
    (cfgdir / "config.json").write_text(json.dumps({"api_key": "cm_test"}))

    body = client.get("/api/runtimes").get_json()
    assert body["pending"] is True, (
        "a linked account with no resolved plan must be advertised as pending, "
        "or the client locks every paid runtime for a paying user"
    )
    assert not any(r.get("locked") for r in body["runtimes"])


def test_api_runtimes_is_not_pending_once_the_plan_lands(api_client):
    client, cfgdir = api_client
    (cfgdir / "config.json").write_text(json.dumps({"api_key": "cm_test"}))
    (cfgdir / "cloud_plan.json").write_text(
        json.dumps({"plan": "cloud_pro", "node_limit": 1, "expiry": None})
    )

    body = client.get("/api/runtimes").get_json()
    assert body["pending"] is False
    entitled = {r["id"]: r.get("entitled") for r in body["runtimes"]}
    assert entitled.get("claude_code") is True


def test_api_runtimes_is_not_pending_on_an_unlinked_machine(api_client):
    """No account: OSS-free is the truth, and the teaser is legitimate."""
    client, _cfgdir = api_client
    assert client.get("/api/runtimes").get_json()["pending"] is False


def test_api_entitlement_carries_pending(api_client):
    client, cfgdir = api_client
    (cfgdir / "config.json").write_text(json.dumps({"api_key": "cm_test"}))
    assert client.get("/api/entitlement").get_json()["pending"] is True
