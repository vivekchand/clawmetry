"""Resolve installed harnesses when a background service has a minimal PATH."""
import os
import shutil


def find_claude_cli():
    """Prefer PATH, then Claude's documented native per-user installation.

    launchd does not inherit shell profiles. The native installer uses
    ~/.local/bin/claude (claude.exe on Windows), so no shell startup script
    needs to execute merely to discover the user's existing harness.
    https://support.claude.com/en/articles/14554922-claude-code-user-faq
    """
    found = shutil.which("claude")
    if found:
        return found
    name = "claude.exe" if os.name == "nt" else "claude"
    candidate = os.path.expanduser(os.path.join("~", ".local", "bin", name))
    if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
        return candidate
    return None
