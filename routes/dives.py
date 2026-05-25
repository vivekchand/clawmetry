"""routes/dives.py — ClawMetry Dives: NL-to-SQL-to-chart over the local DuckDB store.

Sub-issue https://github.com/vivekchand/clawmetry/issues/1002 (DIVES-3).

Depends on:
  clawmetry/dives_sql_safety.py  — SQL allowlist validator      (DIVES-1, done)
  clawmetry/dives_prompt.py      — LLM prompt builder           (DIVES-2, done)
  clawmetry/local_store.py       — raw_select_safe, dives_table_columns

Auth: same zero-config strategy as Advisor —
  1. ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN / CLAUDE_API_KEY env var
  2. claude CLI (OAuth) via _call_via_claude_cli
  3. 412 with setup hint when neither is available

Storage: ~/.clawmetry/dives/<slug>.json — one JSON file per saved Dive.
"""

from __future__ import annotations

import json
import os
import re
import time

from flask import Blueprint, jsonify, request

bp_dives = Blueprint("dives", __name__)

_MAX_QUESTION_LEN = 1_000
_MAX_NAME_LEN = 200
_QUERY_TIMEOUT_SEC = 30


# ── Storage helpers ────────────────────────────────────────────────────────────


def _dives_dir() -> str:
    d = os.path.expanduser("~/.clawmetry/dives")
    os.makedirs(d, exist_ok=True)
    return d


def _safe_slug(raw: str) -> str:
    """Sanitise a slug — alphanumeric + hyphens only, prevents path traversal."""
    return re.sub(r"[^a-z0-9\-]", "", raw.lower())[:80]


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s[:60] or "dive"


def _unique_slug(name: str) -> str:
    base = _slugify(name)
    d = _dives_dir()
    slug, n = base, 1
    while os.path.exists(os.path.join(d, slug + ".json")):
        n += 1
        slug = f"{base}-{n}"
    return slug


def _read_dive(slug: str) -> dict | None:
    path = os.path.join(_dives_dir(), _safe_slug(slug) + ".json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _list_dives() -> list[dict]:
    d = _dives_dir()
    out = []
    for fname in sorted(os.listdir(d)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, fname)) as f:
                obj = json.load(f)
            out.append({
                "slug":       fname[:-5],
                "name":       obj.get("name", ""),
                "question":   obj.get("question", ""),
                "saved_at":   obj.get("saved_at"),
                "chart_type": (obj.get("chart_spec") or {}).get("chart_type"),
            })
        except Exception:
            pass
    return out


# ── LLM dispatch ──────────────────────────────────────────────────────────────


def _call_llm_for_sql(question: str, store) -> dict:
    """Return the LLM-generated {sql, chart_type, x, y, title, description} spec."""
    import shutil
    from routes.advisor import (
        _load_anthropic_auth,
        _call_anthropic_api,
        _call_via_claude_cli,
    )
    from clawmetry.dives_prompt import build_dives_prompt

    mode, credential = _load_anthropic_auth()
    if not credential:
        raise ValueError(
            "no_auth: No Anthropic credential. "
            "Export ANTHROPIC_API_KEY or run `claude` CLI to set up OAuth."
        )

    msgs = build_dives_prompt(question, store)

    if mode == "claude_cli":
        claude_bin = shutil.which("claude") or "claude"
        raw = _call_via_claude_cli(
            claude_bin,
            msgs["user"],
            system=msgs["system"],
            timeout=_QUERY_TIMEOUT_SEC,
        )
    else:
        raw = _call_anthropic_api(
            credential,
            msgs["user"],
            system=msgs["system"],
            max_tokens=512,
            timeout=_QUERY_TIMEOUT_SEC,
        )

    if raw.get("_error"):
        raise ValueError(f"upstream_error: {raw.get('body', '')[:200]}")

    text = "".join(
        b.get("text", "")
        for b in (raw.get("content") or [])
        if isinstance(b, dict) and b.get("type") == "text"
    ).strip()

    # Strip optional markdown fences the model sometimes adds.
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)

    try:
        spec = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"parse_error: LLM returned non-JSON ({e})")

    for key in ("sql", "chart_type", "x", "y", "title"):
        if not spec.get(key):
            raise ValueError(f"incomplete_response: LLM response missing '{key}'")

    return spec


# ── Store + SQL execution ──────────────────────────────────────────────────────


def _get_store():
    from clawmetry import local_store
    return local_store.get_store(read_only=True)


def _execute(sql: str, store) -> tuple[list[dict], str | None]:
    """Validate then run *sql*. Returns (rows, error_or_None)."""
    from clawmetry.dives_sql_safety import validate_sql
    ok, reason = validate_sql(sql)
    if not ok:
        return [], reason
    try:
        return store.raw_select_safe(sql=sql), None
    except Exception as e:
        return [], str(e)[:200]


