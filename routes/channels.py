"""
routes/channels.py — Per-channel adapter endpoints.

Extracted from dashboard.py as Phase 5.7 of the incremental modularisation.
Owns the 21 routes registered on ``bp_channels`` (Telegram, iMessage, WhatsApp,
Signal, Discord, Slack, IRC, WebChat, Google Chat, BlueBubbles, MS Teams,
Matrix, Mattermost, LINE, Nostr, Twitch, Feishu, Zalo, Tlon, Synology Chat,
Nextcloud Talk).

Module-level helpers (``_get_log_dirs``, ``_grep_log_file``,
``_generic_channel_data``) stay in dashboard.py and are reached via late
``import dashboard as _d``. Pure mechanical move — zero behaviour change.
"""

import glob
import json
import os
import sys
from datetime import datetime

from flask import Blueprint, jsonify, request

bp_channels = Blueprint('channels', __name__)


@bp_channels.route("/api/channel/telegram")
def api_channel_telegram():
    """Parse logs and session transcripts for Telegram message activity."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    messages = []
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. Parse log files for telegram events using grep for speed
    log_dirs = _d._get_log_dirs()
    log_files = []
    for ld in log_dirs:
        if os.path.isdir(ld):
            for f in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True):
                log_files.append(f)
    log_files = log_files[:2]  # Only today + yesterday

    run_sessions = {}
    for lf in log_files:
        try:
            # Pre-filter: outbound = "sendMessage ok", inbound via JSONL
            _grep_lines = _d._grep_log_file(
                lf, r"sendMessage ok\|sendMessage failed\|telegram message failed"
            )
            for line in _grep_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg1 = obj.get("1", "") or ""
                ts = obj.get("time", "") or (obj.get("_meta", {}) or {}).get("date", "")

                # Outbound: "telegram sendMessage ok chat=1532693273 message=5961"
                if "sendmessage ok" in msg1.lower():
                    chat_match = re.search(r"chat=(-?\d+)", msg1)
                    msg_match = re.search(r"message=(\d+)", msg1)
                    chat_id = chat_match.group(1) if chat_match else ""
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "out",
                            "sender": "Bot",
                            "text": f"(sent message {msg_match.group(1) if msg_match else ''})",
                            "chatId": chat_id,
                            "sessionId": "",
                        }
                    )
                elif "sendmessage" in msg1.lower() and "failed" in msg1.lower():
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "out",
                            "sender": "Bot",
                            "text": "(delivery failed)",
                            "chatId": "",
                            "sessionId": "",
                        }
                    )
        except Exception:
            pass

    # 2. Parse session JSONL files for inbound messages (user role = incoming Telegram)
    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")
    for msg in messages:
        if msg["direction"] == "in" and msg["sessionId"] and not msg["text"]:
            sf = os.path.join(sessions_dir, msg["sessionId"] + ".jsonl")
            if os.path.exists(sf):
                try:
                    with open(sf, "r", errors="replace") as f:
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except json.JSONDecodeError:
                                continue
                            sm = sd.get("message", {})
                            if sm.get("role") == "user":
                                content = sm.get("content", "")
                                if isinstance(content, list):
                                    for c in content:
                                        if (
                                            isinstance(c, dict)
                                            and c.get("type") == "text"
                                        ):
                                            txt = c.get("text", "")
                                            # Skip system/heartbeat messages
                                            if (
                                                txt
                                                and not txt.startswith("System:")
                                                and "HEARTBEAT" not in txt
                                            ):
                                                msg["text"] = txt[:300]
                                                # Extract real sender from [Telegram Name id:...] pattern
                                                tg_name = re.search(
                                                    r"\[Telegram\s+(.+?)\s+id:", txt
                                                )
                                                if tg_name:
                                                    msg["sender"] = tg_name.group(1)
                                                break
                                elif isinstance(content, str) and content:
                                    if (
                                        not content.startswith("System:")
                                        and "HEARTBEAT" not in content
                                    ):
                                        msg["text"] = content[:300]
                                        tg_name = re.search(
                                            r"\[Telegram\s+(.+?)\s+id:", content
                                        )
                                        if tg_name:
                                            msg["sender"] = tg_name.group(1)
                                if msg["text"]:
                                    break
                except Exception:
                    pass

    # 3. Also scan telegram session files for recent messages
    try:
        with open(os.path.join(sessions_dir, "sessions.json"), "r") as f:
            sess_data = json.load(f)
        tg_sessions = [
            (sid, s)
            for sid, s in sess_data.items()
            if "telegram" in sid and "sessionId" in s
        ]
        tg_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)

        seen_sids = {m["sessionId"] for m in messages if m["sessionId"]}
        for sid_key, sinfo in tg_sessions[:5]:
            uuid = sinfo["sessionId"]
            if uuid in seen_sids:
                continue
            sf = os.path.join(sessions_dir, uuid + ".jsonl")
            if not os.path.exists(sf):
                continue
            try:
                chat_match = re.search(r":(-?\d+)$", sid_key)
                chat_id = chat_match.group(1) if chat_match else ""
                # Read only last 64KB of session file for performance
                fsize = os.path.getsize(sf)
                with open(sf, "r", errors="replace") as f:
                    if fsize > 65536:
                        f.seek(fsize - 65536)
                        f.readline()  # skip partial line
                    for sline in f:
                        sline = sline.strip()
                        if not sline:
                            continue
                        try:
                            sd = json.loads(sline)
                        except json.JSONDecodeError:
                            continue
                        sm = sd.get("message", {})
                        ts = sd.get("timestamp", "")
                        role = sm.get("role", "")
                        if role not in ("user", "assistant"):
                            continue
                        content = sm.get("content", "")
                        txt = ""
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and c.get("type") == "text":
                                    txt = c.get("text", "")
                                    break
                        elif isinstance(content, str):
                            txt = content
                        if not txt or txt.startswith("System:") or "HEARTBEAT" in txt:
                            continue
                        direction = "in" if role == "user" else "out"
                        sender = "User" if role == "user" else "Clawd"
                        if direction == "in":
                            tg_name = re.search(r"\[Telegram\s+(.+?)\s+id:", txt)
                            if tg_name:
                                sender = tg_name.group(1)
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": direction,
                                "sender": sender,
                                "text": txt[:300],
                                "chatId": chat_id,
                                "sessionId": uuid,
                            }
                        )
            except Exception:
                pass
    except Exception:
        pass

    # Deduplicate by timestamp+direction, sort newest first
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    # Stats
    today_in = sum(
        1 for m in unique if m["direction"] == "in" and today in m.get("timestamp", "")
    )
    today_out = sum(
        1 for m in unique if m["direction"] == "out" and today in m.get("timestamp", "")
    )

    total = len(unique)
    page = unique[offset : offset + limit]
    return jsonify(
        {"messages": page, "total": total, "todayIn": today_in, "todayOut": today_out}
    )


@bp_channels.route("/api/channel/imessage")
def api_channel_imessage():
    """Read iMessage history from ~/Library/Messages/chat.db."""
    import dashboard as _d

    if sys.platform != "darwin":
        return jsonify(
            {
                "messages": [],
                "todayIn": 0,
                "todayOut": 0,
                "note": "iMessage is only available on macOS",
            }
        )
    import sqlite3

    limit = request.args.get("limit", 50, type=int)

    messages = []
    today = datetime.now().strftime("%Y-%m-%d")
    # Apple epoch starts 2001-01-01; convert to Unix
    APPLE_EPOCH_OFFSET = 978307200

    db_path = os.path.expanduser("~/Library/Messages/chat.db")
    db_ok = False

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # Get recent messages with handle info
            cur.execute(
                """
                SELECT m.ROWID, m.text, m.is_from_me,
                       m.date / 1000000000 AS date_sec,
                       h.id AS handle_id,
                       h.uncanonicalized_id
                FROM message m
                LEFT JOIN handle h ON m.handle_id = h.ROWID
                WHERE m.text IS NOT NULL AND m.text != ''
                ORDER BY m.date DESC
                LIMIT ?
            """,
                (limit,),
            )
            rows = cur.fetchall()
            conn.close()
            for row in rows:
                direction = "out" if row["is_from_me"] else "in"
                # Convert Apple epoch (nanoseconds) to ISO timestamp
                unix_ts = (row["date_sec"] or 0) + APPLE_EPOCH_OFFSET
                ts = (
                    datetime.utcfromtimestamp(unix_ts).strftime("%Y-%m-%dT%H:%M:%SZ")
                    if unix_ts > APPLE_EPOCH_OFFSET
                    else ""
                )
                contact = row["uncanonicalized_id"] or row["handle_id"] or "Unknown"
                sender = "Me" if direction == "out" else contact
                messages.append(
                    {
                        "timestamp": ts,
                        "direction": direction,
                        "sender": sender,
                        "text": (row["text"] or "")[:300],
                        "chatId": contact,
                        "sessionId": "",
                    }
                )
            db_ok = True
        except Exception:
            pass

    # Fallback: scan OpenClaw logs for imessage delivery events
    if not db_ok or len(messages) == 0:
        log_dirs = _d._get_log_dirs()
        for ld in log_dirs:
            if not os.path.isdir(ld):
                continue
            for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:2]:
                try:
                    _grep_lines = _d._grep_log_file(
                        lf, "imessage\\|iMessage\\|messageChannel=imessage"
                    )
                    for line in _grep_lines:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except Exception:
                            continue
                        ts = obj.get("time", "") or (obj.get("_meta", {}) or {}).get(
                            "date", ""
                        )
                        msg1 = obj.get("1", "") or obj.get("0", "")
                        direction = "out" if "deliver" in msg1.lower() else "in"
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": direction,
                                "sender": "Me" if direction == "out" else "Contact",
                                "text": msg1[:300],
                                "chatId": "",
                                "sessionId": "",
                            }
                        )
                except Exception:
                    pass

    # Deduplicate and sort newest first
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    today_in = sum(
        1 for m in unique if m["direction"] == "in" and today in m.get("timestamp", "")
    )
    today_out = sum(
        1 for m in unique if m["direction"] == "out" and today in m.get("timestamp", "")
    )

    total = len(unique)
    page = unique[:limit]
    return jsonify(
        {"messages": page, "total": total, "todayIn": today_in, "todayOut": today_out}
    )


@bp_channels.route("/api/channel/whatsapp")
def api_channel_whatsapp():
    """Parse logs and session transcripts for WhatsApp message activity."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)
    messages = []
    today = datetime.now().strftime("%Y-%m-%d")

    log_dirs = _d._get_log_dirs()
    log_files = []
    for ld in log_dirs:
        if os.path.isdir(ld):
            for f in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:2]:
                log_files.append(f)

    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")

    for lf in log_files:
        try:
            _grep_lines = _d._grep_log_file(
                lf, "messageChannel=whatsapp\\|whatsapp.*deliver"
            )
            for line in _grep_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg1 = obj.get("1", "") or obj.get("0", "")
                msg0 = obj.get("0", "")
                ts = obj.get("time", "") or (obj.get("_meta", {}) or {}).get("date", "")

                if "messageChannel=whatsapp" in msg1 and "run start" in msg1:
                    sid_match = re.search(r"sessionId=([a-f0-9-]+)", msg1)
                    sid = sid_match.group(1) if sid_match else ""
                    text = ""
                    if sid:
                        sf = os.path.join(sessions_dir, sid + ".jsonl")
                        if os.path.exists(sf):
                            try:
                                with open(sf, "r", errors="replace") as f:
                                    for sline in f:
                                        try:
                                            sd = json.loads(sline.strip())
                                        except Exception:
                                            continue
                                        sm = sd.get("message", {})
                                        if sm.get("role") == "user":
                                            content = sm.get("content", "")
                                            if isinstance(content, list):
                                                for c in content:
                                                    if (
                                                        isinstance(c, dict)
                                                        and c.get("type") == "text"
                                                    ):
                                                        txt = c.get("text", "")
                                                        if (
                                                            txt
                                                            and "HEARTBEAT" not in txt
                                                        ):
                                                            text = txt[:300]
                                                            break
                                            elif (
                                                isinstance(content, str)
                                                and "HEARTBEAT" not in content
                                            ):
                                                text = content[:300]
                                            if text:
                                                break
                            except Exception:
                                pass
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "in",
                            "sender": "User",
                            "text": text,
                            "sessionId": sid,
                        }
                    )

                if "whatsapp" in msg0.lower() and "deliver" in msg0.lower():
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "out",
                            "sender": "Clawd",
                            "text": "(message sent)",
                            "sessionId": "",
                        }
                    )
        except Exception:
            pass

    # Deduplicate and sort
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    today_in = sum(
        1 for m in unique if m["direction"] == "in" and today in m.get("timestamp", "")
    )
    today_out = sum(
        1 for m in unique if m["direction"] == "out" and today in m.get("timestamp", "")
    )
    total = len(unique)
    return jsonify(
        {
            "messages": unique[:limit],
            "total": total,
            "todayIn": today_in,
            "todayOut": today_out,
        }
    )


