"""_build_agent_inventory subscription-coverage enrichment (device parity).

The desk device already shows "covered / EXTRA TODAY $0.00 / Claude Max 20x
covers it - ~$X at API rates" from the daemon's billing-mode detection; the
web Agents roster must read the SAME detection so both surfaces agree:

  - each roster row gains billingMode/billingLabel when the detector knows
    the runtime's mode;
  - the payload gains accountPlan ({mode,label,usd_month}) and
    extraCost24hUsd = the 24h spend of METERED agents only (a subscription is
    a flat fee already paid, so its usage adds $0 marginal spend - the same
    semantics as the cloud device-summary endpoint);
  - a billing-detection failure never breaks the roster (best-effort).
"""

from __future__ import annotations

import importlib


def _sync():
    import clawmetry.sync as sync
    return sync


def _rs():
    # Minimal runtime_summary: two runtimes with substance.
    return {
        "claude_code": {"sessions": 3, "turns": 9, "tokens": 1000,
                        "cost_usd": 812.61, "cost_24h_usd": 85.38,
                        "tokens_24h": 360, "primary_model": "claude-fable-5"},
        "codex": {"sessions": 1, "turns": 2, "tokens": 50,
                  "cost_usd": 4.0, "cost_24h_usd": 1.25,
                  "tokens_24h": 40, "primary_model": "gpt-5"},
    }


def _build(sync):
    return sync._build_agent_inventory(
        _rs(), {}, {}, {}, {}, detected_runtimes=[], agent_meta={},
        node_id="test-node",
    )


def test_rows_carry_billing_mode_and_payload_carries_plan(monkeypatch):
    sync = _sync()
    monkeypatch.setattr(sync, "load_config", lambda: {"node_id": "test-node"})
    monkeypatch.setattr(sync, "_build_billing_payload", lambda cfg: {
        "node_id": "test-node",
        "account_plan": {"mode": "subscription", "label": "Claude Max 20x",
                         "usd_month": 200.0},
        "runtimes": {
            "claude_code": {"mode": "subscription", "label": "Claude Max 20x",
                            "usd_month": 200.0},
            "codex": {"mode": "metered", "label": "OpenAI API",
                      "usd_month": None},
        },
    })
    node_wide, by_rt = _build(sync)
    rows = {a["agentKey"]: a for a in node_wide["agents"]}
    assert rows["claude_code"]["billingMode"] == "subscription"
    assert rows["claude_code"]["billingLabel"] == "Claude Max 20x"
    assert rows["codex"]["billingMode"] == "metered"
    assert node_wide["accountPlan"]["label"] == "Claude Max 20x"
    # extra = METERED agents' 24h cost only: codex 1.25, NOT claude_code 85.38.
    assert node_wide["extraCost24hUsd"] == 1.25
    # by_runtime slices reference the same enriched row objects.
    assert by_rt["claude_code"]["agents"][0]["billingMode"] == "subscription"


def test_unknown_modes_leave_rows_unmarked(monkeypatch):
    sync = _sync()
    monkeypatch.setattr(sync, "load_config", lambda: {})
    monkeypatch.setattr(sync, "_build_billing_payload", lambda cfg: {
        "account_plan": None,
        "runtimes": {},
    })
    node_wide, _ = _build(sync)
    for a in node_wide["agents"]:
        assert "billingMode" not in a
    assert node_wide["accountPlan"] is None
    assert node_wide["extraCost24hUsd"] == 0.0


def test_billing_failure_never_breaks_roster(monkeypatch):
    sync = _sync()

    def _boom(cfg):
        raise RuntimeError("detector exploded")

    monkeypatch.setattr(sync, "load_config", lambda: {})
    monkeypatch.setattr(sync, "_build_billing_payload", _boom)
    node_wide, _ = _build(sync)
    assert node_wide["total"] == 2
    assert node_wide["accountPlan"] is None
    assert node_wide["extraCost24hUsd"] == 0.0
