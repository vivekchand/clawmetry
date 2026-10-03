<!-- i18n-src:c99ac0512cae -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**એક એજન્ટ કોઈ પ્રગતિ કર્યા વિના સો ટૂલ કોલ કરી શકે છે.** ClawMetry
તમારા કોડિંગ એજન્ટો પહેલેથી જ લખે છે તે સેશન ફાઇલો વાંચે છે, અને ટાઇમલાઇન,
ટૂલ કોલ્સ, અને રનટાઇમ જે પણ ટોકન અને ખર્ચનો ડેટા ઉજાગર કરે છે તે બધું એક
વ્યૂમાં મૂકે છે — જેથી તમે કહી શકો કે કયો લાંબો રન કામ કરી રહ્યો છે અને કયો અટકી ગયો છે.

**33 AI એજન્ટ રનટાઇમ્સ** સાથે કામ કરે છે — Claude Code, OpenAI Codex, Hermes, OpenClaw અને બીજા 29. તમારા આખા એજન્ટ ફ્લીટ માટે એક ડેશબોર્ડ. ([સંપૂર્ણ યાદી](SUPPORTED_RUNTIMES.txt), કેટેલોગમાંથી જનરેટ કરવામાં આવી છે.)

> 🌐 **આ વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. શૂન્ય કન્ફિગરેશન. બધું જાતે જ ડિટેક્ટ કરે છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખુલે છે. શૂન્ય કન્ફિગરેશન: તમારી પાસે પહેલેથી જે
એજન્ટ રનટાઇમ્સ છે તે શોધે છે, તેમને રીડ-ઓન્લી રીતે વાંચે છે, અને તે કેવી રીતે ચાલે છે
તેમાં કંઈ બદલાવ કરતું નથી.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ઇન્સ્ટોલ કરતા પહેલા

| | |
|---|---|
| **તે શું કરે છે** | તમારા એજન્ટો પહેલેથી જ લખે છે તે સેશન ફાઇલો અને લોગ્સ વાંચે છે. કોઈ SDK નહીં, કોડમાં કોઈ ફેરફાર નહીં, તમારી એપમાં કોઈ ઇન્સ્ટ્રુમેન્ટેશન નહીં. |
| **તમે શું જુઓ છો** | સેશન ટાઇમલાઇન, ટૂલ-બાય-ટૂલ રિપ્લે, ટોકન અને ખર્ચનું વિભાજન, અને ટ્રેજેક્ટરી સિગ્નલ્સ (લૂપિંગ, વારંવાર નિષ્ફળતા) — દરેક રનટાઇમ પ્રમાણે. |
| **શું મફત છે** | `pip install clawmetry` કોઈ એકાઉન્ટ, કી કે નેટવર્ક કોલ વિના **OpenClaw, NVIDIA NemoClaw, Goose અને Qwen Code** વાંચે છે. બાકીના 28 — Claude Code, Codex, Cursor અને બીજા — ક્લોઝ્ડ-સોર્સ `clawmetry-pro` કમ્પેનિયન દ્વારા વાંચવામાં આવે છે, જે 7-દિવસની ટ્રાયલ અથવા પ્લાન સાથે આવે છે — ચોક્કસ વિભાજન માટે [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) જુઓ. |
| **કેવી રીતે શરૂ કરવું** | `pip install clawmetry && clawmetry`, પછી localhost:8900 ખોલો. આ મશીન પર હજુ કોઈ એજન્ટ નથી? `clawmetry --sample` ત્રણ લેબલવાળા સિન્થેટિક સેશનો સાથે ખુલે છે. |
| **તમારા મશીનમાંથી શું બહાર જાય છે** | જ્યાં સુધી તમે `clawmetry connect` ન ચલાવો ત્યાં સુધી કોઈ સેશન ડેટા નહીં. બે વસ્તુઓ ડિફોલ્ટ રૂપે ચાલે છે, બંને ઓપ્ટ-આઉટ અને બેમાંથી કોઈ સેશન કન્ટેન્ટ વહન કરતી નથી: એક અનામી ઇન્સ્ટોલ પિંગ અને PyPI વર્ઝન ચેક. દરેક ડેસ્ટિનેશન [docs/EGRESS.md](docs/EGRESS.md)માં સૂચિબદ્ધ છે, જે ટિપ્પણીઓ વાંચવાને બદલે વાયર કેપ્ચરમાંથી ફરીથી બનાવવામાં આવ્યું છે. |

