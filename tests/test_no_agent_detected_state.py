"""Tests for agent-presence detection + the no-agent banner REMOVAL.

History: the dashboard used to show a persistent "No OpenClaw or NVIDIA
NemoClaw detected. Install one to start seeing data." banner whenever
neither of those two runtimes was installed. That copy dates from when
ClawMetry supported exactly two runtimes; with 12+ observed runtimes it
was flat wrong (a machine with hundreds of Claude Code sessions still
got told to install OpenClaw) and it rendered on cloud node pages where
the pod can never filesystem-detect anything. The banner, its JS poller
(``checkAgentPresence``), and its locale keys are REMOVED.

What stays: ``detect_agent_install()`` and ``GET /api/agent-presence``.
The cloud still consumes the payload (heartbeat ``agent_install`` mirror
in sync.py + the cloud route-policy entry), so the backend detection
contract keeps its tests here.

This suite now pins:
  1. The backend payload contract (5 detection scenarios + cache TTL +
     runtime-aware detected_runtimes fields) for cloud consumers.
  2. The REMOVAL guard: no banner markup in banners.html, no poller in
     app.js, no orphaned locale keys — so the two-runtime framing can't
     quietly come back.
"""

from __future__ import annotations

import glob
import json
import os


# ── Shared monkeypatch helpers ───────────────────────────────────────────
def _reset_cache(monkeypatch):
    """Force a fresh detect_agent_install() call by clearing the 60s
    cache. Every scenario test depends on a fresh evaluation, otherwise
    test order would leak state across cases."""
    import dashboard as _d
    monkeypatch.setattr(
        _d, "_agent_presence_cache", {"ts": 0.0, "value": None}, raising=False
    )


def _force(monkeypatch, openclaw, nemoclaw, any_data,
           other_runtimes=(), entitled_ids=()):
    """Stub all detectors so a test can drive the exact combo it wants
    without touching the real filesystem, DuckDB, or the entitlement
    resolver."""
    import dashboard as _d
    _reset_cache(monkeypatch)
    monkeypatch.setattr(_d, "_detect_openclaw_install", lambda: openclaw)
    monkeypatch.setattr(_d, "_detect_nemoclaw_install", lambda: nemoclaw)
    monkeypatch.setattr(_d, "_detect_any_local_data", lambda: any_data)
    monkeypatch.setattr(_d, "_detect_other_runtimes_lite",
                        lambda: list(other_runtimes))
    monkeypatch.setattr(_d, "_entitled_runtime_ids",
                        lambda ids: [r for r in ids if r in set(entitled_ids)])


# ── Backend payload contract (cloud consumers still read this) ──────────
def test_no_agent_at_all_reports_no_agent_true(monkeypatch):
    import dashboard as _d
    _force(monkeypatch, openclaw=False, nemoclaw=False, any_data=False)
    payload = _d.detect_agent_install()
    assert payload["no_agent"] is True
    assert payload["openclaw_detected"] is False
    assert payload["nemoclaw_detected"] is False
    assert payload["any_data"] is False
    assert payload["signals"] == [], (
        "signals list MUST be empty when nothing is detected so consumers "
        "do not display a misleading 'detected via X' tag"
    )


def test_openclaw_installed_but_no_heartbeat_is_NOT_no_agent_state(monkeypatch):
    import dashboard as _d
    _force(monkeypatch, openclaw=True, nemoclaw=False, any_data=False)
    payload = _d.detect_agent_install()
    assert payload["no_agent"] is False
    assert payload["openclaw_detected"] is True
    assert "openclaw" in payload["signals"]


def test_openclaw_installed_and_data_present_is_normal_state(monkeypatch):
    import dashboard as _d
    _force(monkeypatch, openclaw=True, nemoclaw=False, any_data=True)
    payload = _d.detect_agent_install()
    assert payload["no_agent"] is False
    assert payload["openclaw_detected"] is True
    assert payload["any_data"] is True
    assert "openclaw" in payload["signals"]
    assert "local_data" in payload["signals"]


def test_nemoclaw_only_install_is_normal_state(monkeypatch):
    import dashboard as _d
    _force(monkeypatch, openclaw=False, nemoclaw=True, any_data=False)
    payload = _d.detect_agent_install()
    assert payload["no_agent"] is False
    assert payload["nemoclaw_detected"] is True
    assert "nemoclaw" in payload["signals"]


def test_both_agents_installed_is_normal_state(monkeypatch):
    import dashboard as _d
    _force(monkeypatch, openclaw=True, nemoclaw=True, any_data=True)
    payload = _d.detect_agent_install()
    assert payload["no_agent"] is False
    assert payload["openclaw_detected"] is True
    assert payload["nemoclaw_detected"] is True
    assert set(payload["signals"]) == {"openclaw", "nemoclaw", "local_data"}


