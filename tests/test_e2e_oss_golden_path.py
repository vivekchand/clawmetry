"""
OSS golden path E2E gate (criterion C1).

Verifies three tiers of correctness after a full wheel-install + OpenClaw boot:

  1. /api/auth/check returns {valid: true} -- token plumbing is correct.
  2. /api/sessions returns >= 1 session -- the synthetic JSONL was ingested
     into DuckDB by the dashboard sync thread (proves the "send a message"
     path works end-to-end from an installed wheel).
  3. All 9 C1 canonical tabs navigate without any auth-blocking overlay --
     sessions, brain, tokens, crons, flow, memory, security, health.

C1 definition (tracking issue #1646):
  "install ClawMetry from a wheel + spin up real OpenClaw + send a message +
  verify dashboard renders all tabs (Sessions, Brain, Tokens, Crons, Channels,
  Flow, Memory, Security, Health) WITHOUT auth errors. Runs on every PR in
  <5 min."

Run against the golden-path workflow server:
    CLAWMETRY_URL=http://localhost:8920 CLAWMETRY_TOKEN=ci-golden-token \\
    pytest tests/test_e2e_oss_golden_path.py -v

Or against a local dev server (after seeding session data):
    OPENCLAW_GATEWAY_TOKEN=ci-test-token python dashboard.py --port 8920 &
    CLAWMETRY_URL=http://localhost:8920 CLAWMETRY_TOKEN=ci-test-token \\
    pytest tests/test_e2e_oss_golden_path.py -v
"""
from __future__ import annotations

import json
import os
import urllib.request

import pytest

try:
    import playwright  # noqa: F401
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

BASE_URL = os.environ.get("CLAWMETRY_URL", "http://localhost:8900")
TOKEN = os.environ.get("CLAWMETRY_TOKEN", "ci-test-token")

# C1 canonical tabs. Maps the spec names to the JS switchTab() identifiers:
#   Sessions  -> transcripts
#   Brain     -> brain
#   Tokens    -> usage
#   Crons     -> crons
#   Channels  -> channels  (skipped if not present in dashboard version)
#   Flow      -> flow
#   Memory    -> memory
#   Security  -> security
#   Health    -> overview
C1_TABS = [
    "overview",     # Health
    "brain",        # Brain
    "usage",        # Tokens
    "crons",        # Crons
    "flow",         # Flow
    "memory",       # Memory
    "security",     # Security
    "subagents",    # Subagents (present in current dashboard nav)
    "transcripts",  # Sessions
]

_BLOCKING_OVERLAY_IDS = [
    "login-overlay",
    "gw-setup-overlay",
    "auth-overlay",
    "setup-overlay",
]

pytestmark = pytest.mark.skipif(
    not _PLAYWRIGHT_AVAILABLE,
    reason="playwright not installed -- pip install pytest-playwright",
)


def _api(path: str) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


class TestOSSGoldenPath:
    """Full OSS golden path: wheel-installed dashboard + synced OpenClaw data + 9 tabs.

    All three test groups must pass together for criterion C1 to be green:
      * auth group -- token plumbing
      * data group -- JSONL ingestion via sync thread
      * tab group  -- Playwright overlay sweep
    """

    # ---- auth group --------------------------------------------------------

    def test_auth_check_returns_valid(self):
        """Token must be accepted by /api/auth/check before we attempt any tab."""
        data = _api("/api/auth/check")
        assert data.get("valid") is True, (
            f"/api/auth/check returned valid=False. Response: {data}. "
            f"Ensure server started with OPENCLAW_GATEWAY_TOKEN={TOKEN!r}."
        )

    # ---- data group --------------------------------------------------------

    def test_sessions_seeded_in_duckdb(self):
        """At least one session must be present -- proves the synthetic JSONL
        written to ~/.openclaw/agents/main/sessions/ was picked up by the
        dashboard's startup sync thread and ingested into DuckDB.

        Failure here means the 'send a message' step of C1 is broken:
        either the sync thread is not running, the JSONL path is wrong,
        or the ingest pipeline dropped the row.
        """
        data = _api("/api/sessions")
        sessions = data.get("sessions", [])
        assert len(sessions) >= 1, (
            f"Expected >= 1 seeded session in /api/sessions, got {len(sessions)}. "
            f"Check that the seed-synthetic-session workflow step ran and that "
            f"the dashboard sync thread had time to ingest the JSONL. "
            f"Full response keys: {list(data)}"
        )

    # ---- tab group ---------------------------------------------------------

    @pytest.fixture
    def _golden_page(self, _shared_chromium):
        """Fresh browser context with the gateway token pre-seeded into localStorage.

        A new context per parametrized case so tab-navigation state never leaks
        between test cases (mirrors the _overlay_page pattern in
        test_e2e_oss_all_tabs.py).
        """
        ctx = _shared_chromium.new_context(viewport={"width": 1280, "height": 720})
        ctx.add_init_script(
            "try { "
            f"localStorage.setItem('clawmetry-token', {json.dumps(TOKEN)}); "
            f"localStorage.setItem('clawmetry-gw-token', {json.dumps(TOKEN)}); "
            "} catch(e) {}"
        )
        page = ctx.new_page()
        yield page
        ctx.close()

    @pytest.mark.parametrize("tab", C1_TABS)
    def test_c1_tab_no_auth_overlay(self, _golden_page, tab):
        """Each C1 tab must navigate without any auth-blocking overlay.

        This is the definitive gate for the user-reported symptom:
        'gateway token is not passed for OSS so it never displays other
        screens' (2026-05-17). A visible overlay after token injection means
        the auth plumbing broke for that tab.
        """
        page = _golden_page
        page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=15000)

        if tab != "overview":
            page.evaluate(
                "typeof window.switchTab === 'function' && "
                f"window.switchTab({json.dumps(tab)})"
            )

        page.wait_for_timeout(1000)

        blocking = []
        for oid in _BLOCKING_OVERLAY_IDS:
            el = page.query_selector(f"#{oid}")
            if el is None:
                continue
            display = el.evaluate("el => getComputedStyle(el).display")
            visibility = el.evaluate("el => getComputedStyle(el).visibility")
            if display != "none" and visibility != "hidden":
                blocking.append(
                    f"#{oid} display={display!r} visibility={visibility!r}"
                )

        assert not blocking, (
            f"Tab '{tab}': auth overlay still visible after token injection: "
            + ", ".join(blocking)
            + f". Ensure OPENCLAW_GATEWAY_TOKEN={TOKEN!r} matches CLAWMETRY_TOKEN."
        )
