"""routes/approval_routing.py — where each runtime's approvals get sent.

Three surfaces:

  GET/PUT /api/approvals/routing         per-runtime channel table
  POST    /api/approvals/routing/test    send a sample page to one runtime's
                                         channels (proves the wiring before
                                         a real agent is stuck waiting)
  GET     /a/<approval_id>?t=<sig>       the phone page: what the agent
                                         wants to do + Approve / Deny
  POST    /a/<approval_id>/decide        the decision writer for that page

The phone page is the fallback that makes every channel useful: Slack,
Discord, WhatsApp and email can't carry a button that talks back to a
laptop, but they can carry a link, and the link works from any device on
the same network (or Tailscale — set ``CLAWMETRY_PUBLIC_BASE``).

AUTH on the link routes is the HMAC in ``?t=`` (approval_notify.sign_link,
per-node secret in ~/.clawmetry/approval_link_secret, 0600). These two
routes are deliberately NOT loopback-only — a phone is not loopback — so
the signature is the whole wall: 128 bits, constant-time compared, scoped
to one approval id.

GET NEVER DECIDES. Mail clients and chat apps prefetch links; a GET that
approved a tool call would let a link preview run ``rm -rf``. The page
renders, the human taps, the POST decides.
"""
from __future__ import annotations

import json

from flask import Blueprint, jsonify, request, Response

from clawmetry._gate import gate

bp_approval_routing = Blueprint("approval_routing", __name__)


# ── store plumbing (daemon proxy owns the writer lock) ─────────────────────

def _rows(result) -> list:
    if isinstance(result, dict):
        result = result.get("result") or result.get("rows") or []
    return result if isinstance(result, list) else []


def _read(method: str, **kwargs):
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store
        return getattr(local_store.get_store(read_only=True), method)(**kwargs)
    except Exception:
        return None


def _find(approval_id: str):
    for r in _rows(_read("query_approvals", limit=500)):
        if str(r.get("id")) == str(approval_id):
            return r
    return None


def _write_decision(approval_id: str, decision: str, resolver: str,
                    reason: str = "") -> bool:
    try:
        from routes.local_query import local_store_via_daemon
        wrote = local_store_via_daemon(
            "update_approval_decision", approval_id=approval_id,
            decision=decision, resolver=resolver, reason=reason)
        if wrote is not None:
            return True
    except Exception:
        pass
    try:
        from clawmetry import local_store
        local_store.get_store().update_approval_decision(
            approval_id, decision, resolver, reason)
        return True
    except Exception:
        return False


# ── routing config API ─────────────────────────────────────────────────────

#: What each channel can actually do from a self-hosted node. The UI renders
#: this verbatim — no channel is allowed to imply a capability it lacks.
CHANNEL_CAPABILITY = {
    "telegram":  {"notify": True,  "decide": True,
                  "note": "Approve/Deny buttons right in the message"},
    "slack":     {"notify": True,  "decide": False,
                  "note": "Message with a one-tap decision link"},
    "discord":   {"notify": True,  "decide": False,
                  "note": "Message with a one-tap decision link"},
    "webhook":   {"notify": True,  "decide": False,
                  "note": "JSON POST to your own endpoint"},
    "pagerduty": {"notify": True,  "decide": False,
                  "note": "Triggers an incident with the decision link"},
    "whatsapp":  {"notify": True,  "decide": False,
                  "note": "Meta Cloud API or Twilio; link decides"},
    "email":     {"notify": True,  "decide": False,
                  "note": "Local SMTP; link decides"},
    "phone":     {"notify": True,  "decide": False,
                  "note": "Twilio call announces it; press-1 needs cloud"},
}


