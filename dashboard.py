#!/usr/bin/env python3
"""
ClawMetry - See your agent think 🦞

Real-time observability dashboard for OpenClaw AI agents.
Single-file Flask app with zero config - auto-detects your setup.

Usage:
    clawmetry                             # Auto-detect everything
    clawmetry --port 9000                 # Custom port
    clawmetry --workspace ~/bot           # Custom workspace
    OPENCLAW_HOME=~/bot clawmetry

https://github.com/vivekchand/clawmetry
MIT License
"""

import os
import sys
import glob
import json
import socket
from collections import deque
import argparse
import subprocess
import time
import threading
import select
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template_string, request, jsonify, Response, make_response

# Optional: OpenTelemetry protobuf support for OTLP receiver
_HAS_OTEL_PROTO = False
try:
    from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2
    from opentelemetry.proto.collector.traces.v1 import trace_service_pb2
    _HAS_OTEL_PROTO = True
except ImportError:
    metrics_service_pb2 = None
    trace_service_pb2 = None

__version__ = "0.8.4"

app = Flask(__name__)

# ── Configuration (auto-detected, overridable via CLI/env) ──────────────
MC_URL = os.environ.get("MC_URL", "")  # Optional Mission Control URL, empty = disabled
WORKSPACE = None
MEMORY_DIR = None
LOG_DIR = None
SESSIONS_DIR = None
USER_NAME = None
GATEWAY_URL = None  # e.g. http://localhost:18789
GATEWAY_TOKEN = None  # Bearer token for /tools/invoke
CET = timezone(timedelta(hours=1))
SSE_MAX_SECONDS = 300
MAX_LOG_STREAM_CLIENTS = 10
MAX_HEALTH_STREAM_CLIENTS = 10
_stream_clients_lock = threading.Lock()
_active_log_stream_clients = 0
_active_health_stream_clients = 0
EXTRA_SERVICES = []  # List of {'name': str, 'port': int} from --monitor-service flags

# ── OTLP Metrics Store ─────────────────────────────────────────────────
METRICS_FILE = None  # Set via CLI/env, defaults to {WORKSPACE}/.clawmetry-metrics.json
_metrics_lock = threading.Lock()
_otel_last_received = 0  # timestamp of last OTLP data received

metrics_store = {
    "tokens": [],       # [{timestamp, input, output, total, model, channel, provider}]
    "cost": [],         # [{timestamp, usd, model, channel, provider}]
    "runs": [],         # [{timestamp, duration_ms, model, channel}]
    "messages": [],     # [{timestamp, channel, outcome, duration_ms}]
    "webhooks": [],     # [{timestamp, channel, type}]
}
MAX_STORE_ENTRIES = 10_000
STORE_RETENTION_DAYS = 14


def _metrics_file_path():
    """Get the path to the metrics persistence file."""
    if METRICS_FILE:
        return METRICS_FILE
    if WORKSPACE:
        return os.path.join(WORKSPACE, '.clawmetry-metrics.json')
    return os.path.expanduser('~/.clawmetry-metrics.json')


def _load_metrics_from_disk():
    """Load persisted metrics on startup."""
    global metrics_store, _otel_last_received
    path = _metrics_file_path()
    if not os.path.exists(path):
        return
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key in metrics_store:
                if key in data and isinstance(data[key], list):
                    metrics_store[key] = data[key][-MAX_STORE_ENTRIES:]
            _otel_last_received = data.get('_last_received', 0)
        _expire_old_entries()
    except json.JSONDecodeError as e:
        print(f"⚠️  Warning: Failed to parse metrics file {path}: {e}")
        # Create backup of corrupted file
        backup_path = f"{path}.corrupted.{int(time.time())}"
        try:
            os.rename(path, backup_path)
            print(f"💾 Corrupted file backed up to {backup_path}")
        except OSError:
            pass
    except (IOError, OSError) as e:
        print(f"⚠️  Warning: Failed to read metrics file {path}: {e}")
    except Exception as e:
        print(f"⚠️  Warning: Unexpected error loading metrics: {e}")


def _save_metrics_to_disk():
    """Persist metrics store to JSON file."""
    path = _metrics_file_path()
    try:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        data = {}
        with _metrics_lock:
            for k in metrics_store:
                data[k] = list(metrics_store[k])
        data['_last_received'] = _otel_last_received
        data['_saved_at'] = time.time()
        tmp = path + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except OSError as e:
        print(f"⚠️  Warning: Failed to save metrics to {path}: {e}")
        if "No space left on device" in str(e):
            print("💾 Disk full! Consider cleaning up old files or expanding storage.")
    except json.JSONEncodeError as e:
        print(f"⚠️  Warning: Failed to serialize metrics data: {e}")
    except Exception as e:
        print(f"⚠️  Warning: Unexpected error saving metrics: {e}")


def _expire_old_entries():
    """Remove entries older than STORE_RETENTION_DAYS."""
    cutoff = time.time() - (STORE_RETENTION_DAYS * 86400)
    with _metrics_lock:
        for key in metrics_store:
            metrics_store[key] = [
                e for e in metrics_store[key]
                if e.get('timestamp', 0) > cutoff
            ][-MAX_STORE_ENTRIES:]


def _add_metric(category, entry):
    """Add an entry to the metrics store (thread-safe)."""
    global _otel_last_received
    with _metrics_lock:
        metrics_store[category].append(entry)
        if len(metrics_store[category]) > MAX_STORE_ENTRIES:
            metrics_store[category] = metrics_store[category][-MAX_STORE_ENTRIES:]
        _otel_last_received = time.time()


def _metrics_flush_loop():
    """Background thread: save metrics to disk every 60 seconds."""
    while True:
        time.sleep(60)
        try:
            _expire_old_entries()
            _save_metrics_to_disk()
        except KeyboardInterrupt:
            print("📊 Metrics flush loop shutting down...")
            break
        except Exception as e:
            print(f"⚠️  Warning: Error in metrics flush loop: {e}")
            # Continue running despite errors


def _start_metrics_flush_thread():
    """Start the background metrics flush thread."""
    t = threading.Thread(target=_metrics_flush_loop, daemon=True)
    t.start()


def _has_otel_data():
    """Check if we have any OTLP metrics data."""
    return any(len(metrics_store[k]) > 0 for k in metrics_store)


# ── OTLP Protobuf Helpers ──────────────────────────────────────────────

def _otel_attr_value(val):
    """Convert an OTel AnyValue to a Python value."""
    if val.HasField('string_value'):
        return val.string_value
    if val.HasField('int_value'):
        return val.int_value
    if val.HasField('double_value'):
        return val.double_value
    if val.HasField('bool_value'):
        return val.bool_value
    return str(val)


def _get_data_points(metric):
    """Extract data points from a metric regardless of type."""
    if metric.HasField('sum'):
        return metric.sum.data_points
    elif metric.HasField('gauge'):
        return metric.gauge.data_points
    elif metric.HasField('histogram'):
        return metric.histogram.data_points
    elif metric.HasField('summary'):
        return metric.summary.data_points
    return []


def _get_dp_value(dp):
    """Extract the numeric value from a data point."""
    if hasattr(dp, 'as_double') and dp.as_double:
        return dp.as_double
    if hasattr(dp, 'as_int') and dp.as_int:
        return dp.as_int
    if hasattr(dp, 'sum') and dp.sum:
        return dp.sum
    if hasattr(dp, 'count') and dp.count:
        return dp.count
    return 0


def _get_dp_attrs(dp):
    """Extract attributes from a data point."""
    attrs = {}
    for attr in dp.attributes:
        attrs[attr.key] = _otel_attr_value(attr.value)
    return attrs


def _process_otlp_metrics(pb_data):
    """Decode OTLP metrics protobuf and store relevant data."""
    req = metrics_service_pb2.ExportMetricsServiceRequest()
    req.ParseFromString(pb_data)

    for resource_metrics in req.resource_metrics:
        resource_attrs = {}
        if resource_metrics.resource:
            for attr in resource_metrics.resource.attributes:
                resource_attrs[attr.key] = _otel_attr_value(attr.value)

        for scope_metrics in resource_metrics.scope_metrics:
            for metric in scope_metrics.metrics:
                name = metric.name
                ts = time.time()

                if name == 'openclaw.tokens':
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric('tokens', {
                            'timestamp': ts,
                            'input': attrs.get('input_tokens', 0),
                            'output': attrs.get('output_tokens', 0),
                            'total': _get_dp_value(dp),
                            'model': attrs.get('model', resource_attrs.get('model', '')),
                            'channel': attrs.get('channel', resource_attrs.get('channel', '')),
                            'provider': attrs.get('provider', resource_attrs.get('provider', '')),
                        })
                elif name == 'openclaw.cost.usd':
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric('cost', {
                            'timestamp': ts,
                            'usd': _get_dp_value(dp),
                            'model': attrs.get('model', resource_attrs.get('model', '')),
                            'channel': attrs.get('channel', resource_attrs.get('channel', '')),
                            'provider': attrs.get('provider', resource_attrs.get('provider', '')),
                        })
                elif name == 'openclaw.run.duration_ms':
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric('runs', {
                            'timestamp': ts,
                            'duration_ms': _get_dp_value(dp),
                            'model': attrs.get('model', resource_attrs.get('model', '')),
                            'channel': attrs.get('channel', resource_attrs.get('channel', '')),
                        })
                elif name == 'openclaw.context.tokens':
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric('tokens', {
                            'timestamp': ts,
                            'input': _get_dp_value(dp),
                            'output': 0,
                            'total': _get_dp_value(dp),
                            'model': attrs.get('model', resource_attrs.get('model', '')),
                            'channel': attrs.get('channel', resource_attrs.get('channel', '')),
                            'provider': attrs.get('provider', resource_attrs.get('provider', '')),
                        })
                elif name in ('openclaw.message.processed', 'openclaw.message.queued', 'openclaw.message.duration_ms'):
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        outcome = 'processed' if 'processed' in name else ('queued' if 'queued' in name else 'duration')
                        _add_metric('messages', {
                            'timestamp': ts,
                            'channel': attrs.get('channel', resource_attrs.get('channel', '')),
                            'outcome': outcome,
                            'duration_ms': _get_dp_value(dp) if 'duration' in name else 0,
                        })
                elif name in ('openclaw.webhook.received', 'openclaw.webhook.error', 'openclaw.webhook.duration_ms'):
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        wtype = 'received' if 'received' in name else ('error' if 'error' in name else 'duration')
                        _add_metric('webhooks', {
                            'timestamp': ts,
                            'channel': attrs.get('channel', resource_attrs.get('channel', '')),
                            'type': wtype,
                        })


def _process_otlp_traces(pb_data):
    """Decode OTLP traces protobuf and extract relevant span data."""
    req = trace_service_pb2.ExportTraceServiceRequest()
    req.ParseFromString(pb_data)

    for resource_spans in req.resource_spans:
        resource_attrs = {}
        if resource_spans.resource:
            for attr in resource_spans.resource.attributes:
                resource_attrs[attr.key] = _otel_attr_value(attr.value)

        for scope_spans in resource_spans.scope_spans:
            for span in scope_spans.spans:
                attrs = {}
                for attr in span.attributes:
                    attrs[attr.key] = _otel_attr_value(attr.value)

                ts = time.time()
                duration_ns = span.end_time_unix_nano - span.start_time_unix_nano
                duration_ms = duration_ns / 1_000_000

                span_name = span.name.lower()
                if 'run' in span_name or 'completion' in span_name:
                    _add_metric('runs', {
                        'timestamp': ts,
                        'duration_ms': duration_ms,
                        'model': attrs.get('model', resource_attrs.get('model', '')),
                        'channel': attrs.get('channel', resource_attrs.get('channel', '')),
                    })
                elif 'message' in span_name:
                    _add_metric('messages', {
                        'timestamp': ts,
                        'channel': attrs.get('channel', resource_attrs.get('channel', '')),
                        'outcome': 'processed',
                        'duration_ms': duration_ms,
                    })


def _get_otel_usage_data():
    """Aggregate OTLP metrics into usage data for the Usage tab."""
    today = datetime.now()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    week_start = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp()

    daily_tokens = {}
    daily_cost = {}
    model_usage = {}

    with _metrics_lock:
        for entry in metrics_store['tokens']:
            ts = entry.get('timestamp', 0)
            day = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            total = entry.get('total', 0)
            daily_tokens[day] = daily_tokens.get(day, 0) + total
            model = entry.get('model', 'unknown') or 'unknown'
            model_usage[model] = model_usage.get(model, 0) + total

        for entry in metrics_store['cost']:
            ts = entry.get('timestamp', 0)
            day = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            daily_cost[day] = daily_cost.get(day, 0) + entry.get('usd', 0)

    days = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        ds = d.strftime('%Y-%m-%d')
        days.append({
            'date': ds,
            'tokens': daily_tokens.get(ds, 0),
            'cost': daily_cost.get(ds, 0),
        })

    today_str = today.strftime('%Y-%m-%d')
    today_tok = daily_tokens.get(today_str, 0)
    week_tok = sum(v for k, v in daily_tokens.items()
                   if _safe_date_ts(k) >= week_start)
    month_tok = sum(v for k, v in daily_tokens.items()
                    if _safe_date_ts(k) >= month_start)
    today_cost_val = daily_cost.get(today_str, 0)
    week_cost_val = sum(v for k, v in daily_cost.items()
                        if _safe_date_ts(k) >= week_start)
    month_cost_val = sum(v for k, v in daily_cost.items()
                         if _safe_date_ts(k) >= month_start)

    run_durations = []
    with _metrics_lock:
        for entry in metrics_store['runs']:
            run_durations.append(entry.get('duration_ms', 0))
    avg_run_ms = sum(run_durations) / len(run_durations) if run_durations else 0

    msg_count = len(metrics_store['messages'])

    # Enhanced cost tracking for OTLP data
    trend_data = _analyze_usage_trends(daily_tokens) 
    warnings = _generate_cost_warnings(today_cost_val, week_cost_val, month_cost_val, trend_data)

    return {
        'source': 'otlp',
        'days': days,
        'today': today_tok,
        'week': week_tok,
        'month': month_tok,
        'todayCost': round(today_cost_val, 4),
        'weekCost': round(week_cost_val, 4),
        'monthCost': round(month_cost_val, 4),
        'avgRunMs': round(avg_run_ms, 1),
        'messageCount': msg_count,
        'modelBreakdown': [
            {'model': k, 'tokens': v}
            for k, v in sorted(model_usage.items(), key=lambda x: -x[1])
        ],
        'trend': trend_data,
        'warnings': warnings,
    }


def _safe_date_ts(date_str):
    """Parse a YYYY-MM-DD date string to a timestamp, returning 0 on failure."""
    if not date_str or not isinstance(date_str, str):
        return 0
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').timestamp()
    except ValueError:
        # Invalid date format - expected but handled gracefully
        return 0
    except Exception as e:
        print(f"⚠️  Warning: Unexpected error parsing date '{date_str}': {e}")
        return 0


def validate_configuration():
    """Validate the detected configuration and provide helpful feedback for new users."""
    warnings = []
    tips = []
    
    # Check if workspace looks like a real OpenClaw setup
    workspace_files = ['SOUL.md', 'AGENTS.md', 'MEMORY.md', 'memory']
    found_files = []
    for f in workspace_files:
        path = os.path.join(WORKSPACE, f)
        if os.path.exists(path):
            found_files.append(f)
    
    if not found_files:
        warnings.append(f"⚠️  No OpenClaw workspace files found in {WORKSPACE}")
        tips.append("💡 Create SOUL.md, AGENTS.md, or MEMORY.md to set up your agent workspace")
    
    # Check if log directory exists and has recent logs
    if not os.path.exists(LOG_DIR):
        warnings.append(f"⚠️  Log directory doesn't exist: {LOG_DIR}")
        tips.append("💡 Make sure OpenClaw/Moltbot is running to generate logs")
    else:
        # Check for recent log files
        log_pattern = os.path.join(LOG_DIR, "*claw*.log")
        recent_logs = [f for f in glob.glob(log_pattern) 
                      if os.path.getmtime(f) > time.time() - 86400]  # Last 24h
        if not recent_logs:
            warnings.append(f"⚠️  No recent log files found in {LOG_DIR}")
            tips.append("💡 Start your OpenClaw agent to see real-time data")
    
    # Check if sessions directory exists
    if not SESSIONS_DIR or not os.path.exists(SESSIONS_DIR):
        warnings.append(f"⚠️  Sessions directory not found: {SESSIONS_DIR}")
        tips.append("💡 Sessions will appear when your agent starts conversations")
    
    # Check if OpenClaw binary is available
    try:
        subprocess.run(['openclaw', '--version'], capture_output=True, timeout=2)
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        warnings.append("⚠️  OpenClaw binary not found in PATH")
        tips.append("💡 Install OpenClaw: https://github.com/openclaw/openclaw")
    
    return warnings, tips


def _auto_detect_data_dir():
    """Auto-detect OpenClaw data directory, including Docker volume mounts."""
    # Standard locations
    candidates = [
        os.path.expanduser('~/.openclaw'),
        os.path.expanduser('~/.clawdbot'),
    ]
    # Docker volume mounts (Hostinger pattern: /docker/*/data/.openclaw)
    try:
        import glob as _glob
        for pattern in ['/docker/*/data/.openclaw', '/docker/*/.openclaw',
                        '/var/lib/docker/volumes/*/_data/.openclaw']:
            candidates.extend(_glob.glob(pattern))
    except Exception:
        pass
    # Check Docker inspect for mount points
    try:
        import subprocess as _sp
        container_ids = _sp.check_output(
            ['docker', 'ps', '-q', '--filter', 'ancestor=*openclaw*'],
            timeout=3, stderr=_sp.DEVNULL
        ).decode().strip().split()
        if not container_ids:
            # Try all containers
            container_ids = _sp.check_output(
                ['docker', 'ps', '-q'], timeout=3, stderr=_sp.DEVNULL
            ).decode().strip().split()
        for cid in container_ids[:3]:
            try:
                mounts = _sp.check_output(
                    ['docker', 'inspect', cid, '--format',
                     '{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}'],
                    timeout=3, stderr=_sp.DEVNULL
                ).decode().strip().split()
                for mount in mounts:
                    parts = mount.split(':')
                    if len(parts) >= 1:
                        src = parts[0]
                        oc_path = os.path.join(src, '.openclaw')
                        if os.path.isdir(oc_path) and oc_path not in candidates:
                            candidates.insert(0, oc_path)
                        # Also check if the mount itself is the .openclaw dir
                        if src.endswith('.openclaw') and os.path.isdir(src):
                            candidates.insert(0, src)
            except Exception:
                pass
    except Exception:
        pass
    for c in candidates:
        if c and os.path.isdir(c) and (
            os.path.isdir(os.path.join(c, 'agents')) or
            os.path.isdir(os.path.join(c, 'workspace')) or
            os.path.exists(os.path.join(c, 'cron', 'jobs.json'))
        ):
            return c
    return None

def detect_config(args=None):
    """Auto-detect OpenClaw/Moltbot paths, with CLI and env overrides."""
    global WORKSPACE, MEMORY_DIR, LOG_DIR, SESSIONS_DIR, USER_NAME

    # 0. --data-dir: set defaults from OpenClaw data directory (e.g. /path/.openclaw)
    data_dir = None
    if args and getattr(args, 'data_dir', None):
        data_dir = os.path.expanduser(args.data_dir)
    elif os.environ.get("OPENCLAW_DATA_DIR"):
        data_dir = os.path.expanduser(os.environ["OPENCLAW_DATA_DIR"])
    else:
        # Auto-detect: check common locations including Docker volumes
        data_dir = _auto_detect_data_dir()
    
    if data_dir and os.path.isdir(data_dir):
        # Auto-set workspace, sessions, crons from data dir
        ws = os.path.join(data_dir, 'workspace')
        if os.path.isdir(ws) and not (args and args.workspace):
            if not args:
                import argparse; args = argparse.Namespace()
            args.workspace = ws
        sess = os.path.join(data_dir, 'agents', 'main', 'sessions')
        if os.path.isdir(sess) and not (args and getattr(args, 'sessions_dir', None)):
            args.sessions_dir = sess

    # 1. Workspace - where agent files live (SOUL.md, MEMORY.md, memory/, etc.)
    if args and args.workspace:
        WORKSPACE = os.path.expanduser(args.workspace)
    elif os.environ.get("OPENCLAW_HOME"):
        WORKSPACE = os.path.expanduser(os.environ["OPENCLAW_HOME"])
    elif os.environ.get("OPENCLAW_WORKSPACE"):
        WORKSPACE = os.path.expanduser(os.environ["OPENCLAW_WORKSPACE"])
    else:
        # Auto-detect: check common locations
        candidates = [
            _detect_workspace_from_config(),
            os.path.expanduser("~/.openclaw/workspace"),
            os.path.expanduser("~/.clawdbot/workspace"),
            os.path.expanduser("~/clawd"),
            os.path.expanduser("~/openclaw"),
            os.getcwd(),
        ]
        for c in candidates:
            if c and os.path.isdir(c) and (
                os.path.exists(os.path.join(c, "SOUL.md")) or
                os.path.exists(os.path.join(c, "AGENTS.md")) or
                os.path.exists(os.path.join(c, "MEMORY.md")) or
                os.path.isdir(os.path.join(c, "memory"))
            ):
                WORKSPACE = c
                break
        if not WORKSPACE:
            WORKSPACE = os.getcwd()

    MEMORY_DIR = os.path.join(WORKSPACE, "memory")

    # 2. Log directory
    if args and args.log_dir:
        LOG_DIR = os.path.expanduser(args.log_dir)
    elif os.environ.get("OPENCLAW_LOG_DIR"):
        LOG_DIR = os.path.expanduser(os.environ["OPENCLAW_LOG_DIR"])
    else:
        candidates = ["/tmp/moltbot", "/tmp/openclaw", os.path.expanduser("~/.clawdbot/logs")]
        LOG_DIR = next((d for d in candidates if os.path.isdir(d)), "/tmp/openclaw")

    # 3. Sessions directory (transcript .jsonl files)
    if args and getattr(args, 'sessions_dir', None):
        SESSIONS_DIR = os.path.expanduser(args.sessions_dir)
    elif os.environ.get("OPENCLAW_SESSIONS_DIR"):
        SESSIONS_DIR = os.path.expanduser(os.environ["OPENCLAW_SESSIONS_DIR"])
    else:
        candidates = [
            os.path.expanduser('~/.openclaw/agents/main/sessions'),
            os.path.expanduser('~/.clawdbot/agents/main/sessions'),
            os.path.join(WORKSPACE, 'sessions') if WORKSPACE else None,
            os.path.expanduser('~/.openclaw/sessions'),
            os.path.expanduser('~/.clawdbot/sessions'),
        ]
        # Also scan agents dirs
        for agents_base in [os.path.expanduser('~/.openclaw/agents'), os.path.expanduser('~/.clawdbot/agents')]:
            if os.path.isdir(agents_base):
                for agent in os.listdir(agents_base):
                    p = os.path.join(agents_base, agent, 'sessions')
                    if p not in candidates:
                        candidates.append(p)
        SESSIONS_DIR = next((d for d in candidates if d and os.path.isdir(d)), candidates[0] if candidates else None)

    # 4. User name (shown in Flow visualization)
    if args and args.name:
        USER_NAME = args.name
    elif os.environ.get("OPENCLAW_USER"):
        USER_NAME = os.environ["OPENCLAW_USER"]
    else:
        USER_NAME = "You"


def _detect_workspace_from_config():
    """Try to read workspace from Moltbot/OpenClaw agent config."""
    config_paths = [
        os.path.expanduser("~/.clawdbot/agents/main/config.json"),
        os.path.expanduser("~/.clawdbot/config.json"),
    ]
    for cp in config_paths:
        try:
            with open(cp) as f:
                data = json.load(f)
                ws = data.get("workspace") or data.get("workspaceDir")
                if ws:
                    return os.path.expanduser(ws)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
    return None


def _detect_gateway_port():
    """Detect the OpenClaw gateway port from config files or environment."""
    # Check environment variable first
    env_port = os.environ.get('OPENCLAW_GATEWAY_PORT', '').strip()
    if env_port:
        try:
            return int(env_port)
        except ValueError:
            pass
    # Try reading from gateway config
    # Try JSON configs first (moltbot.json / clawdbot.json)
    json_paths = [
        os.path.expanduser('~/.openclaw/moltbot.json'),
        os.path.expanduser('~/.openclaw/clawdbot.json'),
        os.path.expanduser('~/.clawdbot/clawdbot.json'),
    ]
    for jp in json_paths:
        try:
            import json as _json
            with open(jp) as f:
                cfg = _json.load(f)
            gw = cfg.get('gateway', {})
            if isinstance(gw, dict) and 'port' in gw:
                return int(gw['port'])
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            pass
    # Try YAML configs
    yaml_paths = [
        os.path.expanduser('~/.openclaw/gateway.yaml'),
        os.path.expanduser('~/.openclaw/gateway.yml'),
        os.path.expanduser('~/.clawdbot/gateway.yaml'),
        os.path.expanduser('~/.clawdbot/gateway.yml'),
    ]
    for cp in yaml_paths:
        try:
            with open(cp) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('port:'):
                        port_val = line.split(':', 1)[1].strip()
                        return int(port_val)
        except (FileNotFoundError, ValueError, IndexError):
            pass
    return 18789  # Default OpenClaw gateway port


def _detect_gateway_token():
    """Detect the OpenClaw gateway auth token from env, config files, or running process."""
    # 1. Environment variable (most reliable - matches running gateway)
    env_token = os.environ.get('OPENCLAW_GATEWAY_TOKEN', '').strip()
    if env_token:
        return env_token
    # 2. Try reading from running gateway process env (Linux only)
    try:
        import subprocess as _sp
        result = _sp.run(['pgrep', '-f', 'openclaw-gatewa'], capture_output=True, text=True, timeout=3)
        for pid in result.stdout.strip().split('\n'):
            pid = pid.strip()
            if pid:
                try:
                    with open(f'/proc/{pid}/environ', 'r') as f:
                        env_data = f.read()
                    for entry in env_data.split('\0'):
                        if entry.startswith('OPENCLAW_GATEWAY_TOKEN='):
                            return entry.split('=', 1)[1]
                except (PermissionError, FileNotFoundError):
                    pass
    except Exception:
        pass
    # 3. Config files
    json_paths = [
        os.path.expanduser('~/.openclaw/moltbot.json'),
        os.path.expanduser('~/.openclaw/clawdbot.json'),
        os.path.expanduser('~/.clawdbot/clawdbot.json'),
    ]
    for jp in json_paths:
        try:
            import json as _json
            with open(jp) as f:
                cfg = _json.load(f)
            gw = cfg.get('gateway', {})
            auth = gw.get('auth', {})
            if isinstance(auth, dict) and 'token' in auth:
                return auth['token']
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            pass
    return None


def _detect_disk_mounts():
    """Detect mounted filesystems to monitor (root + any large data drives)."""
    mounts = ['/']
    try:
        with open('/proc/mounts') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mount_point = parts[1]
                    fs_type = parts[2] if len(parts) > 2 else ''
                    # Include additional data mounts (skip virtual/special filesystems)
                    if (mount_point.startswith('/mnt/') or mount_point.startswith('/data')) and \
                       fs_type not in ('tmpfs', 'devtmpfs', 'proc', 'sysfs', 'cgroup', 'cgroup2'):
                        mounts.append(mount_point)
    except (IOError, OSError):
        pass
    return mounts


def get_public_ip():
    """Get the machine's public IP address (useful for cloud/VPS users)."""
    try:
        import urllib.request
        return urllib.request.urlopen("https://api.ipify.org", timeout=2).read().decode().strip()
    except Exception:
        return None


def get_local_ip():
    """Get the machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except (socket.error, OSError) as e:
        # Network unavailable or socket error - common in offline/restricted environments
        return "127.0.0.1"
    except Exception as e:
        print(f"⚠️  Warning: Unexpected error getting local IP: {e}")
        return "127.0.0.1"


# ── HTML Template ───────────────────────────────────────────────────────

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ClawMetry 🦞</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    /* Light theme (default) */
    --bg-primary: #f5f7fb;
    --bg-secondary: #ffffff;
    --bg-tertiary: #ffffff;
    --bg-hover: #f3f5f8;
    --bg-accent: #0f6fff;
    --border-primary: #e4e8ee;
    --border-secondary: #edf1f5;
    --text-primary: #101828;
    --text-secondary: #344054;
    --text-tertiary: #475467;
    --text-muted: #667085;
    --text-faint: #98a2b3;
    --text-accent: #0f6fff;
    --text-link: #0f6fff;
    --text-success: #15803d;
    --text-warning: #b45309;
    --text-error: #b42318;
    --bg-success: #ecfdf3;
    --bg-warning: #fffaeb;
    --bg-error: #fef3f2;
    --log-bg: #f7f9fc;
    --file-viewer-bg: #ffffff;
    --button-bg: #f3f5f8;
    --button-hover: #e9eef5;
    --card-shadow: 0 1px 2px rgba(16, 24, 40, 0.05), 0 1px 3px rgba(16, 24, 40, 0.1);
    --card-shadow-hover: 0 10px 18px rgba(16, 24, 40, 0.08), 0 2px 6px rgba(16, 24, 40, 0.06);
  }

  [data-theme="dark"] {
    /* Dark theme */
    --bg-primary: #0b0f14;
    --bg-secondary: #121820;
    --bg-tertiary: #151d28;
    --bg-hover: #1b2430;
    --bg-accent: #3b82f6;
    --border-primary: #273243;
    --border-secondary: #1f2937;
    --text-primary: #e6edf5;
    --text-secondary: #c1cad6;
    --text-tertiary: #98a2b3;
    --text-muted: #7c8a9d;
    --text-faint: #667085;
    --text-accent: #60a5fa;
    --text-link: #7dd3fc;
    --text-success: #4ade80;
    --text-warning: #fbbf24;
    --text-error: #f87171;
    --bg-success: #10291c;
    --bg-warning: #2a2314;
    --bg-error: #341717;
    --log-bg: #0f141c;
    --file-viewer-bg: #111722;
    --button-bg: #1d2632;
    --button-hover: #263344;
    --card-shadow: 0 1px 3px rgba(0,0,0,0.4);
    --card-shadow-hover: 0 8px 18px rgba(0,0,0,0.45);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease; }
  body { font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, sans-serif; background: radial-gradient(1200px 600px at 70% -20%, rgba(15,111,255,0.06), transparent 55%), var(--bg-primary); color: var(--text-primary); min-height: 100vh; font-size: 14px; font-weight: 500; line-height: 1.5; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }

  .nav { background: color-mix(in srgb, var(--bg-secondary) 90%, transparent); border-bottom: 1px solid var(--border-primary); padding: 8px 16px; display: flex; align-items: center; gap: 12px; overflow-x: auto; -webkit-overflow-scrolling: touch; box-shadow: 0 1px 2px rgba(16,24,40,0.06); position: sticky; top: 0; z-index: 10; backdrop-filter: blur(8px); }
  .nav h1 { font-size: 18px; font-weight: 700; color: var(--text-primary); white-space: nowrap; letter-spacing: -0.3px; }
  .nav h1 span { color: var(--text-accent); }
  .theme-toggle { background: var(--button-bg); border: none; border-radius: 8px; padding: 8px 12px; color: var(--text-tertiary); cursor: pointer; font-size: 16px; margin-left: 12px; transition: all 0.15s; box-shadow: var(--card-shadow); }
  .theme-toggle:hover { background: var(--button-hover); color: var(--text-secondary); }
  .theme-toggle:active { transform: scale(0.98); }
  
  /* === Zoom Controls === */
  .zoom-controls { display: flex; align-items: center; gap: 4px; margin-left: 12px; }
  .zoom-btn { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 6px; width: 28px; height: 28px; color: var(--text-tertiary); cursor: pointer; font-size: 16px; font-weight: 700; display: flex; align-items: center; justify-content: center; transition: all 0.15s; }
  .zoom-btn:hover { background: var(--button-hover); color: var(--text-secondary); }
  .zoom-level { font-size: 11px; color: var(--text-muted); font-weight: 600; min-width: 36px; text-align: center; }
  .nav-tabs { display: flex; gap: 4px; margin-left: auto; }
  .nav-tab { padding: 8px 16px; border-radius: 8px; background: transparent; border: 1px solid transparent; color: var(--text-tertiary); cursor: pointer; font-size: 13px; font-weight: 600; white-space: nowrap; transition: all 0.2s ease; position: relative; }
  .nav-tab:hover { background: var(--bg-hover); color: var(--text-secondary); }
  .nav-tab.active { background: var(--bg-accent); color: #ffffff; border-color: var(--bg-accent); }
  .nav-tab:active { transform: scale(0.98); }

  .page { display: none; padding: 16px 20px; max-width: 1200px; margin: 0 auto; }
  #page-overview { max-width: 1600px; padding: 8px 12px; }
  .page.active { display: block; }
  body.booting #zoom-wrapper { opacity: 0; pointer-events: none; transform: translateY(4px); }
  #zoom-wrapper { opacity: 1; transition: opacity 0.28s ease, transform 0.28s ease; }
  .boot-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(1000px 540px at 70% -20%, rgba(15,111,255,0.18), transparent 60%), var(--bg-primary);
    transition: opacity 0.28s ease;
  }
  .boot-overlay.hide { opacity: 0; pointer-events: none; }
  .boot-card {
    width: min(540px, calc(100vw - 32px));
    border-radius: 14px;
    background: color-mix(in srgb, var(--bg-secondary) 92%, transparent);
    border: 1px solid var(--border-primary);
    box-shadow: var(--card-shadow-hover);
    padding: 18px 18px 14px;
  }
  .boot-title { font-size: 20px; font-weight: 800; color: var(--text-primary); margin-bottom: 4px; }
  .boot-sub { font-size: 12px; color: var(--text-muted); margin-bottom: 14px; }
  .boot-spinner {
    width: 28px; height: 28px; border-radius: 50%;
    border: 2px solid var(--border-primary); border-top-color: var(--bg-accent);
    animation: spin 0.8s linear infinite; margin-bottom: 10px;
  }
  .boot-steps { display: grid; gap: 8px; }
  .boot-step {
    display: flex; align-items: center; gap: 8px; padding: 8px 10px;
    border: 1px solid var(--border-secondary); border-radius: 10px; background: var(--bg-tertiary);
    font-size: 12px; color: var(--text-secondary);
  }
  .boot-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-faint); flex-shrink: 0; }
  .boot-step.loading .boot-dot { background: #f59e0b; box-shadow: 0 0 0 4px rgba(245,158,11,0.18); }
  .boot-step.done .boot-dot { background: #22c55e; box-shadow: 0 0 0 4px rgba(34,197,94,0.16); }
  .boot-step.fail .boot-dot { background: #ef4444; box-shadow: 0 0 0 4px rgba(239,68,68,0.16); }
  @keyframes spin { to { transform: rotate(360deg); } }

  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 16px; }
  .card { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 12px; padding: 20px; box-shadow: var(--card-shadow); transition: transform 0.2s ease, box-shadow 0.2s ease; }
  .card-title { font-size: 12px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 1px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
  .card-title .icon { font-size: 16px; }
  .card-value { font-size: 32px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.5px; }
  .card-sub { font-size: 12px; color: var(--text-faint); margin-top: 4px; }

  .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border-secondary); }
  .stat-row:last-child { border-bottom: none; }
  .stat-label { color: var(--text-tertiary); font-size: 13px; }
  .stat-val { color: var(--text-primary); font-size: 13px; font-weight: 600; }
  .stat-val.green { color: var(--text-success); }
  .stat-val.yellow { color: var(--text-warning); }
  .stat-val.red { color: var(--text-error); }

  .session-item { padding: 12px; border-bottom: 1px solid var(--border-secondary); }
  .session-item:last-child { border-bottom: none; }
  .session-name { font-weight: 600; font-size: 14px; color: var(--text-primary); }
  .session-meta { font-size: 12px; color: var(--text-muted); margin-top: 4px; display: flex; gap: 12px; flex-wrap: wrap; }
  .session-meta span { display: flex; align-items: center; gap: 4px; }

  .cron-item { padding: 12px; border-bottom: 1px solid var(--border-secondary); }
  .cron-item:last-child { border-bottom: none; }
  .cron-name { font-weight: 600; font-size: 14px; color: var(--text-primary); }
  .cron-schedule { font-size: 12px; color: var(--text-accent); margin-top: 2px; font-family: 'SF Mono', 'Fira Code', monospace; }
  .cron-meta { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
  .cron-status { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .cron-status.ok { background: var(--bg-success); color: var(--text-success); }
  .cron-status.error { background: var(--bg-error); color: var(--text-error); }
  .cron-status.pending { background: var(--bg-warning); color: var(--text-warning); }

  /* Cron error info & fix */
  .cron-error-actions { display: inline-flex; align-items: center; gap: 6px; margin-left: 8px; vertical-align: middle; }
  .cron-info-icon { cursor: pointer; font-size: 14px; color: var(--text-muted); transition: color 0.15s; user-select: none; }
  .cron-info-icon:hover { color: var(--text-accent); }
  .cron-fix-btn { background: #f59e0b; color: #fff; border: none; border-radius: 6px; padding: 2px 10px; font-size: 11px; font-weight: 600; cursor: pointer; transition: background 0.15s; white-space: nowrap; }
  .cron-fix-btn:hover { background: #d97706; }
  .cron-error-popover { position: fixed; z-index: 1000; background: #1a1a2e; color: #e0e0e0; border: 1px solid #333; border-radius: 10px; padding: 14px 18px; max-width: 400px; font-size: 12px; line-height: 1.6; box-shadow: 0 8px 30px rgba(0,0,0,0.5); pointer-events: auto; }
  .cron-error-popover .ep-label { font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 2px; }
  .cron-error-popover .ep-value { color: #fca5a5; margin-bottom: 10px; word-break: break-word; }
  .cron-error-popover .ep-value.ts { color: #93c5fd; }
  .cron-error-popover .ep-close { position: absolute; top: 8px; right: 12px; cursor: pointer; color: #888; font-size: 16px; }
  .cron-error-popover .ep-close:hover { color: #fff; }
  .cron-toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: #16a34a; color: #fff; padding: 10px 24px; border-radius: 8px; font-size: 13px; font-weight: 600; z-index: 2000; box-shadow: 0 4px 16px rgba(0,0,0,0.3); transition: opacity 0.3s; }
  .cron-confirm-modal { position: fixed; inset: 0; z-index: 1500; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
  .cron-confirm-box { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 12px; padding: 24px; max-width: 360px; text-align: center; box-shadow: 0 8px 30px rgba(0,0,0,0.4); }
  .cron-confirm-box p { margin-bottom: 16px; font-size: 14px; color: var(--text-primary); }
  .cron-confirm-box button { padding: 8px 20px; border-radius: 8px; border: none; font-size: 13px; font-weight: 600; cursor: pointer; margin: 0 6px; }
  .cron-confirm-box .confirm-yes { background: #f59e0b; color: #fff; }
  .cron-confirm-box .confirm-yes:hover { background: #d97706; }
  .cron-confirm-box .confirm-no { background: var(--button-bg); color: var(--text-secondary); }
  .cron-confirm-box .confirm-no:hover { background: var(--button-hover); }

  .log-viewer { background: var(--log-bg); border: 1px solid var(--border-primary); border-radius: 8px; font-family: 'SF Mono', 'Fira Code', 'JetBrains Mono', monospace; font-size: 12px; line-height: 1.6; padding: 12px; max-height: 500px; overflow-y: auto; -webkit-overflow-scrolling: touch; white-space: pre-wrap; word-break: break-all; }
  .log-line { padding: 1px 0; }
  .log-line .ts { color: var(--text-muted); }
  .log-line .info { color: var(--text-link); }
  .log-line .warn { color: var(--text-warning); }
  .log-line .err { color: var(--text-error); }
  .log-line .msg { color: var(--text-secondary); }

  .memory-item { padding: 10px 12px; border-bottom: 1px solid var(--border-secondary); display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: background 0.15s; }
  .memory-item:hover { background: var(--bg-hover); }
  .memory-item:last-child { border-bottom: none; }
  .file-viewer { background: var(--file-viewer-bg); border: 1px solid var(--border-primary); border-radius: 12px; padding: 16px; margin-top: 16px; display: none; }
  .file-viewer-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .file-viewer-title { font-size: 14px; font-weight: 600; color: var(--text-accent); }
  .file-viewer-close { background: var(--button-bg); border: none; color: var(--text-secondary); padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; }
  .file-viewer-close:hover { background: var(--button-hover); }
  .file-viewer-content { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12px; color: var(--text-secondary); white-space: pre-wrap; word-break: break-word; max-height: 60vh; overflow-y: auto; line-height: 1.5; }
  .memory-name { font-weight: 600; font-size: 14px; color: var(--text-link); cursor: pointer; }
  .memory-name:hover { text-decoration: underline; }
  .memory-size { font-size: 12px; color: var(--text-faint); }

  .refresh-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
  .refresh-btn { padding: 8px 16px; background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 8px; color: var(--text-primary); cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s ease; }
  .refresh-btn:hover { background: var(--button-hover); }
  .refresh-btn:active { transform: scale(0.98); }
  .refresh-time { font-size: 12px; color: var(--text-muted); }
  .pulse { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #16a34a; animation: pulse 1.5s infinite; }
  @keyframes pulse { 0%,100% { opacity: 1; box-shadow: 0 0 4px #16a34a; } 50% { opacity: 0.3; box-shadow: none; } }
  .live-badge { display: inline-block; padding: 2px 8px; border-radius: 4px; background: var(--bg-success); color: var(--text-success); font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; animation: pulse 1.5s infinite; }

  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .badge.model { background: var(--bg-hover); color: var(--text-accent); }
  .badge.channel { background: var(--bg-hover); color: #7c3aed; }
  .badge.tokens { background: var(--bg-success); color: var(--text-success); }

  /* Cost Optimizer Styles */
  .cost-optimizer-summary { margin-bottom: 20px; }
  .cost-stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; }
  .cost-stat { background: var(--bg-hover); border-radius: 8px; padding: 12px; text-align: center; border: 1px solid var(--border-primary); }
  .cost-label { font-size: 11px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 1px; margin-bottom: 4px; }
  .cost-value { font-size: 20px; font-weight: 700; color: var(--text-primary); }
  .local-status-good { padding: 8px 12px; background: var(--bg-success); color: var(--text-success); border-radius: 6px; font-size: 13px; font-weight: 600; }
  .local-status-warning { padding: 8px 12px; background: var(--bg-warning); color: var(--text-warning); border-radius: 6px; font-size: 13px; font-weight: 600; }
  .model-list { display: flex; flex-wrap: wrap; gap: 6px; }
  .model-badge { background: var(--bg-accent); color: #ffffff; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .recommendation { border-left: 3px solid var(--text-accent); }

  .full-width { grid-column: 1 / -1; }
  .section-title { font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 24px 0 12px; display: flex; align-items: center; gap: 8px; }

  /* === Flow Visualization === */
  .flow-container { width: 100%; overflow: visible; position: relative; }
  .flow-stats { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
  .flow-stat { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 8px; padding: 8px 14px; flex: 1; min-width: 100px; box-shadow: var(--card-shadow); }
  .flow-stat-label { font-size: 10px; text-transform: uppercase; color: var(--text-muted); letter-spacing: 1px; display: block; }
  .flow-stat-value { font-size: 20px; font-weight: 700; color: var(--text-primary); display: block; margin-top: 2px; }
  #flow-svg { width: 100%; height: auto; display: block; overflow: visible; }
  #flow-svg text { font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 14px; font-weight: 700; text-anchor: middle; dominant-baseline: central; pointer-events: none; letter-spacing: -0.1px; }
  .flow-node-channel text, .flow-node-gateway text, .flow-node-session text, .flow-node-tool text { fill: #ffffff !important; }
  .flow-node-optimizer text { fill: #ffffff !important; }
  .flow-node-infra > text { fill: #ffffff !important; }
  /* Refined palette: lower saturation, clearer hierarchy */
  #node-human circle:first-child { fill: #6d5ce8 !important; stroke: #5b4bd4 !important; }
  #node-human text { fill: #6d5ce8 !important; }
  #node-telegram rect { fill: #2f6feb !important; stroke: #1f4fb8 !important; }
  #node-signal rect { fill: #0f766e !important; stroke: #115e59 !important; }
  #node-whatsapp rect { fill: #2f9e44 !important; stroke: #237738 !important; }
  #node-gateway rect { fill: #334155 !important; stroke: #1f2937 !important; }
  #node-brain rect { fill: #a63a16 !important; stroke: #7c2d12 !important; }
  #brain-model-label { fill: #fde68a !important; }
  #brain-model-text { fill: #fed7aa !important; }
  #node-session rect { fill: #3158d4 !important; stroke: #2648b6 !important; }
  #node-exec rect { fill: #d97706 !important; stroke: #b45309 !important; }
  #node-browser rect { fill: #5b39c6 !important; stroke: #4629a1 !important; }
  #node-search rect { fill: #0f766e !important; stroke: #115e59 !important; }
  #node-cron rect { fill: #4b5563 !important; stroke: #374151 !important; }
  #node-tts rect { fill: #a16207 !important; stroke: #854d0e !important; }
  #node-memory rect { fill: #1e3a8a !important; stroke: #172554 !important; }
  #node-cost-optimizer rect { fill: #166534 !important; stroke: #14532d !important; }
  #node-automation-advisor rect { fill: #4338ca !important; stroke: #3730a3 !important; }
  #node-runtime rect { fill: #334155 !important; stroke: #475569 !important; }
  #node-machine rect { fill: #424b57 !important; stroke: #2f3945 !important; }
  #node-storage rect { fill: #52525b !important; stroke: #3f3f46 !important; }
  #node-network rect { fill: #0f766e !important; stroke: #115e59 !important; }
  .flow-node-clickable { cursor: pointer; }
  .flow-node-clickable:hover rect, .flow-node-clickable:hover circle { filter: brightness(1.08); }
  .flow-node rect { rx: 12; ry: 12; stroke-width: 1.6; transition: all 0.25s ease; }
  .flow-node-brain rect { stroke-width: 2.5; }
  @keyframes dashFlow { to { stroke-dashoffset: -24; } }
  .flow-path { stroke-dasharray: 8 4; animation: dashFlow 1.2s linear infinite; }
  .flow-path.flow-path-infra { stroke-dasharray: 6 3; animation: dashFlow 2s linear infinite; }
  .flow-node-channel.active rect { filter: drop-shadow(0 0 8px rgba(59,130,246,0.38)); stroke-width: 2.2; }
  .flow-node-gateway.active rect { filter: drop-shadow(0 0 8px rgba(71,85,105,0.38)); stroke-width: 2.2; }
  .flow-node-session.active rect { filter: drop-shadow(0 0 8px rgba(49,88,212,0.35)); stroke-width: 2.2; }
  .flow-node-tool.active rect { filter: drop-shadow(0 0 7px rgba(217,119,6,0.32)); stroke-width: 2.2; }
  .flow-node-optimizer.active rect { filter: drop-shadow(0 0 7px rgba(22,101,52,0.35)); stroke-width: 2.2; }
  .flow-path { fill: none; stroke: var(--text-muted); stroke-width: 1.8; stroke-linecap: round; transition: stroke 0.35s, opacity 0.35s; opacity: 0.45; }
  .flow-path.glow-blue { stroke: #4080e0; filter: drop-shadow(0 0 6px rgba(64,128,224,0.6)); }
  .flow-path.glow-yellow { stroke: #f0c040; filter: drop-shadow(0 0 6px rgba(240,192,64,0.6)); }
  .flow-path.glow-green { stroke: #50e080; filter: drop-shadow(0 0 6px rgba(80,224,128,0.6)); }
  .flow-path.glow-red { stroke: #e04040; filter: drop-shadow(0 0 6px rgba(224,64,64,0.6)); }
  @keyframes brainPulse { 0%,100% { filter: drop-shadow(0 0 6px rgba(240,192,64,0.25)); } 50% { filter: drop-shadow(0 0 22px rgba(240,192,64,0.7)); } }
  .brain-group { animation: brainPulse 2.2s ease-in-out infinite; }
  .tool-indicator { opacity: 0.2; transition: opacity 0.3s ease; }
  .tool-indicator.active { opacity: 1; }
  .flow-label { font-size: 10px !important; fill: var(--text-muted) !important; font-weight: 500 !important; }
  .flow-node-human circle { transition: all 0.3s ease; }
  .flow-node-human.active circle { filter: drop-shadow(0 0 12px rgba(176,128,255,0.7)); }
  @keyframes humanGlow { 0%,100% { filter: drop-shadow(0 0 3px rgba(160,112,224,0.15)); } 50% { filter: drop-shadow(0 0 10px rgba(160,112,224,0.45)); } }
  .flow-node-human { animation: humanGlow 3.5s ease-in-out infinite; }
  .flow-ground { stroke: var(--border-primary); stroke-width: 1; stroke-dasharray: 8 4; }
  .flow-ground-label { font-size: 10px !important; fill: var(--text-muted) !important; font-weight: 700 !important; letter-spacing: 3px; }
  .flow-node-infra rect { rx: 6; ry: 6; stroke-width: 2; stroke-dasharray: 5 2; transition: all 0.3s ease; }
  .flow-node-infra text { font-size: 12px !important; }
  .flow-node-infra .infra-sub { font-size: 8px !important; fill: var(--text-muted) !important; font-weight: 500 !important; opacity: 0.9; }
  .flow-node-runtime rect { stroke: #4a7090; }
  .flow-node-machine rect { stroke: #606880; }
  .flow-node-storage rect { stroke: #806a30; }
  .flow-node-network rect { stroke: #308080; }
  [data-theme="dark"] .flow-node-runtime rect { fill: #10182a; }
  [data-theme="dark"] .flow-node-machine rect { fill: #141420; }
  [data-theme="dark"] .flow-node-storage rect { fill: #1a1810; }
  [data-theme="dark"] .flow-node-network rect { fill: #0e1c20; }
  .flow-node-runtime.active rect { filter: drop-shadow(0 0 10px rgba(74,112,144,0.7)); stroke-dasharray: none; stroke-width: 2.5; }
  .flow-node-machine.active rect { filter: drop-shadow(0 0 10px rgba(96,104,128,0.7)); stroke-dasharray: none; stroke-width: 2.5; }
  .flow-node-storage.active rect { filter: drop-shadow(0 0 10px rgba(128,106,48,0.7)); stroke-dasharray: none; stroke-width: 2.5; }
  .flow-node-network.active rect { filter: drop-shadow(0 0 10px rgba(48,128,128,0.7)); stroke-dasharray: none; stroke-width: 2.5; }
  .flow-path-infra { stroke-dasharray: 6 3; opacity: 0.3; }
  .flow-path.glow-cyan { stroke: #40a0b0; filter: drop-shadow(0 0 6px rgba(64,160,176,0.6)); stroke-dasharray: none; opacity: 1; }
  .flow-path.glow-purple { stroke: #b080ff; filter: drop-shadow(0 0 6px rgba(176,128,255,0.6)); }

  /* === Activity Heatmap === */
  .heatmap-wrap { overflow-x: auto; padding: 8px 0; }
  .heatmap-grid { display: grid; grid-template-columns: 60px repeat(24, 1fr); gap: 2px; min-width: 650px; }
  .heatmap-label { font-size: 11px; color: #666; display: flex; align-items: center; padding-right: 8px; justify-content: flex-end; }
  .heatmap-hour-label { font-size: 10px; color: #555; text-align: center; padding-bottom: 4px; }
  .heatmap-cell { aspect-ratio: 1; border-radius: 3px; min-height: 16px; transition: all 0.15s; cursor: default; position: relative; }
  .heatmap-cell:hover { transform: scale(1.3); z-index: 2; outline: 1px solid #f0c040; }
  .heatmap-cell[title]:hover::after { content: attr(title); position: absolute; bottom: 120%; left: 50%; transform: translateX(-50%); background: #222; color: #eee; padding: 3px 8px; border-radius: 4px; font-size: 10px; white-space: nowrap; z-index: 10; pointer-events: none; }
  .heatmap-legend { display: flex; align-items: center; gap: 6px; margin-top: 10px; font-size: 11px; color: #666; }
  .heatmap-legend-cell { width: 14px; height: 14px; border-radius: 3px; }

  /* === Health Checks === */
  .health-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
  .health-item { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 10px; padding: 14px 16px; display: flex; align-items: center; gap: 12px; transition: border-color 0.3s; box-shadow: var(--card-shadow); }
  .health-item.healthy { border-left: 3px solid #16a34a; }
  .health-item.warning { border-left: 3px solid #d97706; }
  .health-item.critical { border-left: 3px solid #dc2626; }
  .health-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .health-dot.green { background: #16a34a; box-shadow: 0 0 8px rgba(22,163,74,0.5); }
  .health-dot.yellow { background: #d97706; box-shadow: 0 0 8px rgba(217,119,6,0.5); }
  .health-dot.red { background: #dc2626; box-shadow: 0 0 8px rgba(220,38,38,0.5); }
  .health-info { flex: 1; }
  .health-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
  .health-detail { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

  /* === Usage/Token Charts === */
  .usage-chart { display: flex; align-items: flex-end; gap: 6px; height: 200px; padding: 16px 8px 32px; position: relative; }
  .usage-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; position: relative; }
  .usage-bar { width: 100%; min-width: 20px; max-width: 48px; border-radius: 6px 6px 0 0; background: linear-gradient(180deg, var(--bg-accent), #1d4ed8); transition: height 0.4s ease; position: relative; cursor: default; }
  .usage-bar:hover { filter: brightness(1.25); }
  .usage-bar-label { font-size: 9px; color: var(--text-muted); margin-top: 6px; text-align: center; white-space: nowrap; }
  .usage-bar-value { font-size: 9px; color: var(--text-tertiary); text-align: center; position: absolute; top: -16px; width: 100%; white-space: nowrap; }
  .usage-grid-line { position: absolute; left: 0; right: 0; border-top: 1px dashed var(--border-secondary); }
  .usage-grid-label { position: absolute; right: 100%; padding-right: 8px; font-size: 10px; color: var(--text-muted); white-space: nowrap; }
  .usage-table { width: 100%; border-collapse: collapse; }
  .usage-table th { text-align: left; font-size: 12px; color: var(--text-muted); padding: 8px 12px; border-bottom: 1px solid var(--border-primary); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  .usage-table td { padding: 8px 12px; font-size: 13px; color: var(--text-secondary); border-bottom: 1px solid var(--border-secondary); }
  .usage-table tr:last-child td { border-bottom: none; font-weight: 700; color: var(--text-accent); }
  
  /* === Cost Warnings === */
  .cost-warning { padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; display: flex; align-items: center; gap: 10px; font-size: 13px; }
  /* === Markdown Rendered Content === */
  .md-rendered h1,.md-rendered h2,.md-rendered h3,.md-rendered h4 { margin: 8px 0 4px; color: var(--text-primary); }
  .md-rendered h1 { font-size: 18px; } .md-rendered h2 { font-size: 16px; } .md-rendered h3 { font-size: 14px; }
  .md-rendered p { margin: 4px 0; }
  .md-rendered code { background: var(--bg-secondary); padding: 1px 5px; border-radius: 4px; font-size: 12px; font-family: 'SF Mono','JetBrains Mono',monospace; }
  .md-rendered pre { background: var(--bg-secondary); border: 1px solid var(--border-primary); border-radius: 8px; padding: 10px 14px; overflow-x: auto; margin: 6px 0; }
  .md-rendered pre code { background: none; padding: 0; }
  .md-rendered ul,.md-rendered ol { padding-left: 20px; margin: 4px 0; }
  .md-rendered blockquote { border-left: 3px solid var(--text-accent); padding-left: 12px; margin: 6px 0; color: var(--text-secondary); }
  .md-rendered strong { color: var(--text-primary); }
  .md-rendered a { color: var(--text-link); }
  .md-rendered table { border-collapse: collapse; margin: 6px 0; }
  .md-rendered th,.md-rendered td { border: 1px solid var(--border-primary); padding: 4px 8px; font-size: 12px; }

  .cost-warning.error { background: var(--bg-error); border: 1px solid var(--text-error); color: var(--text-error); }
  .cost-warning.warning { background: var(--bg-warning); border: 1px solid var(--text-warning); color: var(--text-warning); }
  .cost-warning-icon { font-size: 16px; }
  .cost-warning-message { flex: 1; }

  /* === Transcript Viewer === */
  .transcript-item { padding: 12px 16px; border-bottom: 1px solid var(--border-secondary); cursor: pointer; transition: background 0.15s; display: flex; justify-content: space-between; align-items: center; }
  .transcript-item:hover { background: var(--bg-hover); }
  .transcript-item:last-child { border-bottom: none; }
  .transcript-name { font-weight: 600; font-size: 14px; color: var(--text-link); }
  .transcript-meta-row { font-size: 12px; color: var(--text-muted); margin-top: 4px; display: flex; gap: 12px; flex-wrap: wrap; }
  .transcript-viewer-meta { background: var(--bg-secondary); border: 1px solid var(--border-primary); border-radius: 12px; padding: 16px; margin-bottom: 16px; }
  .transcript-viewer-meta .stat-row { padding: 6px 0; }
  .chat-messages { display: flex; flex-direction: column; gap: 10px; padding: 8px 0; }
  .chat-msg { max-width: 85%; padding: 12px 16px; border-radius: 16px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .chat-msg.user { background: #1a2a4a; border: 1px solid #2a4a7a; color: #c0d8ff; align-self: flex-end; border-bottom-right-radius: 4px; }
  .chat-msg.assistant { background: #1a3a2a; border: 1px solid #2a5a3a; color: #c0ffc0; align-self: flex-start; border-bottom-left-radius: 4px; }
  .chat-msg.system { background: #2a2a1a; border: 1px solid #4a4a2a; color: #f0e0a0; align-self: center; font-size: 12px; font-style: italic; max-width: 90%; }
  .chat-msg.tool { background: #1a1a24; border: 1px solid #2a2a3a; color: #a0a0b0; align-self: flex-start; font-family: 'SF Mono', monospace; font-size: 12px; border-left: 3px solid #555; }
  .chat-role { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; opacity: 0.7; }
  .chat-ts { font-size: 10px; color: #555; margin-top: 6px; text-align: right; }
  .chat-expand { display: inline-block; color: #f0c040; font-size: 11px; cursor: pointer; margin-top: 4px; }
  .chat-expand:hover { text-decoration: underline; }
  .chat-content-truncated { max-height: 200px; overflow: hidden; position: relative; }
  .chat-content-truncated::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 40px; background: linear-gradient(transparent, rgba(26,42,74,0.9)); pointer-events: none; }
  .chat-msg.assistant .chat-content-truncated::after { background: linear-gradient(transparent, rgba(26,58,42,0.9)); }
  .chat-msg.tool .chat-content-truncated::after { background: linear-gradient(transparent, rgba(26,26,36,0.9)); }

  /* === Mini Dashboard Widgets === */
  .tool-spark { font-size: 11px; color: var(--text-muted); padding: 3px 8px; background: var(--bg-secondary); border-radius: 6px; border: 1px solid var(--border-secondary); }
  .tool-spark span { color: var(--text-accent); font-weight: 600; }
  .card:hover { transform: translateY(-1px); box-shadow: var(--card-shadow-hover); }
  .card[onclick] { cursor: pointer; }

  /* === Sub-Agent Worker Bees === */
  .subagent-item { display: flex; align-items: center; gap: 6px; padding: 2px 0; font-size: 10px; }
  .subagent-status { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
  .subagent-status.active { background: #16a34a; box-shadow: 0 0 4px rgba(22,163,74,0.5); }
  .subagent-status.idle { background: #d97706; box-shadow: 0 0 4px rgba(217,119,6,0.5); }
  .subagent-status.stale { background: #dc2626; box-shadow: 0 0 4px rgba(220,38,38,0.5); }
  .subagent-name { font-weight: 600; color: var(--text-secondary); }
  .subagent-task { color: var(--text-muted); font-size: 9px; }
  .subagent-runtime { color: var(--text-faint); font-size: 9px; margin-left: auto; }

  /* === Sub-Agent Detailed View === */
  .subagent-row { padding: 12px 16px; border-bottom: 1px solid var(--border-secondary); display: flex; align-items: center; gap: 12px; }
  .subagent-row:last-child { border-bottom: none; }
  .subagent-row:hover { background: var(--bg-hover); }
  .subagent-indicator { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
  .subagent-indicator.active { background: #16a34a; box-shadow: 0 0 8px rgba(22,163,74,0.6); animation: pulse 2s infinite; }
  .subagent-indicator.idle { background: #d97706; box-shadow: 0 0 8px rgba(217,119,6,0.6); }
  .subagent-indicator.stale { background: #dc2626; box-shadow: 0 0 8px rgba(220,38,38,0.6); opacity: 0.7; }
  .subagent-info { flex: 1; }
  .subagent-header { display: flex; justify-content: between; align-items: center; margin-bottom: 4px; }
  .subagent-id { font-weight: 600; font-size: 14px; color: var(--text-primary); }
  .subagent-runtime-badge { background: var(--bg-accent); color: var(--bg-primary); padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .subagent-meta { font-size: 12px; color: var(--text-muted); display: flex; gap: 16px; flex-wrap: wrap; }
  .subagent-meta span { display: flex; align-items: center; gap: 4px; }
  .subagent-description { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }

  /* === Active Tasks Cards === */
  .task-card { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 12px; padding: 16px; box-shadow: var(--card-shadow); position: relative; overflow: hidden; }
  .task-card.running { border-left: 4px solid #16a34a; }
  .task-card.complete { border-left: 4px solid #2563eb; opacity: 0.7; }
  .task-card.failed { border-left: 4px solid #dc2626; }
  .task-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
  .task-card-name { font-weight: 700; font-size: 14px; color: var(--text-primary); line-height: 1.3; }
  .task-card-badge { padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; white-space: nowrap; }
  .task-card-badge.running { background: #dcfce7; color: #166534; }
  .task-card-badge.complete { background: #dbeafe; color: #1e40af; }
  .task-card-badge.failed { background: #fef2f2; color: #991b1b; }
  [data-theme="dark"] .task-card-badge.running { background: #14532d; color: #86efac; }
  [data-theme="dark"] .task-card-badge.complete { background: #1e3a5f; color: #93c5fd; }
  [data-theme="dark"] .task-card-badge.failed { background: #450a0a; color: #fca5a5; }
  .task-card-duration { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
  .task-card-action { font-size: 12px; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; background: var(--bg-secondary); padding: 6px 10px; border-radius: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .task-card-pulse { position: absolute; top: 12px; right: 12px; width: 10px; height: 10px; border-radius: 50%; background: #22c55e; }
  .task-card-pulse.active { animation: taskPulse 1.5s ease-in-out infinite; }
  @keyframes taskPulse { 0%,100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.4); } 50% { box-shadow: 0 0 0 8px rgba(34,197,94,0); } }

  /* === Enhanced Active Tasks Panel === */
  .tasks-panel-scroll { max-height: 70vh; overflow-y: auto; overflow-x: hidden; scrollbar-width: thin; scrollbar-color: var(--border-primary) transparent; }
  .tasks-panel-scroll::-webkit-scrollbar { width: 6px; }
  .tasks-panel-scroll::-webkit-scrollbar-track { background: transparent; }
  .tasks-panel-scroll::-webkit-scrollbar-thumb { background: var(--border-primary); border-radius: 3px; }
  .task-group-header { font-size: 13px; font-weight: 700; color: var(--text-secondary); padding: 8px 4px 6px; margin-top: 4px; letter-spacing: 0.3px; }
  .task-group-header:first-child { margin-top: 0; }
  @keyframes idleBreathe { 0%,100% { opacity: 0.5; transform: scale(1); } 50% { opacity: 1; transform: scale(1.05); } }
  .tasks-empty-icon { animation: idleBreathe 3s ease-in-out infinite; display: inline-block; }
  @keyframes statusPulseGreen { 0%,100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.5); } 50% { box-shadow: 0 0 0 6px rgba(34,197,94,0); } }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
  .status-dot.running { background: #22c55e; animation: statusPulseGreen 1.5s ease-in-out infinite; }
  .status-dot.complete { background: #3b82f6; }
  .status-dot.failed { background: #ef4444; }

  /* === Zoom Wrapper === */
  .zoom-wrapper { transform-origin: top left; transition: transform 0.3s ease; }

  /* === Split-Screen Overview === */
  .overview-split { display: grid; grid-template-columns: 60fr 1px 40fr; gap: 0; margin-bottom: 0; height: calc(100vh - 90px); }
  .overview-flow-pane { position: relative; border: 1px solid var(--border-primary); border-radius: 8px 0 0 8px; overflow: hidden; background: var(--bg-secondary); padding: 4px; }
  .overview-flow-pane .flow-container { height: 100%; }
  .overview-flow-pane svg { width: 100%; height: 100%; min-width: 0 !important; }
  .overview-divider { background: var(--border-primary); width: 1px; }
  .overview-tasks-pane { overflow-y: auto; border: 1px solid var(--border-primary); border-left: none; border-radius: 0 8px 8px 0; padding: 10px 12px; }
  /* Scanline overlay */
  .scanline-overlay { pointer-events: none; position: absolute; inset: 0; z-index: 2; background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,65,0.015) 2px, rgba(0,255,65,0.015) 4px); }
  .grid-overlay { pointer-events: none; position: absolute; inset: 0; z-index: 1; background-image: linear-gradient(var(--border-secondary) 1px, transparent 1px), linear-gradient(90deg, var(--border-secondary) 1px, transparent 1px); background-size: 40px 40px; opacity: 0.3; }
  /* Task cards in overview */
  .ov-task-card { background: var(--bg-tertiary); border: 1px solid var(--border-primary); border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; box-shadow: var(--card-shadow); position: relative; transition: box-shadow 0.2s; }
  .ov-task-card:hover { box-shadow: var(--card-shadow-hover); }
  .ov-task-card.running { border-left: 4px solid #16a34a; }
  .ov-task-card.complete { border-left: 4px solid #2563eb; opacity: 0.75; }
  .ov-task-card.failed { border-left: 4px solid #dc2626; }
  .ov-task-pulse { width: 10px; height: 10px; border-radius: 50%; background: #22c55e; display: inline-block; animation: taskPulse 1.5s ease-in-out infinite; }
  .ov-details { display: none; margin-top: 10px; padding: 10px; background: var(--bg-secondary); border: 1px solid var(--border-secondary); border-radius: 8px; font-family: 'JetBrains Mono', 'SF Mono', monospace; font-size: 11px; line-height: 1.7; color: var(--text-tertiary); }
  .ov-details.open { display: block; }
  .ov-toggle-btn { background: none; border: 1px solid var(--border-primary); border-radius: 6px; padding: 3px 10px; font-size: 11px; color: var(--text-tertiary); cursor: pointer; transition: all 0.15s; }
  .ov-toggle-btn:hover { background: var(--bg-hover); color: var(--text-secondary); }

  /* === Task Detail Modal === */
  .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1000; justify-content: center; align-items: center; }
  .modal-overlay.open { display: flex; }
  .modal-card { background: var(--bg-primary); border: 1px solid var(--border-primary); border-radius: 16px; width: 95%; max-width: 900px; max-height: 80vh; display: flex; flex-direction: column; box-shadow: 0 25px 50px rgba(0,0,0,0.25); }
  .modal-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border-primary); flex-shrink: 0; }
  .modal-header-left { flex: 1; min-width: 0; }
  .modal-title { font-size: 16px; font-weight: 700; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .modal-session-key { font-size: 11px; color: var(--text-muted); font-family: monospace; margin-top: 2px; }
  .modal-header-right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
  .modal-auto-refresh { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-tertiary); cursor: pointer; }
  .modal-auto-refresh input { cursor: pointer; }
  .modal-close { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 8px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 18px; color: var(--text-tertiary); transition: all 0.15s; }
  .modal-close:hover { background: var(--bg-error); color: var(--text-error); }
  .modal-tabs { display: flex; gap: 0; border-bottom: 1px solid var(--border-primary); padding: 0 20px; flex-shrink: 0; }
  .modal-tab { padding: 10px 18px; font-size: 13px; font-weight: 600; color: var(--text-muted); cursor: pointer; border-bottom: 2px solid transparent; transition: all 0.15s; }
  .modal-tab:hover { color: var(--text-secondary); }
  .modal-tab.active { color: var(--text-accent); border-bottom-color: var(--text-accent); }
  .modal-content { flex: 1; overflow-y: auto; padding: 20px; -webkit-overflow-scrolling: touch; }
  .modal-footer { border-top: 1px solid var(--border-primary); padding: 10px 20px; display: flex; gap: 16px; font-size: 12px; color: var(--text-muted); flex-shrink: 0; }
  /* Modal event items */
  .evt-item { border: 1px solid var(--border-secondary); border-radius: 8px; margin-bottom: 8px; overflow: hidden; }
  .evt-header { display: flex; align-items: center; gap: 8px; padding: 10px 14px; cursor: pointer; transition: background 0.15s; }
  .evt-header:hover { background: var(--bg-hover); }
  .evt-icon { font-size: 16px; flex-shrink: 0; }
  .evt-summary { flex: 1; font-size: 13px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .evt-summary strong { color: var(--text-primary); }
  .evt-ts { font-size: 11px; color: var(--text-muted); flex-shrink: 0; font-family: monospace; }
  .evt-body { display: none; padding: 0 14px 12px; font-family: 'JetBrains Mono', 'SF Mono', monospace; font-size: 12px; line-height: 1.6; color: var(--text-tertiary); white-space: pre-wrap; word-break: break-word; max-height: 400px; overflow-y: auto; }
  .evt-body.open { display: block; }
  .evt-item.type-agent { border-left: 3px solid #3b82f6; }
  .evt-item.type-exec { border-left: 3px solid #16a34a; }
  .evt-item.type-read { border-left: 3px solid #8b5cf6; }
  .evt-item.type-result { border-left: 3px solid #ea580c; }
  .evt-item.type-thinking { border-left: 3px solid #6b7280; }
  .evt-item.type-user { border-left: 3px solid #7c3aed; }
  /* === Component Detail Modal === */
  .comp-modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1100; justify-content: center; align-items: center; }
  .comp-modal-overlay.open { display: flex; }
  .comp-modal-card { background: var(--bg-primary); border: 1px solid var(--border-primary); border-radius: 16px; width: 90%; max-width: 560px; display: flex; flex-direction: column; box-shadow: 0 25px 50px rgba(0,0,0,0.25); max-height: 90vh; }
  .comp-modal-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border-primary); }
  .comp-modal-title { font-size: 18px; font-weight: 700; color: var(--text-primary); }
  .comp-modal-close { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 8px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 18px; color: var(--text-tertiary); transition: all 0.15s; }
  .comp-modal-close:hover { background: var(--bg-error); color: var(--text-error); }
  
  /* Time Travel Controls */
  .time-travel-bar { display: none; padding: 12px 20px; border-bottom: 1px solid var(--border-primary); background: var(--bg-secondary); }
  .time-travel-bar.active { display: block; }
  .time-travel-controls { display: flex; align-items: center; gap: 12px; }
  .time-travel-toggle { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 6px; padding: 4px 8px; color: var(--text-tertiary); cursor: pointer; font-size: 12px; transition: all 0.15s; }
  .time-travel-toggle:hover { background: var(--button-hover); }
  .time-travel-toggle.active { background: var(--bg-accent); color: white; }
  .time-scrubber { flex: 1; display: flex; align-items: center; gap: 8px; }
  .time-slider { flex: 1; height: 4px; background: var(--border-primary); border-radius: 2px; cursor: pointer; position: relative; }
  .time-slider-thumb { width: 16px; height: 16px; background: var(--bg-accent); border-radius: 50%; position: absolute; top: -6px; margin-left: -8px; box-shadow: var(--card-shadow); transition: all 0.15s; }
  .time-slider-thumb:hover { transform: scale(1.2); }
  .time-display { font-size: 12px; color: var(--text-secondary); font-weight: 600; min-width: 120px; }
  .time-nav-btn { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 4px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 12px; color: var(--text-tertiary); }
  .time-nav-btn:hover { background: var(--button-hover); }
  .time-nav-btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .comp-modal-body { padding: 24px 20px; font-size: 14px; color: var(--text-secondary); line-height: 1.6; max-height: 70vh; overflow-y: auto; }

  /* Telegram Chat Bubbles */
  .tg-stats { display: flex; gap: 16px; padding: 10px 14px; background: var(--bg-secondary); border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  .tg-stats .in { color: #3b82f6; } .tg-stats .out { color: #22c55e; }
  .tg-chat { display: flex; flex-direction: column; gap: 8px; }
  .tg-bubble { max-width: 85%; padding: 10px 14px; border-radius: 16px; font-size: 13px; line-height: 1.5; word-wrap: break-word; position: relative; }
  .tg-bubble.in { background: #1e3a5f; border: 1px solid #2a5a8a; color: #c0d8ff; align-self: flex-start; border-bottom-left-radius: 4px; }
  .tg-bubble.out { background: #1a3a2a; border: 1px solid #2a5a3a; color: #c0ffc0; align-self: flex-end; border-bottom-right-radius: 4px; }
  [data-theme="light"] .tg-bubble.in { background: #dbeafe; border-color: #93c5fd; color: #1e3a5f; }
  [data-theme="light"] .tg-bubble.out { background: #dcfce7; border-color: #86efac; color: #14532d; }
  .tg-bubble .tg-sender { font-size: 11px; font-weight: 700; margin-bottom: 2px; opacity: 0.7; }
  .tg-bubble .tg-time { font-size: 10px; color: var(--text-muted); margin-top: 4px; text-align: right; }
  .tg-bubble .tg-text { white-space: pre-wrap; }
  .tg-load-more { text-align: center; padding: 10px; }
  .tg-load-more button { background: var(--button-bg); border: 1px solid var(--border-primary); border-radius: 8px; padding: 6px 20px; color: var(--text-secondary); cursor: pointer; font-size: 13px; }
  .tg-load-more button:hover { background: var(--button-hover); }
  .comp-modal-footer { border-top: 1px solid var(--border-primary); padding: 10px 20px; font-size: 11px; color: var(--text-muted); }
  /* === Compact Stats Footer Bar === */
  .stats-footer { display: flex; gap: 0; border: 1px solid var(--border-primary); border-radius: 8px; margin-top: 6px; background: var(--bg-tertiary); overflow: hidden; }
  .stats-footer-item { flex: 1; padding: 6px 12px; display: flex; align-items: center; gap: 8px; border-right: 1px solid var(--border-primary); cursor: pointer; transition: background 0.15s; }
  .stats-footer-item:last-child { border-right: none; }
  .stats-footer-item:hover { background: var(--bg-hover); }
  .stats-footer-icon { font-size: 14px; }
  .stats-footer-label { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
  .stats-footer-value { font-size: 14px; font-weight: 700; color: var(--text-primary); }
  .stats-footer-sub { font-size: 10px; color: var(--text-faint); }
  @media (max-width: 1024px) {
    .stats-footer { flex-wrap: wrap; }
    .stats-footer-item { flex: 1 1 45%; min-width: 0; }
  }

  /* Narrative view */
  .narrative-item { padding: 10px 0; border-bottom: 1px solid var(--border-secondary); font-size: 13px; line-height: 1.6; color: var(--text-secondary); }
  .narrative-item:last-child { border-bottom: none; }
  .narrative-item .narr-icon { margin-right: 8px; }
  .narrative-item code { background: var(--bg-secondary); padding: 1px 6px; border-radius: 4px; font-family: 'JetBrains Mono', monospace; font-size: 12px; }
  /* Summary view */
  .summary-section { margin-bottom: 16px; }
  .summary-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 6px; }
  .summary-text { font-size: 14px; color: var(--text-secondary); line-height: 1.6; white-space: pre-wrap; }

  @media (max-width: 1024px) {
    .overview-split { grid-template-columns: 1fr; height: auto; }
    .overview-flow-pane { height: 40vh; min-height: 250px; border-radius: 8px 8px 0 0; }
    .overview-divider { width: auto; height: 1px; }
    .overview-tasks-pane { height: 60vh; border-radius: 0 0 8px 8px; border-left: 1px solid var(--border-primary); border-top: none; }
  }

  @media (max-width: 768px) {
    .nav { padding: 10px 12px; gap: 8px; }
    .nav h1 { font-size: 16px; }
    .nav-tab { padding: 6px 12px; font-size: 12px; }
    .page { padding: 12px; }
    .grid { grid-template-columns: 1fr; gap: 12px; }
    .card-value { font-size: 22px; }
    .flow-stats { gap: 8px; }
    .flow-stat { min-width: 70px; padding: 6px 10px; }
    .flow-stat-value { font-size: 16px; }
    #flow-svg { min-width: 0; }
    .heatmap-grid { min-width: 500px; }
    .chat-msg { max-width: 95%; }
    .usage-chart { height: 150px; }
    
    /* Enhanced Flow mobile optimizations */
    .flow-container { 
      padding-bottom: 20px; 
      overflow: visible; 
    }
    #flow-svg text { font-size: 11px !important; }
    .flow-label { font-size: 7px !important; }
    .flow-node rect { stroke-width: 1 !important; }
    .flow-node.active rect { stroke-width: 1.5 !important; }
    .brain-group { animation-duration: 1.8s; } /* Faster on mobile */
    
    /* Mobile zoom controls */
    .zoom-controls { margin-left: 8px; gap: 2px; }
    .zoom-btn { width: 24px; height: 24px; font-size: 14px; }
    .zoom-level { min-width: 32px; font-size: 10px; }
  }
</style>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body data-theme="light" class="booting"><script>var t=localStorage.getItem('openclaw-theme');if(t==='dark')document.body.setAttribute('data-theme','dark');</script>
<!-- Login overlay -->
<div id="login-overlay" style="display:none;position:fixed;inset:0;z-index:99999;background:var(--bg-primary,#0f172a);align-items:center;justify-content:center;flex-direction:column;">
  <div style="background:var(--card-bg,#1e293b);border-radius:16px;padding:40px;max-width:400px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,0.4);text-align:center;">
    <div style="font-size:48px;margin-bottom:16px;">🦞</div>
    <h2 style="color:#e2e8f0;margin:0 0 8px;">ClawMetry</h2>
    <p style="color:#94a3b8;margin:0 0 24px;font-size:14px;">Enter your OpenClaw Gateway Token</p>
    <input id="login-token" type="password" placeholder="Gateway token..." style="width:100%;box-sizing:border-box;padding:12px 16px;border-radius:8px;border:1px solid #334155;background:#0f172a;color:#e2e8f0;font-size:15px;margin-bottom:16px;outline:none;" onkeydown="if(event.key==='Enter')clawmetryLogin()">
    <button onclick="clawmetryLogin()" style="width:100%;padding:12px;border-radius:8px;border:none;background:#3b82f6;color:#fff;font-size:15px;font-weight:600;cursor:pointer;">Login</button>
    <p id="login-error" style="color:#f87171;margin:12px 0 0;font-size:13px;display:none;">Invalid token</p>
  </div>
</div>
<script>
(function(){
  var stored = localStorage.getItem('clawmetry-token');
  fetch('/api/auth/check' + (stored ? '?token=' + encodeURIComponent(stored) : ''))
    .then(function(r){return r.json()})
    .then(function(d){
      if(d.needsSetup){
        // No gateway token configured — show mandatory gateway setup wizard
        document.getElementById('login-overlay').style.display='none';
        var overlay=document.getElementById('gw-setup-overlay');
        overlay.dataset.mandatory='true';
        document.getElementById('gw-setup-close').style.display='none';
        overlay.style.display='flex';
        return;
      }
      if(!d.authRequired){
        document.getElementById('login-overlay').style.display='none';
        return;
      }
      if(d.valid){
        document.getElementById('login-overlay').style.display='none';
        var lb=document.getElementById('logout-btn');if(lb)lb.style.display='';
        return;
      }
      document.getElementById('login-overlay').style.display='flex';
    })
    .catch(function(){document.getElementById('login-overlay').style.display='none';});
})();
function clawmetryLogin(){
  var tok=document.getElementById('login-token').value.trim();
  if(!tok)return;
  fetch('/api/auth/check?token='+encodeURIComponent(tok))
    .then(function(r){return r.json()})
    .then(function(d){
      if(d.valid){
        localStorage.setItem('clawmetry-token',tok);
        document.getElementById('login-overlay').style.display='none';
        var lb=document.getElementById('logout-btn');if(lb)lb.style.display='';
        location.reload();
      } else {
        document.getElementById('login-error').style.display='block';
      }
    });
}
function clawmetryLogout(){
  localStorage.removeItem('clawmetry-token');
  location.reload();
}
// Inject auth header into all fetch calls
(function(){
  var _origFetch=window.fetch;
  window.fetch=function(url,opts){
    var tok=localStorage.getItem('clawmetry-token');
    if(tok && typeof url==='string' && url.startsWith('/api/')){
      opts=opts||{};
      opts.headers=opts.headers||{};
      if(opts.headers instanceof Headers){opts.headers.set('Authorization','Bearer '+tok);}
      else{opts.headers['Authorization']='Bearer '+tok;}
    }
    return _origFetch.call(this,url,opts);
  };
})();
</script>
<div class="boot-overlay" id="boot-overlay">
  <div class="boot-card">
    <div class="boot-spinner"></div>
    <div class="boot-title">Initializing ClawMetry</div>
    <div class="boot-sub" id="boot-sub">Loading model, tasks, system health, and live streams…</div>
    <div class="boot-steps">
      <div class="boot-step loading" id="boot-step-overview"><span class="boot-dot"></span><span>Loading overview + model context</span></div>
      <div class="boot-step" id="boot-step-tasks"><span class="boot-dot"></span><span>Loading active tasks</span></div>
      <div class="boot-step" id="boot-step-health"><span class="boot-dot"></span><span>Loading system health</span></div>
      <div class="boot-step" id="boot-step-streams"><span class="boot-dot"></span><span>Connecting live streams</span></div>
    </div>
  </div>
</div>
<div class="zoom-wrapper" id="zoom-wrapper">
<div class="nav">
  <h1><span>🦞</span> ClawMetry</h1>
  <div class="theme-toggle" onclick="var o=document.getElementById('gw-setup-overlay');o.dataset.mandatory='false';document.getElementById('gw-setup-close').style.display='';o.style.display='flex'" title="Gateway settings" style="cursor:pointer;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></div>
  <div class="theme-toggle" id="theme-toggle-btn" onclick="toggleTheme()" title="Toggle theme"><svg class="icon-moon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></div>
  <div class="theme-toggle" id="logout-btn" onclick="clawmetryLogout()" title="Logout" style="display:none;cursor:pointer;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg></div>
  <div class="zoom-controls">
    <button class="zoom-btn" onclick="zoomOut()" title="Zoom out (Ctrl/Cmd + -)">−</button>
    <span class="zoom-level" id="zoom-level" title="Current zoom level. Ctrl/Cmd + 0 to reset">100%</span>
    <button class="zoom-btn" onclick="zoomIn()" title="Zoom in (Ctrl/Cmd + +)">+</button>
  </div>
  <div class="nav-tabs">
    <div class="nav-tab" onclick="switchTab('flow')">Flow</div>
    <div class="nav-tab active" onclick="switchTab('overview')">Overview</div>
    <div class="nav-tab" onclick="switchTab('crons')">Crons</div>
    <div class="nav-tab" onclick="switchTab('memory')">Memory</div>
  </div>
</div>

<!-- OVERVIEW (Split-Screen Hacker Dashboard) -->
<div class="page active" id="page-overview">
  <div class="refresh-bar" style="margin-bottom:6px;">
    <button class="refresh-btn" onclick="loadAll()" style="padding:4px 12px;font-size:12px;">↻</button>
    <span class="pulse"></span>
    <span class="live-badge">LIVE</span>
    <span class="refresh-time" id="refresh-time" style="font-size:11px;">Loading...</span>
  </div>

  <!-- Split Screen: Flow Left | Tasks Right -->
  <div class="overview-split">
    <!-- LEFT: Flow Visualization -->
    <div class="overview-flow-pane">
      <div class="grid-overlay"></div>
      <div class="scanline-overlay"></div>
      <div class="flow-container" id="overview-flow-container">
        <!-- Flow SVG cloned here by JS -->
        <div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);font-size:13px;">Loading flow...</div>
      </div>
    </div>

    <!-- DIVIDER -->
    <div class="overview-divider"></div>

    <!-- RIGHT: Active Tasks Panel -->
    <div class="overview-tasks-pane">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
        <div style="display:flex;align-items:center;gap:8px;">
          <span style="font-size:15px;font-weight:700;color:var(--text-primary);">🐝 Active Tasks</span>
          <span id="overview-tasks-count-badge" style="font-size:11px;color:var(--text-muted);"></span>
        </div>
        <span style="font-size:10px;color:var(--text-faint);letter-spacing:0.5px;">⟳ 10s</span>
      </div>
      <div class="tasks-panel-scroll" id="overview-tasks-list">
        <div style="text-align:center;padding:32px;color:var(--text-muted);">
          <div style="font-size:28px;margin-bottom:8px;" class="tasks-empty-icon">🐝</div>
          <div style="font-size:13px;">Loading tasks...</div>
        </div>
      </div>
      <!-- System Health Panel (inside tasks pane) -->
      <div id="system-health-panel" style="background:var(--bg-secondary);border:1px solid var(--border-primary);border-radius:12px;padding:16px;margin-top:14px;box-shadow:var(--card-shadow);">
        <div style="font-size:14px;font-weight:700;color:var(--text-primary);margin-bottom:12px;">🏥 System Health</div>
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Services</div>
        <div id="sh-services" style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;"></div>
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Disk Usage</div>
        <div id="sh-disks" style="margin-bottom:14px;"></div>
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Cron Jobs</div>
        <div id="sh-crons" style="margin-bottom:14px;"></div>
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Sub-Agents (24h)</div>
        <div id="sh-subagents" style="margin-bottom:14px;"></div>
        <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);font-weight:600;margin-bottom:6px;">Token Usage</div>
        <div style="padding:12px;background:var(--bg-tertiary);border-radius:8px;text-align:center;color:var(--text-muted);font-size:12px;">📊 Coming soon</div>
      </div>
    </div>
  </div>

  <!-- Compact Stats Footer Bar -->
  <div class="stats-footer">
    <div class="stats-footer-item" onclick="openDetailView('cost')">
      <span class="stats-footer-icon">💰</span>
      <div>
        <div class="stats-footer-label">Spending</div>
        <div class="stats-footer-value" id="cost-today">$0.00</div>
      </div>
      <div style="margin-left:auto;text-align:right;">
        <div class="stats-footer-sub">wk: <span id="cost-week">—</span></div>
        <div class="stats-footer-sub">mo: <span id="cost-month">—</span></div>
      </div>
      <span id="cost-trend" style="display:none;">Today's running total</span>
    </div>
    <div class="stats-footer-item" onclick="openDetailView('models')">
      <span class="stats-footer-icon">🤖</span>
      <div>
        <div class="stats-footer-label">Model</div>
        <div class="stats-footer-value" id="model-primary">—</div>
      </div>
      <div id="model-breakdown" style="display:none;">Loading...</div>
    </div>
    <div class="stats-footer-item" onclick="openDetailView('tokens')">
      <span class="stats-footer-icon">📊</span>
      <div>
        <div class="stats-footer-label">Tokens</div>
        <div class="stats-footer-value" id="token-rate">—</div>
      </div>
      <span class="stats-footer-sub" style="margin-left:auto;">today: <span id="tokens-today" style="color:var(--text-success);font-weight:600;">—</span></span>
    </div>
    <div class="stats-footer-item" onclick="switchTab('sessions')">
      <span class="stats-footer-icon">💬</span>
      <div>
        <div class="stats-footer-label">Sessions</div>
        <div class="stats-footer-value" id="hot-sessions-count">—</div>
      </div>
      <div id="hot-sessions-list" style="display:none;">Loading...</div>
    </div>
  </div>

  <!-- Hidden elements referenced by existing JS -->
  <div style="display:none;">
    <span id="tokens-peak">—</span>
    <span id="subagents-count">—</span>
    <span id="subagents-status">—</span>
    <span id="subagents-preview"></span>
    <span id="tools-active">—</span>
    <span id="tools-recent">—</span>
    <div id="tools-sparklines"><div class="tool-spark"><span>—</span></div><div class="tool-spark"><span>—</span></div><div class="tool-spark"><span>—</span></div></div>
    <div id="active-tasks-grid"></div>
    <div id="activity-stream"></div>
  </div>

  <!-- old system health removed, now inside tasks pane -->
</div>

<!-- USAGE -->
<div class="page" id="page-usage">
  <div class="refresh-bar">
    <button class="refresh-btn" onclick="loadUsage()">↻ Refresh</button>
    <button class="refresh-btn" onclick="exportUsageData()" style="margin-left: 8px;">📥 Export CSV</button>
  </div>
  
  <!-- Cost Warnings -->
  <div id="cost-warnings" style="display:none; margin-bottom: 16px;"></div>
  
  <!-- Main Usage Stats -->
  <div class="grid">
    <div class="card">
      <div class="card-title"><span class="icon">📊</span> Today</div>
      <div class="card-value" id="usage-today">—</div>
      <div class="card-sub" id="usage-today-cost"></div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">📅</span> This Week</div>
      <div class="card-value" id="usage-week">—</div>
      <div class="card-sub" id="usage-week-cost"></div>
    </div>
    <div class="card">
      <div class="card-title"><span class="icon">📆</span> This Month</div>
      <div class="card-value" id="usage-month">—</div>
      <div class="card-sub" id="usage-month-cost"></div>
    </div>
    <div class="card" id="trend-card" style="display:none;">
      <div class="card-title"><span class="icon">📈</span> Trend</div>
      <div class="card-value" id="trend-direction">—</div>
      <div class="card-sub" id="trend-prediction"></div>
    </div>
  </div>
  <div class="section-title">📊 Token Usage (14 days)</div>
  <div class="card">
    <div class="usage-chart" id="usage-chart">Loading...</div>
  </div>
  <div class="section-title">💰 Cost Breakdown</div>
  <div class="card"><table class="usage-table" id="usage-cost-table"><tbody><tr><td colspan="3" style="color:#666;">Loading...</td></tr></tbody></table></div>
  <div id="otel-extra-sections" style="display:none;">
    <div class="grid" style="margin-top:16px;">
      <div class="card">
        <div class="card-title"><span class="icon">⏱️</span> Avg Run Duration</div>
        <div class="card-value" id="usage-avg-run">—</div>
        <div class="card-sub">from OTLP openclaw.run.duration_ms</div>
      </div>
      <div class="card">
        <div class="card-title"><span class="icon">💬</span> Messages Processed</div>
        <div class="card-value" id="usage-msg-count">—</div>
        <div class="card-sub">from OTLP openclaw.message.processed</div>
      </div>
    </div>
    <div class="section-title">🤖 Model Breakdown</div>
    <div class="card"><table class="usage-table" id="usage-model-table"><tbody><tr><td colspan="2" style="color:#666;">No model data</td></tr></tbody></table></div>
    <div style="margin-top:12px;padding:8px 12px;background:#1a3a2a;border:1px solid #2a5a3a;border-radius:8px;font-size:12px;color:#60ff80;">📡 Data source: OpenTelemetry OTLP - real-time metrics from OpenClaw</div>
  </div>
</div>

<!-- CRONS -->
<div class="page" id="page-crons">
  <div class="refresh-bar"><button class="refresh-btn" onclick="loadCrons()">↻ Refresh</button></div>
  <div class="card" id="crons-list">Loading...</div>
</div>

<!-- MEMORY -->
<div class="page" id="page-memory">
  <div class="refresh-bar">
    <button class="refresh-btn" onclick="loadMemory()">↻ Refresh</button>
  </div>
  <div class="card" id="memory-list">Loading...</div>
  <div class="file-viewer" id="file-viewer">
    <div class="file-viewer-header">
      <span class="file-viewer-title" id="file-viewer-title"></span>
      <button class="file-viewer-close" onclick="closeFileViewer()">✕ Close</button>
    </div>
    <div class="file-viewer-content" id="file-viewer-content"></div>
  </div>
</div>

<!-- TRANSCRIPTS -->
<div class="page" id="page-transcripts">
  <div class="refresh-bar">
    <button class="refresh-btn" onclick="loadTranscripts()">↻ Refresh</button>
    <button class="refresh-btn" id="transcript-back-btn" style="display:none" onclick="showTranscriptList()">← Back to list</button>
  </div>
  <div class="card" id="transcript-list">Loading...</div>
  <div id="transcript-viewer" style="display:none">
    <div class="transcript-viewer-meta" id="transcript-meta"></div>
    <div class="chat-messages" id="transcript-messages"></div>
  </div>
</div>

<!-- FLOW -->
<div class="page" id="page-flow">
  <div class="flow-stats">
    <div class="flow-stat"><span class="flow-stat-label">Messages / min</span><span class="flow-stat-value" id="flow-msg-rate">0</span></div>
    <div class="flow-stat"><span class="flow-stat-label">Actions Taken</span><span class="flow-stat-value" id="flow-event-count">0</span></div>
    <div class="flow-stat"><span class="flow-stat-label">Active Tools</span><span class="flow-stat-value" id="flow-active-tools">&mdash;</span></div>
    <div class="flow-stat"><span class="flow-stat-label">Tokens Used</span><span class="flow-stat-value" id="flow-tokens">&mdash;</span></div>
  </div>
  <div class="flow-container">
    <svg id="flow-svg" viewBox="0 0 980 550" preserveAspectRatio="xMidYMid meet">
      <defs>
        <pattern id="flow-grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="var(--border-secondary)" stroke-width="0.5"/>
        </pattern>
        <filter id="dropShadow" x="-10%" y="-10%" width="130%" height="130%">
          <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="rgba(0,0,0,0.25)" flood-opacity="0.4"/>
        </filter>
        <filter id="dropShadowLight" x="-10%" y="-10%" width="130%" height="130%">
          <feDropShadow dx="0" dy="1" stdDeviation="2" flood-color="rgba(0,0,0,0.15)" flood-opacity="0.3"/>
        </filter>
      </defs>
      <rect width="980" height="550" fill="var(--bg-primary)" rx="12"/>
      <rect width="980" height="550" fill="url(#flow-grid)"/>

      <!-- Human → Channel paths -->
      <path class="flow-path" id="path-human-tg"  d="M 60 56 C 60 70, 65 85, 75 100"/>
      <path class="flow-path" id="path-human-sig" d="M 60 56 C 55 90, 60 140, 75 170"/>
      <path class="flow-path" id="path-human-wa"  d="M 60 56 C 50 110, 55 200, 75 240"/>

      <!-- Channel → Gateway paths -->
      <path class="flow-path" id="path-tg-gw"  d="M 130 120 C 150 120, 160 165, 180 170"/>
      <path class="flow-path" id="path-sig-gw" d="M 130 190 C 150 190, 160 185, 180 183"/>
      <path class="flow-path" id="path-wa-gw"  d="M 130 260 C 150 260, 160 200, 180 195"/>

      <!-- Gateway → Brain -->
      <path class="flow-path" id="path-gw-brain" d="M 290 183 C 305 183, 315 175, 330 175"/>

      <!-- Brain → Tools -->
      <path class="flow-path" id="path-brain-session" d="M 510 155 C 530 130, 545 95, 560 89"/>
      <path class="flow-path" id="path-brain-exec"    d="M 510 160 C 530 150, 545 143, 560 139"/>
      <path class="flow-path" id="path-brain-browser" d="M 510 175 C 530 175, 545 189, 560 189"/>
      <path class="flow-path" id="path-brain-search"  d="M 510 185 C 530 200, 545 230, 560 239"/>
      <path class="flow-path" id="path-brain-cron"    d="M 510 195 C 530 230, 545 275, 560 289"/>
      <path class="flow-path" id="path-brain-tts"     d="M 510 205 C 530 260, 545 325, 560 339"/>
      <path class="flow-path" id="path-brain-memory"  d="M 510 215 C 530 290, 545 370, 560 389"/>

      <!-- Infrastructure paths (dashed) -->
      <path class="flow-path flow-path-infra" id="path-gw-network"    d="M 235 205 C 235 350, 500 400, 590 450"/>
      <path class="flow-path flow-path-infra" id="path-brain-runtime" d="M 380 220 C 300 350, 150 400, 95 450"/>
      <path class="flow-path flow-path-infra" id="path-brain-machine" d="M 420 220 C 380 350, 300 400, 260 450"/>
      <path class="flow-path flow-path-infra" id="path-memory-storage" d="M 615 408 C 550 420, 470 435, 425 450"/>

      <!-- Human Origin -->
      <g class="flow-node flow-node-human" id="node-human">
        <circle cx="60" cy="30" r="22" fill="#7c3aed" stroke="#6a2ec0" stroke-width="2" filter="url(#dropShadow)"/>
        <circle cx="60" cy="24" r="5" fill="#ffffff" opacity="0.6"/>
        <path d="M 50 38 Q 50 45 60 45 Q 70 45 70 38" fill="#ffffff" opacity="0.4"/>
        <text x="60" y="68" style="font-size:13px;fill:#7c3aed;font-weight:800;text-anchor:middle;" id="flow-human-name">You</text>
      </g>

      <!-- Channel Nodes -->
      <g class="flow-node flow-node-channel" id="node-telegram">
        <rect x="20" y="100" width="110" height="40" rx="10" ry="10" fill="#2196F3" stroke="#1565C0" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="125" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">📱 TG</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-signal">
        <rect x="20" y="170" width="110" height="40" rx="10" ry="10" fill="#2E8B7A" stroke="#1B6B5A" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="195" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">📡 Signal</text>
      </g>
      <g class="flow-node flow-node-channel" id="node-whatsapp">
        <rect x="20" y="240" width="110" height="40" rx="10" ry="10" fill="#43A047" stroke="#2E7D32" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="75" y="265" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">💬 WA</text>
      </g>

      <!-- Gateway -->
      <g class="flow-node flow-node-gateway" id="node-gateway">
        <rect x="180" y="160" width="110" height="45" rx="10" ry="10" fill="#37474F" stroke="#263238" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="235" y="188" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">🔀 Gateway</text>
      </g>

      <!-- Brain -->
      <g class="flow-node flow-node-brain brain-group" id="node-brain">
        <rect x="330" y="130" width="180" height="90" rx="12" ry="12" fill="#C62828" stroke="#B71C1C" stroke-width="3" filter="url(#dropShadow)"/>
        <text x="420" y="162" style="font-size:24px;text-anchor:middle;">&#x1F9E0;</text>
        <text x="420" y="186" style="font-size:18px;font-weight:800;fill:#FFD54F;text-anchor:middle;" id="brain-model-label">AI Model</text>
        <text x="420" y="203" style="font-size:10px;fill:#ffccbc;text-anchor:middle;" id="brain-model-text">unknown</text>
        <circle cx="420" cy="214" r="4" fill="#FF8A65">
          <animate attributeName="r" values="3;5;3" dur="1.1s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0.5;1;0.5" dur="1.1s" repeatCount="indefinite"/>
        </circle>
      </g>

      <!-- Tool Nodes -->
      <g class="flow-node flow-node-session" id="node-session">
        <rect x="560" y="70" width="110" height="38" rx="10" ry="10" fill="#1565C0" stroke="#0D47A1" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="94" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">📋 Sessions</text>
        <circle class="tool-indicator" id="ind-session" cx="665" cy="78" r="5" fill="#42A5F5"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-exec">
        <rect x="560" y="120" width="110" height="38" rx="10" ry="10" fill="#E65100" stroke="#BF360C" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="144" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">⚡ Exec</text>
        <circle class="tool-indicator" id="ind-exec" cx="665" cy="128" r="5" fill="#FF6E40"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-browser">
        <rect x="560" y="170" width="110" height="38" rx="10" ry="10" fill="#6A1B9A" stroke="#4A148C" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="194" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">🌐 Web</text>
        <circle class="tool-indicator" id="ind-browser" cx="665" cy="178" r="5" fill="#CE93D8"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-search">
        <rect x="560" y="220" width="110" height="38" rx="10" ry="10" fill="#00695C" stroke="#004D40" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="244" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">&#x1F50D; Search</text>
        <circle class="tool-indicator" id="ind-search" cx="665" cy="228" r="5" fill="#4DB6AC"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-cron">
        <rect x="560" y="270" width="110" height="38" rx="10" ry="10" fill="#546E7A" stroke="#37474F" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="294" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">📅 Cron</text>
        <circle class="tool-indicator" id="ind-cron" cx="665" cy="278" r="5" fill="#90A4AE"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-tts">
        <rect x="560" y="320" width="110" height="38" rx="10" ry="10" fill="#F9A825" stroke="#F57F17" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="344" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">&#x1F5E3;&#xFE0F; TTS</text>
        <circle class="tool-indicator" id="ind-tts" cx="665" cy="328" r="5" fill="#FFF176"/>
      </g>
      <g class="flow-node flow-node-tool" id="node-memory">
        <rect x="560" y="370" width="110" height="38" rx="10" ry="10" fill="#283593" stroke="#1A237E" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="615" y="394" style="font-size:13px;font-weight:700;fill:#ffffff;text-anchor:middle;">&#x1F4BE; Memory</text>
        <circle class="tool-indicator" id="ind-memory" cx="665" cy="378" r="5" fill="#7986CB"/>
      </g>

      <!-- Cost Optimizer -->
      <g class="flow-node flow-node-optimizer" id="node-cost-optimizer">
        <rect x="680" y="370" width="145" height="44" rx="12" ry="12" fill="#2E7D32" stroke="#1B5E20" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="752" y="389" style="font-size:12px;font-weight:700;fill:#ffffff;text-anchor:middle;">
          <tspan x="752" dy="-5">&#x1F4B0; Cost</tspan>
          <tspan x="752" dy="13">Optimizer</tspan>
        </text>
        <circle class="tool-indicator" id="ind-cost-optimizer" cx="817" cy="378" r="5" fill="#66BB6A"/>
      </g>

      <!-- Automation Advisor -->
      <g class="flow-node flow-node-advisor" id="node-automation-advisor">
        <rect x="835" y="370" width="145" height="44" rx="12" ry="12" fill="#7B1FA2" stroke="#4A148C" stroke-width="2" filter="url(#dropShadow)"/>
        <text x="907" y="389" style="font-size:12px;font-weight:700;fill:#ffffff;text-anchor:middle;">
          <tspan x="907" dy="-5">&#x1F9E0; Automation</tspan>
          <tspan x="907" dy="13">Advisor</tspan>
        </text>
        <circle class="tool-indicator" id="ind-automation-advisor" cx="972" cy="378" r="5" fill="#BA68C8"/>
      </g>

      <!-- Infrastructure Layer -->
      <line class="flow-ground" x1="20" y1="440" x2="970" y2="440"/>
      <text class="flow-ground-label" x="400" y="438" style="text-anchor:middle;font-size:10px;">I N F R A S T R U C T U R E</text>

      <g class="flow-node flow-node-infra flow-node-runtime" id="node-runtime">
        <rect x="30" y="450" width="130" height="40" rx="8" ry="8" fill="#455A64" stroke="#37474F" filter="url(#dropShadowLight)"/>
        <text x="95" y="466" style="font-size:13px;fill:#ffffff;font-weight:700;text-anchor:middle;">&#x2699;&#xFE0F; Runtime</text>
        <text class="infra-sub" x="95" y="480" style="fill:#B0BEC5;font-size:8px;text-anchor:middle;" id="infra-runtime-text">Node.js · Linux</text>
      </g>
      <g class="flow-node flow-node-infra flow-node-machine" id="node-machine">
        <rect x="195" y="450" width="130" height="40" rx="8" ry="8" fill="#4E342E" stroke="#3E2723" filter="url(#dropShadowLight)"/>
        <text x="260" y="466" style="font-size:13px;fill:#ffffff;font-weight:700;text-anchor:middle;">&#x1F5A5;&#xFE0F; Machine</text>
        <text class="infra-sub" x="260" y="480" style="fill:#BCAAA4;font-size:8px;text-anchor:middle;" id="infra-machine-text">Host</text>
      </g>
      <g class="flow-node flow-node-infra flow-node-storage" id="node-storage">
        <rect x="360" y="450" width="130" height="40" rx="8" ry="8" fill="#5D4037" stroke="#4E342E" filter="url(#dropShadowLight)"/>
        <text x="425" y="466" style="font-size:13px;fill:#ffffff;font-weight:700;text-anchor:middle;">&#x1F4BF; Storage</text>
        <text class="infra-sub" x="425" y="480" style="fill:#BCAAA4;font-size:8px;text-anchor:middle;" id="infra-storage-text">Disk</text>
      </g>
      <g class="flow-node flow-node-infra flow-node-network" id="node-network">
        <rect x="525" y="450" width="130" height="40" rx="8" ry="8" fill="#004D40" stroke="#00332E" filter="url(#dropShadowLight)"/>
        <text x="590" y="466" style="font-size:13px;fill:#ffffff;font-weight:700;text-anchor:middle;">&#x1F310; Network</text>
        <text class="infra-sub" x="590" y="480" style="fill:#80CBC4;font-size:8px;text-anchor:middle;" id="infra-network-text">LAN</text>
      </g>

      <!-- Legend -->
      <g transform="translate(140, 510)">
        <rect x="0" y="0" width="700" height="28" rx="14" ry="14" fill="var(--bg-tertiary)" stroke="var(--border-primary)" stroke-width="1" opacity="0.9"/>
        <text x="350" y="18" style="font-size:12px;font-weight:600;fill:var(--text-secondary);letter-spacing:1px;text-anchor:middle;">&#x1F4E8; Channels  &#x27A1;&#xFE0F;  🔀 Gateway  &#x27A1;&#xFE0F;  &#x1F9E0; AI Brain  &#x27A1;&#xFE0F;  &#x1F6E0;&#xFE0F; Tools</text>
      </g>

      <!-- Flow direction labels -->
      <text class="flow-label" x="120" y="155" style="font-size:9px;">messages in</text>
      <text class="flow-label" x="300" y="155" style="font-size:9px;">routes to AI</text>
      <text class="flow-label" x="520" y="155" style="font-size:9px;">uses tools</text>
    </svg>
  </div>

  <!-- Live activity feed under the flow diagram -->
  <div style="margin-top:12px;background:var(--bg-secondary,#111128);border:1px solid var(--border-secondary,#2a2a4a);border-radius:10px;padding:12px 16px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
      <span style="font-size:13px;font-weight:600;color:#aaa;">📡 Live Activity Feed</span>
      <span style="font-size:10px;color:#555;" id="flow-feed-count">0 events</span>
    </div>
    <div id="flow-live-feed" style="max-height:120px;overflow-y:auto;font-family:'SF Mono',monospace;font-size:11px;line-height:1.5;color:#777;">
      <div style="color:#555;">Waiting for activity...</div>
    </div>
  </div>
</div>

<script>
function switchTab(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  event.target.classList.add('active');
  if (name === 'overview') loadAll();
  if (name === 'usage') loadUsage();
  if (name === 'crons') loadCrons();
  if (name === 'memory') loadMemory();
  if (name === 'transcripts') loadTranscripts();
  if (name === 'flow') initFlow();
}

function exportUsageData() {
  window.location.href = '/api/usage/export';
}

var _sunSVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
var _moonSVG = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

function toggleTheme() {
  const body = document.body;
  const toggle = document.getElementById('theme-toggle-btn');
  const isLight = !body.hasAttribute('data-theme') || body.getAttribute('data-theme') !== 'dark';
  
  if (isLight) {
    body.setAttribute('data-theme', 'dark');
    toggle.innerHTML = _sunSVG;
    toggle.title = 'Switch to light theme';
    localStorage.setItem('openclaw-theme', 'dark');
  } else {
    body.removeAttribute('data-theme');
    toggle.innerHTML = _moonSVG;
    toggle.title = 'Switch to dark theme';
    localStorage.setItem('openclaw-theme', 'light');
  }
}

function initTheme() {
  const savedTheme = localStorage.getItem('openclaw-theme') || 'light';
  const body = document.body;
  const toggle = document.getElementById('theme-toggle-btn');
  
  if (savedTheme === 'dark') {
    body.setAttribute('data-theme', 'dark');
    if (toggle) { toggle.innerHTML = _sunSVG; toggle.title = 'Switch to light theme'; }
  } else {
    body.removeAttribute('data-theme');
    if (toggle) { toggle.innerHTML = _moonSVG; toggle.title = 'Switch to dark theme'; }
  }
}

// === Zoom Controls ===
let currentZoom = 1.0;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 2.0;
const ZOOM_STEP = 0.1;

function initZoom() {
  const savedZoom = localStorage.getItem('openclaw-zoom');
  if (savedZoom) {
    currentZoom = parseFloat(savedZoom);
  }
  applyZoom();
}

function applyZoom() {
  const wrapper = document.getElementById('zoom-wrapper');
  const levelDisplay = document.getElementById('zoom-level');
  
  if (wrapper) {
    wrapper.style.transform = `scale(${currentZoom})`;
  }
  if (levelDisplay) {
    levelDisplay.textContent = Math.round(currentZoom * 100) + '%';
  }
  
  // Save to localStorage
  localStorage.setItem('openclaw-zoom', currentZoom.toString());
}

function zoomIn() {
  if (currentZoom < MAX_ZOOM) {
    currentZoom = Math.min(MAX_ZOOM, currentZoom + ZOOM_STEP);
    applyZoom();
  }
}

function zoomOut() {
  if (currentZoom > MIN_ZOOM) {
    currentZoom = Math.max(MIN_ZOOM, currentZoom - ZOOM_STEP);
    applyZoom();
  }
}

function resetZoom() {
  currentZoom = 1.0;
  applyZoom();
}

// Keyboard shortcuts for zoom
document.addEventListener('keydown', function(e) {
  if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey) {
    if (e.key === '=' || e.key === '+') {
      e.preventDefault();
      zoomIn();
    } else if (e.key === '-') {
      e.preventDefault();
      zoomOut();
    } else if (e.key === '0') {
      e.preventDefault();
      resetZoom();
    }
  }
});

function timeAgo(ms) {
  if (!ms) return 'never';
  var diff = Date.now() - ms;
  if (diff < 60000) return Math.floor(diff/1000) + 's ago';
  if (diff < 3600000) return Math.floor(diff/60000) + 'm ago';
  if (diff < 86400000) return Math.floor(diff/3600000) + 'h ago';
  return Math.floor(diff/86400000) + 'd ago';
}

function formatTime(ms) {
  if (!ms) return '—';
  return new Date(ms).toLocaleString('en-GB', {hour:'2-digit',minute:'2-digit',day:'numeric',month:'short'});
}

async function fetchJsonWithTimeout(url, timeoutMs) {
  var ctrl = new AbortController();
  var to = setTimeout(function() { ctrl.abort('timeout'); }, timeoutMs);
  try {
    var r = await fetch(url, {signal: ctrl.signal});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return await r.json();
  } finally {
    clearTimeout(to);
  }
}

async function resolvePrimaryModelFallback() {
  try {
    var data = await fetchJsonWithTimeout('/api/component/brain?limit=25', 4000);
    var model = (((data || {}).stats || {}).model || '').trim();
    return model || 'unknown';
  } catch (e) {
    return 'unknown';
  }
}

function applyBrainModelToAll(modelName) {
  if (!modelName) return;
  var modelText = fitFlowLabel(modelName, 20);
  document.querySelectorAll('[id$="brain-model-text"]').forEach(function(el) {
    el.textContent = modelText;
  });
  document.querySelectorAll('[id$="brain-model-label"]').forEach(function(label) {
    var short = modelName.split('/').pop().split('-').slice(0, 2).join(' ');
    if (!short) short = 'AI Model';
    label.textContent = fitFlowLabel(short.charAt(0).toUpperCase() + short.slice(1), 14);
  });
}

function fitFlowLabel(text, maxLen) {
  var s = String(text || '').trim();
  if (!s) return '';
  if (s.length <= maxLen) return s;
  return s.substring(0, Math.max(1, maxLen - 1)) + '…';
}

function setFlowTextAll(idSuffix, text, maxLen) {
  var fitted = fitFlowLabel(text, maxLen);
  document.querySelectorAll('[id$="' + idSuffix + '"]').forEach(function(el) {
    el.textContent = fitted;
  });
}

async function loadAll() {
  try {
    // Render overview quickly; do not block on heavy usage aggregation.
    var overview = await fetchJsonWithTimeout('/api/overview', 3000);

    // Start secondary panels immediately.
    startActiveTasksRefresh();
    loadActivityStream();
    loadHealth();
    loadMCTasks();
    document.getElementById('refresh-time').textContent = 'Updated ' + new Date().toLocaleTimeString();

    if (overview.infra) {
      var i = overview.infra;
      if (i.runtime) setFlowTextAll('infra-runtime-text', i.runtime, 18);
      if (i.machine) setFlowTextAll('infra-machine-text', i.machine, 18);
      if (i.storage) setFlowTextAll('infra-storage-text', i.storage, 16);
      if (i.network) setFlowTextAll('infra-network-text', 'LAN ' + i.network, 18);
      if (i.userName) setFlowTextAll('flow-human-name', i.userName, 10);
    }

    // If overview cannot determine model yet, use brain endpoint fallback immediately.
    if (!overview.model || overview.model === 'unknown') {
      var fallbackModel = await resolvePrimaryModelFallback();
      if (fallbackModel && fallbackModel !== 'unknown') {
        overview.model = fallbackModel;
      }
    }
    if (overview.model && overview.model !== 'unknown') {
      applyBrainModelToAll(overview.model);
    }

    // Usage may be slow on first run; keep trying in background with timeout.
    try {
      var usage = await fetchJsonWithTimeout('/api/usage', 5000);
      loadMiniWidgets(overview, usage);
    } catch (e) {
      // Keep UI responsive with placeholder values until next refresh.
      loadMiniWidgets(overview, {todayCost:0, weekCost:0, monthCost:0, month:0, today:0});
    }
    return true;
  } catch (e) {
    console.error('Initial load failed', e);
    document.getElementById('refresh-time').textContent = 'Load failed - retrying...';
    return false;
  }
}

async function loadMiniWidgets(overview, usage) {
  // 💰 Cost Ticker 
  function fmtCost(c) { return c >= 0.01 ? '$' + c.toFixed(2) : c > 0 ? '<$0.01' : '$0.00'; }
  document.getElementById('cost-today').textContent = fmtCost(usage.todayCost || 0);
  document.getElementById('cost-week').textContent = fmtCost(usage.weekCost || 0);
  document.getElementById('cost-month').textContent = fmtCost(usage.monthCost || 0);
  
  var trend = '';
  if (usage.trend && usage.trend.trend) {
    var trendIcon = usage.trend.trend === 'increasing' ? '📈' : usage.trend.trend === 'decreasing' ? '📉' : '➡️';
    trend = trendIcon + ' ' + usage.trend.trend;
  }
  document.getElementById('cost-trend').textContent = trend || 'Today\'s running total';
  
  // ⚡ Tool Activity (load from logs)
  loadToolActivity();
  
  // 📊 Token Burn Rate
  function fmtTokens(n) { return n >= 1000000 ? (n/1000000).toFixed(1) + 'M' : n >= 1000 ? (n/1000).toFixed(0) + 'K' : String(n); }
  document.getElementById('token-rate').textContent = fmtTokens(usage.month || 0);
  document.getElementById('tokens-today').textContent = fmtTokens(usage.today || 0);
  
  // 🔥 Hot Sessions
  document.getElementById('hot-sessions-count').textContent = overview.sessionCount || 0;
  var hotHtml = '';
  if (overview.sessionCount > 0) {
    hotHtml = '<div style="font-size:11px;color:#f0c040;">Main session active</div>';
    if (overview.mainSessionUpdated) {
      hotHtml += '<div style="font-size:10px;color:#666;">Updated ' + timeAgo(overview.mainSessionUpdated) + '</div>';
    }
  } else {
    hotHtml = '<div style="font-size:11px;color:#666;">No active sessions</div>';
  }
  document.getElementById('hot-sessions-list').innerHTML = hotHtml;
  
  // 📈 Model Mix
  document.getElementById('model-primary').textContent = overview.model || 'unknown';
  var modelBreakdown = '';
  if (usage.modelBreakdown && usage.modelBreakdown.length > 0) {
    var primary = usage.modelBreakdown[0];
    var others = usage.modelBreakdown.slice(1, 3);
    modelBreakdown = fmtTokens(primary.tokens) + ' tokens';
    if (others.length > 0) {
      modelBreakdown += ' (+' + others.length + ' others)';
    }
  } else {
    modelBreakdown = 'Primary model';
  }
  document.getElementById('model-breakdown').textContent = modelBreakdown;
  
  // 🐝 Worker Bees (Sub-Agents)
  loadSubAgents();
  
}

async function loadSubAgents() {
  try {
    var data = await fetch('/api/subagents').then(r => r.json());
    var counts = data.counts;
    var subagents = data.subagents;
    
    // Update main counter
    document.getElementById('subagents-count').textContent = counts.total;
    
    // Update status text
    var statusText = '';
    if (counts.active > 0) {
      statusText = counts.active + ' active';
      if (counts.idle > 0) statusText += ', ' + counts.idle + ' idle';
      if (counts.stale > 0) statusText += ', ' + counts.stale + ' stale';
    } else if (counts.total === 0) {
      statusText = 'No sub-agents spawned';
    } else {
      statusText = 'All idle/stale';
    }
    document.getElementById('subagents-status').textContent = statusText;
    
    // Update preview with top sub-agents (human-readable)
    var previewHtml = '';
    if (subagents.length === 0) {
      previewHtml = '<div style="font-size:11px;color:#666;">No active tasks</div>';
    } else {
      // Show active ones first
      var activeFirst = subagents.filter(function(a){return a.status==='active';}).concat(subagents.filter(function(a){return a.status!=='active';}));
      var topAgents = activeFirst.slice(0, 3);
      topAgents.forEach(function(agent) {
        var icon = agent.status === 'active' ? '🔄' : agent.status === 'idle' ? '✅' : '⬜';
        var name = cleanTaskName(agent.displayName);
        if (name.length > 40) name = name.substring(0, 37) + '…';
        previewHtml += '<div class="subagent-item">';
        previewHtml += '<span style="font-size:10px;">' + icon + '</span>';
        previewHtml += '<span class="subagent-name" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escHtml(name) + '</span>';
        previewHtml += '<span class="subagent-runtime">' + agent.runtime + '</span>';
        previewHtml += '</div>';
      });
      
      if (subagents.length > 3) {
        previewHtml += '<div style="font-size:9px;color:#555;margin-top:4px;">+' + (subagents.length - 3) + ' more</div>';
      }
    }
    
    document.getElementById('subagents-preview').innerHTML = previewHtml;
    
  } catch(e) {
    document.getElementById('subagents-count').textContent = '?';
    document.getElementById('subagents-status').textContent = 'Error loading sub-agents';
    document.getElementById('subagents-preview').innerHTML = '<div style="color:#e74c3c;font-size:11px;">Failed to load workforce</div>';
  }
}

// === Active Tasks for Overview ===
var _activeTasksTimer = null;
function cleanTaskName(raw) {
  // Strip timestamp prefixes like "[Sun 2026-02-08 18:22 GMT+1] "
  var name = (raw || '').replace(/^\[.*?\]\s*/, '');
  // Truncate to first sentence or 80 chars
  var dot = name.indexOf('. ');
  if (dot > 10 && dot < 80) name = name.substring(0, dot + 1);
  if (name.length > 80) name = name.substring(0, 77) + '…';
  return name || 'Background task';
}

function detectProjectBadge(text) {
  var projects = {
    'mockround': { label: 'MockRound', color: '#7c3aed' },
    'vedicvoice': { label: 'VedicVoice', color: '#d97706' },
    'openclaw': { label: 'OpenClaw', color: '#2563eb' },
    'dashboard': { label: 'Dashboard', color: '#0891b2' },
    'shopify': { label: 'Shopify', color: '#16a34a' },
    'sanskrit': { label: 'Sanskrit', color: '#ea580c' },
    'telegram': { label: 'Telegram', color: '#0088cc' },
    'discord': { label: 'Discord', color: '#5865f2' },
  };
  var lower = (text || '').toLowerCase();
  for (var key in projects) {
    if (lower.includes(key)) return projects[key];
  }
  return null;
}

function humanTime(runtimeMs) {
  if (!runtimeMs || runtimeMs === Infinity) return '';
  var sec = Math.floor(runtimeMs / 1000);
  if (sec < 60) return 'Started ' + sec + 's ago';
  var min = Math.floor(sec / 60);
  if (min < 60) return 'Started ' + min + ' min ago';
  var hr = Math.floor(min / 60);
  if (hr < 24) return 'Started ' + hr + 'h ago';
  return 'Started ' + Math.floor(hr / 24) + 'd ago';
}

function humanTimeDone(runtimeMs) {
  if (!runtimeMs || runtimeMs === Infinity) return '';
  var sec = Math.floor(runtimeMs / 1000);
  if (sec < 60) return 'Finished ' + sec + 's ago';
  var min = Math.floor(sec / 60);
  if (min < 60) return 'Finished ' + min + ' min ago';
  var hr = Math.floor(min / 60);
  if (hr < 24) return 'Finished ' + hr + 'h ago';
  return 'Finished ' + Math.floor(hr / 24) + 'd ago';
}

async function loadActiveTasks() {
  try {
    var data = await fetch('/api/subagents').then(r => r.json());
    var grid = document.getElementById('overview-tasks-list') || document.getElementById('active-tasks-grid');
    if (!grid) return;
    var agents = data.subagents || [];
    if (agents.length === 0) {
      grid.innerHTML = '<div class="card" style="text-align:center;padding:24px;color:var(--text-muted);grid-column:1/-1;">'
        + '<div style="font-size:24px;margin-bottom:8px;">✨</div>'
        + '<div style="font-size:13px;">No active tasks - all quiet</div></div>';
      return;
    }

    // Group by status: running first, then recently completed, then truly failed
    var running = [], done = [], failed = [];
    agents.forEach(function(agent) {
      var isRealFailure = agent.status === 'stale' && agent.abortedLastRun && (agent.outputTokens || 0) === 0;
      if (agent.status === 'active') running.push(agent);
      else if (isRealFailure) failed.push(agent);
      else done.push(agent);
    });
    var sorted = running.concat(done).concat(failed);

    // Only show recent ones (last 2 hours for done, all running)
    sorted = sorted.filter(function(a) {
      if (a.status === 'active') return true;
      return a.runtimeMs < 2 * 60 * 60 * 1000; // 2 hours
    });

    if (sorted.length === 0) {
      grid.innerHTML = '<div class="card" style="text-align:center;padding:24px;color:var(--text-muted);grid-column:1/-1;">'
        + '<div style="font-size:24px;margin-bottom:8px;">✨</div>'
        + '<div style="font-size:13px;">No recent tasks</div></div>';
      return;
    }

    var html = '';
    sorted.forEach(function(agent) {
      // Determine true completion status: only "failed" if zero output and aborted
      var isRealFailure = agent.status === 'stale' && agent.abortedLastRun && (agent.outputTokens || 0) === 0;
      var statusClass = agent.status === 'active' ? 'running' : isRealFailure ? 'failed' : 'complete';
      var statusEmoji, statusLabel, timeStr;
      if (agent.status === 'active') {
        var mins = Math.max(1, Math.floor((agent.runtimeMs || 0) / 60000));
        statusEmoji = '🔄';
        statusLabel = 'Running (' + mins + ' min)';
        timeStr = humanTime(agent.runtimeMs);
      } else if (isRealFailure) {
        statusEmoji = '❌';
        statusLabel = 'Failed';
        timeStr = humanTimeDone(agent.runtimeMs);
      } else {
        statusEmoji = '✅';
        statusLabel = 'Done';
        timeStr = humanTimeDone(agent.runtimeMs);
      }

      var taskName = cleanTaskName(agent.displayName);
      var badge = detectProjectBadge(agent.displayName);

      html += '<div class="task-card ' + statusClass + '" style="cursor:pointer;" onclick="openTaskModal(\'' + escHtml(agent.sessionId).replace(/'/g,"\\'") + '\',\'' + escHtml(taskName).replace(/'/g,"\\'") + '\',\'' + escHtml(agent.key || agent.sessionId).replace(/'/g,"\\'") + '\')">';
      if (agent.status === 'active') html += '<div class="task-card-pulse active"></div>';
      html += '<div class="task-card-header">';
      html += '<div class="task-card-name">' + escHtml(taskName) + '</div>';
      html += '<span class="task-card-badge ' + statusClass + '">' + statusEmoji + ' ' + statusLabel + '</span>';
      html += '</div>';
      // Project badge + human time
      html += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">';
      if (badge) {
        html += '<span style="display:inline-block;padding:1px 8px;border-radius:10px;font-size:10px;font-weight:700;background:' + badge.color + '22;color:' + badge.color + ';border:1px solid ' + badge.color + '44;">' + badge.label + '</span>';
      }
      if (timeStr) {
        html += '<span style="font-size:12px;color:var(--text-muted);">' + escHtml(timeStr) + '</span>';
      }
      html += '</div>';
      // Show/Hide details toggle + logs link
      var detailId = 'task-detail-' + agent.sessionId.replace(/[^a-z0-9]/gi, '');
      html += '<div style="display:flex;align-items:center;gap:12px;margin-top:4px;">';
      html += '<span style="font-size:11px;color:var(--text-tertiary);cursor:pointer;user-select:none;" onclick="event.stopPropagation();var d=document.getElementById(\'' + detailId + '\');var open=d.style.display!==\'none\';d.style.display=open?\'none\':\'block\';this.textContent=open?\'▶ Show details\':\'▼ Hide details\';">▶ Show details</span>';
      html += '<span style="font-size:11px;color:var(--text-link);cursor:pointer;opacity:0.7;" onclick="event.stopPropagation();openTaskModal(\'' + escHtml(agent.sessionId).replace(/'/g,"\\'") + '\',\'' + escHtml(taskName).replace(/'/g,"\\'") + '\',\'' + escHtml(agent.key || agent.sessionId).replace(/'/g,"\\'") + '\');setTimeout(function(){switchModalTab(\'full\');},100);">📋 View logs</span>';
      html += '</div>';
      // Collapsible technical details
      html += '<div id="' + detailId + '" style="display:none;margin-top:8px;padding:10px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;font-size:11px;line-height:1.7;color:var(--text-tertiary);">';
      html += '<div><span style="color:var(--text-muted);">Session:</span> <span style="font-family:monospace;font-size:10px;">' + escHtml(agent.sessionId) + '</span></div>';
      html += '<div><span style="color:var(--text-muted);">Key:</span> <span style="font-family:monospace;font-size:10px;">' + escHtml(agent.key) + '</span></div>';
      html += '<div><span style="color:var(--text-muted);">Model:</span> ' + escHtml(agent.model || 'unknown') + '</div>';
      html += '<div><span style="color:var(--text-muted);">Channel:</span> ' + escHtml(agent.channel || '—') + '</div>';
      html += '<div><span style="color:var(--text-muted);">Runtime:</span> ' + escHtml(agent.runtime) + ' (' + Math.round((agent.runtimeMs||0)/1000) + 's)</div>';
      // Full task prompt
      html += '<div style="margin-top:6px;"><span style="color:var(--text-muted);">Full prompt:</span></div>';
      html += '<div style="font-size:10px;font-family:monospace;white-space:pre-wrap;word-break:break-word;max-height:120px;overflow-y:auto;padding:6px;background:var(--bg-primary);border-radius:4px;margin-top:2px;">' + escHtml(agent.displayName) + '</div>';
      // Recent tool calls
      if (agent.recentTools && agent.recentTools.length > 0) {
        html += '<div style="margin-top:6px;"><span style="color:var(--text-muted);">Recent tools:</span></div>';
        agent.recentTools.forEach(function(t) {
          html += '<div style="font-size:10px;font-family:monospace;color:var(--text-tertiary);"><span style="color:var(--text-accent);">' + escHtml(t.name) + '</span> ' + escHtml(t.summary) + '</div>';
        });
      }
      if (agent.lastText) {
        html += '<div style="margin-top:6px;"><span style="color:var(--text-muted);">Last output:</span></div>';
        html += '<div style="font-size:10px;font-style:italic;color:var(--text-tertiary);max-height:60px;overflow-y:auto;">' + escHtml(agent.lastText) + '</div>';
      }
      html += '</div>';
      html += '</div>';
    });
    grid.innerHTML = html;
  } catch(e) {
    // silently fail
  }
}
// Auto-refresh active tasks every 5s
function startActiveTasksRefresh() {
  loadActiveTasks();
  if (_activeTasksTimer) clearInterval(_activeTasksTimer);
  _activeTasksTimer = setInterval(loadActiveTasks, 5000);
}

async function loadToolActivity() {
  try {
    var logs = await fetch('/api/logs?lines=100').then(r => r.json());
    var toolCounts = { exec: 0, browser: 0, search: 0, other: 0 };
    var recentTools = [];
    
    logs.lines.forEach(function(line) {
      var msg = line.toLowerCase();
      if (msg.includes('tool') || msg.includes('invoke')) {
        if (msg.includes('exec') || msg.includes('shell')) { 
          toolCounts.exec++; recentTools.push('exec'); 
        } else if (msg.includes('browser') || msg.includes('screenshot')) { 
          toolCounts.browser++; recentTools.push('browser'); 
        } else if (msg.includes('web_search') || msg.includes('web_fetch')) { 
          toolCounts.search++; recentTools.push('search'); 
        } else {
          toolCounts.other++;
        }
      }
    });
    
    document.getElementById('tools-active').textContent = recentTools.slice(0, 3).join(', ') || 'Idle';
    document.getElementById('tools-recent').textContent = 'Last ' + Math.min(logs.lines.length, 100) + ' log entries';
    
    var sparks = document.querySelectorAll('.tool-spark span');
    sparks[0].textContent = toolCounts.exec;
    sparks[1].textContent = toolCounts.browser;  
    sparks[2].textContent = toolCounts.search;
  } catch(e) {
    document.getElementById('tools-active').textContent = '—';
  }
}

async function loadActivityStream() {
  try {
    var transcripts = await fetch('/api/transcripts').then(r => r.json());
    var activities = [];
    
    // Get the most recent transcript to parse for activity
    if (transcripts.transcripts && transcripts.transcripts.length > 0) {
      var recent = transcripts.transcripts[0];
      try {
        var transcript = await fetch('/api/transcript/' + recent.id).then(r => r.json());
        var recentMessages = transcript.messages.slice(-10); // Last 10 messages
        
        recentMessages.forEach(function(msg) {
          if (msg.role === 'assistant' && msg.content) {
            var content = msg.content.toLowerCase();
            var activity = '';
            var time = new Date(msg.timestamp || Date.now()).toLocaleTimeString();
            
            if (content.includes('searching') || content.includes('search')) {
              activity = time + ' 🔍 Searching web for information';
            } else if (content.includes('reading') || content.includes('file')) {
              activity = time + ' 📖 Reading files';
            } else if (content.includes('writing') || content.includes('edit')) {
              activity = time + ' ✏️ Editing files'; 
            } else if (content.includes('exec') || content.includes('command')) {
              activity = time + ' ⚡ Running commands';
            } else if (content.includes('browser') || content.includes('screenshot')) {
              activity = time + ' 🌐 Browser automation';
            } else if (msg.content.length > 50) {
              var preview = msg.content.substring(0, 80).replace(/[^\w\s]/g, ' ').trim();
              activity = time + ' 💭 ' + preview + '...';
            }
            
            if (activity) activities.push(activity);
          }
        });
      } catch(e) {}
    }
    
    if (activities.length === 0) {
      activities = [
        new Date().toLocaleTimeString() + ' 🤖 AI agent initialized',
        new Date().toLocaleTimeString() + ' 📡 Monitoring for activity...'
      ];
    }
    
    var html = activities.slice(-8).map(function(a) {
      return '<div style="padding:4px 0; border-bottom:1px solid #1a1a30; color:#ccc;">' + escHtml(a) + '</div>';
    }).join('');
    
    document.getElementById('activity-stream').innerHTML = html;
  } catch(e) {
    document.getElementById('activity-stream').innerHTML = '<div style="color:#666;">Error loading activity stream</div>';
  }
}

// ===== Sub-Agent Live Activity System =====
var _saAutoRefreshTimer = null;
var _saSelectedId = null;

function toggleSAAutoRefresh() {
  if (document.getElementById('sa-auto-refresh').checked) {
    _saAutoRefreshTimer = setInterval(function() { loadSubAgentsPage(true); }, 5000);
  } else {
    clearInterval(_saAutoRefreshTimer);
    _saAutoRefreshTimer = null;
  }
}

async function loadSubAgentsPage(silent) {
  try {
    var data = await fetch('/api/subagents').then(r => r.json());
    var counts = data.counts;
    var subagents = data.subagents;

    // Update stats
    document.getElementById('subagents-active-count').textContent = counts.active;
    document.getElementById('subagents-idle-count').textContent = counts.idle;
    document.getElementById('subagents-stale-count').textContent = counts.stale;
    document.getElementById('subagents-total-count').textContent = counts.total;
    document.getElementById('sa-refresh-time').textContent = 'Updated ' + new Date().toLocaleTimeString();

    var listHtml = '';
    if (subagents.length === 0) {
      listHtml = '<div style="padding:40px;text-align:center;color:#666;">'
        + '<div style="font-size:48px;margin-bottom:16px;">🐝</div>'
        + '<div style="font-size:16px;margin-bottom:8px;">No Sub-Agents Yet</div>'
        + '<div style="font-size:12px;max-width:400px;margin:0 auto;">Sub-agents are spawned by the main AI to handle complex tasks in parallel. They\'ll appear here when active.</div>'
        + '</div>';
    } else {
      subagents.forEach(function(agent) {
        var isSelected = _saSelectedId === agent.sessionId;
        var statusIcon = agent.status === 'active' ? '🟢' : agent.status === 'idle' ? '🟡' : '⬜';
        var statusLabel = agent.status === 'active' ? 'Working...' : agent.status === 'idle' ? 'Recently finished' : 'Completed';

        listHtml += '<div class="subagent-row" style="cursor:pointer;' + (isSelected ? 'background:var(--bg-hover,#1a1a3a);border-left:3px solid #60a0ff;' : '') + '" onclick="openSAActivity(\'' + agent.sessionId + '\',\'' + escHtml(agent.displayName) + '\',\'' + agent.status + '\')">';
        listHtml += '<div class="subagent-indicator ' + agent.status + '"></div>';
        listHtml += '<div class="subagent-info" style="flex:1;">';

        // Header line: name + status badge + time
        listHtml += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">';
        listHtml += '<span class="subagent-id">' + statusIcon + ' ' + escHtml(agent.displayName) + '</span>';
        listHtml += '<div style="display:flex;gap:8px;align-items:center;">';
        listHtml += '<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:' + (agent.status === 'active' ? '#1a3a2a' : '#1a1a2a') + ';color:' + (agent.status === 'active' ? '#60ff80' : '#888') + ';">' + statusLabel + '</span>';
        listHtml += '<span style="font-size:11px;color:#666;">' + agent.runtime + '</span>';
        listHtml += '</div></div>';

        // Recent tool calls (live activity preview)
        if (agent.recentTools && agent.recentTools.length > 0) {
          listHtml += '<div style="margin-top:4px;display:flex;flex-direction:column;gap:2px;">';
          var showTools = agent.recentTools.slice(-3);  // Show last 3 tools
          showTools.forEach(function(tool) {
            var toolColor = tool.name === 'exec' ? '#f0c040' : tool.name.match(/Read|Write|Edit/) ? '#60a0ff' : tool.name === 'web_search' ? '#c0a0ff' : '#50e080';
            listHtml += '<div style="font-size:11px;color:#888;display:flex;align-items:center;gap:6px;font-family:monospace;">';
            listHtml += '<span style="color:' + toolColor + ';font-weight:600;min-width:70px;">' + escHtml(tool.name) + '</span>';
            listHtml += '<span style="color:#666;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escHtml(tool.summary) + '</span>';
            listHtml += '</div>';
          });
          listHtml += '</div>';
        }

        // Last assistant text (what it's thinking/saying)
        if (agent.lastText) {
          listHtml += '<div style="margin-top:4px;font-size:11px;color:#777;font-style:italic;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">💭 ' + escHtml(agent.lastText.substring(0, 120)) + '</div>';
        }

        listHtml += '</div></div>';
      });
    }

    document.getElementById('subagents-list').innerHTML = listHtml;

    // If we have a selected sub-agent, refresh its activity panel too
    if (_saSelectedId && !silent) {
      loadSAActivity(_saSelectedId);
    }

    // Start auto-refresh if enabled
    if (!_saAutoRefreshTimer && document.getElementById('sa-auto-refresh').checked) {
      _saAutoRefreshTimer = setInterval(function() { loadSubAgentsPage(true); }, 5000);
    }

  } catch(e) {
    if (!silent) {
      document.getElementById('subagents-list').innerHTML = '<div style="padding:20px;color:#e74c3c;text-align:center;">Failed to load: ' + e.message + '</div>';
    }
  }
}

function openSAActivity(sessionId, name, status) {
  _saSelectedId = sessionId;
  document.getElementById('sa-activity-panel').style.display = 'block';
  document.getElementById('sa-panel-title').textContent = '🐝 ' + name;
  document.getElementById('sa-panel-status').textContent = status === 'active' ? '🟢 Working' : status === 'idle' ? '🟡 Idle' : '⬜ Done';
  loadSAActivity(sessionId);
  // Re-render list to highlight selected
  loadSubAgentsPage(true);
}

function closeSAPanel() {
  _saSelectedId = null;
  document.getElementById('sa-activity-panel').style.display = 'none';
  loadSubAgentsPage(true);
}

async function loadSAActivity(sessionId) {
  var container = document.getElementById('sa-activity-timeline');
  try {
    var data = await fetch('/api/subagent/' + sessionId + '/activity').then(r => r.json());
    if (!data.events || data.events.length === 0) {
      container.innerHTML = '<div style="padding:20px;text-align:center;color:#666;">No activity recorded yet</div>';
      return;
    }

    var html = '';
    data.events.forEach(function(evt, i) {
      var time = evt.ts ? new Date(evt.ts).toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit',second:'2-digit'}) : '';

      if (evt.type === 'tool_call') {
        var color = evt.tool === 'exec' ? '#f0c040' : evt.tool.match(/Read|Write|Edit/) ? '#60a0ff' : evt.tool === 'web_search' ? '#c0a0ff' : evt.tool === 'browser' ? '#40a0b0' : '#50e080';
        html += '<div style="display:flex;gap:8px;padding:6px 16px;align-items:flex-start;border-left:3px solid ' + color + ';">';
        html += '<span style="font-size:10px;color:#555;min-width:55px;font-family:monospace;">' + time + '</span>';
        html += '<span style="font-size:11px;color:' + color + ';font-weight:700;min-width:80px;">⚡ ' + escHtml(evt.tool) + '</span>';
        html += '<span style="font-size:11px;color:#aaa;font-family:monospace;word-break:break-all;">' + escHtml(evt.input) + '</span>';
        html += '</div>';
      } else if (evt.type === 'tool_result') {
        var resultColor = evt.isError ? '#e04040' : '#2a5a3a';
        html += '<div style="display:flex;gap:8px;padding:4px 16px 4px 24px;align-items:flex-start;">';
        html += '<span style="font-size:10px;color:#555;min-width:55px;font-family:monospace;">' + time + '</span>';
        html += '<span style="font-size:10px;color:' + (evt.isError ? '#e04040' : '#555') + ';min-width:80px;">' + (evt.isError ? '❌ error' : '✓ result') + '</span>';
        html += '<span style="font-size:10px;color:#666;font-family:monospace;max-height:40px;overflow:hidden;word-break:break-all;">' + escHtml((evt.preview || '').substring(0, 200)) + '</span>';
        html += '</div>';
      } else if (evt.type === 'thinking') {
        html += '<div style="display:flex;gap:8px;padding:8px 16px;align-items:flex-start;border-left:3px solid #50e080;">';
        html += '<span style="font-size:10px;color:#555;min-width:55px;font-family:monospace;">' + time + '</span>';
        html += '<span style="font-size:11px;color:#50e080;min-width:80px;">💬 says</span>';
        html += '<span style="font-size:12px;color:#ccc;">' + escHtml(evt.text) + '</span>';
        html += '</div>';
      } else if (evt.type === 'internal_thought') {
        html += '<div style="display:flex;gap:8px;padding:4px 16px;align-items:flex-start;opacity:0.6;">';
        html += '<span style="font-size:10px;color:#555;min-width:55px;font-family:monospace;">' + time + '</span>';
        html += '<span style="font-size:10px;color:#9070d0;min-width:80px;">🧠 thinks</span>';
        html += '<span style="font-size:10px;color:#888;font-style:italic;">' + escHtml(evt.text) + '</span>';
        html += '</div>';
      } else if (evt.type === 'model_change') {
        html += '<div style="display:flex;gap:8px;padding:4px 16px;align-items:center;opacity:0.5;">';
        html += '<span style="font-size:10px;color:#555;min-width:55px;font-family:monospace;">' + time + '</span>';
        html += '<span style="font-size:10px;color:#888;">🔄 Model: ' + escHtml(evt.model) + '</span>';
        html += '</div>';
      }
    });

    container.innerHTML = html;
    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
  } catch(e) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:#e74c3c;">Failed to load activity: ' + e.message + '</div>';
  }
}

function openDetailView(type) {
  // Navigate to the appropriate tab with detail view
  if (type === 'cost' || type === 'tokens') {
    switchTab('usage');
  } else if (type === 'sessions') {
    switchTab('sessions');
  } else if (type === 'subagents') {
    switchTab('subagents');
  } else if (type === 'tools') {
    switchTab('logs');
  } else {
    // For thinking feed and models, stay on overview but could expand in future
    alert('Detail view for ' + type + ' coming soon!');
  }
}

function renderLogs(elId, lines) {
  var html = '';
  lines.forEach(function(l) {
    var cls = 'msg';
    var display = l;
    try {
      var obj = JSON.parse(l);
      var ts = '';
      if (obj.time || (obj._meta && obj._meta.date)) {
        var d = new Date(obj.time || obj._meta.date);
        ts = d.toLocaleTimeString('en-GB', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
      }
      var level = (obj.logLevelName || obj.level || 'info').toLowerCase();
      if (level === 'error' || level === 'fatal') cls = 'err';
      else if (level === 'warn' || level === 'warning') cls = 'warn';
      else if (level === 'debug') cls = 'msg';
      else cls = 'info';
      var msg = obj.msg || obj.message || obj.name || '';
      var extras = [];
      // Field "0" is usually a JSON string like {"subsystem":"gateway/ws"} - extract subsystem
      var subsystem = '';
      if (obj["0"]) {
        try { var sub = JSON.parse(obj["0"]); subsystem = sub.subsystem || ''; } catch(e) { subsystem = String(obj["0"]); }
      }
      // Field "1" can be a string or object - stringify objects
      function flatVal(v) { return (typeof v === 'object' && v !== null) ? JSON.stringify(v) : String(v); }
      if (obj["1"]) {
        if (typeof obj["1"] === 'object') {
          var parts = [];
          for (var k in obj["1"]) { if (k !== 'cause') parts.push(k + '=' + flatVal(obj["1"][k])); else parts.unshift(flatVal(obj["1"][k])); }
          extras.push(parts.join(' '));
        } else {
          extras.push(String(obj["1"]));
        }
      }
      if (obj["2"]) extras.push(flatVal(obj["2"]));
      // Build display
      var prefix = subsystem ? '[' + subsystem + '] ' : '';
      if (msg && extras.length) display = prefix + msg + ' ' + extras.join(' ');
      else if (extras.length) display = prefix + extras.join(' ');
      else if (msg) display = prefix + msg;
      else display = l.substring(0, 200);
      if (ts) display = '<span class="ts">' + ts + '</span> ' + escHtml(display);
      else display = escHtml(display);
    } catch(e) {
      if (l.includes('Error') || l.includes('failed')) cls = 'err';
      else if (l.includes('WARN')) cls = 'warn';
      display = escHtml(l.substring(0, 300));
    }
    html += '<div class="log-line"><span class="' + cls + '">' + display + '</span></div>';
  });
  document.getElementById(elId).innerHTML = html || '<span style="color:#555">No logs</span>';
  document.getElementById(elId).scrollTop = document.getElementById(elId).scrollHeight;
}

function escHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

async function viewFile(path) {
  var viewer = document.getElementById('file-viewer');
  var title = document.getElementById('file-viewer-title');
  var content = document.getElementById('file-viewer-content');
  title.textContent = path;
  content.textContent = 'Loading...';
  viewer.style.display = 'block';
  try {
    var data = await fetch('/api/file?path=' + encodeURIComponent(path)).then(r => r.json());
    if (data.error) { content.textContent = 'Error: ' + data.error; return; }
    content.textContent = data.content;
  } catch(e) {
    content.textContent = 'Failed to load: ' + e.message;
  }
  viewer.scrollIntoView({behavior:'smooth'});
}

function closeFileViewer() {
  document.getElementById('file-viewer').style.display = 'none';
}

async function loadSessions() {
  var [sessData, saData] = await Promise.all([
    fetch('/api/sessions').then(r => r.json()),
    fetch('/api/subagents').then(r => r.json())
  ]);
  var html = '';
  // Main sessions (non-subagent)
  var mainSessions = sessData.sessions.filter(function(s) { return !(s.sessionId || '').includes('subagent'); });
  var subagents = saData.subagents || [];
  
  mainSessions.forEach(function(s) {
    html += '<div class="session-item" style="border-left:3px solid var(--bg-accent);padding-left:16px;">';
    html += '<div class="session-name">🖥️ ' + escHtml(s.displayName || s.key) + ' <span style="font-size:11px;color:var(--text-muted);font-weight:400;">Main Session</span></div>';
    html += '<div class="session-meta">';
    html += '<span><span class="badge model">' + (s.model||'default') + '</span></span>';
    if (s.channel !== 'unknown') html += '<span><span class="badge channel">' + s.channel + '</span></span>';
    html += '<span>Updated ' + timeAgo(s.updatedAt) + '</span>';
    html += '</div>';
    // Sub-agents nested underneath
    if (subagents.length > 0) {
      html += '<div style="margin-top:8px;margin-left:16px;border-left:2px solid var(--border-primary);padding-left:12px;">';
      subagents.forEach(function(sa) {
        var statusIcon = sa.status === 'active' ? '🟢' : sa.status === 'idle' ? '🟡' : '⬜';
        html += '<details style="margin-bottom:4px;">';
        html += '<summary style="cursor:pointer;font-size:13px;color:var(--text-secondary);padding:4px 0;">';
        html += statusIcon + ' <strong>' + escHtml(sa.displayName) + '</strong>';
        html += ' <span style="color:var(--text-muted);font-size:11px;">' + sa.runtime + '</span>';
        html += '</summary>';
        html += '<div style="padding:6px 0 6px 20px;font-size:12px;color:var(--text-muted);">';
        if (sa.recentTools && sa.recentTools.length > 0) {
          sa.recentTools.slice(-3).forEach(function(t) {
            html += '<div style="font-family:monospace;margin-bottom:2px;">⚡ <span style="color:var(--text-accent);">' + escHtml(t.name) + '</span> ' + escHtml(t.summary.substring(0,80)) + '</div>';
          });
        }
        if (sa.lastText) {
          html += '<div style="font-style:italic;margin-top:4px;">💭 ' + escHtml(sa.lastText.substring(0, 120)) + '</div>';
        }
        html += '</div></details>';
      });
      html += '</div>';
    }
    html += '</div>';
  });
  
  // Show orphan sessions that aren't main
  var subSessions = sessData.sessions.filter(function(s) { return (s.sessionId || '').includes('subagent'); });
  if (subSessions.length > 0 && mainSessions.length === 0) {
    sessData.sessions.forEach(function(s) {
      html += '<div class="session-item">';
      html += '<div class="session-name">' + escHtml(s.displayName || s.key) + '</div>';
      html += '<div class="session-meta">';
      html += '<span><span class="badge model">' + (s.model||'default') + '</span></span>';
      html += '<span>Updated ' + timeAgo(s.updatedAt) + '</span>';
      html += '</div></div>';
    });
  }
  
  document.getElementById('sessions-list').innerHTML = html || '<div style="padding:16px;color:var(--text-muted);">No sessions found</div>';
}

async function loadCrons() {
  var data = await fetch('/api/crons').then(r => r.json());
  var html = '';
  data.jobs.forEach(function(j) {
    var status = j.state && j.state.lastStatus ? j.state.lastStatus : 'pending';
    html += '<div class="cron-item">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
    html += '<div class="cron-name">' + escHtml(j.name || j.id) + '</div>';
    html += '<span class="cron-status ' + status + '">' + status + '</span>';
    if (status === 'error') {
      var errMsg = (j.state && j.state.lastError) ? escHtml(j.state.lastError) : 'Unknown error';
      var errTime = (j.state && j.state.lastRunAtMs) ? new Date(j.state.lastRunAtMs).toLocaleString() : 'Unknown';
      var consecutiveFails = (j.state && j.state.consecutiveFailures) ? j.state.consecutiveFailures : '';
      html += '<span class="cron-error-actions">';
      html += '<span class="cron-info-icon" title="Error details" onclick="event.stopPropagation();showCronError(this,\'' + errMsg.replace(/'/g,'\\&#39;').replace(/"/g,'&quot;') + '\',\'' + escHtml(errTime) + '\',' + (consecutiveFails||'null') + ')">ℹ️</span>';
      html += '<button class="cron-fix-btn" onclick="event.stopPropagation();confirmCronFix(\'' + escHtml(j.id) + '\',\'' + escHtml(j.name||j.id).replace(/'/g,'\\&#39;') + '\')">🔧 Fix</button>';
      html += '</span>';
    }
    html += '</div>';
    html += '<div class="cron-schedule">' + formatSchedule(j.schedule) + '</div>';
    html += '<div class="cron-meta">';
    if (j.state && j.state.lastRunAtMs) html += 'Last: ' + timeAgo(j.state.lastRunAtMs);
    if (j.state && j.state.nextRunAtMs) html += ' · Next: ' + formatTime(j.state.nextRunAtMs);
    if (j.state && j.state.lastDurationMs) html += ' · Took: ' + (j.state.lastDurationMs/1000).toFixed(1) + 's';
    html += '</div></div>';
  });
  document.getElementById('crons-list').innerHTML = html || 'No cron jobs';
}

function showCronError(el, msg, ts, fails) {
  // Remove any existing popover
  var old = document.querySelector('.cron-error-popover');
  if (old) old.remove();
  var rect = el.getBoundingClientRect();
  var pop = document.createElement('div');
  pop.className = 'cron-error-popover';
  pop.style.top = (rect.bottom + 8) + 'px';
  pop.style.left = Math.min(rect.left, window.innerWidth - 420) + 'px';
  var h = '<span class="ep-close" onclick="this.parentElement.remove()">&times;</span>';
  h += '<div class="ep-label">Error Message</div><div class="ep-value">' + msg + '</div>';
  h += '<div class="ep-label">Failed At</div><div class="ep-value ts">' + ts + '</div>';
  if (fails) h += '<div class="ep-label">Consecutive Failures</div><div class="ep-value">' + fails + '</div>';
  pop.innerHTML = h;
  document.body.appendChild(pop);
  // Close on outside click
  setTimeout(function() {
    document.addEventListener('click', function handler(e) {
      if (!pop.contains(e.target) && e.target !== el) { pop.remove(); document.removeEventListener('click', handler); }
    });
  }, 10);
}

function confirmCronFix(jobId, jobName) {
  var modal = document.createElement('div');
  modal.className = 'cron-confirm-modal';
  modal.innerHTML = '<div class="cron-confirm-box"><p>Ask AI to diagnose and fix<br><strong>' + jobName + '</strong>?</p><button class="confirm-yes" onclick="submitCronFix(\'' + jobId + '\');this.closest(\'.cron-confirm-modal\').remove()">Yes, fix it</button><button class="confirm-no" onclick="this.closest(\'.cron-confirm-modal\').remove()">Cancel</button></div>';
  document.body.appendChild(modal);
  modal.addEventListener('click', function(e) { if (e.target === modal) modal.remove(); });
}

async function submitCronFix(jobId) {
  try {
    var res = await fetch('/api/cron/fix', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({jobId: jobId})});
    var data = await res.json();
    showCronToast(data.message || 'Fix request sent to AI agent');
  } catch(e) {
    showCronToast('Error: ' + e.message);
  }
}

function showCronToast(msg) {
  var t = document.createElement('div');
  t.className = 'cron-toast';
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(function() { t.style.opacity = '0'; setTimeout(function() { t.remove(); }, 300); }, 3000);
}

function formatSchedule(s) {
  if (s.kind === 'cron') return 'cron: ' + s.expr + (s.tz ? ' (' + s.tz + ')' : '');
  if (s.kind === 'every') return 'every ' + (s.everyMs/60000) + ' min';
  if (s.kind === 'at') return 'once at ' + formatTime(s.atMs);
  return JSON.stringify(s);
}

async function loadLogs() {
  var lines = document.getElementById('log-lines').value;
  var data = await fetch('/api/logs?lines=' + lines).then(r => r.json());
  renderLogs('logs-full', data.lines);
}

async function loadMemory() {
  var data = await fetch('/api/memory-files').then(r => r.json());
  var html = '';
  data.forEach(function(f) {
    var size = f.size > 1024 ? (f.size/1024).toFixed(1) + ' KB' : f.size + ' B';
    html += '<div class="memory-item" onclick="viewFile(\'' + escHtml(f.path) + '\')">';
    html += '<span class="memory-name" style="color:#60a0ff;">' + escHtml(f.path) + '</span>';
    html += '<span class="memory-size">' + size + '</span>';
    html += '</div>';
  });
  document.getElementById('memory-list').innerHTML = html || 'No memory files';
}

// ===== Mission Control Summary Bar =====
var _mcData = null;
var _mcExpanded = null;
var _mcRefreshTimer = null;

async function loadMCTasks() {
  try {
    var r = await fetch('/api/mc-tasks');
    var data = await r.json();
    var wrapper = document.getElementById('mc-bar-wrapper');
    if (!data.available) { wrapper.style.display='none'; return; }
    wrapper.style.display='';
    var tasks = data.tasks || [];
    var cols = [
      {key:'inbox', label:'Inbox', color:'#3b82f6', bg:'#3b82f620', icon:'📥', tasks:[]},
      {key:'in_progress', label:'In Progress', color:'#16a34a', bg:'#16a34a20', icon:'🔄', tasks:[]},
      {key:'review', label:'Review', color:'#d97706', bg:'#d9770620', icon:'👀', tasks:[]},
      {key:'blocked', label:'Blocked', color:'#dc2626', bg:'#dc262620', icon:'🚫', tasks:[]},
      {key:'done', label:'Done', color:'#6b7280', bg:'#6b728020', icon:'✅', tasks:[]}
    ];
    tasks.forEach(function(t) {
      var col = t.column || 'inbox';
      var c = cols.find(function(x){return x.key===col;});
      if (c) c.tasks.push(t);
    });
    _mcData = cols;
    var bar = document.getElementById('mc-summary-bar');
    var html = '<span style="font-size:12px;font-weight:700;color:var(--text-tertiary);margin-right:4px;">🎯 MC</span>';
    cols.forEach(function(c, i) {
      if (i > 0) html += '<span style="color:var(--text-faint);font-size:12px;margin:0 2px;">│</span>';
      var active = _mcExpanded === c.key ? 'outline:2px solid '+c.color+';outline-offset:-2px;' : '';
      html += '<span onclick="toggleMCColumn(\''+c.key+'\')" style="cursor:pointer;display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:16px;background:'+c.bg+';'+active+'transition:all 0.15s;">';
      html += '<span style="font-size:12px;">'+c.icon+'</span>';
      html += '<span style="font-size:11px;color:var(--text-secondary);">'+c.label+'</span>';
      html += '<span style="font-size:12px;font-weight:700;color:'+c.color+';min-width:16px;text-align:center;">'+c.tasks.length+'</span>';
      html += '</span>';
    });
    var total = tasks.length;
    html += '<span style="margin-left:auto;font-size:10px;color:var(--text-muted);">'+total+' tasks</span>';
    bar.innerHTML = html;
    if (_mcExpanded) renderMCExpanded(_mcExpanded);
  } catch(e) {
    var w = document.getElementById('mc-bar-wrapper');
    if (w) w.style.display='none';
  }
}

function toggleMCColumn(key) {
  if (_mcExpanded === key) { _mcExpanded = null; document.getElementById('mc-expanded-section').style.display='none'; }
  else { _mcExpanded = key; renderMCExpanded(key); }
  // Re-render bar to update active pill
  if (_mcData) {
    var bar = document.getElementById('mc-summary-bar');
    var cols = _mcData;
    var html = '<span style="font-size:12px;font-weight:700;color:var(--text-tertiary);margin-right:4px;">🎯 MC</span>';
    cols.forEach(function(c, i) {
      if (i > 0) html += '<span style="color:var(--text-faint);font-size:12px;margin:0 2px;">│</span>';
      var active = _mcExpanded === c.key ? 'outline:2px solid '+c.color+';outline-offset:-2px;' : '';
      html += '<span onclick="toggleMCColumn(\''+c.key+'\')" style="cursor:pointer;display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:16px;background:'+c.bg+';'+active+'transition:all 0.15s;">';
      html += '<span style="font-size:12px;">'+c.icon+'</span>';
      html += '<span style="font-size:11px;color:var(--text-secondary);">'+c.label+'</span>';
      html += '<span style="font-size:12px;font-weight:700;color:'+c.color+';min-width:16px;text-align:center;">'+c.tasks.length+'</span>';
      html += '</span>';
    });
    var total = cols.reduce(function(s,c){return s+c.tasks.length;},0);
    html += '<span style="margin-left:auto;font-size:10px;color:var(--text-muted);">'+total+' tasks</span>';
    bar.innerHTML = html;
  }
}

function renderMCExpanded(key) {
  var sec = document.getElementById('mc-expanded-section');
  if (!_mcData) { sec.style.display='none'; return; }
  var col = _mcData.find(function(c){return c.key===key;});
  if (!col || col.tasks.length === 0) { sec.style.display='block'; sec.innerHTML='<div style="font-size:12px;color:var(--text-muted);padding:4px;">No tasks in '+col.label+'</div>'; return; }
  sec.style.display='block';
  var html = '<div style="font-size:11px;font-weight:700;color:'+col.color+';margin-bottom:8px;">'+col.icon+' '+col.label+' ('+col.tasks.length+')</div>';
  html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:6px;">';
  col.tasks.forEach(function(t) {
    var title = t.title || '—';
    var badge = t.companyId ? '<span style="font-size:9px;background:var(--bg-secondary);padding:1px 5px;border-radius:3px;color:var(--text-muted);margin-left:6px;">'+t.companyId+'</span>' : '';
    html += '<div style="font-size:12px;color:var(--text-secondary);padding:4px 8px;background:var(--bg-secondary);border-radius:6px;border-left:3px solid '+col.color+';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="'+(t.title||'').replace(/"/g,'&quot;')+'">'+title+badge+'</div>';
  });
  html += '</div>';
  sec.innerHTML = html;
}

// MC auto-refresh every 30s
if (!_mcRefreshTimer) {
  _mcRefreshTimer = setInterval(function() {
    if (document.querySelector('.nav-tab.active')?.textContent?.trim() === 'Overview') loadMCTasks();
  }, 30000);
}

// ===== Health Checks =====
async function loadHealth() {
  try {
    var data = await fetch('/api/health').then(r => r.json());
    data.checks.forEach(function(c) {
      var dotEl = document.getElementById('health-dot-' + c.id);
      var detailEl = document.getElementById('health-detail-' + c.id);
      var itemEl = document.getElementById('health-' + c.id);
      if (dotEl) { dotEl.className = 'health-dot ' + c.color; }
      if (detailEl) { detailEl.textContent = c.detail; }
      if (itemEl) { itemEl.className = 'health-item ' + c.status; }
    });
  } catch(e) {}
}

// Health SSE auto-refresh
var healthStream = null;
function startHealthStream() {
  if (healthStream) healthStream.close();
  healthStream = new EventSource('/api/health-stream' + (localStorage.getItem('clawmetry-token') ? '?token=' + encodeURIComponent(localStorage.getItem('clawmetry-token')) : ''));
  healthStream.onmessage = function(e) {
    try {
      var data = JSON.parse(e.data);
      data.checks.forEach(function(c) {
        var dotEl = document.getElementById('health-dot-' + c.id);
        var detailEl = document.getElementById('health-detail-' + c.id);
        var itemEl = document.getElementById('health-' + c.id);
        if (dotEl) { dotEl.className = 'health-dot ' + c.color; }
        if (detailEl) { detailEl.textContent = c.detail; }
        if (itemEl) { itemEl.className = 'health-item ' + c.status; }
      });
    } catch(ex) {}
  };
  healthStream.onerror = function() { setTimeout(startHealthStream, 30000); };
}

// ===== System Health Panel =====
async function loadSystemHealth() {
  try {
    var d = await fetch('/api/system-health').then(function(r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
    var services = Array.isArray(d.services) ? d.services : [];
    var disks = Array.isArray(d.disks) ? d.disks : [];
    var crons = (d.crons && typeof d.crons === 'object') ? d.crons : {enabled: 0, ok24h: 0, failed: []};
    var subagents = (d.subagents && typeof d.subagents === 'object') ? d.subagents : {runs: 0, successPct: 0};

    // Services
    var shtml = '';
    services.forEach(function(s) {
      var dot = s.up ? '🟢' : '🔴';
      shtml += '<div style="display:flex;align-items:center;gap:6px;padding:8px 14px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);font-size:13px;">'
        + dot + ' <span style="font-weight:600;color:var(--text-primary);">' + s.name + '</span>'
        + '<span style="color:var(--text-muted);font-size:11px;margin-left:auto;">:' + s.port + '</span></div>';
    });
    if (!shtml) {
      shtml = '<div style="padding:8px 10px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;font-size:12px;color:var(--text-muted);">No service data available</div>';
    }
    document.getElementById('sh-services').innerHTML = shtml;

    // Disks
    var dhtml = '';
    disks.forEach(function(dk) {
      var barColor = dk.pct > 90 ? '#dc2626' : (dk.pct > 75 ? '#d97706' : '#16a34a');
      dhtml += '<div style="margin-bottom:10px;">'
        + '<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">'
        + '<span style="font-weight:600;color:var(--text-primary);">' + dk.mount + '</span>'
        + '<span style="color:var(--text-muted);">' + dk.used_gb + ' / ' + dk.total_gb + ' GB (' + dk.pct + '%)</span></div>'
        + '<div style="background:var(--bg-secondary);border-radius:6px;height:10px;overflow:hidden;border:1px solid var(--border-secondary);">'
        + '<div style="width:' + dk.pct + '%;height:100%;background:' + barColor + ';border-radius:6px;transition:width 0.5s;"></div>'
        + '</div></div>';
    });
    if (!dhtml) {
      dhtml = '<div style="padding:8px 10px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;font-size:12px;color:var(--text-muted);">No disk data available</div>';
    }
    document.getElementById('sh-disks').innerHTML = dhtml;

    // Crons
    var c = crons;
    var cFailed = Array.isArray(c.failed) ? c.failed : [];
    var chtml = '<div style="display:flex;gap:12px;flex-wrap:wrap;">'
      + '<div style="flex:1;min-width:100px;padding:12px 16px;background:var(--bg-secondary);border-radius:8px;text-align:center;border:1px solid var(--border-secondary);">'
      + '<div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (c.enabled || 0) + '</div>'
      + '<div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">Enabled</div></div>'
      + '<div style="flex:1;min-width:100px;padding:12px 16px;background:var(--bg-secondary);border-radius:8px;text-align:center;border:1px solid var(--border-secondary);">'
      + '<div style="font-size:24px;font-weight:700;color:var(--text-success);">' + (c.ok24h || 0) + '</div>'
      + '<div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">OK (24h)</div></div></div>';
    if (cFailed.length > 0) {
      chtml += '<div style="margin-top:8px;padding:10px 14px;background:var(--bg-error);border:1px solid rgba(220,38,38,0.2);border-radius:8px;font-size:12px;color:var(--text-error);">';
      cFailed.forEach(function(f) { chtml += '<div>❌ ' + f + '</div>'; });
      chtml += '</div>';
    }
    document.getElementById('sh-crons').innerHTML = chtml;

    // Sub-agents
    var sa = subagents;
    var pctColor = sa.successPct >= 100 ? 'var(--text-success)' : (sa.successPct > 80 ? 'var(--text-warning)' : 'var(--text-error)');
    var sahtml = '<div style="display:flex;gap:12px;flex-wrap:wrap;">'
      + '<div style="flex:1;min-width:100px;padding:12px 16px;background:var(--bg-secondary);border-radius:8px;text-align:center;border:1px solid var(--border-secondary);">'
      + '<div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + sa.runs + '</div>'
      + '<div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">Runs</div></div>'
      + '<div style="flex:1;min-width:100px;padding:12px 16px;background:var(--bg-secondary);border-radius:8px;text-align:center;border:1px solid var(--border-secondary);">'
      + '<div style="font-size:24px;font-weight:700;color:' + pctColor + ';">' + sa.successPct + '%</div>'
      + '<div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">Success</div></div></div>';
    document.getElementById('sh-subagents').innerHTML = sahtml;
    return true;
  } catch(e) {
    console.error('System health load failed', e);
    var msg = '<div style="padding:8px 10px;background:var(--bg-secondary);border:1px solid var(--border-secondary);border-radius:8px;font-size:12px;color:var(--text-muted);">Unable to load right now</div>';
    document.getElementById('sh-services').innerHTML = msg;
    document.getElementById('sh-disks').innerHTML = msg;
    document.getElementById('sh-crons').innerHTML = msg;
    document.getElementById('sh-subagents').innerHTML = msg;
    return false;
  }
}
function startSystemHealthRefresh() {
  loadSystemHealth();
  if (window._sysHealthTimer) clearInterval(window._sysHealthTimer);
  window._sysHealthTimer = setInterval(loadSystemHealth, 30000);
}

// ===== Activity Heatmap =====
async function loadHeatmap() {
  try {
    var data = await fetch('/api/heatmap').then(r => r.json());
    var grid = document.getElementById('heatmap-grid');
    var maxVal = Math.max(1, data.max);
    var html = '<div class="heatmap-label"></div>';
    for (var h = 0; h < 24; h++) { html += '<div class="heatmap-hour-label">' + (h < 10 ? '0' : '') + h + '</div>'; }
    data.days.forEach(function(day) {
      html += '<div class="heatmap-label">' + day.label + '</div>';
      day.hours.forEach(function(val, hi) {
        var intensity = val / maxVal;
        var color;
        if (val === 0) color = '#12122a';
        else if (intensity < 0.25) color = '#1a3a2a';
        else if (intensity < 0.5) color = '#2a6a3a';
        else if (intensity < 0.75) color = '#4a9a2a';
        else color = '#6adb3a';
        html += '<div class="heatmap-cell" style="background:' + color + ';" title="' + day.label + ' ' + (hi < 10 ? '0' : '') + hi + ':00 - ' + val + ' events"></div>';
      });
    });
    grid.innerHTML = html;
    var legend = document.getElementById('heatmap-legend');
    legend.innerHTML = 'Less <div class="heatmap-legend-cell" style="background:#12122a"></div><div class="heatmap-legend-cell" style="background:#1a3a2a"></div><div class="heatmap-legend-cell" style="background:#2a6a3a"></div><div class="heatmap-legend-cell" style="background:#4a9a2a"></div><div class="heatmap-legend-cell" style="background:#6adb3a"></div> More';
  } catch(e) {
    document.getElementById('heatmap-grid').innerHTML = '<span style="color:#555">No activity data</span>';
  }
}

// ===== Usage / Token Tracking =====
async function loadUsage() {
  try {
    var data = await fetch('/api/usage').then(r => r.json());
    function fmtTokens(n) { return n >= 1000000 ? (n/1000000).toFixed(1) + 'M' : n >= 1000 ? (n/1000).toFixed(0) + 'K' : String(n); }
    function fmtCost(c) { return c >= 0.01 ? '$' + c.toFixed(2) : c > 0 ? '<$0.01' : '$0.00'; }
    document.getElementById('usage-today').textContent = fmtTokens(data.today);
    document.getElementById('usage-today-cost').textContent = '≈ ' + fmtCost(data.todayCost);
    document.getElementById('usage-week').textContent = fmtTokens(data.week);
    document.getElementById('usage-week-cost').textContent = '≈ ' + fmtCost(data.weekCost);
    document.getElementById('usage-month').textContent = fmtTokens(data.month);
    document.getElementById('usage-month-cost').textContent = '≈ ' + fmtCost(data.monthCost);
    
    // Display cost warnings
    displayCostWarnings(data.warnings || []);
    
    // Display trend analysis
    displayTrendAnalysis(data.trend || {});
    // Bar chart
    var maxTokens = Math.max.apply(null, data.days.map(function(d){return d.tokens;})) || 1;
    var chartHtml = '';
    data.days.forEach(function(d) {
      var pct = Math.max(1, (d.tokens / maxTokens) * 100);
      var label = d.date.substring(5);
      var val = d.tokens >= 1000 ? (d.tokens/1000).toFixed(0) + 'K' : d.tokens;
      chartHtml += '<div class="usage-bar-wrap"><div class="usage-bar" style="height:' + pct + '%"><div class="usage-bar-value">' + (d.tokens > 0 ? val : '') + '</div></div><div class="usage-bar-label">' + label + '</div></div>';
    });
    document.getElementById('usage-chart').innerHTML = chartHtml;
    // Cost table
    var costLabel = data.source === 'otlp' ? 'Cost' : 'Est. Cost';
    var tableHtml = '<thead><tr><th>Period</th><th>Tokens</th><th>' + costLabel + '</th></tr></thead><tbody>';
    tableHtml += '<tr><td>Today</td><td>' + fmtTokens(data.today) + '</td><td>' + fmtCost(data.todayCost) + '</td></tr>';
    tableHtml += '<tr><td>This Week</td><td>' + fmtTokens(data.week) + '</td><td>' + fmtCost(data.weekCost) + '</td></tr>';
    tableHtml += '<tr><td>This Month</td><td>' + fmtTokens(data.month) + '</td><td>' + fmtCost(data.monthCost) + '</td></tr>';
    tableHtml += '</tbody>';
    document.getElementById('usage-cost-table').innerHTML = tableHtml;
    // OTLP-specific sections
    var otelExtra = document.getElementById('otel-extra-sections');
    if (data.source === 'otlp') {
      otelExtra.style.display = '';
      var runEl = document.getElementById('usage-avg-run');
      if (runEl) runEl.textContent = data.avgRunMs > 0 ? (data.avgRunMs > 1000 ? (data.avgRunMs/1000).toFixed(1) + 's' : data.avgRunMs.toFixed(0) + 'ms') : '—';
      var msgEl = document.getElementById('usage-msg-count');
      if (msgEl) msgEl.textContent = data.messageCount || '0';
      // Model breakdown table
      if (data.modelBreakdown && data.modelBreakdown.length > 0) {
        var mHtml = '<thead><tr><th>Model</th><th>Tokens</th></tr></thead><tbody>';
        data.modelBreakdown.forEach(function(m) {
          mHtml += '<tr><td><span class="badge model">' + escHtml(m.model) + '</span></td><td>' + fmtTokens(m.tokens) + '</td></tr>';
        });
        mHtml += '</tbody>';
        document.getElementById('usage-model-table').innerHTML = mHtml;
      }
    } else {
      otelExtra.style.display = 'none';
    }
  } catch(e) {
    document.getElementById('usage-chart').innerHTML = '<span style="color:#555">No usage data available</span>';
  }
}

function displayCostWarnings(warnings) {
  var container = document.getElementById('cost-warnings');
  if (!warnings || warnings.length === 0) {
    container.style.display = 'none';
    return;
  }
  
  var html = '';
  warnings.forEach(function(w) {
    var icon = w.level === 'error' ? '🚨' : '⚠️';
    html += '<div class="cost-warning ' + w.level + '">';
    html += '<div class="cost-warning-icon">' + icon + '</div>';
    html += '<div class="cost-warning-message">' + escHtml(w.message) + '</div>';
    html += '</div>';
  });
  
  container.innerHTML = html;
  container.style.display = 'block';
}

function displayTrendAnalysis(trend) {
  var card = document.getElementById('trend-card');
  if (!trend || trend.trend === 'insufficient_data') {
    card.style.display = 'none';
    return;
  }
  
  var directionEl = document.getElementById('trend-direction');
  var predictionEl = document.getElementById('trend-prediction');
  
  var emoji = trend.trend === 'increasing' ? '📈' : trend.trend === 'decreasing' ? '📉' : '➡️';
  directionEl.textContent = emoji + ' ' + trend.trend.charAt(0).toUpperCase() + trend.trend.slice(1);
  
  if (trend.dailyAvg && trend.monthlyPrediction) {
    var dailyAvg = trend.dailyAvg >= 1000 ? (trend.dailyAvg/1000).toFixed(0) + 'K' : trend.dailyAvg;
    var monthlyPred = trend.monthlyPrediction >= 1000000 ? (trend.monthlyPrediction/1000000).toFixed(1) + 'M' : 
                      trend.monthlyPrediction >= 1000 ? (trend.monthlyPrediction/1000).toFixed(0) + 'K' : trend.monthlyPrediction;
    predictionEl.textContent = dailyAvg + '/day avg, ~' + monthlyPred + '/month projected';
  } else {
    predictionEl.textContent = 'Analyzing usage patterns...';
  }
  
  card.style.display = 'block';
}

function exportUsageData() {
  // Trigger CSV download
  window.open('/api/usage/export', '_blank');
}

// ===== Transcripts =====
async function loadTranscripts() {
  try {
    var data = await fetch('/api/transcripts').then(r => r.json());
    var html = '';
    data.transcripts.forEach(function(t) {
      html += '<div class="transcript-item" onclick="viewTranscript(\'' + escHtml(t.id) + '\')">';
      html += '<div><div class="transcript-name">' + escHtml(t.name) + '</div>';
      html += '<div class="transcript-meta-row">';
      html += '<span>' + t.messages + ' messages</span>';
      html += '<span>' + (t.size > 1024 ? (t.size/1024).toFixed(1) + ' KB' : t.size + ' B') + '</span>';
      html += '<span>' + timeAgo(t.modified) + '</span>';
      html += '</div></div>';
      html += '<span style="color:#444;font-size:18px;">▸</span>';
      html += '</div>';
    });
    document.getElementById('transcript-list').innerHTML = html || '<div style="padding:16px;color:#666;">No transcript files found</div>';
    document.getElementById('transcript-list').style.display = '';
    document.getElementById('transcript-viewer').style.display = 'none';
    document.getElementById('transcript-back-btn').style.display = 'none';
  } catch(e) {
    document.getElementById('transcript-list').innerHTML = '<div style="padding:16px;color:#666;">Failed to load transcripts</div>';
  }
}

function showTranscriptList() {
  document.getElementById('transcript-list').style.display = '';
  document.getElementById('transcript-viewer').style.display = 'none';
  document.getElementById('transcript-back-btn').style.display = 'none';
}

async function viewTranscript(sessionId) {
  document.getElementById('transcript-list').style.display = 'none';
  document.getElementById('transcript-viewer').style.display = '';
  document.getElementById('transcript-back-btn').style.display = '';
  document.getElementById('transcript-messages').innerHTML = '<div style="padding:20px;color:#666;">Loading transcript...</div>';
  try {
    var data = await fetch('/api/transcript/' + encodeURIComponent(sessionId)).then(r => r.json());
    // Metadata
    var metaHtml = '<div class="stat-row"><span class="stat-label">Session</span><span class="stat-val">' + escHtml(data.name) + '</span></div>';
    metaHtml += '<div class="stat-row"><span class="stat-label">Messages</span><span class="stat-val">' + data.messageCount + '</span></div>';
    if (data.model) metaHtml += '<div class="stat-row"><span class="stat-label">Model</span><span class="stat-val"><span class="badge model">' + escHtml(data.model) + '</span></span></div>';
    if (data.totalTokens) metaHtml += '<div class="stat-row"><span class="stat-label">Tokens</span><span class="stat-val"><span class="badge tokens">' + (data.totalTokens/1000).toFixed(0) + 'K</span></span></div>';
    if (data.duration) metaHtml += '<div class="stat-row"><span class="stat-label">Duration</span><span class="stat-val">' + data.duration + '</span></div>';
    document.getElementById('transcript-meta').innerHTML = metaHtml;
    // Messages
    var msgsHtml = '';
    data.messages.forEach(function(m, idx) {
      var role = m.role || 'unknown';
      var cls = role === 'user' ? 'user' : role === 'assistant' ? 'assistant' : role === 'system' ? 'system' : 'tool';
      var content = m.content || '';
      var needsTruncate = content.length > 800;
      var displayContent = needsTruncate ? content.substring(0, 800) : content;
      msgsHtml += '<div class="chat-msg ' + cls + '">';
      msgsHtml += '<div class="chat-role">' + escHtml(role) + '</div>';
      if (needsTruncate) {
        msgsHtml += '<div class="chat-content-truncated" id="msg-' + idx + '-short">' + escHtml(displayContent) + '</div>';
        msgsHtml += '<div id="msg-' + idx + '-full" style="display:none;white-space:pre-wrap;">' + escHtml(content) + '</div>';
        msgsHtml += '<div class="chat-expand" onclick="toggleMsg(' + idx + ')">Show more (' + content.length + ' chars)</div>';
      } else {
        msgsHtml += '<div style="white-space:pre-wrap;">' + escHtml(content) + '</div>';
      }
      if (m.timestamp) msgsHtml += '<div class="chat-ts">' + new Date(m.timestamp).toLocaleString() + '</div>';
      msgsHtml += '</div>';
    });
    document.getElementById('transcript-messages').innerHTML = msgsHtml || '<div style="color:#555;padding:16px;">No messages in this transcript</div>';
  } catch(e) {
    document.getElementById('transcript-messages').innerHTML = '<div style="color:#e74c3c;padding:16px;">Failed to load transcript</div>';
  }
}

function toggleMsg(idx) {
  var short = document.getElementById('msg-' + idx + '-short');
  var full = document.getElementById('msg-' + idx + '-full');
  if (short.style.display === 'none') {
    short.style.display = '';
    full.style.display = 'none';
    short.nextElementSibling.nextElementSibling.textContent = 'Show more';
  } else {
    short.style.display = 'none';
    full.style.display = '';
    event.target.textContent = 'Show less';
  }
}

function startOverviewRefresh() {
  loadAll();
  if (window._overviewTimer) clearInterval(window._overviewTimer);
  window._overviewTimer = setInterval(loadAll, 10000);
}

// Real-time log stream via SSE
var logStream = null;
var streamBuffer = [];
var MAX_STREAM_LINES = 500;

function startLogStream() {
  if (logStream) logStream.close();
  streamBuffer = [];
  logStream = new EventSource('/api/logs-stream' + (localStorage.getItem('clawmetry-token') ? '?token=' + encodeURIComponent(localStorage.getItem('clawmetry-token')) : ''));
  logStream.onmessage = function(e) {
    var data = JSON.parse(e.data);
    streamBuffer.push(data.line);
    if (streamBuffer.length > MAX_STREAM_LINES) streamBuffer.shift();
    appendLogLine('ov-logs', data.line);
    appendLogLine('logs-full', data.line);
    processFlowEvent(data.line);
    document.getElementById('refresh-time').textContent = 'Live • ' + new Date().toLocaleTimeString();
  };
  logStream.onerror = function() {
    setTimeout(startLogStream, 5000);
  };
}

function parseLogLine(line) {
  try {
    var obj = JSON.parse(line);
    var ts = '';
    if (obj.time || (obj._meta && obj._meta.date)) {
      var d = new Date(obj.time || obj._meta.date);
      ts = d.toLocaleTimeString('en-GB', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
    }
    var level = (obj.logLevelName || obj.level || 'info').toLowerCase();
    var cls = 'info';
    if (level === 'error' || level === 'fatal') cls = 'err';
    else if (level === 'warn' || level === 'warning') cls = 'warn';
    else if (level === 'debug') cls = 'msg';
    var msg = obj.msg || obj.message || obj.name || '';
    var extras = [];
    if (obj["0"]) extras.push(obj["0"]);
    if (obj["1"]) extras.push(obj["1"]);
    var display;
    if (msg && extras.length) display = msg + ' | ' + extras.join(' ');
    else if (extras.length) display = extras.join(' ');
    else if (!msg) display = line.substring(0, 200);
    else display = msg;
    if (ts) display = '<span class="ts">' + ts + '</span> ' + escHtml(display);
    else display = escHtml(display);
    return {cls: cls, html: display};
  } catch(e) {
    var cls = 'msg';
    if (line.includes('Error') || line.includes('failed')) cls = 'err';
    else if (line.includes('WARN')) cls = 'warn';
    else if (line.includes('run start') || line.includes('inbound')) cls = 'info';
    return {cls: cls, html: escHtml(line.substring(0, 300))};
  }
}

function appendLogLine(elId, line) {
  var el = document.getElementById(elId);
  if (!el) return;
  var parsed = parseLogLine(line);
  var div = document.createElement('div');
  div.className = 'log-line';
  div.innerHTML = '<span class="' + parsed.cls + '">' + parsed.html + '</span>';
  el.appendChild(div);
  while (el.children.length > MAX_STREAM_LINES) el.removeChild(el.firstChild);
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 150) {
    el.scrollTop = el.scrollHeight;
  }
}

// ===== Flow Visualization Engine =====
var flowStats = { messages: 0, events: 0, activeTools: {}, msgTimestamps: [] };
var flowInitDone = false;

function hideUnconfiguredChannels(svgRoot) {
  // Hide channel nodes and their paths for unconfigured channels
  var channelMap = {
    'telegram': { node: 'node-telegram', paths: ['path-human-tg', 'path-tg-gw'] },
    'signal':   { node: 'node-signal',   paths: ['path-human-sig', 'path-sig-gw'] },
    'whatsapp': { node: 'node-whatsapp', paths: ['path-human-wa', 'path-wa-gw'] }
  };
  fetch('/api/channels').then(function(r){return r.json();}).then(function(d) {
    var active = d.channels || ['telegram', 'signal', 'whatsapp'];
    var allChannels = ['telegram', 'signal', 'whatsapp'];
    var hiddenCount = 0;
    allChannels.forEach(function(ch) {
      if (active.indexOf(ch) === -1) {
        hiddenCount++;
        var info = channelMap[ch];
        var node = svgRoot.getElementById ? svgRoot.getElementById(info.node) : svgRoot.querySelector('#' + info.node);
        if (node) node.style.display = 'none';
        info.paths.forEach(function(pid) {
          var p = svgRoot.getElementById ? svgRoot.getElementById(pid) : svgRoot.querySelector('#' + pid);
          if (p) p.style.display = 'none';
        });
      }
    });
    // Shift remaining visible channel nodes up to fill gaps
    if (hiddenCount > 0) {
      var visibleChannels = allChannels.filter(function(ch) { return active.indexOf(ch) !== -1; });
      var yPositions = [120, 175, 230]; // Evenly spaced positions for 1-3 channels
      if (visibleChannels.length === 1) yPositions = [175];
      else if (visibleChannels.length === 2) yPositions = [130, 210];
      visibleChannels.forEach(function(ch, i) {
        var info = channelMap[ch];
        var node = svgRoot.getElementById ? svgRoot.getElementById(info.node) : svgRoot.querySelector('#' + info.node);
        if (!node) return;
        var rect = node.querySelector('rect');
        var text = node.querySelector('text');
        var targetY = yPositions[i];
        if (rect) { rect.setAttribute('y', targetY - 20); }
        if (text) { text.setAttribute('y', targetY + 5); }
        // Update paths from human to channel and channel to gateway
        var humanPath = svgRoot.getElementById ? svgRoot.getElementById(info.paths[0]) : svgRoot.querySelector('#' + info.paths[0]);
        if (humanPath) {
          humanPath.setAttribute('d', 'M 60 56 C 60 ' + (targetY - 30) + ', 65 ' + (targetY - 15) + ', 75 ' + (targetY - 20));
        }
        var gwPath = svgRoot.getElementById ? svgRoot.getElementById(info.paths[1]) : svgRoot.querySelector('#' + info.paths[1]);
        if (gwPath) {
          gwPath.setAttribute('d', 'M 130 ' + targetY + ' C 150 ' + targetY + ', 160 183, 180 183');
        }
      });
    }
  }).catch(function(){});
}

function initFlow() {
  if (flowInitDone) return;
  flowInitDone = true;
  
  // Performance: Reduce update frequency on mobile
  var updateInterval = window.innerWidth < 768 ? 3000 : 2000;

  // Hide unconfigured channels in the flow SVG
  hideUnconfiguredChannels(document);
  
  fetch('/api/overview').then(function(r){return r.json();}).then(async function(d) {
    if (!d.model || d.model === 'unknown') {
      var fm = await resolvePrimaryModelFallback();
      if (fm && fm !== 'unknown') d.model = fm;
    }
    if (d.model) applyBrainModelToAll(d.model);
    var tok = document.getElementById('flow-tokens');
    if (tok) tok.textContent = (d.mainTokens / 1000).toFixed(0) + 'K';
    
    // Add visual hierarchy hints
    setTimeout(function() {
      enhanceArchitectureClarity();
    }, 1000);
  }).catch(function(){});
  
  setInterval(updateFlowStats, updateInterval);
}

// Add subtle animation to help users understand the flow
function enhanceArchitectureClarity() {
  // Gentle pulse on key nodes to show importance hierarchy
  var keyNodes = ['node-human', 'node-gateway', 'node-brain'];
  keyNodes.forEach(function(nodeId, index) {
    setTimeout(function() {
      var node = document.getElementById(nodeId);
      if (node) {
        node.style.animation = 'none';
        setTimeout(function() {
          node.style.animation = '';
        }, 100);
      }
    }, index * 800);
  });
  
  // Highlight the main message flow path briefly
  var paths = ['path-human-tg', 'path-tg-gw', 'path-gw-brain'];
  paths.forEach(function(pathId, index) {
    setTimeout(function() {
      var path = document.getElementById(pathId);
      if (path) {
        path.style.opacity = '0.8';
        path.style.strokeWidth = '3';
        path.style.transition = 'all 0.5s ease';
        setTimeout(function() {
          path.style.opacity = '';
          path.style.strokeWidth = '';
        }, 1500);
      }
    }, index * 200);
  });
}

function updateFlowStats() {
  var now = Date.now();
  flowStats.msgTimestamps = flowStats.msgTimestamps.filter(function(t){return now - t < 60000;});
  var el1 = document.getElementById('flow-msg-rate');
  if (el1) el1.textContent = flowStats.msgTimestamps.length;
  var el2 = document.getElementById('flow-event-count');
  if (el2) el2.textContent = flowStats.events;
  var names = Object.keys(flowStats.activeTools).filter(function(k){return flowStats.activeTools[k];});
  var el3 = document.getElementById('flow-active-tools');
  if (el3) el3.textContent = names.length > 0 ? names.join(', ') : '\u2014';
  if (flowStats.events % 15 === 0) {
    fetch('/api/overview').then(function(r){return r.json();}).then(function(d) {
      var tok = document.getElementById('flow-tokens');
      if (tok) tok.textContent = (d.mainTokens / 1000).toFixed(0) + 'K';
    }).catch(function(){});
  }
}

// Enhanced particle animation with performance optimizations and better mobile support
var particlePool = [];
var trailPool = [];
var maxParticles = window.innerWidth < 768 ? 3 : 8; // Limit particles on mobile
var trailInterval = window.innerWidth < 768 ? 8 : 4; // Fewer trails on mobile

function getPooledParticle(isTrail) {
  var pool = isTrail ? trailPool : particlePool;
  if (pool.length > 0) return pool.pop();
  var elem = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  elem.setAttribute('r', isTrail ? '2' : '5');
  return elem;
}

function returnToPool(elem, isTrail) {
  var pool = isTrail ? trailPool : particlePool;
  elem.style.opacity = '0';
  elem.style.transform = '';
  if (pool.length < 20) pool.push(elem); // Pool size limit
  else if (elem.parentNode) elem.parentNode.removeChild(elem);
}

function animateParticle(pathId, color, duration, reverse) {
  var path = document.getElementById(pathId);
  if (!path) return;
  var svg = document.getElementById('flow-svg');
  if (!svg) return;
  
  // Skip if too many particles (performance)
  var activeParticles = svg.querySelectorAll('circle[data-particle]').length;
  if (activeParticles > maxParticles) return;
  
  var len = path.getTotalLength();
  var particle = getPooledParticle(false);
  particle.setAttribute('data-particle', 'true');
  particle.setAttribute('fill', color);
  particle.style.filter = 'drop-shadow(0 0 8px ' + color + ')';
  particle.style.opacity = '1';
  svg.appendChild(particle);
  
  var glowCls = color === '#60a0ff' ? 'glow-blue' : color === '#f0c040' ? 'glow-yellow' : color === '#50e080' ? 'glow-green' : color === '#40a0b0' ? 'glow-cyan' : color === '#c0a0ff' ? 'glow-purple' : 'glow-red';
  path.classList.add(glowCls);
  
  var startT = performance.now();
  var trailN = 0;
  var trailElements = [];
  
  function step(now) {
    var t = Math.min((now - startT) / duration, 1);
    var dist = reverse ? (1 - t) * len : t * len;
    
    try {
      var pt = path.getPointAtLength(dist);
      particle.setAttribute('cx', pt.x);
      particle.setAttribute('cy', pt.y);
    } catch(e) { 
      cleanup();
      return; 
    }
    
    // Create trail less frequently, and only if not too many already
    if (trailN++ % trailInterval === 0 && trailElements.length < 6) {
      var tr = getPooledParticle(true);
      tr.setAttribute('cx', particle.getAttribute('cx'));
      tr.setAttribute('cy', particle.getAttribute('cy'));
      tr.setAttribute('fill', color);
      tr.style.opacity = '0.6';
      tr.style.filter = 'blur(0.5px)';
      svg.insertBefore(tr, particle);
      trailElements.push(tr);
      
      // Fade trail with CSS transition instead of JS animation
      setTimeout(function() {
        tr.style.transition = 'opacity 400ms ease-out, transform 400ms ease-out';
        tr.style.opacity = '0';
        tr.style.transform = 'scale(0.3)';
        setTimeout(function() { 
          if (tr.parentNode) tr.parentNode.removeChild(tr);
          returnToPool(tr, true);
        }, 450);
      }, 50);
    }
    
    if (t < 1) {
      requestAnimationFrame(step);
    } else {
      cleanup();
    }
  }
  
  function cleanup() {
    if (particle.parentNode) particle.parentNode.removeChild(particle);
    returnToPool(particle, false);
    setTimeout(function() { 
      path.classList.remove(glowCls); 
    }, 400);
  }
  
  requestAnimationFrame(step);
}

function highlightNode(nodeId, dur) {
  var node = document.getElementById(nodeId);
  if (!node) return;
  node.classList.add('active');
  setTimeout(function() { node.classList.remove('active'); }, dur || 2000);
}

function triggerInbound(ch) {
  ch = ch || 'tg';
  var chNodeId = ch === 'tg' ? 'node-telegram' : ch === 'sig' ? 'node-signal' : 'node-whatsapp';
  highlightNode(chNodeId, 3000);
  animateParticle('path-human-' + ch, '#c0a0ff', 550, false);
  highlightNode('node-human', 2200);
  setTimeout(function() {
    animateParticle('path-' + ch + '-gw', '#60a0ff', 800, false);
    highlightNode('node-gateway', 2000);
  }, 400);
  setTimeout(function() {
    animateParticle('path-gw-brain', '#60a0ff', 600, false);
    highlightNode('node-brain', 2500);
  }, 1050);
  setTimeout(function() {
    animateParticle('path-brain-session', '#60a0ff', 400, false);
    highlightNode('node-session', 1500);
  }, 1550);
  setTimeout(function() { triggerInfraNetwork(); }, 300);
}

function triggerToolCall(toolName) {
  var pathId = 'path-brain-' + toolName;
  animateParticle(pathId, '#f0c040', 700, false);
  highlightNode('node-' + toolName, 2500);
  setTimeout(function() {
    animateParticle(pathId, '#f0c040', 700, true);
  }, 900);
  var ind = document.getElementById('ind-' + toolName);
  if (ind) { ind.classList.add('active'); setTimeout(function() { ind.classList.remove('active'); }, 4000); }
  flowStats.activeTools[toolName] = true;
  setTimeout(function() { delete flowStats.activeTools[toolName]; }, 5000);
  if (toolName === 'exec') {
    setTimeout(function() { triggerInfraMachine(); triggerInfraRuntime(); }, 400);
  } else if (toolName === 'browser' || toolName === 'search') {
    setTimeout(function() { triggerInfraNetwork(); }, 400);
  } else if (toolName === 'memory') {
    setTimeout(function() { triggerInfraStorage(); }, 400);
  }
}

function triggerOutbound(ch) {
  ch = ch || 'tg';
  animateParticle('path-gw-brain', '#50e080', 600, true);
  highlightNode('node-gateway', 2000);
  setTimeout(function() {
    animateParticle('path-' + ch + '-gw', '#50e080', 800, true);
  }, 500);
  setTimeout(function() {
    animateParticle('path-human-' + ch, '#50e080', 550, true);
    highlightNode('node-human', 1800);
  }, 1200);
  setTimeout(function() { triggerInfraNetwork(); }, 200);
}

function triggerError() {
  var brain = document.getElementById('node-brain');
  if (!brain) return;
  var r = brain.querySelector('rect');
  if (r) { r.style.stroke = '#e04040'; setTimeout(function() { r.style.stroke = '#f0c040'; }, 2500); }
}

function triggerInfraNetwork() {
  animateParticle('path-gw-network', '#40a0b0', 1200, false);
  highlightNode('node-network', 2500);
}
function triggerInfraRuntime() {
  animateParticle('path-brain-runtime', '#40a0b0', 1000, false);
  highlightNode('node-runtime', 2200);
}
function triggerInfraMachine() {
  animateParticle('path-brain-machine', '#40a0b0', 1000, false);
  highlightNode('node-machine', 2200);
}
function triggerInfraStorage() {
  animateParticle('path-memory-storage', '#40a0b0', 700, false);
  highlightNode('node-storage', 2000);
}

// Live feed for Flow tab - shows recent events in plain English
var _flowFeedItems = [];
var _flowFeedMax = 30;
function addFlowFeedItem(text, color) {
  var now = new Date();
  var time = now.toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
  _flowFeedItems.push({time: time, text: text, color: color || '#888'});
  if (_flowFeedItems.length > _flowFeedMax) _flowFeedItems.shift();
  var el = document.getElementById('flow-live-feed');
  if (!el) return;
  var html = '';
  for (var i = _flowFeedItems.length - 1; i >= Math.max(0, _flowFeedItems.length - 15); i--) {
    var item = _flowFeedItems[i];
    html += '<div><span style="color:#555;">' + item.time + '</span> <span style="color:' + item.color + ';">' + item.text + '</span></div>';
  }
  el.innerHTML = html;
  var countEl = document.getElementById('flow-feed-count');
  if (countEl) countEl.textContent = flowStats.events + ' events';
}

var flowThrottles = {};
function processFlowEvent(line) {
  flowStats.events++;
  var now = Date.now();
  var msg = '', level = '';
  try {
    var obj = JSON.parse(line);
    msg = ((obj.msg || '') + ' ' + (obj.message || '') + ' ' + (obj.name || '') + ' ' + (obj['0'] || '') + ' ' + (obj['1'] || '')).toLowerCase();
    level = (obj.logLevelName || obj.level || (obj._meta && obj._meta.logLevelName) || '').toLowerCase();
  } catch(e) { msg = line.toLowerCase(); }

  if (level === 'error' || level === 'fatal') { triggerError(); return; }

  if (msg.includes('run start') && msg.includes('messagechannel')) {
    if (now - (flowThrottles['inbound']||0) < 500) return;
    flowThrottles['inbound'] = now;
    var ch = 'tg';
    if (msg.includes('signal')) ch = 'sig';
    else if (msg.includes('whatsapp')) ch = 'wa';
    triggerInbound(ch);
    addFlowFeedItem('📨 New message arrived via ' + (ch === 'tg' ? 'Telegram' : ch === 'wa' ? 'WhatsApp' : 'Signal'), '#c0a0ff');
    flowStats.msgTimestamps.push(now);
    return;
  }
  if (msg.includes('inbound') || msg.includes('dispatching') || msg.includes('message received')) {
    triggerInbound('tg');
    addFlowFeedItem('📨 Incoming message received', '#c0a0ff');
    flowStats.msgTimestamps.push(now);
    return;
  }

  if ((msg.includes('tool start') || msg.includes('tool-call') || msg.includes('tool_use')) && !msg.includes('tool end')) {
    var toolName = '';
    var toolMatch = msg.match(/tool=(\w+)/);
    if (toolMatch) toolName = toolMatch[1].toLowerCase();
    var flowTool = 'exec';
    if (toolName === 'exec' || toolName === 'read' || toolName === 'write' || toolName === 'edit' || toolName === 'process') {
      flowTool = 'exec';
    } else if (toolName.includes('browser') || toolName === 'canvas') {
      flowTool = 'browser';
    } else if (toolName === 'web_search' || toolName === 'web_fetch') {
      flowTool = 'search';
    } else if (toolName === 'cron' || toolName === 'sessions_spawn' || toolName === 'sessions_send') {
      flowTool = 'cron';
    } else if (toolName === 'tts') {
      flowTool = 'tts';
    } else if (toolName === 'memory_search' || toolName === 'memory_get') {
      flowTool = 'memory';
    } else if (toolName === 'message') {
      if (now - (flowThrottles['outbound']||0) < 500) return;
      flowThrottles['outbound'] = now;
      triggerOutbound('tg'); return;
    }
    if (now - (flowThrottles['tool-'+flowTool]||0) < 300) return;
    flowThrottles['tool-'+flowTool] = now;
    var toolNames = {exec:'running a command',browser:'browsing the web',search:'searching the web',cron:'scheduling a task',tts:'generating speech',memory:'accessing memory'};
    addFlowFeedItem('⚡ AI is ' + (toolNames[flowTool] || 'using ' + flowTool), '#f0c040');
    triggerToolCall(flowTool); return;
  }

  var toolMap = {
    'exec': ['exec','shell','command'],
    'browser': ['browser','screenshot','snapshot'],
    'search': ['web_search','web_fetch'],
    'cron': ['cron','schedule'],
    'tts': ['tts','speech','voice'],
    'memory': ['memory_search','memory_get']
  };
  if (msg.includes('tool') || msg.includes('invoke') || msg.includes('calling')) {
    for (var t in toolMap) {
      for (var i = 0; i < toolMap[t].length; i++) {
        if (msg.includes(toolMap[t][i])) { triggerToolCall(t); return; }
      }
    }
  }

  if (msg.includes('response sent') || msg.includes('completion') || msg.includes('reply sent') || msg.includes('deliver') || (msg.includes('lane task done') && msg.includes('main'))) {
    var ch = 'tg';
    if (msg.includes('signal')) ch = 'sig';
    else if (msg.includes('whatsapp')) ch = 'wa';
    addFlowFeedItem('✉️ AI sent a reply via ' + (ch === 'tg' ? 'Telegram' : ch === 'wa' ? 'WhatsApp' : 'Signal'), '#50e080');
    triggerOutbound(ch);
    return;
  }

  // Catch embedded run lifecycle events
  if (msg.includes('embedded run start') && !msg.includes('tool') && !msg.includes('prompt') && !msg.includes('agent')) {
    if (now - (flowThrottles['run-start']||0) < 1000) return;
    flowThrottles['run-start'] = now;
    var ch = 'tg';
    if (msg.includes('messagechannel=signal')) ch = 'sig';
    else if (msg.includes('messagechannel=whatsapp')) ch = 'wa';
    else if (msg.includes('messagechannel=heartbeat')) { addFlowFeedItem('💓 Heartbeat run started', '#4a7090'); return; }
    addFlowFeedItem('🧠 AI run started (' + (ch === 'tg' ? 'Telegram' : ch === 'wa' ? 'WhatsApp' : 'Signal') + ')', '#a080f0');
    triggerInbound(ch);
    flowStats.msgTimestamps.push(now);
    return;
  }
  if (msg.includes('embedded run agent end') || msg.includes('embedded run prompt end')) {
    if (now - (flowThrottles['run-end']||0) < 1000) return;
    flowThrottles['run-end'] = now;
    addFlowFeedItem('✅ AI processing complete', '#50e080');
    return;
  }
  if (msg.includes('session state') && msg.includes('new=processing')) {
    if (now - (flowThrottles['session-active']||0) < 2000) return;
    flowThrottles['session-active'] = now;
    addFlowFeedItem('⚡ Session activated', '#f0c040');
    return;
  }
  if (msg.includes('lane enqueue') && msg.includes('main')) {
    if (now - (flowThrottles['lane']||0) < 2000) return;
    flowThrottles['lane'] = now;
    addFlowFeedItem('📥 Task queued', '#8090b0');
    return;
  }
  if (msg.includes('tool end') || msg.includes('tool_end')) {
    if (now - (flowThrottles['tool-end']||0) < 300) return;
    flowThrottles['tool-end'] = now;
    addFlowFeedItem('✔️ Tool completed', '#50c070');
    return;
  }
}

// === Overview Split-Screen: Clone flow SVG into overview pane ===
function initOverviewFlow() {
  var srcSvg = document.getElementById('flow-svg');
  var container = document.getElementById('overview-flow-container');
  if (!srcSvg || !container) return;
  // Clone the SVG into the overview pane
  var clone = srcSvg.cloneNode(true);
  clone.id = 'overview-flow-svg';
  clone.style.width = '100%';
  clone.style.height = '100%';
  clone.style.minWidth = '0';
  // Rename defs IDs (filters, patterns, etc.) in clone to avoid duplicate-id conflicts
  var defs = clone.querySelectorAll('filter[id], pattern[id], linearGradient[id], radialGradient[id], clipPath[id], mask[id]');
  defs.forEach(function(f) {
    var oldId = f.id;
    var newId = 'ov-' + oldId;
    f.id = newId;
    // Update all url(#oldId) references in filter, fill, stroke, clip-path, mask attributes
    ['filter','fill','stroke','clip-path','mask'].forEach(function(attr) {
      clone.querySelectorAll('[' + attr + '="url(#' + oldId + ')"]').forEach(function(el) {
        el.setAttribute(attr, 'url(#' + newId + ')');
      });
    });
  });
  // Strip any .active classes captured at clone time so nodes render cleanly
  clone.querySelectorAll('.active').forEach(function(el) { el.classList.remove('active'); });
  // Rename element IDs in clone to avoid getElementById conflicts with original SVG
  clone.querySelectorAll('[id]').forEach(function(el) {
    el.id = 'ov-' + el.id;
  });
  container.innerHTML = '';
  container.appendChild(clone);
  // Hide unconfigured channels in the overview clone too
  // Clone has IDs prefixed with 'ov-', so we use a wrapper approach
  fetch('/api/channels').then(function(r){return r.json();}).then(function(d) {
    var active = d.channels || ['telegram', 'signal', 'whatsapp'];
    var channelMap = {
      'telegram': { node: 'ov-node-telegram', paths: ['ov-path-human-tg', 'ov-path-tg-gw'] },
      'signal':   { node: 'ov-node-signal',   paths: ['ov-path-human-sig', 'ov-path-sig-gw'] },
      'whatsapp': { node: 'ov-node-whatsapp', paths: ['ov-path-human-wa', 'ov-path-wa-gw'] }
    };
    var allChannels = ['telegram', 'signal', 'whatsapp'];
    var hiddenCount = 0;
    allChannels.forEach(function(ch) {
      if (active.indexOf(ch) === -1) {
        hiddenCount++;
        var info = channelMap[ch];
        var node = document.getElementById(info.node);
        if (node) node.style.display = 'none';
        info.paths.forEach(function(pid) {
          var p = document.getElementById(pid);
          if (p) p.style.display = 'none';
        });
      }
    });
    if (hiddenCount > 0) {
      var visibleChannels = allChannels.filter(function(ch) { return active.indexOf(ch) !== -1; });
      var yPositions = visibleChannels.length === 1 ? [175] : visibleChannels.length === 2 ? [130, 210] : [120, 175, 230];
      visibleChannels.forEach(function(ch, i) {
        var info = channelMap[ch];
        var node = document.getElementById(info.node);
        if (!node) return;
        var rect = node.querySelector('rect');
        var text = node.querySelector('text');
        var targetY = yPositions[i];
        if (rect) rect.setAttribute('y', targetY - 20);
        if (text) text.setAttribute('y', targetY + 5);
        var humanPath = document.getElementById(info.paths[0]);
        if (humanPath) humanPath.setAttribute('d', 'M 60 56 C 60 ' + (targetY - 30) + ', 65 ' + (targetY - 15) + ', 75 ' + (targetY - 20));
        var gwPath = document.getElementById(info.paths[1]);
        if (gwPath) gwPath.setAttribute('d', 'M 130 ' + targetY + ' C 150 ' + targetY + ', 160 183, 180 183');
      });
    }
  }).catch(function(){});
}

// === Overview Tasks Panel (right side) ===
var _ovTasksTimer = null;
window._ovExpandedSet = {};  // track which detail panels are open across refreshes

function _ovTimeLabel(agent) {
  var ms = agent.runtimeMs || 0;
  var sec = Math.floor(ms / 1000);
  var min = Math.floor(sec / 60);
  var hr = Math.floor(min / 60);
  if (agent.status === 'active') {
    if (min < 1) return 'Running (' + sec + 's)';
    if (min < 60) return 'Running (' + min + ' min)';
    return 'Running (' + hr + 'h ' + (min % 60) + 'm)';
  }
  if (sec < 60) return 'Finished ' + sec + 's ago';
  if (min < 60) return 'Finished ' + min + ' min ago';
  if (hr < 24) return 'Finished ' + hr + 'h ago';
  return 'Finished ' + Math.floor(hr / 24) + 'd ago';
}

function _ovRenderCard(agent, idx) {
  var isRealFailure = agent.status === 'stale' && agent.abortedLastRun && (agent.outputTokens || 0) === 0;
  var sc = agent.status === 'active' ? 'running' : isRealFailure ? 'failed' : 'complete';
  var taskName = cleanTaskName(agent.displayName);
  var badge = detectProjectBadge(agent.displayName);
  var timeLabel = _ovTimeLabel(agent);
  var detailId = 'ovd2-' + idx;
  var isOpen = !!(window._ovExpandedSet || {})[agent.sessionId];
  var tokTotal = (agent.inputTokens || 0) + (agent.outputTokens || 0);
  var cmdsRun = (agent.recentTools || []).length;

  var h = '';
  // Card with left color bar (via border-left on ov-task-card class)
  h += '<div class="ov-task-card ' + sc + '" style="cursor:pointer;" onclick="openTaskModal(\'' + escHtml(agent.sessionId).replace(/'/g,"\\'") + '\',\'' + escHtml(taskName).replace(/'/g,"\\'") + '\',\'' + escHtml(agent.key).replace(/'/g,"\\'") + '\')">';
  // Row 1: status dot + name + status badge
  h += '<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;">';
  h += '<span class="status-dot ' + sc + '" style="margin-top:5px;"></span>';
  h += '<div style="flex:1;min-width:0;">';
  h += '<div style="font-weight:700;font-size:14px;color:var(--text-primary);line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">' + escHtml(taskName) + '</div>';
  // Row 2: project pill + time
  h += '<div style="display:flex;align-items:center;gap:8px;margin-top:4px;flex-wrap:wrap;">';
  if (badge) {
    h += '<span style="display:inline-block;padding:1px 8px;border-radius:10px;font-size:10px;font-weight:700;background:' + badge.color + '18;color:' + badge.color + ';border:1px solid ' + badge.color + '33;">' + badge.label + '</span>';
  }
  h += '<span style="font-size:12px;color:var(--text-muted);">' + escHtml(timeLabel) + '</span>';
  h += '</div>';
  h += '</div>';
  // Status badge top-right
  h += '<span class="task-card-badge ' + sc + '" style="flex-shrink:0;">' + (sc === 'running' ? '🔄' : sc === 'failed' ? '❌' : '✅') + '</span>';
  h += '</div>';
  // Row 3: Show details toggle
  h += '<button class="ov-toggle-btn" onclick="event.stopPropagation();var d=document.getElementById(\'' + detailId + '\');var o=d.classList.toggle(\'open\');this.textContent=o?\'▼ Hide details\':\'▶ Show details\';if(o){window._ovExpandedSet=window._ovExpandedSet||{};window._ovExpandedSet[\'' + escHtml(agent.sessionId) + '\']=true;}else{delete window._ovExpandedSet[\'' + escHtml(agent.sessionId) + '\'];}">' + (isOpen ? '▼ Hide details' : '▶ Show details') + '</button>';
  // Collapsible details
  h += '<div class="ov-details' + (isOpen ? ' open' : '') + '" id="' + detailId + '">';
  h += '<div><span style="color:var(--text-muted);">Session:</span> <span style="font-family:monospace;font-size:10px;">' + escHtml(agent.sessionId) + '</span></div>';
  h += '<div><span style="color:var(--text-muted);">Key:</span> <span style="font-family:monospace;font-size:10px;">' + escHtml(agent.key) + '</span></div>';
  h += '<div><span style="color:var(--text-muted);">Model:</span> ' + escHtml(agent.model || 'unknown') + '</div>';
  if (tokTotal > 0) h += '<div><span style="color:var(--text-muted);">Tokens:</span> ' + tokTotal.toLocaleString() + ' (' + (agent.inputTokens||0).toLocaleString() + ' in / ' + (agent.outputTokens||0).toLocaleString() + ' out)</div>';
  if (cmdsRun > 0) h += '<div><span style="color:var(--text-muted);">Commands run:</span> ' + cmdsRun + '</div>';
  if (agent.recentTools && agent.recentTools.length > 0) {
    h += '<div style="margin-top:6px;"><span style="color:var(--text-muted);">Recent tools:</span></div>';
    agent.recentTools.forEach(function(t) {
      h += '<div style="font-size:10px;font-family:monospace;"><span style="color:var(--text-accent);">' + escHtml(t.name) + '</span> ' + escHtml(t.summary) + '</div>';
    });
  }
  h += '<div style="margin-top:6px;"><span style="color:var(--text-muted);">Full prompt:</span></div>';
  h += '<div style="white-space:pre-wrap;word-break:break-word;max-height:120px;overflow-y:auto;padding:6px;background:var(--bg-primary);border-radius:4px;margin-top:2px;font-size:10px;">' + escHtml(agent.displayName) + '</div>';
  h += '</div>';
  h += '</div>';
  return h;
}

async function loadOverviewTasks() {
  try {
    var data = await fetch('/api/subagents').then(function(r){return r.json();});
    var el = document.getElementById('overview-tasks-list');
    var countBadge = document.getElementById('overview-tasks-count-badge');
    if (!el) return true;
    var agents = data.subagents || [];

    // Also load into hidden active-tasks-grid for compatibility
    loadActiveTasks();

    if (agents.length === 0) {
      if (countBadge) countBadge.textContent = '';
      el.innerHTML = '<div style="text-align:center;padding:40px 20px;color:var(--text-muted);">'
        + '<div style="font-size:32px;margin-bottom:12px;" class="tasks-empty-icon">😴</div>'
        + '<div style="font-size:14px;font-weight:600;color:var(--text-tertiary);margin-bottom:4px;">No active tasks</div>'
        + '<div style="font-size:12px;">The AI is idle.</div></div>';
      return true;
    }

    var running = [], done = [], failed = [];
    agents.forEach(function(a) {
      var isRealFailure = a.status === 'stale' && a.abortedLastRun && (a.outputTokens || 0) === 0;
      if (a.status === 'active') running.push(a);
      else if (isRealFailure) failed.push(a);
      else done.push(a);
    });
    // Filter old completed/failed (2h)
    done = done.filter(function(a) { return a.runtimeMs < 2 * 60 * 60 * 1000; });
    failed = failed.filter(function(a) { return a.runtimeMs < 2 * 60 * 60 * 1000; });

    if (countBadge) countBadge.textContent = running.length > 0 ? '(' + running.length + ' running)' : '(' + (done.length + failed.length) + ' recent)';

    var totalShown = running.length + done.length + failed.length;
    if (totalShown === 0) {
      el.innerHTML = '<div style="text-align:center;padding:40px 20px;color:var(--text-muted);">'
        + '<div style="font-size:32px;margin-bottom:12px;" class="tasks-empty-icon">😴</div>'
        + '<div style="font-size:14px;font-weight:600;color:var(--text-tertiary);margin-bottom:4px;">No active tasks</div>'
        + '<div style="font-size:12px;">The AI is idle.</div></div>';
      return true;
    }

    var html = '';
    var cardIdx = 0;
    if (running.length > 0) {
      html += '<div class="task-group-header">🔄 Running (' + running.length + ')</div>';
      running.forEach(function(a) { html += _ovRenderCard(a, cardIdx++); });
    }
    if (done.length > 0) {
      html += '<div class="task-group-header">✅ Recently Completed (' + done.length + ')</div>';
      done.forEach(function(a) { html += _ovRenderCard(a, cardIdx++); });
    }
    if (failed.length > 0) {
      html += '<div class="task-group-header">❌ Failed (' + failed.length + ')</div>';
      failed.forEach(function(a) { html += _ovRenderCard(a, cardIdx++); });
    }

    // Preserve scroll position for smooth update
    var scrollTop = el.scrollTop;
    el.innerHTML = html;
    el.scrollTop = scrollTop;
    return true;
  } catch(e) {
    return false;
  }
}

function startOverviewTasksRefresh() {
  loadOverviewTasks();
  if (_ovTasksTimer) clearInterval(_ovTasksTimer);
  _ovTasksTimer = setInterval(loadOverviewTasks, 10000);
}

// === Task Detail Modal ===
var _modalSessionId = null;
var _modalTab = 'summary';
var _modalAutoRefresh = true;
var _modalRefreshTimer = null;
var _modalEvents = [];

/* === Component Modal === */
var COMP_MAP = {
  'node-telegram': {type:'channel', name:'Telegram', icon:'📱'},
  'node-signal': {type:'channel', name:'Signal', icon:'💬'},
  'node-whatsapp': {type:'channel', name:'WhatsApp', icon:'📲'},
  'node-gateway': {type:'gateway', name:'Gateway', icon:'🌐'},
  'node-brain': {type:'brain', name:'AI Model', icon:'🧠'},
  'node-session': {type:'tool', name:'Sessions', icon:'📋'},
  'node-exec': {type:'tool', name:'Exec', icon:'⚡'},
  'node-browser': {type:'tool', name:'Web', icon:'🌍'},
  'node-search': {type:'tool', name:'Search', icon:'🔍'},
  'node-cron': {type:'tool', name:'Cron', icon:'⏰'},
  'node-tts': {type:'tool', name:'TTS', icon:'🔊'},
  'node-memory': {type:'tool', name:'Memory', icon:'💾'},
  'node-cost-optimizer': {type:'optimizer', name:'Cost Optimizer', icon:'💰'},
  'node-automation-advisor': {type:'advisor', name:'Automation Advisor', icon:'🧠'},
  'node-runtime': {type:'infra', name:'Runtime', icon:'⚙️'},
  'node-machine': {type:'infra', name:'Machine', icon:'🖥️'},
  'node-storage': {type:'infra', name:'Storage', icon:'💿'},
  'node-network': {type:'infra', name:'Network', icon:'🔗'}
};
function initCompClickHandlers() {
  Object.keys(COMP_MAP).forEach(function(id) {
    // Bind on original flow SVG nodes
    var el = document.getElementById(id);
    if (el) {
      el.classList.add('flow-node-clickable');
      el.addEventListener('click', function(e) {
        e.stopPropagation();
        openCompModal(id);
      });
    }
    // Bind on overview clone nodes (ov- prefixed)
    var ovEl = document.getElementById('ov-' + id);
    if (ovEl) {
      ovEl.classList.add('flow-node-clickable');
      ovEl.addEventListener('click', function(e) {
        e.stopPropagation();
        openCompModal(id);
      });
    }
  });
}

function initOverviewCompClickHandlers() {
  Object.keys(COMP_MAP).forEach(function(id) {
    var ovEl = document.getElementById('ov-' + id);
    if (ovEl) {
      ovEl.classList.add('flow-node-clickable');
      ovEl.addEventListener('click', function(e) {
        e.stopPropagation();
        openCompModal(id);
      });
    }
  });
}
var _tgRefreshTimer = null;
var _tgOffset = 0;
var _tgAllMessages = [];

function isCompModalActive(nodeId) {
  var overlay = document.getElementById('comp-modal-overlay');
  return !!(overlay && overlay.classList.contains('open') && window._currentComponentId === nodeId);
}

function openCompModal(nodeId) {
  var c = COMP_MAP[nodeId];
  if (!c) return;
  
  // Clear ALL existing refresh timers to prevent stale data overwriting new modal
  if (_tgRefreshTimer) { clearInterval(_tgRefreshTimer); _tgRefreshTimer = null; }
  if (_gwRefreshTimer) { clearInterval(_gwRefreshTimer); _gwRefreshTimer = null; }
  if (_brainRefreshTimer) { clearInterval(_brainRefreshTimer); _brainRefreshTimer = null; }
  if (_toolRefreshTimer) { clearInterval(_toolRefreshTimer); _toolRefreshTimer = null; }
  if (_costOptimizerRefreshTimer) { clearInterval(_costOptimizerRefreshTimer); _costOptimizerRefreshTimer = null; }
  
  // Track current component for time travel
  window._currentComponentId = nodeId;
  
  document.getElementById('comp-modal-title').textContent = c.icon + ' ' + c.name;
  
  // Reset time travel state when opening new component
  _timeTravelMode = false;
  _currentTimeContext = null;
  document.getElementById('time-travel-toggle').classList.remove('active');
  document.getElementById('time-travel-bar').classList.remove('active');

  if (nodeId === 'node-telegram') {
    _tgOffset = 0;
    _tgAllMessages = [];
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading messages...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadTelegramMessages(false);
    _tgRefreshTimer = setInterval(function() { loadTelegramMessages(true); }, 10000);
    return;
  }

  if (nodeId === 'node-gateway') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading gateway data...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadGatewayData(false);
    _gwRefreshTimer = setInterval(function() { loadGatewayData(true); }, 10000);
    return;
  }

  if (nodeId === 'node-brain') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading AI brain data...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    _brainPage = 0;
    loadBrainData(false);
    _brainRefreshTimer = setInterval(function() { loadBrainData(true); }, 10000);
    return;
  }

  if (nodeId === 'node-cost-optimizer') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Analyzing costs...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    loadCostOptimizerData(false);
    _costOptimizerRefreshTimer = setInterval(function() { loadCostOptimizerData(true); }, 15000);
    return;
  }

  if (c.type === 'tool') {
    var toolKey = nodeId.replace('node-', '');
    // Show cached data instantly if available, otherwise show loading spinner
    if (!_toolDataCache[toolKey]) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading ' + c.name + ' data...</div>';
    }
    document.getElementById('comp-modal-overlay').classList.add('open');
    // If cached, render immediately then refresh in background
    if (_toolDataCache[toolKey]) {
      loadToolData(toolKey, c, false);
    } else {
      loadToolData(toolKey, c, false);
    }
    _toolRefreshTimer = setInterval(function() { loadToolData(toolKey, c, true); }, 10000);
    return;
  }

  if (nodeId === 'node-runtime' || nodeId === 'node-machine') {
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading ' + c.name + ' info...</div>';
    document.getElementById('comp-modal-overlay').classList.add('open');
    fetch('/api/component/' + nodeId.replace('node-', '')).then(function(r){return r.json();}).then(function(data) {
      if (!isCompModalActive(nodeId)) return;
      var body = document.getElementById('comp-modal-body');
      var html = '<div style="text-align:center;margin-bottom:16px;font-size:36px;">' + c.icon + '</div>';
      var items = data.items || [];
      html += '<div style="display:flex;flex-direction:column;gap:1px;">';
      items.forEach(function(item) {
        var valColor = item.status === 'warning' ? 'var(--text-warning)' : item.status === 'critical' ? 'var(--text-error)' : 'var(--text-primary)';
        html += '<div class="stat-row"><span class="stat-label">' + escapeHtml(item.label) + '</span><span class="stat-val" style="color:' + valColor + ';">' + escapeHtml(item.value) + '</span></div>';
      });
      html += '</div>';
      body.innerHTML = html;
      document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
    }).catch(function(e) {
      if (!isCompModalActive(nodeId)) return;
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load: ' + e.message + '</div>';
    });
    return;
  }

  document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;"><div style="font-size:48px;margin-bottom:16px;">' + c.icon + '</div><div style="font-size:16px;font-weight:600;margin-bottom:8px;">' + c.name + '</div><div style="color:var(--text-muted);">Live view coming soon</div><div style="margin-top:8px;font-size:12px;color:var(--text-muted);text-transform:uppercase;">' + c.type + '</div></div>';
  document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
  document.getElementById('comp-modal-overlay').classList.add('open');
}

function loadTelegramMessages(isRefresh) {
  var expectedNodeId = 'node-telegram';
  var url = '/api/channel/telegram?limit=50&offset=0';
  fetch(url).then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msgs = data.messages || [];
    var body = document.getElementById('comp-modal-body');
    var html = '<div class="tg-stats"><span class="in">📥 ' + (data.todayIn || 0) + ' incoming</span><span class="out">📤 ' + (data.todayOut || 0) + ' outgoing</span><span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today</span></div>';
    html += '<div class="tg-chat">';
    if (msgs.length === 0) {
      html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No messages found</div>';
    }
    msgs.forEach(function(m) {
      var dir = m.direction === 'in' ? 'in' : 'out';
      var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '';
      var date = m.timestamp ? new Date(m.timestamp).toLocaleDateString([], {month:'short',day:'numeric'}) : '';
      var text = m.text || (m.direction === 'in' ? '(message received)' : '(reply sent)');
      html += '<div class="tg-bubble ' + dir + '">';
      html += '<div class="tg-sender">' + escapeHtml(m.sender || (dir === 'in' ? 'User' : 'Clawd')) + '</div>';
      html += '<div class="tg-text md-rendered">' + renderMarkdown(text) + '</div>';
      html += '<div class="tg-time">' + date + ' ' + ts + '</div>';
      html += '</div>';
    });
    if (data.total > msgs.length) {
      html += '<div class="tg-load-more"><button onclick="loadMoreTelegram()">Load more (' + (data.total - msgs.length) + ' remaining)</button></div>';
    }
    html += '</div>';
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString() + ' · ' + data.total + ' total messages';
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load messages</div>';
    }
  });
}

function loadMoreTelegram() {
  // Simple: just increase limit
  fetch('/api/channel/telegram?limit=200&offset=0').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive('node-telegram')) return;
    // Re-render with all data
    var msgs = data.messages || [];
    var body = document.getElementById('comp-modal-body');
    var html = '<div class="tg-stats"><span class="in">📥 ' + (data.todayIn || 0) + ' incoming</span><span class="out">📤 ' + (data.todayOut || 0) + ' outgoing</span><span style="margin-left:auto;color:var(--text-muted);font-size:11px;">Today</span></div>';
    html += '<div class="tg-chat">';
    msgs.forEach(function(m) {
      var dir = m.direction === 'in' ? 'in' : 'out';
      var ts = m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : '';
      var date = m.timestamp ? new Date(m.timestamp).toLocaleDateString([], {month:'short',day:'numeric'}) : '';
      var text = m.text || (m.direction === 'in' ? '(message received)' : '(reply sent)');
      html += '<div class="tg-bubble ' + dir + '">';
      html += '<div class="tg-sender">' + escapeHtml(m.sender || (dir === 'in' ? 'User' : 'Clawd')) + '</div>';
      html += '<div class="tg-text md-rendered">' + renderMarkdown(text) + '</div>';
      html += '<div class="tg-time">' + date + ' ' + ts + '</div>';
      html += '</div>';
    });
    html += '</div>';
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Last updated: ' + new Date().toLocaleTimeString() + ' · ' + data.total + ' total messages';
  });
}

function escapeHtml(s) {
  var d = document.createElement('div'); d.textContent = s; return d.innerHTML;
}

function renderMarkdown(text) {
  if (!text) return '';
  var s = escapeHtml(text);
  // Code blocks (``` ... ```)
  s = s.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
  // Inline code
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Headers
  s = s.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
  s = s.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  s = s.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  s = s.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  // Bold + italic
  s = s.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\*(.+?)\*/g, '<em>$1</em>');
  s = s.replace(/_(.+?)_/g, '<em>$1</em>');
  // Links
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  // Blockquotes
  s = s.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');
  // Unordered lists
  s = s.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
  s = s.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
  // Line breaks (double newline = paragraph, single = br)
  s = s.replace(/\n\n/g, '</p><p>');
  s = s.replace(/\n/g, '<br>');
  s = '<p>' + s + '</p>';
  // Clean up empty paragraphs
  s = s.replace(/<p><\/p>/g, '');
  s = s.replace(/<p>(<h[1-4]>)/g, '$1');
  s = s.replace(/(<\/h[1-4]>)<\/p>/g, '$1');
  s = s.replace(/<p>(<pre>)/g, '$1');
  s = s.replace(/(<\/pre>)<\/p>/g, '$1');
  s = s.replace(/<p>(<ul>)/g, '$1');
  s = s.replace(/(<\/ul>)<\/p>/g, '$1');
  s = s.replace(/<p>(<blockquote>)/g, '$1');
  s = s.replace(/(<\/blockquote>)<\/p>/g, '$1');
  return s;
}

var _brainRefreshTimer = null;
var _brainPage = 0;

function loadBrainData(isRefresh) {
  var expectedNodeId = 'node-brain';
  var url = '/api/component/brain?limit=50&offset=' + (_brainPage * 50);
  fetchJsonWithTimeout(url, 8000).catch(function(err) {
    if (String((err && err.message) || '').toLowerCase().includes('abort')) {
      return fetchJsonWithTimeout(url, 15000);
    }
    throw err;
  }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var body = document.getElementById('comp-modal-body');
    var s = data.stats || {};
    var tok = s.today_tokens || {};
    var totalTok = (tok.input||0) + (tok.output||0) + (tok.cache_read||0);
    var fmtTok = totalTok >= 1e6 ? (totalTok/1e6).toFixed(1) + 'M' : totalTok >= 1e3 ? (totalTok/1e3).toFixed(1) + 'K' : totalTok;

    var html = '';
    // Model badge
    html += '<div style="text-align:center;margin-bottom:14px;"><span style="background:linear-gradient(135deg,#FFD54F,#FF9800);color:#1a1a2e;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:700;letter-spacing:0.5px;">' + escapeHtml(s.model||'unknown') + '</span></div>';

    // Stats cards 2x2
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px;">';
    html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px 14px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;margin-top:2px;">Today\'s Calls</div></div>';
    html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px 14px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + fmtTok + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;margin-top:2px;">Tokens</div></div>';
    var costColor = parseFloat((s.today_cost||'$0').replace('$','')) > 50 ? '#f59e0b' : parseFloat((s.today_cost||'$0').replace('$','')) > 100 ? '#ef4444' : '#22c55e';
    html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px 14px;text-align:center;"><div style="font-size:24px;font-weight:700;color:' + costColor + ';">' + (s.today_cost||'$0.00') + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;margin-top:2px;">Cost</div></div>';
    html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px 14px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + ((s.avg_response_ms||0) >= 1000 ? ((s.avg_response_ms/1000).toFixed(1)+'s') : ((s.avg_response_ms||0)+'ms')) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;margin-top:2px;">Avg Response</div></div>';
    html += '</div>';

    // Thinking & Cache stats row
    var thinkCount = s.thinking_calls || 0;
    var cacheHits = s.cache_hits || 0;
    var cacheRate = s.today_calls > 0 ? Math.round(cacheHits / s.today_calls * 100) : 0;
    html += '<div style="display:flex;gap:8px;margin-bottom:12px;justify-content:center;flex-wrap:wrap;">';
    html += '<span style="background:' + (thinkCount > 0 ? '#7c3aed22' : 'var(--bg-secondary)') + ';color:' + (thinkCount > 0 ? '#7c3aed' : 'var(--text-muted)') + ';padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;">🧠 Thinking: ' + thinkCount + '/' + (s.today_calls||0) + '</span>';
    html += '<span style="background:' + (cacheRate > 50 ? '#22c55e22' : 'var(--bg-secondary)') + ';color:' + (cacheRate > 50 ? '#22c55e' : 'var(--text-muted)') + ';padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;">💾 Cache hit: ' + cacheRate + '%</span>';
    var cacheW = tok.cache_write||0;
    html += '<span style="background:var(--bg-secondary);color:var(--text-muted);padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;">✍️ Cache write: ' + (cacheW>=1e6?(cacheW/1e6).toFixed(1)+'M':cacheW>=1e3?(cacheW/1e3).toFixed(1)+'K':cacheW) + '</span>';
    html += '</div>';

    // Token breakdown bar
    var tIn = tok.input||0, tOut = tok.output||0, tCR = tok.cache_read||0;
    var tTotal = tIn+tOut+tCR || 1;
    html += '<div style="display:flex;height:6px;border-radius:3px;overflow:hidden;margin-bottom:16px;background:var(--bg-secondary);">';
    html += '<div style="width:' + (tIn/tTotal*100) + '%;background:#3b82f6;" title="Input: ' + tIn + '"></div>';
    html += '<div style="width:' + (tOut/tTotal*100) + '%;background:#8b5cf6;" title="Output: ' + tOut + '"></div>';
    html += '<div style="width:' + (tCR/tTotal*100) + '%;background:#22c55e;" title="Cache Read: ' + tCR + '"></div>';
    html += '</div>';
    html += '<div style="display:flex;gap:12px;font-size:10px;color:var(--text-muted);margin-bottom:14px;justify-content:center;">';
    html += '<span>🔵 Input</span><span>🟣 Output</span><span>🟢 Cache Read</span>';
    html += '</div>';

    // Call list
    var calls = data.calls || [];
    if (calls.length === 0) {
      html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No LLM calls found today</div>';
    } else {
      html += '<div style="display:flex;flex-direction:column;gap:6px;max-height:400px;overflow-y:auto;">';
      var TOOL_ICONS = {read:'📄',write:'✏️',edit:'🔧',exec:'⚡',process:'⚙️',browser:'🌐',web_search:'🔍',web_fetch:'🌍',message:'💬',tts:'🔊',image:'🖼️',canvas:'🎨',nodes:'📱'};
      var TOOL_COLORS = {exec:'#f59e0b',browser:'#3b82f6',web_search:'#8b5cf6',web_fetch:'#06b6d4',message:'#ec4899',read:'#6b7280',write:'#22c55e',edit:'#f97316',tts:'#a855f7',image:'#ef4444',canvas:'#14b8a6',nodes:'#6366f1',process:'#64748b'};
      calls.forEach(function(c) {
        var ts = c.timestamp ? new Date(c.timestamp).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'}) : '';
        var costVal = parseFloat((c.cost||'$0').replace('$',''));
        var cColor = costVal > 0.50 ? '#f59e0b' : costVal > 1.0 ? '#ef4444' : '#22c55e';
        var dur = c.duration_ms > 0 ? (c.duration_ms >= 1000 ? (c.duration_ms/1000).toFixed(1)+'s' : c.duration_ms+'ms') : '—';
        html += '<div style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);font-size:11px;flex-wrap:wrap;">';
        html += '<span style="color:var(--text-tertiary);min-width:58px;">' + ts + '</span>';
        html += '<span style="color:var(--text-muted);font-size:10px;min-width:50px;">' + escapeHtml(c.session||'main') + '</span>';
        html += '<span style="color:#3b82f6;min-width:45px;" title="In">' + (c.tokens_in>=1000?(c.tokens_in/1000).toFixed(1)+'K':c.tokens_in) + '→</span>';
        html += '<span style="color:#8b5cf6;min-width:40px;" title="Out">' + (c.tokens_out>=1000?(c.tokens_out/1000).toFixed(1)+'K':c.tokens_out) + '</span>';
        html += '<span style="color:' + cColor + ';min-width:50px;">' + (c.cost||'$0') + '</span>';
        html += '<span style="color:var(--text-muted);min-width:35px;">' + dur + '</span>';
        if (c.thinking) html += '<span style="background:#7c3aed22;color:#7c3aed;padding:1px 5px;border-radius:4px;font-size:10px;" title="Thinking enabled">🧠</span>';
        if (c.cache_read > 0) html += '<span style="background:#22c55e22;color:#22c55e;padding:1px 5px;border-radius:4px;font-size:10px;" title="Cache hit: ' + c.cache_read + ' tokens">💾' + (c.cache_read>=1000?(c.cache_read/1000).toFixed(0)+'K':c.cache_read) + '</span>';
        // Tool badges
        if (c.tools_used && c.tools_used.length > 0) {
          html += '<span style="display:flex;gap:3px;flex-wrap:wrap;">';
          c.tools_used.forEach(function(t) {
            var icon = TOOL_ICONS[t] || '🔧';
            var bg = TOOL_COLORS[t] || '#6b7280';
            html += '<span style="background:' + bg + '22;color:' + bg + ';padding:1px 5px;border-radius:4px;font-size:10px;" title="' + t + '">' + icon + t + '</span>';
          });
          html += '</span>';
        }
        html += '</div>';
      });
      html += '</div>';
    }

    if (data.total > calls.length) {
      html += '<div style="text-align:center;margin-top:12px;font-size:12px;color:var(--text-muted);">' + calls.length + ' of ' + data.total + ' calls shown</div>';
    }

    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Auto-refreshing · Last updated: ' + new Date().toLocaleTimeString() + ' · ' + (data.total||0) + ' LLM calls today';
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    var msg = String((e && e.message) || 'Unknown error');
    if (msg.toLowerCase().includes('abort')) {
      msg = 'Request timed out. The brain panel is heavy; please retry in 2-3 seconds.';
    }
    document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load brain data: ' + msg + '</div>';
  });
}

function loadCostOptimizerData(isRefresh) {
  var expectedNodeId = 'node-cost-optimizer';
  fetch('/api/cost-optimization').then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var body = document.getElementById('comp-modal-body');
    var html = '';
    
    // Cost Summary
    html += '<div class="cost-optimizer-summary">';
    html += '<div class="cost-stat-grid">';
    html += '<div class="cost-stat"><div class="cost-label">Today</div><div class="cost-value">$' + (data.costs.today || 0).toFixed(3) + '</div></div>';
    html += '<div class="cost-stat"><div class="cost-label">This Week</div><div class="cost-value">$' + (data.costs.week || 0).toFixed(3) + '</div></div>';
    html += '<div class="cost-stat"><div class="cost-label">This Month</div><div class="cost-value">$' + (data.costs.month || 0).toFixed(3) + '</div></div>';
    html += '<div class="cost-stat"><div class="cost-label">Projected Monthly</div><div class="cost-value">$' + (data.costs.projected || 0).toFixed(2) + '</div></div>';
    html += '</div>';
    html += '</div>';
    
    // Local Model Availability
    html += '<div class="local-models-section" style="margin-top:20px;">';
    html += '<h3 style="color:var(--text-accent);margin-bottom:12px;">🖥️ Local Model Availability</h3>';
    if (data.localModels.available) {
      html += '<div class="local-status-good">✅ Ollama detected with ' + data.localModels.count + ' tool-capable models</div>';
      html += '<div class="model-list" style="margin-top:8px;">';
      data.localModels.models.forEach(function(model) {
        html += '<span class="model-badge">' + model + '</span>';
      });
      html += '</div>';
    } else {
      html += '<div class="local-status-warning">⚠️ No local models available</div>';
      html += '<div style="margin-top:8px;font-size:12px;color:var(--text-muted);">Install Ollama and pull tool-capable models to reduce API costs</div>';
      html += '<div style="margin-top:4px;font-size:11px;color:var(--text-muted);">Example: <code>ollama pull llama3.3</code></div>';
    }
    html += '</div>';
    
    // Cost Optimization Recommendations
    html += '<div class="recommendations-section" style="margin-top:20px;">';
    html += '<h3 style="color:var(--text-accent);margin-bottom:12px;">💡 Optimization Recommendations</h3>';
    
    if (data.recommendations.length === 0) {
      html += '<div style="padding:12px;background:var(--bg-success);border-radius:8px;color:var(--text-success);">✅ Cost usage is optimal</div>';
    } else {
      data.recommendations.forEach(function(rec) {
        var priority = rec.priority === 'high' ? '🔥' : rec.priority === 'medium' ? '⚡' : '💡';
        var bgClass = rec.priority === 'high' ? 'bg-error' : rec.priority === 'medium' ? 'bg-warning' : 'bg-hover';
        html += '<div class="recommendation" style="padding:12px;margin-bottom:8px;background:var(--' + bgClass + ');border-radius:8px;">';
        html += '<div style="font-weight:600;margin-bottom:4px;">' + priority + ' ' + rec.title + '</div>';
        html += '<div style="font-size:13px;color:var(--text-secondary);margin-bottom:6px;">' + rec.description + '</div>';
        if (rec.action) {
          html += '<div style="font-size:12px;color:var(--text-muted);font-family:monospace;">' + rec.action + '</div>';
        }
        html += '</div>';
      });
    }
    html += '</div>';
    
    // Recent High-Cost Operations
    if (data.expensiveOps && data.expensiveOps.length > 0) {
      html += '<div class="expensive-ops-section" style="margin-top:20px;">';
      html += '<h3 style="color:var(--text-accent);margin-bottom:12px;">💸 Recent High-Cost Operations</h3>';
      data.expensiveOps.forEach(function(op) {
        html += '<div class="expensive-op" style="padding:10px;margin-bottom:6px;background:var(--bg-hover);border-radius:6px;border-left:3px solid var(--text-error);">';
        html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
        html += '<div style="font-weight:600;">' + op.model + '</div>';
        html += '<div style="color:var(--text-error);font-weight:600;">$' + op.cost.toFixed(4) + '</div>';
        html += '</div>';
        html += '<div style="font-size:12px;color:var(--text-muted);margin-top:2px;">' + op.tokens + ' tokens · ' + op.timeAgo + '</div>';
        if (op.canOptimize) {
          html += '<div style="font-size:11px;color:var(--text-success);margin-top:4px;">💡 Could use local model for this task type</div>';
        }
        html += '</div>';
      });
      html += '</div>';
    }
    
    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Auto-refreshing · Last updated: ' + new Date().toLocaleTimeString();
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load cost optimizer: ' + e.message + '</div>';
    }
  });
}

var _gwRefreshTimer = null;
var _gwPage = 0;

// ═══ TIME TRAVEL ═══════════════════════════════════════════════════
var _timelineData = null;  // {days: [{date, label, events, hasMemory, hours}], today: 'YYYY-MM-DD'}
var _currentTimeContext = null;  // {date: 'YYYY-MM-DD', hour: null} or null for "now"
var _timeTravelMode = false;

function toggleTimeTravelMode() {
  _timeTravelMode = !_timeTravelMode;
  var toggle = document.getElementById('time-travel-toggle');
  var bar = document.getElementById('time-travel-bar');
  
  if (_timeTravelMode) {
    toggle.classList.add('active');
    bar.classList.add('active');
    loadTimelineData();
  } else {
    toggle.classList.remove('active');
    bar.classList.remove('active');
    _currentTimeContext = null;
    // Reload current component data
    reloadCurrentComponent();
  }
}

function loadTimelineData() {
  fetch('/api/timeline').then(function(r) { return r.json(); }).then(function(data) {
    _timelineData = data;
    // Set initial time to "now"
    _currentTimeContext = null;
    updateTimeDisplay();
    updateSliderPosition();
  }).catch(function(e) {
    console.error('Failed to load timeline:', e);
  });
}

function timeTravel(direction) {
  if (!_timelineData || !_timelineData.days) return;
  
  var days = _timelineData.days;
  var currentDate = _currentTimeContext ? _currentTimeContext.date : _timelineData.today;
  var currentIndex = days.findIndex(function(d) { return d.date === currentDate; });
  
  if (direction === 'prev-day' && currentIndex > 0) {
    _currentTimeContext = {date: days[currentIndex - 1].date, hour: null};
  } else if (direction === 'next-day' && currentIndex < days.length - 1) {
    _currentTimeContext = {date: days[currentIndex + 1].date, hour: null};
  } else if (direction === 'now') {
    _currentTimeContext = null;
  }
  
  updateTimeDisplay();
  updateSliderPosition();
  reloadCurrentComponent();
}

function onTimeSliderClick(event) {
  if (!_timelineData || !_timelineData.days) return;
  
  var slider = document.getElementById('time-slider');
  var rect = slider.getBoundingClientRect();
  var percent = (event.clientX - rect.left) / rect.width;
  
  var days = _timelineData.days;
  var index = Math.floor(percent * days.length);
  index = Math.max(0, Math.min(index, days.length - 1));
  
  _currentTimeContext = {date: days[index].date, hour: null};
  updateTimeDisplay();
  updateSliderPosition();
  reloadCurrentComponent();
}

function updateTimeDisplay() {
  var display = document.getElementById('time-display');
  if (!display) return;
  
  if (!_currentTimeContext) {
    display.textContent = 'Live (Now)';
    display.style.color = 'var(--text-accent)';
  } else {
    var day = _timelineData.days.find(function(d) { return d.date === _currentTimeContext.date; });
    if (day) {
      display.textContent = day.label + ' (' + day.events + ' events)';
      display.style.color = 'var(--text-secondary)';
    }
  }
}

function updateSliderPosition() {
  var thumb = document.getElementById('time-slider-thumb');
  if (!thumb || !_timelineData) return;
  
  if (!_currentTimeContext) {
    // "Now" - position at the end
    thumb.style.left = '100%';
  } else {
    var days = _timelineData.days;
    var index = days.findIndex(function(d) { return d.date === _currentTimeContext.date; });
    if (index >= 0) {
      var percent = (index / (days.length - 1)) * 100;
      thumb.style.left = percent + '%';
    }
  }
}

function reloadCurrentComponent() {
  // Re-trigger the current component modal with time context
  var overlay = document.getElementById('comp-modal-overlay');
  if (overlay && overlay.classList.contains('open')) {
    var body = document.getElementById('comp-modal-body');
    body.innerHTML = '<div style="text-align:center;padding:40px;"><div class="pulse"></div> Loading ' + (_currentTimeContext ? 'historical' : 'current') + ' data...</div>';
    
    if (window._currentComponentId) {
      loadComponentWithTimeContext(window._currentComponentId);
    }
  }
}

function loadCostOptimizerDataWithTime() {
  var body = document.getElementById('comp-modal-body');
  var timeContext = _currentTimeContext ? ' (' + _currentTimeContext.date + ')' : '';
  body.innerHTML = '<div style="text-align:center;padding:20px;"><div style="font-size:48px;margin-bottom:16px;">💰</div><div style="font-size:16px;font-weight:600;margin-bottom:8px;">Cost Optimizer' + timeContext + '</div><div style="color:var(--text-muted);">Historical cost analysis coming soon</div><div style="margin-top:8px;font-size:12px;color:var(--text-muted);text-transform:uppercase;">optimizer</div></div>';
  document.getElementById('comp-modal-footer').textContent = 'Time travel: ' + (_currentTimeContext ? _currentTimeContext.date : 'Live');
}

function loadAutomationAdvisorDataWithTime() {
  var body = document.getElementById('comp-modal-body');
  var timeContext = _currentTimeContext ? ' (' + _currentTimeContext.date + ')' : '';
  
  if (_currentTimeContext) {
    body.innerHTML = '<div style="text-align:center;padding:20px;"><div style="font-size:48px;margin-bottom:16px;">🧠</div><div style="font-size:16px;font-weight:600;margin-bottom:8px;">Automation Advisor' + timeContext + '</div><div style="color:var(--text-muted);">Historical pattern analysis coming soon</div><div style="margin-top:8px;font-size:12px;color:var(--text-muted);text-transform:uppercase;">advisor</div></div>';
    document.getElementById('comp-modal-footer').textContent = 'Time travel: ' + _currentTimeContext.date;
    return;
  }
  
  body.innerHTML = '<div style="text-align:center;padding:40px;"><div style="font-size:24px;margin-bottom:20px;">🧠 Loading automation analysis...</div></div>';
  document.getElementById('comp-modal-footer').textContent = 'Live';
  
  fetch('/api/automation-analysis').then(function(r){return r.json();}).then(function(data) {
    var html = '<div style="padding:20px;">';
    html += '<div style="text-align:center;margin-bottom:30px;"><div style="font-size:48px;margin-bottom:12px;">🧠</div><h2 style="margin:0;font-size:20px;">Automation Advisor</h2><p style="color:var(--text-muted);margin:8px 0 0 0;">Analyzing patterns to suggest new automations</p></div>';
    
    if (data.patterns && data.patterns.length > 0) {
      html += '<h3 style="color:var(--text-primary);border-bottom:2px solid var(--border-primary);padding-bottom:8px;margin-bottom:16px;">🔍 Detected Patterns</h3>';
      data.patterns.forEach(function(pattern) {
        var priorityColor = pattern.priority === 'high' ? '#f44336' : pattern.priority === 'medium' ? '#ff9800' : '#4caf50';
        html += '<div style="background:var(--bg-hover);border-radius:8px;padding:16px;margin-bottom:16px;border-left:4px solid ' + priorityColor + ';">';
        html += '<div style="font-weight:600;margin-bottom:8px;">' + pattern.title + '</div>';
        html += '<div style="color:var(--text-muted);margin-bottom:12px;">' + pattern.description + '</div>';
        html += '<div style="font-size:12px;color:var(--text-muted);">Frequency: ' + pattern.frequency + ' • Confidence: ' + pattern.confidence + '%</div>';
        html += '</div>';
      });
    }
    
    if (data.suggestions && data.suggestions.length > 0) {
      html += '<h3 style="color:var(--text-primary);border-bottom:2px solid var(--border-primary);padding-bottom:8px;margin-bottom:16px;">💡 Automation Suggestions</h3>';
      data.suggestions.forEach(function(suggestion) {
        var typeIcon = suggestion.type === 'cron' ? '⏰' : suggestion.type === 'skill' ? '🛠️' : '🔧';
        html += '<div style="background:var(--bg-hover);border-radius:8px;padding:16px;margin-bottom:16px;">';
        html += '<div style="display:flex;align-items:center;margin-bottom:8px;"><span style="font-size:20px;margin-right:8px;">' + typeIcon + '</span>';
        html += '<span style="font-weight:600;">' + suggestion.title + '</span></div>';
        html += '<div style="color:var(--text-muted);margin-bottom:12px;">' + suggestion.description + '</div>';
        if (suggestion.implementation) {
          html += '<div style="background:var(--bg-primary);padding:8px;border-radius:4px;font-family:monospace;font-size:12px;color:var(--text-muted);margin-bottom:8px;">' + suggestion.implementation + '</div>';
        }
        html += '<div style="font-size:12px;color:var(--text-muted);">Impact: ' + suggestion.impact + ' • Effort: ' + suggestion.effort + '</div>';
        html += '</div>';
      });
    }
    
    if (!data.patterns || data.patterns.length === 0) {
      html += '<div style="text-align:center;padding:40px;color:var(--text-muted);">';
      html += '<div style="font-size:48px;margin-bottom:16px;">🌱</div>';
      html += '<h3>No patterns detected yet</h3>';
      html += '<p>Continue using the agent and check back later for automation suggestions.</p>';
      html += '</div>';
    }
    
    html += '</div>';
    body.innerHTML = html;
  }).catch(function(e) {
    body.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><div style="font-size:48px;margin-bottom:16px;">⚠️</div><h3>Analysis Unavailable</h3><p>Unable to load automation analysis: ' + e.message + '</p></div>';
  });
}

function loadComponentWithTimeContext(nodeId) {
  var c = COMP_MAP[nodeId];
  if (!c) return;
  
  // Clear existing refresh timers
  if (_tgRefreshTimer) { clearInterval(_tgRefreshTimer); _tgRefreshTimer = null; }
  if (_gwRefreshTimer) { clearInterval(_gwRefreshTimer); _gwRefreshTimer = null; }
  if (_brainRefreshTimer) { clearInterval(_brainRefreshTimer); _brainRefreshTimer = null; }
  if (_toolRefreshTimer) { clearInterval(_toolRefreshTimer); _toolRefreshTimer = null; }
  if (_costOptimizerRefreshTimer) { clearInterval(_costOptimizerRefreshTimer); _costOptimizerRefreshTimer = null; }
  
  // Load data based on component type
  if (nodeId === 'node-telegram') {
    loadTelegramMessagesWithTime();
  } else if (nodeId === 'node-gateway') {
    loadGatewayDataWithTime();
  } else if (nodeId === 'node-brain') {
    loadBrainDataWithTime();
  } else if (nodeId === 'node-cost-optimizer') {
    loadCostOptimizerDataWithTime();
  } else if (nodeId === 'node-automation-advisor') {
    loadAutomationAdvisorDataWithTime();
  } else if (c.type === 'tool') {
    var toolKey = nodeId.replace('node-', '');
    loadToolDataWithTime(toolKey, c);
  } else {
    // Default component view
    var body = document.getElementById('comp-modal-body');
    var timeContext = _currentTimeContext ? ' (' + _currentTimeContext.date + ')' : '';
    body.innerHTML = '<div style="text-align:center;padding:20px;"><div style="font-size:48px;margin-bottom:16px;">' + c.icon + '</div><div style="font-size:16px;font-weight:600;margin-bottom:8px;">' + c.name + timeContext + '</div><div style="color:var(--text-muted);">Historical view coming soon</div><div style="margin-top:8px;font-size:12px;color:var(--text-muted);text-transform:uppercase;">' + c.type + '</div></div>';
    document.getElementById('comp-modal-footer').textContent = 'Time travel: ' + (_currentTimeContext ? _currentTimeContext.date : 'Live');
  }
}

function loadGatewayData(isRefresh) {
  var expectedNodeId = 'node-gateway';
  fetch('/api/component/gateway?limit=50&offset=' + (_gwPage * 50)).then(function(r) { return r.json(); }).then(function(data) {
    if (!isCompModalActive(expectedNodeId)) return;
    var body = document.getElementById('comp-modal-body');
    var s = data.stats || {};
    var cfg = s.config || {};

    // Top stats row
    var html = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;">';
    html += '<div style="flex:1;min-width:70px;background:var(--bg-secondary);border-radius:8px;padding:10px 12px;text-align:center;"><div style="font-size:20px;font-weight:700;color:var(--text-primary);">' + (s.today_messages||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Messages</div></div>';
    html += '<div style="flex:1;min-width:70px;background:var(--bg-secondary);border-radius:8px;padding:10px 12px;text-align:center;"><div style="font-size:20px;font-weight:700;color:var(--text-primary);">' + (s.today_heartbeats||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Heartbeats</div></div>';
    html += '<div style="flex:1;min-width:70px;background:var(--bg-secondary);border-radius:8px;padding:10px 12px;text-align:center;"><div style="font-size:20px;font-weight:700;color:var(--text-primary);">' + (s.today_crons||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Cron</div></div>';
    html += '<div style="flex:1;min-width:70px;background:var(--bg-secondary);border-radius:8px;padding:10px 12px;text-align:center;"><div style="font-size:20px;font-weight:700;color:' + ((s.today_errors||0) > 0 ? 'var(--text-error)' : 'var(--text-primary)') + ';">' + (s.today_errors||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
    html += '<div style="flex:1;min-width:70px;background:var(--bg-secondary);border-radius:8px;padding:10px 12px;text-align:center;"><div style="font-size:20px;font-weight:700;color:#3b82f6;">' + (s.active_sessions||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Active Sessions</div></div>';
    html += '</div>';

    // Config summary & uptime
    html += '<div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;">';
    if (s.uptime) html += '<span style="background:var(--bg-secondary);padding:3px 10px;border-radius:12px;font-size:11px;color:var(--text-muted);">⏱️ Up since: ' + escapeHtml(s.uptime) + '</span>';
    if (cfg.channels && cfg.channels.length) html += '<span style="background:var(--bg-secondary);padding:3px 10px;border-radius:12px;font-size:11px;color:var(--text-muted);">📡 Channels: ' + cfg.channels.join(', ') + '</span>';
    if (cfg.heartbeat) html += '<span style="background:var(--bg-secondary);padding:3px 10px;border-radius:12px;font-size:11px;color:var(--text-muted);">💓 Heartbeat: ' + cfg.heartbeat + '</span>';
    if (cfg.max_concurrent) html += '<span style="background:var(--bg-secondary);padding:3px 10px;border-radius:12px;font-size:11px;color:var(--text-muted);">⚡ Max concurrent: ' + cfg.max_concurrent + '</span>';
    if (cfg.max_subagents) html += '<span style="background:var(--bg-secondary);padding:3px 10px;border-radius:12px;font-size:11px;color:var(--text-muted);">🐝 Max subagents: ' + cfg.max_subagents + '</span>';
    html += '</div>';

    // Restart history
    var restarts = s.restarts || [];
    if (restarts.length > 0) {
      html += '<div style="margin-bottom:12px;font-size:11px;color:var(--text-muted);"><strong>🔄 Restarts today:</strong> ';
      restarts.forEach(function(r) { if(r) html += '<span style="margin-right:8px;">' + new Date(r).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}) + '</span>'; });
      html += '</div>';
    }

    var routes = data.routes || [];
    if (routes.length === 0) {
      html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No routing events found today</div>';
    } else {
      html += '<div style="display:flex;flex-direction:column;gap:6px;">';
      routes.forEach(function(r) {
        var badge = '📨';
        var badgeColor = '#3b82f6';
        if (r.type === 'heartbeat') { badge = '💓'; badgeColor = '#ec4899'; }
        else if (r.type === 'cron') { badge = '⏰'; badgeColor = '#f59e0b'; }
        else if (r.type === 'subagent') { badge = '🐝'; badgeColor = '#8b5cf6'; }
        else if (r.from === 'telegram') { badge = '📱'; badgeColor = '#3b82f6'; }
        else if (r.from === 'whatsapp') { badge = '📲'; badgeColor = '#22c55e'; }

        var status = r.status === 'error' ? '❌' : '✅';
        var ts = r.timestamp ? new Date(r.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'}) : '';
        var model = r.to || '';
        if (model.length > 20) model = model.substring(0, 18) + '…';
        var session = r.session || '';
        if (session.length > 20) session = session.substring(0, 18) + '…';

        html += '<div style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);font-size:12px;">';
        html += '<span style="font-size:16px;">' + badge + '</span>';
        html += '<span style="color:var(--text-tertiary);min-width:60px;">' + ts + '</span>';
        html += '<span style="color:var(--text-secondary);font-weight:600;">' + escapeHtml(r.from || '?') + '</span>';
        html += '<span style="color:var(--text-muted);">→</span>';
        html += '<span style="color:var(--text-accent);font-weight:500;flex:1;">' + escapeHtml(model) + '</span>';
        if (session) html += '<span style="color:var(--text-muted);font-size:11px;">' + escapeHtml(session) + '</span>';
        html += '<span>' + status + '</span>';
        html += '</div>';
      });
      html += '</div>';
    }

    if (data.total > routes.length) {
      html += '<div style="text-align:center;margin-top:12px;font-size:12px;color:var(--text-muted);">' + routes.length + ' of ' + data.total + ' events shown</div>';
    }

    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Auto-refreshing · Last updated: ' + new Date().toLocaleTimeString() + ' · ' + (data.total||0) + ' events today';
  }).catch(function(e) {
    if (!isCompModalActive(expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load gateway data</div>';
    }
  });
}

var _toolRefreshTimer = null;
var _costOptimizerRefreshTimer = null;
var TOOL_COLORS = {
  'session': '#1565C0', 'exec': '#E65100', 'browser': '#6A1B9A',
  'search': '#00695C', 'cron': '#546E7A', 'tts': '#F9A825', 'memory': '#283593'
};

function _fmtToolTs(ts) {
  if (!ts) return '';
  var d = new Date(ts);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
}
function _fmtToolDate(ts) {
  if (!ts) return '';
  var d = new Date(ts);
  if (isNaN(d.getTime())) return '';
  return d.toLocaleDateString([], {month:'short',day:'numeric'}) + ' ' + d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
}
function _timeAgo(ts) {
  if (!ts) return '';
  var secs = (Date.now() - new Date(ts).getTime()) / 1000;
  if (secs < 0) secs = 0;
  if (secs < 60) return Math.floor(secs) + 's ago';
  if (secs < 3600) return Math.floor(secs/60) + 'm ago';
  if (secs < 86400) return Math.floor(secs/3600) + 'h ago';
  return Math.floor(secs/86400) + 'd ago';
}

var _toolDataCache = {};
var _toolCacheAge = {};

function loadToolData(toolKey, comp, isRefresh) {
  // If we have cached data and this is first open, skip loading spinner
  // The fetch below will update with fresh data
  var _expectedNodeId = 'node-' + toolKey;
  fetch('/api/component/tool/' + toolKey).then(function(r) { return r.json(); }).then(function(data) {
    // Guard: don't render if user switched to a different modal
    if (!isCompModalActive(_expectedNodeId)) return;
    _toolDataCache[toolKey] = data;
    _toolCacheAge[toolKey] = Date.now();
    var body = document.getElementById('comp-modal-body');
    var s = data.stats || {};
    var events = data.events || [];
    var color = TOOL_COLORS[toolKey] || '#555';
    var html = '';

    // ─── SESSION MODAL ─────────────────────────────────
    if (toolKey === 'session') {
      var agents = data.subagents || [];
      var active = agents.filter(function(a){return a.status==='active';}).length;
      var idle = agents.filter(function(a){return a.status==='idle';}).length;
      var stale = agents.filter(function(a){return a.status==='stale';}).length;

      html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#22c55e;">' + active + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Active</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#f59e0b;">' + idle + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Idle</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#ef4444;">' + stale + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Stale</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Calls Today</div></div>';
      html += '</div>';

      if (agents.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Sub-Agents</div>';
        html += '<div style="display:flex;flex-direction:column;gap:6px;max-height:50vh;overflow-y:auto;">';
        agents.forEach(function(a) {
          var dotColor = a.status==='active' ? '#22c55e' : a.status==='idle' ? '#f59e0b' : '#ef4444';
          var dotShadow = a.status==='active' ? 'box-shadow:0 0 6px rgba(34,197,94,0.6);' : '';
          html += '<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 12px;background:var(--bg-secondary);border-radius:10px;border:1px solid var(--border-secondary);">';
          html += '<div style="width:10px;height:10px;border-radius:50%;background:'+dotColor+';margin-top:4px;flex-shrink:0;'+dotShadow+'"></div>';
          html += '<div style="flex:1;min-width:0;">';
          html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
          html += '<span style="font-weight:600;font-size:13px;color:var(--text-primary);">' + escapeHtml(a.displayName || a.id || '?') + '</span>';
          html += '<span style="font-size:10px;color:var(--text-muted);">' + _timeAgo(a.updatedAt) + '</span>';
          html += '</div>';
          if (a.task) html += '<div style="font-size:12px;color:var(--text-secondary);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + escapeHtml(a.task) + '</div>';
          var meta = [];
          if (a.model) meta.push(a.model);
          if (a.tokens) meta.push(a.tokens >= 1000 ? (a.tokens/1000).toFixed(1)+'K tok' : a.tokens+' tok');
          if (a.channel) meta.push(a.channel);
          if (meta.length > 0) html += '<div style="font-size:10px;color:var(--text-muted);margin-top:2px;">' + escapeHtml(meta.join(' · ')) + '</div>';
          if (a.lastMessage) html += '<div style="font-size:11px;color:var(--text-tertiary);margin-top:4px;font-style:italic;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">"' + escapeHtml(a.lastMessage.substring(0,120)) + '"</div>';
          html += '</div></div>';
        });
        html += '</div>';
      } else if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Recent Session Activity</div>';
        html += _renderEventList(events, toolKey, color);
      } else {
        html += '<div style="text-align:center;padding:30px;color:var(--text-muted);">No active sub-agents</div>';
      }

    // ─── EXEC MODAL ────────────────────────────────────
    } else if (toolKey === 'exec') {
      var running = data.running_commands || [];
      html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#f59e0b;">' + running.length + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Running</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Total Today</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:'+ ((s.today_errors||0)>0?'#ef4444':'var(--text-primary)') +';">' + (s.today_errors||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
      html += '</div>';

      if (running.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">⚡ Running Now</div>';
        running.forEach(function(cmd) {
          html += '<div style="padding:8px 12px;background:#E6510011;border:1px solid #E6510033;border-radius:8px;margin-bottom:6px;font-family:monospace;font-size:12px;">';
          html += '<div style="display:flex;justify-content:space-between;"><span style="color:var(--text-primary);font-weight:600;">$ ' + escapeHtml((cmd.command||'').substring(0,120)) + '</span>';
          html += '<span class="pulse" style="width:8px;height:8px;"></span></div>';
          if (cmd.pid) html += '<span style="font-size:10px;color:var(--text-muted);">PID: ' + cmd.pid + '</span>';
          html += '</div>';
        });
      }

      if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin:12px 0 8px;">Recent Commands</div>';
        html += '<div style="max-height:45vh;overflow-y:auto;display:flex;flex-direction:column;gap:4px;">';
        events.forEach(function(evt) {
          var ts = _fmtToolTs(evt.timestamp);
          var isErr = evt.status === 'error';
          var borderColor = isErr ? '#ef444433' : 'var(--border-secondary)';
          html += '<div style="padding:6px 10px;background:var(--bg-secondary);border:1px solid '+borderColor+';border-radius:6px;">';
          html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
          html += '<code style="font-size:11px;color:var(--text-secondary);word-break:break-all;">$ ' + escapeHtml((evt.detail||'').substring(0,150)) + '</code>';
          html += '<span style="font-size:10px;color:var(--text-muted);white-space:nowrap;margin-left:8px;">' + ts + '</span>';
          html += '</div>';
          var meta = [];
          if (evt.duration_ms) meta.push(evt.duration_ms >= 1000 ? (evt.duration_ms/1000).toFixed(1)+'s' : evt.duration_ms+'ms');
          if (isErr) meta.push('<span style="color:#ef4444;">✗ error</span>');
          if (meta.length) html += '<div style="font-size:10px;color:var(--text-muted);margin-top:2px;">' + meta.join(' · ') + '</div>';
          html += '</div>';
        });
        html += '</div>';
      } else {
        html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No exec commands today</div>';
      }

    // ─── BROWSER/WEB MODAL ─────────────────────────────
    } else if (toolKey === 'browser') {
      var urls = data.recent_urls || [];
      html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Actions Today</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#6A1B9A;">' + urls.length + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">URLs Visited</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:'+ ((s.today_errors||0)>0?'#ef4444':'var(--text-primary)') +';">' + (s.today_errors||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
      html += '</div>';

      if (urls.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">🌐 Recent URLs</div>';
        html += '<div style="display:flex;flex-direction:column;gap:4px;margin-bottom:14px;">';
        urls.forEach(function(u) {
          html += '<div style="padding:6px 10px;background:var(--bg-secondary);border-radius:6px;display:flex;align-items:center;gap:8px;">';
          html += '<span style="font-size:14px;">🔗</span>';
          html += '<a href="' + escapeHtml(u.url||'') + '" target="_blank" style="font-size:12px;color:var(--text-link);text-decoration:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;">' + escapeHtml((u.url||'').substring(0,80)) + '</a>';
          html += '<span style="font-size:10px;color:var(--text-muted);white-space:nowrap;">' + _timeAgo(u.timestamp) + '</span>';
          html += '</div>';
        });
        html += '</div>';
      }

      if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Action Log</div>';
        html += '<div style="max-height:40vh;overflow-y:auto;display:flex;flex-direction:column;gap:4px;">';
        events.forEach(function(evt) {
          var ts = _fmtToolTs(evt.timestamp);
          var actionColors = {snapshot:'#3b82f6',navigate:'#8b5cf6',click:'#f59e0b',type:'#22c55e',screenshot:'#ec4899',open:'#06b6d4',act:'#f97316'};
          var ac = evt.action || 'unknown';
          var acColor = actionColors[ac] || '#6b7280';
          html += '<div style="padding:6px 10px;background:var(--bg-secondary);border-radius:6px;display:flex;align-items:center;gap:8px;font-size:12px;">';
          html += '<span style="background:'+acColor+'22;color:'+acColor+';padding:1px 8px;border-radius:4px;font-size:10px;font-weight:600;min-width:60px;text-align:center;">' + escapeHtml(ac) + '</span>';
          html += '<span style="color:var(--text-secondary);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escapeHtml((evt.detail||'').substring(0,100)) + '</span>';
          html += '<span style="color:var(--text-muted);font-size:10px;white-space:nowrap;">' + ts + '</span>';
          html += '</div>';
        });
        html += '</div>';
      } else {
        html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No browser actions today</div>';
      }

    // ─── SEARCH MODAL ──────────────────────────────────
    } else if (toolKey === 'search') {
      html += '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Searches Today</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:'+ ((s.today_errors||0)>0?'#ef4444':'var(--text-primary)') +';">' + (s.today_errors||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
      html += '</div>';

      if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Recent Searches</div>';
        html += '<div style="max-height:55vh;overflow-y:auto;display:flex;flex-direction:column;gap:6px;">';
        events.forEach(function(evt) {
          var ts = _fmtToolTs(evt.timestamp);
          html += '<div style="padding:10px 12px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border-secondary);">';
          html += '<div style="display:flex;justify-content:space-between;align-items:flex-start;">';
          html += '<div style="font-size:14px;font-weight:600;color:var(--text-primary);">🔍 ' + escapeHtml(evt.detail || '') + '</div>';
          html += '<span style="font-size:10px;color:var(--text-muted);white-space:nowrap;margin-left:8px;">' + ts + '</span>';
          html += '</div>';
          if (evt.result_count !== undefined) html += '<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">' + evt.result_count + ' results returned</div>';
          if (evt.status === 'error') html += '<div style="font-size:11px;color:#ef4444;margin-top:2px;">✗ Error</div>';
          html += '</div>';
        });
        html += '</div>';
      } else {
        html += '<div style="text-align:center;padding:30px;color:var(--text-muted);">No searches today</div>';
      }

    // ─── CRON MODAL ────────────────────────────────────
    } else if (toolKey === 'cron') {
      var jobs = data.cron_jobs || [];
      html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + jobs.length + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Cron Jobs</div></div>';
      var cronOk = jobs.filter(function(j){return j.lastStatus!=='error';}).length;
      var cronErr = jobs.filter(function(j){return j.lastStatus==='error';}).length;
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#22c55e;">' + cronOk + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Healthy</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:'+(cronErr>0?'#ef4444':'var(--text-primary)')+';">' + cronErr + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
      html += '</div>';

      if (jobs.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Scheduled Jobs</div>';
        html += '<div style="display:flex;flex-direction:column;gap:6px;max-height:55vh;overflow-y:auto;">';
        jobs.forEach(function(j) {
          var isErr = j.lastStatus === 'error';
          var borderLeft = isErr ? '3px solid #ef4444' : '3px solid #22c55e';
          html += '<div style="padding:10px 14px;background:var(--bg-secondary);border-radius:8px;border-left:'+borderLeft+';border:1px solid var(--border-secondary);border-left:'+borderLeft+';">';
          html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
          html += '<span style="font-weight:600;font-size:13px;color:var(--text-primary);">' + escapeHtml(j.name || j.task || j.id || '?') + '</span>';
          html += '<span style="padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;background:' + (isErr ? 'var(--bg-error);color:#ef4444' : 'var(--bg-success);color:#22c55e') + ';">' + (isErr ? 'ERROR' : 'OK') + '</span>';
          html += '</div>';
          var exprStr = typeof j.expr === 'object' ? (j.expr.expr || j.expr.at || ('every ' + Math.round((j.expr.everyMs||0)/60000) + 'm') || JSON.stringify(j.expr)) : (j.expr || j.schedule || '');
          html += '<div style="font-family:monospace;font-size:11px;color:var(--text-accent);margin-top:4px;">' + escapeHtml(exprStr) + '</div>';
          var meta = [];
          if (j.lastRun) meta.push('Last: ' + _fmtToolDate(j.lastRun));
          if (j.nextRun) meta.push('Next: ' + _fmtToolDate(j.nextRun));
          if (j.channel) meta.push('→ ' + j.channel);
          if (meta.length) html += '<div style="font-size:10px;color:var(--text-muted);margin-top:4px;">' + escapeHtml(meta.join(' · ')) + '</div>';
          if (isErr && j.lastError) html += '<div style="font-size:11px;color:#ef4444;margin-top:4px;background:#ef444411;padding:4px 8px;border-radius:4px;">' + escapeHtml((j.lastError||'').substring(0,200)) + '</div>';
          html += '</div>';
        });
        html += '</div>';
      } else if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Recent Cron Activity</div>';
        html += _renderEventList(events, toolKey, color);
      } else {
        html += '<div style="text-align:center;padding:30px;color:var(--text-muted);">No cron jobs configured</div>';
      }

    // ─── TTS MODAL ─────────────────────────────────────
    } else if (toolKey === 'tts') {
      html += '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + (s.today_calls||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Generations Today</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:'+ ((s.today_errors||0)>0?'#ef4444':'var(--text-primary)') +';">' + (s.today_errors||0) + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Errors</div></div>';
      html += '</div>';

      if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Recent TTS Generations</div>';
        html += '<div style="max-height:55vh;overflow-y:auto;display:flex;flex-direction:column;gap:6px;">';
        events.forEach(function(evt) {
          var ts = _fmtToolTs(evt.timestamp);
          html += '<div style="padding:10px 12px;background:var(--bg-secondary);border-radius:8px;border-left:3px solid #F9A825;">';
          html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
          html += '<span style="font-size:14px;">🔊</span>';
          html += '<span style="font-size:10px;color:var(--text-muted);">' + ts + '</span>';
          html += '</div>';
          html += '<div style="font-size:13px;color:var(--text-secondary);margin-top:6px;font-style:italic;line-height:1.4;">"' + escapeHtml((evt.detail || '').substring(0, 200)) + '"</div>';
          if (evt.voice) html += '<div style="font-size:10px;color:var(--text-muted);margin-top:4px;">🎤 Voice: ' + escapeHtml(evt.voice) + '</div>';
          if (evt.duration_ms) html += '<span style="font-size:10px;color:var(--text-muted);">' + (evt.duration_ms>=1000?(evt.duration_ms/1000).toFixed(1)+'s':evt.duration_ms+'ms') + '</span>';
          html += '</div>';
        });
        html += '</div>';
      } else {
        html += '<div style="text-align:center;padding:30px;color:var(--text-muted);">No TTS generations today</div>';
      }

    // ─── MEMORY MODAL ──────────────────────────────────
    } else if (toolKey === 'memory') {
      var files = data.memory_files || [];
      var reads = events.filter(function(e){return e.action!=='write';}).length;
      var writes = events.filter(function(e){return e.action==='write';}).length;
      html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#3b82f6;">' + reads + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Reads</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:#f59e0b;">' + writes + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Writes</div></div>';
      html += '<div style="background:var(--bg-secondary);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:24px;font-weight:700;color:var(--text-primary);">' + files.length + '</div><div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">Files</div></div>';
      html += '</div>';

      if (files.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Workspace Files</div>';
        html += '<div style="display:flex;flex-direction:column;gap:3px;margin-bottom:14px;">';
        files.forEach(function(f) {
          var sizeStr = f.size >= 1024 ? (f.size/1024).toFixed(1)+'KB' : f.size+'B';
          html += '<div style="padding:6px 10px;background:var(--bg-secondary);border-radius:6px;display:flex;align-items:center;gap:8px;font-size:12px;">';
          html += '<span style="font-size:14px;">📄</span>';
          html += '<span style="color:var(--text-link);font-family:monospace;flex:1;">' + escapeHtml(f.path) + '</span>';
          html += '<span style="color:var(--text-muted);font-size:11px;">' + sizeStr + '</span>';
          html += '</div>';
        });
        html += '</div>';
      }

      if (events.length > 0) {
        html += '<div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Recent File Operations</div>';
        html += '<div style="max-height:40vh;overflow-y:auto;display:flex;flex-direction:column;gap:4px;">';
        events.forEach(function(evt) {
          var ts = _fmtToolTs(evt.timestamp);
          var isWrite = evt.action === 'write';
          var badge = isWrite ? '<span style="background:#f59e0b33;color:#f59e0b;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;">WRITE</span>' : '<span style="background:#3b82f633;color:#3b82f6;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;">READ</span>';
          html += '<div style="padding:6px 10px;background:var(--bg-secondary);border-radius:6px;display:flex;align-items:center;gap:8px;font-size:12px;">';
          html += badge;
          html += '<code style="color:var(--text-secondary);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escapeHtml(evt.detail || '') + '</code>';
          html += '<span style="color:var(--text-muted);font-size:10px;white-space:nowrap;">' + ts + '</span>';
          html += '</div>';
        });
        html += '</div>';
      } else {
        html += '<div style="text-align:center;padding:20px;color:var(--text-muted);">No file operations today</div>';
      }

    // ─── FALLBACK ──────────────────────────────────────
    } else {
      html += '<div style="display:flex;gap:12px;padding:10px 16px;background:' + color + '22;border-radius:10px;margin-bottom:14px;align-items:center;flex-wrap:wrap;">';
      html += '<span style="font-size:13px;font-weight:600;color:' + color + ';">Today: ' + (s.today_calls||0) + ' calls</span>';
      if (s.today_errors > 0) html += '<span style="font-size:13px;font-weight:600;color:#ef4444;">| ' + s.today_errors + ' errors</span>';
      html += '</div>';
      html += _renderEventList(events, toolKey, color);
    }

    body.innerHTML = html;
    document.getElementById('comp-modal-footer').textContent = 'Auto-refreshing · Last updated: ' + new Date().toLocaleTimeString() + ' · ' + (data.total||0) + ' events today';
  }).catch(function(e) {
    if (!isCompModalActive(_expectedNodeId)) return;
    if (!isRefresh) {
      document.getElementById('comp-modal-body').innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-error);">Failed to load data: ' + e + '</div>';
    }
  });
}

function _renderEventList(events, toolKey, color) {
  if (events.length === 0) return '<div style="text-align:center;padding:30px;color:var(--text-muted);">No events today</div>';
  var html = '<div style="max-height:50vh;overflow-y:auto;display:flex;flex-direction:column;gap:4px;">';
  events.forEach(function(evt) {
    var ts = _fmtToolTs(evt.timestamp);
    var isErr = evt.status === 'error';
    html += '<div style="padding:6px 10px;background:var(--bg-secondary);border-radius:6px;border:1px solid '+(isErr?'#ef444433':'var(--border-secondary)')+';font-size:12px;">';
    html += '<div style="display:flex;justify-content:space-between;"><span style="color:var(--text-secondary);">' + escapeHtml(evt.detail||evt.action||'') + '</span>';
    html += '<span style="color:var(--text-muted);font-size:10px;">' + ts + '</span></div>';
    html += '</div>';
  });
  html += '</div>';
  return html;
}

function closeCompModal() {
  if (_tgRefreshTimer) { clearInterval(_tgRefreshTimer); _tgRefreshTimer = null; }
  if (_gwRefreshTimer) { clearInterval(_gwRefreshTimer); _gwRefreshTimer = null; }
  if (_brainRefreshTimer) { clearInterval(_brainRefreshTimer); _brainRefreshTimer = null; }
  if (_toolRefreshTimer) { clearInterval(_toolRefreshTimer); _toolRefreshTimer = null; }
  if (_costOptimizerRefreshTimer) { clearInterval(_costOptimizerRefreshTimer); _costOptimizerRefreshTimer = null; }
  
  // Reset time travel state
  _timeTravelMode = false;
  _currentTimeContext = null;
  window._currentComponentId = null;
  
  document.getElementById('comp-modal-overlay').classList.remove('open');
}
document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeCompModal(); });
document.addEventListener('DOMContentLoaded', initCompClickHandlers);

// Pre-fetch tool data so modals open instantly
function _prefetchToolData() {
  var tools = ['session','exec','browser','search','cron','tts','memory','brain','telegram','gateway','runtime','machine'];
  tools.forEach(function(t) {
    fetch('/api/component/tool/' + t).then(function(r){return r.json();}).then(function(data) {
      _toolDataCache[t] = data;
      _toolCacheAge[t] = Date.now();
    }).catch(function(){});
  });
}
document.addEventListener('DOMContentLoaded', function() {
  setTimeout(_prefetchToolData, 2000); // prefetch 2s after load
  setInterval(_prefetchToolData, 30000); // refresh cache every 30s
});

function openTaskModal(sessionId, taskName, sessionKey) {
  _modalSessionId = sessionId;
  document.getElementById('modal-title').textContent = taskName || sessionId;
  document.getElementById('modal-session-key').textContent = sessionKey || sessionId;
  document.getElementById('task-modal-overlay').classList.add('open');
  document.getElementById('modal-content').innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);">Loading transcript...</div>';
  _modalTab = 'summary';
  document.querySelectorAll('.modal-tab').forEach(function(t,i){t.classList.toggle('active',i===0);});
  loadModalTranscript();
  if (_modalAutoRefresh) {
    _modalRefreshTimer = setInterval(loadModalTranscript, 4000);
  }
  document.addEventListener('keydown', _modalEscHandler);
}

function closeTaskModal() {
  document.getElementById('task-modal-overlay').classList.remove('open');
  _modalSessionId = null;
  if (_modalRefreshTimer) { clearInterval(_modalRefreshTimer); _modalRefreshTimer = null; }
  document.removeEventListener('keydown', _modalEscHandler);
}

function _modalEscHandler(e) { if (e.key === 'Escape') closeTaskModal(); }

function toggleModalAutoRefresh() {
  _modalAutoRefresh = document.getElementById('modal-auto-refresh-cb').checked;
  if (_modalRefreshTimer) { clearInterval(_modalRefreshTimer); _modalRefreshTimer = null; }
  if (_modalAutoRefresh && _modalSessionId) {
    _modalRefreshTimer = setInterval(loadModalTranscript, 4000);
  }
}

function switchModalTab(tab) {
  _modalTab = tab;
  document.querySelectorAll('.modal-tab').forEach(function(t){ t.classList.toggle('active', t.textContent.toLowerCase().indexOf(tab) >= 0 || (tab==='full' && t.textContent==='Full Logs')); });
  renderModalContent();
}

async function loadModalTranscript() {
  if (!_modalSessionId) return;
  try {
    var r = await fetch('/api/transcript-events/' + encodeURIComponent(_modalSessionId));
    var data = await r.json();
    if (data.error) {
      document.getElementById('modal-content').innerHTML = '<div style="padding:20px;color:var(--text-error);">Error: ' + escHtml(data.error) + '</div>';
      return;
    }
    _modalEvents = data.events || [];
    document.getElementById('modal-event-count').textContent = '📊 ' + _modalEvents.length + ' events';
    document.getElementById('modal-msg-count').textContent = '💬 ' + (data.messageCount || 0) + ' messages';
    renderModalContent();
  } catch(e) {
    document.getElementById('modal-content').innerHTML = '<div style="padding:20px;color:var(--text-error);">Failed to load transcript</div>';
  }
}

function renderModalContent() {
  var el = document.getElementById('modal-content');
  if (_modalTab === 'summary') renderModalSummary(el);
  else if (_modalTab === 'narrative') renderModalNarrative(el);
  else renderModalFull(el);
}

function renderModalSummary(el) {
  var events = _modalEvents;
  // Find first user message as task description
  var desc = '';
  var result = '';
  for (var i = 0; i < events.length; i++) {
    if (events[i].type === 'user' && !desc) {
      desc = events[i].text || '';
      if (desc.length > 500) desc = desc.substring(0, 500) + '...';
    }
  }
  // Find last assistant text as result
  for (var i = events.length - 1; i >= 0; i--) {
    if (events[i].type === 'agent' && events[i].text) {
      result = events[i].text;
      if (result.length > 1000) result = result.substring(0, 1000) + '...';
      break;
    }
  }
  var html = '';
  var renderMd = (typeof marked !== 'undefined' && marked.parse) ? function(s){ return marked.parse(s); } : escHtml;
  html += '<div class="summary-section"><div class="summary-label">Task Description</div>';
  html += '<div class="summary-text md-rendered">' + renderMd(desc || 'No description found') + '</div></div>';
  html += '<div class="summary-section"><div class="summary-label">Final Result / Output</div>';
  html += '<div class="summary-text md-rendered">' + renderMd(result || 'No result yet...') + '</div></div>';
  el.innerHTML = html;
}

function renderModalNarrative(el) {
  var events = _modalEvents;
  var html = '';
  events.forEach(function(evt) {
    var icon = '', text = '';
    if (evt.type === 'user') {
      icon = '👤'; text = 'User sent: <code>' + escHtml((evt.text||'').substring(0, 150)) + '</code>';
    } else if (evt.type === 'agent') {
      icon = '🤖'; text = 'Agent said: <code>' + escHtml((evt.text||'').substring(0, 200)) + '</code>';
    } else if (evt.type === 'thinking') {
      icon = '💭'; text = 'Agent thought about the problem...';
    } else if (evt.type === 'exec') {
      icon = '⚡'; text = 'Ran command: <code>' + escHtml(evt.command||'') + '</code>';
    } else if (evt.type === 'read') {
      icon = '📖'; text = 'Read file: <code>' + escHtml(evt.file||'') + '</code>';
    } else if (evt.type === 'tool') {
      icon = '🔧'; text = 'Called tool: <code>' + escHtml(evt.toolName||'') + '</code>';
    } else if (evt.type === 'result') {
      icon = '🔍'; text = 'Got result (' + (evt.text||'').length + ' chars)';
    } else return;
    html += '<div class="narrative-item"><span class="narr-icon">' + icon + '</span>' + text + '</div>';
  });
  el.innerHTML = html || '<div style="padding:20px;color:var(--text-muted);">No events yet</div>';
}

function renderModalFull(el) {
  var events = _modalEvents;
  var html = '';
  events.forEach(function(evt, idx) {
    var icon = '📝', typeClass = '', summary = '', body = '';
    var ts = evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : '';
    if (evt.type === 'agent') {
      icon = '🤖'; typeClass = 'type-agent';
      summary = '<strong>Agent</strong> - ' + escHtml((evt.text||'').substring(0, 120));
      body = evt.text || '';
    } else if (evt.type === 'thinking') {
      icon = '💭'; typeClass = 'type-thinking';
      summary = '<strong>Thinking</strong> - ' + escHtml((evt.text||'').substring(0, 120));
      body = evt.text || '';
    } else if (evt.type === 'user') {
      icon = '👤'; typeClass = 'type-user';
      summary = '<strong>User</strong> - ' + escHtml((evt.text||'').substring(0, 120));
      body = evt.text || '';
    } else if (evt.type === 'exec') {
      icon = '⚡'; typeClass = 'type-exec';
      summary = '<strong>EXEC</strong> - <code>' + escHtml(evt.command||'') + '</code>';
      body = evt.command || '';
    } else if (evt.type === 'read') {
      icon = '📖'; typeClass = 'type-read';
      summary = '<strong>READ</strong> - ' + escHtml(evt.file||'');
      body = evt.file || '';
    } else if (evt.type === 'tool') {
      icon = '🔧'; typeClass = 'type-exec';
      summary = '<strong>' + escHtml(evt.toolName||'tool') + '</strong> - ' + escHtml((evt.args||'').substring(0, 100));
      body = evt.args || '';
    } else if (evt.type === 'result') {
      icon = '🔍'; typeClass = 'type-result';
      summary = '<strong>Result</strong> - ' + escHtml((evt.text||'').substring(0, 120));
      body = evt.text || '';
    } else {
      summary = '<strong>' + escHtml(evt.type) + '</strong>';
      body = JSON.stringify(evt, null, 2);
    }
    var bodyId = 'evt-body-' + idx;
    html += '<div class="evt-item ' + typeClass + '">';
    html += '<div class="evt-header" onclick="var b=document.getElementById(\'' + bodyId + '\');b.classList.toggle(\'open\');">';
    html += '<span class="evt-icon">' + icon + '</span>';
    html += '<span class="evt-summary">' + summary + '</span>';
    html += '<span class="evt-ts">' + escHtml(ts) + '</span>';
    html += '</div>';
    var bodyHtml = (typeof marked !== 'undefined' && marked.parse) ? marked.parse(body) : escHtml(body);
    html += '<div class="evt-body md-rendered" id="' + bodyId + '">' + bodyHtml + '</div>';
    html += '</div>';
  });
  el.innerHTML = html || '<div style="padding:20px;color:var(--text-muted);">No events yet</div>';
}

// Initialize theme and zoom on page load
function setBootStep(stepId, state, subtitle) {
  var el = document.getElementById('boot-step-' + stepId);
  if (!el) return;
  el.classList.remove('loading', 'done', 'fail');
  if (state) el.classList.add(state);
  if (subtitle) {
    var textEl = el.querySelector('span:last-child');
    if (textEl) textEl.textContent = subtitle;
  }
}

function finishBootOverlay() {
  var overlay = document.getElementById('boot-overlay');
  document.body.classList.remove('booting');
  document.body.classList.add('app-ready');
  if (overlay) {
    overlay.classList.add('hide');
    setTimeout(function() { if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay); }, 350);
  }
}

async function bootDashboard() {
  setBootStep('overview', 'loading', 'Loading overview + model context');
  var okOverview = await loadAll();
  setBootStep('overview', okOverview ? 'done' : 'fail', okOverview ? 'Overview ready' : 'Overview delayed');

  setBootStep('tasks', 'loading', 'Loading active tasks');
  var okTasks = await loadOverviewTasks();
  setBootStep('tasks', okTasks ? 'done' : 'fail', okTasks ? 'Tasks ready' : 'Tasks delayed');

  setBootStep('health', 'loading', 'Loading system health');
  var okHealth = await loadSystemHealth();
  setBootStep('health', okHealth ? 'done' : 'fail', okHealth ? 'System health ready' : 'System health delayed');

  setBootStep('streams', 'loading', 'Connecting live streams');
  try { startLogStream(); } catch (e) {}
  try { startHealthStream(); } catch (e) {}
  setBootStep('streams', 'done', 'Live streams connected');

  // Pre-fetch crons and memory so they're ready when tabs are clicked
  try { await loadCrons(); } catch (e) { console.warn('Crons prefetch failed:', e); }
  try { await loadMemory(); } catch (e) { console.warn('Memory prefetch failed:', e); }

  startSystemHealthRefresh();
  startOverviewRefresh();
  startOverviewTasksRefresh();
  startActiveTasksRefresh();

  var sub = document.getElementById('boot-sub');
  if (sub) sub.textContent = 'Dashboard ready';
  setTimeout(finishBootOverlay, 180);
}

document.addEventListener('DOMContentLoaded', function() {
  initTheme();
  initZoom();
  // Overview is the default tab
  initOverviewFlow();
  initOverviewCompClickHandlers();
  initFlow();
  bootDashboard();
});
</script>
</div> <!-- end zoom-wrapper -->

<!-- Component Detail Modal -->
<div class="comp-modal-overlay" id="comp-modal-overlay" onclick="if(event.target===this)closeCompModal()">
  <div class="comp-modal-card">
    <div class="comp-modal-header">
      <div class="comp-modal-title" id="comp-modal-title">Component</div>
      <div style="display: flex; align-items: center; gap: 10px;">
        <div class="time-travel-toggle" id="time-travel-toggle" onclick="toggleTimeTravelMode()" title="Enable time travel">🕰️</div>
        <div class="comp-modal-close" onclick="closeCompModal()">&times;</div>
      </div>
    </div>
    <div class="time-travel-bar" id="time-travel-bar">
      <div class="time-travel-controls">
        <div class="time-nav-btn" onclick="timeTravel('prev-day')" title="Previous day">‹</div>
        <div class="time-scrubber">
          <div class="time-slider" id="time-slider" onclick="onTimeSliderClick(event)">
            <div class="time-slider-thumb" id="time-slider-thumb"></div>
          </div>
          <div class="time-display" id="time-display">Loading...</div>
        </div>
        <div class="time-nav-btn" onclick="timeTravel('next-day')" title="Next day">›</div>
        <div class="time-nav-btn" onclick="timeTravel('now')" title="Back to now">⏹</div>
      </div>
    </div>
    <div class="comp-modal-body" id="comp-modal-body">Loading...</div>
    <div class="comp-modal-footer" id="comp-modal-footer">Last updated: —</div>
  </div>
</div>

<!-- Task Detail Modal -->
<div class="modal-overlay" id="task-modal-overlay" onclick="if(event.target===this)closeTaskModal()">
  <div class="modal-card">
    <div class="modal-header">
      <div class="modal-header-left">
        <div class="modal-title" id="modal-title">Task Name</div>
        <div class="modal-session-key" id="modal-session-key">session-id</div>
      </div>
      <div class="modal-header-right">
        <label class="modal-auto-refresh"><input type="checkbox" id="modal-auto-refresh-cb" checked onchange="toggleModalAutoRefresh()"> Auto-refresh</label>
        <div class="modal-close" onclick="closeTaskModal()">&times;</div>
      </div>
    </div>
    <div class="modal-tabs">
      <div class="modal-tab active" onclick="switchModalTab('summary')">Summary</div>
      <div class="modal-tab" onclick="switchModalTab('narrative')">Narrative</div>
      <div class="modal-tab" onclick="switchModalTab('full')">Full Logs</div>
    </div>
    <div class="modal-content" id="modal-content">Loading...</div>
    <div class="modal-footer">
      <span id="modal-event-count">—</span>
      <span id="modal-msg-count">—</span>
    </div>
  </div>
</div>

<!-- Gateway Setup Wizard -->
<div id="gw-setup-overlay" data-mandatory="false" onclick="if(event.target===this && this.dataset.mandatory!=='true'){this.style.display='none'}" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:10000; align-items:center; justify-content:center; font-family:Manrope,sans-serif;">
  <div style="background:var(--bg-secondary, #1a1a2e); border:1px solid var(--border-primary, #333); border-radius:16px; padding:40px; max-width:440px; width:90%; text-align:center; box-shadow:0 20px 60px rgba(0,0,0,0.5); position:relative;">
    <button id="gw-setup-close" onclick="document.getElementById('gw-setup-overlay').style.display='none'" style="display:none; position:absolute; top:12px; right:16px; background:none; border:none; color:var(--text-muted, #888); font-size:22px; cursor:pointer; padding:4px 8px; line-height:1;">✕</button>
    <div style="font-size:48px; margin-bottom:16px;">🦞</div>
    <h2 style="color:var(--text-primary, #fff); margin:0 0 8px; font-size:24px; font-weight:700;">ClawMetry Setup</h2>
    <p style="color:var(--text-muted, #888); margin:0 0 24px; font-size:14px;">Enter your OpenClaw gateway token to connect.</p>
    <input id="gw-token-input" type="password" placeholder="Paste your gateway token" 
      style="width:100%; padding:12px 16px; border:1px solid var(--border-primary, #444); border-radius:8px; background:var(--bg-primary, #111); color:var(--text-primary, #fff); font-size:14px; font-family:monospace; box-sizing:border-box; outline:none; margin-bottom:8px;"
      onkeydown="if(event.key==='Enter')gwSetupConnect()">
    <p id="gw-setup-hint" style="color:var(--text-muted, #888); font-size:12px; margin:0 0 4px; text-align:left;">Find it: <code style="color:var(--text-accent, #0af); background:rgba(0,170,255,0.1); padding:2px 6px; border-radius:4px;">docker exec $(docker ps -q) env | grep TOKEN</code> or <code style="color:var(--text-accent, #0af); background:rgba(0,170,255,0.1); padding:2px 6px; border-radius:4px;">gateway.auth.token</code></p>
    <p id="gw-url-hint" style="color:var(--text-muted, #666); font-size:11px; margin:0 0 16px; text-align:left;">Optional: <input id="gw-url-input" type="text" placeholder="http://localhost:18789 (auto-detected)" style="width:70%; padding:4px 8px; border:1px solid var(--border-primary, #444); border-radius:4px; background:var(--bg-primary, #111); color:var(--text-primary, #fff); font-size:11px; font-family:monospace;"></p>
    <div id="gw-setup-error" style="color:#ff4444; font-size:13px; margin-bottom:12px; display:none;"></div>
    <div id="gw-setup-status" style="color:var(--text-accent, #0af); font-size:13px; margin-bottom:12px; display:none;"></div>
    <button onclick="gwSetupConnect()" id="gw-connect-btn"
      style="width:100%; padding:12px; border:none; border-radius:8px; background:var(--bg-accent, #0f6fff); color:#fff; font-size:15px; font-weight:600; cursor:pointer; font-family:Manrope,sans-serif;">
      Connect
    </button>
    <p style="color:var(--text-faint, #555); font-size:11px; margin:16px 0 0;">Token is stored locally on this ClawMetry instance.</p>
  </div>
</div>

<script>
// Gateway setup wizard
async function checkGwConfig() {
  try {
    const r = await fetch('/api/gw/config');
    const d = await r.json();
    if (!d.configured) {
      // Check localStorage first
      const saved = localStorage.getItem('clawmetry-gw-token');
      if (saved) {
        // Try auto-connecting with saved token
        const r2 = await fetch('/api/gw/config', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({token: saved})
        });
        const d2 = await r2.json();
        if (d2.ok) { updateGwStatus(true, d2.url); return; }
      }
      document.getElementById('gw-setup-overlay').style.display = 'flex';
    } else {
      updateGwStatus(true, d.url);
    }
  } catch(e) {}
}

function updateGwStatus(connected, url) {
  const dot = document.getElementById('gw-status-dot');
  if (!dot) return;
  dot.style.color = connected ? '#4ade80' : '#f87171';
  dot.title = connected ? 'Gateway: connected' + (url ? ' (' + url + ')' : '') : 'Gateway: disconnected';
}

async function gwSetupConnect() {
  const btn = document.getElementById('gw-connect-btn');
  const errEl = document.getElementById('gw-setup-error');
  const statusEl = document.getElementById('gw-setup-status');
  const token = document.getElementById('gw-token-input').value.trim();
  const url = document.getElementById('gw-url-input').value.trim();
  
  errEl.style.display = 'none';
  if (!token) { errEl.textContent = 'Please enter a token'; errEl.style.display = 'block'; return; }
  
  btn.textContent = 'Scanning for gateway...';
  btn.disabled = true;
  statusEl.textContent = 'Scanning ports to find your OpenClaw gateway...';
  statusEl.style.display = 'block';
  
  try {
    const r = await fetch('/api/gw/config', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({token, url})
    });
    const d = await r.json();
    if (d.ok) {
      statusEl.textContent = 'Connected to ' + d.url;
      btn.textContent = 'Connected!';
      localStorage.setItem('clawmetry-gw-token', token);
      localStorage.setItem('clawmetry-token', token);
      updateGwStatus(true, d.url);
      setTimeout(() => {
        document.getElementById('gw-setup-overlay').style.display = 'none';
        location.reload();
      }, 800);
    } else {
      errEl.textContent = d.error || 'Connection failed';
      errEl.style.display = 'block';
      btn.textContent = 'Connect';
      btn.disabled = false;
      statusEl.style.display = 'none';
    }
  } catch(e) {
    errEl.textContent = 'Network error: ' + e.message;
    errEl.style.display = 'block';
    btn.textContent = 'Connect';
    btn.disabled = false;
    statusEl.style.display = 'none';
  }
}

// Check on load
document.addEventListener('DOMContentLoaded', checkGwConfig);
</script>

</body>
</html>
"""


# ── API Routes ──────────────────────────────────────────────────────────

def _acquire_stream_slot(kind):
    """Bound concurrent SSE clients per stream type."""
    global _active_log_stream_clients, _active_health_stream_clients
    with _stream_clients_lock:
        if kind == 'log':
            if _active_log_stream_clients >= MAX_LOG_STREAM_CLIENTS:
                return False
            _active_log_stream_clients += 1
            return True
        if kind == 'health':
            if _active_health_stream_clients >= MAX_HEALTH_STREAM_CLIENTS:
                return False
            _active_health_stream_clients += 1
            return True
    return False


def _release_stream_slot(kind):
    global _active_log_stream_clients, _active_health_stream_clients
    with _stream_clients_lock:
        if kind == 'log':
            _active_log_stream_clients = max(0, _active_log_stream_clients - 1)
        elif kind == 'health':
            _active_health_stream_clients = max(0, _active_health_stream_clients - 1)


# ── Gateway API proxy (WebSocket JSON-RPC + HTTP fallback) ──────────────
import urllib.request as _urllib_req
import urllib.error as _urllib_err
import uuid as _uuid

_GW_CONFIG_FILE = os.path.expanduser('~/.clawmetry-gateway.json')

# ── WebSocket RPC Client ────────────────────────────────────────────────
_ws_client = None
_ws_lock = threading.Lock()
_ws_connected = False


def _gw_ws_connect(url=None, token=None):
    """Connect to the OpenClaw gateway via WebSocket JSON-RPC."""
    global _ws_client, _ws_connected
    try:
        import websocket
    except ImportError:
        return False

    cfg = _load_gw_config()
    ws_url = (url or cfg.get('url', '') or '').replace('http://', 'ws://').replace('https://', 'wss://').rstrip('/')
    tok = token or cfg.get('token', '')
    if not ws_url or not tok:
        return False

    try:
        ws = websocket.create_connection(f'{ws_url}/', timeout=5)
        # Read challenge event
        ws.recv()
        # Send connect
        connect_msg = {
            'type': 'req', 'id': 'clawmetry-connect', 'method': 'connect',
            'params': {
                'minProtocol': 3, 'maxProtocol': 3,
                'client': {'id': 'cli', 'version': __version__, 'platform': 'linux',
                           'mode': 'cli', 'instanceId': f'clawmetry-{_uuid.uuid4().hex[:8]}'},
                'role': 'operator', 'scopes': ['operator.admin'],
                'auth': {'token': tok},
            }
        }
        ws.send(json.dumps(connect_msg))
        # Wait for connect response
        for _ in range(5):
            r = json.loads(ws.recv())
            if r.get('type') == 'res' and r.get('id') == 'clawmetry-connect':
                if r.get('ok'):
                    _ws_client = ws
                    _ws_connected = True
                    return True
                else:
                    ws.close()
                    return False
        ws.close()
    except Exception:
        pass
    return False


def _gw_ws_rpc(method, params=None):
    """Make a JSON-RPC call over the WebSocket connection. Returns payload or None."""
    global _ws_client, _ws_connected
    with _ws_lock:
        if not _ws_connected or _ws_client is None:
            if not _gw_ws_connect():
                return None
        try:
            mid = f'cm-{_uuid.uuid4().hex[:8]}'
            msg = {'type': 'req', 'id': mid, 'method': method, 'params': params or {}}
            _ws_client.send(json.dumps(msg))
            # Read responses, skipping events
            for _ in range(30):
                r = json.loads(_ws_client.recv())
                if r.get('type') == 'res' and r.get('id') == mid:
                    if r.get('ok'):
                        return r.get('payload', {})
                    else:
                        return None
        except Exception:
            # Connection lost, reset
            _ws_connected = False
            try:
                _ws_client.close()
            except Exception:
                pass
            _ws_client = None
    return None


def _load_gw_config():
    """Load gateway config from globals, env, or file."""
    global GATEWAY_URL, GATEWAY_TOKEN
    # Already set via CLI/env/auto-detect
    if GATEWAY_URL and GATEWAY_TOKEN:
        return {'url': GATEWAY_URL, 'token': GATEWAY_TOKEN}
    # Try config file
    try:
        with open(_GW_CONFIG_FILE) as f:
            cfg = json.load(f)
            GATEWAY_URL = cfg.get('url', GATEWAY_URL)
            GATEWAY_TOKEN = cfg.get('token', GATEWAY_TOKEN)
            return cfg
    except Exception:
        pass
    # Auto-detect from environment/process
    token = _detect_gateway_token()
    port = _detect_gateway_port()
    if token:
        GATEWAY_TOKEN = token
        GATEWAY_URL = f'http://127.0.0.1:{port}'
        return {'url': GATEWAY_URL, 'token': GATEWAY_TOKEN}
    return {}


def _gw_invoke(tool, args=None):
    """Invoke a tool via the OpenClaw gateway /tools/invoke endpoint.
    Tries: 1) Direct HTTP, 2) Docker exec fallback."""
    cfg = _load_gw_config()
    token = cfg.get('token')
    url = cfg.get('url')
    
    # Try direct HTTP first
    if url and token:
        try:
            payload = json.dumps({'tool': tool, 'args': args or {}}).encode()
            req = _urllib_req.Request(
                f"{url.rstrip('/')}/tools/invoke",
                data=payload,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                },
                method='POST'
            )
            with _urllib_req.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                if data.get('ok'):
                    return data.get('result', {}).get('details', data.get('result', {}))
        except Exception:
            pass
    
    # Fallback: docker exec (for Hostinger/Docker installs where gateway binds to loopback)
    if token:
        result = _gw_invoke_docker(tool, args, token)
        if result:
            return result
    
    return None

def _gw_invoke_docker(tool, args=None, token=None):
    """Invoke gateway API via docker exec (when gateway is inside Docker)."""
    try:
        container_id = subprocess.check_output(
            ['docker', 'ps', '-q'], timeout=3, stderr=subprocess.DEVNULL
        ).decode().strip().split('\n')[0]
        if not container_id:
            return None
        payload = json.dumps({'tool': tool, 'args': args or {}})
        cmd = [
            'docker', 'exec', container_id, 'curl', '-s', '--max-time', '8',
            '-X', 'POST', 'http://127.0.0.1:18789/tools/invoke',
            '-H', f'Authorization: Bearer {token}',
            '-H', 'Content-Type: application/json',
            '-d', payload
        ]
        output = subprocess.check_output(cmd, timeout=15, stderr=subprocess.DEVNULL).decode()
        if output:
            data = json.loads(output)
            if data.get('ok'):
                return data.get('result', {}).get('details', data.get('result', {}))
    except Exception:
        pass
    return None


@app.route('/api/gw/config', methods=['GET', 'POST'])
def api_gw_config():
    """Get or set gateway configuration."""
    global GATEWAY_URL, GATEWAY_TOKEN, _ws_client, _ws_connected
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        token = data.get('token', '').strip()
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        # Auto-discover gateway port by scanning common ports
        gw_url = data.get('url', '').strip()
        if not gw_url:
            gw_url = _auto_discover_gateway(token)
        if not gw_url:
            return jsonify({'error': 'Could not find OpenClaw gateway. Please provide URL.'}), 404
        # Validate the connection
        valid = False
        
        # Docker mode: skip HTTP/WS, validate via docker exec
        if gw_url.startswith('docker://'):
            result = _gw_invoke_docker('session_status', {}, token)
            if result:
                valid = True
        
        # WebSocket validation (non-docker)
        if not valid and not gw_url.startswith('docker://'):
            ws_url = gw_url.replace('http://', 'ws://').replace('https://', 'wss://')
            try:
                import websocket
                ws = websocket.create_connection(f'{ws_url}/', timeout=5)
                ws.recv()  # challenge
                connect_msg = {
                    'type': 'req', 'id': 'validate', 'method': 'connect',
                    'params': {
                        'minProtocol': 3, 'maxProtocol': 3,
                        'client': {'id': 'cli', 'version': __version__, 'platform': 'linux',
                                   'mode': 'cli', 'instanceId': 'clawmetry-validate'},
                        'role': 'operator', 'scopes': ['operator.admin'],
                        'auth': {'token': token},
                    }
                }
                ws.send(json.dumps(connect_msg))
                for _ in range(5):
                    r = json.loads(ws.recv())
                    if r.get('type') == 'res' and r.get('id') == 'validate':
                        valid = r.get('ok', False)
                        break
                ws.close()
            except Exception:
                pass
        
        # HTTP fallback validation (non-docker)
        if not valid and not gw_url.startswith('docker://'):
            try:
                payload = json.dumps({'tool': 'session_status', 'args': {}}).encode()
                req = _urllib_req.Request(
                    f"{gw_url.rstrip('/')}/tools/invoke",
                    data=payload,
                    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                    method='POST'
                )
                with _urllib_req.urlopen(req, timeout=5) as resp:
                    result = json.loads(resp.read())
                    valid = result.get('ok', False)
            except Exception:
                pass
        
        # Docker exec fallback (last resort)
        if not valid:
            result = _gw_invoke_docker('session_status', {}, token)
            if result:
                valid = True
                gw_url = 'docker://localhost:18789'
        
        if not valid:
            return jsonify({'error': 'Invalid token or gateway not responding'}), 401
        # Save config
        GATEWAY_URL = gw_url
        GATEWAY_TOKEN = token
        # Reset WS connection to use new credentials
        _ws_connected = False
        _ws_client = None
        cfg = {'url': gw_url, 'token': token}
        try:
            with open(_GW_CONFIG_FILE, 'w') as f:
                json.dump(cfg, f)
        except Exception:
            pass
        return jsonify({'ok': True, 'url': gw_url})
    else:
        cfg = _load_gw_config()
        return jsonify({
            'configured': bool(cfg.get('url') and cfg.get('token')),
            'url': cfg.get('url', ''),
            'hasToken': bool(cfg.get('token')),
        })


@app.route('/api/gw/invoke', methods=['POST'])
def api_gw_invoke():
    """Proxy a tool invocation to the OpenClaw gateway."""
    data = request.get_json(silent=True) or {}
    tool = data.get('tool')
    args = data.get('args', {})
    if not tool:
        return jsonify({'error': 'tool is required'}), 400
    result = _gw_invoke(tool, args)
    if result is None:
        return jsonify({'error': 'Gateway not configured or unreachable'}), 503
    return jsonify(result)


@app.route('/api/gw/rpc', methods=['POST'])
def api_gw_rpc():
    """Proxy a JSON-RPC method call to the OpenClaw gateway via WebSocket."""
    data = request.get_json(silent=True) or {}
    method = data.get('method', '')
    params = data.get('params', {})
    if not method:
        return jsonify({'error': 'method is required'}), 400
    result = _gw_ws_rpc(method, params)
    if result is None:
        return jsonify({'error': 'Gateway not connected or method failed'}), 503
    return jsonify(result)


def _auto_discover_gateway(token):
    """Scan common ports to find an OpenClaw gateway."""
    common_ports = [18789, 56089]
    # Also check env and config files
    env_port = os.environ.get('OPENCLAW_GATEWAY_PORT')
    if env_port:
        try:
            common_ports.insert(0, int(env_port))
        except ValueError:
            pass
    # Add ports from config files
    for cfg_name in ['moltbot.json', 'clawdbot.json', 'openclaw.json']:
        for base in [os.path.expanduser('~/.openclaw'), os.path.expanduser('~/.clawdbot')]:
            try:
                with open(os.path.join(base, cfg_name)) as f:
                    c = json.load(f)
                    p = c.get('gateway', {}).get('port')
                    if p and p not in common_ports:
                        common_ports.insert(0, int(p))
            except Exception:
                pass
    # Scan for additional ports
    for port_offset in range(0, 100):
        p = 18700 + port_offset
        if p not in common_ports:
            common_ports.append(p)

    for port in common_ports[:20]:  # Cap at 20 ports to scan
        # Try WebSocket first, then HTTP
        url = f"http://127.0.0.1:{port}"
        ws_url = f"ws://127.0.0.1:{port}"
        try:
            import websocket
            ws = websocket.create_connection(f'{ws_url}/', timeout=2)
            ws.recv()  # challenge
            connect_msg = {
                'type': 'req', 'id': 'discover', 'method': 'connect',
                'params': {
                    'minProtocol': 3, 'maxProtocol': 3,
                    'client': {'id': 'cli', 'version': __version__, 'platform': 'linux',
                               'mode': 'cli', 'instanceId': 'clawmetry-discover'},
                    'role': 'operator', 'scopes': ['operator.admin'],
                    'auth': {'token': token},
                }
            }
            ws.send(json.dumps(connect_msg))
            for _ in range(5):
                r = json.loads(ws.recv())
                if r.get('type') == 'res' and r.get('id') == 'discover':
                    ws.close()
                    if r.get('ok'):
                        return url
                    break
            try:
                ws.close()
            except Exception:
                pass
        except Exception:
            pass
        # HTTP fallback
        try:
            payload = json.dumps({'tool': 'session_status', 'args': {}}).encode()
            req = _urllib_req.Request(
                f"{url}/tools/invoke",
                data=payload,
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                method='POST'
            )
            with _urllib_req.urlopen(req, timeout=2) as resp:
                result = json.loads(resp.read())
                if result.get('ok'):
                    return url
        except Exception:
            continue
    
    # Last resort: try docker exec
    try:
        result = _gw_invoke_docker('session_status', {}, token)
        if result:
            return 'docker://localhost:18789'  # sentinel value indicating docker mode
    except Exception:
        pass
    return None

@app.route('/api/auth/check')
def api_auth_check():
    """Check if auth is required and validate token."""
    if not GATEWAY_TOKEN:
        return jsonify({'authRequired': True, 'valid': False, 'needsSetup': True})
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if not token:
        token = request.args.get('token', '').strip()
    if token == GATEWAY_TOKEN:
        return jsonify({'authRequired': True, 'valid': True})
    return jsonify({'authRequired': True, 'valid': False})


@app.before_request
def _check_auth():
    """Require valid gateway token for all /api/* routes when GATEWAY_TOKEN is set."""
    if request.path == '/api/auth/check':
        return  # Auth check endpoint is always accessible
    if request.path == '/api/gw/config':
        return  # Gateway setup must work before auth is configured
    if not request.path.startswith('/api/'):
        return  # HTML, static, etc. are fine
    if not GATEWAY_TOKEN:
        return jsonify({'error': 'Gateway token not configured. Please set up your gateway token first.', 'needsSetup': True}), 401
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if not token:
        token = request.args.get('token', '').strip()
    if token == GATEWAY_TOKEN:
        return
    return jsonify({'error': 'Unauthorized', 'authRequired': True}), 401


@app.route('/')
def index():
    resp = make_response(render_template_string(DASHBOARD_HTML))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp


@app.route('/api/mc-tasks')
def api_mc_tasks():
    if not MC_URL:
        return jsonify({'available': False, 'tasks': []})
    try:
        import requests as _req
        r = _req.get(f'{MC_URL}/api/tasks', timeout=3)
        data = r.json()
        data['available'] = True
        return jsonify(data)
    except Exception:
        return jsonify({'available': False, 'tasks': []})

@app.route('/api/channels')
def api_channels():
    """Return list of configured channel names (telegram, signal, whatsapp, discord, webchat, etc.)."""
    KNOWN_CHANNELS = ('telegram', 'signal', 'whatsapp', 'discord', 'webchat')
    configured = []

    def _add(name):
        n = name.lower()
        if n in KNOWN_CHANNELS and n not in configured:
            configured.append(n)

    # 1. Check gateway.yaml / gateway.yml (OpenClaw gateway config)
    yaml_candidates = [
        os.path.expanduser('~/.openclaw/gateway.yaml'),
        os.path.expanduser('~/.openclaw/gateway.yml'),
        os.path.expanduser('~/.clawdbot/gateway.yaml'),
        os.path.expanduser('~/.clawdbot/gateway.yml'),
    ]
    for yf in yaml_candidates:
        try:
            import yaml as _yaml
            with open(yf) as f:
                ydata = _yaml.safe_load(f)
            if not isinstance(ydata, dict):
                continue
            # channels: or plugins: section
            for section_key in ('channels', 'plugins'):
                section = ydata.get(section_key, {})
                if isinstance(section, dict):
                    for name, conf in section.items():
                        if isinstance(conf, dict) and conf.get('enabled', True):
                            _add(name)
                        elif isinstance(conf, bool) and conf:
                            _add(name)
                elif isinstance(section, list):
                    for name in section:
                        _add(str(name))
            if configured:
                break
        except Exception:
            continue

    # 2. Check JSON config files (clawdbot/openclaw/moltbot)
    if not configured:
        config_files = [
            os.path.expanduser('~/.clawdbot/openclaw.json'),
            os.path.expanduser('~/.clawdbot/clawdbot.json'),
            os.path.expanduser('~/.clawdbot/moltbot.json'),
        ]
        for cf in config_files:
            try:
                with open(cf) as f:
                    data = json.load(f)
                # Check plugins.entries for enabled channels
                plugins = data.get('plugins', {}).get('entries', {})
                for name, pconf in plugins.items():
                    if isinstance(pconf, dict) and pconf.get('enabled'):
                        _add(name)
                # Also check channels key
                channels = data.get('channels', {})
                if isinstance(channels, dict):
                    for name in channels:
                        _add(name)
                elif isinstance(channels, list):
                    for name in channels:
                        _add(str(name))
                if configured:
                    break
            except Exception:
                continue

    # Filter to channels that actually have data directories (proof of real usage)
    if configured:
        active_channels = []
        oc_dir = os.path.expanduser('~/.openclaw')
        cb_dir = os.path.expanduser('~/.clawdbot')
        for ch in configured:
            # Check for channel-specific directories that indicate real setup
            if any(os.path.isdir(os.path.join(d, ch)) for d in [oc_dir, cb_dir]):
                active_channels.append(ch)
        if active_channels:
            configured = active_channels

    # Fallback: show all if nothing found
    if not configured:
        configured = ['telegram', 'signal', 'whatsapp']
    return jsonify({'channels': configured})


@app.route('/api/overview')
def api_overview():
    # Try gateway API for sessions
    gw_sessions = _gw_invoke('sessions_list', {'limit': 50, 'messageLimit': 0})
    if gw_sessions and 'sessions' in gw_sessions:
        sessions = gw_sessions['sessions']
    else:
        sessions = _get_sessions()
    main = next((s for s in sessions if 'subagent' not in (s.get('key', s.get('sessionId', '')).lower())), sessions[0] if sessions else {})

    crons = _get_crons()
    enabled = len([j for j in crons if j.get('enabled')])
    disabled = len(crons) - enabled

    mem_files = _get_memory_files()
    total_size = sum(f['size'] for f in mem_files)

    # System info
    system = []
    try:
        disk = subprocess.run(['df', '-h', '/'], capture_output=True, text=True).stdout.strip().split('\n')[-1].split()
        disk_pct = int(disk[4].replace('%', '')) if len(disk) > 4 else 0
        disk_color = 'green' if disk_pct < 80 else ('yellow' if disk_pct < 90 else 'red')
        system.append(['Disk /', f'{disk[2]} / {disk[1]} ({disk[4]})', disk_color])
    except Exception:
        system.append(['Disk /', '—', ''])

    try:
        mem = subprocess.run(['free', '-h'], capture_output=True, text=True).stdout.strip().split('\n')[1].split()
        system.append(['RAM', f'{mem[2]} / {mem[1]}', ''])
    except Exception:
        system.append(['RAM', '—', ''])

    try:
        load = open('/proc/loadavg').read().split()[:3]
        system.append(['Load', ' '.join(load), ''])
    except Exception:
        system.append(['Load', '—', ''])

    try:
        uptime = subprocess.run(['uptime', '-p'], capture_output=True, text=True).stdout.strip()
        system.append(['Uptime', uptime.replace('up ', ''), ''])
    except Exception:
        system.append(['Uptime', '—', ''])

    gw = subprocess.run(['pgrep', '-f', 'moltbot'], capture_output=True, text=True)
    system.append(['Gateway', 'Running' if gw.returncode == 0 else 'Stopped',
                    'green' if gw.returncode == 0 else 'red'])

    # Infrastructure details for Flow tab
    infra = {
        'userName': USER_NAME,
        'network': get_local_ip(),
    }
    try:
        import platform
        uname = platform.uname()
        infra['machine'] = uname.node
        infra['runtime'] = f'Node.js · {uname.system} {uname.release.split("-")[0]}'
    except Exception:
        infra['machine'] = 'Host'
        infra['runtime'] = 'Runtime'

    try:
        disk_info = subprocess.run(['df', '-h', '/'], capture_output=True, text=True).stdout.strip().split('\n')[-1].split()
        infra['storage'] = f'{disk_info[1]} root'
    except Exception:
        infra['storage'] = 'Disk'

    model_name = main.get('model') or 'unknown'
    return jsonify({
        'model': model_name,
        'provider': _infer_provider_from_model(model_name),
        'sessionCount': len(sessions),
        'mainSessionUpdated': main.get('updatedAt'),
        'mainTokens': main.get('totalTokens', 0),
        'contextWindow': main.get('contextTokens', 200000),
        'cronCount': len(crons),
        'cronEnabled': enabled,
        'cronDisabled': disabled,
        'memoryCount': len(mem_files),
        'memorySize': total_size,
        'system': system,
        'infra': infra,
    })


@app.route('/api/sessions')
def api_sessions():
    gw_data = _gw_invoke('sessions_list', {'limit': 50, 'messageLimit': 0})
    if gw_data and 'sessions' in gw_data:
        return jsonify({'sessions': gw_data['sessions']})
    return jsonify({'sessions': _get_sessions()})


@app.route('/api/crons')
def api_crons():
    # Try gateway API first
    gw_data = _gw_invoke('cron', {'action': 'list', 'includeDisabled': True})
    if gw_data and 'jobs' in gw_data:
        return jsonify({'jobs': gw_data['jobs']})
    return jsonify({'jobs': _get_crons()})


@app.route('/api/cron/fix', methods=['POST'])
def api_cron_fix():
    data = request.get_json(silent=True) or {}
    job_id = data.get('jobId', '')
    if not job_id:
        return jsonify({'error': 'Missing jobId'}), 400
    # Find the job name for context
    job_name = job_id
    for j in _get_crons():
        if j.get('id') == job_id:
            job_name = j.get('name', job_id)
            break
    # TODO: integrate with AI agent messaging system
    return jsonify({'ok': True, 'message': f'Fix request submitted for "{job_name}"'})


def _find_log_file(ds):
    """Find log file for a given date string, trying multiple prefixes and dirs."""
    dirs = [LOG_DIR, '/tmp/openclaw', '/tmp/moltbot']
    prefixes = ['openclaw-', 'moltbot-']
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for p in prefixes:
            f = os.path.join(d, f'{p}{ds}.log')
            if os.path.exists(f):
                return f
    return None


def _infer_provider_from_model(model_name):
    """Best-effort provider inference for display only."""
    m = (model_name or '').lower()
    if not m:
        return 'unknown'
    if 'claude' in m:
        return 'anthropic'
    if 'grok' in m or 'x-ai' in m or m.startswith('xai'):
        return 'xai'
    if 'gpt' in m or 'o1' in m or 'o3' in m or 'o4' in m:
        return 'openai'
    if 'gemini' in m:
        return 'google'
    if 'llama' in m or 'mistral' in m or 'qwen' in m or 'deepseek' in m:
        return 'local/other'
    return 'unknown'

@app.route('/api/timeline')
def api_timeline():
    """Return available dates with activity counts for time travel."""
    now = datetime.now()
    days = []
    for i in range(30, -1, -1):
        d = now - timedelta(days=i)
        ds = d.strftime('%Y-%m-%d')
        log_file = _find_log_file(ds)
        count = 0
        hours = {}
        if log_file:
            try:
                with open(log_file) as f:
                    for line in f:
                        count += 1
                        try:
                            obj = json.loads(line.strip())
                            ts = obj.get('time') or ''
                            if 'T' in ts:
                                h = int(ts.split('T')[1][:2])
                                hours[h] = hours.get(h, 0) + 1
                        except Exception:
                            pass
            except Exception:
                pass
        # Also check memory files for that date
        mem_file = os.path.join(MEMORY_DIR, f'{ds}.md') if MEMORY_DIR else None
        has_memory = mem_file and os.path.exists(mem_file)
        if count > 0 or has_memory:
            days.append({
                'date': ds,
                'label': d.strftime('%a %b %d'),
                'events': count,
                'hasMemory': has_memory,
                'hours': hours,
            })
    return jsonify({'days': days, 'today': now.strftime('%Y-%m-%d')})


@app.route('/api/logs')
def api_logs():
    lines_count = int(request.args.get('lines', 100))
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    hour_start = request.args.get('hour_start', None)
    hour_end = request.args.get('hour_end', None)
    log_file = _find_log_file(date_str)
    lines = []
    if log_file:
        if hour_start is not None or hour_end is not None:
            # Time-filtered reading
            h_start = int(hour_start) if hour_start is not None else 0
            h_end = int(hour_end) if hour_end is not None else 23
            try:
                with open(log_file) as f:
                    for line in f:
                        try:
                            obj = json.loads(line.strip())
                            ts = obj.get('time') or ''
                            if 'T' in ts:
                                hour = int(ts.split('T')[1][:2])
                                if h_start <= hour <= h_end:
                                    lines.append(line.strip())
                            else:
                                lines.append(line.strip())
                        except (json.JSONDecodeError, ValueError):
                            lines.append(line.strip())
                lines = lines[-lines_count:]
            except Exception:
                pass
        else:
            result = subprocess.run(['tail', f'-{lines_count}', log_file], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
    return jsonify({'lines': lines, 'date': date_str})


@app.route('/api/logs-stream')
def api_logs_stream():
    """SSE endpoint - streams new log lines in real-time."""
    if not _acquire_stream_slot('log'):
        return jsonify({'error': 'Too many active log streams'}), 429

    today = datetime.now().strftime('%Y-%m-%d')
    log_file = _find_log_file(today)

    def generate():
        started_at = time.time()
        if not log_file:
            yield 'data: {"line":"No log file found"}\n\n'
            _release_stream_slot('log')
            return
        proc = subprocess.Popen(
            ['tail', '-f', '-n', '0', log_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        try:
            while True:
                if time.time() - started_at > SSE_MAX_SECONDS:
                    yield 'event: done\ndata: {"reason":"max_duration_reached"}\n\n'
                    break
                ready, _, _ = select.select([proc.stdout], [], [], 1.0)
                if not ready:
                    continue
                line = proc.stdout.readline()
                if line:
                    yield f'data: {json.dumps({"line": line.rstrip()})}\n\n'
        except GeneratorExit:
            pass
        finally:
            try:
                proc.kill()
            except Exception:
                pass
            _release_stream_slot('log')

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/memory-files')
def api_memory_files():
    return jsonify(_get_memory_files())


@app.route('/api/file')
def api_view_file():
    """Return the contents of a memory file."""
    path = request.args.get('path', '')
    full = os.path.normpath(os.path.join(WORKSPACE, path))
    if not full.startswith(os.path.normpath(WORKSPACE)):
        return jsonify({'error': 'Access denied'}), 403
    if not os.path.exists(full):
        return jsonify({'error': 'File not found'}), 404
    try:
        with open(full, 'r') as f:
            content = f.read(100_000)
        return jsonify({'path': path, 'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── OTLP Receiver Endpoints ─────────────────────────────────────────────

@app.route('/v1/metrics', methods=['POST'])
def otlp_metrics():
    """OTLP/HTTP receiver for metrics (protobuf)."""
    if not _HAS_OTEL_PROTO:
        return jsonify({
            'error': 'opentelemetry-proto not installed',
            'message': 'Install OTLP support: pip install clawmetry[otel]  '
                       'or: pip install opentelemetry-proto protobuf',
        }), 501

    try:
        pb_data = request.get_data()
        _process_otlp_metrics(pb_data)
        return '{}', 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/v1/traces', methods=['POST'])
def otlp_traces():
    """OTLP/HTTP receiver for traces (protobuf)."""
    if not _HAS_OTEL_PROTO:
        return jsonify({
            'error': 'opentelemetry-proto not installed',
            'message': 'Install OTLP support: pip install clawmetry[otel]  '
                       'or: pip install opentelemetry-proto protobuf',
        }), 501

    try:
        pb_data = request.get_data()
        _process_otlp_traces(pb_data)
        return '{}', 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/otel-status')
def api_otel_status():
    """Return OTLP receiver status."""
    counts = {}
    with _metrics_lock:
        for k in metrics_store:
            counts[k] = len(metrics_store[k])
    return jsonify({
        'available': _HAS_OTEL_PROTO,
        'hasData': _has_otel_data(),
        'lastReceived': _otel_last_received,
        'counts': counts,
    })


# ── Enhanced Cost Tracking Utilities ─────────────────────────────────────

def _get_model_pricing():
    """Model-specific pricing per 1M tokens (input, output)."""
    return {
        'claude-opus': (15.0, 75.0),      # Claude 3 Opus
        'claude-sonnet': (3.0, 15.0),     # Claude 3 Sonnet  
        'claude-haiku': (0.25, 1.25),     # Claude 3 Haiku
        'gpt-4': (10.0, 30.0),            # GPT-4 Turbo
        'gpt-3.5': (1.0, 2.0),            # GPT-3.5 Turbo
        'default': (15.0, 45.0),          # Conservative estimate
    }

def _calculate_enhanced_costs(daily_tokens, today_str, week_start, month_start):
    """Enhanced cost calculation with model-specific pricing."""
    pricing = _get_model_pricing()
    
    # For log parsing fallback, assume 60/40 input/output ratio
    input_ratio, output_ratio = 0.6, 0.4
    
    def calc_cost(tokens, model_key='default'):
        if tokens == 0:
            return 0.0
        in_price, out_price = pricing.get(model_key, pricing['default'])
        input_cost = (tokens * input_ratio) * (in_price / 1_000_000)
        output_cost = (tokens * output_ratio) * (out_price / 1_000_000)
        return input_cost + output_cost
    
    today_tok = daily_tokens.get(today_str, 0)
    week_tok = sum(v for k, v in daily_tokens.items() if k >= week_start)
    month_tok = sum(v for k, v in daily_tokens.items() if k >= month_start)
    
    return (
        round(calc_cost(today_tok), 4),
        round(calc_cost(week_tok), 4), 
        round(calc_cost(month_tok), 4)
    )

def _analyze_usage_trends(daily_tokens):
    """Analyze usage trends for predictions."""
    if len(daily_tokens) < 3:
        return {'prediction': None, 'trend': 'insufficient_data'}
    
    # Get last 7 days of data
    recent_days = sorted(daily_tokens.items())[-7:]
    if len(recent_days) < 3:
        return {'prediction': None, 'trend': 'insufficient_data'}
    
    tokens_series = [v for k, v in recent_days]
    
    # Simple trend analysis
    if len(tokens_series) >= 3:
        recent_avg = sum(tokens_series[-3:]) / 3
        older_avg = sum(tokens_series[:-3]) / max(1, len(tokens_series) - 3) if len(tokens_series) > 3 else recent_avg
        
        if recent_avg > older_avg * 1.2:
            trend = 'increasing'
        elif recent_avg < older_avg * 0.8:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Monthly prediction based on recent average
        daily_avg = sum(tokens_series[-7:]) / len(tokens_series[-7:])
        monthly_prediction = daily_avg * 30
        
        return {
            'trend': trend,
            'dailyAvg': int(daily_avg),
            'monthlyPrediction': int(monthly_prediction),
        }
    
    return {'prediction': None, 'trend': 'stable'}

def _generate_cost_warnings(today_cost, week_cost, month_cost, trend_data):
    """Generate cost warnings based on thresholds."""
    warnings = []
    
    # Daily cost warnings
    if today_cost > 10.0:
        warnings.append({
            'type': 'high_daily_cost',
            'level': 'error',
            'message': f'High daily cost: ${today_cost:.2f} (threshold: $10)',
        })
    elif today_cost > 5.0:
        warnings.append({
            'type': 'elevated_daily_cost', 
            'level': 'warning',
            'message': f'Elevated daily cost: ${today_cost:.2f}',
        })
    
    # Weekly cost warnings  
    if week_cost > 50.0:
        warnings.append({
            'type': 'high_weekly_cost',
            'level': 'error', 
            'message': f'High weekly cost: ${week_cost:.2f} (threshold: $50)',
        })
    elif week_cost > 25.0:
        warnings.append({
            'type': 'elevated_weekly_cost',
            'level': 'warning',
            'message': f'Elevated weekly cost: ${week_cost:.2f}',
        })
    
    # Monthly cost warnings
    if month_cost > 200.0:
        warnings.append({
            'type': 'high_monthly_cost',
            'level': 'error',
            'message': f'High monthly cost: ${month_cost:.2f} (threshold: $200)', 
        })
    elif month_cost > 100.0:
        warnings.append({
            'type': 'elevated_monthly_cost',
            'level': 'warning', 
            'message': f'Elevated monthly cost: ${month_cost:.2f}',
        })
    
    # Trend-based warnings
    if trend_data.get('trend') == 'increasing' and trend_data.get('monthlyPrediction', 0) > 300:
        warnings.append({
            'type': 'trend_warning',
            'level': 'warning',
            'message': f'Usage trending up - projected monthly cost: ${(trend_data["monthlyPrediction"] * 0.00003):.2f}',
        })
    
    return warnings

# ── Usage cache ─────────────────────────────────────────────────────────
_usage_cache = {'data': None, 'ts': 0}
_USAGE_CACHE_TTL = 60  # seconds
_sessions_cache = {'data': None, 'ts': 0}
_SESSIONS_CACHE_TTL = 10  # seconds

# ── New Feature APIs ────────────────────────────────────────────────────

@app.route('/api/usage')
def api_usage():
    """Token/cost tracking from transcript files - Enhanced OTLP workaround."""
    import time as _time
    now = _time.time()
    if _usage_cache['data'] is not None and (now - _usage_cache['ts']) < _USAGE_CACHE_TTL:
        return jsonify(_usage_cache['data'])

    # Prefer OTLP data when available
    if _has_otel_data():
        result = _get_otel_usage_data()
        _usage_cache['data'] = result
        _usage_cache['ts'] = now
        return jsonify(result)

    # NEW: Parse transcript JSONL files for real usage data
    sessions_dir = SESSIONS_DIR or os.path.expanduser('~/.moltbot/agents/main/sessions')
    daily_tokens = {}
    daily_cost = {}
    model_usage = {}
    session_costs = {}
    
    if os.path.isdir(sessions_dir):
        for fname in os.listdir(sessions_dir):
            if not fname.endswith('.jsonl'):
                continue
            fpath = os.path.join(sessions_dir, fname)
            session_cost = 0
            
            try:
                with open(fpath, 'r') as f:
                    for line in f:
                        try:
                            obj = json.loads(line.strip())
                            
                            # Only process message entries with usage data
                            if obj.get('type') != 'message':
                                continue
                                
                            message = obj.get('message', {})
                            usage = message.get('usage')
                            if not usage or not isinstance(usage, dict):
                                continue
                                
                            # Extract the exact usage format from the brief
                            tokens_data = {
                                'input': usage.get('input', 0),
                                'output': usage.get('output', 0),
                                'cacheRead': usage.get('cacheRead', 0),
                                'cacheWrite': usage.get('cacheWrite', 0),
                                'totalTokens': usage.get('totalTokens', 0),
                                'cost': usage.get('cost', {})
                            }
                            
                            cost_data = tokens_data['cost']
                            if isinstance(cost_data, dict) and 'total' in cost_data:
                                total_cost = float(cost_data['total'])
                            else:
                                total_cost = 0.0
                            
                            # Extract model name
                            model = message.get('model', 'unknown') or 'unknown'
                            
                            # Get timestamp and convert to date
                            ts = obj.get('timestamp')
                            if ts:
                                # Handle ISO timestamp strings
                                if isinstance(ts, str):
                                    try:
                                        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                                    except:
                                        continue
                                else:
                                    # Handle numeric timestamps
                                    dt = datetime.fromtimestamp(ts / 1000 if ts > 1e12 else ts)
                                
                                day = dt.strftime('%Y-%m-%d')
                                
                                # Aggregate daily tokens and costs
                                daily_tokens[day] = daily_tokens.get(day, 0) + tokens_data['totalTokens']
                                daily_cost[day] = daily_cost.get(day, 0) + total_cost
                                
                                # Track model usage
                                model_usage[model] = model_usage.get(model, 0) + tokens_data['totalTokens']
                                
                                # Track session costs
                                session_cost += total_cost
                                
                        except (json.JSONDecodeError, ValueError, KeyError):
                            continue
                            
                # Store session cost
                session_costs[fname.replace('.jsonl', '')] = session_cost
                        
            except Exception:
                continue

    # Build response data
    today = datetime.now()
    days = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        ds = d.strftime('%Y-%m-%d')
        days.append({
            'date': ds, 
            'tokens': daily_tokens.get(ds, 0),
            'cost': daily_cost.get(ds, 0)
        })

    # Calculate aggregations
    today_str = today.strftime('%Y-%m-%d')
    week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
    month_start = today.strftime('%Y-%m-01')
    
    today_tok = daily_tokens.get(today_str, 0)
    week_tok = sum(v for k, v in daily_tokens.items() if k >= week_start)
    month_tok = sum(v for k, v in daily_tokens.items() if k >= month_start)
    
    today_cost = daily_cost.get(today_str, 0)
    week_cost = sum(v for k, v in daily_cost.items() if k >= week_start)
    month_cost = sum(v for k, v in daily_cost.items() if k >= month_start)
    
    # Trend analysis & predictions
    trend_data = _analyze_usage_trends(daily_tokens)
    
    # Cost warnings
    warnings = _generate_cost_warnings(today_cost, week_cost, month_cost, trend_data)
    
    # Model breakdown for display
    model_breakdown = [
        {'model': k, 'tokens': v}
        for k, v in sorted(model_usage.items(), key=lambda x: -x[1])
    ]
    
    result = {
        'source': 'transcripts',
        'days': days,
        'today': today_tok,
        'week': week_tok, 
        'month': month_tok,
        'todayCost': round(today_cost, 4),
        'weekCost': round(week_cost, 4),
        'monthCost': round(month_cost, 4),
        'modelBreakdown': model_breakdown,
        'sessionCosts': session_costs,
        'trend': trend_data,
        'warnings': warnings,
    }
    import time as _time
    _usage_cache['data'] = result
    _usage_cache['ts'] = _time.time()
    return jsonify(result)


@app.route('/api/usage/export')
def api_usage_export():
    """Export usage data as CSV."""
    try:
        # Get usage data
        if _has_otel_data():
            data = _get_otel_usage_data()
        else:
            # Call the same logic as /api/usage but get full data
            sessions_dir = SESSIONS_DIR or os.path.expanduser('~/.clawdbot/agents/main/sessions')
            daily_tokens = {}
            
            if os.path.isdir(sessions_dir):
                for fname in os.listdir(sessions_dir):
                    if not fname.endswith('.jsonl'):
                        continue
                    fpath = os.path.join(sessions_dir, fname)
                    try:
                        fmtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                        with open(fpath, 'r') as f:
                            for line in f:
                                try:
                                    obj = json.loads(line.strip())
                                    tokens = 0
                                    usage = obj.get('usage') or obj.get('tokens_used') or {}
                                    if isinstance(usage, dict):
                                        tokens = (usage.get('total_tokens') or usage.get('totalTokens')
                                                  or (usage.get('input_tokens', 0) + usage.get('output_tokens', 0))
                                                  or 0)
                                    elif isinstance(usage, (int, float)):
                                        tokens = int(usage)
                                    if not tokens:
                                        content = obj.get('content', '')
                                        if isinstance(content, str) and len(content) > 0:
                                            tokens = max(1, len(content) // 4)
                                        elif isinstance(content, list):
                                            total_len = sum(len(str(c.get('text', ''))) for c in content if isinstance(c, dict))
                                            tokens = max(1, total_len // 4) if total_len else 0
                                    ts = obj.get('timestamp') or obj.get('time') or obj.get('created_at')
                                    if ts:
                                        if isinstance(ts, (int, float)):
                                            dt = datetime.fromtimestamp(ts / 1000 if ts > 1e12 else ts)
                                        else:
                                            try:
                                                dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                                            except Exception:
                                                dt = fmtime
                                    else:
                                        dt = fmtime
                                    day = dt.strftime('%Y-%m-%d')
                                    if tokens > 0:
                                        daily_tokens[day] = daily_tokens.get(day, 0) + tokens
                                except (json.JSONDecodeError, ValueError):
                                    pass
                    except Exception:
                        pass
            
            today = datetime.now()
            today_str = today.strftime('%Y-%m-%d')
            week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            month_start = today.strftime('%Y-%m-01')
            
            # Build data structure similar to OTLP
            days = []
            for i in range(30, -1, -1):  # Last 30 days for export
                d = today - timedelta(days=i)
                ds = d.strftime('%Y-%m-%d')
                tokens = daily_tokens.get(ds, 0)
                cost = round(tokens * (30.0 / 1_000_000), 4)  # Default pricing
                days.append({'date': ds, 'tokens': tokens, 'cost': cost})
                
            data = {'days': days}
        
        # Generate CSV content
        csv_lines = ['Date,Tokens,Cost']
        for day in data['days']:
            csv_lines.append(f"{day['date']},{day['tokens']},{day.get('cost', 0):.4f}")
        
        csv_content = '\n'.join(csv_lines)
        
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=openclaw-usage-{datetime.now().strftime("%Y%m%d")}.csv'
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcripts')
def api_transcripts():
    """List available session transcript .jsonl files."""
    sessions_dir = SESSIONS_DIR or os.path.expanduser('~/.clawdbot/agents/main/sessions')
    transcripts = []
    if os.path.isdir(sessions_dir):
        for fname in sorted(os.listdir(sessions_dir), key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)), reverse=True):
            if not fname.endswith('.jsonl') or 'deleted' in fname:
                continue
            fpath = os.path.join(sessions_dir, fname)
            try:
                msg_count = 0
                with open(fpath) as f:
                    for _ in f:
                        msg_count += 1
                transcripts.append({
                    'id': fname.replace('.jsonl', ''),
                    'name': fname.replace('.jsonl', '')[:40],
                    'messages': msg_count,
                    'size': os.path.getsize(fpath),
                    'modified': int(os.path.getmtime(fpath) * 1000),
                })
            except Exception:
                pass
    return jsonify({'transcripts': transcripts[:50]})


@app.route('/api/transcript/<session_id>')
def api_transcript(session_id):
    """Parse and return a session transcript for the chat viewer."""
    sessions_dir = SESSIONS_DIR or os.path.expanduser('~/.clawdbot/agents/main/sessions')
    fpath = os.path.join(sessions_dir, session_id + '.jsonl')
    # Sanitize path
    fpath = os.path.normpath(fpath)
    if not fpath.startswith(os.path.normpath(sessions_dir)):
        return jsonify({'error': 'Access denied'}), 403
    if not os.path.exists(fpath):
        return jsonify({'error': 'Transcript not found'}), 404

    messages = []
    model = None
    total_tokens = 0
    first_ts = None
    last_ts = None
    try:
        with open(fpath) as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    role = obj.get('role', obj.get('type', 'unknown'))
                    content = obj.get('content', '')
                    if isinstance(content, list):
                        parts = []
                        for part in content:
                            if isinstance(part, dict):
                                parts.append(part.get('text', str(part)))
                            else:
                                parts.append(str(part))
                        content = '\n'.join(parts)
                    elif not isinstance(content, str):
                        content = str(content) if content else ''
                    # Tool use handling
                    if obj.get('tool_calls') or obj.get('tool_use'):
                        tools = obj.get('tool_calls') or obj.get('tool_use') or []
                        if isinstance(tools, list):
                            for tc in tools:
                                tname = tc.get('name', tc.get('function', {}).get('name', 'tool'))
                                messages.append({
                                    'role': 'tool',
                                    'content': f"[Tool Call: {tname}]\n{json.dumps(tc.get('input', tc.get('arguments', {})), indent=2)[:500]}",
                                    'timestamp': obj.get('timestamp') or obj.get('time'),
                                })
                    if role == 'tool_result':
                        role = 'tool'
                    ts = obj.get('timestamp') or obj.get('time') or obj.get('created_at')
                    if ts:
                        if isinstance(ts, (int, float)):
                            ts_ms = int(ts * 1000) if ts < 1e12 else int(ts)
                        else:
                            try:
                                ts_ms = int(datetime.fromisoformat(str(ts).replace('Z', '+00:00')).timestamp() * 1000)
                            except Exception:
                                ts_ms = None
                        if ts_ms:
                            if not first_ts or ts_ms < first_ts:
                                first_ts = ts_ms
                            if not last_ts or ts_ms > last_ts:
                                last_ts = ts_ms
                    else:
                        ts_ms = None
                    if not model:
                        model = obj.get('model')
                    usage = obj.get('usage', {})
                    if isinstance(usage, dict):
                        total_tokens += usage.get('total_tokens', 0) or (
                            usage.get('input_tokens', 0) + usage.get('output_tokens', 0))
                    if content or role in ('user', 'assistant', 'system'):
                        messages.append({
                            'role': role, 'content': content, 'timestamp': ts_ms,
                        })
                except (json.JSONDecodeError, ValueError):
                    pass
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    duration = None
    if first_ts and last_ts and last_ts > first_ts:
        dur_sec = (last_ts - first_ts) / 1000
        if dur_sec < 60:
            duration = f'{dur_sec:.0f}s'
        elif dur_sec < 3600:
            duration = f'{dur_sec / 60:.0f}m'
        else:
            duration = f'{dur_sec / 3600:.1f}h'

    return jsonify({
        'name': session_id[:40],
        'messageCount': len(messages),
        'model': model,
        'totalTokens': total_tokens,
        'duration': duration,
        'messages': messages[:500],  # Cap at 500 messages
    })


@app.route('/api/transcript-events/<session_id>')
def api_transcript_events(session_id):
    """Parse a session transcript JSONL into structured events for the detail modal."""
    sessions_dir = SESSIONS_DIR or os.path.expanduser('~/.clawdbot/agents/main/sessions')
    fpath = os.path.join(sessions_dir, session_id + '.jsonl')
    fpath = os.path.normpath(fpath)
    if not fpath.startswith(os.path.normpath(sessions_dir)):
        return jsonify({'error': 'Access denied'}), 403
    if not os.path.exists(fpath):
        return jsonify({'error': 'Transcript not found'}), 404

    events = []
    msg_count = 0
    try:
        with open(fpath) as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                except (json.JSONDecodeError, ValueError):
                    continue

                ts = obj.get('timestamp') or obj.get('time') or obj.get('created_at')
                ts_val = None
                if ts:
                    if isinstance(ts, (int, float)):
                        ts_val = int(ts * 1000) if ts < 1e12 else int(ts)
                    else:
                        try:
                            ts_val = int(datetime.fromisoformat(str(ts).replace('Z', '+00:00')).timestamp() * 1000)
                        except Exception:
                            pass

                obj_type = obj.get('type', '')
                if obj_type == 'message':
                    msg = obj.get('message', {})
                    role = msg.get('role', '')
                    content = msg.get('content', '')
                    msg_count += 1

                    if isinstance(content, list):
                        for block in content:
                            if not isinstance(block, dict):
                                continue
                            btype = block.get('type', '')
                            if btype == 'thinking':
                                events.append({'type': 'thinking', 'text': block.get('thinking', '')[:2000], 'timestamp': ts_val})
                            elif btype == 'text':
                                text = block.get('text', '')
                                if role == 'user':
                                    events.append({'type': 'user', 'text': text[:3000], 'timestamp': ts_val})
                                elif role == 'assistant':
                                    events.append({'type': 'agent', 'text': text[:3000], 'timestamp': ts_val})
                            elif btype in ('toolCall', 'tool_use'):
                                name = block.get('name', '?')
                                args = block.get('arguments') or block.get('input') or {}
                                args_str = json.dumps(args, indent=2)[:1000] if isinstance(args, dict) else str(args)[:1000]
                                if name == 'exec':
                                    cmd = args.get('command', '') if isinstance(args, dict) else ''
                                    events.append({'type': 'exec', 'command': cmd, 'toolName': name, 'args': args_str, 'timestamp': ts_val})
                                elif name in ('Read', 'read'):
                                    fp = (args.get('file_path') or args.get('path') or '') if isinstance(args, dict) else ''
                                    events.append({'type': 'read', 'file': fp, 'toolName': name, 'args': args_str, 'timestamp': ts_val})
                                else:
                                    events.append({'type': 'tool', 'toolName': name, 'args': args_str, 'timestamp': ts_val})
                    elif isinstance(content, str) and content:
                        if role == 'user':
                            events.append({'type': 'user', 'text': content[:3000], 'timestamp': ts_val})
                        elif role == 'assistant':
                            events.append({'type': 'agent', 'text': content[:3000], 'timestamp': ts_val})
                        elif role == 'toolResult':
                            events.append({'type': 'result', 'text': content[:2000], 'timestamp': ts_val})

                    if role == 'toolResult' and isinstance(content, list):
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                text_parts.append(block.get('text', ''))
                        if text_parts:
                            events.append({'type': 'result', 'text': '\n'.join(text_parts)[:2000], 'timestamp': ts_val})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'events': events[-500:], 'messageCount': msg_count, 'totalEvents': len(events)})


@app.route('/api/subagents')
def api_subagents():
    """Get sub-agent sessions from sessions.json index (batch read, no N+1)."""
    sessions_dir = SESSIONS_DIR or os.path.expanduser('~/.openclaw/agents/main/sessions')
    index_path = os.path.join(sessions_dir, 'sessions.json')
    subagents = []
    now = time.time() * 1000

    # Read the authoritative session index
    try:
        with open(index_path, 'r') as f:
            index = json.load(f)
    except Exception:
        return jsonify({'subagents': [], 'counts': {'active': 0, 'idle': 0, 'stale': 0, 'total': 0}, 'totalActive': 0})

    # Collect sub-agent entries and their session IDs for batch transcript reading
    sa_entries = []
    for key, meta in index.items():
        if ':subagent:' not in key:
            continue
        sa_entries.append((key, meta))

    # Batch: read first+last lines of each transcript for task detection
    tasks = {}
    labels = {}
    for key, meta in sa_entries:
        sid = meta.get('sessionId', '')
        if not sid:
            continue
        fpath = os.path.join(sessions_dir, f"{sid}.jsonl")
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, 'rb') as f:
                # Read first few lines for session label
                first_lines = []
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    first_lines.append(line)

                # Read last ~8KB for recent activity
                try:
                    f.seek(0, 2)
                    fsize = f.tell()
                    tail_start = max(0, fsize - 8192)
                    f.seek(tail_start)
                    tail_data = f.read().decode('utf-8', errors='replace')
                    tail_lines = tail_data.strip().split('\n')
                    if tail_start > 0:
                        tail_lines = tail_lines[1:]  # drop partial first line
                except Exception:
                    tail_lines = []

                # Extract label from session spawn message (first user message)
                label = None
                for raw in first_lines:
                    try:
                        obj = json.loads(raw)
                        if obj.get('type') == 'message' and obj.get('message', {}).get('role') == 'user':
                            content = obj['message'].get('content', [])
                            if isinstance(content, list):
                                for block in content:
                                    if block.get('type') == 'text':
                                        text = block.get('text', '')
                                        # Extract the label from subagent context
                                        if 'Label:' in text:
                                            label = text.split('Label:')[1].split('\n')[0].strip()
                                        elif len(text) > 20:
                                            # Use first line as label
                                            label = text.split('\n')[0][:100]
                                        break
                            break
                    except Exception:
                        continue
                if label:
                    labels[key] = label

                # Extract recent tool calls and activity from tail
                recent_tools = []
                last_text = None
                for raw in reversed(tail_lines[-20:]):
                    try:
                        obj = json.loads(raw)
                        if obj.get('type') != 'message':
                            continue
                        msg = obj.get('message', {})
                        content = msg.get('content', [])
                        if not isinstance(content, list):
                            continue
                        for block in content:
                            btype = block.get('type', '')
                            if btype in ('tool_use', 'toolCall') and len(recent_tools) < 5:
                                tool_name = block.get('name', '?')
                                tool_input = block.get('input') or block.get('arguments') or {}
                                summary = _summarize_tool_input(tool_name, tool_input)
                                recent_tools.append({'name': tool_name, 'summary': summary[:120], 'ts': obj.get('timestamp', '')})
                            elif btype == 'text' and msg.get('role') == 'assistant' and not last_text:
                                t = block.get('text', '').strip()
                                if t and len(t) > 5:
                                    last_text = t[:200]
                    except Exception:
                        continue
                tasks[key] = {
                    'recentTools': list(reversed(recent_tools)),
                    'lastText': last_text,
                }
        except Exception:
            continue

    # Build response
    for key, meta in sa_entries:
        uuid = key.split(':')[-1]
        updated_at = meta.get('updatedAt', 0)
        sid = meta.get('sessionId', '')

        # Status based on recency
        age_ms = now - updated_at if updated_at else float('inf')
        if age_ms < 5 * 60 * 1000:
            status = 'active'
        elif age_ms < 30 * 60 * 1000:
            status = 'idle'
        else:
            status = 'stale'

        # Runtime (from first seen to last update)
        runtime_ms = age_ms if age_ms != float('inf') else 0
        if runtime_ms < 60000:
            runtime = f"{int(runtime_ms / 1000)}s ago"
        elif runtime_ms < 3600000:
            runtime = f"{int(runtime_ms / 60000)}m ago"
        elif runtime_ms < 86400000:
            runtime = f"{int(runtime_ms / 3600000)}h ago"
        else:
            runtime = f"{int(runtime_ms / 86400000)}d ago"

        task_info = tasks.get(key, {})
        # Prefer label from sessions.json metadata, fallback to transcript extraction
        label = meta.get('label') or labels.get(key, f'Worker {uuid[:8]}')

        subagents.append({
            'key': key,
            'uuid': uuid,
            'sessionId': sid,
            'displayName': label,
            'status': status,
            'runtime': runtime,
            'runtimeMs': runtime_ms,
            'updatedAt': updated_at,
            'recentTools': task_info.get('recentTools', []),
            'lastText': task_info.get('lastText', ''),
            'model': meta.get('model', 'unknown'),
            'channel': meta.get('channel', meta.get('lastChannel', 'agent')),
            'spawnedBy': meta.get('spawnedBy', ''),
            'abortedLastRun': meta.get('abortedLastRun', False),
            'totalTokens': meta.get('totalTokens', 0),
            'outputTokens': meta.get('outputTokens', 0),
        })

    subagents.sort(key=lambda x: x['updatedAt'] or 0, reverse=True)

    counts = {
        'active': sum(1 for s in subagents if s['status'] == 'active'),
        'idle': sum(1 for s in subagents if s['status'] == 'idle'),
        'stale': sum(1 for s in subagents if s['status'] == 'stale'),
        'total': len(subagents),
    }

    return jsonify({'subagents': subagents, 'counts': counts, 'totalActive': counts['active']})


@app.route('/api/subagent/<session_id>/activity')
def api_subagent_activity(session_id):
    """Stream recent activity from a sub-agent's transcript. Progressive: reads tail only."""
    sessions_dir = SESSIONS_DIR or os.path.expanduser('~/.openclaw/agents/main/sessions')
    fpath = os.path.join(sessions_dir, f"{session_id}.jsonl")
    if not os.path.exists(fpath):
        return jsonify({'error': 'not found', 'events': []}), 404

    # Read last ~16KB for activity timeline
    tail_size = int(request.args.get('tail', 16384))
    events = []
    try:
        with open(fpath, 'rb') as f:
            f.seek(0, 2)
            fsize = f.tell()
            start = max(0, fsize - tail_size)
            f.seek(start)
            data = f.read().decode('utf-8', errors='replace')
            lines = data.strip().split('\n')
            if start > 0:
                lines = lines[1:]

            for raw in lines:
                try:
                    obj = json.loads(raw)
                    etype = obj.get('type', '')
                    ts = obj.get('timestamp', '')

                    if etype == 'message':
                        msg = obj.get('message', {})
                        role = msg.get('role', '')
                        content = msg.get('content', [])
                        if not isinstance(content, list):
                            continue
                        for block in content:
                            btype = block.get('type', '')
                            if btype in ('tool_use', 'toolCall'):
                                inp = block.get('input') or block.get('arguments') or {}
                                events.append({
                                    'type': 'tool_call',
                                    'ts': ts,
                                    'tool': block.get('name', '?'),
                                    'input': _summarize_tool_input(block.get('name', ''), inp),
                                })
                            elif btype in ('tool_result', 'toolResult'):
                                result_text = ''
                                sub = block.get('content', '')
                                if isinstance(sub, list):
                                    for sb in sub[:1]:
                                        result_text = sb.get('text', '')[:300]
                                elif isinstance(sub, str):
                                    result_text = sub[:300]
                                events.append({
                                    'type': 'tool_result',
                                    'ts': ts,
                                    'preview': result_text,
                                    'isError': block.get('is_error', False),
                                })
                            elif btype == 'text' and role == 'assistant':
                                text = block.get('text', '').strip()
                                if text:
                                    events.append({
                                        'type': 'thinking',
                                        'ts': ts,
                                        'text': text[:500],
                                    })
                            elif btype == 'thinking':
                                text = block.get('thinking', '').strip()
                                if text:
                                    events.append({
                                        'type': 'internal_thought',
                                        'ts': ts,
                                        'text': text[:300],
                                    })
                    elif etype == 'model_change':
                        events.append({
                            'type': 'model_change',
                            'ts': ts,
                            'model': obj.get('modelId', '?'),
                        })
                except Exception:
                    continue
    except Exception as e:
        return jsonify({'error': str(e), 'events': []}), 500

    return jsonify({'events': events, 'fileSize': fsize if 'fsize' in dir() else 0})


def _summarize_tool_input(name, inp):
    """Create a human-readable one-line summary of a tool call."""
    if name == 'exec':
        return (inp.get('command') or str(inp))[:150]
    elif name in ('Read', 'read'):
        return f"📖 {inp.get('file_path') or inp.get('path') or '?'}"
    elif name in ('Write', 'write'):
        return f"✏️ {inp.get('file_path') or inp.get('path') or '?'}"
    elif name in ('Edit', 'edit'):
        return f"🔧 {inp.get('file_path') or inp.get('path') or '?'}"
    elif name == 'web_search':
        return f"🔍 {inp.get('query', '?')}"
    elif name == 'web_fetch':
        return f"🌐 {inp.get('url', '?')[:80]}"
    elif name == 'browser':
        return f"🖥️ {inp.get('action', '?')}"
    elif name == 'message':
        return f"💬 {inp.get('action', '?')} → {inp.get('message', '')[:60]}"
    elif name == 'tts':
        return f"🔊 {inp.get('text', '')[:60]}"
    else:
        return str(inp)[:120]


@app.route('/api/channel/telegram')
def api_channel_telegram():
    """Parse logs and session transcripts for Telegram message activity."""
    import re
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)

    messages = []
    today = datetime.now().strftime('%Y-%m-%d')

    # 1. Parse log files for telegram events using grep for speed
    log_dirs = ['/tmp/openclaw', '/tmp/moltbot']
    log_files = []
    for ld in log_dirs:
        if os.path.isdir(ld):
            for f in sorted(glob.glob(os.path.join(ld, '*.log')), reverse=True):
                log_files.append(f)
    log_files = log_files[:2]  # Only today + yesterday

    run_sessions = {}
    for lf in log_files:
        try:
            # Use grep to pre-filter telegram-relevant lines
            result = subprocess.run(
                ['grep', '-i', 'messageChannel=telegram\\|telegram.*deliver\\|telegram message failed', lf],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg1 = obj.get('1', '') or obj.get('0', '')
                ts = obj.get('time', '') or (obj.get('_meta', {}) or {}).get('date', '')

                if 'messageChannel=telegram' in msg1 and 'run start' in msg1:
                    sid_match = re.search(r'sessionId=([a-f0-9-]+)', msg1)
                    sid = sid_match.group(1) if sid_match else ''
                    messages.append({
                        'timestamp': ts, 'direction': 'in', 'sender': 'User',
                        'text': '', 'chatId': '', 'sessionId': sid,
                    })
                    if sid:
                        run_sessions[sid] = ts

                msg0 = obj.get('0', '')
                if 'telegram' in msg0.lower() and 'deliver' in msg0.lower():
                    chat_match = re.search(r'telegram:(-?\d+)', msg0)
                    chat_id = chat_match.group(1) if chat_match else ''
                    failed = 'failed' in msg0.lower()
                    messages.append({
                        'timestamp': ts, 'direction': 'out', 'sender': 'Clawd',
                        'text': '(delivery failed)' if failed else '(message sent)',
                        'chatId': chat_id, 'sessionId': '',
                    })

                if 'telegram message failed' in msg1:
                    messages.append({
                        'timestamp': ts, 'direction': 'out', 'sender': 'Clawd',
                        'text': msg1[:200], 'chatId': '', 'sessionId': '',
                    })
        except Exception:
            pass

    # 2. Try to enrich incoming messages with text from session transcripts
    sessions_dir = os.path.expanduser('~/.clawdbot/agents/main/sessions')
    for msg in messages:
        if msg['direction'] == 'in' and msg['sessionId'] and not msg['text']:
            sf = os.path.join(sessions_dir, msg['sessionId'] + '.jsonl')
            if os.path.exists(sf):
                try:
                    with open(sf, 'r', errors='replace') as f:
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except json.JSONDecodeError:
                                continue
                            sm = sd.get('message', {})
                            if sm.get('role') == 'user':
                                content = sm.get('content', '')
                                if isinstance(content, list):
                                    for c in content:
                                        if isinstance(c, dict) and c.get('type') == 'text':
                                            txt = c.get('text', '')
                                            # Skip system/heartbeat messages
                                            if txt and not txt.startswith('System:') and 'HEARTBEAT' not in txt:
                                                msg['text'] = txt[:300]
                                                # Extract real sender from [Telegram Name id:...] pattern
                                                tg_name = re.search(r'\[Telegram\s+(.+?)\s+id:', txt)
                                                if tg_name:
                                                    msg['sender'] = tg_name.group(1)
                                                break
                                elif isinstance(content, str) and content:
                                    if not content.startswith('System:') and 'HEARTBEAT' not in content:
                                        msg['text'] = content[:300]
                                        tg_name = re.search(r'\[Telegram\s+(.+?)\s+id:', content)
                                        if tg_name:
                                            msg['sender'] = tg_name.group(1)
                                if msg['text']:
                                    break
                except Exception:
                    pass

    # 3. Also scan telegram session files for recent messages
    try:
        with open(os.path.join(sessions_dir, 'sessions.json'), 'r') as f:
            sess_data = json.load(f)
        tg_sessions = [(sid, s) for sid, s in sess_data.items()
                       if 'telegram' in sid and 'sessionId' in s]
        tg_sessions.sort(key=lambda x: x[1].get('updatedAt', 0), reverse=True)

        seen_sids = {m['sessionId'] for m in messages if m['sessionId']}
        for sid_key, sinfo in tg_sessions[:5]:
            uuid = sinfo['sessionId']
            if uuid in seen_sids:
                continue
            sf = os.path.join(sessions_dir, uuid + '.jsonl')
            if not os.path.exists(sf):
                continue
            try:
                chat_match = re.search(r':(-?\d+)$', sid_key)
                chat_id = chat_match.group(1) if chat_match else ''
                # Read only last 64KB of session file for performance
                fsize = os.path.getsize(sf)
                with open(sf, 'r', errors='replace') as f:
                    if fsize > 65536:
                        f.seek(fsize - 65536)
                        f.readline()  # skip partial line
                    for sline in f:
                        sline = sline.strip()
                        if not sline:
                            continue
                        try:
                            sd = json.loads(sline)
                        except json.JSONDecodeError:
                            continue
                        sm = sd.get('message', {})
                        ts = sd.get('timestamp', '')
                        role = sm.get('role', '')
                        if role not in ('user', 'assistant'):
                            continue
                        content = sm.get('content', '')
                        txt = ''
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and c.get('type') == 'text':
                                    txt = c.get('text', '')
                                    break
                        elif isinstance(content, str):
                            txt = content
                        if not txt or txt.startswith('System:') or 'HEARTBEAT' in txt:
                            continue
                        direction = 'in' if role == 'user' else 'out'
                        sender = 'User' if role == 'user' else 'Clawd'
                        if direction == 'in':
                            tg_name = re.search(r'\[Telegram\s+(.+?)\s+id:', txt)
                            if tg_name:
                                sender = tg_name.group(1)
                        messages.append({
                            'timestamp': ts,
                            'direction': direction,
                            'sender': sender,
                            'text': txt[:300],
                            'chatId': chat_id,
                            'sessionId': uuid,
                        })
            except Exception:
                pass
    except Exception:
        pass

    # Deduplicate by timestamp+direction, sort newest first
    seen = set()
    unique = []
    for m in messages:
        key = (m['timestamp'], m['direction'], m['text'][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x['timestamp'], reverse=True)

    # Stats
    today_in = sum(1 for m in unique if m['direction'] == 'in' and today in m.get('timestamp', ''))
    today_out = sum(1 for m in unique if m['direction'] == 'out' and today in m.get('timestamp', ''))

    total = len(unique)
    page = unique[offset:offset + limit]
    return jsonify({'messages': page, 'total': total, 'todayIn': today_in, 'todayOut': today_out})


_api_tool_cache = {}
_api_tool_cache_time = {}

@app.route('/api/component/tool/<name>')
def api_component_tool(name):
    """Parse session transcripts for tool-specific events. Cached for 15s."""
    import time as _time
    now = _time.time()
    if name in _api_tool_cache and (now - _api_tool_cache_time.get(name, 0)) < 15:
        return jsonify(_api_tool_cache[name])
    sessions_dir = SESSIONS_DIR or os.path.expanduser('~/.openclaw/agents/main/sessions')
    if not os.path.isdir(sessions_dir):
        for p in [
            os.path.expanduser('~/.clawdbot/agents/main/sessions'),
            os.path.expanduser('~/.moltbot/agents/main/sessions'),
            os.path.expanduser('~/.openclaw/agents/main/sessions'),
        ]:
            if os.path.isdir(p):
                sessions_dir = p
                break
    if not os.path.isdir(sessions_dir):
        sessions_dir = os.path.expanduser('~/.clawdbot/agents/main/sessions')

    today = datetime.now().strftime('%Y-%m-%d')

    # Map tool key to tool names in transcripts
    TOOL_MAP = {
        'session': ['sessions_spawn', 'sessions_send', 'sessions_list', 'sessions_poll'],
        'exec': ['exec', 'process'],
        'browser': ['browser', 'web_fetch'],
        'search': ['web_search'],
        'cron': ['cron'],
        'tts': ['tts'],
        'memory': ['Read', 'read', 'Write', 'write', 'Edit', 'edit'],
    }

    tool_names = TOOL_MAP.get(name, [name])
    events = []
    today_calls = 0
    today_errors = 0

    if os.path.isdir(sessions_dir):
        for fname in os.listdir(sessions_dir):
            if not fname.endswith('.jsonl'):
                continue
            fpath = os.path.join(sessions_dir, fname)
            try:
                mtime = os.path.getmtime(fpath)
                if datetime.fromtimestamp(mtime).strftime('%Y-%m-%d') != today:
                    continue

                with open(fpath, 'r') as f:
                    for line in f:
                        try:
                            obj = json.loads(line.strip())
                        except json.JSONDecodeError:
                            continue

                        if obj.get('type') != 'message':
                            continue
                        msg = obj.get('message', {})

                        # Tool calls (assistant side)
                        if msg.get('role') == 'assistant':
                            for c in (msg.get('content') or []):
                                if isinstance(c, dict) and c.get('type') == 'toolCall' and c.get('name') in tool_names:
                                    ts = obj.get('timestamp', '')
                                    if not ts.startswith(today):
                                        continue
                                    tn = c.get('name', '')
                                    args = c.get('arguments', {})
                                    today_calls += 1

                                    evt = {'timestamp': ts, 'status': 'ok', 'tool': tn}

                                    if name == 'exec':
                                        evt['detail'] = (args.get('command') or str(args))[:200]
                                        evt['action'] = 'exec'
                                    elif name == 'browser':
                                        evt['action'] = args.get('action', 'unknown')
                                        evt['detail'] = args.get('targetUrl') or args.get('url') or args.get('selector') or evt['action']
                                    elif name == 'search':
                                        evt['detail'] = args.get('query', '?')
                                        evt['action'] = 'search'
                                    elif name == 'tts':
                                        evt['detail'] = (args.get('text') or '')[:100]
                                        evt['action'] = 'tts'
                                        evt['voice'] = args.get('voice', '')
                                    elif name == 'memory':
                                        path = args.get('file_path') or args.get('path') or '?'
                                        evt['detail'] = path
                                        evt['action'] = 'write' if tn in ('Write', 'write', 'Edit', 'edit') else 'read'
                                    elif name == 'session':
                                        evt['detail'] = args.get('sessionId') or args.get('name') or tn
                                        evt['action'] = tn
                                        evt['session_status'] = 'running'
                                    elif name == 'cron':
                                        evt['detail'] = args.get('expr') or args.get('action') or str(args)[:80]
                                        evt['action'] = 'cron'
                                    else:
                                        evt['detail'] = str(args)[:120]
                                        evt['action'] = tn

                                    events.append(evt)

                        # Tool results
                        elif msg.get('role') == 'toolResult' and msg.get('toolName') in tool_names:
                            ts = obj.get('timestamp', '')
                            if not ts.startswith(today):
                                continue
                            details = msg.get('details', {})
                            is_error = msg.get('isError', False) or (isinstance(details, dict) and details.get('status') == 'error')
                            if is_error:
                                today_errors += 1
                                # Mark last matching event as error
                                for e in reversed(events):
                                    if e.get('tool') == msg.get('toolName') and e.get('status') == 'ok':
                                        e['status'] = 'error'
                                        break

                            # Add duration from details
                            if isinstance(details, dict) and details.get('duration_ms'):
                                for e in reversed(events):
                                    if e.get('tool') == msg.get('toolName') and not e.get('duration_ms'):
                                        e['duration_ms'] = details['duration_ms']
                                        break

                            # For sessions, update status from result
                            if name == 'session' and isinstance(details, dict):
                                for e in reversed(events):
                                    if e.get('tool') == msg.get('toolName'):
                                        if details.get('status') == 'done':
                                            e['session_status'] = 'done'
                                        if details.get('model'):
                                            e['model'] = details['model']
                                        if details.get('tokens'):
                                            e['tokens'] = details['tokens']
                                        break

            except Exception:
                continue

    # For cron, also pull from cron jobs data
    if name == 'cron' and not events:
        try:
            crons = _get_crons()
            for cj in crons[:20]:
                events.append({
                    'timestamp': cj.get('lastRun') or cj.get('createdAt') or '',
                    'action': 'cron',
                    'detail': (cj.get('expr') or '') + ' → ' + (cj.get('task') or cj.get('command') or '')[:60],
                    'status': 'ok' if cj.get('lastStatus') != 'error' else 'error',
                })
        except Exception:
            pass

    # For sessions, also pull live session data
    if name == 'session' and not events:
        try:
            sessions = _get_sessions()
            for sess in sessions[:20]:
                events.append({
                    'timestamp': datetime.fromtimestamp(sess['updatedAt'] / 1000).isoformat() if sess.get('updatedAt') else '',
                    'action': 'session',
                    'detail': sess.get('displayName') or sess.get('sessionId', '?')[:20],
                    'session_status': 'running',
                    'model': sess.get('model', ''),
                    'tokens': sess.get('totalTokens', 0),
                    'status': 'ok',
                })
        except Exception:
            pass

    # Sort by timestamp descending, limit to 50
    events.sort(key=lambda e: e.get('timestamp', ''), reverse=True)
    events = events[:50]

    result = {
        'name': name,
        'stats': {'today_calls': today_calls, 'today_errors': today_errors},
        'events': events,
        'total': today_calls,
    }

    # Enrich with tool-specific data
    if name == 'session':
        # Add live sub-agent data
        try:
            sa_data = api_subagents().get_json()
            result['subagents'] = sa_data.get('subagents', [])
        except Exception:
            result['subagents'] = []

    elif name == 'exec':
        # Check for running background processes
        running = []
        try:
            proc_dir = os.path.expanduser('~/.openclaw/processes')
            if not os.path.isdir(proc_dir):
                proc_dir = os.path.expanduser('~/.clawdbot/processes')
            if os.path.isdir(proc_dir):
                for pf in os.listdir(proc_dir):
                    try:
                        with open(os.path.join(proc_dir, pf)) as pfile:
                            pdata = json.load(pfile)
                            if pdata.get('running', False):
                                running.append({
                                    'command': pdata.get('command', '?'),
                                    'pid': pdata.get('pid', ''),
                                })
                    except Exception:
                        pass
        except Exception:
            pass
        result['running_commands'] = running

    elif name == 'browser':
        # Extract unique URLs from events
        seen = set()
        urls = []
        for evt in events:
            url = evt.get('detail', '')
            if url.startswith('http') and url not in seen:
                seen.add(url)
                urls.append({'url': url, 'timestamp': evt.get('timestamp', '')})
        result['recent_urls'] = urls[:20]

    elif name == 'cron':
        # Add full cron job list
        try:
            crons = _get_crons()
            result['cron_jobs'] = []
            for cj in crons:
                result['cron_jobs'].append({
                    'id': cj.get('id', ''),
                    'name': cj.get('name') or cj.get('task') or cj.get('id', '?'),
                    'expr': (cj['expr'].get('expr', str(cj['expr'])) if isinstance(cj.get('expr'), dict) else cj.get('expr') or cj.get('schedule', '')),
                    'task': cj.get('task') or cj.get('command', ''),
                    'channel': cj.get('channel', ''),
                    'lastRun': cj.get('lastRun') or cj.get('lastRunAt', ''),
                    'nextRun': cj.get('nextRun') or cj.get('nextRunAt', ''),
                    'lastStatus': cj.get('lastStatus', 'ok'),
                    'lastError': cj.get('lastError', ''),
                })
        except Exception:
            result['cron_jobs'] = []

    elif name == 'memory':
        # Add workspace file listing
        try:
            result['memory_files'] = _get_memory_files()
        except Exception:
            result['memory_files'] = []

    _api_tool_cache[name] = result
    _api_tool_cache_time[name] = _time.time()
    return jsonify(result)


@app.route('/api/component/runtime')
def api_component_runtime():
    """Return runtime environment info."""
    import platform
    items = []
    items.append({'label': 'Python', 'value': platform.python_version(), 'status': 'ok'})
    items.append({'label': 'OS', 'value': f'{platform.system()} {platform.release()}', 'status': 'ok'})
    items.append({'label': 'Architecture', 'value': platform.machine(), 'status': 'ok'})
    # OpenClaw version
    try:
        oc_ver = subprocess.check_output(['openclaw', '--version'], stderr=subprocess.STDOUT, timeout=5).decode().strip()
        items.append({'label': 'OpenClaw', 'value': oc_ver, 'status': 'ok'})
    except Exception:
        items.append({'label': 'OpenClaw', 'value': 'unknown', 'status': 'warning'})
    # Uptime
    try:
        up = subprocess.check_output(['uptime', '-p'], timeout=5).decode().strip()
        items.append({'label': 'Uptime', 'value': up, 'status': 'ok'})
    except Exception:
        pass
    # Memory
    try:
        mem = subprocess.check_output(['free', '-h'], timeout=5).decode().strip().split('\n')
        if len(mem) >= 2:
            parts = mem[1].split()
            used, total = parts[2], parts[1]
            items.append({'label': 'Memory', 'value': f'{used} / {total}', 'status': 'ok'})
    except Exception:
        pass
    # Disk
    try:
        df = subprocess.check_output(['df', '-h', '/'], timeout=5).decode().strip().split('\n')
        if len(df) >= 2:
            parts = df[1].split()
            items.append({'label': 'Disk /', 'value': f'{parts[2]} / {parts[1]} ({parts[4]} used)', 'status': 'critical' if int(parts[4].replace('%','')) > 90 else 'warning' if int(parts[4].replace('%','')) > 80 else 'ok'})
    except Exception:
        pass
    # Node.js
    try:
        nv = subprocess.check_output(['node', '--version'], timeout=5).decode().strip()
        items.append({'label': 'Node.js', 'value': nv, 'status': 'ok'})
    except Exception:
        pass
    return jsonify({'items': items})


@app.route('/api/component/machine')
def api_component_machine():
    """Return machine/host hardware info."""
    import platform
    items = []
    items.append({'label': 'Hostname', 'value': socket.gethostname(), 'status': 'ok'})
    # IP
    items.append({'label': 'IP', 'value': get_local_ip(), 'status': 'ok'})
    # CPU
    try:
        with open('/proc/cpuinfo') as f:
            for line in f:
                if line.startswith('model name'):
                    items.append({'label': 'CPU', 'value': line.split(':')[1].strip(), 'status': 'ok'})
                    break
    except Exception:
        items.append({'label': 'CPU', 'value': platform.processor() or 'unknown', 'status': 'ok'})
    # CPU cores
    items.append({'label': 'CPU Cores', 'value': str(os.cpu_count() or '?'), 'status': 'ok'})
    # Load average
    try:
        load = os.getloadavg()
        cores = os.cpu_count() or 1
        load_str = f'{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}'
        status = 'critical' if load[0] > cores * 2 else 'warning' if load[0] > cores else 'ok'
        items.append({'label': 'Load (1/5/15m)', 'value': load_str, 'status': status})
    except Exception:
        pass
    # GPU
    try:
        gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.used,memory.total,utilization.gpu', '--format=csv,noheader,nounits'], timeout=5).decode().strip()
        for line in gpu.split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 4:
                items.append({'label': 'GPU', 'value': f'{parts[0]}', 'status': 'ok'})
                items.append({'label': 'GPU Memory', 'value': f'{parts[1]} MiB / {parts[2]} MiB', 'status': 'ok'})
                items.append({'label': 'GPU Utilization', 'value': f'{parts[3]}%', 'status': 'warning' if int(parts[3]) > 80 else 'ok'})
    except Exception:
        items.append({'label': 'GPU', 'value': 'N/A (no nvidia-smi)', 'status': 'ok'})
    # Kernel
    items.append({'label': 'Kernel', 'value': platform.release(), 'status': 'ok'})
    return jsonify({'items': items})


@app.route('/api/component/gateway')
def api_component_gateway():
    """Parse gateway routing events from today's log file."""
    import re
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    today = datetime.now().strftime('%Y-%m-%d')
    # Try both openclaw and moltbot log dirs/naming
    candidates = [
        os.path.join(LOG_DIR, f'openclaw-{today}.log'),
        os.path.join(LOG_DIR, f'moltbot-{today}.log'),
        f'/tmp/openclaw/openclaw-{today}.log',
        f'/tmp/moltbot/moltbot-{today}.log',
    ]
    log_path = next((p for p in candidates if os.path.exists(p)), None)

    routes = []
    stats = {'today_messages': 0, 'today_heartbeats': 0, 'today_crons': 0, 'today_errors': 0}

    if not log_path:
        return jsonify({'routes': [], 'stats': stats, 'total': 0})

    try:
        with open(log_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg = entry.get('1', '') or entry.get('0', '')
                ts = entry.get('time', '')
                level = entry.get('_meta', {}).get('logLevelName', '')

                # embedded run start - main routing event
                if 'embedded run start:' in msg:
                    route = {'timestamp': ts, 'from': '', 'to': '', 'session': '', 'type': 'message', 'status': 'ok'}
                    # Extract fields: model, messageChannel, sessionId
                    m_model = re.search(r'model=(\S+)', msg)
                    m_chan = re.search(r'messageChannel=(\S+)', msg)
                    m_sid = re.search(r'sessionId=(\S+)', msg)
                    if m_model:
                        route['to'] = m_model.group(1)
                    if m_chan:
                        ch = m_chan.group(1)
                        route['from'] = ch
                        if ch == 'heartbeat':
                            route['type'] = 'heartbeat'
                            stats['today_heartbeats'] += 1
                        elif ch == 'cron':
                            route['type'] = 'cron'
                            stats['today_crons'] += 1
                        else:
                            stats['today_messages'] += 1
                    else:
                        stats['today_messages'] += 1
                    if m_sid:
                        route['session'] = m_sid.group(1)[:12]
                    # Check if it's a subagent
                    if 'subagent' in msg.lower():
                        route['type'] = 'subagent'
                    routes.append(route)
                    continue

                # Delivery failures
                if 'Delivery failed' in msg or ('Delivery' in msg and level == 'ERROR'):
                    stats['today_errors'] += 1
                    # Try to annotate the last route
                    route = {'timestamp': ts, 'from': '', 'to': '', 'session': '', 'type': 'message', 'status': 'error'}
                    m_chan = re.search(r'\((\w+) to', msg)
                    if m_chan:
                        route['from'] = m_chan.group(1)
                    route['to'] = 'delivery'
                    routes.append(route)
                    continue

                pass  # Only count delivery errors for routing stats

    except Exception:
        pass

    # Sort by timestamp descending (newest first)
    routes.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    total = len(routes)
    page = routes[offset:offset + limit]

    # --- Enhanced: active sessions, config summary, uptime, restart history ---
    import re as _re

    # Active sessions
    active_sessions = 0
    try:
        sess_file = os.path.join(SESSIONS_DIR or os.path.expanduser('~/.clawdbot/agents/main/sessions'), 'sessions.json')
        with open(sess_file) as f:
            sess_data = json.load(f)
        now_ts = time.time() * 1000  # ms
        for sid, sinfo in sess_data.items():
            updated = sinfo.get('updatedAt', 0)
            if now_ts - updated < 3600_000:  # active in last hour
                active_sessions += 1
    except Exception:
        pass

    # Config summary
    config_summary = {}
    for cf in [os.path.expanduser('~/.clawdbot/openclaw.json'), os.path.expanduser('~/.openclaw/openclaw.json')]:
        try:
            with open(cf) as f:
                cfg = json.load(f)
            plugins = cfg.get('plugins', {}).get('entries', {})
            config_summary['channels'] = [k for k, v in plugins.items() if v.get('enabled')]
            ad = cfg.get('agents', {}).get('defaults', {})
            config_summary['max_concurrent'] = ad.get('maxConcurrent', '?')
            config_summary['max_subagents'] = ad.get('subagents', {}).get('maxConcurrent', '?')
            hb = ad.get('heartbeat', {})
            config_summary['heartbeat'] = hb.get('every', '?')
            config_summary['workspace'] = ad.get('workspace', '?')
            break
        except Exception:
            continue

    # Gateway uptime (from systemd)
    uptime_str = ''
    try:
        r = subprocess.run(['systemctl', '--user', 'show', 'openclaw-gateway', '--property=ActiveEnterTimestamp'],
                          capture_output=True, text=True, timeout=3)
        ts_line = r.stdout.strip()
        if '=' in ts_line:
            uptime_str = ts_line.split('=', 1)[1].strip()
    except Exception:
        pass
    if not uptime_str:
        try:
            r = subprocess.run(['pgrep', '-a', 'openclaw'], capture_output=True, text=True, timeout=3)
            if r.stdout.strip():
                pid = r.stdout.strip().split()[0]
                r2 = subprocess.run(['ps', '-o', 'etime=', '-p', pid], capture_output=True, text=True, timeout=3)
                uptime_str = r2.stdout.strip()
        except Exception:
            pass

    # Restart history from log (look for "gateway start" or "listening" entries)
    restarts = []
    if log_path:
        try:
            r = subprocess.run(['grep', '-i', 'gateway.*start\\|listening on\\|server started', log_path],
                              capture_output=True, text=True, timeout=5)
            for line in r.stdout.splitlines()[-5:]:  # last 5 restarts
                try:
                    obj = json.loads(line.strip())
                    restarts.append(obj.get('time', ''))
                except Exception:
                    pass
        except Exception:
            pass

    stats['active_sessions'] = active_sessions
    stats['config'] = config_summary
    stats['uptime'] = uptime_str
    stats['restarts'] = restarts

    return jsonify({'routes': page, 'stats': stats, 'total': total})


@app.route('/api/component/brain')
def api_component_brain():
    """Parse session transcripts for LLM API call details."""
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    sessions_dir = SESSIONS_DIR or os.path.expanduser('~/.openclaw/agents/main/sessions')
    if not os.path.isdir(sessions_dir):
        sessions_dir = os.path.expanduser('~/.moltbot/agents/main/sessions')

    today = datetime.now().strftime('%Y-%m-%d')
    calls = []
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cost = 0.0
    durations = []
    models_seen = set()

    if os.path.isdir(sessions_dir):
        for fname in os.listdir(sessions_dir):
            if not fname.endswith('.jsonl'):
                continue
            fpath = os.path.join(sessions_dir, fname)
            session_id = fname.replace('.jsonl', '')

            try:
                # Quick check: only process files modified today
                mtime = os.path.getmtime(fpath)
                file_date = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
                if file_date != today:
                    continue

                # Detect if subagent from session metadata
                session_label = 'main'
                prev_ts = None
                with open(fpath, 'r') as f:
                    for line in f:
                        try:
                            obj = json.loads(line.strip())
                        except json.JSONDecodeError:
                            continue

                        # Check session header for subagent hints
                        if obj.get('type') == 'session':
                            continue
                        if obj.get('type') == 'custom' and obj.get('customType') == 'openclaw.session-info':
                            data = obj.get('data', {})
                            if 'subagent' in str(data.get('session', '')):
                                session_label = 'subagent:' + session_id[:8]

                        if obj.get('type') != 'message':
                            # Track user message timestamps for duration calc
                            if obj.get('type') == 'message' or (isinstance(obj.get('message'), dict) and obj['message'].get('role') == 'user'):
                                pass
                            continue

                        msg = obj.get('message', {})
                        usage = msg.get('usage')
                        if not usage or not isinstance(usage, dict):
                            # Track user message time for duration
                            if msg.get('role') == 'user':
                                prev_ts = obj.get('timestamp')
                            continue

                        if msg.get('role') != 'assistant':
                            continue

                        ts = obj.get('timestamp', '')
                        if not ts:
                            continue

                        # Only include today's entries
                        if not ts.startswith(today):
                            prev_ts = None
                            continue

                        model = msg.get('model', 'unknown') or 'unknown'
                        models_seen.add(model)

                        tokens_in = usage.get('input', 0) + usage.get('cacheRead', 0) + usage.get('cacheWrite', 0)
                        tokens_out = usage.get('output', 0)
                        cache_read = usage.get('cacheRead', 0)
                        cost_data = usage.get('cost', {})
                        call_cost = float(cost_data.get('total', 0)) if isinstance(cost_data, dict) else 0.0

                        total_input += usage.get('input', 0)
                        total_output += tokens_out
                        total_cache_read += cache_read
                        total_cost += call_cost

                        # Detect thinking blocks
                        has_thinking = False
                        for c in (msg.get('content') or []):
                            if isinstance(c, dict) and c.get('type') == 'thinking':
                                has_thinking = True
                                break

                        # Extract tools used
                        tools = []
                        for c in (msg.get('content') or []):
                            if isinstance(c, dict) and c.get('type') == 'toolCall':
                                tool_name = c.get('name', '')
                                if tool_name and tool_name not in tools:
                                    tools.append(tool_name)

                        # Compute duration from previous user message
                        duration_ms = 0
                        if prev_ts:
                            try:
                                t1 = datetime.fromisoformat(prev_ts.replace('Z', '+00:00'))
                                t2 = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                                duration_ms = int((t2 - t1).total_seconds() * 1000)
                                if 0 < duration_ms < 300000:  # sanity: < 5 min
                                    durations.append(duration_ms)
                            except:
                                pass

                        # Detect subagent from content context
                        if session_label == 'main':
                            for c in (msg.get('content') or []):
                                if isinstance(c, dict) and c.get('type') == 'text':
                                    text = c.get('text', '')[:200]
                                    if 'subagent' in text.lower():
                                        session_label = 'subagent:' + session_id[:8]
                                        break

                        calls.append({
                            'timestamp': ts,
                            'model': model,
                            'tokens_in': tokens_in,
                            'tokens_out': tokens_out,
                            'cache_read': cache_read,
                            'cache_write': usage.get('cacheWrite', 0),
                            'thinking': has_thinking,
                            'cost': '${:.4f}'.format(call_cost),
                            'cost_raw': call_cost,
                            'tools_used': tools,
                            'duration_ms': duration_ms,
                            'session': session_label,
                            'stop_reason': msg.get('stopReason', ''),
                        })

                        prev_ts = ts

            except Exception:
                continue

    # Sort by timestamp descending
    calls.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    total = len(calls)
    avg_ms = int(sum(durations) / len(durations)) if durations else 0
    primary_model = max(models_seen, key=lambda m: sum(1 for c in calls if c['model'] == m)) if models_seen else 'unknown'
    thinking_count = sum(1 for c in calls if c.get('thinking'))
    cache_hit_count = sum(1 for c in calls if c.get('cache_read', 0) > 0)
    total_cache_write = sum(c.get('cache_write', 0) for c in calls)

    result = {
        'stats': {
            'today_calls': total,
            'today_tokens': {
                'input': total_input,
                'output': total_output,
                'cache_read': total_cache_read,
                'cache_write': total_cache_write,
            },
            'today_cost': '${:.2f}'.format(total_cost),
            'model': primary_model,
            'avg_response_ms': avg_ms,
            'thinking_calls': thinking_count,
            'cache_hits': cache_hit_count,
        },
        'calls': calls[offset:offset + limit],
        'total': total,
    }
    return jsonify(result)


@app.route('/api/heatmap')
def api_heatmap():
    """Activity heatmap - events per hour for the last 7 days."""
    now = datetime.now()
    # Initialize 7 days × 24 hours grid
    grid = {}
    day_labels = []
    for i in range(6, -1, -1):
        d = now - timedelta(days=i)
        ds = d.strftime('%Y-%m-%d')
        grid[ds] = [0] * 24
        day_labels.append({'date': ds, 'label': d.strftime('%a %d')})

    # Parse log files for the last 7 days
    for i in range(7):
        d = now - timedelta(days=i)
        ds = d.strftime('%Y-%m-%d')
        log_file = _find_log_file(ds)
        if not log_file:
            continue
        try:
            with open(log_file) as f:
                for line in f:
                    try:
                        obj = json.loads(line.strip())
                        ts = obj.get('time') or (obj.get('_meta', {}).get('date') if isinstance(obj.get('_meta'), dict) else None)
                        if ts:
                            if isinstance(ts, (int, float)):
                                dt = datetime.fromtimestamp(ts / 1000 if ts > 1e12 else ts)
                            else:
                                dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00').replace('+00:00', ''))
                            hour = dt.hour
                            day_key = dt.strftime('%Y-%m-%d')
                            if day_key in grid:
                                grid[day_key][hour] += 1
                    except Exception:
                        # Count non-JSON lines too
                        if ds in grid:
                            grid[ds][12] += 1  # default to noon
        except Exception:
            pass

    max_val = max(max(hours) for hours in grid.values()) if grid else 0
    days = []
    for dl in day_labels:
        days.append({'label': dl['label'], 'hours': grid.get(dl['date'], [0] * 24)})

    return jsonify({'days': days, 'max': max_val})


@app.route('/api/system-health')
def api_system_health():
    """Comprehensive system health for the Overview tab."""
    import shutil

    # --- SERVICES (auto-detect gateway + user-configured extras) ---
    services = []
    # Always check OpenClaw Gateway (from gateway config or auto-detect)
    cfg = _load_gw_config()
    if cfg.get('url'):
        try:
            from urllib.parse import urlparse
            gw_port = urlparse(cfg['url']).port or 18789
        except Exception:
            gw_port = _detect_gateway_port()
    else:
        gw_port = _detect_gateway_port()
    service_checks = [('OpenClaw Gateway', gw_port)]
    # Add any user-configured extra services
    for svc in EXTRA_SERVICES:
        service_checks.append((svc['name'], svc['port']))
    # Add Mission Control only if MC_URL is explicitly configured
    if MC_URL:
        try:
            from urllib.parse import urlparse
            mc_parsed = urlparse(MC_URL)
            mc_port = mc_parsed.port or 3002
            service_checks.append(('Mission Control', mc_port))
        except Exception:
            pass
    for name, port in service_checks:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            ok = s.connect_ex(('127.0.0.1', port)) == 0
            s.close()
            # If direct socket fails and this is the gateway, try docker exec
            if not ok and 'Gateway' in name:
                cfg_check = _load_gw_config()
                if cfg_check.get('url', '').startswith('docker://') or cfg_check.get('token'):
                    docker_result = _gw_invoke_docker('session_status', {}, cfg_check.get('token'))
                    if docker_result:
                        ok = True
            services.append({'name': name, 'port': port, 'up': ok})
        except Exception:
            services.append({'name': name, 'port': port, 'up': False})

    # --- DISK USAGE ---
    disks = []
    for mount in _detect_disk_mounts():
        try:
            usage = shutil.disk_usage(mount)
            used_gb = usage.used / (1024**3)
            total_gb = usage.total / (1024**3)
            pct = (usage.used / usage.total) * 100
            disks.append({'mount': mount, 'used_gb': round(used_gb, 1), 'total_gb': round(total_gb, 1), 'pct': round(pct, 1)})
        except Exception:
            pass

    # --- CRON JOBS ---
    gw_cron_data = _gw_invoke('cron', {'action': 'list', 'includeDisabled': True})
    crons = gw_cron_data.get('jobs', []) if gw_cron_data and 'jobs' in gw_cron_data else _get_crons()
    cron_enabled = len([j for j in crons if j.get('enabled', True)])
    cron_ok_24h = 0
    cron_failed = []
    now_ts = time.time()
    for j in crons:
        last = j.get('lastRun', {})
        if not last:
            continue
        run_ts = last.get('timestamp', 0)
        if isinstance(run_ts, str):
            try:
                run_ts = datetime.fromisoformat(run_ts.replace('Z', '+00:00')).timestamp()
            except Exception:
                run_ts = 0
        if run_ts and (now_ts - run_ts) < 86400:
            if last.get('exitCode', last.get('exit', 0)) == 0 and not last.get('error'):
                cron_ok_24h += 1
            else:
                cron_failed.append(j.get('name', j.get('id', 'unknown')))

    # --- SUB-AGENTS (24H) ---
    sessions = _get_sessions()
    sa_runs = 0
    sa_success = 0
    for s in sessions:
        mtime = s.get('updatedAt', 0)
        if isinstance(mtime, (int, float)) and mtime > 1e12:
            mtime = mtime / 1000
        if mtime and (now_ts - mtime) < 86400:
            sid = s.get('sessionId', '')
            if 'subagent' in sid:
                sa_runs += 1
                sa_success += 1  # We don't track failure in session files currently

    sa_pct = round((sa_success / sa_runs * 100) if sa_runs > 0 else 100, 0)

    return jsonify({
        'services': services,
        'disks': disks,
        'crons': {'enabled': cron_enabled, 'ok24h': cron_ok_24h, 'failed': cron_failed},
        'subagents': {'runs': sa_runs, 'successPct': sa_pct},
    })


@app.route('/api/health')
def api_health():
    """System health checks."""
    checks = []
    # 1. Gateway - check if gateway port is responding
    gw_port = _detect_gateway_port()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex(('127.0.0.1', gw_port))
        s.close()
        if result == 0:
            checks.append({'id': 'gateway', 'status': 'healthy', 'color': 'green', 'detail': f'Port {gw_port} responding'})
        else:
            # Fallback: check process
            gw = subprocess.run(['pgrep', '-f', 'moltbot'], capture_output=True, text=True)
            if gw.returncode == 0:
                checks.append({'id': 'gateway', 'status': 'warning', 'color': 'yellow', 'detail': 'Process running, port not responding'})
            else:
                checks.append({'id': 'gateway', 'status': 'critical', 'color': 'red', 'detail': 'Not running'})
    except Exception:
        checks.append({'id': 'gateway', 'status': 'critical', 'color': 'red', 'detail': 'Check failed'})

    # 2. Disk space - warn if < 5GB free
    try:
        st = os.statvfs('/')
        free_gb = (st.f_bavail * st.f_frsize) / (1024 ** 3)
        total_gb = (st.f_blocks * st.f_frsize) / (1024 ** 3)
        pct_used = ((total_gb - free_gb) / total_gb) * 100
        if free_gb < 2:
            checks.append({'id': 'disk', 'status': 'critical', 'color': 'red', 'detail': f'{free_gb:.1f} GB free ({pct_used:.0f}% used)'})
        elif free_gb < 5:
            checks.append({'id': 'disk', 'status': 'warning', 'color': 'yellow', 'detail': f'{free_gb:.1f} GB free ({pct_used:.0f}% used)'})
        else:
            checks.append({'id': 'disk', 'status': 'healthy', 'color': 'green', 'detail': f'{free_gb:.1f} GB free ({pct_used:.0f}% used)'})
    except Exception:
        checks.append({'id': 'disk', 'status': 'warning', 'color': 'yellow', 'detail': 'Check failed'})

    # 3. Memory usage (RSS of this process + overall)
    try:
        import resource
        rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # KB -> MB on Linux
        mem = subprocess.run(['free', '-m'], capture_output=True, text=True)
        mem_parts = mem.stdout.strip().split('\n')[1].split()
        used_mb = int(mem_parts[2])
        total_mb = int(mem_parts[1])
        pct = (used_mb / total_mb) * 100
        if pct > 90:
            checks.append({'id': 'memory', 'status': 'critical', 'color': 'red', 'detail': f'{used_mb}MB / {total_mb}MB ({pct:.0f}%)'})
        elif pct > 75:
            checks.append({'id': 'memory', 'status': 'warning', 'color': 'yellow', 'detail': f'{used_mb}MB / {total_mb}MB ({pct:.0f}%)'})
        else:
            checks.append({'id': 'memory', 'status': 'healthy', 'color': 'green', 'detail': f'{used_mb}MB / {total_mb}MB ({pct:.0f}%)'})
    except Exception:
        checks.append({'id': 'memory', 'status': 'warning', 'color': 'yellow', 'detail': 'Check failed'})

    # 4. Uptime
    try:
        uptime = subprocess.run(['uptime', '-p'], capture_output=True, text=True).stdout.strip().replace('up ', '')
        checks.append({'id': 'uptime', 'status': 'healthy', 'color': 'green', 'detail': uptime})
    except Exception:
        checks.append({'id': 'uptime', 'status': 'warning', 'color': 'yellow', 'detail': 'Unknown'})

    # 5. OTLP Metrics
    if _has_otel_data():
        ago = time.time() - _otel_last_received
        if ago < 300:  # <5min
            total = sum(len(metrics_store[k]) for k in metrics_store)
            checks.append({'id': 'otel', 'status': 'healthy', 'color': 'green',
                           'detail': f'Connected - {total} data points, last {int(ago)}s ago'})
        elif ago < 3600:
            checks.append({'id': 'otel', 'status': 'warning', 'color': 'yellow',
                           'detail': f'Stale - last data {int(ago/60)}m ago'})
        else:
            checks.append({'id': 'otel', 'status': 'warning', 'color': 'yellow',
                           'detail': f'Stale - last data {int(ago/3600)}h ago'})
    elif _HAS_OTEL_PROTO:
        checks.append({'id': 'otel', 'status': 'warning', 'color': 'yellow',
                       'detail': 'OTLP ready - no data received yet'})
    else:
        checks.append({'id': 'otel', 'status': 'warning', 'color': 'yellow',
                       'detail': 'Not installed - pip install clawmetry[otel]'})

    return jsonify({'checks': checks})


@app.route('/api/health-stream')
def api_health_stream():
    """SSE endpoint - auto-refresh health checks every 30 seconds."""
    if not _acquire_stream_slot('health'):
        return jsonify({'error': 'Too many active health streams'}), 429

    def generate():
        started_at = time.time()
        try:
            while True:
                if time.time() - started_at > SSE_MAX_SECONDS:
                    yield 'event: done\ndata: {"reason":"max_duration_reached"}\n\n'
                    break
                try:
                    with app.test_request_context():
                        resp = api_health()
                        data = resp.get_json()
                        yield f'data: {json.dumps(data)}\n\n'
                except Exception:
                    yield f'data: {json.dumps({"checks": []})}\n\n'
                time.sleep(30)
        finally:
            _release_stream_slot('health')

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/cost-optimization')
def api_cost_optimization():
    """Cost optimization analysis and local model fallback recommendations."""
    try:
        # Get cost metrics
        costs = _get_cost_summary()
        
        # Check Ollama availability
        local_models = _check_ollama_availability()
        
        # Generate recommendations
        recommendations = _generate_cost_recommendations(costs, local_models)
        
        # Get recent expensive operations
        expensive_ops = _get_expensive_operations()
        
        return jsonify({
            'costs': costs,
            'localModels': local_models,
            'recommendations': recommendations,
            'expensiveOps': expensive_ops
        })
    except Exception as e:
        return jsonify({
            'costs': {'today': 0, 'week': 0, 'month': 0, 'projected': 0},
            'localModels': {'available': False, 'count': 0, 'models': []},
            'recommendations': [{'title': 'API Error', 'description': str(e), 'priority': 'low'}],
            'expensiveOps': []
        })


@app.route('/api/automation-analysis')
def api_automation_analysis():
    """Automation pattern analysis and suggestions for new cron jobs or skills."""
    try:
        # Analyze recent patterns
        patterns = _analyze_work_patterns()
        
        # Generate automation suggestions
        suggestions = _generate_automation_suggestions(patterns)
        
        return jsonify({
            'patterns': patterns,
            'suggestions': suggestions,
            'lastAnalysis': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({
            'patterns': [],
            'suggestions': [],
            'error': str(e),
            'lastAnalysis': datetime.now(timezone.utc).isoformat()
        })


# ── Data Helpers ────────────────────────────────────────────────────────

def _get_sessions():
    """Get sessions via gateway API first, file fallback."""
    now = time.time()
    if _sessions_cache['data'] is not None and (now - _sessions_cache['ts']) < _SESSIONS_CACHE_TTL:
        return _sessions_cache['data']

    # Try WebSocket RPC first
    api_data = _gw_ws_rpc('sessions.list')
    if api_data and 'sessions' in api_data:
        sessions = []
        for s in api_data['sessions'][:30]:
            sessions.append({
                'sessionId': s.get('key', ''),
                'key': s.get('key', '')[:12] + '...',
                'displayName': s.get('displayName', s.get('key', '')[:20]),
                'updatedAt': s.get('updatedAtMs', s.get('lastActiveMs', 0)),
                'model': s.get('model', s.get('modelRef', 'unknown')),
                'channel': s.get('channel', 'unknown'),
                'totalTokens': s.get('totalTokens', 0),
                'contextTokens': api_data.get('defaults', {}).get('contextTokens', 200000),
                'kind': s.get('kind', 'direct'),
                'agent': s.get('agentId', 'main'),
            })
        _sessions_cache['data'] = sessions
        _sessions_cache['ts'] = now
        return sessions

    # File-based fallback
    return _get_sessions_from_files()


def _get_sessions_from_files():
    """Read active sessions from the session directory (file-based fallback)."""
    now = time.time()

    def _read_session_model_fast(file_path):
        """Best-effort model extraction from the tail of a session file."""
        try:
            lines = []
            with open(file_path, 'r') as f:
                lines = list(deque(f, maxlen=400))
                for line in reversed(lines):
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    if obj.get('type') != 'message':
                        continue
                    msg = obj.get('message', {})
                    if not isinstance(msg, dict):
                        continue
                    model = msg.get('model')
                    if model:
                        return model
        except Exception:
            pass
        return 'unknown'

    sessions = []
    try:
        base = SESSIONS_DIR or os.path.expanduser('~/.clawdbot/agents/main/sessions')
        if not os.path.isdir(base):
            return sessions
        idx_files = sorted(
            [f for f in os.listdir(base) if f.endswith('.jsonl') and 'deleted' not in f],
            key=lambda f: os.path.getmtime(os.path.join(base, f)),
            reverse=True
        )
        for fname in idx_files[:30]:
            fpath = os.path.join(base, fname)
            try:
                mtime = os.path.getmtime(fpath)
                size = os.path.getsize(fpath)
                with open(fpath) as f:
                    first = json.loads(f.readline())
                sid = fname.replace('.jsonl', '')
                sessions.append({
                    'sessionId': sid,
                    'key': sid[:12] + '...',
                    'displayName': sid[:20],
                    'updatedAt': int(mtime * 1000),
                    'model': _read_session_model_fast(fpath),
                    'channel': 'unknown',
                    'totalTokens': size,
                    'contextTokens': 200000,
                })
            except Exception:
                pass
    except Exception:
        pass
    _sessions_cache['data'] = sessions
    _sessions_cache['ts'] = now
    return sessions


def _get_crons():
    """Get crons via gateway API first, file fallback."""
    # Try WebSocket RPC first
    api_data = _gw_ws_rpc('cron.list')
    if api_data and 'jobs' in api_data:
        return api_data['jobs']
    # File-based fallback
    return _get_crons_from_files()


def _get_crons_from_files():
    """Read crons from OpenClaw/moltbot state (file-based fallback)."""
    candidates = [
        os.path.expanduser('~/.openclaw/cron/jobs.json'),
        os.path.expanduser('~/.clawdbot/cron/jobs.json'),
    ]
    # Also check data dir if set via env
    data_dir = os.environ.get('OPENCLAW_DATA_DIR', '')
    if data_dir:
        candidates.insert(0, os.path.join(data_dir, 'cron', 'jobs.json'))
    for crons_file in candidates:
        try:
            if os.path.exists(crons_file):
                with open(crons_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        return data.get('jobs', list(data.values()))
        except Exception:
            pass
    return []


def _get_memory_files():
    """List workspace memory files."""
    result = []
    workspace = WORKSPACE or os.getcwd()
    memory_dir = MEMORY_DIR or os.path.join(workspace, "memory")

    for name in ['MEMORY.md', 'SOUL.md', 'IDENTITY.md', 'USER.md', 'AGENTS.md', 'TOOLS.md', 'HEARTBEAT.md']:
        path = os.path.join(workspace, name)
        if os.path.exists(path):
            result.append({'path': name, 'size': os.path.getsize(path)})
    if os.path.isdir(memory_dir):
        pattern = os.path.join(memory_dir, '*.md')
        for f in sorted(glob.glob(pattern), reverse=True):
            name = 'memory/' + os.path.basename(f)
            result.append({'path': name, 'size': os.path.getsize(f)})
    return result


def _get_cost_summary():
    """Calculate cost summary from metrics store."""
    now = datetime.now(CET)
    today = now.strftime('%Y-%m-%d')
    week_start = (now - timedelta(days=7)).strftime('%Y-%m-%d')
    month_start = (now - timedelta(days=30)).strftime('%Y-%m-%d')
    
    costs = {'today': 0, 'week': 0, 'month': 0, 'projected': 0}
    
    with _metrics_lock:
        for entry in metrics_store.get('cost', []):
            entry_date = datetime.fromtimestamp(entry.get('timestamp', 0) / 1000, CET).strftime('%Y-%m-%d')
            entry_cost = entry.get('usd', 0)
            
            if entry_date == today:
                costs['today'] += entry_cost
            if entry_date >= week_start:
                costs['week'] += entry_cost
            if entry_date >= month_start:
                costs['month'] += entry_cost
    
    # Project monthly cost based on current daily average
    if costs['month'] > 0:
        days_in_period = min(30, (now - datetime.strptime(month_start, '%Y-%m-%d').replace(tzinfo=CET)).days + 1)
        daily_avg = costs['month'] / days_in_period
        costs['projected'] = daily_avg * 30
    
    return costs


def _check_ollama_availability():
    """Check if Ollama is running and what models are available."""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=3)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            tool_capable_models = []
            
            for model in models:
                # Check if model supports tools (simplified check)
                model_name = model.get('name', '')
                # Common tool-capable models
                if any(x in model_name.lower() for x in ['llama3', 'qwen', 'gpt-oss', 'mistral', 'deepseek']):
                    tool_capable_models.append(model_name)
            
            return {
                'available': True,
                'count': len(tool_capable_models),
                'models': tool_capable_models[:10]  # Limit display
            }
    except Exception:
        pass
    
    return {'available': False, 'count': 0, 'models': []}


def _generate_cost_recommendations(costs, local_models):
    """Generate cost optimization recommendations."""
    recommendations = []
    
    # High cost alerts
    if costs['today'] > 1.0:
        recommendations.append({
            'title': 'High Daily Cost',
            'description': f"Today's usage (${costs['today']:.3f}) is high. Consider using local models for routine tasks.",
            'priority': 'high',
            'action': 'Review recent expensive operations below'
        })
    
    # Local model setup
    if not local_models['available']:
        recommendations.append({
            'title': 'Install Local Models',
            'description': 'Set up Ollama with local models to reduce API costs for formatting, simple lookups, and drafts.',
            'priority': 'medium',
            'action': 'curl -fsSL https://ollama.ai/install.sh | sh && ollama pull llama3.3'
        })
    elif local_models['count'] < 2:
        recommendations.append({
            'title': 'Expand Local Model Selection',
            'description': 'Add more local models for better task coverage and cost optimization.',
            'priority': 'low',
            'action': 'ollama pull qwen2.5-coder:32b'
        })
    
    # Projected cost warning
    if costs['projected'] > 50.0:
        recommendations.append({
            'title': 'High Monthly Projection',
            'description': f"Projected monthly cost (${costs['projected']:.2f}) is high. Implement local model fallback urgently.",
            'priority': 'high',
            'action': 'Configure cost thresholds and local model routing'
        })
    
    # Low-stakes task identification
    with _metrics_lock:
        recent_calls = metrics_store.get('tokens', [])[-100:]  # Last 100 calls
        high_cost_calls = [c for c in recent_calls if c.get('total', 0) > 10000]
        if len(high_cost_calls) > 20:
            recommendations.append({
                'title': 'High Token Usage Detected',
                'description': 'Many recent calls use >10K tokens. Review if all require cloud models.',
                'priority': 'medium',
                'action': 'Implement task classification for local vs cloud routing'
            })
    
    return recommendations


def _get_expensive_operations():
    """Get recent high-cost operations for analysis."""
    expensive_ops = []
    
    with _metrics_lock:
        # Combine cost and token data
        recent_tokens = metrics_store.get('tokens', [])[-50:]
        recent_costs = metrics_store.get('cost', [])[-50:]
        
        # Match tokens with costs by timestamp (approximate)
        for cost_entry in recent_costs:
            if cost_entry.get('usd', 0) > 0.01:  # Only show operations >$0.01
                timestamp = cost_entry.get('timestamp', 0)
                model = cost_entry.get('model', 'unknown')
                cost = cost_entry.get('usd', 0)
                
                # Find matching token entry
                token_entry = None
                for t in recent_tokens:
                    if abs(t.get('timestamp', 0) - timestamp) < 5000:  # Within 5 seconds
                        if t.get('model', '') == model:
                            token_entry = t
                            break
                
                tokens = token_entry.get('total', 0) if token_entry else 0
                time_ago = datetime.fromtimestamp(timestamp / 1000, CET).strftime('%H:%M')
                
                # Determine if this operation could be optimized
                can_optimize = False
                if tokens > 0:
                    # Simple heuristic: high token count with low complexity ratio might be local-model suitable
                    # This is a simplified check - in practice you'd analyze the actual request content
                    if tokens < 5000 and 'gpt' not in model.lower() and 'simple' in model.lower():
                        can_optimize = True
                
                expensive_ops.append({
                    'model': model,
                    'cost': cost,
                    'tokens': f"{tokens:,}" if tokens > 0 else "unknown",
                    'timeAgo': time_ago,
                    'canOptimize': can_optimize
                })
    
    return sorted(expensive_ops, key=lambda x: x['cost'], reverse=True)[:10]


def _analyze_work_patterns():
    """Analyze recent work patterns from logs and metrics to detect repetitive tasks."""
    patterns = []
    
    try:
        # Analyze recent log files for repetitive patterns
        log_files = _get_recent_log_files(7)  # Last 7 days
        command_frequency = {}
        tool_frequency = {}
        error_patterns = {}
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Track tool usage patterns
                        if 'tool_call' in line and 'exec' in line:
                            try:
                                if '"command"' in line:
                                    # Extract command from tool call
                                    import re
                                    cmd_match = re.search(r'"command":\s*"([^"]+)"', line)
                                    if cmd_match:
                                        cmd = cmd_match.group(1).split()[0]  # First word only
                                        command_frequency[cmd] = command_frequency.get(cmd, 0) + 1
                            except:
                                pass
                        
                        # Track tool names
                        for tool in ['curl', 'git', 'npm', 'systemctl', 'grep', 'find', 'ls']:
                            if tool in line and 'tool_call' in line:
                                tool_frequency[tool] = tool_frequency.get(tool, 0) + 1
                        
                        # Track common error patterns
                        if 'error' in line.lower() or 'failed' in line.lower():
                            for pattern in ['connection failed', 'timeout', 'not found', 'permission denied']:
                                if pattern in line.lower():
                                    error_patterns[pattern] = error_patterns.get(pattern, 0) + 1
                                    
            except Exception:
                continue
        
        # Generate pattern insights
        # High-frequency commands
        for cmd, count in command_frequency.items():
            if count >= 5:  # Used 5+ times in the past week
                confidence = min(90, count * 10)  # Higher frequency = higher confidence
                priority = 'high' if count >= 15 else 'medium' if count >= 10 else 'low'
                patterns.append({
                    'title': f'Frequent "{cmd}" command usage',
                    'description': f'Command "{cmd}" has been used {count} times in the past week. This might be a candidate for automation.',
                    'frequency': f'{count} times/week',
                    'confidence': confidence,
                    'priority': priority,
                    'type': 'command',
                    'target': cmd
                })
        
        # Repeated error handling
        for error, count in error_patterns.items():
            if count >= 3:
                patterns.append({
                    'title': f'Recurring error: {error}',
                    'description': f'This error pattern has occurred {count} times. Consider adding error handling automation.',
                    'frequency': f'{count} occurrences/week',
                    'confidence': 75,
                    'priority': 'medium',
                    'type': 'error',
                    'target': error
                })
        
        # Check for Mission Control task patterns (only if MC_URL is configured)
        if MC_URL:
            try:
                mc_response = subprocess.run(['curl', '-s', f'{MC_URL}/api/tasks'],
                                           capture_output=True, text=True, timeout=5)
                if mc_response.returncode == 0:
                    mc_data = json.loads(mc_response.stdout)
                    if 'tasks' in mc_data:
                        task_types = {}
                        for task in mc_data['tasks']:
                            title = task.get('title', '').lower()
                            for keyword in ['deploy', 'fix', 'update', 'build', 'test', 'backup']:
                                if keyword in title:
                                    task_types[keyword] = task_types.get(keyword, 0) + 1
                        for task_type, count in task_types.items():
                            if count >= 3:
                                patterns.append({
                                    'title': f'Frequent {task_type} tasks',
                                    'description': f'You have {count} tasks involving "{task_type}". This could be automated.',
                                    'frequency': f'{count} tasks',
                                    'confidence': 80,
                                    'priority': 'medium',
                                    'type': 'task',
                                    'target': task_type
                                })
            except Exception:
                pass
            
    except Exception as e:
        # Add a debug pattern if analysis fails
        patterns.append({
            'title': 'Pattern analysis limited',
            'description': f'Could not fully analyze patterns: {str(e)}',
            'frequency': 'unknown',
            'confidence': 10,
            'priority': 'low',
            'type': 'debug',
            'target': 'analysis'
        })
    
    return sorted(patterns, key=lambda x: (x['priority'] == 'high', x['priority'] == 'medium', x['confidence']), reverse=True)


def _generate_automation_suggestions(patterns):
    """Generate concrete automation suggestions based on detected patterns."""
    suggestions = []
    
    for pattern in patterns:
        if pattern['type'] == 'command' and pattern['target']:
            cmd = pattern['target']
            
            # Command-specific automation suggestions
            if cmd in ['curl', 'git', 'systemctl']:
                suggestions.append({
                    'title': f'Automate {cmd} monitoring',
                    'description': f'Create a cron job to monitor and auto-fix common {cmd} operations.',
                    'type': 'cron',
                    'implementation': f'# Add to cron: */15 * * * * /path/to/auto-{cmd}.sh',
                    'impact': 'Medium - reduces manual monitoring',
                    'effort': 'Low - single script creation'
                })
            
            elif cmd in ['npm', 'git']:
                suggestions.append({
                    'title': f'{cmd.upper()} automation skill',
                    'description': f'Create a skill that automates common {cmd} workflows with error handling.',
                    'type': 'skill',
                    'implementation': f'Skills/{cmd}-automation/SKILL.md - wrapper with retry logic',
                    'impact': 'High - automates entire workflow',
                    'effort': 'Medium - requires skill development'
                })
        
        elif pattern['type'] == 'error':
            error_type = pattern['target']
            suggestions.append({
                'title': f'Auto-recovery for {error_type}',
                'description': f'Create monitoring that detects "{error_type}" errors and attempts automatic recovery.',
                'type': 'cron',
                'implementation': f'*/10 * * * * /scripts/auto-recover-{error_type.replace(" ", "-")}.sh',
                'impact': 'High - prevents manual intervention',
                'effort': 'Medium - requires error detection logic'
            })
        
        elif pattern['type'] == 'task':
            task_type = pattern['target']
            if task_type in ['deploy', 'build', 'update']:
                suggestions.append({
                    'title': f'CI/CD pipeline for {task_type}',
                    'description': f'Automate {task_type} tasks with GitHub Actions or cron-based pipeline.',
                    'type': 'automation',
                    'implementation': f'.github/workflows/{task_type}.yml or cron-based pipeline',
                    'impact': 'Very High - eliminates manual tasks',
                    'effort': 'High - requires pipeline setup'
                })
    
    # Add some universal automation suggestions
    suggestions.extend([
        {
            'title': 'Health monitoring cron',
            'description': 'Create a cron job that monitors system health and alerts on issues.',
            'type': 'cron',
            'implementation': '0 */6 * * * /scripts/health-check.sh | logger',
            'impact': 'Medium - proactive issue detection',
            'effort': 'Low - single monitoring script'
        },
        {
            'title': 'Log rotation automation',
            'description': 'Automate log cleanup to prevent disk space issues.',
            'type': 'cron',
            'implementation': '0 2 * * 0 find /var/log -type f -name "*.log" -mtime +7 -delete',
            'impact': 'Medium - prevents disk space issues',
            'effort': 'Very Low - single command cron'
        },
        {
            'title': 'Backup verification skill',
            'description': 'Create a skill that verifies backup integrity and reports status.',
            'type': 'skill',
            'implementation': 'Skills/backup-monitor/SKILL.md - checks backup health',
            'impact': 'High - ensures backup reliability',
            'effort': 'Medium - requires backup checking logic'
        }
    ])
    
    # Remove duplicates and limit to top suggestions
    seen_titles = set()
    unique_suggestions = []
    for suggestion in suggestions:
        if suggestion['title'] not in seen_titles:
            seen_titles.add(suggestion['title'])
            unique_suggestions.append(suggestion)
    
    return unique_suggestions[:8]  # Limit to 8 suggestions max


def _get_recent_log_files(days=7):
    """Get list of recent log files to analyze."""
    log_files = []
    
    if LOG_DIR and os.path.isdir(LOG_DIR):
        # OpenClaw/Moltbot logs
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            log_file = os.path.join(LOG_DIR, f'moltbot-{date}.log')
            if os.path.isfile(log_file):
                log_files.append(log_file)
    
    # Also check journalctl if available
    try:
        result = subprocess.run(['journalctl', '--user', '-u', 'moltbot-gateway', 
                               '--since', f'{days} days ago', '--no-pager'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            # Create temporary file with journalctl output for analysis
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
                f.write(result.stdout)
                log_files.append(f.name)
    except:
        pass
    
    return log_files


# ── CLI Entry Point ─────────────────────────────────────────────────────

BANNER = r"""
   ____ _                 __  __      _
  / ___| | __ ___      __|  \/  | ___| |_ _ __ _   _
 | |   | |/ _` \ \ /\ / /| |\/| |/ _ \ __| '__| | | |
 | |___| | (_| |\ V  V / | |  | |  __/ |_| |  | |_| |
  \____|_|\__,_| \_/\_/  |_|  |_|\___|\__|_|   \__, |
                                                |___/
                          v{version}

  🦞  See your agent think

  Tabs: Overview · 📊 Usage · Sessions · Crons · Logs
        Memory · 📜 Transcripts · 🌊 Flow
  Flow: Click nodes: 🧠 Automation Advisor · 💰 Cost Optimizer · 🕰️ Time Travel
"""


def main():
    parser = argparse.ArgumentParser(
        description="ClawMetry - Real-time observability for your AI agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Environment variables:\n"
               "  OPENCLAW_HOME         Agent workspace directory\n"
               "  OPENCLAW_LOG_DIR      Log directory (default: auto-detected)\n"
               "  OPENCLAW_METRICS_FILE Path to metrics persistence JSON file\n"
               "  OPENCLAW_USER         Your name in the Flow visualization\n"
               "  OPENCLAW_SSE_MAX_SECONDS  Max duration for each SSE stream (default: 300)\n"
    )
    parser.add_argument('--port', '-p', type=int, default=8900, help='Port (default: 8900)')
    parser.add_argument('--host', '-H', type=str, default='127.0.0.1', help='Host (default: 127.0.0.1)')
    parser.add_argument('--workspace', '-w', type=str, help='Agent workspace directory')
    parser.add_argument('--data-dir', '-d', type=str, help='OpenClaw data directory (e.g. ~/.openclaw). Auto-sets sessions, crons, workspace if not specified.')
    parser.add_argument('--log-dir', '-l', type=str, help='Log directory')
    parser.add_argument('--sessions-dir', '-s', type=str, help='Sessions directory (transcript .jsonl files)')
    parser.add_argument('--metrics-file', '-m', type=str, help='Path to metrics persistence JSON file')
    parser.add_argument('--name', '-n', type=str, help='Your name (shown in Flow tab)')
    parser.add_argument('--debug', dest='debug', action='store_true', default=True, help='Enable debug mode with auto-reload (default: enabled)')
    parser.add_argument('--no-debug', dest='debug', action='store_false', help='Disable debug mode and auto-reload')
    parser.add_argument('--sse-max-seconds', type=int, default=None, help='Max seconds per SSE connection (default: 300)')
    parser.add_argument('--max-log-stream-clients', type=int, default=10, help='Max concurrent /api/logs-stream clients')
    parser.add_argument('--max-health-stream-clients', type=int, default=10, help='Max concurrent /api/health-stream clients')
    parser.add_argument('--monitor-service', action='append', default=[], metavar='NAME:PORT',
                        help='Additional service to monitor (e.g. "My App:8080"). Can be repeated.')
    parser.add_argument('--mc-url', type=str, help='Mission Control URL (e.g. http://localhost:3002). Disabled by default.')
    parser.add_argument('--version', '-v', action='version', version=f'clawmetry {__version__}')

    args = parser.parse_args()
    detect_config(args)

    # Parse --monitor-service flags
    global EXTRA_SERVICES, MC_URL
    for svc_spec in args.monitor_service:
        if ':' in svc_spec:
            name, port_str = svc_spec.rsplit(':', 1)
            try:
                EXTRA_SERVICES.append({'name': name.strip(), 'port': int(port_str.strip())})
            except ValueError:
                print(f"⚠️  Invalid --monitor-service format: {svc_spec} (expected NAME:PORT)")
        else:
            print(f"⚠️  Invalid --monitor-service format: {svc_spec} (expected NAME:PORT)")

    # Mission Control URL
    if args.mc_url:
        MC_URL = args.mc_url
    elif not MC_URL:
        MC_URL = os.environ.get("MC_URL", "")

    # Metrics file config
    global METRICS_FILE
    if args.metrics_file:
        METRICS_FILE = os.path.expanduser(args.metrics_file)
    elif os.environ.get('OPENCLAW_METRICS_FILE'):
        METRICS_FILE = os.path.expanduser(os.environ['OPENCLAW_METRICS_FILE'])

    # Stream limits
    global SSE_MAX_SECONDS, MAX_LOG_STREAM_CLIENTS, MAX_HEALTH_STREAM_CLIENTS
    sse_max = args.sse_max_seconds
    if sse_max is None:
        env_sse_max = os.environ.get('OPENCLAW_SSE_MAX_SECONDS', '').strip()
        if env_sse_max:
            try:
                sse_max = int(env_sse_max)
            except ValueError:
                sse_max = None
    if sse_max is not None and sse_max > 0:
        SSE_MAX_SECONDS = sse_max
    MAX_LOG_STREAM_CLIENTS = max(1, args.max_log_stream_clients)
    MAX_HEALTH_STREAM_CLIENTS = max(1, args.max_health_stream_clients)

    # Load persisted metrics and start flush thread
    _load_metrics_from_disk()
    _start_metrics_flush_thread()

    # Print banner
    print(BANNER.format(version=__version__))
    print(f"  Workspace:  {WORKSPACE}")
    print(f"  Sessions:   {SESSIONS_DIR}")
    print(f"  Logs:       {LOG_DIR}")
    print(f"  Metrics:    {_metrics_file_path()}")
    print(f"  OTLP:       {'✅ Ready (opentelemetry-proto installed)' if _HAS_OTEL_PROTO else '❌ Not available (pip install clawmetry[otel])'}")
    print(f"  User:       {USER_NAME}")
    print(f"  Mode:       {'🛠️  Dev (auto-reload ON)' if args.debug else '🚀 Prod (auto-reload OFF)'}")
    print(f"  SSE Limits: {SSE_MAX_SECONDS}s max duration · logs {MAX_LOG_STREAM_CLIENTS} clients · health {MAX_HEALTH_STREAM_CLIENTS} clients")
    print()

    # Validate configuration and show warnings/tips for new users
    warnings, tips = validate_configuration()
    if warnings or tips:
        print("🔍 Configuration Check:")
        for warning in warnings:
            print(f"  {warning}")
        for tip in tips:
            print(f"  {tip}")
        print()
        if warnings:
            print("💡 The dashboard will work with limited functionality. See tips above for full experience.")
            print()

    local_ip = get_local_ip()
    public_ip = get_public_ip()
    print(f"  → http://localhost:{args.port}")
    if local_ip != '127.0.0.1':
        print(f"  → http://{local_ip}:{args.port}  (LAN)")
    if public_ip and public_ip != local_ip:
        print(f"  → http://{public_ip}:{args.port}  (Public - ensure port is open)")
    if _HAS_OTEL_PROTO:
        print(f"  → OTLP endpoint: http://{local_ip}:{args.port}/v1/metrics")
    print()

    app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=args.debug, threaded=True)


if __name__ == '__main__':
    main()
