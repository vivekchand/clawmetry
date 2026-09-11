<!-- i18n-src:12b97259721e -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**એક એજન્ટ કોઈ પ્રગતિ કર્યા વિના સેંકડો ટૂલ કૉલ્સ કરી શકે છે.** ClawMetry
તમારા કોડિંગ એજન્ટો પહેલેથી જે સેશન ફાઇલો લખે છે તે વાંચે છે, અને ટાઇમલાઇન,
ટૂલ કૉલ્સ, અને રનટાઇમ જે પણ ટોકન અને ખર્ચ ડેટા ઉજાગર કરે છે તેને એક
વ્યુમાં મૂકે છે — જેથી તમે કહી શકો કે લાંબો રન કામ કરી રહ્યો છે કે અટકી ગયો છે.

**31 AI એજન્ટ રનટાઇમ** સાથે કામ કરે છે — Claude Code, OpenAI Codex, Hermes, OpenClaw અને બીજા 27. તમારા આખા એજન્ટ ફ્લીટ માટે એક ડેશબોર્ડ. ([સંપૂર્ણ યાદી](SUPPORTED_RUNTIMES.txt), કેટલોગમાંથી જનરેટ થયેલ.)

> 🌐 **આને આમાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. ઝીરો કન્ફિગ. બધું ઓટો-ડિટેક્ટ કરે છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે. ઝીરો કન્ફિગ: તમારી પાસે પહેલેથી જે
એજન્ટ રનટાઇમ છે તેને શોધી કાઢે છે, તેમને રીડ-ઓન્લી વાંચે છે, અને તેઓ કેવી રીતે ચાલે છે તેમાં કંઈ બદલતું નથી.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ઇન્સ્ટોલ કરતાં પહેલાં

| | |
|---|---|
| **તે શું કરે છે** | તમારા એજન્ટો પહેલેથી જે સેશન ફાઇલો અને લોગ લખે છે તે વાંચે છે. કોઈ SDK નહીં, કોડ ફેરફાર નહીં, તમારી એપમાં કોઈ ઇન્સ્ટ્રુમેન્ટેશન નહીં. |
| **તમે શું જુઓ છો** | સેશન ટાઇમલાઇન, ટૂલ-બાય-ટૂલ રિપ્લે, ટોકન અને ખર્ચનું વિભાજન, અને ટ્રેજેક્ટરી સિગ્નલ્સ (લૂપિંગ, વારંવાર થતી નિષ્ફળતાઓ) — દરેક રનટાઇમ પ્રમાણે. |
| **શું ફ્રી છે** | `pip install clawmetry` કોઈ એકાઉન્ટ, કી કે નેટવર્ક કૉલ વિના **OpenClaw, NVIDIA NemoClaw અને Goose** વાંચે છે. બાકીના 27 — Claude Code, Codex, Cursor અને બીજા બધા — ક્લોઝ્ડ-સોર્સ `clawmetry-pro` કંપેનિયન દ્વારા વંચાય છે, જે 7-દિવસના ટ્રાયલ અથવા પ્લાન સાથે આવે છે — ચોક્કસ વિભાજન માટે [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) જુઓ. |
| **કેવી રીતે શરૂ કરવું** | `pip install clawmetry && clawmetry`, પછી localhost:8900 ખોલો. આ મશીન પર હજી કોઈ એજન્ટ નથી? `clawmetry --sample` ત્રણ લેબલવાળા સિન્થેટિક સેશન સાથે ખૂલે છે. |
| **તમારા મશીનમાંથી શું બહાર જાય છે** | જ્યાં સુધી તમે `clawmetry connect` ન ચલાવો ત્યાં સુધી કોઈ સેશન ડેટા નહીં. ડિફોલ્ટ રીતે બે વસ્તુઓ ચાલે છે, બંને ઓપ્ટ-આઉટ કરી શકાય તેવી અને બંનેમાં કોઈ સેશન કન્ટેન્ટ સામેલ નથી: એક એનોનિમસ ઇન્સ્ટોલ પિંગ અને PyPI વર્ઝન ચેક. દરેક ડેસ્ટિનેશન [docs/EGRESS.md](docs/EGRESS.md)માં સૂચિબદ્ધ છે, જે કમેન્ટ્સ વાંચવાને બદલે વાયર કેપ્ચરમાંથી ફરીથી બનાવવામાં આવ્યું છે. |

