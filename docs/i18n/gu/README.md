<!-- i18n-src:a855a14295b0 -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**એક એજન્ટ પ્રગતિ કર્યા વગર સેંકડો ટૂલ કૉલ કરી શકે છે.** ClawMetry
તમારા કોડિંગ એજન્ટો પહેલેથી જ લખે છે તે સેશન ફાઇલો વાંચે છે, અને ટાઇમલાઇન,
ટૂલ કૉલ્સ અને રનટાઇમ જે પણ ટોકન અને ખર્ચનો ડેટા ઉજાગર કરે છે તે બધું એક
દૃશ્યમાં મૂકે છે — જેથી તમે કામ કરી રહેલા લાંબા રનને અટકી ગયેલા રનથી અલગ પારખી શકો.

**32 AI એજન્ટ રનટાઇમ** સાથે કામ કરે છે — Claude Code, OpenAI Codex, Hermes, OpenClaw અને બીજા 28. તમારા સમગ્ર એજન્ટ ફ્લીટ માટે એક જ ડેશબોર્ડ. ([સંપૂર્ણ યાદી](SUPPORTED_RUNTIMES.txt), કેટલોગમાંથી જનરેટ થયેલી.)

> 🌐 **આ ભાષામાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. શૂન્ય કન્ફિગ. બધું જાતે જ શોધી કાઢે છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે. શૂન્ય કન્ફિગ: તે તમારી પાસે પહેલેથી જ રહેલા
એજન્ટ રનટાઇમ શોધી કાઢે છે, તેમને ફક્ત-વાંચન રીતે વાંચે છે, અને તેઓ કેવી રીતે ચાલે છે
તેમાં કંઈ પણ બદલતું નથી.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ઇન્સ્ટોલ કરતાં પહેલાં

| | |
|---|---|
| **તે શું કરે છે** | તમારા એજન્ટો પહેલેથી જ લખે છે તે સેશન ફાઇલો અને લોગ વાંચે છે. કોઈ SDK નહીં, કોડમાં કોઈ ફેરફાર નહીં, તમારી એપ્લિકેશનમાં કોઈ ઇન્સ્ટ્રુમેન્ટેશન નહીં. |
| **તમે શું જુઓ છો** | સેશન ટાઇમલાઇન, ટૂલ-બાય-ટૂલ રિપ્લે, ટોકન અને ખર્ચનું વિભાજન, અને ટ્રેજેક્ટરી સિગ્નલો (લૂપિંગ, વારંવારની નિષ્ફળતાઓ) — દરેક રનટાઇમ પ્રમાણે. |
| **શું મફત છે** | `pip install clawmetry` કોઈ ખાતું, કોઈ કી અને કોઈ નેટવર્ક કૉલ વગર **OpenClaw, NVIDIA NemoClaw અને Goose** વાંચે છે. બાકીના 27 — Claude Code, Codex, Cursor અને બાકીના — ક્લોઝ્ડ-સોર્સ `clawmetry-pro` કમ્પેનિયન દ્વારા વંચાય છે, જે 7-દિવસની ટ્રાયલ અથવા પ્લાન સાથે આવે છે — ચોક્કસ વિભાજન માટે [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) જુઓ. |
| **કેવી રીતે શરૂ કરવું** | `pip install clawmetry && clawmetry`, પછી localhost:8900 ખોલો. આ મશીન પર હજુ કોઈ એજન્ટ નથી? `clawmetry --sample` ત્રણ લેબલવાળા સિન્થેટિક સેશન પર ખૂલે છે. |
| **તમારા મશીનમાંથી શું બહાર જાય છે** | કોઈ સેશન ડેટા નહીં, સિવાય કે તમે `clawmetry connect` ચલાવો. બે વસ્તુઓ ડિફોલ્ટ રીતે ચાલે છે, બંને ઓપ્ટ-આઉટ છે અને બંનેમાં સેશન સામગ્રી હોતી નથી: એક અનામી ઇન્સ્ટોલ પિંગ અને PyPI વર્ઝન ચેક. દરેક ડેસ્ટિનેશન [docs/EGRESS.md](docs/EGRESS.md) માં સૂચિબદ્ધ છે, જે ટિપ્પણીઓ વાંચીને નહીં પણ વાયર કેપ્ચરમાંથી ફરીથી બનાવેલ છે. |

