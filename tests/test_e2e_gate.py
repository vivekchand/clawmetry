"""The merge gate must actually block the things it claims to block.

``scripts/e2e_gate.py`` backs the one required status check on ``main``. If its
evaluation is wrong, every other guard in the repository is decorative, so the
logic is tested directly over synthetic check-run payloads (no network).

The regression that motivated the file has its own test below:
``test_syntax_and_lint_failure_blocks_the_merge``. Before L0, ``Syntax & Lint``
was not aggregated, so the Python 3.9 annotation guard could go red while the
pull request merged green -- which is how 0.12.753 shipped a CLI that died at
import on every 3.9 install.
"""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts"))

import e2e_gate  # noqa: E402
from e2e_gate import REQUIRED_SPECS, Spec, evaluate  # noqa: E402


def run(name, conclusion="success", status="completed", run_id=1):
    return {
        "name": name,
        "status": status,
        "conclusion": conclusion,
        "id": run_id,
        "html_url": f"https://example.invalid/{run_id}",
    }


def state_of(results, label):
    for res in results:
        if res.spec.label == label:
            return res.state
    raise AssertionError(f"no result for {label!r}")


# --------------------------------------------------------------------------
# Single-job specs
# --------------------------------------------------------------------------

def test_single_check_passes():
    spec = Spec("Lint", "Syntax & Lint")
    assert state_of(evaluate([spec], [run("Syntax & Lint")]), "Lint") == "passed"


def test_single_check_failure_fails_the_gate():
    spec = Spec("Lint", "Syntax & Lint")
    results = evaluate([spec], [run("Syntax & Lint", "failure")])
    assert state_of(results, "Lint") == "failed"


def test_missing_check_is_pending_not_passed():
    """A check that never reported must never count as success."""
    spec = Spec("Lint", "Syntax & Lint")
    assert state_of(evaluate([spec], []), "Lint") == "pending"


def test_skipped_and_neutral_count_as_passing():
    spec = Spec("Lint", "Syntax & Lint")
    for conclusion in ("skipped", "neutral"):
        results = evaluate([spec], [run("Syntax & Lint", conclusion)])
        assert state_of(results, "Lint") == "passed", conclusion


# --------------------------------------------------------------------------
# Matrix specs -- the shrinking-matrix trap
# --------------------------------------------------------------------------

def test_matrix_passes_when_all_legs_pass():
    spec = Spec("pip", "pip install (*)", min_count=4)
    runs = [run(f"pip install (os{i})", run_id=i) for i in range(4)]
    assert state_of(evaluate([spec], runs), "pip") == "passed"


def test_matrix_fails_when_one_leg_fails():
    spec = Spec("pip", "pip install (*)", min_count=4)
    runs = [run(f"pip install (os{i})", run_id=i) for i in range(3)]
    runs.append(run("pip install (windows)", "failure", run_id=9))
    assert state_of(evaluate([spec], runs), "pip") == "failed"


def test_matrix_pending_while_legs_still_reporting():
    spec = Spec("pip", "pip install (*)", min_count=4)
    runs = [run(f"pip install (os{i})", run_id=i) for i in range(2)]
    assert state_of(evaluate([spec], runs), "pip") == "pending"


def test_shrinking_the_matrix_does_not_silently_pass():
    """Deleting a matrix leg must fail the gate, not reduce coverage quietly.

    This is the whole point of min_count. A glob alone would happily match the
    three remaining legs and report success, so dropping Windows from the
    matrix would look identical to passing on it.
    """
    spec = Spec("pip", "pip install (*)", min_count=4)
    runs = [run(f"pip install (os{i})", run_id=i) for i in range(3)]
    assert state_of(evaluate([spec], runs), "pip") == "pending"


# --------------------------------------------------------------------------
# Cancellation / replacement races
# --------------------------------------------------------------------------

def test_cancelled_alone_is_pending_not_failed():
    """cancel-in-progress must not fast-fail the gate."""
    spec = Spec("Lint", "Syntax & Lint")
    results = evaluate([spec], [run("Syntax & Lint", "cancelled")])
    assert state_of(results, "Lint") == "pending"


