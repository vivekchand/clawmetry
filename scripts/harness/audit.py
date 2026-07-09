#!/usr/bin/env python3
"""Daily harness-observability audit: for every monitored runtime, compare what
its upstream harness EXPOSES (sessions, events, tool calls, cost/tokens, cache,
telemetry, new features) against what ClawMetry's adapter actually CAPTURES, and
file a GitHub issue for each gap so it can be picked up.

Runs locally or in CI (.github/workflows/harness-observability-audit.yml). The
comparison is done by Claude (the `claude` CLI, same as i18n-autotranslate) so it
keeps up as harnesses evolve. Every step degrades gracefully — a missing clone,
a missing token, or a bad model response skips that runtime, never crashes the
run (so the workflow is safe to schedule before secrets exist).

Anti-hallucination (FLYWHEEL §1d): the model is given the REAL adapter source +
the REAL harness files + the declared Capability enum, and asked to ground every
gap in a concrete file/path it can point to. Gaps with no `where` are dropped.
Issues are deduplicated by a stable fingerprint so a daily run doesn't spam.

Usage:
  python3 scripts/harness/audit.py                 # audit all, DRY-RUN (print)
  python3 scripts/harness/audit.py --file-issues   # actually open/refresh issues
  python3 scripts/harness/audit.py --runtime goose # one runtime
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
MANIFEST = os.path.join(HERE, "manifest.json")

# Keyword groups that flag a harness file as part of its OBSERVABLE surface — what
# a monitoring tool would want to read. Used to pull the most relevant files into
# the audit context (a shallow clone can be large; we never feed the whole tree).
_OBS_KEYWORDS = (
    "session", "transcript", "rollout", "event", "telemetry", "otel",
    "opentelemetry", "trace", "span", "usage", "token", "cost", "price",
    "cache", "model", "tool_call", "tool_use", "log", "metric", "history",
)
_ISSUE_LABELS = ["harness-gap", "automated", "observability"]


def _load_manifest() -> dict:
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def _clone_dir(manifest: dict) -> str:
    env = os.environ.get("HARNESS_DIR")
    if env:
        return env
    return os.path.normpath(os.path.join(REPO_ROOT, manifest.get("clone_dir", "../harness")))


def _read(path: str, limit: int = 16000) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except Exception:
        return ""


def _git(cwd: str, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=cwd, text=True,
                                       stderr=subprocess.DEVNULL, timeout=30)
    except Exception:
        return ""


def _harness_surface(clone: str) -> str:
    """A compact view of the harness's observable surface: recent commit subjects
    + the top files whose names hint at session/telemetry/cost data, trimmed."""
    if not os.path.isdir(clone):
        return ""
    out = []
    log = _git(clone, "log", "--oneline", "-30")
    if log:
        out.append("RECENT COMMITS (last 30):\n" + log.strip())
    hits = []
    for root, dirs, files in os.walk(clone):
        if ".git" in dirs:
            dirs.remove(".git")
        # don't descend into vendored deps
        dirs[:] = [d for d in dirs if d not in ("node_modules", "target", "dist", "build", ".venv")]
        for fn in files:
            low = fn.lower()
            if any(k in low for k in _OBS_KEYWORDS) and low.rsplit(".", 1)[-1] in (
                    "py", "rs", "ts", "tsx", "js", "go", "md", "json", "toml"):
                hits.append(os.path.join(root, fn))
    # rank: prefer shorter paths (closer to root) and dedupe; cap to keep prompt small
    hits = sorted(set(hits), key=lambda p: (p.count(os.sep), len(p)))[:6]
    for p in hits:
        rel = os.path.relpath(p, clone)
        out.append(f"\n--- {rel} (excerpt) ---\n" + _read(p, 4000))
    return "\n".join(out)[:32000]


def _adapter_source(h: dict) -> str:
    """Read the FULL ClawMetry adapter for this runtime. Read the whole file (up
    to 60k) — truncating drops the tail, and capabilities()/cost-derivation often
    live at the BOTTOM of the adapter, which caused false-positive gaps (e.g.
    aider's conditional COST at line ~527 was cut, so the audit wrongly flagged
    'no COST').

    OSS audits only the FREE runtimes (openclaw + nemoclaw), whose adapters are in
    this repo. The 12 closed pro adapters are audited by clawmetry-pro's own
    private copy of this script, so no closed adapter path is referenced here."""
    return _read(os.path.join(REPO_ROOT, h["adapter"]), 60000)


def _capabilities_enum() -> str:
    return _read(os.path.join(REPO_ROOT, "clawmetry", "adapters", "base.py"), 6000)


def _build_prompt(h: dict, surface: str, adapter: str, caps: str) -> str:
    return f"""You audit observability coverage for ClawMetry, which monitors AI agent runtimes.

