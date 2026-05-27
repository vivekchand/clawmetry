"""
routes/nemoclaw.py — NemoClaw governance + approval endpoints.

Extracted from dashboard.py as Phase 5.13 (FINAL) of the incremental
modularisation. Owns the 7 routes registered on ``bp_nemoclaw``:

  /api/nemoclaw/governance                     — governance summary
  /api/nemoclaw/governance/acknowledge-drift   — POST ack
  /api/nemoclaw/status                         — daemon status
  /api/nemoclaw/policy                         — active policy
  /api/nemoclaw/approve                        — approve pending action
  /api/nemoclaw/reject                         — reject pending action
  /api/nemoclaw/pending-approvals              — list queue

Module-level helpers (``_detect_nemoclaw``, ``_parse_network_policies``)
and module state (``_nemoclaw_policy_hash``, ``_nemoclaw_drift_info``)
stay in ``dashboard.py`` and are reached via late ``import dashboard as _d``.

Pure mechanical move — zero behaviour change.

Phase 4 of epic #1032 adds an opt-in DuckDB fast path
(``CLAWMETRY_LOCAL_STORE_READ=1``) to ``/api/nemoclaw/pending-approvals``:
when local DuckDB has rows in the ``approvals`` table, we serve the
queue from there (tagged ``_source: "local_store"``) instead of shelling
out to ``openshell draft get``. Sits in front of the legacy CLI path —
fresh installs or non-NemoClaw users degrade to the same response as
before.
"""
import os

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from clawmetry.config import is_local_store_read_enabled

bp_nemoclaw = Blueprint('nemoclaw', __name__)


# ── Local DuckDB fast path (epic #1032 Phase 4 — approvals queue) ───────────
#
# Opt-in via CLAWMETRY_LOCAL_STORE_READ=1. Mirrors routes/crons.py: a dedicated
# helper attempts a DuckDB read and returns ``None`` on any error / empty
# table so the legacy ``openshell draft get`` path runs untouched. The fast
# path NEVER replaces the legacy code — it sits in front of it, so a fresh
# install with no local store (or a non-NemoClaw user) sees the same data
# as before.
#
# The local ``approvals`` table is populated by the policy watcher in
# clawmetry/approvals.py via LocalStore.ingest_approval (Phase 4). Schema:
#
#   approvals (
#     id, owner_hash, requestor_session_id, action, args BLOB, status,
#     created_at, resolved_at, resolver, decision, decision_reason
#   )
#
# Response shape mirrors the legacy ``/api/nemoclaw/pending-approvals``
# contract (``{installed, approvals}``) — only adding ``_source:
# "local_store"`` so tests can assert which path served the response.


def _try_local_store_approvals():
    """Return pending-approvals dict shaped like ``/api/nemoclaw/pending-
    approvals`` from the local DuckDB.

    Returns ``None`` to defer to the legacy openshell CLI fallback if:
      - the ``local_store`` module isn't importable
      - the ``approvals`` table is empty (fresh install / no pending rows)
      - any unexpected error happens (we'd rather degrade than 500)
    """
    # Issue #1282 / memory `feedback_daemon_proxy_pattern.md`: writable
    # ``get_store`` raced the sync daemon's exclusive DuckDB writer lock
    # on multi-process installs (launchd/systemd). Try the daemon HTTP
    # proxy first; fall back to a direct read-only open for single-process
    # boots (tests, dev mode).
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_approvals", status="pending", limit=500)
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_approvals(status="pending", limit=500)
        except Exception:
            return None
    if not rows:
        return None
    approvals = []
    for r in rows:
        args = r.get("args") if isinstance(r.get("args"), dict) else {}
        approvals.append({
            # Preserve the column names so the cloud + dashboard can address
            # rows directly by id without translation.
            "id":                   r.get("id"),
            # Legacy fields the dashboard JS still reads — derived from the
            # row when present, kept as None otherwise so the renderer's
            # `||` fallbacks behave unchanged.
            "chunk_id":             r.get("id"),
            "session_id":           r.get("requestor_session_id"),
            "requestor_session_id": r.get("requestor_session_id"),
            "action":               r.get("action"),
            "tool_name":            r.get("action"),
            "args":                 args,
            "status":               r.get("status", "pending"),
            "ts":                   r.get("created_at"),
            "created_at":           r.get("created_at"),
        })
    return {
        "installed": True,
        "approvals": approvals,
        "_source":   "local_store",
    }


# ── NemoClaw Governance API ───────────────────────────────────────────────────