ચુકાદો આપતાં પહેલાં જાણવા જેવી બે મર્યાદાઓ: રનટાઇમ ખૂબ જ
અલગ ડેટા ઉજાગર કરે છે (કેટલાક તો કોઈ ખર્ચ પ્રકાશિત જ કરતા નથી — [મેટ્રિક્સ](docs/compatibility.md)
કહે છે કયા, દરેક રનટાઇમ પ્રમાણે), અને કોઈ ક્રિયાનું નિરીક્ષણ કરવું એ તેને
અટકાવવા સક્ષમ હોવા બરાબર નથી ([કયા કંટ્રોલ્સ ખરેખર કામ કરે છે, દરેક રનટાઇમ પ્રમાણે](docs/APPROVALS.md)).


## 31 એજન્ટ રનટાઇમ સાથે કામ કરે છે

**ઓપન સોર્સ એપમાં ફ્રી:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**પેઇડ પ્લાન પર:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

દરેક રનટાઇમને એ જ ડેશબોર્ડ મળે છે. એકસાથે અનેક ચલાવો અને હેડર
સ્વિચર દરેક ટેબને એમાંથી એક પર ફરીથી સ્કોપ કરે છે.

તમારો પોતાનો એજન્ટ SDK પર બનાવ્યો છે? ઇન્ટરસેપ્ટર તેના LLM કૉલ્સને
પણ ટ્રૅક કરે છે. જુઓ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## તમને શું મળે છે

- **સેશન્સ અને ટ્રાન્સક્રિપ્ટ્સ**: દરેક એજન્ટે શું કર્યું, ટર્ન બાય ટર્ન, રિપ્લે સાથે
- **ખર્ચ અને ટોકન્સ**: રનટાઇમ, મોડલ, સેશન અને દિવસ પ્રમાણે, અસામાન્યતાના ફ્લેગ્સ સાથે
- **ફ્લો**: ચેનલો, મોડલ્સ અને ટૂલ્સ વચ્ચેથી પસાર થતા મેસેજિસનો લાઇવ ડાયાગ્રામ
- **બ્રેઇન**: રિઝનિંગ અને ટૂલ-કૉલ ઇવેન્ટ સ્ટ્રીમ, જેમ તે થાય તેમ
- **કોન્ટેક્સ્ટ બ્લોઆઉટ**: પ્રોવાઇડર પ્રમાણે માપેલ વિન્ડો ઉપયોગ, કોમ્પેક્શન વિ. ફોર્સ્ડ ઓવરફ્લો, ઉપરાંત આપણે શું *જોઈ નથી શકતા* તેનો દરેક રનટાઇમ પ્રમાણેનો નકશો ([કેવી રીતે](docs/CONTEXT_BLOWOUT.md))
- **મેમરી અને સ્કિલ્સ**: દરેક રનટાઇમે ખરેખર જે ફાઇલો અને સ્કિલ્સ લોડ કરી તે
- **હેલ્થ અને લોગ્સ**: ડિસ્ક, મેમરી, એરર રેટ્સ, રેટ લિમિટ્સ, લાઇવ લોગ સ્ટ્રીમ
- **અલર્ટ્સ**: બજેટ કેપ્સ, એરર સ્પાઇક્સ, એજન્ટ-ઓફલાઇન, Slack, Discord, PagerDuty, Telegram, Email પર રૂટ થયેલ
- **એપ્રૂવલ્સ**: જોખમી ટૂલ કૉલ્સને ચાલતા *પહેલાં* થોભાવો અને તમારા ફોનથી એપ્રૂવ કરો ([કેવી રીતે](docs/APPROVALS.md))

