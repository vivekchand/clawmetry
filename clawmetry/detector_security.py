"""Action signatures which otherwise run only when the Security page opens."""
from __future__ import annotations

import posixpath
import re
import shlex

from clawmetry.detector_surface import _is_shell_tool, _strip_heredocs
from clawmetry.security_signatures import _scan_events_for_threats

# Credential, injection, file and privilege findings have dedicated detectors.
# These complementary action classes retain one aggregate finding per window.
_SHELLS = frozenset({"bash", "sh", "dash", "zsh", "ksh"})
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_CONTROL = frozenset({"if", "then", "else", "elif", "fi", "for", "while", "until", "do", "done", "case", "esac", "function", "{"})
_SOURCE_PROGRAMS = frozenset({"python", "python3", "node", "perl", "ruby", "powershell", "pwsh", "cmd"})
_RULES_BY_VERB = {
    "nc": {"SEC-001"}, "ncat": {"SEC-001"}, "netcat": {"SEC-001"},
    "mkfifo": {"SEC-001"}, "socat": {"SEC-001"},
    "ssh": {"SEC-005"}, "scp": {"SEC-005"}, "rsync": {"SEC-005"},
    "xmrig": {"SEC-006"}, "cpuminer": {"SEC-006"},
    "pip": {"SEC-008"}, "pip3": {"SEC-008"}, "npm": {"SEC-008"},
    "crontab": {"SEC-010"}, "systemctl": {"SEC-010"},
    "nmap": {"SEC-011"}, "masscan": {"SEC-011"}, "netstat": {"SEC-011"}, "ss": {"SEC-011"},
    "gdb": {"SEC-014"}, "strace": {"SEC-014"}, "ptrace": {"SEC-014"}, "cat": {"SEC-014"},
}
CONTINUOUS_RULES = frozenset(rule for rules in _RULES_BY_VERB.values() for rule in rules)


def _unquote(token):
    return token[1:-1] if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'" else token


def _substitution_end(text, start):
    stack, quote, i = [""], "", start + 2
    while i < len(text):
        c = text[i]
        if c == "\\" and quote != "'":
            i += 2
            continue
        if quote == "'":
            if c == "'":
                quote = ""
        elif text.startswith("$(", i):
            stack.append(quote)
            quote = ""
            i += 2
            continue
        elif c in "\"'":
            quote = "" if quote == c else c if not quote else quote
        elif not quote and c == "(":
            stack.append(quote)
        elif not quote and c == ")":
            quote = stack.pop()
            if not stack:
                return i
        i += 1
    return None


def _extract_substitutions(text):
    """Separate executable substitutions from single-quoted data."""
    scripts, output, quote, i = [], [], "", 0
    while i < len(text):
        c = text[i]
        if c == "\\" and quote != "'" and i + 1 < len(text):
            following = text[i + 1]
            # shlex non-POSIX mode retains quote provenance but does not
            # interpret escapes. Preserve escaped operators as data before
            # tokenization, and join escaped newlines as the shell does.
            output.append("" if following == "\n" else "__escaped_semicolon__" if following == ";"
                          else "__literal__" if following in "&|<>()" else text[i:i + 2])
            i += 2
            continue
        if quote != "'" and text.startswith("$(", i):
            end = _substitution_end(text, i)
            if end is None:
                return text, scripts, False
            scripts.append(text[i + 2:end])
            output.append("__substitution__")
            i = end + 1
            continue
        if quote != "'" and c == "`":
            end = i + 1
            while end < len(text) and (text[end] != "`" or text[end - 1] == "\\"):
                end += 1
            if end >= len(text):
                return text, scripts, False
            scripts.append(text[i + 1:end])
            output.append("__substitution__")
            i = end + 1
            continue
        if c in "\"'":
            quote = "" if quote == c else c if not quote else quote
        output.append(c)
        i += 1
    return "".join(output), scripts, not quote


