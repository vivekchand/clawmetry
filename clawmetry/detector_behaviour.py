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

from clawmetry.detector_payload import (
    _SEGMENT_SPLIT_RE, SECRET_VALUE_OWNERS, _segment_write_hosts, host_owned_by,
)
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
    # Deliberately narrow: a bare ``env``/``printenv`` as its own statement.
    # ``os.environ`` inside a script is source code, and matching it made every
    # Python heredoc look like a secret dump on real sessions. The statement
    # may end at a pipe, ``;``, ``&&`` or end of line: ``id; env; cat ...`` was
    # the first command of the July 2026 Hugging Face intrusion and used to
    # slip through. ``env FOO=1 prog`` (running a program) still does not match.
    ("environment dump", re.compile(r"(?:^|[;&|]\s*)(?:env|printenv)\s*(?:[;&|]|$)", re.I)),
    ("cloud metadata endpoint", re.compile(r"169\.254\.169\.254|metadata\.google\.internal", re.I)),
    # A pod's mounted identity: whoever holds it acts as the workload.
    ("service account token", re.compile(
        r"/run/secrets/(?:kubernetes\.io|eks\.amazonaws\.com)/serviceaccount|"
        r"/var/run/secrets/tokens/", re.I)),
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
    "cloud metadata endpoint", "service account token",
})


def _a(noun: str) -> str:
    return ("an " if noun[:1].lower() in "aeiou" else "a ") + noun


