"""What kind of money a cost figure is.

Why this file exists
--------------------
``clawmetry/provenance.py`` answers *how a number was computed*: measured,
derived, estimated or unknown. That is the right question for a score or a
threshold, and for a dollar figure it is not enough. "Derived" is true of
almost every cost ClawMetry shows (token counts times a rate), and it says
nothing about the thing a finance reviewer asks first: **is this what we were
billed?** (vivekchand/clawmetry#5937, REQ-OBS-CEA-025.)

So a cost figure carries a second, orthogonal label, its *financial basis*:

``published_rate``
    Usage value at published rates. What the usage costs at a provider's list
    price. This is nearly every figure ClawMetry has, including a cost the
    runtime reported itself: runtimes compute that from published rates too,
    so being written by the runtime makes it a *source*, not a receipt.

``contract``
    Expected contract spend. The usage priced at the operator's negotiated
    rate. Needs a contract rate version (the price book, #5936). No build
    produces one yet; the label exists so no figure can claim it wrongly.

``allocated_actual``
    Allocated actual spend. Drawn from an invoice or billing ledger. Needs a
    ledger reference. Nothing ingests invoices yet.

``unknown``
    Nobody can say what kind of money it is, so nothing is shown.

The rule that matters
---------------------
A label that says "contract" or "actual" is a claim about a bill. :func:`label`
refuses either one unless the evidence it rests on is recorded with it, and
returns an **unknown** provenance entry with the reason instead. An unknown
entry nulls the figure when stamped (see :func:`clawmetry.provenance.stamp`),
so an unevidenced "actual spend" cannot reach a screen as a number at all.
It never silently upgrades or downgrades the label.

Billing route
-------------
Separate again: *which route paid for the usage*. ``subscription`` usage is
included in a plan, so its published-rate figure is **value, not an extra
bill**. ``metered`` usage is billed per token. ``unknown`` is a route we did
not detect, and is never presented as either. ClawMetry cannot see a plan fee,
an included allowance or an overage, and says so rather than printing zero.

Existing payload keys are untouched; these fields ride inside the provenance
entry beside ``basis``, so every consumer that ignores them keeps working.
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from clawmetry import provenance as _prov

# ── The financial basis ─────────────────────────────────────────────────────

PUBLISHED_RATE = "published_rate"
CONTRACT = "contract"
ALLOCATED_ACTUAL = "allocated_actual"
UNKNOWN = "unknown"

COST_BASES = (PUBLISHED_RATE, CONTRACT, ALLOCATED_ACTUAL, UNKNOWN)

#: Short visible text beside the figure. Mirrored in static/js/provenance.js.
COST_BASIS_LABEL = {
    PUBLISHED_RATE: "published rates",
    CONTRACT: "contract rate",
    ALLOCATED_ACTUAL: "actual spend",
    UNKNOWN: "not available",
}

#: One sentence for the explanation. Mirrored in static/js/provenance.js.
COST_BASIS_HINT = {
    PUBLISHED_RATE: ("Usage value at published rates: what this usage costs "
                     "at the provider's list price. It is not an invoice."),
    CONTRACT: ("Expected contract spend: this usage priced at your "
               "negotiated rate. It is not an invoice."),
    ALLOCATED_ACTUAL: ("Allocated actual spend: drawn from an invoice or "
                       "billing ledger."),
    UNKNOWN: ("No financial basis: it is not known what kind of money this "
              "is, so no amount is shown."),
}

#: The evidence each bill-shaped basis must carry, by key.
REQUIRED_EVIDENCE = {
    CONTRACT: "rate_version",
    ALLOCATED_ACTUAL: "ledger_ref",
}

# ── The billing route ───────────────────────────────────────────────────────

ROUTE_SUBSCRIPTION = "subscription"
ROUTE_METERED = "metered"
ROUTE_UNKNOWN = "unknown"

BILLING_ROUTES = (ROUTE_SUBSCRIPTION, ROUTE_METERED, ROUTE_UNKNOWN)

BILLING_ROUTE_LABEL = {
    ROUTE_SUBSCRIPTION: ("included in a subscription: this is value, not an "
                         "extra bill"),
    ROUTE_METERED: "metered: billed per token at the provider",
    ROUTE_UNKNOWN: "billing route not detected",
}

#: Where the rate behind a published-rate figure comes from, when the figure
#: is the usual "runtime's own cost, else the price table" sum.
RATE_SOURCE_RUNTIME_OR_TABLE = (
    "the runtime's own per-call cost when it reported one (computed by the "
    "runtime from published rates), otherwise ClawMetry's published price "
    "table (clawmetry/providers_pricing.py)"
)

#: What ClawMetry cannot see about a subscription, said once.
PLAN_TERMS_UNSEEN = (
    "the provider does not expose the plan fee, included allowance or "
    "overages to ClawMetry, so none of them are included in these figures"
)


def _clean(text: Any) -> str:
    return str(text or "").strip()


def label(entry: Mapping[str, Any], cost_basis: str, *,
          rate_source: str = "",
          billing_route: Optional[str] = None,
          evidence: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    """Return ``entry`` (a provenance entry) with its financial basis attached.

    ``contract`` and ``allocated_actual`` need their evidence
    (:data:`REQUIRED_EVIDENCE`); without it the result is an ``unknown``
    provenance entry saying which evidence was missing. An unrecognised basis
    or route degrades to ``unknown`` rather than raising, because this runs
    while building payloads and a typo must not take a tab down.
    """
    base = dict(entry or {})
    b = _clean(cost_basis).lower()
    ev = {str(k): v for k, v in dict(evidence or {}).items() if v}
    if b not in COST_BASES:
        base = _prov.unknown(
            "unrecognised financial basis %r" % (cost_basis,),
            formula=base.get("formula", ""), source=base.get("source", ""))
        b = UNKNOWN
    need = REQUIRED_EVIDENCE.get(b)
    if need and not ev.get(need):
        base = _prov.unknown(
            "a %s figure needs a recorded %s and none was recorded, so it "
            "is not shown" % (COST_BASIS_LABEL[b], need),
            formula=base.get("formula", ""), source=base.get("source", ""),
            window=base.get("window"))
        b = UNKNOWN
    if base.get("basis") == _prov.UNKNOWN:
        b = UNKNOWN
    base["cost_basis"] = b
    base["cost_basis_label"] = COST_BASIS_LABEL[b]
    base["cost_basis_hint"] = COST_BASIS_HINT[b]
    if rate_source:
        base["rate_source"] = _clean(rate_source)
    if billing_route is not None:
        r = _clean(billing_route).lower()
        if r not in BILLING_ROUTES:
            r = ROUTE_UNKNOWN
        base["billing_route"] = r
        base["billing_route_label"] = BILLING_ROUTE_LABEL[r]
    if ev and b in REQUIRED_EVIDENCE:
        base["evidence"] = ev
    return base


def published_rate(formula: str, source: str, *,
                   basis: str = _prov.DERIVED,
                   rate_source: str = RATE_SOURCE_RUNTIME_OR_TABLE,
                   billing_route: Optional[str] = None,
                   **kw: Any) -> Dict[str, Any]:
    """A provenance entry for usage value at published rates.

    ``basis`` stays the arithmetic label (``derived`` for an exact rule,
    ``estimated`` when an assumption is involved); the financial label is
    always ``published_rate``.
    """
    return label(_prov.figure(basis, formula, source, **kw), PUBLISHED_RATE,
                 rate_source=rate_source, billing_route=billing_route)


def unavailable(reason: str, **kw: Any) -> Dict[str, Any]:
    """A cost figure nobody can put a basis on."""
    return label(_prov.unknown(reason, **kw), UNKNOWN)


def coverage_entries(coverage: Optional[Mapping[str, Any]],
                     source: str = "clawmetry subscription detection"
                     ) -> Dict[str, Dict[str, Any]]:
    """Provenance entries for a ``billingCoverage`` block.

    ``covered_usd`` is subscription value; ``out_of_pocket_usd`` is the rest,
    whose route is ``metered`` only when a metered runtime was detected, and
    otherwise not detected. Both are estimates, because the split is by token
    share on the assumption the detected plan is the one billed. The key name
    ``out_of_pocket_usd`` is kept for older consumers; its label says what it
    actually is.
    """
    cov = coverage or {}
    rest_route = ROUTE_METERED if cov.get("any_metered") else ROUTE_UNKNOWN
    covered = published_rate(
        "the published-rate value of usage on routes a detected subscription "
        "includes, split by token share, which assumes the detected plan is "
        "the one actually billed. It is value used, not an extra bill",
        source, basis=_prov.ESTIMATED, billing_route=ROUTE_SUBSCRIPTION,
        note=PLAN_TERMS_UNSEEN)
    rest = published_rate(
        "published-rate value of usage minus the subscription-covered share, "
        "on the same assumption",
        source, basis=_prov.ESTIMATED, billing_route=rest_route)
    plan_fee = unavailable(PLAN_TERMS_UNSEEN, source=source)
    return {
        "billingCoverage.covered_usd": covered,
        "billingCoverage.out_of_pocket_usd": rest,
        "billingCoverage.plan_fee_usd": plan_fee,
        "covered_usd": covered,
        "out_of_pocket_usd": rest,
        "plan_fee_usd": plan_fee,
    }


def entry_cost_basis(entry: Any) -> Optional[str]:
    """The financial basis on a provenance entry, or ``None``. Never raises."""
    if isinstance(entry, dict):
        got = entry.get("cost_basis")
        return got if got in COST_BASES else None
    return None
