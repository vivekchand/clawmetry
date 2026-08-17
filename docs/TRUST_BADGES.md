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

### 6. CISA Secure Software Development Attestation
**Cost: $0. Effort: ~half a day. US entity — this one is ours to take.**

https://www.cisa.gov/secure-software-attestation-form — the self-attestation a
software producer must file to sell to US federal agencies. The requirement
cascades: federal *contractors* increasingly ask their own suppliers for it,
so it shows up well outside government deals.

The reason to do this now rather than later: its four attestation areas are
almost exactly what this branch just built.

| CISA attestation area | What we can already point at |
|---|---|
| Software developed and built in a secure environment | GitHub-hosted CI, branch protection, no long-lived publish credential once Trusted Publishing is on |
| Good-faith effort to maintain trusted source code supply chains | `scripts/verify_vendor.py` byte-compares every vendored bundle to its published npm release |
| Data provenance maintained for internal and third-party code | `scripts/vendor.lock.json` + CycloneDX SBOM per release |
| Automated tooling checks for vulnerabilities | `pip-audit` + OpenSSF Scorecard, per PR and weekly |

Filing it is mostly transcription. Don't attest to anything not actually true —
this one is signed by a company officer and carries real liability, unlike a
marketing badge.

---

## Paid — within a $500 budget

**Entity: Instalabs LLC, a US entity.** That settles two things below.

### 1. GDPR EU representative (Article 27) — ~$110-750/yr, IF it applies
**Answer the establishment question first — it may cost nothing.**

Every EU enterprise DPA review asks who your Article 27 representative is, and
unlike SOC 2 it cannot be waved through as "in progress": the answer is a name
and an EU address, or it is nothing. So this needs a settled answer either way.

But **do not buy a representative before checking whether we need one.**
Article 27 applies only to a controller *not established in the Union*. The
entity is a Wyoming LLC, which points one way — but the sole owner-operator is
resident in the Netherlands, and GDPR "establishment" turns on stable
arrangements and where activities are actually carried out, not on where the
company is registered. If the business is effectively run from the NL, there is
a real argument that:

- GDPR applies directly under Article 3(1) rather than 3(2);
- **no Article 27 representative is required**; and
- there is a lead supervisory authority (the Dutch AP), which is a *better*
  answer to give an EU buyer than a contracted mailbox.

That is a lawyer question, not an engineering one, and it cuts both ways —
an EU establishment also brings obligations a pure Art. 27 appointment does
not. Get a one-off opinion (far cheaper than getting it wrong in either
direction), then either:

- **Not established in the EU** → appoint a representative. Providers run
  ~€100/yr (DataRep minimum annual appointment) to ~€490-708/yr (EU Shield,
  Engage Compliance); some are pay-as-you-go, free until a data-subject
  request arrives. The cheap end is fine at our volume.
- **Established in the EU** → skip the purchase, name the lead supervisory
  authority in the privacy policy instead.

Either way, publish the conclusion in the privacy policy and in `SECURITY.md`'s
compliance table. The gap that actually hurts is having *no* answer.

### 2. Cyber / Tech E&O insurance — quote it, expect above budget
**Not $500, but get the number now.**

US market rates for a small software company: roughly **$1,500-4,000/yr** for
bundled Tech E&O + cyber at under ~$2M revenue; basic cyber alone can start
near $1,000. Brokers serving startups: Vouch, Coalition, Insureon,
TechInsurance.

Why it belongs on this list even though it exceeds the budget: an MSA
routinely requires **$2-5M** of cyber/E&O cover, and that is a hard gate no
amount of engineering clears. It is the single most likely thing to stop a
signed pilot at the paperwork stage. Get a quote before a deal is on the
table, not during it — bind it when the first contract requires it.

### Not applicable to us

**Cyber Essentials (UK, IASME, ~£300+VAT)** was the previous recommendation
here and is now **ruled out**. It certifies UK-registered organisations, and
its genuinely valuable part — bundled cyber liability insurance for UK
entities under £20m turnover — is UK-only. As a US LLC we get neither. The
insurance need is real; item 2 above is how a US entity meets it.

### Not worth it at this budget

| | Cost | Why not |
|---|---|---|
| SOC 2 Type II | $15-50k + 3-6 month observation window | Start the clock when a design partner asks, in parallel with the pilot — not speculatively |
| ISO 27001 / 42001 | $20k+ | Same, and less commonly demanded by US buyers than SOC 2 |
| Independent pen test | $8-25k | Real value, but commission it when a buyer requires the report |
| CSA STAR Valid-AI-ted | $595 | Over budget; same registry entry as the free listing |

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
HSTS.

**This month:** OpenSSF Best Practices `passing` (free); CSA STAR Level 1
(free); CISA Secure Software Development Attestation (free); **settle the GDPR
establishment question** and then either appoint an Article 27 representative
(~$110-750/yr) or document the lead supervisory authority (free).

**Get the number, bind later:** cyber / Tech E&O quote. Above budget, but the
most likely single thing to stall a signed pilot at the paperwork stage.

**When a buyer asks, not before:** SOC 2 clock, pen test, DPA, SSO. Every
artifact built against an imagined buyer is worthless, and these all expire or
drift.

---

## Prerequisites that are not badges

These block a deal harder than any missing certification, and no badge
substitutes:

1. ~~`security@clawmetry.com` must exist.~~ **Done** — the mailbox is live.
   `SECURITY.md` and `security.txt` both publish it.
2. **`clawmetry.com/security` currently 404s** while `SECURITY.md` is the real
   policy. Redirect it, or the badge links to nothing.
3. **`clawmetry.com/enterprise` promises artifacts that do not exist** — DPA
   templates, pentest summaries, a controls roadmap, an IR plan. Delete those
   claims. Being caught overstating costs more than every badge here earns.
   (Both live in the landing-site repo, not this one.)
4. **There is no answer to "who is your EU representative / lead supervisory
   authority?"** See the paid section. The answer may be free (if the business
   counts as EU-established through its NL-resident operator) or ~€100-700/yr
   (if not) — but it has to be *one of the two*. This is the one item on this
   page a buyer's DPA review cannot accept as "in progress".
