"""Usage valued from the price book, when it is read.

REQ-OBS-CEA-024 (Software Factory), second increment: AC-OBS-CEA-024.12, .13,
.14 and .17. Issue #5936.

The design, smallest that is safe:

* **The fact is stored once.** A usage fact is the recorded billable turn in
  the events table (model, observed time, token categories, Azure deployment
  and resource when the interceptor saw them), read through the store's
  ``query_usage_facts``. No valuation table, no daemon pricing pass, no
  backfill, and nothing is ever written back.
* **The valuation is derived on read,** against the book version that was in
  effect when the usage was observed (``price_book_edit.timeline``). Editing a
  rate changes usage from the moment the edit comes into effect; usage before
  it keeps the valuation it had. Valuing history against a different version
  is a restatement, and only happens when the caller asks (``restate``).
* **Selection is open source, arithmetic is not.** Each fact is resolved with
  ``price_book.resolve_usage``; amounts come from the paid engine behind
  ``pricing.value_usage``. Without an engine the block still says how much
  usage the book covers and what could not be priced, and says plainly that
  contract amounts need the engine.
* **A contract figure is only as good as its evidence.** A valuation labelled
  contract must come from a resolution that matched exactly one entry and
  name a book version that is recorded on disk; anything else is withheld
  from the contract figure (AC-OBS-CEA-024.12, .14). Ambiguous usage is
  counted as unknown with its reason and adds no amount.

Facts that resolve identically (same local day, model, provider, deployment,
resource, book version, and the same stretch between two rate boundaries) are
summed before valuation, so a month of turns costs a handful of calls. A turn
with more cached than input tokens is never merged, so a source that counts
cache inside input still reports that record as unknown instead of hiding it
in a sum.

Only the local ``/api/usage`` handler calls this module. The daemon, the
snapshot and every exporter never import it (tests/test_price_book.py,
tests/test_price_book_usage.py).
"""
from __future__ import annotations

import bisect
import hashlib
import json
import threading
import time
from datetime import datetime, timedelta

from clawmetry import cost_basis as cb
from clawmetry import price_book as pb
from clawmetry import price_book_edit as pe
from clawmetry import provenance as prov

MAX_FACTS = 50000
CACHE_TTL_S = 20.0

_TOKEN_KEYS = ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens")
_WINDOWS = ("today", "week", "month")
_WINDOW_TEXT = {
    "today": "today, the local calendar day",
    "week": "this week, the local calendar week starting Monday",
    "month": "this month, the local calendar month from the 1st",
}
RULE = ("Each model call is valued against the price book version that was in effect when "
        "it happened. Editing the book changes usage from that moment on; earlier usage keeps "
        "its valuation unless you restate it.")
NO_ENGINE = ("Contract amounts need the valuation engine, which this build does not include. "
             "The figures below show how much usage your price book covers.")

_cache_lock = threading.Lock()
_cache: dict = {}


def _local_day(ts) -> str:
    try:
        from clawmetry.cost_windows import local_day
        return local_day(ts) or ""
    except Exception:
        return str(ts or "")[:10]


def window_start(now=None) -> str:
    """The earliest local day any Usage window needs (14-day chart or month)."""
    now = now or datetime.now()
    return min((now - timedelta(days=13)).strftime("%Y-%m-%d"), now.strftime("%Y-%m-01"))


def facts_since(now=None) -> str:
    """A UTC ISO lower bound for the store read, one day early so a local day
    that starts before UTC midnight is not cut off."""
    day = datetime.strptime(window_start(now), "%Y-%m-%d") - timedelta(days=1)
    return day.strftime("%Y-%m-%dT00:00:00")


def _boundaries(book) -> list:
    out = set()
    for item in list(book.get("entries", [])) + list(book.get("aliases", [])):
        for key in ("_from", "_to"):
            if item.get(key) is not None:
                out.add(item[key])
    return sorted(out)


def _count(raw) -> int:
    return int(raw) if pb._rate_number(raw) else 0


