"""Issue #5716: a first-run screen must say WHERE ClawMetry looked.

Same failure class as #5534 (an unreadable store rendering as "you have no
data"), one layer earlier: at detection, before ingest. A person who installs
ClawMetry on a machine with no agent data saw a screen that could not
distinguish three very different situations:

  * no agent has ever run here;
  * an agent HAS run here and ClawMetry was refused access to its files
    (macOS Full Disk Access is the common one) -- the opposite conclusion,
    and the only one the person can actually fix;
  * the path could not even be resolved because its env var is unset.

All three collapsed into one `False`, because `RuntimeProbe.found()` answered
one bit and `probe_runtimes()` threw the rest away.

The trap this file exists to pin: `glob.glob` and `os.path.exists` BOTH
swallow PermissionError and answer ""/False. Checking those alone can never
detect a refused read, so the "we were blocked" message would be dead code
that no test would notice. `test_a_refused_directory_is_not_reported_absent`
runs against a real chmod-000 directory for exactly that reason.
"""
from __future__ import annotations

import os
import sys

import pytest

from clawmetry.runtime_probe import (
    RUNTIME_PROBES,
    RuntimeProbe,
    detection_report,
    probe_runtimes,
    render_detection_lines,
)


# ── where we looked ─────────────────────────────────────────────────────────


def test_probe_reports_the_paths_it_actually_checked(tmp_path):
    pr = RuntimeProbe("demo", "Demo", (str(tmp_path / "nope" / "*.json"),))
    info = pr.inspect()
    assert info["found"] is False
    paths = [e["path"] for e in info["checked"]]
    assert paths == [str(tmp_path / "nope" / "*.json")]


