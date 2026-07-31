<!-- i18n-src:9a05336fbdc1 -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**તમારા એજન્ટને વિચારતું જુઓ.** **14 AI એજન્ટ રનટાઈમ્સ** માટે રિયલ-ટાઈમ ઓબ્ઝર્વેબિલિટી: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex અને બીજા 10. તમારા આખા એજન્ટ ફ્લીટ માટે એક જ ડેશબોર્ડ.

> 🌐 **આ ભાષામાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. ઝીરો કન્ફિગ. બધું ઓટો-ડિટેક્ટ થાય છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે અને તમારું કામ પૂરું.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 એજન્ટ રનટાઈમ્સ સાથે કામ કરે છે

ClawMetry ની શરૂઆત OpenClaw માટેની ઓબ્ઝર્વેબિલિટી તરીકે થઈ હતી, અને હવે તે તમારા **સમગ્ર એજન્ટ ફ્લીટ**ને એક જ ડેશબોર્ડમાં માપે છે, તમારા મશીન પર દરેક રનટાઈમને ઓટો-ડિટેક્ટ કરીને:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw અને NemoClaw ઓપન-સોર્સ એપમાં મફત છે; બાકીના રનટાઈમ્સ ClawMetry Cloud અથવા સેલ્ફ-હોસ્ટેડ Pro લાયસન્સ સાથે સક્રિય થાય છે. હેડરમાંથી રનટાઈમ બદલો અને દરેક ટેબ, કોસ્ટ, ટોકન્સ, ટૂલ્સ, ટ્રેસ, તે રનટાઈમ પ્રમાણે ફરીથી સ્કોપ થાય છે. ચોક્કસ ફ્રી/પેઇડ વિભાજન, ટિયર મેટ્રિક્સ, `/api/entitlement` શેપ, અને `clawmetry license` CLI માટે **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** જુઓ.

## તમને શું મળે છે

- **Flow** — ચેનલ્સ, બ્રેઇન, ટૂલ્સ અને પાછા દ્વારા વહેતા મેસેજીસ બતાવતું લાઇવ એનિમેટેડ ડાયાગ્રામ
- **Overview** — હેલ્થ ચેક્સ, એક્ટિવિટી હીટમેપ, સેશન કાઉન્ટ્સ, મોડેલ ઇન્ફો
- **Usage** — દૈનિક/સાપ્તાહિક/માસિક બ્રેકડાઉન સાથે ટોકન અને કોસ્ટ ટ્રેકિંગ
- **Sessions** — મોડેલ, ટોકન્સ, છેલ્લી પ્રવૃત્તિ સાથે સક્રિય એજન્ટ સેશન્સ
- **Crons** — સ્ટેટસ, નેક્સ્ટ રન, ડ્યુરેશન સાથે શેડ્યુલ્ડ જોબ્સ
- **Logs** — કલર-કોડેડ રિયલ-ટાઈમ લોગ સ્ટ્રીમિંગ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ડેઈલી નોટ્સ બ્રાઉઝ કરો
- **Transcripts** — સેશન હિસ્ટ્રી વાંચવા માટે ચેટ-બબલ UI
- **Alerts** — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, એજન્ટ-ઓફલાઇન ડિટેક્શન; Slack, Discord, PagerDuty, Telegram, Email પર રૂટ કરે છે
- **Approvals** — વિનાશક ડિલીટ્સ, ફોર્સ પુશીસ, DB મ્યુટેશન્સ, sudo, પેકેજ ઇન્સ્ટોલ્સ, નેટવર્ક કોલ્સને એક-ક્લિક સાઇન-ઓફ પાછળ ગેટ કરો

## સ્ક્રીનશોટ્સ

