"""routes/insights.py — Weekly Insights Digest endpoints.

Tier split (#1420 P0a):

  Cloud-Free / OSS-only: 1 weekly digest, dashboard view only, no dispatch.
  Cloud-Pro            : daily/scheduled cron + Slack/Telegram/email dispatch.

Both tiers also honour the legacy ``CLAWMETRY_INSIGHTS=1`` env-var as an
explicit-on override (kept as an emergency kill switch for CI/tests). When
the env-var is set every gate opens, matching pre-tier-split behaviour.

  GET  /api/insights/preview         — latest digest (cached 6h) — ALL tiers
  GET  /api/insights/history?weeks=N — past N weeks                — ALL tiers
  POST /api/insights/send-now        — dispatch via channel        — Pro-only
  GET/POST /api/insights/config      — insights_config.json        — GET all, POST Pro
  GET  /insights                     — HTML preview page           — ALL tiers

Heavy lifting in ``clawmetry/insights.py``. Per
``project_alerts_pro_feature.md`` dispatch is Cloud-Pro; Free sees an
upsell CTA in the JSON response instead of a silent paywall.
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

# Single-source upsell copy. NO em-dashes / double-dashes per
# ``feedback_no_em_dashes_in_user_facing_copy.md``.
_UPGRADE_CTA = (
    "Want this delivered to Slack every Monday at 9am? Upgrade to Cloud-Pro."
)


def _feature_enabled() -> bool:
    """Legacy explicit-on env-var override. When set, all gates open
    (used by CI / tests / emergency kill switch). When unset, tier check
    decides."""
    return os.environ.get("CLAWMETRY_INSIGHTS", "").strip() == "1"


def _is_pro() -> bool:
    """Pro-tier check via ``dashboard._is_pro_user()``. Fail-closed: any
    import / lookup failure returns False so we never leak Pro dispatch
    onto a Free / OSS node."""
    try:
        import dashboard as _d
        return bool(_d._is_pro_user())
    except Exception:  # noqa: BLE001
        return False


def _can_view() -> bool:
    """View tier = Free + Pro + OSS. Always True today because the
    weekly dashboard digest is ClawMetry-subsidised (~$0.05/user fits CAC).
    Kept as a function so a future quota check has one place to land."""
    return True


def _can_dispatch() -> bool:
    """Dispatch tier = Pro only. Env-var override still wins for tests
    so existing flag-on integration tests don't need an account."""
    return _feature_enabled() or _is_pro()


def _upgrade_payload() -> dict:
    """Standard non-Pro upsell envelope. Embedded in every preview /
    history / config response when the caller isn't on Cloud-Pro so the
    UI can render a one-line conversion button (per
    ``project_free_plan_upsell.md`` — every click is a conversion event,
    no silent failures)."""
    return {
        "_upgrade_cta": _UPGRADE_CTA,
        "_upgrade_url": "/cloud/billing",
        "_tier": "pro" if _is_pro() else "free",
    }


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
    # ALL tiers can view. Free / OSS pay zero — the synthesis cost
    # (~$0.05/user/week) fits inside CAC and is ClawMetry-subsidised.
    # TODO #1420 P0b: cloud-relayed Anthropic key for Pro users (separate
    # PR). For now, callers without ANTHROPIC_API_KEY get the "no data"
    # fallback digest produced by WeeklyDigestGenerator (the same path
    # test_generate_on_empty_store_no_api_key already exercises).
    if not _can_view():
        return jsonify({"error": "feature_disabled"}), 404
    refresh = request.args.get("refresh", "0") == "1"
    now = time.time()
    if (
        not refresh
        and _PREVIEW_CACHE["digest"] is not None
        and (now - _PREVIEW_CACHE["ts"]) < _PREVIEW_TTL_SECS
    ):
        out = dict(_PREVIEW_CACHE["digest"])
        if not _is_pro():
            out.update(_upgrade_payload())
        return jsonify(out)

    from clawmetry.insights import WeeklyDigestGenerator
    digest = WeeklyDigestGenerator().generate()
    out = digest.to_dict()
    _PREVIEW_CACHE["digest"] = out
    _PREVIEW_CACHE["ts"] = now
    _persist_history(out)
    # Attach CTA to the response only (don't poison the cache, in case
    # the user upgrades mid-TTL and we want a clean payload on next hit).
    resp = dict(out)
    if not _is_pro():
        resp.update(_upgrade_payload())
    return jsonify(resp)