તમે આઉટપુટનો ન્યાય કરો તે પહેલાં જાણવા જેવી બે મર્યાદાઓ: રનટાઇમ્સ ખૂબ
જ અલગ ડેટા ઉજાગર કરે છે (કેટલાક બિલકુલ ખર્ચ પ્રકાશિત કરતા નથી — [મેટ્રિક્સ](docs/compatibility.md)
જણાવે છે કે કયું, દરેક રનટાઇમ પ્રમાણે), અને કોઈ ક્રિયાને જોવી એ તેને
બ્લોક કરવામાં સક્ષમ થવા બરાબર નથી ([કયા નિયંત્રણો વાસ્તવિક છે, દરેક રનટાઇમ પ્રમાણે](docs/APPROVALS.md)).


## 33 એજન્ટ રનટાઇમ્સ સાથે કામ કરે છે

**ઓપન સોર્સ એપમાં મફત:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**પેઇડ પ્લાન પર:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

દરેક રનટાઇમને એક જ ડેશબોર્ડ મળે છે. એકસાથે ઘણા ચલાવો અને હેડર
સ્વિચર દરેક ટેબને તેમાંથી એક પર ફરીથી સ્કોપ કરે છે.

તમારા પોતાના SDK પર એજન્ટ બનાવ્યો છે? ઇન્ટરસેપ્ટર તેના LLM કોલ્સ પણ
ટ્રેક કરે છે. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) જુઓ.

## તમને શું મળે છે

- **સેશન્સ અને ટ્રાન્સક્રિપ્ટ્સ**: દરેક એજન્ટે શું કર્યું, ટર્ન બાય ટર્ન, રિપ્લે સાથે
- **ખર્ચ અને ટોકન્સ**: રનટાઇમ, મોડેલ, સેશન અને દિવસ પ્રમાણે, અસામાન્યતા ફ્લેગ્સ સાથે
- **ફ્લો**: ચેનલ્સ, મોડેલ્સ અને ટૂલ્સમાંથી પસાર થતા મેસેજોનો લાઇવ ડાયાગ્રામ
- **બ્રેઇન**: જેમ થાય તેમ રિઝનિંગ અને ટૂલ-કોલ ઇવેન્ટ સ્ટ્રીમ
- **કોન્ટેક્સ્ટ બ્લોઆઉટ**: પ્રોવાઇડર પ્રમાણે સાઈઝ કરેલ વિન્ડો યુટિલાઇઝેશન, કોમ્પેક્શન વિ. ફોર્સ્ડ ઓવરફ્લો, ઉપરાંત આપણે શું *જોઈ નથી શકતા* તેનો રનટાઇમ-પ્રમાણે નકશો ([કેવી રીતે](docs/CONTEXT_BLOWOUT.md))
- **મેમરી અને સ્કિલ્સ**: દરેક રનટાઇમે ખરેખર લોડ કરેલી ફાઇલો અને સ્કિલ્સ
- **હેલ્થ અને લોગ્સ**: ડિસ્ક, મેમરી, એરર દરો, રેટ લિમિટ્સ, લાઇવ લોગ સ્ટ્રીમ
- **એલર્ટ્સ**: બજેટ કેપ્સ, એરર સ્પાઇક્સ, એજન્ટ-ઓફલાઇન, Slack, Discord, PagerDuty, Telegram, Email પર રૂટ કરેલા
- **એપ્રૂવલ્સ**: જોખમી ટૂલ કોલ્સને ચાલે *તે પહેલાં* થોભાવો અને તમારા ફોનથી મંજૂર કરો ([કેવી રીતે](docs/APPROVALS.md))

