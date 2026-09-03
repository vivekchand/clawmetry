"""Guards for the end-to-end encryption invariant (2026-08-24 security review).

The product's headline privacy claim is that session content only leaves the
machine as ciphertext. Four of the eleven findings in that review existed
because the claim was enforced by convention at each call site rather than by a
rule, and two more existed because a test asserted on a code path that wasn't
the one running.

Every test here fails against the pre-fix code. That is the point: a guard that
passes before the fix guards nothing.
"""
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import sync  # noqa: E402


# ── Finding 1: the managed cloud cannot turn encryption off ──────────────────


class _FakeArgs:
    enc_key = None
    start_sync_now = False
    keep_local = False
    custom_node_id = None
    restart = False
    foreground = False


@pytest.mark.parametrize(
    "endpoint_env, expect_honoured",
    [
        ({}, False),                                                # managed cloud
        ({"CLAWMETRY_ENDPOINT": "https://ingest.clawmetry.com"}, False),  # managed, spelled out
        ({"CLAWMETRY_ENDPOINT": "https://clawmetry.internal.acme"}, True),  # self-hosted
    ],
)
def test_plaintext_downgrade_only_from_a_custom_endpoint(
    monkeypatch, endpoint_env, expect_honoured
):
    """``{"e2e": false}`` is a self-hosted opt-out, never a remote kill switch.

    Before the fix, ``ingest.clawmetry.com`` answering ``e2e:false`` set the
    client's key to "" and every subsequent transcript went up as plaintext.
    """
    from clawmetry import endpoints

    for key in ("CLAWMETRY_ENDPOINT", "CLAWMETRY_INGEST_URL", "CLAWMETRY_APP_BASE"):
        monkeypatch.delenv(key, raising=False)
    for key, value in endpoint_env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(endpoints, "_cfg_cache", None)
    monkeypatch.setattr(endpoints, "CONFIG_PATH", "/nonexistent/clawmetry/config.json")

    assert endpoints.is_custom_endpoint() is expect_honoured


def test_endpoints_module_is_the_only_authority_on_managed_vs_custom():
    """The gate must key off the shared resolver, not a hand-rolled comparison."""
    src = open(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "clawmetry", "cli.py"),
        encoding="utf-8",
    ).read()
    downgrade = src.split("_server_e2e = result.get")[1][:600]
    assert "is_custom_endpoint" in downgrade, (
        "the e2e:false branch must consult endpoints.is_custom_endpoint(); "
        "without it the managed cloud can downgrade any client to plaintext"
    )


def test_existing_key_is_never_wiped_by_a_downgrade():
    """A node that already has a key keeps it, whatever the server says.

    ``save_config`` is a whole-file overwrite that only re-adds
    ``encryption_key`` when it is non-empty, so accepting a downgrade on
    reconnect used to destroy the key with no keychain fallback.
    """
    src = open(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "clawmetry", "cli.py"),
        encoding="utf-8",
    ).read()
    block = src.split("_server_plaintext = (")[1].split(")")[0]
    assert "_existing_key" in block, (
        "the plaintext branch must exclude nodes that already hold a key"
    )


# ── Finding 3: no key means no upload, never a plaintext upload ──────────────


def test_content_egress_permitted_refuses_without_a_key():
    assert sync.content_egress_permitted("", "/ingest/events") is False
    assert sync.content_egress_permitted(None, "/ingest/events") is False
    assert sync.content_egress_permitted("a-key", "/ingest/events") is True


CONTENT_ENDPOINTS = (
    "/ingest/events",
    "/ingest/logs",
    "/ingest/memory",
    "/ingest/stream",
)


@pytest.mark.parametrize("endpoint", CONTENT_ENDPOINTS)
def test_no_content_endpoint_has_a_plaintext_post(endpoint):
    """No call site may POST a content endpoint outside the AES-GCM envelope.

    Reads the source rather than exercising each daemon path, because the
    thing being guarded is the *shape* — ``if enc_key: blob else: payload`` —
    and a new one can be added anywhere in an 20k-line module.
    """
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "clawmetry",
        "sync.py",
    )
    src = open(path, encoding="utf-8").read()
    for chunk in src.split('_post(')[1:]:
        head = chunk[:400]
        if endpoint not in head:
            continue
        assert '"encrypted": True' in head or '"blob"' in head, (
            f"a _post() to {endpoint} does not carry an encrypted blob:\n"
            f"{head[:300]}"
        )


def test_the_no_key_rule_is_logged_once_per_endpoint():
    """A keyless node should say so plainly, not flood the log every tick."""
    sync._NO_KEY_REFUSALS.clear()
    assert sync.content_egress_permitted("", "/ingest/events") is False
    assert sync._NO_KEY_REFUSALS.get("/ingest/events") is True
    assert sync.content_egress_permitted("", "/ingest/events") is False


# ── Finding 4: content-bearing fields ride inside the envelope ───────────────


