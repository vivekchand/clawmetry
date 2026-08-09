"""ClawMetry desktop app — first-launch onboarding pane.

Renders three surfaces inside the native pywebview window:

1. **Auth pane** — shown once, on first launch. Detects paid runtimes
   on the machine (Claude Code, Cursor, Codex, …) and offers three
   sign-in paths that mirror ``clawmetry onboard``:

   - GitHub OAuth  → system browser → cloud site → loopback callback
   - Google OAuth  → system browser → cloud site → loopback callback
   - Email OTP     → in-window form → /api/auth/email-otp

   The desktop shell is the high-intent surface (a user chose ``.dmg``
   over ``pip``); we lean into that by auto-starting the 7-day Pro trial
   for any account that lands here with paid runtimes detected. Payment
   is deferred to trial-day-6+ via a header chip, never blocked at
   onboarding.

2. **Bootstrap carousel** — shown WHILE the runtime venv provisions
   and clawmetry pip-installs. Ubuntu-installer-style: 4 auto-advancing
   slides cross-selling the rest of the ClawMetry product family
   (Agent Builder, Desk Device, Enterprise SSO). Auto-dismisses the
   moment the daemon is ready.

3. **Dashboard-ready gate** — the last splash before the real UI loads.
   Polls the daemon's /api/overview and swaps only when either
   sessions>0, runtimes_detected>0, or 20s elapsed. Prevents the flash
   of empty state that a "wait for HTTP 200" bar would produce.

All three surfaces return self-contained HTML (no external assets, no
network beyond loopback). Colors + logo come from the same brand
tokens as the splash in ``app.py``. Everything below is deliberately
pure — no pywebview imports here; the module can be unit-tested from
plain Python."""

from __future__ import annotations

import base64
import http.server
import json
import os
import platform
import shutil
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Callable, Optional

# OAuth loopback deadline. The CLI uses 180s; the desktop pane matches
# so a user who tabs away for a minute doesn't get kicked out.
OAUTH_LOOPBACK_TIMEOUT_SECS = 180.0

# Email OTP endpoints (match `clawmetry onboard` exactly). Overridable
# via the same env vars clawmetry/endpoints.py honours — self-hosted
# customers with a private cloud base need the pane to hit their own
# endpoint, not app.clawmetry.com.
DEFAULT_APP_BASE = "https://app.clawmetry.com"


def resolve_app_base() -> str:
    for env in ("CLAWMETRY_APP_URL", "CLAWMETRY_ENDPOINT", "CLAWMETRY_INGEST_URL"):
        v = (os.environ.get(env) or "").strip().rstrip("/")
        if v:
            return v
    return DEFAULT_APP_BASE

# ─── Brand tokens (must match desktop/app.py) ───────────────────────────
BRAND_RED = "#E94644"
BRAND_BG_DARK = "#0b0e14"
BRAND_BG_PANEL = "#141924"
BRAND_TEXT = "#e2e8f0"
BRAND_MUTED = "#94a3b8"
BRAND_BORDER = "#1f2937"

# ─── First-launch state ─────────────────────────────────────────────────
# A stamp file in the runtime dir marks that we've shown onboarding at
# least once. Users who ONBOARDED without signing in (skipped) still see
# it dismissed — the sign-in CTA moves to the dashboard header. This
# avoids nag-loops on machines where the user genuinely wants local-only.
ONBOARDING_STAMP_NAME = "onboarding-completed.json"


def is_first_launch(runtime_dir: Path) -> bool:
    """True when we have never completed onboarding for this install."""
    return not (Path(runtime_dir) / ONBOARDING_STAMP_NAME).exists()


def mark_onboarding_completed(
    runtime_dir: Path,
    *,
    signed_in: bool,
    provider: str = "",
    email: str = "",
) -> None:
    """Stamp the runtime dir so we don't show onboarding again. ``signed_in``
    is False for users who dismissed the pane without authenticating — the
    stamp still writes so we don't re-prompt on relaunch."""
    stamp = Path(runtime_dir) / ONBOARDING_STAMP_NAME
    payload = {
        "completed": True,
        "signed_in": bool(signed_in),
        "provider": provider or "",
        "email": email or "",
    }
    try:
        stamp.write_text(json.dumps(payload))
    except OSError:
        pass  # onboarding stamp is best-effort; a re-shown pane is not a bug


def _win_subprocess_kwargs() -> dict:
    """Extra Popen/run kwargs that stop Windows from flashing a console
    window when this windowed (console=False) shell spawns a console
    executable (the venv's python.exe / clawmetry.exe). No-op elsewhere.
    Mirrors app.py's helper — duplicated rather than imported to keep
    onboarding.py importable standalone (app.py imports IT, not vice
    versa)."""
    if platform.system() == "Windows":
        return {"creationflags": subprocess.CREATE_NO_WINDOW}  # type: ignore[attr-defined]
    return {}


# ─── Runtime detection ──────────────────────────────────────────────────
# The clawmetry package (which lives in the runtime venv) has the
# canonical detection logic in ``clawmetry/entitlements.py``. From the
# desktop shell we do NOT import clawmetry directly — that would pull
# code across the shell/runtime boundary. Instead we shell out to the
# same detection via the venv's clawmetry CLI, which prints JSON.
#
# Detection is a HINT for messaging only. The trial-start path validates
# entitlement against the cloud, so a stale/spoofed local detection just
# means the pane copy is slightly less specific — it never grants Pro.


def detect_runtimes_via_venv(venv_python: Path, *, timeout: float = 6.0) -> list[dict]:
    """Ask the runtime venv's clawmetry to list detected runtimes.

    Returns [{"key": "claude-code", "name": "Claude Code", "tier": "pro"}, ...]
    or an empty list on any failure. Timeout intentionally short: the
    onboarding pane can't stall on detection — better to under-personalise
    than to make users stare at "Detecting..." for 30s."""
    py = Path(venv_python)
    if not py.exists():
        return []
    script = (
        "import json, sys\n"
        "try:\n"
        "    from clawmetry.entitlements import list_detected_runtimes\n"
        "    print(json.dumps(list_detected_runtimes()))\n"
        "except Exception:\n"
        "    print('[]')\n"
    )
    try:
        r = subprocess.run(
            [str(py), "-c", script],
            capture_output=True, text=True, timeout=timeout,
            **_win_subprocess_kwargs(),
        )
        if r.returncode == 0:
            data = json.loads(r.stdout.strip() or "[]")
            if isinstance(data, list):
                return [d for d in data if isinstance(d, dict)]
    except Exception:
        pass
    return []


