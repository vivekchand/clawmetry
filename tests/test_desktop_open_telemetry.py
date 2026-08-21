"""Desktop open telemetry — the download → open → working-daemon funnel.

A .dmg download told us nothing about whether anyone ever opened the app.
Two pings close that gap, and each stage exists because the other cannot
cover it:

  shell  (desktop/app.py)        fires when the window appears, so it
                                 reports opens whose Python bootstrap
                                 never completes — the failure mode we
                                 were structurally blind to.
  daemon (clawmetry/telemetry.py) fires once the dashboard is live, and
                                 is the only stage that can say which
                                 runtimes the machine has data for and
                                 whether it syncs to cloud or stays local.

Both are opt-out, both are silent on enterprise endpoints, and neither may
ever slow, block, or visibly break a launch. The tests below hold those
properties: nothing here touches the network or the real ~/.clawmetry.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import desktop.app as dapp  # noqa: E402


# ── Shell stage ─────────────────────────────────────────────────────────────


@pytest.fixture
def shell(monkeypatch, tmp_path):
    """desktop.app with its ~/.clawmetry paths redirected at a tmp dir."""
    cfg_dir = tmp_path / ".clawmetry"
    monkeypatch.setattr(dapp, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(dapp, "INSTALL_ID_FILE", cfg_dir / "install_id")
    monkeypatch.setattr(dapp, "OPTOUT_MARKER", cfg_dir / "notelemetry")
    monkeypatch.setattr(dapp, "NOCLOUD_MARKER", cfg_dir / "nocloud")
    monkeypatch.setattr(dapp, "CONFIG_JSON", cfg_dir / "config.json")
    monkeypatch.setattr(dapp, "OPEN_STATE_FILE", cfg_dir / "desktop-opens.json")
    for k in ("CLAWMETRY_NO_TELEMETRY", "DO_NOT_TRACK", "CLAWMETRY_ENDPOINT",
              "CLAWMETRY_INGEST_URL", "CLAWMETRY_DESKTOP_PING_URL"):
        monkeypatch.delenv(k, raising=False)
    return dapp


def _write_cfg(shell_mod, **keys):
    shell_mod.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    shell_mod.CONFIG_JSON.write_text(json.dumps(keys), encoding="utf-8")


def test_open_counter_survives_relaunch(shell):
    """The nth-open number comes off disk, not the server, so opens that
    happen offline still show up in the count on the next ping."""
    first = shell._bump_open_state("s1")
    second = shell._bump_open_state("s2")
    third = shell._bump_open_state("s3")
    assert [first["open_count"], second["open_count"], third["open_count"]] == [1, 2, 3]
    # first_open_ts is pinned at the first launch — it dates the install.
    assert third["first_open_ts"] == pytest.approx(first["first_open_ts"])
    on_disk = json.loads(shell.OPEN_STATE_FILE.read_text())
    assert on_disk["open_count"] == 3


def test_first_open_flagged_then_not(shell, monkeypatch):
    sent = []
    monkeypatch.setattr(shell, "_post_open_ping",
                        lambda payload, base, key: sent.append((payload, base, key)))
    monkeypatch.setattr(shell.threading, "Thread",
                        lambda target, args, daemon, name: type(
                            "T", (), {"start": lambda _self: target(*args)})())
    shell.open_ping_state("s1")
    shell.open_ping_state("s2")
    assert [p["first_open"] for p, _, _ in sent] == [True, False]
    assert [p["open_count"] for p, _, _ in sent] == [1, 2]
    assert sent[0][0]["event"] == "desktop_open"
    assert sent[0][0]["stage"] == "shell"


def test_optout_still_counts_locally_but_never_posts(shell, monkeypatch):
    """Opting out silences the network, not the local counter — the user's
    own 'nth open' bookkeeping stays correct if they later opt back in."""
    posted = []
    monkeypatch.setattr(shell, "_post_open_ping",
                        lambda *a, **k: posted.append(a))
    monkeypatch.setenv("CLAWMETRY_NO_TELEMETRY", "1")
    state = shell.open_ping_state("s1")
    assert state["open_count"] == 1
    assert posted == []


def test_optout_marker_file_also_silences(shell, monkeypatch):
    posted = []
    monkeypatch.setattr(shell, "_post_open_ping", lambda *a, **k: posted.append(a))
    shell.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    shell.OPTOUT_MARKER.write_text("")
    shell.open_ping_state("s1")
    assert posted == []


def test_enterprise_endpoint_never_phones_the_managed_cloud(shell, monkeypatch):
    """A self-hosted deployment's data stays inside the deployment: we skip
    the ping rather than redirect it at someone's private server."""
    monkeypatch.setenv("CLAWMETRY_ENDPOINT", "https://clawmetry.internal.acme")
    assert shell._app_base({}) is None
    assert shell._app_base({"endpoint": "https://x.internal"}) is None
    monkeypatch.delenv("CLAWMETRY_ENDPOINT")
    assert shell._app_base({}) == shell.DEFAULT_APP_BASE


