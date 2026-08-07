<!-- i18n-src:7cfb63716507 -->
> മലയാളം translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**നിങ്ങളുടെ ഏജന്റ് ചിന്തിക്കുന്നത് കാണൂ.** **14 AI ഏജന്റ് റൺടൈമുകൾക്കുള്ള** തത്സമയ നിരീക്ഷണം: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex കൂടാതെ 10 എണ്ണം കൂടി. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരൊറ്റ ഡാഷ്ബോർഡ്.

> 🌐 **ഇത് വായിക്കുക:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [കൂടുതൽ →](docs/i18n/)

ഒരു കമാൻഡ്. കോൺഫിഗ് ഒന്നും വേണ്ട. എല്ലാം സ്വയമേവ കണ്ടെത്തുന്നു.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** എന്നതിൽ തുറക്കും, അത്രമാത്രം.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ഏജന്റ് റൺടൈമുകളുമായി പ്രവർത്തിക്കുന്നു

ClawMetry ആരംഭിച്ചത് OpenClaw-നുള്ള നിരീക്ഷണമായിട്ടാണ്, ഇപ്പോൾ അത് നിങ്ങളുടെ **മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റും** ഒരൊറ്റ ഡാഷ്ബോർഡിൽ അളക്കുന്നു, നിങ്ങളുടെ മെഷീനിലുള്ള ഓരോ റൺടൈമും സ്വയമേവ കണ്ടെത്തിക്കൊണ്ട്:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw, NemoClaw എന്നിവ ഓപ്പൺ സോഴ്‌സ് ആപ്പിൽ സൗജന്യമാണ്; മറ്റ് റൺടൈമുകൾ ClawMetry Cloud അല്ലെങ്കിൽ സ്വയം-ഹോസ്റ്റ് ചെയ്ത Pro ലൈസൻസ് ഉപയോഗിച്ച് സജീവമാകും. ഹെഡറിൽ നിന്ന് റൺടൈമുകൾ മാറ്റുക, ഓരോ ടാബും - ചെലവ്, ടോക്കണുകൾ, ടൂളുകൾ, ട്രെയ്‌സുകൾ - ആ റൺടൈമിലേക്ക് വീണ്ടും സ്കോപ്പ് ചെയ്യപ്പെടും. കൃത്യമായ സൗജന്യ/പണമടച്ചുള്ള വിഭജനം, ടയർ മാട്രിക്സ്, `/api/entitlement` ഘടന, `clawmetry license` CLI എന്നിവയ്ക്കായി **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** കാണുക.

## നിങ്ങൾക്ക് ലഭിക്കുന്നത്

- **Flow** — ചാനലുകൾ, ബ്രെയിൻ, ടൂളുകൾ എന്നിവയിലൂടെ സന്ദേശങ്ങൾ ഒഴുകുന്നത് കാണിക്കുന്ന തത്സമയ ആനിമേറ്റഡ് ഡയഗ്രം
- **Overview** — ഹെൽത്ത് ചെക്കുകൾ, ആക്ടിവിറ്റി ഹീറ്റ്മാപ്പ്, സെഷൻ എണ്ണം, മോഡൽ വിവരങ്ങൾ
- **Usage** — ദിവസേന/ആഴ്ചതോറും/മാസംതോറും വേർതിരിവുകളോടെ ടോക്കൺ, ചെലവ് ട്രാക്കിംഗ്
- **Sessions** — മോഡൽ, ടോക്കണുകൾ, അവസാന ആക്ടിവിറ്റി എന്നിവയോടെ സജീവ ഏജന്റ് സെഷനുകൾ
- **Crons** — സ്റ്റാറ്റസ്, അടുത്ത റൺ, ദൈർഘ്യം എന്നിവയോടെ ഷെഡ്യൂൾ ചെയ്ത ജോലികൾ
- **Logs** — കളർ-കോഡഡ് തത്സമയ ലോഗ് സ്ട്രീമിംഗ്
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ദിവസേനയുള്ള കുറിപ്പുകൾ ബ്രൗസ് ചെയ്യുക
- **Transcripts** — സെഷൻ ചരിത്രങ്ങൾ വായിക്കാനുള്ള ചാറ്റ്-ബബിൾ UI
- **Alerts** — ബജറ്റ് പരിധികൾ, പിശക്-നിരക്ക് ട്രിഗറുകൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ കണ്ടെത്തൽ; Slack, Discord, PagerDuty, Telegram, Email എന്നിവയിലേക്ക് റൂട്ട് ചെയ്യുന്നു
- **Approvals** — വിനാശകരമായ ഡിലീറ്റുകൾ, ഫോഴ്‌സ് പുഷുകൾ, DB മ്യൂട്ടേഷനുകൾ, sudo, പാക്കേജ് ഇൻസ്റ്റാളുകൾ, നെറ്റ്‌വർക്ക് കോളുകൾ എന്നിവ ഒറ്റ-ക്ലിക്ക് അംഗീകാരത്തിന് പിന്നിൽ തടയുക

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

