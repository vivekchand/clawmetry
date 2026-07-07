"""routes/reports.py — ClawMetry Reports: markdown + embedded DuckDB SQL.

Write .md files to ~/.clawmetry/reports/. Embed SQL with:
    <!-- duckdb: SELECT count(*) FROM sessions -->
Navigate to /reports/<slug> to see them rendered as HTML tables.

Issue: https://github.com/vivekchand/clawmetry/issues/1005
"""
from __future__ import annotations

import csv
import html
import io
import os
import re

from flask import Blueprint, Response, jsonify, request

bp_reports = Blueprint("reports", __name__)

_MAX_SQL_LEN = 2_000
_BLOCK_RE = re.compile(r"<!--\s*duckdb:\s*(.*?)\s*-->", re.DOTALL | re.IGNORECASE)


# ── Storage ─────────────────────────────────────────────────────────────────────────────


def _reports_dir() -> str:
    d = os.path.expanduser("~/.clawmetry/reports")
    os.makedirs(d, exist_ok=True)
    return d


# ── Query helpers ────────────────────────────────────────────────────────────────────────


def _run_sql(sql: str) -> tuple[list[dict], str | None]:
    """Run SQL via daemon proxy, falling back to direct store. Returns (rows, error)."""
    sql = sql.strip()
    if len(sql) > _MAX_SQL_LEN:
        return [], f"SQL block too long (max {_MAX_SQL_LEN} chars)"
    try:
        from clawmetry.dives_sql_safety import validate_sql
        ok, reason = validate_sql(sql)
        if not ok:
            return [], f"SQL rejected: {reason}"
    except Exception as e:
        return [], f"SQL validator unavailable: {e}"
    # Daemon proxy first - avoids contending on the DuckDB writer lock
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("raw_select_safe", sql=sql)
        if rows is not None:
            return rows, None
    except Exception:
        pass
    # Fall back to direct store (dev mode / unit tests)
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        return store.raw_select_safe(sql=sql), None
    except Exception as e:
        return [], str(e)[:200]


# ── Rendering ───────────────────────────────────────────────────────────────────────────