def test_in_progress_replacement_beats_stale_cancellation():
    spec = Spec("Lint", "Syntax & Lint")
    runs = [
        run("Syntax & Lint", "cancelled", run_id=1),
        run("Syntax & Lint", None, status="in_progress", run_id=2),
    ]
    assert state_of(evaluate([spec], runs), "Lint") == "pending"


def test_stale_cancellation_never_outranks_a_real_failure():
    """Priority must require BOTH completed AND a definitive conclusion.

    Found by mutation testing: changing ``status == \"completed\" and conclusion
    in DEFINITIVE`` to ``or`` survived the original suite, because the cases it
    covered happened to reach the same verdict either way. This one does not.
    A cancelled run with a HIGHER id must still lose to a genuine failure --
    under ``or`` the cancellation would score (2, high), outrank the failure,
    and the gate would report pending instead of failing. A red check would
    quietly become a slow check.
    """
    spec = Spec("Lint", "Syntax & Lint")
    runs = [
        run("Syntax & Lint", "failure", run_id=1),
        run("Syntax & Lint", "cancelled", run_id=99),
    ]
    assert state_of(evaluate([spec], runs), "Lint") == "failed"


def test_queued_run_does_not_outrank_a_definitive_one():
    """A queued rerun must not mask an already-known failure."""
    spec = Spec("Lint", "Syntax & Lint")
    runs = [
        run("Syntax & Lint", "failure", run_id=1),
        run("Syntax & Lint", None, status="queued", run_id=50),
    ]
    assert state_of(evaluate([spec], runs), "Lint") == "failed"


def test_definitive_result_beats_in_progress_rerun():
    spec = Spec("Lint", "Syntax & Lint")
    runs = [
        run("Syntax & Lint", None, status="in_progress", run_id=1),
        run("Syntax & Lint", "failure", run_id=2),
    ]
    assert state_of(evaluate([spec], runs), "Lint") == "failed"


# --------------------------------------------------------------------------
# The shipped configuration
# --------------------------------------------------------------------------

def test_syntax_and_lint_failure_blocks_the_merge():
    """Revert-proof for the 0.12.753 class.

    Syntax & Lint carries scripts/check_py39_annotations.py. Before L0 this
    check was not aggregated by the gate, so it could be red on a merging PR.
    If someone removes it from REQUIRED_SPECS, this test goes red.
    """
    # Every spec satisfied at exactly its required leg count.
    runs = []
    rid = 0
    for spec in REQUIRED_SPECS:
        for leg in range(spec.min_count):
            rid += 1
            name = (
                spec.pattern.replace("*", f"leg{leg}")
                if "*" in spec.pattern
                else spec.pattern
            )
            runs.append(run(name, run_id=rid))
    assert all(r.state == "passed" for r in evaluate(REQUIRED_SPECS, runs)), (
        "baseline should be fully green"
    )

    # Now fail only Syntax & Lint.
    broken = [r for r in runs if r["name"] != "Syntax & Lint"]
    broken.append(run("Syntax & Lint", "failure", run_id=999))
    results = evaluate(REQUIRED_SPECS, broken)
    assert any(r.state == "failed" for r in results), (
        "A red Syntax & Lint MUST block the merge. If this fails, the py3.9 "
        "guard is advisory again and 0.12.753 can recur."
    )


@pytest.mark.parametrize(
    "label",
    [
        "Syntax & Lint",
        "API Tests (3 OS)",
        "pip install matrix",
        "MOAT Verifier",
        "Entitlement API tests",
        "Wheel install & assets",
        "Store invariants",
    ],
)
def test_l0_additions_are_still_required(label):
    """These were advisory before L0. Removing one is a coverage regression."""
    assert any(s.label == label for s in REQUIRED_SPECS), (
        f"{label!r} was dropped from the merge gate. It was added in L0 "
        "precisely because a green PR could merge with it red."
    )