def _secret_value_lane(steps) -> Optional[dict]:
    """The VALUE half of ``credential_access``: token-shaped strings in a
    call's arguments or in a tool's output (see
    ``detector_surface._SECRET_VALUE_PATTERNS``). ``None`` when there are none.

    * critical: a token rode in a call to a host that does not own it (a
      Hugging Face token posted to an Artifactory board), or a token that
      first appeared in tool OUTPUT was later sent anywhere.
    * warning: the agent handled a token in its own arguments.
    * info: a token only appeared in output. Observation, not accusation.
    """
    in_output: dict = {}
    held: dict = {}
    sent_to: dict = {}
    reused: set = set()
    first_idx = None
    for pos, st in enumerate(steps):
        vals = st.get("secret_values") or ()
        if not vals:
            continue
        if first_idx is None:
            first_idx = st.get("i")
        kind = st.get("kind")
        if kind == "tool_result":
            for c in vals:
                in_output.setdefault(c, pos)
            continue
        if kind != "tool_call":
            continue
        call_hosts = st.get("hosts") or ()
        for c in vals:
            held[c] = held.get(c, 0) + 1
            owners = SECRET_VALUE_OWNERS.get(c)
            if owners is not None:
                for h in call_hosts:
                    if not host_owned_by(h, owners) and h not in sent_to.get(c, ()):
                        sent_to.setdefault(c, []).append(h)
            if call_hosts and c in in_output and in_output[c] < pos:
                reused.add(c)
    if not in_output and not held:
        return None

    if sent_to:
        c = sorted(sent_to)[0]
        h = sent_to[c][0]
        sev, title = "critical", f"sent {_a(c)} to {h}"
        detail = (f"{_a(c).capitalize()} rode in a call that reached {h}, which "
                  f"is not a host that token belongs to. Tokens go to the "
                  f"service that issued them; one sent elsewhere is the shape "
                  f"of a leak. Only the kind of token is recorded. ")
    elif reused:
        c = sorted(reused)[0]
        sev, title = "critical", f"found {_a(c)} in tool output, then used it"
        detail = (f"{_a(c).capitalize()} first appeared in a tool's output and "
                  f"later rode in a call that reached the network. An agent "
                  f"picking up a credential it was not handed, and using it, is "
                  f"worth a look before it continues. ")
    elif held:
        c = sorted(held)[0]
        sev, title = "warning", f"handled {_a(c)} in its commands"
        detail = (f"{_a(c).capitalize()} appeared in the agent's tool "
                  f"arguments. Only the kind of token is recorded, never the "
                  f"value. ")
    else:
        c = sorted(in_output)[0]
        sev, title = "info", f"{_a(c)} appeared in tool output"
        detail = (f"{_a(c).capitalize()} appeared in a tool's output. Nothing "
                  f"used it in this window; surfaced so it is not invisible. ")
    return {
        "severity": sev, "title": title, "detail": detail,
        "first_idx": first_idx,
        "categories": sorted(set(in_output) | set(held)),
        "in_output": sorted(in_output),
        "sent_to_hosts": sorted({h for hs in sent_to.values() for h in hs}),
        "reused": sorted(reused),
    }


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
        values = _secret_value_lane(steps)
        if not categories and not values:
            return None

        # Egress AFTER the first credential touch, in the same window.
        egress_after = []
        for st in steps[(first_pos or 0) + 1:] if categories else ():
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
            # No paths, no commands, no values. The category IS the finding.
            "redacted": "paths, commands and secret values are deliberately not recorded",
        }
        if values:
            evidence.update({
                "value_categories": values["categories"],
                "values_in_output": values["in_output"],
                "values_sent_to": values["sent_to_hosts"][:5],
                "values_reused": values["reused"],
            })
            if values["in_output"]:
                evidence["observed"] = "tool_arguments_and_results"
            # A token leaving for a host that does not own it outranks any
            # location finding; with no location finding, the value lane is
            # the whole story at whatever severity it earned.
            if values["severity"] == "critical" or not categories:
                return _core()._incident(
                    "credential_access", session_id, runtime, values["severity"],
                    f"{runtime}: {values['title']}",
                    values["detail"] + _core()._stop_hint(), evidence,
                    values["first_idx"])

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
        read_only = th.get("read_only_hosts") or frozenset()
        hosts: dict = {}
        written: dict = {}
        first_idx = None
        for st in steps:
            for h in st.get("hosts") or ():
                if h not in hosts:
                    hosts[h] = st.get("i")
                    if first_idx is None:
                        first_idx = st.get("i")
            for h in st.get("write_hosts") or ():
                written.setdefault(h, st.get("i"))
        if not hosts:
            return None

        distinct = sorted(hosts)
        new_hosts = [h for h in distinct if h not in known] if known else []
        # Sent data to a host the cohort has only ever READ from: the package
        # mirror used as a message board (Hugging Face swarm, July 2026).
        ro_writes = [h for h in sorted(written) if h in read_only]
        raw_ips = [h for h in distinct if _IPV4_RE.match(h)]
        fanout_limit = int(th["egress_hosts"])
        fanout = len(distinct) >= fanout_limit

        if new_hosts:
            ground, sev = "first_time", "warning"
        elif ro_writes:
            ground, sev = "write_to_read_only_host", "warning"
        elif fanout:
            ground, sev = "fanout", "warning"
        elif raw_ips:
            ground, sev = "raw_address", "info"
        else:
            return None

        # Hosts other sessions in the cohort reached only recently. They are in
        # the cohort's memory but not yet counted as normal (see
        # detector_calibration.EGRESS_SETTLE_HOURS), so a swarm cannot vouch
        # for its own destination.
        settling = th.get("settling_hosts") or frozenset()
        settling_new = [h for h in new_hosts if h in settling]
        evidence = {
            "ground": ground,
            "distinct_hosts": len(distinct),
            "hosts": distinct[:8],
            "new_hosts": new_hosts[:8],
            "settling_hosts": settling_new[:8],
            "raw_addresses": raw_ips[:4],
            "known_host_count": len(known),
            "threshold": fanout_limit,
            # Direction: hosts this window SENT data to, and which of those
            # the cohort has only ever read from.
            "write_hosts": sorted(written)[:8],
            "read_only_writes": ro_writes[:8],
            "observed": "tool_arguments",
        }
        settle_h = th.get("egress_settle_hours") or 0
        window = f"{settle_h:g}h"
        if ground == "first_time":
            shown = ", ".join(new_hosts[:3])
            detail = (f"This agent has not reached {shown} in the {len(known)} "
                      f"host(s) its cohort has used for longer than {window}. ")
            if settling_new:
                detail += (f"{len(settling_new)} of them were first reached by "
                           f"other sessions in this cohort within the last "
                           f"{window}, so they are not counted as normal yet. ")
            verb = ("first write to" if any(h in written for h in new_hosts[:3])
                    else "first contact with")
            return _core()._incident(
                "network_egress", session_id, runtime, sev,
                f"{runtime}: {verb} {shown}"
                + (f" +{len(new_hosts) - 3} more" if len(new_hosts) > 3 else ""),
                detail + _core()._stop_hint(),
                evidence, hosts.get(new_hosts[0]))
        if ground == "write_to_read_only_host":
            shown = ", ".join(ro_writes[:3])
            return _core()._incident(
                "network_egress", session_id, runtime, sev,
                f"{runtime}: sent data to {shown}, a host its cohort only reads from",
                f"The agent wrote to {shown} (an upload, a PUT or POST, a "
                f"publish). Sessions in its cohort have only ever read from "
                f"there, watched for at least {window}. A package mirror or "
                f"shared cache is where agents get things; an agent putting "
                f"things there is the unusual direction. " + _core()._stop_hint(),
                evidence, written.get(ro_writes[0]))
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
    # Remote tier: privilege on SOMEONE ELSE'S system. A role binding or an
    # access key outlives the session exactly as a setuid bit does, so these
    # are critical too. The Hugging Face swarm reached cluster-admin this way
    # (scorecard rows 3 and 12) while the local tier saw nothing.
    ("granted a Kubernetes role binding",
     re.compile(r"\bkubectl\b[^;&|\n]*\bcreate\s+(?:cluster)?rolebinding\b", re.I), True),
    ("acted as a Kubernetes cluster admin",
     re.compile(r"\bkubectl\b[^;&|\n]*--as(?:-group)?[=\s]['\"]?system:(?:admin|masters)\b",
                re.I), True),
    ("created cloud credentials or attached an IAM policy",
     re.compile(r"\baws\s+iam\s+(?:create-access-key|create-login-profile|"
                r"attach-(?:user|role|group)-policy|put-(?:user|role|group)-policy|"
                r"update-assume-role-policy|add-user-to-group)\b", re.I), True),
    ("granted a cloud IAM role",
     re.compile(r"\bgcloud\b[^;&|\n]*\badd-iam-policy-binding\b|"
                r"\baz\s+role\s+assignment\s+create\b", re.I), True),
    ("ran a privileged container",
     re.compile(r"\b(?:docker|podman)\s+run\b[^;&|\n]*(?:--privileged\b|"
                r"(?:-v|--volume)[=\s]['\"]?/:/|--pid[=\s]host\b)", re.I), True),
)
# Admin endpoints that turn an HTTP request into standing privilege or code
# execution on the server: Artifactory token minting and plugin execution,
# Jenkins' script console. Only a WRITING request counts: fetching the page is
# looking, POSTing a script is running it.
_ADMIN_API_RE = re.compile(
    r"://[^\s'\"]+/(?:api/security/token|api/plugins/(?:execute|reload)|"
    r"scriptText|scriptExecution|script)(?=[\s'\"?/#]|$)", re.I)
_ADMIN_API_LABEL = "called a remote admin API"


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
            if any(_ADMIN_API_RE.search(seg) and _segment_write_hosts(seg)
                   for seg in _SEGMENT_SPLIT_RE.split(cmd)[:40]):
                found[_ADMIN_API_LABEL] = found.get(_ADMIN_API_LABEL, 0) + 1
                critical.append(_ADMIN_API_LABEL)
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
