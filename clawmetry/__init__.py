"""ClawMetry — OpenClaw Observability Dashboard."""
import re as _re
import os as _os

# Read version directly from dashboard.py without importing it (avoids circular import)
def _read_version():
    try:
        db = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'dashboard.py')
        with open(db, 'r', encoding='utf-8') as f:
            for line in f:
                m = _re.match(r'^__version__\s*=\s*["\'](.+?)["\']', line)
                if m:
                    return m.group(1)
    except Exception:
        pass
    return "unknown"

__version__ = _read_version()

def main():
    """CLI entry point — delegates to dashboard.main()."""
    import sys, os
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from dashboard import main as _main
    _main()

__all__ = ["__version__", "main"]