def test_pip_install_matrix_expects_exactly_the_py39_leg():
    """3 OS on 3.11 + the ubuntu 3.9 leg = 4. Exact, in both directions.

    Too FEW means the 3.9 leg stopped gating -- how 0.12.753 escaped. Too MANY
    means the gate waits forever for a leg that never reports, which times out
    and blocks every merge. Both directions are bugs, so this is ==, not >=.
    Changing the CI matrix means changing this number deliberately.
    """
    spec = next(s for s in REQUIRED_SPECS if s.label == "pip install matrix")
    assert spec.min_count == 4, (
        "The pip install matrix must be exactly 4 legs (ubuntu/macos/windows on "
        "3.11, plus ubuntu on 3.9). If ci.yml's matrix genuinely changed, update "
        "this number in the same PR."
    )


def test_api_tests_matrix_covers_all_three_operating_systems():
    spec = next(s for s in REQUIRED_SPECS if s.label == "API Tests (3 OS)")
    assert spec.min_count == 3, (
        "API Tests must gate on all three operating systems. Fewer silently "
        "drops an OS from merge protection."
    )


def test_main_refuses_to_run_without_credentials():
    """No token or no sha must be a hard error, never an accidental pass.

    Found by mutation testing: dropping the ``not`` from the credential guard,
    or turning its ``and`` into ``or``, both survived the original suite. Either
    mutation makes the gate skip its own check and fall through -- the worst
    possible failure mode for a merge gate, since it would report success
    without ever looking at a single check run.

    A mutant that breaks the guard makes main() fall through into the polling
    loop, and that used to reach the real network and a 30s sleep. Whether the
    mutation harness's per-mutant timeout tripped first was then a race with
    machine speed, which made the mutation score NONDETERMINISTIC: the same
    commit measured 53%, 50% and 47% on three runs, and the ratchet failed a PR
    that had not touched this file. A gate that can go red for reasons
    unrelated to test quality has no reliable path to green.

    So the fall-through is made fast and offline: `list_check_runs` is stubbed
    so no request is issued, and `--max-wait 0` makes the loop exit on its
    first pass. A broken guard now returns 1 instead of 2 and is killed by the
    ASSERTION, deterministically, rather than by a timeout race.
    """
    argv, env = sys.argv[:], os.environ.get("GITHUB_TOKEN")
    real_list = e2e_gate.list_check_runs
    e2e_gate.list_check_runs = lambda repo, sha, token: []

    os.environ.pop("GITHUB_TOKEN", None)
    sys.argv = ["e2e_gate.py", "--repo", "o/r", "--sha", "abc123", "--max-wait", "0"]
    try:
        assert e2e_gate.main() == 2, "missing GITHUB_TOKEN must exit 2"
    finally:
        sys.argv = argv
        if env is not None:
            os.environ["GITHUB_TOKEN"] = env

    argv = sys.argv[:]
    os.environ["GITHUB_TOKEN"] = "t"
    sys.argv = ["e2e_gate.py", "--sha", "abc123", "--max-wait", "0"]
    try:
        assert e2e_gate.main() == 2, "missing --repo must exit 2"
    finally:
        sys.argv = argv
        e2e_gate.list_check_runs = real_list
        if env is None:
            os.environ.pop("GITHUB_TOKEN", None)
        else:
            os.environ["GITHUB_TOKEN"] = env


def test_every_spec_has_a_nonempty_pattern_and_sane_count():
    for spec in REQUIRED_SPECS:
        assert spec.pattern.strip(), f"{spec.label} has an empty pattern"
        assert spec.min_count >= 1, f"{spec.label} has min_count < 1"


def test_no_duplicate_labels():
    labels = [s.label for s in REQUIRED_SPECS]
    assert len(labels) == len(set(labels)), f"duplicate spec labels: {labels}"


def test_list_mode_runs_without_network():
    """--list must work with no token, so the gate is inspectable locally."""
    argv = sys.argv[:]
    sys.argv = ["e2e_gate.py", "--list"]
    try:
        assert e2e_gate.main() == 0
    finally:
        sys.argv = argv