તમે આઉટપુટનો ન્યાય કરો તે પહેલાં જાણવા જેવી બે મર્યાદાઓ: રનટાઇમ ખૂબ જ
અલગ ડેટા ઉજાગર કરે છે (કેટલાક કોઈ ખર્ચ જ પ્રકાશિત કરતા નથી — [મેટ્રિક્સ](docs/compatibility.md)
દરેક રનટાઇમ પ્રમાણે કહે છે કયું), અને કોઈ ક્રિયાનું અવલોકન કરવું તેને
અટકાવવા સક્ષમ હોવા સમાન નથી ([દરેક રનટાઇમ પ્રમાણે કયા નિયંત્રણો સાચા છે](docs/APPROVALS.md)).


## 32 એજન્ટ રનટાઇમ સાથે કામ કરે છે

**ઓપન સોર્સ એપમાં મફત:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**પેઇડ પ્લાનમાં:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

દરેક રનટાઇમને એક જ ડેશબોર્ડ મળે છે. એકસાથે અનેક ચલાવો અને હેડર
સ્વિચર દરેક ટેબનો સ્કોપ તેમાંથી એક પર ફરીથી સેટ કરે છે.

SDK પર તમારો પોતાનો એજન્ટ બનાવ્યો છે? ઇન્ટરસેપ્ટર તેના LLM કૉલ્સ
પણ ટ્રૅક કરે છે. જુઓ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## તમને શું મળે છે

- **સેશન્સ અને ટ્રાન્સક્રિપ્ટ્સ**: દરેક એજન્ટે શું કર્યું, વારો-વારો, રિપ્લે સાથે
- **ખર્ચ અને ટોકન**: રનટાઇમ, મોડેલ, સેશન અને દિવસ પ્રમાણે, અસાધારણતાના ફ્લેગ સાથે
- **ફ્લો**: ચેનલો, મોડેલો અને ટૂલ્સમાંથી પસાર થતા મેસેજનું લાઇવ ડાયાગ્રામ
- **બ્રેઇન**: રિઝનિંગ અને ટૂલ-કૉલ ઇવેન્ટ સ્ટ્રીમ, જેમ થાય તેમ
- **કોન્ટેક્સ્ટ બ્લોઆઉટ**: પ્રોવાઇડર પ્રમાણે માપેલી વિન્ડો યુટિલાઇઝેશન, કોમ્પેક્શન વિ. ફોર્સ્ડ ઓવરફ્લો, ઉપરાંત આપણે શું *ન* જોઈ શકીએ તેનો રનટાઇમ-પ્રમાણેનો નકશો ([કેવી રીતે](docs/CONTEXT_BLOWOUT.md))
- **મેમરી અને સ્કિલ્સ**: દરેક રનટાઇમે ખરેખર લોડ કરેલી ફાઇલો અને સ્કિલ્સ
- **હેલ્થ અને લોગ્સ**: ડિસ્ક, મેમરી, એરર રેટ, રેટ લિમિટ, લાઇવ લોગ સ્ટ્રીમ
- **એલર્ટ્સ**: બજેટ કેપ્સ, એરર સ્પાઇક્સ, એજન્ટ-ઓફલાઇન, Slack, Discord, PagerDuty, Telegram, Email પર રૂટ થયેલા
- **અપ્રૂવલ્સ**: જોખમી ટૂલ કૉલ્સને ચાલતા *પહેલાં* થોભાવો અને તમારા ફોનથી મંજૂર કરો ([કેવી રીતે](docs/APPROVALS.md))

## કોન્ટેક્સ્ટ બ્લોઆઉટ, અને મોનિટરિંગનો ખર્ચ

કોઈપણ એજન્ટ-સરખામણી ટૂલ પર વિશ્વાસ કરતાં પહેલાં જવાબ આપવા યોગ્ય બે પ્રશ્નો.

