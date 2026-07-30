<!-- i18n-src:9a05336fbdc1 -->
> മലയാളം translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**നിങ്ങളുടെ ഏജന്റ് ചിന്തിക്കുന്നത് കാണൂ.** **14 AI ഏജന്റ് റൺടൈമുകൾക്കുള്ള** തത്സമയ നിരീക്ഷണം: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex, കൂടാതെ 10 എണ്ണം കൂടി. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരൊറ്റ ഡാഷ്ബോർഡ്.

> 🌐 **ഇത് ഇതിലും വായിക്കാം:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [കൂടുതൽ →](docs/i18n/)

ഒരൊറ്റ കമാൻഡ്. കോൺഫിഗ് ഒന്നും വേണ്ട. എല്ലാം സ്വയമേവ കണ്ടെത്തുന്നു.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ൽ തുറക്കും, അതോടെ പണി കഴിഞ്ഞു.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ഏജന്റ് റൺടൈമുകളുമായി പ്രവർത്തിക്കുന്നു

ClawMetry ആരംഭിച്ചത് OpenClaw-ന് വേണ്ടിയുള്ള നിരീക്ഷണമായിട്ടാണ്, ഇപ്പോൾ ഇത് നിങ്ങളുടെ **മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റും** ഒരൊറ്റ ഡാഷ്ബോർഡിൽ അളക്കുന്നു, നിങ്ങളുടെ മെഷീനിലുള്ള ഓരോ റൺടൈമും സ്വയമേവ കണ്ടെത്തിക്കൊണ്ട്:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw ഉം NemoClaw ഉം ഓപ്പൺ സോഴ്‌സ് ആപ്പിൽ സൗജന്യമാണ്; മറ്റ് റൺടൈമുകൾ ClawMetry Cloud ഉപയോഗിച്ചോ അല്ലെങ്കിൽ സ്വയം-ഹോസ്റ്റ് ചെയ്ത Pro ലൈസൻസ് ഉപയോഗിച്ചോ പ്രവർത്തനക്ഷമമാകും. ഹെഡറിൽ നിന്ന് റൺടൈമുകൾ മാറ്റുക, ഓരോ ടാബും - ചെലവ്, ടോക്കണുകൾ, ടൂളുകൾ, ട്രെയ്സുകൾ - ആ റൺടൈമിലേക്ക് വീണ്ടും സ്കോപ്പ് ചെയ്യപ്പെടും. കൃത്യമായ സൗജന്യ/പണമടച്ചുള്ള വിഭജനം, ടയർ മാട്രിക്സ്, `/api/entitlement` ഘടന, `clawmetry license` CLI എന്നിവയ്ക്കായി **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** കാണുക.

## നിങ്ങൾക്ക് ലഭിക്കുന്നത്

- **Flow** — ചാനലുകൾ, ബ്രെയിൻ, ടൂളുകൾ എന്നിവയിലൂടെ സന്ദേശങ്ങൾ ഒഴുകുന്നതും തിരികെ വരുന്നതും കാണിക്കുന്ന തത്സമയ ആനിമേറ്റഡ് ഡയഗ്രം
- **Overview** — ഹെൽത്ത് ചെക്കുകൾ, ആക്റ്റിവിറ്റി ഹീറ്റ്മാപ്പ്, സെഷൻ എണ്ണം, മോഡൽ വിവരങ്ങൾ
- **Usage** — ദിവസേന/ആഴ്ചതോറും/മാസംതോറുമുള്ള വിഭജനങ്ങളോടെയുള്ള ടോക്കൺ, ചെലവ് ട്രാക്കിംഗ്
- **Sessions** — മോഡൽ, ടോക്കണുകൾ, അവസാന പ്രവർത്തനം എന്നിവയോടെയുള്ള സജീവ ഏജന്റ് സെഷനുകൾ
- **Crons** — സ്റ്റാറ്റസ്, അടുത്ത റൺ, ദൈർഘ്യം എന്നിവയോടെയുള്ള ഷെഡ്യൂൾ ചെയ്ത ജോലികൾ
- **Logs** — കളർ-കോഡഡ് തത്സമയ ലോഗ് സ്ട്രീമിംഗ്
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ദിവസേനയുള്ള കുറിപ്പുകൾ എന്നിവ ബ്രൗസ് ചെയ്യുക
- **Transcripts** — സെഷൻ ചരിത്രങ്ങൾ വായിക്കാനുള്ള ചാറ്റ്-ബബിൾ UI
- **Alerts** — ബജറ്റ് പരിധികൾ, പിശക്-നിരക്ക് ട്രിഗറുകൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ കണ്ടെത്തൽ; Slack, Discord, PagerDuty, Telegram, Email എന്നിവയിലേക്ക് റൂട്ട് ചെയ്യുന്നു
- **Approvals** — നശിപ്പിക്കുന്ന ഡിലീറ്റുകൾ, ഫോഴ്‌സ് പുഷുകൾ, DB മ്യൂട്ടേഷനുകൾ, sudo, പാക്കേജ് ഇൻസ്റ്റാളേഷനുകൾ, നെറ്റ്‌വർക്ക് കോളുകൾ എന്നിവ ഒറ്റ-ക്ലിക്ക് അംഗീകാരത്തിന് പിന്നിൽ ഗേറ്റ് ചെയ്യുക

