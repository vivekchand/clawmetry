"""Pull-request provenance: which agent sessions wrote which changed files.

REQ-OBS-PRP-001 (Software Factory requirement 4e224b46-71a6-4d32-933d-7fb6bfde30d0),
vivekchand/clawmetry#5946.

A reviewer wants AI-assisted changes flagged where review already happens: the
pull request, its checks and its code-scanning annotations. ClawMetry already
knows which session wrote a file, which runtime and model it used, what it cost
and which Guard findings it raised. This module turns that into the formats a
pipeline consumes, and nothing more:

* a **provenance bundle** (JSON) the developer's machine exports, because the
  agent's local store never exists on a CI runner;
* **SARIF 2.1.0**, where each Guard finding of a linked session is a result on
  the files that session wrote, and where findings from the scanners a team
  already runs (Semgrep, Snyk, CodeQL, ...) are reproduced with the session
  that touched the file attached;
* a **markdown** summary for one pull-request comment, updated in place;
* an **opt-in gate** whose every decision records who, when, which rule
  version, which head commit and which exceptions applied.

What it is not
--------------
ClawMetry is not a code scanner. Nothing here judges code content; the only
findings are Guard findings (about what an agent *did*) and findings a real
scanner produced. A file-to-session link is **association**, not proof that a
prompt caused a vulnerability, so every link and every annotation carries its
``basis``:

``commit_trailer``  a commit in the range carries ``Clawmetry-Session: <id>``
                    (written by ``clawmetry trace init``) and changed the file.
                    Declared, but a human may have edited lines in that commit.
``observed_write``  the session's own transcript holds a write tool call
                    (Write / Edit / apply_patch / ...) on that path before the
                    head commit was made. Observed, but a later human edit is
                    not excluded.

Nothing a session was *asked* is ever emitted: no prompt text, no tool output.
Scanner text that is copied through passes secret redaction, and Guard finding
titles pass the stricter publication redaction PR Trace uses.

Pure by design: git and the store are reached only through the small functions
at the bottom (``git_*`` and :func:`collect_from_store`), so the linking,
bundle, SARIF, markdown and gate logic is testable without either.
"""

from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import json
import logging
import os
import re
from typing import Any, Iterable

logger = logging.getLogger("clawmetry.pr_provenance")

#: Bumped whenever linking, severity mapping or gate semantics change, and
#: recorded on every bundle, SARIF run and gate decision so a reader can tell
#: which rules produced a verdict.
RULE_VERSION = "clawmetry-pr-provenance/1"

BUNDLE_KIND = "clawmetry.pr_provenance"
BUNDLE_VERSION = 1

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"

COMMENT_MARKER = "<!-- clawmetry-pr-provenance -->"

BASIS_TRAILER = "commit_trailer"
BASIS_WRITE = "observed_write"

#: What the bundle digest is and is not. Printed and embedded so nobody reads
#: a matching digest as a signature.
DIGEST_NOTE = (
    "sha256 over the bundle content: detects a bundle edited after export. "
    "It is an integrity check, not proof of authenticity; authenticity rests "
    "on where the bundle was stored (for example the CI artifact store)."
)

PROVENANCE_RULE_ID = "clawmetry/agent-provenance"

#: Severity ranks shared by Guard findings and scanner findings.
SEVERITY_RANK = {"note": 1, "warning": 2, "critical": 3}
GATE_THRESHOLDS = ("warning", "critical")
EVIDENCE_BEHAVIOURS = ("fail", "pass")

#: Evidence states. Only ``ok`` means every commit in the range was examined
#: by whoever produced the evidence.
EVIDENCE_OK = "ok"
EVIDENCE_PARTIAL = "partial"    # commits the bundle never saw, or a read limit cut it short
EVIDENCE_STALE = "stale"        # older than the operator's freshness window
EVIDENCE_INVALID = "invalid"    # digest mismatch, wrong kind, or another change's bundle
EVIDENCE_MISSING = "missing"    # no bundle and no store

#: Read limits. Hitting any of them is recorded as an evidence gap, which makes
#: the evidence ``partial`` (AC-OBS-PRP-001.13): a gate must never pass on
#: evidence the report did not read.
_MAX_COMMITS = 500
_MAX_SESSION_ROWS = 1000
_MAX_SESSIONS = 50
_MAX_EVENTS_PER_PAGE = 5000
_MAX_EVENT_PAGES = 10
_MAX_INCIDENTS_PER_SESSION = 200
_PATH_KEYS = ("file_path", "path", "filename", "notebook_path", "target_file")
_PATCH_HEADER = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File: (.+?)\s*$|^\*\*\* Move to: (.+?)\s*$|^\+\+\+ b/(.+?)\s*$",
    re.MULTILINE,
)
_TOOL_EVENT_TYPES = ("tool.call", "toolcall", "tool_use", "tool_call")

_DEFAULT_WRITE_TOOLS = (
    "write", "edit", "apply_patch", "applypatch", "str_replace", "create_file",
    "multiedit", "notebookedit", "patch_file", "write_file", "save_file",
)


class GateConfigError(ValueError):
    """The gate was enabled without the choices it needs to be honest."""


# ── small helpers ──────────────────────────────────────────────────────────

def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


