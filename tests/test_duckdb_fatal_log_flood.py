"""Guards for the 2026-08-24 founder-machine incident.

A corrupt DuckDB index made every ``events`` flush raise. Two separate bugs
turned that into a 12.5-hour outage nobody was told about:

1. The retry path logged ``%s`` of the DuckDB exception. A DuckDB constraint
   error embeds the ENTIRE failing chunk in its message (30 columns x 258
   rows), so each failure wrote tens of KB -- three attempts per tick, every
   tick. ``sync.log`` reached **3.3 GB**.
2. Nothing recognised "database has been invalidated". Once DuckDB kills a
   connection every later statement fails identically, so the daemon retried
   a dead handle forever instead of reporting the (known, no-data-loss)
   recovery once.

These tests pin the bounded-logging and fatal-detection behaviour.
"""

from __future__ import annotations

import clawmetry.local_store as ls


# ── 1. exception text is bounded no matter what the driver puts in it ─────

def test_brief_exc_truncates_a_chunk_dump():
    # Shape of the real thing: a short headline then a huge chunk dump.
    huge = "Invalid Input Error: Failed to delete all rows from index. " + (
        "- FLAT VARCHAR: 258 = [ a10e57e08ab846e4, ] " * 2000
    )
    assert len(huge) > 50_000
    out = ls._brief_exc(Exception(huge))
    assert len(out) < ls._EXC_LOG_LIMIT + 100
    assert "truncated" in out
    # The diagnostic headline must survive the truncation.
    assert "Failed to delete all rows from index" in out


def test_brief_exc_leaves_a_short_message_alone():
    assert ls._brief_exc(Exception("boom")) == "boom"


def test_brief_exc_never_raises_on_a_hostile_exception():
    class _Nasty(Exception):
        def __str__(self):
            raise RuntimeError("cannot stringify")

    # A logging helper that throws takes down the line it was protecting.
    assert ls._brief_exc(_Nasty()) == "_Nasty"


def test_brief_exc_collapses_newlines_to_one_line():
    out = ls._brief_exc(Exception("line one\nline two\n\tline three"))
    assert "\n" not in out and "\t" not in out


# ── 2. an invalidated connection is recognised, not retried ───────────────

def test_is_fatal_db_state_matches_the_real_duckdb_message():
    real = (
        "FATAL Error: Failed: database has been invalidated because of a "
        "previous fatal error. The database must be restarted prior to being "
        'used again.\nOriginal error: "Invalid Input Error: Failed to delete '
        'all rows from index. Only deleted 0 out of 258 rows.'
    )
    assert ls._is_fatal_db_state(Exception(real)) is True


def test_is_fatal_db_state_ignores_an_ordinary_error():
    assert ls._is_fatal_db_state(Exception("constraint violated")) is False
    assert ls._is_fatal_db_state(Exception("boom")) is False


def test_fatal_db_is_reported_once_per_process(monkeypatch, caplog):
    """The whole point: one actionable line, not one per tick for 12 hours."""
    monkeypatch.setattr(ls, "_fatal_db_reported", False, raising=False)
    exc = Exception("database has been invalidated because of a previous fatal error")
    with caplog.at_level("ERROR", logger="clawmetry.local_store"):
        for _ in range(50):
            ls._report_fatal_db_once(exc)
    errors = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(errors) == 1
    # It must tell the operator how to recover, or it is just a nicer log flood.
    assert "DROP INDEX" in errors[0].getMessage()
