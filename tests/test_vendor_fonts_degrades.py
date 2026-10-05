"""An unreachable upstream is "cannot verify", never "drift".

``scripts/vendor_fonts.py --check`` regenerates the vendored font stylesheets
from the Google Fonts API and diffs them against what is checked in. The API is
outside any contributor's control, so an outage, a slow response, or a change to
the CSS shape used to crash the script and fail the check on every pull request
with nothing anyone could do to make it green.

A check with no path to green is a trap. It teaches whoever meets it that red is
normal, or invites them to weaken the assertion. That is not hypothetical here:
the OpenSSF Scorecard job sat broken for its entire life behind a nonexistent
action tag, and the required-check watchdog never ran at all because its YAML
did not parse. Both looked like "ran and failed".

The distinction this file protects is narrow and load-bearing:

* could not FETCH  -> SKIP, exit 0, loudly labelled unverified
* fetched and DIFFERS -> DRIFT, non-zero exit, exactly as before
* could not fetch in GENERATE mode -> still raises, because you cannot write a
  stylesheet you were unable to download

The middle case is the one that matters. Degrading on an unreachable upstream is
only correct if it cannot swallow a real difference, so that is asserted
directly rather than assumed.

Mirrors the posture ``scripts/verify_vendor.py`` already takes for the npm
registry, which prints "registry fetch failed -- skipping byte-comparison".
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "vendor_fonts.py")


def _load_module():
    """Import the script fresh so each test gets its own patchable copy."""
    spec = importlib.util.spec_from_file_location("_vendor_fonts_under_test", SCRIPT)
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


def test_script_exists() -> None:
    assert os.path.isfile(SCRIPT), "scripts/vendor_fonts.py is missing"


@pytest.mark.parametrize(
    "error",
    [
        OSError("simulated network outage"),
        TimeoutError("simulated slow upstream"),
        SystemExit("no @font-face blocks parsed -- API shape changed?"),
    ],
    ids=["network", "timeout", "api-shape-change"],
)
def test_unreachable_upstream_skips_rather_than_failing(error) -> None:
    """None of these are the contributor's fault, so none may fail the check."""
    module = _load_module()

    def boom(_spec):
        raise error

    module.build = boom
    code, out = _run(module, ["vendor_fonts.py", "--check"])

    assert code == 0, (
        f"{type(error).__name__} from the font API failed the check. That is "
        "outside any contributor's control, so it leaves them with no path to "
        "green. Report it as unverified instead."
    )
    assert "SKIP" in out, "the skip must be visible, not silent"
    assert "DRIFT" not in out, "an unreachable API must never be reported as drift"


def test_real_drift_still_fails() -> None:
    """The load-bearing half.

    Degrading on an unreachable upstream is only acceptable if it cannot
    swallow a genuine difference. If this ever passes, the tolerance above has
    become a way to hide bugs and must be reverted.
    """
    module = _load_module()
    module.build = lambda _spec: "/* deliberately not what is checked in */"

    code, out = _run(module, ["vendor_fonts.py", "--check"])

    assert code != 0, (
        "A successful fetch whose content differs from the checked-in "
        "stylesheet MUST still fail. The unreachable-upstream tolerance is "
        "only safe while this holds."
    )
    assert "DRIFT" in out


def test_generate_mode_still_raises_when_upstream_is_unreachable() -> None:
    """You cannot write a stylesheet you were unable to fetch."""
    module = _load_module()

    def boom(_spec):
        raise OSError("simulated network outage")

    module.build = boom

    with pytest.raises(OSError):
        _run(module, ["vendor_fonts.py"])


def test_keyboard_interrupt_is_not_swallowed() -> None:
    """A person pressing Ctrl-C is not an upstream outage."""
    module = _load_module()

    def boom(_spec):
        raise KeyboardInterrupt()

    module.build = boom

    with pytest.raises(KeyboardInterrupt):
        _run(module, ["vendor_fonts.py", "--check"])