def test_session_title_is_encrypted_not_sent_in_the_clear():
    """A session's title comes from its first prompt or a chat subject line."""
    clear, blob = sync.split_session_title(
        "Reset the prod database password", sync.generate_encryption_key(), "sess-1234"
    )
    assert clear == "sess-1234", "the cleartext row must carry a neutral identifier"
    assert blob, "the readable title must travel encrypted"
    assert "prod database" not in json.dumps(clear)


def test_session_title_is_withheld_entirely_when_there_is_no_key():
    clear, blob = sync.split_session_title("Draft the layoff email", "", "sess-1234")
    assert clear == "sess-1234"
    assert blob is None


def test_session_title_round_trips_for_the_browser():
    key = sync.generate_encryption_key()
    _, blob = sync.split_session_title("Reset the prod database password", key, "s-1")
    assert sync.decrypt_payload(blob, key)["display_name"] == (
        "Reset the prod database password"
    )


def test_cron_events_carry_no_prompt_or_shell_command():
    """The cron event is server-parsed, so it must hold no content.

    ``task`` is the job's prompt text and ``watchedCommand`` is a shell command
    line; both used to ship in the clear on ``/api/ingest``.
    """
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "clawmetry",
        "sync.py",
    )
    src = open(path, encoding="utf-8").read()
    block = src.split("event_data = {")[1].split("\n            }")[0]
    for banned in ('"task"', '"watchedCommand"', '"lastError"'):
        assert banned not in block, (
            f"{banned} is content and must not ride in the unencrypted cron event"
        )


# ── Finding 2: approval requests carry no tool arguments ─────────────────────