## કોન્ટેક્સ્ટ બ્લોઆઉટ, અને મોનિટરિંગનો ખર્ચ

કોઈ પણ એજન્ટ-સરખામણી ટૂલ પર ભરોસો કરતા પહેલાં જવાબ આપવા જેવા બે પ્રશ્નો.

**તે રનટાઇમ્સમાં કોન્ટેક્સ્ટ-વિન્ડો બ્લોઆઉટને કેવી રીતે હેન્ડલ કરે છે?**

યુટિલાઇઝેશન પર્સન્ટેજ એટલું જ પ્રામાણિક છે જેટલું તે શેના વડે ભાગે છે. ClawMetry
[તમે વાંચી શકો અને PR કરી શકો તેવા ટેબલ](clawmetry/context_windows.py)માંથી દરેક
પ્રોવાઇડર પ્રમાણે વિન્ડો સાઈઝ કરે છે, જેમાં Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama અને GLM સામેલ છે. તે બધા 33
રનટાઇમને એક જ વેન્ડરના સ્કેલથી માપતું નથી. આ મહત્વનું છે: Anthropicના
200Kની સામે માપેલો 300K GPT-5 ટર્ન ">100%, બ્લોન" વાંચે છે જ્યારે તે ખરેખર
GPT-5ના 400Kના 75% પર છે. એ જ સ્કેલ ખરેખર ઓવરફ્લો થયેલા 130K DeepSeek
ટર્નને આરામદાયક 65% તરીકે છુપાવે છે.

દરેક વિન્ડો તેના મૂળ સાથે આવે છે: `model_table`, `explicit_marker`,
`observed_floor`, અથવા જ્યારે આપણને મોડેલ ખબર નથી ત્યારે પ્રામાણિક
`default`. અનુમાન પર બનેલું ગેજ ક્યારેય લુકઅપ પર બનેલા ગેજ જેટલા
અધિકાર સાથે રેન્ડર થતું નથી.

ClawMetry કેટલાક રનટાઇમ્સ પર જ કોમ્પેક્શન ઇવેન્ટ્સ જોઈ શકે છે. તેથી
`GET /api/context-coverage` દરેક રનટાઇમ પ્રમાણે જણાવે છે કે **શૂન્યનો
અર્થ "સ્વચ્છ રીતે ચાલ્યું" છે કે "આપણે અંધ છીએ"**. એક `0` જેનો ખરેખર
અર્થ અંધ છે તે એવું જ કહે છે. [સંપૂર્ણ વિગત](docs/CONTEXT_BLOWOUT.md)

**ઇન્સ્ટ્રુમેન્ટેશનનો ખર્ચ શું છે?**

| પાથ | તમારા એજન્ટમાં ઉમેરાયેલું | ડિફોલ્ટ? |
|---|---|---|
| સેશન-ફાઇલ ટેઇલિંગ (બધા 33 રનટાઇમ્સ) | **0**. અલગ પ્રોસેસ, તમારા એજન્ટમાં કોઈ ClawMetry કોડ નથી | ચાલુ |
| HTTP ઇન્ટરસેપ્ટર (`CLAWMETRY_INTERCEPT=1`) | દરેક LLM કોલ દીઠ **+0.44 ms**, અથવા 5s કોલના 0.009% | બંધ |
| પ્રી-ટૂલ હુક ગેટ (ગરમ કેશ) | 36 ms ઇન્ટરપ્રિટર ફ્લોર ઉપર, દરેક ગેટેડ ટૂલ કોલ દીઠ **+44 ms** | બંધ |
| એન્ફોર્સમેન્ટ પ્રોક્સી | દરેક LLM કોલ દીઠ **+9.7 ms** | બંધ |

ડેમન હોસ્ટ ખર્ચ: **2,762 ઇવેન્ટ્સ/સેકન્ડ** ઇન્જેસ્ટ, ડિસ્ક પર **710 બાઇટ્સ/ઇવેન્ટ**
(100k ઇવેન્ટ્સ દીઠ 67.7 MB), અને વ્યસ્ત ઇન્સ્ટોલ પર સતત **એક કોરના ~12%**.
તે છેલ્લો આંકડો આપણા જણાવેલા 5-10% બજેટ કરતાં વધારે છે, તેથી તેને પાનાંમાંથી
છોડી દેવાને બદલે પીછો કરવા જેવી બગ તરીકે પ્રકાશિત કરવામાં આવ્યો છે.

