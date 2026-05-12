"""Live cross-process E2E verification of epic vivekchand/clawmetry#1032
Phases 2-5 (heartbeat-piggyback relay v2).

Strategy
========
The 5 phases of #1032 form a round-trip between the OSS daemon (this repo)
and the cloud Flask app (sibling repo at ``../clawmetry-cloud``). This test
exercises BOTH halves in one Python process by:

1. Importing the cloud's ``cloud_cache`` + relay + dashboard modules with the
   InMemoryCache backend selected (no real Upstash needed).
2. Running the OSS daemon's heartbeat builders + dispatchers IN-PROCESS,
   pointing them at an isolated DuckDB under ``tmp_path``.
3. POSTing the daemon-built heartbeat payload directly to the cloud Flask
   blueprint via Flask's test client — the same wire shape a real daemon
   would send over HTTP, but without a real socket. The heartbeat handler's
   ``_accept_cache_pushes`` call writes to the cloud cache exactly as it
   would in production.
4. Reading the cloud's cache-first endpoints via Flask's test client and
   asserting ``_source: "cache"`` (hit) or ``_source: "fallback"`` (miss).

Each phase has its own test class with cache HIT + cache MISS + invariant
assertions:

* Cloud NEVER decrypts the blob (verified by pushing random bytes that
  cannot decrypt and asserting the read path returns them unchanged).
* Cloud NEVER writes Cloud SQL on the cache-first relay path (``db_write``
  and ``db_query`` are monkey-patched to a counter that must stay at 0).

Phases 3 + 4 are MARKED ``xfail`` (expected to fail) because the cache-first
read paths and the action-queue contract for these phases haven't shipped
to ``clawmetry-cloud`` yet — see the punch list in the PR body for the
filed bugs.

Auth model
==========
The cloud's ``routes.auth._validate_cm_token`` is monkey-patched to accept
a single test token; ``_get_node_ids_for_token`` returns a single test node.
The OSS daemon's heartbeat builders only need an api_key + encryption key
in their config dict — they don't touch a real OpenClaw workspace.

Run
===
    python3 -m pytest tests/test_phase_2_to_5_live_e2e.py -v

Requires `clawmetry-cloud` repo at `../clawmetry-cloud` relative to this
repo's root.
"""
from __future__ import annotations

import base64
import hashlib
import importlib
import json
import os
import sys
import time
from pathlib import Path

import pytest


# ── Locate sibling cloud repo ───────────────────────────────────────────────

_OSS_ROOT = Path(__file__).resolve().parent.parent
_CLOUD_ROOT = _OSS_ROOT.parent.parent.parent.parent / "clawmetry-cloud"
if not _CLOUD_ROOT.exists():
    # Worktree layout: this file lives at
    #   /Users/vivek/projects/clawmetry/.claude/worktrees/agent-ad63e5aa/tests/...
    # The sibling cloud repo is at /Users/vivek/projects/clawmetry-cloud .
    # Walk parents until we find one called 'projects', then look for cloud.
    for p in Path(__file__).resolve().parents:
        candidate = p.parent / "clawmetry-cloud"
        if candidate.exists() and (candidate / "cloud_cache.py").exists():
            _CLOUD_ROOT = candidate
            break

pytestmark = pytest.mark.skipif(
    not (_CLOUD_ROOT.exists() and (_CLOUD_ROOT / "cloud_cache.py").exists()),
    reason=(
        "clawmetry-cloud sibling repo not found; this test requires both "
        "repos checked out side-by-side."
    ),
)


# Cloud repo on sys.path so its modules import. We also force OSS root to
# come FIRST so that any name collision (`routes/`) resolves to the OSS
# version in the daemon helpers, and the cloud's own `routes/` only resolves
# from inside cloud code that imports its own modules.
if str(_OSS_ROOT) not in sys.path:
    sys.path.insert(0, str(_OSS_ROOT))


# ── Constants ───────────────────────────────────────────────────────────────

API_KEY = "cm_phase2_5_e2e_token"
NODE_ID = "node-e2e-test"
OWNER_HASH = hashlib.sha256(API_KEY.encode("utf-8")).hexdigest()

# 32 random bytes, base64url-encoded — fixed so tests are deterministic.
ENCRYPTION_KEY = base64.urlsafe_b64encode(b"e2e-test-key-32-bytes-padding!!!").decode().rstrip("=")