## કોન્ટેક્સ્ટ બ્લોઆઉટ, અને મોનિટરિંગનો ખર્ચ

કોઈપણ એજન્ટ-કમ્પેરિઝન ટૂલ પર વિશ્વાસ કરતાં પહેલાં જવાબ આપવા યોગ્ય બે પ્રશ્નો.

**તે રનટાઇમ્સ વચ્ચે કોન્ટેક્સ્ટ-વિન્ડો બ્લોઆઉટને કેવી રીતે હેન્ડલ કરે છે?**

ઉપયોગની ટકાવારી એટલી જ પ્રામાણિક છે જેટલો તેનો છેદ પ્રામાણિક છે. ClawMetry
[એક ટેબલ પરથી](clawmetry/context_windows.py) જે તમે વાંચી અને PR કરી શકો છો, પ્રોવાઇડર પ્રમાણે વિન્ડોનું
માપ કાઢે છે, જે Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama અને GLM ને આવરી લે છે. તે તમામ 31
રનટાઇમને એક જ વેન્ડરના માપદંડથી માપતું નથી. આ મહત્વનું છે: Anthropic ના
200K સામે માપેલો 300K GPT-5 ટર્ન ">100%, ફૂટ્યો" વાંચે છે જ્યારે તે ખરેખર
GPT-5 ના 400K નો 75% છે. એ જ માપદંડ ખરેખર ઓવરફ્લો થયેલા 130K DeepSeek ટર્નને
આરામદાયક 65% તરીકે છુપાવે છે.

દરેક વિન્ડો તેની ઉત્પત્તિ સાથે આવે છે: `model_table`, `explicit_marker`,
`observed_floor`, અથવા જ્યારે આપણને મોડલ ખબર ન હોય ત્યારે એક પ્રામાણિક `default`.
અંદાજ પર બનેલો ગેજ ક્યારેય લુકઅપ પર બનેલા ગેજ જેટલી જ સત્તા સાથે રેન્ડર થતો નથી.

ClawMetry ફક્ત કેટલાક રનટાઇમ પર જ કોમ્પેક્શન ઇવેન્ટ્સ જોઈ શકે છે. તેથી
`GET /api/context-coverage` દરેક રનટાઇમ પ્રમાણે રિપોર્ટ કરે છે કે **શૂન્યનો અર્થ
"સાફ ચાલ્યું" છે કે "આપણે અંધ છીએ"**. શૂન્ય જેનો ખરેખર અર્થ અંધ છે એ એવું જ કહે છે.
[સંપૂર્ણ વિગત](docs/CONTEXT_BLOWOUT.md)

**ઇન્સ્ટ્રુમેન્ટેશનનો ખર્ચ કેટલો છે?**

| પાથ | તમારા એજન્ટમાં ઉમેરાયેલ | ડિફોલ્ટ? |
|---|---|---|
| સેશન-ફાઇલ ટેલિંગ (બધા 31 રનટાઇમ) | **0**. અલગ પ્રોસેસ, તમારા એજન્ટમાં કોઈ ClawMetry કોડ નહીં | ચાલુ |
| HTTP ઇન્ટરસેપ્ટર (`CLAWMETRY_INTERCEPT=1`) | પ્રતિ LLM કૉલ **+0.44 ms**, અથવા 5s કૉલના 0.009% | બંધ |
| પ્રી-ટૂલ હૂક ગેટ (વોર્મ કેશ) | 36 ms ઇન્ટરપ્રિટર ફ્લોર પર, પ્રતિ ગેટેડ ટૂલ કૉલ **+44 ms** | બંધ |
| એન્ફોર્સમેન્ટ પ્રોક્સી | પ્રતિ LLM કૉલ **+9.7 ms** | બંધ |

