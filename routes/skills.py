"""
routes/skills.py — Skills fidelity telemetry endpoints (GH #687).

Tracks how OpenClaw skills are used across the 3 fidelity levels:
  - Header: always loaded in system context (~3-4 lines from SKILL.md)
  - Body:   fetched on-demand when agent finds skill relevant (remainder of SKILL.md)
  - Linked Files: additional files under the skill directory, fetched when acting

Exposes:
  GET /api/skills       — list all installed skills with fidelity stats
  GET /api/skills/<name> — detail for one skill (usage over last 7d)

Blueprints: bp_skills
"""

import json
import os
import time

from flask import Blueprint, jsonify

bp_skills = Blueprint("skills", __name__)

# Subdirectory names that count as linked-file directories
_LINKED_DIRS = frozenset({"scripts", "references", "assets"})


def _get_skills_dir():
    """Return the skills directory, trying common locations."""
    import dashboard as _d

    workspace = _d.WORKSPACE or ""

    # If WORKSPACE already points at ~/.openclaw (contains agents/ memory/ etc.)
    # then skills are at WORKSPACE/skills
    candidates = [
        os.path.join(workspace, "skills") if workspace else None,
        os.path.expanduser("~/.openclaw/skills"),
        os.path.expanduser("~/.clawdbot/skills"),
    ]
    for c in candidates:
        if c and os.path.isdir(c):
            return c
    # Return first non-None candidate as a best guess (may not exist)
    return next((c for c in candidates if c), os.path.expanduser("~/.openclaw/skills"))


def _parse_skill_md(skill_md_path):
    """Parse a SKILL.md file and return (header_text, description).

    The frontmatter block is between the first pair of ``---`` lines.
    ``header_text`` is the frontmatter + the first few lines of body
    (the "header" that the agent always loads), which we approximate as
    everything up to and including the closing ``---`` line plus the first
    non-blank body line.
    """
    try:
        with open(skill_md_path, "r", errors="replace") as fh:
            content = fh.read()
    except OSError:
        return "", ""

    lines = content.splitlines()
    description = ""
    frontmatter_end = -1

    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                frontmatter_end = i
                break
            if line.startswith("description:"):
                description = line[len("description:"):].strip()

    # Header text: frontmatter block (lines 0..frontmatter_end inclusive)
    # plus first non-blank line of body — this is what OpenClaw keeps in context.
    if frontmatter_end >= 0:
        header_lines = lines[: frontmatter_end + 1]
        # Append first non-blank body line as well
        for bline in lines[frontmatter_end + 1:]:
            if bline.strip():
                header_lines.append(bline)
                break
        header_text = "\n".join(header_lines)
    else:
        # No frontmatter — treat first 4 lines as header
        header_text = "\n".join(lines[:4])

    return header_text, description


