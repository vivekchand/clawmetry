"""
routes/selfconfig.py — Self-configuration diff viewer endpoints.

Tracks agent-managed identity/values/config files and provides a git-like
history of edits. Files monitored:

  USER.md     — user profile
  SOUL.md     — agent temperament and values  *** values drift alert ***
  AGENTS.md   — how to "be" an agent
  TOOLS.md    — tooling idiosyncrasies
  IDENTITY.md — agent identity
  MEMORY.md   — memory index

Snapshots are stored in ~/.clawmetry/selfconfig_history/<filename>/v<timestamp>.md.
A small index file ~/.clawmetry/selfconfig_history/index.json tracks hashes and
metadata so we can detect changes cheaply without reading every stored file.

Endpoints:

  GET /api/selfconfig                             — list tracked files + state
  GET /api/selfconfig/<filename>                  — revision history for a file
  GET /api/selfconfig/<filename>/diff             — unified diff between two versions
  GET /api/selfconfig/<filename>/content          — raw content of one version

Blueprint: bp_selfconfig
"""
import difflib
import hashlib
import json
import logging
import os
import time

from flask import Blueprint, jsonify, request

log = logging.getLogger(__name__)

bp_selfconfig = Blueprint("selfconfig", __name__)

# Files we track — order matters (displayed in this order in the UI).
_TRACKED_FILES = [
    "USER.md",
    "SOUL.md",
    "AGENTS.md",
    "TOOLS.md",
    "IDENTITY.md",
    "MEMORY.md",
]

# Only SOUL.md gets the values-drift highlight.
_VALUES_FILES = {"SOUL.md"}

# Re-run threshold: skip snapshot scan if last run was less than 60 s ago.
_SNAPSHOT_INTERVAL = 60

# Cap file reads at 500 KB to keep diff computation fast.
_MAX_FILE_BYTES = 500 * 1024


# ── Internal helpers ──────────────────────────────────────────────────────────


def _history_root() -> str:
    """Return (and create) the selfconfig history storage directory."""
    path = os.path.expanduser("~/.clawmetry/selfconfig_history")
    os.makedirs(path, exist_ok=True)
    return path


def _index_path() -> str:
    return os.path.join(_history_root(), "index.json")


