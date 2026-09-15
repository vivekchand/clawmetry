"""LiteLLM proxy telemetry: recognise it, and turn a proxied request into one
gateway usage record (REQ-OBS-GWY-001, issue #5940).

LiteLLM's OpenTelemetry callback (``litellm_settings: callbacks: ["otel"]``)
already knows, for every request a proxy serves, which virtual key, team and
user made it, which model it reached, the tokens it used and what LiteLLM
charged. Sent to the generic span mapper, that telemetry used to become one
"session" per request under a runtime named after the proxy, re-priced from our
own table, with the team and user dropped, and summed into the same totals the
local agents already report. This module is the translation that stops that.

Everything here is PURE: attribute dicts in, plain dicts out, no store, no
network. ``dashboard._process_otlp_traces`` calls it; the store persists what it
returns. Behaviour was established against a real LiteLLM 1.83.7 proxy backed by
its own Postgres database, not from documentation alone. What that run showed,
each point load-bearing below:

* **Recognition.** Every span LiteLLM exports carries the instrumentation scope
  ``litellm`` and the resource attribute ``model_id``, which LiteLLM's own
  resource builder sets. Proxy-internal spans (``auth``, ``postgres``,
  ``router``, ``raw_gen_ai_request``, management routes) carry both too, and
  often arrive in a different export batch from their request span.
* **The billable span.** Behind a proxy there is no ``litellm_request`` span:
  LiteLLM writes the request's attributes onto the parent
  ``Received Proxy Server Request`` span. The billable span is therefore
  identified by LiteLLM's request attributes (``llm.request.type`` plus the key
  metadata the proxy's auth sets), never by span name.
* **Identity.** ``metadata.user_api_key_team_id`` / ``..._user_id`` /
  ``..._user_email`` / ``..._org_id`` come from the key LiteLLM authenticated.
  ``metadata.team_id`` does NOT: a caller that put ``team_id`` in the request
  body's ``metadata`` saw it copied there verbatim while LiteLLM's spend log
  still billed the key's own team. Only the ``user_api_key_*`` fields are read.
* **Models.** ``gen_ai.request.model`` holds the deployment model LiteLLM
  called; ``gen_ai.response.model`` holds the name returned to the caller,
  which the proxy sets to the model group (the alias the caller asked for).
* **Cost.** ``gen_ai.cost.total_cost`` is present on successful requests,
  streaming included; ``hidden_params.response_cost`` is null on a streamed
  request, so it is only a fallback. A failed request carries neither.
* **Response cache.** A request LiteLLM answered from its own response cache
  exports the SAME ``gen_ai.response.id`` as the request it replayed, and the
  full model cost, while LiteLLM's spend log charges it nothing. Cache replays
  are therefore resolved at read time by response id (see the store), not here.
"""
from __future__ import annotations

import ast
import json
from typing import Any

from clawmetry import cost_basis as _cost_basis
from clawmetry import provenance as _prov

# Stored on the ledger row (``otlp_records.source``) and used as the span row's
# ``agent_type``, so every reader that must keep gateway figures out of agent
# figures can do it with one equality test. The colon is deliberate: an
# ``agent_type`` derived from a service name is slugified to ``[a-z0-9_]``, so
# no app can collide with it. ``litellm_gateway`` could, and did: it is exactly
# what ``OTEL_SERVICE_NAME=litellm-gateway`` slugifies to.
GATEWAY_SOURCE = "gateway:litellm"

# LiteLLM's default tracer name (``OTEL_TRACER_NAME`` overrides it; the docs say
# to keep the default for this integration).
LITELLM_SCOPE_NAME = "litellm"

COST_SOURCE_REPORTED = "gateway_reported"
COST_SOURCE_NOT_REPORTED = "not_reported"

# LiteLLM prices from its model cost map and custom pricing, both in US dollars.
GATEWAY_CURRENCY = "USD"

# The request-body ``metadata`` echo and the usage object are Python reprs, not
# JSON. Parsing is bounded so a pathological attribute cannot cost real CPU on
# the receiver (FLYWHEEL 1e).
_LITERAL_PARSE_CAP = 16_000


def _nonempty(v: Any) -> bool:
    return v is not None and v != ""


def _str_or_none(v: Any) -> str | None:
    if not _nonempty(v):
        return None
    s = str(v).strip()
    return s or None


def _float_or_none(v: Any) -> float | None:
    if not _nonempty(v):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def _int_or_none(v: Any) -> int | None:
    f = _float_or_none(v)
    return None if f is None else int(f)


