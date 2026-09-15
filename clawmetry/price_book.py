"""Price book contract: negotiated rates, Azure OpenAI aliases, effective dates.

REQ-OBS-CEA-024 (Software Factory, "Price Book: negotiated rates, deployment
aliases and effective dates"). Issue #5936.

What this module owns, and what it deliberately does not:

* **Owns (open source):** the price book file schema and its validation, a
  content-addressed version store so a rate that was used can always be
  reproduced, Azure OpenAI deployment-alias resolution, AWS Bedrock model id
  normalisation, deterministic effective-dated rate *selection* (which entry
  applies to a usage record and why), the published-list basis for the same
  record, and the valuation record contract every valuation must satisfy.
* **Does not own:** contract valuation, restatement and invoice reconciliation.
  Those are the paid engine (clawmetry-pro #252), reached through the
  ``pricing.value_usage`` extension call (:data:`VALUE_USAGE_EVENT`). The route
  in ``routes/pricing.py`` checks every record that engine returns against
  :func:`valuation_problems` and refuses the ones that do not state their basis.

The book is a local JSON file (``~/.clawmetry/pricing.json``, or
``CLAWMETRY_PRICE_BOOK``). It stays on this machine: nothing that sends data
off the machine imports this module (``tests/test_price_book.py`` enforces it).

File shape (``schema`` is required)::

    {
      "schema": "clawmetry.price_book/1",
      "entries": [
        {"id": "bedrock-sonnet-2026", "model": "claude-sonnet-4-5",
         "channel": "aws-bedrock", "effective_from": "2026-01-01",
         "currency": "USD",
         "rates": {"input_per_1m": 2.4, "output_per_1m": 12.0,
                   "cache_read_per_1m": 0.24, "cache_write_per_1m": 3.0}},
        {"id": "azure-gpt4o-discount", "model_prefix": "gpt-4o",
         "channel": "azure-openai", "effective_from": "2026-03-01",
         "effective_to": "2027-03-01", "discount_pct": 18}
      ],
      "aliases": [
        {"deployment": "prod-chat", "model": "gpt-4o",
         "resource": "myres.openai.azure.com"}
      ]
    }

Precedence when several entries match one record, highest first: an entry
scoped to the record's channel, then one scoped to its region, then an exact
model over a prefix over a pattern, then the longer name. An exact model
name also covers its dated snapshots. A tie at the top
is reported as ambiguous and no rate is chosen.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import date, datetime, timezone

SCHEMA = "clawmetry.price_book/1"

#: Every valuation states exactly one of these as its basis.
PRICED_FROM = ("vendor_reported", "contract", "list", "default", "unknown")

#: Extension call the paid valuation engine answers (clawmetry.extensions.call).
VALUE_USAGE_EVENT = "pricing.value_usage"

#: Version label for the published list rates in providers_pricing.py.
LIST_RATE_VERSION = "providers_pricing"

MAX_BOOK_BYTES = 2 * 1024 * 1024
MAX_ENTRIES = 5000
MAX_PATTERN_LEN = 200

_TOP_KEYS = {"schema", "entries", "aliases", "note"}
_ENTRY_KEYS = {
    "id", "model", "model_prefix", "model_regex", "provider", "channel",
    "region", "effective_from", "effective_to", "currency", "rates",
    "discount_pct", "note",
}
_RATE_KEYS = {"input_per_1m", "output_per_1m", "cache_read_per_1m", "cache_write_per_1m"}
_ALIAS_KEYS = {"id", "deployment", "model", "resource", "channel",
               "effective_from", "effective_to", "note"}
_MATCH_KINDS = ("model", "model_prefix", "model_regex")
_KIND_RANK = {"model": 3, "model_prefix": 2, "model_regex": 1}

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
_VERSION_RE = re.compile(r"^pb1-[0-9a-f]{20}$")

# AWS Bedrock model ids: an optional cross-region inference prefix, a vendor
# prefix, and a version suffix ("us.anthropic.claude-sonnet-4-5-20250929-v1:0").
_BEDROCK_REGION_RE = re.compile(r"^(us-gov|us|eu|apac|global|jp|au|ca)\.")
_BEDROCK_VENDOR_RE = re.compile(
    r"^(anthropic|amazon|meta|mistral|cohere|ai21|deepseek|openai|qwen|writer)\."
)


# ── Time ────────────────────────────────────────────────────────────────────


def _parse_book_time(value):
    """A book date: ``YYYY-MM-DD`` (00:00 UTC) or an ISO datetime WITH a
    timezone. Returns (datetime | None, problem | None)."""
    if not isinstance(value, str) or not value.strip():
        return None, "must be a date (YYYY-MM-DD) or an ISO datetime with a timezone"
    text = value.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        try:
            d = date.fromisoformat(text)
        except ValueError:
            return None, f"{text!r} is not a real date"
        return datetime(d.year, d.month, d.day, tzinfo=timezone.utc), None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None, f"{text!r} is not a date or ISO datetime"
    if dt.tzinfo is None:
        return None, f"{text!r} has no timezone; add Z or an offset"
    return dt.astimezone(timezone.utc), None


def parse_observed_at(value):
    """A usage record's observed time: epoch seconds or milliseconds, or an ISO
    string. A naive ISO string is read as UTC (the store's convention).
    Returns an aware UTC datetime or None. Never raises."""
    try:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            if not math.isfinite(value) or value <= 0:
                return None
            secs = value / 1000.0 if value > 1e11 else float(value)
            return datetime.fromtimestamp(secs, tz=timezone.utc)
        if isinstance(value, str) and value.strip():
            text = value.strip()
            if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
                d = date.fromisoformat(text)
                return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError, OSError):
        return None
    return None


def _iso(dt):
    return dt.isoformat().replace("+00:00", "Z") if dt else None


def _active(item, at) -> bool:
    start, end = item.get("_from"), item.get("_to")
    if start is not None and at < start:
        return False
    return not (end is not None and at >= end)


def _overlap(a, b) -> bool:
    far_past = datetime.min.replace(tzinfo=timezone.utc)
    far_future = datetime.max.replace(tzinfo=timezone.utc)
    a0, a1 = a.get("_from") or far_past, a.get("_to") or far_future
    b0, b1 = b.get("_from") or far_past, b.get("_to") or far_future
    return a0 < b1 and b0 < a1


# ── Model ids ───────────────────────────────────────────────────────────────


def canonical_model(model) -> str:
    """The model name a book entry is matched against.

    Lower-cased, namespace stripped (``openrouter/anthropic/x`` and Bedrock
    ARNs keep the last segment), and for Bedrock ids the region prefix, vendor
    prefix and version suffix removed, so ``us.anthropic.claude-sonnet-4-5-
    20250929-v1:0`` and ``claude-sonnet-4-5-20250929`` are the same model. A
    ``-vN`` suffix is only stripped from a Bedrock-shaped id: ``deepseek-v4``
    is a model name, not a version.
    """
    m = str(model or "").strip().lower()
    if not m:
        return ""
    if "/" in m:
        m = m.rsplit("/", 1)[-1]
    bedrock = False
    stripped = _BEDROCK_REGION_RE.sub("", m, count=1)
    if stripped != m:
        bedrock, m = True, stripped
    stripped = _BEDROCK_VENDOR_RE.sub("", m, count=1)
    if stripped != m:
        bedrock, m = True, stripped
    if re.search(r"-v\d+:\d+$", m):
        m = re.sub(r"-v\d+:\d+$", "", m)
    elif bedrock:
        m = re.sub(r"-v\d+$", "", m)
    return m


def undated_model(canon: str) -> str:
    """``canon`` without a trailing snapshot date (``-20250929`` or
    ``-2024-08-06``)."""
    return re.sub(r"-(\d{8}|\d{4}-\d{2}-\d{2})$", "", canon or "")


def bedrock_shape(model):
    """``(is_bedrock, region_or_None)`` for a model id. Never raises."""
    m = str(model or "").strip().lower()
    if "/" in m:
        m = m.rsplit("/", 1)[-1]
    region = None
    rm = _BEDROCK_REGION_RE.match(m)
    if rm:
        region = rm.group(1)
        m = m[rm.end():]
    return bool(_BEDROCK_VENDOR_RE.match(m)), region


# ── Parsing and validation ─────────────────────────────────────────────────


def _canonical_json(doc) -> str:
    return json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def version_of(doc) -> str:
    """Content address of a book document. Any edit yields a new version."""
    digest = hashlib.sha256(_canonical_json(doc).encode("utf-8")).hexdigest()
    return "pb1-" + digest[:20]


def _rate_number(value):
    return (
        isinstance(value, (int, float)) and not isinstance(value, bool)
        and math.isfinite(value) and value >= 0
    )


def _optional_slug(raw, key, problems):
    if key not in raw:
        return None
    val = raw[key]
    if not isinstance(val, str) or not _SLUG_RE.match(val.strip().lower()):
        problems.append(f"{key} must be a short lower-case name like 'aws-bedrock'")
        return None
    return val.strip().lower()


def _parse_window(raw, problems, required):
    start = end = None
    if "effective_from" in raw:
        start, p = _parse_book_time(raw["effective_from"])
        if p:
            problems.append(f"effective_from {p}")
    elif required:
        problems.append("effective_from is required")
    if raw.get("effective_to") is not None:
        end, p = _parse_book_time(raw["effective_to"])
        if p:
            problems.append(f"effective_to {p}")
    if start and end and end <= start:
        problems.append("effective_to must be after effective_from")
    return start, end


def _parse_entry(raw, index):
    problems = []
    if not isinstance(raw, dict):
        return None, ["entry must be an object"]
    unknown = sorted(set(raw) - _ENTRY_KEYS)
    if unknown:
        problems.append("unknown field(s): " + ", ".join(unknown))
    eid = raw.get("id")
    if not isinstance(eid, str) or not _ID_RE.match(eid):
        problems.append("id is required: letters, digits and . _ : - (max 64)")
    kinds = [k for k in _MATCH_KINDS if k in raw]
    if len(kinds) != 1:
        problems.append("give exactly one of model, model_prefix, model_regex")
    kind = kinds[0] if len(kinds) == 1 else None
    value = raw.get(kind) if kind else None
    compiled = None
    if kind:
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{kind} must be a non-empty string")
        elif kind == "model_regex":
            if len(value) > MAX_PATTERN_LEN:
                problems.append(f"model_regex is longer than {MAX_PATTERN_LEN} characters")
            else:
                try:
                    compiled = re.compile(value, re.IGNORECASE)
                except re.error:
                    # The compiler's message is not echoed back (CodeQL
                    # py/stack-trace-exposure): the book API returns problems.
                    problems.append("model_regex does not compile as a regular expression")
    provider = _optional_slug(raw, "provider", problems)
    channel = _optional_slug(raw, "channel", problems)
    region = _optional_slug(raw, "region", problems)
    start, end = _parse_window(raw, problems, required=True)
    currency = raw.get("currency", "USD")
    if not isinstance(currency, str) or not _CURRENCY_RE.match(currency):
        problems.append("currency must be a three-letter code such as USD")
    has_rates, has_discount = "rates" in raw, "discount_pct" in raw
    if has_rates == has_discount:
        problems.append("give exactly one of rates or discount_pct")
    rates = None
    if has_rates:
        r = raw["rates"]
        if not isinstance(r, dict):
            problems.append("rates must be an object")
        else:
            bad = sorted(set(r) - _RATE_KEYS)
            if bad:
                problems.append("unknown rate field(s): " + ", ".join(bad))
            for need in ("input_per_1m", "output_per_1m"):
                if need not in r:
                    problems.append(f"rates.{need} is required")
            for k, v in r.items():
                if k in _RATE_KEYS and not _rate_number(v):
                    problems.append(f"rates.{k} must be a number of at least 0")
            rates = {k: float(v) for k, v in r.items() if k in _RATE_KEYS and _rate_number(v)}
    discount = None
    if has_discount:
        d = raw["discount_pct"]
        if not _rate_number(d) or not (0 < d < 100):
            problems.append("discount_pct must be a number between 0 and 100")
        else:
            discount = float(d)
        if currency != "USD":
            problems.append("discount_pct applies to the published USD rate; currency must be USD")
    if problems:
        return None, problems
    match_value = value.strip()
    return {
        "id": eid,
        "kind": kind,
        "match": match_value,
        "_canon": canonical_model(match_value) if kind != "model_regex" else None,
        "_regex": compiled,
        "provider": provider,
        "channel": channel,
        "region": region,
        "currency": currency,
        "rates": rates,
        "discount_pct": discount,
        "_from": start,
        "_to": end,
        "index": index,
    }, []


def _parse_alias(raw, index):
    problems = []
    if not isinstance(raw, dict):
        return None, ["alias must be an object"]
    unknown = sorted(set(raw) - _ALIAS_KEYS)
    if unknown:
        problems.append("unknown field(s): " + ", ".join(unknown))
    dep, model = raw.get("deployment"), raw.get("model")
    if not isinstance(dep, str) or not dep.strip() or len(dep) > 128:
        problems.append("deployment is required (the name chosen in Azure)")
    if not isinstance(model, str) or not model.strip():
        problems.append("model is required (the model the deployment serves)")
    resource = raw.get("resource")
    if resource is not None and (
        not isinstance(resource, str) or not re.match(r"^[a-z0-9.-]{3,253}$", resource.strip().lower())
    ):
        problems.append("resource must be a host name such as myres.openai.azure.com")
    aid = raw.get("id")
    if aid is not None and (not isinstance(aid, str) or not _ID_RE.match(aid)):
        problems.append("id must be letters, digits and . _ : - (max 64)")
    channel = _optional_slug(raw, "channel", problems) or "azure-openai"
    start, end = _parse_window(raw, problems, required=False)
    if problems:
        return None, problems
    return {
        "id": aid or f"alias-{index}",
        "deployment": dep.strip(),
        "model": model.strip(),
        "resource": resource.strip().lower() if resource else None,
        "channel": channel,
        "_from": start,
        "_to": end,
        "index": index,
    }, []


def _entry_key(e):
    return (e["kind"], e["_canon"] if e["kind"] != "model_regex" else e["match"],
            e["provider"], e["channel"], e["region"])


def parse_price_book(doc, *, source=None) -> dict:
    """Validate a decoded book. Never raises.

    Returns ``{"schema", "version", "entries", "aliases", "rejected",
    "errors", "source"}``. ``errors`` are book-level problems that make the
    whole book unusable (wrong schema, wrong shape); ``rejected`` lists each
    entry or alias refused with its reasons, while the rest stay usable.
    """
    book = {"schema": SCHEMA, "version": None, "entries": [], "aliases": [],
            "rejected": [], "errors": [], "source": source}
    if not isinstance(doc, dict):
        book["errors"].append("the price book must be a JSON object")
        return book
    if doc.get("schema") != SCHEMA:
        book["errors"].append(f"schema must be {SCHEMA!r}")
        return book
    unknown = sorted(set(doc) - _TOP_KEYS)
    if unknown:
        book["errors"].append("unknown top-level field(s): " + ", ".join(unknown))
        return book
    entries_raw = doc.get("entries", [])
    aliases_raw = doc.get("aliases", [])
    if not isinstance(entries_raw, list) or not isinstance(aliases_raw, list):
        book["errors"].append("entries and aliases must be lists")
        return book
    if len(entries_raw) + len(aliases_raw) > MAX_ENTRIES:
        book["errors"].append(f"more than {MAX_ENTRIES} entries and aliases")
        return book
    book["version"] = version_of(doc)

    accepted, seen_ids = [], {}
    for i, raw in enumerate(entries_raw):
        entry, problems = _parse_entry(raw, i)
        if entry and entry["id"] in seen_ids:
            problems, entry = [f"id {entry['id']!r} is used by entry {seen_ids[entry['id']]}"], None
        if entry is None:
            book["rejected"].append({"kind": "entry", "index": i,
                                     "id": raw.get("id") if isinstance(raw, dict) else None,
                                     "problems": problems})
            continue
        seen_ids[entry["id"]] = i
        accepted.append(entry)

    # Two entries claiming the same usage over overlapping dates: there is no
    # right answer to pick, so both are refused and both are named.
    clash = set()
    for a_i, a in enumerate(accepted):
        for b in accepted[a_i + 1:]:
            if _entry_key(a) == _entry_key(b) and _overlap(a, b):
                clash.add(a["id"])
                clash.add(b["id"])
                for x, y in ((a, b), (b, a)):
                    book["rejected"].append({
                        "kind": "entry", "index": x["index"], "id": x["id"],
                        "problems": [(f"overlaps entry {y['id']!r} for the same model, "
                                      "channel and region over the same dates")],
                    })
    book["entries"] = [e for e in accepted if e["id"] not in clash]

    aliases = []
    for i, raw in enumerate(aliases_raw):
        alias, problems = _parse_alias(raw, i)
        if alias is None:
            book["rejected"].append({"kind": "alias", "index": i,
                                     "id": raw.get("id") if isinstance(raw, dict) else None,
                                     "problems": problems})
            continue
        aliases.append(alias)
    alias_clash = set()
    for a_i, a in enumerate(aliases):
        for b in aliases[a_i + 1:]:
            same = (a["deployment"].lower() == b["deployment"].lower()
                    and a["resource"] == b["resource"])
            if same and _overlap(a, b) and canonical_model(a["model"]) != canonical_model(b["model"]):
                alias_clash.update((a["index"], b["index"]))
                for x, y in ((a, b), (b, a)):
                    book["rejected"].append({
                        "kind": "alias", "index": x["index"], "id": x["id"],
                        "problems": [(f"deployment {x['deployment']!r} is also mapped to "
                                      f"{y['model']!r} by {y['id']!r} over the same dates")],
                    })
    book["aliases"] = [a for a in aliases if a["index"] not in alias_clash]
    book["rejected"].sort(key=lambda r: (r["kind"], r["index"]))
    return book


# ── Files ───────────────────────────────────────────────────────────────────


def _clawmetry_home() -> str:
    return os.environ.get("CLAWMETRY_HOME") or os.path.join(os.path.expanduser("~"), ".clawmetry")


def default_path() -> str:
    return os.environ.get("CLAWMETRY_PRICE_BOOK") or os.path.join(_clawmetry_home(), "pricing.json")


def versions_dir() -> str:
    return os.path.join(_clawmetry_home(), "pricing_versions")


def _read_doc(path):
    """(doc, error). error is None on success."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return None, "absent"
    if size > MAX_BOOK_BYTES:
        return None, f"the price book is larger than {MAX_BOOK_BYTES // 1024} KB"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), None
    except (OSError, UnicodeDecodeError):
        return None, "the price book could not be read (check the file's permissions and encoding)"
    except ValueError:
        # Nothing from the exception reaches a caller (CodeQL
        # py/stack-trace-exposure); the owner can validate the file locally.
        return None, "the price book is not valid JSON (check it with: python3 -m json.tool <file>)"


