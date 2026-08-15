<!-- i18n-src:c422fb7dd0da -->
> தமிழ் translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**உங்கள் ஏஜென்ட் சிந்திப்பதைப் பாருங்கள்.** **20 AI ஏஜென்ட் ரன்டைம்களுக்கான** நிகழ்நேர கண்காணிப்பு: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex மற்றும் மேலும் 16. உங்கள் முழு ஏஜென்ட் கூட்டத்திற்கும் ஒரே டாஷ்போர்டு.

> 🌐 **இதை இதில் படிக்கவும்:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [மேலும் →](docs/i18n/)

ஒரே கட்டளை. கட்டமைப்பு தேவையில்லை. எல்லாவற்றையும் தானாக கண்டறியும்.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** இல் திறக்கும், அவ்வளவே.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 20 ஏஜென்ட் ரன்டைம்களுடன் இயங்குகிறது

ClawMetry OpenClaw-க்கான கண்காணிப்பாகத் தொடங்கியது, இப்போது உங்கள் **முழு ஏஜென்ட் கூட்டத்தையும்** ஒரே டாஷ்போர்டில் அளவிடுகிறது, உங்கள் இயந்திரத்தில் உள்ள ஒவ்வொரு ரன்டைமையும் தானாக கண்டறிகிறது:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw மற்றும் NemoClaw ஓபன்-சோர்ஸ் ஆப்பில் இலவசம்; மற்ற ரன்டைம்கள் ClawMetry Cloud அல்லது சுய-ஹோஸ்ட் செய்யப்பட்ட Pro உரிமத்துடன் இயங்கும். ஹெடரிலிருந்து ரன்டைம்களை மாற்றவும், ஒவ்வொரு டேபும் - செலவு, டோக்கன்கள், கருவிகள், ட்ரேஸ்கள் - அந்த ரன்டைமிற்கு மறுஅளவிடப்படும். சரியான இலவச/கட்டண பிரிவு, டையர் மேட்ரிக்ஸ், `/api/entitlement` வடிவம், மற்றும் `clawmetry license` CLI ஆகியவற்றிற்கு **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ஐப் பார்க்கவும்.

## நீங்கள் பெறுவது என்ன

- **Flow** — சேனல்கள், மூளை, கருவிகள் வழியாக செய்திகள் பாய்வதையும் திரும்பி வருவதையும் காட்டும் நேரடி அனிமேட்டட் வரைபடம்
- **Overview** — ஆரோக்கிய சோதனைகள், செயல்பாட்டு ஹீட்மேப், அமர்வு எண்ணிக்கைகள், மாடல் தகவல்
- **Usage** — தினசரி/வாராந்திர/மாதாந்திர பிரிவுகளுடன் டோக்கன் மற்றும் செலவு கண்காணிப்பு
- **Sessions** — மாடல், டோக்கன்கள், கடைசி செயல்பாடு ஆகியவற்றுடன் செயலில் உள்ள ஏஜென்ட் அமர்வுகள்
- **Crons** — நிலை, அடுத்த இயக்கம், கால அளவுடன் திட்டமிடப்பட்ட வேலைகள்
- **Logs** — வண்ண-குறியிடப்பட்ட நிகழ்நேர பதிவு ஸ்ட்ரீமிங்
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, தினசரி குறிப்புகளை உலாவவும்
- **Transcripts** — அமர்வு வரலாறுகளைப் படிக்க சாட்-பபிள் UI
- **Alerts** — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், ஏஜென்ட்-ஆஃப்லைன் கண்டறிதல்; Slack, Discord, PagerDuty, Telegram, Email க்கு வழிநடத்துகிறது
- **Approvals** — அழிவூட்டும் நீக்கல்கள், ஃபோர்ஸ் புஷ்கள், DB மாற்றங்கள், sudo, தொகுப்பு நிறுவல்கள், நெட்வொர்க் அழைப்புகளை ஒரே-கிளிக் ஒப்புதலுக்குப் பின்னால் தடுக்கும்

## ஸ்கிரீன்ஷாட்கள்

