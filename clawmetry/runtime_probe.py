"""clawmetry/runtime_probe.py — zero-dependency presence probes for every
supported agent runtime (#3917, founder request 2026-07-22).

The adapter registry can only detect runtimes whose adapters are REGISTERED,
so a free (OSS-only) install is blind to the ten Pro runtimes: a machine full
of Cursor or Claude Code sessions onboards with no hint that ClawMetry could
watch them, and no hint that doing so needs a license key or the Cloud plan.
That is the conversion moment, wasted.

These probes are presence checks over each runtime's default on-disk data
location, nothing more: no parsing, no session reading, no gated behaviour.
The Pro adapters remain the single source of truth for real detection and
ingestion; a probe hit only drives honest onboarding copy ("Cursor was found
on this machine; the free tier does not watch it").

Path notes: each entry mirrors the default location the corresponding
adapter reads (verified live on Windows 2026-07-20 by planting fixture data
at exactly these paths and watching the adapters ingest it). ``~`` expands
per-OS; env overrides honoured where the adapter honours them.
"""
from __future__ import annotations

import glob as _glob
import sys as _sys
import os
from dataclasses import dataclass

# Runtimes the free tier watches (FLYWHEEL: free on every plan).
#
# Sourced from the entitlement catalogue rather than duplicated: this module
# only labels a probe row ``free``, and a stale copy here would show a free
# runtime as locked in onboarding while the gate happily allowed it. The
# literal is kept solely as an import-failure fallback (this module is
# imported by the installer path, which must never hard-fail on an import).
try:  # pragma: no cover - trivial import shim
    from clawmetry.entitlements import FREE_RUNTIMES
except Exception:  # pragma: no cover - defensive; keep onboarding alive
    FREE_RUNTIMES = frozenset({"openclaw", "nemoclaw", "goose"})


def _tilde(path: str) -> str:
    """``/Users/ada/.codex`` -> ``~/.codex``. Never widens a path."""
    try:
        home = os.path.expanduser("~")
        if home and home != os.sep and path.startswith(home):
            return "~" + path[len(home):]
    except Exception:
        pass
    return path


def _refusal_reason(expanded: str):
    """Why an apparently-absent path is actually unreadable, or ``None``.

    This exists because the obvious check does not work. ``glob.glob`` and
    ``os.path.exists`` BOTH swallow ``PermissionError`` and answer ""/False,
    so a directory we are refused is indistinguishable from one that was
    never created -- which is the whole bug (#5716) and would have made a
    "we were blocked" message dead code. Verified on macOS: against a
    ``chmod 000`` directory, ``glob`` returns ``[]`` and ``exists`` returns
    ``False``, while ``os.listdir`` / ``os.stat`` / ``os.scandir`` raise
    ``PermissionError(errno 13)``.

    So walk up to the nearest ancestor we can name and ask it a question that
    is allowed to fail. Returns a plain-words reason, or ``None`` when the
    path is simply not there.
    """
    try:
        cur = os.path.dirname(expanded.rstrip(os.sep)) or os.sep
        seen = 0
        while cur and seen < 24:
            seen += 1
            try:
                os.listdir(cur)
                return None  # readable, so the target really is absent
            except PermissionError as e:
                return _permission_reason(e)
            except NotADirectoryError:
                return None
            except FileNotFoundError:
                parent = os.path.dirname(cur)
                if not parent or parent == cur:
                    return None
                cur = parent
                continue
            except OSError as e:
                return _permission_reason(e)
    except Exception:
        return None
    return None


def _permission_reason(exc: BaseException) -> str:
    """A plain-words reason for a refused read, never an errno the reader
    has to look up (FLYWHEEL: never show the user an upstream error code)."""
    import errno as _errno

    code = getattr(exc, "errno", None)
    if code in (_errno.EACCES, _errno.EPERM):
        if _sys.platform == "darwin":
            return ("macOS blocked the read. Give your terminal (or the "
                    "ClawMetry app) Full Disk Access in System Settings > "
                    "Privacy & Security, then reopen it.")
        return "Permission denied. Check that your user can read this path."
    if code == _errno.ELOOP:
        return "A symlink loop stopped the read."
    if code == _errno.ENAMETOOLONG:
        return "The path is too long for this filesystem."
    return "Could not be read on this machine."