def _executables(command, depth=0):
    """Bounded declared executable slots, not a general shell evaluator.

    Unknown control syntax and non-shell program source are coverage gaps.
    Quoting is retained until operators have been classified.
    """
    if depth > 4 or not isinstance(command, str) or len(command) > 8192:
        return [], False
    if "<<" in command:
        return [], False  # heredoc language and expansion need native parsing
    command, scripts, complete = _extract_substitutions(command)
    try:
        lexer = shlex.shlex(command, posix=False, punctuation_chars=";&|<>()\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        tokens = []
        for token in lexer:
            tokens.append(token)
            if len(tokens) > 256:
                return [], False
    except ValueError:
        return [], False
    commands = []
    for script in scripts[:32]:
        inner, inspected = _executables(script, depth + 1)
        commands.extend(inner)
        complete = complete and inspected
    segments = [[]]
    for token in tokens:
        if token and all(c in ";&|\n()" for c in token):
            segments.append([])
        else:
            segments[-1].append(token)
    for segment in segments[:64]:
        plain, redirects, assignments = [], [], []
        i = 0
        while i < len(segment):
            token = segment[i]
            if token and token[0] in "<>":
                if i + 1 >= len(segment):
                    complete = False
                    break
                redirects.append(_unquote(segment[i + 1]))
                i += 2
                continue
            plain.append(_unquote(token))
            i += 1
        if not plain:
            continue
        if plain[0] == "env":
            plain = plain[1:]
            while plain and plain[0] in ("-i", "--ignore-environment", "--"):
                plain.pop(0)
        while plain and _ASSIGNMENT.match(plain[0]):
            assignments.append(plain.pop(0))
        if plain and plain[0] in ("sudo", "command", "exec", "nohup"):
            wrapper = plain.pop(0)
            while plain and plain[0].startswith("-"):
                option = plain.pop(0)
                if wrapper == "sudo" and option in ("-u", "-g", "--user", "--group") and plain:
                    plain.pop(0)
        if not plain:
            complete = False
            continue
        verb = posixpath.basename(plain[0].replace("\\", "/")).lower().removesuffix(".exe")
        if verb in _CONTROL or "$" in verb or "`" in verb:
            complete = False
            continue
        if verb in _SHELLS:
            inline = False
            for index, arg in enumerate(plain[1:], 1):
                if arg.startswith("-") and not arg.startswith("--") and "c" in arg[1:]:
                    inline = True
                    inner, inspected = _executables(plain[index + 1] if index + 1 < len(plain) else "", depth + 1)
                    commands.extend(inner)
                    complete = complete and inspected
                    break
            if not inline:
                complete = False  # stdin or a script supplies uninspected code
        elif verb == "eval":
            inner, inspected = _executables(" ".join(plain[1:]), depth + 1)
            commands.extend(inner)
            complete = complete and inspected
        elif verb == "find":
            for index, arg in enumerate(plain):
                if arg in ("-exec", "-execdir", "-ok", "-okdir"):
                    tail = plain[index + 1:]
                    end = next((j for j, v in enumerate(tail) if v in (";", "__escaped_semicolon__", "+")), None)
                    if end is None:
                        complete = False
                        continue
                    tail = tail[:end]
                    inner, inspected = _executables(" ".join(shlex.quote(v) for v in tail), depth + 1)
                    commands.extend(inner)
                    complete = complete and inspected
        elif verb in _SOURCE_PROGRAMS or verb == "xargs":
            complete = False
        commands.append(dict(verb=verb, argv=plain, redirects=redirects, assignments=assignments))
    return commands[:256], complete and len(scripts) <= 32 and len(segments) <= 64


def _command_hits(command):
    commands, complete = _executables(_strip_heredocs(command))
    hits = []
    for executable in commands:
        verb, argv = executable["verb"], executable["argv"]
        rules = set(_RULES_BY_VERB.get(verb, ()))
        if verb == "crontab" and any(arg in ("-l", "--list") for arg in argv[1:]):
            rules.discard("SEC-010")
        if any(value.startswith("LD_PRELOAD=") for value in executable["assignments"]):
            rules.add("SEC-014")
        if any(path.startswith("/dev/tcp/") for path in executable["redirects"]):
            hits.append({"rule_id": "SEC-001", "severity": "critical"})
        if not rules:
            continue
        # Only the known executable's own arguments can satisfy its signature.
        text = " ".join(executable["assignments"] + [verb] + argv[1:])
        matched, _ = _scan_events_for_threats([dict(type="EXEC", detail=text)])
        hits.extend(hit for hit in matched if hit["rule_id"] in rules)
    return hits, complete


def security_threat(events, session_id, runtime=None, *, thresholds=None, steps=None, facts=None, inspection=None):
    from clawmetry import detectors as d
    runtime, _, steps = d._prepare(events, steps, thresholds, runtime, session_id)
    evlist = d._chronological(events)
    matches = []
    matched_indices = set()
    critical_indices = set()
    uninspected_indices = set()
    first = None
    for step in steps:
        if step.get("kind") != "tool_call":
            continue
        if not _is_shell_tool(step.get("tool") or ""):
            continue  # code written by an edit tool is data, not execution
        text = step.get("cmd") or ""
        if not text:
            continue
        index = step.get("i")
        if isinstance(index, int) and 0 <= index < len(evlist):
            event = evlist[index]
            calls = d._iter_tool_calls_from_data(str(event.get("event_type") or "").lower(),
                                                 d._coerce_dict(event.get("data")))
            for candidate in calls[:40]:
                args = candidate.get("args")
                if (candidate.get("tool") == step.get("tool") and d._args_hash(args) == step.get("args_hash")
                        and isinstance(args, dict) and any(key in args for key in ("code", "input"))
                        and not any(key in args for key in ("command", "cmd", "shell_command", "bash_command", "script", "commands", "argv", "args"))):
                    # An orchestration tool named exec may run JavaScript or
                    # Python code. Those source strings are not shell syntax.
                    uninspected_indices.add(index)
                    text = ""
                    break
        if not text:
            continue
        hits, inspected = _command_hits(text)
        if not inspected:
            uninspected_indices.add(step.get("i"))
        if hits:
            matches.extend(hits)
            matched_indices.add(step.get("i"))
            if any(hit["severity"] == "critical" for hit in hits):
                critical_indices.add(step.get("i"))
            if first is None:
                first = step.get("i")
    if not matches:
        if not uninspected_indices:
            return None
        incident = d._incident(
            "inspection_incomplete", session_id, runtime, "info",
            "Some command syntax was not inspected",
            "The bounded command parser could not inspect this syntax. This is a coverage gap, not evidence of an attack.",
            {"reasons": ["shell_syntax_uninspected"], "limited_payloads": len(uninspected_indices),
             "observed": "tool_arguments", "policy_eligible": False}, min(uninspected_indices))
        incident["_evidence_step_indices"] = sorted(uninspected_indices)
        return incident
    severity = "critical" if any(m["severity"] == "critical" for m in matches) else "warning"
    incident = d._incident(
        "security_threat", session_id, runtime, severity,
        "Tool arguments match a security action signature",
        "Review the recorded call. A signature match does not prove execution or malicious intent.",
        {"rules": sorted({m["rule_id"] for m in matches}),
         "execution_scope": "declared_executable", "inspection_complete": not uninspected_indices,
         "matches": len(matches), "observed": "tool_arguments"}, first)
    incident["_evidence_step_indices"] = sorted(critical_indices or matched_indices)
    return incident