def load_price_book(path=None) -> dict:
    """Load and validate the local book. ``present`` is False when no file
    exists, which is the normal state and not an error. Never raises."""
    path = path or default_path()
    doc, err = _read_doc(path)
    if err == "absent":
        book = parse_price_book({"schema": SCHEMA}, source=path)
        book.update(present=False, version=None)
        return book
    if err:
        book = parse_price_book({"schema": SCHEMA}, source=path)
        book.update(present=True, version=None, errors=[err])
        return book
    book = parse_price_book(doc, source=path)
    book["present"] = True
    book["_doc"] = doc
    return book


def record_version(book) -> bool:
    """Write the book's document to the version store, once.

    Versions are content-addressed, so an existing file already holds exactly
    this content and is never rewritten. Returns True when the version is on
    disk afterwards. Never raises.
    """
    try:
        doc, version = book.get("_doc"), book.get("version")
        if doc is None or not version or book.get("errors"):
            return False
        target = os.path.join(versions_dir(), version + ".json")
        if os.path.exists(target):
            return True
        os.makedirs(versions_dir(), exist_ok=True)
        tmp = f"{target}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(_canonical_json(doc))
        if os.path.exists(target):
            os.unlink(tmp)
        else:
            os.replace(tmp, target)
        return True
    except (OSError, TypeError, ValueError):
        return False