@bp_nemoclaw.route('/api/nemoclaw/governance')
def api_nemoclaw_governance():
    """Return NemoClaw governance status: policy, sandbox state, drift detection."""
    import dashboard as _d
    info = _d._detect_nemoclaw()
    if info is None:
        return jsonify({'installed': False})

    result = {
        'installed': True,
        'sandboxes': [],
        'policy': None,
        'network_policies': [],
        'presets': info.get('presets', []),
        'drift': None,
        'config': {},
    }

    # Config summary (sanitise - remove tokens/keys)
    cfg = info.get('config', {})
    if cfg:
        safe_cfg = {k: v for k, v in cfg.items() if 'token' not in k.lower() and 'key' not in k.lower() and 'secret' not in k.lower()}
        result['config'] = safe_cfg

    # Sandbox state
    state = info.get('state', {})
    if isinstance(state, dict):
        sandboxes_raw = state.get('sandboxes') or state.get('shells') or {}
        if isinstance(sandboxes_raw, dict):
            for name, sb in sandboxes_raw.items():
                if isinstance(sb, dict):
                    result['sandboxes'].append({
                        'name': name,
                        'status': sb.get('status', 'unknown'),
                        'pid': sb.get('pid'),
                        'created': sb.get('created') or sb.get('createdAt'),
                        'preset': sb.get('preset') or sb.get('policy_preset'),
                    })
        elif isinstance(sandboxes_raw, list):
            for sb in sandboxes_raw:
                if isinstance(sb, dict):
                    result['sandboxes'].append({
                        'name': sb.get('name', 'unknown'),
                        'status': sb.get('status', 'unknown'),
                        'pid': sb.get('pid'),
                        'created': sb.get('created') or sb.get('createdAt'),
                        'preset': sb.get('preset') or sb.get('policy_preset'),
                    })

    # Parse sandbox list from CLI output if state didn't give sandboxes
    if not result['sandboxes'] and info.get('sandbox_list_raw'):
        for line in info['sandbox_list_raw'].splitlines():
            line = line.strip()
            if not line or line.startswith('#') or line.lower().startswith('name'):
                continue
            parts = line.split()
            if parts:
                status = parts[1] if len(parts) > 1 else 'unknown'
                result['sandboxes'].append({'name': parts[0], 'status': status, 'pid': None, 'created': None, 'preset': None})

    # Policy summary
    policy_yaml = info.get('policy_yaml')
    policy_hash = info.get('policy_hash')
    if policy_yaml:
        result['network_policies'] = _d._parse_network_policies(policy_yaml)
        result['policy'] = {
            'hash': policy_hash,
            'lines': len(policy_yaml.splitlines()),
            'size_bytes': len(policy_yaml.encode()),
        }

    # Drift detection: compare policy hash vs last seen
    if policy_hash:
        if _d._nemoclaw_policy_hash is None:
            _d._nemoclaw_policy_hash = policy_hash
        elif _d._nemoclaw_policy_hash != policy_hash:
            _d._nemoclaw_drift_info = {
                'detected_at': datetime.utcnow().isoformat() + 'Z',
                'previous_hash': _d._nemoclaw_policy_hash,
                'current_hash': policy_hash,
            }
            _d._nemoclaw_policy_hash = policy_hash

        if _d._nemoclaw_drift_info:
            result['drift'] = _d._nemoclaw_drift_info

    return jsonify(result)


@bp_nemoclaw.route('/api/nemoclaw/governance/acknowledge-drift', methods=['POST'])
def api_nemoclaw_acknowledge_drift():
    """Clear the drift alert (user acknowledged the policy change)."""
    import dashboard as _d
    _d._nemoclaw_drift_info = {}
    return jsonify({'ok': True})


# ── NemoClaw Governance Routes ───────────────────────────────────────────────


@bp_nemoclaw.route('/api/nemoclaw/status')
def api_nemoclaw_status():
    """Detect NemoClaw installation and return full status."""
    import dashboard as _d
    data = _d._detect_nemoclaw()
    if not data:
        return jsonify({"installed": False})
    # Policy drift detection
    current_hash = data.get("policy_hash")
    if current_hash:
        if _d._nemoclaw_policy_hash is None:
            _d._nemoclaw_policy_hash = current_hash
        elif _d._nemoclaw_policy_hash != current_hash:
            _d._nemoclaw_drift_info = {
                "old_hash": _d._nemoclaw_policy_hash,
                "new_hash": current_hash,
                "detected_at": datetime.now(timezone.utc).isoformat(),
            }
            _d._nemoclaw_policy_hash = current_hash
            data["policy_drifted"] = True
            data["drift_info"] = _d._nemoclaw_drift_info
        else:
            data["policy_drifted"] = False
    # Parse network policies for structured display
    if data.get("policy_yaml"):
        data["network_policies"] = _d._parse_network_policies(data["policy_yaml"])
    return jsonify(data)


