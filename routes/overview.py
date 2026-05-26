"""
routes/overview.py — Main-dashboard endpoints.

Extracted from dashboard.py as Phase 5.8 of the incremental modularisation.
Owns the 6 routes registered on ``bp_overview``:

  GET  /api/channels              — active input channels for Flow diagram
  GET  /api/overview              — top-bar live data (polled every 10s)
  GET  /api/timeline              — 30-day session-activity timeline
  GET  /api/cloud-cta/status      — cloud-sync CTA connected status
  POST /api/cloud-cta/send-otp    — cloud-sync CTA: send email OTP
  POST /api/cloud-cta/verify-otp  — cloud-sync CTA: verify code + store token

Module-level helpers (``_gw_invoke``, ``_get_sessions``, ``_get_crons``,
``_get_memory_files``, ``_find_log_file``, ``_infer_provider_from_model``,
``_read_cloud_token``, ``_write_cloud_token``, ``get_local_ip``,
``SESSIONS_DIR``, ``MEMORY_DIR``, ``USER_NAME``) stay in ``dashboard.py``
and are reached via late ``import dashboard as _d``. Pure mechanical move
— zero behaviour change.
"""

import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time
import time as _time
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from clawmetry.config import is_local_store_read_enabled

bp_overview = Blueprint('overview', __name__)


# Default OpenClaw heartbeat cadence (30 min). Surfaced in /api/overview's
# `heartbeat` block so the dashboard can compare to actual gap.
_HEARTBEAT_EXPECTED_SECONDS = 1800

# 30s cache for the heartbeat block. Computing it scans DuckDB and is cheap
# (~ms), but /api/overview fires on every refresh and we don't need fresher
# than once-per-30s liveness data.
_HEARTBEAT_CACHE_TTL = 30.0
_heartbeat_cache: dict = {"ts": 0.0, "value": None}
_heartbeat_cache_lock = threading.Lock()


def _parse_iso_to_epoch(ts_str):
    """ISO-8601 string → Unix float. Returns 0.0 on any parse failure."""
    if not ts_str or not isinstance(ts_str, str):
        return 0.0
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _classify_heartbeat_outcome(ev_data):
    """Return ``"ok"`` if the heartbeat event ended with a HEARTBEAT_OK reply,
    ``"action"`` if any other content was produced.

    The OpenClaw heartbeat replies exactly ``HEARTBEAT_OK`` when nothing needs
    attention; anything else means the agent took action. We look for the
    canonical marker in a few common shape variants so we don't miss either
    the gateway-emitted event shape or the sync-relayed one.
    """
    if not isinstance(ev_data, dict):
        return "action"

    # Direct flags / classifier from upstream — honour first.
    if ev_data.get("heartbeat_ok") is True:
        return "ok"
    if ev_data.get("outcome") in ("ok", "action"):
        return ev_data["outcome"]

    # Scan likely text fields for the literal marker.
    candidates = []
    for key in ("response", "reply", "assistant_text", "content", "text", "body"):
        v = ev_data.get(key)
        if isinstance(v, str):
            candidates.append(v)
        elif isinstance(v, list):
            for blk in v:
                if isinstance(blk, str):
                    candidates.append(blk)
                elif isinstance(blk, dict):
                    t = blk.get("text") or blk.get("content")
                    if isinstance(t, str):
                        candidates.append(t)
    for txt in candidates:
        if txt.strip() == "HEARTBEAT_OK":
            return "ok"
    return "action"


def _is_heartbeat_event(ev):
    """Heuristic: the event came from a heartbeat session.

    The OpenClaw gateway tags heartbeat sessions with ``session_type ==
    "heartbeat"`` somewhere on the payload; older shapes embed the type in
    the session_id or event_type. We check all of these so we capture
    heartbeats regardless of how the upstream tagged them.
    """
    data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
    if (data.get("session_type") or "").lower() == "heartbeat":
        return True
    if (ev.get("event_type") or "").lower() == "heartbeat":
        return True
    sid = (ev.get("session_id") or "").lower()
    if "heartbeat" in sid:
        return True
    return False


def _compute_overview_heartbeat(now=None, expected_seconds=_HEARTBEAT_EXPECTED_SECONDS):
    """Build the `heartbeat` block for /api/overview from DuckDB.

    Returns a dict with:
      expected_cadence_seconds — the configured cadence (default 1800)
      last_heartbeat_ts        — ISO-8601 UTC of most recent heartbeat or None
      gap_seconds              — seconds since last heartbeat (None if never)
      ok_ratio                 — of last 20 heartbeats, fraction that were
                                 HEARTBEAT_OK (vs action taken). None if no
                                 heartbeats observed.
      sample_size              — how many heartbeats fed the ratio (≤20)
      status                   — "green"  if gap < 1.5×expected
                                 "amber"  if 1.5×–3×
                                 "red"    if >3×
                                 None     if no heartbeats observed

    Source priority:
      1. `events` table — OpenClaw gateway heartbeat *sessions* (replies
         with HEARTBEAT_OK / action). Carries the OK-ratio signal.
      2. `heartbeats` table — sync-daemon liveness pings (one per
         interval). No OK-ratio (every row is "alive"), but proves the
         agent is reachable. This is the only signal when the gateway
         isn't running but the daemon is — which is the common case for
         Cloud-Free / OSS users post-install (regression #1228: dashboard
         showed `sample_size: 0` despite hundreds of fresh daemon pings).
    """
    if now is None:
        now = _time.time()

    out = {
        "expected_cadence_seconds": int(expected_seconds),
        "last_heartbeat_ts": None,
        "gap_seconds": None,
        "ok_ratio": None,
        "sample_size": 0,
        "status": None,
    }

    # Read events from DuckDB. Pull a generous window (200) and filter
    # client-side — there is no SQL filter on data.session_type today, and
    # heartbeats are sparse (~48/day) so 200 covers >4 days.
    #
    # Cross-process safety (#1228): the sync daemon owns DuckDB's
    # exclusive lock, which blocks even RO opens cross-process. Route
    # through the daemon's local_query proxy first; fall back to direct
    # RO open in single-process / dev mode.
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon(
            "query_events", agent_id="main", limit=200,
        )
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_events(agent_id="main", limit=200)
        except Exception:
            rows = []

    heartbeats = []
    for ev in (rows or []):
        if not _is_heartbeat_event(ev):
            continue
        ts_epoch = _parse_iso_to_epoch(ev.get("ts"))
        if ts_epoch <= 0:
            continue
        outcome = _classify_heartbeat_outcome(ev.get("data"))
        heartbeats.append({"ts": ts_epoch, "outcome": outcome})

    # Fallback: if no gateway-heartbeat events found, read sync-daemon
    # liveness rows from the dedicated `heartbeats` table. These don't
    # carry an OK/action outcome (the daemon only writes when alive), so
    # ok_ratio stays None — but `last_heartbeat_ts`, `gap_seconds`, and
    # `status` populate correctly, which is what the UI cares about.
    if not heartbeats:
        hb_rows = None
        try:
            from routes.local_query import local_store_via_daemon
            hb_rows = local_store_via_daemon("query_heartbeats", limit=20)
        except Exception:
            hb_rows = None
        if hb_rows is None:
            try:
                from clawmetry import local_store
                store = local_store.get_store(read_only=True)
                hb_rows = store.query_heartbeats(limit=20)
            except Exception:
                hb_rows = []
        for hb in (hb_rows or []):
            ts_epoch = _parse_iso_to_epoch(hb.get("ts"))
            if ts_epoch <= 0:
                continue
            # No outcome signal — leave ok_ratio None (sentinel).
            heartbeats.append({"ts": ts_epoch, "outcome": None})

    if not heartbeats:
        return out

    # Most recent first.
    heartbeats.sort(key=lambda h: h["ts"], reverse=True)

    last_ts = heartbeats[0]["ts"]
    gap = max(0.0, now - last_ts)

    last_20 = heartbeats[:20]
    classified = [h for h in last_20 if h["outcome"] in ("ok", "action")]
    if classified:
        ok_count = sum(1 for h in classified if h["outcome"] == "ok")
        ratio = round(ok_count / len(classified), 3)
    else:
        # All sync-daemon liveness rows — no OK/action signal available.
        ratio = None

    if gap < 1.5 * expected_seconds:
        status = "green"
    elif gap < 3.0 * expected_seconds:
        status = "amber"
    else:
        status = "red"

    from datetime import timezone as _tz
    out["last_heartbeat_ts"] = datetime.fromtimestamp(last_ts, tz=_tz.utc).isoformat()
    out["gap_seconds"] = int(gap)
    out["ok_ratio"] = ratio
    out["sample_size"] = len(last_20)
    out["status"] = status
    return out