def _iso(value: _dt.datetime) -> str:
    return value.astimezone(_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> _dt.datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        try:
            return _dt.datetime.fromtimestamp(float(value), tz=_dt.timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    try:
        text = str(value).strip().replace("Z", "+00:00")
        parsed = _dt.datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = _dt.datetime.combine(_dt.date.fromisoformat(str(value).strip()),
                                          _dt.time())
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_dt.timezone.utc)
    return parsed


def _as_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return {}
    if isinstance(value, str) and value:
        try:
            out = json.loads(value)
            return out if isinstance(out, dict) else {}
        except ValueError:
            return {}
    return {}


def _redact_secret(text: Any) -> Any:
    """Secret redaction for text copied from a scanner. Fails closed."""
    if not isinstance(text, str) or not text:
        return text
    try:
        from clawmetry import redaction
        return redaction.redact_text(text)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("redaction failed: %s", exc)
        return "[REDACTION FAILED - TEXT WITHHELD]"


def _redact_publication(text: Any) -> str:
    """The stricter pass PR Trace applies before anything becomes public."""
    if not isinstance(text, str) or not text:
        return "" if text is None else str(text)
    try:
        from clawmetry import trace_capture
        return trace_capture.redact_for_publication(text)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("publication redaction failed: %s", exc)
        return "[REDACTION FAILED - TEXT WITHHELD]"


def runtime_of(session_id: str) -> str:
    """``claude_code:abc`` -> ``claude_code``; a bare id is OpenClaw's."""
    sid = str(session_id or "")
    return sid.split(":", 1)[0] if ":" in sid else "openclaw"


def severity_of(value: Any) -> str:
    v = str(value or "").strip().lower()
    if v in ("critical", "error", "high"):
        return "critical"
    if v in ("warning", "warn", "medium"):
        return "warning"
    return "note"


def sarif_level(severity: str) -> str:
    return {"critical": "error", "warning": "warning"}.get(severity_of(severity), "note")


def severity_from_sarif_level(level: Any) -> str:
    return {"error": "critical", "warning": "warning"}.get(str(level or "warning").lower(), "note")


# ── observed writes ────────────────────────────────────────────────────────

def _write_vocab() -> tuple:
    try:
        from clawmetry.detectors import WRITE_TOOL_SUBSTRINGS
        return tuple(WRITE_TOOL_SUBSTRINGS) or _DEFAULT_WRITE_TOOLS
    except Exception:
        return _DEFAULT_WRITE_TOOLS


def is_write_tool(name: Any, vocab: Iterable[str] | None = None) -> bool:
    n = str(name or "").strip().lower()
    if not n:
        return False
    return any(s in n for s in (vocab or _write_vocab()))


def _paths_from_input(inp: Any) -> list[str]:
    out: list[str] = []
    if isinstance(inp, str):
        parsed = _as_dict(inp)
        if parsed:
            inp = parsed
        else:
            # A raw patch passed as the whole input (Codex apply_patch).
            for m in _PATCH_HEADER.finditer(inp):
                out.append(next(g for g in m.groups() if g))
            return out
    if not isinstance(inp, dict):
        return out
    for key in _PATH_KEYS:
        v = inp.get(key)
        if isinstance(v, str) and v.strip():
            out.append(v.strip())
            break
    for key in ("patch", "input", "command", "diff"):
        v = inp.get(key)
        if isinstance(v, str) and "\n" in v:
            for m in _PATCH_HEADER.finditer(v):
                out.append(next(g for g in m.groups() if g))
    return out


def iter_tool_calls(event: dict) -> Iterable[tuple]:
    """Yield ``(tool_name, input)`` for every tool call an event describes.

    Probes the four stored shapes the local store's own extractors handle:
    a top-level tool event, ``data.tool_calls[*]`` (family adapters),
    ``data.toolMetas[*]`` and assistant ``message.content`` blocks.
    """
    if not isinstance(event, dict):
        return
    data = _as_dict(event.get("data"))
    etype = str(event.get("event_type") or "").lower()
    if etype in _TOOL_EVENT_TYPES:
        name = (data.get("name") or data.get("tool_name") or data.get("tool")
                or event.get("tool_name"))
        yield name, data.get("input") if data.get("input") is not None else data.get("arguments")
    for blk in data.get("tool_calls") or []:
        if isinstance(blk, dict):
            yield blk.get("name") or blk.get("tool_name"), blk.get("input") or blk.get("arguments")
    for meta in data.get("toolMetas") or []:
        if isinstance(meta, dict):
            yield meta.get("name") or meta.get("tool") or meta.get("toolName"), meta.get("input")
    msg = data.get("message")
    if isinstance(msg, dict) and msg.get("role") == "assistant":
        for blk in msg.get("content") or []:
            if isinstance(blk, dict) and blk.get("type") in ("toolCall", "tool_use"):
                yield blk.get("name"), blk.get("input") or blk.get("arguments")


def repo_relative(path: str, repo_root: str, cwd: str | None = None,
                  relative_without_cwd: bool = True) -> str | None:
    """Normalise a tool's path argument to a repository-relative POSIX path.

    Returns None when the path lies outside the repository. A relative path
    with no known working directory is taken as repository-relative, which is
    what an agent running at the repository root writes, unless
    ``relative_without_cwd`` is False: then it cannot be placed and is None.
    """
    p = str(path or "").strip()
    if not p:
        return None
    if p.startswith("file://"):
        p = p[len("file://"):]
    if not os.path.isabs(p):
        if cwd:
            p = os.path.join(cwd, p)
        elif not relative_without_cwd:
            return None
        else:
            rel = os.path.normpath(p).replace(os.sep, "/")
            return None if rel.startswith("..") or rel == "." else rel
    root = os.path.normpath(repo_root)
    candidates = {(os.path.normpath(p), root)}
    try:
        candidates.add((os.path.realpath(p), os.path.realpath(root)))
    except OSError:
        pass
    for full, base in candidates:
        try:
            rel = os.path.relpath(full, base)
        except ValueError:  # different drive on Windows
            continue
        if not rel.startswith("..") and rel != ".":
            return rel.replace(os.sep, "/")
    return None


def observed_writes(events: Iterable[dict], repo_root: str, *, cwd: str | None = None,
                    until: _dt.datetime | None = None, relative_without_cwd: bool = True,
                    unplaced: set | None = None) -> set:
    """Repository-relative paths a session wrote, from its own events.

    ``until`` drops events after the head commit: a write made after the
    change was committed cannot be in it. With ``relative_without_cwd``
    False and no ``cwd``, relative paths are not attributed; they are added,
    normalised, to ``unplaced`` so the caller can report what it could not place.
    """
    vocab = _write_vocab()
    out: set = set()
    for ev in events or ():
        if until is not None:
            ts = _parse_time(ev.get("ts"))
            if ts is not None and ts > until:
                continue
        for name, inp in iter_tool_calls(ev):
            if not is_write_tool(name, vocab):
                continue
            for raw in _paths_from_input(inp):
                rel = repo_relative(raw, repo_root, cwd, relative_without_cwd)
                if rel:
                    out.add(rel)
                elif unplaced is not None and not cwd and not relative_without_cwd:
                    guess = repo_relative(raw, repo_root, None, True)
                    if guess and not os.path.isabs(str(raw).strip()):
                        unplaced.add(guess)
    return out


# ── linking ────────────────────────────────────────────────────────────────

def link_files(changed_files: Iterable[str], commits: Iterable[dict],
               writes_by_session: dict) -> dict:
    """``{path: [{session_id, basis}]}`` for every changed file.

    A file no session is linked to maps to ``[]`` so it is reported as
    unattributed rather than dropped (AC-OBS-PRP-001.1).
    """
    files = list(dict.fromkeys(changed_files))
    wanted = set(files)
    links: dict = {f: [] for f in files}

    def _add(path: str, sid: str, basis: str) -> None:
        row = {"session_id": sid, "basis": basis}
        if path in links and row not in links[path]:
            links[path].append(row)

    for c in commits or ():
        sid = c.get("session_id")
        if not sid:
            continue
        for path in c.get("files") or ():
            if path in wanted:
                _add(path, sid, BASIS_TRAILER)
    for sid, paths in (writes_by_session or {}).items():
        for path in sorted(paths or ()):
            if path in wanted:
                _add(path, sid, BASIS_WRITE)
    return links


# ── bundle ─────────────────────────────────────────────────────────────────

def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      default=str).encode("utf-8")


