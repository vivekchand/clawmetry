"""Are sessions that should be independent behaving as if they're coordinated?

Every other detector reads ONE session and asks whether it is doing something
it does not normally do. The July 2026 Hugging Face swarm defeated that
question by construction: each of ~1,200 agents looked only slightly off, and
the population used a shared Artifactory cache as a message board (WebDAV
MKCOL/PUT under one path) that no single session made visible. Scorecard rows
5 and 11: https://clawmetry.com/blog/could-clawmetry-have-caught-the-hugging-face-swarm

This module asks the fleet question instead. It groups the WRITE calls of
recently active sessions by an action fingerprint ``(verb, host, path
prefix)`` and reports a fingerprint when sessions from several unrelated
families share it and the node has no settled history of it.

* Unrelated: sessions are grouped into families by walking
  ``subagents.parent_session_id`` up to a root. An orchestrator and its
  subagents SHOULD look coordinated, so a family counts once.
* Unusual: a fingerprint counts as normal only after it has been in the
  node's memory for the settle window (``EGRESS_SETTLE_HOURS``), the same rule
  that stops a swarm vouching for its own destination. A node that has not
  been recording fingerprints for a full window reports nothing: on day one
  every fingerprint is "new", and saying so would be noise.
* Pure: no I/O and no clock beyond the ``now`` the caller passes. The daemon
  supplies the fingerprints, the parent edges and the history.

Like every behavioural detector it reads tool ARGUMENTS, and says so. It only
reports: acting on it takes a policy that names ``coordinated_action``
explicitly (see ``policy_engine``), because a swarm detector that could pause
700 sessions on a catch-all rule would be an incident of its own.
"""
from __future__ import annotations

import os
import re
import time
from typing import Optional

from clawmetry.detector_calibration import EGRESS_SETTLE_HOURS
from clawmetry.detector_surface import _SEGMENT_SPLIT_RE, _program, _segment_write_hosts

#: The incident kinds only a fleet-wide pass can produce. Re-exported through
#: ``detectors.ALL_INCIDENT_KINDS`` so every renderer and policy form knows them.
FLEET_KINDS = ("coordinated_action",)

#: Unrelated session families that must share an unusual fingerprint.
COORD_MIN_FAMILIES = int(os.environ.get("CLAWMETRY_COORD_MIN_SESSIONS", "5"))
_MAX_PARENT_DEPTH = 25
_MAX_SESSION_IDS = 20

_URL_PATH_RE = re.compile(
    r"\b[a-z][a-z0-9+.\-]{1,15}://([^/\s'\"<>|)]+)(/[^\s'\"<>|)?#]*)?", re.I)
_METHOD_RE = re.compile(
    r"(?:(?:^|\s)-(?!-)[A-Za-z]*X\s*|--request[=\s]+|--method[=\s]+)['\"]?([A-Za-z]+)")
_HTTPIE_METHOD_RE = re.compile(r"^(?:https?|xh|xhs)\s+(?:-\S+\s+)*([A-Za-z]+)\s")
_CURL_UPLOAD_RE = re.compile(r"(?:^|\s)(?:-(?!-)[A-Za-z]*T(?![A-Za-z])|--upload-file)")


def _verb(segment: str) -> str:
    """The HTTP method a writing segment used, or the kind of transfer."""
    seg = segment.strip()
    m = _METHOD_RE.search(seg)
    if m:
        return m.group(1).upper()
    prog = _program(seg)
    if prog in ("http", "https", "xh", "xhs"):
        m = _HTTPIE_METHOD_RE.search(seg)
        if m:
            return m.group(1).upper()
    if prog == "curl":
        return "PUT" if _CURL_UPLOAD_RE.search(seg) else "POST"
    if prog == "wget":
        return "POST"
    return "UPLOAD"


def _path_prefix(segment: str, host: str) -> str:
    """The first two path segments of the URL that reaches ``host``.

    A segment containing a digit becomes ``*``: per-agent names such as
    ``zz17`` or ``v1`` would otherwise give every agent its own fingerprint,
    and a digit run is also the most likely place for an id to hide.
    """
    for m in _URL_PATH_RE.finditer(segment):
        netloc = m.group(1).rsplit("@", 1)[-1].lower()
        if netloc.split(":", 1)[0].rstrip(".") != host:
            continue
        parts = [p for p in (m.group(2) or "").split("/") if p][:2]
        parts = ["*" if any(c.isdigit() for c in p) else p[:40] for p in parts]
        return "/" + "/".join(parts) if parts else "/"
    return ""


def write_fingerprints(steps) -> list:
    """``(verb, host, path_prefix)`` for every write call in a session's
    normalized steps. Never raises."""
    out: set = set()
    try:
        for st in steps or ():
            if not isinstance(st, dict) or st.get("kind") != "tool_call":
                continue
            written = st.get("write_hosts") or ()
            if not written:
                continue
            covered = set()
            for seg in _SEGMENT_SPLIT_RE.split(st.get("cmd") or "")[:40]:
                for h in _segment_write_hosts(seg):
                    out.add((_verb(seg), h, _path_prefix(seg, h)))
                    covered.add(h)
            # A write known only from a tool's ``method`` argument.
            for h in written:
                if h not in covered:
                    out.add(("WRITE", h, ""))
    except Exception:
        pass
    return sorted(out)


