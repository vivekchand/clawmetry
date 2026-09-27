"""Bounded, inert text views for credential inspection (REQ-GOV-DET-001).

These are possible representations, not proof that a command executed them.
Nothing is evaluated, decompressed, fetched, or written. Limits are returned
alongside the views so exhausting a budget cannot silently mean clean.
"""
from __future__ import annotations

import base64
import binascii
from collections import deque
from itertools import islice
import re
from urllib.parse import unquote

MAX_INPUT_CHARS = 65536
MAX_TOTAL_CHARS = 131072
MAX_VIEWS = 128
MAX_CANDIDATES = 128
MAX_DECODE_DEPTH = 4
MAX_NODES = 512
MAX_CONTAINER_DEPTH = 8
_BASE64 = re.compile(r"(?<![A-Za-z0-9+/_-])[A-Za-z0-9+/_-]{24,}={0,2}")
_HEX = re.compile(r"(?<![A-Za-z0-9])[0-9a-fA-F]{32,}(?![A-Za-z0-9])")
_ESCAPE = re.compile(r"\\(?:u([0-9a-fA-F]{4})|x([0-9a-fA-F]{2}))")
_PERCENT = re.compile(r"%[0-9a-fA-F]{2}")


def text_views(value) -> tuple:
    """Return (case-preserving string views, non-content limit reason codes).

    Walk JSON-like containers without serializing the whole object. Both
    rejected decode attempts and accepted output consume fixed budgets.
    """
    reasons = set()
    raw = []
    remaining = MAX_INPUT_CHARS
    nodes = 0
    seen_containers = set()
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        nodes += 1
        if nodes > MAX_NODES:
            reasons.add("container_items")
            break
        if isinstance(item, str):
            if len(item) > remaining:
                reasons.add("input_size")
            part = item[:remaining]
            remaining -= len(part)
            if part:
                raw.append(part)
        elif isinstance(item, (dict, list, tuple)):
            if id(item) in seen_containers:
                reasons.add("repeated_container")
                continue
            seen_containers.add(id(item))
            if depth >= MAX_CONTAINER_DEPTH:
                reasons.add("container_depth")
                continue
            # Include keys: map keys can themselves carry sensitive values.
            slots = max(0, MAX_NODES - nodes - len(pending))
            if isinstance(item, dict):
                children = []
                for key, val in islice(item.items(), (slots + 1) // 2):
                    children.extend((key, val))
                count = len(item) * 2
            else:
                children = list(islice(item, slots))
                count = len(item)
            if count > slots:
                reasons.add("container_items")
            pending.extend((child, depth + 1) for child in reversed(children[:slots]))

    queue = deque((part, 0) for part in raw)
    views = []
    seen_text = set()
    total = 0
    attempts = 0
    while queue:
        text, depth = queue.popleft()
        if text in seen_text:
            continue
        if len(views) >= MAX_VIEWS:
            reasons.add("view_count")
            break
        if total + len(text) > MAX_TOTAL_CHARS:
            reasons.add("decoded_size")
            break
        seen_text.add(text)
        views.append(text)
        total += len(text)

        def enqueue(decoded):
            if not decoded or decoded == text or decoded in seen_text:
                return
            if depth >= MAX_DECODE_DEPTH:
                reasons.add("decode_depth")
            elif len(decoded) + total > MAX_TOTAL_CHARS:
                reasons.add("decoded_size")
            else:
                queue.append((decoded, depth + 1))

        if _PERCENT.search(text):
            enqueue(unquote(text, errors="replace"))
        if _ESCAPE.search(text):
            enqueue(_ESCAPE.sub(lambda m: chr(int(m.group(1) or m.group(2), 16)), text))
        for pattern, encoding in ((_HEX, "hex"), (_BASE64, "base64")):
            for match in pattern.finditer(text):
                if attempts >= MAX_CANDIDATES:
                    reasons.add("decode_candidates")
                    break
                attempts += 1
                token = match.group(0)
                try:
                    if encoding == "hex":
                        payload = bytes.fromhex(token)
                    else:
                        payload = base64.b64decode(token + "=" * (-len(token) % 4),
                                                   altchars=b"-_", validate=True)
                    decoded = payload.decode("utf-8")
                except (ValueError, UnicodeError, binascii.Error):
                    continue
                if all(c.isprintable() or c in "\n\r\t" for c in decoded):
                    enqueue(decoded)
    return tuple(views), tuple(sorted(reasons))