# ── Cloud-side imports (lazy, inside fixtures) ──────────────────────────────


def _import_cloud():
    """Add the cloud repo to sys.path and import its core modules.

    Done inside a fixture (not at module load) so the OSS-only smoke tests
    that don't need the cloud (none here, but it's a good habit) don't drag
    in cloud-only deps."""
    cloud_root = str(_CLOUD_ROOT)
    if cloud_root not in sys.path:
        # Append (don't prepend) so OSS `routes/*` keeps priority for the
        # daemon-side calls; the cloud's own intra-package imports use
        # absolute paths anyway.
        sys.path.append(cloud_root)

    # Reset state ON EVERY CALL so tests get fresh in-memory cache + relay.
    import cloud_cache
    cloud_cache._reset_singleton_for_tests()

    # We need to nudge the cloud's `routes` package to be findable when
    # we're already on the OSS `routes` path. Python's import system caches
    # modules by name, so the FIRST `import routes` wins. We use absolute
    # path manipulation: temporarily clear cached routes modules tied to
    # the OSS root, then import the cloud ones, then restore.
    return cloud_cache


@pytest.fixture
def cloud_modules(monkeypatch, tmp_path):
    """Boot the cloud Flask app with InMemoryCache + auth/DB stubs.

    Returns a dict:
        {
            "app":          Flask app (with cloud blueprints registered),
            "client":       Flask test client,
            "cache":        the cloud_cache singleton (InMemoryCache),
            "relay":        the heartbeat_relay module,
            "api":          the cloud routes/api module (for _accept_cache_pushes),
            "channels_adapter": cloud routes/channels_adapter module,
            "db_calls":     {"write": int, "query": int} tracking
        }
    """
    # Make sure cloud is on sys.path BEFORE OSS so that `import routes` in
    # cloud-side code resolves to clawmetry-cloud/routes/, not OSS routes/.
    cloud_root = str(_CLOUD_ROOT)
    if cloud_root in sys.path:
        sys.path.remove(cloud_root)
    sys.path.insert(0, cloud_root)

    # The cloud's `routes` package may already be cached from a previous
    # test that imported the OSS one. Purge so we get the cloud version.
    for mod_name in list(sys.modules.keys()):
        if mod_name == "routes" or mod_name.startswith("routes."):
            del sys.modules[mod_name]
        if mod_name in (
            "cloud_cache", "dashboard", "config", "db", "bridge.script", "bridge"
        ):
            del sys.modules[mod_name]

    # Don't talk to a real DB. db._get_pool returns None when DATABASE_URL +
    # DB_HOST are both unset, and db_query/db_write degrade to no-op.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.setenv("CLOUD_MODE", "1")
    monkeypatch.setenv("TESTING", "1")
    # Disable cloud_route_policy enforcement: this test pulls in the OSS
    # blueprints via the policy loader for parity with production, but the
    # OSS-only routes (update-check, skills/fidelity, token-attribution, …)
    # aren't classified in cloud_route_policy/policy.py — strict mode would
    # sys.exit(1) the test process.
    monkeypatch.setenv("POLICY_MODE", "off")
    # No Upstash creds → falls back to InMemoryCache.
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)

    import cloud_cache
    cloud_cache._reset_singleton_for_tests()
    cache = cloud_cache.get_cache()
    assert isinstance(cache, cloud_cache.InMemoryCache), (
        "test must run with InMemoryCache; check no UPSTASH_* env vars"
    )

    # Now import cloud's routes + dashboard.
    import routes.heartbeat_relay as relay
    importlib.reload(relay)
    relay._reset_state_for_tests()

    import routes.api as cloud_api
    importlib.reload(cloud_api)
    import routes.channels_adapter as channels_adapter
    importlib.reload(channels_adapter)

    # Stub the cloud's auth helpers so our single test token is accepted.
    import routes.auth as auth_mod

    def _validate(token):
        if token == API_KEY:
            return {"email": "e2e@test", "plan": "trial"}
        return None

    def _nodes(token):
        return [NODE_ID] if token == API_KEY else []

    monkeypatch.setattr(auth_mod, "_validate_cm_token", _validate, raising=False)
    monkeypatch.setattr(auth_mod, "_get_node_ids_for_token", _nodes, raising=False)

    # Stub the cloud dashboard's copies too (dashboard.py defines its own at
    # module level; some routes reference those directly).
    import dashboard as cloud_d
    monkeypatch.setattr(cloud_d, "_validate_cm_token", _validate, raising=False)
    monkeypatch.setattr(cloud_d, "_get_node_ids_for_token", _nodes, raising=False)
    monkeypatch.setattr(cloud_d, "CLOUD_MODE", True, raising=False)

    # db_query/db_write counters — assert NO Cloud SQL traffic on cache-hit
    # paths.
    db_calls = {"write": 0, "query": 0}
    import db as cloud_db

    def _counting_query(*args, **kw):
        db_calls["query"] += 1
        return []

    def _counting_write(*args, **kw):
        db_calls["write"] += 1
        return {"affected_rows": 0}

    monkeypatch.setattr(cloud_db, "db_query", _counting_query, raising=False)
    monkeypatch.setattr(cloud_db, "db_write", _counting_write, raising=False)
    monkeypatch.setattr(cloud_d, "db_query", _counting_query, raising=False)
    monkeypatch.setattr(cloud_d, "db_write", _counting_write, raising=False)

    # Build a Flask app with the relay + adapter blueprints; the dashboard's
    # full app also has them, but the dashboard's import side-effects (auto-
    # starting threads, opening files) are heavy. We mount only what we need.
    # For brain-history we need the dashboard.app since it owns that route.
    yield {
        "app":              cloud_d.app,
        "client":           cloud_d.app.test_client(),
        "cache":            cache,
        "relay":            relay,
        "api":              cloud_api,
        "channels_adapter": channels_adapter,
        "dashboard":        cloud_d,
        "auth":             auth_mod,
        "db_calls":         db_calls,
    }