def test_approval_request_carries_no_tool_arguments():
    """For a Bash gate ``args`` is the literal shell command; for Write/Edit
    it is the file path and its contents."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "clawmetry",
        "approvals.py",
    )
    src = open(path, encoding="utf-8").read()
    req = src.split("req = {")[1].split("}")[0]
    assert '"args"' not in req
    assert '"context"' not in req
    assert '"tool_name"' in req, "the routing envelope is still needed"


# ── Finding 10: server-supplied prompts need a local opt-in ──────────────────


def test_prompt_bearing_actions_are_off_by_default(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ALLOW_REMOTE_PROMPTS", raising=False)
    assert sync._remote_prompts_enabled({}) is False
    assert sync._remote_prompts_enabled({"remote_prompts": True}) is True


def test_prompt_bearing_actions_respect_the_env_override(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_ALLOW_REMOTE_PROMPTS", "1")
    assert sync._remote_prompts_enabled({}) is True
    monkeypatch.setenv("CLAWMETRY_ALLOW_REMOTE_PROMPTS", "0")
    assert sync._remote_prompts_enabled({"remote_prompts": True}) is False


def test_agent_invoking_actions_are_all_gated():
    """Every action that interpolates a server string into an agent prompt."""
    assert sync._PROMPT_BEARING_ACTIONS == {
        "selfevolve_fix",
        "cron_create",
        "cron_fix",
    }
    assert sync._PROMPT_BEARING_ACTIONS <= sync._PENDING_ACTIONS


def test_dispatcher_refuses_a_prompt_action_when_not_opted_in(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_ALLOW_REMOTE_PROMPTS", raising=False)
    called = []
    monkeypatch.setattr(
        sync, "_action_selfevolve_fix", lambda *a, **k: called.append(a)
    )
    sync._dispatch_pending_action({}, {"type": "selfevolve_fix", "id": "x"})
    assert called == [], "a server-supplied prompt reached a local agent"


# ── Finding 11: the key travels in the fragment, and nowhere else ────────────


def _dashboard_handoff_url():
    """The hand-off URL as one string, however it is spelled in source.

    Reads the ``_dashboard_url = ...`` assignment and joins it, so an
    f-string split across several lines (which is how it is written now)
    cannot make this guard silently match nothing and pass.
    """
    src = open(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "clawmetry", "cli.py"),
        encoding="utf-8",
    ).read()
    marker = "_dashboard_url = "
    i = src.index(marker)
    chunk = src[i:i + 600]
    # Keep only the quoted pieces, which is where the URL actually lives.
    parts = re.findall(r'f?"([^"]*)"', chunk)
    joined = "".join(parts)
    assert "/cloud" in joined, f"could not recover the hand-off URL from: {chunk[:200]}"
    return joined


def test_credentials_are_delivered_only_in_the_url_fragment():
    """Both secrets must sit after ``#``.

    A fragment is never transmitted. A refactor from ``#key=`` to ``&key=``,
    or from ``#token=`` back to ``?token=``, hands a live credential to the
    server, its access log and the browser's history — and would otherwise
    ship with a green suite. That is not hypothetical: the account key rode in
    the query string until 2026-08-24 and was measured landing in Cloud
    Logging about 180 times a day.
    """
    url = _dashboard_handoff_url()
    assert "#" in url, f"the hand-off URL has no fragment at all: {url}"
    before_fragment, fragment = url.split("#", 1)

    for secret in ("{enc_key}", "{api_key}"):
        assert secret in url, f"{secret} is no longer in the hand-off URL: {url}"
        assert secret not in before_fragment, (
            f"{secret} must sit after '#', never in the query or path: {url}"
        )
        assert secret in fragment


def test_handoff_url_has_no_query_string_at_all():
    """Nothing in the query string means nothing to leak or to audit later."""
    url = _dashboard_handoff_url()
    before_fragment = url.split("#", 1)[0]
    assert "?" not in before_fragment, (
        f"the hand-off URL grew a query string again: {url}"
    )


def test_browser_handoff_keeps_the_key_out_of_argv():
    src = open(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "clawmetry", "cli.py"),
        encoding="utf-8",
    ).read()
    assert "_open_url_without_argv(_dashboard_url)" in src
    assert "webbrowser.open(_dashboard_url)" not in src, (
        "webbrowser.open shells out; the URL (key fragment included) lands in argv"
    )


def test_fleet_installer_passes_the_key_by_env_not_argv():
    src = open(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "install.sh"),
        encoding="utf-8",
    ).read()
    live = [
        line for line in src.splitlines()
        if "--enc-key" in line and not line.lstrip().startswith("#")
    ]
    assert live == [], (
        "an argv key is readable via ps / /proc/<pid>/cmdline on host and pod: "
        f"{live}"
    )
    assert "CM_KEY=" in src


# ── Finding 7: the Claude rate-limit probe is opt-in and honest ──────────────


def test_claude_limit_probe_is_off_by_default(monkeypatch, tmp_path):
    monkeypatch.delenv("CLAWMETRY_CLAUDE_LIMIT_PROBE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert sync._claude_limit_probe_enabled() is False


def test_claude_limit_probe_does_not_impersonate_claude_code():
    src = open(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "clawmetry", "sync.py"),
        encoding="utf-8",
    ).read()
    assert '"claude-code/' not in src, (
        "sending another product's User-Agent to its own API is impersonation"
    )


# ── Wire audit 2026-09-03: the key never rides a query string ────────────────


def test_claim_watcher_sends_the_key_in_a_header_not_the_url():
    """The server logs the request line; a ``?token=cm_…`` query writes a
    whole account credential into its access logs on every daemon start.

    * AC-OBS-LADC-003.8 -- the account credential travels in a header, never the URL.
    """
    import inspect

    src = inspect.getsource(sync.start_claim_watcher)
    assert "token=" not in src, "claim watcher still puts the key in the URL"
    assert "api_key=token" in src


def test_cloud_get_json_puts_the_key_in_x_api_key(monkeypatch):
    seen = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"ok": true}'

    def _fake_urlopen(req, timeout=0):
        seen["url"] = req.full_url
        seen["headers"] = dict(req.header_items())
        return _Resp()

    import urllib.request as _ur

    monkeypatch.setattr(_ur, "urlopen", _fake_urlopen)
    out = sync._cloud_get_json("/api/cloud/account", api_key="cm_secret")
    assert out == {"ok": True}
    assert "cm_secret" not in seen["url"]
    assert seen["headers"].get("X-api-key") == "cm_secret"


def test_cli_status_lookup_has_no_token_in_the_url():
    path = os.path.join(os.path.dirname(sync.__file__), "cli.py")
    src = open(path, encoding="utf-8").read()
    assert "/api/cloud/account?token=" not in src


# ── Wire audit 2026-09-03: config files stay home ────────────────────────────


def test_memory_push_never_carries_runtime_config_files():
    """settings.json / openclaw.json / mcp.json are catalogued locally so the
    Memory tab can show hooks and servers, but they hold tokens. Sealed or
    not, they have no reason to leave the machine.

    * AC-OBS-LADC-003.9 -- runtime configuration files are never uploaded.
    """
    assert {"hooks", "mcp"} <= set(sync.MEMORY_PUSH_EXCLUDED_CATEGORIES)
    import inspect

    src = inspect.getsource(sync._build_memory_cache_pushes)
    assert "MEMORY_PUSH_EXCLUDED_CATEGORIES" in src


# ── Wire audit 2026-09-03: cloud-relayed actions are audited locally ────────


def test_every_relayed_action_is_written_to_the_local_audit_log(monkeypatch):
    """
    * AC-OBS-LADC-003.7 -- every relayed action is audited locally on arrival, body excluded.
    """
    calls = []
    from clawmetry import audit as _audit

    monkeypatch.setattr(_audit, "audit_event", lambda *a, **k: calls.append((a, k)))
    monkeypatch.delenv("CLAWMETRY_ALLOW_REMOTE_PROMPTS", raising=False)
    monkeypatch.setattr(sync, "_action_selfevolve_fix", lambda *a, **k: None)
    sync._dispatch_pending_action({}, {"type": "selfevolve_fix", "id": "x1"})
    assert calls and calls[0][0][0] == "remote_action.refused"
    assert calls[0][1]["target"] == "selfevolve_fix"
    # The action body (which may carry a server-supplied prompt) is not stored.
    assert "suggestion" not in json.dumps(calls[0][1].get("metadata") or {})
