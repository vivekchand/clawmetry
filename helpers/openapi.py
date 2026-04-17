"""helpers/openapi.py — auto-generate an OpenAPI 3.1 spec from Flask routes.

Goal: every endpoint that powers a UI tab is also queryable via API, so
integrators (Clawnify, KiloCode, custom dashboards) can build on top of
ClawMetry without screen-scraping.

Strategy:
  1. Walk app.url_map. For each rule whose path starts with `/api/`,
     synthesise a minimal OpenAPI operation: path, methods, parameters
     extracted from URL converters (`<node_id>` → string param).
  2. Pull docstring from the view_function as the operation `description`
     so the existing Python docstrings become user-facing API docs.
  3. Hand-curated `_RESPONSE_SCHEMAS` overrides the generic `{}` for the
     handful of endpoints we care about presenting cleanly (subagents,
     overview, security/posture, approvals, etc.).
  4. Serve at:
       /openapi.json  — the spec
       /api/docs      — Swagger UI (CDN-hosted, no build step)

Drop-in: import `openapi_blueprint` from this module and register it on
the Flask app. No external Python deps; Swagger UI is loaded from CDN.
"""
from __future__ import annotations

import json
import re
from flask import Blueprint, jsonify, current_app

bp_openapi = Blueprint("openapi", __name__)


# Hand-curated response schemas for the endpoints worth documenting cleanly.
# Anything not listed gets a generic `{type: object}` placeholder.
_RESPONSE_SCHEMAS: dict[str, dict] = {
    "/api/overview": {
        "type": "object",
        "properties": {
            "model": {"type": "string"},
            "sessionCount": {"type": "integer"},
            "cronCount": {"type": "integer"},
            "mainTokens": {"type": "integer"},
            "system": {"type": "array", "items": {"type": "array"}},
            "infra": {"type": "object"},
        },
    },
    "/api/subagents": {
        "type": "object",
        "properties": {
            "subagents": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "sessionId": {"type": "string"},
                        "key": {"type": "string"},
                        "displayName": {"type": "string"},
                        "status": {"type": "string",
                                   "enum": ["active", "idle", "stale", "failed"]},
                        "model": {"type": "string"},
                        "task": {"type": "string"},
                        "error": {"type": "string"},
                        "completionStatus": {"type": "string"},
                        "completionResult": {"type": "string"},
                        "tokensIn": {"type": "integer"},
                        "tokensOut": {"type": "integer"},
                        "runtime": {"type": "string"},
                        "runtimeMs": {"type": "integer"},
                    },
                },
            },
            "counts": {
                "type": "object",
                "properties": {
                    "total": {"type": "integer"},
                    "active": {"type": "integer"},
                    "idle": {"type": "integer"},
                    "stale": {"type": "integer"},
                    "failed": {"type": "integer"},
                },
            },
        },
    },
    "/api/security/posture": {
        "type": "object",
        "properties": {
            "score": {"type": "string", "description": "A–F or U (unknown)"},
            "score_color": {"type": "string"},
            "passed": {"type": "integer"},
            "failed": {"type": "integer"},
            "warnings": {"type": "integer"},
            "checks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "label": {"type": "string"},
                        "status": {"type": "string",
                                   "enum": ["pass", "warn", "fail"]},
                        "severity": {"type": "string"},
                        "detail": {"type": "string"},
                        "remediation": {"type": "string"},
                        "weight": {"type": "integer"},
                    },
                },
            },
            "snapshot_at": {"type": "string", "format": "date-time"},
        },
    },
    "/api/cloud/approvals": {
        "type": "object",
        "properties": {
            "approvals": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/Approval"},
            },
            "count": {"type": "integer"},
        },
    },
    "/api/approvals/request": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "status": {"type": "string", "enum": ["pending"]},
            "expires_at": {"type": "string", "format": "date-time"},
        },
    },
    "/api/brain-history": {
        "type": "object",
        "properties": {
            "events": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "time": {"type": "string", "format": "date-time"},
                        "source": {"type": "string"},
                        "sourceLabel": {"type": "string"},
                        "detail": {"type": "string"},
                        "color": {"type": "string"},
                    },
                },
            },
        },
    },
    "/api/usage": {
        "type": "object",
        "properties": {
            "todayCost": {"type": "number"},
            "weekCost": {"type": "number"},
            "monthCost": {"type": "number"},
            "today": {"type": "integer"},
            "month": {"type": "integer"},
            "trend": {"type": "object"},
            "billingSummary": {"type": "string"},
        },
    },
}


_COMPONENTS = {
    "schemas": {
        "Approval": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "node_id": {"type": "string"},
                "session_id": {"type": "string"},
                "tool_name": {"type": "string"},
                "args": {"type": "object"},
                "context": {"type": "string"},
                "policy_name": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["pending", "approved", "denied", "timeout", "expired"],
                },
                "requested_at": {"type": "string", "format": "date-time"},
                "expires_at":   {"type": "string", "format": "date-time"},
                "decided_at":   {"type": "string", "format": "date-time"},
                "decided_by":   {"type": "string"},
                "decision_reason": {"type": "string"},
            },
        },
        "Error": {
            "type": "object",
            "properties": {
                "error": {"type": "string"},
            },
            "required": ["error"],
        },
    },
    "securitySchemes": {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "description": (
                "Either an OpenClaw gateway token (local OSS install) or a "
                "ClawMetry cm_… key (cloud). Token can be passed in the "
                "Authorization header (`Bearer <token>`) or for cloud "
                "endpoints as `?token=<value>` query string."
            ),
        },
    },
}


