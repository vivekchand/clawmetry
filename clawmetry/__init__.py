"""ClawMetry — OpenClaw Observability Dashboard."""
import sys
import os

# Ensure root dashboard.py is importable when this package is imported
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from dashboard import __version__, main, app  # noqa: F401

__all__ = ["__version__", "main", "app"]
