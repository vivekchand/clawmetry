"""Minimal Flask backend for ClawMetry landing - serves static files + email subscribe."""
import json
import os
import re
from datetime import datetime, timezone

import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "re_jWLL59fj_PBctxiwxDLFiWjBZ9MiJ4ems")
SUBSCRIBERS_FILE = "/tmp/subscribers.json"
FROM_EMAIL = "ClawMetry <hello@clawmetry.com>"

WELCOME_HTML = """
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


def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_subscribers(subs):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subs, f, indent=2)


def send_welcome_email(email):
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": FROM_EMAIL,
                "to": [email],
                "subject": "Welcome to ClawMetry \U0001f99e",
                "html": WELCOME_HTML,
            },
            timeout=10,
        )
        return resp.status_code in (200, 201)
    except Exception:
        return False


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Invalid email"}), 400

    subs = load_subscribers()
    if any(s["email"] == email for s in subs):
        return jsonify({"ok": True, "message": "Already subscribed"})

    subs.append({"email": email, "subscribedAt": datetime.now(timezone.utc).isoformat()})
    save_subscribers(subs)
    send_welcome_email(email)
    return jsonify({"ok": True, "message": "Subscribed!"})


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(".", path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
