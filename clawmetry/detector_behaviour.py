"""Is this agent doing something it does not normally do?

Split out of :mod:`clawmetry.detectors`, which answers the other question: is
this agent stuck? These four read what the calls DID rather than how they
repeated, so they carry their own pattern tables and their own honesty rules,
and they are easier to review as one file than as the tail of a long one.

THE BOUND, repeated in every incident as ``evidence.observed =
"tool_arguments"``: these read tool-call ARGUMENTS, not syscalls. An agent that
shells out to a program which itself opens ``~/.ssh`` is invisible here. Two
rules keep that bound from becoming noise, both learned from real sessions:
heredoc bodies are stripped before matching, so a script that merely CONTAINS
the text ``csrutil disable`` is not an escalation, and privilege patterns are
ignored inside inspect-only commands such as ``grep`` or ``git log``.
"""
from __future__ import annotations

import re
from typing import Iterable, Optional

from clawmetry.detector_surface import _IPV4_RE, _cmd_sketch, _is_inspect_only, _redact_path


def _core():
    """The orchestrator's shared primitives, imported late.

    ``clawmetry.detectors`` imports this module to build its registry, so a
    module-level import back into it would be circular. The repo already uses
    this late-import shape where a leaf needs something from its parent.
    """
    from clawmetry import detectors as _d
    return _d


# ── Detector 5: file_blast_radius ────────────────────────────────────────────
# Destructive shell verbs, matched on the command text. Each entry is
# (label, regex). The label — never the command — is what reaches the incident.
_DESTRUCTIVE_PATTERNS = (
    ("recursive delete", re.compile(r"\brm\s+(?:-\w+\s+)*-\w*[rR]\w*", re.I)),
    ("history rewrite", re.compile(r"\bgit\s+(?:reset\s+--hard|clean\s+-\w*[fd])", re.I)),
    ("branch force-push", re.compile(r"\bgit\s+push\s+(?:\S+\s+)*--force", re.I)),
    ("disk write", re.compile(r"\bdd\s+.*\bof=", re.I)),
    ("recursive chmod/chown", re.compile(r"\b(?:chmod|chown)\s+-\w*[rR]", re.I)),
    ("mirror delete", re.compile(r"\brsync\b[^|;]*--delete", re.I)),
    ("truncate", re.compile(r"\btruncate\s+-s\s*0", re.I)),
)
# Roots where a recursive delete is not "cleaning node_modules" — it is the
# agent removing something it was never asked to touch.
_DANGEROUS_ROOTS = ("/", "/*", "~", "~/", "$HOME", "/etc", "/usr", "/var",
                    "/System", "/Users", "/home", "C:\\", "/Library")


def _destructive_hits(cmd: str) -> list:
    return [label for label, rx in _DESTRUCTIVE_PATTERNS if rx.search(cmd)]


def _deletes_a_root(cmd: str, paths) -> bool:
    """True when a recursive delete targets a home/system root rather than a
    subdirectory of the project."""
    if not _DESTRUCTIVE_PATTERNS[0][1].search(cmd):
        return False
    for p in paths:
        q = str(p).strip().rstrip("/") or "/"
        if q in ("", "/", "~", "$HOME") or q in _DANGEROUS_ROOTS:
            return True
        if q in ("/*", "~/*"):
            return True
    # ``rm -rf /`` with no token our path scanner kept still shows in the text.
    return bool(re.search(r"\brm\s+(?:-\w+\s+)*-\w*[rR]\w*\s+(?:/|~|\$HOME)\s*\*?\s*$",
                          cmd.strip(), re.I))