@bp_channels.route("/api/channel/signal")
def api_channel_signal():
    """Parse logs and session transcripts for Signal message activity."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)
    messages = []
    today = datetime.now().strftime("%Y-%m-%d")

    log_dirs = _d._get_log_dirs()
    log_files = []
    for ld in log_dirs:
        if os.path.isdir(ld):
            for f in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:2]:
                log_files.append(f)

    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")

    for lf in log_files:
        try:
            _grep_lines = _d._grep_log_file(lf, "messageChannel=signal\\|signal.*deliver")
            for line in _grep_lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg1 = obj.get("1", "") or obj.get("0", "")
                msg0 = obj.get("0", "")
                ts = obj.get("time", "") or (obj.get("_meta", {}) or {}).get("date", "")

                if "messageChannel=signal" in msg1 and "run start" in msg1:
                    sid_match = re.search(r"sessionId=([a-f0-9-]+)", msg1)
                    sid = sid_match.group(1) if sid_match else ""
                    text = ""
                    if sid:
                        sf = os.path.join(sessions_dir, sid + ".jsonl")
                        if os.path.exists(sf):
                            try:
                                with open(sf, "r", errors="replace") as f:
                                    for sline in f:
                                        try:
                                            sd = json.loads(sline.strip())
                                        except Exception:
                                            continue
                                        sm = sd.get("message", {})
                                        if sm.get("role") == "user":
                                            content = sm.get("content", "")
                                            if isinstance(content, list):
                                                for c in content:
                                                    if (
                                                        isinstance(c, dict)
                                                        and c.get("type") == "text"
                                                    ):
                                                        txt = c.get("text", "")
                                                        if (
                                                            txt
                                                            and "HEARTBEAT" not in txt
                                                        ):
                                                            text = txt[:300]
                                                            break
                                            elif (
                                                isinstance(content, str)
                                                and "HEARTBEAT" not in content
                                            ):
                                                text = content[:300]
                                            if text:
                                                break
                            except Exception:
                                pass
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "in",
                            "sender": "User",
                            "text": text,
                            "sessionId": sid,
                        }
                    )

                if "signal" in msg0.lower() and "deliver" in msg0.lower():
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": "out",
                            "sender": "Clawd",
                            "text": "(message sent)",
                            "sessionId": "",
                        }
                    )
        except Exception:
            pass

    # Deduplicate and sort
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    today_in = sum(
        1 for m in unique if m["direction"] == "in" and today in m.get("timestamp", "")
    )
    today_out = sum(
        1 for m in unique if m["direction"] == "out" and today in m.get("timestamp", "")
    )
    total = len(unique)
    return jsonify(
        {
            "messages": unique[:limit],
            "total": total,
            "todayIn": today_in,
            "todayOut": today_out,
        }
    )


@bp_channels.route("/api/channel/discord")
def api_channel_discord():
    """Discord channel data: log-based with guild/channel extraction."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)
    today = datetime.now().strftime("%Y-%m-%d")
    messages = []
    guilds = set()
    channels = set()
    today_in = 0
    today_out = 0

    # Scan log files for Discord events
    log_dirs = _d._get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:3]:
            try:
                _grep_lines = _d._grep_log_file(
                    lf, "messageChannel=discord|discord.*deliver"
                )
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    if "messageChannel=discord" in msg1:
                        direction = "in"
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": "in",
                                "sender": "User",
                                "text": msg1[:300],
                            }
                        )
                        if today and today in ts:
                            today_in += 1
                    elif re.search(r"discord.*deliver", msg1, re.IGNORECASE):
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": "out",
                                "sender": "Bot",
                                "text": msg1[:300],
                            }
                        )
                        if today and today in ts:
                            today_out += 1
            except Exception:
                pass

    # Scan session transcripts for Discord messages and guild/channel info
    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")
    sessions_file = os.path.join(sessions_dir, "sessions.json")
    if os.path.exists(sessions_file):
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            ch_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if "discord" in sid.lower() and "sessionId" in s
            ]
            ch_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in ch_sessions[:5]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    fsize = os.path.getsize(sf)
                    with open(sf, "r", errors="replace") as f:
                        if fsize > 65536:
                            f.seek(fsize - 65536)
                            f.readline()
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if (
                                not txt
                                or txt.startswith("System:")
                                or "HEARTBEAT" in txt
                            ):
                                continue
                            # Extract guild/channel from [Discord guildName channelName] pattern
                            m = re.search(r"\[Discord\s+([^\]]+?)\s+#?(\S+)\]", txt)
                            if m:
                                guilds.add(m.group(1))
                                channels.add(m.group(2))
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Bot",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    # Deduplicate and sort
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "guilds": sorted(guilds),
            "channels": sorted(channels),
        }
    )


