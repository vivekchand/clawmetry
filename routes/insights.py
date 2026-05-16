"""routes/insights.py — Weekly Insights Digest endpoints.

Gated by ``CLAWMETRY_INSIGHTS=1`` (off for v1 soak).

  GET  /api/insights/preview         — latest digest (cached 6h)
  GET  /api/insights/history?weeks=N — past N weeks
  POST /api/insights/send-now        — dispatch via configured channel
  GET/POST /api/insights/config      — insights_config.json
  GET  /insights                     — HTML preview page

Heavy lifting in ``clawmetry/insights.py``. Per
``project_alerts_pro_feature.md`` digest becomes Pro-only after soak.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from flask import Blueprint, jsonify, request, Response

log = logging.getLogger("clawmetry.routes.insights")

bp_insights = Blueprint("insights", __name__)

# Past digests live next to the config so a single chmod 700 protects both.
_HISTORY_DIR = Path(
    os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
) / ".clawmetry" / "insights_history"

# In-process cache so ``/api/insights/preview`` doesn't pay the LLM cost on
# every page-load. Manual ``send-now`` always re-generates.
_PREVIEW_CACHE: dict = {"digest": None, "ts": 0.0}
_PREVIEW_TTL_SECS = 6 * 3600  # 6h


def _feature_enabled() -> bool:
    return os.environ.get("CLAWMETRY_INSIGHTS", "").strip() == "1"


def _gated() -> Response | None:
    """Return a 404 Response when the feature flag is off, else None."""
    if _feature_enabled():
        return None
    return jsonify({
        "error": "feature_disabled",
        "hint": "Set CLAWMETRY_INSIGHTS=1 to enable Weekly Insights Digest.",
    }), 404  # type: ignore[return-value]


def _persist_history(digest_dict: dict) -> None:
    """Persist into ``insights_history/<week_start>.json`` (last-write-wins)."""
    try:
        _HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        wk = digest_dict.get("week_start") or time.strftime("%Y-%m-%d")
        (Path(_HISTORY_DIR) / f"{wk}.json").write_text(
            json.dumps(digest_dict, indent=2), encoding="utf-8"
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("insights: failed to persist history: %s", exc)


def _load_history(weeks: int = 4) -> list[dict]:
    """Return up to ``weeks`` most-recent persisted digests (newest first)."""
    try:
        if not _HISTORY_DIR.exists():
            return []
        files = sorted(_HISTORY_DIR.glob("*.json"), reverse=True)[: max(1, weeks)]
        out: list[dict] = []
        for f in files:
            try:
                out.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                continue
        return out
    except Exception:  # noqa: BLE001
        return []


@bp_insights.route("/api/insights/preview", methods=["GET"])
def api_preview():
    gated = _gated()
    if gated is not None:
        return gated
    refresh = request.args.get("refresh", "0") == "1"
    now = time.time()
    if (
        not refresh
        and _PREVIEW_CACHE["digest"] is not None
        and (now - _PREVIEW_CACHE["ts"]) < _PREVIEW_TTL_SECS
    ):
        return jsonify(_PREVIEW_CACHE["digest"])

    from clawmetry.insights import WeeklyDigestGenerator
    digest = WeeklyDigestGenerator().generate()
    out = digest.to_dict()
    _PREVIEW_CACHE["digest"] = out
    _PREVIEW_CACHE["ts"] = now
    _persist_history(out)
    return jsonify(out)


@bp_insights.route("/api/insights/history", methods=["GET"])
def api_history():
    gated = _gated()
    if gated is not None:
        return gated
    weeks = request.args.get("weeks", 4, type=int)
    return jsonify({"digests": _load_history(weeks)})


@bp_insights.route("/api/insights/send-now", methods=["POST"])
def api_send_now():
    gated = _gated()
    if gated is not None:
        return gated
    from clawmetry.insights import WeeklyDigestGenerator, deliver, load_config
    cfg = load_config()
    digest = WeeklyDigestGenerator(cfg).generate()
    out = digest.to_dict()
    _persist_history(out)
    result = deliver(digest, cfg)
    return jsonify({"ok": True, "digest": out, "delivery": result})


@bp_insights.route("/api/insights/config", methods=["GET", "POST"])
def api_config():
    # GET always returns 200 with `{enabled: bool, ...}` so the dashboard's
    # nav-tab-reveal probe (`app.js` IIFE checking /api/insights/config) can
    # render the tab in either an active or a Pro-locked state without the
    # browser console-erroring on a 404. POSTs (writes) still 404 when the
    # feature flag is off — writes only make sense when the feature is on.
    #
    # Fixes #1431 (Pro-locked vs invisible-when-off) AND removes the need
    # for the cloud-contract 404 allowlist entry from PR #1435.
    from clawmetry.insights import load_config, save_config
    enabled = _feature_enabled()
    if request.method == "POST":
        if not enabled:
            return jsonify({
                "error": "feature_disabled",
                "hint": "Set CLAWMETRY_INSIGHTS=1 to enable Weekly Insights Digest.",
            }), 404
        data = request.get_json(silent=True) or {}
        cfg = save_config(data)
        return jsonify({"ok": True, "enabled": True, "config": cfg})
    # GET: always 200. When disabled, return only the enabled flag (no
    # config payload — nothing to expose to a viewer who hasn't opted in).
    if not enabled:
        return jsonify({"enabled": False})
    cfg = load_config()
    # Don't leak the API key back to the browser — return only a presence flag.
    cfg_safe = dict(cfg)
    cfg_safe["anthropic_api_key"] = "***" if cfg_safe.get("anthropic_api_key") else ""
    cfg_safe["enabled"] = True
    return jsonify(cfg_safe)


# ── Minimal HTML page (kept here, not in dashboard.py, to limit blast
# radius until the feature flips on) ─────────────────────────────────────

_INSIGHTS_HTML = """<!doctype html>
<html><head>
<meta charset="utf-8">
<title>ClawMetry — Weekly Insights</title>
<style>
  body{font:14px -apple-system,BlinkMacSystemFont,sans-serif;
       background:#0d1117;color:#e6edf3;margin:0;padding:24px;max-width:880px;
       margin-left:auto;margin-right:auto;}
  h1{margin:0 0 4px}
  h2{font-size:15px;margin:24px 0 6px;color:#7ee787}
  .meta{color:#7d8590;font-size:12px;margin-bottom:24px}
  .summary{background:#161b22;border:1px solid #30363d;border-radius:8px;
           padding:14px 18px;margin-bottom:18px}
  .insight{background:#161b22;border:1px solid #30363d;border-radius:8px;
           padding:12px 16px;margin-bottom:12px}
  .narrative{color:#e6edf3}
  .rows{margin-top:8px;font:11px ui-monospace,Menlo,monospace;
        color:#7d8590;background:#0d1117;border:1px solid #21262d;
        border-radius:4px;padding:8px;max-height:160px;overflow:auto;white-space:pre}
  .toolbar{display:flex;gap:8px;margin-bottom:18px}
  button{background:#238636;border:0;color:#fff;padding:6px 12px;
         border-radius:6px;cursor:pointer;font:13px inherit}
  button.secondary{background:#21262d}
  button:disabled{opacity:0.5;cursor:wait}
  .err{color:#f85149}
  .empty{color:#7d8590;font-style:italic}
  /* Inline status feedback for the Send-to-channel button. Replaces the
     debug-style alert(JSON.stringify(...)) that used to fire here. */
  #toast{position:fixed;bottom:24px;right:24px;background:#161b22;
         border:1px solid #30363d;border-radius:6px;padding:10px 14px;
         font-size:13px;color:#e6edf3;box-shadow:0 4px 12px rgba(0,0,0,0.4);
         opacity:0;transform:translateY(8px);
         transition:opacity 180ms ease,transform 180ms ease;
         pointer-events:none;max-width:340px}
  #toast.show{opacity:1;transform:translateY(0)}
  #toast.ok{border-color:#238636}
  #toast.err{border-color:#f85149}
</style></head><body>
<h1>Weekly Insights</h1>
<div class="meta" id="meta">Loading…</div>
<div class="toolbar">
  <button id="btn-refresh" onclick="refresh(true)">Regenerate</button>
  <button id="btn-send" class="secondary" onclick="sendNow()">Send to channel</button>
  <a href="/" style="color:#58a6ff;align-self:center;text-decoration:none;font-size:13px">
    &larr; Dashboard</a>
</div>
<div class="summary" id="summary">—</div>
<div id="insights"></div>
<div id="toast" role="status" aria-live="polite"></div>
<script>
function showToast(msg, kind){
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show ' + (kind === 'err' ? 'err' : 'ok');
  clearTimeout(showToast._h);
  showToast._h = setTimeout(function(){t.className = '';}, 4500);
}
async function refresh(force){
  const url='/api/insights/preview' + (force?'?refresh=1':'');
  document.getElementById('meta').textContent = 'Generating…';
  const r = await fetch(url);
  if(!r.ok){document.getElementById('meta').innerHTML =
    '<span class="err">Feature disabled. Set CLAWMETRY_INSIGHTS=1.</span>'; return;}
  const d = await r.json();
  document.getElementById('meta').textContent =
    'Week of ' + d.week_start + ' — generated ' + d.generated_at +
    ' (cost ~$' + d.cost_usd.toFixed(3) + ', ' + d.tokens_used + ' tokens)';
  document.getElementById('summary').textContent = d.summary || '(no summary)';
  const c = document.getElementById('insights');
  c.innerHTML = '';
  for(const ins of (d.insights||[])){
    const block = document.createElement('div');
    block.className = 'insight';
    const rowsTxt = (ins.rows && ins.rows.length)
      ? JSON.stringify(ins.rows, null, 2)
      : '(no rows)';
    block.innerHTML = '<h2>' + escape(ins.title) + '</h2>' +
      '<div class="narrative' + (ins.rows.length?'':' empty') + '">' +
        escape(ins.narrative || '(no narrative)') + '</div>' +
      '<details><summary style="cursor:pointer;font-size:11px;color:#7d8590;' +
        'margin-top:8px">raw rows (' + ins.rows.length + ')</summary>' +
      '<div class="rows">' + escape(rowsTxt) + '</div></details>';
    c.appendChild(block);
  }
}
async function sendNow(){
  const btn = document.getElementById('btn-send');
  btn.disabled = true; btn.textContent = 'Sending…';
  try {
    const r = await fetch('/api/insights/send-now', {method:'POST'});
    if (!r.ok){ showToast('Send failed: HTTP ' + r.status, 'err'); return; }
    const j = await r.json();
    const d = (j && j.delivery) || {};
    const sent = d.sent || [];
    const errs = d.errors || [];
    if (sent.length){
      // Successful dispatch — name the channel so the user knows where it went.
      showToast('Sent to ' + sent.map(c=>c[0].toUpperCase()+c.slice(1)).join(', ') + ' ✓', 'ok');
    } else if (errs.length){
      // Surface the first error verbatim — the deliver() shape already produces
      // human-readable strings like "slack: no webhook configured".
      showToast('Failed: ' + errs[0], 'err');
    } else {
      // Channel == "dashboard_only" — successful no-op. Tell the user instead
      // of leaving them wondering whether the click did anything.
      showToast('No channel configured — set one in /api/insights/config', 'err');
    }
  } catch(e){
    showToast('Send failed: ' + (e && e.message || e), 'err');
  } finally {
    btn.disabled = false; btn.textContent = 'Send to channel';
  }
}
function escape(s){return (s||'').toString()
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
refresh(false);
</script>
</body></html>"""


@bp_insights.route("/insights", methods=["GET"])
def insights_page():
    if not _feature_enabled():
        return Response(
            "<h2>Weekly Insights Digest</h2>"
            "<p>This feature is gated by <code>CLAWMETRY_INSIGHTS=1</code>. "
            "Restart with the env var set to enable.</p>",
            mimetype="text/html",
            status=404,
        )
    return Response(_INSIGHTS_HTML, mimetype="text/html")
