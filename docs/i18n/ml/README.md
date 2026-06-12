<!-- i18n-src:48548997be76 -->
> മലയാളം translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**നിങ്ങളുടെ ഏജന്റ് ചിന്തിക്കുന്നത് കാണൂ.** **12 AI ഏജന്റ് റൺടൈമുകൾക്കുള്ള** തത്സമയ ഒബ്സർവബിലിറ്റി: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex എന്നിവയും മറ്റ് 8 എണ്ണവും. നിങ്ങളുടെ മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റിനും ഒരൊറ്റ ഡാഷ്ബോർഡ്.

> 🌐 **ഇത് വായിക്കൂ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

ഒരൊറ്റ കമാൻഡ്. കോൺഫിഗറേഷൻ ഇല്ല. എല്ലാം സ്വയം കണ്ടെത്തുന്നു.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ൽ തുറക്കുന്നു, ജോലി തീർന്നു.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 12 ഏജന്റ് റൺടൈമുകളുമായി പ്രവർത്തിക്കുന്നു

ClawMetry OpenClaw-നുള്ള ഒബ്സർവബിലിറ്റിയായി ആരംഭിച്ചു, ഇപ്പോൾ ഒരൊറ്റ ഡാഷ്ബോർഡിൽ നിങ്ങളുടെ **മുഴുവൻ ഏജന്റ് ഫ്ലീറ്റും** അളക്കുന്നു, നിങ്ങളുടെ മെഷീനിലെ ഓരോ റൺടൈമും സ്വയം കണ്ടെത്തി:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw, NemoClaw എന്നിവ ഓപ്പൺ സോഴ്സ് ആപ്പിൽ സൗജന്യമാണ്; മറ്റ് റൺടൈമുകൾ ClawMetry Cloud അല്ലെങ്കിൽ സ്വയം ഹോസ്റ്റ് ചെയ്ത Pro ലൈസൻസ് ഉപയോഗിച്ച് സജീവമാകുന്നു. ഹെഡറിൽ നിന്ന് റൺടൈം മാറ്റുക, എല്ലാ ടാബും, ചെലവ്, ടോക്കണുകൾ, ടൂളുകൾ, ട്രേസുകൾ, ആ റൺടൈമിലേക്ക് പുനഃക്രമീകരിക്കും.

## നിങ്ങൾക്ക് ലഭിക്കുന്നത്

- **Flow** — ചാനലുകൾ, ബ്രെയിൻ, ടൂളുകൾ, തിരിച്ചും ഒഴുകുന്ന സന്ദേശങ്ങൾ കാണിക്കുന്ന തത്സമയ ആനിമേഷൻ ഡയഗ്രം
- **Overview** — ഹെൽത്ത് ചെക്കുകൾ, ആക്ടിവിറ്റി ഹീറ്റ്മാപ്പ്, സെഷൻ എണ്ണം, മോഡൽ വിവരങ്ങൾ
- **Usage** — ദൈനംദിന/പ്രതിവാര/പ്രതിമാസ വിശകലനങ്ങളോടെ ടോക്കൺ, ചെലവ് ട്രാക്കിങ്
- **Sessions** — മോഡൽ, ടോക്കണുകൾ, അവസാന പ്രവർത്തനം സഹിതം സജീവ ഏജന്റ് സെഷനുകൾ
- **Crons** — സ്റ്റാറ്റസ്, അടുത്ത റൺ, ദൈർഘ്യം സഹിതം ഷെഡ്യൂൾ ചെയ്ത ജോലികൾ
- **Logs** — നിറ-കോഡ് ചെയ്ത തത്സമയ ലോഗ് സ്ട്രീമിങ്
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ദൈനംദിന കുറിപ്പുകൾ ബ്രൗസ് ചെയ്യൂ
- **Transcripts** — സെഷൻ ചരിത്രങ്ങൾ വായിക്കാൻ ചാറ്റ്-ബബിൾ UI
- **Alerts** — ബജറ്റ് പരിധികൾ, പിശക് നിരക്ക് ട്രിഗറുകൾ, ഏജന്റ്-ഓഫ്‌ലൈൻ കണ്ടെത്തൽ; Slack, Discord, PagerDuty, Telegram, Email-ലേക്ക് റൂട്ട് ചെയ്യുന്നു
- **Approvals** — നശിപ്പിക്കുന്ന ഡിലീറ്റുകൾ, ഫോഴ്സ് പുഷുകൾ, DB മ്യൂട്ടേഷനുകൾ, sudo, പാക്കേജ് ഇൻസ്റ്റോളുകൾ, നെറ്റ്‌വർക്ക് കോളുകൾ ഒറ്റ ക്ലിക്ക് അംഗീകാരത്തിന് പിന്നിൽ ഗേറ്റ് ചെയ്യൂ