def _scan_fidelity_events(sessions_dir, skill_dirs_map, cutoff_ts):
    """Scan session transcripts and return fidelity event counts per skill.

    ``skill_dirs_map`` maps skill_name -> skill_dir_path (absolute).
    ``cutoff_ts``  is a Unix timestamp; only events in files modified after
    this are counted for the 7d window.

    Returns:
        dict skill_name -> {
            "body_fetch_count_7d": int,
            "linked_file_read_count_7d": int,
            "last_used_ts": float,
        }
    """
    stats = {
        name: {"body_fetch_count_7d": 0, "linked_file_read_count_7d": 0, "last_used_ts": 0.0}
        for name in skill_dirs_map
    }

    if not sessions_dir or not os.path.isdir(sessions_dir):
        return stats

    # Build lookup structures for fast matching
    # skill_md_paths: set of lowercased absolute paths to SKILL.md files
    skill_md_lower = {}  # lowercased path -> skill_name
    linked_prefix_lower = {}  # lowercased dir prefix -> skill_name

    for skill_name, skill_dir in skill_dirs_map.items():
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        skill_md_lower[skill_md_path.lower()] = skill_name
        for ldir in _LINKED_DIRS:
            ldir_path = os.path.join(skill_dir, ldir)
            linked_prefix_lower[ldir_path.lower()] = skill_name

    try:
        session_files = [
            f for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl") and ".deleted." not in f and ".reset." not in f
        ]
    except OSError:
        return stats

    for fname in session_files:
        fpath = os.path.join(sessions_dir, fname)
        try:
            file_mtime = os.path.getmtime(fpath)
        except OSError:
            continue
        # Only scan files touched in the 7d window
        if file_mtime < cutoff_ts:
            continue

        try:
            with open(fpath, "r", errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue

                    if ev.get("type") != "message":
                        continue
                    msg = ev.get("message", {}) or {}
                    role = msg.get("role", "")

                    if role != "assistant":
                        continue

                    content = msg.get("content") or []
                    if not isinstance(content, list):
                        continue

                    for blk in content:
                        if not isinstance(blk, dict):
                            continue
                        if blk.get("type") not in ("toolCall", "tool_use"):
                            continue
                        tool_name = (blk.get("name") or "").lower()
                        if tool_name not in ("read", "readfile", "read_file"):
                            continue

                        # Extract file path argument
                        args = blk.get("arguments") or blk.get("input") or {}
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                args = {}
                        if not isinstance(args, dict):
                            continue

                        file_path_arg = (
                            args.get("file_path")
                            or args.get("path")
                            or args.get("filename")
                            or ""
                        )
                        if not file_path_arg:
                            continue

                        fp_lower = file_path_arg.lower().replace("\\", "/")

                        # Check body-fetch: Read on SKILL.md itself
                        for sm_lower, skill_name in skill_md_lower.items():
                            sm_norm = sm_lower.replace("\\", "/")
                            if fp_lower.endswith(sm_norm) or sm_norm in fp_lower:
                                stats[skill_name]["body_fetch_count_7d"] += 1
                                if file_mtime > stats[skill_name]["last_used_ts"]:
                                    stats[skill_name]["last_used_ts"] = file_mtime

                        # Check linked-file read: Read on a file under scripts|refs|assets
                        for lp_lower, skill_name in linked_prefix_lower.items():
                            lp_norm = lp_lower.replace("\\", "/")
                            if lp_norm in fp_lower:
                                stats[skill_name]["linked_file_read_count_7d"] += 1
                                if file_mtime > stats[skill_name]["last_used_ts"]:
                                    stats[skill_name]["last_used_ts"] = file_mtime
        except Exception:
            continue

    return stats


@bp_skills.route("/api/skills")
def api_skills():
    """List all installed skills with fidelity stats.

    Returns:
        {
          "skills": [ { name, description, header_tokens, has_body,
                        has_linked_files, body_fetch_count_7d,
                        linked_file_read_count_7d, last_used_ts, status } ],
          "summary": { total_installed, dead_count, stuck_count,
                       total_header_tokens, wasted_header_tokens }
        }
    """
    import dashboard as _d

    empty_summary = {
        "total_installed": 0,
        "dead_count": 0,
        "stuck_count": 0,
        "total_header_tokens": 0,
        "wasted_header_tokens": 0,
    }

    skills_dir = _get_skills_dir()
    if not skills_dir or not os.path.isdir(skills_dir):
        return jsonify({"skills": [], "summary": empty_summary})

    # Discover installed skills
    try:
        entries = os.listdir(skills_dir)
    except OSError:
        return jsonify({"skills": [], "summary": empty_summary})

    skill_dirs_map = {}  # name -> absolute path
    for entry in sorted(entries):
        entry_path = os.path.join(skills_dir, entry)
        if not os.path.isdir(entry_path):
            continue
        skill_md = os.path.join(entry_path, "SKILL.md")
        if os.path.isfile(skill_md):
            skill_dirs_map[entry] = entry_path

    if not skill_dirs_map:
        return jsonify({"skills": [], "summary": empty_summary})

    now_ts = time.time()
    cutoff_7d = now_ts - 7 * 86400
    cutoff_30d = now_ts - 30 * 86400

    # Scan session transcripts for fidelity events
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions")
    fidelity_stats = _scan_fidelity_events(sessions_dir, skill_dirs_map, cutoff_7d)

    skills_out = []
    total_header_tokens = 0
    dead_count = 0
    stuck_count = 0
    wasted_header_tokens = 0

    for skill_name, skill_dir in skill_dirs_map.items():
        skill_md_path = os.path.join(skill_dir, "SKILL.md")
        header_text, description = _parse_skill_md(skill_md_path)

        # header_tokens: rough estimate (characters // 4)
        header_tokens = max(1, len(header_text) // 4)

        # has_body: SKILL.md exists and has content beyond frontmatter
        has_body = os.path.isfile(skill_md_path)

        # has_linked_files: any of scripts|references|assets subdirs exist
        has_linked_files = any(
            os.path.isdir(os.path.join(skill_dir, ldir)) for ldir in _LINKED_DIRS
        )

        fev = fidelity_stats.get(skill_name, {
            "body_fetch_count_7d": 0,
            "linked_file_read_count_7d": 0,
            "last_used_ts": 0.0,
        })
        body_fetch_count_7d = fev["body_fetch_count_7d"]
        linked_file_read_count_7d = fev["linked_file_read_count_7d"]
        last_used_ts = fev["last_used_ts"] or None

        # Determine install age from skill_md mtime
        try:
            install_ts = os.path.getmtime(skill_md_path)
        except OSError:
            install_ts = now_ts

        skill_age_days = (now_ts - install_ts) / 86400

        # Status rules:
        # dead   — body_fetch_count_7d==0 AND skill installed >30d
        # unused — has_body AND body_fetch_count_7d==0 AND installed >7d (but <=30d)
        # stuck  — has_linked_files AND linked_file_read_count_7d==0 AND body_fetch_count_7d>0
        # healthy — otherwise
        if body_fetch_count_7d == 0 and skill_age_days > 30:
            status = "dead"
            dead_count += 1
            wasted_header_tokens += header_tokens
        elif has_body and body_fetch_count_7d == 0 and skill_age_days > 7:
            status = "unused"
        elif has_linked_files and linked_file_read_count_7d == 0 and body_fetch_count_7d > 0:
            status = "stuck"
            stuck_count += 1
        else:
            status = "healthy"

        total_header_tokens += header_tokens

        skills_out.append({
            "name": skill_name,
            "description": description,
            "header_tokens": header_tokens,
            "has_body": has_body,
            "has_linked_files": has_linked_files,
            "body_fetch_count_7d": body_fetch_count_7d,
            "linked_file_read_count_7d": linked_file_read_count_7d,
            "last_used_ts": last_used_ts,
            "status": status,
        })

    # Sort: dead first, then stuck, unused, healthy; within each group by name
    _status_order = {"dead": 0, "stuck": 1, "unused": 2, "healthy": 3}
    skills_out.sort(key=lambda s: (_status_order.get(s["status"], 9), s["name"]))

    summary = {
        "total_installed": len(skills_out),
        "dead_count": dead_count,
        "stuck_count": stuck_count,
        "total_header_tokens": total_header_tokens,
        "wasted_header_tokens": wasted_header_tokens,
    }

    return jsonify({"skills": skills_out, "summary": summary})


@bp_skills.route("/api/skills/<skill_name>")
def api_skill_detail(skill_name):
    """Detail for one skill — usage over last 7 days.

    Returns the same fields as the list entry plus ``skill_dir`` path.
    404 if skill not found.
    """
    import dashboard as _d

    skills_dir = _get_skills_dir()
    if not skills_dir:
        return jsonify({"error": "skills directory not found"}), 404

    skill_dir = os.path.join(skills_dir, skill_name)
    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isdir(skill_dir) or not os.path.isfile(skill_md_path):
        return jsonify({"error": "skill not found"}), 404

    now_ts = time.time()
    cutoff_7d = now_ts - 7 * 86400

    header_text, description = _parse_skill_md(skill_md_path)
    header_tokens = max(1, len(header_text) // 4)
    has_body = True
    has_linked_files = any(
        os.path.isdir(os.path.join(skill_dir, ldir)) for ldir in _LINKED_DIRS
    )

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions")
    fidelity_stats = _scan_fidelity_events(sessions_dir, {skill_name: skill_dir}, cutoff_7d)
    fev = fidelity_stats.get(skill_name, {
        "body_fetch_count_7d": 0,
        "linked_file_read_count_7d": 0,
        "last_used_ts": 0.0,
    })

    body_fetch_count_7d = fev["body_fetch_count_7d"]
    linked_file_read_count_7d = fev["linked_file_read_count_7d"]
    last_used_ts = fev["last_used_ts"] or None

    try:
        install_ts = os.path.getmtime(skill_md_path)
    except OSError:
        install_ts = now_ts

    skill_age_days = (now_ts - install_ts) / 86400

    if body_fetch_count_7d == 0 and skill_age_days > 30:
        status = "dead"
    elif has_body and body_fetch_count_7d == 0 and skill_age_days > 7:
        status = "unused"
    elif has_linked_files and linked_file_read_count_7d == 0 and body_fetch_count_7d > 0:
        status = "stuck"
    else:
        status = "healthy"

    return jsonify({
        "name": skill_name,
        "description": description,
        "skill_dir": skill_dir,
        "header_tokens": header_tokens,
        "has_body": has_body,
        "has_linked_files": has_linked_files,
        "body_fetch_count_7d": body_fetch_count_7d,
        "linked_file_read_count_7d": linked_file_read_count_7d,
        "last_used_ts": last_used_ts,
        "status": status,
    })
