"""Render a trace bundle to a self-contained HTML page (PRD-pr-trace.md §4g).

The hosted viewer lives in **clawmetry-cloud**; this is the local renderer, and
it exists for two reasons. It makes the bundle format tangible and reviewable
before any server exists, and it is what powers the mandatory
"this is what the world will see" review screen (§4f) — you cannot ask someone
to approve a publication they cannot look at.

Design follows §4g: GitHub-shaped chrome, immediate context above the fold,
Prompts as the default lens. No external assets — the page is one file with no
network dependency, which is also what makes it safe to hand to a reviewer.
"""

from __future__ import annotations

import html
import json
from typing import Any

_ATTR_COPY = {
    "exact": ("exact", "Every commit named its session directly."),
    "shared": ("shared", ("This session also produced work outside this range; "
                          "cost is an upper bound.")),
    "heuristic": ("heuristic", ("Sessions were inferred from commit timing, not "
                                "declared. Treat as a hint, not a measurement.")),
}

_CSS = """
:root{--bg:#fff;--fg:#1f2328;--muted:#59636e;--line:#d1d9e0;--accent:#0969da;
--chip:#f6f8fa;--warn:#9a6700;--warnbg:#fff8c5}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;
--muted:#9198a1;--line:#3d444d;--accent:#4493f8;--chip:#151b23;
--warn:#d29922;--warnbg:#282215}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
.wrap{max-width:1012px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:20px;font-weight:600;margin:0 0 4px}
h1 .num{color:var(--muted);font-weight:400}
.sub{color:var(--muted);margin:0 0 16px}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.stat{background:var(--chip);border:1px solid var(--line);border-radius:6px;
padding:8px 12px;min-width:96px}
.stat b{display:block;font-size:18px;font-weight:600}
.stat span{color:var(--muted);font-size:12px}
.chip{display:inline-block;border:1px solid var(--line);border-radius:2em;
padding:2px 10px;font-size:12px;background:var(--chip);color:var(--muted)}
.chip.warn{background:var(--warnbg);color:var(--warn);border-color:var(--warn)}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin:20px 0 0}
.tab{padding:8px 14px;border:0;background:none;color:var(--fg);cursor:pointer;
font:inherit;border-bottom:2px solid transparent}
.tab[aria-selected=true]{border-bottom-color:#fd8c73;font-weight:600}
.tab:disabled{color:var(--muted);cursor:not-allowed}
.panel{padding:20px 0}
.prompt{border:1px solid var(--line);border-radius:6px;margin:0 0 12px;
overflow:hidden}
.prompt .hd{background:var(--chip);padding:6px 12px;font-size:12px;
color:var(--muted);border-bottom:1px solid var(--line)}
.prompt pre{margin:0;padding:12px;white-space:pre-wrap;word-wrap:break-word;
font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}
.ev{display:flex;gap:10px;padding:6px 0;border-bottom:1px solid var(--line);
font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}
.ev .t{color:var(--muted);min-width:150px}
.ev .c{flex:1;white-space:pre-wrap;word-wrap:break-word;overflow-wrap:anywhere}
.empty{border:1px dashed var(--line);border-radius:6px;padding:24px;
color:var(--muted);text-align:center}
.note{background:var(--warnbg);color:var(--warn);border:1px solid var(--warn);
border-radius:6px;padding:10px 12px;margin:12px 0;font-size:13px}
footer{color:var(--muted);font-size:12px;margin-top:32px;
border-top:1px solid var(--line);padding-top:12px}
"""

_JS = """
document.querySelectorAll('.tab').forEach(function(t){
  t.addEventListener('click', function(){
    document.querySelectorAll('.tab').forEach(function(x){
      x.setAttribute('aria-selected','false');});
    document.querySelectorAll('.panel').forEach(function(p){p.hidden=true;});
    t.setAttribute('aria-selected','true');
    var el=document.getElementById('panel-'+t.dataset.lens);
    if(el){el.hidden=false;}
  });
});
"""


def _esc(v: Any) -> str:
    return html.escape(str(v if v is not None else ""), quote=True)


def _fmt_money(v) -> str:
    try:
        return f"${float(v):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def _fmt_int(v) -> str:
    try:
        return f"{int(v):,}"
    except (TypeError, ValueError):
        return "0"


def _models_line(models: dict) -> str:
    if not models:
        return "no model recorded"
    total = sum(models.values()) or 1
    parts = [f"{name} ({round(100 * n / total)}%)"
             for name, n in sorted(models.items(), key=lambda kv: -kv[1])]
    return " · ".join(parts)


