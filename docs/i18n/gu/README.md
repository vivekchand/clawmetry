<!-- i18n-src:48548997be76 -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**તમારા એજન્ટને વિચારતા જુઓ.** **12 AI એજન્ટ રનટાઇમ** માટે રિઅલ-ટાઇમ ઓબ્ઝર્વેબિલિટી: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex અને 8 વધુ. તમારા સમગ્ર એજન્ટ ફ્લીટ માટે એક ડેશબોર્ડ.

> 🌐 **આ ભાષામાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક આદેશ. શૂન્ય કોન્ફિગ. બધું આપોઆપ શોધે છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખુલે છે અને તમે તૈયાર છો.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 12 એજન્ટ રનટાઇમ સાથે કામ કરે છે

ClawMetry OpenClaw માટે ઓબ્ઝર્વેબિલિટી તરીકે શરૂ થયું, અને હવે એક ડેશબોર્ડમાં તમારો **સમગ્ર એજન્ટ ફ્લીટ** માપે છે, તમારી મશીન પર દરેક રનટાઇમ આપોઆપ શોધે છે:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw અને NemoClaw ઓપન-સોર્સ એપ્લિકેશનમાં મફત છે; બાકીના રનટાઇમ ClawMetry Cloud અથવા સ્વ-હોસ્ટ Pro લાઇસન્સ સાથે સક્રિય થાય છે. હેડરમાંથી રનટાઇમ બદલો અને દરેક ટૅબ — ખર્ચ, ટોકન, ટૂલ, ટ્રેસ — તે રનટાઇમ પ્રમાણે ફરીથી ગોઠવાઈ જાય છે.

## તમને શું મળે છે

- **Flow** — ચૅનલ, બ્રેઇન, ટૂલ અને પાછા આવતા સંદેશાઓ દર્શાવતો લાઇવ એનિમેટેડ ડાયાગ્રામ
- **Overview** — હેલ્થ ચૅક, પ્રવૃત્તિ હીટમૅપ, સેશન ગણતરી, મૉડેલ માહિતી
- **Usage** — દૈનિક/સાપ્તાહિક/માસિક વિભાજન સહિત ટોકન અને ખર્ચ ટ્રૅકિંગ
- **Sessions** — મૉડેલ, ટોકન, છેલ્લી પ્રવૃત્તિ સહિત સક્રિય એજન્ટ સેશન
- **Crons** — સ્ટૅટસ, આગળની રન, અવધિ સહિત શિડ્યૂલ્ડ જૉબ
- **Logs** — રંગ-કોડ કરેલ રિઅલ-ટાઇમ લૉગ સ્ટ્રીમિંગ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, દૈનિક નોંધ બ્રાઉઝ કરો
- **Transcripts** — સેશન ઇતિહાસ વાંચવા માટે ચૅટ-બબલ UI
- **Alerts** — બજેટ મર્યાદા, ભૂલ-દર ટ્રિગર, એજન્ટ-ઑફલાઇન શોધ; Slack, Discord, PagerDuty, Telegram, Email પર રૂટ થાય છે
- **Approvals** — વિનાશક ડિલીટ, ફોર્સ પુશ, DB મ્યૂટેશન, sudo, પૅકેજ ઇન્સ્ટૉલ, નેટવર્ક કૉલ એક-ક્લિક સ્વીકૃતિ પાછળ રોકો

## સ્ક્રીનશૉટ

### 🧠 Brain — લાઇવ એજન્ટ ઇવેન્ટ સ્ટ્રીમ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ટોકન ઉપયોગ અને સેશન સારાંશ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — રિઅલ-ટાઇમ ટૂલ કૉલ ફીડ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — મૉડેલ અને સેશન પ્રમાણે ખર્ચ વિભાજન
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — વર્કસ્પેસ ફાઇલ બ્રાઉઝર
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — પોસ્ચર અને ઓડિટ લૉગ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — બજેટ મર્યાદા, ભૂલ-દર ટ્રિગર, Slack / Discord / PagerDuty / Email પર વેબહૂક
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — જોખમી ટૂલ કૉલ મૅન્યુઅલ સ્વીકૃતિ પાછળ રોકો; નીતિ-આધારિત સુરક્ષા નિયમો
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## ઇન્સ્ટૉલ

**એક-લાઇન (ભલામણ કરેલ):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**સ્રોતમાંથી:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 ફ્રન્ટએન્ડ ડેવલપમેન્ટ