# --- pagination follow -------------------------------------------------------
#
# list_check_runs pages through the check-runs API by following the Link
# header's rel="next". That value is chosen by whatever answered the request,
# and the follow-up request carries the gate's Authorization header, so it is
# pinned to the origin of the page just read. These cover both halves: real
# pagination still works, and a link that points anywhere else is dropped.

PAGE1 = "https://api.github.com/repos/o/r/commits/abc/check-runs?per_page=100"


def test_next_page_followed_when_it_stays_on_the_same_origin():
    link = f'<{PAGE1}&page=2>; rel="next", <{PAGE1}&page=9>; rel="last"'
    assert e2e_gate._next_page_url(link, PAGE1) == f"{PAGE1}&page=2"


def test_no_next_link_ends_pagination():
    assert e2e_gate._next_page_url(f'<{PAGE1}>; rel="prev"', PAGE1) is None
    assert e2e_gate._next_page_url("", PAGE1) is None


@pytest.mark.parametrize(
    "target",
    [
        "https://evil.example/repos/o/r/check-runs",   # other host: would leak the token
        "http://api.github.com/repos/o/r/check-runs",  # downgraded scheme
        "file:///etc/passwd",                          # urlopen speaks file://
        "ftp://api.github.com/x",
        "//api.github.com/repos/o/r/check-runs",        # scheme-relative, not guessed at
    ],
)
def test_off_origin_next_link_is_not_followed(target):
    link = f'<{target}>; rel="next"'
    assert e2e_gate._next_page_url(link, PAGE1) is None


# ---------------------------------------------------------------------------
# A reporter that posts "pending" and then never returns a verdict.
#
# The 8090 App stopped finalising drift-bot after 2026-09-27T20:53Z. It kept
# posting "Drift Bot is analyzing the changed files..." and never replaced it,
# so `skip_if_unreported` did not apply -- a status WAS matched, it simply had
# no verdict. The gate read that as still running, waited the full 3600s and
# failed, on every open pull request at once, because the stall was in a shared
# third-party service and not in anybody's diff.
#
# The subtle half: the App re-posts `pending` on each CI re-trigger as a NEW
# entry. Aging the newest entry would let a stuck reporter reset its own clock
# forever, so a stall is dated from the OLDEST entry of the undecided run.
# ---------------------------------------------------------------------------
STALE = e2e_gate.STALE_PENDING_SECS
IN_PROGRESS = {"name": "drift-bot", "status": "in_progress", "conclusion": None}


def _ago(secs):
    stamp = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=secs)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def entry(state, age_secs, context="drift-bot"):
    """One status as the LIST endpoint returns it (created_at == updated_at)."""
    written = _ago(age_secs)
    return {"context": context, "state": state, "created_at": written, "updated_at": written}