Apple M2 Pro પર `benchmarks/overhead.py` સાથે માપવામાં આવ્યું. હાર્નેસ
દરેક સ્થિતિને અલગ પ્રોસેસમાં ચલાવે છે, તેમનો ક્રમ બદલે છે, અને
**જ્યારે રાઉન્ડ્સ તેની નિશાની પર સહમત ન થાય ત્યારે નંબર પ્રિન્ટ કરવાનો ઇનકાર
કરે છે**. તેને તમારા પોતાના મશીન પર એક મિનિટમાં ચલાવો:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

દરેક પાથ માપવામાં આવ્યો છે, જેમાં હુક ગેટ્સ અને એન્ફોર્સમેન્ટ પ્રોક્સી સામેલ
છે, અને હાર્નેસ CIમાં Linux, macOS અને Windows પર ચાલે છે. જાણવા જેવા
બે પરિણામો: પ્રોક્સીનો ખર્ચ Windows પર Linux કરતાં લગભગ સાત ગણો વધારે છે,
અને ડેમન હાલમાં એક કોરના લગભગ 12% સતત વાપરે છે, જે આપણા પોતાના 5-10%
બજેટ કરતાં વધારે છે. કાચો JSON, પદ્ધતિ, અને હજુ શું માપવામાં આવ્યું નથી
તે [docs/OVERHEAD.md](docs/OVERHEAD.md)માં છે.

## ભાવ

| પ્લાન | તેમાં શું સમાવેલું છે | કિંમત |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, સંપૂર્ણ ડેશબોર્ડ, ફક્ત લોકલ | $0 |
| **Starter** | ઉપરનાં બાકીના બધા રનટાઇમ્સ, ફ્લીટ વ્યૂ, ક્લાઉડ સિંક | $9 પ્રતિ નોડ / મહિનો |
| **Pro** | Starter + નિયંત્રણ અને મૂલ્યાંકન: એપ્રૂવલ્સ, ટૂલ-રિસ્ક પોલિસીઝ, ઇવલ્સ, અસામાન્યતા શોધ, કોસ્ટ ઓપ્ટિમાઇઝર, OTel એક્સપોર્ટ, ટેમ્પર-એવિડન્ટ ઓડિટ લોગ | $19 પ્રતિ નોડ / મહિનો |

વાર્ષિક પ્લાન્સ, Enterprise અને હાલના આંકડા
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** પર છે. સેલ્ફ-હોસ્ટેડ
લાઇસન્સ કી ક્લાઉડ વિના કામ કરે છે (`clawmetry license`). ચોક્કસ free/paid
વિભાજન [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)માં છે.

## તમારો ડેટા તમારા મશીન પર જ રહે છે

ClawMetry લોકલ સેશન ફાઇલો અને લોગ્સ વાંચે છે. **જ્યાં સુધી તમે `clawmetry connect`
ન ચલાવો ત્યાં સુધી કોઈ સેશન ડેટા તમારા બોક્સની બહાર જતો નથી** — કોઈ પ્રોમ્પ્ટ્સ,
જવાબો, ટૂલ આર્ગ્યુમેન્ટ્સ, ફાઇલ કન્ટેન્ટ કે લોગ લાઇન નહીં. જ્યારે તમે કનેક્ટ કરો છો,
ત્યારે સ્નેપશોટ એવી કી સાથે એન્ડ-ટુ-એન્ડ એન્ક્રિપ્ટેડ હોય છે જે ક્યારેય તમારા મશીનમાંથી
બહાર જતી નથી, અને તમારા બ્રાઉઝરમાં ડિક્રિપ્ટ થાય છે. જો કોઈ નોડ પાસે કી ન હોય, તો
અપલોડ ક્લિયરમાં મોકલવાને બદલે છોડી દેવાય છે, અને કોઈ સર્વર રિસ્પોન્સ તેને બંધ કરી
શકતો નથી.