@bp_nemoclaw.route('/api/nemoclaw/policy')
def api_nemoclaw_policy():
    """Return full policy YAML + hash + drift status."""
    import dashboard as _d
    data = _d._detect_nemoclaw()
    if not data:
        return jsonify({"installed": False, "policy_yaml": None})
    result = {
        "installed": True,
        "policy_yaml": data.get("policy_yaml"),
        "policy_hash": data.get("policy_hash"),
        "policy_drifted": False,
        "drift_info": None,
    }
    current_hash = data.get("policy_hash")
    if current_hash:
        if _d._nemoclaw_policy_hash and _d._nemoclaw_policy_hash != current_hash:
            result["policy_drifted"] = True
            result["drift_info"] = _d._nemoclaw_drift_info
        elif _d._nemoclaw_policy_hash is None:
            _d._nemoclaw_policy_hash = current_hash
    if data.get("policy_yaml"):
        result["network_policies"] = _d._parse_network_policies(data["policy_yaml"])
    return jsonify(result)


@bp_nemoclaw.route('/api/nemoclaw/approve', methods=['POST'])
def api_nemoclaw_approve():
    """Approve a pending NemoClaw egress chunk."""
    data = request.get_json() or {}
    sandbox = data.get('sandbox')
    chunk_id = data.get('chunk_id')
    if not sandbox or not chunk_id:
        return jsonify({'error': 'missing sandbox or chunk_id'}), 400
    import subprocess as _sp
    r = _sp.run(
        ['openshell', 'draft', 'approve', sandbox, chunk_id],
        capture_output=True, text=True, timeout=10
    )
    return jsonify({'ok': r.returncode == 0, 'output': r.stdout or r.stderr})


@bp_nemoclaw.route('/api/nemoclaw/reject', methods=['POST'])
def api_nemoclaw_reject():
    """Reject a pending NemoClaw egress chunk."""
    data = request.get_json() or {}
    sandbox = data.get('sandbox')
    chunk_id = data.get('chunk_id')
    reason = data.get('reason', '')
    if not sandbox or not chunk_id:
        return jsonify({'error': 'missing sandbox or chunk_id'}), 400
    import subprocess as _sp
    cmd = ['openshell', 'draft', 'reject', sandbox, chunk_id]
    if reason:
        cmd += ['--reason', reason]
    r = _sp.run(cmd, capture_output=True, text=True, timeout=10)
    return jsonify({'ok': r.returncode == 0, 'output': r.stdout or r.stderr})


# ── Cloud-Pro upsell flag (issue #1328) ────────────────────────────────────
#
# OSS users can SEE the approvals queue grow but get zero notification surface
# (Slack / PagerDuty / email dispatch lives in Cloud-Pro per memory
# ``project_alerts_pro_feature.md``). The dashboard JS renders an inline CTA
# above the queue table whenever this flag is true: queue has >=1 pending row
# AND the caller is NOT a Cloud-Pro user. Pro users never see the CTA.
#
# Same pattern as ``capped_pro_gated`` on /api/loop-signals (issue #1376):
# decision lives on the server so the dashboard does not have to re-implement
# the Pro check. Fails closed (treats any error as "not pro") so we never
# accidentally suppress the upsell on a free node.
def _annotate_pro_upsell(payload):
    """Stamp ``pro_gated_upsell`` + ``pending_count`` on the response when the
    queue has rows and the caller is NOT Cloud-Pro. No-op on empty queues so
    the empty-state stays clean."""
    try:
        approvals = payload.get("approvals") or []
        pending_count = len(approvals)
        payload["pending_count"] = pending_count
        if pending_count <= 0:
            payload["pro_gated_upsell"] = False
            return payload
        try:
            import dashboard as _d
            is_pro = bool(_d._is_pro_user())
        except Exception:
            is_pro = False
        payload["pro_gated_upsell"] = (not is_pro)
    except Exception:
        # Never let the CTA flag-stamping break the response — the queue
        # itself is the load-bearing thing here.
        payload.setdefault("pro_gated_upsell", False)
        payload.setdefault("pending_count", 0)
    return payload


