<!-- i18n-src:bab48eec552f -->
> తెలుగు translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**మీ ఏజెంట్ ఆలోచించడాన్ని చూడండి.** **14 AI ఏజెంట్ రన్‌టైమ్‌ల** కోసం రియల్-టైమ్ అబ్జర్వబిలిటీ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & మరో 10. మీ మొత్తం ఏజెంట్ ఫ్లీట్ కోసం ఒకే డాష్‌బోర్డ్.

> 🌐 **దీన్ని ఈ భాషల్లో చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒక్క కమాండ్. జీరో కాన్ఫిగ్. ప్రతిదీ ఆటో-డిటెక్ట్ అవుతుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది, పని అయిపోయింది.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ఏజెంట్ రన్‌టైమ్‌లతో పనిచేస్తుంది

ClawMetry OpenClaw కోసం అబ్జర్వబిలిటీగా మొదలైంది, ఇప్పుడు మీ మెషీన్‌లో ఉన్న ప్రతి రన్‌టైమ్‌ను ఆటో-డిటెక్ట్ చేస్తూ, ఒకే డాష్‌బోర్డ్‌లో మీ **మొత్తం ఏజెంట్ ఫ్లీట్**‌ను మీటర్ చేస్తుంది:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw మరియు NemoClaw ఓపెన్-సోర్స్ యాప్‌లో ఉచితం; మిగతా రన్‌టైమ్‌లు ClawMetry Cloud లేదా సెల్ఫ్-హోస్టెడ్ Pro లైసెన్స్‌తో యాక్టివేట్ అవుతాయి. హెడర్ నుండి రన్‌టైమ్‌లను మార్చండి, ప్రతి ట్యాబ్ — కాస్ట్, టోకెన్లు, టూల్స్, ట్రేసెస్ — ఆ రన్‌టైమ్‌కు రీ-స్కోప్ అవుతుంది. ఖచ్చితమైన ఉచిత/చెల్లింపు విభజన, టైర్ మ్యాట్రిక్స్, `/api/entitlement` షేప్, మరియు `clawmetry license` CLI కోసం **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** చూడండి.

## మీకు లభించేది

- **Flow** — చానెల్స్, బ్రెయిన్, టూల్స్ ద్వారా ప్రవహించే మెసేజ్‌లను చూపే లైవ్ యానిమేటెడ్ డయాగ్రామ్
- **Overview** — హెల్త్ చెక్‌లు, యాక్టివిటీ హీట్‌మ్యాప్, సెషన్ కౌంట్‌లు, మోడల్ ఇన్ఫో
- **Usage** — రోజువారీ/వారపు/నెలవారీ బ్రేక్‌డౌన్‌లతో టోకెన్ మరియు కాస్ట్ ట్రాకింగ్
- **Sessions** — మోడల్, టోకెన్లు, చివరి యాక్టివిటీతో యాక్టివ్ ఏజెంట్ సెషన్‌లు
- **Crons** — స్టేటస్, తదుపరి రన్, డ్యురేషన్‌తో షెడ్యూల్డ్ జాబ్‌లు
- **Logs** — కలర్-కోడెడ్ రియల్-టైమ్ లాగ్ స్ట్రీమింగ్
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, డైలీ నోట్స్ బ్రౌజ్ చేయండి
- **Transcripts** — సెషన్ హిస్టరీలను చదవడానికి చాట్-బబుల్ UI
- **Alerts** — బడ్జెట్ క్యాప్‌లు, ఎర్రర్-రేట్ ట్రిగ్గర్‌లు, ఏజెంట్-ఆఫ్‌లైన్ డిటెక్షన్; Slack, Discord, PagerDuty, Telegram, Emailకు రూట్ చేస్తుంది
- **Approvals** — డిస్ట్రక్టివ్ డిలీట్‌లు, ఫోర్స్ పుష్‌లు, DB మ్యుటేషన్‌లు, sudo, ప్యాకేజీ ఇన్‌స్టాల్‌లు, నెట్‌వర్క్ కాల్‌లను ఒక్క క్లిక్‌తో సైన్-ఆఫ్ వెనుక గేట్ చేయండి

## స్క్రీన్‌షాట్‌లు

