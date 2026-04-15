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
"""
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

bp_nemoclaw = Blueprint('nemoclaw', __name__)


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


@bp_nemoclaw.route('/api/nemoclaw/pending-approvals')
def api_nemoclaw_pending_approvals():
    """Return pending egress approval requests from openshell."""
    import shutil as _shutil
    if not _shutil.which('openshell'):
        return jsonify({'installed': False, 'approvals': []})
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
        return jsonify({'installed': True, 'approvals': approvals})
    except Exception as e:
        return jsonify({'installed': True, 'approvals': [], 'error': str(e)})
