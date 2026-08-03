<!-- i18n-src:0e34918f8f2e -->
> తెలుగు translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**మీ ఏజెంట్ ఆలోచించడాన్ని చూడండి.** **14 AI ఏజెంట్ రన్‌టైమ్‌ల** కోసం రియల్-టైమ్ అబ్జర్వబిలిటీ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & మరో 10. మీ మొత్తం ఏజెంట్ ఫ్లీట్ కోసం ఒకే డాష్‌బోర్డ్.

> 🌐 **దీన్ని ఇలా చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒకే కమాండ్. జీరో కాన్ఫిగ్. ప్రతిదాన్ని ఆటోమేటిక్‌గా గుర్తిస్తుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది, అంతే.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ఏజెంట్ రన్‌టైమ్‌లతో పనిచేస్తుంది

ClawMetry OpenClaw కోసం అబ్జర్వబిలిటీగా మొదలైంది, ఇప్పుడు ఒకే డాష్‌బోర్డ్‌లో మీ **మొత్తం ఏజెంట్ ఫ్లీట్‌ను** మీటర్ చేస్తుంది, మీ మెషిన్‌లో ప్రతి రన్‌టైమ్‌ను ఆటోమేటిక్‌గా గుర్తిస్తూ:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw మరియు NemoClaw ఓపెన్-సోర్స్ యాప్‌లో ఉచితం; మిగతా రన్‌టైమ్‌లు ClawMetry Cloud లేదా సెల్ఫ్-హోస్టెడ్ Pro లైసెన్స్‌తో యాక్టివేట్ అవుతాయి. హెడర్ నుండి రన్‌టైమ్‌లను మార్చండి, ప్రతి ట్యాబ్ — cost, tokens, tools, traces — ఆ రన్‌టైమ్‌కు రీ-స్కోప్ అవుతుంది. ఖచ్చితమైన ఉచిత/చెల్లింపు విభజన, టైర్ మ్యాట్రిక్స్, `/api/entitlement` షేప్, మరియు `clawmetry license` CLI కోసం **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** చూడండి.

## మీకు లభించేది

- **Flow** — ఛానెల్స్, బ్రెయిన్, టూల్స్ ద్వారా ప్రవహించే మెసేజ్‌లను చూపే లైవ్ యానిమేటెడ్ డయాగ్రామ్
- **Overview** — హెల్త్ చెక్‌లు, యాక్టివిటీ హీట్‌మ్యాప్, సెషన్ కౌంట్‌లు, మోడల్ సమాచారం
- **Usage** — డైలీ/వీక్లీ/మంత్లీ బ్రేక్‌డౌన్‌లతో టోకెన్ మరియు కాస్ట్ ట్రాకింగ్
- **Sessions** — మోడల్, టోకెన్లు, చివరి యాక్టివిటీతో యాక్టివ్ ఏజెంట్ సెషన్లు
- **Crons** — స్టేటస్, తర్వాతి రన్, వ్యవధితో షెడ్యూల్డ్ జాబ్‌లు
- **Logs** — కలర్-కోడెడ్ రియల్-టైమ్ లాగ్ స్ట్రీమింగ్
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, డైలీ నోట్స్ బ్రౌజ్ చేయండి
- **Transcripts** — సెషన్ హిస్టరీలను చదవడానికి చాట్-బబుల్ UI
- **Alerts** — బడ్జెట్ క్యాప్‌లు, ఎర్రర్-రేట్ ట్రిగ్గర్‌లు, ఏజెంట్-ఆఫ్‌లైన్ డిటెక్షన్; Slack, Discord, PagerDuty, Telegram, Email కు రూట్ చేస్తుంది
- **Approvals** — డిస్ట్రక్టివ్ డిలీట్‌లు, ఫోర్స్ పుష్‌లు, DB మ్యూటేషన్లు, sudo, ప్యాకేజీ ఇన్‌స్టాల్‌లు, నెట్‌వర్క్ కాల్‌లను ఒక్క-క్లిక్ సైన్-ఆఫ్ వెనుక గేట్ చేస్తుంది

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