@bp_insights.route("/api/insights/history", methods=["GET"])
def api_history():
    if not _can_view():
        return jsonify({"error": "feature_disabled"}), 404
    weeks = request.args.get("weeks", 4, type=int)
    payload: dict = {"digests": _load_history(weeks)}
    if not _is_pro():
        payload.update(_upgrade_payload())
    return jsonify(payload)


@bp_insights.route("/api/insights/send-now", methods=["POST"])
def api_send_now():
    # Pro-only: dispatch (Slack/Telegram/email) is the Cloud-Pro value-add.
    # Free callers get the standard 402 + upsell envelope so the UI can
    # render a conversion CTA instead of a silent failure (per
    # ``project_free_plan_upsell.md`` and ``project_alerts_pro_feature.md``).
    if not _can_dispatch():
        return jsonify({
            "ok": False,
            "error": "pro_required",
            **_upgrade_payload(),
        }), 402
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
    # browser console-erroring on a 404. Writes (POST) still require Pro
    # because the only thing they configure is dispatch (channel + creds).
    #
    # Fixes #1431 (Pro-locked vs invisible-when-off) AND removes the need
    # for the cloud-contract 404 allowlist entry from PR #1435.
    from clawmetry.insights import load_config, save_config
    if request.method == "POST":
        # Writes touch dispatch config — Pro-gated.
        if not _can_dispatch():
            return jsonify({
                "ok": False,
                "error": "pro_required",
                **_upgrade_payload(),
            }), 402
        data = request.get_json(silent=True) or {}
        cfg = save_config(data)
        return jsonify({"ok": True, "enabled": True, "config": cfg})
    # GET: always 200. View tier opens the panel for all callers; we
    # return the full config so the dashboard nav-tab probe reveals the
    # tab, and attach the upsell CTA for Free / OSS so the UI can render
    # the conversion button.
    cfg = load_config()
    cfg_safe = dict(cfg)
    cfg_safe["anthropic_api_key"] = "***" if cfg_safe.get("anthropic_api_key") else ""
    cfg_safe["enabled"] = True
    if not _is_pro():
        cfg_safe.update(_upgrade_payload())
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
<div id="upsell" style="display:none;background:#1f6feb1a;border:1px solid #1f6feb;
     border-radius:6px;padding:10px 14px;margin-bottom:14px;font-size:13px">
  <span id="upsell-text"></span>
  <a id="upsell-link" href="/cloud/billing" style="color:#58a6ff;margin-left:8px;
     text-decoration:none;font-weight:600">Upgrade →</a>
</div>
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
    '<span class="err">Insights unavailable on this node.</span>'; return;}
  const d = await r.json();
  document.getElementById('meta').textContent =
    'Week of ' + d.week_start + ', generated ' + d.generated_at +
    ' (cost ~$' + d.cost_usd.toFixed(3) + ', ' + d.tokens_used + ' tokens)';
  document.getElementById('summary').textContent = d.summary || '(no summary)';
  // Tier-split upsell (#1420). Pro callers get _tier='pro' and no banner;
  // Free / OSS get a one-line conversion button linking to /cloud/billing.
  const upsell = document.getElementById('upsell');
  if (d._upgrade_cta) {
    document.getElementById('upsell-text').textContent = d._upgrade_cta;
    if (d._upgrade_url) document.getElementById('upsell-link').href = d._upgrade_url;
    upsell.style.display = '';
  } else {
    upsell.style.display = 'none';
  }
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
    if (r.status === 402){
      // Tier-split: Free / OSS hit the Pro paywall. Surface the upsell
      // CTA from the response (no silent failure per
      // project_free_plan_upsell.md). Click takes the user to billing.
      const j = await r.json().catch(function(){return {};});
      const cta = (j && j._upgrade_cta) || 'Upgrade to Cloud-Pro for dispatch.';
      const url = (j && j._upgrade_url) || '/cloud/billing';
      showToast(cta + ' (open ' + url + ')', 'err');
      return;
    }
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
    # View tier is universal under the tier-split (#1420 P0a). The page
    # itself fetches /api/insights/preview which carries the upsell CTA
    # for non-Pro callers; the inline JS renders it as a one-line button.
    if not _can_view():
        return Response(
            "<h2>Weekly Insights Digest</h2>"
            "<p>Disabled on this node.</p>",
            mimetype="text/html",
            status=404,
        )
    return Response(_INSIGHTS_HTML, mimetype="text/html")