def bundle_digest(bundle: dict) -> str:
    body = {k: v for k, v in bundle.items() if k not in ("digest", "digest_note")}
    return "sha256:" + hashlib.sha256(_canonical(body)).hexdigest()


def _incident_row(inc: dict) -> dict:
    details = inc.get("details") if isinstance(inc.get("details"), dict) else {}
    kind = str(inc.get("kind") or str(inc.get("signature") or "").replace("daemon_detect_", "")
               or "finding")
    spend = details.get("spend_at_risk_usd")
    try:
        spend = round(float(spend), 4) if spend is not None else None
    except (TypeError, ValueError):
        spend = None
    return {
        "kind": re.sub(r"[^a-z0-9_.-]", "_", kind.lower())[:64] or "finding",
        "severity": severity_of(inc.get("severity")),
        "title": _redact_publication(str(inc.get("title") or details.get("message") or kind))[:300],
        "first_seen": str(inc.get("first_seen") or ""),
        "last_seen": str(inc.get("last_seen") or ""),
        "spend_at_risk_usd": spend,
        "spend_basis": str(details.get("spend_basis") or "unknown") if spend is not None else "unknown",
        "signature": str(inc.get("signature") or "")[:128],
    }


def build_bundle(*, project: str | None, base_sha: str, head_sha: str, commits: list,
                 changed_files: list, links: dict, sessions: dict,
                 incidents_by_session: dict, generated_at: _dt.datetime | None = None,
                 generated_by: str | None = None,
                 evidence_gaps: Iterable[str] | None = None) -> dict:
    """Assemble the exportable bundle. No prompts, no tool output, no paths
    outside the repository: it may be committed to a public pull request.

    ``sessions`` maps a session id to ``{runtime, models, cost_usd,
    started_at}``; ``cost_usd`` of None means the cost is unknown and is
    labelled so rather than rendered as zero. ``evidence_gaps`` are the
    sentences :func:`collect_from_store` returned for read limits it hit; a
    bundle carrying any is ``partial`` evidence wherever it is read
    (AC-OBS-PRP-001.13). They name no session.
    """
    linked_ids = sorted({row["session_id"] for rows in links.values() for row in rows})
    sess_out = []
    for sid in linked_ids:
        meta = sessions.get(sid) or {}
        cost = meta.get("cost_usd")
        try:
            cost = round(float(cost), 4) if cost is not None else None
        except (TypeError, ValueError):
            cost = None
        sess_out.append({
            "session_id": sid,
            "runtime": str(meta.get("runtime") or runtime_of(sid)),
            "models": sorted({str(m) for m in (meta.get("models") or []) if m}),
            "cost_usd": cost,
            "cost_basis": "measured" if cost is not None else "unknown",
            "started_at": str(meta.get("started_at") or ""),
            "in_store": bool(meta),
            "incidents": [_incident_row(i) for i in (incidents_by_session.get(sid) or [])],
            "evidence_ref": f"clawmetry://session/{sid}",
        })
    bundle = {
        "kind": BUNDLE_KIND,
        "bundle_version": BUNDLE_VERSION,
        "rule_version": RULE_VERSION,
        "project": project,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "generated_at": _iso(generated_at or _now()),
        "generated_by": generated_by or "",
        "commits": [
            {"sha": c.get("sha"), "session_id": c.get("session_id") or None,
             "files": sorted(c.get("files") or [])}
            for c in commits
        ],
        "changed_files": sorted(changed_files),
        "links": {path: rows for path, rows in sorted(links.items())},
        "sessions": sess_out,
        "evidence_gaps": list(dict.fromkeys(str(g) for g in (evidence_gaps or ()) if g)),
    }
    bundle["digest"] = bundle_digest(bundle)
    bundle["digest_note"] = DIGEST_NOTE
    return bundle


def verify_bundle(bundle: Any) -> tuple:
    """``(ok, reason)``. A bundle that fails here is invalid evidence."""
    if not isinstance(bundle, dict):
        return False, "not a JSON object"
    if bundle.get("kind") != BUNDLE_KIND:
        return False, "not a ClawMetry PR provenance bundle"
    if bundle.get("bundle_version") != BUNDLE_VERSION:
        return False, f"unsupported bundle_version {bundle.get('bundle_version')!r}"
    if bundle.get("digest") != bundle_digest(bundle):
        return False, "digest does not match content (edited after export)"
    return True, ""


def assess_evidence(bundle: dict | None, *, range_shas: list, head_sha: str,
                    now: _dt.datetime | None = None, max_age_hours: float | None = None,
                    ignored_shas: Iterable[str] = ()) -> dict:
    """Bind a bundle to the change being evaluated (AC-OBS-PRP-001.7).

    ``range_shas`` are the commits CI sees for this change. A bundle that
    covers none of them belongs to another change (substitution); one that
    misses some was exported before those commits existed.
    """
    out = {"status": EVIDENCE_MISSING, "reason": "", "covered": 0, "uncovered": [],
           "head_sha": head_sha, "bundle_head_sha": None, "generated_at": None,
           "digest": None, "digest_note": DIGEST_NOTE}
    if bundle is None:
        out["reason"] = "no provenance bundle and no local store"
        return out
    ok, why = verify_bundle(bundle)
    out["bundle_head_sha"] = bundle.get("head_sha") if isinstance(bundle, dict) else None
    out["digest"] = bundle.get("digest") if isinstance(bundle, dict) else None
    if not ok:
        out.update(status=EVIDENCE_INVALID, reason=why)
        return out
    out["generated_at"] = bundle.get("generated_at")
    ignored = set(ignored_shas or ())
    wanted = [s for s in range_shas if s not in ignored]
    covered = {c.get("sha") for c in bundle.get("commits") or []}
    hit = [s for s in wanted if s in covered]
    missing = [s for s in wanted if s not in covered]
    out["covered"] = len(hit)
    out["uncovered"] = missing
    if wanted and not hit:
        out.update(status=EVIDENCE_INVALID,
                   reason="bundle covers none of this change's commits (it belongs to another change)")
        return out
    stray = [s for s in covered if s and s not in set(range_shas)]
    if stray and not hit:
        out.update(status=EVIDENCE_INVALID, reason="bundle commits are not in this change")
        return out
    if max_age_hours is not None:
        gen = _parse_time(bundle.get("generated_at"))
        age_limit = _dt.timedelta(hours=float(max_age_hours))
        if gen is None or (now or _now()) - gen > age_limit:
            out.update(status=EVIDENCE_STALE,
                       reason=f"bundle is older than {max_age_hours:g} hours")
            return out
    reasons = []
    if missing:
        reasons.append(f"{len(missing)} commit(s) in this change are not covered by the bundle")
    # The exporter hit a read limit: what it did not read cannot be "ok".
    gaps = [str(g) for g in (bundle.get("evidence_gaps") or []) if g]
    out["gaps"] = gaps
    reasons.extend(gaps)
    if reasons:
        out.update(status=EVIDENCE_PARTIAL, reason="; ".join(reasons))
        return out
    out.update(status=EVIDENCE_OK, reason="")
    return out


