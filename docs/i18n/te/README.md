<!-- i18n-src:48548997be76 -->
> తెలుగు translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**మీ ఏజెంట్ ఆలోచించడం చూడండి.** **12 AI ఏజెంట్ రన్‌టైమ్‌ల** కోసం రియల్-టైమ్ పరిశీలన: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex మరియు మరో 8. మీ మొత్తం ఏజెంట్ సమూహం కోసం ఒకే డ్యాష్‌బోర్డ్.

> 🌐 **దీన్ని చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒకే కమాండ్. సున్నా కాన్ఫిగరేషన్. అన్నీ స్వయంచాలకంగా గుర్తిస్తుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** లో తెరుచుకుంటుంది, అంతే.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 12 ఏజెంట్ రన్‌టైమ్‌లతో పనిచేస్తుంది

ClawMetry మొదలైంది OpenClaw కోసం పరిశీలనగా, ఇప్పుడు మీ **మొత్తం ఏజెంట్ సమూహాన్ని** ఒకే డ్యాష్‌బోర్డ్‌లో కొలుస్తుంది, మీ మెషీన్‌పై ప్రతి రన్‌టైమ్‌ను స్వయంచాలకంగా గుర్తించి:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw మరియు NemoClaw ఓపెన్-సోర్స్ యాప్‌లో ఉచితంగా అందుబాటులో ఉంటాయి; మిగిలిన రన్‌టైమ్‌లు ClawMetry Cloud లేదా స్వయం-హోస్ట్ చేసిన Pro లైసెన్స్‌తో వెలిగిపోతాయి. హెడర్ నుండి రన్‌టైమ్‌లు మారండి, ప్రతి ట్యాబ్ అంటే ఖర్చు, టోకెన్లు, టూళ్లు, ట్రేస్‌లు ఆ రన్‌టైమ్‌కు మళ్లీ స్కోప్ అవుతాయి.

## మీకు లభించేది

- **Flow** — ఛానెళ్ల ద్వారా, బ్రెయిన్, టూళ్ల ద్వారా మరియు వెనక్కి ప్రవహించే సందేశాలను చూపించే లైవ్ యానిమేటెడ్ రేఖాచిత్రం
- **Overview** — హెల్త్ చెక్‌లు, యాక్టివిటీ హీట్‌మ్యాప్, సెషన్ సంఖ్యలు, మోడల్ సమాచారం
- **Usage** — రోజువారీ/వారపు/నెలవారీ విభజనలతో టోకెన్ మరియు ఖర్చు ట్రాకింగ్
- **Sessions** — మోడల్, టోకెన్లు, చివరి యాక్టివిటీతో యాక్టివ్ ఏజెంట్ సెషన్లు
- **Crons** — స్టేటస్, తదుపరి రన్, వ్యవధితో షెడ్యూల్ చేసిన జాబ్‌లు
- **Logs** — రంగు-కోడెడ్ రియల్-టైమ్ లాగ్ స్ట్రీమింగ్
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, రోజువారీ నోట్స్ చదవండి
- **Transcripts** — సెషన్ చరిత్రలు చదవడానికి చాట్-బబుల్ UI
- **Alerts** — బడ్జెట్ పరిమితులు, ఎర్రర్-రేట్ ట్రిగ్గర్‌లు, ఏజెంట్-ఆఫ్‌లైన్ గుర్తింపు; Slack, Discord, PagerDuty, Telegram, Email కు రూట్ చేస్తుంది
- **Approvals** — విధ్వంసకర తొలగింపులు, ఫోర్స్ పుష్‌లు, DB మ్యుటేషన్లు, sudo, ప్యాకేజీ ఇన్‌స్టాల్‌లు, నెట్‌వర్క్ కాల్‌లను ఒక్క క్లిక్ అనుమతితో నిరోధించడం

## స్క్రీన్‌షాట్లు

