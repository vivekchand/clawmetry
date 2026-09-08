"""Every number says how it was obtained.

Why this file exists
--------------------
A dashboard's job is to be believed. The category default is to print a
confident dollar figure and bury the caveat in a help page: one competitor's
documentation says outright that its numbers "are estimates, not
measurements" and warns against quoting them to two decimal places, while the
product itself renders exactly that. A reader has no way to tell which of the
figures in front of them survived that warning.

ClawMetry already keeps the discipline internally, in three places, in three
private vocabularies:

* Guard incidents carry ``spend_basis`` and refuse to invent a dollar figure
  (:mod:`clawmetry.detector_money`).
* Guard thresholds carry ``threshold_source`` so a learned number is
  distinguishable from a shipped constant
  (:func:`clawmetry.detector_calibration.resolve_thresholds`).
* Context windows carry ``source`` / ``confidence`` for the same reason
  (:mod:`clawmetry.context_windows`).

None of that reaches the person reading the number. This module is the one
vocabulary those three collapse into, and the seam that puts it on screen.

The four bases
--------------
``measured``
    Read from a record the producer wrote, or a plain aggregation (sum,
    count, min, max) of such records over a stated window. No modelling.
    Summing the ``cost_usd`` an adapter recorded per call is measured; so is
    a threshold an operator set by hand, or one learned from observed
    sessions.

``derived``
    Computed from measured inputs by an exact rule: a price-table lookup
    times a measured token count, a ratio of two measured figures, a rate
    over a measured duration. The rule can be written down and checked, and
    nothing about unobserved data is assumed.

``estimated``
    A model with an assumption that can be wrong. A forecast, a session cost
    apportioned by "spend is even across the window", a shipped default
    standing in for a measurement nobody took. Useful, and may not be quoted
    as a fact.

``unknown``
    We could not obtain it. **The value is ``None``, never ``0.0``.**

Why unknown is not zero
-----------------------
This is the trap the module exists to close. On 2026-08-22 a failed DuckDB
read was published as ``$0.00`` and read, correctly, as a real result: a zero
and a hole are indistinguishable once formatted, and the hole is the one that
matters. So the two are not allowed to share a shape. Label a figure
``unknown`` and :func:`stamp` nulls the value it labels on the way out, which
means a renderer physically cannot print ``$0.00`` for a number nobody knows.
A genuine measured zero keeps its ``0.0`` and its ``measured`` badge, and the
two read differently on screen.

Using it
--------
Provenance is attached beside the figures, never in place of them::

    return provenance.stamp({
        "todayCost": 4.12,
        "weekCost": 18.30,
    }, {
        "todayCost": provenance.measured(
            "sum(cost_usd) over events in the window",
            "duckdb:daily_aggregates.cost_usd",
            window="today (local calendar day)",
            inputs={"days": 1},
        ),
        "weekCost": ...,
    })

Existing consumers keep reading ``payload["todayCost"]`` unchanged; the badge
reads ``payload["provenance"]["todayCost"]``. That matters more than elegance:
the hosted dashboard, the desk device and three cloud interceptors all parse
these payloads, and rewriting every scalar into an object would break all of
them at once.

:func:`audit_payload` walks a payload, finds every money-shaped and
score-shaped number in it, and reports the ones with no basis. It discovers
figures by shape rather than from a hand-kept list, because a hand-kept list
of "figures we remembered to label" is exactly the thing that drifts.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

# ── The vocabulary ───────────────────────────────────────────────────────────

MEASURED = "measured"
DERIVED = "derived"
ESTIMATED = "estimated"
UNKNOWN = "unknown"

BASES = (MEASURED, DERIVED, ESTIMATED, UNKNOWN)

#: One sentence per basis, for the badge tooltip. Kept here rather than in the
#: frontend so the Python side, the JS side and the docs cannot drift apart.
BASIS_HINT = {
    MEASURED: "Measured: read from a record the agent wrote.",
    DERIVED: "Derived: computed from measured inputs by an exact rule.",
    ESTIMATED: "Estimated: modelled, with an assumption that can be wrong.",
    UNKNOWN: "No basis: this number is not available, so nothing is shown.",
}

#: Short badge text. Deliberately lower-case and boring; a badge that shouts
#: gets ignored, and this one has to survive appearing next to every figure.
BASIS_LABEL = {
    MEASURED: "measured",
    DERIVED: "derived",
    ESTIMATED: "estimated",
    UNKNOWN: "no basis",
}

#: Where the provenance map hangs off a payload.
PROVENANCE_KEY = "provenance"

#: Bumped when the entry shape changes, so a cloud renderer served by an older
#: daemon can tell it is looking at a shape it does not fully understand.
PROVENANCE_VERSION = 1


def _clean(text: Any) -> str:
    return str(text or "").strip()


def figure(basis: str, formula: str, source: str, *,
           window: Optional[str] = None,
           inputs: Optional[Mapping[str, Any]] = None,
           reason: Optional[str] = None,
           note: Optional[str] = None) -> Dict[str, Any]:
    """One provenance entry.

    ``formula`` is how the number was computed, in words a reader can check
    against the code. ``source`` is where the inputs came from (a table and
    column, an API, a config key). ``window`` is the period it covers, when
    that is part of what the number means. ``inputs`` are the actual operand
    values, so a reader can reconstruct the figure rather than take it on
    faith.

    An unrecognised basis degrades to ``unknown`` rather than raising: this
    runs on the ingest path, and a typo must not take a dashboard down. It is
    loud on screen ("no basis"), which is how it gets fixed.
    """
    b = _clean(basis).lower()
    extra_note = note
    if b not in BASES:
        extra_note = "unrecognised basis %r" % (basis,)
        b = UNKNOWN
    entry: Dict[str, Any] = {
        "basis": b,
        "label": BASIS_LABEL[b],
        "hint": BASIS_HINT[b],
        "formula": _clean(formula),
        "source": _clean(source),
    }
    if window:
        entry["window"] = _clean(window)
    if inputs:
        try:
            entry["inputs"] = {str(k): v for k, v in dict(inputs).items()}
        except (TypeError, ValueError):
            pass
    if reason:
        entry["reason"] = _clean(reason)
    if extra_note:
        entry["note"] = _clean(extra_note)
    return entry


def measured(formula: str, source: str, **kw: Any) -> Dict[str, Any]:
    """A figure read from a record, or aggregated from records."""
    return figure(MEASURED, formula, source, **kw)


def derived(formula: str, source: str, **kw: Any) -> Dict[str, Any]:
    """A figure computed from measured inputs by an exact rule."""
    return figure(DERIVED, formula, source, **kw)


def estimated(formula: str, source: str, **kw: Any) -> Dict[str, Any]:
    """A figure that rests on an assumption which can be wrong."""
    return figure(ESTIMATED, formula, source, **kw)


def unknown(reason: str, *, formula: str = "", source: str = "",
            **kw: Any) -> Dict[str, Any]:
    """A figure nobody knows.

    ``reason`` is the thing a reader actually wants: not "no data" but "the
    local store did not answer", "this runtime records no per-call cost",
    "the session ended before a price was resolved".
    """
    return figure(UNKNOWN, formula, source, reason=reason, **kw)


# ── Attaching it to a payload ────────────────────────────────────────────────

def stamp(payload: Dict[str, Any],
          entries: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    """Attach ``entries`` to ``payload`` under ``provenance``, and null every
    figure labelled ``unknown``.

    The nulling is the point, not a side effect. It is what makes "an unknown
    cost never renders as a real zero" a property of the data rather than a
    rule every renderer has to remember. Existing keys are untouched
    otherwise, so consumers that never heard of provenance keep working.

    Merges into an existing ``provenance`` map rather than replacing it, so a
    handler can stamp what it knows and a wrapper can add the rest.
    """
    if not isinstance(payload, dict):
        return payload
    existing = payload.get(PROVENANCE_KEY)
    prov: Dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
    for key, entry in (entries or {}).items():
        if not isinstance(entry, dict):
            continue
        prov[str(key)] = dict(entry)
        if entry.get("basis") == UNKNOWN and str(key) in payload:
            payload[str(key)] = None
    payload[PROVENANCE_KEY] = prov
    payload.setdefault("provenance_version", PROVENANCE_VERSION)
    return payload


def entry_for(payload: Any, key: str) -> Optional[Dict[str, Any]]:
    """The provenance entry for ``key``, or ``None``. Never raises."""
    if not isinstance(payload, dict):
        return None
    prov = payload.get(PROVENANCE_KEY)
    if not isinstance(prov, dict):
        return None
    got = prov.get(key)
    return got if isinstance(got, dict) else None


# ── Translating the vocabularies that came first ─────────────────────────────
#
# Guard, the calibrator and the context-window resolver each grew their own
# word for this before there was a shared one. Rather than rename their
# fields (and break every consumer and test that reads them), map them here.
# One place to look when the mapping is questioned.

#: ``detector_money.annotate_spend`` → basis.
#: ``burn_rate`` prices a stretch against a real clock, so it is measured.
#: ``window_fraction`` assumes spend is even across the window, which on real
#: sessions attributed most of a $100 session to four failed greps, so it is
#: an estimate and never escalates anything.
SPEND_BASIS_TO_PROVENANCE = {
    "burn_rate": MEASURED,
    "window_fraction": ESTIMATED,
    "unknown": UNKNOWN,
}

_SPEND_BASIS_FORMULA = {
    "burn_rate": ("session cost ÷ session minutes, times the minutes the "
                  "session has been flagged"),
    "window_fraction": ("session cost times (steps after the first bad step ÷ "
                        "steps in the window), which assumes spend is even "
                        "across the window"),
}

#: ``detector_calibration.resolve_thresholds`` → basis. An operator's env
#: override and a learned cohort baseline are both records somebody wrote or
#: something we observed; the runtime profile is a checkable fact about the
#: adapter; a shipped static default is a guess standing in for a measurement.
THRESHOLD_SOURCE_TO_PROVENANCE = {
    "env_runtime": MEASURED,
    "baseline": MEASURED,
    "runtime_profile": DERIVED,
    "static": ESTIMATED,
}

#: ``context_windows.resolve_context_window`` → basis.
CONTEXT_CONFIDENCE_TO_PROVENANCE = {
    "exact": MEASURED,
    "inferred": DERIVED,
    "fallback": ESTIMATED,
}


def from_spend_basis(spend_basis: Any, *,
                     inputs: Optional[Mapping[str, Any]] = None,
                     window: Optional[str] = None) -> Dict[str, Any]:
    """A provenance entry for a Guard incident's ``spend_at_risk_usd``."""
    key = _clean(spend_basis).lower() or "unknown"
    basis = SPEND_BASIS_TO_PROVENANCE.get(key, UNKNOWN)
    if basis == UNKNOWN:
        return unknown(
            "no cost was recorded for this session, so the spend behind the "
            "flagged stretch cannot be priced",
            source="clawmetry.detector_money.annotate_spend",
            inputs=inputs, window=window)
    return figure(basis, _SPEND_BASIS_FORMULA.get(key, key),
                  "clawmetry.detector_money.annotate_spend",
                  inputs=inputs, window=window)


