"""Daemon-side Guard enforcement: the three safety locks and the latch.

These tests drive ``sync._apply_guard_policies`` with a fake store and a
stubbed actuator, so nothing is ever signalled for real. What they assert is
the thing that matters: a policy must NOT reach a live process unless every
lock is open, and must never fire twice for the same session.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from clawmetry import sync as _sync  # noqa: E402


class FakeStore:
    """Minimal stand-in for LocalStore's Guard surface."""

    def __init__(self, policies):
        self._policies = policies
        self.recorded = []
        self.fired = set()

    def query_session_policies(self, enabled_only=False):
        return [p for p in self._policies
                if p.get("enabled", True) or not enabled_only]

    def policy_already_fired(self, session_id, policy_id):
        return (session_id, policy_id) in self.fired

    def record_policy_action(self, session_id, policy_id, **kw):
        self.fired.add((session_id, policy_id))
        self.recorded.append({"session_id": session_id,
                              "policy_id": policy_id, **kw})


def _incident(session_id="s1", kind="no_progress", runtime="claude_code"):
    return {"kind": kind, "session_id": session_id, "runtime": runtime,
            "severity": "warning", "title": "agent not advancing",
            "evidence": {"total_tool_calls": 40}}


def _policy(action="kill", policy_id="p1"):
    return {"policy_id": policy_id, "enabled": True, "scope_runtime": "",
            "scope_agent_id": "", "trigger_kind": "", "min_severity": "info",
            "min_repeat": 0, "min_duration_s": 0, "min_spend_usd": 0,
            "action": action}


_FACTS = {"s1": {"cost_usd": 9.0, "bad_for_seconds": 600,
                 "runtime": "claude_code", "cwd": "/tmp/x", "agent_id": "main"}}


@pytest.fixture(autouse=True)
def _stub_actuator(monkeypatch):
    """Record actuator calls instead of signalling anything."""
    calls = []

    def fake_actuate(runtime, session_id, cwd, action):
        calls.append((runtime, session_id, cwd, action))
        return {"ok": True, "detail": "stub"}

    monkeypatch.setattr(_sync, "_guard_actuate", fake_actuate)
    monkeypatch.delenv("CLAWMETRY_POLICY_ENFORCE", raising=False)
    monkeypatch.delenv("CLAWMETRY_GUARD_POLICIES", raising=False)
    return calls


def _entitled(monkeypatch, value=True):
    monkeypatch.setattr(_sync, "_guard_enforcement_allowed", lambda: value)


# ── lock 1: the action itself ──────────────────────────────────────────────

def test_monitor_never_actuates_even_fully_enabled(monkeypatch, _stub_actuator):
    monkeypatch.setenv("CLAWMETRY_POLICY_ENFORCE", "1")
    _entitled(monkeypatch)
    store = FakeStore([_policy(action="monitor")])
    n = _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    assert n == 1, "the decision is still recorded"
    assert _stub_actuator == [], "monitor must never signal a process"
    assert store.recorded[0]["enforced"] is False


# ── lock 2: the enforce env flag ───────────────────────────────────────────

def test_dry_run_by_default_records_but_does_not_act(monkeypatch, _stub_actuator):
    _entitled(monkeypatch)
    store = FakeStore([_policy(action="kill")])
    n = _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    assert n == 1
    assert _stub_actuator == [], "no enforce flag: must not kill"
    rec = store.recorded[0]
    assert rec["enforced"] is False
    assert "DRY RUN" in rec["result_detail"]
    assert "CLAWMETRY_POLICY_ENFORCE" in rec["result_detail"]


def test_guard_can_be_disabled_entirely(monkeypatch, _stub_actuator):
    monkeypatch.setenv("CLAWMETRY_GUARD_POLICIES", "0")
    monkeypatch.setenv("CLAWMETRY_POLICY_ENFORCE", "1")
    _entitled(monkeypatch)
    store = FakeStore([_policy(action="kill")])
    assert _sync._apply_guard_policies(store, {}, [_incident()], _FACTS) == 0
    assert _stub_actuator == []
    assert store.recorded == []


# ── lock 3: entitlement ────────────────────────────────────────────────────

