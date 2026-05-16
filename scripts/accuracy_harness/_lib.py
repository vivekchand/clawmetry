"""scripts/accuracy_harness/_lib.py — shared helpers for every harness.

Extracted from ``tokens.py`` (PR #1395) when the second harness landed
(``approvals.py``, this PR). Keeping the discovery / HTTP / openclaw-CLI
shims in one place means a future ``alerts.py`` / ``crons.py`` /
``channels.py`` harness can ``from _lib import ...`` without copy-paste,
and a fix to (e.g.) the daemon discovery flow only needs to land once.

Public surface:
    DEFAULT_DASHBOARD_PORTS, GH_REPO, OPENCLAW_BIN
    http_get_json, http_post_json
    discover_dashboard_url, discover_daemon, daemon_event_count
    daemon_call (generic ``__local_query__/<method>`` proxy)
    drive_openclaw_message, extract_openclaw_usage
    file_drift_issue_per_endpoint, format_drift_issue_body
    file_consolidated_issue (meta-runner roll-up — one issue per day, idempotent)
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

# ─── Constants ──────────────────────────────────────────────────────────────

DEFAULT_DASHBOARD_PORTS = (8900, 8903, 8905)
GH_REPO = "vivekchand/clawmetry"
OPENCLAW_BIN = shutil.which("openclaw") or "openclaw"
LOCAL_QUERY_DISCOVERY = Path.home() / ".clawmetry" / "local_query.json"


# ─── HTTP shims ─────────────────────────────────────────────────────────────

def http_get_json(url: str, timeout: float = 10.0,
                  headers: dict | None = None) -> Any:
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post_json(url: str, body: dict | None = None,
                   headers: dict | None = None,
                   timeout: float = 10.0) -> Any:
    data = json.dumps(body or {}).encode("utf-8")
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_delete_json(url: str, headers: dict | None = None,
                     timeout: float = 10.0) -> Any:
    """DELETE shim used for harness cleanup. Returns parsed JSON or None on
    empty bodies (DELETE handlers sometimes return ``""`` / 204)."""
    h = {"Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h, method="DELETE")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8") or ""
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return raw


# ─── Polling ────────────────────────────────────────────────────────────────

def wait_for_event(predicate, *, timeout: float = 30.0,
                   interval: float = 0.5,
                   description: str = "event") -> Any:
    """Call ``predicate()`` every ``interval`` seconds until it returns a
    truthy value or ``timeout`` elapses. Returns whatever the predicate
    returns (truthy value on success, last falsy value on timeout).

    ``predicate`` should swallow its own transient exceptions and return
    a falsy sentinel — re-raises propagate out and abort the poll.

    Used by harnesses that need to wait on an async sink (alert eval
    tick, daemon DuckDB write, webhook listener receive) without
    duplicating the deadline/sleep boilerplate.
    """
    import time as _time
    deadline = _time.time() + timeout
    last = None
    while _time.time() < deadline:
        last = predicate()
        if last:
            return last
        _time.sleep(interval)
    return last


# ─── Discovery ──────────────────────────────────────────────────────────────

def _port_listening(port: int, host: str = "127.0.0.1") -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def discover_dashboard_url(override: str | None,
                            probe_path: str = "/api/usage",
                            probe_keys: Iterable[str] = ("days",)) -> str:
    """Return the first dashboard base URL that responds with JSON containing
    any of ``probe_keys`` at ``probe_path``. Honours ``--dashboard-url`` >
    ``$CLAWMETRY_URL`` > auto-scan ``DEFAULT_DASHBOARD_PORTS``.
    """
    if override:
        return override.rstrip("/")
    env = os.environ.get("CLAWMETRY_URL")
    if env:
        return env.rstrip("/")
    for port in DEFAULT_DASHBOARD_PORTS:
        if not _port_listening(port):
            continue
        url = f"http://localhost:{port}"
        try:
            payload = http_get_json(f"{url}{probe_path}", timeout=3.0)
            if isinstance(payload, dict) and any(k in payload for k in probe_keys):
                return url
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError):
            continue
    raise RuntimeError(
        f"could not find a ClawMetry dashboard on any of {DEFAULT_DASHBOARD_PORTS}. "
        f"Set CLAWMETRY_URL or pass --dashboard-url."
    )


def discover_daemon() -> dict | None:
    """Return ``{port, token}`` for the daemon's local_query proxy, or None
    when unavailable. Liveness-checked via ``os.kill(pid, 0)``."""
    try:
        with open(LOCAL_QUERY_DISCOVERY) as fh:
            d = json.load(fh)
        if not (d.get("port") and d.get("token")):
            return None
        try:
            os.kill(int(d.get("pid") or 0), 0)
        except (OSError, ValueError):
            return None
        return {"port": int(d["port"]), "token": d["token"]}
    except (FileNotFoundError, ValueError, OSError):
        return None


def daemon_call(daemon: dict, method: str, *, timeout: float = 5.0,
                **kwargs) -> Any:
    """Call ``LocalStore.<method>(**kwargs)`` via the daemon's
    ``/__local_query__/<method>`` proxy. Returns the parsed ``"result"``
    value on success, raises on HTTP / allowlist / serialisation failure.
    """
    url = f"http://127.0.0.1:{daemon['port']}/__local_query__/{method}"
    body = http_post_json(
        url, body={"kwargs": kwargs},
        headers={"Authorization": f"Bearer {daemon['token']}"},
        timeout=timeout,
    )
    if isinstance(body, dict) and "error" in body:
        raise RuntimeError(f"daemon proxy {method} returned error: {body['error']}")
    return body.get("result") if isinstance(body, dict) else None


def daemon_event_count(daemon: dict) -> int | None:
    """Return total event_count from ``health``. None if unreachable."""
    try:
        result = daemon_call(daemon, "health", timeout=3.0)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError,
            TimeoutError, OSError, RuntimeError):
        return None
    if isinstance(result, dict):
        ev = result.get("event_count")
        try:
            return int(ev) if ev is not None else None
        except (TypeError, ValueError):
            return None
    return None


# ─── OpenClaw CLI driver (used by tokens harness; reusable) ─────────────────

def drive_openclaw_message(message: str, tag: str,
                            timeout_s: int = 120) -> dict[str, Any]:
    """Run ``openclaw agent --agent main --message <m> --json`` once.
    The tag is appended to the message body so the resulting transcript /
    DuckDB row is searchable."""
    full_msg = f"{message} [{tag}]"
    cmd = [OPENCLAW_BIN, "agent", "--agent", "main", "--message", full_msg, "--json"]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout_s, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"openclaw agent exited {proc.returncode}\nstderr: {proc.stderr[:500]}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"openclaw agent --json returned non-JSON: {e}\nfirst 300 bytes: {proc.stdout[:300]}"
        )


def extract_openclaw_usage(agent_json: dict) -> dict[str, Any] | None:
    """Pull the usage block out of an ``openclaw agent --json`` response."""
    meta = (agent_json or {}).get("result", {}).get("meta", {}) or {}
    agent_meta = meta.get("agentMeta") or {}
    usage = agent_meta.get("usage") or {}
    if not usage:
        return None
    return {
        "input":      int(usage.get("input") or 0),
        "output":     int(usage.get("output") or 0),
        "cacheRead":  int(usage.get("cacheRead") or 0),
        "cacheWrite": int(usage.get("cacheWrite") or 0),
        "sessionId":  agent_meta.get("sessionId") or "",
        "model":      agent_meta.get("model") or "",
    }


# ─── Drift issue filing (shared shape) ──────────────────────────────────────

def _open_audit_issue_exists(harness_label: str, endpoint: str,
                              today: str) -> bool:
    """Cheap dedup probe so re-runs in one day don't fan out N issues."""
    try:
        proc = subprocess.run(
            ["gh", "issue", "list",
             "--repo", GH_REPO,
             "--state", "open",
             "--search",
             f"[accuracy-audit {today}] {harness_label} drift: {endpoint} in:title",
             "--json", "number"],
            check=True, capture_output=True, text=True, timeout=15,
        )
        return bool(json.loads(proc.stdout or "[]"))
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError,
            subprocess.TimeoutExpired):
        return False