def load_version(version):
    """The book exactly as ``version`` recorded it, or None when the version is
    unknown or its file no longer hashes to its name (it was altered)."""
    if not isinstance(version, str) or not _VERSION_RE.match(version):
        return None
    # The id comes from a request: resolve the path and require it to stay
    # inside the version store, whatever the id looks like.
    base = os.path.realpath(versions_dir())
    path = os.path.realpath(os.path.join(base, version + ".json"))
    if os.path.dirname(path) != base or not path.startswith(base + os.sep):
        return None
    doc, err = _read_doc(path)
    if err or version_of(doc) != version:
        return None
    book = parse_price_book(doc, source=path)
    book["present"] = True
    book["_doc"] = doc
    return book


def recorded_versions() -> list:
    """Recorded version ids, oldest first. Never raises."""
    try:
        names = [n[:-5] for n in os.listdir(versions_dir())
                 if n.endswith(".json") and _VERSION_RE.match(n[:-5])]
        return sorted(names, key=lambda v: os.path.getmtime(os.path.join(versions_dir(), v + ".json")))
    except OSError:
        return []


def public_entry(entry) -> dict:
    return {
        "id": entry["id"], entry["kind"]: entry["match"],
        "provider": entry["provider"], "channel": entry["channel"],
        "region": entry["region"], "currency": entry["currency"],
        "rates": entry["rates"], "discount_pct": entry["discount_pct"],
        "effective_from": _iso(entry["_from"]), "effective_to": _iso(entry["_to"]),
    }


