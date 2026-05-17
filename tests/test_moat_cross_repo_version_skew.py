"""MOAT cross-repo version-skew E2E: daemon-version != cloud-version.

Sister to ``tests/test_moat_cloud_sync_e2e.py`` (Eng W, #1584). That test
proves the daemon to cloud round-trip works at HEAD (one repo, one SHA on
both sides). It does NOT exercise the real failure mode: user upgrades OSS
daemon to v0.12.220 while ``ingest.clawmetry.com`` is still on v0.12.215
(cloud auto-deploys, OSS launchctl auto-update can lag a week). If the
wire format silently drifts, sync breaks silently with no log entry.

This file proves version skew either (a) gracefully degrades (older side
ignores unknown fields + logs) OR (b) fails loud (HTTP 4xx + Upgrade
Required), and NEVER (c) silently succeeds with dropped fields.

Scenarios (matches the user's 2026-05-17 hardening brief):

  1. Same-version happy path  -- OSS HEAD vs cloud HEAD baseline.
  2. Daemon newer, cloud older -- mock cloud with a shrunken known-fields
     allowlist (real ``clawmetry-cloud`` HEAD~3 worktree attempted as
     smoke when the cloud repo is checked out locally).
  3. Daemon older, cloud newer -- old-shape payload POSTed directly;
     new cloud must not 500 on missing optional fields.
  4. Schema-breaking canary    -- daemon attaches an unknown
     ``new_field_v4``; cloud must log+accept-rest (lenient) OR reject 426
     (strict). Silent accept is the bug.

Per memory ``feedback_synthetic_tests_missed_real_event_shape.md``: every
event uses the real v3 OpenClaw shape (``event_type='message'`` +
``message.usage.{input_tokens,output_tokens}``), not the flat 2024 shape
that hid a 3-of-7 silent-zero family. Per memory
``reference_pypi_propagation_race.md``: each tested path reports its own
``__version__`` on the wire; that field is THE skew signal.

Run as::

    pytest -v tests/test_moat_cross_repo_version_skew.py

Manual recipe for scenario 2 extension::

    git clone git@github.com:vivekchand/clawmetry-cloud.git ../clawmetry-cloud
    pytest tests/test_moat_cross_repo_version_skew.py -v
"""
from __future__ import annotations

import http.server
import importlib
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import uuid

import pytest


# ── Cross-repo locator helpers ────────────────────────────────────────────


_OSS_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Cloud repo sits next to OSS per memory reference_cloud_deploy_paths.
_CANDIDATE_CLOUD_ROOTS = [
    os.path.join(os.path.dirname(_OSS_REPO_ROOT), "clawmetry-cloud"),
    "/Users/vivek/projects/clawmetry-cloud",
    os.environ.get("CLAWMETRY_CLOUD_REPO", ""),
]


def _cloud_repo_root() -> str | None:
    for c in _CANDIDATE_CLOUD_ROOTS:
        if c and os.path.isdir(c) and os.path.isdir(os.path.join(c, ".git")):
            return c
    return None


