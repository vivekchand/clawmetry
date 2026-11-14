"""Delivery attribution: which pull request did this session's money buy?

Every cost figure ClawMetry showed before this was keyed on a session, a
runtime, a model or a node, so the product could say what agents cost but
not what the spend produced. These tests pin the two properties that make
the answer trustworthy rather than merely present:

* **The parts sum to the whole.** One session touches several pull requests,
  so joining session cost to each PR it mentions multiplies the money. On a
  real node that join reported a $106,946 pull request on a $3,843 machine.
  Cost is therefore split at event level, and the split plus the
  unattributed remainder must equal the session's own cost.
* **A reference must be a real reference.** Each false positive measured
  against live data has a test here, because a table that quietly attributes
  spend to the wrong pull request is worse than no table.
"""

from __future__ import annotations

import importlib

import pytest

from clawmetry import attribution


# ── Helpers ─────────────────────────────────────────────────────────────────

def _call(command, ts="2026-10-15T10:00:00Z", cost=None):
    """A tool_call event shaped the way the family adapters emit one."""
    return {
        "event_type": "tool_call",
        "ts": ts,
        "cost_usd": cost,
        "data": {
            "role": "assistant",
            "tool_name": "Bash",
            "tool_calls": [{
                "id": "toolu_1",
                "name": "Bash",
                "input": {"command": command},
            }],
        },
    }


def _usage(cost, ts="2026-10-15T10:00:01Z"):
    """A usage event: where the money actually is."""
    return {
        "event_type": "usage",
        "ts": ts,
        "cost_usd": None,
        "data": {"extra": {"costUsd": cost, "model": "claude-opus-5"}},
    }


def _newest_first(events):
    """``query_events`` hands the store's rows back newest-first."""
    return list(reversed(events))


# ── Extraction: the signal ──────────────────────────────────────────────────

