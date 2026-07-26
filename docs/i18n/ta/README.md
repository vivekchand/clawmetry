<!-- i18n-src:bab48eec552f -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்.** **14 AI ஏஜென்ட் ரன்டைம்களுக்கான** நேரடி (real-time) கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex மற்றும் மேலும் 10. உங்கள் முழு ஏஜென்ட் கூட்டத்திற்கும் ஒரே டாஷ்போர்டு.

> 🌐 **இதை இதில் படிக்கவும்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. கட்டமைப்பு தேவையில்லை (Zero config). எல்லாவற்றையும் தானாகவே கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும், அவ்வளவுதான்.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

ClawMetry, OpenClaw-க்கான கண்காணிப்பாக தொடங்கியது, இப்போது உங்கள் **முழு ஏஜென்ட் கூட்டத்தையும்** ஒரே டாஷ்போர்டில் அளவிடுகிறது, உங்கள் கணினியில் உள்ள ஒவ்வொரு ரன்டைமையும் தானாகவே கண்டறிகிறது:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw மற்றும் NemoClaw ஓப்பன்-சோர்ஸ் ஆப்பில் இலவசம்; மற்ற ரன்டைம்கள் ClawMetry Cloud அல்லது சுய-ஹோஸ்ட் செய்யப்பட்ட Pro உரிமத்துடன் இயங்கும். ஹெடரிலிருந்து ரன்டைம்களை மாற்றவும், ஒவ்வொரு தாவலும் (செலவு, டோக்கன்கள், கருவிகள், தடங்கள்) அந்த ரன்டைமுக்கு ஏற்ப மீண்டும் வரையறுக்கப்படும். சரியான இலவச/கட்டண பிரிவு, நிலை அட்டவணை, `/api/entitlement` வடிவம், மற்றும் `clawmetry license` CLI ஆகியவற்றிற்கு **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** பார்க்கவும்.

## நீங்கள் பெறுவது என்ன

- **Flow** — சேனல்கள், brain, கருவிகள் வழியாகவும் திரும்பவும் செய்திகள் பாய்வதைக் காட்டும் நேரடி அனிமேஷன் வரைபடம்
- **Overview** — ஆரோக்கிய சோதனைகள், செயல்பாட்டு ஹீட்மேப், அமர்வு எண்ணிக்கைகள், மாடல் தகவல்
- **Usage** — தினசரி/வாராந்திர/மாதாந்திர பிரிவுகளுடன் டோக்கன் மற்றும் செலவு கண்காணிப்பு
- **Sessions** — மாடல், டோக்கன்கள், கடைசி செயல்பாடு ஆகியவற்றுடன் செயலில் உள்ள ஏஜென்ட் அமர்வுகள்
- **Crons** — நிலை, அடுத்த இயக்கம், கால அளவுடன் திட்டமிடப்பட்ட பணிகள்
- **Logs** — வண்ண-குறியிடப்பட்ட நேரடி பதிவு ஸ்ட்ரீமிங்
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, தினசரி குறிப்புகளை உலாவவும்
- **Transcripts** — அமர்வு வரலாறுகளைப் படிக்க chat-bubble UI
- **Alerts** — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், ஏஜென்ட்-ஆஃப்லைன் கண்டறிதல்; Slack, Discord, PagerDuty, Telegram, Email ஆகியவற்றுக்கு வழிநடத்துகிறது
- **Approvals** — அழிவுகரமான நீக்கங்கள், force pushes, DB மாற்றங்கள், sudo, பேக்கேஜ் நிறுவல்கள், நெட்வொர்க் அழைப்புகளை ஒரே கிளிக் ஒப்புதலுக்குப் பின்னால் தடுக்கவும்

## ஸ்க்ரீன்ஷாட்டுகள்

