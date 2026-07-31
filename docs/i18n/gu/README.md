<!-- i18n-src:8252f6b1d31d -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**તમારા એજન્ટને વિચારતું જુઓ.** **14 AI એજન્ટ રનટાઇમ્સ** માટે રીયલ-ટાઇમ ઓબ્ઝર્વેબિલિટી: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex અને બીજા 10. તમારા આખા એજન્ટ ફ્લીટ માટે એક ડેશબોર્ડ.

> 🌐 **આ ભાષામાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. શૂન્ય કન્ફિગ. બધું જ ઓટો-ડિટેક્ટ થાય છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે અને તમારું કામ પૂરું.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 એજન્ટ રનટાઇમ્સ સાથે કામ કરે છે

ClawMetry એ OpenClaw માટેની ઓબ્ઝર્વેબિલિટી તરીકે શરૂઆત કરી હતી, અને હવે તે એક જ ડેશબોર્ડમાં તમારા **આખા એજન્ટ ફ્લીટ**ને મીટર કરે છે, તમારા મશીન પર દરેક રનટાઇમને ઓટો-ડિટેક્ટ કરીને:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw અને NemoClaw ઓપન-સોર્સ એપમાં મફત છે; બાકીના રનટાઇમ્સ ClawMetry Cloud અથવા સેલ્ફ-હોસ્ટેડ Pro લાયસન્સ સાથે સક્રિય થાય છે. હેડરમાંથી રનટાઇમ બદલો અને દરેક ટેબ - કોસ્ટ, ટોકન્સ, ટૂલ્સ, ટ્રેસ - તે રનટાઇમ પ્રમાણે ફરીથી સ્કોપ થાય છે. ચોક્કસ ફ્રી/પેઇડ વિભાજન, ટાયર મેટ્રિક્સ, `/api/entitlement` શેપ, અને `clawmetry license` CLI માટે **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** જુઓ.

## તમને શું મળે છે

- **Flow** — ચેનલો, બ્રેઈન, ટૂલ્સ અને પાછળ સંદેશાઓના પ્રવાહને દર્શાવતું લાઈવ એનિમેટેડ ડાયાગ્રામ
- **Overview** — હેલ્થ ચેક્સ, એક્ટિવિટી હીટમેપ, સેશન કાઉન્ટ્સ, મોડેલ માહિતી
- **Usage** — દૈનિક/સાપ્તાહિક/માસિક બ્રેકડાઉન સાથે ટોકન અને કોસ્ટ ટ્રેકિંગ
- **Sessions** — મોડેલ, ટોકન્સ, છેલ્લી પ્રવૃત્તિ સાથે સક્રિય એજન્ટ સેશન્સ
- **Crons** — સ્ટેટસ, નેક્સ્ટ રન, ડ્યુરેશન સાથે શેડ્યુલ્ડ જોબ્સ
- **Logs** — કલર-કોડેડ રીયલ-ટાઇમ લોગ સ્ટ્રીમિંગ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ડેઇલી નોટ્સ બ્રાઉઝ કરો
- **Transcripts** — સેશન હિસ્ટ્રી વાંચવા માટે ચેટ-બબલ UI
- **Alerts** — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, એજન્ટ-ઓફલાઈન ડિટેક્શન; Slack, Discord, PagerDuty, Telegram, Email પર રૂટ કરે છે
- **Approvals** — વિનાશક ડિલીટ્સ, ફોર્સ પુશ, DB મ્યુટેશન્સ, sudo, પેકેજ ઇન્સ્ટોલ્સ, નેટવર્ક કૉલ્સને એક-ક્લિક સાઈન-ઓફ પાછળ ગેટ કરો

## સ્ક્રીનશોટ્સ

