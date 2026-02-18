"""Minimal Flask backend for ClawMetry landing - serves static files + email subscribe via Resend."""
import os
import re
from datetime import datetime, timezone

import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "re_jWLL59fj_PBctxiwxDLFiWjBZ9MiJ4ems")
RESEND_AUDIENCE_ID = os.environ.get("RESEND_AUDIENCE_ID", "48212e72-0d6c-489c-90c3-85a03a52d54c")
FROM_EMAIL = "ClawMetry <hello@clawmetry.com>"
UPDATES_EMAIL = "ClawMetry Updates <updates@clawmetry.com>"
NOTIFY_SECRET = os.environ.get("NOTIFY_SECRET", "clawmetry-notify-2026")

VIVEK_EMAIL = "vivekchand19@gmail.com"
RESEND_HEADERS = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}

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
    """POST to Resend API, return (ok, data)."""
    try:
        r = requests.post(f"https://api.resend.com{path}", headers=RESEND_HEADERS, json=payload, timeout=10)
        return r.status_code in (200, 201), r.json() if r.content else {}
    except Exception as e:
        return False, {"error": str(e)}


def _resend_get(path):
    """GET from Resend API."""
    try:
        r = requests.get(f"https://api.resend.com{path}", headers=RESEND_HEADERS, timeout=10)
        return r.json() if r.content else {}
    except Exception:
        return {}


def send_welcome_email(email):
    return _resend_post("/emails", {
        "from": FROM_EMAIL,
        "to": [email],
        "subject": "Welcome to ClawMetry \U0001f99e",
        "html": WELCOME_HTML,
    })


def _get_visitor_info(req):
    """Extract location/browser info from request."""
    ip = req.headers.get("X-Forwarded-For", req.headers.get("X-Real-IP", req.remote_addr))
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    ua = req.headers.get("User-Agent", "Unknown")
    referer = req.headers.get("Referer", "Direct")
    # Try IP geolocation (best-effort)
    location = "Unknown"
    try:
        geo = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2).json()
        city = geo.get("city", "")
        region = geo.get("region", "")
        country = geo.get("country_name", "")
        loc = ", ".join(filter(None, [city, region, country]))
        if loc:
            location = loc
    except Exception as e:
        print(f"[geo] Failed for {ip}: {e}")
    return {"ip": ip, "user_agent": ua, "referer": referer, "location": location or "Unknown"}


def notify_vivek(subject, body_html):
    """Send a notification email to Vivek."""
    try:
        ok, resp = _resend_post("/emails", {
            "from": FROM_EMAIL,
            "to": [VIVEK_EMAIL],
            "subject": subject,
            "html": body_html,
        })
        if not ok:
            print(f"[notify_vivek] Resend error: {resp}")
    except Exception as e:
        print(f"[notify_vivek] Exception: {e}")


def add_contact(email):
    """Add contact to Resend audience. Returns (ok, already_existed)."""
    ok, data = _resend_post(f"/audiences/{RESEND_AUDIENCE_ID}/contacts", {
        "email": email,
        "unsubscribed": False,
    })
    # Resend returns the contact even if it already exists
    return ok, data


def get_all_contacts():
    """Get all subscribed contacts from Resend audience."""
    data = _resend_get(f"/audiences/{RESEND_AUDIENCE_ID}/contacts")
    contacts = data.get("data", [])
    return [c for c in contacts if not c.get("unsubscribed")]


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Invalid email"}), 400

    ok, resp = add_contact(email)
    if not ok:
        return jsonify({"error": "Failed to subscribe. Try again."}), 500

    send_welcome_email(email)

    # Notify Vivek (best-effort, don't block response)
    try:
        visitor = _get_visitor_info(request)
        notify_vivek(
            f"🦞 New ClawMetry subscriber: {email}",
            f"""<div style="font-family:sans-serif;max-width:500px;">
            <h2>New Subscriber!</h2>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Location:</strong> {visitor['location']}</p>
            <p><strong>IP:</strong> {visitor['ip']}</p>
            <p><strong>Browser:</strong> {visitor['user_agent'][:120]}</p>
            <p><strong>Referer:</strong> {visitor['referer']}</p>
            <p><strong>Time:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
            </div>"""
        )
    except Exception as e:
        print(f"[subscribe] Notify error: {e}")

    return jsonify({"ok": True, "message": "Subscribed!"})


