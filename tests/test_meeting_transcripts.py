"""OpenClaw meeting transcripts reach ClawMetry, and the speech stays sealed (#5747).

OpenClaw 2026.9.3 ships a meeting library. Its transcripts land in the SAME
``~/.openclaw/state/openclaw.sqlite`` the run ledger already uses, so this
needed no new path and no new permission -- but it is the first thing ClawMetry
ingests whose payload is other people's speech, including speakers who never
installed it and cannot consent to it leaving a colleague's laptop.

That is the property these tests exist to hold:

  * the reader parses the REAL harness schema (the fixture DDL below is copied
    verbatim from a live ``openclaw.sqlite``, not invented, so a column rename
    upstream fails here instead of silently reading nothing);
  * the store's query withholds speech unless a caller asks for it;
  * content leaves the machine ONLY through the node-key-encrypted blob, and a
    node with no key sends nothing rather than falling back to plaintext.

The product already draws this line for a session title and a session intent
(REQ-OBS-RSO-032: a title is content, not a total). A transcript is further
past it than either.
"""
from __future__ import annotations

import importlib
import os
import sqlite3
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

# Verbatim from a live ~/.openclaw/state/openclaw.sqlite (OpenClaw 2026.9.3,
# 1391f7c). Trimmed only of trailing constraints the reader does not depend on.
_DDL = """
CREATE TABLE meeting_transcript_sessions (
  session_id TEXT NOT NULL, started_at TEXT NOT NULL,
  selector TEXT NOT NULL UNIQUE, export_key TEXT NOT NULL,
  session_slug TEXT NOT NULL, provider_id TEXT NOT NULL, title TEXT,
  source_json TEXT NOT NULL, stopped_at TEXT, metadata_json TEXT,
  export_manifest_json TEXT NOT NULL DEFAULT '{}',
  export_pending_json TEXT NOT NULL DEFAULT '[]',
  next_utterance_seq INTEGER NOT NULL DEFAULT 0,
  created_at_ms INTEGER NOT NULL DEFAULT 0,
  updated_at_ms INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (session_id, started_at));
CREATE TABLE meeting_transcript_utterances (
  session_id TEXT NOT NULL, session_started_at TEXT NOT NULL,
  sequence INTEGER NOT NULL, utterance_id TEXT, started_at TEXT,
  ended_at TEXT, speaker_id TEXT, speaker_label TEXT, text TEXT NOT NULL,
  final INTEGER, metadata_json TEXT,
  PRIMARY KEY (session_id, session_started_at, sequence));
CREATE TABLE meeting_transcript_summaries (
  session_id TEXT NOT NULL, session_started_at TEXT NOT NULL,
  generated_at TEXT, summary_json TEXT, markdown TEXT,
  utterance_count INTEGER NOT NULL,
  PRIMARY KEY (session_id, session_started_at));
"""

_START = "2026-09-09T10:00:00Z"
_STOP = "2026-09-09T10:34:00Z"


def _harness_db(tmp_path, *, with_meetings=True, updated_at_ms=1757400000000):
    p = tmp_path / "openclaw.sqlite"
    con = sqlite3.connect(p)
    if with_meetings:
        con.executescript(_DDL)
        con.execute(
            "INSERT INTO meeting_transcript_sessions (session_id, started_at, "
            "selector, export_key, session_slug, provider_id, title, "
            "source_json, stopped_at, updated_at_ms) VALUES "
            "(?,?,?,?,?,?,?,?,?,?)",
            ["m-1", _START, "zoom:/j/123", "k1", "weekly-sync", "zoom",
             "Weekly sync", "{}", _STOP, updated_at_ms])
        for i, (who, txt) in enumerate([
            ("Ada", "The migration is still failing."),
            ("Grace", "I will take it after standup."),
            ("Ada", "Thanks."),
        ]):
            con.execute(
                "INSERT INTO meeting_transcript_utterances (session_id, "
                "session_started_at, sequence, speaker_label, text, final) "
                "VALUES (?,?,?,?,?,1)", ["m-1", _START, i, who, txt])
        con.execute(
            "INSERT INTO meeting_transcript_summaries (session_id, "
            "session_started_at, markdown, utterance_count) VALUES (?,?,?,?)",
            ["m-1", _START, "# Notes\nGrace owns the migration.", 3])
    else:
        con.execute("CREATE TABLE task_runs (task_id TEXT PRIMARY KEY)")
    con.commit()
    con.close()
    return p


@pytest.fixture
def sync_mod():
    import clawmetry.sync as sync
    return sync


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "cm.duckdb"))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda *a, **k: False)
    s = ls.get_store()
    yield s
    try:
        s.stop(flush=True)
    except Exception:
        pass


# ── the reader parses the real schema ───────────────────────────────────────


def test_reads_a_meeting_from_the_real_harness_schema(sync_mod, tmp_path):
    db = _harness_db(tmp_path)
    rows, watermark = sync_mod._read_meeting_transcripts(db, 0)
    assert len(rows) == 1
    r = rows[0]
    assert r["session_id"] == "m-1"
    assert r["title"] == "Weekly sync"
    assert r["provider_id"] == "zoom"
    assert r["utterance_count"] == 3
    assert r["speaker_count"] == 2, "Ada and Grace"
    assert r["duration_ms"] == 34 * 60 * 1000
    assert "Grace owns the migration" in r["summary_markdown"]
    assert "Ada: The migration is still failing." in r["transcript_text"]
    assert watermark == 1757400000000