@pytest.fixture
def oss_modules(monkeypatch, tmp_path):
    """Boot the OSS daemon helpers + an isolated local DuckDB.

    Returns a dict:
        {
            "sync":   the clawmetry.sync module,
            "store":  the LocalStore instance backing tmp_path,
            "config": the daemon config dict we'll pass to builders,
        }
    """
    # Force a fresh DuckDB file per test.
    db_path = tmp_path / "clawmetry.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.delenv("CLAWMETRY_LOCAL_DISABLE", raising=False)

    # Cloud must not be on sys.path during OSS-side calls (OSS has its own
    # routes/ package — collisions break local_query.relay_dispatch import).
    # We remove cloud_root from sys.path, purge cached cloud modules, then
    # re-import OSS.
    cloud_root = str(_CLOUD_ROOT)
    if cloud_root in sys.path:
        sys.path.remove(cloud_root)

    # IMPORTANT: don't delete `cloud_cache` etc. — the cloud test client
    # we built in `cloud_modules` still needs them. We only purge OSS
    # routes if they got shadowed by cloud's `routes` in a prior test.
    for mod_name in list(sys.modules.keys()):
        if mod_name == "routes" or mod_name.startswith("routes."):
            # Decide whether the cached module is from cloud or OSS via
            # its __file__.
            mod = sys.modules.get(mod_name)
            mfile = getattr(mod, "__file__", "") or ""
            if str(_CLOUD_ROOT) in mfile:
                del sys.modules[mod_name]

    # Ensure OSS root takes priority again.
    if str(_OSS_ROOT) in sys.path:
        sys.path.remove(str(_OSS_ROOT))
    sys.path.insert(0, str(_OSS_ROOT))

    # Now import OSS local_store + sync.
    # Reset local_store singletons so each test gets a fresh DB.
    import clawmetry.local_store as ls
    ls._store_rw = None
    ls._store_ro = None
    # Re-evaluate DB_PATH after env change.
    importlib.reload(ls)

    import clawmetry.sync as sync_mod
    # We don't reload sync (it has side effects); we just call its
    # builder functions directly.

    store = ls.get_store()  # read-write

    config = {
        "api_key":        API_KEY,
        "node_id":        NODE_ID,
        "encryption_key": ENCRYPTION_KEY,
    }

    yield {"sync": sync_mod, "store": store, "config": config, "local_store": ls}

    # Cleanup: close the store so the next test gets a fresh DuckDB.
    try:
        store.stop()
    except Exception:
        pass
    ls._store_rw = None
    ls._store_ro = None