def _load_index() -> dict:
    """Load the index.json file; return empty dict on any error."""
    try:
        with open(_index_path(), "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save_index(index: dict) -> None:
    try:
        with open(_index_path(), "w", encoding="utf-8") as fh:
            json.dump(index, fh)
    except Exception as exc:
        log.warning("selfconfig: failed to save index: %s", exc)


def _file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _versioned_path(filename: str, ts: int) -> str:
    """Return the path for a versioned snapshot file."""
    file_dir = os.path.join(_history_root(), filename)
    os.makedirs(file_dir, exist_ok=True)
    return os.path.join(file_dir, f"v{ts}.md")


def _locate_file(filename):
    """
    Find a tracked file on disk.  Checks:
      1. WORKSPACE root
      2. WORKSPACE/.openclaw/
      3. ~/.openclaw/
    Returns the first path that exists, or None.
    """
    try:
        import dashboard as _d
        workspace = getattr(_d, "WORKSPACE", None)
    except Exception:
        workspace = None

    candidates = []
    if workspace:
        candidates.append(os.path.join(workspace, filename))
        candidates.append(os.path.join(workspace, ".openclaw", filename))
    candidates.append(os.path.expanduser(os.path.join("~/.openclaw", filename)))

    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _read_file_safe(path):
    """
    Read a file, capped at _MAX_FILE_BYTES.
    Returns (content_bytes, truncated).
    """
    try:
        size = os.path.getsize(path)
        truncated = size > _MAX_FILE_BYTES
        with open(path, "rb") as fh:
            data = fh.read(_MAX_FILE_BYTES)
        return data, truncated
    except Exception as exc:
        log.warning("selfconfig: cannot read %s: %s", path, exc)
        return b"", False


def _snapshot_if_changed() -> None:
    """
    Walk tracked files; save a new versioned snapshot whenever the content
    hash has changed since the last snapshot.  Skips if called within the
    last _SNAPSHOT_INTERVAL seconds (cheap lazy polling).
    """
    index = _load_index()
    now = int(time.time())

    last_run = index.get("_last_run_ts", 0)
    if now - last_run < _SNAPSHOT_INTERVAL:
        return

    index["_last_run_ts"] = now

    for filename in _TRACKED_FILES:
        path = _locate_file(filename)
        if path is None:
            continue

        content, _truncated = _read_file_safe(path)
        if not content:
            continue

        new_hash = _file_hash(content)
        file_meta = index.get(filename, {})
        last_hash = file_meta.get("last_hash")

        if new_hash != last_hash:
            ts = now
            versioned = _versioned_path(filename, ts)
            try:
                with open(versioned, "wb") as fh:
                    fh.write(content)
            except Exception as exc:
                log.warning("selfconfig: cannot write snapshot %s: %s", versioned, exc)
                continue

            revisions = file_meta.get("revisions", [])
            revisions.append({"ts": ts, "hash": new_hash, "size": len(content)})
            index[filename] = {
                "last_hash": new_hash,
                "last_modified_ts": int(os.path.getmtime(path)),
                "revisions": revisions,
            }

    _save_index(index)


def _revision_list(filename: str, index: dict) -> list:
    """Return revisions list for a filename, newest-first."""
    meta = index.get(filename, {})
    revisions = meta.get("revisions", [])
    return list(reversed(revisions))


# ── API endpoints ─────────────────────────────────────────────────────────────


@bp_selfconfig.route("/api/selfconfig")
def api_selfconfig_list():
    """List all tracked files with their current state and revision counts."""
    try:
        _snapshot_if_changed()
    except Exception as exc:
        log.warning("selfconfig: snapshot error: %s", exc)

    index = _load_index()
    files = []

    for filename in _TRACKED_FILES:
        path = _locate_file(filename)
        meta = index.get(filename, {})
        revisions = meta.get("revisions", [])
        exists = path is not None

        last_edit_delta = 0
        if len(revisions) >= 2:
            prev_size = revisions[-2]["size"]
            curr_size = revisions[-1]["size"]
            last_edit_delta = curr_size - prev_size
        elif len(revisions) == 1:
            last_edit_delta = revisions[0]["size"]

        size = 0
        if path is not None:
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
        files.append({
            "name": filename,
            "tracked": True,
            "exists": exists,
            "current_hash": meta.get("last_hash", ""),
            "last_modified_ts": meta.get("last_modified_ts", 0),
            "revision_count": len(revisions),
            "last_edit_delta_chars": last_edit_delta,
            "size": size,
            "is_values_file": filename in _VALUES_FILES,
        })

    return jsonify({
        "files": files,
        "storage_path": "~/.clawmetry/selfconfig_history",
    })


@bp_selfconfig.route("/api/selfconfig/<filename>")
def api_selfconfig_file(filename):
    """Return revision history for a specific tracked file."""
    if filename not in _TRACKED_FILES:
        return jsonify({"error": f"Unknown file: {filename}"}), 404

    try:
        _snapshot_if_changed()
    except Exception as exc:
        log.warning("selfconfig: snapshot error: %s", exc)

    index = _load_index()
    revisions_raw = _revision_list(filename, index)

    revisions = []
    for rev in revisions_raw:
        ts = rev["ts"]
        version_path = _versioned_path(filename, ts)
        revisions.append({
            "ts": ts,
            "hash": rev.get("hash", ""),
            "size": rev.get("size", 0),
            "version_path": version_path,
        })

    return jsonify({
        "name": filename,
        "is_values_file": filename in _VALUES_FILES,
        "revisions": revisions,
    })


@bp_selfconfig.route("/api/selfconfig/<filename>/diff")
def api_selfconfig_diff(filename):
    """
    Return a structured unified diff between two snapshots.

    Query params:
      from=<ts_a>  — older revision timestamp
      to=<ts_b>    — newer revision timestamp
    """
    if filename not in _TRACKED_FILES:
        return jsonify({"error": f"Unknown file: {filename}"}), 404

    from_ts_str = request.args.get("from", "")
    to_ts_str = request.args.get("to", "")

    if not from_ts_str or not to_ts_str:
        return jsonify({"error": "Both 'from' and 'to' query params are required"}), 400

    try:
        from_ts = int(from_ts_str)
        to_ts = int(to_ts_str)
    except ValueError:
        return jsonify({"error": "'from' and 'to' must be integer timestamps"}), 400

    def _read_version(ts):
        path = _versioned_path(filename, ts)
        if not os.path.isfile(path):
            return "", False
        data, truncated = _read_file_safe(path)
        return data.decode("utf-8", errors="replace"), truncated

    from_content, from_truncated = _read_version(from_ts)
    to_content, to_truncated = _read_version(to_ts)
    truncated = from_truncated or to_truncated

    from_lines = from_content.splitlines(keepends=True)
    to_lines = to_content.splitlines(keepends=True)

    raw_diff = list(difflib.unified_diff(
        from_lines,
        to_lines,
        fromfile=f"{filename}@{from_ts}",
        tofile=f"{filename}@{to_ts}",
        lineterm="",
    ))

    diff_lines = []
    added_chars = 0
    removed_chars = 0
    added_lines_count = 0
    removed_lines_count = 0
    added_raw = []  # text of added lines, for summarization
    removed_raw = []

    for line in raw_diff:
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            diff_lines.append({"type": "meta", "text": line})
        elif line.startswith("+"):
            text = line[1:]
            added_chars += len(text)
            added_lines_count += 1
            added_raw.append(text)
            diff_lines.append({"type": "added", "text": "+ " + text})
        elif line.startswith("-"):
            text = line[1:]
            removed_chars += len(text)
            removed_lines_count += 1
            removed_raw.append(text)
            diff_lines.append({"type": "removed", "text": "- " + text})
        else:
            diff_lines.append({"type": "context", "text": line})

    summary = _summarize_change(added_raw, removed_raw)

    return jsonify({
        "name": filename,
        "from_ts": from_ts,
        "to_ts": to_ts,
        "diff_lines": diff_lines,
        "added_chars": added_chars,
        "removed_chars": removed_chars,
        "added_lines": added_lines_count,
        "removed_lines": removed_lines_count,
        "summary": summary,
        "truncated": truncated,
    })


def _summarize_change(added_raw, removed_raw):
    """
    Generate a 1-line plain-English summary of a change.

    Heuristics:
      * If the change adds/edits markdown fields (``- **Name:** …``), list the
        field names.
      * If lines are mostly additions under a ``## Heading``, mention the
        heading ("added notes under Context").
      * If the change is a pure deletion, say "Removed ...".
      * Fall back to a small/large change descriptor so the UI never shows
        raw byte counts.
    """
    import re

    def _extract_field_names(lines):
        names = []
        for line in lines:
            m = re.match(r"\s*[-*]\s*\*\*([^*]+?)[:\*]", line)
            if m:
                nm = m.group(1).strip().rstrip(":").strip()
                if nm and nm not in names:
                    names.append(nm)
        return names

    def _extract_headings(lines):
        heads = []
        for line in lines:
            m = re.match(r"\s*#{1,6}\s+(.+?)\s*$", line)
            if m:
                h = m.group(1).strip()
                if h and h not in heads:
                    heads.append(h)
        return heads

    added_fields = _extract_field_names(added_raw)
    removed_fields = _extract_field_names(removed_raw)
    common_fields = [f for f in added_fields if f in removed_fields]
    only_added = [f for f in added_fields if f not in common_fields]
    only_removed = [f for f in removed_fields if f not in common_fields]

    if common_fields and not only_added and not only_removed:
        parts = common_fields[:3]
        suffix = (", and " + str(len(common_fields) - 3) + " more") if len(common_fields) > 3 else ""
        return "Updated " + ", ".join(parts) + suffix
    if only_added and not only_removed and not common_fields:
        parts = only_added[:3]
        suffix = (", and " + str(len(only_added) - 3) + " more") if len(only_added) > 3 else ""
        return "Added " + ", ".join(parts) + suffix
    if common_fields or only_added:
        fields = (common_fields + only_added)[:3]
        suffix = (" and more") if len(common_fields + only_added) > 3 else ""
        return "Edited " + ", ".join(fields) + suffix

    added_headings = _extract_headings(added_raw)
    if added_headings:
        return "Added a '" + added_headings[0] + "' section"

    # Plain-prose change with no obvious structure.
    total = len(added_raw) + len(removed_raw)
    if len(added_raw) > 0 and len(removed_raw) == 0:
        return "Added new notes"
    if len(removed_raw) > 0 and len(added_raw) == 0:
        return "Removed some content"
    if total <= 4:
        return "Small tweak"
    if total <= 20:
        return "Reworded a paragraph"
    return "Substantial rewrite"


@bp_selfconfig.route("/api/selfconfig/<filename>/content", methods=["POST", "PUT"])
def api_selfconfig_content_write(filename):
    """
    Write content back to the tracked file on disk.

    Body: {"content": "...markdown..."}

    After writing, runs ``_snapshot_if_changed`` so the new version is
    recorded in the revision history.
    """
    if filename not in _TRACKED_FILES:
        return jsonify({"error": f"Unknown file: {filename}"}), 404

    body = request.get_json(silent=True) or {}
    new_content = body.get("content")
    if new_content is None or not isinstance(new_content, str):
        return jsonify({"error": "'content' field (string) is required"}), 400

    # Respect the 500 KB read cap on writes too.
    if len(new_content.encode("utf-8")) > _MAX_FILE_BYTES:
        return jsonify({"error": f"File too large (>{_MAX_FILE_BYTES} bytes)"}), 413

    # Locate where the file should go. Prefer existing location; fall back to
    # WORKSPACE root if the file doesn't exist yet.
    path = _locate_file(filename)
    if path is None:
        try:
            import dashboard as _d
            workspace = getattr(_d, "WORKSPACE", None)
        except Exception:
            workspace = None
        if workspace and os.path.isdir(os.path.join(workspace, "workspace")):
            path = os.path.join(workspace, "workspace", filename)
        elif workspace:
            path = os.path.join(workspace, filename)
        else:
            path = os.path.expanduser(os.path.join("~/.openclaw/workspace", filename))

    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_content)
    except Exception as exc:
        log.warning("selfconfig: failed to write %s: %s", path, exc)
        return jsonify({"error": f"Failed to write file: {exc}"}), 500

    # Force a fresh snapshot so the new version is recorded immediately.
    index = _load_index()
    index["_last_run_ts"] = 0
    _save_index(index)
    try:
        _snapshot_if_changed()
    except Exception as exc:
        log.warning("selfconfig: snapshot after write failed: %s", exc)

    return jsonify({
        "ok": True,
        "name": filename,
        "path": path,
        "size": len(new_content.encode("utf-8")),
    })


