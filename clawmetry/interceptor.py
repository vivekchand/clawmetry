"""
clawmetry/interceptor.py — Zero-config HTTP monkey-patching.

Patches httpx (sync + async), requests, and urllib so that any LLM API call
is automatically captured. Never reads request bodies. Token counts are parsed
from the response JSON (which is already in memory at that point).

Design goals:
  - Sub-millisecond overhead on the hot path
  - Never throws — all errors silently swallowed
  - Idempotent: calling patch() twice is safe
"""
from __future__ import annotations

import threading
from typing import Any, Optional

from clawmetry.providers import detect_provider, get_cost, extract_usage

_patched_lock = threading.Lock()
_patched: set[str] = set()


# ──────────────────────────────────────────────────────────────────────────────
# Core handler — called after every response
# ──────────────────────────────────────────────────────────────────────────────

def _handle_response(url: str, response_body: Optional[bytes]) -> None:
    """Parse token usage from *response_body* and record cost. Never throws."""
    try:
        from clawmetry.ledger import get_ledger
        from clawmetry.providers import detect_provider, extract_usage, get_cost

        provider = detect_provider(url)
        if provider is None:
            return

        if not response_body:
            return

        usage = extract_usage(provider, response_body)
        if usage is None:
            return

        model = usage.get("model", "")
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))

        if input_tokens == 0 and output_tokens == 0:
            return

        cost = get_cost(provider, model, input_tokens, output_tokens)
        get_ledger().record(provider, model, input_tokens, output_tokens, cost)
    except Exception:
        pass


def _url_from_response(response: Any) -> str:
    """Extract URL string from various response objects."""
    try:
        # httpx Response → response.request.url  (httpx.URL object)
        req = getattr(response, "request", None)
        if req is not None:
            url = getattr(req, "url", None)
            if url is not None:
                return str(url)
    except Exception:
        pass
    try:
        url = getattr(response, "url", None)
        if url is not None:
            return str(url)
    except Exception:
        pass
    return ""


def _read_body_safe(response: Any) -> Optional[bytes]:
    """Return already-buffered body bytes without consuming a stream."""
    try:
        # httpx: .content property (bytes, already buffered after .read())
        content = getattr(response, "content", None)
        if isinstance(content, (bytes, bytearray)):
            return bytes(content)
    except Exception:
        pass
    try:
        # requests: .content (bytes)
        content = getattr(response, "_content", None)
        if isinstance(content, (bytes, bytearray)):
            return bytes(content)
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
# httpx patch
# ──────────────────────────────────────────────────────────────────────────────

def _patch_httpx() -> None:
    try:
        import httpx  # noqa: F401
    except ImportError:
        return

    with _patched_lock:
        if "httpx" in _patched:
            return
        _patched.add("httpx")

    import httpx

    # ── sync Client ──────────────────────────────────────────────────────────
    _orig_send = httpx.Client.send

    def _send(self, request, **kwargs):  # type: ignore[override]
        response = _orig_send(self, request, **kwargs)
        try:
            _handle_response(str(request.url), response.content)
        except Exception:
            pass
        return response

    httpx.Client.send = _send  # type: ignore[method-assign]

    # ── async Client ─────────────────────────────────────────────────────────
    _orig_async_send = httpx.AsyncClient.send

    async def _async_send(self, request, **kwargs):  # type: ignore[override]
        response = await _orig_async_send(self, request, **kwargs)
        try:
            _handle_response(str(request.url), response.content)
        except Exception:
            pass
        return response

    httpx.AsyncClient.send = _async_send  # type: ignore[method-assign]


# ──────────────────────────────────────────────────────────────────────────────
# requests patch
# ──────────────────────────────────────────────────────────────────────────────

def _patch_requests() -> None:
    try:
        import requests  # noqa: F401
    except ImportError:
        return

    with _patched_lock:
        if "requests" in _patched:
            return
        _patched.add("requests")

    import requests
    from requests import adapters

    _orig_send = adapters.HTTPAdapter.send

    def _adapter_send(self, request, **kwargs):  # type: ignore[override]
        response = _orig_send(self, request, **kwargs)
        try:
            _handle_response(request.url or "", response.content)
        except Exception:
            pass
        return response

    adapters.HTTPAdapter.send = _adapter_send  # type: ignore[method-assign]


# ──────────────────────────────────────────────────────────────────────────────
# urllib patch
# ──────────────────────────────────────────────────────────────────────────────

def _patch_urllib() -> None:
    with _patched_lock:
        if "urllib" in _patched:
            return
        _patched.add("urllib")

    import urllib.request as _ureq

    _orig_urlopen = _ureq.urlopen

    def _urlopen(url, data=None, timeout=None, **kwargs):  # type: ignore[override]
        response = _orig_urlopen(url, data=data, timeout=timeout, **kwargs)
        try:
            # urllib responses are streams; we wrap to intercept .read()
            return _UrllibResponseWrapper(response, _get_url(url))
        except Exception:
            return response

    def _get_url(url) -> str:
        if isinstance(url, str):
            return url
        if isinstance(url, urllib.request.Request):
            return url.full_url
        try:
            return str(url.full_url)
        except Exception:
            return ""

    _ureq.urlopen = _urlopen  # type: ignore[assignment]


class _UrllibResponseWrapper:
    """Wraps a urllib HTTPResponse to capture the body after .read()."""

    __slots__ = ("_resp", "_url", "_body_seen")

    def __init__(self, resp: Any, url: str) -> None:
        self._resp = resp
        self._url = url
        self._body_seen = False

    def read(self, amt: Optional[int] = None) -> bytes:
        try:
            if amt is None:
                body = self._resp.read()
            else:
                body = self._resp.read(amt)
            if not self._body_seen and amt is None:
                self._body_seen = True
                _handle_response(self._url, body)
            return body
        except Exception:
            return self._resp.read() if amt is None else self._resp.read(amt)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._resp, name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return self._resp.__exit__(*args)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def patch() -> None:
    """
    Monkey-patch httpx, requests, and urllib.

    Idempotent — safe to call multiple times. Any library not installed is
    silently skipped. Never raises.
    """
    try:
        _patch_httpx()
    except Exception:
        pass
    try:
        _patch_requests()
    except Exception:
        pass
    try:
        _patch_urllib()
    except Exception:
        pass


def patch_http(ledger: Any = None) -> None:
    """
    Alias for patch(). The *ledger* argument is accepted for API compatibility
    with sitecustomize_hook but is not required — the interceptor always uses
    the global singleton ledger from :func:`clawmetry.ledger.get_ledger`.
    """
    patch()
