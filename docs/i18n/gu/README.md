<!-- i18n-src:c422fb7dd0da -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**તમારા એજન્ટને વિચારતું જુઓ.** **20 AI એજન્ટ રનટાઇમ્સ** માટે રિયલ-ટાઇમ ઓબ્ઝર્વેબિલિટી: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex અને બીજા 16. તમારા આખા એજન્ટ ફ્લીટ માટે એક જ ડેશબોર્ડ.

> 🌐 **આ ભાષામાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. શૂન્ય કન્ફિગ. બધું જ ઓટો-ડિટેક્ટ થાય છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે અને તમારું કામ પૂરું.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 20 એજન્ટ રનટાઇમ્સ સાથે કામ કરે છે

ClawMetry એ OpenClaw માટેની ઓબ્ઝર્વેબિલિટી તરીકે શરૂ થયું, અને હવે તે એક જ ડેશબોર્ડમાં તમારા **આખા એજન્ટ ફ્લીટ**ને મીટર કરે છે, તમારા મશીન પર દરેક રનટાઇમને ઓટો-ડિટેક્ટ કરીને:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw અને NemoClaw ઓપન-સોર્સ એપમાં મફત છે; બાકીના રનટાઇમ્સ ClawMetry Cloud અથવા સેલ્ફ-હોસ્ટેડ Pro લાયસન્સ સાથે સક્રિય થાય છે. હેડરમાંથી રનટાઇમ સ્વિચ કરો અને દરેક ટૅબ, કોસ્ટ, ટોકન્સ, ટૂલ્સ, ટ્રેસ, તે રનટાઇમ પ્રમાણે ફરીથી સ્કોપ થાય છે. ચોક્કસ ફ્રી/પેઇડ સ્પ્લિટ, ટાયર મેટ્રિક્સ, `/api/entitlement` શેપ, અને `clawmetry license` CLI માટે **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** જુઓ.

## તમને શું મળે છે

- **Flow** — ચેનલો, બ્રેઇન, ટૂલ્સ અને પાછા થઈને પસાર થતા મેસેજ બતાવતું લાઇવ એનિમેટેડ ડાયાગ્રામ
- **Overview** — હેલ્થ ચેક્સ, એક્ટિવિટી હીટમેપ, સેશન કાઉન્ટ્સ, મોડલ માહિતી
- **Usage** — દૈનિક/સાપ્તાહિક/માસિક બ્રેકડાઉન સાથે ટોકન અને કોસ્ટ ટ્રેકિંગ
- **Sessions** — મોડલ, ટોકન્સ, છેલ્લી પ્રવૃત્તિ સાથે સક્રિય એજન્ટ સેશન્સ
- **Crons** — સ્ટેટસ, આગામી રન, ડ્યુરેશન સાથે શેડ્યુલ કરેલી જોબ્સ
- **Logs** — કલર-કોડેડ રિયલ-ટાઇમ લોગ સ્ટ્રીમિંગ
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, દૈનિક નોંધો બ્રાઉઝ કરો
- **Transcripts** — સેશન હિસ્ટ્રી વાંચવા માટે ચેટ-બબલ UI
- **Alerts** — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, એજન્ટ-ઑફલાઇન ડિટેક્શન; Slack, Discord, PagerDuty, Telegram, Email પર રૂટ કરે છે
- **Approvals** — વિનાશક ડિલીટ્સ, ફોર્સ પુશ, DB મ્યુટેશન્સ, sudo, પેકેજ ઇન્સ્ટોલ્સ, નેટવર્ક કૉલ્સને એક-ક્લિક સાઇન-ઑફ પાછળ ગેટ કરો

## સ્ક્રીનશોટ્સ

