"""Cost Optimizer advice: observed provider routes, experiments, and cost basis.

Fulfils REQ-OBS-CEA-023 (Cost and Efficiency Analytics > "Cost Optimizer:
honest, fast and provider-aware"), vivekchand/clawmetry#5934. Served by
``GET /api/cost-optimizer`` in ``routes/infra.py`` and rendered by
``loadCostOptimizerData`` in ``clawmetry/static/js/app.js``.

The optimizer used to print advice nobody measured: a fixed "60-80% with
local models" claim, per-model "~$0.50/day" savings strings, hardcoded task
recommendations naming a model the operator may never have used, and
"install Ollama" advice to teams whose traffic runs through a managed cloud
provider. Everything here is derived from rows the operator's own agents
recorded, and says so:

* ``provider_route`` names the route a model id travelled (Bedrock, Azure,
  Vertex, a first-party API, a local runtime) or ``unrecognised``. An
  unrecognised route is never counted as local.
* ``observed_usage`` aggregates recorded model events per model.
* ``local_advice`` shows local-model suggestions only when local traffic was
  actually observed, and otherwise says why they are hidden.
* ``experiments`` proposes a trial grounded in observed usage, never a
  savings figure. A cheaper model is only worth it if the tasks still pass
  the operator's acceptance checks, and a switch starts a fresh prompt cache.
* ``cost_provenance`` labels ``todayCost`` / ``projectedMonthlyCost`` /
  ``expensiveOps`` with the shared vocabulary in ``clawmetry/provenance.py``
  so the renderer never shows an unlabelled figure or a hole as $0.00.

Pure functions, no I/O: every input is passed in, so the rules are testable
without a store, a daemon or a dashboard.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Optional

from clawmetry import provenance as _prov

# ── Provider routes ─────────────────────────────────────────────────────────

LOCAL = "local"
UNRECOGNISED = "unrecognised"

ROUTE_LABEL: Dict[str, str] = {
    "anthropic": "Anthropic",
    "openai": "OpenAI",
    "google": "Google",
    "bedrock": "AWS Bedrock",
    "azure": "Azure",
    "vertex": "Google Vertex AI",
    "openrouter": "OpenRouter",
    "xai": "xAI",
    "meta": "Meta",
    "mistral": "Mistral",
    LOCAL: "a local model",
    UNRECOGNISED: "an unrecognised provider",
}

# Bedrock model ids: "<vendor>.<model>" with an optional cross-region
# inference prefix ("us.anthropic.claude-...-v1:0"), or an ARN.
_BEDROCK_RE = re.compile(
    r"^(?:(?:us|eu|apac|global|us-gov)\.)?"
    r"(?:anthropic|amazon|meta|mistral|cohere|ai21|deepseek|qwen|openai|writer)"
    r"\.[a-z0-9]"
)
# Explicit local-runtime prefixes ("ollama/qwen3", "lmstudio/...").
_LOCAL_PREFIXES = ("ollama/", "ollama_chat/", "lmstudio/", "llamacpp/", "llama.cpp/", "vllm/", "local/")
# Ollama-style tags: "qwen3:4b", "deepseek-coder-v2:16b", "llama3.2:latest".
_OLLAMA_TAG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*:(?:\d+(?:\.\d+)?[bm]|latest)$")


def provider_route(model: Any) -> str:
    """The route a model id travelled, or ``unrecognised``. Never raises."""
    m = str(model or "").strip().lower()
    if not m or m == "unknown":
        return UNRECOGNISED
    if m.startswith(("bedrock/", "arn:aws:bedrock")) or _BEDROCK_RE.match(m):
        return "bedrock"
    if m.startswith(("azure/", "azure_ai/", "azure-openai/")):
        return "azure"
    if m.startswith(("vertex_ai/", "vertex/")) or ("claude" in m and "@" in m):
        return "vertex"
    if _OLLAMA_TAG_RE.match(m) or m.startswith(_LOCAL_PREFIXES):
        return LOCAL
    try:
        from clawmetry.providers_pricing import provider_for_model

        prov = provider_for_model(m)
    except Exception:
        prov = ""
    if prov == LOCAL:
        # The pricing helper also calls a model local when its NAME merely
        # contains an open-weights family ("llama", "gemma"), which is true
        # of plenty of hosted deployments. Showing local-model advice on that
        # guess is exactly what REQ-OBS-CEA-023 forbids, so only the
        # unambiguous Ollama "name:tag" shape counts here.
        return LOCAL if (":" in m and "/" not in m) else UNRECOGNISED
    return prov if prov in ROUTE_LABEL else UNRECOGNISED


# ── Observed usage ──────────────────────────────────────────────────────────

def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if f == f else None  # NaN is not a number a reader can use


def observed_usage(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Per-model totals over recorded model events, most expensive first.

    A row is a model event when it names a model and carries a cost or a
    token count. Rows sharing (session, second, model) are one turn: runtimes
    write an ``assistant`` row and a slim ``model.completed`` sibling for the
    same call, and counting both would double every figure (the same dedupe
    the daily rollup applies in SQL).
    """
    seen: Dict[tuple, Dict[str, Any]] = {}
    for r in rows or ():
        if not isinstance(r, Mapping):
            continue
        model = str(r.get("model") or "").strip()
        if not model or model.lower() == "unknown":
            continue
        cost = _num(r.get("cost_usd", r.get("cost")))
        tokens = _num(r.get("token_count", r.get("tokens")))
        if not (cost and cost > 0) and not (tokens and tokens > 0):
            continue
        key = (r.get("session_id"), str(r.get("ts") or "")[:19], model)
        prev = seen.get(key)
        if prev is None or (cost or 0) > (prev["cost"] or 0):
            seen[key] = {"model": model, "cost": cost, "tokens": tokens}
    by_model: Dict[str, Dict[str, Any]] = {}
    for turn in seen.values():
        agg = by_model.setdefault(turn["model"], {
            "model": turn["model"],
            "route": provider_route(turn["model"]),
            "events": 0,
            "costUsd": 0.0,
            "costKnownEvents": 0,
            "tokens": 0,
        })
        agg["events"] += 1
        if turn["cost"] is not None and turn["cost"] > 0:
            agg["costUsd"] += turn["cost"]
            agg["costKnownEvents"] += 1
        if turn["tokens"]:
            agg["tokens"] += int(turn["tokens"])
    out = []
    for agg in by_model.values():
        agg["routeLabel"] = ROUTE_LABEL[agg["route"]]
        # No event carried a cost: that is unknown, not free.
        agg["costUsd"] = round(agg["costUsd"], 6) if agg["costKnownEvents"] else None
        out.append(agg)
    out.sort(key=lambda a: (-(a["costUsd"] or 0.0), -a["events"], a["model"]))
    return out


