"""Post-trial, the clawmetry-pro package is REMOVED, not merely gated.

Gating stops ClawMetry from using the paid adapters, but the closed-source
wheel sitting in site-packages is still importable by hand -- a user can
`import clawmetry_pro` and keep the paid capability without paying. Removing
the code is the only version of that boundary that actually holds.

The dangerous direction here is the opposite of the request gate's. A wrongly
blocked request self-heals on the next heartbeat; a wrongly REMOVED package
needs a re-download the machine may not be able to make. So
should_deprovision_pro fails OPEN on every uncertainty and only removes on a
positive, provable lapse.
"""

import json
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

DAY = 86400.0


def _ent(monkeypatch, tmp_path, **fields):
    from clawmetry import entitlements as ent
    cache = str(tmp_path / ".clawmetry" / "cloud_plan.json")
    monkeypatch.setattr(ent, "_CLOUD_PLAN_CACHE", cache)
    monkeypatch.setattr(ent, "_LICENSE_PATH", str(tmp_path / "nope.key"))
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    with open(cache, "w") as fh:
        json.dump(fields, fh)
    ent.invalidate()
    return ent.get_entitlement(force=True)


# ── the decision ────────────────────────────────────────────────────────────

def test_lapsed_trial_is_removed(monkeypatch, tmp_path):
    import time
    from clawmetry.license import should_deprovision_pro
    e = _ent(monkeypatch, tmp_path, plan="cloud_free", node_limit=1,
             expiry=time.time() - 2 * DAY, trial_used=True)
    assert should_deprovision_pro(e) is True


def test_paying_customer_is_never_removed(monkeypatch, tmp_path):
    """Signup is trial-by-default, so a paying customer also has
    trial_used=True. Removing their adapters would be a self-inflicted outage
    on a live subscriber."""
    from clawmetry.license import should_deprovision_pro
    e = _ent(monkeypatch, tmp_path, plan="cloud_pro", node_limit=5,
             expiry=None, trial_used=True)
    assert should_deprovision_pro(e) is False


def test_live_trial_is_never_removed(monkeypatch, tmp_path):
    import time
    from clawmetry.license import should_deprovision_pro
    e = _ent(monkeypatch, tmp_path, plan="cloud_free", node_limit=1,
             expiry=time.time() + 3 * DAY, trial_used=True)
    assert should_deprovision_pro(e) is False


def test_never_trialed_is_never_removed(monkeypatch, tmp_path):
    from clawmetry.license import should_deprovision_pro
    e = _ent(monkeypatch, tmp_path, plan="cloud_free", node_limit=1, expiry=None)
    assert should_deprovision_pro(e) is False


def test_unresolvable_entitlement_fails_open():
    """Offline / cloud outage / corrupt cache. Never remove on uncertainty."""
    from clawmetry.license import should_deprovision_pro
    assert should_deprovision_pro(None) is False


def test_trial_used_without_expiry_fails_open(monkeypatch, tmp_path):
    """We know a trial happened but not when it ended -- cannot prove a lapse."""
    from clawmetry.license import should_deprovision_pro
    e = _ent(monkeypatch, tmp_path, plan="cloud_free", node_limit=1,
             expiry=None, trial_used=True)
    assert should_deprovision_pro(e) is False


def test_signed_local_license_is_never_removed(monkeypatch, tmp_path):
    """A self-hosted key governs locally; the cloud plan does not get to
    revoke it."""
    import time
    from clawmetry import entitlements as ent
    from clawmetry.license import should_deprovision_pro
    lic = ent._build(ent.TIER_CLOUD_STARTER, "license", node_limit=1,
                     expiry=time.time() + 30 * DAY, trial_used=True)
    assert should_deprovision_pro(lic) is False


# ── the removal ─────────────────────────────────────────────────────────────

def _fake_install(root):
    """Lay down a clawmetry_pro package + dist-info the way the unzip
    installer does."""
    pkg = os.path.join(root, "clawmetry_pro")
    os.makedirs(os.path.join(pkg, "adapters"), exist_ok=True)
    with open(os.path.join(pkg, "__init__.py"), "w") as fh:
        fh.write("VALUE = 'paid-adapters'\n")
    with open(os.path.join(pkg, "adapters", "__init__.py"), "w") as fh:
        fh.write("\n")
    di = os.path.join(root, "clawmetry_pro-0.7.6.dist-info")
    os.makedirs(di, exist_ok=True)
    with open(os.path.join(di, "METADATA"), "w") as fh:
        fh.write("Name: clawmetry-pro\nVersion: 0.7.6\n")
    return pkg, di