@dataclass
class RuntimeProbe:
    """One supported runtime: id, human label, and where its data lives."""

    id: str
    label: str
    paths: tuple  # candidate globs, relative to ~ unless absolute / env-based
    env: str = ""  # optional env var naming the data dir (adapter-honoured)

    def found(self) -> bool:
        """True when any candidate location exists. Never raises.

        Kept as the one-bit answer its existing callers expect; ``inspect``
        is the same probe with its findings retained. The try/except is the
        contract, not decoration: this is called from the installer path,
        which must never hard-fail.
        """
        try:
            return bool(self.inspect().get("found"))
        except Exception:
            return False

    def inspect(self) -> dict:
        """The same probe, but keeping what it learned. Never raises.

        ``found()`` answers one bit and throws the rest away, which is why a
        first-run user could not be told anything (#5716). Three outcomes are
        collapsed into that single ``False``:

          * the location genuinely is not there — nothing has run here;
          * the location is there and we were REFUSED (macOS TDD / Full Disk
            Access, a root-owned dir, a locked profile) — the runtime is
            present and we are blind to it, which is the opposite conclusion;
          * the path could not even be resolved because the env var it is
            written against is unset.

        Returns ``{found, checked, unreadable, env, env_set}``:

          * ``checked``   - every candidate location, EXPANDED as the probe
            actually looked at it, so a reader sees the real path on their own
            machine rather than the tilde-form in our source;
          * ``unreadable`` - the subset we were refused access to, each with
            the reason. Non-empty means "present but blind", never "absent";
          * ``env`` / ``env_set`` - the data-dir override this runtime
            honours and whether it is set, so "I did set that" is checkable.
        """
        checked: list = []
        unreadable: list = []
        found = False

        def _look(raw: str, expanded: str) -> None:
            nonlocal found
            # Home-collapsed, ALWAYS. An absolute path carries the account
            # name, and everything that renders one ends up in a screenshot,
            # a screen-share or a pasted issue. ``~/.claude/projects`` is
            # exactly as checkable and names nobody. Mirrors the rule the
            # detector surface already holds itself to (AC-OBS-RSO-030.7:
            # no report carries a full filesystem path).
            entry = {"path": _tilde(expanded)}
            if expanded != raw:
                entry["pattern"] = raw
            try:
                if _glob.glob(expanded) or os.path.exists(expanded):
                    entry["exists"] = True
                    found = True
                else:
                    # "Not found" here can mean refused: see _refusal_reason.
                    reason = _refusal_reason(expanded)
                    if reason:
                        entry["exists"] = None
                        entry["unreadable"] = reason
                        unreadable.append(entry)
                    else:
                        entry["exists"] = False
            except PermissionError as e:
                # The distinction the whole issue is about: refused is not
                # absent. Report it as its own state so the UI can say
                # "present, but ClawMetry was not allowed to read it".
                entry["exists"] = None
                entry["unreadable"] = _permission_reason(e)
                unreadable.append(entry)
            except OSError as e:
                entry["exists"] = None
                entry["unreadable"] = _permission_reason(e)
                unreadable.append(entry)
            except Exception:
                entry["exists"] = None
            checked.append(entry)

        env_set = False
        try:
            if self.env:
                root = os.environ.get(self.env)
                env_set = bool(root)
                if root:
                    _look(root, os.path.expanduser(root))
        except Exception:
            pass

        for raw in self.paths:
            try:
                # expandvars FIRST so "$XDG_DATA_HOME/..." resolves; an unset
                # var stays literal and simply globs to nothing, which is the
                # honest answer rather than a bare-root false positive.
                expanded = os.path.expanduser(os.path.expandvars(raw))
                if "$" in expanded:
                    # Unresolved because its variable is unset. Say so rather
                    # than listing a path with a dollar sign in it as though
                    # we had looked there.
                    checked.append({"path": raw, "exists": False,
                                    "unresolved_env": True})
                    continue
                _look(raw, expanded)
            except Exception:
                continue

        return {
            "found": found,
            "checked": checked,
            "unreadable": unreadable,
            "env": self.env,
            "env_set": env_set,
        }


