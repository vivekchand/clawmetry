# `ci-node/` — the npm pin sets CI installs

Each subdirectory here is a `package.json` + `package-lock.json` pair that a CI
job installs with `npm ci`, so the job runs a recorded tree with an integrity
hash for every tarball instead of whatever the registry serves for a version at
run time. Nothing here ships in the wheel or is imported by the app.

| Directory | Installed by |
|---|---|
| `claude-cli/` | `harness-observability-audit`, `i18n-autotranslate`, `i18n-docs-autotranslate` |
| `auth-bootstrap/` | `auth-bootstrap-guard` (the pinned Playwright its smoke test runs on) |

## Why these live outside `.github/`

A lockfile is only half a pin. The other half is the Dependabot entry that lets
it move, because a frozen lockfile accumulates advisories exactly as a moving
dist-tag accumulates surprises. On this account an npm Dependabot entry whose
`directory:` is under `.github/` cannot deliver that half: the updater resolves
the new version and writes the files, then the pull-request call is refused
with `400 — The request contains invalid or unauthorized changes`, and the job
ends with `dependency_file_not_supported`. Nothing is opened, and the only place
it is visible is the updater log.

Measured on 2026-11-24 over the Dependabot `npm_and_yarn` job history of
`clawmetry`, `clawmetry-pro` and `clawmetry-cloud`:

| `directory:` | runs | result |
|---|---|---|
| outside `.github/` (`/frontend`, `/tests/e2e`, `/clawhub-plugin`, `/sdk/typescript`, `/scripts/harness`, `/.`) | 91 | 91 succeeded |
| under `.github/` (`/.github/claude-cli`, `/.github/ci-node/auth-bootstrap`, `/.github/actions/setup-openclaw`, `/.github/ci-node/demo-lab-clis`) | 87 | 82 failed; the 5 successes are all on or before 2026-09-18 |

The same package in both places settles it. `@anthropic-ai/claude-code` is
pinned in `clawmetry-pro` at `scripts/harness` and was pinned here at
`.github/claude-cli`; the manifests are the same shape and neither carries
`overrides`. The copy outside `.github/` took three Dependabot bumps and sits
at `2.1.329`. The copy under it has not moved since the commit that added it,
and sits at `2.1.251` — the gap is the whole point: every advisory fix
published in between had to be noticed and applied by a person, or not at
all.

`pip` entries under `.github/` (`/.github/requirements`) are unaffected and
keep opening pull requests, so this is specific to npm rather than to the path.
The upstream cause is not documented by GitHub and reports of it elsewhere
disagree about the mechanism, which is why the fix here is the one thing the
measurement actually supports: keep npm pin sets out of `.github/`.

### What is still under `.github/`

Two npm pin sets cannot simply move and are left as they are:

- `.github/actions/setup-openclaw/` — a composite action installs it, and its
  `package.json` and lockfile have to sit beside `action.yml`.
- `.github/scripts/` — holds the workflow scripts themselves
  (`visual-diff.mjs`, `post-visual-diff.mjs`), not only a pin set.

Both keep needing their advisory fixes raised by hand until they are given
somewhere else to live. Add a new pin set here, not under `.github/`.
