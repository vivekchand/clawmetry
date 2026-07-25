<!-- i18n-src:8f42d460a973 -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்.** **14 AI ஏஜென்ட் ரன்டைம்களுக்கான** நிகழ்நேர கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex மற்றும் மேலும் 10. உங்கள் முழு ஏஜென்ட் கூட்டத்திற்கும் ஒரே டாஷ்போர்டு.

> 🌐 **இதை இந்த மொழிகளில் படியுங்கள்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. எந்த கட்டமைப்பும் தேவையில்லை. எல்லாவற்றையும் தானாகவே கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும், முடிந்தது.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

ClawMetry ஆரம்பத்தில் OpenClaw க்கான கண்காணிப்புக் கருவியாக இருந்தது, இப்போது உங்கள் **முழு ஏஜென்ட் கூட்டத்தையும்** ஒரே டாஷ்போர்டில் அளவிடுகிறது, உங்கள் கணினியில் உள்ள ஒவ்வொரு ரன்டைமையும் தானாகவே கண்டறிந்து:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw மற்றும் NemoClaw திறந்த மூலப் பயன்பாட்டில் இலவசம்; மற்ற ரன்டைம்கள் ClawMetry Cloud அல்லது சுய-நேர்த்தி Pro உரிமத்துடன் செயல்படுகின்றன. தலைப்பிலிருந்து ரன்டைம்களை மாற்றவும், ஒவ்வொரு தாவலும் - செலவு, டோக்கன்கள், கருவிகள், தடங்கள் - அந்த ரன்டைமிற்கு மீண்டும் வரையறுக்கப்படும். துல்லியமான இலவச/கட்டணச் சிதைவு, அடுக்கு அணி, `/api/entitlement` வடிவம், மற்றும் `clawmetry license` CLI க்கு **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ஐக் காணவும்.

## நீங்கள் பெறுவது

- **Flow** - சேனல்கள், மூளை, கருவிகள் வழியாக சென்று திரும்பும் செய்திகளின் ஓட்டத்தைக் காட்டும் நேரடி அசைவூட்ட வரைபடம்
- **Overview** - சுகாதார சோதனைகள், செயல்பாட்டு வெப்பவரைபடம், அமர்வு எண்ணிக்கைகள், மாதிரி தகவல்
- **Usage** - தினசரி/வாராந்திர/மாதாந்திர பிரிவுகளுடன் டோக்கன் மற்றும் செலவு கண்காணிப்பு
- **Sessions** - மாதிரி, டோக்கன்கள், கடைசி செயல்பாட்டுடன் கூடிய தீவிர ஏஜென்ட் அமர்வுகள்
- **Crons** - நிலை, அடுத்த இயக்கம், கால அளவுடன் திட்டமிடப்பட்ட வேலைகள்
- **Logs** - வண்ணக் குறியீடு செய்யப்பட்ட நிகழ்நேர பதிவு ஸ்ட்ரீமிங்
- **Memory** - SOUL.md, MEMORY.md, AGENTS.md, தினசரிக் குறிப்புகளை உலாவுங்கள்
- **Transcripts** - அமர்வு வரலாறுகளைப் படிக்க அரட்டைக் குமிழி UI
- **Alerts** - பட்ஜெட் வரம்புகள், பிழை-விகிதத் தூண்டிகள், ஏஜென்ட்-ஆஃப்லைன் கண்டறிதல்; Slack, Discord, PagerDuty, Telegram, Email க்கு அனுப்புகிறது
- **Approvals** - அழிக்கும் நீக்கங்கள், கட்டாயப் புஷ்கள், DB மாற்றங்கள், sudo, பேக்கேஜ் நிறுவல்கள், நெட்வொர்க் அழைப்புகளை ஒரு-கிளிக் ஒப்புதலுக்குப் பின்னால் தடுக்கவும்

## ஸ்கிரீன்ஷாட்கள்