ડિમન હોસ્ટનો ખર્ચ: **2,762 ઇવેન્ટ્સ/સેકન્ડ** ઇન્જેસ્ટ, ડિસ્ક પર
**પ્રતિ ઇવેન્ટ 710 બાઇટ્સ** (100k ઇવેન્ટ્સ દીઠ 67.7 MB), અને વ્યસ્ત
ઇન્સ્ટોલ પર સતત **એક કોરના ~12%**. છેલ્લો આંકડો આપણા પોતાના જાહેર કરેલા
5-10% બજેટ કરતાં વધારે છે, તેથી તેને પાનાં પરથી કાઢી નાખવાને બદલે
ધ્યાન દેવા યોગ્ય બગ તરીકે પ્રકાશિત કરવામાં આવ્યો છે.

Apple M2 Pro પર `benchmarks/overhead.py` વડે માપવામાં આવ્યું. હાર્નેસ
દરેક શરત અલગ પ્રોસેસમાં ચલાવે છે, તેમનો ક્રમ બદલે છે, અને **જ્યારે રાઉન્ડ્સ
તેની નિશાની બાબતે અસહમત હોય ત્યારે નંબર છાપવાનો ઇનકાર કરે છે**. તેને તમારા
પોતાના મશીન પર એક મિનિટમાં ચલાવો:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

દરેક પાથ માપવામાં આવે છે, જેમાં હૂક ગેટ્સ અને એન્ફોર્સમેન્ટ પ્રોક્સીનો પણ સમાવેશ થાય છે,
અને હાર્નેસ CI માં Linux, macOS અને Windows પર ચાલે છે. જાણવા યોગ્ય બે પરિણામો:
પ્રોક્સીનો ખર્ચ Windows પર Linux કરતાં લગભગ સાત ગણો વધારે છે, અને
ડિમન હાલમાં આપણા પોતાના 5-10% બજેટ કરતાં વધારે, એક કોરના લગભગ 12% સતત ટકાવી રાખે છે.
રો JSON, પદ્ધતિ, અને હજુ સુધી શું માપવામાં નથી આવ્યું તે
[docs/OVERHEAD.md](docs/OVERHEAD.md)માં છે.

## કિંમત

| પ્લાન | તે શું આવરી લે છે | કિંમત |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, સંપૂર્ણ ડેશબોર્ડ, ફક્ત લોકલ | $0 |
| **Starter** | ઉપરના બાકીના દરેક રનટાઇમ, ફ્લીટ વ્યુ, ક્લાઉડ સિંક | $9 પ્રતિ નોડ / મહિનો |
| **Pro** | Starter + કંટ્રોલ અને ઇવેલ્યુએશન: એપ્રૂવલ્સ, ટૂલ-રિસ્ક પોલિસીઝ, ઇવલ્સ, અસામાન્યતા શોધ, કોસ્ટ ઓપ્ટિમાઇઝર, OTel એક્સપોર્ટ, ટેમ્પર-એવિડન્ટ ઓડિટ લોગ | $19 પ્રતિ નોડ / મહિનો |

વાર્ષિક પ્લાન્સ, Enterprise અને હાલના આંકડા
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** પર છે. સેલ્ફ-હોસ્ટેડ લાયસન્સ
કી ક્લાઉડ વિના કામ કરે છે (`clawmetry license`). ચોક્કસ ફ્રી/પેઇડ વિભાજન
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)માં છે.

## તમારો ડેટા તમારા મશીન પર જ રહે છે

ClawMetry લોકલ સેશન ફાઇલો અને લોગ વાંચે છે. **જ્યાં સુધી તમે `clawmetry connect`
ન ચલાવો ત્યાં સુધી કોઈ સેશન ડેટા તમારા બોક્સમાંથી બહાર જતો નથી** — કોઈ પ્રોમ્પ્ટ, જવાબ,
ટૂલ આર્ગ્યુમેન્ટ્સ, ફાઇલ કન્ટેન્ટ કે લોગ લાઇન નહીં. જ્યારે તમે કનેક્ટ કરો છો, ત્યારે
સ્નેપશોટ એક એવી કી વડે એન્ડ-ટુ-એન્ડ એન્ક્રિપ્ટેડ હોય છે જે તમારા મશીનમાંથી ક્યારેય
બહાર જતી નથી, અને તમારા બ્રાઉઝરમાં ડિક્રિપ્ટ થાય છે. જો કોઈ નોડ પાસે કી ન હોય,
તો અપલોડને ક્લિયરમાં મોકલવાને બદલે છોડી દેવામાં આવે છે, અને કોઈ સર્વર રિસ્પોન્સ
તેને બંધ કરી શકતો નથી.

