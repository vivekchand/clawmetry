"""CI guard against the #2251-class bug.

Two route modules registering Flask `Blueprint`s with the same `name`
silently drops the second one at `app.register_blueprint` time, making
the route unreachable at runtime with no visible error.

This bit OSS 0.12.350-0.12.352 when `routes/meta.py` and
`routes/otel_export.py` both defined Blueprint('otel_export'), shadowing
`/api/export/traces` to a 404. Fixed in #2251 / PyPI 0.12.353.

The two tests below would have caught that at OSS CI time.
"""

from __future__ import annotations

import importlib
import pkgutil

from flask import Blueprint, Flask


def _discover_oss_blueprints() -> list[tuple[str, Blueprint]]:
    """Yield (qualified-name, Blueprint) for every Blueprint exported by routes/*."""
    import routes  # noqa: WPS433 — intentional runtime import to walk the package

    bps: list[tuple[str, Blueprint]] = []
    for _, mod_name, _ in pkgutil.iter_modules(routes.__path__):
        module = importlib.import_module(f"routes.{mod_name}")
        for attr_name in dir(module):
            value = getattr(module, attr_name)
            if isinstance(value, Blueprint):
                bps.append((f"routes.{mod_name}.{attr_name}", value))
    return bps


def test_no_duplicate_blueprint_names() -> None:
    """Every OSS Blueprint must have a unique `name` attribute."""
    by_name: dict[str, list[str]] = {}
    for path, bp in _discover_oss_blueprints():
        by_name.setdefault(bp.name, []).append(path)

    duplicates = {name: paths for name, paths in by_name.items() if len(paths) > 1}
    assert not duplicates, (
        "Duplicate Blueprint name(s) found — Flask silently drops the second on "
        "register_blueprint, making routes unreachable at runtime (see #2251 / "
        "reference_duplicate_blueprint_name_silent_route_drop.md): "
        f"{duplicates}"
    )


def test_all_oss_blueprints_register_together() -> None:
    """Every OSS Blueprint must register cleanly into a single Flask app.

    Catches duplicate names, route-rule collisions, and endpoint-name
    collisions across blueprints — anything Flask rejects at registration.
    """
    app = Flask(__name__)
    for path, bp in _discover_oss_blueprints():
        try:
            app.register_blueprint(bp)
        except Exception as exc:  # noqa: BLE001 — re-raise with provenance
            raise AssertionError(
                f"{path} failed to register: {exc}. "
                "Most likely a duplicate Blueprint name or route-rule collision (see #2251)."
            ) from exc
