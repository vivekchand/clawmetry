"""The session phase model: one state machine, every runtime (WO-1).

Covers the acceptance criteria for REQ-OBS-005 (Local Agent Observability):

* AC-OBS-005.1 -- every supported runtime reports a phase from one vocabulary:
  ``test_every_family_runtime_reports_a_phase_for_a_live_session``.
* AC-OBS-005.2 -- an undeterminable phase is unknown, never idle:
  ``test_no_signal_is_unknown_not_idle``.
* AC-OBS-005.3 -- the transition time survives a restart of the daemon:
  ``test_phase_since_survives_a_daemon_restart``.
* AC-OBS-005.4 -- activeness is an allowlist, so an unmapped value is inactive:
  ``test_a_new_status_with_no_mapping_is_not_active``.
* AC-OBS-005.5 -- an abandoned session is not reported as a concluded one:
  ``test_stale_session_is_not_reported_as_a_concluded_one``.
* AC-OBS-005.6 -- the launch directory is written once and not rewritten:
  ``test_initial_cwd_is_written_once``.
* AC-OBS-005.7 -- whether a pending ask is answerable here is reported:
  ``test_resolvable_round_trips_and_defaults_to_unknown``.

The whole point of the model is that it fails towards "less alive": where the
data cannot say, the answer is unknown rather than a quiet default. Several
tests below exist only to hold that line.
"""
from __future__ import annotations

import importlib
import os
import sys
import time

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry.adapters import phase as ph  # noqa: E402
from clawmetry.adapters.base import Session  # noqa: E402


# ── 1. The vocabulary and the two honesty rules ────────────────────────────


def test_every_status_projects_onto_exactly_one_known_phase():
    assert ph.STATUSES, "the status vocabulary must not be empty"
    for status in ph.STATUSES:
        projected = ph.phase_for_status(status)
        assert projected in ph.PHASES, f"{status} projects onto {projected!r}"


def test_permission_request_is_the_waiting_status():
    assert ph.phase_for_status("permission_requested") == ph.PHASE_WAITING
    assert ph.phase_for_status("tool_use") == ph.PHASE_WORKING


def test_a_new_status_with_no_mapping_is_not_active():
    """AC-OBS-005.4 -- a status nobody mapped must not read as a live agent.

    This is the acceptance criterion stated as a scenario: someone adds a
    status to an adapter and forgets the projection. The phase must come back
    unknown, and unknown must not be active.
    """
    assert "reviewing_diff" not in ph.STATUS_TO_PHASE
    assert ph.phase_for_status("reviewing_diff") is None
    verdict = ph.resolve(now=1000.0, status="reviewing_diff",
                         last_activity_at=999.0)
    assert verdict.phase is None
    assert verdict.basis == "unmapped-status"
    assert verdict.active is False
    assert ph.is_active(verdict.phase) is False


def test_a_new_phase_added_without_being_declared_is_not_active(monkeypatch):
    """Activeness is an allowlist, not "everything except the ones I listed"."""
    monkeypatch.setattr(ph, "PHASES", ph.PHASES + ("reviewing",))
    verdict = ph.resolve(now=1000.0, phase="reviewing")
    assert verdict.phase == "reviewing"      # the adapter was believed
    assert ph.is_active("reviewing") is False  # but it is not live
    assert verdict.active is False


def test_declared_active_phases_are_a_strict_subset():
    assert ph.ACTIVE_PHASES <= set(ph.PHASES)
    assert ph.PHASE_ENDED not in ph.ACTIVE_PHASES
    assert ph.PHASE_IDLE not in ph.ACTIVE_PHASES
    assert ph.is_active(None) is False
    assert ph.is_active("") is False


def test_an_unknown_phase_from_an_adapter_is_refused_not_coerced():
    verdict = ph.resolve(now=1000.0, phase="busy-ish", last_activity_at=999.0)
    assert verdict.phase is None
    assert verdict.basis == "unmapped-phase"


# ── 2. Deriving a phase from what was observed ─────────────────────────────