def test_detection_result_is_cached_for_60s(monkeypatch):
    """Consumers poll /api/agent-presence — without a cache that would
    re-stat the workspace + shell out to ``shutil.which`` on every call.
    The 60s TTL is the contract."""
    import dashboard as _d
    _reset_cache(monkeypatch)
    calls = {"openclaw": 0, "nemoclaw": 0, "data": 0}

    def _oc():
        calls["openclaw"] += 1
        return False

    def _nc():
        calls["nemoclaw"] += 1
        return False

    def _da():
        calls["data"] += 1
        return False

    monkeypatch.setattr(_d, "_detect_openclaw_install", _oc)
    monkeypatch.setattr(_d, "_detect_nemoclaw_install", _nc)
    monkeypatch.setattr(_d, "_detect_any_local_data", _da)

    _d.detect_agent_install()
    assert calls == {"openclaw": 1, "nemoclaw": 1, "data": 1}
    _d.detect_agent_install()
    _d.detect_agent_install()
    assert calls == {"openclaw": 1, "nemoclaw": 1, "data": 1}, (
        "cache MUST suppress re-running the detectors within the 60s TTL"
    )


# ── Runtime-aware payload fields (cloud install-state aggregation) ──────
_CLAUDE_CODE = {"id": "claude_code", "label": "Claude Code", "sessions": 12}
_CURSOR = {"id": "cursor", "label": "Cursor", "sessions": 0}


def test_detected_paid_runtime_keeps_no_agent_but_flags_upgrade(monkeypatch):
    import dashboard as _d
    _force(monkeypatch, openclaw=False, nemoclaw=False, any_data=False,
           other_runtimes=[_CLAUDE_CODE, _CURSOR], entitled_ids=[])
    payload = _d.detect_agent_install()
    assert payload["no_agent"] is True
    assert [r["id"] for r in payload["detected_runtimes"]] == ["claude_code", "cursor"]
    assert all(r["entitled"] is False for r in payload["detected_runtimes"])
    assert payload["detected_runtimes"][0]["label"] == "Claude Code"
    assert payload["upgrade_candidate"] is True
    assert payload["signals"] == []


def test_entitled_runtime_is_not_an_upgrade_candidate(monkeypatch):
    import dashboard as _d
    _force(monkeypatch, openclaw=False, nemoclaw=False, any_data=False,
           other_runtimes=[_CLAUDE_CODE], entitled_ids=["claude_code"])
    payload = _d.detect_agent_install()
    assert payload["detected_runtimes"][0]["entitled"] is True
    assert payload["upgrade_candidate"] is False


def test_truly_empty_machine_has_no_detected_runtimes(monkeypatch):
    import dashboard as _d
    _force(monkeypatch, openclaw=False, nemoclaw=False, any_data=False)
    payload = _d.detect_agent_install()
    assert payload["detected_runtimes"] == []
    assert payload["upgrade_candidate"] is False


# ── Removal guard: the two-runtime banner must NOT come back ────────────
def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(_repo_root(), relpath), "r", encoding="utf-8") as fh:
        return fh.read()


def test_no_agent_banner_markup_is_gone():
    """The banner claimed 'No OpenClaw or NVIDIA NemoClaw detected' on
    machines running any of the 10+ other observed runtimes. Removed;
    must not resurface in the partial."""
    html = _read("clawmetry/templates/partials/banners.html")
    assert 'id="no-agent-banner"' not in html
    assert "No OpenClaw or NVIDIA NemoClaw detected" not in html
    assert "Install one to start seeing data" not in html


def test_no_agent_banner_js_poller_is_gone():
    """checkAgentPresence polled /api/agent-presence every 60s purely to
    drive the removed banner. The dashboard must not fetch that endpoint
    anymore (the endpoint itself stays for cloud consumers)."""
    js = _read("clawmetry/static/js/app.js")
    assert "checkAgentPresence" not in js
    assert "_cmApplyNoAgentVariant" not in js
    assert "/api/agent-presence" not in js
    assert "no-agent-banner" not in js


def test_no_agent_banner_locale_keys_are_gone_in_every_locale():
    """Orphaned i18n keys linger for years; sweep all locales."""
    removed = {
        "banners.no_agent_msg",
        "banners.install_openclaw",
        "banners.install_nemoclaw",
        "banners.detected_runtimes_msg",
        "banners.start_pro_trial",
    }
    locale_files = glob.glob(
        os.path.join(_repo_root(), "clawmetry", "static", "locales", "*.json")
    )
    assert locale_files, "locale dir must exist"
    for path in locale_files:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            continue  # _meta.json / _glossary.json are list-shaped
        leftovers = removed & set(data.keys())
        assert not leftovers, (
            os.path.basename(path) + " still carries removed banner keys: "
            + ", ".join(sorted(leftovers))
        )


def test_agent_presence_endpoint_still_exists():
    """The /api/agent-presence route must survive the banner removal —
    the cloud route policy classifies it and the heartbeat mirror in
    sync.py shares its shape. Removing it is a separate, coordinated
    cross-repo change."""
    src = _read("routes/health.py")
    assert "/api/agent-presence" in src


# ── Announcement pill: Agent Builder cross-sell (unrelated, kept) ───────
def test_announcement_pill_cross_sells_agent_builder():
    """ONE announcement pill, and it points at Agent Builder now — the
    desk-device launch pill was retired in its favor."""
    html = _read("clawmetry/templates/partials/banners.html")
    assert "build.clawmetry.com" in html
    assert "Agent Builder" in html
    assert "desk device, $49" not in html
