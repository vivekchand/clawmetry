<!-- i18n-src:191e9094d7fa -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**તમારા એજન્ટને વિચારતું જુઓ.** **14 AI એજન્ટ રનટાઇમ્સ** માટે રિયલ-ટાઇમ ઓબ્ઝર્વેબિલિટી: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex અને બીજા 10. તમારા આખા એજન્ટ ફ્લીટ માટે એક જ ડેશબોર્ડ.

> 🌐 **આ ભાષામાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. ઝીરો કન્ફિગ. બધું જ ઓટો-ડિટેક્ટ થાય છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે અને તમારું કામ પૂરું.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 એજન્ટ રનટાઇમ્સ સાથે કામ કરે છે

ClawMetry ની શરૂઆત OpenClaw માટેની ઓબ્ઝર્વેબિલિટી તરીકે થઈ હતી, અને હવે તે તમારા **આખા એજન્ટ ફ્લીટ**ને એક જ ડેશબોર્ડમાં માપે છે, તમારા મશીન પર દરેક રનટાઇમને ઓટો-ડિટેક્ટ કરીને:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw અને NemoClaw ઓપન-સોર્સ એપમાં મફત છે; બાકીના રનટાઇમ્સ ClawMetry Cloud અથવા સેલ્ફ-હોસ્ટેડ Pro લાયસન્સ સાથે સક્રિય થાય છે. હેડરમાંથી રનટાઇમ સ્વિચ કરો અને દરેક ટેબ — કોસ્ટ, ટોકન્સ, ટૂલ્સ, ટ્રેસ — તે રનટાઇમ પ્રમાણે ફરીથી સ્કોપ થાય છે. ચોક્કસ ફ્રી/પેઇડ વિભાજન, ટાયર મેટ્રિક્સ, `/api/entitlement` શેપ, અને `clawmetry license` CLI માટે **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** જુઓ.

## તમને શું મળે છે

- **Flow** — ચેનલ્સ, બ્રેઇન, ટૂલ્સ અને પાછા થઈને પસાર થતા મેસેજીસ દર્શાવતું લાઇવ એનિમેટેડ ડાયાગ્રામ
- **Overview** — હેલ્થ ચેક્સ, એક્ટિવિટી હીટમેપ, સેશન કાઉન્ટ્સ, મોડેલ માહિતી
- **Usage** — દૈનિક/સાપ્તાહિક/માસિક વિભાજન સાથે ટોકન અને કોસ્ટ ટ્રેકિંગ
- **Sessions** — મોડેલ, ટોકન્સ, છેલ્લી પ્રવૃત્તિ સાથે સક્રિય એજન્ટ સેશન્સ
- **Crons** — સ્ટેટસ, નેક્સ્ટ રન, ડ્યુરેશન સાથે શેડ્યુલ્ડ જોબ્સ
- **Logs** — કલર-કોડેડ રિયલ-ટાઇમ લોગ સ્ટ્રીમિંગ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, ડેઇલી નોટ્સ બ્રાઉઝ કરો
- **Transcripts** — સેશન હિસ્ટ્રી વાંચવા માટે ચેટ-બબલ UI
- **Alerts** — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, એજન્ટ-ઓફલાઇન ડિટેક્શન; Slack, Discord, PagerDuty, Telegram, Email પર રૂટ થાય છે
- **Approvals** — વિનાશક ડિલીટ્સ, ફોર્સ પુશ, DB મ્યુટેશન્સ, sudo, પેકેજ ઇન્સ્ટોલ્સ, નેટવર્ક કૉલ્સને એક-ક્લિક સાઇન-ઑફ પાછળ ગેટ કરો

## સ્ક્રીનશોટ્સ