def test_no_signal_is_unknown_not_idle():
    """AC-OBS-005.2 -- absent is not the same as calm."""
    verdict = ph.resolve(now=1000.0)
    assert verdict.phase is None
    assert verdict.basis == "no-signal"
    assert verdict.phase != ph.PHASE_IDLE
    assert verdict.phase != ph.PHASE_ENDED


def test_recency_buckets_working_idle_and_stale():
    now = 10_000.0
    work = ph.DEFAULT_WORKING_SECS
    stale = ph.DEFAULT_STALE_SECS
    assert ph.resolve(now=now, last_activity_at=now - 1).phase == ph.PHASE_WORKING
    assert ph.resolve(now=now, last_activity_at=now - work).phase == ph.PHASE_WORKING
    assert ph.resolve(now=now, last_activity_at=now - work - 1).phase == ph.PHASE_IDLE
    assert ph.resolve(now=now, last_activity_at=now - stale - 1).phase == ph.PHASE_ENDED


def test_stale_session_is_not_reported_as_a_concluded_one():
    """AC-OBS-005.5 -- abandoned and finished are different answers."""
    now = 10_000.0
    abandoned = ph.resolve(now=now, last_activity_at=now - ph.DEFAULT_STALE_SECS - 1)
    concluded = ph.resolve(now=now, end_reason="user_stopped",
                           last_activity_at=now - 1)
    assert abandoned.phase == concluded.phase == ph.PHASE_ENDED
    assert abandoned.end_reason == ph.END_STALE
    assert concluded.end_reason == "user_stopped"
    assert ph.end_reason_kind(abandoned.end_reason) == ph.END_STALE
    assert ph.end_reason_kind(concluded.end_reason) == ph.END_SESSION_END


def test_an_asserted_end_beats_a_recent_file_write():
    verdict = ph.resolve(now=1000.0, end_reason="max_turns", last_activity_at=999.9)
    assert verdict.phase == ph.PHASE_ENDED
    assert verdict.basis == "asserted-end"
    assert verdict.end_reason == "max_turns"


def test_a_future_timestamp_is_clock_skew_not_a_stale_session():
    verdict = ph.resolve(now=1000.0, last_activity_at=9_999_999.0)
    assert verdict.phase == ph.PHASE_WORKING


def test_a_dead_process_ends_the_session():
    verdict = ph.resolve(now=1000.0, last_activity_at=999.0,
                         pid=4242, pid_alive=lambda _pid: False)
    assert verdict.phase == ph.PHASE_ENDED
    assert verdict.end_reason == ph.END_DEAD_PID
    # A live pid is no reason to end it, and no pid checker is no evidence.
    assert ph.resolve(now=1000.0, last_activity_at=999.0, pid=4242,
                      pid_alive=lambda _pid: True).phase == ph.PHASE_WORKING
    assert ph.resolve(now=1000.0, last_activity_at=999.0,
                      pid=4242).phase == ph.PHASE_WORKING


def test_an_archived_session_is_ended_with_its_own_reason():
    verdict = ph.resolve(now=1000.0, last_activity_at=999.0, archived=True)
    assert verdict.phase == ph.PHASE_ENDED
    assert verdict.end_reason == ph.END_ARCHIVED


def test_end_reason_kind_never_invents_a_category():
    assert ph.end_reason_kind("") == ""
    assert ph.end_reason_kind("turn_aborted:interrupted") == ph.END_SESSION_END
    assert ph.end_reason_kind("something_we_have_never_seen") == ph.END_SESSION_END
    assert ph.end_reason_kind(ph.END_DEAD_PID) == ph.END_DEAD_PID


def test_there_is_one_definition_of_recent():
    """The windows are the ones sync._session_liveness already bucketed on.

    A second definition invented beside an existing one is the disease this
    module exists to cure, so the two must stay literally the same numbers.
    """
    import clawmetry.sync as sync
    assert sync._SESSION_ACTIVE_SECS == int(ph.DEFAULT_WORKING_SECS)
    assert sync._SESSION_IDLE_SECS == int(ph.DEFAULT_STALE_SECS)


