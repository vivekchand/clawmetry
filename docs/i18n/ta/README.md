<!-- i18n-src:0e34918f8f2e -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்.** **14 AI ஏஜென்ட் ரன்டைம்களுக்கான** நிகழ்நேர கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex மற்றும் மேலும் 10. உங்கள் முழு ஏஜென்ட் கூட்டத்திற்கும் ஒரே டாஷ்போர்டு.

> 🌐 **இதை இதில் படியுங்கள்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. கட்டமைப்பு தேவையில்லை. எல்லாவற்றையும் தானாகவே கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும், அவ்வளவுதான்.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

ClawMetry, OpenClaw-க்கான கண்காணிப்பாக தொடங்கியது, இப்போது உங்கள் **முழு ஏஜென்ட் கூட்டத்தையும்** ஒரே டாஷ்போர்டில் அளவிடுகிறது, உங்கள் கணினியில் உள்ள ஒவ்வொரு ரன்டைமையும் தானாகவே கண்டறிந்து:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw மற்றும் NemoClaw ஓப்பன்-சோர்ஸ் ஆப்பில் இலவசம்; மற்ற ரன்டைம்கள் ClawMetry Cloud அல்லது சுய-ஹோஸ்ட் செய்யப்பட்ட Pro உரிமத்துடன் இயங்கும். ஹெடரிலிருந்து ரன்டைம்களை மாற்றவும், ஒவ்வொரு டேபும் - செலவு, டோக்கன்கள், கருவிகள், ட்ரேஸ்கள் - அந்த ரன்டைமிற்கு மீண்டும் வரம்பிடப்படும். சரியான இலவச/கட்டண பிரிவு, டையர் மேட்ரிக்ஸ், `/api/entitlement` வடிவம், மற்றும் `clawmetry license` CLI ஆகியவற்றுக்கு **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ஐப் பார்க்கவும்.

## நீங்கள் பெறுவது என்ன

- **Flow** — சேனல்கள், மூளை, கருவிகள் வழியாக செய்திகள் பாய்ந்து மீண்டும் திரும்புவதைக் காட்டும் நேரடி அனிமேட்டட் வரைபடம்
- **Overview** — ஆரோக்கிய சோதனைகள், செயல்பாட்டு ஹீட்மேப், அமர்வு எண்ணிக்கைகள், மாடல் தகவல்
- **Usage** — தினசரி/வாராந்திர/மாதாந்திர பிரிவுகளுடன் டோக்கன் மற்றும் செலவு கண்காணிப்பு
- **Sessions** — மாடல், டோக்கன்கள், கடைசி செயல்பாட்டுடன் செயலில் உள்ள ஏஜென்ட் அமர்வுகள்
- **Crons** — நிலை, அடுத்த இயக்கம், கால அளவுடன் திட்டமிடப்பட்ட வேலைகள்
- **Logs** — வண்ண-குறியிடப்பட்ட நிகழ்நேர பதிவு ஸ்ட்ரீமிங்
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, தினசரி குறிப்புகளை உலாவவும்
- **Transcripts** — அமர்வு வரலாறுகளைப் படிக்க சாட்-பபிள் UI
- **Alerts** — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், ஏஜென்ட்-ஆஃப்லைன் கண்டறிதல்; Slack, Discord, PagerDuty, Telegram, Email-க்கு வழிநடத்துகிறது
- **Approvals** — அழிவுகரமான நீக்குதல்கள், ஃபோர்ஸ் புஷ்கள், DB மாற்றங்கள், sudo, பேக்கேஜ் நிறுவல்கள், நெட்வொர்க் அழைப்புகளை ஒரு கிளிக் ஒப்புதலுக்குப் பின்னால் தடுக்கவும்

## ஸ்கிரீன்ஷாட்கள்