# One entry per supported runtime. Keep ids in sync with the entitlement
# catalogue (clawmetry/entitlements.py) — tests assert the parity.
RUNTIME_PROBES: tuple = (
    RuntimeProbe("openclaw", "OpenClaw", ("~/.openclaw/openclaw.json", "~/.openclaw/gateway"), env="OPENCLAW_HOME"),
    RuntimeProbe("nemoclaw", "NVIDIA NemoClaw", ("~/.nemoclaw", "~/.openclaw/sandboxes")),
    RuntimeProbe("claude_code", "Claude Code", ("~/.claude/projects",)),
    RuntimeProbe("codex", "Codex", ("~/.codex/sessions", "~/.codex/archived_sessions")),
    RuntimeProbe("cursor", "Cursor", (
        "~/AppData/Roaming/Cursor/User/globalStorage/state.vscdb",
        "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb",
        "~/.config/Cursor/User/globalStorage/state.vscdb",
    )),
    RuntimeProbe("aider", "Aider", ("~/.aider*",), env="AIDER_HISTORY_DIRS"),
    # Goose resolves its data dir with etcetera's choose_app_strategy, which
    # is XDG on macOS as well as Linux (NOT ~/Library/Application Support)
    # and RoamingAppData on Windows; GOOSE_PATH_ROOT relocates all of it.
    # The last entry is the legacy macOS location Goose's own paths.rs still
    # names for pre-existing installs. The env-var forms are globbed rather
    # than declared via ``env=``, because "$GOOSE_PATH_ROOT exists" is not
    # evidence of a Goose install — "$GOOSE_PATH_ROOT/data/sessions exists"
    # is. Kept in step with clawmetry/adapters/goose.py::_candidate_db_paths().
    RuntimeProbe("goose", "Goose", (
        "$GOOSE_PATH_ROOT/data/sessions",
        "$XDG_DATA_HOME/goose/sessions",
        "~/.local/share/goose/sessions",
        "$APPDATA/Block/goose/data/sessions",
        "~/AppData/Roaming/Block/goose/data/sessions",
        "~/Library/Application Support/Block/goose/sessions",
    )),
    RuntimeProbe("opencode", "opencode", ("~/.local/share/opencode",)),
    RuntimeProbe("qwen_code", "Qwen Code", ("~/.qwen/projects",)),
    RuntimeProbe("hermes", "Hermes", ("~/.hermes",), env="HERMES_HOME"),
    RuntimeProbe("picoclaw", "PicoClaw", ("~/.picoclaw/workspace",)),
    RuntimeProbe("nanoclaw", "NanoClaw", ("~/.nanoclaw",)),
    RuntimeProbe("pi", "Pi", ("~/.pi/agent/sessions",)),
    RuntimeProbe("deepagents", "DeepAgents", ("~/.deepagents/.state", "~/.deepagents")),
    RuntimeProbe("n8n", "n8n", ("~/.n8n",), env="N8N_USER_FOLDER"),
    RuntimeProbe("antigravity", "Antigravity",
                 ("~/.gemini/antigravity", "~/.gemini/antigravity-cli",
                  "~/.gemini/antigravity-ide", "~/.gemini/jetski"),
                 env="CLAWMETRY_ANTIGRAVITY_HOME"),
    RuntimeProbe("copilot", "GitHub Copilot", ("~/.copilot/session-state",),
                 env="CLAWMETRY_COPILOT_HOME"),
    RuntimeProbe("grok", "Grok",
                 ("~/.grok/logs", "~/.grok/sessions", "~/.grok/bin/grok"),
                 env="CLAWMETRY_GROK_HOME"),
    # DeepSeek Harness (`dsh`) keeps everything under one home ($DSH_HOME,
    # default ~/.dsh); JSONL session logs live in <home>/sessions.
    RuntimeProbe("deepseek_harness", "DeepSeek Harness",
                 ("~/.dsh/sessions",), env="DSH_HOME"),
    # Exo harness state is WORKSPACE-relative (<workspace>/.exo/exoharness),
    # not home-anchored; the probe checks the common clone locations and the
    # CLAWMETRY_EXO_ROOTS override. The pro adapter does the deeper
    # well-known-parents scan.
    RuntimeProbe("exo", "Exo",
                 ("~/exo/.exo/exoharness", "~/.exo/exoharness"),
                 env="CLAWMETRY_EXO_ROOTS"),
    # Kimi CLI keeps everything under one share dir ($KIMI_SHARE_DIR,
    # default ~/.kimi); the standalone successor Kimi Code CLI uses
    # ~/.kimi-code. Same store shape, same runtime here.
    RuntimeProbe("kimi", "Kimi CLI",
                 ("~/.kimi/sessions", "~/.kimi-code/sessions"),
                 env="KIMI_SHARE_DIR"),
    # Google Gemini CLI keeps per-project chat recordings under
    # <home>/.gemini/tmp/<project-basename>/chats/. NOTE the env var names the
    # dir CONTAINING .gemini (unlike KIMI_SHARE_DIR/QWEN_HOME, which name the
    # data dir itself), so the probe globs both the plain ~/.gemini tree and
    # the CLAWMETRY override that points straight at a data dir.
    RuntimeProbe("gemini_cli", "Gemini CLI",
                 ("~/.gemini/tmp/*/chats", "~/.gemini/projects.json"),
                 env="CLAWMETRY_GEMINI_CLI_HOME"),
    # Cline CLI keeps sessions under the DATA leaf of its home -- ~/.cline
    # itself only holds hooks/ and worktrees/, which our own installer creates,
    # so probing the bare ~/.cline would false-positive on every machine that
    # has ClawMetry's hooks installed and no Cline at all.
    RuntimeProbe("cline", "Cline",
                 ("~/.cline/data/db/sessions.db", "~/.cline/data/sessions"),
                 env="CLAWMETRY_CLINE_DATA_DIR"),
    # OpenHands persists one directory per conversation. The probe requires the
    # conversations dir rather than the ~/.openhands root, because the CLI
    # creates ~/.openhands/profiles and ~/.openhands/cache on first launch even
    # when the persistence dir points elsewhere -- so the root existing is not
    # evidence that any conversation was ever recorded.
    # OpenWorker ("coworker") is a desktop app; its state dir is
    # $COWORKER_STATE_DIR, else %APPDATA%\\coworker on Windows, else
    # ~/.config/coworker (coworker/secrets.py::state_dir). Probe the STORE
    # files rather than the directory: the dir alone is created by a first
    # launch that never recorded a session, and ~/.config is shared with
    # every other tool, so a bare-dir probe is the weakest possible evidence.
    RuntimeProbe("openworker", "OpenWorker",
                 ("~/.config/coworker/coworker.db",
                  "~/.config/coworker/conversations",
                  "~/AppData/Roaming/coworker/coworker.db"),
                 env="CLAWMETRY_OPENWORKER_STATE_DIR"),
    # Lovable (lovable.dev) has NO install and no fixed data dir: the local
    # evidence is a git clone of a Lovable-synced repo, identified by its
    # CONTENT (README project marker + bot commits), which a path glob cannot
    # express without false positives. So the probe fires only on the
    # explicit env override; real discovery is content-based in the adapter.
    RuntimeProbe("lovable", "Lovable", (),
                 env="CLAWMETRY_LOVABLE_DIRS"),
    # Replit Agent serializes into the Repl WORKSPACE, not the machine home:
    # <workspace>/.local/state/replit/agent/. On a laptop that dir only
    # exists inside a cloned/exported Repl, so the probe checks the in-Repl
    # location (a daemon running inside a Repl sees it under ~/workspace)
    # and otherwise relies on the env override the adapter honours.
    RuntimeProbe("replit", "Replit Agent",
                 ("~/workspace/.local/state/replit/agent",
                  "~/.local/state/replit/agent"),
                 env="CLAWMETRY_REPLIT_ROOTS"),
    # Grok Bot (Anysphere "sand" desktop client). Probe the SLICE DIR and
    # ~/.grokbot, not ~/.grok -- that is Grok Build, a different runtime.
    RuntimeProbe("grok_bot", "Grok Bot",
                 ("~/Library/Application Support/Grok Bot/sand-client-persistence",
                  "~/AppData/Roaming/Grok Bot/sand-client-persistence",
                  "~/.config/Grok Bot/sand-client-persistence",
                  "~/.grokbot/settings.json"),
                 env="CLAWMETRY_GROK_BOT_DATA_ROOT"),
    RuntimeProbe("openhands", "OpenHands",
                 ("~/.openhands/conversations/*/base_state.json",),
                 env="CLAWMETRY_OPENHANDS_HOME"),
    # qm (github.com/yc-software/qm) has no on-disk session store — it's a
    # Node service backed by Postgres — so the probe looks for the npm
    # install artefacts (typical install layouts) plus a CLAWMETRY_QM_HOME
    # override. The adapter itself uses DATABASE_URL + qm's tables directly.
    RuntimeProbe("qm", "QM",
                 ("~/node_modules/@yc-software/qm",
                  "~/.qm", "~/qm/package.json",
                  "/opt/qm/package.json"),
                 env="CLAWMETRY_QM_HOME"),
    # Devin CLI (cli.devin.ai) keeps every session in ONE XDG-anchored SQLite
    # store; ~/.config/devin/config.json is the other half of a real install
    # (it exists even when the CLI has only ever run in ACP mode under an
    # IDE, which never creates sessions.db). Devin Cloud sessions are
    # API-only and cannot be probed from disk at all.
    RuntimeProbe("devin", "Devin",
                 ("~/.local/share/devin/cli/sessions.db",
                  "~/.local/share/cognition/cli/sessions.db",
                  "~/.local/share/chisel/cli/sessions.db",
                  "~/.config/devin/config.json",
                  "~/AppData/Local/devin/cli/sessions.db",
                  "~/AppData/Roaming/devin/config.json"),
                 env="CLAWMETRY_DEVIN_DB"),
)