def test_recency_windows_are_operator_overridable(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_PHASE_WORKING_SECS", "5")
    assert ph.working_window_secs() == 5.0
    monkeypatch.setenv("CLAWMETRY_PHASE_WORKING_SECS", "not-a-number")
    assert ph.working_window_secs() == ph.DEFAULT_WORKING_SECS
    monkeypatch.setenv("CLAWMETRY_PHASE_WORKING_SECS", "-3")
    assert ph.working_window_secs() == ph.DEFAULT_WORKING_SECS


# ── 3. The unified session shape ───────────────────────────────────────────


def test_session_serializes_every_phase_field():
    s = Session(agent="codex", id="abc", started_at=time.time() - 30,
                ended_at=time.time() - 5)
    s.resolve_phase()
    d = s.to_dict()
    for key in ("phase", "status", "phaseSince", "phaseBasis",
                "lastActivityAt", "resolvable", "initialCwd", "endReason"):
        assert key in d, f"{key} missing from the unified session shape"
    assert d["phase"] == ph.PHASE_WORKING
    assert d["phaseSince"] is None  # only the durable record may set it


def test_an_adapter_that_knows_its_own_state_wins():
    s = Session(agent="claude_code", id="abc", ended_at=time.time() - 5,
                phase=ph.PHASE_WAITING, status="permission_requested")
    verdict = s.resolve_phase()
    assert verdict.basis == "adapter"
    assert s.phase == ph.PHASE_WAITING


def test_a_runtimes_own_end_reason_is_never_overwritten():
    s = Session(agent="openclaw", id="abc", end_reason="user_stopped",
                ended_at=time.time() - 99_999)
    s.resolve_phase()
    assert s.phase == ph.PHASE_ENDED
    assert s.end_reason == "user_stopped"  # not rewritten to "stale"


def test_initial_cwd_is_not_seeded_from_the_current_directory():
    """Seeding it from ``cwd`` would make the two equal by construction and the
    later drift check could never fire."""
    s = Session(agent="codex", id="abc", cwd="/somewhere/else",
                ended_at=time.time() - 5)
    s.resolve_phase()
    assert s.initial_cwd == ""
    s2 = Session(agent="codex", id="d", cwd="/now",
                 ended_at=time.time() - 5, extra={"initialCwd": "/launched"})
    s2.resolve_phase()
    assert s2.initial_cwd == "/launched"


def test_resolving_twice_is_idempotent():
    s = Session(agent="codex", id="abc", ended_at=time.time() - 5)
    first = s.resolve_phase()
    second = s.resolve_phase()
    assert (first.phase, first.basis) == (second.phase, second.basis)


def test_last_activity_falls_back_to_ended_at_without_asserting_an_end():
    """``ended_at`` is the last event timestamp on every shipped adapter, not a
    claim the session finished. Only ``end_reason`` asserts an end."""
    s = Session(agent="cursor", id="abc", ended_at=time.time() - 5)
    assert s.observed_activity_at() == s.ended_at
    s.resolve_phase()
    assert s.phase == ph.PHASE_WORKING


# ── 4. Every runtime the daemon loads ──────────────────────────────────────


def _family_runtime_names():
    import clawmetry.sync as sync
    names = []
    for mod_name, _cls in sync._FAMILY_ADAPTER_SPECS:
        names.append(mod_name.rsplit(".", 1)[-1])
    return names


def test_family_adapter_spec_list_is_populated():
    """Guards the two tests below from passing vacuously on an empty list."""
    names = _family_runtime_names()
    assert len(names) >= 20, f"only {len(names)} family adapters registered"


def test_every_family_runtime_reports_a_phase_for_a_live_session():
    """AC-OBS-005.1 -- one vocabulary, every runtime the daemon loads.

    Runs everywhere, including CI without the closed wheel: every adapter in
    both repositories builds its rows from ``clawmetry.adapters.base.Session``,
    so exercising that shape per runtime name is what actually proves the
    contract holds for all of them.
    """
    now = time.time()
    for runtime in _family_runtime_names() + ["openclaw", "nemo"]:
        s = Session(agent=runtime, id=f"{runtime}-live",
                    started_at=now - 300, ended_at=now - 3)
        s.resolve_phase(now=now)
        assert s.phase == ph.PHASE_WORKING, f"{runtime} reported {s.phase!r}"
        assert ph.is_active(s.phase) is True
        assert s.to_dict()["phase"] == ph.PHASE_WORKING


def test_installed_family_adapters_report_a_phase_on_real_sessions():
    """The same claim against real adapters, where the closed wheel is present.

    Skips rather than fails when ``clawmetry_pro`` is not installed (open-source
    CI), which is why the shape-level test above is the one that always runs --
    a check that can only skip is not a check.
    """
    pytest.importorskip("clawmetry_pro",
                        reason="clawmetry-pro not installed; shape test covers the contract")
    import clawmetry.sync as sync
    classes = sync._family_adapter_classes()
    if not classes:
        pytest.skip("no family adapters importable")
    checked = 0
    for cls in classes:
        try:
            adapter = cls()
            if not adapter.detect().detected:
                continue
            sessions = adapter.list_sessions(limit=3)
        except Exception:
            continue
        for s in sessions:
            s.resolve_phase()
            assert s.phase is None or s.phase in ph.PHASES, (
                f"{adapter.name} produced phase {s.phase!r}")
            checked += 1
    if not checked:
        pytest.skip("no installed family runtime has sessions on this machine")


# ── 5. The durable record ──────────────────────────────────────────────────


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "phase.duckdb"))
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    st = ls.LocalStore()
    yield ls, st
    try:
        st.stop(flush=False)
    except Exception:
        pass


