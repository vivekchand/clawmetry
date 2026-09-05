"""Briefs (WO-62): cron matcher, due logic, scheduler tick, cap, failure
posting, no-credential fallback, routes.

Requirement 0904463d-6472-4812-978c-86d541f1cca5 (REQ-BRIEF-001).

* The in-house cron matcher handles ``*``, lists, ranges and steps and
  rejects anything else; no dependency was added for it.
* ``is_due`` fires once per matching minute and never for a disabled brief.
* The scheduler tick runs due briefs only, bounded by the per-node cap,
  and records the outcome on the row.
* A brief that fails to run POSTS the failure (never silence).
* Without a narrator credential the post carries the raw table and says so;
  without any credential a free-text question fails honestly while the
  built-in digest (canned SQL) still runs.
* Routes: list offers the built-in digest until it is saved; save validates
  and enforces the cap; run-now returns the run record; mutating routes
  refuse a cross-origin POST.
"""
from __future__ import annotations

import datetime as dt
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from clawmetry import briefs as br

pytest.importorskip("duckdb")

UTC = dt.timezone.utc


# ── cron ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("expr,when,expected", [
    ("0 9 * * 1", dt.datetime(2026, 9, 7, 9, 0, tzinfo=UTC), True),    # Monday 09:00
    ("0 9 * * 1", dt.datetime(2026, 9, 8, 9, 0, tzinfo=UTC), False),   # Tuesday
    ("0 9 * * *", dt.datetime(2026, 9, 8, 9, 1, tzinfo=UTC), False),
    ("*/15 * * * *", dt.datetime(2026, 9, 8, 9, 45, tzinfo=UTC), True),
    ("*/15 * * * *", dt.datetime(2026, 9, 8, 9, 50, tzinfo=UTC), False),
    ("30 8-10 * * 1-5", dt.datetime(2026, 9, 9, 10, 30, tzinfo=UTC), True),
    ("30 8-10 * * 1-5", dt.datetime(2026, 9, 12, 10, 30, tzinfo=UTC), False),  # Saturday
    ("0 0 1,15 * *", dt.datetime(2026, 9, 15, 0, 0, tzinfo=UTC), True),
    ("0 0 1,15 * *", dt.datetime(2026, 9, 16, 0, 0, tzinfo=UTC), False),
    ("0 12 * * 7", dt.datetime(2026, 9, 13, 12, 0, tzinfo=UTC), True),    # 7 == Sunday
    ("0 12 * 9 *", dt.datetime(2026, 10, 1, 12, 0, tzinfo=UTC), False),
])
def test_cron_matches(expr, when, expected):
    assert br.cron_matches(expr, when) is expected


@pytest.mark.parametrize("bad", ["", "0 9 * *", "60 9 * * *", "0 24 * * *", "0 9 0 * *",
                                 "a b c d e", "0 9 * * 8", "*/0 * * * *", "5-3 * * * *"])
def test_cron_rejects_garbage(bad):
    with pytest.raises(ValueError):
        br.parse_cron(bad)


def test_is_due_once_per_minute_and_never_when_off():
    now = dt.datetime(2026, 9, 7, 9, 0, 20, tzinfo=UTC)
    b = {"enabled": True, "cron_expr": "0 9 * * 1", "last_run_at": None}
    assert br.is_due(b, now)
    b["last_run_at"] = int(now.replace(second=5).timestamp() * 1000)
    assert not br.is_due(b, now), "already ran this minute"
    b["last_run_at"] = int((now - dt.timedelta(days=7)).timestamp() * 1000)
    assert br.is_due(b, now)
    assert not br.is_due(dict(b, enabled=False), now)
    assert not br.is_due(dict(b, cron_expr="nonsense"), now)


def test_is_due_respects_the_brief_timezone():
    pytest.importorskip("zoneinfo")
    # 09:00 in Kolkata is 03:30 UTC.
    now = dt.datetime(2026, 9, 7, 3, 30, tzinfo=UTC)
    assert br.is_due({"enabled": True, "cron_expr": "30 3 * * *"}, now)
    assert br.is_due({"enabled": True, "cron_expr": "0 9 * * *", "tz": "Asia/Kolkata"}, now)
    assert not br.is_due({"enabled": True, "cron_expr": "0 9 * * *", "tz": "UTC"}, now)


# ── validation ──────────────────────────────────────────────────────────────

