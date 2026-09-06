"""The non-security digest helper, and the ratchet that keeps it used.

Two things are being pinned here:

1. ``nonsecret_hash.md5``/``sha1`` return the SAME digest as ``hashlib``.
   That is not a nicety -- the call sites this helper replaced produce
   persisted ids (event dedup keys in DuckDB, trace/span ids, cron
   change-detection hashes). If ``usedforsecurity=False`` changed the bytes,
   the switch would silently re-ingest every already-stored event. It does
   not, and this test is what says so out loud.

2. No runtime module reaches for ``hashlib.md5``/``hashlib.sha1`` directly
   again. A bare constructor raises ``ValueError`` on a host whose crypto
   provider allows only approved algorithms, which turns a dedup key into a
   crashed ingest pass. Bandit reports this as B324; this test is the
   in-repo ratchet so it cannot come back between audit runs.
"""

import ast
import hashlib
import io
import os
import re
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import nonsecret_hash  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.parametrize("payload", [
    b"",
    b"hello",
    "cron|2026-09-06T00:00:00Z|job-1".encode("utf-8"),
    bytes(range(256)),
])
def test_digests_match_hashlib(payload):
    """The helper must not change any already-persisted id."""
    assert nonsecret_hash.md5(payload).hexdigest() == hashlib.md5(payload).hexdigest()
    assert nonsecret_hash.sha1(payload).hexdigest() == hashlib.sha1(payload).hexdigest()


def test_update_is_supported():
    """Callers may build a digest incrementally, as with hashlib."""
    h = nonsecret_hash.sha1()
    h.update(b"ab")
    h.update(b"cd")
    assert h.hexdigest() == hashlib.sha1(b"abcd").hexdigest()


def test_declares_not_for_security_where_the_runtime_accepts_it():
    """On 3.9+ the kwarg must actually be passed, not merely available."""
    if sys.version_info < (3, 9):
        pytest.skip("usedforsecurity= reached hashlib in CPython 3.9")
    assert nonsecret_hash._ACCEPTS_USEDFORSECURITY is True
    # A digest object built with the flag reports it the only way it can:
    # by being constructible at all under a restricted provider. Assert the
    # call shape instead, so this stays meaningful off a FIPS host.
    src = io.open(
        os.path.join(REPO, "clawmetry", "nonsecret_hash.py"), encoding="utf-8"
    ).read()
    assert "hashlib.md5(data, usedforsecurity=False)" in src
    assert "hashlib.sha1(data, usedforsecurity=False)" in src


def test_the_weak_digest_calls_stay_contained_and_marked():
    """Exactly four ``hashlib`` calls live here, and the 3.8 pair keeps B324.

    The bandit marker lives on the call line and is silently lost by a
    reformat or a copy-paste, which re-raises B324 without failing any test
    run -- so this is the test run.

    There is deliberately no CodeQL annotation to assert. An
    ``# codeql[py/weak-sensitive-data-hashing]`` comment was tried on all
    four calls and measured: CodeQL re-ran and reported the same four
    alerts, renumbered 977-980 -> 981-984. Default setup does not honour
    inline suppression, so such a comment is decoration that reads like a
    fix. This asserts it does not come back.
    """
    path = os.path.join(REPO, "clawmetry", "nonsecret_hash.py")
    src = io.open(path, encoding="utf-8").read()
    lines = src.splitlines()

    # Parsed, not grepped: the module docstring quotes `hashlib.md5(...)`
    # while explaining itself, and prose must not count as a call site.
    calls = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if (isinstance(fn, ast.Attribute) and fn.attr in ("md5", "sha1")
                and isinstance(fn.value, ast.Name) and fn.value.id == "hashlib"):
            calls.append((node.lineno, lines[node.lineno - 1]))
    calls.sort()

    assert len(calls) == 4, (
        "expected exactly the two md5 and two sha1 constructor calls, got:\n  "
        + "\n  ".join("%d: %s" % (n, ln.strip()) for n, ln in calls)
    )

    for n, ln in calls:
        assert "codeql[" not in ln, (
            "nonsecret_hash.py:%d carries an inline CodeQL suppression. "
            "Default setup does not honour those -- it was measured on this "
            "very file -- so the comment silences nothing and reads like a "
            "fix. Dismiss the alert in the Security tab instead:\n  %s"
            % (n, ln.strip())
        )
        if "usedforsecurity" not in ln:
            assert "nosec B324" in ln, (
                "nonsecret_hash.py:%d omits usedforsecurity= and so needs "
                "bandit's B324 marker too:\n  %s" % (n, ln.strip())
            )