def local_advice(usage: List[Mapping[str, Any]]) -> Dict[str, Any]:
    """Whether to show local-model suggestions, and why.

    Shown only when local traffic was observed. Managed-provider traffic and
    unrecognised traffic both hide it: moving a Bedrock or Azure deployment to
    a laptop is not a like-for-like option, and a guess is not an observation.
    """
    events_by_route: Dict[str, int] = {}
    for u in usage or ():
        route = u.get("route") or UNRECOGNISED
        events_by_route[route] = events_by_route.get(route, 0) + int(u.get("events") or 0)
    routes = [
        {"route": r, "label": ROUTE_LABEL.get(r, ROUTE_LABEL[UNRECOGNISED]), "events": n}
        for r, n in sorted(events_by_route.items(), key=lambda kv: -kv[1])
    ]
    if events_by_route.get(LOCAL):
        return {
            "show": True,
            "reason": "Your recorded traffic already includes local models, so local options are shown.",
            "routes": routes,
        }
    if not events_by_route:
        return {
            "show": False,
            "reason": "No model traffic has been recorded yet, so local-model suggestions are not shown.",
            "routes": routes,
        }
    managed = [r["label"] for r in routes if r["route"] not in (LOCAL, UNRECOGNISED)]
    if managed:
        return {
            "show": False,
            "reason": (
                "Local-model suggestions are hidden because your recorded traffic runs through "
                + _join(managed)
                + ". Running those tasks on this computer is not a like-for-like option for that deployment."
            ),
            "routes": routes,
        }
    return {
        "show": False,
        "reason": (
            "Local-model suggestions are hidden because the provider behind your recorded "
            "traffic could not be recognised."
        ),
        "routes": routes,
    }


def _join(labels: List[str]) -> str:
    if len(labels) <= 1:
        return "".join(labels)
    return ", ".join(labels[:-1]) + " and " + labels[-1]


MIN_EVENTS_FOR_EXPERIMENT = 3
MAX_EXPERIMENTS = 3


def experiments(usage: List[Mapping[str, Any]], window: str) -> List[Dict[str, Any]]:
    """Trials worth running, each citing the usage it rests on. No savings figure."""
    out: List[Dict[str, Any]] = []
    for u in usage or ():
        if len(out) >= MAX_EXPERIMENTS:
            break
        route = u.get("route") or UNRECOGNISED
        if route == LOCAL or int(u.get("events") or 0) < MIN_EVENTS_FOR_EXPERIMENT:
            continue
        label = ROUTE_LABEL.get(route, ROUTE_LABEL[UNRECOGNISED])
        where = (
            "a cheaper model available through " + label
            if route != UNRECOGNISED
            else "a cheaper model your deployment already supports"
        )
        out.append({
            "task": "%s via %s" % (u.get("model"), label),
            "model": u.get("model"),
            "route": route,
            "routeLabel": label,
            "evidence": {
                "events": int(u.get("events") or 0),
                "costUsd": u.get("costUsd"),
                "window": window,
            },
            "experiment": (
                "Try sending a sample of these tasks to " + where + ", and keep the switch "
                "only if the results still pass your own acceptance checks. Compare cost per "
                "accepted result rather than cost per call, and allow for a fresh prompt cache: "
                "a different model does not share the current one."
            ),
        })
    return out