### 🧠 Brain — లైవ్ ఏజెంట్ ఈవెంట్ స్ట్రీమ్
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — టోకెన్ వినియోగం మరియు సెషన్ సారాంశం
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — రియల్-టైమ్ టూల్ కాల్ ఫీడ్
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — మోడల్ మరియు సెషన్ వారీగా ఖర్చు విభజన
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — వర్క్‌స్పేస్ ఫైల్ బ్రౌజర్
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — పోచర్ మరియు ఆడిట్ లాగ్
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — బడ్జెట్ పరిమితులు, ఎర్రర్-రేట్ ట్రిగ్గర్‌లు, Slack / Discord / PagerDuty / Email కు వెబ్‌హుక్‌లు
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — ప్రమాదకర టూల్ కాల్‌లను మాన్యువల్ అనుమతి వెనక నిరోధించడం; పాలసీ-ఆధారిత రక్షణ నియమాలు
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

v2 React యాప్ `frontend/` లో ఉంటుంది మరియు Flask సర్వర్ v2 ఎనేబుల్‌తో ప్రారంభించినప్పుడు `/v2` వద్ద సర్వ్ చేయబడుతుంది.

డెవలప్ చేసేటప్పుడు రెండు టెర్మినల్‌లు వాడండి:

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

`http://localhost:5173/v2/` తెరవండి. Vite అదనపు CORS సెటప్ లేకుండా React యాప్ లోకల్ Flask సర్వర్‌తో మాట్లాడేలా `/api` అభ్యర్థనలను `http://localhost:8900` కు ప్రాక్సీ చేస్తుంది.

Python ప్యాకేజీతో పంపిన బండిల్ నిర్మించడానికి:

```bash
cd frontend
npm run build
```

ప్రొడక్షన్ బండిల్ `clawmetry/static/v2/dist/` కు వ్రాయబడుతుంది.

## రన్‌టైమ్ / ఏజెంట్ అనుకూలత

ClawMetry చాలా AI-ఏజెంట్ రన్‌టైమ్‌లను గమనిస్తుంది, కేవలం OpenClaw మాత్రమే కాదు. ప్రతి OpenClaw-కాని రన్‌టైమ్ దాని స్థానిక సెషన్ ఫార్మాట్‌ను ClawMetry యొక్క యూనిఫైడ్ షేప్‌లలోకి అనువదించే ఒక అంకిత రీడర్ అడాప్టర్‌తో వస్తుంది; డీమన్ వాటిని రన్‌టైమ్‌తో ట్యాగ్ చేసి అదే DuckDB స్టోర్ మరియు క్లౌడ్ స్నాప్‌షాట్‌లో స్వీకరిస్తుంది, మరియు ఒకటి కంటే ఎక్కువ ఉన్నప్పుడు సెషన్ రీప్లే ట్యాబ్ **రన్‌టైమ్ స్విచర్** చూపిస్తుంది. పూర్తి మ్యాట్రిక్స్ మరియు రన్‌టైమ్‌లు జోడించడానికి గైడ్ కోసం [`docs/compatibility.md`](docs/compatibility.md) చూడండి, మరియు OpenClaw-ఫ్యామిలీ ప్రైమర్ కోసం [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) చూడండి.

