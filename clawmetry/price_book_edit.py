"""Editing the price book, and when each version came into effect.

REQ-OBS-CEA-024 (Software Factory, "Price Book: negotiated rates, deployment
aliases and effective dates"), second increment: AC-OBS-CEA-024.13, .15 and
.16. Issue #5936.

Two things live here, both local to this machine:

* **The activation ledger.** ``clawmetry/price_book.py`` content-addresses
  every book document, which answers *what* a version said. It cannot answer
  *when* that version started to apply, and that is the question Usage needs
  so that editing a rate today leaves last week's figures alone. The ledger is
  an append-only JSON Lines file beside the version store,
  ``~/.clawmetry/pricing_versions/activations.jsonl``, one line per change of
  the version in effect: ``{"version", "activated_at", "source"}``. A line is
  written only after the version file itself is recorded, so a version in the
  ledger can always be reloaded (unless its file was altered, which
  ``price_book.load_version`` refuses).

  A save from the screen comes into effect at the moment of the save. A hand
  edit comes into effect at the file's modification time, never earlier than
  the version before it and never later than the moment it is first read. The
  daemon must not read the book (AC-OBS-CEA-024.11), so "first read" means the
  local dashboard or API; the screen shows the time for every version.

* **Entry edits.** :func:`check_entry` validates one added or edited entry in
  the context of the whole book and maps each problem to the field it
  concerns, as a sentence. :func:`save_entry` writes only when the caller
  confirmed the save and the book is still the version the caller loaded.

Nothing here computes a price. Selection is ``price_book.py``; valuation is
the paid engine behind ``pricing.value_usage``.
"""
from __future__ import annotations

import copy
import json
import os
import re
from datetime import datetime, timezone

from clawmetry import price_book as pb

LEDGER_NAME = "activations.jsonl"
MAX_LEDGER_BYTES = 1024 * 1024

#: Words in a validation problem, and how a person would say them.
_FIELD_WORDS = (
    ("rates.input_per_1m", "the input rate"),
    ("rates.output_per_1m", "the output rate"),
    ("rates.cache_read_per_1m", "the cache read rate"),
    ("rates.cache_write_per_1m", "the cache write rate"),
    ("model_regex", "the model pattern"),
    ("model_prefix", "the model prefix"),
    ("effective_from", "the start date"),
    ("effective_to", "the end date"),
    ("discount_pct", "the discount"),
)


# ── The activation ledger ───────────────────────────────────────────────────


def ledger_path() -> str:
    return os.path.join(pb.versions_dir(), LEDGER_NAME)


def _parse_at(text):
    try:
        dt = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(timezone.utc)


def _iso(dt) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def timeline() -> list:
    """Every change of the version in effect, in the order it happened.

    ``[{"version", "activated_at", "source"}]`` with ``activated_at`` an ISO
    UTC string. Lines that are not a well-formed entry are skipped, and a
    line whose time runs backwards is ignored, so a damaged ledger can hide a
    change but never reorder history. Never raises.
    """
    path = ledger_path()
    try:
        if os.path.getsize(path) > MAX_LEDGER_BYTES:
            return []
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    out, last = [], None
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue
        version = row.get("version")
        at = _parse_at(row.get("activated_at"))
        if not (isinstance(version, str) and pb._VERSION_RE.match(version)) or at is None:
            continue
        if last is not None and at < last:
            continue
        last = at
        out.append({"version": version, "activated_at": _iso(at),
                    "source": row.get("source") if row.get("source") in ("screen", "file") else "file"})
    return out


def version_in_effect(at, entries):
    """The ledger entry in effect at ``at`` (an aware datetime), or None when
    ``at`` is unknown or earlier than the first recorded version."""
    if at is None:
        return None
    found = None
    for row in entries:
        when = _parse_at(row.get("activated_at"))
        if when is None or when > at:
            break
        found = row
    return found