@app.route("/api/notify", methods=["POST"])
def notify():
    """Send version bump notification to all subscribers.

    POST /api/notify
    Headers: X-Notify-Secret: <secret>
    Body: {"version": "0.5.0", "changes": "- Feature X\\n- Fix Y", "subject": "optional custom subject"}
    """
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
  <div style="text-align:center;padding:32px 0 24px;">
    <span style="font-size:48px;">&#x1F680;</span>
    <h1 style="font-size:24px;margin:12px 0 0;">ClawMetry {version}</h1>
  </div>
  <p>A new version of ClawMetry is out!</p>
  {"<h3>What's new:</h3><ul>" + changes_html + "</ul>" if changes_html else ""}
  <div style="background:#f4f4f8;border-radius:8px;padding:16px;margin:20px 0;font-family:'Courier New',monospace;font-size:14px;">
    <span style="color:#888;">$</span> pip install --upgrade clawmetry
  </div>
  <p>
    <a href="https://github.com/vivekchand/clawmetry/releases" style="color:#E5443A;">Release Notes</a> |
    <a href="https://pypi.org/project/clawmetry/" style="color:#E5443A;">PyPI</a> |
    <a href="https://clawmetry.com" style="color:#E5443A;">Website</a>
  </p>
  <p style="color:#888;font-size:13px;margin-top:32px;border-top:1px solid #eee;padding-top:16px;">
    You're receiving this because you subscribed at clawmetry.com.
  </p>
</div>"""

    contacts = get_all_contacts()
    if not contacts:
        return jsonify({"ok": True, "sent": 0, "message": "No subscribers yet"})

    # Use Resend batch send
    emails = [c["email"] for c in contacts]
    sent = 0
    errors = []
    for email in emails:
        ok, resp = _resend_post("/emails", {
            "from": UPDATES_EMAIL,
            "to": [email],
            "subject": subject,
            "html": html,
        })
        if ok:
            sent += 1
        else:
            errors.append({"email": email, "error": resp})

    return jsonify({"ok": True, "sent": sent, "total": len(emails), "errors": errors})


@app.route("/api/copy-track", methods=["POST"])
def copy_track():
    """Track when someone copies the install command."""
    data = request.get_json(silent=True) or {}
    tab = data.get("tab", "unknown")
    command = data.get("command", "")
    visitor = _get_visitor_info(request)

    notify_vivek(
        f"🦞 Someone copied ClawMetry install command ({tab})",
        f"""<div style="font-family:sans-serif;max-width:500px;">
        <h2>Install Command Copied!</h2>
        <p><strong>Tab:</strong> {tab}</p>
        <p><strong>Command:</strong> <code>{command}</code></p>
        <p><strong>Location:</strong> {visitor['location']}</p>
        <p><strong>IP:</strong> {visitor['ip']}</p>
        <p><strong>Browser:</strong> {visitor['user_agent'][:120]}</p>
        <p><strong>Referer:</strong> {visitor['referer']}</p>
        <p><strong>Time:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
        </div>"""
    )

    return jsonify({"ok": True})


@app.route("/api/subscribers", methods=["GET"])
def list_subscribers():
    """List subscriber count (protected)."""
    if request.headers.get("X-Notify-Secret") != NOTIFY_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    contacts = get_all_contacts()
    return jsonify({"count": len(contacts), "subscribers": [c["email"] for c in contacts]})


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