# ─── Post-auth: hand key to clawmetry connect ───────────────────────────

def apply_cm_key(
    venv_clawmetry: Path, cm_key: str, *, mode: str = "cloud", timeout: float = 60.0
) -> tuple[bool, str]:
    """Run ``clawmetry connect --key cm_…`` in the venv.

    This is the single seam that:
      * validates the key against the cloud (/auth)
      * writes ~/.clawmetry/config.json
      * calls ``auto_provision_pro`` (Pro wheel downloads iff account is
        Trial/Starter/Pro/Enterprise) — this is what starts the 7-day
        all-runtimes trial in both modes
      * starts the sync daemon

    ``mode`` is the user's hosting choice from the onboarding pane:
      * "cloud"    → ``--start-sync-now``: cloud sync ON (E2E-encrypted
                     snapshots to ingest.clawmetry.com).
      * "selfhost" → ``--keep-local --defer-sync`` + ``clawmetry sync``:
                     account linked, trial provisioned, nocloud marker
                     kept, data stays on this machine; the sync daemon
                     runs local-only ingest.

    We avoid duplicating any of that in the shell. Returns
    (ok, short_message). The message is user-safe (no key/token
    fragments)."""
    bin_ = Path(venv_clawmetry)
    if not bin_.exists():
        return False, "runtime venv is not ready yet"
    if not (cm_key or "").startswith("cm_"):
        return False, "invalid sign-in key"
    # selfhost: --keep-local preserves the nocloud marker (sign-in must not
    # flip a self-host install to cloud sync), skips the ownership OTP that
    # would otherwise kill this non-interactive subprocess, and still mints
    # the account's 7-day trial; --defer-sync leaves daemon/dashboard
    # management to this shell.
    mode_flags = (
        ["--keep-local", "--defer-sync"] if mode == "selfhost"
        else ["--start-sync-now"]
    )
    try:
        r = subprocess.run(
            [str(bin_), "connect", "--key", cm_key, *mode_flags],
            capture_output=True, text=True, timeout=timeout,
            **_win_subprocess_kwargs(),
        )
        if r.returncode == 0 and mode == "selfhost":
            # --defer-sync leaves the daemon down; start local-only
            # ingest now so the dashboard has data on first paint. The
            # shell's watcher heals it from here on.
            try:
                subprocess.run(
                    [str(bin_), "sync"],
                    capture_output=True, text=True, timeout=timeout,
                    **_win_subprocess_kwargs(),
                )
            except Exception:
                pass  # ensure_sync_daemon() in app.py retries
    except subprocess.TimeoutExpired:
        return False, "sign-in timed out — check your connection and try again"
    except Exception as exc:
        return False, f"sign-in error: {exc}"
    if r.returncode == 0:
        return True, "signed in"
    # Trim to the last non-empty line — clawmetry connect prints a
    # user-friendly one-liner on failure.
    tail = next(
        (ln for ln in reversed((r.stderr + r.stdout).splitlines()) if ln.strip()),
        "sign-in failed",
    )
    return False, tail.strip()[:200]


# ─── Cross-sell slides (Ubuntu-installer style) ─────────────────────────
# One tuple = one card. Copy is deliberately declarative — no exclamation
# marks, no "!". Ordered by strongest cross-sell first: the dashboard's
# own capability, then the two adjacent products, then Enterprise SSO for
# the buying committee reading over a developer's shoulder.

CROSS_SELL_SLIDES = [
    {
        "eyebrow": "You just installed ClawMetry.",
        "title": "Every AI agent on this machine, in one dashboard.",
        "body": (
            "Watch spend, sessions, and errors across 14+ runtimes in real time. "
            "Cost breakdowns per model, per skill, per session. Loop detection. "
            "Budget alerts. All read-only, all local, all yours."
        ),
        "cta_label": "",
        "cta_url": "",
        "art": "dashboard",
    },
    {
        "eyebrow": "Also from ClawMetry",
        "title": "ClawMetry Agent Builder: ship an agent in an afternoon.",
        "body": (
            "Blueprints, requirements, work orders: the same platform that "
            "ships ClawMetry itself. If you can describe the agent, the builder "
            "can scaffold it and keep the docs in sync with the code."
        ),
        "cta_label": "Explore Agent Builder",
        "cta_url": "https://build.clawmetry.com",
        "art": "builder",
    },
    {
        "eyebrow": "Also from ClawMetry",
        "title": "ClawMetry Desk: always-on hardware for your agents.",
        "body": (
            "A pocket-sized ambient device that shows every agent at a "
            "glance and lets you tap Approve, Deny, Stop, Pause, or Resume "
            "right on its 4-inch touchscreen. Wi-Fi, USB-C powered, "
            "end-to-end encrypted."
        ),
        "cta_label": "See the Desk device",
        "cta_url": "https://clawmetry.com/device",
        "art": "desk",
    },
    {
        "eyebrow": "For teams",
        "title": "SSO, RBAC, and audit: Enterprise-ready.",
        "body": (
            "Okta, Azure AD, or Google Workspace. Per-runtime role scoping. "
            "Every action logged. SOC 2 Type II, GDPR, and CCPA covered. "
            "Included on Enterprise plans."
        ),
        "cta_label": "Talk to sales",
        "cta_url": "https://clawmetry.com/enterprise",
        "art": "enterprise",
    },
]


# ─── Slide art (inline SVG) ─────────────────────────────────────────────
# One hand-drawn vector illustration per slide, in brand colors. Inline
# SVG keeps the pane self-contained (the module promises no external
# assets) and stays crisp at any DPI — a downscaled raster screenshot of
# the landing site reads as cheap; a purpose-built diagram reads as the
# product. One idea per picture, nothing else.