def probe_runtimes() -> list:
    """Presence-probe every supported runtime.

    Returns ``[{id, label, free, found, checked, unreadable, env, env_set}]``
    in catalogue order. Never raises.

    ``checked`` / ``unreadable`` are what makes a "nothing found" answer
    actionable (#5716): this used to return the ``found`` bit alone, so no
    endpoint, CLI or screen could tell a first-run user WHERE we looked, and
    a runtime we were refused access to was reported exactly like one that
    was never installed. The keys are additive, so every existing consumer
    reading ``id`` / ``label`` / ``free`` / ``found`` is unaffected.
    """
    out = []
    for probe in RUNTIME_PROBES:
        try:
            info = probe.inspect()
        except Exception:
            info = {"found": False, "checked": [], "unreadable": [],
                    "env": getattr(probe, "env", ""), "env_set": False}
        out.append(
            {
                "id": probe.id,
                "label": probe.label,
                "free": probe.id in FREE_RUNTIMES,
                "found": bool(info.get("found")),
                "checked": info.get("checked") or [],
                "unreadable": info.get("unreadable") or [],
                "env": info.get("env") or "",
                "env_set": bool(info.get("env_set")),
            }
        )
    return out


def detection_report(probes: list = None) -> dict:
    """What a first-run screen needs to say instead of "you have no data".

    Answers the three questions #5716 asks, from the probe results:

      * WHERE we looked - ``locations``, the expanded candidate paths per
        runtime, capped so the answer stays readable on a 30-runtime
        catalogue;
      * WHAT it needs - ``blocked``, the runtimes whose data is present but
        unreadable, with a plain-words reason. This is the case that most
        deserves saying out loud, because the user CAN fix it and the old
        screen told them nothing;
      * ``found`` - what was detected, so the caller can tell the
        genuinely-empty machine from the partly-readable one.

    Pure over its input, so a caller can pass planted probe results.
    """
    probes = probe_runtimes() if probes is None else probes
    found = [p for p in probes if p.get("found")]
    blocked = []
    locations = []
    for p in probes:
        seen_reasons = set()
        for entry in (p.get("unreadable") or []):
            reason = entry.get("unreadable")
            if reason in seen_reasons:
                continue
            seen_reasons.add(reason)
            # No path. A blocked read is actionable from the runtime name and
            # the reason alone ("give your terminal Full Disk Access"); the
            # path would only add the account name to a screenshot.
            blocked.append({
                "runtime": p.get("id"), "label": p.get("label"),
                "reason": reason,
            })
        if p.get("found"):
            continue
        paths = [e.get("path") for e in (p.get("checked") or [])
                 if e.get("path") and not e.get("unresolved_env")]
        if paths:
            locations.append({"runtime": p.get("id"), "label": p.get("label"),
                              "paths": paths, "env": p.get("env") or ""})
    return {
        "found": [{"id": p.get("id"), "label": p.get("label")} for p in found],
        "found_count": len(found),
        "blocked": blocked,
        "locations": locations,
        "runtimes_checked": len(probes),
    }


