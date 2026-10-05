"""``vendor_fonts.py --check`` must not write into the tree it is verifying.

What went wrong
---------------
On 2026-10-05 the "Vendored fonts not stale" job failed on ``main`` reporting
that both generated stylesheets were stale. The regeneration the very next step
of the same job ran -- same commit, same runner, seconds later -- produced
output byte-identical to what was already checked in, and the evidence artifact
it uploaded diffs clean against the tree. Nothing had drifted. One fetch from
the upstream font API simply came back different from the next.

Two defects in the checker made that a hard failure instead of a shrug, and
both are covered here:

1. **A single fetch decided the verdict.** The script already separates "could
   not verify" from "verified and wrong", because an upstream nobody controls
   must never leave a contributor with no path to green. An upstream that
   answers the *same request inconsistently* is the same situation and was
   missing from that taxonomy. ``--check`` now corroborates a difference with a
   second independent generation and reports drift only when the two agree.

2. **Checking wrote into what it was checking.** ``build()`` wrote the woff2
   files straight into the checked-in font directory before anything was
   compared, so the comparison ran against a directory the check had just
   overwritten. Two consequences, opposite in sign:

   * a font whose bytes moved upstream without changing its name could never be
     reported, because the old bytes were gone by the time anything looked --
     the gate's whole purpose, silently unenforceable;
   * one odd fetch left a stray file in the tree, poisoning every later
     comparison in that run and leaving a contributor's working tree dirty.

   ``--check`` now generates into a temporary directory and compares the real
   tree against it, by content.

Read with tests/test_vendor_fonts_degrades.py, which holds the other half of
the same contract: tolerating an upstream problem is only acceptable while a
genuine difference still fails. That assertion is repeated here against the new
corroboration path, because it is the part that keeps the tolerance honest.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "vendor_fonts.py")


def _load_module():
    """Import the script fresh so each test gets its own patchable copy."""
    spec = importlib.util.spec_from_file_location("_vendor_fonts_readonly", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run(module, argv):
    """Run main() capturing stdout; return (exit_code, output)."""
    previous = sys.argv[:]
    sys.argv = argv
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = module.main()
    finally:
        sys.argv = previous
    return code, buf.getvalue()


def _dashboard(module) -> dict:
    spec = next(s for s in module.FONT_SETS if s["name"] == "dashboard")
    return spec


def _snapshot(directory: str) -> dict:
    """{name: (bytes, mtime_ns)} so a rewrite with identical bytes still shows."""
    return {
        name: (
            open(os.path.join(directory, name), "rb").read(),
            os.stat(os.path.join(directory, name)).st_mtime_ns,
        )
        for name in sorted(os.listdir(directory))
    }


def test_check_does_not_touch_the_checked_in_font_directory() -> None:
    """The check may not write into the directory whose contents it compares.

    A verifier that overwrites its own evidence cannot fail, and leaves the
    contributor who ran it with a dirty tree.
    """
    module = _load_module()
    spec = _dashboard(module)
    before = _snapshot(spec["fonts_dir"])

    seen: list[str] = []

    def record(_spec, fonts_dir=None):
        # A real build writes the woff2 files here. Prove it is somewhere else.
        seen.append(fonts_dir)
        open(os.path.join(fonts_dir, "manrope-latin.woff2"), "wb").write(b"stub")
        return module._read_text(_spec["css_path"])

    module.build = record
    _run(module, ["vendor_fonts.py", "--check", "--only", "dashboard"])

    assert seen, "build() was never called, so this test proves nothing"
    for directory in seen:
        assert directory is not None, "--check must hand build() an explicit destination"
        assert os.path.realpath(directory) != os.path.realpath(spec["fonts_dir"]), (
            "--check generated straight into the checked-in font directory. The "
            "comparison that follows then runs against files the check itself "
            "just wrote, which is how a changed font upstream became invisible."
        )
    assert _snapshot(spec["fonts_dir"]) == before, (
        "--check modified the checked-in font files. Verifying must be read-only."
    )


def test_inconsistent_upstream_is_unverified_not_drift() -> None:
    """Two fetches that disagree with each other say nothing about the tree.

    This is the case that took main red: the tree was current, and one fetch
    disagreed with the next. Reporting that as drift points the contributor at
    a file that is not wrong, and there is no edit that makes it green.
    """
    module = _load_module()
    answers = iter(
        [
            "/* generation one */",
            "/* generation two, different for the same request */",
        ]
    )

    module.build = lambda _spec, fonts_dir=None: next(answers)

    code, out = _run(module, ["vendor_fonts.py", "--check", "--only", "dashboard"])

    assert code == 0, (
        "An upstream that served two different answers for one request failed "
        "the check. Which of the two would a contributor commit? Neither is "
        "known to be right, so this is 'could not verify', not drift."
    )
    assert "SKIP" in out, "the skip must be visible, not silent"
    assert "DRIFT" not in out, "an inconsistent upstream must never be called drift"


def test_corroborated_difference_still_fails() -> None:
    """The load-bearing half of the tolerance above.

    Corroborating before failing is only safe while a stable, reproducible
    difference still fails. If this ever passes, the corroboration has become a
    way to hide drift and must be reverted.
    """
    module = _load_module()
    module.build = lambda _spec, fonts_dir=None: "/* stably not what is checked in */"

    code, out = _run(module, ["vendor_fonts.py", "--check", "--only", "dashboard"])

    assert code != 0, (
        "A difference that reproduced across two independent generations MUST "
        "still fail. That is exactly what a real upstream font change looks "
        "like, and it is the only thing this job exists to catch."
    )
    assert "DRIFT" in out


def test_second_generation_failing_to_fetch_is_unverified() -> None:
    """An outage while corroborating is still an outage, not a verdict."""
    module = _load_module()
    calls = {"n": 0}

    def flaky(_spec, fonts_dir=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return "/* differs from the checked-in stylesheet */"
        raise OSError("simulated outage while corroborating")

    module.build = flaky

    code, out = _run(module, ["vendor_fonts.py", "--check", "--only", "dashboard"])

    assert calls["n"] == 2, "a difference must trigger a corroborating generation"
    assert code == 0, (
        "The upstream went away before the difference could be confirmed. "
        "Unconfirmed is unverified, not drift."
    )
    assert "SKIP" in out
    assert "DRIFT" not in out


def test_changed_font_bytes_are_reported_even_when_the_css_matches() -> None:
    """The hole the in-place writes hid.

    woff2 filenames are derived from the family and the subset, so a font file
    whose CONTENT changes upstream keeps its name and the generated stylesheet
    is byte-identical. Comparing stylesheets and filenames alone therefore
    reports a clean tree while the shipped bytes are superseded -- which is the
    one thing "vendored fonts not stale" is supposed to mean.
    """
    module = _load_module()
    spec = _dashboard(module)
    checked_in = sorted(os.listdir(spec["fonts_dir"]))
    assert checked_in, "the dashboard font set is empty; this test needs real files"

    def same_css_different_bytes(_spec, fonts_dir=None):
        for name in checked_in:
            with open(os.path.join(fonts_dir, name), "wb") as fh:
                fh.write(b"a newer release of this exact subset")
        return module._read_text(_spec["css_path"])

    module.build = same_css_different_bytes

    code, out = _run(module, ["vendor_fonts.py", "--check", "--only", "dashboard"])

    assert code != 0, (
        "The stylesheet matched but every vendored woff2 differed from the "
        "fresh download, and the check passed. Then the gate cannot detect a "
        "font changing upstream at all."
    )
    assert "DRIFT" in out
    assert "woff2" in out, "the message must name what differs, not just 'stale'"