def _get_overview_heartbeat_cached():
    """30s memoised wrapper around ``_compute_overview_heartbeat``.

    /api/overview is on the dashboard's hot path (fires on every refresh).
    Heartbeats fire every 30 min, so caching for 30s loses zero fidelity
    while avoiding repeated DuckDB scans across rapid refreshes.
    """
    now_mono = _time.monotonic()
    with _heartbeat_cache_lock:
        cached = _heartbeat_cache["value"]
        if cached is not None and (now_mono - _heartbeat_cache["ts"]) < _HEARTBEAT_CACHE_TTL:
            return cached
    # Compute outside the lock — it can hit DuckDB.
    fresh = _compute_overview_heartbeat()
    with _heartbeat_cache_lock:
        _heartbeat_cache["value"] = fresh
        _heartbeat_cache["ts"] = now_mono
    return fresh


# Issue #556: detect users still on Anthropic Claude.ai OAuth tokens
# (`sk-ant-oat-...`) and prompt migration to API keys (`sk-ant-api-...`).
# OAuth tokens have lower rate limits and different pricing, so flagging
# them in the dashboard is a high-leverage nudge.
_OAUTH_PREFIX = "sk-ant-oat"
_API_KEY_PREFIX = "sk-ant-api"
# Match an OAuth-token bearer inside an Authorization header. Tolerates
# arbitrary punctuation between the header name and value so it works on
# both raw HTTP dumps (``Authorization: Bearer …``) and JSON-encoded payloads
# (``"Authorization": "Bearer …"``). Header name is case-insensitive; the
# bearer prefix itself is always lowercase.
_OAUTH_BEARER_RE = re.compile(
    r"authorization\W+bearer\W+sk-ant-oat[-_a-z0-9]*",
    re.IGNORECASE,
)


def _detect_anthropic_oauth(limit=50):
    """Scan the most recent events for evidence of an Anthropic OAuth token
    (``sk-ant-oat...``) being used instead of an API key (``sk-ant-api...``).

    Two signals, in order of preference:

    1. ``data.api_key_prefix`` — an explicit field some interceptors emit.
       Values starting with ``sk-ant-oat`` are an unambiguous OAuth hit;
       ``sk-ant-api`` is an unambiguous API-key hit.
    2. A raw ``Authorization: Bearer sk-ant-oat...`` substring anywhere in
       the event payload (covers captured HTTP request dumps).

    Returns ``{"using_oauth": bool, "last_seen_ts": <iso8601 or None>}``.

    Safe to call even when the local store is unreachable — returns
    ``using_oauth=False`` on any error instead of raising.
    """
    result = {"using_oauth": False, "last_seen_ts": None}

    # Read events from the daemon-proxied store first (standard install).
    # Only fall back to direct local-process open when the proxy returns
    # None (daemon down / single-process dev mode). Calling BOTH on every
    # /api/overview was the dominant source of dashboard slowness pre-#1228:
    # the direct RO open burns DuckDB's ~2.5s lock-retry budget on every
    # request when the daemon owns the writer lock cross-process.
    rows: list = []
    daemon_hit = False
    try:
        from routes.local_query import local_store_via_daemon
        d = local_store_via_daemon("query_events", limit=int(limit))
        if d is not None:
            daemon_hit = True
            rows.extend(d)
    except Exception:
        pass
    if not daemon_hit:
        try:
            from clawmetry import local_store
            direct = local_store.get_store(read_only=True).query_events(
                limit=int(limit)
            )
            if direct:
                rows.extend(direct)
        except Exception:
            pass
    if not rows:
        return result

    for ev in rows:
        data = ev.get("data") if isinstance(ev, dict) else None
        prefix = None
        if isinstance(data, dict):
            prefix = data.get("api_key_prefix") or data.get("apiKeyPrefix")
        if isinstance(prefix, str):
            p = prefix.strip().lower()
            if p.startswith(_OAUTH_PREFIX):
                result["using_oauth"] = True
                result["last_seen_ts"] = ev.get("ts") or result["last_seen_ts"]
                return result
            if p.startswith(_API_KEY_PREFIX):
                # Explicit API-key prefix — strong negative signal; keep scanning
                # in case an earlier event used OAuth, but don't flag from this row.
                continue
        # Fall back to scanning the JSON-serialised payload for a bearer.
        try:
            blob = json.dumps(data) if data is not None else ""
        except Exception:
            blob = str(data)
        if _OAUTH_BEARER_RE.search(blob):
            result["using_oauth"] = True
            result["last_seen_ts"] = ev.get("ts") or result["last_seen_ts"]
            return result

    return result


# ── Autonomy score (issue #688) ─────────────────────────────────────────────
#
# Surface a north-star metric on /api/overview so the dashboard can show a
# primary KPI card (above cost). Sourced entirely from the v3 OpenClaw parser's
# ``prompt.submitted`` events in the local DuckDB store — every event of that
# type maps 1:1 to a human turn.
#
# Shape (top-level field on /api/overview response):
#   "autonomy": {
#       "median_gap_seconds": <float|null>,  # median seconds between user
#                                              turns within a session (7d)
#       "autonomy_ratio":     <float 0-1>,    # share of sessions completed
#                                              with <=1 user turn (7d)
#       "trend_pct":          <float>,        # last-7d median vs prior-7d
#                                              median, positive = improving
#       "sample_size_7d":     <int>,          # total user-turn events seen
#   }
#
# Cached in-process for 60s — it's an analytic over up to ~14 days of events,
# not a hot read. If the store is unreachable or empty we return the canonical
# "no data" payload (median_gap_seconds=null, ratio=0, trend_pct=0, samples=0)
# rather than omit the field — the UI can render the placeholder unconditionally.

