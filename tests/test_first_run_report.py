"""The first-run report has to be able to say WHERE it looked (#5716).

A dashboard showing nothing is indistinguishable from a broken install. The
panel that fixes that is only as good as the data behind it, so this pins the
part that can silently rot: the probe must expose the paths it actually
checked, and the detection endpoint must pass them through (it whitelists
keys, so a new field on the probe does not reach the UI by itself).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clawmetry import runtime_probe  # noqa: E402


def test_every_probe_reports_the_paths_it_checked() -> None:
    rows = runtime_probe.probe_runtimes()
    assert rows, "no probes registered"
    for r in rows:
        assert "paths" in r, f"{r.get('id')} does not report its checked paths"
        assert isinstance(r["paths"], list)
        assert r["paths"], f"{r.get('id')} reports an empty path list"


def test_checked_paths_are_expanded_not_raw_globs() -> None:
    """A user cannot act on '~/.claude/projects' if their home is elsewhere."""
    rows = {r["id"]: r for r in runtime_probe.probe_runtimes()}
    cc = rows.get("claude_code")
    assert cc, "claude_code probe missing"
    assert not any(p.startswith("~") for p in cc["paths"]), cc["paths"]


def test_unset_env_candidate_is_named_not_dropped() -> None:
    """"We looked here and that variable is not set" is the honest answer;
    silently omitting the location hides why we found nothing."""
    probe = runtime_probe.RuntimeProbe(
        "x", "X", ("~/.x",), env="CLAWMETRY_TEST_UNSET_VAR_5716"
    )
    os.environ.pop("CLAWMETRY_TEST_UNSET_VAR_5716", None)
    paths = probe.checked_paths()
    assert any("CLAWMETRY_TEST_UNSET_VAR_5716" in p and "unset" in p for p in paths), paths


def test_checked_paths_never_raises(monkeypatch) -> None:
    """A probe that throws must not take the whole empty state down with it."""
    monkeypatch.setattr(os.path, "expanduser", lambda p: (_ for _ in ()).throw(OSError("boom")))
    probe = runtime_probe.RuntimeProbe("y", "Y", ("~/.y",))
    assert probe.checked_paths() == []


def test_detection_endpoint_passes_paths_through() -> None:
    """The endpoint builds its payload from an explicit key whitelist, so a
    field added to the probe does NOT reach the UI unless it is added there
    too. That is the failure this test exists to catch."""
    import re
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "..", "routes", "entitlement.py"),
               encoding="utf-8").read()
    # Both payload builders (the no-plan fallback and the tier-decorated one).
    hits = len(re.findall(r'"paths": list\(p\.get\("paths"\)', src))
    assert hits >= 2, (
        f"only {hits} of the 2 runtime-detection payload builders forward "
        "'paths'; the first-run report would show an empty 'where we looked' "
        "list on that code path"
    )


def test_endpoint_reports_whether_anything_is_ingesting() -> None:
    """#5740: `clawmetry` alone starts the dashboard, not the sync daemon, so a
    machine WITH agent data can show zero sessions. The panel must be able to
    tell that apart from "your agents have not run yet" -- otherwise it tells
    the user to go run their agent, which cannot possibly help."""
    import re
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "..", "routes", "entitlement.py"),
               encoding="utf-8").read()
    assert "def _ingest_is_running(" in src
    # Both payload shapes must carry it, same as `paths`.
    assert len(re.findall(r'"ingest_running"', src)) >= 2, (
        "only one runtime-detection payload builder reports ingest state"
    )
    js = open(os.path.join(here, "..", "clawmetry", "static", "js", "app.js"),
              encoding="utf-8").read()
    sec = js[js.index("First-run report (#5716)"):]
    assert "ingest_running === false" in sec, (
        "the panel does not branch on ingest state"
    )
    # The misleading advice must be unreachable when nothing is ingesting.
    i_no = sec.index("noIngest")
    i_advice = sec.index("Run some work")
    assert i_no < i_advice, (
        "'Run some work through the agent' must sit in the else-branch, after "
        "the no-ingest case"
    )


def test_ingest_probe_fails_toward_silence() -> None:
    """A broken probe must not accuse a healthy install of not ingesting."""
    import inspect, re
    here = os.path.dirname(os.path.abspath(__file__))
    src = open(os.path.join(here, "..", "routes", "entitlement.py"),
               encoding="utf-8").read()
    body = re.search(r"def _ingest_is_running\(\).*?(?=\ndef |\n@)", src, re.S).group(0)
    assert "except Exception:\n        return True" in body, (
        "the ingest probe must answer True on error, so an unrelated failure "
        "never renders as 'nothing is ingesting'"
    )