તમે કનેક્ટ કરો તે પહેલાં ડિફોલ્ટ રીતે બે વસ્તુઓ ચાલે છે, બંને ઓપ્ટ-આઉટ કરી
શકાય તેવી અને બંનેમાં કોઈ સેશન ડેટા સામેલ નથી: એક એનોનિમસ ઇન્સ્ટોલ પિંગ અને
PyPI સામે વર્ઝન ચેક. ડિફોલ્ટ ઇન્સ્ટોલ સ્ટાર્ટઅપ બેનર લાઇન માટે તમારો
પબ્લિક IP પણ એકવાર લુકઅપ કરે છે. દરેક ડેસ્ટિનેશન, તે શું વહન કરે છે અને તેને
કેવી રીતે બંધ કરવું તે [docs/EGRESS.md](docs/EGRESS.md)માં સૂચિબદ્ધ છે; સેલ્ફ-હોસ્ટેડ,
રીપોઇન્ટેડ અને એર-ગેપ્ડ ઇન્સ્ટોલ્સ કોઈ સ્વૈચ્છિક આઉટબાઉન્ડ કૉલ કરતા જ નથી.

ડિક્રિપ્શન તમારા બ્રાઉઝરમાં થાય છે, અમે તમને પીરસેલા કોડમાં. તે પહેલાં એક
વચન હતું; હવે તે એવી વસ્તુ છે જે તમે ચકાસી શકો છો. તમારી કીને સ્પર્શતી દરેક
લાઇન એક વાંચી શકાય તેવી ફાઇલમાં છે, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
જે wheel ની અંદર શિપ થાય છે અને Subresource Integrity હેશ સાથે પિન કરેલી,
શબ્દશઃ પીરસવામાં આવે છે. બ્રાઉઝર અમે પ્રકાશિત કરેલું જ ચલાવે છે તેની પુષ્ટિ કરવા માટે:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

આ શું સાબિત નથી કરતું: અમે એ પેજ પીરસીએ છીએ જે ફાઇલ લોડ કરે છે, તેથી અમે અલગ
પેજ પીરસી શકીએ છીએ. ઇન્ટેગ્રિટી હેશ તમને એક ચેડાં કરેલા CDN થી બચાવે છે,
વેન્ડરથી નહીં. તમને જે મળે છે તે એ છે કે કોઈપણ અદલાબદલી ઇરાદાપૂર્વકની,
પેજ સોર્સમાં દેખાતી, અને PyPI પરના આર્ટિફેક્ટથી અલગ હોવી જોઈએ જેને
કોઈપણ મેળવી શકે છે. સેલ્ફ-હોસ્ટિંગ અથવા ફક્ત-લોકલ રહેવાથી આ નિર્ભરતા
સંપૂર્ણપણે દૂર થઈ જાય છે.

## ઇન્સ્ટોલ

```bash
pip install clawmetry     # પછી: clawmetry
```

અથવા વન-લાઇનર: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux કે Windows પર Python 3.8+ જરૂરી છે, અને એ જ મશીન પર ઓછામાં ઓછો
એક એજન્ટ રનટાઇમ. Docker સૂચનાઓ: [docs/DOCKER.md](docs/DOCKER.md).

