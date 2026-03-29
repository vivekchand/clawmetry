"""Minimal Flask backend for ClawMetry landing - serves static files + email subscribe via Resend.
Includes admin panel for inbox, subscribers, copy events.
Storage: Firestore (primary). SQLite only used as fallback for public API writes when Firestore is down."""
import os
import re
import json
import sqlite3
import hashlib
import logging
import sys
import time
import secrets
import threading
from datetime import datetime, timezone
from functools import wraps

import requests
from flask import Flask, request, jsonify, send_from_directory, make_response, redirect, url_for, session, render_template_string, render_template

app = Flask(__name__, static_folder=".", static_url_path="")




def _ai_personalize_reply(name: str, message: str, help_type: str) -> dict:
    """Generate a personalised subject + follow-up question using Claude.
    Returns dict with subject and question keys, or None on failure/empty message."""
    if not ANTHROPIC_API_KEY or not message or not message.strip():
        return None
    try:
        clawmetry_context = (
            "ClawMetry is an open-source real-time observability dashboard for OpenClaw (224k+ GitHub stars). "
            "OpenClaw is a self-hosted AI agent framework — connects to Telegram, WhatsApp, Discord etc. "
            "ClawMetry installs in 30 seconds (pip install clawmetry) and auto-detects OpenClaw on the same machine. "
            "It shows: live token usage and cost per session, all tool calls, cron job history, "
            "sub-agent activity, memory files, session transcripts, and configurable cost alerts. "
            "Works with any AI model: Claude, GPT-4, Gemini, or local models via Ollama. "
            "Runs on the same machine as OpenClaw: Mac mini, old laptop, VPS, Railway, Hostinger etc. "
            "Managed tier = hosted ClawMetry in the cloud, no infra to manage. "
            "Common pain points: surprise token bills, agent loops draining budget, no sub-agent visibility, "
            "cron jobs failing silently, no audit trail for enterprise use."
        )
        req_type = "managed instance request" if help_type == "managed" else "onboarding support request"
        prompt = (
            f"You are Vivek, founder of ClawMetry. A user named {name or 'someone'} submitted a {req_type}. "
            f"ClawMetry context: {clawmetry_context} "
            f"Their message: \"{message.strip()}\". "
            f"Return ONLY a JSON object with two keys: subject and question. "
            f"subject: a short punchy email subject (max 8 words) that feels personal and premium, "
            f"makes the recipient want to open it, references their context, never generic. "
            f"question: ONE follow-up question (max 20 words) directly relevant to their message. "
            f"Rules for both: sound like a real person, not a company. "
            f"No em dashes. No exclamation marks. No filler words. No AI tells. "
            f"question: ask directly, no preamble like Quick question. "
            f"Output only the raw JSON, nothing else. Example: {{\"subject\": \"your OpenClaw setup\", \"question\": \"which model are you running?\"}}"
        )
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 80, "messages": [{"role": "user", "content": prompt}]},
            timeout=3,
        )
        if resp.status_code == 200:
            import json as _json
            text = resp.json()["content"][0]["text"].strip()
            parsed = _json.loads(text)
            return {"subject": parsed.get("subject", ""), "question": parsed.get("question", "")}
    except Exception as e:
        log.warning(f"[ai-email] failed: {e}")
    return None


def _bg_send_managed_email(name, email, use_case):
    """Send managed request confirmation email in background thread."""
    try:
        ai = _ai_personalize_reply(name, use_case, "managed")
        ai_q = ai.get("question") if ai else None
        ai_s = ai.get("subject") if ai else None
        uc_block = (f'<div style="background:#1a1a2e;border-left:3px solid #555;padding:10px 14px;margin:12px 0;font-size:14px;color:#9ca3af;font-style:italic;">You mentioned: {use_case}</div>' if use_case else '')
        _resend_post("/emails", {
            "from": FROM_EMAIL, "to": [email], "bcc": ["vivek@clawmetry.com"],
            "reply_to": ["vivek@clawmetry.com"],
            "subject": ai_s or "You're on the ClawMetry managed hosting list",
            "html": f'''<div style="font-family:sans-serif;max-width:500px;margin:0 auto;background:#0d0d14;color:#e0e0e0;border-radius:12px;overflow:hidden;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:32px 28px;text-align:center;">
    <img src="https://clawmetry.com/web-app-manifest-192x192.png" style="width:56px;height:56px;border-radius:10px;margin-bottom:12px;display:block;margin-left:auto;margin-right:auto;" alt="ClawMetry">
    <h1 style="color:#fff;font-size:20px;margin:0;">Thanks, {name}!</h1>
  </div>
  <div style="padding:28px;">
    <p style="font-size:15px;line-height:1.7;color:#d1d5db;">Thanks for your interest in a managed ClawMetry setup. I will keep you posted once we are ready with the cloud hosted version of ClawMetry.</p>
    {uc_block}
    <p style="font-size:15px;color:#d1d5db;">Vivek<br><span style="color:#9ca3af;font-size:13px;">Founder, ClawMetry</span></p>
  </div>
</div>'''
        })
    except Exception as e:
        log.error(f"[managed-email-bg] {e}")


def _bg_send_support_email(name, email, message, help_type):
    """Send support request confirmation email in background thread."""
    try:
        ai = _ai_personalize_reply(name, message, help_type)
        ai_q = ai.get("question") if ai else None
        ai_s = ai.get("subject") if ai else None
        display_name = name or "there"
        msg_block = (f'<div style="background:#f5f5f5;border-left:3px solid #ccc;padding:10px 14px;margin:12px 0;font-size:14px;color:#555;font-style:italic;">You said: {message}</div>' if message else '')
        _resend_post("/emails", {
            "from": FROM_EMAIL, "to": email, "bcc": ["vivek@clawmetry.com"],
            "reply_to": ["vivek@clawmetry.com"],
            "subject": ai_s or "Quick question before I set up ClawMetry for you",
            "html": (
                f'<div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;max-width:520px;margin:0 auto;">' +
                f'<p style="font-size:15px;color:#111;line-height:1.7;">Hi {display_name},</p>' +
                f'<p style="font-size:15px;color:#111;line-height:1.7;">Thanks for reaching out! I got your request and will personally get back to you shortly to help you get ClawMetry set up.</p>' +
                msg_block +
                f'<p style="font-size:15px;color:#111;line-height:1.7;">{ai_q or "Quick question first: where are you running OpenClaw? Mac mini, old laptop, a VPS like Hostinger or Railway, or still planning to try it?"}</p>' +
                f'<p style="font-size:15px;color:#111;line-height:1.7;">Either way I can help, just want to make sure the setup guide I send actually fits your situation.</p>' +
                f'<p style="font-size:15px;color:#111;margin-top:20px;">Vivek<br><span style="color:#888;font-size:13px;">Founder, ClawMetry &middot; <a href=&quot;https://clawmetry.com&quot; style=&quot;color:#E5443A;text-decoration:none;&quot;>clawmetry.com</a></span></p>' +
                f'</div>'
            )
        })
    except Exception as e:
        log.error(f"[support-email-bg] {e}")

@app.before_request
def enforce_https():
    if request.headers.get("X-Forwarded-Proto", "https") == "http":
        return redirect(request.url.replace("http://", "https://", 1), code=301)
app.secret_key = os.environ.get("SECRET_KEY", "clawmetry-secret-key-2026-xk9m")

# ─── Admin OTP Auth ─────────────────────────────────────────────────────────

_admin_otps = {}  # email -> {otp, expires_at}
ADMIN_EMAIL = "vivekchand19@gmail.com"


def _generate_otp(email):
    otp = str(secrets.randbelow(900000) + 100000)  # 6 digits
    _admin_otps[email] = {'otp': otp, 'expires_at': time.time() + 600}
    return otp


def _verify_otp(email, otp):
    record = _admin_otps.get(email)
    if not record:
        return False
    if time.time() > record['expires_at']:
        del _admin_otps[email]
        return False
    if record['otp'] != otp:
        return False
    del _admin_otps[email]
    return True


def _send_otp_email(email, otp):
    import urllib.request, json as _j
    payload = {
        "from": "ClawMetry <hello@clawmetry.com>",
        "to": [email],
        "subject": f"Your ClawMetry admin OTP: {otp}",
        "html": f"<p>Your one-time code is: <strong style='font-size:24px;letter-spacing:4px;'>{otp}</strong></p><p>Valid for 10 minutes.</p>"
    }
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=_j.dumps(payload).encode(),
        headers={"Authorization": "Bearer re_jWLL59fj_PBctxiwxDLFiWjBZ9MiJ4ems", "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 200
    except Exception as e:
        log.error(f"[otp-email] send failed: {e}")
        return False

# Force logs to stdout for Cloud Run
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger("clawmetry")

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "clawmetry-admin-2026")
# Set to False to suppress per-click email notifications (use /admin/analytics instead)
NOTIFY_CLICKS = os.environ.get("NOTIFY_CLICKS", "false").lower() == "true"

DB_PATH = "/tmp/clawmetry.db"

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "re_jWLL59fj_PBctxiwxDLFiWjBZ9MiJ4ems")
RESEND_AUDIENCE_ID = os.environ.get("RESEND_AUDIENCE_ID", "48212e72-0d6c-489c-90c3-85a03a52d54c")
FROM_EMAIL = "ClawMetry <vivek@clawmetry.com>"
UPDATES_EMAIL = "ClawMetry Updates <updates@clawmetry.com>"
NOTIFY_SECRET = os.environ.get("NOTIFY_SECRET", "clawmetry-notify-2026")

VIVEK_EMAIL = "vivekchand19@gmail.com"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLM_KEY = "clm2026"

# ─── Firestore Setup ────────────────────────────────────────────────────────

_firestore_db = None
_firestore_available = False

try:
    from google.cloud import firestore as _firestore_mod
    _firestore_db = _firestore_mod.Client()
    # Quick connectivity check
    _firestore_db.collection("_health").document("ping").set({"ts": _firestore_mod.SERVER_TIMESTAMP})
    _firestore_available = True
    log.info("[storage] Firestore connected ✓")
except Exception as _fs_err:
    log.warning(f"[storage] Firestore unavailable, falling back to SQLite: {_fs_err}")
    _firestore_available = False


def _fs():
    """Return Firestore client or None."""
    return _firestore_db if _firestore_available else None


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def _decrypt_payload(req):
    """Decrypt XOR+base64 encoded request body. Falls back to plain JSON."""
    data = req.get_json(silent=True) or {}
    if "p" in data and len(data) == 1:
        try:
            import base64
            decoded = base64.b64decode(data["p"])
            decrypted = "".join(chr(b ^ ord(CLM_KEY[i % len(CLM_KEY)])) for i, b in enumerate(decoded))
            return json.loads(decrypted)
        except Exception as e:
            log.error(f"[decrypt] failed: {e}")
            return {}
    return data
RESEND_HEADERS = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}

# ─── Database (SQLite fallback) ─────────────────────────────────────────────

def get_db():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS emails_received (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_email TEXT, from_name TEXT, to_email TEXT, subject TEXT,
            body_html TEXT, body_text TEXT,
            received_at TEXT DEFAULT (datetime('now')),
            read INTEGER DEFAULT 0, replied INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS emails_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            to_email TEXT, subject TEXT, body_html TEXT,
            sent_at TEXT DEFAULT (datetime('now')),
            in_reply_to TEXT
        );
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT, source TEXT, utm_data TEXT, location TEXT, ip TEXT, browser TEXT,
            subscribed_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS copy_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tab TEXT, command TEXT, source TEXT, utm_data TEXT, location TEXT, ip TEXT, browser TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS roadmap_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feature TEXT NOT NULL,
            ip_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS managed_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, email TEXT, company TEXT, use_case TEXT,
            location TEXT, ip TEXT, browser TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    db.commit()
    db.close()

# Only init SQLite if Firestore unavailable (fallback for public API writes)
if not _firestore_available:
    init_db()

# ─── Firestore Storage Layer ────────────────────────────────────────────────

def _fs_add(collection, data):
    """Add a document to a Firestore collection. Returns doc id or None."""
    fs = _fs()
    if not fs:
        return None
    try:
        _, ref = fs.collection(collection).add(data)
        return ref.id
    except Exception as e:
        log.error(f"[firestore] add to {collection} failed: {e}")
        return None


def _fs_get_all(collection, order_by=None, order_dir="DESCENDING", limit=None):
    """Get all docs from a collection, ordered. Returns list of dicts with 'id' key."""
    fs = _fs()
    if not fs:
        return None  # Signal caller to use SQLite
    try:
        q = fs.collection(collection)
        if order_by:
            direction = _firestore_mod.Query.DESCENDING if order_dir == "DESCENDING" else _firestore_mod.Query.ASCENDING
            q = q.order_by(order_by, direction=direction)
        if limit:
            q = q.limit(limit)
        docs = q.stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            results.append(d)
        return results
    except Exception as e:
        log.error(f"[firestore] get_all {collection} failed: {e}")
        return None


def _fs_get(collection, doc_id):
    """Get a single document by id. Returns dict or None."""
    fs = _fs()
    if not fs:
        return None
    try:
        doc = fs.collection(collection).document(doc_id).get()
        if doc.exists:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None
    except Exception as e:
        log.error(f"[firestore] get {collection}/{doc_id} failed: {e}")
        return None


def _fs_update(collection, doc_id, data):
    """Update fields on a document."""
    fs = _fs()
    if not fs:
        return False
    try:
        fs.collection(collection).document(doc_id).update(data)
        return True
    except Exception as e:
        log.error(f"[firestore] update {collection}/{doc_id} failed: {e}")
        return False


def _fs_count(collection):
    """Count docs in a collection."""
    fs = _fs()
    if not fs:
        return None
    try:
        agg = fs.collection(collection).count().get()
        return agg[0][0].value
    except Exception as e:
        log.error(f"[firestore] count {collection} failed: {e}")
        return None


def _fs_query(collection, field, op, value, order_by=None, order_dir="DESCENDING"):
    """Query docs with a filter."""
    fs = _fs()
    if not fs:
        return None
    try:
        q = fs.collection(collection).where(field, op, value)
        if order_by:
            direction = _firestore_mod.Query.DESCENDING if order_dir == "DESCENDING" else _firestore_mod.Query.ASCENDING
            q = q.order_by(order_by, direction=direction)
        return [dict(**doc.to_dict(), id=doc.id) for doc in q.stream()]
    except Exception as e:
        log.error(f"[firestore] query {collection} failed: {e}")
        return None


# ─── Resend → Firestore Sync (on startup) ───────────────────────────────────

def _sync_resend_contacts():
    """Sync Resend audience contacts into Firestore subscribers collection."""
    fs = _fs()
    if not fs:
        return
    try:
        contacts = get_all_contacts()
        if not contacts:
            return
        # Get existing emails in Firestore
        existing = set()
        for doc in fs.collection("subscribers").stream():
            d = doc.to_dict()
            if d.get("email"):
                existing.add(d["email"].lower())
        
        added = 0
        for c in contacts:
            email = (c.get("email") or "").lower()
            if email and email not in existing:
                created = c.get("created_at", _now_iso())
                if isinstance(created, str) and "T" in created:
                    created = created[:19].replace("T", " ")
                fs.collection("subscribers").add({
                    "email": email,
                    "source": "Resend (synced)",
                    "utm_data": "",
                    "location": "-",
                    "ip": "-",
                    "browser": "-",
                    "subscribed_at": created,
                })
                added += 1
        if added:
            log.info(f"[sync] Added {added} contacts from Resend to Firestore")
    except Exception as e:
        log.error(f"[sync] Resend→Firestore sync failed: {e}")

# Run sync in background thread on startup
if _firestore_available:
    threading.Thread(target=_sync_resend_contacts, daemon=True).start()

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
  <span class="brand"><img src="/favicon.svg" width="22" height="22" style="vertical-align:middle;margin-right:4px;border-radius:4px"> ClawMetry</span>
  <a href="/admin" class="{{ 'active' if active=='dash' }}">Dashboard</a>
  <a href="/admin/inbox" class="{{ 'active' if active=='inbox' }}">Inbox</a>
  <a href="/admin/compose" class="{{ 'active' if active=='compose' }}">Compose</a>
  <a href="/admin/blast" class="{{ 'active' if active=='blast' }}">Blast</a>
  <a href="/admin/sent" class="{{ 'active' if active=='sent' }}">Sent</a>
  <a href="/admin/subscribers" class="{{ 'active' if active=='subs' }}">Subscribers</a>
  <a href="/admin/events" class="{{ 'active' if active=='events' }}">Events</a>
  <a href="/admin/managed" class="{{ 'active' if active=='managed' }}">Managed</a>
  <a href="/admin/logout" style="margin-left:auto">Logout</a>
