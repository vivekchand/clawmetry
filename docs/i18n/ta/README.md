<!-- i18n-src:02b789586c7d -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்.** **14 AI ஏஜென்ட் ரன்டைம்களுக்கான** நேரடி கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex மற்றும் மேலும் 10. உங்கள் முழு ஏஜென்ட் கூட்டத்திற்கும் ஒரே டாஷ்போர்டு.

> 🌐 **இதை இதில் படிக்கவும்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே ஒரு கட்டளை. கட்டமைப்பு தேவையில்லை. அனைத்தையும் தானாகவே கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும், அவ்வளவுதான்.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

ClawMetry OpenClaw-க்கான கண்காணிப்பாக தொடங்கியது, இப்போது உங்கள் **முழு ஏஜென்ட் கூட்டத்தையும்** ஒரே டாஷ்போர்டில் அளவிடுகிறது, உங்கள் மெஷினில் உள்ள ஒவ்வொரு ரன்டைமையும் தானாகவே கண்டறிந்து:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw மற்றும் NemoClaw ஓபன்-சோர்ஸ் ஆப்பில் இலவசம்; மற்ற ரன்டைம்கள் ClawMetry Cloud அல்லது சுய-ஹோஸ்ட் செய்யப்பட்ட Pro உரிமத்துடன் இயங்கும். ஹெடரிலிருந்து ரன்டைம்களை மாற்றவும், ஒவ்வொரு டேபும் — செலவு, டோக்கன்கள், டூல்கள், டிரேஸ்கள் — அந்த ரன்டைமிற்கு மீண்டும் வரம்பிடப்படும். சரியான இலவச/கட்டண பிரிவு, டையர் மேட்ரிக்ஸ், `/api/entitlement` வடிவம், மற்றும் `clawmetry license` CLI ஆகியவற்றுக்கு **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ஐப் பார்க்கவும்.

## நீங்கள் பெறுவது என்ன

- **Flow** — சேனல்கள், பிரெயின், டூல்கள் வழியாக மற்றும் மீண்டும் செய்திகள் பாய்வதைக் காட்டும் நேரடி அனிமேட்டட் வரைபடம்
- **Overview** — ஆரோக்கிய சோதனைகள், செயல்பாட்டு ஹீட்மேப், அமர்வு எண்ணிக்கைகள், மாடல் தகவல்
- **Usage** — தினசரி/வாராந்திர/மாதாந்திர பிரிவுகளுடன் டோக்கன் மற்றும் செலவு கண்காணிப்பு
- **Sessions** — மாடல், டோக்கன்கள், கடைசி செயல்பாடு ஆகியவற்றுடன் செயலில் உள்ள ஏஜென்ட் அமர்வுகள்
- **Crons** — நிலை, அடுத்த இயக்கம், கால அளவு ஆகியவற்றுடன் திட்டமிடப்பட்ட பணிகள்
- **Logs** — வண்ண-குறியிடப்பட்ட நேரடி பதிவு ஸ்ட்ரீமிங்
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, தினசரி குறிப்புகளை உலாவவும்
- **Transcripts** — அமர்வு வரலாறுகளைப் படிக்க சாட்-குமிழி UI
- **Alerts** — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், ஏஜென்ட்-ஆஃப்லைன் கண்டறிதல்; Slack, Discord, PagerDuty, Telegram, Email க்கு வழிநடத்துகிறது
- **Approvals** — அழிவுகரமான நீக்குதல்கள், ஃபோர்ஸ் புஷ்கள், DB மாற்றங்கள், sudo, தொகுப்பு நிறுவல்கள், நெட்வொர்க் அழைப்புகள் ஆகியவற்றை ஒரு-கிளிக் ஒப்புதலுக்குப் பின்னால் தடுக்கவும்

## திரைப்படங்கள்