## സ്ക്രീൻഷോട്ടുകൾ

### 🧠 Brain — തത്സമയ ഏജന്റ് ഇവന്റ് സ്ട്രീം
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ടോക്കൺ ഉപയോഗം & സെഷൻ സംഗ്രഹം
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — തത്സമയ ടൂൾ കോൾ ഫീഡ്
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — മോഡൽ & സെഷൻ അനുസരിച്ച് ചെലവ് വിശദാംശം
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — വർക്ക്സ്പേസ് ഫയൽ ബ്രൗസർ
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — പോസ്ചർ & ഓഡിറ്റ് ലോഗ്
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — ബജറ്റ് പരിധികൾ, പിശക് നിരക്ക് ട്രിഗറുകൾ, Slack / Discord / PagerDuty / Email-ലേക്ക് വെബ്ഹുക്കുകൾ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — അപകടകരമായ ടൂൾ കോളുകൾ മാനുവൽ അംഗീകാരത്തിന് പിന്നിൽ ഗേറ്റ് ചെയ്യൂ; നയ-പിന്തുണയുള്ള സംരക്ഷണ നിയമങ്ങൾ
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## ഇൻസ്റ്റോൾ ചെയ്യൂ

**ഒറ്റ ലൈൻ (ശുപാർശ ചെയ്യുന്നത്):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**സോഴ്സിൽ നിന്ന്:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 ഫ്രണ്ടെൻഡ് ഡെവലപ്മെന്റ്

v2 React ആപ്പ് `frontend/` ൽ ഉണ്ട്, Flask സർവർ v2 പ്രാപ്തമാക്കി ആരംഭിക്കുമ്പോൾ `/v2` ൽ സേവനം ചെയ്യുന്നു.

ഡെവലപ്മെന്റ് സമയത്ത് രണ്ട് ടെർമിനലുകൾ ഉപയോഗിക്കൂ:

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

`http://localhost:5173/v2/` തുറക്കൂ. Vite `/api` അഭ്യർഥനകൾ `http://localhost:8900`-ലേക്ക് പ്രോക്സി ചെയ്യുന്നു, അതിനാൽ React ആപ്പിന് അധിക CORS സജ്ജീകരണം ആവശ്യമില്ലാതെ ലോക്കൽ Flask സർവറുമായി സംസാരിക്കാം.

Python പാക്കേജിൽ ഉൾപ്പെടുന്ന ബണ്ടിൽ ബിൽഡ് ചെയ്യാൻ:

```bash
cd frontend
npm run build
```

പ്രൊഡക്ഷൻ ബണ്ടിൽ `clawmetry/static/v2/dist/` ലേക്ക് എഴുതുന്നു.

## റൺടൈം / ഏജന്റ് അനുയോജ്യത

