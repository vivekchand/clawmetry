"""A channel is four lists, and a channel in three of them is broken (#5045).

Shipping a chat channel means naming it in four independent places. Each
omission fails silently, and each looks like a different bug:

    ``sync._CHANNEL_DIRS``          historical transcripts ingest
    ``gateway_tap.CHANNEL_NAMES``   live events arrive
    ``entitlements.ALL_CHANNELS``   the UI and entitlement can see it
    ``routes/channels.py``          the endpoint exists

Miss the gateway list and live messages never arrive while history works fine
-- the reporter says "old messages show up but nothing new", which points at
ingest, not at a missing subscription. Miss the catalogue and the channel is
invisible even with rows already in the store.

The blueprint section "A chat channel is four lists, and a channel in three of
them is broken" records this, and its ADR admitted the gap these tests close:
the lists could not drift *undetectably*, but a genuinely independent omission
was caught by review rather than by a check. It is a check now.

The disk name and the wire name may legitimately differ (``fish-audio`` on
disk, ``fishaudio`` on the wire), so comparison is on a normalised form rather
than byte equality -- deriving one list from the other is exactly what the
blueprint forbids.
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _tuple_literal(path: str, var: str) -> set:
    """Names in a module-level tuple literal, read as TEXT.

    Deliberately not an import: `sync.py` and `gateway_tap.py` pull in the
    daemon's dependencies, and this check must run in a plain lint job.
    """
    src = open(os.path.join(ROOT, path), encoding="utf-8").read()
    m = re.search(re.escape(var) + r"[^=]*=\s*\((.*?)\)", src, re.S)
    assert m, "{}: could not find a tuple literal for {}".format(path, var)
    found = set(re.findall(r'"([a-z0-9_\-]+)"', m.group(1)))
    assert found, "{}: {} parsed as empty".format(path, var)
    return found


def _norm(name: str) -> str:
    return name.replace("-", "").replace("_", "").lower()


def _lists():
    return (
        _tuple_literal("clawmetry/sync.py", "_CHANNEL_DIRS"),
        _tuple_literal("clawmetry/gateway_tap.py", "CHANNEL_NAMES"),
        _tuple_literal("clawmetry/entitlements.py", "ALL_CHANNELS"),
    )


def test_every_catalogued_channel_can_receive_live_events():
    """The failure this test exists for: an endpoint and a directory, but no
    gateway subscription, so live messages never arrive."""
    dirs, wire, catalogue = _lists()
    wire_n = {_norm(w) for w in wire}
    missing = sorted(c for c in catalogue if _norm(c) not in wire_n)
    assert not missing, (
        "in ALL_CHANNELS but not in gateway_tap.CHANNEL_NAMES: {}. "
        "Live messages for these never arrive, while historical transcripts "
        "ingest normally -- which reads as an ingest bug, not a missing "
        "subscription.".format(missing)
    )


def test_every_catalogued_channel_has_its_transcripts_ingested():
    dirs, wire, catalogue = _lists()
    dirs_n = {_norm(d) for d in dirs}
    missing = sorted(c for c in catalogue if _norm(c) not in dirs_n)
    assert not missing, (
        "in ALL_CHANNELS but not in sync._CHANNEL_DIRS: {}. The daemon never "
        "walks ~/.openclaw/<channel>/*.jsonl for these, so history never "
        "ingests.".format(missing)
    )


def test_no_orphan_in_the_ingest_lists():
    """The other direction: a directory or subscription for a channel the
    catalogue does not know about is dead weight that reads as support."""
    dirs, wire, catalogue = _lists()
    cat_n = {_norm(c) for c in catalogue}
    orphan_dirs = sorted(d for d in dirs if _norm(d) not in cat_n)
    orphan_wire = sorted(w for w in wire if _norm(w) not in cat_n)
    assert not orphan_dirs, "in _CHANNEL_DIRS but not catalogued: {}".format(orphan_dirs)
    assert not orphan_wire, "in CHANNEL_NAMES but not catalogued: {}".format(orphan_wire)


def test_every_catalogued_channel_has_a_label():
    """`CHANNEL_LABELS` is what the UI renders; a channel without one shows a
    raw slug where a name belongs."""
    from clawmetry.entitlements import ALL_CHANNELS, CHANNEL_LABELS

    missing = sorted(c for c in ALL_CHANNELS if not CHANNEL_LABELS.get(c))
    assert not missing, "catalogued with no CHANNEL_LABELS entry: {}".format(missing)


def test_the_three_lists_are_the_same_size():
    """A count mismatch means one of the assertions above is about to fire, and
    this says so in one number rather than a diff."""
    dirs, wire, catalogue = _lists()
    assert len(dirs) == len(wire) == len(catalogue), (
        "_CHANNEL_DIRS={} CHANNEL_NAMES={} ALL_CHANNELS={}".format(
            len(dirs), len(wire), len(catalogue))
    )


def test_the_guard_would_catch_a_half_wired_channel():
    """Proving the check goes RED rather than merely existing: a channel in the
    catalogue and nowhere else must fail the two membership tests."""
    dirs, wire, catalogue = _lists()
    pretend = catalogue | {"a-channel-that-ships-nowhere"}
    wire_n = {_norm(w) for w in wire}
    dirs_n = {_norm(d) for d in dirs}
    assert [c for c in pretend if _norm(c) not in wire_n] == \
        ["a-channel-that-ships-nowhere"]
    assert [c for c in pretend if _norm(c) not in dirs_n] == \
        ["a-channel-that-ships-nowhere"]