**તે રનટાઇમ્સમાં કોન્ટેક્સ્ટ-વિન્ડો બ્લોઆઉટને કેવી રીતે હેન્ડલ કરે છે?**

યુટિલાઇઝેશન ટકાવારી ફક્ત તેટલી જ પ્રામાણિક છે જેટલો તેનો ડિવાઇઝર છે. ClawMetry
[એક ટેબલ પરથી](clawmetry/context_windows.py) જે તમે વાંચી શકો છો અને PR કરી શકો છો,
પ્રોવાઇડર પ્રમાણે વિન્ડોનું કદ નક્કી કરે છે, જેમાં Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama અને GLM આવરી લેવાય છે. તે તમામ 32
રનટાઇમને એક વેન્ડરના માપદંડથી માપતું નથી. તે મહત્વનું છે: 300K GPT-5 વારો
Anthropic ના 200K સામે માપવામાં આવે તો ">100%, બ્લોન" વંચાય છે જ્યારે તે ખરેખર
GPT-5 ના 400K ના 75% પર છે. એ જ માપદંડ ખરેખર ઓવરફ્લો થયેલા 130K DeepSeek
વારાને આરામદાયક 65% તરીકે છુપાવે છે.

દરેક વિન્ડો તેની ઉત્પત્તિ સાથે આવે છે: `model_table`, `explicit_marker`,
`observed_floor`, અથવા મોડેલ ખબર ન હોય ત્યારે પ્રામાણિક `default`. અંદાજ પર
બનેલો ગેજ ક્યારેય લુકઅપ પર બનેલા ગેજ જેટલી જ સત્તા સાથે રેન્ડર થતો નથી.

ClawMetry કેટલાક રનટાઇમ પર જ કોમ્પેક્શન ઇવેન્ટ્સ જોઈ શકે છે. તેથી
`GET /api/context-coverage` દરેક રનટાઇમ પ્રમાણે રિપોર્ટ કરે છે કે **શૂન્યનો અર્થ
"સ્વચ્છ રીતે ચાલ્યું" કે "આપણે અંધ છીએ"**. જે `0` ખરેખર અંધ હોવાનો અર્થ ધરાવે છે
તે એમ કહે છે.
[સંપૂર્ણ વિગત](docs/CONTEXT_BLOWOUT.md)

**ઇન્સ્ટ્રુમેન્ટેશનનો ખર્ચ શું છે?**

| પાથ | તમારા એજન્ટમાં ઉમેરાયું | ડિફોલ્ટ? |
|---|---|---|
| સેશન-ફાઇલ ટેઇલિંગ (તમામ 32 રનટાઇમ) | **0**. અલગ પ્રોસેસ, તમારા એજન્ટમાં કોઈ ClawMetry કોડ નહીં | ચાલુ |
| HTTP ઇન્ટરસેપ્ટર (`CLAWMETRY_INTERCEPT=1`) | પ્રતિ LLM કૉલ **+0.44 ms**, અથવા 5s કૉલના 0.009% | બંધ |
| પ્રી-ટૂલ હૂક ગેટ (વોર્મ કેશ) | પ્રતિ ગેટેડ ટૂલ કૉલ **+44 ms**, 36 ms ઇન્ટરપ્રિટર ફ્લોર ઉપર | બંધ |
| એન્ફોર્સમેન્ટ પ્રોક્સી | પ્રતિ LLM કૉલ **+9.7 ms** | બંધ |

ડિમન હોસ્ટ ખર્ચ: **2,762 ઇવેન્ટ્સ/સેકન્ડ** ઇન્જેસ્ટ, ડિસ્ક પર **710 bytes/ઇવેન્ટ**
(100k ઇવેન્ટ્સ દીઠ 67.7 MB), અને વ્યસ્ત ઇન્સ્ટોલ પર સતત **એક કોરના ~12%**. તે
છેલ્લો આંકડો આપણા પોતાના જાહેર કરેલા 5-10% બજેટ કરતાં વધારે છે, તેથી તેને
પાછળ છોડવાને બદલે પકડવા યોગ્ય બગ તરીકે પ્રકાશિત કરવામાં આવ્યો છે.

