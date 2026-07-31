<!-- i18n-src:8252f6b1d31d -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்.** **14 AI ஏஜென்ட் ரன்டைம்களுக்கான** நேரடி கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex மற்றும் மேலும் 10. உங்கள் முழு ஏஜென்ட் கூட்டத்திற்கும் ஒரே டாஷ்போர்டு.

> 🌐 **இதை இந்த மொழிகளில் படிக்கவும்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. கட்டமைப்பு தேவையில்லை. எல்லாவற்றையும் தானாக கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும், அவ்வளவுதான்.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

ClawMetry OpenClaw-க்கான கண்காணிப்பாக தொடங்கியது, இப்போது உங்கள் இயந்திரத்தில் உள்ள ஒவ்வொரு ரன்டைமையும் தானாக கண்டறிந்து, **உங்கள் முழு ஏஜென்ட் கூட்டத்தையும்** ஒரே டாஷ்போர்டில் அளவிடுகிறது:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw மற்றும் NemoClaw ஓப்பன்-சோர்ஸ் ஆப்பில் இலவசம்; மற்ற ரன்டைம்கள் ClawMetry Cloud அல்லது சுய-ஹோஸ்ட் செய்யப்பட்ட Pro உரிமத்துடன் இயங்கும். ஹெடரிலிருந்து ரன்டைம்களை மாற்றவும், ஒவ்வொரு தாவலும் (செலவு, டோக்கன்கள், டூல்கள், ட்ரேஸ்கள்) அந்த ரன்டைமுக்கு மீண்டும் அளவிடப்படும். சரியான இலவச/பணம் செலுத்தும் பிரிவு, tier மேட்ரிக்ஸ், `/api/entitlement` வடிவம், மற்றும் `clawmetry license` CLI ஆகியவற்றுக்கு **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** பார்க்கவும்.

## நீங்கள் பெறுவது என்ன

- **Flow** — சேனல்கள், மூளை, டூல்கள் வழியாகவும் திரும்பவும் செய்திகள் பாய்வதைக் காட்டும் நேரடி அனிமேஷன் வரைபடம்
- **Overview** — ஆரோக்கிய சோதனைகள், செயல்பாட்டு ஹீட்மேப், அமர்வு எண்ணிக்கைகள், மாடல் தகவல்
- **Usage** — தினசரி/வாராந்திர/மாதாந்திர பிரிவுகளுடன் டோக்கன் மற்றும் செலவு கண்காணிப்பு
- **Sessions** — மாடல், டோக்கன்கள், கடைசி செயல்பாடு உடன் செயலில் உள்ள ஏஜென்ட் அமர்வுகள்
- **Crons** — நிலை, அடுத்த இயக்கம், கால அளவுடன் திட்டமிடப்பட்ட வேலைகள்
- **Logs** — வண்ண-குறியிடப்பட்ட நேரடி லாக் ஸ்ட்ரீமிங்
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, தினசரி குறிப்புகளை உலாவவும்
- **Transcripts** — அமர்வு வரலாறுகளைப் படிக்க சாட்-குமிழி UI
- **Alerts** — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், ஏஜென்ட்-ஆஃப்லைன் கண்டறிதல்; Slack, Discord, PagerDuty, Telegram, மின்னஞ்சலுக்கு வழிநடத்துகிறது
- **Approvals** — அழிவுகரமான நீக்குதல்கள், force push-கள், DB மாற்றங்கள், sudo, தொகுப்பு நிறுவல்கள், நெட்வொர்க் அழைப்புகளை ஒரே கிளிக் ஒப்புதலுக்குப் பின்னால் தடுக்கவும்

## ஸ்கிரீன்ஷாட்கள்