| రన్‌టైమ్ / ఏజెంట్ | స్టేటస్ | గమనికలు |
|---|---|---|
| **OpenClaw** | నేటివ్ | రెఫరెన్స్ రన్‌టైమ్, స్వయంచాలకంగా గుర్తించబడింది |
| **PicoClaw** | బీటా అడాప్టర్ | ఫ్లాట్ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు. |
| **NanoClaw** | బీటా అడాప్టర్ | పర్-సెషన్ SQLite (`data/v2-sessions`). ట్రాన్స్‌క్రిప్ట్‌లు మరియు మెసేజ్ కౌంట్‌లు. |
| **Hermes** | బీటా అడాప్టర్ | SQLite `~/.hermes/state.db`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టోకెన్లు/ఖర్చు. |
| **Claude Code** | బీటా అడాప్టర్ | JSONL `~/.claude/projects/.../<id>.jsonl`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు మరియు థింకింగ్, టోకెన్ వినియోగం. |
| **Codex** | బీటా అడాప్టర్ | రోలౌట్ JSONL `~/.codex/sessions/...`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్ వినియోగం. |
| **Cursor** | బీటా అడాప్టర్ | SQLite `state.vscdb`. చాట్/కంపోజర్ ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్. |
| **Aider** | బీటా అడాప్టర్ | ప్రతి ప్రాజెక్ట్‌కు `.aider.chat.history.md`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టోకెన్ కౌంట్‌లు. |
| **Goose** | బీటా అడాప్టర్ | SQLite `~/.local/share/goose`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్ మొత్తాలు. |
| **opencode** | బీటా అడాప్టర్ | SQLite `~/.local/share/opencode`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్లు మరియు ఖర్చు. |
| **Qwen Code** | బీటా అడాప్టర్ | JSONL `~/.qwen/projects/.../chats`. ట్రాన్స్‌క్రిప్ట్‌లు, మోడల్, టూల్ కాల్‌లు, టోకెన్ వినియోగం. |

"బీటా అడాప్టర్" అంటే ClawMetry ఆ రన్‌టైమ్ యొక్క నిజమైన డిస్క్-పై ఫార్మాట్ కోసం రీడర్‌ను పంపిస్తుంది, ప్రతి ఒక్కటి నిజమైన మెషీన్‌పై నిజమైన ఇన్‌స్టాల్‌పై నిర్మించబడి ధృవీకరించబడింది (చూడండి `tests/fixtures/runtimes/<rt>/`). అడాప్టర్‌లు చదవడానికి మాత్రమే; ప్రతి ఒక్కటి దాని రన్‌టైమ్ నిజంగా ఏమి నిల్వ చేస్తుందో దానిపై నిజాయితీగా ఉంటుంది (ఉదాహరణకు PicoClaw/NanoClaw/Cursor టోకెన్ ఖర్చును డిస్క్‌కు వ్రాయవు). ఒక నోడ్‌పై అనేక రన్‌టైమ్‌లు నడుస్తున్నప్పుడు, రన్‌టైమ్ స్విచర్ లోతైన అన్వేషణ కోసం సెషన్‌ల వీక్షణను ఒకదానికి పరిమితం చేస్తుంది.

## ఏదైనా SDK ఏజెంట్‌ను ట్రాక్ చేయండి - అవుట్-లూప్ కాస్ట్ అట్రిబ్యూషన్

పైన పేర్కొన్న రన్‌టైమ్‌లన్నీ సెషన్‌లను డిస్క్‌కు వ్రాస్తాయి. మీరు OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B లేదా సాదా `httpx` లూప్‌పై నిర్మించిన మీ స్వంత **ప్రొడక్షన్ ఏజెంట్** వ్రాయదు. ClawMetry యొక్క జీరో-కాన్ఫిగ్ ఇంటర్‌సెప్టర్ `httpx`/`requests` ను మంకీ-పాచింగ్ చేయడం ద్వారా దాని LLM కాల్‌లను (ఖర్చు, టోకెన్లు, లేటెన్సీ, ఎర్రర్‌లు) ఇంకా సేకరిస్తుంది:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (లేదా `CLAWMETRY_SOURCE=support-agent` env var) ప్రతి కాల్‌కు **పేరు పెట్టబడిన సోర్స్‌తో** ట్యాగ్ చేస్తుంది, కాబట్టి మీరు నడిపే ప్రతి ప్రొడక్ట్ డ్యాష్‌బోర్డ్ యొక్క Overview లో **🔌 Out-loop sources** కార్డ్‌లో దాని స్వంత ఫస్ట్-క్లాస్, కాస్ట్-అట్రిబ్యూటబుల్ లైన్‌గా కనిపిస్తుంది. కాల్‌లు, ప్రొవైడర్‌లు, లేటెన్సీ, ఏజెంట్ వారీగా ఎర్రర్ రేట్. సోర్స్ సెట్ చేయలేదా? కాల్‌లు ఇంకా ట్రాక్ చేయబడతాయి; కార్డ్ మాత్రమే దాచబడుతుంది.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