### 🧠 Brain — લાઇવ એજન્ટ ઇવેન્ટ સ્ટ્રીમ
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ટોકન વપરાશ અને સેશન સારાંશ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — રિયલ-ટાઇમ ટૂલ કૉલ ફીડ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — મોડલ અને સેશન પ્રમાણે કોસ્ટ બ્રેકડાઉન
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — વર્કસ્પેસ ફાઇલ બ્રાઉઝર
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — પોસ્ચર અને ઓડિટ લોગ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — બજેટ કેપ્સ, એરર-રેટ ટ્રિગર્સ, Slack / Discord / PagerDuty / Email માટે વેબહૂક્સ
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — જોખમી ટૂલ કૉલ્સને મેન્યુઅલ સાઇન-ઑફ પાછળ ગેટ કરો; પોલિસી-બેક્ડ પ્રોટેક્શન નિયમો
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code માટે પ્રી-એક્ઝિક્યુશન બ્લોકિંગ** — એક કમાન્ડ એક PreToolUse
હૂક ઇન્સ્ટોલ કરે છે જે મેચ થતા ટૂલ કૉલ્સને તે *ચાલે તે પહેલાં* થોભાવે છે અને
તમારા નિર્ણયની રાહ જુએ છે ([cloud push notifications](https://app.clawmetry.com/push)
સક્રિય કરેલ હોય તો તમારા ફોનથી એક ટૅપમાં):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

એક ડિનાય ફક્ત તે એક ટૂલ કૉલને જ બ્લોક કરે છે, એજન્ટ પોતાનું સેશન રાખે
છે અને બીજો અભિગમ અજમાવી શકે છે. તમારા ફોન પર એપ્રૂવ કરવાથી Claude Code ના
પોતાના પરમિશન પ્રોમ્પ્ટને સ્કિપ કરે છે (તમે પહેલેથી જ જવાબ આપી દીધો છે).
અનમેચ્ડ ટૂલ્સનો ખર્ચ ~40ms છે અને તે Claude Code ના સામાન્ય પરમિશન ફ્લોમાં
પડે છે. જ્યારે Claude Code પોતે તમારી રાહ જોતું હોય ત્યારે પણ તમને ફોન
પુશ મળે છે (`permission_prompt` / `idle_prompt` નોટિફિકેશન્સ).

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

v2 React એપ `frontend/` માં રહે છે અને Flask સર્વર v2 સક્રિય રાખીને
શરૂ કરવામાં આવે ત્યારે `/v2` પર સર્વ થાય છે.

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

`http://localhost:5173/v2/` ખોલો. Vite `/api` રિક્વેસ્ટ્સને
`http://localhost:8900` પર પ્રોક્સી કરે છે, જેથી React એપ વધારાના CORS
સેટઅપ વગર લોકલ Flask સર્વર સાથે વાત કરી શકે.

Python પેકેજ સાથે શિપ થતું બંડલ બિલ્ડ કરવા માટે:

```bash
cd frontend
npm run build
```

પ્રોડક્શન બંડલ `clawmetry/static/v2/dist/` માં લખાય છે.

## રનટાઇમ / એજન્ટ કમ્પેટિબિલિટી

ClawMetry ફક્ત OpenClaw જ નહીં, ઘણા AI-એજન્ટ રનટાઇમ્સનું નિરીક્ષણ કરે છે. દરેક નોન-OpenClaw રનટાઇમ એક ડેડિકેટેડ રીડર એડેપ્ટર શિપ કરે છે જે તેના નેટિવ સેશન ફોર્મેટને ClawMetry ના યુનિફાઇડ શેપ્સમાં ટ્રાન્સલેટ કરે છે; ડિમન તેમને એ જ DuckDB સ્ટોર + ક્લાઉડ સ્નેપશોટમાં ઇન્જેસ્ટ કરે છે, રનટાઇમ સાથે ટૅગ કરીને, અને Session replay ટૅબ એકથી વધુ રનટાઇમ હાજર હોય ત્યારે **રનટાઇમ સ્વિચર** બતાવે છે. સંપૂર્ણ મેટ્રિક્સ + રનટાઇમ્સ ઉમેરવાની ગાઇડ માટે [`docs/compatibility.md`](docs/compatibility.md) જુઓ, અને OpenClaw-ફેમિલી પ્રાઇમર માટે [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) જુઓ.

[Perplexity નું numbat](https://github.com/perplexityai/numbat) એજન્ટ-સિક્યુરિટી ટૂલ ચલાવો છો? ClawMetry તેના તારણો અને એન્ફોર્સમેન્ટ નિર્ણયોને આઉટ ઓફ ધ બોક્સ ઇન્જેસ્ટ કરે છે — [`docs/NUMBAT.md`](docs/NUMBAT.md) જુઓ.

| Runtime / Agent | Status | Notes |
|---|---|---|
| **OpenClaw** | Native | રેફરન્સ રનટાઇમ, ઓટો-ડિટેક્ટેડ |
| **PicoClaw** | Beta adapter | Flat `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કૉલ્સ. |
| **NanoClaw** | Beta adapter | પ્રતિ-સેશન SQLite (`data/v2-sessions`). ટ્રાન્સક્રિપ્ટ્સ + મેસેજ કાઉન્ટ્સ. |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટોકન્સ/કોસ્ટ. |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કૉલ્સ + થિન્કિંગ, ટોકન વપરાશ. |
| **Codex** | Beta adapter | Rollout JSONL `~/.codex/sessions/...`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કૉલ્સ, ટોકન વપરાશ. |
| **Cursor** | Beta adapter | SQLite `state.vscdb`. ચેટ/કમ્પોઝર ટ્રાન્સક્રિપ્ટ્સ, મોડલ. |
| **Aider** | Beta adapter | પ્રતિ-પ્રોજેક્ટ `.aider.chat.history.md`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટોકન કાઉન્ટ્સ. |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કૉલ્સ, ટોકન ટોટલ્સ. |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કૉલ્સ, ટોકન્સ + કોસ્ટ. |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કૉલ્સ, ટોકન વપરાશ. |
| **Pi** | Beta adapter | JSONL `~/.pi/agent/sessions`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કૉલ્સ, ટોકન્સ + કોસ્ટ. |
| **Deep Agents** | Beta adapter | SQLite `~/.deepagents/.state/sessions.db`. ટ્રાન્સક્રિપ્ટ્સ, મોડલ, ટૂલ કૉલ્સ, ટોકન્સ + કોસ્ટ. |
| **n8n** | Beta adapter | SQLite `~/.n8n/database.sqlite`. વર્કફ્લો એક્ઝિક્યુશન્સ, નોડ રન્સ, AI Agent પ્રોમ્પ્ટ્સ, n8n જ્યાં રેકોર્ડ કરે ત્યાં મોડલ + ટોકન્સ. |
| **Antigravity** | Beta adapter | `~/.gemini/<flavor>/brain/` હેઠળ Brain JSONL. વાતચીતો, ટૂલ સ્ટેપ્સ, થિન્કિંગ, પ્રતિ-જનરેશન Gemini ટોકન સ્પ્લિટ + કોસ્ટ, બેકગ્રાઉન્ડ-જનરેશન બર્ન. |
| **GitHub Copilot** | Beta adapter | `~/.copilot/session-state/` હેઠળ Copilot CLI `events.jsonl` + `session-store.db` પ્રતિ-કૉલ વપરાશ લેજર. વાતચીતો, ટૂલ કૉલ્સ, મોડલ રાઉટિંગ, કેશ-અવેર ટોકન સ્પ્લિટ, વેન્ડર-બિલ્ડ AI-ક્રેડિટ કોસ્ટ. |
| **Grok** | Beta adapter | xAI Grok Build CLI (`~/.grok/bin/grok` હેઠળ Rust બાઇનરી): ગ્લોબલ ઇવેન્ટ લોગ `~/.grok/logs/unified.jsonl` + પ્રતિ-સેશન `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. વાતચીતો, પ્રતિ-ટર્ન ટોકન સ્પ્લિટ, મોડલ રાઉટિંગ, અને CLI નું આઉટબાઉન્ડ રિપો પેલોડ `~/.grok/upload_queue/` હેઠળ સ્ટેજ કરેલું જેથી તમારા મશીનમાંથી શું બહાર ગયું તે તમે જોઈ શકો. |

"Beta adapter" નો અર્થ છે કે ClawMetry તે રનટાઇમના વાસ્તવિક ડિસ્ક-પર ફોર્મેટ માટે એક રીડર શિપ કરે છે, દરેક વાસ્તવિક મશીન પરના વાસ્તવિક ઇન્સ્ટોલ સામે બિલ્ડ + વેરિફાય કરેલ (જુઓ `tests/fixtures/runtimes/<rt>/`). એડેપ્ટર્સ રીડ-ઓન્લી છે; દરેક તેના રનટાઇમ ખરેખર શું સ્ટોર કરે છે તે વિશે પ્રામાણિક છે (દા.ત. PicoClaw/NanoClaw/Cursor ડિસ્ક પર ટોકન કોસ્ટ લખતા નથી). જ્યારે એક નોડ પર ઘણા રનટાઇમ્સ ચાલે ત્યારે, રનટાઇમ સ્વિચર સ્વચ્છ ડીપ-ડાઇવ માટે સેશન્સ વ્યુને એક પર સ્કોપ કરે છે.

## કોઈપણ SDK એજન્ટને ટ્રેક કરો — આઉટ-લૂપ કોસ્ટ એટ્રિબ્યુશન

ઉપરના રનટાઇમ્સ બધા સેશન્સ ડિસ્ક પર લખે છે. તમારો પોતાનો **પ્રોડક્શન એજન્ટ** — જે તમે OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, અથવા સાદા `httpx` લૂપ પર બનાવ્યો છે — તે લખતો નથી. ClawMetry નું ઝીરો-કન્ફિગ ઇન્ટરસેપ્ટર `httpx`/`requests` ને મંકી-પેચ કરીને તેના LLM કૉલ્સ (કોસ્ટ, ટોકન્સ, લેટન્સી, એરર્સ) હજુ પણ કેપ્ચર કરે છે:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (અથવા `CLAWMETRY_SOURCE=support-agent` એન્વ વેરિયેબલ) દરેક કૉલને એક **નામાંકિત સોર્સ** સાથે ટૅગ કરે છે, જેથી તમે ચલાવો છો તે દરેક પ્રોડક્ટ ડેશબોર્ડના Overview પરના **🔌 Out-loop sources** કાર્ડમાં પોતાની ફર્સ્ટ-ક્લાસ, કોસ્ટ-એટ્રિબ્યુટેબલ લાઇન તરીકે દેખાય — પ્રતિ એજન્ટ કૉલ્સ, પ્રોવાઇડર્સ, લેટન્સી, એરર રેટ. કોઈ સોર્સ સેટ ન કર્યો? કૉલ્સ હજુ પણ ટ્રેક થાય છે; ફક્ત કાર્ડ છુપાયેલું રહે છે.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

આ એ જ ડેટા લેયર છે જે રનટાઇમ એડેપ્ટર્સ ફીડ કરે છે (DuckDB → ક્લાઉડ સ્નેપશોટ), તેથી આઉટ-લૂપ સોર્સિસ બાકીની બધી વસ્તુની જેમ જ ક્લાઉડ ડેશબોર્ડ સાથે સિંક થાય છે, E2E-એન્ક્રિપ્ટેડ.

## OpenTelemetry — વેન્ડર-ન્યુટ્રલ, તમારા ટ્રેસ ગમે ત્યાં મોકલો

ClawMetry બંને દિશામાં **OpenTelemetry** બોલે છે, **GenAI સિમેન્ટિક કન્વેન્શન્સ** વાપરીને, જેથી તમારા એજન્ટ ટ્રેસ ક્યારેય એક જ ટૂલમાં લૉક ન થાય.

**એક્સપોર્ટ** — દરેક સેશન, LLM કૉલ્સ, ટૂલ્સ, સબ-એજન્ટ્સ, ટોકન્સ, કોસ્ટ, ને OTLP/HTTP GenAI સ્પાન્સ તરીકે કોઈપણ કલેક્ટર (Datadog, Grafana, Honeycomb, અથવા તમારો પોતાનો OTel Collector) પર:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ઓથ હેડર્સ અને પોલ ઇન્ટરવલ વૈકલ્પિક એન્વ વેરિયેબલ્સ છે:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ઇન્જેસ્ટ** — બિલ્ટ-ઇન OTLP રિસીવર `/v1/traces`, `/v1/logs`, અને `/v1/metrics` પર બીજા ગમે તેમાંથી ટ્રેસ, લોગ્સ, અને મેટ્રિક્સ સ્વીકારે છે. કોઈપણ OpenTelemetry-ઇન્સ્ટ્રુમેન્ટેડ એપને તેના તરફ પોઇન્ટ કરો:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON ટ્રેસ અને લોગ્સ સાદા `pip install clawmetry` પર કામ કરે છે, કોઈ એક્સ્ટ્રા વગર. Protobuf ઇન્જેસ્ટ (અને OTLP/JSON મેટ્રિક્સ) માટે `pip install clawmetry[otel]` જોઈએ. જે એપ પોતાનું `service.name` સેટ કરે છે તે રનટાઇમ સ્વિચરમાં પોતાના એજન્ટ તરીકે, પોતાની કોસ્ટ અને ટોકન્સ સાથે દેખાય છે.

તમને ઝીરો-કન્ફિગ, લોકલ-ફર્સ્ટ ClawMetry ડેશબોર્ડ **અને** તમારી ટીમ પહેલેથી ચલાવે છે તે કોઈપણ બેકએન્ડમાં તમારો ડેટા મળે છે — કોઈ લોક-ઇન નહીં, ઇન્સ્ટોલ કરવા માટે બીજો એજન્ટ નહીં.

## કન્ફિગરેશન

મોટાભાગના લોકોને કોઈ કન્ફિગની જરૂર નથી. ClawMetry તમારો વર્કસ્પેસ, લોગ્સ, સેશન્સ, અને ક્રોન્સ ઓટો-ડિટેક્ટ કરે છે.

જો તમારે કસ્ટમાઇઝ કરવાની જરૂર હોય તો:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

બધા વિકલ્પો: `clawmetry --help`

## સપોર્ટેડ ચેનલ્સ

તમે કન્ફિગર કરેલ દરેક OpenClaw ચેનલ માટે ClawMetry લાઇવ પ્રવૃત્તિ બતાવે છે. ફક્ત તમારા `openclaw.json` માં ખરેખર સેટ અપ કરેલી ચેનલ્સ જ Flow ડાયાગ્રામમાં દેખાય છે — કન્ફિગર ન કરેલી ચેનલ્સ આપોઆપ છુપાવવામાં આવે છે.

Flow માં કોઈપણ ચેનલ નોડ પર ક્લિક કરો ઇનકમિંગ/આઉટગોઇંગ મેસેજ કાઉન્ટ્સ સાથે લાઇવ ચેટ બબલ વ્યુ જોવા માટે.

| Channel | Status | Live Popup | Notes |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Full | ✅ | મેસેજ, સ્ટેટ્સ, 10s રિફ્રેશ |
| 💬 **iMessage** | ✅ Full | ✅ | `~/Library/Messages/chat.db` સીધું વાંચે છે |
| 💚 **WhatsApp** | ✅ Full | ✅ | WhatsApp Web (Baileys) દ્વારા |
| 🔵 **Signal** | ✅ Full | ✅ | signal-cli દ્વારા |
| 🟣 **Discord** | ✅ Full | ✅ | Guild + channel ડિટેક્શન |
| 🟪 **Slack** | ✅ Full | ✅ | Workspace + channel ડિટેક્શન |
| 🌐 **Webchat** | ✅ Full | ✅ | બિલ્ટ-ઇન વેબ UI સેશન્સ |
| 📡 **IRC** | ✅ Full | ✅ | ટર્મિનલ-સ્ટાઇલ બબલ UI |
| 🍏 **BlueBubbles** | ✅ Full | ✅ | BlueBubbles REST API દ્વારા iMessage |
| 🔵 **Google Chat** | ✅ Full | ✅ | Chat API વેબહૂક્સ દ્વારા |
| 🟣 **MS Teams** | ✅ Full | ✅ | Teams bot પ્લગઇન દ્વારા |
| 🔷 **Mattermost** | ✅ Full | ✅ | સેલ્ફ-હોસ્ટેડ ટીમ ચેટ |
| 🟩 **Matrix** | ✅ Full | ✅ | ડિસેન્ટ્રલાઇઝ્ડ, E2EE સપોર્ટ |
| 🟢 **LINE** | ✅ Full | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Full | ✅ | ડિસેન્ટ્રલાઇઝ્ડ NIP-04 DMs |
| 🟣 **Twitch** | ✅ Full | ✅ | IRC કનેક્શન દ્વારા ચેટ |
| 🔷 **Feishu/Lark** | ✅ Full | ✅ | WebSocket ઇવેન્ટ સબસ્ક્રિપ્શન |
| 🔵 **Zalo** | ✅ Full | ✅ | Zalo Bot API |

> **ઓટો-ડિટેક્શન:** ClawMetry તમારો `~/.openclaw/openclaw.json` વાંચે છે અને ફક્ત તમે ખરેખર કન્ફિગર કરેલી ચેનલ્સ જ રેન્ડર કરે છે. કોઈ મેન્યુઅલ સેટઅપ જરૂરી નથી.

## Docker ડિપ્લોયમેન્ટ

ClawMetry ને કન્ટેનરમાં ચલાવવા માંગો છો? કોઈ સમસ્યા નથી! 🐳

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

> **નોંધ:** Docker માં ચલાવતી વખતે, તમારા એજન્ટની ડેટા + લોગ ડિરેક્ટરીઓ (દા.ત. `~/.openclaw`, `~/.claude`, `~/.codex`) માઉન્ટ કરો જેથી ClawMetry તમારું સેટઅપ ઓટો-ડિટેક્ટ કરી શકે.

## જરૂરિયાતો

- Python 3.8+
- Flask (pip દ્વારા આપોઆપ ઇન્સ્ટોલ થાય છે)
- એ જ મશીન પર એક AI એજન્ટ રનટાઇમ: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, અથવા QM (અથવા Docker માટે માઉન્ટેડ વોલ્યુમ્સ)
- Linux અથવા macOS

## NemoClaw / OpenShell સપોર્ટ

ClawMetry આપોઆપ [NemoClaw](https://github.com/NVIDIA/NemoClaw) ને ડિટેક્ટ કરે છે — NVIDIA નું એન્ટરપ્રાઇઝ સિક્યુરિટી રેપર જે OpenClaw માટે છે અને એજન્ટ્સને સેન્ડબોક્સ કરેલા OpenShell કન્ટેનર્સની અંદર ચલાવે છે.

મોટાભાગના કિસ્સાઓમાં કોઈ વધારાના કન્ફિગરેશનની જરૂર નથી. સિંક ડિમન સેશન ફાઇલ્સ ઓટો-ડિસ્કવર કરે છે, ભલે તે હોસ્ટ પર `~/.openclaw/` માં હોય કે OpenShell કન્ટેનરની અંદર.

### તે કેવી રીતે કામ કરે છે

ClawMetry બે રીતે NemoClaw ને ડિટેક્ટ કરે છે:

1. **બાઇનરી ડિટેક્શન** — `nemoclaw` CLI માટે તપાસ કરે છે અને સેન્ડબોક્સ માહિતી મેળવવા `nemoclaw status` ચલાવે છે
2. **કન્ટેનર ડિટેક્શન** — `openshell`, `nemoclaw`, અથવા `ghcr.io/nvidia/` ઇમેજ માટે ચાલી રહેલા Docker કન્ટેનર્સ સ્કેન કરે છે, પછી વોલ્યુમ માઉન્ટ્સ અથવા `docker cp` દ્વારા સેશન્સ વાંચે છે

NemoClaw કન્ટેનર્સમાંથી સિંક કરેલી સેશન ફાઇલ્સને ક્લાઉડ ડેશબોર્ડમાં `runtime=nemoclaw` અને `container_id` મેટાડેટા સાથે ટૅગ કરવામાં આવે છે, જેથી તમે તેમને સ્ટાન્ડર્ડ OpenClaw સેશન્સથી એક નજરમાં અલગ પાડી શકો.

### ભલામણ કરેલ સેટઅપ: HOST પર સિંક ડિમન

શ્રેષ્ઠ અનુભવ માટે, ClawMetry ના સિંક ડિમનને **હોસ્ટ મશીન** પર ચલાવો (સેન્ડબોક્સની અંદર નહીં). આ NemoClaw ના નેટવર્ક પોલિસી પ્રતિબંધોને ટાળે છે.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

સિંક ડિમન આપોઆપ કોઈપણ ચાલી રહેલા OpenShell કન્ટેનર્સની અંદર સેશન્સ શોધી કાઢશે.

### વૈકલ્પિક: સ્પષ્ટ સેન્ડબોક્સ નામ

જો ઓટો-ડિટેક્શન કામ ન કરે, તો ClawMetry ને યોગ્ય સેન્ડબોક્સ તરફ પોઇન્ટ કરો:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### સેન્ડબોક્સની અંદર ચલાવવું (એડવાન્સ્ડ)

જો તમારે સિંક ડિમનને OpenShell સેન્ડબોક્સની **અંદર** ચલાવવો જ પડે, તો તમારી NemoClaw નેટવર્ક પોલિસીમાં આ એગ્રેસ નિયમ ઉમેરો જેથી તે ClawMetry ingest API સુધી પહોંચી શકે:

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

| Endpoint | Port | Protocol | Required |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | હા (સિંક ડિમન → ક્લાઉડ) |
| `localhost:8900` | 8900 | HTTP | હા (લોકલ ડેશબોર્ડ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | કન્ટેનર સેશન ડિસ્કવરી માટે |

સિંક ડિમન ફક્ત `ingest.clawmetry.com` પર જ આઉટબાઉન્ડ HTTPS કૉલ્સ કરે છે. કોઈ ઇનબાઉન્ડ પોર્ટ્સ જરૂરી નથી.

---

## ક્લાઉડ ડિપ્લોયમેન્ટ

SSH ટનલ્સ, રિવર્સ પ્રોક્સી, અને Docker માટે **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** જુઓ.

## ટેસ્ટિંગ

આ પ્રોજેક્ટ BrowserStack સાથે ટેસ્ટ કરવામાં આવે છે.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ટેલિમેટ્રી

ClawMetry `https://app.clawmetry.com/api/install` પર અનામી
ઇન્સ્ટોલ-લાઇફસાઇકલ પિંગ મોકલે છે: નવા મશીન પર `clawmetry` CLI પ્રથમ
વખત ચલાવો ત્યારે એક `install` પિંગ, નવા વર્ઝન પર અપગ્રેડ કર્યા પછીના
પ્રથમ રનમાં એક `update` પિંગ, અને ડેશબોર્ડની અંદરની ઓનબોર્ડિંગ પસંદગી
પૂર્ણ કરો ત્યારે એક `onboarded` પિંગ. અમે આનો ઉપયોગ વાસ્તવિક ઇન્સ્ટોલ્સ
ગણવા માટે કરીએ છીએ (કાચા PyPI ડાઉનલોડ નંબર્સ ~98% મિરર્સ, CI, અને
ઓટો-અપડેટ ફરીથી-ડાઉનલોડ છે) અને એ જાણવા માટે કે કયા એજન્ટ ફ્રેમવર્ક્સ
અને વર્ઝન્સ ખરેખર ઉપયોગમાં છે.

**દરેક વર્ઝન દીઠ, દરેક લાઇફસાઇકલ ઇવેન્ટ માટે વધુમાં વધુ એક POST**, જેમાં આ સમાયેલું છે:

| Field | Example | Why |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` પર સંગ્રહિત રેન્ડમ UUID | ડિડુપ; તમે સ્પષ્ટપણે Cloud sync કનેક્ટ ન કરો ત્યાં સુધી અનામી (ત્યારબાદ ઓથેન્ટિકેટેડ ડિમન હાર્ટબીટ તેને વહન કરે છે, આ ઇન્સ્ટોલને તમારા એકાઉન્ટ સાથે લિંક કરે છે) |
| `event` | `install` / `update` / `onboarded` | નવું ઇન્સ્ટોલ કે વર્તમાનનું અપગ્રેડ |
| `version` | `0.12.167` | કયા વર્ઝન્સ ઉપયોગમાં છે |
| `os` / `os_version` | `Darwin` / `25.3.0` | પ્લેટફોર્મ સપોર્ટ પ્રાયોરિટીઝ |
| `python` | `3.11.15` | Python વર્ઝન સપોર્ટ મેટ્રિક્સ |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | આગળ કયા એજન્ટ્સ સાથે અમારે ઇન્ટિગ્રેટ કરવું જોઈએ |
| `is_ci` / `ci_provider` | `true` / `github_actions` | માનવ ઇન્સ્ટોલ્સને CI નોઇઝથી અલગ કરો |

**અમે શું નથી મોકલતા**: IP (ક્લાઉડ સર્વર-સાઇડ પર રિક્વેસ્ટમાંથી
દેશ કોડ મેળવે છે, પછી IP કાઢી નાખે છે), હોસ્ટનેમ, યુઝરનેમ, વર્કસ્પેસ
પાથ, ફાઇલ કન્ટેન્ટ, તમારી api_key, તમારો ઇમેલ, કંઈપણ PII અથવા
વર્કસ્પેસ-સ્પેસિફિક. વાયર પેલોડ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) માં ઓડિટ કરી શકાય તેવો છે.

**ઓપ્ટ આઉટ** (આમાંથી કોઈ એક તેને કાયમ માટે નિષ્ક્રિય કરે છે):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

અહીં નેટવર્ક નિષ્ફળતા ક્યારેય `clawmetry` ને ચાલવાથી અટકાવતી નથી —
પિંગ ડિમન થ્રેડ પર 3 સેકન્ડ ટાઇમઆઉટ સાથે ફાયર-એન્ડ-ફર્ગેટ છે.

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## License

MIT

---

<p align="center">
  <strong>🦞 તમારા એજન્ટને વિચારતું જુઓ</strong><br>
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> દ્વારા બનાવેલ · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ઇકોસિસ્ટમનો ભાગ</sub>
</p>
