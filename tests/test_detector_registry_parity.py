"""Every detector is registered, exported, invoked, and honours the contract.

The failure this guards is silence, which is the expensive kind: a detector
function that exists, has passing unit tests of its own, and is never called by
``run_all`` looks exactly like a working feature. Nothing goes red. The daemon
simply never runs it. (The repo has burned on this shape before: a helper with
seven green tests that was never wired in.)

So rather than trusting a reader to notice, these assertions re-derive the
facts from the module itself:

* ``DETECTOR_KINDS`` and ``_ALL_DETECTORS`` describe the same set;
* every name in ``DETECTOR_KINDS`` resolves to a real callable;
* ``run_all`` actually invokes each one, proven by substitution, not by
  reading the source;
* every detector accepts the shared keyword contract
  (``thresholds`` / ``steps`` / ``facts``), so adding one that quietly ignores
  the resolved thresholds is a test failure rather than a silent regression to
  module constants.
"""
from __future__ import annotations

import inspect
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import detectors  # noqa: E402

# The eleven the product promises. Written out rather than derived, because a
# guard that derives BOTH sides of its own comparison cannot catch a deletion.
EXPECTED_KINDS = {
    "stuck_loop",
    "no_progress",
    "repeated_tool_failure",
    "action_discrepancy",
    "file_blast_radius",
    "credential_access",
    "network_egress",
    "privilege_change",
    # Silent failure: it stopped, and nobody was told.
    "rate_limited",
    "blocked_on_user",
    "crashed",
}


def test_expected_detectors_are_all_registered():
    assert set(detectors.DETECTOR_KINDS) == EXPECTED_KINDS


def test_registry_and_exported_kinds_agree():
    # Two independently maintained facts: the literal at the head of the module
    # and the tuple of function objects at its foot. When DETECTOR_KINDS was
    # derived from _ALL_DETECTORS this comparison could not fail, which is the
    # exact shape of guard this file exists to argue against.
    assert {d.__name__ for d in detectors._ALL_DETECTORS} == set(detectors.DETECTOR_KINDS)
    # No duplicates: a detector registered twice would emit twice.
    assert len(detectors._ALL_DETECTORS) == len(set(detectors._ALL_DETECTORS))


def test_every_kind_resolves_to_a_callable():
    for kind in detectors.DETECTOR_KINDS:
        fn = getattr(detectors, kind, None)
        assert callable(fn), f"{kind} is exported but not callable"


def test_run_all_invokes_every_registered_detector(monkeypatch):
    """Substitution proof: each detector is replaced by a recorder, and
    ``run_all`` must call all of them. Reading the source would not catch a
    detector dropped from the loop by a bad merge."""
    called = []

    def _recorder(name):
        def _fn(events, session_id, runtime=None, **kwargs):
            called.append(name)
            return None
        return _fn

    patched = tuple(_recorder(d.__name__) for d in detectors._ALL_DETECTORS)
    monkeypatch.setattr(detectors, "_ALL_DETECTORS", patched)

    detectors.run_all([], "claude_code:x", "claude_code")
    assert set(called) == EXPECTED_KINDS


def test_every_detector_accepts_the_shared_keyword_contract():
    """thresholds / steps / facts are how calibration, the shared parse, and
    the money model reach a detector. One that does not accept them silently
    falls back to module constants."""
    for kind in detectors.DETECTOR_KINDS:
        sig = inspect.signature(getattr(detectors, kind))
        for param in ("thresholds", "steps", "facts"):
            assert param in sig.parameters, f"{kind} does not accept {param}"
            assert sig.parameters[param].kind is inspect.Parameter.KEYWORD_ONLY, (
                f"{kind}'s {param} must be keyword-only so positional calls "
                f"cannot silently bind the wrong argument")


def test_every_detector_survives_junk_without_raising():
    """The daemon tick must never die on one malformed session."""
    junk = [None, 42, "str", {"event_type": "tool_call", "data": "not-json{"}]
    for kind in detectors.DETECTOR_KINDS:
        fn = getattr(detectors, kind)
        assert fn(junk, "claude_code:x", "claude_code") is None


def test_incident_shape_carries_the_fields_every_consumer_reads():
    """One real incident, end to end, with the keys the daemon writes into
    loop_signals and the route flattens for the renderer."""
    events = [{"event_type": "tool_call", "ts": "2026-06-11T10:00:0%d" % i,
               "data": {"tool": "Bash", "args": {"command": "make"}}}
              for i in range(6)]
    out = detectors.run_all(list(reversed(events)), "codex:x", "codex",
                            facts={"cost_usd": 12.0, "session_seconds": 1800,
                                   "bad_for_seconds": 600})
    assert out, "six identical calls must produce an incident"
    inc = out[0]
    for key in ("kind", "session_id", "runtime", "severity", "title", "detail",
                "evidence", "first_bad_step", "spend_at_risk_usd",
                "spend_basis", "burn_rate_usd_per_min"):
        assert key in inc, f"incident is missing {key}"
    assert inc["severity"] in detectors._SEVERITY_RANK
    assert inc["spend_basis"] in ("burn_rate", "window_fraction", "unknown")