def _serve(combined, listed, seen=None):
    """Stub urlopen, dispatching on which status endpoint was asked for.

    The two endpoints answer differently and the gate reads both for different
    reasons, so a stub that cannot tell them apart would not test anything.
    """
    class _Resp:
        def __init__(self, payload):
            self._payload = payload

        def read(self):
            return json.dumps(self._payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake(req, *a, **kw):
        url = req.full_url
        if seen is not None:
            seen.append(url)
        return _Resp(listed if "/statuses" in url else combined)

    return fake


def combined_of(*entries):
    """The combined endpoint's envelope: one status per context, latest wins."""
    return {"statuses": [dict(e) for e in entries]}


def shape(monkeypatch, combined, listed, seen=None):
    monkeypatch.setattr(e2e_gate.urllib.request, "urlopen", _serve(combined, listed, seen))
    return e2e_gate.list_commit_statuses("o/r", "deadbeef", "tok")


def _all_green_runs(except_label=None):
    """One successful check run per required leg, derived from the spec list.

    Built from REQUIRED_SPECS rather than a hand-kept list of names, so a spec
    added to the gate cannot leave this test asserting over a stale universe.
    """
    runs = []
    for spec in REQUIRED_SPECS:
        if spec.label == except_label:
            continue
        for leg in range(spec.min_count):
            runs.append(run(spec.pattern.replace("*", f"leg{leg}"), run_id=len(runs) + 1))
    return runs


# ── the stall itself ────────────────────────────────────────────────────────────────────────────

def test_fresh_pending_status_still_makes_the_gate_wait(monkeypatch):
    """A reporter that is simply still working must not be skipped."""
    fresh = entry("pending", 60)
    shaped = shape(monkeypatch, combined_of(fresh), [fresh])
    assert shaped == [IN_PROGRESS]
    assert state_of(evaluate(REQUIRED_SPECS, shaped), "Drift Bot") == "pending"


def test_status_undecided_past_the_window_is_treated_as_unreported(monkeypatch):
    old = entry("pending", STALE + 60)
    assert shape(monkeypatch, combined_of(old), [old]) == []
    assert state_of(evaluate(REQUIRED_SPECS, []), "Drift Bot") == "passed"


def test_a_reposted_pending_cannot_reset_its_own_clock(monkeypatch):
    """The regression a first cut of this fix missed.

    The combined endpoint shows only the newest entry, a minute old. The history
    shows the context has been undecided for hours. The history wins.
    """
    newest = entry("pending", 60)
    listed = [newest, entry("pending", STALE + 3600)]
    assert shape(monkeypatch, combined_of(newest), listed) == []


def test_a_run_of_fresh_reposts_still_waits(monkeypatch):
    newest = entry("pending", 30)
    listed = [newest, entry("pending", 90)]
    assert shape(monkeypatch, combined_of(newest), listed) == [IN_PROGRESS]


def test_a_stall_is_dated_from_the_latest_verdict_not_the_first_ever(monkeypatch):
    """pending -> failure -> pending is aged from the NEW pending only.

    A re-run after a red result starts a fresh clock; the ancient pending that
    preceded that verdict says nothing about the current attempt.
    """
    newest = entry("pending", 60)
    listed = [newest, entry("failure", 7200), entry("pending", STALE + 99999)]
    assert shape(monkeypatch, combined_of(newest), listed) == [IN_PROGRESS]


# ── what must never be softened ─────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("state,conclusion", [("failure", "failure"), ("error", "failure")])
def test_a_red_status_still_blocks_the_merge_at_any_age(monkeypatch, state, conclusion):
    """Staleness is only ever read off a status with no verdict.

    FLYWHEEL 1f calls a red drift-bot non-negotiable, and an old red one is
    still red. `error` is the transport-level failure and must not soften.
    """
    for age in (60, STALE + 99999):
        red = entry(state, age)
        shaped = shape(monkeypatch, combined_of(red), [red])
        assert shaped == [{"name": "drift-bot", "status": "completed", "conclusion": conclusion}]
        assert state_of(evaluate(REQUIRED_SPECS, shaped), "Drift Bot") == "failed"


def test_an_old_success_is_not_aged_out(monkeypatch):
    ok = entry("success", STALE + 99999)
    assert shape(monkeypatch, combined_of(ok), [ok]) == [
        {"name": "drift-bot", "status": "completed", "conclusion": "success"}
    ]


def test_a_spec_without_skip_if_unreported_stays_pending_when_stalled(monkeypatch):
    """Dropping a stale status must not invent a pass for a mandatory check."""
    spec = Spec("Syntax & Lint", "Syntax & Lint")
    assert not spec.skip_if_unreported
    old = entry("pending", STALE + 60, context="Syntax & Lint")
    assert shape(monkeypatch, combined_of(old), [old]) == []
    assert state_of(evaluate([spec], []), "Syntax & Lint") == "pending"


def test_a_stalled_reporter_does_not_wedge_the_whole_gate():
    """The regression in full: every other check green, drift-bot skipped."""
    results = evaluate(REQUIRED_SPECS, _all_green_runs(except_label="Drift Bot"))
    assert [r.spec.label for r in results if r.state != "passed"] == []


# ── failing towards waiting, never towards merging ────────────────────────────────────────────────────────────────

def test_an_unreadable_timestamp_never_skips_a_check(monkeypatch):
    for raw in (None, "", "not-a-date", "2026-09-30T02:44:16+00:00"):
        assert e2e_gate._status_written_at({"created_at": raw}) is None
    bare = {"context": "drift-bot", "state": "pending"}
    assert shape(monkeypatch, combined_of(bare), [bare]) == [IN_PROGRESS]
    # One unreadable entry inside the run discards the whole run's age, so the
    # gate waits rather than skipping on a partial clock.
    listed = [entry("pending", 60), bare, entry("pending", STALE + 9999)]
    assert shape(monkeypatch, combined_of(entry("pending", 60)), listed) == [IN_PROGRESS]


def test_updated_at_is_the_fallback_when_created_at_is_absent():
    assert e2e_gate._status_written_at({"updated_at": _ago(300)}) is not None
    assert e2e_gate._status_written_at({}) is None


def test_a_context_missing_from_the_history_page_is_not_aged(monkeypatch):
    """The list endpoint is newest-first GLOBALLY, so a page can omit a context.

    Absence must mean \"no age known\" -> keep waiting, never \"stale\" -> skip.
    """
    pending = entry("pending", STALE + 9999)
    assert shape(monkeypatch, combined_of(pending), []) == [IN_PROGRESS]


def test_a_failed_history_read_leaves_the_status_pending(monkeypatch):
    """If only the history call dies, the gate must still wait, not skip."""
    def fake(req, *a, **kw):
        if "/statuses" in req.full_url:
            raise urllib.error.HTTPError(req.full_url, 503, "nope", {}, io.BytesIO(b"down"))

        class _R:
            def read(self):
                return json.dumps(combined_of(entry("pending", STALE + 9999))).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return _R()

    monkeypatch.setattr(e2e_gate.urllib.request, "urlopen", fake)
    assert e2e_gate.list_commit_statuses("o/r", "sha", "tok") == [IN_PROGRESS]


def test_a_failed_status_read_returns_nothing_rather_than_a_verdict(monkeypatch):
    def boom(req, *a, **kw):
        raise urllib.error.HTTPError(req.full_url, 503, "nope", {}, io.BytesIO(b"down"))

    monkeypatch.setattr(e2e_gate.urllib.request, "urlopen", boom)
    assert e2e_gate.list_commit_statuses("o/r", "sha", "tok") == []


# ── shape of the reads themselves ────────────────────────────────────────────────────────────────────────────────

def test_current_state_comes_from_the_combined_endpoint(monkeypatch):
    """Both endpoints are read, each for what only it can answer.

    The combined endpoint is documented to give one status per context; the
    list endpoint gives the history a stall is dated from. Reading current
    state off the list endpoint would risk a context whose latest entry fell
    off the page.
    """
    seen = []
    old = entry("pending", STALE + 60)
    shape(monkeypatch, combined_of(old), [old], seen)
    assert any(u.endswith("/status?per_page=100") for u in seen), seen
    assert any("/statuses?per_page=100" in u for u in seen), seen


def test_history_is_read_only_when_something_is_undecided(monkeypatch):
    """No pending status means no reason to pay for the second call."""
    seen = []
    ok = entry("success", 60)
    shape(monkeypatch, combined_of(ok), [ok], seen)
    assert not any("/statuses" in u for u in seen), seen


def test_history_is_read_once_even_with_several_stalled_contexts(monkeypatch):
    seen = []
    a = entry("pending", STALE + 60, context="drift-bot")
    b = entry("pending", STALE + 60, context="other-bot")
    assert shape(monkeypatch, combined_of(a, b), [a, b], seen) == []
    assert len([u for u in seen if "/statuses" in u]) == 1, seen


def test_the_staleness_window_is_far_wider_than_observed_run_times():
    """Guard the constant: 1.3 min was the slowest real finalisation measured."""
    assert e2e_gate.STALE_PENDING_SECS >= 600
