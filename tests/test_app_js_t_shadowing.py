"""Guard: no callback whose parameter shadows the global i18n ``t()`` may
call ``t(...)`` inside its body.

Founder report 2026-08-09: the Sessions tab rendered "Failed to load
transcripts" for anyone with >= 1 session. Root cause:
``data.transcripts.forEach(function(t) {...})`` shadowed the global i18n
helper, and the score-button line inside the loop called
``t('transcripts.score_btn', ...)`` -> ``TypeError: t is not a function``
-> the catch blanked the whole tab. The API was fine; only the render died.

This scans app.js for every ``function(t)`` / ``function (t, ...)``
callback, extracts the balanced-brace body, and fails if the body contains
an i18n-style call ``t('`` or ``t("``. Auto-discovers its scope: a NEW
shadowing callback that starts calling i18n fails CI immediately, without
anyone hand-maintaining a list.
"""

import re
from pathlib import Path

APP_JS = (
    Path(__file__).resolve().parents[1]
    / "clawmetry" / "static" / "js" / "app.js"
)

# function(t), function (t), function(t, i) ... — param list STARTING with
# a bare `t` parameter.
_SHADOW_RE = re.compile(r"function\s*\(\s*t\s*[,)]")
# An i18n-style call: t('key'... or t("key"... — property access like x.t(
# is excluded by the negative lookbehind.
_I18N_CALL_RE = re.compile(r"(?<![\w.$])t\(\s*['\"]")


def _body_after(src: str, start: int) -> str:
    """Return the balanced {...} body of the function starting at ``start``."""
    brace = src.index("{", start)
    depth = 0
    for i in range(brace, len(src)):
        c = src[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return src[brace:i + 1]
    return src[brace:]


def test_no_i18n_call_inside_t_shadowing_callback():
    src = APP_JS.read_text(encoding="utf-8")
    offenders = []
    for m in _SHADOW_RE.finditer(src):
        body = _body_after(src, m.start())
        hit = _I18N_CALL_RE.search(body)
        if hit:
            line = src.count("\n", 0, m.start()) + 1
            hit_line = line + body.count("\n", 0, hit.start())
            offenders.append(
                f"callback with param `t` at app.js:{line} calls i18n t() "
                f"at app.js:{hit_line} - the param shadows the global t() "
                f"and throws at runtime; rename the callback param"
            )
    assert not offenders, "\n".join(offenders)