@bp_approval_routing.route("/api/approvals/routing", methods=["GET"])
@gate("approval_queue")
def api_approvals_routing_get():
    from clawmetry import approval_notify as an
    from clawmetry import approval_inbound as ai
    cfg = an.load_channel_config()
    routes = an.load_routes()
    configured = an.configured_channels(cfg)
    runtimes = _known_runtimes()
    return jsonify({
        "ok": True,
        "routing": routes,
        "channels": [
            {"key": k, "configured": k in configured,
             **CHANNEL_CAPABILITY.get(k, {})}
            for k in an.CHANNELS
        ],
        "runtimes": [{"id": r, "label": an.runtime_label(r),
                      "resolved": an.resolve_targets(r, cfg)}
                     for r in runtimes],
        "telegram_poller": ai.poller_status(),
        "link_base": an.base_url(),
    })


@bp_approval_routing.route("/api/approvals/routing", methods=["PUT"])
@gate("approval_queue")
def api_approvals_routing_put():
    from clawmetry import approval_notify as an
    body = request.get_json(silent=True) or {}
    known = set(_known_runtimes())
    unknown = [r for r in (body.get("runtimes") or {}) if r not in known]
    if unknown:
        # Never silently widen: an unknown runtime id would create a row
        # nothing ever reads, and the user would think they configured it.
        return jsonify({"ok": False,
                        "error": "unknown runtime(s): %s"
                                 % ", ".join(sorted(unknown))}), 400
    bad = [c for row in [body.get("default") or {}]
           + list((body.get("runtimes") or {}).values())
           for c in (row.get("channels") or []) if c not in an.CHANNELS]
    if bad:
        return jsonify({"ok": False,
                        "error": "unknown channel(s): %s"
                                 % ", ".join(sorted(set(bad)))}), 400
    if not an.save_routes(body):
        return jsonify({"ok": False, "error": "could not write routing"}), 500
    return jsonify({"ok": True, "routing": an.load_routes()})


@bp_approval_routing.route("/api/approvals/routing/test", methods=["POST"])
@gate("approval_queue")
def api_approvals_routing_test():
    """Deliver a sample approval page to a runtime's channels.

    Sends synchronously so the response can report exactly which channels
    accepted it — a test that returned before delivery would be useless.
    """
    from clawmetry import approval_notify as an
    body = request.get_json(silent=True) or {}
    runtime = str(body.get("runtime") or "claude_code").strip()
    sent = an.notify_pending({
        "id": "test-%s" % runtime,
        "runtime": runtime,
        "kind": "test",
        "tool_name": "Bash",
        "command": "echo 'ClawMetry approval routing test'",
        "cwd": "~",
        "policy": "routing test",
    }, blocking=True)
    targets = an.resolve_targets(runtime)
    return jsonify({"ok": bool(sent), "sent": sent, "targets": targets,
                    "hint": ("no channel configured for this runtime — add "
                             "one in Notifications first") if not targets
                            else ""})


def _known_runtimes() -> list:
    try:
        from clawmetry.entitlements import ALL_RUNTIMES
        return sorted(ALL_RUNTIMES)
    except Exception:
        return ["openclaw", "claude_code"]


# ── the phone page ─────────────────────────────────────────────────────────

def _unauthorised() -> Response:
    return Response(_page("Link expired",
                          "<p class=sub>This decision link is not valid for "
                          "this approval.</p>"),
                    status=403, mimetype="text/html")


@bp_approval_routing.route("/a/<approval_id>", methods=["GET"])
def approval_link_page(approval_id: str):
    from clawmetry import approval_notify as an
    if not an.verify_link(approval_id, request.args.get("t", "")):
        return _unauthorised()
    row = _find(approval_id)
    if row is None:
        return Response(_page("Not found",
                              "<p class=sub>This approval is no longer in "
                              "the queue.</p>"),
                        status=404, mimetype="text/html")
    status = str(row.get("status") or "pending")
    args = row.get("args") if isinstance(row.get("args"), dict) else {}
    p = an.build_payload({**row, "runtime": args.get("runtime")})
    if status != "pending":
        return Response(_page("Already decided",
                              "<p class=sub>This call was already <b>%s</b>."
                              "</p>" % _esc(status)),
                        mimetype="text/html")
    return Response(_decide_page(p, request.args.get("t", ""),
                                 request.args.get("d", "")),
                    mimetype="text/html")