### 🧠 Brain — లైవ్ ఏజెంట్ ఈవెంట్ స్ట్రీమ్
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — టోకెన్ యూసేజ్ & సెషన్ సారాంశం
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — రియల్-టైమ్ టూల్ కాల్ ఫీడ్
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — మోడల్ & సెషన్ వారీగా కాస్ట్ బ్రేక్‌డౌన్
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — వర్క్‌స్పేస్ ఫైల్ బ్రౌజర్
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — పొజిషన్ & ఆడిట్ లాగ్
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — బడ్జెట్ క్యాప్‌లు, ఎర్రర్-రేట్ ట్రిగ్గర్‌లు, Slack / Discord / PagerDuty / Emailకు వెబ్‌హుక్‌లు
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — రిస్కీ టూల్ కాల్‌లను మాన్యువల్ సైన్-ఆఫ్ వెనుక గేట్ చేయండి; పాలసీ-బ్యాక్డ్ ప్రొటెక్షన్ రూల్స్
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code కోసం ప్రీ-ఎగ్జిక్యూషన్ బ్లాకింగ్** — ఒక కమాండ్ మ్యాచింగ్
టూల్ కాల్‌లను అవి రన్ అయ్యే *ముందు* పాజ్ చేసి, మీ నిర్ణయం కోసం వేచి ఉండే
PreToolUse హుక్‌ను ఇన్‌స్టాల్ చేస్తుంది (ఫోన్ నుండి ఒక్క ట్యాప్‌తో,
[cloud push notifications](https://app.clawmetry.com/push) ఎనేబుల్ చేసి ఉంటే):

```bash
clawmetry hooks install     # ~/.claude/settings.json రాస్తుంది (ఇడెంపొటెంట్)
clawmetry hooks status      # ఏమి వైర్ చేయబడింది + ఎన్ని పాలసీలు యాక్టివ్‌గా ఉన్నాయి
clawmetry hooks uninstall   # ClawMetry ఎంట్రీలను మాత్రమే తొలగిస్తుంది
```

ఒక డినై ఆ ఒక్క టూల్ కాల్‌ను మాత్రమే బ్లాక్ చేస్తుంది — ఏజెంట్ తన సెషన్‌ను
కొనసాగించి మరో మార్గాన్ని ప్రయత్నించవచ్చు. మీ ఫోన్‌లో అప్రూవ్ చేయడం Claude
Code యొక్క సొంత పర్మిషన్ ప్రాంప్ట్‌ను స్కిప్ చేస్తుంది (మీరు ఇప్పటికే
సమాధానం ఇచ్చారు). మ్యాచ్ కాని టూల్స్‌కు ~40ms ఖర్చవుతుంది, ఇవి Claude Code
యొక్క సాధారణ పర్మిషన్ ఫ్లోకు ఫాల్ త్రూ అవుతాయి. Claude Code స్వయంగా మీ
కోసం వేచి ఉన్నప్పుడు (`permission_prompt` / `idle_prompt` నోటిఫికేషన్‌లు)
మీకు ఫోన్ పుష్ కూడా వస్తుంది.

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

v2 React యాప్ `frontend/`లో ఉంటుంది, v2 ఎనేబుల్ చేసి Flask సర్వర్
స్టార్ట్ చేసినప్పుడు `/v2` వద్ద సర్వ్ చేయబడుతుంది.

డెవలప్ చేస్తున్నప్పుడు రెండు టెర్మినల్‌లను వాడండి:

```bash
# టెర్మినల్ 1: :8900 వద్ద Flask API/సర్వర్
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# టెర్మినల్ 2: :5173 వద్ద Vite డెవ్ సర్వర్
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` తెరవండి. Vite `/api` రిక్వెస్ట్‌లను
`http://localhost:8900`కు ప్రాక్సీ చేస్తుంది, కాబట్టి React యాప్ ఎలాంటి
అదనపు CORS సెటప్ లేకుండా లోకల్ Flask సర్వర్‌తో మాట్లాడగలదు.

Python ప్యాకేజీతో పంపే బండిల్‌ను బిల్డ్ చేయడానికి:

```bash
cd frontend
npm run build
```

ప్రొడక్షన్ బండిల్ `clawmetry/static/v2/dist/`కు రాయబడుతుంది.

## రన్‌టైమ్ / ఏజెంట్ కంపాటిబిలిటీ

ClawMetry OpenClaw మాత్రమే కాకుండా అనేక AI-ఏజెంట్ రన్‌టైమ్‌లను గమనిస్తుంది. OpenClaw కాని ప్రతి రన్‌టైమ్ దాని నేటివ్ సెషన్ ఫార్మాట్‌ను ClawMetry యొక్క యూనిఫైడ్ షేప్‌లుగా అనువదించే ఒక అంకితమైన రీడర్ అడాప్టర్‌ను షిప్ చేస్తుంది; డెమన్ వాటిని రన్‌టైమ్‌తో ట్యాగ్ చేసి అదే DuckDB స్టోర్ + క్లౌడ్ స్నాప్‌షాట్‌లోకి ఇన్జెస్ట్ చేస్తుంది, మరియు ఒకటి కంటే ఎక్కువ రన్‌టైమ్‌లు ఉన్నప్పుడు Session replay ట్యాబ్ ఒక **రన్‌టైమ్ స్విచర్**‌ను చూపిస్తుంది. పూర్తి మ్యాట్రిక్స్ + రన్‌టైమ్‌లను జోడించే గైడ్ కోసం [`docs/compatibility.md`](docs/compatibility.md), మరియు OpenClaw-ఫ్యామిలీ ప్రైమర్ కోసం [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) చూడండి.

| రన్‌టైమ్ / ఏజెంట్ | స్టేటస్ | నోట్స్ |
|---|---|---|
| **OpenClaw** | నేటివ్ | రిఫరెన్స్ రన్‌టైమ్, ఆటో-డిటెక్టెడ్ |
| **PicoClaw** | బీటా అడాప్టర్ | ఫ్లాట్ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ట్రాన్‌స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు. |
| **NanoClaw** | బీటా అడాప్టర్ | పర్-సెషన్ SQLite (`data/v2-sessions`). ట్రాన్‌స్క్రిప్ట్‌లు + మెసేజ్ కౌంట్‌లు. |
| **Hermes** | బీటా అడాప్టర్ | SQLite `~/.hermes/state.db`. ట్రాన్‌స్క్రిప్ట్‌లు, మోడల్, టోకెన్లు/కాస్ట్. |
| **Claude Code** | బీటా అడాప్టర్ | JSONL `~/.claude/projects/.../<id>.jsonl`. ట్రాన్‌స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు + థింకింగ్, టోకెన్ యూసేజ్. |
| **Codex** | బీటా అడాప్టర్ | రోల్‌అవుట్ JSONL `~/.codex/sessions/...`. ట్రాన్‌స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్ యూసేజ్. |
| **Cursor** | బీటా అడాప్టర్ | SQLite `state.vscdb`. చాట్/కంపోజర్ ట్రాన్‌స్క్రిప్ట్‌లు, మోడల్. |
| **Aider** | బీటా అడాప్టర్ | ప్రాజెక్ట్‌కు ఒక `.aider.chat.history.md`. ట్రాన్‌స్క్రిప్ట్‌లు, మోడల్, టోకెన్ కౌంట్‌లు. |
| **Goose** | బీటా అడాప్టర్ | SQLite `~/.local/share/goose`. ట్రాన్‌స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్ టోటల్స్. |
| **opencode** | బీటా అడాప్టర్ | SQLite `~/.local/share/opencode`. ట్రాన్‌స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్లు + కాస్ట్. |
| **Qwen Code** | బీటా అడాప్టర్ | JSONL `~/.qwen/projects/.../chats`. ట్రాన్‌స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్ యూసేజ్. |
| **Pi** | బీటా అడాప్టర్ | JSONL `~/.pi/agent/sessions`. ట్రాన్‌స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్లు + కాస్ట్. |
| **Deep Agents** | బీటా అడాప్టర్ | SQLite `~/.deepagents/.state/sessions.db`. ట్రాన్‌స్క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్లు + కాస్ట్. |

"బీటా అడాప్టర్" అంటే ClawMetry ఆ రన్‌టైమ్ యొక్క వాస్తవ ఆన్-డిస్క్ ఫార్మాట్ కోసం ఒక రీడర్‌ను షిప్ చేస్తుంది, ప్రతి ఒక్కటి ఒక వాస్తవ మెషీన్‌లో వాస్తవ ఇన్‌స్టాల్‌కు వ్యతిరేకంగా బిల్డ్ చేసి + వెరిఫై చేయబడింది (`tests/fixtures/runtimes/<rt>/` చూడండి). అడాప్టర్‌లు రీడ్-ఓన్లీ; ప్రతి ఒక్కటి తన రన్‌టైమ్ వాస్తవానికి ఏమి స్టోర్ చేస్తుందో దాని గురించి నిజాయితీగా ఉంటుంది (ఉదా. PicoClaw/NanoClaw/Cursor టోకెన్ కాస్ట్‌ను డిస్క్‌కు రాయవు). ఒక నోడ్‌పై అనేక రన్‌టైమ్‌లు రన్ అవుతున్నప్పుడు, రన్‌టైమ్ స్విచర్ క్లీన్ డీప్-డైవ్ కోసం సెషన్‌ల వ్యూను ఒకదానికి స్కోప్ చేస్తుంది.

## ఏ SDK ఏజెంట్‌నైనా ట్రాక్ చేయండి — అవుట్-లూప్ కాస్ట్ అట్రిబ్యూషన్

పైన ఉన్న రన్‌టైమ్‌లన్నీ సెషన్‌లను డిస్క్‌కు రాస్తాయి. మీరు OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, లేదా ప్లెయిన్ `httpx` లూప్‌పై బిల్డ్ చేసిన మీ సొంత **ప్రొడక్షన్ ఏజెంట్** అలా చేయదు. ClawMetry యొక్క జీరో-కాన్ఫిగ్ ఇంటర్‌సెప్టర్ `httpx`/`requests`ను మంకీ-పాచ్ చేయడం ద్వారా దాని LLM కాల్‌లను (కాస్ట్, టోకెన్లు, లేటెన్సీ, ఎర్రర్‌లు) ఇప్పటికీ క్యాప్చర్ చేస్తుంది:

```python
import clawmetry.track            # ఇంటర్‌సెప్టర్‌ను యాక్టివేట్ చేయండి
clawmetry.track.set_source("support-agent")   # ఈ ప్రొడక్ట్‌కు పేరు పెట్టండి

# ...మీ ఏజెంట్ మామూలుగా రన్ అవుతుంది; ప్రతి LLM కాల్ ఇప్పుడు ట్రాక్ చేయబడి + అట్రిబ్యూట్ చేయబడుతుంది.
```

`set_source()` (లేదా `CLAWMETRY_SOURCE=support-agent` env var) ప్రతి కాల్‌ను ఒక **నేమ్డ్ సోర్స్**‌తో ట్యాగ్ చేస్తుంది, కాబట్టి మీరు నడిపే ప్రతి ప్రొడక్ట్ డాష్‌బోర్డ్ యొక్క Overview పై **🔌 Out-loop sources** కార్డ్‌లో దాని స్వంత ఫస్ట్-క్లాస్, కాస్ట్-అట్రిబ్యూటబుల్ లైన్‌గా కనిపిస్తుంది — ప్రతి ఏజెంట్‌కు కాల్‌లు, ప్రొవైడర్‌లు, లేటెన్సీ, ఎర్రర్ రేటు. సోర్స్ సెట్ చేయలేదా? కాల్‌లు ఇప్పటికీ ట్రాక్ చేయబడతాయి; కార్డ్ మాత్రం దాగి ఉంటుంది.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ఇది రన్‌టైమ్ అడాప్టర్‌లు ఫీడ్ చేసే అదే డేటా లేయర్ (DuckDB → క్లౌడ్ స్నాప్‌షాట్), కాబట్టి అవుట్-లూప్ సోర్సెస్ మిగతా ప్రతిదాని లాగానే, E2E-ఎన్‌క్రిప్ట్ చేయబడి, క్లౌడ్ డాష్‌బోర్డ్‌కు సింక్ అవుతాయి.

## OpenTelemetry — వెండర్-న్యూట్రల్, మీ ట్రేసెస్‌ను ఎక్కడికైనా పంపండి

ClawMetry **GenAI సెమాంటిక్ కన్వెన్షన్స్** వాడుతూ రెండు దిశల్లోనూ **OpenTelemetry** మాట్లాడుతుంది, కాబట్టి మీ ఏజెంట్ ట్రేసెస్ ఎప్పటికీ ఒక టూల్‌కు లాక్ కాబడవు.

మీ ప్రతి సెషన్‌ను — LLM కాల్‌లు, టూల్స్, సబ్-ఏజెంట్‌లు, టోకెన్లు, కాస్ట్ — ఏ కలెక్టర్‌కైనా (Datadog, Grafana, Honeycomb, లేదా మీ సొంత OTel Collector) OTLP/HTTP GenAI స్పాన్‌లుగా **ఎక్స్‌పోర్ట్** చేయండి:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# సమానంగా:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ఆథ్ హెడర్‌లు మరియు పోల్ ఇంటర్వెల్ ఐచ్ఛిక env vars:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # అదనపు HTTP హెడర్‌లు
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # సెకన్లు (డిఫాల్ట్ 60)
```

**ఇన్జెస్ట్** — బిల్ట్-ఇన్ OTLP రిసీవర్ `/v1/traces` మరియు `/v1/metrics` వద్ద మరేదైనా ఇతర సోర్స్ నుండి ట్రేసెస్ మరియు మెట్రిక్‌లను అంగీకరిస్తుంది (ప్రోటోబఫ్ ఇన్జెస్ట్ కోసం `pip install clawmetry[otel]`).

మీకు జీరో-కాన్ఫిగ్, లోకల్-ఫస్ట్ ClawMetry డాష్‌బోర్డ్ **మరియు** మీ టీమ్ ఇప్పటికే నడుపుతున్న ఏ బ్యాకెండ్‌లోనైనా మీ డేటా లభిస్తుంది — లాక్-ఇన్ లేదు, రెండో ఏజెంట్‌ను ఇన్‌స్టాల్ చేయాల్సిన అవసరం లేదు.

## కాన్ఫిగరేషన్

చాలామందికి ఎలాంటి కాన్ఫిగ్ అవసరం లేదు. ClawMetry మీ వర్క్‌స్పేస్, లాగ్‌లు, సెషన్‌లు, మరియు క్రాన్‌లను ఆటో-డిటెక్ట్ చేస్తుంది.

కస్టమైజ్ చేయాల్సి వస్తే:

```bash
clawmetry --port 9000              # కస్టమ్ పోర్ట్ (డిఫాల్ట్: 8900)
clawmetry --host 127.0.0.1         # లోకల్‌హోస్ట్‌కు మాత్రమే బైండ్ చేయండి
clawmetry --workspace ~/mybot      # కస్టమ్ వర్క్‌స్పేస్ పాత్
clawmetry --name "Alice"           # Flow విజువలైజేషన్‌లో మీ పేరు
```

అన్ని ఆప్షన్‌లు: `clawmetry --help`

## సపోర్టెడ్ చానెల్స్

మీరు కాన్ఫిగర్ చేసిన ప్రతి OpenClaw చానెల్ కోసం ClawMetry లైవ్ యాక్టివిటీని చూపుతుంది. మీ `openclaw.json`లో నిజంగా సెటప్ చేయబడిన చానెల్స్ మాత్రమే Flow డయాగ్రామ్‌లో కనిపిస్తాయి — కాన్ఫిగర్ చేయని వాటిని ఆటోమేటిక్‌గా దాచేస్తుంది.

Flowలో ఏదైనా చానెల్ నోడ్‌ను క్లిక్ చేసి, ఇన్‌కమింగ్/అవుట్‌గోయింగ్ మెసేజ్ కౌంట్‌లతో లైవ్ చాట్ బబుల్ వ్యూను చూడండి.

| చానెల్ | స్టేటస్ | లైవ్ పాప్‌అప్ | నోట్స్ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ పూర్తి | ✅ | మెసేజ్‌లు, స్టాట్స్, 10s రిఫ్రెష్ |
| 💬 **iMessage** | ✅ పూర్తి | ✅ | `~/Library/Messages/chat.db`ను నేరుగా చదువుతుంది |
| 💚 **WhatsApp** | ✅ పూర్తి | ✅ | WhatsApp Web (Baileys) ద్వారా |
| 🔵 **Signal** | ✅ పూర్తి | ✅ | signal-cli ద్వారా |
| 🟣 **Discord** | ✅ పూర్తి | ✅ | గిల్డ్ + చానెల్ డిటెక్షన్ |
| 🟪 **Slack** | ✅ పూర్తి | ✅ | వర్క్‌స్పేస్ + చానెల్ డిటెక్షన్ |
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

> **ఆటో-డిటెక్షన్:** ClawMetry మీ `~/.openclaw/openclaw.json`ను చదివి, మీరు నిజంగా కాన్ఫిగర్ చేసిన చానెల్స్‌ను మాత్రమే రెండర్ చేస్తుంది. మాన్యువల్ సెటప్ అవసరం లేదు.

## Docker డిప్లాయ్‌మెంట్

ClawMetryను ఒక కంటైనర్‌లో రన్ చేయాలనుకుంటున్నారా? సమస్య లేదు! 🐳

**Docker‌తో త్వరిత ప్రారంభం:**

```bash
# ఇమేజ్‌ను బిల్డ్ చేయండి
docker build -t clawmetry .

# డిఫాల్ట్ సెట్టింగ్‌లతో రన్ చేయండి
docker run -p 8900:8900 clawmetry

# లేదా మీ ఏజెంట్ యొక్క డేటా డైర్‌ను మౌంట్ చేయండి (చూపబడింది: OpenClaw యొక్క ~/.openclaw)
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

> **గమనిక:** Dockerలో రన్ చేస్తున్నప్పుడు, ClawMetry మీ సెటప్‌ను ఆటో-డిటెక్ట్ చేయగలిగేలా మీ ఏజెంట్ యొక్క డేటా + లాగ్ డైరెక్టరీలను (ఉదా. `~/.openclaw`, `~/.claude`, `~/.codex`) మౌంట్ చేయండి.

## అవసరాలు

- Python 3.8+
- Flask (pip ద్వారా ఆటోమేటిక్‌గా ఇన్‌స్టాల్ అవుతుంది)
- అదే మెషీన్‌పై ఒక AI ఏజెంట్ రన్‌టైమ్: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, లేదా Deep Agents (లేదా Docker కోసం మౌంటెడ్ వాల్యూమ్‌లు)
- Linux లేదా macOS

## NemoClaw / OpenShell సపోర్ట్

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw)ను ఆటోమేటిక్‌గా డిటెక్ట్ చేస్తుంది — NVIDIA యొక్క ఎంటర్‌ప్రైజ్ సెక్యూరిటీ ర్యాపర్, ఇది ఏజెంట్‌లను శాండ్‌బాక్స్డ్ OpenShell కంటైనర్‌ల లోపల నడుపుతుంది.

చాలా సందర్భాల్లో అదనపు కాన్ఫిగరేషన్ అవసరం లేదు. సెషన్ ఫైల్‌లు హోస్ట్‌పై `~/.openclaw/`లో ఉన్నా లేదా OpenShell కంటైనర్‌లో ఉన్నా, సింక్ డెమన్ వాటిని ఆటో-డిస్కవర్ చేస్తుంది.

### ఇది ఎలా పనిచేస్తుంది

ClawMetry NemoClawను రెండు విధాలుగా డిటెక్ట్ చేస్తుంది:

1. **బైనరీ డిటెక్షన్** — `nemoclaw` CLI ఉందా అని చెక్ చేసి, శాండ్‌బాక్స్ ఇన్ఫో పొందడానికి `nemoclaw status` రన్ చేస్తుంది
2. **కంటైనర్ డిటెక్షన్** — `openshell`, `nemoclaw`, లేదా `ghcr.io/nvidia/` ఇమేజ్‌ల కోసం రన్నింగ్ Docker కంటైనర్‌లను స్కాన్ చేసి, వాల్యూమ్ మౌంట్‌లు లేదా `docker cp` ద్వారా సెషన్‌లను చదువుతుంది

NemoClaw కంటైనర్‌ల నుండి సింక్ చేయబడిన సెషన్ ఫైల్‌లు క్లౌడ్ డాష్‌బోర్డ్‌లో `runtime=nemoclaw` మరియు `container_id` మెటాడేటాతో ట్యాగ్ చేయబడతాయి, కాబట్టి మీరు వాటిని ఒక్క చూపులో స్టాండర్డ్ OpenClaw సెషన్‌ల నుండి వేరు చేయగలరు.

### సిఫార్సు చేసిన సెటప్: HOST పై సింక్ డెమన్

ఉత్తమ అనుభవం కోసం, ClawMetry యొక్క సింక్ డెమన్‌ను (శాండ్‌బాక్స్ లోపల కాకుండా) **హోస్ట్ మెషీన్**‌పై రన్ చేయండి. ఇది NemoClaw నెట్‌వర్క్ పాలసీ పరిమితులను తప్పిస్తుంది.

```bash
# హోస్ట్‌పై (శాండ్‌బాక్స్ బయట)
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

### శాండ్‌బాక్స్ లోపల రన్ చేయడం (అడ్వాన్స్డ్)

మీరు తప్పనిసరిగా సింక్ డెమన్‌ను OpenShell శాండ్‌బాక్స్ **లోపల** రన్ చేయాల్సి వస్తే, అది ClawMetry ఇన్జెస్ట్ APIని చేరుకోగలిగేలా మీ NemoClaw నెట్‌వర్క్ పాలసీకి ఈ ఎగ్రెస్ రూల్‌ను జోడించండి:

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

సింక్ డెమన్ `ingest.clawmetry.com`కు మాత్రమే అవుట్‌బౌండ్ HTTPS కాల్‌లు చేస్తుంది. ఇన్‌బౌండ్ పోర్ట్‌లు అవసరం లేదు.

---

## క్లౌడ్ డిప్లాయ్‌మెంట్

SSH టన్నెల్‌లు, రివర్స్ ప్రాక్సీ, మరియు Docker కోసం **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** చూడండి.

## టెస్టింగ్

ఈ ప్రాజెక్ట్ BrowserStackతో టెస్ట్ చేయబడింది.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## టెలిమెట్రీ

మీరు కొత్త మెషీన్‌లో `clawmetry` CLIని మొదటిసారి రన్ చేసినప్పుడు
ClawMetry ఒకే ఒక్క అనానిమస్ "ఫస్ట్ రన్" పింగ్‌ను
`https://app.clawmetry.com/api/install`కు పంపుతుంది. దీన్ని ఇన్‌స్టాల్‌లను
లెక్కించడానికి (OSS ప్రాజెక్ట్‌కు మా వద్ద ఉన్న ఏకైక మార్కెటింగ్ మెట్రిక్)
మరియు మా యూజర్లు ఏ ఏజెంట్ ఫ్రేమ్‌వర్క్‌లను ఇన్‌స్టాల్ చేశారో తెలుసుకోవడానికి
వాడతాము.

**ఇన్‌స్టాల్‌కు ఖచ్చితంగా ఒక్క POST**, అందులో ఉండేవి:

| ఫీల్డ్ | ఉదాహరణ | ఎందుకు |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` వద్ద స్టోర్ చేసిన రాండమ్ UUID | డెడప్; మీ ఇమెయిల్ లేదా api_keyతో లింక్ కాదు |
| `version` | `0.12.167` | ఏ వెర్షన్‌లు వాడుకలో ఉన్నాయి |
| `os` / `os_version` | `Darwin` / `25.3.0` | ప్లాట్‌ఫారమ్ సపోర్ట్ ప్రాధాన్యతలు |
| `python` | `3.11.15` | Python వెర్షన్ సపోర్ట్ మ్యాట్రిక్స్ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | తర్వాత మేము ఏ ఏజెంట్‌లతో ఇంటిగ్రేట్ చేయాలి |
| `is_ci` / `ci_provider` | `true` / `github_actions` | హ్యూమన్ ఇన్‌స్టాల్‌లను CI నాయిస్ నుండి వేరు చేయడానికి |

**మేము పంపనివి**: IP (క్లౌడ్ రిక్వెస్ట్ నుండి సర్వర్-సైడ్‌లో దేశం కోడ్‌ను
డిరైవ్ చేసి, తర్వాత IPని డిస్కార్డ్ చేస్తుంది), హోస్ట్‌నేమ్, యూజర్‌నేమ్,
వర్క్‌స్పేస్ పాత్, ఫైల్ కంటెంట్‌లు, మీ api_key, మీ ఇమెయిల్, PII లేదా
వర్క్‌స్పేస్-స్పెసిఫిక్ ఏదైనా. వైర్ పేలోడ్
[`clawmetry/telemetry.py`](clawmetry/telemetry.py)లో ఆడిటబుల్‌గా ఉంది.

**ఆప్ట్ అవుట్** (వీటిలో ఏదైనా ఒకటి దీన్ని శాశ్వతంగా డిజేబుల్ చేస్తుంది):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # ప్రతి షెల్‌కు
export DO_NOT_TRACK=1                          # W3C క్రాస్-టూల్ స్టాండర్డ్
touch ~/.clawmetry/notelemetry                 # పర్సిస్టెంట్ ఫైల్ మార్కర్
```

నెట్‌వర్క్ ఫెయిల్యూర్ ఇక్కడ `clawmetry` రన్ కావడాన్ని ఎప్పుడూ బ్లాక్
చేయదు — పింగ్ 3s టైమ్‌అవుట్‌తో డెమన్ థ్రెడ్‌పై ఫైర్-అండ్-ఫర్గెట్‌గా
ఉంటుంది.

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
