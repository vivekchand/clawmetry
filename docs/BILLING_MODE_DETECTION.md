# Billing-Mode Detection — Cross-Runtime Spec

> **Status:** design spec for the ClawMetry sync daemon (`clawmetry/sync.py`).
> **Goal:** for each detected coding-agent runtime on a machine, classify whether
> it is billed via a **flat-fee subscription** (Claude Pro/Max, ChatGPT/Codex,
> Cursor Pro, Gemini Code Assist, Qwen OAuth…) or **metered pay-per-token**
> (BYO API key, Vertex/Bedrock cloud billing) — **without ever reading a secret
> value or triggering an OS keychain/keyring password prompt.**

Why we care: ClawMetry already derives an **API-equivalent cost** for every
session (tokens × model pricing). For an OAuth-subscriber that number is the
*notional* cost, not money they actually pay — surfacing it as "spend" is
misleading. `billing_mode` lets the UI (and the hardware device) say *"$29.58
API-equivalent — covered by your Max plan"* instead of falsely implying a bill.

---

## 1. Unified detection contract

```python
def detect_billing_mode(
    runtime: str,            # 'claude_code' | 'codex' | 'cursor' | 'gemini' |
                             # 'qwen_code' | 'aider' | 'goose' | 'opencode' | ...
    os_name: str,            # 'macos' | 'windows' | 'linux'
    home: str,               # resolved user home dir for the account that owns the runtime
    env: Mapping[str, str] | None = None,   # daemon-visible env; default os.environ
    project_dir: str | None = None,         # cwd of the runtime's sessions, for .env/.aider.conf.yml
) -> "BillingResult":
    ...

@dataclass(frozen=True)
class BillingResult:
    mode: Literal['subscription', 'metered', 'local', 'unknown']
    tier: str | None        # 'max' | 'pro' | 'team' | 'enterprise' | 'plus' | 'pro_plus' |
                            # 'coding_plan' | 'copilot' | 'vertex' | 'bedrock' | None
    signal: str             # short machine-readable reason, e.g. 'oauthAccount.billingType=stripe_subscription'
    confidence: Literal['high', 'medium', 'low']
    source: str             # which artifact decided it: file path, env var name, or keychain svce
```

### Mode semantics