def file_blast_radius(events: Iterable[dict], session_id: str,
                      runtime: Optional[str] = None, *,
                      thresholds: Optional[dict] = None,
                      steps: Optional[list] = None,
                      facts: Optional[dict] = None) -> Optional[dict]:
    """Flag an unusually WIDE file footprint, or a destructive one.

    Two distinct failures share one detector because they are the same
    question asked at two scales:

    * **Wide** — the agent mutated more distinct files in this window than the
      cohort's baseline (or, with no baseline, than ``blast_files``). A
      refactor touching 200 files may be correct; it is also the shape of an
      agent that misread the task, and it is worth a human glance either way.
    * **Destructive** — a recursive delete at a home/system root, a hard
      reset, a force-push. Severity ``critical``: these are not recoverable by
      pressing Stop a minute later.

    Path-escape (writing outside the session's workspace) is reported when the
    caller passes ``facts["cwd"]``; without it we do not guess a root.
    """
    try:
        runtime, th, steps = _core()._prepare(events, steps, thresholds, runtime, session_id)
        root = str((facts or {}).get("cwd") or "").rstrip("/")
        write_tools = th.get("write_tools")
        files: dict = {}
        outside = []
        destructive: list = []
        root_delete = False
        write_calls = 0
        first_idx = None
        for st in steps:
            if st.get("kind") != "tool_call":
                continue
            cmd = st.get("cmd") or ""
            hits = _destructive_hits(cmd) if cmd else []
            if hits:
                destructive.extend(hits)
                if first_idx is None:
                    first_idx = st.get("i")
                if _deletes_a_root(cmd, st.get("paths") or ()):
                    root_delete = True
            if not (_core()._step_mutates(st, write_tools) or hits):
                continue
            write_calls += 1
            if first_idx is None:
                first_idx = st.get("i")
            for p in st.get("paths") or ():
                files.setdefault(p, st.get("tool") or "")
                if root and not str(p).startswith(("-", "~")) \
                        and str(p).startswith("/") and not str(p).startswith(root):
                    outside.append(p)

        limit = int(th["blast_files"])
        n_files = len(files)
        wide = n_files >= limit
        if not (wide or destructive):
            return None

        # Evidence NEVER carries a raw command or a full path: this dict is
        # written to loop_signals, folded into the heartbeat, and shipped to
        # the cloud device summary.
        evidence = {
            "distinct_files": n_files,
            "write_calls": write_calls,
            "threshold": limit,
            "threshold_source": th["sources"]["blast_files"],
            "baseline": th.get("baseline", {}).get("write_files"),
            "outside_workspace": len(set(outside)),
            "destructive": sorted(set(destructive))[:4],
            "samples": [_redact_path(p) for p in list(files)[:3]],
            "observed": "tool_arguments",
        }
        if root_delete:
            return _core()._incident(
                "file_blast_radius", session_id, runtime, "critical",
                f"{runtime}: recursive delete at a home or system root",
                "The agent ran a recursive delete targeting a home or system "
                "root rather than a project subdirectory. " + _core()._stop_hint(),
                evidence, first_idx)
        if destructive:
            label = sorted(set(destructive))[0]
            return _core()._incident(
                "file_blast_radius", session_id, runtime, "warning",
                f"{runtime}: {label} across {n_files} file(s)",
                f"The agent ran a {label} command. Destructive commands are "
                f"not undone by stopping the agent afterwards. " + _core()._stop_hint(),
                evidence, first_idx)
        return _core()._incident(
            "file_blast_radius", session_id, runtime, "warning",
            f"{runtime}: {n_files} files changed in one stretch",
            f"The agent mutated {n_files} distinct files (threshold {limit}) "
            f"without a pause. Wide edits are sometimes right and sometimes a "
            f"misread task. " + _core()._stop_hint(),
            evidence, first_idx)
    except Exception:
        return None


