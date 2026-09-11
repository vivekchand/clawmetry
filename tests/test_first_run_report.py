"""The first-run report has to be able to say WHERE it looked (#5716).

A dashboard showing nothing is indistinguishable from a broken install. The
panel that fixes that is only as good as the data behind it, so this pins the
part that can silently rot: the probe must expose the paths it actually
checked, and ``clawmetry diagnose`` must print them.

WHERE those paths are allowed to appear changed after review. They are
printed by ``clawmetry diagnose``, a local command whose output a person
runs and chooses to share, and they are NOT served over HTTP or rendered in
the dashboard. Two reasons, both load-bearing:

  * an expanded path carries the account name (``/Users/<name>/...``) into
    every screenshot, screen-share and pasted issue of an empty dashboard.
    ``AC-OBS-RSO-030.7`` already forbids a report carrying a full filesystem
    path, and the detector surface holds itself to it;
  * a complete, copy-pasteable map of where we look for every supported
    runtime is a different artefact from the same table sitting in a source
    file. It would ship with every install and land in every screenshot of a
    fresh machine.

The panel still says HOW MANY runtimes were checked, which is what makes
"nothing detected" trustworthy, and points at the command for the list.

Recorded in the product record as ADR-005 on the Sample Mode and First-Run
Report blueprint, and in the requirement's Capability 2, so the spec and the
code agree on where the map is allowed to appear.
"""
from __future__ import annotations

import glob
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clawmetry import runtime_probe  # noqa: E402


def _read_entitlement_src(here: str) -> str:
    """Read the full source of routes/entitlement, whether file or package."""
    pkg_dir = os.path.join(here, "..", "routes", "entitlement")
    single = os.path.join(here, "..", "routes", "entitlement.py")
    if os.path.isdir(pkg_dir):
        return "\n".join(
            open(f, encoding="utf-8").read()
            for f in sorted(glob.glob(os.path.join(pkg_dir, "*.py")))
        )
    return open(single, encoding="utf-8").read()


def test_every_probe_reports_the_paths_it_checked() -> None:
    rows = runtime_probe.probe_runtimes()
    assert rows, "no probes registered"
    for r in rows:
        assert "paths" in r, f"{r.get('id')} does not report its checked paths"
        assert isinstance(r["paths"], list)
        assert r["paths"], f"{r.get('id')} reports an empty path list"


def test_checked_paths_are_home_collapsed() -> None:
    """Reversed after review.

    This asserted the EXPANDED path, on the reasoning that a user cannot act
    on ``~/.claude/projects`` if their home is elsewhere. ``~`` IS their home
    on every platform we support, and the shell expands it, so the tilde form
    is exactly as actionable and names nobody.
    """
    rows = {r["id"]: r for r in runtime_probe.probe_runtimes()}
    cc = rows.get("claude_code")
    assert cc, "claude_code probe missing"
    assert cc["paths"] == ["~/.claude/projects"], cc["paths"]


def test_no_reported_path_carries_the_home_directory() -> None:
    """Auto-discovering over the catalogue, so a runtime added later cannot
    reintroduce an absolute path without this failing."""
    home = os.path.expanduser("~")
    if home in ("", os.sep):
        return
    for r in runtime_probe.probe_runtimes():
        for path in r.get("paths") or []:
            assert home not in path, (r.get("id"), path)


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


def test_detection_endpoint_serves_no_probed_paths() -> None:
    """The probe map must not travel over HTTP.

    Reversed after review: this used to assert that BOTH payload builders
    forwarded ``paths``. Serving them turns every install into a
    copy-pasteable map of our detection strategy and puts the account name in
    the response. Both builders are checked, because leaving it in one is the
    same leak on that code path.
    """
    import re
    here = os.path.dirname(os.path.abspath(__file__))
    src = _read_entitlement_src(here)
    hits = re.findall(r'"paths": list\(p\.get\("paths"\)', src)
    assert not hits, (
        f"{len(hits)} runtime-detection payload builder(s) still forward the "
        "probed paths; they belong in `clawmetry diagnose`, not in an HTTP "
        "response"
    )


def test_the_served_response_carries_no_path_and_no_home() -> None:
    """The behavioural half of the test above, against the real endpoint."""
    import json
    from flask import Flask
    import routes.entitlement as ent

    app = Flask(__name__)
    app.register_blueprint(ent.bp_entitlement)
    with app.test_client() as c:
        body = c.get("/api/entitlement/runtime-detection").get_json()
    blob = json.dumps(body)
    home = os.path.expanduser("~")
    if home not in ("", os.sep):
        assert home not in blob, "the endpoint must not carry the account name"
    for probe in body.get("probes") or []:
        assert "paths" not in probe, probe.get("id")


def test_the_panel_points_at_the_command_instead_of_listing_paths() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    app_js = open(os.path.join(here, "..", "clawmetry", "static", "js", "app.js"),
                  encoding="utf-8").read()
    assert "clawmetry diagnose" in app_js
    assert "p.paths" not in app_js, "the first-run panel must not render the map"


def test_diagnose_is_where_the_map_lives() -> None:
    import inspect
    from clawmetry import cli as _cli

    assert hasattr(_cli, "_diagnose_runtime_paths")
    src = inspect.getsource(_cli._diagnose_runtime_paths)
    assert "Where ClawMetry looked" in src


def test_endpoint_reports_whether_anything_is_ingesting() -> None:
    """#5740: `clawmetry` alone starts the dashboard, not the sync daemon, so a
    machine WITH agent data can show zero sessions. The panel must be able to
    tell that apart from "your agents have not run yet" -- otherwise it tells
    the user to go run their agent, which cannot possibly help."""
    import re
    here = os.path.dirname(os.path.abspath(__file__))
    src = _read_entitlement_src(here)
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
    src = _read_entitlement_src(here)
    body = re.search(r"def _ingest_is_running\(\).*?(?=\ndef |\n@)", src, re.S).group(0)
    assert "except Exception:\n        return True" in body, (
        "the ingest probe must answer True on error, so an unrelated failure "
        "never renders as 'nothing is ingesting'"
    )
