"""
clawmetry/skills.py — Per-skill cost attribution with ClawHub integration hooks.

Parses OpenClaw session JSONL transcripts to detect skill usage (via `read` tool
calls to paths ending in SKILL.md), attributes token costs to each skill, and
builds a leaderboard.

ClawHub schema: each skill execution record includes a `clawmetry_skill` metadata
block designed for future ClawHub marketplace API integration.
"""
from __future__ import annotations

import glob
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── ClawHub schema version ──────────────────────────────────────────────────
CLAWHUB_SCHEMA_VERSION = "1.0"

# ── Pricing defaults (Claude Sonnet — used when no cost recorded in transcript)
_DEFAULT_INPUT_COST_PER_1M = 3.0    # USD per 1M input tokens
_DEFAULT_OUTPUT_COST_PER_1M = 15.0  # USD per 1M output tokens
_DEFAULT_BLENDED_COST_PER_1M = 7.5  # blended estimate


def _estimate_cost(tokens: int) -> float:
    """Estimate cost from total tokens using blended rate."""
    return round(tokens * _DEFAULT_BLENDED_COST_PER_1M / 1_000_000, 6)


# ── Skill detection helpers ──────────────────────────────────────────────────

_SKILL_MD_RE = re.compile(r'SKILL\.md$', re.IGNORECASE)
_SKILL_NAME_RE = re.compile(
    r'skills[/\\]([^/\\]+)[/\\]SKILL\.md',
    re.IGNORECASE,
)


def _extract_skill_name_from_path(path: str) -> str | None:
    """Extract the skill name from a SKILL.md file path, e.g. 'coding-agent'."""
    m = _SKILL_NAME_RE.search(path.replace('\\', '/'))
    if m:
        return m.group(1).lower().strip()
    # Fallback: parent directory name
    parts = path.replace('\\', '/').split('/')
    for i, p in enumerate(parts):
        if p.lower() == 'skill.md' and i > 0:
            return parts[i - 1].lower().strip()
    return None


def _is_skill_read(obj: dict) -> str | None:
    """
    If this transcript event is a `read` tool call to a SKILL.md path,
    return the skill name. Otherwise return None.
    """
    message = obj.get('message', {}) if isinstance(obj.get('message'), dict) else {}
    content = message.get('content') or []
    if not isinstance(content, list):
        return None
    for part in content:
        if not isinstance(part, dict):
            continue
        if part.get('type') != 'toolCall':
            continue
        tool_name = str(part.get('name', '')).lower()
        if tool_name not in ('read',):
            continue
        args = part.get('arguments') or part.get('input') or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                continue
        if not isinstance(args, dict):
            continue
        # Check file_path or path argument
        fpath = args.get('file_path') or args.get('path') or ''
        if _SKILL_MD_RE.search(str(fpath)):
            name = _extract_skill_name_from_path(str(fpath))
            return name
    return None


def _extract_usage_for_event(obj: dict) -> tuple[int, float]:
    """Return (total_tokens, cost_usd) from a transcript event."""
    message = obj.get('message', {}) if isinstance(obj.get('message'), dict) else {}
    usage = message.get('usage')
    if not isinstance(usage, dict):
        usage = obj.get('usage')
    if not isinstance(usage, dict):
        return 0, 0.0

    in_toks = int(usage.get('input', usage.get('input_tokens', 0)) or 0)
    out_toks = int(usage.get('output', usage.get('output_tokens', 0)) or 0)
    cache_r = int(usage.get('cacheRead', usage.get('cache_read_tokens', 0)) or 0)
    cache_w = int(usage.get('cacheWrite', usage.get('cache_write_tokens', 0)) or 0)
    total = int(usage.get('totalTokens', usage.get('total_tokens', 0)) or 0)
    if not total:
        total = in_toks + out_toks + cache_r + cache_w

    cost = 0.0
    cost_data = usage.get('cost', {})
    if isinstance(cost_data, dict):
        try:
            cost = float(cost_data.get('total', cost_data.get('usd', 0)) or 0)
        except Exception:
            cost = 0.0
    elif isinstance(cost_data, (int, float)):
        cost = float(cost_data)

    if cost == 0.0 and total > 0:
        cost = _estimate_cost(total)

    return total, cost


# ── ClawHub metadata schema ──────────────────────────────────────────────────