def render_html(bundle: dict) -> str:
    """Return a complete, dependency-free HTML document for ``bundle``."""
    summary = bundle.get("summary") or {}
    project = bundle.get("project") or "(unknown project)"
    pr = bundle.get("pr")
    attr = bundle.get("attribution") or "heuristic"
    attr_label, attr_why = _ATTR_COPY.get(attr, _ATTR_COPY["heuristic"])
    title = f"{project} #{pr}" if pr else f"{project} {bundle.get('commit_range','')}"

    prompts = (bundle.get("lenses") or {}).get("prompts") or []
    trace = (bundle.get("lenses") or {}).get("trace") or []

    stats = [
        (_fmt_money(summary.get("cost_usd")), "cost" + (" (upper bound)"
                                                        if summary.get("cost_is_upper_bound") else "")),
        (_fmt_int(summary.get("tokens")), "tokens"),
        (_fmt_int(summary.get("prompts")), "prompts"),
        (_fmt_int(summary.get("turns")), "turns"),
        (_fmt_int(summary.get("tools")), "tool calls"),
        (_fmt_int(len(bundle.get("commits") or [])), "commits"),
    ]

    out = [
        "<!doctype html><html lang=en><head><meta charset=utf-8>",
        '<meta name=viewport content="width=device-width,initial-scale=1">',
        f"<title>{_esc(title)} — ClawMetry trace</title>",
        f"<style>{_CSS}</style></head><body><div class=wrap>",
        f"<h1>{_esc(project)} {'<span class=num>#' + _esc(pr) + '</span>' if pr else ''}</h1>",
        f"<p class=sub>{_esc(bundle.get('commit_range') or '')}</p>",
        "<div class=stats>",
    ]
    for value, label in stats:
        out.append(f"<div class=stat><b>{_esc(value)}</b><span>{_esc(label)}</span></div>")
    out.append("</div>")
    attr_cls = "chip" if attr == "exact" else "chip warn"
    models_line = _models_line(summary.get("models") or {})
    out.append(
        "<p><span class='" + attr_cls + "'>attribution: " + _esc(attr_label)
        + "</span> <span class=chip>" + _esc(models_line) + "</span></p>"
    )
    out.append(f"<p class=sub>{_esc(attr_why)}</p>")

    # Tabs. Lenses with no data producer yet (§3b) are disabled, not faked.
    out.append("<div class=tabs role=tablist>")
    out.append("<button class=tab data-lens=prompts role=tab aria-selected=true>Prompts</button>")
    out.append("<button class=tab data-lens=trace role=tab aria-selected=false>Trace</button>")
    out.append("<button class=tab role=tab disabled title='Needs iter_replay_events "
               "(PRD §3b)'>Agent graph</button>")
    out.append("<button class=tab role=tab disabled title='Needs iter_replay_events "
               "(PRD §3b)'>Workflows</button>")
    out.append("</div>")

    # Prompts (default)
    out.append("<div class=panel id=panel-prompts>")
    if prompts:
        for i, p in enumerate(prompts, 1):
            out.append(
                f"<div class=prompt><div class=hd>#{i} · {_esc(p.get('ts'))}</div>"
                f"<pre>{_esc(p.get('text'))}</pre></div>"
            )
    else:
        out.append("<div class=empty>No user prompts resolved for this range.</div>")
    out.append("</div>")

    # Trace
    out.append("<div class=panel id=panel-trace hidden>")
    if trace:
        for ev in trace:
            label = ev.get("tool") or ev.get("role") or ev.get("type") or ""
            text = (ev.get("text") or "")[:2000]
            out.append(
                f"<div class=ev><span class=t>{_esc(ev.get('ts'))} "
                f"{_esc(ev.get('type'))}</span>"
                f"<span class=c><b>{_esc(label)}</b> {_esc(text)}</span></div>"
            )
    else:
        out.append("<div class=empty>No events resolved for this range.</div>")
    out.append("</div>")

    out.append(
        "<footer>Generated by ClawMetry · secrets and private detail removed "
        "before publication (PRD-pr-trace.md §4f). Agent graph and Workflows "
        "are disabled until replay-event mappers land (§3b).</footer>"
    )
    out.append(f"</div><script>{_JS}</script></body></html>")
    return "\n".join(out)


def render_json(bundle: dict) -> str:
    return json.dumps(bundle, indent=2, default=str)