અથવા એજન્ટને તમારા માટે તેને સેટ અપ કરવા દો. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
સ્કિલ Claude Code, Codex, Cursor, Gemini CLI, Copilot અથવા OpenCode ને
ClawMetry ઇન્સ્ટોલ કરવાનું, મશીન પરના એજન્ટો શું કરી રહ્યા છે અને શું ખર્ચ
કરી રહ્યા છે તે રિપોર્ટ કરવાનું, વિનંતી પર એક સેશન રોકવાનું, અને એપ્રૂવલ માટે
જોખમી ટૂલ કૉલ્સને રોકી રાખવાનું શીખવે છે:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## દસ્તાવેજો

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | દરેક એડેપ્ટર શું વાંચે છે, અને રનટાઇમ કેવી રીતે ઉમેરવું |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | પ્રોવાઇડર-પ્રમાણેની વિન્ડોઝ, કોમ્પેક્શન વિ. ઓવરફ્લો, રનટાઇમ-પ્રમાણેનું કવરેજ |
| [Overhead](docs/OVERHEAD.md) | ઇન્સ્ટ્રુમેન્ટેશનનો ખર્ચ કેટલો છે, માપેલો, તેને પુનઃઉત્પન્ન કરવાના હાર્નેસ સાથે |
| [Entitlements](docs/ENTITLEMENTS.md) | Free વિ. paid, ટિયર મેટ્રિક્સ, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | પ્રી-એક્ઝિક્યુશન ગેટિંગ, રિસ્ક સ્કોરિંગ, ફોન એપ્રૂવલ્સ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ટ્રેસ ગમે ત્યાં એક્સપોર્ટ કરો, ગમે તેમાંથી OTLP ઇન્જેસ્ટ કરો |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain અંતથી અંત સુધી, ચલાવી શકાય તેવા ઉદાહરણો સાથે |
| [SDK tracking](docs/SDK_TRACKING.md) | તમે જાતે બનાવેલા એજન્ટો માટે ખર્ચની ફાળવણી |
| [Chat channels](docs/CHANNELS.md) | Flow માં દેખાતા ચેટ એડેપ્ટર્સ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | સેન્ડબોક્સ કરેલા NVIDIA NemoClaw સેટઅપ્સ |
| [Docker](docs/DOCKER.md) | ઇમેજ, કમ્પોઝ, વોલ્યુમ માઉન્ટ્સ |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | અંદર તે કેવી રીતે કામ કરે છે; સોર્સમાંથી ચલાવવું |
| [Telemetry](docs/TELEMETRY.md) | એનોનિમસ ઇન્સ્ટોલ અને ડેસ્કટોપ-ઓપન પિંગ્સ, અને તેમને કેવી રીતે બંધ કરવા |

## સ્ક્રીનશોટ્સ

નીચેનો દરેક આંકડો એક વાસ્તવિક મશીન પરથી છે, રીડ-ઓન્લી, કંઈ પણ સીડ કર્યા વિના.

