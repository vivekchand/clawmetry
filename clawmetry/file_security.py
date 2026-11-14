"""Shared containment check for filesystem-backed HTTP responses."""
import os


def is_path_within(path, root):
    """Compare path components, resolving both sides so linked roots work.

    Resolve the candidate too: a link inside the root must not grant access
    to files outside it. commonpath also handles filesystem roots and drives.
    """
    try:
        if not isinstance(path, str) or not isinstance(root, str):
            return False
        if "\0" in path or "\0" in root:
            return False
        base = os.path.normcase(os.path.realpath(os.path.abspath(root)))
        full = os.path.normcase(os.path.realpath(os.path.abspath(path)))
        return os.path.commonpath((base, full)) == base
    except (OSError, ValueError, TypeError):
        return False