def activate(book, *, now=None, source="file"):
    """Record ``book``'s version and note when it came into effect.

    Returns the ledger entry now in effect, or None when the book is absent,
    unusable, or its version could not be recorded (in which case nothing is
    in effect from it, so no figure can claim its rates). Never raises.
    """
    try:
        if not book or not book.get("present") or book.get("errors") or not book.get("version"):
            return None
        if not pb.record_version(book):
            return None
        entries = timeline()
        if entries and entries[-1]["version"] == book["version"]:
            return entries[-1]
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        at = now
        if source != "screen":
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(book.get("source") or pb.default_path()),
                                               tz=timezone.utc)
                at = min(now, mtime)
            except (OSError, OverflowError, ValueError):
                at = now
        if entries:
            previous = _parse_at(entries[-1]["activated_at"])
            if previous is not None and at < previous:
                at = previous
        row = {"version": book["version"], "activated_at": _iso(at),
               "source": "screen" if source == "screen" else "file"}
        os.makedirs(pb.versions_dir(), exist_ok=True)
        with open(ledger_path(), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
        return row
    except (OSError, TypeError, ValueError):
        return None


# ── Entry edits ─────────────────────────────────────────────────────────────


def _sentence(problem: str) -> str:
    text = str(problem or "").strip()
    for word, spoken in _FIELD_WORDS:
        text = re.sub(r"(?<![\w.])" + re.escape(word) + r"(?![\w])", spoken, text)
    text = re.sub(r"^id\b", "the entry id", text)
    text = text.replace("give exactly one of model, the model prefix, the model pattern",
                        "choose how the entry names its model: an exact model, a prefix or a pattern")
    text = text.replace("give exactly one of rates or the discount",
                        "give either rates or a discount, not both")
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    return text if text.endswith(".") else text + "."


def problem_field(problem: str) -> str:
    """The form field a validation problem is about."""
    p = str(problem or "")
    m = re.match(r"^(rates\.(?:input|output|cache_read|cache_write)_per_1m)\b", p)
    if m:
        return m.group(1)
    for prefix, field in (
        ("id ", "id"), ("give exactly one of model", "match"), ("model", "match"),
        ("overlaps entry", "match"), ("provider", "provider"), ("channel", "channel"),
        ("region", "region"), ("effective_from", "effective_from"),
        ("effective_to", "effective_to"), ("currency", "currency"),
        ("give exactly one of rates", "pricing"), ("rates", "rates"),
        ("unknown rate field", "rates"), ("discount_pct", "discount_pct"),
    ):
        if p.startswith(prefix):
            return field
    return "entry"


def field_problems(problems) -> list:
    return [{"field": problem_field(p), "message": _sentence(p)} for p in (problems or []) if p]


def _current_doc(book):
    doc = book.get("_doc") if book.get("present") else None
    if doc is None:
        return {"schema": pb.SCHEMA, "entries": [], "aliases": []}
    return copy.deepcopy(doc)


def check_entry(raw, *, replace_id=None, book=None) -> dict:
    """Validate one added or edited entry against the whole book. Writes
    nothing. Never raises.

    Returns ``{"ok", "problems": [{field, message}], "doc", "version",
    "entry"}``; ``doc`` is the book as it would be saved.
    """
    book = book if book is not None else pb.load_price_book()
    out = {"ok": False, "problems": [], "doc": None, "version": None, "entry": None}
    if book.get("present") and book.get("errors"):
        out["problems"] = [{"field": "book", "message": _sentence(
            "the price book file cannot be read as it is (" + "; ".join(book["errors"])
            + "), so it cannot be edited here; fix the file first")}]
        return out
    if not isinstance(raw, dict):
        out["problems"] = [{"field": "entry", "message": "Send the entry as an object."}]
        return out
    doc = _current_doc(book)
    entries = doc.get("entries") if isinstance(doc.get("entries"), list) else []
    doc["entries"] = entries
    ids = [e.get("id") if isinstance(e, dict) else None for e in entries]
    if replace_id is not None:
        if replace_id not in ids:
            out["problems"] = [{"field": "entry", "message": _sentence(
                f"there is no entry {replace_id!r} to edit; it may have been removed from the file")}]
            return out
        index = ids.index(replace_id)
        entries[index] = raw
    else:
        if raw.get("id") in ids:
            out["problems"] = [{"field": "id", "message": _sentence(
                f"id {raw.get('id')!r} is already used by another entry; choose a different id")}]
            return out
        entries.append(raw)
        index = len(entries) - 1
    parsed = pb.parse_price_book(doc)
    problems = list(parsed.get("errors", []))
    others = []
    for rej in parsed.get("rejected", []):
        if rej.get("kind") != "entry":
            continue
        if rej.get("index") == index:
            problems.extend(rej.get("problems", []))
        elif not any(r.get("kind") == "entry" and r.get("index") == rej.get("index")
                     for r in book.get("rejected", [])):
            others.append(rej)
    for rej in others:
        problems.append(f"overlaps entry {rej.get('id')!r}, which would then be rejected too")
    out["problems"] = field_problems(problems)
    out["doc"] = doc
    out["version"] = parsed.get("version")
    if not out["problems"]:
        accepted = [e for e in parsed.get("entries", []) if e.get("index") == index]
        out["entry"] = pb.public_entry(accepted[0]) if accepted else None
        out["ok"] = out["entry"] is not None
    return out


def save_entry(raw, *, replace_id=None, base_version=None, confirm=False, now=None):
    """Write one added or edited entry. Returns ``(http_status, body)``.

    Refuses without ``confirm`` (400), when the book changed after the caller
    loaded it (409), and when the entry does not validate (422). On success
    the whole book is replaced atomically, its version recorded, and the time
    it comes into effect is noted in the ledger. Never raises.
    """
    if confirm is not True:
        return 400, {"error": "not_confirmed",
                     "message": "Nothing was saved. Confirm the save to write the price book."}
    book = pb.load_price_book()
    current = book.get("version") if book.get("present") else None
    if book.get("present") and current is None and not book.get("errors"):
        current = None
    if (base_version or None) != current:
        return 409, {"error": "book_changed", "current_version": current,
                     "message": ("Nothing was saved. The price book changed after you opened it. "
                                 "Reload it to see the current entries, then make your edit again.")}
    checked = check_entry(raw, replace_id=replace_id, book=book)
    if not checked["ok"]:
        return 422, {"error": "invalid_entry", "problems": checked["problems"],
                     "message": "Nothing was saved. Fix the problems shown next to each field."}
    path = pb.default_path()
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(checked["doc"], fh, indent=2, sort_keys=False, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)
    except (OSError, TypeError, ValueError):
        return 500, {"error": "write_failed",
                     "message": "Nothing was saved. The price book file could not be written; check its folder's permissions."}
    saved = pb.load_price_book()
    row = activate(saved, now=now, source="screen")
    if row is None:
        return 500, {"error": "version_not_recorded", "version": saved.get("version"),
                     "message": ("The file was written, but its version could not be recorded, so no figure "
                                 "will use these rates until it is. Check the pricing_versions folder's permissions.")}
    return 200, {
        "version": row["version"],
        "effective_at": row["activated_at"],
        "entry": checked["entry"],
        "message": (f"Saved as version {row['version']}. It applies to usage observed from "
                    f"{row['activated_at']}. Usage before then keeps its earlier valuation "
                    "unless you restate it."),
    }