### 🧠 Brain — நேரடி ஏஜென்ட் நிகழ்வு ஸ்ட்ரீம்
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — டோக்கன் பயன்பாடு மற்றும் அமர்வு சுருக்கம்
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — நிகழ்நேர கருவி அழைப்பு ஃபீட்
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — மாடல் மற்றும் அமர்வு வாரியான செலவு பிரிவு
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — பணியிட கோப்பு உலாவி
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — நிலைப்பாடு மற்றும் தணிக்கை பதிவு
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — பட்ஜெட் வரம்புகள், பிழை-விகித தூண்டுதல்கள், Slack / Discord / PagerDuty / Email க்கு வெப்ஹூக்குகள்
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ஆபத்தான கருவி அழைப்புகளை கைமுறை ஒப்புதலுக்குப் பின்னால் தடுக்கவும்; கொள்கை-ஆதரவு பாதுகாப்பு விதிகள்
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code-க்கான செயல்படுத்தலுக்கு முந்தைய தடுப்பு** — ஒரே கட்டளை ஒரு
PreToolUse ஹூக்கை நிறுவுகிறது, இது பொருந்தும் கருவி அழைப்புகளை அவை இயங்குவதற்கு *முன்பே*
இடைநிறுத்தி உங்கள் முடிவுக்காக காத்திருக்கும் (உங்கள் ஃபோனிலிருந்து ஒரே தட்டல்,
[cloud push notifications](https://app.clawmetry.com/push) இயக்கப்பட்டிருந்தால்):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ஒரு நிராகரிப்பு அந்த ஒரு கருவி அழைப்பை மட்டும் தடுக்கும் — ஏஜென்ட் அதன் அமர்வைத் தக்கவைத்துக்கொண்டு
வேறு அணுகுமுறையை முயற்சிக்கலாம். உங்கள் ஃபோனில் ஒப்புதல் அளிப்பது Claude Code-இன் சொந்த
அனுமதி வேண்டுகோளைத் தவிர்க்கிறது (நீங்கள் ஏற்கனவே பதிலளித்துவிட்டீர்கள்). பொருந்தாத கருவிகள் ~40ms
செலவழிக்கும், மேலும் Claude Code-இன் இயல்பான அனுமதி ஓட்டத்திற்குச் செல்லும். Claude Code
தானே உங்களுக்காகக் காத்திருக்கும்போது (`permission_prompt` / `idle_prompt` அறிவிப்புகள்)
உங்களுக்கு ஃபோன் புஷ் கிடைக்கும்.

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

v2 React ஆப் `frontend/` இல் உள்ளது, மேலும் v2 இயக்கப்பட்ட நிலையில்
Flask சர்வர் தொடங்கும்போது `/v2` இல் வழங்கப்படுகிறது.

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

`http://localhost:5173/v2/` ஐத் திறக்கவும். Vite `/api` கோரிக்கைகளை
`http://localhost:8900` க்கு ப்ராக்ஸி செய்கிறது, எனவே React ஆப் கூடுதல்
CORS அமைப்பு இல்லாமல் லோக்கல் Flask சர்வருடன் தொடர்பு கொள்ள முடியும்.

Python தொகுப்புடன் அனுப்பப்படும் பண்டிலைக் கட்டமைக்க:

```bash
cd frontend
npm run build
```

உற்பத்தி பண்டில் `clawmetry/static/v2/dist/` இல் எழுதப்படுகிறது.

## ரன்டைம் / ஏஜென்ட் இணக்கத்தன்மை

ClawMetry OpenClaw மட்டுமல்ல, பல AI-ஏஜென்ட் ரன்டைம்களையும் கண்காணிக்கிறது. ஒவ்வொரு OpenClaw-அல்லாத ரன்டைமும் அதன் சொந்த அமர்வு வடிவமைப்பை ClawMetry-இன் ஒருங்கிணைந்த வடிவங்களாக மொழிபெயர்க்கும் ஒரு பிரத்யேக ரீடர் அடாப்டரை வழங்குகிறது; டீமன் அவற்றை அதே DuckDB ஸ்டோர் + கிளவுட் ஸ்னாப்ஷாட்டில் உள்ளீடு செய்கிறது, ரன்டைமுடன் குறியிடப்பட்டு, மேலும் ஒன்றுக்கு மேற்பட்ட ரன்டைம்கள் இருக்கும்போது Session replay டேப் ஒரு **ரன்டைம் மாற்றியை** காட்டுகிறது. முழு மேட்ரிக்ஸ் + ரன்டைம்களைச் சேர்ப்பதற்கான வழிகாட்டிக்கு [`docs/compatibility.md`](docs/compatibility.md) ஐயும், OpenClaw-குடும்ப அறிமுகத்திற்கு [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) ஐயும் பார்க்கவும்.

[Perplexity-இன் numbat](https://github.com/perplexityai/numbat) ஏஜென்ட்-பாதுகாப்பு கருவியை இயக்குகிறீர்களா? ClawMetry அதன் கண்டுபிடிப்புகள் மற்றும் அமலாக்க முடிவுகளை உடனடியாக உள்ளீடு செய்கிறது — [`docs/NUMBAT.md`](docs/NUMBAT.md) ஐப் பார்க்கவும்.

| ரன்டைம் / ஏஜென்ட் | நிலை | குறிப்புகள் |
|---|---|---|
| **OpenClaw** | சொந்தமானது | குறிப்பு ரன்டைம், தானாக கண்டறியப்படுகிறது |
| **PicoClaw** | பீட்டா அடாப்டர் | Flat `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள். |
| **NanoClaw** | பீட்டா அடாப்டர் | ஒவ்வொரு அமர்விற்கும் SQLite (`data/v2-sessions`). டிரான்ஸ்கிரிப்ட்கள் + செய்தி எண்ணிக்கைகள். |
| **Hermes** | பீட்டா அடாப்டர் | SQLite `~/.hermes/state.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன்கள்/செலவு. |
| **Claude Code** | பீட்டா அடாப்டர் | JSONL `~/.claude/projects/.../<id>.jsonl`. டிரான்ஸ்கிரிப்ட்கள், மாடல், சிந்தனையுடன் கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Codex** | பீட்டா அடாப்டர் | Rollout JSONL `~/.codex/sessions/...`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Cursor** | பீட்டா அடாப்டர் | SQLite `state.vscdb`. சாட்/காம்போசர் டிரான்ஸ்கிரிப்ட்கள், மாடல். |
| **Aider** | பீட்டா அடாப்டர் | ஒவ்வொரு திட்டத்திற்கும் `.aider.chat.history.md`. டிரான்ஸ்கிரிப்ட்கள், மாடல், டோக்கன் எண்ணிக்கைகள். |
| **Goose** | பீட்டா அடாப்டர் | SQLite `~/.local/share/goose`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் மொத்தங்கள். |
| **opencode** | பீட்டா அடாப்டர் | SQLite `~/.local/share/opencode`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Qwen Code** | பீட்டா அடாப்டர் | JSONL `~/.qwen/projects/.../chats`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன் பயன்பாடு. |
| **Pi** | பீட்டா அடாப்டர் | JSONL `~/.pi/agent/sessions`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **Deep Agents** | பீட்டா அடாப்டர் | SQLite `~/.deepagents/.state/sessions.db`. டிரான்ஸ்கிரிப்ட்கள், மாடல், கருவி அழைப்புகள், டோக்கன்கள் + செலவு. |
| **n8n** | பீட்டா அடாப்டர் | SQLite `~/.n8n/database.sqlite`. Workflow இயக்கங்கள், நோட் ரன்கள், AI Agent ப்ராம்ப்ட்கள், n8n பதிவு செய்யும் இடங்களில் மாடல் + டோக்கன்கள். |
| **Antigravity** | பீட்டா அடாப்டர் | `~/.gemini/<flavor>/brain/` க்குக் கீழே Brain JSONL. உரையாடல்கள், கருவி படிகள், சிந்தனை, ஒவ்வொரு-உருவாக்கத்திற்கான Gemini டோக்கன் பிரிவு + செலவு, பின்னணி-உருவாக்க எரிப்பு. |
| **GitHub Copilot** | பீட்டா அடாப்டர் | `~/.copilot/session-state/` இன் கீழ் Copilot CLI `events.jsonl` + ஒவ்வொரு-அழைப்பு பயன்பாட்டு லெட்ஜரான `session-store.db`. உரையாடல்கள், கருவி அழைப்புகள், மாடல் வழிநடத்துதல், கேச்-விழிப்புணர்வு டோக்கன் பிரிவு, விற்பனையாளர்-பில் செய்யப்பட்ட AI-கிரெடிட் செலவு. |
| **Grok** | பீட்டா அடாப்டர் | xAI Grok Build CLI (`~/.grok/bin/grok` இன் கீழ் Rust பைனரி): குளோபல் நிகழ்வு பதிவு `~/.grok/logs/unified.jsonl` + ஒவ்வொரு-அமர்வு `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. உரையாடல்கள், ஒவ்வொரு-முறை டோக்கன் பிரிவு, மாடல் வழிநடத்துதல், மற்றும் CLI-இன் வெளிச்செல்லும் ரெப்போ பேலோட் `~/.grok/upload_queue/` இல் நிலைநிறுத்தப்பட்டு, உங்கள் இயந்திரத்திலிருந்து என்ன வெளியேறியது என்பதைப் பார்க்க முடியும். |

"பீட்டா அடாப்டர்" என்பது ClawMetry அந்த ரன்டைமின் உண்மையான ஆன்-டிஸ்க் வடிவமைப்பிற்கான ரீடரை வழங்குகிறது என்பதைக் குறிக்கிறது, ஒவ்வொன்றும் உண்மையான இயந்திரத்தில் உண்மையான நிறுவலுக்கு எதிராக கட்டமைக்கப்பட்டு + சரிபார்க்கப்பட்டது (`tests/fixtures/runtimes/<rt>/` ஐப் பார்க்கவும்). அடாப்டர்கள் ரீட்-ஒன்லி; ஒவ்வொன்றும் அதன் ரன்டைம் உண்மையில் என்ன சேமிக்கிறது என்பதில் நேர்மையானது (எ.கா. PicoClaw/NanoClaw/Cursor டோக்கன் செலவை டிஸ்க்கில் எழுதுவதில்லை). ஒரு நோடில் பல ரன்டைம்கள் இயங்கும்போது, ரன்டைம் மாற்றி சுத்தமான ஆழமான ஆய்விற்காக அமர்வுகள் காட்சியை ஒன்றுக்கு அளவிடும்.

## எந்த SDK ஏஜென்டையும் கண்காணிக்கவும் — அவுட்-லூப் செலவு பண்பளிப்பு

மேலே உள்ள ரன்டைம்கள் அனைத்தும் அமர்வுகளை டிஸ்க்கில் எழுதுகின்றன. நீங்கள் உருவாக்கிய உங்கள் சொந்த **உற்பத்தி ஏஜென்ட்** — OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, அல்லது வெறும் `httpx` லூப் மீது கட்டப்பட்டது — அப்படி எழுதுவதில்லை. ClawMetry-இன் கட்டமைப்பு தேவையில்லாத இன்டர்செப்டர் `httpx`/`requests` ஐ மங்கி-பேட்ச் செய்வதன் மூலம் அதன் LLM அழைப்புகளை (செலவு, டோக்கன்கள், தாமதம், பிழைகள்) இன்னும் பிடிக்கிறது:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (அல்லது `CLAWMETRY_SOURCE=support-agent` சூழல் மாறி) ஒவ்வொரு அழைப்பையும் ஒரு **பெயரிடப்பட்ட மூலத்துடன்** குறியிடுகிறது, எனவே நீங்கள் இயக்கும் ஒவ்வொரு தயாரிப்பும் டாஷ்போர்டின் Overview-இல் உள்ள **🔌 Out-loop sources** கார்டில் அதன் சொந்த முதல்-வகுப்பு, செலவு-பண்பளிக்கக்கூடிய வரியாகத் தோன்றும் — ஒவ்வொரு ஏஜென்டிற்கும் அழைப்புகள், வழங்குநர்கள், தாமதம், பிழை விகிதம். மூலம் அமைக்கப்படவில்லையா? அழைப்புகள் இன்னும் கண்காணிக்கப்படும்; கார்டு மட்டும் மறைந்தே இருக்கும்.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

இது ரன்டைம் அடாப்டர்கள் உள்ளீடு செய்யும் அதே தரவு அடுக்கு (DuckDB → கிளவுட் ஸ்னாப்ஷாட்), எனவே அவுட்-லூப் மூலங்கள் மற்ற அனைத்தையும் போலவே கிளவுட் டாஷ்போர்டுக்கு ஒத்திசைக்கப்படுகின்றன, E2E-குறியாக்கம் செய்யப்பட்டு.

## OpenTelemetry — விற்பனையாளர்-நடுநிலை, உங்கள் ட்ரேஸ்களை எங்கு வேண்டுமானாலும் அனுப்பவும்

ClawMetry இரு திசைகளிலும் **OpenTelemetry** பேசுகிறது, **GenAI செமான்டிக் மரபுகளைப்** பயன்படுத்தி, எனவே உங்கள் ஏஜென்ட் ட்ரேஸ்கள் ஒரே ஒரு கருவியில் ஒருபோதும் பூட்டப்படாது.

**Export** — ஒவ்வொரு அமர்வையும் — LLM அழைப்புகள், கருவிகள், துணை-ஏஜென்ட்கள், டோக்கன்கள், செலவு — எந்த கலெக்டருக்கும் (Datadog, Grafana, Honeycomb, அல்லது உங்கள் சொந்த OTel Collector) OTLP/HTTP GenAI ஸ்பான்களாக:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

அங்கீகார ஹெடர்கள் மற்றும் போல் இடைவெளி விருப்பமான சூழல் மாறிகள்:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** — உள்ளமைக்கப்பட்ட OTLP ரிசீவர் ட்ரேஸ்கள், பதிவுகள், மற்றும் மெட்ரிக்குகளை `/v1/traces`, `/v1/logs`, மற்றும் `/v1/metrics` இல் ஏற்றுக்கொள்கிறது. வேறு எதையும் OpenTelemetry-கருவியமைக்கப்பட்ட ஆப்பை அதை நோக்கி இயக்கவும்:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON ட்ரேஸ்கள் மற்றும் பதிவுகள் வெற்று `pip install clawmetry` இல் கூடுதல் இல்லாமல் வேலை செய்கின்றன. Protobuf ingest (மற்றும் OTLP/JSON மெட்ரிக்குகள்) க்கு `pip install clawmetry[otel]` தேவை. தனது சொந்த `service.name` ஐ அமைக்கும் ஒரு ஆப் ரன்டைம் மாற்றியில் அதன் சொந்த செலவு மற்றும் டோக்கன்களுடன் அதன் சொந்த ஏஜென்டாகத் தோன்றும்.

நீங்கள் கட்டமைப்பு தேவையில்லாத, லோக்கல்-முதல் ClawMetry டாஷ்போர்டையும் **மேலும்** உங்கள் அணி ஏற்கனவே இயக்கும் எந்த பேக்எண்டிலும் உங்கள் தரவையும் பெறுவீர்கள் — பூட்டு இல்லை, இரண்டாவது ஏஜென்ட் நிறுவ வேண்டியதில்லை.

## கட்டமைப்பு

பெரும்பாலான மக்களுக்கு கட்டமைப்பு தேவையில்லை. ClawMetry உங்கள் பணியிடம், பதிவுகள், அமர்வுகள், மற்றும் cron-களை தானாக கண்டறிகிறது.

நீங்கள் தனிப்பயனாக்க வேண்டியிருந்தால்:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

அனைத்து விருப்பங்களும்: `clawmetry --help`

## ஆதரிக்கப்படும் சேனல்கள்

நீங்கள் கட்டமைத்துள்ள ஒவ்வொரு OpenClaw சேனலுக்கும் ClawMetry நேரடி செயல்பாட்டைக் காட்டுகிறது. உங்கள் `openclaw.json` இல் உண்மையில் அமைக்கப்பட்ட சேனல்கள் மட்டுமே Flow வரைபடத்தில் தோன்றும் — கட்டமைக்கப்படாதவை தானாக மறைக்கப்படும்.

Flow-இல் எந்த சேனல் நோடையும் கிளிக் செய்து, உள்வரும்/வெளிச்செல்லும் செய்தி எண்ணிக்கைகளுடன் நேரடி சாட் பபிள் காட்சியைப் பார்க்கலாம்.

| சேனல் | நிலை | நேரடி பாப்அப் | குறிப்புகள் |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ முழு | ✅ | செய்திகள், புள்ளிவிவரங்கள், 10வி புதுப்பிப்பு |
| 💬 **iMessage** | ✅ முழு | ✅ | `~/Library/Messages/chat.db` ஐ நேரடியாகப் படிக்கிறது |
| 💚 **WhatsApp** | ✅ முழு | ✅ | WhatsApp Web (Baileys) வழியாக |
| 🔵 **Signal** | ✅ முழு | ✅ | signal-cli வழியாக |
| 🟣 **Discord** | ✅ முழு | ✅ | Guild + சேனல் கண்டறிதல் |
| 🟪 **Slack** | ✅ முழு | ✅ | பணியிடம் + சேனல் கண்டறிதல் |
| 🌐 **Webchat** | ✅ முழு | ✅ | உள்ளமைக்கப்பட்ட வெப் UI அமர்வுகள் |
| 📡 **IRC** | ✅ முழு | ✅ | டெர்மினல்-பாணி பபிள் UI |
| 🍏 **BlueBubbles** | ✅ முழு | ✅ | BlueBubbles REST API வழியாக iMessage |
| 🔵 **Google Chat** | ✅ முழு | ✅ | Chat API வெப்ஹூக்குகள் வழியாக |
| 🟣 **MS Teams** | ✅ முழு | ✅ | Teams bot ப்ளகின் வழியாக |
| 🔷 **Mattermost** | ✅ முழு | ✅ | சுய-ஹோஸ்ட் செய்யப்பட்ட அணி சாட் |
| 🟩 **Matrix** | ✅ முழு | ✅ | பரவலாக்கப்பட்டது, E2EE ஆதரவு |
| 🟢 **LINE** | ✅ முழு | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ முழு | ✅ | பரவலாக்கப்பட்ட NIP-04 DM-கள் |
| 🟣 **Twitch** | ✅ முழு | ✅ | IRC இணைப்பு வழியாக சாட் |
| 🔷 **Feishu/Lark** | ✅ முழு | ✅ | WebSocket நிகழ்வு சந்தா |
| 🔵 **Zalo** | ✅ முழு | ✅ | Zalo Bot API |

> **தானியங்கு கண்டறிதல்:** ClawMetry உங்கள் `~/.openclaw/openclaw.json` ஐப் படித்து, நீங்கள் உண்மையில் கட்டமைத்த சேனல்களை மட்டுமே வழங்குகிறது. கைமுறை அமைப்பு தேவையில்லை.

## Docker வரிசைப்படுத்தல்

ClawMetry ஐ ஒரு கன்டெய்னரில் இயக்க வேண்டுமா? பிரச்சனை இல்லை! 🐳

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

> **குறிப்பு:** Docker-இல் இயக்கும்போது, ClawMetry உங்கள் அமைப்பை தானாக கண்டறிய, உங்கள் ஏஜென்டின் தரவு + பதிவு கோப்பகங்களை (எ.கா. `~/.openclaw`, `~/.claude`, `~/.codex`) மவுன்ட் செய்யவும்.

## தேவைகள்

- Python 3.8+
- Flask (pip வழியாக தானாக நிறுவப்படுகிறது)
- அதே இயந்திரத்தில் ஒரு AI ஏஜென்ட் ரன்டைம்: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, அல்லது QM (அல்லது Docker-க்கான மவுன்ட் செய்யப்பட்ட வால்யூம்கள்)
- Linux அல்லது macOS

## NemoClaw / OpenShell ஆதரவு

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) ஐ தானாக கண்டறிகிறது — OpenClaw ஏஜென்ட்களை சாண்ட்பாக்ஸ் செய்யப்பட்ட OpenShell கன்டெய்னர்களுக்குள் இயக்கும் NVIDIA-இன் நிறுவன பாதுகாப்பு ரேப்பர்.

பெரும்பாலான சந்தர்ப்பங்களில் கூடுதல் கட்டமைப்பு தேவையில்லை. அமர்வு கோப்புகள் ஹோஸ்டில் `~/.openclaw/` இல் இருந்தாலும் அல்லது OpenShell கன்டெய்னருக்குள் இருந்தாலும் சிங்க் டீமன் தானாக கண்டறிகிறது.

### இது எப்படி வேலை செய்கிறது

ClawMetry இரண்டு வழிகளில் NemoClaw ஐக் கண்டறிகிறது:

1. **பைனரி கண்டறிதல்** — `nemoclaw` CLI க்காக சரிபார்த்து, சாண்ட்பாக்ஸ் தகவலைப் பெற `nemoclaw status` ஐ இயக்குகிறது
2. **கன்டெய்னர் கண்டறிதல்** — `openshell`, `nemoclaw`, அல்லது `ghcr.io/nvidia/` இமேஜ்களுக்காக இயங்கும் Docker கன்டெய்னர்களை ஸ்கேன் செய்கிறது, பின்னர் வால்யூம் மவுன்ட்கள் அல்லது `docker cp` வழியாக அமர்வுகளைப் படிக்கிறது

NemoClaw கன்டெய்னர்களிலிருந்து ஒத்திசைக்கப்பட்ட அமர்வு கோப்புகள் கிளவுட் டாஷ்போர்டில் `runtime=nemoclaw` மற்றும் `container_id` மெட்டாடேட்டாவுடன் குறியிடப்படுகின்றன, எனவே அவற்றை நிலையான OpenClaw அமர்வுகளிலிருந்து ஒரே பார்வையில் வேறுபடுத்தி அறியலாம்.

### பரிந்துரைக்கப்பட்ட அமைப்பு: HOST-இல் சிங்க் டீமன்

சிறந்த அனுபவத்திற்கு, ClawMetry-இன் சிங்க் டீமனை **ஹோஸ்ட் இயந்திரத்தில்** இயக்கவும் (சாண்ட்பாக்ஸிற்குள் அல்ல). இது NemoClaw நெட்வொர்க் கொள்கை கட்டுப்பாடுகளைத் தவிர்க்கிறது.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

இயங்கும் எந்த OpenShell கன்டெய்னர்களுக்குள்ளும் உள்ள அமர்வுகளை சிங்க் டீமன் தானாக கண்டுபிடிக்கும்.

### விருப்பமானது: வெளிப்படையான சாண்ட்பாக்ஸ் பெயர்

தானியங்கு கண்டறிதல் வேலை செய்யவில்லை என்றால், ClawMetry ஐ சரியான சாண்ட்பாக்ஸை நோக்கி சுட்டிக்காட்டவும்:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### சாண்ட்பாக்ஸிற்குள் இயக்குதல் (மேம்பட்டது)

சிங்க் டீமனை OpenShell சாண்ட்பாக்ஸிற்குள் **தான்** இயக்க வேண்டுமெனில், அது ClawMetry ingest API ஐ அடைய உங்கள் NemoClaw நெட்வொர்க் கொள்கையில் இந்த வெளிச்செல்லும் விதியைச் சேர்க்கவும்:

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

### போர்ட்கள் மற்றும் endpoint-கள்

| Endpoint | போர்ட் | ப்ரோட்டோகால் | தேவையா |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ஆம் (சிங்க் டீமன் → கிளவுட்) |
| `localhost:8900` | 8900 | HTTP | ஆம் (லோக்கல் டாஷ்போர்டு UI) |
| Docker சாக்கெட் (`/var/run/docker.sock`) | — | Unix சாக்கெட் | கன்டெய்னர் அமர்வு கண்டறிதலுக்கு |

சிங்க் டீமன் `ingest.clawmetry.com` க்கு மட்டுமே வெளிச்செல்லும் HTTPS அழைப்புகளை செய்கிறது. உள்வரும் போர்ட்கள் எதுவும் தேவையில்லை.

---

## கிளவுட் வரிசைப்படுத்தல்

SSH டன்னல்கள், reverse proxy, மற்றும் Docker-க்கு **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** ஐப் பார்க்கவும்.

## சோதனை

இந்த திட்டம் BrowserStack உடன் சோதிக்கப்படுகிறது.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## தொலைமெட்ரி

ClawMetry அனானிமஸ் நிறுவல்-வாழ்க்கைச்சுழற்சி பிங்குகளை
`https://app.clawmetry.com/api/install` க்கு அனுப்புகிறது: புதிய இயந்திரத்தில் முதல்முறையாக
`clawmetry` CLI ஐ இயக்கும்போது ஒரு `install` பிங், புதிய பதிப்புக்கு
மேம்படுத்திய பிறகு முதல் இயக்கத்தில் ஒரு `update` பிங், மற்றும் டாஷ்போர்டு-உள்-தொடக்க
விருப்பத்தை நிறைவு செய்யும்போது ஒரு `onboarded` பிங். உண்மையான நிறுவல்களை
எண்ணுவதற்கும் (மூல PyPI பதிவிறக்க எண்கள் ~98% மிரர்கள், CI, மற்றும் ஆட்டோ-அப்டேட்
மறு-பதிவிறக்கங்கள்) உண்மையில் பயன்பாட்டில் உள்ள ஏஜென்ட் ஃப்ரேம்வொர்க்குகள் மற்றும் பதிப்புகளை
அறியவும் இதைப் பயன்படுத்துகிறோம்.

**ஒவ்வொரு பதிப்பிற்கும் ஒவ்வொரு வாழ்க்கைச்சுழற்சி நிகழ்விற்கும் அதிகபட்சம் ஒரு POST**, இதில் அடங்கியிருப்பது:

| புலம் | எடுத்துக்காட்டு | ஏன் |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` இல் சேமிக்கப்பட்ட ரேண்டம் UUID | நகல் நீக்கம்; நீங்கள் வெளிப்படையாக Cloud sync ஐ இணைக்கும் வரை அனானிமஸ் (அங்கீகரிக்கப்பட்ட டீமன் ஹார்ட்பீட் பின்னர் இதைச் சுமந்து, இந்த நிறுவலை உங்கள் கணக்குடன் இணைக்கிறது) |
| `event` | `install` / `update` / `onboarded` | புதிய நிறுவலா அல்லது ஏற்கனவே உள்ள ஒன்றின் மேம்படுத்தலா |
| `version` | `0.12.167` | என்னென்ன பதிப்புகள் பயன்பாட்டில் உள்ளன |
| `os` / `os_version` | `Darwin` / `25.3.0` | பிளாட்ஃபார்ம் ஆதரவு முன்னுரிமைகள் |
| `python` | `3.11.15` | Python பதிப்பு ஆதரவு மேட்ரிக்ஸ் |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | அடுத்து நாங்கள் எந்த ஏஜென்ட்களுடன் ஒருங்கிணைக்க வேண்டும் |
| `is_ci` / `ci_provider` | `true` / `github_actions` | மனித நிறுவல்களை CI சத்தத்திலிருந்து பிரிக்கிறது |

**நாங்கள் அனுப்பாதவை**: IP (கிளவுட் கோரிக்கையிலிருந்து சேவையக-பக்கமாக நாட்டுக் குறியீட்டைப் பெறுகிறது,
பின்னர் IP ஐத் தூக்கி எறிகிறது), ஹோஸ்ட்பெயர், பயனர்பெயர், பணியிடப் பாதை, கோப்பு உள்ளடக்கங்கள்,
உங்கள் api_key, உங்கள் மின்னஞ்சல், PII அல்லது பணியிடம்-சார்ந்த எதுவும். வயர் பேலோட்
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) இல் தணிக்கை செய்யக்கூடியது.

**விலகல்** (இவற்றில் ஏதேனும் ஒன்று இதை நிரந்தரமாக முடக்கும்):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

இங்கு நெட்வொர்க் தோல்வி ஒருபோதும் `clawmetry` இயங்குவதைத் தடுக்காது — பிங்
டீமன் த்ரெட்டில் ஃபயர்-அண்ட்-ஃபர்கெட், 3 வி டைம்அவுட்டுடன்.

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> ஆல் உருவாக்கப்பட்டது · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> சுற்றுச்சூழல் அமைப்பின் ஒரு பகுதி</sub>
</p>