# ── Detector 6: credential_access ────────────────────────────────────────────
# (category label, path/command regex). The CATEGORY is what an incident
# publishes — never the path. "read an ssh private key" is the finding;
# ``/Users/dana/.ssh/id_ed25519_acme_prod`` is a leak in its own right.
_CREDENTIAL_PATTERNS = (
    ("ssh private key", re.compile(r"(?:^|/)\.ssh/(?:id_|.*_key$)|\bid_(?:rsa|ed25519|ecdsa|dsa)\b", re.I)),
    ("cloud credentials", re.compile(r"\.aws/credentials|\.aws/config|\.config/gcloud|"
                                     r"\.azure/|gcloud\s+auth|aws\s+configure|"
                                     r"\.kube/config", re.I)),
    ("environment file", re.compile(r"(?:^|[/\s])\.env(?:\.[\w-]+)?(?![\w./-])", re.I)),
    ("private certificate", re.compile(r"\.(?:pem|p12|pfx|jks)\b|private[_-]?key", re.I)),
    ("stored token file", re.compile(r"\.netrc|\.npmrc|\.pypirc|\.git-credentials|"
                                     r"\.docker/config\.json|credentials\.json", re.I)),
    ("keychain / secret store", re.compile(r"\bsecurity\s+find-(?:generic|internet)-password|"
                                           r"\bkeyring\b|\bvault\s+(?:read|kv)\b|"
                                           r"\bkubectl\s+get\s+secret", re.I)),
    # Deliberately narrow: a bare ``env``/``printenv`` as its own command.
    # ``os.environ`` inside a script is source code, and matching it made every
    # Python heredoc look like a secret dump on real sessions.
    ("environment dump", re.compile(r"(?:^|[;&|]\s*)(?:env|printenv)\s*(?:\||$)", re.I)),
    ("cloud metadata endpoint", re.compile(r"169\.254\.169\.254|metadata\.google\.internal", re.I)),
)
# ``.env.example`` / ``id_rsa.pub`` are templates and public halves, not secrets.
_CREDENTIAL_BENIGN = re.compile(r"\.env\.(?:example|sample|template)|\.pub\b|"
                                r"example\.pem|\.env\.d/", re.I)

# Categories that name a specific secret-bearing artefact. Only these justify
# the exfiltration reading when egress follows; an environment dump on its own
# is too common in ordinary shell work to escalate on.
_CREDENTIAL_STRONG = frozenset({
    "ssh private key", "cloud credentials", "environment file",
    "private certificate", "stored token file", "keychain / secret store",
    "cloud metadata endpoint",
})


def credential_access(events: Iterable[dict], session_id: str,
                      runtime: Optional[str] = None, *,
                      thresholds: Optional[dict] = None,
                      steps: Optional[list] = None,
                      facts: Optional[dict] = None) -> Optional[dict]:
    """Flag an agent reading secret-bearing files or dumping the environment.

    Reading a credential is not by itself wrong — plenty of legitimate tasks
    need ``.env``. What makes it worth surfacing is that nobody currently sees
    it happen at all, and that the same window sometimes also contains network
    egress, which is the shape of exfiltration rather than configuration.

    Severity is ``warning`` alone, ``critical`` when credential access is
    followed by egress to an external host in the same window. The critical
    wording says "reached the network after" — an observation — not
    "exfiltrated data", which we cannot see and will not claim.
    """
    try:
        runtime, th, steps = _core()._prepare(events, steps, thresholds, runtime, session_id)
        categories: dict = {}
        first_idx = None
        first_pos = None
        for pos, st in enumerate(steps):
            if st.get("kind") != "tool_call":
                continue
            haystack = " ".join(list(st.get("paths") or ()) + [st.get("cmd") or ""])
            if not haystack.strip():
                continue
            if _CREDENTIAL_BENIGN.search(haystack):
                haystack = _CREDENTIAL_BENIGN.sub(" ", haystack)
            for label, rx in _CREDENTIAL_PATTERNS:
                if rx.search(haystack):
                    categories[label] = categories.get(label, 0) + 1
                    if first_idx is None:
                        first_idx = st.get("i")
                        first_pos = pos
        if not categories:
            return None

        # Egress AFTER the first credential touch, in the same window.
        egress_after = []
        for st in steps[(first_pos or 0) + 1:]:
            for h in st.get("hosts") or ():
                egress_after.append(h)
        egress_after = sorted(set(egress_after))

        labels = sorted(categories)
        strong = [c for c in labels if c in _CREDENTIAL_STRONG]
        evidence = {
            "categories": labels,
            "strong_categories": strong,
            "accesses": sum(categories.values()),
            "egress_after": egress_after[:5],
            "observed": "tool_arguments",
            # No paths, no commands. The category IS the finding.
            "redacted": "paths and commands are deliberately not recorded",
        }
        # Rank a named secret above a generic environment dump in the headline.
        head = (strong or labels)[0]
        more = f" and {len(labels) - 1} more" if len(labels) > 1 else ""
        if egress_after and not strong:
            # Egress after a bare `env` is not the exfiltration shape; say what
            # was seen without the escalation.
            return _core()._incident(
                "credential_access", session_id, runtime, "info",
                f"{runtime}: dumped the environment",
                f"The agent printed its environment variables and later "
                f"contacted {len(egress_after)} external host(s). Common in "
                f"ordinary shell work, surfaced so it is not invisible. "
                + _core()._stop_hint(),
                evidence, first_idx)
        if not strong:
            return _core()._incident(
                "credential_access", session_id, runtime, "info",
                f"{runtime}: dumped the environment",
                "The agent printed its environment variables. " + _core()._stop_hint(),
                evidence, first_idx)
        if egress_after:
            return _core()._incident(
                "credential_access", session_id, runtime, "critical",
                f"{runtime}: read {head}{more}, then reached {len(egress_after)} "
                f"external host(s)",
                f"The agent opened {head}{more} and afterwards contacted "
                f"{', '.join(egress_after[:3])}. That ordering is worth a look "
                f"before it continues. " + _core()._stop_hint(),
                evidence, first_idx)
        return _core()._incident(
            "credential_access", session_id, runtime, "warning",
            f"{runtime}: read {head}{more}",
            f"The agent opened {head}{more}. Plenty of tasks legitimately need "
            f"this; it is surfaced so the choice is yours rather than "
            f"invisible. " + _core()._stop_hint(),
            evidence, first_idx)
    except Exception:
        return None