ఇది రన్‌టైమ్ అడాప్టర్‌లు ఫీడ్ చేసే అదే డేటా లేయర్ (DuckDB క్లౌడ్ స్నాప్‌షాట్), కాబట్టి అవుట్-లూప్ సోర్స్‌లు మిగతా వన్నీ చేసే విధంగానే క్లౌడ్ డ్యాష్‌బోర్డ్‌కు సింక్ అవుతాయి, E2E-ఎన్‌క్రిప్ట్ చేయబడి.

## OpenTelemetry — వెండర్-న్యూట్రల్, మీ ట్రేస్‌లను ఎక్కడైనా పంపండి

ClawMetry **GenAI సెమాంటిక్ కన్వెన్షన్‌లను** ఉపయోగించి రెండు దిశలలో **OpenTelemetry** మాట్లాడుతుంది, కాబట్టి మీ ఏజెంట్ ట్రేస్‌లు ఒక టూల్‌కు లాక్ అవ్వవు.

ప్రతి సెషన్‌ను LLM కాల్‌లు, టూళ్లు, సబ్-ఏజెంట్‌లు, టోకెన్లు, ఖర్చుతో OTLP/HTTP GenAI స్పాన్‌లుగా ఏదైనా కలెక్టర్‌కు (Datadog, Grafana, Honeycomb లేదా మీ స్వంత OTel కలెక్టర్) **ఎక్స్‌పోర్ట్** చేయండి:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ఆథ్ హెడర్‌లు మరియు పోల్ ఇంటర్వల్ ఐచ్ఛిక env వేరియబుల్‌లు:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**స్వీకరించడం** - బిల్ట్-ఇన్ OTLP రిసీవర్ `/v1/traces` మరియు `/v1/metrics` వద్ద మరే దానినైనా ట్రేస్‌లు మరియు మెట్రిక్‌లను అంగీకరిస్తుంది (ప్రోటోబఫ్ ఇంజెస్ట్ కోసం `pip install clawmetry[otel]`).

మీకు జీరో-కాన్ఫిగ్, లోకల్-ఫస్ట్ ClawMetry డ్యాష్‌బోర్డ్ **మరియు** మీ టీమ్ ఇప్పటికే నడిపే బ్యాకెండ్‌లో మీ డేటా లభిస్తుంది - లాక్-ఇన్ లేదు, ఇన్‌స్టాల్ చేయడానికి రెండవ ఏజెంట్ లేదు.

## కాన్ఫిగరేషన్

చాలా మంది వ్యక్తులకు ఏ కాన్ఫిగ్ అవసరం లేదు. ClawMetry మీ వర్క్‌స్పేస్, లాగ్‌లు, సెషన్‌లు మరియు crons ను స్వయంచాలకంగా గుర్తిస్తుంది.

మీరు కస్టమైజ్ చేయాల్సిన అవసరం ఉంటే:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

అన్ని ఆప్షన్‌లు: `clawmetry --help`

## మద్దతు ఉన్న ఛానెళ్లు

ClawMetry మీరు కాన్ఫిగర్ చేసిన ప్రతి OpenClaw ఛానెల్ కోసం లైవ్ యాక్టివిటీ చూపిస్తుంది. మీ `openclaw.json` లో నిజంగా సెటప్ చేయబడిన ఛానెళ్లు మాత్రమే Flow రేఖాచిత్రంలో కనిపిస్తాయి, కాన్ఫిగర్ చేయబడనవి స్వయంచాలకంగా దాచబడతాయి.

రాబోయే/వెళ్లే మెసేజ్ కౌంట్‌లతో లైవ్ చాట్ బబుల్ వీక్షణ చూడడానికి Flow లో ఏదైనా ఛానెల్ నోడ్‌ను క్లిక్ చేయండి.

