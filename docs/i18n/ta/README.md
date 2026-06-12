<!-- i18n-src:48548997be76 -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**உங்கள் ஏஜென்ட் சிந்திப்பதை பாருங்கள்.** **12 AI ஏஜென்ட் ரன்டைம்களுக்கான** நிகழ்நேர கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex மற்றும் 8 மேலும். உங்கள் முழு ஏஜென்ட் கூட்டத்திற்கும் ஒரே டாஷ்போர்டு.

> 🌐 **இதை இங்கே படியுங்கள்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. எந்த கட்டமைப்பும் தேவையில்லை. எல்லாவற்றையும் தானாகவே கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும், முடிந்தது.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 12 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

ClawMetry ஆரம்பத்தில் OpenClaw க்கான கண்காணிப்பு கருவியாக இருந்தது, இப்போது உங்கள் **முழு ஏஜென்ட் கூட்டத்தையும்** ஒரே டாஷ்போர்டில் அளவிடுகிறது, உங்கள் கணினியில் உள்ள ஒவ்வொரு ரன்டைமையும் தானாகவே கண்டறிகிறது:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw மற்றும் NemoClaw திறந்த மூல பயன்பாட்டில் இலவசம்; மற்ற ரன்டைம்கள் ClawMetry Cloud அல்லது சுய-நேர்த்தி Pro உரிமத்துடன் இயக்கப்படுகின்றன. தலைப்பிலிருந்து ரன்டைம்களை மாற்றவும், ஒவ்வொரு தாவலும் - செலவு, டோக்கன்கள், கருவிகள், தடங்கள் - அந்த ரன்டைமுக்கு மீண்டும் வரையறுக்கப்படும்.

## நீங்கள் பெறுவது

- **Flow**: சேனல்கள், மூளை, கருவிகள் வழியாக செய்திகள் பாயும் விதத்தை காட்டும் நேரடி அனிமேஷன் வரைபடம்
- **Overview**: சுகாதார சோதனைகள், செயல்பாட்டு வெப்பவரைபடம், அமர்வு எண்ணிக்கைகள், மாதிரி தகவல்
- **Usage**: தினசரி/வார/மாதாந்திர பிரிவுகளுடன் டோக்கன் மற்றும் செலவு கண்காணிப்பு
- **Sessions**: மாதிரி, டோக்கன்கள், கடைசி செயல்பாட்டுடன் தீவிர ஏஜென்ட் அமர்வுகள்
- **Crons**: நிலை, அடுத்த இயக்கம், கால அளவுடன் திட்டமிட்ட வேலைகள்
- **Logs**: வண்ண-குறியிடப்பட்ட நிகழ்நேர பதிவு ஸ்ட்ரீமிங்
- **Memory**: SOUL.md, MEMORY.md, AGENTS.md, தினசரி குறிப்புகளை உலாவுங்கள்
- **Transcripts**: அமர்வு வரலாறுகளை படிக்க அரட்டை-குமிழி UI
- **Alerts**: பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டிகள், ஏஜென்ட்-ஆஃப்லைன் கண்டறிதல்; Slack, Discord, PagerDuty, Telegram, Email க்கு வழிகாட்டுகிறது
- **Approvals**: அழிக்கும் நீக்கங்கள், வலுக்கட்டாயமான புஷ்கள், DB மாற்றங்கள், sudo, பேக்கேஜ் நிறுவல்கள், நெட்வொர்க் அழைப்புகளை ஒரு-கிளிக் ஒப்புதலுக்கு பின்னால் வைக்கவும்

## திரைப்படங்கள்

### 🧠 Brain - நேரடி ஏஜென்ட் நிகழ்வு ஸ்ட்ரீம்
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview - டோக்கன் பயன்பாடு மற்றும் அமர்வு சுருக்கம்
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow - நிகழ்நேர கருவி அழைப்பு ஊட்டம்
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens - மாதிரி மற்றும் அமர்வு வாரியான செலவு பிரிவு
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory - பணியிட கோப்பு உலாவி
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security - நிலை மற்றும் தணிக்கை பதிவு
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts - பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டிகள், Slack / Discord / PagerDuty / Email க்கு வெப்ஹுக்குகள்
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals - ஆபத்தான கருவி அழைப்புகளை கைமுறை ஒப்புதலுக்கு பின்னால் வைக்கவும்; கொள்கை-ஆதரவு பாதுகாப்பு விதிகள்
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## நிறுவல்