def with_gaps(evidence: dict, gaps: Iterable[str]) -> dict:
    """Downgrade ``ok`` evidence to ``partial`` when there are gaps, and add
    their reasons to evidence that is already partial. Stale, invalid and
    missing evidence keep their status: they are already not ``ok``."""
    new = [str(g) for g in (gaps or ()) if g and str(g) not in (evidence.get("gaps") or [])]
    if not new:
        return evidence
    evidence["gaps"] = list(evidence.get("gaps") or []) + new
    if evidence.get("status") in (EVIDENCE_OK, EVIDENCE_PARTIAL):
        reason = "; ".join([r for r in [evidence.get("reason") or ""] if r] + new)
        evidence.update(status=EVIDENCE_PARTIAL, reason=reason)
    return evidence


# ── SARIF ──────────────────────────────────────────────────────────────────

def _session_index(bundle: dict) -> dict:
    return {s.get("session_id"): s for s in bundle.get("sessions") or []}


def _links_by_path(bundle: dict) -> dict:
    return {p: rows for p, rows in (bundle.get("links") or {}).items() if rows}


def _link_props(path: str, bundle: dict) -> list:
    """One entry per session linked to ``path``, with every basis for it.

    A session can be linked to a file twice (its commit names it AND its own
    write was observed). That is one session and one annotation, carrying
    both bases, not two annotations of the same finding.
    """
    index = _session_index(bundle)
    grouped: dict = {}
    for row in (bundle.get("links") or {}).get(path) or []:
        sid = row["session_id"]
        if sid not in grouped:
            s = index.get(sid) or {}
            grouped[sid] = {
                "session_id": sid,
                "runtime": s.get("runtime") or runtime_of(sid),
                "models": s.get("models") or [],
                "basis": [],
                "association_only": True,
                "evidence_ref": s.get("evidence_ref") or f"clawmetry://session/{sid}",
            }
        if row["basis"] not in grouped[sid]["basis"]:
            grouped[sid]["basis"].append(row["basis"])
    return list(grouped.values())


def _location(path: str) -> dict:
    # GitHub code scanning needs a region to place an annotation; the finding
    # is about the file, so it anchors on line 1.
    return {"physicalLocation": {"artifactLocation": {"uri": path},
                                 "region": {"startLine": 1}}}


def _fingerprint(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:32]


def _basis_words(basis: Any) -> str:
    words = {"commit_trailer": "a commit trailer names the session",
             "observed_write": "the session's own write tool call on this path"}
    items = basis if isinstance(basis, list) else [basis]
    return " and ".join(words.get(b, str(b)) for b in items)


def _clawmetry_run(bundle: dict) -> dict:
    index = _session_index(bundle)
    rules: dict = {PROVENANCE_RULE_ID: {
        "id": PROVENANCE_RULE_ID,
        "name": "AgentSessionProvenance",
        "shortDescription": {"text": "File written by an AI agent session"},
        "fullDescription": {"text": (
            "An agent session observed by ClawMetry is linked to this file. The link is "
            "association, not proof that the session caused any finding on the file.")},
        "defaultConfiguration": {"level": "note"},
        "properties": {"tags": ["ai-provenance"]},
    }}
    results = []
    for path in sorted(_links_by_path(bundle)):
        for link in _link_props(path, bundle):
            sid = link["session_id"]
            s = index.get(sid) or {}
            model = ", ".join(link["models"]) or "model not recorded"
            results.append({
                "ruleId": PROVENANCE_RULE_ID,
                "level": "note",
                "message": {"text": (
                    f"Written by agent session {sid} ({link['runtime']}, {model}); "
                    f"basis: {_basis_words(link['basis'])}. Association, not proof of cause.")},
                "locations": [_location(path)],
                "partialFingerprints": {"clawmetryProvenance/v1": _fingerprint(
                    PROVENANCE_RULE_ID, path, sid)},
                "properties": {"clawmetry": [link]},
            })
            for inc in s.get("incidents") or []:
                rule_id = f"clawmetry/guard/{inc['kind']}"
                rules.setdefault(rule_id, {
                    "id": rule_id,
                    "name": "Guard" + "".join(w.title() for w in inc["kind"].split("_")),
                    "shortDescription": {"text": f"Guard finding: {inc['kind']}"},
                    "fullDescription": {"text": (
                        "A ClawMetry Guard detector flagged what this agent session did while "
                        "it ran. It describes the session's behaviour, not the file's code.")},
                    "defaultConfiguration": {"level": sarif_level(inc["severity"])},
                    "properties": {"tags": ["ai-provenance", "guard"]},
                })
                spend = ""
                if inc.get("spend_at_risk_usd") is not None:
                    spend = f" Spend at risk ${inc['spend_at_risk_usd']:.2f} ({inc['spend_basis']})."
                results.append({
                    "ruleId": rule_id,
                    "level": sarif_level(inc["severity"]),
                    "message": {"text": (
                        f"Guard {inc['severity']}: {inc['title']} (session {sid}, "
                        f"linked to this file by {_basis_words(link['basis'])}).{spend}")},
                    "locations": [_location(path)],
                    "partialFingerprints": {"clawmetryGuard/v1": _fingerprint(
                        rule_id, path, sid, inc.get("signature") or "")},
                    "properties": {"clawmetry": {
                        "session_id": sid, "basis": link["basis"],
                        "association_only": True, "severity": inc["severity"],
                        "first_seen": inc.get("first_seen"), "last_seen": inc.get("last_seen"),
                        "evidence_ref": (s.get("evidence_ref") or "")
                        + (f"#incident={inc['signature']}" if inc.get("signature") else ""),
                    }},
                })
    return {
        "tool": {"driver": {
            "name": "ClawMetry agent provenance",
            "informationUri": "https://github.com/vivekchand/clawmetry",
            "semanticVersion": _package_version(),
            "rules": list(rules.values()),
        }},
        "automationDetails": {"id": "clawmetry-pr-provenance/"},
        "results": results,
        "properties": {"clawmetry": {
            "rule_version": RULE_VERSION, "base_sha": bundle.get("base_sha"),
            "head_sha": bundle.get("head_sha"), "bundle_digest": bundle.get("digest"),
            "unattributed_files": sorted(p for p, r in (bundle.get("links") or {}).items() if not r),
        }},
    }


