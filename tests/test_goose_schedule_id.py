"""obs-gap #2622: the Goose adapter must surface schedule_id (the cron link).

Goose runs recipes on a cron scheduler; a scheduled session carries
session_type='scheduled' + a schedule_id pointing at its recurring job. The
adapter previously read session_type but not schedule_id, so a scheduled session
was observable as "scheduled" but you couldn't tell WHICH schedule. Now it
surfaces extra['scheduleId']. Must degrade gracefully on an older Goose db that
lacks the schedule_id column (never return []).
"""
import os
import sqlite3
import tempfile

from clawmetry.adapters.goose import GooseAdapter

_COLS_WITH_SCHED = (
    "id TEXT PRIMARY KEY, name TEXT, description TEXT, session_type TEXT, "
    "working_dir TEXT, created_at TEXT, updated_at TEXT, total_tokens INT, "
    "input_tokens INT, output_tokens INT, accumulated_total_tokens INT, "
    "accumulated_cost REAL, provider_name TEXT, model_config_json TEXT, "
    "goose_mode TEXT, schedule_id TEXT, recipe_json TEXT"
)
_COLS_NO_SCHED = _COLS_WITH_SCHED.replace(", schedule_id TEXT, recipe_json TEXT", "")


def _make_db(cols, rows):
    d = tempfile.mkdtemp()
    db = os.path.join(d, "sessions.db")
    c = sqlite3.connect(db)
    c.execute(f"CREATE TABLE sessions ({cols})")
    c.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, message_id TEXT, "
              "session_id TEXT, role TEXT, content_json TEXT, created_timestamp INT, tokens INT)")
    for r in rows:
        c.execute(f"INSERT INTO sessions VALUES ({','.join('?' * len(r))})", r)
    c.commit()
    c.close()
    return db


def test_schedule_id_surfaced_for_scheduled_session():
    db = _make_db(_COLS_WITH_SCHED, [
        ("s_sched", "daily", "", "scheduled", "/tmp", "2026-06-01 10:00:00",
         "2026-06-01 10:01:00", 100, 80, 20, 100, 0.01, "anthropic",
         '{"model_name":"claude-3-5-haiku"}', "auto", "daily-standup",
         '{"version":"1.0","title":"Daily Standup Summary"}'),
        ("s_user", "manual", "", "user", "/tmp", "2026-06-01 09:00:00",
         "2026-06-01 09:01:00", 50, 40, 10, 50, None, "ollama",
         '{"model_name":"llama3.2"}', "auto", None, None),
    ])
    by = {s.id: s for s in GooseAdapter(db_path=db).list_sessions(limit=5)}
    assert by["s_sched"].extra["scheduleId"] == "daily-standup"
    assert by["s_sched"].extra["sessionType"] == "scheduled"
    # recipe title surfaced from recipe_json (#2625)
    assert by["s_sched"].extra["recipe"] == "Daily Standup Summary"
    assert by["s_user"].extra["scheduleId"] is None
    assert by["s_user"].extra["recipe"] is None


def test_old_db_without_schedule_id_column_does_not_break():
    # An older Goose db lacking schedule_id must still list sessions (graceful
    # fallback), with scheduleId=None — never an empty list.
    db = _make_db(_COLS_NO_SCHED, [
        ("s1", "manual", "", "user", "/tmp", "2026-06-01 09:00:00",
         "2026-06-01 09:01:00", 50, 40, 10, 50, None, "ollama",
         '{"model_name":"llama3.2"}', "auto"),
    ])
    sessions = GooseAdapter(db_path=db).list_sessions(limit=5)
    assert len(sessions) == 1, "old db without schedule_id must not return []"
    assert sessions[0].extra["scheduleId"] is None