def _parse_literal(v: Any) -> dict:
    """A dict from a JSON or Python-repr string LiteLLM put on a span.
    Anything else, or anything too large, is an empty dict."""
    if isinstance(v, dict):
        return v
    if not isinstance(v, str) or not v or len(v) > _LITERAL_PARSE_CAP:
        return {}
    try:
        out = json.loads(v)
    except (ValueError, TypeError):
        try:
            out = ast.literal_eval(v)
        except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
            return {}
    return out if isinstance(out, dict) else {}


def is_litellm_telemetry(scope_name: Any, resource_attrs: dict | None) -> bool:
    """True for any span LiteLLM's own OpenTelemetry integration exported.

    Both markers are required: the scope name alone could be reused by another
    instrumentation, and the ``model_id`` resource attribute is what LiteLLM's
    resource builder adds. A span that fails the test takes the unchanged
    generic path, so an unrecognised LiteLLM version degrades to today's
    behaviour rather than to silence.
    """
    return (
        str(scope_name or "") == LITELLM_SCOPE_NAME
        and isinstance(resource_attrs, dict)
        and _nonempty(resource_attrs.get("model_id"))
    )


def is_billable_request(attrs: dict | None) -> bool:
    """True for the span that carries one proxied request's usage.

    ``llm.request.type`` is written only by LiteLLM's request logger; the key
    metadata only by the proxy's auth. A LiteLLM SDK call made inside an app
    (no proxy) has the first but no key hash or proxy route.
    """
    if not isinstance(attrs, dict) or not _nonempty(attrs.get("llm.request.type")):
        return False
    return _nonempty(attrs.get("metadata.user_api_key_hash")) or _nonempty(
        attrs.get("metadata.user_api_key_request_route")
    )


def _cache_tokens(usage: dict) -> tuple[int | None, int | None]:
    """Cache-read and cache-write tokens from LiteLLM's usage object, under the
    OpenAI (``prompt_tokens_details.cached_tokens``) or Anthropic
    (``cache_read_input_tokens`` / ``cache_creation_input_tokens``) spelling.
    ``None`` when the provider reported no cache figure, never 0 by default."""
    read = _int_or_none(usage.get("cache_read_input_tokens"))
    write = _int_or_none(usage.get("cache_creation_input_tokens"))
    details = usage.get("prompt_tokens_details")
    if read is None and isinstance(details, dict):
        read = _int_or_none(details.get("cached_tokens"))
    return read, write