v2 React ઍપ `frontend/` માં રહે છે અને Flask સર્વર v2 સક્ષમ સાથે શરૂ થાય ત્યારે `/v2` પર પ્રસ્તુત થાય છે.

ડેવલપ કરતી વખતે બે ટર્મિનલ વાપરો:

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

`http://localhost:5173/v2/` ખોલો. Vite `/api` વિનંતીઓ `http://localhost:8900` પર પ્રૉક્સી કરે છે, જેથી React ઍપ વધારાના CORS સેટઅપ વિના સ્થાનિક Flask સર્વર સાથે વાત કરી શકે.

Python પૅકેજ સાથે શિપ થતો બૉડલ બિલ્ડ કરવા:

```bash
cd frontend
npm run build
```

પ્રૉડક્શન બૉડલ `clawmetry/static/v2/dist/` માં લખાય છે.

## રનટાઇમ / એજન્ટ સુસંગતતા

ClawMetry ઘણા AI-એજન્ટ રનટાઇમ નિહાળે છે, માત્ર OpenClaw નહીં. દરેક બિન-OpenClaw રનટાઇમ એક સમર્પિત રીડર ઍડૅપ્ટર સાથે આવે છે જે તેના મૂળ સેશન ફૉર્મૅટને ClawMetry ના એકીકૃત આકારોમાં રૂપાંતરિત કરે છે; ડીમોન તેમને રનટાઇમ સાથે ટૅગ કરીને તે જ DuckDB સ્ટોર અને ક્લાઉડ સ્નૅપશૉટમાં ઇન્જેસ્ટ કરે છે, અને Session replay ટૅબ **રનટાઇમ સ્વિચર** બતાવે છે જ્યારે એકથી વધુ હાજર હોય. સંપૂર્ણ મૅટ્રિક્સ અને રનટાઇમ ઉમેરવાની માર્ગદર્શિકા માટે [`docs/compatibility.md`](docs/compatibility.md) જુઓ, અને OpenClaw-ફૅમિલી પ્રાઇમર માટે [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) જુઓ.

| રનટાઇમ / એજન્ટ | સ્ટૅટસ | નોંધ |
|---|---|---|
| **OpenClaw** | Native | સંદર્ભ રનટાઇમ, આપોઆપ-શોધ |
| **PicoClaw** | Beta adapter | ફ્લૅટ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ટ્રાન્સ્ક્રિપ્ટ, મૉડેલ, ટૂલ કૉલ. |
| **NanoClaw** | Beta adapter | પ્રતિ-સેશન SQLite (`data/v2-sessions`). ટ્રાન્સ્ક્રિપ્ટ અને સંદેશ ગણતરી. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. ટ્રાન્સ્ક્રિપ્ટ, મૉડેલ, ટોકન/ખર્ચ. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. ટ્રાન્સ્ક્રિપ્ટ, મૉડેલ, ટૂલ કૉલ + વિચાર, ટોકન ઉપયોગ. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. ટ્રાન્સ્ક્રિપ્ટ, મૉડેલ, ટૂલ કૉલ, ટોકન ઉપયોગ. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. ચૅટ/કૉમ્પોઝર ટ્રાન્સ્ક્રિપ્ટ, મૉડેલ. |
| **Aider** | Beta adapter | દરેક પ્રૉજેક્ટ દીઠ `.aider.chat.history.md`. ટ્રાન્સ્ક્રિપ્ટ, મૉડેલ, ટોકન ગણતરી. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. ટ્રાન્સ્ક્રિપ્ટ, મૉડેલ, ટૂલ કૉલ, ટોકન કુલ. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. ટ્રાન્સ્ક્રિપ્ટ, મૉડેલ, ટૂલ કૉલ, ટોકન અને ખર્ચ. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. ટ્રાન્સ્ક્રિપ્ટ, મૉડેલ, ટૂલ કૉલ, ટોકન ઉપયોગ. |

"Beta adapter" એટલે ClawMetry તે રનટાઇમના વાસ્તવિક ઑન-ડિસ્ક ફૉર્મૅટ માટે રીડર સાથે આવે છે, દરેક વાસ્તવિक મશીન પર વાસ્તવિক ઇન્સ્ટૉલ સામે બિલ્ડ અને ચકાસાયેલ (જુઓ `tests/fixtures/runtimes/<rt>/`). ઍડૅપ્ટર માત્ર-વાંચવા-યોગ્ય છે; દરેક તેના રનટાઇમ ખરેખર શું સ્ટોર કરે છે તે વિશે પ્રામાણિક છે (દા.ત. PicoClaw/NanoClaw/Cursor ડિસ્ક પર ટોકન ખર્ચ લખતા નથી). જ્યારે ઘણા રનટાઇમ એક નોડ પર ચાલે છે, ત્યારે રનટાઇમ સ્વિચર સ્વચ્છ ઊંડા-ડાઇવ માટે સેશન વ્યૂ એકને સ્કોપ કરે છે.