ClawMetry പല AI ഏജന്റ് റൺടൈമുകൾ നിരീക്ഷിക്കുന്നു, OpenClaw മാത്രമല്ല. OpenClaw അല്ലാത്ത ഓരോ റൺടൈമും ഒരു സമർപ്പിത റീഡർ അഡാപ്റ്ററുമായി വരുന്നു, അത് അതിന്റെ നേറ്റീവ് സെഷൻ ഫോർമാറ്റ് ClawMetry-യുടെ ഏകീകൃത രൂപങ്ങളിലേക്ക് മൊഴിമാറ്റം ചെയ്യുന്നു; daemon അവ ഒരേ DuckDB സ്റ്റോറിലേക്ക് ഇൻജസ്റ്റ് ചെയ്യുന്നു, ക്ലൗഡ് സ്നാപ്ഷോട്ടും, റൺടൈം ടാഗ് ചെയ്ത്, ഒന്നിലധികം ഉള്ളപ്പോൾ Session replay ടാബ് **റൺടൈം സ്വിച്ചർ** കാണിക്കുന്നു. പൂർണ്ണ മാട്രിക്സിനും റൺടൈമുകൾ ചേർക്കുന്നതിനുള്ള ഗൈഡിനും [`docs/compatibility.md`](docs/compatibility.md) കാണൂ, OpenClaw ഫാമിലി പ്രൈമറിന് [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) കാണൂ.

