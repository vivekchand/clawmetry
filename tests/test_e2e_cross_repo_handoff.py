"""C4 cross-repo handoff E2E.

Tests the full funnel in four tiers:

  T1 -- landing signup:   POST /api/subscribe returns {ok:true, handoff_url}
  T2 -- cloud server:     /cloud returns HTTP 200 (stubbed DB + auth)
  T3 -- daemon pair:      /ingest/heartbeat returns 200 (daemon authenticated)
  T4 -- first sync event: cache_push included in heartbeat, accepted by cloud

Checkout layout expected by the workflow:

  $GITHUB_WORKSPACE/oss/    <- this repo (clawmetry)
  $GITHUB_WORKSPACE/cloud/  <- vivekchand/clawmetry-cloud

T1 currently uses an inline Flask stub for the landing server so there is no
dependency on clawmetry-landing#279 being merged. Once that PR lands, replace
the inline stub with a subprocess that boots clawmetry-landing/tests/run_landing.py.

DaemonSim (T3/T4) is imported from $GITHUB_WORKSPACE/cloud/tests/e2e_browser/
at runtime so the wire format stays in sync with the real daemon.

Tracking: vivekchand/clawmetry#1646 (C4).
Budget: < 10 min.
"""
from __future__ import annotations

import base64
import os
import secrets
import subprocess
import sys
import threading
import time

import pytest
import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))
# Workflow layout: oss/ and cloud/ are siblings under $GITHUB_WORKSPACE.
_WORKSPACE = os.path.abspath(os.path.join(_REPO_ROOT, ".."))
_CLOUD_DIR = os.environ.get("CLOUD_CHECKOUT_PATH",
                             os.path.join(_WORKSPACE, "cloud"))
_CLOUD_E2E_DIR = os.path.join(_CLOUD_DIR, "tests", "e2e_browser")

LANDING_PORT = 18910
CLOUD_PORT = 18912
LANDING_BASE = f"http://127.0.0.1:{LANDING_PORT}"
CLOUD_BASE = f"http://127.0.0.1:{CLOUD_PORT}"

# Must match run_cloud.py TEST_TOKEN / TEST_NODE_ID constants.
TEST_TOKEN = "cm_test_brain_e2e_token_aaaaaaaaaa"
TEST_NODE_ID = "test-node-laptop-001"