def test_validate_brief():
    ok, err = br.validate_brief({"title": "Costs", "question": "what cost more?",
                                 "cron_expr": "0  9 * * 1", "channel_ref": "Slack"})
    assert err is None and ok["cron_expr"] == "0 9 * * 1" and ok["channel_ref"] == "slack"
    assert ok["id"].startswith("brief_") and ok["enabled"] is False
    for bad, word in (({"question": "q", "cron_expr": "0 9 * * *"}, "title"),
                      ({"title": "t", "cron_expr": "0 9 * * *"}, "question"),
                      ({"title": "t", "question": "q", "cron_expr": "x"}, "schedule"),
                      ({"title": "t", "question": "q", "cron_expr": "0 9 * * *",
                        "channel_ref": "pager"}, "channel"),
                      ({"title": "t", "question": "q", "cron_expr": "0 9 * * *",
                        "id": "../x"}, "id")):
        _, err = br.validate_brief(bad)
        assert err and word in err, (bad, err)


# ── running ─────────────────────────────────────────────────────────────────

class _Store:
    """Just enough store for run_brief: a canned result set."""

    def __init__(self, rows=None, raise_on_select=None):
        self.rows = rows if rows is not None else [{"runtime": "cursor", "sessions": 3, "cost_usd": 1.5}]
        self.raise_on_select = raise_on_select

    def raw_select_safe(self, *, sql, params=None):
        if self.raise_on_select:
            raise RuntimeError(self.raise_on_select)
        return list(self.rows)


def _capture():
    posts = []

    def poster(url, payload):
        posts.append((url, payload))
        return True
    return posts, poster


CFG = {"slack_webhook_url": "https://hooks.example/slack", "webhook_url": "https://hooks.example/generic"}


def test_builtin_digest_runs_without_any_credential_and_says_so():
    posts, poster = _capture()
    b = dict(br.BUILTIN_DAILY_DIGEST, channel_ref="slack", enabled=True)
    res = br.run_brief(b, _Store(), narrate=lambda *a, **k: None, poster=poster, channel_config=CFG,
                       llm_sql=lambda q, s: (_ for _ in ()).throw(AssertionError("must not be called")))
    assert res["status"] == "ok" and res["narrated"] is False and res["posted"] is True
    assert res["rows"] == 1
    assert len(posts) == 1 and posts[0][0] == CFG["slack_webhook_url"]
    text = posts[0][1]["text"]
    assert "raw table" in text and "cursor" in text and "#signals" in text
    assert "—" not in text and " -- " not in text


def test_narrated_when_a_credential_exists():
    posts, poster = _capture()
    b = dict(br.BUILTIN_DAILY_DIGEST, channel_ref="webhook", enabled=True)
    res = br.run_brief(b, _Store(), narrate=lambda et, ctx, **k: "Cursor ran three sessions for $1.50.",
                       poster=poster, channel_config=CFG)
    assert res["status"] == "ok" and res["narrated"] is True
    assert "Cursor ran three sessions" in posts[0][1]["text"]
    assert "raw table" not in posts[0][1]["text"]


def test_question_brief_without_credential_fails_honestly_and_posts_it():
    posts, poster = _capture()
    b = {"id": "b1", "title": "Costs", "question": "what cost more?", "cron_expr": "0 9 * * 1",
         "channel_ref": "slack", "enabled": True}

    def no_auth(q, s):
        raise ValueError("no_auth: No Anthropic credential.")
    res = br.run_brief(b, _Store(), llm_sql=no_auth, narrate=lambda *a, **k: None,
                       poster=poster, channel_config=CFG)
    assert res["status"] == "failed" and "no model credential" in res["error"]
    assert res["posted"] is True, "a failure is posted, never silence"
    assert "could not run" in posts[0][1]["text"] and "no model credential" in posts[0][1]["text"]


def test_query_failure_is_posted_and_unsafe_sql_is_refused():
    posts, poster = _capture()
    b = {"id": "b1", "title": "Costs", "question": "q", "cron_expr": "0 9 * * 1",
         "channel_ref": "slack", "enabled": True}
    res = br.run_brief(b, _Store(raise_on_select="table missing"),
                       llm_sql=lambda q, s: {"sql": "SELECT 1 FROM sessions"},
                       narrate=lambda *a, **k: None, poster=poster, channel_config=CFG)
    assert res["status"] == "failed" and "table missing" in res["error"] and posts
    res = br.run_brief(b, _Store(), llm_sql=lambda q, s: {"sql": "DELETE FROM sessions"},
                       narrate=lambda *a, **k: None, poster=poster, channel_config=CFG)
    assert res["status"] == "failed" and "rejected" in res["error"]


def test_unconfigured_channel_is_a_posted_failure_not_silence():
    b = dict(br.BUILTIN_DAILY_DIGEST, channel_ref="telegram", enabled=True)
    res = br.run_brief(b, _Store(), narrate=lambda *a, **k: None, poster=lambda u, p: True,
                       channel_config={})
    assert res["status"] == "failed" and "Telegram" in res["error"]
    ok, err = br.post_to_channel("dashboard", "t", "x", config={})
    assert ok and err is None


# ── scheduler tick (isolated DuckDB) ───────────────────────────────────────