| റൺടൈം / ഏജന്റ് | സ്റ്റാറ്റസ് | കുറിപ്പുകൾ |
|---|---|---|
| **OpenClaw** | Native | റഫറൻസ് റൺടൈം, സ്വയം കണ്ടെത്തുന്നു |
| **PicoClaw** | Beta adapter | ഫ്ലാറ്റ് `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ. |
| **NanoClaw** | Beta adapter | പ്രതി-സെഷൻ SQLite (`data/v2-sessions`). ട്രാൻസ്ക്രിപ്റ്റുകളും സന്ദേശ എണ്ണവും. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടോക്കണുകൾ/ചെലവ്. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ + ചിന്ത, ടോക്കൺ ഉപയോഗം. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ഉപയോഗം. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. ചാറ്റ്/കോംപോസർ ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ. |
| **Aider** | Beta adapter | പ്രതി-പ്രോജക്ട് `.aider.chat.history.md`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടോക്കൺ എണ്ണം. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ആകെ. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കണുകൾ + ചെലവ്. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. ട്രാൻസ്ക്രിപ്റ്റുകൾ, മോഡൽ, ടൂൾ കോളുകൾ, ടോക്കൺ ഉപയോഗം. |

"Beta adapter" എന്നാൽ ClawMetry ആ റൺടൈമിന്റെ യഥാർഥ ഓൺ-ഡിസ്ക് ഫോർമാറ്റിനുള്ള ഒരു റീഡർ ഷിപ്പ് ചെയ്യുന്നു, ഓരോന്നും ഒരു യഥാർഥ മെഷീനിൽ ഒരു യഥാർഥ ഇൻസ്റ്റോളിനെതിരെ നിർമ്മിക്കുകയും പരിശോധിക്കുകയും ചെയ്തിട്ടുണ്ട് (`tests/fixtures/runtimes/<rt>/` കാണൂ). അഡാപ്റ്ററുകൾ റീഡ്-ഓൺലി ആണ്; ഓരോന്നും അതിന്റെ റൺടൈം യഥാർഥത്തിൽ ഡിസ്കിൽ സ്റ്റോർ ചെയ്യുന്നതിനെക്കുറിച്ച് സത്യസന്ധമാണ് (ഉദാ. PicoClaw/NanoClaw/Cursor ടോക്കൺ ചെലവ് ഡിസ്കിൽ എഴുതുന്നില്ല). ഒരു നോഡിൽ നിരവധി റൺടൈമുകൾ പ്രവർത്തിക്കുമ്പോൾ, റൺടൈം സ്വിച്ചർ ഒരു വ്യക്തമായ ആഴത്തിലുള്ള പഠനത്തിനായി സെഷൻ വ്യൂ ഒന്നിലേക്ക് ചുരുക്കുന്നു.

## ഏത് SDK ഏജന്റും ട്രാക്ക് ചെയ്യൂ — ഔട്ട്-ലൂപ്പ് ചെലവ് ആട്രിബ്യൂഷൻ

മുകളിലെ റൺടൈമുകൾ എല്ലാം സെഷനുകൾ ഡിസ്കിൽ എഴുതുന്നു. നിങ്ങളുടെ സ്വന്തം **പ്രൊഡക്ഷൻ ഏജന്റ്**, OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, അല്ലെങ്കിൽ ഒരു സാദാ `httpx` ലൂപ്പ് ഉപയോഗിച്ച് നിർമ്മിച്ചത്, എഴുതുന്നില്ല. ClawMetry-യുടെ സീറോ-കോൺഫിഗ് ഇന്റർസെപ്റ്റർ `httpx`/`requests` മങ്കി-പാച്ചിങ് ചെയ്ത് അതിന്റെ LLM കോളുകൾ (ചെലവ്, ടോക്കണുകൾ, レイテンシ, പിശകുകൾ) ഇപ്പോഴും ക്യാപ്ചർ ചെയ്യുന്നു:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (അല്ലെങ്കിൽ `CLAWMETRY_SOURCE=support-agent` എൻവ് വേർ) ഓരോ കോളിനും ഒരു **പേരിട്ട സോഴ്സ്** ടാഗ് ചെയ്യുന്നു, അതിനാൽ നിങ്ങൾ പ്രവർത്തിപ്പിക്കുന്ന ഓരോ ഉൽപ്പന്നവും Overview-ലെ ഡാഷ്ബോർഡിന്റെ **🔌 Out-loop sources** കാർഡിൽ ഒരു സ്വന്തം ഫസ്റ്റ്-ക്ലാസ്, ചെലവ്-ആട്രിബ്യൂട്ടബിൾ ലൈനായി പ്രത്യക്ഷപ്പെടുന്നു, ഏജന്റ് അനുസരിച്ച് കോളുകൾ, പ്രൊവൈഡറുകൾ, レイテンシ, പിശക് നിരക്ക്. സോഴ്സ് സജ്ജമല്ലേ? കോളുകൾ ഇപ്പോഴും ട്രാക്ക് ചെയ്യുന്നു; കാർഡ് മറഞ്ഞിരിക്കുന്നു.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ഇത് റൺടൈം അഡാപ്റ്ററുകൾ ഫീഡ് ചെയ്യുന്ന അതേ ഡേറ്റ ലെയർ ആണ് (DuckDB → ക്ലൗഡ് സ്നാപ്ഷോട്ട്), അതിനാൽ ഔട്ട്-ലൂപ്പ് സോഴ്സുകൾ മറ്റെല്ലാം പോലെ ക്ലൗഡ് ഡാഷ്ബോർഡിലേക്ക് സിങ്ക് ചെയ്യുന്നു, E2E-എൻക്രിപ്റ്റ് ചെയ്ത്.

## OpenTelemetry — വെൻഡർ-ന്യൂട്രൽ, നിങ്ങളുടെ ട്രേസുകൾ എവിടേക്കും അയക്കൂ

ClawMetry **GenAI സെമാന്റിക് കൺവൻഷനുകൾ** ഉപയോഗിച്ച് രണ്ട് ദിശകളിലും **OpenTelemetry** സംസാരിക്കുന്നു, അതിനാൽ നിങ്ങളുടെ ഏജന്റ് ട്രേസുകൾ ഒരിക്കലും ഒരൊറ്റ ടൂളിൽ ലോക്ക് ചെയ്യപ്പെടുന്നില്ല.

ഓരോ സെഷനും, LLM കോളുകൾ, ടൂളുകൾ, സബ്-ഏജന്റുകൾ, ടോക്കണുകൾ, ചെലവ്, OTLP/HTTP GenAI സ്പാനുകളായി ഏത് കളക്ടറിലേക്കും (Datadog, Grafana, Honeycomb, അല്ലെങ്കിൽ നിങ്ങളുടെ സ്വന്തം OTel Collector) **എക്സ്പോർട്ട്** ചെയ്യൂ:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ഓഥ് ഹെഡറുകളും പോൾ ഇന്റർവലും ഓപ്ഷണൽ എൻവ് വേർ ആണ്:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ഇൻജസ്റ്റ്** — ബിൽറ്റ്-ഇൻ OTLP റിസീവർ `/v1/traces`, `/v1/metrics` എന്നിവയിൽ മറ്റേതും നിന്ന് ട്രേസുകളും മെട്രിക്കുകളും സ്വീകരിക്കുന്നു (`pip install clawmetry[otel]` protobuf ഇൻജസ്റ്റിന്).

നിങ്ങൾക്ക് സീറോ-കോൺഫിഗ്, ലോക്കൽ-ഫസ്റ്റ് ClawMetry ഡാഷ്ബോർഡ് **ഒപ്പം** നിങ്ങളുടെ ടീം ഇതിനകം ഉപയോഗിക്കുന്ന ഏത് ബ്ക്കെൻഡിലും ഡേറ്റ ലഭിക്കുന്നു, ലോക്ക്-ഇൻ ഇല്ല, ഇൻസ്റ്റോൾ ചെയ്യാൻ രണ്ടാമത്തെ ഏജന്റ് ഇല്ല.

## കോൺഫിഗറേഷൻ

മിക്ക ആളുകൾക്കും ഒരു കോൺഫിഗും ആവശ്യമില്ല. ClawMetry നിങ്ങളുടെ വർക്ക്സ്പേസ്, ലോഗുകൾ, സെഷനുകൾ, cron ജോലികൾ എല്ലാം സ്വയം കണ്ടെത്തുന്നു.

നിങ്ങൾക്ക് ഇച്ഛാനുസരണം ആക്കണമെങ്കിൽ:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

എല്ലാ ഓപ്ഷനുകളും: `clawmetry --help`

## പിന്തുണയ്ക്കുന്ന ചാനലുകൾ

നിങ്ങൾ കോൺഫിഗർ ചെയ്ത ഓരോ OpenClaw ചാനലിനും ClawMetry തത്സമയ പ്രവർത്തനം കാണിക്കുന്നു. Flow ഡയഗ്രാമിൽ നിങ്ങളുടെ `openclaw.json` ൽ യഥാർഥത്തിൽ സജ്ജമാക്കിയ ചാനലുകൾ മാത്രം ദൃശ്യമാകുന്നു, കോൺഫിഗർ ചെയ്യാത്തവ സ്വയം മറഞ്ഞിരിക്കുന്നു.

Flow-ൽ ഏത് ചാനൽ നോഡും ക്ലിക്ക് ചെയ്ത് ഇൻകമിങ്/ഔട്ട്ഗോയിങ് സന്ദേശ എണ്ണം സഹിതം ഒരു തത്സമയ ചാറ്റ് ബബിൾ വ്യൂ കാണൂ.

| ചാനൽ | സ്റ്റാറ്റസ് | തത്സമയ പോപ്പ്അപ്പ് | കുറിപ്പുകൾ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | സന്ദേശങ്ങൾ, സ്റ്റാറ്റ്സ്, 10s റിഫ്രഷ് |
| 💬 **iMessage** | ✅ Full | ✅ | `~/Library/Messages/chat.db` നേരിട്ട് വായിക്കുന്നു |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) വഴി |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli വഴി |
| 🟣 **Discord** | ✅ Full | ✅ | Guild + ചാനൽ കണ്ടെത്തൽ |
| 🟪 **Slack** | ✅ Full | ✅ | Workspace + ചാനൽ കണ്ടെത്തൽ |
| 🌐 **Webchat** | ✅ Full | ✅ | ബിൽറ്റ്-ഇൻ വെബ് UI സെഷനുകൾ |
| 📡 **IRC** | ✅ Full | ✅ | ടെർമിനൽ-സ്റ്റൈൽ ബബിൾ UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API വഴി iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API വെബ്ഹുക്കുകൾ വഴി |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams bot പ്ലഗിൻ വഴി |
| 🔷 **Mattermost** | ✅ Full | ✅ | സ്വയം-ഹോസ്റ്റ് ടീം ചാറ്റ് |
| 🟩 **Matrix** | ✅ Full | ✅ | വികേന്ദ്രീകൃതം, E2EE പിന്തുണ |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | വികേന്ദ്രീകൃത NIP-04 DMs |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC കണക്ഷൻ വഴി ചാറ്റ് |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket ഇവന്റ് സബ്സ്ക്രിപ്ഷൻ |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **സ്വയം-കണ്ടെത്തൽ:** ClawMetry നിങ്ങളുടെ `~/.openclaw/openclaw.json` വായിക്കുകയും നിങ്ങൾ യഥാർഥത്തിൽ കോൺഫിഗർ ചെയ്ത ചാനലുകൾ മാത്രം റെൻഡർ ചെയ്യുകയും ചെയ്യുന്നു. മാനുവൽ സജ്ജീകരണം ആവശ്യമില്ല.

## Docker ഡിപ്ലോയ്മെന്റ്

ClawMetry ഒരു കണ്ടെയ്നറിൽ പ്രവർത്തിപ്പിക്കണോ? പ്രശ്നമില്ല! 🐳

**Docker ഉപയോഗിച്ച് ദ്രുത ആരംഭം:**

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

> **കുറിപ്പ്:** Docker-ൽ പ്രവർത്തിക്കുമ്പോൾ, ClawMetry നിങ്ങളുടെ സജ്ജീകരണം സ്വയം കണ്ടെത്തുന്നതിന് നിങ്ങളുടെ ഏജന്റിന്റെ ഡേറ്റ + ലോഗ് ഡയറക്ടറികൾ (ഉദാ. `~/.openclaw`, `~/.claude`, `~/.codex`) മൌണ്ട് ചെയ്യൂ.

## ആവശ്യകതകൾ

- Python 3.8+
- Flask (pip വഴി സ്വയം ഇൻസ്റ്റോൾ ചെയ്യുന്നു)
- ഒരേ മെഷീനിൽ ഒരു AI ഏജന്റ് റൺടൈം: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, അല്ലെങ്കിൽ PicoClaw (അല്ലെങ്കിൽ Docker-നുള്ള മൌണ്ടഡ് വോളിയങ്ങൾ)
- Linux അല്ലെങ്കിൽ macOS

## NemoClaw / OpenShell പിന്തുണ

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) സ്വയം കണ്ടെത്തുന്നു, NVIDIA-യുടെ എന്റർപ്രൈസ് സുരക്ഷാ ആവരണം OpenClaw-ന്, ഏജന്റുകൾ സാൻഡ്ബോക്സ്ഡ് OpenShell കണ്ടെയ്നറുകൾക്കുള്ളിൽ പ്രവർത്തിപ്പിക്കുന്നു.

മിക്ക കേസുകളിലും അധിക കോൺഫിഗറേഷൻ ആവശ്യമില്ല. sync daemon സെഷൻ ഫയലുകൾ ഹോസ്റ്റിലെ `~/.openclaw/` ൽ ആണോ OpenShell കണ്ടെയ്നറിനുള്ളിൽ ആണോ ഉള്ളത് എന്നതൊക്കെ സ്വയം കണ്ടെത്തുന്നു.

### ഇത് എങ്ങനെ പ്രവർത്തിക്കുന്നു

ClawMetry NemoClaw-നെ രണ്ട് രീതിയിൽ കണ്ടെത്തുന്നു:

1. **ബൈനറി കണ്ടെത്തൽ** — `nemoclaw` CLI ഉണ്ടോ എന്ന് പരിശോധിക്കുകയും `nemoclaw status` പ്രവർത്തിപ്പിച്ച് sandbox വിവരം ലഭ്യമാക്കുകയും ചെയ്യുന്നു
2. **കണ്ടെയ്നർ കണ്ടെത്തൽ** — `openshell`, `nemoclaw`, അല്ലെങ്കിൽ `ghcr.io/nvidia/` ഇമേജുകൾക്കായി ഡോക്കർ കണ്ടെയ്നറുകൾ സ്കാൻ ചെയ്ത്, വോളിയം മൌണ്ടുകൾ അല്ലെങ്കിൽ `docker cp` വഴി സെഷനുകൾ വായിക്കുന്നു

NemoClaw കണ്ടെയ്നറുകളിൽ നിന്ന് സിങ്ക് ചെയ്ത സെഷൻ ഫയലുകൾ ക്ലൗഡ് ഡാഷ്ബോർഡിൽ `runtime=nemoclaw`, `container_id` മെറ്റാഡേറ്റ ഉപയോഗിച്ച് ടാഗ് ചെയ്തിരിക്കുന്നു, അതിനാൽ ഒറ്റ നോട്ടത്തിൽ അവ സ്റ്റാൻഡേർഡ് OpenClaw സെഷനുകളിൽ നിന്ന് വേർതിരിക്കാം.

### ശുപാർശ ചെയ്ത സജ്ജീകരണം: ഹോസ്റ്റിൽ sync daemon

ഏറ്റവും മികച്ച അനുഭവത്തിനായി, **ഹോസ്റ്റ് മെഷീനിൽ** (sandbox-ന് ഉള്ളിൽ അല്ല) ClawMetry-യുടെ sync daemon പ്രവർത്തിപ്പിക്കൂ. ഇത് NemoClaw നെറ്റ്‌വർക്ക് നയ നിയന്ത്രണങ്ങൾ ഒഴിവാക്കുന്നു.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon ഏത് റണ്ണിങ് OpenShell കണ്ടെയ്നറുകൾക്കുള്ളിലെ സെഷനുകളും സ്വയം കണ്ടെത്തും.

### ഓപ്ഷണൽ: വ്യക്തമായ sandbox പേര്

സ്വയം-കണ്ടെത്തൽ പ്രവർത്തിക്കുന്നില്ലെങ്കിൽ, ClawMetry-നെ ശരിയായ sandbox-ലേക്ക് ചൂണ്ടിക്കാണിക്കൂ:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### sandbox-ന് ഉള്ളിൽ പ്രവർത്തിപ്പിക്കൽ (വിദഗ്ധർക്ക്)

sync daemon OpenShell sandbox-ന് **ഉള്ളിൽ** പ്രവർത്തിപ്പിക്കേണ്ടി വന്നാൽ, ClawMetry ingest API-ലേക്ക് എത്താൻ നിങ്ങളുടെ NemoClaw നെറ്റ്‌വർക്ക് നയത്തിൽ ഈ egress നിയമം ചേർക്കൂ:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

ഇത് ഉപയോഗിച്ച് പ്രയോഗിക്കൂ:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### പോർട്ടുകളും എൻഡ്‌പോയിന്റുകളും

| എൻഡ്‌പോയിന്റ് | പോർട്ട് | പ്രോട്ടോക്കോൾ | ആവശ്യമാണോ |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | അതെ (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | അതെ (ലോക്കൽ ഡാഷ്ബോർഡ് UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | കണ്ടെയ്നർ സെഷൻ കണ്ടെത്തലിന് |

sync daemon `ingest.clawmetry.com`-ലേക്ക് മാത്രം ഔട്ട്ബൗണ്ട് HTTPS കോളുകൾ ചെയ്യുന്നു. ഇൻബൗണ്ട് പോർട്ടുകൾ ആവശ്യമില്ല.

---

## ക്ലൗഡ് ഡിപ്ലോയ്മെന്റ്

SSH ടണലുകൾ, റിവേഴ്സ് പ്രോക്സി, Docker എന്നിവ ഉൾപ്പെടെ **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** കാണൂ.

## ടെസ്റ്റിങ്

ഈ പ്രോജക്ട് BrowserStack ഉപയോഗിച്ച് ടെസ്റ്റ് ചെയ്യുന്നു.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ടെലിമെട്രി

ഒരു പുതിയ മെഷീനിൽ ആദ്യമായി `clawmetry` CLI പ്രവർത്തിപ്പിക്കുമ്പോൾ ClawMetry ഒരൊറ്റ അജ്ഞാത "ആദ്യ റൺ" പിങ്ക്
`https://app.clawmetry.com/api/install`-ലേക്ക് അയക്കുന്നു. ഇൻസ്റ്റോളുകൾ എണ്ണുന്നതിനും (ഒരു OSS പ്രോജക്ടിന് ഞങ്ങളുടെ ഏക മാർക്കറ്റിങ് മെട്രിക്) ഞങ്ങളുടെ ഉപയോക്താക്കൾ ഏത് ഏജന്റ് ഫ്രെയിംവർക്കുകൾ ഇൻസ്റ്റോൾ ചെയ്തിട്ടുണ്ടെന്ന് മനസ്സിലാക്കുന്നതിനും ഞങ്ങൾ ഇത് ഉപയോഗിക്കുന്നു.