def public_alias(alias) -> dict:
    return {
        "id": alias["id"], "deployment": alias["deployment"], "model": alias["model"],
        "resource": alias["resource"], "channel": alias["channel"],
        "effective_from": _iso(alias["_from"]), "effective_to": _iso(alias["_to"]),
    }


def public_book(book) -> dict:
    return {
        "schema": book.get("schema"), "version": book.get("version"),
        "present": bool(book.get("present")), "source": book.get("source"),
        "entries": [public_entry(e) for e in book.get("entries", [])],
        "aliases": [public_alias(a) for a in book.get("aliases", [])],
        "rejected": list(book.get("rejected", [])),
        "errors": list(book.get("errors", [])),
    }


# ── Resolution ──────────────────────────────────────────────────────────────


def _resolve_alias(book, deployment, resource, at):
    """(status, alias). status: matched | none | ambiguous | no_timestamp."""
    if not deployment or not book:
        return "none", None
    dep = deployment.lower()
    candidates = [a for a in book.get("aliases", [])
                  if a["deployment"].lower() == dep
                  and (a["resource"] is None or a["resource"] == resource)]
    if not candidates:
        return "none", None
    dated = [a for a in candidates if a["_from"] or a["_to"]]
    if at is None:
        candidates = [a for a in candidates if a not in dated]
        if not candidates:
            return "no_timestamp", None
    else:
        candidates = [a for a in candidates if _active(a, at)]
        if not candidates:
            return "none", None
    best = max(1 if a["resource"] else 0 for a in candidates)
    top = [a for a in candidates if (1 if a["resource"] else 0) == best]
    models = {canonical_model(a["model"]) for a in top}
    if len(models) > 1:
        return "ambiguous", None
    return "matched", top[0]