def _group_facts(facts, versions, load):
    """Sum facts that must resolve identically. Returns ``[(version, fact,
    events)]``; ``version`` is a ledger entry or None (no book in effect)."""
    groups, order = {}, []
    bounds_for = {}
    for i, raw in enumerate(facts):
        if not isinstance(raw, dict):
            continue
        at = pb.parse_observed_at(raw.get("observed_at"))
        day = _local_day(raw.get("observed_at")) if at else ""
        entry = pe.version_in_effect(at, versions)
        version = entry["version"] if entry else None
        book = load(version) if version else None
        if version and version not in bounds_for:
            bounds_for[version] = _boundaries(book) if book else []
        segment = bisect.bisect_right(bounds_for.get(version, []), at) if at else -1
        dims = tuple(str(raw.get(k) or "") for k in ("model", "provider", "deployment", "resource",
                                                     "channel", "region"))
        tokens = {k: raw.get(k) for k in _TOKEN_KEYS}
        odd = any(v is not None and not pb._rate_number(v) for v in tokens.values()) or (
            _count(tokens["cache_read_tokens"]) + _count(tokens["cache_write_tokens"])
            > _count(tokens["input_tokens"]))
        key = (day, dims, version, segment, i if odd else None)
        if key not in groups:
            fact = {k: raw.get(k) for k in ("model", "provider", "deployment", "resource", "channel", "region")}
            fact.update({k: (raw.get(k) if odd else 0) for k in _TOKEN_KEYS})
            fact["observed_at"] = raw.get("observed_at")
            fact["request_id"] = "usage-" + hashlib.sha256(
                json.dumps([day, dims, version, segment, i if odd else None], default=str).encode()
            ).hexdigest()[:20]
            groups[key] = {"version": entry, "fact": fact, "events": 0, "day": day}
            order.append(key)
        g = groups[key]
        g["events"] += 1
        if not odd:
            for k in _TOKEN_KEYS:
                g["fact"][k] += _count(tokens[k])
    return [groups[k] for k in order]


def _engine_answer(payload):
    from clawmetry import extensions

    return extensions.call(pb.VALUE_USAGE_EVENT, payload, default=None)