### 🧠 Brain - நேரடி ஏஜென்ட் நிகழ்வு ஸ்ட்ரீம்
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview - டோக்கன் பயன்பாடு & அமர்வுச் சுருக்கம்
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow - நிகழ்நேர கருவி அழைப்பு ஊட்டம்
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens - மாதிரி & அமர்வு வாரியான செலவுப் பிரிவு
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory - பணியிடக் கோப்பு உலாவி
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security - நிலைப்பாடு & தணிக்கைப் பதிவு
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts - பட்ஜெட் வரம்புகள், பிழை-விகிதத் தூண்டிகள், Slack / Discord / PagerDuty / Email க்கு வெப்ஹுக்குகள்
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals - ஆபத்தான கருவி அழைப்புகளை கைமுறை ஒப்புதலுக்குப் பின்னால் தடுக்கவும்; கொள்கை ஆதரவு பாதுகாப்பு விதிகள்
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## நிறுவுதல்

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

## v2 முன்முனை மேம்பாடு

v2 React பயன்பாடு `frontend/` இல் உள்ளது, மேலும் Flask சேவையகம் v2 இயக்கப்பட்ட நிலையில் தொடங்கப்படும்போது இது `/v2` இல் வழங்கப்படுகிறது.

மேம்படுத்தும்போது இரண்டு டெர்மினல்களைப் பயன்படுத்தவும்:

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
`http://localhost:8900` க்கு ப்ராக்ஸி செய்கிறது, எனவே React பயன்பாடு கூடுதல்
CORS அமைப்பு இல்லாமல் லோக்கல் Flask சேவையகத்துடன் தொடர்பு கொள்ள முடியும்.

Python பேக்கேஜுடன் அனுப்பப்படும் பண்டலை உருவாக்க:

```bash
cd frontend
npm run build
```

உற்பத்தி பண்டல் `clawmetry/static/v2/dist/` இல் எழுதப்படுகிறது.

## ரன்டைம் / ஏஜென்ட் இணக்கத்தன்மை