def test_a_pre_2026_9_3_harness_is_a_skip_not_an_error(sync_mod, tmp_path):
    """The tables simply do not exist on an older OpenClaw."""
    db = _harness_db(tmp_path, with_meetings=False)
    rows, watermark = sync_mod._read_meeting_transcripts(db, 0)
    assert rows == [] and watermark == 0


def test_the_watermark_skips_what_it_already_read(sync_mod, tmp_path):
    db = _harness_db(tmp_path, updated_at_ms=1000)
    assert sync_mod._read_meeting_transcripts(db, 0)[0]
    assert sync_mod._read_meeting_transcripts(db, 1001)[0] == []


def test_a_meeting_still_being_captured_overwrites_rather_than_duplicates(
        sync_mod, store, tmp_path):
    db = _harness_db(tmp_path)
    rows, _ = sync_mod._read_meeting_transcripts(db, 0)
    for _ in range(3):
        store.ingest_meeting_transcript(rows[0], node_id="n1")
    assert len(store.query_meeting_transcripts()) == 1


def test_duration_never_raises_on_a_missing_or_odd_timestamp(sync_mod):
    assert sync_mod._meeting_duration_ms(None, _STOP) == 0
    assert sync_mod._meeting_duration_ms(_START, None) == 0
    assert sync_mod._meeting_duration_ms("not-a-date", _STOP) == 0
    assert sync_mod._meeting_duration_ms(_STOP, _START) == 0, "never negative"


# ── the speech is withheld by default ───────────────────────────────────────


def test_the_default_query_returns_no_speech(sync_mod, store, tmp_path):
    """A caller has to ASK for the words. A default that ships transcript text
    to every incidental reader is how content reaches a surface nobody
    audited."""
    rows, _ = sync_mod._read_meeting_transcripts(_harness_db(tmp_path), 0)
    store.ingest_meeting_transcript(rows[0], node_id="n1")
    got = store.query_meeting_transcripts()[0]
    assert "transcript_text" not in got and "summary_markdown" not in got
    # But the operational signal is all there.
    assert got["utterance_count"] == 3 and got["speaker_count"] == 2
    assert got["duration_ms"] > 0 and got["title"] == "Weekly sync"

    full = store.query_meeting_transcripts(include_text=True)[0]
    assert "Ada: The migration is still failing." in full["transcript_text"]


# ── content leaves ONLY sealed ──────────────────────────────────────────────


def test_speech_is_sealed_with_the_node_key(sync_mod, tmp_path):
    rows, _ = sync_mod._read_meeting_transcripts(_harness_db(tmp_path), 0)
    key = sync_mod.generate_encryption_key()
    blob = sync_mod.seal_meeting_transcript(rows[0], key)
    assert blob, "a keyed node must seal the content"
    assert "The migration is still failing" not in str(blob)
    assert "Weekly sync" not in str(blob)


def test_a_node_with_no_key_sends_nothing_rather_than_plaintext(
        sync_mod, tmp_path):
    """The rule that makes the design safe: no key is not a licence to fall
    back to cleartext."""
    rows, _ = sync_mod._read_meeting_transcripts(_harness_db(tmp_path), 0)
    assert sync_mod.seal_meeting_transcript(rows[0], None) is None
    assert sync_mod.seal_meeting_transcript(rows[0], "") is None


def test_sealing_never_raises_and_never_leaks_on_failure(sync_mod):
    assert sync_mod.seal_meeting_transcript({}, "k") is None
    assert sync_mod.seal_meeting_transcript(None, "k") is None


def test_the_ingest_is_actually_called_by_the_daemon():
    """A reader nothing calls observes nothing.

    Both daemon paths that run the run-ledger ingest must run this one too,
    or the table stays empty on every real install while the tests pass.
    """
    src = open(os.path.join(REPO, "clawmetry", "sync.py"),
               encoding="utf-8").read()
    calls = src.count("sync_meeting_transcripts(config, state, paths)")
    assert calls >= 2, (
        f"wired into only {calls} of the 2 daemon cycles that ingest the "
        "run ledger from the same database"
    )


def test_the_sealed_payload_carries_the_content_fields_and_no_others(
        sync_mod, tmp_path):
    """Counts and timings are NOT content and belong in the cleartext row;
    putting them in the blob too would hide the operational signal behind a
    key the service does not have."""
    rows, _ = sync_mod._read_meeting_transcripts(_harness_db(tmp_path), 0)
    key = sync_mod.generate_encryption_key()
    blob = sync_mod.seal_meeting_transcript(rows[0], key)
    payload = sync_mod.decrypt_payload(blob, key) if hasattr(
        sync_mod, "decrypt_payload") else None
    if payload is None:
        pytest.skip("no decrypt helper exposed in this build")
    assert set(payload) <= {"title", "summary_markdown", "transcript_text",
                            "selector"}
    assert "utterance_count" not in payload and "duration_ms" not in payload
