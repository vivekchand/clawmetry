"""routes/public_api.py -- the keyed, cross-origin read API custom UIs use.

Requirement: "Build your own UI: a keyed, scoped read API for custom
dashboards" (64c10afd-038d-4fde-9c55-ddca80aaff1e), blueprint
0ea7523c-12b5-4033-84ea-bf1f46e20d70.

This is the "build your own UI" surface (docs/BUILD_YOUR_OWN_UI.md). It
serves the declared ``q/1`` query contract to anything holding a scoped
API key: a page vibe-coded on v0 or Lovable, a Grafana-ish panel, a
terminal script, an agent with curl.

    GET /api/q/1                     what this key can read
    GET /api/q/1/llms.txt            the whole API, written for an agent
    GET /api/q/1/<shape>?<args>      one query

Every response is JSON. Every shape, arg and default comes from
``clawmetry/query_contract.py`` and every query goes through
``routes.local_query._dispatch`` -- the same code path the dashboard
uses, so there is no second SQL surface to keep correct and no way for a
key to reach a query the contract does not declare.

What makes this different from the rest of the dashboard
--------------------------------------------------------
Everywhere else, a request from ``127.0.0.1`` is trusted, because a
local tool talking to itself is the normal case. Here it is not, and
that inversion is the entire security design:

* **A key is always required.** Loopback earns nothing. Without a key
  this surface behaves as if it does not exist.
* **CORS is per key, never global.** ``Access-Control-Allow-Origin`` is
  echoed only for an origin the key holder named when they created the
  key. There is no wildcard and no way to ask for one. This matters more
  than it looks: any page in any tab can already send a request to
  ``127.0.0.1:8900``, and the only reason that has been harmless is that
  the browser will not let the page read the reply. That protection is
  what we are selectively removing, one named origin at a time.
* **Read only.** The dispatch table is the q/1 read contract. Nothing
  here can pause, stop or kill an agent, and nothing here writes. This
  adds no entry to the control-plane surfaces listed in CLAUDE.md: a key
  cannot cause a write, so the "no surprise writes" rule has nothing to
  bite on here.
* **GET only.** Every q/1 arg is a scalar, so nothing needs a body.
  Being GET-only means this API can never be the target of a
  cross-origin write, which removes a whole class of question.
"""

from __future__ import annotations

import logging
import os
import re
import time
from collections import deque
from flask import Blueprint, Response, jsonify, request

from clawmetry import apikeys
from clawmetry.query_contract import (
    CONTRACT_VERSION,
    QUERY_CONTRACT,
    SCOPE_DOC,
    SCOPES,
    STATUS_LIVE,
)

logger = logging.getLogger("clawmetry.routes.public_api")

bp_public_api = Blueprint("public_api", __name__)

#: Requests per key per minute. Generous enough for a page polling every
#: second with a few panels, low enough that a runaway loop in someone's
#: custom UI cannot pin the daemon's DuckDB connection (see the CPU
#: budget in FLYWHEEL.md 1e).
RATE_LIMIT_PER_MIN = int(os.environ.get("CLAWMETRY_API_RATE_LIMIT", "240") or 240)

_RATE: dict = {}
_RATE_WINDOW_SEC = 60.0

#: Flask stashes the resolved key record here so ``_add_cors`` can echo
#: the right origin after the view has run.
_G_KEY = "_cm_api_key_record"

# Structural guard for browser Origin values: scheme://host[:port].
# Applied in _add_cors BEFORE comparing against stored origins so that
# structurally invalid values are rejected early.
_ORIGIN_RE = re.compile(r"^https?://[A-Za-z0-9._-]+(:\d{1,5})?$")

# Same pattern for the Host header in llms.txt: RFC 3986 host + optional port.
_HOST_RE = re.compile(r"^[A-Za-z0-9._-]+(:\d{1,5})?$")


def _rate_limited(key_id: str) -> bool:
    """True when this key has spent its minute. Sliding window, in memory.

    Per process and not shared with the daemon, which is the honest
    scope: this is a runaway-loop guard for a local API, not a billing
    meter.
    """
    if RATE_LIMIT_PER_MIN <= 0:
        return False
    now = time.monotonic()
    hits = _RATE.setdefault(key_id, deque())
    cutoff = now - _RATE_WINDOW_SEC
    while hits and hits[0] < cutoff:
        hits.popleft()
    if len(hits) >= RATE_LIMIT_PER_MIN:
        return True
    hits.append(now)
    return False


