"""
ClawMetry configuration dataclass.
Phase 2: defines the Config structure that will replace global variables in Phase 3.
Currently used for type hints and documentation. dashboard.py globals remain unchanged.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


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