def test_unentitled_node_records_but_does_not_act(monkeypatch, _stub_actuator):
    monkeypatch.setenv("CLAWMETRY_POLICY_ENFORCE", "1")
    _entitled(monkeypatch, False)
    store = FakeStore([_policy(action="kill")])
    _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    assert _stub_actuator == []
    assert "not enabled on this plan" in store.recorded[0]["result_detail"]


def test_entitlement_check_fails_closed(monkeypatch):
    """A resolver explosion must read as 'not allowed', never 'allowed'."""
    import clawmetry.entitlements as _ent

    def boom():
        raise RuntimeError("resolver down")

    monkeypatch.setattr(_ent, "get_entitlement", boom)
    assert _sync._guard_enforcement_allowed() is False


# ── all locks open: it actually acts ───────────────────────────────────────

def test_all_locks_open_actuates(monkeypatch, _stub_actuator):
    monkeypatch.setenv("CLAWMETRY_POLICY_ENFORCE", "1")
    _entitled(monkeypatch)
    store = FakeStore([_policy(action="kill")])
    _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    assert _stub_actuator == [("claude_code", "s1", "/tmp/x", "kill")]
    final = store.recorded[-1]
    assert final["enforced"] is True and final["result_ok"] is True


# ── the latch ──────────────────────────────────────────────────────────────

def test_latch_prevents_double_fire(monkeypatch, _stub_actuator):
    monkeypatch.setenv("CLAWMETRY_POLICY_ENFORCE", "1")
    _entitled(monkeypatch)
    store = FakeStore([_policy(action="kill")])
    _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    assert len(_stub_actuator) == 1, "a policy must fire at most once per session"


def test_latch_read_failure_declines_to_act(monkeypatch, _stub_actuator):
    monkeypatch.setenv("CLAWMETRY_POLICY_ENFORCE", "1")
    _entitled(monkeypatch)
    store = FakeStore([_policy(action="kill")])

    def boom(*a, **k):
        raise RuntimeError("duckdb gone")

    store.policy_already_fired = boom
    assert _sync._apply_guard_policies(store, {}, [_incident()], _FACTS) == 0
    assert _stub_actuator == []


# ── never break ingest ─────────────────────────────────────────────────────

def test_store_failure_never_raises(monkeypatch, _stub_actuator):
    class Broken:
        def query_session_policies(self, enabled_only=False):
            raise RuntimeError("boom")

    assert _sync._apply_guard_policies(Broken(), {}, [_incident()], _FACTS) == 0


def test_no_incidents_is_a_noop(_stub_actuator):
    store = FakeStore([_policy(action="kill")])
    assert _sync._apply_guard_policies(store, {}, [], _FACTS) == 0
    assert store.recorded == []


def test_one_session_one_signal_even_with_many_policies(monkeypatch, _stub_actuator):
    monkeypatch.setenv("CLAWMETRY_POLICY_ENFORCE", "1")
    _entitled(monkeypatch)
    store = FakeStore([_policy(action="pause", policy_id="a"),
                       _policy(action="kill", policy_id="b"),
                       _policy(action="stop", policy_id="c")])
    _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    assert len(_stub_actuator) == 1
    assert _stub_actuator[0][3] == "kill", "strongest action wins"


# ── escalation ladders must not weaken any lock ──────────────────────────
_LADDER = [{"action": "pause", "after_secs": 0},
           {"action": "kill", "after_secs": 300}]


def _ladder_policy(policy_id="p1"):
    p = _policy(action="pause", policy_id=policy_id)
    p["steps"] = _LADDER
    return p


class LadderStore(FakeStore):
    """FakeStore that tracks rungs, like the real per-step latch."""

    def __init__(self, policies):
        super().__init__(policies)
        self.rungs = {}
        self.now = 1000.0

    def query_policy_ladder_state(self, limit=2000):
        out = {}
        for (sid, pid, step), ts in self.rungs.items():
            cur = out.setdefault(sid, {}).get(pid)
            if cur is None or step > cur["last_step"]:
                out.setdefault(sid, {})[pid] = {"last_step": step,
                                                "last_fired_at": ts}
        return out

    def policy_already_fired(self, session_id, policy_id, step_index=0):
        return (session_id, policy_id, step_index) in self.rungs

    def record_policy_action(self, session_id, policy_id, step_index=0, **kw):
        self.rungs.setdefault((session_id, policy_id, step_index), self.now)
        self.recorded.append({"session_id": session_id,
                              "policy_id": policy_id,
                              "step_index": step_index, **kw})


