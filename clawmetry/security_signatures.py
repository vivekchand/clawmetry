"""Pure legacy action signatures shared by the daemon and dashboard.

Inputs are observed tool arguments. A match does not prove execution.
"""
import re as _sec_re

_THREAT_SIGNATURES = [
    # Critical: Direct system compromise attempts
    {
        "id": "SEC-001",
        "severity": "critical",
        "description": "Reverse shell attempt via exec",
        "tool_types": ["EXEC"],
        "patterns": [
            r"(?:bash|sh|nc|ncat|netcat)\s.*-[ie]\s",
            r"/dev/tcp/",
            r"mkfifo\s+/tmp/",
            r"\bsocat\b.*\bexec\b",
            r"\btelnet\b.*\|.*\bsh\b",
        ],
    },
    {
        "id": "SEC-002",
        "severity": "critical",
        "description": "Credential/secret file access",
        "tool_types": ["READ", "EXEC"],
        "patterns": [
            r"(?:/etc/shadow|/etc/passwd)",
            r"\.ssh/(?:id_rsa|id_ed25519|authorized_keys)",
            r"\.aws/credentials",
            r"\.env(?:\b|$)",
            r"(?:\.kube|kubeconfig)",
            r"\.gnupg/private",
            r"\.netrc",
        ],
    },
    {
        "id": "SEC-003",
        "severity": "critical",
        "description": "Privilege escalation attempt",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bsudo\s+(?:su|bash|sh|chmod\s+[ugo]*s)",
            r"\bchmod\s+[0-7]*4[0-7]{2}\b",
            r"\bchmod\s+u\+s\b",
            r"\bpkexec\b",
            r"\bsu\s+-\s",
        ],
    },
    # High: Data exfiltration and suspicious network activity
    {
        "id": "SEC-004",
        "severity": "high",
        "description": "Potential data exfiltration via curl/wget POST",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bcurl\b.*\b-[dX]\b.*(?:POST|PUT)",
            r"\bcurl\b.*--data(?:-binary|-raw|-urlencode)?\b",
            r"\bwget\b.*--post-(?:data|file)\b",
        ],
    },
    {
        "id": "SEC-005",
        "severity": "high",
        "description": "SSH/SCP to unknown external host",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bssh\b\s+(?!localhost|127\.0\.0\.1|192\.168\.|10\.|172\.(?:1[6-9]|2[0-9]|3[01]))",
            r"\bscp\b\s+.*:",
            r"\brsync\b.*(?<!localhost):",
        ],
    },
    {
        "id": "SEC-006",
        "severity": "high",
        "description": "Cryptocurrency miner indicators",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bxmrig\b",
            r"\bstratum\+tcp\b",
            r"(?:mine|pool)\..*\.(?:com|net|org)",
            r"\bcpuminer\b",
        ],
    },
    # Medium: Suspicious but potentially legitimate
    {
        "id": "SEC-007",
        "severity": "medium",
        "description": "Destructive file operation (rm -rf on system paths)",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\brm\s+(?:-[rfRv]+\s+)*(?:/(?:etc|usr|var|boot|lib|bin|sbin|opt|root)\b|/\s*$)",
            r"\brm\s+-[rfR]+\s+\*",
            r"\bdd\s+.*of=/dev/",
            r"\bmkfs\b",
        ],
    },
    {
        "id": "SEC-008",
        "severity": "medium",
        "description": "Package manager running as agent (supply chain risk)",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bpip\s+install\b.*(?:--index-url|--extra-index-url|--trusted-host)",
            r"\bnpm\s+install\b.*(?:--registry|--unsafe-perm)",
            r"\bcurl\b.*\|\s*(?:sudo\s+)?(?:bash|sh)\b",
            r"\bwget\b.*\|\s*(?:sudo\s+)?(?:bash|sh)\b",
        ],
    },
    {
        "id": "SEC-009",
        "severity": "medium",
        "description": "Firewall or security policy modification",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\b(?:ufw|iptables|nftables|firewall-cmd)\b.*(?:allow|disable|delete|flush)",
            r"\bsetenforce\s+0\b",
            r"\bsystemctl\s+(?:stop|disable)\s+(?:firewalld|ufw|apparmor)",
        ],
    },
    {
        "id": "SEC-010",
        "severity": "medium",
        "description": "Cron/systemd persistence mechanism",
        "tool_types": ["EXEC", "WRITE"],
        "patterns": [
            r"\bcrontab\b",
            r"/etc/cron\.",
            r"/etc/systemd/system/.*\.service",
            r"systemctl\s+enable\b",
        ],
    },
    # Low: Informational security events
    {
        "id": "SEC-011",
        "severity": "low",
        "description": "Port scanning or network reconnaissance",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bnmap\b",
            r"\bmasscan\b",
            r"\bnetstat\s+-[tul]*p",
            r"\bss\s+-[tul]*p",
        ],
    },
    {
        "id": "SEC-012",
        "severity": "low",
        "description": "Large file download (potential payload)",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bwget\b\s+https?://(?!github\.com|pypi\.org|registry\.npmjs\.org|dl\.google\.com)",
            r"\bcurl\b\s+-[oOL]+\s+https?://(?!github\.com|pypi\.org|registry\.npmjs\.org)",
        ],
    },
    {
        "id": "SEC-013",
        "severity": "medium",
        "description": "Environment variable or API key extraction",
        "tool_types": ["EXEC", "READ"],
        "patterns": [
            r"\bprintenv\b",
            r"\benv\s*$",
            r"\bset\s*\|\s*grep\b.*(?:KEY|SECRET|TOKEN|PASS)",
            r"cat\s+.*(?:\.env|secrets|credentials)",
        ],
    },
    {
        "id": "SEC-014",
        "severity": "high",
        "description": "Process injection or debugging attachment",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bgdb\b.*-p\s*\d+",
            r"\bstrace\b.*-p\s*\d+",
            r"\bptrace\b",
            r"\bLD_PRELOAD\b",
            r"\b/proc/\d+/mem\b",
        ],
    },
    {
        "id": "SEC-015",
        "severity": "high",
        "description": "Browser tool accessing sensitive URLs",
        "tool_types": ["BROWSER", "SEARCH"],
        "patterns": [
            r"(?:bank|paypal|stripe\.com/dashboard|console\.aws|portal\.azure)",
            r"(?:admin|phpmyadmin|wp-admin|cpanel)",
            r"file:///etc/",
        ],
    },
    {
        "id": "SEC-016",
        "severity": "high",
        "description": "Prompt injection attempt in external content",
        "tool_types": ["READ", "BROWSER", "SEARCH"],
        "patterns": [
            r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions",
            r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+instructions",
            r"forget\s+(?:all\s+)?(?:your\s+)?(?:previous|prior|above)\s+instructions",
            r"override\s+(?:your\s+)?(?:system\s+prompt|instructions|directives)",
            r"you\s+are\s+now\s+(?:a\s+)?(?:DAN|uncensored|unrestricted|jailbroken)",
            r"\bdo\s+anything\s+now\b",
            r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
            r"new\s+instructions?[:]\s*(?:you|your|from\s+now)",
        ],
    },
]

