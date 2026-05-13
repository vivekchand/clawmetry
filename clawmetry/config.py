"""
ClawMetry configuration dataclass.
Phase 2: defines the Config structure that will replace global variables in Phase 3.
Currently used for type hints and documentation. dashboard.py globals remain unchanged.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import List, Optional


# ── DuckDB local-store fast-path feature gate ──────────────────────────────
# Default flipped to ON in 0.12.174 (see PR feat/duckdb-default-on-2026-05-13).
# Prior to that release every route's DuckDB fast path was opt-in via
# CLAWMETRY_LOCAL_STORE_READ=1, which no installer/plist set, so 100% of users
# silently fell through to the legacy gateway/JSONL paths. Default-on is safe
# because every fast path is wrapped in try/except and falls through to the
# legacy code path on any miss (daemon down, query fails, no rows, etc).

# Disable values are checked case-insensitively after .strip(). Empty string
# is treated as disable so ``CLAWMETRY_LOCAL_STORE_READ=`` behaves the same
# as explicitly setting it to 0 (matches the task spec for the flip PR).
_LOCAL_STORE_DISABLE_VALUES = frozenset({"0", "false", "no", "off", ""})


def is_local_store_read_enabled() -> bool:
    """Return True unless explicitly disabled via CLAWMETRY_LOCAL_STORE_READ=0.

    Defaults to ON since 0.12.174. Set ``CLAWMETRY_LOCAL_STORE_READ=0`` (or
    ``false`` / ``no`` / ``off``) to force the legacy gateway/JSONL path —
    useful for A/B comparisons or to bypass a corrupt local store.

    Fast paths fall through to the legacy path on any miss, so default-on is
    safe even when the daemon isn't running. See routes/*.py — every caller
    of this helper wraps its DuckDB read in try/except + None-on-failure.
    """
    # Default "1" so unset env → enabled. Pre-flip behaviour (default OFF)
    # required CLAWMETRY_LOCAL_STORE_READ=1, which no installer set.
    return os.environ.get("CLAWMETRY_LOCAL_STORE_READ", "1").strip().lower() \
        not in _LOCAL_STORE_DISABLE_VALUES


@dataclass
class ClawMetryConfig:
    """
    Unified configuration for ClawMetry.

    In Phase 3, this will replace the module-level globals in dashboard.py:
    WORKSPACE, SESSIONS_DIR, LOG_DIR, MEMORY_DIR, METRICS_FILE, etc.
    """

    # Paths
    workspace: str = ""
    sessions_dir: str = ""
    log_dir: str = ""
    memory_dir: str = ""
    metrics_file: str = ""
    fleet_db: str = ""

    # Gateway
    gateway_url: str = ""
    gateway_token: str = ""
    gateway_port: int = 18789

    # Runtime
    model: str = ""
    provider: str = ""
    channels: List[str] = field(default_factory=list)
    host: str = "127.0.0.1"
    port: int = 8900
    debug: bool = False

    # Auth
    auth_token: Optional[str] = None

    def from_globals(self, _dashboard_module=None) -> "ClawMetryConfig":
        """
        Populate from dashboard.py module-level globals (migration bridge).

        Args:
            _dashboard_module: Optional dashboard module to use instead of importing.
                             If None, will attempt to import dashboard dynamically.

        This method uses a lazy import pattern to avoid circular dependencies.
        The dashboard module is only imported when this method is called, not at
        module load time.
        """
        try:
            if _dashboard_module is not None:
                d = _dashboard_module
            else:
                import importlib
                import sys

                for mod in list(sys.modules.keys()):
                    if mod == "dashboard" or mod.startswith("dashboard."):
                        d = sys.modules[mod]
                        break
                else:
                    d = importlib.import_module("dashboard")

            self.workspace = getattr(d, "WORKSPACE", "") or ""
            self.sessions_dir = getattr(d, "SESSIONS_DIR", "") or ""
            self.log_dir = getattr(d, "LOG_DIR", "") or ""
            self.memory_dir = getattr(d, "MEMORY_DIR", "") or ""
            self.metrics_file = getattr(d, "METRICS_FILE", "") or ""
            self.gateway_token = getattr(d, "_AUTH_TOKEN", "") or ""
        except (ImportError, AttributeError):
            pass
        return self