### ✋ Approvals — రిస్కీ టూల్ కాల్‌లను మాన్యువల్ సైన్-ఆఫ్ వెనుక గేట్ చేయండి; పాలసీ-బ్యాక్డ్ ప్రొటెక్షన్ రూల్స్
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code కోసం ప్రీ-ఎగ్జిక్యూషన్ బ్లాకింగ్** — ఒక కమాండ్ మ్యాచింగ్ టూల్
కాల్‌లను అవి *రన్ అయ్యే ముందు* పాజ్ చేసి మీ నిర్ణయం కోసం వేచి ఉండే PreToolUse
హుక్‌ను ఇన్‌స్టాల్ చేస్తుంది (
[క్లౌడ్ పుష్ నోటిఫికేషన్‌లు](https://app.clawmetry.com/push) ఎనేబుల్ చేస్తే మీ ఫోన్ నుండి ఒకే ట్యాప్‌తో):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ఒక deny ఆ ఒక్క టూల్ కాల్‌ను మాత్రమే బ్లాక్ చేస్తుంది — ఏజెంట్ తన సెషన్‌ను
కొనసాగిస్తుంది, వేరే విధానాన్ని ప్రయత్నించవచ్చు. మీ ఫోన్‌లో ఆమోదించడం Claude
Code యొక్క సొంత పర్మిషన్ ప్రాంప్ట్‌ను స్కిప్ చేస్తుంది (మీరు ఇప్పటికే
సమాధానం ఇచ్చారు కదా). మ్యాచ్ కాని టూల్స్‌కు ~40ms ఖర్చవుతుంది, అవి Claude
Code యొక్క సాధారణ పర్మిషన్ ఫ్లోలోకి పడిపోతాయి. Claude Code స్వయంగా మీ కోసం
వేచి ఉన్నప్పుడు కూడా మీకు ఫోన్ పుష్ వస్తుంది (`permission_prompt` /
`idle_prompt` నోటిఫికేషన్‌లు).

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

v2 React యాప్ `frontend/`లో ఉంది, v2 ఎనేబుల్ చేసి Flask సర్వర్‌ను స్టార్ట్
చేసినప్పుడు `/v2` వద్ద సర్వ్ చేయబడుతుంది.

డెవలప్ చేస్తున్నప్పుడు రెండు టెర్మినల్స్ వాడండి:

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
`http://localhost:8900`కు ప్రాక్సీ చేస్తుంది, కాబట్టి React యాప్ ఎలాంటి
అదనపు CORS సెటప్ లేకుండానే లోకల్ Flask సర్వర్‌తో మాట్లాడగలదు.

Python ప్యాకేజీతో పంపే బండిల్‌ను బిల్డ్ చేయడానికి:

```bash
cd frontend
npm run build
```

ప్రొడక్షన్ బండిల్ `clawmetry/static/v2/dist/`కు రాయబడుతుంది.

## రన్‌టైమ్ / ఏజెంట్ కంపాటిబిలిటీ

ClawMetry కేవలం OpenClaw మాత్రమే కాకుండా అనేక AI-ఏజెంట్ రన్‌టైమ్‌లను గమనిస్తుంది. OpenClaw కాని ప్రతి రన్‌టైమ్ దాని native సెషన్ ఫార్మాట్‌ను ClawMetry యొక్క యూనిఫైడ్ షేప్‌లుగా అనువదించే ఒక అంకితమైన రీడర్ అడాప్టర్‌ను కలిగి ఉంటుంది; డీమన్ వాటిని రన్‌టైమ్‌తో ట్యాగ్ చేసి అదే DuckDB స్టోర్ + క్లౌడ్ స్నాప్‌షాట్‌లోకి ఇంజెస్ట్ చేస్తుంది, ఒకటి కంటే ఎక్కువ ఉన్నప్పుడు Session replay ట్యాబ్ ఒక **రన్‌టైమ్ స్విచర్**ను చూపిస్తుంది. పూర్తి మ్యాట్రిక్స్ + రన్‌టైమ్‌లను జోడించడానికి గైడ్ కోసం [`docs/compatibility.md`](docs/compatibility.md) చూడండి, మరియు OpenClaw-family ప్రైమర్ కోసం [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) చూడండి.

[Perplexity యొక్క numbat](https://github.com/perplexityai/numbat) ఏజెంట్-సెక్యూరిటీ టూల్ రన్ చేస్తున్నారా? ClawMetry దాని ఫైండింగ్స్ మరియు ఎన్‌ఫోర్స్‌మెంట్ నిర్ణయాలను బాక్స్ నుండే ఇంజెస్ట్ చేస్తుంది — [`docs/NUMBAT.md`](docs/NUMBAT.md) చూడండి.

| రన్‌టైమ్ / ఏజెంట్ | స్టేటస్ | నోట్స్ |
|---|---|---|
| **OpenClaw** | Native | రిఫరెన్స్ రన్‌టైమ్, ఆటో-డిటెక్టెడ్ |
| **PicoClaw** | Beta adapter | ఫ్లాట్ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ట్రాన్స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్. |
| **NanoClaw** | Beta adapter | పర్-సెషన్ SQLite (`data/v2-sessions`). ట్రాన్స్క్రిప్ట్‌లు + మెసేజ్ కౌంట్‌లు. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. ట్రాన్స్క్రిప్ట్‌లు, మోడల్, టోకెన్లు/కాస్ట్. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. ట్రాన్స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్ + థింకింగ్, టోకెన్ వాడకం. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. ట్రాన్స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్ వాడకం. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. చాట్/కంపోజర్ ట్రాన్స్క్రిప్ట్‌లు, మోడల్. |
| **Aider** | Beta adapter | ప్రాజెక్ట్‌కు ఒక `.aider.chat.history.md`. ట్రాన్స్క్రిప్ట్‌లు, మోడల్, టోకెన్ కౌంట్‌లు. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. ట్రాన్స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్ మొత్తాలు. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. ట్రాన్స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్లు + కాస్ట్. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. ట్రాన్స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్ వాడకం. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. ట్రాన్స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్లు + కాస్ట్. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. ట్రాన్స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్స్, టోకెన్లు + కాస్ట్. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. వర్క్‌ఫ్లో ఎగ్జిక్యూషన్లు, నోడ్ రన్‌లు, AI Agent ప్రాంప్ట్‌లు, n8n రికార్డ్ చేసిన చోట మోడల్ + టోకెన్లు. |
| **Antigravity** | Beta adapter | `~/.gemini/<flavor>/brain/` కింద బ్రెయిన్ JSONL. సంభాషణలు, టూల్ స్టెప్‌లు, థింకింగ్, జనరేషన్‌కు Gemini టోకెన్ స్ప్లిట్ + కాస్ట్, బ్యాక్‌గ్రౌండ్-జనరేషన్ బర్న్. |
| **GitHub Copilot** | Beta adapter | `~/.copilot/session-state/` కింద Copilot CLI `events.jsonl` + పర్-కాల్ వాడక లెడ్జర్ అయిన `session-store.db`. సంభాషణలు, టూల్ కాల్స్, మోడల్ రూటింగ్, కాష్-అవేర్ టోకెన్ స్ప్లిట్, వెండర్-బిల్డ్ AI-క్రెడిట్ కాస్ట్. |

"Beta adapter" అంటే ClawMetry ఆ రన్‌టైమ్ యొక్క నిజమైన ఆన్-డిస్క్ ఫార్మాట్ కోసం రీడర్‌ను షిప్ చేస్తుంది, ప్రతి ఒక్కటి నిజమైన మెషిన్‌లో నిజమైన ఇన్‌స్టాల్‌కు వ్యతిరేకంగా బిల్డ్ చేయబడి + వెరిఫై చేయబడింది (చూడండి `tests/fixtures/runtimes/<rt>/`). అడాప్టర్లు రీడ్-ఓన్లీ; ప్రతి ఒక్కటి తన రన్‌టైమ్ నిజంగా ఏమి స్టోర్ చేస్తుందో దాని గురించి నిజాయితీగా ఉంటుంది (ఉదా. PicoClaw/NanoClaw/Cursor టోకెన్ కాస్ట్‌ను డిస్క్‌కు రాయవు). ఒక నోడ్‌పై అనేక రన్‌టైమ్‌లు రన్ అయినప్పుడు, రన్‌టైమ్ స్విచర్ క్లీన్ డీప్-డైవ్ కోసం సెషన్స్ వ్యూను ఒకదానికి స్కోప్ చేస్తుంది.

## ఏదైనా SDK ఏజెంట్‌ను ట్రాక్ చేయండి — అవుట్-లూప్ కాస్ట్ అట్రిబ్యూషన్

పైన ఉన్న రన్‌టైమ్‌లన్నీ సెషన్‌లను డిస్క్‌కు రాస్తాయి. మీరు OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, లేదా ప్లెయిన్ `httpx` లూప్‌పై బిల్డ్ చేసిన మీ సొంత **ప్రొడక్షన్ ఏజెంట్** అలా చేయదు. ClawMetry యొక్క జీరో-కాన్ఫిగ్ ఇంటర్‌సెప్టర్ `httpx`/`requests`ను మంకీ-పాచింగ్ చేయడం ద్వారా ఇప్పటికీ దాని LLM కాల్‌లను (కాస్ట్, టోకెన్లు, లేటెన్సీ, ఎర్రర్‌లు) క్యాప్చర్ చేస్తుంది:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (లేదా `CLAWMETRY_SOURCE=support-agent` env var) ప్రతి కాల్‌ను ఒక **నేమ్డ్ సోర్స్**తో ట్యాగ్ చేస్తుంది, కాబట్టి మీరు నడిపే ప్రతి ప్రొడక్ట్ డాష్‌బోర్డ్ యొక్క ఓవర్‌వ్యూలోని **🔌 Out-loop sources** కార్డ్‌లో దాని సొంత ఫస్ట్-క్లాస్, కాస్ట్-అట్రిబ్యూటబుల్ లైన్‌గా కనిపిస్తుంది — ప్రతి ఏజెంట్‌కు కాల్స్, ప్రొవైడర్లు, లేటెన్సీ, ఎర్రర్ రేట్. సోర్స్ సెట్ చేయలేదా? కాల్‌లు ఇప్పటికీ ట్రాక్ అవుతాయి; కార్డ్ మాత్రం దాగి ఉంటుంది.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ఇది రన్‌టైమ్ అడాప్టర్లు ఫీడ్ చేసే అదే డేటా లేయర్ (DuckDB → క్లౌడ్ స్నాప్‌షాట్), కాబట్టి అవుట్-లూప్ సోర్సెస్ మిగతా అన్నిటిలాగే క్లౌడ్ డాష్‌బోర్డ్‌కు E2E-ఎన్‌క్రిప్టెడ్‌గా సింక్ అవుతాయి.

## OpenTelemetry — వెండర్-న్యూట్రల్, మీ ట్రేసులను ఎక్కడికైనా పంపండి

ClawMetry రెండు దిశలలోనూ **OpenTelemetry** మాట్లాడుతుంది, **GenAI సెమాంటిక్ కన్వెన్షన్‌లను** వాడుతూ, కాబట్టి మీ ఏజెంట్ ట్రేసులు ఎప్పుడూ ఒకే టూల్‌కు లాక్ చేయబడవు.

ప్రతి సెషన్‌ను — LLM కాల్స్, టూల్స్, సబ్-ఏజెంట్లు, టోకెన్లు, కాస్ట్ — ఏ కలెక్టర్‌కైనా (Datadog, Grafana, Honeycomb, లేదా మీ సొంత OTel Collector) OTLP/HTTP GenAI స్పాన్‌లుగా **ఎక్స్‌పోర్ట్** చేయండి:

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

**ఇంజెస్ట్** — బిల్ట్-ఇన్ OTLP రిసీవర్ `/v1/traces` మరియు `/v1/metrics` వద్ద మరేదైనా చోటి నుండి ట్రేసులు మరియు మెట్రిక్‌లను అంగీకరిస్తుంది (protobuf ఇంజెస్ట్ కోసం `pip install clawmetry[otel]`).

మీకు జీరో-కాన్ఫిగ్, లోకల్-ఫస్ట్ ClawMetry డాష్‌బోర్డ్ **మరియు** మీ టీమ్ ఇప్పటికే నడుపుతున్న ఏ బ్యాకెండ్‌లోనైనా మీ డేటా లభిస్తుంది — లాక్-ఇన్ లేదు, ఇన్‌స్టాల్ చేయడానికి రెండో ఏజెంట్ అవసరం లేదు.

## కాన్ఫిగరేషన్

చాలామందికి ఎలాంటి కాన్ఫిగ్ అవసరం లేదు. ClawMetry మీ వర్క్‌స్పేస్, లాగ్‌లు, సెషన్లు, మరియు క్రాన్‌లను ఆటోమేటిక్‌గా గుర్తిస్తుంది.

మీరు కస్టమైజ్ చేయాల్సి వస్తే:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

అన్ని ఆప్షన్లు: `clawmetry --help`

## సపోర్టెడ్ ఛానెల్స్

మీరు కాన్ఫిగర్ చేసిన ప్రతి OpenClaw ఛానెల్ కోసం ClawMetry లైవ్ యాక్టివిటీని చూపిస్తుంది. మీ `openclaw.json`లో నిజంగా సెటప్ చేసిన ఛానెల్స్ మాత్రమే Flow డయాగ్రామ్‌లో కనిపిస్తాయి — కాన్ఫిగర్ చేయని వాటిని ఆటోమేటిక్‌గా దాచేస్తుంది.

ఇన్‌కమింగ్/అవుట్‌గోయింగ్ మెసేజ్ కౌంట్‌లతో లైవ్ చాట్ బబుల్ వ్యూ చూడటానికి Flowలో ఏదైనా ఛానెల్ నోడ్‌పై క్లిక్ చేయండి.

| ఛానెల్ | స్టేటస్ | లైవ్ పాప్అప్ | నోట్స్ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | మెసేజ్‌లు, స్టాట్స్, 10s రిఫ్రెష్ |
| 💬 **iMessage** | ✅ Full | ✅ | `~/Library/Messages/chat.db`ను నేరుగా చదువుతుంది |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) ద్వారా |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli ద్వారా |
| 🟣 **Discord** | ✅ Full | ✅ | గిల్డ్ + ఛానెల్ డిటెక్షన్ |
| 🟪 **Slack** | ✅ Full | ✅ | వర్క్‌స్పేస్ + ఛానెల్ డిటెక్షన్ |
| 🌐 **Webchat** | ✅ Full | ✅ | బిల్ట్-ఇన్ వెబ్ UI సెషన్లు |
| 📡 **IRC** | ✅ Full | ✅ | టెర్మినల్-స్టైల్ బబుల్ UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API ద్వారా iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API వెబ్‌హుక్‌ల ద్వారా |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams బాట్ ప్లగిన్ ద్వారా |
| 🔷 **Mattermost** | ✅ Full | ✅ | సెల్ఫ్-హోస్టెడ్ టీమ్ చాట్ |
| 🟩 **Matrix** | ✅ Full | ✅ | డీసెంట్రలైజ్డ్, E2EE సపోర్ట్ |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | డీసెంట్రలైజ్డ్ NIP-04 DMs |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC కనెక్షన్ ద్వారా చాట్ |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket ఈవెంట్ సబ్‌స్క్రిప్షన్ |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **ఆటో-డిటెక్షన్:** ClawMetry మీ `~/.openclaw/openclaw.json`ను చదివి మీరు నిజంగా కాన్ఫిగర్ చేసిన ఛానెల్స్‌ను మాత్రమే రెండర్ చేస్తుంది. మాన్యువల్ సెటప్ అవసరం లేదు.

## Docker డిప్లాయ్‌మెంట్

Containerలో ClawMetryను రన్ చేయాలనుకుంటున్నారా? ఎలాంటి సమస్య లేదు! 🐳

**Dockerతో త్వరిత ప్రారంభం:**

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

> **గమనిక:** Dockerలో రన్ చేసేటప్పుడు, ClawMetry మీ సెటప్‌ను ఆటో-డిటెక్ట్ చేయగలిగేలా మీ ఏజెంట్ యొక్క డేటా + లాగ్ డైరెక్టరీలను (ఉదా. `~/.openclaw`, `~/.claude`, `~/.codex`) మౌంట్ చేయండి.

## అవసరాలు

- Python 3.8+
- Flask (pip ద్వారా ఆటోమేటిక్‌గా ఇన్‌స్టాల్ అవుతుంది)
- అదే మెషిన్‌పై ఒక AI ఏజెంట్ రన్‌టైమ్: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, లేదా GitHub Copilot (లేదా Docker కోసం మౌంటెడ్ వాల్యూమ్‌లు)
- Linux లేదా macOS

## NemoClaw / OpenShell సపోర్ట్

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw)ను ఆటోమేటిక్‌గా గుర్తిస్తుంది — ఇది సాండ్‌బాక్స్డ్ OpenShell కంటైనర్‌ల లోపల ఏజెంట్లను నడిపే NVIDIA యొక్క ఎంటర్‌ప్రైజ్ సెక్యూరిటీ ర్యాపర్.

చాలా సందర్భాలలో అదనపు కాన్ఫిగరేషన్ అవసరం లేదు. హోస్ట్‌పై `~/.openclaw/`లో ఉన్నా లేదా OpenShell కంటైనర్ లోపల ఉన్నా, సింక్ డీమన్ సెషన్ ఫైళ్లను ఆటో-డిస్కవర్ చేస్తుంది.

### ఇది ఎలా పనిచేస్తుంది

ClawMetry రెండు విధాలుగా NemoClawను గుర్తిస్తుంది:

1. **బైనరీ డిటెక్షన్** — `nemoclaw` CLI కోసం చెక్ చేసి, సాండ్‌బాక్స్ సమాచారం పొందడానికి `nemoclaw status` రన్ చేస్తుంది
2. **కంటైనర్ డిటెక్షన్** — `openshell`, `nemoclaw`, లేదా `ghcr.io/nvidia/` ఇమేజ్‌ల కోసం రన్నింగ్ Docker కంటైనర్‌లను స్కాన్ చేసి, వాల్యూమ్ మౌంట్‌ల ద్వారా లేదా `docker cp` ద్వారా సెషన్లను చదువుతుంది

NemoClaw కంటైనర్‌ల నుండి సింక్ చేసిన సెషన్ ఫైళ్లు క్లౌడ్ డాష్‌బోర్డ్‌లో `runtime=nemoclaw` మరియు `container_id` మెటాడేటాతో ట్యాగ్ చేయబడతాయి, కాబట్టి మీరు వాటిని ఒక్క చూపులో స్టాండర్డ్ OpenClaw సెషన్ల నుండి వేరు చేయగలరు.

### సిఫార్సు చేయబడిన సెటప్: HOST పై సింక్ డీమన్

ఉత్తమ అనుభవం కోసం, ClawMetry యొక్క సింక్ డీమన్‌ను (సాండ్‌బాక్స్ లోపల కాకుండా) **హోస్ట్ మెషిన్‌పై** రన్ చేయండి. ఇది NemoClaw నెట్‌వర్క్ పాలసీ నిర్బంధాలను నివారిస్తుంది.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

సింక్ డీమన్ ఏదైనా రన్నింగ్ OpenShell కంటైనర్‌ల లోపల సెషన్లను ఆటోమేటిక్‌గా కనుగొంటుంది.

### ఐచ్ఛికం: స్పష్టమైన సాండ్‌బాక్స్ పేరు

ఆటో-డిటెక్షన్ పనిచేయకపోతే, ClawMetryను సరైన సాండ్‌బాక్స్‌వైపు పాయింట్ చేయండి:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### సాండ్‌బాక్స్ లోపల రన్ చేయడం (అడ్వాన్స్‌డ్)

మీరు తప్పనిసరిగా సింక్ డీమన్‌ను OpenShell సాండ్‌బాక్స్ **లోపల** రన్ చేయాల్సి వస్తే, అది ClawMetry ఇంజెస్ట్ APIని చేరుకోగలిగేలా మీ NemoClaw నెట్‌వర్క్ పాలసీకి ఈ ఎగ్రెస్ రూల్‌ను జోడించండి:

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
| `ingest.clawmetry.com` | 443 | HTTPS | అవును (సింక్ డీమన్ → క్లౌడ్) |
| `localhost:8900` | 8900 | HTTP | అవును (లోకల్ డాష్‌బోర్డ్ UI) |
| Docker సాకెట్ (`/var/run/docker.sock`) | — | Unix సాకెట్ | కంటైనర్ సెషన్ డిస్కవరీ కోసం |

సింక్ డీమన్ కేవలం `ingest.clawmetry.com`కు మాత్రమే అవుట్‌బౌండ్ HTTPS కాల్‌లు చేస్తుంది. ఎలాంటి ఇన్‌బౌండ్ పోర్ట్‌లు అవసరం లేదు.

---

## క్లౌడ్ డిప్లాయ్‌మెంట్

SSH టన్నెల్‌లు, రివర్స్ ప్రాక్సీ, మరియు Docker కోసం **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** చూడండి.

## టెస్టింగ్

ఈ ప్రాజెక్ట్ BrowserStackతో టెస్ట్ చేయబడింది.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## టెలిమెట్రీ

ClawMetry అనామక ఇన్‌స్టాల్-లైఫ్‌సైకిల్ పింగ్‌లను
`https://app.clawmetry.com/api/install`కు పంపుతుంది: మీరు కొత్త మెషిన్‌లో
`clawmetry` CLIని మొదటిసారి రన్ చేసినప్పుడు ఒక `install` పింగ్, కొత్త
వెర్షన్‌కు అప్‌గ్రేడ్ చేసిన తర్వాత మొదటి రన్ వద్ద ఒక `update` పింగ్, మరియు
మీరు డాష్‌బోర్డ్-లో-ఇన్ ఆన్‌బోర్డింగ్ ఎంపికను పూర్తి చేసినప్పుడు ఒక
`onboarded` పింగ్. నిజమైన ఇన్‌స్టాల్‌లను లెక్కించడానికి (రా PyPI డౌన్‌లోడ్
నంబర్‌లలో ~98% మిర్రర్‌లు, CI, మరియు ఆటో-అప్‌డేట్ రీ-డౌన్‌లోడ్‌లే), మరియు
నిజంగా వాడుకలో ఏ ఏజెంట్ ఫ్రేమ్‌వర్క్‌లు, వెర్షన్లు ఉన్నాయో తెలుసుకోవడానికి
దీన్ని వాడుతున్నాం.

**ప్రతి వెర్షన్‌కు ప్రతి లైఫ్‌సైకిల్ ఈవెంట్‌కు గరిష్టంగా ఒక POST**, ఇందులో:

| ఫీల్డ్ | ఉదాహరణ | ఎందుకు |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` వద్ద నిల్వ చేయబడిన రాండమ్ UUID | డిడప్; మీరు స్పష్టంగా Cloud సింక్‌ను కనెక్ట్ చేసేవరకు అనామకం (అప్పుడు అథెంటికేటెడ్ డీమన్ హార్ట్‌బీట్ దాన్ని మోసుకెళ్తుంది, ఈ ఇన్‌స్టాల్‌ను మీ ఖాతాకు లింక్ చేస్తుంది) |
| `event` | `install` / `update` / `onboarded` | కొత్త ఇన్‌స్టాల్ vs ఇప్పటికే ఉన్న దాని అప్‌గ్రేడ్ |
| `version` | `0.12.167` | వాడుకలో ఏ వెర్షన్లు ఉన్నాయి |
| `os` / `os_version` | `Darwin` / `25.3.0` | ప్లాట్‌ఫారమ్ సపోర్ట్ ప్రాధాన్యతలు |
| `python` | `3.11.15` | Python వెర్షన్ సపోర్ట్ మ్యాట్రిక్స్ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | తర్వాత మేము ఏ ఏజెంట్లతో ఇంటిగ్రేట్ చేయాలి |
| `is_ci` / `ci_provider` | `true` / `github_actions` | మనుషుల ఇన్‌స్టాల్‌లను CI నాయిస్ నుండి వేరు చేయడానికి |

**మేము దేన్ని పంపము**: IP (క్లౌడ్ రిక్వెస్ట్ నుండి సర్వర్-సైడ్‌గా దేశం
కోడ్‌ను డిరైవ్ చేసి, తర్వాత IPని విస్మరిస్తుంది), హోస్ట్‌నేమ్, యూజర్‌నేమ్,
వర్క్‌స్పేస్ పాత్, ఫైల్ కంటెంట్‌లు, మీ api_key, మీ ఇమెయిల్, PII లేదా
వర్క్‌స్పేస్-స్పెసిఫిక్ ఏదైనా. వైర్ పేలోడ్ ఆడిటబుల్‌గా
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)లో ఉంది.

**ఆప్ట్ అవుట్** (వీటిలో ఏదైనా ఒకటి దీన్ని శాశ్వతంగా డిజేబుల్ చేస్తుంది):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ఇక్కడ నెట్‌వర్క్ ఫెయిల్యూర్ ఎప్పుడూ `clawmetry`ను రన్ చేయకుండా బ్లాక్ చేయదు
— పింగ్ 3 సెకన్ల టైమ్‌అవుట్‌తో డీమన్ థ్రెడ్‌పై ఫైర్-అండ్-ఫర్గెట్‌గా ఉంటుంది.

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
  <strong>🦞 మీ ఏజెంట్ ఆలోచించడాన్ని చూడండి</strong><br>
  <sub>నిర్మించినవారు <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ఎకోసిస్టమ్‌లో భాగం</sub>
</p>
