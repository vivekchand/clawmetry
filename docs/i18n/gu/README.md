<!-- i18n-src:bab48eec552f -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**તમારા એજન્ટને વિચારતું જુઓ.** **14 AI એજન્ટ રનટાઈમ્સ** માટે રિયલ-ટાઈમ ઓબ્ઝર્વેબિલિટી: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex અને બીજા 10. તમારા આખા એજન્ટ ફ્લીટ માટે એક જ ડેશબોર્ડ.

> 🌐 **આને આ ભાષામાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. શૂન્ય કન્ફિગ. બધું જાતે જ ડિટેક્ટ થાય છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે અને તમારું કામ પૂરું.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 એજન્ટ રનટાઈમ્સ સાથે કામ કરે છે

ClawMetry ની શરૂઆત OpenClaw માટેની ઓબ્ઝર્વેબિલિટી તરીકે થઈ હતી, અને હવે તે તમારા **આખા એજન્ટ ફ્લીટ**ને એક જ ડેશબોર્ડમાં માપે છે, તમારા મશીન પરના દરેક રનટાઈમને જાતે ડિટેક્ટ કરીને:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw અને NemoClaw ઓપન-સોર્સ એપમાં મફત છે; બાકીના રનટાઈમ્સ ClawMetry Cloud અથવા સેલ્ફ-હોસ્ટેડ Pro લાયસન્સ સાથે સક્રિય થાય છે. હેડરમાંથી રનટાઈમ બદલો અને દરેક ટેબ, ખર્ચ, ટોકન્સ, ટૂલ્સ, ટ્રેસ, તે રનટાઈમ પ્રમાણે ફરીથી ગોઠવાય છે. ચોક્કસ મફત/પેઈડ વિભાજન, ટિયર મેટ્રિક્સ, `/api/entitlement` નું સ્વરૂપ, અને `clawmetry license` CLI માટે **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** જુઓ.

## તમને શું મળે છે

- **Flow** — ચેનલો, બ્રેન, ટૂલ્સ, અને પાછા થઈને પસાર થતા મેસેજ બતાવતું લાઈવ એનિમેટેડ ડાયાગ્રામ
- **Overview** — હેલ્થ ચેક્સ, એક્ટિવિટી હીટમેપ, સેશન કાઉન્ટ્સ, મોડલ માહિતી
- **Usage** — રોજિંદા/સાપ્તાહિક/માસિક બ્રેકડાઉન સાથે ટોકન અને ખર્ચ ટ્રેકિંગ
- **Sessions** — મોડલ, ટોકન્સ, છેલ્લી પ્રવૃત્તિ સાથે સક્રિય એજન્ટ સેશન્સ
- **Crons** — સ્ટેટસ, નેક્સ્ટ રન, ડ્યુરેશન સાથે શેડ્યુલ થયેલા જોબ્સ
- **Logs** — કલર-કોડેડ રિયલ-ટાઈમ લોગ સ્ટ્રીમિંગ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, દૈનિક નોંધો બ્રાઉઝ કરો
- **Transcripts** — સેશન હિસ્ટ્રી વાંચવા માટે ચેટ-બબલ UI
- **Alerts** — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, એજન્ટ-ઓફલાઈન ડિટેક્શન; Slack, Discord, PagerDuty, Telegram, Email પર રૂટ થાય છે
- **Approvals** — વિનાશક ડિલીટ્સ, ફોર્સ પુશ, DB મ્યુટેશન્સ, sudo, પેકેજ ઈન્સ્ટોલ્સ, નેટવર્ક કોલ્સને એક-ક્લિક સાઈન-ઓફ પાછળ ગેટ કરો

## સ્ક્રીનશોટ્સ

