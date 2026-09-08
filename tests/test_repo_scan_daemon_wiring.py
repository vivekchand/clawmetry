"""The workspace scan runs in the daemon, once per (directory, file stamp).

``clawmetry/repo_scan.py`` shipped with a CLI and nothing in the product called
it. A detector nobody runs protects nobody, so ``sync._emit_detector_incidents``
now scans each session's workspace and emits findings on the existing Guard
path. This file pins the four properties that wiring has to keep:

* a poisoned repo produces a ``repo_config_exec`` loop_signals row,
* the scan is cached on the mtime of exactly the files it reads (a 50-repo
  fleet must not re-read them every tick) and re-runs the moment one changes,
* workspace findings reach the policy pass, so a policy that names the kind
  can act on them (the catch-all exclusion is pinned in
  ``tests/test_guard_workspace_kinds.py``),
* the cwd comes from the ``sessions.cwd`` COLUMN, which is where every
  cwd-aware consumer already keys.
"""
from __future__ import annotations

import os
import sys
import time

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import detectors as _det  # noqa: E402
from clawmetry import repo_scan as _rs  # noqa: E402
from clawmetry import sync as _sync  # noqa: E402

_POISON = "[core]\n\tfsmonitor = /tmp/payload.sh\n"


def _poisoned_repo(tmp_path, name="repo"):
    ws = tmp_path / name
    (ws / ".git").mkdir(parents=True)
    (ws / ".git" / "config").write_text(_POISON, encoding="utf-8")
    return str(ws)


# ── the cwd the scan keys on ────────────────────────────────────────────────
def test_session_row_cwd_prefers_the_column_over_metadata():
    """Regression: reading only ``metadata`` hid the column every cwd-aware
    consumer already uses, so cursor/goose/opencode/pi/qwen_code sessions all
    looked like they had no workspace.

    Named ``_session_row_cwd`` because ``_session_cwd`` was already taken by
    the alias-based reader for raw adapter dicts; sharing the name silently
    replaced that one for all three of its callers.
    """
    assert _sync._session_row_cwd({"cwd": "/tmp/a", "metadata": {"cwd": "/tmp/b"}}) == "/tmp/a"
    assert _sync._session_row_cwd({"cwd": None, "metadata": {"cwd": "/tmp/b"}}) == "/tmp/b"
    assert _sync._session_row_cwd({"cwd": "  ", "metadata": {"project_dir": "/tmp/c"}}) == "/tmp/c"
    assert _sync._session_row_cwd({"metadata": {}}) == ""
    assert _sync._session_row_cwd(None) == ""
    # The metadata fallback goes through the SAME twelve-alias set the raw
    # reader uses, so a runtime that spells it `workingDir` or `directory` is
    # found. Reading two keys is what the shadowing accident reduced it to.
    assert _sync._session_row_cwd({"metadata": {"workingDir": "/tmp/d"}}) == "/tmp/d"
    assert _sync._session_row_cwd({"metadata": {"directory": "/tmp/e"}}) == "/tmp/e"


def test_the_alias_reader_still_answers_for_raw_dicts():
    """``_session_cwd`` is the OTHER helper: a raw adapter/gateway dict read by
    alias. Its three callers are why the shadowing mattered."""
    assert _sync._session_cwd({"workingDir": "/tmp/w"}) == "/tmp/w"
    assert _sync._session_cwd({"directory": "/tmp/d"}) == "/tmp/d"
    assert _sync._session_cwd({"folder": "/tmp/f"}) == "/tmp/f"


def test_detector_facts_carry_the_column_cwd():
    facts = _sync._detector_session_facts(
        [{"session_id": "goose:1", "cwd": "/tmp/ws", "metadata": {}}], {}, time.time())
    assert facts["goose:1"]["cwd"] == "/tmp/ws"


# ── the scan itself ────────────────────────────────────────────────────────
def test_poisoned_workspace_yields_an_incident(tmp_path):
    inc = _sync._workspace_incidents({}, _poisoned_repo(tmp_path), "cursor:1",
                                     "cursor", time.time())
    assert [i["kind"] for i in inc] == ["repo_config_exec"]
    assert inc[0]["session_id"] == "cursor:1" and inc[0]["runtime"] == "cursor"
    # No cost is knowable for a property of a folder; it must not be invented.
    assert inc[0]["spend_at_risk_usd"] == 0.0
    assert inc[0]["spend_basis"] == "unknown"


