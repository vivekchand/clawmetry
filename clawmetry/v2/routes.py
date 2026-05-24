"""ClawMetry v2 Flask blueprint.

Serves the pre-built React SPA from `clawmetry/static/v2/dist/` at `/v2`.
Opt-in: `dashboard.py` only registers this blueprint when env var
`CLAWMETRY_V2=1` is set (or the user passed `--v2` to the CLI). When the
flag is off, the blueprint is never registered, so `/v2` 404s and the v1
dashboard is unchanged — matches the "parallel rails" plan in the design
handoff README.

SPA routing: `/v2` and `/v2/<anything>` both serve `index.html`; the
React BrowserRouter (basename="/v2") handles client-side navigation.
Hashed JS/CSS asset URLs like `/v2/assets/index-xyz.js` are caught by
Flask's static_folder dispatch automatically.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from flask import Blueprint, send_from_directory, abort, jsonify, request

_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "v2", "dist")
_ASSETS_DIR = os.path.join(_DIST_DIR, "assets")

_PREFS_DIR = Path.home() / ".clawmetry"
_PREFS_FILE = _PREFS_DIR / "preferences.json"

_VALID_THEMES = {"light", "mid", "dark"}
_VALID_DENSITIES = {"compact", "regular", "comfy"}
_DEFAULT_PREFS = {"theme": "light", "density": "regular"}

bp_v2 = Blueprint(
    "v2",
    __name__,
    static_folder=_ASSETS_DIR,
    static_url_path="/v2/assets",
)


def _read_prefs() -> dict:
    try:
        if _PREFS_FILE.is_file():
            with open(_PREFS_FILE) as f:
                stored = json.load(f)
            return {
                "theme": stored.get("theme", "light") if stored.get("theme") in _VALID_THEMES else "light",
                "density": stored.get("density", "regular") if stored.get("density") in _VALID_DENSITIES else "regular",
            }
    except (json.JSONDecodeError, OSError):
        pass
    return dict(_DEFAULT_PREFS)


def _write_prefs(prefs: dict) -> None:
    _PREFS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _PREFS_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(prefs, f, indent=2)
    tmp.rename(_PREFS_FILE)


def _serve_index():
    """Serve the SPA entry point."""
    index_path = os.path.join(_DIST_DIR, "index.html")
    if not os.path.isfile(index_path):
        return (
            "<h1>ClawMetry v2 bundle missing</h1>"
            "<p>Run <code>cd frontend && npm install && npm run build</code> "
            "to produce the static bundle at "
            f"<code>{os.path.normpath(_DIST_DIR)}</code>.</p>",
            503,
            {"Content-Type": "text/html; charset=utf-8"},
        )
    return send_from_directory(_DIST_DIR, "index.html")


# ── Preferences API ──────────────────────────────────────────────────────

@bp_v2.route("/api/v2/preferences", methods=["GET"])
def get_preferences():
    return jsonify(_read_prefs())


@bp_v2.route("/api/v2/preferences", methods=["POST"])
def set_preferences():
    body = request.get_json(silent=True) or {}
    prefs = _read_prefs()
    if "theme" in body and body["theme"] in _VALID_THEMES:
        prefs["theme"] = body["theme"]
    if "density" in body and body["density"] in _VALID_DENSITIES:
        prefs["density"] = body["density"]
    _write_prefs(prefs)
    return jsonify(prefs)


# ── SPA serving ──────────────────────────────────────────────────────────

@bp_v2.route("/v2")
@bp_v2.route("/v2/")
def v2_root():
    return _serve_index()


@bp_v2.route("/v2/<path:path>")
def v2_catchall(path: str):
    asset_path = os.path.join(_DIST_DIR, path)
    if os.path.isfile(asset_path):
        return send_from_directory(_DIST_DIR, path)
    if ".." in path.split("/"):
        abort(404)
    return _serve_index()