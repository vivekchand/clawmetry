"""Bounded lexical workspace checks over declared mutation destinations.

No filesystem is opened. In particular, these checks cannot resolve symlinks,
shell expansions, mount points or a child process's actual working directory.
The result describes argument scope, never an observed filesystem write.
"""
from __future__ import annotations

import ntpath
import posixpath
import re
import shlex

_MAX_PATH_CHARS = 4096
_MAX_COMMAND_CHARS = 16000
_MAX_TOKENS = 96
_MAX_PATHS = 40
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
_UNRESOLVED = re.compile(r"[$%`~\x00\r\n]")


def _windows(path: str) -> bool:
    return bool(_WINDOWS_DRIVE.match(path) or path.startswith("\\\\")
                or re.match(r"^//[^/]+/[^/]+", path))


def _windows_path(path: str) -> str:
    if path.lower().startswith("\\\\?\\unc\\"):
        return "\\\\" + path[8:]
    if path.startswith("\\\\?\\"):
        return path[4:]
    return path


def path_scope(path, cwd, *, relative_base=None) -> str:
    """Return inside/outside/unknown using the root's own path semantics."""
    if not isinstance(path, str) or not isinstance(cwd, str):
        return "unknown"
    if not path or not cwd or max(len(path), len(cwd)) > _MAX_PATH_CHARS:
        return "unknown"
    if _UNRESOLVED.search(path) or _UNRESOLVED.search(cwd):
        return "unknown"
    if relative_base is not None and (not isinstance(relative_base, str)
            or len(relative_base) > _MAX_PATH_CHARS or _UNRESOLVED.search(relative_base)):
        return "unknown"
    try:
        if _windows(cwd):
            if cwd.startswith("\\\\.\\"):
                return "unknown"
            root = ntpath.normcase(ntpath.normpath(_windows_path(cwd)))
            drive, tail = ntpath.splitdrive(root)
            if drive.startswith("\\\\") and not tail:
                root += "\\"
                tail = "\\"
            if not drive or not tail.startswith("\\"):
                return "unknown"
            candidate = _windows_path(path)
            pdrive, ptail = ntpath.splitdrive(candidate)
            base = ntpath.join(root, relative_base) if relative_base else root
            if pdrive and not ptail.startswith(("/", "\\")):
                # D:relative is relative to that drive's own unknown cwd.
                if ntpath.normcase(pdrive) != ntpath.normcase(ntpath.splitdrive(base)[0]):
                    return "unknown"
            if candidate.startswith("\\\\.\\"):
                return "unknown"
            candidate = ntpath.normcase(ntpath.normpath(ntpath.join(base, candidate)))
            try:
                common = ntpath.commonpath((root, candidate))
            except ValueError:  # different absolute drives or UNC shares
                return "outside"
        else:
            if not cwd.startswith("/") or _windows(path) or "\\" in path:
                return "unknown"
            root = posixpath.normpath(cwd)
            base = posixpath.join(root, relative_base) if relative_base else root
            candidate = posixpath.normpath(posixpath.join(base, path))
            common = posixpath.commonpath((root, candidate))
        return "inside" if common == root else "outside"
    except (TypeError, ValueError):
        return "unknown"


def shell_mutation_paths(command: str) -> tuple:
    """Explicit POSIX-shell destinations, excluding read sources and code.

    This is deliberately a small parser, not a shell evaluator. Unsupported
    commands expose no destinations. Quotes are preserved by tokenization;
    expansions remain unresolved in path_scope. Work is capped before parsing.
    """
    if not isinstance(command, str) or not command or len(command) > _MAX_COMMAND_CHARS:
        return ()
    try:
        # Preserve quoting so a literal '>' passed to printf cannot become
        # an operator. Only unquoted punctuation has shell syntax here.
        lex = shlex.shlex(command, posix=False, punctuation_chars=";&|<>")
        lex.whitespace_split = True
        tokens = []
        for token in lex:
            tokens.append(token)
            if len(tokens) > _MAX_TOKENS:
                return ()
    except ValueError:
        return ()
    destinations = []
    segments = [[]]
    for token in tokens:
        if token in (";", "&&", "||", "|", "&"):
            segments.append([])
        else:
            segments[-1].append(token)
    for segment in segments:
        plain = []
        idx = 0
        while idx < len(segment):
            token = segment[idx]
            if token in (">", ">>", "<", "<<", "<<<"):
                if token in (">", ">>") and idx + 1 < len(segment):
                    target = segment[idx + 1]
                    if len(target) >= 2 and target[0] == target[-1] and target[0] in "\"'":
                        target = target[1:-1]
                    if target not in ("/dev/null", "/dev/stdout", "/dev/stderr"):
                        destinations.append(target)
                idx += 2
                continue
            if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
                token = token[1:-1]
            plain.append(token)
            idx += 1
        if not plain:
            continue
        # A command's data arguments are never interpreted as other commands.
        # Only a declared executable position (optionally prefixed by sudo)
        # selects a mutation verb.
        if plain[0] == "sudo":
            plain = plain[1:]
            while plain and plain[0].startswith("-"):
                option = plain.pop(0)
                if option in ("-u", "-g", "--user", "--group") and plain:
                    plain.pop(0)
        if not plain:
            continue
        verb = posixpath.basename(plain[0])
        args = plain[1:]
        operands = [arg for arg in args if not arg.startswith("-")]
        if verb in ("cp", "ln", "install"):
            # A copy's source is read; -t/--target-directory names its target.
            target = None
            for idx, arg in enumerate(args):
                if arg in ("-t", "--target-directory") and idx + 1 < len(args):
                    target = args[idx + 1]
                elif arg.startswith("--target-directory="):
                    target = arg.split("=", 1)[1]
            if target is not None:
                destinations.append(target)
            elif len(operands) >= 2:
                destinations.append(operands[-1])
        elif verb in ("rm", "rmdir", "mkdir", "touch", "unlink", "tee", "mv"):
            destinations.extend(operands)
        elif verb in ("chmod", "chown", "chgrp"):
            destinations.extend(operands[1:])  # first operand is mode/owner
        elif verb == "dd":
            destinations.extend(arg[3:] for arg in args if arg.startswith("of="))
    return tuple(dict.fromkeys(destinations))[:_MAX_PATHS]