RUNTIME: {h['runtime']} ({h.get('display', h['runtime'])})
{('NOTE: ' + h['note']) if h.get('note') else ''}

ClawMetry's Capability contract (the things an adapter can declare it observes):
```
{caps}
```

ClawMetry's adapter that observes this runtime (what it ACTUALLY captures today):
```
{adapter}
```

The upstream harness — its observable surface (recent commits + data/telemetry files):
```
{surface or '(no public source available — reason for that is in NOTE above)'}
```

TASK: List concrete OBSERVABLE signals the harness EXPOSES that the ClawMetry
adapter does NOT capture today — e.g. a new session field, a cost/token/cache
counter, an OTel/telemetry stream, tool-call metadata, error/retry signals, a new
storage format, a new feature that emits data. Ground EVERY gap in a real file or
path you can point to in the harness; if you can't point to where the harness
exposes it, DO NOT include it (no speculation).

CRITICAL — verify against the FULL adapter above before reporting (it is provided
in full): do NOT flag something the adapter already handles. In particular check
``capabilities()`` (capabilities are often added CONDITIONALLY at the bottom of
the file), any ``derive_cost_usd`` / cost-derivation, and the field mapping. If
the adapter already captures or derives it, it is NOT a gap.

Output ONLY a JSON array (no prose). Each element:
{{"title": "<short, runtime-prefixed>", "exposes": "<what the harness emits>",
  "missing": "<what ClawMetry doesn't capture>", "where": "<harness file/path>",
  "severity": "high|medium|low", "capability": "<closest Capability enum name or 'new'>"}}
