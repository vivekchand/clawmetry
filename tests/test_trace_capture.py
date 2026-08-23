"""Trace bundle capture and publication redaction (PRD-pr-trace.md §4b, §4f).

Names the proposed criteria AC-TRACE-001.1/001.2 (attribution tiers),
AC-TRACE-002.1 (nothing secret-shaped is published) and AC-TRACE-004.1 (a
session spanning several PRs reports shared attribution, not a full cost).
Those ids are not yet in ``docs/acceptance_criteria.json``; that manifest is
mirrored from 8090 Software Factory and is refreshed with ``make ac-sync``,
never hand-edited (FLYWHEEL §1g).

The rule under most of these tests: **a bundle must never overstate what it
knows.** An ambiguous attribution that renders as a confident dollar figure is
worse than no bundle at all.
"""

from __future__ import annotations

import re

import pytest

from clawmetry import trace_capture as tc


# ── attribution tiers ──────────────────────────────────────────────────────

def _commit(sha="a1b2c3d", ts=1000, session=None, coauth=False, subject="feat: x"):
    return {"sha": sha, "short_sha": sha[:9], "ts": ts, "author": "A",
            "subject": subject, "session_id": session, "ai_coauthored": coauth}


def _session(sid, start="2026-08-22T00:00:00+00:00", end="2026-08-22T01:00:00+00:00"):
    return {"session_id": sid, "started_at": start, "updated_at": end,
            "cost_usd": 1.0}


def test_all_commits_stamped_is_exact():
    """AC-TRACE-001.1 -- every commit named its session."""
    commits = [_commit(session="claude_code:s1"), _commit(sha="b", session="claude_code:s1")]
    ids, attr = tc.resolve_sessions(commits, [_session("claude_code:s1")])
    assert ids == ["claude_code:s1"]
    assert attr == tc.ATTR_EXACT


def test_partially_stamped_range_is_shared_not_exact():
    """A range we cannot fully account for must not claim exactness."""
    commits = [_commit(session="claude_code:s1"), _commit(sha="b", session=None)]
    ids, attr = tc.resolve_sessions(commits, [_session("claude_code:s1")])
    assert ids == ["claude_code:s1"]
    assert attr == tc.ATTR_SHARED


def test_unstamped_ai_commits_fall_back_to_heuristic():
    """AC-TRACE-001.2 -- inferred, and labelled as inferred."""
    import datetime
    ts = int(datetime.datetime(2026, 8, 22, 0, 30,
                               tzinfo=datetime.timezone.utc).timestamp())
    commits = [_commit(ts=ts, coauth=True)]
    ids, attr = tc.resolve_sessions(commits, [_session("claude_code:s1")])
    assert ids == ["claude_code:s1"]
    assert attr == tc.ATTR_HEURISTIC


def test_human_commits_resolve_to_nothing():
    ids, attr = tc.resolve_sessions([_commit()], [_session("claude_code:s1")])
    assert ids == []


def test_trailer_naming_an_unknown_session_is_not_exact():
    """A trailer we cannot resolve must not be treated as a resolution."""
    commits = [_commit(session="claude_code:gone")]
    ids, attr = tc.resolve_sessions(commits, [_session("claude_code:s1")])
    assert "claude_code:gone" not in ids
    assert attr != tc.ATTR_EXACT


# ── publication redaction ──────────────────────────────────────────────────

@pytest.mark.parametrize("raw,must_not_contain", [
    ("ANTHROPIC_API_KEY=sk-ant-api03-" + "A" * 24, "sk-ant-api03"),
    ("Authorization: Bearer ghp_" + "B" * 36, "ghp_"),
    ("aws AKIA" + "C" * 16, "AKIA"),
    ("/home/vivek/.ssh/id_rsa", "/home/vivek"),
    ("/Users/jane/private", "/Users/jane"),
    ("ping me at someone@example.com", "someone@example.com"),
    ("host 192.168.1.44", "192.168.1.44"),
])
def test_publication_redaction_removes_it(raw, must_not_contain):
    """AC-TRACE-002.1 -- nothing secret- or private-shaped survives."""
    assert must_not_contain not in tc.redact_for_publication(raw)


def test_redaction_failure_withholds_content(monkeypatch):
    """Publication fails CLOSED: withhold rather than leak.

    The opposite of the ingest path, which fails open to avoid losing data.
    Here the blast radius is the public internet.
    """
    monkeypatch.setattr(tc.redaction, "redact_text",
                        lambda _t: (_ for _ in ()).throw(RuntimeError("boom")))
    out = tc.redact_for_publication("some secret text")
    assert "some secret text" not in out
    assert "WITHHELD" in out


