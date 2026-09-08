"""The Overview "Active Tasks" panel must not lie about whose task it is,
whether it succeeded, or when it ended.

Founder report 2026-09-07, hosted dashboard, runtime switcher pinned to Codex
(``app.clawmetry.com/node/<node>/?runtime=codex``). One screen, four lies:

1. A task card carried a blue **OpenClaw** pill while the switcher said Codex.
   The pill came from ``detectProjectBadge()`` — a substring match over a
   hardcoded list of the developer's own project names (``mockround``,
   ``vedicvoice``, ``openclaw``, ...) shipped to every customer. Any task whose
   prompt merely *contained* the word "openclaw" was stamped OpenClaw.
2. The panel applied no runtime filter at all, so ``?runtime=codex`` listed
   every runtime's tasks (FLYWHEEL 0a.2, per-runtime honesty, HARD GATE).
3. A sub-agent whose own detail modal read **FAILED** rendered in the list with
   a green tick under "Recently Completed": the buckets were
   ``active -> running``, a narrow ``stale && abortedLastRun && 0 tokens``
   heuristic ``-> failed``, and *everything else* ``-> done``. The server emits
   ``status == 'failed'`` outright and nothing caught it.
4. A task spawned **2026-08-20** that never ran (runtime 0s) displayed
   "Finished 1 min ago", because the end time fell back to ``updatedAt`` and
   the ingest path stamps ``now`` when a spawn timestamp will not parse.

His words: *"how is a task started on August 20th active tasks -- bunch of
shitty non functional things are the reasons customers run away"*.

The rule these tests pin: the panel shows real attribution or none, one bucket
per task decided in one place, and no invented timestamps. Blank beats wrong.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP_JS = REPO / "clawmetry" / "static" / "js" / "app.js"
OVERVIEW_HTML = REPO / "clawmetry" / "templates" / "tabs" / "overview.html"

SRC = APP_JS.read_text(encoding="utf-8")


def _body(name: str) -> str:
    """Return the source of a top-level `function <name>(` by brace matching."""
    m = re.search(r"^(?:async )?function %s\(" % re.escape(name), SRC, re.M)
    assert m, "function %s() not found in app.js" % name
    i = SRC.index("{", m.start())
    depth = 0
    for j in range(i, len(SRC)):
        if SRC[j] == "{":
            depth += 1
        elif SRC[j] == "}":
            depth -= 1
            if depth == 0:
                return SRC[i:j + 1]
    raise AssertionError("unbalanced braces in %s()" % name)


# ── 1. The fake project badge is gone and stays gone ────────────────────────
def test_hardcoded_developer_project_badge_is_deleted():
    assert "function detectProjectBadge" not in SRC, (
        "detectProjectBadge() is back. It substring-matched task text against a "
        "hardcoded list of the developer's own projects and stamped a runtime "
        "pill from it. A pill must come from real attribution."
    )


def test_no_personal_project_names_in_the_served_bundle():
    for name in ("mockround", "vedicvoice"):
        assert name not in SRC.lower(), (
            "%r is a personal project name and must not ship in app.js" % name
        )


def test_runtime_pill_refuses_to_guess():
    body = _body("_ovRuntimePill")
    assert "return null" in body, "_ovRuntimePill must be able to show nothing"
    assert "runtimeName" in body, (
        "_ovRuntimePill must read real attribution (runtimeName/agentType), not "
        "prose"
    )


# ── 2. The panel scopes to the selected runtime ─────────────────────────────
def test_overview_tasks_filters_by_selected_runtime():
    body = _body("loadOverviewTasks")
    assert "_cmRuntimeFilter" in body and "_cmRuntimeOf" in body, (
        "loadOverviewTasks() must scope its list to the selected runtime. "
        "FLYWHEEL 0a.2: a list shown under a runtime filter either scopes to "
        "that runtime or carries a visible node-wide label."
    )


def test_empty_state_names_the_runtime_instead_of_claiming_the_node_is_idle():
    body = _body("loadOverviewTasks")
    assert "No active tasks for " in body, (
        "Under a runtime filter the empty state must name the runtime; saying "
        "'The AI is idle' is false when other runtimes are busy."
    )
    assert "on other runtimes" in body, (
        "When the filter hides tasks, say how many are on other runtimes."
    )


def test_runtime_resolver_ignores_the_duration_field_named_runtime():
    """`/api/subagents` records carry `runtime` = a formatted DURATION.

    routes/sessions.py builds ``"runtime": "44s" | "12m" | "2h 5m"``. The
    resolver used to short-circuit on the first truthy candidate, so that
    duration string won, failed the prefix check, and every sub-agent fell
    through to the 'openclaw' default — which is how a Codex sub-agent was
    filed under OpenClaw in the first place.
    """
    body = _body("_cmRuntimeOf")
    assert "runtimeName" in body, "_cmRuntimeOf must consider runtimeName"
    idx_name = body.index("runtimeName")
    idx_runtime = body.rindex("o.runtime")
    assert idx_name < idx_runtime, (
        "the ambiguous `runtime` field (a duration string on sub-agent records) "
        "must be considered AFTER runtimeName/agentType, never before"
    )
    assert "o.runtime ||" not in body, (
        "short-circuiting on `o.runtime` lets a duration string suppress the "
        "real runtime name"
    )


# ── 3. One bucket per task, decided in one place ────────────────────────────
def test_failed_status_is_a_real_bucket():
    body = _body("_ovBucketOf")
    assert "_cmIsFailedStatus" in body, (
        "_ovBucketOf must route the server's `status == 'failed'` to the failed "
        "bucket. Without it a failed spawn falls through to `done` and renders "
        "with a green tick."
    )
    # The grouping lives in _ovVisible (which loadOverviewTasks calls); pin the
    # invariant — the buckets come from _ovBucketOf — not the call site, which
    # moved when the count and the list were unified (2026-09-08).
    assert "_ovBucketOf(a)" in _body("_ovVisible"), (
        "the grouping must use the shared classifier"
    )


def test_card_and_grouping_share_one_classifier():
    """They disagreed once; that is exactly how a FAILED task got a ✅."""
    assert "_ovBucketOf(agent)" in _body("_ovRenderCard"), (
        "_ovRenderCard must read _ovBucketOf, not re-derive the status"
    )
    assert "_ovBucketOf(a)" in _body("_ovVisible"), (
        "the panel's bucket splitter must read _ovBucketOf, not re-derive status"
    )
    assert "_ovVisible(" in _body("loadOverviewTasks"), (
        "loadOverviewTasks must go through the shared splitter"
    )
    assert SRC.count("abortedLastRun") == 1, (
        "the stale/aborted heuristic must live in exactly one place "
        "(_ovBucketOf); a second copy is how the two renderers drifted apart"
    )


def test_failed_status_vocabulary_helper_exists():
    body = _body("_cmIsFailedStatus")
    assert "'failed'" in body


# ── 4. No invented timestamps ───────────────────────────────────────────────
def test_end_time_is_derived_once():
    assert SRC.count("function _ovEndedMs") == 1, (
        "_ovEndedMs must be defined exactly once; a local copy inside "
        "loadOverviewTasks is how the panel's recency window and the card's "
        "label drifted apart"
    )


def test_end_time_refuses_to_invent_one():
    body = _body("_ovEndedMs")
    assert "return 0" in body, "_ovEndedMs must be able to answer 'unknown'"
    # updatedAt may only be trusted behind evidence the spawn actually ran.
    ran = body.index("var ran")
    upd = body.index("a.updatedAt")
    assert ran < upd, (
        "`updatedAt` is stamped `now` at ingest when a spawn timestamp will not "
        "parse. It may only be used as an end time after checking the spawn "
        "actually ran — otherwise an 18-day-old task reads 'Finished 1 min ago'."
    )


def test_time_label_shows_nothing_when_end_time_is_unknown():
    body = _body("_ovTimeLabel")
    assert "_ovEndedMs(agent)" in body, "_ovTimeLabel must use the shared derivation"
    assert "if (!endedMs) return '';" in body, (
        "unknown end time must render no timestamp at all"
    )


# ── 5. The dead renderer is gone ────────────────────────────────────────────
def test_legacy_duplicate_renderer_is_deleted():
    for dead in ("loadActiveTasks", "startActiveTasksRefresh", "humanTimeDone"):
        assert dead not in SRC, (
            "%s() is dead code — it was never called, drifted away from the "
            "live renderer, and filtered runtimes with a resolver that "
            "misclassified every sub-agent." % dead
        )


def test_graveyard_div_is_gone():
    assert "active-tasks-grid" not in OVERVIEW_HTML.read_text(encoding="utf-8"), (
        "the hidden #active-tasks-grid existed only so the dead renderer would "
        "not throw"
    )


# ── 6. A count never promises more than the panel will show ─────────────────
def test_other_runtime_count_uses_the_visible_set():
    """Verified live 2026-09-08 on app.clawmetry.com under ?runtime=codex.

    The empty state read "489 tasks on other runtimes — switch runtime to see
    them"; switching to all-runtimes rendered NOTHING, because all 489 had
    finished more than an hour earlier and the panel's own recency rule excludes
    them. The count was of every row the runtime filter removed, not of the rows
    a user would actually see. An empty state that sends someone to an empty
    view is its own small lie.
    """
    body = _body("loadOverviewTasks")
    assert "_ovVisible(allAgents.filter(" in body, (
        "the other-runtime count must be derived from _ovVisible (the rows that "
        "actually render), not from a raw length difference"
    )
    assert "allAgents.length - agents.length" not in body, (
        "counting raw filtered-out rows is what produced the false '489 tasks' "
        "promise"
    )


def test_one_visibility_rule_for_counts_and_rendering():
    assert SRC.count("function _ovVisible") == 1
    assert SRC.count("function _ovRecentlyFinished") == 1, (
        "one recency rule; a second copy is how a count and a list disagree"
    )
    body = _body("loadOverviewTasks")
    assert "_ovVisible(agents)" in body, (
        "the rendered buckets must come from the same splitter the counts use"
    )
