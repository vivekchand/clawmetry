"""Muse Code wiring guards — the OSS half of the runtime.

The adapter itself lives in clawmetry-pro; what is asserted here is everything
OSS owns and everything that has historically gone wrong when a runtime lands:
the catalogue/loader pair, the pricing row, the MCP writer, and the control
verdict.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

RUNTIME = "muse_code"


# ── catalogue and loader ─────────────────────────────────────────────────────


def test_runtime_is_in_the_catalogue():
    from clawmetry.entitlements import ALL_RUNTIMES, PAID_RUNTIMES
    assert RUNTIME in PAID_RUNTIMES
    assert RUNTIME in ALL_RUNTIMES


def test_daemon_actually_loads_the_adapter():
    """The catalogue and the loader are independent lists and BOTH are
    required: 11 adapters once shipped in the wheel while absent from this
    tuple, so those runtimes were never ingested on a paying node and nothing
    anywhere raised."""
    text = (REPO / "clawmetry" / "sync.py").read_text(encoding="utf-8")
    assert '("clawmetry_pro.adapters.muse_code", "MuseCodeAdapter")' in text


def test_it_has_a_label_and_a_landing_path():
    from clawmetry.entitlements import RUNTIME_LABELS, RUNTIME_LANDING_PATHS
    assert RUNTIME_LABELS[RUNTIME] == "Muse Code"
    assert RUNTIME_LANDING_PATHS[RUNTIME] == "/runtimes/muse-code"


def test_session_prefix_is_registered_everywhere_it_is_read():
    """A session id arrives as "muse_code:<id>". Every module that splits that
    prefix keeps its own copy of the runtime set, and a missing entry silently
    mis-buckets the runtime rather than erroring."""
    for rel in ("clawmetry/local_store.py", "routes/usage.py",
                "routes/attention.py", "routes/harness.py"):
        text = (REPO / rel).read_text(encoding="utf-8")
        assert '"muse_code"' in text, f"{rel} does not know the muse_code prefix"


# ── the consumer product is deliberately NOT a runtime ───────────────────────

def test_the_consumer_muse_agent_is_not_claimed_as_a_runtime():
    """Meta ships two things called Muse. The personal agent runs wholly
    inside Meta's cloud VM with no API and no local footprint, so it cannot be
    observed and must never appear as a supported runtime; only the CLI can."""
    from clawmetry.entitlements import ALL_RUNTIMES
    assert "muse" not in ALL_RUNTIMES
    assert "muse_agent" not in ALL_RUNTIMES


# ── pricing ──────────────────────────────────────────────────────────────────


def test_muse_spark_is_priced_from_published_rates_not_the_unknown_default():
    """Before this runtime landed, every muse-spark model fell through to the
    (1.0, 3.0) unknown-provider default — the same dollars for every model,
    which is a guess wearing a number's clothes."""
    from clawmetry.providers_pricing import _get_rates
    assert _get_rates("meta", "muse-spark-1.3") == (1.25, 4.25)


def test_the_contributor_tier_is_priced_separately():
    """Contributor is 12.5x cheaper on input and ~21x on output. Pricing both
    tiers from one family rate misreports whichever tier the user is not on."""
    from clawmetry.providers_pricing import _get_rates
    assert _get_rates("meta", "muse-spark-1.3-contributor") == (0.10, 0.20)


def test_the_longer_variant_prefix_wins():
    """_get_rates picks the LONGEST matching prefix; if that ever regresses to
    first-match, the contributor id would silently price at the standard rate."""
    from clawmetry.providers_pricing import _get_rates
    standard = _get_rates("meta", "muse-spark-1.3")
    contributor = _get_rates("meta", "muse-spark-1.3-contributor")
    assert contributor != standard


def test_a_muse_model_resolves_to_the_meta_provider():
    from clawmetry.providers_pricing import provider_for_model
    assert provider_for_model("muse-spark-1.3") == "meta"


def test_muse_spark_is_not_priced_as_a_free_local_model():
    """The pricing path returns a legitimate 0.0 for self-hosted models. Muse
    Spark is a hosted paid API, so a $0 here would under-report real spend."""
    from clawmetry.providers_pricing import estimate_event_cost_usd
    cost = estimate_event_cost_usd("muse-spark-1.3", input_tokens=1_000_000,
                                   output_tokens=1_000_000)
    assert cost == pytest.approx(5.50)


# ── MCP registration ─────────────────────────────────────────────────────────


def test_muse_is_not_listed_as_having_no_mcp():
    """Muse Code speaks MCP (an mcp_servers block in its settings file), so
    claiming otherwise would be a false statement about the runtime."""
    from clawmetry.mcp_install import NO_MCP, SUPPORTED
    assert RUNTIME not in NO_MCP
    assert RUNTIME in SUPPORTED


def test_install_writes_muses_own_shape(tmp_path, monkeypatch):
    """Muse names the container `mcp_servers` and the stdio/http choice
    `transport`; the mcpServers/type spelling every other runtime uses would
    be silently ignored by Muse."""
    from clawmetry import mcp_install as mi

    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"schema_version": 1, "model": "muse-spark-1.3"}),
                        encoding="utf-8")
    inst = mi.Installer(marker_path=str(tmp_path / "marker.json"))
    monkeypatch.setattr(inst, "path_for", lambda rt: str(settings))

    result = inst.install(RUNTIME)
    assert result["status"] == mi.REGISTERED

    data = json.loads(settings.read_text(encoding="utf-8"))
    entry = data["mcp_servers"][mi.SERVER_NAME]
    assert entry["transport"] == "stdio"
    assert "type" not in entry
    assert "mcpServers" not in data
    # The user's own keys survive.
    assert data["model"] == "muse-spark-1.3"
    assert data["schema_version"] == 1


