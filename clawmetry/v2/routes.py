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
import os
from flask import Blueprint, send_from_directory, abort

# `static_folder` is resolved relative to this file. After `npm run build`
# in `frontend/`, the bundle lives at `clawmetry/static/v2/dist/`.
_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "v2", "dist")
_ASSETS_DIR = os.path.join(_DIST_DIR, "assets")

# static_url_path is narrowed to `/v2/assets` so Flask's static dispatcher
# only handles real hashed asset URLs (Vite emits everything under
# `/v2/assets/*`). Earlier this was mounted at `/v2`, which preempted the
# SPA catch-all and 404'd every client-side route like `/v2/trace`.
bp_v2 = Blueprint(
    "v2",
    __name__,
    static_folder=_ASSETS_DIR,
    static_url_path="/v2/assets",
)


def _serve_index():
    """Serve the SPA entry point. Returns 503 with a helpful message if the
    React bundle hasn't been built yet (devs running from source without
    having executed `npm run build`)."""
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


@bp_v2.route("/v2")
@bp_v2.route("/v2/")
def v2_root():
    return _serve_index()


@bp_v2.route("/v2/<path:path>")
def v2_catchall(path: str):
    """SPA catch-all. Real asset files (assets/*.js, *.css, *.png) are served
    by the static_folder dispatcher BEFORE this view runs; this view only
    fires for client-side router paths like `/v2/trace` or `/v2/brain`."""
    # If a file exists on disk for this path, serve it (defence-in-depth;
    # Flask's static dispatch should normally handle this first).
    asset_path = os.path.join(_DIST_DIR, path)
    if os.path.isfile(asset_path):
        return send_from_directory(_DIST_DIR, path)
    # Otherwise fall through to the SPA shell so the React router can match.
    # Refuse path-escapes for safety.
    if ".." in path.split("/"):
        abort(404)
    return _serve_index()