### 🧠 Brain — લાઇવ એજન્ટ ઇવેન્ટ સ્ટ્રીમ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ટોકન યુસેજ અને સેશન સારાંશ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — રિયલ-ટાઇમ ટૂલ કૉલ ફીડ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — મોડેલ અને સેશન પ્રમાણે કોસ્ટ વિભાજન
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — વર્કસ્પેસ ફાઇલ બ્રાઉઝર
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — પોસ્ચર અને ઓડિટ લોગ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, Slack / Discord / PagerDuty / Email માટે વેબહૂક્સ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — જોખમી ટૂલ કૉલ્સને મેન્યુઅલ સાઇન-ઑફ પાછળ ગેટ કરો; પોલિસી-બેક્ડ પ્રોટેક્શન નિયમો
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code માટે પ્રી-એક્ઝિક્યુશન બ્લોકિંગ** — એક કમાન્ડ એક
PreToolUse હૂક ઇન્સ્ટોલ કરે છે જે મેચ થતા ટૂલ કૉલ્સને તે *ચાલે તે પહેલાં*
અટકાવે છે અને તમારા નિર્ણયની રાહ જુએ છે ([ક્લાઉડ પુશ નોટિફિકેશન્સ](https://app.clawmetry.com/push)
સક્રિય હોય ત્યારે તમારા ફોનથી એક ટેપ):

```bash
clawmetry hooks install     # ~/.claude/settings.json લખે છે (idempotent)
clawmetry hooks status      # શું વાયર્ડ છે + કેટલી પોલિસીઓ સક્રિય છે
clawmetry hooks uninstall   # ફક્ત ClawMetry ની એન્ટ્રીઓ દૂર કરે છે
```

ડિનાય ફક્ત તે એક ટૂલ કૉલને બ્લોક કરે છે — એજન્ટ પોતાનું સેશન જાળવી રાખે
છે અને બીજો અભિગમ અજમાવી શકે છે. તમારા ફોન પર એપ્રૂવ કરવાથી Claude Code
ની પોતાની પરમિશન પ્રોમ્પ્ટ સ્કિપ થાય છે (તમે પહેલેથી જ જવાબ આપી દીધો છે).
મેચ ન થતા ટૂલ્સનો ખર્ચ ~40ms છે અને તે Claude Code ના સામાન્ય પરમિશન
ફ્લોમાં પડે છે. જ્યારે Claude Code પોતે તમારી રાહ જોઈ રહ્યું હોય ત્યારે
પણ તમને ફોન પુશ મળે છે (`permission_prompt` / `idle_prompt` નોટિફિકેશન્સ).

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

v2 React એપ `frontend/` માં રહે છે અને જ્યારે Flask સર્વર v2 સક્રિય
કરીને શરૂ કરવામાં આવે ત્યારે `/v2` પર સર્વ થાય છે.

ડેવલપ કરતી વખતે બે ટર્મિનલ્સનો ઉપયોગ કરો:

```bash
# ટર્મિનલ 1: :8900 પર Flask API/સર્વર
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ટર્મિનલ 2: :5173 પર Vite ડેવ સર્વર
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` ખોલો. Vite `/api` રિક્વેસ્ટ્સને
`http://localhost:8900` પર પ્રોક્સી કરે છે, જેથી React એપ વધારાના CORS
સેટઅપ વગર લોકલ Flask સર્વર સાથે વાત કરી શકે.

Python પેકેજ સાથે શિપ થતું બંડલ બનાવવા માટે:

```bash
cd frontend
npm run build
```

પ્રોડક્શન બંડલ `clawmetry/static/v2/dist/` માં લખવામાં આવે છે.

## રનટાઇમ / એજન્ટ સુસંગતતા

ClawMetry ફક્ત OpenClaw જ નહીં, ઘણા બધા AI-એજન્ટ રનટાઇમ્સનું નિરીક્ષણ
કરે છે. દરેક નોન-OpenClaw રનટાઇમ એક સમર્પિત રીડર એડેપ્ટર શિપ કરે છે જે
તેના નેટિવ સેશન ફોર્મેટને ClawMetry ના યુનિફાઇડ શેપ્સમાં અનુવાદિત કરે
છે; ડિમન તેમને એ જ DuckDB સ્ટોર + ક્લાઉડ સ્નેપશોટમાં ઇન્જેસ્ટ કરે છે,
રનટાઇમ સાથે ટેગ કરીને, અને Session replay ટેબ એકથી વધુ રનટાઇમ હાજર
હોય ત્યારે **રનટાઇમ સ્વિચર** દર્શાવે છે. સંપૂર્ણ મેટ્રિક્સ + રનટાઇમ્સ
ઉમેરવાની ગાઇડ માટે [`docs/compatibility.md`](docs/compatibility.md)
જુઓ, અને OpenClaw-ફેમિલી પ્રાઇમર માટે
[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) જુઓ.

[Perplexity નું numbat](https://github.com/perplexityai/numbat)
એજન્ટ-સિક્યુરિટી ટૂલ ચલાવી રહ્યા છો? ClawMetry તેના ફાઇન્ડિંગ્સ અને
એન્ફોર્સમેન્ટ નિર્ણયોને બોક્સની બહાર જ ઇન્જેસ્ટ કરે છે — જુઓ
[`docs/NUMBAT.md`](docs/NUMBAT.md).

| રનટાઇમ / એજન્ટ | સ્ટેટસ | નોંધ |
|---|---|---|
| **OpenClaw** | નેટિવ | રેફરન્સ રનટાઇમ, ઓટો-ડિટેક્ટેડ |
| **PicoClaw** | બીટા એડેપ્ટર | ફ્લેટ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ. |
| **NanoClaw** | બીટા એડેપ્ટર | પ્રતિ-સેશન SQLite (`data/v2-sessions`). ટ્રાન્સક્રિપ્ટ્સ + મેસેજ કાઉન્ટ્સ. |
| **Hermes** | બીટા એડેપ્ટર | SQLite `~/.hermes/state.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટોકન્સ/કોસ્ટ. |
| **Claude Code** | બીટા એડેપ્ટર | JSONL `~/.claude/projects/.../<id>.jsonl`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ + થિંકિંગ, ટોકન યુસેજ. |
| **Codex** | બીટા એડેપ્ટર | રોલઆઉટ JSONL `~/.codex/sessions/...`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન યુસેજ. |
| **Cursor** | બીટા એડેપ્ટર | SQLite `state.vscdb`. ચેટ/કમ્પોઝર ટ્રાન્સક્રિપ્ટ્સ, મોડેલ. |
| **Aider** | બીટા એડેપ્ટર | પ્રતિ-પ્રોજેક્ટ `.aider.chat.history.md`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટોકન કાઉન્ટ્સ. |
| **Goose** | બીટા એડેપ્ટર | SQLite `~/.local/share/goose`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન ટોટલ્સ. |
| **opencode** | બીટા એડેપ્ટર | SQLite `~/.local/share/opencode`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન્સ + કોસ્ટ. |
| **Qwen Code** | બીટા એડેપ્ટર | JSONL `~/.qwen/projects/.../chats`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન યુસેજ. |
| **Pi** | બીટા એડેપ્ટર | JSONL `~/.pi/agent/sessions`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન્સ + કોસ્ટ. |
| **Deep Agents** | બીટા એડેપ્ટર | SQLite `~/.deepagents/.state/sessions.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન્સ + કોસ્ટ. |
| **n8n** | બીટા એડેપ્ટર | SQLite `~/.n8n/database.sqlite`. વર્કફ્લો એક્ઝિક્યુશન્સ, નોડ રન્સ, AI Agent પ્રોમ્પ્ટ્સ, n8n જ્યાં રેકોર્ડ કરે ત્યાં મોડેલ + ટોકન્સ. |
| **Antigravity** | બીટા એડેપ્ટર | `~/.gemini/<flavor>/brain/` હેઠળ બ્રેઇન JSONL. કન્વર્સેશન્સ, ટૂલ સ્ટેપ્સ, થિંકિંગ, પ્રતિ-જનરેશન Gemini ટોકન વિભાજન + કોસ્ટ, બેકગ્રાઉન્ડ-જનરેશન બર્ન. |

"બીટા એડેપ્ટર" નો અર્થ છે કે ClawMetry તે રનટાઇમના વાસ્તવિક
ઓન-ડિસ્ક ફોર્મેટ માટે એક રીડર શિપ કરે છે, જે દરેક વાસ્તવિક મશીન પર
વાસ્તવિક ઇન્સ્ટોલ સામે બિલ્ટ + વેરિફાઇડ છે (જુઓ
`tests/fixtures/runtimes/<rt>/`). એડેપ્ટર્સ રીડ-ઓન્લી છે; દરેક તેના
રનટાઇમ ખરેખર શું સ્ટોર કરે છે તે વિશે પ્રામાણિક છે (દા.ત.
PicoClaw/NanoClaw/Cursor ડિસ્ક પર ટોકન કોસ્ટ લખતા નથી). જ્યારે એક નોડ
પર ઘણા રનટાઇમ્સ ચાલે છે, ત્યારે રનટાઇમ સ્વિચર ક્લીન ડીપ-ડાઇવ માટે
સેશન્સ વ્યૂને એક પર સ્કોપ કરે છે.

## કોઈપણ SDK એજન્ટ ટ્રેક કરો — આઉટ-લૂપ કોસ્ટ એટ્રિબ્યુશન

ઉપરના રનટાઇમ્સ બધા ડિસ્ક પર સેશન્સ લખે છે. તમારો પોતાનો **પ્રોડક્શન
એજન્ટ** — જે તમે OpenAI Agents SDK, LangChain, Vercel AI SDK,
LlamaIndex, E2B, અથવા સાદા `httpx` લૂપ પર બનાવ્યો છે — તે લખતો નથી.
ClawMetry નું ઝીરો-કન્ફિગ ઇન્ટરસેપ્ટર `httpx`/`requests` ને
મંકી-પેચ કરીને પણ તેના LLM કૉલ્સ (કોસ્ટ, ટોકન્સ, લેટન્સી, એરર્સ)
કેપ્ચર કરે છે:

```python
import clawmetry.track            # ઇન્ટરસેપ્ટર સક્રિય કરો
clawmetry.track.set_source("support-agent")   # આ પ્રોડક્ટનું નામ આપો

# ...તમારો એજન્ટ સામાન્ય રીતે ચાલે છે; દરેક LLM કૉલ હવે ટ્રેક + એટ્રિબ્યુટેડ છે.
```

`set_source()` (અથવા `CLAWMETRY_SOURCE=support-agent` env var) દરેક
કૉલને એક **નામવાળા સોર્સ** સાથે ટેગ કરે છે, જેથી તમે ચલાવો છો તે દરેક
પ્રોડક્ટ ડેશબોર્ડના Overview પરના **🔌 Out-loop sources** કાર્ડમાં
પોતાની ફર્સ્ટ-ક્લાસ, કોસ્ટ-એટ્રિબ્યુટેબલ લાઇન તરીકે દેખાય છે — પ્રતિ
એજન્ટ કૉલ્સ, પ્રોવાઇડર્સ, લેટન્સી, એરર રેટ. કોઈ સોર્સ સેટ ન કર્યો?
કૉલ્સ હજુ પણ ટ્રેક થાય છે; ફક્ત કાર્ડ છુપાયેલું રહે છે.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

આ એ જ ડેટા લેયર છે જે રનટાઇમ એડેપ્ટર્સ ફીડ કરે છે (DuckDB → ક્લાઉડ
સ્નેપશોટ), તેથી આઉટ-લૂપ સોર્સિસ બાકીના બધા ડેટાની જેમ જ ક્લાઉડ
ડેશબોર્ડમાં સિંક થાય છે, E2E-એન્ક્રિપ્ટેડ.

## OpenTelemetry — વેન્ડર-ન્યુટ્રલ, તમારા ટ્રેસ ગમે ત્યાં મોકલો

ClawMetry બંને દિશામાં **OpenTelemetry** બોલે છે, **GenAI સિમેન્ટિક
કન્વેન્શન્સ** નો ઉપયોગ કરીને, જેથી તમારા એજન્ટ ટ્રેસ ક્યારેય એક ટૂલમાં
લૉક ન થાય.

દરેક સેશન — LLM કૉલ્સ, ટૂલ્સ, સબ-એજન્ટ્સ, ટોકન્સ, કોસ્ટ — ને કોઈપણ
કલેક્ટર (Datadog, Grafana, Honeycomb, અથવા તમારો પોતાનો OTel
Collector) માટે OTLP/HTTP GenAI સ્પાન્સ તરીકે **એક્સપોર્ટ** કરો:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# સમાનરૂપે:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ઓથ હેડર્સ અને પોલ ઇન્ટરવલ વૈકલ્પિક env vars છે:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # વધારાના HTTP હેડર્સ
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # સેકન્ડ્સ (ડિફોલ્ટ 60)
```

**ઇન્જેસ્ટ** — બિલ્ટ-ઇન OTLP રિસીવર `/v1/traces` અને `/v1/metrics` પર
બીજા કોઈપણમાંથી ટ્રેસ અને મેટ્રિક્સ સ્વીકારે છે (protobuf ઇન્જેસ્ટ
માટે `pip install clawmetry[otel]`).

તમને ઝીરો-કન્ફિગ, લોકલ-ફર્સ્ટ ClawMetry ડેશબોર્ડ **અને** તમારી ટીમ
પહેલેથી ચલાવે છે તે ગમે તે બેકએન્ડમાં તમારો ડેટા મળે છે — કોઈ લૉક-ઇન
નહીં, બીજો એજન્ટ ઇન્સ્ટોલ કરવાની જરૂર નહીં.

## કન્ફિગરેશન

મોટાભાગના લોકોને કોઈ કન્ફિગની જરૂર નથી. ClawMetry તમારું વર્કસ્પેસ,
લોગ્સ, સેશન્સ અને ક્રોન્સ ઓટો-ડિટેક્ટ કરે છે.

જો તમારે કસ્ટમાઇઝ કરવાની જરૂર હોય:

```bash
clawmetry --port 9000              # કસ્ટમ પોર્ટ (ડિફોલ્ટ: 8900)
clawmetry --host 127.0.0.1         # ફક્ત લોકલહોસ્ટ સાથે બાઇન્ડ કરો
clawmetry --workspace ~/mybot      # કસ્ટમ વર્કસ્પેસ પાથ
clawmetry --name "Alice"           # Flow વિઝ્યુલાઇઝેશનમાં તમારું નામ
```

બધા વિકલ્પો: `clawmetry --help`

## સપોર્ટેડ ચેનલ્સ

ClawMetry તમે કન્ફિગર કરેલી દરેક OpenClaw ચેનલ માટે લાઇવ એક્ટિવિટી
દર્શાવે છે. ફક્ત તમારા `openclaw.json` માં ખરેખર સેટ અપ કરેલી ચેનલો
જ Flow ડાયાગ્રામમાં દેખાય છે — કન્ફિગર ન કરેલી ચેનલો આપોઆપ છુપાયેલી
રહે છે.

Flow માં કોઈપણ ચેનલ નોડ પર ક્લિક કરો જેથી ઇનકમિંગ/આઉટગોઇંગ મેસેજ
કાઉન્ટ્સ સાથે લાઇવ ચેટ બબલ વ્યૂ જોઈ શકાય.

| ચેનલ | સ્ટેટસ | લાઇવ પોપઅપ | નોંધ |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ સંપૂર્ણ | ✅ | મેસેજીસ, સ્ટેટ્સ, 10s રિફ્રેશ |
| 💬 **iMessage** | ✅ સંપૂર્ણ | ✅ | `~/Library/Messages/chat.db` સીધું વાંચે છે |
| 💚 **WhatsApp** | ✅ સંપૂર્ણ | ✅ | WhatsApp Web (Baileys) દ્વારા |
| 🔵 **Signal** | ✅ સંપૂર્ણ | ✅ | signal-cli દ્વારા |
| 🟣 **Discord** | ✅ સંપૂર્ણ | ✅ | ગિલ્ડ + ચેનલ ડિટેક્શન |
| 🟪 **Slack** | ✅ સંપૂર્ણ | ✅ | વર્કસ્પેસ + ચેનલ ડિટેક્શન |
| 🌐 **Webchat** | ✅ સંપૂર્ણ | ✅ | બિલ્ટ-ઇન વેબ UI સેશન્સ |
| 📡 **IRC** | ✅ સંપૂર્ણ | ✅ | ટર્મિનલ-સ્ટાઇલ બબલ UI |
| 🍏 **BlueBubbles** | ✅ સંપૂર્ણ | ✅ | BlueBubbles REST API દ્વારા iMessage |
| 🔵 **Google Chat** | ✅ સંપૂર્ણ | ✅ | Chat API વેબહૂક્સ દ્વારા |
| 🟣 **MS Teams** | ✅ સંપૂર્ણ | ✅ | Teams બોટ પ્લગઇન દ્વારા |
| 🔷 **Mattermost** | ✅ સંપૂર્ણ | ✅ | સેલ્ફ-હોસ્ટેડ ટીમ ચેટ |
| 🟩 **Matrix** | ✅ સંપૂર્ણ | ✅ | ડિસેન્ટ્રલાઇઝ્ડ, E2EE સપોર્ટ |
| 🟢 **LINE** | ✅ સંપૂર્ણ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ સંપૂર્ણ | ✅ | ડિસેન્ટ્રલાઇઝ્ડ NIP-04 DMs |
| 🟣 **Twitch** | ✅ સંપૂર્ણ | ✅ | IRC કનેક્શન દ્વારા ચેટ |
| 🔷 **Feishu/Lark** | ✅ સંપૂર્ણ | ✅ | WebSocket ઇવેન્ટ સબસ્ક્રિપ્શન |
| 🔵 **Zalo** | ✅ સંપૂર્ણ | ✅ | Zalo Bot API |

> **ઓટો-ડિટેક્શન:** ClawMetry તમારો `~/.openclaw/openclaw.json` વાંચે
> છે અને ફક્ત તમે ખરેખર કન્ફિગર કરેલી ચેનલો જ રેન્ડર કરે છે. કોઈ
> મેન્યુઅલ સેટઅપની જરૂર નથી.

## Docker ડિપ્લોયમેન્ટ

ClawMetry ને કન્ટેનરમાં ચલાવવા માંગો છો? કોઈ સમસ્યા નથી! 🐳

**Docker સાથે ક્વિક સ્ટાર્ટ:**

```bash
# ઇમેજ બિલ્ડ કરો
docker build -t clawmetry .

# ડિફોલ્ટ સેટિંગ્સ સાથે ચલાવો
docker run -p 8900:8900 clawmetry

# અથવા તમારા એજન્ટની ડેટા ડિર માઉન્ટ કરો (દર્શાવેલ: OpenClaw નું ~/.openclaw)
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
- Flask (pip દ્વારા આપોઆપ ઇન્સ્ટોલ થાય છે)
- એ જ મશીન પર એક AI એજન્ટ રનટાઇમ: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, અથવા Antigravity (અથવા Docker માટે માઉન્ટેડ વોલ્યુમ્સ)
- Linux અથવા macOS

## NemoClaw / OpenShell સપોર્ટ

ClawMetry [NemoClaw](https://github.com/NVIDIA/NemoClaw) ને આપોઆપ
ડિટેક્ટ કરે છે — NVIDIA નું એન્ટરપ્રાઇઝ સિક્યુરિટી રેપર જે OpenClaw
માટે છે અને એજન્ટ્સને સેન્ડબોક્સ્ડ OpenShell કન્ટેનર્સની અંદર ચલાવે
છે.

મોટાભાગના કિસ્સાઓમાં કોઈ વધારાનું કન્ફિગરેશન જરૂરી નથી. સિંક ડિમન
સેશન ફાઇલો ઓટો-ડિસ્કવર કરે છે, ભલે તે હોસ્ટ પર `~/.openclaw/` માં
રહેતી હોય કે OpenShell કન્ટેનરની અંદર.

### તે કેવી રીતે કામ કરે છે

ClawMetry બે રીતે NemoClaw ડિટેક્ટ કરે છે:

1. **બાઇનરી ડિટેક્શન** — `nemoclaw` CLI માટે તપાસ કરે છે અને સેન્ડબોક્સ
   માહિતી મેળવવા `nemoclaw status` ચલાવે છે
2. **કન્ટેનર ડિટેક્શન** — `openshell`, `nemoclaw`, અથવા
   `ghcr.io/nvidia/` ઇમેજીસ માટે ચાલી રહેલા Docker કન્ટેનર્સ સ્કેન
   કરે છે, પછી વોલ્યુમ માઉન્ટ્સ અથવા `docker cp` દ્વારા સેશન્સ વાંચે
   છે

NemoClaw કન્ટેનર્સમાંથી સિંક કરેલી સેશન ફાઇલોને ક્લાઉડ ડેશબોર્ડમાં
`runtime=nemoclaw` અને `container_id` મેટાડેટા સાથે ટેગ કરવામાં આવે
છે, જેથી તમે તેમને એક નજરમાં સ્ટાન્ડર્ડ OpenClaw સેશન્સથી અલગ પાડી
શકો.

### ભલામણ કરેલ સેટઅપ: HOST પર સિંક ડિમન

શ્રેષ્ઠ અનુભવ માટે, ClawMetry નો સિંક ડિમન **હોસ્ટ મશીન** પર ચલાવો
(સેન્ડબોક્સની અંદર નહીં). આનાથી NemoClaw નેટવર્ક પોલિસી પ્રતિબંધો
ટાળી શકાય છે.

```bash
# હોસ્ટ પર (સેન્ડબોક્સની બહાર)
pip install clawmetry
clawmetry connect
clawmetry sync
```

સિંક ડિમન કોઈપણ ચાલી રહેલા OpenShell કન્ટેનર્સની અંદર સેશન્સ આપોઆપ
શોધી કાઢશે.

### વૈકલ્પિક: સ્પષ્ટ સેન્ડબોક્સ નામ

જો ઓટો-ડિટેક્શન કામ ન કરે, તો ClawMetry ને યોગ્ય સેન્ડબોક્સ તરફ
દર્શાવો:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### સેન્ડબોક્સની અંદર ચલાવવું (એડવાન્સ્ડ)

જો તમારે સિંક ડિમન **OpenShell સેન્ડબોક્સની અંદર** જ ચલાવવો પડે, તો
ClawMetry ingest API સુધી પહોંચી શકે તે માટે તમારી NemoClaw નેટવર્ક
પોલિસીમાં આ egress નિયમ ઉમેરો:

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

### પોર્ટ્સ અને એન્ડપોઇન્ટ્સ

| એન્ડપોઇન્ટ | પોર્ટ | પ્રોટોકોલ | જરૂરી |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | હા (સિંક ડિમન → ક્લાઉડ) |
| `localhost:8900` | 8900 | HTTP | હા (લોકલ ડેશબોર્ડ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | કન્ટેનર સેશન ડિસ્કવરી માટે |

સિંક ડિમન ફક્ત `ingest.clawmetry.com` તરફ આઉટબાઉન્ડ HTTPS કૉલ્સ કરે
છે. કોઈ ઇનબાઉન્ડ પોર્ટ્સ જરૂરી નથી.

---

## ક્લાઉડ ડિપ્લોયમેન્ટ

SSH ટનલ્સ, રિવર્સ પ્રોક્સી, અને Docker માટે
**[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**
જુઓ.

## ટેસ્ટિંગ

આ પ્રોજેક્ટ BrowserStack સાથે ટેસ્ટ કરવામાં આવે છે.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ટેલિમેટ્રી

ClawMetry `https://app.clawmetry.com/api/install` પર અનામી
ઇન્સ્ટોલ-લાઇફસાયકલ પિંગ્સ મોકલે છે: નવા મશીન પર પ્રથમ વખત `clawmetry`
CLI ચલાવો ત્યારે એક `install` પિંગ, નવા વર્ઝન પર અપગ્રેડ કર્યા પછીના
પ્રથમ રન પર એક `update` પિંગ, અને તમે ડેશબોર્ડની અંદરની ઓનબોર્ડિંગ
પસંદગી પૂરી કરો ત્યારે એક `onboarded` પિંગ. અમે આનો ઉપયોગ વાસ્તવિક
ઇન્સ્ટોલ્સ ગણવા માટે કરીએ છીએ (કાચા PyPI ડાઉનલોડ નંબર્સ ~98% મિરર્સ,
CI, અને ઓટો-અપડેટ રી-ડાઉનલોડ્સ છે) અને એ જાણવા માટે કે વાસ્તવમાં કયા
એજન્ટ ફ્રેમવર્ક્સ અને વર્ઝન્સ ઉપયોગમાં છે.

**દરેક વર્ઝન દીઠ દરેક લાઇફસાયકલ ઇવેન્ટ માટે વધુમાં વધુ એક POST**,
જેમાં આ સમાવેશ થાય છે:

| ફિલ્ડ | ઉદાહરણ | શા માટે |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` પર સંગ્રહિત રેન્ડમ UUID | ડિડુપ; જ્યાં સુધી તમે સ્પષ્ટપણે Cloud sync કનેક્ટ ન કરો ત્યાં સુધી અનામી (ત્યારબાદ ઓથેન્ટિકેટેડ ડિમન હાર્ટબીટ તેને લઈ જાય છે, આ ઇન્સ્ટોલને તમારા એકાઉન્ટ સાથે લિંક કરે છે) |
| `event` | `install` / `update` / `onboarded` | નવું ઇન્સ્ટોલ vs હાલના એકનું અપગ્રેડ |
| `version` | `0.12.167` | ઉપયોગમાં કયા વર્ઝન્સ છે |
| `os` / `os_version` | `Darwin` / `25.3.0` | પ્લેટફોર્મ સપોર્ટ પ્રાયોરિટીઝ |
| `python` | `3.11.15` | Python વર્ઝન સપોર્ટ મેટ્રિક્સ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | આગળ કયા એજન્ટ્સ સાથે અમારે ઇન્ટિગ્રેટ કરવું જોઈએ |
| `is_ci` / `ci_provider` | `true` / `github_actions` | માનવ ઇન્સ્ટોલ્સને CI નોઇઝથી અલગ કરવા |

**અમે શું નથી મોકલતા**: IP (ક્લાઉડ સર્વર-સાઇડ પર રિક્વેસ્ટમાંથી
દેશ કોડ મેળવે છે, પછી IP ડિસ્કાર્ડ કરે છે), હોસ્ટનેમ, યુઝરનેમ,
વર્કસ્પેસ પાથ, ફાઇલ કન્ટેન્ટ્સ, તમારી api_key, તમારો ઇમેઇલ, કંઈપણ
PII અથવા વર્કસ્પેસ-સ્પેસિફિક. વાયર પેલોડ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) માં ઓડિટેબલ છે.

**ઓપ્ટ આઉટ** (આમાંથી કોઈપણ એક તેને કાયમ માટે નિષ્ક્રિય કરે છે):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # પ્રતિ-શેલ
export DO_NOT_TRACK=1                          # W3C ક્રોસ-ટૂલ સ્ટાન્ડર્ડ
touch ~/.clawmetry/notelemetry                 # પર્સિસ્ટન્ટ ફાઇલ માર્કર
```

નેટવર્ક ફેલ્યોર ક્યારેય `clawmetry` ને ચાલવાથી બ્લોક નથી કરતું —
પિંગ ડિમન થ્રેડ પર 3s ટાઇમઆઉટ સાથે ફાયર-એન્ડ-ફર્ગેટ છે.

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> દ્વારા બનાવેલ · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ઇકોસિસ્ટમનો ભાગ</sub>
</p>
