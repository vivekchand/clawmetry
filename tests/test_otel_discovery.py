"""Find apps already emitting OpenTelemetry, without lying about what we saw (#4784).

Runtime detection is filesystem-shaped, so the LangChain service two terminal
windows over is invisible until someone points it at us. This finds it, and
the interesting part is not the finding, it is the honesty around it.

Three platform facts were MEASURED rather than assumed, and each changed the
design away from the issue's own plan:

1. **macOS does not block same-user process environs.** The issue expected it
   to, and specified a macOS-wide degraded path. On macOS 26 with psutil
   7.2.2 a same-user child's environ reads fine (699 readable / 39 blocked of
   this machine's processes). Shipping the planned degradation would have
   told macOS users about a limitation they do not have. What actually
   degrades is psutil being absent, since it is not in ``install_requires``.

2. **A port probe cannot identify who is listening, and cannot be made to.**
   ``psutil.net_connections()`` raises ``AccessDenied`` on macOS without
   root, and requiring root to render a suggestion is not a trade this
   product makes. So a port finding says something listens, never who.

3. **ClawMetry itself listens on 4318** (``instrument._COMPAT_PORT``).
   Measured live: the naive probe reported "a collector is running, send us a
   copy" pointing at our own receiver. A port we may own is never offered a
   redirect.

Read-only throughout (ADR-005): nothing here edits another application's
environment, config or files.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import otel_discovery as od  # noqa: E402


# ── port probing ────────────────────────────────────────────────────────────


def test_a_dead_port_is_not_reported(monkeypatch):
    monkeypatch.setattr(od, "_port_is_listening", lambda *a, **k: False)
    assert od.probe_collector_ports() == []


def test_a_live_port_is_reported_but_never_claims_to_know_who(monkeypatch):
    """The honesty that root-less port probing forces."""
    monkeypatch.setattr(od, "_port_is_listening", lambda *a, **k: True)
    monkeypatch.setattr(od, "_own_receiver_port", lambda: None)
    apps = od.probe_collector_ports()
    assert apps, "a listening port must be reported"
    for a in apps:
        assert a["evidence"] == "port_probe"
        assert a["identified"] is False, "a port probe identifies nothing"
        assert "something listening" in a["name"]


def test_our_own_receiver_is_recognised_and_never_offered_a_redirect(monkeypatch):
    """The live false positive: ClawMetry binds 4318, so a naive probe says
    'a collector is running, send us a copy' about ClawMetry."""
    monkeypatch.setattr(od, "_port_is_listening", lambda *a, **k: True)
    monkeypatch.setattr(od, "_own_receiver_port", lambda: 4318)
    monkeypatch.setattr(od, "scan_process_env", lambda: ([], None))
    r = od.discover_otel_emitters()
    mine = [a for a in r["apps"] if a["endpoint"].endswith(":4318")]
    assert mine and mine[0]["is_clawmetry_receiver"] is True
    assert "ClawMetry" in mine[0]["name"]
    assert all(not a["is_clawmetry_receiver"] for a in r["suggestable"])
    assert not any(a["endpoint"].endswith(":4318") for a in r["suggestable"])


def test_the_port_probe_only_touches_loopback():
    """A discovery feature must never become a scan of anything remote."""
    import inspect
    src = inspect.getsource(od._port_is_listening)
    assert "127.0.0.1" in src and "::1" in src
    assert "0.0.0.0" not in src


def test_the_probed_port_list_stays_short():
    """Two conventional ports is a probe. Twenty is a port scan of the user's
    own machine."""
    assert len(od.COLLECTOR_PORTS) <= 4


# ── process env scan ────────────────────────────────────────────────────────


@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX spawn")
def test_names_a_real_app_and_the_endpoint_it_currently_uses():
    """Acceptance case 2, against a REAL process, not a mock."""
    pytest.importorskip("psutil")
    env = dict(os.environ,
               OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:9999",
               OTEL_SERVICE_NAME="cm-test-langchain-app")
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"],
                             env=env)
    try:
        found = None
        for _ in range(20):
            apps, reason = od.scan_process_env()
            found = next((a for a in apps
                          if a.get("service_name") == "cm-test-langchain-app"), None)
            if found:
                break
            time.sleep(0.25)
        assert found, "a same-user OTLP-exporting process must be found"
        assert found["endpoint"] == "http://localhost:9999"
        assert found["evidence"] == "process_env"
        assert found["identified"] is True
        assert found["name"] == "cm-test-langchain-app", (
            "the app's own name beats the process name, which is often "
            "just 'Python'")
    finally:
        child.terminate()


def test_a_per_signal_endpoint_wins_over_the_general_one():
    """An exporter reads the specific variable first, so reporting the
    general one would name an endpoint the app is not using."""
    assert od._ENDPOINT_VARS[0].endswith("TRACES_ENDPOINT")
    assert od._ENDPOINT_VARS[-1] == "OTEL_EXPORTER_OTLP_ENDPOINT"


def test_another_users_process_is_filtered_by_ownership_not_by_exception():
    """Measured why this matters: psutil.Process(0).environ() on macOS
    returns {} and raises NOTHING, so an implementation that waits for
    AccessDenied has no cross-user boundary at all."""
    import inspect
    src = inspect.getsource(od.scan_process_env)
    assert "owner != me" in src, "ownership must be compared explicitly"


def test_no_psutil_degrades_with_a_reason_a_person_can_act_on(monkeypatch):
    """And the reason names psutil, NOT the operating system."""
    import builtins
    real = builtins.__import__

    def _no_psutil(name, *a, **k):
        if name == "psutil":
            raise ImportError("no psutil")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", _no_psutil)
    apps, reason = od.scan_process_env()
    assert apps == []
    assert reason and "psutil" in reason
    for os_word in ("macOS", "Mac", "Darwin", "Windows"):
        assert os_word not in reason, (
            "the limitation is a missing package, not the platform: macOS "
            "same-user environ reads were measured working")


def test_discovery_reports_degradation_up_to_the_caller(monkeypatch):
    monkeypatch.setattr(od, "scan_process_env",
                        lambda: ([], "Cannot list processes: psutil is not installed."))
    monkeypatch.setattr(od, "probe_collector_ports", lambda: [])
    r = od.discover_otel_emitters()
    assert r["degraded"] is True and "psutil" in r["degraded_reason"]
    assert r["apps"] == []


# ── contract ────────────────────────────────────────────────────────────────


def test_discovery_never_raises(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(od, "probe_collector_ports", boom)
    monkeypatch.setattr(od, "scan_process_env", boom)
    r = od.discover_otel_emitters()
    assert r["apps"] == [] and r["degraded"] is True


def test_the_instruction_is_a_suggestion_never_an_edit():
    """ADR-005: we detect and suggest; the person applies."""
    line = od.redirect_instruction("http://localhost:8900")
    assert line.startswith("OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900")
    import inspect
    src = inspect.getsource(od)
    for forbidden in ("os.environ[", "subprocess.run", "shutil.copy", "open("):
        assert forbidden not in src, (
            f"discovery must never write anything ({forbidden})")


def test_the_discovery_has_a_reader_from_the_first_commit():
    """A snapshot slice nothing renders is the shape that left
    /api/run-ledger with zero UI consumers (#5721). Discovery ships with a
    surface: `clawmetry diagnose`."""
    import inspect
    from clawmetry import cli as _cli

    assert hasattr(_cli, "_diagnose_otel_emitters")
    assert "_diagnose_otel_emitters()" in inspect.getsource(_cli._cmd_diagnose), (
        "the surface exists but nothing calls it"
    )
    src = inspect.getsource(_cli._diagnose_otel_emitters)
    assert "never edits" in src, "the read-only promise must be on screen"


# ── the snapshot slice and the prompt (#4784, second half) ──────────────────


def test_the_snapshot_slice_is_built_and_never_raises(monkeypatch):
    import clawmetry.sync as sync

    slice_ = sync._build_detected_otel_apps()
    for key in ("apps", "suggestable", "degraded", "degradedReason",
                "checkedPorts", "instruction", "scannedAtMs"):
        assert key in slice_, key

    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(od, "discover_otel_emitters", boom)
    degraded = sync._build_detected_otel_apps()
    assert degraded["apps"] == [] and degraded["suggestable"] == []


def test_the_slice_is_in_the_encrypted_snapshot_not_the_heartbeat():
    """An OTEL_SERVICE_NAME is the user's own name for their own service
    ("acme-billing-prod"). It is theirs to see and not ours to hold in the
    clear, so it rides the AES-encrypted snapshot like session content."""
    import inspect
    import clawmetry.sync as sync

    src = inspect.getsource(sync)
    i = src.find('"detectedOtelApps"')
    assert i > 0, "the slice must be in the snapshot payload"
    # The snapshot builder, not _build_heartbeat / the plaintext path.
    window = src[max(0, i - 4000):i]
    assert '"securityPosture"' in window, (
        "detectedOtelApps must sit in the same encrypted snapshot dict as "
        "securityPosture, which documents the encrypted-only rule"
    )


def test_the_overview_payload_carries_the_slice_too():
    """The bug the browser caught, not the tests.

    The slice was built into the cloud SNAPSHOT only, and the first-run panel
    reads `/api/overview`. On a local dashboard the prompt therefore never
    rendered: it would have appeared on the hosted dashboard and nowhere
    else. Both payloads carry it now.
    """
    import inspect
    import routes.overview as ov

    src = inspect.getsource(ov)
    assert '"detectedOtelApps"' in src, "the local overview must serve it"
    assert hasattr(ov, "_detected_otel_apps_cached")
    cached = inspect.getsource(ov._detected_otel_apps_cached)
    assert "monotonic" in cached, (
        "discovery costs ~86 ms; /api/overview is polled every few seconds, "
        "so it must be memoised rather than run per request"
    )


def test_the_prompt_reads_suggestable_never_apps():
    """`apps` can include a port ClawMetry itself holds (it binds 4318).
    Telling someone to redirect their app to ClawMetry, from ClawMetry, is
    worse than saying nothing."""
    from pathlib import Path
    app_js = (Path(__file__).resolve().parents[1] / "clawmetry" / "static"
              / "js" / "app.js").read_text(encoding="utf-8")
    i = app_js.find("detectedOtelApps")
    assert i > 0, "the first-run panel must read the slice"
    block = app_js[i:i + 1800]
    assert "otel.suggestable" in block
    assert "otel.apps" not in block, "the prompt must not render self-detections"
    assert "never changes another application" in block, (
        "the read-only promise belongs on screen next to the instruction")


def test_a_pass_is_cheap_enough_for_the_snapshot_timer():
    """FLYWHEEL 1e: the daemon budget. Measured at 86 ms of CPU per pass on
    the dev machine, 0.14% of one core on a 60s timer."""
    t0 = time.perf_counter()
    od.discover_otel_emitters()
    assert (time.perf_counter() - t0) < 5.0, "a discovery pass must stay cheap"