def _build_clawhub_metadata(
    skill_name: str,
    session_id: str,
    execution_id: str,
    started_at: str,
    ended_at: str,
    tokens: int,
    cost_usd: float,
    turns: int,
    success: bool,
    node_id: str = "",
    model: str = "",
) -> dict[str, Any]:
    """
    Build the clawmetry_skill metadata block for a skill execution.

    This schema is designed for future ClawHub API integration — a marketplace
    where skills can be discovered, rated, and their economics tracked across
    the OpenClaw ecosystem.

    Fields:
      schema_version  — incremented when the schema changes
      skill_name      — canonical skill identifier (e.g. 'coding-agent')
      execution_id    — UUID for this specific invocation
      session_id      — source OpenClaw session
      node_id         — machine/node that ran the skill
      model           — LLM model used during this execution
      started_at      — ISO-8601 UTC timestamp of skill load
      ended_at        — ISO-8601 UTC timestamp of skill completion
      tokens          — total tokens attributed to this execution
      cost_usd        — estimated USD cost
      turns           — number of assistant turns after skill load
      success         — whether the session completed without apparent error
      source          — always "clawmetry" for provenance tracking
    """
    return {
        "schema_version": CLAWHUB_SCHEMA_VERSION,
        "skill_name": skill_name,
        "execution_id": execution_id,
        "session_id": session_id,
        "node_id": node_id,
        "model": model,
        "started_at": started_at,
        "ended_at": ended_at,
        "tokens": tokens,
        "cost_usd": round(cost_usd, 6),
        "turns": turns,
        "success": success,
        "source": "clawmetry",
    }


# ── Core: parse a session file for skill executions ─────────────────────────

def _parse_session_for_skills(fpath: str) -> list[dict]:
    """
    Parse a single JSONL session file and return a list of skill execution
    records. Each record contains aggregated token/cost data for one skill
    invocation plus the `clawmetry_skill` ClawHub metadata block.

    Strategy:
      1. Scan events linearly.
      2. When we see a `read` tool call to SKILL.md, start attributing.
      3. Continue attributing turns until we see another skill load or EOF.
      4. Each attribution window becomes one execution record.
    """
    sid = os.path.basename(fpath).replace('.jsonl', '')
    results = []

    # State for the current skill window
    active_skill: str | None = None
    window_tokens = 0
    window_cost = 0.0
    window_turns = 0
    window_start_ts: str = ""
    window_last_ts: str = ""
    window_model: str = ""
    last_ts: str = ""
    model: str = ""
    _exec_counter = 0

    def _flush_window(end_ts: str, success: bool = True):
        nonlocal active_skill, window_tokens, window_cost, window_turns
        nonlocal window_start_ts, window_last_ts, window_model
        if active_skill is None or window_tokens == 0:
            return
        _exec_counter_val = len(results)
        exec_id = f"{sid[:8]}-{active_skill[:12]}-{_exec_counter_val:03d}"
        clawhub = _build_clawhub_metadata(
            skill_name=active_skill,
            session_id=sid,
            execution_id=exec_id,
            started_at=window_start_ts,
            ended_at=end_ts or window_last_ts,
            tokens=window_tokens,
            cost_usd=window_cost,
            turns=window_turns,
            success=success,
            model=window_model or model,
        )
        results.append({
            'skill_name': active_skill,
            'session_id': sid,
            'execution_id': exec_id,
            'tokens': window_tokens,
            'cost_usd': round(window_cost, 6),
            'turns': window_turns,
            'started_at': window_start_ts,
            'ended_at': end_ts or window_last_ts,
            'success': success,
            'model': window_model or model,
            'clawmetry_skill': clawhub,
        })
        # Reset window
        active_skill = None
        window_tokens = 0
        window_cost = 0.0
        window_turns = 0
        window_start_ts = ""
        window_last_ts = ""

    try:
        with open(fpath, 'r', errors='replace') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue

                ts = (obj.get('timestamp') or obj.get('time') or obj.get('created_at') or '')
                if ts:
                    last_ts = ts

                msg = obj.get('message', {}) if isinstance(obj.get('message'), dict) else {}
                if msg.get('model'):
                    model = msg['model']

                # Check if this is a skill load event
                skill_loaded = _is_skill_read(obj)
                if skill_loaded:
                    # Flush previous skill window (if any)
                    _flush_window(ts)
                    # Start new window
                    active_skill = skill_loaded
                    window_start_ts = ts
                    window_last_ts = ts
                    window_model = model
                    continue  # the read turn itself doesn't count as attribution

                # Accumulate tokens for active skill window
                if active_skill is not None:
                    tokens, cost = _extract_usage_for_event(obj)
                    if tokens > 0:
                        window_tokens += tokens
                        window_cost += cost
                        window_turns += 1
                        window_last_ts = ts

        # Flush last window at end of session
        _flush_window(last_ts, success=True)

    except Exception:
        pass

    return results


# ── Leaderboard builder ──────────────────────────────────────────────────────