def _rows_to_html_table(rows: list[dict]) -> str:
    if not rows:
        return '<p class="cm-rpt-empty">No results.</p>'
    cols = list(rows[0].keys())
    parts = ['<div class="cm-rpt-wrap"><table class="cm-rpt-tbl">']
    parts.append("<thead><tr>")
    for c in cols:
        parts.append(f"<th>{html.escape(str(c))}</th>")
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        for c in cols:
            v = row.get(c)
            parts.append(f"<td>{html.escape('' if v is None else str(v))}</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def _md_to_html(text: str) -> str:
    """Minimal markdown to HTML for report prose (no SQL blocks remain here)."""
    lines = text.split("\n")
    out: list[str] = []
    in_code = False
    for line in lines:
        if line.startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                lang = html.escape(line[3:].strip())
                out.append(f'<pre class="cm-rpt-code"><code class="language-{lang}">')
                in_code = True
            continue
        if in_code:
            out.append(html.escape(line) + "\n")
            continue
        if line.startswith("### "):
            out.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith(("- ", "* ")):
            out.append(f"<li>{html.escape(line[2:])}</li>")
        elif line.strip() == "":
            out.append("")
        else:
            escaped = html.escape(line)
            escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
            escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
            out.append(f"<p>{escaped}</p>")
    return "\n".join(out)


_CSS = """
body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;
  color:#1a1a1a;line-height:1.6}
a{color:#2563eb}
.cm-rpt-wrap{overflow-x:auto;margin:1rem 0}
.cm-rpt-tbl{border-collapse:collapse;width:100%;font-size:.875rem}
.cm-rpt-tbl th,.cm-rpt-tbl td{border:1px solid #d1d5db;padding:.4rem .75rem;text-align:left}
.cm-rpt-tbl th{background:#f3f4f6;font-weight:600}
.cm-rpt-tbl tr:hover td{background:#f9fafb}
.cm-rpt-empty{color:#6b7280;font-style:italic}
.cm-rpt-err{color:#dc2626;font-style:italic}
.cm-rpt-code{background:#f3f4f6;padding:1rem;overflow-x:auto;border-radius:.375rem;
  font-size:.875rem}
h1{font-size:1.75rem;margin-top:0}
h2{font-size:1.25rem;margin-top:1.5rem}
h3{font-size:1rem;margin-top:1.25rem}
"""


def _render_page(slug: str, md_content: str) -> str:
    """Render a report .md file to a full HTML page (SQL blocks replaced with tables)."""
    parts: list[str] = []
    last_end = 0
    for m in _BLOCK_RE.finditer(md_content):
        segment = md_content[last_end : m.start()]
        if segment.strip():
            parts.append(_md_to_html(segment))
        sql = m.group(1).strip()
        rows, err = _run_sql(sql)
        if err:
            parts.append(f'<div class="cm-rpt-err">Query error: {html.escape(err)}</div>')
        else:
            parts.append(_rows_to_html_table(rows))
        last_end = m.end()
    remaining = md_content[last_end:]
    if remaining.strip():
        parts.append(_md_to_html(remaining))
    body = "\n".join(parts)
    return (
        f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        f"<meta charset=\"utf-8\">\n"
        f"<title>{html.escape(slug)} - ClawMetry Reports</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n{body}\n</body>\n</html>"
    )


def _safe_slug(raw: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]", "", raw)


# ── Endpoints ─────────────────────────────────────────────────────────────────────────────


@bp_reports.route("/api/reports")
def api_reports_list():
    """GET /api/reports returns {reports: [{slug, title}]}"""
    try:
        d = _reports_dir()
        items = []
        for fname in sorted(os.listdir(d)):
            if not fname.endswith(".md"):
                continue
            slug = fname[:-3]
            title = slug
            try:
                with open(os.path.join(d, fname), encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        stripped = line.strip().lstrip("# ").strip()
                        if stripped:
                            title = stripped
                            break
            except Exception:
                pass
            items.append({"slug": slug, "title": title})
        return jsonify({"reports": items})
    except Exception as e:
        return jsonify({"reports": [], "error": str(e)}), 200


@bp_reports.route("/reports/")
def reports_index():
    """GET /reports/ returns an HTML index listing all reports."""
    data = api_reports_list().get_json(force=True) or {}
    items = data.get("reports", [])
    if not items:
        body = (
            "<h1>No reports yet</h1>"
            "<p>Create a <code>.md</code> file in "
            "<code>~/.clawmetry/reports/</code> with embedded SQL blocks:</p>"
            "<pre>&lt;!-- duckdb: SELECT count(*) FROM sessions --&gt;</pre>"
            "<p>Then refresh this page.</p>"
        )
    else:
        links = "".join(
            f'<li><a href="/reports/{html.escape(r["slug"])}">'
            f'{html.escape(r["title"])}</a></li>'
            for r in items
        )
        body = f"<h1>Reports</h1><ul>{links}</ul>"
    page = (
        f"<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>ClawMetry Reports</title><style>{_CSS}</style></head>"
        f"<body>{body}</body></html>"
    )
    return Response(page, content_type="text/html; charset=utf-8")


@bp_reports.route("/reports/<slug>")
def reports_render(slug: str):
    """GET /reports/<slug> returns a rendered HTML report."""
    slug = _safe_slug(slug)
    if not slug:
        return Response("Invalid report name.", status=400)
    path = os.path.join(_reports_dir(), f"{slug}.md")
    if not os.path.isfile(path):
        return Response(f"Report '{slug}' not found.", status=404, content_type="text/plain")
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            content = fh.read()
    except Exception as e:
        return Response(f"Cannot read report: {e}", status=500, content_type="text/plain")
    return Response(_render_page(slug, content), content_type="text/html; charset=utf-8")


@bp_reports.route("/reports/<slug>/export.csv")
def reports_export_csv(slug: str):
    """GET /reports/<slug>/export.csv?block=<n> returns CSV of SQL block n."""
    slug = _safe_slug(slug)
    if not slug:
        return Response("Invalid report name.", status=400)
    try:
        block_idx = int(request.args.get("block", "0"))
    except (TypeError, ValueError):
        return Response("'block' must be an integer", status=400)
    path = os.path.join(_reports_dir(), f"{slug}.md")
    if not os.path.isfile(path):
        return Response(f"Report '{slug}' not found.", status=404)
    with open(path, encoding="utf-8", errors="replace") as fh:
        content = fh.read()
    blocks = _BLOCK_RE.findall(content)
    if block_idx >= len(blocks):
        return Response(
            f"Block {block_idx} not found (report has {len(blocks)} block(s)).",
            status=404,
        )
    rows, err = _run_sql(blocks[block_idx].strip())
    if err:
        return Response(f"Query error: {err}", status=400)
    if not rows:
        return Response("", content_type="text/csv")
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    fname = f"{slug}-block{block_idx}.csv"
    return Response(
        buf.getvalue(),
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