@bp_channels.route("/api/channel/slack")
def api_channel_slack():
    """Slack channel data: log-based with workspace/channel extraction."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)
    today = datetime.now().strftime("%Y-%m-%d")
    messages = []
    workspaces = set()
    channels = set()
    today_in = 0
    today_out = 0

    # Scan log files for Slack events
    log_dirs = _d._get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:3]:
            try:
                _grep_lines = _d._grep_log_file(lf, "messageChannel=slack|slack.*deliver")
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    if "messageChannel=slack" in msg1:
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": "in",
                                "sender": "User",
                                "text": msg1[:300],
                            }
                        )
                        if today and today in ts:
                            today_in += 1
                    elif re.search(r"slack.*deliver", msg1, re.IGNORECASE):
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": "out",
                                "sender": "Bot",
                                "text": msg1[:300],
                            }
                        )
                        if today and today in ts:
                            today_out += 1
            except Exception:
                pass

    # Scan session transcripts for Slack messages and workspace/channel info
    sessions_dir = os.path.expanduser("~/.openclaw/agents/main/sessions")
    sessions_file = os.path.join(sessions_dir, "sessions.json")
    if os.path.exists(sessions_file):
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            ch_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if "slack" in sid.lower() and "sessionId" in s
            ]
            ch_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in ch_sessions[:5]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    fsize = os.path.getsize(sf)
                    with open(sf, "r", errors="replace") as f:
                        if fsize > 65536:
                            f.seek(fsize - 65536)
                            f.readline()
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if (
                                not txt
                                or txt.startswith("System:")
                                or "HEARTBEAT" in txt
                            ):
                                continue
                            # Extract workspace/channel from [Slack workspace #channel] pattern
                            m = re.search(r"\[Slack\s+([^\]]+?)\s+#?(\S+)\]", txt)
                            if m:
                                workspaces.add(m.group(1))
                                channels.add(m.group(2))
                            # Also look for channel mentions like #general
                            ch_m = re.findall(r"#([a-z0-9_-]+)", txt[:200])
                            for ch in ch_m:
                                channels.add(ch)
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Bot",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    # Deduplicate and sort
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "workspaces": sorted(workspaces),
            "channels": sorted(channels),
        }
    )


@bp_channels.route("/api/channel/irc")
def api_channel_irc():
    """IRC channel data: log-based, extracts channel names and nicks."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)
    today = datetime.now().strftime("%Y-%m-%d")
    base = (
        _d._generic_channel_data.__wrapped__("irc")
        if hasattr(_d._generic_channel_data, "__wrapped__")
        else None
    )

    messages = []
    today_in = 0
    today_out = 0
    channels = set()
    nicks = set()

    log_dirs = _d._get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:3]:
            try:
                _grep_lines = _d._grep_log_file(lf, "messageChannel=irc")
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    direction = "out" if "deliver" in msg1.lower() else "in"
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": direction,
                            "sender": "User" if direction == "in" else "Clawd",
                            "text": msg1[:200],
                        }
                    )
                    if today and today in ts:
                        if direction == "in":
                            today_in += 1
                        else:
                            today_out += 1
                    # Extract IRC channels/nicks from log
                    for ch in re.findall(r"#\w+", msg1):
                        channels.add(ch)
                    for nick in re.findall(r"nick[=:](\w+)", msg1, re.I):
                        nicks.add(nick)
            except Exception:
                pass

    # Also scan session transcripts
    for sessions_dir in [
        os.path.expanduser("~/.openclaw/agents/main/sessions"),
        os.path.expanduser("~/.clawdbot/agents/main/sessions"),
    ]:
        sessions_file = os.path.join(sessions_dir, "sessions.json")
        if not os.path.exists(sessions_file):
            continue
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            ch_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if "irc" in sid.lower() and "sessionId" in s
            ]
            ch_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in ch_sessions[:5]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    with open(sf, "r", errors="replace") as f:
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if not txt or "HEARTBEAT" in txt:
                                continue
                            for ch in re.findall(r"\[IRC\s+(#\w+)", txt):
                                channels.add(ch)
                            for nick in re.findall(r"\[IRC\s+#\w+\s+(\w+)\]", txt):
                                nicks.add(nick)
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Clawd",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "channels": sorted(channels),
            "nicks": sorted(nicks),
            "status": "connected" if unique else "configured",
        }
    )