Apple M2 Pro પર `benchmarks/overhead.py` વડે માપવામાં આવ્યું. હાર્નેસ
દરેક કન્ડિશનને અલગ પ્રોસેસમાં ચલાવે છે, તેમનો ક્રમ બદલે છે, અને **રાઉન્ડ્સ
તેની નિશાની પર અસહમત હોય તો સંખ્યા છાપવાનો ઇનકાર કરે છે**. તેને તમારા પોતાના
મશીન પર એક મિનિટમાં ચલાવો:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

દરેક પાથ માપવામાં આવે છે, જેમાં હૂક ગેટ્સ અને એન્ફોર્સમેન્ટ પ્રોક્સી પણ સામેલ છે,
અને હાર્નેસ CI માં Linux, macOS અને Windows પર ચાલે છે. જાણવા યોગ્ય બે
પરિણામો: પ્રોક્સીનો ખર્ચ Windows પર Linux કરતાં લગભગ સાત ગણો વધારે છે, અને
ડિમન હાલમાં એક કોરના લગભગ 12% સતત ટકાવી રાખે છે, જે આપણા પોતાના 5-10%
બજેટ કરતાં વધારે છે. કાચો JSON, પદ્ધતિ, અને હજુ શું અમાપેલું છે તે
[docs/OVERHEAD.md](docs/OVERHEAD.md) માં છે.

## પ્રાઇસિંગ

| પ્લાન | તે શું આવરી લે છે | કિંમત |
|---|---|---|
| **મફત** | OpenClaw + NVIDIA NemoClaw + Goose, સંપૂર્ણ ડેશબોર્ડ, ફક્ત લોકલ | $0 |
| **સ્ટાર્ટર** | ઉપરના બાકીના દરેક રનટાઇમ, ફ્લીટ વ્યૂ, ક્લાઉડ સિંક | $9 પ્રતિ નોડ / મહિનો |
| **Pro** | સ્ટાર્ટર + નિયંત્રણ અને મૂલ્યાંકન: અપ્રૂવલ્સ, ટૂલ-જોખમ પોલિસી, ઇવલ્સ, અસાધારણતા શોધ, ખર્ચ ઓપ્ટિમાઇઝર, OTel એક્સપોર્ટ, ટેમ્પર-એવિડન્ટ ઓડિટ લોગ | $19 પ્રતિ નોડ / મહિનો |

વાર્ષિક પ્લાન, એન્ટરપ્રાઇઝ અને વર્તમાન આંકડા
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** પર છે. સેલ્ફ-હોસ્ટેડ લાયસન્સ
કી ક્લાઉડ વગર કામ કરે છે (`clawmetry license`). ચોક્કસ મફત/પેઇડ વિભાજન
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) માં છે.

## તમારો ડેટા તમારા મશીન પર જ રહે છે

ClawMetry લોકલ સેશન ફાઇલો અને લોગ વાંચે છે. **તમે `clawmetry connect` ન ચલાવો
ત્યાં સુધી કોઈ સેશન ડેટા તમારા બોક્સમાંથી બહાર જતો નથી** — કોઈ પ્રોમ્પ્ટ, જવાબ,
ટૂલ આર્ગ્યુમેન્ટ, ફાઇલ સામગ્રી કે લોગ લાઇન નહીં. જ્યારે તમે કનેક્ટ કરો છો, ત્યારે
સ્નેપશોટ એવી કી વડે એન્ડ-ટુ-એન્ડ એન્ક્રિપ્ટેડ હોય છે જે તમારા મશીનમાંથી ક્યારેય
બહાર જતી નથી, અને તમારા બ્રાઉઝરમાં ડિક્રિપ્ટ થાય છે. જો કોઈ નોડ પાસે કી ન હોય,
તો અપલોડ સ્પષ્ટ રીતે મોકલવાને બદલે છોડી દેવામાં આવે છે, અને કોઈપણ સર્વર
રિસ્પોન્સ તેને બંધ કરી શકતો નથી.

