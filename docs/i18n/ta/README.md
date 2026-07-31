<!-- i18n-src:9a05336fbdc1 -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்.** **14 AI ஏஜென்ட் ரன்டைம்களுக்கான** நிகழ்நேர கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex மற்றும் மேலும் 10. உங்கள் முழு ஏஜென்ட் கூட்டத்திற்கும் ஒரே டாஷ்போர்டு.

> 🌐 **இதை படிக்க:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. கட்டமைப்பு தேவையில்லை. அனைத்தையும் தானாகவே கண்டறிகிறது.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும், முடிந்தது.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

ClawMetry OpenClaw-க்கான கண்காணிப்பாகத் தொடங்கியது, இப்போது உங்கள் **முழு ஏஜென்ட் கூட்டத்தையும்** ஒரே டாஷ்போர்டில் அளவிடுகிறது, உங்கள் மெஷினில் உள்ள ஒவ்வொரு ரன்டைமையும் தானாகவே கண்டறிந்து:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw மற்றும் NemoClaw திறந்த மூல ஆப்பில் இலவசம்; மற்ற ரன்டைம்கள் ClawMetry Cloud அல்லது சுய-ஹோஸ்ட் செய்யப்பட்ட Pro உரிமத்துடன் இயங்கத் தொடங்குகின்றன. ஹெடரிலிருந்து ரன்டைம்களை மாற்றுங்கள், ஒவ்வொரு தாவலும் - செலவு, டோக்கன்கள், கருவிகள், டிரேஸ்கள் - அந்த ரன்டைமிற்கு மீண்டும் வரம்பிடப்படும். சரியான இலவச/கட்டண பிரிவு, டையர் மேட்ரிக்ஸ், `/api/entitlement` வடிவம், மற்றும் `clawmetry license` CLI ஆகியவற்றுக்கு **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ஐப் பார்க்கவும்.

## நீங்கள் என்ன பெறுவீர்கள்

- **Flow** — சேனல்கள், மூளை, கருவிகள் மற்றும் மீண்டும் வழியாக செய்திகள் பாய்வதைக் காட்டும் நேரடி அனிமேட்டட் வரைபடம்
- **Overview** — சுகாதார சோதனைகள், செயல்பாட்டு ஹீட்மேப், அமர்வு எண்ணிக்கைகள், மாடல் தகவல்
- **Usage** — தினசரி/வாராந்திர/மாதாந்திர பிரிவுகளுடன் டோக்கன் மற்றும் செலவு கண்காணிப்பு
- **Sessions** — மாடல், டோக்கன்கள், கடைசி செயல்பாட்டுடன் செயலில் உள்ள ஏஜென்ட் அமர்வுகள்
- **Crons** — நிலை, அடுத்த இயக்கம், கால அளவு ஆகியவற்றுடன் திட்டமிடப்பட்ட வேலைகள்
- **Logs** — வண்ண-குறியிடப்பட்ட நிகழ்நேர பதிவு ஸ்ட்ரீமிங்
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, தினசரி குறிப்புகளை உலாவவும்
- **Transcripts** — அமர்வு வரலாறுகளைப் படிக்க சாட்-பப்பிள் UI
- **Alerts** — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், ஏஜென்ட்-ஆஃப்லைன் கண்டறிதல்; Slack, Discord, PagerDuty, Telegram, Email ஆகியவற்றுக்கு வழிநடத்துகிறது
- **Approvals** — அழிவூட்டும் நீக்கங்கள், ஃபோர்ஸ் புஷ்கள், DB மாற்றங்கள், sudo, பேக்கேஜ் நிறுவல்கள், நெட்வொர்க் அழைப்புகளை ஒரே கிளிக் ஒப்புதலுக்குப் பின்னால் தடுக்கவும்

## ஸ்கிரீன்ஷாட்கள்