def _entry_matches(entry, canon, provider, channel, region):
    if entry["provider"] and entry["provider"] != provider:
        return False
    if entry["channel"] and entry["channel"] != channel:
        return False
    if entry["region"] and entry["region"] != region:
        return False
    kind = entry["kind"]
    if kind == "model":
        # An exact name also covers that model's dated snapshots, so an entry
        # for "claude-sonnet-4-5" prices "claude-sonnet-4-5-20250929"; an entry
        # naming the snapshot itself outranks it (see _entry_rank).
        return entry["_canon"] in (canon, undated_model(canon))
    if kind == "model_prefix":
        return canon.startswith(entry["_canon"])
    return entry["_regex"].fullmatch(canon) is not None


def _entry_rank(entry):
    return (
        1 if entry["channel"] else 0,
        1 if entry["region"] else 0,
        _KIND_RANK[entry["kind"]],
        len(entry["_canon"] or "") if entry["kind"] in ("model", "model_prefix") else 0,
    )


#: The financial basis (clawmetry/cost_basis.py, #5937) each ``priced_from``
#: is, so a figure from this surface reads the same as every other cost figure.
#: A vendor-reported cost is still published-rate money: the vendor computed it
#: from its list rates, which makes it a source, not a receipt.
_COST_BASIS_FOR = {
    "vendor_reported": "published_rate",
    "contract": "contract",
    "list": "published_rate",
    "default": "published_rate",
    "unknown": "unknown",
}


