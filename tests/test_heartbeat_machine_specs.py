"""The heartbeat carries enough to tell one of your machines from another.

Founder live-hit 2026-08-22 on an 18-node account: "it's really confusing to
know who owns this instance". Every identifying field had been moved into the
E2E-encrypted snapshot, which can only be opened with THAT node's key — the
very thing you walk to the machine to fetch. So the fleet card had nothing to
show but an opaque node id.

The line drawn here, and pinned by these tests: specs you could read off a
sticker on the case travel in cleartext; anything the machine can be REACHED
at does not.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clawmetry import sync  # noqa: E402


def test_specs_identify_this_machine():
    specs = sync._machine_specs()
    assert specs.get("hostname"), "a fleet card with no hostname identifies nothing"
    assert specs.get("os"), "OS is how you tell the Linux box from the laptop"
    assert specs.get("arch")
    assert isinstance(specs.get("cpu_count"), int) and specs["cpu_count"] >= 1


def test_specs_never_carry_a_network_address():
    """The privacy line. Local IPs stay in the E2E snapshot."""
    specs = sync._machine_specs()
    assert "local_ips" not in specs
    assert "ip" not in specs
    blob = repr(specs)
    for marker in ("192.168.", "10.0.", "172.16."):
        assert marker not in blob, f"{marker} address leaked into the plaintext heartbeat"


def test_node_meta_carries_specs_alongside_routing_fields():
    meta = sync._build_node_meta()
    assert meta.get("hostname")
    assert meta.get("os")
    # Routing/entitlement fields must survive the addition.
    assert "pro_version" in meta
    assert "auto_update" in meta
    assert "local_ips" not in meta


def test_os_is_named_the_way_a_person_names_it(monkeypatch):
    """"Ubuntu 24.04", not "Linux 6.8.0-45-generic" — every Linux box gives
    roughly the same kernel string, which identifies nothing."""
    monkeypatch.setattr(sync.platform, "system", lambda: "Linux")
    release = 'NAME="Ubuntu"\nVERSION_ID="24.04"\nPRETTY_NAME="Ubuntu 24.04.1 LTS"\n'

    import builtins

    real_open = builtins.open

    def fake_open(path, *a, **k):
        if str(path) == "/etc/os-release":
            import io

            return io.StringIO(release)
        return real_open(path, *a, **k)

    monkeypatch.setattr(builtins, "open", fake_open)
    specs = sync._machine_specs()
    assert specs["os"] == "Ubuntu"
    assert specs["os_release"] == "24.04"


def test_unreadable_os_release_omits_rather_than_guesses(monkeypatch):
    """A card reading "unknown - 0 GB" is worse than one showing nothing."""
    monkeypatch.setattr(sync.platform, "system", lambda: "Linux")

    import builtins

    real_open = builtins.open

    def boom(path, *a, **k):
        if str(path) == "/etc/os-release":
            raise OSError("no such file")
        return real_open(path, *a, **k)

    monkeypatch.setattr(builtins, "open", boom)
    monkeypatch.setattr(sync, "_total_ram_gb", lambda: 0.0)
    specs = sync._machine_specs()
    assert "ram_gb" not in specs, "0 GB must be omitted, not reported"
    assert specs.get("os") in (None, "Linux") or specs["os"], "never a blank value"
    assert "" not in specs.values()


def test_specs_never_raise_on_a_hostile_platform(monkeypatch):
    """The heartbeat must keep flowing even where every probe fails."""
    monkeypatch.setattr(sync.platform, "system", lambda: (_ for _ in ()).throw(RuntimeError("nope")))
    monkeypatch.setattr(sync.platform, "machine", lambda: (_ for _ in ()).throw(RuntimeError("nope")))
    specs = sync._machine_specs()
    assert isinstance(specs, dict)
    meta = sync._build_node_meta()
    assert isinstance(meta, dict)


def test_ram_reader_is_shared_with_the_machine_popup(monkeypatch):
    """One reader, so the fleet card and the Machine popup cannot disagree
    about how much memory the box has."""
    monkeypatch.setattr(sync, "_total_ram_gb", lambda: 64.0)
    assert sync._machine_specs().get("ram_gb") == 64.0
    items = {i["label"]: i["value"] for i in sync._build_machine_info()["items"]}
    assert items.get("RAM") == "64.0 GB"


def test_machine_popup_still_carries_the_local_ips():
    """The addresses did not disappear — they moved nowhere. They are still in
    the E2E-encrypted snapshot, readable only with this node's key."""
    labels = {i["label"] for i in sync._build_machine_info()["items"]}
    assert "Local IPs" in labels or "IP" in labels
