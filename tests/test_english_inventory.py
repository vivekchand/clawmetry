"""AC-STE-002.1/.2/.3/.4/.5: corpus extraction and a baseline that only shrinks."""
import json
from pathlib import Path
import subprocess

import pytest

from scripts.check_english import (BASELINE, CATALOG, Message, VisibleText,
                                   collect, inventory, main, violations)


@pytest.fixture(scope="session")
def server():
    """Corpus checks use temporary files, not a live dashboard."""
    yield None


def fixture_root(tmp_path, text="The agent stopped; open the session."):
    catalog = tmp_path / CATALOG
    catalog.parent.mkdir(parents=True)
    catalog.write_text(json.dumps({"example": text}))
    (tmp_path / "docs").mkdir()
    return tmp_path


def test_inline_tags_cannot_split_a_long_sentence():
    parser = VisibleText("sample.html")
    parser.feed("<p>" + "word " * 10 + "<strong>" + "word " * 12 + "</strong>.</p>")
    parser.flush()
    assert len(parser.messages) == 1
    counts, _ = violations(parser.messages)
    assert any(key.endswith("STE-5.1") for key in counts)


def test_extractor_ignores_executable_content_and_keeps_accessibility():
    parser = VisibleText("sample.html")
    parser.feed('<style>bad; css</style><script>bad; code</script><!-- bad; comment -->'
                '<button title="The agent stopped; try again.">Open <b>the</b> session.</button>')
    parser.flush()
    assert [m.text for m in parser.messages] == ["The agent stopped; try again.", "Open the session."]


def test_baseline_only_decreases(tmp_path):
    root = fixture_root(tmp_path)
    assert main(["--root", str(root), "--bootstrap-baseline"]) == 0
    assert main(["--root", str(root), "--bootstrap-baseline"]) == 1
    assert main(["--root", str(root)]) == 0
    (root / CATALOG).write_text(json.dumps({"example": "The agent stopped. Open its session."}))
    assert main(["--root", str(root)]) == 1  # stale debt must be removed
    assert main(["--root", str(root), "--update-baseline"]) == 0
    (root / CATALOG).write_text(json.dumps({"example": "It isn't active."}))
    before = (root / BASELINE).read_bytes()
    assert main(["--root", str(root), "--update-baseline"]) == 1
    assert (root / BASELINE).read_bytes() == before


def test_changed_text_cannot_inherit_an_old_exception(tmp_path):
    root = fixture_root(tmp_path)
    assert main(["--root", str(root), "--bootstrap-baseline"]) == 0
    (root / CATALOG).write_text(json.dumps({"example": "The tool stopped; open the session."}))
    assert main(["--root", str(root)]) == 1


def test_duplicate_occurrences_are_counted():
    message = Message("page.html", "visible", 1, "It isn't active.")
    once, _ = violations([message])
    twice, _ = violations([message, message])
    assert twice - once == once


def test_missing_corrupt_or_duplicate_catalog_fails(tmp_path):
    root = fixture_root(tmp_path)
    path = root / CATALOG
    for raw in ('{"example": 3}', '{"a":"One","a":"Two"}', '{'):
        path.write_text(raw)
        assert main(["--root", str(root)]) == 1
    path.unlink()
    assert main(["--root", str(root)]) == 1


def test_ci_cannot_grow_baseline(tmp_path):
    root = fixture_root(tmp_path)
    assert main(["--root", str(root), "--bootstrap-baseline"]) == 0
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.test",
                    "-c", "commit.gpgsign=false", "commit", "-qm", "baseline"], cwd=root, check=True)
    data = json.loads((root / BASELINE).read_text())
    data["findings"]["fake"] = 1
    (root / BASELINE).write_text(json.dumps(data))
    assert main(["--root", str(root), "--base-ref", "HEAD"]) == 1


def test_invalid_base_ref_fails_closed(tmp_path):
    root = fixture_root(tmp_path)
    assert main(["--root", str(root), "--bootstrap-baseline"]) == 0
    assert main(["--root", str(root), "--base-ref", "not-a-revision"]) == 1


def test_inventory_does_not_count_source_files_as_reviewed(tmp_path):
    root = fixture_root(tmp_path)
    source = root / "clawmetry/static/js/new-feature.js"
    source.parent.mkdir(parents=True)
    source.write_text('show("An unchecked message");')
    messages = collect(root)
    counts, _ = violations(messages)
    result = inventory(root, messages, counts)
    assert any(s["path"].endswith("new-feature.js") for s in result["remaining_sources"])
    assert not any(s["path"].endswith("new-feature.js") for s in result["checked_sources"])
    assert "Full compliance is not established" in result["claim"]
    assert set(result["external_repositories"]) == {"clawmetry-pro", "clawmetry-cloud", "clawmetry-landing"}


def test_repository_baseline_is_current():
    assert main([]) == 0


def test_rendered_setup_has_clear_control_boundary():
    """AC-STE-004.1: the live template must not promise observation-only behavior."""
    from jinja2 import Environment, FileSystemLoader
    from scripts.check_english import ROOT
    env = Environment(loader=FileSystemLoader(str(ROOT / "clawmetry/templates")), autoescape=True)
    rendered = env.get_template("partials/onboarding-modal.html").render()
    parser = VisibleText("onboarding-modal.html")
    parser.feed(rendered)
    parser.flush()
    counts, _ = violations(parser.messages)
    assert not counts
    visible = " ".join(m.text for m in parser.messages)
    assert "Agent controls require your action or an enabled policy." in visible
    assert "never changes them" not in visible
    assert "Cloud" in visible and "license key" in visible
