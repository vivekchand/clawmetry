"""Shared plumbing for the agent-facing read CLI.

Interface contract (docs/CLI.md is the user-facing copy of this):

* stdout carries DATA, stderr carries decoration (notes, hints, errors).
* ``--json`` emits one JSON object per invocation — the same rows/dicts the
  local store methods serve (the shape the ``/api/local`` read API returns),
  no envelope. ``default=str`` so Decimal/datetime never crash the dump.
* ``--follow`` (where offered) emits NDJSON: first line
  ``{"type":"_meta",...}``, one event object per line, final line
  ``{"type":"_end","reason":...,"next_cursor":...}`` so an agent can resume.
* Exit codes are a stable contract:
    0 success (including empty results)
    1 internal/runtime error
    2 usage error
    3 no data source answered (no daemon, no local store) — retryable
    4 entitlement-gated (the CLI's 402)
    5 auth failure
    6 not found (unknown session id, ...)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_UNAVAILABLE = 3
EXIT_ENTITLEMENT = 4
EXIT_AUTH = 5
EXIT_NOT_FOUND = 6


class CliError(Exception):
    """Structured CLI failure. ``code`` is the machine-readable error code
    (mirrors the API error vocabulary: unavailable / not_found /
    upgrade_required / bad_request / internal), ``extra`` merges into the
    JSON error body (used by the selfevolve stub to carry the full 402
    shape)."""

    def __init__(self, code: str, message: str, exit_code: int, extra: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.extra = extra or {}


def fail(err: CliError) -> int:
    """Print the error to stderr (JSON when stdout is being parsed is the
    caller's concern — the error body is always JSON so agents can parse it,
    prefixed with a plain sentence for humans) and return the exit code."""
    body = {"error": {"code": err.code, "message": err.message, **err.extra}}
    print(f"clawmetry: {err.message}", file=sys.stderr)
    print(json.dumps(body, default=str), file=sys.stderr)
    return err.exit_code


def note(msg: str) -> None:
    """Decoration → stderr, never stdout."""
    print(msg, file=sys.stderr)


# ── Time handling ───────────────────────────────────────────────────────────

_RELATIVE_RE = re.compile(r"^(\d+)\s*([smhdw])$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def utcnow_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_when(value: str | None, flag: str = "--since") -> str | None:
    """Accept ISO-8601 (passed through) or relative ``90s|15m|6h|7d|2w``
    (converted to a UTC ISO timestamp that far in the past)."""
    if not value:
        return None
    value = value.strip()
    m = _RELATIVE_RE.match(value)
    if m:
        secs = int(m.group(1)) * _UNIT_SECONDS[m.group(2)]
        return (datetime.utcnow() - timedelta(seconds=secs)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    # ISO-ish: let the store's SQL comparison handle precision; just sanity-check.
    if re.match(r"^\d{4}-\d{2}-\d{2}", value):
        return value
    raise CliError(
        "bad_request",
        f"{flag} must be ISO-8601 (2026-07-31T12:00:00Z) or relative (90s, 15m, 6h, 7d)",
        EXIT_USAGE,
    )


# ── Shared flags ────────────────────────────────────────────────────────────

def add_output_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--json", action="store_true", dest="as_json",
        help="Emit JSON (the same shape the local read API serves) instead of the table",
    )


def add_window_flags(p: argparse.ArgumentParser, default_since: str | None = None) -> None:
    p.add_argument(
        "--since", metavar="WHEN", default=default_since,
        help="Window start: ISO-8601 or relative (90s, 15m, 6h, 7d)"
        + (f" (default: {default_since})" if default_since else ""),
    )
    p.add_argument("--until", metavar="WHEN", help="Window end (same formats)")
    p.add_argument(
        "--last", metavar="SPAN",
        help="Sugar for --since <SPAN> (e.g. --last 24h)",
    )


def add_runtime_flag(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--runtime", metavar="R",
        help="Scope to one runtime (openclaw, claude_code, codex, cursor, ...)",
    )


def resolve_window(args) -> tuple[str | None, str | None]:
    since = parse_when(getattr(args, "last", None), "--last") or parse_when(
        getattr(args, "since", None)
    )
    until = parse_when(getattr(args, "until", None), "--until")
    return since, until


# ── Transport (the invisible ladder) ────────────────────────────────────────

def get_read_store():
    """Return ``(store, source)`` where source is ``daemon`` (HTTP proxy to
    the sync daemon that owns the DuckDB writer) or ``direct`` (read-only
    DuckDB open — single-process installs only).

    ``local_store.get_store(read_only=True)`` already implements the ladder:
    a registered daemon → ``_ProxyStore`` (never opens DuckDB here, which
    would block the daemon's writer — the recurring lock bug); no daemon →
    direct RO open. We only classify which rung answered so output can carry
    ``source`` honestly.
    """
    try:
        from clawmetry import local_store
    except Exception as exc:
        raise CliError(
            "unavailable", f"clawmetry install is broken (cannot import local_store: {exc})",
            EXIT_UNAVAILABLE,
        )
    daemon = False
    try:
        daemon = bool(local_store._daemon_registered())
    except Exception:
        daemon = False
    try:
        store = local_store.get_store(read_only=True)
    except Exception as exc:
        raise CliError(
            "unavailable",
            "no daemon, dashboard, or local store found "
            f"({exc.__class__.__name__}); run `clawmetry sync` or `clawmetry onboard`",
            EXIT_UNAVAILABLE,
        )
    return store, ("daemon" if daemon else "direct")


def call(store, method: str, **kwargs):
    """Invoke a store read method (kwargs only — the daemon proxy forwards
    kwargs verbatim and every method must be in routes/local_query.py's
    ``_DAEMON_METHODS`` allowlist). ``None`` from the proxy means the daemon
    didn't answer (busy / restarting / method not allowlisted) — surfaced as
    the retryable exit-3, never a silent empty table."""
    fn = getattr(store, method, None)
    if fn is None:
        raise CliError("internal", f"store method {method} missing", EXIT_ERROR)
    try:
        result = fn(**kwargs)
    except Exception as exc:
        raise CliError("internal", f"{method} failed: {exc}", EXIT_ERROR)
    if result is None:
        raise CliError(
            "unavailable",
            f"the sync daemon did not answer {method} (busy or restarting); "
            "retry in a few seconds",
            EXIT_UNAVAILABLE,
        )
    return result


# ── Output ──────────────────────────────────────────────────────────────────

def emit_json(payload) -> None:
    json.dump(payload, sys.stdout, default=str)
    sys.stdout.write("\n")


def emit_jsonl(obj) -> None:
    sys.stdout.write(json.dumps(obj, default=str) + "\n")
    sys.stdout.flush()


def fmt_cell(value, width: int) -> str:
    s = "" if value is None else str(value)
    s = s.replace("\n", " ").replace("\t", " ")
    if len(s) > width:
        s = s[: width - 1] + "…"
    return s.ljust(width)


def print_table(rows: list[dict], columns: list[tuple[str, str, int]]) -> None:
    """``columns`` = [(key, header, max_width)]. Whitespace-aligned, one
    header line, awk/cut-safe. Empty input prints headers + a stderr note
    and exits 0 upstream."""
    widths = []
    for key, header, max_w in columns:
        w = len(header)
        for r in rows:
            w = max(w, min(max_w, len(str(r.get(key, "") or ""))))
        widths.append(min(w, max_w))
    header_line = "  ".join(
        h.ljust(w) for (_, h, _), w in zip(columns, widths)
    )
    print(header_line)
    for r in rows:
        print("  ".join(
            fmt_cell(r.get(k), w) for (k, _, _), w in zip(columns, widths)
        ).rstrip())
    if not rows:
        note("(no data)")


def fmt_cost(v) -> str:
    try:
        return f"${float(v):.4f}" if float(v) < 1 else f"${float(v):.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def fmt_tokens(v) -> str:
    try:
        n = int(v)
    except (TypeError, ValueError):
        return "0"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def short_sid(sid: str, keep: int = 30) -> str:
    sid = sid or ""
    return sid if len(sid) <= keep else sid[: keep - 1] + "…"


# ── Parser assembly ─────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    from clawmetry.cli_cmds import activity, progress, selfevolve, sessions, usage, waste

    parser = argparse.ArgumentParser(
        prog="clawmetry",
        description="Agent-facing observability reads (see docs/CLI.md)",
        epilog=(
            "exit codes: 0 ok · 1 error · 2 usage · 3 no data source · "
            "4 upgrade required · 5 auth · 6 not found"
        ),
    )
    sub = parser.add_subparsers(dest="cmd")
    sessions.register(sub)
    activity.register(sub)
    waste.register(sub)
    progress.register(sub)
    usage.register(sub)
    selfevolve.register(sub)
    return parser
