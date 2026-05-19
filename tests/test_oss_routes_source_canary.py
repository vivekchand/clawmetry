"""OSS route-source canary for event-derived API responses.

The MOAT send-message E2E test already proves a hand-picked set of routes
serve from DuckDB. This file keeps that contract tied to Flask's blueprint
registry: each canary case names a registered endpoint, the test builds its
URL from ``app.url_map``, then asserts the JSON envelope says
``_source == "local_store"``.

Run as::

    python3 -m pytest tests/test_oss_routes_source_canary.py -v
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from flask import jsonify, url_for

from routes import event_data, source_exempt
from tests.test_moat_send_message_e2e import (
    CHANNEL_PROVIDER,
    env,  # noqa: F401 - re-exported pytest fixture
    _seed_session_events,
    _seed_session_metadata,
    _seed_telegram_message,
)


TOKEN = "oss-source-canary-token"


@dataclass(frozen=True)
class CanaryCase:
    endpoint: str
    values: dict[str, object] = field(default_factory=dict)
    seeded_modes: tuple[str, ...] = ("full",)


CANARY_CASES = (
    CanaryCase("sessions.api_sessions", seeded_modes=("full", "empty_events")),
    CanaryCase("brain.api_brain_history", {"limit": 50}, ("full", "empty_events")),
    CanaryCase("usage.api_usage"),
    CanaryCase(
        "channels.api_channel_messages",
        {"provider": CHANNEL_PROVIDER, "limit": 10},
    ),
    CanaryCase(
        "channels.api_channel_threads",
        {"provider": CHANNEL_PROVIDER, "limit": 10},
    ),
    CanaryCase("channels.api_channels_summary", seeded_modes=("full", "empty_events")),
)


def _app(env_):
    return env_["client"].application


def _headers():
    return {"Authorization": f"Bearer {TOKEN}"}


def _install_exempt_route(app):
    if "canary.gateway_passthrough" in app.view_functions:
        return

    @source_exempt(reason="gateway pass-through")
    @event_data
    def gateway_passthrough():
        return jsonify({"ok": True, "source": "gateway"})

    app.add_url_rule(
        "/api/canary/gateway-passthrough",
        endpoint="canary.gateway_passthrough",
        view_func=gateway_passthrough,
        methods=["GET"],
    )


def _seed(env_, mode: str) -> None:
    if mode == "empty_events":
        # The sessions table has metadata, but the events/channel tables are
        # empty. This guards the empty-fastpath class without falling through
        # to JSONL/gateway data.
        _seed_session_metadata(env_)
        return

    store = env_["ls"].get_store()
    _seed_telegram_message(store, text="oss source canary inbound msg")
    _seed_session_events(env_)
    _seed_session_metadata(env_)


def _registered_case_by_endpoint(app) -> dict[str, CanaryCase]:
    cases = {case.endpoint: case for case in CANARY_CASES}
    registered = {rule.endpoint for rule in app.url_map.iter_rules()}
    missing = sorted(set(cases) - registered)
    assert not missing, (
        "source canary cases are not registered in Flask url_map: "
        + ", ".join(missing)
    )
    return cases


def _canary_urls(app, mode: str):
    cases = _registered_case_by_endpoint(app)
    urls = []
    exemptions = []

    with app.test_request_context():
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
            if "GET" not in rule.methods or rule.endpoint == "static":
                continue
            view_func = app.view_functions[rule.endpoint]
            case = cases.get(rule.endpoint)
            is_marked_event_data = bool(getattr(view_func, "_event_data", False))
            if case is None and not is_marked_event_data:
                continue

            if getattr(view_func, "_source_exempt", False):
                reason = getattr(view_func, "_source_exempt_reason", "")
                exemptions.append((rule.endpoint, rule.rule, reason))
                continue

            if case is None:
                if rule.arguments:
                    raise AssertionError(
                        f"event-data endpoint {rule.endpoint!r} has route "
                        f"arguments {sorted(rule.arguments)!r}; add a "
                        "CanaryCase with sample values or mark "
                        "@source_exempt(reason=...)"
                    )
                urls.append((rule.endpoint, url_for(rule.endpoint)))
                continue

            if mode not in case.seeded_modes:
                continue
            urls.append((rule.endpoint, url_for(rule.endpoint, **case.values)))

    return urls, exemptions


def _assert_local_store_sources(env_, mode: str, record_property=None) -> None:
    app = _app(env_)
    client = env_["client"]
    urls, exemptions = _canary_urls(app, mode)
    if record_property is not None:
        record_property("source_exemptions", len(exemptions))

    failures = []
    for _endpoint, path in urls:
        response = client.get(path, headers=_headers())
        label = f"GET {path}"
        if response.status_code != 200:
            failures.append(
                f"endpoint {label!r} returned HTTP {response.status_code} "
                "-- add _source='local_store' or mark @source_exempt(reason=...)"
            )
            continue

        body = response.get_json(silent=True)
        if not isinstance(body, dict):
            failures.append(
                f"endpoint {label!r} did not return a JSON object "
                "-- add _source='local_store' or mark @source_exempt(reason=...)"
            )
            continue

        source = body.get("_source")
        if source is None:
            failures.append(
                f"endpoint {label!r} missing _source "
                "-- add _source='local_store' or mark @source_exempt(reason=...)"
            )
        elif source != "local_store":
            failures.append(
                f"endpoint {label!r} expected _source='local_store', "
                f"got {source!r} -- add _source='local_store' or mark "
                "@source_exempt(reason=...)"
            )

    assert not failures, "OSS local-store source canary failed:\n" + "\n".join(
        f"  {failure}" for failure in failures
    )


@pytest.mark.parametrize("mode", ["full", "empty_events"])
def test_event_data_routes_report_local_store_source(env, mode, record_property):
    app = _app(env)
    _install_exempt_route(app)
    _seed(env, mode)

    _assert_local_store_sources(env, mode, record_property)


def test_source_canary_fails_when_event_data_route_drops_source(env, monkeypatch):
    _install_exempt_route(_app(env))
    _seed(env, "full")

    def missing_source():
        return jsonify({"events": []})

    monkeypatch.setitem(
        _app(env).view_functions,
        "brain.api_brain_history",
        missing_source,
    )

    with pytest.raises(
        AssertionError,
        match=r"GET /api/brain-history\?limit=50.*missing _source",
    ):
        _assert_local_store_sources(env, "full")


def test_source_exempt_routes_are_skipped_with_reason(env):
    app = _app(env)
    _install_exempt_route(app)

    _, exemptions = _canary_urls(app, "full")

    assert (
        "canary.gateway_passthrough",
        "/api/canary/gateway-passthrough",
        "gateway pass-through",
    ) in exemptions
