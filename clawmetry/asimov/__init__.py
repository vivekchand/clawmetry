"""Free, read-only Asimov evidence collection, with optional Menlo SDK support."""


def observe(robot, **kwargs):
    """Trace an existing SDK Robot without taking ownership of its connection."""
    from .sdk import observe as attach

    return attach(robot, **kwargs)


def import_recording(path, **kwargs):
    """Import an official Menlo recording without installing Menlo dependencies."""
    from .recording import import_recording as load

    return load(path, **kwargs)


__all__ = ["import_recording", "observe"]