# ── Detector 7: network_egress ───────────────────────────────────────────────
def network_egress(events: Iterable[dict], session_id: str,
                   runtime: Optional[str] = None, *,
                   thresholds: Optional[dict] = None,
                   steps: Optional[list] = None,
                   facts: Optional[dict] = None) -> Optional[dict]:
    """Flag network destinations this agent has not used before.

    "First-time egress" only means something against a memory of what came
    before, so this detector fires on one of three grounds and says which:

    * ``first_time`` — hosts absent from the cohort's learned host set. Needs a
      baseline; without one we do not pretend every host is new.
    * ``fanout`` — more distinct external hosts in one window than
      ``egress_hosts``, which is unusual regardless of history.
    * ``raw_address`` — a bare IP literal instead of a hostname. Package
      registries and APIs have names; IPs in an agent's command line usually
      mean something hand-assembled.

    Contacting a host is not an accusation. The incident says where it went.
    """
    try:
        runtime, th, steps = _core()._prepare(events, steps, thresholds, runtime, session_id)
        known = th.get("known_hosts") or frozenset()
        hosts: dict = {}
        first_idx = None
        for st in steps:
            for h in st.get("hosts") or ():
                if h not in hosts:
                    hosts[h] = st.get("i")
                    if first_idx is None:
                        first_idx = st.get("i")
        if not hosts:
            return None

        distinct = sorted(hosts)
        new_hosts = [h for h in distinct if h not in known] if known else []
        raw_ips = [h for h in distinct if _IPV4_RE.match(h)]
        fanout_limit = int(th["egress_hosts"])
        fanout = len(distinct) >= fanout_limit

        if new_hosts:
            ground, sev = "first_time", "warning"
        elif fanout:
            ground, sev = "fanout", "warning"
        elif raw_ips:
            ground, sev = "raw_address", "info"
        else:
            return None

        evidence = {
            "ground": ground,
            "distinct_hosts": len(distinct),
            "hosts": distinct[:8],
            "new_hosts": new_hosts[:8],
            "raw_addresses": raw_ips[:4],
            "known_host_count": len(known),
            "threshold": fanout_limit,
            "observed": "tool_arguments",
        }
        if ground == "first_time":
            shown = ", ".join(new_hosts[:3])
            return _core()._incident(
                "network_egress", session_id, runtime, sev,
                f"{runtime}: first contact with {shown}"
                + (f" +{len(new_hosts) - 3} more" if len(new_hosts) > 3 else ""),
                f"This agent has not reached {shown} in the "
                f"{len(known)} host(s) seen from it before now. " + _core()._stop_hint(),
                evidence, hosts.get(new_hosts[0]))
        if ground == "fanout":
            return _core()._incident(
                "network_egress", session_id, runtime, sev,
                f"{runtime}: reached {len(distinct)} external hosts",
                f"The agent contacted {len(distinct)} distinct external hosts "
                f"in one stretch (threshold {fanout_limit}). " + _core()._stop_hint(),
                evidence, first_idx)
        return _core()._incident(
            "network_egress", session_id, runtime, sev,
            f"{runtime}: connected to a raw IP address",
            f"The agent connected to {raw_ips[0]} by address rather than by "
            f"name. " + _core()._stop_hint(),
            evidence, hosts.get(raw_ips[0]))
    except Exception:
        return None


