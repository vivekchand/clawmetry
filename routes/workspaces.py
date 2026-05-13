"""
routes/workspaces.py — Multi-profile OpenClaw workspace discovery + switcher.

Issue #950: power users keep multiple OpenClaw workspaces (work / personal /
experiments). This module exposes two endpoints:

  GET  /api/workspaces          — list discovered workspaces.
  POST /api/workspaces/active   — body {"name": str | "path": str}, switch
                                  the active workspace for this dashboard
                                  process. Mutates ``dashboard.WORKSPACE`` /
                                  ``SESSIONS_DIR`` / ``MEMORY_DIR`` / ``LOG_DIR``
                                  and re-initialises the DataProvider.

Discovery scans only paths under ``$HOME`` (or an explicit JSON-listed path),
does not follow symlinks, and never reads file contents outside the
``~/.clawmetry/workspaces.json`` config file.

Zero-config remains intact: when there is only one ``~/.openclaw``, the
endpoint just returns a one-element list and the UI shows no dropdown.
"""

import os
import json
from pathlib import Path

from flask import Blueprint, jsonify, request

bp_workspaces = Blueprint("workspaces", __name__)


def _list_workspaces():
    """Wrap clawmetry.sync.discover_workspaces with graceful fallback."""
    try:
        from clawmetry.sync import discover_workspaces

        return discover_workspaces()
    except Exception:
        # Never crash on bad input — fall back to whatever dashboard already has.
        try:
            import dashboard as _d

            ws = getattr(_d, "WORKSPACE", None)
            if ws and os.path.isdir(ws):
                return [
                    {
                        "name": "default",
                        "path": ws,
                        "agent_count": 0,
                        "last_active_ts": 0.0,
                    }
                ]
        except Exception:
            pass
        return []


@bp_workspaces.route("/api/workspaces")
def api_workspaces():
    """List all discovered OpenClaw workspace profiles.

    Response: ``{"workspaces": [{name, path, agent_count, last_active_ts}],
                 "active": "<path or null>"}``
    """
    import dashboard as _d

    workspaces = _list_workspaces()
    active = getattr(_d, "WORKSPACE", None)
    try:
        active_abs = str(Path(active).resolve(strict=False)) if active else None
    except (OSError, RuntimeError):
        active_abs = active
    return jsonify({"workspaces": workspaces, "active": active_abs})


def _persist_active(path: str) -> None:
    """Best-effort write of the chosen workspace to ~/.clawmetry/last_workspace.

    Survives dashboard restarts but failures are non-fatal (read-only FS, etc.)
    — the in-process switch still takes effect for this session.
    """
    try:
        cfg_dir = Path(os.path.expanduser("~/.clawmetry"))
        cfg_dir.mkdir(parents=True, exist_ok=True)
        (cfg_dir / "last_workspace").write_text(path + "\n")
    except (PermissionError, OSError):
        pass


@bp_workspaces.route("/api/workspaces/active", methods=["POST"])
def api_workspaces_set_active():
    """Switch the active workspace for the running dashboard.

    Body: ``{"name": "<profile-name>"}`` or ``{"path": "/abs/path"}``.
    """
    import dashboard as _d

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    path_arg = (body.get("path") or "").strip()

    workspaces = _list_workspaces()
    target = None
    if path_arg:
        try:
            wanted = str(Path(os.path.expanduser(path_arg)).resolve(strict=False))
        except (OSError, RuntimeError):
            wanted = path_arg
        for w in workspaces:
            if w.get("path") == wanted:
                target = w
                break
    if target is None and name:
        for w in workspaces:
            if w.get("name") == name:
                target = w
                break
    if target is None:
        return (
            jsonify(
                {
                    "error": "workspace not found",
                    "hint": "POST {name} or {path} matching /api/workspaces",
                }
            ),
            404,
        )

    new_ws = target["path"]
    if not os.path.isdir(new_ws):
        return jsonify({"error": "workspace path no longer exists"}), 410

    # Pick best matching sub-paths inside this workspace.
    sessions_candidates = [
        os.path.join(new_ws, "agents", "main", "sessions"),
        os.path.join(new_ws, "sessions"),
    ]
    # Also scan agents/* for the first one with a sessions/ dir.
    agents_base = os.path.join(new_ws, "agents")
    if os.path.isdir(agents_base):
        try:
            for agent in sorted(os.listdir(agents_base)):
                sd = os.path.join(agents_base, agent, "sessions")
                if sd not in sessions_candidates:
                    sessions_candidates.append(sd)
        except OSError:
            pass
    sessions_dir = next(
        (d for d in sessions_candidates if os.path.isdir(d)),
        sessions_candidates[0],
    )

    log_candidates = [
        os.path.join(new_ws, "logs"),
        os.path.join(new_ws, "log"),
    ]
    log_dir = next(
        (d for d in log_candidates if os.path.isdir(d)),
        getattr(_d, "LOG_DIR", log_candidates[0]),
    )

    memory_dir = os.path.join(new_ws, "memory")

    # Mutate module globals so all late `import dashboard as _d` helpers see
    # the new values. Read-only routes pick this up on the next request.
    _d.WORKSPACE = new_ws
    _d.SESSIONS_DIR = sessions_dir
    _d.MEMORY_DIR = memory_dir
    _d.LOG_DIR = log_dir

    # Re-init the data provider so DuckDB / LocalDataProvider sees the new dir.
    init_fn = getattr(_d, "_init_data_provider", None)
    if callable(init_fn):
        try:
            init_fn()
        except Exception:
            pass

    _persist_active(new_ws)

    return jsonify(
        {
            "ok": True,
            "active": new_ws,
            "name": target.get("name"),
            "sessions_dir": sessions_dir,
            "memory_dir": memory_dir,
            "log_dir": log_dir,
        }
    )