def file_drift_issue_per_endpoint(
    *,
    harness_label: str,
    drifts: list,                              # list with .endpoint, .delta, .window_label, .metric, .ground, .actual, .tolerance attrs OR dict-likes
    extra_labels: list[str] | None = None,
    body_builder=None,                         # callable(endpoint, group) -> str
) -> int:
    """Group drifts by endpoint, file ONE issue per endpoint with all
    drifted (window, metric) rows in the body. Returns count of issues filed.

    ``body_builder`` is an optional callable invoked as
    ``body_builder(endpoint, group_of_drifts)`` returning a markdown string.
    Falls back to ``format_drift_issue_body`` when None.
    """
    if not shutil.which("gh"):
        print("[harness] `gh` CLI not on PATH; cannot file issues. Skipping.")
        return 0
    grouped: dict[str, list] = {}
    for c in drifts:
        ep = getattr(c, "endpoint", None) or (c.get("endpoint") if isinstance(c, dict) else None)
        if not ep:
            continue
        grouped.setdefault(ep, []).append(c)
    today = datetime.now().strftime("%Y-%m-%d")
    labels = ["accuracy-audit", harness_label, "bug"]
    if extra_labels:
        labels.extend(extra_labels)
    filed = 0
    for endpoint, cs in grouped.items():
        headline = max(cs, key=lambda c: abs(getattr(c, "delta", 0) or 0))
        title = (
            f"[accuracy-audit {today}] {harness_label} drift: {endpoint} "
            f"{getattr(headline, 'window_label', '?')}/{getattr(headline, 'metric', '?')} "
            f"ground={getattr(headline, 'ground', '?')} "
            f"actual={getattr(headline, 'actual', '?')} "
            f"(delta={getattr(headline, 'delta', 0):+d}; {len(cs)} drifts total)"
        )
        if _open_audit_issue_exists(harness_label, endpoint, today):
            print(f"[harness] open issue for {endpoint} already exists today — skipping file")
            continue
        body = (body_builder or format_drift_issue_body)(endpoint, cs)
        cmd = ["gh", "issue", "create", "--repo", GH_REPO,
               "--title", title, "--body", body]
        for lbl in labels:
            cmd += ["--label", lbl]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"[harness] filed issue: {title}")
            filed += 1
        except subprocess.CalledProcessError:
            try:
                proc = subprocess.run(
                    ["gh", "issue", "create", "--repo", GH_REPO,
                     "--title", title, "--body", body],
                    check=True, capture_output=True, text=True,
                )
                print(f"[harness] filed (no labels): {proc.stdout.strip()}")
                filed += 1
            except subprocess.CalledProcessError as e2:
                print(f"[harness] FAILED to file issue: {e2.stderr[:300]}",
                      file=sys.stderr)
    return filed