If coverage looks complete, output []."""


def _run_claude(prompt: str) -> str:
    """Call the `claude` CLI (CLAUDE_CODE_OAUTH_TOKEN in env). Returns raw text or ''."""
    if not (os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")):
        print("  [skip] no CLAUDE_CODE_OAUTH_TOKEN / ANTHROPIC_API_KEY — analysis skipped")
        return ""
    try:
        p = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, timeout=300)
        return p.stdout or ""
    except FileNotFoundError:
        print("  [skip] `claude` CLI not on PATH")
        return ""
    except Exception as e:
        print(f"  [skip] claude call failed: {e}")
        return ""


def _extract_json_array(text: str) -> list:
    if not text:
        return []
    # tolerate ```json fences / surrounding prose: grab the first [...] block
    i, j = text.find("["), text.rfind("]")
    if i == -1 or j == -1 or j < i:
        return []
    try:
        data = json.loads(text[i:j + 1])
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _fingerprint(runtime: str, gap: dict) -> str:
    key = f"{runtime}:{gap.get('title', '')}:{gap.get('where', '')}".lower()
    return "hgap-" + hashlib.sha1(key.encode()).hexdigest()[:10]


def _existing_fingerprints() -> set:
    """Fingerprints of already-filed gaps (from issue bodies), so a daily run
    never re-files the same gap. Matches the `hgap-<10hex>` token we embed."""
    import re
    try:
        out = subprocess.check_output(
            ["gh", "issue", "list", "--label", "harness-gap", "--state", "all",
             "--limit", "500", "--json", "body"], text=True, stderr=subprocess.DEVNULL)
        fps: set = set()
        for it in json.loads(out):
            fps.update(re.findall(r"hgap-[0-9a-f]{10}", it.get("body") or ""))
        return fps
    except Exception:
        return set()


def _file_issue(runtime: str, gap: dict, fp: str, dry: bool) -> None:
    title = f"[obs-gap:{runtime}] " + str(gap.get("title", "observability gap"))[:140]
    sev = gap.get("severity", "medium")
    body = (
        f"Automated harness-observability audit found a gap for **{runtime}**.\n\n"
        f"- **Harness exposes:** {gap.get('exposes', '')}\n"
        f"- **ClawMetry misses:** {gap.get('missing', '')}\n"
        f"- **Where (harness):** `{gap.get('where', '')}`\n"
        f"- **Severity:** {sev}\n"
        f"- **Closest capability:** {gap.get('capability', 'new')}\n\n"
        f"_Filed by `scripts/harness/audit.py`. Fingerprint: {fp} (used to dedupe — keep it in the body)._"
    )
    labels = _ISSUE_LABELS + [f"runtime:{runtime}", f"severity:{sev}"]
    if dry:
        print(f"  [dry-run] would file: {title}  ({fp})")
        return
    try:
        subprocess.run(["gh", "issue", "create", "--title", title, "--body", body,
                        "--label", ",".join(labels)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(f"  [filed] {title}")
    except Exception as e:
        # label may not exist yet; retry without labels rather than lose the issue
        try:
            subprocess.run(["gh", "issue", "create", "--title", title, "--body", body],
                           check=True, stdout=subprocess.DEVNULL)
            print(f"  [filed, no labels] {title}")
        except Exception as e2:
            print(f"  [error] could not file issue: {e2}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file-issues", action="store_true", help="actually open issues (default: dry-run)")
    ap.add_argument("--runtime", help="audit a single runtime")
    ap.add_argument("--max-per-runtime", type=int, default=5,
                    help="cap issues filed per runtime (highest-severity first); 0 = no cap")
    ap.add_argument("--include-low", action="store_true",
                    help="also file low-severity gaps (default: skip them)")
    args = ap.parse_args()

    manifest = _load_manifest()
    clone_base = _clone_dir(manifest)
    caps = _capabilities_enum()
    existing = _existing_fingerprints() if args.file_issues else set()
    total_gaps = 0

    for h in manifest["harnesses"]:
        rt = h["runtime"]
        if args.runtime and rt != args.runtime:
            continue
        print(f"== {rt} ==")
        clone = os.path.join(clone_base, rt)
        surface = _harness_surface(clone)
        if not surface and not h.get("repo"):
            print("  (no public source — covered by on-disk-format audit, skipping model pass)")
            continue
        if not surface:
            print(f"  [skip] no clone at {clone} — run scripts/harness/sync.sh first")
            continue
        adapter = _adapter_source(h)
        raw = _run_claude(_build_prompt(h, surface, adapter, caps))
        gaps = _extract_json_array(raw)
        print(f"  {len(gaps)} gap(s) reported")
        # Ground (anti-hallucination), severity-sort, drop low, cap per runtime so a
        # daily run produces a focused, high-value stream — not 100+ noisy issues.
        # The cap is LOGGED (no silent truncation, FLYWHEEL "no silent caps").
        _sev = {"high": 0, "medium": 1, "low": 2}
        grounded = [g for g in gaps if g.get("where")]
        grounded.sort(key=lambda g: _sev.get(str(g.get("severity", "medium")).lower(), 1))
        keep = grounded if args.include_low else [
            g for g in grounded if str(g.get("severity", "medium")).lower() != "low"]
        capped = keep if args.max_per_runtime <= 0 else keep[:args.max_per_runtime]
        deferred = len(grounded) - len(capped)
        if deferred:
            print(f"  filing {len(capped)} of {len(grounded)} grounded gap(s); "
                  f"{deferred} lower-priority deferred (raise --max-per-runtime / --include-low)")
        for gap in capped:
            fp = _fingerprint(rt, gap)
            if fp in existing:
                print(f"  [dup] {gap.get('title')} ({fp}) — already filed")
                continue
            total_gaps += 1
            _file_issue(rt, gap, fp, dry=not args.file_issues)

    print(f"\nDone. {total_gaps} new gap(s) "
          + ("filed." if args.file_issues else "(dry-run; pass --file-issues to open them)."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