_AUTONOMY_OVERVIEW_CACHE = {"ts": 0.0, "data": None}
_AUTONOMY_OVERVIEW_CACHE_TTL = 60.0  # seconds


def _autonomy_empty() -> dict:
    return {
        "median_gap_seconds": None,
        "autonomy_ratio": 0.0,
        "trend_pct": 0.0,
        "sample_size_7d": 0,
    }


def _ls_call_autonomy(method_name: str, **kwargs):
    """Cross-process LocalStore call for the autonomy helper.

    Mirrors the pattern in ``_ls_call`` below — tries the daemon HTTP proxy
    first (covers the standard launchd/systemd install where the daemon owns
    the DuckDB writer lock), then falls back to a direct ``get_store()`` open
    for single-process boots (tests + dev mode).
    """
    try:
        from routes.local_query import local_store_via_daemon
        r = local_store_via_daemon(method_name, **kwargs)
        if r is not None:
            return r
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _compute_autonomy_overview() -> dict:
    """Compute the 4-field autonomy block from ``prompt.submitted`` events.

    Pulls the last 14 days of user-turn events from DuckDB (need 14d so we
    can compare current-7d median against prior-7d for the trend %), buckets
    by session_id, computes consecutive gaps in seconds, takes the median,
    and counts "one nudge" sessions (sessions with <=1 user turn = the agent
    finished without further human input).

    Always returns a dict — never raises. On any error or empty data set,
    returns ``_autonomy_empty()`` so the UI can render the placeholder card.
    """
    now = datetime.now(tz=timezone.utc)
    cutoff_14d_iso = (now - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    cutoff_7d_ts = (now - timedelta(days=7)).timestamp()
    cutoff_14d_ts = (now - timedelta(days=14)).timestamp()

    rows = _ls_call_autonomy(
        "query_events",
        event_type="prompt.submitted",
        since=cutoff_14d_iso,
        limit=5000,
    )
    if not rows:
        return _autonomy_empty()

    # session_id → [ts_unix, ts_unix, ...] sorted ascending. We collect ALL
    # 14d events so we can compute both the 7d window (current) and the
    # 7-14d window (prior) from the same scan.
    by_session_7d: dict = {}
    by_session_prior: dict = {}

    for r in rows:
        ts_str = r.get("ts") or ""
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
        except Exception:
            continue
        sid = r.get("session_id") or ""
        if ts >= cutoff_7d_ts:
            by_session_7d.setdefault(sid, []).append(ts)
        elif ts >= cutoff_14d_ts:
            by_session_prior.setdefault(sid, []).append(ts)

    def _stats(by_session):
        """Return (median_gap_seconds_or_None, ratio_one_nudge, total_msgs,
        total_sessions) for the per-session bucket."""
        all_gaps: list = []
        one_nudge = 0
        total_msgs = 0
        total_sessions = 0
        for stamps in by_session.values():
            if not stamps:
                continue
            stamps.sort()
            total_sessions += 1
            total_msgs += len(stamps)
            if len(stamps) <= 1:
                one_nudge += 1
            for i in range(len(stamps) - 1):
                d = stamps[i + 1] - stamps[i]
                if d > 0:
                    all_gaps.append(d)
        med = statistics.median(all_gaps) if all_gaps else None
        ratio = (one_nudge / total_sessions) if total_sessions else 0.0
        return med, ratio, total_msgs, total_sessions

    med_7d, ratio_7d, msgs_7d, sess_7d = _stats(by_session_7d)
    med_prior, _, _, _ = _stats(by_session_prior)

    # trend_pct: positive when current 7d median > prior-7d median (gaps
    # growing → user nudging less often → more autonomous). Expressed as a
    # percentage delta. Zero when either window has no data (we can't claim
    # improvement without something to compare against).
    if med_7d is not None and med_prior is not None and med_prior > 0:
        trend_pct = ((med_7d - med_prior) / med_prior) * 100.0
    else:
        trend_pct = 0.0

    if sess_7d == 0 and msgs_7d == 0:
        return _autonomy_empty()

    return {
        "median_gap_seconds": float(med_7d) if med_7d is not None else None,
        "autonomy_ratio": float(ratio_7d),
        "trend_pct": round(float(trend_pct), 2),
        "sample_size_7d": int(msgs_7d),
    }


def _autonomy_for_overview() -> dict:
    """Cached wrapper around ``_compute_autonomy_overview``.

    60s TTL — the metric is over a 7d window, so sub-minute freshness is
    pointless and the cost of the scan would dominate the /api/overview
    response time on busy nodes.
    """
    now = time.monotonic()
    cached = _AUTONOMY_OVERVIEW_CACHE.get("data")
    cached_ts = float(_AUTONOMY_OVERVIEW_CACHE.get("ts") or 0.0)
    if cached is not None and (now - cached_ts) < _AUTONOMY_OVERVIEW_CACHE_TTL:
        return cached
    try:
        data = _compute_autonomy_overview()
    except Exception:
        data = _autonomy_empty()
    _AUTONOMY_OVERVIEW_CACHE["data"] = data
    _AUTONOMY_OVERVIEW_CACHE["ts"] = now
    return data


@bp_overview.route("/api/channels")
def api_channels():
    """Return active input channels for the Flow diagram.

    Includes:
    - `tui` (always — the CLI is always available)
    - configured delivery channels from openclaw.json / gateway.yaml
    - `webchat` if recent activity in gateway.log (control UI counts as input)

    Previously fell back to a hardcoded ['telegram', 'signal', 'whatsapp']
    list when nothing was detected — which displayed fake channels for users
    who hadn't configured any. Removed.
    """
    KNOWN_CHANNELS = (
        "tui",
        "telegram",
        "signal",
        "whatsapp",
        "discord",
        "webchat",
        "imessage",
        "irc",
        "slack",
        "googlechat",
        "bluebubbles",
        "matrix",
        "mattermost",
        "msteams",
        "line",
        "nostr",
        "twitch",
        "feishu",
        "synology-chat",
        "nextcloud-talk",
        "tlon",
        "zalo",
        "zalouser",
    )
    configured = []

    def _add(name):
        n = name.lower()
        if n in KNOWN_CHANNELS and n not in configured:
            configured.append(n)

    # 1. Check gateway.yaml / gateway.yml (OpenClaw gateway config)
    yaml_candidates = [
        os.path.expanduser("~/.openclaw/gateway.yaml"),
        os.path.expanduser("~/.openclaw/gateway.yml"),
        os.path.expanduser("~/.clawdbot/gateway.yaml"),
        os.path.expanduser("~/.clawdbot/gateway.yml"),
    ]
    for yf in yaml_candidates:
        try:
            import yaml as _yaml

            with open(yf) as f:
                ydata = _yaml.safe_load(f)
            if not isinstance(ydata, dict):
                continue
            # channels: or plugins: section
            for section_key in ("channels", "plugins"):
                section = ydata.get(section_key, {})
                if isinstance(section, dict):
                    for name, conf in section.items():
                        if isinstance(conf, dict) and conf.get("enabled", True):
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
            os.path.expanduser("~/.openclaw/openclaw.json"),
            os.path.expanduser("~/.clawdbot/openclaw.json"),
            os.path.expanduser("~/.clawdbot/clawdbot.json"),
            os.path.expanduser("~/.clawdbot/moltbot.json"),
        ]
        for cf in config_files:
            try:
                with open(cf) as f:
                    data = json.load(f)
                # Check plugins.entries for enabled channels
                plugins = data.get("plugins", {}).get("entries", {})
                for name, pconf in plugins.items():
                    if isinstance(pconf, dict) and pconf.get("enabled"):
                        _add(name)
                # Also check channels key
                channels = data.get("channels", {})
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
    # Some channels (like imessage) use system paths, not openclaw dirs -- skip dir check for those
    DIR_EXEMPT_CHANNELS = {
        "imessage",
        "irc",
        "googlechat",
        "slack",
        "webchat",
        "bluebubbles",
        "matrix",
        "mattermost",
        "msteams",
        "line",
        "nostr",
        "twitch",
        "feishu",
        "synology-chat",
        "nextcloud-talk",
        "tlon",
        "zalo",
        "zalouser",
    }
    if configured:
        active_channels = []
        oc_dir = os.path.expanduser("~/.openclaw")
        cb_dir = os.path.expanduser("~/.clawdbot")
        for ch in configured:
            if ch in DIR_EXEMPT_CHANNELS:
                active_channels.append(ch)
            elif any(os.path.isdir(os.path.join(d, ch)) for d in [oc_dir, cb_dir]):
                active_channels.append(ch)
        if active_channels:
            configured = active_channels

    # TUI is always available (it's the CLI) — pin it to the front so the
    # Flow diagram reflects that the user can always reach the agent that way.
    if "tui" not in configured:
        configured.insert(0, "tui")

    # Surface webchat if the OpenClaw control-UI has recent activity. Looking
    # for "webchat connected" in the rolling gateway.log catches the case
    # where the user is using the OpenClaw control UI but hasn't configured
    # webchat as a formal channel.
    try:
        gw_log_paths = [
            os.path.expanduser("~/.openclaw/logs/gateway.log"),
            os.path.expanduser("~/.openclaw-dev/logs/gateway.log"),
        ]
        gw_log = next((p for p in gw_log_paths if os.path.isfile(p)), None)
        if gw_log:
            today = datetime.now().strftime("%Y-%m-%d")
            with open(gw_log) as _wf:
                for line in _wf:
                    if today in line and "webchat connected" in line:
                        if "webchat" not in configured:
                            configured.append("webchat")
                        break
    except Exception:
        pass

    return jsonify({"channels": configured})


