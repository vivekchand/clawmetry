# Trust badges and certifications: what we have, what to get, what it costs

A working list for making ClawMetry survive an enterprise security review.
Ordered by value per pound, not by prestige.

The honest frame: **badges do not close deals.** A CISO does not buy because of
a Scorecard score. What badges do is stop a deal *stalling* — they answer the
first ten questions of a vendor questionnaire before anyone has to email us,
and they signal that a small vendor takes this seriously. Get the free ones
because they cost only time; buy only what a real buyer has actually asked for.

Prices verified 2026-08-17. Re-check before spending.

---

## Already done (in this branch)

| Item | What it proves | Where |
|---|---|---|
| **CycloneDX SBOM** | Full dependency inventory, per CI run and per release | `.github/workflows/supply-chain.yml` |
| **pip-audit** | No known-vulnerable dependencies, re-checked weekly not just at merge | same |
| **OpenSSF Scorecard** | Automated security-health score, published + SARIF to the Security tab | same |
| **Vendored-asset provenance** | Every third-party JS bundle byte-matches its published npm release | `scripts/verify_vendor.py`, `scripts/vendor.lock.json` |
| **Zero third-party asset loads** | Dashboard contacts no external origin, enforced in CI | `scripts/verify_no_external_assets.py` |
| **Egress inventory** | Every outbound destination, documented and testable | `docs/EGRESS.md` |
| **Vulnerability disclosure policy** | Contact, response targets, scope, coordinated disclosure | `SECURITY.md` |
| **RFC 9116 security.txt** | Machine-readable security contact, served by the app itself | `/.well-known/security.txt` |
| **GitHub build provenance** | Signed link from artifact to workflow run and commit | `.github/workflows/publish.yml` |

---

## Free — do these next

### 1. PyPI Trusted Publishing + PEP 740 attestations
**Cost: £0. Effort: ~2 minutes on PyPI, then flip one repo variable.**

The single highest-value item left. Two wins:

- **Deletes a standing credential.** `PYPI_API_TOKEN` is a long-lived secret
  that can publish to PyPI. "What happens if your CI is compromised?" is a
  standard question, and "there is no persistent publishing credential" is a
  much better answer than "it's in GitHub secrets."
- **Puts a Provenance badge on every release file**, cryptographically linking
  it to the workflow run that built it — verifiable by anyone, without
  trusting us.

Worth noting: this is a *stronger* claim than the Ed25519 self-attestation
competitors sell, and it is free, standard, and issued by an index we don't
control. Already wired in `publish.yml`; see the comment block there for the
three steps.

### 2. OpenSSF Best Practices Badge
**Cost: £0. Effort: 2-3 hours of form-filling. Self-certified.**

https://www.bestpractices.dev — passing / silver / gold tiers. Self-asserted,
so it proves process rather than audit, but it is the recognised
open-source-hygiene badge and most criteria are already met (MIT license,
public repo, CI, tests, this security policy, disclosure process).

Do `passing` now. Silver wants things we lack (signed releases — item 1 covers
this; a documented security review process). Gold needs two maintainers, so it
is out of reach while this is a solo project. Say so rather than chasing it.

### 3. CSA STAR Level 1 (CAIQ self-assessment)
**Cost: £0 for standard submission. Effort: 1-2 days.**

https://cloudsecurityalliance.org/star/submit — a public registry listing many
enterprise procurement teams check by name. The CAIQ is ~260 questions across
the Cloud Controls Matrix.

Two warnings:

- **Answer honestly.** A published CAIQ is a public document, and inflated
  answers are far worse than absent ones — this is the same failure mode as the
  `/enterprise` page promising a DPA and pen test that don't exist. Many answers
  will legitimately be "not applicable — customer-managed, single-tenant
  self-hosted" or "no."
- Don't pay for **Valid-AI-ted** ($595). It is over budget and adds AI
  consistency-checking, not assurance. The free listing is the same registry
  entry.

### 4. GitHub-native, zero cost
- **CodeQL** default setup — one click in Settings > Security.
- **Dependabot** alerts + security updates — one click.
- **Private vulnerability reporting** — one click; already referenced from
  `SECURITY.md`, so turn it on or that link 404s.
- **Branch protection on `main`** — also lifts the Scorecard score.

### 5. Domain and email hygiene
SPF, DKIM, DMARC on `clawmetry.com`; HSTS preload; TLS config to an A on SSL
Labs. Free, and it is the first thing an automated vendor-risk scanner
(SecurityScorecard, BitSight) grades you on — often *before* a human reads
anything. A poor external rating can sink a deal without a conversation.

---

## Paid — within a £500 budget

### Cyber Essentials (UK, IASME) — ~£300 + VAT
**The only paid certification worth it at this budget, if the entity qualifies.**

- Government-backed, recognised in UK procurement, and mandatory for many UK
  public-sector contracts.
- Self-assessment questionnaire, verified by IASME. Days, not months.
- **Includes free Cyber Liability Insurance** for UK-registered organisations
  with turnover under £20m. That matters more than the badge: an MSA typically
  requires £2-5M cyber/E&O cover, which is a hard gate no amount of engineering
  clears.

**Open question before spending:** this requires a **UK-registered** entity.
If ClawMetry trades through a US LLC, the certification may not apply and the
insurance definitely will not. Confirm the trading entity first. If it is
US-only, skip this and put the £300 toward a cyber liability quote directly.

### Not worth it at this budget

| | Cost | Why not |
|---|---|---|
| SOC 2 Type II | $15-50k + 3-6 month observation window | Start the clock when a design partner asks, in parallel with the pilot — not speculatively |
| ISO 27001 / 42001 | $20k+ | Same, and less commonly demanded by US buyers than SOC 2 |
| Independent pen test | $8-25k | Real value, but commission it when a buyer requires the report |
| CSA STAR Valid-AI-ted | $595 | Over budget; same registry entry as the free listing |
| Paid trust-centre SaaS | $10k+/yr | `SECURITY.md` + `docs/EGRESS.md` do the same job at this stage |

---

## Sequencing

**This week (free):** flip PyPI Trusted Publishing; turn on CodeQL, Dependabot,
private vulnerability reporting, branch protection; fix SPF/DKIM/DMARC and
HSTS; create `security@clawmetry.com`.

**This month (free):** OpenSSF Best Practices `passing`; CSA STAR Level 1.

**When a buyer asks, not before:** SOC 2 clock, pen test, DPA, SSO. Every
artifact built against an imagined buyer is worthless, and these three all
expire or drift.

**Decide:** Cyber Essentials, contingent on the entity question above.

---

## Prerequisites that are not badges

These block a deal harder than any missing certification, and no badge
substitutes:

1. **`security@clawmetry.com` must exist.** `SECURITY.md` and `security.txt`
   both publish it. A published contact that bounces is worse than none.
2. **`clawmetry.com/security` currently 404s** while `SECURITY.md` is the real
   policy. Redirect it, or the badge links to nothing.
3. **`clawmetry.com/enterprise` promises artifacts that do not exist** — DPA
   templates, pentest summaries, a controls roadmap, an IR plan. Delete those
   claims. Being caught overstating costs more than every badge here earns.
   (Both live in the landing-site repo, not this one.)