@bp_nemoclaw.route('/api/nemoclaw/pending-approvals')
def api_nemoclaw_pending_approvals():
    """Return pending egress approval requests from openshell.

    Phase 4 of epic #1032: when ``CLAWMETRY_LOCAL_STORE_READ=1`` AND the
    local DuckDB ``approvals`` table has pending rows, serve from there
    and tag ``_source: "local_store"``. Otherwise fall through to the
    legacy ``openshell draft get`` CLI path (response is unchanged).

    Issue #1328: every return path is annotated with ``pro_gated_upsell``
    + ``pending_count`` so the dashboard JS can render the Cloud-Pro
    notifications upsell CTA without re-deriving tier on the client.
    """
    if is_local_store_read_enabled():
        fast = _try_local_store_approvals()
        if fast is not None:
            return jsonify(_annotate_pro_upsell(fast))
    import shutil as _shutil
    if not _shutil.which('openshell'):
        return jsonify(_annotate_pro_upsell({'installed': False, 'approvals': []}))
    try:
        # Get sandbox names
        import subprocess as _sp
        r = _sp.run(['nemoclaw', 'list'], capture_output=True, text=True, timeout=5)
        approvals = []
        sandboxes = []
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith('#') or line.lower().startswith('name') or line.startswith('-'):
                continue
            parts = line.split()
            if parts:
                sandboxes.append(parts[0])
        for sandbox in sandboxes:
            # Try JSON output first
            r2 = _sp.run(
                ['openshell', 'draft', 'get', sandbox, '--status', 'pending', '--json'],
                capture_output=True, text=True, timeout=5
            )
            if r2.returncode == 0 and r2.stdout.strip():
                try:
                    import json as _j
                    chunks = _j.loads(r2.stdout)
                    if not isinstance(chunks, list):
                        chunks = [chunks] if isinstance(chunks, dict) else []
                    for chunk in chunks:
                        endpoints = chunk.get('proposed_rule', {}).get('endpoints', [{}])
                        first_ep = endpoints[0] if endpoints else {}
                        approvals.append({
                            'sandbox': sandbox,
                            'chunk_id': chunk.get('id'),
                            'rule_name': chunk.get('rule_name'),
                            'host': first_ep.get('host'),
                            'port': first_ep.get('port'),
                            'protocol': first_ep.get('protocol'),
                            'status': 'pending',
                            'ts': chunk.get('created_at'),
                        })
                    continue
                except (ValueError, KeyError):
                    pass
            # Fallback: plain text
            r3 = _sp.run(
                ['openshell', 'draft', 'get', sandbox, '--status', 'pending'],
                capture_output=True, text=True, timeout=5
            )
            if r3.returncode == 0:
                for line in r3.stdout.splitlines():
                    line = line.strip()
                    if not line or line.startswith('#') or line.lower().startswith('id'):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        approvals.append({
                            'sandbox': sandbox,
                            'chunk_id': parts[0],
                            'rule_name': parts[1] if len(parts) > 1 else None,
                            'host': parts[2] if len(parts) > 2 else None,
                            'port': parts[3] if len(parts) > 3 else None,
                            'protocol': None,
                            'status': 'pending',
                            'ts': None,
                        })
        return jsonify(_annotate_pro_upsell({'installed': True, 'approvals': approvals}))
    except Exception as e:
        return jsonify(_annotate_pro_upsell({'installed': True, 'approvals': [], 'error': str(e)}))


# ── NemoClaw guardrail events + metrics (issue #876) ─────────────────────────

def _try_local_store_guardrail_events(since=None, limit=100):
    """Return guardrail events from DuckDB via daemon proxy, or None on failure."""
    try:
        from routes.local_query import local_store_via_daemon
        kwargs = {"limit": limit}
        if since:
            kwargs["since"] = since
        rows = local_store_via_daemon("query_guardrail_events", **kwargs)
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            kwargs = {"limit": limit}
            if since:
                kwargs["since"] = since
            rows = store.query_guardrail_events(**kwargs)
        except Exception:
            return None
    return rows if rows is not None else []


@bp_nemoclaw.route('/api/nemoclaw/events')
def api_nemoclaw_events():
    """Return recent NemoClaw guardrail enforcement events from local DuckDB."""
    import dashboard as _d
    installed = _d._detect_nemoclaw() is not None
    since = request.args.get('since')
    try:
        limit = max(1, min(500, int(request.args.get('limit', 100))))
    except (TypeError, ValueError):
        limit = 100
    events = _try_local_store_guardrail_events(since=since, limit=limit) or []
    return jsonify({
        'installed': installed,
        'events': events,
        'total': len(events),
    })


def _try_local_store_nemoclaw_metrics():
    """Return NemoClaw metrics from DuckDB via daemon proxy, or None on failure."""
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon("query_nemoclaw_metrics")
    except Exception:
        result = None
    if result is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            result = store.query_nemoclaw_metrics()
        except Exception:
            return None
    return result


@bp_nemoclaw.route('/api/nemoclaw/metrics')
def api_nemoclaw_metrics():
    """Return aggregate NemoClaw metrics (approval rates, latency, trigger count)."""
    import dashboard as _d
    installed = _d._detect_nemoclaw() is not None
    metrics = _try_local_store_nemoclaw_metrics() or {
        "total_approvals": 0,
        "approved_count": 0,
        "denied_count": 0,
        "approval_rate_pct": None,
        "avg_latency_secs": None,
        "triggers_24h": 0,
    }
    return jsonify({
        'installed': installed,
        'metrics': metrics,
    })