def recommendations_note(usage: List[Mapping[str, Any]], recs: List[Any]) -> Optional[str]:
    if recs:
        return None
    if not usage:
        return "No model traffic has been recorded yet, so there is nothing to base an experiment on."
    return (
        "Not enough recorded usage to suggest an experiment yet. One appears once a model "
        "has at least %d recorded events." % MIN_EVENTS_FOR_EXPERIMENT
    )


# ── Cost basis ──────────────────────────────────────────────────────────────

LOCAL_STORE_WINDOW = "the most recent 200 events in the local store"
INTERCEPTOR_WINDOW = "model calls this dashboard intercepted since it started"

_PRICED = (
    "the cost the runtime recorded, or the recorded tokens priced at the "
    "provider's published rates when it recorded none"
)


def cost_provenance(source: str, where: str = "this computer") -> Dict[str, Dict[str, Any]]:
    """Provenance for the optimizer's figures, by where they were read.

    ``source`` is ``local_store`` (daemon rollup), ``interceptor`` (this
    dashboard's in-process ring), ``none`` (nothing recorded by either) or
    ``error`` (the read failed). The last two label the figures unknown, and
    ``provenance.stamp`` then nulls them, so neither can render as $0.00.
    """
    if source == "local_store":
        src = "local store (DuckDB) on " + where
        return {
            "todayCost": _prov.derived(
                "sum over today's recorded events of " + _PRICED, src,
                window="today (UTC date)"),
            "projectedMonthlyCost": _prov.estimated(
                "month-to-date spend divided by the number of days with recorded spend "
                "this month, times 30", src, window="this calendar month (UTC)"),
            "expensiveOps": _prov.derived(_PRICED, src, window=LOCAL_STORE_WINDOW),
            "modelUsage": _prov.derived(
                "sum per model of " + _PRICED, src, window=LOCAL_STORE_WINDOW),
        }
    if source == "interceptor":
        src = "model calls intercepted by this dashboard process"
        return {
            "todayCost": _prov.derived(
                "sum of intercepted calls today, tokens priced at the provider's published rates",
                src, window="today (this computer's calendar day)"),
            "projectedMonthlyCost": _prov.estimated(
                "month-to-date intercepted spend divided by the days elapsed this month, "
                "times the days in the month", src, window="this calendar month"),
            "expensiveOps": _prov.derived(
                "tokens priced at the provider's published rates", src,
                window=INTERCEPTOR_WINDOW),
            "modelUsage": _prov.derived(
                "sum per model of intercepted calls priced at published rates", src,
                window=INTERCEPTOR_WINDOW),
        }
    if source == "error":
        reason = "the cost analysis could not read spend just now"
    elif source == "store_empty":
        # The hosted snapshot has no in-process interceptor ring to fall back
        # on, so the reason names only the store it actually read.
        reason = "no spend has been recorded on %s yet: its local store holds no cost rows" % where
    else:
        reason = ("no spend has been recorded yet: the local store holds no cost rows and this "
                  "dashboard has intercepted no model calls since it started")
    return {
        "todayCost": _prov.unknown(reason),
        "projectedMonthlyCost": _prov.unknown(reason),
    }


# ── Shared by the local route and the hosted snapshot slice ─────────────────

def advice_fields(usage_rows: Iterable[Mapping[str, Any]], window: str) -> Dict[str, Any]:
    """The data-derived advice block, identical for the local route and the
    hosted snapshot (AC-OBS-CEA-023.9): one function, so the two cannot drift."""
    usage = observed_usage(usage_rows)
    recs = experiments(usage, window)
    return {
        "localAdvice": local_advice(usage),
        "modelUsage": usage[:10],
        "taskRecommendations": recs,
        "recommendationsNote": recommendations_note(usage, recs),
    }


def tokens_recorded_or_none(ops: Any) -> List[Dict[str, Any]]:
    """A token count nobody recorded is ``None`` ("not recorded"), not "unknown tokens"."""
    return [
        dict(op, tokens=(None if op.get("tokens") in (None, "", "0", "unknown") else op.get("tokens")))
        for op in (ops or []) if isinstance(op, Mapping)
    ]
