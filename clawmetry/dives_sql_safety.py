"""SQL safety validator for ClawMetry Dives (AI SQL -> chart over local DuckDB).

The Dives feature lets users ask plain-English questions; an LLM generates a SQL
query against the local DuckDB store; the result is rendered as a chart. Because
the SQL is LLM-generated, every query MUST pass this validator before execution.
Never trust the raw model output.

The validator is intentionally tiny, pure-Python, and dependency-free so it can
be fuzzed in isolation. Sub-issue: https://github.com/vivekchand/clawmetry/issues/1000.

Design notes
------------
- Allowlist-first: we only let through ``SELECT`` queries (optionally preceded by
  ``WITH ... SELECT``). Everything else is rejected by default.
- Two layers of defence:
    1. A lexical pass that strips strings + comments, then scans the remaining
       tokens for banned keywords / functions / multi-statements. This catches
       the classic injection tricks: ``'; DROP TABLE x; --``, comment-hidden
       statements, ``EXEC`` / ``ATTACH`` / file-system functions, etc.
    2. If ``sqlglot`` is available (best-effort, optional dep) a structural
       parse is run as defence in depth. We never *require* sqlglot — the
       lexical pass alone is enough to enforce the allowlist.
- Pure static analysis. The validator never touches DuckDB; execution is the
  caller's job (see #1002).

Public API
----------
    validate_sql(sql: str) -> tuple[bool, str | None]

Returns ``(True, None)`` if the query is safe to execute, ``(False, reason)``
otherwise. The reason is a short human-readable string suitable for surfacing
in the UI.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

#: Hard cap on input size. The LLM should never produce queries longer than a
#: few hundred bytes; 10 KB is generous and prevents prompt-injection bombing.
MAX_SQL_LENGTH = 10_000

#: Statement-level keywords that are never allowed. These cover every DuckDB
#: write / DDL / side-effect command we want to keep out of Dives.
BANNED_STATEMENT_KEYWORDS = frozenset({
    "INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT", "REPLACE",
    "DROP", "ALTER", "CREATE", "TRUNCATE", "RENAME", "GRANT", "REVOKE",
    "ATTACH", "DETACH", "USE", "SET",
    "PRAGMA", "COPY", "EXPORT", "IMPORT", "INSTALL", "LOAD", "UNLOAD",
    "VACUUM", "ANALYZE", "REINDEX", "CHECKPOINT", "BEGIN", "COMMIT",
    "ROLLBACK", "SAVEPOINT", "TRANSACTION", "EXEC", "EXECUTE", "CALL",
    "DESCRIBE", "SHOW", "EXPLAIN",
})

#: Dangerous SQL functions (file-system / shell / DB-attach style) that DuckDB
#: exposes. We block them by name; the lexer pass spots any identifier
#: immediately followed by ``(``.
BANNED_FUNCTIONS = frozenset({
    # File readers / writers
    "read_csv", "read_csv_auto", "read_parquet", "read_json",
    "read_json_auto", "read_ndjson", "read_ndjson_auto", "read_blob",
    "read_text", "read_xlsx", "parquet_scan", "csv_scan",
    "write_csv", "write_parquet", "write_json", "copy_to",
    # Filesystem / shell-ish
    "glob", "list_files", "system_function", "shell", "system",
    # HTTP / object stores
    "httpfs", "http_get", "http_post", "s3_get",
    # DB-attach helpers
    "sqlite_attach", "postgres_attach", "duckdb_attach", "attach_database",
    # Settings / pragma helpers
    "set_search_path", "current_setting", "set_config",
})

# Tables the Dives feature is allowed to read. The validator does NOT enforce
# this — table allowlisting belongs in the prompt + schema descriptor (#1002).
# We keep the list here as documentation only.
ALLOWED_TABLES = frozenset({
    "events", "sessions", "daily_aggregates", "memory_blobs",
    "heartbeats", "system_snapshots", "openclaw_channels",
    "crons", "subagents",
})

# Optional structural parse — best effort.
try:  # pragma: no cover - import guard
    import sqlglot  # type: ignore
    from sqlglot import expressions as _sg_exp  # type: ignore
    _SQLGLOT_AVAILABLE = True
except Exception:  # pragma: no cover
    sqlglot = None  # type: ignore
    _sg_exp = None  # type: ignore
    _SQLGLOT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Lexical helpers
# ---------------------------------------------------------------------------

_LINE_COMMENT_RE = re.compile(r"--[^\n]*")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
# Match SQL string literals (single-quoted, with doubled-quote escapes) plus
# double-quoted identifiers. Both are stripped before keyword scanning so a
# literal like ``'DROP TABLE x'`` doesn't trigger a false positive.
_STRING_RE = re.compile(
    r"'(?:''|[^'])*'"            # 'foo' or 'it''s'
    r"|\"(?:\"\"|[^\"])*\""      # "ident"
    r"|\$\$.*?\$\$",             # $$ dollar-quoted $$
    re.DOTALL,
)
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _strip_comments_and_strings(sql: str) -> str:
    """Return the SQL with comments + literals replaced by spaces.

    We replace (rather than delete) so character offsets stay stable, which
    keeps later regex behaviour predictable. The result is only used for
    keyword scanning — never executed.
    """
    out = _BLOCK_COMMENT_RE.sub(lambda m: " " * len(m.group(0)), sql)
    out = _LINE_COMMENT_RE.sub(lambda m: " " * len(m.group(0)), out)
    out = _STRING_RE.sub(lambda m: " " * len(m.group(0)), out)
    return out


def _split_statements(sanitized: str) -> list[str]:
    """Split on ``;`` boundaries. Strings/comments are already stripped, so any
    remaining semicolon is a real statement separator."""
    parts = [p.strip() for p in sanitized.split(";")]
    return [p for p in parts if p]


def _first_keyword(stmt: str) -> str | None:
    """Return the first SQL identifier token in *stmt*, uppercased."""
    m = _IDENT_RE.search(stmt)
    return m.group(0).upper() if m else None


def _contains_banned_function(sanitized: str) -> str | None:
    """Return the name of a banned function call found in *sanitized*, or None."""
    # Identifier followed by optional whitespace then '(' = function call.
    for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", sanitized):
        name = m.group(1).lower()
        if name in BANNED_FUNCTIONS:
            return name
    return None


def _contains_banned_keyword(sanitized: str) -> str | None:
    """Return any banned statement-level keyword found as a whole token."""
    for m in _IDENT_RE.finditer(sanitized):
        word = m.group(0).upper()
        if word in BANNED_STATEMENT_KEYWORDS:
            return word
    return None


# ---------------------------------------------------------------------------
# Optional sqlglot pass
# ---------------------------------------------------------------------------

def _sqlglot_check(sql: str) -> str | None:
    """Run sqlglot as defence-in-depth. Returns a rejection reason, or None.

    If sqlglot isn't installed we skip — the lexical pass already enforces the
    allowlist. If sqlglot is installed but fails to parse, we reject (a query
    we can't parse is a query we shouldn't execute).
    """
    if not _SQLGLOT_AVAILABLE:
        return None
    try:
        parsed = sqlglot.parse(sql, dialect="duckdb")
    except Exception as exc:  # noqa: BLE001
        return f"sqlglot parse failed: {exc.__class__.__name__}"

    parsed = [p for p in parsed if p is not None]
    if not parsed:
        return "empty parse tree"
    if len(parsed) > 1:
        return "multiple statements not allowed"

    root = parsed[0]
    # Allow Select, or a With that wraps a Select.
    if isinstance(root, _sg_exp.Select):
        return None
    if isinstance(root, _sg_exp.With):
        inner = root.this
        if isinstance(inner, _sg_exp.Select):
            return None
    # sqlglot wraps CTE-driven selects as Select with a `with` attribute.
    if isinstance(root, _sg_exp.Select) or (
        hasattr(root, "args") and isinstance(root.args.get("this"), _sg_exp.Select)
    ):
        return None
    return f"non-SELECT root: {root.__class__.__name__}"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def validate_sql(sql: str) -> tuple[bool, str | None]:
    """Validate *sql* against the Dives allowlist.

    Returns ``(True, None)`` if the query is safe, otherwise ``(False, reason)``.

    The validator is intentionally strict — when in doubt, reject. Any
    rejection reason returned here is suitable for showing to the user (it's
    short and doesn't leak internals).
    """
    if sql is None:
        return False, "empty query"
    if not isinstance(sql, str):
        return False, "query must be a string"

    stripped = sql.strip()
    if not stripped:
        return False, "empty query"
    if len(sql) > MAX_SQL_LENGTH:
        return False, f"query too long (> {MAX_SQL_LENGTH} bytes)"

    # Reject NUL / control bytes that have no business in a query and could
    # confuse downstream parsers.
    if "\x00" in sql:
        return False, "query contains NUL byte"

    sanitized = _strip_comments_and_strings(stripped)

    # Multi-statement check (post-sanitize so semicolons inside strings are
    # ignored).
    statements = _split_statements(sanitized)
    if len(statements) > 1:
        return False, "multiple statements not allowed"
    if not statements:
        # Only thing in the input was comments / whitespace.
        return False, "query contains no statement"

    head = _first_keyword(statements[0])
    if head is None:
        return False, "query contains no statement"
    if head not in ("SELECT", "WITH"):
        return False, f"only SELECT/WITH allowed (got {head})"

    banned_kw = _contains_banned_keyword(sanitized)
    if banned_kw:
        return False, f"banned keyword: {banned_kw}"

    banned_fn = _contains_banned_function(sanitized)
    if banned_fn:
        return False, f"banned function: {banned_fn}"

    sg_reason = _sqlglot_check(stripped)
    if sg_reason:
        return False, sg_reason

    return True, None


__all__ = [
    "validate_sql",
    "MAX_SQL_LENGTH",
    "BANNED_STATEMENT_KEYWORDS",
    "BANNED_FUNCTIONS",
    "ALLOWED_TABLES",
]