def ledger_record(
    *,
    attrs: dict,
    resource_attrs: dict,
    trace_id: str,
    span_id: str,
    parent_span_id: str | None,
    start_ts: float,
    duration_ms: float | None,
    status_code: Any,
    received_at: float,
) -> dict[str, Any] | None:
    """One ``otlp_records`` row for a billable LiteLLM request span, or None.

    ``record_id`` is derived from the span's own identity, so a redelivered
    export replaces its row (no total moves) while a separate request, which
    LiteLLM exports as a separate span, is a separate row.
    """
    if not is_billable_request(attrs) or not trace_id or not span_id:
        return None

    hidden = _parse_literal(attrs.get("hidden_params"))
    usage = _parse_literal(attrs.get("metadata.usage_object"))

    cost = _float_or_none(attrs.get("gen_ai.cost.total_cost"))
    if cost is None:
        cost = _float_or_none(hidden.get("response_cost"))

    error_type = _str_or_none(attrs.get("error.type"))
    # OTel status code 2 is ERROR on both decoders (protobuf enum, JSON int).
    try:
        failed = int(status_code or 0) == 2
    except (TypeError, ValueError):
        failed = str(status_code or "").upper().endswith("ERROR")
    success = not (failed or error_type)

    tokens_in = _int_or_none(attrs.get("gen_ai.usage.input_tokens"))
    tokens_out = _int_or_none(attrs.get("gen_ai.usage.output_tokens"))
    tokens_total = _int_or_none(attrs.get("gen_ai.usage.total_tokens"))
    if tokens_total is None and (tokens_in is not None or tokens_out is not None):
        tokens_total = (tokens_in or 0) + (tokens_out or 0)
    cache_read, cache_write = _cache_tokens(usage)

    deployment_model = _str_or_none(hidden.get("litellm_model_name")) or _str_or_none(
        attrs.get("gen_ai.request.model")
    )
    streaming_raw = attrs.get("llm.is_streaming")
    streaming = (
        None if not _nonempty(streaming_raw)
        else str(streaming_raw).strip().lower() == "true"
    )

    details = {
        "gateway": "litellm",
        "cost_source": COST_SOURCE_REPORTED if cost is not None else COST_SOURCE_NOT_REPORTED,
        "currency": GATEWAY_CURRENCY,
        "requested_model": _str_or_none(attrs.get("gen_ai.response.model")),
        "deployment_model": deployment_model,
        "provider": _str_or_none(attrs.get("gen_ai.system")),
        "streaming": streaming,
        "request_type": _str_or_none(attrs.get("llm.request.type")),
        "span_id": span_id,
        "parent_span_id": parent_span_id or None,
        "request_id": _str_or_none(attrs.get("gen_ai.request.id")),
        # Nothing derived from the virtual key rides in this blob: no key hash
        # and no other ``metadata.user_api_key_*`` value. The key is already
        # identified by its alias column; everything here is stored as
        # plaintext and passed through the ingest redaction scrubber, which is
        # no place for key material.
        # Supplied by the CALLER (the request's ``user`` field). Kept for the
        # record, never used to attribute spend to a team or user.
        "end_user_client_supplied": _str_or_none(attrs.get("llm.user")),
        "cache_read_tokens": cache_read,
        "cache_write_tokens": cache_write,
        "error_type": error_type,
        "service_name": _str_or_none(resource_attrs.get("service.name")),
    }

    return {
        "record_id": "{}:{}:{}".format(GATEWAY_SOURCE, trace_id, span_id),
        "ts": float(start_ts),
        "received_at": float(received_at),
        "event_name": "litellm.request",
        "session_id": None,
        "user_id": _str_or_none(attrs.get("metadata.user_api_key_user_id")),
        "user_email": _str_or_none(attrs.get("metadata.user_api_key_user_email")),
        "org_id": _str_or_none(attrs.get("metadata.user_api_key_org_id")),
        "team": _str_or_none(attrs.get("metadata.user_api_key_team_id")),
        "repo": None,
        "node_id": _str_or_none(resource_attrs.get("host.name")),
        "agent_type": GATEWAY_SOURCE,
        "service_name": _str_or_none(resource_attrs.get("service.name")),
        "model": deployment_model,
        "provider": details["provider"],
        "cost_usd": cost,
        "tokens_input": tokens_in,
        "tokens_output": tokens_out,
        "token_count": tokens_total,
        "duration_ms": duration_ms,
        "tool_name": None,
        "decision": None,
        "success": success,
        "attributes": details,
        # Typed ledger columns the gateway read groups and joins on.
        "source": GATEWAY_SOURCE,
        "cost_source": details["cost_source"],
        "trace_id": trace_id,
        "response_id": _str_or_none(attrs.get("gen_ai.response.id")),
        "key_alias": _str_or_none(attrs.get("metadata.user_api_key_alias")),
        "team_alias": _str_or_none(attrs.get("metadata.user_api_key_team_alias")),
    }


# ── Read side: gateway usage by team, user and key ───────────────────────────

_GATEWAY_USAGE_SQL = """
WITH win AS (
    SELECT record_id, ts, team, team_alias, user_id, user_email, key_alias,
           cost_usd, cost_source, success, tokens_input, tokens_output,
           trace_id, response_id
    FROM otlp_records
    WHERE source = ? AND ts >= ?
),
-- A cache replay repeats the provider response id of the request it replayed.
-- The EARLIEST record with that id is the charged one, looked up across every
-- gateway row (not only this window) so arrival order and a window boundary
-- cannot move the charge onto the replay.
firsts AS (
    SELECT response_id, MIN(ts) AS first_ts
    FROM otlp_records
    WHERE source = ?
      AND response_id IN (SELECT response_id FROM win WHERE response_id IS NOT NULL)
    GROUP BY response_id
),
first_ids AS (
    SELECT o.response_id, MIN(o.record_id) AS first_id
    FROM otlp_records o
    JOIN firsts f ON o.response_id = f.response_id AND o.ts = f.first_ts
    WHERE o.source = ?
    GROUP BY o.response_id
),
g AS (
    SELECT w.*,
           (w.response_id IS NOT NULL AND fi.first_id <> w.record_id) AS is_replay,
           EXISTS (
               SELECT 1 FROM spans s
               WHERE s.trace_id = w.trace_id AND s.agent_type <> ?
           ) AS correlated
    FROM win w
    LEFT JOIN first_ids fi ON fi.response_id = w.response_id
)
SELECT team, MAX(team_alias), user_id, MAX(user_email), key_alias,
       COUNT(*),
       SUM(CASE WHEN COALESCE(success, TRUE) = FALSE THEN 1 ELSE 0 END),
       SUM(CASE WHEN is_replay THEN 1 ELSE 0 END),
       SUM(CASE WHEN NOT is_replay AND COALESCE(success, TRUE)
                 AND COALESCE(cost_source, '') <> ? THEN 1 ELSE 0 END),
       SUM(CASE WHEN NOT is_replay AND cost_source = ? THEN cost_usd END),
       COUNT(CASE WHEN NOT is_replay AND cost_source = ? THEN 1 END),
       SUM(CASE WHEN NOT is_replay THEN tokens_input END),
       SUM(CASE WHEN NOT is_replay THEN tokens_output END),
       SUM(CASE WHEN correlated THEN 1 ELSE 0 END),
       MIN(ts), MAX(ts)
FROM g
GROUP BY team, user_id, key_alias
"""