### 🧠 Brain — நேரடி ஏஜென்ட் நிகழ்வு ஸ்ட்ரீம்
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — டோக்கன் பயன்பாடு & அமர்வு சுருக்கம்
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — நேரடி டூல் அழைப்பு ஃபீட்
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — மாடல் & அமர்வு வாரியான செலவு பிரிவு
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — பணியிட கோப்பு உலாவி
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — நிலைப்பாடு & தணிக்கை பதிவு
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், Slack / Discord / PagerDuty / மின்னஞ்சலுக்கான வெப்ஹூக்குகள்
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ஆபத்தான டூல் அழைப்புகளை கைமுறை ஒப்புதலுக்குப் பின்னால் தடுக்கவும்; பாலிசி-ஆதரவு பாதுகாப்பு விதிகள்
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-க்கான இயக்கத்திற்கு முந்தைய தடுப்பு** — ஒரே கட்டளை பொருந்தும் டூல்
அழைப்புகளை *அவை இயங்குவதற்கு முன்* இடைநிறுத்தி உங்கள் முடிவுக்காக காத்திருக்கும்
ஒரு PreToolUse ஹூக்கை நிறுவுகிறது (உங்கள் ஃபோனிலிருந்து ஒரு தட்டல்,
[cloud push notifications](https://app.clawmetry.com/push) இயக்கப்பட்டால்):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ஒரு மறுப்பு அந்த ஒரு டூல் அழைப்பை மட்டுமே தடுக்கும் — ஏஜென்ட் அதன் அமர்வைத்
தக்கவைத்துக் கொண்டு வேறு அணுகுமுறையை முயற்சிக்கலாம். உங்கள் ஃபோனில்
ஒப்புதல் அளிப்பது Claude Code-இன் சொந்த அனுமதி வேண்டுகோளைத் தவிர்க்கிறது
(நீங்கள் ஏற்கனவே பதிலளித்துவிட்டீர்கள்). பொருந்தாத டூல்கள் ~40ms செலவாகும்
மற்றும் Claude Code-இன் இயல்பான அனுமதி ஓட்டத்திற்கு தானாக செல்லும். Claude
Code தானே உங்களுக்காக காத்திருக்கும் போதும் (`permission_prompt` /
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

v2 React ஆப் `frontend/` இல் உள்ளது, மற்றும் Flask
சர்வர் v2 இயக்கப்பட்ட நிலையில் தொடங்கும்போது `/v2` இல் வழங்கப்படுகிறது.

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

`http://localhost:5173/v2/` திறக்கவும். Vite `/api` கோரிக்கைகளை
`http://localhost:8900`-க்கு proxy செய்கிறது, எனவே React ஆப் கூடுதல்
CORS அமைப்பு இல்லாமல் லோக்கல் Flask சர்வருடன் பேசலாம்.

Python தொகுப்புடன் வரும் பண்டிலை உருவாக்க:

```bash
cd frontend
npm run build
```

Production பண்டில் `clawmetry/static/v2/dist/` இல் எழுதப்படுகிறது.

## ரன்டைம் / ஏஜென்ட் இணக்கத்தன்மை

ClawMetry OpenClaw மட்டுமல்லாமல் பல AI-ஏஜென்ட் ரன்டைம்களையும் கண்காணிக்கிறது. OpenClaw அல்லாத ஒவ்வொரு ரன்டைமும் அதன் சொந்த அமர்வு வடிவத்தை ClawMetry-இன் ஒருங்கிணைந்த வடிவங்களாக மொழிபெயர்க்கும் ஒரு பிரத்யேக reader adapter-ஐ கொண்டு வருகிறது; daemon அவற்றை அதே DuckDB store + cloud snapshot-இல் இணைக்கிறது, ரன்டைம் மூலம் குறியிடப்பட்டு, ஒன்றுக்கும் மேற்பட்ட ரன்டைம்கள் இருக்கும்போது Session replay தாவல் ஒரு **ரன்டைம் switcher**-ஐ காட்டுகிறது. முழு மேட்ரிக்ஸ் + ரன்டைம்களைச் சேர்ப்பதற்கான வழிகாட்டிக்கு [`docs/compatibility.md`](docs/compatibility.md) பார்க்கவும், மற்றும் OpenClaw-குடும்ப அறிமுகத்திற்கு [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) பார்க்கவும்.

| ரன்டைம் / ஏஜென்ட் | நிலை | குறிப்புகள் |
|---|---|---|
| **OpenClaw** | Native | குறிப்பு ரன்டைம், தானாக கண்டறியப்படுகிறது |
| **PicoClaw** | Beta adapter | Flat `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, மாடல், டூல் அழைப்புகள். |
| **NanoClaw** | Beta adapter | ஒரு-அமர்வு SQLite (`data/v2-sessions`). Transcripts + செய்தி எண்ணிக்கைகள். |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. Transcripts, மாடல், டோக்கன்கள்/செலவு. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, மாடல், டூல் அழைப்புகள் + சிந்தனை, டோக்கன் பயன்பாடு. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripts, மாடல், டூல் அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Chat/composer transcripts, மாடல். |
| **Aider** | Beta adapter | ஒவ்வொரு திட்டத்திற்கும் `.aider.chat.history.md`. Transcripts, மாடல், டோக்கன் எண்ணிக்கைகள். |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. Transcripts, மாடல், டூல் அழைப்புகள், டோக்கன் மொத்தங்கள். |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. Transcripts, மாடல், டூல் அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, மாடல், டூல் அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. Transcripts, மாடல், டூல் அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, மாடல், டூல் அழைப்புகள், டோக்கன்கள் + செலவு. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. Workflow executions, node runs, AI Agent prompts, n8n பதிவு செய்யும் இடங்களில் மாடல் + டோக்கன்கள். |

"Beta adapter" என்பது ClawMetry அந்த ரன்டைமின் உண்மையான on-disk வடிவத்திற்கான ஒரு reader-ஐ கொண்டு வருகிறது என்பதைக் குறிக்கிறது, ஒவ்வொன்றும் ஒரு உண்மையான இயந்திரத்தில் உள்ள உண்மையான நிறுவலுக்கு எதிராக உருவாக்கப்பட்டு + சரிபார்க்கப்பட்டது (`tests/fixtures/runtimes/<rt>/` பார்க்கவும்). Adapters read-only ஆகும்; ஒவ்வொன்றும் அதன் ரன்டைம் உண்மையில் என்ன சேமிக்கிறது என்பதில் நேர்மையானது (எ.கா. PicoClaw/NanoClaw/Cursor டோக்கன் செலவை டிஸ்க்கில் எழுதுவதில்லை). ஒரு நோடில் பல ரன்டைம்கள் இயங்கும்போது, ரன்டைம் switcher அமர்வுகள் காட்சியை ஒன்றுக்கு அளவிட்டு தெளிவான deep-dive அளிக்கிறது.

## எந்த SDK ஏஜென்டையும் கண்காணிக்கவும் — out-loop செலவு பங்கீடு

மேலே உள்ள ரன்டைம்கள் அனைத்தும் அமர்வுகளை டிஸ்க்கில் எழுதுகின்றன. நீங்கள் கட்டமைத்த உங்கள் சொந்த **production ஏஜென்ட்** — OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, அல்லது ஒரு plain `httpx` லூப்பில் — அப்படி எழுதாது. ClawMetry-இன் zero-config interceptor இன்னும் `httpx`/`requests`-ஐ monkey-patch செய்வதன் மூலம் அதன் LLM அழைப்புகளை (செலவு, டோக்கன்கள், latency, பிழைகள்) பிடிக்கிறது:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (அல்லது `CLAWMETRY_SOURCE=support-agent` env var) ஒவ்வொரு அழைப்பையும் ஒரு **பெயரிடப்பட்ட மூலத்துடன்** குறியிடுகிறது, எனவே நீங்கள் இயக்கும் ஒவ்வொரு தயாரிப்பும் டாஷ்போர்டின் Overview-இல் உள்ள **🔌 Out-loop sources** கார்டில் அதன் சொந்த முதல்-தர, செலவு-பங்கீடு செய்யக்கூடிய வரியாக காட்டப்படும் — ஒவ்வொரு ஏஜென்டுக்கும் அழைப்புகள், providers, latency, பிழை விகிதம். மூலம் அமைக்கப்படவில்லையா? அழைப்புகள் இன்னும் கண்காணிக்கப்படுகின்றன; கார்டு மட்டும் மறைந்திருக்கும்.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

இது ரன்டைம் adapters ஊட்டும் அதே தரவு அடுக்கு (DuckDB → cloud snapshot), எனவே out-loop sources மற்ற அனைத்தையும் போலவே cloud டாஷ்போர்டுடன் ஒத்திசைக்கப்படுகிறது, E2E-குறியாக்கம் செய்யப்பட்டது.

## OpenTelemetry — vendor-neutral, உங்கள் trace-களை எங்கும் அனுப்புங்கள்

ClawMetry இரு திசைகளிலும் **OpenTelemetry** பேசுகிறது, **GenAI semantic conventions**-ஐ பயன்படுத்தி, எனவே உங்கள் ஏஜென்ட் trace-கள் ஒரு டூலில் மட்டும் பூட்டப்படுவதில்லை.

ஒவ்வொரு அமர்வையும் — LLM அழைப்புகள், டூல்கள், sub-agents, டோக்கன்கள், செலவு — OTLP/HTTP GenAI spans ஆக எந்த collector-க்கும் (Datadog, Grafana, Honeycomb, அல்லது உங்கள் சொந்த OTel Collector) **Export** செய்யவும்:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth headers மற்றும் poll interval விருப்பமான env vars ஆகும்:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** — உள்ளமைக்கப்பட்ட OTLP receiver `/v1/traces` மற்றும் `/v1/metrics`-இல் மற்ற எதிலிருந்தும் traces மற்றும் metrics-ஐ ஏற்றுக்கொள்கிறது (protobuf ingest-க்கு `pip install clawmetry[otel]`).

நீங்கள் zero-config, local-first ClawMetry டாஷ்போர்டையும் **மற்றும்** உங்கள் அணி ஏற்கனவே இயக்கும் எந்த backend-இலும் உங்கள் தரவையும் பெறுவீர்கள் — lock-in இல்லை, இரண்டாவது ஏஜென்ட் நிறுவ வேண்டியதில்லை.

## கட்டமைப்பு

பெரும்பாலான மக்களுக்கு எந்த கட்டமைப்பும் தேவையில்லை. ClawMetry உங்கள் பணியிடம், logs, sessions, மற்றும் crons-ஐ தானாக கண்டறிகிறது.

நீங்கள் தனிப்பயனாக்க வேண்டும் என்றால்:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

அனைத்து விருப்பங்களும்: `clawmetry --help`

## ஆதரிக்கப்படும் சேனல்கள்

நீங்கள் கட்டமைத்துள்ள ஒவ்வொரு OpenClaw சேனலின் நேரடி செயல்பாட்டையும் ClawMetry காட்டுகிறது. உங்கள் `openclaw.json`-இல் உண்மையில் அமைக்கப்பட்ட சேனல்கள் மட்டுமே Flow வரைபடத்தில் தோன்றும் — கட்டமைக்கப்படாதவை தானாக மறைக்கப்படும்.

Flow-இல் ஏதேனும் சேனல் நோடை கிளிக் செய்தால் உள்வரும்/வெளிச்செல்லும் செய்தி எண்ணிக்கைகளுடன் ஒரு நேரடி chat bubble காட்சி கிடைக்கும்.

| சேனல் | நிலை | நேரடி Popup | குறிப்புகள் |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ முழு | ✅ | செய்திகள், புள்ளிவிவரங்கள், 10s புதுப்பிப்பு |
| 💬 **iMessage** | ✅ முழு | ✅ | `~/Library/Messages/chat.db`-ஐ நேரடியாகப் படிக்கிறது |
| 💚 **WhatsApp** | ✅ முழு | ✅ | WhatsApp Web (Baileys) வழியாக |
| 🔵 **Signal** | ✅ முழு | ✅ | signal-cli வழியாக |
| 🟣 **Discord** | ✅ முழு | ✅ | Guild + channel கண்டறிதல் |
| 🟪 **Slack** | ✅ முழு | ✅ | Workspace + channel கண்டறிதல் |
| 🌐 **Webchat** | ✅ முழு | ✅ | உள்ளமைக்கப்பட்ட web UI sessions |
| 📡 **IRC** | ✅ முழு | ✅ | Terminal-பாணி bubble UI |
| 🍏 **BlueBubbles** | ✅ முழு | ✅ | BlueBubbles REST API வழியாக iMessage |
| 🔵 **Google Chat** | ✅ முழு | ✅ | Chat API webhooks வழியாக |
| 🟣 **MS Teams** | ✅ முழு | ✅ | Teams bot plugin வழியாக |
| 🔷 **Mattermost** | ✅ முழு | ✅ | Self-hosted team chat |
| 🟩 **Matrix** | ✅ முழு | ✅ | Decentralized, E2EE ஆதரவு |
| 🟢 **LINE** | ✅ முழு | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ முழு | ✅ | Decentralized NIP-04 DMs |
| 🟣 **Twitch** | ✅ முழு | ✅ | IRC இணைப்பு வழியாக chat |
| 🔷 **Feishu/Lark** | ✅ முழு | ✅ | WebSocket event subscription |
| 🔵 **Zalo** | ✅ முழு | ✅ | Zalo Bot API |

> **தானியங்கு கண்டறிதல்:** ClawMetry உங்கள் `~/.openclaw/openclaw.json`-ஐ படித்து நீங்கள் உண்மையில் கட்டமைத்த சேனல்களை மட்டுமே காட்டுகிறது. கைமுறை அமைப்பு தேவையில்லை.

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

> **குறிப்பு:** Docker-இல் இயங்கும்போது, ClawMetry உங்கள் அமைப்பை தானாக கண்டறிய, உங்கள் ஏஜென்டின் தரவு + log அடைவுகளை (எ.கா. `~/.openclaw`, `~/.claude`, `~/.codex`) mount செய்யவும்.

## தேவைகள்

- Python 3.8+
- Flask (pip வழியாக தானாக நிறுவப்படும்)
- அதே இயந்திரத்தில் ஒரு AI ஏஜென்ட் ரன்டைம்: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, அல்லது n8n (அல்லது Docker-க்கான mounted volumes)
- Linux அல்லது macOS

## NemoClaw / OpenShell ஆதரவு

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw)-ஐ தானாக கண்டறிகிறது — sandboxed OpenShell கன்டெய்னர்களுக்குள் ஏஜென்ட்களை இயக்கும் OpenClaw-க்கான NVIDIA-இன் enterprise பாதுகாப்பு wrapper.

பெரும்பாலான சந்தர்ப்பங்களில் கூடுதல் கட்டமைப்பு தேவையில்லை. Sync daemon அமர்வு கோப்புகள் host-இல் `~/.openclaw/` இல் இருந்தாலும் அல்லது OpenShell கன்டெய்னருக்குள் இருந்தாலும் தானாக கண்டறியும்.

### இது எப்படி வேலை செய்கிறது

ClawMetry NemoClaw-ஐ இரண்டு வழிகளில் கண்டறிகிறது:

1. **Binary கண்டறிதல்** — `nemoclaw` CLI-க்கு சரிபார்த்து sandbox தகவலைப் பெற `nemoclaw status`-ஐ இயக்குகிறது
2. **கன்டெய்னர் கண்டறிதல்** — `openshell`, `nemoclaw`, அல்லது `ghcr.io/nvidia/` images-க்காக இயங்கும் Docker கன்டெய்னர்களை ஸ்கேன் செய்கிறது, பின்னர் volume mounts அல்லது `docker cp` வழியாக sessions-ஐ படிக்கிறது

NemoClaw கன்டெய்னர்களில் இருந்து ஒத்திசைக்கப்பட்ட session கோப்புகள் cloud டாஷ்போர்டில் `runtime=nemoclaw` மற்றும் `container_id` metadata உடன் குறியிடப்படுகின்றன, எனவே நீங்கள் ஒரு பார்வையிலேயே அவற்றை நிலையான OpenClaw sessions-இலிருந்து வேறுபடுத்தலாம்.

### பரிந்துரைக்கப்பட்ட அமைப்பு: HOST-இல் sync daemon

சிறந்த அனுபவத்திற்கு, ClawMetry-இன் sync daemon-ஐ (sandbox-க்குள் அல்ல) **host இயந்திரத்தில்** இயக்கவும். இது NemoClaw network policy கட்டுப்பாடுகளைத் தவிர்க்கிறது.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Sync daemon இயங்கும் எந்த OpenShell கன்டெய்னருக்குள்ளும் sessions-ஐ தானாக கண்டறியும்.

### விருப்பமானது: வெளிப்படையான sandbox பெயர்

தானியங்கு கண்டறிதல் வேலை செய்யவில்லை என்றால், ClawMetry-ஐ சரியான sandbox-க்கு சுட்டிக்காட்டவும்:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### sandbox-க்குள் இயக்குதல் (மேம்பட்டது)

Sync daemon-ஐ **OpenShell sandbox-க்குள்** இயக்க வேண்டியிருந்தால், அது ClawMetry ingest API-ஐ அடைய உங்கள் NemoClaw network policy-இல் இந்த egress விதியைச் சேர்க்கவும்:

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

| Endpoint | போர்ட் | Protocol | தேவையா |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ஆம் (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | ஆம் (local dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | கன்டெய்னர் session கண்டறிதலுக்கு |

Sync daemon `ingest.clawmetry.com`-க்கு மட்டுமே வெளிச்செல்லும் HTTPS அழைப்புகளை செய்கிறது. உள்வரும் போர்ட்கள் தேவையில்லை.

---

## Cloud வரிசைப்படுத்தல்

SSH tunnels, reverse proxy, மற்றும் Docker-க்கு **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** பார்க்கவும்.

## சோதனை

இந்த திட்டம் BrowserStack உடன் சோதிக்கப்படுகிறது.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

ClawMetry அநாமதேய install-lifecycle pings-ஐ
`https://app.clawmetry.com/api/install`-க்கு அனுப்புகிறது: நீங்கள் புதிய
இயந்திரத்தில் `clawmetry` CLI-ஐ முதன்முறையாக இயக்கும்போது ஒரு `install`
ping, புதிய version-க்கு upgrade செய்த பிறகு முதல் இயக்கத்தில் ஒரு
`update` ping, மற்றும் in-dashboard onboarding தேர்வை நிறைவு
செய்யும்போது ஒரு `onboarded` ping. உண்மையான நிறுவல்களை எண்ணவும் (raw
PyPI download எண்கள் ~98% mirrors, CI, மற்றும் auto-update
re-downloads ஆகும்), மேலும் எந்த ஏஜென்ட் frameworks மற்றும்
versions-கள் உண்மையில் பயன்பாட்டில் உள்ளன என்பதை அறியவும் இதைப்
பயன்படுத்துகிறோம்.

**ஒரு lifecycle நிகழ்வுக்கு ஒரு version-க்கு அதிகபட்சம் ஒரு POST**, இதில் அடங்கியிருப்பது:

| Field | எடுத்துக்காட்டு | ஏன் |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`-இல் சேமிக்கப்பட்ட random UUID | dedup; நீங்கள் வெளிப்படையாக Cloud sync-ஐ இணைக்கும் வரை அநாமதேயமானது (அங்கீகரிக்கப்பட்ட daemon heartbeat பின்னர் அதை carry செய்கிறது, இந்த install-ஐ உங்கள் கணக்குடன் இணைக்கிறது) |
| `event` | `install` / `update` / `onboarded` | புதிய நிறுவல் vs ஏற்கனவே உள்ள ஒன்றின் upgrade |
| `version` | `0.12.167` | பயன்பாட்டில் உள்ள versions-கள் |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform ஆதரவு முன்னுரிமைகள் |
| `python` | `3.11.15` | Python version ஆதரவு மேட்ரிக்ஸ் |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | அடுத்து நாங்கள் எந்த ஏஜென்ட்களை integrate செய்ய வேண்டும் |
| `is_ci` / `ci_provider` | `true` / `github_actions` | மனித நிறுவல்களை CI சத்தத்திலிருந்து பிரிக்கிறது |

**நாங்கள் அனுப்பாதவை**: IP (cloud request-இலிருந்து country code-ஐ
server-side-இல் derive செய்து, பின்னர் IP-ஐ discard செய்கிறது),
hostname, username, workspace path, கோப்பு content-கள், உங்கள்
api_key, உங்கள் மின்னஞ்சல், PII அல்லது workspace-குறிப்பிட்ட எதுவும்.
Wire payload
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)-இல் தணிக்கை
செய்யக்கூடியது.

**Opt out** (இவற்றில் ஏதேனும் ஒன்று இதை நிரந்தரமாக முடக்கும்):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

இங்கு network failure ஒருபோதும் `clawmetry`-ஐ இயங்குவதைத் தடுக்காது —
ping என்பது 3 வினாடி timeout உடன் daemon thread-இல் fire-and-forget
ஆகும்.

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
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