def _package_version() -> str:
    try:
        from clawmetry import __version__
        return str(__version__)
    except Exception:
        return "0"


def _redact_tree(node: Any) -> Any:
    """Redact every ``text`` / ``markdown`` string in a SARIF subtree."""
    if isinstance(node, dict):
        return {k: (_redact_secret(v) if k in ("text", "markdown") and isinstance(v, str)
                    else _redact_tree(v)) for k, v in node.items()}
    if isinstance(node, list):
        return [_redact_tree(v) for v in node]
    return node


def _result_path(result: dict, repo_root: str | None) -> str | None:
    for loc in result.get("locations") or []:
        uri = (((loc or {}).get("physicalLocation") or {}).get("artifactLocation") or {}).get("uri")
        if not isinstance(uri, str) or not uri:
            continue
        uri = uri.replace("\\", "/")
        if uri.startswith("file://"):
            uri = uri[len("file://"):]
        if uri.startswith("/") and repo_root:
            rel = repo_relative(uri, repo_root)
            if rel:
                return rel
        while uri.startswith("./"):
            uri = uri[2:]
        return uri.lstrip("/") if not repo_root else uri
    return None


def annotate_scanner_runs(scanner_sarif: Iterable[dict], bundle: dict,
                          repo_root: str | None = None) -> tuple:
    """Reproduce supplied scanner runs, annotating findings on linked files.

    Returns ``(runs, annotated)`` where ``annotated`` lists the
    ``{tool, rule_id, path, severity, links}`` of every finding that landed
    on a file an agent session is linked to. Findings on other files are
    reproduced unchanged apart from redaction (AC-OBS-PRP-001.4).
    """
    linked = _links_by_path(bundle)
    runs_out: list = []
    annotated: list = []
    for doc in scanner_sarif or ():
        if not isinstance(doc, dict):
            continue
        for run in doc.get("runs") or []:
            if not isinstance(run, dict):
                continue
            run = _redact_tree(copy.deepcopy(run))
            tool = (((run.get("tool") or {}).get("driver") or {}).get("name")) or "scanner"
            for res in run.get("results") or []:
                if not isinstance(res, dict):
                    continue
                path = _result_path(res, repo_root)
                if not path or path not in linked:
                    continue
                props = _link_props(path, bundle)
                # SARIF result property bag, not any config file.
                res.setdefault("properties", {}).update({"clawmetry": props})
                sessions = ", ".join(
                    f"{p['session_id']} ({p['runtime']}, {'+'.join(p['basis'])})" for p in props)
                msg = res.setdefault("message", {})
                if isinstance(msg.get("text"), str):
                    msg["text"] = (msg["text"].rstrip()
                                   + f" [ClawMetry: file linked to agent session {sessions}; "
                                   "association, not proof of cause]")
                annotated.append({
                    "tool": tool, "rule_id": str(res.get("ruleId") or ""), "path": path,
                    "severity": severity_from_sarif_level(res.get("level")),
                    "links": props,
                })
            runs_out.append(run)
    return runs_out, annotated


def to_sarif(bundle: dict, scanner_runs: Iterable[dict] = ()) -> dict:
    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [_clawmetry_run(bundle)] + list(scanner_runs or ()),
    }


# ── gate ───────────────────────────────────────────────────────────────────

def gate_findings(bundle: dict, annotated: Iterable[dict]) -> list:
    """Every finding the gate may act on: Guard findings of linked sessions,
    on each linked file, plus scanner findings on linked files."""
    index = _session_index(bundle)
    out = []
    for path in sorted(_links_by_path(bundle)):
        for link in _link_props(path, bundle):
            sid = link["session_id"]
            for inc in (index.get(sid) or {}).get("incidents") or []:
                out.append({"source": "guard", "rule_id": f"clawmetry/guard/{inc['kind']}",
                            "path": path, "session_id": sid,
                            "severity": inc["severity"], "tool": "ClawMetry agent provenance"})
    for a in annotated or ():
        for link in a.get("links") or [{"session_id": None}]:
            out.append({"source": "scanner", "rule_id": a["rule_id"], "path": a["path"],
                        "session_id": link.get("session_id"), "severity": a["severity"],
                        "tool": a["tool"]})
    return out


def load_exceptions(doc: Any) -> list:
    if doc is None:
        return []
    rows = doc.get("exceptions") if isinstance(doc, dict) else doc
    return [r for r in (rows or []) if isinstance(r, dict)]


def _exception_problem(exc: dict) -> str:
    for key in ("id", "rule", "expires", "approved_by", "reason"):
        if not str(exc.get(key) or "").strip():
            return f"missing {key}"
    if _parse_time(exc.get("expires")) is None:
        return "expires is not a date"
    return ""


def _exception_matches(exc: dict, finding: dict) -> bool:
    if str(exc.get("rule")) != finding["rule_id"]:
        return False
    for key in ("path", "session_id", "tool"):
        want = exc.get(key)
        if want not in (None, "") and str(want) != str(finding.get(key) or ""):
            return False
    return True