SLIDE_ART_SVG = {
    # An idealized in-app view (Apple-style marketing render, not a
    # raster screenshot): window chrome, live stat tiles, spend chart,
    # session rows. Detailed enough to sell "this is what you get".
    "dashboard": """<svg viewBox="0 0 460 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The ClawMetry dashboard"
     font-family="-apple-system,'Segoe UI',system-ui,sans-serif">
  <rect x="10" y="10" width="440" height="260" rx="14" fill="#10151f" stroke="#1f2937" stroke-width="1.5"/>
  <g fill="#273143">
    <circle cx="30" cy="28" r="4"/><circle cx="44" cy="28" r="4"/><circle cx="58" cy="28" r="4"/>
  </g>
  <circle cx="86" cy="28" r="4.5" fill="#E94644"/>
  <text x="96" y="32" font-size="11" font-weight="700" fill="#e2e8f0">ClawMetry</text>
  <g font-size="10" fill="#94a3b8">
    <text x="240" y="32" fill="#e2e8f0" font-weight="600">Overview</text>
    <text x="298" y="32">Sessions</text>
    <text x="352" y="32">Usage</text>
    <text x="392" y="32">Brain</text>
  </g>
  <rect x="240" y="38" width="48" height="2" rx="1" fill="#E94644"/>
  <g>
    <rect x="26" y="52" width="128" height="52" rx="10" fill="#141924" stroke="#1f2937"/>
    <text x="38" y="70" font-size="7.5" letter-spacing="1" fill="#94a3b8">TOKENS TODAY</text>
    <text x="38" y="92" font-size="16" font-weight="700" fill="#e2e8f0">4.2M</text>
    <rect x="166" y="52" width="128" height="52" rx="10" fill="#141924" stroke="#1f2937"/>
    <text x="178" y="70" font-size="7.5" letter-spacing="1" fill="#94a3b8">SPEND TODAY</text>
    <text x="178" y="92" font-size="16" font-weight="700" fill="#e2e8f0">$12.40</text>
    <rect x="306" y="52" width="128" height="52" rx="10" fill="#141924" stroke="#1f2937"/>
    <text x="318" y="70" font-size="7.5" letter-spacing="1" fill="#94a3b8">AGENTS LIVE</text>
    <text x="318" y="92" font-size="16" font-weight="700" fill="#e2e8f0">7</text>
    <circle cx="350" cy="87" r="4" fill="#4ade80"/>
  </g>
  <g>
    <rect x="26" y="114" width="268" height="104" rx="10" fill="#141924" stroke="#1f2937"/>
    <text x="38" y="132" font-size="7.5" letter-spacing="1" fill="#94a3b8">SPEND · LAST 24H</text>
    <g stroke="#1c2433" stroke-width="1">
      <path d="M38 156 L 282 156"/><path d="M38 180 L 282 180"/>
    </g>
    <defs>
      <linearGradient id="cm-a" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#E94644" stop-opacity=".28"/>
        <stop offset="1" stop-color="#E94644" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <path d="M38 196 L 66 184 L 94 190 L 122 168 L 150 176 L 178 152 L 206 160 L 234 142 L 262 148 L 282 138 L 282 206 L 38 206 Z"
          fill="url(#cm-a)"/>
    <path d="M38 196 L 66 184 L 94 190 L 122 168 L 150 176 L 178 152 L 206 160 L 234 142 L 262 148 L 282 138"
          fill="none" stroke="#E94644" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="282" cy="138" r="3.5" fill="#E94644"/>
  </g>
  <g>
    <rect x="306" y="114" width="128" height="104" rx="10" fill="#141924" stroke="#1f2937"/>
    <text x="318" y="132" font-size="7.5" letter-spacing="1" fill="#94a3b8">BY MODEL</text>
    <g font-size="8.5" fill="#94a3b8">
      <text x="318" y="152">opus</text>
      <text x="318" y="176">sonnet</text>
      <text x="318" y="200">haiku</text>
    </g>
    <g fill="#E94644">
      <rect x="352" y="145" width="70" height="8" rx="4"/>
      <rect x="352" y="169" width="44" height="8" rx="4" opacity=".65"/>
      <rect x="352" y="193" width="22" height="8" rx="4" opacity=".4"/>
    </g>
  </g>
  <g>
    <circle cx="34" cy="238" r="4" fill="#4ade80"/>
    <text x="46" y="241" font-size="9.5" fill="#e2e8f0">claude-code · refactor auth flow</text>
    <text x="252" y="241" font-size="9.5" fill="#94a3b8">$0.84</text>
    <circle cx="316" cy="238" r="4" fill="#4ade80"/>
    <text x="328" y="241" font-size="9.5" fill="#e2e8f0">openclaw · main</text>
    <text x="412" y="241" font-size="9.5" fill="#94a3b8">$2.10</text>
    <circle cx="34" cy="256" r="4" fill="#facc15"/>
    <text x="46" y="259" font-size="9.5" fill="#e2e8f0">cursor · fix flaky e2e</text>
    <text x="252" y="259" font-size="9.5" fill="#94a3b8">$0.31</text>
    <circle cx="316" cy="256" r="4" fill="#94a3b8"/>
    <text x="328" y="259" font-size="9.5" fill="#e2e8f0">codex · idle</text>
    <text x="412" y="259" font-size="9.5" fill="#94a3b8">$0.00</text>
  </g>
</svg>""",
    # Blueprint scaffold: describe the agent, the builder wires it up.
    "builder": """<svg viewBox="0 0 440 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Agent blueprint being scaffolded">
  <rect x="70" y="30" width="300" height="180" rx="14" fill="none"
        stroke="#334155" stroke-width="1.5" stroke-dasharray="7 7"/>
  <g stroke="#334155" fill="none" stroke-width="1.5">
    <path d="M220 78 L 150 132"/>
    <path d="M220 78 L 290 132"/>
    <path d="M150 156 L 150 168"/>
    <path d="M290 156 L 290 168"/>
  </g>
  <circle cx="220" cy="68" r="20" fill="#141924" stroke="#E94644" stroke-width="2"/>
  <rect x="212" y="60" width="16" height="16" rx="4" fill="#E94644"/>
  <g fill="#141924" stroke="#1f2937">
    <rect x="122" y="132" width="56" height="26" rx="8"/>
    <rect x="262" y="132" width="56" height="26" rx="8"/>
  </g>
  <g fill="#94a3b8">
    <rect x="132" y="142" width="36" height="5" rx="2.5"/>
    <rect x="272" y="142" width="36" height="5" rx="2.5"/>
  </g>
  <g fill="#141924" stroke="#334155" stroke-dasharray="4 4">
    <rect x="122" y="168" width="56" height="26" rx="8"/>
    <rect x="262" y="168" width="56" height="26" rx="8"/>
  </g>
  <g stroke="#94a3b8" stroke-width="1.6" stroke-linecap="round">
    <path d="M150 176 L 150 186 M145 181 L 155 181"/>
    <path d="M290 176 L 290 186 M285 181 L 295 181"/>
  </g>
</svg>""",
    # The Desk device: a screen of agents with approve/deny at a glance.
    "desk": """<svg viewBox="0 0 440 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ClawMetry Desk device">
  <ellipse cx="220" cy="212" rx="96" ry="8" fill="#0f131c"/>
  <rect x="140" y="28" width="160" height="178" rx="20" fill="#141924" stroke="#1f2937" stroke-width="1.5"/>
  <rect x="154" y="42" width="132" height="128" rx="10" fill="#0b0e14" stroke="#1f2937"/>
  <g>
    <circle cx="170" cy="60" r="4" fill="#4ade80"/>
    <rect x="182" y="56" width="66" height="7" rx="3.5" fill="#94a3b8"/>
    <circle cx="170" cy="84" r="4" fill="#4ade80"/>
    <rect x="182" y="80" width="52" height="7" rx="3.5" fill="#94a3b8"/>
    <circle cx="170" cy="108" r="4" fill="#E94644"/>
    <rect x="182" y="104" width="60" height="7" rx="3.5" fill="#94a3b8"/>
  </g>
  <g>
    <rect x="164" y="130" width="52" height="24" rx="12" fill="none" stroke="#4ade80" stroke-width="1.5"/>
    <path d="M182 142 L 187 147 L 197 136" fill="none" stroke="#4ade80" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <rect x="224" y="130" width="52" height="24" rx="12" fill="none" stroke="#E94644" stroke-width="1.5"/>
    <path d="M244 137 L 255 147 M255 137 L 244 147" stroke="#E94644" stroke-width="2" stroke-linecap="round"/>
  </g>
  <rect x="204" y="182" width="32" height="8" rx="4" fill="#1f2937"/>
  <rect x="210" y="206" width="20" height="5" rx="2.5" fill="#1f2937"/>
</svg>""",
    # Shield + identity ring: SSO in, every action audited.
    "enterprise": """<svg viewBox="0 0 440 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Enterprise SSO and audit shield">
  <g stroke="#334155" fill="none" stroke-width="1.5">
    <path d="M96 70 C 140 70, 150 120, 178 120"/>
    <path d="M96 120 L 178 120"/>
    <path d="M96 170 C 140 170, 150 120, 178 120"/>
  </g>
  <g fill="#141924" stroke="#1f2937">
    <circle cx="78" cy="70" r="17"/>
    <circle cx="78" cy="120" r="17"/>
    <circle cx="78" cy="170" r="17"/>
  </g>
  <g fill="#94a3b8">
    <circle cx="78" cy="65" r="5"/>
    <path d="M68 79 C 68 71, 88 71, 88 79 Z"/>
    <circle cx="78" cy="115" r="5"/>
    <path d="M68 129 C 68 121, 88 121, 88 129 Z"/>
    <circle cx="78" cy="165" r="5"/>
    <path d="M68 179 C 68 171, 88 171, 88 179 Z"/>
  </g>
  <path d="M240 40 L 306 62 L 306 122 C 306 164, 276 190, 240 202
           C 204 190, 174 164, 174 122 L 174 62 Z"
        fill="#141924" stroke="#E94644" stroke-width="2"/>
  <path d="M214 120 L 234 142 L 268 100" fill="none" stroke="#E94644"
        stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  <g fill="#334155">
    <rect x="336" y="76" width="70" height="9" rx="4.5"/>
    <rect x="336" y="96" width="54" height="9" rx="4.5"/>
    <rect x="336" y="116" width="62" height="9" rx="4.5"/>
    <rect x="336" y="136" width="44" height="9" rx="4.5"/>
  </g>
</svg>""",
}


