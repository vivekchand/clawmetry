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
  <span class="brand">🦞 ClawMetry</span>
  <a href="/admin" class="{{ 'active' if active=='dash' }}">Dashboard</a>
  <a href="/admin/inbox" class="{{ 'active' if active=='inbox' }}">Inbox</a>
  <a href="/admin/compose" class="{{ 'active' if active=='compose' }}">Compose</a>
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
<h1>🦞 ClawMetry Admin</h1>
{% if error %}<p class="err">{{ error }}</p>{% endif %}
<form method="POST"><input type="password" name="password" placeholder="Password" autofocus><button type="submit">Login</button></form>
</div></body></html>
"""

# ─── Helpers ─────────────────────────────────────────────────────────────────

WELCOME_HTML = """\
<div style="font-family:sans-serif;max-width:600px;margin:0 auto;background:#0d0d14;color:#e0e0e0;border-radius:12px;overflow:hidden;">
  <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:32px 28px;text-align:center;">
    <div style="font-size:28px;margin-bottom:8px;">🦞</div>
    <h1 style="color:#fff;font-size:22px;margin:0 0 6px;">Welcome to ClawMetry!</h1>
    <p style="color:#9ca3af;font-size:13px;margin:0;">Real-time observability for your AI agents</p>
  </div>
  <div style="padding:28px;">
    <p style="font-size:15px;line-height:1.7;color:#d1d5db;">Hey there 👋</p>
    <p style="font-size:15px;line-height:1.7;color:#d1d5db;">Thanks for subscribing! ClawMetry is a free, open-source dashboard that lets you see token costs, cron jobs, sub-agents, memory files, and session history in one place.</p>
    <p style="font-size:14px;line-height:1.7;color:#9ca3af;">Get started in one line:</p>
    <div style="background:#111827;border:1px solid #2d2d44;border-radius:8px;padding:14px 18px;font-family:monospace;font-size:13px;color:#10b981;margin:12px 0;">curl -fsSL https://clawmetry.com/install.sh | bash</div>
    <p style="font-size:15px;line-height:1.7;color:#d1d5db;margin-top:20px;">We just launched on Product Hunt and would love your support:</p>
    <div style="background:#1a1a2e;border:1px solid #2d2d44;border-radius:10px;padding:20px;margin:20px 0;">
      <div style="font-size:16px;font-weight:700;color:#fff;margin-bottom:8px;">🔼 Upvote on Product Hunt</div>
      <p style="font-size:13px;color:#9ca3af;margin:0 0 12px;">One click helps us reach more developers.</p>
      <a href="https://www.producthunt.com/products/clawmetry" style="display:inline-block;background:#ff6154;color:#fff;font-weight:700;font-size:13px;padding:10px 24px;border-radius:8px;text-decoration:none;">Upvote on Product Hunt →</a>
    </div>
    <div style="background:#1a1a2e;border:1px solid #2d2d44;border-radius:10px;padding:20px;margin:20px 0;">
      <div style="font-size:16px;font-weight:700;color:#fff;margin-bottom:8px;">⭐ Star us on GitHub</div>
      <p style="font-size:13px;color:#9ca3af;margin:0 0 12px;">Help other OpenClaw users discover ClawMetry.</p>
      <a href="https://github.com/vivekchand/clawmetry" style="display:inline-block;background:#238636;color:#fff;font-weight:700;font-size:13px;padding:10px 24px;border-radius:8px;text-decoration:none;">Star on GitHub →</a>
    </div>
    <div style="background:linear-gradient(135deg,#1e3a5f,#1a2744);border:1px solid #3b82f6;border-radius:10px;padding:20px;margin:24px 0;text-align:center;">
      <div style="font-size:24px;margin-bottom:8px;">🎁</div>
      <div style="font-size:16px;font-weight:700;color:#fff;margin-bottom:8px;">Get a $10 Amazon Gift Card</div>
      <p style="font-size:13px;color:#93c5fd;line-height:1.6;margin:0;">Try ClawMetry, leave a <a href="https://www.producthunt.com/products/clawmetry/reviews/new" style="color:#93c5fd;font-weight:700;">Product Hunt review</a>, and reply to this email with a screenshot of your dashboard. We will send you a <strong>$10 Amazon gift card</strong> as a thank you.</p>
    </div>
    <p style="font-size:15px;color:#d1d5db;">Cheers,<br><strong style="color:#fff;">The ClawMetry Team</strong> 🦞</p>
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
    subject = "Welcome to ClawMetry \U0001f99e"
    ok, resp = _resend_post("/emails", {
        "from": FROM_EMAIL, "to": [email], "bcc": ["hello@clawmetry.com"],
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

    # Notify Vivek — celebratory!
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

    # Send confirmation to requester
    try:
        _resend_post("/emails", {
            "from": FROM_EMAIL, "to": [email], "bcc": ["hello@clawmetry.com"],
            "subject": "We got your request! 🦞",
            "html": f"""<div style="font-family:sans-serif;max-width:500px;margin:0 auto;background:#0d0d14;color:#e0e0e0;border-radius:12px;overflow:hidden;">
              <div style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:32px 28px;text-align:center;">
                <div style="font-size:28px;margin-bottom:8px;">🦞</div>
                <h1 style="color:#fff;font-size:20px;margin:0;">Thanks, {name}!</h1>
              </div>
              <div style="padding:28px;">
                <p style="font-size:15px;line-height:1.7;color:#d1d5db;">We received your request for a managed ClawMetry instance. We'll review it and get back to you within 24-48 hours.</p>
                <p style="font-size:15px;line-height:1.7;color:#d1d5db;">In the meantime, you can always self-host ClawMetry for free:</p>
                <div style="background:#111827;border:1px solid #2d2d44;border-radius:8px;padding:14px 18px;font-family:monospace;font-size:13px;color:#10b981;margin:12px 0;">pip install clawmetry</div>
                <p style="font-size:15px;color:#d1d5db;">Cheers,<br><strong style="color:#fff;">Vivek @ ClawMetry</strong></p>
              </div>
            </div>"""
        })
    except Exception as e:
        log.error(f"[managed-request] confirmation email error: {e}")

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

    # Notify Vivek
    try:
        help_label = help_type.replace("-", " ").replace("_", " ").title() if help_type else "General"
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

    # Send confirmation email to requester
    try:
        display_name = name or "there"
        requests.post("https://api.resend.com/emails", headers={
            "Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"
        }, json={
            "from": FROM_EMAIL, "to": email, "bcc": ["hello@clawmetry.com"],
            "subject": "Got your request! Setting up your ClawMetry support 🤝",
            "text": f"Hey {display_name},\n\nThanks for reaching out! I got your request and will personally get back to you shortly to help you get ClawMetry up and running.\n\nClawMetry is open source and I want to make sure you get the most out of it.\n\nTalk soon,\nVivek"
        }, timeout=10)
    except Exception as e:
        log.error(f"[support-request] confirmation email error: {e}")

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