def evaluate_gate(*, bundle: dict | None, evidence: dict, annotated: Iterable[dict] = (),
                  fail_on: str | None = None, on_missing_evidence: str | None = None,
                  exceptions: Iterable[dict] = (), actor: str | None = None,
                  now: _dt.datetime | None = None) -> dict:
    """The gate decision, with everything an auditor needs to re-derive it.

    Off unless ``fail_on`` is given. Enabled without an explicit
    ``on_missing_evidence`` it refuses to run: a default here would silently
    block or silently allow a change (AC-OBS-PRP-001.8).
    """
    now = now or _now()
    head = (evidence or {}).get("head_sha")
    decision = {
        "rule_version": RULE_VERSION,
        "enabled": bool(fail_on),
        "outcome": "disabled",
        "threshold": fail_on or None,
        "evidence_behaviour": on_missing_evidence or None,
        "evidence_status": (evidence or {}).get("status"),
        "evidence_reason": (evidence or {}).get("reason") or "",
        "actor": (actor or "").strip() or "unknown",
        "decided_at": _iso(now),
        "head_sha": head,
        "blocking": [],
        "exceptions_applied": [],
        "exceptions_expired": [],
        "exceptions_rejected": [],
        "reasons": [],
    }
    if not fail_on:
        decision["reasons"].append("gate not enabled; report only")
        return decision
    if fail_on not in GATE_THRESHOLDS:
        raise GateConfigError(f"--fail-on must be one of {', '.join(GATE_THRESHOLDS)}")
    if on_missing_evidence not in EVIDENCE_BEHAVIOURS:
        raise GateConfigError(
            "the gate is enabled but no behaviour for missing, stale or invalid evidence was "
            "chosen; pass --on-missing-evidence fail or --on-missing-evidence pass")

    failed = False
    if decision["evidence_status"] != EVIDENCE_OK:
        if on_missing_evidence == "fail":
            failed = True
            decision["reasons"].append(
                f"evidence {decision['evidence_status']}: {decision['evidence_reason']}")
        else:
            decision["reasons"].append(
                f"evidence {decision['evidence_status']} allowed by --on-missing-evidence pass")

    live, expired = [], []
    for exc in exceptions or ():
        problem = _exception_problem(exc)
        if problem:
            decision["exceptions_rejected"].append({"id": exc.get("id"), "problem": problem})
            continue
        if _parse_time(exc["expires"]) <= now:
            expired.append(exc)
        else:
            live.append(exc)
    decision["exceptions_expired"] = [
        {"id": e["id"], "rule": e["rule"], "expires": str(e["expires"]),
         "approved_by": e["approved_by"]} for e in expired]

    threshold = SEVERITY_RANK[fail_on]
    applied: dict = {}
    for finding in gate_findings(bundle or {}, annotated):
        if SEVERITY_RANK.get(finding["severity"], 1) < threshold:
            continue
        match = next((e for e in live if _exception_matches(e, finding)), None)
        if match is not None:
            applied.setdefault(match["id"], {
                "id": match["id"], "rule": match["rule"], "expires": str(match["expires"]),
                "approved_by": match["approved_by"], "reason": _redact_secret(match["reason"]),
                "findings": 0})
            applied[match["id"]]["findings"] += 1
            continue
        failed = True
        decision["blocking"].append(finding)
    decision["exceptions_applied"] = list(applied.values())
    if decision["blocking"]:
        decision["reasons"].append(
            f"{len(decision['blocking'])} finding(s) at or above {fail_on} on agent-linked files")
    decision["outcome"] = "fail" if failed else "pass"
    return decision


# ── markdown ───────────────────────────────────────────────────────────────

def _md(text: Any) -> str:
    return str(text if text is not None else "").replace("|", "\\|").replace("\n", " ")


def render_markdown(bundle: dict, evidence: dict, decision: dict,
                    annotated: Iterable[dict] = ()) -> str:
    annotated = list(annotated or ())
    links = bundle.get("links") or {}
    linked = {p: r for p, r in links.items() if r}
    unattributed = sorted(p for p, r in links.items() if not r)
    lines = [
        "### ClawMetry: agent sessions in this change",
        "",
        f"{len(linked)} of {len(links)} changed file(s) are linked to an agent session. "
        "A link is association, not proof that a session caused a finding.",
        "",
    ]
    if bundle.get("sessions"):
        lines += ["| session | runtime | model | cost | Guard findings | files |",
                  "|---|---|---|---|---|---|"]
        for s in bundle["sessions"]:
            files = sorted(p for p, rows in linked.items()
                           if any(r["session_id"] == s["session_id"] for r in rows))
            cost = (f"${s['cost_usd']:.2f} ({s['cost_basis']})" if s.get("cost_usd") is not None
                    else "unknown")
            incs = s.get("incidents") or []
            worst = max((SEVERITY_RANK.get(i["severity"], 1) for i in incs), default=0)
            worst_txt = {3: "critical", 2: "warning", 1: "note"}.get(worst, "")
            inc_txt = f"{len(incs)} ({worst_txt})" if incs else "0"
            lines.append(
                f"| `{_md(s['session_id'])}` | {_md(s['runtime'])} | "
                f"{_md(', '.join(s.get('models') or []) or 'not recorded')} | {cost} | "
                f"{inc_txt} | {len(files)} |")
        lines.append("")
    if annotated:
        lines.append(f"{len(annotated)} scanner finding(s) are on agent-linked files; "
                     "each carries its session in the SARIF properties.")
        lines.append("")
    if unattributed:
        shown = ", ".join(f"`{_md(p)}`" for p in unattributed[:20])
        more = f" and {len(unattributed) - 20} more" if len(unattributed) > 20 else ""
        lines += [f"Not linked to any session: {shown}{more}.", ""]
    ev = evidence or {}
    ev_line = f"Evidence: **{ev.get('status')}**"
    if ev.get("reason"):
        ev_line += f" ({_md(ev['reason'])})"
    lines += [ev_line + ".", ""]
    if decision.get("enabled"):
        lines.append(
            f"Gate: **{decision['outcome']}** at threshold `{decision['threshold']}`, "
            f"evidence behaviour `{decision['evidence_behaviour']}`, rule "
            f"`{decision['rule_version']}`, head `{_md((decision.get('head_sha') or '')[:12])}`, "
            f"actor `{_md(decision['actor'])}`, {decision['decided_at']}.")
        if decision.get("blocking"):
            lines.append("")
            for f in decision["blocking"][:20]:
                lines.append(f"- {_md(f['severity'])} `{_md(f['rule_id'])}` on "
                             f"`{_md(f['path'])}` (session `{_md(f.get('session_id'))}`)")
        for e in decision.get("exceptions_applied") or []:
            lines.append(f"- exception `{_md(e['id'])}` applied ({e['findings']} finding(s), "
                         f"approved by {_md(e['approved_by'])}, expires {_md(e['expires'])})")
        for e in decision.get("exceptions_expired") or []:
            lines.append(f"- exception `{_md(e['id'])}` EXPIRED on {_md(e['expires'])}, not applied")
    else:
        lines.append("Gate: not enabled (report only).")
    lines += ["", COMMENT_MARKER]
    return "\n".join(lines)


# ── pull-request comment ───────────────────────────────────────────────────