### 🧠 Brain — લાઈવ એજન્ટ ઇવેન્ટ સ્ટ્રીમ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ટોકન ઉપયોગ અને સેશન સારાંશ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — રીયલ-ટાઇમ ટૂલ કૉલ ફીડ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — મોડેલ અને સેશન પ્રમાણે કોસ્ટ બ્રેકડાઉન
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — વર્કસ્પેસ ફાઇલ બ્રાઉઝર
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — સ્થિતિ અને ઓડિટ લોગ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, Slack / Discord / PagerDuty / Email પર વેબહૂક્સ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — જોખમી ટૂલ કૉલ્સને મેન્યુઅલ સાઈન-ઓફ પાછળ ગેટ કરો; પોલિસી-બેક્ડ પ્રોટેક્શન નિયમો
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code માટે પ્રી-એક્ઝિક્યુશન બ્લોકિંગ** — એક કમાન્ડ એક
PreToolUse હૂક ઇન્સ્ટોલ કરે છે જે મેચ થતા ટૂલ કૉલ્સને તે *ચાલે તે પહેલાં*
અટકાવે છે અને તમારા નિર્ણયની રાહ જુએ છે (તમારા ફોનથી એક ટેપ
[cloud push notifications](https://app.clawmetry.com/push) સક્રિય કરેલા હોય ત્યારે):

```bash
clawmetry hooks install     # ~/.claude/settings.json લખે છે (આઇડમ્પોટન્ટ)
clawmetry hooks status      # શું વાયર થયેલું છે + કેટલી પોલિસીઓ સક્રિય છે
clawmetry hooks uninstall   # ફક્ત ClawMetry ની એન્ટ્રીઓ દૂર કરે છે
```

એક ડિનાય ફક્ત તે એક ટૂલ કૉલને બ્લોક કરે છે — એજન્ટ પોતાનું સેશન જાળવી રાખે છે અને
બીજો અભિગમ અજમાવી શકે છે. તમારા ફોન પર મંજૂરી આપવાથી Claude Code ની પોતાની
પરમિશન પ્રોમ્પ્ટ સ્કિપ થાય છે (તમે પહેલેથી જ જવાબ આપ્યો છે). ન મેચ થતા ટૂલ્સનો ખર્ચ ~40ms
છે અને તે Claude Code ના સામાન્ય પરમિશન ફ્લોમાં પડે છે. Claude Code પોતે
તમારી રાહ જોતું હોય ત્યારે પણ તમને ફોન પુશ મળે છે (`permission_prompt` /
`idle_prompt` નોટિફિકેશન્સ).

## ઇન્સ્ટોલ

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

## v2 Frontend ડેવલપમેન્ટ

v2 React એપ `frontend/` માં રહે છે અને જ્યારે Flask
સર્વર v2 સક્રિય કરીને શરૂ કરવામાં આવે ત્યારે `/v2` પર સર્વ થાય છે.

ડેવલપ કરતી વખતે બે ટર્મિનલ્સ વાપરો:

```bash
# ટર્મિનલ 1: :8900 પર Flask API/server
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ટર્મિનલ 2: :5173 પર Vite dev server
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` ખોલો. Vite `/api` રિક્વેસ્ટ્સને
`http://localhost:8900` પર પ્રોક્સી કરે છે, જેથી React એપ વધારાના
CORS સેટઅપ વગર લોકલ Flask સર્વર સાથે વાત કરી શકે.

Python પેકેજ સાથે શિપ થતું બંડલ બનાવવા માટે:

```bash
cd frontend
npm run build
```

પ્રોડક્શન બંડલ `clawmetry/static/v2/dist/` માં લખાય છે.

## રનટાઇમ / એજન્ટ સુસંગતતા

ClawMetry ફક્ત OpenClaw જ નહીં, ઘણા AI-એજન્ટ રનટાઇમ્સનું અવલોકન કરે છે. દરેક નોન-OpenClaw રનટાઇમ એક સમર્પિત રીડર એડેપ્ટર શિપ કરે છે જે તેના નેટિવ સેશન ફોર્મેટને ClawMetry ના યુનિફાઇડ શેપ્સમાં ટ્રાન્સલેટ કરે છે; ડેમન તેમને એ જ DuckDB સ્ટોર + ક્લાઉડ સ્નેપશોટમાં ઇન્જેસ્ટ કરે છે, રનટાઇમ સાથે ટેગ કરેલા, અને જ્યારે એકથી વધુ હાજર હોય ત્યારે Session replay ટેબ **રનટાઇમ સ્વિચર** બતાવે છે. સંપૂર્ણ મેટ્રિક્સ + રનટાઇમ ઉમેરવાની ગાઈડ માટે [`docs/compatibility.md`](docs/compatibility.md) જુઓ, અને OpenClaw-family પ્રાઈમર માટે [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) જુઓ.

| રનટાઇમ / એજન્ટ | સ્ટેટસ | નોંધ |
|---|---|---|
| **OpenClaw** | નેટિવ | રેફરન્સ રનટાઇમ, ઓટો-ડિટેક્ટેડ |
| **PicoClaw** | બીટા એડેપ્ટર | ફ્લેટ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ. |
| **NanoClaw** | બીટા એડેપ્ટર | પ્રતિ-સેશન SQLite (`data/v2-sessions`). ટ્રાન્સક્રિપ્ટ્સ + મેસેજ કાઉન્ટ્સ. |
| **Hermes** | બીટા એડેપ્ટર | SQLite `~/.hermes/state.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટોકન્સ/કોસ્ટ. |
| **Claude Code** | બીટા એડેપ્ટર | JSONL `~/.claude/projects/.../<id>.jsonl`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ + થિંકિંગ, ટોકન વપરાશ. |
| **Codex** | બીટા એડેપ્ટર | Rollout JSONL `~/.codex/sessions/...`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન વપરાશ. |
| **Cursor** | બીટા એડેપ્ટર | SQLite `state.vscdb`. ચેટ/કમ્પોઝર ટ્રાન્સક્રિપ્ટ્સ, મોડેલ. |
| **Aider** | બીટા એડેપ્ટર | પ્રતિ-પ્રોજેક્ટ `.aider.chat.history.md`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટોકન કાઉન્ટ્સ. |
| **Goose** | બીટા એડેપ્ટર | SQLite `~/.local/share/goose`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન ટોટલ્સ. |
| **opencode** | બીટા એડેપ્ટર | SQLite `~/.local/share/opencode`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન્સ + કોસ્ટ. |
| **Qwen Code** | બીટા એડેપ્ટર | JSONL `~/.qwen/projects/.../chats`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન વપરાશ. |
| **Pi** | બીટા એડેપ્ટર | JSONL `~/.pi/agent/sessions`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન્સ + કોસ્ટ. |
| **Deep Agents** | બીટા એડેપ્ટર | SQLite `~/.deepagents/.state/sessions.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન્સ + કોસ્ટ. |
| **n8n** | બીટા એડેપ્ટર | SQLite `~/.n8n/database.sqlite`. વર્કફ્લો એક્ઝિક્યુશન્સ, નોડ રન્સ, AI Agent પ્રોમ્પ્ટ્સ, જ્યાં n8n રેકોર્ડ કરે છે ત્યાં મોડેલ + ટોકન્સ. |

"બીટા એડેપ્ટર" નો અર્થ છે કે ClawMetry તે રનટાઇમના વાસ્તવિક ઓન-ડિસ્ક ફોર્મેટ માટે એક રીડર શિપ કરે છે, દરેક વાસ્તવિક મશીન પર વાસ્તવિક ઇન્સ્ટોલ સામે બનાવેલો + વેરિફાઇડ (જુઓ `tests/fixtures/runtimes/<rt>/`). એડેપ્ટર્સ રીડ-ઓન્લી છે; દરેક તેના રનટાઇમ ખરેખર શું સ્ટોર કરે છે તે વિશે પ્રામાણિક છે (દા.ત. PicoClaw/NanoClaw/Cursor ડિસ્ક પર ટોકન કોસ્ટ લખતા નથી). જ્યારે એક નોડ પર અનેક રનટાઇમ્સ ચાલતા હોય, ત્યારે રનટાઇમ સ્વિચર ક્લીન ડીપ-ડાઇવ માટે સેશન્સ વ્યુને એક પર સ્કોપ કરે છે.

## કોઈપણ SDK એજન્ટને ટ્રેક કરો — આઉટ-લૂપ કોસ્ટ એટ્રિબ્યુશન

ઉપરના રનટાઇમ્સ બધા સેશન્સને ડિસ્ક પર લખે છે. તમારો પોતાનો **પ્રોડક્શન એજન્ટ** — જે તમે OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, અથવા સાદા `httpx` લૂપ પર બનાવ્યો છે — તે નથી લખતો. ClawMetry નું શૂન્ય-કન્ફિગ ઇન્ટરસેપ્ટર `httpx`/`requests` ને મંકી-પેચ કરીને હજુ પણ તેના LLM કૉલ્સ (કોસ્ટ, ટોકન્સ, લેટન્સી, એરર્સ) કેપ્ચર કરે છે:

```python
import clawmetry.track            # ઇન્ટરસેપ્ટર સક્રિય કરો
clawmetry.track.set_source("support-agent")   # આ પ્રોડક્ટનું નામ આપો

# ...તમારો એજન્ટ સામાન્ય રીતે ચાલે છે; દરેક LLM કૉલ હવે ટ્રેક + એટ્રિબ્યુટ થાય છે.
```

`set_source()` (અથવા `CLAWMETRY_SOURCE=support-agent` env var) દરેક કૉલને એક **નામવાળા સોર્સ**થી ટેગ કરે છે, જેથી તમે ચલાવો છો તે દરેક પ્રોડક્ટ ડેશબોર્ડના Overview પરના **🔌 Out-loop sources** કાર્ડમાં પોતાની ફર્સ્ટ-ક્લાસ, કોસ્ટ-એટ્રિબ્યુટેબલ લાઇન તરીકે દેખાય — દરેક એજન્ટ પ્રમાણે કૉલ્સ, પ્રોવાઈડર્સ, લેટન્સી, એરર રેટ. કોઈ સોર્સ સેટ ન કર્યો? કૉલ્સ હજુ પણ ટ્રેક થાય છે; ફક્ત કાર્ડ છુપાયેલું રહે છે.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

આ એ જ ડેટા લેયર છે જે રનટાઇમ એડેપ્ટર્સ ફીડ કરે છે (DuckDB → ક્લાઉડ સ્નેપશોટ), તેથી આઉટ-લૂપ સોર્સ બાકીની બધી વસ્તુઓની જેમ જ ક્લાઉડ ડેશબોર્ડ સાથે સિંક થાય છે, E2E-એન્ક્રિપ્ટેડ.

## OpenTelemetry — વેન્ડર-ન્યુટ્રલ, તમારા ટ્રેસ ગમે ત્યાં મોકલો

ClawMetry બંને દિશામાં **OpenTelemetry** બોલે છે, **GenAI સિમેન્ટિક કન્વેન્શન્સ** વાપરીને, જેથી તમારા એજન્ટ ટ્રેસ ક્યારેય એક ટૂલમાં લોક ન થાય.

**એક્સપોર્ટ** કરો દરેક સેશન — LLM કૉલ્સ, ટૂલ્સ, સબ-એજન્ટ્સ, ટોકન્સ, કોસ્ટ — OTLP/HTTP GenAI સ્પાન્સ તરીકે કોઈપણ કલેક્ટરમાં (Datadog, Grafana, Honeycomb, અથવા તમારો પોતાનો OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# સમાન રીતે:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth હેડર્સ અને પોલ ઇન્ટરવલ વૈકલ્પિક env vars છે:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # વધારાના HTTP હેડર્સ
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # સેકંડ (ડિફોલ્ટ 60)
```

**ઇન્જેસ્ટ** — બિલ્ટ-ઇન OTLP રીસીવર `/v1/traces` અને `/v1/metrics` પર બીજા કોઈપણ સ્રોતમાંથી ટ્રેસ અને મેટ્રિક્સ સ્વીકારે છે (protobuf ingest માટે `pip install clawmetry[otel]`).

તમને શૂન્ય-કન્ફિગ, લોકલ-ફર્સ્ટ ClawMetry ડેશબોર્ડ **અને** તમારી ટીમ પહેલેથી ચલાવે છે તે કોઈપણ બેકએન્ડમાં તમારો ડેટા મળે છે — કોઈ લોક-ઇન નહીં, બીજું એજન્ટ ઇન્સ્ટોલ કરવાની જરૂર નહીં.

## કન્ફિગરેશન

મોટાભાગના લોકોને કોઈ કન્ફિગની જરૂર નથી. ClawMetry તમારા વર્કસ્પેસ, લોગ્સ, સેશન્સ અને ક્રોન્સને ઓટો-ડિટેક્ટ કરે છે.

જો તમારે કસ્ટમાઇઝ કરવાની જરૂર હોય તો:

```bash
clawmetry --port 9000              # કસ્ટમ પોર્ટ (ડિફોલ્ટ: 8900)
clawmetry --host 127.0.0.1         # ફક્ત localhost પર બાઈન્ડ કરો
clawmetry --workspace ~/mybot      # કસ્ટમ વર્કસ્પેસ પાથ
clawmetry --name "Alice"           # Flow વિઝ્યુલાઇઝેશનમાં તમારું નામ
```

બધા વિકલ્પો: `clawmetry --help`

## સપોર્ટેડ ચેનલ્સ

ClawMetry તમે કન્ફિગર કરેલા દરેક OpenClaw ચેનલ માટે લાઈવ પ્રવૃત્તિ બતાવે છે. તમારા `openclaw.json` માં ખરેખર સેટઅપ કરેલી ચેનલો જ Flow ડાયાગ્રામમાં દેખાય છે — કન્ફિગર ન કરેલી ચેનલો આપોઆપ છુપાયેલી રહે છે.

Flow માં કોઈપણ ચેનલ નોડ પર ક્લિક કરીને ઇનકમિંગ/આઉટગોઈંગ મેસેજ કાઉન્ટ્સ સાથે લાઈવ ચેટ બબલ વ્યુ જુઓ.

| ચેનલ | સ્ટેટસ | લાઈવ પોપઅપ | નોંધ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ પૂર્ણ | ✅ | મેસેજિસ, સ્ટેટ્સ, 10s રિફ્રેશ |
| 💬 **iMessage** | ✅ પૂર્ણ | ✅ | `~/Library/Messages/chat.db` સીધું વાંચે છે |
| 💚 **WhatsApp** | ✅ પૂર્ણ | ✅ | WhatsApp Web (Baileys) દ્વારા |
| 🔵 **Signal** | ✅ પૂર્ણ | ✅ | signal-cli દ્વારા |
| 🟣 **Discord** | ✅ પૂર્ણ | ✅ | ગિલ્ડ + ચેનલ ડિટેક્શન |
| 🟪 **Slack** | ✅ પૂર્ણ | ✅ | વર્કસ્પેસ + ચેનલ ડિટેક્શન |
| 🌐 **Webchat** | ✅ પૂર્ણ | ✅ | બિલ્ટ-ઇન વેબ UI સેશન્સ |
| 📡 **IRC** | ✅ પૂર્ણ | ✅ | ટર્મિનલ-સ્ટાઈલ બબલ UI |
| 🍏 **BlueBubbles** | ✅ પૂર્ણ | ✅ | BlueBubbles REST API દ્વારા iMessage |
| 🔵 **Google Chat** | ✅ પૂર્ણ | ✅ | Chat API વેબહૂક્સ દ્વારા |
| 🟣 **MS Teams** | ✅ પૂર્ણ | ✅ | Teams બોટ પ્લગઇન દ્વારા |
| 🔷 **Mattermost** | ✅ પૂર્ણ | ✅ | સેલ્ફ-હોસ્ટેડ ટીમ ચેટ |
| 🟩 **Matrix** | ✅ પૂર્ણ | ✅ | વિકેન્દ્રિત, E2EE સપોર્ટ |
| 🟢 **LINE** | ✅ પૂર્ણ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ પૂર્ણ | ✅ | વિકેન્દ્રિત NIP-04 DMs |
| 🟣 **Twitch** | ✅ પૂર્ણ | ✅ | IRC કનેક્શન દ્વારા ચેટ |
| 🔷 **Feishu/Lark** | ✅ પૂર્ણ | ✅ | WebSocket ઇવેન્ટ સબસ્ક્રિપ્શન |
| 🔵 **Zalo** | ✅ પૂર્ણ | ✅ | Zalo Bot API |

> **ઓટો-ડિટેક્શન:** ClawMetry તમારો `~/.openclaw/openclaw.json` વાંચે છે અને ફક્ત તમે ખરેખર કન્ફિગર કરેલી ચેનલોને જ રેન્ડર કરે છે. કોઈ મેન્યુઅલ સેટઅપની જરૂર નથી.

## Docker ડિપ્લોયમેન્ટ

ClawMetry ને કન્ટેનરમાં ચલાવવા માંગો છો? કોઈ સમસ્યા નથી! 🐳

**Docker સાથે ઝડપી શરૂઆત:**

```bash
# ઈમેજ બિલ્ડ કરો
docker build -t clawmetry .

# ડિફોલ્ટ સેટિંગ્સ સાથે ચલાવો
docker run -p 8900:8900 clawmetry

# અથવા તમારા એજન્ટની ડેટા ડિરેક્ટરી માઉન્ટ કરો (દર્શાવેલ: OpenClaw ની ~/.openclaw)
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

> **નોંધ:** Docker માં ચલાવતી વખતે, તમારા એજન્ટની ડેટા + લોગ ડિરેક્ટરીઓ (દા.ત. `~/.openclaw`, `~/.claude`, `~/.codex`) માઉન્ટ કરો જેથી ClawMetry તમારું સેટઅપ ઓટો-ડિટેક્ટ કરી શકે.

## જરૂરિયાતો

- Python 3.8+
- Flask (pip દ્વારા આપોઆપ ઇન્સ્ટોલ થાય છે)
- એ જ મશીન પર એક AI એજન્ટ રનટાઇમ: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, અથવા n8n (અથવા Docker માટે માઉન્ટેડ વોલ્યુમ્સ)
- Linux અથવા macOS

## NemoClaw / OpenShell સપોર્ટ

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) ને આપોઆપ ડિટેક્ટ કરે છે — NVIDIA નું એન્ટરપ્રાઈઝ સિક્યુરિટી રેપર જે OpenClaw માટે છે અને એજન્ટ્સને સેન્ડબોક્સ્ડ OpenShell કન્ટેનર્સની અંદર ચલાવે છે.

મોટાભાગના કિસ્સાઓમાં કોઈ વધારાના કન્ફિગરેશનની જરૂર નથી. સિન્ક ડેમન સેશન ફાઇલોને આપોઆપ શોધે છે, ભલે તે હોસ્ટ પર `~/.openclaw/` માં હોય કે OpenShell કન્ટેનરની અંદર.

### આ કેવી રીતે કામ કરે છે

ClawMetry બે રીતે NemoClaw ને ડિટેક્ટ કરે છે:

1. **બાઈનરી ડિટેક્શન** — `nemoclaw` CLI માટે તપાસ કરે છે અને સેન્ડબોક્સ માહિતી મેળવવા માટે `nemoclaw status` ચલાવે છે
2. **કન્ટેનર ડિટેક્શન** — `openshell`, `nemoclaw`, અથવા `ghcr.io/nvidia/` ઈમેજિસ માટે ચાલી રહેલા Docker કન્ટેનર્સને સ્કેન કરે છે, પછી વોલ્યુમ માઉન્ટ્સ અથવા `docker cp` દ્વારા સેશન્સ વાંચે છે

NemoClaw કન્ટેનર્સમાંથી સિન્ક કરેલી સેશન ફાઇલોને ક્લાઉડ ડેશબોર્ડમાં `runtime=nemoclaw` અને `container_id` મેટાડેટા સાથે ટેગ કરવામાં આવે છે, જેથી તમે તેમને એક નજરમાં સ્ટાન્ડર્ડ OpenClaw સેશન્સથી અલગ ઓળખી શકો.

### ભલામણ કરેલ સેટઅપ: HOST પર સિન્ક ડેમન

શ્રેષ્ઠ અનુભવ માટે, ClawMetry ના સિન્ક ડેમનને **હોસ્ટ મશીન** પર ચલાવો (સેન્ડબોક્સની અંદર નહીં). આ NemoClaw નેટવર્ક પોલિસી પ્રતિબંધોને ટાળે છે.

```bash
# હોસ્ટ પર (સેન્ડબોક્સની બહાર)
pip install clawmetry
clawmetry connect
clawmetry sync
```

સિન્ક ડેમન કોઈપણ ચાલી રહેલા OpenShell કન્ટેનર્સની અંદર સેશન્સને આપોઆપ શોધી કાઢશે.

### વૈકલ્પિક: સ્પષ્ટ સેન્ડબોક્સ નામ

જો ઓટો-ડિટેક્શન કામ ન કરે, તો ClawMetry ને યોગ્ય સેન્ડબોક્સ તરફ નિર્દેશિત કરો:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### સેન્ડબોક્સની અંદર ચલાવવું (એડવાન્સ્ડ)

જો તમારે સિન્ક ડેમનને OpenShell સેન્ડબોક્સની **અંદર** ચલાવવો જ પડે, તો તમારી NemoClaw નેટવર્ક પોલિસીમાં આ egress નિયમ ઉમેરો જેથી તે ClawMetry ingest API સુધી પહોંચી શકે:

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
| `ingest.clawmetry.com` | 443 | HTTPS | હા (સિન્ક ડેમન → ક્લાઉડ) |
| `localhost:8900` | 8900 | HTTP | હા (લોકલ ડેશબોર્ડ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | કન્ટેનર સેશન ડિસ્કવરી માટે |

સિન્ક ડેમન ફક્ત `ingest.clawmetry.com` પર જ આઉટબાઉન્ડ HTTPS કૉલ્સ કરે છે. કોઈ ઇનબાઉન્ડ પોર્ટ્સની જરૂર નથી.

---

## Cloud ડિપ્લોયમેન્ટ

SSH ટનલ્સ, રિવર્સ પ્રોક્સી, અને Docker માટે **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** જુઓ.

## ટેસ્ટિંગ

આ પ્રોજેક્ટ BrowserStack સાથે ટેસ્ટ કરવામાં આવે છે.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ટેલિમેટ્રી

ClawMetry `https://app.clawmetry.com/api/install` પર અનામી
ઇન્સ્ટોલ-લાઇફસાઇકલ પિંગ મોકલે છે: નવા મશીન પર `clawmetry` CLI
પ્રથમ વખત ચલાવો ત્યારે એક `install` પિંગ, નવા વર્ઝનમાં અપગ્રેડ કર્યા
પછીના પ્રથમ રન પર એક `update` પિંગ, અને તમે ડેશબોર્ડની અંદરની
ઓનબોર્ડિંગ પસંદગી પૂર્ણ કરો ત્યારે એક `onboarded` પિંગ. અમે વાસ્તવિક
ઇન્સ્ટોલ્સ ગણવા માટે આનો ઉપયોગ કરીએ છીએ (કાચા PyPI ડાઉનલોડ નંબર્સ
~98% મિરર્સ, CI, અને ઓટો-અપડેટ રી-ડાઉનલોડ્સ છે) અને એ જાણવા માટે કે
કયા એજન્ટ ફ્રેમવર્ક્સ અને વર્ઝન્સ ખરેખર ઉપયોગમાં છે.

**દરેક વર્ઝન દીઠ, દરેક લાઈફસાઇકલ ઇવેન્ટ માટે વધુમાં વધુ એક POST**, જેમાં આ સમાવેશ થાય છે:

| ફિલ્ડ | ઉદાહરણ | કારણ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` પર સંગ્રહિત રેન્ડમ UUID | ડિડપ; અનામી જ્યાં સુધી તમે સ્પષ્ટપણે Cloud sync કનેક્ટ ન કરો (ત્યાર બાદ પ્રમાણિત ડેમન હાર્ટબીટ તેને લઈ જાય છે, આ ઇન્સ્ટોલને તમારા એકાઉન્ટ સાથે લિંક કરે છે) |
| `event` | `install` / `update` / `onboarded` | નવો ઇન્સ્ટોલ vs હાલના ઇન્સ્ટોલનું અપગ્રેડ |
| `version` | `0.12.167` | કયા વર્ઝન્સ ઉપયોગમાં છે |
| `os` / `os_version` | `Darwin` / `25.3.0` | પ્લેટફોર્મ સપોર્ટ પ્રાયોરિટીઝ |
| `python` | `3.11.15` | Python વર્ઝન સપોર્ટ મેટ્રિક્સ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | આગળ કયા એજન્ટ્સ સાથે અમારે ઈન્ટિગ્રેટ કરવું જોઈએ |
| `is_ci` / `ci_provider` | `true` / `github_actions` | માનવ ઇન્સ્ટોલ્સને CI નોઈઝથી અલગ કરવા |

**અમે શું નથી મોકલતા**: IP (ક્લાઉડ સર્વર-સાઈડ પર રિક્વેસ્ટમાંથી
દેશ કોડ મેળવે છે, પછી IP ડિસ્કાર્ડ કરે છે), હોસ્ટનેમ, યુઝરનેમ, વર્કસ્પેસ
પાથ, ફાઇલ કન્ટેન્ટ્સ, તમારી api_key, તમારો ઈમેલ, કંઈપણ PII અથવા
વર્કસ્પેસ-સ્પેસિફિક. વાયર પેલોડ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) માં ઓડિટેબલ છે.

**ઓપ્ટ આઉટ** (આમાંથી કોઈપણ એક તેને કાયમ માટે અક્ષમ કરે છે):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # પ્રતિ-શેલ
export DO_NOT_TRACK=1                          # W3C ક્રોસ-ટૂલ સ્ટાન્ડર્ડ
touch ~/.clawmetry/notelemetry                 # સ્થાયી ફાઇલ માર્કર
```

નેટવર્ક નિષ્ફળતા ક્યારેય `clawmetry` ને ચાલવાથી અટકાવતી નથી — પિંગ
ડેમન થ્રેડ પર 3s ટાઈમઆઉટ સાથે ફાયર-એન્ડ-ફોર્ગેટ છે.

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
  <sub>નિર્માતા <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ઇકોસિસ્ટમનો ભાગ</sub>
</p>