def _push_to_cloud(cloud, payload_pushes):
    """Drive `_accept_cache_pushes` like the heartbeat handler would.

    Returns the count of pushes successfully written. This is the same
    function the cloud's `ingest_heartbeat` calls when it sees a
    `cache_pushes` array on the body.
    """
    return cloud["api"]._accept_cache_pushes(API_KEY, NODE_ID, payload_pushes)


# ════════════════════════════════════════════════════════════════════════════
# Phase 2 — Brain cache-first read path
# ════════════════════════════════════════════════════════════════════════════


class TestPhase2Brain:
    """OSS daemon seeds events → builds brain cache_push → cloud caches →
    /api/brain-history serves from cache with _source: 'cache'."""

    def _seed_events(self, store):
        """Insert 5 tool_call events so the brain cache_push has something
        to encrypt. The local-store ring is flushed synchronously at the
        end so the next query_events read sees them all."""
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for i in range(5):
            store.ingest({
                "id":         f"evt-{i}",
                "node_id":    NODE_ID,
                "event_type": "tool_call",
                "ts":         now_iso,
                "data":       {"tool": "Bash", "input": f"echo {i}"},
                "cost_usd":   0.001,
                "token_count": 25,
                "model":      "claude-opus-4-7",
                "session_id": "sess-1",
                "agent_id":   "main",
            })
        store._flush_now()

    def test_round_trip_cache_hit(self, oss_modules, cloud_modules):
        """Daemon-builds → cloud-caches → cloud-reads with _source: cache."""
        self._seed_events(oss_modules["store"])

        # 1. OSS daemon builds the cache_push (in-process).
        pushes = oss_modules["sync"]._build_brain_cache_pushes(oss_modules["config"])
        assert len(pushes) == 1, "expected exactly one brain cache_push entry"
        push = pushes[0]
        assert push["key"] == f"brain:{OWNER_HASH}:{NODE_ID}:recent"
        assert push["ttl_s"] == oss_modules["sync"].BRAIN_CACHE_TTL_SEC
        assert isinstance(push["blob"], str), "blob must be base64url string"

        # 2. Cloud accepts the push (same call the heartbeat handler makes).
        written = _push_to_cloud(cloud_modules, pushes)
        assert written == 1

        # 3. Cloud /api/brain-history serves from cache.
        # Reset db_calls counter — we only care about calls AFTER cache push.
        cloud_modules["db_calls"]["query"] = 0
        cloud_modules["db_calls"]["write"] = 0

        r = cloud_modules["client"].get(
            f"/api/brain-history?token={API_KEY}&node_id={NODE_ID}&limit=50"
        )
        assert r.status_code == 200, r.data
        body = r.get_json()
        assert body["_source"] == "cache", body
        assert body["node_id"] == NODE_ID
        assert body["shape"] == "brain_history"
        assert r.headers.get("X-Cache") == "hit"

        # Cache-hit path must NOT touch Cloud SQL.
        assert cloud_modules["db_calls"]["query"] == 0, (
            "brain cache-hit must not query Cloud SQL"
        )
        assert cloud_modules["db_calls"]["write"] == 0, (
            "brain cache-hit must not write Cloud SQL"
        )

        # 4. Cloud invariant: blob is unchanged ciphertext. Decryption
        # happens client-side (browser holds the key).
        ciphertext_b64 = body["events_blob"]
        # The OSS daemon used the same encryption_key, so we (acting as the
        # browser) can decrypt to verify the round-trip.
        plaintext = oss_modules["sync"].decrypt_payload(ciphertext_b64, ENCRYPTION_KEY)
        assert plaintext["_shape"] == "brain_history"
        assert len(plaintext["events"]) == 5

    def test_cache_miss_falls_through_to_db(self, oss_modules, cloud_modules):
        """No cache_push → /api/brain-history serves from Cloud SQL path
        with _source: 'fallback'."""
        # Don't seed; don't push. Cache is empty.
        r = cloud_modules["client"].get(
            f"/api/brain-history?token={API_KEY}&node_id={NODE_ID}&limit=50"
        )
        assert r.status_code == 200, r.data
        body = r.get_json()
        assert body.get("_source") != "cache", body
        assert body["_source"] == "fallback", body
        assert body["node_id"] == NODE_ID

    def test_cloud_never_decrypts(self, oss_modules, cloud_modules):
        """Push garbage bytes; cloud serves them back as-is."""
        garbage = b"\x99\x88\x77NotARealCiphertext"
        cloud_modules["api"]._accept_cache_pushes(API_KEY, NODE_ID, [{
            "key":   f"brain:{OWNER_HASH}:{NODE_ID}:recent",
            "ttl_s": 3600,
            "blob":  base64.urlsafe_b64encode(garbage).decode().rstrip("="),
        }])
        r = cloud_modules["client"].get(
            f"/api/brain-history?token={API_KEY}&node_id={NODE_ID}&limit=50"
        )
        body = r.get_json()
        assert body["_source"] == "cache"
        assert base64.urlsafe_b64decode(body["events_blob"] + "==") == garbage


