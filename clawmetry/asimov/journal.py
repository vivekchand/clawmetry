"""Bounded asynchronous journals compatible with the Physical AI evidence contract."""

import json
import logging
import math
import os
import queue
import threading
import time
import uuid
from pathlib import Path

LOG = logging.getLogger(__name__)
SCHEMA = "clawmetry.robotics.v1"
MAX_EVENT_BYTES = 64 * 1024
DEFAULT_RUN_BYTES = 16 * 1024 * 1024
DEFAULT_DIRECTORY_BYTES = 256 * 1024 * 1024


def journal_directory(path=None):
    """Return the shared robotics journal directory."""
    return Path(
        path
        or os.environ.get("CLAWMETRY_ROBOTICS_DIR", "~/.clawmetry/robotics/journal")
    ).expanduser()


def plain(value, depth=0):
    """Convert bounded evidence to finite JSON; unavailable numbers remain null."""
    import dataclasses
    import enum

    if depth > 12:
        raise ValueError("Evidence is nested too deeply")
    if isinstance(value, enum.Enum):
        return value.name
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: plain(getattr(value, f.name), depth + 1)
            for f in dataclasses.fields(value)
        }
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Evidence contains a nonfinite measurement")
        return value
    if isinstance(value, str):
        if len(value) > 8192:
            raise ValueError("Evidence text exceeds the supported bound")
        return value
    if isinstance(value, (tuple, list)):
        if len(value) > 4096:
            raise ValueError("Evidence array exceeds the supported bound")
        return [plain(x, depth + 1) for x in value]
    if isinstance(value, dict):
        if len(value) > 256:
            raise ValueError("Evidence object exceeds the supported bound")
        return {str(k)[:256]: plain(v, depth + 1) for k, v in value.items()}
    raise ValueError("Unsupported evidence value: " + type(value).__name__)