## કોઈ પણ SDK એજન્ટ ટ્રૅક કરો — આઉટ-લૂપ ખર્ચ એટ્રિબ્યૂશન

ઉપરના રનટાઇમ બધા ડિસ્ક પર સેશન લખે છે. તમારો પોતાનો **પ્રૉડક્શન એજન્ટ** — જે તમે OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, અથવા સાદા `httpx` લૂપ પર બનાવ્યો છે — તેમ કરતો નથી. ClawMetry નો ઝીરો-કોન્ફિગ ઇન્ટરસેપ્ટર `httpx`/`requests` ને મૉન્કી-પૅચ કરીને તેના LLM કૉલ (ખર્ચ, ટોકન, લેટન્સી, ભૂલ) હજી કૅપ્ચર કરે છે:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (અથવા `CLAWMETRY_SOURCE=support-agent` env var) દરેક કૉલને **નામવાળા સ્રોત** સાથે ટૅગ કરે છે, જેથી તમે ચલાવો છો તે દરેક પ્રૉડક્ટ ડેશબોર્ડના Overview પરના **🔌 Out-loop sources** કાર્ડમાં પ્રતિ-એજન્ટ કૉલ, પ્રૉવાઇડર, લેટન્સી, ભૂલ દર સાથે પોતાની પ્રથમ-વર્ગ, ખર્ચ-એટ્રિબ્યૂટ-સક્ષમ લાઇન તરીકે દેખાય છે. કોઈ સ્રોત સેટ નથી? કૉલ હજી ટ્રૅક થાય છે; કાર્ડ ફક્ત છુપાયેલ રહે છે.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

આ તે જ ડેટા સ્તર છે જ્યાં રનટાઇમ ઍડૅપ્ટર ફીડ કરે છે (DuckDB → ક્લાઉડ સ્નૅપશૉટ), તેથી આઉટ-લૂપ સ્રોત ક્લાઉડ ડેશબોર્ડ સાથે બાકી બધી જેમ E2E-એન્ક્રિપ્ટેડ સિંક થાય છે.

## OpenTelemetry — વિક્રેતા-તટસ્થ, તમારા ટ્રેસ ગમે ત્યાં મોકલો

ClawMetry **GenAI સેમૅન્ટિક કન્વેન્શન** વાપરીને બંને દિશામાં **OpenTelemetry** બોલે છે, જેથી તમારા એજન્ટ ટ્રેસ ક્યારેય એક ટૂલ સાથે બંધ ન થાય.

**Export** — દરેક સેશન — LLM કૉલ, ટૂલ, સબ-એજન્ટ, ટોકન, ખર્ચ — OTLP/HTTP GenAI સ્પૅન તરીકે કોઈ પણ કલેક્ટર (Datadog, Grafana, Honeycomb, અથવા તમારો પોતાનો OTel Collector) પર:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ઑથ હેડર અને પૉલ ઇન્ટર્વૉલ વૈકલ્પિક env var છે:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** — બિલ્ટ-ઇન OTLP રિસીવર `/v1/traces` અને `/v1/metrics` પર બીજા ગમે ત્યાંથી ટ્રેસ અને મૅટ્રિક સ્વીકારે છે (`pip install clawmetry[otel]` protobuf ingest માટે).

તમને ઝીરો-કોન્ફિગ, લોકલ-ફર્સ્ટ ClawMetry ડેશબોર્ડ **અને** તમારી ટીમ પહેલાથી ચલાવે છે તે ગમે તે બૅકએન્ડ પર ડેટા મળે છે — કોઈ બંધ-ઉપાય નહીં, ઇન્સ્ટૉલ કરવા માટે બીજો એજન્ટ નહીં.

## કોન્ફિગ્યુરેશન

મોટા ભાગના લોકોને કોઈ કોન્ફિગ જોઈતી નથી. ClawMetry તમારો વર્કસ્પેસ, લૉગ, સેશન અને cron આપોઆપ શોધે છે.

જો તમારે કસ્ટમાઇઝ કરવાની જરૂર હોય:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

બધા વિકલ્પ: `clawmetry --help`

## સપૉર્ટ કરેલ ચૅનલ