def test_helper_is_importable_on_py38_syntax():
    """The helper is imported by modules that still have to load on 3.8."""
    src = io.open(
        os.path.join(REPO, "clawmetry", "nonsecret_hash.py"), encoding="utf-8"
    ).read()
    compile(src, "nonsecret_hash.py", "exec")
    assert "sys.version_info >= (3, 9)" in src, "the 3.8 fallback must stay"


# --------------------------------------------------------------------------
# The ratchet.
# --------------------------------------------------------------------------

#: Directly-constructed MD5/SHA-1 that does NOT declare usedforsecurity.
_BARE = re.compile(r"hashlib\.(?:md5|sha1)\s*\((?![^)]*usedforsecurity)")

#: Scanned trees. `scripts/` is deliberately absent: those are standalone CI
#: harnesses run as `python3 scripts/...`, so the package is not on their
#: sys.path and they cannot import this helper.
_SCANNED = ("clawmetry", "routes", "helpers")

_EXEMPT = {
    # The helper itself owns the one guarded fallback call, for 3.8.
    os.path.join("clawmetry", "nonsecret_hash.py"),
}


def _python_files():
    for tree in _SCANNED:
        base = os.path.join(REPO, tree)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in ("__pycache__", "node_modules")]
            for name in filenames:
                if name.endswith(".py"):
                    yield os.path.join(dirpath, name)
    top = os.path.join(REPO, "dashboard.py")
    if os.path.isfile(top):
        yield top


def test_no_bare_md5_or_sha1_in_runtime_code():
    offenders = []
    for path in _python_files():
        rel = os.path.relpath(path, REPO)
        if rel in _EXEMPT:
            continue
        try:
            src = io.open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for lineno, line in enumerate(src.splitlines(), 1):
            if _BARE.search(line):
                offenders.append("%s:%d: %s" % (rel, lineno, line.strip()))
    assert not offenders, (
        "Use clawmetry.nonsecret_hash.md5 / .sha1 for non-security digests -- a "
        "bare constructor raises on a host with a restricted crypto provider:\n  "
        + "\n  ".join(offenders)
    )


def test_ratchet_would_catch_a_regression():
    """The guard above is worthless if its pattern does not actually bite."""
    assert _BARE.search("h = hashlib.md5(raw).hexdigest()")
    assert _BARE.search('x = hashlib.sha1(b"a")')
    assert not _BARE.search("hashlib.md5(data, usedforsecurity=False)")
    assert not _BARE.search("hashlib.sha256(raw)")


def test_every_rewritten_call_site_still_imports_the_helper():
    """Catches a merge that keeps `_nsh.md5(...)` but drops the import."""
    missing = []
    for path in _python_files():
        src = io.open(path, encoding="utf-8", errors="replace").read()
        if "_nsh." not in src:
            continue
        if "nonsecret_hash as _nsh" not in src:
            missing.append(os.path.relpath(path, REPO))
    assert not missing, "uses _nsh without importing it: %s" % missing


def test_package_imports_cleanly_in_a_fresh_interpreter():
    """The new module must not introduce an import cycle."""
    out = subprocess.run(
        [sys.executable, "-c",
         "import clawmetry.nonsecret_hash as m; print(m.md5(b'x').hexdigest())"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == hashlib.md5(b"x").hexdigest()