તમે કનેક્ટ કરો તે પહેલાં ડિફોલ્ટ રૂપે બે વસ્તુઓ ચાલે છે, બંને ઓપ્ટ-આઉટ અને
બેમાંથી કોઈ સેશન ડેટા વહન કરતી નથી: એક અનામી ઇન્સ્ટોલ પિંગ અને PyPI સામે
વર્ઝન ચેક. ડિફોલ્ટ ઇન્સ્ટોલ સ્ટાર્ટઅપ બેનર લાઇન માટે તમારો પબ્લિક IP પણ
એક વાર જુએ છે. દરેક ડેસ્ટિનેશન, તે શું વહન કરે છે અને તેને કેવી રીતે બંધ
કરવું તે [docs/EGRESS.md](docs/EGRESS.md)માં સૂચિબદ્ધ છે; સેલ્ફ-હોસ્ટેડ, રિપોઇન્ટેડ
અને એર-ગેપ્ડ ઇન્સ્ટોલ બિલકુલ કોઈ મરજી મુજબની આઉટબાઉન્ડ કોલ કરતા નથી.

ડિક્રિપ્શન તમારા બ્રાઉઝરમાં, આપણે તમને આપેલા કોડમાં થાય છે. તે પહેલાં
એક વચન હતું; હવે તે કંઈક છે જે તમે ચકાસી શકો છો. તમારી કીને સ્પર્શતી
દરેક લાઇન એક વાંચી શકાય તેવી ફાઇલ [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)માં
છે, જે વ્હીલની અંદર શિપ થાય છે અને શબ્દશઃ સર્વ કરવામાં આવે છે, Subresource
Integrity હેશ સાથે પિન કરેલી. બ્રાઉઝર આપણે પ્રકાશિત કરેલું જ ચલાવે છે તેની
પુષ્ટિ કરવા માટે:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

તે શું સાબિત નથી કરતું: આપણે તે પેજ સર્વ કરીએ છીએ જે ફાઇલ લોડ કરે છે,
તેથી આપણે અલગ પેજ સર્વ કરી શકીએ છીએ. ઇન્ટેગ્રિટી હેશ તમને ચેડા કરેલા
CDNથી રક્ષણ આપે છે, વેન્ડરથી નહીં. તમને જે મળે છે તે એ છે કે કોઈ પણ
બદલી ઇરાદાપૂર્વકની, પેજ સોર્સમાં દૃશ્યમાન, અને PyPI પરના આર્ટિફેક્ટ કરતાં
અલગ હોવી જોઈએ જેને કોઈ પણ ફેચ કરી શકે છે. સેલ્ફ-હોસ્ટિંગ અથવા ફક્ત-લોકલ
રહેવાથી આ નિર્ભરતા સંપૂર્ણપણે દૂર થાય છે.

## ઇન્સ્ટોલ

```bash
pip install clawmetry     # પછી: clawmetry
```

અથવા એક-લાઇનર: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux કે Windows પર Python 3.8+ જરૂરી છે, અને તે જ મશીન પર ઓછામાં
ઓછું એક એજન્ટ રનટાઇમ. Docker સૂચનાઓ: [docs/DOCKER.md](docs/DOCKER.md).

