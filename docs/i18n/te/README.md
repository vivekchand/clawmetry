<!-- i18n-src:9a05336fbdc1 -->
> తెలుగు translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**మీ ఏజెంట్ ఆలోచించడం చూడండి.** **14 AI ఏజెంట్ రన్‌టైమ్‌ల** కోసం రియల్-టైమ్ అబ్జర్వబిలిటీ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & మరో 10. మీ మొత్తం ఏజెంట్ ఫ్లీట్ కోసం ఒకే డాష్‌బోర్డ్.

> 🌐 **దీన్ని ఈ భాషల్లో చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒకే ఒక కమాండ్. జీరో కాన్ఫిగరేషన్. ప్రతిదాన్ని ఆటో-డిటెక్ట్ చేస్తుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది, అంతే.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ఏజెంట్ రన్‌టైమ్‌లతో పనిచేస్తుంది

ClawMetry OpenClaw కోసం అబ్జర్వబిలిటీగా ప్రారంభమైంది, ఇప్పుడు మీ **మొత్తం ఏజెంట్ ఫ్లీట్‌ను** ఒకే డాష్‌బోర్డ్‌లో మీటర్ చేస్తుంది, మీ మెషీన్‌లో ప్రతి రన్‌టైమ్‌ను ఆటో-డిటెక్ట్ చేస్తూ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw మరియు NemoClaw ఓపెన్-సోర్స్ యాప్‌లో ఉచితం; మిగతా రన్‌టైమ్‌లు ClawMetry Cloud లేదా సెల్ఫ్-హోస్టెడ్ Pro లైసెన్స్‌తో యాక్టివేట్ అవుతాయి. హెడర్ నుండి రన్‌టైమ్‌లను మార్చండి, ప్రతి ట్యాబ్ — కాస్ట్, టోకెన్‌లు, టూల్స్, ట్రేసెస్ — ఆ రన్‌టైమ్‌కు రీ-స్కోప్ అవుతుంది. ఖచ్చితమైన ఉచిత/చెల్లింపు విభజన, టైర్ మ్యాట్రిక్స్, `/api/entitlement` షేప్, మరియు `clawmetry license` CLI కోసం **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** చూడండి.

## మీకు లభించేవి

- **Flow** — ఛానెల్స్, బ్రెయిన్, టూల్స్ ద్వారా ప్రవహించే మెసేజ్‌లను చూపే లైవ్ యానిమేటెడ్ డయాగ్రామ్
- **Overview** — హెల్త్ చెక్‌లు, యాక్టివిటీ హీట్‌మ్యాప్, సెషన్ కౌంట్‌లు, మోడల్ సమాచారం
- **Usage** — రోజువారీ/వారపు/నెలవారీ బ్రేక్‌డౌన్‌లతో టోకెన్ మరియు కాస్ట్ ట్రాకింగ్
- **Sessions** — మోడల్, టోకెన్‌లు, చివరి యాక్టివిటీతో యాక్టివ్ ఏజెంట్ సెషన్‌లు
- **Crons** — స్టేటస్, నెక్స్ట్ రన్, డ్యూరేషన్‌తో షెడ్యూల్డ్ జాబ్‌లు
- **Logs** — కలర్-కోడెడ్ రియల్-టైమ్ లాగ్ స్ట్రీమింగ్
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, రోజువారీ నోట్స్‌ను బ్రౌజ్ చేయండి
- **Transcripts** — సెషన్ హిస్టరీలను చదవడానికి చాట్-బబుల్ UI
- **Alerts** — బడ్జెట్ క్యాప్‌లు, ఎర్రర్-రేట్ ట్రిగ్గర్‌లు, ఏజెంట్-ఆఫ్‌లైన్ డిటెక్షన్; Slack, Discord, PagerDuty, Telegram, Emailకు రూట్ చేస్తుంది
- **Approvals** — డిస్ట్రక్టివ్ డిలీట్‌లు, ఫోర్స్ పుష్‌లు, DB మ్యుటేషన్‌లు, sudo, ప్యాకేజీ ఇన్‌స్టాల్‌లు, నెట్‌వర్క్ కాల్స్‌ను వన్-క్లిక్ సైన్-ఆఫ్ వెనుక గేట్ చేయండి

## స్క్రీన్‌షాట్‌లు