def test_removal_sweeps_both_install_locations(monkeypatch, tmp_path):
    """The provisioner writes to site-packages OR the HOME fallback depending
    on writability. Removing only one leaves the package importable."""
    from clawmetry import license as lic
    site = tmp_path / "site-packages"
    fallback = tmp_path / "pro-packages"
    site.mkdir()
    fallback.mkdir()
    pkg_a, di_a = _fake_install(str(site))
    pkg_b, di_b = _fake_install(str(fallback))

    monkeypatch.setattr(lic, "_site_packages_target", lambda: (str(site), True))
    monkeypatch.setattr(lic, "_PRO_FALLBACK_DIR", str(fallback))
    monkeypatch.setattr(lic, "_PRO_MARKER_PATH", str(tmp_path / "pro_installed.json"))
    monkeypatch.setattr(lic, "_pip_run", lambda args: (False, "no pip"))
    monkeypatch.setattr(lic, "_pro_installed_version", lambda: None)

    removed, msg = lic.deprovision_pro("test")
    assert removed is True, msg
    for p in (pkg_a, di_a, pkg_b, di_b):
        assert not os.path.isdir(p), f"{p} survived removal"


def test_removal_clears_the_marker(monkeypatch, tmp_path):
    from clawmetry import license as lic
    site = tmp_path / "site-packages"
    site.mkdir()
    _fake_install(str(site))
    marker = tmp_path / "pro_installed.json"
    marker.write_text('{"version": "0.7.6"}')

    monkeypatch.setattr(lic, "_site_packages_target", lambda: (str(site), True))
    monkeypatch.setattr(lic, "_PRO_FALLBACK_DIR", str(tmp_path / "absent"))
    monkeypatch.setattr(lic, "_PRO_MARKER_PATH", str(marker))
    monkeypatch.setattr(lic, "_pip_run", lambda args: (False, "no pip"))
    monkeypatch.setattr(lic, "_pro_installed_version", lambda: None)

    lic.deprovision_pro("test")
    assert not marker.exists(), "stale marker would make re-provision skip the download"


def test_removal_purges_imported_modules(monkeypatch, tmp_path):
    """Deleting files is not enough: the daemon already has the adapter classes
    imported and Python keeps using a module whose file is gone. Without the
    purge the paid runtimes keep ingesting until the next restart -- exactly
    the window removal exists to close."""
    from clawmetry import license as lic
    import types
    monkeypatch.setitem(sys.modules, "clawmetry_pro", types.ModuleType("clawmetry_pro"))
    monkeypatch.setitem(sys.modules, "clawmetry_pro.adapters",
                        types.ModuleType("clawmetry_pro.adapters"))
    lic._purge_pro_from_memory()
    assert "clawmetry_pro" not in sys.modules
    assert "clawmetry_pro.adapters" not in sys.modules


def test_removal_reports_failure_when_still_importable(monkeypatch, tmp_path):
    """Honest status: if the package survives, say so rather than claim a
    removal that did not happen."""
    from clawmetry import license as lic
    monkeypatch.setattr(lic, "_site_packages_target", lambda: (str(tmp_path), True))
    monkeypatch.setattr(lic, "_PRO_FALLBACK_DIR", str(tmp_path / "absent"))
    monkeypatch.setattr(lic, "_PRO_MARKER_PATH", str(tmp_path / "m.json"))
    monkeypatch.setattr(lic, "_pip_run", lambda args: (False, "no pip"))
    monkeypatch.setattr(lic, "_pro_installed_version", lambda: "0.7.6")
    removed, msg = lic.deprovision_pro("test")
    assert removed is False
    assert "still importable" in msg


def test_removal_is_idempotent_when_absent(monkeypatch, tmp_path):
    from clawmetry import license as lic
    monkeypatch.setattr(lic, "_site_packages_target", lambda: (str(tmp_path), True))
    monkeypatch.setattr(lic, "_PRO_FALLBACK_DIR", str(tmp_path / "absent"))
    monkeypatch.setattr(lic, "_PRO_MARKER_PATH", str(tmp_path / "m.json"))
    monkeypatch.setattr(lic, "_pip_run", lambda args: (False, "no pip"))
    monkeypatch.setattr(lic, "_pro_installed_version", lambda: None)
    removed, msg = lic.deprovision_pro("test")
    assert removed is False
    assert "not installed" in msg