### 🧠 Brain — நேரடி ஏஜென்ட் நிகழ்வு ஸ்ட்ரீம்
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — டோக்கன் பயன்பாடு & அமர்வு சுருக்கம்
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — நேரடி டூல் அழைப்பு ஃபீட்
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — மாடல் & அமர்வு வாரியான செலவு பிரிவு
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — பணியிடக் கோப்பு உலாவி
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — நிலைப்பாடு & தணிக்கை பதிவு
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், Slack / Discord / PagerDuty / Email க்கான webhook-கள்
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ஆபத்தான டூல் அழைப்புகளை கைமுறை ஒப்புதலுக்குப் பின்னால் தடுக்கவும்; பாலிசி-ஆதரவு பாதுகாப்பு விதிகள்
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-க்கான இயக்கத்திற்கு முந்தைய தடுப்பு** — ஒரு கட்டளை
பொருந்தும் டூல் அழைப்புகளை அவை இயங்குவதற்கு *முன்பே* இடைநிறுத்தி உங்கள்
முடிவுக்காக காத்திருக்கும் PreToolUse ஹூக்கை நிறுவுகிறது ([cloud push notifications](https://app.clawmetry.com/push)
இயக்கப்பட்டிருந்தால் உங்கள் ஃபோனிலிருந்து ஒரே ஒரு தட்டல்):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

deny செய்தால் அந்த ஒரு டூல் அழைப்பு மட்டும் தடுக்கப்படும் — ஏஜென்ட் தனது
அமர்வைத் தக்கவைத்துக்கொண்டு வேறு அணுகுமுறையை முயற்சிக்கலாம். உங்கள்
ஃபோனில் ஒப்புதல் அளிப்பது Claude Code-இன் சொந்த அனுமதி வேண்டுகோளைத்
தவிர்க்கிறது (நீங்கள் ஏற்கனவே பதிலளித்துவிட்டீர்கள்). பொருந்தாத டூல்கள்
~40ms செலவாகி Claude Code-இன் வழக்கமான அனுமதி ஓட்டத்திற்குள் விழும்.
Claude Code தானே உங்களுக்காக காத்திருக்கும்போதும் (`permission_prompt` /
`idle_prompt` அறிவிப்புகள்) உங்களுக்கு ஃபோன் புஷ் கிடைக்கும்.

## நிறுவல்

**ஒரு-லைனர் (பரிந்துரைக்கப்படுகிறது):**
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

## v2 Frontend மேம்பாடு

v2 React ஆப் `frontend/` இல் உள்ளது, மேலும் Flask
சர்வர் v2 இயக்கப்பட்ட நிலையில் தொடங்கப்படும்போது `/v2` இல் வழங்கப்படுகிறது.

மேம்பாட்டின் போது இரண்டு டெர்மினல்களைப் பயன்படுத்தவும்:

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
`http://localhost:8900` க்கு ப்ராக்ஸி செய்கிறது, எனவே React ஆப்
கூடுதல் CORS அமைப்பு இல்லாமல் லோக்கல் Flask சர்வருடன் பேசலாம்.

Python தொகுப்புடன் அனுப்பப்படும் bundle ஐ உருவாக்க:

```bash
cd frontend
npm run build
```

புரொடக்ஷன் bundle `clawmetry/static/v2/dist/` க்கு எழுதப்படுகிறது.

## ரன்டைம் / ஏஜென்ட் இணக்கத்தன்மை

ClawMetry OpenClaw மட்டுமல்லாமல் பல AI-ஏஜென்ட் ரன்டைம்களையும் கண்காணிக்கிறது. ஒவ்வொரு OpenClaw அல்லாத ரன்டைமும் அதன் சொந்த அமர்வு வடிவத்தை ClawMetry-இன் ஒருங்கிணைந்த வடிவங்களாக மொழிபெயர்க்கும் ஒரு அர்ப்பணிப்பு reader அடாப்டரை ஏற்றி வருகிறது; டேமன் அவற்றை அதே DuckDB ஸ்டோர் + கிளவுட் ஸ்னாப்ஷாட்டில் இணைக்கிறது, ரன்டைமுடன் டேக் செய்யப்பட்டு, ஒன்றுக்கும் மேற்பட்ட ரன்டைம் இருக்கும்போது Session replay டேப் ஒரு **ரன்டைம் மாற்றி**யைக் காட்டுகிறது. முழு மேட்ரிக்ஸ் + ரன்டைம்களைச் சேர்ப்பதற்கான வழிகாட்டிக்கு [`docs/compatibility.md`](docs/compatibility.md) ஐயும், OpenClaw-குடும்ப அறிமுகத்திற்கு [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ஐயும் பார்க்கவும்.

| Runtime / Agent | Status | குறிப்புகள் |
|---|---|---|
| **OpenClaw** | Native | குறிப்பு ரன்டைம், தானாக கண்டறியப்படும் |
| **PicoClaw** | Beta adapter | Flat `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). டிரான்ஸ்கிரிப்ட்கள், மாடல், டூல் அழைப்புகள். |
| **NanoClaw** | Beta adapter | ஒவ்வொரு அமர்வுக்கும் SQLite (`data/v2-sessions`). டிரான்ஸ்கிரிப்ட்கள் + செய்தி எண்ணிக்கைகள். |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன்கள்/செலவு. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டூல் அழைப்புகள் + சிந்தனை, டோக்கன் பயன்பாடு. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டூல் அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Chat/composer டிரான்ஸ்கிரிப்ட்கள், மாடல். |
| **Aider** | Beta adapter | ஒவ்வொரு ப்ராஜெக்டுக்கும் `.aider.chat.history.md`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன் எண்ணிக்கைகள். |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டூல் அழைப்புகள், டோக்கன் மொத்தங்கள். |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டூல் அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டூல் அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டூல் அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டூல் அழைப்புகள், டோக்கன்கள் + செலவு. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. Workflow executions, node runs, AI Agent prompts, மாடல் + டோக்கன்கள் n8n அவற்றை பதிவு செய்யும் இடங்களில். |
| **Antigravity** | Beta adapter | `~/.gemini/<flavor>/brain/` இன் கீழ் Brain JSONL. உரையாடல்கள், டூல் படிகள், சிந்தனை, ஒவ்வொரு-generation Gemini டோக்கன் பிரிவு + செலவு, பின்னணி-generation எரிப்பு. |

"Beta adapter" என்பது ClawMetry அந்த ரன்டைமின் உண்மையான டிஸ்க்-மேல் வடிவத்திற்கான reader ஐ வழங்குகிறது என்பதைக் குறிக்கிறது, ஒவ்வொன்றும் ஒரு உண்மையான மெஷினில் ஒரு உண்மையான நிறுவலுக்கு எதிராக கட்டமைக்கப்பட்டு + சரிபார்க்கப்பட்டவை (`tests/fixtures/runtimes/<rt>/` ஐப் பார்க்கவும்). அடாப்டர்கள் read-only ஆகும்; ஒவ்வொன்றும் அதன் ரன்டைம் உண்மையில் என்ன சேமிக்கிறது என்பதைப் பற்றி நேர்மையானது (எ.கா. PicoClaw/NanoClaw/Cursor டோக்கன் செலவை டிஸ்க்கில் எழுதாது). ஒரே நோட்டில் பல ரன்டைம்கள் இயங்கும்போது, ரன்டைம் மாற்றி sessions காட்சியை ஒரு சுத்தமான ஆழ்ந்த-பார்வைக்கு ஒன்றுக்கு வரம்பிடுகிறது.

## எந்த SDK ஏஜென்டையும் கண்காணிக்கவும் — out-loop செலவு பங்கீடு

மேலே உள்ள ரன்டைம்கள் அனைத்தும் அமர்வுகளை டிஸ்க்கில் எழுதுகின்றன. நீங்கள் கட்டியெழுப்பிய உங்கள் சொந்த **புரொடக்ஷன் ஏஜென்ட்** — OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, அல்லது ஒரு சாதாரண `httpx` லூப் மீது — அதை செய்யாது. ClawMetry-இன் zero-config இண்டர்செப்டர் இன்னும் `httpx`/`requests` ஐ மங்கி-பேட்ச் செய்வதன் மூலம் அதன் LLM அழைப்புகளை (செலவு, டோக்கன்கள், லேட்டன்சி, பிழைகள்) பிடிக்கிறது:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (அல்லது `CLAWMETRY_SOURCE=support-agent` env var) ஒவ்வொரு அழைப்பையும் **பெயரிடப்பட்ட மூலம்** கொண்டு டேக் செய்கிறது, எனவே நீங்கள் இயக்கும் ஒவ்வொரு தயாரிப்பும் டாஷ்போர்டின் Overview-இல் உள்ள **🔌 Out-loop sources** கார்டில் அதன் சொந்த முதல்-தர, செலவு-பங்கீடு செய்யக்கூடிய வரியாகத் தோன்றும் — ஒவ்வொரு ஏஜென்டுக்கும் அழைப்புகள், providers, லேட்டன்சி, பிழை விகிதம். மூலம் அமைக்கப்படவில்லையா? அழைப்புகள் இன்னும் கண்காணிக்கப்படுகின்றன; கார்டு மட்டும் மறைந்தே இருக்கும்.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

இது ரன்டைம் அடாப்டர்கள் ஊட்டும் அதே தரவு லேயர் (DuckDB → கிளவுட் ஸ்னாப்ஷாட்) என்பதால், out-loop sources மற்ற அனைத்தையும் போலவே கிளவுட் டாஷ்போர்டுக்கு ஒத்திசைக்கின்றன, E2E-குறியாக்கம் செய்யப்பட்டு.

## OpenTelemetry — வென்டர்-நடுநிலை, உங்கள் டிரேஸ்களை எங்கு வேண்டுமானாலும் அனுப்புங்கள்

ClawMetry இரு திசைகளிலும் **OpenTelemetry** பேசுகிறது, **GenAI semantic conventions** ஐப் பயன்படுத்தி, எனவே உங்கள் ஏஜென்ட் டிரேஸ்கள் ஒரு டூலில் மட்டும் பூட்டப்படாது.

**Export** — ஒவ்வொரு அமர்வையும் — LLM அழைப்புகள், டூல்கள், துணை-ஏஜென்ட்கள், டோக்கன்கள், செலவு — எந்த கலெக்டருக்கும் (Datadog, Grafana, Honeycomb, அல்லது உங்கள் சொந்த OTel Collector) OTLP/HTTP GenAI spans ஆக ஏற்றுமதி செய்யவும்:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth headers மற்றும் poll இடைவெளி விருப்பமான env vars:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** — உள்ளமைக்கப்பட்ட OTLP receiver `/v1/traces` மற்றும் `/v1/metrics` இல் வேறு எதிலிருந்தும் டிரேஸ்கள் மற்றும் மெட்ரிக்குகளை ஏற்கிறது (protobuf ingest-க்கு `pip install clawmetry[otel]`).

நீங்கள் zero-config, லோக்கல்-முதல் ClawMetry டாஷ்போர்டையும் **மற்றும்** உங்கள் அணி ஏற்கனவே இயக்கும் எந்த பேக்கெண்டிலும் உங்கள் தரவையும் பெறுவீர்கள் — lock-in இல்லை, இரண்டாவது ஏஜென்ட் நிறுவ வேண்டாம்.

## கட்டமைப்பு

பெரும்பாலான மக்களுக்கு எந்த கட்டமைப்பும் தேவையில்லை. ClawMetry உங்கள் பணியிடம், பதிவுகள், அமர்வுகள் மற்றும் crons ஐ தானாகவே கண்டறிகிறது.

நீங்கள் தனிப்பயனாக்க வேண்டும் என்றால்:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

அனைத்து விருப்பங்களும்: `clawmetry --help`

## ஆதரிக்கப்படும் சேனல்கள்

நீங்கள் கட்டமைத்திருக்கும் ஒவ்வொரு OpenClaw சேனலுக்கும் ClawMetry நேரடி செயல்பாட்டைக் காட்டுகிறது. உங்கள் `openclaw.json` இல் உண்மையில் அமைக்கப்பட்ட சேனல்கள் மட்டுமே Flow வரைபடத்தில் தோன்றும் — கட்டமைக்கப்படாதவை தானாகவே மறைக்கப்படும்.

Flow-இல் எந்த சேனல் நோடையும் கிளிக் செய்து உள்வரும்/வெளிச்செல்லும் செய்தி எண்ணிக்கைகளுடன் ஒரு நேரடி சாட் குமிழி காட்சியைப் பார்க்கவும்.

| Channel | Status | Live Popup | குறிப்புகள் |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | செய்திகள், புள்ளிவிவரங்கள், 10s புதுப்பிப்பு |
| 💬 **iMessage** | ✅ Full | ✅ | `~/Library/Messages/chat.db` ஐ நேரடியாகப் படிக்கிறது |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) வழியாக |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli வழியாக |
| 🟣 **Discord** | ✅ Full | ✅ | Guild + channel கண்டறிதல் |
| 🟪 **Slack** | ✅ Full | ✅ | Workspace + channel கண்டறிதல் |
| 🌐 **Webchat** | ✅ Full | ✅ | உள்ளமைக்கப்பட்ட வெப் UI அமர்வுகள் |
| 📡 **IRC** | ✅ Full | ✅ | டெர்மினல்-பாணி குமிழி UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API வழியாக iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API webhooks வழியாக |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams bot plugin வழியாக |
| 🔷 **Mattermost** | ✅ Full | ✅ | சுய-ஹோஸ்ட் செய்யப்பட்ட அணி சாட் |
| 🟩 **Matrix** | ✅ Full | ✅ | பரவலாக்கப்பட்ட, E2EE ஆதரவு |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | பரவலாக்கப்பட்ட NIP-04 DMs |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC இணைப்பு வழியாக சாட் |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket நிகழ்வு சந்தா |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **தானியங்கு கண்டறிதல்:** ClawMetry உங்கள் `~/.openclaw/openclaw.json` ஐப் படித்து நீங்கள் உண்மையில் கட்டமைத்த சேனல்களை மட்டுமே காட்டுகிறது. கைமுறை அமைப்பு தேவையில்லை.

## Docker Deployment

Container-இல் ClawMetry ஐ இயக்க விரும்புகிறீர்களா? பிரச்சனை இல்லை! 🐳

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

**Docker Compose எடுத்துக்காட்டு:**

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

> **குறிப்பு:** Docker இல் இயங்கும்போது, ClawMetry உங்கள் அமைப்பை தானாகவே கண்டறிய உங்கள் ஏஜென்டின் தரவு + பதிவு டைரக்டரிகளை (எ.கா. `~/.openclaw`, `~/.claude`, `~/.codex`) mount செய்யவும்.

## தேவைகள்

- Python 3.8+
- Flask (pip வழியாக தானாகவே நிறுவப்படும்)
- அதே மெஷினில் ஒரு AI ஏஜென்ட் ரன்டைம்: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, அல்லது Antigravity (அல்லது Docker-க்கான mounted volumes)
- Linux அல்லது macOS

## NemoClaw / OpenShell ஆதரவு

ClawMetry தானாகவே [NemoClaw](https://github.com/NVIDIA/NemoClaw) ஐக் கண்டறியும் — sandboxed OpenShell containers-க்குள் ஏஜென்ட்களை இயக்கும் OpenClaw-க்கான NVIDIA-இன் நிறுவன பாதுகாப்பு wrapper.

பெரும்பாலான நிலைமைகளில் கூடுதல் கட்டமைப்பு தேவையில்லை. sync daemon அமர்வு கோப்புகளை host-இல் உள்ள `~/.openclaw/` இல் இருந்தாலும் சரி, OpenShell container-க்குள் இருந்தாலும் சரி தானாகவே கண்டறியும்.

### இது எப்படி வேலை செய்கிறது

ClawMetry இரண்டு வழிகளில் NemoClaw ஐக் கண்டறிகிறது:

1. **Binary கண்டறிதல்** — `nemoclaw` CLI ஐச் சரிபார்த்து sandbox தகவலைப் பெற `nemoclaw status` ஐ இயக்குகிறது
2. **Container கண்டறிதல்** — `openshell`, `nemoclaw`, அல்லது `ghcr.io/nvidia/` images க்கான இயங்கும் Docker containers ஐ ஸ்கேன் செய்து, பின்னர் volume mounts அல்லது `docker cp` வழியாக அமர்வுகளைப் படிக்கிறது

NemoClaw containers-இலிருந்து ஒத்திசைக்கப்பட்ட அமர்வு கோப்புகள் கிளவுட் டாஷ்போர்டில் `runtime=nemoclaw` மற்றும் `container_id` metadata உடன் டேக் செய்யப்படுகின்றன, எனவே அவற்றை standard OpenClaw அமர்வுகளிலிருந்து ஒரே பார்வையில் வேறுபடுத்திப் பார்க்கலாம்.

### பரிந்துரைக்கப்பட்ட அமைப்பு: HOST-இல் sync daemon

சிறந்த அனுபவத்திற்கு, ClawMetry-இன் sync daemon ஐ **host மெஷினில்** (sandbox-க்குள் அல்ல) இயக்கவும். இது NemoClaw நெட்வொர்க் பாலிசி கட்டுப்பாடுகளைத் தவிர்க்கிறது.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon இயங்கும் எந்த OpenShell containers-க்குள்ளும் உள்ள அமர்வுகளை தானாகவே கண்டறியும்.

### விருப்பமானது: வெளிப்படையான sandbox பெயர்

தானியங்கு கண்டறிதல் வேலை செய்யவில்லை என்றால், ClawMetry ஐ சரியான sandbox-இற்கு சுட்டிக்காட்டவும்:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### sandbox-க்குள் இயக்குதல் (மேம்பட்டது)

நீங்கள் sync daemon ஐ OpenShell sandbox **உள்ளே** இயக்க வேண்டியிருந்தால், ClawMetry ingest API ஐ அடைய முடியும் என்பதற்காக உங்கள் NemoClaw நெட்வொர்க் பாலிசியில் இந்த egress விதியைச் சேர்க்கவும்:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

இதனுடன் Apply செய்யவும்:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### போர்ட்கள் மற்றும் endpoints

| Endpoint | Port | Protocol | தேவையா |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ஆம் (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | ஆம் (local dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | container அமர்வு கண்டறிதலுக்கு |

sync daemon `ingest.clawmetry.com` க்கு மட்டுமே வெளிச்செல்லும் HTTPS அழைப்புகளை செய்கிறது. inbound ports எதுவும் தேவையில்லை.

---

## Cloud Deployment

SSH tunnels, reverse proxy, மற்றும் Docker-க்கு **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ஐப் பார்க்கவும்.

## சோதனை

இந்த ப்ராஜெக்ட் BrowserStack உடன் சோதிக்கப்படுகிறது.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

ClawMetry `https://app.clawmetry.com/api/install` க்கு அநாமதேய install-lifecycle
pings அனுப்புகிறது: புதிய மெஷினில் நீங்கள் `clawmetry` CLI ஐ முதன்முறையாக
இயக்கும்போது ஒரு `install` ping, புதிய பதிப்பிற்கு அப்கிரேட் செய்த பிறகு
முதல் இயக்கத்தில் ஒரு `update` ping, மற்றும் டாஷ்போர்டு-உள்ளடங்கிய
onboarding தேர்வை நீங்கள் முடிக்கும்போது ஒரு `onboarded` ping. உண்மையான
நிறுவல்களை எண்ண இதைப் பயன்படுத்துகிறோம் (raw PyPI download எண்கள் ~98%
mirrors, CI, மற்றும் auto-update மறு-பதிவிறக்கங்கள்) மற்றும் எந்த ஏஜென்ட்
frameworks மற்றும் பதிப்புகள் உண்மையில் பயன்பாட்டில் உள்ளன என்பதை
அறிய.

**ஒவ்வொரு பதிப்பிற்கும் ஒவ்வொரு lifecycle நிகழ்விற்கும் அதிகபட்சம் ஒரு POST**, இதில் அடங்கியுள்ளவை:

| Field | Example | ஏன் |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` இல் சேமிக்கப்பட்ட random UUID | dedup; நீங்கள் வெளிப்படையாக Cloud sync ஐ இணைக்கும் வரை அநாமதேயமானது (அங்கீகரிக்கப்பட்ட daemon heartbeat பின்னர் அதை carry செய்து, இந்த install ஐ உங்கள் கணக்குடன் இணைக்கிறது) |
| `event` | `install` / `update` / `onboarded` | புதிய நிறுவல் vs ஏற்கனவே உள்ள ஒன்றின் அப்கிரேட் |
| `version` | `0.12.167` | எந்த பதிப்புகள் பயன்பாட்டில் உள்ளன |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform ஆதரவு முன்னுரிமைகள் |
| `python` | `3.11.15` | Python பதிப்பு ஆதரவு matrix |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | அடுத்து நாம் எந்த ஏஜென்ட்களுடன் ஒருங்கிணைக்க வேண்டும் |
| `is_ci` / `ci_provider` | `true` / `github_actions` | மனித நிறுவல்களை CI சத்தத்திலிருந்து பிரிக்கிறது |

**நாங்கள் அனுப்பாதவை**: IP (cloud கோரிக்கையிலிருந்து server-side
நாட்டுக் குறியீட்டைப் பெறுகிறது, பின்னர் IP ஐ நிராகரிக்கிறது), hostname,
username, workspace path, file contents, உங்கள் api_key, உங்கள் email,
PII அல்லது workspace-குறிப்பிட்ட எதுவும். wire payload
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) இல் தணிக்கை செய்யக்கூடியது.

**Opt out** (இவற்றில் ஏதேனும் ஒன்று அதை நிரந்தரமாக முடக்கும்):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

இங்கு நெட்வொர்க் தோல்வி `clawmetry` இயங்குவதை ஒருபோதும் தடுக்காது —
ping என்பது daemon thread-இல் 3s timeout உடன் fire-and-forget ஆகும்.

## Star History

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
  <sub>உருவாக்கியவர் <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> சூழ்அமைப்பின் ஒரு பகுதி</sub>
</p>