def detection_summary(probes: list = None) -> dict:
    """The SERVABLE half of :func:`detection_report`: no paths, ever.

    ``detection_report`` carries ``locations``, which is the full per-runtime
    probe map for all 30 runtimes. That belongs in ``clawmetry diagnose`` --
    a local command whose output a person chooses to share -- and not in an
    HTTP response, where it becomes a tidy copy-pasteable detection map that
    ships with every install and lands in every screenshot of the empty
    state. The paths are readable in this file either way; a finished map
    rendered in the product is a different artefact from a table in source.

    So the endpoint serves the counts and the blocked reasons, which is
    everything a screen needs to stop saying "you have no data" when the
    truth is "I was refused".
    """
    report = detection_report(probes)
    return {
        "found": report["found"],
        "found_count": report["found_count"],
        "blocked": report["blocked"],
        "runtimes_checked": report["runtimes_checked"],
    }


def _render_nothing_detected(probes: list) -> list:
    """Copy for the machine where no runtime was detected (#5716).

    The onboarding wizard is a screen, so it gets the same treatment as the
    dashboard: the count and the blocked case, no probed paths. ``clawmetry
    diagnose`` is where the map lives.
    """
    report = detection_summary(probes)
    blocked = report.get("blocked") or []
    lines: list = []
    if blocked:
        lines.append("Agent data looks present on this machine, but could not be read:")
        for b in blocked[:4]:
            lines.append(f"  {b.get('label') or b.get('runtime')}: {b.get('reason')}")
        lines.append("")
        lines.append("Run 'clawmetry diagnose' to see exactly where ClawMetry looked.")
        return lines
    checked = report.get("runtimes_checked") or len(probes)
    return [
        f"No agent runtime detected yet. ClawMetry checked {checked} runtimes and found none.",
        "Run 'clawmetry diagnose' to see exactly where it looked.",
        "",
        "Start an agent and ClawMetry picks it up on its own. Nothing to configure.",
    ]