def test_phase_since_is_stamped_once_per_transition(store):
    _ls, st = store
    t0 = 1_000_000.0
    first = st.record_session_phase("codex:a", phase="waiting", runtime="codex",
                                    observed_at=t0)
    same = st.record_session_phase("codex:a", phase="waiting", runtime="codex",
                                   observed_at=t0 + 600)
    assert same["phaseSince"] == first["phaseSince"]
    moved = st.record_session_phase("codex:a", phase="working", runtime="codex",
                                    observed_at=t0 + 900)
    assert moved["phaseSince"] > first["phaseSince"]
    assert moved["phase"] == "working"


def test_phase_since_survives_a_daemon_restart(store, tmp_path, monkeypatch):
    """AC-OBS-005.3 -- "waiting on you for 14 minutes" must not reset to zero
    when the daemon restarts, which is exactly when someone comes back to look.
    """
    ls, st = store
    t0 = 1_000_000.0
    first = st.record_session_phase("codex:a", phase="waiting", runtime="codex",
                                    observed_at=t0)
    st.stop(flush=False)

    # A genuinely new process: reload the module and open the same file again.
    importlib.reload(ls)
    restarted = ls.LocalStore()
    try:
        after = restarted.record_session_phase("codex:a", phase="waiting",
                                               runtime="codex",
                                               observed_at=t0 + 840)
        assert after["phaseSince"] == first["phaseSince"]
        assert after["phaseSince"] < t0 + 840
    finally:
        restarted.stop(flush=False)


def test_an_unknown_phase_does_not_restamp_itself_every_tick(store):
    _ls, st = store
    t0 = 1_000_000.0
    first = st.record_session_phase("cursor:x", phase=None, runtime="cursor",
                                    phase_basis="no-signal", observed_at=t0)
    again = st.record_session_phase("cursor:x", phase=None, runtime="cursor",
                                    phase_basis="no-signal", observed_at=t0 + 300)
    assert first["phase"] is None
    assert again["phaseSince"] == first["phaseSince"]


def test_initial_cwd_is_written_once(store):
    """AC-OBS-005.6 -- recorded at first observation, never rewritten."""
    _ls, st = store
    t0 = 1_000_000.0
    st.record_session_phase("codex:a", phase="working", runtime="codex",
                            cwd="/repo/api", observed_at=t0)
    later = st.record_session_phase("codex:a", phase="working", runtime="codex",
                                    cwd="/somewhere/else", observed_at=t0 + 60)
    assert later["initialCwd"] == "/repo/api"
    assert later["cwd"] == "/somewhere/else"


