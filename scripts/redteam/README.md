# Red-team detection corpus

One question, asked every day: **an attack really happened to somebody — would we have caught it?**

`scripts/harness/audit.py` asks what a harness exposes that we fail to *observe*. This asks the
sharper version. Each file in `corpus/` is one publicly disclosed attack against an agent runtime,
written down as a reproducible case with the detector that must fire and the severity it must reach.
A corpus entry is a signature. A case that fails is either a gap worth an issue or a regression
worth a red build.

```bash
python3 scripts/redteam/audit.py                     # run everything, print verdicts
python3 scripts/redteam/audit.py --case gitspawn-core-fsmonitor
python3 scripts/redteam/audit.py --json report.json  # machine-readable
python3 scripts/redteam/audit.py --file-issues       # open sec-gap issues (private tracker)
pytest tests/test_redteam_corpus.py                  # the same corpus, as a CI gate
```

## Two surfaces, because attacks arrive on both

**`tool_stream`** — synthetic events fed to `detectors.run_all`. This is what the agent *chose* to do,
and it is the surface every behavioural detector already reads.

**`repo_config` / `agent_config`** — files materialised into a throwaway workspace and handed to
`clawmetry.repo_scan`. GitSpawn lives here, and it is exactly what a tool-stream detector cannot see:
a repository's own `.git/config` names a program in `core.fsmonitor`, git runs it during a routine
background `git status`, and the code executes outside the sandbox before any approval prompt. The
agent called no tool. Opening the folder was the exploit.

That second surface is why `repo_scan` exists at all. It was written because this audit reported
`MISS` on five cases in a row and made the shape of the blind spot impossible to argue with.

## Controls are load-bearing

Four cases are marked `"control": true` and they are not padding.

- Two **positives** (`control-credential-exfil`, `control-privilege-change`) must be caught by detectors
  that already ship. If one stops firing, the audit's verdict on everything else is worthless, so a
  control failure exits `2` and is reported separately from gaps.
- Two **negatives** must produce silence. `control-benign-repo` carries a real git-lfs config:
  `filter.lfs.clean` is a command-valued key in millions of legitimate repositories, and a scanner
  that cannot tell git-lfs from a payload gets muted within a week and then protects nobody.
  `control-ordinary-dev-session` is a working day in the tool stream (install, read `.env.example`,
  run tests, push), and it sits beside the two supply-chain cases for the same reason.

The false-positive half is not a formality. Measured across 50 real repositories on a working
machine, the first version of `repo_scan` flagged **clawmetry itself** — `core.hooksPath` pointing at
the default `.git/hooks`. The current version reports **0 critical, 3 warning** on the same 50.

## What is deliberately NOT here

A case is a signature for something we catch. Three disclosed attacks were measured against the
detectors and are recorded as `sec-gap` issues on the private tracker instead, with the audit's own
verdict pasted in, because a corpus entry that always fails is a red build nobody can act on:

- **npm postinstall credential harvesting.** Measured verdict: `MISS — nothing fired at all`. The
  agent's tool stream for the attack is byte-identical to the tool stream for an ordinary
  `npm install`, so no tool-stream detector can separate them, ever. The visible half (the agent
  itself reading the token file) is covered by `npm-postinstall-visible-harvest`.
- **Cross-session coordination** (the Hugging Face evaluation swarm using a shared package cache as
  a covert channel). Every detector we ship is per-session, and so is this runner: the case cannot
  even be *written* here, which is a finding about the corpus as much as about the detectors.
- **Credential scoping bypass** (session-scoped credentials outliving their session). Nothing in the
  tool stream distinguishes a credential that should have expired from one that should not.

## Writing a case

```jsonc
{
  "id": "kebab-case-id",
  "name": "One line a human can scan",
  "disclosed": "2026-09-01",
  "source": "https://…",              // required — a signature with no disclosure is folklore
  "cve": ["CVE-2026-72718"],
  "attack_class": "silent-rce",       // silent-rce | persistence | exfiltration | privilege-escalation
  "surface": "repo_config",           // repo_config | agent_config | tool_stream
  "affects_runtimes": ["claude_code", "cursor"],
  "summary": "What the attack does.",
  "why_hard_to_see": "Why our existing detectors would miss it.",

  "workspace": {"files": {".git/config": "[core]\n\tfsmonitor = {{MARKER_CMD}}\n"}},
  "events":    [{"event_type": "tool_call", "ts": "…", "data": {"tool": "Bash", "args": {…}}}],

  "expect": {
    "detected": true,
    "any_of": ["repo_config_exec"],
    "min_severity": "critical",
    "rationale": "What closing this gap actually means."
  }
}
```

Events are written **chronologically**; the runner reverses them, because the store hands detectors
events newest-first and nobody writes an attack down backwards.

### Payloads must be inert

`{{MARKER_CMD}}` is the only payload a case may carry. The runner expands it to a command that writes
a marker file inside a temp directory and does nothing else, then **fails the case with
`UNSAFE-CORPUS` if that marker ever appears** — a case may describe execution, never perform it.
`test_corpus_payloads_are_inert` additionally rejects any case with a literal `curl`, `wget`,
`rm -rf`, `nc` or `base64 -d` in its workspace files.

Workspaces are materialised under `tempfile.mkdtemp()` and removed afterwards. Nothing is written
inside a real repository, and no case ever invokes `git` — asking git to read an untrusted
repository's config is part of how several of these bugs fire in the first place.

## Severity means recognition, not suppression

husky points `core.hooksPath` at the working tree. Those hooks travel with a clone and run on
ordinary git commands, which is *mechanically the same thing GitSpawn abuses*. Hiding husky would be
dishonest; calling it critical would get the scanner muted. So a recognised hook manager is reported
at `warning`, named, with the mechanism spelled out — and an unrecognised directory in the same key
stays `critical`.

The same rule splits CHAINDROP in two: a committed `.claude/settings.json` is usually the project
author's own tooling (`warning`, "check `git log` on this file"), while a gitignored
`.claude/settings.local.json` has no provenance a reviewer can check and outranks it (`critical`).

## Adding a signature after a new disclosure

1. Write the case. Ground it in the disclosure; do not invent a mechanism.
2. Run `--case <id>`. Expect `MISS` — that is the point.
3. Either close the gap in `repo_scan`/`detectors`, or run `--file-issues` and let the tracker hold it.
   "We looked and we do not catch it" is a fine outcome; an unrecorded one is not.
4. Add a negative control if the new detector could plausibly fire on ordinary behaviour.
5. Confirm the corpus is still green, **including the controls**.