# ─── HTML surfaces ──────────────────────────────────────────────────────
# All three panes share a common shell (font, dark background, centered
# card). Kept as one string so re-flowing the layout is a single edit.

def _shared_css() -> str:
    return f"""
    :root {{
      --bg: {BRAND_BG_DARK};
      --panel: {BRAND_BG_PANEL};
      --border: {BRAND_BORDER};
      --text: {BRAND_TEXT};
      --muted: {BRAND_MUTED};
      --accent: {BRAND_RED};
    }}
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0; padding: 0; height: 100%;
      background: var(--bg); color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
        "Inter", system-ui, sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    button {{
      font-family: inherit; font-size: 14px; font-weight: 600;
      border: 0; border-radius: 8px; padding: 12px 18px;
      cursor: pointer; transition: background 120ms, transform 60ms;
    }}
    button:active {{ transform: translateY(1px); }}
    button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
    input {{
      font-family: inherit; font-size: 14px;
      background: var(--bg); color: var(--text);
      border: 1px solid var(--border); border-radius: 8px;
      padding: 12px 14px; width: 100%;
    }}
    input:focus {{ outline: none; border-color: var(--accent); }}
    .center {{
      min-height: 100vh; display: flex; align-items: center;
      justify-content: center; padding: 32px;
    }}
    .brand-logo {{
      display: block; margin: 0 auto 24px; width: 220px; height: auto;
      opacity: 0.98;
    }}
    """


def _asset_data_uri(assets_dir: Path, name: str, mime: str) -> str:
    """Embed a bundled asset as a data URI so the HTML is fully
    self-contained (no external asset loads)."""
    p = Path(assets_dir) / name
    try:
        return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()
    except OSError:
        return ""


def _logo_data_uri(assets_dir: Path) -> str:
    return _asset_data_uri(
        assets_dir, "clawmetry-logo-horizontal-darkbg.svg", "image/svg+xml"
    )


