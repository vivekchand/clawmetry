"""OpenExecutive wiring guards — the OSS half of the runtime.

The adapter itself lives in clawmetry-pro; what is asserted here is everything
OSS owns and everything that has historically gone wrong when a runtime lands:
the catalogue/loader pair, the session-prefix sets, the control verdict and
the declared record.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

RUNTIME = "openexecutive"


# ── catalogue and loader ─────────────────────────────────────────────────────


def test_runtime_is_in_the_catalogue():
    from clawmetry.entitlements import ALL_RUNTIMES, PAID_RUNTIMES
    assert RUNTIME in PAID_RUNTIMES
    assert RUNTIME in ALL_RUNTIMES


def test_daemon_actually_loads_the_adapter():
    """The catalogue and the loader are independent lists and BOTH are
    required: 11 adapters once shipped in the wheel while absent from this
    tuple, so those runtimes were never ingested on a paying node."""
    text = (REPO / "clawmetry" / "sync.py").read_text(encoding="utf-8")
    assert '("clawmetry_pro.adapters.openexecutive", "OpenExecutiveAdapter")' in text


def test_it_has_a_label_and_a_landing_path():
    from clawmetry.entitlements import RUNTIME_LABELS, RUNTIME_LANDING_PATHS
    assert RUNTIME_LABELS[RUNTIME] == "OpenExecutive"
    assert RUNTIME_LANDING_PATHS[RUNTIME] == "/runtimes/openexecutive"


def _js_object_keys(text: str, var: str) -> set[str]:
    m = re.search(r"var %s = \{(.*?)\};" % re.escape(var), text, re.S)
    assert m, f"{var} not found in app.js"
    return set(re.findall(r"([a-z_]+):", m.group(1)))


def test_session_prefix_is_registered_everywhere_it_is_read():
    """A session id arrives as "openexecutive:<id>". Every module that splits
    that prefix keeps its own copy of the runtime set, and a missing entry
    silently files the runtime's sessions under openclaw instead of erroring."""
    for rel in ("clawmetry/local_store.py", "routes/usage.py",
                "routes/attention.py", "routes/harness.py"):
        text = (REPO / rel).read_text(encoding="utf-8")
        assert f'"{RUNTIME}"' in text, f"{rel} does not know the {RUNTIME} prefix"


def test_the_newest_runtimes_are_in_the_backend_and_frontend_prefix_sets():
    """sync._RUNTIME_PREFIXES and app.js _CM_RT_PREFIXES are the two hand-kept
    mirrors of the closed prefix set. Muse Code landed in every other list but
    neither of these, so its sessions bucketed as openclaw in the runtime
    switcher; this pins both runtimes that were at risk."""
    import clawmetry.sync as sync
    js = (REPO / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    prefixes = _js_object_keys(js, "_CM_RT_PREFIXES")
    for rt in ("muse_code", RUNTIME):
        assert rt in sync._RUNTIME_PREFIXES, f"sync._RUNTIME_PREFIXES lacks {rt}"
        assert rt in prefixes, f"app.js _CM_RT_PREFIXES lacks {rt}"


def test_frontend_labels_name_it():
    js = (REPO / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    assert js.count("openexecutive: 'OpenExecutive'") == 2


# ── control surface ──────────────────────────────────────────────────────────


def test_control_is_unsupported_with_a_human_reason():
    """One API server serves every conversation, every channel and the
    scheduler. There is no per-conversation process, so the honest verdict is
    "unsupported", and the reason must say why in words rather than the generic
    "No signal support for openexecutive"."""
    from clawmetry.process_control import runtime_control_support
    verdict = runtime_control_support(RUNTIME, "openexecutive:abc")
    if verdict["state"] == "unsupported" and not verdict.get("platform", {}).get("controllable", True):
        return  # an OS with no signal primitive answers first, for every runtime
    assert verdict["controllable"] is False
    assert verdict["actions"] == []
    assert verdict["state"] == "unsupported"
    assert "No signal support" not in verdict["reason"]
    assert "every conversation" in verdict["reason"]


def test_it_is_never_in_the_signalable_sets():
    """Membership would light buttons that signal the whole server."""
    from clawmetry.process_control import (SHARED_PROCESS_RUNTIMES,
                                           SUPPORTED_RUNTIMES, UNVERIFIED_RUNTIMES)
    assert RUNTIME not in SUPPORTED_RUNTIMES
    assert RUNTIME not in UNVERIFIED_RUNTIMES
    assert RUNTIME in SHARED_PROCESS_RUNTIMES


def test_there_is_a_reopen_hint_since_control_is_not_offered():
    from clawmetry.resume_hints import known_runtimes, resume_hint
    assert RUNTIME in known_runtimes()
    hint = resume_hint(RUNTIME, "openexecutive:abc-123")
    assert hint["command"] == ""
    assert "web UI" in hint["note"]


# ── declared records ─────────────────────────────────────────────────────────


def test_cost_is_declared_partial_not_on_disk():
    """Specialist agents write no usage row, so tokens and cost are a floor.
    Declaring them complete would present an undercount as the full bill."""
    from clawmetry.runtime_records import ON_DISK, PARTIAL, RUNTIME_RECORDS
    rec = RUNTIME_RECORDS[RUNTIME]
    assert rec["tokens"] == PARTIAL
    assert rec["cost"] == PARTIAL
    assert rec["model"] == ON_DISK
    assert "floor" in rec["note"]


def test_probe_looks_where_make_dev_and_docker_write_the_store():
    from clawmetry.runtime_probe import RUNTIME_PROBES
    probe = next(p for p in RUNTIME_PROBES if p.id == RUNTIME)
    assert probe.env == "CLAWMETRY_OPENEXECUTIVE_DB"
    assert any(p.endswith("packages/core/episodic_memory.db") for p in probe.paths)
    assert "/data/episodic_memory.db" in probe.paths


def test_context_coverage_does_not_report_a_clean_zero():
    """OpenExecutive drops old turns from its short-term window without
    recording it, so zero compactions is absence of evidence."""
    from clawmetry.context_coverage import UNSUPPORTED_COMPACTION
    assert RUNTIME in UNSUPPORTED_COMPACTION