@bp_selfconfig.route("/api/selfconfig/<filename>/content", methods=["GET"])
def api_selfconfig_content(filename):
    """Return the content of a version, or the live file if ``ts`` is omitted."""
    if filename not in _TRACKED_FILES:
        return jsonify({"error": f"Unknown file: {filename}"}), 404

    ts_str = request.args.get("ts", "")

    if not ts_str:
        # No ts => return the live file on disk (the "current" version).
        path = _locate_file(filename)
        if path is None:
            return jsonify({
                "name": filename,
                "ts": None,
                "content": "",
                "truncated": False,
                "exists": False,
                "is_values_file": filename in _VALUES_FILES,
            })
        data, truncated = _read_file_safe(path)
        return jsonify({
            "name": filename,
            "ts": int(os.path.getmtime(path)),
            "content": data.decode("utf-8", errors="replace"),
            "truncated": truncated,
            "exists": True,
            "is_values_file": filename in _VALUES_FILES,
        })

    try:
        ts = int(ts_str)
    except ValueError:
        return jsonify({"error": "'ts' must be an integer timestamp"}), 400

    path = _versioned_path(filename, ts)
    if not os.path.isfile(path):
        return jsonify({"error": f"Version {ts} not found for {filename}"}), 404

    data, truncated = _read_file_safe(path)
    content = data.decode("utf-8", errors="replace")

    return jsonify({
        "name": filename,
        "ts": ts,
        "content": content,
        "truncated": truncated,
        "exists": True,
        "is_values_file": filename in _VALUES_FILES,
    })