class JournalWriter:
    """Queue evidence without database/network I/O on producer threads.

    A full run stops accepting disk writes at its bound; it never silently rotates
    away evidence the daemon might not yet have ingested. Start a new run after
    archiving old journals. All loss remains visible in the small status file.
    """

    def __init__(
        self,
        robot_id,
        source_kind,
        *,
        directory=None,
        environment="hardware",
        run_id=None,
        queue_size=256,
        max_bytes=DEFAULT_RUN_BYTES,
        directory_bytes=DEFAULT_DIRECTORY_BYTES,
        metadata=None,
        robot_type="asimov_1",
    ):
        if environment not in ("hardware", "simulation"):
            raise ValueError("Environment must be hardware or simulation")
        if not isinstance(robot_id, str) or not robot_id.strip() or len(robot_id) > 200:
            raise ValueError("A robot identifier of at most 200 characters is required")
        if not isinstance(robot_type, str) or not robot_type.strip() or len(robot_type) > 100 or any(ord(c) < 32 for c in robot_type):
            raise ValueError("A robot type of at most 100 characters is required")
        if queue_size < 1 or max_bytes < 1024 or directory_bytes < max_bytes:
            raise ValueError("Invalid journal bounds")
        self.run_id = run_id or uuid.uuid4().hex
        if len(self.run_id) != 32 or any(
            c not in "0123456789abcdef" for c in self.run_id
        ):
            raise ValueError("Run identifier must be a lowercase UUID32")
        self.directory = journal_directory(directory)
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.path = self.directory / (self.run_id + ".jsonl")
        self.status_path = self.directory / (self.run_id + ".status.json")
        self.robot_id, self.source_kind = robot_id, source_kind
        self.environment = environment
        self.max_bytes, self.directory_bytes = max_bytes, directory_bytes
        self._queue = queue.Queue(maxsize=queue_size)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._closing = False
        self._closed = False
        self._seq = self._written = self._bytes = self._dropped = self._errors = 0
        self._last_error = None
        self._last_status = 0.0
        fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        self._file = os.fdopen(fd, "wb")
        started = dict(metadata or {})
        started.update(
            robot_id=robot_id,
            robot_type=robot_type,
            source_kind=source_kind,
            complete_control_trace=False,
            validation="sdk_only_hardware_unverified",
        )
        started.setdefault("observation_only", True)
        self.emit("run.started", started)
        self._worker = threading.Thread(
            target=self._run, name="clawmetry-asimov-journal", daemon=True
        )
        self._worker.start()

    def _loss(self, message=None):
        with self._lock:
            self._dropped += 1
            if message:
                self._errors += 1
                self._last_error = str(message)[:512]

    def emit(self, kind, data, *, wall_time_ns=None, monotonic_ns=None, block=False):
        """Nonblocking producer API; False means evidence was dropped."""
        if self._closing:
            self._loss("Evidence arrived after the recorder stopped")
            return False
        try:
            body = plain(data)
            if not isinstance(body, dict):
                raise TypeError("Event data must be an object")
            encoded = json.dumps(
                body, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            )
            if len(encoded.encode("utf-8")) > MAX_EVENT_BYTES - 1024:
                raise ValueError("Event exceeds the 64 KiB journal limit")
            item = (
                str(kind)[:80],
                body,
                int(wall_time_ns or time.time_ns()),
                int(monotonic_ns or time.monotonic_ns()),
            )
            if block:
                self._queue.put(item, timeout=5.0)
            else:
                self._queue.put_nowait(item)
            return True
        except queue.Full:
            self._loss()
        except (TypeError, ValueError, OverflowError) as exc:
            self._loss(exc)
        return False

    def status(self):
        """Return recorder health without inspecting robot state."""
        with self._lock:
            return {
                "schema": SCHEMA,
                "run_id": self.run_id,
                "robot_id": self.robot_id,
                "source_kind": self.source_kind,
                "active": not self._closed,
                "flushed": self._closed and self._queue.empty(),
                "queued": self._queue.qsize(),
                "written": self._written,
                "dropped_total": self._dropped,
                "dropped": self._dropped,
                "errors": self._errors,
                "last_error": self._last_error,
                "error": self._last_error,
                "bytes_written": self._bytes,
                "path": str(self.path),
                "incomplete": bool(self._dropped or self._errors),
                "closed_at_ns": str(self._closed_at_ns) if self._closed else None,
            }

    def _directory_size(self):
        return sum(
            p.stat().st_size for p in self.directory.glob("*.jsonl") if p.is_file()
        )

    def _write(self, item, terminal=False):
        kind, data, wall, mono = item
        if self._seq == 0 and kind != "run.started":
            self._loss("Run header could not be stored; later evidence was skipped")
            return
        if not (0 < wall < 2**63 and 0 < mono < 2**63):
            self._loss("Timestamp is outside the supported nanosecond range")
            return
        event = {
            "schema": SCHEMA,
            "run_id": self.run_id,
            "robot_id": self.robot_id,
            "sequence": self._seq + 1,
            "kind": kind,
            "wall_time_ns": str(wall),
            "monotonic_ns": str(mono),
            "environment": self.environment,
            "dropped_total": self._dropped,
            "data": data,
        }
        line = (
            json.dumps(
                event, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            )
            + "\n"
        ).encode("utf-8")
        # Reserve one event for a truthful terminal status after ordinary evidence fills the run.
        reserve = 0 if terminal else min(2048, self.max_bytes // 4)
        try:
            if (
                len(line) > MAX_EVENT_BYTES
                or self._bytes + len(line) > self.max_bytes - reserve
                or self._directory_size() + len(line) > self.directory_bytes
            ):
                self._loss(
                    "Journal storage limit reached; archive old evidence before starting another run"
                )
                return
            self._file.write(line)
            self._file.flush()
            self._seq += 1
            with self._lock:
                self._written += 1
                self._bytes += len(line)
        except OSError:
            self._loss("Journal could not be written")
            LOG.warning("Asimov journal could not be written")

    def _persist_status(self):
        try:
            tmp = self.status_path.with_suffix(".tmp")
            fd = os.open(str(tmp), os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self.status(), fh, allow_nan=False, separators=(",", ":"))
            os.replace(str(tmp), str(self.status_path))
        except OSError:
            LOG.warning("Asimov recorder health could not be saved")

    def _run(self):
        try:
            while not self._stop.is_set() or not self._queue.empty():
                try:
                    self._write(self._queue.get(timeout=0.1))
                    self._queue.task_done()
                except queue.Empty:
                    pass
                if time.monotonic() - self._last_status >= 1.0:
                    self._persist_status()
                    self._last_status = time.monotonic()
            health = self.status()
            self._write(
                (
                    "run.ended",
                    {
                        "status": "incomplete" if health["incomplete"] else "recorded",
                        "dropped_total": health["dropped_total"],
                        "errors": health["errors"],
                        "outcome": "unknown",
                        "complete_control_trace": False,
                    },
                    time.time_ns(),
                    time.monotonic_ns(),
                ),
                terminal=True,
            )
        finally:
            try:
                self._file.flush()
                os.fsync(self._file.fileno())
            except OSError:
                self._loss("Journal could not be fully flushed to disk")
            self._file.close()
            with self._lock:
                self._closed_at_ns = time.time_ns()
                self._closed = True
            self._persist_status()

    def close(self, timeout=5.0):
        """Drain outside SDK callbacks; bounded timeout reports pending evidence."""
        self._closing = True
        self._stop.set()
        self._worker.join(timeout=timeout)
        if self._worker.is_alive():
            self._loss("Journal flush is still pending")
        return self.status()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