def fingerprint_key(fp) -> str:
    """``PUT artifactory.internal/artifactory/github-remote-cache``."""
    verb, host, prefix = fp
    return f"{verb} {host}{prefix}"[:300]


def _bare(sid: str) -> str:
    """``claude_code:abc`` -> ``abc``. The subagent table may hold either."""
    head, sep, tail = str(sid or "").partition(":")
    return tail if sep and head.replace("_", "").isalnum() else str(sid or "")


def _family(sid: str, edges: dict) -> str:
    """Walk bare-id parent ``edges`` to the root. Depth-bounded. Sessions on a
    parent cycle are one family, named by the cycle's smallest member, so
    every member resolves to the same root whichever one the walk starts at."""
    cur = _bare(sid)
    path = [cur]
    index = {cur: 0}
    for _ in range(_MAX_PARENT_DEPTH):
        parent = edges.get(cur)
        if not parent:
            return cur
        if parent in index:
            return min(path[index[parent]:])
        index[parent] = len(path)
        path.append(parent)
        cur = parent
    return cur


def coordinated_action(fingerprints_by_session: dict, *,
                       parents: Optional[dict] = None,
                       history: Optional[dict] = None,
                       history_since_ms: Optional[float] = None,
                       now: Optional[float] = None,
                       min_families: Optional[int] = None,
                       settle_hours: Optional[float] = None) -> list:
    """One incident per unusual fingerprint shared by enough unrelated families.

    ``fingerprints_by_session``: ``{session_id: [(verb, host, prefix), ...]}``
    for the recently active sessions. ``parents``: ``{child_id: parent_id}``.
    ``history``: ``{fingerprint_key: first_seen_ms}`` from the node's memory.
    ``history_since_ms``: when that memory started; ``None`` means it has not.

    Each incident carries ``participants``, the session ids involved, so the
    caller can attach it to each of their Guard rows. Never raises.
    """
    try:
        now_s = time.time() if now is None else float(now)
        settle = EGRESS_SETTLE_HOURS if settle_hours is None else float(settle_hours)
        cutoff_ms = (now_s - max(0.0, settle) * 3600) * 1000
        if history_since_ms is None or float(history_since_ms) > cutoff_ms:
            return []   # not watching long enough to call anything unusual
        hist = history if isinstance(history, dict) else {}
        # Bare ids on both sides: the subagents table and the sessions table
        # may disagree about a ``<runtime>:`` prefix.
        edges = {_bare(k): _bare(v) for k, v in (parents or {}).items()
                 if k and v} if isinstance(parents, dict) else {}
        need = max(2, int(COORD_MIN_FAMILIES if min_families is None else min_families))

        groups: dict = {}
        for sid, fps in (fingerprints_by_session or {}).items():
            fam = _family(sid, edges)
            for fp in fps or ():
                g = groups.setdefault(fingerprint_key(fp), {"fp": tuple(fp), "families": {}})
                g["families"].setdefault(fam, set()).add(sid)

        out = []
        for key, g in groups.items():
            families = g["families"]
            if len(families) < need:
                continue
            seen = hist.get(key)
            if seen is not None:
                try:
                    if float(seen) <= cutoff_ms:
                        continue   # the node has long known this; it is normal
                except (TypeError, ValueError):
                    continue
            sessions = sorted({s for ss in families.values() for s in ss})
            verb, host, prefix = g["fp"]
            where = f"{host}{prefix}"
            if seen is None:
                history_line = "This node has no record of that action before now. "
            else:
                mins = max(1, int((now_s * 1000 - float(seen)) / 60000))
                history_line = (f"This node first saw it {mins} min ago, inside the "
                                f"{settle:g}h window before an action counts as normal. ")
            out.append({
                "kind": "coordinated_action",
                "session_id": sessions[0],
                "runtime": "fleet",
                "severity": "warning",
                "title": f"{len(families)} unrelated sessions sent {verb} to {where}",
                "detail": (f"{len(families)} sessions with no parent or child link "
                           f"between them sent {verb} requests to {where}. "
                           + history_line
                           + "Independent agents converging on one shared "
                             "destination is how a shared cache becomes a "
                             "message board. You can Stop or Pause these agents "
                             "from the ClawMetry dashboard or device."),
                "evidence": {
                    "fingerprint": {"verb": verb, "host": host, "path_prefix": prefix},
                    "fingerprint_key": key,
                    "families": len(families),
                    "sessions": len(sessions),
                    "session_ids": sessions[:_MAX_SESSION_IDS],
                    "threshold": need,
                    "first_seen_by_node": int(float(seen)) if seen is not None else None,
                    "settle_hours": settle,
                    "observed": "tool_arguments",
                },
                "first_bad_step": None,
                "participants": sessions,
            })
        out.sort(key=lambda inc: -inc["evidence"]["families"])
        return out
    except Exception:
        return []