@bp_channels.route("/api/channel/webchat")
def api_channel_webchat():
    """Webchat channel data: parse logs + sessions, return active session info."""
    import dashboard as _d
    import re

    limit = request.args.get("limit", 50, type=int)
    today = datetime.now().strftime("%Y-%m-%d")

    messages = []
    today_in = 0
    today_out = 0
    active_sessions = set()
    last_active = None

    log_dirs = _d._get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:3]:
            try:
                _grep_lines = _d._grep_log_file(lf, "messageChannel=webchat")
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    direction = "out" if "deliver" in msg1.lower() else "in"
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": direction,
                            "sender": "User" if direction == "in" else "Clawd",
                            "text": msg1[:200],
                        }
                    )
                    if today and today in ts:
                        if direction == "in":
                            today_in += 1
                        else:
                            today_out += 1
                    # Extract session IDs
                    for sid in re.findall(r"sessionId=([a-f0-9\-]+)", msg1):
                        active_sessions.add(sid)
                    if ts and (last_active is None or ts > last_active):
                        last_active = ts
            except Exception:
                pass

    # Scan sessions for webchat sessions
    for sessions_dir in [
        os.path.expanduser("~/.openclaw/agents/main/sessions"),
        os.path.expanduser("~/.clawdbot/agents/main/sessions"),
    ]:
        sessions_file = os.path.join(sessions_dir, "sessions.json")
        if not os.path.exists(sessions_file):
            continue
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            wc_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if "webchat" in sid.lower() and "sessionId" in s
            ]
            wc_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in wc_sessions[:10]:
                active_sessions.add(sinfo["sessionId"])
                upd = sinfo.get("updatedAt", 0)
                if upd:
                    ts_str = datetime.fromtimestamp(
                        upd / 1000 if upd > 1e10 else upd
                    ).isoformat()
                    if last_active is None or ts_str > last_active:
                        last_active = ts_str
            # Load messages from recent webchat sessions
            for sid_key, sinfo in wc_sessions[:3]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    fsize = os.path.getsize(sf)
                    with open(sf, "r", errors="replace") as f:
                        if fsize > 65536:
                            f.seek(fsize - 65536)
                            f.readline()
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if not txt or "HEARTBEAT" in txt:
                                continue
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Clawd",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    # Also check ~/.openclaw/webchat/ dir
    wc_dir = os.path.expanduser("~/.openclaw/webchat")
    if os.path.isdir(wc_dir):
        for f in glob.glob(os.path.join(wc_dir, "*.json"))[:5]:
            active_sessions.add(os.path.basename(f).replace(".json", ""))

    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "activeSessions": len(active_sessions),
            "lastActive": last_active,
            "status": "connected" if unique else "configured",
        }
    )