@pytest.fixture()
def store(tmp_path, monkeypatch):
    """A direct LocalStore on a per-test DuckDB file. ``DB_PATH`` is resolved
    at connect time from the module global, and conftest has already pinned
    the env var for the whole session, so the global is patched here: one
    file per test, nothing shared, nothing from the developer's store."""
    from pathlib import Path
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "3600")
    from clawmetry import local_store as ls
    monkeypatch.setattr(ls, "DB_PATH", Path(tmp_path / "briefs.duckdb"))
    s = ls.LocalStore()
    yield s
    try:
        s.stop(flush=False)
    except Exception:  # noqa: BLE001, S110
        pass


def _brief(i, cron="0 9 * * 1", enabled=True):
    return {"id": f"b{i}", "title": f"Brief {i}", "question": "q", "cron_expr": cron,
            "channel_ref": "dashboard", "enabled": enabled}


def test_tick_runs_due_briefs_only_and_records_the_outcome(store):
    store.upsert_brief(brief=_brief(1))                      # due Monday 09:00
    store.upsert_brief(brief=_brief(2, cron="0 10 * * *"))   # not due
    store.upsert_brief(brief=_brief(3, enabled=False))       # off
    now = dt.datetime(2026, 9, 7, 9, 0, 10, tzinfo=UTC)
    ran_ids = []

    def runner(b, s, now=None):
        ran_ids.append(b["id"])
        return {"status": "ok" if b["id"] == "b1" else "failed", "error": None, "narrated": True}
    state: dict = {}
    ran = br.tick(store, now=now, runner=runner, state=state)
    assert ran_ids == ["b1"] and ran[0]["id"] == "b1"
    b1 = store.get_brief(brief_id="b1")
    assert b1["last_status"] == "ok" and b1["last_run_at"] == int(now.timestamp() * 1000)
    assert store.get_brief(brief_id="b2")["last_run_at"] is None
    assert state["briefs"]["runs"] == 1 and state["briefs"]["narrations"] == 1
    # Same minute again: nothing runs twice.
    assert br.tick(store, now=now.replace(second=40), runner=runner) == []
    assert ran_ids == ["b1"]


def test_tick_posts_a_failure_and_records_it(store):
    store.upsert_brief(brief=_brief(1))
    now = dt.datetime(2026, 9, 7, 9, 0, tzinfo=UTC)

    def runner(b, s, now=None):
        raise RuntimeError("channel exploded")
    ran = br.tick(store, now=now, runner=runner)
    assert ran and ran[0]["status"] == "failed"
    b1 = store.get_brief(brief_id="b1")
    assert b1["last_status"] == "failed" and "channel exploded" in b1["last_error"]


def test_cap_bounds_how_many_briefs_run(store):
    for i in range(1, 6):
        store.upsert_brief(brief=_brief(i))
    now = dt.datetime(2026, 9, 7, 9, 0, tzinfo=UTC)
    ran_ids = []
    ran = br.tick(store, now=now, cap=2,
                  runner=lambda b, s, now=None: (ran_ids.append(b["id"]) or {"status": "ok"}))
    assert len(ran) == 2 and ran_ids == ["b1", "b2"]
    assert br.BRIEFS_MAX == int(os.environ.get("CLAWMETRY_BRIEFS_MAX", "10"))