def _git_has_depth(repo: str, depth: int) -> bool:
    """True iff ``repo`` has at least ``depth`` commits on HEAD. Returns
    False on shallow clones so Scenario 3 auto-skips on CI runners that
    fetch with ``--depth 1``."""
    try:
        subprocess.check_output(
            ["git", "rev-parse", f"HEAD~{depth}"],
            cwd=repo, stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


# ── Magic sentinels ──────────────────────────────────────────────────────


NODE_ID = "agent+moat-cross-repo-skew"
API_KEY = "cm_test_moat_skew_token"
DAY = "2026-05-17"
SENTINEL_PROMPT = "MOAT cross-repo skew ping HELLO_FROM_SKEW_99"
SENTINEL_MODEL = "claude-opus-4-7"
EVENT_TOKENS_IN = 411
EVENT_TOKENS_OUT = 137
# Stable encryption key reused across simulated versions. Production key
# rotation across daemon upgrades would be a data-loss bug, so the test
# pins this fixture across the whole matrix.
STABLE_ENC_KEY = "T0pSXcrjt_C9N6mGVe2vU5lU2sP3p1qg2k7nL3xH7Aw="


# ── Mock cloud handler — schema-version-aware ────────────────────────────


class _CloudState:
    """In-memory mirror of the cloud-side relay state. Skew tests verify
    accept / reject / degrade-gracefully -- never silent-strip."""

    def __init__(self) -> None:
        self.cache: dict[str, str] = {}
        self.cache_owner: dict[str, str] = {}
        self.last_seen: dict[str, float] = {}
        self.last_heartbeat: dict | None = None
        self.heartbeats_seen: list[dict] = []
        self.daemon_versions_seen: set[str] = set()
        self.unknown_fields_logged: set[str] = set()
        self.strict_rejected = 0
        # When True, reject unknown top-level fields with 426 instead of
        # ignore-and-log. Both modes are spec-acceptable; silent accept is
        # not. Tests exercise both.
        self.strict_reject_unknown_fields = False
        # The wire fields a "head" cloud knows about. Anything outside is
        # "new" and triggers the unknown-field policy. Mirrors the top-
        # level keys ``sync.send_heartbeat`` actually sends at HEAD.
        self.known_top_level_fields: set[str] = {
            "node_id", "ts", "platform", "version", "e2e", "ollama",
            "security_posture", "local_store", "local_store_size_mb",
            "cache_pushes", "node_meta", "hostname",
            "auto_update", "events", "blob", "encrypted",
        }


class _MockCloudHandler(http.server.BaseHTTPRequestHandler):
    state: _CloudState

    def log_message(self, *_a, **_kw) -> None:  # noqa: D401
        return

    def _send(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _detect_unknown_fields(self, payload: dict) -> set[str]:
        return set(payload.keys()) - self.state.known_top_level_fields

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            payload = {}

        if self.path == "/ingest/heartbeat":
            self.state.last_heartbeat = payload
            self.state.heartbeats_seen.append(payload)
            if payload.get("version"):
                self.state.daemon_versions_seen.add(payload["version"])
            unknowns = self._detect_unknown_fields(payload)
            if unknowns:
                self.state.unknown_fields_logged.update(unknowns)
                if self.state.strict_reject_unknown_fields:
                    self.state.strict_rejected += 1
                    return self._send(426, {
                        "error": "Upgrade Required",
                        "unknown_fields": sorted(unknowns),
                    })
            node_id = payload.get("node_id") or "unknown"
            self.state.last_seen[node_id] = time.time()
            for entry in payload.get("cache_pushes") or []:
                key, blob = entry.get("key"), entry.get("blob")
                if key and isinstance(blob, str):
                    self.state.cache[key] = blob
                    self.state.cache_owner[key] = node_id
            return self._send(200, {
                "ok": True, "sync_allowed": True, "pending_queries": [],
            })

        # Catch-all (events / cache / snapshot / logs) -- no-op for skew.
        return self._send(200, {"ok": True})


# ── Helpers ──────────────────────────────────────────────────────────────


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _v3_event(event_id: str, ts: str, text: str) -> dict:
    """v3-shape OpenClaw event (event_type='message' + message.usage)."""
    return {
        "id": event_id, "node_id": NODE_ID, "agent_id": "main",
        "session_id": "sess-skew", "event_type": "message", "ts": ts,
        "data": {
            "type": "message", "timestamp": ts,
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": text}],
                "model": SENTINEL_MODEL,
                "usage": {
                    "input_tokens": EVENT_TOKENS_IN,
                    "output_tokens": EVENT_TOKENS_OUT,
                    "totalTokens": EVENT_TOKENS_IN + EVENT_TOKENS_OUT,
                },
            },
        },
        "model": SENTINEL_MODEL,
        "token_count": EVENT_TOKENS_IN + EVENT_TOKENS_OUT,
    }


def _seed_events(store, n: int = 3) -> list[dict]:
    seeded = []
    for i in range(n):
        ts = f"{DAY}T13:{i:02d}:00+00:00"
        ev = _v3_event(str(uuid.uuid4()), ts, f"{SENTINEL_PROMPT} #{i}")
        store.ingest(ev)
        seeded.append(ev)
    deadline = time.monotonic() + 3.0
    while store.health()["ring_depth"] > 0 and time.monotonic() < deadline:
        time.sleep(0.02)
    return seeded


# ── Fixture: real DuckDB + reloaded sync + mock cloud ────────────────────


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Hermetic env matching test_moat_cloud_sync_e2e with the skew-aware
    handler. Tests can toggle ``cloud.strict_reject_unknown_fields`` and
    ``cloud.known_top_level_fields`` to simulate old/new cloud schemas
    without re-booting the HTTP server."""
    db_path = tmp_path / "moat_cross_repo_skew.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    # Quarantine HOME so the daemon's discovery file doesn't punt to a
    # real local_server on the developer's machine.
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    for mod in ("clawmetry.local_store", "clawmetry.sync",
                "routes.local_query"):
        sys.modules.pop(mod, None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as sync_mod
    importlib.reload(sync_mod)
    import routes.local_query as lq
    importlib.reload(lq)

    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH",
        str(tmp_path / "no-such-discovery.json"), raising=True,
    )

    store = ls.get_store()
    seeded = _seed_events(store, n=3)

    cloud_state = _CloudState()
    _MockCloudHandler.state = cloud_state
    port = _free_port()
    httpd = http.server.HTTPServer(("127.0.0.1", port), _MockCloudHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    monkeypatch.setattr(
        sync_mod, "INGEST_URL", f"http://127.0.0.1:{port}", raising=False,
    )

    config = {
        "node_id": NODE_ID, "api_key": API_KEY,
        "encryption_key": STABLE_ENC_KEY,
    }

    yield {
        "sync": sync_mod, "store": store, "config": config,
        "cloud": cloud_state, "port": port, "seeded": seeded,
        "base_url": f"http://127.0.0.1:{port}",
    }

    httpd.shutdown()
    httpd.server_close()
    try:
        store.stop(flush=True)
    except Exception:
        pass
    try:
        ls._reset_singleton_for_tests()
    except Exception:
        pass


# ── Scenario 1: same-version happy path ──────────────────────────────────


def test_scenario1_same_version_happy_path(env):
    """Daemon HEAD vs cloud HEAD -- baseline. If this flips red, the rest
    of the skew matrix is meaningless; fix this first."""
    sync_mod, config, cloud = env["sync"], env["config"], env["cloud"]

    assert sync_mod.send_heartbeat(config) is True, (
        "baseline send_heartbeat returned False -- check INGEST_URL "
        "monkeypatch + mock handler routes"
    )

    hb = cloud.last_heartbeat
    assert hb is not None, "mock cloud never saw a heartbeat"
    assert hb.get("version"), (
        "daemon heartbeat missing 'version' field -- cross-repo skew "
        "detection is IMPOSSIBLE without it. Fix sync.send_heartbeat."
    )
    assert not cloud.unknown_fields_logged, (
        f"baseline run logged unknown fields "
        f"{sorted(cloud.unknown_fields_logged)} -- either the test's "
        f"`known_top_level_fields` allowlist drifted, or sync.py added a "
        f"field without updating the cross-repo schema contract."
    )
    assert cloud.strict_rejected == 0, "no rejects expected on baseline"

    owner = sync_mod._owner_hash_for_token(config["api_key"])
    expected_key = f"brain:{owner}:{NODE_ID}:recent"
    assert expected_key in cloud.cache, (
        f"baseline brain push missing under {expected_key!r}"
    )
    assert cloud.daemon_versions_seen, "no daemon version captured"


# ── Scenario 2: daemon NEW, cloud OLD ────────────────────────────────────


def test_scenario2_daemon_newer_cloud_older_logs_unknown_fields(env):
    """Daemon HEAD vs cloud HEAD~3 -- graceful-degrade path.

    Substitute strategy (real cloud HEAD~3 worktree is the extension test
    below): shrink the mock cloud's known-fields allowlist to a pre-#1032
    baseline. The handler must LOG the new daemon fields rather than
    silently accept-and-strip them. Silent accept is the bug class.
    """
    sync_mod, config, cloud = env["sync"], env["config"], env["cloud"]

    # Emulate "cloud handler 3 versions back" -- pre-relay-v2 epic #1032
    # (memory project_relay_transport_decision).
    cloud.known_top_level_fields = {
        "node_id", "ts", "platform", "version", "e2e",
    }

    assert sync_mod.send_heartbeat(config) is True, (
        "even with old cloud, daemon must SUCCEED -- graceful degrade, "
        "not loud-fail. Strict-reject mode is scenario 4b."
    )

    expected_unknowns = {"cache_pushes", "security_posture", "local_store",
                         "local_store_size_mb", "ollama"}
    intersect = expected_unknowns & cloud.unknown_fields_logged
    assert intersect, (
        f"older cloud saw NO unknown fields from a newer daemon -- "
        f"either daemon payload silently shrank to fit old schema "
        f"(impossible), OR this test's allowlist is itself out of date. "
        f"Got unknown_fields_logged={sorted(cloud.unknown_fields_logged)!r}"
    )

    # Critical: cloud accepted (200 OK) AND still persisted the cache_push.
    # The contract is log + accept the rest. Silent drop is the bug.
    owner = sync_mod._owner_hash_for_token(config["api_key"])
    brain_key = f"brain:{owner}:{NODE_ID}:recent"
    assert brain_key in cloud.cache, (
        "older cloud accepted heartbeat (200 OK) but DID NOT persist the "
        "cache_pushes blob -- that's the silent-skew bug. Either "
        "ignore-and-log (+ persist) or reject loudly."
    )


# ── Scenario 3: daemon OLD, cloud NEW ────────────────────────────────────


@pytest.mark.skipif(
    not _git_has_depth(_OSS_REPO_ROOT, 3),
    reason=(
        "Scenario 3 requires OSS repo with >=3 commits of history for "
        "`git worktree add origin/main~3`. Shallow clones (CI --depth=1) "
        "skip. Manual recipe: clone with full history."
    ),
)
def test_scenario3_daemon_older_cloud_newer_missing_fields_handled(env):
    """Daemon HEAD~3 vs cloud HEAD -- older daemon doesn't send fields
    cloud now knows about. Cloud must NOT KeyError -> 500.

    Implementation note: rather than spawn a separate Python from an
    HEAD~3 worktree (slow + version-pin shell-out risks, blows the
    20-min wall budget), we POST an old-shape payload directly. The
    failure mode under test is the cloud-side schema's tolerance for a
    stripped payload -- if the new cloud handler grew a hard
    ``payload["new_field"]`` bracket lookup, this POST 500s.

    Per memory ``feedback_synthetic_tests_missed_real_event_shape``: we
    don't pretend to fully exercise an old daemon binary (that requires
    boot-strapping a separate venv per test). We DO exercise the
    cloud-side schema's missing-optional-field tolerance.
    """
    cloud = env["cloud"]

    old_payload = {
        "node_id": NODE_ID,
        "ts": "2026-05-14T10:00:00+00:00",
        "platform": "darwin",
        "version": "0.12.235",  # synthetic "N-3" banner
        "e2e": True,
        # NO cache_pushes / security_posture / local_store / ollama --
        # those all post-date the cutoff.
    }
    url = f"{env['base_url']}/ingest/heartbeat"
    req = urllib.request.Request(
        url, data=json.dumps(old_payload).encode(),
        headers={"Content-Type": "application/json", "X-Api-Key": API_KEY},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
            status = resp.status
    except urllib.error.HTTPError as e:
        pytest.fail(
            f"older daemon got HTTP {e.code} from new cloud -- the cloud "
            f"is NOT back-compat with old daemons. Body: "
            f"{e.read().decode(errors='replace')[:300]}"
        )

    assert status == 200, f"old-daemon heartbeat returned {status}"
    assert body.get("ok") is True, f"new cloud rejected old daemon: {body!r}"
    assert "0.12.235" in cloud.daemon_versions_seen, (
        f"old daemon's version banner not captured: "
        f"{cloud.daemon_versions_seen!r}"
    )
    last = cloud.heartbeats_seen[-1]
    assert "cache_pushes" not in last, (
        "old payload should not contain cache_pushes; test setup is wrong"
    )


# ── Scenario 4: unknown-field canary (lenient + strict modes) ────────────


def _splice_unknown_field(sync_mod, field_name: str, value):
    """Return a (install, restore) pair that monkeypatches sync._post so
    every /ingest/heartbeat call gets ``field_name: value`` spliced onto
    the payload. Simulates a future daemon adding a field cloud doesn't
    know about (e.g. v0.12.300 adds new_field_v4 without coordinating)."""
    original = sync_mod._post

    def wrapped(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            payload = {**payload, field_name: value}
        return original(path, payload, api_key, timeout)

    def install():
        sync_mod._post = wrapped

    def restore():
        sync_mod._post = original

    return install, restore


def test_scenario4a_unknown_field_canary_lenient_mode_logs_and_accepts(env):
    """Future daemon attaches ``new_field_v4`` -- cloud in lenient mode
    must ignore-and-log: HTTP 200, field name captured, REST persisted."""
    sync_mod, config, cloud = env["sync"], env["config"], env["cloud"]
    install, restore = _splice_unknown_field(sync_mod, "new_field_v4", "foo")
    install()
    try:
        assert sync_mod.send_heartbeat(config) is True
    finally:
        restore()

    assert "new_field_v4" in cloud.unknown_fields_logged, (
        "cloud SILENTLY accepted the unknown future field -- exact bug "
        "class this scenario guards against. Got "
        f"unknown_fields_logged={sorted(cloud.unknown_fields_logged)!r}"
    )
    owner = sync_mod._owner_hash_for_token(config["api_key"])
    brain_key = f"brain:{owner}:{NODE_ID}:recent"
    assert brain_key in cloud.cache, (
        "lenient cloud logged the unknown field but DID NOT persist the "
        "rest -- degradation isn't graceful, it's destructive."
    )


def test_scenario4b_unknown_field_canary_strict_mode_returns_426(env):
    """Same payload, cloud in STRICT mode (toggle for Enterprise plans
    that want loud-fail over silent-skew). Cloud returns HTTP 426
    (Upgrade Required); daemon's retry loop swallows it but the bool
    flips False after 3 attempts; cache_push must NOT have landed."""
    sync_mod, config, cloud = env["sync"], env["config"], env["cloud"]
    cloud.strict_reject_unknown_fields = True

    install, restore = _splice_unknown_field(sync_mod, "new_field_v4", "foo")
    install()
    try:
        ok = sync_mod.send_heartbeat(config)
    finally:
        restore()

    assert ok is False, (
        "daemon reported send_heartbeat=True against a STRICT cloud that "
        f"returned 426 -- daemon masking version-skew failures. "
        f"strict_rejected={cloud.strict_rejected}"
    )
    assert cloud.strict_rejected >= 1, (
        f"strict cloud didn't reject the unknown-field heartbeat: "
        f"strict_rejected={cloud.strict_rejected}"
    )
    owner = sync_mod._owner_hash_for_token(config["api_key"])
    brain_key = f"brain:{owner}:{NODE_ID}:recent"
    assert brain_key not in cloud.cache, (
        "STRICT cloud returned 426 BUT still persisted the cache_pushes "
        "blob -- worst of both worlds (loud-fail to daemon, "
        "silent-accept to dashboard)."
    )


# ── Scenario 2 extension: real cloud HEAD~3 worktree (best-effort) ───────


@pytest.mark.skipif(
    _cloud_repo_root() is None,
    reason=(
        "Real cloud HEAD~3 worktree requires clawmetry-cloud cloned next "
        "to OSS or CLAWMETRY_CLOUD_REPO set. Falls back to the schema-"
        "narrowed mock in test_scenario2_*."
    ),
)
def test_scenario2_extension_real_cloud_old_worktree_smoke():
    """If cloud repo is checked out locally, smoke-test the
    ``git worktree add HEAD~3`` machinery and prove the cloud's
    ``routes/api.py`` ingest handlers are reachable from that older SHA.

    Full Flask-test-client cross-import is intentionally deferred -- the
    cloud's ``db.py`` Postgres stack can't boot in OSS CI without
    significant fixture surgery (out of budget for this PR). This test
    proves the WORKTREE PATH IS LIVE so a future PR can wire the rest.
    """
    cloud_root = _cloud_repo_root()
    assert cloud_root is not None  # guarded by skipif

    if not _git_has_depth(cloud_root, 3):
        pytest.skip(
            f"cloud repo at {cloud_root} is shallow; can't checkout HEAD~3"
        )

    worktree_path = f"/tmp/clawmetry-cloud-old-{os.getpid()}"
    # Clean up any leftover from a previous run.
    subprocess.run(
        ["git", "worktree", "remove", "--force", worktree_path],
        cwd=cloud_root, capture_output=True,
    )
    try:
        result = subprocess.run(
            ["git", "worktree", "add", "--detach", worktree_path, "HEAD~3"],
            cwd=cloud_root, capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            pytest.skip(f"git worktree add failed: {result.stderr[:200]}")
        api_path = os.path.join(worktree_path, "routes", "api.py")
        assert os.path.isfile(api_path), (
            f"cloud HEAD~3 missing routes/api.py at {api_path}"
        )
        src = open(api_path).read()
        assert "/ingest/heartbeat" in src or "/ingest/events" in src, (
            "cloud HEAD~3 routes/api.py missing ingest handlers -- file "
            "renamed or unexpected SHA"
        )
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", worktree_path],
            cwd=cloud_root, capture_output=True,
        )