</nav>
<div class="container">
{% for cat, msg in get_flashed_messages(with_categories=true) %}
<div class="flash flash-{{ cat }}">{{ msg }}</div>
{% endfor %}
{{ content|safe }}
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
<h1>ClawMetry Admin</h1>
{% if error %}<p class="err">{{ error }}</p>{% endif %}
<form method="POST"><input type="email" name="email" placeholder="your@email.com" autofocus required><button type="submit">Send OTP</button></form>
</div></body></html>
"""

VERIFY_PAGE = """
<!DOCTYPE html><html><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Verify OTP — ClawMetry Admin</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#0B0F1A;color:#E5E7EB;display:flex;align-items:center;justify-content:center;min-height:100vh}
.box{background:#111827;border:1px solid #1F2937;border-radius:16px;padding:40px;width:360px;text-align:center}
h1{font-size:20px;margin-bottom:8px}
p.sub{color:#9CA3AF;font-size:13px;margin-bottom:24px}
input{width:100%;padding:12px;border-radius:8px;border:1px solid #1F2937;background:#0B0F1A;color:#E5E7EB;font-size:20px;letter-spacing:8px;text-align:center;margin-bottom:16px}
button{width:100%;padding:12px;border-radius:8px;border:none;background:#E5443A;color:#fff;font-size:14px;font-weight:600;cursor:pointer}
.err{color:#fca5a5;font-size:13px;margin-bottom:12px}
</style></head><body>
<div class="box">
<h1>Enter OTP</h1>
<p class="sub">Check your email for the 6-digit code.</p>
{% if error %}<p class="err">{{ error }}</p>{% endif %}
<form method="POST"><input type="text" name="otp" placeholder="000000" maxlength="6" autofocus required><button type="submit">Verify</button></form>
</div></body></html>
"""

# ─── Helpers ─────────────────────────────────────────────────────────────────

WELCOME_HTML = """\
<div style="font-family:sans-serif;max-width:600px;margin:0 auto;background:#0d0d14;color:#e0e0e0;border-radius:12px;overflow:hidden;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:32px 28px;text-align:center;">
    <img src="https://clawmetry.com/web-app-manifest-192x192.png" style="width:56px;height:56px;border-radius:10px;margin-bottom:12px;display:block;margin-left:auto;margin-right:auto;" alt="ClawMetry">
    <h1 style="color:#fff;font-size:22px;margin:0 0 6px;">Welcome to ClawMetry!</h1>
    <p style="color:#9ca3af;font-size:13px;margin:0;">Real-time observability for your AI agents</p>
  </div>
  <div style="padding:28px;">
    <p style="font-size:15px;line-height:1.7;color:#d1d5db;">Hey there 👋</p>
    <p style="font-size:15px;line-height:1.7;color:#d1d5db;">Thanks for subscribing! ClawMetry is a free, open-source dashboard that lets you see token costs, cron jobs, sub-agents, memory files, and session history in one place.</p>
    <p style="font-size:14px;line-height:1.7;color:#9ca3af;">Get started in one line:</p>
    <div style="background:#111827;border:1px solid #2d2d44;border-radius:8px;padding:14px 18px;font-family:monospace;font-size:13px;color:#10b981;margin:12px 0;">curl -fsSL https://clawmetry.com/install.sh | bash</div>
    <div style="background:#1a1a2e;border:1px solid #2d2d44;border-radius:10px;padding:20px;margin:20px 0;">
      <div style="font-size:16px;font-weight:700;color:#fff;margin-bottom:8px;">&#x1F4AC; Share your experience on Product Hunt</div>
      <p style="font-size:13px;color:#9ca3af;margin:0 0 12px;">Used ClawMetry? A quick review helps others find it.</p>
      <a href="https://www.producthunt.com/products/clawmetry/reviews/new" style="display:inline-block;background:#ff6154;color:#fff;font-weight:700;font-size:13px;padding:10px 24px;border-radius:8px;text-decoration:none;">Write a review &#x2192;</a>
    </div>
    <div style="background:#1a1a2e;border:1px solid #2d2d44;border-radius:10px;padding:20px;margin:20px 0;">
      <div style="font-size:16px;font-weight:700;color:#fff;margin-bottom:8px;">⭐ Star us on GitHub</div>
      <p style="font-size:13px;color:#9ca3af;margin:0 0 12px;">Help other OpenClaw users discover ClawMetry.</p>
      <a href="https://github.com/vivekchand/clawmetry" style="display:inline-block;background:#238636;color:#fff;font-weight:700;font-size:13px;padding:10px 24px;border-radius:8px;text-decoration:none;">Star on GitHub →</a>
    </div>
    <div style="background:#1a1a2e;border:1px solid #2d2d44;border-radius:10px;padding:20px;margin:20px 0;">
      <div style="font-size:16px;font-weight:700;color:#fff;margin-bottom:4px;">&#x1F6E3; What we are building next</div>
      <p style="font-size:13px;color:#9ca3af;margin:0 0 14px;">Cloud dashboard, alerting, iOS/Android app, human-in-the-loop controls. Vote on what ships first.</p>
      <div style="margin-bottom:14px;">
        <span style="display:inline-block;background:#1e293b;border:1px solid #334155;border-radius:6px;padding:5px 12px;font-size:12px;color:#94a3b8;margin:3px;">&#x2601; Cloud dashboard</span>
        <span style="display:inline-block;background:#1e293b;border:1px solid #334155;border-radius:6px;padding:5px 12px;font-size:12px;color:#94a3b8;margin:3px;">&#x1F514; Alerting</span>
        <span style="display:inline-block;background:#1e293b;border:1px solid #334155;border-radius:6px;padding:5px 12px;font-size:12px;color:#94a3b8;margin:3px;">&#x1F4F1; iOS/Android</span>
        <span style="display:inline-block;background:#1e293b;border:1px solid #334155;border-radius:6px;padding:5px 12px;font-size:12px;color:#94a3b8;margin:3px;">&#x1F9D1;&#x200D;&#x1F4BB; Human-in-the-loop</span>
      </div>
      <a href="https://clawmetry.com/roadmap" style="display:inline-block;background:#E5443A;color:#fff;font-weight:700;font-size:13px;padding:10px 24px;border-radius:8px;text-decoration:none;">Vote on what ships next &#x2192;</a>
    </div>
    <div style="background:linear-gradient(135deg,#1e3a5f,#1a2744);border:1px solid #3b82f6;border-radius:10px;padding:20px;margin:24px 0;text-align:center;">
      <div style="font-size:24px;margin-bottom:8px;">🎁</div>
      <div style="font-size:16px;font-weight:700;color:#fff;margin-bottom:8px;">Get a $10 Amazon Gift Card</div>
      <p style="font-size:13px;color:#93c5fd;line-height:1.6;margin:0;">Try ClawMetry, leave a <a href="https://www.producthunt.com/products/clawmetry/reviews/new" style="color:#93c5fd;font-weight:700;">Product Hunt review</a>, and reply to this email with a screenshot of your dashboard. We will send you a <strong>$10 Amazon gift card</strong> as a thank you.</p>
    </div>
    <p style="font-size:15px;color:#d1d5db;">Cheers,<br><strong style="color:#fff;">The ClawMetry Team</strong></p>
  </div>
  <div style="border-top:1px solid #1f1f2e;padding:20px 28px;text-align:center;">
    <p style="font-size:13px;color:#9ca3af;margin:0 0 12px;">Need help setting up?</p>
    <div style="margin-bottom:8px;">
      <a href="https://clawmetry.com/?support=1" style="color:#60a5fa;font-weight:600;font-size:14px;text-decoration:none;">Get free onboarding support →</a>
    </div>
    <div style="margin-bottom:12px;">
      <a href="https://clawmetry.com/?managed=1" style="color:#9ca3af;font-size:13px;text-decoration:underline;text-underline-offset:3px;">Request a managed instance →</a>
    </div>
    <p style="font-size:11px;color:#6b7280;margin:0;">We email on major releases only. No spam. Ever.</p>
  </div>
</div>
"""



WELCOME_SIGNUP_HTML_TMPL = """\
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,sans-serif;max-width:580px;margin:0 auto;background:#080d16;color:#e2e8f0;border-radius:16px;overflow:hidden;border:1px solid #1e2d40;">

  <!-- Header -->
  <div style="background:linear-gradient(135deg,#0f1623 0%,#1a1a2e 100%);padding:36px 32px;text-align:center;border-bottom:1px solid #1e2d40;">
    <img src="https://clawmetry.com/apple-touch-icon.png" style="width:48px;height:48px;border-radius:10px;margin-bottom:16px;display:block;margin-left:auto;margin-right:auto;" alt="ClawMetry">
    <h1 style="color:#fff;font-size:24px;font-weight:700;margin:0 0 6px;letter-spacing:-0.3px;">Welcome to ClawMetry Cloud</h1>
    <p style="color:#64748b;font-size:14px;margin:0;">Real-time observability for your AI agents</p>
  </div>

  <!-- Body -->
  <div style="padding:32px;">

    <p style="font-size:15px;line-height:1.7;color:#cbd5e1;margin:0 0 20px;">Your cloud account is live. Everything your agents do — tool calls, sessions, memory, cost — streams to your dashboard in real time.</p>

    <!-- No API key in email - security -->
    <div style="background:#0f1623;border:1px solid #1e2d40;border-radius:10px;padding:16px 20px;margin:0 0 24px;">
      <p style="font-size:13px;color:#cbd5e1;margin:0 0 10px;line-height:1.6;">Your account is live. Open the dashboard to find your API key under <strong style="color:#e2e8f0;">Account</strong>.</p>
      <a href="https://app.clawmetry.com" style="display:inline-block;background:#10b981;color:#fff;font-size:12px;font-weight:600;padding:8px 18px;border-radius:6px;text-decoration:none;">Open Dashboard</a>
    </div>

    <!-- Setup steps -->
    <p style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 14px;">Connect your first machine</p>

    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 28px;">
      <tr><td style="padding-bottom:10px;">
        <table width="100%" cellpadding="14" cellspacing="0" border="0" style="background:#0f1623;border:1px solid #1e2d40;border-radius:8px;">
          <tr>
            <td width="28" valign="top" style="padding:14px 8px 14px 16px;">
              <span style="display:inline-block;background:#e5443a;color:#fff;font-size:11px;font-weight:700;padding:2px 7px;border-radius:4px;">1</span>
            </td>
            <td valign="top" style="padding:14px 16px 14px 4px;">
              <p style="margin:0 0 4px;font-size:12px;color:#64748b;">Install</p>
              <code style="font-size:12px;color:#10b981;">curl -fsSL https://clawmetry.com/install.sh | bash</code>
            </td>
          </tr>
        </table>
      </td></tr>
      <tr><td>
        <table width="100%" cellpadding="14" cellspacing="0" border="0" style="background:#0f1623;border:1px solid #1e2d40;border-radius:8px;">
          <tr>
            <td width="28" valign="top" style="padding:14px 8px 14px 16px;">
              <span style="display:inline-block;background:#e5443a;color:#fff;font-size:11px;font-weight:700;padding:2px 7px;border-radius:4px;">2</span>
            </td>
            <td valign="top" style="padding:14px 16px 14px 4px;">
              <p style="margin:0 0 4px;font-size:12px;color:#64748b;">Onboard — run this and follow the prompts</p>
              <code style="font-size:12px;color:#10b981;">clawmetry onboard</code>
            </td>
          </tr>
        </table>
      </td></tr>
    </table>

    <!-- CTA -->
    <div style="text-align:center;margin:0 0 28px;">
      <a href="https://app.clawmetry.com" style="display:inline-block;background:#e5443a;color:#fff;font-weight:700;font-size:15px;padding:14px 36px;border-radius:10px;text-decoration:none;letter-spacing:-0.1px;">Open Dashboard &rarr;</a>
    </div>

    <!-- What you get -->
    <div style="background:#0f1623;border:1px solid #1e2d40;border-radius:10px;padding:20px;margin:0 0 24px;">
      <p style="font-size:12px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;margin:0 0 14px;">What you can see in your dashboard</p>
      <div style="display:grid;gap:10px;">
        <div style="display:flex;gap:10px;align-items:flex-start;"><span style="color:#e5443a;font-size:14px;flex-shrink:0;">&#9679;</span><span style="font-size:13px;color:#cbd5e1;line-height:1.5;"><strong style="color:#e2e8f0;">Brain tab</strong> &mdash; live stream of every thought your agent has, as it happens</span></div>
        <div style="display:flex;gap:10px;align-items:flex-start;"><span style="color:#e5443a;font-size:14px;flex-shrink:0;">&#9679;</span><span style="font-size:13px;color:#cbd5e1;line-height:1.5;"><strong style="color:#e2e8f0;">Flow tab</strong> &mdash; visual graph of every tool call, sub-agent, and session</span></div>
        <div style="display:flex;gap:10px;align-items:flex-start;"><span style="color:#e5443a;font-size:14px;flex-shrink:0;">&#9679;</span><span style="font-size:13px;color:#cbd5e1;line-height:1.5;"><strong style="color:#e2e8f0;">Memory tab</strong> &mdash; see what your agent remembers across sessions</span></div>
        <div style="display:flex;gap:10px;align-items:flex-start;"><span style="color:#e5443a;font-size:14px;flex-shrink:0;">&#9679;</span><span style="font-size:13px;color:#cbd5e1;line-height:1.5;"><strong style="color:#e2e8f0;">Crons tab</strong> &mdash; monitor scheduled tasks and heartbeats</span></div>
      </div>
    </div>

    <!-- Referral -->
    <div style="background:#0d1f35;border:1px solid #1e3a5f;border-radius:10px;padding:18px;margin:0 0 28px;text-align:center;">
      <p style="font-size:13px;font-weight:700;color:#fff;margin:0 0 4px;">&#127381; Share &amp; get 1 month free</p>
      <p style="font-size:12px;color:#64748b;margin:0 0 10px;">For every friend who signs up with your link, you both get 1 month of Cloud Pro.</p>
      <code style="font-size:12px;color:#e5443a;word-break:break-all;">https://clawmetry.com?ref={referral_code}</code>
    </div>

    <!-- Sign-off -->
    <p style="font-size:14px;color:#cbd5e1;line-height:1.7;margin:0 0 4px;">Stuck? Just hit reply &mdash; I personally help every new user get set up.</p>
    <p style="font-size:15px;color:#e2e8f0;margin:16px 0 0;line-height:1.6;">Cheers,<br><strong style="color:#fff;">Vivek</strong><br><span style="font-size:12px;color:#64748b;">Founder, ClawMetry &middot; <a href="https://clawmetry.com" style="color:#e5443a;text-decoration:none;">clawmetry.com</a></span></p>
  </div>

  <!-- Footer -->
  <div style="border-top:1px solid #1e2d40;padding:16px 32px;text-align:center;">
    <p style="font-size:12px;color:#334155;margin:0;">ClawMetry &middot; <a href="https://clawmetry.com/cloud" style="color:#475569;text-decoration:none;">Cloud features</a> &middot; <a href="https://github.com/vivekchand/clawmetry" style="color:#475569;text-decoration:none;">GitHub</a></p>
  </div>

</div>
"""


def send_signup_welcome_email(email, api_key, referral_code=""):
    """Send welcome email with API key to new OTP signups. Reply goes to vivek@clawmetry.com."""
    subject = "Welcome to ClawMetry"
    referral_code_val = referral_code or _generate_referral_code(email)
    html = WELCOME_SIGNUP_HTML_TMPL.format(referral_code=referral_code_val)
    ok, resp = _resend_post("/emails", {
        "from": FROM_EMAIL, "to": [email], "bcc": ["vivek@clawmetry.com"],
        "reply_to": ["vivek@clawmetry.com"],
        "subject": subject, "html": html,
    })
    if ok:
        sent_data = {
            "to_email": email, "subject": subject,
            "body_html": html, "sent_at": _now_iso(),
            "in_reply_to": "", "resend_id": resp.get("id", ""),
        }
        _fs_add("emails_sent", sent_data)
    return ok, resp


def _resend_post(path, payload, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(f"https://api.resend.com{path}", headers=RESEND_HEADERS, json=payload, timeout=10)
            if r.status_code == 429 and attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            return r.status_code in (200, 201), r.json() if r.content else {}
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return False, {"error": str(e)}
    return False, {"error": "max retries exceeded"}


def _resend_get(path):
    try:
        r = requests.get(f"https://api.resend.com{path}", headers=RESEND_HEADERS, timeout=10)
        return r.json() if r.content else {}
    except Exception:
        return {}


def send_welcome_email(email):
    subject = "Welcome to ClawMetry"
    ok, resp = _resend_post("/emails", {
        "from": FROM_EMAIL, "to": [email], "bcc": ["vivek@clawmetry.com"],
        "subject": subject, "html": WELCOME_HTML,
    })
    # Store in emails_sent so it shows in thread view
    if ok:
        sent_data = {
            "to_email": email, "subject": subject,
            "body_html": WELCOME_HTML, "sent_at": _now_iso(),
            "in_reply_to": "", "resend_id": resp.get("id", ""),
        }
        _fs_add("emails_sent", sent_data)
    return ok, resp


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
    # Try to detect source from UTM params first
    if utm:
        source = utm.get("utm_source",""); medium = utm.get("utm_medium",""); campaign = utm.get("utm_campaign","")
        if utm.get("gclid") or utm.get("gad_source"): return f"🔵 Google Ads" + (f" ({campaign})" if campaign else "")
        if utm.get("fbclid"): return "📘 Facebook/Meta Ads"
        if source: return " / ".join(filter(None, [source, medium, campaign]))
    # Fallback: parse referer URL for known patterns
    ref = referer or ""
    if "gclid=" in ref or "gad_source=" in ref: return "🔵 Google Ads"
    if "fbclid=" in ref: return "📘 Facebook/Meta Ads"
    if "google.com" in ref: return "🔍 Google (organic)"
    if "bing.com" in ref: return "🔍 Bing (organic)"
    if "twitter.com" in ref or "x.com" in ref: return "🐦 X/Twitter"
    if "linkedin.com" in ref: return "💼 LinkedIn"
    if "reddit.com" in ref: return "🟠 Reddit"
    if "producthunt.com" in ref: return "🔼 Product Hunt"
    if "github.com" in ref: return "🐙 GitHub"
    if "youtube.com" in ref: return "▶️ YouTube"
    if "hacker" in ref.lower() or "ycombinator" in ref: return "🟧 Hacker News"
    if ref and ref != "Direct": return f"🌐 {ref[:60]}"
    return "Direct / Unknown"


def _utm_html(utm):
    if not utm: return ""
    rows = "".join(f"<p><strong>{k}:</strong> {v}</p>" for k, v in utm.items() if k != "landing_url")
    landing = utm.get("landing_url","")
    if landing: rows += f"<p><strong>Landing URL:</strong> <a href='{landing}'>{landing[:80]}</a></p>"
    return rows


CLICK_NOISE_SUBJECTS = ("[Click]", "[Social Click]", "[Install Copy]")

def notify_vivek(subject, body_html):
    # Suppress high-frequency click emails when NOTIFY_CLICKS is off
    if not NOTIFY_CLICKS and any(subject.startswith(s) for s in CLICK_NOISE_SUBJECTS):
        log.info(f"[notify_vivek] suppressed (NOTIFY_CLICKS=false): {subject}")
        return
    try:
        ok, resp = _resend_post("/emails", {"from": FROM_EMAIL, "to": [VIVEK_EMAIL], "subject": subject, "html": body_html})
        if not ok:
            log.error(f"[notify_vivek] Resend failed: {resp}")
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

VALID_FEATURES = {
    'cloud', 'alerting', 'hitl', 'mac-app',
    'ios-app', 'android-app', 'frameworks', 'team', 'cost'
}



import hashlib as _rl_hash
import string as _rl_string

def _generate_referral_code(email):
    """Generate a short anonymous referral code from email."""
    return _rl_hash.md5(email.lower().encode()).hexdigest()[:6]

def _credit_referrer(ref_code, new_email):
    """Credit the referrer with +30 days of pro access."""
    if not ref_code or not _firestore_available:
        return
    try:
        import datetime as _dt_ref
        # Find the referrer by their referral_code
        fs = _firestore_db
        docs = list(fs.collection("api_keys").where("referral_code", "==", ref_code).limit(1).stream())
        if not docs:
            log.warning(f"[referral] code {ref_code} not found")
            return
        referrer_doc = docs[0]
        referrer_data = referrer_doc.to_dict()
        referrer_email = referrer_data.get("email", "")

        # Don't allow self-referral
        if referrer_email.lower() == new_email.lower():
            return

        # Track the referral
        fs.collection("referrals").add({
            "referrer_code": ref_code,
            "referrer_email": referrer_email,
            "referred_email": new_email,
            "created_at": _dt_ref.datetime.utcnow().isoformat() + "Z",
            "reward": "30_days_pro",
        })

        # Extend referrer's pro access by 30 days
        current_plan = referrer_data.get("plan", "trial")
        current_expires = referrer_data.get("coupon_expires", "")
        now = _dt_ref.datetime.now(_dt_ref.timezone.utc)

        if current_expires:
            try:
                base = _dt_ref.datetime.fromisoformat(current_expires.replace("Z", "+00:00"))
                if base < now:
                    base = now
            except Exception:
                base = now
        elif current_plan in ("cloud_pro", "pro"):
            # Already paid, extend from far future or just track
            base = now + _dt_ref.timedelta(days=365)
        else:
            base = now

        new_expires = base + _dt_ref.timedelta(days=30)
        referrer_doc.reference.update({
            "plan": "cloud_pro",
            "coupon_expires": new_expires.isoformat(),
            "referral_months_earned": (referrer_data.get("referral_months_earned", 0) or 0) + 1,
        })

        log.info(f"[referral] {referrer_email} earned +30 days (referred {new_email}), pro until {new_expires.date()}")

        # Notify referrer
        try:
            _resend_post("/emails", {
                "from": FROM_EMAIL,
                "to": [referrer_email],
                "reply_to": ["vivek@clawmetry.com"],
                "subject": "You earned 1 month free! \U0001f389",
                "html": f"""<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:520px;margin:0 auto;padding:32px 24px;background:#ffffff;color:#111;">
                    <div style="font-size:48px;text-align:center;margin-bottom:16px;">\U0001f381</div>
                    <h2 style="text-align:center;margin:0 0 16px;">You earned 1 month of free ClawMetry Cloud!</h2>
                    <p style="font-size:15px;line-height:1.7;color:#333;">Someone signed up using your referral link. As a thank you, we have extended your Cloud Pro access by 30 days.</p>
                    <p style="font-size:15px;line-height:1.7;color:#333;">Keep sharing to earn more free months!</p>
                    <div style="text-align:center;margin:24px 0;">
                        <a href="https://app.clawmetry.com" style="display:inline-block;background:#E5443A;color:#fff;font-weight:700;font-size:14px;padding:10px 24px;border-radius:8px;text-decoration:none;">Open Dashboard</a>
                    </div>
                    <p style="font-size:13px;color:#666;">Your referral code: <strong>{ref_code}</strong></p>
                </div>""",
            })
        except Exception:
            pass

        # Notify Vivek
        try:
            _resend_post("/emails", {
                "from": FROM_EMAIL,
                "to": ["vivekchand19@gmail.com"],
                "subject": f"Referral conversion: {referrer_email} referred {new_email}",
                "html": f"<p><strong>{referrer_email}</strong> (code: {ref_code}) referred <strong>{new_email}</strong>. Referrer earned +30 days pro.</p>",
            })
        except Exception:
            pass

    except Exception as e:
        log.error(f"[referral] credit error: {e}")


@app.route("/ref/<code>")
def referral_redirect(code):
    """Redirect referral links to main page with ref tracking."""
    return redirect(f"/?ref={code}")


@app.route("/api/roadmap-vote", methods=["POST"])
def roadmap_vote():
    import hashlib
    data = request.get_json(silent=True) or {}
    feature = str(data.get("feature", "")).strip().lower()
    if feature not in VALID_FEATURES:
        return jsonify({"error": "invalid feature"}), 400

    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16] if ip else None

    fs = _fs()
    if fs:
        try:
            fs.collection("roadmap_votes").add({
                "feature": feature,
                "ip_hash": ip_hash,
                "created_at": _firestore_mod.SERVER_TIMESTAMP,
            })
        except Exception as e:
            log.warning(f"[roadmap-vote] firestore error: {e}")
    else:
        try:
            with _db() as db:
                db.execute(
                    "INSERT INTO roadmap_votes (feature, ip_hash) VALUES (?, ?)",
                    (feature, ip_hash)
                )
        except Exception as e:
            log.warning(f"[roadmap-vote] sqlite error: {e}")

    log.info(f"[roadmap-vote] feature={feature} ip_hash={ip_hash}")

    # Notify Vivek in background
    visitor = _get_visitor_info(request)
    def _notify_vote(feat, v):
        try:
            feature_labels = {
                "cloud": "Cloud version", "alerting": "Alerting",
                "hitl": "Human-in-the-loop", "mac-app": "Mac app",
                "ios-app": "iOS & Android", "frameworks": "More Claws support",
                "team": "Team features", "cost": "Cost analytics",
            }
            label = feature_labels.get(feat, feat)
            _resend_post("/emails", {
                "from": FROM_EMAIL,
                "to": [VIVEK_EMAIL],
                "subject": f"Roadmap vote: {label}",
                "html": (
                    f"<p style='font-size:15px;'><strong>{label}</strong> just got an upvote on the roadmap.</p>"
                    f"<table style='font-size:14px;border-collapse:collapse;'>"
                    f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>Location</td><td>{v.get('location','Unknown')}</td></tr>"
                    f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>Referrer</td><td>{v.get('referer','Direct')}</td></tr>"
                    f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>IP</td><td>{v.get('ip','')}</td></tr>"
                    f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>Browser</td>"
                    f"<td style='font-size:12px;color:#888;'>{v.get('user_agent','')[:120]}</td></tr>"
                    f"</table>"
                ),
            })
        except Exception as ex:
            log.warning(f"[roadmap-vote] notify error: {ex}")
    import threading
    threading.Thread(target=_notify_vote, args=(feature, visitor), daemon=True).start()

    return jsonify({"ok": True})


@app.route("/api/roadmap-votes", methods=["GET"])
def roadmap_votes_admin():
    """Admin endpoint to see vote tallies."""
    secret = request.args.get("secret", "")
    if secret != os.environ.get("ADMIN_SECRET", "clawmetry-admin"):
        return jsonify({"error": "unauthorized"}), 403

    fs = _fs()
    tallies = {f: 0 for f in VALID_FEATURES}
    if fs:
        try:
            docs = fs.collection("roadmap_votes").stream()
            for doc in docs:
                d = doc.to_dict()
                f = d.get("feature")
                if f in tallies:
                    tallies[f] += 1
        except Exception as e:
            log.warning(f"[roadmap-votes] firestore error: {e}")
    else:
        try:
            with _db() as db:
                rows = db.execute(
                    "SELECT feature, COUNT(*) as cnt FROM roadmap_votes GROUP BY feature"
                ).fetchall()
                for row in rows:
                    if row["feature"] in tallies:
                        tallies[row["feature"]] = row["cnt"]
        except Exception as e:
            log.warning(f"[roadmap-votes] sqlite error: {e}")

    sorted_tallies = dict(sorted(tallies.items(), key=lambda x: x[1], reverse=True))
    return jsonify({"votes": sorted_tallies})


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = _decrypt_payload(request)
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

        sub_data = {
            "email": email, "source": source, "utm_data": json.dumps(utm),
            "location": visitor['location'], "ip": visitor['ip'],
            "browser": visitor['user_agent'][:200], "subscribed_at": _now_iso(),
        }
        if not _fs_add("subscribers", sub_data):
            # Fallback to SQLite
            db = get_db()
            db.execute("INSERT INTO subscribers (email, source, utm_data, location, ip, browser) VALUES (?,?,?,?,?,?)",
                       (email, source, json.dumps(utm), visitor['location'], visitor['ip'], visitor['user_agent'][:200]))
            db.commit(); db.close()

        notify_vivek(
            f"🎉 [New Subscriber] {email}",
            f"""<div style="font-family:sans-serif;max-width:500px;text-align:center;">
            <div style="font-size:64px;margin:20px 0;">🎉</div>
            <h1 style="color:#E5443A;font-size:28px;margin:0 0 8px;">New ClawMetry Subscriber!</h1>
            <div style="background:#f8f9fa;border-radius:12px;padding:20px;text-align:left;margin:16px 0;">
            <p style="font-size:16px;margin:8px 0;"><strong>📧 Email:</strong> {email}</p>
            <p style="font-size:16px;margin:8px 0;"><strong>🔗 Source:</strong> {source}</p>
            <p style="font-size:16px;margin:8px 0;"><strong>📍 Location:</strong> {visitor['location']}</p>
            </div>
            {_utm_html(utm)}
            </div>"""
        )
    except Exception as e:
        log.error(f"[subscribe] {e}", exc_info=True)

    return jsonify({"ok": True, "message": "Subscribed!"})


@app.route("/api/managed-request", methods=["POST"])
def managed_request():
    """Lead capture for managed/cloud ClawMetry instances."""
    data = _decrypt_payload(request)
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    company = (data.get("company") or "").strip()
    instances = (data.get("instances") or "").strip()
    use_case = (data.get("use_case") or "").strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Invalid email"}), 400

    log.info(f"[managed-request] {name} <{email}> company={company}")

    visitor = _get_visitor_info(request)

    # Store in Firestore (or SQLite fallback)
    req_data = {
        "name": name, "email": email, "company": company, "use_case": use_case,
        "location": visitor['location'], "ip": visitor['ip'],
        "browser": visitor['user_agent'][:200], "created_at": _now_iso(),
    }
    if not _fs_add("managed_requests", req_data):
        try:
            db = get_db()
            db.execute("INSERT INTO managed_requests (name, email, company, use_case, location, ip, browser) VALUES (?,?,?,?,?,?,?)",
                       (name, email, company, use_case, visitor['location'], visitor['ip'], visitor['user_agent'][:200]))
            db.commit(); db.close()
        except Exception as e:
            log.error(f"[managed-request] DB error: {e}")

    # Fire emails in background so form returns in <200ms
    def _send_managed_emails():
        # Notify Vivek
        notify_vivek(
            f"🎉 [New Signup] Managed Instance Request from {name}!",
            f"""<div style="font-family:sans-serif;max-width:500px;text-align:center;">
        <div style="font-size:64px;margin:20px 0;">🎉</div>
        <h1 style="color:#E5443A;font-size:28px;margin:0 0 8px;">New Managed Instance Signup!</h1>
        <p style="font-size:18px;color:#333;margin:0 0 24px;">Someone wants ClawMetry hosted for them</p>
        <div style="background:#f8f9fa;border-radius:12px;padding:20px;text-align:left;margin:16px 0;">
        <p style="font-size:16px;margin:8px 0;"><strong>👤 Name:</strong> {name}</p>
        <p style="font-size:16px;margin:8px 0;"><strong>📧 Email:</strong> {email}</p>
        <p style="font-size:16px;margin:8px 0;"><strong>🏢 Company:</strong> {company or '(not provided)'}</p>
        <p style="font-size:16px;margin:8px 0;"><strong>🖥️ Instances:</strong> {instances or '(not provided)'}</p>
        <p style="font-size:16px;margin:8px 0;"><strong>📍 Location:</strong> {visitor['location']}</p>
        </div>
        {"<div style='background:#fff3cd;border:1px solid #ffc107;border-radius:8px;padding:16px;margin:16px 0;text-align:left;'><strong>💡 Use Case:</strong><br>" + use_case + "</div>" if use_case else ""}
        <p style="color:#666;font-size:13px;margin-top:20px;">Reply to them within 24h! → {email}</p>
        </div>"""
        )
        # AI follow-up
        _ai_result_managed = _ai_personalize_reply(name, use_case, "managed")
        ai_question_managed = _ai_result_managed.get("question") if _ai_result_managed else None
        ai_subject_managed = _ai_result_managed.get("subject") if _ai_result_managed else None
        # Build confirmation email HTML
        uc_block = (
            f'<div style="background:#f5f5f5;border-left:3px solid #ccc;border-radius:4px;padding:10px 16px;margin:14px 0;font-size:14px;color:#555;font-style:italic;">You mentioned: {use_case}</div>'
            if use_case else ""
        )
        email_html = f"""<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:560px;margin:0 auto;padding:32px 24px;background:#0d0d14;color:#e0e0e0;border-radius:12px;">
    <div style="text-align:center;margin-bottom:24px;">
      <div style="margin-bottom:8px;"><img src="https://clawmetry.com/favicon.svg" width="40" height="40" style="border-radius:6px" alt="ClawMetry"></div>
      <h2 style="color:#fff;margin:0 0 4px;font-size:20px;">You're in, {name}!</h2>
      <p style="color:#9ca3af;font-size:13px;margin:0;">Your ClawMetry account is live</p>
    </div>
    {uc_block}
    <p style="font-size:14px;line-height:1.7;color:#d1d5db;margin:0 0 20px;">Your dashboard is live at <a href="https://app.clawmetry.com" style="color:#E5443A;font-weight:600;">app.clawmetry.com</a>. Connect your first machine with two commands:</p>
    <div style="background:#111827;border:1px solid #1e2d40;border-radius:8px;padding:16px;margin:0 0 12px;">
      <p style="margin:0 0 6px;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">Step 1 — Install</p>
      <code style="color:#10b981;font-size:13px;display:block;word-break:break-all;">curl -fsSL https://clawmetry.com/install.sh | bash</code>
    </div>
    <div style="background:#111827;border:1px solid #1e2d40;border-radius:8px;padding:16px;margin:0 0 24px;">
      <p style="margin:0 0 6px;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">Step 2 — Onboard</p>
      <code style="color:#10b981;font-size:13px;display:block;">clawmetry onboard</code>
    </div>
    <div style="text-align:center;margin:24px 0;">
      <a href="https://app.clawmetry.com" style="display:inline-block;background:#E5443A;color:#fff;font-weight:700;font-size:15px;padding:12px 32px;border-radius:8px;text-decoration:none;">Open Your Dashboard &#x2192;</a>
    </div>
    <p style="font-size:13px;line-height:1.7;color:#64748b;margin:0 0 16px;">Your API key is in the dashboard under <a href="https://app.clawmetry.com/account" style="color:#E5443A;">Account</a>. Need help? Just hit reply.</p>
    <p style="font-size:15px;color:#e0e0e0;margin-top:24px;line-height:1.7;">Cheers,<br><strong style="color:#fff;">Vivek</strong><br><span style="font-size:13px;color:#64748b;">Founder, ClawMetry &middot; <a href="https://clawmetry.com" style="color:#E5443A;text-decoration:none;">clawmetry.com</a></span></p>
</div>"""
        try:
            _resend_post("/emails", {
                "from": FROM_EMAIL, "to": [email], "bcc": ["vivek@clawmetry.com"],
                "reply_to": ["vivek@clawmetry.com"],
                "subject": "You're in — here's how to connect your first agent",
                "html": email_html
            })
        except Exception as e:
            log.error(f"[managed-request] confirmation email error: {e}")

    threading.Thread(target=_send_managed_emails, daemon=True).start()
    return jsonify({"ok": True, "message": "Request received! We'll be in touch."})


@app.route("/api/support-request", methods=["POST"])
def support_request():
    """Handle free onboarding support requests."""
    visitor = _get_visitor_info(request)
    data = _decrypt_payload(request)
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    help_type = (data.get("help_type") or "").strip()
    message = (data.get("message") or "").strip()
    utm = data.get("utm", {})
    source = _format_source(utm, visitor['referer'])

    if not email:
        return jsonify({"ok": False, "error": "Email required"}), 400

    log.info(f"[support-request] {name} <{email}> type={help_type}")

    # Store in Firestore
    if _firestore_available:
        try:
            _firestore_db.collection("support_requests").add({
                "name": name, "email": email, "help_type": help_type,
                "message": message, "source": source,
                "ip": visitor['ip'], "ua": visitor['ua'],
                "utm": utm, "ts": _firestore_mod.SERVER_TIMESTAMP,
            })
        except Exception as e:
            log.error(f"[support-request] DB error: {e}")

    # Fire emails in background so form returns in <200ms
    def _send_support_emails():
        help_label = help_type.replace("-", " ").replace("_", " ").title() if help_type else "General"
        # Notify Vivek
        try:
            requests.post("https://api.resend.com/emails", headers={
                "Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"
            }, json={
                "from": FROM_EMAIL, "to": VIVEK_EMAIL,
                "subject": f"🤝 [Setup Help] {name or email} — {help_label}",
                "html": f"""<div style="font-family:sans-serif;max-width:600px;">
<h2>🤝 New Support Request</h2>
<table style="border-collapse:collapse;width:100%;">
<tr><td style="padding:8px;font-weight:bold;border-bottom:1px solid #eee;">Name</td><td style="padding:8px;border-bottom:1px solid #eee;">{name or '—'}</td></tr>
<tr><td style="padding:8px;font-weight:bold;border-bottom:1px solid #eee;">Email</td><td style="padding:8px;border-bottom:1px solid #eee;"><a href="mailto:{email}">{email}</a></td></tr>
<tr><td style="padding:8px;font-weight:bold;border-bottom:1px solid #eee;">Help Type</td><td style="padding:8px;border-bottom:1px solid #eee;">{help_label}</td></tr>
<tr><td style="padding:8px;font-weight:bold;border-bottom:1px solid #eee;">Message</td><td style="padding:8px;border-bottom:1px solid #eee;">{message or '—'}</td></tr>
<tr><td style="padding:8px;font-weight:bold;border-bottom:1px solid #eee;">Source</td><td style="padding:8px;border-bottom:1px solid #eee;">{source}</td></tr>
</table>
<p style="margin-top:16px;color:#666;">Reply directly to help them get set up.</p>
</div>"""
            }, timeout=10)
        except Exception as e:
            log.error(f"[support-request] notification email error: {e}")

        _ai_result = _ai_personalize_reply(name, message, help_type)
        ai_question = _ai_result.get("question") if _ai_result else None
        ai_subject = _ai_result.get("subject") if _ai_result else None
        # Send confirmation email to requester
        try:
            display_name = name or "there"
            msg_block = (
                f'<div style="background:#f5f5f5;border-left:3px solid #ccc;border-radius:4px;padding:10px 16px;margin:14px 0;font-size:14px;color:#555;font-style:italic;">You said: {message}</div>'
                if message else ""
            )
            question = ai_question or "Quick question first: where are you running OpenClaw? Mac mini, old laptop, a VPS like Hostinger or Railway, or still planning to try it?"
            email_html = f"""<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:520px;margin:0 auto;padding:32px 24px;background:#ffffff;color:#111111;">
    <p style="font-size:15px;line-height:1.7;margin:0 0 12px;">Hi {display_name},</p>
    <p style="font-size:15px;line-height:1.7;margin:0 0 12px;">Thanks for reaching out! I got your request and will personally get back to you shortly to help you get ClawMetry set up.</p>
    {msg_block}
    <p style="font-size:15px;line-height:1.7;color:#111;margin:12px 0;">{question}</p>
    <p style="font-size:15px;line-height:1.7;color:#111;margin:0 0 24px;">Either way I can help, just want to make sure the setup guide I send actually fits your situation.</p>
    <p style="font-size:15px;color:#111;margin:0;line-height:1.7;">Vivek<br><span style="font-size:13px;color:#666;">Founder, ClawMetry &middot; <a href="https://clawmetry.com" style="color:#E5443A;text-decoration:none;">clawmetry.com</a></span></p>
</div>"""
            requests.post("https://api.resend.com/emails", headers={
                "Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"
            }, json={
                "from": FROM_EMAIL, "to": email, "bcc": ["vivek@clawmetry.com"],
                "reply_to": ["vivek@clawmetry.com"],
                "subject": ai_subject or "Quick question before I set up ClawMetry for you",
                "html": email_html
            }, timeout=10)
        except Exception as e:
            log.error(f"[support-request] confirmation email error: {e}")

    threading.Thread(target=_send_support_emails, daemon=True).start()
    return jsonify({"ok": True, "message": "We'll be in touch!"})


@app.route("/api/managed-click", methods=["POST"])
def managed_click():
    """Track when someone clicks the managed instance CTA."""
    visitor = _get_visitor_info(request)
    data = _decrypt_payload(request)
    utm = data.get("utm", {})
    source = _format_source(utm, visitor['referer'])
    click_source = data.get("source", "")  # 'support' if from support modal
    is_support = click_source == "support"
    evt_label = "Support CTA clicked" if is_support else "Managed instance CTA clicked"
    evt_tab = "support-cta" if is_support else "managed-cta"
    evt = {
        "tab": evt_tab, "command": evt_label,
        "source": source, "utm_data": json.dumps(utm),
        "location": visitor['location'], "ip": visitor['ip'],
        "browser": visitor['user_agent'][:200], "created_at": _now_iso(),
    }
    if not _fs_add("copy_events", evt):
        try:
            db = get_db()
            db.execute("INSERT INTO copy_events (tab, command, source, utm_data, location, ip, browser) VALUES (?,?,?,?,?,?,?)",
                       ("managed-cta", "Managed instance CTA clicked", source, json.dumps(utm), visitor['location'], visitor['ip'], visitor['user_agent'][:200]))
            db.commit(); db.close()
        except Exception as e:
            log.error(f"[managed-click] db error: {e}")
    identity = data.get("identity", {})
    id_name = identity.get("name", "")
    id_email = identity.get("email", "")
    id_line = f"<p style='margin:4px 0;'><strong>Known as:</strong> {id_name} &lt;{id_email}&gt;</p>" if id_email else "<p style='margin:4px 0;color:#999;'>Anonymous visitor</p>"
    subject_who = f" — {id_name or id_email}" if id_email else ""
    click_emoji = "🤝" if is_support else "👀"
    click_label = "Support" if is_support else "Managed Instance"
    click_desc = "free onboarding support form" if is_support else "managed instance form"
    notify_vivek(
        f"{click_emoji} [Click] {click_label}{subject_who}",
        f"""<div style="font-family:sans-serif;max-width:500px;text-align:center;">
        <div style="font-size:48px;margin:16px 0;">{click_emoji}</div>
        <h2 style="color:#666;font-size:20px;">{click_label} CTA Clicked</h2>
        <p style="color:#999;">A visitor opened the {click_desc} on clawmetry.com</p>
        <div style="background:#f8f9fa;border-radius:8px;padding:14px;text-align:left;margin:12px 0;">
        {id_line}
        <p style="margin:4px 0;"><strong>Source:</strong> {source}</p>
        <p style="margin:4px 0;"><strong>Location:</strong> {visitor['location']}</p>
        </div>
        <p style="color:#aaa;font-size:12px;">Watch for a 🎉 [New Signup] email if they submit the form.</p>
        </div>"""
    )
    return jsonify({"ok": True})


@app.route("/api/copy-track", methods=["POST"])
def copy_track():
    data = _decrypt_payload(request)
    tab = data.get("tab", "unknown"); command = data.get("command", ""); utm = data.get("utm", {})
    visitor = _get_visitor_info(request)
    source = _format_source(utm, visitor['referer'])

    evt = {
        "tab": tab, "command": command, "source": source, "utm_data": json.dumps(utm),
        "location": visitor['location'], "ip": visitor['ip'],
        "browser": visitor['user_agent'][:200], "created_at": _now_iso(),
    }
    if not _fs_add("copy_events", evt):
        try:
            db = get_db()
            db.execute("INSERT INTO copy_events (tab, command, source, utm_data, location, ip, browser) VALUES (?,?,?,?,?,?,?)",
                       (tab, command, source, json.dumps(utm), visitor['location'], visitor['ip'], visitor['user_agent'][:200]))
            db.commit(); db.close()
        except Exception as e:
            log.error(f"[copy-track] db error: {e}")

    identity = data.get("identity", {})
    id_email = identity.get("email", "")
    id_name = identity.get("name", "")
    who = f" by {id_name or id_email}" if id_email else ""
    if tab == "agent":
        _resend_post("/emails", {
            "from": FROM_EMAIL, "to": [VIVEK_EMAIL],
            "subject": f"🤖 Agent tab copied{who} [{source}]",
            "html": f"""<div style="font-family:sans-serif;max-width:500px;">
            <h2>🤖 Agent Tab Copied!</h2>
            {f"<p><strong>👤 User:</strong> {id_name} &lt;{id_email}&gt;</p>" if id_email else "<p><strong>👤 User:</strong> Anonymous</p>"}
            <p><strong>Command:</strong> <code>{command}</code></p>
            <p style="font-size:18px;color:#E5443A;"><strong>Source:</strong> {source}</p>
            <p><strong>Location:</strong> {visitor['location']}</p>
            </div>"""
        })
    else:
        notify_vivek(
            f"🦞 [Install Copy] {tab}{who} [{source}]",
            f"""<div style="font-family:sans-serif;max-width:500px;">
            <h2>Install Command Copied!</h2>
            {f"<p><strong>👤 User:</strong> {id_name} &lt;{id_email}&gt;</p>" if id_email else "<p><strong>👤 User:</strong> Anonymous</p>"}
            <p><strong>Tab:</strong> {tab}</p><p><strong>Command:</strong> <code>{command}</code></p>
            <p style="font-size:18px;color:#E5443A;"><strong>Source:</strong> {source}</p>
            <p><strong>Location:</strong> {visitor['location']}</p>
            </div>"""
        )
    return jsonify({"ok": True})



@app.route("/api/social-click", methods=["POST"])
def social_click():
    """Track when someone clicks a testimonial/social link."""
    data = _decrypt_payload(request)
    visitor = _get_visitor_info(request)
    utm = data.get("utm", {})
    source = _format_source(utm, visitor['referer'])
    url = data.get("url", "unknown")
    author = data.get("author", "unknown")
    platform = data.get("platform", "unknown")

    evt = {
        "tab": "social-click", "command": f"{platform}: {author}",
        "source": source, "utm_data": json.dumps(utm),
        "location": visitor['location'], "ip": visitor['ip'],
        "browser": visitor['user_agent'][:200], "created_at": _now_iso(),
    }
    if not _fs_add("copy_events", evt):
        try:
            db = get_db()
            db.execute("INSERT INTO copy_events (tab, command, source, utm_data, location, ip, browser) VALUES (?,?,?,?,?,?,?)",
                       ("social-click", f"{platform}: {author}", source, json.dumps(utm), visitor['location'], visitor['ip'], visitor['user_agent'][:200]))
            db.commit(); db.close()
        except Exception as e:
            log.error(f"[social-click] db error: {e}")

    identity = data.get("identity", {})
    id_email = identity.get("email", "")
    id_name = identity.get("name", "")
    who_line = f"<p style='margin:4px 0;'><strong>Known as:</strong> {id_name} &lt;{id_email}&gt;</p>" if id_email else "<p style='margin:4px 0;color:#999;'>Anonymous visitor</p>"

    platform_emoji = {"twitter": "🐦", "producthunt": "🏆", "medium": "📝", "linkedin": "💼", "instagram": "📸"}.get(platform, "🔗")

    notify_vivek(
        f"{platform_emoji} [Social Click] {author} [{source}]",
        f"""<div style="font-family:sans-serif;max-width:500px;text-align:center;">
        <div style="font-size:48px;margin:16px 0;">{platform_emoji}</div>
        <h2 style="color:#666;font-size:20px;">Testimonial Card Clicked</h2>
        <p style="color:#999;">A visitor clicked a social proof card on clawmetry.com</p>
        <div style="background:#f8f9fa;border-radius:8px;padding:14px;text-align:left;margin:12px 0;">
        {who_line}
        <p style="margin:4px 0;"><strong>Author:</strong> {author}</p>
        <p style="margin:4px 0;"><strong>Platform:</strong> {platform}</p>
        <p style="margin:4px 0;"><strong>Link:</strong> <a href="{url}">{url[:80]}</a></p>
        <p style="margin:4px 0;"><strong>Source:</strong> {source}</p>
        <p style="margin:4px 0;"><strong>Location:</strong> {visitor['location']}</p>
        </div>
        <p style="color:#aaa;font-size:12px;">Track social proof engagement to see which testimonials drive conversions.</p>
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

    # Handle click / open tracking events
    if event_type in ("email.clicked", "email.opened"):
        click = payload.get("click", {})
        link = click.get("link", payload.get("link", ""))
        ip = click.get("ip_address", payload.get("ip_address", ""))
        ua = click.get("user_agent", payload.get("user_agent", ""))
        to = payload.get("to", [])
        to_addr = to[0] if isinstance(to, list) and to else str(to)
        # Geo lookup
        location = "Unknown"
        try:
            if ip:
                geo = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2).json()
                loc = ", ".join(filter(None, [geo.get("city",""), geo.get("region",""), geo.get("country_name","")]))
                if loc: location = loc
        except Exception:
            pass
        action = "clicked a link in" if event_type == "email.clicked" else "opened"
        subject_line = f"Email {action.split()[0]}: {to_addr}"
        body_html = (
            f"<p style='font-size:15px;'><strong>{to_addr}</strong> {action} your email.</p>"
            f"<table style='font-size:14px;border-collapse:collapse;'>"
            + (f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>Link</td><td><a href='{link}'>{link}</a></td></tr>" if link else "")
            + f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>Location</td><td>{location}</td></tr>"
            f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>IP</td><td>{ip}</td></tr>"
            f"<tr><td style='padding:4px 12px 4px 0;color:#666;'>Browser</td><td style='font-size:12px;color:#888;'>{ua[:120]}</td></tr>"
            f"</table>"
        )
        try:
            _resend_post("/emails", {"from": FROM_EMAIL, "to": [VIVEK_EMAIL], "subject": subject_line, "html": body_html})
        except Exception as ex:
            log.warning(f"[webhook/click] notify error: {ex}")
        log.info(f"[webhook/{event_type}] to={to_addr} link={link} location={location}")
        return jsonify({"ok": True})

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

    # Extract Message-ID for threading
    message_id = payload.get("message_id", "") or payload.get("headers", {}).get("message-id", "")

    # Extract attachments
    attachments = []
    for att in payload.get("attachments", []):
        attachments.append({
            "filename": att.get("filename", att.get("name", "attachment")),
            "content_type": att.get("content_type", att.get("type", "")),
            "url": att.get("url", ""),
        })

    email_data = {
        "from_email": from_email, "from_name": from_name, "to_email": to_email,
        "subject": subject, "body_html": body_html, "body_text": body_text,
        "message_id": message_id, "attachments": attachments,
        "received_at": _now_iso(), "read": 0, "replied": 0,
    }
    if not _fs_add("emails_received", email_data):
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

@app.route("/signin")
@app.route("/login")
def signin_page():
    """Sign-in page - same as connect but in sign-in mode."""
    return send_from_directory(".", "connect.html")

@app.route("/connect")
def connect_page():
    return send_from_directory(".", "connect.html")


@app.route("/api/connect", methods=["POST"])
def api_connect():
    import uuid
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    node_name = str(data.get("node_name", "my-agent")).strip() or "my-agent"

    if not email or "@" not in email:
        return jsonify({"error": "Valid email required"}), 400

    api_key = "cm_" + uuid.uuid4().hex[:24]
    created_at = _now_iso()

    key_doc = {
        "email": email,
        "api_key": api_key,
        "node_name": node_name,
        "created_at": created_at,
        "status": "active",
    }

    # Store in Firestore
    _fs_add("api_keys", key_doc)

    # Also subscribe to Resend audience
    try:
        _resend_post(f"/audiences/{RESEND_AUDIENCE_ID}/contacts", {"email": email, "unsubscribed": False})
    except Exception:
        pass

    # Email the key to the user
    key_email_html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:520px;margin:0 auto;">
      <div style="background:#0B0F1A;padding:24px 28px 16px;border-radius:12px 12px 0 0;">
        <div style="font-size:20px;font-weight:800;color:#fff;"><img src="https://clawmetry.com/favicon.svg" width="22" height="22" style="vertical-align:middle;border-radius:4px;margin-right:6px" alt="">Claw<span style="color:#E5443A;">metry</span></div>
      </div>
      <div style="background:#fff;padding:28px;border-radius:0 0 12px 12px;border:1px solid #e2e8f0;border-top:none;">
        <p style="font-size:15px;color:#111;margin:0 0 16px;">Here is your ClawMetry API key:</p>
        <div style="background:#0d1117;border-radius:8px;padding:16px;font-family:monospace;font-size:13px;color:#22c55e;word-break:break-all;margin-bottom:20px;">{api_key}</div>
        <p style="font-size:14px;color:#374151;margin:0 0 6px;font-weight:600;">Next steps:</p>
        <ol style="font-size:14px;color:#374151;padding-left:20px;line-height:2;">
          <li>Install: <code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:12px;">curl -fsSL https://clawmetry.com/install.sh | bash</code></li>
          <li>Run: <code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:12px;">clawmetry onboard</code> and paste your API key</li>
          <li>Open <a href="https://app.clawmetry.com" style="color:#E5443A;">app.clawmetry.com</a> and enter the secret key from your terminal for E2E encryption</li>
        </ol>
        <p style="font-size:13px;color:#94a3b8;margin-top:20px;">Questions? Reply to this email.</p>
      </div>
    </div>"""

    _resend_post("/emails", {
        "from": FROM_EMAIL,
        "to": [email],
        "reply_to": VIVEK_EMAIL,
        "subject": "Your ClawMetry API key",
        "html": key_email_html,
    })

    # Notify Vivek
    def _notify():
        _resend_post("/emails", {
            "from": FROM_EMAIL, "to": [VIVEK_EMAIL],
            "subject": f"New cloud connect: {email}",
            "html": f"<p><b>{email}</b> just requested a ClawMetry cloud API key.</p><p>Node: {node_name}</p><p>Key: <code>{api_key}</code></p>",
        })
    import threading
    threading.Thread(target=_notify, daemon=True).start()

    log.info(f"[connect] new key for {email} node={node_name}")
    return jsonify({"ok": True, "api_key": api_key})


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if email != ADMIN_EMAIL:
            error = "Access denied."
        else:
            otp = _generate_otp(email)
            _send_otp_email(email, otp)
            return redirect("/admin/verify")
    return render_template_string(LOGIN_PAGE, error=error)


@app.route("/admin/verify", methods=["GET", "POST"])
def admin_verify():
    error = ""
    if request.method == "POST":
        otp = (request.form.get("otp") or "").strip()
        if _verify_otp(ADMIN_EMAIL, otp):
            session["admin"] = True
            return redirect("/admin")
        error = "Invalid or expired code."
    return render_template_string(VERIFY_PAGE, error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin/login")


@app.route("/admin")
@login_required
def admin_dashboard():
    resend_contacts = get_all_contacts()

    subs = len(resend_contacts) or (_fs_count("subscribers") or 0)
    emails_count = _fs_count("emails_received") or 0
    unread_list = _fs_query("emails_received", "read", "==", 0)
    unread = len(unread_list) if unread_list else 0
    events_count = _fs_count("copy_events") or 0
    sent_count = _fs_count("emails_sent") or 0
    recent_emails = _fs_get_all("emails_received", order_by="received_at", limit=5) or []
    recent_subs = _fs_get_all("subscribers", order_by="subscribed_at", limit=5) or []

    rows_emails = ""
    for e in recent_emails:
        badge = '<span class="badge badge-unread">NEW</span>' if not e.get("read") else '<span class="badge badge-read">read</span>'
        rows_emails += f'<tr><td><a href="/admin/inbox/{e["id"]}">{e.get("from_name") or e.get("from_email")}</a></td><td>{e.get("subject","")}</td><td>{badge}</td><td>{e.get("received_at","")}</td></tr>'

    rows_subs = ""
    for s in recent_subs:
        rows_subs += f'<tr><td>{s.get("email","")}</td><td>{s.get("source") or "-"}</td><td>{s.get("location") or "-"}</td><td>{s.get("subscribed_at","")}</td></tr>'

    html = f"""
    <h2 style="margin-bottom:20px">Dashboard</h2>
    <div class="stat-grid">
      <div class="card stat"><h3>{subs}</h3><p>Subscribers</p></div>
      <div class="card stat"><h3>{emails_count}</h3><p>Emails Received ({unread} unread)</p></div>
      <div class="card stat"><h3>{sent_count}</h3><p>Emails Sent</p></div>
      <div class="card stat"><h3>{events_count}</h3><p>Copy Events</p></div>
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
    emails = _fs_get_all("emails_received", order_by="received_at") or []

    if not emails:
        html = '<h2 style="margin-bottom:20px">Inbox</h2><div class="card"><p class="empty">No emails received yet. Send one to hello@clawmetry.com!</p></div>'
        return _render_admin("Inbox", html, "inbox")

    rows = ""
    for e in emails:
        badge = '<span class="badge badge-unread">NEW</span>' if not e.get("read") else '<span class="badge badge-read">read</span>'
        replied = ' 📨' if e.get("replied") else ''
        name = e.get("from_name") or e.get("from_email","")
        rows += f'<tr><td><a href="/admin/inbox/{e["id"]}"><strong>{name}</strong></a></td><td><a href="/admin/inbox/{e["id"]}">{e.get("subject","")}</a></td><td>{badge}{replied}</td><td style="white-space:nowrap">{e.get("received_at","")}</td></tr>'

    html = f"""
    <h2 style="margin-bottom:20px">Inbox <span style="color:var(--muted);font-size:16px">({len(emails)} emails)</span></h2>
    <div class="card"><table><th>From</th><th>Subject</th><th>Status</th><th>Date</th>{rows}</table></div>
    """
    return _render_admin("Inbox", html, "inbox")


def _normalize_subject(s):
    """Strip Re:/Fwd: prefixes for thread matching."""
    s = (s or "").strip()
    while True:
        lower = s.lower()
        if lower.startswith("re:") or lower.startswith("fw:"):
            s = s[3:].strip()
        elif lower.startswith("fwd:"):
            s = s[4:].strip()
        else:
            break
    return s


def _render_email_body(e):
    """Render email body, handling empty bodies with attachments."""
    body_html = e.get("body_html", "")
    body_text = e.get("body_text", "")
    attachments = e.get("attachments", [])

    # Build body content
    if body_html:
        content = body_html
    elif body_text:
        content = f'<pre style="white-space:pre-wrap;color:var(--text)">{body_text}</pre>'
    else:
        content = ""

    # Render attachments
    att_html = ""
    if attachments:
        for att in attachments:
            fname = att.get("filename", att.get("name", "attachment"))
            content_type = att.get("content_type", att.get("type", ""))
            url = att.get("url", "")
            if content_type.startswith("image/") and url:
                att_html += f'<div style="margin:8px 0"><img src="{url}" alt="{fname}" style="max-width:100%;max-height:400px;border-radius:8px;border:1px solid var(--border)"></div>'
            elif url:
                att_html += f'<div style="margin:4px 0">📎 <a href="{url}" target="_blank">{fname}</a></div>'
            else:
                att_html += f'<div style="margin:4px 0">📎 {fname}</div>'

    if not content and not att_html:
        content = '<p style="color:var(--muted);font-style:italic">(no content)</p>'

    return content + att_html


def _build_thread(e):
    """Build full email thread: all sent+received emails for this contact, chronologically."""
    contact_email = e.get("from_email", "")
    base_subject = _normalize_subject(e.get("subject", ""))

    # Get all sent emails to this contact
    all_sent = _fs_get_all("emails_sent", order_by="sent_at", order_dir="ASCENDING") or []
    # Get all received emails from this contact
    all_received = _fs_get_all("emails_received", order_by="received_at", order_dir="ASCENDING") or []

    thread = []

    # Match by email address (primary) and optionally by subject
    for s in all_sent:
        to = (s.get("to_email", "") or "").lower()
        subj = _normalize_subject(s.get("subject", ""))
        if to == contact_email.lower() or (base_subject and subj == base_subject):
            thread.append({
                "type": "sent", "sender": "You (ClawMetry)",
                "recipient": s.get("to_email", ""),
                "subject": s.get("subject", ""),
                "body": s, "timestamp": s.get("sent_at", ""),
                "id": s.get("id", ""),
            })

    for r in all_received:
        frm = (r.get("from_email", "") or "").lower()
        subj = _normalize_subject(r.get("subject", ""))
        if frm == contact_email.lower() or (base_subject and subj == base_subject):
            thread.append({
                "type": "received",
                "sender": r.get("from_name") or r.get("from_email", ""),
                "recipient": r.get("to_email", ""),
                "subject": r.get("subject", ""),
                "body": r, "timestamp": r.get("received_at", ""),
                "id": r.get("id", ""),
            })

    # Sort chronologically — normalize timestamps to strings for comparison
    def _ts_key(x):
        t = x.get("timestamp", "")
        if hasattr(t, "isoformat"):
            return t.isoformat()
        return str(t) if t else ""
    thread.sort(key=_ts_key)
    return thread


@app.route("/admin/inbox/<eid>")
@login_required
def admin_view_email(eid):
    e = _fs_get("emails_received", eid)
    if not e:
        return redirect("/admin/inbox")
    if not e.get("read"):
        _fs_update("emails_received", eid, {"read": 1})

    thread = _build_thread(e)

    # Build conversation thread HTML
    thread_html = ""
    for msg in thread:
        is_sent = msg["type"] == "sent"
        body_html = _render_email_body(msg["body"])

        if is_sent:
            # Right-aligned, accent colored — like a chat bubble from "you"
            thread_html += f"""
    <div style="display:flex;justify-content:flex-end;margin-bottom:12px">
      <div style="max-width:85%;background:rgba(229,68,58,0.08);border:1px solid rgba(229,68,58,0.25);border-radius:12px 12px 4px 12px;padding:16px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
          <span style="background:var(--accent);border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:12px;color:#fff">✉️</span>
          <div><strong style="color:var(--accent)">You</strong> → {msg["recipient"]}
          <span style="color:var(--muted);font-size:11px;margin-left:8px">{msg["timestamp"]}</span></div>
        </div>
        <div class="email-body" style="background:transparent;border:none;padding:0;max-height:300px;overflow:auto">{body_html}</div>
      </div>
    </div>"""
        else:
            # Left-aligned — inbound message
            thread_html += f"""
    <div style="display:flex;justify-content:flex-start;margin-bottom:12px">
      <div style="max-width:85%;background:var(--surface);border:1px solid var(--border);border-radius:12px 12px 12px 4px;padding:16px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
          <span style="background:var(--border);border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:12px">📨</span>
          <div><strong>{msg["sender"]}</strong>
          <span style="color:var(--muted);font-size:11px;margin-left:8px">{msg["timestamp"]}</span></div>
        </div>
        <div class="email-body" style="background:transparent;border:none;padding:0;max-height:300px;overflow:auto">{body_html}</div>
      </div>
    </div>"""

    if not thread:
        thread_html = '<p class="empty">No messages found</p>'

    html = f"""
    <p><a href="/admin/inbox" class="btn btn-outline" style="margin-bottom:16px">← Back to Inbox</a></p>
    <div style="margin-bottom:16px">
      <p style="color:var(--muted);font-size:13px">Thread with: <strong style="color:var(--text)">{e.get("from_name","") or ""} &lt;{e.get("from_email","")}&gt;</strong></p>
      <h2 style="margin:8px 0">{e.get("subject","")}</h2>
    </div>
    <h3 style="color:var(--muted);font-size:14px;margin-bottom:12px">Conversation ({len(thread)} messages)</h3>
    <div style="padding:8px 0">{thread_html}</div>
    <div class="card" style="margin-top:16px">
      <h3 style="margin-bottom:12px">↩ Quick Reply</h3>
      <form method="POST" action="/admin/inbox/{eid}/reply">
        <textarea name="body" rows="6" placeholder="Type your reply..." required style="margin-bottom:12px"></textarea>
        <button type="submit" class="btn btn-primary">Send Reply</button>
      </form>
    </div>
    """
    return _render_admin(e["subject"], html, "inbox")


@app.route("/admin/inbox/<eid>/reply", methods=["GET", "POST"])
@login_required
def admin_reply_email(eid):
    from flask import flash

    e = _fs_get("emails_received", eid)

    if not e:
        return redirect("/admin/inbox")

    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if body:
            body_html = body.replace("\n", "<br>")
            subj = e.get("subject", "")
            subject = f"Re: {subj}" if not subj.startswith("Re:") else subj

            # Build threading headers
            email_payload = {
                "from": FROM_EMAIL, "to": [e.get("from_email","")],
                "subject": subject, "html": body_html,
            }
            orig_msg_id = e.get("message_id", "")
            if orig_msg_id:
                email_payload["headers"] = {
                    "In-Reply-To": orig_msg_id,
                    "References": orig_msg_id,
                }

            ok, resp = _resend_post("/emails", email_payload)
            if ok:
                resend_id = resp.get("id", "")
                sent_data = {
                    "to_email": e.get("from_email",""), "subject": subject,
                    "body_html": body_html, "sent_at": _now_iso(), "in_reply_to": eid,
                    "resend_id": resend_id,
                }
                _fs_add("emails_sent", sent_data)
                _fs_update("emails_received", eid, {"replied": 1})
                flash("Reply sent!", "success")
            else:
                flash(f"Failed to send: {resp}", "error")
        return redirect(f"/admin/inbox/{eid}")

    html = f"""
    <p><a href="/admin/inbox/{eid}" class="btn btn-outline">← Back</a></p>
    <div class="card">
      <h2 style="margin-bottom:4px">Reply to {e.get("from_name") or e.get("from_email","")}</h2>
      <p style="color:var(--muted);font-size:13px;margin-bottom:16px">Re: {e.get("subject","")}</p>
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
                sent_data = {"to_email": to, "subject": subject, "body_html": body_html, "sent_at": _now_iso(), "in_reply_to": ""}
                _fs_add("emails_sent", sent_data)
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



BLAST_EMAIL_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:520px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    <div style="background:#0B0F1A;padding:28px 32px 20px;">
      <div style="font-size:22px;font-weight:800;color:#fff;letter-spacing:-0.02em;"><img src="https://clawmetry.com/favicon.svg" width="22" height="22" style="vertical-align:middle;border-radius:4px;margin-right:6px" alt="">Claw<span style="color:#E5443A;">metry</span></div>
      <p style="font-size:13px;color:#94a3b8;margin:4px 0 0;">Real-time observability for your AI agents</p>
    </div>
    <div style="padding:32px;">
      <p style="font-size:15px;color:#111;line-height:1.7;margin:0 0 16px;">Hey &#x1F44B;</p>
      <p style="font-size:15px;color:#111;line-height:1.7;margin:0 0 16px;">
        Thanks for being an early ClawMetry user. Since you signed up, a lot has shipped:
        the <strong>cloud version</strong> (connect any OpenClaw instance with one command),
        a redesigned dashboard, and 7-day history for agents and sub-agents.
      </p>
      <p style="font-size:15px;color:#111;line-height:1.7;margin:0 0 24px;">
        Want to see how it all fits together:
      </p>
      <div style="text-align:center;margin:0 0 28px;">
        <a href="https://clawmetry.com/how-it-works" style="display:inline-block;background:#E5443A;color:#fff;font-weight:700;font-size:14px;padding:13px 28px;border-radius:10px;text-decoration:none;">See how it works</a>
      </div>
      <p style="font-size:15px;color:#111;line-height:1.7;margin:0 0 12px;font-weight:600;">What we are building next:</p>
      <ul style="margin:0 0 24px;padding-left:20px;color:#374151;font-size:14px;line-height:2.1;">
        <li><strong>Alerting</strong> - PagerDuty, Slack, Telegram when an agent loops or goes silent</li>
        <li><strong>Human-in-the-loop</strong> - pause, inspect, and approve actions before they run</li>
        <li><strong>Mobile apps</strong> - iOS and Android, manage agents from your phone</li>
        <li><strong>Team features</strong> - shared dashboards, audit logs, role-based access</li>
      </ul>
      <a href="https://clawmetry.com/roadmap" style="display:block;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px 18px;text-decoration:none;margin-bottom:28px;">
        <span style="font-size:14px;color:#111;font-weight:600;">Full roadmap + vote on what ships next</span>
        <span style="font-size:13px;color:#E5443A;display:block;margin-top:2px;">clawmetry.com/roadmap &#x2192;</span>
      </a>
      <div style="background:#fff7f7;border:1px solid #ffd5d5;border-radius:10px;padding:20px;margin-bottom:28px;">
        <p style="font-size:15px;font-weight:700;color:#111;margin:0 0 8px;">&#x1F4AC; Had a chance to use ClawMetry?</p>
        <p style="font-size:13px;color:#555;margin:0 0 14px;line-height:1.6;">A quick review on Product Hunt helps other OpenClaw users find us. Takes about 2 minutes.</p>
        <a href="https://www.producthunt.com/products/clawmetry/reviews/new" style="display:inline-block;background:#ff6154;color:#fff;font-weight:700;font-size:13px;padding:10px 22px;border-radius:8px;text-decoration:none;">Write a review &#x2192;</a>
      </div>
      <p style="font-size:14px;color:#374151;margin:0 0 4px;">Vivek</p>
      <p style="font-size:13px;color:#94a3b8;margin:0;">Founder, ClawMetry</p>
    </div>
    <div style="border-top:1px solid #f1f5f9;padding:16px 32px;text-align:center;">
      <p style="font-size:12px;color:#94a3b8;margin:0;">
        You are receiving this because you subscribed at clawmetry.com.
        <a href="{{unsubscribe_url}}" style="color:#94a3b8;">Unsubscribe</a>
      </p>
    </div>
  </div>
</body>
</html>"""


@app.route("/admin/blast", methods=["GET", "POST"])
@login_required
def admin_blast():
    from flask import flash
    import html as html_lib
    contacts = get_all_contacts() or []
    count = len(contacts)

    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        html_body = request.form.get("html_body", "").strip()
        confirm = request.form.get("confirm", "")

        if confirm != "SEND":
            flash("Type SEND in the confirmation box to proceed.", "error")
        elif not subject or not html_body:
            flash("Subject and body required.", "error")
        else:
            ok1, bc = _resend_post("/broadcasts", {
                "audience_id": RESEND_AUDIENCE_ID,
                "from": FROM_EMAIL,
                "name": "Blast: " + subject,
                "subject": subject,
                "html": html_body,
            })
            if not ok1:
                flash("Failed to create broadcast: " + str(bc), "error")
            else:
                bc_id = (bc.get("data") or {}).get("id") or bc.get("id")
                if not bc_id:
                    flash("No broadcast ID returned: " + str(bc), "error")
                else:
                    ok2, resp2 = _resend_post("/broadcasts/" + bc_id + "/send", {})
                    if ok2:
                        _fs_add("emails_sent", {
                            "to_email": "[BLAST to " + str(count) + " subscribers]",
                            "subject": subject,
                            "body_html": html_body[:500],
                            "sent_at": _now_iso(),
                            "in_reply_to": "",
                        })
                        flash("Blast sent to " + str(count) + " subscribers! Broadcast ID: " + bc_id, "success")
                        return redirect("/admin/blast")
                    else:
                        flash("Broadcast created (" + bc_id + ") but send failed: " + str(resp2), "error")

    escaped_template = html_lib.escape(BLAST_EMAIL_HTML.strip())
    page_html = (
        '''<div class="card" style="max-width:740px;">'''
        '''<h2 style="margin-bottom:4px">Email Blast</h2>'''
        '''<p style="color:var(--muted);font-size:13px;margin-bottom:20px;">Sends to all <strong>'''
        + str(count) +
        '''</strong> subscribed contacts via Resend Broadcasts.</p>'''
        '''<form method="POST">'''
        '''<label>Subject</label>'''
        '''<input type="text" name="subject" value="What&apos;s new in ClawMetry" required style="margin-bottom:14px;">'''
        '''<label>HTML Body</label>'''
        '''<textarea name="html_body" rows="22" required style="font-family:monospace;font-size:12px;">'''
        + escaped_template +
        '''</textarea>'''
        '''<label style="margin-top:14px;">Type <strong>SEND</strong> to confirm</label>'''
        '''<input type="text" name="confirm" placeholder="SEND" required style="max-width:120px;margin-bottom:16px;">'''
        '''<div><button type="submit" class="btn btn-danger">Send blast to '''
        + str(count) +
        ''' subscribers</button></div></form></div>'''
    )
    return _render_admin("Email Blast", page_html, "blast")


@app.route("/admin/sent")
@login_required
def admin_sent():
    emails = _fs_get_all("emails_sent", order_by="sent_at") or []
    rows = ""
    for e in emails:
        rows += f'<tr><td>{e.get("to_email","")}</td><td>{e.get("subject","")}</td><td>{e.get("sent_at","")}</td></tr>'
    html = f"""
    <h2 style="margin-bottom:16px">Sent Emails ({len(emails)})</h2>
    <table><thead><tr><th>To</th><th>Subject</th><th>Sent</th></tr></thead><tbody>{rows or '<tr><td colspan="3" style="text-align:center;color:var(--muted)">No sent emails yet</td></tr>'}</tbody></table>
    """
    return _render_admin("Sent", html, "sent")


@app.route("/admin/subscribers")
@login_required
def admin_subscribers():
    resend_contacts = get_all_contacts()

    fs_subs = _fs_get_all("subscribers", order_by="subscribed_at") or []
    local_subs = {s.get("email","").lower(): s for s in fs_subs}

    if not resend_contacts and not local_subs:
        html = '<h2>Subscribers</h2><div class="card"><p class="empty">No subscribers yet</p></div>'
        return _render_admin("Subscribers", html, "subs")

    rows = ""
    for c in resend_contacts:
        email = c.get("email", "")
        local = local_subs.get(email.lower(), {})
        source = local.get("source", "-") if local else "-"
        location = local.get("location", "-") if local else "-"
        created = c.get("created_at", local.get("subscribed_at", "-") if local else "-")
        if isinstance(created, str) and "T" in created:
            created = created[:19].replace("T", " ")
        rows += f'<tr><td>{email}</td><td>{source}</td><td>{location}</td><td style="white-space:nowrap">{created}</td></tr>'

    html = f"""
    <h2 style="margin-bottom:20px">Subscribers <span style="color:var(--muted);font-size:16px">({len(resend_contacts)})</span></h2>
    <div class="card"><table><th>Email</th><th>Source</th><th>Location</th><th>Date</th>{rows}</table></div>
    """
    return _render_admin("Subscribers", html, "subs")


@app.route("/admin/events")
@login_required
def admin_events():
    events = _fs_get_all("copy_events", order_by="created_at") or []

    if not events:
        html = '<h2>Copy Events</h2><div class="card"><p class="empty">No events yet</p></div>'
        return _render_admin("Events", html, "events")

    rows = ""
    for e in events:
        cmd = e.get("command","") or ""
        rows += f'<tr><td>{e.get("tab","")}</td><td><code>{cmd[:60] if cmd else "-"}</code></td><td>{e.get("source") or "-"}</td><td>{e.get("location") or "-"}</td><td style="white-space:nowrap">{e.get("created_at","")}</td></tr>'

    html = f"""
    <h2 style="margin-bottom:20px">Copy Events <span style="color:var(--muted);font-size:16px">({len(events)})</span></h2>
    <div class="card"><table><th>Tab</th><th>Command</th><th>Source</th><th>Location</th><th>Date</th>{rows}</table></div>
    """
    return _render_admin("Events", html, "events")


@app.route("/admin/managed")
@login_required
def admin_managed():
    reqs = _fs_get_all("managed_requests", order_by="created_at") or []

    if not reqs:
        html = '<h2>Managed Requests</h2><div class="card"><p class="empty">No managed instance requests yet</p></div>'
        return _render_admin("Managed", html, "managed")

    rows = ""
    for r in reqs:
        uc = r.get("use_case","") or ""
        rows += f'<tr><td>{r.get("name","")}</td><td>{r.get("email","")}</td><td>{r.get("company") or "-"}</td><td title="{uc}">{(uc or "-")[:60]}</td><td>{r.get("location") or "-"}</td><td style="white-space:nowrap">{r.get("created_at","")}</td></tr>'

    html = f"""
    <h2 style="margin-bottom:20px">Managed Instance Requests <span style="color:var(--muted);font-size:16px">({len(reqs)})</span></h2>
    <div class="card"><table><th>Name</th><th>Email</th><th>Company</th><th>Use Case</th><th>Location</th><th>Date</th>{rows}</table></div>
    """
    return _render_admin("Managed", html, "managed")



# ─── Visitor Tracking ────────────────────────────────────────────────────────

_ip_geo_cache = {}
_rate_limit_set = {}
_globe_cache = {"data": None, "ts": 0}

_PYPI_INSTALL_POINTS = [
    {"lat": 37.09,  "lng": -95.71,  "city": "United States",  "country": "United States",  "type": "install", "count": 1600},
    {"lat": 20.59,  "lng": 78.96,   "city": "India",          "country": "India",          "type": "install", "count": 520},
    {"lat": 51.51,  "lng": -0.13,   "city": "United Kingdom", "country": "United Kingdom", "type": "install", "count": 420},
    {"lat": 52.52,  "lng": 13.40,   "city": "Germany",        "country": "Germany",        "type": "install", "count": 380},
    {"lat": 56.13,  "lng": -106.35, "city": "Canada",         "country": "Canada",         "type": "install", "count": 280},
    {"lat": 46.23,  "lng": 2.21,    "city": "France",         "country": "France",         "type": "install", "count": 220},
    {"lat": 52.13,  "lng": 5.29,    "city": "Netherlands",    "country": "Netherlands",    "type": "install", "count": 180},
    {"lat": -25.27, "lng": 133.78,  "city": "Australia",      "country": "Australia",      "type": "install", "count": 160},
    {"lat": -14.24, "lng": -51.93,  "city": "Brazil",         "country": "Brazil",         "type": "install", "count": 140},
    {"lat": 36.20,  "lng": 138.25,  "city": "Japan",          "country": "Japan",          "type": "install", "count": 130},
    {"lat": 35.91,  "lng": 127.77,  "city": "South Korea",    "country": "South Korea",    "type": "install", "count": 110},
    {"lat": 1.35,   "lng": 103.82,  "city": "Singapore",      "country": "Singapore",      "type": "install", "count": 90},
    {"lat": 60.13,  "lng": 18.64,   "city": "Sweden",         "country": "Sweden",         "type": "install", "count": 80},
    {"lat": 51.92,  "lng": 19.15,   "city": "Poland",         "country": "Poland",         "type": "install", "count": 75},
    {"lat": 40.46,  "lng": -3.75,   "city": "Spain",          "country": "Spain",          "type": "install", "count": 70},
]


def _geo_lookup(ip):
    if ip in _ip_geo_cache:
        return _ip_geo_cache[ip]
    try:
        r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        if r.ok:
            d = r.json()
            lat = d.get("latitude")
            lng = d.get("longitude")
            if lat is not None and lng is not None:
                geo = {
                    "city": d.get("city", ""),
                    "country": d.get("country_name", ""),
                    "country_code": d.get("country_code", ""),
                    "lat": float(lat),
                    "lng": float(lng),
                }
                _ip_geo_cache[ip] = geo
                return geo
    except Exception:
        pass
    return {"city": "", "country": "", "country_code": "", "lat": None, "lng": None}


def _clean_rate_limit():
    cutoff = time.time() - 1800
    expired = [k for k, ts in _rate_limit_set.items() if ts < cutoff]
    for k in expired:
        del _rate_limit_set[k]


@app.route("/api/track", methods=["POST"])
def api_track():
    try:
        data = request.get_json(silent=True) or {}
        event_type = str(data.get("event_type", "page_visit"))[:64]
        visitor_id = str(data.get("visitor_id", ""))[:64]
        page = str(data.get("page", "/"))[:256]
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        _clean_rate_limit()
        rl_key = (visitor_id, event_type, page)
        if rl_key in _rate_limit_set:
            return jsonify({"ok": True})
        _rate_limit_set[rl_key] = time.time()

        ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
        ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]

        def _do_write():
            try:
                geo = _geo_lookup(ip)
                doc = {
                    "visitor_id": visitor_id,
                    "event_type": event_type,
                    "page": page,
                    "city": geo.get("city", ""),
                    "country": geo.get("country", ""),
                    "country_code": geo.get("country_code", ""),
                    "lat": geo.get("lat"),
                    "lng": geo.get("lng"),
                    "ip_hash": ip_hash,
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "metadata": metadata,
                }
                _fs_add("visitor_events", doc)
            except Exception as e:
                log.warning(f"[track] write error: {e}")

        threading.Thread(target=_do_write, daemon=True).start()
    except Exception as e:
        log.warning(f"[track] error: {e}")

    return jsonify({"ok": True})


@app.route("/api/globe-data", methods=["GET"])
def api_globe_data():
    import datetime as _dt
    now = time.time()
    if _globe_cache["data"] and now - _globe_cache["ts"] < 300:
        return jsonify(_globe_cache["data"])

    fs = _fs()
    points = list(_PYPI_INSTALL_POINTS)
    total_visitors = 0
    country_set = set()

    if fs:
        try:
            cutoff_dt = _dt.datetime.utcnow() - _dt.timedelta(days=30)
            cutoff = cutoff_dt.isoformat() + "Z"
            docs = list(fs.collection("visitor_events").stream())

            agg = {}
            visitor_ids = set()
            for doc in docs:
                d = doc.to_dict()
                ts = d.get("ts", "")
                if ts and str(ts) < cutoff:
                    continue
                lat = d.get("lat")
                lng = d.get("lng")
                if lat is None or lng is None:
                    continue
                city = d.get("city", "") or ""
                country = d.get("country", "") or ""
                etype = d.get("event_type", "page_visit") or "page_visit"
                vid = d.get("visitor_id", "")
                if vid:
                    visitor_ids.add(vid)
                if country:
                    country_set.add(country)
                key = (round(float(lat), 1), round(float(lng), 1), city, country, etype)
                agg[key] = agg.get(key, 0) + 1

            total_visitors = len(visitor_ids)

            for (lat, lng, city, country, etype), count in agg.items():
                points.append({
                    "lat": lat, "lng": lng,
                    "city": city, "country": country,
                    "type": etype, "count": count,
                })
        except Exception as e:
            log.warning(f"[globe-data] query error: {e}")

    hardcoded_countries = {p["country"] for p in _PYPI_INSTALL_POINTS}
    all_countries = country_set | hardcoded_countries

    result = {
        "points": points,
        "total_visitors": total_visitors,
        "total_countries": len(all_countries),
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }
    _globe_cache["data"] = result
    _globe_cache["ts"] = now
    return jsonify(result)



_hero_stats_cache = {"data": None, "ts": 0}
_HERO_STATS_DAILY_FILE = "/tmp/hero_stats_daily.json"


def _load_daily_stats():
    """Load last successful stats from daily file cache."""
    try:
        import json as _jdc
        with open(_HERO_STATS_DAILY_FILE, "r") as _f:
            cached = _jdc.load(_f)
            if cached.get("date") == time.strftime("%Y-%m-%d"):
                return cached.get("data")
    except Exception:
        pass
    return None


def _save_daily_stats(data):
    """Persist successful stats to daily file cache."""
    try:
        import json as _jdc
        with open(_HERO_STATS_DAILY_FILE, "w") as _f:
            _jdc.dump({"date": time.strftime("%Y-%m-%d"), "data": data}, _f)
    except Exception:
        pass


@app.route("/api/hero-stats", methods=["GET"])
def api_hero_stats():
    now = time.time()
    if _hero_stats_cache["data"] and now - _hero_stats_cache["ts"] < 300:
        return jsonify(_hero_stats_cache["data"])
    result = {}
    # Downloads from pypistats.org (reliable, always up)
    try:
        r = requests.get("https://pypistats.org/api/packages/clawmetry/overall",
                         timeout=10, headers={"User-Agent": "ClawMetry/1.0"})
        r.raise_for_status()
        total = sum(row["downloads"] for row in r.json().get("data", []) if row.get("category") == "with_mirrors")
        # Never show a number lower than 84k (pypistats returns rolling windows, not lifetime)
        total = max(total, 84000)
        result["downloads"] = f"{round(total / 1000)}k" if total >= 1000 else str(total)
        result["downloads_exact"] = total
    except Exception as e:
        log.warning(f"[hero-stats] pypistats error: {e}")
    # Countries from Metabase (best-effort)
    try:
        rows = _fetch_metabase_rows()
        if rows:
            result["countries"] = str(len([r for r in rows if r[1] and int(r[1]) > 0]))
    except Exception as e:
        log.warning(f"[hero-stats] metabase countries error: {e}")
    # If live fetches failed, use daily cache before hardcoded fallback
    if "downloads" not in result or "countries" not in result:
        daily = _load_daily_stats()
        if daily:
            if "downloads" not in result:
                result["downloads"] = daily.get("downloads", "84k")
                result["downloads_exact"] = daily.get("downloads_exact", 84000)
            if "countries" not in result:
                result["countries"] = daily.get("countries", "100")
            log.info("[hero-stats] using daily cache for missing fields")
    if "downloads" not in result:
        result["downloads"] = "84k"
        result["downloads_exact"] = 84000
    if "countries" not in result:
        result["countries"] = "100"
    # GitHub stars
    try:
        r = requests.get("https://api.github.com/repos/vivekchand/clawmetry", timeout=5,
                         headers={"Accept": "application/vnd.github.v3+json"})
        result["stars"] = str(r.json().get("stargazers_count", 107))
    except Exception:
        result["stars"] = "107"
    _hero_stats_cache["data"] = result
    _hero_stats_cache["ts"] = now
    # Persist to daily cache on every successful fetch
    _save_daily_stats(result)
    return jsonify(result)


@app.route('/robots.txt')
def robots_txt():
    return send_from_directory('.', 'robots.txt')

@app.route('/llms.txt')
def llms_txt():
    return send_from_directory('.', 'llms.txt')

@app.route('/.well-known/llms.txt')
def wellknown_llms_txt():
    return send_from_directory('.', 'llms.txt')

@app.route('/.well-known/ai-plugin.json')
def ai_plugin_json():
    from flask import jsonify
    return jsonify({
        "schema_version": "v1",
        "name_for_human": "ClawMetry",
        "name_for_model": "clawmetry",
        "description_for_human": "Real-time observability dashboard for OpenClaw AI agents. Monitor token costs, cron jobs, sub-agents, memory files, and session history. Free and open source.",
        "description_for_model": "ClawMetry is a free, open-source observability dashboard for OpenClaw AI agents. It provides real-time monitoring of token costs, cron jobs, sub-agents, memory files, and session history. Install with: pip install clawmetry. No config needed. Works on Linux, macOS, Windows.",
        "auth": {"type": "none"},
        "logo_url": "https://clawmetry.com/web-app-manifest-192x192.png",
        "contact_email": "vivek@clawmetry.com",
        "legal_info_url": "https://clawmetry.com",
        "pricing": "free",
        "license": "MIT",
        "install": "pip install clawmetry",
        "website": "https://clawmetry.com",
        "github": "https://github.com/vivekchand/clawmetry"
    })


# --- PyPI Countries (Metabase / ClickHouse source) ---------------------------

_COUNTRY_LATLNG = {
    'AD':(42.50,1.52),'AE':(23.42,53.85),'AL':(41.15,20.17),'AM':(40.07,45.04),
    'AR':(-38.42,-63.62),'AT':(47.52,14.55),'AU':(-25.27,133.78),'AZ':(40.14,47.58),
    'BA':(43.92,17.68),'BD':(23.68,90.36),'BE':(50.50,4.47),'BG':(42.73,25.49),
    'BH':(25.93,50.64),'BN':(4.94,114.73),'BR':(-14.24,-51.93),'BY':(53.71,27.95),
    'CA':(56.13,-106.35),'CH':(46.82,8.23),'CL':(-35.68,-71.54),'CN':(35.86,104.20),
    'CO':(4.57,-74.30),'CR':(9.75,-83.75),'CY':(35.13,33.43),'CZ':(49.82,15.47),
    'DE':(51.17,10.45),'DK':(56.26,9.50),'DO':(18.74,-70.16),'DZ':(28.03,1.66),
    'EC':(-1.83,-78.18),'EE':(58.60,25.01),'EG':(26.82,30.80),'ES':(40.46,-3.75),
    'ET':(9.15,40.49),'FI':(61.92,25.75),'FR':(46.23,2.21),'GB':(55.38,-3.44),
    'GE':(42.32,43.36),'GH':(7.95,-1.02),'GR':(39.07,21.82),'HK':(22.40,114.11),
    'HN':(15.20,-86.24),'HR':(45.10,15.20),'HU':(47.16,19.50),'ID':(-0.79,113.92),
    'IE':(53.41,-8.24),'IL':(31.05,34.85),'IM':(54.24,-4.55),'IN':(20.59,78.96),
    'IQ':(33.22,43.68),'IR':(32.43,53.69),'IS':(64.96,-19.02),'IT':(41.87,12.57),
    'JO':(30.59,36.24),'JP':(36.20,138.25),'KE':(-0.02,37.91),'KH':(12.57,104.99),
    'KR':(35.91,127.77),'KW':(29.31,47.48),'KZ':(48.02,66.92),'LB':(33.85,35.86),
    'LI':(47.17,9.56),'LK':(7.87,80.77),'LT':(55.17,23.88),'LU':(49.82,6.13),
    'LV':(56.88,24.60),'MA':(31.79,-7.09),'MC':(43.75,7.41),'MD':(47.41,28.37),
    'ME':(42.71,19.37),'MK':(41.61,21.75),'MM':(21.92,95.96),'MN':(46.86,103.85),
    'MT':(35.94,14.38),'MX':(23.63,-102.55),'MY':(4.21,101.98),'NG':(9.08,8.68),
    'NL':(52.13,5.29),'NO':(60.47,8.47),'NP':(28.39,84.12),'NZ':(-40.90,174.89),
    'OM':(21.47,55.98),'PA':(8.54,-80.78),'PE':(-9.19,-75.02),'PH':(12.88,121.77),
    'PK':(30.38,69.35),'PL':(51.92,19.15),'PT':(39.40,-8.22),'PY':(-23.44,-58.44),
    'QA':(25.35,51.18),'RO':(45.94,24.97),'RS':(44.02,21.01),'RU':(61.52,105.32),
    'SA':(23.89,45.08),'SE':(60.13,18.64),'SG':(1.35,103.82),'SI':(46.15,14.99),
    'SK':(48.67,19.70),'TH':(15.87,100.99),'TN':(33.89,9.54),'TR':(38.96,35.24),
    'TW':(23.70,120.96),'TZ':(-6.37,34.89),'UA':(48.38,31.17),'UG':(1.37,32.29),
    'US':(37.09,-95.71),'UY':(-32.52,-55.77),'UZ':(41.38,64.59),'VE':(6.42,-66.59),
    'VN':(14.06,108.28),'ZA':(-30.56,22.94),'ZW':(-19.02,29.15),
}

_COUNTRY_NAMES = {
    'AD':'Andorra','AE':'United Arab Emirates','AL':'Albania','AM':'Armenia',
    'AR':'Argentina','AT':'Austria','AU':'Australia','AZ':'Azerbaijan',
    'BA':'Bosnia & Herzegovina','BD':'Bangladesh','BE':'Belgium','BG':'Bulgaria',
    'BH':'Bahrain','BN':'Brunei','BR':'Brazil','BY':'Belarus','CA':'Canada',
    'CH':'Switzerland','CL':'Chile','CN':'China','CO':'Colombia','CR':'Costa Rica',
    'CY':'Cyprus','CZ':'Czech Republic','DE':'Germany','DK':'Denmark',
    'DO':'Dominican Republic','DZ':'Algeria','EC':'Ecuador','EE':'Estonia',
    'EG':'Egypt','ES':'Spain','ET':'Ethiopia','FI':'Finland','FR':'France',
    'GB':'United Kingdom','GE':'Georgia','GH':'Ghana','GR':'Greece',
    'HK':'Hong Kong','HN':'Honduras','HR':'Croatia','HU':'Hungary',
    'ID':'Indonesia','IE':'Ireland','IL':'Israel','IM':'Isle of Man',
    'IN':'India','IQ':'Iraq','IR':'Iran','IS':'Iceland','IT':'Italy',
    'JO':'Jordan','JP':'Japan','KE':'Kenya','KH':'Cambodia','KR':'South Korea',
    'KW':'Kuwait','KZ':'Kazakhstan','LB':'Lebanon','LI':'Liechtenstein',
    'LK':'Sri Lanka','LT':'Lithuania','LU':'Luxembourg','LV':'Latvia',
    'MA':'Morocco','MC':'Monaco','MD':'Moldova','ME':'Montenegro',
    'MK':'North Macedonia','MM':'Myanmar','MN':'Mongolia','MT':'Malta',
    'MX':'Mexico','MY':'Malaysia','NG':'Nigeria','NL':'Netherlands',
    'NO':'Norway','NP':'Nepal','NZ':'New Zealand','OM':'Oman','PA':'Panama',
    'PE':'Peru','PH':'Philippines','PK':'Pakistan','PL':'Poland',
    'PT':'Portugal','PY':'Paraguay','QA':'Qatar','RO':'Romania',
    'RS':'Serbia','RU':'Russia','SA':'Saudi Arabia','SE':'Sweden',
    'SG':'Singapore','SI':'Slovenia','SK':'Slovakia','TH':'Thailand',
    'TN':'Tunisia','TR':'Turkey','TW':'Taiwan','TZ':'Tanzania',
    'UA':'Ukraine','UG':'Uganda','US':'United States','UY':'Uruguay',
    'UZ':'Uzbekistan','VE':'Venezuela','VN':'Vietnam','ZA':'South Africa',
    'ZW':'Zimbabwe',
}

_METABASE_COUNTRIES_URL = (
    'https://clickhouse-analytics.metabaseapp.com/api/public/dashboard/'
    '365e0045-2935-4fe3-a66f-4f8059261dc4/dashcard/603/card/654'
    '?parameters=%5B%7B%22type%22%3A%22string%2F%3D%22%2C%22value%22%3A%5B%22clawmetry%22%5D'
    '%2C%22id%22%3A%2216d64bfb%22%2C%22target%22%3A%5B%22dimension%22%2C%5B%22field%22%2C598'
    '%2C%7B%22base-type%22%3A%22type%2FText%22%7D%5D%2C%7B%22stage-number%22%3A0%7D%5D%7D%5D'
)

_pypi_countries_cache = {'data': None, 'ts': 0}


def _fetch_metabase_rows():
    try:
        r = requests.get(_METABASE_COUNTRIES_URL, timeout=10,
                         headers={'User-Agent': 'ClawMetry/1.0'})
        r.raise_for_status()
        return r.json().get('data', {}).get('rows', [])
    except Exception as e:
        log.warning(f'[metabase] fetch error: {e}')
        return []


@app.route('/api/pypi-countries')
def api_pypi_countries():
    now = time.time()
    if _pypi_countries_cache['data'] and now - _pypi_countries_cache['ts'] < 3600:
        return jsonify(_pypi_countries_cache['data'])
    rows = _fetch_metabase_rows()
    countries = []
    total = 0
    for row in rows:
        code = (row[0] or '').upper().strip()
        count = int(row[1]) if row[1] else 0
        if not code or count <= 0:
            continue
        coords = _COUNTRY_LATLNG.get(code)
        if not coords:
            continue
        total += count
        countries.append({
            'country_code': code,
            'country_name': _COUNTRY_NAMES.get(code, code),
            'lat': coords[0], 'lng': coords[1],
            'downloads': count,
        })
    countries.sort(key=lambda x: x['downloads'], reverse=True)
    result = {'countries': countries, 'total_downloads': total, 'total_countries': len(countries)}
    if countries:
        _pypi_countries_cache['data'] = result
        _pypi_countries_cache['ts'] = now
    return jsonify(result)

# ─── Static Routes ───────────────────────────────────────────────────────────


@app.route("/globe")
def globe_page():
    return send_from_directory(".", "globe.html")

@app.route("/pricing")
def pricing():
    return send_from_directory(".", "pricing.html")

@app.route("/roadmap")
def roadmap():
    return send_from_directory(".", "roadmap.html")

@app.route("/how-it-works-v2")
def how_it_works_v2():
    return send_from_directory(".", "how-it-works-v2.html")

@app.route("/privacy")
def privacy():
    return send_from_directory(".", "privacy.html")

@app.route("/terms")
def terms():
    return send_from_directory(".", "terms.html")

@app.route("/how-it-works")
def how_it_works():
    return send_from_directory(".", "how-it-works.html")

@app.route("/showcase")
def showcase():
    return send_from_directory(".", "showcase.html")

@app.route("/blog")
@app.route("/blog/")
def blog_index():
    return send_from_directory("blog", "index.html")

@app.route("/blog/<slug>")
def blog_post(slug):
    """Serve a blog post by slug."""
    if not re.match(r'^[a-z0-9_-]+$', slug):
        return "Not Found", 404
    filepath = os.path.join("blog", f"{slug}.html")
    if not os.path.isfile(filepath):
        return "Not Found", 404
    return send_from_directory("blog", f"{slug}.html")


@app.route("/mac")
def mac_app():
    return send_from_directory(".", "mac.html")

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/new")
def new_landing():
    return send_from_directory(".", "new.html")


@app.route("/old")
def old_landing():
    return send_from_directory(".", "old.html")


@app.route("/v2")
def v2_landing():
    return send_from_directory(".", "v2.html")



@app.route("/install.sh")
def install_sh():
    from flask import Response
    import urllib.request
    try:
        with urllib.request.urlopen("https://raw.githubusercontent.com/vivekchand/clawmetry/refs/heads/main/install.sh", timeout=5) as r:
            script = r.read().decode()
    except Exception:
        script = "echo 'Install script unavailable. Visit https://github.com/vivekchand/clawmetry'; exit 1"
    return Response(script, mimetype="text/plain", headers={"Cache-Control": "no-cache, no-store"})

@app.route("/install.cmd")
def install_cmd():
    from flask import Response
    import urllib.request
    try:
        with urllib.request.urlopen("https://raw.githubusercontent.com/vivekchand/clawmetry/refs/heads/main/install.cmd", timeout=5) as r:
            script = r.read().decode()
    except Exception:
        script = "echo Install script unavailable. Visit https://github.com/vivekchand/clawmetry"
    return Response(script, mimetype="text/plain", headers={"Cache-Control": "no-cache, no-store"})

@app.route("/install.ps1")
def install_ps1():
    from flask import Response
    import urllib.request
    try:
        with urllib.request.urlopen("https://raw.githubusercontent.com/vivekchand/clawmetry/refs/heads/main/install.ps1", timeout=5) as r:
            script = r.read().decode()
    except Exception:
        script = "Write-Host 'Install script unavailable. Visit https://github.com/vivekchand/clawmetry'"
    return Response(script, mimetype="text/plain", headers={"Cache-Control": "no-cache, no-store"})

@app.route("/cloud")
def cloud():
    return send_from_directory(".", "cloud.html")
@app.route("/nemoclaw")
def nemoclaw():
    return send_from_directory(".", "nemoclaw.html")

@app.route("/slides/openclaw-intro")
def slides_openclaw_intro():
    return send_from_directory("slides", "openclaw-intro.html")





@app.route("/hidden/pitch-deck")
def pitch_deck_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ClawMetry - Investor Pitch Deck</title>
<meta name="robots" content="noindex, nofollow">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Inter, -apple-system, sans-serif; background: #0B0F1A; color: #E2E8F0; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 40px 24px; }
  .card { max-width: 540px; width: 100%; text-align: center; }
  .logo { font-size: 28px; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 32px; }
  .logo span { color: #E5443A; }
  h1 { font-size: 32px; font-weight: 800; margin-bottom: 12px; letter-spacing: -1px; }
  .sub { color: #64748B; font-size: 15px; margin-bottom: 40px; line-height: 1.6; }
  .btn { display: inline-flex; align-items: center; gap: 10px; padding: 16px 36px; border-radius: 12px; font-size: 16px; font-weight: 700; text-decoration: none; transition: all 0.2s; margin: 6px; }
  .btn-primary { background: #E5443A; color: #fff; box-shadow: 0 0 20px rgba(229,68,58,0.3); }
  .btn-primary:hover { filter: brightness(1.15); box-shadow: 0 0 30px rgba(229,68,58,0.4); transform: translateY(-1px); }
  .btn-secondary { background: transparent; color: #E2E8F0; border: 1px solid rgba(255,255,255,0.12); }
  .btn-secondary:hover { border-color: rgba(229,68,58,0.3); color: #E5443A; }
  .stats { display: flex; justify-content: center; gap: 32px; margin-bottom: 40px; flex-wrap: wrap; }
  .stat .num { font-size: 28px; font-weight: 800; color: #E5443A; }
  .stat .label { font-size: 12px; color: #64748B; margin-top: 4px; }
  .meta { color: #4A5568; font-size: 12px; margin-top: 32px; }
</style>
</head>
<body>
<div class="card">
  <div class="logo">Claw<span>Metry</span></div>
  <h1>Investor Pitch Deck</h1>
  <p class="sub">Real-time observability for AI agents. The Datadog for OpenClaw.</p>
  <div class="stats">
    <div class="stat"><div class="num">75k+</div><div class="label">Installs</div></div>
    <div class="stat"><div class="num">100+</div><div class="label">Countries</div></div>
    <div class="stat"><div class="num">133</div><div class="label">Cloud Users</div></div>
    <div class="stat"><div class="num">#5</div><div class="label">Product Hunt</div></div>
  </div>
  <div style="margin-bottom:32px;">
    <a href="/pitch-deck.pdf" class="btn btn-primary" download>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
      Download PDF
    </a>
    <a href="/pitch-deck.html" class="btn btn-secondary" target="_blank">View Online</a>
  </div>
  <div style="text-align:left;max-width:400px;margin:0 auto;">
    <p style="font-size:13px;color:#64748B;margin-bottom:12px;text-align:center;">4 versions, each for a different investor type:</p>
    <a href="/hidden/pitch-v1" target="_blank" style="display:block;padding:10px 16px;border:1px solid rgba(255,255,255,0.08);border-radius:8px;margin-bottom:8px;color:#E2E8F0;font-size:14px;font-weight:500;text-decoration:none;transition:border-color 0.2s;" onmouseover="this.style.borderColor='rgba(229,68,58,0.3)'" onmouseout="this.style.borderColor='rgba(255,255,255,0.08)'">V1: OpenClaw Ecosystem <span style="color:#64748B;font-size:12px;">OSS VCs, YC</span></a>
    <a href="/hidden/pitch-v2" target="_blank" style="display:block;padding:10px 16px;border:1px solid rgba(255,255,255,0.08);border-radius:8px;margin-bottom:8px;color:#E2E8F0;font-size:14px;font-weight:500;text-decoration:none;transition:border-color 0.2s;" onmouseover="this.style.borderColor='rgba(229,68,58,0.3)'" onmouseout="this.style.borderColor='rgba(255,255,255,0.08)'">V2: Multi-Claw Platform <span style="color:#64748B;font-size:12px;">a16z, Sequoia</span></a>
    <a href="/hidden/pitch-v3" target="_blank" style="display:block;padding:10px 16px;border:1px solid rgba(255,255,255,0.08);border-radius:8px;margin-bottom:8px;color:#E2E8F0;font-size:14px;font-weight:500;text-decoration:none;transition:border-color 0.2s;" onmouseover="this.style.borderColor='rgba(229,68,58,0.3)'" onmouseout="this.style.borderColor='rgba(255,255,255,0.08)'">V3: Product Depth <span style="color:#64748B;font-size:12px;">Technical angels</span></a>
    <a href="/hidden/pitch-v4" target="_blank" style="display:block;padding:10px 16px;border:1px solid rgba(255,255,255,0.08);border-radius:8px;margin-bottom:8px;color:#E2E8F0;font-size:14px;font-weight:500;text-decoration:none;transition:border-color 0.2s;" onmouseover="this.style.borderColor='rgba(229,68,58,0.3)'" onmouseout="this.style.borderColor='rgba(255,255,255,0.08)'">V4: Growth Metrics <span style="color:#64748B;font-size:12px;">Seedcamp, Point Nine</span></a>
    <a href="/hidden/pitch-scorecard" target="_blank" style="display:block;padding:10px 16px;border:1px solid rgba(229,68,58,0.15);border-radius:8px;color:#E5443A;font-size:14px;font-weight:600;text-decoration:none;text-align:center;">Investability Scorecard</a>
  </div>
  <p class="meta">Vivek Chand &middot; vivek@clawmetry.com &middot; clawmetry.com</p>
</div>
</body>
</html>"""

@app.route("/pitch-deck.pdf")
def pitch_deck_pdf():
    return send_from_directory(".", "pitch-deck.pdf", mimetype="application/pdf")

@app.route("/pitch-deck.html")
def pitch_deck_html():
    return send_from_directory(".", "pitch-deck.html")



@app.route("/hidden/pitch-v1")
def pitch_v1():
    return send_from_directory(".", "pitch-v1-openclaw.html")

@app.route("/hidden/pitch-v2")
def pitch_v2():
    return send_from_directory(".", "pitch-v2-platform.html")

@app.route("/hidden/pitch-v3")
def pitch_v3():
    return send_from_directory(".", "pitch-v3-product.html")

@app.route("/hidden/pitch-v4")
def pitch_v4():
    return send_from_directory(".", "pitch-v4-growth.html")

@app.route("/hidden/pitch-scorecard")
def pitch_scorecard():
    return send_from_directory(".", "pitch-scorecard.html")



@app.route('/api/feature-request', methods=['POST'])
def api_feature_request():
    data = request.get_json(silent=True) or {}
    feature = (data.get('feature') or '').strip()
    email = (data.get('email') or '').strip()
    name = (data.get('name') or '').strip()
    if not feature:
        return jsonify({'error': 'No feature described'}), 400
    subject = f"NemoClaw Setup Help Request" if 'NemoClaw setup help' in feature else f"Feature Request: {feature[:60]}"
    notify_vivek(
        subject,
        f"""<div style="font-family:sans-serif;max-width:500px;">
        <h2 style="color:#E5443A;">{subject}</h2>
        <div style="background:#f8f9fa;border-radius:8px;padding:16px;margin:12px 0;">
          <p style="margin:8px 0;"><strong>Name:</strong> {name or 'not provided'}</p>
          <p style="margin:8px 0;"><strong>Email:</strong> {email or 'not provided'}</p>
          <p style="margin:8px 0;"><strong>Message:</strong> {feature}</p>
        </div>
        </div>"""
    )
    return jsonify({'ok': True})

@app.route("/<path:path>")
def static_files(path):
    # Don't serve admin routes as static
    if path.startswith("admin"):
        return "Not found", 404
    # Explicit HTML page mappings (no extension in URL)
    page_map = {
        'pricing': 'pricing.html',
        'roadmap': 'roadmap.html',
        'showcase': 'showcase.html',
        'how-it-works': 'how-it-works.html',
        'cloud': 'cloud.html',
        'nemoclaw': 'nemoclaw.html',
        'docs': 'docs.html',
        'globe': 'globe.html',
    }
    if path in page_map:
        return send_from_directory('.', page_map[path])
    return send_from_directory('.', path)



@app.route("/docs")
def docs_redirect():
    return redirect("/docs.html", code=301)


@app.route("/Clawmetry-<version>.dmg")
def download_mac_app(version):
    import threading, datetime, json as _j, urllib.request as _ur
    url = f"https://github.com/vivekchand/clawmetry-mac/releases/latest/download/ClawMetry-{version}.dmg"
    def _notify():
        try:
            ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
            ua = request.headers.get("User-Agent", "")
            body = f"<p>Mac app downloaded</p><ul><li>Version: {version}</li><li>IP: {ip}</li><li>UA: {ua}</li></ul>"
            payload = _j.dumps({"from": FROM_EMAIL, "to": ["vivek@clawmetry.com"], "subject": f"[ClawMetry] Mac downloaded: {version}", "html": body}).encode()
            req = _ur.Request("https://api.resend.com/emails", data=payload, headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}, method="POST")
            _ur.urlopen(req, timeout=5)
        except Exception:
            pass
    threading.Thread(target=_notify, daemon=True).start()
    return redirect(url, code=302)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

# ─── Traction Page ───────────────────────────────────────────────────────────

import time as _time

_traction_cache = {"data": None, "ts": 0}
_last_known = {"pypi_day": "1,809", "pypi_week": "10,054", "pypi_month": "17,550", "gh_stars": "78", "gh_forks": "15", "gh_issues": "0"}  # seeded fallbacks; updated on each successful API call

def _fetch_traction_data():
    now = _time.time()
    if _traction_cache["data"] and now - _traction_cache["ts"] < 300:
        return _traction_cache["data"]
    
    import requests as _req
    
    data = {}
    
    # PyPI
    try:
        r = _req.get("https://pypistats.org/api/packages/clawmetry/recent", timeout=10,
                      headers={"User-Agent": "ClawMetry-Traction/1.0"})
        if r.ok:
            j = r.json().get("data", {})
            data["pypi_day"] = f"{j.get('last_day', 0):,}"
            data["pypi_week"] = f"{j.get('last_week', 0):,}"
            data["pypi_month"] = f"{j.get('last_month', 0):,}"
            _last_known["pypi_day"] = data["pypi_day"]
            _last_known["pypi_week"] = data["pypi_week"]
            _last_known["pypi_month"] = data["pypi_month"]
    except:
        pass
    data.setdefault("pypi_day", _last_known.get("pypi_day", "..."))
    data.setdefault("pypi_week", _last_known.get("pypi_week", "..."))
    data.setdefault("pypi_month", _last_known.get("pypi_month", "..."))
    
    # GitHub
    try:
        r = _req.get("https://api.github.com/repos/vivekchand/clawmetry", timeout=5,
                      headers={"User-Agent": "ClawMetry-Traction/1.0"})
        if r.ok:
            j = r.json()
            data["gh_stars"] = f"{j.get('stargazers_count', 0):,}"
            data["gh_forks"] = f"{j.get('forks_count', 0):,}"
            data["gh_issues"] = f"{j.get('open_issues_count', 0):,}"
            _last_known["gh_stars"] = data["gh_stars"]
            _last_known["gh_forks"] = data["gh_forks"]
            _last_known["gh_issues"] = data["gh_issues"]
    except:
        pass
    data.setdefault("gh_stars", _last_known.get("gh_stars", "0"))
    data.setdefault("gh_forks", _last_known.get("gh_forks", "0"))
    data.setdefault("gh_issues", _last_known.get("gh_issues", "0"))
    
    # Subscriber count from Resend (source of truth, includes pre-Firestore signups)
    try:
        resend_contacts = get_all_contacts()
        data["subscribers"] = str(len(resend_contacts)) if resend_contacts else str(_fs_count("subscribers") or 0)
    except:
        try:
            data["subscribers"] = str(_fs_count("subscribers") or 0)
        except:
            data["subscribers"] = "0"
    try:
        data["managed_requests"] = str(_fs_count("managed_requests") or 0)
    except:
        data["managed_requests"] = "0"
    try:
        data["copy_events"] = str(_fs_count("copy_events") or 0)
    except:
        data["copy_events"] = "0"
    
    from datetime import datetime, timezone
    data["updated_at"] = datetime.now(timezone.utc).strftime("%b %d, %Y at %H:%M UTC")
    
    _traction_cache["data"] = data
    _traction_cache["ts"] = now
    return data


@app.route("/traction")
def traction_page():
    data = _fetch_traction_data()
    with open(os.path.join(os.path.dirname(__file__), "traction.html")) as f:
        html = f.read()
    data["days_since_launch"] = str((datetime.now() - datetime(2026, 2, 18)).days)
    for key, val in data.items():
        html = html.replace("{{" + key + "}}", val)
    return html

# ─────────────────────────────────────────────────────────────
# ANALYTICS DASHBOARD  /admin/analytics
# ─────────────────────────────────────────────────────────────
import functools, collections

_analytics_cache = {"data": None, "ts": 0}
_ANALYTICS_TTL = 120  # seconds

def _require_admin(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        pwd = request.args.get("pwd", "")
        if auth == f"Bearer {ADMIN_PASSWORD}" or pwd == ADMIN_PASSWORD:
            return f(*args, **kwargs)
        if request.method == "GET" and not request.is_json:
            return """<!doctype html><html><body style="font:16px sans-serif;padding:40px;background:#111;color:#eee;">
            <h2 style="color:#ef4444;">ClawMetry Analytics</h2>
            <form method="GET">
            <input name="pwd" type="password" placeholder="Admin password" autofocus
              style="padding:10px 14px;border-radius:8px;border:1px solid #333;background:#1a1a1a;color:#eee;font-size:15px;width:260px;">
            <button type="submit" style="padding:10px 20px;background:#ef4444;color:#fff;border:none;border-radius:8px;margin-left:8px;cursor:pointer;font-size:15px;">Enter</button>
            </form></body></html>"""
        return jsonify({"error": "Unauthorized"}), 401
    return wrapper

def _fetch_analytics_data(force=False):
    now = time.time()
    if not force and _analytics_cache["data"] and now - _analytics_cache["ts"] < _ANALYTICS_TTL:
        return _analytics_cache["data"]

    import datetime as _dt
    fs = _fs()
    result = {
        "generated_at": _dt.datetime.utcnow().isoformat() + "Z",
        "summary": {},
        "by_event": {},
        "by_hour": {},
        "by_day": {},
        "by_country": {},
        "by_source": {},
        "recent": []
    }

    if not fs:
        result["error"] = "Firestore not available"
        return result

    now_dt = _dt.datetime.utcnow()
    day7_ago = (now_dt - _dt.timedelta(days=7)).isoformat() + "Z"
    day1_ago = (now_dt - _dt.timedelta(hours=24)).isoformat() + "Z"
    today_str = now_dt.strftime("%Y-%m-%d")

    all_events = []

    # Collect visitor_events (most recent 2000, ordered)
    ve = _fs_get_all("visitor_events", order_by="ts", order_dir="DESCENDING", limit=2000) or []
    for d in ve:
        d["_collection"] = "visitor_events"
        all_events.append(d)

    # Collect copy_events (most recent 500)
    ce = _fs_get_all("copy_events", order_by="created_at", order_dir="DESCENDING", limit=500) or []
    for d in ce:
        d["_collection"] = "copy_events"
        d.setdefault("event_type", d.get("tab", "copy"))
        d.setdefault("ts", d.get("created_at", ""))
        d.setdefault("country", "")
        d.setdefault("visitor_id", d.get("ip", ""))
        all_events.append(d)

    # Filter to last 7 days
    events_7d = [e for e in all_events if str(e.get("ts","")) >= day7_ago]
    events_24h = [e for e in events_7d if str(e.get("ts","")) >= day1_ago]

    # Summary
    unique_visitors_7d = len(set(e.get("visitor_id","") for e in events_7d if e.get("visitor_id")))
    unique_visitors_24h = len(set(e.get("visitor_id","") for e in events_24h if e.get("visitor_id")))
    result["summary"] = {
        "total_events_7d": len(events_7d),
        "total_events_24h": len(events_24h),
        "unique_visitors_7d": unique_visitors_7d,
        "unique_visitors_24h": unique_visitors_24h,
        "total_all_time": len(all_events),
    }

    # By event type
    ctr = collections.Counter(e.get("event_type","unknown") for e in events_7d)
    result["by_event"] = dict(ctr.most_common(20))

    # By hour (last 24h)
    hour_ctr = collections.Counter()
    for e in events_24h:
        ts = str(e.get("ts",""))
        if len(ts) >= 13:
            hour_ctr[ts[11:13] + ":00"] += 1
    result["by_hour"] = dict(sorted(hour_ctr.items()))

    # By day (last 7d)
    day_ctr = collections.Counter()
    for e in events_7d:
        ts = str(e.get("ts",""))
        if len(ts) >= 10:
            day_ctr[ts[:10]] += 1
    result["by_day"] = dict(sorted(day_ctr.items()))

    # By country
    country_ctr = collections.Counter(e.get("country","Unknown") or "Unknown" for e in events_7d)
    result["by_country"] = dict(country_ctr.most_common(15))

    # By source (utm_source or referer)
    source_ctr = collections.Counter()
    for e in events_7d:
        meta = e.get("metadata") or {}
        if isinstance(meta, str):
            try: meta = json.loads(meta)
            except: meta = {}
        src = (meta.get("utm_source") or e.get("source") or "direct")[:40]
        source_ctr[src] += 1
    result["by_source"] = dict(source_ctr.most_common(15))

    # Recent events feed (last 50)
    sorted_events = sorted(events_7d, key=lambda e: str(e.get("ts","")), reverse=True)[:50]
    result["recent"] = [{
        "ts": e.get("ts",""),
        "type": e.get("event_type", e.get("tab","?")),
        "country": e.get("country",""),
        "city": e.get("city",""),
        "source": (e.get("source","") or "")[:40],
        "meta": str(e.get("metadata",""))[:80] if e.get("metadata") else "",
        "visitor": (e.get("visitor_id","") or "")[:8],
    } for e in sorted_events]

    _analytics_cache["data"] = result
    _analytics_cache["ts"] = time.time()
    return result


@app.route("/admin/analytics")
@_require_admin
def admin_analytics():
    data = _fetch_analytics_data()
    s = data.get("summary", {})
    by_event = data.get("by_event", {})
    by_day = data.get("by_day", {})
    by_country = data.get("by_country", {})
    by_source = data.get("by_source", {})
    recent = data.get("recent", [])

    def bar(val, max_val, color="#ef4444"):
        pct = int(val / max_val * 100) if max_val else 0
        return f'<div style="height:6px;background:#1e1e1e;border-radius:3px;margin-top:4px;"><div style="height:6px;width:{pct}%;background:{color};border-radius:3px;"></div></div>'

    max_event = max(by_event.values()) if by_event else 1
    max_country = max(by_country.values()) if by_country else 1
    max_source = max(by_source.values()) if by_source else 1
    max_day = max(by_day.values()) if by_day else 1

    event_rows = "".join(
        f'<tr><td style="padding:6px 8px;color:#94a3b8;font-size:13px;">{k}</td>'
        f'<td style="padding:6px 8px;font-weight:600;color:#eee;">{v}</td>'
        f'<td style="padding:6px 8px;width:160px;">{bar(v, max_event)}</td></tr>'
        for k, v in sorted(by_event.items(), key=lambda x: -x[1])
    )

    country_rows = "".join(
        f'<tr><td style="padding:5px 8px;color:#94a3b8;font-size:13px;">{k}</td>'
        f'<td style="padding:5px 8px;font-weight:600;color:#eee;">{v}</td>'
        f'<td style="padding:5px 8px;width:120px;">{bar(v, max_country, "#3b82f6")}</td></tr>'
        for k, v in list(by_country.items())[:10]
    )

    source_rows = "".join(
        f'<tr><td style="padding:5px 8px;color:#94a3b8;font-size:13px;">{k}</td>'
        f'<td style="padding:5px 8px;font-weight:600;color:#eee;">{v}</td>'
        f'<td style="padding:5px 8px;width:120px;">{bar(v, max_source, "#22c55e")}</td></tr>'
        for k, v in list(by_source.items())[:10]
    )

    day_bars = "".join(
        f'<div style="display:flex;flex-direction:column;align-items:center;gap:4px;flex:1;">'
        f'<div style="font-size:10px;color:#64748b;">{v}</div>'
        f'<div style="width:100%;background:#1e1e1e;border-radius:3px;height:60px;display:flex;align-items:flex-end;">'
        f'<div style="width:100%;background:#ef4444;border-radius:3px 3px 0 0;height:{int(v/max_day*60)}px;"></div></div>'
        f'<div style="font-size:9px;color:#64748b;">{k[5:]}</div>'
        f'</div>'
        for k, v in list(by_day.items())[-7:]
    )

    type_emoji = {
        "page_visit": "👁", "install_copy": "🦞", "copy": "📋",
        "social-click": "🔗", "cta_click": "👆", "managed-cta": "👀",
        "subscribe": "📧", "signup": "🎉", "page_view": "👁"
    }

    recent_rows = "".join(
        f'<tr style="border-bottom:1px solid #1e1e1e;">'
        f'<td style="padding:6px 8px;color:#64748b;font-size:11px;white-space:nowrap;">{e["ts"][11:19] if len(e["ts"])>10 else e["ts"]}</td>'
        f'<td style="padding:6px 8px;font-size:13px;">{type_emoji.get(e["type"],"•")} {e["type"]}</td>'
        f'<td style="padding:6px 8px;color:#94a3b8;font-size:12px;">{e.get("city","")}, {e.get("country","")}</td>'
        f'<td style="padding:6px 8px;color:#64748b;font-size:12px;">{e.get("source","")[:30]}</td>'
        f'<td style="padding:6px 8px;color:#475569;font-size:11px;">{e.get("meta","")[:50]}</td>'
        f'</tr>'
        for e in recent
    )

    notify_status = "🔴 OFF (emails suppressed)" if not NOTIFY_CLICKS else "🟢 ON (sending emails)"

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ClawMetry Analytics</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0a0a0a; color: #e2e8f0; min-height: 100vh; }}
.header {{ background: #111; border-bottom: 1px solid #1e1e1e; padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 10; }}
.logo {{ font-size: 18px; font-weight: 700; color: #ef4444; }}
.logo span {{ color: #94a3b8; font-weight: 400; font-size: 13px; margin-left: 8px; }}
.refresh {{ font-size: 12px; color: #475569; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 24px 20px; }}
.grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
.card {{ background: #111; border: 1px solid #1e1e1e; border-radius: 12px; padding: 18px 20px; }}
.stat-label {{ font-size: 12px; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }}
.stat-value {{ font-size: 32px; font-weight: 700; color: #fff; }}
.stat-sub {{ font-size: 12px; color: #475569; margin-top: 4px; }}
.grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
.grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
.card h3 {{ font-size: 13px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 14px; }}
table {{ width: 100%; border-collapse: collapse; }}
th {{ text-align: left; font-size: 11px; color: #475569; padding: 4px 8px; text-transform: uppercase; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }}
.badge-red {{ background: #2d1515; color: #ef4444; }}
.badge-green {{ background: #0f1f12; color: #22c55e; }}
.notify-bar {{ background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 8px; padding: 10px 16px; margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; font-size: 13px; }}
.full {{ grid-column: 1 / -1; }}
@media(max-width:768px) {{ .grid-4,.grid-3,.grid-2 {{ grid-template-columns: 1fr 1fr; }} }}
@media(max-width:480px) {{ .grid-4,.grid-3,.grid-2 {{ grid-template-columns: 1fr; }} }}
</style>
</head><body>
<div class="header">
  <div class="logo"><img src="/favicon.svg" width="22" height="22" style="vertical-align:middle;margin-right:4px;border-radius:4px"> ClawMetry <span>Analytics</span></div>
  <div class="refresh">Updated: {data.get("generated_at","")[:19].replace("T"," ")} UTC &nbsp;|&nbsp;
    <a href="?pwd={request.args.get('pwd','')}&bust={int(time.time())}" style="color:#ef4444;text-decoration:none;">↻ Refresh</a>
  </div>
</div>
<div class="container">

  <div class="notify-bar">
    <span>Click notifications: <strong>{notify_status}</strong></span>
    <span style="color:#475569;font-size:12px;">Set <code>NOTIFY_CLICKS=true</code> env var to re-enable &nbsp;|&nbsp; Signups & setup-help emails still send always</span>
  </div>

  <div class="grid-4">
    <div class="card">
      <div class="stat-label">Events today</div>
      <div class="stat-value">{s.get("total_events_24h",0):,}</div>
      <div class="stat-sub">Last 24 hours</div>
    </div>
    <div class="card">
      <div class="stat-label">Visitors today</div>
      <div class="stat-value">{s.get("unique_visitors_24h",0):,}</div>
      <div class="stat-sub">Unique visitor IDs</div>
    </div>
    <div class="card">
      <div class="stat-label">Events (7d)</div>
      <div class="stat-value">{s.get("total_events_7d",0):,}</div>
      <div class="stat-sub">{s.get("unique_visitors_7d",0):,} unique visitors</div>
    </div>
    <div class="card">
      <div class="stat-label">All-time events</div>
      <div class="stat-value">{s.get("total_all_time",0):,}</div>
      <div class="stat-sub">Since launch</div>
    </div>
  </div>

  <div class="card" style="margin-bottom:24px;">
    <h3>Activity — Last 7 Days</h3>
    <div style="display:flex;gap:6px;height:80px;align-items:flex-end;">{day_bars}</div>
  </div>

  <div class="grid-3">
    <div class="card">
      <h3>Events by Type (7d)</h3>
      <table><thead><tr><th>Type</th><th>Count</th><th></th></tr></thead>
      <tbody>{event_rows}</tbody></table>
    </div>
    <div class="card">
      <h3>By Country (7d)</h3>
      <table><thead><tr><th>Country</th><th>Count</th><th></th></tr></thead>
      <tbody>{country_rows}</tbody></table>
    </div>
    <div class="card">
      <h3>By Source (7d)</h3>
      <table><thead><tr><th>Source</th><th>Count</th><th></th></tr></thead>
      <tbody>{source_rows}</tbody></table>
    </div>
  </div>

  <div class="card">
    <h3>Recent Events Feed <span style="color:#475569;font-weight:400;text-transform:none;font-size:11px;">(last 50 — replaces email inbox)</span></h3>
    <div style="overflow-x:auto;">
    <table>
      <thead><tr><th>Time</th><th>Event</th><th>Location</th><th>Source</th><th>Detail</th></tr></thead>
      <tbody>{recent_rows}</tbody>
    </table>
    </div>
  </div>

</div>
</body></html>"""
    return html


@app.route("/admin/analytics/data")
@_require_admin
def admin_analytics_data():
    """Raw JSON endpoint for the analytics data."""
    force = request.args.get("force") == "1"
    return jsonify(_fetch_analytics_data(force=force))

# ─────────────────────────────────────────────────────────────


@app.route("/admin/support", methods=["GET"])
def admin_support():
    """Admin inbox for support messages from the cloud dashboard."""
    pwd = request.args.get("pwd", "")
    if pwd != "clawmetry-admin-2026":
        return "Unauthorized", 401

    fs_client = _fs()
    messages = []
    if fs_client:
        try:
            docs = (fs_client.collection("support_messages")
                    .order_by("created_at", direction="DESCENDING")
                    .limit(200).get())
            for d in docs:
                m = d.to_dict()
                m["_id"] = d.id
                messages.append(m)
        except Exception as e:
            log.warning(f"[admin/support] Firestore error: {e}")

    rows_html = ""
    for m in messages:
        email = m.get("email", "anonymous")
        node  = m.get("node_id", "")
        msg   = m.get("message", "")
        ts    = m.get("created_at", "")[:19].replace("T", " ")
        replied = m.get("replied", False)
        mid   = m.get("_id", "")
        badge = ('<span style="background:#10b981;color:#fff;font-size:10px;padding:2px 7px;border-radius:99px;">replied</span>'
                 if replied else
                 '<span style="background:#e5443a;color:#fff;font-size:10px;padding:2px 7px;border-radius:99px;">new</span>')
        mailto = f"mailto:{email}?subject=Re: Your ClawMetry support request&body=Hi%2C%0A%0AThanks for reaching out!%0A%0A---%0A{msg[:200]}"
        rows_html += f"""
<div style="background:#0f1623;border:1px solid #1e2d40;border-radius:12px;padding:18px;margin-bottom:14px;" id="msg-{mid}">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px;">
    <div style="display:flex;gap:10px;align-items:center;">
      {badge}
      <span style="color:#e2e8f0;font-weight:600;font-size:14px;">{email}</span>
      {('<span style="color:#64748b;font-size:12px;">· '+node+'</span>') if node else ''}
    </div>
    <span style="color:#64748b;font-size:12px;">{ts}</span>
  </div>
  <div style="background:#1a2332;border-left:3px solid #e5443a;padding:12px 14px;border-radius:0 8px 8px 0;margin-bottom:12px;">
    <p style="margin:0;font-size:14px;color:#e2e8f0;white-space:pre-wrap;line-height:1.6;">{msg}</p>
  </div>
  <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-start;">
    <a href="{mailto}" style="background:#e5443a;color:#fff;padding:8px 14px;border-radius:7px;text-decoration:none;font-size:12px;font-weight:600;">Reply via email</a>
    <div style="display:flex;gap:6px;flex:1;">
      <textarea id="rt-{mid}" placeholder="Quick reply..." style="flex:1;background:#1a2332;border:1px solid #1e2d40;border-radius:7px;color:#e2e8f0;font-size:12px;padding:8px;min-height:36px;resize:none;font-family:inherit;outline:none;"></textarea>
      <button onclick="cmReply('{mid}','{email}')" style="background:#334155;color:#e2e8f0;border:none;border-radius:7px;padding:8px 12px;font-size:12px;cursor:pointer;font-weight:600;white-space:nowrap;">Send reply</button>
    </div>
  </div>
  <div id="rstat-{mid}" style="font-size:11px;color:#64748b;margin-top:6px;"></div>
</div>"""

    page = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Support Inbox | ClawMetry</title>
<meta name="robots" content="noindex,nofollow">
<style>*{{box-sizing:border-box;}}body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#080d16;color:#e2e8f0;min-height:100vh;padding:24px;}}
h1{{margin:0 0 4px;font-size:22px;}}p{{margin:0 0 20px;color:#64748b;font-size:14px;}}
.stats{{display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;}}
.stat{{background:#0f1623;border:1px solid #1e2d40;border-radius:10px;padding:12px 18px;min-width:100px;}}
.stat .n{{font-size:24px;font-weight:700;color:#fff;}}
.stat .l{{font-size:11px;color:#64748b;margin-top:2px;}}
</style></head><body>
<div style="max-width:760px;margin:0 auto;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px;">
    <div>
      <h1>&#128172; Support Inbox</h1>
      <p>{len(messages)} message{"s" if len(messages)!=1 else ""} total</p>
    </div>
    <a href="/admin/analytics?pwd=clawmetry-admin-2026" style="color:#64748b;font-size:13px;text-decoration:none;">&#8592; Analytics</a>
  </div>
  <div class="stats">
    <div class="stat"><div class="n">{len(messages)}</div><div class="l">Total</div></div>
    <div class="stat"><div class="n" style="color:#e5443a;">{sum(1 for m in messages if not m.get("replied"))}</div><div class="l">Unread</div></div>
    <div class="stat"><div class="n" style="color:#10b981;">{sum(1 for m in messages if m.get("replied"))}</div><div class="l">Replied</div></div>
  </div>
  {rows_html if rows_html else '<div style="text-align:center;padding:60px 0;color:#64748b;">No messages yet.</div>'}
</div>
<script>
function cmReply(mid, email) {{
  var txt = document.getElementById('rt-' + mid).value.trim();
  if (!txt) return;
  var stat = document.getElementById('rstat-' + mid);
  stat.textContent = 'Sending...'; stat.style.color = '#94a3b8';
  fetch('/admin/support/reply?pwd=clawmetry-admin-2026', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{doc_id: mid, email: email, reply: txt}})
  }}).then(r => r.json()).then(d => {{
    if (d.ok) {{
      stat.textContent = 'Replied!'; stat.style.color = '#10b981';
      document.getElementById('rt-' + mid).value = '';
    }} else {{
      stat.textContent = d.error || 'Failed'; stat.style.color = '#e5443a';
    }}
  }}).catch(() => {{ stat.textContent = 'Network error'; stat.style.color = '#e5443a'; }});
}}
</script>
</body></html>"""
    return page


@app.route("/admin/support/reply", methods=["POST"])
def admin_support_reply():
    """Send a reply email and mark message as replied in Firestore."""
    pwd = request.args.get("pwd", "")
    if pwd != "clawmetry-admin-2026":
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    doc_id    = str(data.get("doc_id", "")).strip()
    email     = str(data.get("email", "")).strip()
    reply_txt = str(data.get("reply", "")).strip()

    if not doc_id or not email or not reply_txt:
        return jsonify({"error": "Missing fields"}), 400
    if email == "anonymous" or "@" not in email:
        return jsonify({"error": "No valid email to reply to"}), 400

    reply_html = f"""<div style="font-family:-apple-system,sans-serif;max-width:520px;margin:0 auto;background:#0f1623;color:#e2e8f0;padding:28px;border-radius:12px;">
<div style="display:flex;align-items:center;gap:10px;margin-bottom:20px;">
  <img src="https://clawmetry.com/apple-touch-icon.png" style="width:32px;height:32px;border-radius:6px;">
  <strong style="color:#fff;font-size:16px;">ClawMetry Support</strong>
</div>
<div style="background:#1a2332;border-left:3px solid #e5443a;padding:14px 16px;border-radius:0 8px 8px 0;margin-bottom:20px;">
  <p style="margin:0;font-size:15px;line-height:1.7;white-space:pre-wrap;">{reply_txt}</p>
</div>
<p style="color:#64748b;font-size:12px;margin:0;">Reply from the ClawMetry team. Questions? Email us at hello@clawmetry.com</p>
</div>"""

    # Send email
    try:
        ok, resp = _resend_post("/emails", {
            "from": "ClawMetry Support <hello@clawmetry.com>",
            "to": [email],
            "subject": "Re: Your ClawMetry support message",
            "html": reply_html,
        })
        if not ok:
            return jsonify({"error": f"Resend error: {resp}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Mark as replied in Firestore
    fs_client = _fs()
    if fs_client and doc_id:
        try:
            import datetime as _dt
            fs_client.collection("support_messages").document(doc_id).update({
                "replied": True,
                "reply_text": reply_txt,
                "replied_at": _dt.datetime.utcnow().isoformat() + "Z",
            })
        except Exception as e:
            log.warning(f"[admin/support/reply] Firestore update failed: {e}")

    return jsonify({"ok": True})


@app.route('/api/track-click', methods=['POST'])
def api_track_click():
    """Track high-intent button clicks and notify Vivek via email."""
    import datetime
    data = request.get_json(silent=True) or {}
    event = data.get('event', 'unknown')
    ref = data.get('ref', '')[:200]
    ua = data.get('ua', '')[:150]
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')[:60]
    ts = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    NOTIFY_EVENTS = {'try_cloud', 'get_started', 'pricing_click'}
    if event not in NOTIFY_EVENTS:
        return jsonify({'ok': True})

    label_map = {
        'try_cloud': 'Try Cloud button clicked',
        'get_started': 'Get Started Free clicked',
        'pricing_click': 'Pricing page CTA clicked',
    }
    subject = f"[ClawMetry] {label_map.get(event, event)} on clawmetry.com"
    body = f"""<p style="font-family:sans-serif;font-size:15px;">
<strong>{label_map.get(event, event)}</strong><br><br>
<b>Time:</b> {ts}<br>
<b>IP:</b> {ip}<br>
<b>Referrer:</b> {ref or 'direct'}<br>
<b>User-agent:</b> {ua}<br>
</p>"""

    try:
        import urllib.request as _ur2, json as _j2
        _payload = {
            "from": "ClawMetry <noreply@clawmetry.com>",
            "to": ["vivek@clawmetry.com"],
            "subject": subject,
            "html": body,
        }
        _req = _ur2.Request(
            "https://api.resend.com/emails",
            data=_j2.dumps(_payload).encode(),
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            method="POST",
        )
        _ur2.urlopen(_req, timeout=5)
    except Exception:
        pass

    return jsonify({'ok': True})

