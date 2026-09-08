"""On a sub-agent record, ``runtime`` is the runtime's NAME — not a duration.

Founder report 2026-09-07: a Codex task on the hosted Home screen carried a
blue **OpenClaw** pill. The proximate cause was a hardcoded project-badge map
(fixed in #5645), but the reason the *correct* attribution could not be used
was this: ``/api/subagents`` emitted a field literally called ``runtime``
holding a formatted duration — ``"44s"``, ``"12m"``, ``"2h 5m"``.

Everywhere else in this product — alerts, attention, guard, live sessions — a
field named ``runtime`` is the agent runtime's name. So the generic client
resolver ``_cmRuntimeOf``, which reads ``o.runtime``, took ``"12m"`` for a
runtime name, failed to match it against the known runtimes, and fell through
to its ``openclaw`` default. **Every** sub-agent in the product resolved to
OpenClaw. #5645 hardened the resolver to try other candidates first, which
stops the mis-attribution; this removes the landmine that caused it.

The duration is not lost: ``runtimeMs`` carries it numerically and
``runtimeFormatted`` carries the display string, which is what the UI reads.

A field whose name means the opposite of its contents is not a naming nit. It
is a defect generator: every future consumer that reasonably assumes the
product-wide meaning gets a wrong answer, silently, and the wrongness looks
like data rather than a bug.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SESSIONS = (REPO / "routes" / "sessions.py").read_text(encoding="utf-8")
APP_JS = (REPO / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")


def test_no_shaper_assigns_a_duration_to_a_variable_named_runtime():
    """The local variable is where the confusion started."""
    assert not re.search(r"^\s+runtime = f\"\{elapsed_s", SESSIONS, re.M), (
        "a formatted duration is being assigned to a variable named `runtime`; "
        "call it runtime_label — `runtime` means the runtime's NAME in every "
        "other record this product emits"
    )


def test_subagent_records_emit_the_runtime_name():
    """Both sub-agent shapers must emit a name under `runtime`."""
    assert SESSIONS.count('"runtime":          runtime_name,') == 1, (
        "the DuckDB sub-agent shaper must emit the runtime NAME as `runtime`"
    )
    assert SESSIONS.count('"runtime": runtime_name,') == 1, (
        "the gateway/roster sub-agent shaper must emit the runtime NAME as "
        "`runtime`"
    )


def test_the_duration_still_has_a_home():
    """Removing the ambiguity must not lose the duration."""
    assert '"runtimeMs"' in SESSIONS, "the numeric duration must still be emitted"
    assert SESSIONS.count('"runtimeFormatted"') >= 2, (
        "every sub-agent shaper must emit runtimeFormatted; it is now the only "
        "field carrying a display duration"
    )
    assert "or runtime_label," in SESSIONS, (
        "runtimeFormatted must fall back to the computed duration — the "
        "upstream completion field is frequently absent, and without the "
        "fallback the UI would show no elapsed time at all"
    )


def test_no_ui_consumer_reads_runtime_as_a_duration():
    """The readers that displayed `.runtime` must read runtimeFormatted."""
    for bad in ("agent.runtime +", "sa.runtime +", "match.runtimeFormatted || match.runtime"):
        assert bad not in APP_JS, (
            f"{bad!r} treats the runtime NAME as a duration; read "
            f"runtimeFormatted instead"
        )
    # No consumer may interpolate a runtime-ish value into HTML unescaped.
    # Expressed as an absence so it still holds if a consumer is deleted — the
    # `agent.runtimeFormatted` one was, when the invisible Home widget went.
    import re as _re
    raw = _re.findall(r"\+ *(?:agent|sa|match)\.runtime[A-Za-z]* *\+", APP_JS)
    assert not raw, f"unescaped interpolation of a runtime value: {raw}"


def test_those_consumers_escape_their_output():
    """Both interpolated the value raw before this change.

    One of the two (the Home mini-widget) was later deleted outright as a fetch
    rendering into a hidden element, so this asserts the surviving consumers
    escape rather than naming a call site that may legitimately disappear.
    """
    import re as _re
    for m in _re.finditer(r"(?:agent|sa)\.runtimeFormatted", APP_JS):
        line_start = APP_JS.rfind("\n", 0, m.start()) + 1
        line = APP_JS[line_start:APP_JS.index("\n", m.start())]
        if line.lstrip().startswith("//"):
            continue
        assert "escHtml(" in line, (
            f"runtimeFormatted interpolated without escaping: {line.strip()[:90]}"
        )


def test_the_task_modal_does_not_label_a_duration_as_runtime():
    """A row reading `Runtime: 1s` is the same collision, in the UI."""
    assert "meta.push(['Duration', rtDisplay])" in APP_JS, (
        "the elapsed-time row must be labelled Duration; labelling it Runtime "
        "in a product where runtime means Codex/Claude Code/OpenClaw is the "
        "collision this row exists to remove"
    )
    assert "meta.push(['Runtime', _cmRuntimeLabel(" in APP_JS, (
        "now that `runtime` carries the name, the modal should show it — "
        "'which runtime ran this?' is the question that started this thread"
    )
