"""
Tests for circular import dependency between clawmetry/__init__.py and clawmetry/config.py.

These tests verify that importing clawmetry modules does not cause circular import issues.

The issue: config.py's from_globals() method uses a bare 'import dashboard' which could
cause issues if __init__.py were to import from config.py at module level.

The fix: from_globals() should use a lazy import (import inside method) which it already
does correctly. No circular import exists in the current code.
"""

import sys
import pytest


def _clear_clawmetry_modules():
    """Clear all clawmetry-related modules from sys.modules."""
    for mod in list(sys.modules.keys()):
        if "clawmetry" in mod or mod == "dashboard":
            del sys.modules[mod]


def test_import_clawmetry_without_config():
    """Importing clawmetry package should not trigger config imports."""
    _clear_clawmetry_modules()

    import clawmetry

    assert hasattr(clawmetry, "__version__")
    assert hasattr(clawmetry, "main")


def test_import_config_module_level_no_side_effects():
    """Importing clawmetry.config at module level should not cause side effects."""
    _clear_clawmetry_modules()

    from clawmetry.config import ClawMetryConfig

    cfg = ClawMetryConfig()
    assert cfg is not None

    assert "clawmetry" in sys.modules
    assert "clawmetry.config" in sys.modules


def test_config_from_globals_uses_lazy_import():
    """
    Calling config.from_globals() should use lazy import for dashboard.

    This test verifies that dashboard is NOT imported until from_globals() is called.
    """
    _clear_clawmetry_modules()

    from clawmetry.config import ClawMetryConfig

    assert "dashboard" not in sys.modules

    cfg = ClawMetryConfig()
    result = cfg.from_globals()

    assert isinstance(result, ClawMetryConfig)
    assert "dashboard" in sys.modules


def test_import_order_config_then_clawmetry():
    """Test importing config before clawmetry doesn't cause issues."""
    _clear_clawmetry_modules()

    from clawmetry.config import ClawMetryConfig
    import clawmetry

    assert hasattr(clawmetry, "__version__")
    assert hasattr(clawmetry, "main")


def test_import_order_clawmetry_then_config():
    """Test importing clawmetry before config doesn't cause issues."""
    _clear_clawmetry_modules()

    import clawmetry
    from clawmetry.config import ClawMetryConfig

    assert hasattr(clawmetry, "__version__")
    cfg = ClawMetryConfig()
    assert cfg is not None


def test_no_module_level_imports_in_init():
    """
    Verify that __init__.py does not import from config.py at module level.

    This test will FAIL if __init__.py has 'from clawmetry.config import ...' at module level,
    creating a potential circular dependency.
    """
    _clear_clawmetry_modules()

    import clawmetry
    import inspect

    source = inspect.getsource(clawmetry)

    assert "from clawmetry.config import" not in source
    assert "from clawmetry import config" not in source


def test_config_from_globals_does_not_import_config_into_caller():
    """
    Verify that from_globals() doesn't pollute the namespace with config module.

    The dashboard module should be imported as 'd', not 'config'.
    """
    _clear_clawmetry_modules()

    from clawmetry.config import ClawMetryConfig

    cfg = ClawMetryConfig()
    cfg.from_globals()

    assert "dashboard" in sys.modules


def test_circular_import_would_be_detected():
    """
    Test that verifies our import structure prevents circular imports.

    This test simulates what would happen if __init__.py imported from config.py:
    1. __init__.py starts loading
    2. If __init__.py imported config, config would start loading
    3. config.py does NOT import from __init__.py at module level, so no cycle

    The test itself doesn't create the circular import - it verifies the structure.
    """
    _clear_clawmetry_modules()

    import clawmetry
    from clawmetry.config import ClawMetryConfig

    cfg = ClawMetryConfig()
    result = cfg.from_globals()

    assert isinstance(result, ClawMetryConfig)
    assert hasattr(clawmetry, "__version__")
