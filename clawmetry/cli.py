"""CLI entry point for the clawmetry package."""
import sys
import os

# Ensure root dashboard.py is importable
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from dashboard import main  # noqa: F401

if __name__ == "__main__":
    main()