def test_shell_sync_mode(shell):
    assert shell._sync_mode({}) == "unknown"
    assert shell._sync_mode({"api_key": "cm_live_x"}) == "cloud"
    assert shell._sync_mode({"api_key": "cm_live_x", "local_only": True}) == "local"
    shell.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    shell.NOCLOUD_MARKER.write_text("")
    assert shell._sync_mode({"api_key": "cm_live_x"}) == "local"


def test_attached_window_is_marked(shell, monkeypatch):
    """A second window joins the first instance's daemon and never spawns
    one. Unmarked, it would read as an open whose daemon never came up."""
    sent = []
    monkeypatch.setattr(shell, "_post_open_ping",
                        lambda payload, base, key: sent.append(payload))
    monkeypatch.setattr(shell.threading, "Thread",
                        lambda target, args, daemon, name: type(
                            "T", (), {"start": lambda _self: target(*args)})())
    shell.open_ping_state("s1", attached=True)
    assert sent[0]["attached"] is True


def test_install_id_is_shared_with_the_cli(shell):
    """One machine is one install — the shell reuses the CLI's id file
    rather than minting a second identity for the same person."""
    first = shell._install_id()
    assert first and shell.INSTALL_ID_FILE.exists()
    assert shell._install_id() == first


def test_key_is_sent_as_a_header_only_when_paired(shell, monkeypatch):
    seen = {}

    class _Resp:
        def read(self): return b""
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def _urlopen(req, timeout=None, context=None):
        seen["headers"] = dict(req.headers)
        seen["url"] = req.full_url
        return _Resp()

    monkeypatch.setattr(shell.urllib.request, "urlopen", _urlopen)
    shell._post_open_ping({"desktop_version": "1"}, "https://app.example", "")
    assert "Authorization" not in seen["headers"]
    assert seen["url"].endswith("/api/desktop/open")
    shell._post_open_ping({"desktop_version": "1"}, "https://app.example", "cm_live_k")
    assert seen["headers"]["Authorization"] == "Bearer cm_live_k"


def test_network_failure_is_invisible(shell, monkeypatch):
    def _boom(*a, **k):
        raise OSError("network down")

    monkeypatch.setattr(shell.urllib.request, "urlopen", _boom)
    shell._post_open_ping({}, "https://app.example", "")  # must not raise


def test_version_is_dev_without_a_build_stamp(shell, monkeypatch, tmp_path):
    monkeypatch.setattr(shell, "_assets_dir", lambda: tmp_path / "nope")
    assert shell._desktop_version() == "dev"
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "version.txt").write_text("0.12.999\n")
    monkeypatch.setattr(shell, "_assets_dir", lambda: assets)
    assert shell._desktop_version() == "0.12.999"


# ── Daemon stage ────────────────────────────────────────────────────────────


@pytest.fixture
def tele(monkeypatch, tmp_path):
    from clawmetry import telemetry as t
    importlib.reload(t)
    cfg_dir = tmp_path / ".clawmetry"
    monkeypatch.setattr(t, "CONFIG_DIR", cfg_dir)
    monkeypatch.setattr(t, "INSTALL_ID_FILE", cfg_dir / "install_id")
    monkeypatch.setattr(t, "OPTOUT_MARKER", cfg_dir / "notelemetry")
    monkeypatch.setattr(t, "STATE_FILE", cfg_dir / "telemetry_state.json")
    monkeypatch.setattr(t, "CONFIG_JSON", cfg_dir / "config.json")
    monkeypatch.setattr(t, "NOCLOUD_MARKER", cfg_dir / "nocloud")
    monkeypatch.setattr(t, "DESKTOP_PING_DELAY_SEC", 0.0)
    for k in ("CLAWMETRY_NO_TELEMETRY", "DO_NOT_TRACK", "CLAWMETRY_LAUNCHER",
              "CLAWMETRY_ENDPOINT", "CLAWMETRY_INGEST_URL",
              "CLAWMETRY_DESKTOP_PING_URL", "CLAWMETRY_DESKTOP_SESSION",
              "CLAWMETRY_DESKTOP_VERSION", "CLAWMETRY_DESKTOP_OPEN_COUNT"):
        monkeypatch.delenv(k, raising=False)
    return t


def test_pip_installs_never_send_the_desktop_ping(tele):
    """The daemon stage is desktop-only. A plain `clawmetry` run must not
    start a thread, let alone post."""
    assert tele.maybe_desktop_ping("0.0.0") is None