**તે તમને કહે છે કે ક્યારે કંઈક ખોટું છે, ફક્ત શું થયું એ નહીં.**
ટોચ પર બે અસામાન્યતા બેનર: દૈનિક સરેરાશ કરતાં 7x ખર્ચ ચાલી રહ્યો છે, અને
4.2x ખર્ચ સ્પાઇક. તેમની નીચે, તાજેતરના 667 સેશનમાંથી 324, કારણ પ્રમાણે
વિભાજિત, વેસ્ટ સિગ્નલ સાથે.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**તે તમને બતાવે છે કે પૈસા ક્યાં ગયા, દરેક વિન્ડોમાં.**
આજે $252.47, આ અઠવાડિયે $513.15, આ મહિને $1,312.92, દરેક પાછળના
ટોકન સાથે અને તમારું સબસ્ક્રિપ્શન કેટલું પહેલેથી આવરી લે છે તે સાથે. તેની નીચે,
લગભગ $1,128/મહિનો પુનઃપ્રાપ્ત કરી શકાય તેવો તરીકે વિભાજિત અને કેશ પુનઃઉપયોગ
દ્વારા પહેલેથી બચેલા $17,256/મહિનો.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**તે દોરે છે કે એક મેસેજ કેવી રીતે જવાબ બને છે.**
લાઇવ ફ્લો ડાયાગ્રામ: તમે, જે ચેનલ પર તે આવ્યો, ગેટવે, અત્યારે જવાબ આપી
રહેલો મોડલ, અને તેણે જે દરેક ટૂલ સુધી પહોંચ્યો. કામ તેમાંથી પસાર થતાં
નોડ્સ ચમકે છે.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**મશીન પરના દરેક એજન્ટ, એક જ ટેબલમાં.**
તે શું ચલાવે છે, છેલ્લા 24 કલાકમાં અને તેના જીવનકાળ દરમિયાન તેનો ખર્ચ કેટલો,
તે છેલ્લે ક્યારે જોવાયો, તેનો માલિક કોણ, અને શું સબસ્ક્રિપ્શન બિલ આવરી લે છે.
અહીં 14 એજન્ટ, 3 સેશન કામ કરી રહ્યા, 13 શાંત.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**તે બતાવે છે કે ટર્નનો સમય અને પૈસા ક્યાં ગયા, ટૂલ બાય ટૂલ.**
એક વાસ્તવિક સેશનનો એક ટર્ન: $1.16 માં 11.2 મિનિટમાં 11 ટૂલ્સ. દરેક Bash
કૉલ અને મોડલ કૉલને ટાઇમલાઇન પર પોતાનો બાર મળે છે, જેથી 4.1 મિનિટ ચાલેલો
કમાન્ડ અને 226ms ચાલેલો કમાન્ડ એક નજરમાં અલગ પડે.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**તે કામને ગ્રેડ કરે છે, ફક્ત ખર્ચને નહીં.**
આ અઠવાડિયે A: 54 ટાસ્ક સ્વચ્છ પાછા આવ્યા, 2 કાચા ટાસ્કનો ખર્ચ $48.57
થયો, અને ચુકાદો આપવા માટે બહુ ઓછી પ્રવૃત્તિ ધરાવતા રનને જીત તરીકે ગણવાને
બદલે ગ્રેડમાંથી બાકાત રાખવામાં આવે છે. દરેક કાચો રન તેના ટ્રેસ સાથે લિંક કરે છે.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**તે બતાવે છે કે કોન્ટેક્સ્ટ વિન્ડો શા માટે ભરાતી રહે છે.**
છેલ્લા ટર્ન પર 1M-ટોકન વિન્ડોમાંથી 715K, 83.3% પીક, 4 કોમ્પેક્શન જે
બધા ઓવરફ્લો પર નહીં પણ સક્રિય રીતે ફાયર થયા, ઉપરાંત તેની પાછળના દરેક
ટર્નનો ઉપયોગ.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**તમે કંઈ કન્ફિગર કર્યા વિના ડિટેક્શન ચાલે છે.**
બિલ્ટ-ઇન ડિટેક્ટર્સ ઇન્સ્ટોલથી જ ચાલુ છે: એજન્ટ શાંત થઈ ગયો, ટેલિમેટ્રી ફીડ
બંધ થઈ, ખર્ચ સ્પાઇક, ટોકન બર્સ્ટ, વધતી ભૂલો, એરર સ્પાઇક, બજેટ
થ્રેશોલ્ડ, થ્રેટ સિગ્નેચર મેચ થયો, સિક્યુરિટી ટૂલ ફાઇન્ડિંગ, સિક્યુરિટી પોશ્ચર
બદલાયું. તમારા પોતાના નિયમો ટોચ પર ઓપ્શનલ છે.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**જોખમી કૉલને રોકવો ઓપ્ટ-ઇન છે, અને બંધ સ્થિતિમાં શિપ થાય છે.**
રિકર્સિવ ડિલીટ્સ, ફોર્સ પુશ, sudo, સિક્રેટ્સ, પેકેજ ઇન્સ્ટોલ્સ અને આઉટબાઉન્ડ
કૉલ્સ દરેકને એક નિયમ મળે છે જે તમે ચાલુ કરી શકો. તમે ચાલુ ન કરો ત્યાં સુધી,
ClawMetry જુએ છે અને કંઈ બદલતું નથી. એકવાર ચાલુ કર્યા પછી, મેચ થતા કૉલ્સ
અહીં (અથવા તમારા ફોન પર) એપ્રૂવ કે ડિનાય માટે રાહ જુએ છે.

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
