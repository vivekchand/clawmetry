"""Import official Menlo JSONL recordings without optional SDK dependencies."""

import hashlib
import json
from pathlib import Path

from .journal import MAX_EVENT_BYTES, JournalWriter, journal_directory
from .sdk import normalize_state

MAX_IMPORT_BYTES = 1024 * 1024 * 1024


def _source_hash(path):
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            total += len(block)
            if total > MAX_IMPORT_BYTES:
                raise ValueError("Recording exceeds the 1 GiB import limit")
            digest.update(block)
    return digest.hexdigest()


def import_recording(
    path, *, robot_id, directory=None, environment="hardware", source=None
):
    """Retain original clock values and identify imports independently of live robots."""
    path = Path(path).expanduser()
    fingerprint = _source_hash(path)
    source = source or path.name
    if not isinstance(source, str) or len(source) > 256:
        raise ValueError("Source label must be at most 256 characters")
    identity = json.dumps(
        [fingerprint, robot_id, environment, source], ensure_ascii=True
    )
    run_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]
    target = journal_directory(directory) / (run_id + ".jsonl")
    if target.exists():
        with target.open("rb") as existing:
            first = json.loads(existing.readline(MAX_EVENT_BYTES + 1))
        if (
            first.get("data", {}).get("source_sha256") != fingerprint
            or first.get("data", {}).get("robot_id") != robot_id
        ):
            raise ValueError("An existing run conflicts with this recording")
        status_path = target.with_suffix(".status.json")
        if not status_path.exists() or status_path.stat().st_size > MAX_EVENT_BYTES:
            raise ValueError(
                "An earlier import has no final recorder status; inspect it before retrying"
            )
        result = json.loads(status_path.read_text(encoding="utf-8"))
        if result.get("active"):
            raise ValueError("This recording is already being imported")
        result["replayed"] = True
        return result
    writer = JournalWriter(
        robot_id,
        "asimov_recording",
        directory=directory,
        environment=environment,
        run_id=run_id,
        metadata={
            "source_scope": "official_sdk_recording",
            "source_label": source,
            "source_sha256": fingerprint,
            "observation_only": True,
            "historical": True,
            "clock_mapping": "receipt_time_only; source clocks retained without a guessed wall clock",
        },
    )
    valid = invalid = 0
    first_t = last_t = None
    observed_hash = hashlib.sha256()
    consumed_bytes = 0
    try:
        with path.open("rb") as fh:
            while True:
                line = fh.readline(MAX_EVENT_BYTES + 1)
                if not line:
                    break
                consumed_bytes += len(line)
                observed_hash.update(line)
                if consumed_bytes > MAX_IMPORT_BYTES:
                    invalid += 1
                    break
                if len(line) > MAX_EVENT_BYTES:
                    while line and not line.endswith(b"\n"):
                        line = fh.readline(MAX_EVENT_BYTES + 1)
                        consumed_bytes += len(line)
                        observed_hash.update(line)
                        if consumed_bytes > MAX_IMPORT_BYTES:
                            break
                    invalid += 1
                    continue
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise TypeError("Record must be an object")
                    kind = record.get("kind")
                    if kind == "state":
                        data = normalize_state(record)
                        event_kind = "observation"
                    elif (
                        kind == "sent"
                        and isinstance(record.get("name"), str)
                        and isinstance(record.get("command"), dict)
                    ):
                        data = {
                            "name": record["name"],
                            "command": record["command"],
                            "source_sequence": record.get("sequence"),
                            "outcome": "unknown",
                            "evidence": "sdk_recorded_send",
                        }
                        event_kind = "command.sent"
                    else:
                        raise ValueError("Unsupported recording row")
                    source_t = record.get("t")
                    if isinstance(source_t, (int, float)) and not isinstance(
                        source_t, bool
                    ):
                        import math

                        if math.isfinite(source_t):
                            data["source_timestamp_s"] = source_t
                            first_t = source_t if first_t is None else first_t
                            last_t = source_t
                    data["historical"] = True
                    # Receipt clocks are generated now; source time is never cast to epoch.
                    if writer.emit(event_kind, data, block=True):
                        valid += 1
                    else:
                        invalid += 1
                except (UnicodeError, ValueError, TypeError, KeyError, RecursionError):
                    invalid += 1
        source_changed = observed_hash.hexdigest() != fingerprint
        if source_changed:
            invalid += 1
        duration = (
            max(0.0, last_t - first_t)
            if first_t is not None and last_t is not None
            else None
        )
        writer.emit(
            "run.health",
            {
                "imported_records": valid,
                "skipped_records": invalid,
                "incomplete": bool(invalid),
                "source_duration_s": duration,
                "source_changed_during_import": source_changed,
                "outcome": "unknown",
                "hardware_verified": False,
            },
            block=True,
        )
        if invalid:
            writer._loss(
                "Some recording rows were malformed, unsupported or outside the evidence bounds"
            )
    except OSError:
        writer._loss("The recording could not be read completely")
        raise
    finally:
        result = writer.close()
    result.update(
        imported_records=valid,
        skipped_records=invalid,
        source_duration_s=duration,
        replayed=False,
        source_sha256=fingerprint,
    )
    return result