def from_threshold_source(threshold_source: Any, *,
                          inputs: Optional[Mapping[str, Any]] = None
                          ) -> Dict[str, Any]:
    """A provenance entry for a Guard threshold."""
    key = _clean(threshold_source).lower()
    basis = THRESHOLD_SOURCE_TO_PROVENANCE.get(key, ESTIMATED)
    formulas = {
        "env_runtime": "set by hand for this runtime via an env override",
        "baseline": "learned from this cohort's observed sessions, clamped to "
                    "a band around the shipped default",
        "runtime_profile": "the runtime adapter's own write-tool vocabulary",
        "static": "the shipped default; no measurement of this cohort",
    }
    return figure(basis, formulas.get(key, "threshold source %r" % (key,)),
                  "clawmetry.detector_calibration.resolve_thresholds",
                  inputs=inputs)


def from_context_confidence(confidence: Any, *,
                            inputs: Optional[Mapping[str, Any]] = None
                            ) -> Dict[str, Any]:
    """A provenance entry for a context-window denominator."""
    key = _clean(confidence).lower()
    basis = CONTEXT_CONFIDENCE_TO_PROVENANCE.get(key, ESTIMATED)
    formulas = {
        "exact": "the model string carries an explicit window marker, or a "
                 "prompt larger than the table value was observed",
        "inferred": "matched against the published context-window table",
        "fallback": "no table entry matched this model, so the documented "
                    "default is standing in",
    }
    return figure(basis, formulas.get(key, "context window %r" % (key,)),
                  "clawmetry.context_windows.resolve_context_window",
                  inputs=inputs)