def render_mode_pane(*, assets_dir: Path) -> str:
    """Post-sign-in hosting choice: ClawMetry Cloud vs Local / Self-host.

    Both choices start the same 7-day all-runtimes trial (the account's
    entitlement does that); the ONLY difference is where the data goes,
    and the pane says so explicitly. Calls
    ``window.pywebview.api.choose_mode('cloud'|'selfhost')``."""
    logo = _logo_data_uri(assets_dir)
    return f"""<!doctype html>
<html><head>
  <meta charset="utf-8"/>
  <title>ClawMetry: Choose hosting</title>
  <style>
    {_shared_css()}
    .card {{
      width: 100%; max-width: 620px;
      background: var(--panel); border: 1px solid var(--border);
      border-radius: 16px; padding: 40px 36px;
    }}
    .headline {{
      font-size: 22px; font-weight: 700; letter-spacing: -0.01em;
      margin: 0 0 8px; line-height: 1.25;
    }}
    .subline {{
      color: var(--muted); font-size: 14px; line-height: 1.5;
      margin: 0 0 24px;
    }}
    .modes {{ display: flex; gap: 14px; }}
    .mode {{
      flex: 1; text-align: left; cursor: pointer;
      background: var(--bg); border: 1px solid var(--border);
      border-radius: 12px; padding: 20px 18px;
      transition: border-color .15s ease;
      /* <button> does NOT inherit text color — without this the
         headings render UA-default black on the dark card. */
      color: var(--text);
    }}
    .mode:hover {{ border-color: var(--accent); }}
    .mode h3 {{ margin: 0 0 6px; font-size: 15px; color: var(--text); }}
    .mode p {{ margin: 0; color: var(--muted); font-size: 12.5px; line-height: 1.5; }}
    .mode .tag {{
      display: inline-block; margin-bottom: 10px; padding: 2px 9px;
      border-radius: 999px; font-size: 10.5px; font-weight: 700;
      letter-spacing: .04em; text-transform: uppercase;
    }}
    .mode.cloud .tag {{ background: rgba(124,140,255,.15); color: #a5b4ff; }}
    .mode.selfhost .tag {{ background: rgba(74,222,128,.12); color: #4ade80; }}
    .trial-note {{
      margin-top: 20px; text-align: center; font-size: 12.5px;
      color: var(--muted);
    }}
    .trial-note b {{ color: var(--text); }}
  </style>
</head><body>
  <div class="center"><div class="card">
    {'<img class="brand-logo" src="' + logo + '" alt="ClawMetry"/>' if logo else ''}
    <h1 class="headline">Where should your data live?</h1>
    <p class="subline">Either way, your <b>7-day free trial of every runtime</b> starts
      now — this only decides where dashboards are served from.</p>
    <div class="modes">
      <button class="mode cloud" onclick="choose('cloud')">
        <span class="tag">Cloud</span>
        <h3>ClawMetry Cloud</h3>
        <p>See this machine's agents from anywhere at app.clawmetry.com.
           Snapshots leave this machine E2E-encrypted; only your browser
           holds the key.</p>
      </button>
      <button class="mode selfhost" onclick="choose('selfhost')">
        <span class="tag">Local / Self-host</span>
        <h3>Stay on this machine</h3>
        <p>Nothing leaves this box. Dashboard on localhost only.
           You can turn cloud sync on later with one click.</p>
      </button>
    </div>
    <p class="trial-note">No card required. After 7 days the free tier keeps
      OpenClaw &amp; NemoClaw; paid tiers keep everything.</p>
  </div></div>
  <script>
    var done = false;
    function choose(mode) {{
      if (done) return; done = true;
      try {{ window.pywebview.api.choose_mode(mode); }} catch (e) {{ done = false; }}
    }}
  </script>
</body></html>
"""