# ── Gateway-tap opt-in comms (issue #1233) ─────────────────────────────────
#
# PR #1228 flipped the live WS gateway tap (clawmetry/gateway_tap.py) from
# default-ON to default-OFF for the OpenClaw scope-grant transition. Users
# who previously relied on the tap for inbound channel-message bodies
# (Telegram, Signal, WhatsApp, Discord, ...) now silently see no new rows.
#
# We detect the gap from DuckDB: 1+ channel_messages in the prior 7d window
# AND zero in the last 24h AND the tap env var is not enabled. If all three
# hold, /api/overview piggybacks a one-line ``_comms.show_gateway_tap_banner``
# flag so the dashboard frontend can render a dismissible "Channel watch is
# now opt-in — enable in Settings, or upgrade to Pro for defaults" banner.
#
# Cached for 5 min so the dashboard's hot 10s refresh doesn't re-query the
# store for slow-moving state. Always degrades to ``show=False`` on error
# (no banner is the safe default — never block the dashboard render).
_GATEWAY_TAP_COMMS_CACHE = {"ts": 0.0, "value": None}
_GATEWAY_TAP_COMMS_TTL = 300.0  # 5 min


def _compute_gateway_tap_comms() -> dict:
    """Return ``{"show_gateway_tap_banner": bool, "show_pro_cta": bool}``.

    Heuristic for ``show_gateway_tap_banner``:
      * The ``CLAWMETRY_ENABLE_WS_TAP`` env var is NOT set (i.e. user is on
        the post-#1228 default-OFF path).
      * The DuckDB ``channel_messages`` table has >=1 row in the
        ``[now-7d, now-24h]`` window (proves the user previously got tap
        data — they're impacted, not a fresh install).
      * The DuckDB ``channel_messages`` table has 0 rows in the last 24h
        (proves the gap is currently active — not a stale historical row).

    ``show_pro_cta`` adds a "Pro defaults this on" hint when the user is not
    already on Pro. Both flags default to ``False`` on any failure.
    """
    now = time.time()
    cached = _GATEWAY_TAP_COMMS_CACHE.get("value")
    if cached is not None and (now - _GATEWAY_TAP_COMMS_CACHE["ts"]) < _GATEWAY_TAP_COMMS_TTL:
        return cached

    out = {"show_gateway_tap_banner": False, "show_pro_cta": False}
    try:
        # Tap already opted-in? Nothing to nag about.
        if os.environ.get("CLAWMETRY_ENABLE_WS_TAP", "").strip() in ("1", "true", "yes"):
            _GATEWAY_TAP_COMMS_CACHE.update(ts=now, value=out)
            return out

        # Prior-7d activity (any inbound or outbound channel row).
        seven_d_iso = datetime.fromtimestamp(now - 7 * 86400, tz=timezone.utc).isoformat()
        prior = _ls_call("query_channel_messages", since=seven_d_iso, limit=1)
        if not prior:
            _GATEWAY_TAP_COMMS_CACHE.update(ts=now, value=out)
            return out

        # Last-24h activity. If we see ANY row, the tap isn't the gap.
        one_d_iso = datetime.fromtimestamp(now - 86400, tz=timezone.utc).isoformat()
        recent = _ls_call("query_channel_messages", since=one_d_iso, limit=1)
        if recent:
            _GATEWAY_TAP_COMMS_CACHE.update(ts=now, value=out)
            return out

        out["show_gateway_tap_banner"] = True

        # Pro CTA — same pattern as routes/alerts.py.
        try:
            import dashboard as _d
            is_pro = bool(_d._is_pro_user())
        except Exception:
            is_pro = False
        out["show_pro_cta"] = not is_pro
    except Exception:
        # Never let comms compute break the overview render.
        out = {"show_gateway_tap_banner": False, "show_pro_cta": False}

    _GATEWAY_TAP_COMMS_CACHE.update(ts=now, value=out)
    return out


# ── LLM Context Inspector parity helpers (issue: OSS↔cloud mismatch) ──────
# The Context tab on OSS and on app.clawmetry.com used to disagree because
# they computed Context Window Usage and Skills from different sources
# (OSS hit /api/overview.mainTokens + /api/skills; cloud read the snapshot's
# top-level mainTokens and had no /api/skills route → 410 Gone).
# These two helpers compute the new shared fields (currentContextTokens,
# skillHeaderTokens) that both /api/overview and the daemon snapshot now
# expose so the Context tab reads one value on both sides.