ClawMetry તમારા OpenClaw ના દરેક ગોઠવેલ ચૅનલ માટે લાઇવ પ્રવૃત્તિ બતાવે છે. ફ્લો ડાયાગ્રામમાં ફક્ત તે ચૅનલ દેખાય છે જે ખરેખર તમારા `openclaw.json` માં ગોઠવેલ છે — ગોઠવ્યા વિનાના ચૅનલ આપોઆપ છુપાઈ જાય છે.

ઇનકમિંગ/આઉટગોઇંગ સંદેશ ગણતરી સાથે લાઇવ ચૅટ બબલ વ્યૂ જોવા Flow માં કોઈ પણ ચૅનલ નોડ ક્લિક કરો.

| ચૅનલ | સ્ટૅટસ | લાઇવ પૉપઅપ | નોંધ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | સંદેશ, સ્ટૅટ, 10s રિફ્રેશ |
| 💬 **iMessage** | ✅ Full | ✅ | `~/Library/Messages/chat.db` સીધું વાંચે છે |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) દ્વારા |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli દ્વારા |
| 🟣 **Discord** | ✅ Full | ✅ | Guild અને ચૅનલ શોધ |
| 🟪 **Slack** | ✅ Full | ✅ | Workspace અને ચૅનલ શોધ |
| 🌐 **Webchat** | ✅ Full | ✅ | બિલ્ટ-ઇન વેબ UI સેશન |
| 📡 **IRC** | ✅ Full | ✅ | ટર્મિનલ-સ્ટાઇલ બબલ UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API દ્વારા iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API વેબહૂક દ્વારા |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams bot plugin દ્વારા |
| 🔷 **Mattermost** | ✅ Full | ✅ | સ્વ-હોસ્ટ ટીમ ચૅટ |
| 🟩 **Matrix** | ✅ Full | ✅ | વિકેન્દ્રીભૂત, E2EE સપૉર્ટ |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | વિકેન્દ્રીભૂત NIP-04 DM |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC કનેક્શન દ્વારા ચૅટ |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket ઇવેન્ટ સબ્સ્ક્રિપ્શન |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **આપોઆપ-શોધ:** ClawMetry તમારો `~/.openclaw/openclaw.json` વાંચે છે અને ફક્ત તે ચૅનલ પ્રસ્તુત કરે છે જે તમે ખરેખર ગોઠવ્યા છે. કોઈ મૅન્યુઅલ સેટઅપ જરૂરી નથી.

## Docker ડિપ્લૉઇમેન્ટ

ClawMetry ને કન્ટેઇનરમાં ચલાવવો છે? કોઈ સમસ્યા નહીં! 🐳

**Docker સાથે ઝડપી શરૂઆત:**

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

**Docker Compose ઉદાહરણ:**

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

> **નોંધ:** Docker માં ચાલતી વખતે, ClawMetry આપોઆپ તમારો સેટઅપ શોધી શકે તે માટે તમારા એજન્ટના ડેટા અને લૉગ ડિરેક્ટ્રરી (દા.ત. `~/.openclaw`, `~/.claude`, `~/.codex`) માઉન્ટ કરો.

## જરૂરિયાત

- Python 3.8+
- Flask (pip દ્વારા આપોઆپ ઇન્સ્ટૉલ)
- તે જ મશીન પર AI એજન્ટ રનટાઇમ: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, અથવા PicoClaw (અથવા Docker માટે માઉન્ટ કરેલ વૉલ્યૂમ)
- Linux અથવા macOS

## NemoClaw / OpenShell સપૉર્ટ

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) આપોઆپ શોધે છે — NVIDIA નો OpenClaw માટેનો એન્ટરપ્રાઇઝ સિક્યૉરિટી રૅપર જે સૅન્ડબૉક્સ OpenShell કન્ટેઇનરમાં એજન્ટ ચલાવે છે.

મોટા ભાગના કિસ્સામાં કોઈ વધારાની ગોઠવણ જરૂरी નથી. sync ડીમોન સ્વ-શોધ કરે છે કે સેशन ફાઇલ હોસ્ટ પર `~/.openclaw/` માં છે કે OpenShell કન્ટેઇनरमाં.

### તે કેવી રીতે કામ કરે છે

ClawMetry NemoClaw ને બે રીતે શોધે છે:

1. **બાઇનરી શોધ** — `nemoclaw` CLI ના ચૅક અને સૅન્ડબૉક્સ માહિتي મેળવવા `nemoclaw status` ચલાવે છે
2. **કન્ટેઇनर शोध** — `openshell`, `nemoclaw`, અthvа `ghcr.io/nvidia/` ઇmejवाळा runting Docker कन्टेनर સ्कॅन કरे है, पछी volume माउन्ट या `docker cp` द्वारा सेशन वांचे है