# Random 32-byte AES key per test run. DaemonSim encrypts with this key;
# the cloud stores the blob as-is (client-side decryption only).
_ENC_KEY = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wait_http(url: str, timeout_s: float = 30.0, label: str = "") -> None:
    """Poll url until it returns a non-5xx status, or raise TimeoutError."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=3, allow_redirects=True)
            if r.status_code < 500:
                return
        except Exception:
            pass
        time.sleep(0.4)
    raise TimeoutError(
        f"{'[' + label + '] ' if label else ''}"
        f"Server at {url} never returned < 500 in {timeout_s}s"
    )


def _dump_log(path: str, label: str) -> None:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            content = f.read()[-3000:]
        sys.stderr.write(f"\n=== {label} log (last 3000 chars) ===\n{content}\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# T1 landing stub (inline Flask, no clawmetry-landing dep required)
# ---------------------------------------------------------------------------
# Replace with a subprocess booting clawmetry-landing/tests/run_landing.py
# once clawmetry-landing#279 is merged.

def _start_landing_stub() -> threading.Thread:
    """Boot a minimal stub for the landing /api/subscribe endpoint."""
    import flask  # noqa: PLC0415

    app = flask.Flask(__name__)

    @app.route("/api/subscribe", methods=["POST"])
    def subscribe():
        body = flask.request.get_json(silent=True) or {}
        email = str(body.get("email", "")).strip()
        if not email or "@" not in email:
            return flask.jsonify({"ok": False, "error": "invalid email"}), 400
        # handoff_url is the cloud signup deep-link the landing page redirects to.
        return flask.jsonify({
            "ok": True,
            "email": email,
            "handoff_url": "https://app.clawmetry.com/connect",
        })

    @app.route("/", methods=["GET"])
    def root():
        return (
            "<html><head></head><body>"
            "<h1>ClawMetry</h1>"
            "<a href='#get-started' id='get-started-cta'>Get Started</a>"
            "<section id='get-started'></section>"
            "</body></html>"
        )

    def _serve():
        import logging
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        app.run(host="127.0.0.1", port=LANDING_PORT, debug=False,
                use_reloader=False)

    t = threading.Thread(target=_serve, daemon=True, name="landing-stub")
    t.start()
    return t


# ---------------------------------------------------------------------------
# Module-scoped server lifecycle
# ---------------------------------------------------------------------------

_cloud_proc: subprocess.Popen | None = None
_cloud_log_f = None
_landing_thread: threading.Thread | None = None


def setup_module(module):  # noqa: ARG001
    global _cloud_proc, _cloud_log_f, _landing_thread

    # T1 landing stub (in-process, no port collision risk).
    _landing_thread = _start_landing_stub()
    _wait_http(f"{LANDING_BASE}/", 10, label="landing")

    # T2 cloud server via the existing run_cloud.py stub.
    run_cloud_py = os.path.join(_CLOUD_E2E_DIR, "run_cloud.py")
    if not os.path.exists(run_cloud_py):
        raise RuntimeError(
            f"run_cloud.py not found at {run_cloud_py}. "
            "Ensure the clawmetry-cloud checkout is at $GITHUB_WORKSPACE/cloud/ "
            "(or set CLOUD_CHECKOUT_PATH env)."
        )

    cloud_env = os.environ.copy()
    cloud_env.update({
        "DATABASE_URL": "dummy",
        "CLOUD_MODE": "1",
        "POLICY_MODE": "off",
        "CLAWMETRY_E2E_STUB_AUTH": "1",
        "CLAWMETRY_E2E_PORT": str(CLOUD_PORT),
    })
    _cloud_log_f = open("/tmp/c4-cloud.log", "wb")  # noqa: SIM115
    _cloud_proc = subprocess.Popen(
        [sys.executable, run_cloud_py],
        cwd=_CLOUD_DIR,
        env=cloud_env,
        stdout=_cloud_log_f,
        stderr=subprocess.STDOUT,
    )
    try:
        _wait_http(f"{CLOUD_BASE}/cloud", 30, label="cloud")
    except TimeoutError:
        _dump_log("/tmp/c4-cloud.log", "cloud")
        raise


def teardown_module(module):  # noqa: ARG001
    if _cloud_proc and _cloud_proc.poll() is None:
        _cloud_proc.terminate()
        try:
            _cloud_proc.wait(5)
        except subprocess.TimeoutExpired:
            _cloud_proc.kill()
            _cloud_proc.wait(2)
    if _cloud_log_f:
        _cloud_log_f.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_t1_landing_signup_returns_ok():
    """T1: landing POST /api/subscribe returns {ok:true, handoff_url}.

    Proves the landing signup endpoint accepts a valid email and returns
    the cloud handoff URL. Currently exercises the inline stub server;
    will be upgraded to boot the real clawmetry-landing app once
    clawmetry-landing#279 merges.
    """
    r = requests.post(
        f"{LANDING_BASE}/api/subscribe",
        json={"email": "c4-handoff-test@example.com"},
        timeout=10,
    )
    assert r.status_code == 200, (
        f"Expected 200, got {r.status_code}: {r.text[:300]}"
    )
    body = r.json()
    assert body.get("ok") is True, (
        f"/api/subscribe: expected ok=true. Got: {body!r}"
    )
    assert "handoff_url" in body, (
        f"Response must include a handoff_url pointing to cloud signup. "
        f"Got: {body!r}"
    )


def test_t2_cloud_server_boots():
    """T2: cloud /cloud returns HTTP 200 (stubbed DB + auth wired).

    Baseline check: the cloud server must be live before the daemon can pair.
    """
    r = requests.get(
        f"{CLOUD_BASE}/cloud?token={TEST_TOKEN}",
        timeout=10,
        allow_redirects=True,
    )
    assert r.status_code == 200, (
        f"Cloud /cloud returned {r.status_code}, expected 200. "
        "Check that run_cloud.py is starting with CLAWMETRY_E2E_STUB_AUTH=1 "
        "and CLAWMETRY_E2E_PORT matches CLOUD_PORT."
    )


def test_t3_daemon_pairs_via_heartbeat():
    """T3: DaemonSim sends /ingest/heartbeat; cloud returns 200.

    Proves the OSS daemon can authenticate and register with the cloud
    using the real wire format (Authorization: Bearer token + JSON body
    with node metadata). No TLS, no external service.
    """
    if _CLOUD_E2E_DIR not in sys.path:
        sys.path.insert(0, _CLOUD_E2E_DIR)
    from daemon_sim import DaemonSim, make_fake_events  # noqa: PLC0415

    sim = DaemonSim(
        api_base=CLOUD_BASE,
        api_key=TEST_TOKEN,
        node_id=TEST_NODE_ID,
        encryption_key=_ENC_KEY,
        events=make_fake_events(2, TEST_NODE_ID),
        heartbeat_interval_s=9999,
        push_cache=False,
    )
    sim._heartbeat_once()  # single synchronous heartbeat, no background thread

    assert sim.last_error is None, (
        f"Heartbeat raised: {sim.last_error}\n"
        "Daemon pair failed. Verify TEST_TOKEN and TEST_NODE_ID match "
        "run_cloud.py constants and that the auth stub is active."
    )
    assert sim.heartbeats_sent == 1, (
        f"Expected 1 heartbeat, got {sim.heartbeats_sent}"
    )


def test_t4_first_sync_event_lands():
    """T4: DaemonSim sends heartbeat WITH cache_pushes; cloud accepts both.

    cache_pushes_sent >= 1 proves the AES-256-GCM encrypted brain payload
    was accepted by /ingest/heartbeat, which is the 'first sync event lands'
    assertion in the C4 criterion. The node also appears in /api/cloud/nodes,
    confirming the token -> owner_hash -> node ownership chain is intact.
    """
    if _CLOUD_E2E_DIR not in sys.path:
        sys.path.insert(0, _CLOUD_E2E_DIR)
    from daemon_sim import DaemonSim, make_fake_events  # noqa: PLC0415

    sim = DaemonSim(
        api_base=CLOUD_BASE,
        api_key=TEST_TOKEN,
        node_id=TEST_NODE_ID,
        encryption_key=_ENC_KEY,
        events=make_fake_events(5, TEST_NODE_ID),
        heartbeat_interval_s=9999,
        push_cache=True,
    )
    sim._heartbeat_once()

    assert sim.last_error is None, (
        f"Heartbeat+cache_push failed: {sim.last_error}\n"
        "The sync event did not land. Check /ingest/heartbeat handler and "
        "cloud_cache.py InMemoryCache. See /tmp/c4-cloud.log for detail."
    )
    assert sim.heartbeats_sent == 1, (
        f"Expected heartbeats_sent=1, got {sim.heartbeats_sent}"
    )
    assert sim.cache_pushes_sent == 1, (
        f"cache_pushes_sent={sim.cache_pushes_sent}: expected >= 1.\n"
        "DaemonSim.push_cache=True should populate cache_pushes in the "
        "heartbeat body. Check that make_fake_events() returned > 0 events."
    )

    # Belt-and-suspenders: the node list confirms ownership chain.
    r = requests.get(
        f"{CLOUD_BASE}/api/cloud/nodes",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        params={"token": TEST_TOKEN},
        timeout=10,
    )
    assert r.status_code == 200, (
        f"/api/cloud/nodes returned {r.status_code} after heartbeat+cache_push."
    )
    try:
        body = r.json()
        nodes = body if isinstance(body, list) else body.get("nodes", [])
        node_ids = [n.get("node_id") for n in nodes]
        assert TEST_NODE_ID in node_ids, (
            f"Node {TEST_NODE_ID!r} missing from nodes list {node_ids!r}. "
            "Sync event may have landed in cache but ownership chain is broken."
        )
    except Exception as exc:
        raise AssertionError(
            f"/api/cloud/nodes parse error: {exc}. Body: {r.text[:300]!r}"
        ) from exc