### 🧠 Brain — లైవ్ ఏజెంట్ ఈవెంట్ స్ట్రీమ్
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — టోకెన్ వినియోగం & సెషన్ సారాంశం
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — రియల్-టైమ్ టూల్ కాల్ ఫీడ్
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — మోడల్ & సెషన్ వారీగా కాస్ట్ బ్రేక్‌డౌన్
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — వర్క్‌స్పేస్ ఫైల్ బ్రౌజర్
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — పోశ్చర్ & ఆడిట్ లాగ్
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — బడ్జెట్ క్యాప్‌లు, ఎర్రర్-రేట్ ట్రిగ్గర్‌లు, Slack / Discord / PagerDuty / Emailకు వెబ్‌హుక్‌లు
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — రిస్కీ టూల్ కాల్‌లను మాన్యువల్ సైన్-ఆఫ్ వెనుక గేట్ చేయండి; పాలసీ-బ్యాక్డ్ ప్రొటెక్షన్ రూల్స్
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code కోసం ప్రీ-ఎగ్జిక్యూషన్ బ్లాకింగ్** — ఒకే కమాండ్ ఒక
PreToolUse హుక్‌ను ఇన్‌స్టాల్ చేస్తుంది, ఇది సరిపోలే టూల్ కాల్‌లను అవి రన్ అయ్యే *ముందే* పాజ్ చేసి మీ నిర్ణయం కోసం
వేచి ఉంటుంది (
[క్లౌడ్ పుష్ నోటిఫికేషన్‌లు](https://app.clawmetry.com/push) ఎనేబుల్ చేస్తే మీ ఫోన్ నుండి ఒక్క ట్యాప్‌తో):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ఒక డినై (deny) కేవలం ఆ ఒక్క టూల్ కాల్‌ను మాత్రమే బ్లాక్ చేస్తుంది — ఏజెంట్ తన సెషన్‌ను కొనసాగిస్తుంది మరియు
మరో విధానాన్ని ప్రయత్నించవచ్చు. మీ ఫోన్‌లో అప్రూవ్ చేయడం Claude Code యొక్క సొంత
పర్మిషన్ ప్రాంప్ట్‌ను స్కిప్ చేస్తుంది (మీరు ఇప్పటికే సమాధానం ఇచ్చారు). సరిపోలని టూల్స్ ~40ms ఖర్చవుతాయి మరియు
Claude Code యొక్క సాధారణ పర్మిషన్ ఫ్లోకి ఫాల్ త్రూ అవుతాయి. Claude Code స్వయంగా మీ కోసం వేచి ఉన్నప్పుడు కూడా మీకు ఫోన్
పుష్ వస్తుంది (`permission_prompt` / `idle_prompt` నోటిఫికేషన్‌లు).

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

v2 React యాప్ `frontend/`లో ఉంటుంది మరియు v2 ఎనేబుల్ చేసి Flask
సర్వర్‌ను స్టార్ట్ చేసినప్పుడు `/v2` వద్ద సర్వ్ చేయబడుతుంది.

డెవలప్ చేస్తున్నప్పుడు రెండు టెర్మినల్‌లను ఉపయోగించండి:

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

`http://localhost:5173/v2/` తెరవండి. Vite `/api` రిక్వెస్ట్‌లను
`http://localhost:8900`కు ప్రాక్సీ చేస్తుంది, కాబట్టి React యాప్ అదనపు CORS సెటప్ లేకుండా
లోకల్ Flask సర్వర్‌తో మాట్లాడగలదు.

Python ప్యాకేజీతో పంపే బండిల్‌ను బిల్డ్ చేయడానికి:

```bash
cd frontend
npm run build
```

ప్రొడక్షన్ బండిల్ `clawmetry/static/v2/dist/`కు రాయబడుతుంది.

## రన్‌టైమ్ / ఏజెంట్ కంపాటిబిలిటీ

ClawMetry కేవలం OpenClaw మాత్రమే కాకుండా అనేక AI-ఏజెంట్ రన్‌టైమ్‌లను గమనిస్తుంది. ఒక్కో OpenClaw-యేతర రన్‌టైమ్ దాని స్వంత సెషన్ ఫార్మాట్‌ను ClawMetry యొక్క యూనిఫైడ్ షేప్‌లుగా అనువదించే ఒక అంకితమైన రీడర్ అడాప్టర్‌ను షిప్ చేస్తుంది; డెమన్ వాటిని రన్‌టైమ్‌తో ట్యాగ్ చేసి అదే DuckDB స్టోర్ + క్లౌడ్ స్నాప్‌షాట్‌లోకి ఇంజెస్ట్ చేస్తుంది, మరియు ఒకటి కంటే ఎక్కువ రన్‌టైమ్‌లు ఉన్నప్పుడు Session replay ట్యాబ్ ఒక **రన్‌టైమ్ స్విచర్**ను చూపుతుంది. పూర్తి మ్యాట్రిక్స్ + రన్‌టైమ్‌లను జోడించే గైడ్ కోసం [`docs/compatibility.md`](docs/compatibility.md) చూడండి, మరియు OpenClaw-ఫ్యామిలీ ప్రైమర్ కోసం [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) చూడండి.

| రన్‌టైమ్ / ఏజెంట్ | స్థితి | గమనికలు |
|---|---|---|
| **OpenClaw** | నేటివ్ | రిఫరెన్స్ రన్‌టైమ్, ఆటో-డిటెక్ట్ చేయబడింది |
| **PicoClaw** | బీటా అడాప్టర్ | ఫ్లాట్ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు. |
| **NanoClaw** | బీటా అడాప్టర్ | పర్-సెషన్ SQLite (`data/v2-sessions`). ట్రాన్స్‌క్రిప్ట్‌లు + మెసేజ్ కౌంట్‌లు. |
| **Hermes** | బీటా అడాప్టర్ | SQLite `~/.hermes/state.db`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టోకెన్‌లు/కాస్ట్. |
| **Claude Code** | బీటా అడాప్టర్ | JSONL `~/.claude/projects/.../<id>.jsonl`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు + థింకింగ్, టోకెన్ వినియోగం. |
| **Codex** | బీటా అడాప్టర్ | రోల్‌అవుట్ JSONL `~/.codex/sessions/...`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్ వినియోగం. |
| **Cursor** | బీటా అడాప్టర్ | SQLite `state.vscdb`. చాట్/కంపోజర్ ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్. |
| **Aider** | బీటా అడాప్టర్ | ప్రతి ప్రాజెక్ట్‌కు `.aider.chat.history.md`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టోకెన్ కౌంట్‌లు. |
| **Goose** | బీటా అడాప్టర్ | SQLite `~/.local/share/goose`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్ మొత్తాలు. |
| **opencode** | బీటా అడాప్టర్ | SQLite `~/.local/share/opencode`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్‌లు + కాస్ట్. |
| **Qwen Code** | బీటా అడాప్టర్ | JSONL `~/.qwen/projects/.../chats`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్ వినియోగం. |
| **Pi** | బీటా అడాప్టర్ | JSONL `~/.pi/agent/sessions`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్‌లు + కాస్ట్. |
| **Deep Agents** | బీటా అడాప్టర్ | SQLite `~/.deepagents/.state/sessions.db`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్‌లు + కాస్ట్. |
| **n8n** | బీటా అడాప్టర్ | SQLite `~/.n8n/database.sqlite`. వర్క్‌ఫ్లో ఎగ్జిక్యూషన్‌లు, నోడ్ రన్‌లు, AI Agent ప్రాంప్ట్‌లు, n8n రికార్డ్ చేసే చోట మోడల్ + టోకెన్‌లు. |

"బీటా అడాప్టర్" అంటే ClawMetry ఆ రన్‌టైమ్ యొక్క నిజమైన ఆన్-డిస్క్ ఫార్మాట్ కోసం ఒక రీడర్‌ను షిప్ చేస్తుంది, ప్రతి ఒక్కటి నిజమైన మెషీన్‌పై నిజమైన ఇన్‌స్టాల్‌కు వ్యతిరేకంగా బిల్డ్ చేయబడి + వెరిఫై చేయబడింది (`tests/fixtures/runtimes/<rt>/` చూడండి). అడాప్టర్‌లు రీడ్-ఓన్లీ; ప్రతి ఒక్కటి దాని రన్‌టైమ్ నిజంగా ఏమి స్టోర్ చేస్తుందో దాని గురించి నిజాయితీగా ఉంటుంది (ఉదా. PicoClaw/NanoClaw/Cursor టోకెన్ కాస్ట్‌ను డిస్క్‌కు రాయవు). ఒకే నోడ్‌పై అనేక రన్‌టైమ్‌లు రన్ అవుతున్నప్పుడు, రన్‌టైమ్ స్విచర్ శుభ్రమైన డీప్-డైవ్ కోసం సెషన్‌ల వ్యూను ఒకదానికి స్కోప్ చేస్తుంది.

## ఏదైనా SDK ఏజెంట్‌ను ట్రాక్ చేయండి — అవుట్-లూప్ కాస్ట్ అట్రిబ్యూషన్

పైన ఉన్న రన్‌టైమ్‌లు అన్నీ సెషన్‌లను డిస్క్‌కు రాస్తాయి. మీరు OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, లేదా ప్లెయిన్ `httpx` లూప్‌పై నిర్మించిన మీ సొంత **ప్రొడక్షన్ ఏజెంట్** అలా చేయదు. `httpx`/`requests`ను మంకీ-పాచ్ చేయడం ద్వారా ClawMetry యొక్క జీరో-కాన్ఫిగ్ ఇంటర్‌సెప్టర్ ఇప్పటికీ దాని LLM కాల్‌లను (కాస్ట్, టోకెన్‌లు, లేటెన్సీ, ఎర్రర్‌లు) క్యాప్చర్ చేస్తుంది:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (లేదా `CLAWMETRY_SOURCE=support-agent` env var) ప్రతి కాల్‌ను ఒక **నేమ్డ్ సోర్స్**తో ట్యాగ్ చేస్తుంది, కాబట్టి మీరు రన్ చేసే ప్రతి ప్రొడక్ట్ డాష్‌బోర్డ్ యొక్క Overviewలోని **🔌 Out-loop sources** కార్డ్‌లో దాని స్వంత ఫస్ట్-క్లాస్, కాస్ట్-అట్రిబ్యూటబుల్ లైన్‌గా కనిపిస్తుంది — ఒక్కో ఏజెంట్‌కు కాల్‌లు, ప్రొవైడర్‌లు, లేటెన్సీ, ఎర్రర్ రేట్. సోర్స్ సెట్ చేయలేదా? కాల్‌లు ఇప్పటికీ ట్రాక్ అవుతాయి; కార్డ్ మాత్రమే దాగి ఉంటుంది.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ఇది రన్‌టైమ్ అడాప్టర్‌లు ఫీడ్ చేసే అదే డేటా లేయర్ (DuckDB → క్లౌడ్ స్నాప్‌షాట్), కాబట్టి అవుట్-లూప్ సోర్స్‌లు మిగతా ప్రతిదాని లాగే క్లౌడ్ డాష్‌బోర్డ్‌కు సింక్ అవుతాయి, E2E-ఎన్‌క్రిప్టెడ్‌గా.

## OpenTelemetry — వెండార్-న్యూట్రల్, మీ ట్రేసెస్‌ను ఎక్కడికైనా పంపండి

ClawMetry **GenAI సెమాంటిక్ కన్వెన్షన్‌లు** ఉపయోగించి రెండు దిశలలో **OpenTelemetry** మాట్లాడుతుంది, కాబట్టి మీ ఏజెంట్ ట్రేసెస్ ఎప్పుడూ ఒకే టూల్‌కు లాక్ చేయబడవు.

ప్రతి సెషన్‌ను — LLM కాల్‌లు, టూల్స్, సబ్-ఏజెంట్‌లు, టోకెన్‌లు, కాస్ట్ — ఏ కలెక్టర్‌కైనా (Datadog, Grafana, Honeycomb, లేదా మీ సొంత OTel Collector) OTLP/HTTP GenAI స్పాన్‌లుగా **ఎక్స్‌పోర్ట్** చేయండి:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth హెడర్‌లు మరియు పోల్ ఇంటర్వల్ ఐచ్ఛిక env వేరియబుల్స్:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ఇంజెస్ట్** — బిల్ట్-ఇన్ OTLP రిసీవర్ `/v1/traces` మరియు `/v1/metrics` వద్ద మరేదైనా దాని నుండి ట్రేసెస్ మరియు మెట్రిక్‌లను అంగీకరిస్తుంది (ప్రోటోబఫ్ ఇంజెస్ట్ కోసం `pip install clawmetry[otel]`).

మీకు జీరో-కాన్ఫిగ్, లోకల్-ఫస్ట్ ClawMetry డాష్‌బోర్డ్ **మరియు** మీ టీమ్ ఇప్పటికే రన్ చేస్తున్న ఏ బ్యాకెండ్‌లోనైనా మీ డేటా లభిస్తుంది — లాక్-ఇన్ లేదు, ఇన్‌స్టాల్ చేయవలసిన రెండో ఏజెంట్ లేదు.

## కాన్ఫిగరేషన్

చాలామందికి ఎలాంటి కాన్ఫిగ్ అవసరం లేదు. ClawMetry మీ వర్క్‌స్పేస్, లాగ్‌లు, సెషన్‌లు, మరియు క్రాన్‌లను ఆటో-డిటెక్ట్ చేస్తుంది.

మీరు కస్టమైజ్ చేయవలసి వస్తే:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

అన్ని ఆప్షన్‌లు: `clawmetry --help`

## మద్దతు ఉన్న ఛానెల్స్

మీరు కాన్ఫిగర్ చేసిన ప్రతి OpenClaw ఛానెల్ కోసం ClawMetry లైవ్ యాక్టివిటీని చూపుతుంది. మీ `openclaw.json`లో వాస్తవంగా సెటప్ చేయబడిన ఛానెల్స్ మాత్రమే Flow డయాగ్రామ్‌లో కనిపిస్తాయి — కాన్ఫిగర్ చేయని వాటిని ఆటోమేటిక్‌గా దాచివేస్తారు.

Flowలో ఏదైనా ఛానెల్ నోడ్‌ను క్లిక్ చేసి ఇన్‌కమింగ్/అవుట్‌గోయింగ్ మెసేజ్ కౌంట్‌లతో లైవ్ చాట్ బబుల్ వ్యూను చూడండి.

| ఛానెల్ | స్థితి | లైవ్ పాపప్ | గమనికలు |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ పూర్తి | ✅ | మెసేజ్‌లు, స్టాట్స్, 10s రిఫ్రెష్ |
| 💬 **iMessage** | ✅ పూర్తి | ✅ | `~/Library/Messages/chat.db`ను నేరుగా చదువుతుంది |
| 💚 **WhatsApp** | ✅ పూర్తి | ✅ | WhatsApp Web (Baileys) ద్వారా |
| 🔵 **Signal** | ✅ పూర్తి | ✅ | signal-cli ద్వారా |
| 🟣 **Discord** | ✅ పూర్తి | ✅ | గిల్డ్ + ఛానెల్ డిటెక్షన్ |
| 🟪 **Slack** | ✅ పూర్తి | ✅ | వర్క్‌స్పేస్ + ఛానెల్ డిటెక్షన్ |
| 🌐 **Webchat** | ✅ పూర్తి | ✅ | బిల్ట్-ఇన్ వెబ్ UI సెషన్‌లు |
| 📡 **IRC** | ✅ పూర్తి | ✅ | టెర్మినల్-స్టైల్ బబుల్ UI |
| 🍏 **BlueBubbles** | ✅ పూర్తి | ✅ | BlueBubbles REST API ద్వారా iMessage |
| 🔵 **Google Chat** | ✅ పూర్తి | ✅ | Chat API వెబ్‌హుక్‌ల ద్వారా |
| 🟣 **MS Teams** | ✅ పూర్తి | ✅ | Teams బాట్ ప్లగిన్ ద్వారా |
| 🔷 **Mattermost** | ✅ పూర్తి | ✅ | సెల్ఫ్-హోస్టెడ్ టీమ్ చాట్ |
| 🟩 **Matrix** | ✅ పూర్తి | ✅ | డీసెంట్రలైజ్డ్, E2EE మద్దతు |
| 🟢 **LINE** | ✅ పూర్తి | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ పూర్తి | ✅ | డీసెంట్రలైజ్డ్ NIP-04 DMs |
| 🟣 **Twitch** | ✅ పూర్తి | ✅ | IRC కనెక్షన్ ద్వారా చాట్ |
| 🔷 **Feishu/Lark** | ✅ పూర్తి | ✅ | WebSocket ఈవెంట్ సబ్‌స్క్రిప్షన్ |
| 🔵 **Zalo** | ✅ పూర్తి | ✅ | Zalo Bot API |

> **ఆటో-డిటెక్షన్:** ClawMetry మీ `~/.openclaw/openclaw.json`ను చదివి మీరు వాస్తవంగా కాన్ఫిగర్ చేసిన ఛానెల్స్‌ను మాత్రమే రెండర్ చేస్తుంది. మాన్యువల్ సెటప్ అవసరం లేదు.

## Docker డిప్లాయ్‌మెంట్

ClawMetryని ఒక కంటైనర్‌లో రన్ చేయాలనుకుంటున్నారా? ఎలాంటి సమస్య లేదు! 🐳

**Docker తో త్వరిత ప్రారంభం:**

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

> **గమనిక:** Dockerలో రన్ చేస్తున్నప్పుడు, మీ ఏజెంట్ యొక్క డేటా + లాగ్ డైరెక్టరీలను (ఉదా. `~/.openclaw`, `~/.claude`, `~/.codex`) మౌంట్ చేయండి, తద్వారా ClawMetry మీ సెటప్‌ను ఆటో-డిటెక్ట్ చేయగలదు.

## అవసరాలు

- Python 3.8+
- Flask (pip ద్వారా ఆటోమేటిక్‌గా ఇన్‌స్టాల్ చేయబడుతుంది)
- అదే మెషీన్‌పై ఒక AI ఏజెంట్ రన్‌టైమ్: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, లేదా n8n (లేదా Docker కోసం మౌంటెడ్ వాల్యూమ్‌లు)
- Linux లేదా macOS

## NemoClaw / OpenShell మద్దతు

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw)ను ఆటోమేటిక్‌గా గుర్తిస్తుంది — ఇది NVIDIA యొక్క ఎంటర్‌ప్రైజ్ సెక్యూరిటీ ర్యాపర్, ఇది శాండ్‌బాక్స్డ్ OpenShell కంటైనర్‌ల లోపల ఏజెంట్‌లను రన్ చేయడానికి OpenClaw కోసం ఉద్దేశించబడింది.

చాలా సందర్భాలలో అదనపు కాన్ఫిగరేషన్ అవసరం లేదు. సింక్ డెమన్ సెషన్ ఫైల్‌లు హోస్ట్‌పై `~/.openclaw/`లో ఉన్నా లేదా OpenShell కంటైనర్ లోపల ఉన్నా వాటిని ఆటో-డిస్కవర్ చేస్తుంది.

### ఇది ఎలా పనిచేస్తుంది

ClawMetry NemoClawను రెండు విధాలుగా గుర్తిస్తుంది:

1. **బైనరీ డిటెక్షన్** — `nemoclaw` CLI కోసం చెక్ చేస్తుంది మరియు శాండ్‌బాక్స్ సమాచారం పొందడానికి `nemoclaw status`ను రన్ చేస్తుంది
2. **కంటైనర్ డిటెక్షన్** — `openshell`, `nemoclaw`, లేదా `ghcr.io/nvidia/` ఇమేజ్‌ల కోసం రన్నింగ్ Docker కంటైనర్‌లను స్కాన్ చేసి, ఆ తర్వాత వాల్యూమ్ మౌంట్‌లు లేదా `docker cp` ద్వారా సెషన్‌లను చదువుతుంది

NemoClaw కంటైనర్‌ల నుండి సింక్ చేసిన సెషన్ ఫైల్‌లు క్లౌడ్ డాష్‌బోర్డ్‌లో `runtime=nemoclaw` మరియు `container_id` మెటాడేటాతో ట్యాగ్ చేయబడతాయి, తద్వారా మీరు వాటిని ఒక్క చూపులో స్టాండర్డ్ OpenClaw సెషన్‌ల నుండి వేరు చేయగలరు.

### సిఫార్సు చేయబడిన సెటప్: HOSTపై సింక్ డెమన్

ఉత్తమ అనుభవం కోసం, ClawMetry యొక్క సింక్ డెమన్‌ను **హోస్ట్ మెషీన్**పై (శాండ్‌బాక్స్ లోపల కాదు) రన్ చేయండి. ఇది NemoClaw నెట్‌వర్క్ పాలసీ పరిమితులను నివారిస్తుంది.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

సింక్ డెమన్ ఏదైనా రన్నింగ్ OpenShell కంటైనర్‌ల లోపల సెషన్‌లను ఆటోమేటిక్‌గా కనుగొంటుంది.

### ఐచ్ఛికం: స్పష్టమైన శాండ్‌బాక్స్ పేరు

ఆటో-డిటెక్షన్ పనిచేయకపోతే, ClawMetryను సరైన శాండ్‌బాక్స్‌కు పాయింట్ చేయండి:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### శాండ్‌బాక్స్ లోపల రన్ చేయడం (అడ్వాన్స్‌డ్)

మీరు సింక్ డెమన్‌ను OpenShell శాండ్‌బాక్స్ **లోపల** తప్పనిసరిగా రన్ చేయవలసి వస్తే, అది ClawMetry ఇంజెస్ట్ APIని చేరుకోగలిగేలా మీ NemoClaw నెట్‌వర్క్ పాలసీకి ఈ ఎగ్రెస్ రూల్‌ను జోడించండి:

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

సింక్ డెమన్ కేవలం `ingest.clawmetry.com`కు మాత్రమే అవుట్‌బౌండ్ HTTPS కాల్‌లు చేస్తుంది. ఎలాంటి ఇన్‌బౌండ్ పోర్ట్‌లు అవసరం లేదు.

---

## క్లౌడ్ డిప్లాయ్‌మెంట్

SSH టన్నెల్‌లు, రివర్స్ ప్రాక్సీ, మరియు Docker కోసం **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** చూడండి.

## టెస్టింగ్

ఈ ప్రాజెక్ట్ BrowserStackతో టెస్ట్ చేయబడింది.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## టెలిమెట్రీ

మీరు కొత్త మెషీన్‌లో `clawmetry` CLIని మొదటిసారి రన్ చేసినప్పుడు ClawMetry
`https://app.clawmetry.com/api/install`కు ఒకే ఒక అనామక "ఫస్ట్ రన్" పింగ్‌ను
పంపుతుంది. ఇన్‌స్టాల్‌లను లెక్కించడానికి (OSS ప్రాజెక్ట్ కోసం మా వద్ద ఉన్న
ఏకైక మార్కెటింగ్ మెట్రిక్) మరియు మా యూజర్లు ఏ ఏజెంట్ ఫ్రేమ్‌వర్క్‌లను ఇన్‌స్టాల్ చేశారో
తెలుసుకోవడానికి మేము దీన్ని ఉపయోగిస్తాము.

**ప్రతి ఇన్‌స్టాల్‌కు సరిగ్గా ఒక POST**, ఇందులో ఉండేవి:

| ఫీల్డ్ | ఉదాహరణ | ఎందుకు |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` వద్ద నిల్వ చేయబడిన రాండమ్ UUID | డిడప్; మీ ఇమెయిల్ లేదా api_keyతో లింక్ చేయబడలేదు |
| `version` | `0.12.167` | వైల్డ్‌లో ఏ వెర్షన్‌లు ఉన్నాయో |
| `os` / `os_version` | `Darwin` / `25.3.0` | ప్లాట్‌ఫారమ్ మద్దతు ప్రాధాన్యతలు |
| `python` | `3.11.15` | Python వెర్షన్ మద్దతు మ్యాట్రిక్స్ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | తర్వాత మేము ఏ ఏజెంట్‌లతో ఇంటిగ్రేట్ చేయాలి |
| `is_ci` / `ci_provider` | `true` / `github_actions` | మానవ ఇన్‌స్టాల్‌లను CI నాయిస్ నుండి వేరు చేయడానికి |

**మేము పంపనివి**: IP (క్లౌడ్ రిక్వెస్ట్ నుండి సర్వర్-సైడ్‌లో దేశం కోడ్‌ను
తీసుకుని, తర్వాత IPను తొలగిస్తుంది), హోస్ట్‌నేమ్, యూజర్‌నేమ్, వర్క్‌స్పేస్
పాత్, ఫైల్ కంటెంట్‌లు, మీ api_key, మీ ఇమెయిల్, PII లేదా
వర్క్‌స్పేస్-నిర్దిష్టమైనది ఏదీ కాదు. వైర్ పేలోడ్
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)లో ఆడిటబుల్‌గా ఉంది.

**ఆప్ట్ అవుట్** (వీటిలో ఏదైనా ఒకటి దీన్ని శాశ్వతంగా డిసేబుల్ చేస్తుంది):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

నెట్‌వర్క్ వైఫల్యం ఇక్కడ ఎప్పుడూ `clawmetry` రన్ కావడాన్ని బ్లాక్ చేయదు — పింగ్
3 సెకన్ల టైమౌట్‌తో ఒక డెమన్ థ్రెడ్‌పై ఫైర్-అండ్-ఫర్గెట్‌గా ఉంటుంది.

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
  <strong>🦞 మీ ఏజెంట్ ఆలోచించడం చూడండి</strong><br>
  <sub>నిర్మించినది <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> పర్యావరణ వ్యవస్థలో భాగం</sub>
</p>