def render_detection_lines(probes: list) -> list:
    """Plain-words onboarding copy for the probe results.

    Pure function (list of printable lines, no ANSI) so the wizard can style
    it and tests can pin it.

    When nothing was detected this used to return ``[]`` and the wizard
    printed nothing at all, which is the same silence the dashboard's first
    screen had (#5716): a person watching an empty install could not tell
    "no agent has run here" from "ClawMetry cannot read them". Now it says
    where it looked, and leads with the runtimes whose data is present but
    unreadable, because that is the one the reader can fix.
    """
    found = [p for p in probes if p.get("found")]
    if not found:
        return _render_nothing_detected(probes)
    n = len(found)
    plural = "runtime" if n == 1 else "runtimes"
    lines = [f"Detected {n} AI agent {plural} on this machine:"]
    # Compact grid, 3 per row: ten detections should read as one confident
    # block of checkmarks, not a ten-line paywall ledger (per-line tier
    # labels moved into the two summary lines below).
    cell = max(len(p["label"]) for p in found) + 3
    for i in range(0, n, 3):
        row = "".join(f"[x] {p['label']:<{cell}}" for p in found[i : i + 3])
        lines.append("  " + row.rstrip())
    paid = [p for p in found if not p.get("free")]
    if paid:
        lines.append("")
    if len(paid) == 1:
        lines.append(
            f"A free 7-day Pro trial (sign in below) unlocks {paid[0]['label']} too, or paste a license key."
        )
    elif paid:
        lines.append(
            f"A free 7-day Pro trial (sign in below) unlocks the other {len(paid)}, or paste a license key."
        )
    return lines