def render_auth_pane(
    *,
    assets_dir: Path,
    detected_runtimes: list[dict],
) -> str:
    """First-launch sign-in pane. Three buttons + collapsible email OTP.
    Communicates to Python via ``window.pywebview.api.*`` (exposed by
    RuntimeSupervisor in app.py)."""
    logo = _logo_data_uri(assets_dir)

    # Personalised headline when a paid runtime is detected.
    paid = [r for r in detected_runtimes if (r.get("tier") or "").lower() == "pro"]
    if paid:
        names = ", ".join(r.get("name", r.get("key", "")) for r in paid[:3])
        headline = f"Detected {names} on this machine."
        subline = (
            "Start your free 7-day ClawMetry Pro trial to watch these live. "
            "No card required. Payment kicks in on day 8 if you keep it."
        )
    else:
        headline = "Welcome to ClawMetry."
        subline = (
            "Sign in to sync your dashboards across devices and unlock Pro "
            "runtimes when they show up on this machine."
        )

    return f"""<!doctype html>
<html><head>
  <meta charset="utf-8"/>
  <title>ClawMetry: Sign in</title>
  <style>
    {_shared_css()}
    .card {{
      width: 100%; max-width: 460px;
      background: var(--panel); border: 1px solid var(--border);
      border-radius: 16px; padding: 40px 36px;
    }}
    .headline {{
      font-size: 22px; font-weight: 700; letter-spacing: -0.01em;
      margin: 0 0 8px; line-height: 1.25;
    }}
    .subline {{
      color: var(--muted); font-size: 14px; line-height: 1.5;
      margin: 0 0 28px;
    }}
    .btn-primary {{
      background: var(--accent); color: #fff; width: 100%;
      display: flex; align-items: center; justify-content: center; gap: 10px;
    }}
    .btn-primary:hover:not(:disabled) {{ background: #d63b39; }}
    .btn-primary svg {{ width: 18px; height: 18px; }}
    .btn-oauth {{
      background: var(--bg); color: var(--text);
      border: 1px solid var(--border); width: 100%;
      display: flex; align-items: center; justify-content: center; gap: 10px;
    }}
    .btn-oauth:hover:not(:disabled) {{ background: #1a2130; }}
    .btn-oauth svg {{ width: 18px; height: 18px; }}
    /* Email is a tertiary CTA — subdued outlined below the OAuth pair.
       Visual weight goes: GitHub (primary red) > Google (outlined) >
       Email (thin outlined). Matches the CLI's `[1] GitHub [2] Google`
       presentation with email as fallback. */
    .btn-tertiary {{
      background: transparent; color: var(--muted);
      border: 1px solid var(--border); width: 100%;
      display: flex; align-items: center; justify-content: center; gap: 10px;
      font-weight: 500;
    }}
    .btn-tertiary:hover:not(:disabled) {{
      color: var(--text); border-color: var(--muted);
    }}
    .stack {{ display: flex; flex-direction: column; gap: 10px; }}
    .rule {{
      display: flex; align-items: center; gap: 12px;
      color: var(--muted); font-size: 12px;
      margin: 20px 0 16px;
    }}
    .rule::before, .rule::after {{
      content: ""; flex: 1; height: 1px; background: var(--border);
    }}
    .otp-block {{ display: none; }}
    .otp-block.open {{ display: block; }}
    .otp-hint {{
      color: var(--muted); font-size: 12px; margin: 10px 0 0;
      text-align: center;
    }}
    .status {{
      margin-top: 16px; font-size: 13px;
      min-height: 18px; color: var(--muted);
      text-align: center;
    }}
    .status.error {{ color: #f87171; }}
    .status.success {{ color: #4ade80; }}
    .skip-link {{
      display: block; text-align: center; font-size: 12px;
      color: var(--muted); margin-top: 20px;
    }}
  </style>
</head><body>
  <div class="center"><div class="card">
    {'<img class="brand-logo" src="' + logo + '" alt="ClawMetry"/>' if logo else '<div style="text-align:center;font-size:22px;font-weight:700;margin-bottom:24px">ClawMetry</div>'}
    <h1 class="headline">{headline}</h1>
    <p class="subline">{subline}</p>

    <div class="stack">
      <button class="btn-primary" id="btn-github" onclick="oauth('github')">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M12 .5C5.65.5.5 5.65.5 12A11.5 11.5 0 0 0 8.36 22.94c.58.11.79-.25.79-.55v-2.02c-3.2.7-3.88-1.37-3.88-1.37-.52-1.32-1.28-1.68-1.28-1.68-1.04-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.76 2.7 1.25 3.35.96.1-.75.4-1.25.73-1.54-2.55-.29-5.24-1.28-5.24-5.68 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.47.11-3.06 0 0 .97-.31 3.18 1.18a11.02 11.02 0 0 1 5.79 0c2.21-1.49 3.18-1.18 3.18-1.18.63 1.59.23 2.77.11 3.06.74.81 1.19 1.83 1.19 3.09 0 4.41-2.7 5.38-5.27 5.67.42.35.79 1.05.79 2.13v3.16c0 .3.21.67.8.55A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5z"/>
        </svg>
        Continue with GitHub
      </button>
      <button class="btn-oauth" id="btn-google" onclick="oauth('google')">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.76h3.56c2.08-1.92 3.28-4.75 3.28-8.09z"/>
          <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.56-2.76c-.99.66-2.25 1.06-3.72 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.85A11 11 0 0 0 12 23z"/>
          <path fill="#FBBC05" d="M5.84 14.11a6.6 6.6 0 0 1 0-4.22V7.04H2.18a11 11 0 0 0 0 9.92l3.66-2.85z"/>
          <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.2 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.04l3.66 2.85C6.71 7.31 9.14 5.38 12 5.38z"/>
        </svg>
        Continue with Google
      </button>
    </div>

    <div class="rule">or</div>

    <div class="stack">
      <button class="btn-tertiary" id="btn-email" onclick="toggleEmail()">
        Continue with email
      </button>
    </div>

    <div class="otp-block" id="otp-block">
      <div class="stack" style="margin-top:12px">
        <input id="email-input" type="email" placeholder="you@company.com" autocomplete="email"/>
        <button class="btn-primary" id="btn-send-otp" onclick="sendOtp()">Send code</button>
      </div>
      <div class="stack" id="otp-input-block" style="margin-top:10px; display:none">
        <input id="otp-input" type="text" placeholder="6-digit code" maxlength="6" inputmode="numeric" autocomplete="one-time-code"/>
        <button class="btn-primary" id="btn-verify-otp" onclick="verifyOtp()">Verify &amp; sign in</button>
      </div>
      <p class="otp-hint">A one-time code will land in your inbox in a few seconds.</p>
    </div>

    <div class="status" id="status"></div>

    <a class="skip-link" href="#" onclick="skipAuth(); return false;">
      Skip for now, I'll sign in later
    </a>
  </div></div>

  <script>
    const $ = (id) => document.getElementById(id);
    const setStatus = (msg, kind) => {{
      const el = $('status');
      el.textContent = msg || '';
      el.className = 'status' + (kind ? ' ' + kind : '');
    }};
    const disableAll = (yes) => {{
      ['btn-github','btn-google','btn-email','btn-send-otp','btn-verify-otp']
        .forEach(id => {{ const b = $(id); if (b) b.disabled = yes; }});
    }};

    function toggleEmail() {{
      const block = $('otp-block');
      block.classList.toggle('open');
      if (block.classList.contains('open')) $('email-input').focus();
    }}

    async function oauth(provider) {{
      disableAll(true);
      setStatus('Opening your browser to sign in with ' + provider + '…');
      try {{
        const res = await window.pywebview.api.start_oauth(provider);
        if (res && res.ok) {{
          setStatus('Signed in. Setting up your workspace…', 'success');
          // The Python side will swap the window when provisioning finishes.
        }} else {{
          setStatus((res && res.error) || 'Sign-in was cancelled.', 'error');
          disableAll(false);
        }}
      }} catch (e) {{
        setStatus('Sign-in failed: ' + e, 'error');
        disableAll(false);
      }}
    }}

    async function sendOtp() {{
      const email = ($('email-input').value || '').trim();
      if (!email.includes('@')) {{
        setStatus('Enter a valid email address.', 'error');
        return;
      }}
      disableAll(true);
      setStatus('Sending code to ' + email + '…');
      try {{
        const res = await window.pywebview.api.send_email_otp(email);
        if (res && res.ok) {{
          setStatus('Code sent. Check your inbox.', 'success');
          $('otp-input-block').style.display = 'flex';
          $('otp-input').focus();
          disableAll(false);
        }} else {{
          setStatus((res && res.error) || 'Could not send code.', 'error');
          disableAll(false);
        }}
      }} catch (e) {{
        setStatus('Error: ' + e, 'error');
        disableAll(false);
      }}
    }}

    async function verifyOtp() {{
      const email = ($('email-input').value || '').trim();
      const code = ($('otp-input').value || '').trim();
      if (code.length < 4) {{
        setStatus('Enter the 6-digit code from your email.', 'error');
        return;
      }}
      disableAll(true);
      setStatus('Verifying…');
      try {{
        const res = await window.pywebview.api.verify_email_otp(email, code);
        if (res && res.ok) {{
          setStatus('Signed in. Setting up your workspace…', 'success');
        }} else {{
          setStatus((res && res.error) || 'Invalid code.', 'error');
          disableAll(false);
        }}
      }} catch (e) {{
        setStatus('Error: ' + e, 'error');
        disableAll(false);
      }}
    }}

    function skipAuth() {{
      window.pywebview.api.skip_auth();
    }}
  </script>
</body></html>
"""