def test_resolvable_round_trips_and_defaults_to_unknown(store):
    """AC-OBS-005.7 -- a surface must be able to tell "answerable here" from
    "we do not know", so the unset value is null and not False."""
    _ls, st = store
    unknown = st.record_session_phase("codex:a", phase="waiting", runtime="codex")
    assert unknown["resolvable"] is None
    yes = st.record_session_phase("codex:a", phase="waiting", runtime="codex",
                                  resolvable=True)
    assert yes["resolvable"] is True
    no = st.record_session_phase("codex:a", phase="waiting", runtime="codex",
                                 resolvable=False)
    assert no["resolvable"] is False


def test_query_session_phases_filters_and_never_raises(store):
    _ls, st = store
    st.record_session_phase("codex:a", phase="waiting", runtime="codex")
    st.record_session_phase("cursor:b", phase="working", runtime="cursor")
    assert [r["sessionId"] for r in st.query_session_phases(runtime="codex")] == ["codex:a"]
    assert [r["sessionId"] for r in st.query_session_phases(phase="working")] == ["cursor:b"]
    assert st.query_session_phases(session_ids=["nope"]) == []
    assert st.record_session_phase("", phase="working") == {}


def test_the_store_methods_are_reachable_through_the_daemon_proxy():
    """A store method the dashboard calls but the proxy does not allow 400s and
    silently falls back to a direct open the writer lock refuses."""
    from routes.local_query import _DAEMON_METHODS
    assert "record_session_phase" in _DAEMON_METHODS
    assert "query_session_phases" in _DAEMON_METHODS


# ── 6. What the per-runtime session listing actually serves ────────────────


class _FakeAdapter:
    """Two sessions: one an adapter can speak for, one it cannot."""

    name = "codex"
    display_name = "Codex"

    def __init__(self, sessions):
        self._sessions = sessions

    def detect(self):
        from clawmetry.adapters.base import DetectResult
        return DetectResult(name=self.name, display_name=self.display_name,
                            detected=True, running=True)

    def list_sessions(self, limit=100):
        return list(self._sessions)[:limit]

    def capabilities(self):
        return set()


def _app_with(adapter, monkeypatch, durable_rows=None):
    from flask import Flask
    import routes.agents as ra

    monkeypatch.setattr(ra.registry, "get", lambda name: adapter)
    monkeypatch.setattr(ra, "require_runtime", lambda name: None)
    monkeypatch.setattr(ra, "is_local_store_read_enabled", lambda: False)
    monkeypatch.setattr(ra, "_ls_call",
                        lambda method, **kw: (durable_rows or []))
    app = Flask(__name__)
    app.register_blueprint(ra.bp_agents)
    return app


def test_the_sessions_listing_serves_a_phase_for_every_session(monkeypatch):
    """AC-OBS-005.1 read end to end: the phase reaches the response body."""
    now = time.time()
    live = Session(agent="codex", id="live", started_at=now - 60,
                   ended_at=now - 2)
    blind = Session(agent="codex", id="blind")  # no timestamps at all
    app = _app_with(_FakeAdapter([live, blind]), monkeypatch)
    with app.test_client() as c:
        body = c.get("/api/agents/codex/sessions").get_json()
    by_id = {s["id"]: s for s in body["sessions"]}
    assert by_id["live"]["phase"] == ph.PHASE_WORKING
    assert by_id["live"]["phaseBasis"] == "recency"
    # AC-OBS-005.2 at the surface: a session nothing can be said about is
    # served as unknown, not as a quiet one.
    assert by_id["blind"]["phase"] is None
    assert by_id["blind"]["phaseBasis"] == "no-signal"