def test_creating_the_settings_file_seeds_schema_version(tmp_path, monkeypatch):
    """Muse's settings file must carry schema_version or the app FAILS AT
    STARTUP. Writing a bare {"mcp_servers": ...} into a machine that had no
    settings file would leave the user unable to launch Muse at all."""
    from clawmetry import mcp_install as mi

    settings = tmp_path / "settings.json"
    assert not settings.exists()
    inst = mi.Installer(marker_path=str(tmp_path / "marker.json"))
    monkeypatch.setattr(inst, "path_for", lambda rt: str(settings))

    assert inst.install(RUNTIME)["status"] == mi.REGISTERED
    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1


def test_uninstall_does_not_create_a_settings_file(tmp_path, monkeypatch):
    """Uninstall removes; it must never leave a config behind for a runtime
    the user just detached from."""
    from clawmetry import mcp_install as mi

    settings = tmp_path / "settings.json"
    inst = mi.Installer(marker_path=str(tmp_path / "marker.json"))
    monkeypatch.setattr(inst, "path_for", lambda rt: str(settings))

    inst.uninstall(RUNTIME)
    assert not settings.exists() or "schema_version" not in settings.read_text(encoding="utf-8")


def test_the_seed_is_not_merged_into_a_file_the_user_already_has(tmp_path, monkeypatch):
    """A settings file that exists but declares no schema_version is the
    user's, not ours to amend."""
    from clawmetry import mcp_install as mi

    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"model": "muse-spark-1.3"}), encoding="utf-8")
    inst = mi.Installer(marker_path=str(tmp_path / "marker.json"))
    monkeypatch.setattr(inst, "path_for", lambda rt: str(settings))

    inst.install(RUNTIME)
    assert "schema_version" not in json.loads(settings.read_text(encoding="utf-8"))


# ── control surface ──────────────────────────────────────────────────────────


def test_control_is_unknown_not_unsupported():
    """"unsupported" asserts no per-session process exists here, ever. Muse
    Code runs a real local process tree, so that claim would be false — but
    MSP reports no pid, so we cannot offer working buttons either. The honest
    third answer is "unknown", and the Guard tab must get it."""
    from clawmetry.process_control import runtime_control_support
    verdict = runtime_control_support(RUNTIME, "muse_code:abc")
    assert verdict["controllable"] is False
    assert verdict["actions"] == []
    assert verdict["state"] == "unknown"
    assert verdict["reason"]


def test_the_control_reason_says_why_rather_than_printing_a_code():
    from clawmetry.process_control import runtime_control_support
    reason = runtime_control_support(RUNTIME, "muse_code:abc")["reason"]
    assert "pid" in reason.lower()
    assert len(reason) > 40


def test_it_is_not_in_the_signalable_runtime_set():
    """Membership would light four buttons whose resolver has never been run
    against a real `muse` process."""
    from clawmetry.process_control import SUPPORTED_RUNTIMES, UNVERIFIED_RUNTIMES
    assert RUNTIME not in SUPPORTED_RUNTIMES
    assert RUNTIME in UNVERIFIED_RUNTIMES


def test_there_is_a_resume_hint_since_control_is_not_offered():
    """A session we cannot signal is exactly the case where the operator needs
    the resume command instead."""
    from clawmetry.resume_hints import known_runtimes, resume_hint
    assert RUNTIME in known_runtimes()
    hint = resume_hint(RUNTIME, "muse_code:abc-123")
    assert hint["kind"] == "command"
    assert hint["command"].startswith("muse ")
    # The store's prefixed id must not reach the printed command.
    assert "muse_code:" not in hint["command"]
    assert hint["note"] and hint["source"]


# ── declared records ─────────────────────────────────────────────────────────


def test_cost_is_declared_derived_not_recorded():
    """Muse writes no dollars anywhere, so a surface must say "derived" rather
    than present the figure as the vendor's."""
    from clawmetry.runtime_records import DERIVED, ON_DISK, RUNTIME_RECORDS
    rec = RUNTIME_RECORDS[RUNTIME]
    assert rec["tokens"] == ON_DISK
    assert rec["cost"] == DERIVED
    assert rec["model"] == ON_DISK


def test_the_note_names_the_counted_once_gap():
    """The one place our token figure is knowingly not MSP's best number."""
    from clawmetry.runtime_records import RUNTIME_RECORDS
    note = RUNTIME_RECORDS[RUNTIME]["note"]
    assert "counted-once" in note


def test_context_coverage_does_not_excuse_this_runtime():
    """Muse Code emits real compaction items, so a zero blowout count is a
    real zero here and must not be labelled "absence proves nothing"."""
    text = (REPO / "clawmetry" / "context_coverage.py").read_text(encoding="utf-8")
    assert "muse_code" not in text


def test_probe_looks_in_the_real_data_home_not_only_the_config_dir():
    """Verified against muse 1.0.3: the session store lives under
    ~/.local/share/muse (XDG, even on macOS), while ~/.config/muse holds only
    settings and credentials. Probing the config dir alone would miss the
    evidence that Muse actually ran."""
    from clawmetry.runtime_probe import RUNTIME_PROBES
    probe = next(p for p in RUNTIME_PROBES if p.id == RUNTIME)
    assert probe.paths[0] == "~/.local/share/muse/session-index.db"
    assert any(".config/muse" in path for path in probe.paths)
    # macOS uses XDG here, so an Application Support path would be wrong.
    assert not any("Application Support" in path for path in probe.paths)
    # The bare ~/.config/muse directory is created by a FAILED first launch,
    # so it is not evidence and must not be probed.
    assert not any(path.rstrip("/").endswith("/muse") for path in probe.paths)