અથવા એજન્ટને તમારા માટે તે સેટ કરવા દો. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
સ્કિલ Claude Code, Codex, Cursor, Gemini CLI, Copilot અથવા OpenCodeને
ClawMetry ઇન્સ્ટોલ કરવાનું, મશીન પરના એજન્ટો શું કરી રહ્યા છે અને શું ખર્ચી
રહ્યા છે તેની જાણ કરવાનું, વિનંતી પર એક સેશન રોકવાનું, અને મંજૂરી માટે જોખમી
ટૂલ કોલ્સ રોકી રાખવાનું શીખવે છે:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## દસ્તાવેજો

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | દરેક અડેપ્ટર શું વાંચે છે, અને રનટાઇમ કેવી રીતે ઉમેરવું |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | પ્રોવાઇડર-પ્રમાણે વિન્ડો, કોમ્પેક્શન વિ. ઓવરફ્લો, રનટાઇમ-પ્રમાણે કવરેજ |
| [Overhead](docs/OVERHEAD.md) | ઇન્સ્ટ્રુમેન્ટેશનનો ખર્ચ શું છે, માપેલો, તેને રિપ્રોડ્યુસ કરવા માટેના હાર્નેસ સાથે |
| [Entitlements](docs/ENTITLEMENTS.md) | Free વિ. paid, ટિયર મેટ્રિક્સ, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | પ્રી-એક્ઝિક્યુશન ગેટિંગ, રિસ્ક સ્કોરિંગ, ફોન એપ્રૂવલ્સ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ગમે ત્યાં ટ્રેસ એક્સપોર્ટ કરો, ગમે ત્યાંથી OTLP ઇન્જેસ્ટ કરો |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain અંત થી અંત, ચલાવી શકાય તેવા ઉદાહરણો સાથે |
| [SDK tracking](docs/SDK_TRACKING.md) | તમે જાતે બનાવેલા એજન્ટો માટે ખર્ચ એટ્રિબ્યુશન |
| [Chat channels](docs/CHANNELS.md) | Flowમાં દેખાતા ચેટ અડેપ્ટર્સ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | સેન્ડબોક્સ્ડ NVIDIA NemoClaw સેટઅપ્સ |
| [Docker](docs/DOCKER.md) | ઇમેજ, કમ્પોઝ, વોલ્યુમ માઉન્ટ્સ |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | તે અંદરથી કેવી રીતે કામ કરે છે; સોર્સમાંથી ચલાવવું |
| [Telemetry](docs/TELEMETRY.md) | અનામી ઇન્સ્ટોલ અને ડેસ્કટોપ-ઓપન પિંગ્સ, અને તેમને કેવી રીતે બંધ કરવા |

## સ્ક્રીનશોટ્સ

નીચેનો દરેક આંકડો એક વાસ્તવિક મશીન પરથી છે, રીડ-ઓન્લી, કંઈ પણ સીડ કર્યા
વિના.

