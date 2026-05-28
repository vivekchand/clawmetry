"""Secret/credential redaction for snapshot data (issue #2198).

Applied daemon-side before snapshot data leaves the machine.  Default scope is
``"snapshot"`` (scrub on the way out to the cloud); ``"ingest"`` also scrubs
before the DuckDB write (loses local fidelity but maximises defense-in-depth).
Disabled by default — opt in via ``config.redact.enabled: true``.
"""

import re
import logging

log = logging.getLogger(__name__)

# Default patterns cover the most common secret shapes found in agent tool-call
# parameters and transcript content.  Users can append custom patterns via
# ``config.redact.patterns``.  Apache-2.0 reference set (OpenClaw plugin
# ecosystem); tune for false-positives in production.
_DEFAULT_PATTERNS: list[str] = [
    r'(?i)(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']?[a-z0-9_\-]{16,}',
    r'(?i)(password|passwd|pwd)["\']?\s*[:=]\s*["\'][^"\']+["\']',
    r'(?i)(secret|token|auth)["\']?\s*[:=]\s*["\']?[a-z0-9_\-]{16,}',
    r'(?i)bearer\s+[a-z0-9_\-]{20,}',
    r'(?i)(aws_secret|aws_access)[a-z_]*["\']?\s*[:=]\s*["\']?[a-zA-Z0-9/+=]{20,}',
    r'sk-[a-zA-Z0-9]{32,}',
    r'ghp_[a-zA-Z0-9]{36}',
    r'gho_[a-zA-Z0-9]{36}',
    r'glpat-[a-zA-Z0-9_\-]{20,}',
    r'xox[baprs]-[a-zA-Z0-9\-]{10,}',
]

# Module-level cache: (pattern_strings, compiled_patterns)
_compiled_cache: tuple[list[str], list[re.Pattern]] = ([], [])


def compile_patterns(extra: list[str] | None = None) -> list[re.Pattern]:
    """Return compiled patterns (default set + *extra*), cached by input list."""
    global _compiled_cache
    keys = _DEFAULT_PATTERNS + list(extra or [])
    if _compiled_cache[0] == keys:
        return _compiled_cache[1]
    out: list[re.Pattern] = []
    for p in keys:
        try:
            out.append(re.compile(p))
        except re.error as exc:
            log.warning("redact: skipping bad pattern %r: %s", p, exc)
    _compiled_cache = (keys, out)
    return out


def redact_value(v, patterns: list[re.Pattern], replacement: str) -> tuple:
    """Recursively scrub *v* (str/dict/list). Returns ``(scrubbed_value, count)``."""
    count = 0
    if isinstance(v, str):
        out = v
        for p in patterns:
            out, n = p.subn(replacement, out)
            count += n
        return out, count
    if isinstance(v, dict):
        out = {}
        for k, val in v.items():
            out[k], n = redact_value(val, patterns, replacement)
            count += n
        return out, count
    if isinstance(v, list):
        out = []
        for item in v:
            r, n = redact_value(item, patterns, replacement)
            out.append(r)
            count += n
        return out, count
    return v, 0


def build_redactor(config: dict):
    """Return a callable ``f(v) -> v`` bound to *config*, or ``None`` if disabled.

    The returned callable exposes a ``.scope`` attribute (``"snapshot"`` or
    ``"ingest"``) so callers know which data path to scrub.
    """
    rc = (config or {}).get("redact") if isinstance(config, dict) else None
    if not isinstance(rc, dict) or not rc.get("enabled"):
        return None
    patterns = compile_patterns(rc.get("patterns") or [])
    replacement = rc.get("replacement") or "[REDACTED]"
    scope = rc.get("scope") or "snapshot"

    def _apply(v):
        scrubbed, count = redact_value(v, patterns, replacement)
        if count:
            log.debug("redact: %d substitution(s) in snapshot data", count)
        return scrubbed

    _apply.scope = scope  # type: ignore[attr-defined]
    return _apply