તમે કનેક્ટ કરો તે પહેલાં બે વસ્તુઓ ડિફોલ્ટ રીતે ચાલે છે, બંને ઓપ્ટ-આઉટ છે અને
બંનેમાં સેશન ડેટા હોતો નથી: એક અનામી ઇન્સ્ટોલ પિંગ અને PyPI સામે વર્ઝન ચેક.
ડિફોલ્ટ ઇન્સ્ટોલ સ્ટાર્ટઅપ બેનર લાઇન માટે તમારો પબ્લિક IP પણ એકવાર જુએ છે.
દરેક ડેસ્ટિનેશન, તે શું વહન કરે છે અને તેને કેવી રીતે બંધ કરવું તે
[docs/EGRESS.md](docs/EGRESS.md) માં સૂચિબદ્ધ છે; સેલ્ફ-હોસ્ટેડ, રીપોઇન્ટેડ અને
એર-ગેપ્ડ ઇન્સ્ટોલ કોઈ પણ મુનસફી પરનો આઉટબાઉન્ડ કૉલ કરતા નથી.

ડિક્રિપ્શન તમારા બ્રાઉઝરમાં, અમે તમને પીરસેલા કોડમાં થાય છે. તે પહેલાં
એક વચન હતું; હવે તે એવી વસ્તુ છે જે તમે ચકાસી શકો છો. તમારી કીને સ્પર્શતી
દરેક લાઇન એક વાંચી શકાય તેવી ફાઇલમાં રહે છે, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
જે wheel ની અંદર શિપ થાય છે અને Subresource Integrity હેશ સાથે પિન કરીને
શબ્દશઃ પીરસવામાં આવે છે. બ્રાઉઝર અમે પ્રકાશિત કરેલું ચલાવે છે તેની પુષ્ટિ કરવા:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

તે શું સાબિત નથી કરતું: અમે એ પેજ પીરસીએ છીએ જે ફાઇલ લોડ કરે છે, તેથી અમે
અલગ પેજ પીરસી શકીએ છીએ. ઇન્ટેગ્રિટી હેશ તમને કોમ્પ્રોમાઇઝ થયેલા CDN થી
બચાવે છે, વેન્ડરથી નહીં. તમને જે મળે છે તે એ છે કે કોઈપણ અવેજી ઇરાદાપૂર્વકની,
પેજ સોર્સમાં દેખાતી, અને PyPI પરના આર્ટિફેક્ટ કરતાં અલગ હોવી જોઈએ જેને
કોઈ પણ મેળવી શકે છે. સેલ્ફ-હોસ્ટિંગ કરવાથી અથવા ફક્ત-લોકલ રહેવાથી
આ નિર્ભરતા સંપૂર્ણપણે દૂર થાય છે.

## ઇન્સ્ટોલ

```bash
pip install clawmetry     # પછી: clawmetry
```

અથવા વન-લાઇનર: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux અથવા Windows પર Python 3.8+ ની જરૂર છે, અને એ જ મશીન પર
ઓછામાં ઓછું એક એજન્ટ રનટાઇમ. Docker સૂચનાઓ: [docs/DOCKER.md](docs/DOCKER.md).

