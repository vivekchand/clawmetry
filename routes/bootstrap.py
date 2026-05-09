"""
routes/bootstrap.py — Bootstrap.md archive endpoint (#690).

OpenClaw runs BOOTSTRAP.md once at first startup to negotiate agent identity,
then the agent self-deletes it ("you're you now").  ClawMetry captures it on
first sight and persists a snapshot so it survives the deletion.

Endpoint:

  GET /api/bootstrap  — return the archived first-contact artifact:
    {
      "status":       "live" | "archived" | "not_found",
      "bootstrap_md": "<raw markdown content>" | null,
      "captured_at":  <unix float> | null,
      "first_session": {
        "session_id":    str,
        "created_at":    <unix float>,
        "preview_lines": [str, ...]   # first 3 assistant text blocks
      } | null
    }

Snapshot is stored at ~/.clawmetry/bootstrap_snapshot.json.

Shared helpers (``SESSIONS_DIR``, ``WORKSPACE``) stay in ``dashboard.py`` and
are reached via late ``import dashboard as _d`` to avoid circular imports.
"""

import json
import os
import time

from flask import Blueprint, jsonify

bp_bootstrap = Blueprint("bootstrap", __name__)

_SNAPSHOT_FILENAME = "bootstrap_snapshot.json"


def _clawmetry_dir() -> str:
    path = os.path.expanduser("~/.clawmetry")
    os.makedirs(path, exist_ok=True)
    return path


def _snapshot_path() -> str:
    return os.path.join(_clawmetry_dir(), _SNAPSHOT_FILENAME)


def _find_live_bootstrap():
    """Return absolute path of BOOTSTRAP.md if it exists, else None."""
    try:
        import dashboard as _d
        workspace = getattr(_d, "WORKSPACE", None)
    except Exception:
        workspace = None

    candidates = []
    if workspace:
        candidates.append(os.path.join(workspace, "BOOTSTRAP.md"))
        candidates.append(os.path.join(workspace, ".openclaw", "BOOTSTRAP.md"))
    candidates.append(os.path.expanduser("~/.openclaw/BOOTSTRAP.md"))
    candidates.append(os.path.expanduser("~/.clawdbot/BOOTSTRAP.md"))

    return next((p for p in candidates if os.path.isfile(p)), None)


def _load_snapshot():
    """Return previously stored snapshot dict, or None."""
    try:
        with open(_snapshot_path(), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _save_snapshot(content: str) -> float:
    """Persist BOOTSTRAP.md content; return captured_at timestamp."""
    captured_at = time.time()
    data = {"bootstrap_md": content, "captured_at": captured_at}
    try:
        with open(_snapshot_path(), "w", encoding="utf-8") as fh:
            json.dump(data, fh)
    except Exception:
        pass
    return captured_at


def _find_first_session():
    """Return a compact summary of the earliest session JSONL file."""
    try:
        import dashboard as _d
        sessions_dir = getattr(_d, "SESSIONS_DIR", None) or os.path.expanduser(
            "~/.openclaw/agents/main/sessions"
        )
    except Exception:
        sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")

    if not os.path.isdir(sessions_dir):
        return None

    try:
        files = [
            f for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl")
            and ".deleted." not in f
            and ".reset." not in f
        ]
    except OSError:
        return None

    if not files:
        return None

    # Oldest file by mtime = first-contact session
    oldest_path = None
    oldest_mtime = float("inf")
    for fname in files:
        fpath = os.path.join(sessions_dir, fname)
        try:
            mt = os.stat(fpath).st_mtime
            if mt < oldest_mtime:
                oldest_mtime = mt
                oldest_path = fpath
                oldest_fname = fname
        except OSError:
            continue

    if not oldest_path:
        return None

    session_id = oldest_fname.removesuffix(".jsonl")
    preview = []
    try:
        with open(oldest_path, "r", errors="replace") as fh:
            for raw in fh:
                if len(preview) >= 3:
                    break
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    ev = json.loads(raw)
                except Exception:
                    continue
                msg = ev.get("message") or {}
                if msg.get("role") != "assistant":
                    continue
                content = msg.get("content") or []
                text = ""
                for blk in (content if isinstance(content, list) else []):
                    if isinstance(blk, dict) and blk.get("type") == "text":
                        text += blk.get("text", "")
                    elif isinstance(blk, str):
                        text += blk
                text = text.strip()
                if text:
                    preview.append(text[:300])
    except Exception:
        pass

    return {
        "session_id": session_id,
        "created_at": oldest_mtime,
        "preview_lines": preview,
    }


@bp_bootstrap.route("/api/bootstrap")
def api_bootstrap():
    """Return the Bootstrap.md first-contact archive.

    On each call we check whether BOOTSTRAP.md is still live.  If it is, we
    snapshot it immediately (so it survives self-deletion) and return
    status='live'.  If it's already gone but we snapshotted it previously,
    we return status='archived'.  Otherwise status='not_found'.
    """
    live_path = _find_live_bootstrap()

    if live_path:
        try:
            with open(live_path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except Exception:
            content = ""

        existing = _load_snapshot()
        if existing is None:
            captured_at = _save_snapshot(content)
        else:
            captured_at = existing.get("captured_at", time.time())

        return jsonify({
            "status": "live",
            "bootstrap_md": content,
            "captured_at": captured_at,
            "first_session": _find_first_session(),
        })

    snapshot = _load_snapshot()
    if snapshot:
        return jsonify({
            "status": "archived",
            "bootstrap_md": snapshot.get("bootstrap_md"),
            "captured_at": snapshot.get("captured_at"),
            "first_session": _find_first_session(),
        })

    return jsonify({
        "status": "not_found",
        "bootstrap_md": None,
        "captured_at": None,
        "first_session": _find_first_session(),
    })