def upsert_pr_comment(*, repository: str, pr_number: int, token: str, body: str,
                      api_url: str = "https://api.github.com", timeout: int = 30) -> dict:
    """Create the provenance comment, or edit the one carrying the marker.

    One comment per pull request however many times CI runs
    (AC-OBS-PRP-001.11). Returns ``{"ok", "action"}`` or ``{"ok": False,
    "error"}``; never raises.

    Only a comment written by this token's identity is edited, so a person
    who quotes the marker never has their comment overwritten. A personal
    token answers ``GET /user`` with its login; the Actions token cannot,
    and its comments are the ones a bot account wrote.
    """
    import urllib.error
    import urllib.request

    base = api_url.rstrip("/")
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
               "User-Agent": "clawmetry-pr-provenance", "X-GitHub-Api-Version": "2022-11-28"}

    def _call(method: str, url: str, payload: dict | None = None):
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=dict(
            headers, **({"Content-Type": "application/json"} if data else {})))
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return json.loads(raw) if raw else None

    try:
        try:
            me = str((_call("GET", f"{base}/user") or {}).get("login") or "")
        except Exception:
            me = ""

        def _ours(c: dict) -> bool:
            user = c.get("user") if isinstance(c.get("user"), dict) else {}
            if COMMENT_MARKER not in str(c.get("body") or ""):
                return False
            if me:
                return str(user.get("login") or "") == me
            return str(user.get("type") or "") == "Bot"

        existing = None
        for page in range(1, 11):
            rows = _call("GET", f"{base}/repos/{repository}/issues/{int(pr_number)}/comments"
                                f"?per_page=100&page={page}") or []
            existing = next((c for c in rows if _ours(c)), None)
            if existing or len(rows) < 100:
                break
        if existing:
            _call("PATCH", f"{base}/repos/{repository}/issues/comments/{existing['id']}",
                  {"body": body})
            return {"ok": True, "action": "updated", "id": existing["id"]}
        made = _call("POST", f"{base}/repos/{repository}/issues/{int(pr_number)}/comments",
                     {"body": body}) or {}
        return {"ok": True, "action": "created", "id": made.get("id")}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"HTTP {exc.code} from the GitHub API"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


# ── git + store (the only I/O) ─────────────────────────────────────────────
#
# CLAUDE.md: "A user's repository is read, never written." Every git call here
# goes through clawmetry.git_outcomes' chokepoint, which refuses any
# subcommand outside its read-only allowlist and any option that writes a
# file. An UnsafeGitCommand is a programming error and is not swallowed.

def _git(repo: str, *args: str) -> str:
    from clawmetry import git_outcomes

    try:
        out = git_outcomes._git(repo, *args)
    except git_outcomes.UnsafeGitCommand:
        raise
    except Exception as exc:
        logger.warning("git %s failed: %s", " ".join(args), exc)
        return ""
    return out or ""


def git_rev_parse(repo: str, ref: str) -> str:
    return _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").strip()


def git_merge_base(repo: str, a: str, b: str) -> str:
    return _git(repo, "merge-base", a, b).strip()