def test_drift_capture_is_same_generation_and_still_fails(tmp_path):
    """Never repair a failed generation using evidence from a second fetch."""
    module = _load_module()
    css_path = tmp_path / "fonts.css"
    css_path.write_text("old generation")
    module.FONT_SETS = [{"name": "test", "css_path": str(css_path)}]
    calls = []
    mirrors = []

    def alternating_build(_spec):
        calls.append(1)
        return "failed generation" if len(calls) == 1 else "old generation"

    module.build = alternating_build
    module._mirror = lambda _spec, text: mirrors.append(text)
    code, out = _run(module, ["vendor_fonts.py", "--check", "--capture-drift"])
    assert code == 1
    assert "DRIFT" in out and "CAPTURE" in out
    assert calls == [1]
    assert css_path.read_text() == "failed generation"
    assert mirrors == ["failed generation"]


def test_capture_flag_requires_check():
    module = _load_module()
    with pytest.raises(SystemExit) as error:
        _run(module, ["vendor_fonts.py", "--capture-drift"])
    assert error.value.code == 2


def _real_font():
    return open(os.path.join(REPO_ROOT, 'clawmetry/static/fonts/manrope-latin-ext.woff2'), 'rb').read()


def test_metadata_without_additional_glyphs_has_identical_effective_range():
    module = _load_module()
    raw = _real_font()
    old = 'U+0100-02BA, U+20AD-20C0'
    new = 'U+0100-02BA, U+20AD-20C4'
    assert module._effective_range(raw, old) == module._effective_range(raw, new)
    # A genuine loss of supported points must still alter the generation.
    assert module._effective_range(raw, 'U+0101-02BA') != module._effective_range(raw, 'U+0100-02BA')


def test_invalid_downloaded_font_is_failure_not_unverified():
    module = _load_module()
    module.build = lambda _spec: (_ for _ in ()).throw(module.FontDataError('corrupt downloaded font'))
    code, output = _run(module, ['vendor_fonts.py', '--check'])
    assert code == 1 and 'DRIFT' in output
    assert 'SKIP' not in output


def test_corrupt_committed_binary_fails_even_when_css_matches(tmp_path):
    module = _load_module()
    spec = {'name':'test', 'url':'https://fonts.invalid/css', 'fonts_dir': str(tmp_path/'fonts'), 'css_path':str(tmp_path/'fonts.css'), 'rel':'fonts', 'note':'test'}
    raw = _real_font()
    css = b"/* latin-ext */ @font-face { font-family: 'Manrope'; font-weight: 400; font-style: normal; src: url(https://fonts.invalid/manrope.woff2); unicode-range: U+0100-02BA; }"
    module._fetch = lambda url: raw if url.endswith('.woff2') else css
    expected = module.build(spec)
    assert 'font-sha256:' in expected
    with open(spec['css_path'], 'w') as out:
        out.write(expected)
    module.FONT_SETS = [spec]
    code, _ = _run(module, ['vendor_fonts.py', '--check'])
    assert code == 0
    with open(os.path.join(spec['fonts_dir'], 'manrope-latin-ext.woff2'), 'wb') as out:
        out.write(b'corrupt committed font')
    code, output = _run(module, ['vendor_fonts.py', '--check'])
    assert code == 1 and 'DRIFT' in output


def test_mirror_binary_mismatch_fails(tmp_path):
    module = _load_module()
    source=tmp_path/'fonts'; source.mkdir()
    (source/'one.woff2').write_bytes(b'valid source')
    mirror=tmp_path/'mirror'; mirror.mkdir(); (mirror/'fonts').mkdir()
    (mirror/'fonts'/'one.woff2').write_bytes(b'wrong mirror')
    (mirror/'fonts.css').write_text('same css')
    spec={'fonts_dir':str(source),'css_path':str(tmp_path/'fonts.css'),'mirror_dir':str(mirror)}
    assert module._mirror_is_current(spec,'same css') is False
