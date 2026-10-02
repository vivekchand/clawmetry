"""OpenClaw 2026.9.x SQLite transcript store -> JSONL mirror.

OpenClaw 2026.9.x stopped writing live transcripts to
``~/.openclaw/agents/<agent>/sessions/<sid>.jsonl``. They now live in a
per-agent SQLite database::

    ~/.openclaw/agents/<agent>/agent/openclaw-agent.sqlite
        session_nodes              session_key -> entry_json (the old
                                   sessions.json entry, byte for byte)
        session_windows            one row per session id
        transcript_events          (session_id, seq) -> event_json, or
                                   event_zstd for large events (that column
                                   exists from 2026.9.6 / agent schema 23;
                                   earlier stores carry event_json only)
        trajectory_runtime_events  the old <sid>.trajectory.jsonl lines

The event JSON is the SAME shape the ``.jsonl`` lines had (``type`` /
``id`` / ``parentId`` / ``timestamp`` / ``message``), so rather than teach
every JSONL consumer in the daemon a second storage format, this module
materialises the SQLite store back into the directory layout they already
read: ``<sid>.jsonl``, ``<sid>.trajectory.jsonl`` and ``sessions.json`` under
``~/.clawmetry/openclaw-mirror/agents/<agent>/sessions/``. The daemon then
points its ``sessions_dir`` at the mirror and the whole existing pipeline
(events, session rows, sub-agent mapping, context capture) works unchanged.

Read-only on the OpenClaw side: the database is opened ``mode=ro`` and
nothing is ever written under ``~/.openclaw``.

Verified against a live OpenClaw 2026.9.7 install (schema_version 24) on
2026-10-02, and against a live 2026.9.2 install (schema_version 19) on the
same day - the version CI's ``setup-openclaw`` pins.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from clawmetry import nonsecret_hash

log = logging.getLogger("clawmetry.openclaw_sqlite")

AGENT_DB_NAME = "openclaw-agent.sqlite"

# Bounds for one mirror pass so a first-run backfill of a large store can
# never starve the daemon heartbeat. The pass resumes where it stopped.
MAX_ROWS_PER_PASS = 20000
MAX_SECONDS_PER_PASS = 8.0

_STATE_KEY = "openclaw_sqlite_mirror"

# (db mtime_ns, db size, wal mtime_ns, wal size) per db path at the end of
# the last COMPLETE pass. Unchanged fingerprint == nothing to do.
_fingerprints: dict[str, tuple] = {}
_zstd_warned = False


def agent_db_path(openclaw_dir, agent_id: str = "main") -> Path:
    return Path(openclaw_dir) / "agents" / agent_id / "agent" / AGENT_DB_NAME


def mirror_root() -> Path:
    return Path(os.path.expanduser("~/.clawmetry/openclaw-mirror"))


def mirror_sessions_dir(agent_id: str = "main") -> Path:
    return mirror_root() / "agents" / agent_id / "sessions"


def has_transcript_store(openclaw_dir, agent_id: str = "main") -> bool:
    """True when this OpenClaw install keeps transcripts in SQLite."""
    try:
        return agent_db_path(openclaw_dir, agent_id).is_file()
    except OSError:
        return False


def _zstd_decompress(blob: bytes) -> bytes | None:
    """Decompress one zstd frame, or None when no decoder is available.
    Python 3.14+ ships one in the stdlib; older Pythons need ``zstandard``."""
    try:
        from compression import zstd as _zstd  # Python 3.14+
        return _zstd.decompress(blob)
    except ImportError:
        pass
    try:
        import zstandard
        return zstandard.ZstdDecompressor().decompressobj().decompress(blob)
    except ImportError:
        pass
    try:
        import pyzstd
        return pyzstd.decompress(blob)
    except ImportError:
        return None


def _event_text(event_json, event_zstd) -> str | None:
    """The event's JSON text, or None when it cannot be decoded yet."""
    global _zstd_warned
    if event_json is not None:
        return event_json
    if event_zstd is None:
        return ""
    raw = _zstd_decompress(bytes(event_zstd))
    if raw is None:
        if not _zstd_warned:
            _zstd_warned = True
            log.warning(
                "openclaw: a transcript event is zstd-compressed and this "
                "Python has no zstd decoder. Run `pip install zstandard` "
                "(or use Python 3.14+); the session resumes from this event "
                "once a decoder is available."
            )
        return None
    return raw.decode("utf-8", errors="replace")


def _loads(text):
    """``json.loads`` that answers None instead of raising."""
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def _one_line(text: str) -> str | None:
    """Re-serialise as a single pure-ASCII JSON line (the JSONL readers open
    files with the platform default encoding), or None if it isn't JSON."""
    obj = _loads(text)
    return None if obj is None else json.dumps(obj, separators=(",", ":"))