def _err(status: int, message: str, **extra):
    """A failure a person can act on.

    Never an upstream code on its own: the body always carries a
    sentence saying what happened and what to do next, because these
    land in someone's browser console while they are building.
    """
    body = {"error": message, "contract": CONTRACT_VERSION}
    body.update(extra)
    return jsonify(body), status  # codeql[py/stack-trace-exposure]


# ── auth + CORS ─────────────────────────────────────────────────────────

def _presented_key() -> str:
    """The key on this request. ``Authorization: Bearer`` is the documented
    form; ``X-ClawMetry-Key`` exists for clients that cannot set it."""
    auth = (request.headers.get("Authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return (request.headers.get("X-ClawMetry-Key") or "").strip()


def _authenticate():
    """``(record, None)`` on success, ``(None, response)`` on failure."""
    presented = _presented_key()
    if not presented:
        return None, _err(
            401,
            "This API needs a key. Create one with: clawmetry key create "
            "--name my-ui --scope read:metrics --origin https://example.com, "
            "then send it as: Authorization: Bearer cmk_...",
            docs="/api/q/1/llms.txt",
        )
    record = apikeys.verify(presented)
    if not record:
        return None, _err(
            401,
            "That key is not valid on this machine. It may have been revoked, "
            "or it may belong to a different ClawMetry install. List the keys "
            "this machine knows with: clawmetry key list",
            docs="/api/q/1/llms.txt",
        )
    if _rate_limited(str(record.get("id"))):
        return None, _err(
            429,
            f"This key has made more than {RATE_LIMIT_PER_MIN} requests in the "
            "last minute and is being throttled. Poll less often, or raise "
            "CLAWMETRY_API_RATE_LIMIT on the machine running ClawMetry.",
        )
    from flask import g

    setattr(g, _G_KEY, record)
    return record, None


@bp_public_api.after_request
def _add_cors(response):
    """Echo CORS headers for an origin THIS key authorised, and no other.

    Blueprint-scoped on purpose: nothing else in the dashboard gains a
    CORS header from this file existing.

    CWE-113 design: the Access-Control-Allow-Origin value MUST come from
    the key store, never from the request Origin header. The implementation
    achieves this by fetching stored origins WITHOUT passing the request
    header to any helper function -- origin never flows into stored_origins,
    so matched (assigned from stored_origins) is provably not tainted.
    """
    from flask import g

    origin = (request.headers.get("Origin") or "").strip()
    if not origin:
        return response  # not a browser; nothing to negotiate
    if not (request.path or "").startswith("/api/q/"):
        # Belt and braces. Every rule in this blueprint is under /api/q/
        # today, and this makes sure a route added here later cannot
        # inherit cross-origin readability by accident. Key MANAGEMENT
        # (minting, listing, revoking) deliberately lives in its own
        # module, routes/apikeys_admin.py, behind the dashboard's own
        # same-origin gate.
        return response

    # Structural guard: reject structurally invalid origin values before
    # any comparison with stored data. This is an early exit, not the
    # CWE-113 sanitizer (the sanitizer is the stored-value lookup below).
    _m = _ORIGIN_RE.fullmatch(origin.rstrip("/"))
    if not _m:
        return response

    record = getattr(g, _G_KEY, None)

    # Fetch stored canonical origins WITHOUT passing the request-supplied
    # origin to any function. This severs the CodeQL CWE-113 taint chain:
    # stored_origins comes entirely from the key store (no request input),
    # so any value selected from it is provably not derived from user input.
    if record is not None:
        stored_origins = list(record.get("origins") or [])
    else:
        # Preflight: no key presented yet. Check whether the origin is named
        # by any live key. apikeys.all_live_origins() takes no user input.
        stored_origins = apikeys.all_live_origins()

    # Compare the sanitized origin string against each stored canonical.
    # The header value is assigned from stored_origins (the key store),
    # not from the request header or any value derived from it.
    safe_origin = _m.group(0)
    matched = None
    for _stored in stored_origins:
        if str(_stored).lower() == safe_origin.lower():
            matched = str(_stored)
            break
    if not matched:
        return response

    response.headers["Access-Control-Allow-Origin"] = matched
    response.headers["Vary"] = "Origin"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = (
        "Authorization, X-ClawMetry-Key, Content-Type"
    )
    response.headers["Access-Control-Max-Age"] = "600"
    return response


# CORS preflight needs no view of its own: Flask answers OPTIONS for every
# rule below automatically, and ``_add_cors`` decides whether that answer
# carries permission. A preflight arrives with no Authorization header, so
# the only question it can answer is "has the user authorised this origin
# for any live key" -- and an origin nobody named gets no header, which is
# what makes the browser abandon the request before it is ever sent.


# ── the index ───────────────────────────────────────────────────────────

def _shape_spec(name: str) -> dict:
    spec = QUERY_CONTRACT[name]
    return {
        "shape": name,
        "scope": spec["scope"],
        "description": spec["doc"],
        "args": {
            arg: dict(meta, required=bool(meta.get("required")))
            for arg, meta in spec["args"].items()
        },
        "url": f"/api/q/1/{name}",
    }


@bp_public_api.route("/api/q/1", methods=["GET"])
def q_index():
    """What this key can read. The first call a custom UI should make."""
    record, failure = _authenticate()
    if failure:
        return failure
    granted = sorted(apikeys.granted_shapes(record))
    return jsonify({
        "contract": CONTRACT_VERSION,
        "key": {
            "id": record.get("id"),
            "name": record.get("name"),
            "scopes": record.get("scopes") or [],
            "origins": record.get("origins") or [],
        },
        "scopes": [
            {"scope": s, "grants": SCOPE_DOC[s], "held": s in (record.get("scopes") or [])}
            for s in SCOPES
        ],
        "shapes": [_shape_spec(n) for n in granted],
        "docs": "/api/q/1/llms.txt",
    })


# ── the agent-readable guide ────────────────────────────────────────────

def _llms_txt(record: dict) -> str:
    """The whole API as plain text, generated from the contract.

    Written to be pasted into a coding agent. It is generated rather
    than authored so it can never describe a shape that is not served,
    and it is scoped to the presented key so an agent is never told
    about a query it will get a 403 for.
    """
    granted = sorted(apikeys.granted_shapes(record))
    # Validate the Host header against an explicit allowlist pattern before
    # using it in the response body (CWE-113 sanitizer: RFC 3986 host + port
    # chars only). Using request.host (just the netloc) rather than
    # request.host_url avoids a urlparse intermediate that CodeQL cannot
    # see through for taint tracking.
    _host_hdr = (request.host or "").strip()
    _m = _HOST_RE.fullmatch(_host_hdr)
    if _m:
        _scheme = "https" if request.is_secure else "http"
        # Use _m.group(0) -- the matched text -- not _host_hdr (the raw tainted
        # string). CodeQL tracks taint through string variables; a regex match
        # group is a recognised sanitizer break in the data flow.
        host = f"{_scheme}://{_m.group(0)}"
    else:
        host = "http://127.0.0.1:8900"
    lines = [
        "# ClawMetry query API (%s)" % CONTRACT_VERSION,
        "",
        "Read-only telemetry for AI agent runs on this machine: sessions,",
        "tokens, cost, tool calls, traces. Use it to build a custom UI.",
        "",
        "## Auth",
        "",
        "Send the key on every request:",
        "",
        "    Authorization: Bearer <your cmk_ key>",
        "",
        "All requests are GET. All responses are JSON. Errors are",
        '{"error": "<a sentence>"} with a 4xx status.',
        "",
        "## Base URL",
        "",
        "    %s/api/q/1" % host,
        "",
        "## Response shape",
        "",
        "Row-returning queries answer:",
        "",
        '    {"shape": "sessions", "rows": [...], "count": 12,',
        '     "contract": "q/1", "elapsed_ms": 8}',
        "",
        "`health`, `agent_graph`, `transcript_page` and `similar_sessions`",
        "answer an object instead of `rows`. Read `shape` to tell them apart.",
        "",
        "## Queries this key can make",
        "",
    ]
    for name in granted:
        spec = QUERY_CONTRACT[name]
        lines.append("### GET /api/q/1/%s" % name)
        lines.append("")
        lines.append(spec["doc"])
        lines.append("")
        if spec["args"]:
            lines.append("Query parameters:")
            for arg, meta in spec["args"].items():
                bits = []
                if meta.get("required"):
                    bits.append("required")
                if "default" in meta:
                    bits.append("default %s" % meta["default"])
                if "lo" in meta and "hi" in meta:
                    bits.append("%s..%s" % (meta["lo"], meta["hi"]))
                suffix = (" (%s)" % ", ".join(bits)) if bits else ""
                lines.append("  - %s%s" % (arg, suffix))
        else:
            lines.append("No parameters.")
        lines.append("")
    missing = [s for s in SCOPES if s not in (record.get("scopes") or [])]
    if missing:
        lines += [
            "## Not available to this key",
            "",
            "This key does not hold:",
            "",
        ]
        for s in missing:
            lines.append("  - %s: %s" % (s, SCOPE_DOC[s]))
        lines += [
            "",
            "The person running ClawMetry can issue a key with more scopes:",
            "",
            "    clawmetry key create --name my-ui --scope %s --origin <site>"
            % " --scope ".join(list((record.get("scopes") or [])) + missing[:1]),
            "",
        ]
    lines += [
        "## Notes",
        "",
        "- Timestamps in `since` / `until` are ISO 8601, e.g. 2026-09-01T00:00:00Z.",
        "- `limit` is clamped to the range shown; asking for more is not an error.",
        "- On a free plan, `events` returns the last 24 hours and the response",
        "  carries `capped_at_24h: true`. Other queries are not time-capped.",
        "- The key is a secret. Put it in a server-side env var where you can;",
        "  if it must live in the browser, scope it to `read:metrics`.",
        "",
    ]
    return "\n".join(lines)


@bp_public_api.route("/api/q/1/llms.txt", methods=["GET"])
def q_llms_txt():
    """The API, written for a coding agent to read in one pass."""
    record, failure = _authenticate()
    if failure:
        return failure
    return Response(_llms_txt(record), mimetype="text/plain; charset=utf-8")


# ── the query ───────────────────────────────────────────────────────────

@bp_public_api.route("/api/q/1/<shape>", methods=["GET"])
def q_shape(shape: str):
    """Run one declared q/1 query and return its rows."""
    record, failure = _authenticate()
    if failure:
        return failure

    spec = QUERY_CONTRACT.get(shape)
    if spec is None or spec["status"] != STATUS_LIVE:
        # A planned-but-unserved shape and a typo get the same answer on
        # purpose: the caller's next step is identical either way.
        # Do NOT reflect `shape` here -- it is unvalidated user input at this
        # point (it was not found in the contract), so echoing it is a
        # reflected-content sink. Direct the caller to GET /api/q/1 instead.
        return _err(
            404,
            "There is no such query. Ask GET /api/q/1 for the list "
            "this key can run.",
            docs="/api/q/1/llms.txt",
        )
    if shape not in apikeys.granted_shapes(record):
        needed = spec["scope"]
        return _err(
            403,
            f"This key cannot read {shape!r}. It needs the {needed} scope "
            f"({SCOPE_DOC[needed]}) and holds "
            f"{', '.join(record.get('scopes') or []) or 'none'}. Issue a new "
            f"key with: clawmetry key create --name my-ui --scope {needed} "
            "--origin <your site>",
            required_scope=needed,
            held_scopes=record.get("scopes") or [],
        )

    from routes import local_query as _lq

    try:
        args = _lq._coerce_args(shape, request.args.to_dict())
    except ValueError:
        # _coerce_args raises only for a missing required argument. The
        # sentence is built from the CONTRACT rather than from the
        # exception: the contract already declares which arguments are
        # required, so the message is both more consistent across queries
        # and free of exception-derived text reaching a caller.
        needed = [a for a, m in spec["args"].items() if m.get("required")]
        missing = [a for a in needed
                   if not (request.args.get(a) or "").strip()] or needed
        return _err(
            400,
            f"{shape} needs {', '.join(missing)}. Ask GET /api/q/1 for every "
            "argument this query takes.",
            missing_args=missing,
        )

    capped = False
    if shape == "events":
        # Same retention cap the dashboard's own /api/local/events applies
        # (issue #1448): free plans see the last 24h of raw events. Doing
        # it here too means a custom UI and the dashboard never disagree
        # about how much history exists.
        capped = _lq._apply_24h_cap(args)

    started = time.monotonic()
    try:
        body = _lq._dispatch(shape, args)
    except Exception as exc:
        # `shape` came off the URL. It has been validated against the
        # contract by now, but the validated thing to log is the contract's
        # OWN key rather than the request string that matched it: a log line
        # built from request text is a log-injection sink even when the
        # value turned out to be legitimate.
        logger.warning("public api: %s failed for key %s: %s",
                       QUERY_CONTRACT[shape]["backing"], record.get("id"), exc)
        # The upstream message can carry a DuckDB path or a column name.
        # Neither helps the person building a UI, and both are ours.
        return _err(
            503,
            "ClawMetry could not read its local store just now. This is "
            "usually the sync daemon restarting; try again in a moment. If it "
            "persists, run: clawmetry doctor",
        )

    out = {k: v for k, v in body.items() if not k.startswith("_")}
    out["shape"] = shape
    out["contract"] = CONTRACT_VERSION
    out["elapsed_ms"] = int((time.monotonic() - started) * 1000)
    if shape == "events":
        out["capped_at_24h"] = capped
    apikeys.touch(str(record.get("id")))
    return jsonify(out)
