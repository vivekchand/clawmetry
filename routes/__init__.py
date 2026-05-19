"""Shared helpers for route modules."""

from __future__ import annotations

from typing import Callable, Optional, TypeVar, Union

F = TypeVar("F", bound=Callable)


def source_exempt(*, reason: str) -> Callable[[F], F]:
    """Mark a route as intentionally exempt from the local-store source canary.

    Use this only for routes that do not serve event-derived OSS data, such as
    gateway pass-throughs or OTLP receivers. The reason is required so the
    canary output explains why the endpoint is skipped.
    """
    reason = (reason or "").strip()
    if not reason:
        raise ValueError("source_exempt requires a non-empty reason")

    def decorator(func: F) -> F:
        setattr(func, "_source_exempt", True)
        setattr(func, "_source_exempt_reason", reason)
        return func

    return decorator


def event_data(func: Optional[F] = None) -> Union[F, Callable[[F], F]]:
    """Mark a route as serving event-derived data for the source canary."""

    def decorator(inner: F) -> F:
        setattr(inner, "_event_data", True)
        return inner

    if func is None:
        return decorator
    return decorator(func)