@bp_channels.route("/api/channel/googlechat")
def api_channel_googlechat():
    import dashboard as _d
    result = _d._generic_channel_data("googlechat")
    data = result.get_json()
    data["spaces"] = []
    return jsonify(data)


@bp_channels.route("/api/channel/bluebubbles")
def api_channel_bluebubbles():
    """BlueBubbles channel: try REST API first, fallback to logs."""
    import dashboard as _d

    limit = request.args.get("limit", 50, type=int)
    today = datetime.now().strftime("%Y-%m-%d")

    messages = []
    today_in = 0
    today_out = 0
    chat_count = None
    bb_status = "configured"

    # Check for BlueBubbles config
    cfg_path = os.path.expanduser("~/.openclaw/openclaw.json")
    bb_url = None
    bb_pass = None
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path) as f:
                cfg = json.load(f)
            bb_cfg = cfg.get("channels", {}).get("bluebubbles", {})
            bb_url = bb_cfg.get("serverUrl", "").rstrip("/")
            bb_pass = bb_cfg.get("password", "")
        except Exception:
            pass

    # Try BlueBubbles REST API
    if bb_url:
        try:
            import urllib.request

            api_url = f"{bb_url}/api/v1/chat/count"
            req = urllib.request.Request(
                api_url,
                headers={"Authorization": f"Bearer {bb_pass}"} if bb_pass else {},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                bb_data = json.loads(resp.read().decode())
                chat_count = bb_data.get("data", {}).get(
                    "total", bb_data.get("total", 0)
                )
                bb_status = "connected"
            # Try to get recent messages
            msgs_url = f"{bb_url}/api/v1/message/count/me?limit=50"
            req2 = urllib.request.Request(
                msgs_url,
                headers={"Authorization": f"Bearer {bb_pass}"} if bb_pass else {},
            )
            with urllib.request.urlopen(req2, timeout=3) as resp2:
                pass  # just count endpoint
        except Exception:
            pass

    # Fallback: parse logs
    log_dirs = _d._get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:3]:
            try:
                _grep_lines = _d._grep_log_file(lf, "messageChannel=bluebubbles")
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    direction = "out" if "deliver" in msg1.lower() else "in"
                    messages.append(
                        {
                            "timestamp": ts,
                            "direction": direction,
                            "sender": "User" if direction == "in" else "Clawd",
                            "text": msg1[:200],
                        }
                    )
                    if today and today in ts:
                        if direction == "in":
                            today_in += 1
                        else:
                            today_out += 1
                    if bb_status == "configured":
                        bb_status = "log-only"
            except Exception:
                pass

    # Scan sessions
    for sessions_dir in [
        os.path.expanduser("~/.openclaw/agents/main/sessions"),
        os.path.expanduser("~/.clawdbot/agents/main/sessions"),
    ]:
        sessions_file = os.path.join(sessions_dir, "sessions.json")
        if not os.path.exists(sessions_file):
            continue
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            ch_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if "bluebubbles" in sid.lower() and "sessionId" in s
            ]
            ch_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in ch_sessions[:3]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    with open(sf, "r", errors="replace") as f:
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if not txt or "HEARTBEAT" in txt:
                                continue
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Clawd",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "chatCount": chat_count,
            "status": bb_status,
        }
    )