def _blank_bucket() -> dict[str, Any]:
    return {
        "requests": 0, "failed": 0, "cache_replays": 0, "cost_not_reported": 0,
        "cost_usd": None, "tokens_input": 0, "tokens_output": 0,
        "correlated": 0, "first_ts": None, "last_ts": None,
    }


def _add_into(bucket: dict[str, Any], part: dict[str, Any]) -> None:
    for k in ("requests", "failed", "cache_replays", "cost_not_reported",
              "tokens_input", "tokens_output", "correlated"):
        bucket[k] += int(part.get(k) or 0)
    if part.get("cost_usd") is not None:
        bucket["cost_usd"] = round((bucket["cost_usd"] or 0.0) + part["cost_usd"], 10)
    for k, pick in (("first_ts", min), ("last_ts", max)):
        if part.get(k) is not None:
            bucket[k] = part[k] if bucket[k] is None else pick(bucket[k], part[k])


def gateway_usage(fetch, *, window_days: int = 7, now: float | None = None) -> dict[str, Any]:
    """Gateway usage over the last ``window_days``, grouped team -> user/key.

    Rules, each an acceptance criterion of REQ-OBS-GWY-001:

    * ``cost_usd`` sums only what the gateway REPORTED. A team whose requests
      carried no reported cost has ``cost_usd: None``, not 0; successful
      requests without a cost are counted in ``cost_not_reported``.
    * A cache replay is counted in ``requests`` and ``cache_replays`` but its
      cost and tokens are not added again (the gateway charged it nothing).
    * Failed requests are counted in ``failed``.
    * ``correlated`` counts requests whose trace also holds a span from another
      source on this store; ``uncorrelated`` is the rest. Neither is ever added
      to an agent total: this whole object is a separate subtotal.
    """
    import time as _time

    days = max(1, min(int(window_days or 7), 365))
    since = (now if now is not None else _time.time()) - days * 86400
    params = [
        GATEWAY_SOURCE, since, GATEWAY_SOURCE, GATEWAY_SOURCE, GATEWAY_SOURCE,
        COST_SOURCE_REPORTED, COST_SOURCE_REPORTED, COST_SOURCE_REPORTED,
    ]
    teams: dict[Any, dict[str, Any]] = {}
    totals = _blank_bucket()
    for row in fetch(_GATEWAY_USAGE_SQL, params) or []:
        (team, team_alias, user_id, user_email, key_alias, requests, failed,
         replays, not_reported, cost, cost_rows, tin, tout, correlated,
         first_ts, last_ts) = row
        part = {
            "user_id": user_id, "user_email": user_email, "key_alias": key_alias,
            "requests": int(requests or 0), "failed": int(failed or 0),
            "cache_replays": int(replays or 0),
            "cost_not_reported": int(not_reported or 0),
            "cost_usd": (round(float(cost), 10) if cost_rows else None),
            "tokens_input": int(tin or 0), "tokens_output": int(tout or 0),
            "correlated": int(correlated or 0),
            "first_ts": float(first_ts) if first_ts is not None else None,
            "last_ts": float(last_ts) if last_ts is not None else None,
        }
        t = teams.get(team)
        if t is None:
            t = teams[team] = {"team": team, "team_alias": team_alias,
                               **_blank_bucket(), "users": []}
        if team_alias and not t.get("team_alias"):
            t["team_alias"] = team_alias
        t["users"].append(part)
        _add_into(t, part)
        _add_into(totals, part)

    ordered = sorted(
        teams.values(),
        key=lambda t: (-(t["cost_usd"] or 0.0), -t["requests"], str(t["team"] or "")),
    )
    for t in ordered:
        t["users"].sort(key=lambda u: (-(u["cost_usd"] or 0.0), -u["requests"]))
    totals["uncorrelated"] = totals["requests"] - totals["correlated"]
    return _prov.stamp({
        "available": True,
        "gateway": "litellm",
        # WHERE the spend came from: LiteLLM priced every request, ClawMetry
        # did not. WHAT KIND of money it is rides in ``provenance``, in the one
        # cost vocabulary every other cost surface uses.
        "cost_source": COST_SOURCE_REPORTED,
        # The same fact in the price book's vocabulary
        # (``clawmetry/price_book.py::PRICED_FROM``): the vendor in front of
        # the model priced it, ClawMetry did not.
        "priced_from": GATEWAY_PRICED_FROM,
        "currency": GATEWAY_CURRENCY,
        "window_days": days,
        "totals": totals,
        "teams": ordered,
    }, gateway_provenance(days))