| mode | meaning | cost-display rule |
|------|---------|-------------------|
| `subscription` | Flat-fee OAuth/console subscription is the **active** billing path and no metered override outranks it. | Show API-equivalent **labeled "covered by your <tier> plan"**. |
| `metered` | A pay-per-token API key / cloud-billed routing (Bedrock/Vertex/Azure/Vertex-ADC) is the active path. | Show API-equivalent **as actual spend**. |
| `local` | Self-hosted / local model (Ollama, localhost base URL) — no external meter. | Show **$0 external** (compute is the user's). |
| `unknown` | Could not determine without reading a secret or prompting. | Show API-equivalent with a **soft caveat** (see §4). Never claim "covered." |

### Global precedence (applies to every runtime)

Checked **top-down; first match wins**. This ordering is deliberate — it mirrors
each tool's *own* auth-resolution chain so we report the path the runtime will
actually bill against, not merely what's installed.

1. **Cloud-provider routing env** (Bedrock/Vertex/Foundry/Azure) → `metered` (tier=`vertex`/`bedrock`/`azure`). Outranks everything.
2. **Explicit API-key / auth-token env var** present & non-empty → `metered`.
3. **Config-file API-key directive** (`apiKeyHelper`, `OPENAI_API_KEY` in settings, `type:'api'`, BYO-key rows, `*-api-key:` yaml) → `metered`.
4. **Account-metadata subscription marker** (`oauthAccount.billingType=*_subscription`, `cursorAuth/stripeMembershipType=pro`, `type:'oauth'`, `selectedType=oauth-personal`…) → `subscription`.
5. **OAuth-token-blob existence** (file or keychain item) with no override above → `subscription` (lower confidence).
6. **Local model marker** (`ollama/…`, localhost base URL) → `local`.
7. Otherwise → `unknown`.

> **The #1 false positive is precedence inversion:** a user can hold Claude Max
> *and* export `ANTHROPIC_API_KEY`; Claude Code then bills the **key**. So env /
> apiKeyHelper / approved-key checks (steps 1–3) **must run before** the
> subscription-tier check (step 4). Every runtime below honors this.

---

## 2. Per-runtime ordered checks + path table

### 2.0 Path table (config dirs)

| Runtime | macOS | Windows | Linux |
|---------|-------|---------|-------|
| **claude_code** | `~/.claude.json`, `~/.claude/` (+Keychain svce `Claude Code-credentials`) | `%USERPROFILE%\.claude.json`, `%USERPROFILE%\.claude\.credentials.json` | `~/.claude.json`, `~/.claude/.credentials.json` |
| **codex** | `~/.codex/auth.json`, `config.toml` (+Keychain svce `Codex Auth`) | `%USERPROFILE%\.codex\auth.json` (+Cred Mgr `Codex Auth`) | `~/.codex/auth.json` (+libsecret svc `Codex Auth`) |
| **cursor** | `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb` (+Keychain `Cursor Safe Storage`) | `%APPDATA%\Cursor\User\globalStorage\state.vscdb` | `~/.config/Cursor/User/globalStorage/state.vscdb` |
| **gemini** | `~/.gemini/{oauth_creds.json,google_accounts.json,settings.json,.env}` | `%USERPROFILE%\.gemini\…` | `~/.gemini/…` |
| **qwen_code** | `~/.qwen/{oauth_creds.json,settings.json,.env}` | `%USERPROFILE%\.qwen\…` | `~/.qwen/…` |
| **aider** | `~/.aider.conf.yml`, `~/.env`, `<proj>/.env`, `<proj>/.aider.conf.yml` | `%USERPROFILE%\.aider.conf.yml`, … | `~/.aider.conf.yml`, … |
| **goose** | `~/.config/goose/{config.yaml,secrets.yaml}` (+Keychain svce `goose`/acct `secrets`) | `%APPDATA%\Block\goose\config\{config.yaml,secrets.yaml}` (+Cred Mgr `goose`) | `~/.config/goose/{config.yaml,secrets.yaml}` (+libsecret svc `goose`) |
| **opencode** | `~/.local/share/opencode/auth.json` (XDG) | `%USERPROFILE%\.local\share\opencode\auth.json` | `$XDG_DATA_HOME/opencode/auth.json` → `~/.local/share/opencode/auth.json` |

> **Always resolve override env vars first:** `CLAUDE_CONFIG_DIR`, `CODEX_HOME`,
> `GEMINI_DIR`-style, `XDG_DATA_HOME`. They relocate the files above.

---

### 2.1 claude_code  — confidence: **high**

```
STEP 0  CFG = $CLAUDE_CONFIG_DIR or $HOME (macOS/Linux) / %USERPROFILE% (Win)
STEP 1  env CLAUDE_CODE_USE_BEDROCK|VERTEX|FOUNDRY set → metered (tier=cloud), STOP
STEP 2  env ANTHROPIC_AUTH_TOKEN set → metered; elif ANTHROPIC_API_KEY set → metered
        (corroborate with Step 4a), STOP
STEP 3  parse each existing settings.json (managed > settings.local.json > project
        .claude/settings.json > CFG/.claude/settings.json) for KEY 'apiKeyHelper'
        or 'env.ANTHROPIC_API_KEY'/'env.ANTHROPIC_AUTH_TOKEN' → metered, STOP
        (read keys only; NEVER execute apiKeyHelper)
STEP 4  open CFG/.claude.json (non-secret read):
        a) customApiKeyResponses.approved is non-empty array → metered (console key approved)
        b) elif oauthAccount object exists:
             billingType matches /_subscription$/  (stripe_subscription | apple_subscription)
               OR organizationType/organizationRateLimitTier contains
                  claude_max|claude_pro|team|enterprise
             → subscription, tier from organizationType (max/pro/team/enterprise)
           else (api-usage/console platform org) → metered
STEP 5  (secondary, existence-only, NO secret read)
        macOS:  security find-generic-password -s "Claude Code-credentials"   # NO -w / NO -g
                exit 0 ⇒ OAuth login item exists
        Lin/Win: stat CFG/.claude/.credentials.json                            # existence only
STEP 6  resolve: Step4=subscription & no override ⇒ subscription;
        token blob exists but Step2-4 found override ⇒ metered (override wins);
        nothing ⇒ unknown
```

Managed/enterprise settings to also parse:
macOS `/Library/Application Support/ClaudeCode/managed-settings.json` (+`.d/`);
Win `C:\Program Files\ClaudeCode\managed-settings.json` (+`.d\`) and GPO registry
`HKLM\SOFTWARE\Policies\ClaudeCode`; Linux `/etc/claude-code/managed-settings.json`.

Do **not** trust `subscriptionType`/`rateLimitTier` inside the token blob — often
`null` (issue #34262). Prefer `oauthAccount.*` in `.claude.json`.

---

### 2.2 codex  — confidence: **high**

```
STEP 0  CODEX_HOME = $CODEX_HOME or ~/.codex (%USERPROFILE%\.codex on Win)
STEP 1  env OPENAI_API_KEY or CODEX_API_KEY non-empty → metered (env wins over file), STOP
STEP 2  stat CODEX_HOME/auth.json; if a plain readable file (no prompt):
        parse TOP-LEVEL KEYS ONLY:
          'OPENAI_API_KEY' non-empty           → metered, STOP
          'personal_access_token' OR auth_mode=='apikey' → metered, STOP
          'tokens' object present               → subscription
              (optional tier: base64url-decode tokens.id_token middle segment,
               read claim chatgpt_plan_type = plus|pro|business|enterprise|team)
STEP 3  auth.json ABSENT but CODEX_HOME exists ⇒ keyring-store mode.
        Read config.toml key cli_auth_credentials_store (non-secret).
        EXISTENCE-ONLY keychain probe (never read value):
          macOS:  security find-generic-password -s "Codex Auth"   # NO -g / NO -w
          Linux:  secret-tool search service "Codex Auth"          # attributes only
          Win:    cmdkey /list | match "Codex Auth"
        If item present: env OPENAI_API_KEY unset ⇒ subscription; set ⇒ metered
STEP 4  nothing ⇒ unknown
```

Resolution mirrors `manager.rs::resolved_mode`: `auth_mode` > `personal_access_token`
> `OPENAI_API_KEY` > `tokens`(Chatgpt). Keyring item value = same serialized
`AuthDotJson` JSON — but **don't read it**; presence + env is enough.

---

### 2.3 cursor  — confidence: **medium**

```
STEP 0  resolve state.vscdb per OS (see path table)
STEP 1  open SQLite READ-ONLY + IMMUTABLE:  file:<path>?mode=ro&immutable=1
        (no keychain prompt; avoids locking Cursor's writer)
STEP 2  SELECT key,value FROM ItemTable WHERE key IN (
          'cursorAuth/stripeMembershipType','cursorAuth/accessToken',
          'cursorAuth/openAIKey','cursorAuth/claudeKey','cursorAuth/googleKey')
        also detect existence of any 'secret://…' row tied to API-key storage
STEP 3  classify (membership & BYO are INDEPENDENT flags):
          any of openAIKey|claudeKey|googleKey non-empty       → metered (legacy build)
          elif a secret:// API-key row EXISTS                  → metered (new build; existence only)
          elif stripeMembershipType ∈ {pro,pro_plus,business,team,enterprise,free_trial}
                                                                → subscription (tier=value)
          elif stripeMembershipType=='free'/absent + valid accessToken → free plan
STEP 4  (optional, existence-only) Safe-Storage key probe:
          macOS security find-generic-password -s "Cursor Safe Storage" (exit 0=present)
          — proves SecretStorage initialized, NOT that a BYO key exists; rely on the
            secret:// ItemTable row instead.
```

**Never decrypt** the `secret://` blob — that needs the keychain and prompts.
Local `stripeMembershipType` can be stale (cursor-stats refetches from
`cursor.com/api`); a free membership + BYO key is a real combo, hence the two
independent flags.

---

### 2.4 gemini  — confidence: **high**

```
STEP 0  geminiDir = home + '/.gemini'  (dir name '.gemini' on ALL OSes; no XDG)
STEP 1  env metered check (no file reads): any of
          GEMINI_API_KEY | GOOGLE_API_KEY | GOOGLE_APPLICATION_CREDENTIALS |
          GOOGLE_GENAI_USE_VERTEXAI=true  → metered (tier=vertex if vertex), STOP
STEP 2  read geminiDir/settings.json security.auth.selectedType (or legacy top-level
        selectedAuthType):
          'oauth-personal'|'oauth'|'cloud-shell'  → subscription
          'gemini-api-key'|'api-key'              → metered
          'vertex-ai'                             → metered (cloud-billed)
STEP 3  settings absent/ambiguous → existence:
          stat geminiDir/oauth_creds.json OR geminiDir/google_accounts.json → subscription
STEP 4  scan geminiDir/.env and ~/.env for line-prefix 'GEMINI_API_KEY='/'GOOGLE_API_KEY='
        (KEY NAME only) → metered
        Precedence: selectedType > env key/Vertex > oauth_creds.json existence
```

`oauth_creds.json` is **plaintext** (not Keychain) — existence never prompts. The
Keychain/keytar path is only for MCP tokens, ignore it. Both OAuth creds and a key
can coexist → `settings.json` `selectedType` is the tie-breaker.

---

### 2.5 qwen_code  — confidence: **high** (Gemini-CLI fork; layout under `.qwen`)

```
STEP 0  qwenDir = home + '/.qwen'
STEP 1  read qwenDir/settings.json security.auth.selectedType:
          'qwen-oauth'                         → subscription (OAuth)
          'openai'|'anthropic'|'gemini'|'vertex-ai' → metered, THEN refine:
             if any configured baseUrl / OPENAI_BASE_URL contains
                'coding.dashscope.aliyuncs.com' → subscription (tier=coding_plan)
             else → metered (per-token)
STEP 2  ambiguous → stat qwenDir/oauth_creds.json → OAuth path
        (FLAG: free OAuth tier discontinued 2026-04-15; a present file may be a
         stale/expired free login — prefer selectedType)
STEP 3  metered env scan (key NAMES only) in env + qwenDir/.env + ~/.env + ./.env:
          DASHSCOPE_API_KEY | OPENAI_API_KEY | ANTHROPIC_API_KEY | GEMINI_API_KEY → metered
        Also read settings.json modelProviders[].envKey (a non-secret NAME) and
        check THAT var's presence — don't assume only standard names.
```

> **Coding-Plan trap:** the Alibaba Coding Plan is a flat-fee subscription
> delivered *as an API key* against `coding.dashscope.aliyuncs.com/v1`. A naive
> "`DASHSCOPE_API_KEY` ⇒ metered" rule mislabels it. Use the base-URL
> discriminator (Step 1).

---

### 2.6 aider  — confidence: **high** (no subscription concept; metered-BYO or local)

```
DEFAULT: metered-BYO
STEP 0  consider project_dir (aider's .env/.aider.conf.yml are git/project-relative)
STEP 1  scan env for /^[A-Z0-9_]*_API_KEY$/  (OPENAI_/ANTHROPIC_/GEMINI_/DEEPSEEK_/
        OPENROUTER_/GROQ_/…) → metered
STEP 2  read NON-SECRET KEYS of ~/.aider.conf.yml and <proj>/.aider.conf.yml:
          'openai-api-key' / 'anthropic-api-key' / 'api-key:' map present → metered
STEP 3  grep .env files aider loads (<proj>/.env, ~/.env, ~/.aider/.env) for
        line-prefix '*_API_KEY=' (key NAME only) → metered
STEP 4  LOCAL override: model name 'ollama/…' OR OPENAI_API_BASE/OLLAMA_API_BASE
        pointing at localhost/private host → local (un-metered)
STEP 5  no key + no local marker → unknown (may be local, may be unconfigured)
```

No keychain anywhere → never prompts. Absence of `*_API_KEY` ≠ unconfigured (could
be local) — check model/base-URL before concluding.

---

### 2.7 goose  — confidence: **high**

```
STEP 0  read config.yaml (macOS/Linux ~/.config/goose/config.yaml;
        Win %APPDATA%\Block\goose\config\config.yaml) — NON-SECRET. Read GOOSE_PROVIDER.
STEP 1  provider → mode:
          {github_copilot, databricks, gcp_vertex_ai, azure_openai}
              → subscription/enterprise-OAuth, corroborate:
                 stat ~/.config/goose/githubcopilot/info.json (copilot, tier=copilot)
                 stat ~/.config/gcloud/application_default_credentials.json (vertex-ADC, tier=vertex)
          else (openai/anthropic/google/openrouter/groq/…)  → metered
STEP 2  for metered, confirm key WITHOUT reading secrets, in goose's own order:
          (a) env <PROVIDER>_API_KEY present?
          (b) GOOSE_DISABLE_KEYRING set (env OR config.yaml since v1.30.0)?
                → stat ~/.config/goose/secrets.yaml; read top-level KEY NAMES only
          (c) else key is in OS keyring svce 'goose'/acct 'secrets' —
                EXISTENCE check only:
                  macOS security find-generic-password -s goose -a secrets   # NO -w / NO -g
                  Linux  best-effort; prefer config+env over a libsecret lookup that may unlock-prompt
                  Win    cmdkey /list | match 'goose'
STEP 3  Precedence: env > keyring > secrets.yaml
```

Goose has **no single-user subscription tier** like Claude Pro — do not infer one.
Vertex/Azure/ADC are "metered via cloud billing" but use no per-provider key →
classify as enterprise/non-keyed (tier=vertex/azure), not pay-per-token.

---

### 2.8 opencode  — confidence: **high** (explicit `type` discriminant — cleanest)

```
STEP 0  dataDir = $XDG_DATA_HOME/opencode if set else home/.local/share/opencode
        authFile = dataDir/auth.json
STEP 1  if authFile exists, parse JSON (providerId → {type, …}); per entry read
        ONLY the 'type' field (and non-secret accountId/enterpriseUrl/expires):
          type=='oauth'              → subscription for that provider
          type=='api' | 'wellknown'  → metered for that provider
        Aggregate: any oauth entry ⇒ at least one subscription login (report per-provider)
STEP 2  scan env for <PROVIDER>_API_KEY → metered provider via env (no auth.json needed)
STEP 3  precedence: explicit env key overrides auth.json at runtime — a present env
        key means the ACTIVE provider may be metered even if an oauth entry exists
        for a different provider
```

Plaintext `auth.json`, no keychain → never prompts. Read only `type`/`accountId`/
`expires`; **never** `key`/`access`/`refresh`. An `oauth` entry can be expired
(check `expires`) but still indicates the chosen path.

---

## 3. Anti-hacks — "NEVER do this"

1. **Never read a secret value.** No `-w`/`-g` on `security find-generic-password`;
   no `secret-tool lookup` that returns the secret; no decrypting Electron
   `safeStorage` / `secret://` blobs; no reading `key`/`access`/`refresh`/
   `accessToken`/`OPENAI_API_KEY` *values*. Existence + non-secret keys only.
2. **Never trigger a keychain/keyring prompt.** macOS existence form is
   `security find-generic-password -s "<svce>"` with **no `-g`/`-w`**. On
   headless/SSH macOS even a benign lookup can return `errSecInteractionNotAllowed`
   (exit 36) → fall back to plaintext metadata files, don't retry interactively.
   On Linux a `secret-tool lookup` may unlock-prompt on some desktops → prefer
   config.yaml/env over keyring probes; treat "keyring item present" as best-effort.
3. **Never execute a helper.** `apiKeyHelper` and friends are read as a *string
   key*, never run.
4. **Never assume macOS.** Resolve OS first; the path table and credential store
   differ on all three. Claude Code/Codex/Goose use the keychain on macOS but
   **plaintext files** on Linux/Windows — don't go looking in libsecret/Credential
   Manager for tokens that live in a `.json`.
5. **Never assume `$HOME`/default dir.** Resolve `CLAUDE_CONFIG_DIR`, `CODEX_HOME`,
   `XDG_DATA_HOME`, `.gemini`/`.qwen` overrides first.
6. **Never lock the app's DB.** Open `state.vscdb` as
   `file:…?mode=ro&immutable=1`; retry on busy, never write.
7. **Never log/transmit the bytes you read.** Even plaintext files (aider/.env,
   opencode auth.json, gemini oauth_creds.json) must be inspected for key
   *presence* only; the daemon must not persist values into DuckDB or the snapshot.
8. **Never let "installed" mean "active."** A present OAuth blob with an
   overriding env key is **metered**, not subscription (precedence inversion).
9. **Never trust the daemon's env == the user's shell env.** A key in `~/.zshrc`
   won't be in the daemon's process env → always also scan the runtime's `.env`
   files for the key *name*.

---

## 4. Confidence + fallback to `unknown`

| Runtime | base confidence | downgrade to `unknown`/`low` when… |
|---------|-----------------|------------------------------------|
| claude_code | high | only token-blob exists, no `oauthAccount` (issue #57026 SSO hydration); env unreadable |
| codex | high | keyring-store mode + can't existence-probe; env ambiguous |
| cursor | **medium** | version-renamed keys; stale `stripeMembershipType`; can't read DB |
| gemini | high | both creds+key present and no `selectedType` to break tie |
| qwen_code | high | `oauth_creds.json` present but possibly expired (post-2026-04-15) |
| aider | high | no key + no local marker → could be local or unconfigured |
| goose | high | metered provider but key only in keyring and probe inconclusive (still report `metered` w/ medium) |
| opencode | high | provider configured only via env for a *different* active provider |

**Rule:** if any step would require reading a secret or prompting to decide,
**return `unknown`** rather than guessing. Mark `confidence='low'` when a result
rests solely on token-blob existence with no metadata corroboration.

### UI / device treatment of `unknown`

- **Never render a green "covered by your plan" badge on `unknown`.** That's a
  false-positive we must not ship.
- Show the **API-equivalent cost** (we always have it) with a neutral, soft
  caveat: *"≈ $X API-equivalent — billing mode not detected."* Optionally a
  one-line CTA: *"Sign in / set a key so ClawMetry can label this correctly."*
- `subscription` → *"≈ $X API-equivalent · covered by your `<tier>` plan."*
- `metered` → render as **actual spend** *"$X"* (the existing behavior).
- `local` → *"$0 external · local model."*

Default for a brand-new/undetected runtime is `unknown`, **not** `metered` —
metered overstates cost for the large OAuth-subscriber base.

---

## 5. Implementation plan — `clawmetry/sync.py` + threading to the device

### 5.1 Where it lives

- New module `clawmetry/billing_mode.py` (keeps `sync.py` lean; mirrors the
  `error_signal.py` / `waste_flags.py` helper-module pattern). Exposes
  `detect_billing_mode(runtime, os_name, home, env=None, project_dir=None)
  -> BillingResult` plus a `detect_all(detected_runtimes) -> dict[runtime, BillingResult]`.
- Pure stdlib: `os`, `pathlib`, `json`, `sqlite3` (cursor), `tomllib`/`toml`
  (codex config), `subprocess` for the **non-prompting** keychain existence probe
  (wrapped with a hard 2s timeout + `errSecInteractionNotAllowed` swallow). No
  new third-party deps. **Never crash on bad input** (per CLAUDE.md) — every
  branch falls through to `unknown`.

### 5.2 When it runs

- The sync daemon already enumerates installed runtimes (the
  `CLAWMETRY_FAMILY_SESSION_LIMIT` ingest of claude_code/codex/cursor/…). After
  that enumeration, call `detect_all()` once per sync cycle (cheap: a handful of
  `stat`s + at most one non-prompting keychain probe per runtime). Cache the
  result for ~5 min to avoid re-probing each tick.
- Run under the same user context the runtime belongs to so `home`/env resolve
  correctly (multi-node fleet: each node reports its own).

### 5.3 Storage (DuckDB)

- Store **only** the classification, never any secret bytes. Add a small table
  via `local_store.py`:

  ```sql
  CREATE TABLE IF NOT EXISTS runtime_billing (
    runtime    TEXT PRIMARY KEY,
    mode       TEXT,        -- subscription|metered|local|unknown
    tier       TEXT,
    signal     TEXT,        -- non-secret reason string
    confidence TEXT,
    source     TEXT,        -- file path / env var name / keychain svce
    detected_at TIMESTAMP
  );
  ```

- The daemon owns the writer lock (per CLAUDE.md); the dashboard reads it through
  `routes/local_query.py` (`/api/local/*`), **not** by re-running detection in a
  request handler (would be empty in cloud).

### 5.4 Threading to the UI, snapshot, and device

1. **Sessions/Usage read path:** join `runtime_billing` by the session's runtime
   (= `session_id` prefix, per the runtime-switcher convention) so each session's
   API-equivalent cost carries a `billing_mode`/`tier`. Surface on `/api/sessions`,
   `/api/usage`, `/api/overview` (and the per-harness custom-tab `extra`).
2. **Cloud snapshot:** add a compact `runtimeBilling` slice to the
   E2E-encrypted snapshot (`sync.py` snapshot builder) — `{runtime: {mode, tier,
   confidence}}` only, no secrets. Cloud renders the same caveat logic client-side
   after decrypt.
3. **Hardware device:** the ESP32 already decrypts a `deviceSummary` slice
   (0.12.439). Add a single byte/enum per active runtime (`mode`+`tier`) to that
   slice so the device can show *"$X · covered"* vs *"$X spent"* vs *"$X · mode
   unknown"* without ever seeing a token. Keep it to the enum — the device must
   never receive credential material.
4. **Fleet:** roll up per-node billing_mode so the fleet view can show, e.g.,
   "3 nodes subscription, 1 metered, 1 unknown."

### 5.5 Tests (real-pipeline, per the no-synthetic-seeds standing order)

- Per-runtime fixtures of **non-secret** metadata (a fake `~/.claude.json` with
  `oauthAccount.billingType=stripe_subscription`; a `codex/auth.json` with
  `tokens` vs `OPENAI_API_KEY`; a cursor `state.vscdb` with `stripeMembershipType`
  rows; an opencode `auth.json` with `type:'oauth'` vs `'api'`).
- **Precedence-inversion test:** Max `oauthAccount` + `ANTHROPIC_API_KEY` env ⇒
  asserts `metered`.
- **No-secret guarantee test:** assert the code never invokes `security … -w/-g`,
  never opens keyring secret values, and `runtime_billing.signal`/`source` contain
  no token-shaped strings.
- **Coding-Plan test:** `DASHSCOPE_API_KEY` + `coding.dashscope` base URL ⇒
  `subscription/coding_plan`, not `metered`.
- Cross-OS path resolution unit tests (macOS/Win/Linux) honoring the override
  env vars.

---

## 6. Quick reference — decisive signal per runtime

| Runtime | subscription signal (non-secret) | metered signal (checked first) | local |
|---------|----------------------------------|--------------------------------|-------|
| claude_code | `~/.claude.json` `oauthAccount.billingType` ∈ `*_subscription` / `organizationType` ∈ max/pro/team/enterprise | `ANTHROPIC_API_KEY`/`_AUTH_TOKEN` env, `apiKeyHelper`, `customApiKeyResponses.approved`, `CLAUDE_CODE_USE_*` | — |
| codex | `auth.json` `tokens` present & no `OPENAI_API_KEY` (id_token claim `chatgpt_plan_type`) | env/file `OPENAI_API_KEY`, `personal_access_token`, `auth_mode=apikey` | — |
| cursor | `cursorAuth/stripeMembershipType` ∈ pro/pro_plus/business/team/enterprise/free_trial | `cursorAuth/openAIKey|claudeKey|googleKey` or `secret://` API row | — |
| gemini | `settings.selectedType=oauth-personal` / `oauth_creds.json` exists | `GEMINI_API_KEY`/`GOOGLE_API_KEY`/Vertex env, `selectedType=gemini-api-key|vertex-ai` | — |
| qwen_code | `selectedType=qwen-oauth`; or `coding.dashscope` base URL (coding_plan) | `DASHSCOPE_/OPENAI_/ANTHROPIC_/GEMINI_API_KEY` (non-coding base) | — |
| aider | none | any `*_API_KEY`, `*-api-key:` in yaml/.env | `ollama/…` or localhost base URL |
| goose | `GOOSE_PROVIDER` ∈ github_copilot/databricks/gcp_vertex_ai/azure_openai | other provider + key in env/keyring `goose`/`secrets.yaml` | — |
| opencode | `auth.json` entry `type=='oauth'` | `auth.json` `type=='api'|'wellknown'` or env `*_API_KEY` | — |