def financial_basis(priced_from, amount, rate_version=None) -> dict:
    """``cost_basis`` and ``cost_basis_label`` for one priced figure. Never raises.

    Goes through :func:`clawmetry.cost_basis.label`, so a contract figure with
    no rate version, or a figure with no amount, is labelled ``unknown`` rather
    than claiming a basis it cannot show.
    """
    from clawmetry import cost_basis as cb

    basis = _COST_BASIS_FOR.get(priced_from, cb.UNKNOWN) if amount is not None else cb.UNKNOWN
    evidence = {"rate_version": rate_version} if isinstance(rate_version, str) and rate_version else None
    labelled = cb.label({}, basis, evidence=evidence)
    return {"cost_basis": labelled["cost_basis"], "cost_basis_label": labelled["cost_basis_label"]}


def _list_basis(provider, model, fact):
    from clawmetry import providers_pricing as pp

    if not model:
        return {"priced_from": "unknown", "rate_source": None, "input_per_1m": None,
                "output_per_1m": None, "cost_usd": None, "rate_version": None,
                "reason": "no model is known for this record"}
    lookup_provider = "azure-openai" if fact.get("channel") == "azure-openai" and provider == "openai" else provider
    i_rate, o_rate, basis = pp.rate_basis(lookup_provider, model)
    if basis == "unknown_default":
        return {"priced_from": "unknown", "rate_source": None, "input_per_1m": None,
                "output_per_1m": None, "cost_usd": None, "rate_version": None,
                "reason": "no published rate for this model or provider"}
    priced_from = "default" if basis == "provider_baseline" else "list"
    rate_source = {
        "model": "published_model_rate", "local": "local_model",
        "provider_baseline": "provider_baseline",
    }[basis]
    out = {"priced_from": priced_from, "rate_source": rate_source,
           "input_per_1m": i_rate, "output_per_1m": o_rate,
           "rate_version": LIST_RATE_VERSION, "cost_usd": None, "reason": None}
    if lookup_provider == "azure-openai":
        out["reason"] = ("OpenAI's published rate; Azure's own list can differ by region "
                         "and deployment type. Add a price book entry for the contracted rate.")
    elif fact.get("channel") == "aws-bedrock":
        out["reason"] = ("the model vendor's published rate; AWS Bedrock's own list can differ, "
                         "for example on regional inference profiles. Add a price book entry "
                         "for the contracted rate.")
    elif basis == "provider_baseline":
        out["reason"] = "this model is not in the published table; a representative model's rate stands in"
    counts, bad = {}, []
    for key in _TOKEN_KEYS:
        raw = fact.get(key)
        if raw is None:
            counts[key] = 0
        elif _rate_number(raw):
            counts[key] = int(raw)
        else:
            bad.append(key)
    if bad:
        # Pricing the valid fields alone would undercount, so price nothing.
        note = (", ".join(bad) + (" is" if len(bad) == 1 else " are")
                + " not a non-negative finite number, so no amount was computed")
        out["reason"] = f"{out['reason']} {note[0].upper()}{note[1:]}." if out["reason"] else note
    elif any(counts.values()):
        out["cost_usd"] = pp.estimate_event_cost_usd(
            model, counts["input_tokens"], counts["output_tokens"],
            counts["cache_read_tokens"], counts["cache_write_tokens"],
            provider=lookup_provider,
        )
    return out