def build_skill_leaderboard(sessions_dir: str) -> dict:
    """
    Scan all JSONL session files in sessions_dir, detect skill usage,
    attribute token costs, and return a leaderboard.

    Returns:
        {
            "leaderboard": [...sorted by total_cost desc...],
            "executions": [...all execution records, newest first...],
            "summary": {total_cost, total_tokens, total_executions, ...},
            "generated_at": "<ISO timestamp>",
        }
    """
    if not os.path.isdir(sessions_dir):
        return _empty_leaderboard()

    all_executions: list[dict] = []
    jsonl_files = glob.glob(os.path.join(sessions_dir, '*.jsonl'))

    for fpath in jsonl_files:
        execs = _parse_session_for_skills(fpath)
        all_executions.extend(execs)

    # Sort executions by started_at descending (newest first)
    all_executions.sort(key=lambda e: e.get('started_at', ''), reverse=True)

    # Aggregate per skill
    skill_agg: dict[str, dict] = defaultdict(lambda: {
        'total_cost': 0.0,
        'total_tokens': 0,
        'executions': 0,
        'successful': 0,
        'total_turns': 0,
        'models': set(),
        'sessions': set(),
    })

    for ex in all_executions:
        name = ex['skill_name']
        agg = skill_agg[name]
        agg['total_cost'] += ex['cost_usd']
        agg['total_tokens'] += ex['tokens']
        agg['executions'] += 1
        agg['total_turns'] += ex['turns']
        if ex.get('success'):
            agg['successful'] += 1
        if ex.get('model'):
            agg['models'].add(ex['model'])
        agg['sessions'].add(ex['session_id'])

    leaderboard = []
    for skill_name, agg in skill_agg.items():
        n = agg['executions']
        s = agg['successful']
        leaderboard.append({
            'skill_name': skill_name,
            'total_cost': round(agg['total_cost'], 6),
            'total_tokens': agg['total_tokens'],
            'executions': n,
            'avg_cost': round(agg['total_cost'] / n, 6) if n > 0 else 0.0,
            'avg_tokens': int(agg['total_tokens'] / n) if n > 0 else 0,
            'avg_turns': round(agg['total_turns'] / n, 1) if n > 0 else 0.0,
            'success_rate': round((s / n) * 100, 1) if n > 0 else 0.0,
            'unique_sessions': len(agg['sessions']),
            'models': sorted(agg['models']),
            # ClawHub fields for future marketplace integration
            'clawmetry_skill': {
                'schema_version': CLAWHUB_SCHEMA_VERSION,
                'skill_name': skill_name,
                'aggregate': True,
                'total_cost': round(agg['total_cost'], 6),
                'total_tokens': agg['total_tokens'],
                'executions': n,
                'success_rate': round((s / n) * 100, 1) if n > 0 else 0.0,
                'source': 'clawmetry',
            },
        })

    # Sort by total_cost descending (primary leaderboard metric)
    leaderboard.sort(key=lambda r: r['total_cost'], reverse=True)

    total_cost = sum(r['total_cost'] for r in leaderboard)
    total_tokens = sum(r['total_tokens'] for r in leaderboard)
    total_execs = sum(r['executions'] for r in leaderboard)

    return {
        'leaderboard': leaderboard,
        'executions': all_executions[:200],  # cap to avoid huge payloads
        'summary': {
            'total_cost': round(total_cost, 6),
            'total_tokens': total_tokens,
            'total_executions': total_execs,
            'unique_skills': len(leaderboard),
            'schema_version': CLAWHUB_SCHEMA_VERSION,
        },
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }


def _empty_leaderboard() -> dict:
    return {
        'leaderboard': [],
        'executions': [],
        'summary': {
            'total_cost': 0.0,
            'total_tokens': 0,
            'total_executions': 0,
            'unique_skills': 0,
            'schema_version': CLAWHUB_SCHEMA_VERSION,
        },
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }


# ── Simple TTL cache ─────────────────────────────────────────────────────────
_skill_cache: dict = {'data': None, 'ts': 0.0, 'sessions_dir': ''}
_SKILL_CACHE_TTL = 60  # seconds


def get_skill_leaderboard_cached(sessions_dir: str) -> dict:
    """Return cached leaderboard, refreshing if stale."""
    now = time.time()
    if (
        _skill_cache['data'] is not None
        and _skill_cache['sessions_dir'] == sessions_dir
        and (now - _skill_cache['ts']) < _SKILL_CACHE_TTL
    ):
        return _skill_cache['data']
    data = build_skill_leaderboard(sessions_dir)
    _skill_cache['data'] = data
    _skill_cache['ts'] = now
    _skill_cache['sessions_dir'] = sessions_dir
    return data