def _try_local_store_context_peek():
    """Full context-window peek for the user's most-recent assistant turn.

    Returns ``{"input_tokens": int, "context_window": int}`` (other keys
    from ``query_context_window_peek`` may be present). ``exclude_clawmetry``
    is pinned True so the gauge tracks the user's agent, not ClawMetry's own
    plumbing. ``context_window`` is sized from the turn's model + observed
    size so a 1M-context session (≈323K live) reads against a 1M window
    instead of the old hardcoded 200K (which showed ">100%"). Returns an
    empty dict on any miss so callers fall back to defaults.
    """
    try:
        from routes.local_query import local_store_via_daemon
        peek = local_store_via_daemon(
            "query_context_window_peek", scan_sessions=5, exclude_clawmetry=True,
        )
    except Exception:
        peek = None
    if peek is None:
        try:
            from clawmetry import local_store
            peek = local_store.get_store(read_only=True).query_context_window_peek(
                scan_sessions=5, exclude_clawmetry=True,
            )
        except Exception:
            return {}
    return peek if isinstance(peek, dict) else {}


def _try_local_store_current_context_tokens():
    """Live prompt size (int) for the user's most-recent assistant turn.

    Thin wrapper over :func:`_try_local_store_context_peek` kept for
    backwards compatibility. Returns 0 on any miss — the frontend then
    falls back to mainTokens.
    """
    try:
        return int((_try_local_store_context_peek() or {}).get("input_tokens") or 0)
    except Exception:
        return 0


def _compute_skill_header_tokens():
    """Sum of header tokens for all installed skills.

    Reuses ``routes.skills.compute_skills_payload`` (the same source
    /api/skills serves) so OSS and the daemon snapshot agree on the
    number rendered by the LLM Context Inspector's ``## Skills`` bar.
    Returns 0 if the helper raises — we never fail the overview render
    on a missing skill catalogue.
    """
    try:
        from routes.skills import compute_skills_payload
        payload = compute_skills_payload() or {}
        return int((payload.get("summary") or {}).get("total_header_tokens") or 0)
    except Exception:
        return 0


def _try_local_store_overview():
    """Epic #964: opt-in local-store fast path for /api/overview.

    Builds the same response shape as the legacy gateway-backed handler from
    DuckDB: session counts (from query_sessions), most-recently-active session
    metadata (model, tokens, updatedAt) — all derivable from
    ``query_sessions`` + ``query_aggregates`` + ``query_events``.

    System-info and infra blocks still come from local subprocesses; the fast
    path only replaces the gateway-dependent fields (model, sessionCount,
    activeSessions, mainSessionUpdated, mainTokens). Cron + memory counts
    intentionally stay on their existing helpers (they hit the filesystem
    directly and are already <5ms).

    Returns ``None`` to defer to the legacy handler if:
      - the local_store module isn't importable
      - the sessions table is empty (fresh install / non-OpenClaw user)
      - any unexpected error happens (we'd rather degrade than 500)
    """
    import subprocess as _sub
    import sys as _sys
    # Issue #1088: cross-process fast path. Try the daemon HTTP proxy first
    # (covers the standard launchd/systemd install where DuckDB's writer lock
    # blocks the dashboard from opening directly), then fall back to direct
    # open for tests + dev mode.
    sess_rows = None
    try:
        from routes.local_query import local_store_via_daemon
        sess_rows = local_store_via_daemon("query_sessions_table", limit=200)
    except Exception:
        sess_rows = None
    if sess_rows is None:
        try:
            from clawmetry import local_store
            sess_rows = local_store.get_store(read_only=True).query_sessions_table(limit=200)
        except Exception:
            return None
    if not sess_rows:
        return None

    # Build a normalized view of sessions.
    sessions = []
    for r in sess_rows:
        meta = r.get("metadata") or {}
        sessions.append({
            "session_id": r.get("session_id"),
            "agent_id": r.get("agent_id"),
            "title": r.get("title") or "",
            "started_at": r.get("started_at") or "",
            "last_active_at": r.get("last_active_at") or "",
            "ended_at": r.get("ended_at") or "",
            "status": (r.get("status") or "").lower(),
            "total_tokens": int(r.get("total_tokens") or 0),
            "cost_usd": float(r.get("cost_usd") or 0.0),
            "message_count": int(r.get("message_count") or 0),
            "model": meta.get("model"),
        })

    # Pick the user's main session — first non-subagent, non-ClawMetry-
    # internal session in the most-recently-active-first order from
    # query_sessions_table (`ORDER BY last_active_at DESC`).
    #
    # Without the ClawMetry filter OSS surfaced clawmetry-selfevolve /
    # clawmetry-fix plumbing sessions as "main" — e.g. it reported the
    # 204K cumulative tokens of a SelfEvolve run as the user's main
    # session while the cloud snapshot (which already filters them at
    # clawmetry/sync.py:9167) reported the real ~38K. Bug surfaced
    # 2026-05-23.
    from clawmetry.config import hide_clawmetry_session
    def _is_subagent(s):
        sid = (s.get("session_id") or "").lower()
        return "subagent" in sid or "sub-agent" in sid
    def _is_user_main(s):
        sid = s.get("session_id") or ""
        return not _is_subagent(s) and not hide_clawmetry_session(sid)
    user_sessions = [s for s in sessions if _is_user_main(s)]
    main = user_sessions[0] if user_sessions else sessions[0]

    # Active = status=='active' (DuckDB persists status as a free-form string;
    # 'active' is what sync.py writes for in-progress sessions).
    active_count = sum(1 for s in sessions if s["status"] == "active")

    # Model: prefer metadata.model on the main session; fall back to the most
    # recently observed model across events.
    model_name = main.get("model") or "unknown"
    if model_name == "unknown":
        evs = None
        try:
            from routes.local_query import local_store_via_daemon
            evs = local_store_via_daemon("query_events", limit=20)
        except Exception:
            evs = None
        if evs is None:
            try:
                from clawmetry import local_store
                evs = local_store.get_store(read_only=True).query_events(limit=20)
            except Exception:
                evs = []
        for e in (evs or []):
            m = e.get("model")
            if m:
                model_name = m
                break

    # Pull the latest cron + memory totals using the existing dashboard
    # helpers. They're already filesystem-backed and fast — and they read
    # from canonical sources (the gateway / .openclaw memory dir) that the
    # local store doesn't replicate. We still want the fast path to be 100%
    # local-only, so we wrap them in try/except so a missing FS doesn't break
    # the response.
    import dashboard as _d
    try:
        crons = _d._get_crons()
    except Exception:
        crons = []
    enabled = len([j for j in crons if j.get("enabled")])
    disabled = len(crons) - enabled
    try:
        mem_files = _d._get_memory_files()
    except Exception:
        mem_files = []
    total_size = sum(f.get("size", 0) for f in mem_files)

    # System info — copied verbatim from the legacy handler so the response
    # shape matches byte-for-byte. Each subprocess has a 2s timeout so a slow
    # df/free/uptime can't hang the request thread.
    system = []
    try:
        disk = (
            _sub.run(["df", "-h", "/"], capture_output=True, text=True, timeout=2)
            .stdout.strip().split("\n")[-1].split()
        )
        disk_pct = int(disk[4].replace("%", "")) if len(disk) > 4 else 0
        disk_color = "green" if disk_pct < 80 else ("yellow" if disk_pct < 90 else "red")
        system.append(["Disk /", f"{disk[2]} / {disk[1]} ({disk[4]})", disk_color])
    except Exception:
        system.append(["Disk /", "--", ""])

    try:
        mem = (
            _sub.run(["free", "-h"], capture_output=True, text=True, timeout=2)
            .stdout.strip().split("\n")[1].split()
        )
        system.append(["RAM", f"{mem[2]} / {mem[1]}", ""])
    except Exception:
        system.append(["RAM", "--", ""])

    try:
        load = open("/proc/loadavg").read().split()[:3]
        system.append(["Load", " ".join(load), ""])
    except Exception:
        system.append(["Load", "--", ""])

    try:
        # Portable: GNU `uptime -p` doesn't exist on macOS / BSD.
        from helpers.system import uptime_pretty

        uptime = uptime_pretty()
        system.append([
            "Uptime",
            uptime.replace("up ", "") if uptime != "unknown" else "--",
            "",
        ])
    except Exception:
        system.append(["Uptime", "--", ""])

    if _sys.platform != "win32":
        try:
            gw = _sub.run(
                ["pgrep", "-f", "moltbot"], capture_output=True, text=True, timeout=2
            )
            gw_running = gw.returncode == 0
        except Exception:
            gw_running = False
    else:
        gw_running = False
    system.append([
        "Gateway",
        "Running" if gw_running else "Stopped",
        "green" if gw_running else "red",
    ])

    # Infra block — same shape as legacy.
    infra = {
        "userName": _d.USER_NAME,
        "network": _d.get_local_ip(),
    }
    try:
        import platform
        uname = platform.uname()
        infra["machine"] = uname.node
        infra["runtime"] = f"Node.js - {uname.system} {uname.release.split('-')[0]}"
    except Exception:
        infra["machine"] = "Host"
        infra["runtime"] = "Runtime"
    try:
        disk_info = (
            _sub.run(["df", "-h", "/"], capture_output=True, text=True, timeout=2)
            .stdout.strip().split("\n")[-1].split()
        )
        infra["storage"] = f"{disk_info[1]} root"
    except Exception:
        infra["storage"] = "Disk"

    # OSS/cloud parity: user-visible session count excludes sub-agents and
    # ClawMetry-internal plumbing sessions so the OSS Overview matches the
    # cloud snapshot's `sessionCount` (clawmetry/sync.py builds the same way).
    user_session_count = len(user_sessions) if user_sessions else len(sessions)

    # `currentContextTokens` is the right "Context Window Usage" gauge —
    # the most recent assistant turn's live prompt size (input + cache),
    # filtered to exclude clawmetry-* plumbing sessions. `contextWindow`
    # is sized from THAT turn's model + observed size so the gauge stays
    # coherent: a 1M-context session (≈323K live) reads against a 1M
    # window instead of the old hardcoded 200K (which showed ">100%").
    # Falls back to 0 / 200K so the frontend can degrade to mainTokens
    # for daemons without these fields.
    _ctx_peek = _try_local_store_context_peek()
    current_context_tokens = int(_ctx_peek.get("input_tokens") or 0)
    context_window = int(_ctx_peek.get("context_window") or 0) or 200000

    # `skillHeaderTokens` lets the LLM Context Inspector render the
    # "## Skills" bar from the snapshot/overview without a separate
    # /api/skills fetch (which is 410 Gone in cloud mode). Same source
    # of truth on OSS and cloud.
    skill_header_tokens = _compute_skill_header_tokens()

    return {
        "model": model_name,
        "provider": _d._infer_provider_from_model(model_name),
        "sessionCount": user_session_count,
        "sessions": user_session_count,  # alias for E2E compatibility
        "activeSessions": active_count,
        "mainSessionUpdated": main.get("last_active_at") or main.get("started_at"),
        "mainTokens": main.get("total_tokens", 0),
        "currentContextTokens": current_context_tokens or 0,
        "skillHeaderTokens": skill_header_tokens or 0,
        "contextWindow": context_window,
        "cronCount": len(crons),
        "cronEnabled": enabled,
        "cronDisabled": disabled,
        "memoryCount": len(mem_files),
        "memorySize": total_size,
        "system": system,
        "infra": infra,
        "heartbeat": _get_overview_heartbeat_cached(),
        "client_health": _detect_anthropic_oauth(),
        # Issue #688: north-star metric. Always present, even on empty data.
        "autonomy": _autonomy_for_overview(),
        # Issue #1233: opt-in nudge for users impacted by PR #1228 default-OFF flip.
        "_comms": _compute_gateway_tap_comms(),
        "_source": "local_store",
    }