### 🧠 Brain — நேரடி ஏஜென்ட் நிகழ்வு ஸ்ட்ரீம்
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — டோக்கன் பயன்பாடு & அமர்வு சுருக்கம்
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — நிகழ்நேர கருவி அழைப்பு ஃபீட்
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — மாடல் & அமர்வு வாரியான செலவு பிரிவு
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — பணியிட கோப்பு உலாவி
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — நிலைப்பாடு & தணிக்கை பதிவு
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், Slack / Discord / PagerDuty / Email-க்கான வெப்ஹூக்குகள்
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ஆபத்தான கருவி அழைப்புகளை கைமுறை ஒப்புதலுக்குப் பின்னால் தடுக்கவும்; கொள்கை-ஆதரவு பாதுகாப்பு விதிகள்
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-க்கான செயல்படுத்தலுக்கு முந்தைய தடுப்பு** — ஒரு கட்டளை ஒரு
PreToolUse ஹூக்கை நிறுவுகிறது, இது பொருந்தும் கருவி அழைப்புகளை அவை இயங்குவதற்கு *முன்பே*
இடைநிறுத்தி உங்கள் முடிவுக்காக காத்திருக்கும் (உங்கள் தொலைபேசியிலிருந்து ஒரே தட்டு,
[cloud push notifications](https://app.clawmetry.com/push) இயக்கப்பட்டால்):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ஒரு நிராகரிப்பு அந்த ஒரு கருவி அழைப்பை மட்டுமே தடுக்கும் — ஏஜென்ட் அதன் அமர்வைத்
தக்கவைத்துக்கொண்டு வேறொரு அணுகுமுறையை முயற்சிக்கலாம். உங்கள் தொலைபேசியில் ஒப்புதல் அளிப்பது
Claude Code-இன் சொந்த அனுமதி வரியை தவிர்க்கிறது (நீங்கள் ஏற்கனவே பதிலளித்துவிட்டீர்கள்).
பொருந்தாத கருவிகள் ~40ms செலவாகும், மேலும் Claude Code-இன் இயல்பான அனுமதி ஓட்டத்திற்குள்
சென்றுவிடும். Claude Code தானே உங்களுக்காக காத்திருக்கும்போதும் (`permission_prompt` /
`idle_prompt` அறிவிப்புகள்) நீங்கள் தொலைபேசி புஷ் பெறுவீர்கள்.

## நிறுவுதல்

**ஒரே-வரி (பரிந்துரைக்கப்படுகிறது):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**சோர்ஸிலிருந்து:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 Frontend மேம்பாடு

v2 React ஆப் `frontend/` இல் உள்ளது, மேலும் Flask சர்வர் v2
இயக்கப்பட்டு தொடங்கப்படும்போது `/v2` இல் வழங்கப்படுகிறது.

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
`http://localhost:8900` க்கு ப்ராக்ஸி செய்கிறது, எனவே React ஆப் கூடுதல்
CORS அமைப்பு இல்லாமலேயே உள்ளூர் Flask சர்வருடன் பேச முடியும்.

Python பேக்கேஜுடன் அனுப்பப்படும் பண்டிலை உருவாக்க:

```bash
cd frontend
npm run build
```

உற்பத்தி பண்டில் `clawmetry/static/v2/dist/` இல் எழுதப்படுகிறது.

## ரன்டைம் / ஏஜென்ட் இணக்கத்தன்மை

ClawMetry, OpenClaw மட்டுமல்லாமல் பல AI-ஏஜென்ட் ரன்டைம்களையும் கவனிக்கிறது. OpenClaw அல்லாத ஒவ்வொரு ரன்டைமும் அதன் சொந்த அமர்வு வடிவத்தை ClawMetry-இன் ஒருங்கிணைந்த வடிவங்களாக மொழிபெயர்க்கும் ஒரு பிரத்யேக ரீடர் அடாப்டரை வழங்குகிறது; டீமன் அவற்றை அதே DuckDB ஸ்டோர் + கிளவுட் ஸ்னாப்ஷாட்டில் உள்ளிடுகிறது, ரன்டைமுடன் குறியிடப்பட்டு, மேலும் ஒன்றுக்கு மேற்பட்ட ரன்டைம்கள் இருக்கும்போது Session replay டேப் ஒரு **ரன்டைம் மாற்றி**யைக் காட்டுகிறது. முழு மேட்ரிக்ஸ் + ரன்டைம்களைச் சேர்ப்பதற்கான வழிகாட்டிக்கு [`docs/compatibility.md`](docs/compatibility.md) ஐயும், OpenClaw-குடும்ப அறிமுகத்திற்கு [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ஐயும் பார்க்கவும்.

[Perplexity's numbat](https://github.com/perplexityai/numbat) ஏஜென்ட்-பாதுகாப்பு கருவியை இயக்குகிறீர்களா? ClawMetry அதன் கண்டுபிடிப்புகள் மற்றும் அமலாக்க முடிவுகளை உடனடியாக உள்ளிடுகிறது — [`docs/NUMBAT.md`](docs/NUMBAT.md) ஐப் பார்க்கவும்.

| ரன்டைம் / ஏஜென்ட் | நிலை | குறிப்புகள் |
|---|---|---|
| **OpenClaw** | நேட்டிவ் | குறிப்பு ரன்டைம், தானாகவே கண்டறியப்படுகிறது |
| **PicoClaw** | பீட்டா அடாப்டர் | ஃபிளாட் `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள். |
| **NanoClaw** | பீட்டா அடாப்டர் | ஒவ்வொரு அமர்விற்கும் SQLite (`data/v2-sessions`). டிரான்ஸ்கிரிப்ட்கள் + செய்தி எண்ணிக்கைகள். |
| **Hermes** | பீட்டா அடாப்டர் | SQLite `~/.hermes/state.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன்கள்/செலவு. |
| **Claude Code** | பீட்டா அடாப்டர் | JSONL `~/.claude/projects/.../<id>.jsonl`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள் + சிந்தனை, டோக்கன் பயன்பாடு. |
| **Codex** | பீட்டா அடாப்டர் | Rollout JSONL `~/.codex/sessions/...`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Cursor** | பீட்டா அடாப்டர் | SQLite `state.vscdb`. Chat/composer டிரான்ஸ்கிரிப்ட்கள், மாடல். |
| **Aider** | பீட்டா அடாப்டர் | ஒவ்வொரு திட்டத்திற்கும் `.aider.chat.history.md`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன் எண்ணிக்கைகள். |
| **Goose** | பீட்டா அடாப்டர் | SQLite `~/.local/share/goose`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் மொத்தங்கள். |
| **opencode** | பீட்டா அடாப்டர் | SQLite `~/.local/share/opencode`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Qwen Code** | பீட்டா அடாப்டர் | JSONL `~/.qwen/projects/.../chats`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Pi** | பீட்டா அடாப்டர் | JSONL `~/.pi/agent/sessions`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Deep Agents** | பீட்டா அடாப்டர் | SQLite `~/.deepagents/.state/sessions.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **n8n** | பீட்டா அடாப்டர் | SQLite `~/.n8n/database.sqlite`. Workflow நிறைவேற்றங்கள், node இயக்கங்கள், AI Agent prompts, n8n பதிவு செய்யும் இடங்களில் மாடல் + டோக்கன்கள். |
| **Antigravity** | பீட்டா அடாப்டர் | `~/.gemini/<flavor>/brain/` இன் கீழ் Brain JSONL. உரையாடல்கள், கருவி படிகள், சிந்தனை, ஒவ்வொரு-தலைமுறை Gemini டோக்கன் பிரிவு + செலவு, பின்னணி-தலைமுறை எரிப்பு. |
| **GitHub Copilot** | பீட்டா அடாப்டர் | `~/.copilot/session-state/` இன் கீழ் Copilot CLI இன் `events.jsonl` + ஒவ்வொரு-அழைப்பு பயன்பாட்டு லெட்ஜர் `session-store.db`. உரையாடல்கள், கருவி அழைப்புகள், மாடல் திசைவழி, கேச்-விழிப்புணர்வு டோக்கன் பிரிவு, விற்பனையாளர்-பில் செய்யப்பட்ட AI-கிரெடிட் செலவு. |

"பீட்டா அடாப்டர்" என்பது அந்த ரன்டைமின் உண்மையான டிஸ்க்-ஆன் வடிவத்திற்கான ரீடரை ClawMetry வழங்குகிறது என்பதைக் குறிக்கிறது, ஒவ்வொன்றும் ஒரு உண்மையான கணினியில் உள்ள உண்மையான நிறுவலுக்கு எதிராக உருவாக்கப்பட்டு + சரிபார்க்கப்பட்டுள்ளது (`tests/fixtures/runtimes/<rt>/` ஐப் பார்க்கவும்). அடாப்டர்கள் படிக்க-மட்டும்; ஒவ்வொன்றும் அதன் ரன்டைம் உண்மையில் என்ன சேமிக்கிறது என்பதில் நேர்மையாக இருக்கும் (எ.கா., PicoClaw/NanoClaw/Cursor டோக்கன் செலவை டிஸ்க்கில் எழுதாது). ஒரு நோட்டில் பல ரன்டைம்கள் இயங்கும்போது, ரன்டைம் மாற்றி sessions காட்சியை ஒரு தூய்மையான ஆழமான-டைவிற்காக ஒன்றுக்கு வரம்பிடுகிறது.

## எந்த SDK ஏஜென்டையும் கண்காணிக்கவும் — out-loop செலவு பொறுப்பு

மேலே உள்ள ரன்டைம்கள் அனைத்தும் அமர்வுகளை டிஸ்க்கில் எழுதுகின்றன. உங்கள் சொந்த **உற்பத்தி ஏஜென்ட்** — நீங்கள் OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, அல்லது வெறும் `httpx` லூப்பில் கட்டியது — அப்படி எழுதாது. ClawMetry-இன் கட்டமைப்பு-தேவையில்லா இன்டர்செப்டர் இன்னும் அதன் LLM அழைப்புகளை (செலவு, டோக்கன்கள், லேட்டன்சி, பிழைகள்) `httpx`/`requests` ஐ மங்கி-பேட்ச் செய்வதன் மூலம் பிடிக்கிறது:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (அல்லது `CLAWMETRY_SOURCE=support-agent` env வேரியபிள்) ஒவ்வொரு அழைப்பையும் ஒரு **பெயரிடப்பட்ட மூலத்துடன்** குறியிடுகிறது, எனவே நீங்கள் இயக்கும் ஒவ்வொரு தயாரிப்பும் டாஷ்போர்டின் Overview-இல் உள்ள **🔌 Out-loop sources** கார்டில் தன் சொந்த முதல்-வகுப்பு, செலவு-பொறுப்புள்ள வரியாகத் தோன்றும் — ஒவ்வொரு ஏஜென்டிற்கும் அழைப்புகள், வழங்குநர்கள், லேட்டன்சி, பிழை விகிதம். மூலம் அமைக்கப்படவில்லையா? அழைப்புகள் இன்னும் கண்காணிக்கப்படும்; கார்டு மட்டும் மறைந்திருக்கும்.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

இது ரன்டைம் அடாப்டர்கள் உட்செலுத்தும் அதே தரவு அடுக்கு (DuckDB → கிளவுட் ஸ்னாப்ஷாட்), எனவே out-loop மூலங்கள் மற்ற எல்லாவற்றையும் போலவே கிளவுட் டாஷ்போர்டுக்கு ஒத்திசைக்கின்றன, E2E-மறையாக்கத்துடன்.

## OpenTelemetry — வழங்குநர்-நடுநிலை, உங்கள் ட்ரேஸ்களை எங்கும் அனுப்பவும்

ClawMetry **GenAI செமான்டிக் மரபுகளை** பயன்படுத்தி இரு திசைகளிலும் **OpenTelemetry** பேசுகிறது, எனவே உங்கள் ஏஜென்ட் ட்ரேஸ்கள் ஒரு கருவியில் ஒருபோதும் பூட்டப்படாது.

ஒவ்வொரு அமர்வையும் — LLM அழைப்புகள், கருவிகள், துணை-ஏஜென்ட்கள், டோக்கன்கள், செலவு — OTLP/HTTP GenAI ஸ்பான்களாக எந்த கலெக்டருக்கும் (Datadog, Grafana, Honeycomb, அல்லது உங்கள் சொந்த OTel Collector) **ஏற்றுமதி** செய்யவும்:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

அங்கீகார தலைப்புகள் மற்றும் வாக்கெடுப்பு இடைவெளி விருப்ப env வேரியபிள்கள்:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**உள்ளிடுதல்** — உள்ளமைந்த OTLP ரிசீவர் `/v1/traces` மற்றும் `/v1/metrics` இல் வேறு எதிலிருந்தும் ட்ரேஸ்கள் மற்றும் மெட்ரிக்குகளை ஏற்கிறது (protobuf உள்ளீட்டிற்கு `pip install clawmetry[otel]`).

நீங்கள் கட்டமைப்பு-தேவையில்லா, உள்ளூர்-முதல் ClawMetry டாஷ்போர்டையும் **மற்றும்** உங்கள் குழு ஏற்கனவே இயக்கும் எந்த பேக்எண்டிலும் உங்கள் தரவையும் பெறுகிறீர்கள் — பூட்டு இல்லை, இரண்டாவது ஏஜென்ட் நிறுவ வேண்டியதில்லை.

## கட்டமைப்பு

பெரும்பாலான மக்களுக்கு எந்த கட்டமைப்பும் தேவையில்லை. ClawMetry உங்கள் பணியிடம், பதிவுகள், அமர்வுகள், மற்றும் crons ஐ தானாகவே கண்டறிகிறது.

நீங்கள் தனிப்பயனாக்க வேண்டியிருந்தால்:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

அனைத்து விருப்பங்களும்: `clawmetry --help`

## ஆதரிக்கப்படும் சேனல்கள்

நீங்கள் கட்டமைத்த ஒவ்வொரு OpenClaw சேனலுக்கும் ClawMetry நேரடி செயல்பாட்டைக் காட்டுகிறது. உங்கள் `openclaw.json` இல் உண்மையில் அமைக்கப்பட்டுள்ள சேனல்கள் மட்டுமே Flow வரைபடத்தில் தோன்றும் — கட்டமைக்கப்படாதவை தானாகவே மறைக்கப்படும்.

Flow-இல் உள்ள எந்த சேனல் நோடிலும் கிளிக் செய்தால், உள்வரும்/வெளிச்செல்லும் செய்தி எண்ணிக்கைகளுடன் ஒரு நேரடி சாட் பபிள் காட்சி காணப்படும்.

| சேனல் | நிலை | நேரடி பாப்அப் | குறிப்புகள் |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ முழு | ✅ | செய்திகள், புள்ளிவிவரங்கள், 10s புதுப்பிப்பு |
| 💬 **iMessage** | ✅ முழு | ✅ | `~/Library/Messages/chat.db` ஐ நேரடியாகப் படிக்கிறது |
| 💚 **WhatsApp** | ✅ முழு | ✅ | WhatsApp Web (Baileys) வழியாக |
| 🔵 **Signal** | ✅ முழு | ✅ | signal-cli வழியாக |
| 🟣 **Discord** | ✅ முழு | ✅ | Guild + channel கண்டறிதல் |
| 🟪 **Slack** | ✅ முழு | ✅ | Workspace + channel கண்டறிதல் |
| 🌐 **Webchat** | ✅ முழு | ✅ | உள்ளமைந்த வலை UI அமர்வுகள் |
| 📡 **IRC** | ✅ முழு | ✅ | டெர்மினல்-பாணி பபிள் UI |
| 🍏 **BlueBubbles** | ✅ முழு | ✅ | BlueBubbles REST API வழியாக iMessage |
| 🔵 **Google Chat** | ✅ முழு | ✅ | Chat API வெப்ஹூக்குகள் வழியாக |
| 🟣 **MS Teams** | ✅ முழு | ✅ | Teams bot plugin வழியாக |
| 🔷 **Mattermost** | ✅ முழு | ✅ | சுய-ஹோஸ்ட் செய்யப்பட்ட குழு சாட் |
| 🟩 **Matrix** | ✅ முழு | ✅ | பரவலாக்கப்பட்டது, E2EE ஆதரவு |
| 🟢 **LINE** | ✅ முழு | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ முழு | ✅ | பரவலாக்கப்பட்ட NIP-04 DMs |
| 🟣 **Twitch** | ✅ முழு | ✅ | IRC இணைப்பு வழியாக சாட் |
| 🔷 **Feishu/Lark** | ✅ முழு | ✅ | WebSocket நிகழ்வு சந்தா |
| 🔵 **Zalo** | ✅ முழு | ✅ | Zalo Bot API |

> **தானியங்கு-கண்டறிதல்:** ClawMetry உங்கள் `~/.openclaw/openclaw.json` ஐப் படித்து, நீங்கள் உண்மையில் கட்டமைத்த சேனல்களை மட்டுமே காட்டுகிறது. கைமுறை அமைப்பு தேவையில்லை.

## Docker வரிசைப்படுத்தல்

ClawMetry ஐ ஒரு கன்டெய்னரில் இயக்க விரும்புகிறீர்களா? பிரச்சனை இல்லை! 🐳

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

> **குறிப்பு:** Docker இல் இயக்கும்போது, ClawMetry உங்கள் அமைப்பை தானாகவே கண்டறிய, உங்கள் ஏஜென்டின் தரவு + பதிவு அடைவுகளை (எ.கா., `~/.openclaw`, `~/.claude`, `~/.codex`) மவுன்ட் செய்யவும்.

## தேவைகள்

- Python 3.8+
- Flask (pip வழியாக தானாகவே நிறுவப்படும்)
- அதே கணினியில் ஒரு AI ஏஜென்ட் ரன்டைம்: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, அல்லது GitHub Copilot (அல்லது Docker-க்கான மவுன்ட் செய்யப்பட்ட வால்யூம்கள்)
- Linux அல்லது macOS

## NemoClaw / OpenShell ஆதரவு

ClawMetry தானாகவே [NemoClaw](https://github.com/NVIDIA/NemoClaw) ஐ கண்டறிகிறது — OpenClaw-க்கான NVIDIA-இன் நிறுவன பாதுகாப்பு ரேப்பர், இது sandboxed OpenShell கன்டெய்னர்களுக்குள் ஏஜென்ட்களை இயக்குகிறது.

பெரும்பாலான சந்தர்ப்பங்களில் கூடுதல் கட்டமைப்பு தேவையில்லை. அமர்வு கோப்புகள் ஹோஸ்டில் உள்ள `~/.openclaw/` இலோ அல்லது ஒரு OpenShell கன்டெய்னருக்குள்ளோ இருந்தாலும், சிங்க் டீமன் தானாகவே அவற்றைக் கண்டறியும்.

### இது எப்படி வேலை செய்கிறது

ClawMetry NemoClaw ஐ இரண்டு வழிகளில் கண்டறிகிறது:

1. **பைனரி கண்டறிதல்** — `nemoclaw` CLI க்காக சரிபார்த்து, sandbox தகவலைப் பெற `nemoclaw status` ஐ இயக்குகிறது
2. **கன்டெய்னர் கண்டறிதல்** — `openshell`, `nemoclaw`, அல்லது `ghcr.io/nvidia/` இமேஜ்களுக்காக இயங்கும் Docker கன்டெய்னர்களை ஸ்கேன் செய்து, பின்னர் வால்யூம் மவுன்ட்கள் அல்லது `docker cp` வழியாக அமர்வுகளைப் படிக்கிறது

NemoClaw கன்டெய்னர்களிலிருந்து ஒத்திசைக்கப்பட்ட அமர்வு கோப்புகள் கிளவுட் டாஷ்போர்டில் `runtime=nemoclaw` மற்றும் `container_id` மெட்டாடேட்டாவுடன் குறியிடப்படுகின்றன, எனவே நீங்கள் அவற்றை நிலையான OpenClaw அமர்வுகளிலிருந்து ஒரே பார்வையில் வேறுபடுத்தி அறியலாம்.

### பரிந்துரைக்கப்பட்ட அமைப்பு: HOST இல் சிங்க் டீமன்

சிறந்த அனுபவத்திற்கு, ClawMetry-இன் சிங்க் டீமனை (sandbox-க்குள் அல்ல) **ஹோஸ்ட் கணினியில்** இயக்கவும். இது NemoClaw நெட்வொர்க் கொள்கை கட்டுப்பாடுகளைத் தவிர்க்கிறது.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

சிங்க் டீமன் தானாகவே இயங்கும் எந்த OpenShell கன்டெய்னர்களுக்குள்ளும் அமர்வுகளைக் கண்டறியும்.

### விருப்பம்: வெளிப்படையான sandbox பெயர்

தானியங்கு-கண்டறிதல் வேலை செய்யவில்லை எனில், ClawMetry-ஐ சரியான sandbox-இற்கு சுட்டிக்காட்டவும்:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### sandbox-க்குள் இயக்குதல் (மேம்பட்டது)

நீங்கள் சிங்க் டீமனை OpenShell sandbox-க்குள் **இயக்க வேண்டும்** எனில், அது ClawMetry ingest API ஐ அடைய, உங்கள் NemoClaw நெட்வொர்க் கொள்கையில் இந்த egress விதியைச் சேர்க்கவும்:

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

### போர்ட்கள் மற்றும் எண்ட்பாயிண்ட்கள்

| எண்ட்பாயிண்ட் | போர்ட் | நெறிமுறை | தேவை |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ஆம் (சிங்க் டீமன் → கிளவுட்) |
| `localhost:8900` | 8900 | HTTP | ஆம் (உள்ளூர் டாஷ்போர்டு UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | கன்டெய்னர் அமர்வு கண்டறிதலுக்கு |

சிங்க் டீமன் `ingest.clawmetry.com` க்கு மட்டுமே வெளிச்செல்லும் HTTPS அழைப்புகளை செய்கிறது. உள்வரும் போர்ட்கள் எதுவும் தேவையில்லை.

---

## கிளவுட் வரிசைப்படுத்தல்

SSH டன்னல்கள், ரிவர்ஸ் ப்ராக்ஸி, மற்றும் Docker க்கு **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ஐப் பார்க்கவும்.

## சோதனை

இந்த திட்டம் BrowserStack உடன் சோதிக்கப்படுகிறது.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## டெலிமெட்ரி

ClawMetry அநாமதேய நிறுவல்-வாழ்க்கைச்சுழற்சி பிங்குகளை
`https://app.clawmetry.com/api/install` க்கு அனுப்புகிறது: புதிய கணினியில்
முதல் முறையாக `clawmetry` CLI ஐ இயக்கும்போது ஒரு `install` பிங், புதிய
பதிப்பிற்கு மேம்படுத்திய பின் முதல் இயக்கத்தில் ஒரு `update` பிங், மற்றும்
டாஷ்போர்டுக்குள் ஆன்போர்டிங் தேர்வை முடிக்கும்போது ஒரு `onboarded` பிங்.
உண்மையான நிறுவல்களை எண்ண இதைப் பயன்படுத்துகிறோம் (மூல PyPI பதிவிறக்க
எண்கள் ~98% மிரர்கள், CI, மற்றும் தானியங்கி-புதுப்பிப்பு மறு-பதிவிறக்கங்கள்)
மற்றும் எந்த ஏஜென்ட் கட்டமைப்புகள் மற்றும் பதிப்புகள் உண்மையில் பயன்பாட்டில்
உள்ளன என்பதை அறிய.

**ஒவ்வொரு பதிப்பிற்கும் ஒவ்வொரு வாழ்க்கைச்சுழற்சி நிகழ்விற்கும் அதிகபட்சம் ஒரு POST**, இதில் அடங்கியிருப்பது:

| புலம் | எடுத்துக்காட்டு | ஏன் |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` இல் சேமிக்கப்பட்ட ரேண்டம் UUID | நகல்நீக்கம்; நீங்கள் வெளிப்படையாக Cloud sync ஐ இணைக்கும் வரை அநாமதேயமானது (பின்னர் அங்கீகரிக்கப்பட்ட டீமன் ஹார்ட்பீட் இதை எடுத்துச் செல்கிறது, இந்த நிறுவலை உங்கள் கணக்குடன் இணைக்கிறது) |
| `event` | `install` / `update` / `onboarded` | புதிய நிறுவல் vs ஏற்கனவே உள்ளதன் மேம்படுத்தல் |
| `version` | `0.12.167` | பயன்பாட்டில் உள்ள பதிப்புகள் என்ன |
| `os` / `os_version` | `Darwin` / `25.3.0` | தள ஆதரவு முன்னுரிமைகள் |
| `python` | `3.11.15` | Python பதிப்பு ஆதரவு மேட்ரிக்ஸ் |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | அடுத்து எந்த ஏஜென்ட்களுடன் நாங்கள் ஒருங்கிணைக்க வேண்டும் |
| `is_ci` / `ci_provider` | `true` / `github_actions` | மனித நிறுவல்களை CI சத்தத்திலிருந்து பிரிக்கவும் |

**நாங்கள் அனுப்பாதவை**: IP (கிளவுட் கோரிக்கையிலிருந்து சர்வர்-பக்கத்தில்
நாட்டுக் குறியீட்டைப் பெற்று, பின்னர் IP ஐ நிராகரிக்கிறது), ஹோஸ்ட்பெயர்,
பயனர்பெயர், பணியிடப் பாதை, கோப்பு உள்ளடக்கங்கள், உங்கள் api_key, உங்கள்
மின்னஞ்சல், PII அல்லது பணியிடம்-தொடர்பான எதுவும். வயர் பேலோட்
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) இல் தணிக்கை செய்யக்கூடியது.

**விலகல்** (இவற்றில் ஏதேனும் ஒன்று இதை நிரந்தரமாக முடக்கும்):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

இங்கு ஒரு நெட்வொர்க் தோல்வி `clawmetry` இயங்குவதை ஒருபோதும் தடுக்காது —
பிங் டீமன் த்ரெட்டில் 3 வினாடி டைம்அவுட்டுடன் fire-and-forget ஆகும்.

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
  <sub>உருவாக்கியவர் <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> சுற்றுச்சூழல் அமைப்பின் ஒரு பகுதி</sub>
</p>
