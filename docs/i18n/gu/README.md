<!-- i18n-src:7cfb63716507 -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**તમારા એજન્ટને વિચારતું જુઓ.** **14 AI એજન્ટ રનટાઇમ્સ** માટે રિયલ-ટાઇમ ઓબ્ઝર્વેબિલિટી: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex અને બીજા 10. તમારા સમગ્ર એજન્ટ ફ્લીટ માટે એક જ ડેશબોર્ડ.

> 🌐 **આ ભાષામાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. ઝીરો કન્ફિગ. બધું જ ઓટો-ડિટેક્ટ કરે છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે અને તમારું કામ પૂરું.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 એજન્ટ રનટાઇમ્સ સાથે કામ કરે છે

ClawMetry ની શરૂઆત OpenClaw માટે ઓબ્ઝર્વેબિલિટી તરીકે થઈ હતી, અને હવે તે તમારા **સમગ્ર એજન્ટ ફ્લીટ**ને એક જ ડેશબોર્ડમાં માપે છે, તમારા મશીન પર દરેક રનટાઇમને ઓટો-ડિટેક્ટ કરીને:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw અને NemoClaw ઓપન-સોર્સ એપમાં મફત છે; બાકીના રનટાઇમ્સ ClawMetry Cloud અથવા સેલ્ફ-હોસ્ટેડ Pro લાયસન્સ સાથે સક્રિય થાય છે. હેડરમાંથી રનટાઇમ બદલો અને દરેક ટેબ, ખર્ચ, ટોકન્સ, ટૂલ્સ, ટ્રેસ, તે રનટાઇમ પ્રમાણે ફરી ગોઠવાય છે. ચોક્કસ મફત/પેઇડ વિભાજન, ટિયર મેટ્રિક્સ, `/api/entitlement` શેપ, અને `clawmetry license` CLI માટે **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** જુઓ.

## તમને શું મળે છે

- **Flow** — ચેનલો, બ્રેઇન, ટૂલ્સ અને પાછા મારફતે વહેતા સંદેશાઓ દર્શાવતું લાઇવ એનિમેટેડ ડાયાગ્રામ
- **Overview** — હેલ્થ ચેક્સ, એક્ટિવિટી હીટમેપ, સેશન કાઉન્ટ્સ, મોડેલ માહિતી
- **Usage** — દૈનિક/સાપ્તાહિક/માસિક બ્રેકડાઉન સાથે ટોકન અને ખર્ચ ટ્રેકિંગ
- **Sessions** — મોડેલ, ટોકન્સ, છેલ્લી પ્રવૃત્તિ સાથે સક્રિય એજન્ટ સેશન્સ
- **Crons** — સ્ટેટસ, આગામી રન, ડ્યુરેશન સાથે શેડ્યુલ્ડ જોબ્સ
- **Logs** — કલર-કોડેડ રિયલ-ટાઇમ લોગ સ્ટ્રીમિંગ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, દૈનિક નોંધો બ્રાઉઝ કરો
- **Transcripts** — સેશન હિસ્ટ્રી વાંચવા માટે ચેટ-બબલ UI
- **Alerts** — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, એજન્ટ-ઓફલાઇન ડિટેક્શન; Slack, Discord, PagerDuty, Telegram, Email પર રૂટ કરે છે
- **Approvals** — ડિસ્ટ્રક્ટિવ ડિલીટ્સ, ફોર્સ પુશ, DB મ્યુટેશન્સ, sudo, પેકેજ ઇન્સ્ટોલ્સ, નેટવર્ક કૉલ્સને એક-ક્લિક સાઇન-ઓફ પાછળ ગેટ કરો

## સ્ક્રીનશોટ્સ

