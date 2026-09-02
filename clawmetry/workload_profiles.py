"""Workload profiling for the Harness Engineering tab (REQ-HB-004).

Classifies observed sessions into coarse workload profiles and maps each
profile to the harness *qualities* that matter for it. Pure functions; the
route feeds session rows in and renders recommendation cards out.

A recommendation is never a single winner: candidates always list at least
two options where two exist, each carrying its evidence (the user's own
$/done where the harness is installed, a dated published pair where not).
"""

from __future__ import annotations

from typing import Any

PROFILE_CODING = "coding"
PROFILE_CHAT = "chat_automation"
PROFILE_SCHEDULED = "scheduled_background"
PROFILE_RESEARCH = "research_long_horizon"
PROFILE_GENERAL = "general"

PROFILES = (PROFILE_CODING, PROFILE_CHAT, PROFILE_SCHEDULED,
            PROFILE_RESEARCH, PROFILE_GENERAL)

# Qualities per profile, in plain language. Wire ids stay stable; the tab
# translates via locale keys bench.profile.<id>.*.
PROFILE_QUALITIES: dict[str, list[str]] = {
    PROFILE_CODING: ["long-horizon context", "a verification loop", "cheap retries"],
    PROFILE_CHAT: ["knows what can wait", "shares the work", "channel adapters"],
    PROFILE_SCHEDULED: ["cron-first delegation", "quiet failure reporting",
                        "cheap models by default"],
    PROFILE_RESEARCH: ["parallel fan-out", "long-horizon context"],
    PROFILE_GENERAL: ["finishes the job", "keeps its head clear"],
}

_RESEARCH_MIN_TOKENS = 200_000


def classify_session(row: dict) -> str:
    """Best-effort profile for one query_quality_sessions row. Uses only
    facts the row actually carries; defaults to general."""
    if not isinstance(row, dict):
        return PROFILE_GENERAL
    meta = row.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
    sid = str(row.get("session_id") or "")
    # Cron/scheduled sessions: OpenClaw stamps run kind into the session key
    # or metadata; a cron-spawned session is background work by definition.
    kind = str(meta.get("runKind") or meta.get("run_kind") or "").lower()
    if kind == "cron" or "::cron" in sid or ":cron:" in sid:
        return PROFILE_SCHEDULED
    # Channel-originated sessions are chat automation.
    if meta.get("channel") or meta.get("chatChannel"):
        return PROFILE_CHAT
    # Sessions rooted in a repository are coding work.
    if row.get("git_branch") or meta.get("gitBranch"):
        return PROFILE_CODING
    cwd = str(row.get("cwd") or meta.get("cwd") or "")
    if cwd and not cwd.rstrip("/").endswith(("Desktop", "Documents", "Downloads")):
        # A working directory alone is a weak coding signal; require it to
        # look like a project checkout rather than a home-adjacent folder.
        if any(seg in cwd for seg in ("/projects", "/src", "/repos", "/code", "/dev")):
            return PROFILE_CODING
    # Very long token streams with no repo look like research / long-horizon.
    try:
        if float(row.get("total_tokens") or 0) >= _RESEARCH_MIN_TOKENS:
            return PROFILE_RESEARCH
    except (TypeError, ValueError):
        pass
    return PROFILE_GENERAL


def profile_spend(rows_by_runtime: dict[str, list[dict]] | None) -> dict[str, Any]:
    """Spend share per profile across all runtimes, plus each profile's
    per-runtime spend so candidates can carry the user's own numbers."""
    totals: dict[str, float] = {p: 0.0 for p in PROFILES}
    per_runtime: dict[str, dict[str, float]] = {p: {} for p in PROFILES}
    grand = 0.0
    for rt, rows in (rows_by_runtime or {}).items():
        for row in rows or []:
            try:
                cost = max(0.0, float(row.get("cost_usd") or 0))
            except (TypeError, ValueError):
                cost = 0.0
            p = classify_session(row)
            totals[p] += cost
            per_runtime[p][rt] = per_runtime[p].get(rt, 0.0) + cost
            grand += cost
    out = []
    for p in PROFILES:
        if totals[p] <= 0:
            continue
        out.append({
            "profile": p,
            "qualities": PROFILE_QUALITIES[p],
            "spend_usd": round(totals[p], 2),
            "spend_share": round(totals[p] / grand, 3) if grand > 0 else 0.0,
            "by_runtime": {rt: round(v, 2)
                           for rt, v in sorted(per_runtime[p].items(),
                                               key=lambda kv: -kv[1])},
        })
    out.sort(key=lambda e: -e["spend_usd"])
    return {"profiles": out, "total_spend_usd": round(grand, 2)}


def build_recommendations(
    spend: dict[str, Any],
    bench_by_runtime: dict[str, dict] | None,
    published_pairs: list[dict] | None,
) -> list[dict[str, Any]]:
    """One card per observed profile: qualities + candidate harnesses with
    evidence. Candidates are unranked when evidence is insufficient
    (AC-HB-004.4); the list never collapses to a single vendor when a second
    option with any evidence exists."""
    bench = bench_by_runtime or {}
    pubs = published_pairs or []
    cards = []
    for entry in (spend or {}).get("profiles", []):
        candidates = []
        for rt, spend_usd in entry.get("by_runtime", {}).items():
            scope = bench.get(rt) or {}
            dpd = (scope.get("dollars_per_done") or {}).get("value")
            candidates.append({
                "runtime": rt,
                "evidence": ("measured" if dpd is not None else "observed"),
                "dollars_per_done": dpd,
                "spend_usd": spend_usd,
                "stamp": scope.get("stamp"),
            })
        measured = [c for c in candidates if c["dollars_per_done"] is not None]
        ranked = len(measured) >= 2
        if ranked:
            candidates.sort(key=lambda c: (c["dollars_per_done"] is None,
                                           c["dollars_per_done"] or 0))
        # Top up with published pairs for harnesses the user does not run.
        if len(candidates) < 2:
            seen = {c["runtime"] for c in candidates}
            for p in pubs:
                if p.get("harness") in seen:
                    continue
                candidates.append({
                    "runtime": p.get("harness"),
                    "evidence": "published",
                    "published": {k: p.get(k) for k in
                                  ("benchmark", "model", "result",
                                   "result_date", "source_url", "historical")},
                })
                seen.add(p.get("harness"))
                if len(candidates) >= 3:
                    break
        cards.append({
            "profile": entry["profile"],
            "qualities": entry["qualities"],
            "spend_share": entry["spend_share"],
            "spend_usd": entry["spend_usd"],
            "ranked": ranked,
            "candidates": candidates[:4],
        })
    return cards
