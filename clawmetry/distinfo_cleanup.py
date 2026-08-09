"""clawmetry/distinfo_cleanup.py — prune stale dist-info left by partial upgrades.

On Windows an in-place ``pip install --upgrade`` regularly runs while a
sibling clawmetry process (dashboard child, proxy, a second daemon) still
holds ``.pyd``/``.exe`` files from the old wheel open. pip's uninstall of
the previous version then partially fails: the new wheel and its dist-info
land fine, but the OLD ``clawmetry-<ver>.dist-info`` directory (and
sometimes a ``~lawmetry*`` stash pip renamed mid-uninstall) stays behind.
Observed live on the Windows lab machine 2026-08-10: five stale dist-infos
(0.12.655–0.12.669) alongside the current one.

Stale dist-infos are not cosmetic:

* ``importlib.metadata.version("clawmetry")`` returns the FIRST matching
  distribution in directory-listing order — on NTFS that is alphabetical,
  so the OLDEST stale dist-info wins and every metadata-based version
  probe lies.
* pip itself resolves "installed version" from the same metadata, so its
  upgrade/uninstall decisions run against the wrong RECORD.

This module removes ``clawmetry-*.dist-info`` directories whose version is
STRICTLY OLDER than the one actually installed (the running code's
``dashboard.__version__``), plus ``~lawmetry*`` pip-uninstall corpses.
Newer-than-current dist-infos are deliberately kept: right after an
in-place upgrade the running process is still the old build while the new
wheel's metadata is already on disk — deleting it would brick the fresh
install. Callers run this at process boot and after a successful install,
both windows in which no pip is active (updates hold the cross-process
update lock). Never raises.
"""

from __future__ import annotations

import logging
import os
import shutil

log = logging.getLogger(__name__)

_DIST_INFO_SUFFIX = ".dist-info"


def _ver_tuple(v):
    """``"0.12.660"`` -> ``(0, 12, 660)``; None when unparseable."""
    try:
        return tuple(int(x) for x in str(v).split("."))
    except (TypeError, ValueError):
        return None


def cleanup_stale_dist_info(keep_version=None, site_packages=None,
                            package="clawmetry"):
    """Remove stale ``<package>-*.dist-info`` dirs and pip-uninstall corpses.

    ``keep_version`` defaults to the running code's ``dashboard.__version__``
    (the wheel actually installed); ``site_packages`` defaults to the
    directory containing ``dashboard.py`` — in an installed wheel that IS
    site-packages, and in a source checkout it contains no dist-info so the
    call is a natural no-op. Returns the list of removed entry names.
    """
    removed = []
    if keep_version is None:
        try:
            import dashboard as _d
            keep_version = str(_d.__version__)
        except Exception:
            return removed
    if site_packages is None:
        try:
            import dashboard as _d
            site_packages = os.path.dirname(os.path.abspath(_d.__file__))
        except Exception:
            return removed
    keep_t = _ver_tuple(keep_version)
    if keep_t is None:
        return removed

    prefix = package + "-"
    # pip stashes a pending uninstall by renaming the first character to
    # "~" ("clawmetry-…" -> "~lawmetry-…"); a leftover one is a crashed or
    # partially-failed pip run, never a live install.
    corpse_prefix = "~" + package[1:]
    try:
        entries = os.listdir(site_packages)
    except OSError:
        return removed

    for name in entries:
        stale = False
        if name.startswith(corpse_prefix):
            stale = True
        elif name.startswith(prefix) and name.endswith(_DIST_INFO_SUFFIX):
            ver = name[len(prefix):-len(_DIST_INFO_SUFFIX)]
            vt = _ver_tuple(ver)
            stale = vt is not None and vt < keep_t
        if not stale:
            continue
        path = os.path.join(site_packages, name)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            removed.append(name)
        except OSError as exc:
            # Locked entries heal on a later boot; never block startup.
            log.debug("stale dist-info %s not removable now: %s", name, exc)

    if removed:
        log.info("pruned %d stale %s metadata entr%s from %s: %s",
                 len(removed), package, "y" if len(removed) == 1 else "ies",
                 site_packages, ", ".join(sorted(removed)))
    return removed
