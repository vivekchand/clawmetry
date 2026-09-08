"""Where Goose actually keeps sessions.db, per platform.

Raised by review on aaif-goose/goose#11554: the tutorial (and the adapter it
describes) claimed a single XDG location, which is wrong on Windows and blind
to ``GOOSE_PATH_ROOT``. The truth, read out of Goose's own
``crates/goose/src/config/paths.rs``:

* ``GOOSE_PATH_ROOT`` wins when set to an ABSOLUTE path -> ``<root>/data``.
* otherwise etcetera's ``choose_app_strategy``, which is the CLI convention:
  ``Windows`` on Windows, ``Xdg`` **everywhere else, macOS included**
  (``create_strategies!(Apple, Xdg)``).

So macOS is XDG, not ``~/Library/Application Support`` — the reviewer's
correction was aimed at the right line but named the platform-native path.
The legacy ``Block/goose`` location that Goose's own paths.rs still mentions
for pre-existing installs is honoured only when a DB is really sitting there.

Every test pins ``sys.platform`` and the home env vars so the whole matrix
runs on any CI OS.
"""
from __future__ import annotations

import importlib.util
import os
import sys

import pytest

from clawmetry.adapters import goose as G
from clawmetry.adapters.goose import GooseAdapter

_FIX_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "runtimes", "goose")
_GEN_PATH = os.path.join(_FIX_DIR, "_make_fixture.py")

_GOOSE_ENV = ("GOOSE_PATH_ROOT", "CLAWMETRY_GOOSE_DB", "XDG_DATA_HOME", "APPDATA")