def test_paths_are_reported_expanded_not_as_written(monkeypatch, tmp_path):
    """A reader needs the path on THEIR machine, not the tilde form we ship."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(os.path, "expanduser",
                        lambda p: p.replace("~", str(tmp_path), 1))
    pr = RuntimeProbe("demo", "Demo", ("~/.demo/sessions",))
    entry = pr.inspect()["checked"][0]
    assert entry["path"] == str(tmp_path) + "/.demo/sessions"
    assert entry["pattern"] == "~/.demo/sessions"
    assert "~" not in entry["path"]


def test_every_shipped_runtime_can_say_where_it_looked():
    """Auto-discovering over the catalogue, so a runtime added later is
    covered without anyone remembering to extend this test."""
    for p in probe_runtimes():
        assert "checked" in p and isinstance(p["checked"], list)
        if not p["found"] and p["checked"]:
            assert any(e.get("path") for e in p["checked"]), p["id"]


def test_an_unresolved_env_path_is_not_presented_as_a_place_we_looked():
    """"$XDG_DATA_HOME/x" with the var unset is not a path anyone can check."""
    pr = RuntimeProbe("demo", "Demo", ("$CM_DEFINITELY_UNSET_VAR_5716/data",))
    entry = pr.inspect()["checked"][0]
    assert entry.get("unresolved_env") is True
    report = detection_report([{"id": "demo", "label": "Demo", "found": False,
                                "checked": [entry], "unreadable": []}])
    assert report["locations"] == [], "an unresolvable path must not be listed"


# ── what it needs: refused is not absent ────────────────────────────────────


@pytest.mark.skipif(sys.platform.startswith("win"),
                    reason="POSIX permission bits")
@pytest.mark.skipif(os.geteuid() == 0 if hasattr(os, "geteuid") else False,
                    reason="root reads everything, so nothing is refused")
def test_a_refused_directory_is_not_reported_absent(tmp_path):
    """The whole point, against a REAL chmod-000 directory.

    glob() returns [] and exists() returns False here, so a probe built on
    those alone would report "not found" for data that is present and simply
    unreadable, and would say so with total confidence.
    """
    locked = tmp_path / "locked"
    (locked / "inner").mkdir(parents=True)
    (locked / "inner" / "session.json").write_text("{}")
    locked.chmod(0o000)
    try:
        pr = RuntimeProbe("demo", "Demo", (str(locked / "inner" / "*.json"),))
        info = pr.inspect()
        assert info["found"] is False
        assert info["unreadable"], (
            "a refused read must be reported as refused, not as absent")
        reason = info["unreadable"][0]["unreadable"]
        assert reason and not reason.strip().isdigit(), reason
        assert "errno" not in reason.lower(), (
            "never show the user an upstream error code")
    finally:
        locked.chmod(0o755)


def test_the_plain_glob_check_alone_would_miss_it(tmp_path):
    """Pins the platform fact the implementation is built around, so nobody
    'simplifies' the readability probe back into a glob call."""
    import glob
    locked = tmp_path / "locked"
    (locked / "inner").mkdir(parents=True)
    (locked / "inner" / "s.json").write_text("{}")
    locked.chmod(0o000)
    try:
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            pytest.skip("root reads everything")
        assert glob.glob(str(locked / "inner" / "*.json")) == []
        assert os.path.exists(str(locked / "inner")) is False
    finally:
        locked.chmod(0o755)


# ── the report a screen renders ─────────────────────────────────────────────


def test_report_separates_found_blocked_and_looked_here():
    probes = [
        {"id": "a", "label": "A", "found": True, "checked": [], "unreadable": []},
        {"id": "b", "label": "B", "found": False,
         "checked": [{"path": "/x/b", "exists": False}], "unreadable": []},
        {"id": "c", "label": "C", "found": False,
         "checked": [{"path": "/x/c", "exists": None, "unreadable": "Denied."}],
         "unreadable": [{"path": "/x/c", "unreadable": "Denied."}]},
    ]
    r = detection_report(probes)
    assert r["found_count"] == 1 and r["found"][0]["id"] == "a"
    assert [b["runtime"] for b in r["blocked"]] == ["c"]
    assert [l["runtime"] for l in r["locations"]] == ["b", "c"]
    assert r["runtimes_checked"] == 3


def test_a_found_runtime_is_not_listed_as_somewhere_we_came_up_empty():
    r = detection_report([
        {"id": "a", "label": "A", "found": True,
         "checked": [{"path": "/x/a", "exists": True}], "unreadable": []},
    ])
    assert r["locations"] == []


def test_report_never_raises_on_junk():
    for junk in ([], [{}], [{"id": None}], [{"checked": None, "unreadable": None}]):
        detection_report(junk)


# ── the surfaces ────────────────────────────────────────────────────────────


def test_the_cli_wizard_is_no_longer_silent_on_an_empty_machine():
    probes = [{"id": "openclaw", "label": "OpenClaw", "free": True,
               "found": False, "checked": [{"path": "/h/.openclaw",
                                            "exists": False}],
               "unreadable": []}]
    out = "\n".join(render_detection_lines(probes))
    assert "/h/.openclaw" in out
    assert "Start an agent" in out


def test_the_endpoint_carries_the_report():
    from flask import Flask
    import routes.entitlement as ent

    app = Flask(__name__)
    app.register_blueprint(ent.bp_entitlement)
    with app.test_client() as c:
        body = c.get("/api/entitlement/runtime-detection").get_json()
    det = body.get("detection")
    assert isinstance(det, dict), "the first-run answer must be one round trip"
    for key in ("found", "found_count", "blocked", "locations", "runtimes_checked"):
        assert key in det, key
    assert det["runtimes_checked"] == len(RUNTIME_PROBES)
    for p in body["probes"]:
        assert "checked" in p and "unreadable" in p


def test_the_empty_envelope_still_answers_the_question():
    """The endpoint promises never to 5xx; its fallback must carry the key
    too, or a consumer reading `detection.blocked` throws on the bad day."""
    import routes.entitlement as ent
    det = ent._EMPTY_RUNTIME_DETECTION.get("detection")
    assert isinstance(det, dict)
    assert det["blocked"] == [] and det["locations"] == []


def test_both_first_run_screens_branch_instead_of_returning():
    """The two places that used to go silent when nothing was detected."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "clawmetry" / "static" / "js"
    onboarding = (root / "onboarding.js").read_text(encoding="utf-8")
    app_js = (root / "app.js").read_text(encoding="utf-8")
    assert "_fillNothingDetected" in onboarding
    assert "if (!found.length) { _fillNothingDetected(d); return; }" in onboarding
    assert "_invFillWhereWeLooked" in app_js
    assert "Where ClawMetry looked" in app_js