### 🧠 Brain — લાઈવ એજન્ટ ઈવેન્ટ સ્ટ્રીમ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ટોકન વપરાશ અને સેશન સારાંશ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — રિયલ-ટાઈમ ટૂલ કોલ ફીડ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — મોડલ અને સેશન પ્રમાણે ખર્ચનું બ્રેકડાઉન
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — વર્કસ્પેસ ફાઈલ બ્રાઉઝર
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — સ્થિતિ અને ઓડિટ લોગ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, Slack / Discord / PagerDuty / Email પર વેબહૂક્સ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — જોખમી ટૂલ કોલ્સને મેન્યુઅલ સાઈન-ઓફ પાછળ ગેટ કરો; પોલિસી-બેક્ડ પ્રોટેક્શન નિયમો
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code માટે પ્રી-એક્ઝિક્યુશન બ્લોકિંગ** — એક કમાન્ડ એક PreToolUse
હૂક ઈન્સ્ટોલ કરે છે જે મેચ થતા ટૂલ કોલ્સને ચાલવા *પહેલાં* થોભાવે છે અને તમારા
નિર્ણયની રાહ જુએ છે (તમારા ફોનથી એક ટેપમાં
[ક્લાઉડ પુશ નોટિફિકેશન્સ](https://app.clawmetry.com/push) સક્રિય હોય ત્યારે):

```bash
clawmetry hooks install     # ~/.claude/settings.json લખે છે (idempotent)
clawmetry hooks status      # શું જોડાયેલું છે + કેટલી પોલિસીઓ સક્રિય છે
clawmetry hooks uninstall   # ફક્ત ClawMetry ની એન્ટ્રીઓ દૂર કરે છે
```

એક ડિનાય ફક્ત તે એક ટૂલ કોલને બ્લોક કરે છે, એજન્ટ પોતાનું સેશન જાળવી રાખે છે અને
બીજો અભિગમ અજમાવી શકે છે. તમારા ફોન પર મંજૂરી આપવાથી Claude Code ના પોતાના
પરમિશન પ્રોમ્પ્ટને છોડી દેવાય છે (તમે પહેલેથી જ જવાબ આપી દીધો છે). ન મેચ થતા ટૂલ્સનો
ખર્ચ ~40ms છે અને તે Claude Code ના સામાન્ય પરમિશન ફ્લોમાં પડી જાય છે. જ્યારે
Claude Code પોતે તમારી રાહ જોતું હોય ત્યારે પણ તમને ફોન પુશ મળે છે
(`permission_prompt` / `idle_prompt` નોટિફિકેશન્સ).

## ઈન્સ્ટોલ

**વન-લાઈનર (ભલામણ કરેલ):**
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

v2 React એપ `frontend/` માં રહે છે અને જ્યારે Flask
સર્વર v2 સક્રિય કરીને શરૂ કરવામાં આવે ત્યારે `/v2` પર સર્વ થાય છે.

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

`http://localhost:5173/v2/` ખોલો. Vite `/api` વિનંતીઓને
`http://localhost:8900` પર પ્રોક્સી કરે છે, જેથી React એપ વધારાના
CORS સેટઅપ વગર લોકલ Flask સર્વર સાથે વાત કરી શકે.

Python પેકેજ સાથે શિપ થતું બંડલ બનાવવા માટે:

```bash
cd frontend
npm run build
```

પ્રોડક્શન બંડલ `clawmetry/static/v2/dist/` માં લખાય છે.

## રનટાઈમ / એજન્ટ કમ્પેટિબિલિટી

ClawMetry ફક્ત OpenClaw જ નહીં, પરંતુ ઘણા AI-એજન્ટ રનટાઈમ્સનું અવલોકન કરે છે. દરેક OpenClaw સિવાયનું રનટાઈમ એક સમર્પિત રીડર એડેપ્ટર શિપ કરે છે જે તેના મૂળ સેશન ફોર્મેટને ClawMetry ના યુનિફાઈડ શેપ્સમાં ટ્રાન્સલેટ કરે છે; ડિમન તેમને એ જ DuckDB સ્ટોર + ક્લાઉડ સ્નેપશોટમાં, રનટાઈમ સાથે ટેગ કરીને ઈન્જેસ્ટ કરે છે, અને જ્યારે એકથી વધુ હાજર હોય ત્યારે Session replay ટેબ **રનટાઈમ સ્વિચર** બતાવે છે. પૂરું મેટ્રિક્સ + રનટાઈમ ઉમેરવાની ગાઈડ માટે [`docs/compatibility.md`](docs/compatibility.md) જુઓ, અને OpenClaw-ફેમિલી પ્રાઈમર માટે [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) જુઓ.

| રનટાઈમ / એજન્ટ | સ્થિતિ | નોંધ |
|---|---|---|
| **OpenClaw** | Native | રેફરન્સ રનટાઈમ, ઑટો-ડિટેક્ટેડ |
| **PicoClaw** | Beta adapter | ફ્લેટ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કોલ્સ. |
| **NanoClaw** | Beta adapter | પ્રતિ-સેશન SQLite (`data/v2-sessions`). ટ્રાન્સક્રિપ્ટ્સ + મેસેજ કાઉન્ટ્સ. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટોકન્સ/ખર્ચ. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કોલ્સ + થિંકિંગ, ટોકન વપરાશ. |
| **Codex** | Beta adapter | રોલઆઉટ JSONL `~/.codex/sessions/...`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કોલ્સ, ટોકન વપરાશ. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. ચેટ/કમ્પોઝર ટ્રાન્સક્રિપ્ટ્સ, મોડલ. |
| **Aider** | Beta adapter | પ્રતિ-પ્રોજેક્ટ `.aider.chat.history.md`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટોકન કાઉન્ટ્સ. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કોલ્સ, ટોકન ટોટલ્સ. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કોલ્સ, ટોકન્સ + ખર્ચ. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કોલ્સ, ટોકન વપરાશ. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કોલ્સ, ટોકન્સ + ખર્ચ. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કોલ્સ, ટોકન્સ + ખર્ચ. |

"Beta adapter" નો અર્થ છે કે ClawMetry તે રનટાઈમના વાસ્તવિક ડિસ્ક-ફોર્મેટ માટે એક રીડર શિપ કરે છે, જે દરેક વાસ્તવિક મશીન પર વાસ્તવિક ઈન્સ્ટોલ સામે બનાવેલ + વેરિફાઈડ છે (જુઓ `tests/fixtures/runtimes/<rt>/`). એડેપ્ટર્સ રીડ-ઓન્લી છે; દરેક તેના રનટાઈમ ખરેખર શું સ્ટોર કરે છે તે વિશે પ્રામાણિક છે (દા.ત. PicoClaw/NanoClaw/Cursor ડિસ્ક પર ટોકન ખર્ચ લખતા નથી). જ્યારે એક નોડ પર ઘણા રનટાઈમ્સ ચાલે છે, ત્યારે રનટાઈમ સ્વિચર ક્લીન ડીપ-ડાઈવ માટે સેશન્સ વ્યુને એક પર સ્કોપ કરે છે.

## કોઈપણ SDK એજન્ટને ટ્રેક કરો — આઉટ-લૂપ કોસ્ટ એટ્રિબ્યુશન

ઉપરોક્ત રનટાઈમ્સ બધા સેશન્સને ડિસ્ક પર લખે છે. તમારો પોતાનો **પ્રોડક્શન એજન્ટ**, જે તમે OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, અથવા સાદા `httpx` લૂપ પર બનાવ્યો છે, તે નથી લખતો. ClawMetry નું શૂન્ય-કન્ફિગ ઈન્ટરસેપ્ટર હજુ પણ `httpx`/`requests` ને મંકી-પેચ કરીને તેના LLM કોલ્સ (ખર્ચ, ટોકન્સ, લેટન્સી, એરર્સ) કેપ્ચર કરે છે:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (અથવા `CLAWMETRY_SOURCE=support-agent` env var) દરેક કોલને એક **નામ આપેલા સોર્સ** સાથે ટેગ કરે છે, જેથી તમે ચલાવો છો તે દરેક પ્રોડક્ટ ડેશબોર્ડના Overview પરના **🔌 Out-loop sources** કાર્ડમાં પોતાની ફર્સ્ટ-ક્લાસ, ખર્ચ-એટ્રિબ્યુટેબલ લાઈન તરીકે દેખાય, દરેક એજન્ટ પ્રમાણે કોલ્સ, પ્રોવાઈડર્સ, લેટન્સી, એરર રેટ. કોઈ સોર્સ સેટ ન કર્યો? કોલ્સ હજુ પણ ટ્રેક થાય છે; ફક્ત કાર્ડ છુપાયેલું રહે છે.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

આ એ જ ડેટા લેયર છે જે રનટાઈમ એડેપ્ટર્સ ફીડ કરે છે (DuckDB → ક્લાઉડ સ્નેપશોટ), તેથી આઉટ-લૂપ સોર્સિસ ક્લાઉડ ડેશબોર્ડ સાથે એ જ રીતે સિંક થાય છે, બાકીના બધા સાથે, E2E-એન્ક્રિપ્ટેડ.

## OpenTelemetry — વેન્ડર-ન્યુટ્રલ, તમારા ટ્રેસ ગમે ત્યાં મોકલો

ClawMetry બંને દિશામાં **OpenTelemetry** બોલે છે, **GenAI સિમેન્ટિક કન્વેન્શન્સ** વાપરીને, જેથી તમારા એજન્ટ ટ્રેસ ક્યારેય એક જ ટૂલમાં લોક ન થાય.

દરેક સેશનને, LLM કોલ્સ, ટૂલ્સ, સબ-એજન્ટ્સ, ટોકન્સ, ખર્ચ, OTLP/HTTP GenAI સ્પાન્સ તરીકે કોઈપણ કલેક્ટરમાં **એક્સપોર્ટ** કરો (Datadog, Grafana, Honeycomb, અથવા તમારો પોતાનો OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ઓથ હેડર્સ અને પોલ ઈન્ટરવલ વૈકલ્પિક env vars છે:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** — બિલ્ટ-ઈન OTLP રીસીવર `/v1/traces` અને `/v1/metrics` પર બીજા કોઈપણમાંથી ટ્રેસ અને મેટ્રિક્સ સ્વીકારે છે (પ્રોટોબફ ઈન્જેસ્ટ માટે `pip install clawmetry[otel]`).

તમને શૂન્ય-કન્ફિગ, લોકલ-ફર્સ્ટ ClawMetry ડેશબોર્ડ **અને** તમારો ડેટા તમારી ટીમ પહેલેથી ચલાવે છે તે કોઈપણ બેકએન્ડમાં મળે છે, કોઈ લોક-ઈન નથી, ઈન્સ્ટોલ કરવા માટે બીજો એજન્ટ નથી.

## કન્ફિગરેશન

મોટાભાગના લોકોને કોઈ કન્ફિગની જરૂર નથી. ClawMetry તમારો વર્કસ્પેસ, લોગ્સ, સેશન્સ, અને ક્રોન્સ જાતે ડિટેક્ટ કરે છે.

જો તમારે કસ્ટમાઈઝ કરવાની જરૂર હોય તો:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

બધા વિકલ્પો: `clawmetry --help`

## સપોર્ટેડ ચેનલ્સ

તમે કન્ફિગર કરેલી દરેક OpenClaw ચેનલ માટે ClawMetry લાઈવ પ્રવૃત્તિ બતાવે છે. ફક્ત તમારા `openclaw.json` માં ખરેખર સેટઅપ થયેલી ચેનલો જ Flow ડાયાગ્રામમાં દેખાય છે, જે કન્ફિગર થયેલી નથી તે આપોઆપ છુપાયેલી રહે છે.

Flow માં કોઈપણ ચેનલ નોડ પર ક્લિક કરો જેથી ઈનકમિંગ/આઉટગોઈંગ મેસેજ કાઉન્ટ્સ સાથે લાઈવ ચેટ બબલ વ્યુ જોઈ શકાય.

| ચેનલ | સ્થિતિ | લાઈવ પોપઅપ | નોંધ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | મેસેજિસ, સ્ટેટ્સ, 10s રિફ્રેશ |
| 💬 **iMessage** | ✅ Full | ✅ | `~/Library/Messages/chat.db` સીધું વાંચે છે |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) મારફતે |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli મારફતે |
| 🟣 **Discord** | ✅ Full | ✅ | Guild + ચેનલ ડિટેક્શન |
| 🟪 **Slack** | ✅ Full | ✅ | Workspace + ચેનલ ડિટેક્શન |
| 🌐 **Webchat** | ✅ Full | ✅ | બિલ્ટ-ઈન વેબ UI સેશન્સ |
| 📡 **IRC** | ✅ Full | ✅ | ટર્મિનલ-સ્ટાઈલ બબલ UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API મારફતે iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API વેબહૂક્સ મારફતે |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams બોટ પ્લગિન મારફતે |
| 🔷 **Mattermost** | ✅ Full | ✅ | સેલ્ફ-હોસ્ટેડ ટીમ ચેટ |
| 🟩 **Matrix** | ✅ Full | ✅ | ડિસેન્ટ્રલાઈઝ્ડ, E2EE સપોર્ટ |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | ડિસેન્ટ્રલાઈઝ્ડ NIP-04 DM |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC કનેક્શન મારફતે ચેટ |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket ઈવેન્ટ સબસ્ક્રિપ્શન |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **ઑટો-ડિટેક્શન:** ClawMetry તમારો `~/.openclaw/openclaw.json` વાંચે છે અને ફક્ત તમે ખરેખર કન્ફિગર કરેલી ચેનલો જ રેન્ડર કરે છે. કોઈ મેન્યુઅલ સેટઅપની જરૂર નથી.

## Docker ડિપ્લોયમેન્ટ

ClawMetry ને કન્ટેનરમાં ચલાવવું છે? કોઈ સમસ્યા નથી! 🐳

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

> **નોંધ:** Docker માં ચલાવતી વખતે, તમારા એજન્ટની ડેટા + લોગ ડિરેક્ટરીઓ (દા.ત. `~/.openclaw`, `~/.claude`, `~/.codex`) માઉન્ટ કરો જેથી ClawMetry તમારું સેટઅપ જાતે ડિટેક્ટ કરી શકે.

## જરૂરિયાતો

- Python 3.8+
- Flask (pip દ્વારા આપોઆપ ઈન્સ્ટોલ થાય છે)
- એ જ મશીન પર એક AI એજન્ટ રનટાઈમ: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, અથવા Deep Agents (અથવા Docker માટે માઉન્ટેડ વોલ્યુમ્સ)
- Linux અથવા macOS

## NemoClaw / OpenShell સપોર્ટ

ClawMetry આપોઆપ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ને ડિટેક્ટ કરે છે, જે NVIDIA નું એન્ટરપ્રાઈઝ સિક્યુરિટી રેપર છે OpenClaw માટે જે એજન્ટ્સને સેન્ડબોક્સ્ડ OpenShell કન્ટેનર્સની અંદર ચલાવે છે.

મોટાભાગના કિસ્સાઓમાં કોઈ વધારાના કન્ફિગરેશનની જરૂર નથી. સિન્ક ડિમન સેશન ફાઈલોને જાતે શોધે છે ભલે તે હોસ્ટ પર `~/.openclaw/` માં હોય કે OpenShell કન્ટેનરની અંદર.

### તે કેવી રીતે કામ કરે છે

ClawMetry બે રીતે NemoClaw ને ડિટેક્ટ કરે છે:

1. **બાઈનરી ડિટેક્શન** — `nemoclaw` CLI માટે તપાસ કરે છે અને સેન્ડબોક્સ માહિતી મેળવવા માટે `nemoclaw status` ચલાવે છે
2. **કન્ટેનર ડિટેક્શન** — ચાલી રહેલા Docker કન્ટેનર્સને `openshell`, `nemoclaw`, અથવા `ghcr.io/nvidia/` ઈમેજ માટે સ્કેન કરે છે, પછી વોલ્યુમ માઉન્ટ્સ અથવા `docker cp` મારફતે સેશન્સ વાંચે છે

NemoClaw કન્ટેનર્સમાંથી સિન્ક થયેલી સેશન ફાઈલો ક્લાઉડ ડેશબોર્ડમાં `runtime=nemoclaw` અને `container_id` મેટાડેટા સાથે ટેગ થાય છે, જેથી તમે તેમને સ્ટાન્ડર્ડ OpenClaw સેશન્સથી એક નજરમાં અલગ પાડી શકો.

### ભલામણ કરેલ સેટઅપ: HOST પર સિન્ક ડિમન

શ્રેષ્ઠ અનુભવ માટે, ClawMetry નો સિન્ક ડિમન **હોસ્ટ મશીન** પર ચલાવો (સેન્ડબોક્સની અંદર નહીં). આ NemoClaw નેટવર્ક પોલિસી પ્રતિબંધોને ટાળે છે.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

સિન્ક ડિમન કોઈપણ ચાલી રહેલા OpenShell કન્ટેનર્સની અંદર સેશન્સ આપોઆપ શોધી કાઢશે.

### વૈકલ્પિક: સ્પષ્ટ સેન્ડબોક્સ નામ

જો ઑટો-ડિટેક્શન કામ ન કરે, તો ClawMetry ને સાચા સેન્ડબોક્સ તરફ પોઈન્ટ કરો:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### સેન્ડબોક્સની અંદર ચલાવવું (એડવાન્સ્ડ)

જો તમારે સિન્ક ડિમન **સેન્ડબોક્સની અંદર** ચલાવવો જ પડે, તો તમારી NemoClaw નેટવર્ક પોલિસીમાં આ એગ્રેસ નિયમ ઉમેરો જેથી તે ClawMetry ingest API સુધી પહોંચી શકે:

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
| `ingest.clawmetry.com` | 443 | HTTPS | હા (સિન્ક ડિમન → ક્લાઉડ) |
| `localhost:8900` | 8900 | HTTP | હા (લોકલ ડેશબોર્ડ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | કન્ટેનર સેશન ડિસ્કવરી માટે |

સિન્ક ડિમન ફક્ત `ingest.clawmetry.com` તરફ આઉટબાઉન્ડ HTTPS કોલ કરે છે. કોઈ ઈનબાઉન્ડ પોર્ટ્સની જરૂર નથી.

---

## ક્લાઉડ ડિપ્લોયમેન્ટ

SSH ટનલ્સ, રિવર્સ પ્રોક્સી, અને Docker માટે **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** જુઓ.

## ટેસ્ટિંગ

આ પ્રોજેક્ટ BrowserStack સાથે ટેસ્ટ કરવામાં આવે છે.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ટેલિમેટ્રી

જ્યારે તમે નવા મશીન પર પહેલી વાર `clawmetry` CLI ચલાવો છો ત્યારે ClawMetry
`https://app.clawmetry.com/api/install` પર એક જ અનામી "ફર્સ્ટ રન" પિંગ
મોકલે છે. અમે આનો ઉપયોગ ઈન્સ્ટોલ્સ ગણવા માટે કરીએ છીએ (OSS પ્રોજેક્ટ માટે
અમારી પાસે એકમાત્ર માર્કેટિંગ મેટ્રિક છે) અને અમારા યુઝર્સે કયા
એજન્ટ ફ્રેમવર્ક ઈન્સ્ટોલ કરેલા છે તે જાણવા માટે.

**ઈન્સ્ટોલ દીઠ બરાબર એક POST**, જેમાં આ સમાયેલું છે:

| ફિલ્ડ | ઉદાહરણ | શા માટે |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` પર સ્ટોર થયેલ રેન્ડમ UUID | ડિડપ; તમારા ઈમેલ કે api_key સાથે લિંક નથી |
| `version` | `0.12.167` | કયા વર્ઝન્સ પ્રચલિત છે |
| `os` / `os_version` | `Darwin` / `25.3.0` | પ્લેટફોર્મ સપોર્ટ પ્રાયોરિટીઝ |
| `python` | `3.11.15` | Python વર્ઝન સપોર્ટ મેટ્રિક્સ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | આગળ અમારે કયા એજન્ટ્સ સાથે ઈન્ટિગ્રેટ કરવું જોઈએ |
| `is_ci` / `ci_provider` | `true` / `github_actions` | માનવ ઈન્સ્ટોલ્સને CI નોઈઝથી અલગ કરવા |

**અમે શું નથી મોકલતા**: IP (ક્લાઉડ વિનંતીમાંથી સર્વર-સાઈડ પર દેશ કોડ
મેળવે છે, પછી IP ડિસ્કાર્ડ કરે છે), હોસ્ટનેમ, યુઝરનેમ, વર્કસ્પેસ
પાથ, ફાઈલ કન્ટેન્ટ્સ, તમારો api_key, તમારો ઈમેલ, PII અથવા
વર્કસ્પેસ-વિશિષ્ટ કંઈ પણ. વાયર પેલોડ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) માં ઓડિટ કરી શકાય તેવો છે.

**ઓપ્ટ આઉટ** (આમાંથી કોઈપણ એક તેને કાયમ માટે નિષ્ક્રિય કરે છે):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

નેટવર્ક નિષ્ફળતા ક્યારેય `clawmetry` ને ચાલવાથી બ્લોક નથી કરતી, પિંગ
3 સેકન્ડના ટાઈમઆઉટ સાથે ડિમન થ્રેડ પર ફાયર-એન્ડ-ફર્ગેટ છે.

## Star History

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