def render_bootstrap_carousel(*, assets_dir: Path, status: str = "Preparing runtime") -> str:
    """Carousel shown while the runtime venv provisions + clawmetry
    installs. Ubuntu-installer style: 4 auto-advancing slides, click
    on a CTA opens the URL in the system browser (via pywebview API)."""
    logo = _logo_data_uri(assets_dir)
    slides_json = json.dumps(CROSS_SELL_SLIDES)
    art_json = json.dumps(SLIDE_ART_SVG)
    safe_status = status.replace("<", "&lt;")

    return f"""<!doctype html>
<html><head>
  <meta charset="utf-8"/>
  <title>ClawMetry</title>
  <style>
    {_shared_css()}
    .center {{ align-items: stretch; padding: 0; flex-direction: column; }}
    .top-bar {{
      display: flex; align-items: center; justify-content: space-between;
      padding: 20px 28px; border-bottom: 1px solid var(--border);
    }}
    .top-bar img {{ height: 22px; width: auto; }}
    .top-bar .status {{
      color: var(--muted); font-size: 12px;
      display: flex; align-items: center; gap: 8px;
    }}
    .status-dot {{
      width: 8px; height: 8px; border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 12px {BRAND_RED}88;
      animation: pulse 1.4s ease-in-out infinite;
    }}
    @keyframes pulse {{
      0%, 100% {{ transform: scale(.8); opacity: .5 }}
      50% {{ transform: scale(1); opacity: 1 }}
    }}
    .carousel {{
      flex: 1; display: flex; align-items: center; justify-content: center;
      padding: 40px; overflow: hidden; position: relative;
    }}
    .slide {{
      max-width: 720px; text-align: center;
      position: absolute; padding: 0 20px;
      /* Inactive slides stay stacked underneath for the cross-fade but
         must not swallow clicks meant for the active slide's CTA
         (opacity:0 alone leaves them clickable). */
      opacity: 0; visibility: hidden; pointer-events: none;
      transition: opacity 500ms ease, visibility 0s linear 500ms;
    }}
    .slide.active {{
      opacity: 1; visibility: visible; pointer-events: auto;
      transition: opacity 500ms ease;
    }}
    /* Frameless vector illustration floating on the dark canvas — no
       gradient box, no border. The art carries its own chrome. */
    .slide-art {{
      width: 460px; max-width: 100%; margin: 0 auto 28px;
    }}
    .slide-art svg {{
      display: block; width: 100%; height: auto;
      filter: drop-shadow(0 18px 40px rgba(0,0,0,.45));
    }}
    .eyebrow {{
      font-size: 11px; font-weight: 700; letter-spacing: 0.12em;
      text-transform: uppercase; color: var(--accent);
      margin: 0 0 12px;
    }}
    .slide h2 {{
      font-size: 28px; font-weight: 700; letter-spacing: -0.01em;
      margin: 0 0 16px; line-height: 1.2;
    }}
    .slide p {{
      color: var(--muted); font-size: 15px; line-height: 1.6;
      margin: 0 0 24px;
    }}
    .slide-cta {{
      display: inline-block; padding: 10px 18px;
      background: var(--panel); border: 1px solid var(--border);
      border-radius: 8px; color: var(--text); font-weight: 600;
      font-size: 13px; cursor: pointer;
    }}
    .slide-cta:hover {{ background: #1a2130; text-decoration: none; }}
    .dots {{
      display: flex; justify-content: center; gap: 8px;
      padding: 20px 0 32px;
    }}
    .dot {{
      width: 6px; height: 6px; border-radius: 50%;
      background: var(--border); transition: background 200ms;
    }}
    .dot.active {{ background: var(--accent); }}
  </style>
</head><body>
  <div class="center">
    <div class="top-bar">
      {'<img src="' + logo + '" alt="ClawMetry"/>' if logo else '<div style="font-weight:700">ClawMetry</div>'}
      <div class="status"><span class="status-dot"></span><span id="status-text">{safe_status}</span></div>
    </div>
    <div class="carousel" id="carousel"></div>
    <div class="dots" id="dots"></div>
  </div>

  <script>
    const SLIDES = {slides_json};
    const ART = {art_json};
    let idx = 0;

    function render() {{
      const c = document.getElementById('carousel');
      c.innerHTML = SLIDES.map((s, i) => `
        <div class="slide ${{i === idx ? 'active' : ''}}" data-i="${{i}}">
          <div class="slide-art">${{ART[s.art] || ''}}</div>
          <div class="eyebrow">${{s.eyebrow}}</div>
          <h2>${{s.title}}</h2>
          <p>${{s.body}}</p>
          ${{s.cta_url ? `<a class="slide-cta" onclick="open_ext('${{s.cta_url}}')">${{s.cta_label}} →</a>` : ''}}
        </div>
      `).join('');
      const d = document.getElementById('dots');
      d.innerHTML = SLIDES.map((_, i) =>
        `<div class="dot ${{i === idx ? 'active' : ''}}" data-i="${{i}}" onclick="goto(${{i}})"></div>`
      ).join('');
    }}
    function goto(n) {{ idx = ((n % SLIDES.length) + SLIDES.length) % SLIDES.length; render(); }}
    function advance() {{ goto(idx + 1); }}

    function open_ext(url) {{
      try {{ window.pywebview.api.open_external(url); }}
      catch (e) {{ /* fallback: do nothing; the pane will close soon anyway */ }}
    }}

    // Expose update_status so Python can push progress into the top bar.
    window.set_status = (msg) => {{
      const el = document.getElementById('status-text');
      if (el) el.textContent = msg;
    }};

    render();
    setInterval(advance, 6500);
  </script>
</body></html>
"""


# ─── OAuth loopback (mirrors clawmetry.cli._oauth_browser_login) ────────
# Kept self-contained (stdlib only) so the desktop shell doesn't need
# the runtime venv to be primed before showing the auth pane. Same
# protocol as CLI: /api/oauth/<provider>/start?cli_port=<local_port> →
# cloud site → OAuth → cloud site redirects to
# http://127.0.0.1:<local_port>/?token=cm_...

