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


def test_key_is_delivered_only_in_the_url_fragment():
    """A refactor from ``#key=`` to ``&key=`` would hand the key to the server
    with no test failing — this is that test."""
    src = open(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "clawmetry", "cli.py"),
        encoding="utf-8",
    ).read()
    urls = [
        line for line in src.splitlines()
        if "{enc_key}" in line and "/cloud" in line
    ]
    assert urls, "expected the dashboard hand-off URL to be present"
    for line in urls:
        before_fragment = line.split("#")[0]
        assert "{enc_key}" not in before_fragment, (
            f"the encryption key must sit after '#', never in the query or path: {line}"
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
