"""ClawMetry v2 Flask blueprint.

Serves the pre-built React SPA from `clawmetry/static/v2/dist/` at `/v2`
(default) or at `/` when ``CLAWMETRY_V2_DEFAULT=1`` (``clawmetry --v2-default``).

Opt-in: `dashboard.py` only registers this blueprint when env var
`CLAWMETRY_V2=1` is set (or the user passed `--v2` / `--v2-default` to the
CLI). When the flag is off, the blueprint is never registered, so `/v2` 404s
and the v1 dashboard is unchanged — matches the "parallel rails" plan in the
design handoff README.

SPA routing: the root and all sub-paths serve `index.html`; the React
BrowserRouter handles client-side navigation. Hashed JS/CSS asset URLs are
caught by Flask's static_folder dispatch automatically.

Mode A (default): `/v2`, `/v2/`, `/v2/<path>` serve the SPA; assets at
``/v2/assets/*`` (Vite ``base: "/v2/"``).

Mode B (--v2-default): `/`, `/<path>` serve the SPA; assets at ``/assets/*``
(Vite ``base: "/"``). The v1 dashboard moves to ``/v1/``.
"""

from __future__ import annotations
import os
from flask import Blueprint, send_from_directory, abort

# `static_folder` is resolved relative to this file. After `npm run build`
# in `frontend/`, the bundle lives at `clawmetry/static/v2/dist/`.
_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "v2", "dist")
_ASSETS_DIR = os.path.join(_DIST_DIR, "assets")

# Read the env var at import time (cli.py sets it before dashboard.py is
# imported, so the value is already available when Flask evaluates the routes).
_v2_default = os.environ.get("CLAWMETRY_V2_DEFAULT") == "1"

# static_url_path mirrors the Vite `base` config: "/assets" when v2 is at the
# root, "/v2/assets" when v2 is at /v2. This only matters once a bundle is
# built; the "missing bundle" 503 path is unaffected.
_static_url = "/assets" if _v2_default else "/v2/assets"

bp_v2 = Blueprint(
    "v2",
    __name__,
    static_folder=_ASSETS_DIR,
    static_url_path=_static_url,
)


def _serve_index():
    """Serve the SPA entry point. Returns 503 with a helpful message if the
    React bundle hasn't been built yet (devs running from source without
    having executed `npm run build`)."""
    index_path = os.path.join(_DIST_DIR, "index.html")
    if not os.path.isfile(index_path):
        base = "/" if _v2_default else "/v2/"
        return (
            "<h1>ClawMetry v2 bundle missing</h1>"
            "<p>Run <code>cd frontend && npm install && npm run build</code> "
            "to produce the static bundle at "
            f"<code>{os.path.normpath(_DIST_DIR)}</code>.</p>"
            f"<p>Build with <code>VITE_BASE={base}</code> when running in "
            f"{'root' if _v2_default else '/v2'} mode.</p>",
            503,
            {"Content-Type": "text/html; charset=utf-8"},
        )
    return send_from_directory(_DIST_DIR, "index.html")


def _catchall(path: str = ""):
    """SPA catch-all. Real asset files are served by the static_folder
    dispatcher BEFORE this view runs; this view only fires for client-side
    router paths like `/v2/trace` or (in default mode) `/trace`."""
    if path:
        asset_path = os.path.join(_DIST_DIR, path)
        if os.path.isfile(asset_path):
            return send_from_directory(_DIST_DIR, path)
        if ".." in path.split("/"):
            abort(404)
    return _serve_index()


if _v2_default:
    # Mode B: v2 owns the root. v1 moves to /v1/ (see routes/meta.py).
    bp_v2.add_url_rule("/", "v2_root", _catchall)
    bp_v2.add_url_rule("/<path:path>", "v2_catchall", _catchall)
else:
    # Mode A: v2 lives at /v2, v1 stays at /.
    bp_v2.add_url_rule("/v2", "v2_root", _serve_index)
    bp_v2.add_url_rule("/v2/", "v2_root_slash", _serve_index)
    bp_v2.add_url_rule("/v2/<path:path>", "v2_catchall", _catchall)
