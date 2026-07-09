"""Cross-adapter no-leak contract for the runtime switcher.

Seeds events from every known runtime (claude_code / qwen_code / codex / hermes
/ goose / opencode / openclaw / cursor / nanoclaw / picoclaw / aider) plus a
prefix-less session that should bucket to ``openclaw`` (the default), then
asserts that the runtime-aware endpoints scope correctly with zero cross-
adapter leakage:

- ``/api/model-attribution?runtime=<rt>`` returns ONLY that runtime's turns;
  the total must match the seeded count exactly (no leakage, no loss).
- ``/api/runtime-summary`` buckets each session into exactly one runtime; the
  per-runtime ``turns`` / ``primary_model`` reflect only that runtime's seeds.
- The pure ``_runtime_of_session`` bucketing function (mirrored from the
  frontend ``_cmRuntimeOf`` and ``sync._runtime_of_session``) classifies every
  known prefix and falls unrecognised prefixes / bare UUIDs back to openclaw.

Pinned regression guard for the runtime-leak bugs in screenshots:
- Brain density chart that wasn't filtering by runtime (#image-14) — caught
  client-side; the matching client-side check is in test_appjs_units.js.
- "OpenClaw" view leaking events from non-OpenClaw-prefixed sessions
  (#image-15) — caught here at the aggregation layer.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


# Mirror the frontend `_cmRuntimeOf` and `sync._runtime_of_session` — when
# either drifts from this list, the no-leak tests below catch it.
KNOWN_RUNTIMES = [
    "picoclaw", "nanoclaw", "hermes", "claude_code", "codex", "cursor",
    "aider", "goose", "opencode", "qwen_code", "pi", "deepagents",
]


def runtime_of(sid: str) -> str:
    """Python mirror of the frontend `_cmRuntimeOf`."""
    sid = sid or ""
    if ":" in sid:
        p = sid.split(":", 1)[0].lower()
        if p in KNOWN_RUNTIMES:
            return p
    return "openclaw"


def _iso(s: float) -> str:
    return datetime.fromtimestamp(s, tz=timezone.utc).isoformat()


def _wait_flush(store, t: float = 2.0) -> None:
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def app_and_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)
    import routes.usage as usage_mod
    importlib.reload(usage_mod)
    a = Flask(__name__)
    a.register_blueprint(usage_mod.bp_usage)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed(store, sid: str, model: str, ts: float) -> None:
    store.ingest({
        "id": sid + "-" + str(int(ts * 1000)),
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": sid,
        "event_type": "tool_call",
        "ts": _iso(ts),
        "data": {"tool_name": "X"},
        "cost_usd": 0.01,
        "token_count": 100,
        "model": model,
    })


def _seed_span(store, *, agent_type: str, service_name: str, span_id: str,
               ts: float, model: str = "", cost: float = 0.0, tokens: int = 0,
               session_id: str | None = None) -> None:
    """Seed one OTLP-shaped span (#2822: agent_type stamped from service.name)."""
    store.ingest_span({
        "span_id": span_id,
        "trace_id": "trace-" + span_id,
        "agent_type": agent_type,
        "service_name": service_name,
        "session_id": session_id,
        "name": "chat" if model else "op",
        "start_ts": ts,
        "end_ts": ts + 0.1,
        "model": model or None,
        "cost_usd": cost,
        "token_count": tokens,
    })


# ── 1. Pure bucketing function ──────────────────────────────────────────────


def test_runtime_of_session_classifies_every_known_runtime():
    """Every known prefix lands in its own bucket; unknowns → openclaw."""
    for rt in KNOWN_RUNTIMES:
        assert runtime_of(rt + ":anything") == rt, f"{rt} mis-bucketed"
    # Unknowns and bare UUIDs default to openclaw.
    assert runtime_of("openclaw:abc") == "openclaw"
    assert runtime_of("625c0ad9-71af-4a56-9a3b") == "openclaw"
    assert runtime_of("clawmetry-selfevolve") == "openclaw"
    assert runtime_of("unknown_future_runtime:xyz") == "openclaw"
    assert runtime_of("") == "openclaw"
    assert runtime_of(None) == "openclaw"


def test_picoclaw_never_mis_buckets_to_pi():
    """Regression guard for the pi runtime: "pi" is a leading substring of
    "picoclaw", so a startswith-style matcher would swallow every PicoClaw
    session into the pi bucket. The matcher exact-matches the token before the
    first ':' (the daemon stamps ``<runtime>:<raw id>``), so picoclaw ids must
    keep bucketing to picoclaw, and a raw un-namespaced ``pi-...`` id (no
    colon) must fall back to openclaw, never pi."""
    from clawmetry.sync import _runtime_of_session

    for fn in (runtime_of, _runtime_of_session):
        assert fn("picoclaw:abc") == "picoclaw", fn
        assert fn("pi:abc") == "pi", fn
        assert fn("deepagents:abc") == "deepagents", fn
        # Raw adapter ids without the daemon's ``<runtime>:`` namespace carry
        # no colon, so they take the openclaw default (never a prefix guess).
        assert fn("pi-0a1b2c") == "openclaw", fn
        assert fn("deepagents-0a1b2c") == "openclaw", fn
        # And the exact-token match means neither swallows the other even if a
        # raw id embeds a colon later in the string.
        assert fn("picoclaw:pi:abc") == "picoclaw", fn


# ── 2. /api/model-attribution?runtime= scopes with zero leakage ─────────────


def test_model_attribution_per_runtime_no_leak(app_and_store):
    a, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    # Two claude_code sessions, one of each other runtime, plus a bare-UUID
    # session that must bucket to openclaw.
    seeds = {
        "claude_code:c1": "claude-opus-4-7",
        "claude_code:c2": "claude-opus-4-7",
        "qwen_code:q1":   "qwen3:8b",
        "codex:x1":       "gpt-5",
        "hermes:h1":      "hermes-fast",
        "goose:g1":       "goose-lite",
        "opencode:o1":    "opencode-1",
        "cursor:k1":      "cursor-mid",
        "nanoclaw:n1":    "nano-1",
        "picoclaw:p1":    "pico-1",
        "aider:a1":       "aider-1",
        "pi:i1":          "pi-mini",
        "deepagents:d1":  "deep-1",
        "bareuuid-zzz":   "claude-opus-4-7",   # → openclaw bucket
    }
    for i, (sid, m) in enumerate(seeds.items()):
        _seed(store, sid, m, now - 600 + i)
    _wait_flush(store)
    cli = a.test_client()

    # For each runtime, scope the endpoint and assert the total turns match
    # exactly what we seeded for that runtime — no more (leak), no less (loss).
    for rt in KNOWN_RUNTIMES + ["openclaw"]:
        body = cli.get("/api/model-attribution?runtime=" + rt).get_json() or {}
        expected = sum(1 for sid in seeds if runtime_of(sid) == rt)
        actual = body.get("total_turns") or 0
        assert actual == expected, (
            f"{rt}: expected {expected} turns, got {actual}. Body={body}")
        # And the returned models, summed, must equal total_turns (no model
        # column from another runtime sneaking in).
        models_sum = sum(int(m.get("turns") or 0) for m in (body.get("models") or []))
        assert models_sum == actual, f"{rt}: model rows sum {models_sum} != total {actual}"
        # Empty case: an honest empty set, never a silent merge.
        if expected == 0:
            assert (body.get("models") or []) == [], f"{rt}: expected empty models, got {body.get('models')}"


# ── 3. /api/runtime-summary buckets every session into one runtime ──────────


def test_runtime_summary_buckets_each_session_into_one_runtime(app_and_store):
    a, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    seeds = {
        "claude_code:c1": "claude-opus-4-7",
        "claude_code:c2": "claude-opus-4-7",
        "qwen_code:q1":   "qwen3:8b",
        "codex:x1":       "gpt-5",
        "bareuuid-aaa":   "claude-opus-4-7",   # → openclaw
        "bareuuid-bbb":   "claude-opus-4-7",   # → openclaw
    }
    for i, (sid, m) in enumerate(seeds.items()):
        _seed(store, sid, m, now - 600 + i)
    _wait_flush(store)
    body = a.test_client().get("/api/runtime-summary").get_json() or {}
    runtimes = body.get("runtimes") or {}

    # Expected per-runtime turn counts.
    expected_turns = {}
    for sid in seeds:
        rt = runtime_of(sid)
        expected_turns[rt] = expected_turns.get(rt, 0) + 1

    # No runtime in the response that wasn't seeded.
    for rt in runtimes:
        assert rt in expected_turns, f"unexpected runtime in response: {rt}"
    # Each seeded runtime has the right turn count + the right primary model.
    for rt, exp in expected_turns.items():
        assert rt in runtimes, f"missing runtime in response: {rt}"
        assert runtimes[rt]["turns"] == exp, (
            f"{rt}: expected {exp} turns, got {runtimes[rt]['turns']}")
    # Sum across runtimes equals total seeds (every session bucketed once).
    assert sum(runtimes[rt]["turns"] for rt in runtimes) == len(seeds)

    # Sanity: claude_code's primary is claude-opus, qwen's is qwen3:8b.
    assert runtimes["claude_code"]["primary_model"] == "claude-opus-4-7"
    assert runtimes["qwen_code"]["primary_model"] == "qwen3:8b"


# ── 4. /api/usage?runtime= scopes with zero leakage ────────────────────────


def test_usage_api_per_runtime_no_leak(app_and_store):
    """Seeding distinct token counts per runtime and querying /api/usage?runtime=
    must return exactly that runtime's tokens — no cross-adapter leak or loss."""
    a, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    seeds = {
        "claude_code:c1": ("claude-opus-4-7", 500),
        "qwen_code:q1":   ("qwen3:8b",        300),
        "bareuuid-z1":    ("claude-opus-4-7", 200),  # → openclaw bucket
    }
    for i, (sid, (model, toks)) in enumerate(seeds.items()):
        store.ingest({
            "id": f"{sid}-{i}",
            "node_id": "test",
            "agent_id": "main",
            "session_id": sid,
            "event_type": "tool_call",
            "ts": _iso(now - 3600 + i),
            "data": {},
            "cost_usd": 0.01,
            "token_count": toks,
            "model": model,
        })
    _wait_flush(store)
    cli = a.test_client()

    expected_tokens = {"claude_code": 500, "qwen_code": 300, "openclaw": 200}
    for rt, exp in expected_tokens.items():
        body = cli.get(f"/api/usage?runtime={rt}").get_json() or {}
        # today = tokens from events in the last 24 h for this runtime only.
        actual = body.get("today") or 0
        assert actual == exp, (
            f"{rt}: expected {exp} tokens today, got {actual}. Body keys={list(body)}")

    # Unfiltered total must equal the sum of all seeded tokens.
    body_all = cli.get("/api/usage").get_json() or {}
    assert (body_all.get("today") or 0) == sum(t for _, t in seeds.values()), (
        f"unfiltered today mismatch: {body_all.get('today')}")


# ── 5. Foreign OTLP / OpenLLMetry apps: surfaced + no-leak (#2822/#2853) ─────
#
# A LangChain/CrewAI/OpenAI-Agents app sends OTLP traces; #2822 stamps
# ``agent_type`` from the resource ``service.name`` onto the spans. The app has
# NO session-id prefix, so it must be surfaced by agent_type (not prefix) and
# must obey the same no-leak contract: selecting it returns ONLY its data, and
# selecting a native runtime returns ZERO of its data (no leak either way).


def test_otlp_app_rollup_excludes_native_runtimes(app_and_store):
    """``query_otlp_app_rollup`` returns ONLY foreign apps, never a native
    session-prefix runtime (the pre-#2822 mis-bucket bug, inverted)."""
    import clawmetry.sync as sync
    a, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    # Native runtimes write spans too (agent_type = prefix); they must NOT
    # appear in the OTLP rollup.
    _seed_span(store, agent_type="claude_code", service_name="claude-code",
               span_id="native-cc", ts=now - 50, model="claude-opus-4-7")
    _seed_span(store, agent_type="openclaw", service_name="openclaw",
               span_id="native-oc", ts=now - 49, model="claude-opus-4-7")
    # Foreign OTLP apps.
    _seed_span(store, agent_type="my_app", service_name="my-app",
               span_id="otlp-m1", ts=now - 40, model="gpt-4o", cost=0.05,
               tokens=120, session_id="my_app-s1")
    _seed_span(store, agent_type="my_app", service_name="my-app",
               span_id="otlp-m2", ts=now - 39, model="gpt-4o", cost=0.02,
               tokens=80, session_id="my_app-s1")
    _seed_span(store, agent_type="crew", service_name="crew-bot",
               span_id="otlp-c1", ts=now - 30, model="gpt-4o-mini", cost=0.01,
               tokens=40)
    _wait_flush(store)

    exclude = set(sync._RUNTIME_PREFIXES) | {"openclaw", "nemoclaw"}
    rows = store.query_otlp_app_rollup(exclude_agent_types=exclude, limit=50)
    by_type = {r["agent_type"]: r for r in rows}
    # Only the two foreign apps; no native runtime.
    assert set(by_type) == {"my_app", "crew"}, f"unexpected rollup: {set(by_type)}"
    assert "claude_code" not in by_type and "openclaw" not in by_type
    # Aggregates are correct + scoped to the app.
    assert by_type["my_app"]["turns"] == 2
    assert by_type["my_app"]["tokens"] == 200
    assert round(by_type["my_app"]["cost_usd"], 4) == 0.07
    assert by_type["my_app"]["sessions"] == 1
    assert by_type["my_app"]["primary_model"] == "gpt-4o"
    assert by_type["crew"]["turns"] == 1


def test_runtime_summary_folds_otlp_app_without_leak(app_and_store):
    """``_build_runtime_summary`` surfaces a foreign OTLP app as its own entry
    (otlp=True + display_name) and its cost/tokens never bleed into openclaw."""
    import clawmetry.sync as sync
    a, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    # A real openclaw EVENT (session-prefix path) + a foreign OTLP app SPAN.
    _seed(store, "bareuuid-oc", "claude-opus-4-7", now - 60)   # → openclaw
    _seed_span(store, agent_type="my_app", service_name="my-app",
               span_id="otlp-a1", ts=now - 40, model="gpt-4o", cost=0.05,
               tokens=120, session_id="my_app-s1")
    _wait_flush(store)

    summary = sync._build_runtime_summary()
    assert "my_app" in summary, f"OTLP app missing from runtime_summary: {list(summary)}"
    assert "openclaw" in summary
    my = summary["my_app"]
    assert my.get("otlp") is True
    assert my.get("display_name") == "my-app (OTel)"
    assert my["tokens"] == 120
    assert round(my["cost_usd"], 4) == 0.05
    # No leak: the OTLP app's cost/tokens did NOT land in the openclaw bucket.
    oc = summary["openclaw"]
    assert oc.get("otlp") is not True
    assert oc["tokens"] == 100        # only the seeded openclaw event
    assert round(oc["cost_usd"], 4) == 0.01
    # And openclaw's tokens are not my_app's.
    assert oc["tokens"] != my["tokens"]


def test_agent_inventory_by_runtime_otlp_no_leak(app_and_store):
    """``agentInventoryByRuntime['my_app']`` contains ONLY the my_app row, and
    selecting 'openclaw' returns ZERO my_app rows (no leak either direction)."""
    import clawmetry.sync as sync
    a, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    _seed(store, "bareuuid-oc", "claude-opus-4-7", now - 60)   # → openclaw
    _seed_span(store, agent_type="my_app", service_name="my-app",
               span_id="otlp-i1", ts=now - 40, model="gpt-4o", cost=0.05,
               tokens=120, session_id="my_app-s1")
    _wait_flush(store)

    summary = sync._build_runtime_summary()
    node_wide, by_rt = sync._build_agent_inventory(
        summary, {}, {}, {}, {}, [], {}, "node-test",
    )
    keys = {a["agentKey"] for a in node_wide["agents"]}
    assert "my_app" in keys and "openclaw" in keys

    # my_app slice: only the my_app row, tagged otlp, with its cost.
    assert "my_app" in by_rt
    my_slice = by_rt["my_app"]
    assert my_slice["total"] == 1
    assert len(my_slice["agents"]) == 1
    my_row = my_slice["agents"][0]
    assert my_row["agentKey"] == "my_app"
    assert my_row["otlp"] is True
    assert my_row["displayName"] == "my-app (OTel)"
    assert round(my_row["costUsd"], 4) == 0.05
    assert all(x["agentKey"] != "openclaw" for x in my_slice["agents"])

    # openclaw slice: only openclaw, ZERO my_app rows.
    assert "openclaw" in by_rt
    oc_slice = by_rt["openclaw"]
    assert all(x["agentKey"] != "my_app" for x in oc_slice["agents"])
    assert oc_slice["agents"][0]["agentKey"] == "openclaw"

    # An absent runtime is simply not a key (interceptor returns zero, not the
    # node total).
    assert "no_such_app" not in by_rt


def test_otlp_custom_fallback_is_honest_single_bucket(app_and_store):
    """#2822 sets agent_type='custom' when service.name was absent; those group
    under ONE 'custom' entry labeled 'Custom (OTel)', never the openclaw bucket."""
    import clawmetry.sync as sync
    a, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    _seed_span(store, agent_type="custom", service_name="",
               span_id="otlp-cu1", ts=now - 20, model="gpt-4o", cost=0.01,
               tokens=10)
    _seed_span(store, agent_type="custom", service_name="",
               span_id="otlp-cu2", ts=now - 19, model="gpt-4o", cost=0.01,
               tokens=10)
    _wait_flush(store)
    summary = sync._build_runtime_summary()
    assert "custom" in summary
    assert summary["custom"]["display_name"] == "Custom (OTel)"
    assert summary["custom"]["otlp"] is True
    # Two spans, one bucket (not two phantom runtimes, not openclaw).
    assert summary["custom"]["turns"] == 2
    assert "custom" != "openclaw"


def test_otlp_app_cap_is_logged_not_silent(app_and_store, caplog):
    """More OTLP apps than the cap truncates to top-N AND logs a warning (no
    silent cap — FLYWHEEL)."""
    import logging
    import clawmetry.sync as sync
    a, ls = app_and_store
    store = ls.get_store()
    now = time.time()
    # Seed cap+5 distinct apps.
    n = sync._OTLP_APP_CAP + 5
    for i in range(n):
        _seed_span(store, agent_type=f"app{i}", service_name=f"svc{i}",
                   span_id=f"otlp-cap-{i}", ts=now - (n - i), model="gpt-4o",
                   tokens=1)
    _wait_flush(store)
    # The "clawmetry-sync" logger may not propagate to caplog's root handler;
    # attach caplog's handler to it directly so the warning is captured.
    _slog = logging.getLogger("clawmetry-sync")
    _prev_prop = _slog.propagate
    _slog.propagate = True
    try:
        with caplog.at_level(logging.WARNING, logger="clawmetry-sync"):
            summary = sync._build_runtime_summary()
    finally:
        _slog.propagate = _prev_prop
    otlp_keys = [k for k, v in summary.items()
                 if isinstance(v, dict) and v.get("otlp")]
    assert len(otlp_keys) == sync._OTLP_APP_CAP, (
        f"expected exactly {sync._OTLP_APP_CAP} OTLP apps, got {len(otlp_keys)}")
    assert "otlp app rollup truncated" in caplog.text.lower(), (
        "cap truncation was not logged")