### 🧠 Brain — લાઇવ એજન્ટ ઇવેન્ટ સ્ટ્રીમ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ટોકન ઉપયોગ અને સેશન સારાંશ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — રિયલ-ટાઈમ ટૂલ કોલ ફીડ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — મોડેલ અને સેશન પ્રમાણે કોસ્ટ બ્રેકડાઉન
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — વર્કસ્પેસ ફાઇલ બ્રાઉઝર
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — સ્થિતિ અને ઓડિટ લોગ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, Slack / Discord / PagerDuty / Email ને વેબહુક્સ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — જોખમી ટૂલ કોલ્સને મેન્યુઅલ સાઇન-ઓફ પાછળ ગેટ કરો; પોલિસી-બેક્ડ પ્રોટેક્શન નિયમો
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code માટે પ્રી-એક્ઝિક્યુશન બ્લોકિંગ** — એક કમાન્ડ એક
PreToolUse હૂક ઇન્સ્ટોલ કરે છે જે મેચિંગ ટૂલ કોલ્સને એ ચાલે તે *પહેલાં*
અટકાવે છે અને તમારા નિર્ણયની રાહ જુએ છે (તમારા ફોન પરથી એક ટેપમાં જો
[cloud push notifications](https://app.clawmetry.com/push) સક્ષમ હોય તો):

```bash
clawmetry hooks install     # ~/.claude/settings.json લખે છે (idempotent)
clawmetry hooks status      # શું વાયર્ડ છે + કેટલી પોલિસીસ સક્રિય છે
clawmetry hooks uninstall   # ફક્ત ClawMetry ની એન્ટ્રીઓ દૂર કરે છે
```

એક ડિનાય ફક્ત તે એક ટૂલ કોલને બ્લોક કરે છે — એજન્ટ પોતાનું સેશન જાળવી
રાખે છે અને બીજો અભિગમ અજમાવી શકે છે. તમારા ફોન પર મંજૂરી આપવાથી Claude
Code ની પોતાની પરમિશન પ્રોમ્પ્ટ સ્કિપ થાય છે (તમે પહેલેથી જવાબ આપી
દીધો છે). અનમેચ્ડ ટૂલ્સનો ખર્ચ ~40ms આવે છે અને એ Claude Code ના
સામાન્ય પરમિશન ફ્લોમાં પાછા જાય છે. જ્યારે Claude Code પોતે તમારી
રાહ જોઈ રહ્યું હોય (`permission_prompt` / `idle_prompt` નોટિફિકેશન્સ)
ત્યારે પણ તમને ફોન પુશ મળે છે.

## ઇન્સ્ટોલ

**વન-લાઇનર (ભલામણ કરેલ):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**સોર્સમાંથી:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 ફ્રન્ટએન્ડ ડેવલપમેન્ટ

v2 React એપ `frontend/` માં રહે છે અને જ્યારે Flask સર્વર v2 સક્ષમ
સાથે શરૂ થાય ત્યારે `/v2` પર સર્વ થાય છે.

ડેવલપ કરતી વખતે બે ટર્મિનલનો ઉપયોગ કરો:

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

`http://localhost:5173/v2/` ખોલો. Vite `/api` વિનંતીઓને
`http://localhost:8900` પર પ્રોક્સી કરે છે, જેથી React એપ વધારાના
CORS સેટઅપ વગર લોકલ Flask સર્વર સાથે વાત કરી શકે.

Python પેકેજ સાથે શિપ થતું બંડલ બનાવવા માટે:

```bash
cd frontend
npm run build
```

પ્રોડક્શન બંડલ `clawmetry/static/v2/dist/` માં લખાય છે.

## રનટાઈમ / એજન્ટ સુસંગતતા

ClawMetry ફક્ત OpenClaw જ નહીં, બીજા ઘણા AI-એજન્ટ રનટાઈમ્સનું અવલોકન
કરે છે. દરેક નોન-OpenClaw રનટાઈમ એક ડેડિકેટેડ રીડર એડેપ્ટર શિપ કરે છે
જે એના નેટિવ સેશન ફોર્મેટને ClawMetry ના યુનિફાઇડ શેપ્સમાં ટ્રાન્સલેટ
કરે છે; ડિમન એમને એ જ DuckDB સ્ટોર + ક્લાઉડ સ્નેપશોટમાં ઇન્જેસ્ટ કરે
છે, રનટાઈમ સાથે ટેગ કરીને, અને જ્યારે એકથી વધુ હાજર હોય ત્યારે Session
replay ટેબ એક **રનટાઈમ સ્વિચર** બતાવે છે. પૂરું મેટ્રિક્સ + રનટાઈમ્સ
ઉમેરવાની ગાઇડ માટે [`docs/compatibility.md`](docs/compatibility.md)
અને OpenClaw-ફેમિલી પ્રાઈમર માટે [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) જુઓ.

| રનટાઈમ / એજન્ટ | સ્ટેટસ | નોંધ |
|---|---|---|
| **OpenClaw** | નેટિવ | રેફરન્સ રનટાઈમ, ઓટો-ડિટેક્ટેડ |
| **PicoClaw** | બીટા એડેપ્ટર | ફ્લેટ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કોલ્સ. |
| **NanoClaw** | બીટા એડેપ્ટર | પર-સેશન SQLite (`data/v2-sessions`). ટ્રાન્સક્રિપ્ટ્સ + મેસેજ કાઉન્ટ્સ. |
| **Hermes** | બીટા એડેપ્ટર | SQLite `~/.hermes/state.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટોકન્સ/કોસ્ટ. |
| **Claude Code** | બીટા એડેપ્ટર | JSONL `~/.claude/projects/.../<id>.jsonl`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કોલ્સ + થિંકિંગ, ટોકન વપરાશ. |
| **Codex** | બીટા એડેપ્ટર | રોલઆઉટ JSONL `~/.codex/sessions/...`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કોલ્સ, ટોકન વપરાશ. |
| **Cursor** | બીટા એડેપ્ટર | SQLite `state.vscdb`. ચેટ/કંપોઝર ટ્રાન્સક્રિપ્ટ્સ, મોડેલ. |
| **Aider** | બીટા એડેપ્ટર | પ્રોજેક્ટ દીઠ `.aider.chat.history.md`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટોકન કાઉન્ટ્સ. |
| **Goose** | બીટા એડેપ્ટર | SQLite `~/.local/share/goose`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કોલ્સ, ટોકન ટોટલ્સ. |
| **opencode** | બીટા એડેપ્ટર | SQLite `~/.local/share/opencode`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કોલ્સ, ટોકન્સ + કોસ્ટ. |
| **Qwen Code** | બીટા એડેપ્ટર | JSONL `~/.qwen/projects/.../chats`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કોલ્સ, ટોકન વપરાશ. |
| **Pi** | બીટા એડેપ્ટર | JSONL `~/.pi/agent/sessions`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કોલ્સ, ટોકન્સ + કોસ્ટ. |
| **Deep Agents** | બીટા એડેપ્ટર | SQLite `~/.deepagents/.state/sessions.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કોલ્સ, ટોકન્સ + કોસ્ટ. |
| **n8n** | બીટા એડેપ્ટર | SQLite `~/.n8n/database.sqlite`. વર્કફ્લો એક્ઝિક્યુશન્સ, નોડ રન્સ, AI Agent પ્રોમ્પ્ટ્સ, જ્યાં n8n રેકોર્ડ કરે ત્યાં મોડેલ + ટોકન્સ. |

"બીટા એડેપ્ટર" નો અર્થ છે કે ClawMetry એ રનટાઈમના વાસ્તવિક ઓન-ડિસ્ક
ફોર્મેટ માટે એક રીડર શિપ કરે છે, દરેક વાસ્તવિક મશીન પર વાસ્તવિક
ઇન્સ્ટોલ સામે બનાવેલ + ચકાસેલ (જુઓ `tests/fixtures/runtimes/<rt>/`).
એડેપ્ટર્સ રીડ-ઓન્લી છે; દરેક એના રનટાઈમ ખરેખર શું સ્ટોર કરે છે એ
વિશે પ્રામાણિક છે (દા.ત. PicoClaw/NanoClaw/Cursor ટોકન કોસ્ટ ડિસ્ક
પર લખતા નથી). જ્યારે એક નોડ પર ઘણા રનટાઈમ્સ ચાલે છે, ત્યારે રનટાઈમ
સ્વિચર સેશન્સ વ્યુને એક પર સ્કોપ કરે છે જેથી ડીપ-ડાઈવ સ્પષ્ટ રહે.

## કોઈપણ SDK એજન્ટને ટ્રેક કરો — આઉટ-લૂપ કોસ્ટ એટ્રિબ્યુશન

ઉપરના રનટાઈમ્સ બધા સેશન્સને ડિસ્ક પર લખે છે. તમારો પોતાનો
**પ્રોડક્શન એજન્ટ** — જે તમે OpenAI Agents SDK, LangChain, Vercel AI
SDK, LlamaIndex, E2B, અથવા સાદા `httpx` લૂપ પર બનાવ્યો છે — એવું
કરતો નથી. ClawMetry નું ઝીરો-કન્ફિગ ઇન્ટરસેપ્ટર તોય એના LLM કોલ્સ
(કોસ્ટ, ટોકન્સ, લેટન્સી, એરર્સ) `httpx`/`requests` ને મંકી-પેચ કરીને
કેપ્ચર કરે છે:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (અથવા `CLAWMETRY_SOURCE=support-agent` env var) દરેક
કોલને એક **નામાંકિત સોર્સ** સાથે ટેગ કરે છે, જેથી તમે ચલાવો છો દરેક
પ્રોડક્ટ ડેશબોર્ડના Overview પરના **🔌 Out-loop sources** કાર્ડમાં
પોતાની એક ફર્સ્ટ-ક્લાસ, કોસ્ટ-એટ્રિબ્યુટેબલ લાઈન તરીકે દેખાય છે —
દરેક એજન્ટ પ્રમાણે કોલ્સ, પ્રોવાઇડર્સ, લેટન્સી, એરર રેટ. કોઈ સોર્સ
સેટ ન કર્યો? કોલ્સ તોય ટ્રેક થાય છે; કાર્ડ ફક્ત છુપાયેલું રહે છે.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

આ એ જ ડેટા લેયર છે જે રનટાઈમ એડેપ્ટર્સ ફીડ કરે છે (DuckDB → ક્લાઉડ
સ્નેપશોટ), તેથી આઉટ-લૂપ સોર્સીસ બાકીની બધી બાબતોની જેમ ક્લાઉડ
ડેશબોર્ડ સાથે સિંક થાય છે, E2E-એન્ક્રિપ્ટેડ.

## OpenTelemetry — વેન્ડર-ન્યુટ્રલ, તમારા ટ્રેસ ગમે ત્યાં મોકલો

ClawMetry બંને દિશામાં **OpenTelemetry** બોલે છે, **GenAI સિમેન્ટિક
કન્વેન્શન્સ** વાપરીને, જેથી તમારા એજન્ટ ટ્રેસ ક્યારેય એક ટૂલમાં
લોક ન થાય.

દરેક સેશન — LLM કોલ્સ, ટૂલ્સ, સબ-એજન્ટ્સ, ટોકન્સ, કોસ્ટ — **એક્સપોર્ટ**
કરો OTLP/HTTP GenAI સ્પાન્સ તરીકે કોઈપણ કલેક્ટરને (Datadog, Grafana,
Honeycomb, અથવા તમારો પોતાનો OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ઓથ હેડર્સ અને પોલ ઇન્ટરવલ વૈકલ્પિક env vars છે:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ઇન્જેસ્ટ** — બિલ્ટ-ઇન OTLP રિસીવર `/v1/traces` અને `/v1/metrics` પર
બીજા બધામાંથી ટ્રેસ અને મેટ્રિક્સ સ્વીકારે છે (protobuf ઇન્જેસ્ટ માટે
`pip install clawmetry[otel]`).

તમને ઝીરો-કન્ફિગ, લોકલ-ફર્સ્ટ ClawMetry ડેશબોર્ડ **અને** તમારી ટીમ
પહેલેથી ચલાવે છે એ ગમે તે બેકએન્ડમાં તમારો ડેટા મળે છે — કોઈ લોક-ઇન
નહીં, ઇન્સ્ટોલ કરવા માટે બીજું એજન્ટ નહીં.

## કન્ફિગરેશન

મોટા ભાગના લોકોને કોઈ કન્ફિગની જરૂર નથી. ClawMetry તમારું વર્કસ્પેસ,
લોગ્સ, સેશન્સ અને ક્રોન્સ ઓટો-ડિટેક્ટ કરે છે.

જો તમારે કસ્ટમાઇઝ કરવાની જરૂર હોય:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

બધા વિકલ્પો: `clawmetry --help`

## સપોર્ટેડ ચેનલ્સ

ClawMetry તમે કન્ફિગર કરેલા દરેક OpenClaw ચેનલ માટે લાઇવ પ્રવૃત્તિ
બતાવે છે. ફક્ત તમારા `openclaw.json` માં ખરેખર સેટ કરેલી ચેનલ્સ જ
Flow ડાયાગ્રામમાં દેખાય છે — કન્ફિગર ન કરેલી ચેનલ્સ ઓટોમેટિકલી
છુપાયેલી રહે છે.

Flow માં કોઈપણ ચેનલ નોડ ક્લિક કરીને ઇનકમિંગ/આઉટગોઇંગ મેસેજ કાઉન્ટ્સ
સાથે લાઇવ ચેટ બબલ વ્યુ જુઓ.

| ચેનલ | સ્ટેટસ | લાઇવ પોપઅપ | નોંધ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ પૂર્ણ | ✅ | મેસેજીસ, સ્ટેટ્સ, 10s રિફ્રેશ |
| 💬 **iMessage** | ✅ પૂર્ણ | ✅ | `~/Library/Messages/chat.db` સીધું વાંચે છે |
| 💚 **WhatsApp** | ✅ પૂર્ણ | ✅ | WhatsApp Web (Baileys) મારફતે |
| 🔵 **Signal** | ✅ પૂર્ણ | ✅ | signal-cli મારફતે |
| 🟣 **Discord** | ✅ પૂર્ણ | ✅ | ગિલ્ડ + ચેનલ ડિટેક્શન |
| 🟪 **Slack** | ✅ પૂર્ણ | ✅ | વર્કસ્પેસ + ચેનલ ડિટેક્શન |
| 🌐 **Webchat** | ✅ પૂર્ણ | ✅ | બિલ્ટ-ઇન વેબ UI સેશન્સ |
| 📡 **IRC** | ✅ પૂર્ણ | ✅ | ટર્મિનલ-સ્ટાઈલ બબલ UI |
| 🍏 **BlueBubbles** | ✅ પૂર્ણ | ✅ | BlueBubbles REST API મારફતે iMessage |
| 🔵 **Google Chat** | ✅ પૂર્ણ | ✅ | Chat API વેબહુક્સ મારફતે |
| 🟣 **MS Teams** | ✅ પૂર્ણ | ✅ | Teams બોટ પ્લગઇન મારફતે |
| 🔷 **Mattermost** | ✅ પૂર્ણ | ✅ | સેલ્ફ-હોસ્ટેડ ટીમ ચેટ |
| 🟩 **Matrix** | ✅ પૂર્ણ | ✅ | ડિસેન્ટ્રલાઇઝ્ડ, E2EE સપોર્ટ |
| 🟢 **LINE** | ✅ પૂર્ણ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ પૂર્ણ | ✅ | ડિસેન્ટ્રલાઇઝ્ડ NIP-04 DMs |
| 🟣 **Twitch** | ✅ પૂર્ણ | ✅ | IRC કનેક્શન મારફતે ચેટ |
| 🔷 **Feishu/Lark** | ✅ પૂર્ણ | ✅ | WebSocket ઇવેન્ટ સબસ્ક્રિપ્શન |
| 🔵 **Zalo** | ✅ પૂર્ણ | ✅ | Zalo Bot API |

> **ઓટો-ડિટેક્શન:** ClawMetry તમારો `~/.openclaw/openclaw.json` વાંચે
> છે અને ફક્ત તમે ખરેખર કન્ફિગર કરેલી ચેનલ્સ જ રેન્ડર કરે છે. કોઈ
> મેન્યુઅલ સેટઅપની જરૂર નથી.

## Docker ડિપ્લોયમેન્ટ

ClawMetry ને કન્ટેનરમાં ચલાવવું છે? કોઈ સમસ્યા નથી! 🐳

**Docker સાથે ક્વિક સ્ટાર્ટ:**

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

> **નોંધ:** Docker માં ચલાવતી વખતે, તમારા એજન્ટની ડેટા + લોગ
> ડિરેક્ટરીઓ (દા.ત. `~/.openclaw`, `~/.claude`, `~/.codex`) માઉન્ટ
> કરો જેથી ClawMetry તમારું સેટઅપ ઓટો-ડિટેક્ટ કરી શકે.

## જરૂરિયાતો

- Python 3.8+
- Flask (pip મારફતે ઓટોમેટિકલી ઇન્સ્ટોલ થાય છે)
- એ જ મશીન પર એક AI એજન્ટ રનટાઈમ: OpenClaw, NVIDIA NemoClaw, Claude
  Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider,
  NanoClaw, PicoClaw, Pi, Deep Agents, અથવા n8n (અથવા Docker માટે
  માઉન્ટેડ વોલ્યુમ્સ)
- Linux અથવા macOS

## NemoClaw / OpenShell સપોર્ટ

ClawMetry ઓટોમેટિકલી [NemoClaw](https://github.com/NVIDIA/NemoClaw)
ડિટેક્ટ કરે છે — NVIDIA નું એન્ટરપ્રાઈઝ સિક્યુરિટી રેપર જે
OpenClaw માટે એજન્ટ્સને સેન્ડબોક્સ્ડ OpenShell કન્ટેનર્સની અંદર
ચલાવે છે.

મોટા ભાગના કિસ્સાઓમાં કોઈ વધારાના કન્ફિગરેશનની જરૂર નથી. સિંક ડિમન
ઓટો-ડિસ્કવર કરે છે સેશન ફાઇલ્સ ભલે એ હોસ્ટ પર `~/.openclaw/` માં
હોય કે OpenShell કન્ટેનરની અંદર.

### આ કેવી રીતે કામ કરે છે

ClawMetry બે રીતે NemoClaw ડિટેક્ટ કરે છે:

1. **બાઈનરી ડિટેક્શન** — `nemoclaw` CLI ચેક કરે છે અને સેન્ડબોક્સ
   ઇન્ફો મેળવવા `nemoclaw status` ચલાવે છે
2. **કન્ટેનર ડિટેક્શન** — `openshell`, `nemoclaw`, અથવા
   `ghcr.io/nvidia/` ઇમેજીસ માટે ચાલી રહેલા Docker કન્ટેનર્સ સ્કેન
   કરે છે, પછી વોલ્યુમ માઉન્ટ્સ અથવા `docker cp` મારફતે સેશન્સ વાંચે
   છે

NemoClaw કન્ટેનર્સમાંથી સિંક કરેલી સેશન ફાઇલ્સને ક્લાઉડ ડેશબોર્ડમાં
`runtime=nemoclaw` અને `container_id` મેટાડેટા સાથે ટેગ કરવામાં આવે
છે, જેથી તમે એમને એક નજરમાં સ્ટાન્ડર્ડ OpenClaw સેશન્સથી અલગ ઓળખી
શકો.

### ભલામણ કરેલ સેટઅપ: HOST પર સિંક ડિમન

શ્રેષ્ઠ અનુભવ માટે, ClawMetry ના સિંક ડિમનને **હોસ્ટ મશીન** પર ચલાવો
(સેન્ડબોક્સની અંદર નહીં). આ NemoClaw નેટવર્ક પોલિસી પ્રતિબંધોને
ટાળે છે.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

સિંક ડિમન ઓટોમેટિકલી કોઈપણ ચાલી રહેલા OpenShell કન્ટેનર્સની અંદર
સેશન્સ શોધી લેશે.

### વૈકલ્પિક: સ્પષ્ટ સેન્ડબોક્સ નામ

જો ઓટો-ડિટેક્શન કામ ન કરે, તો ClawMetry ને યોગ્ય સેન્ડબોક્સ તરફ
પોઈન્ટ કરો:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### સેન્ડબોક્સની અંદર ચલાવવું (એડવાન્સ્ડ)

જો તમારે સિંક ડિમન OpenShell સેન્ડબોક્સની **અંદર** ચલાવવો જ પડે, તો
તમારી NemoClaw નેટવર્ક પોલિસીમાં આ egress નિયમ ઉમેરો જેથી એ
ClawMetry ingest API સુધી પહોંચી શકે:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

આ સાથે લાગુ કરો:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### પોર્ટ્સ અને એન્ડપોઈન્ટ્સ

| એન્ડપોઈન્ટ | પોર્ટ | પ્રોટોકોલ | જરૂરી |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | હા (સિંક ડિમન → ક્લાઉડ) |
| `localhost:8900` | 8900 | HTTP | હા (લોકલ ડેશબોર્ડ UI) |
| Docker સોકેટ (`/var/run/docker.sock`) | — | Unix socket | કન્ટેનર સેશન ડિસ્કવરી માટે |

સિંક ડિમન ફક્ત `ingest.clawmetry.com` તરફ આઉટબાઉન્ડ HTTPS કોલ્સ
કરે છે. કોઈ ઇનબાઉન્ડ પોર્ટ્સની જરૂર નથી.

---

## ક્લાઉડ ડિપ્લોયમેન્ટ

SSH ટનલ્સ, રિવર્સ પ્રોક્સી, અને Docker માટે **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** જુઓ.

## ટેસ્ટિંગ

આ પ્રોજેક્ટ BrowserStack સાથે ટેસ્ટ કરવામાં આવે છે.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ટેલિમેટ્રી

ClawMetry તમારા મશીન પર પહેલી વાર `clawmetry` CLI ચલાવો ત્યારે
`https://app.clawmetry.com/api/install` પર એક જ અનામી "ફર્સ્ટ રન"
પિંગ મોકલે છે. અમે આનો ઉપયોગ ઇન્સ્ટોલ ગણવા માટે કરીએ છીએ (OSS
પ્રોજેક્ટ માટે અમારી પાસે એકમાત્ર માર્કેટિંગ મેટ્રિક છે) અને એ
જાણવા માટે કે અમારા યુઝર્સે કયા એજન્ટ ફ્રેમવર્ક ઇન્સ્ટોલ કરેલા છે.

**ઇન્સ્ટોલ દીઠ બરાબર એક POST**, જેમાં આ સમાવેશ થાય છે:

| ફિલ્ડ | ઉદાહરણ | કારણ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` પર સંગ્રહિત રેન્ડમ UUID | ડિડુપ; તમારા ઈમેલ કે api_key સાથે લિંક્ડ નથી |
| `version` | `0.12.167` | કઈ વર્ઝન્સ ઉપયોગમાં છે |
| `os` / `os_version` | `Darwin` / `25.3.0` | પ્લેટફોર્મ સપોર્ટ પ્રાયોરિટીઝ |
| `python` | `3.11.15` | Python વર્ઝન સપોર્ટ મેટ્રિક્સ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | અમારે આગળ કયા એજન્ટ્સ સાથે ઇન્ટિગ્રેટ કરવું જોઈએ |
| `is_ci` / `ci_provider` | `true` / `github_actions` | માનવ ઇન્સ્ટોલ્સને CI નોઈઝથી અલગ કરવા |

**અમે શું નથી મોકલતા**: IP (ક્લાઉડ સર્વર-સાઈડ પર વિનંતીમાંથી કન્ટ્રી
કોડ મેળવે છે, પછી IP ડિસ્કાર્ડ કરે છે), હોસ્ટનેમ, યુઝરનેમ, વર્કસ્પેસ
પાથ, ફાઇલ કન્ટેન્ટ, તમારો api_key, તમારો ઈમેલ, કંઈપણ PII અથવા
વર્કસ્પેસ-સ્પેસિફિક. વાયર પેલોડ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) માં ઓડિટેબલ છે.

**ઓપ્ટ આઉટ** (આમાંથી કોઈ પણ એક એને કાયમ માટે નિષ્ક્રિય કરે છે):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

નેટવર્ક નિષ્ફળતા અહીં `clawmetry` ને ચાલવાથી ક્યારેય રોકતી નથી —
પિંગ ડિમન થ્રેડ પર 3s ટાઈમઆઉટ સાથે ફાયર-એન્ડ-ફર્ગેટ છે.

## સ્ટાર હિસ્ટ્રી

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## લાયસન્સ

MIT

---

<p align="center">
  <strong>🦞 તમારા એજન્ટને વિચારતું જુઓ</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