NemoClaw कन्टेनरमাंथी sync करेला सेशन क्लाउड डेशबोर्डमा `runtime=nemoclaw` और `container_id` मेटाडेटा साथे टॅग थाय है, तेथी तमे तेमने एक नजरे सामान्य OpenClaw सेशनथी अलग पाडी शको.

### ভলামণ кरायेला सेटअप: HOST पर sync daemon

सर्वश्रेष्ठ अनुभव माते, ClawMetry नो sync daemon **host मशीन** पर चलावो (सॅन्डबॉक्स अन्दर नहीं). आ NemoClaw नेटवर्क पॉलिसी प्रतिबंध टाले है.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

sync daemon कोईपण running OpenShell कन्टेनर अन्दर सेशन आपोआप शोधशे.

### वैकल्पिक: स्पष्ट सॅन्डबॉक्स नाम

जो आपोआप-शोध काम न करे, तो ClawMetry ने योग्य सॅन्डबॉक्स तरफ दर्शावो:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### सॅन्डबॉक्स अन्दर चलावो (उन्नत)

जो तमारे OpenShell सॅन्डबॉक्स **अन्दर** sync daemon चलाववो पडे, तो ClawMetry ingest API सुधी पहोंची शके तेना माटे तमारी NemoClaw नेटवर्क पॉलिसीमां आ egress नियम उमेरो:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

आ साथे लागु करो:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### पोर्ट और एन्डपोइन्ट

| एन्डपोइन्ट | पोर्ट | प्रोटोकॉल | जरूरी |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | हा (sync daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | हा (स्थानिक डेशबोर्ड UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | कन्टेनर सेशन शोध माते |

sync daemon फक्त `ingest.clawmetry.com` ने बाहरी HTTPS कॉल करे है. कोईपण inbound पोर्ट जरूरी नथी.

---

## ক্লাউড ডিপ্ল৉ইমেন্ট

SSH ટૅনल, રિવर्स प्रॉक्सी और Docker माते **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** जुओ.

## परीक्षण

आ प्रोजेक्ट BrowserStack साथे परीक्षण थयेलो छे.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## टेलीमेट्री

ClawMetry पहेली वार नवी मशीन पर `clawmetry` CLI चलावो त्यारे `https://app.clawmetry.com/api/install` ने एकल अनामी "first run" ping मोकले छे. अमे आनो उपयोग इन्स्टॉल गणवा (OSS प्रोजेक्ट माटे आ एकमात्र मार्केटिंग मेट्रिक छे) और अमारा उपयोगकर्ताओए कया एजन्ट ফ্রেমওয়ার्क इन्स্टॉল कर्या छे ते जाणवा करीए छीए.

**प्रति इन्स्टॉल बिल्कुल एक POST**, जेमां:

| फील्ड | ઉदाहरण | कारण |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` पर संग्रहित random UUID | dedup; तमारी email या api_key साथे जोडेलो नथी |
| `version` | `0.12.167` | कया संस्करण प्रचलित छे |
| `os` / `os_version` | `Darwin` / `25.3.0` | प्लेटफॉर्म सपोर्ट प्राथमिकता |
| `python` | `3.11.15` | Python संस्करण सपोर्ट मेट्रिक्स |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | आगळा कया एजन्ट साथे एकीकृत करवा |
| `is_ci` / `ci_provider` | `true` / `github_actions` | मानव इन्स्टॉलने CI अवाजथी अलग करवा |

**अमे शुं नथी मोकलता**: IP (cloud सर्वर-साइड विनंतीमांथी देशनो कोड काढे छे, पछी IP काढी नाखे छे), hostname, username, workspace path, फाइल सामग्री, तमारी api_key, तमारी email, कोईपण PII या workspace-विशिष्ट माहिती. wire payload [`clawmetry/telemetry.py`](clawmetry/telemetry.py) मां ऑडिट करी शकाय छे.

**ऑप्ट आउट** (आमांथी कोईपण एक तेने कायमी अक्षम करे छे):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

अहीं नेटवर्क विफळता `clawmetry` ने चलतो रोकती नथी — ping 3 s timeout साथे daemon thread पर fire-and-forget छे.

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## लाइसन्स

MIT

---

<p align="center">
  <strong>🦞 तमारा एजन्टने विचारता जुओ</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> द्वारा बनावेलुं · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ઇकोसिस्टमनो भाग</sub>
</p>
