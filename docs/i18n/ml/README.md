<!-- i18n-src:191e9094d7fa -->
> മലയാളം translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**നിങ്ങളുടെ ഏജന്റ് ചിന്തിക്കുന്നത് കാണൂ.** **14 AI ഏജന്റ് റൺടൈമുകൾക്കായുള്ള** തത്സമയ ഒബ്സർവബിലിറ്റി: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex കൂടാതെ 10 എണ്ണം കൂടി. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരു ഡാഷ്ബോർഡ്.

> 🌐 **ഇത് ഇതിൽ വായിക്കുക:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

ഒരൊറ്റ കമാൻഡ്. കോൺഫിഗ് ഒന്നും വേണ്ട. എല്ലാം സ്വയമേവ കണ്ടെത്തുന്നു.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ൽ തുറക്കുന്നു, കഴിഞ്ഞു.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ഏജന്റ് റൺടൈമുകളുമായി പ്രവർത്തിക്കുന്നു

ClawMetry OpenClaw-നായുള്ള ഒബ്സർവബിലിറ്റിയായി ആരംഭിച്ചു, ഇപ്പോൾ ഒരൊറ്റ ഡാഷ്ബോർഡിൽ നിങ്ങളുടെ **മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റും** അളക്കുന്നു, നിങ്ങളുടെ മെഷീനിലെ ഓരോ റൺടൈമും സ്വയമേവ കണ്ടെത്തിക്കൊണ്ട്:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw, NemoClaw എന്നിവ ഓപ്പൺ സോഴ്‌സ് ആപ്പിൽ സൗജന്യമാണ്; മറ്റ് റൺടൈമുകൾ ClawMetry Cloud വഴിയോ സ്വയം ഹോസ്റ്റ് ചെയ്ത Pro ലൈസൻസ് വഴിയോ പ്രവർത്തനക്ഷമമാകും. ഹെഡറിൽ നിന്ന് റൺടൈമുകൾ മാറ്റുക, ഓരോ ടാബും — cost, tokens, tools, traces — ആ റൺടൈമിലേക്ക് വീണ്ടും സ്കോപ്പ് ചെയ്യപ്പെടും. കൃത്യമായ സൗജന്യ/പെയ്ഡ് വിഭജനം, ടയർ മാട്രിക്സ്, `/api/entitlement` ഷേപ്പ്, `clawmetry license` CLI എന്നിവയ്ക്കായി **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** കാണുക.

## നിങ്ങൾക്ക് ലഭിക്കുന്നത്

- **Flow** — ചാനലുകൾ, ബ്രെയിൻ, ടൂളുകൾ എന്നിവയിലൂടെ സന്ദേശങ്ങൾ ഒഴുകുന്നതും തിരികെ വരുന്നതും കാണിക്കുന്ന ലൈവ് ആനിമേറ്റഡ് ഡയഗ്രം
- **Overview** — ഹെൽത്ത് ചെക്കുകൾ, ആക്റ്റിവിറ്റി ഹീറ്റ്മാപ്പ്, സെഷൻ കൗണ്ടുകൾ, മോഡൽ വിവരങ്ങൾ
- **Usage** — ദിവസേന/ആഴ്ചതോറും/മാസംതോറും ബ്രേക്ക്ഡൗണോടു കൂടിയ ടോക്കൺ, കോസ്റ്റ് ട്രാക്കിംഗ്
- **Sessions** — മോഡൽ, ടോക്കണുകൾ, അവസാന ആക്റ്റിവിറ്റി എന്നിവയോടു കൂടിയ സജീവ ഏജന്റ് സെഷനുകൾ
- **Crons** — സ്റ്റാറ്റസ്, അടുത്ത റൺ, ദൈർഘ്യം എന്നിവയോടു കൂടിയ ഷെഡ്യൂൾ ചെയ്ത ജോലികൾ
- **Logs** — കളർ-കോഡഡ് തത്സമയ ലോഗ് സ്ട്രീമിംഗ്
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ദിവസേനയുള്ള കുറിപ്പുകൾ ബ്രൗസ് ചെയ്യുക
- **Transcripts** — സെഷൻ ചരിത്രങ്ങൾ വായിക്കുന്നതിനുള്ള ചാറ്റ്-ബബിൾ UI
- **Alerts** — ബജറ്റ് കാപ്പുകൾ, എറർ-റേറ്റ് ട്രിഗറുകൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ കണ്ടെത്തൽ; Slack, Discord, PagerDuty, Telegram, Email എന്നിവയിലേക്ക് റൂട്ട് ചെയ്യുന്നു
- **Approvals** — വിനാശകരമായ ഡിലീറ്റുകൾ, ഫോഴ്‌സ് പുഷുകൾ, DB മ്യൂട്ടേഷനുകൾ, sudo, പാക്കേജ് ഇൻസ്റ്റാളുകൾ, നെറ്റ്‌വർക്ക് കോളുകൾ എന്നിവ ഒറ്റ-ക്ലിക്ക് സൈൻ-ഓഫിന് പിന്നിൽ ഗേറ്റ് ചെയ്യുക