def test_redaction_passes_through_empty_and_non_str():
    assert tc.redact_for_publication("") == ""
    assert tc.redact_for_publication(None) is None


# ── bundle assembly ────────────────────────────────────────────────────────

def _events(session_id, base_ts="2026-08-22T00:0"):
    return [
        {"ts": base_ts + "0:00+00:00", "event_type": "message", "model": "claude-opus-5",
         "token_count": 10, "cost_usd": 0.5,
         "data": {"role": "user", "content": "do the thing"}},
        {"ts": base_ts + "1:00+00:00", "event_type": "tool_call", "model": "claude-opus-5",
         "token_count": 5, "cost_usd": 0.25,
         "data": {"role": "assistant", "content": "running", "tool_name": "Bash"}},
        {"ts": base_ts + "2:00+00:00", "event_type": "message", "model": "claude-opus-5",
         "token_count": 7, "cost_usd": 0.25,
         "data": {"role": "assistant", "content": "done"}},
    ]


def _build(commits, session_ids, attr, events, **kw):
    return tc.build_bundle(
        repo="/tmp/x", commit_range="A..B", commits=commits,
        session_ids=session_ids, attribution=attr,
        events_by_session=events,
        sessions_meta={s: {"cost_usd": 1.0} for s in session_ids},
        project="owner/repo", **kw)


def test_bundle_summarises_prompts_tools_and_cost():
    import datetime
    ts = int(datetime.datetime(2026, 8, 22, 1, 0,
                               tzinfo=datetime.timezone.utc).timestamp())
    b = _build([_commit(ts=ts, session="claude_code:s1")], ["claude_code:s1"],
               tc.ATTR_EXACT, {"claude_code:s1": _events("claude_code:s1")}, pr="42")
    assert b["summary"]["prompts"] == 1
    assert b["summary"]["tools"] == 1
    assert b["summary"]["cost_usd"] == 1.0
    assert b["lenses"]["prompts"][0]["text"] == "do the thing"
    assert b["pr"] == "42"
    assert b["project"] == "owner/repo"


def test_events_after_the_last_commit_are_excluded_and_flip_to_shared():
    """AC-TRACE-004.1 -- a session that kept working past this PR reports an
    upper bound, not a figure."""
    import datetime
    # last commit lands BEFORE the final event
    ts = int(datetime.datetime(2026, 8, 22, 0, 1, 30,
                               tzinfo=datetime.timezone.utc).timestamp())
    b = _build([_commit(ts=ts, session="claude_code:s1")], ["claude_code:s1"],
               tc.ATTR_EXACT, {"claude_code:s1": _events("claude_code:s1")})
    assert b["attribution"] == tc.ATTR_SHARED
    assert b["summary"]["cost_is_upper_bound"] is True
    assert b["summary"]["cost_usd"] < 1.0


def test_exact_bundle_is_not_marked_upper_bound():
    import datetime
    ts = int(datetime.datetime(2026, 8, 22, 9, 0,
                               tzinfo=datetime.timezone.utc).timestamp())
    b = _build([_commit(ts=ts, session="claude_code:s1")], ["claude_code:s1"],
               tc.ATTR_EXACT, {"claude_code:s1": _events("claude_code:s1")})
    assert b["attribution"] == tc.ATTR_EXACT
    assert b["summary"]["cost_is_upper_bound"] is False


def test_bundle_redacts_prompt_text():
    """AC-TRACE-002.1 -- the lens content is redacted, not just the raw store."""
    import datetime
    ts = int(datetime.datetime(2026, 8, 22, 9, 0,
                               tzinfo=datetime.timezone.utc).timestamp())
    evs = _events("claude_code:s1")
    evs[0]["data"]["content"] = "use key sk-ant-api03-" + "Z" * 24
    b = _build([_commit(ts=ts, session="claude_code:s1")], ["claude_code:s1"],
               tc.ATTR_EXACT, {"claude_code:s1": evs})
    assert "sk-ant-api03" not in b["lenses"]["prompts"][0]["text"]


def test_unbacked_lenses_are_empty_not_fabricated():
    """PRD §3b -- an honest empty beats a synthesised graph."""
    b = _build([_commit(session="claude_code:s1")], ["claude_code:s1"],
               tc.ATTR_EXACT, {"claude_code:s1": []})
    assert b["lenses"]["agent_graph"] == {"nodes": [], "edges": []}
    assert b["lenses"]["workflows"] == []


