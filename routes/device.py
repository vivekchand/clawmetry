"""Device snapshot — a compact, screen-sized JSON for hardware companions.

ClawMetry already ingests every supported runtime (OpenClaw, NVIDIA NemoClaw,
and the 10 Pro adapters) into DuckDB. A small desk device (e.g. an ESP32 with a
tiny display) can't render the full dashboard, so this Blueprint exposes one
tiny, all-runtime payload it can poll over the local network and a ``/device-
preview`` page that renders that payload like the physical gauge would, so the
whole data path can be proven with zero hardware.

The endpoint is read-only and DuckDB-first like the rest of ClawMetry: it reads
through the daemon proxy (``_ls_call``) and reuses the same aggregate helpers
the dashboard uses, so it stays correct in cloud (no raw filesystem reads). A
short TTL cache keeps a chatty device from storming the daemon.
"""

import time

from flask import Blueprint, jsonify

bp_device = Blueprint("device", __name__)

# How long a built snapshot is reused before recomputing. A device that polls
# every second must not trigger a fresh DuckDB sweep every second — share one
# build across all pollers within the window (the performance-is-a-cost rule).
_SNAPSHOT_TTL_SECONDS = 5.0
_snapshot_cache = {"ts": 0.0, "payload": None}

SCHEMA_VERSION = 1


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback (issue #1088).

    Mirrors the per-module helper used across ``routes/`` — prefer the daemon
    HTTP proxy (so we never grab the writer lock), fall back to a read-only
    open for tests/dev where no daemon is running.
    """
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


def _coerce_rows(rows):
    """Normalise the proxy envelope (``{"result": [...]}`` / ``{"rows": [...]}``)
    or a bare list into a plain list."""
    if isinstance(rows, dict):
        rows = rows.get("result") or rows.get("rows") or []
    return rows if isinstance(rows, list) else []


def _runtime_for(session_id):
    """Map a session id to its runtime label. OSS-Free always resolves to
    ``openclaw``; the clawmetry-pro plugin resolves the real runtime."""
    try:
        from clawmetry import waste_flags as _wf

        return _wf.runtime_from_session_id(session_id) or "openclaw"
    except Exception:
        return "openclaw"


def _usage_today():
    """(cost_today_usd, tokens_today) across ALL runtimes, or (0.0, 0)."""
    try:
        from routes.usage import _try_local_store_usage

        usage = _try_local_store_usage() or {}
        return (
            round(float(usage.get("todayCost", 0.0)), 4),
            int(usage.get("today", 0)),
        )
    except Exception:
        return (0.0, 0)


def _active_sessions():
    """(active_count, sorted distinct runtimes among active sessions).

    Derived from the typed ``sessions`` table — the same source the Overview
    helper counts from (status == "active"). Runtime is the session-id prefix
    (``agent_type`` is always "openclaw"), so distinct runtimes light up across
    all 12 once clawmetry-pro is installed.
    """
    rows = _coerce_rows(_ls_call("query_sessions_table", limit=300))
    active = [s for s in rows if isinstance(s, dict) and s.get("status") == "active"]
    runtimes = sorted({_runtime_for(s.get("session_id") or "") for s in active})
    return len(active), runtimes


def _top_alert():
    """The single most important currently-firing alert (newest unack'd in the
    last 24h), or None."""
    try:
        import dashboard as _d

        alerts = _d._get_active_alerts() or []
        if not alerts:
            return None
        a = alerts[0]  # _get_active_alerts is ORDER BY fired_at DESC
        return {
            "message": a.get("message") or a.get("rule_id") or "Alert firing",
            "fired_at": a.get("fired_at"),
        }
    except Exception:
        return None


def _oldest_pending_approval():
    """The oldest pending approval (so the device surfaces what's been waiting
    longest), with its tool action + runtime, or None.

    ``query_approvals`` returns newest-first, so we take the min by
    ``created_at`` to get the oldest.
    """
    try:
        rows = _coerce_rows(_ls_call("query_approvals", status="pending", limit=200))
        rows = [r for r in rows if isinstance(r, dict)]
        if not rows:
            return None
        oldest = min(rows, key=lambda r: (r.get("created_at") or ""))
        sid = oldest.get("requestor_session_id") or ""
        created = oldest.get("created_at") or ""
        waiting = None
        # created_at is an ISO-ish string; best-effort age in seconds.
        try:
            from datetime import datetime

            ts = datetime.fromisoformat(str(created).replace("Z", "")[:19])
            waiting = max(0, int(time.time() - ts.timestamp()))
        except Exception:
            waiting = None
        return {
            "id": oldest.get("id"),
            "action": oldest.get("action") or "tool call",
            "runtime": _runtime_for(sid),
            "session_id": sid,
            "waiting_seconds": waiting,
        }
    except Exception:
        return None


def _overall_health(has_alert, has_approval):
    """Coarse green/amber/red the size of one LED.

    red   — daemon is broken.
    amber — daemon degraded, an alert is firing, or an approval is waiting.
    green — nothing needs a human.
    """
    daemon_status = None
    try:
        from routes.health import compute_daemon_health

        daemon_status = (compute_daemon_health() or {}).get("status")
    except Exception:
        daemon_status = None

    if daemon_status == "broken":
        return "red"
    if daemon_status == "degraded" or has_alert or has_approval:
        return "amber"
    return "green"


def _build_device_snapshot():
    """Assemble the compact, all-runtime device payload."""
    cost_today, tokens_today = _usage_today()
    active_count, runtimes = _active_sessions()
    alert = _top_alert()
    approval = _oldest_pending_approval()
    health = _overall_health(alert is not None, approval is not None)
    return {
        "schema": SCHEMA_VERSION,
        "generated_at": int(time.time()),
        "cost_today_usd": cost_today,
        "tokens_today": tokens_today,
        "active_sessions": active_count,
        "runtimes_active": runtimes,
        "health": health,
        "alert": alert,
        "approval": approval,
    }


def _device_snapshot_cached():
    """Build at most once per TTL window; share across all pollers."""
    now = time.time()
    cached = _snapshot_cache.get("payload")
    if cached is not None and (now - _snapshot_cache["ts"]) < _SNAPSHOT_TTL_SECONDS:
        return cached
    payload = _build_device_snapshot()
    _snapshot_cache["payload"] = payload
    _snapshot_cache["ts"] = now
    return payload


@bp_device.route("/api/device/snapshot")
def api_device_snapshot():
    """Compact, all-runtime snapshot a hardware companion can poll.

    Never raises: every contributing read degrades to a safe default, so the
    device always gets a well-formed payload (the never-crash-on-bad-input
    convention). Shape::

        {
          "schema": 1,
          "generated_at": 1733356800,
          "cost_today_usd": 4.12,
          "tokens_today": 1840000,
          "active_sessions": 3,
          "runtimes_active": ["claude_code", "openclaw"],
          "health": "green" | "amber" | "red",
          "alert":   {"message": "...", "fired_at": ...} | null,
          "approval": {"id": ..., "action": "Bash", "runtime": "claude_code",
                        "session_id": "...", "waiting_seconds": 42} | null
        }
    """
    try:
        return jsonify(_device_snapshot_cached())
    except Exception:
        # Absolute last resort — still hand the device a valid shape.
        return jsonify({
            "schema": SCHEMA_VERSION,
            "generated_at": int(time.time()),
            "cost_today_usd": 0.0,
            "tokens_today": 0,
            "active_sessions": 0,
            "runtimes_active": [],
            "health": "green",
            "alert": None,
            "approval": None,
        })


@bp_device.route("/device-preview")
def device_preview():
    """A browser stand-in for the physical device — proves the whole data path
    (DuckDB → /api/device/snapshot → rendered gauge) with no hardware. The same
    JSON later drives the ESP32 firmware."""
    return _DEVICE_PREVIEW_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}


# A single self-contained page (no build step, matching the repo convention).
# It polls the snapshot, renders the all-runtime metrics, a health "LED", and —
# when an approval is pending — Approve / Deny buttons that POST the decision,
# the physical-button behaviour rendered in software.
_DEVICE_PREVIEW_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ClawMetry Device Preview</title>
<style>
  :root { color-scheme: dark; }
  body { margin:0; min-height:100vh; display:flex; align-items:center;
         justify-content:center; background:#0b0d12; font-family:-apple-system,
         BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; color:#e8eaf0; }
  .device { width:280px; border-radius:28px; padding:22px 20px 26px;
            background:linear-gradient(160deg,#181b22,#0e1015);
            box-shadow:0 30px 80px rgba(0,0,0,.6), inset 0 1px 0 rgba(255,255,255,.05);
            border:1px solid #23262f; }
  .top { display:flex; align-items:center; justify-content:space-between; }
  .brand { font-size:11px; letter-spacing:.14em; text-transform:uppercase;
           color:#7c8190; }
  .led { width:14px; height:14px; border-radius:50%; background:#3a3f4b;
         transition:background .4s, box-shadow .4s; }
  .led.green { background:#34d399; box-shadow:0 0 14px #34d39988; }
  .led.amber { background:#fbbf24; box-shadow:0 0 14px #fbbf2488; }
  .led.red   { background:#f87171; box-shadow:0 0 16px #f87171aa;
               animation:pulse 1s infinite; }
  @keyframes pulse { 50% { opacity:.45; } }
  .mascot { font-size:62px; text-align:center; margin:14px 0 6px;
            transition:transform .3s; }
  .state { text-align:center; font-size:12px; color:#9aa0ad; margin-bottom:16px;
           min-height:14px; }
  .cost { text-align:center; font-size:40px; font-weight:700; letter-spacing:-.02em; }
  .costlabel { text-align:center; font-size:10px; letter-spacing:.12em;
               text-transform:uppercase; color:#7c8190; margin-top:2px; }
  .grid { display:flex; gap:10px; margin:18px 0 4px; }
  .cell { flex:1; background:#13161d; border:1px solid #23262f; border-radius:14px;
          padding:10px 8px; text-align:center; }
  .cell .v { font-size:18px; font-weight:600; }
  .cell .k { font-size:9px; letter-spacing:.1em; text-transform:uppercase;
             color:#7c8190; margin-top:3px; }
  .runtimes { font-size:10px; color:#9aa0ad; text-align:center; margin-top:10px;
              min-height:12px; word-break:break-word; }
  .alert { margin-top:14px; background:#2a1d12; border:1px solid #5a3a1c;
           color:#fcd9a8; border-radius:12px; padding:9px 11px; font-size:11px;
           display:none; }
  .approval { margin-top:14px; background:#161b2a; border:1px solid #2d3550;
              border-radius:14px; padding:12px; display:none; }
  .approval .ask { font-size:12px; margin-bottom:3px; }
  .approval .tool { font-weight:700; }
  .approval .meta { font-size:10px; color:#8a90a0; margin-bottom:10px; }
  .btns { display:flex; gap:8px; }
  .btns button { flex:1; border:0; border-radius:10px; padding:9px 0; font-size:12px;
                 font-weight:600; cursor:pointer; }
  .approve { background:#34d399; color:#06231a; }
  .deny    { background:#f87171; color:#2a0c0c; }
  .foot { text-align:center; font-size:9px; color:#5a5f6c; margin-top:16px; }
  .foot b { color:#8a90a0; }
</style>
</head>
<body>
  <div class="device">
    <div class="top">
      <div class="brand">ClawMetry</div>
      <div id="led" class="led"></div>
    </div>
    <div id="mascot" class="mascot">😴</div>
    <div id="state" class="state">connecting…</div>
    <div id="cost" class="cost">$0.00</div>
    <div class="costlabel">spent today · all runtimes</div>
    <div class="grid">
      <div class="cell"><div id="tokens" class="v">0</div><div class="k">tokens</div></div>
      <div class="cell"><div id="active" class="v">0</div><div class="k">active</div></div>
      <div class="cell"><div id="rtcount" class="v">0</div><div class="k">runtimes</div></div>
    </div>
    <div id="runtimes" class="runtimes"></div>
    <div id="alert" class="alert"></div>
    <div id="approval" class="approval">
      <div class="ask">Approve <span id="apTool" class="tool"></span>?</div>
      <div id="apMeta" class="meta"></div>
      <div class="btns">
        <button class="approve" onclick="decide('approve')">Approve</button>
        <button class="deny" onclick="decide('deny')">Deny</button>
      </div>
    </div>
    <div class="foot">one device · <b>all 12 runtimes</b></div>
  </div>
<script>
const MOODS = {
  idle:   {emoji:'😺', text:'idle'},
  busy:   {emoji:'😼', text:'working…'},
  alert:  {emoji:'🙀', text:'needs you'},
  approve:{emoji:'🐱', text:'waiting for approval'},
  sleep:  {emoji:'😴', text:'sleeping'},
};
function fmtTokens(n){
  if(n>=1e9) return (n/1e9).toFixed(1)+'B';
  if(n>=1e6) return (n/1e6).toFixed(1)+'M';
  if(n>=1e3) return (n/1e3).toFixed(1)+'k';
  return String(n||0);
}
let last = null;
async function tick(){
  try{
    const r = await fetch('/api/device/snapshot');
    const d = await r.json();
    last = d;
    document.getElementById('led').className = 'led ' + (d.health||'green');
    document.getElementById('cost').textContent =
      '$' + (Number(d.cost_today_usd)||0).toFixed(2);
    document.getElementById('tokens').textContent = fmtTokens(d.tokens_today);
    document.getElementById('active').textContent = d.active_sessions||0;
    const rts = d.runtimes_active||[];
    document.getElementById('rtcount').textContent = rts.length;
    document.getElementById('runtimes').textContent = rts.join(' · ');

    const al = document.getElementById('alert');
    if(d.alert){ al.style.display='block'; al.textContent='⚠ '+d.alert.message; }
    else al.style.display='none';

    const ap = document.getElementById('approval');
    if(d.approval){
      ap.style.display='block';
      document.getElementById('apTool').textContent = d.approval.action;
      const w = d.approval.waiting_seconds;
      document.getElementById('apMeta').textContent =
        d.approval.runtime + (w!=null ? ' · waiting '+w+'s' : '');
    } else ap.style.display='none';

    let mood = 'idle';
    if(d.approval) mood='approve';
    else if(d.alert) mood='alert';
    else if((d.active_sessions||0)>0) mood='busy';
    else if((d.tokens_today||0)===0) mood='sleep';
    document.getElementById('mascot').textContent = MOODS[mood].emoji;
    document.getElementById('state').textContent = MOODS[mood].text;
  }catch(e){
    document.getElementById('state').textContent = 'daemon offline';
  }
}
async function decide(decision){
  // The physical Approve/Deny button. Best-effort POST to the approvals API;
  // the preview stays useful even where the write path isn't wired yet.
  if(!last || !last.approval) return;
  try{
    await fetch('/api/approvals/'+encodeURIComponent(last.approval.id)+'/'+decision,
                {method:'POST'});
  }catch(e){}
  document.getElementById('approval').style.display='none';
  tick();
}
tick();
setInterval(tick, 3000);
</script>
</body>
</html>"""