# ── Endpoints ──────────────────────────────────────────────────────────────────


@bp_dives.route("/api/dives/query", methods=["POST"])
def api_dives_query():
    """POST {question} → {sql, chart_spec, rows, ms, error?}"""
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Provide a non-empty 'question' field."}), 400
    if len(question) > _MAX_QUESTION_LEN:
        return jsonify({"error": f"Question too long (max {_MAX_QUESTION_LEN} chars)."}), 400

    try:
        store = _get_store()
    except Exception:
        # Cold/cloud fall-through: there's no local DuckDB to query here (the
        # cloud container has no ~/.clawmetry, and a keyless browser hasn't
        # rerouted through the cm-cloud-dives relay yet). Return a clean,
        # graceful message instead of leaking the raw DuckDB IO error — the
        # frontend renders `error` verbatim in its result box. When the cloud
        # interceptor IS active it reroutes POST /api/dives/query to the
        # heartbeat relay and this handler is never reached. (#2124)
        return jsonify({
            "error": "Dives runs SQL against your local data store, which isn't "
                     "reachable from here. Open your local dashboard at "
                     "http://localhost:8900 to run Dives — your raw event data "
                     "stays on your machine.",
        }), 200

    t0 = time.monotonic()
    try:
        spec = _call_llm_for_sql(question, store)
    except ValueError as e:
        msg = str(e)
        if msg.startswith("no_auth"):
            return jsonify({"error": "no_auth", "message": msg[8:].strip()}), 412
        return jsonify({"error": "upstream_error", "detail": msg}), 502

    sql = spec["sql"]
    rows, sql_error = _execute(sql, store)
    ms = int((time.monotonic() - t0) * 1000)

    chart_spec = {
        "chart_type":  spec.get("chart_type", "table"),
        "x":           spec.get("x"),
        "y":           spec.get("y"),
        "title":       spec.get("title", question[:60]),
        "description": spec.get("description", ""),
    }
    body: dict = {"sql": sql, "chart_spec": chart_spec, "rows": rows, "ms": ms}
    if sql_error:
        body["error"] = sql_error
    return jsonify(body)


@bp_dives.route("/api/dives/save", methods=["POST"])
def api_dives_save():
    """POST {question, sql, chart_spec, name} → {slug}"""
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    sql = (payload.get("sql") or "").strip()
    name = (payload.get("name") or question[:60]).strip()
    chart_spec = payload.get("chart_spec") or {}

    if not question or not sql or not name:
        return jsonify({"error": "Provide 'question', 'sql', and 'name'."}), 400
    if len(name) > _MAX_NAME_LEN:
        return jsonify({"error": f"Name too long (max {_MAX_NAME_LEN} chars)."}), 400

    from clawmetry.dives_sql_safety import validate_sql
    ok, reason = validate_sql(sql)
    if not ok:
        return jsonify({"error": f"SQL rejected: {reason}"}), 400

    slug = _unique_slug(name)
    record = {
        "slug":       slug,
        "name":       name,
        "question":   question,
        "sql":        sql,
        "chart_spec": chart_spec,
        "saved_at":   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    try:
        path = os.path.join(_dives_dir(), slug + ".json")
        with open(path, "w") as f:
            json.dump(record, f)
    except OSError as e:
        return jsonify({"error": f"Save failed: {e}"}), 500
    return jsonify({"slug": slug}), 201


@bp_dives.route("/api/dives")
def api_dives_list():
    """GET → {dives: [{slug, name, question, saved_at, chart_type}]}"""
    return jsonify({"dives": _list_dives()})


@bp_dives.route("/api/dives/<slug>")
def api_dives_get(slug: str):
    """GET → dive record + re-run rows against live data."""
    record = _read_dive(slug)
    if record is None:
        return jsonify({"error": "Not found."}), 404

    sql = record.get("sql", "")
    rows: list[dict] = []
    run_error: str | None = None
    if sql:
        try:
            store = _get_store()
            rows, run_error = _execute(sql, store)
        except Exception as e:
            run_error = str(e)[:200]

    body = dict(record)
    body["rows"] = rows
    if run_error:
        body["run_error"] = run_error
    return jsonify(body)


@bp_dives.route("/api/dives/<slug>", methods=["DELETE"])
def api_dives_delete(slug: str):
    """DELETE → {deleted: slug}"""
    safe = _safe_slug(slug)
    path = os.path.join(_dives_dir(), safe + ".json")
    if not os.path.isfile(path):
        return jsonify({"error": "Not found."}), 404
    try:
        os.remove(path)
    except OSError as e:
        return jsonify({"error": f"Delete failed: {e}"}), 500
    return jsonify({"deleted": safe})