_TAGS = [
    {"name": "overview",     "description": "Top-level dashboard data."},
    {"name": "sessions",     "description": "Session transcripts + sub-agent tree + spawn events."},
    {"name": "brain",        "description": "Unified activity stream (THINK/AGENT/EXEC/READ/WRITE/SPAWN…)."},
    {"name": "usage",        "description": "Tokens, cost, billing-mode hints."},
    {"name": "crons",        "description": "Cron CRUD + run history."},
    {"name": "memory",       "description": "Agent memory file explorer."},
    {"name": "security",     "description": "Posture scan + threat detection + signature catalog."},
    {"name": "approvals",    "description": "Cloud-mediated human-in-the-loop approval queue."},
    {"name": "alerts",       "description": "Alert rules + active alerts + history."},
    {"name": "cloud",        "description": "Cloud-only endpoints: per-account fleet + node detail."},
    {"name": "ingest",       "description": "Sync-daemon ingest (heartbeat, sessions, events, logs)."},
    {"name": "nemoclaw",     "description": "NeMo Guardrails governance + sandbox approval queue."},
    {"name": "fleet",        "description": "Multi-node fleet view."},
    {"name": "history",      "description": "Time-series collector (SQLite)."},
    {"name": "internal",     "description": "Internal/system endpoints (cron triggers, etc.)."},
]


def _tag_for(path: str) -> list[str]:
    p = path.lower()
    # v1 public API — clean domain tags
    if p.startswith("/api/v1/nodes"):
        return ["Nodes"]
    if p.startswith("/api/v1/sessions"):
        return ["Sessions"]
    if p.startswith("/api/v1/activity"):
        return ["Activity"]
    if p.startswith("/api/v1/usage"):
        return ["Usage"]
    if p.startswith("/api/v1/approvals") or p.startswith("/api/v1/policies") or p.startswith("/api/v1/integrations"):
        return ["Approvals"]
    if p.startswith("/api/v1/security"):
        return ["Security"]
    if p.startswith("/api/v1/account"):
        return ["Account"]
    if p.startswith("/api/v1/"):
        return ["Other"]
    # Legacy internal endpoints
    if p.startswith("/api/cloud/approvals") or "/approvals" in p or p.startswith("/approve/"):
        return ["approvals"]
    if p.startswith("/ingest/"):
        return ["ingest"]
    if p.startswith("/api/cloud/"):
        return ["cloud"]
    if "/security" in p:
        return ["security"]
    if "/subagent" in p or "/sessions" in p or "/transcript" in p or "/spawn" in p:
        return ["sessions"]
    if "/brain" in p:
        return ["brain"]
    if "/usage" in p or "/cost" in p or "/tokens" in p:
        return ["usage"]
    if "/cron" in p:
        return ["crons"]
    if "/memory" in p:
        return ["memory"]
    if "/overview" in p or p == "/api/overview":
        return ["overview"]
    if "/alerts" in p or "/budget" in p:
        return ["alerts"]
    if "/nemoclaw" in p:
        return ["nemoclaw"]
    if "/fleet" in p or "/node" in p:
        return ["fleet"]
    if "/history" in p:
        return ["history"]
    if "/internal/" in p:
        return ["internal"]
    return ["internal"]


def _flask_to_openapi_path(rule: str) -> tuple[str, list[dict]]:
    """Convert Flask `<int:id>` / `<node_id>` → OpenAPI `{id}` + parameter list."""
    params: list[dict] = []
    def repl(m: re.Match) -> str:
        spec = m.group(1)
        if ":" in spec:
            type_str, name = spec.split(":", 1)
        else:
            type_str, name = "string", spec
        ot = {"int": "integer", "float": "number", "string": "string",
              "uuid": "string", "path": "string"}.get(type_str, "string")
        params.append({
            "name": name, "in": "path", "required": True,
            "schema": {"type": ot},
        })
        return "{" + name + "}"
    new_path = re.sub(r"<([^>]+)>", repl, rule)
    return new_path, params