def format_drift_issue_body(endpoint: str, cs: list) -> str:
    """Default body shape: drift table (no ground-truth log — harness-specific
    bodies should subclass via the ``body_builder`` callable instead)."""
    lines = [
        f"## Drift report — `{endpoint}`",
        "",
        "Auto-filed by `scripts/accuracy_harness/`.",
        "",
        "### Drifted (window, metric) pairs",
        "| window | metric | ground | actual | delta | tolerance |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for c in cs:
        lines.append(
            f"| {getattr(c, 'window_label', '?')} | {getattr(c, 'metric', '?')} | "
            f"{getattr(c, 'ground', '?')} | {getattr(c, 'actual', '?')} | "
            f"{getattr(c, 'delta', 0):+d} | "
            f"±{getattr(c, 'tolerance', 0)} |"
        )
    return "\n".join(lines)


# ─── Consolidated meta-runner issue (one per day, idempotent) ────────────────

CONSOLIDATED_LABEL = "accuracy-meta"
CONSOLIDATED_TITLE_PREFIX = "[accuracy-audit"  # full prefix: f"[accuracy-audit {today}]"

# Reproducer command per harness — surfaced in the issue body so the
# auto-fixer cron (and humans) can reproduce a drift in one paste.
REPRODUCER_COMMANDS = {
    "tokens":    "python3 scripts/accuracy_harness/tokens.py",
    "approvals": "python3 scripts/accuracy_harness/approvals.py",
    "alerts":    "CLAWMETRY_HARNESS_HOOKS=1 python3 scripts/accuracy_harness/alerts.py",
}


def _find_open_consolidated_issue(today: str) -> int | None:
    """Return the issue number of today's open consolidated issue, or None.

    Searches for an OPEN issue with the ``accuracy-meta`` label whose title
    starts with ``[accuracy-audit YYYY-MM-DD]``. Date prefix in the title
    is the dedup key — re-running the meta on the same day must EDIT not
    create. Failures (network, gh missing, parse error) return None so the
    caller falls through to ``create`` rather than silently skipping.
    """
    if not shutil.which("gh"):
        return None
    try:
        proc = subprocess.run(
            ["gh", "issue", "list",
             "--repo", GH_REPO,
             "--state", "open",
             "--label", CONSOLIDATED_LABEL,
             "--search", f"{CONSOLIDATED_TITLE_PREFIX} {today}] in:title",
             "--json", "number,title",
             "--limit", "10"],
            check=True, capture_output=True, text=True, timeout=15,
        )
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return None
    try:
        rows = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return None
    needle = f"{CONSOLIDATED_TITLE_PREFIX} {today}]"
    for row in rows:
        if str(row.get("title", "")).startswith(needle):
            try:
                return int(row.get("number"))
            except (TypeError, ValueError):
                continue
    return None


def _format_consolidated_body(results: list, today: str) -> str:
    """Build the markdown body for the consolidated meta issue.

    ``results`` is duck-typed (anything with ``.name``, ``.status``,
    ``.pass_count``, ``.drift_count``, ``.exit_code``, ``.note``, and
    optionally ``.stdout``) so ``_lib.py`` doesn't import ``all.py``'s
    ``HarnessResult`` dataclass — that would create a circular import.
    """
    n_h = len(results)
    n_drift_h = sum(1 for r in results if getattr(r, "status", "") == "drift")
    n_err_h = sum(1 for r in results if getattr(r, "status", "") == "error")
    n_drifts_total = sum(max(getattr(r, "drift_count", 0) or 0, 0) for r in results)

    lines = [
        f"## Accuracy meta-harness — {today}",
        "",
        "Auto-filed by `scripts/accuracy_harness/all.py`. This issue is "
        "**idempotent per UTC date**: re-running the meta-runner edits this "
        "body in place rather than opening a duplicate.",
        "",
        f"- Harnesses run: **{n_h}**",
        f"- Harnesses with drift: **{n_drift_h}**",
        f"- Harnesses errored / timed out: **{n_err_h}**",
        f"- Total drifted (window, metric) pairs: **{n_drifts_total}**",
        "",
        "### Scoreboard",
        "| harness | status | pass | drift | exit | note |",
        "|---|---|---:|---:|---:|---|",
    ]
    for r in results:
        p = getattr(r, "pass_count", -1)
        d = getattr(r, "drift_count", -1)
        p_s = str(p) if isinstance(p, int) and p >= 0 else "?"
        d_s = str(d) if isinstance(d, int) and d >= 0 else "?"
        # Pipes in notes break Markdown tables — replace defensively.
        note = str(getattr(r, "note", "") or "").replace("|", "\\|")
        lines.append(
            f"| {getattr(r, 'name', '?')} "
            f"| {str(getattr(r, 'status', '?')).upper()} "
            f"| {p_s} | {d_s} "
            f"| {getattr(r, 'exit_code', '?')} "
            f"| {note} |"
        )

    lines += ["", "### Per-harness detail"]
    for r in results:
        name = getattr(r, "name", "?")
        status = str(getattr(r, "status", "?")).upper()
        if status == "PASS":
            continue
        repro = REPRODUCER_COMMANDS.get(name, f"python3 scripts/accuracy_harness/{name}.py")
        lines += [
            "",
            f"#### `{name}` — {status}",
            "",
            f"Reproducer:",
            "",
            "```bash",
            repro,
            "```",
        ]
        # Include the harness's own drift/error tail so the auto-fixer cron
        # has the same evidence a human would see locally. Cap at 60 lines
        # to keep the issue body well under GitHub's 65 KB limit even when
        # all 3 harnesses error out together.
        stdout = getattr(r, "stdout", "") or ""
        if stdout:
            tail = stdout.strip().splitlines()[-60:]
            lines += ["", "<details><summary>Harness tail (last 60 lines)</summary>",
                      "", "```", *tail, "```", "</details>"]
        stderr = getattr(r, "stderr", "") or ""
        if stderr.strip():
            tail_e = stderr.strip().splitlines()[-30:]
            lines += ["", "<details><summary>stderr (last 30 lines)</summary>",
                      "", "```", *tail_e, "```", "</details>"]

    lines += [
        "",
        "---",
        "",
        "When this issue is closed, the cloud auto-fixer cron treats the "
        "drift as resolved for the day. Re-runs that find no drifts will "
        "**not** reopen this issue — the meta only files when "
        "`overall_exit_code != 0`.",
    ]
    return "\n".join(lines)


def file_consolidated_issue(results: list) -> str | None:
    """File (or edit) ONE consolidated GitHub issue summarising every
    harness in this meta-run. Returns the issue URL on success, None on
    failure (or when nothing actionable to file).

    Idempotency: searches for an OPEN issue with the ``accuracy-meta``
    label whose title starts with ``[accuracy-audit YYYY-MM-DD]``. If
    found, the body is REWRITTEN in place via ``gh issue edit``; if not,
    a new issue is created via ``gh issue create``. Re-running on the
    same UTC date never duplicates.

    The caller is responsible for skipping the call when ``--no-issue``
    is set or when overall exit code is 0 (all PASS) — the meta runner
    in ``all.py`` enforces both conditions.
    """
    if not shutil.which("gh"):
        print("[meta] `gh` CLI not on PATH; cannot file consolidated issue.",
              file=sys.stderr)
        return None
    if not results:
        print("[meta] no harness results to summarise; skipping file.",
              file=sys.stderr)
        return None

    today = datetime.utcnow().strftime("%Y-%m-%d")
    n_h = len(results)
    n_drift_h = sum(1 for r in results if getattr(r, "status", "") == "drift")
    n_err_h = sum(1 for r in results if getattr(r, "status", "") == "error")
    n_drifts_total = sum(max(getattr(r, "drift_count", 0) or 0, 0) for r in results)
    n_actionable = n_drift_h + n_err_h
    title = (f"{CONSOLIDATED_TITLE_PREFIX} {today}] meta-run: "
             f"{n_drifts_total} drifts across {n_actionable} harness(es)")
    body = _format_consolidated_body(results, today)

    existing = _find_open_consolidated_issue(today)
    if existing is not None:
        # EDIT in place — same date prefix → same issue.
        try:
            proc = subprocess.run(
                ["gh", "issue", "edit", str(existing),
                 "--repo", GH_REPO,
                 "--title", title,
                 "--body", body],
                check=True, capture_output=True, text=True, timeout=20,
            )
            url = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else ""
            if not url:
                url = f"https://github.com/{GH_REPO}/issues/{existing}"
            print(f"[meta] edited consolidated issue #{existing}: {url}")
            return url
        except subprocess.CalledProcessError as e:
            print(f"[meta] FAILED to edit issue #{existing}: "
                  f"{(e.stderr or '')[:300]}", file=sys.stderr)
            return None

    # CREATE — first run today.
    cmd = ["gh", "issue", "create",
           "--repo", GH_REPO,
           "--title", title,
           "--body", body,
           "--label", CONSOLIDATED_LABEL]
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True,
                              timeout=20)
        url = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else ""
        print(f"[meta] filed consolidated issue: {url}")
        return url or None
    except subprocess.CalledProcessError as e:
        # Most common cause: label missing on the repo. Retry without it
        # so we still get the issue filed (humans can re-label later).
        err = (e.stderr or "")[:300]
        if "label" in err.lower() or "not found" in err.lower():
            try:
                proc = subprocess.run(
                    ["gh", "issue", "create", "--repo", GH_REPO,
                     "--title", title, "--body", body],
                    check=True, capture_output=True, text=True, timeout=20,
                )
                url = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else ""
                print(f"[meta] filed (no label — please add `{CONSOLIDATED_LABEL}` "
                      f"to repo): {url}")
                return url or None
            except subprocess.CalledProcessError as e2:
                print(f"[meta] FAILED to file consolidated issue (no-label retry): "
                      f"{(e2.stderr or '')[:300]}", file=sys.stderr)
                return None
        print(f"[meta] FAILED to file consolidated issue: {err}", file=sys.stderr)
        return None