def test_gh_pr_command_yields_pr_repo_and_role():
    """``gh pr edit 6275 --repo nordwind/nano`` is an explicit, authoring reference."""
    out = attribution.extract_session_delivery(
        _newest_first([_call("gh pr edit 6275 --repo nordwind/repo")]), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == 1
    assert prs[0]["ref"] == "6275"
    assert prs[0]["repo"] == "nordwind/repo"
    assert prs[0]["role"] == attribution.ROLE_AUTHORED
    assert prs[0]["confidence"] == 1.0
    assert prs[0]["basis"] == attribution.BASIS_PR_REFERENCE


def test_pr_url_carries_its_own_repo():
    """A pull-request URL is the strongest form: number and repo together."""
    out = attribution.extract_session_delivery(
        _newest_first([_call("open https://github.com/nordwind/repo/pull/42")]), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert (prs[0]["ref"], prs[0]["repo"]) == ("42", "nordwind/repo")


def test_a_url_that_merely_appears_is_explored_not_reviewed():
    """Reviewing is an action. A link in a comment or an output line is
    evidence the pull request was seen, nothing more, and collapsing the two
    is what makes the role column stop meaning anything."""
    seen = attribution.extract_session_delivery(_newest_first([
        {"event_type": "tool_result", "ts": "2026-10-15T10:00:00Z",
         "data": {"content": "see https://github.com/nordwind/repo/pull/42"}}]), "s1")
    assert [a for a in seen["artifacts"] if a["kind"] == "pr"][0]["role"] \
        == attribution.ROLE_EXPLORED

    acted = attribution.extract_session_delivery(
        _newest_first([_call("gh pr diff 42 --repo nordwind/repo")]), "s1")
    assert [a for a in acted["artifacts"] if a["kind"] == "pr"][0]["role"] \
        == attribution.ROLE_REVIEWED


def test_read_only_verb_is_a_review_not_authorship():
    out = attribution.extract_session_delivery(
        _newest_first([_call("gh pr checks 7 --repo nordwind/repo")]), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert prs[0]["role"] == attribution.ROLE_REVIEWED


def test_a_commit_elsewhere_does_not_make_a_viewed_pr_authored():
    """Role is what the session did TO THAT pull request, nothing else.

    An earlier version promoted every referenced PR to "authored" whenever
    the session ran any git write anywhere. On a real node almost every
    session commits something, so the column read "authored" on all 100
    rows: it claimed authorship of pull requests the session had only looked
    at, and a column whose value never varies tells a reader nothing.
    """
    out = attribution.extract_session_delivery(_newest_first([
        _call("gh pr view 7 --repo nordwind/repo"),
        _call("git commit -m 'fix' && git push origin feat/x"),
    ]), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert prs[0]["role"] == attribution.ROLE_REVIEWED


def test_roles_stay_distinct_within_one_session():
    """The column has to be able to say different things about two PRs."""
    out = attribution.extract_session_delivery(_newest_first([
        _call("gh pr view 7 --repo nordwind/repo"),
        _call("gh pr merge 8 --repo nordwind/repo --squash"),
        _call("git commit -m 'fix'"),
    ]), "s1")
    roles = {a["ref"]: a["role"] for a in out["artifacts"] if a["kind"] == "pr"}
    assert roles == {"7": attribution.ROLE_REVIEWED,
                     "8": attribution.ROLE_AUTHORED}


def test_evidence_leads_with_the_reference_not_its_surroundings():
    """A PR URL inside a tool RESULT has no command around it, so a centred
    window led with whatever JSON preceded it. The claim comes first."""
    noise = '{"role": "tool", "content": "' + "x" * 400
    out = attribution.extract_session_delivery(_newest_first([{
        "event_type": "tool_result", "ts": "2026-10-15T10:00:00Z",
        "cost_usd": None,
        "data": {"content": noise
                 + " https://github.com/nordwind/repo/pull/4242 and then more text"},
    }]), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert prs and prs[0]["ref"] == "4242"
    ev = prs[0]["evidence"]
    assert "github.com/nordwind/repo/pull/4242" in ev
    assert ev.index("github.com") < 40, (
        f"the reference must lead the snippet, got: {ev[:80]!r}")


def test_sole_repo_fills_a_bare_pr_but_lowers_confidence():
    """One repo in the session can own a flagless PR; two must not guess."""
    one = attribution.extract_session_delivery(_newest_first([
        _call("gh pr edit 6338 --title x"),
        _call("git remote -v   # github.com/nordwind/alpha.git"),
    ]), "s1")
    pr = [a for a in one["artifacts"] if a["kind"] == "pr"][0]
    assert pr["repo"] == "nordwind/alpha"
    assert pr["confidence"] < 1.0, "a guessed repo must not claim certainty"

    two = attribution.extract_session_delivery(_newest_first([
        _call("gh pr edit 6338 --title x"),
        _call("git remote -v  # github.com/nordwind/alpha.git github.com/nordwind/beta.git"),
    ]), "s1")
    pr2 = [a for a in two["artifacts"] if a["kind"] == "pr"][0]
    assert pr2["repo"] == "", "two candidate repos must stay blank, not guess"


# ── Extraction: the false positives, each measured on live data ─────────────

@pytest.mark.parametrize("command", [
    # `gh pr list` takes no PR argument, so `20` is the --limit value.
    "gh pr list --repo nordwind/repo --limit 20",
    "gh pr status",
    # Prose, not a command.
    "the fix landed in pr 6275",
    # A different gh subcommand that happens to carry a number.
    "gh run list --repo nordwind/repo 42",
])
def test_these_are_not_pull_request_references(command):
    out = attribution.extract_session_delivery(
        _newest_first([_call(command)]), "s1")
    assert [a for a in out["artifacts"] if a["kind"] == "pr"] == []


def test_repo_resolves_per_command_not_per_payload():
    """Chained commands against different repos must not cross-contaminate.

    One tool call runs several commands; resolving ``--repo`` against the
    whole payload filed PR 2566 under the first command's repository, which
    surfaced as the same pull request appearing under two repositories.

    The neighbouring command's ``--repo`` is deliberately placed CLOSER to
    the pull-request token than the owning command's own flag, which is the
    shape live data actually takes (``gh pr checks N --json a,b,c --repo X``).
    Proximity alone therefore picks the wrong repository here, so this pins
    the command boundary rather than the tie-breaker in front of it.
    """
    out = attribution.extract_session_delivery(_newest_first([
        _call("gh run list --repo nordwind/alpha; gh pr checks 2566 "
              "--json name,state,bucket,link,description,workflow,event "
              "--repo nordwind/beta"),
    ]), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == 1
    assert prs[0]["repo"] == "nordwind/beta"


def test_bracketed_digits_are_not_a_commit():
    """``[2026-10-09 37085346064]`` is a timestamp, not git commit output."""
    assert attribution._find_commit_refs("[2026-10-09 37085346064]") == []
    found = attribution._find_commit_refs("[feat/x 4c9cfa6] subject")
    assert found and found[0]["commit"] == "4c9cfa6"


def test_trunk_branches_are_not_a_unit_of_delivery():
    out = attribution.extract_session_delivery(_newest_first([
        _call("git push origin main"),
        _call("git checkout -b feat/real-work"),
    ]), "s1")
    branches = {a["ref"] for a in out["artifacts"] if a["kind"] == "branch"}
    assert "feat/real-work" in branches
    assert "main" not in branches


# ── Evidence must never leak a secret ───────────────────────────────────────

def test_evidence_is_redacted_before_it_is_stored():
    """Evidence is a slice of a real command line and is scanned first."""
    token = "ghp_" + "a1b2c3d4e5" * 4
    out = attribution.extract_session_delivery(_newest_first([
        _call(f"GH_TOKEN={token} gh pr view 6275 --repo nordwind/repo"),
    ]), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert prs, "the PR itself must still be found"
    assert token not in prs[0]["evidence"]
    for art in out["artifacts"]:
        assert token not in art["evidence"]


# ── The cost split: the parts sum to the whole ──────────────────────────────

def test_cost_split_sums_to_the_session_total():
    """The fan-out guard.

    Two pull requests, $3 spent while each was in play. A session-level join
    would report $6 against each; the split must report $3 each and $6 in
    total, never more.
    """
    events = [
        _call("gh pr edit 100 --repo nordwind/repo", ts="2026-10-15T10:00:00Z"),
        _usage(3.0, ts="2026-10-15T10:00:01Z"),
        _call("gh pr edit 200 --repo nordwind/repo", ts="2026-10-15T10:00:02Z"),
        _usage(3.0, ts="2026-10-15T10:00:03Z"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = {a["ref"]: a["cost_usd"] for a in out["artifacts"] if a["kind"] == "pr"}
    assert prs == {"100": 3.0, "200": 3.0}
    assert out["total_usd"] == 6.0
    assert out["unattributed_usd"] == 0.0
    assert sum(prs.values()) + out["unattributed_usd"] == out["total_usd"]
    assert out["basis"] == "last_touch_segment"


def test_spend_before_any_pull_request_is_unattributed():
    """Honest remainder: exploration that never named a PR is not free."""
    events = [
        _usage(2.5, ts="2026-10-15T10:00:00Z"),
        _call("gh pr edit 100 --repo nordwind/repo", ts="2026-10-15T10:00:01Z"),
        _usage(1.5, ts="2026-10-15T10:00:02Z"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = {a["ref"]: a["cost_usd"] for a in out["artifacts"] if a["kind"] == "pr"}
    assert prs == {"100": 1.5}
    assert out["unattributed_usd"] == 2.5
    assert out["total_usd"] == 4.0


def test_a_session_that_names_no_pull_request_attributes_nothing():
    out = attribution.extract_session_delivery(
        _newest_first([_usage(9.0)]), "s1")
    assert [a for a in out["artifacts"] if a["kind"] == "pr"] == []
    assert out["unattributed_usd"] == 9.0


def test_cost_comes_from_the_column_when_present():
    """``events.cost_usd`` is authoritative; the payload is the fallback."""
    events = [
        _call("gh pr edit 1 --repo nordwind/repo"),
        {"event_type": "usage", "ts": "2026-10-15T10:00:05Z",
         "cost_usd": 4.0, "data": {"extra": {"costUsd": 99.0}}},
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    assert out["total_usd"] == 4.0


@pytest.mark.parametrize("bad", [-5.0, float("inf"), float("nan"), "abc", None])
def test_a_bad_cost_is_zero_not_a_crash(bad):
    out = attribution.extract_session_delivery(_newest_first([
        _call("gh pr edit 1 --repo nordwind/repo"),
        {"event_type": "usage", "ts": "2026-10-15T10:00:05Z",
         "cost_usd": bad, "data": {}},
    ]), "s1")
    assert out["total_usd"] == 0.0


# ── Never crash on bad input ────────────────────────────────────────────────

@pytest.mark.parametrize("events", [
    [],
    [None, 3, "nonsense"],
    [{"event_type": "tool_call"}],
    [{"event_type": "tool_call", "ts": None, "data": b"\xff\xfe not json"}],
    [{"event_type": "tool_call", "ts": "x", "data": "{broken json"}],
])
def test_malformed_event_streams_never_raise(events):
    out = attribution.extract_session_delivery(events, "s1")
    assert out["artifacts"] == []
    assert out["total_usd"] == 0.0


def test_event_count_is_reported_so_truncation_is_visible():
    out = attribution.extract_session_delivery(
        _newest_first([_call("echo hi"), _usage(1.0)]), "s1")
    assert out["event_count"] == 2


def test_runtime_is_recorded_as_the_store_agent_type():
    out = attribution.extract_session_delivery([], "s1", runtime="codex")
    assert out["agent_type"] == "codex"
    assert attribution.extract_session_delivery([], "s1")["agent_type"] == "openclaw"


def test_per_session_caps_bound_the_work():
    """A digest cron naming hundreds of PRs cannot dominate the table."""
    events = [_call(f"gh pr view {n} --repo nordwind/repo")
              for n in range(1000, 1000 + attribution.MAX_PRS_PER_SESSION + 25)]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == attribution.MAX_PRS_PER_SESSION


# ── Persistence + the read API ──────────────────────────────────────────────

@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH",
                       str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls

    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=True)


def _attribute(store, session_id, events, runtime="openclaw"):
    result = attribution.extract_session_delivery(
        _newest_first(events), session_id, runtime=runtime)
    written = store.persist_session_attribution(result, node_id="node-a")
    return result, written


def test_persist_then_query_delivery_roundtrip(store):
    _attribute(store, "s1", [
        _call("gh pr edit 6275 --repo nordwind/repo"),
        _usage(12.0),
    ])
    out = store.query_delivery(kind="pr")
    assert out["available"] is True
    assert len(out["rows"]) == 1
    row = out["rows"][0]
    assert (row["repo"], row["ref"]) == ("nordwind/repo", "6275")
    assert row["sessions"] == 1
    assert row["cost_usd"] == 12.0
    assert row["role"] == "authored"
    assert row["basis"] == attribution.BASIS_PR_REFERENCE


def test_two_sessions_on_one_pull_request_add_up(store):
    _attribute(store, "s1", [_call("gh pr edit 1 --repo nordwind/repo"), _usage(4.0)])
    _attribute(store, "s2", [_call("gh pr edit 1 --repo nordwind/repo"), _usage(6.0)])
    row = store.query_delivery(kind="pr")["rows"][0]
    assert row["sessions"] == 2
    assert row["cost_usd"] == 10.0


def test_recomputation_drops_an_artifact_that_is_no_longer_there(store):
    """Replace-per-session, so a stale pull request cannot linger forever."""
    _attribute(store, "s1", [_call("gh pr edit 1 --repo nordwind/repo"), _usage(1.0)])
    _attribute(store, "s1", [_call("gh pr edit 2 --repo nordwind/repo"), _usage(1.0)])
    refs = {r["ref"] for r in store.query_delivery(kind="pr")["rows"]}
    assert refs == {"2"}


def test_totals_report_the_unattributed_remainder(store):
    """Attributed spend shown without the remainder reads as the whole bill."""
    _attribute(store, "s1", [
        _usage(7.0, ts="2026-10-15T10:00:00Z"),
        _call("gh pr edit 1 --repo nordwind/repo", ts="2026-10-15T10:00:01Z"),
        _usage(3.0, ts="2026-10-15T10:00:02Z"),
    ])
    totals = store.query_delivery(kind="pr")["totals"]
    assert totals["attributed_usd"] == 3.0
    assert totals["unattributed_usd"] == 7.0
    assert totals["sessions_attributed"] == 1


def test_delivery_is_filtered_by_runtime_server_side(store):
    """The runtime switcher contract: one runtime means one runtime's rows."""
    _attribute(store, "s1", [_call("gh pr edit 1 --repo nordwind/repo"), _usage(5.0)],
               runtime="claude_code")
    _attribute(store, "s2", [_call("gh pr edit 2 --repo nordwind/repo"), _usage(8.0)],
               runtime="codex")

    cc = store.query_delivery(kind="pr", runtime="claude_code")
    assert {r["ref"] for r in cc["rows"]} == {"1"}
    assert cc["totals"]["attributed_usd"] == 5.0

    cx = store.query_delivery(kind="pr", runtime="codex")
    assert {r["ref"] for r in cx["rows"]} == {"2"}
    assert cx["totals"]["attributed_usd"] == 8.0

    absent = store.query_delivery(kind="pr", runtime="cursor")
    assert absent["rows"] == []
    assert absent["totals"]["attributed_usd"] == 0.0, \
        "an absent runtime must report zero, never the node total"

    assert len(store.query_delivery(kind="pr")["rows"]) == 2


def test_session_artifacts_read_back_for_one_session(store):
    _attribute(store, "s1", [
        _call("gh pr edit 9 --repo nordwind/repo"),
        _call("git checkout -b feat/x"),
        _usage(2.0),
    ])
    rows = store.query_session_artifacts(session_id="s1")
    kinds = {r["kind"] for r in rows}
    assert "pr" in kinds and "branch" in kinds
    assert store.query_session_artifacts(session_id="nope") == []


def test_watermarks_let_the_daemon_skip_unchanged_sessions(store):
    _attribute(store, "s1", [_call("gh pr edit 1 --repo nordwind/repo"), _usage(1.0)])
    marks = store.attribution_watermarks()
    assert marks.get("s1") == 2


def test_only_pull_request_rows_carry_money(store):
    """A per-file share of a model call would be an invented number."""
    _attribute(store, "s1", [
        _call("gh pr edit 1 --repo nordwind/repo"),
        _call("git checkout -b feat/x"),
        _usage(5.0),
    ])
    for row in store.query_session_artifacts(session_id="s1"):
        if row["kind"] == "pr":
            assert row["cost_usd"] is not None
        else:
            assert row["cost_usd"] is None


def test_one_pull_request_is_one_row_however_many_checkouts_exist(store):
    """The worktree fan-out guard.

    ``git_repos`` is keyed on ``repo_root``, so the same GitHub repository has
    one row per working directory: a git worktree, a second clone and the
    original checkout are three rows with identical owner/name. Joining the
    pull-request metadata straight through multiplied every row by that
    count, and the live list showed one pull request five times.
    """
    _attribute(store, "s1", [_call("gh pr edit 6382 --repo nordwind/repo"),
                             _usage(15.0)])
    for root in ("/src/repo", "/src/repo-worktree-a", "/src/repo-worktree-b"):
        store.ingest_git_scan({
            "repo_root": root, "owner": "nordwind", "name": "repo",
            "pull_requests": [{"number": 6382, "state": "MERGED",
                               "title": "the one real PR",
                               "url": "https://github.com/nordwind/repo/pull/6382"}],
        })
    rows = store.query_delivery(kind="pr")["rows"]
    assert len(rows) == 1, f"one PR, {len(rows)} rows: the join fanned out"
    assert rows[0]["ref"] == "6382"
    assert rows[0]["cost_usd"] == 15.0, "cost must not be multiplied either"
    assert rows[0]["title"] == "the one real PR", \
        "the enrichment must still arrive after de-duplication"
    assert rows[0]["state"] == "MERGED"


def test_a_pull_request_with_no_local_checkout_still_gets_a_row(store):
    """Attribution must not depend on the repository being on this machine."""
    _attribute(store, "s1", [_call("gh pr edit 77 --repo halcyon/repo"),
                             _usage(2.0)])
    rows = store.query_delivery(kind="pr")["rows"]
    assert len(rows) == 1
    assert rows[0]["ref"] == "77"
    assert rows[0]["title"] == "", "no checkout means no title, not no row"


def test_evidence_reads_as_the_command_not_as_json(store):
    """Evidence sits under a column headed "How we know".

    Cut as a fixed character window out of the serialized payload it landed
    in neighbouring JSON (``...ods", "name": "Bash", "input": {``), which
    tells a reader nothing. It is bounded to the matched command instead.
    """
    out = attribution.extract_session_delivery(_newest_first([
        _call("gh pr checks 6283 --repo nordwind/repo --json name,state"),
    ]), "s1")
    ev = [a for a in out["artifacts"] if a["kind"] == "pr"][0]["evidence"]
    assert "gh pr checks 6283" in ev
    for noise in ('"name": "Bash"', '"input"', "tool_calls", "toolu_"):
        assert noise not in ev, f"evidence leaked payload structure: {noise}"


def test_a_rules_change_recomputes_sessions_that_never_moved(store, monkeypatch):
    """The migration guard.

    The watermark compares event counts, so it only ever notices a session
    that GREW. When the extraction or role rules change, a dormant session
    keeps the answer the old rules gave it and the table holds two meanings
    at once with nothing to tell them apart. That is not hypothetical: the
    role fix that made this column mean anything would have reached none of
    the rows already stored.
    """
    events = [_call("gh pr edit 1 --repo nordwind/repo"), _usage(1.0)]
    for i, ev in enumerate(events):
        store.ingest(dict(ev, id=f"e{i}", session_id="s1", node_id="node-a",
                          agent_id="main", agent_type="openclaw"))
    store.flush()

    pending = store.sessions_pending_attribution()
    assert [p["session_id"] for p in pending] == ["s1"], \
        "a session never attributed must pend"
    _attribute(store, "s1", events)
    assert store.sessions_pending_attribution() == [], \
        "an unchanged session under the same rules must not be re-read"

    monkeypatch.setattr(attribution, "RULES_VERSION", "99-newer")
    pending = store.sessions_pending_attribution()
    assert [p["session_id"] for p in pending] == ["s1"], \
        "a rules bump must bring the untouched session back for recomputation"

    # And once recomputed under the new rules it settles again.
    _attribute(store, "s1", events)
    assert store.sessions_pending_attribution() == []


def test_the_rules_version_is_a_plain_string_that_can_only_move_forward(store):
    """It is compared as a value, not parsed, so anything non-empty works;
    an empty one would make every session pend forever."""
    assert isinstance(attribution.RULES_VERSION, str)
    assert attribution.RULES_VERSION.strip()


def test_the_runtime_comes_from_the_session_id_not_the_event_column(store):
    """The runtime switcher contract, at the source.

    ``events.agent_type`` reads 'openclaw' for almost every event on a real
    multi-runtime node (77,323 of 77,474 on the node this was measured on)
    while the session ids said claude_code, codex, cursor and five more.
    Filing artifacts under the column left the Delivered tab empty under
    every runtime the switcher offers.
    """
    from clawmetry import sync as _sync

    # The id prefix wins over a column that says otherwise.
    assert _sync._attribution_runtime(
        "codex:01a0feac", {"agent_type": "openclaw"}) == "codex"
    assert _sync._attribution_runtime(
        "claude_code:abc", {"agent_type": "openclaw"}) == "claude_code"
    # A bare id genuinely is OpenClaw's, and the column still answers.
    assert _sync._attribution_runtime("plain-uuid", {}) == "openclaw"
    assert _sync._attribution_runtime(
        "plain-uuid", {"agent_type": "nemoclaw"}) == "nemoclaw"


def test_refiling_a_session_under_a_new_runtime_leaves_no_duplicate(store):
    """The migration this correction needs.

    A recomputation that derives a different runtime than the stored one must
    REPLACE the session's rows, not add a second set beside them. Deleting by
    (session_id, agent_type) would have left the old 'openclaw' rows in place
    and doubled every figure on the tab.
    """
    events = [_call("gh pr edit 1 --repo nordwind/repo"), _usage(6.0)]
    _attribute(store, "s1", events, runtime="openclaw")
    assert store.query_delivery(kind="pr")["totals"]["attributed_usd"] == 6.0

    _attribute(store, "s1", events, runtime="codex")
    out = store.query_delivery(kind="pr")
    assert len(out["rows"]) == 1, "the old runtime's row must be gone"
    assert out["totals"]["attributed_usd"] == 6.0, "cost must not double"
    assert store.query_delivery(kind="pr", runtime="codex")["rows"]
    assert store.query_delivery(kind="pr", runtime="openclaw")["rows"] == []
    # And exactly one state row survives, so the remainder is not counted twice.
    assert store._delivery_totals()["unattributed_usd"] == 0.0


def test_one_pull_request_seen_with_and_without_a_repo_is_one_row(store):
    """The constraint-error guard.

    A session can reference the same pull request twice: once in a command
    that carried no ``--repo`` and once in a command that did. The sole-repo
    backfill then filled the first one in, producing two artifacts with the
    same (kind, ref, repo), which IS the primary key. The write failed on a
    constraint error and the session stayed unattributed on every pass
    forever. Measured on a real node: copilot:7d1766c8, PR 4465, seven
    consecutive failures.
    """
    events = [
        _call("gh pr view 4465"),
        _call("gh pr edit 4465 --repo nordwind/repo"),
        _usage(5.0),
    ]
    result, written = _attribute(store, "s1", events)
    prs = [a for a in result["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == 1, f"one pull request, {len(prs)} artifacts"
    assert prs[0]["repo"] == "nordwind/repo"
    assert written > 0, "the session must persist, not fail on a constraint"

    rows = store.query_delivery(kind="pr")["rows"]
    assert len(rows) == 1
    assert rows[0]["cost_usd"] == 5.0, "cost must not be counted twice"
    # The merged row carries the authoring verb, and flags that part of it
    # was inferred.
    assert prs[0]["role"] == attribution.ROLE_AUTHORED


def test_a_duplicate_artifact_cannot_cost_the_session_its_whole_write(store):
    """Defence in depth: even if an extractor change produced a colliding
    pair, the session must still be attributed rather than lost."""
    result = {
        "session_id": "s2", "agent_type": "openclaw", "event_count": 2,
        "total_usd": 3.0, "unattributed_usd": 0.0, "basis": "last_touch_segment",
        "artifacts": [
            {"kind": "pr", "ref": "9", "repo": "nordwind/repo", "role": "authored",
             "confidence": 1.0, "cost_usd": 3.0, "evidence": "a", "basis": "pr_reference"},
            {"kind": "pr", "ref": "9", "repo": "nordwind/repo", "role": "reviewed",
             "confidence": 0.5, "cost_usd": 3.0, "evidence": "b", "basis": "pr_reference"},
        ],
    }
    assert store.persist_session_attribution(result, node_id="n") == 1
    rows = store.query_delivery(kind="pr")["rows"]
    assert len(rows) == 1 and rows[0]["cost_usd"] == 3.0


def test_a_failed_persist_leaves_the_session_exactly_as_it_was(store):
    """Atomicity, learned from a live node.

    DuckDB autocommits each statement, and an executemany that hits a
    constraint on row N leaves rows 0..N-1 committed. One session ended up
    with artifacts and NO state row that way, which also means it is
    recomputed on every pass forever, because a missing state row reads as
    never attributed. The write has to be all or nothing.
    """
    good = [_call("gh pr edit 1 --repo nordwind/repo"), _usage(4.0)]
    _attribute(store, "s1", good)
    before = store.query_session_artifacts(session_id="s1")
    assert before

    # Fail precisely where the live one failed: after the artifact rows are
    # written and before the state row is. No input a caller can supply
    # lands there, so the connection raises on that one statement.
    real_conn = store._conn

    class _FailsOnStateWrite:
        def __getattr__(self, name):
            return getattr(real_conn, name)

        def execute(self, sql, *a, **kw):
            if "session_attribution_state" in str(sql) and "INSERT" in str(sql):
                raise RuntimeError("simulated failure between the two writes")
            return real_conn.execute(sql, *a, **kw)

    store._conn = _FailsOnStateWrite()
    try:
        rewrite = {
            "session_id": "s1", "agent_type": "openclaw", "event_count": 99,
            "total_usd": 1.0, "unattributed_usd": 0.0,
            "basis": "last_touch_segment",
            "artifacts": [
                {"kind": "pr", "ref": "2", "repo": "nordwind/repo",
                 "role": "authored", "confidence": 1.0, "cost_usd": 1.0,
                 "evidence": "x", "basis": "pr_reference"},
            ],
        }
        assert store.persist_session_attribution(rewrite, node_id="n") == 0
    finally:
        store._conn = real_conn

    after = store.query_session_artifacts(session_id="s1")
    assert after == before, (
        "a failed persist must not delete the previous answer or leave a "
        "half-written one")
    state = store.attribution_watermarks()
    assert "s1" in state, "the state row must survive a failed rewrite"


def test_empty_store_is_an_honest_empty_not_an_error(store):
    out = store.query_delivery(kind="pr")
    assert out["available"] is True
    assert out["rows"] == []
    assert out["totals"]["attributed_usd"] == 0.0


# ── Evidence has to read as the work, not as the harness ────────────────────
#
# The rows below are live strings off a real node. Evidence is the "How we
# know" column: a reader who cannot read it cannot check the claim, so a
# snippet that is technically correct and practically unreadable is a bug.
# 53% of the pull-request rows on the shipped tab opened on wrapper debris.

def _codex_call(script, ts="2026-10-15T10:00:00Z", cost=None):
    """A Codex tool call: the shell command is inside a SERIALIZED payload.

    This is the shape that made the first version of the unwrap a no-op. The
    quotes around the command arrive escaped, ``{cmd:\\"gh pr ...``, so a
    pattern written against ``{cmd:"gh pr ...`` matched nothing at all on a
    real node.
    """
    return {
        "event_type": "tool_call",
        "ts": ts,
        "cost_usd": cost,
        "data": {"tool_name": "shell", "tool_calls": [
            {"name": "shell", "input": {"script": script}}]},
    }


def test_evidence_opens_on_the_command_not_on_the_tool_wrapper():
    """Live: ``ols.exec_command({cmd:\\"gh pr edit 6248 --repo ...``."""
    script = (r'const r=await tools.exec_command({cmd:\"gh pr edit 6248 '
              r'--repo vivekchand/clawmetry --body-file /tmp/body.md\",'
              r'\"max_output_tokens\":3000});')
    out = attribution.extract_session_delivery(
        _newest_first([_codex_call(script)]), "s1", "codex")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == 1
    assert prs[0]["evidence"].startswith("gh pr edit 6248"), prs[0]["evidence"]
    assert "exec_command" not in prs[0]["evidence"]
    assert "max_output_tokens" not in prs[0]["evidence"]


def test_evidence_ends_on_the_command_not_on_its_keyword_arguments():
    """Live: ``gh pr ready 2562 --repo nordwind/nano",workdir:"/tmp",max_output...}))``."""
    script = (r'tools.exec_command({cmd:\"gh pr ready 2562 --repo nordwind/repo\",'
              r'workdir:\"/tmp\",max_output_tokens:1400})')
    out = attribution.extract_session_delivery(
        _newest_first([_codex_call(script)]), "s1", "codex")
    evidence = [a["evidence"] for a in out["artifacts"] if a["kind"] == "pr"][0]
    assert evidence == "gh pr ready 2562 --repo nordwind/repo", evidence


def test_evidence_opens_on_a_whole_word():
    """Live: a row opened ``026-09-25 (later run): `gh pr merge 6160 ...``.

    The run-up is a fixed number of characters, so it lands wherever it
    lands. Finishing the word it was cut inside costs a few characters and
    is the difference between a date and a typo.
    """
    text = ("Note from 2026-09-25 (later run): `gh pr merge 6160 --squash` did "
            "go through, but the classifier then flagged it as Merge Without "
            "Review and the reviewer had to reopen the question from scratch.")
    out = attribution.extract_session_delivery(
        _newest_first([_call(text)]), "s1")
    evidence = [a["evidence"] for a in out["artifacts"] if a["kind"] == "pr"][0]
    assert "2026-09-25" in evidence, evidence
    assert not evidence.startswith("026-"), evidence


def test_evidence_keeps_the_bracket_of_a_markdown_link():
    """Live: ``[vivekchand/clawmetry#6186](...`` lost its opening bracket.

    Edge punctuation is debris when the cut landed mid-structure and is
    meaningful once the cut is snapped to a word boundary. Only the right
    edge is still stripped.
    """
    text = ("Status: [vivekchand/clawmetry#6186]"
            "(https://github.com/vivekchand/clawmetry/pull/6186) fixes the "
            "approval gate that kept reporting a held tool after approval "
            "was turned off out of band, which nobody could reproduce.")
    out = attribution.extract_session_delivery(
        _newest_first([_call(text)]), "s1")
    evidence = [a["evidence"] for a in out["artifacts"] if a["kind"] == "pr"][0]
    assert evidence.startswith("[vivekchand/clawmetry#6186]"), evidence


def test_evidence_decodes_an_escape_that_survived_serialization():
    """Live: 17 rows read ``\\u2014 all green`` instead of ``— all green``."""
    assert attribution._readable(r"and #6314 — all green") == \
        "and #6314 — all green"
    # A decoded control character would break the cell it lands in.
    assert attribution._readable(r"tab\u0009here") == "tab here"


@pytest.mark.parametrize("ref", [
    "gh pr edit 6248 --repo nordwind/repo",
    "https://github.com/nordwind/repo/pull/6248",
])
def test_the_reference_always_survives_the_tightening(ref):
    """Whatever the snippet rules do, the row must still show its claim."""
    text = f'{{"role":"tool","content":"wrapped {ref} tail","x":1}}'
    out = attribution.extract_session_delivery(
        _newest_first([_call(text)]), "s1")
    for a in out["artifacts"]:
        if a["kind"] == "pr":
            assert a["ref"] in a["evidence"], a


# ── One pull request is one row, and one row's money ────────────────────────

def test_a_pull_request_named_both_ways_is_one_row_across_two_repos():
    """The sole-repo fold only fires when the session touched ONE repo.

    A session that works across repositories kept both keys — ``#6283`` and
    ``vivekchand/clawmetry#6283`` — and emitted a row for each: the tab showed
    81 pull requests twice, once with the repository and once with the cell
    blank. A bare number folds into the one qualified row that shares it.
    """
    events = [
        _call("gh pr checks 6283"),
        _call("gh pr merge 6283 --repo nordwind/repo"),
        _call("gh pr view 2564 --repo sudwind/cloud"),
        _usage(9.0),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert sorted(a["ref"] for a in prs) == ["2564", "6283"], prs
    row = [a for a in prs if a["ref"] == "6283"][0]
    assert row["repo"] == "nordwind/repo"
    assert row["confidence"] < 1.0, "part of the row rests on an inference"


def test_one_pull_request_is_not_charged_twice():
    """The $327.92 bug.

    Cost was looked up as ``per_pr[repo#pr]`` with a fallback to
    ``per_pr[#pr]``. The fallback fired for the qualified row while the bare
    row was also emitted, so both claimed the same segment and the node's
    attributed total over-reported by $327.92 — 11% of it.
    """
    # The shape that does it, taken from session af5b37e6: the bare mention
    # is the one with money behind it, and the repository is learned from a
    # URL that no cost follows. ``per_pr`` then holds ``#6283`` and NOT
    # ``nordwind/repo#6283``, so the qualified row took the fallback and the bare
    # row took the same segment. Two repositories in the session, so the
    # sole-repo fold cannot hide it.
    events = [
        _call("gh pr checks 6283", ts="2026-10-15T10:00:00Z"),
        _usage(4.0, ts="2026-10-15T10:00:01Z"),
        _call("open https://github.com/nordwind/repo/pull/6283",
              ts="2026-10-15T10:00:02Z"),
        _call("gh pr view 2564 --repo sudwind/cloud", ts="2026-10-15T10:00:03Z"),
        _usage(5.0, ts="2026-10-15T10:00:04Z"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    charged = sum(a["cost_usd"] or 0 for a in out["artifacts"]
                  if a["kind"] == "pr")
    assert charged + out["unattributed_usd"] == pytest.approx(
        out["total_usd"]), out
    assert charged == pytest.approx(9.0)


def test_no_segment_of_the_split_is_reported_nowhere():
    """The $5.00 bug, the same root cause pointing the other way.

    Where the two keys WERE folded into one row only one of them was read,
    so the other segment's money appeared neither against a pull request nor
    in the remainder. One live session lost $5.00 of $11.95 that way.
    """
    # Explicit, increasing timestamps: with the helpers' defaults all four
    # events share two instants, ``chronological`` is free to put both calls
    # before both usages, and the two segments collapse into one. The test
    # then passed against the unfixed code for the wrong reason.
    events = [
        _call("gh pr view 6401", ts="2026-10-15T10:00:00Z"),   # segment one
        _usage(5.0, ts="2026-10-15T10:00:01Z"),
        _call("gh pr edit 6401 --repo nordwind/repo",
              ts="2026-10-15T10:00:02Z"),                      # segment two
        _usage(0.36, ts="2026-10-15T10:00:03Z"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == 1, prs
    assert prs[0]["cost_usd"] == pytest.approx(5.36), prs
    assert out["unattributed_usd"] == pytest.approx(0.0)


def test_a_bare_number_is_not_folded_when_two_repos_share_it():
    """Two repositories really can both have a #302. A wrong repository is
    worse than a blank one, so the bare row is left as it is and its money
    stays on it.

    A preservation guard, not a reproduction: this held before the fold
    existed and has to keep holding now that it does.
    """
    events = [
        _call("gh pr view 302 --repo nordwind/repo", ts="2026-10-15T10:00:00Z"),
        _usage(1.0, ts="2026-10-15T10:00:01Z"),
        _call("gh pr view 302 --repo nordwind/pro", ts="2026-10-15T10:00:02Z"),
        _usage(1.0, ts="2026-10-15T10:00:03Z"),
        _call("gh pr checks 302", ts="2026-10-15T10:00:04Z"),
        _usage(1.0, ts="2026-10-15T10:00:05Z"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert sorted(a["repo"] for a in prs) == ["", "nordwind/pro", "nordwind/repo"], prs
    charged = sum(a["cost_usd"] or 0 for a in prs)
    assert charged + out["unattributed_usd"] == pytest.approx(out["total_usd"])


def test_the_remainder_absorbs_a_segment_that_cannot_be_placed():
    """Under-claiming is honest; double-counting is not.

    ``MAX_PRS_PER_SESSION`` can drop the row a segment belonged to. The money
    then has to appear as the remainder, because the invariant the tab rests
    on is that the parts plus the remainder are the session's own cost.
    """
    charged, leftover = attribution._distribute_pr_cost(
        {"nordwind/repo#1": 2.0, "halcyon/repo#9": 3.0}, {("nordwind/repo", "1"): {}})
    assert charged == {("nordwind/repo", "1"): 2.0}
    assert leftover == pytest.approx(3.0)


# ── An artifact must be a real artifact ─────────────────────────────────────

@pytest.mark.parametrize("url", [
    "https://docs.github.com/site-policy/github-terms/github-terms-of-service",
    "https://docs.github.com/en/rest/branches/branches",
    "https://github.com/settings/personal-access-tokens/new",
    "https://gist.github.com/someone/abcdef123456",
])
def test_these_github_urls_are_not_repositories(url):
    """Live: the repo list carried ``site-policy/github-terms``,
    ``rest/branches``, ``repos/vivekchand`` and ``settings/personal-access-
    tokens``. A subdomain is not github.com and a reserved page is not an
    account, so each of those named a repository that does not exist."""
    out = attribution.extract_session_delivery(
        _newest_first([_call(f"open {url}")]), "s1")
    assert [a for a in out["artifacts"] if a["kind"] == "repo"] == []


def test_the_github_api_url_does_name_the_repository():
    """``api.github.com/repos/nordwind/repo`` is the one subdomain that does."""
    out = attribution.extract_session_delivery(
        _newest_first([_call("curl https://api.github.com/repos/nordwind/repo/pulls")]),
        "s1")
    repos = [a["ref"] for a in out["artifacts"] if a["kind"] == "repo"]
    assert repos == ["nordwind/repo"]


@pytest.mark.parametrize("candidate", [
    "<tr><td>Vapi</td><td>Voice",          # an HTML edit, not a file
    "defer></script>",
    r"\[.*?\]",                            # a regex literal
    "homepage</td><td>Your",
    "--short",                             # a flag
    "/*",                                  # a glob
    "/admin/*",
    "src/**/*.ts",
    "notes",                               # no directory and no extension
    "",
])
def test_these_are_not_files_the_session_wrote(candidate):
    """Live: 52% of the file rows on the shipped tab were not paths.

    The step normalizer hands back whatever sat next to the match, and the
    tab printed it as a file the session authored. A dropped row is the
    honest failure; a fabricated filename teaches the reader that the table
    invents things.
    """
    assert attribution._clean_path(candidate) == ""


@pytest.mark.parametrize("candidate,expected", [
    (r'.claude/sf_client.py\",\"max_output_tokens\":10000}));',
     ".claude/sf_client.py"),
    ("clawmetry/templates/tabs/improve.html",
     "clawmetry/templates/tabs/improve.html"),
    ("Makefile", "Makefile"),              # conventional, no extension
    ("README.md", "README.md"),
    ("routes/attribution.py", "routes/attribution.py"),
])
def test_a_real_path_survives_a_serialized_payload_tail(candidate, expected):
    assert attribution._clean_path(candidate) == expected


def test_the_rules_version_moved_so_existing_rows_are_refiled():
    """These changes alter what is stored for a session that may never grow
    again. The watermark only notices a session whose event count CHANGED, so
    a semantics fix that does not move ``RULES_VERSION`` reaches no existing
    install. Three was the shipped value."""
    assert int(attribution.RULES_VERSION) >= 4


# ── A branch must be a branch ───────────────────────────────────────────────
#
# The five most common "branches" on the live tab were `refs/tags`, `from`,
# `feat`, `2` and `release`: a tag prefix, two words of prose, a shell
# redirect and a documentation placeholder. Every branch on that node that
# was real carried a `/`.

@pytest.mark.parametrize("command", [
    "git push origin refs/tags/v1.2.3",          # a tag is not a branch
    "git push -q 2>&1 | tail -3",                # `2` was a shell redirect
    "git checkout -b release/<slug> origin/main",  # a docs placeholder
    "git checkout -B feat/<slug> origin/main",
    "the step runs `git push -f origin` from inside the cloud checkout",
])
def test_these_are_not_branches(command):
    out = attribution.extract_session_delivery(
        _newest_first([_call(command)]), "s1")
    assert [a for a in out["artifacts"] if a["kind"] == "branch"] == []


@pytest.mark.parametrize("command,expected", [
    ("git push -f origin feat/so101-physical-ai", "feat/so101-physical-ai"),
    ("git checkout -b fix/home-session-activity", "fix/home-session-activity"),
    ("git push origin HEAD:auto/pin-clawmetry-0.12.906",
     "auto/pin-clawmetry-0.12.906"),
    ("git push origin refs/heads/feat/x", "feat/x"),
    ("git push origin hotfix-login", "hotfix-login"),
])
def test_a_real_branch_is_still_recorded(command, expected):
    out = attribution.extract_session_delivery(
        _newest_first([_call(command)]), "s1")
    assert [a["ref"] for a in out["artifacts"]
            if a["kind"] == "branch"] == [expected]


@pytest.mark.parametrize("candidate", [
    "origin/main",                 # a git ref, listed as a file 18 times
    "vivekchand/clawmetry-cloud",  # a repository, listed as a file 10 times
    "/search",                     # a URL path
    "/heading",                    # an ARIA role out of a selector
    "s/last",                      # a sed expression
])
def test_an_extensionless_name_needs_to_be_a_rooted_path(candidate):
    assert attribution._clean_path(candidate) == ""


@pytest.mark.parametrize("candidate", [
    "/Users/vivek/projects/clawmetry",
    "/dev/null",
    "../clawmetry-cloud",
    "./scripts/build.sh",
])
def test_a_rooted_path_without_an_extension_is_still_a_path(candidate):
    assert attribution._clean_path(candidate) == candidate


# ── Evidence is the work, not the markup around it ──────────────────────────

def test_an_anchor_becomes_its_href_not_a_deletion():
    """Live: four rows read ``· <a href="…/pull/6420">Correction release</a>``.

    Stripping tags alone would have removed the href, and the href is where
    the pull-request number lives — the row would have lost the very
    reference it is evidence for. The anchor is replaced BY its target.
    """
    out = attribution._readable(
        '&middot; <a href="https://github.com/nordwind/repo/pull/6420">Correction'
        ' release</a></p>')
    assert "https://github.com/nordwind/repo/pull/6420" in out
    assert "<" not in out and ">" not in out
    assert "Correction release" in out, "the link text is context, keep it"
    assert "&middot;" not in out and "middot;" not in out


def test_a_shell_command_is_not_mistaken_for_markup():
    """`&&` and `2>&1` are not HTML, and must come through untouched."""
    cmd = "gh pr merge 6388 --repo nordwind/repo --squash && echo ok 2>&1"
    assert attribution._readable(cmd) == cmd


def test_markup_evidence_still_carries_its_reference():
    """The invariant, applied to the one shape that used to break it."""
    text = ('<p>· <a href="https://github.com/nordwind/repo/pull/6420">Correction'
            ' release</a> shipped</p>')
    out = attribution.extract_session_delivery(
        _newest_first([_call(text)]), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == 1 and prs[0]["ref"] == "6420"
    assert "6420" in prs[0]["evidence"], prs[0]["evidence"]


# ── A name cut short by the tool that printed it is not a repository ────────

def test_a_repo_name_cut_short_is_dropped_for_the_whole_one():
    """Live: `vivekchand/c` and `vivekchand/clawm` were repositories on the tab.

    The text had already been cut mid-token before we saw it
    (`gh pr view 6354 --repo vivekchand/c` then a line break), so nothing in
    the command distinguishes a complete value from a truncated one. The rest
    of the session does: a longer name under the same owner that this is a
    prefix of.
    """
    events = [
        _call("gh pr view 6354 --repo nordwind/c"),
        _call("gh pr view 6354 --repo nordwind/clawmetry-cloud"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    repos = sorted(a["ref"] for a in out["artifacts"] if a["kind"] == "repo")
    assert repos == ["nordwind/clawmetry-cloud"], repos


def test_a_different_owner_is_never_a_truncation():
    """Only a longer name under the SAME owner can be the whole of this one."""
    events = [
        _call("gh pr view 1 --repo kestrel/condor"),
        _call("gh pr view 2 --repo merlin/clawmetry"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    repos = sorted(a["ref"] for a in out["artifacts"] if a["kind"] == "repo")
    assert repos == ["kestrel/condor", "merlin/clawmetry"], repos


def test_unrelated_repositories_both_survive():
    """The rule must not thin out a session that touched several repos."""
    events = [
        _call("gh pr view 1 --repo nordwind/repo"),
        _call("gh pr view 2 --repo nordwind/cloud"),
        _call("gh pr view 3 --repo nordwind/pro"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    repos = sorted(a["ref"] for a in out["artifacts"] if a["kind"] == "repo")
    assert repos == ["nordwind/cloud", "nordwind/pro", "nordwind/repo"], repos


def test_the_rules_version_moved_again():
    """Both changes alter stored rows, so existing sessions must refile."""
    assert int(attribution.RULES_VERSION) >= 6


# ── A cut-short name reaches a pull request by its own route ────────────────

def test_a_pull_request_is_not_filed_under_a_cut_short_repository():
    """The half #6424 missed, found by re-reading the live tab after it shipped.

    `_drop_truncated_repos` cleans the repository bucket, but a pull request
    carries its OWN repository string, resolved from the `--repo` flag in its
    own command. So `vivekchand/clawm` vanished from Repositories and stayed
    on Pull requests. Repairing beats dropping here: the whole name is known,
    so the row is real and only its label was cut.
    """
    events = [
        _call("gh pr edit 6248 --repo nordwind/clawm"),
        _call("gh pr view 6248 --repo nordwind/clawmetry"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == 1, prs
    assert prs[0]["repo"] == "nordwind/clawmetry"


def test_an_ambiguous_cut_name_loses_the_repository_not_the_row():
    """Several known names extend it, so no single one can be chosen.

    This used to leave the cut name in place, and six live rows went on
    reading ``vivekchand/c`` -- a repository nobody has. The number is the
    reference that matters, so the row survives and the LABEL goes.
    """
    events = [
        _call("gh pr view 1 --repo nordwind/c"),
        _call("gh pr view 2 --repo nordwind/clawmetry"),
        _call("gh pr view 3 --repo nordwind/cloud"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = {a["ref"]: a["repo"] for a in out["artifacts"] if a["kind"] == "pr"}
    assert prs["1"] == "", f"a cut name must not be shown: {prs}"
    assert prs["2"] == "nordwind/clawmetry"
    assert prs["3"] == "nordwind/cloud"


def test_the_length_cut_does_not_leave_half_a_tag():
    """The cut itself can create markup.

    One live row read `· https://…/pull/6420 Correction release · <a href`:
    the anchor was unwrapped correctly, and then trimming to the cell length
    landed inside a SECOND one. No tag pattern can match it, because the
    closing `>` is on the other side of the cut.
    """
    out = attribution._clean_evidence(
        "· https://github.com/nordwind/repo/pull/6420 Correction release · <a href")
    assert out == "· https://github.com/nordwind/repo/pull/6420 Correction release"
    assert "<" not in out


def test_a_sibling_repository_is_not_a_truncation_of_its_shorter_name():
    """The regression that cost $348.74.

    ``clawmetry`` is a prefix of ``clawmetry-cloud``, so the prefix rule read
    the busiest repository on the node as a cut-short form of its own sibling
    and DELETED it -- from 49 sessions' Repositories lists. What separates the
    two cases is where the longer name resumes: ``clawm`` -> ``clawmetry``
    resumes at "e", inside a word, which is a cut; ``clawmetry`` ->
    ``clawmetry-cloud`` resumes at "-", a token boundary, which is a second
    repository.
    """
    events = [
        _call("gh pr view 1 --repo nordwind/clawmetry"),
        _call("gh pr view 2 --repo nordwind/clawmetry-cloud"),
        _call("gh pr view 3 --repo nordwind/clawmetry-pro"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    repos = sorted(a["ref"] for a in out["artifacts"] if a["kind"] == "repo")
    assert repos == ["nordwind/clawmetry", "nordwind/clawmetry-cloud",
                     "nordwind/clawmetry-pro"], repos


def test_a_pull_request_keeps_the_repository_its_own_command_named():
    """71 live rows read ``clawmetry-cloud`` while their own evidence read
    ``--repo vivekchand/clawmetry``. $348.74 was filed against the wrong
    repository -- worse than a blank cell, because it reads as an answer.
    """
    events = [
        _call("gh pr merge 6426 --repo nordwind/clawmetry --squash"),
        _call("gh pr view 2 --repo nordwind/clawmetry-cloud"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    row = next(a for a in out["artifacts"]
               if a["kind"] == "pr" and a["ref"] == "6426")
    assert row["repo"] == "nordwind/clawmetry", row


def test_a_genuine_cut_is_still_repaired():
    """The separator rule must not switch the original repair off."""
    events = [
        _call("gh pr edit 6248 --repo nordwind/clawm"),
        _call("gh pr view 6248 --repo nordwind/clawmetry"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == 1, prs
    assert prs[0]["repo"] == "nordwind/clawmetry"


def test_a_documentation_placeholder_is_not_a_repository():
    """``own/repo`` carried 14 pull-request rows and $11.85 on the live node.

    These come out of help text, docs and this repository's OWN test
    fixtures, which the agent reads and runs while it works. They are
    well-formed, so every shape test passes them; the OWNER half is what
    gives them away. No real account is called ``owner`` or ``example``,
    while plenty of real repositories are named ``repo`` or ``docs``.
    """
    for name in ("owner/repo", "OWNER/REPO", "your-org/service",
                 "example/thing", "octocat/Hello-World", "foo/bar",
                 "me/project", "username/dotfiles"):
        assert attribution._clean_repo(name) == "", name
    # The owner half only: a real repository NAMED "repo" survives.
    assert attribution._clean_repo("nordwind/repo") == "nordwind/repo"
    assert attribution._clean_repo("stripe/ai") == "stripe/ai"
    assert attribution._clean_repo("npm/cli") == "npm/cli"


def test_a_placeholder_command_is_a_specimen_not_a_delivery():
    """Blanking only the repository was not enough.

    The number came out of the same fictional command, and leaving it behind
    let the fold dress it in a real repository: a line of this repository's
    OWN test source became a $0.27 pull request "#2" in
    ``vivekchand/clawmetry-pro``. There is no pull request #2.
    """
    events = [_call('_call("gh pr edit 2 --repo owner/repo")'), _usage(4.0)]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    assert [a for a in out["artifacts"] if a["kind"] == "pr"] == []
    assert [a for a in out["artifacts"] if a["kind"] == "repo"] == []
    # The money has to go somewhere, and nowhere is the remainder.
    assert out["unattributed_usd"] == 4.0


def test_a_git_config_key_is_not_a_repository_name():
    """``actions/checkout`` writes a config key on every CI run.

    A build log in the stream carries
    ``GIT_CONFIG_KEY_0='http.https://github.com/OWNER/NAME.extraheader'``, and
    the live tab listed ``vivekchand/clawmetry-pro.extraheader`` and
    ``vivekchand/clawmetry-pro.git.extraheader`` as two repositories. The
    repository inside the key is real, so the variable is removed and the
    sighting is kept rather than dropped.
    """
    for key in ("+ GIT_CONFIG_KEY_0='http.https://github.com/"
                "nordwind/clawmetry-pro.extraheader",
                "+ GIT_CONFIG_KEY_0='http.https://github.com/"
                "nordwind/clawmetry-pro.git.extraheader"):
        out = attribution.extract_session_delivery(_newest_first([
            {"event_type": "tool_result", "ts": "2026-10-15T10:00:00Z",
             "data": {"content": key}}]), "s1")
        assert [a["ref"] for a in out["artifacts"] if a["kind"] == "repo"] \
            == ["nordwind/clawmetry-pro"], key


def test_only_gits_own_word_is_stripped_from_a_name():
    """A vocabulary of one, deliberately.

    git documents many variables for ``http.<url>.<variable>``, but
    ``version``, ``proxy`` and ``sslverify`` are words a real repository name
    could end with. Rewriting ``acmecorp/app.version`` to ``acmecorp/app``
    would INVENT a repository, which is the failure this tab has been fixed
    four times to avoid.
    """
    assert attribution._clean_repo("acmecorp/thing.extraheader") \
        == "acmecorp/thing"
    for kept in ("acmecorp/app.version", "acmecorp/mitm.proxy",
                 "acmecorp/app.sslverify", "acmecorp/tool.useragent"):
        assert attribution._clean_repo(kept) == kept, kept


def test_a_github_product_page_is_not_a_repository():
    """``github.com/resources/insights/<slug>`` is an article GitHub
    publishes, and it reached the live tab as ``resources/insights``."""
    for url in ("https://github.com/resources/insights/2026-pricing-changes",
                "https://github.com/solutions/industries/healthcare",
                "https://github.com/education/students"):
        out = attribution.extract_session_delivery(_newest_first([
            {"event_type": "tool_result", "ts": "2026-10-15T10:00:00Z",
             "data": {"content": url}}]), "s1")
        assert [a for a in out["artifacts"] if a["kind"] == "repo"] == [], url
    # An owner that merely looks like a product word is still an owner.
    out = attribution.extract_session_delivery(_newest_first([
        {"event_type": "tool_result", "ts": "2026-10-15T10:00:00Z",
         "data": {"content": "https://github.com/nordwind/resources"}}]), "s1")
    assert [a["ref"] for a in out["artifacts"] if a["kind"] == "repo"] \
        == ["nordwind/resources"]


def test_a_documentation_example_list_is_not_a_repository():
    """``openai/openai`` reached the live tab in two sessions.

    The sighting is a documentation line listing the URL shapes a tool
    accepts. There is no ``openai/openai`` account, and the damage was not
    only the phantom row: in one of the two sessions it became a SECOND
    repository, so the fold could no longer tell which repository pull
    request #6351 belonged to, and a real $10.89 row lost its label.
    """
    doc = ("URL. Examples: `https://github.com/openai/openai/pulls/123`, "
           "`https://api.github.com/repos/openai/openai`, "
           "`https://github.example.com/api/v3/repos/octo/repo`.")
    out = attribution.extract_session_delivery(_newest_first([
        {"event_type": "tool_result", "ts": "2026-10-15T10:00:00Z",
         "data": {"content": doc}}]), "s1")
    assert [a for a in out["artifacts"] if a["kind"] == "repo"] == []
    assert [a for a in out["artifacts"] if a["kind"] == "pr"] == []


@pytest.mark.parametrize("text, kept", [
    # The word is in the repository's OWN name.
    ("- Working examples: [tavus-examples](https://github.com/"
     "Tavus-Engineering/tavus-examples/tree/main/examples#readme)",
     "Tavus-Engineering/tavus-examples"),
    # "Example" introduces the skill, not the repository.
    ("- Example (experimental skill): `scripts/install-skill-from-github.py "
     "--repo openai/skills --path skills/.experimental/`",
     "openai/skills"),
    # Sighted only because a PATH ends ".env.example".
    ("OpenBot/.env.example at main \u00b7 CopilotKit/OpenBot \u00b7 GitHub "
     "(https://github.com/CopilotKit/OpenBot/blob/main/.env.example)",
     "CopilotKit/OpenBot"),
    ("OpenTag/.env.example at main \u00b7 CopilotKit/OpenTag \u00b7 GitHub "
     "(https://github.com/CopilotKit/OpenTag/blob/main/.env.example)",
     "CopilotKit/OpenTag"),
])
def test_the_word_example_alone_does_not_delete_a_real_repository(text, kept):
    """The half of this filter that matters is what it does NOT remove.

    Measured over the 1120 repository and pull-request rows on a live node,
    a rule keyed on the word ``example`` alone would have deleted these four
    REAL repositories while removing two phantoms. That is why a reserved
    documentation domain is required on the same line as a second signal.
    """
    out = attribution.extract_session_delivery(_newest_first([
        {"event_type": "tool_result", "ts": "2026-10-15T10:00:00Z",
         "data": {"content": text}}]), "s1")
    assert [a["ref"] for a in out["artifacts"] if a["kind"] == "repo"] == [kept]


def test_a_reserved_domain_alone_does_not_delete_a_real_repository():
    """``example.com`` CONTAINS the word ``example``.

    Left alone the reserved domain answers both halves by itself and the
    two-signal rule collapses into one, so this line lost a real repository
    until the domains were masked out before looking for an announcement.
    """
    out = attribution.extract_session_delivery(_newest_first([
        {"event_type": "tool_result", "ts": "2026-10-15T10:00:00Z",
         "data": {"content": "mirror at example.com of "
                             "https://github.com/nordwind/repo"}}]), "s1")
    assert [a["ref"] for a in out["artifacts"] if a["kind"] == "repo"] \
        == ["nordwind/repo"]


def test_an_example_elsewhere_cannot_delete_a_real_repository():
    """Only the match's own line is read, as for a pytest node id. A session
    that pastes a documentation example and then does real work keeps the
    real work."""
    text = ("Examples: `https://github.example.com/api/v3/repos/octo/repo`\n"
            "git remote add origin https://github.com/nordwind/repo")
    out = attribution.extract_session_delivery(_newest_first([
        {"event_type": "tool_result", "ts": "2026-10-15T10:00:00Z",
         "data": {"content": text}}]), "s1")
    assert [a["ref"] for a in out["artifacts"] if a["kind"] == "repo"] \
        == ["nordwind/repo"]


def test_an_announcement_after_the_match_does_not_govern_it():
    """A sentence cannot illustrate something it has not reached yet."""
    out = attribution.extract_session_delivery(_newest_first([
        {"event_type": "tool_result", "ts": "2026-10-15T10:00:00Z",
         "data": {"content": "https://github.com/nordwind/repo -- for "
                             "example.com style hosts see the docs"}}]), "s1")
    assert [a["ref"] for a in out["artifacts"] if a["kind"] == "repo"] \
        == ["nordwind/repo"]


def test_a_phantom_repository_no_longer_blocks_a_real_pull_request():
    """The live payoff: #6351 was filed with a BLANK repository.

    The session named one real repository and one phantom out of a
    documentation example, and the fold correctly refuses to guess between
    two candidates. Removing the phantom leaves one, so the row recovers its
    label -- and the money does not move, because the split never depended
    on the name.
    """
    doc = ("URL. Examples: `https://github.com/openai/openai/pulls/123`, "
           "`https://github.example.com/api/v3/repos/octo/repo`.")
    events = [
        _call("git remote -v  # https://github.com/nordwind/clawmetry"),
        {"event_type": "tool_result", "ts": "2026-10-15T10:00:01Z",
         "data": {"content": doc}},
        _call("gh pr view 6351 --json title,body", ts="2026-10-15T10:00:02Z"),
        _usage(10.0, ts="2026-10-15T10:00:03Z"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == 1, prs
    assert prs[0]["ref"] == "6351"
    assert prs[0]["repo"] == "nordwind/clawmetry"
    repos = [a["ref"] for a in out["artifacts"] if a["kind"] == "repo"]
    assert repos == ["nordwind/clawmetry"], repos


def test_a_number_the_session_also_names_for_real_keeps_its_row():
    """The specimen rule must not take a real delivery with it.

    A number sighted in a placeholder command AND in a real one is real; the
    real sighting arrives by its own route and is untouched.
    """
    events = [
        _call("gh pr edit 6407 --repo owner/repo"),
        _call("gh pr merge 6407 --repo nordwind/clawmetry --squash"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == 1, prs
    assert prs[0]["repo"] == "nordwind/clawmetry"
    assert "owner/repo" not in (prs[0]["evidence"] or "")


def test_evidence_does_not_name_a_repository_the_row_is_not_filed_under():
    """Five live rows were filed correctly and evidenced by the name that had
    just been rejected: ``--repo vivekchand/c`` under a row reading
    ``vivekchand/clawmetry``. The column exists to be checked against the
    row, so it has to agree with it.
    """
    events = [
        _call("gh pr edit 6211 --repo nordwind/c"),
        _call("gh pr view 6211 --repo nordwind/clawmetry"),
        _call("gh pr view 9 --repo nordwind/cloud"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    row = next(a for a in out["artifacts"]
               if a["kind"] == "pr" and a["ref"] == "6211")
    assert row["repo"] == "nordwind/clawmetry", row
    assert not attribution._evidence_contradicts(row["evidence"] or "",
                                                 row["repo"]), row["evidence"]


def test_a_trailing_full_stop_is_not_part_of_the_name():
    """``vivekchand/clawmetry.`` reached the live tab as its own repository.

    GitHub rejects a name ending in ".", so this is a sentence's full stop
    glued on by the prose around it -- and left alone it SPLITS one real
    repository across two rows.
    """
    assert attribution._clean_repo("nordwind/clawmetry.") == "nordwind/clawmetry"
    assert attribution._clean_repo("julienXX/terminal-notifier.") == \
        "julienXX/terminal-notifier"
    events = [
        _call("gh pr view 1 --repo nordwind/clawmetry"),
        _call("cloned from github.com/nordwind/clawmetry."),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    repos = sorted(a["ref"] for a in out["artifacts"] if a["kind"] == "repo")
    assert repos == ["nordwind/clawmetry"], repos


def test_an_ellipsis_name_is_not_a_repository():
    """``mitre-atlas/atlas-...e`` -- cut in the MIDDLE by whatever rendered
    it, so there is no name here to recover."""
    assert attribution._clean_repo("mitre-atlas/atlas-...e") == ""
    assert attribution._clean_repo("nordwind/claw\u2026try") == ""


def test_a_two_character_pair_is_not_a_repository():
    """``o/n``, ``a/b``, ``x/y``: a shape nobody ships real work under."""
    for name in ("o/n", "a/b", "x/y"):
        assert attribution._clean_repo(name) == "", name
    # Three characters on either side is a real possibility, so it stands.
    assert attribution._clean_repo("npm/cli") == "npm/cli"


def test_placeholder_rows_do_not_block_the_bare_fold():
    """Live #6275 showed FIVE rows for one pull request.

    Not a fold bug: three of the five were placeholder repositories, which
    made the bare row's sibling set ambiguous, so the fold correctly refused
    to guess. Remove the invented rows and the real fold happens.
    """
    events = [
        _call("gh pr checks 6275"),
        _call("gh pr edit 6275 --repo owner/repo"),
        _call("gh pr edit 6275 --repo own/repo"),
        _call("gh pr merge 6275 --repo nordwind/clawmetry"),
        _usage(6.0),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    prs = [a for a in out["artifacts"] if a["kind"] == "pr"]
    assert len(prs) == 1, [(p["ref"], p["repo"]) for p in prs]
    assert prs[0]["repo"] == "nordwind/clawmetry"


def test_one_repository_spelled_two_ways_is_one_row():
    """GitHub is case-insensitive, and the live tab listed
    ``NVIDIA/OpenShell`` beside ``nvidia/openshell`` in the same session.

    The spelling with the most sightings wins, so the row reads the way its
    author typed it rather than however the loop happened to run.
    """
    events = [
        _call("git clone https://github.com/nvidia/openshell"),
        _call("gh pr view 4 --repo NVIDIA/OpenShell"),
        _call("gh pr view 5 --repo NVIDIA/OpenShell"),
        _call("gh pr view 6 --repo NVIDIA/OpenShell"),
    ]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    repos = [a["ref"] for a in out["artifacts"] if a["kind"] == "repo"]
    assert repos == ["NVIDIA/OpenShell"], repos
    # Both halves of the tab have to agree about the name.
    pr_repos = {a["repo"] for a in out["artifacts"] if a["kind"] == "pr"}
    assert pr_repos == {"NVIDIA/OpenShell"}, pr_repos


def test_githubs_own_service_namespaces_are_not_accounts():
    """``user-attachments/assets`` is the image CDN path and
    ``assets-cdn/worker`` is GitHub's service worker. Both look exactly like
    an account in a URL and both reached the live tab as repositories."""
    for name in ("user-attachments/assets", "assets-cdn/worker",
                 "codeload/thing"):
        assert attribution._clean_repo(name) == "", name
    out = attribution.extract_session_delivery(_newest_first([
        _call("curl https://github.com/user-attachments/assets/abc123")]), "s1")
    assert [a for a in out["artifacts"] if a["kind"] == "repo"] == []


def test_a_parametrised_test_id_is_not_a_branch():
    """Four live rows read ``feat/x-feat/x`` and
    ``fix/home-session-activity-fix/home-session-activity``.

    A pytest node id repeats its parameter after the test name, so the doubled
    name is the id's own shape. The agent runs this repository's tests all day,
    so their output is in the stream it reads.
    """
    events = [_call(
        "tests/test_delivery_attribution.py::test_a_real_branch_is_still_recorded"
        "[git push origin hotfix-login-hotfix-login] PASSED [100%]")]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    assert [a for a in out["artifacts"] if a["kind"] == "branch"] == []


def test_a_real_command_beside_test_output_is_still_read():
    """Only the match's OWN line disqualifies it, so a node id elsewhere in
    the snippet cannot delete a branch the session really pushed."""
    events = [_call("tests/test_x.py::test_y[git push origin specimen] PASSED\n"
                    "git push origin feat/real-work")]
    out = attribution.extract_session_delivery(_newest_first(events), "s1")
    branches = sorted(a["ref"] for a in out["artifacts"] if a["kind"] == "branch")
    assert branches == ["feat/real-work"], branches


def test_a_json_escaped_newline_still_ends_a_line():
    """A tool_result's text is read out of the event's JSON, where a newline
    is the two characters ``\\n``.

    Splitting on the real character alone made a whole multi-line tool
    result ONE line, so a documentation example or a pytest node id at the
    top of a long output reached down and disqualified a real sighting named
    further on. The tool_call path never showed this because a command
    arrives verbatim.
    """
    escaped = 'Examples: github.example.com/x\\ngit remote add nordwind/repo'
    lo, hi = attribution._line_bounds(escaped, escaped.index("nordwind"))
    assert escaped[lo:hi] == "git remote add nordwind/repo"

    real = "Examples: github.example.com/x\ngit remote add nordwind/repo"
    lo, hi = attribution._line_bounds(real, real.index("nordwind"))
    assert real[lo:hi] == "git remote add nordwind/repo"

    # A text with no break of either kind is one line, from its very start.
    assert attribution._line_bounds("no breaks here", 5) == (0, 14)


def test_rules_version_moved_to_eight():
    assert int(attribution.RULES_VERSION) >= 8


def test_two_sessions_spelling_one_repository_differently_are_one_row(store):
    """``_fold_repo_case`` folds WITHIN a session; rows must fold across them.

    The live tab listed ``ClawMetry/clawmetry-pro`` beside
    ``clawmetry/clawmetry-pro``: one repository, two rows, because the two
    spellings came from two different sessions and the read query grouped on
    the exact text. GitHub treats an owner and a name case-insensitively, so
    the spelling the node's sessions used most is the one to show.
    """
    _attribute(store, "s1", [_call("gh pr edit 7 --repo nordwind/repo"), _usage(3.0)])
    _attribute(store, "s2", [_call("gh pr edit 7 --repo nordwind/repo"), _usage(4.0)])
    _attribute(store, "s3", [_call("gh pr edit 7 --repo NordWind/Repo"), _usage(5.0)])
    rows = store.query_delivery(kind="pr")["rows"]
    assert len(rows) == 1, [(r["repo"], r["ref"], r["sessions"]) for r in rows]
    assert rows[0]["repo"] == "nordwind/repo"
    assert rows[0]["sessions"] == 3
    assert rows[0]["cost_usd"] == 12.0


def test_a_branch_keeps_its_own_case(store):
    """git is case-sensitive about refs, so two branches stay two branches.

    The guard on the fix above: lowercasing the whole key would merge
    ``Feature/Login`` into ``feature/login`` and claim work on a branch that
    does not exist.
    """
    _attribute(store, "s1", [_call("git push origin Feature/Login"), _usage(1.0)])
    _attribute(store, "s2", [_call("git push origin feature/login"), _usage(1.0)])
    refs = sorted(r["ref"] for r in store.query_delivery(kind="branch")["rows"])
    assert refs == ["Feature/Login", "feature/login"], refs


def test_a_pull_request_finds_its_title_despite_a_different_case(store):
    """The title/state/URL join was case-sensitive too.

    A session that typed ``nordwind/repo`` while the local checkout reports
    ``NordWind/Repo`` got a row with no title and no state, which reads as a
    pull request nobody can identify.
    """
    store.ingest_git_scan({
        "repo_root": "/tmp/nordwind-repo",
        "remote_url": "https://github.com/NordWind/Repo.git",
        "host": "github.com",
        "owner": "NordWind",
        "name": "Repo",
        "pull_requests": [{"number": 7, "state": "merged",
                           "title": "Add the thing",
                           "url": "https://github.com/NordWind/Repo/pull/7",
                           "merged_at": 1760000000}],
    })
    _attribute(store, "s1", [_call("gh pr edit 7 --repo nordwind/repo"), _usage(2.0)])
    row = store.query_delivery(kind="pr")["rows"][0]
    assert row["title"] == "Add the thing"
    assert row["state"] == "merged"
    assert row["url"].endswith("/NordWind/Repo/pull/7")
