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


# Characters that can only ever move a path out of its base directory.
# ``\`` is a separator on Windows; ``\0`` truncates the path at the libc
# boundary, so a suffix check upstream can be bypassed with it.
_SEPARATORS = ("/", "\\", "\x00")


def is_safe_path_component(value):
    """True when ``value`` can only name an entry inside its base directory.

    Rejects separators, NUL, and any ``..`` run. This is the *first* of two
    checks a request value needs before it reaches the filesystem; the
    second is :func:`is_path_within` on the joined result, which also
    contains a symlink pointing out of the base.

    Both are needed. This check alone still allows a link inside the base
    to be followed outward, and ``is_path_within`` alone trusts the OS to
    resolve ``..`` against real directories — true on POSIX, but Windows
    collapses ``..`` lexically before the filesystem ever sees the path, so
    a non-existent first segment is no obstacle there.
    """
    if not isinstance(value, str) or not value:
        return False
    if ".." in value:
        return False
    return not any(c in value for c in _SEPARATORS)
