<!-- i18n-src:191e9094d7fa -->
> తెలుగు translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**మీ ఏజెంట్ ఆలోచనను చూడండి.** **14 AI ఏజెంట్ రన్‌టైమ్‌ల** కోసం రియల్-టైమ్ అబ్జర్వబిలిటీ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & మరో 10. మీ మొత్తం ఏజెంట్ ఫ్లీట్ కోసం ఒకే డాష్‌బోర్డ్.

> 🌐 **దీన్ని ఈ భాషల్లో చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒక్క కమాండ్. జీరో కాన్ఫిగ్. అన్నింటినీ ఆటో-డిటెక్ట్ చేస్తుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది, అంతే.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ఏజెంట్ రన్‌టైమ్‌లతో పనిచేస్తుంది

ClawMetry OpenClaw కోసం అబ్జర్వబిలిటీగా ప్రారంభమైంది, ఇప్పుడు ఇది మీ **మొత్తం ఏజెంట్ ఫ్లీట్**‌ను ఒకే డాష్‌బోర్డ్‌లో మీటర్ చేస్తుంది, మీ మెషీన్‌లో ప్రతి రన్‌టైమ్‌ను ఆటో-డిటెక్ట్ చేస్తుంది:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw మరియు NemoClaw ఓపెన్-సోర్స్ యాప్‌లో ఉచితం; మిగిలిన రన్‌టైమ్‌లు ClawMetry Cloud లేదా సెల్ఫ్-హోస్టెడ్ Pro లైసెన్స్‌తో యాక్టివేట్ అవుతాయి. హెడర్ నుండి రన్‌టైమ్‌లను మార్చండి మరియు ప్రతి ట్యాబ్ — cost, tokens, tools, traces — ఆ రన్‌టైమ్‌కు రీ-స్కోప్ అవుతుంది. ఖచ్చితమైన ఉచిత/చెల్లింపు విభజన, టైర్ మ్యాట్రిక్స్, `/api/entitlement` షేప్, మరియు `clawmetry license` CLI కోసం **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** చూడండి.

## మీకు లభించేవి

- **Flow** — ఛానెల్స్, బ్రెయిన్, టూల్స్ ద్వారా మరియు తిరిగి ప్రవహించే మెసేజ్‌లను చూపే లైవ్ యానిమేటెడ్ డయాగ్రామ్
- **Overview** — హెల్త్ చెక్‌లు, యాక్టివిటీ హీట్‌మ్యాప్, సెషన్ కౌంట్‌లు, మోడల్ సమాచారం
- **Usage** — రోజువారీ/వారానికి/నెలవారీ బ్రేక్‌డౌన్‌లతో టోకెన్ మరియు కాస్ట్ ట్రాకింగ్
- **Sessions** — మోడల్, టోకెన్‌లు, చివరి యాక్టివిటీతో యాక్టివ్ ఏజెంట్ సెషన్‌లు
- **Crons** — స్టేటస్, తదుపరి రన్, వ్యవధితో షెడ్యూల్ చేసిన జాబ్‌లు
- **Logs** — కలర్-కోడెడ్ రియల్-టైమ్ లాగ్ స్ట్రీమింగ్
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, రోజువారీ నోట్స్ బ్రౌజ్ చేయండి
- **Transcripts** — సెషన్ హిస్టరీలను చదవడానికి చాట్-బబుల్ UI
- **Alerts** — బడ్జెట్ క్యాప్‌లు, ఎర్రర్-రేట్ ట్రిగ్గర్‌లు, ఏజెంట్-ఆఫ్‌లైన్ డిటెక్షన్; Slack, Discord, PagerDuty, Telegram, Email కు రూట్ చేస్తుంది
- **Approvals** — వినాశకరమైన డిలీట్‌లు, ఫోర్స్ పుష్‌లు, DB మ్యుటేషన్‌లు, sudo, ప్యాకేజీ ఇన్‌స్టాల్‌లు, నెట్‌వర్క్ కాల్‌లను ఒక్క-క్లిక్ సైన్-ఆఫ్ వెనుక గేట్ చేయండి

