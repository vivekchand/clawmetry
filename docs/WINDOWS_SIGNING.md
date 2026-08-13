# Windows code signing — activation guide

End state we want: a Windows user double-clicks
`ClawMetry-windows-setup.exe` and it just installs. **No "Windows
protected your PC" wall. No "Unknown publisher". No orange bar.** The
publisher string reads `InstaLabs LLC`, verified.

**The CI is already wired for this.** PR #4705 (2026-08-10) landed the
Authenticode signing pipeline: `.github/workflows/desktop-artifacts.yml`
already signs the tray `ClawMetry.exe`, the NSIS installer, and the
embedded uninstaller stub whenever the right secrets exist. All that's
missing is (a) buying a code-signing certificate, (b) pasting two
secrets, and — depending on the cert type — (c) a one-time submission
to Microsoft to seed SmartScreen reputation.

---

## The one blocker today: no cert has been bought

`gh secret list` today shows only `MACOS_*` secrets. Windows is
unsigned, which is why the current release (`v0.12.692`, shipped
2026-08-12) triggers SmartScreen and — worse — Smart App Control in
enforce mode blocks the NSIS uninstaller too.

---

## The four paths, ranked

| Path | Cost | SmartScreen | Setup effort | Best when |
|---|---|---|---|---|
| **1. SignPath Foundation** *(free for OSS — try this first)* | **$0** | **Instant** — SignPath signs with a publicly-trusted OV via their own HSM; reputation attaches to their publisher identity, so new projects inherit trust immediately. | Medium — GitHub-integration onboarding, needs an application + review (typically days to a few weeks). Needs a follow-up PR to wire their signing action into the workflow. | ClawMetry is OSS on GitHub — likely qualifies. Try this before paying. |
| **2. EV code-signing cert** *(recommended paid — matches wired CI)* | **$149–349/yr** (SSL.com: 5-yr $149/yr, 3-yr $249/yr, 1-yr $349) | **Instant** — EV = "reputation from first signature" | Low (~1 day: buy, verify, paste 2 secrets) | You want to ship today. Zero CI changes. |
| **3. Azure Artifact Signing** (formerly "Trusted Signing") | **~$120/yr** ($9.99/mo + $0.005/sig) | **Instant** — Microsoft-issued cert chain | Medium (~1 week: portal setup + identity verify + CI PR to add signtool `/dlib` mode) | Ongoing cost matters more than time-to-ship |
| **4. OV code-signing cert** | ~$70–200/yr | **Warns until reputation builds** (weeks of downloads or MSRC submission) | Low (same as #2) | Not recommended — false economy |

**Playbook:** apply for SignPath Foundation the same day you buy the EV
cert. SignPath is free but takes days/weeks to approve; the EV cert
ships in ~1–3 days and unblocks the current release cycle immediately.
When SignPath approves, migrate to it and let the EV cert lapse at
renewal.

---

## Path 1 — SignPath Foundation (free for OSS — try first)

SignPath Foundation is a nonprofit that provides free code signing for
qualifying OSS projects through the enterprise SignPath.io platform.
They sign through a managed pipeline using their own publicly-trusted
OV cert — reputation is theirs, so new projects inherit trust from day
one (no per-file SmartScreen wait).

**Eligibility checklist** — ClawMetry meets these today:
- OSI-approved OSS license, no commercial dual-licensing → MIT ✅
- Actively maintained → ✅ (daily releases)
- No malware / no PUP → ✅
- Publicly released in the exact form being signed → ✅ (the desktop `.exe` is a GitHub Release asset)

### The application

1. Start at https://signpath.io/solutions/open-source-community — the OSS landing page. Click "Contact us" or "Request a Demo" (Foundation program funnels through the standard contact form; explain "SignPath Foundation for OSS project" in the message).
2. Also read the Foundation terms at https://signpath.org/terms.html — you'll be asked to accept them during onboarding.
3. Provide: GitHub repo URL (github.com/vivekchand/clawmetry), OSI license (MIT), project maintainers, release channel (GitHub Releases), signing target (the Windows `.exe` and `.exe` installer inside the release artifact).
4. Review turnaround is a few days to a few weeks. In the meantime, activate **Path 2 (EV cert)** to unblock releases today.
5. Once approved, SignPath supplies a GitHub Action that signs artifacts as a webhook: CI uploads unsigned artifacts, waits for the countersigned artifact to come back. That's a follow-up PR that swaps the current `signtool sign /f <pfx>` steps for their action.

---

## Path 2 — Buy an EV cert (fastest paid path — matches wired CI)

### Where to buy

Any of these vendors sells an EV code-signing cert with **cloud-signing
(HSM-backed .pfx)** — mandatory, because since June 2023 CA/B Forum
rules ban downloadable EV private keys. You want the "cloud" or
"eSigner" variant, not the shipped-Yubikey variant, so CI can sign
without a physical token plugged into a runner.

- **SSL.com** — https://www.ssl.com/products/software-integrity/code-signing/ev/ — **1yr $349, 3yr $249/yr, 5yr $149/yr**. eSigner cloud signing (HSM-backed PFX). Fastest identity verification (~24h for an established LLC). *Cheapest per-year at 5yr; least commitment at 1yr.*
- **DigiCert KeyLocker** — https://www.digicert.com/signing/code-signing-certificates — ~$474/yr, industry standard.
- **Sectigo (formerly Comodo)** — https://sectigo.com/ssl-certificates-tls/code-signing — ~$399/yr.

### The 20-minute activation

1. **Buy** an EV code-signing cert (cloud/eSigner variant) from any vendor above. Use `InstaLabs LLC` as the organization. They'll need business docs (state registration, D-U-N-S optional but speeds review, phone call). Established LLCs clear in 1–3 business days.

2. **Export the cert as a password-protected PFX.** Vendor's cloud console has a "Download PFX for CI" or "Export for automation" flow. Save the file and the password.

3. **Base64-encode the PFX** (secrets take bytes, not files):
   ```bash
   base64 -i clawmetry.pfx -o clawmetry.pfx.b64
   # or on Linux: base64 -w0 clawmetry.pfx > clawmetry.pfx.b64
   ```

4. **Paste 2 secrets** into GitHub → **Settings → Secrets and variables → Actions → New repository secret**:

   | Secret name | Value |
   |---|---|
   | `WINDOWS_CERT_PFX_BASE64` | contents of `clawmetry.pfx.b64` |
   | `WINDOWS_CERT_PASSWORD` | the PFX password |

5. **Delete the local PFX file.** It's already in `.gitignore` (`*.pfx`) but shred it anyway: `rm clawmetry.pfx clawmetry.pfx.b64`.

6. **Trigger a build.** Either push a `v*.*.*` tag or run **Actions → Build desktop artifacts → Run workflow** manually. Confirm the "Sign ClawMetry.exe" and "Verify signatures + scrub cert" steps ran (not skipped) and the workflow ended green.

7. **Download and test.** From the GitHub Release, grab `ClawMetry-windows-setup.exe`, run it on a Windows machine. SmartScreen should NOT warn. Right-click → Properties → Digital Signatures should show "InstaLabs LLC" with a valid green check.

### If SmartScreen still warns after signing

EV certs are supposed to give instant reputation, but Microsoft occasionally still shows the warning on the very first signed release from a new publisher. To skip the wait:

1. Ship a signed release (any version).
2. Submit at https://www.microsoft.com/en-us/wdsi/filesubmission → **"Software developer"** as reason. Upload `ClawMetry-windows-setup.exe`. Turnaround is 1–3 business days.
3. From then on, reputation follows the publisher identity — every new signed release inherits the trust.

---

## Path 3 — Azure Artifact Signing (cheaper ongoing, needs a PR)

Best-in-class economics: ~$120/yr and instant SmartScreen reputation via the Microsoft cert chain. **Downside:** the current CI pipeline uses `signtool sign /f <pfx>` — Azure Artifact Signing needs `signtool sign /dlib <Trusted.Signing.dll> /dmdf <metadata.json>` instead. That's a follow-up PR to rework the sign wrapper, not something the current secrets flow supports as-is.

If you want to go this route:

1. Buy: **portal.azure.com** → *Create a resource* → **Artifact Signing**. Resource group `clawmetry-signing`, account `clawmetry-signing-acct` (Basic SKU $9.99/mo), identity validation for InstaLabs LLC, cert profile `clawmetry-public-trust`.
2. Mint a service principal:
   ```bash
   az ad sp create-for-rbac \
     --name clawmetry-ci-signer \
     --scopes /subscriptions/<SUB>/resourceGroups/clawmetry-signing/providers/Microsoft.CodeSigning/codeSigningAccounts/clawmetry-signing-acct \
     --role "Artifact Signing Certificate Profile Signer"
   ```
3. Open a follow-up PR that:
   - Downloads the `Microsoft.Trusted.Signing.Client` NuGet in the workflow.
   - Rewrites the `sign.cmd` wrapper to use `signtool sign /dlib "Trusted.Signing.dll" /dmdf metadata.json` instead of `/f <pfx> /p <pw>`.
   - Adds `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `ARTIFACT_SIGNING_ENDPOINT`, `ARTIFACT_SIGNING_ACCOUNT_NAME`, `ARTIFACT_SIGNING_CERT_PROFILE_NAME` as recognized secrets (in addition to `WINDOWS_CERT_*` for backwards compat during migration).

**Eligibility caveat:** Azure verifies subscriber identity. Businesses under 3 years old go through a manual review path — same outcome, adds 1–2 weeks. Test-run identity verification while you're still using an EV cert (path 1) so the switch-over is instant.

---

## Path 4 — OV cert (not recommended)

An Organization Validation (OV) cert is cheaper (~$70–200/yr) and drops into the same signtool flow as an EV cert. But **OV certs don't grant instant SmartScreen reputation** — Microsoft treats them as a lower-trust tier. The workflow warning fades only after ClawMetry accumulates thousands of downloads per unique file hash, which for a rapidly-versioning app means it never fades in practice.

Only pick this if the $200/yr difference is genuinely a dealbreaker. Otherwise it's false economy — enterprises won't install a warning app regardless of how "signed" it technically is.

---

## What VERSIONINFO already gets you (unsigned)

Even before you buy a cert, this branch adds VERSIONINFO to the `.exe` (via `desktop/build_windows.spec`). That means:

- Explorer → right-click ClawMetry.exe → Properties → Details tab: shows CompanyName = `InstaLabs LLC`, ProductName = `ClawMetry`, FileVersion = current release.
- Task Manager → Details tab: shows "ClawMetry" and "InstaLabs LLC" instead of a blank publisher column.
- SmartScreen's "More info" click-through: shows the real publisher string instead of "Unknown publisher".

It doesn't clear the warning — only a valid Authenticode signature does — but it means when a user does click through, they see a real identity, not "unknown".

---

## Verifying it worked (on a Windows machine)

```powershell
# The installer's Authenticode signature should be Valid and the
# signer should list InstaLabs LLC (or the exact EV cert subject).
Get-AuthenticodeSignature .\ClawMetry-windows-setup.exe |
  Format-List Status, StatusMessage, SignerCertificate

# Right-click → Properties → Digital Signatures — should show a
# valid green check with "InstaLabs LLC" and a timestamp countersignature.
```

If SmartScreen still warns:
- Give it 24–48h for reputation propagation, or submit to MSRC (link above).
- Confirm BOTH the outer `ClawMetry-windows-setup.exe` **and** the inner tray `ClawMetry.exe` (inside the zip / install tree) are signed — CI signs both; verify by extracting the zip and running `Get-AuthenticodeSignature` on `ClawMetry.exe`.

---

## Related files (already in-tree)

- `.github/workflows/desktop-artifacts.yml` — full sign + verify pipeline. NO-OPs safely when `WINDOWS_CERT_*` secrets aren't set.
- `desktop/installer/windows.nsi` — NSIS installer script; per-user install to `%LOCALAPPDATA%\Programs\ClawMetry`, no UAC prompt.
- `desktop/build_windows.spec` — PyInstaller spec; renders VERSIONINFO from `dashboard.py __version__` on every build.