def test_desktop_launcher_fires(tele, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LAUNCHER", "desktop")
    posted = []
    monkeypatch.setattr(tele, "_post",
                        lambda payload, url, api_key="": posted.append((payload, url, api_key)))
    monkeypatch.setattr(tele, "_monitored_runtimes", lambda: ["openclaw", "claude_code"])
    t = tele.maybe_desktop_ping("0.12.900")
    assert t is not None
    t.join(timeout=5)
    payload, url, api_key = posted[0]
    assert payload["event"] == "desktop_ready"
    assert payload["stage"] == "daemon"
    assert payload["runtimes"] == ["openclaw", "claude_code"]
    assert payload["runtime_count"] == 2
    assert payload["version"] == "0.12.900"
    assert url.endswith("/api/desktop/open")
    assert api_key == ""


def test_daemon_ping_carries_the_shell_session_and_count(tele, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LAUNCHER", "desktop")
    monkeypatch.setenv("CLAWMETRY_DESKTOP_SESSION", "sess-42")
    monkeypatch.setenv("CLAWMETRY_DESKTOP_OPEN_COUNT", "7")
    monkeypatch.setenv("CLAWMETRY_DESKTOP_VERSION", "0.12.901")
    monkeypatch.setattr(tele, "_monitored_runtimes", lambda: [])
    payload = tele._build_desktop_payload("0.12.900")
    assert payload["session_id"] == "sess-42"
    assert payload["open_count"] == 7
    assert payload["first_open"] is False
    assert payload["desktop_version"] == "0.12.901"


def test_garbage_open_count_does_not_raise(tele, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_DESKTOP_OPEN_COUNT", "not-a-number")
    monkeypatch.setattr(tele, "_monitored_runtimes", lambda: [])
    assert tele._build_desktop_payload("0.0.0")["open_count"] == 0


def test_daemon_optout_beats_the_launcher(tele, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LAUNCHER", "desktop")
    monkeypatch.setenv("DO_NOT_TRACK", "1")
    assert tele.maybe_desktop_ping("0.0.0") is None


def test_daemon_skips_enterprise_endpoints(tele, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LAUNCHER", "desktop")
    monkeypatch.setenv("CLAWMETRY_ENDPOINT", "https://clawmetry.internal.acme")
    posted = []
    monkeypatch.setattr(tele, "_post", lambda *a, **k: posted.append(a))
    monkeypatch.setattr(tele, "_monitored_runtimes", lambda: [])
    tele._send_desktop_ping("0.0.0")
    assert posted == []


def test_paired_install_attributes_to_its_account(tele, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LAUNCHER", "desktop")
    tele.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tele.CONFIG_JSON.write_text(json.dumps({"api_key": "cm_live_abc", "node_id": "n1"}))
    posted = []
    monkeypatch.setattr(tele, "_post",
                        lambda payload, url, api_key="": posted.append((payload, api_key)))
    monkeypatch.setattr(tele, "_monitored_runtimes", lambda: [])
    tele._send_desktop_ping("0.0.0")
    payload, api_key = posted[0]
    assert api_key == "cm_live_abc"
    assert payload["mode"] == "cloud"
    assert payload["node_id"] == "n1"
    # The key is a header, never part of the stored body.
    assert "api_key" not in payload


def test_daemon_sync_mode_local(tele):
    tele.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tele.NOCLOUD_MARKER.write_text("")
    assert tele._sync_mode({"api_key": "cm_live_abc"}) == "local"


def test_monitored_runtimes_are_ids_only(tele, monkeypatch):
    monkeypatch.setattr(tele, "_AGENT_DIRS", ())
    import clawmetry.sync as sync
    monkeypatch.setattr(sync, "_detect_runtimes_lite",
                        lambda: [{"id": "claude_code", "label": "Claude Code", "sessions": 91},
                                 {"id": "cursor", "label": "Cursor", "sessions": 0}])
    assert tele._monitored_runtimes() == ["claude_code", "cursor"]


def test_runtime_detection_failure_is_not_fatal(tele, monkeypatch):
    monkeypatch.setattr(tele, "_AGENT_DIRS", ())
    import clawmetry.sync as sync

    def _boom():
        raise RuntimeError("detection exploded")

    monkeypatch.setattr(sync, "_detect_runtimes_lite", _boom)
    assert tele._monitored_runtimes() == []


# ── TLS trust (the 2026-08-12 class) ────────────────────────────────────────
#
# A frozen bundle has no OpenSSL trust store at the paths the default
# context looks in, so every HTTPS call from inside the .app/.exe fails
# with CERTIFICATE_VERIFY_FAILED. That took out the onboarding "Send
# code" button once already. Both pings swallow errors by design, so the
# same mistake here does not surface as a bug report: it surfaces as an
# endpoint that quietly receives nothing, from precisely the installs it
# exists to hear about. These guards fail if either ping ever goes back
# to an unverified default context.


def _capture_urlopen(monkeypatch, mod):
    seen = {}

    class _Resp:
        def read(self): return b""
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def _urlopen(req, timeout=None, context=None, **kw):
        seen["context"] = context
        seen["url"] = getattr(req, "full_url", req)
        return _Resp()

    monkeypatch.setattr(mod.urllib.request, "urlopen", _urlopen)
    return seen


def test_shell_ping_verifies_certificates(shell, monkeypatch):
    import ssl

    seen = _capture_urlopen(monkeypatch, shell)
    shell._post_open_ping({"desktop_version": "1"}, "https://app.clawmetry.com", "")
    assert isinstance(seen["context"], ssl.SSLContext), (
        "the shell ping must pass a verifying SSL context; the frozen bundle "
        "cannot verify public certs with the default one"
    )


def test_shell_ping_skips_the_context_for_plain_http(shell, monkeypatch):
    """A local sink over http has no certificates to verify, and handing
    a context to a plain-http request is meaningless."""
    seen = _capture_urlopen(monkeypatch, shell)
    shell._post_open_ping({"desktop_version": "1"}, "http://127.0.0.1:8977", "")
    assert seen["context"] is None


def test_daemon_ping_verifies_certificates(tele, monkeypatch):
    import ssl

    seen = _capture_urlopen(monkeypatch, tele)
    tele._post({"version": "1"}, "https://app.clawmetry.com/api/desktop/open")
    assert isinstance(seen["context"], ssl.SSLContext)


def test_daemon_ping_skips_the_context_for_plain_http(tele, monkeypatch):
    seen = _capture_urlopen(monkeypatch, tele)
    tele._post({"version": "1"}, "http://127.0.0.1:8977/api/desktop/open")
    assert seen["context"] is None


def test_trust_ladder_never_raises(tele, monkeypatch):
    """Every rung is best-effort: a missing truststore/certifi must
    degrade to the default context, not take the ping down with it."""
    import builtins
    import ssl

    real_import = builtins.__import__

    def _no_tls_libs(name, *a, **kw):
        if name in ("truststore", "certifi"):
            raise ImportError(name)
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", _no_tls_libs)
    monkeypatch.setattr(tele, "_SSL_CTX", None)
    assert isinstance(tele._ssl_context(), ssl.SSLContext)


# ── The trust store must exist on every install ─────────────────────────────
#
# The ladder is only as good as what is installed alongside it. truststore
# cannot install below 3.10, so on 3.8/3.9 certifi is the ONLY rung that
# works, and without it the ladder falls through to a default context that
# has no CA bundle at all on interpreters whose certificate step was never
# run. That is a silent failure by construction: the pings swallow their
# errors, so it surfaces as an endpoint that never hears from those
# machines rather than as anything anybody could report.


def _install_requires():
    """Read setup.py's install_requires without importing it (importing
    runs setup())."""
    import ast

    tree = ast.parse(Path(REPO_ROOT / "setup.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "install_requires":
            return [ast.literal_eval(e) for e in node.value.elts]
    raise AssertionError("install_requires not found in setup.py")


def test_certifi_is_an_unconditional_dependency():
    """Ungated on purpose: 3.8/3.9 cannot have truststore, and those are
    exactly the interpreters most likely to lack a CA bundle."""
    reqs = _install_requires()
    certifi_reqs = [r for r in reqs if r.split(">=")[0].split(";")[0].strip() == "certifi"]
    assert certifi_reqs, f"certifi must be in install_requires; got {reqs}"
    assert ";" not in certifi_reqs[0], (
        f"certifi must NOT carry a version marker ({certifi_reqs[0]}) -- gating it "
        "would leave 3.8/3.9 with no usable trust store at all"
    )


def test_truststore_stays_gated_at_310():
    """It cannot install below 3.10, so the marker has to stay or the
    whole package becomes uninstallable on 3.9."""
    reqs = _install_requires()
    ts = [r for r in reqs if r.startswith("truststore")]
    assert ts and 'python_version >= "3.10"' in ts[0], ts


def test_ladder_finds_real_cas_when_truststore_is_unavailable(tele, monkeypatch):
    """The 3.8/3.9 path, exercised on whatever Python runs the suite: with
    truststore blocked, the context must still carry actual CA
    certificates. An empty store is what CERTIFICATE_VERIFY_FAILED looks
    like before it happens."""
    import builtins

    real_import = builtins.__import__

    def _no_truststore(name, *a, **kw):
        if name == "truststore":
            raise ImportError("simulating a 3.9 interpreter")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", _no_truststore)
    monkeypatch.setattr(tele, "_SSL_CTX", None)
    ctx = tele._ssl_context()
    assert len(ctx.get_ca_certs()) > 0, (
        "no CA certificates loaded -- every HTTPS call from this install "
        "would fail with CERTIFICATE_VERIFY_FAILED, silently"
    )