# ── The audit: find figures by shape, not from a list ────────────────────────
#
# A hand-kept register of "figures we remembered to label" drifts the moment
# somebody adds a card. So the audit recognises a figure by the shape of its
# key, and a new unlabelled one fails the guard the day it lands.

_MONEY_SUFFIXES = ("_usd", "usd", "_cost", "cost", "_spend", "spend",
                   "_savings", "savings", "_price", "price")
_SCORE_SUFFIXES = ("_score", "score")

#: Keys that end money-shaped or score-shaped but are not figures: a window
#: length, a row count, a flag, or the provenance bookkeeping itself.
_NOT_A_FIGURE = frozenset({
    "provenance_version", "cost_basis", "spend_basis", "score_basis",
    "cost_source", "score_source", "cost_window", "cost_window_days",
    "has_cost", "any_cost", "cost_count", "score_count", "price_id",
    "stripe_price", "stripe_price_id",
})


def figure_kind(key: Any) -> Optional[str]:
    """``"money"``, ``"score"`` or ``None`` for a payload key.

    Matched on the lower-cased key so ``todayCost`` and ``today_cost`` are the
    same thing, which they are.
    """
    k = _clean(key).lower()
    if not k or k in _NOT_A_FIGURE:
        return None
    if any(k.endswith(s) for s in _MONEY_SUFFIXES):
        return "money"
    if any(k.endswith(s) for s in _SCORE_SUFFIXES):
        return "score"
    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def audit_payload(payload: Any, *, path: str = "") -> List[Dict[str, Any]]:
    """Every money-shaped or score-shaped number with no basis behind it.

    Walks nested dicts and lists. A figure counts as labelled when any
    provenance map on the way down to it names either the figure's key or the
    path from that map to the figure (``"sessions[].cost_usd"``), so a
    collection of rows is labelled once rather than per row.

    Returns a list of ``{"path", "key", "kind", "value"}``, empty when the
    payload is clean. Never raises: an un-walkable branch is skipped, because
    an audit that crashes on a surprise shape teaches nobody anything.
    """
    found: List[Dict[str, Any]] = []
    _walk(payload, path, (), found)
    return found