**ஒரு-வரி (பரிந்துரைக்கப்படுகிறது):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**மூல குறியிலிருந்து:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 முன்னிணை மேம்பாடு

v2 React பயன்பாடு `frontend/` இல் உள்ளது மற்றும் Flask சர்வர் v2 இயக்கப்பட்டு தொடங்கப்படும்போது `/v2` இல் வழங்கப்படுகிறது.

மேம்படுத்தும்போது இரண்டு டெர்மினல்களை பயன்படுத்தவும்:

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

`http://localhost:5173/v2/` திறக்கவும். Vite `/api` கோரிக்கைகளை `http://localhost:8900` க்கு ப்ராக்ஸி செய்கிறது, எனவே React பயன்பாடு கூடுதல் CORS அமைப்பு இல்லாமல் உள்ளூர் Flask சர்வருடன் தொடர்பு கொள்ளலாம்.

Python பேக்கேஜுடன் அனுப்பப்படும் தொகுப்பை உருவாக்க:

```bash
cd frontend
npm run build
```

உற்பத்தி தொகுப்பு `clawmetry/static/v2/dist/` க்கு எழுதப்படுகிறது.

## ரன்டைம் / ஏஜென்ட் இணக்கத்தன்மை

ClawMetry பல AI-ஏஜென்ட் ரன்டைம்களை கண்காணிக்கிறது, OpenClaw மட்டுமல்ல. OpenClaw அல்லாத ஒவ்வொரு ரன்டைமும் அதன் உள்ளூர் அமர்வு வடிவமைப்பை ClawMetry இன் ஒருங்கிணைந்த வடிவங்களாக மொழிபெயர்க்கும் ஒரு அர்ப்பணிப்பு வாசிப்பு அடாப்டரை அனுப்புகிறது; daemon அவற்றை அதே DuckDB சேமிப்பகம் மற்றும் கிளவுட் ஸ்னாப்ஷாட்டில் ரன்டைமுடன் குறியிட்டு உள்வாங்குகிறது, மேலும் அமர்வு மீண்டும் இயக்கும் தாவல் ஒன்றுக்கும் மேற்பட்டவை இருக்கும்போது ஒரு **ரன்டைம் மாற்றியை** காட்டுகிறது. முழு அணி மற்றும் ரன்டைம்களை சேர்ப்பதற்கான வழிகாட்டிக்கு [`docs/compatibility.md`](docs/compatibility.md) ஐ காணவும், OpenClaw-குடும்ப அறிமுகத்திற்கு [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ஐ காணவும்.

| ரன்டைம் / ஏஜென்ட் | நிலை | குறிப்புகள் |
|---|---|---|
| **OpenClaw** | நேரடி | குறிப்பு ரன்டைம், தானாகவே கண்டறியப்படும் |
| **PicoClaw** | Beta adapter | தட்டையான `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). டிரான்ஸ்கிரிப்ட்கள், மாதிரி, கருவி அழைப்புகள். |
| **NanoClaw** | Beta adapter | அமர்வு-வாரியான SQLite (`data/v2-sessions`). டிரான்ஸ்கிரிப்ட்கள் மற்றும் செய்தி எண்ணிக்கைகள். |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. டிரான்ஸ்கிரிப்ட்கள், மாதிரி, டோக்கன்கள்/செலவு. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. டிரான்ஸ்கிரிப்ட்கள், மாதிரி, கருவி அழைப்புகள் மற்றும் சிந்தனை, டோக்கன் பயன்பாடு. |
| **Codex** | Beta adapter | ரோலவுட் JSONL `~/.codex/sessions/...`. டிரான்ஸ்கிரிப்ட்கள், மாதிரி, கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. அரட்டை/கம்போஸர் டிரான்ஸ்கிரிப்ட்கள், மாதிரி. |
| **Aider** | Beta adapter | திட்டத்திற்கு ஒரு `.aider.chat.history.md`. டிரான்ஸ்கிரிப்ட்கள், மாதிரி, டோக்கன் எண்ணிக்கைகள். |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. டிரான்ஸ்கிரிப்ட்கள், மாதிரி, கருவி அழைப்புகள், டோக்கன் மொத்தங்கள். |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. டிரான்ஸ்கிரிப்ட்கள், மாதிரி, கருவி அழைப்புகள், டோக்கன்கள் மற்றும் செலவு. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. டிரான்ஸ்கிரிப்ட்கள், மாதிரி, கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |

"Beta adapter" என்பது ClawMetry அந்த ரன்டைமின் உண்மையான ஆன்-டிஸ்க் வடிவமைப்பிற்கான வாசிப்பாளரை அனுப்புகிறது என்பதாகும், ஒவ்வொன்றும் உண்மையான கணினியில் உண்மையான நிறுவலில் கட்டப்பட்டு சரிபார்க்கப்பட்டது (பார்க்கவும் `tests/fixtures/runtimes/<rt>/`). அடாப்டர்கள் படிக்கமட்டுமே; ஒவ்வொன்றும் அதன் ரன்டைம் உண்மையில் சேமிக்கும் என்பதில் நேர்மையானது (எ.கா. PicoClaw/NanoClaw/Cursor டோக்கன் செலவை டிஸ்கில் எழுதுவதில்லை). ஒரு முனையில் பல ரன்டைம்கள் இயங்கும்போது, ரன்டைம் மாற்றி அமர்வுகள் காட்சியை சுத்தமான ஆழமான ஆராய்வுக்காக ஒன்றிற்கு வரையறுக்கிறது.

## எந்த SDK ஏஜென்டையும் கண்காணியுங்கள் - அவுட்-லூப் செலவு காரணி

மேலே உள்ள ரன்டைம்கள் அனைத்தும் அமர்வுகளை டிஸ்கில் எழுதுகின்றன. நீங்கள் கட்டமைத்த **உற்பத்தி ஏஜென்ட்** - OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, அல்லது சாதாரண `httpx` லூப்பில் உருவாக்கப்பட்டது - அவ்வாறு செய்யாது. ClawMetry இன் ஜீரோ-கான்பிக் இடைமறிப்பான் `httpx`/`requests` ஐ மங்கி-பேட்சிங் மூலம் அதன் LLM அழைப்புகளை (செலவு, டோக்கன்கள், தாமதம், பிழைகள்) இன்னும் கைப்பற்றுகிறது:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (அல்லது `CLAWMETRY_SOURCE=support-agent` env var) ஒவ்வொரு அழைப்பையும் ஒரு **பெயரிடப்பட்ட மூலத்துடன்** குறியிடுகிறது, எனவே நீங்கள் இயக்கும் ஒவ்வொரு தயாரிப்பும் டாஷ்போர்டின் Overview இல் உள்ள **🔌 Out-loop sources** அட்டையில் தனது சொந்த முதல்-வகுப்பு, செலவு-காரணி வரியாக தோன்றும் - ஏஜென்டுக்கு அழைப்புகள், வழங்குனர்கள், தாமதம், பிழை விகிதம். மூலம் அமைக்கப்படவில்லையா? அழைப்புகள் இன்னும் கண்காணிக்கப்படுகின்றன; அட்டை மட்டும் மறைக்கப்படும்.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

இது ரன்டைம் அடாப்டர்கள் ஊட்டும் அதே தரவு அடுக்கு (DuckDB க்கு கிளவுட் ஸ்னாப்ஷாட்), எனவே அவுட்-லூப் மூலங்கள் கிளவுட் டாஷ்போர்டுக்கு மற்ற எல்லாவற்றையும் போல ஒத்திசைக்கப்படுகின்றன, E2E-குறியாக்கப்பட்டவை.

## OpenTelemetry - வழங்குனர்-நடுநிலை, உங்கள் தடங்களை எங்கும் அனுப்புங்கள்

ClawMetry **GenAI சிமான்டிக் கன்வென்ஷன்களை** பயன்படுத்தி இரு திசைகளிலும் **OpenTelemetry** பேசுகிறது, எனவே உங்கள் ஏஜென்ட் தடங்கள் ஒரு கருவியில் பூட்டப்படுவதில்லை.

ஒவ்வொரு அமர்வையும் - LLM அழைப்புகள், கருவிகள், துணை-ஏஜென்ட்கள், டோக்கன்கள், செலவு - OTLP/HTTP GenAI ஸ்பான்களாக எந்த கலெக்டருக்கும் (Datadog, Grafana, Honeycomb, அல்லது உங்கள் சொந்த OTel Collector) **ஏற்றுமதி** செய்யுங்கள்:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth தலைப்புகள் மற்றும் பட்ல் இடைவெளி விருப்ப env vars:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**உள்வாங்கு** - உள்ளமைக்கப்பட்ட OTLP ரிசீவர் `/v1/traces` மற்றும் `/v1/metrics` இல் மற்ற எதிலிருந்தும் தடங்கள் மற்றும் அளவீடுகளை ஏற்றுக்கொள்கிறது (`pip install clawmetry[otel]` protobuf உள்வாங்குக்கு).

ஜீரோ-கான்பிக், லோக்கல்-முதல் ClawMetry டாஷ்போர்டும் **மற்றும்** உங்கள் குழு ஏற்கனவே இயக்கும் எந்த பின்னணியிலும் உங்கள் தரவும் கிடைக்கும் - பூட்டு இல்லை, நிறுவ இரண்டாவது ஏஜென்ட் இல்லை.

## கட்டமைப்பு

பெரும்பாலானவர்களுக்கு எந்த கட்டமைப்பும் தேவையில்லை. ClawMetry உங்கள் பணியிடம், பதிவுகள், அமர்வுகள் மற்றும் cron ஐ தானாகவே கண்டறியும்.

தனிப்பயனாக்கம் தேவைப்பட்டால்:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

அனைத்து விருப்பங்களும்: `clawmetry --help`

## ஆதரிக்கப்படும் சேனல்கள்

ClawMetry நீங்கள் கட்டமைத்த ஒவ்வொரு OpenClaw சேனலுக்கும் நேரடி செயல்பாட்டை காட்டுகிறது. உங்கள் `openclaw.json` இல் உண்மையில் அமைக்கப்பட்ட சேனல்கள் மட்டுமே Flow வரைபடத்தில் தோன்றும் - கட்டமைக்கப்படாதவை தானாகவே மறைக்கப்படுகின்றன.

உள்வரும்/வெளிச்செல்லும் செய்தி எண்ணிக்கைகளுடன் நேரடி அரட்டை குமிழி காட்சியை காண Flow இல் எந்த சேனல் முனையையும் கிளிக் செய்யுங்கள்.

| சேனல் | நிலை | நேரடி பாப்-அப் | குறிப்புகள் |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ முழு | ✅ | செய்திகள், புள்ளிவிவரங்கள், 10 வினாடி புதுப்பிப்பு |
| 💬 **iMessage** | ✅ முழு | ✅ | `~/Library/Messages/chat.db` ஐ நேரடியாக படிக்கிறது |
| 💚 **WhatsApp** | ✅ முழு | ✅ | WhatsApp Web வழியாக (Baileys) |
| 🔵 **Signal** | ✅ முழு | ✅ | signal-cli வழியாக |
| 🟣 **Discord** | ✅ முழு | ✅ | Guild மற்றும் சேனல் கண்டறிதல் |
| 🟪 **Slack** | ✅ முழு | ✅ | பணியிடம் மற்றும் சேனல் கண்டறிதல் |
| 🌐 **Webchat** | ✅ முழு | ✅ | உள்ளமைக்கப்பட்ட web UI அமர்வுகள் |
| 📡 **IRC** | ✅ முழு | ✅ | டெர்மினல்-ஸ்டைல் குமிழி UI |
| 🍏 **BlueBubbles** | ✅ முழு | ✅ | BlueBubbles REST API வழியாக iMessage |
| 🔵 **Google Chat** | ✅ முழு | ✅ | Chat API webhooks வழியாக |
| 🟣 **MS Teams** | ✅ முழு | ✅ | Teams bot plugin வழியாக |
| 🔷 **Mattermost** | ✅ முழு | ✅ | சுய-நேர்த்தி குழு அரட்டை |
| 🟩 **Matrix** | ✅ முழு | ✅ | பரவலாக்கப்பட்டது, E2EE ஆதரவு |
| 🟢 **LINE** | ✅ முழு | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ முழு | ✅ | பரவலாக்கப்பட்ட NIP-04 DMs |
| 🟣 **Twitch** | ✅ முழு | ✅ | IRC இணைப்பு வழியாக அரட்டை |
| 🔷 **Feishu/Lark** | ✅ முழு | ✅ | WebSocket நிகழ்வு சந்தா |
| 🔵 **Zalo** | ✅ முழு | ✅ | Zalo Bot API |

> **தானியங்கு கண்டறிதல்:** ClawMetry உங்கள் `~/.openclaw/openclaw.json` ஐ படிக்கிறது மற்றும் நீங்கள் உண்மையில் கட்டமைத்த சேனல்களை மட்டுமே வழங்குகிறது. கைமுறை அமைப்பு தேவையில்லை.

## Docker வரிசைப்படுத்தல்

கொள்கலனில் ClawMetry ஐ இயக்க விரும்புகிறீர்களா? பிரச்சனையில்லை! 🐳

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

> **குறிப்பு:** Docker இல் இயங்கும்போது, ClawMetry உங்கள் அமைப்பை தானாகவே கண்டறிய ஏஜென்டின் தரவு மற்றும் பதிவு கோப்பகங்களை (எ.கா. `~/.openclaw`, `~/.claude`, `~/.codex`) இணைக்கவும்.

## தேவைகள்

- Python 3.8+
- Flask (pip வழியாக தானாக நிறுவப்படும்)
- அதே கணினியில் ஒரு AI ஏஜென்ட் ரன்டைம்: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, அல்லது PicoClaw (அல்லது Docker க்கான இணைக்கப்பட்ட தொகுதிகள்)
- Linux அல்லது macOS

## NemoClaw / OpenShell ஆதரவு

ClawMetry தானாகவே [NemoClaw](https://github.com/NVIDIA/NemoClaw) ஐ கண்டறிகிறது - OpenShell கொள்கலன்களுக்குள் ஏஜென்ட்களை இயக்கும் OpenClaw க்கான NVIDIA இன் நிறுவன பாதுகாப்பு மேலோடு.

பெரும்பாலான சந்தர்ப்பங்களில் கூடுதல் கட்டமைப்பு தேவையில்லை. sync daemon அமர்வு கோப்புகளை ஹோஸ்டில் `~/.openclaw/` இல் அல்லது OpenShell கொள்கலனுக்குள் இருந்தாலும் தானாகவே கண்டுபிடிக்கிறது.

### இது எவ்வாறு செயல்படுகிறது

ClawMetry NemoClaw ஐ இரண்டு வழிகளில் கண்டறிகிறது:

1. **பைனரி கண்டறிதல்** - `nemoclaw` CLI ஐ சரிபார்க்கிறது மற்றும் சாண்ட்பாக்ஸ் தகவல் பெற `nemoclaw status` ஐ இயக்குகிறது
2. **கொள்கலன் கண்டறிதல்** - `openshell`, `nemoclaw`, அல்லது `ghcr.io/nvidia/` படங்களுக்கான இயங்கும் Docker கொள்கலன்களை ஸ்கேன் செய்கிறது, பின்னர் தொகுதி இணைப்புகள் அல்லது `docker cp` வழியாக அமர்வுகளை படிக்கிறது

NemoClaw கொள்கலன்களிலிருந்து ஒத்திசைக்கப்பட்ட அமர்வு கோப்புகள் கிளவுட் டாஷ்போர்டில் `runtime=nemoclaw` மற்றும் `container_id` மெட்டாடேட்டாவுடன் குறியிடப்படுகின்றன, எனவே நீங்கள் அவற்றை நிலையான OpenClaw அமர்வுகளிலிருந்து ஒரு பார்வையில் வேறுபடுத்தலாம்.

### பரிந்துரைக்கப்பட்ட அமைப்பு: ஹோஸ்டில் sync daemon

சிறந்த அனுபவத்திற்கு, ClawMetry இன் sync daemon ஐ **ஹோஸ்ட் கணினியில்** (சாண்ட்பாக்ஸுக்குள் அல்ல) இயக்கவும். இது NemoClaw நெட்வொர்க் கொள்கை கட்டுப்பாடுகளை தவிர்க்கிறது.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon இயங்கும் எந்த OpenShell கொள்கலன்களுக்குள்ளும் உள்ள அமர்வுகளை தானாகவே கண்டுபிடிக்கும்.

### விருப்ப: வெளிப்படையான சாண்ட்பாக்ஸ் பெயர்

தானியங்கு கண்டறிதல் வேலை செய்யாவிட்டால், ClawMetry ஐ சரியான சாண்ட்பாக்ஸில் சுட்டிக்காட்டவும்:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### சாண்ட்பாக்ஸுக்குள் இயங்குதல் (மேம்பட்டது)

sync daemon ஐ OpenShell சாண்ட்பாக்ஸுக்குள் இயக்க வேண்டும் என்றால், ClawMetry ingest API ஐ அடைய உங்கள் NemoClaw நெட்வொர்க் கொள்கையில் இந்த egress விதியை சேர்க்கவும்:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

பயன்படுத்தவும்:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### போர்ட்டுகள் மற்றும் endpoints

| Endpoint | போர்ட் | நெறிமுறை | தேவையா |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ஆம் (sync daemon முதல் கிளவுட்) |
| `localhost:8900` | 8900 | HTTP | ஆம் (உள்ளூர் டாஷ்போர்ட் UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | கொள்கலன் அமர்வு கண்டறிதலுக்கு |

sync daemon `ingest.clawmetry.com` க்கு மட்டுமே வெளிச்செல்லும் HTTPS அழைப்புகளை செய்கிறது. உள்வரும் போர்ட்டுகள் தேவையில்லை.

---

## கிளவுட் வரிசைப்படுத்தல்

SSH டன்னல்கள், ரிவர்ஸ் ப்ராக்ஸி மற்றும் Docker க்கு **[கிளவுட் சோதனை வழிகாட்டி](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ஐ காணவும்.

## சோதனை

இந்த திட்டம் BrowserStack உடன் சோதிக்கப்படுகிறது.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## டெலிமெட்ரி

ClawMetry புதிய கணினியில் முதல் முறை `clawmetry` CLI ஐ இயக்கும்போது `https://app.clawmetry.com/api/install` க்கு ஒரே ஒரு அநாமதேய "முதல் இயக்கம்" ping அனுப்புகிறது. நாங்கள் இதை நிறுவல்களை எண்ண (ஒரு OSS திட்டத்திற்கு எங்களிடம் உள்ள ஒரே மார்க்கெட்டிங் அளவீடு) மற்றும் எந்த ஏஜென்ட் கட்டமைப்புகளை எங்கள் பயனர்கள் நிறுவியிருக்கிறார்கள் என்பதை அறிய பயன்படுத்துகிறோம்.

**நிறுவலுக்கு ஒரே ஒரு POST**, கொண்டிருக்கும்:

| புலம் | உதாரணம் | ஏன் |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` இல் சேமிக்கப்பட்ட சீரற்ற UUID | நகல் நீக்கம்; உங்கள் மின்னஞ்சல் அல்லது api_key உடன் இணைக்கப்படவில்லை |
| `version` | `0.12.167` | காட்டுப்பகுதியில் என்ன பதிப்புகள் உள்ளன |
| `os` / `os_version` | `Darwin` / `25.3.0` | தளம் ஆதரவு முன்னுரிமைகள் |
| `python` | `3.11.15` | Python பதிப்பு ஆதரவு அணி |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | அடுத்து எந்த ஏஜென்ட்களுடன் ஒருங்கிணைக்க வேண்டும் |
| `is_ci` / `ci_provider` | `true` / `github_actions` | மனித நிறுவல்களை CI சத்தத்திலிருந்து பிரிக்கவும் |

**நாங்கள் அனுப்பாதவை**: IP (கிளவுட் கோரிக்கையிலிருந்து நாட்டு குறியீட்டை சர்வர்-பக்கத்தில் பெறுகிறது, பின்னர் IP ஐ நிராகரிக்கிறது), hostname, பயனர்பெயர், பணியிட பாதை, கோப்பு உள்ளடக்கங்கள், உங்கள் api_key, உங்கள் மின்னஞ்சல், எந்த PII அல்லது பணியிட-குறிப்பிட்டவை. wire payload [`clawmetry/telemetry.py`](clawmetry/telemetry.py) இல் தணிக்கை செய்யத்தக்கது.

**விலகு** (இவற்றில் ஏதேனும் ஒன்று இதை நிரந்தரமாக முடக்கும்):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ஒரு நெட்வொர்க் தோல்வி `clawmetry` ஐ இயங்குவதிலிருந்து ஒருபோதும் தடுக்காது - ping ஒரு daemon thread இல் 3 வினாடி timeout உடன் fire-and-forget ஆகும்.

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
  <strong>🦞 உங்கள் ஏஜென்ட் சிந்திப்பதை பாருங்கள்</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> ஆல் கட்டப்பட்டது · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> சூழலின் பகுதி</sub>
</p>
