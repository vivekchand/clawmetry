"""`clawmetry status` is a READ. It must never download the pro wheel.

Founder live-hit 2026-08-23: `clawmetry status --show-key` took 85s on a Linux
box while taking ~2s on a Mac. cProfile put 82.6s of it inside
``socket.connect`` across 8 hanging connects, reached via

    _cmd_status
      -> sync._persist_cloud_plan_to_disk        (the "self-heal plan cache" line)
        -> sync._sync_auto_update_with_plan
          -> license.auto_provision_pro          (20s entitlement probe)
            -> license._provision_pro_wheel      (60s wheel GET)

The box had a global IPv6 address and a default route from RA, but no working
IPv6 path. glibc therefore ordered AAAA first, and
``socket.create_connection`` walks getaddrinfo results strictly in order with
no Happy Eyeballs — so each call burned its FULL timeout before ever trying
the IPv4 address that answered in 23ms.

The timeouts are the daemon's business, not a status read's. These tests pin
the ``allow_provision=False`` contract that keeps the read local.
"""

import clawmetry.sync as sync


def test_persist_cloud_plan_skips_provision_when_disallowed(monkeypatch):
    """allow_provision=False must not reach the network provisioner."""
    called = []

    def _boom(*a, **kw):  # pragma: no cover - must never run
        called.append(a)
        raise AssertionError("auto_provision_pro must not run for a read")

    monkeypatch.setattr("clawmetry.license.auto_provision_pro", _boom)
    monkeypatch.setattr("clawmetry.license._pro_installed_version", lambda: None)

    sync._sync_auto_update_with_plan("cloud_pro", allow_provision=False)

    assert called == []


def test_persist_cloud_plan_forwards_the_flag(monkeypatch):
    """_persist_cloud_plan_to_disk must thread allow_provision through rather
    than silently provisioning on behalf of its caller."""
    seen = {}

    def _fake(tier, *, allow_provision=True):
        seen["tier"] = tier
        seen["allow_provision"] = allow_provision

    monkeypatch.setattr(sync, "_sync_auto_update_with_plan", _fake)
    # Keep the write side inert — this test is about the flag, not the cache.
    monkeypatch.setattr(sync, "_CLOUD_PLAN_CACHE_PATH", "/nonexistent/cloud_plan.json")

    try:
        sync._persist_cloud_plan_to_disk("cloud_pro", allow_provision=False)
    except Exception:
        # The cache write may fail on the bogus path; the forwarding already
        # happened and is what we assert on.
        pass

    assert seen["allow_provision"] is False


def test_cli_status_passes_allow_provision_false():
    """The status handler must call the mirror with allow_provision=False.

    Asserted on the source because the surrounding handler prints a full
    status report and reaches the network for the account lookup; the
    regression we are guarding is exactly this one keyword going missing.
    """
    import inspect
    import clawmetry.cli as cli

    src = inspect.getsource(cli._cmd_status)
    assert "_pcp(_acct_plan, allow_provision=False)" in src, (
        "clawmetry status must mirror the cloud plan without provisioning; "
        "dropping allow_provision=False reintroduces the 85s status hang"
    )


def test_provision_still_runs_by_default(monkeypatch):
    """The daemon path is unchanged: provisioning is opt-out, not removed."""
    ran = []

    monkeypatch.setattr("clawmetry.license.ensure_pro_on_path", lambda: None)
    monkeypatch.setattr("clawmetry.license._pro_installed_version", lambda: None)
    monkeypatch.setattr(
        "clawmetry.license.auto_provision_pro",
        lambda key, node=None: (ran.append(key), (False, ""))[1],
    )
    monkeypatch.setattr(sync, "load_config", lambda: {"api_key": "cm_test", "node_id": "n1"})

    sync._sync_auto_update_with_plan("cloud_pro")

    assert ran == ["cm_test"]
