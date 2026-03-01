"""Provider registry for ClawMetry data backends."""
from __future__ import annotations
import logging
import os
from typing import Dict, Optional, Type

from clawmetry.providers.base import ClawMetryDataProvider

logger = logging.getLogger("clawmetry.providers")

_registry: Dict[str, Type[ClawMetryDataProvider]] = {}
_active_provider: Optional[ClawMetryDataProvider] = None


def register_provider(name: str, cls: Type[ClawMetryDataProvider]) -> None:
    _registry[name] = cls


def get_provider(name: str, **kwargs) -> ClawMetryDataProvider:
    if name not in _registry:
        raise ValueError(f"Unknown provider: {name!r}. Available: {list(_registry)}")
    return _registry[name](**kwargs)


def get_active_provider() -> Optional[ClawMetryDataProvider]:
    return _active_provider


def set_active_provider(provider: ClawMetryDataProvider) -> None:
    global _active_provider
    _active_provider = provider


def init_providers(sessions_dir: str = "", log_dir: str = "", workspace: str = "",
                   metrics_file: str = "", fleet_db: str = "") -> ClawMetryDataProvider:
    """
    Initialize built-in providers and set the active one.
    Called once at dashboard startup after path detection.
    """
    from clawmetry.providers.local import LocalDataProvider
    register_provider("local", LocalDataProvider)

    # Load 3rd-party providers via entry points
    try:
        import importlib.metadata
        for ep in importlib.metadata.entry_points(group="clawmetry.providers"):
            try:
                cls = ep.load()
                register_provider(ep.name, cls)
                logger.info(f"Loaded provider plugin: {ep.name!r}")
            except Exception as e:
                logger.warning(f"Failed to load provider {ep.name!r}: {e}")
    except Exception:
        pass

    provider_name = os.environ.get("CLAWMETRY_PROVIDER", "local")
    if provider_name not in _registry:
        provider_name = "local"

    provider = _registry[provider_name](
        sessions_dir=sessions_dir,
        log_dir=log_dir,
        workspace=workspace,
        metrics_file=metrics_file,
        fleet_db=fleet_db,
    )
    set_active_provider(provider)
    return provider