# Compile patterns once
for _sig in _THREAT_SIGNATURES:
    _sig["_compiled"] = [
        _sec_re.compile(p, _sec_re.IGNORECASE) for p in _sig["patterns"]
    ]


# Action labels a signature's ``tool_types`` may declare. These come from the
# LEGACY JSONL parser's ``tool_to_type()`` (routes/brain.py) and predate the
# DuckDB-first read path.
_THREAT_ACTION_TYPES = frozenset(
    {"EXEC", "READ", "WRITE", "BROWSER", "SEARCH", "MSG", "SPAWN", "TOOL"}
)

# Rows that are agent *speech*, not agent *action*. Running action signatures
# over these is how you flag the model for merely discussing ``~/.ssh/id_rsa``.
# Content-borne risk (PII, injection, leaked keys) is the content scanners'
# job — see ``_scan_content_for_policy_events``.
_THREAT_NON_ACTION_TYPES = frozenset(
    {"MESSAGE", "THINKING", "USER", "ASSISTANT", "SUMMARY", "COMPACT", "SYSTEM"}
)

# Tool-CALL rows as the DuckDB fast path emits them (routes/brain.py's
# ``evt_type = event_type.upper()``). Only the call is an agent ACTION.
#
# TOOL_RESULT is deliberately absent, and so is ERROR (which routes/brain.py
# derives from a failed TOOL_RESULT). A result is data the agent RECEIVED, not
# something it did, and results are big free-text blobs — a page of docs, web
# search output, a source file. Scanning them for action patterns produced
# nothing but noise: live on a real node, all four hits were TOOL_RESULT rows
# and all four were false positives (a Devin CLI docs page and a geocoding
# result matched "browser reaching an admin panel"; a Python source file
# matched "credential file access" at CRITICAL). Content-borne risk in results
# is the policy scanners' job — see ``_scan_content_for_policy_events``.
_THREAT_TOOL_TYPES = frozenset({"TOOL_CALL", "TOOL.CALL", "TOOL_USE"})

# Returned data, not agent action. Excluded for the reason above.
_THREAT_RESULT_TYPES = frozenset({"TOOL_RESULT", "TOOL.RESULT", "ERROR"})


