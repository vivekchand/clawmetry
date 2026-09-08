"""Every baseline the Anomaly Detection card reads must actually be served.

Founder screenshot 2026-09-07, hosted Home: the "🔍 Anomaly Detection" card
showed an **all clear** badge above the words *"Collecting baseline data..."*.
It was not collecting anything. It would have said that forever.

`/api/anomalies` has two paths. The fallback
(`dashboard.py::_detect_and_store_anomalies`) returns `baseline_cost_7d`,
`baseline_tokens_7d`, `baseline_sessions_per_day_7d` and friends — the names
`app.js` reads. The DuckDB fast path returned exactly one key,
`cost_7d_avg_usd`, which the frontend never looks at. Once the local store
became the default the fast path always won, every key the card checks was
`undefined`, and the card fell through to its placeholder:

    blEl.innerHTML = blHtml || '...Collecting baseline data...'

Measured on a real store after the fix: cost 4.877039, tokens 30226.43,
sessions/day 30.02 across 162 sessions — none of which the card could show.

This is the same class as the false-empty-tab burn: a store fast path that
returns a NARROWER shape than the fallback it replaced, where the missing part
renders as a plausible "still working on it" rather than as an error.

The guard is derived from the frontend, so a baseline key added to the card
later is covered without editing this test.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP_JS = (REPO / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
USAGE = (REPO / "routes" / "usage.py").read_text(encoding="utf-8")


def _keys_the_card_reads():
    """Every `baselines.<key>` the frontend dereferences."""
    return sorted(set(re.findall(r"\bbaselines\.(\w+)", APP_JS)))


def _fast_path_baselines_block():
    """The emitted dict only — `#` comments stripped.

    The block carries a comment naming the keys it deliberately does NOT emit,
    and an assertion matching raw text would fail on that explanation. (Third
    time this has bitten in one session: assert on code, not on the prose that
    describes it.)
    """
    i = USAGE.index("    baselines = {")
    j = USAGE.index("    }", i)
    return "\n".join(
        ln for ln in USAGE[i:j].splitlines() if not ln.lstrip().startswith("#")
    )


def test_the_card_reads_some_baselines():
    keys = _keys_the_card_reads()
    assert keys, "no baselines.<key> reads found in app.js — guard lost its subject"


def test_every_key_the_card_reads_is_served_by_the_fast_path():
    block = _fast_path_baselines_block()
    missing = [k for k in _keys_the_card_reads() if f'"{k}"' not in block]
    assert not missing, (
        f"the /api/anomalies local-store fast path does not emit {missing}, but "
        "app.js reads them. Every one that is absent is `undefined` in the "
        "browser, and the card renders 'Collecting baseline data...' — a "
        "placeholder that never resolves, on a node with plenty of data."
    )


def test_the_legacy_key_is_kept_as_an_alias():
    assert '"cost_7d_avg_usd"' in _fast_path_baselines_block(), (
        "cost_7d_avg_usd was the fast path's only key for a long time; keep it "
        "so anything written against it does not break"
    )


def test_error_rate_is_absent_rather_than_zero():
    """A gap must not be served as a measurement.

    The fallback derives error-rate baselines from stored error events. The
    fast path cannot read those, so it omits the keys. Emitting 0.0 would
    render as "0% errors" — a claim, not a gap.
    """
    block = _fast_path_baselines_block()
    for fabricated in ("baseline_error_rate_7d", "recent_error_rate_24h"):
        assert fabricated not in block, (
            f"{fabricated} is emitted by the fast path, which cannot measure "
            "it. Absent is honest; 0.0 is a fabricated reassurance."
        )