**તે તમને જણાવે છે કે ક્યારે કંઈક ખોટું છે, ફક્ત શું થયું તે નહીં.**
ઉપર બે અસામાન્યતા બેનર: દૈનિક સરેરાશ કરતાં 7x ખર્ચ ચાલી રહ્યો છે, અને
4.2x ખર્ચ સ્પાઇક. તેમની નીચે, તાજેતરના 667 સેશનોમાંથી 324 માં
વેસ્ટ સિગ્નલ છે, કારણ પ્રમાણે યાદી કરેલ.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**તે તમને બતાવે છે કે પૈસા ક્યાં ગયા, દરેક વિન્ડોમાં.**
આજે $252.47, આ અઠવાડિયે $513.15, આ મહિને $1,312.92, દરેકની પાછળના
ટોકન્સ અને તમારું સબસ્ક્રિપ્શન તેમાંથી કેટલું પહેલેથી કવર કરે છે તેની સાથે. તેની
નીચે, લગભગ $1,128/મહિનો રિકવરેબલ તરીકે યાદી કરેલ અને કેશ રિયુઝ દ્વારા
પહેલેથી જ $17,256/મહિનો બચાવેલ.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**તે દોરે છે કે મેસેજ કેવી રીતે જવાબ બને છે.**
લાઇવ ફ્લો ડાયાગ્રામ: તમે, તે જે ચેનલ પર આવ્યો, ગેટવે, હમણાં જવાબ આપી
રહેલું મોડેલ, અને તેણે વાપરેલ દરેક ટૂલ. કામ તેમાંથી પસાર થતાં નોડ્સ પ્રકાશિત
થાય છે.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**મશીન પરનો દરેક એજન્ટ, એક ટેબલમાં.**
તે શું ચલાવે છે, છેલ્લા 24 કલાકમાં અને તેના જીવનકાળમાં તેનો ખર્ચ કેટલો
છે, તે છેલ્લે ક્યારે જોવા મળ્યું, તેનો માલિક કોણ છે, અને સબસ્ક્રિપ્શન બિલ
કવર કરે છે કે નહીં. અહીં 14 એજન્ટો, 3 સેશન કામ કરી રહ્યા છે, 13 શાંત.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**તે બતાવે છે કે એક ટર્નનો સમય અને પૈસા ક્યાં ગયા, ટૂલ બાય ટૂલ.**
વાસ્તવિક સેશનનો એક ટર્ન: $1.16માં 11.2 મિનિટમાં 11 ટૂલ્સ. દરેક Bash
કોલ અને મોડેલ કોલને ટાઇમલાઇન પર પોતાનો બાર મળે છે, જેથી 4.1 મિનિટ
ચાલેલો કમાન્ડ અને 226ms ચાલેલો કમાન્ડ એક નજરે અલગ પડે.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**તે ફક્ત ખર્ચ નહીં, કામને ગ્રેડ આપે છે.**
આ અઠવાડિયે A: 54 કાર્યો સ્વચ્છ રીતે પાછા આવ્યા, 2 ખરબચડા કાર્યોનો ખર્ચ
$48.57 થયો, અને જે રન ન્યાય કરવા માટે બહુ ઓછી પ્રવૃત્તિ ધરાવતા હતા
તેમને જીત તરીકે ગણવાને બદલે ગ્રેડમાંથી બહાર રાખવામાં આવ્યા. દરેક ખરબચડો
રન તેના ટ્રેસ સાથે લિંક કરે છે.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**તે બતાવે છે કે કોન્ટેક્સ્ટ વિન્ડો કેમ ભરાતી રહે છે.**
છેલ્લા ટર્ન પર 1M-ટોકન વિન્ડોમાંથી 715K, 83.3% પીક, ઓવરફ્લોને બદલે
બધા જ પ્રોએક્ટિવલી ફાયર થયેલા 4 કોમ્પેક્શન, ઉપરાંત તેની પાછળના દરેક
ટર્નનું યુટિલાઇઝેશન.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ડિટેક્શન તમારે કંઈ પણ કન્ફિગર કર્યા વિના ચાલે છે.**
બિલ્ટ-ઇન ડિટેક્ટર્સ ઇન્સ્ટોલથી જ ચાલુ છે: એજન્ટ શાંત થયો, ટેલીમેટ્રી ફીડ
બંધ થયો, ખર્ચ સ્પાઇક, ટોકન બર્સ્ટ, એરર્સ વધી રહ્યા છે, એરર સ્પાઇક, બજેટ
થ્રેશોલ્ડ, થ્રેટ સિગ્નેચર મેચ થયું, સિક્યોરિટી ટૂલ ફાઇન્ડિંગ, સિક્યોરિટી
પોઝિશન બદલાઈ. તેની ઉપર તમારા પોતાના નિયમો વૈકલ્પિક છે.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**જોખમી કોલ રોકી રાખવો એ ઓપ્ટ-ઇન છે, અને બંધ સ્થિતિમાં શિપ થાય છે.**
રિકર્સિવ ડિલીટ્સ, ફોર્સ પુશ, sudo, સિક્રેટ્સ, પેકેજ ઇન્સ્ટોલ્સ અને આઉટબાઉન્ડ
કોલ્સ દરેકને એક નિયમ મળે છે જે તમે ચાલુ કરી શકો છો. તમે ચાલુ ન કરો ત્યાં
સુધી, ClawMetry જુએ છે અને કંઈ બદલતું નથી. એક વાર ચાલુ થાય, પછી
મેચિંગ કોલ્સ અહીં (અથવા તમારા ફોન પર) મંજૂરી અથવા નકાર માટે રાહ જુએ છે.

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

## લાઇસન્સ

MIT · [@vivekchand](https://github.com/vivekchand) દ્વારા બનાવવામાં આવ્યું · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
