"""Declared built-in robot history destinations, never live-device detection."""

import logging
import re


BUILTIN_HARDWARE = (("jumper", "Jumper"), ("asimov_1", "Asimov 1"))


def hardware_navigation():
    """Return fresh metadata; applications cannot mutate the shared catalog."""
    return [{"id": identity, "label": label, "href": "/physical-ai?hardware=" + identity}
            for identity, label in BUILTIN_HARDWARE]


def workbench_navigation(entries):
    """Keep one declared installed default and validated optional destinations."""
    navigation = entries if isinstance(entries, list) else []
    advanced, other = [], []
    for entry in navigation[:8]:
        if not isinstance(entry, dict):
            continue
        if entry.get("view_group") != "physical_ai":
            other.append(entry)
            continue
        href = entry.get("href")
        if isinstance(href, str) and re.fullmatch(r"/[a-zA-Z0-9][a-zA-Z0-9/_-]*", href) and href != "/physical-ai":
            if not any(link["href"] == href for link in advanced):
                advanced.append({"href": href, "label": str(entry.get("label") or "Robot workbench")[:40]})
    primary = {"label": "Physical AI", "href": advanced[0]["href"] if advanced else "/physical-ai", "view_group": "physical_ai"}
    return [primary] + other, advanced


def snapshot_metadata():
    """Use an explicit local plugin declaration, never package-name inference."""
    declared = {}
    try:
        from clawmetry import extensions
        declared = extensions.call("ui.snapshot", {}, default={})
    except Exception:
        logging.getLogger("clawmetry.physical_ai").warning("Installed workbench navigation is unavailable")
    entries = declared.get("navigation", []) if isinstance(declared, dict) else []
    navigation, _ = workbench_navigation(entries)
    return {"navigation": navigation[:1], "physical_ai_hardware": hardware_navigation()}
