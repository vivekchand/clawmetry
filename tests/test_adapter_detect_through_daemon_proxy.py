"""Guard: runtime detection must survive the daemon proxy.

Outside the daemon process ``local_store.get_store()`` returns a
``_ProxyStore`` that forwards ``query_*`` methods over the daemon's HTTP proxy
and REFUSES private helpers, because ``_fetch`` would be arbitrary SQL over the
RPC. It logs a warning and returns None.

``NemoClawAdapter.detect()`` ran ``store._fetch("SELECT COUNT(*) ...")``, so on
every standard install (the daemon owns the writer lock) it got None, counted
zero, and reported ``detected=False``. NemoClaw is one of the two FREE
runtimes, so it silently vanished from the runtime list, and the refusal
warning printed into `clawmetry status`. Found 2026-08-22.

Enrichment paths that DOCUMENT a proxy degradation (e.g.
``_nemoclaw_child_texts``) are deliberately not covered here: degrading extra
detail is an honest floor, whereas failing to detect the runtime at all is not.
"""
import ast
import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


class _FakeProxyStore:
    """Mimics _ProxyStore: query_* works, private helpers are refused."""

    def __init__(self, count=0):
        self._count = count
        self.fetch_attempts = 0

    def __getattr__(self, name):
        if name.startswith("_"):
            # _ProxyStore logs and returns a callable yielding None.
            def _refused(*a, **k):
                object.__getattribute__(self, "__dict__")["fetch_attempts"] = \
                    object.__getattribute__(self, "__dict__").get("fetch_attempts", 0) + 1
                return None
            return _refused
        raise AttributeError(name)

    def query_event_count(self, *, runtime=None):
        return self._count


def test_query_event_count_is_daemon_allowlisted():
    """An unlisted method 400s and the caller swallows it as 'no data'."""
    from routes.local_query import _DAEMON_METHODS

    assert "query_event_count" in _DAEMON_METHODS


def test_local_store_exposes_query_event_count():
    from clawmetry.local_store import LocalStore

    assert hasattr(LocalStore, "query_event_count")
    sig = inspect.signature(LocalStore.query_event_count)
    assert "runtime" in sig.parameters


def test_nemoclaw_is_detected_through_a_proxy_store(monkeypatch):
    """The regression: real data present, store is a proxy -> must detect."""
    from clawmetry.adapters.nemo import NemoClawAdapter
    import clawmetry.local_store as _ls

    fake = _FakeProxyStore(count=42)
    monkeypatch.setattr(_ls, "get_store", lambda *a, **k: fake)

    res = NemoClawAdapter().detect()
    assert res.detected is True, (
        "NemoClaw has 42 events but detect() reported not-detected: it is "
        "reading through a path the daemon proxy refuses"
    )
    assert res.meta.get("event_count") == 42
    assert fake.fetch_attempts == 0, "detect() still reached for a private helper"


def test_nemoclaw_absent_still_reports_not_detected(monkeypatch):
    """The fix must not turn detection into 'always true'."""
    from clawmetry.adapters.nemo import NemoClawAdapter
    import clawmetry.local_store as _ls

    monkeypatch.setattr(_ls, "get_store", lambda *a, **k: _FakeProxyStore(count=0))
    assert NemoClawAdapter().detect().detected is False


# ------------------------------------------------------------- class guard

def _adapter_classes():
    """Auto-discover adapters so a NEW one is covered without editing this."""
    import importlib
    import pkgutil

    import clawmetry.adapters as pkg

    out = []
    for mod in pkgutil.iter_modules(pkg.__path__):
        try:
            m = importlib.import_module(f"clawmetry.adapters.{mod.name}")
        except Exception:
            continue
        for attr in dir(m):
            obj = getattr(m, attr)
            if (isinstance(obj, type) and attr.endswith("Adapter")
                    and hasattr(obj, "detect")
                    and obj.__module__ == m.__name__):
                out.append((mod.name, attr, obj))
    return out


def test_adapters_discovered():
    assert _adapter_classes(), "no adapters discovered"


def test_no_adapter_detect_uses_a_non_proxyable_helper():
    """detect() may not call a private store helper.

    Detection runs in the dashboard and CLI processes, where the store is a
    proxy. A private helper there is silently None, which reads as 'runtime
    not installed'.
    """
    offenders = []
    for mod_name, cls_name, cls in _adapter_classes():
        try:
            src = inspect.getsource(cls.detect)
        except (OSError, TypeError):
            continue
        try:
            tree = ast.parse(__import__("textwrap").dedent(src))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr.startswith("_")
                    and not node.func.attr.startswith("__")):
                # store._fetch(...) and friends
                if isinstance(node.func.value, ast.Name) and \
                        node.func.value.id in ("store", "store_obj", "_store"):
                    offenders.append(f"{mod_name}.{cls_name}.detect -> {node.func.attr}()")
    assert not offenders, (
        "adapter detect() calls a helper the daemon proxy refuses, so the "
        "runtime will read as not-installed on any standard install: "
        + ", ".join(offenders)
    )