@bp_channels.route("/api/channel/msteams")
def api_channel_msteams():
    import dashboard as _d
    result = _d._generic_channel_data("msteams")
    data = result.get_json()
    data["teams"] = []
    return jsonify(data)


@bp_channels.route("/api/channel/matrix")
def api_channel_matrix():
    import dashboard as _d
    return _d._generic_channel_data("matrix")


@bp_channels.route("/api/channel/mattermost")
def api_channel_mattermost():
    import dashboard as _d
    result = _d._generic_channel_data("mattermost")
    data = result.get_json()
    data["channels"] = []
    return jsonify(data)


@bp_channels.route("/api/channel/line")
def api_channel_line():
    import dashboard as _d
    return _d._generic_channel_data("line")


@bp_channels.route("/api/channel/nostr")
def api_channel_nostr():
    import dashboard as _d
    return _d._generic_channel_data("nostr")


@bp_channels.route("/api/channel/twitch")
def api_channel_twitch():
    import dashboard as _d
    return _d._generic_channel_data("twitch")


@bp_channels.route("/api/channel/feishu")
def api_channel_feishu():
    import dashboard as _d
    return _d._generic_channel_data("feishu")


@bp_channels.route("/api/channel/zalo")
def api_channel_zalo():
    import dashboard as _d
    return _d._generic_channel_data("zalo")


@bp_channels.route("/api/channel/tlon")
def api_channel_tlon():
    import dashboard as _d
    return _d._generic_channel_data("tlon")


@bp_channels.route("/api/channel/synology-chat")
def api_channel_synology_chat():
    import dashboard as _d
    return _d._generic_channel_data("synology-chat")


@bp_channels.route("/api/channel/nextcloud-talk")
def api_channel_nextcloud_talk():
    import dashboard as _d
    return _d._generic_channel_data("nextcloud-talk")
