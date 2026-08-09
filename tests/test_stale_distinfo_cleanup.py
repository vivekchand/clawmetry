"""Stale dist-info cleanup — regression guard for the Windows in-place
upgrade leak (2026-08-10).

Every in-place pip upgrade run while a sibling process held ``.pyd``/
``.exe`` files open half-failed its uninstall of the previous version and
left that version's ``clawmetry-*.dist-info`` behind (five stale ones,
0.12.655–0.12.669, observed live alongside the current install). Because
``importlib.metadata`` resolves the FIRST matching dist-info in
directory-listing order (alphabetical on NTFS), the OLDEST stale version
won every metadata probe, and pip's own installed-version resolution ran
against the wrong RECORD.

``clawmetry.distinfo_cleanup.cleanup_stale_dist_info`` must remove
dist-infos strictly older than the installed version plus ``~lawmetry*``
pip-uninstall corpses, keep the current AND any newer dist-info (the
just-upgraded-but-not-yet-restarted window), and be wired into both the
update-check worker boot and ``perform_self_update``.
"""

from __future__ import annotations

import importlib.metadata

from clawmetry.distinfo_cleanup import cleanup_stale_dist_info


def _make_dist_info(sp, version, name="clawmetry"):
    d = sp / f"{name}-{version}.dist-info"
    d.mkdir(parents=True)
    (d / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
    )
    (d / "RECORD").write_text("")
    return d


def test_removes_stale_keeps_current_and_newer(tmp_path):
    sp = tmp_path / "site-packages"
    for v in ("0.12.655", "0.12.660", "0.12.669"):
        _make_dist_info(sp, v)
    current = _make_dist_info(sp, "0.12.674")
    newer = _make_dist_info(sp, "0.12.700")  # mid-upgrade window: keep
    corpse = sp / "~lawmetry-0.12.650.dist-info"
    corpse.mkdir()
    (corpse / "METADATA").write_text("stash")
    other = _make_dist_info(sp, "0.12.1", name="clawmetry_pro")

    removed = cleanup_stale_dist_info(
        keep_version="0.12.674", site_packages=str(sp)
    )

    assert sorted(removed) == [
        "clawmetry-0.12.655.dist-info",
        "clawmetry-0.12.660.dist-info",
        "clawmetry-0.12.669.dist-info",
        "~lawmetry-0.12.650.dist-info",
    ]
    assert current.is_dir()
    assert newer.is_dir()
    assert other.is_dir(), "unrelated packages must never be touched"
    assert not corpse.exists()


def test_metadata_resolves_installed_version_after_cleanup(tmp_path):
    """The observed symptom: importlib.metadata returned the OLDEST stale
    dist-info's version. After cleanup exactly one clawmetry distribution
    remains and it is the installed one."""
    sp = tmp_path / "site-packages"
    for v in ("0.12.655", "0.12.660", "0.12.669", "0.12.674"):
        _make_dist_info(sp, v)

    cleanup_stale_dist_info(keep_version="0.12.674", site_packages=str(sp))

    versions = [
        d.metadata["Version"]
        for d in importlib.metadata.distributions(path=[str(sp)])
        if (d.metadata["Name"] or "").lower() == "clawmetry"
    ]
    assert versions == ["0.12.674"]


def test_noop_on_source_checkout_layout(tmp_path):
    """A directory without dist-info entries (source checkout) is a no-op."""
    (tmp_path / "dashboard.py").write_text("__version__ = 'x'\n")
    assert cleanup_stale_dist_info(
        keep_version="0.12.674", site_packages=str(tmp_path)
    ) == []


def test_stale_removed_even_without_current_dist_info(tmp_path):
    """Ghost install (current version's dist-info missing): stale ones are
    still pruned so pip's next run starts from clean metadata."""
    sp = tmp_path / "site-packages"
    _make_dist_info(sp, "0.12.655")
    removed = cleanup_stale_dist_info(
        keep_version="0.12.674", site_packages=str(sp)
    )
    assert removed == ["clawmetry-0.12.655.dist-info"]


def test_unparseable_keep_version_is_noop(tmp_path):
    sp = tmp_path / "site-packages"
    _make_dist_info(sp, "0.12.655")
    assert cleanup_stale_dist_info(
        keep_version="latest", site_packages=str(sp)
    ) == []
    assert (sp / "clawmetry-0.12.655.dist-info").is_dir()


def test_perform_self_update_prunes_after_install(monkeypatch, tmp_path):
    """Wiring guard: a successful perform_self_update must invoke the
    cleanup with the freshly installed version as keep_version."""
    import types

    import clawmetry.distinfo_cleanup as dc
    from routes import meta

    calls = []
    monkeypatch.setattr(
        dc, "cleanup_stale_dist_info",
        lambda keep_version=None, **kw: calls.append(keep_version) or [],
    )

    def _fake_run(cmd, *a, **k):
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    def _fake_check_output(cmd, *a, **k):
        return b"Name: clawmetry\nVersion: 0.12.674\n"

    monkeypatch.setattr(meta, "_win_cleanup_old_exe_stubs", lambda: None)
    monkeypatch.setattr(meta, "_win_rename_exe_before_pip",
                        lambda: (None, None))
    # Keep the crash-loop rollback guard from touching real ~/.clawmetry.
    from clawmetry import update_guard
    monkeypatch.setattr(update_guard, "arm_rollback_guard",
                        lambda *a, **k: None)
    import subprocess
    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setattr(subprocess, "check_output", _fake_check_output)

    payload, status = meta.perform_self_update(reason="test", restart=False)

    assert status == 200 and payload.get("ok")
    assert calls == ["0.12.674"]


def test_update_check_worker_boot_prunes(monkeypatch):
    """Wiring guard: the update-check worker prunes stale dist-info at boot
    (this is what heals a box after the Windows respawn helper upgraded)."""
    import threading

    import clawmetry.distinfo_cleanup as dc
    from routes import update_check

    called = threading.Event()
    monkeypatch.setattr(
        dc, "cleanup_stale_dist_info", lambda *a, **k: called.set() or []
    )
    stop = threading.Event()
    stop.set()  # worker exits at the first wait, right after the cleanup
    update_check._update_check_worker(stop)
    assert called.is_set()
