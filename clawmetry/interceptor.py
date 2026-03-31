"""
clawmetry/interceptor.py — Zero-config HTTP interceptor for LLM API cost tracking.

Monkey-patches httpx.Client.send and requests.Session.send on import to intercept
LLM API calls and write cost data to ~/.openclaw/clawmetry-intercepted.jsonl.

ClawMetry picks up this file via its existing sync mechanism.

Activation options:
  1. Import directly:          import clawmetry.interceptor
  2. Environment variable:     CLAWMETRY_INTERCEPT=1  (auto-activates on clawmetry startup)

Design goals:
  - Zero user code changes
  - Silently no-ops if library not installed
  - Thread-safe JSONL writes
  - Never crashes the host application
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import re

# ── Config ─────────────────────────────────────────────────────────────────────

# LLM provider URL patterns to intercept
_LLM_URL_PATTERNS = [
    "api.anthropic.com",
    "api.openai.com",
    "generativelanguage.googleapis.com",
    "openrouter.ai",
]

# Output file — in OpenClaw dir so ClawMetry sync picks it up
def _get_output_file() -> Path:
    openclaw_dir = os.environ.get("CLAWMETRY_OPENCLAW_DIR", str(Path.home() / ".openclaw"))
    return Path(openclaw_dir) / "clawmetry-intercepted.jsonl"


# Write lock for thread-safe JSONL appends
_write_lock = threading.Lock()

# Track whether we've already patched each library
_patched_httpx = False
_patched_requests = False


# ── Pricing table (per 1M tokens, USD) ────────────────────────────────────────

_PRICING: Dict[str, Dict[str, float]] = {
    # Anthropic
    "claude-opus-4": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4": {"input": 3.0, "output": 15.0},
    "claude-haiku-4": {"input": 0.8, "output": 4.0},
    "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku": {"input": 0.8, "output": 4.0},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    # OpenAI
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "o1": {"input": 15.0, "output": 60.0},
    "o1-mini": {"input": 3.0, "output": 12.0},
    "o3-mini": {"input": 1.1, "output": 4.4},
    # Google
    "gemini-2.0-flash": {"input": 0.1, "output": 0.4},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.0},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.3},
    "gemini-1.0-pro": {"input": 0.5, "output": 1.5},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> Optional[float]:
    """Estimate cost in USD for given model and token counts."""
    if not model or (input_tokens == 0 and output_tokens == 0):
        return None
    # Find best match (model names can have version suffixes like -20240229)
    model_lower = model.lower()
    for key, prices in _PRICING.items():
        if key in model_lower:
            cost = (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
            return round(cost, 8)
    return None


# ── URL detection ──────────────────────────────────────────────────────────────

def _is_llm_url(url: str) -> bool:
    """Return True if the URL looks like an LLM provider endpoint."""
    if not url:
        return False
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in _LLM_URL_PATTERNS)


def _detect_provider(url: str) -> str:
    """Detect provider name from URL."""
    url_lower = url.lower()
    if "anthropic.com" in url_lower:
        return "anthropic"
    if "openai.com" in url_lower:
        return "openai"
    if "googleapis.com" in url_lower:
        return "google"
    if "openrouter.ai" in url_lower:
        return "openrouter"
    return "unknown"


# ── Request/Response parsing ───────────────────────────────────────────────────

def _extract_model_from_body(body_bytes: bytes, url: str) -> Optional[str]:
    """Try to extract model name from request body JSON."""
    if not body_bytes:
        return None
    try:
        body = json.loads(body_bytes.decode("utf-8", errors="replace"))
        # Standard field across providers
        model = body.get("model") or body.get("modelId")
        if isinstance(model, str):
            return model
        # Google: model embedded in URL path like /v1beta/models/gemini-1.5-pro:generateContent
        if "googleapis.com" in url:
            match = re.search(r"/models/([^/:?]+)", url)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


def _extract_tokens_from_response(body_bytes: bytes, provider: str) -> Dict[str, int]:
    """Extract input/output token counts from response body."""
    result = {"input_tokens": 0, "output_tokens": 0}
    if not body_bytes:
        return result
    try:
        body = json.loads(body_bytes.decode("utf-8", errors="replace"))

        if provider == "anthropic":
            usage = body.get("usage", {})
            result["input_tokens"] = usage.get("input_tokens", 0)
            result["output_tokens"] = usage.get("output_tokens", 0)

        elif provider in ("openai", "openrouter"):
            usage = body.get("usage", {})
            result["input_tokens"] = usage.get("prompt_tokens", 0)
            result["output_tokens"] = usage.get("completion_tokens", 0)

        elif provider == "google":
            # Gemini API response
            meta = body.get("usageMetadata", {})
            result["input_tokens"] = meta.get("promptTokenCount", 0)
            result["output_tokens"] = meta.get("candidatesTokenCount", 0)

    except Exception:
        pass
    return result


def _extract_model_from_response(body_bytes: bytes, provider: str) -> Optional[str]:
    """Some providers echo the model in the response."""
    if not body_bytes:
        return None
    try:
        body = json.loads(body_bytes.decode("utf-8", errors="replace"))
        model = body.get("model")
        if isinstance(model, str):
            return model
    except Exception:
        pass
    return None


# ── JSONL writer ───────────────────────────────────────────────────────────────

def _write_event(event: Dict[str, Any]) -> None:
    """Thread-safely append an event to the JSONL output file."""
    try:
        out_file = _get_output_file()
        out_file.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event, separators=(",", ":")) + "\n"
        with _write_lock:
            with open(out_file, "a", encoding="utf-8") as f:
                f.write(line)
    except Exception:
        pass  # Never crash the host application


def _build_event(
    provider: str,
    url: str,
    model: Optional[str],
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    status_code: int,
    library: str,
) -> Dict[str, Any]:
    """Build the event dict to write to JSONL."""
    cost = _estimate_cost(model or "", input_tokens, output_tokens)
    event: Dict[str, Any] = {
        "type": "llm_call",
        "ts": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "url": url,
        "library": library,
        "status_code": status_code,
        "latency_ms": round(latency_ms, 1),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }
    if model:
        event["model"] = model
    if cost is not None:
        event["cost_usd"] = cost
    return event


# ── httpx patching ─────────────────────────────────────────────────────────────

def _patch_httpx() -> bool:
    """Monkey-patch httpx.Client.send. Returns True on success."""
    global _patched_httpx
    if _patched_httpx:
        return True
    try:
        import httpx

        _original_send = httpx.Client.send

        def _intercepted_send(self: httpx.Client, request: httpx.Request, **kwargs: Any) -> httpx.Response:
            url = str(request.url)
            if not _is_llm_url(url):
                return _original_send(self, request, **kwargs)

            provider = _detect_provider(url)

            # Read request body
            req_body = b""
            try:
                req_body = request.content
            except Exception:
                pass

            model = _extract_model_from_body(req_body, url)

            t0 = time.monotonic()
            response = _original_send(self, request, **kwargs)
            latency_ms = (time.monotonic() - t0) * 1000

            # Read response body (may need to buffer streaming responses)
            resp_body = b""
            try:
                resp_body = response.content
            except Exception:
                pass

            tokens = _extract_tokens_from_response(resp_body, provider)
            resp_model = _extract_model_from_response(resp_body, provider)
            final_model = resp_model or model

            event = _build_event(
                provider=provider,
                url=url,
                model=final_model,
                input_tokens=tokens["input_tokens"],
                output_tokens=tokens["output_tokens"],
                latency_ms=latency_ms,
                status_code=response.status_code,
                library="httpx",
            )
            _write_event(event)
            return response

        httpx.Client.send = _intercepted_send  # type: ignore[method-assign]

        # Also patch async client
        try:
            _original_async_send = httpx.AsyncClient.send

            async def _intercepted_async_send(
                self: httpx.AsyncClient, request: httpx.Request, **kwargs: Any
            ) -> httpx.Response:
                url = str(request.url)
                if not _is_llm_url(url):
                    return await _original_async_send(self, request, **kwargs)

                provider = _detect_provider(url)
                req_body = b""
                try:
                    req_body = request.content
                except Exception:
                    pass

                model = _extract_model_from_body(req_body, url)

                t0 = time.monotonic()
                response = await _original_async_send(self, request, **kwargs)
                latency_ms = (time.monotonic() - t0) * 1000

                resp_body = b""
                try:
                    resp_body = response.content
                except Exception:
                    pass

                tokens = _extract_tokens_from_response(resp_body, provider)
                resp_model = _extract_model_from_response(resp_body, provider)
                final_model = resp_model or model

                event = _build_event(
                    provider=provider,
                    url=url,
                    model=final_model,
                    input_tokens=tokens["input_tokens"],
                    output_tokens=tokens["output_tokens"],
                    latency_ms=latency_ms,
                    status_code=response.status_code,
                    library="httpx.async",
                )
                _write_event(event)
                return response

            httpx.AsyncClient.send = _intercepted_async_send  # type: ignore[method-assign]
        except Exception:
            pass  # Async patch failure is non-fatal

        _patched_httpx = True
        return True
    except ImportError:
        return False  # httpx not installed — skip silently
    except Exception:
        return False  # Any other error — skip silently


# ── requests patching ──────────────────────────────────────────────────────────

def _patch_requests() -> bool:
    """Monkey-patch requests.Session.send. Returns True on success."""
    global _patched_requests
    if _patched_requests:
        return True
    try:
        import requests

        _original_session_send = requests.Session.send

        def _intercepted_session_send(
            self: requests.Session,
            request: requests.PreparedRequest,
            **kwargs: Any,
        ) -> requests.Response:
            url = str(request.url or "")
            if not _is_llm_url(url):
                return _original_session_send(self, request, **kwargs)

            provider = _detect_provider(url)

            # Read request body
            req_body = b""
            try:
                body = request.body
                if isinstance(body, bytes):
                    req_body = body
                elif isinstance(body, str):
                    req_body = body.encode("utf-8")
            except Exception:
                pass

            model = _extract_model_from_body(req_body, url)

            t0 = time.monotonic()
            response = _original_session_send(self, request, **kwargs)
            latency_ms = (time.monotonic() - t0) * 1000

            resp_body = b""
            try:
                resp_body = response.content
            except Exception:
                pass

            tokens = _extract_tokens_from_response(resp_body, provider)
            resp_model = _extract_model_from_response(resp_body, provider)
            final_model = resp_model or model

            event = _build_event(
                provider=provider,
                url=url,
                model=final_model,
                input_tokens=tokens["input_tokens"],
                output_tokens=tokens["output_tokens"],
                latency_ms=latency_ms,
                status_code=response.status_code,
                library="requests",
            )
            _write_event(event)
            return response

        requests.Session.send = _intercepted_session_send  # type: ignore[method-assign]
        _patched_requests = True
        return True
    except ImportError:
        return False  # requests not installed — skip silently
    except Exception:
        return False


# ── Public API ─────────────────────────────────────────────────────────────────

def activate() -> Dict[str, bool]:
    """
    Explicitly activate the interceptor.

    Returns a dict of {library_name: patched_successfully}.
    Safe to call multiple times — idempotent.
    """
    return {
        "httpx": _patch_httpx(),
        "requests": _patch_requests(),
    }


def get_output_file() -> Path:
    """Return the path to the intercepted calls JSONL file."""
    return _get_output_file()


# ── Auto-activate on import ────────────────────────────────────────────────────
# Patching happens immediately when this module is imported.
# Failures are silently swallowed so the host application is never disrupted.

_patch_httpx()
_patch_requests()
