"""Usage for work a runtime handed to another vendor's agent.

Some runtimes do not do all their own work. A Grok Bot, whose own inference
happens on an xAI cloud VM and is therefore unmeasurable from this machine
(see ``clawmetry_pro.adapters.grok_bot``), delegates tasks to **Cursor cloud
agents** -- and those are the operator's OWN agents, in the operator's own
Cursor account, metered and billed to them. The Grok Bot transcript records
the agent id and even links the operator to ``cursor.com/agents/<id>``.

So a slice of what is unknowable locally is knowable from the vendor that did
the billing. This module holds that slice, and the rules that keep it honest.

Two lanes, both landing here
----------------------------
* **Push** -- the operator's Cursor admin points Cursor's OpenTelemetry export
  at the OTLP receiver this product already runs. No credential, no outbound
  call. Cursor Enterprise only.
* **Pull** -- the operator supplies their own Cursor API key and
  ``clawmetry.cursor_connector`` asks ``GET /v1/agents/{id}/usage``. Any paid
  Cursor plan; Cursor's free tier cannot use that API at all.

Neither gate is ours. Offering this capability on our entry tier does not
widen either one, and no surface may imply that it does.

The rules this module exists to enforce
---------------------------------------
* **Delegated spend is never the session's own spend.** A Grok Bot session
  reports ``cost_status="unavailable"`` and continues to, because nobody can
  price its own reasoning. The delegated figure sits ALONGSIDE, named for the
  vendor that produced it. Summing the two would answer "what did this bot
  cost" with a number that silently omits most of the bot.
* **Attribution is bounded by what we saw locally.** Usage is attributed only
  to an agent id that appeared in a transcript on this machine. We never
  enumerate a vendor's agents, so a colleague's Cursor agent on the same team
  key cannot land on your session.
* **A guessed attribute yields nothing, never something.** Cursor's per-log
  token attribute names are not in its public docs, so the OTLP lane reads a
  candidate list. A miss records no usage rather than a wrong figure.
* **Cost carries the label its source earns.** Cursor's own docs call its cost
  metric "a best-effort USD estimate, not an invoice", and under BYOK it
  reflects only the Cursor Token Rate rather than provider spend. We therefore
  DERIVE from the token split we are given rather than passing that figure
  through, and mark it ``estimated`` when the model is unknown -- which for
  this lane is the common case, because Cursor returns tokens per agent but
  not the model that produced them.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Iterable

logger = logging.getLogger("clawmetry.delegated_usage")

#: Vendors whose delegated work we can price. Keyed by the id shape their
#: agents use, so a caller does not have to say which vendor it is holding.
CURSOR = "cursor"

#: Cursor cloud agent ids are customer-visible and prefixed. This is the only
#: shape we accept, so an unrelated session id can never be mistaken for one.
_CURSOR_ID_PREFIX = "bc-"

#: Where a figure came from, surfaced so a reader can weigh it.
SOURCE_OTEL = "cursor_otel_export"     # vendor pushed it to our receiver
SOURCE_API = "cursor_agents_api"       # we asked, with the operator's key


def is_delegated_agent_id(value: Any) -> bool:
    """True for an id shaped like a Cursor cloud agent id.

    Deliberately strict. ``session.id`` on an OTLP record can be anything at
    all, and treating an arbitrary string as a delegated agent would attribute
    a stranger's tokens to a local session.
    """
    if not isinstance(value, str):
        return False
    v = value.strip()
    return v.startswith(_CURSOR_ID_PREFIX) and len(v) > len(_CURSOR_ID_PREFIX) + 8


@dataclass
class DelegatedUsage:
    """One vendor agent's metered work.

    ``cost_usd`` is None until something can price it. That is not the same as
    zero, and the two must not be conflated: see ``cost_status``.
    """

    agent_id: str
    vendor: str = CURSOR
    source: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    model: str = ""
    cost_usd: float | None = None
    cost_status: str = "unavailable"
    updated_at: float = 0.0
    extra: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens + self.output_tokens
            + self.cache_read_tokens + self.cache_write_tokens
        )

    def to_dict(self) -> dict[str, Any]:
        d = {
            "agentId": self.agent_id,
            "vendor": self.vendor,
            "source": self.source,
            "inputTokens": self.input_tokens,
            "outputTokens": self.output_tokens,
            "cacheReadTokens": self.cache_read_tokens,
            "cacheWriteTokens": self.cache_write_tokens,
            "totalTokens": self.total_tokens,
            "model": self.model,
            "costUsd": self.cost_usd,
            "costStatus": self.cost_status,
            "updatedAt": self.updated_at,
        }
        if self.extra:
            d["extra"] = self.extra
        return d


def price(usage: DelegatedUsage) -> DelegatedUsage:
    """Derive ``cost_usd`` from the token split. Never raises.

    Cursor returns tokens per agent but NOT the model, so the model is usually
    empty here. That is precisely when a fallback rate is in play, so the label
    is ``estimated`` rather than ``derived`` -- the same distinction the Kimi
    adapter draws, and for the same reason.
    """
    if usage.total_tokens <= 0:
        usage.cost_usd = None
        usage.cost_status = "unavailable"
        return usage
    try:
        from clawmetry.providers_pricing import estimate_cost_usd, provider_for_model

        model = usage.model or ""
        provider = provider_for_model(model) if model else "anthropic"
        # Cache reads bill far below fresh input; folding them into input_tokens
        # would overcharge a cache-heavy agent, which is the common shape for a
        # long-running cloud agent re-reading the same repository.
        cost = estimate_cost_usd(
            provider,
            usage.input_tokens,
            usage.output_tokens,
            model=model,
        )
        if usage.cache_read_tokens:
            from clawmetry.providers_pricing import _CACHE_READ_MULT
            cost += estimate_cost_usd(
                provider, usage.cache_read_tokens, 0, model=model
            ) * _CACHE_READ_MULT
        usage.cost_usd = round(float(cost), 6)
        usage.cost_status = "derived" if model else "estimated"
    except Exception as exc:  # pricing must never break ingest
        logger.debug("delegated_usage: pricing failed for %s: %s", usage.agent_id, exc)
        usage.cost_usd = None
        usage.cost_status = "unavailable"
    return usage


class DelegatedUsageStore:
    """In-memory ledger keyed by vendor agent id.

    Deliberately not a DuckDB table yet: this is a small, bounded, refreshable
    cache of figures the vendor remains the system of record for. Persisting it
    would create a second source of truth for someone else's billing.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_agent: dict[str, DelegatedUsage] = {}
        #: agent ids observed in local transcripts. Attribution is bounded to
        #: these -- see the module docstring.
        self._observed: set[str] = set()

    # ── what the local transcripts told us ──────────────────────────────

    def observe(self, agent_ids: Iterable[str]) -> int:
        """Record that these agent ids appear in a transcript on this machine."""
        added = 0
        with self._lock:
            for a in agent_ids:
                if is_delegated_agent_id(a) and a not in self._observed:
                    self._observed.add(a)
                    added += 1
        return added

    def observed(self) -> set[str]:
        with self._lock:
            return set(self._observed)

    def is_observed(self, agent_id: str) -> bool:
        with self._lock:
            return agent_id in self._observed

    # ── what a vendor told us ───────────────────────────────────────────

    def record(self, usage: DelegatedUsage, *, require_observed: bool = True) -> bool:
        """Store one agent's usage. Returns False if it was not attributed.

        ``require_observed`` is the bound: usage for an agent this machine
        never saw is dropped rather than filed against nothing. The push lane
        delivers a whole team's traffic, so without this a colleague's agent
        would appear in your ledger.
        """
        if not is_delegated_agent_id(usage.agent_id):
            return False
        if require_observed and not self.is_observed(usage.agent_id):
            logger.debug(
                "delegated_usage: dropping %s -- not seen in any local transcript",
                usage.agent_id,
            )
            return False
        if not usage.updated_at:
            usage.updated_at = time.time()
        price(usage)
        with self._lock:
            self._by_agent[usage.agent_id] = usage
        return True

    def get(self, agent_id: str) -> DelegatedUsage | None:
        with self._lock:
            return self._by_agent.get(agent_id)

    def rollup(self, agent_ids: Iterable[str]) -> dict[str, Any]:
        """Aggregate the delegated work for one session's agent ids.

        The returned shape is deliberately NOT a session cost. It names the
        vendor and keeps its own status, so a caller cannot fold it into the
        session's own figure without saying so.
        """
        ids = [a for a in dict.fromkeys(agent_ids) if is_delegated_agent_id(a)]
        with self._lock:
            rows = [self._by_agent[a] for a in ids if a in self._by_agent]
        known = [r for r in rows if r.cost_usd is not None]
        cost = round(sum(r.cost_usd or 0.0 for r in known), 6) if known else None
        # One unpriced agent makes the total a floor, and saying so is the
        # difference between an honest sum and a quiet undercount.
        partial = bool(known) and len(known) != len(rows)
        if not rows:
            status = "unavailable"
        elif not known:
            status = "unavailable"
        elif any(r.cost_status == "estimated" for r in known):
            status = "estimated"
        else:
            status = "derived"
        return {
            "vendor": CURSOR,
            "agentsSeen": len(ids),
            "agentsPriced": len(known),
            "inputTokens": sum(r.input_tokens for r in rows),
            "outputTokens": sum(r.output_tokens for r in rows),
            "cacheReadTokens": sum(r.cache_read_tokens for r in rows),
            "cacheWriteTokens": sum(r.cache_write_tokens for r in rows),
            "totalTokens": sum(r.total_tokens for r in rows),
            "costUsd": cost,
            "costStatus": status,
            "isFloor": partial,
            "sources": sorted({r.source for r in rows if r.source}),
        }


_STORE = DelegatedUsageStore()


def get_store() -> DelegatedUsageStore:
    return _STORE