def _make_db(path: str) -> str:
    spec = importlib.util.spec_from_file_location("_goose_fixture_gen", _GEN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.make_fixture(path)


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A clean HOME with no Goose env vars leaking in from the real machine."""
    h = tmp_path / "home"
    h.mkdir()
    for var in _GOOSE_ENV:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("HOME", str(h))
    monkeypatch.setenv("USERPROFILE", str(h))  # expanduser() on Windows
    return h


def _as(monkeypatch, platform: str):
    monkeypatch.setattr(sys, "platform", platform)


# ── platform defaults ──────────────────────────────────────────────────────


@pytest.mark.parametrize("platform", ["linux", "darwin"])
def test_posix_default_is_xdg(home, monkeypatch, platform):
    """macOS gets the SAME XDG path as Linux — this is the review's line."""
    _as(monkeypatch, platform)
    assert G._candidate_db_paths()[0] == os.path.join(
        str(home), ".local", "share", "goose", "sessions", "sessions.db")
    assert G._default_db_path() == G._candidate_db_paths()[0]


@pytest.mark.parametrize("platform", ["linux", "darwin"])
def test_posix_honours_xdg_data_home(home, monkeypatch, platform):
    _as(monkeypatch, platform)
    monkeypatch.setenv("XDG_DATA_HOME", str(home / "xdg"))
    assert G._candidate_db_paths()[0] == os.path.join(
        str(home), "xdg", "goose", "sessions", "sessions.db")


def test_windows_default_is_roaming_appdata(home, monkeypatch):
    """etcetera's Windows app strategy: <RoamingAppData>/<author>/<app>/data."""
    _as(monkeypatch, "win32")
    monkeypatch.setenv("APPDATA", str(home / "AppData" / "Roaming"))
    assert G._candidate_db_paths()[0] == os.path.join(
        str(home), "AppData", "Roaming", "Block", "goose", "data",
        "sessions", "sessions.db")


def test_windows_falls_back_when_appdata_unset(home, monkeypatch):
    _as(monkeypatch, "win32")
    assert G._candidate_db_paths()[0] == os.path.join(
        str(home), "AppData", "Roaming", "Block", "goose", "data",
        "sessions", "sessions.db")


def test_windows_never_offers_a_posix_path(home, monkeypatch):
    _as(monkeypatch, "win32")
    assert not [p for p in G._candidate_db_paths() if ".local" in p]


def test_posix_never_offers_the_windows_path(home, monkeypatch):
    _as(monkeypatch, "linux")
    assert not [p for p in G._candidate_db_paths() if "Block" in p]


# ── GOOSE_PATH_ROOT ────────────────────────────────────────────────────────


@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
def test_goose_path_root_wins_on_every_platform(home, monkeypatch, platform, tmp_path):
    _as(monkeypatch, platform)
    root = tmp_path / "goose-root"
    monkeypatch.setenv("GOOSE_PATH_ROOT", str(root))
    assert G._candidate_db_paths()[0] == os.path.join(
        str(root), "data", "sessions", "sessions.db")


def test_relative_goose_path_root_is_ignored_like_goose_does(home, monkeypatch):
    """Goose's validated_path_root() drops non-absolute values; so must we."""
    _as(monkeypatch, "linux")
    monkeypatch.setenv("GOOSE_PATH_ROOT", "relative/root")
    assert G._candidate_db_paths()[0] == os.path.join(
        str(home), ".local", "share", "goose", "sessions", "sessions.db")


def test_goose_path_root_store_is_actually_read(home, monkeypatch, tmp_path):
    _as(monkeypatch, "darwin")
    root = tmp_path / "root"
    monkeypatch.setenv("GOOSE_PATH_ROOT", str(root))
    _make_db(str(root / "data" / "sessions" / "sessions.db"))
    assert GooseAdapter().detect().detected is True


# ── macOS legacy location ──────────────────────────────────────────────────


def _legacy(home):
    return os.path.join(str(home), "Library", "Application Support", "Block",
                        "goose", "sessions", "sessions.db")


def test_macos_legacy_store_is_found_when_it_exists(home, monkeypatch):
    _as(monkeypatch, "darwin")
    _make_db(_legacy(home))
    assert G._default_db_path() == _legacy(home)
    assert GooseAdapter().detect().detected is True


def test_macos_legacy_never_reported_when_nothing_is_on_disk(home, monkeypatch):
    """An empty machine must be told where Goose WILL write, not a ghost."""
    _as(monkeypatch, "darwin")
    assert "Library" not in G._default_db_path()


def test_xdg_store_beats_legacy_when_both_exist(home, monkeypatch):
    _as(monkeypatch, "darwin")
    xdg_db = os.path.join(str(home), ".local", "share", "goose", "sessions",
                          "sessions.db")
    _make_db(xdg_db)
    _make_db(_legacy(home))
    assert G._default_db_path() == xdg_db


def test_linux_does_not_probe_the_macos_legacy_path(home, monkeypatch):
    _as(monkeypatch, "linux")
    assert _legacy(home) not in G._candidate_db_paths()


# ── explicit override ──────────────────────────────────────────────────────


def test_clawmetry_goose_db_override_wins(home, monkeypatch, tmp_path):
    _as(monkeypatch, "linux")
    db = _make_db(str(tmp_path / "elsewhere" / "sessions.db"))
    monkeypatch.setenv("CLAWMETRY_GOOSE_DB", db)
    assert G._default_db_path() == db
    assert GooseAdapter().detect().detected is True


def test_explicit_db_path_argument_still_wins_over_env(home, monkeypatch, tmp_path):
    _as(monkeypatch, "linux")
    monkeypatch.setenv("CLAWMETRY_GOOSE_DB", str(tmp_path / "nope.db"))
    db = _make_db(str(tmp_path / "explicit" / "sessions.db"))
    assert GooseAdapter(db_path=db).detect().detected is True


# ── never-raises + no duplicates ───────────────────────────────────────────


@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
def test_candidates_are_unique_and_nonempty(home, monkeypatch, platform):
    _as(monkeypatch, platform)
    cands = G._candidate_db_paths()
    assert cands and len(cands) == len(set(cands))


def test_detect_never_raises_on_a_bogus_root(home, monkeypatch, tmp_path):
    _as(monkeypatch, "linux")
    monkeypatch.setenv("GOOSE_PATH_ROOT", str(tmp_path / "does" / "not" / "exist"))
    assert GooseAdapter().detect().detected is False


def test_detect_never_raises_when_the_store_is_a_directory(home, monkeypatch, tmp_path):
    _as(monkeypatch, "linux")
    root = tmp_path / "root"
    os.makedirs(str(root / "data" / "sessions" / "sessions.db"))
    monkeypatch.setenv("GOOSE_PATH_ROOT", str(root))
    assert GooseAdapter().detect().detected is False


def test_detect_never_raises_on_a_corrupt_store(home, monkeypatch):
    _as(monkeypatch, "linux")
    db = os.path.join(str(home), ".local", "share", "goose", "sessions",
                      "sessions.db")
    os.makedirs(os.path.dirname(db))
    with open(db, "wb") as fh:
        fh.write(b"not a sqlite database at all")
    assert G._default_db_path() == db
    assert GooseAdapter().detect().detected is False


# ── one source of truth ────────────────────────────────────────────────────


def test_data_dir_candidates_mirror_the_db_candidates(home, monkeypatch):
    _as(monkeypatch, "darwin")
    assert G.data_dir_candidates() == [
        os.path.dirname(os.path.dirname(p)) for p in G._candidate_db_paths()]


def test_sync_detection_reads_the_adapter_not_a_copy(home, monkeypatch):
    """The daemon's recency/nudge tables must not hardcode a stale path."""
    _as(monkeypatch, "win32")
    monkeypatch.setenv("APPDATA", str(home / "AppData" / "Roaming"))
    from clawmetry import sync
    assert sync._goose_data_dirs() == G.data_dir_candidates()
    assert sync._runtime_data_paths("goose") == G.data_dir_candidates()


def test_runtime_probe_covers_every_platform_layout(home, monkeypatch):
    from clawmetry.runtime_probe import RUNTIME_PROBES
    probe = next(p for p in RUNTIME_PROBES if p.id == "goose")
    joined = " ".join(probe.paths)
    assert ".local/share/goose" in joined
    assert "AppData/Roaming/Block/goose/data" in joined
    assert "Library/Application Support/Block/goose" in joined
    assert "$GOOSE_PATH_ROOT/data/sessions" in probe.paths
    assert "$XDG_DATA_HOME/goose/sessions" in probe.paths
    assert probe.found() is False
    os.makedirs(os.path.join(str(home), "AppData", "Roaming", "Block", "goose",
                             "data", "sessions"))
    assert probe.found() is True