def test_clean_workspace_is_quiet(tmp_path):
    ws = tmp_path / "clean"
    (ws / ".git").mkdir(parents=True)
    (ws / ".git" / "config").write_text("[core]\n\tbare = false\n", encoding="utf-8")
    assert _sync._workspace_incidents({}, str(ws), "s", "openclaw", time.time()) == []


def test_missing_or_empty_cwd_is_quiet(tmp_path):
    state = {}
    assert _sync._workspace_incidents(state, "", "s", "openclaw", time.time()) == []
    assert _sync._workspace_incidents(
        state, str(tmp_path / "gone"), "s", "openclaw", time.time()) == []
    assert state.get("repo_scan_memo") in (None, {})


def test_kill_switch_disables_the_scan(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_REPO_SCAN", "0")
    assert _sync._workspace_incidents({}, _poisoned_repo(tmp_path), "s",
                                      "cursor", time.time()) == []


# ── the cache: this is what makes it affordable on a fleet ─────────────────
def test_scan_runs_once_per_directory_then_reuses_the_cache(tmp_path, monkeypatch):
    ws = _poisoned_repo(tmp_path)
    calls = []
    real = _rs.scan_workspace
    monkeypatch.setattr(_rs, "scan_workspace",
                        lambda *a, **k: (calls.append(a[0]), real(*a, **k))[1])
    state = {}
    for sid in ("a", "b", "c", "d"):          # four sessions, one repo
        assert _sync._workspace_incidents(state, ws, sid, "cursor", time.time())
    assert len(calls) == 1, f"re-scanned {len(calls)}x for one unchanged repo"


def test_a_changed_config_is_rescanned(tmp_path, monkeypatch):
    ws = _poisoned_repo(tmp_path)
    calls = []
    real = _rs.scan_workspace
    monkeypatch.setattr(_rs, "scan_workspace",
                        lambda *a, **k: (calls.append(a[0]), real(*a, **k))[1])
    state = {}
    assert _sync._workspace_incidents(state, ws, "a", "cursor", time.time())
    cfg = os.path.join(ws, ".git", "config")
    os.utime(cfg, (time.time() + 5, time.time() + 5))
    _sync._workspace_incidents(state, ws, "a", "cursor", time.time())
    assert len(calls) == 2, "a repo poisoned after first sight must be re-scanned"


def test_a_repo_poisoned_later_is_caught(tmp_path, monkeypatch):
    """The case that matters: clean at first sight, poisoned five minutes on."""
    ws = tmp_path / "later"
    (ws / ".git").mkdir(parents=True)
    cfg = ws / ".git" / "config"
    cfg.write_text("[core]\n\tbare = false\n", encoding="utf-8")
    state = {}
    assert _sync._workspace_incidents(state, str(ws), "a", "cursor", time.time()) == []
    cfg.write_text(_POISON, encoding="utf-8")
    os.utime(cfg, (time.time() + 5, time.time() + 5))
    found = _sync._workspace_incidents(state, str(ws), "a", "cursor", time.time())
    assert [i["kind"] for i in found] == ["repo_config_exec"]


def test_cache_is_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(_sync, "_REPO_SCAN_CACHE_MAX", 5)
    state = {}
    for i in range(12):
        ws = tmp_path / f"r{i}"
        ws.mkdir()
        _sync._workspace_incidents(state, str(ws), "s", "openclaw", time.time() + i)
    assert len(state["repo_scan_memo"]) <= 5


def test_stamp_covers_every_file_the_scanner_declares(tmp_path):
    """The stamp must include every file a scan reads, or a checkout poisoned
    AFTER first sight sits behind a cache that never expires.

    Derived from ``repo_scan.SCANNED_FILES`` rather than listed here, because a
    hand-kept copy is exactly how package.json ended up scanned-but-not-stamped:
    the scanner learned a new file and the cache did not.
    """
    from clawmetry import repo_scan as _rs
    ws = tmp_path / "hooks"
    (ws / ".claude").mkdir(parents=True)
    names = {rel for rel, _m, _s in _sync._repo_scan_stamp(str(ws))}
    for rel in _rs.SCANNED_FILES:
        assert rel in names, f"{rel} is scanned but not stamped"
    for entry in _rs._AGENT_HOOK_FILES:
        rel = entry[0] if isinstance(entry, (tuple, list)) else entry
        assert rel in names, f"{rel} is scanned but not stamped"


def test_a_manifest_poisoned_after_first_sight_is_caught(tmp_path):
    """The bug this pins: package.json was read by the scanner and ignored by
    the cache stamp, so a repo that was clean when first seen stayed clean
    forever, whatever anyone added to it afterwards."""
    import json as _json
    ws = tmp_path / "later"
    (ws / ".git").mkdir(parents=True)
    (ws / ".git" / "config").write_text("[core]\n\tbare = false\n", encoding="utf-8")
    (ws / "package.json").write_text(
        _json.dumps({"name": "x", "scripts": {"build": "tsc"}}), encoding="utf-8")
    state = {}
    assert _sync._workspace_incidents(state, str(ws), "s", "cursor", time.time()) == []
    (ws / "package.json").write_text(
        _json.dumps({"name": "x", "scripts": {"postinstall": "cat ~/.npmrc"}}),
        encoding="utf-8")
    os.utime(ws / "package.json", (time.time() + 5, time.time() + 5))
    found = _sync._workspace_incidents(state, str(ws), "s", "cursor", time.time())
    assert [f["kind"] for f in found] == ["package_manifest_exec"]
    assert found[0]["severity"] == "critical"


# ── the emit path ──────────────────────────────────────────────────────────
class _EmitStore:
    def __init__(self, cwd):
        self.cwd = cwd
        self.signals = []
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
        self.row = {"session_id": "cursor:abc", "agent_type": "cursor",
                    "started_at": now_iso, "last_active_at": now_iso,
                    "status": "active", "cost_usd": 1.0, "cwd": cwd,
                    "metadata": {}}

    def query_sessions_table(self, limit=300):
        return [self.row]

    def query_events(self, **kw):
        return [{"event_type": "tool_call", "ts": self.row["started_at"],
                 "data": {"tool": "x"}}]

    def query_approvals(self, **kw):
        return []

    def ingest_loop_signal(self, **kw):
        self.signals.append(kw)

    def __getattr__(self, name):
        return lambda *a, **k: None


@pytest.fixture()
def _quiet(monkeypatch):
    monkeypatch.setattr(_det, "run_all", lambda *a, **k: [])
    monkeypatch.setattr(_sync, "_record_guard_observation", lambda *a, **k: None)


def test_emit_writes_a_loop_signal_for_a_poisoned_workspace(tmp_path, _quiet,
                                                            monkeypatch):
    """End of the wire: a session in a poisoned repo, no behavioural incident
    at all, still produces a Guard row within one tick."""
    monkeypatch.setattr(_sync, "_apply_guard_policies", lambda *a, **k: 0)
    store = _EmitStore(_poisoned_repo(tmp_path))
    assert _sync._emit_detector_incidents(store, {}) == 1
    sig = store.signals[0]
    assert sig["signature"] == "daemon_detect_repo_config_exec"
    assert sig["details"]["kind"] == "repo_config_exec"
    assert sig["details"]["spend_at_risk_usd"] == 0.0
    assert sig["details"]["spend_basis"] == "unknown"


def test_workspace_findings_reach_the_policy_pass(tmp_path, _quiet,
                                                 monkeypatch):
    """They are handed to the pass so a policy that NAMES the kind can act.
    The safety property lives in ``policy_engine`` instead, where an empty
    ``trigger_kind`` excludes them: see
    ``tests/test_guard_workspace_kinds.py``, which pins that a catch-all rule
    cannot fire on a poisoned checkout."""
    seen = []
    monkeypatch.setattr(_sync, "_apply_guard_policies",
                        lambda store, state, incs, facts: seen.append(
                            [i["kind"] for i in incs]))
    store = _EmitStore(_poisoned_repo(tmp_path))
    _sync._emit_detector_incidents(store, {})
    assert seen == [["repo_config_exec"]]


def test_a_clean_workspace_emits_nothing(tmp_path, _quiet, monkeypatch):
    monkeypatch.setattr(_sync, "_apply_guard_policies", lambda *a, **k: 0)
    ws = tmp_path / "clean"
    (ws / ".git").mkdir(parents=True)
    (ws / ".git" / "config").write_text("[core]\n\tbare = false\n", encoding="utf-8")
    store = _EmitStore(str(ws))
    assert _sync._emit_detector_incidents(store, {}) == 0
    assert store.signals == []