def _threat_tool_name_to_action(name):
    """Map a tool NAME to a legacy action label. Mirrors routes/brain.py's
    ``tool_to_type`` so both taxonomies agree on what 'EXEC' means."""
    tn = str(name or "").lower()
    if tn == "exec" or "shell" in tn or "bash" in tn or tn == "process":
        return "EXEC"
    if "read" in tn or "grep" in tn or "glob" in tn:
        return "READ"
    if "write" in tn or "edit" in tn:
        return "WRITE"
    if "browser" in tn or "canvas" in tn or "image" in tn:
        return "BROWSER"
    if "web_search" in tn or "web_fetch" in tn or "search" in tn or "fetch" in tn:
        return "SEARCH"
    if "subagent" in tn or "spawn" in tn or "task" in tn:
        return "SPAWN"
    return "TOOL"


def _threat_action_types(ev):
    """Which action labels an event should be matched against.

    The signature table gates on the legacy ``EXEC/READ/WRITE/...`` vocabulary,
    but since the DuckDB-first migration brain rows arrive as
    ``TOOL_CALL/TOOL_RESULT/MESSAGE/THINKING/ERROR``. The two vocabularies do
    not intersect, so every event fell through every signature and the scanner
    could never report a threat (it was structurally pinned at 0). This bridges
    them: legacy labels pass through, speech rows are excluded, and a tool row
    with no tool NAME is matched against every signature — the store keeps the
    tool INPUT in ``detail`` but not which tool produced it, and the signature
    regexes are specific enough (``/dev/tcp/``, ``.ssh/id_rsa``) to carry the
    precision on their own.
    """
    ev_type = str(ev.get("type") or "").upper()
    if not ev_type:
        return frozenset()
    if ev_type in _THREAT_ACTION_TYPES:
        return frozenset({ev_type})
    if ev_type in _THREAT_NON_ACTION_TYPES or ev_type in _THREAT_RESULT_TYPES:
        return frozenset()
    if ev_type in _THREAT_TOOL_TYPES:
        name = ev.get("tool") or ev.get("toolName") or ev.get("name")
        if name:
            return frozenset({_threat_tool_name_to_action(name)})
        return _THREAT_ACTION_TYPES
    # CHANNEL.*, NUMBAT_FINDING, daemon rows, anything else we don't recognise
    # as an agent action: leave alone rather than guess.
    return frozenset()


def _threat_event_session(ev):
    """Session id for a brain event across both read paths.

    The legacy parser used ``source``; the DuckDB fast path emits ``sessionId``
    (full) plus ``src`` (truncated to 32 chars). Reading only ``source`` meant
    every event reported the empty string, so a node with five active sessions
    reported ``sessions_scanned: 1``.
    """
    return str(
        ev.get("sessionId") or ev.get("source") or ev.get("src") or ""
    )


def _threat_session_runtime(session_id):
    """``claude_code:1bfbb30f-...`` → ``claude_code``. Bare ids → ""."""
    sid = str(session_id or "")
    return sid.split(":", 1)[0] if ":" in sid else ""


def _scan_events_for_threats(events, runtime=None):
    """Scan brain-history events against threat signatures. Returns list of threat matches.

    ``runtime`` scopes the scan to one agent runtime (per FLYWHEEL §1c —
    a number shown under the runtime switcher must belong to that runtime).
    """
    threats = []
    sessions_seen = set()
    sessions_with_threats = set()
    want_runtime = str(runtime or "").strip().lower()

    for ev in events:
        source = _threat_event_session(ev)
        if want_runtime and _threat_session_runtime(source).lower() != want_runtime:
            continue
        sessions_seen.add(source)
        action_types = _threat_action_types(ev)
        if not action_types:
            continue
        ev_type = str(ev.get("type") or "")
        detail = ev.get("detail", "")
        if not detail:
            continue

        for sig in _THREAT_SIGNATURES:
            if not action_types.intersection(sig["tool_types"]):
                continue
            for compiled in sig["_compiled"]:
                if compiled.search(detail):
                    sessions_with_threats.add(source)
                    threats.append(
                        {
                            "rule_id": sig["id"],
                            "severity": sig["severity"],
                            "description": sig["description"],
                            "detail": detail[:500],
                            "time": ev.get("time", ""),
                            "session": ev.get("sourceLabel", source),
                            "source": source,
                            "event_type": ev_type,
                            "engine": "builtin",
                            "runtime": _threat_session_runtime(source),
                        }
                    )
                    break  # One match per signature per event

    # Sort by severity then time
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    threats.sort(
        key=lambda t: (sev_order.get(t["severity"], 9), t.get("time", "") or ""),
        reverse=False,
    )
    threats.sort(key=lambda t: t.get("time", "") or "", reverse=True)

    counts = {
        "critical": sum(1 for t in threats if t["severity"] == "critical"),
        "high": sum(1 for t in threats if t["severity"] == "high"),
        "medium": sum(1 for t in threats if t["severity"] == "medium"),
        "low": sum(1 for t in threats if t["severity"] == "low"),
        "total": len(threats),
        "sessions_scanned": len(sessions_seen),
        "clean_sessions": len(sessions_seen - sessions_with_threats),
    }
    return threats, counts