#: Gateway spend in the price book's ``priced_from`` vocabulary (#5959): a cost
#: the gateway computed and reported, which the price book maps onto the
#: ``published_rate`` financial basis through ``financial_basis``.
GATEWAY_PRICED_FROM = "vendor_reported"

#: Where the rate behind gateway spend comes from, for the cost badge tooltip.
GATEWAY_RATE_SOURCE = (
    "the cost LiteLLM reported for each request (gen_ai.cost.total_cost), "
    "priced by LiteLLM from its model cost map or custom prices configured on "
    "the proxy. ClawMetry does not re-price it"
)


def gateway_financial_basis() -> str:
    """The financial basis of gateway spend, taken from the price book's own
    mapping (``price_book.financial_basis``) so a gateway figure and a price
    book valuation of the same kind can never disagree. Pure: it reads no
    price book file. Never raises; ``published_rate`` if the mapping is
    unavailable, since that is what a vendor-reported cost is."""
    try:
        from clawmetry import price_book as _pb
        return _pb.financial_basis(GATEWAY_PRICED_FROM, 0.0)["cost_basis"]
    except Exception:
        return _cost_basis.PUBLISHED_RATE


def gateway_provenance(window_days: int) -> dict[str, dict[str, Any]]:
    """Provenance entries for :func:`gateway_usage` (REQ-OBS-CEA-025 labels).

    Gateway spend is labelled like every other cost ClawMetry shows
    (``clawmetry/cost_basis.py``): the arithmetic basis is ``measured`` (a sum
    of what the gateway recorded, with no re-pricing), and the financial basis
    is ``published_rate``, because a cost a gateway computed from a price map
    is usage value, not an invoice. That basis is the price book's mapping
    for ``vendor_reported`` (:func:`gateway_financial_basis`), not a second
    copy of it. ``contract`` would need a recorded rate version, which the
    telemetry does not carry, so it is never claimed. The ``rate_source``
    names LiteLLM, so the badge says whose price it is.

    A team or user whose requests carried no reported cost has
    ``cost_usd: None``; ``not_reported`` is the entry a renderer shows for
    that null, so it reads "not reported" and never "$0.00".
    """
    window = "the last %d days" % int(window_days)
    source = "duckdb:otlp_records.cost_usd (source %s, cost_source %s)" % (
        GATEWAY_SOURCE, COST_SOURCE_REPORTED)
    spend = _cost_basis.label(
        _prov.figure(
            _prov.MEASURED,
            "sum of the cost LiteLLM reported on each proxied request; a request "
            "LiteLLM answered from its own cache is counted but not charged again",
            source, window=window,
            note="if the proxy is configured with custom prices, LiteLLM applied "
                 "those, and the telemetry does not say which"),
        gateway_financial_basis(), rate_source=GATEWAY_RATE_SOURCE)
    not_reported = _cost_basis.unavailable(
        "LiteLLM reported no cost for these requests, so no amount is shown "
        "and they are not counted as free", source=source, window=window)
    return {
        "totals.cost_usd": spend,
        "teams[].cost_usd": spend,
        "teams[].users[].cost_usd": spend,
        "not_reported": not_reported,
    }
