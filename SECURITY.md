# Security Policy

ClawMetry runs on developer machines and reads AI agent transcripts. That is
sensitive material, so this document states plainly what we protect, what we
do not, how to report a problem, and how fast we will answer.

- **Report a vulnerability:** security@clawmetry.com, or a
  [private GitHub advisory](https://github.com/vivekchand/clawmetry/security/advisories/new).
  Please do not open a public issue for a security bug.
- **Network egress inventory:** [docs/EGRESS.md](docs/EGRESS.md) — every
  outbound destination, what it sends, and how to disable it.

## Reporting a vulnerability

Email **security@clawmetry.com** or file a private advisory through GitHub.
Include what you found, how to reproduce it, and what an attacker gains. A
proof of concept helps but is not required to report.

### What you can expect

| Stage | Target |
|---|---|
| Acknowledgement that a human read your report | 2 business days |
| Initial assessment: confirmed / not reproducible / need more detail, with a severity | 5 business days |
| Fix released for a confirmed critical or high | 30 days |
| Fix released for a confirmed medium or low | next scheduled release |

These are targets from a small maintainer team, not a contractual SLA. If a
deadline is going to slip you will be told, with a reason, rather than left
waiting. Enterprise customers with a support agreement have separate,
contractual response terms.

### Disclosure

Coordinated disclosure. We ask for 90 days from acknowledgement before public
detail, or until a fix ships if that is sooner. If a vulnerability is being
exploited we will move faster and say so. Reporters are credited in the
advisory and the changelog by default; tell us if you would rather not be.

We do not currently run a paid bug bounty.

## Supported versions

ClawMetry releases continuously from `main`, and nodes on the managed cloud
track the latest release.

| Version | Supported |
|---|---|
| Latest release on PyPI | Yes — all fixes land here |
| Anything older | No — upgrade to the latest release |
| Enterprise self-hosted pinned versions | Per your support agreement |

There is no long-term-support branch in the open-source project. Security
fixes ship as a new release rather than being backported.

## Scope

### In scope

- The `clawmetry` package: dashboard, sync daemon, CLI, local store, proxy.
- The self-hosted server (`SELF_HOSTED=true`) and its ingest API.
- `clawmetry.com`, `app.clawmetry.com`, `ingest.clawmetry.com`.
- The published PyPI package and the installer scripts.

Especially wanted: anything that reads agent transcripts across a trust
boundary, that lets a local process reach the dashboard without a credential,
that gets code onto a node through the update or licensing path, or that
causes traffic to a host not listed in [docs/EGRESS.md](docs/EGRESS.md).

### Out of scope

- Vulnerabilities in the agent runtimes ClawMetry observes — report those to
  their maintainers.
- Findings that require an already-compromised machine or root on the host.
  ClawMetry's data is readable by anyone who already owns the account it runs
  under; that is the operating system's trust boundary, not ours.
- Missing hardening headers with no demonstrated impact, raw scanner output
  with no exploit path, and social engineering of maintainers.
- Denial of service by resource exhaustion against a local dashboard.

## Security model

**Read-only by default.** ClawMetry observes agent runtimes. It does not
modify agent behaviour, except where you explicitly opt in (cron management
and the enforcement proxy).

**Local-first.** All data lives in DuckDB at `~/.clawmetry/`. Nothing is
uploaded unless you run `clawmetry connect`.

**End-to-end encrypted cloud sync.** Snapshots are encrypted client-side with
AES-256-GCM. The key is generated locally, never transmitted, and not
recoverable by us — the browser decrypts for display. A compromise of our
storage yields ciphertext.

**Localhost binding.** The dashboard binds `127.0.0.1`. Binding to a
non-loopback address puts it on the network: put it behind a reverse proxy
that terminates TLS and authenticates.

### Known limitations

Stated because a security review will find them anyway, and because knowing
where the edges are is more useful than a clean-looking list:

- **A loopback request is trusted without a credential.** Any process running
  as any user on the machine can read the dashboard API. On a single-user
  workstation this matches the OS boundary. On a shared build host, a
  multi-tenant jump box, or a cloud dev environment it does not — treat
  ClawMetry as readable by every local process there.
- **The bearer token may be supplied as a URL query parameter**, so it can
  reach proxy logs, browser history and `Referer` headers. Prefer the
  `Authorization` header.
- **No SSO, SAML, OIDC or SCIM.** Self-hosted authentication is a shared node
  token plus HTTP Basic admin credentials, configured by environment variable.
  Front it with your own identity-aware proxy if you need real identity.
- **The admin audit log is not attributed to a user identity** — there is no
  identity model to attribute it to (see above).
- **No SOC 2 or ISO 27001 certification.** See the status table below rather
  than assuming either exists.

## Deployment guidance

**Workstation (default).** `pip install clawmetry && clawmetry`. Bound to
localhost; nothing else required.

**Shared or multi-tenant host.** Assume any local process can read the
dashboard. Run it as a dedicated user with a restrictive umask, or don't run
it there.

**Networked / self-hosted.** Set `SELF_HOSTED=true`. Put it behind a reverse
proxy that terminates TLS and enforces authentication. Set
`CLAWMETRY_API_TOKENS` and `CLAWMETRY_ADMIN_PASSWORD` to values from a
password manager, never defaults. See
[deploy/self-hosted/](deploy/self-hosted/).

**Air-gapped.** `SELF_HOSTED=true` plus `CLAWMETRY_OFFLINE=1` for fully local
licensing and zero outbound calls. Verify against
[docs/EGRESS.md](docs/EGRESS.md).

## Supply chain

- **No third-party asset loads.** Served pages contact no external origin —
  no CDN, no font provider, no analytics. Enforced in CI by
  `scripts/verify_no_external_assets.py`.
- **Vendored JavaScript is provenance-locked.** `scripts/vendor.lock.json`
  records package, version, license and SHA-256 for every bundle;
  `scripts/verify_vendor.py` re-downloads the npm registry tarball and
  byte-compares on every CI run.
- **Dependency auditing.** `pip-audit` and a CycloneDX SBOM run per PR and
  weekly on a schedule, so a fresh advisory surfaces without a code change.
- **Minimal dependencies** by design — Flask, waitress, cryptography, duckdb.

## Compliance status

Stated honestly, because a vendor questionnaire will ask and an optimistic
answer is worse than a missing one.

| | Status |
|---|---|
| Data residency / self-hosted | **Available** — single-tenant, air-gapped supported |
| SBOM (CycloneDX) | **Available** — generated per CI run |
| Egress inventory | **Available** — [docs/EGRESS.md](docs/EGRESS.md) |
| Vulnerability disclosure policy | **Available** — this document |
| SOC 2 Type II | Not started |
| ISO 27001 / ISO 42001 | Not started |
| Independent penetration test | Not yet commissioned |
| DPA / sub-processor list | Available on request; not yet published |
| SSO / SAML / SCIM | Not implemented |

If you need one of the missing items to evaluate ClawMetry, say so at
security@clawmetry.com — that demand is how this list gets reordered.