_TOKEN_KEYS = ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens")


def resolve_usage(fact, book=None) -> dict:
    """Which rate applies to one usage record, and why. Never raises.

    ``fact`` keys (all optional): ``request_id``, ``observed_at``, ``provider``,
    ``model`` (as reported), ``deployment``, ``resource``, ``url``, ``channel``,
    ``region``, ``input_tokens``, ``output_tokens``, ``cache_read_tokens``,
    ``cache_write_tokens``, ``vendor_reported_cost_usd``.

    The result carries the resolved model and how it was found, the contract
    selection (``status`` matched | no_entry | ambiguous | no_book | no_model |
    no_timestamp | not_priceable, with the entry and its effective interval),
    the published-list basis, and whether this source counts cached tokens
    inside input tokens.
    """
    from clawmetry import providers_pricing as pp

    if not isinstance(fact, dict):
        fact = {}
    fact = dict(fact)
    at = parse_observed_at(fact.get("observed_at"))

    resource = str(fact.get("resource") or "").strip().lower() or None
    deployment = str(fact.get("deployment") or "").strip() or None
    if fact.get("url"):
        az = pp.parse_azure_openai_url(str(fact["url"]))
        if az:
            resource = resource or az["resource"]
            deployment = deployment or az.get("deployment")
    reported = str(fact.get("model") or "").strip() or None
    is_bedrock, bedrock_region = bedrock_shape(reported)
    channel = str(fact.get("channel") or "").strip().lower() or None
    if channel is None:
        if resource or deployment:
            channel = "azure-openai"
        elif is_bedrock:
            channel = "aws-bedrock"
    fact["channel"] = channel
    region = str(fact.get("region") or "").strip().lower() or bedrock_region

    alias_status, alias = _resolve_alias(book, deployment, resource, at)
    model_info = {"reported": reported, "resolved": None, "canonical": None,
                  "via": "none", "alias_id": None, "alias_status": alias_status,
                  "deployment": deployment, "resource": resource, "note": None}
    if alias_status == "matched":
        model_info.update(resolved=alias["model"], via="alias", alias_id=alias["id"])
        if reported:
            rc, ac = canonical_model(reported), canonical_model(alias["model"])
            if not rc.startswith(ac):
                model_info["note"] = (f"the response reported {reported!r}; the alias "
                                      f"{alias['id']!r} maps this deployment to {alias['model']!r}")
    elif reported:
        model_info.update(resolved=reported, via="reported")
    resolved = model_info["resolved"]
    canon = canonical_model(resolved)
    model_info["canonical"] = canon or None

    provider = str(fact.get("provider") or "").strip().lower()
    if provider in ("", "azure-openai", "aws-bedrock", "bedrock", "unknown"):
        provider = pp.provider_for_model(canon or "") or ("openai" if channel == "azure-openai" else "")

    contract = {"status": None, "entry": None, "candidates": [], "reason": None}
    usable = book is not None and bool(book.get("present")) and not book.get("errors")
    if not usable:
        contract.update(status="no_book", reason=("no price book on this machine" if not (book or {}).get("errors")
                                                  else "the price book could not be used: " + "; ".join(book["errors"])))
    elif alias_status == "ambiguous":
        contract.update(status="ambiguous", reason="more than one alias maps this deployment to different models")
    elif not canon:
        contract.update(status="no_model", reason=("the deployment has no alias and no model was reported"
                                                   if deployment else "no model is known for this record"))
    elif at is None:
        contract.update(status="no_timestamp", reason="dated rates need the time the usage was observed")
    else:
        matches = [e for e in book["entries"]
                   if _entry_matches(e, canon, provider, channel, region) and _active(e, at)]
        if not matches:
            contract.update(status="no_entry", reason="no entry covers this model, channel and date")
        else:
            best = max(_entry_rank(e) for e in matches)
            top = [e for e in matches if _entry_rank(e) == best]
            contract["candidates"] = sorted(e["id"] for e in top)
            if len(top) > 1:
                contract.update(status="ambiguous",
                                reason="entries of equal precedence both match; no rate was chosen")
            else:
                contract.update(status="matched", entry=public_entry(top[0]))

    list_basis = _list_basis(provider, resolved, fact)
    list_basis.update(financial_basis(list_basis["priced_from"], list_basis["cost_usd"],
                                      list_basis["rate_version"]))
    if contract["status"] == "matched" and contract["entry"]["discount_pct"] is not None \
            and list_basis["priced_from"] != "list":
        contract.update(status="not_priceable",
                        reason="a discount needs a published rate for this model, and there is none")

    cache_provider = "azure-openai" if channel == "azure-openai" else provider
    vendor_cost = fact.get("vendor_reported_cost_usd")
    return {
        "request_id": fact.get("request_id"),
        "observed_at": _iso(at),
        "provider": provider or None,
        "channel": channel,
        "region": region,
        "model": model_info,
        "cache_tokens_in_input": pp.cache_tokens_included_in_input(cache_provider),
        "contract": contract,
        "list": list_basis,
        "vendor_reported_cost_usd": vendor_cost if _rate_number(vendor_cost) else None,
        "book_version": (book or {}).get("version") if usable else None,
    }


