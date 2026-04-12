import json
import os
import time

import dashboard


def _write_session(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _msg(ts, tokens=0, cost=0.0):
    usage = {"total_tokens": tokens}
    if cost > 0:
        usage["cost"] = {"total": cost}
    return {"timestamp": ts, "message": {"usage": usage}}


def test_session_cost_threshold_evaluator_and_cooldown(tmp_path):
    now = time.time()
    sid = "session-cost"
    fpath = tmp_path / f"{sid}.jsonl"
    _write_session(
        fpath,
        [
            _msg(now - 50, tokens=2000, cost=2.5),
            _msg(now - 40, tokens=2000, cost=2.6),
            _msg(now - 30, tokens=1500, cost=1.0),
        ],
    )
    os.utime(fpath, (now, now))

    metrics = dashboard._collect_active_session_alert_metrics(
        now=now, sessions_dir=str(tmp_path), baseline_min=60
    )
    rule = {
        "id": "rule-session-cost",
        "type": "session_cost_threshold",
        "threshold": 5.0,
        "params": {"scope": "session", "target": "active"},
    }
    msg = dashboard._evaluate_session_cost_threshold(rule, metrics)
    assert "Session cost threshold exceeded" in msg

    dashboard._budget_alert_cooldowns["rule-session-cost"] = now
    assert dashboard._is_rule_cooldown_elapsed("rule-session-cost", 300, now=now) is False
    assert dashboard._is_rule_cooldown_elapsed("rule-session-cost", 300, now=now + 301) is True


def test_token_velocity_spike_session_scope_1min(tmp_path):
    now = time.time()
    sid = "velocity-session"
    fpath = tmp_path / f"{sid}.jsonl"
    rows = []
    # Prior baseline minute buckets ~200 tokens/min.
    for i in range(2, 62):
        rows.append(_msg(now - (i * 60) + 5, tokens=200))
    # Current minute spikes to 1200 tokens.
    rows.append(_msg(now - 20, tokens=1200))
    _write_session(fpath, rows)
    os.utime(fpath, (now, now))

    metrics = dashboard._collect_active_session_alert_metrics(
        now=now, sessions_dir=str(tmp_path), baseline_min=60
    )
    rule = {
        "type": "token_velocity_spike",
        "threshold": 3.0,
        "params": {"scope": "session", "window_min": 1, "baseline_min": 60, "min_tokens_1min": 500},
    }
    msg = dashboard._evaluate_token_velocity_spike(rule, metrics)
    assert "Token velocity spike (session" in msg
    # Noise gate should suppress same signal with a higher floor.
    rule["params"]["min_tokens_1min"] = 1500
    assert dashboard._evaluate_token_velocity_spike(rule, metrics) == ""


def test_token_velocity_spike_fleet_scope_1min(tmp_path):
    now = time.time()
    f1 = tmp_path / "fleet-a.jsonl"
    f2 = tmp_path / "fleet-b.jsonl"

    rows_a = []
    rows_b = []
    for i in range(2, 62):
        rows_a.append(_msg(now - (i * 60) + 3, tokens=300))
        rows_b.append(_msg(now - (i * 60) + 7, tokens=300))
    rows_a.append(_msg(now - 10, tokens=2500))
    rows_b.append(_msg(now - 15, tokens=1300))
    _write_session(f1, rows_a)
    _write_session(f2, rows_b)
    os.utime(f1, (now, now))
    os.utime(f2, (now, now))

    metrics = dashboard._collect_active_session_alert_metrics(
        now=now, sessions_dir=str(tmp_path), baseline_min=60
    )
    rule = {
        "type": "token_velocity_spike",
        "threshold": 3.0,
        "params": {"scope": "fleet", "window_min": 1, "baseline_min": 60, "min_tokens_1min": 500},
    }
    msg = dashboard._evaluate_token_velocity_spike(rule, metrics)
    assert "Token velocity spike (fleet)" in msg