# ── Detector 8: privilege_change ─────────────────────────────────────────────
# (label, regex, critical?) — critical entries disable a protection or grant
# standing privilege; the rest are ordinary elevation worth seeing.
_PRIVILEGE_PATTERNS = (
    ("disabled a system protection",
     re.compile(r"\bcsrutil\s+disable|\bspctl\s+--master-disable|"
                r"\bsetenforce\s+0|\bufw\s+disable|"
                r"\bdefaults\s+write\s+/Library", re.I), True),
    ("edited sudoers",
     re.compile(r"\bvisudo\b|/etc/sudoers", re.I), True),
    ("piped a password into sudo",
     re.compile(r"\becho\s+[^|]*\|\s*sudo\s+-S\b|\bsudo\s+-S\b", re.I), True),
    ("world-writable permissions",
     re.compile(r"\bchmod\s+(?:-\w+\s+)*(?:777|a\+rwx|o\+w)\b", re.I), True),
    ("setuid bit",
     re.compile(r"\bchmod\s+(?:-\w+\s+)*[ug]?\+s\b|\bsetcap\b", re.I), True),
    ("ran a command as root",
     re.compile(r"(?:^|[;&|]\s*|\s)(?:sudo|doas)\s+(?!-S)|(?:^|\s)su\s+-", re.I), False),
    ("changed file ownership",
     re.compile(r"\bchown\s+(?:-\w+\s+)*root\b", re.I), False),
    ("installed a launch/system service",
     re.compile(r"\blaunchctl\s+(?:load|bootstrap)|\bsystemctl\s+(?:enable|start)|"
                r"\bcrontab\s+-", re.I), False),
)


def privilege_change(events: Iterable[dict], session_id: str,
                     runtime: Optional[str] = None, *,
                     thresholds: Optional[dict] = None,
                     steps: Optional[list] = None,
                     facts: Optional[dict] = None) -> Optional[dict]:
    """Flag an agent elevating privilege or weakening a protection.

    An agent that reaches for ``sudo`` mid-task has left the shape of work its
    operator approved, whether or not the command itself is reasonable. The
    critical tier is reserved for the ones that OUTLIVE the session: a disabled
    protection, an edited sudoers file, a setuid bit, world-writable
    permissions. Stopping the agent does not undo any of those.
    """
    try:
        runtime, th, steps = _core()._prepare(events, steps, thresholds, runtime, session_id)
        found: dict = {}
        critical: list = []
        first_idx = None
        sketch = ""
        for st in steps:
            if st.get("kind") != "tool_call":
                continue
            cmd = st.get("cmd") or ""
            if not cmd or _is_inspect_only(cmd):
                continue  # a mention inside a search is not an escalation
            for label, rx, is_crit in _PRIVILEGE_PATTERNS:
                if rx.search(cmd):
                    found[label] = found.get(label, 0) + 1
                    if is_crit:
                        critical.append(label)
                    if first_idx is None:
                        first_idx = st.get("i")
                        sketch = _cmd_sketch(cmd)
        if not found:
            return None

        labels = sorted(found)
        evidence = {
            "patterns": labels,
            "matches": sum(found.values()),
            "irreversible": sorted(set(critical)),
            # Program + first flag only; a full command line can carry a token.
            "command_sketch": sketch,
            "observed": "tool_arguments",
        }
        if critical:
            head = sorted(set(critical))[0]
            return _core()._incident(
                "privilege_change", session_id, runtime, "critical",
                f"{runtime}: {head}",
                f"The agent {head}. This outlives the session: stopping the "
                f"agent does not undo it. " + _core()._stop_hint(),
                evidence, first_idx)
        head = labels[0]
        more = f" and {len(labels) - 1} more" if len(labels) > 1 else ""
        return _core()._incident(
            "privilege_change", session_id, runtime, "warning",
            f"{runtime}: {head}{more}",
            f"The agent {head}{more}. Elevation mid-task is worth confirming "
            f"was part of the plan. " + _core()._stop_hint(),
            evidence, first_idx)
    except Exception:
        return None