# ════════════════════════════════════════════════════════════════════════════
# Phase 3 — Alert rules cache-first read + relay-queued writes
# ════════════════════════════════════════════════════════════════════════════


class TestPhase3Alerts:
    """Daemon seeds alert rules in local DuckDB → builds alerts cache_push →
    cloud caches → /api/alerts/rules or /api/alerts serves from cache.

    EXPECTED FAILURE: as of 2026-05-12, cloud-side `/api/alerts` reads from
    Postgres directly with NO cache-first short-circuit. The cache_push is
    accepted (Phase 2's _accept_cache_pushes handler is generic enough to
    catch ANY {owner_hash} key), but no cloud read endpoint serves it back.
    See bug filed in PR body.
    """

    def _seed_rule(self, store):
        store.ingest_alert_rule({
            "id":              "rule-1",
            "owner_hash":      OWNER_HASH,
            "name":            "Daily spend > $5",
            "condition_json":  {"alert_type": "daily_spend", "threshold": 5.0},
            "enabled":         True,
            "created_at":      "2026-05-12T00:00:00Z",
            "updated_at":      "2026-05-12T00:00:00Z",
        })

    def test_oss_daemon_builds_cache_push(self, oss_modules):
        """OSS-side smoke: the daemon's `_build_alert_rules_cache_pushes`
        produces a well-formed entry from local DuckDB rows."""
        self._seed_rule(oss_modules["store"])
        pushes = oss_modules["sync"]._build_alert_rules_cache_pushes(oss_modules["config"])
        assert len(pushes) == 1
        push = pushes[0]
        assert push["key"] == f"alerts:{OWNER_HASH}:rules"
        assert push["ttl_s"] == oss_modules["sync"].ALERT_RULES_CACHE_TTL_SEC
        assert isinstance(push["blob"], str)

        # Decrypt to verify shape — we have the key (browser-side role).
        decrypted = oss_modules["sync"].decrypt_payload(push["blob"], ENCRYPTION_KEY)
        assert decrypted["_shape"] == "alert_rules"
        assert decrypted["count"] == 1
        assert decrypted["rules"][0]["id"] == "rule-1"

    def test_cloud_accepts_cache_push(self, oss_modules, cloud_modules):
        """Cloud's `_accept_cache_pushes` writes the alerts key under the
        same owner_hash binding it uses for brain."""
        self._seed_rule(oss_modules["store"])
        pushes = oss_modules["sync"]._build_alert_rules_cache_pushes(oss_modules["config"])
        written = _push_to_cloud(cloud_modules, pushes)
        assert written == 1
        entry = cloud_modules["relay"]._read_entry(f"alerts:{OWNER_HASH}:rules")
        assert entry is not None
        assert entry["owner_hash"] == OWNER_HASH

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Phase 3 cloud-side cache-first read NOT IMPLEMENTED. "
            "clawmetry-cloud/routes/alerts.py:list_alerts reads Postgres "
            "directly with no `alerts:{owner_hash}:rules` cache lookup. "
            "Bug filed: see PR body."
        ),
    )
    def test_cloud_alerts_endpoint_serves_from_cache(self, oss_modules, cloud_modules):
        """Per epic #1032 Phase 3, GET /api/alerts should short-circuit on
        cache before hitting Postgres. Today it does not."""
        self._seed_rule(oss_modules["store"])
        pushes = oss_modules["sync"]._build_alert_rules_cache_pushes(oss_modules["config"])
        _push_to_cloud(cloud_modules, pushes)

        cloud_modules["db_calls"]["query"] = 0
        r = cloud_modules["client"].get(
            f"/api/alerts?token={API_KEY}",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        assert r.status_code == 200, r.data
        body = r.get_json()
        # MISSING IMPLEMENTATION: this assertion is the contract we want.
        assert body.get("_source") == "cache", (
            "GET /api/alerts must serve from cache when "
            "alerts:{owner_hash}:rules is hot"
        )
        assert cloud_modules["db_calls"]["query"] == 0, (
            "cache hit must not query Postgres"
        )

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Phase 3 write-through relay-queue contract NOT IMPLEMENTED. "
            "Cloud-side `routes/alerts.py:create_alert` writes Postgres "
            "directly; there is no `alert_rule_upsert` enqueue back to the "
            "daemon's pending_queries channel. Bug filed: see PR body."
        ),
    )
    def test_cloud_alert_create_enqueues_relay_action(self, oss_modules, cloud_modules):
        """POST /api/alerts should enqueue an `alert_rule_upsert` action so
        the daemon's local DuckDB stays in sync. Today it does not."""
        r = cloud_modules["client"].post(
            "/api/alerts",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "alert_type":      "daily_spend",
                "name":            "Spend cap",
                "threshold_value": 5.0,
            },
        )
        # We don't even get a chance to check the queue — assertions about
        # the contract below WILL fail because the endpoint writes to
        # Postgres (which is stubbed to no-op) and never queues the action.
        drained = cloud_modules["relay"].drain_queue(OWNER_HASH, NODE_ID, max_items=10)
        actions = [d for d in drained if d.get("type") == "alert_rule_upsert"]
        assert len(actions) == 1, (
            f"expected one alert_rule_upsert in relay queue; got {drained}"
        )