def _line_key(line: str) -> str:
    """Identity of a mirrored line: the event's own id when it has one."""
    obj = _loads(line)
    if isinstance(obj, dict) and obj.get("id"):
        return str(obj["id"])
    return nonsecret_hash.sha1(line.encode("utf-8", "replace")).hexdigest()


def _fingerprint(db: Path) -> tuple:
    out = []
    for p in (db, Path(str(db) + "-wal")):
        try:
            st = p.stat()
            out += [st.st_mtime_ns, st.st_size]
        except OSError:
            out += [0, 0]
    return tuple(out)


def _connect(db: Path):
    import sqlite3
    conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=5)
    conn.execute("PRAGMA query_only=ON")
    return conn


def _table_exists(conn, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _column_exists(conn, table: str, column: str) -> bool:
    """True when ``table`` has ``column``.

    ``transcript_events.event_zstd`` is not in every store this module can
    be pointed at: measured across the releases, it arrives with OpenClaw
    2026.9.6 (agent schema 23) and is absent from 2026.9.2 - 2026.9.5
    (schema 19, 19, 19, 21). Naming it unconditionally raised ``no such
    column: event_zstd``, which ``sync_mirror`` caught and turned into a
    whole pass returning None - i.e. on those versions the mirror silently
    produced nothing rather than the transcript it had in hand.
    """
    try:
        return any(
            row[1] == column
            for row in conn.execute(f'PRAGMA table_info("{table}")')
        )
    except Exception:  # noqa: BLE001 - a probe must never break the pass
        return False


def _mirror_transcript(conn, sid: str, out_dir: Path, cur: dict, budget: dict) -> int:
    """Append this session's new transcript events to ``<sid>.jsonl``.

    ``cur`` is the session's persisted cursor ``{"seq", "n", "last"}``: the
    highest mirrored seq, how many rows existed at or below it, and the event
    id at it. If OpenClaw rewrote the transcript underneath us (compaction,
    rewind) that prefix no longer matches; we then re-walk the session from
    the start and append only events the mirror has not seen, so the mirror
    stays append-only and the daemon's line cursors stay valid.
    """
    fpath = out_dir / f"{sid}.jsonl"
    seq = int(cur.get("seq", -1))
    if seq >= 0 and not fpath.is_file():
        seq = -1  # mirror file was removed; rebuild it
    seen: set | None = None
    if seq >= 0:
        n, = conn.execute(
            "SELECT count(*) FROM transcript_events WHERE session_id=? AND seq<=?",
            (sid, seq),
        ).fetchone()
        row = conn.execute(
            "SELECT event_id FROM transcript_event_identities"
            " WHERE session_id=? AND seq=?", (sid, seq),
        ).fetchone() if cur.get("last") else None
        last = row[0] if row else None
        if n != int(cur.get("n", -1)) or (cur.get("last") and last != cur.get("last")):
            seq = -1
    if seq < 0 and fpath.is_file():
        seen = set()
        with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    seen.add(_line_key(line))

    # Two whole literals rather than one interpolated query: a store whose
    # schema predates event_zstd (see _column_exists) is read without that
    # column, and the NULL keeps the row shape below identical either way.
    if _column_exists(conn, "transcript_events", "event_zstd"):
        rows = conn.execute(
            "SELECT seq, event_json, event_zstd FROM transcript_events"
            " WHERE session_id=? AND seq>? ORDER BY seq", (sid, seq),
        )
    else:
        rows = conn.execute(
            "SELECT seq, event_json, NULL FROM transcript_events"
            " WHERE session_id=? AND seq>? ORDER BY seq", (sid, seq),
        )
    written = 0
    lines: list[str] = []
    last_seq = seq
    for r_seq, r_json, r_zstd in rows:
        if budget["rows"] <= 0 or time.monotonic() > budget["deadline"]:
            budget["complete"] = False
            break
        text = _event_text(r_json, r_zstd)
        if text is None:
            # Undecodable for now: stop here so order is preserved and the
            # event is picked up once a zstd decoder is installed.
            budget["complete"] = False
            break
        last_seq = r_seq
        budget["rows"] -= 1
        line = _one_line(text) if text else None
        if line is None:
            continue
        if seen is not None:
            key = _line_key(line)
            if key in seen:
                continue
            seen.add(key)
        lines.append(line)
    if lines:
        with open(fpath, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        written = len(lines)
    if last_seq != seq or seq < 0:
        n, = conn.execute(
            "SELECT count(*) FROM transcript_events WHERE session_id=? AND seq<=?",
            (sid, last_seq),
        ).fetchone()
        row = conn.execute(
            "SELECT event_id FROM transcript_event_identities"
            " WHERE session_id=? AND seq=?", (sid, last_seq),
        ).fetchone()
        cur.update({"seq": last_seq, "n": n, "last": row[0] if row else ""})
    return written


def _mirror_trajectory(conn, sid: str, out_dir: Path, cur: dict, budget: dict) -> int:
    """Append new ``context.compiled`` trajectory events to
    ``<sid>.trajectory.jsonl`` — the only trajectory event type the daemon
    reads; the rest duplicate the transcript."""
    fpath = out_dir / f"{sid}.trajectory.jsonl"
    seq = int(cur.get("tseq", -1))
    if seq >= 0 and not fpath.is_file():
        seq = -1
    rows = conn.execute(
        "SELECT seq, event_json FROM trajectory_runtime_events"
        " WHERE session_id=? AND seq>? ORDER BY seq", (sid, seq),
    )
    lines: list[str] = []
    last_seq = seq
    for r_seq, r_json in rows:
        if budget["rows"] <= 0 or time.monotonic() > budget["deadline"]:
            budget["complete"] = False
            break
        last_seq = r_seq
        if not r_json or '"context.compiled"' not in r_json:
            continue
        budget["rows"] -= 1
        obj = _loads(r_json)
        if not isinstance(obj, dict):
            continue
        # The event's own ``seq`` restarts on every run attempt (it is always
        # 2 for context.compiled), and the daemon ids these rows by it. The
        # table's seq is unique per session; ``sourceSeq`` keeps the original.
        obj["seq"] = r_seq
        lines.append(json.dumps(obj, separators=(",", ":")))
    if lines:
        with open(fpath, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
    cur["tseq"] = last_seq
    return len(lines)


def _write_index(conn, out_dir: Path) -> None:
    """Rebuild ``sessions.json`` (session key -> entry) from session_nodes.
    ``entry_json`` is the legacy index entry; we only fill the few fields the
    daemon reads that OpenClaw now keeps in columns instead."""
    windows: dict[str, dict] = {}
    for sid, model, provider, chat_type, display, status in conn.execute(
        "SELECT session_id, model, model_provider, chat_type, display_name, status"
        " FROM session_windows"
    ):
        windows[sid] = {"model": model, "modelProvider": provider,
                        "chatType": chat_type, "displayName": display,
                        "status": status}
    index: dict[str, dict] = {}
    for key, sid, entry_json in conn.execute(
        "SELECT session_key, current_session_id, entry_json FROM session_nodes"
    ):
        entry = _loads(entry_json) if entry_json else {}
        if not isinstance(entry, dict):
            entry = {}
        entry.setdefault("sessionId", sid)
        for k, v in (windows.get(entry["sessionId"]) or {}).items():
            if v and not entry.get(k):
                entry[k] = v
        entry.setdefault(
            "sessionFile", str(out_dir / f"{entry['sessionId']}.jsonl"))
        index[key] = entry
    text = json.dumps(index, separators=(",", ":"), sort_keys=True)
    target = out_dir / "sessions.json"
    try:
        if target.is_file() and target.read_text(encoding="utf-8") == text:
            return
    except OSError:
        pass
    tmp = out_dir / "sessions.json.tmp"
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)


def sync_mirror(openclaw_dir, state: dict, agent_id: str = "main") -> str | None:
    """Bring the JSONL mirror for ``agent_id`` up to date.

    Returns the mirror sessions directory, or None when this install has no
    SQLite transcript store (or it cannot be read). Never raises. Cursors
    live in ``state["openclaw_sqlite_mirror"]``; the caller persists state.
    """
    db = agent_db_path(openclaw_dir, agent_id)
    try:
        if not db.is_file():
            return None
        out_dir = mirror_sessions_dir(agent_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        fp = _fingerprint(db)
        if _fingerprints.get(str(db)) == fp and (out_dir / "sessions.json").is_file():
            return str(out_dir)
        cursors: dict = state.setdefault(_STATE_KEY, {}).setdefault(agent_id, {})
        budget = {"rows": MAX_ROWS_PER_PASS,
                  "deadline": time.monotonic() + MAX_SECONDS_PER_PASS,
                  "complete": True}
        conn = _connect(db)
        try:
            if not _table_exists(conn, "transcript_events"):
                return None
            has_traj = _table_exists(conn, "trajectory_runtime_events")
            written = 0
            sids = [r[0] for r in conn.execute(
                "SELECT session_id FROM session_windows"
                " ORDER BY coalesce(transcript_updated_at, updated_at) DESC")]
            for sid in sids:
                if budget["rows"] <= 0 or time.monotonic() > budget["deadline"]:
                    budget["complete"] = False
                    break
                cur = cursors.setdefault(sid, {})
                written += _mirror_transcript(conn, sid, out_dir, cur, budget)
                if has_traj:
                    written += _mirror_trajectory(conn, sid, out_dir, cur, budget)
            _write_index(conn, out_dir)
        finally:
            conn.close()
        if budget["complete"]:
            _fingerprints[str(db)] = fp
        if written:
            log.info("openclaw: mirrored %d new SQLite transcript line(s) "
                     "for agent %s", written, agent_id)
        return str(out_dir)
    except Exception as e:  # noqa: BLE001 - a daemon sync pass must never raise
        log.warning("openclaw: SQLite transcript mirror failed: %s", e)
        return None