def git_default_base_ref(repo: str) -> str:
    """The ref a pull request from this checkout targets, asked of the remote."""
    head = _git(repo, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD").strip()
    if head.startswith("refs/remotes/"):
        return head[len("refs/remotes/"):]
    for cand in ("origin/main", "origin/master", "main", "master"):
        if git_rev_parse(repo, cand):
            return cand
    return ""


def git_project(repo: str) -> str | None:
    """``owner/repo`` from ``clawmetry.project`` or the origin remote."""
    configured = _git(repo, "config", "--get", "clawmetry.project").strip()
    if configured:
        return configured
    url = _git(repo, "remote", "get-url", "origin").strip()
    m = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?$", url)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def git_changed_files(repo: str, base: str, head: str) -> list:
    """Files the change touches: the tree diff from the merge base to head,
    which is what a pull request shows."""
    mb = git_merge_base(repo, base, head) or base
    raw = _git(repo, "diff-tree", "-r", "--name-only", "--no-renames", "-z", mb, head)
    return sorted({p.strip("\n") for p in raw.split("\0") if p.strip("\n")})


def git_commits(repo: str, base: str, head: str) -> list:
    """Commits in ``base..head`` (oldest first) with their files and trailer."""
    from clawmetry import trace_stamp

    raw = _git(repo, "log", f"--max-count={_MAX_COMMITS}", "--format=%H%x1f%ct%x1f%B%x1e",
               f"{base}..{head}")
    commits = []
    for rec in raw.split("\x1e"):
        rec = rec.strip("\n")
        if not rec:
            continue
        sha, ct, body = (rec.split("\x1f") + ["", ""])[:3]
        sha = sha.strip()
        files = _git(repo, "log", "-1", "--format=", "--name-only", "--no-renames", "-z", sha)
        commits.append({
            "sha": sha,
            "ts": int(ct) if ct.strip().isdigit() else 0,
            "session_id": trace_stamp.existing_trailer(body),
            "files": sorted({p.strip("\n") for p in files.split("\0") if p.strip("\n")}),
        })
    return list(reversed(commits))


def commit_limit_gap(commits: list) -> str | None:
    """The evidence gap when ``git_commits`` hit its ceiling, else None."""
    if len(commits or ()) >= _MAX_COMMITS:
        return (f"the change has at least {_MAX_COMMITS} commits, the read limit; "
                "older commits were not examined")
    return None


def _session_cwd(store: Any, sid: str, events: Iterable[dict]) -> str:
    """The working directory a session recorded, or "" when unknown.

    The session row is keyed ``(agent_type, session_id)``: family runtimes
    under the prefixed id, OpenClaw under the bare one, so the bare lookup is
    scoped to the prefix's runtime rather than matching another runtime's id.
    Falls back to a ``cwd`` carried on the session's own events.
    """
    getter = getattr(store, "get_session_location", None)
    if callable(getter):
        tries = [{"session_id": sid}]
        if ":" in sid:
            prefix, bare = sid.split(":", 1)
            tries.append({"session_id": bare, "agent_type": prefix})
        for kw in tries:
            try:
                row = getter(**kw)
            except Exception:
                continue
            if isinstance(row, dict) and str(row.get("cwd") or "").strip():
                return str(row["cwd"]).strip()
    for ev in events or ():
        data = _as_dict(ev.get("data"))
        for value in (ev.get("cwd"), data.get("cwd"), _as_dict(data.get("message")).get("cwd")):
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def _read_session_events(store: Any, sid: str) -> tuple:
    """``(events, complete)``: every event of one session, newest first.

    ``query_events`` is newest first with a limit, so a session that kept
    working after the head commit can fill a page with events the head filter
    then discards. Pages walk back by timestamp until a short page;
    ``complete`` is False when the page budget ran out or the walk could not
    advance (a whole page sharing one timestamp).
    """
    seen: set = set()
    out: list = []
    until = None
    for _ in range(_MAX_EVENT_PAGES):
        kw = {"session_id": sid, "limit": _MAX_EVENTS_PER_PAGE}
        if until:
            kw["until"] = until
        page = [dict(e) for e in (store.query_events(**kw) or [])]
        added = 0
        for ev in page:
            key = ev.get("id") or json.dumps([ev.get("ts"), ev.get("event_type"), ev.get("data")],
                                             sort_keys=True, default=str)
            if key in seen:
                continue
            seen.add(key)
            out.append(ev)
            added += 1
        if len(page) < _MAX_EVENTS_PER_PAGE:
            return out, True
        oldest = str(page[-1].get("ts") or "")
        if not added or not oldest or oldest == until:
            return out, False
        until = oldest
    return out, False


def collect_from_store(store: Any, *, repo: str, commits: list, changed_files: list,
                       window_s: int = 7200, max_sessions: int | None = None) -> tuple:
    """Read linked sessions, their writes and their Guard findings.

    Candidates are the sessions a trailer names plus sessions active from
    ``window_s`` before the first commit to the head commit. Returns
    ``(links, sessions_meta, incidents_by_session, gaps)``.

    A candidate's relative write paths resolve only against its own recorded
    working directory, so a session working in another repository on the
    same machine is never linked by a relative path such as ``README.md``
    (AC-OBS-PRP-001.12). With no recorded directory, relative paths count
    only for a session a commit trailer names.

    ``gaps`` are sentences for every read limit hit and every read that
    failed; the caller turns any gap into ``partial`` evidence
    (AC-OBS-PRP-001.13). A gap never names a session: the sessions it is
    about are, by construction, ones this change may not involve.
    """
    max_sessions = _MAX_SESSIONS if max_sessions is None else int(max_sessions)
    gaps: list = []
    head_ts = max((c.get("ts") or 0 for c in commits), default=0)
    first_ts = min((c.get("ts") or 0 for c in commits if c.get("ts")), default=0)
    until = (_dt.datetime.fromtimestamp(head_ts + 60, tz=_dt.timezone.utc) if head_ts else None)
    window_start = first_ts - window_s

    try:
        rows = [dict(r) for r in (store.query_sessions(limit=_MAX_SESSION_ROWS) or [])]
    except Exception as exc:
        logger.warning("session query failed: %s", exc)
        rows = []
        gaps.append("the session list could not be read from the store")
    if head_ts and len(rows) >= _MAX_SESSION_ROWS:
        # Rows come newest-activity first, so the cut rows are no newer than
        # the oldest returned. Only a cut inside the window can hide a session.
        ends = [_parse_time(r.get("updated_at") or r.get("started_at")) for r in rows]
        oldest = min((e for e in ends if e is not None), default=None)
        if oldest is None or oldest.timestamp() >= window_start:
            gaps.append(f"the session list reached its {_MAX_SESSION_ROWS}-session read limit "
                        "inside this change's time window; older sessions were not considered")
    by_id = {r.get("session_id"): r for r in rows if r.get("session_id")}
    trailer_named = list(dict.fromkeys(c["session_id"] for c in commits if c.get("session_id")))
    candidates = list(trailer_named)
    if head_ts:
        for r in rows:
            start = _parse_time(r.get("started_at"))
            end = _parse_time(r.get("updated_at") or r.get("ended_at") or r.get("last_active_at")) or start
            if start is None:
                continue
            if start.timestamp() <= head_ts + 60 and end.timestamp() >= window_start:
                candidates.append(r["session_id"])
    candidates = list(dict.fromkeys(candidates))
    if len(candidates) > max_sessions:
        gaps.append(f"{len(candidates) - max_sessions} active session(s) beyond the "
                    f"{max_sessions}-session read limit were not read")
        candidates = candidates[:max_sessions]

    wanted = set(changed_files or ())
    named = set(trailer_named)
    counts = {"events_cut": 0, "events_failed": 0, "unplaced": 0}
    incidents_short: dict = {}
    writes: dict = {}
    meta: dict = {}
    incidents: dict = {}
    for sid in candidates:
        try:
            events, complete = _read_session_events(store, sid)
            if not complete:
                counts["events_cut"] += 1
        except Exception as exc:
            logger.warning("events for %s unavailable: %s", sid, exc)
            events = []
            counts["events_failed"] += 1
        row = by_id.get(sid) or {}
        cwd = _session_cwd(store, sid, events)
        unplaced: set = set()
        writes[sid] = observed_writes(events, repo, cwd=cwd or None, until=until,
                                      relative_without_cwd=sid in named, unplaced=unplaced)
        if unplaced & wanted:
            counts["unplaced"] += 1
        # Cost comes from the session row, which the store de-duplicates (an
        # OpenClaw turn is stamped on two sibling events, #1460). A session no
        # event ever priced has an UNKNOWN cost, not a zero one: the row's
        # COALESCE(..., 0) cannot tell those apart, so the events decide.
        priced = any(e.get("cost_usd") is not None for e in events)
        cost = None
        if priced:
            try:
                cost = float(row["cost_usd"]) if row.get("cost_usd") is not None else sum(
                    float(e["cost_usd"]) for e in events if e.get("cost_usd") is not None)
            except (TypeError, ValueError):
                cost = None
        runtime = next((str(e.get("runtime_kind") or e.get("agent_type")) for e in events
                        if e.get("runtime_kind") or e.get("agent_type")), "") or runtime_of(sid)
        if events or row:
            meta[sid] = {
                "runtime": runtime if ":" not in sid else runtime_of(sid),
                "models": sorted({str(e["model"]) for e in events if e.get("model")}),
                "cost_usd": cost,
                # Events are newest first: the earliest timestamp is the start.
                "started_at": row.get("started_at") or min(
                    (str(e["ts"]) for e in events if e.get("ts")), default=""),
            }
        try:
            incidents[sid] = list(store.query_guard_incidents(
                session_id=sid, since_secs=0, limit=_MAX_INCIDENTS_PER_SESSION) or [])
            if len(incidents[sid]) >= _MAX_INCIDENTS_PER_SESSION:
                incidents_short[sid] = "cut"
        except Exception as exc:
            logger.warning("Guard findings for %s unavailable: %s", sid, exc)
            incidents[sid] = []
            incidents_short[sid] = "failed"
    links = link_files(changed_files, commits, writes)

    if counts["events_cut"]:
        gaps.append(f"events of {counts['events_cut']} session(s) exceeded the "
                    f"{_MAX_EVENTS_PER_PAGE * _MAX_EVENT_PAGES}-event read limit; "
                    "earlier writes may be missing")
    if counts["events_failed"]:
        gaps.append(f"events of {counts['events_failed']} session(s) could not be read "
                    "from the store")
    if counts["unplaced"]:
        gaps.append(f"{counts['unplaced']} session(s) with no recorded working directory "
                    "wrote relative paths matching changed files; those writes were not "
                    "attributed")
    # Findings only gate through a linked session, so only those gaps count.
    linked = {r["session_id"] for rows_ in links.values() for r in rows_}
    cut = sum(1 for s, why in incidents_short.items() if s in linked and why == "cut")
    failed = sum(1 for s, why in incidents_short.items() if s in linked and why == "failed")
    if cut:
        gaps.append(f"Guard findings of {cut} linked session(s) reached the "
                    f"{_MAX_INCIDENTS_PER_SESSION}-finding read limit")
    if failed:
        gaps.append(f"Guard findings of {failed} linked session(s) could not be read")
    return links, meta, incidents, gaps
