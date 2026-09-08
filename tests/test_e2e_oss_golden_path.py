"""
OSS golden path E2E gate (criterion C1).

Verifies four tiers of correctness after a full wheel-install + OpenClaw boot:

  1. /api/auth/check returns {valid: true} -- token plumbing is correct.
  2. /api/sessions returns >= 1 session -- the synthetic JSONL was ingested
     into DuckDB by the dashboard sync thread (proves the "send a message"
     path works end-to-end from an installed wheel).
  3. All C1 canonical tabs navigate without any auth-blocking overlay --
     sessions, brain, tokens, crons, channels, flow, memory, security, health,
     subagents.
  4. Sessions tab DOM contains the seeded session title "Golden Path E2E" --
     proves the full render pipeline from JSONL seed to DOM is intact.
  5. /api/attention returns correct shape + honesty invariant holds --
     the needs-you strip never surfaces a confident list when the daemon is
     stale. Added 2026-08-16 to close the C1 gap opened by PR #4916.
  6. /api/hooks/attention accepts a known-runtime POST with HTTP 200 (fail-
     open) and returns the correct shape.

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
import urllib.error
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
#   Channels  -> channels
#   Flow      -> flow
#   Memory    -> memory
#   Security  -> security
#   Health    -> overview
C1_TABS = [
    "overview",     # Health
    "brain",        # Brain
    "usage",        # Tokens
    "crons",        # Crons
    "channels",     # Channels
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


def _switch_tab(page, tab: str) -> None:
    """Switch the dashboard to *tab* via window.switchTab(), asserting it exists.

    Replaces the old short-circuit guard
      page.evaluate("typeof window.switchTab === 'function' && switchTab(tab)")
    which silently no-oped when switchTab was absent, causing every subsequent
    overlay check to inspect the overview tab instead of the intended tab.
    """
    result = page.evaluate(
        "(tab) => {"
        "  if (typeof window.switchTab !== 'function') return 'no-switchtab';"
        "  window.switchTab(tab);"
        "  return 'ok';"
        "}",
        tab,
    )
    assert result == "ok", (
        f"window.switchTab() not available when switching to tab '{tab}'. "
        f"Root causes: app.js parse/load error, auth overlay still blocking, "
        f"or page not yet initialised. "
        f"Ensure {BASE_URL!r} started with OPENCLAW_GATEWAY_TOKEN={TOKEN!r}."
    )


class TestOSSGoldenPath:
    """Full OSS golden path: wheel-installed dashboard + synced OpenClaw data + C1 tabs.

    All four test groups must pass together for criterion C1 to be green:
      * auth group      -- token plumbing
      * data group      -- JSONL ingestion via sync thread
      * tab group       -- Playwright overlay sweep
      * render group    -- DOM content verification (seeded session title present)
      * attention group -- /api/attention shape + honesty invariant (added 2026-08-16)
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

    # ---- render group ------------------------------------------------------

    def test_sessions_tab_renders_seeded_session(self, _golden_page):
        """Sessions tab DOM must contain the seeded session title after data loads.

        Tier 4 of the C1 gate: proves the full end-to-end render pipeline from
        JSONL seed to DuckDB ingest to API response to DOM render is working.
        The previous three tiers prove:
          - /api/auth/check accepts the token
          - /api/sessions has >= 1 session in DuckDB
          - No auth overlay blocks the Sessions tab
        This tier proves the session title "Golden Path E2E" actually appears
        in the rendered DOM after loadTranscripts() completes.

        A broken render pipeline that shows an empty tab with no overlay
        would pass tiers 1-3 but fail here.
        """
        page = _golden_page
        page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=15000)

        # Switch to the transcripts (Sessions) tab; this triggers loadTranscripts()
        # which fetches /api/sessions and renders the list into #transcript-list.
        _switch_tab(page, "transcripts")

        # Wait up to 8s for the seeded session title to appear in the live DOM.
        # Playwright polls after each mutation so this catches the render as
        # soon as loadTranscripts() populates #transcript-list.
        found = False
        try:
            page.wait_for_selector("text=Golden Path E2E", timeout=8000)
            found = True
        except Exception:
            pass

        if not found:
            # Secondary check: scan full page HTML in case the text is present
            # but not matched by the selector (e.g. inside a partially-hidden
            # container or an attribute value).
            found = "Golden Path E2E" in page.content()

        assert found, (
            "Sessions tab did not render the seeded session title 'Golden Path E2E' "
            "within 8s of tab switch. Possible root causes:\n"
            "  (1) JSONL ingest is broken: the session never reached DuckDB\n"
            "      (check test_sessions_seeded_in_duckdb for prior failure);\n"
            "  (2) loadTranscripts() is not populating #transcript-list\n"
            "      (check /api/sessions response in the CI dashboard log);\n"
            "  (3) The 'session_start' event title field is not rendered in the UI\n"
            "      (check routes/sessions.py and the #transcript-list DOM content).\n"
            f"  BASE_URL={BASE_URL!r}"
        )

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
            _switch_tab(page, tab)

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

    # ---- attention group ---------------------------------------------------
    # Closes the C1 gap opened by PR #4916 (2026-08-16): the needs-you
    # attention layer ships /api/attention + /api/hooks/attention but neither
    # was covered by any golden-path test. A 500 or shape regression on
    # /api/attention silently renders the 'needs you' strip as 'Can't tell
    # right now' for all users with no CI signal, because the tab overlay
    # tests only check auth overlays, not API contract.

    def test_attention_endpoint_returns_valid_shape(self):
        """/api/attention must return HTTP 200 with the complete response shape.

        In the golden-path environment the sync daemon is NOT running, so
        fresh=False is expected. The test also verifies the honesty invariant:
        fresh=False must return items=[] and waiting=0 so a stale daemon never
        surfaces a confident list of blocked sessions in the UI strip.

        If this test fails with a KeyError, check routes/attention.py
        build_attention() -- all three exit paths (unavailable, stale, fresh)
        must return the same seven keys.
        """
        data = _api("/api/attention")
        required_keys = (
            "items", "waiting", "working", "fresh",
            "reason", "daemon_age_seconds", "runtimes_without_approval",
        )
        for key in required_keys:
            assert key in data, (
                f"/api/attention missing required key {key!r}. Response: {data}. "
                f"All three exit paths in build_attention() (unavailable/stale/fresh) "
                f"must return all {len(required_keys)} keys."
            )
        assert isinstance(data["items"], list), (
            f"'items' must be list, got {type(data['items']).__name__}. "
            f"Response: {data}."
        )
        assert isinstance(data["waiting"], int), (
            f"'waiting' must be int, got {type(data['waiting']).__name__}."
        )
        assert isinstance(data["working"], int), (
            f"'working' must be int, got {type(data['working']).__name__}."
        )
        assert isinstance(data["fresh"], bool), (
            f"'fresh' must be bool, got {type(data['fresh']).__name__}."
        )
        assert isinstance(data["runtimes_without_approval"], list), (
            f"'runtimes_without_approval' must be list, "
            f"got {type(data['runtimes_without_approval']).__name__}."
        )
        # Honesty invariant: a stale daemon must NEVER surface a confident list.
        # fresh=False + items!=[] would show outdated attention badges as real,
        # defeating the three-state design (waiting / quiet / can't tell).
        if not data["fresh"]:
            assert data["items"] == [], (
                f"Honesty invariant violated: fresh=False but items={data['items']!r}. "
                f"A stale daemon must return items=[] so the strip renders "
                f"'Can't tell right now' rather than a potentially outdated list. "
                f"Check build_attention() in routes/attention.py: "
                f"the payload line must be 'items: items if fresh else []'."
            )
            assert data["waiting"] == 0, (
                f"Honesty invariant violated: fresh=False but waiting={data['waiting']}. "
                f"Must be 0 when fresh=False (consistent with items=[])."
            )

    def test_attention_hook_accepts_known_runtime(self):
        """/api/hooks/attention must accept a POST from a known runtime and return ok.

        The endpoint is loopback-only; the test runner is on the same host as the
        dashboard server so the remote_addr guard is satisfied.

        The endpoint is fail-open by design: it ALWAYS returns HTTP 200 even when
        the daemon proxy is unavailable (stored=False). A hook that 500s would
        stall the runtime process that called it mid-permission-decision, which
        is far worse than a missing badge. This test verifies that contract.

        In the golden-path environment the daemon proxy may be unavailable, so
        stored=False is acceptable -- the test only asserts it is a bool.
        """
        body = json.dumps({
            "session_id": "golden-path-test-session-attn-001",
            "tool_name":  "Bash",
        }).encode()
        req = urllib.request.Request(
            f"{BASE_URL}/api/hooks/attention?runtime=claude_code",
            data=body,
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type":  "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
                data = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            status = exc.code
            data = {}

        assert status == 200, (
            f"/api/hooks/attention returned HTTP {status} (expected 200). "
            f"The endpoint must ALWAYS return 200 -- it is fail-open by design "
            f"so a runtime hook process calling it mid-permission-decision is "
            f"never stalled by a 500. "
            f"Check the outer try/except in routes/attention.py "
            f"api_hook_attention(): it must catch ALL exceptions and return 200."
        )
        assert data.get("ok") is True, (
            f"/api/hooks/attention returned ok={data.get('ok')!r} (expected True). "
            f"Response: {data}."
        )
        assert data.get("state") == "waiting", (
            f"/api/hooks/attention returned state={data.get('state')!r} "
            f"(expected 'waiting'). Response: {data}."
        )
        assert "stored" in data, (
            f"/api/hooks/attention response missing 'stored' key. "
            f"Response: {data}. "
            f"'stored' tells the caller whether the badge was persisted -- "
            f"absent means the caller cannot distinguish success from a silent no-op."
        )
        assert isinstance(data["stored"], bool), (
            f"'stored' must be bool, got {type(data.get('stored')).__name__}."
        )