@bp_overview.route("/api/overview")
def api_overview():
    import dashboard as _d

    # Epic #964: opt-in local-store fast path. When CLAWMETRY_LOCAL_STORE_READ=1
    # AND the local sessions table has rows, serve directly from DuckDB. Falls
    # through to gateway/JSONL otherwise (zero-change default).
    if is_local_store_read_enabled():
        fast = _try_local_store_overview()
        if fast is not None:
            return jsonify(fast)

    # Try gateway API for sessions
    gw_sessions = _d._gw_invoke("sessions_list", {"limit": 20, "messageLimit": 0})
    if gw_sessions and "sessions" in gw_sessions:
        sessions = gw_sessions["sessions"]
    else:
        sessions = _d._get_sessions()
    main = next(
        (
            s
            for s in sessions
            if "subagent" not in (s.get("key", s.get("sessionId", "")).lower())
        ),
        sessions[0] if sessions else {},
    )

    crons = _d._get_crons()
    enabled = len([j for j in crons if j.get("enabled")])
    disabled = len(crons) - enabled

    mem_files = _d._get_memory_files()
    total_size = sum(f["size"] for f in mem_files)

    # System info
    system = []
    # 2s timeout on every subprocess: on slow/NFS-backed volumes df/free/uptime
    # can hang the request thread indefinitely, and /api/overview is on the
    # dashboard's hot path (fires every refresh). Better to show "--" than hang.
    try:
        disk = (
            subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=2)
            .stdout.strip()
            .split("\n")[-1]
            .split()
        )
        disk_pct = int(disk[4].replace("%", "")) if len(disk) > 4 else 0
        disk_color = (
            "green" if disk_pct < 80 else ("yellow" if disk_pct < 90 else "red")
        )
        system.append(["Disk /", f"{disk[2]} / {disk[1]} ({disk[4]})", disk_color])
    except Exception:
        system.append(["Disk /", "--", ""])

    try:
        mem = (
            subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=2)
            .stdout.strip()
            .split("\n")[1]
            .split()
        )
        system.append(["RAM", f"{mem[2]} / {mem[1]}", ""])
    except Exception:
        system.append(["RAM", "--", ""])

    try:
        load = open("/proc/loadavg").read().split()[:3]
        system.append(["Load", " ".join(load), ""])
    except Exception:
        system.append(["Load", "--", ""])

    try:
        # Portable: GNU `uptime -p` doesn't exist on macOS / BSD.
        from helpers.system import uptime_pretty

        uptime = uptime_pretty()
        system.append([
            "Uptime",
            uptime.replace("up ", "") if uptime != "unknown" else "--",
            "",
        ])
    except Exception:
        system.append(["Uptime", "--", ""])

    if sys.platform != "win32":
        try:
            gw = subprocess.run(
                ["pgrep", "-f", "moltbot"], capture_output=True, text=True, timeout=2
            )
            gw_running = gw.returncode == 0
        except Exception:
            gw_running = False
    else:
        gw_running = False
    system.append(
        [
            "Gateway",
            "Running" if gw_running else "Stopped",
            "green" if gw_running else "red",
        ]
    )

    # Infrastructure details for Flow tab
    infra = {
        "userName": _d.USER_NAME,
        "network": _d.get_local_ip(),
    }
    try:
        import platform

        uname = platform.uname()
        infra["machine"] = uname.node
        infra["runtime"] = f"Node.js - {uname.system} {uname.release.split('-')[0]}"
    except Exception:
        infra["machine"] = "Host"
        infra["runtime"] = "Runtime"

    try:
        disk_info = (
            subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=2)
            .stdout.strip()
            .split("\n")[-1]
            .split()
        )
        infra["storage"] = f"{disk_info[1]} root"
    except Exception:
        infra["storage"] = "Disk"

    model_name = main.get("model") or "unknown"
    return jsonify(
        {
            "model": model_name,
            "provider": _d._infer_provider_from_model(model_name),
            "sessionCount": len(sessions),
            "sessions": len(sessions),  # alias for E2E compatibility
            "activeSessions": len([s for s in sessions if s.get("active")]),
            "mainSessionUpdated": main.get("updatedAt"),
            "mainTokens": main.get("totalTokens", 0),
            "contextWindow": main.get("contextTokens", 200000),
            "cronCount": len(crons),
            "cronEnabled": enabled,
            "cronDisabled": disabled,
            "memoryCount": len(mem_files),
            "memorySize": total_size,
            "system": system,
            "infra": infra,
            "heartbeat": _get_overview_heartbeat_cached(),
            "client_health": _detect_anthropic_oauth(),
            # Issue #688: north-star autonomy metric (always present).
            "autonomy": _autonomy_for_overview(),
            # Issue #1233: opt-in nudge for users impacted by PR #1228 default-OFF flip.
            "_comms": _compute_gateway_tap_comms(),
        }
    )


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback (issue #1088)."""
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _try_local_store_timeline():
    """Epic #964: opt-in local-store fast path for /api/timeline.

    The legacy handler walks 31 daily JSONL log files (one per day for the
    last 30 days), parsing every line to count events and bucket by hour.
    On busy nodes that's hundreds of MB of disk I/O on a hot path.

    ``query_aggregates`` is the perfect fit: DuckDB pre-buckets events by day
    on the columnar layout in single-digit ms even at 100k+ events. We then
    re-derive the per-hour distribution by querying ``query_events`` once per
    day with a tight window — only days that already showed activity in the
    aggregates pass actually get scanned.

    Issue #1088: routes through the daemon HTTP proxy first via ``_ls_call``,
    with the standard direct-open fallback for single-process boots.

    Returns ``None`` to defer to the JSONL fallback if:
      - neither path can reach the local store
      - query_aggregates returns empty (no events seen yet)
      - any unexpected error happens
    """
    now = datetime.now()
    cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d") + "T00:00:00"
    rows = _ls_call("query_aggregates", since=cutoff)
    if not rows:
        return None

    # Roll up per-day counts (sum across agent_ids).
    day_counts = {}
    for r in rows:
        d = r.get("day")
        if not d:
            continue
        day_counts[d] = day_counts.get(d, 0) + int(r.get("event_count", 0) or 0)

    # Build the per-hour distribution. We pull events once for each day that
    # had activity using the (since, until) window and bucket client-side.
    days = []
    import dashboard as _d
    mem_dir = getattr(_d, "MEMORY_DIR", None)
    for i in range(30, -1, -1):
        d = now - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        count = day_counts.get(ds, 0)
        hours = {}
        if count > 0:
            ev_rows = _ls_call(
                "query_events",
                since=ds + "T00:00:00",
                until=ds + "T23:59:59",
                limit=10000,
            ) or []
            for ev in ev_rows:
                ts = ev.get("ts") or ""
                if "T" in ts:
                    try:
                        h = int(ts.split("T")[1][:2])
                        hours[h] = hours.get(h, 0) + 1
                    except Exception:
                        pass
        mem_file = os.path.join(mem_dir, f"{ds}.md") if mem_dir else None
        has_memory = bool(mem_file and os.path.exists(mem_file))
        if count > 0 or has_memory:
            days.append({
                "date": ds,
                "label": d.strftime("%a %b %d"),
                "events": count,
                "hasMemory": has_memory,
                "hours": hours,
            })
    return {
        "days": days,
        "today": now.strftime("%Y-%m-%d"),
        "_source": "local_store",
    }


@bp_overview.route("/api/timeline")
def api_timeline():
    """Return available dates with activity counts for time travel."""
    import dashboard as _d

    # Epic #964: opt-in local-store fast path. When CLAWMETRY_LOCAL_STORE_READ=1
    # AND query_aggregates returns rows, serve from DuckDB. Falls through to the
    # 30-day JSONL scan otherwise (zero-change default).
    if is_local_store_read_enabled():
        fast = _try_local_store_timeline()
        if fast is not None:
            return jsonify(fast)

    now = datetime.now()
    days = []
    for i in range(30, -1, -1):
        d = now - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        log_file = _d._find_log_file(ds)
        count = 0
        hours = {}
        if log_file:
            try:
                with open(log_file) as f:
                    for line in f:
                        count += 1
                        try:
                            obj = json.loads(line.strip())
                            ts = obj.get("time") or ""
                            if "T" in ts:
                                h = int(ts.split("T")[1][:2])
                                hours[h] = hours.get(h, 0) + 1
                        except Exception:
                            pass
            except Exception:
                pass
        # Also check memory files for that date
        mem_file = os.path.join(_d.MEMORY_DIR, f"{ds}.md") if _d.MEMORY_DIR else None
        has_memory = mem_file and os.path.exists(mem_file)
        if count > 0 or has_memory:
            days.append(
                {
                    "date": ds,
                    "label": d.strftime("%a %b %d"),
                    "events": count,
                    "hasMemory": has_memory,
                    "hours": hours,
                }
            )
    return jsonify({"days": days, "today": now.strftime("%Y-%m-%d")})


def _try_local_store_prompt_errors(since_iso):
    """Fast path for /api/prompt-errors. Reads ``openclaw:prompt-error``
    events from DuckDB instead of scanning the 20 most-recent JSONL files.

    Issue #1088: tries the daemon HTTP proxy FIRST (cross-process safe under
    the standard install where the daemon owns the writer lock), then falls
    back to a direct ``get_store()`` open for single-process boots (tests +
    dev mode).

    Returns ``None`` to defer to the JSONL scan if:
      - neither path can reach the local store
      - the events table is empty / no prompt-error rows
      - any unexpected error happens (we'd rather degrade than 500)
    """
    def _fetch(event_type):
        # Cross-process: ask the daemon first.
        try:
            from routes.local_query import local_store_via_daemon
            r = local_store_via_daemon(
                "query_events",
                event_type=event_type,
                since=since_iso,
                limit=200,
            )
            if r is not None:
                return r
        except Exception:
            pass
        # Single-process fallback.
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            return store.query_events(
                event_type=event_type,
                since=since_iso,
                limit=200,
            )
        except Exception:
            return None

    # Two event_type spellings have been seen in the wild — the canonical
    # ``openclaw:prompt-error`` and the bare ``prompt-error`` from older
    # ingest paths. Try both.
    rows = _fetch("openclaw:prompt-error")
    if not rows:
        rows = _fetch("prompt-error")
    if not rows:
        return None
    errors = []
    for ev in rows:
        data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
        errors.append({
            "ts": ev.get("ts"),
            "runId": data.get("runId"),
            "sessionId": ev.get("session_id") or data.get("sessionId"),
            "provider": data.get("provider"),
            "model": ev.get("model") or data.get("model"),
            "api": data.get("api"),
            "error": data.get("error"),
        })
    errors.sort(key=lambda e: e.get("ts") or "", reverse=True)
    errors = errors[:50]
    return {"errors": errors, "count": len(errors), "_source": "local_store"}


@bp_overview.route("/api/prompt-errors")
def api_prompt_errors():
    """Return recent openclaw:prompt-error events from session JSONL files.

    Scans the 20 most-recently-modified session files so the response stays
    fast regardless of how many sessions exist.  Supports ?since=<ISO8601>
    for incremental polling by the client.
    """
    import dashboard as _d

    since_raw = request.args.get("since")
    since_ts = None
    if since_raw:
        try:
            since_ts = datetime.fromisoformat(since_raw.replace("Z", "+00:00"))
        except Exception:
            pass

    # Epic #964 — opt-in DuckDB fast path. Falls through on miss.
    if is_local_store_read_enabled():
        fast = _try_local_store_prompt_errors(since_raw)
        if fast is not None:
            return jsonify(fast)

    session_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(session_dir):
        return jsonify({"errors": [], "count": 0})

    try:
        all_files = [
            f for f in os.listdir(session_dir) if f.endswith(".jsonl")
        ]
        # Scan most-recently-modified first so we surface fresh errors quickly.
        all_files.sort(
            key=lambda f: os.path.getmtime(os.path.join(session_dir, f)),
            reverse=True,
        )
        files = all_files[:20]
    except Exception:
        return jsonify({"errors": [], "count": 0})

    errors = []
    for fname in files:
        fpath = os.path.join(session_dir, fname)
        try:
            with open(fpath, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    if obj.get("customType") != "openclaw:prompt-error":
                        continue

                    ts_raw = (
                        obj.get("timestamp")
                        or obj.get("time")
                        or obj.get("created_at")
                    )
                    if since_ts and ts_raw:
                        try:
                            ev_ts = datetime.fromisoformat(
                                str(ts_raw).replace("Z", "+00:00")
                            )
                            if ev_ts < since_ts:
                                continue
                        except Exception:
                            pass

                    # Fields may be at the top level or nested under "data".
                    data = obj.get("data") if isinstance(obj.get("data"), dict) else obj
                    errors.append(
                        {
                            "ts": ts_raw,
                            "runId": data.get("runId") or obj.get("runId"),
                            "sessionId": data.get("sessionId") or obj.get("sessionId"),
                            "provider": data.get("provider") or obj.get("provider"),
                            "model": data.get("model") or obj.get("model"),
                            "api": data.get("api") or obj.get("api"),
                            "error": data.get("error") or obj.get("error"),
                        }
                    )
        except Exception:
            continue

    errors.sort(key=lambda e: e.get("ts") or "", reverse=True)
    errors = errors[:50]
    return jsonify({"errors": errors, "count": len(errors)})


@bp_overview.route("/api/cloud-cta/status")
def cloud_cta_status():
    import dashboard as _d

    token = _d._read_cloud_token()
    return jsonify({"connected": bool(token)})


@bp_overview.route(
    "/api/cloud-proxy/<path:cloud_path>",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
def cloud_proxy(cloud_path):
    """Forward an authenticated request to https://app.clawmetry.com/<path>.

    Used by the Alerts tab (and anything else that needs cloud-side data) so
    the cm_ token never has to leave the OSS dashboard. The token is read from
    ~/.openclaw/openclaw.json.cloudToken and injected as Bearer.

    Returns 401 if no cloud token is configured (UI shows the "Sign up for
    Cloud" CTA in that case).
    """
    import dashboard as _d
    import urllib.error
    import urllib.request

    token = _d._read_cloud_token()
    if not token:
        return jsonify({"error": "cloud_not_connected"}), 401

    url = "https://app.clawmetry.com/" + cloud_path
    if request.query_string:
        url += "?" + request.query_string.decode("utf-8", errors="replace")

    body = None
    if request.method in ("POST", "PUT", "PATCH"):
        body = request.get_data() or b""

    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": request.headers.get("Content-Type", "application/json"),
        "Accept": "application/json",
    }

    req = urllib.request.Request(url, data=body, headers=headers, method=request.method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = resp.read()
            ct = resp.headers.get("Content-Type", "application/json")
            return (payload, resp.status, {"Content-Type": ct})
    except urllib.error.HTTPError as e:
        # Pass through 4xx/5xx with body so the UI can read 402 upgrade_required etc.
        return (e.read() or b"{}", e.code,
                {"Content-Type": e.headers.get("Content-Type", "application/json")})
    except Exception as e:
        return jsonify({"error": "proxy_failed", "detail": str(e)[:200]}), 502


@bp_overview.route("/api/cloud-cta/send-otp", methods=["POST"])
def cloud_cta_send_otp():
    import urllib.request as _ur
    import json as _jr

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "Invalid email"}), 400
    try:
        _body = _jr.dumps({"email": email, "source": "dashboard"}).encode()
        _req = _ur.Request(
            "https://app.clawmetry.com/api/otp/send",
            data=_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _ur.urlopen(_req, timeout=10) as _resp:
            result = _jr.loads(_resp.read())
            return jsonify({"ok": True, "error": result.get("error")})
    except Exception as _ex:
        _sc = getattr(getattr(_ex, "code", None), "__class__", type(_ex)).__name__
        try:
            _eb = _jr.loads(_ex.read()) if hasattr(_ex, "read") else {}
        except Exception:
            _eb = {}
        return jsonify(
            {"ok": False, "error": _eb.get("error", "Could not reach ClawMetry server")}
        ), 502


@bp_overview.route("/api/cloud-cta/verify-otp", methods=["POST"])
def cloud_cta_verify_otp():
    import dashboard as _d
    import urllib.request as _ur
    import json as _jr

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    code = (data.get("code") or "").strip()
    if not email or not code:
        return jsonify({"ok": False, "error": "Missing email or code"}), 400
    try:
        _body = _jr.dumps({"email": email, "code": code}).encode()
        _req = _ur.Request(
            "https://app.clawmetry.com/api/otp/verify",
            data=_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _ur.urlopen(_req, timeout=10) as _resp:
            result = _jr.loads(_resp.read())
            if result.get("token"):
                _d._write_cloud_token(result["token"])
                return jsonify({"ok": True, "token": result["token"]})
            return jsonify({"ok": False, "error": result.get("error", "Invalid code")})
    except Exception as _ex:
        try:
            _eb = _jr.loads(_ex.read()) if hasattr(_ex, "read") else {}
        except Exception:
            _eb = {}
        return jsonify({"ok": False, "error": _eb.get("error", "Invalid code")}), 502