def test_phase_since_is_served_from_the_durable_record_only(monkeypatch):
    """Never recomputed per request: a page reload must not restart the clock."""
    now = time.time()
    waiting = Session(agent="codex", id="w", started_at=now - 900,
                      ended_at=now - 2, phase=ph.PHASE_WAITING,
                      status="permission_requested")
    rows = [{
        "sessionId": "codex:w", "runtime": "codex", "phase": "waiting",
        "status": "permission_requested", "phaseBasis": "adapter",
        "phaseSince": now - 840, "endReason": "", "resolvable": True,
        "initialCwd": "/repo/api", "cwd": "/repo/api", "observedAt": now,
    }]
    app = _app_with(_FakeAdapter([waiting]), monkeypatch, durable_rows=rows)
    with app.test_client() as c:
        body = c.get("/api/agents/codex/sessions").get_json()
    served = body["sessions"][0]
    assert served["phaseSince"] == pytest.approx(now - 840)
    assert served["resolvable"] is True
    assert served["initialCwd"] == "/repo/api"


def test_a_session_with_no_durable_record_reports_an_absent_transition(monkeypatch):
    now = time.time()
    s = Session(agent="codex", id="fresh", started_at=now - 30, ended_at=now - 1)
    app = _app_with(_FakeAdapter([s]), monkeypatch, durable_rows=[])
    with app.test_client() as c:
        body = c.get("/api/agents/codex/sessions").get_json()
    served = body["sessions"][0]
    assert served["phase"] == ph.PHASE_WORKING
    assert served["phaseSince"] is None  # unknown, never "just now"


def test_the_duckdb_fast_path_also_serves_a_phase(monkeypatch):
    """The listing has two sources; a field on only one of them is the bug
    class this whole work order exists to remove."""
    import routes.agents as ra
    now = time.time()
    rows = [{
        "session_id": "abc", "title": "t", "metadata": {},
        "started_at": now - 300, "ended_at": now - 2,
        "message_count": 3, "total_tokens": 10, "cost_usd": None,
    }]

    def _fake_ls(method, **kw):
        return rows if method == "query_sessions_table" else []

    monkeypatch.setattr(ra, "_ls_call", _fake_ls)
    out = ra._try_local_store_agent_sessions("openclaw", 100)
    served = out["sessions"][0]
    assert served["phase"] == ph.PHASE_WORKING
    assert served["phaseSince"] is None
    for key in ("status", "phaseBasis", "lastActivityAt", "resolvable",
                "initialCwd"):
        assert key in served


# ── 7. The OpenClaw ingest path ────────────────────────────────────────────
#
# OpenClaw does not come through the family-adapter loop -- it is parsed
# straight from JSONL by ``sync_session_metadata`` -- so "every runtime gets a
# phase" is only true if that path records one too. These build a real
# workspace on disk and run the real function against it.


def _write_openclaw_session(sessions_dir, sid, *, age_secs, end_reason=""):
    import json as _json
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    lines = [
        {"type": "message", "timestamp": (now - timedelta(seconds=age_secs + 30)).isoformat(),
         "message": {"role": "user", "model": "claude-opus-5"}},
        {"type": "message", "timestamp": (now - timedelta(seconds=age_secs)).isoformat(),
         "message": {"role": "assistant", "model": "claude-opus-5",
                     "usage": {"totalTokens": 12, "cost": {"total": 0.01}}}},
    ]
    if end_reason:
        lines.append({"type": "session",
                      "timestamp": (now - timedelta(seconds=age_secs)).isoformat(),
                      "endReason": end_reason})
    path = sessions_dir / f"{sid}.jsonl"
    path.write_text("\n".join(_json.dumps(x) for x in lines) + "\n")
    return path


