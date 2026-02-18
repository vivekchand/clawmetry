"""Minimal Flask backend for ClawMetry landing - serves static files + email subscribe via Resend.
Includes admin panel for inbox, subscribers, copy events."""
import os
import re
import json
import sqlite3
import hashlib
import logging
import sys
import time
import secrets
from datetime import datetime, timezone
from functools import wraps

import requests
from flask import Flask, request, jsonify, send_from_directory, make_response, redirect, url_for, session, render_template_string

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "clawmetry-secret-key-2026-xk9m")

# Force logs to stdout for Cloud Run
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("clawmetry")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "clawmetry-admin-2026")
DB_PATH = "/tmp/clawmetry.db"

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "re_jWLL59fj_PBctxiwxDLFiWjBZ9MiJ4ems")
RESEND_AUDIENCE_ID = os.environ.get("RESEND_AUDIENCE_ID", "48212e72-0d6c-489c-90c3-85a03a52d54c")
FROM_EMAIL = "ClawMetry <hello@clawmetry.com>"
UPDATES_EMAIL = "ClawMetry Updates <updates@clawmetry.com>"
NOTIFY_SECRET = os.environ.get("NOTIFY_SECRET", "clawmetry-notify-2026")

VIVEK_EMAIL = "vivekchand19@gmail.com"
RESEND_HEADERS = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}

# ─── Database ───────────────────────────────────────────────────────────────

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS emails_received (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_email TEXT,
            from_name TEXT,
            to_email TEXT,
            subject TEXT,
            body_html TEXT,
            body_text TEXT,
            received_at TEXT DEFAULT (datetime('now')),
            read INTEGER DEFAULT 0,
            replied INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS emails_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            to_email TEXT,
            subject TEXT,
            body_html TEXT,
            sent_at TEXT DEFAULT (datetime('now')),
            in_reply_to INTEGER REFERENCES emails_received(id)
        );
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            source TEXT,
            utm_data TEXT,
            location TEXT,
            ip TEXT,
            browser TEXT,
            subscribed_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS copy_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tab TEXT,
            command TEXT,
            source TEXT,
            utm_data TEXT,
            location TEXT,
            ip TEXT,
            browser TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    db.commit()
    db.close()

init_db()

# ─── Admin Auth ─────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated

# ─── Admin Templates ────────────────────────────────────────────────────────