@bp_approval_routing.route("/a/<approval_id>/decide", methods=["POST"])
def approval_link_decide(approval_id: str):
    from clawmetry import approval_notify as an
    token = (request.form.get("t") or request.args.get("t")
             or (request.get_json(silent=True) or {}).get("t") or "")
    if not an.verify_link(approval_id, token):
        return _unauthorised()
    decision = str(request.form.get("decision")
                   or (request.get_json(silent=True) or {}).get("decision")
                   or "").strip().lower()
    if decision not in ("approve", "deny"):
        return _unauthorised()
    row = _find(approval_id)
    if row is None:
        return Response(_page("Not found", "<p class=sub>Gone.</p>"),
                        status=404, mimetype="text/html")
    status = str(row.get("status") or "pending")
    if status != "pending":
        return Response(_page("Already decided",
                              "<p class=sub>This call was already <b>%s</b>."
                              "</p>" % _esc(status)),
                        mimetype="text/html")
    ok = _write_decision(approval_id, decision, "link",
                         "decided from a notification link")
    if not ok:
        return Response(_page("Could not save",
                              "<p class=sub>The approvals store did not "
                              "accept the decision. Try the dashboard.</p>"),
                        status=500, mimetype="text/html")
    try:
        an.notify_resolved(approval_id, decision, "link")
    except Exception:
        pass
    word = "Approved" if decision == "approve" else "Denied"
    return Response(_page(word,
                          "<p class=sub>%s. You can close this page.</p>"
                          % ("The agent is continuing"
                             if decision == "approve"
                             else "The call was blocked")),
                    mimetype="text/html")


def _esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _page(title: str, body_html: str) -> str:
    return """<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>%s · ClawMetry</title><style>
:root{color-scheme:dark light}
body{margin:0;font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
background:#0b0f17;color:#e6edf3;display:flex;min-height:100vh;
align-items:center;justify-content:center;padding:20px}
.card{background:#131a26;border:1px solid #223047;border-radius:16px;
padding:26px;max-width:520px;width:100%%}
h1{font-size:20px;margin:0 0 10px}
.sub{color:#8b9bb4;font-size:14px;margin:0 0 18px}
pre{background:#0b1220;border:1px solid #223047;border-radius:10px;padding:14px;
overflow:auto;font-size:13px;white-space:pre-wrap;word-break:break-word;margin:0 0 16px}
.meta{color:#8b9bb4;font-size:12px;margin:0 0 20px}
.row{display:flex;gap:12px}
button{flex:1;padding:16px;border-radius:12px;border:0;font-size:16px;
font-weight:600;cursor:pointer}
.ok{background:#16a34a;color:#fff}.no{background:#dc2626;color:#fff}
</style></head><body><div class=card><h1>%s</h1>%s</div></body></html>
""" % (_esc(title), _esc(title), body_html)


def _decide_page(p: dict, token: str, preselect: str) -> str:
    meta_bits = [p["runtime_label"], p["node"]]
    if p["cwd"]:
        meta_bits.append(p["cwd"])
    if p["policy"]:
        meta_bits.append("rule: " + p["policy"])
    form = (
        "<p class=sub>%s wants to run:</p>"
        "<pre>%s</pre>"
        "<p class=meta>%s</p>"
        "<form method=post action=\"/a/%s/decide\" class=row>"
        "<input type=hidden name=t value=\"%s\">"
        "<button class=ok name=decision value=approve>Approve</button>"
        "<button class=no name=decision value=deny>Deny</button>"
        "</form>"
        % (_esc(p["runtime_label"]),
           _esc(p["command"] or p["tool_name"]),
           _esc(" · ".join(meta_bits)),
           _esc(p["id"]), _esc(token))
    )
    if preselect in ("approve", "deny"):
        form += ("<p class=meta>Tap %s to confirm — links never decide on "
                 "their own.</p>" % preselect)
    return _page("Approval needed", form)
