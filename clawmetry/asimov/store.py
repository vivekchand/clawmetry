"""Free Asimov projections on the existing daemon-owned DuckDB connection.

This module consumes the public robotics journal contract. It does not import
the private robotics implementation or open a database connection.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

log = logging.getLogger(__name__)
RUN_ID = re.compile(r"[0-9a-f]{32}\Z")
JOURNAL = re.compile(r"([0-9a-f]{32})(?:\.([0-9]{8}))?\.jsonl\Z")
ASIMOV_SOURCES = frozenset({"asimov_sdk", "asimov_recording"})
JUMPER_SOURCES = frozenset({"jumper_native", "jumper_app", "jumper_recording"})
SOURCES = ASIMOV_SOURCES | JUMPER_SOURCES
MAX_LINE = 65536
DDL = (
    """CREATE TABLE IF NOT EXISTS asimov_events (
        run_id VARCHAR, sequence BIGINT, wall_time_ns BIGINT, kind VARCHAR,
        event_json VARCHAR, PRIMARY KEY(run_id, sequence))""",
    """CREATE TABLE IF NOT EXISTS asimov_runs (
        run_id VARCHAR PRIMARY KEY, robot_id VARCHAR, source_kind VARCHAR,
        environment VARCHAR, started_ns BIGINT, updated_ns BIGINT,
        last_sequence BIGINT, event_count BIGINT, dropped_total BIGINT,
        start_json VARCHAR, observation_json VARCHAR, observation_ns BIGINT,
        observation_sequence BIGINT, lifecycle VARCHAR, lifecycle_sequence BIGINT,
        health_json VARCHAR)""",
    """CREATE TABLE IF NOT EXISTS asimov_cursors (
        source VARCHAR PRIMARY KEY, identity VARCHAR, byte_offset BIGINT,
        discarding BOOLEAN, invalid_count BIGINT)""",
    """CREATE TABLE IF NOT EXISTS asimov_source_support (
        source VARCHAR PRIMARY KEY, registry VARCHAR, ignored BOOLEAN)""",
    "CREATE INDEX IF NOT EXISTS asimov_runs_updated ON asimov_runs(updated_ns, run_id)",
)


def _integer(value, minimum=0):
    if type(value) is bool or not isinstance(value, (int, str)):
        raise ValueError("Invalid Asimov counter")
    if isinstance(value, str) and (not value.isascii() or not value.isdigit()):
        raise ValueError("Invalid Asimov counter")
    result = int(value)
    if not minimum <= result < 2**63:
        raise ValueError("Invalid Asimov counter")
    return result


def validate(event, run_id):
    if not isinstance(event, dict) or event.get("schema") != "clawmetry.robotics.v1":
        raise ValueError("Unsupported Asimov event schema")
    if event.get("run_id") != run_id or not RUN_ID.fullmatch(run_id):
        raise ValueError("Invalid Asimov run identifier")
    _integer(event.get("sequence"), 1)
    _integer(event.get("wall_time_ns"))
    _integer(event.get("monotonic_ns"))
    _integer(event.get("dropped_total"))
    if (not isinstance(event.get("robot_id"), str) or not event["robot_id"]
            or len(event["robot_id"]) > 200
            or event.get("environment") not in {"hardware", "simulation"}
            or not isinstance(event.get("kind"), str) or not event["kind"]
            or len(event["kind"]) > 80 or not isinstance(event.get("data"), dict)):
        raise ValueError("Invalid Asimov event fields")
    json.dumps(event, allow_nan=False)
    return event


class AsimovLocalStore:
    def __init__(self, store, *, initialize=False):
        self.store = store
        self._scan_cursor = 0
        self._health_seen = {}
        self._source_registry = json.dumps(sorted(SOURCES), separators=(",", ":"))
        if initialize:
            if getattr(store, "_read_only", True):
                raise RuntimeError("Asimov ingestion requires the daemon writer")
            with store._write_lock:
                for statement in DDL:
                    store._conn.execute(statement)

    def _exists(self):
        return bool(self.store._fetch(
            "SELECT 1 FROM information_schema.tables WHERE table_name='asimov_runs'", []))

    def ingest(self, directory, *, max_lines=2000, max_bytes=4 * 1024 * 1024):
        """Bounded tail pass. Evidence and source cursor commit together."""
        if getattr(self.store, "_read_only", True):
            raise RuntimeError("Asimov ingestion requires the daemon writer")
        directory = Path(directory)
        if not directory.is_dir():
            return 0
        candidates = []
        for path in directory.iterdir():
            match = JOURNAL.fullmatch(path.name)
            if match and not path.is_symlink() and path.is_file():
                candidates.append((match[1], int(match[2] or 0), path))
        # A segment without a header can only be attributed after its first file.
        candidates.sort(key=lambda item: (item[0], item[1]))
        total = 0
        if candidates:
            start = self._scan_cursor % len(candidates)
            selected = (candidates[start:] + candidates[:start])[:16]
            remaining_lines, remaining_bytes, processed = max_lines, max_bytes, 0
            for run_id, _, path in selected:
                if remaining_lines <= 0 or remaining_bytes <= 0:
                    break
                count, used, lines = self._tail(path, run_id,
                                               max_lines=min(128, remaining_lines),
                                               max_bytes=min(256 * 1024, remaining_bytes))
                total += count
                remaining_bytes -= used
                remaining_lines -= lines
                processed += 1
            self._scan_cursor = (start + processed) % len(candidates)
        self._health(directory)
        return total

    def _tail(self, path, run_id, *, max_lines, max_bytes):
        from clawmetry.local_store import _txn
        alerts = []
        stat = path.stat()
        identity = str(stat.st_dev) + ":" + str(stat.st_ino)
        with self.store._write_lock:
            conn = self.store._conn
            row = conn.execute("SELECT identity,byte_offset,discarding,invalid_count "
                               "FROM asimov_cursors WHERE source=?", [str(path)]).fetchone()
            support = conn.execute("SELECT registry,ignored FROM asimov_source_support WHERE source=?",
                                   [str(path)]).fetchone()
            reclassify = row is None or support is None or support[0] != self._source_registry
            offset, discarding, invalid = (row[1], row[2], row[3]) if row else (0, False, 0)
            ignored = bool(support[1]) if support and not reclassify else False
            if row and (row[0] != identity or stat.st_size < offset):
                offset, discarding = 0, False
                ignored = False
            if reclassify:
                # Older collectors consumed unsupported headers to EOF. A
                # durable registry marker makes a support change replay once,
                # across bounded passes and restarts, without losing evidence.
                offset, discarding, invalid = 0, False, 0
            if offset == stat.st_size and not reclassify:
                return 0, 0, 0
            if ignored:
                # Already classified for this inode and support registry.
                # Appending to an unrelated source must not parse its body.
                with _txn(conn):
                    conn.execute("UPDATE asimov_cursors SET byte_offset=? WHERE source=?",
                                 [stat.st_size, str(path)])
                return 0, 0, 0
            count, used, lines = 0, 0, 0
            with path.open("rb") as source, _txn(conn):
                source.seek(offset)
                for _ in range(max_lines):
                    if used >= max_bytes:
                        break
                    start = source.tell()
                    raw = source.readline(MAX_LINE + 1)
                    if not raw:
                        break
                    used += len(raw)
                    lines += 1
                    if discarding or len(raw) > MAX_LINE:
                        # Drain an oversized record without allocating its full line.
                        if not discarding:
                            invalid += 1
                        discarding = not raw.endswith(b"\n")
                        offset = source.tell()
                        continue
                    if not raw.endswith(b"\n"):
                        source.seek(start)  # writer has not completed this record
                        break
                    offset = source.tell()
                    try:
                        event = validate(json.loads(raw), run_id)
                        if event["kind"] != "run.started" and not conn.execute(
                                "SELECT 1 FROM asimov_runs WHERE run_id=?", [run_id]).fetchone():
                            # A copied segment can arrive before its base header.
                            # Keep its cursor until source attribution is available.
                            offset = start
                            break
                        if event["kind"] == "run.started" and event["data"].get("source_kind") not in SOURCES:
                            # A run cannot switch platforms later. Do not parse an
                            # unrelated SO-101 or simulator history on every pass.
                            offset = stat.st_size
                            ignored = True
                            break
                        inserted = self._insert(conn, event)
                        count += inserted
                        if inserted and event["kind"] == "guard.incident":
                            alerts.append(event)
                    except (ValueError, TypeError, UnicodeError, OverflowError, RecursionError):
                        invalid += 1
                conn.execute("INSERT OR REPLACE INTO asimov_cursors VALUES (?,?,?,?,?)",
                             [str(path), identity, offset, discarding, invalid])
                conn.execute("INSERT OR REPLACE INTO asimov_source_support VALUES (?,?,?)",
                             [str(path), self._source_registry, ignored])
            if invalid > (row[3] if row else 0):
                log.warning("Skipped invalid Asimov journal records")
        # Network notification work must not hold the DuckDB transaction/lock.
        if alerts:
            from clawmetry.physical_ai.alerts import dispatch
            for event in alerts:
                dispatch(self.store, event)
        return count, used, lines

    def _insert(self, conn, event):
        run_id, data = event["run_id"], event["data"]
        sequence = _integer(event["sequence"], 1)
        stamp = _integer(event["wall_time_ns"])
        kind = event["kind"]
        run = conn.execute("SELECT robot_id,source_kind,environment FROM asimov_runs "
                           "WHERE run_id=?", [run_id]).fetchone()
        if run is None:
            if kind != "run.started" or data.get("source_kind") not in SOURCES:
                return 0  # journal belongs to another robotics integration
            raw_start = json.dumps(data, separators=(",", ":"), allow_nan=False)
            conn.execute("INSERT INTO asimov_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         [run_id, event["robot_id"], data["source_kind"], event["environment"],
                          stamp, stamp, 0, 0, 0, raw_start, None, None, 0,
                          "run.started", sequence, None])
            run = (event["robot_id"], data["source_kind"], event["environment"])
        if run[0] != event["robot_id"] or run[2] != event["environment"]:
            raise ValueError("Conflicting Asimov identity")
        if kind == "run.started" and data.get("source_kind") != run[1]:
            raise ValueError("Conflicting Asimov source")
        existing = conn.execute("SELECT event_json FROM asimov_events "
                                "WHERE run_id=? AND sequence=?", [run_id, sequence]).fetchone()
        raw = json.dumps(event, separators=(",", ":"), sort_keys=True, allow_nan=False)
        if existing:
            if existing[0] != raw:
                raise ValueError("Conflicting Asimov event identity")
            return 0
        conn.execute("INSERT INTO asimov_events VALUES (?,?,?,?,?)",
                     [run_id, sequence, stamp, kind, raw])
        conn.execute("UPDATE asimov_runs SET updated_ns=greatest(updated_ns,?), "
                     "last_sequence=greatest(last_sequence,?),event_count=event_count+1, "
                     "dropped_total=greatest(dropped_total,?) WHERE run_id=?",
                     [stamp, sequence, _integer(event["dropped_total"]), run_id])
        if kind == "observation":
            conn.execute("UPDATE asimov_runs SET observation_json=?,observation_ns=?, "
                         "observation_sequence=? WHERE run_id=? AND observation_sequence<?",
                         [json.dumps(data, separators=(",", ":")), stamp, sequence, run_id, sequence])
        if kind in {"run.started", "run.ended", "telemetry.lost", "telemetry.restored"}:
            conn.execute("UPDATE asimov_runs SET lifecycle=?,lifecycle_sequence=? "
                         "WHERE run_id=? AND lifecycle_sequence<=?", [kind, sequence, run_id, sequence])
        return 1

    def _health(self, directory):
        rows = self.store._fetch("SELECT run_id FROM asimov_runs ORDER BY updated_ns DESC LIMIT 100", [])
        for (run_id,) in rows:
            path = directory / (run_id + ".status.json")
            if not path.is_file() or path.is_symlink():
                continue
            try:
                stat = path.stat()
                signature = (stat.st_ino, stat.st_mtime_ns, stat.st_size)
                if stat.st_size > MAX_LINE or self._health_seen.get(str(path)) == signature:
                    continue
                health = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(health, dict) or health.get("run_id") != run_id:
                    continue
                # Do not copy unbounded error details or paths into a cloud snapshot.
                safe = {}
                for key in ("active", "incomplete", "flushed"):
                    value = health.get(key)
                    safe[key] = value if type(value) is bool else None
                for key in ("queued", "written", "dropped_total", "errors"):
                    value = health.get(key)
                    safe[key] = _integer(value) if value is not None else None
                dropped = _integer(health.get("dropped_total", 0))
                with self.store._write_lock:
                    self.store._conn.execute("UPDATE asimov_runs SET health_json=?, "
                                             "dropped_total=greatest(dropped_total,?) WHERE run_id=?",
                                             [json.dumps(safe), dropped, run_id])
                if len(self._health_seen) >= 4096:
                    self._health_seen.clear()
                self._health_seen[str(path)] = signature
            except (ValueError, OSError, TypeError, RecursionError):
                log.warning("Could not read Asimov recorder health")

    def runs(self, *, limit=20, robot_id=None, before_ns=None, before_run_id=None, sources=ASIMOV_SOURCES):
        limit = max(1, min(100, int(limit)))
        if not self._exists():
            return {"runs": [], "has_more": False, "next_cursor": None}
        selected = sorted(sources & SOURCES)
        if not selected:
            return {"runs": [], "has_more": False, "next_cursor": None}
        where, args = ["source_kind IN (" + ",".join("?" for _ in selected) + ")"], list(selected)
        if robot_id is not None:
            if not isinstance(robot_id, str) or len(robot_id) > 200:
                raise ValueError("Invalid robot identifier")
            where.append("robot_id=?")
            args.append(robot_id)
        if before_ns is not None:
            stamp = _integer(before_ns)
            if before_run_id is None or not RUN_ID.fullmatch(str(before_run_id)):
                raise ValueError("A run cursor requires its run identifier")
            where.append("(updated_ns,run_id)<(?,?)")
            args.extend([stamp, before_run_id])
        query = "SELECT * FROM asimov_runs"
        if where:
            query += " WHERE " + " AND ".join(where)
        rows = self.store._fetch(query + " ORDER BY updated_ns DESC,run_id DESC LIMIT ?", args + [limit + 1])
        invalid = dict(self.store._fetch(
            "SELECT regexp_extract(source, '([0-9a-f]{32})(?:\\.[0-9]{8})?\\.jsonl$', 1), "
            "sum(invalid_count) FROM asimov_cursors WHERE invalid_count>0 GROUP BY 1", []))
        now = time.time_ns()
        result = []
        for row in rows[:limit]:
            observation = json.loads(row[10]) if row[10] else None
            age = max(0, (now - row[11]) / 1e9) if row[11] else None
            status = "recorded" if row[2].endswith("_recording") else (
                "ended" if row[13] == "run.ended" else
                "disconnected" if row[13] == "telemetry.lost" else
                "live" if age is not None and 0 <= now - row[11] < 5_000_000_000 else "stale")
            health = json.loads(row[15]) if row[15] else {}
            health["invalid_records"] = int(invalid.get(row[0], 0))
            health["incomplete"] = bool(health.get("incomplete") or health["invalid_records"]
                                        or row[8] or health.get("errors"))
            result.append({"run_id": row[0], "robot_id": row[1], "source_kind": row[2],
                           "environment": row[3], "started_ns": str(row[4]), "updated_ns": str(row[5]),
                           "last_sequence": row[6], "event_count": row[7], "dropped_total": row[8],
                           "start": json.loads(row[9]), "observation": observation,
                           "observation_age_s": age, "status": status,
                           "observation_received_at_ns": str(row[11]) if row[11] is not None else None,
                           "health": health,
                           "command_outcome": "unknown", "hardware_verified": False})
        cursor = {"before_ns": str(rows[limit-1][5]), "before_run_id": rows[limit-1][0]} if len(rows) > limit else None
        return {"runs": result, "has_more": len(rows) > limit, "next_cursor": cursor}

    def events(self, *, run_id, after=0, limit=200, sources=ASIMOV_SOURCES):
        if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
            raise ValueError("Invalid Asimov run identifier")
        after, limit = _integer(after), max(1, min(500, int(limit)))
        if not self._exists():
            return {"events": [], "has_more": False, "next_after": after}
        selected = sorted(sources & SOURCES)
        if not selected or not self.store._fetch(
                "SELECT 1 FROM asimov_runs WHERE run_id=? AND source_kind=ANY(?)",
                [run_id, selected]):
            return {"events": [], "has_more": False, "next_after": after}
        rows = self.store._fetch("SELECT sequence,event_json FROM asimov_events "
                                 "WHERE run_id=? AND sequence>? ORDER BY sequence LIMIT ?",
                                 [run_id, after, limit + 1])
        return {"events": [json.loads(row[1]) for row in rows[:limit]],
                "has_more": len(rows) > limit,
                "next_after": rows[min(limit, len(rows))-1][0] if rows else after}

    def snapshot(self, *, sources=ASIMOV_SOURCES):
        # No raw journal scans or full-history replay in the snapshot builder.
        result = self.runs(limit=8, sources=sources)
        result["schema"] = "clawmetry.asimov.snapshot.v1" if sources == ASIMOV_SOURCES else "clawmetry.physical_ai.snapshot.v1"
        if sources != ASIMOV_SOURCES:
            result["navigation"] = [{"label": "Physical AI", "href": "/physical-ai", "view_group": "physical_ai"}]
        result["generated_at_ns"] = str(time.time_ns())
        result["observation_only"] = True
        result["events"] = {}
        result["trace_window"] = {}
        # A retained source event may approach 64 KiB. Keep the shared cloud
        # snapshot inexpensive even when eight robots have detailed feedback.
        while len(json.dumps(result, separators=(",", ":")).encode("utf-8")) > 60 * 1024:
            if not result["runs"]:
                break
            result["runs"].pop()
            result["has_more"] = True
        if result["has_more"] and result["runs"]:
            last = result["runs"][-1]
            result["next_cursor"] = {"before_ns": last["updated_ns"],
                                     "before_run_id": last["run_id"]}
        for run in result["runs"]:
            run_id = run["run_id"]
            rows = self.store._fetch(
                "SELECT event_json FROM asimov_events WHERE run_id=? "
                "AND kind NOT IN ('observation','observation.raw') "
                "ORDER BY sequence DESC LIMIT 25", [run_id])
            result["events"][run_id] = []
            window = {"scope": "recent", "retained": 0, "truncated": bool(rows)}
            result["trace_window"][run_id] = window
            # Prefer recent evidence. Oversized details stay in local history;
            # a snapshot never grows without limit or claims a complete trace.
            for row in rows[:24]:
                event = json.loads(row[0])
                result["events"][run_id].insert(0, event)
                if len(json.dumps(result, separators=(",", ":")).encode("utf-8")) > 62 * 1024:
                    result["events"][run_id].pop(0)
                else:
                    window["retained"] += 1
            window["truncated"] = len(rows) > window["retained"]
        return result


def runs(store, **kwargs):
    return AsimovLocalStore(store).runs(**kwargs)


def events(store, **kwargs):
    return AsimovLocalStore(store).events(**kwargs)


def physical_ai_runs(store, **kwargs):
    return AsimovLocalStore(store).runs(sources=SOURCES, **kwargs)


def physical_ai_events(store, **kwargs):
    return AsimovLocalStore(store).events(sources=SOURCES, **kwargs)


def physical_ai_snapshot(store):
    return AsimovLocalStore(store).snapshot(sources=SOURCES)