### 🧠 Brain — நேரடி ஏஜென்ட் நிகழ்வு ஸ்ட்ரீம்
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — டோக்கன் பயன்பாடு & அமர்வு சுருக்கம்
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — நேரடி கருவி அழைப்பு ஊட்டம்
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — மாடல் & அமர்வு வாரியாக செலவு பிரிவு
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — பணிமனை (workspace) கோப்பு உலாவி
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — நிலை & தணிக்கை பதிவு
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், Slack / Discord / PagerDuty / Email-க்கு webhooks
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ஆபத்தான கருவி அழைப்புகளை கைமுறை ஒப்புதலுக்குப் பின்னால் தடுக்கவும்; கொள்கை-ஆதரவு பாதுகாப்பு விதிகள்
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-க்கான செயல்படுத்தலுக்கு முந்தைய தடுப்பு** — ஒரே கட்டளை, பொருந்தும்
கருவி அழைப்புகளை அவை இயங்குவதற்கு *முன்* இடைநிறுத்தி, உங்கள் முடிவுக்காக
காத்திருக்கும் ஒரு PreToolUse ஹுக்கை நிறுவுகிறது (உங்கள் தொலைபேசியிலிருந்து ஒரே
தட்டலில், [cloud push notifications](https://app.clawmetry.com/push) இயக்கப்பட்டிருந்தால்):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ஒரு denial (மறுப்பு) அந்த ஒரு கருவி அழைப்பை மட்டுமே தடுக்கும் — ஏஜென்ட் தனது அமர்வை
தக்கவைத்துக் கொண்டு வேறு அணுகுமுறையை முயற்சிக்கலாம். உங்கள் தொலைபேசியில்
ஒப்புதல் அளிப்பது Claude Code-இன் சொந்த அனுமதி கேள்வியைத் தவிர்க்கிறது (நீங்கள்
ஏற்கனவே பதிலளித்துவிட்டீர்கள்). பொருந்தாத கருவிகளுக்கு ~40ms செலவாகி, Claude
Code-இன் வழக்கமான அனுமதி ஓட்டத்திற்குள் விழும். Claude Code தானே உங்களுக்காக
காத்திருக்கும்போதும் (`permission_prompt` / `idle_prompt` அறிவிப்புகள்) உங்களுக்கு
தொலைபேசி push கிடைக்கும்.

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

## v2 Frontend மேம்பாடு

v2 React ஆப் `frontend/`-இல் உள்ளது, மேலும் v2 இயக்கப்பட்ட நிலையில் Flask
சேவையகம் தொடங்கப்படும்போது `/v2` இல் வழங்கப்படுகிறது.

மேம்பாட்டின்போது இரண்டு டெர்மினல்களைப் பயன்படுத்தவும்:

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

`http://localhost:5173/v2/`-ஐ திறக்கவும். Vite `/api` கோரிக்கைகளை
`http://localhost:8900`-க்கு ப்ராக்ஸி செய்கிறது, அதனால் React ஆப் கூடுதல்
CORS அமைப்பு இல்லாமல் லோக்கல் Flask சேவையகத்துடன் பேசலாம்.

Python பேக்கேஜுடன் வழங்கப்படும் bundle-ஐ உருவாக்க:

```bash
cd frontend
npm run build
```

Production bundle `clawmetry/static/v2/dist/`-இல் எழுதப்படுகிறது.

## ரன்டைம் / ஏஜென்ட் இணக்கத்தன்மை

ClawMetry OpenClaw மட்டுமல்லாமல் பல AI-ஏஜென்ட் ரன்டைம்களைக் கண்காணிக்கிறது. OpenClaw அல்லாத ஒவ்வொரு ரன்டைமும் அதன் சொந்த அமர்வு வடிவமைப்பை ClawMetry-இன் ஒருங்கிணைந்த வடிவங்களாக மொழிபெயர்க்கும் ஒரு அர்ப்பணிக்கப்பட்ட reader adapter-ஐ வழங்குகிறது; daemon அவற்றை அதே DuckDB ஸ்டோர் + கிளவுட் ஸ்னாப்ஷாட்டில் உள்ளிடுகிறது, ரன்டைமுடன் குறியிடப்பட்டு, ஒன்றுக்கு மேற்பட்ட ரன்டைம் இருக்கும்போது Session replay தாவலில் ஒரு **ரன்டைம் மாற்றி** காட்டப்படும். முழு அட்டவணை + ரன்டைம்களைச் சேர்ப்பதற்கான வழிகாட்டிக்கு [`docs/compatibility.md`](docs/compatibility.md)-ஐயும், OpenClaw-குடும்ப அறிமுகத்திற்கு [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)-ஐயும் பார்க்கவும்.

| ரன்டைம் / ஏஜென்ட் | நிலை | குறிப்புகள் |
|---|---|---|
| **OpenClaw** | Native | குறிப்பு ரன்டைம், தானாகக் கண்டறியப்படும் |
| **PicoClaw** | Beta adapter | ஃபிளாட் `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள். |
| **NanoClaw** | Beta adapter | ஒரு அமர்வுக்கு SQLite (`data/v2-sessions`). டிரான்ஸ்கிரிப்ட்கள் + செய்தி எண்ணிக்கைகள். |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன்கள்/செலவு. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள் + சிந்தனை, டோக்கன் பயன்பாடு. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. Chat/composer டிரான்ஸ்கிரிப்ட்கள், மாடல். |
| **Aider** | Beta adapter | ஒரு ப்ராஜெக்ட்டுக்கு `.aider.chat.history.md`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன் எண்ணிக்கைகள். |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் மொத்தங்கள். |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |

"Beta adapter" என்பதன் பொருள், அந்த ரன்டைமின் உண்மையான on-disk வடிவத்திற்கான reader-ஐ ClawMetry வழங்குகிறது என்பதே, ஒவ்வொன்றும் ஒரு உண்மையான கணினியில் உள்ள உண்மையான நிறுவலுக்கு எதிராக உருவாக்கப்பட்டு + சரிபார்க்கப்பட்டவை (`tests/fixtures/runtimes/<rt>/` பார்க்கவும்). Adapter-கள் read-only ஆனவை; ஒவ்வொன்றும் அதன் ரன்டைம் உண்மையில் என்ன சேமிக்கிறது என்பதில் நேர்மையானது (எ.கா. PicoClaw/NanoClaw/Cursor டோக்கன் செலவை டிஸ்க்கில் எழுதுவதில்லை). ஒரே நோட்டில் பல ரன்டைம்கள் இயங்கும்போது, ரன்டைம் மாற்றி sessions காட்சியை ஒன்றுக்கு scope செய்து, சுத்தமான ஆழ்ந்த-பரிசோதனைக்கு உதவும்.

## எந்த SDK ஏஜென்டையும் கண்காணிக்கவும் — out-loop செலவு பகிர்வு

மேலே உள்ள ரன்டைம்கள் அனைத்தும் அமர்வுகளை டிஸ்க்கில் எழுதுகின்றன. நீங்கள் உருவாக்கிய உங்கள் சொந்த **production ஏஜென்ட்** — OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, அல்லது ஒரு சாதாரண `httpx` loop மீது கட்டப்பட்டது — அப்படி செய்வதில்லை. ClawMetry-இன் zero-config interceptor `httpx`/`requests`-ஐ monkey-patch செய்வதன் மூலம் அதன் LLM அழைப்புகளை (செலவு, டோக்கன்கள், தாமதம், பிழைகள்) இன்னும் பிடிக்கிறது:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (அல்லது `CLAWMETRY_SOURCE=support-agent` env var) ஒவ்வொரு அழைப்பையும் ஒரு **பெயரிடப்பட்ட மூலத்துடன்** குறியிடுகிறது, அதனால் நீங்கள் இயக்கும் ஒவ்வொரு தயாரிப்பும் டாஷ்போர்டின் Overview-இல் **🔌 Out-loop sources** கார்டில் அதன் சொந்த முதல்-தர, செலவு-பகிரப்படக்கூடிய வரியாகத் தோன்றும் — ஒரு ஏஜென்ட்டுக்கு அழைப்புகள், providers, தாமதம், பிழை விகிதம். மூலம் அமைக்கப்படவில்லையா? அழைப்புகள் இன்னும் கண்காணிக்கப்படுகின்றன; கார்டு மறைந்திருக்கும்.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

இது ரன்டைம் adapter-கள் ஊட்டும் அதே தரவு அடுக்கு (DuckDB → கிளவுட் ஸ்னாப்ஷாட்) என்பதால், out-loop sources மற்ற அனைத்தையும் போலவே கிளவுட் டாஷ்போர்டுக்கு ஒத்திசைகிறது, E2E-குறியாக்கம் செய்யப்பட்டு.

## OpenTelemetry — வென்டர்-நடுநிலை, உங்கள் தடங்களை எங்கு வேண்டுமானாலும் அனுப்புங்கள்

ClawMetry இரு திசைகளிலும் **OpenTelemetry**-ஐப் பேசுகிறது, **GenAI சொற்பொருள் மரபுகளை** பயன்படுத்தி, அதனால் உங்கள் ஏஜென்ட் தடங்கள் ஒரு கருவியில் மட்டும் பூட்டப்படாது.

ஒவ்வொரு அமர்வையும் — LLM அழைப்புகள், கருவிகள், sub-agents, டோக்கன்கள், செலவு — OTLP/HTTP GenAI spans ஆக எந்த collector-க்கும் (Datadog, Grafana, Honeycomb, அல்லது உங்கள் சொந்த OTel Collector) **ஏற்றுமதி** செய்யவும்:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth தலைப்புகள் மற்றும் poll இடைவெளி விருப்பமான env vars:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**இறக்குமதி** — உள்ளமைக்கப்பட்ட OTLP receiver `/v1/traces` மற்றும் `/v1/metrics`-இல் வேறு எதிலிருந்தும் traces மற்றும் metrics-ஐ ஏற்கிறது (protobuf இறக்குமதிக்கு `pip install clawmetry[otel]`).

நீங்கள் zero-config, local-first ClawMetry டாஷ்போர்டையும் **மற்றும்** உங்கள் அணி ஏற்கனவே இயக்கும் எந்த backend-இலும் உங்கள் தரவையும் பெறுவீர்கள் — பூட்டு இல்லை, இரண்டாவது ஏஜென்ட்டை நிறுவ தேவையில்லை.

## கட்டமைப்பு

பெரும்பாலான மக்களுக்கு எந்த கட்டமைப்பும் தேவையில்லை. ClawMetry உங்கள் பணிமனை, பதிவுகள், அமர்வுகள், மற்றும் crons-ஐ தானாகவே கண்டறிகிறது.

நீங்கள் தனிப்பயனாக்க வேண்டும் என்றால்:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

அனைத்து விருப்பங்களும்: `clawmetry --help`

## ஆதரிக்கப்படும் சேனல்கள்

நீங்கள் கட்டமைத்துள்ள ஒவ்வொரு OpenClaw சேனலுக்கும் ClawMetry நேரடி செயல்பாட்டைக் காட்டுகிறது. உங்கள் `openclaw.json`-இல் உண்மையில் அமைக்கப்பட்ட சேனல்கள் மட்டுமே Flow வரைபடத்தில் தோன்றும் — கட்டமைக்கப்படாதவை தானாகவே மறைக்கப்படும்.

Flow-இல் எந்தவொரு சேனல் நோடையும் கிளிக் செய்து, உள்வரும்/வெளிச்செல்லும் செய்தி எண்ணிக்கைகளுடன் ஒரு நேரடி chat bubble காட்சியைப் பார்க்கவும்.

| சேனல் | நிலை | நேரடி பாப்அப் | குறிப்புகள் |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ முழுமையானது | ✅ | செய்திகள், புள்ளிவிவரங்கள், 10s புதுப்பிப்பு |
| 💬 **iMessage** | ✅ முழுமையானது | ✅ | `~/Library/Messages/chat.db`-ஐ நேரடியாகப் படிக்கிறது |
| 💚 **WhatsApp** | ✅ முழுமையானது | ✅ | WhatsApp Web (Baileys) வழியாக |
| 🔵 **Signal** | ✅ முழுமையானது | ✅ | signal-cli வழியாக |
| 🟣 **Discord** | ✅ முழுமையானது | ✅ | Guild + சேனல் கண்டறிதல் |
| 🟪 **Slack** | ✅ முழுமையானது | ✅ | Workspace + சேனல் கண்டறிதல் |
| 🌐 **Webchat** | ✅ முழுமையானது | ✅ | உள்ளமைக்கப்பட்ட web UI அமர்வுகள் |
| 📡 **IRC** | ✅ முழுமையானது | ✅ | Terminal-பாணி bubble UI |
| 🍏 **BlueBubbles** | ✅ முழுமையானது | ✅ | BlueBubbles REST API வழியாக iMessage |
| 🔵 **Google Chat** | ✅ முழுமையானது | ✅ | Chat API webhooks வழியாக |
| 🟣 **MS Teams** | ✅ முழுமையானது | ✅ | Teams bot plugin வழியாக |
| 🔷 **Mattermost** | ✅ முழுமையானது | ✅ | சுய-ஹோஸ்ட் செய்யப்பட்ட குழு chat |
| 🟩 **Matrix** | ✅ முழுமையானது | ✅ | பரவலாக்கப்பட்டது, E2EE ஆதரவு |
| 🟢 **LINE** | ✅ முழுமையானது | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ முழுமையானது | ✅ | பரவலாக்கப்பட்ட NIP-04 DMs |
| 🟣 **Twitch** | ✅ முழுமையானது | ✅ | IRC இணைப்பு வழியாக Chat |
| 🔷 **Feishu/Lark** | ✅ முழுமையானது | ✅ | WebSocket நிகழ்வு சந்தா |
| 🔵 **Zalo** | ✅ முழுமையானது | ✅ | Zalo Bot API |

> **தானியங்கு கண்டறிதல்:** ClawMetry உங்கள் `~/.openclaw/openclaw.json`-ஐ படித்து, நீங்கள் உண்மையில் கட்டமைத்த சேனல்களை மட்டுமே காட்டுகிறது. கைமுறை அமைப்பு தேவையில்லை.

## Docker வரிசைப்படுத்தல்

ClawMetry-ஐ ஒரு container-இல் இயக்க வேண்டுமா? பிரச்சனை இல்லை! 🐳

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

> **குறிப்பு:** Docker-இல் இயக்கும்போது, ClawMetry உங்கள் அமைப்பை தானாகவே கண்டறிய, உங்கள் ஏஜென்ட்-இன் தரவு + பதிவு டைரக்டரிகளை (எ.கா. `~/.openclaw`, `~/.claude`, `~/.codex`) மவுன்ட் செய்யவும்.

## தேவைகள்

- Python 3.8+
- Flask (pip வழியாக தானாகவே நிறுவப்படும்)
- அதே கணினியில் ஒரு AI ஏஜென்ட் ரன்டைம்: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, அல்லது Deep Agents (அல்லது Docker-க்கான மவுன்ட் செய்யப்பட்ட volumes)
- Linux அல்லது macOS

## NemoClaw / OpenShell ஆதரவு

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw)-ஐ தானாகவே கண்டறிகிறது — sandboxed OpenShell containers-க்குள் ஏஜென்ட்களை இயக்கும் OpenClaw-க்கான NVIDIA-இன் நிறுவன பாதுகாப்பு wrapper.

பெரும்பாலான சந்தர்ப்பங்களில் கூடுதல் கட்டமைப்பு தேவையில்லை. sync daemon, அமர்வு கோப்புகள் ஹோஸ்டில் `~/.openclaw/`-இல் இருந்தாலும் அல்லது OpenShell container-க்குள் இருந்தாலும் தானாகவே கண்டறியும்.

### இது எப்படி வேலை செய்கிறது

ClawMetry NemoClaw-ஐ இரண்டு வழிகளில் கண்டறிகிறது:

1. **Binary கண்டறிதல்** — `nemoclaw` CLI-ஐ சரிபார்த்து, sandbox தகவலைப் பெற `nemoclaw status`-ஐ இயக்குகிறது
2. **Container கண்டறிதல்** — `openshell`, `nemoclaw`, அல்லது `ghcr.io/nvidia/` images-க்கு இயங்கும் Docker containers-ஐ ஸ்கேன் செய்து, பின்னர் volume mounts அல்லது `docker cp` வழியாக அமர்வுகளைப் படிக்கிறது

NemoClaw containers-இலிருந்து ஒத்திசைக்கப்பட்ட அமர்வு கோப்புகள் கிளவுட் டாஷ்போர்டில் `runtime=nemoclaw` மற்றும் `container_id` மெட்டாடேட்டாவுடன் குறியிடப்படுகின்றன, அதனால் அவற்றை நிலையான OpenClaw அமர்வுகளிலிருந்து ஒரே பார்வையில் வேறுபடுத்தி அறியலாம்.

### பரிந்துரைக்கப்பட்ட அமைப்பு: HOST-இல் sync daemon

சிறந்த அனுபவத்திற்கு, ClawMetry-இன் sync daemon-ஐ **ஹோஸ்ட் கணினியில்** (sandbox-க்குள் அல்ல) இயக்கவும். இது NemoClaw நெட்வொர்க் கொள்கை கட்டுப்பாடுகளைத் தவிர்க்கிறது.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon இயங்கும் எந்த OpenShell containers-க்குள்ளும் உள்ள அமர்வுகளை தானாகவே கண்டுபிடிக்கும்.

### விருப்பம்: வெளிப்படையான sandbox பெயர்

தானியங்கு கண்டறிதல் வேலை செய்யவில்லை என்றால், சரியான sandbox-ஐ ClawMetry-க்கு சுட்டிக்காட்டவும்:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### sandbox-க்குள் இயக்குதல் (மேம்பட்டது)

sync daemon-ஐ OpenShell sandbox-க்குள் **இயக்க வேண்டியிருந்தால்**, அது ClawMetry ingest API-ஐ அடைய, உங்கள் NemoClaw நெட்வொர்க் கொள்கையில் இந்த egress விதியைச் சேர்க்கவும்:

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

### போர்ட்கள் மற்றும் endpoints

| Endpoint | போர்ட் | நெறிமுறை | தேவையா |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ஆம் (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | ஆம் (local dashboard UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | container அமர்வு கண்டறிதலுக்கு |

sync daemon `ingest.clawmetry.com`-க்கு மட்டுமே வெளிச்செல்லும் HTTPS அழைப்புகளைச் செய்கிறது. இன்பவுண்ட் போர்ட்கள் எதுவும் தேவையில்லை.

---

## Cloud வரிசைப்படுத்தல்

SSH tunnels, reverse proxy, மற்றும் Docker-க்கான **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**-ஐ பார்க்கவும்.

## சோதனை

இந்த ப்ராஜெக்ட் BrowserStack-உடன் சோதிக்கப்படுகிறது.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetry

நீங்கள் `clawmetry` CLI-ஐ ஒரு புதிய கணினியில் முதன்முறையாக இயக்கும்போது, ClawMetry ஒரே ஒரு அநாமதேய "first run" ping-ஐ `https://app.clawmetry.com/api/install`-க்கு அனுப்புகிறது. நிறுவல்களை எண்ணுவதற்கும் (OSS ப்ராஜெக்ட்டிற்கான எங்களிடம் உள்ள ஒரே மார்க்கெட்டிங் அளவீடு), எங்கள் பயனர்கள் எந்த ஏஜென்ட் framework-களை நிறுவியுள்ளனர் என்பதை அறியவும் இதைப் பயன்படுத்துகிறோம்.

**ஒரு நிறுவலுக்கு சரியாக ஒரு POST**, இதில் இருப்பவை:

| புலம் | எடுத்துக்காட்டு | ஏன் |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id`-இல் சேமிக்கப்பட்ட random UUID | dedup; உங்கள் மின்னஞ்சல் அல்லது api_key-உடன் இணைக்கப்படவில்லை |
| `version` | `0.12.167` | எந்த பதிப்புகள் பயன்பாட்டில் உள்ளன |
| `os` / `os_version` | `Darwin` / `25.3.0` | platform ஆதரவு முன்னுரிமைகள் |
| `python` | `3.11.15` | Python பதிப்பு ஆதரவு matrix |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | அடுத்து எந்த ஏஜென்ட்களுடன் நாங்கள் ஒருங்கிணைக்க வேண்டும் |
| `is_ci` / `ci_provider` | `true` / `github_actions` | மனித நிறுவல்களை CI சத்தத்திலிருந்து பிரிக்க |

**நாங்கள் அனுப்பாதவை**: IP (கிளவுட் சர்வர்-பக்கமாக request-இலிருந்து நாட்டுக் குறியீட்டைப் பெற்று, பின்னர் IP-ஐ நிராகரிக்கிறது), ஹோஸ்ட்பெயர், பயனர்பெயர், பணிமனை பாதை, கோப்பு உள்ளடக்கங்கள், உங்கள் api_key, உங்கள் மின்னஞ்சல், எந்த PII அல்லது பணிமனை-குறிப்பிட்டவை. வயர் payload [`clawmetry/telemetry.py`](clawmetry/telemetry.py)-இல் தணிக்கை செய்யக்கூடியது.

**Opt out** (இவற்றில் ஏதேனும் ஒன்று இதை நிரந்தரமாக முடக்கும்):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

இங்கு ஒரு நெட்வொர்க் தோல்வி `clawmetry` இயங்குவதை ஒருபோதும் தடுக்காது — ping என்பது daemon thread-இல் 3 வினாடி timeout-உடன் fire-and-forget ஆகும்.

## Star வரலாறு

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
  <sub>உருவாக்கியவர் <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> சுற்றுச்சூழல் அமைப்பின் ஒரு பகுதி</sub>
</p>