# ── Valuation record contract ───────────────────────────────────────────────


def valuation_problems(record) -> list:
    """Why a valuation record may not be returned; empty when it may.

    Every valuation states its basis, amount, currency, the rate version and
    effective interval it used, and whether it restates an earlier valuation.
    """
    if not isinstance(record, dict):
        return ["a valuation must be an object"]
    problems = []
    for key in ("priced_from", "amount", "currency", "rate_version",
                "effective_from", "effective_to", "restated"):
        if key not in record:
            problems.append(f"{key} is missing")
    basis = record.get("priced_from")
    if "priced_from" in record and basis not in PRICED_FROM:
        problems.append(f"priced_from must be one of {', '.join(PRICED_FROM)}")
    amount = record.get("amount")
    if basis == "unknown":
        if amount is not None:
            problems.append("an unknown price has no amount")
    elif "amount" in record and not _rate_number(amount):
        problems.append("amount must be a number of at least 0")
    currency = record.get("currency")
    if basis != "unknown" and "currency" in record and not (isinstance(currency, str) and _CURRENCY_RE.match(currency)):
        problems.append("currency must be a three-letter code")
    if basis in ("contract", "list", "default") and not (
        isinstance(record.get("rate_version"), str) and record.get("rate_version")
    ):
        problems.append("rate_version must name the rates used")
    if basis == "contract" and not (
        isinstance(record.get("effective_from"), str) and record.get("effective_from")
    ):
        problems.append("a contract valuation must state the effective_from of its rate")
    restated = record.get("restated")
    if "restated" in record and not isinstance(restated, bool):
        problems.append("restated must be true or false")
    if restated is True:
        for key in ("restatement_of", "original_rate_version"):
            if not (isinstance(record.get(key), str) and record.get(key)):
                problems.append(f"a restatement must state {key}")
    return problems