અથવા એજન્ટને તમારા માટે તેને સેટ અપ કરવા દો. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
સ્કિલ Claude Code, Codex, Cursor, Gemini CLI, Copilot અથવા OpenCode ને
ClawMetry ઇન્સ્ટોલ કરવાનું, મશીન પરના એજન્ટો શું કરી રહ્યા છે અને શું ખર્ચ કરી
રહ્યા છે તે રિપોર્ટ કરવાનું, વિનંતી પર એક સેશન રોકવાનું, અને મંજૂરી માટે
જોખમી ટૂલ કૉલ્સ પકડી રાખવાનું શીખવે છે:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ડોક્સ

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | દરેક એડેપ્ટર શું વાંચે છે, અને રનટાઇમ કેવી રીતે ઉમેરવું |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | પ્રોવાઇડર-પ્રમાણેની વિન્ડો, કોમ્પેક્શન વિ. ઓવરફ્લો, રનટાઇમ-પ્રમાણેનું કવરેજ |
| [Overhead](docs/OVERHEAD.md) | ઇન્સ્ટ્રુમેન્ટેશનનો ખર્ચ શું છે, માપેલો, તેને પુનઃઉત્પન્ન કરવા માટેના હાર્નેસ સાથે |
| [Entitlements](docs/ENTITLEMENTS.md) | મફત વિ. પેઇડ, ટિયર મેટ્રિક્સ, લાયસન્સ CLI |
| [Approvals & policies](docs/APPROVALS.md) | પ્રી-એક્ઝેક્યુશન ગેટિંગ, જોખમ સ્કોરિંગ, ફોન અપ્રૂવલ્સ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ટ્રેસ ગમે ત્યાં એક્સપોર્ટ કરો, ગમે તેમાંથી OTLP ઇન્જેસ્ટ કરો |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain અંતથી અંત, ચલાવી શકાય તેવા ઉદાહરણો સાથે |
| [SDK tracking](docs/SDK_TRACKING.md) | તમે જાતે બનાવેલા એજન્ટો માટે ખર્ચ એટ્રિબ્યુશન |
| [Chat channels](docs/CHANNELS.md) | Flow માં દેખાતા ચેટ એડેપ્ટર્સ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | સેન્ડબોક્સ્ડ NVIDIA NemoClaw સેટઅપ |
| [Docker](docs/DOCKER.md) | ઇમેજ, કમ્પોઝ, વોલ્યુમ માઉન્ટ |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | અંદરથી તે કેવી રીતે કામ કરે છે; સોર્સમાંથી ચલાવવું |
| [Telemetry](docs/TELEMETRY.md) | અનામી ઇન્સ્ટોલ અને ડેસ્કટોપ-ઓપન પિંગ, અને તેમને કેવી રીતે બંધ કરવા |

## સ્ક્રીનશોટ્સ

નીચેનો દરેક આંકડો એક વાસ્તવિક મશીન પરથી છે, ફક્ત-વાંચન, કંઈ પણ સીડ કર્યા વગર.