| ఛానెల్ | స్టేటస్ | లైవ్ పాప్అప్ | గమనికలు |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ పూర్తి | ✅ | సందేశాలు, స్టాట్‌లు, 10s రిఫ్రెష్ |
| 💬 **iMessage** | ✅ పూర్తి | ✅ | నేరుగా `~/Library/Messages/chat.db` చదువుతుంది |
| 💚 **WhatsApp** | ✅ పూర్తి | ✅ | WhatsApp Web ద్వారా (Baileys) |
| 🔵 **Signal** | ✅ పూర్తి | ✅ | signal-cli ద్వారా |
| 🟣 **Discord** | ✅ పూర్తి | ✅ | గిల్డ్ మరియు ఛానెల్ గుర్తింపు |
| 🟪 **Slack** | ✅ పూర్తి | ✅ | వర్క్‌స్పేస్ మరియు ఛానెల్ గుర్తింపు |
| 🌐 **Webchat** | ✅ పూర్తి | ✅ | బిల్ట్-ఇన్ వెబ్ UI సెషన్‌లు |
| 📡 **IRC** | ✅ పూర్తి | ✅ | టెర్మినల్-స్టైల్ బబుల్ UI |
| 🍏 **BlueBubbles** | ✅ పూర్తి | ✅ | BlueBubbles REST API ద్వారా iMessage |
| 🔵 **Google Chat** | ✅ పూర్తి | ✅ | Chat API వెబ్‌హుక్‌ల ద్వారా |
| 🟣 **MS Teams** | ✅ పూర్తి | ✅ | Teams బాట్ ప్లగిన్ ద్వారా |
| 🔷 **Mattermost** | ✅ పూర్తి | ✅ | స్వయం-హోస్ట్ చేసిన టీమ్ చాట్ |
| 🟩 **Matrix** | ✅ పూర్తి | ✅ | డీసెంట్రలైజ్డ్, E2EE మద్దతు |
| 🟢 **LINE** | ✅ పూర్తి | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ పూర్తి | ✅ | డీసెంట్రలైజ్డ్ NIP-04 DMs |
| 🟣 **Twitch** | ✅ పూర్తి | ✅ | IRC కనెక్షన్ ద్వారా చాట్ |
| 🔷 **Feishu/Lark** | ✅ పూర్తి | ✅ | WebSocket ఈవెంట్ సబ్‌స్క్రిప్షన్ |
| 🔵 **Zalo** | ✅ పూర్తి | ✅ | Zalo Bot API |

> **స్వయంచాలక గుర్తింపు:** ClawMetry మీ `~/.openclaw/openclaw.json` చదువుతుంది మరియు మీరు నిజంగా కాన్ఫిగర్ చేసిన ఛానెళ్లను మాత్రమే రెండర్ చేస్తుంది. మాన్యువల్ సెటప్ అవసరం లేదు.

## Docker డెప్లాయ్‌మెంట్

కంటైనర్‌లో ClawMetry నడపాలనుకుంటున్నారా? సమస్య లేదు! 🐳

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

> **గమనిక:** Docker లో నడుపుతున్నప్పుడు, ClawMetry మీ సెటప్‌ను స్వయంచాలకంగా గుర్తించగలిగేలా మీ ఏజెంట్ యొక్క డేటా మరియు లాగ్ డైరెక్టరీలు (ఉదాహరణకు `~/.openclaw`, `~/.claude`, `~/.codex`) మౌంట్ చేయండి.

## అవసరాలు

- Python 3.8+
- Flask (pip ద్వారా స్వయంచాలకంగా ఇన్‌స్టాల్ చేయబడుతుంది)
- అదే మెషీన్‌పై ఒక AI ఏజెంట్ రన్‌టైమ్: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw లేదా PicoClaw (లేదా Docker కోసం మౌంటెడ్ వాల్యూమ్‌లు)
- Linux లేదా macOS

## NemoClaw / OpenShell మద్దతు