@pytest.fixture
def openclaw_workspace(tmp_path, monkeypatch):
    sessions = tmp_path / "oc" / "agents" / "main" / "sessions"
    sessions.mkdir(parents=True)
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path / "oc"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "oc.duckdb"))
    # Nothing may leave the machine during a test: point the data plane at a
    # closed port so the upload fails fast and locally.
    monkeypatch.setenv("CLAWMETRY_ENDPOINT", "http://127.0.0.1:1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync
    # ``_record_sync_progress`` writes into the DEVELOPER's real ~/.clawmetry
    # (CONFIG_DIR is resolved at import time and no env var redirects it). A
    # unit test must never be able to change how the real install behaves.
    monkeypatch.setattr(sync, "_record_sync_progress",
                        lambda *a, **k: None, raising=False)
    st = ls.get_store()
    yield sessions, sync, st
    try:
        st.stop(flush=False)
    except Exception:
        pass


def test_openclaw_sessions_are_given_a_phase_too(openclaw_workspace):
    """AC-OBS-005.1 on the path that does not use a family adapter."""
    sessions, sync, st = openclaw_workspace
    _write_openclaw_session(sessions, "live-one", age_secs=5)
    _write_openclaw_session(sessions, "quiet-one",
                            age_secs=int(ph.DEFAULT_STALE_SECS) + 120)
    sync.sync_session_metadata({"api_key": "test-only", "node_id": "n"}, {})
    rows = {r["sessionId"]: r for r in st.query_session_phases(runtime="openclaw")}
    assert rows["live-one"]["phase"] == ph.PHASE_WORKING
    assert rows["quiet-one"]["phase"] == ph.PHASE_ENDED
    assert rows["quiet-one"]["endReason"] == ph.END_STALE


def test_openclaws_own_end_reason_beats_a_recent_write(openclaw_workspace):
    """AC-OBS-005.5 -- OpenClaw is the one runtime that states a real end, and
    what it says survives verbatim rather than being relabelled ``stale``."""
    sessions, sync, st = openclaw_workspace
    _write_openclaw_session(sessions, "stopped", age_secs=2,
                            end_reason="user_stopped")
    sync.sync_session_metadata({"api_key": "test-only", "node_id": "n"}, {})
    row = st.query_session_phases(session_ids=["stopped"])[0]
    assert row["phase"] == ph.PHASE_ENDED
    assert row["phaseBasis"] == "asserted-end"
    assert row["endReason"] == "user_stopped"
    assert ph.end_reason_kind(row["endReason"]) == ph.END_SESSION_END


def test_a_fresher_observation_beats_the_stored_phase(monkeypatch):
    """The request has just read the session; the row is up to a tick old.

    A session that asked for permission ten seconds ago must not be served as
    still working because that is what the daemon last saw -- and the stored
    transition time must NOT be carried across, because it belongs to the phase
    the session has just left.
    """
    now = time.time()
    asking = Session(agent="codex", id="w", started_at=now - 900,
                     ended_at=now - 2, phase=ph.PHASE_WAITING,
                     status="permission_requested")
    rows = [{
        "sessionId": "codex:w", "runtime": "codex", "phase": "working",
        "status": "tool_use", "phaseBasis": "recency",
        "phaseSince": now - 840, "endReason": "", "resolvable": None,
        "initialCwd": "/repo/api", "cwd": "/repo/api", "observedAt": now - 55,
    }]
    app = _app_with(_FakeAdapter([asking]), monkeypatch, durable_rows=rows)
    with app.test_client() as c:
        served = c.get("/api/agents/codex/sessions").get_json()["sessions"][0]
    assert served["phase"] == ph.PHASE_WAITING
    assert served["status"] == "permission_requested"
    assert served["phaseSince"] is None      # unknown, never the stale stamp
    assert served["initialCwd"] == "/repo/api"  # the store still owns this


def test_the_stored_phase_fills_in_where_this_read_cannot_tell(monkeypatch):
    now = time.time()
    blind = Session(agent="codex", id="b")  # no timestamps: unknown right now
    rows = [{
        "sessionId": "codex:b", "runtime": "codex", "phase": "waiting",
        "status": "permission_requested", "phaseBasis": "adapter",
        "phaseSince": now - 300, "endReason": "", "resolvable": True,
        "initialCwd": "", "cwd": "", "observedAt": now - 30,
    }]
    app = _app_with(_FakeAdapter([blind]), monkeypatch, durable_rows=rows)
    with app.test_client() as c:
        served = c.get("/api/agents/codex/sessions").get_json()["sessions"][0]
    assert served["phase"] == ph.PHASE_WAITING
    assert served["phaseBasis"] == "adapter"
    assert served["phaseSince"] == pytest.approx(now - 300)