def _day_windows(now):
    now = now or datetime.now()
    today = now.strftime("%Y-%m-%d")
    return {
        "today": today,
        "week": (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d"),
        "month": now.strftime("%Y-%m-01"),
    }, [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(13, -1, -1)], today


def _empty_window():
    return {"contract_usd": None, "covered_published_usd": 0.0, "published_usd": 0.0,
            "events": 0, "covered_events": 0, "unknown_events": 0, "contract_versions": []}


def _add(bucket, key, amount):
    if amount is None:
        return
    bucket[key] = round((bucket.get(key) or 0.0) + float(amount), 8)


def build_block(facts, *, now=None, restate=None, book=None, truncated=False):
    """The ``priceBook`` block for ``/api/usage``. Never raises.

    ``facts`` are store usage facts; ``restate`` is ``"current"`` or a recorded
    version id to value every fact against instead (a labelled restatement,
    returned beside the original, never in place of it).
    """
    try:
        return _build_block(facts, now=now, restate=restate, book=book, truncated=truncated)
    except Exception:  # pragma: no cover - an honest absence beats a 500 on Usage
        return {"present": True, "usable": False,
                "errors": ["the price book figures could not be built for this request"]}


def _build_block(facts, *, now, restate, book, truncated):
    book = book if book is not None else pb.load_price_book()
    if not book.get("present"):
        return {"present": False}
    if book.get("errors"):
        return {"present": True, "usable": False, "errors": list(book["errors"])}
    pe.activate(book)
    ledger = pe.timeline()

    loaded = {}

    def load(version):
        if version not in loaded:
            loaded[version] = pb.load_version(version)
        return loaded[version]

    groups = _group_facts(facts or [], ledger, load)
    engine_seen = False
    windows_by, chart_days, _today = _day_windows(now)
    windows = {w: _empty_window() for w in _WINDOWS}
    days = {d: {"date": d, "contract_usd": None, "covered_published_usd": 0.0, "unknown_events": 0}
            for d in chart_days}
    unknown, unknown_today, withheld = {}, {}, 0

    restate_book = None
    restate_version = None
    if restate:
        if restate == "current":
            restate_book = book if pb.record_version(book) else None
        else:
            restate_book = load(restate)
        restate_version = restate_book.get("version") if restate_book else None
    restatement = None
    if restate:
        restatement = {"requested": restate, "against": restate_version,
                       "available": bool(restate_book),
                       "windows": {w: {"restated_usd": None, "original_usd": None, "delta_usd": None,
                                       "events": 0} for w in _WINDOWS}}

    by_version = {}
    for g in groups:
        by_version.setdefault(g["version"]["version"] if g["version"] else None, []).append(g)

    for version, members in by_version.items():
        vbook = load(version) if version else None
        facts_v = [g["fact"] for g in members]
        resolutions = [pb.resolve_usage(f, vbook) for f in facts_v]
        payload = {"facts": facts_v, "resolutions": resolutions,
                   "book": pb.public_book(vbook) if vbook else None,
                   "restate_against": pb.public_book(restate_book) if restate_book else None,
                   "restated_resolutions": ([pb.resolve_usage(f, restate_book) for f in facts_v]
                                            if restate_book else None)}
        answer = _engine_answer(payload)
        records = answer.get("valuations") if isinstance(answer, dict) else None
        if isinstance(records, list):
            engine_seen = True
        originals, restated = {}, {}
        for rec in records if isinstance(records, list) else []:
            if not isinstance(rec, dict) or pb.valuation_problems(rec):
                withheld += 1
                continue
            idx = rec.get("index")
            if not isinstance(idx, int) or not 0 <= idx < len(members):
                withheld += 1
                continue
            (restated if rec.get("restated") else originals)[idx] = rec

        for idx, g in enumerate(members):
            res = resolutions[idx]
            status = (res.get("contract") or {}).get("status")
            listed = res.get("list") or {}
            rec = originals.get(idx)
            day, n = g["day"], g["events"]
            # By name: two windows with equal figures compare equal as dicts.
            names = [w for w in _WINDOWS if day and day >= windows_by[w]]
            targets = [windows[w] for w in names]
            day_row = days.get(day)
            for t in targets:
                t["events"] += n
            reason = None
            contract_ok = (rec is not None and rec.get("priced_from") == "contract"
                           and status == "matched" and version is not None
                           and rec.get("rate_version") == version and load(version) is not None)
            if status == "matched":
                for t in targets:
                    t["covered_events"] += n
            if contract_ok:
                for t in targets:
                    _add(t, "contract_usd", rec.get("amount"))
                    _add(t, "covered_published_usd", listed.get("cost_usd"))
                    if version not in t["contract_versions"]:
                        t["contract_versions"].append(version)
                if day_row is not None:
                    _add(day_row, "contract_usd", rec.get("amount"))
                    _add(day_row, "covered_published_usd", listed.get("cost_usd"))
            elif status in ("ambiguous", "not_priceable", "no_timestamp", "no_model") or (
                    rec is not None and rec.get("priced_from") == "unknown"):
                reason = (rec or {}).get("reason") or (res.get("contract") or {}).get("reason") \
                    or "no rate could be selected for this usage"
            elif status == "matched":
                # Matched, but no contract amount came back that can carry the
                # label: no engine, or the engine's record failed the checks.
                if engine_seen or rec is not None:
                    reason = "the contract valuation for this usage was withheld because it did not state its basis"
                for t in targets:
                    _add(t, "covered_published_usd", listed.get("cost_usd"))
                if day_row is not None:
                    _add(day_row, "covered_published_usd", listed.get("cost_usd"))
            else:
                amount = rec.get("amount") if rec is not None and rec.get("priced_from") in (
                    "list", "default", "vendor_reported") else listed.get("cost_usd")
                for t in targets:
                    _add(t, "published_usd", amount)
            if reason:
                for t in targets:
                    t["unknown_events"] += n
                if day_row is not None:
                    day_row["unknown_events"] += n
                if "month" in names:
                    unknown[reason] = unknown.get(reason, 0) + n
                if "today" in names:
                    unknown_today[reason] = unknown_today.get(reason, 0) + n

            if restatement is not None and idx in restated:
                r = restated[idx]
                for w in _WINDOWS:
                    if day and day >= windows_by[w]:
                        rw = restatement["windows"][w]
                        rw["events"] += n
                        # One basis per figure: only usage the restated book
                        # prices at a contract rate is summed, beside what
                        # that same usage was originally reported as.
                        if r.get("priced_from") == "contract" and r.get("amount") is not None \
                                and r.get("original_amount") is not None:
                            _add(rw, "restated_usd", r["amount"])
                            _add(rw, "original_usd", r["original_amount"])

    for w in _WINDOWS:
        t = windows[w]
        t["covered_published_usd"] = round(t["covered_published_usd"], 6)
        t["published_usd"] = round(t["published_usd"], 6)
        if t["contract_usd"] is not None:
            t["contract_usd"] = round(t["contract_usd"], 6)
    if restatement is not None:
        for rw in restatement["windows"].values():
            if rw["restated_usd"] is not None and rw["original_usd"] is not None:
                rw["delta_usd"] = round(rw["restated_usd"] - rw["original_usd"], 6)

    in_window = sorted({g["version"]["version"] for g in groups if g["version"]})
    block = {
        "present": True,
        "usable": True,
        "book_version": book.get("version"),
        "engine": engine_seen or _engine_registered(),
        "rule": RULE,
        "message": None if (engine_seen or _engine_registered()) else NO_ENGINE,
        "versions": [row for row in ledger if row["version"] in in_window or row["version"] == book.get("version")],
        "windows": windows,
        "days": [days[d] for d in chart_days],
        "unknown": [{"reason": r, "events": c} for r, c in sorted(unknown.items(), key=lambda kv: -kv[1])],
        "unknown_today": [{"reason": r, "events": c}
                          for r, c in sorted(unknown_today.items(), key=lambda kv: -kv[1])],
        "withheld": withheld,
        "restatement": restatement,
        "truncated": bool(truncated),
        "facts_read": len(facts or []),
    }
    block["provenance"] = _provenance(block)
    return block


def _engine_registered() -> bool:
    try:
        from clawmetry import extensions
        return pb.VALUE_USAGE_EVENT in extensions.registered_events()
    except Exception:
        return False


def _provenance(block) -> dict:
    source = "stored usage events valued at read time against your price book"
    out = {}
    for w in _WINDOWS:
        t = block["windows"][w]
        versions = t.get("contract_versions") or []
        if t.get("contract_usd") is None:
            why = (NO_ENGINE if not block["engine"] else
                   "no usage in this window was valued at a contract rate")
            out[f"windows.{w}.contract_usd"] = cb.unavailable(why, source=source, window=_WINDOW_TEXT[w])
        else:
            out[f"windows.{w}.contract_usd"] = cb.label(
                prov.figure(prov.DERIVED, "the usage your price book covers, each model call priced at the "
                            "entry in the book version in effect when it happened", source,
                            window=_WINDOW_TEXT[w]),
                cb.CONTRACT, rate_source="your price book", evidence={"rate_version": ", ".join(versions)})
        out[f"windows.{w}.covered_published_usd"] = cb.published_rate(
            "the same covered usage at published rates, for comparison", source, window=_WINDOW_TEXT[w],
            rate_source="ClawMetry's published price table (clawmetry/providers_pricing.py)")
        out[f"windows.{w}.published_usd"] = cb.published_rate(
            "usage your price book does not cover, at published rates", source, window=_WINDOW_TEXT[w],
            rate_source="ClawMetry's published price table (clawmetry/providers_pricing.py)")
        rs = block.get("restatement")
        if rs:
            rw = rs["windows"][w]
            if rw.get("restated_usd") is None or not rs.get("against"):
                out[f"restatement.windows.{w}.restated_usd"] = cb.unavailable(
                    "nothing in this window could be restated", source=source, window=_WINDOW_TEXT[w])
            else:
                entry = prov.figure(prov.DERIVED, "a restatement: this window's usage valued against book "
                                    "version " + rs["against"] + " instead of the version in effect at the time",
                                    source, window=_WINDOW_TEXT[w], note="not saved; the original stays as reported")
                out[f"restatement.windows.{w}.restated_usd"] = cb.label(
                    entry, cb.CONTRACT, rate_source="your price book", evidence={"rate_version": rs["against"]})
    return out


def usage_block(*, runtime=None, restate=None, facts_loader=None, now=None):
    """Cached :func:`build_block` for the ``/api/usage`` handler.

    ``facts_loader(since, limit)`` returns store usage facts or None. The cache
    key includes the book file and ledger state, so a save or a hand edit is
    seen on the next request. Never raises.
    """
    try:
        import os

        def _stat(path):
            try:
                st = os.stat(path)
                return (st.st_mtime_ns, st.st_size)
            except OSError:
                return None

        key = (runtime or "", restate or "", pb.default_path(), _stat(pb.default_path()),
               _stat(pe.ledger_path()), _engine_registered())
        with _cache_lock:
            hit = _cache.get(key)
            if hit and time.monotonic() - hit[0] < CACHE_TTL_S:
                return hit[1]
        book = pb.load_price_book()
        if not book.get("present"):
            block = {"present": False}
        else:
            facts = []
            if not book.get("errors") and facts_loader is not None:
                facts = facts_loader(facts_since(now), MAX_FACTS) or []
            block = build_block(facts, now=now, restate=restate, book=book,
                                truncated=len(facts) >= MAX_FACTS)
        with _cache_lock:
            if len(_cache) > 32:
                _cache.clear()
            _cache[key] = (time.monotonic(), block)
        return block
    except Exception:  # pragma: no cover
        return None


def clear_cache():
    with _cache_lock:
        _cache.clear()