## స్క్రీన్‌షాట్‌లు

### 🧠 Brain — లైవ్ ఏజెంట్ ఈవెంట్ స్ట్రీమ్
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — టోకెన్ వాడకం & సెషన్ సారాంశం
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — రియల్-టైమ్ టూల్ కాల్ ఫీడ్
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — మోడల్ & సెషన్ వారీగా కాస్ట్ బ్రేక్‌డౌన్
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — వర్క్‌స్పేస్ ఫైల్ బ్రౌజర్
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — పోశ్చర్ & ఆడిట్ లాగ్
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — బడ్జెట్ క్యాప్‌లు, ఎర్రర్-రేట్ ట్రిగ్గర్‌లు, Slack / Discord / PagerDuty / Email కు వెబ్‌హుక్‌లు
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — రిస్కీ టూల్ కాల్‌లను మ్యానువల్ సైన్-ఆఫ్ వెనుక గేట్ చేయండి; పాలసీ-బ్యాక్డ్ ప్రొటెక్షన్ రూల్స్
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code కోసం ప్రీ-ఎగ్జిక్యూషన్ బ్లాకింగ్** — ఒక కమాండ్ మ్యాచింగ్ టూల్ కాల్‌లను అవి రన్ అయ్యేముందే *pause* చేసి, మీ నిర్ణయం కోసం వేచి ఉండే PreToolUse హుక్‌ను ఇన్‌స్టాల్ చేస్తుంది (మీ ఫోన్ నుండి ఒక్క ట్యాప్‌తో, [cloud push notifications](https://app.clawmetry.com/push) ఎనేబుల్ చేసినప్పుడు):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ఒక deny కేవలం ఆ ఒక్క టూల్ కాల్‌ను మాత్రమే బ్లాక్ చేస్తుంది — ఏజెంట్ తన సెషన్‌ను కొనసాగించి వేరే విధానాన్ని ప్రయత్నించవచ్చు. మీ ఫోన్‌లో ఆమోదించడం Claude Code యొక్క సొంత పర్మిషన్ ప్రాంప్ట్‌ను స్కిప్ చేస్తుంది (మీరు ఇప్పటికే జవాబిచ్చారు కాబట్టి). మ్యాచ్ కాని టూల్స్ ~40ms ఖర్చు చేసి Claude Code యొక్క సాధారణ పర్మిషన్ ఫ్లోకు ఫాల్ త్రూ అవుతాయి. Claude Code స్వయంగా మీ కోసం వేచి ఉన్నప్పుడు కూడా మీకు ఫోన్ పుష్ లభిస్తుంది (`permission_prompt` / `idle_prompt` నోటిఫికేషన్‌లు).

## ఇన్‌స్టాల్

**వన్-లైనర్ (సిఫార్సు చేయబడింది):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**సోర్స్ నుండి:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 ఫ్రంటెండ్ డెవలప్‌మెంట్

v2 React యాప్ `frontend/` లో ఉంది మరియు Flask సర్వర్ v2 ఎనేబుల్‌తో ప్రారంభించినప్పుడు `/v2` వద్ద సర్వ్ చేయబడుతుంది.

డెవలప్‌మెంట్ చేస్తున్నప్పుడు రెండు టెర్మినల్స్ ఉపయోగించండి:

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

`http://localhost:5173/v2/` తెరవండి. Vite `/api` రిక్వెస్ట్‌లను `http://localhost:8900` కు ప్రాక్సీ చేస్తుంది, కాబట్టి React యాప్ ఎక్స్‌ట్రా CORS సెటప్ లేకుండా లోకల్ Flask సర్వర్‌తో మాట్లాడగలదు.

Python ప్యాకేజీతో పంపే బండిల్‌ను బిల్డ్ చేయడానికి:

```bash
cd frontend
npm run build
```

ప్రొడక్షన్ బండిల్ `clawmetry/static/v2/dist/` కు వ్రాయబడుతుంది.

## రన్‌టైమ్ / ఏజెంట్ కంపాటిబిలిటీ

ClawMetry OpenClaw మాత్రమే కాకుండా అనేక AI-ఏజెంట్ రన్‌టైమ్‌లను అబ్జర్వ్ చేస్తుంది. OpenClaw కాని ప్రతి రన్‌టైమ్ దాని నేటివ్ సెషన్ ఫార్మాట్‌ను ClawMetry యొక్క యూనిఫైడ్ షేప్‌లలోకి అనువదించే ప్రత్యేక రీడర్ అడాప్టర్‌ను షిప్ చేస్తుంది; డెమన్ వాటిని రన్‌టైమ్‌తో ట్యాగ్ చేసి అదే DuckDB స్టోర్ + క్లౌడ్ స్నాప్‌షాట్‌లోకి ఇంజెస్ట్ చేస్తుంది, మరియు ఒకటి కంటే ఎక్కువ రన్‌టైమ్‌లు ఉన్నప్పుడు Session replay ట్యాబ్ ఒక **రన్‌టైమ్ స్విచర్**‌ను చూపిస్తుంది. పూర్తి మ్యాట్రిక్స్ + రన్‌టైమ్‌లను జోడించే గైడ్ కోసం [`docs/compatibility.md`](docs/compatibility.md) చూడండి, మరియు OpenClaw-family ప్రైమర్ కోసం [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) చూడండి.

[Perplexity యొక్క numbat](https://github.com/perplexityai/numbat) ఏజెంట్-సెక్యూరిటీ టూల్‌ను రన్ చేస్తున్నారా? ClawMetry దాని ఫైండింగ్‌లు మరియు ఎన్‌ఫోర్స్‌మెంట్ నిర్ణయాలను ఔట్ ఆఫ్ ది బాక్స్‌గా ఇంజెస్ట్ చేస్తుంది — [`docs/NUMBAT.md`](docs/NUMBAT.md) చూడండి.

| రన్‌టైమ్ / ఏజెంట్ | స్టేటస్ | నోట్స్ |
|---|---|---|
| **OpenClaw** | Native | రిఫరెన్స్ రన్‌టైమ్, ఆటో-డిటెక్టెడ్ |
| **PicoClaw** | Beta adapter | ఫ్లాట్ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్. |
| **NanoClaw** | Beta adapter | సెషన్‌కు SQLite (`data/v2-sessions`). ట్రాన్స్‌క్రిప్ట్‌లు + మెసేజ్ కౌంట్‌లు. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టోకెన్‌లు/కాస్ట్. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్ + థింకింగ్, టోకెన్ వాడకం. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్ వాడకం. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. చాట్/కంపోజర్ ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్. |
| **Aider** | Beta adapter | ప్రాజెక్ట్‌కు `.aider.chat.history.md`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టోకెన్ కౌంట్‌లు. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్ మొత్తాలు. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్‌లు + కాస్ట్. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్ వాడకం. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్‌లు + కాస్ట్. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్‌లు + కాస్ట్. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. వర్క్‌ఫ్లో ఎగ్జిక్యూషన్‌లు, నోడ్ రన్‌లు, AI Agent ప్రాంప్ట్‌లు, n8n రికార్డ్ చేసిన చోట మోడల్ + టోకెన్‌లు. |
| **Antigravity** | Beta adapter | `~/.gemini/<flavor>/brain/` కింద Brain JSONL. సంభాషణలు, టూల్ స్టెప్‌లు, థింకింగ్, జనరేషన్‌కు Gemini టోకెన్ స్ప్లిట్ + కాస్ట్, బ్యాక్‌గ్రౌండ్-జనరేషన్ బర్న్. |

"Beta adapter" అంటే ClawMetry ఆ రన్‌టైమ్ యొక్క వాస్తవ ఆన్-డిస్క్ ఫార్మాట్ కోసం ఒక రీడర్‌ను షిప్ చేస్తుంది, ప్రతి ఒక్కటి నిజమైన మెషీన్‌లో నిజమైన ఇన్‌స్టాల్‌కు వ్యతిరేకంగా బిల్డ్ + వెరిఫై చేయబడింది (`tests/fixtures/runtimes/<rt>/` చూడండి). అడాప్టర్‌లు రీడ్-ఓన్లీ; ప్రతి ఒక్కటి దాని రన్‌టైమ్ నిజంగా దేన్ని స్టోర్ చేస్తుందనే దాని గురించి నిజాయితీగా ఉంటుంది (ఉదా., PicoClaw/NanoClaw/Cursor డిస్క్‌కు టోకెన్ కాస్ట్ వ్రాయవు). ఒక నోడ్‌పై అనేక రన్‌టైమ్‌లు రన్ అవుతున్నప్పుడు, రన్‌టైమ్ స్విచర్ క్లీన్ డీప్-డైవ్ కోసం సెషన్‌ల వ్యూను ఒకదానికి స్కోప్ చేస్తుంది.

## ఏదైనా SDK ఏజెంట్‌ను ట్రాక్ చేయండి — అవుట్-లూప్ కాస్ట్ అట్రిబ్యూషన్

పైన ఉన్న రన్‌టైమ్‌లన్నీ సెషన్‌లను డిస్క్‌కు వ్రాస్తాయి. మీ సొంత **ప్రొడక్షన్ ఏజెంట్** — మీరు OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, లేదా ప్లెయిన్ `httpx` లూప్‌పై బిల్డ్ చేసినది — అలా చేయదు. ClawMetry యొక్క జీరో-కాన్ఫిగ్ ఇంటర్‌సెప్టర్ ఇప్పటికీ దాని LLM కాల్‌లను (కాస్ట్, టోకెన్‌లు, లేటెన్సీ, ఎర్రర్‌లు) `httpx`/`requests`ను మంకీ-పాచింగ్ చేయడం ద్వారా క్యాప్చర్ చేస్తుంది:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (లేదా `CLAWMETRY_SOURCE=support-agent` ఎన్విరాన్మెంట్ వేరియబుల్) ప్రతి కాల్‌ను **నేమ్డ్ సోర్స్**‌తో ట్యాగ్ చేస్తుంది, కాబట్టి మీరు రన్ చేసే ప్రతి ప్రొడక్ట్ డాష్‌బోర్డ్ యొక్క Overview లోని **🔌 Out-loop sources** కార్డ్‌లో దాని సొంత ఫస్ట్-క్లాస్, కాస్ట్-అట్రిబ్యూటబుల్ లైన్‌గా కనిపిస్తుంది — ఏజెంట్‌కు కాల్‌లు, ప్రొవైడర్‌లు, లేటెన్సీ, ఎర్రర్ రేట్. సోర్స్ సెట్ చేయలేదా? కాల్‌లు ఇప్పటికీ ట్రాక్ అవుతాయి; కార్డ్ మాత్రమే హిడెన్‌గా ఉంటుంది.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ఇది రన్‌టైమ్ అడాప్టర్‌లు ఫీడ్ చేసే అదే డేటా లేయర్ (DuckDB → cloud snapshot), కాబట్టి అవుట్-లూప్ సోర్స్‌లు మిగతా అన్నింటిలాగే క్లౌడ్ డాష్‌బోర్డ్‌కు సింక్ అవుతాయి, E2E-encrypted.

## OpenTelemetry — వెండర్-న్యూట్రల్, మీ ట్రేస్‌లను ఎక్కడికైనా పంపండి

ClawMetry రెండు దిశలలో **OpenTelemetry** మాట్లాడుతుంది, **GenAI సెమాంటిక్ కన్వెన్షన్‌లను** ఉపయోగించి, కాబట్టి మీ ఏజెంట్ ట్రేస్‌లు ఎప్పుడూ ఒకే టూల్‌కు లాక్ చేయబడవు.

**ఎక్స్‌పోర్ట్** — ప్రతి సెషన్‌ను — LLM కాల్‌లు, టూల్స్, సబ్-ఏజెంట్‌లు, టోకెన్‌లు, కాస్ట్ — ఏ కలెక్టర్‌కైనా (Datadog, Grafana, Honeycomb, లేదా మీ సొంత OTel Collector) OTLP/HTTP GenAI స్పాన్‌లుగా:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth హెడర్‌లు మరియు పోల్ ఇంటర్వల్ ఆప్షనల్ ఎన్విరాన్మెంట్ వేరియబుల్స్:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ఇంజెస్ట్** — బిల్ట్-ఇన్ OTLP రిసీవర్ `/v1/traces` మరియు `/v1/metrics` వద్ద మరేదైనా దాని నుండి ట్రేస్‌లు మరియు మెట్రిక్‌లను అంగీకరిస్తుంది (protobuf ingest కోసం `pip install clawmetry[otel]`).

మీకు జీరో-కాన్ఫిగ్, లోకల్-ఫస్ట్ ClawMetry డాష్‌బోర్డ్ **మరియు** మీ టీమ్ ఇప్పటికే రన్ చేస్తున్న ఏ బ్యాకెండ్‌లోనైనా మీ డేటా లభిస్తుంది — లాక్-ఇన్ లేదు, రెండో ఏజెంట్‌ను ఇన్‌స్టాల్ చేయాల్సిన అవసరం లేదు.

## కాన్ఫిగరేషన్

చాలామందికి ఏ కాన్ఫిగ్ అవసరం లేదు. ClawMetry మీ వర్క్‌స్పేస్, లాగ్‌లు, సెషన్‌లు, మరియు క్రాన్‌లను ఆటో-డిటెక్ట్ చేస్తుంది.

మీకు కస్టమైజ్ చేయాల్సిన అవసరం ఉంటే:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

అన్ని ఆప్షన్‌లు: `clawmetry --help`

## సపోర్టెడ్ ఛానెల్స్

మీరు కాన్ఫిగర్ చేసిన ప్రతి OpenClaw ఛానెల్ కోసం ClawMetry లైవ్ యాక్టివిటీని చూపిస్తుంది. మీ `openclaw.json` లో వాస్తవంగా సెటప్ చేసిన ఛానెల్స్ మాత్రమే Flow డయాగ్రామ్‌లో కనిపిస్తాయి — కాన్ఫిగర్ చేయని వాటిని ఆటోమేటిక్‌గా దాచేస్తుంది.

Flowలో ఏదైనా ఛానెల్ నోడ్‌పై క్లిక్ చేస్తే ఇన్‌కమింగ్/అవుట్‌గోయింగ్ మెసేజ్ కౌంట్‌లతో లైవ్ చాట్ బబుల్ వ్యూ కనిపిస్తుంది.

| ఛానెల్ | స్టేటస్ | లైవ్ పాపప్ | నోట్స్ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ పూర్తి | ✅ | మెసేజ్‌లు, స్టాట్స్, 10s రిఫ్రెష్ |
| 💬 **iMessage** | ✅ పూర్తి | ✅ | `~/Library/Messages/chat.db` నేరుగా చదువుతుంది |
| 💚 **WhatsApp** | ✅ పూర్తి | ✅ | WhatsApp Web (Baileys) ద్వారా |
| 🔵 **Signal** | ✅ పూర్తి | ✅ | signal-cli ద్వారా |
| 🟣 **Discord** | ✅ పూర్తి | ✅ | Guild + ఛానెల్ డిటెక్షన్ |
| 🟪 **Slack** | ✅ పూర్తి | ✅ | Workspace + ఛానెల్ డిటెక్షన్ |
| 🌐 **Webchat** | ✅ పూర్తి | ✅ | బిల్ట్-ఇన్ వెబ్ UI సెషన్‌లు |
| 📡 **IRC** | ✅ పూర్తి | ✅ | టెర్మినల్-స్టైల్ బబుల్ UI |
| 🍏 **BlueBubbles** | ✅ పూర్తి | ✅ | BlueBubbles REST API ద్వారా iMessage |
| 🔵 **Google Chat** | ✅ పూర్తి | ✅ | Chat API వెబ్‌హుక్‌ల ద్వారా |
| 🟣 **MS Teams** | ✅ పూర్తి | ✅ | Teams బాట్ ప్లగిన్ ద్వారా |
| 🔷 **Mattermost** | ✅ పూర్తి | ✅ | సెల్ఫ్-హోస్టెడ్ టీమ్ చాట్ |
| 🟩 **Matrix** | ✅ పూర్తి | ✅ | డీసెంట్రలైజ్డ్, E2EE సపోర్ట్ |
| 🟢 **LINE** | ✅ పూర్తి | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ పూర్తి | ✅ | డీసెంట్రలైజ్డ్ NIP-04 DMs |
| 🟣 **Twitch** | ✅ పూర్తి | ✅ | IRC కనెక్షన్ ద్వారా చాట్ |
| 🔷 **Feishu/Lark** | ✅ పూర్తి | ✅ | WebSocket ఈవెంట్ సబ్‌స్క్రిప్షన్ |
| 🔵 **Zalo** | ✅ పూర్తి | ✅ | Zalo Bot API |

> **ఆటో-డిటెక్షన్:** ClawMetry మీ `~/.openclaw/openclaw.json` ను చదివి, మీరు వాస్తవంగా కాన్ఫిగర్ చేసిన ఛానెల్స్‌ను మాత్రమే రెండర్ చేస్తుంది. మ్యానువల్ సెటప్ అవసరం లేదు.

## Docker డిప్లాయ్‌మెంట్

కంటైనర్‌లో ClawMetry రన్ చేయాలనుకుంటున్నారా? ఎటువంటి సమస్య లేదు! 🐳

**Docker తో క్విక్ స్టార్ట్:**

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

**Docker Compose ఉదాహరణ:**

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

> **గమనిక:** Dockerలో రన్ చేస్తున్నప్పుడు, మీ ఏజెంట్ యొక్క డేటా + లాగ్ డైరెక్టరీలను మౌంట్ చేయండి (ఉదా., `~/.openclaw`, `~/.claude`, `~/.codex`) తద్వారా ClawMetry మీ సెటప్‌ను ఆటో-డిటెక్ట్ చేయగలదు.

## అవసరాలు

- Python 3.8+
- Flask (pip ద్వారా ఆటోమేటిక్‌గా ఇన్‌స్టాల్ అవుతుంది)
- అదే మెషీన్‌లో ఒక AI ఏజెంట్ రన్‌టైమ్: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, లేదా Antigravity (లేదా Docker కోసం మౌంటెడ్ వాల్యూమ్‌లు)
- Linux లేదా macOS

## NemoClaw / OpenShell సపోర్ట్

ClawMetry ఆటోమేటిక్‌గా [NemoClaw](https://github.com/NVIDIA/NemoClaw) ను డిటెక్ట్ చేస్తుంది — ఇది NVIDIA యొక్క ఎంటర్‌ప్రైజ్ సెక్యూరిటీ ర్యాపర్, ఇది సాండ్‌బాక్స్డ్ OpenShell కంటైనర్‌ల లోపల ఏజెంట్‌లను రన్ చేసే OpenClaw కోసం.

చాలా సందర్భాలలో అదనపు కాన్ఫిగరేషన్ అవసరం లేదు. సింక్ డెమన్ సెషన్ ఫైల్‌లు హోస్ట్‌లో `~/.openclaw/` లో ఉన్నా లేదా OpenShell కంటైనర్ లోపల ఉన్నా వాటిని ఆటో-డిస్కవర్ చేస్తుంది.

### ఇది ఎలా పనిచేస్తుంది

ClawMetry రెండు విధాలుగా NemoClaw ను డిటెక్ట్ చేస్తుంది:

1. **బైనరీ డిటెక్షన్** — `nemoclaw` CLI కోసం చెక్ చేసి, సాండ్‌బాక్స్ సమాచారం పొందడానికి `nemoclaw status` రన్ చేస్తుంది
2. **కంటైనర్ డిటెక్షన్** — `openshell`, `nemoclaw`, లేదా `ghcr.io/nvidia/` ఇమేజ్‌ల కోసం రన్నింగ్ Docker కంటైనర్‌లను స్కాన్ చేసి, తర్వాత వాల్యూమ్ మౌంట్‌ల ద్వారా లేదా `docker cp` ద్వారా సెషన్‌లను చదువుతుంది

NemoClaw కంటైనర్‌ల నుండి సింక్ చేసిన సెషన్ ఫైల్‌లు క్లౌడ్ డాష్‌బోర్డ్‌లో `runtime=nemoclaw` మరియు `container_id` మెటాడేటాతో ట్యాగ్ చేయబడతాయి, కాబట్టి మీరు వాటిని ఒక్క చూపులో స్టాండర్డ్ OpenClaw సెషన్‌ల నుండి వేరు చేయవచ్చు.

### సిఫార్సు చేయబడిన సెటప్: HOST పై సింక్ డెమన్

ఉత్తమ అనుభవం కోసం, ClawMetry యొక్క సింక్ డెమన్‌ను **హోస్ట్ మెషీన్**‌పై రన్ చేయండి (సాండ్‌బాక్స్ లోపల కాదు). ఇది NemoClaw నెట్‌వర్క్ పాలసీ నియంత్రణలను నివారిస్తుంది.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

సింక్ డెమన్ ఆటోమేటిక్‌గా రన్నింగ్ OpenShell కంటైనర్‌ల లోపల సెషన్‌లను కనుగొంటుంది.

### ఆప్షనల్: స్పష్టమైన సాండ్‌బాక్స్ పేరు

ఆటో-డిటెక్షన్ పనిచేయకపోతే, ClawMetryను సరైన సాండ్‌బాక్స్‌కు పాయింట్ చేయండి:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### సాండ్‌బాక్స్ లోపల రన్ చేయడం (అడ్వాన్స్‌డ్)

మీరు తప్పనిసరిగా సింక్ డెమన్‌ను OpenShell సాండ్‌బాక్స్ **లోపల** రన్ చేయాలంటే, ClawMetry ఇంజెస్ట్ API ను చేరుకోవడానికి మీ NemoClaw నెట్‌వర్క్ పాలసీకి ఈ ఎగ్రెస్ రూల్‌ను జోడించండి:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

దీనితో అప్లై చేయండి:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### పోర్ట్‌లు మరియు ఎండ్‌పాయింట్‌లు

| ఎండ్‌పాయింట్ | పోర్ట్ | ప్రోటోకాల్ | అవసరమా |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | అవును (సింక్ డెమన్ → క్లౌడ్) |
| `localhost:8900` | 8900 | HTTP | అవును (లోకల్ డాష్‌బోర్డ్ UI) |
| Docker సాకెట్ (`/var/run/docker.sock`) | — | Unix సాకెట్ | కంటైనర్ సెషన్ డిస్కవరీ కోసం |

సింక్ డెమన్ కేవలం `ingest.clawmetry.com` కు అవుట్‌బౌండ్ HTTPS కాల్‌లను మాత్రమే చేస్తుంది. ఏ ఇన్‌బౌండ్ పోర్ట్‌లు అవసరం లేదు.

---

## క్లౌడ్ డిప్లాయ్‌మెంట్

SSH టన్నెల్‌లు, రివర్స్ ప్రాక్సీ, మరియు Docker కోసం **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** చూడండి.

## టెస్టింగ్

ఈ ప్రాజెక్ట్ BrowserStack తో టెస్ట్ చేయబడింది.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## టెలిమెట్రీ

ClawMetry అనామక ఇన్‌స్టాల్-లైఫ్‌సైకిల్ పింగ్‌లను
`https://app.clawmetry.com/api/install` కు పంపిస్తుంది: మీరు కొత్త మెషీన్‌లో `clawmetry` CLI ను మొదటిసారి రన్ చేసినప్పుడు ఒక `install` పింగ్, కొత్త వెర్షన్‌కు అప్‌గ్రేడ్ చేసిన తర్వాత మొదటి రన్‌లో ఒక `update` పింగ్, మరియు మీరు డాష్‌బోర్డ్-లోపల ఆన్‌బోర్డింగ్ ఎంపికను పూర్తి చేసినప్పుడు ఒక `onboarded` పింగ్. మేము దీన్ని నిజమైన ఇన్‌స్టాల్‌లను లెక్కించడానికి (రా PyPI డౌన్‌లోడ్ నంబర్‌లు ~98% మిర్రర్‌లు, CI, మరియు ఆటో-అప్‌డేట్ రీ-డౌన్‌లోడ్‌లు) మరియు ఏ ఏజెంట్ ఫ్రేమ్‌వర్క్‌లు మరియు వెర్షన్‌లు నిజంగా వాడుకలో ఉన్నాయో తెలుసుకోవడానికి ఉపయోగిస్తాము.

**ప్రతి వెర్షన్‌కు ప్రతి లైఫ్‌సైకిల్ ఈవెంట్‌కు గరిష్టంగా ఒక POST**, దీనిలో ఉన్నవి:

| ఫీల్డ్ | ఉదాహరణ | ఎందుకు |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` వద్ద నిల్వ చేసిన రాండమ్ UUID | dedup; మీరు స్పష్టంగా Cloud sync కనెక్ట్ చేసేవరకు అనామకం (అప్పుడు authenticated డెమన్ heartbeat దీన్ని క్యారీ చేస్తుంది, ఈ ఇన్‌స్టాల్‌ను మీ ఖాతాకు లింక్ చేస్తుంది) |
| `event` | `install` / `update` / `onboarded` | కొత్త ఇన్‌స్టాల్ vs ఇప్పటికే ఉన్నదాని అప్‌గ్రేడ్ |
| `version` | `0.12.167` | ఏ వెర్షన్‌లు వాడుకలో ఉన్నాయి |
| `os` / `os_version` | `Darwin` / `25.3.0` | ప్లాట్‌ఫారమ్ సపోర్ట్ ప్రాధాన్యతలు |
| `python` | `3.11.15` | Python వెర్షన్ సపోర్ట్ మ్యాట్రిక్స్ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | మేము తర్వాత ఏ ఏజెంట్‌లతో ఇంటిగ్రేట్ చేయాలి |
| `is_ci` / `ci_provider` | `true` / `github_actions` | మనుష్యుల ఇన్‌స్టాల్‌లను CI నాయిస్ నుండి వేరు చేయడం |

**మేము పంపనివి**: IP (క్లౌడ్ రిక్వెస్ట్ నుండి సర్వర్-సైడ్‌లో దేశ కోడ్‌ను డిరైవ్ చేసి, తర్వాత IPని డిస్కార్డ్ చేస్తుంది), హోస్ట్‌నేమ్, యూజర్‌నేమ్, వర్క్‌స్పేస్ పాత్, ఫైల్ కంటెంట్‌లు, మీ api_key, మీ ఇమెయిల్, PII లేదా వర్క్‌స్పేస్-స్పెసిఫిక్ ఏదైనా. వైర్ పేలోడ్ [`clawmetry/telemetry.py`](clawmetry/telemetry.py) లో ఆడిటబుల్‌గా ఉంది.

**ఆప్ట్ అవుట్** (వీటిలో ఏదైనా ఒకటి దీన్ని శాశ్వతంగా డిజేబుల్ చేస్తుంది):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ఇక్కడ నెట్‌వర్క్ ఫెయిల్యూర్ ఎప్పుడూ `clawmetry` రన్ అవ్వకుండా బ్లాక్ చేయదు — పింగ్ 3 సెకన్ల టైమ్‌అవుట్‌తో డెమన్ థ్రెడ్‌పై ఫైర్-అండ్-ఫర్గెట్‌గా ఉంటుంది.

## స్టార్ హిస్టరీ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## లైసెన్స్

MIT

---

<p align="center">
  <strong>🦞 మీ ఏజెంట్ ఆలోచనను చూడండి</strong><br>
  <sub>నిర్మించినవారు <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ఎకోసిస్టమ్‌లో భాగం</sub>
</p>
