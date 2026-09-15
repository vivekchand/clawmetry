"""Cost Optimizer slice for the hosted dashboard (AC-OBS-CEA-023.9).

Fulfils REQ-OBS-CEA-023 (Cost and Efficiency Analytics > "Cost Optimizer:
honest, fast and provider-aware"), vivekchand/clawmetry#5934, hosted half.

The local ``GET /api/cost-optimizer`` (``routes/infra.py``) builds its
experiments, provider-aware local-model advice and basis-labelled figures
from rows in this computer's DuckDB store. The hosted dashboard has no store:
the cloud holds an opaque, end-to-end encrypted snapshot. Its optimizer
interceptor used to send generic recommendations that cite no observed usage,
which the renderer now hides, so the hosted panel showed no experiments.

The daemon is the only side that can read the rows, so it runs the SAME rules
(``_try_local_store_cost_optimizer`` + ``cost_optimizer_advice.advice_fields``)
on its own store handle and ships the finished data slice in the snapshot as
``costOptimizer``. clawmetry-cloud's ``cm-cloud-overview`` interceptor decrypts
it in the browser and returns it for ``/api/cost-optimizer``. The cloud never
holds the key or the plaintext.

Not shipped: host state that only exists on the computer (llmfit model fit,
whether Ollama is installed). The hosted interceptor adds hardware from
``machineInfo`` and says model fit is computed on the computer itself.
"""

from __future__ import annotations

from typing import Any, Dict

# How the hosted panel names the computer the figures came from. "this
# computer" would read as the viewer's own machine on app.clawmetry.com.
HOSTED_WHERE = "the connected computer"


def build_slice(store: Any) -> Dict[str, Any]:
    """The ``costOptimizer`` snapshot slice, or ``{}`` with no store. Never raises."""
    if store is None:
        return {}
    from clawmetry import cost_optimizer_advice as _adv
    from clawmetry import provenance as _prov

    base: Dict[str, Any] = {"scope": "all runtimes on " + HOSTED_WHERE, "_source": "snapshot"}

    def _call(method: str, **kwargs: Any) -> Any:
        return getattr(store, method)(**kwargs)

    try:
        from routes.infra import _try_local_store_cost_optimizer

        ls_slice = _try_local_store_cost_optimizer(call=_call)
    except Exception:
        payload = dict(base, **_adv.advice_fields([], _adv.LOCAL_STORE_WINDOW))
        payload.update({
            "localAdvice": {"show": False, "reason": "", "routes": []},
            "recommendationsNote": (
                "The cost analysis could not finish on the connected computer, "
                "so no experiments are shown."
            ),
            "todayCost": None,
            "projectedMonthlyCost": None,
            "expensiveOps": [],
            "error": "analysis_failed",
        })
        return _prov.stamp(payload, _adv.cost_provenance("error", where=HOSTED_WHERE))

    if ls_slice is None:
        source, rows, today, projected, ops = "store_empty", [], None, None, []
    else:
        source = "local_store"
        rows = ls_slice.get("modelRows") or []
        today = ls_slice.get("todayCost")
        projected = ls_slice.get("projectedMonthlyCost")
        ops = ls_slice.get("expensiveOps") or []

    payload = dict(base, **_adv.advice_fields(rows, _adv.LOCAL_STORE_WINDOW))
    payload.update({
        "todayCost": today,
        "projectedMonthlyCost": projected,
        "expensiveOps": _adv.tokens_recorded_or_none(ops),
    })
    return _prov.stamp(payload, _adv.cost_provenance(source, where=HOSTED_WHERE))
