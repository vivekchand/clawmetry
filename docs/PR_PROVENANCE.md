# PR provenance: agent sessions on a pull request's files

`clawmetry trace report` tells a pull request's reviewers which AI agent sessions
wrote which changed files. It shows the runtime, model and cost of each session
and any Guard findings it raised. The output goes where review already happens:
SARIF annotations in code scanning, one pull-request comment, and an opt-in
check.

Requirement: REQ-OBS-PRP-001 ([Software Factory](https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/4e224b46-71a6-4d32-933d-7fb6bfde30d0)).
Issue: vivekchand/clawmetry#5946.

## What it is not

- **Not a code scanner.** ClawMetry adds no finding about code content. The
  only ClawMetry results are provenance notes and Guard findings, which describe
  what an agent session *did* while it ran. Vulnerability findings come from the
  scanners you already run (Semgrep, Snyk, CodeQL and others). Pass their SARIF
  in, and the findings on agent-written files come back with the session attached.
- **Not proof of cause.** A link between a file and a session is association.
  Every link and every annotation carries its basis:

  | basis | meaning | limit |
  |---|---|---|
  | `commit_trailer` | a commit in the change carries `Clawmetry-Session: <id>` (written by `clawmetry trace init`) and changed the file | a human may have edited lines in the same commit |
  | `observed_write` | the session's own transcript holds a write tool call (Write, Edit, MultiEdit, apply_patch, ...) on that path before the head commit | a later human edit is not excluded |

  A file written without a path argument is not observed: a shell redirection,
  a generated file, or a write into a different checkout of the same
  repository. Such a file is reported as **unattributed**, never guessed,
  unless a commit trailer names the session.
- **Not deployment authorization.** Your CI owns that. The gate is one input
  your pipeline may opt into.

## What is never written

No prompt text, no tool output, no credential-shaped value, in the SARIF, the
markdown, the JSON report, the console or the bundle. Scanner text copied into
the output passes secret redaction. Guard finding titles pass the stricter
redaction PR Trace applies before publishing: secrets, home paths, email
addresses, IP addresses and provider ids. A session is referenced by its local
id (`clawmetry://session/<id>`), which resolves only on the machine that
recorded it.

## Where the evidence comes from

A CI runner has no ClawMetry store: the transcripts live on the machine the
agent ran on. So there are two modes.

**On the developer's machine** (or a self-hosted runner that has the store):

```bash
clawmetry trace report --export-bundle .clawmetry/pr-provenance.json
git add .clawmetry/pr-provenance.json && git commit -m "chore: provenance bundle"
```

**On the CI runner**, from the bundle, with no store and no network:

```bash
clawmetry trace report --bundle .clawmetry/pr-provenance.json \
  --base "$BASE_SHA" --head "$HEAD_SHA" \
  --scanner-sarif semgrep.sarif --sarif-out provenance.sarif
```

The bundle holds the commits it examined, the changed files, the links, and
per session: runtime, models, cost with its basis (`measured` or `unknown`,
never an invented zero) and redacted Guard findings. A commit that only adds
the bundle is not counted against coverage.

### Binding evidence to the change

| evidence status | when |
|---|---|
| `ok` | every commit in the change was examined by the bundle's exporter (or the report read the store directly) |
| `partial` | commits in the change are not in the bundle, for example pushed after the export |
| `stale` | the bundle is older than `--max-evidence-age-hours` |
| `invalid` | the digest does not match the content, or the bundle covers none of this change's commits (it belongs to another change) |
| `missing` | no bundle and no store |

The bundle's `digest` is a sha256 over its content. It detects a bundle edited
after export. **It is an integrity check, not proof of authenticity**:
authenticity rests on where the bundle is stored and who can write there.

## The gate

Off unless you enable it. While off, the report exits 0 whatever it finds.

```bash
clawmetry trace report --bundle ... \
  --fail-on critical \              # or warning
  --on-missing-evidence fail \       # required: fail or pass
  --exceptions exceptions.json --actor "$GITHUB_ACTOR"
```

- `--fail-on` without `--on-missing-evidence` exits 2 and evaluates nothing.
  A default there would silently block or silently allow a change.
- Gate inputs are Guard findings of linked sessions and scanner findings on
  linked files. SARIF level `error` counts as critical, `warning` as warning,
  anything else as note. Findings on files no session is linked to do not gate.
- An exception needs `id`, `rule`, `expires`, `approved_by` and `reason`, and
  may narrow by `path`, `session_id` or `tool`. A date-only `expires` stops
  applying at 00:00 UTC that day. An expired exception does not apply and is
  listed as expired. One missing a field is rejected and listed.

```json
{"exceptions": [
  {"id": "EX-12", "rule": "clawmetry/guard/credential_access", "path": "app/db.py",
   "expires": "2026-10-01", "approved_by": "security-owner", "reason": "test fixture credentials"}
]}
```

Every decision records `outcome`, `rule_version`, `threshold`,
`evidence_behaviour`, `evidence_status`, `actor`, `decided_at`, `head_sha`,
`blocking`, `exceptions_applied`, `exceptions_expired` and
`exceptions_rejected`. It is written to `--json-out` and to the SARIF run's
`properties.clawmetry.gate`.

Exit codes: `0` report written (gate passed or off), `1` gate failed, `2`
usage or configuration error.

## GitHub Actions

```yaml
on: pull_request
permissions:
  contents: read
  security-events: write   # SARIF upload
  pull-requests: write     # the comment
jobs:
  provenance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<sha>
        with:
          fetch-depth: 0
      # ... run your scanner, writing semgrep.sarif ...
      - uses: vivekchand/clawmetry/integrations/github-action@<sha>
        with:
          bundle: .clawmetry/pr-provenance.json
          scanner-sarif: semgrep.sarif
          # fail-on: critical
          # on-missing-evidence: fail
```

The action installs clawmetry and runs the report. It uploads the SARIF to code
scanning and keeps one pull-request comment, found by a hidden marker and
edited on later runs. It writes the markdown to the job summary and then
applies the gate's exit code. A pull request from a fork gets a read-only token,
so the upload and the comment fail there. This repository runs the action
against a scratch demo repository in `.github/workflows/pr-provenance-action.yml`.

## Not yet

- An Azure DevOps task or another CI wrapper.
- Exporting the bundle automatically on `git push`. Today it is a command.
- Gating on agent evaluation scores.
- Signed bundles, and linking the decision into the Compliance Pack evidence bundle.