## സ്ക്രീൻഷോട്ടുകൾ

### 🧠 Brain — തത്സമയ ഏജന്റ് ഇവന്റ് സ്ട്രീം
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ടോക്കൺ ഉപയോഗവും സെഷൻ സംഗ്രഹവും
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — തത്സമയ ടൂൾ കോൾ ഫീഡ്
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — മോഡലും സെഷനും അനുസരിച്ചുള്ള ചെലവ് വിഭജനം
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — വർക്ക്‌സ്പേസ് ഫയൽ ബ്രൗസർ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — സ്ഥിതിയും ഓഡിറ്റ് ലോഗും
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ബജറ്റ് പരിധികൾ, പിശക്-നിരക്ക് ട്രിഗറുകൾ, Slack / Discord / PagerDuty / Email എന്നിവയിലേക്കുള്ള വെബ്‌ഹുക്കുകൾ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — അപകടകരമായ ടൂൾ കോളുകൾ മാനുവൽ അംഗീകാരത്തിന് പിന്നിൽ ഗേറ്റ് ചെയ്യുക; നയാധിഷ്ഠിത സംരക്ഷണ നിയമങ്ങൾ
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-നായുള്ള നിർവ്വഹണ-മുൻപുള്ള തടയൽ** — ഒരു കമാൻഡ് ഒരു
PreToolUse ഹുക്ക് ഇൻസ്റ്റാൾ ചെയ്യുന്നു, അത് പൊരുത്തപ്പെടുന്ന ടൂൾ കോളുകൾ *ഓടുന്നതിന് മുൻപ്*
താൽക്കാലികമായി നിർത്തി നിങ്ങളുടെ തീരുമാനത്തിനായി കാത്തിരിക്കുന്നു (
[ക്ലൗഡ് പുഷ് അറിയിപ്പുകൾ](https://app.clawmetry.com/push) പ്രവർത്തനക്ഷമമാക്കിയാൽ
നിങ്ങളുടെ ഫോണിൽ നിന്ന് ഒറ്റ ടാപ്പ്):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ഒരു നിരസിക്കൽ ആ ഒരു ടൂൾ കോൾ മാത്രം തടയുന്നു — ഏജന്റ് അതിന്റെ സെഷൻ നിലനിർത്തുകയും
മറ്റൊരു സമീപനം പരീക്ഷിക്കാൻ കഴിയുകയും ചെയ്യുന്നു. നിങ്ങളുടെ ഫോണിൽ അംഗീകരിക്കുന്നത് Claude Code-ന്റെ
സ്വന്തം അനുമതി പ്രോംപ്റ്റ് ഒഴിവാക്കുന്നു (നിങ്ങൾ ഇതിനകം ഉത്തരം നൽകിക്കഴിഞ്ഞു). പൊരുത്തപ്പെടാത്ത ടൂളുകൾക്ക് ~40ms
ചെലവ് വരികയും Claude Code-ന്റെ സാധാരണ അനുമതി ഫ്ലോയിലേക്ക് വീണ്ടും വീഴുകയും ചെയ്യുന്നു. Claude Code തന്നെ
നിങ്ങളെ കാത്തിരിക്കുമ്പോഴും നിങ്ങൾക്ക് ഫോൺ പുഷ് ലഭിക്കും (`permission_prompt` /
`idle_prompt` അറിയിപ്പുകൾ).

## ഇൻസ്റ്റാൾ ചെയ്യുക

**ഒറ്റ-ലൈൻ (ശുപാർശ ചെയ്യുന്നത്):**
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

v2 React ആപ്പ് `frontend/` ൽ ആണ് സ്ഥിതി ചെയ്യുന്നത്, v2 പ്രവർത്തനക്ഷമമാക്കി
Flask സെർവർ ആരംഭിക്കുമ്പോൾ `/v2` ൽ സെർവ് ചെയ്യപ്പെടും.

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

`http://localhost:5173/v2/` തുറക്കുക. Vite `/api` അഭ്യർത്ഥനകൾ
`http://localhost:8900` ലേക്ക് പ്രോക്സി ചെയ്യുന്നു, അതിനാൽ അധിക CORS സജ്ജീകരണം കൂടാതെ
React ആപ്പിന് ലോക്കൽ Flask സെർവറുമായി സംസാരിക്കാൻ കഴിയും.

Python പാക്കേജിനൊപ്പം ഷിപ്പ് ചെയ്യുന്ന ബണ്ടിൽ നിർമ്മിക്കാൻ:

```bash
cd frontend
npm run build
```

പ്രൊഡക്ഷൻ ബണ്ടിൽ `clawmetry/static/v2/dist/` ലേക്ക് എഴുതപ്പെടുന്നു.

## റൺടൈം / ഏജന്റ് അനുയോജ്യത

ClawMetry പല AI-ഏജന്റ് റൺടൈമുകളും നിരീക്ഷിക്കുന്നു, OpenClaw മാത്രമല്ല. OpenClaw അല്ലാത്ത ഓരോ റൺടൈമും അതിന്റെ നേറ്റീവ് സെഷൻ ഫോർമാറ്റിനെ ClawMetry-യുടെ ഏകീകൃത ഘടനകളിലേക്ക് പരിവർത്തനം ചെയ്യുന്ന ഒരു സമർപ്പിത റീഡർ അഡാപ്റ്റർ ഷിപ്പ് ചെയ്യുന്നു; ഡെമൺ അവയെ അതേ DuckDB സ്റ്റോറിലേക്കും ക്ലൗഡ് സ്നാപ്ഷോട്ടിലേക്കും ഇൻജസ്റ്റ് ചെയ്യുന്നു, റൺടൈം ടാഗ് ചെയ്തുകൊണ്ട്, ഒന്നിലധികം സാന്നിധ്യമുള്ളപ്പോൾ Session replay ടാബ് ഒരു **റൺടൈം സ്വിച്ചർ** കാണിക്കുന്നു. പൂർണ്ണ മാട്രിക്സിനും റൺടൈമുകൾ ചേർക്കുന്നതിനുള്ള ഗൈഡിനും [`docs/compatibility.md`](docs/compatibility.md) കാണുക, OpenClaw-ഫാമിലി പ്രൈമറിന് [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) കാണുക.

| റൺടൈം / ഏജന്റ് | സ്റ്റാറ്റസ് | കുറിപ്പുകൾ |
|---|---|---|
| **OpenClaw** | Native | റഫറൻസ് റൺടൈം, സ്വയമേവ കണ്ടെത്തുന്നു |
| **PicoClaw** | Beta adapter | ഫ്ലാറ്റ് `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ. |
| **NanoClaw** | Beta adapter | ഓരോ-സെഷൻ SQLite (`data/v2-sessions`). ട്രാൻസ്ക്രിപ്റ്റുകൾ + സന്ദേശ എണ്ണങ്ങൾ. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടോക്കണുകൾ/ചെലവ്. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ + ചിന്ത, ടോക്കൺ ഉപയോഗം. |
| **Codex** | Beta adapter | റോൾഔട്ട് JSONL `~/.codex/sessions/...`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ഉപയോഗം. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. ചാറ്റ്/കമ്പോസർ ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ. |
| **Aider** | Beta adapter | ഓരോ പ്രോജക്റ്റിനും `.aider.chat.history.md`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടോക്കൺ എണ്ണങ്ങൾ. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ആകെത്തുകകൾ. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കണുകൾ + ചെലവ്. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ഉപയോഗം. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കണുകൾ + ചെലവ്. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കണുകൾ + ചെലവ്. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. വർക്ക്ഫ്ലോ എക്സിക്യൂഷനുകൾ, നോഡ് റണ്ണുകൾ, AI Agent പ്രോംപ്റ്റുകൾ, n8n രേഖപ്പെടുത്തുന്നിടത്ത് മോഡലും ടോക്കണുകളും. |

"Beta adapter" എന്നാൽ ClawMetry ആ റൺടൈമിന്റെ യഥാർത്ഥ ഓൺ-ഡിസ്ക് ഫോർമാറ്റിനുള്ള ഒരു റീഡർ ഷിപ്പ് ചെയ്യുന്നു എന്നാണ്, ഓരോന്നും ഒരു യഥാർത്ഥ മെഷീനിലെ യഥാർത്ഥ ഇൻസ്റ്റാളിനെതിരെ നിർമ്മിച്ചതും പരിശോധിച്ചുറപ്പിച്ചതുമാണ് (`tests/fixtures/runtimes/<rt>/` കാണുക). അഡാപ്റ്ററുകൾ റീഡ്-ഒൺലി ആണ്; ഓരോന്നും അതിന്റെ റൺടൈം യഥാർത്ഥത്തിൽ ഡിസ്കിൽ എന്ത് സൂക്ഷിക്കുന്നു എന്നതിനെക്കുറിച്ച് സത്യസന്ധമാണ് (ഉദാ. PicoClaw/NanoClaw/Cursor ടോക്കൺ ചെലവ് ഡിസ്കിലേക്ക് എഴുതുന്നില്ല). ഒരു നോഡിൽ പല റൺടൈമുകൾ പ്രവർത്തിക്കുമ്പോൾ, റൺടൈം സ്വിച്ചർ ഒരു വൃത്തിയുള്ള ഡീപ്-ഡൈവിനായി സെഷനുകൾ വ്യൂ ഒരു എണ്ണത്തിലേക്ക് സ്കോപ്പ് ചെയ്യുന്നു.

## ഏത് SDK ഏജന്റിനെയും ട്രാക്ക് ചെയ്യുക — ഔട്ട്-ലൂപ്പ് ചെലവ് ആട്രിബ്യൂഷൻ

മുകളിലുള്ള റൺടൈമുകൾ എല്ലാം സെഷനുകൾ ഡിസ്കിലേക്ക് എഴുതുന്നു. നിങ്ങളുടെ സ്വന്തം **പ്രൊഡക്ഷൻ ഏജന്റ്** — OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, അല്ലെങ്കിൽ ഒരു സാധാരണ `httpx` ലൂപ്പ് ഉപയോഗിച്ച് നിങ്ങൾ നിർമ്മിച്ചത് — അങ്ങനെ ചെയ്യുന്നില്ല. `httpx`/`requests` മങ്കി-പാച്ച് ചെയ്തുകൊണ്ട് ClawMetry-യുടെ കോൺഫിഗ് ആവശ്യമില്ലാത്ത ഇന്റർസെപ്റ്റർ അതിന്റെ LLM കോളുകൾ (ചെലവ്, ടോക്കണുകൾ, ലേറ്റൻസി, പിശകുകൾ) ഇപ്പോഴും പിടിച്ചെടുക്കുന്നു:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (അല്ലെങ്കിൽ `CLAWMETRY_SOURCE=support-agent` env var) ഓരോ കോളിനെയും ഒരു **പേരുള്ള സോഴ്‌സ്** കൊണ്ട് ടാഗ് ചെയ്യുന്നു, അതിനാൽ നിങ്ങൾ പ്രവർത്തിപ്പിക്കുന്ന ഓരോ ഉൽപ്പന്നവും ഡാഷ്ബോർഡിന്റെ Overview-ലെ **🔌 Out-loop sources** കാർഡിൽ അതിന്റേതായ ഒന്നാം-ക്ലാസ്, ചെലവ്-ആട്രിബ്യൂട്ട് ചെയ്യാവുന്ന വരിയായി പ്രത്യക്ഷപ്പെടുന്നു — ഓരോ ഏജന്റിനുമുള്ള കോളുകൾ, പ്രൊവൈഡറുകൾ, ലേറ്റൻസി, പിശക് നിരക്ക്. സോഴ്‌സ് സെറ്റ് ചെയ്തിട്ടില്ലേ? കോളുകൾ ഇപ്പോഴും ട്രാക്ക് ചെയ്യപ്പെടുന്നു; കാർഡ് മാത്രം മറഞ്ഞിരിക്കും.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ഇത് റൺടൈം അഡാപ്റ്ററുകൾ നൽകുന്ന അതേ ഡാറ്റ ലെയർ ആണ് (DuckDB → ക്ലൗഡ് സ്നാപ്ഷോട്ട്), അതിനാൽ ഔട്ട്-ലൂപ്പ് സോഴ്‌സുകൾ മറ്റെല്ലാം പോലെ, E2E-എൻക്രിപ്റ്റ് ചെയ്തുകൊണ്ട്, ക്ലൗഡ് ഡാഷ്ബോർഡിലേക്ക് സിങ്ക് ചെയ്യപ്പെടുന്നു.

## OpenTelemetry — വെണ്ടർ-ന്യൂട്രൽ, നിങ്ങളുടെ ട്രെയ്സുകൾ എവിടെയും അയക്കുക

ClawMetry രണ്ട് ദിശകളിലും **OpenTelemetry** സംസാരിക്കുന്നു, **GenAI സെമാന്റിക് കൺവെൻഷനുകൾ** ഉപയോഗിച്ചുകൊണ്ട്, അതിനാൽ നിങ്ങളുടെ ഏജന്റ് ട്രെയ്സുകൾ ഒരിക്കലും ഒരൊറ്റ ടൂളിൽ ലോക്ക് ചെയ്യപ്പെടില്ല.

ഓരോ സെഷനും — LLM കോളുകൾ, ടൂളുകൾ, സബ്-ഏജന്റുകൾ, ടോക്കണുകൾ, ചെലവ് — OTLP/HTTP GenAI സ്പാനുകളായി ഏത് കളക്ടറിലേക്കും (Datadog, Grafana, Honeycomb, അല്ലെങ്കിൽ നിങ്ങളുടെ സ്വന്തം OTel Collector) **എക്സ്പോർട്ട്** ചെയ്യുക:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ഓത്ത് ഹെഡറുകളും പോൾ ഇന്റർവെലും ഐച്ഛിക env vars ആണ്:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ഇൻജസ്റ്റ്** — ബിൽറ്റ്-ഇൻ OTLP റിസീവർ `/v1/traces`, `/v1/metrics` എന്നിവിടങ്ങളിൽ മറ്റെന്തിൽ നിന്നും ട്രെയ്സുകളും മെട്രിക്സുകളും സ്വീകരിക്കുന്നു (protobuf ഇൻജസ്റ്റിനായി `pip install clawmetry[otel]`).

നിങ്ങൾക്ക് കോൺഫിഗ് ആവശ്യമില്ലാത്ത, ലോക്കൽ-ഫസ്റ്റ് ClawMetry ഡാഷ്ബോർഡും **കൂടാതെ** നിങ്ങളുടെ ടീം ഇതിനകം പ്രവർത്തിപ്പിക്കുന്ന ഏത് ബാക്കെൻഡിലും നിങ്ങളുടെ ഡാറ്റയും ലഭിക്കും — ലോക്ക്-ഇൻ ഇല്ല, രണ്ടാമത്തെ ഏജന്റ് ഇൻസ്റ്റാൾ ചെയ്യേണ്ടതില്ല.

## കോൺഫിഗറേഷൻ

മിക്കവർക്കും ഒരു കോൺഫിഗും ആവശ്യമില്ല. ClawMetry നിങ്ങളുടെ വർക്ക്‌സ്പേസ്, ലോഗുകൾ, സെഷനുകൾ, ക്രോണുകൾ എന്നിവ സ്വയമേവ കണ്ടെത്തുന്നു.

നിങ്ങൾക്ക് ഇഷ്ടാനുസൃതമാക്കേണ്ടതുണ്ടെങ്കിൽ:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

എല്ലാ ഓപ്ഷനുകളും: `clawmetry --help`

## പിന്തുണയ്ക്കുന്ന ചാനലുകൾ

നിങ്ങൾ കോൺഫിഗർ ചെയ്ത ഓരോ OpenClaw ചാനലിന്റെയും തത്സമയ പ്രവർത്തനം ClawMetry കാണിക്കുന്നു. നിങ്ങളുടെ `openclaw.json` ൽ യഥാർത്ഥത്തിൽ സജ്ജീകരിച്ചിട്ടുള്ള ചാനലുകൾ മാത്രമേ Flow ഡയഗ്രത്തിൽ പ്രത്യക്ഷപ്പെടൂ — സജ്ജീകരിക്കാത്തവ സ്വയമേവ മറയ്ക്കപ്പെടും.

ഇൻകമിംഗ്/ഔട്ട്ഗോയിംഗ് സന്ദേശ എണ്ണങ്ങളോടെയുള്ള തത്സമയ ചാറ്റ് ബബിൾ വ്യൂ കാണാൻ Flow-ലെ ഏത് ചാനൽ നോഡിലും ക്ലിക്ക് ചെയ്യുക.

| ചാനൽ | സ്റ്റാറ്റസ് | ലൈവ് പോപ്പപ്പ് | കുറിപ്പുകൾ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | സന്ദേശങ്ങൾ, സ്ഥിതിവിവരക്കണക്കുകൾ, 10s റിഫ്രഷ് |
| 💬 **iMessage** | ✅ Full | ✅ | `~/Library/Messages/chat.db` നേരിട്ട് വായിക്കുന്നു |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) വഴി |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli വഴി |
| 🟣 **Discord** | ✅ Full | ✅ | ഗിൽഡ് + ചാനൽ കണ്ടെത്തൽ |
| 🟪 **Slack** | ✅ Full | ✅ | വർക്ക്‌സ്പേസ് + ചാനൽ കണ്ടെത്തൽ |
| 🌐 **Webchat** | ✅ Full | ✅ | ബിൽറ്റ്-ഇൻ വെബ് UI സെഷനുകൾ |
| 📡 **IRC** | ✅ Full | ✅ | ടെർമിനൽ-ശൈലി ബബിൾ UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API വഴി iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API വെബ്‌ഹുക്കുകൾ വഴി |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams ബോട്ട് പ്ലഗിൻ വഴി |
| 🔷 **Mattermost** | ✅ Full | ✅ | സ്വയം-ഹോസ്റ്റ് ചെയ്ത ടീം ചാറ്റ് |
| 🟩 **Matrix** | ✅ Full | ✅ | വികേന്ദ്രീകൃതം, E2EE പിന്തുണ |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | വികേന്ദ്രീകൃത NIP-04 DM-കൾ |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC കണക്ഷൻ വഴി ചാറ്റ് |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket ഇവന്റ് സബ്സ്ക്രിപ്ഷൻ |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **സ്വയമേവ കണ്ടെത്തൽ:** ClawMetry നിങ്ങളുടെ `~/.openclaw/openclaw.json` വായിക്കുകയും നിങ്ങൾ യഥാർത്ഥത്തിൽ കോൺഫിഗർ ചെയ്ത ചാനലുകൾ മാത്രം റെൻഡർ ചെയ്യുകയും ചെയ്യുന്നു. മാനുവൽ സജ്ജീകരണം ആവശ്യമില്ല.

## Docker വിന്യാസം

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

> **കുറിപ്പ്:** Docker-ൽ പ്രവർത്തിപ്പിക്കുമ്പോൾ, ClawMetry-ക്ക് നിങ്ങളുടെ സജ്ജീകരണം സ്വയമേവ കണ്ടെത്താൻ കഴിയുന്നതിന് നിങ്ങളുടെ ഏജന്റിന്റെ ഡാറ്റ + ലോഗ് ഡയറക്ടറികൾ (ഉദാ. `~/.openclaw`, `~/.claude`, `~/.codex`) മൗണ്ട് ചെയ്യുക.

## ആവശ്യകതകൾ

- Python 3.8+
- Flask (pip വഴി സ്വയമേവ ഇൻസ്റ്റാൾ ചെയ്യപ്പെടും)
- അതേ മെഷീനിൽ ഒരു AI ഏജന്റ് റൺടൈം: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, അല്ലെങ്കിൽ n8n (അല്ലെങ്കിൽ Docker-നായി മൗണ്ട് ചെയ്ത വോള്യൂമുകൾ)
- Linux അല്ലെങ്കിൽ macOS

## NemoClaw / OpenShell പിന്തുണ

[NemoClaw](https://github.com/NVIDIA/NemoClaw) — OpenClaw ഏജന്റുകളെ സാൻഡ്ബോക്സ് ചെയ്ത OpenShell കണ്ടെയ്നറുകൾക്കുള്ളിൽ പ്രവർത്തിപ്പിക്കുന്ന NVIDIA-യുടെ എന്റർപ്രൈസ് സെക്യൂരിറ്റി റാപ്പർ — ClawMetry സ്വയമേവ കണ്ടെത്തുന്നു.

മിക്ക കേസുകളിലും അധിക കോൺഫിഗറേഷൻ ആവശ്യമില്ല. സെഷൻ ഫയലുകൾ ഹോസ്റ്റിലെ `~/.openclaw/` ലാണോ അതോ ഒരു OpenShell കണ്ടെയ്നറിനുള്ളിലാണോ എന്ന് സിങ്ക് ഡെമൺ സ്വയമേവ കണ്ടെത്തുന്നു.

### ഇത് എങ്ങനെ പ്രവർത്തിക്കുന്നു

ClawMetry NemoClaw-നെ രണ്ട് വിധത്തിൽ കണ്ടെത്തുന്നു:

1. **ബൈനറി കണ്ടെത്തൽ** — `nemoclaw` CLI ഉണ്ടോ എന്ന് പരിശോധിക്കുകയും സാൻഡ്ബോക്സ് വിവരങ്ങൾ ലഭിക്കാൻ `nemoclaw status` പ്രവർത്തിപ്പിക്കുകയും ചെയ്യുന്നു
2. **കണ്ടെയ്നർ കണ്ടെത്തൽ** — `openshell`, `nemoclaw`, അല്ലെങ്കിൽ `ghcr.io/nvidia/` ഇമേജുകൾക്കായി പ്രവർത്തിക്കുന്ന Docker കണ്ടെയ്നറുകൾ സ്കാൻ ചെയ്യുന്നു, തുടർന്ന് വോള്യൂം മൗണ്ടുകൾ വഴിയോ `docker cp` വഴിയോ സെഷനുകൾ വായിക്കുന്നു

NemoClaw കണ്ടെയ്നറുകളിൽ നിന്ന് സിങ്ക് ചെയ്ത സെഷൻ ഫയലുകൾ ക്ലൗഡ് ഡാഷ്ബോർഡിൽ `runtime=nemoclaw`, `container_id` മെറ്റാഡാറ്റ എന്നിവയോടെ ടാഗ് ചെയ്യപ്പെടുന്നു, അതിനാൽ ഒറ്റനോട്ടത്തിൽ അവയെ സ്റ്റാൻഡേർഡ് OpenClaw സെഷനുകളിൽ നിന്ന് വേർതിരിച്ചറിയാൻ കഴിയും.

### ശുപാർശ ചെയ്യുന്ന സജ്ജീകരണം: HOST-ൽ സിങ്ക് ഡെമൺ

മികച്ച അനുഭവത്തിനായി, ClawMetry-യുടെ സിങ്ക് ഡെമൺ (സാൻഡ്ബോക്സിനുള്ളിലല്ല) **ഹോസ്റ്റ് മെഷീനിൽ** പ്രവർത്തിപ്പിക്കുക. ഇത് NemoClaw നെറ്റ്‌വർക്ക് നയ നിയന്ത്രണങ്ങൾ ഒഴിവാക്കുന്നു.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

പ്രവർത്തിക്കുന്ന ഏത് OpenShell കണ്ടെയ്നറുകൾക്കുള്ളിലും സെഷനുകൾ സിങ്ക് ഡെമൺ സ്വയമേവ കണ്ടെത്തും.

### ഐച്ഛികം: വ്യക്തമായ സാൻഡ്ബോക്സ് പേര്

സ്വയമേവ കണ്ടെത്തൽ പ്രവർത്തിക്കുന്നില്ലെങ്കിൽ, ശരിയായ സാൻഡ്ബോക്സിലേക്ക് ClawMetry-യെ ചൂണ്ടിക്കാണിക്കുക:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### സാൻഡ്ബോക്സിനുള്ളിൽ പ്രവർത്തിപ്പിക്കൽ (വിപുലമായത്)

സിങ്ക് ഡെമൺ OpenShell സാൻഡ്ബോക്സിനുള്ളിൽ **തന്നെ** പ്രവർത്തിപ്പിക്കണമെങ്കിൽ, ClawMetry ഇൻജസ്റ്റ് API യിലേക്ക് എത്താൻ കഴിയുന്നതിന് നിങ്ങളുടെ NemoClaw നെറ്റ്‌വർക്ക് നയത്തിലേക്ക് ഈ എഗ്രസ് നിയമം ചേർക്കുക:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

ഇത് ഇങ്ങനെ പ്രയോഗിക്കുക:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### പോർട്ടുകളും എൻഡ്‌പോയിന്റുകളും

| എൻഡ്‌പോയിന്റ് | പോർട്ട് | പ്രോട്ടോക്കോൾ | ആവശ്യമുണ്ടോ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | അതെ (സിങ്ക് ഡെമൺ → ക്ലൗഡ്) |
| `localhost:8900` | 8900 | HTTP | അതെ (ലോക്കൽ ഡാഷ്ബോർഡ് UI) |
| Docker സോക്കറ്റ് (`/var/run/docker.sock`) | — | Unix സോക്കറ്റ് | കണ്ടെയ്നർ സെഷൻ കണ്ടെത്തലിന് |

സിങ്ക് ഡെമൺ `ingest.clawmetry.com` ലേക്ക് മാത്രമേ ഔട്ട്ബൗണ്ട് HTTPS കോളുകൾ ചെയ്യൂ. ഇൻബൗണ്ട് പോർട്ടുകൾ ആവശ്യമില്ല.

---

## ക്ലൗഡ് വിന്യാസം

SSH ടണലുകൾ, റിവേഴ്സ് പ്രോക്സി, Docker എന്നിവയ്ക്കായി **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** കാണുക.

## ടെസ്റ്റിംഗ്

ഈ പ്രോജക്റ്റ് BrowserStack ഉപയോഗിച്ച് ടെസ്റ്റ് ചെയ്യപ്പെടുന്നു.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ടെലിമെട്രി

നിങ്ങൾ ഒരു പുതിയ മെഷീനിൽ `clawmetry` CLI ആദ്യമായി പ്രവർത്തിപ്പിക്കുമ്പോൾ ClawMetry ഒരൊറ്റ അജ്ഞാത "ആദ്യ റൺ" പിംഗ് `https://app.clawmetry.com/api/install` ലേക്ക് അയക്കുന്നു. ഇൻസ്റ്റാളുകൾ എണ്ണാൻ (ഒരു OSS പ്രോജക്റ്റിനുള്ള ഞങ്ങളുടെ ഒരേയൊരു മാർക്കറ്റിംഗ് മെട്രിക്) ഞങ്ങൾ ഇത് ഉപയോഗിക്കുന്നു, കൂടാതെ ഞങ്ങളുടെ ഉപയോക്താക്കൾ ഇൻസ്റ്റാൾ ചെയ്തിട്ടുള്ള ഏജന്റ് ഫ്രെയിംവർക്കുകൾ ഏതെല്ലാമെന്ന് അറിയാനും.

**ഇൻസ്റ്റാളിന് കൃത്യമായി ഒരു POST**, ഇത് ഉൾക്കൊള്ളുന്നു:

| ഫീൽഡ് | ഉദാഹരണം | എന്തുകൊണ്ട് |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` ൽ സൂക്ഷിച്ചിരിക്കുന്ന റാൻഡം UUID | ഡീഡ്യൂപ്പ്; നിങ്ങളുടെ ഇമെയിലുമായോ api_key യുമായോ ബന്ധിപ്പിച്ചിട്ടില്ല |
| `version` | `0.12.167` | ഏതെല്ലാം പതിപ്പുകൾ ഉപയോഗത്തിലുണ്ട് |
| `os` / `os_version` | `Darwin` / `25.3.0` | പ്ലാറ്റ്‌ഫോം പിന്തുണ മുൻഗണനകൾ |
| `python` | `3.11.15` | Python പതിപ്പ് പിന്തുണ മാട്രിക്സ് |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ഇനി ഏത് ഏജന്റുകളുമായി ഞങ്ങൾ ഇന്റഗ്രേറ്റ് ചെയ്യണം |
| `is_ci` / `ci_provider` | `true` / `github_actions` | മനുഷ്യ ഇൻസ്റ്റാളുകളെ CI ശബ്ദത്തിൽ നിന്ന് വേർതിരിക്കുന്നു |

**ഞങ്ങൾ അയക്കാത്തത്**: IP (ക്ലൗഡ് അഭ്യർത്ഥനയിൽ നിന്ന് സെർവർ-സൈഡിൽ രാജ്യ കോഡ് നിർവ്വചിക്കുന്നു, തുടർന്ന് IP ഒഴിവാക്കുന്നു), ഹോസ്റ്റ്നാമം, യൂസർനെയിം, വർക്ക്‌സ്പേസ്
പാത്ത്, ഫയൽ ഉള്ളടക്കങ്ങൾ, നിങ്ങളുടെ api_key, നിങ്ങളുടെ ഇമെയിൽ, PII അല്ലെങ്കിൽ
വർക്ക്‌സ്പേസ്-നിർദ്ദിഷ്ടമായ ഒന്നും. വയർ പേലോഡ് ഓഡിറ്റ് ചെയ്യാവുന്നതാണ്
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) ൽ.

**ഒഴിവാകുക** (ഇവയിൽ ഏതെങ്കിലും ഒന്ന് ഇത് ശാശ്വതമായി പ്രവർത്തനരഹിതമാക്കുന്നു):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ഒരു നെറ്റ്‌വർക്ക് പരാജയം ഇവിടെ ഒരിക്കലും `clawmetry` പ്രവർത്തിക്കുന്നതിൽ നിന്ന് തടയില്ല — പിംഗ്
3 സെക്കൻഡ് ടൈംഔട്ടോടെ ഒരു ഡെമൺ ത്രെഡിൽ ഫയർ-ആൻഡ്-ഫോർഗെറ്റ് ആണ്.

## സ്റ്റാർ ചരിത്രം

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
  <sub>നിർമ്മിച്ചത് <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ഇക്കോസിസ്റ്റത്തിന്റെ ഭാഗം</sub>
</p>