# ════════════════════════════════════════════════════════════════════════════
# Phase 4 — Approvals queue cache-first + decision relay
# ════════════════════════════════════════════════════════════════════════════


class TestPhase4Approvals:
    """Daemon seeds approvals → builds approvals cache_push → cloud caches
    → /api/cloud/approvals serves from cache. Cloud POST .../decide should
    enqueue a relay action so the daemon updates its DuckDB.

    EXPECTED FAILURE: Phase 4 is NOT IMPLEMENTED. Neither side has the
    approvals cache_push builder, the cache-first read, nor the relay
    write-through. See bug filed in PR body.
    """

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Phase 4 NOT IMPLEMENTED in OSS daemon. There is no "
            "`_build_approvals_cache_pushes` in clawmetry/sync.py and "
            "no `approvals:{owner_hash}:queue` key in send_heartbeat. "
            "Bug filed: see PR body."
        ),
    )
    def test_oss_daemon_builds_approvals_cache_push(self, oss_modules):
        """Daemon should expose `_build_approvals_cache_pushes(config)`."""
        builder = getattr(
            oss_modules["sync"], "_build_approvals_cache_pushes", None
        )
        assert builder is not None, "OSS sync.py missing _build_approvals_cache_pushes"

    @pytest.mark.xfail(
        strict=False,  # not strict — suite-context vs isolated yields different fails
        reason=(
            "Phase 4 cloud-side cache-first NOT IMPLEMENTED. "
            "clawmetry-cloud/routes/cloud.py:cloud_approvals_list queries "
            "Postgres `approvals` table; no `approvals:{owner_hash}:queue` "
            "cache lookup exists. Bug filed: see PR body."
        ),
    )
    def test_cloud_approvals_endpoint_serves_from_cache(self, oss_modules, cloud_modules):
        """GET /api/cloud/approvals should short-circuit on cache."""
        # Direct cache seed (since OSS builder doesn't exist yet, we manually
        # place an entry matching what Phase 4's contract would produce).
        from clawmetry.sync import encrypt_payload
        blob = encrypt_payload({
            "approvals": [{"id": "ap-1", "status": "pending", "tool_name": "Bash"}],
            "_shape":    "approvals_queue",
        }, ENCRYPTION_KEY)
        cloud_modules["api"]._accept_cache_pushes(API_KEY, NODE_ID, [{
            "key":   f"approvals:{OWNER_HASH}:queue",
            "ttl_s": 3600,
            "blob":  blob,
        }])

        cloud_modules["db_calls"]["query"] = 0
        r = cloud_modules["client"].get(
            f"/api/cloud/approvals?token={API_KEY}",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        body = r.get_json() or {}
        # Contract: cache hit must surface as _source: "cache".
        assert body.get("_source") == "cache", (
            f"GET /api/cloud/approvals must serve from cache when "
            f"approvals:{OWNER_HASH}:queue is hot; got body={body!r}"
        )
        assert cloud_modules["db_calls"]["query"] == 0, (
            "cache hit must not query Postgres"
        )

    @pytest.mark.xfail(
        strict=False,
        reason=(
            "Phase 4 decide-via-relay NOT IMPLEMENTED. "
            "POST /api/cloud/approvals/<id>/decide writes Postgres directly "
            "via `db_write`, no `approval_decide` relay action enqueued. "
            "Bug filed: see PR body."
        ),
    )
    def test_cloud_decide_enqueues_relay_action(self, oss_modules, cloud_modules):
        """POST .../decide should enqueue an `approval_decide` action."""
        cloud_modules["client"].post(
            "/api/cloud/approvals/ap-1/decide",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"action": "approve"},
        )
        drained = cloud_modules["relay"].drain_queue(OWNER_HASH, NODE_ID, max_items=10)
        actions = [d for d in drained if d.get("type") in ("approval_decide", "approval_decision")]
        assert len(actions) == 1, (
            f"expected one approval_decide in relay queue; got {drained}"
        )


