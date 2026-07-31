"""`clawmetry selfevolve` — OSS 402 stub for the Pro self-improvement engine.

    clawmetry selfevolve analyze|status|fix [--json]

The command EXISTS in OSS so an agent that just diagnosed its own failure
(via `clawmetry progress` / `clawmetry waste`) discovers the next step. On
an install without the entitlement it exits 4 with the same
``upgrade_required`` body the HTTP API's 402 carries (plus ``upgrade_url``),
and records a paywall event — that moment is the product's peak-intent
second, not an error to hide.

The real implementation ships in the closed-source ``clawmetry-pro``
package (repo rule: Pro code never lands here) and fulfils via the
``clawmetry.extensions`` entry-point group, attr ``selfevolve_cli``.
"""
from __future__ import annotations

import json

from clawmetry.cli_cmds import _common as c

_FEATURE = "self_evolve"
_UPGRADE_URL = "https://clawmetry.com/upgrade?feature=self_evolve&src=cli"


def register(sub) -> None:
    p = sub.add_parser(
        "selfevolve",
        help="[pro] Analyze telemetry and propose/apply agent improvements",
    )
    p.add_argument("action", choices=["analyze", "status", "fix"],
                   help="analyze: find improvements · status: engine state · fix: apply one")
    c.add_output_flags(p)
    p.set_defaults(_handler=run)


def _pro_impl():
    """Return the Pro package's CLI hook when installed, else None."""
    try:
        from clawmetry.extensions import _select_entry_points
    except Exception:
        return None
    try:
        for ep in _select_entry_points("clawmetry.extensions"):
            if ep.name == "selfevolve_cli":
                return ep.load()
    except Exception:
        return None
    return None


def _allowed() -> bool:
    try:
        from clawmetry import entitlements
        return bool(entitlements.get_entitlement().allows_feature(_FEATURE))
    except Exception:
        return False


def _record_paywall_event(action: str) -> None:
    """Best-effort beacon to the local dashboard's rolling paywall store —
    the same telemetry the UI's upgrade CTAs feed. Never blocks, never
    raises; 1 s budget."""
    try:
        import os
        import urllib.request
        payload = json.dumps({
            "event": "paywall_view",
            "feature": _FEATURE,
            "source": "cli",
            "harness": f"selfevolve_{action}",
        }).encode("utf-8")
        base = (os.environ.get("CLAWMETRY_URL") or "http://127.0.0.1:8900").rstrip("/")
        req = urllib.request.Request(
            f"{base}/api/paywall/event",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=1.0).close()
    except Exception:
        pass


def run(args) -> int:
    impl = _pro_impl()
    if impl is not None and _allowed():
        try:
            return int(impl(args) or 0)
        except Exception as exc:
            raise c.CliError("internal", f"selfevolve ({args.action}) failed: {exc}",
                             c.EXIT_ERROR)

    _record_paywall_event(args.action)
    try:
        from clawmetry._paywall import upgrade_required_body
        body = upgrade_required_body(_FEATURE)
    except Exception:
        body = {"error": "upgrade_required", "feature": _FEATURE,
                "tier": "oss", "required_tier": None,
                "hint": "Self-Evolve ships in clawmetry-pro."}
    body["upgrade_url"] = _UPGRADE_URL
    raise c.CliError(
        "upgrade_required",
        f"selfevolve {args.action} requires the Self-Evolve feature "
        f"(tier: {body.get('tier')}, unlocks at: {body.get('required_tier') or 'pro'}). "
        f"Upgrade: {_UPGRADE_URL}",
        c.EXIT_ENTITLEMENT,
        extra=body,
    )