ClawMetry OpenClaw மட்டுமல்லாமல் பல AI-ஏஜென்ட் ரன்டைம்களையும் கண்காணிக்கிறது. OpenClaw அல்லாத ஒவ்வொரு ரன்டைமும் அதன் சொந்த அமர்வு வடிவமைப்பை ClawMetry இன் ஒருங்கிணைந்த வடிவங்களாக மொழிபெயர்க்கும் ஒரு பிரத்யேக ரீடர் அடாப்டரை வழங்குகிறது; daemon அவற்றை ரன்டைம் குறியிடப்பட்ட அதே DuckDB ஸ்டோர் + கிளவுட் ஸ்னாப்ஷாட்டில் இன்ஜெஸ்ட் செய்கிறது, மேலும் ஒன்றுக்கும் மேற்பட்ட ரன்டைம்கள் இருக்கும்போது Session replay தாவல் ஒரு **ரன்டைம் மாற்றியைக்** காட்டுகிறது. முழு அணி + ரன்டைம்களைச் சேர்ப்பதற்கான வழிகாட்டிக்கு [`docs/compatibility.md`](docs/compatibility.md) ஐயும், OpenClaw-குடும்ப அறிமுகத்திற்கு [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ஐயும் காணவும்.

| ரன்டைம் / ஏஜென்ட் | நிலை | குறிப்புகள் |
|---|---|---|
| **OpenClaw** | நேட்டிவ் | குறிப்பு ரன்டைம், தானாகக் கண்டறியப்பட்டது |
| **PicoClaw** | பீட்டா அடாப்டர் | தட்டையான `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள். |
| **NanoClaw** | பீட்டா அடாப்டர் | ஒரு அமர்வுக்கான SQLite (`data/v2-sessions`). டிரான்ஸ்கிரிப்ட்கள் + செய்தி எண்ணிக்கைகள். |
| **Hermes** | பீட்டா அடாப்டர் | SQLite `~/.hermes/state.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன்கள்/செலவு. |
| **Claude Code** | பீட்டா அடாப்டர் | JSONL `~/.claude/projects/.../<id>.jsonl`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள் + சிந்தனை, டோக்கன் பயன்பாடு. |
| **Codex** | பீட்டா அடாப்டர் | ரோலவுட் JSONL `~/.codex/sessions/...`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Cursor** | பீட்டா அடாப்டர் | SQLite `state.vscdb`. அரட்டை/கம்போசர் டிரான்ஸ்கிரிப்ட்கள், மாடல். |
| **Aider** | பீட்டா அடாப்டர் | ஒவ்வொரு திட்டத்திற்கும் `.aider.chat.history.md`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன் எண்ணிக்கைகள். |
| **Goose** | பீட்டா அடாப்டர் | SQLite `~/.local/share/goose`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் மொத்தங்கள். |
| **opencode** | பீட்டா அடாப்டர் | SQLite `~/.local/share/opencode`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Qwen Code** | பீட்டா அடாப்டர் | JSONL `~/.qwen/projects/.../chats`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Pi** | பீட்டா அடாப்டர் | JSONL `~/.pi/agent/sessions`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Deep Agents** | பீட்டா அடாப்டர் | SQLite `~/.deepagents/.state/sessions.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |

"பீட்டா அடாப்டர்" என்றால் ClawMetry அந்த ரன்டைமின் உண்மையான ஆன்-டிஸ்க் வடிவமைப்பிற்கான ரீடரை வழங்குகிறது என்பதாகும், ஒவ்வொன்றும் ஒரு உண்மையான கணினியில் உண்மையான நிறுவலுக்கு எதிராக உருவாக்கப்பட்டு + சரிபார்க்கப்பட்டது (`tests/fixtures/runtimes/<rt>/` ஐக் காணவும்). அடாப்டர்கள் படிக்க-மட்டும்; ஒவ்வொன்றும் அதன் ரன்டைம் உண்மையில் என்ன சேமிக்கிறது என்பதில் நேர்மையாக இருக்கும் (எ.கா. PicoClaw/NanoClaw/Cursor டோக்கன் செலவை டிஸ்கில் எழுதுவதில்லை). ஒரு நோடில் பல ரன்டைம்கள் இயங்கும்போது, ரன்டைம் மாற்றி அமர்வுகள் காட்சியை ஒரு சுத்தமான ஆழமான ஆய்வுக்காக ஒரே ஒன்றுக்கு வரையறுக்கிறது.

## எந்த SDK ஏஜென்டையும் கண்காணியுங்கள் - அவுட்-லூப் செலவு பங்கீடு

மேலே உள்ள ரன்டைம்கள் அனைத்தும் அமர்வுகளை டிஸ்கில் எழுதுகின்றன. நீங்கள் OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, அல்லது ஒரு சாதாரண `httpx` லூப்பில் கட்டமைத்த உங்கள் சொந்த **உற்பத்தி ஏஜென்ட்** அவ்வாறு செய்யாது. ClawMetry இன் ஜீரோ-கான்ஃபிக் இன்டர்செப்டர் `httpx`/`requests` ஐ மங்கி-பேட்ச் செய்வதன் மூலம் அதன் LLM அழைப்புகளை (செலவு, டோக்கன்கள், தாமதம், பிழைகள்) இன்னும் பிடிக்கிறது:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (அல்லது `CLAWMETRY_SOURCE=support-agent` env var) ஒவ்வொரு அழைப்பையும் ஒரு **பெயரிடப்பட்ட சோர்ஸுடன்** குறியிடுகிறது, எனவே நீங்கள் இயக்கும் ஒவ்வொரு தயாரிப்பும் Overview இல் உள்ள டாஷ்போர்டின் **🔌 Out-loop sources** கார்டில் அதன் சொந்த முதல்-வகுப்பு, செலவு-பங்கீடு செய்யக்கூடிய வரியாகத் தோன்றும் - ஒரு ஏஜென்டுக்கான அழைப்புகள், வழங்குநர்கள், தாமதம், பிழை விகிதம். சோர்ஸ் எதுவும் அமைக்கப்படவில்லையா? அழைப்புகள் இன்னும் கண்காணிக்கப்படும்; கார்டு மட்டும் மறைந்திருக்கும்.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

இது ரன்டைம் அடாப்டர்கள் ஊட்டும் அதே தரவு அடுக்கு (DuckDB → கிளவுட் ஸ்னாப்ஷாட்), எனவே அவுட்-லூப் சோர்ஸ்கள் மற்ற எல்லாவற்றையும் போலவே கிளவுட் டாஷ்போர்டுடன் ஒத்திசைக்கப்படுகின்றன, E2E-குறியாக்கம் செய்யப்பட்டவை.

## OpenTelemetry - வழங்குநர்-நடுநிலை, உங்கள் தடங்களை எங்கும் அனுப்புங்கள்

ClawMetry **GenAI செமான்டிக் கன்வென்ஷன்களைப்** பயன்படுத்தி இரு திசைகளிலும் **OpenTelemetry** பேசுகிறது, எனவே உங்கள் ஏஜென்ட் தடங்கள் ஒரு கருவியில் மட்டும் பூட்டப்படுவதில்லை.

ஒவ்வொரு அமர்வையும் - LLM அழைப்புகள், கருவிகள், துணை-ஏஜென்ட்கள், டோக்கன்கள், செலவு - எந்த கலெக்டருக்கும் (Datadog, Grafana, Honeycomb, அல்லது உங்கள் சொந்த OTel Collector) OTLP/HTTP GenAI ஸ்பான்களாக **ஏற்றுமதி** செய்யுங்கள்:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth ஹெடர்கள் மற்றும் போல் இடைவெளி விருப்பமான env vars ஆகும்:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** - உள்ளமைக்கப்பட்ட OTLP ரிசீவர் `/v1/traces` மற்றும் `/v1/metrics` இல் வேறு எதிலிருந்தும் தடங்கள் மற்றும் மெட்ரிக்குகளை ஏற்றுக்கொள்கிறது (protobuf இன்ஜெஸ்டுக்கு `pip install clawmetry[otel]`).

உங்களுக்கு ஜீரோ-கான்ஃபிக், லோக்கல்-முதல் ClawMetry டாஷ்போர்டு **மற்றும்** உங்கள் குழு ஏற்கனவே இயக்கும் எந்தப் பேக்எண்டிலும் உங்கள் தரவும் கிடைக்கும் - பூட்டு இல்லை, நிறுவ இரண்டாவது ஏஜென்ட் இல்லை.

## கட்டமைப்பு

பெரும்பாலானவர்களுக்கு எந்தக் கட்டமைப்பும் தேவையில்லை. ClawMetry உங்கள் பணியிடம், பதிவுகள், அமர்வுகள் மற்றும் cron களை தானாகவே கண்டறியும்.

தனிப்பயனாக்க வேண்டும் என்றால்:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

அனைத்து விருப்பங்களும்: `clawmetry --help`

## ஆதரிக்கப்படும் சேனல்கள்

நீங்கள் கட்டமைத்த ஒவ்வொரு OpenClaw சேனலுக்கும் ClawMetry நேரடி செயல்பாட்டைக் காட்டுகிறது. உங்கள் `openclaw.json` இல் உண்மையில் அமைக்கப்பட்ட சேனல்கள் மட்டுமே Flow வரைபடத்தில் தோன்றும் - கட்டமைக்கப்படாதவை தானாகவே மறைக்கப்படும்.

உள்வரும்/வெளிச்செல்லும் செய்தி எண்ணிக்கைகளுடன் கூடிய நேரடி அரட்டைக் குமிழி காட்சியைக் காண Flow இல் உள்ள எந்த சேனல் நோடையும் கிளிக் செய்யவும்.

| சேனல் | நிலை | நேரடி பாப்-அப் | குறிப்புகள் |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ முழு | ✅ | செய்திகள், புள்ளிவிவரங்கள், 10 வினாடி புதுப்பிப்பு |
| 💬 **iMessage** | ✅ முழு | ✅ | `~/Library/Messages/chat.db` ஐ நேரடியாகப் படிக்கிறது |
| 💚 **WhatsApp** | ✅ முழு | ✅ | WhatsApp Web (Baileys) வழியாக |
| 🔵 **Signal** | ✅ முழு | ✅ | signal-cli வழியாக |
| 🟣 **Discord** | ✅ முழு | ✅ | கில்ட் + சேனல் கண்டறிதல் |
| 🟪 **Slack** | ✅ முழு | ✅ | பணியிடம் + சேனல் கண்டறிதல் |
| 🌐 **Webchat** | ✅ முழு | ✅ | உள்ளமைக்கப்பட்ட வெப் UI அமர்வுகள் |
| 📡 **IRC** | ✅ முழு | ✅ | டெர்மினல்-பாணி குமிழி UI |
| 🍏 **BlueBubbles** | ✅ முழு | ✅ | BlueBubbles REST API வழியாக iMessage |
| 🔵 **Google Chat** | ✅ முழு | ✅ | Chat API வெப்ஹுக்குகள் வழியாக |
| 🟣 **MS Teams** | ✅ முழு | ✅ | Teams பாட் ப்ளக்இன் வழியாக |
| 🔷 **Mattermost** | ✅ முழு | ✅ | சுய-நேர்த்தி குழு அரட்டை |
| 🟩 **Matrix** | ✅ முழு | ✅ | பரவலாக்கப்பட்டது, E2EE ஆதரவு |
| 🟢 **LINE** | ✅ முழு | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ முழு | ✅ | பரவலாக்கப்பட்ட NIP-04 DM கள் |
| 🟣 **Twitch** | ✅ முழு | ✅ | IRC இணைப்பு வழியாக அரட்டை |
| 🔷 **Feishu/Lark** | ✅ முழு | ✅ | WebSocket நிகழ்வு சந்தா |
| 🔵 **Zalo** | ✅ முழு | ✅ | Zalo Bot API |

> **தானியங்கு கண்டறிதல்:** ClawMetry உங்கள் `~/.openclaw/openclaw.json` ஐப் படித்து, நீங்கள் உண்மையில் கட்டமைத்த சேனல்களை மட்டுமே காட்டுகிறது. கைமுறை அமைப்பு எதுவும் தேவையில்லை.

## Docker வரிசைப்படுத்தல்

ClawMetry ஐ ஒரு கன்டெய்னரில் இயக்க விரும்புகிறீர்களா? பிரச்சனையே இல்லை! 🐳

**Docker உடன் விரைவான தொடக்கம்:**

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

> **குறிப்பு:** Docker இல் இயக்கும்போது, ClawMetry உங்கள் அமைப்பைத் தானாகவே கண்டறிய, உங்கள் ஏஜென்டின் தரவு + பதிவுக் கோப்பகங்களை (எ.கா. `~/.openclaw`, `~/.claude`, `~/.codex`) மவுன்ட் செய்யவும்.

## தேவைகள்

- Python 3.8+
- Flask (pip வழியாகத் தானாக நிறுவப்படும்)
- அதே கணினியில் ஒரு AI ஏஜென்ட் ரன்டைம்: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, அல்லது Deep Agents (அல்லது Docker க்கான மவுன்ட் செய்யப்பட்ட வால்யூம்கள்)
- Linux அல்லது macOS

## NemoClaw / OpenShell ஆதரவு

ClawMetry தானாகவே [NemoClaw](https://github.com/NVIDIA/NemoClaw) ஐக் கண்டறிகிறது - இது சாண்ட்பாக்ஸ் செய்யப்பட்ட OpenShell கன்டெய்னர்களுக்குள் ஏஜென்ட்களை இயக்கும், OpenClaw க்கான NVIDIA இன் நிறுவன பாதுகாப்பு மேலாடை.

பெரும்பாலான சந்தர்ப்பங்களில் கூடுதல் கட்டமைப்பு தேவையில்லை. sync daemon அமர்வுக் கோப்புகளை, அவை ஹோஸ்டில் `~/.openclaw/` இல் இருந்தாலும் அல்லது OpenShell கன்டெய்னருக்குள் இருந்தாலும், தானாகவே கண்டுபிடிக்கிறது.

### இது எவ்வாறு செயல்படுகிறது

ClawMetry NemoClaw ஐ இரண்டு வழிகளில் கண்டறிகிறது:

1. **பைனரி கண்டறிதல்** - `nemoclaw` CLI ஐச் சரிபார்த்து, சாண்ட்பாக்ஸ் தகவலைப் பெற `nemoclaw status` ஐ இயக்குகிறது
2. **கன்டெய்னர் கண்டறிதல்** - இயங்கும் Docker கன்டெய்னர்களை `openshell`, `nemoclaw`, அல்லது `ghcr.io/nvidia/` இமேஜ்களுக்காக ஸ்கேன் செய்து, பின்னர் வால்யூம் மவுன்ட்கள் அல்லது `docker cp` வழியாக அமர்வுகளைப் படிக்கிறது

NemoClaw கன்டெய்னர்களிலிருந்து ஒத்திசைக்கப்பட்ட அமர்வுக் கோப்புகள் கிளவுட் டாஷ்போர்டில் `runtime=nemoclaw` மற்றும் `container_id` மெட்டாடேட்டாவுடன் குறியிடப்படுகின்றன, எனவே அவற்றை நிலையான OpenClaw அமர்வுகளிலிருந்து ஒரே பார்வையில் பிரித்தறியலாம்.

### பரிந்துரைக்கப்பட்ட அமைப்பு: HOST இல் sync daemon

சிறந்த அனுபவத்திற்கு, ClawMetry இன் sync daemon ஐ **ஹோஸ்ட் கணினியில்** இயக்கவும் (சாண்ட்பாக்ஸுக்குள் அல்ல). இது NemoClaw நெட்வொர்க் கொள்கைக் கட்டுப்பாடுகளைத் தவிர்க்கிறது.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon இயங்கும் எந்த OpenShell கன்டெய்னர்களுக்குள்ளும் உள்ள அமர்வுகளைத் தானாகவே கண்டுபிடிக்கும்.

### விருப்பம்: வெளிப்படையான சாண்ட்பாக்ஸ் பெயர்

தானியங்கு கண்டறிதல் வேலை செய்யவில்லை என்றால், ClawMetry ஐ சரியான சாண்ட்பாக்ஸை நோக்கிச் சுட்டவும்:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### சாண்ட்பாக்ஸுக்குள் இயக்குதல் (மேம்பட்டது)

sync daemon ஐ OpenShell சாண்ட்பாக்ஸுக்குள் **இயக்கவே** வேண்டும் என்றால், அது ClawMetry ingest API ஐ அடைய, உங்கள் NemoClaw நெட்வொர்க் கொள்கையில் இந்த egress விதியைச் சேர்க்கவும்:

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

### போர்ட்டுகள் மற்றும் எண்ட்பாயிண்ட்கள்

| எண்ட்பாயிண்ட் | போர்ட் | நெறிமுறை | தேவையா |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ஆம் (sync daemon → கிளவுட்) |
| `localhost:8900` | 8900 | HTTP | ஆம் (லோக்கல் டாஷ்போர்டு UI) |
| Docker சாக்கெட் (`/var/run/docker.sock`) | — | Unix சாக்கெட் | கன்டெய்னர் அமர்வு கண்டறிதலுக்காக |

sync daemon `ingest.clawmetry.com` க்கு மட்டுமே அவுட்பவுண்ட் HTTPS அழைப்புகளை மேற்கொள்கிறது. எந்த இன்பவுண்ட் போர்ட்டும் தேவையில்லை.

---

## கிளவுட் வரிசைப்படுத்தல்

SSH டன்னல்கள், ரிவர்ஸ் ப்ராக்ஸி, மற்றும் Docker க்கு **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ஐக் காணவும்.

## சோதனை

இந்தத் திட்டம் BrowserStack உடன் சோதிக்கப்படுகிறது.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## டெலிமெட்ரி

ClawMetry ஒரு புதிய கணினியில் `clawmetry` CLI ஐ முதல் முறையாக இயக்கும்போது
`https://app.clawmetry.com/api/install` க்கு ஒரே ஒரு அநாமதேய "முதல் இயக்கம்" பிங்
அனுப்புகிறது. நாங்கள் இதை நிறுவல்களை எண்ணிக்கை செய்யப் பயன்படுத்துகிறோம் (ஒரு OSS
திட்டத்திற்கு எங்களிடம் உள்ள ஒரே மார்க்கெட்டிங் அளவீடு இதுவே) மேலும் எங்கள் பயனர்கள்
எந்த ஏஜென்ட் ஃப்ரேம்வொர்க்குகளை நிறுவியிருக்கிறார்கள் என்பதை அறிந்துகொள்ளவும்.

**ஒரு நிறுவலுக்கு சரியாக ஒரு POST**, கொண்டிருப்பது:

| புலம் | உதாரணம் | ஏன் |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` இல் சேமிக்கப்பட்ட ரேண்டம் UUID | நகல் நீக்கம்; உங்கள் மின்னஞ்சல் அல்லது api_key உடன் இணைக்கப்படவில்லை |
| `version` | `0.12.167` | வெளியில் உள்ள பதிப்புகள் என்ன |
| `os` / `os_version` | `Darwin` / `25.3.0` | தளம் ஆதரவு முன்னுரிமைகள் |
| `python` | `3.11.15` | Python பதிப்பு ஆதரவு அணி |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | அடுத்து எந்த ஏஜென்ட்களுடன் நாங்கள் ஒருங்கிணைக்க வேண்டும் |
| `is_ci` / `ci_provider` | `true` / `github_actions` | மனித நிறுவல்களை CI சத்தத்திலிருந்து பிரிக்க |

**நாங்கள் அனுப்பாதவை**: IP (கிளவுட் கோரிக்கையிலிருந்து நாட்டுக் குறியீட்டை
சர்வர்-பக்கத்தில் பெற்றுக்கொண்டு, பின்னர் IP ஐ நிராகரிக்கிறது), ஹோஸ்ட்நேம், யூசர்நேம்,
பணியிடப் பாதை, கோப்பு உள்ளடக்கங்கள், உங்கள் api_key, உங்கள் மின்னஞ்சல், எந்த PII அல்லது
பணியிடம் சார்ந்த தகவலும் இல்லை. வயர் பேலோட்
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) இல் தணிக்கை செய்யக்கூடியது.

**விலகல்** (இவற்றில் ஏதேனும் ஒன்று இதை நிரந்தரமாக முடக்கும்):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

இங்கு ஒரு நெட்வொர்க் தோல்வி `clawmetry` இயங்குவதைத் தடுக்காது - பிங்
ஒரு daemon த்ரெட்டில் 3 வினாடி டைம்அவுட்டுடன் fire-and-forget ஆக அமைந்துள்ளது.

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> ஆல் உருவாக்கப்பட்டது · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> சூழல்தொகுப்பின் ஒரு பகுதி</sub>
</p>