### 🧠 Brain — நேரடி ஏஜென்ட் நிகழ்வு ஸ்ட்ரீம்
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — டோக்கன் பயன்பாடு மற்றும் அமர்வு சுருக்கம்
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — நிகழ்நேர கருவி அழைப்பு ஃபீட்
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — மாடல் & அமர்வு வாரியான செலவு பிரிவு
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — பணியிட கோப்பு உலாவி
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — நிலைப்பாடு & தணிக்கை பதிவு
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், Slack / Discord / PagerDuty / Email க்கான வெப்ஹூக்குகள்
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ஆபத்தான கருவி அழைப்புகளை கைமுறை ஒப்புதலுக்குப் பின்னால் தடுக்கவும்; கொள்கை-ஆதரவுள்ள பாதுகாப்பு விதிகள்
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-க்கான முன்-செயல்படுத்தல் தடுப்பு** — ஒரே கட்டளை
பொருந்தும் கருவி அழைப்புகளை அவை இயங்குவதற்கு *முன்* இடைநிறுத்தி உங்கள்
முடிவுக்காக காத்திருக்கும் PreToolUse hook ஐ நிறுவுகிறது (உங்கள்
தொலைபேசியிலிருந்து ஒரே தட்டல் [கிளவுட் புஷ் அறிவிப்புகள்](https://app.clawmetry.com/push) இயக்கப்பட்டால்):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ஒரு மறுப்பு அந்த ஒரு கருவி அழைப்பை மட்டும் தடுக்கிறது - ஏஜென்ட் தனது அமர்வைத் தக்க வைத்துக் கொண்டு
மற்றொரு அணுகுமுறையை முயற்சி செய்யலாம். உங்கள் தொலைபேசியில் ஒப்புதல் அளிப்பது Claude Code-இன் சொந்த
அனுமதி வேண்டுகோளைத் தவிர்க்கிறது (நீங்கள் ஏற்கனவே பதிலளித்துவிட்டீர்கள்). பொருந்தாத கருவிகள் ~40ms செலவாகி
Claude Code-இன் வழக்கமான அனுமதி ஓட்டத்திற்குச் செல்கின்றன. Claude Code தானே உங்களுக்காக காத்திருக்கும்போதும்
நீங்கள் தொலைபேசி புஷ் பெறுவீர்கள் (`permission_prompt` /
`idle_prompt` அறிவிப்புகள்).

## நிறுவல்

**ஒரே வரி (பரிந்துரைக்கப்படுகிறது):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**மூலத்திலிருந்து:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 ஃப்ரண்ட்எண்ட் மேம்பாடு

v2 React ஆப் `frontend/` இல் உள்ளது, மேலும் v2 இயக்கப்பட்டு Flask
சர்வர் தொடங்கப்படும்போது `/v2` இல் வழங்கப்படுகிறது.

மேம்பாடு செய்யும் போது இரண்டு டெர்மினல்களைப் பயன்படுத்தவும்:

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

`http://localhost:5173/v2/` ஐத் திறக்கவும். Vite `/api` கோரிக்கைகளை
`http://localhost:8900` க்கு ப்ராக்ஸி செய்கிறது, எனவே React ஆப் கூடுதல்
CORS அமைப்பு இல்லாமல் உள்ளூர் Flask சர்வருடன் பேசலாம்.

Python பேக்கேஜுடன் அனுப்பப்படும் பண்டிலை உருவாக்க:

```bash
cd frontend
npm run build
```

உற்பத்தி பண்டில் `clawmetry/static/v2/dist/` இல் எழுதப்படுகிறது.

## ரன்டைம் / ஏஜென்ட் இணக்கத்தன்மை

ClawMetry OpenClaw மட்டுமல்ல, பல AI-ஏஜென்ட் ரன்டைம்களைக் கவனிக்கிறது. OpenClaw அல்லாத ஒவ்வொரு ரன்டைமும் அதன் சொந்த அமர்வு வடிவத்தை ClawMetry-இன் ஒருங்கிணைந்த வடிவங்களாக மொழிபெயர்க்கும் ஒரு அர்ப்பணிப்பு reader adapter-ஐ வழங்குகிறது; டீமன் அவற்றை அதே DuckDB ஸ்டோர் + கிளவுட் ஸ்னாப்ஷாட்டில் உள்ளீடு செய்கிறது, ரன்டைமுடன் குறியிடப்பட்டு, ஒன்றுக்கு மேற்பட்ட ரன்டைம் இருக்கும்போது Session replay தாவல் ஒரு **ரன்டைம் ஸ்விட்சரைக்** காட்டுகிறது. முழு மேட்ரிக்ஸ் + ரன்டைம்களைச் சேர்ப்பதற்கான வழிகாட்டிக்கு [`docs/compatibility.md`](docs/compatibility.md) ஐயும், OpenClaw-குடும்ப அறிமுகத்திற்கு [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ஐயும் பார்க்கவும்.

| ரன்டைம் / ஏஜென்ட் | நிலை | குறிப்புகள் |
|---|---|---|
| **OpenClaw** | நேட்டிவ் | குறிப்பு ரன்டைம், தானாகக் கண்டறியப்படுகிறது |
| **PicoClaw** | பீட்டா அடாப்டர் | ஃபிளாட் `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள். |
| **NanoClaw** | பீட்டா அடாப்டர் | அமர்வுக்கு ஒரு SQLite (`data/v2-sessions`). டிரான்ஸ்கிரிப்ட்கள் + செய்தி எண்ணிக்கைகள். |
| **Hermes** | பீட்டா அடாப்டர் | SQLite `~/.hermes/state.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன்கள்/செலவு. |
| **Claude Code** | பீட்டா அடாப்டர் | JSONL `~/.claude/projects/.../<id>.jsonl`. டிரான்ஸ்கிரிப்ட்கள், மாடல், சிந்தனையுடன் கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Codex** | பீட்டா அடாப்டர் | ரோலவுட் JSONL `~/.codex/sessions/...`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Cursor** | பீட்டா அடாப்டர் | SQLite `state.vscdb`. சாட்/காம்போசர் டிரான்ஸ்கிரிப்ட்கள், மாடல். |
| **Aider** | பீட்டா அடாப்டர் | ஒவ்வொரு திட்டத்திற்கும் `.aider.chat.history.md`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன் எண்ணிக்கைகள். |
| **Goose** | பீட்டா அடாப்டர் | SQLite `~/.local/share/goose`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் மொத்தங்கள். |
| **opencode** | பீட்டா அடாப்டர் | SQLite `~/.local/share/opencode`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Qwen Code** | பீட்டா அடாப்டர் | JSONL `~/.qwen/projects/.../chats`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Pi** | பீட்டா அடாப்டர் | JSONL `~/.pi/agent/sessions`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Deep Agents** | பீட்டா அடாப்டர் | SQLite `~/.deepagents/.state/sessions.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **n8n** | பீட்டா அடாப்டர் | SQLite `~/.n8n/database.sqlite`. வொர்க்ஃப்ளோ செயலாக்கங்கள், நோட் இயக்கங்கள், AI Agent ப்ராம்ப்ட்கள், n8n பதிவு செய்யும் இடங்களில் மாடல் + டோக்கன்கள். |

"பீட்டா அடாப்டர்" என்பது அந்த ரன்டைமின் உண்மையான ஆன்-டிஸ்க் வடிவத்திற்கான reader-ஐ ClawMetry வழங்குகிறது என்பதைக் குறிக்கிறது, ஒவ்வொன்றும் ஒரு உண்மையான மெஷினில் உண்மையான நிறுவலுக்கு எதிராக உருவாக்கப்பட்டு + சரிபார்க்கப்பட்டது (`tests/fixtures/runtimes/<rt>/` ஐப் பார்க்கவும்). அடாப்டர்கள் ரீட்-ஓன்லி; ஒவ்வொன்றும் அதன் ரன்டைம் உண்மையில் என்ன சேமிக்கிறது என்பதைப் பற்றி நேர்மையானது (எ.கா. PicoClaw/NanoClaw/Cursor டிஸ்கில் டோக்கன் செலவை எழுதுவதில்லை). ஒரு நோடில் பல ரன்டைம்கள் இயங்கும்போது, ரன்டைம் ஸ்விட்சர் தூய்மையான ஆழமான-ஆய்வுக்காக அமர்வுகள் காட்சியை ஒன்றுக்கு வரம்பிடுகிறது.

## எந்த SDK ஏஜென்ட்டையும் கண்காணிக்கவும் — அவுட்-லூப் செலவு பண்புகூறல்

மேலே உள்ள ரன்டைம்கள் அனைத்தும் அமர்வுகளை டிஸ்கில் எழுதுகின்றன. நீங்கள் OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, அல்லது ஒரு சாதாரண `httpx` லூப்பில் உருவாக்கிய உங்கள் சொந்த **உற்பத்தி ஏஜென்ட்** அவ்வாறு செய்யாது. `httpx`/`requests` ஐ மங்கிப்-படைப்பதன் மூலம் ClawMetry-இன் கட்டமைப்பு தேவையில்லாத இன்டர்செப்டர் இன்னும் அதன் LLM அழைப்புகளை (செலவு, டோக்கன்கள், தாமதம், பிழைகள்) கைப்பற்றுகிறது:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (அல்லது `CLAWMETRY_SOURCE=support-agent` env var) ஒவ்வொரு அழைப்பையும் ஒரு **பெயரிடப்பட்ட மூலத்துடன்** குறியிடுகிறது, எனவே நீங்கள் இயக்கும் ஒவ்வொரு தயாரிப்பும் டாஷ்போர்டின் Overview-இல் உள்ள **🔌 அவுட்-லூப் மூலங்கள்** கார்டில் தனிப்பட்ட, செலவு-பண்புகூறக்கூடிய வரியாகக் காட்டப்படும் - அழைப்புகள், வழங்குநர்கள், தாமதம், ஏஜென்ட் ஒன்றுக்கு பிழை விகிதம். மூலம் அமைக்கப்படவில்லையா? அழைப்புகள் இன்னும் கண்காணிக்கப்படுகின்றன; கார்டு மட்டும் மறைந்தே இருக்கும்.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

இது ரன்டைம் அடாப்டர்கள் ஊட்டும் அதே தரவு அடுக்கு (DuckDB → கிளவுட் ஸ்னாப்ஷாட்), எனவே அவுட்-லூப் மூலங்கள் மற்ற அனைத்தையும் போலவே கிளவுட் டாஷ்போர்டுக்கு ஒத்திசைக்கப்படுகின்றன, E2E-குறியாக்கம் செய்யப்பட்டு.

## OpenTelemetry — வழங்குநர்-நடுநிலை, உங்கள் டிரேஸ்களை எங்கும் அனுப்புங்கள்

ClawMetry இரு திசைகளிலும் **OpenTelemetry** பேசுகிறது, **GenAI சொற்பொருள் மரபுகளைப்** பயன்படுத்தி, எனவே உங்கள் ஏஜென்ட் டிரேஸ்கள் ஒரு கருவியில் ஒருபோதும் பூட்டப்படாது.

ஒவ்வொரு அமர்வையும் - LLM அழைப்புகள், கருவிகள், துணை-ஏஜென்ட்கள், டோக்கன்கள், செலவு - எந்த கலெக்டருக்கும் (Datadog, Grafana, Honeycomb, அல்லது உங்கள் சொந்த OTel Collector) OTLP/HTTP GenAI spans ஆக **ஏற்றுமதி** செய்யவும்:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

அங்கீகார ஹெடர்கள் மற்றும் போல் இடைவெளி விருப்ப env vars:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**உள்ளீடு** — உள்ளமைந்த OTLP ரிசீவர் `/v1/traces` மற்றும் `/v1/metrics` இல் மற்ற எதிலிருந்தும் டிரேஸ்கள் மற்றும் மெட்ரிக்குகளை ஏற்கிறது (protobuf உள்ளீட்டுக்கு `pip install clawmetry[otel]`).

நீங்கள் கட்டமைப்பு தேவையில்லாத, லோக்கல்-முதல் ClawMetry டாஷ்போர்டையும், உங்கள் அணி ஏற்கனவே இயக்கும் எந்த பேக்கெண்டிலும் உங்கள் தரவையும் பெறுவீர்கள் - பூட்டு இல்லை, இரண்டாவது ஏஜென்ட் நிறுவ வேண்டியதில்லை.

## கட்டமைப்பு

பெரும்பாலான மக்களுக்கு எந்த கட்டமைப்பும் தேவையில்லை. ClawMetry உங்கள் பணியிடம், பதிவுகள், அமர்வுகள் மற்றும் க்ரான்களை தானாகவே கண்டறிகிறது.

நீங்கள் தனிப்பயனாக்க வேண்டுமெனில்:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

அனைத்து விருப்பங்களும்: `clawmetry --help`

## ஆதரிக்கப்படும் சேனல்கள்

நீங்கள் கட்டமைத்துள்ள ஒவ்வொரு OpenClaw சேனலுக்கும் ClawMetry நேரடி செயல்பாட்டைக் காட்டுகிறது. உங்கள் `openclaw.json` இல் உண்மையில் அமைக்கப்பட்ட சேனல்கள் மட்டுமே Flow வரைபடத்தில் தோன்றும் - கட்டமைக்கப்படாதவை தானாகவே மறைக்கப்படும்.

வருகை/வெளிச்செல்லும் செய்தி எண்ணிக்கைகளுடன் நேரடி சாட் பப்பிள் காட்சியைப் பார்க்க Flow-இல் எந்த சேனல் நோடையும் கிளிக் செய்யவும்.

| சேனல் | நிலை | நேரடி பாப்அப் | குறிப்புகள் |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ முழுமையானது | ✅ | செய்திகள், புள்ளிவிவரங்கள், 10s புதுப்பிப்பு |
| 💬 **iMessage** | ✅ முழுமையானது | ✅ | `~/Library/Messages/chat.db` ஐ நேரடியாகப் படிக்கிறது |
| 💚 **WhatsApp** | ✅ முழுமையானது | ✅ | WhatsApp Web (Baileys) மூலம் |
| 🔵 **Signal** | ✅ முழுமையானது | ✅ | signal-cli மூலம் |
| 🟣 **Discord** | ✅ முழுமையானது | ✅ | குயில்ட் + சேனல் கண்டறிதல் |
| 🟪 **Slack** | ✅ முழுமையானது | ✅ | பணியிடம் + சேனல் கண்டறிதல் |
| 🌐 **Webchat** | ✅ முழுமையானது | ✅ | உள்ளமைந்த வெப் UI அமர்வுகள் |
| 📡 **IRC** | ✅ முழுமையானது | ✅ | டெர்மினல்-பாணி பப்பிள் UI |
| 🍏 **BlueBubbles** | ✅ முழுமையானது | ✅ | BlueBubbles REST API வழியாக iMessage |
| 🔵 **Google Chat** | ✅ முழுமையானது | ✅ | Chat API வெப்ஹூக்குகள் மூலம் |
| 🟣 **MS Teams** | ✅ முழுமையானது | ✅ | Teams bot ப்ளக்இன் மூலம் |
| 🔷 **Mattermost** | ✅ முழுமையானது | ✅ | சுய-ஹோஸ்ட் செய்யப்பட்ட குழு அரட்டை |
| 🟩 **Matrix** | ✅ முழுமையானது | ✅ | பரவலாக்கப்பட்ட, E2EE ஆதரவு |
| 🟢 **LINE** | ✅ முழுமையானது | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ முழுமையானது | ✅ | பரவலாக்கப்பட்ட NIP-04 DMs |
| 🟣 **Twitch** | ✅ முழுமையானது | ✅ | IRC இணைப்பு மூலம் அரட்டை |
| 🔷 **Feishu/Lark** | ✅ முழுமையானது | ✅ | WebSocket நிகழ்வு சந்தா |
| 🔵 **Zalo** | ✅ முழுமையானது | ✅ | Zalo Bot API |

> **தானியங்கு கண்டறிதல்:** ClawMetry உங்கள் `~/.openclaw/openclaw.json` ஐப் படித்து, நீங்கள் உண்மையில் கட்டமைத்த சேனல்களை மட்டுமே காட்டுகிறது. கைமுறை அமைப்பு தேவையில்லை.

## Docker வரிசைப்படுத்தல்

ClawMetry-ஐ ஒரு கன்டெய்னரில் இயக்க விரும்புகிறீர்களா? பிரச்சனை இல்லை! 🐳

**Docker உடன் விரைவு தொடக்கம்:**

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

**Docker Compose உதாரணம்:**

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

> **குறிப்பு:** Docker-இல் இயங்கும்போது, ClawMetry உங்கள் அமைப்பை தானாகக் கண்டறிய, உங்கள் ஏஜென்டின் தரவு + பதிவு அடைவுகளை (எ.கா. `~/.openclaw`, `~/.claude`, `~/.codex`) மவுன்ட் செய்யவும்.

## தேவைகள்

- Python 3.8+
- Flask (pip வழியாக தானாக நிறுவப்படும்)
- அதே மெஷினில் ஒரு AI ஏஜென்ட் ரன்டைம்: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, அல்லது n8n (அல்லது Docker-க்கான மவுன்ட் செய்யப்பட்ட வால்யூம்கள்)
- Linux அல்லது macOS

## NemoClaw / OpenShell ஆதரவு

ClawMetry தானாகவே [NemoClaw](https://github.com/NVIDIA/NemoClaw) ஐக் கண்டறிகிறது — சான்ட்பாக்ஸ் செய்யப்பட்ட OpenShell கன்டெய்னர்களுக்குள் ஏஜென்ட்களை இயக்கும் OpenClaw-க்கான NVIDIA-இன் நிறுவன பாதுகாப்பு ரேப்பர்.

பெரும்பாலான நிகழ்வுகளில் கூடுதல் கட்டமைப்பு தேவையில்லை. அமர்வு கோப்புகள் ஹோஸ்டில் `~/.openclaw/` இல் இருந்தாலும் அல்லது OpenShell கன்டெய்னருக்குள் இருந்தாலும் சிங்க் டீமன் தானாகவே கண்டுபிடிக்கிறது.

### இது எப்படி வேலை செய்கிறது

ClawMetry NemoClaw ஐ இரண்டு வழிகளில் கண்டறிகிறது:

1. **பைனரி கண்டறிதல்** — `nemoclaw` CLI-க்காக சரிபார்த்து, சான்ட்பாக்ஸ் தகவலைப் பெற `nemoclaw status` ஐ இயக்குகிறது
2. **கன்டெய்னர் கண்டறிதல்** — `openshell`, `nemoclaw`, அல்லது `ghcr.io/nvidia/` இமேஜ்களுக்காக இயங்கும் Docker கன்டெய்னர்களை ஸ்கேன் செய்து, பின்னர் வால்யூம் மவுன்ட்கள் அல்லது `docker cp` வழியாக அமர்வுகளைப் படிக்கிறது

NemoClaw கன்டெய்னர்களிலிருந்து ஒத்திசைக்கப்பட்ட அமர்வு கோப்புகள் கிளவுட் டாஷ்போர்டில் `runtime=nemoclaw` மற்றும் `container_id` மெட்டாடேட்டாவுடன் குறியிடப்படுகின்றன, எனவே நீங்கள் அவற்றை நிலையான OpenClaw அமர்வுகளிலிருந்து ஒரு பார்வையில் வேறுபடுத்திப் பார்க்கலாம்.

### பரிந்துரைக்கப்பட்ட அமைப்பு: HOST இல் சிங்க் டீமன்

சிறந்த அனுபவத்திற்கு, ClawMetry-இன் சிங்க் டீமனை **ஹோஸ்ட் மெஷினில்** (சான்ட்பாக்ஸிற்குள் அல்ல) இயக்கவும். இது NemoClaw நெட்வொர்க் கொள்கை கட்டுப்பாடுகளைத் தவிர்க்கிறது.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

இயங்கும் எந்த OpenShell கன்டெய்னர்களுக்குள்ளும் இருக்கும் அமர்வுகளை சிங்க் டீமன் தானாகவே கண்டுபிடிக்கும்.

### விருப்பம்: வெளிப்படையான சான்ட்பாக்ஸ் பெயர்

தானியங்கு கண்டறிதல் வேலை செய்யவில்லை என்றால், சரியான சான்ட்பாக்ஸை ClawMetry-க்குக் காட்டவும்:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### சான்ட்பாக்ஸிற்குள் இயக்குதல் (மேம்பட்டது)

நீங்கள் சிங்க் டீமனை OpenShell சான்ட்பாக்ஸிற்குள் **உள்ளே** இயக்க வேண்டுமெனில், ClawMetry ingest API ஐ அடைய முடியும்படி உங்கள் NemoClaw நெட்வொர்க் கொள்கையில் இந்த egress விதியைச் சேர்க்கவும்:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

இதனுடன் பயன்படுத்தவும்:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### போர்ட்கள் மற்றும் இறுதிப்புள்ளிகள்

| இறுதிப்புள்ளி | போர்ட் | நெறிமுறை | தேவை |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ஆம் (சிங்க் டீமன் → கிளவுட்) |
| `localhost:8900` | 8900 | HTTP | ஆம் (உள்ளூர் டாஷ்போர்டு UI) |
| Docker சாக்கெட் (`/var/run/docker.sock`) | — | Unix சாக்கெட் | கன்டெய்னர் அமர்வு கண்டறிதலுக்கு |

சிங்க் டீமன் `ingest.clawmetry.com` க்கு மட்டுமே அவுட்பவுண்ட் HTTPS அழைப்புகளை செய்கிறது. இன்பவுண்ட் போர்ட்கள் தேவையில்லை.

---

## கிளவுட் வரிசைப்படுத்தல்

SSH டன்னல்கள், ரிவர்ஸ் ப்ராக்ஸி, மற்றும் Docker-க்கு **[கிளவுட் சோதனை வழிகாட்டி](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ஐப் பார்க்கவும்.

## சோதனை

இந்த திட்டம் BrowserStack உடன் சோதிக்கப்படுகிறது.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## டெலிமெட்ரி

புதிய மெஷினில் `clawmetry` CLI ஐ முதன்முறையாக இயக்கும்போது ClawMetry
`https://app.clawmetry.com/api/install` க்கு ஒரு அனாமிக "முதல் இயக்க" பிங்கை
அனுப்புகிறது. நிறுவல்களை எண்ணிக்கை செய்ய (OSS திட்டத்திற்கான
எங்களிடம் இருக்கும் ஒரே மார்க்கெட்டிங் மெட்ரிக்) மற்றும் எங்கள் பயனர்கள்
எந்த ஏஜென்ட் ஃப்ரேம்வொர்க்குகளை நிறுவியுள்ளனர் என்பதை அறிய இதைப் பயன்படுத்துகிறோம்.

**நிறுவலுக்கு சரியாக ஒரு POST**, கீழ்க்காணும் தகவல்களைக் கொண்டது:

| புலம் | உதாரணம் | ஏன் |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` இல் சேமிக்கப்பட்ட ரேண்டம் UUID | dedup; உங்கள் மின்னஞ்சல் அல்லது api_key உடன் இணைக்கப்படவில்லை |
| `version` | `0.12.167` | காட்டில் என்ன பதிப்புகள் உள்ளன |
| `os` / `os_version` | `Darwin` / `25.3.0` | பிளாட்பாரம் ஆதரவு முன்னுரிமைகள் |
| `python` | `3.11.15` | Python பதிப்பு ஆதரவு மேட்ரிக்ஸ் |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | அடுத்து எந்த ஏஜென்ட்களுடன் நாங்கள் ஒருங்கிணைக்க வேண்டும் |
| `is_ci` / `ci_provider` | `true` / `github_actions` | மனித நிறுவல்களை CI சத்தத்திலிருந்து பிரிக்கவும் |

**நாங்கள் அனுப்பாதவை**: IP (கிளவுட் சர்வர் பக்கத்தில் கோரிக்கையிலிருந்து
நாட்டுக் குறியீட்டைப் பெற்று, பின்னர் IP ஐ நிராகரிக்கிறது), ஹோஸ்ட்நேம், பயனர்பெயர், பணியிடப் பாதை, கோப்பு உள்ளடக்கங்கள், உங்கள் api_key, உங்கள் மின்னஞ்சல், PII அல்லது
பணியிடம்-குறிப்பிட்ட எதுவும். வயர் பேலோட்
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) இல் தணிக்கை செய்யக்கூடியது.

**விலகல்** (இவற்றில் ஏதேனும் ஒன்று அதை நிரந்தரமாக முடக்கும்):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

இங்கு ஒரு நெட்வொர்க் தோல்வி ஒருபோதும் `clawmetry` இயங்குவதைத் தடுக்காது - பிங் 3s காலக்கெடுவுடன் ஒரு டீமன் த்ரெட்டில் ஃபயர்-அண்ட்-ஃபர்கெட் ஆகும்.

## நட்சத்திர வரலாறு

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## உரிமம்

MIT

---

<p align="center">
  <strong>🦞 உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்</strong><br>
  <sub>உருவாக்கியவர் <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> சூழல்தொகுதியின் ஒரு பகுதி</sub>
</p>