def test_data_field_accepts_dict_json_and_repr():
    """The store hands ``data`` back in all three shapes depending on transport."""
    assert tc._as_dict({"a": 1}) == {"a": 1}
    assert tc._as_dict('{"a": 1}') == {"a": 1}
    assert tc._as_dict("{'a': 1}") == {"a": 1}
    assert tc._as_dict("not parseable") == {}
    assert tc._as_dict(None) == {}



# ── self-containment ───────────────────────────────────────────────────────

_RESOURCE_LOAD = re.compile(
    r"""<(?:script|link|img|iframe|source|video|audio|embed|object)\b[^>]*"""
    r"""\b(?:src|href)\s*=\s*["']?(https?://[^"'\s>]+)""",
    re.IGNORECASE,
)


def _external_resource_loads(page: str) -> list:
    """URLs the page would actually FETCH, ignoring URLs that are merely text.

    The earlier version of this guard asserted ``"http://" not in page``, which
    reads like a self-containment check and is not one: it passed only because
    the fixture happened to contain no URLs. A real bundle carries URLs inside
    prompts and tool output all the time (a captured trace of this very repo has
    98 of them), and those are inert escaped text, not network dependencies.
    Asserting on the raw substring would therefore have to be deleted the first
    time someone traced a session that mentioned a link, taking the actual guard
    with it. Match the tag that would do the fetching instead.
    """
    return _RESOURCE_LOAD.findall(page or "")


# ── viewer ─────────────────────────────────────────────────────────────────

def test_viewer_renders_a_self_contained_page():
    from clawmetry import trace_viewer
    import datetime
    ts = int(datetime.datetime(2026, 8, 22, 9, 0,
                               tzinfo=datetime.timezone.utc).timestamp())
    b = _build([_commit(ts=ts, session="claude_code:s1")], ["claude_code:s1"],
               tc.ATTR_EXACT, {"claude_code:s1": _events("claude_code:s1")}, pr="42")
    page = trace_viewer.render_html(b)
    assert page.startswith("<!doctype html>")
    assert "do the thing" in page
    assert "attribution: exact" in page
    assert _external_resource_loads(page) == []


def test_viewer_escapes_prompt_html():
    """Prompt text is untrusted input; it must not become markup."""
    from clawmetry import trace_viewer
    import datetime
    ts = int(datetime.datetime(2026, 8, 22, 9, 0,
                               tzinfo=datetime.timezone.utc).timestamp())
    b = _build([_commit(ts=ts, session="claude_code:s1")], ["claude_code:s1"],
               tc.ATTR_EXACT, {"claude_code:s1": [
                   {"ts": "2026-08-22T00:00:00+00:00", "event_type": "message",
                    "token_count": 0, "cost_usd": 0,
                    "data": {"role": "user", "content": "<img src=x onerror=alert(1)>"}}]})
    assert b["summary"]["prompts"] == 1, "fixture must actually produce a prompt"
    page = trace_viewer.render_html(b)
    assert "<img src=x" not in page
    assert "&lt;img" in page

def test_urls_inside_prompt_text_are_not_resource_loads():
    """A prompt that mentions a link must not count as a network dependency.

    This is the case that made the old `"http://" not in page` assertion
    untenable: real traces are full of URLs in prompts and tool output. They
    must render as inert escaped text, and the page must still fetch nothing.
    """
    from clawmetry import trace_viewer
    import datetime
    ts = int(datetime.datetime(2026, 8, 22, 9, 0,
                               tzinfo=datetime.timezone.utc).timestamp())
    evs = _events("claude_code:s1")
    evs[0]["data"]["content"] = "read https://github.com/openclaw/openclaw and fix it"
    b = _build([_commit(ts=ts, session="claude_code:s1")], ["claude_code:s1"],
               tc.ATTR_EXACT, {"claude_code:s1": evs})
    page = trace_viewer.render_html(b)
    assert "github.com/openclaw/openclaw" in page, "the URL should still be readable"
    assert _external_resource_loads(page) == [], "but nothing may be fetched"


def test_guard_catches_a_real_external_resource():
    """Revert-proof: the guard must fail on the thing it claims to prevent."""
    injected = '<html><head><script src="https://cdn.example.com/x.js"></script></head></html>'
    assert _external_resource_loads(injected) == ["https://cdn.example.com/x.js"]