# ════════════════════════════════════════════════════════════════════════════
# Phase 5 — Channel adapters cache-first + configure via relay
# ════════════════════════════════════════════════════════════════════════════


class TestPhase5Channels:
    """Daemon seeds channel_config rows → builds status cache_push → cloud
    caches → /api/channel-adapters/<provider>/status serves from cache.
    Cloud POST .../configure enqueues a relay action; daemon picks it up."""

    def _seed_channel_config(self, store):
        store.ingest_channel_config(
            provider="telegram",
            encrypted_blob=b"OPAQUE-CIPHER-CONFIG",
            enabled=True,
            status_meta={
                "last_test_at":    "2026-05-12T00:00:00Z",
                "last_test_ok":    True,
                "last_test_error": "",
            },
        )

    def test_round_trip_cache_hit(self, oss_modules, cloud_modules):
        """Daemon-builds channels status push → cloud-caches → cloud-reads
        cache hit on /api/channel-adapters/telegram/status."""
        self._seed_channel_config(oss_modules["store"])
        pushes = oss_modules["sync"]._build_channel_config_status_cache_pushes(
            oss_modules["config"]
        )
        assert len(pushes) == 1, f"expected 1 channel push, got {pushes}"
        push = pushes[0]
        assert push["key"] == f"channels:{OWNER_HASH}:status"
        assert push["ttl_s"] == oss_modules["sync"].CHANNEL_STATUS_CACHE_TTL_SEC

        written = _push_to_cloud(cloud_modules, pushes)
        assert written == 1

        # Cloud reads cache-first.
        cloud_modules["db_calls"]["query"] = 0
        cloud_modules["db_calls"]["write"] = 0

        r = cloud_modules["client"].get(
            "/api/channel-adapters/telegram/status",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        assert r.status_code == 200, r.data
        body = r.get_json()
        assert body["_source"] == "cache", body
        assert body["provider"] == "telegram"
        assert "status_blob" in body
        assert r.headers.get("X-Cache") == "hit"

        # Phase 5 invariant: NO Cloud SQL for adapter status.
        assert cloud_modules["db_calls"]["write"] == 0, (
            "channel status cache-hit must not write Cloud SQL"
        )

        # Decrypt to verify status round-trips (we hold the key as browser).
        plaintext = oss_modules["sync"].decrypt_payload(
            body["status_blob"], ENCRYPTION_KEY
        )
        assert plaintext["_shape"] == "channel_config_status"
        ch = plaintext["channels"]
        assert any(c["provider"] == "telegram" and c["enabled"] for c in ch)

    def test_cache_miss_returns_configured_false(self, oss_modules, cloud_modules):
        """No daemon push → cache miss → cloud returns _source: 'miss'."""
        r = cloud_modules["client"].get(
            "/api/channel-adapters/telegram/status",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        assert r.status_code == 200, r.data
        body = r.get_json()
        assert body["_source"] == "miss", body
        assert body["configured"] is False

    def test_configure_enqueues_relay_action(self, oss_modules, cloud_modules):
        """POST /configure should enqueue a channel_config_upsert action."""
        cipher_b64 = base64.urlsafe_b64encode(b"CIPHER-FOR-DAEMON").decode().rstrip("=")
        r = cloud_modules["client"].post(
            "/api/channel-adapters/telegram/configure",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"encrypted_blob": cipher_b64, "enabled": True},
        )
        assert r.status_code == 202, r.data

        drained = cloud_modules["relay"].drain_queue(OWNER_HASH, NODE_ID, max_items=10)
        upserts = [d for d in drained if d.get("type") == "channel_config_upsert"]
        assert len(upserts) == 1
        action = upserts[0]
        assert action["provider"] == "telegram"
        assert action["encrypted_blob"] == cipher_b64

    def test_daemon_consumes_relay_action(self, oss_modules, cloud_modules):
        """Full round-trip: cloud queues a config_upsert, daemon dispatches
        it locally, the row lands in DuckDB."""
        cipher_b64 = base64.urlsafe_b64encode(b"CIPHER-FOR-DAEMON").decode().rstrip("=")
        cloud_modules["client"].post(
            "/api/channel-adapters/telegram/configure",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"encrypted_blob": cipher_b64, "enabled": True},
        )

        # Drain the way the heartbeat handler would.
        pending = cloud_modules["relay"].drain_queue(OWNER_HASH, NODE_ID, max_items=10)

        # Daemon dispatches each pending entry.
        for action in pending:
            oss_modules["sync"]._dispatch_pending_action(oss_modules["config"], action)

        # DuckDB now has the row.
        rows = oss_modules["store"].query_channel_configs(provider="telegram", limit=1)
        assert len(rows) == 1
        assert rows[0]["provider"] == "telegram"
        assert bool(rows[0]["enabled"]) is True
        assert rows[0]["config_json_encrypted"] is not None

    def test_cloud_never_decrypts_channel_status(self, oss_modules, cloud_modules):
        """Push garbage bytes; cloud serves them back as-is."""
        garbage = b"\x99\x88NOT-A-REAL-CIPHER"
        cloud_modules["api"]._accept_cache_pushes(API_KEY, NODE_ID, [{
            "key":   f"channels:{OWNER_HASH}:status",
            "ttl_s": 3600,
            "blob":  base64.urlsafe_b64encode(garbage).decode().rstrip("="),
        }])
        r = cloud_modules["client"].get(
            "/api/channel-adapters/telegram/status",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        body = r.get_json()
        assert body["_source"] == "cache"
        assert base64.urlsafe_b64decode(body["status_blob"] + "==") == garbage


# ════════════════════════════════════════════════════════════════════════════
# Cross-phase invariants
# ════════════════════════════════════════════════════════════════════════════


class TestInvariants:
    def test_owner_hash_binding_rejects_cross_tenant(self, cloud_modules):
        """A push under another owner's owner_hash is silently dropped by
        the cloud (defense against token-A poisoning user-B's cache)."""
        other_owner = hashlib.sha256(b"cm_someone_else").hexdigest()
        garbage = base64.urlsafe_b64encode(b"X").decode().rstrip("=")
        written = cloud_modules["api"]._accept_cache_pushes(API_KEY, NODE_ID, [{
            "key":   f"brain:{other_owner}:other-node:recent",
            "ttl_s": 3600,
            "blob":  garbage,
        }])
        assert written == 0, "cross-tenant push must be dropped"
        # And the entry truly doesn't exist.
        assert cloud_modules["relay"]._read_entry(
            f"brain:{other_owner}:other-node:recent"
        ) is None

    def test_inmemory_cache_selected_when_no_upstash_env(self, cloud_modules):
        """The whole point of the test: it runs without Upstash credentials.
        Verify the cache backend is InMemoryCache (not Upstash) so this
        suite stays self-contained."""
        import cloud_cache as cc
        assert isinstance(cloud_modules["cache"], cc.InMemoryCache)