## സ്ക്രീൻഷോട്ടുകൾ

### 🧠 Brain — ലൈവ് ഏജന്റ് ഇവന്റ് സ്ട്രീം
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ടോക്കൺ ഉപയോഗവും സെഷൻ സംഗ്രഹവും
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — തത്സമയ ടൂൾ കോൾ ഫീഡ്
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — മോഡലും സെഷനും അനുസരിച്ചുള്ള കോസ്റ്റ് ബ്രേക്ക്ഡൗൺ
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — വർക്ക്സ്പേസ് ഫയൽ ബ്രൗസർ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — പൊസ്ചറും ഓഡിറ്റ് ലോഗും
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ബജറ്റ് കാപ്പുകൾ, എറർ-റേറ്റ് ട്രിഗറുകൾ, Slack / Discord / PagerDuty / Email എന്നിവയിലേക്കുള്ള വെബ്‌ഹുക്കുകൾ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — അപകടകരമായ ടൂൾ കോളുകൾ മാനുവൽ സൈൻ-ഓഫിന് പിന്നിൽ ഗേറ്റ് ചെയ്യുക; പോളിസി-പിന്തുണയുള്ള സംരക്ഷണ നിയമങ്ങൾ
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-നുള്ള പ്രീ-എക്‌സിക്യൂഷൻ ബ്ലോക്കിംഗ്** — ഒരു കമാൻഡ് ഒരു
PreToolUse ഹുക്ക് ഇൻസ്റ്റാൾ ചെയ്യുന്നു, ഇത് പൊരുത്തപ്പെടുന്ന ടൂൾ കോളുകൾ *അവ റൺ ചെയ്യുന്നതിന് മുൻപ്* താൽക്കാലികമായി നിർത്തുകയും
നിങ്ങളുടെ തീരുമാനത്തിനായി കാത്തിരിക്കുകയും ചെയ്യുന്നു (
[ക്ലൗഡ് പുഷ് നോട്ടിഫിക്കേഷനുകൾ](https://app.clawmetry.com/push) പ്രവർത്തനക്ഷമമാക്കിയാൽ നിങ്ങളുടെ ഫോണിൽ നിന്ന് ഒറ്റ ടാപ്പ്):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ഒരു ഡിനൈ (deny) ആ ഒരു ടൂൾ കോൾ മാത്രം ബ്ലോക്ക് ചെയ്യുന്നു — ഏജന്റിന് അതിന്റെ സെഷൻ നിലനിർത്താനും
മറ്റൊരു സമീപനം പരീക്ഷിക്കാനും കഴിയും. നിങ്ങളുടെ ഫോണിൽ അപ്രൂവ് ചെയ്യുന്നത് Claude Code-ന്റെ സ്വന്തം
പെർമിഷൻ പ്രോംപ്റ്റ് ഒഴിവാക്കുന്നു (നിങ്ങൾ ഇതിനകം ഉത്തരം നൽകിക്കഴിഞ്ഞു). പൊരുത്തപ്പെടാത്ത ടൂളുകൾക്ക് ~40ms ചെലവ്
വരികയും Claude Code-ന്റെ സാധാരണ പെർമിഷൻ ഫ്ലോയിലേക്ക് വീഴുകയും ചെയ്യുന്നു. Claude Code തന്നെ
നിങ്ങൾക്കായി കാത്തിരിക്കുമ്പോഴും (`permission_prompt` / `idle_prompt` നോട്ടിഫിക്കേഷനുകൾ) നിങ്ങൾക്ക് ഒരു ഫോൺ പുഷ് ലഭിക്കും.

## ഇൻസ്റ്റാൾ ചെയ്യുക

**ഒറ്റ-ലൈനർ (ശുപാർശ ചെയ്യുന്നത്):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**സോഴ്‌സിൽ നിന്ന്:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 ഫ്രണ്ട്എൻഡ് ഡെവലപ്മെന്റ്

v2 React ആപ്പ് `frontend/`-ൽ ജീവിക്കുന്നു, v2 പ്രവർത്തനക്ഷമമാക്കി Flask
സെർവർ ആരംഭിക്കുമ്പോൾ `/v2`-ൽ സെർവ് ചെയ്യപ്പെടുന്നു.

ഡെവലപ്പ് ചെയ്യുമ്പോൾ രണ്ട് ടെർമിനലുകൾ ഉപയോഗിക്കുക:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` തുറക്കുക. Vite `/api` റിക്വസ്റ്റുകൾ
`http://localhost:8900`-ലേക്ക് പ്രോക്സി ചെയ്യുന്നു, അതിനാൽ അധിക CORS സെറ്റപ്പ് ഇല്ലാതെ തന്നെ React ആപ്പിന് ലോക്കൽ Flask സെർവറുമായി സംസാരിക്കാൻ കഴിയും.

Python പാക്കേജിനൊപ്പം ഷിപ്പ് ചെയ്യുന്ന ബണ്ടിൽ ബിൽഡ് ചെയ്യാൻ:

```bash
cd frontend
npm run build
```

പ്രൊഡക്ഷൻ ബണ്ടിൽ `clawmetry/static/v2/dist/`-ലേക്ക് എഴുതപ്പെടുന്നു.

## റൺടൈം / ഏജന്റ് കോംപാറ്റിബിലിറ്റി

ClawMetry പല AI-ഏജന്റ് റൺടൈമുകളും നിരീക്ഷിക്കുന്നു, OpenClaw മാത്രമല്ല. OpenClaw ഒഴികെയുള്ള ഓരോ റൺടൈമും അതിന്റെ നേറ്റീവ് സെഷൻ ഫോർമാറ്റ് ClawMetry-യുടെ ഏകീകൃത ഷേപ്പുകളിലേക്ക് വിവർത്തനം ചെയ്യുന്ന ഒരു സമർപ്പിത റീഡർ അഡാപ്റ്റർ ഷിപ്പ് ചെയ്യുന്നു; ഡെമൺ അവയെ അതേ DuckDB സ്റ്റോർ + ക്ലൗഡ് സ്നാപ്ഷോട്ടിലേക്ക് ഇൻജസ്റ്റ് ചെയ്യുന്നു, റൺടൈം ടാഗ് ചെയ്തിരിക്കുന്നു, ഒന്നിലധികം സാന്നിധ്യമുള്ളപ്പോൾ Session replay ടാബ് ഒരു **റൺടൈം സ്വിച്ചർ** കാണിക്കുന്നു. പൂർണ്ണമായ മാട്രിക്സിനും റൺടൈമുകൾ ചേർക്കുന്നതിനുള്ള ഗൈഡിനുമായി [`docs/compatibility.md`](docs/compatibility.md) കാണുക, കൂടാതെ OpenClaw-ഫാമിലി പ്രൈമറിനായി [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) കാണുക.

[Perplexity-യുടെ numbat](https://github.com/perplexityai/numbat) ഏജന്റ്-സെക്യൂരിറ്റി ടൂൾ പ്രവർത്തിപ്പിക്കുന്നുണ്ടോ? ClawMetry അതിന്റെ കണ്ടെത്തലുകളും എൻഫോഴ്‌സ്മെന്റ് തീരുമാനങ്ങളും ബോക്സിന് പുറത്ത് തന്നെ ഇൻജസ്റ്റ് ചെയ്യുന്നു — [`docs/NUMBAT.md`](docs/NUMBAT.md) കാണുക.

| Runtime / Agent | Status | Notes |
|---|---|---|
| **OpenClaw** | നേറ്റീവ് | റഫറൻസ് റൺടൈം, സ്വയമേവ കണ്ടെത്തുന്നത് |
| **PicoClaw** | ബീറ്റ അഡാപ്റ്റർ | ഫ്ലാറ്റ് `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ. |
| **NanoClaw** | ബീറ്റ അഡാപ്റ്റർ | ഓരോ-സെഷനും SQLite (`data/v2-sessions`). ട്രാൻസ്ക്രിപ്റ്റുകൾ + സന്ദേശ എണ്ണങ്ങൾ. |
| **Hermes** | ബീറ്റ അഡാപ്റ്റർ | SQLite `~/.hermes/state.db`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടോക്കണുകൾ/ചെലവ്. |
| **Claude Code** | ബീറ്റ അഡാപ്റ്റർ | JSONL `~/.claude/projects/.../<id>.jsonl`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ചിന്തയോടു കൂടിയ ടൂൾ കോളുകൾ, ടോക്കൺ ഉപയോഗം. |
| **Codex** | ബീറ്റ അഡാപ്റ്റർ | റോൾഔട്ട് JSONL `~/.codex/sessions/...`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ഉപയോഗം. |
| **Cursor** | ബീറ്റ അഡാപ്റ്റർ | SQLite `state.vscdb`. ചാറ്റ്/കമ്പോസർ ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ. |
| **Aider** | ബീറ്റ അഡാപ്റ്റർ | ഓരോ പ്രോജക്ടിനും `.aider.chat.history.md`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടോക്കൺ എണ്ണങ്ങൾ. |
| **Goose** | ബീറ്റ അഡാപ്റ്റർ | SQLite `~/.local/share/goose`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ടോട്ടലുകൾ. |
| **opencode** | ബീറ്റ അഡാപ്റ്റർ | SQLite `~/.local/share/opencode`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കണുകൾ + ചെലവ്. |
| **Qwen Code** | ബീറ്റ അഡാപ്റ്റർ | JSONL `~/.qwen/projects/.../chats`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ഉപയോഗം. |
| **Pi** | ബീറ്റ അഡാപ്റ്റർ | JSONL `~/.pi/agent/sessions`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കണുകൾ + ചെലവ്. |
| **Deep Agents** | ബീറ്റ അഡാപ്റ്റർ | SQLite `~/.deepagents/.state/sessions.db`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കണുകൾ + ചെലവ്. |
| **n8n** | ബീറ്റ അഡാപ്റ്റർ | SQLite `~/.n8n/database.sqlite`. വർക്ക്ഫ്ലോ എക്സിക്യൂഷനുകൾ, നോഡ് റണ്ണുകൾ, AI Agent പ്രോംപ്റ്റുകൾ, n8n രേഖപ്പെടുത്തുന്നിടത്ത് മോഡൽ + ടോക്കണുകൾ. |
| **Antigravity** | ബീറ്റ അഡാപ്റ്റർ | `~/.gemini/<flavor>/brain/`-ന് കീഴിലുള്ള ബ്രെയിൻ JSONL. സംഭാഷണങ്ങൾ, ടൂൾ സ്റ്റെപ്പുകൾ, ചിന്ത, ഓരോ-ജനറേഷനും Gemini ടോക്കൺ വിഭജനം + ചെലവ്, ബാക്ക്‌ഗ്രൗണ്ട്-ജനറേഷൻ ബേൺ. |

"ബീറ്റ അഡാപ്റ്റർ" എന്നാൽ ClawMetry ആ റൺടൈമിന്റെ യഥാർത്ഥ ഓൺ-ഡിസ്ക് ഫോർമാറ്റിനുള്ള ഒരു റീഡർ ഷിപ്പ് ചെയ്യുന്നു, ഓരോന്നും ഒരു യഥാർത്ഥ മെഷീനിലെ യഥാർത്ഥ ഇൻസ്റ്റാളിനെതിരെ നിർമ്മിച്ചതും പരിശോധിച്ചുറപ്പിച്ചതുമാണ് (`tests/fixtures/runtimes/<rt>/` കാണുക). അഡാപ്റ്ററുകൾ read-only ആണ്; ഓരോന്നും അതിന്റെ റൺടൈം യഥാർത്ഥത്തിൽ എന്താണ് സ്റ്റോർ ചെയ്യുന്നത് എന്നതിനെക്കുറിച്ച് സത്യസന്ധമാണ് (ഉദാ. PicoClaw/NanoClaw/Cursor ടോക്കൺ ചെലവ് ഡിസ്കിലേക്ക് എഴുതുന്നില്ല). ഒരു നോഡിൽ ഒന്നിലധികം റൺടൈമുകൾ പ്രവർത്തിക്കുമ്പോൾ, ക്ലീൻ ഡീപ്-ഡൈവിനായി റൺടൈം സ്വിച്ചർ സെഷനുകൾ വ്യൂ ഒന്നിലേക്ക് സ്കോപ്പ് ചെയ്യുന്നു.

## ഏത് SDK ഏജന്റും ട്രാക്ക് ചെയ്യുക — ഔട്ട്-ലൂപ്പ് കോസ്റ്റ് ആട്രിബ്യൂഷൻ

മുകളിലുള്ള റൺടൈമുകളെല്ലാം സെഷനുകൾ ഡിസ്കിലേക്ക് എഴുതുന്നു. നിങ്ങളുടെ സ്വന്തം **പ്രൊഡക്ഷൻ ഏജന്റ്** — OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, അല്ലെങ്കിൽ ഒരു സാധാരണ `httpx` ലൂപ്പ് ഉപയോഗിച്ച് നിങ്ങൾ നിർമ്മിച്ചത് — ചെയ്യുന്നില്ല. ClawMetry-യുടെ zero-config ഇന്റർസെപ്റ്റർ ഇപ്പോഴും `httpx`/`requests` മങ്കി-പാച്ച് ചെയ്തുകൊണ്ട് അതിന്റെ LLM കോളുകൾ (cost, tokens, latency, errors) പിടിച്ചെടുക്കുന്നു:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (അല്ലെങ്കിൽ `CLAWMETRY_SOURCE=support-agent` env var) ഓരോ കോളിനെയും ഒരു **പേരുള്ള സോഴ്‌സ്** ഉപയോഗിച്ച് ടാഗ് ചെയ്യുന്നു, അതിനാൽ നിങ്ങൾ പ്രവർത്തിപ്പിക്കുന്ന ഓരോ പ്രൊഡക്ടും ഡാഷ്ബോർഡിന്റെ Overview-ലെ **🔌 Out-loop sources** കാർഡിൽ അതിന്റേതായ ഫസ്റ്റ്-ക്ലാസ്, ചെലവ്-ആട്രിബ്യൂട്ട് ചെയ്യാവുന്ന ഒരു ലൈനായി കാണിക്കും — ഓരോ ഏജന്റിനും കോളുകൾ, പ്രൊവൈഡറുകൾ, ലേറ്റൻസി, എറർ റേറ്റ്. സോഴ്‌സ് സെറ്റ് ചെയ്തിട്ടില്ലേ? കോളുകൾ ഇപ്പോഴും ട്രാക്ക് ചെയ്യപ്പെടും, കാർഡ് മാത്രം മറഞ്ഞിരിക്കും.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ഇത് റൺടൈം അഡാപ്റ്ററുകൾ ഫീഡ് ചെയ്യുന്ന അതേ ഡാറ്റ ലെയർ ആണ് (DuckDB → ക്ലൗഡ് സ്നാപ്ഷോട്ട്), അതിനാൽ ഔട്ട്-ലൂപ്പ് സോഴ്‌സുകൾ മറ്റെല്ലാം പോലെ ക്ലൗഡ് ഡാഷ്ബോർഡിലേക്ക് സിങ്ക് ചെയ്യുന്നു, E2E-എൻക്രിപ്റ്റഡ്.

## OpenTelemetry — vendor-neutral, നിങ്ങളുടെ traces എവിടെയും അയക്കുക

ClawMetry രണ്ട് ദിശകളിലും **OpenTelemetry** സംസാരിക്കുന്നു, **GenAI സെമാന്റിക് കൺവെൻഷനുകൾ** ഉപയോഗിച്ച്, അതിനാൽ നിങ്ങളുടെ ഏജന്റ് traces ഒരിക്കലും ഒരു ടൂളിലേക്ക് ലോക്ക് ചെയ്യപ്പെടില്ല.

ഓരോ സെഷനും — LLM കോളുകൾ, ടൂളുകൾ, സബ്-ഏജന്റുകൾ, ടോക്കണുകൾ, ചെലവ് — ഏത് കളക്ടറിലേക്കും (Datadog, Grafana, Honeycomb, അല്ലെങ്കിൽ നിങ്ങളുടെ സ്വന്തം OTel Collector) OTLP/HTTP GenAI spans ആയി **എക്സ്പോർട്ട്** ചെയ്യുക:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth ഹെഡറുകളും പോൾ ഇന്റർവെലും ഓപ്ഷണൽ env vars ആണ്:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ഇൻജസ്റ്റ്** — ബിൽറ്റ്-ഇൻ OTLP റിസീവർ `/v1/traces`, `/v1/metrics` എന്നിവയിൽ മറ്റെവിടെ നിന്നും traces, metrics സ്വീകരിക്കുന്നു (protobuf ഇൻജസ്റ്റിനായി `pip install clawmetry[otel]`).

നിങ്ങൾക്ക് zero-config, local-first ClawMetry ഡാഷ്ബോർഡും **കൂടെ** നിങ്ങളുടെ ടീം ഇതിനകം പ്രവർത്തിപ്പിക്കുന്ന ഏത് ബാക്കെൻഡിലും നിങ്ങളുടെ ഡാറ്റയും ലഭിക്കും — ലോക്ക്-ഇൻ ഇല്ല, രണ്ടാമത്തെ ഏജന്റ് ഇൻസ്റ്റാൾ ചെയ്യേണ്ട ആവശ്യമില്ല.

## കോൺഫിഗറേഷൻ

മിക്ക ആളുകൾക്കും ഒരു കോൺഫിഗും ആവശ്യമില്ല. ClawMetry നിങ്ങളുടെ വർക്ക്സ്പേസ്, ലോഗുകൾ, സെഷനുകൾ, crons എന്നിവ സ്വയമേവ കണ്ടെത്തുന്നു.

നിങ്ങൾക്ക് കസ്റ്റമൈസ് ചെയ്യേണ്ടതുണ്ടെങ്കിൽ:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

എല്ലാ ഓപ്ഷനുകളും: `clawmetry --help`

## പിന്തുണയ്ക്കുന്ന ചാനലുകൾ

നിങ്ങൾ കോൺഫിഗർ ചെയ്ത ഓരോ OpenClaw ചാനലിനും ClawMetry തത്സമയ ആക്റ്റിവിറ്റി കാണിക്കുന്നു. നിങ്ങളുടെ `openclaw.json`-ൽ യഥാർത്ഥത്തിൽ സെറ്റപ്പ് ചെയ്ത ചാനലുകൾ മാത്രമേ Flow ഡയഗ്രമിൽ ദൃശ്യമാകൂ — കോൺഫിഗർ ചെയ്യാത്തവ സ്വയമേവ മറയ്ക്കപ്പെടും.

വരുന്നതും പോകുന്നതുമായ സന്ദേശ എണ്ണങ്ങളുള്ള ലൈവ് ചാറ്റ് ബബിൾ വ്യൂ കാണാൻ Flow-ലെ ഏത് ചാനൽ നോഡിലും ക്ലിക്ക് ചെയ്യുക.

| Channel | Status | Live Popup | Notes |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | സന്ദേശങ്ങൾ, സ്ഥിതിവിവരക്കണക്കുകൾ, 10s റിഫ്രഷ് |
| 💬 **iMessage** | ✅ Full | ✅ | `~/Library/Messages/chat.db` നേരിട്ട് വായിക്കുന്നു |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) വഴി |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli വഴി |
| 🟣 **Discord** | ✅ Full | ✅ | Guild + channel കണ്ടെത്തൽ |
| 🟪 **Slack** | ✅ Full | ✅ | Workspace + channel കണ്ടെത്തൽ |
| 🌐 **Webchat** | ✅ Full | ✅ | ബിൽറ്റ്-ഇൻ വെബ് UI സെഷനുകൾ |
| 📡 **IRC** | ✅ Full | ✅ | ടെർമിനൽ-ശൈലി ബബിൾ UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API വഴി iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API വെബ്‌ഹുക്കുകൾ വഴി |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams bot പ്ലഗിൻ വഴി |
| 🔷 **Mattermost** | ✅ Full | ✅ | സ്വയം-ഹോസ്റ്റ് ചെയ്ത ടീം ചാറ്റ് |
| 🟩 **Matrix** | ✅ Full | ✅ | വികേന്ദ്രീകൃതം, E2EE പിന്തുണ |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | വികേന്ദ്രീകൃത NIP-04 DMs |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC കണക്ഷൻ വഴി ചാറ്റ് |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket ഇവന്റ് സബ്സ്ക്രിപ്ഷൻ |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **സ്വയമേവ കണ്ടെത്തൽ:** ClawMetry നിങ്ങളുടെ `~/.openclaw/openclaw.json` വായിക്കുകയും നിങ്ങൾ യഥാർത്ഥത്തിൽ കോൺഫിഗർ ചെയ്ത ചാനലുകൾ മാത്രം റെൻഡർ ചെയ്യുകയും ചെയ്യുന്നു. മാനുവൽ സെറ്റപ്പ് ആവശ്യമില്ല.

## Docker ഡിപ്ലോയ്മെന്റ്

ClawMetry ഒരു കണ്ടെയ്നറിൽ പ്രവർത്തിപ്പിക്കണോ? കുഴപ്പമില്ല! 🐳

**Docker ഉപയോഗിച്ചുള്ള ദ്രുത ആരംഭം:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Docker Compose ഉദാഹരണം:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **ശ്രദ്ധിക്കുക:** Docker-ൽ പ്രവർത്തിപ്പിക്കുമ്പോൾ, ClawMetry-ക്ക് നിങ്ങളുടെ സെറ്റപ്പ് സ്വയമേവ കണ്ടെത്താൻ കഴിയുന്നതിന് നിങ്ങളുടെ ഏജന്റിന്റെ ഡാറ്റ + ലോഗ് ഡയറക്ടറികൾ (ഉദാ. `~/.openclaw`, `~/.claude`, `~/.codex`) മൗണ്ട് ചെയ്യുക.

## ആവശ്യകതകൾ

- Python 3.8+
- Flask (pip വഴി സ്വയമേവ ഇൻസ്റ്റാൾ ചെയ്യപ്പെടുന്നു)
- അതേ മെഷീനിലുള്ള ഒരു AI ഏജന്റ് റൺടൈം: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, അല്ലെങ്കിൽ Antigravity (അല്ലെങ്കിൽ Docker-നായി മൗണ്ട് ചെയ്ത വോള്യങ്ങൾ)
- Linux അല്ലെങ്കിൽ macOS

## NemoClaw / OpenShell പിന്തുണ

[NemoClaw](https://github.com/NVIDIA/NemoClaw) — sandboxed OpenShell കണ്ടെയ്നറുകൾക്കുള്ളിൽ ഏജന്റുകൾ പ്രവർത്തിപ്പിക്കുന്ന OpenClaw-നുള്ള NVIDIA-യുടെ എന്റർപ്രൈസ് സെക്യൂരിറ്റി റാപ്പർ — ClawMetry സ്വയമേവ കണ്ടെത്തുന്നു.

മിക്ക കേസുകളിലും അധിക കോൺഫിഗറേഷൻ ആവശ്യമില്ല. സെഷൻ ഫയലുകൾ ഹോസ്റ്റിലെ `~/.openclaw/`-ൽ ആയാലും OpenShell കണ്ടെയ്നറിനുള്ളിൽ ആയാലും sync ഡെമൺ അവ സ്വയമേവ കണ്ടെത്തുന്നു.

### ഇത് എങ്ങനെ പ്രവർത്തിക്കുന്നു

ClawMetry NemoClaw-യെ രണ്ട് വിധത്തിൽ കണ്ടെത്തുന്നു:

1. **ബൈനറി കണ്ടെത്തൽ** — `nemoclaw` CLI-ക്കായി പരിശോധിക്കുകയും sandbox വിവരങ്ങൾ ലഭിക്കാൻ `nemoclaw status` പ്രവർത്തിപ്പിക്കുകയും ചെയ്യുന്നു
2. **കണ്ടെയ്നർ കണ്ടെത്തൽ** — `openshell`, `nemoclaw`, അല്ലെങ്കിൽ `ghcr.io/nvidia/` ഇമേജുകൾക്കായി പ്രവർത്തിക്കുന്ന Docker കണ്ടെയ്നറുകൾ സ്കാൻ ചെയ്യുന്നു, തുടർന്ന് വോള്യം മൗണ്ടുകൾ വഴിയോ `docker cp` വഴിയോ സെഷനുകൾ വായിക്കുന്നു

NemoClaw കണ്ടെയ്നറുകളിൽ നിന്ന് സിങ്ക് ചെയ്ത സെഷൻ ഫയലുകൾ ക്ലൗഡ് ഡാഷ്ബോർഡിൽ `runtime=nemoclaw`, `container_id` മെറ്റാഡാറ്റ എന്നിവ ഉപയോഗിച്ച് ടാഗ് ചെയ്യപ്പെടുന്നു, അതിനാൽ ഒറ്റനോട്ടത്തിൽ അവയെ സ്റ്റാൻഡേർഡ് OpenClaw സെഷനുകളിൽ നിന്ന് വേർതിരിച്ചറിയാൻ കഴിയും.

### ശുപാർശ ചെയ്യുന്ന സെറ്റപ്പ്: HOST-ൽ sync ഡെമൺ

മികച്ച അനുഭവത്തിനായി, ClawMetry-യുടെ sync ഡെമൺ **host മെഷീനിൽ** (sandbox-നുള്ളിൽ അല്ല) പ്രവർത്തിപ്പിക്കുക. ഇത് NemoClaw നെറ്റ്‌വർക്ക് പോളിസി നിയന്ത്രണങ്ങൾ ഒഴിവാക്കുന്നു.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync ഡെമൺ പ്രവർത്തിക്കുന്ന ഏത് OpenShell കണ്ടെയ്നറിനുള്ളിലെയും സെഷനുകൾ സ്വയമേവ കണ്ടെത്തും.

### ഓപ്ഷണൽ: വ്യക്തമായ sandbox പേര്

സ്വയമേവ കണ്ടെത്തൽ പ്രവർത്തിക്കുന്നില്ലെങ്കിൽ, ClawMetry-യെ ശരിയായ sandbox-ലേക്ക് ചൂണ്ടിക്കാണിക്കുക:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### sandbox-നുള്ളിൽ പ്രവർത്തിപ്പിക്കുന്നത് (advanced)

sync ഡെമൺ OpenShell sandbox-നുള്ളിൽ **തന്നെ** പ്രവർത്തിപ്പിക്കണമെങ്കിൽ, അതിന് ClawMetry ingest API-യിലേക്ക് എത്താൻ കഴിയുന്നതിന് നിങ്ങളുടെ NemoClaw നെറ്റ്‌വർക്ക് പോളിസിയിലേക്ക് ഈ egress നിയമം ചേർക്കുക:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

ഇതുപയോഗിച്ച് പ്രയോഗിക്കുക:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### പോർട്ടുകളും എൻഡ്‌പോയിന്റുകളും

| Endpoint | Port | Protocol | Required |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | അതെ (sync ഡെമൺ → ക്ലൗഡ്) |
| `localhost:8900` | 8900 | HTTP | അതെ (ലോക്കൽ ഡാഷ്ബോർഡ് UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | കണ്ടെയ്നർ സെഷൻ കണ്ടെത്തലിനായി |

sync ഡെമൺ `ingest.clawmetry.com`-ലേക്ക് മാത്രമേ ഔട്ട്ബൗണ്ട് HTTPS കോളുകൾ നടത്തൂ. ഇൻബൗണ്ട് പോർട്ടുകൾ ആവശ്യമില്ല.

---

## ക്ലൗഡ് ഡിപ്ലോയ്മെന്റ്

SSH ടണലുകൾ, റിവേഴ്‌സ് പ്രോക്സി, Docker എന്നിവയ്ക്കായി **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** കാണുക.

## ടെസ്റ്റിംഗ്

ഈ പ്രോജക്ട് BrowserStack ഉപയോഗിച്ച് ടെസ്റ്റ് ചെയ്യപ്പെടുന്നു.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ടെലിമെട്രി

ClawMetry `https://app.clawmetry.com/api/install`-ലേക്ക് അജ്ഞാത
ഇൻസ്റ്റാൾ-ലൈഫ്‌സൈക്കിൾ പിംഗുകൾ അയക്കുന്നു: ഒരു പുതിയ മെഷീനിൽ ആദ്യമായി `clawmetry` CLI
പ്രവർത്തിപ്പിക്കുമ്പോൾ ഒരു `install` പിംഗ്, ഒരു പുതിയ വേർഷനിലേക്ക് അപ്ഗ്രേഡ് ചെയ്തതിന് ശേഷമുള്ള
ആദ്യ റണ്ണിൽ ഒരു `update` പിംഗ്, ഇൻ-ഡാഷ്ബോർഡ് ഓൺബോർഡിംഗ് തിരഞ്ഞെടുപ്പ് പൂർത്തിയാക്കുമ്പോൾ ഒരു
`onboarded` പിംഗ്. യഥാർത്ഥ ഇൻസ്റ്റാളുകൾ എണ്ണാനും (റോ PyPI ഡൗൺലോഡ്
നമ്പറുകൾ ~98% മിററുകൾ, CI, ഓട്ടോ-അപ്ഡേറ്റ് വീണ്ടും-ഡൗൺലോഡുകൾ ആണ്) ഏതൊക്കെ ഏജന്റ് ഫ്രെയിംവർക്കുകളും
വേർഷനുകളും യഥാർത്ഥത്തിൽ ഉപയോഗത്തിലുണ്ടെന്ന് അറിയാനും ഞങ്ങൾ ഇത് ഉപയോഗിക്കുന്നു.

**ഓരോ ലൈഫ്‌സൈക്കിൾ ഇവന്റിനും ഓരോ വേർഷനും പരമാവധി ഒരു POST**, ഇതിൽ ഇവ അടങ്ങിയിരിക്കുന്നു:

| Field | Example | Why |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`-ൽ സൂക്ഷിച്ചിരിക്കുന്ന റാൻഡം UUID | ഡീഡ്യൂപ്പ്; നിങ്ങൾ വ്യക്തമായി Cloud sync കണക്റ്റ് ചെയ്യുന്നത് വരെ അജ്ഞാതം (ഓതന്റിക്കേറ്റഡ് ഡെമൺ ഹാർട്ട്ബീറ്റ് പിന്നീട് ഇത് വഹിക്കുന്നു, ഈ ഇൻസ്റ്റാളിനെ നിങ്ങളുടെ അക്കൗണ്ടുമായി ബന്ധിപ്പിക്കുന്നു) |
| `event` | `install` / `update` / `onboarded` | പുതിയ ഇൻസ്റ്റാൾ vs നിലവിലുള്ള ഒന്നിന്റെ അപ്ഗ്രേഡ് |
| `version` | `0.12.167` | ഏതൊക്കെ വേർഷനുകൾ ഉപയോഗത്തിലുണ്ട് |
| `os` / `os_version` | `Darwin` / `25.3.0` | പ്ലാറ്റ്ഫോം പിന്തുണ മുൻഗണനകൾ |
| `python` | `3.11.15` | Python വേർഷൻ പിന്തുണ മാട്രിക്സ് |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | അടുത്തതായി ഏതൊക്കെ ഏജന്റുകളുമായി ഞങ്ങൾ ഇന്റഗ്രേറ്റ് ചെയ്യണം |
| `is_ci` / `ci_provider` | `true` / `github_actions` | മനുഷ്യ ഇൻസ്റ്റാളുകളെ CI ശബ്ദത്തിൽ നിന്ന് വേർതിരിക്കുന്നു |

**ഞങ്ങൾ അയക്കാത്തത്**: IP (ക്ലൗഡ് സെർവർ-സൈഡിൽ റിക്വസ്റ്റിൽ നിന്ന് കൺട്രി കോഡ്
ഡെറൈവ് ചെയ്യുന്നു, തുടർന്ന് IP നിരസിക്കുന്നു), ഹോസ്റ്റ്നെയിം, യൂസർനെയിം, വർക്ക്സ്പേസ്
പാത്ത്, ഫയൽ ഉള്ളടക്കങ്ങൾ, നിങ്ങളുടെ api_key, നിങ്ങളുടെ ഇമെയിൽ, PII അല്ലെങ്കിൽ
വർക്ക്സ്പേസ്-നിർദ്ദിഷ്ടമായ എന്തെങ്കിലും. വയർ പേലോഡ് ഓഡിറ്റ് ചെയ്യാവുന്നതാണ്
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)-ൽ.

**ഒപ്റ്റ് ഔട്ട്** (ഇവയിൽ ഏതെങ്കിലും ഒന്ന് ഇത് സ്ഥിരമായി പ്രവർത്തനരഹിതമാക്കുന്നു):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ഇവിടെ ഒരു നെറ്റ്‌വർക്ക് പരാജയം ഒരിക്കലും `clawmetry` പ്രവർത്തിക്കുന്നതിൽ നിന്ന് തടയില്ല — പിംഗ്
3 സെക്കൻഡ് ടൈംഔട്ടോടു കൂടിയ ഒരു ഡെമൺ ത്രെഡിൽ ഫയർ-ആന്റ്-ഫോർഗെറ്റ് ആണ്.

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ലൈസൻസ്

MIT

---

<p align="center">
  <strong>🦞 നിങ്ങളുടെ ഏജന്റ് ചിന്തിക്കുന്നത് കാണൂ</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> നിർമ്മിച്ചത് · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ഇക്കോസിസ്റ്റത്തിന്റെ ഭാഗം</sub>
</p>