def _tick(store, monkeypatch, at):
    """Run one daemon tick with the engine's clock pinned to ``at``."""
    from clawmetry import policy_engine as pe
    store.now = at
    real = pe.evaluate
    monkeypatch.setattr(
        pe, "evaluate",
        lambda i, p, f, ladder_state=None, now=None:
            real(i, p, f, ladder_state=ladder_state, now=at))
    _sync._apply_guard_policies(store, {}, [_incident()], _FACTS)
    monkeypatch.setattr(pe, "evaluate", real)


def test_ladder_kill_rung_is_a_dry_run_without_the_enforce_flag(
        monkeypatch, _stub_actuator):
    """A ladder must not become a way to skip CLAWMETRY_POLICY_ENFORCE."""
    monkeypatch.delenv("CLAWMETRY_POLICY_ENFORCE", raising=False)
    monkeypatch.setattr(_sync, "_guard_enforcement_allowed", lambda: True)
    store = LadderStore([_ladder_policy()])
    _tick(store, monkeypatch, 1000)
    _tick(store, monkeypatch, 1400)
    assert _stub_actuator == [], "no rung may signal with enforcement off"
    # Both rungs are still RECORDED, which is what makes dry run honest.
    assert sorted(r["step_index"] for r in store.recorded) == [0, 1]
    assert all("DRY RUN" in r["result_detail"] for r in store.recorded)


def test_ladder_kill_rung_respects_the_entitlement_lock(
        monkeypatch, _stub_actuator):
    monkeypatch.setenv("CLAWMETRY_POLICY_ENFORCE", "1")
    monkeypatch.setattr(_sync, "_guard_enforcement_allowed", lambda: False)
    store = LadderStore([_ladder_policy()])
    _tick(store, monkeypatch, 1000)
    _tick(store, monkeypatch, 1400)
    assert _stub_actuator == []


def test_ladder_climbs_when_every_lock_is_open(monkeypatch, _stub_actuator):
    monkeypatch.setenv("CLAWMETRY_POLICY_ENFORCE", "1")
    monkeypatch.setattr(_sync, "_guard_enforcement_allowed", lambda: True)
    store = LadderStore([_ladder_policy()])
    _tick(store, monkeypatch, 1000)
    assert [c[3] for c in _stub_actuator] == ["pause"]
    _tick(store, monkeypatch, 1100)          # too early for the kill rung
    assert [c[3] for c in _stub_actuator] == ["pause"]
    _tick(store, monkeypatch, 1400)
    assert [c[3] for c in _stub_actuator] == ["pause", "kill"]
    _tick(store, monkeypatch, 9999)          # exhausted: never again
    assert [c[3] for c in _stub_actuator] == ["pause", "kill"]


def test_a_prelader_store_refuses_to_climb_rather_than_replaying(
        monkeypatch, _stub_actuator):
    """Version skew: a daemon whose store predates ladders can only latch per
    (session, policy). It must stop at rung 0, not re-fire it forever."""
    monkeypatch.setenv("CLAWMETRY_POLICY_ENFORCE", "1")
    monkeypatch.setattr(_sync, "_guard_enforcement_allowed", lambda: True)

    class OldStore(LadderStore):
        def policy_already_fired(self, session_id, policy_id):  # 2-arg only
            return any(k[0] == session_id and k[1] == policy_id
                       for k in self.rungs)

        def record_policy_action(self, session_id, policy_id, **kw):
            kw.pop("step_index", None)
            self.rungs.setdefault((session_id, policy_id, 0), self.now)
            self.recorded.append({"session_id": session_id,
                                  "policy_id": policy_id, **kw})

    store = OldStore([_ladder_policy()])
    _tick(store, monkeypatch, 1000)
    _tick(store, monkeypatch, 1400)
    _tick(store, monkeypatch, 5000)
    assert [c[3] for c in _stub_actuator] == ["pause"], \
        "an old store must not re-fire rung 0 nor climb"