**ഇൻസ്റ്റോൾ ഒന്നിന് കൃത്യമായി ഒരൊറ്റ POST**, ഇവ ഉൾക്കൊള്ളുന്നു:

| ഫീൽഡ് | ഉദാഹരണം | എന്തുകൊണ്ട് |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` ൽ സ്റ്റോർ ചെയ്ത random UUID | ഡ്യൂപ്; നിങ്ങളുടെ ഇമെയിലുമായോ api_key-ഉമായോ ബന്ധിപ്പിക്കുന്നില്ല |
| `version` | `0.12.167` | ഏത് പതിപ്പുകൾ ഉപയോഗത്തിലുണ്ട് |
| `os` / `os_version` | `Darwin` / `25.3.0` | പ്ലാറ്റ്ഫോം പിന്തുണ മുൻഗണനകൾ |
| `python` | `3.11.15` | Python പതിപ്പ് പിന്തുണ മാട്രിക്സ് |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ഞങ്ങൾ അടുത്തത് ഏത് ഏജന്റുകളുമായി ഇന്റഗ്രേഷൻ ചെയ്യണം |
| `is_ci` / `ci_provider` | `true` / `github_actions` | മനുഷ്യ ഇൻസ്റ്റോളുകളെ CI നോയ്സിൽ നിന്ന് വേർതിരിക്കൂ |

**ഞങ്ങൾ അയക്കാത്തവ**: IP (ക്ലൗഡ് അഭ്യർഥനയിൽ നിന്ന് കൺട്രി കോഡ് സർവർ-സൈഡ് ഡിറൈവ് ചെയ്ത് IP ഉടൻ ഉപേക്ഷിക്കുന്നു), hostname, username, workspace പഥം, ഫയൽ ഉള്ളടക്കം, നിങ്ങളുടെ api_key, ഇമെയിൽ, PII അല്ലെങ്കിൽ workspace-സ്പെസിഫിക് ഒന്നും. വയർ പേലോഡ്
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)-ൽ ഓഡിറ്റ് ചെയ്യാവുന്നതാണ്.

**ഒഴിവാക്കൂ** (ഇതിൽ ഏതെങ്കിലും ഒന്ന് ശാശ്വതമായി നിരോധിക്കുന്നു):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ഇവിടെ ഒരു നെറ്റ്‌വർക്ക് പരാജയം ഒരിക്കലും `clawmetry` പ്രവർത്തിക്കുന്നതിൽ നിന്ന് തടഞ്ഞുവെക്കുന്നില്ല, പിങ്ക് 3 സെക്കൻഡ് ടൈംഔട്ടോടെ ഒരു daemon ത്രെഡിൽ ഫയർ-ആൻഡ്-ഫോർഗറ്റ് ആണ്.

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> നിർമ്മിച്ചത് · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ആവാസവ്യവസ്ഥയുടെ ഭാഗം</sub>
</p>