### 🧠 Brain — લાઇવ એજન્ટ ઇવેન્ટ સ્ટ્રીમ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ટોકન વપરાશ અને સેશન સારાંશ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — રિયલ-ટાઇમ ટૂલ કૉલ ફીડ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — મોડેલ અને સેશન પ્રમાણે ખર્ચ બ્રેકડાઉન
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — વર્કસ્પેસ ફાઇલ બ્રાઉઝર
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — સ્થિતિ અને ઓડિટ લોગ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, Slack / Discord / PagerDuty / Email પર વેબહુક્સ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — જોખમી ટૂલ કૉલ્સને મેન્યુઅલ સાઇન-ઓફ પાછળ ગેટ કરો; પોલિસી-બેક્ડ પ્રોટેક્શન નિયમો
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code માટે પ્રી-એક્ઝિક્યુશન બ્લોકિંગ** — એક કમાન્ડ એક
PreToolUse હૂક ઇન્સ્ટોલ કરે છે જે મેચ થતા ટૂલ કૉલ્સને તે *ચાલે તે પહેલાં*
રોકે છે અને તમારા નિર્ણયની રાહ જુએ છે (તમારા ફોનથી એક ટૅપમાં
[ક્લાઉડ પુશ નોટિફિકેશન્સ](https://app.clawmetry.com/push) સક્રિય હોય ત્યારે):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

એક ડિનાય ફક્ત તે એક ટૂલ કૉલને બ્લોક કરે છે — એજન્ટ પોતાનું સેશન જાળવી રાખે
છે અને બીજો અભિગમ અજમાવી શકે છે. તમારા ફોન પર મંજૂરી આપવાથી Claude Code
ની પોતાની પરમિશન પ્રોમ્પ્ટ સ્કિપ થાય છે (તમે પહેલેથી જ જવાબ આપી દીધો છે).
અમેચ ન થયેલા ટૂલ્સનો ખર્ચ ~40ms જેટલો છે અને તે Claude Code ના સામાન્ય
પરમિશન ફ્લોમાં જ ચાલ્યા જાય છે. જ્યારે Claude Code પોતે તમારી રાહ જોતું
હોય ત્યારે પણ તમને ફોન પુશ મળે છે (`permission_prompt` /
`idle_prompt` નોટિફિકેશન્સ).

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

v2 React એપ `frontend/` માં રહે છે અને Flask સર્વર v2 સક્રિય કરીને
શરૂ કરવામાં આવે ત્યારે `/v2` પર સર્વ થાય છે.

ડેવલપ કરતી વખતે બે ટર્મિનલ્સનો ઉપયોગ કરો:

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
CORS સેટઅપ વિના લોકલ Flask સર્વર સાથે વાત કરી શકે.

Python પેકેજ સાથે શિપ થતું બંડલ બિલ્ડ કરવા માટે:

```bash
cd frontend
npm run build
```

પ્રોડક્શન બંડલ `clawmetry/static/v2/dist/` માં લખવામાં આવે છે.

## રનટાઇમ / એજન્ટ સુસંગતતા

ClawMetry ફક્ત OpenClaw જ નહીં, પણ ઘણા AI-એજન્ટ રનટાઇમ્સનું અવલોકન કરે
છે. દરેક નોન-OpenClaw રનટાઇમ એક સમર્પિત રીડર એડેપ્ટર શિપ કરે છે જે તેના
મૂળ સેશન ફોર્મેટને ClawMetry ના યુનિફાઇડ શેપ્સમાં ટ્રાન્સલેટ કરે છે;
ડિમન તેમને એ જ DuckDB સ્ટોર + ક્લાઉડ સ્નેપશોટમાં ઇન્જેસ્ટ કરે છે, રનટાઇમ
સાથે ટૅગ કરીને, અને એકથી વધુ રનટાઇમ હાજર હોય ત્યારે Session replay ટેબ
એક **રનટાઇમ સ્વિચર** બતાવે છે. સંપૂર્ણ મેટ્રિક્સ + રનટાઇમ્સ ઉમેરવાની
ગાઇડ માટે [`docs/compatibility.md`](docs/compatibility.md) જુઓ, અને
OpenClaw-ફેમિલી પ્રાઇમર માટે [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) જુઓ.

[Perplexity નું numbat](https://github.com/perplexityai/numbat) એજન્ટ-સિક્યુરિટી ટૂલ ચલાવો છો? ClawMetry તેના તારણો અને
એન્ફોર્સમેન્ટ નિર્ણયોને શરૂઆતથી જ ઇન્જેસ્ટ કરે છે — [`docs/NUMBAT.md`](docs/NUMBAT.md) જુઓ.

| રનટાઇમ / એજન્ટ | સ્થિતિ | નોંધો |
|---|---|---|
| **OpenClaw** | નેટિવ | સંદર્ભ રનટાઇમ, ઓટો-ડિટેક્ટેડ |
| **PicoClaw** | બીટા એડેપ્ટર | ફ્લેટ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ. |
| **NanoClaw** | બીટા એડેપ્ટર | પ્રતિ-સેશન SQLite (`data/v2-sessions`). ટ્રાન્સક્રિપ્ટ્સ + મેસેજ કાઉન્ટ્સ. |
| **Hermes** | બીટા એડેપ્ટર | SQLite `~/.hermes/state.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટોકન્સ/ખર્ચ. |
| **Claude Code** | બીટા એડેપ્ટર | JSONL `~/.claude/projects/.../<id>.jsonl`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ + થિંકિંગ, ટોકન વપરાશ. |
| **Codex** | બીટા એડેપ્ટર | Rollout JSONL `~/.codex/sessions/...`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન વપરાશ. |
| **Cursor** | બીટા એડેપ્ટર | SQLite `state.vscdb`. ચેટ/કમ્પોઝર ટ્રાન્સક્રિપ્ટ્સ, મોડેલ. |
| **Aider** | બીટા એડેપ્ટર | પ્રતિ-પ્રોજેક્ટ `.aider.chat.history.md`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટોકન કાઉન્ટ્સ. |
| **Goose** | બીટા એડેપ્ટર | SQLite `~/.local/share/goose`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન ટોટલ્સ. |
| **opencode** | બીટા એડેપ્ટર | SQLite `~/.local/share/opencode`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન્સ + ખર્ચ. |
| **Qwen Code** | બીટા એડેપ્ટર | JSONL `~/.qwen/projects/.../chats`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન વપરાશ. |
| **Pi** | બીટા એડેપ્ટર | JSONL `~/.pi/agent/sessions`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન્સ + ખર્ચ. |
| **Deep Agents** | બીટા એડેપ્ટર | SQLite `~/.deepagents/.state/sessions.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડેલ, ટૂલ કૉલ્સ, ટોકન્સ + ખર્ચ. |
| **n8n** | બીટા એડેપ્ટર | SQLite `~/.n8n/database.sqlite`. વર્કફ્લો એક્ઝિક્યુશન્સ, નોડ રન્સ, AI Agent પ્રોમ્પ્ટ્સ, n8n જ્યાં રેકોર્ડ કરે ત્યાં મોડેલ + ટોકન્સ. |
| **Antigravity** | બીટા એડેપ્ટર | `~/.gemini/<flavor>/brain/` હેઠળ Brain JSONL. વાતચીતો, ટૂલ સ્ટેપ્સ, થિંકિંગ, પ્રતિ-જનરેશન Gemini ટોકન સ્પ્લિટ + ખર્ચ, બેકગ્રાઉન્ડ-જનરેશન બર્ન. |
| **GitHub Copilot** | બીટા એડેપ્ટર | Copilot CLI `events.jsonl` `~/.copilot/session-state/` હેઠળ + `session-store.db` પ્રતિ-કૉલ વપરાશ લેજર. વાતચીતો, ટૂલ કૉલ્સ, મોડેલ રાઉટિંગ, કેશ-અવેર ટોકન સ્પ્લિટ, વેન્ડર-બિલ્ડ AI-ક્રેડિટ ખર્ચ. |
| **Grok** | બીટા એડેપ્ટર | xAI Grok Build CLI (Rust બાઇનરી `~/.grok/bin/grok` હેઠળ): ગ્લોબલ ઇવેન્ટ લોગ `~/.grok/logs/unified.jsonl` + પ્રતિ-સેશન `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. વાતચીતો, પ્રતિ-ટર્ન ટોકન સ્પ્લિટ, મોડેલ રાઉટિંગ, અને CLI નું આઉટબાઉન્ડ રિપો પેલોડ જે `~/.grok/upload_queue/` હેઠળ સ્ટેજ થાય છે જેથી તમે જોઈ શકો કે તમારા મશીનમાંથી શું બહાર ગયું. |

"બીટા એડેપ્ટર" નો અર્થ છે કે ClawMetry તે રનટાઇમના વાસ્તવિક ડિસ્ક-ફોર્મેટ
માટે એક રીડર શિપ કરે છે, દરેક વાસ્તવિક મશીન પર વાસ્તવિક ઇન્સ્ટોલ સામે
બિલ્ડ + વેરિફાય કરેલ (જુઓ `tests/fixtures/runtimes/<rt>/`). એડેપ્ટર્સ
રીડ-ઓન્લી છે; દરેક પોતાના રનટાઇમ ખરેખર શું સ્ટોર કરે છે તે અંગે
પ્રમાણિક છે (દા.ત. PicoClaw/NanoClaw/Cursor ડિસ્ક પર ટોકન ખર્ચ લખતા
નથી). એક નોડ પર અનેક રનટાઇમ્સ ચાલતાં હોય ત્યારે, રનટાઇમ સ્વિચર
સેશન્સ વ્યૂને એક ડીપ-ડાઇવ માટે એક જ પર સ્કોપ કરે છે.

## કોઈપણ SDK એજન્ટને ટ્રેક કરો — આઉટ-લૂપ કોસ્ટ એટ્રિબ્યુશન

ઉપરોક્ત રનટાઇમ્સ બધા સેશન્સ ડિસ્ક પર લખે છે. તમારો પોતાનો **પ્રોડક્શન
એજન્ટ** — જે તમે OpenAI Agents SDK, LangChain, Vercel AI SDK,
LlamaIndex, E2B, અથવા સાદા `httpx` લૂપ પર બનાવ્યો છે — તે નથી કરતો.
ClawMetry નું ઝીરો-કન્ફિગ ઇન્ટરસેપ્ટર `httpx`/`requests` ને
મંકી-પેચ કરીને હજુ પણ તેના LLM કૉલ્સ (ખર્ચ, ટોકન્સ, લેટન્સી, એરર્સ)
કૅપ્ચર કરે છે:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (અથવા `CLAWMETRY_SOURCE=support-agent` એન્વ વેરિયેબલ)
દરેક કૉલને એક **નામવાળા સોર્સ** સાથે ટૅગ કરે છે, જેથી તમે ચલાવો છો
તે દરેક પ્રોડક્ટ ડેશબોર્ડના Overview પરના **🔌 Out-loop sources**
કાર્ડમાં પોતાની ફર્સ્ટ-ક્લાસ, ખર્ચ-એટ્રિબ્યુટેબલ લાઇન તરીકે દેખાય
છે — કૉલ્સ, પ્રોવાઇડર્સ, લેટન્સી, પ્રતિ-એજન્ટ એરર રેટ. કોઈ સોર્સ
સેટ ન કર્યો? કૉલ્સ હજુ પણ ટ્રેક થાય છે; ફક્ત કાર્ડ છુપાયેલું રહે છે.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

આ એ જ ડેટા લેયર છે જે રનટાઇમ એડેપ્ટર્સ ફીડ કરે છે (DuckDB →
ક્લાઉડ સ્નેપશોટ), તેથી આઉટ-લૂપ સોર્સ પણ બાકીની જેમ, E2E-એન્ક્રિપ્ટેડ
રીતે ક્લાઉડ ડેશબોર્ડ સાથે સિંક થાય છે.

## OpenTelemetry — વેન્ડર-ન્યુટ્રલ, તમારા ટ્રેસ ગમે ત્યાં મોકલો

ClawMetry બંને દિશામાં **OpenTelemetry** બોલે છે, **GenAI સિમેન્ટિક
કન્વેન્શન્સ** નો ઉપયોગ કરીને, જેથી તમારા એજન્ટ ટ્રેસ ક્યારેય એક જ
ટૂલમાં લોક ન થાય.

**નિકાસ** — દરેક સેશન, LLM કૉલ્સ, ટૂલ્સ, સબ-એજન્ટ્સ, ટોકન્સ, ખર્ચ,
કોઈપણ કલેક્ટર (Datadog, Grafana, Honeycomb, અથવા તમારો પોતાનો OTel
Collector) પર OTLP/HTTP GenAI સ્પાન્સ તરીકે:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth હેડર્સ અને પોલ ઇન્ટરવલ વૈકલ્પિક એન્વ વેરિયેબલ છે:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ઇનજેસ્ટ** — બિલ્ટ-ઇન OTLP રિસીવર `/v1/traces` અને `/v1/metrics` પર
બીજા કોઈપણ સ્રોતમાંથી ટ્રેસ અને મેટ્રિક્સ સ્વીકારે છે (પ્રોટોબફ
ઇનજેસ્ટ માટે `pip install clawmetry[otel]`).

તમને ઝીરો-કન્ફિગ, લોકલ-ફર્સ્ટ ClawMetry ડેશબોર્ડ **અને** તમારી ટીમ
પહેલેથી ચલાવે છે તે કોઈપણ બેકએન્ડમાં તમારો ડેટા મળે છે — કોઈ
લોક-ઇન નહીં, બીજું એજન્ટ ઇન્સ્ટોલ કરવાની જરૂર નહીં.

## કન્ફિગરેશન

મોટાભાગના લોકોને કોઈ કન્ફિગની જરૂર નથી. ClawMetry તમારું વર્કસ્પેસ,
લોગ્સ, સેશન્સ, અને ક્રોન્સ ઓટો-ડિટેક્ટ કરે છે.

જો તમારે કસ્ટમાઇઝ કરવાની જરૂર હોય તો:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

બધા વિકલ્પો: `clawmetry --help`

## સપોર્ટેડ ચેનલો

તમે કન્ફિગર કરેલી દરેક OpenClaw ચેનલ માટે ClawMetry લાઇવ પ્રવૃત્તિ
દર્શાવે છે. તમારા `openclaw.json` માં ખરેખર સેટ થયેલી ચેનલો જ Flow
ડાયાગ્રામમાં દેખાય છે, બિન-કન્ફિગર્ડ ચેનલો આપોઆપ છુપાયેલી રહે છે.

Flow માં કોઈપણ ચેનલ નોડ પર ક્લિક કરીને ઇનકમિંગ/આઉટગોઇંગ મેસેજ
કાઉન્ટ્સ સાથે લાઇવ ચેટ બબલ વ્યૂ જુઓ.

| ચેનલ | સ્થિતિ | લાઇવ પોપઅપ | નોંધો |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ સંપૂર્ણ | ✅ | મેસેજ, સ્ટેટ્સ, 10s રિફ્રેશ |
| 💬 **iMessage** | ✅ સંપૂર્ણ | ✅ | `~/Library/Messages/chat.db` સીધું વાંચે છે |
| 💚 **WhatsApp** | ✅ સંપૂર્ણ | ✅ | WhatsApp Web (Baileys) મારફતે |
| 🔵 **Signal** | ✅ સંપૂર્ણ | ✅ | signal-cli મારફતે |
| 🟣 **Discord** | ✅ સંપૂર્ણ | ✅ | ગિલ્ડ + ચેનલ ડિટેક્શન |
| 🟪 **Slack** | ✅ સંપૂર્ણ | ✅ | વર્કસ્પેસ + ચેનલ ડિટેક્શન |
| 🌐 **Webchat** | ✅ સંપૂર્ણ | ✅ | બિલ્ટ-ઇન વેબ UI સેશન્સ |
| 📡 **IRC** | ✅ સંપૂર્ણ | ✅ | ટર્મિનલ-સ્ટાઇલ બબલ UI |
| 🍏 **BlueBubbles** | ✅ સંપૂર્ણ | ✅ | BlueBubbles REST API મારફતે iMessage |
| 🔵 **Google Chat** | ✅ સંપૂર્ણ | ✅ | Chat API વેબહુક્સ મારફતે |
| 🟣 **MS Teams** | ✅ સંપૂર્ણ | ✅ | Teams બોટ પ્લગિન મારફતે |
| 🔷 **Mattermost** | ✅ સંપૂર્ણ | ✅ | સેલ્ફ-હોસ્ટેડ ટીમ ચેટ |
| 🟩 **Matrix** | ✅ સંપૂર્ણ | ✅ | ડિસેન્ટ્રલાઇઝ્ડ, E2EE સપોર્ટ |
| 🟢 **LINE** | ✅ સંપૂર્ણ | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ સંપૂર્ણ | ✅ | ડિસેન્ટ્રલાઇઝ્ડ NIP-04 DMs |
| 🟣 **Twitch** | ✅ સંપૂર્ણ | ✅ | IRC કનેક્શન મારફતે ચેટ |
| 🔷 **Feishu/Lark** | ✅ સંપૂર્ણ | ✅ | WebSocket ઇવેન્ટ સબસ્ક્રિપ્શન |
| 🔵 **Zalo** | ✅ સંપૂર્ણ | ✅ | Zalo Bot API |

> **ઓટો-ડિટેક્શન:** ClawMetry તમારો `~/.openclaw/openclaw.json`
> વાંચે છે અને તમે ખરેખર કન્ફિગર કરેલી ચેનલો જ રેન્ડર કરે છે.
> મેન્યુઅલ સેટઅપની જરૂર નથી.

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

> **નોંધ:** Docker માં ચલાવતી વખતે, તમારા એજન્ટની ડેટા + લોગ
> ડિરેક્ટરીઓ (દા.ત. `~/.openclaw`, `~/.claude`, `~/.codex`) માઉન્ટ
> કરો જેથી ClawMetry તમારું સેટઅપ ઓટો-ડિટેક્ટ કરી શકે.

## જરૂરિયાતો

- Python 3.8+
- Flask (pip મારફતે આપોઆપ ઇન્સ્ટોલ થાય છે)
- એ જ મશીન પર AI એજન્ટ રનટાઇમ: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, અથવા QM (અથવા Docker માટે માઉન્ટેડ વોલ્યુમ્સ)
- Linux અથવા macOS

## NemoClaw / OpenShell સપોર્ટ

ClawMetry આપોઆપ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ને
ડિટેક્ટ કરે છે — NVIDIA નું એન્ટરપ્રાઇઝ સિક્યુરિટી રેપર જે OpenClaw
માટે છે અને એજન્ટ્સને સેન્ડબોક્સ્ડ OpenShell કન્ટેનર્સની અંદર ચલાવે
છે.

મોટાભાગના કિસ્સાઓમાં કોઈ વધારાના કન્ફિગરેશનની જરૂર નથી. સિંક ડિમન
સેશન ફાઇલો ઓટો-ડિસ્કવર કરે છે, ભલે તે હોસ્ટ પર `~/.openclaw/` માં
હોય કે OpenShell કન્ટેનરની અંદર.

### તે કેવી રીતે કામ કરે છે

ClawMetry બે રીતે NemoClaw ડિટેક્ટ કરે છે:

1. **બાઇનરી ડિટેક્શન** — `nemoclaw` CLI માટે ચેક કરે છે અને સેન્ડબોક્સ
   માહિતી મેળવવા `nemoclaw status` ચલાવે છે
2. **કન્ટેનર ડિટેક્શન** — ચાલી રહેલા Docker કન્ટેનર્સને `openshell`,
   `nemoclaw`, અથવા `ghcr.io/nvidia/` ઇમેજ માટે સ્કેન કરે છે, પછી
   વોલ્યુમ માઉન્ટ્સ અથવા `docker cp` મારફતે સેશન્સ વાંચે છે

NemoClaw કન્ટેનર્સમાંથી સિંક કરેલી સેશન ફાઇલોને ક્લાઉડ ડેશબોર્ડમાં
`runtime=nemoclaw` અને `container_id` મેટાડેટા સાથે ટૅગ કરવામાં આવે
છે, જેથી તમે તેને એક નજરમાં સ્ટાન્ડર્ડ OpenClaw સેશન્સથી અલગ ઓળખી
શકો.

### ભલામણ કરેલ સેટઅપ: HOST પર સિંક ડિમન

શ્રેષ્ઠ અનુભવ માટે, ClawMetry નો સિંક ડિમન **હોસ્ટ મશીન** પર ચલાવો
(સેન્ડબોક્સની અંદર નહીં). આ NemoClaw નેટવર્ક પોલિસી પ્રતિબંધોને ટાળે
છે.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

સિંક ડિમન આપોઆપ કોઈપણ ચાલી રહેલા OpenShell કન્ટેનર્સની અંદરના
સેશન્સ શોધી કાઢશે.

### વૈકલ્પિક: સ્પષ્ટ સેન્ડબોક્સ નામ

જો ઓટો-ડિટેક્શન કામ ન કરે, તો ClawMetry ને યોગ્ય સેન્ડબોક્સ તરફ
નિર્દેશ કરો:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### સેન્ડબોક્સની અંદર ચલાવવું (એડવાન્સ્ડ)

જો તમારે સિંક ડિમન સેન્ડબોક્સની **અંદર** ચલાવવો જ પડે, તો તમારી
NemoClaw નેટવર્ક પોલિસીમાં આ egress નિયમ ઉમેરો જેથી તે ClawMetry
ingest API સુધી પહોંચી શકે:

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

સિંક ડિમન ફક્ત `ingest.clawmetry.com` તરફ આઉટબાઉન્ડ HTTPS કૉલ્સ
કરે છે. કોઈ ઇનબાઉન્ડ પોર્ટ્સની જરૂર નથી.

---

## ક્લાઉડ ડિપ્લોયમેન્ટ

SSH ટનલ્સ, રિવર્સ પ્રોક્સી, અને Docker માટે **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** જુઓ.

## ટેસ્ટિંગ

આ પ્રોજેક્ટ BrowserStack સાથે ટેસ્ટ કરવામાં આવે છે.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ટેલિમેટ્રી

ClawMetry `https://app.clawmetry.com/api/install` પર અનામી
ઇન્સ્ટોલ-લાઇફસાઇકલ પિંગ્સ મોકલે છે: નવા મશીન પર પહેલી વાર `clawmetry`
CLI ચલાવો ત્યારે એક `install` પિંગ, નવા વર્ઝનમાં અપગ્રેડ કર્યા પછી
પહેલી રન વખતે એક `update` પિંગ, અને તમે ડેશબોર્ડની અંદરની
ઓનબોર્ડિંગ પસંદગી પૂર્ણ કરો ત્યારે એક `onboarded` પિંગ. અમે આનો
ઉપયોગ વાસ્તવિક ઇન્સ્ટોલ્સ ગણવા માટે કરીએ છીએ (કાચા PyPI ડાઉનલોડ
નંબર્સ ~98% મિરર્સ, CI, અને ઓટો-અપડેટ રિ-ડાઉનલોડ્સ છે) અને એ જાણવા
માટે કે ખરેખર કયા એજન્ટ ફ્રેમવર્ક્સ અને વર્ઝન્સ ઉપયોગમાં છે.

**પ્રતિ વર્ઝન પ્રતિ લાઇફસાઇકલ ઇવેન્ટ વધુમાં વધુ એક POST**, જેમાં
સમાવેશ થાય છે:

| ફિલ્ડ | ઉદાહરણ | કારણ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` પર સંગ્રહિત રેન્ડમ UUID | ડિડુપ; જ્યાં સુધી તમે સ્પષ્ટપણે Cloud sync કનેક્ટ ન કરો ત્યાં સુધી અનામી (પછી ઓથેન્ટિકેટેડ ડિમન હાર્ટબીટ તેને લઈ જાય છે, આ ઇન્સ્ટોલને તમારા એકાઉન્ટ સાથે લિંક કરે છે) |
| `event` | `install` / `update` / `onboarded` | નવું ઇન્સ્ટોલ vs હાલના ઇન્સ્ટોલનું અપગ્રેડ |
| `version` | `0.12.167` | કયા વર્ઝન્સ ઉપયોગમાં છે |
| `os` / `os_version` | `Darwin` / `25.3.0` | પ્લેટફોર્મ સપોર્ટ પ્રાયોરિટીઝ |
| `python` | `3.11.15` | Python વર્ઝન સપોર્ટ મેટ્રિક્સ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | આગળ કયા એજન્ટ્સ સાથે અમારે ઇન્ટિગ્રેટ કરવું જોઈએ |
| `is_ci` / `ci_provider` | `true` / `github_actions` | માનવ ઇન્સ્ટોલ્સને CI નોઈઝથી અલગ કરવા |

**અમે શું નથી મોકલતા**: IP (ક્લાઉડ સર્વર-સાઇડ પર વિનંતીમાંથી કન્ટ્રી
કોડ મેળવે છે, પછી IP ડિસ્કાર્ડ કરે છે), હોસ્ટનેમ, યુઝરનેમ, વર્કસ્પેસ
પાથ, ફાઇલ કન્ટેન્ટ્સ, તમારી api_key, તમારો ઇમેલ, કોઈપણ PII અથવા
વર્કસ્પેસ-સ્પેસિફિક વસ્તુ. વાયર પેલોડ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) માં ઓડિટ કરી
શકાય તેવો છે.

**ઓપ્ટ આઉટ** (આમાંથી કોઈપણ એક તેને કાયમ માટે અક્ષમ કરે છે):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

નેટવર્ક નિષ્ફળતા `clawmetry` ને ચાલવાથી ક્યારેય રોકતી નથી — પિંગ
3 સેકન્ડના ટાઇમઆઉટ સાથે ડિમન થ્રેડ પર ફાયર-એન્ડ-ફર્ગેટ છે.

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
