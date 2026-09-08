"""Guard: the harness-observability manifest stays well-formed and complete.

scripts/harness/manifest.json drives the daily audit that keeps ClawMetry's
coverage current as the runtimes evolve. If it drifts (a runtime dropped, a bad
repo URL, a wrong adapter path), the audit silently skips that runtime — so we
pin the shape here.

Split (2026-06-04): the OSS manifest is free-only (openclaw + nemoclaw). The 10
pro runtimes (claude_code, codex, goose, aider, opencode, qwen_code, cursor,
hermes, picoclaw, nanoclaw) moved to clawmetry-pro's private manifest and audit
workflow to keep closed adapter paths out of the public repo. This test guards
that the free-only scope is preserved; the pro side is guarded separately there.
"""
import json
import os
import re

HERE = os.path.dirname(__file__)
MANIFEST = os.path.join(HERE, "..", "scripts", "harness", "manifest.json")

# Only the two free runtimes live in the OSS manifest. Pro runtimes are audited
# by clawmetry-pro's own private manifest (see scripts/harness/manifest.json
# _comment and _verified fields for the authoritative rationale).
_FREE_RUNTIMES = {"openclaw", "nemoclaw"}


def _load():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def test_manifest_is_valid_json_and_covers_free_runtimes():
    m = _load()
    runtimes = {h["runtime"] for h in m["harnesses"]}
    assert runtimes == _FREE_RUNTIMES, (
        f"manifest runtimes drifted: missing={_FREE_RUNTIMES - runtimes}, "
        f"extra={runtimes - _FREE_RUNTIMES}"
    )


def test_every_entry_is_well_formed():
    m = _load()
    for h in m["harnesses"]:
        rt = h.get("runtime")
        assert rt, f"entry missing runtime: {h}"
        assert h.get("adapter"), f"{rt}: missing adapter path"
        assert h.get("adapter_repo") in ("clawmetry", "clawmetry-pro"), f"{rt}: bad adapter_repo"
        repo = h.get("repo")
        # repo is either null (closed/unknown, with a note) or a real https GitHub URL
        if repo is None:
            assert h.get("note"), f"{rt}: repo=null must carry a note explaining why"
        else:
            assert re.match(r"^https://github\.com/[\w.-]+/[\w.-]+$", repo), \
                f"{rt}: repo is not a github https URL: {repo}"


def test_openclaw_and_nemoclaw_are_free_tier():
    m = _load()
    by = {h["runtime"]: h for h in m["harnesses"]}
    assert by["openclaw"]["tier"] == "free"
    assert by["nemoclaw"]["tier"] == "free"
    # nemoclaw is sandboxed openclaw -> shares the openclaw adapter
    assert by["nemoclaw"]["adapter"] == by["openclaw"]["adapter"]