ClawMetry స్వయంచాలకంగా [NemoClaw](https://github.com/NVIDIA/NemoClaw) ను గుర్తిస్తుంది, ఇది NVIDIA యొక్క ఎంటర్‌ప్రైజ్ సెక్యూరిటీ ర్యాపర్ OpenClaw కోసం, ఇది ఏజెంట్‌లను శాండ్‌బాక్స్ చేయబడిన OpenShell కంటైనర్‌లలో నడిపిస్తుంది.

చాలా సందర్భాలలో అదనపు కాన్ఫిగరేషన్ అవసరం లేదు. సింక్ డీమన్ సెషన్ ఫైల్‌లను హోస్ట్‌పై `~/.openclaw/` లో లేదా OpenShell కంటైనర్ లోపల ఎక్కడ ఉన్నా స్వయంచాలకంగా కనుగొంటుంది.

### ఇది ఎలా పనిచేస్తుంది

ClawMetry NemoClaw ను రెండు విధాలుగా గుర్తిస్తుంది:

1. **బైనరీ గుర్తింపు** - `nemoclaw` CLI కోసం తనిఖీ చేస్తుంది మరియు శాండ్‌బాక్స్ సమాచారం పొందడానికి `nemoclaw status` నడిపిస్తుంది
2. **కంటైనర్ గుర్తింపు** - `openshell`, `nemoclaw` లేదా `ghcr.io/nvidia/` ఇమేజ్‌ల కోసం నడుస్తున్న Docker కంటైనర్‌లను స్కాన్ చేస్తుంది, తర్వాత వాల్యూమ్ మౌంట్‌లు లేదా `docker cp` ద్వారా సెషన్‌లు చదువుతుంది

NemoClaw కంటైనర్‌ల నుండి సింక్ చేయబడిన సెషన్ ఫైల్‌లు క్లౌడ్ డ్యాష్‌బోర్డ్‌లో `runtime=nemoclaw` మరియు `container_id` మెటాడేటాతో ట్యాగ్ చేయబడతాయి, కాబట్టి మీరు వాటిని ఒక్క చూపుతో స్టాండర్డ్ OpenClaw సెషన్‌ల నుండి వేరు చేయవచ్చు.

### సిఫార్సు చేయబడిన సెటప్: HOST పై సింక్ డీమన్

అత్యుత్తమ అనుభవం కోసం, ClawMetry యొక్క సింక్ డీమన్‌ను **హోస్ట్ మెషీన్‌పై** నడపండి (శాండ్‌బాక్స్ లోపల కాదు). ఇది NemoClaw నెట్‌వర్క్ పాలసీ పరిమితులను నివారిస్తుంది.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

సింక్ డీమన్ నడుస్తున్న ఏదైనా OpenShell కంటైనర్‌లలో సెషన్‌లను స్వయంచాలకంగా కనుగొంటుంది.

### ఐచ్ఛికం: స్పష్టమైన శాండ్‌బాక్స్ పేరు

స్వయంచాలక గుర్తింపు పనిచేయకపోతే, ClawMetry ని సరైన శాండ్‌బాక్స్‌వైపు చూపించండి:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### శాండ్‌బాక్స్ లోపల నడపడం (అడ్వాన్స్డ్)

మీరు OpenShell శాండ్‌బాక్స్ **లోపల** సింక్ డీమన్‌ను నడపాల్సిన అవసరం ఉంటే, అది ClawMetry ఇంజెస్ట్ API కి చేరుకోగలిగేలా మీ NemoClaw నెట్‌వర్క్ పాలసీకి ఈ ఎగ్రెస్ నియమాన్ని జోడించండి:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

దీన్ని వర్తింపజేయండి:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### పోర్ట్‌లు మరియు ఎండ్‌పాయింట్‌లు

| ఎండ్‌పాయింట్ | పోర్ట్ | ప్రోటోకాల్ | అవసరం |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | అవును (సింక్ డీమన్ క్లౌడ్) |
| `localhost:8900` | 8900 | HTTP | అవును (లోకల్ డ్యాష్‌బోర్డ్ UI) |
| Docker సాకెట్ (`/var/run/docker.sock`) | — | Unix సాకెట్ | కంటైనర్ సెషన్ డిస్కవరీ కోసం |

సింక్ డీమన్ `ingest.clawmetry.com` కు అవుట్‌బౌండ్ HTTPS కాల్‌లు మాత్రమే చేస్తుంది. ఇన్‌బౌండ్ పోర్ట్‌లు అవసరం లేదు.

---

## క్లౌడ్ డెప్లాయ్‌మెంట్

SSH టన్నెల్‌లు, రివర్స్ ప్రాక్సీ మరియు Docker కోసం **[క్లౌడ్ టెస్టింగ్ గైడ్](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** చూడండి.

## టెస్టింగ్

ఈ ప్రాజెక్ట్ BrowserStack తో టెస్ట్ చేయబడింది.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## టెలిమెట్రీ

ClawMetry కొత్త మెషీన్‌పై మీరు మొదటిసారి `clawmetry` CLI నడిపినప్పుడు `https://app.clawmetry.com/api/install` కు ఒకే ఒక్క అనామక "మొదటి రన్" పింగ్ పంపిస్తుంది. ఇన్‌స్టాల్‌లు లెక్కించడానికి (ఒక OSS ప్రాజెక్ట్‌కు మాకు ఉన్న ఏకైక మార్కెటింగ్ మెట్రిక్) మరియు మా వినియోగదారులు ఏ ఏజెంట్ ఫ్రేమ్‌వర్క్‌లు ఇన్‌స్టాల్ చేశారో తెలుసుకోవడానికి ఇది ఉపయోగిస్తాం.

**ఇన్‌స్టాల్ కు సరిగ్గా ఒక POST**, దీన్ని కలిగి ఉంటుంది:

| ఫీల్డ్ | ఉదాహరణ | ఎందుకు |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` వద్ద నిల్వ చేయబడిన యాదృచ్ఛిక UUID | డీడప్; మీ ఇమెయిల్ లేదా api_key తో లింక్ కాదు |
| `version` | `0.12.167` | ఏ వెర్షన్‌లు వాడుకలో ఉన్నాయి |
| `os` / `os_version` | `Darwin` / `25.3.0` | ప్లాట్‌ఫాం మద్దతు ప్రాధాన్యతలు |
| `python` | `3.11.15` | Python వెర్షన్ మద్దతు మ్యాట్రిక్స్ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | తర్వాత ఏ ఏజెంట్‌లతో ఇంటిగ్రేట్ చేయాలి |
| `is_ci` / `ci_provider` | `true` / `github_actions` | మానవ ఇన్‌స్టాల్‌లను CI నాయిస్ నుండి వేరు చేయడం |

**మేము పంపించనివి**: IP (క్లౌడ్ అభ్యర్థన నుండి సర్వర్-సైడ్‌లో కంట్రీ కోడ్ పొందుతుంది, తర్వాత IP తొలగిస్తుంది), హోస్ట్‌నేమ్, యూజర్‌నేమ్, వర్క్‌స్పేస్ పాత్, ఫైల్ కంటెంట్‌లు, మీ api_key, మీ ఇమెయిల్, ఏదైనా PII లేదా వర్క్‌స్పేస్-స్పెసిఫిక్ విషయాలు. వైర్ పేలోడ్ [`clawmetry/telemetry.py`](clawmetry/telemetry.py) లో ఆడిట్ చేయగలిగేది.

**ఆప్ట్ అవుట్** (వీటిలో ఏదైనా ఒకటి దాన్ని శాశ్వతంగా నిలిపివేస్తుంది):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

ఇక్కడ నెట్‌వర్క్ వైఫల్యం ఎప్పుడూ `clawmetry` ని నడపకుండా ఆపదు. పింగ్ 3 s టైమ్‌అవుట్‌తో డీమన్ థ్రెడ్‌పై ఫైర్-అండ్-ఫర్గెట్.

## స్టార్ చరిత్ర

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> చే నిర్మించబడింది · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> పర్యావరణ వ్యవస్థలో భాగం</sub>
</p>