**તે તમને કહે છે કે ક્યારે કંઈક ખોટું છે, ફક્ત શું થયું તે નહીં.**
ટોચ પર બે અસાધારણતા બેનર: રોજિંદા સરેરાશ કરતાં 7 ગણો ખર્ચ ચાલી રહ્યો છે, અને
4.2x ખર્ચ સ્પાઇક. તેમની નીચે, 667 તાજેતરના સેશન્સમાંથી 324 વેસ્ટ સિગ્નલ
ધરાવે છે, કારણ પ્રમાણે વિભાજિત.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**તે તમને બતાવે છે કે પૈસા ક્યાં ગયા, દરેક વિન્ડોમાં.**
આજે $252.47, આ અઠવાડિયે $513.15, આ મહિને $1,312.92, દરેકની પાછળના
ટોકન સાથે અને તમારું સબસ્ક્રિપ્શન તેમાંથી કેટલો ભાગ પહેલેથી આવરી લે છે.
તેની નીચે, લગભગ $1,128/મહિનો પુનઃપ્રાપ્ય તરીકે વિભાજિત અને કેશ પુનઃઉપયોગ
દ્વારા પહેલેથી બચેલા $17,256/મહિનો.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**તે દોરે છે કે એક મેસેજ કેવી રીતે જવાબ બને છે.**
લાઇવ ફ્લો ડાયાગ્રામ: તમે, જે ચેનલ પર તે આવ્યો, ગેટવે, અત્યારે જવાબ આપી
રહેલું મોડેલ, અને દરેક ટૂલ જેના સુધી તે પહોંચ્યું. કામ તેમાંથી પસાર થાય તેમ
નોડ્સ પ્રકાશિત થાય છે.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**મશીન પરનો દરેક એજન્ટ, એક જ ટેબલમાં.**
તે શું ચલાવે છે, છેલ્લા 24 કલાકમાં અને તેના જીવનકાળ દરમિયાન તેનો ખર્ચ કેટલો
છે, તે છેલ્લે ક્યારે જોવાયો, તેનો માલિક કોણ છે, અને સબસ્ક્રિપ્શન બિલ આવરી
લે છે કે નહીં. અહીં 14 એજન્ટ, 3 સેશન કામ કરી રહ્યા છે, 13 શાંત.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**તે બતાવે છે કે એક વારાનો સમય અને પૈસા ક્યાં ગયા, ટૂલ પ્રમાણે.**
એક વાસ્તવિક સેશનનો એક વારો: $1.16 માટે 11.2 મિનિટમાં 11 ટૂલ્સ. દરેક
Bash કૉલ અને મોડેલ કૉલને ટાઇમલાઇન પર પોતાનો બાર મળે છે, જેથી 4.1 મિનિટ
ચાલેલો કમાન્ડ અને 226ms ચાલેલો કમાન્ડ એક નજરમાં અલગ ઓળખાય.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**તે કામને ગ્રેડ આપે છે, ફક્ત ખર્ચને નહીં.**
આ અઠવાડિયે A: 54 ટાસ્ક ચોખ્ખા પાછા આવ્યા, 2 ખરબચડા ટાસ્કનો ખર્ચ $48.57
થયો, અને જે રન ન્યાય કરવા માટે ખૂબ ઓછી પ્રવૃત્તિ ધરાવે છે તેમને જીત તરીકે
ગણવાને બદલે ગ્રેડમાંથી બહાર રાખવામાં આવે છે. દરેક ખરબચડો રન તેના
ટ્રેસ સાથે લિંક કરે છે.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**તે બતાવે છે કે કોન્ટેક્સ્ટ વિન્ડો કેમ ભરાતી રહે છે.**
છેલ્લા વારામાં 1M-ટોકન વિન્ડોમાંથી 715K, 83.3% ટોચ, 4 કોમ્પેક્શન જે
ઓવરફ્લો પર નહીં પણ પ્રોએક્ટિવલી ફાયર થયા, ઉપરાંત તેની પાછળના દરેક
વારાનું યુટિલાઇઝેશન.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**તમારે કંઈ પણ કન્ફિગર કર્યા વગર ડિટેક્શન ચાલે છે.**
બિલ્ટ-ઇન ડિટેક્ટર્સ ઇન્સ્ટોલથી જ ચાલુ છે: એજન્ટ શાંત થઈ ગયો, ટેલિમેટ્રી
ફીડ બંધ થઈ ગયો, ખર્ચ સ્પાઇક, ટોકન બર્સ્ટ, વધતી ભૂલો, એરર સ્પાઇક,
બજેટ થ્રેશોલ્ડ, થ્રેટ સિગ્નેચર મેચ, સિક્યુરિટી ટૂલ ફાઇન્ડિંગ, સિક્યુરિટી
પોસ્ચર બદલાયું. તમારા પોતાના નિયમો તેની ઉપર વૈકલ્પિક છે.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**જોખમી કૉલ રોકવો ઓપ્ટ-ઇન છે, અને બંધ સ્થિતિમાં શિપ થાય છે.**
રિકર્સિવ ડિલીટ, ફોર્સ પુશ, sudo, સિક્રેટ્સ, પેકેજ ઇન્સ્ટોલ અને આઉટબાઉન્ડ
કૉલ્સ દરેકને એક નિયમ મળે છે જે તમે ચાલુ કરી શકો છો. તમે તેમ ન કરો ત્યાં
સુધી, ClawMetry જુએ છે અને કંઈ પણ બદલતું નથી. એકવાર એક ચાલુ થાય, પછી
મેચિંગ કૉલ્સ અહીં (અથવા તમારા ફોન પર) મંજૂરી અથવા ઇનકાર માટે રાહ જુએ છે.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

વધુ, દરેક રનટાઇમ પ્રમાણે: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## માન્યતા

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## સ્ટાર હિસ્ટ્રી

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## લાયસન્સ

MIT · [@vivekchand](https://github.com/vivekchand) દ્વારા બનાવેલ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