def oauth_loopback_flow(
    provider: str,
    *,
    app_base: Optional[str] = None,
    open_browser: Callable[[str], None] = webbrowser.open,
    timeout_secs: float = OAUTH_LOOPBACK_TIMEOUT_SECS,
) -> tuple[bool, str]:
    """Run the OAuth loopback flow for GitHub/Google. Returns
    (ok, key_or_error_message). Blocking. Safe to call from any
    thread — starts + tears down its own HTTPServer."""
    base = (app_base or resolve_app_base()).rstrip("/")

    captured: dict = {}

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            token = (params.get("token") or [""])[0]
            captured["token"] = token
            ok = token.startswith("cm_")
            msg = ("You're connected. Return to the ClawMetry app."
                   if ok else "Sign-in failed. Return to the ClawMetry app and try email instead.")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                 "<title>ClawMetry</title></head>"
                 "<body style='font-family:-apple-system,sans-serif;background:#0b0e14;"
                 "color:#e2e8f0;display:flex;align-items:center;justify-content:center;"
                 "height:100vh;margin:0'>"
                 "<div style='text-align:center'><div style='font-size:40px'>\U0001f99e</div>"
                 f"<h2 style='font-weight:700'>{msg}</h2></div>"
                 "</body></html>").encode("utf-8")
            )

        def log_message(self, *args):  # silence stderr access log
            pass

    try:
        srv = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    except OSError as exc:
        return False, f"could not bind loopback socket ({exc})"

    try:
        port = srv.server_address[1]
        url = f"{base}/api/oauth/{provider}/start?cli_port={port}"
        try:
            open_browser(url)
        except Exception:
            # Browser open is best-effort; the user can still copy-paste
            # the URL. But without a UI to show it in the desktop pane,
            # bail rather than silently hang for 180s.
            srv.server_close()
            return False, f"could not open your browser (URL: {url})"

        srv.timeout = 1.0
        deadline = time.time() + timeout_secs
        while "token" not in captured and time.time() < deadline:
            srv.handle_request()
    finally:
        srv.server_close()

    tok = captured.get("token", "") or ""
    if tok.startswith("cm_"):
        return True, tok
    if not tok:
        return False, "sign-in timed out — no response from the browser"
    return False, "sign-in was declined by the identity provider"


# ─── Email OTP (mirrors /api/auth/email-otp in CLI) ─────────────────────

def _post_email_otp(
    action: str,
    payload: dict,
    *,
    app_base: Optional[str] = None,
    timeout: float = 15.0,
) -> tuple[bool, str, dict]:
    """POST to /api/auth/email-otp. Returns (ok, message, raw)."""
    base = (app_base or resolve_app_base()).rstrip("/")
    body = json.dumps({"action": action, **payload}).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/api/auth/email-otp",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        # 503 = rate limited (matches CLI's backoff path)
        try:
            raw = json.loads(e.read().decode("utf-8") or "{}")
        except Exception:
            raw = {}
        return False, (raw.get("error") or f"HTTP {e.code}"), raw
    except Exception as exc:
        return False, f"network error: {exc}", {}
    if not raw.get("ok", True):
        return False, (raw.get("error") or "email OTP failed"), raw
    return True, "", raw


def send_email_otp(email: str, *, app_base: Optional[str] = None) -> tuple[bool, str]:
    """Ask the server to send an OTP to ``email``."""
    if not email or "@" not in email:
        return False, "enter a valid email address"
    ok, msg, _ = _post_email_otp("send", {"email": email.strip()}, app_base=app_base)
    return ok, msg


def verify_email_otp(
    email: str,
    otp: str,
    *,
    app_base: Optional[str] = None,
) -> tuple[bool, str]:
    """Redeem an OTP for a ``cm_`` API key. Returns (ok, key_or_error)."""
    if not email or "@" not in email:
        return False, "enter a valid email address"
    if not otp or len(otp.strip()) < 4:
        return False, "enter the 6-digit code from your email"
    ok, msg, raw = _post_email_otp(
        "verify",
        {"email": email.strip(), "otp": otp.strip()},
        app_base=app_base,
    )
    if not ok:
        return False, msg
    key = (raw.get("api_key") or raw.get("key") or "").strip()
    if not key.startswith("cm_"):
        return False, "server did not return an API key — try again"
    return True, key


def render_ready_gate() -> str:
    """Spinner shown between "daemon is listening" and "dashboard has
    content". Doesn't self-navigate — Python drives that by polling
    /api/overview and calling ``window.load_url`` when ready (or 20s
    timeout). Doing the poll from Python avoids CORS: ``load_html``
    content has origin ``null``, and browsers block ``fetch`` from a
    null origin to ``http://127.0.0.1``. The daemon does not set
    ``Access-Control-Allow-Origin`` — no reason to; the real dashboard
    is same-origin. Keeping the ready-gate as a passive splash means
    we don't have to add CORS just for this."""
    return f"""<!doctype html>
<html><head>
  <meta charset="utf-8"/>
  <title>ClawMetry</title>
  <style>
    {_shared_css()}
    .msg {{ text-align: center; color: var(--muted); font-size: 13px; }}
    .spin {{
      width: 40px; height: 40px; margin: 0 auto 20px;
      border: 3px solid var(--border); border-top-color: var(--accent);
      border-radius: 50%;
      animation: spin 900ms linear infinite;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  </style>
</head><body>
  <div class="center">
    <div>
      <div class="spin"></div>
      <div class="msg">Loading your dashboard…</div>
    </div>
  </div>
</body></html>
"""


def wait_for_dashboard_content(
    port: int,
    *,
    deadline_secs: float = 20.0,
    poll_interval_secs: float = 0.5,
) -> bool:
    """Python-side companion to :func:`render_ready_gate`. Polls the
    daemon's ``/api/overview`` from the shell process. Returns True
    when the daemon returns content (sessions, detected runtimes, or
    the normal ok=True shape); False on timeout."""
    url = f"http://127.0.0.1:{port}/api/overview"
    deadline = time.time() + deadline_secs
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                if 200 <= resp.status < 300:
                    body = resp.read().decode("utf-8", errors="replace")
                    try:
                        data = json.loads(body) if body else {}
                    except Exception:
                        data = {}
                    if isinstance(data, dict) and (
                        (data.get("sessions") or [])
                        or (data.get("runtimes_detected") or [])
                        or data.get("ok") is True
                    ):
                        return True
        except Exception:
            pass
        time.sleep(poll_interval_secs)
    return False