def build_spec(app, v1_only: bool = False) -> dict:
    """Walk the Flask url_map and assemble an OpenAPI 3.1 spec.

    When v1_only=True, only document /api/v1/* endpoints — the clean
    public API for integrators, mobile apps, and custom widgets.
    """
    paths: dict = {}
    seen: set[str] = set()
    for rule in app.url_map.iter_rules():
        path = rule.rule
        if v1_only:
            if not path.startswith("/api/v1/"):
                continue
        else:
            # Only document API endpoints + the public approve page.
            if not (path.startswith("/api/") or path.startswith("/approve/")):
                continue
        if path in seen:
            # Methods overlap on same path get merged below.
            pass
        seen.add(path)
        oapi_path, path_params = _flask_to_openapi_path(path)
        if oapi_path not in paths:
            paths[oapi_path] = {}
        view = app.view_functions.get(rule.endpoint)
        doc = (getattr(view, "__doc__", None) or "").strip()
        summary = doc.split("\n")[0][:140] if doc else rule.endpoint
        description = doc
        for method in (rule.methods or set()):
            m = method.lower()
            if m in ("head", "options"):
                continue
            tag = _tag_for(path)
            response_schema = _RESPONSE_SCHEMAS.get(path) or {"type": "object"}
            op = {
                "summary": summary,
                "description": description,
                "operationId": f"{m}_{rule.endpoint.replace('.', '_')}",
                "tags": tag,
                "parameters": list(path_params),
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {"application/json": {"schema": response_schema}},
                    },
                    "401": {
                        "description": "Unauthorized",
                        "content": {"application/json":
                                    {"schema": {"$ref": "#/components/schemas/Error"}}},
                    },
                    "404": {
                        "description": "Not found",
                        "content": {"application/json":
                                    {"schema": {"$ref": "#/components/schemas/Error"}}},
                    },
                    "500": {
                        "description": "Server error",
                        "content": {"application/json":
                                    {"schema": {"$ref": "#/components/schemas/Error"}}},
                    },
                },
                "security": [{"bearerAuth": []}],
            }
            if m == "post":
                op["requestBody"] = {
                    "required": True,
                    "content": {"application/json": {"schema": {"type": "object"}}},
                }
            paths[oapi_path][m] = op
    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": "ClawMetry API",
            "version": _detect_version(),
            "description": (
                "ClawMetry — real-time observability + control plane for "
                "OpenClaw AI agents.\n\n"
                "Every UI tab is backed by these endpoints. Build custom "
                "dashboards, integrate with KiloCode/Clawnify/internal "
                "tooling, or feed the data into your own analytics stack.\n\n"
                "Auth: Bearer token in `Authorization` header (cm_… key for "
                "cloud, gateway token for local OSS), or `?token=<value>` "
                "query string on cloud-flavored routes."
            ),
            "contact": {"name": "ClawMetry", "url": "https://clawmetry.com"},
            "license": {"name": "MIT"},
        },
        "servers": [
            {"url": "https://app.clawmetry.com", "description": "ClawMetry Cloud (production)"},
            {"url": "http://localhost:8900", "description": "Local OSS install"},
        ],
        "tags": _TAGS,
        "components": _COMPONENTS,
        "paths": paths,
    }
    return spec


def _detect_version() -> str:
    try:
        import dashboard
        return getattr(dashboard, "__version__", "?")
    except Exception:
        return "?"


@bp_openapi.route("/openapi.json")
def openapi_json():
    """Return the auto-generated OpenAPI 3.1 spec for this ClawMetry instance.

    In cloud mode (CLOUD_MODE=true or v1_only query param), only show
    the clean /api/v1/* public API. Otherwise show all endpoints.
    """
    from flask import request
    v1 = (request.args.get("v1_only") == "1"
          or getattr(current_app, '_cloud_mode', False)
          or bool(current_app.config.get("CLOUD_MODE")))
    return jsonify(build_spec(current_app, v1_only=v1))


@bp_openapi.route("/api/docs")
def swagger_ui():
    """Serve a CDN-hosted Swagger UI pointed at /openapi.json.

    No build step, no extra dep: Swagger UI's standalone bundle works
    inline. Set `deepLinking: true` so per-endpoint URLs are shareable.
    """
    html = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>ClawMetry API — Swagger</title>
<link rel="icon" href="https://clawmetry.com/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css">
<style>
  html, body { margin: 0; padding: 0; background: #0B0F1A; }
  body { font-family: -apple-system, Inter, sans-serif; }
  /* Slight dark-mode tint */
  .swagger-ui, .swagger-ui .info .title, .swagger-ui .info .description {
    color: #E2E8F0;
  }
  .swagger-ui .topbar { background: #0F1626; border-bottom: 1px solid #1E293B; }
  .swagger-ui .topbar .download-url-wrapper input { background: #0B0F1A; color: #E2E8F0; }
  .swagger-ui section.models, .swagger-ui .opblock-tag,
  .swagger-ui .opblock { background: rgba(15,22,38,0.6); border-color: #1E293B; }
  .swagger-ui .opblock .opblock-summary-method { font-weight: 700; }
</style>
</head><body>
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
<script>
  window.onload = function() {
    SwaggerUIBundle({
      url: '/openapi.json',
      dom_id: '#swagger-ui',
      deepLinking: true,
      docExpansion: 'list',
      defaultModelsExpandDepth: 1,
      tagsSorter: 'alpha',
      operationsSorter: 'alpha',
      tryItOutEnabled: true,
      persistAuthorization: true
    });
  };
</script>
</body></html>"""
    from flask import Response
    return Response(html, mimetype="text/html")
