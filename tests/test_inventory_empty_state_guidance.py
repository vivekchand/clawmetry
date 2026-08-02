"""Guards for the Agents-tab empty state (live-hit 2026-08-02).

A fresh self-host install showed "No agents yet, and that is fine.
Nothing to configure." on a machine with 523 Claude Code sessions:

  1. ``/api/inventory``'s empty branch detected runtimes via the ADAPTER
     registry, which only knows loaded adapters. Paid-runtime adapters
     (Claude Code, Cursor, ...) live in clawmetry-pro, which is not
     importable until the wheel lands post-activation — so detection
     returned [] exactly when the guidance mattered most. The fix falls
     back to the filesystem-based lite detector.
  2. The client rendered the empty state once per tab visit and never
     re-polled, so a transient empty (daemon warming up, one failed
     fetch) stuck until the user re-clicked the tab.
  3. The copy hardcoded "and 10 more runtimes" (16 at the time of the
     fix); counts in copy always go stale.
"""

from __future__ import annotations

import json
import os


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(relpath):
    with open(os.path.join(_repo_root(), relpath), "r", encoding="utf-8") as fh:
        return fh.read()


# ── 1) Server: lite-detector fallback ───────────────────────────────────
def test_empty_roster_falls_back_to_lite_detection(monkeypatch):
    """Registry-blind machine (no pro plugin) with Claude Code on disk:
    the payload must still carry detectedRuntimes so the UI can render
    guidance instead of the generic empty state."""
    import dashboard as _d
    from routes import inventory as inv

    monkeypatch.setattr(inv, "_detected_runtimes", lambda: [])
    monkeypatch.setattr(inv, "_daemon_running", lambda: True)
    monkeypatch.setattr(inv, "_build_local_inventory", lambda: None)
    monkeypatch.setattr(inv, "is_local_store_read_enabled", lambda: True)
    monkeypatch.setattr(
        _d, "_detect_other_runtimes_lite",
        lambda: [{"id": "claude_code", "label": "Claude Code", "sessions": 523}],
    )

    with _d.app.test_request_context("/api/inventory"):
        payload = json.loads(inv.api_inventory().get_data(as_text=True))

    assert payload["agents"] == []
    detected = payload.get("detectedRuntimes")
    assert detected, (
        "empty roster + registry-blind detection MUST fall back to the "
        "lite detector — otherwise a fresh self-host install shows the "
        "generic 'No agents yet' copy on a machine full of Claude Code "
        "sessions (live-hit 2026-08-02)"
    )
    assert detected[0]["displayName"] == "Claude Code"
    assert payload["daemonRunning"] is True


def test_empty_roster_with_nothing_anywhere_stays_zero(monkeypatch):
    """Truly empty machine: both detectors empty → plain zero payload."""
    import dashboard as _d
    from routes import inventory as inv

    monkeypatch.setattr(inv, "_detected_runtimes", lambda: [])
    monkeypatch.setattr(inv, "_build_local_inventory", lambda: None)
    monkeypatch.setattr(inv, "is_local_store_read_enabled", lambda: True)
    monkeypatch.setattr(_d, "_detect_other_runtimes_lite", lambda: [])

    with _d.app.test_request_context("/api/inventory"):
        payload = json.loads(inv.api_inventory().get_data(as_text=True))

    assert payload["agents"] == []
    assert "detectedRuntimes" not in payload


# ── 2) Client: transient-empty heal ─────────────────────────────────────
def test_render_inventory_repolls_while_empty():
    js = _read("clawmetry/static/js/app.js")
    anchor = js.find("async function renderInventory")
    assert anchor != -1
    block = js[anchor:anchor + 6000]
    assert "_invEmptyRetryTimer" in block, (
        "the empty state must schedule a retry — a transient empty "
        "roster (daemon warming up, one dropped fetch) used to stick "
        "until the user re-clicked the tab"
    )
    assert "_cmCurrentTab === 'inventory'" in block, (
        "the retry must be gated to the active inventory tab (perf "
        "budget: no off-screen pollers)"
    )
    assert "document.hidden" in block, (
        "the retry must pause when the browser tab is hidden"
    )


# ── 3) Copy: no hardcoded runtime counts, no double dash ────────────────
def test_empty_state_copy_carries_no_runtime_count():
    html = _read("clawmetry/templates/tabs/inventory.html")
    assert "10 more runtimes" not in html and "12 more runtimes" not in html, (
        "hardcoded runtime counts in copy always go stale (the '10 "
        "more' era ended at 12; we are at 16 as of 2026-08)"
    )
    en = json.loads(_read("clawmetry/static/locales/en.json"))
    assert "inventory.empty_body" not in en, (
        "the stale-count key must be gone (renamed to _v2 so all "
        "locales fall back to correct English instead of a stale "
        "translated count)"
    )
    body = en.get("inventory.empty_body_v2", "")
    assert body and "more runtimes" not in body
    assert "every other supported runtime" in body


def test_empty_state_guidance_avoids_double_dash():
    js = _read("clawmetry/static/js/app.js")
    anchor = js.find("async function renderInventory")
    block = js[anchor:anchor + 6000]
    assert " -- " not in block.split("bodyEl.innerHTML")[0].split("var msg")[-1], (
        "user-facing guidance copy must not use double dashes "
        "(feedback_no_em_dashes_in_user_facing_copy)"
    )