### 🚨 Alerts — ബജറ്റ് പരിധികൾ, പിശക്-നിരക്ക് ട്രിഗറുകൾ, Slack / Discord / PagerDuty / Email എന്നിവയിലേക്കുള്ള webhooks
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — അപകടകരമായ ടൂൾ കോളുകൾ മാനുവൽ അംഗീകാരത്തിന് പിന്നിൽ തടയുക; പോളിസി-പിന്തുണയുള്ള സംരക്ഷണ നിയമങ്ങൾ
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-നുള്ള എക്സിക്യൂഷനു-മുമ്പുള്ള ബ്ലോക്കിംഗ്** — ഒരു കമാൻഡ്
പൊരുത്തപ്പെടുന്ന ടൂൾ കോളുകളെ അവ *പ്രവർത്തിക്കുന്നതിന് മുമ്പ്* താൽക്കാലികമായി
നിർത്തുകയും നിങ്ങളുടെ തീരുമാനത്തിനായി കാത്തിരിക്കുകയും ചെയ്യുന്ന ഒരു PreToolUse
ഹുക്ക് ഇൻസ്റ്റാൾ ചെയ്യുന്നു ([cloud push notifications](https://app.clawmetry.com/push)
പ്രവർത്തനക്ഷമമാക്കിയാൽ നിങ്ങളുടെ ഫോണിൽ നിന്ന് ഒറ്റ ടാപ്പിൽ):

```bash
clawmetry hooks install     # ~/.claude/settings.json എഴുതുന്നു (ഇഡംപൊട്ടന്റ്)
clawmetry hooks status      # എന്താണ് വയർ ചെയ്തിരിക്കുന്നത് + എത്ര പോളിസികൾ സജീവമാണ്
clawmetry hooks uninstall   # ClawMetry-യുടെ എൻട്രികൾ മാത്രം നീക്കം ചെയ്യുന്നു
```

ഒരു deny ആ ഒരു ടൂൾ കോൾ മാത്രമേ തടയൂ — ഏജന്റ് അതിന്റെ സെഷൻ നിലനിർത്തുകയും
മറ്റൊരു സമീപനം പരീക്ഷിക്കുകയും ചെയ്യാം. നിങ്ങളുടെ ഫോണിൽ അംഗീകരിക്കുന്നത്
Claude Code-ന്റെ സ്വന്തം അനുമതി പ്രോംപ്റ്റിനെ ഒഴിവാക്കുന്നു (നിങ്ങൾ ഇതിനകം
ഉത്തരം നൽകിക്കഴിഞ്ഞു). പൊരുത്തപ്പെടാത്ത ടൂളുകൾക്ക് ~40ms ചെലവാകുകയും
Claude Code-ന്റെ സാധാരണ അനുമതി ഫ്ലോയിലേക്ക് വീഴുകയും ചെയ്യും. Claude Code
തന്നെ നിങ്ങൾക്കായി കാത്തിരിക്കുമ്പോഴും നിങ്ങൾക്ക് ഫോൺ പുഷ് ലഭിക്കും
(`permission_prompt` / `idle_prompt` അറിയിപ്പുകൾ).

## ഇൻസ്റ്റാൾ ചെയ്യുക

**ഒറ്റ-വരി (ശുപാർശ ചെയ്യുന്നത്):**
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

v2 React ആപ്പ് `frontend/`-ൽ സ്ഥിതി ചെയ്യുന്നു, v2 പ്രവർത്തനക്ഷമമാക്കി
Flask സെർവർ ആരംഭിക്കുമ്പോൾ അത് `/v2`-ൽ സെർവ് ചെയ്യപ്പെടും.

ഡെവലപ് ചെയ്യുമ്പോൾ രണ്ട് ടെർമിനലുകൾ ഉപയോഗിക്കുക:

```bash
# Terminal 1: :8900-ൽ Flask API/സെർവർ
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: :5173-ൽ Vite dev സെർവർ
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` തുറക്കുക. Vite `/api` അഭ്യർത്ഥനകൾ
`http://localhost:8900`-ലേക്ക് പ്രോക്സി ചെയ്യുന്നു, അതിനാൽ അധിക CORS
സെറ്റപ്പ് ഇല്ലാതെ React ആപ്പിന് ലോക്കൽ Flask സെർവറുമായി സംസാരിക്കാൻ കഴിയും.

Python പാക്കേജിനൊപ്പം ഷിപ്പ് ചെയ്യുന്ന ബണ്ടിൽ ബിൽഡ് ചെയ്യാൻ:

```bash
cd frontend
npm run build
```

പ്രൊഡക്ഷൻ ബണ്ടിൽ `clawmetry/static/v2/dist/`-ൽ എഴുതപ്പെടും.

## റൺടൈം / ഏജന്റ് അനുയോജ്യത

ClawMetry OpenClaw മാത്രമല്ല, നിരവധി AI-ഏജന്റ് റൺടൈമുകൾ നിരീക്ഷിക്കുന്നു. OpenClaw അല്ലാത്ത ഓരോ റൺടൈമും അതിന്റെ നേറ്റീവ് സെഷൻ ഫോർമാറ്റ് ClawMetry-യുടെ ഏകീകൃത ഘടനകളിലേക്ക് പരിവർത്തനം ചെയ്യുന്ന ഒരു സമർപ്പിത റീഡർ അഡാപ്റ്റർ ഷിപ്പ് ചെയ്യുന്നു; ഡെമൺ അവയെ അതേ DuckDB സ്റ്റോർ + ക്ലൗഡ് സ്നാപ്ഷോട്ടിലേക്ക് റൺടൈം ടാഗ് ചെയ്ത് ഇൻജെസ്റ്റ് ചെയ്യുന്നു, ഒന്നിലധികം സാന്നിധ്യമുള്ളപ്പോൾ Session replay ടാബ് ഒരു **റൺടൈം സ്വിച്ചർ** കാണിക്കുന്നു. പൂർണ്ണ മാട്രിക്സിനും റൺടൈമുകൾ ചേർക്കുന്നതിനുള്ള ഗൈഡിനും [`docs/compatibility.md`](docs/compatibility.md) കാണുക, കൂടാതെ OpenClaw-ഫാമിലി പ്രൈമറിനായി [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) കാണുക.

[Perplexity-യുടെ numbat](https://github.com/perplexityai/numbat) ഏജന്റ്-സെക്യൂരിറ്റി ടൂൾ പ്രവർത്തിപ്പിക്കുന്നുണ്ടോ? ClawMetry അതിന്റെ കണ്ടെത്തലുകളും എൻഫോഴ്‌സ്മെന്റ് തീരുമാനങ്ങളും ബോക്സിന് പുറത്ത് ഇൻജെസ്റ്റ് ചെയ്യുന്നു — [`docs/NUMBAT.md`](docs/NUMBAT.md) കാണുക.

| റൺടൈം / ഏജന്റ് | സ്റ്റാറ്റസ് | കുറിപ്പുകൾ |
|---|---|---|
| **OpenClaw** | നേറ്റീവ് | റഫറൻസ് റൺടൈം, സ്വയമേവ കണ്ടെത്തുന്നു |
| **PicoClaw** | ബീറ്റ അഡാപ്റ്റർ | ഫ്ലാറ്റ് `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ. |
| **NanoClaw** | ബീറ്റ അഡാപ്റ്റർ | ഓരോ-സെഷന് SQLite (`data/v2-sessions`). ട്രാൻസ്ക്രിപ്റ്റുകൾ + സന്ദേശ എണ്ണങ്ങൾ. |
| **Hermes** | ബീറ്റ അഡാപ്റ്റർ | SQLite `~/.hermes/state.db`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടോക്കണുകൾ/ചെലവ്. |
| **Claude Code** | ബീറ്റ അഡാപ്റ്റർ | JSONL `~/.claude/projects/.../<id>.jsonl`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ + ചിന്ത, ടോക്കൺ ഉപയോഗം. |
| **Codex** | ബീറ്റ അഡാപ്റ്റർ | Rollout JSONL `~/.codex/sessions/...`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ഉപയോഗം. |
| **Cursor** | ബീറ്റ അഡാപ്റ്റർ | SQLite `state.vscdb`. ചാറ്റ്/കമ്പോസർ ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ. |
| **Aider** | ബീറ്റ അഡാപ്റ്റർ | ഓരോ-പ്രോജക്ടിനും `.aider.chat.history.md`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടോക്കൺ എണ്ണങ്ങൾ. |
| **Goose** | ബീറ്റ അഡാപ്റ്റർ | SQLite `~/.local/share/goose`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ആകെത്തുകകൾ. |
| **opencode** | ബീറ്റ അഡാപ്റ്റർ | SQLite `~/.local/share/opencode`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കണുകൾ + ചെലവ്. |
| **Qwen Code** | ബീറ്റ അഡാപ്റ്റർ | JSONL `~/.qwen/projects/.../chats`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ഉപയോഗം. |
| **Pi** | ബീറ്റ അഡാപ്റ്റർ | JSONL `~/.pi/agent/sessions`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കണുകൾ + ചെലവ്. |
| **Deep Agents** | ബീറ്റ അഡാപ്റ്റർ | SQLite `~/.deepagents/.state/sessions.db`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കണുകൾ + ചെലവ്. |
| **n8n** | ബീറ്റ അഡാപ്റ്റർ | SQLite `~/.n8n/database.sqlite`. വർക്ക്ഫ്ലോ എക്സിക്യൂഷനുകൾ, നോഡ് റണ്ണുകൾ, AI Agent പ്രോംപ്റ്റുകൾ, n8n രേഖപ്പെടുത്തുന്നിടത്ത് മോഡൽ + ടോക്കണുകൾ. |
| **Antigravity** | ബീറ്റ അഡാപ്റ്റർ | `~/.gemini/<flavor>/brain/`-ന് കീഴിലുള്ള Brain JSONL. സംഭാഷണങ്ങൾ, ടൂൾ സ്റ്റെപ്പുകൾ, ചിന്ത, ഓരോ-ജനറേഷനിലുമുള്ള Gemini ടോക്കൺ വിഭജനം + ചെലവ്, ബാക്ക്ഗ്രൗണ്ട്-ജനറേഷൻ ബേൺ. |
| **GitHub Copilot** | ബീറ്റ അഡാപ്റ്റർ | Copilot CLI `events.jsonl` `~/.copilot/session-state/`-ന് കീഴിൽ + ഓരോ-കോളിനുമുള്ള ഉപയോഗ ലെഡ്ജറായ `session-store.db`. സംഭാഷണങ്ങൾ, ടൂൾ കോളുകൾ, മോഡൽ റൂട്ടിംഗ്, കാഷെ-ബോധമുള്ള ടോക്കൺ വിഭജനം, വെണ്ടർ-ബിൽ ചെയ്ത AI-ക്രെഡിറ്റ് ചെലവ്. |
| **Grok** | ബീറ്റ അഡാപ്റ്റർ | xAI Grok Build CLI (`~/.grok/bin/grok`-ന് കീഴിലുള്ള Rust ബൈനറി): ഗ്ലോബൽ ഇവന്റ് ലോഗ് `~/.grok/logs/unified.jsonl` + ഓരോ-സെഷനുമുള്ള `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. സംഭാഷണങ്ങൾ, ഓരോ-ടേണിലുമുള്ള ടോക്കൺ വിഭജനം, മോഡൽ റൂട്ടിംഗ്, കൂടാതെ നിങ്ങളുടെ മെഷീനിൽ നിന്ന് പുറത്തുപോയത് കാണാൻ `~/.grok/upload_queue/`-ൽ സ്റ്റേജ് ചെയ്ത CLI-യുടെ ഔട്ട്ബൗണ്ട് റിപ്പോ പേലോഡ്. |

"ബീറ്റ അഡാപ്റ്റർ" എന്നാൽ ClawMetry ആ റൺടൈമിന്റെ യഥാർത്ഥ ഓൺ-ഡിസ്ക് ഫോർമാറ്റിനുള്ള ഒരു റീഡർ ഷിപ്പ് ചെയ്യുന്നു എന്നാണ്, ഓരോന്നും ഒരു യഥാർത്ഥ മെഷീനിലെ യഥാർത്ഥ ഇൻസ്റ്റാളിനെതിരെ നിർമ്മിച്ച് + സ്ഥിരീകരിച്ചത് (`tests/fixtures/runtimes/<rt>/` കാണുക). അഡാപ്റ്ററുകൾ റീഡ്-ഒൺലി ആണ്; ഓരോന്നും അതിന്റെ റൺടൈം യഥാർത്ഥത്തിൽ ഡിസ്കിൽ സൂക്ഷിക്കുന്നതിനെക്കുറിച്ച് സത്യസന്ധമാണ് (ഉദാ. PicoClaw/NanoClaw/Cursor ടോക്കൺ ചെലവ് ഡിസ്കിലേക്ക് എഴുതുന്നില്ല). ഒരു നോഡിൽ പല റൺടൈമുകൾ പ്രവർത്തിക്കുമ്പോൾ, റൺടൈം സ്വിച്ചർ ഒരു ക്ലീൻ ഡീപ്-ഡൈവിനായി സെഷനുകൾ വ്യൂ ഒന്നിലേക്ക് സ്കോപ്പ് ചെയ്യുന്നു.

## ഏത് SDK ഏജന്റും ട്രാക്ക് ചെയ്യുക — ഔട്ട്-ലൂപ്പ് ചെലവ് ആട്രിബ്യൂഷൻ

മുകളിലുള്ള റൺടൈമുകൾ എല്ലാം സെഷനുകൾ ഡിസ്കിലേക്ക് എഴുതുന്നു. നിങ്ങൾ OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, അല്ലെങ്കിൽ ഒരു സാധാരണ `httpx` ലൂപ്പിൽ നിർമ്മിച്ച നിങ്ങളുടെ സ്വന്തം **പ്രൊഡക്ഷൻ ഏജന്റ്** അങ്ങനെ ചെയ്യുന്നില്ല. ClawMetry-യുടെ സീറോ-കോൺഫിഗ് ഇന്റർസെപ്റ്റർ `httpx`/`requests`-നെ മങ്കി-പാച്ച് ചെയ്തുകൊണ്ട് അതിന്റെ LLM കോളുകൾ (ചെലവ്, ടോക്കണുകൾ, ലേറ്റൻസി, പിശകുകൾ) ഇപ്പോഴും പിടിക്കുന്നു:

```python
import clawmetry.track            # ഇന്റർസെപ്റ്റർ സജീവമാക്കുക
clawmetry.track.set_source("support-agent")   # ഈ ഉൽപ്പന്നത്തിന് പേരിടുക

# ...നിങ്ങളുടെ ഏജന്റ് സാധാരണപോലെ പ്രവർത്തിക്കുന്നു; ഇപ്പോൾ ഓരോ LLM കോളും ട്രാക്ക് + ആട്രിബ്യൂട്ട് ചെയ്യപ്പെടുന്നു.
```

`set_source()` (അല്ലെങ്കിൽ `CLAWMETRY_SOURCE=support-agent` env വേരിയബിൾ) ഓരോ കോളും ഒരു **പേരുള്ള സോഴ്‌സ്** ഉപയോഗിച്ച് ടാഗ് ചെയ്യുന്നു, അതിനാൽ നിങ്ങൾ പ്രവർത്തിപ്പിക്കുന്ന ഓരോ ഉൽപ്പന്നവും Overview-യുടെ **🔌 Out-loop sources** കാർഡിൽ ഡാഷ്ബോർഡിൽ അതിന്റേതായ ഫസ്റ്റ്-ക്ലാസ്, ചെലവ്-ആട്രിബ്യൂട്ട് ചെയ്യാവുന്ന വരിയായി കാണിക്കുന്നു — ഓരോ ഏജന്റിനും കോളുകൾ, പ്രൊവൈഡറുകൾ, ലേറ്റൻസി, പിശക് നിരക്ക്. സോഴ്‌സ് സെറ്റ് ചെയ്തിട്ടില്ലേ? കോളുകൾ ഇപ്പോഴും ട്രാക്ക് ചെയ്യപ്പെടുന്നു; കാർഡ് മറഞ്ഞിരിക്കും എന്ന് മാത്രം.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ഇത് റൺടൈം അഡാപ്റ്ററുകൾ ഫീഡ് ചെയ്യുന്ന അതേ ഡാറ്റ ലെയർ ആണ് (DuckDB → ക്ലൗഡ് സ്നാപ്ഷോട്ട്), അതിനാൽ ഔട്ട്-ലൂപ്പ് സോഴ്‌സുകൾ മറ്റെല്ലാം പോലെ ക്ലൗഡ് ഡാഷ്ബോർഡിലേക്ക് സിങ്ക് ചെയ്യുന്നു, E2E-എൻക്രിപ്റ്റഡ്.

## OpenTelemetry — വെണ്ടർ-ന്യൂട്രൽ, നിങ്ങളുടെ ട്രെയ്‌സുകൾ എവിടെയും അയക്കുക

ClawMetry രണ്ട് ദിശകളിലും **OpenTelemetry** സംസാരിക്കുന്നു, **GenAI സെമാന്റിക് കൺവെൻഷനുകൾ** ഉപയോഗിച്ച്, അതിനാൽ നിങ്ങളുടെ ഏജന്റ് ട്രെയ്‌സുകൾ ഒരിക്കലും ഒരു ടൂളിൽ ലോക്ക് ചെയ്യപ്പെടില്ല.

ഓരോ സെഷനും — LLM കോളുകൾ, ടൂളുകൾ, സബ്-ഏജന്റുകൾ, ടോക്കണുകൾ, ചെലവ് — ഏത് കളക്ടറിലേക്കും (Datadog, Grafana, Honeycomb, അല്ലെങ്കിൽ നിങ്ങളുടെ സ്വന്തം OTel Collector) OTLP/HTTP GenAI സ്പാനുകളായി **എക്സ്പോർട്ട്** ചെയ്യുക:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# തുല്യമായി:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth ഹെഡറുകളും പോൾ ഇന്റർവലും ഓപ്ഷണൽ env വേരിയബിളുകളാണ്:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # അധിക HTTP ഹെഡറുകൾ
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # സെക്കൻഡുകൾ (സ്ഥിരസ്ഥിതി 60)
```

**ഇൻജെസ്റ്റ്** — ബിൽറ്റ്-ഇൻ OTLP റിസീവർ `/v1/traces`, `/v1/metrics` എന്നിവയിൽ മറ്റെന്തിൽ നിന്നും ട്രെയ്‌സുകളും മെട്രിക്സുകളും സ്വീകരിക്കുന്നു (protobuf ഇൻജെസ്റ്റിന് `pip install clawmetry[otel]`).

നിങ്ങൾക്ക് സീറോ-കോൺഫിഗ്, ലോക്കൽ-ഫസ്റ്റ് ClawMetry ഡാഷ്ബോർഡും **കൂടാതെ** നിങ്ങളുടെ ടീം ഇതിനകം പ്രവർത്തിപ്പിക്കുന്ന ഏത് ബാക്കെൻഡിലും നിങ്ങളുടെ ഡാറ്റയും ലഭിക്കും — ലോക്ക്-ഇൻ ഇല്ല, രണ്ടാമത്തെ ഏജന്റ് ഇൻസ്റ്റാൾ ചെയ്യേണ്ടതില്ല.

## കോൺഫിഗറേഷൻ

മിക്ക ആളുകൾക്കും കോൺഫിഗ് ഒന്നും ആവശ്യമില്ല. ClawMetry നിങ്ങളുടെ വർക്ക്‌സ്പേസ്, ലോഗുകൾ, സെഷനുകൾ, ക്രോണുകൾ എന്നിവ സ്വയമേവ കണ്ടെത്തുന്നു.

നിങ്ങൾക്ക് ഇഷ്ടാനുസൃതമാക്കണമെങ്കിൽ:

```bash
clawmetry --port 9000              # ഇഷ്ടാനുസൃത പോർട്ട് (സ്ഥിരസ്ഥിതി: 8900)
clawmetry --host 127.0.0.1         # ലോക്കൽഹോസ്റ്റിൽ മാത്രം ബൈൻഡ് ചെയ്യുക
clawmetry --workspace ~/mybot      # ഇഷ്ടാനുസൃത വർക്ക്‌സ്പേസ് പാത്ത്
clawmetry --name "Alice"           # Flow വിഷ്വലൈസേഷനിൽ നിങ്ങളുടെ പേര്
```

എല്ലാ ഓപ്ഷനുകളും: `clawmetry --help`

## പിന്തുണയ്ക്കുന്ന ചാനലുകൾ

നിങ്ങൾ കോൺഫിഗർ ചെയ്ത എല്ലാ OpenClaw ചാനലിനും ClawMetry തത്സമയ ആക്ടിവിറ്റി കാണിക്കുന്നു. നിങ്ങളുടെ `openclaw.json`-ൽ യഥാർത്ഥത്തിൽ സെറ്റപ്പ് ചെയ്ത ചാനലുകൾ മാത്രമേ Flow ഡയഗ്രമിൽ ദൃശ്യമാകൂ — കോൺഫിഗർ ചെയ്യാത്തവ സ്വയമേവ മറയ്ക്കപ്പെടും.

ഇൻകമിംഗ്/ഔട്ട്ഗോയിംഗ് സന്ദേശ എണ്ണങ്ങളോടെ ഒരു തത്സമയ ചാറ്റ് ബബിൾ വ്യൂ കാണാൻ Flow-ലെ ഏത് ചാനൽ നോഡിലും ക്ലിക്ക് ചെയ്യുക.

| ചാനൽ | സ്റ്റാറ്റസ് | ലൈവ് പോപ്പപ്പ് | കുറിപ്പുകൾ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ പൂർണ്ണം | ✅ | സന്ദേശങ്ങൾ, സ്ഥിതിവിവരക്കണക്കുകൾ, 10s റിഫ്രഷ് |
| 💬 **iMessage** | ✅ പൂർണ്ണം | ✅ | `~/Library/Messages/chat.db` നേരിട്ട് വായിക്കുന്നു |
| 💚 **WhatsApp** | ✅ പൂർണ്ണം | ✅ | WhatsApp Web (Baileys) വഴി |
| 🔵 **Signal** | ✅ പൂർണ്ണം | ✅ | signal-cli വഴി |
| 🟣 **Discord** | ✅ പൂർണ്ണം | ✅ | Guild + ചാനൽ കണ്ടെത്തൽ |
| 🟪 **Slack** | ✅ പൂർണ്ണം | ✅ | Workspace + ചാനൽ കണ്ടെത്തൽ |
| 🌐 **Webchat** | ✅ പൂർണ്ണം | ✅ | ബിൽറ്റ്-ഇൻ വെബ് UI സെഷനുകൾ |
| 📡 **IRC** | ✅ പൂർണ്ണം | ✅ | ടെർമിനൽ-ശൈലി ബബിൾ UI |
| 🍏 **BlueBubbles** | ✅ പൂർണ്ണം | ✅ | BlueBubbles REST API വഴി iMessage |
| 🔵 **Google Chat** | ✅ പൂർണ്ണം | ✅ | Chat API webhooks വഴി |
| 🟣 **MS Teams** | ✅ പൂർണ്ണം | ✅ | Teams bot പ്ലഗിൻ വഴി |
| 🔷 **Mattermost** | ✅ പൂർണ്ണം | ✅ | സ്വയം-ഹോസ്റ്റ് ചെയ്ത ടീം ചാറ്റ് |
| 🟩 **Matrix** | ✅ പൂർണ്ണം | ✅ | വികേന്ദ്രീകൃതം, E2EE പിന്തുണ |
| 🟢 **LINE** | ✅ പൂർണ്ണം | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ പൂർണ്ണം | ✅ | വികേന്ദ്രീകൃത NIP-04 DMs |
| 🟣 **Twitch** | ✅ പൂർണ്ണം | ✅ | IRC കണക്ഷൻ വഴി ചാറ്റ് |
| 🔷 **Feishu/Lark** | ✅ പൂർണ്ണം | ✅ | WebSocket ഇവന്റ് സബ്സ്ക്രിപ്ഷൻ |
| 🔵 **Zalo** | ✅ പൂർണ്ണം | ✅ | Zalo Bot API |

> **സ്വയമേവ കണ്ടെത്തൽ:** ClawMetry നിങ്ങളുടെ `~/.openclaw/openclaw.json` വായിക്കുകയും നിങ്ങൾ യഥാർത്ഥത്തിൽ കോൺഫിഗർ ചെയ്ത ചാനലുകൾ മാത്രം റെൻഡർ ചെയ്യുകയും ചെയ്യുന്നു. മാനുവൽ സെറ്റപ്പ് ആവശ്യമില്ല.

## Docker ഡിപ്ലോയ്‌മെന്റ്

ClawMetry ഒരു കണ്ടെയ്നറിൽ പ്രവർത്തിപ്പിക്കണോ? കുഴപ്പമില്ല! 🐳

**Docker ഉപയോഗിച്ച് ദ്രുത ആരംഭം:**

```bash
# ഇമേജ് ബിൽഡ് ചെയ്യുക
docker build -t clawmetry .

# സ്ഥിരസ്ഥിതി ക്രമീകരണങ്ങളോടെ പ്രവർത്തിപ്പിക്കുക
docker run -p 8900:8900 clawmetry

# അല്ലെങ്കിൽ നിങ്ങളുടെ ഏജന്റിന്റെ ഡാറ്റ ഡയറക്ടറി മൗണ്ട് ചെയ്യുക (കാണിക്കുന്നത്: OpenClaw-യുടെ ~/.openclaw)
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

> **കുറിപ്പ്:** Docker-ൽ പ്രവർത്തിപ്പിക്കുമ്പോൾ, ClawMetry-ക്ക് നിങ്ങളുടെ സെറ്റപ്പ് സ്വയമേവ കണ്ടെത്താൻ കഴിയുന്ന വിധം നിങ്ങളുടെ ഏജന്റിന്റെ ഡാറ്റ + ലോഗ് ഡയറക്ടറികൾ (ഉദാ. `~/.openclaw`, `~/.claude`, `~/.codex`) മൗണ്ട് ചെയ്യുക.

## ആവശ്യകതകൾ

- Python 3.8+
- Flask (pip വഴി സ്വയമേവ ഇൻസ്റ്റാൾ ചെയ്യപ്പെടുന്നു)
- അതേ മെഷീനിൽ ഒരു AI ഏജന്റ് റൺടൈം: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, അല്ലെങ്കിൽ QM (അല്ലെങ്കിൽ Docker-നായി മൗണ്ട് ചെയ്ത വോള്യങ്ങൾ)
- Linux അല്ലെങ്കിൽ macOS

## NemoClaw / OpenShell പിന്തുണ

ClawMetry സ്വയമേവ [NemoClaw](https://github.com/NVIDIA/NemoClaw) — സാൻഡ്ബോക്സ്ഡ് OpenShell കണ്ടെയ്നറുകൾക്കുള്ളിൽ ഏജന്റുകൾ പ്രവർത്തിപ്പിക്കുന്ന NVIDIA-യുടെ OpenClaw-നുള്ള എന്റർപ്രൈസ് സെക്യൂരിറ്റി റാപ്പർ — കണ്ടെത്തുന്നു.

മിക്ക കേസുകളിലും അധിക കോൺഫിഗറേഷൻ ആവശ്യമില്ല. സെഷൻ ഫയലുകൾ ഹോസ്റ്റിലെ `~/.openclaw/`-ൽ ആയാലും OpenShell കണ്ടെയ്നറിനുള്ളിൽ ആയാലും സിങ്ക് ഡെമൺ അവ സ്വയമേവ കണ്ടെത്തുന്നു.

### ഇത് എങ്ങനെ പ്രവർത്തിക്കുന്നു

ClawMetry രണ്ട് വിധത്തിൽ NemoClaw കണ്ടെത്തുന്നു:

1. **ബൈനറി കണ്ടെത്തൽ** — `nemoclaw` CLI ഉണ്ടോ എന്ന് പരിശോധിക്കുകയും സാൻഡ്ബോക്സ് വിവരങ്ങൾ ലഭിക്കാൻ `nemoclaw status` പ്രവർത്തിപ്പിക്കുകയും ചെയ്യുന്നു
2. **കണ്ടെയ്നർ കണ്ടെത്തൽ** — `openshell`, `nemoclaw`, അല്ലെങ്കിൽ `ghcr.io/nvidia/` ഇമേജുകൾക്കായി പ്രവർത്തിക്കുന്ന Docker കണ്ടെയ്നറുകൾ സ്കാൻ ചെയ്യുന്നു, തുടർന്ന് വോള്യം മൗണ്ടുകൾ അല്ലെങ്കിൽ `docker cp` വഴി സെഷനുകൾ വായിക്കുന്നു

NemoClaw കണ്ടെയ്നറുകളിൽ നിന്ന് സിങ്ക് ചെയ്ത സെഷൻ ഫയലുകൾ ക്ലൗഡ് ഡാഷ്ബോർഡിൽ `runtime=nemoclaw`, `container_id` മെറ്റാഡാറ്റ എന്നിവയോടെ ടാഗ് ചെയ്യപ്പെടുന്നു, അതിനാൽ ഒറ്റനോട്ടത്തിൽ അവയെ സ്റ്റാൻഡേർഡ് OpenClaw സെഷനുകളിൽ നിന്ന് വേർതിരിച്ചറിയാൻ കഴിയും.

### ശുപാർശ ചെയ്യുന്ന സെറ്റപ്പ്: HOST-ൽ സിങ്ക് ഡെമൺ

മികച്ച അനുഭവത്തിന്, ClawMetry-യുടെ സിങ്ക് ഡെമൺ **ഹോസ്റ്റ് മെഷീനിൽ** (സാൻഡ്ബോക്സിനുള്ളിൽ അല്ല) പ്രവർത്തിപ്പിക്കുക. ഇത് NemoClaw നെറ്റ്‌വർക്ക് പോളിസി നിയന്ത്രണങ്ങൾ ഒഴിവാക്കുന്നു.

```bash
# ഹോസ്റ്റിൽ (സാൻഡ്ബോക്സിന് പുറത്ത്)
pip install clawmetry
clawmetry connect
clawmetry sync
```

സിങ്ക് ഡെമൺ പ്രവർത്തിക്കുന്ന ഏത് OpenShell കണ്ടെയ്നറിനുള്ളിലും സെഷനുകൾ സ്വയമേവ കണ്ടെത്തും.

### ഓപ്ഷണൽ: വ്യക്തമായ സാൻഡ്ബോക്സ് പേര്

സ്വയമേവ കണ്ടെത്തൽ പ്രവർത്തിക്കുന്നില്ലെങ്കിൽ, ശരിയായ സാൻഡ്ബോക്സിലേക്ക് ClawMetry ചൂണ്ടിക്കാണിക്കുക:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### സാൻഡ്ബോക്സിനുള്ളിൽ പ്രവർത്തിപ്പിക്കുന്നു (നൂതനം)

സിങ്ക് ഡെമൺ OpenShell സാൻഡ്ബോക്സിനുള്ളിൽ **തന്നെ** പ്രവർത്തിപ്പിക്കണമെങ്കിൽ, ClawMetry ingest API-യിലേക്ക് എത്താൻ കഴിയുന്ന വിധം നിങ്ങളുടെ NemoClaw നെറ്റ്‌വർക്ക് പോളിസിയിലേക്ക് ഈ egress നിയമം ചേർക്കുക:

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

| എൻഡ്‌പോയിന്റ് | പോർട്ട് | പ്രോട്ടോക്കോൾ | ആവശ്യമാണോ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | അതെ (സിങ്ക് ഡെമൺ → ക്ലൗഡ്) |
| `localhost:8900` | 8900 | HTTP | അതെ (ലോക്കൽ ഡാഷ്ബോർഡ് UI) |
| Docker സോക്കറ്റ് (`/var/run/docker.sock`) | — | Unix സോക്കറ്റ് | കണ്ടെയ്നർ സെഷൻ കണ്ടെത്തലിന് |

സിങ്ക് ഡെമൺ `ingest.clawmetry.com`-ലേക്ക് മാത്രമേ ഔട്ട്ബൗണ്ട് HTTPS കോളുകൾ ചെയ്യൂ. ഇൻബൗണ്ട് പോർട്ടുകൾ ആവശ്യമില്ല.

---

## ക്ലൗഡ് ഡിപ്ലോയ്‌മെന്റ്

SSH ടണലുകൾ, റിവേഴ്സ് പ്രോക്സി, Docker എന്നിവയ്ക്കായി **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** കാണുക.

## ടെസ്റ്റിംഗ്

ഈ പ്രോജക്ട് BrowserStack ഉപയോഗിച്ച് ടെസ്റ്റ് ചെയ്യപ്പെടുന്നു.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ടെലിമെട്രി

ClawMetry `https://app.clawmetry.com/api/install`-ലേക്ക് അജ്ഞാത
ഇൻസ്റ്റാൾ-ലൈഫ്‌സൈക്കിൾ പിംഗുകൾ അയക്കുന്നു: നിങ്ങൾ ഒരു പുതിയ മെഷീനിൽ
`clawmetry` CLI ആദ്യമായി പ്രവർത്തിപ്പിക്കുമ്പോൾ ഒരു `install` പിംഗ്,
ഒരു പുതിയ വേർഷനിലേക്ക് അപ്ഗ്രേഡ് ചെയ്തതിന് ശേഷമുള്ള ആദ്യ റണ്ണിൽ ഒരു
`update` പിംഗ്, ഡാഷ്ബോർഡിനുള്ളിലെ ഓൺബോർഡിംഗ് തിരഞ്ഞെടുപ്പ്
പൂർത്തിയാക്കുമ്പോൾ ഒരു `onboarded` പിംഗ്. യഥാർത്ഥ ഇൻസ്റ്റാളുകൾ
എണ്ണാൻ ഞങ്ങൾ ഇത് ഉപയോഗിക്കുന്നു (അസംസ്‌കൃത PyPI ഡൗൺലോഡ് സംഖ്യകൾ
~98% മിററുകൾ, CI, ഓട്ടോ-അപ്ഡേറ്റ് പുനർ-ഡൗൺലോഡുകൾ ആണ്), ഏതൊക്കെ
ഏജന്റ് ഫ്രെയിംവർക്കുകളും വേർഷനുകളും ലോകത്ത് യഥാർത്ഥത്തിൽ
ഉപയോഗത്തിലുണ്ടെന്ന് അറിയാനും.

**ഓരോ വേർഷനിലും ഓരോ ലൈഫ്‌സൈക്കിൾ ഇവന്റിനും പരമാവധി ഒരു POST**, ഇവ അടങ്ങിയത്:

| ഫീൽഡ് | ഉദാഹരണം | എന്തുകൊണ്ട് |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`-ൽ സൂക്ഷിച്ച റാൻഡം UUID | ഡീഡ്യൂപ്; നിങ്ങൾ Cloud sync വ്യക്തമായി കണക്ട് ചെയ്യുന്നത് വരെ അജ്ഞാതം (പ്രാമാണീകരിച്ച ഡെമൺ ഹാർട്ട്ബീറ്റ് പിന്നീട് അത് വഹിക്കുന്നു, ഈ ഇൻസ്റ്റാളിനെ നിങ്ങളുടെ അക്കൗണ്ടുമായി ബന്ധിപ്പിക്കുന്നു) |
| `event` | `install` / `update` / `onboarded` | പുതിയ ഇൻസ്റ്റാൾ vs നിലവിലുള്ള ഒന്നിന്റെ അപ്ഗ്രേഡ് |
| `version` | `0.12.167` | ഏതൊക്കെ വേർഷനുകൾ ഉപയോഗത്തിലുണ്ട് |
| `os` / `os_version` | `Darwin` / `25.3.0` | പ്ലാറ്റ്ഫോം പിന്തുണ മുൻഗണനകൾ |
| `python` | `3.11.15` | Python വേർഷൻ പിന്തുണ മാട്രിക്സ് |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | അടുത്തതായി ഞങ്ങൾ ഏത് ഏജന്റുകളുമായി ഇന്റഗ്രേറ്റ് ചെയ്യണം |
| `is_ci` / `ci_provider` | `true` / `github_actions` | മനുഷ്യ ഇൻസ്റ്റാളുകളെ CI ശബ്ദത്തിൽ നിന്ന് വേർതിരിക്കുന്നു |

**ഞങ്ങൾ അയക്കാത്തത്**: IP (ക്ലൗഡ് അഭ്യർത്ഥനയിൽ നിന്ന് സെർവർ-സൈഡിൽ
രാജ്യ കോഡ് കണ്ടെത്തി, തുടർന്ന് IP നിരസിക്കുന്നു), ഹോസ്റ്റ്നാമം,
യൂസർനാമം, വർക്ക്‌സ്പേസ് പാത്ത്, ഫയൽ ഉള്ളടക്കങ്ങൾ, നിങ്ങളുടെ
api_key, നിങ്ങളുടെ ഇമെയിൽ, PII അല്ലെങ്കിൽ വർക്ക്‌സ്പേസ്-നിർദ്ദിഷ്ടമായ
ഒന്നും തന്നെ. വയർ പേലോഡ് [`clawmetry/telemetry.py`](clawmetry/telemetry.py)-ൽ
ഓഡിറ്റ് ചെയ്യാവുന്നതാണ്.

**ഒഴിവാക്കുക** (ഇവയിൽ ഏതെങ്കിലും ഒന്ന് ഇത് സ്ഥിരമായി പ്രവർത്തനരഹിതമാക്കും):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # ഓരോ-ഷെല്ലിനും
export DO_NOT_TRACK=1                          # W3C ക്രോസ്-ടൂൾ സ്റ്റാൻഡേർഡ്
touch ~/.clawmetry/notelemetry                 # സ്ഥിരമായ ഫയൽ മാർക്കർ
```

നെറ്റ്‌വർക്ക് പരാജയം ഇവിടെ ഒരിക്കലും `clawmetry` പ്രവർത്തിക്കുന്നതിൽ
നിന്ന് തടയില്ല — പിംഗ് ഒരു ഡെമൺ ത്രെഡിൽ 3 സെക്കൻഡ് ടൈംഔട്ടോടെ
ഫയർ-ആൻഡ്-ഫോർഗെറ്റ് ആണ്.

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> നിർമ്മിച്ചത് · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ഇക്കോസിസ്റ്റത്തിന്റെ ഭാഗം</sub>
</p>