def test_scheduler_start_is_gated_and_idempotent(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_BRIEFS", "0")
    assert br.start_scheduler(lambda: None) is False
    monkeypatch.delenv("CLAWMETRY_BRIEFS")
    monkeypatch.setattr(br, "_scheduler_started", True)
    assert br.start_scheduler(lambda: None) is False


# ── routes ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def client(store, monkeypatch):
    from flask import Flask

    import routes.signals as rs
    monkeypatch.setattr(rs, "_ls_call",
                        lambda method, **kw: getattr(store, method)(**kw))
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(rs.bp_signals)
    return app.test_client()


def test_brief_routes(client, store, monkeypatch):
    r = client.get("/api/briefs")
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 0 and body["offered"]["id"] == br.BUILTIN_DAILY_DIGEST_ID
    assert body["offered"]["enabled"] is False and body["max"] == br.BRIEFS_MAX
    assert set(body["channels"]) == set(br.CHANNELS)

    r = client.post("/api/briefs", json={"title": "Costs", "question": "what cost more?",
                                         "cron_expr": "0 9 * * 1", "channel_ref": "slack",
                                         "enabled": True})
    assert r.status_code == 200, r.get_json()
    bid = r.get_json()["brief"]["id"]
    assert client.post("/api/briefs", json={"title": "x"}).status_code == 400

    r = client.post("/api/briefs", json={"id": br.BUILTIN_DAILY_DIGEST_ID, "enabled": True})
    assert r.status_code == 200 and r.get_json()["brief"]["builtin"] is True
    body = client.get("/api/briefs").get_json()
    assert body["count"] == 2 and body["offered"] is None

    monkeypatch.setattr(br, "BRIEFS_MAX", 2)
    r = client.post("/api/briefs", json={"title": "Third", "question": "q", "cron_expr": "0 9 * * *"})
    assert r.status_code == 409
    # Updating an existing one is still allowed at the cap.
    r = client.post("/api/briefs", json={"id": bid, "title": "Costs", "question": "q2",
                                         "cron_expr": "0 9 * * 1", "enabled": False})
    assert r.status_code == 200 and r.get_json()["brief"]["enabled"] is False

    posts = []
    monkeypatch.setattr(br, "_http_post_json", lambda u, p: posts.append((u, p)) or True)
    monkeypatch.setattr(br, "_load_channel_config", dict)
    monkeypatch.setattr(br, "_narrate", lambda b, rows, n: None)
    r = client.post(f"/api/briefs/{br.BUILTIN_DAILY_DIGEST_ID}/run", json={})
    assert r.status_code == 200
    res = r.get_json()
    assert res["ok"] is True and res["result"]["status"] == "ok"
    assert res["brief"]["last_status"] == "ok"

    assert client.post("/api/briefs", json={"title": "t", "question": "q", "cron_expr": "0 9 * * *"},
                       headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.delete(f"/api/briefs/{bid}", headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.delete(f"/api/briefs/{bid}").status_code == 200
    assert client.delete("/api/briefs/nope").status_code == 404
    assert client.post("/api/briefs/nope/run", json={}).status_code == 404


# ── snapshot slice (hosted dashboard) ──────────────────────────────────────

SNAPSHOT_BRIEF_KEYS = {"id", "title", "question", "cron_expr", "tz", "channel_ref", "enabled",
                       "last_run_at", "last_status", "last_error", "created_at", "builtin"}


def test_snapshot_slice_has_the_api_shape_and_offers_the_digest(store):
    store.upsert_brief(brief=_brief(1))
    store.mark_brief_run(brief_id="b1", status="failed", error="channel exploded")
    sl = br.build_snapshot_slice(store)
    assert set(sl) == {"briefs", "count", "max", "channels", "offered", "generated_at"}
    assert sl["count"] == 1 and sl["max"] == br.BRIEFS_MAX
    assert set(sl["channels"]) == set(br.CHANNELS)
    assert sl["offered"]["id"] == br.BUILTIN_DAILY_DIGEST_ID and sl["offered"]["enabled"] is False
    row = sl["briefs"][0]
    assert set(row) == SNAPSHOT_BRIEF_KEYS, sorted(row)
    assert row["last_status"] == "failed" and "channel exploded" in row["last_error"]
    assert row["builtin"] is False
    # Saving the digest removes the offer and marks the row built in.
    store.upsert_brief(brief=dict(br.BUILTIN_DAILY_DIGEST))
    sl = br.build_snapshot_slice(store)
    assert sl["offered"] is None
    assert any(b["builtin"] for b in sl["briefs"])


def test_snapshot_slice_is_capped_and_never_raises(store, monkeypatch):
    for i in range(br.SNAPSHOT_MAX + 7):
        store.upsert_brief(brief=_brief(i))
    assert len(store.list_briefs(limit=500)) == br.SNAPSHOT_MAX + 7
    sl = br.build_snapshot_slice(store)
    assert br.SNAPSHOT_MAX == 50
    assert len(sl["briefs"]) == 50 and sl["count"] == 50
    # A caller cannot lift the cap above the module ceiling.
    assert len(br.build_snapshot_slice(store, limit=500)["briefs"]) == 50
    # A store without the method, or one that raises, yields {} (the
    # snapshot carries an empty slice, never a traceback).
    assert br.build_snapshot_slice(object()) == {}

    class Boom:
        def list_briefs(self, **kw):
            raise RuntimeError("disk gone")
    assert br.build_snapshot_slice(Boom()) == {}


def test_sync_emits_the_briefs_slice_next_to_signal_issues():
    import pathlib
    src = pathlib.Path(__file__).resolve().parents[1].joinpath("clawmetry", "sync.py") \
        .read_text(encoding="utf-8")
    assert '"briefs": _briefs_slice,' in src
    assert "_briefs_snap.build_snapshot_slice(_br_store)" in src
    # Wrapped like the neighbouring slices: a failure logs and moves on.
    assert 'log.debug("snapshot: briefs slice failed: %s", _e_br)' in src
    assert src.index('"signalIssues": _signal_issues_slice,') < src.index('"briefs": _briefs_slice,')


def test_narrator_has_a_brief_prompt():
    from clawmetry import narrator
    assert "brief" in narrator._PROMPTS
    assert "—" not in narrator._PROMPTS["brief"]