def _labelled(maps, key: str, trails) -> bool:
    for prov, trail in zip(maps, trails):
        if key in prov:
            return True
        if trail and trail in prov:
            return True
    return False


def _walk(node: Any, path: str, scopes: tuple, found: List[Dict[str, Any]],
          _depth: int = 0) -> None:
    if _depth > 12:
        return
    if isinstance(node, dict):
        prov = node.get(PROVENANCE_KEY)
        # Each scope is (provenance map, path of the dict that owns it).
        here = scopes
        if isinstance(prov, dict):
            here = scopes + ((prov, path),)
        for key, value in node.items():
            if key == PROVENANCE_KEY:
                continue
            child = "%s.%s" % (path, key) if path else str(key)
            kind = figure_kind(key)
            if kind and _is_number(value):
                maps = [p for p, _ in here]
                trails = [_trail(owner, child) for _, owner in here]
                if not _labelled(maps, str(key), trails):
                    found.append({"path": child, "key": str(key),
                                  "kind": kind, "value": value})
                continue
            _walk(value, child, here, found, _depth + 1)
    elif isinstance(node, (list, tuple)):
        # Rows in a collection share one label, so the path they are audited
        # under is the collection's, with the index collapsed to "[]".
        for item in node[:200]:
            _walk(item, path + "[]", scopes, found, _depth + 1)


def _trail(owner_path: str, child_path: str) -> str:
    if owner_path and child_path.startswith(owner_path + "."):
        return child_path[len(owner_path) + 1:]
    return child_path


def assert_labelled(payload: Any, where: str = "payload") -> None:
    """Raise ``AssertionError`` naming every unlabelled figure.

    The guard tests call this; so can a handler under
    ``CLAWMETRY_STRICT_PROVENANCE=1`` if we ever want it enforced at runtime.
    """
    gaps = audit_payload(payload)
    if gaps:
        lines = "\n".join(
            "  %s = %r (%s)" % (g["path"], g["value"], g["kind"]) for g in gaps)
        raise AssertionError(
            "%s renders %d figure(s) with no basis:\n%s\n"
            "Give each one a provenance entry (clawmetry.provenance.stamp) or "
            "stop rendering it." % (where, len(gaps), lines))