ADMIN_BASE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} — ClawMetry Admin</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0B0F1A;--surface:#111827;--border:#1F2937;--text:#E5E7EB;--muted:#9CA3AF;--accent:#E5443A;--accent-hover:#ff5a50}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
a{color:var(--accent);text-decoration:none}a:hover{color:var(--accent-hover)}
.top-nav{background:var(--surface);border-bottom:1px solid var(--border);padding:12px 24px;display:flex;align-items:center;gap:24px;flex-wrap:wrap}
.top-nav .brand{font-weight:700;font-size:18px;color:var(--accent)}
.top-nav a{color:var(--muted);font-size:14px;font-weight:500}
.top-nav a:hover,.top-nav a.active{color:#fff}
.container{max-width:1100px;margin:0 auto;padding:24px 16px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:24px}
.stat{text-align:center}.stat h3{font-size:32px;color:var(--accent)}.stat p{color:var(--muted);font-size:13px;margin-top:4px}
table{width:100%;border-collapse:collapse;font-size:14px}
th{text-align:left;color:var(--muted);font-weight:500;padding:8px 12px;border-bottom:1px solid var(--border)}
td{padding:10px 12px;border-bottom:1px solid var(--border)}
tr:hover{background:rgba(255,255,255,.02)}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
.badge-unread{background:var(--accent);color:#fff}.badge-read{background:var(--border);color:var(--muted)}
.btn{display:inline-block;padding:8px 20px;border-radius:8px;border:none;cursor:pointer;font-size:14px;font-weight:500;font-family:inherit}
.btn-primary{background:var(--accent);color:#fff}.btn-primary:hover{background:var(--accent-hover)}
.btn-outline{border:1px solid var(--border);color:var(--text);background:transparent}.btn-outline:hover{border-color:var(--accent)}
input[type=text],input[type=email],input[type=password],textarea{width:100%;padding:10px 14px;border-radius:8px;border:1px solid var(--border);background:var(--bg);color:var(--text);font-family:inherit;font-size:14px}
input:focus,textarea:focus{outline:none;border-color:var(--accent)}
label{display:block;color:var(--muted);font-size:13px;margin-bottom:4px;margin-top:12px}
.email-body{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:16px;margin:16px 0;overflow:auto;max-height:500px}
.email-body img{max-width:100%}
.flash{padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:14px}
.flash-success{background:#065f46;color:#6ee7b7}.flash-error{background:#7f1d1d;color:#fca5a5}
.empty{text-align:center;padding:40px;color:var(--muted)}
</style>
</head>
<body>
<nav class="top-nav">
  <span class="brand">🦞 ClawMetry</span>
  <a href="/admin" class="{{ 'active' if active=='dash' }}">Dashboard</a>
  <a href="/admin/inbox" class="{{ 'active' if active=='inbox' }}">Inbox</a>
  <a href="/admin/compose" class="{{ 'active' if active=='compose' }}">Compose</a>
  <a href="/admin/sent" class="{{ 'active' if active=='sent' }}">Sent</a>
  <a href="/admin/subscribers" class="{{ 'active' if active=='subs' }}">Subscribers</a>
  <a href="/admin/events" class="{{ 'active' if active=='events' }}">Events</a>
  <a href="/admin/logout" style="margin-left:auto">Logout</a>
</nav>
<div class="container">
{% for cat, msg in get_flashed_messages(with_categories=true) %}
<div class="flash flash-{{ cat }}">{{ msg }}</div>
{% endfor %}
{{ content }}
</div>
</body></html>
"""

LOGIN_PAGE = """
<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login — ClawMetry Admin</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#0B0F1A;color:#E5E7EB;display:flex;align-items:center;justify-content:center;min-height:100vh}
.box{background:#111827;border:1px solid #1F2937;border-radius:16px;padding:40px;width:360px;text-align:center}
h1{font-size:20px;margin-bottom:24px}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #1F2937;background:#0B0F1A;color:#E5E7EB;font-size:14px;margin-bottom:16px}
button{width:100%;padding:12px;border-radius:8px;border:none;background:#E5443A;color:#fff;font-size:14px;font-weight:600;cursor:pointer}
.err{color:#fca5a5;font-size:13px;margin-bottom:12px}
</style></head><body>
<div class="box">
<h1>🦞 ClawMetry Admin</h1>
{% if error %}<p class="err">{{ error }}</p>{% endif %}
<form method="POST"><input type="password" name="password" placeholder="Password" autofocus><button type="submit">Login</button></form>
</div></body></html>
"""

# ─── Helpers ─────────────────────────────────────────────────────────────────

WELCOME_HTML = """\
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:560px;margin:0 auto;color:#1a1a2e;">
  <div style="text-align:center;padding:32px 0 24px;">
    <span style="font-size:48px;">&#x1F99E;</span>
    <h1 style="font-size:24px;margin:12px 0 0;">Welcome to ClawMetry</h1>
  </div>
  <p>Thanks for subscribing! You're now on the list for release updates.</p>
  <p><strong>What is ClawMetry?</strong><br>
  A free, open-source real-time observability dashboard for AI agents. See token costs, cron jobs, sub-agents, memory files, and session history in one place.</p>
  <div style="background:#f4f4f8;border-radius:8px;padding:16px;margin:20px 0;font-family:'Courier New',monospace;font-size:14px;">
    <span style="color:#888;">$</span> curl -fsSL https://clawmetry.com/install.sh | bash
  </div>
  <p>
    <a href="https://github.com/vivekchand/clawmetry" style="color:#E5443A;">GitHub</a> |
    <a href="https://pypi.org/project/clawmetry/" style="color:#E5443A;">PyPI</a> |
    <a href="https://clawmetry.com" style="color:#E5443A;">Website</a>
  </p>
  <p style="color:#888;font-size:13px;margin-top:32px;border-top:1px solid #eee;padding-top:16px;">
    We'll email you on major releases only. No spam. Ever.
  </p>
</div>
"""


def _resend_post(path, payload):
    try:
        r = requests.post(f"https://api.resend.com{path}", headers=RESEND_HEADERS, json=payload, timeout=10)
        return r.status_code in (200, 201), r.json() if r.content else {}
    except Exception as e:
        return False, {"error": str(e)}


def _resend_get(path):
    try:
        r = requests.get(f"https://api.resend.com{path}", headers=RESEND_HEADERS, timeout=10)
        return r.json() if r.content else {}
    except Exception:
        return {}


def send_welcome_email(email):
    return _resend_post("/emails", {
        "from": FROM_EMAIL, "to": [email],
        "subject": "Welcome to ClawMetry \U0001f99e", "html": WELCOME_HTML,
    })


def _get_visitor_info(req):
    ip = req.headers.get("X-Forwarded-For", req.headers.get("X-Real-IP", req.remote_addr))
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    ua = req.headers.get("User-Agent", "Unknown")
    referer = req.headers.get("Referer", "Direct")
    location = "Unknown"
    try:
        geo = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2).json()
        loc = ", ".join(filter(None, [geo.get("city",""), geo.get("region",""), geo.get("country_name","")]))
        if loc: location = loc
    except Exception:
        pass
    return {"ip": ip, "user_agent": ua, "referer": referer, "location": location}


def _format_source(utm, referer):
    if not utm:
        if referer and referer != "Direct": return f"Referer: {referer}"
        return "Direct / Unknown"
    source = utm.get("utm_source",""); medium = utm.get("utm_medium",""); campaign = utm.get("utm_campaign","")
    if utm.get("gclid") or utm.get("gad_source"): return f"Google Ads ({campaign})" if campaign else "Google Ads"
    if utm.get("fbclid"): return "Facebook/Meta Ads"
    if source: return " / ".join(filter(None, [source, medium, campaign]))
    return "Direct / Unknown"


def _utm_html(utm):
    if not utm: return ""
    rows = "".join(f"<p><strong>{k}:</strong> {v}</p>" for k, v in utm.items() if k != "landing_url")
    landing = utm.get("landing_url","")
    if landing: rows += f"<p><strong>Landing URL:</strong> <a href='{landing}'>{landing[:80]}</a></p>"
    return rows


def notify_vivek(subject, body_html):
    try:
        _resend_post("/emails", {"from": FROM_EMAIL, "to": [VIVEK_EMAIL], "subject": subject, "html": body_html})
    except Exception as e:
        log.info(f"[notify_vivek] {e}")


def add_contact(email):
    return _resend_post(f"/audiences/{RESEND_AUDIENCE_ID}/contacts", {"email": email, "unsubscribed": False})


def get_all_contacts():
    data = _resend_get(f"/audiences/{RESEND_AUDIENCE_ID}/contacts")
    return [c for c in data.get("data", []) if not c.get("unsubscribed")]


def _render_admin(title, content_html, active=""):
    from flask import get_flashed_messages
    return render_template_string(ADMIN_BASE, title=title, content=content_html, active=active,
                                   get_flashed_messages=get_flashed_messages)


# ─── Public API Routes ──────────────────────────────────────────────────────

@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Invalid email"}), 400

    log.info(f"[subscribe] {email}")
    ok, resp = add_contact(email)
    if not ok:
        return jsonify({"error": "Failed to subscribe. Try again."}), 500

    send_welcome_email(email)
    time.sleep(1)

    try:
        visitor = _get_visitor_info(request)
        utm = data.get("utm", {})
        source = _format_source(utm, visitor['referer'])

        # Store in SQLite
        db = get_db()
        db.execute("INSERT INTO subscribers (email, source, utm_data, location, ip, browser) VALUES (?,?,?,?,?,?)",
                   (email, source, json.dumps(utm), visitor['location'], visitor['ip'], visitor['user_agent'][:200]))
        db.commit(); db.close()

        notify_vivek(
            f"🦞 New ClawMetry subscriber: {email} [{source}]",
            f"""<div style="font-family:sans-serif;max-width:500px;">
            <h2>New Subscriber!</h2>
            <p><strong>Email:</strong> {email}</p>
            <p style="font-size:18px;color:#E5443A;"><strong>Source:</strong> {source}</p>
            <p><strong>Location:</strong> {visitor['location']}</p>
            <p><strong>IP:</strong> {visitor['ip']}</p>
            <p><strong>Browser:</strong> {visitor['user_agent'][:120]}</p>
            {_utm_html(utm)}
            </div>"""
        )
    except Exception as e:
        log.error(f"[subscribe] {e}", exc_info=True)

    return jsonify({"ok": True, "message": "Subscribed!"})


@app.route("/api/copy-track", methods=["POST"])
def copy_track():
    data = request.get_json(silent=True) or {}
    tab = data.get("tab", "unknown"); command = data.get("command", ""); utm = data.get("utm", {})
    visitor = _get_visitor_info(request)
    source = _format_source(utm, visitor['referer'])

    # Store in SQLite
    try:
        db = get_db()
        db.execute("INSERT INTO copy_events (tab, command, source, utm_data, location, ip, browser) VALUES (?,?,?,?,?,?,?)",
                   (tab, command, source, json.dumps(utm), visitor['location'], visitor['ip'], visitor['user_agent'][:200]))
        db.commit(); db.close()
    except Exception as e:
        log.error(f"[copy-track] db error: {e}")

    notify_vivek(
        f"🦞 Install command copied ({tab}) [{source}]",
        f"""<div style="font-family:sans-serif;max-width:500px;">
        <h2>Install Command Copied!</h2>
        <p><strong>Tab:</strong> {tab}</p><p><strong>Command:</strong> <code>{command}</code></p>
        <p style="font-size:18px;color:#E5443A;"><strong>Source:</strong> {source}</p>
        <p><strong>Location:</strong> {visitor['location']}</p>
        <p><strong>IP:</strong> {visitor['ip']}</p>
        </div>"""
    )
    return jsonify({"ok": True})


@app.route("/api/notify", methods=["POST"])
def notify():
    if request.headers.get("X-Notify-Secret") != NOTIFY_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    version = data.get("version", "")
    changes = data.get("changes", "")
    subject = data.get("subject") or f"ClawMetry {version} released \U0001f680"
    if not version:
        return jsonify({"error": "version is required"}), 400

    changes_html = "".join(f"<li>{line.lstrip('- ')}</li>" for line in changes.strip().split("\n") if line.strip())
    html = f"""\
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:560px;margin:0 auto;color:#1a1a2e;">
  <div style="text-align:center;padding:32px 0 24px;"><span style="font-size:48px;">&#x1F680;</span>
    <h1 style="font-size:24px;margin:12px 0 0;">ClawMetry {version}</h1></div>
  <p>A new version of ClawMetry is out!</p>
  {"<h3>What's new:</h3><ul>" + changes_html + "</ul>" if changes_html else ""}
  <div style="background:#f4f4f8;border-radius:8px;padding:16px;margin:20px 0;font-family:'Courier New',monospace;font-size:14px;">
    <span style="color:#888;">$</span> pip install --upgrade clawmetry</div>
  <p><a href="https://github.com/vivekchand/clawmetry/releases" style="color:#E5443A;">Release Notes</a> |
    <a href="https://pypi.org/project/clawmetry/" style="color:#E5443A;">PyPI</a></p>
</div>"""

    contacts = get_all_contacts()
    if not contacts:
        return jsonify({"ok": True, "sent": 0, "message": "No subscribers yet"})

    sent, errors = 0, []
    for c in contacts:
        ok, resp = _resend_post("/emails", {"from": UPDATES_EMAIL, "to": [c["email"]], "subject": subject, "html": html})
        if ok: sent += 1
        else: errors.append({"email": c["email"], "error": resp})
    return jsonify({"ok": True, "sent": sent, "total": len(contacts), "errors": errors})


@app.route("/api/subscribers", methods=["GET"])
def list_subscribers():
    if request.headers.get("X-Notify-Secret") != NOTIFY_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    contacts = get_all_contacts()
    return jsonify({"count": len(contacts), "subscribers": [c["email"] for c in contacts]})


# ─── Email Webhook ───────────────────────────────────────────────────────────

@app.route("/api/webhook/email", methods=["POST"])
def webhook_email():
    """Receive inbound emails from Resend webhook."""
    data = request.get_json(silent=True) or {}
    log.info(f"[webhook/email] Received: {json.dumps(data)[:500]}")

    # Resend wraps in type/data
    event_type = data.get("type", "")
    payload = data.get("data", data)

    from_email = payload.get("from", "")
    from_name = ""
    # Parse "Name <email>" format
    if "<" in from_email and ">" in from_email:
        from_name = from_email.split("<")[0].strip().strip('"')
        from_email = from_email.split("<")[1].split(">")[0]

    to_email = payload.get("to", "")
    if isinstance(to_email, list):
        to_email = to_email[0] if to_email else ""
    subject = payload.get("subject", "(no subject)")
    body_html = payload.get("html", "")
    body_text = payload.get("text", payload.get("plain_text", ""))

    try:
        db = get_db()
        db.execute("""INSERT INTO emails_received (from_email, from_name, to_email, subject, body_html, body_text)
                      VALUES (?,?,?,?,?,?)""", (from_email, from_name, to_email, subject, body_html, body_text))
        db.commit(); db.close()
    except Exception as e:
        log.error(f"[webhook/email] DB error: {e}")

    # Notify Vivek
    notify_vivek(
        f"📧 New email from {from_name or from_email}: {subject}",
        f"""<div style="font-family:sans-serif;">
        <h2>New inbound email</h2>
        <p><strong>From:</strong> {from_name} &lt;{from_email}&gt;</p>
        <p><strong>To:</strong> {to_email}</p>
        <p><strong>Subject:</strong> {subject}</p>
        <hr><div>{body_html or body_text or '(empty)'}</div>
        <p><a href="https://clawmetry.com/admin/inbox">View in Admin</a></p>
        </div>"""
    )

    return jsonify({"ok": True})


# ─── Admin Routes ────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin")
        error = "Wrong password"
    return render_template_string(LOGIN_PAGE, error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin/login")


@app.route("/admin")
@login_required
def admin_dashboard():
    db = get_db()
    subs = db.execute("SELECT COUNT(*) c FROM subscribers").fetchone()["c"]
    emails = db.execute("SELECT COUNT(*) c FROM emails_received").fetchone()["c"]
    unread = db.execute("SELECT COUNT(*) c FROM emails_received WHERE read=0").fetchone()["c"]
    events = db.execute("SELECT COUNT(*) c FROM copy_events").fetchone()["c"]
    sent = db.execute("SELECT COUNT(*) c FROM emails_sent").fetchone()["c"]

    recent_emails = db.execute("SELECT id, from_email, from_name, subject, received_at, read FROM emails_received ORDER BY id DESC LIMIT 5").fetchall()
    recent_subs = db.execute("SELECT email, source, location, subscribed_at FROM subscribers ORDER BY id DESC LIMIT 5").fetchall()
    db.close()

    rows_emails = ""
    for e in recent_emails:
        badge = '<span class="badge badge-unread">NEW</span>' if not e["read"] else '<span class="badge badge-read">read</span>'
        rows_emails += f'<tr><td><a href="/admin/inbox/{e["id"]}">{e["from_name"] or e["from_email"]}</a></td><td>{e["subject"]}</td><td>{badge}</td><td>{e["received_at"]}</td></tr>'

    rows_subs = ""
    for s in recent_subs:
        rows_subs += f'<tr><td>{s["email"]}</td><td>{s["source"] or "-"}</td><td>{s["location"] or "-"}</td><td>{s["subscribed_at"]}</td></tr>'

    html = f"""
    <h2 style="margin-bottom:20px">Dashboard</h2>
    <div class="stat-grid">
      <div class="card stat"><h3>{subs}</h3><p>Subscribers</p></div>
      <div class="card stat"><h3>{emails}</h3><p>Emails Received ({unread} unread)</p></div>
      <div class="card stat"><h3>{sent}</h3><p>Emails Sent</p></div>
      <div class="card stat"><h3>{events}</h3><p>Copy Events</p></div>
    </div>
    <div class="card"><h3 style="margin-bottom:12px">Recent Emails</h3>
    {"<table><th>From</th><th>Subject</th><th>Status</th><th>Date</th>" + rows_emails + "</table>" if rows_emails else '<p class="empty">No emails yet</p>'}
    </div>
    <div class="card"><h3 style="margin-bottom:12px">Recent Subscribers</h3>
    {"<table><th>Email</th><th>Source</th><th>Location</th><th>Date</th>" + rows_subs + "</table>" if rows_subs else '<p class="empty">No subscribers yet</p>'}
    </div>
    """
    return _render_admin("Dashboard", html, "dash")


@app.route("/admin/inbox")
@login_required
def admin_inbox():
    db = get_db()
    emails = db.execute("SELECT id, from_email, from_name, subject, received_at, read, replied FROM emails_received ORDER BY id DESC").fetchall()
    db.close()

    if not emails:
        html = '<h2 style="margin-bottom:20px">Inbox</h2><div class="card"><p class="empty">No emails received yet. Send one to hello@clawmetry.com!</p></div>'
        return _render_admin("Inbox", html, "inbox")

    rows = ""
    for e in emails:
        badge = '<span class="badge badge-unread">NEW</span>' if not e["read"] else '<span class="badge badge-read">read</span>'
        replied = ' 📨' if e["replied"] else ''
        name = e["from_name"] or e["from_email"]
        rows += f'<tr><td><a href="/admin/inbox/{e["id"]}"><strong>{name}</strong></a></td><td><a href="/admin/inbox/{e["id"]}">{e["subject"]}</a></td><td>{badge}{replied}</td><td style="white-space:nowrap">{e["received_at"]}</td></tr>'

    html = f"""
    <h2 style="margin-bottom:20px">Inbox <span style="color:var(--muted);font-size:16px">({len(emails)} emails)</span></h2>
    <div class="card"><table><th>From</th><th>Subject</th><th>Status</th><th>Date</th>{rows}</table></div>
    """
    return _render_admin("Inbox", html, "inbox")


@app.route("/admin/inbox/<int:eid>")
@login_required
def admin_view_email(eid):
    db = get_db()
    e = db.execute("SELECT * FROM emails_received WHERE id=?", (eid,)).fetchone()
    if not e:
        db.close()
        return redirect("/admin/inbox")

    # Mark as read
    if not e["read"]:
        db.execute("UPDATE emails_received SET read=1 WHERE id=?", (eid,))
        db.commit()

    replies = db.execute("SELECT * FROM emails_sent WHERE in_reply_to=? ORDER BY id", (eid,)).fetchall()
    db.close()

    replies_html = ""
    for r in replies:
        replies_html += f'<div class="card" style="margin-top:12px;border-left:3px solid var(--accent)"><p style="color:var(--muted);font-size:12px">Reply sent to {r["to_email"]} at {r["sent_at"]}</p><div style="margin-top:8px">{r["body_html"]}</div></div>'

    body = e["body_html"] or f'<pre style="white-space:pre-wrap;color:var(--text)">{e["body_text"] or "(empty)"}</pre>'

    html = f"""
    <p><a href="/admin/inbox" class="btn btn-outline" style="margin-bottom:16px">← Back to Inbox</a></p>
    <div class="card">
      <p style="color:var(--muted);font-size:13px">From: <strong style="color:var(--text)">{e["from_name"] or ""} &lt;{e["from_email"]}&gt;</strong></p>
      <p style="color:var(--muted);font-size:13px">To: {e["to_email"]}</p>
      <p style="color:var(--muted);font-size:13px">Date: {e["received_at"]}</p>
      <h2 style="margin:12px 0">{e["subject"]}</h2>
      <div class="email-body">{body}</div>
      <a href="/admin/inbox/{eid}/reply" class="btn btn-primary">↩ Reply</a>
    </div>
    {replies_html}
    """
    return _render_admin(e["subject"], html, "inbox")


@app.route("/admin/inbox/<int:eid>/reply", methods=["GET", "POST"])
@login_required
def admin_reply_email(eid):
    from flask import flash
    db = get_db()
    e = db.execute("SELECT * FROM emails_received WHERE id=?", (eid,)).fetchone()
    if not e:
        db.close()
        return redirect("/admin/inbox")

    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if body:
            body_html = body.replace("\n", "<br>")
            subject = f"Re: {e['subject']}" if not e['subject'].startswith("Re:") else e['subject']
            ok, resp = _resend_post("/emails", {
                "from": FROM_EMAIL, "to": [e["from_email"]],
                "subject": subject, "html": body_html,
            })
            if ok:
                db.execute("INSERT INTO emails_sent (to_email, subject, body_html, in_reply_to) VALUES (?,?,?,?)",
                           (e["from_email"], subject, body_html, eid))
                db.execute("UPDATE emails_received SET replied=1 WHERE id=?", (eid,))
                db.commit()
                flash("Reply sent!", "success")
            else:
                flash(f"Failed to send: {resp}", "error")
        db.close()
        return redirect(f"/admin/inbox/{eid}")

    db.close()
    html = f"""
    <p><a href="/admin/inbox/{eid}" class="btn btn-outline">← Back</a></p>
    <div class="card">
      <h2 style="margin-bottom:4px">Reply to {e["from_name"] or e["from_email"]}</h2>
      <p style="color:var(--muted);font-size:13px;margin-bottom:16px">Re: {e["subject"]}</p>
      <form method="POST">
        <label>Message</label>
        <textarea name="body" rows="10" placeholder="Type your reply..." required></textarea>
        <div style="margin-top:16px"><button type="submit" class="btn btn-primary">Send Reply</button></div>
      </form>
    </div>
    """
    return _render_admin("Reply", html, "inbox")


@app.route("/admin/compose", methods=["GET", "POST"])
@login_required
def admin_compose():
    from flask import flash
    if request.method == "POST":
        to = request.form.get("to", "").strip()
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()
        if to and subject and body:
            body_html = body.replace("\n", "<br>")
            ok, resp = _resend_post("/emails", {"from": FROM_EMAIL, "to": [to], "subject": subject, "html": body_html})
            if ok:
                db = get_db()
                db.execute("INSERT INTO emails_sent (to_email, subject, body_html) VALUES (?,?,?)", (to, subject, body_html))
                db.commit(); db.close()
                flash("Email sent!", "success")
                return redirect("/admin/compose")
            else:
                flash(f"Failed: {resp}", "error")

    html = """
    <div class="card">
      <h2 style="margin-bottom:16px">Compose Email</h2>
      <form method="POST">
        <label>To</label><input type="email" name="to" required placeholder="recipient@example.com">
        <label>Subject</label><input type="text" name="subject" required placeholder="Subject">
        <label>Body</label><textarea name="body" rows="12" required placeholder="Write your email..."></textarea>
        <div style="margin-top:16px"><button type="submit" class="btn btn-primary">Send Email</button></div>
      </form>
    </div>
    """
    return _render_admin("Compose", html, "compose")


@app.route("/admin/sent")
@login_required
def admin_sent():
    db = _get_db()
    emails = db.execute("SELECT * FROM emails_sent ORDER BY id DESC").fetchall()
    rows = ""
    for e in emails:
        rows += f'<tr><td>{e["to_email"]}</td><td>{e["subject"]}</td><td>{e["sent_at"]}</td></tr>'
    html = f"""
    <h2 style="margin-bottom:16px">Sent Emails ({len(emails)})</h2>
    <table><thead><tr><th>To</th><th>Subject</th><th>Sent</th></tr></thead><tbody>{rows or '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No sent emails yet</td></tr>'}</tbody></table>
    """
    return _render_admin("Sent", html, "sent")


@app.route("/admin/subscribers")
@login_required
def admin_subscribers():
    db = get_db()
    subs = db.execute("SELECT * FROM subscribers ORDER BY id DESC").fetchall()
    db.close()

    if not subs:
        html = '<h2>Subscribers</h2><div class="card"><p class="empty">No subscribers yet</p></div>'
        return _render_admin("Subscribers", html, "subs")

    rows = ""
    for s in subs:
        rows += f'<tr><td>{s["email"]}</td><td>{s["source"] or "-"}</td><td>{s["location"] or "-"}</td><td>{s["ip"] or "-"}</td><td style="white-space:nowrap">{s["subscribed_at"]}</td></tr>'

    html = f"""
    <h2 style="margin-bottom:20px">Subscribers <span style="color:var(--muted);font-size:16px">({len(subs)})</span></h2>
    <div class="card"><table><th>Email</th><th>Source</th><th>Location</th><th>IP</th><th>Date</th>{rows}</table></div>
    """
    return _render_admin("Subscribers", html, "subs")


@app.route("/admin/events")
@login_required
def admin_events():
    db = get_db()
    events = db.execute("SELECT * FROM copy_events ORDER BY id DESC").fetchall()
    db.close()

    if not events:
        html = '<h2>Copy Events</h2><div class="card"><p class="empty">No events yet</p></div>'
        return _render_admin("Events", html, "events")

    rows = ""
    for e in events:
        rows += f'<tr><td>{e["tab"]}</td><td><code>{e["command"][:60] if e["command"] else "-"}</code></td><td>{e["source"] or "-"}</td><td>{e["location"] or "-"}</td><td style="white-space:nowrap">{e["created_at"]}</td></tr>'

    html = f"""
    <h2 style="margin-bottom:20px">Copy Events <span style="color:var(--muted);font-size:16px">({len(events)})</span></h2>
    <div class="card"><table><th>Tab</th><th>Command</th><th>Source</th><th>Location</th><th>Date</th>{rows}</table></div>
    """
    return _render_admin("Events", html, "events")


# ─── Static Routes ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:path>")
def static_files(path):
    # Don't serve admin routes as static
    if path.startswith("admin"):
        return "Not found", 404
    return send_from_directory(".", path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
