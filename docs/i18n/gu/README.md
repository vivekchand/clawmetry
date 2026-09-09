<!-- i18n-src:61beb8393e2f -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**એક એજન્ટ પ્રગતિ કર્યા વગર સેંકડો ટૂલ કૉલ કરી શકે છે.** ClawMetry
તમારા કોડિંગ એજન્ટ્સ પહેલેથી જ લખે છે તે સેશન ફાઇલો વાંચે છે, અને ટાઇમલાઇન,
ટૂલ કૉલ્સ, અને રનટાઇમ જે પણ ટોકન અને કિંમતનો ડેટા આપે છે તે બધું એક
વ્યુમાં મૂકે છે — જેથી તમે કહી શકો કે લાંબો રન કામ કરી રહ્યો છે કે અટકી ગયો છે.

**30 AI એજન્ટ રનટાઇમ્સ** સાથે કામ કરે છે — Claude Code, OpenAI Codex, Hermes, OpenClaw અને બીજા 26. તમારા આખા એજન્ટ ફ્લીટ માટે એક જ ડેશબોર્ડ. ([સંપૂર્ણ યાદી](SUPPORTED_RUNTIMES.txt), કેટલોગમાંથી જનરેટ થયેલ.)

> 🌐 **આ ભાષામાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. ઝીરો કન્ફિગ. બધું ઑટો-ડિટેક્ટ કરે છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે. ઝીરો કન્ફિગ: તમારી પાસે પહેલેથી જે એજન્ટ રનટાઇમ્સ છે
તેને શોધે છે, તેમને ફક્ત-વાંચવા-માટે (read-only) વાંચે છે, અને તેઓ કેવી રીતે ચાલે છે તેમાં કંઈ બદલતું નથી.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ઇન્સ્ટોલ કરતાં પહેલાં

| | |
|---|---|
| **તે શું કરે છે** | તમારા એજન્ટ્સ પહેલેથી લખે છે તે સેશન ફાઇલો અને લોગ્સ વાંચે છે. કોઈ SDK નહીં, કોડમાં કોઈ ફેરફાર નહીં, તમારી એપમાં કોઈ ઇન્સ્ટ્રુમેન્ટેશન નહીં. |
| **તમે શું જુઓ છો** | સેશન ટાઇમલાઇન, ટૂલ-બાય-ટૂલ રિપ્લે, ટોકન અને કિંમતનું બ્રેકડાઉન, અને ટ્રેજેક્ટરી સિગ્નલ્સ (લૂપિંગ, વારંવાર થતી નિષ્ફળતાઓ) — દરેક રનટાઇમ પ્રમાણે. |
| **શું ફ્રી છે** | `pip install clawmetry` **OpenClaw, NVIDIA NemoClaw અને Goose** ને કોઈ એકાઉન્ટ, કોઈ કી અને કોઈ નેટવર્ક કૉલ વગર વાંચે છે. બાકીના 27 — Claude Code, Codex, Cursor અને બીજા — ક્લોઝ્ડ-સોર્સ `clawmetry-pro` કમ્પેનિયન દ્વારા વંચાય છે, જે 7-દિવસની ટ્રાયલ અથવા પ્લાન સાથે મળે છે — ચોક્કસ વિભાજન માટે [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) જુઓ. |
| **કેવી રીતે શરૂ કરવું** | `pip install clawmetry && clawmetry`, પછી localhost:8900 ખોલો. આ મશીન પર હજુ કોઈ એજન્ટ નથી? `clawmetry --sample` ત્રણ લેબલવાળા સિન્થેટિક સેશન સાથે ખૂલે છે. |
| **તમારા મશીનમાંથી શું બહાર જાય છે** | કોઈ સેશન ડેટા બહાર જતો નથી, જ્યાં સુધી તમે `clawmetry connect` ન ચલાવો. બે વસ્તુઓ ડિફોલ્ટ રીતે ચાલે છે, બંને ઑપ્ટ-આઉટ કરી શકાય તેવી અને બંનેમાં કોઈ સેશન કન્ટેન્ટ હોતું નથી: એક એનોનિમસ ઇન્સ્ટોલ પિંગ અને એક PyPI વર્ઝન ચેક. દરેક ડેસ્ટિનેશનની યાદી [docs/EGRESS.md](docs/EGRESS.md) માં છે, જે કમેન્ટ્સ વાંચીને નહીં પણ વાયર કેપ્ચરમાંથી ફરી બનાવવામાં આવી છે. |

આઉટપુટનો નિર્ણય લેતાં પહેલાં જાણવા જેવી બે મર્યાદાઓ: રનટાઇમ્સ ખૂબ
અલગ-અલગ ડેટા આપે છે (કેટલાક તો કિંમત જ પ્રકાશિત નથી કરતા — [મેટ્રિક્સ](docs/compatibility.md)
દરેક રનટાઇમ પ્રમાણે કહે છે કે કયું), અને કોઈ ક્રિયાનું નિરીક્ષણ કરવું એ તેને
રોકી શકવા બરાબર નથી ([દરેક રનટાઇમ પ્રમાણે કયા કંટ્રોલ્સ ખરેખર કામ કરે છે](docs/APPROVALS.md)).


## 30 એજન્ટ રનટાઇમ્સ સાથે કામ કરે છે

**ઓપન સોર્સ એપમાં ફ્રી:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**પેઇડ પ્લાનમાં:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

દરેક રનટાઇમને એક જ ડેશબોર્ડ મળે છે. એકસાથે અનેક ચલાવો અને હેડર
સ્વિચર દરેક ટેબને તેમાંથી એક પર રિ-સ્કોપ કરે છે.

તમારો પોતાનો એજન્ટ SDK પર બનાવ્યો છે? ઇન્ટરસેપ્ટર તેના LLM કૉલ્સ પણ
ટ્રેક કરે છે. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) જુઓ.

## તમને શું મળે છે

- **સેશન્સ અને ટ્રાન્સ્ક્રિપ્ટ્સ**: દરેક એજન્ટે શું કર્યું, ટર્ન બાય ટર્ન, રિપ્લે સાથે
- **કિંમત અને ટોકન**: રનટાઇમ, મોડેલ, સેશન અને દિવસ પ્રમાણે, અસામાન્યતાના ફ્લેગ સાથે
- **ફ્લો**: ચેનલ્સ, મોડેલ્સ અને ટૂલ્સ વચ્ચે ફરતા મેસેજિસનું લાઇવ ડાયાગ્રામ
- **બ્રેઇન**: રિઝનિંગ અને ટૂલ-કૉલ ઇવેન્ટ સ્ટ્રીમ, થાય તે સમયે
- **કોન્ટેક્સ્ટ બ્લોઆઉટ**: પ્રોવાઇડર પ્રમાણે ગણેલી વિન્ડો યુટિલાઇઝેશન, કૉમ્પેક્શન વિ. ફોર્સ્ડ ઓવરફ્લો, અને આપણે શું *નથી* જોઈ શકતા તેનો રનટાઇમ-પ્રમાણેનો નકશો ([કેવી રીતે](docs/CONTEXT_BLOWOUT.md))
- **મેમરી અને સ્કિલ્સ**: દરેક રનટાઇમે ખરેખર જે ફાઇલો અને સ્કિલ્સ લોડ કરી તે
- **હેલ્થ અને લોગ્સ**: ડિસ્ક, મેમરી, એરર રેટ્સ, રેટ લિમિટ્સ, લાઇવ લોગ સ્ટ્રીમ
- **અલર્ટ્સ**: બજેટ કેપ્સ, એરર સ્પાઇક્સ, એજન્ટ-ઓફલાઇન, Slack, Discord, PagerDuty, Telegram, Email પર રૂટ થયેલા
- **એપ્રૂવલ્સ**: જોખમી ટૂલ કૉલ્સને ચાલે તે *પહેલાં* થોભાવો અને તમારા ફોનથી મંજૂર કરો ([કેવી રીતે](docs/APPROVALS.md))

## કોન્ટેક્સ્ટ બ્લોઆઉટ, અને મોનિટરિંગની કિંમત

કોઈપણ એજન્ટ-કમ્પેરિઝન ટૂલ પર ભરોસો કરતાં પહેલાં જવાબ આપવા જેવા બે પ્રશ્નો.

**તે રનટાઇમ્સમાં કોન્ટેક્સ્ટ-વિન્ડો બ્લોઆઉટ કેવી રીતે હેન્ડલ કરે છે?**

યુટિલાઇઝેશન ટકાવારી એટલી જ પ્રામાણિક હોય છે જેટલો તેનો છેદ (divisor) હોય.
ClawMetry [એક કોષ્ટક](clawmetry/context_windows.py) પરથી, જે તમે વાંચી શકો છો અને PR કરી શકો છો,
પ્રોવાઇડર પ્રમાણે વિન્ડોનું માપ નક્કી કરે છે, જેમાં Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama અને GLM આવરી લેવાય છે. તે બધા 30
રનટાઇમ્સને એક જ વેન્ડરના માપદંડથી માપતું નથી. આ મહત્વનું છે: 300K GPT-5 ટર્નને
Anthropic ના 200K સામે માપવામાં આવે તો ">100%, blown" વંચાય, જ્યારે તે ખરેખર
GPT-5 ના 400K માંથી 75% પર જ છે. એ જ માપદંડ ખરેખર ઓવરફ્લો થયેલા 130K
DeepSeek ટર્નને 65% ના આરામદાયક આંકડા તરીકે છુપાવે છે.

દરેક વિન્ડો પોતાની ઉત્પત્તિ (provenance) સાથે આવે છે: `model_table`, `explicit_marker`,
`observed_floor`, અથવા મોડેલ ખબર ન હોય ત્યારે પ્રામાણિક `default`. અંદાજ પર
બનેલો ગેજ ક્યારેય લુકઅપ પર બનેલા ગેજ જેટલી સત્તા સાથે રેન્ડર થતો નથી.

ClawMetry ફક્ત અમુક રનટાઇમ્સ પર જ કૉમ્પેક્શન ઇવેન્ટ્સ જોઈ શકે છે. તેથી
`GET /api/context-coverage` દરેક રનટાઇમ પ્રમાણે જણાવે છે કે **શૂન્યનો અર્થ
"ક્લીન ચાલ્યું" છે કે "આપણે અંધ છીએ"**. જે `0` ખરેખર અંધ હોવાનો અર્થ કરે છે તે
તેમ કહે છે. [સંપૂર્ણ વિગત](docs/CONTEXT_BLOWOUT.md)

**ઇન્સ્ટ્રુમેન્ટેશનનો ખર્ચ કેટલો છે?**

| પાથ | તમારા એજન્ટમાં ઉમેરાયું | ડિફોલ્ટ? |
|---|---|---|
| સેશન-ફાઇલ ટેઇલિંગ (બધા 30 રનટાઇમ્સ) | **0**. અલગ પ્રોસેસ, તમારા એજન્ટમાં કોઈ ClawMetry કોડ નહીં | on |
| HTTP ઇન્ટરસેપ્ટર (`CLAWMETRY_INTERCEPT=1`) | LLM કૉલ દીઠ **+0.44 ms**, અથવા 5s ના કૉલના 0.009% | off |
| પ્રી-ટૂલ હૂક ગેટ (વૉર્મ કેશ) | ગેટેડ ટૂલ કૉલ દીઠ **+44 ms**, 36 ms ના ઇન્ટરપ્રિટર ફ્લોર ઉપર | off |
| એન્ફોર્સમેન્ટ પ્રોક્સી | LLM કૉલ દીઠ **+9.7 ms** | off |

ડિમન હોસ્ટ ખર્ચ: **2,762 ઇવેન્ટ્સ/સેકન્ડ** ઇન્જેસ્ટ, ડિસ્ક પર ઇવેન્ટ દીઠ
**710 બાઇટ્સ** (100k ઇવેન્ટ્સ દીઠ 67.7 MB), અને વ્યસ્ત ઇન્સ્ટોલ પર સતત
**એક કોરના ~12%**. છેલ્લો આંકડો અમારા પોતાના જાહેર કરેલા 5-10% ના
બજેટ કરતાં વધારે છે, તેથી તેને પાનાં પરથી કાઢી નાખવાને બદલે પીછો કરવા
યોગ્ય બગ તરીકે પ્રકાશિત કરવામાં આવ્યો છે.

Apple M2 Pro પર `benchmarks/overhead.py` વડે માપવામાં આવ્યું. હાર્નેસ
દરેક કન્ડિશનને અલગ પ્રોસેસમાં ચલાવે છે, તેમનો ક્રમ બદલે છે, અને
**રાઉન્ડ્સ તેની નિશાની (sign) પર સહમત ન થાય ત્યારે આંકડો છાપવાનો ઇનકાર કરે છે**.
તેને તમારા પોતાના મશીન પર એક મિનિટમાં ચલાવો:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

દરેક પાથ માપવામાં આવે છે, જેમાં હૂક ગેટ્સ અને એન્ફોર્સમેન્ટ પ્રોક્સીનો
સમાવેશ થાય છે, અને હાર્નેસ CI માં Linux, macOS અને Windows પર ચાલે છે.
જાણવા જેવા બે પરિણામો: Windows પર પ્રોક્સીનો ખર્ચ Linux કરતાં લગભગ સાત
ગણો વધારે છે, અને ડિમન હાલમાં એક કોરના લગભગ 12% સતત વાપરે છે, જે
અમારા પોતાના 5-10% ના બજેટ કરતાં વધારે છે. કાચો JSON, પદ્ધતિ, અને
હજુ શું માપાયું નથી તે [docs/OVERHEAD.md](docs/OVERHEAD.md) માં છે.

## કિંમત

| પ્લાન | તે શું આવરી લે છે | કિંમત |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, સંપૂર્ણ ડેશબોર્ડ, ફક્ત લોકલ | $0 |
| **Starter** | ઉપરના બાકીના બધા રનટાઇમ્સ, ફ્લીટ વ્યુ, ક્લાઉડ સિંક | $9 પ્રતિ નોડ / મહિનો |
| **Pro** | Starter + કંટ્રોલ અને ઇવેલ્યુએશન: એપ્રૂવલ્સ, ટૂલ-રિસ્ક પોલિસીસ, ઇવલ્સ, અસામાન્યતા ડિટેક્શન, કોસ્ટ ઓપ્ટિમાઇઝર, OTel એક્સપોર્ટ, ટેમ્પર-એવિડન્ટ ઑડિટ લોગ | $19 પ્રતિ નોડ / મહિનો |

વાર્ષિક પ્લાન, એન્ટરપ્રાઇઝ અને હાલના આંકડા
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** પર છે. સેલ્ફ-હોસ્ટેડ લાઇસન્સ
કીઓ ક્લાઉડ વગર કામ કરે છે (`clawmetry license`). ચોક્કસ ફ્રી/પેઇડ વિભાજન
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) માં છે.

## તમારો ડેટા તમારા મશીન પર જ રહે છે

ClawMetry લોકલ સેશન ફાઇલો અને લોગ્સ વાંચે છે. **તમે `clawmetry connect` ન
ચલાવો ત્યાં સુધી કોઈ સેશન ડેટા તમારા બોક્સમાંથી બહાર જતો નથી** — કોઈ પ્રોમ્પ્ટ્સ,
રિપ્લાય્સ, ટૂલ આર્ગ્યુમેન્ટ્સ, ફાઇલ કન્ટેન્ટ કે લોગ લાઇન્સ નહીં. જ્યારે તમે
કનેક્ટ કરો છો, ત્યારે સ્નેપશોટ એન્ડ-ટુ-એન્ડ એન્ક્રિપ્ટેડ હોય છે, જેની કી
તમારા મશીનમાંથી ક્યારેય બહાર જતી નથી, અને તમારા બ્રાઉઝરમાં ડિક્રિપ્ટ થાય છે.
જો કોઈ નોડ પાસે કી ન હોય, તો અપલોડ સ્કિપ થાય છે તેને બદલે ક્લિયર ટેક્સ્ટમાં
મોકલવાને, અને કોઈ સર્વર રિસ્પોન્સ તેને બંધ કરી શકતો નથી.

તમે કનેક્ટ કરો તે પહેલાં ડિફોલ્ટ રીતે બે વસ્તુઓ ચાલે છે, બંને ઑપ્ટ-આઉટ
કરી શકાય તેવી અને બંનેમાં કોઈ સેશન ડેટા હોતો નથી: એક એનોનિમસ ઇન્સ્ટોલ
પિંગ અને PyPI સામે વર્ઝન ચેક. ડિફોલ્ટ ઇન્સ્ટોલ સ્ટાર્ટઅપ બેનર લાઇન માટે
તમારો પબ્લિક IP પણ એકવાર લુકઅપ કરે છે. દરેક ડેસ્ટિનેશન, તે શું લઈ જાય છે,
અને તેને કેવી રીતે બંધ કરવું તેની યાદી [docs/EGRESS.md](docs/EGRESS.md) માં
છે; સેલ્ફ-હોસ્ટેડ, રિપોઇન્ટેડ અને એર-ગેપ્ડ ઇન્સ્ટોલ્સ કોઈ મરજિયાત આઉટબાઉન્ડ
કૉલ કરતા જ નથી.

ડિક્રિપ્શન તમારા બ્રાઉઝરમાં થાય છે, અમે તમને આપેલા કોડમાં. તે પહેલાં એક
વચન હતું; હવે તે એવી વસ્તુ છે જે તમે ચકાસી શકો છો. તમારી કીને સ્પર્શતી
દરેક લાઇન એક વાંચી શકાય તેવી ફાઇલમાં છે, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
જે wheel ની અંદર શિપ થાય છે અને Subresource Integrity હેશ સાથે
પિન કરીને, જેમ છે તેમ (verbatim) સર્વ કરવામાં આવે છે. બ્રાઉઝર અમે
પ્રકાશિત કરેલું જ ચલાવે છે તેની પુષ્ટિ કરવા:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

આ જે સાબિત નથી કરતું: અમે એ પેજ સર્વ કરીએ છીએ જે ફાઇલ લોડ કરે છે, તેથી
અમે અલગ પેજ સર્વ કરી શકીએ. ઇન્ટેગ્રિટી હેશ તમને કોમ્પ્રોમાઇઝ થયેલા CDN
થી બચાવે છે, વેન્ડરથી નહીં. તમને જે મળે છે તે એ છે કે કોઈપણ ફેરબદલ
ઇરાદાપૂર્વકની, પેજ સોર્સમાં દેખાય તેવી, અને PyPI પરના આર્ટિફેક્ટથી અલગ
હોવી જ પડે, જેને કોઈપણ ફેચ કરી શકે છે. સેલ્ફ-હોસ્ટિંગ અથવા લોકલ-ઓન્લી
રહેવાથી આ નિર્ભરતા સંપૂર્ણપણે દૂર થાય છે.

## ઇન્સ્ટોલ

```bash
pip install clawmetry     # પછી: clawmetry
```

અથવા વન-લાઇનર: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux કે Windows પર Python 3.8+ જોઈએ, અને એ જ મશીન પર ઓછામાં ઓછું
એક એજન્ટ રનટાઇમ. Docker સૂચનાઓ: [docs/DOCKER.md](docs/DOCKER.md).

અથવા એજન્ટ પાસે તમારા માટે તેને સેટ કરાવો. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
સ્કિલ Claude Code, Codex, Cursor, Gemini CLI, Copilot અથવા OpenCode ને
ClawMetry ઇન્સ્ટોલ કરવાનું, મશીન પરના એજન્ટ્સ શું કરી રહ્યા છે અને શું
ખર્ચ કરી રહ્યા છે તે જણાવવાનું, વિનંતી પર એક સેશન રોકવાનું, અને જોખમી
ટૂલ કૉલ્સને મંજૂરી માટે થોભાવવાનું શીખવે છે:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ડોક્સ

| | |
|---|---|
| [રનટાઇમ કમ્પેટિબિલિટી](docs/compatibility.md) | દરેક એડેપ્ટર શું વાંચે છે, અને રનટાઇમ કેવી રીતે ઉમેરવું |
| [કોન્ટેક્સ્ટ બ્લોઆઉટ](docs/CONTEXT_BLOWOUT.md) | પ્રોવાઇડર-પ્રમાણેની વિન્ડોઝ, કૉમ્પેક્શન વિ. ઓવરફ્લો, રનટાઇમ-પ્રમાણેનું કવરેજ |
| [ઓવરહેડ](docs/OVERHEAD.md) | ઇન્સ્ટ્રુમેન્ટેશનનો ખર્ચ કેટલો છે, માપેલો, તેને ફરીથી બનાવવા માટેના હાર્નેસ સાથે |
| [એન્ટાઇટલમેન્ટ્સ](docs/ENTITLEMENTS.md) | ફ્રી વિ. પેઇડ, ટિયર મેટ્રિક્સ, લાઇસન્સ CLI |
| [એપ્રૂવલ્સ અને પોલિસીસ](docs/APPROVALS.md) | પ્રી-એક્ઝિક્યુશન ગેટિંગ, રિસ્ક સ્કોરિંગ, ફોન એપ્રૂવલ્સ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ટ્રેસ ગમે ત્યાં એક્સપોર્ટ કરો, ગમે ત્યાંથી OTLP ઇન્જેસ્ટ કરો |
| [તમારો પોતાનો એજન્ટ લાવો](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain અંતથી અંત સુધી, ચલાવી શકાય તેવા ઉદાહરણો સાથે |
| [SDK ટ્રેકિંગ](docs/SDK_TRACKING.md) | તમે જાતે બનાવેલા એજન્ટ્સ માટે કિંમતનું એટ્રિબ્યુશન |
| [ચેટ ચેનલ્સ](docs/CHANNELS.md) | Flow માં દેખાતા ચેટ એડેપ્ટર્સ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | સેન્ડબોક્સ્ડ NVIDIA NemoClaw સેટઅપ્સ |
| [Docker](docs/DOCKER.md) | ઇમેજ, કમ્પોઝ, વોલ્યુમ માઉન્ટ્સ |
| [આર્કિટેક્ચર](ARCHITECTURE.md) · [ડેવલપમેન્ટ](docs/DEVELOPMENT.md) | અંદર તે કેવી રીતે કામ કરે છે; સોર્સમાંથી ચલાવવું |
| [ટેલિમેટ્રી](docs/TELEMETRY.md) | એનોનિમસ ઇન્સ્ટોલ અને ડેસ્કટોપ-ઓપન પિંગ્સ, અને તેમને કેવી રીતે બંધ કરવા |

## સ્ક્રીનશોટ્સ

નીચેનો દરેક આંકડો એક વાસ્તવિક મશીન પરથી, ફક્ત-વાંચવા-માટે, કંઈ પણ
સીડ કર્યા વગર છે.

**તે તમને જણાવે છે કે ક્યારે કંઈક ખોટું છે, ફક્ત શું થયું તે નહીં.**
ટોચ પર બે અસામાન્યતા બેનર્સ: રોજિંદા સરેરાશ કરતાં 7x ખર્ચ ચાલી રહ્યો છે,
અને 4.2x કિંમતનો સ્પાઇક. તેની નીચે, તાજેતરના 667 સેશન્સમાંથી 324
વેસ્ટ સિગ્નલ ધરાવે છે, કારણ પ્રમાણે વિભાજિત.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**તે તમને બતાવે છે કે પૈસા ક્યાં ગયા, દરેક વિન્ડોમાં.**
આજે $252.47, આ અઠવાડિયે $513.15, આ મહિને $1,312.92, દરેકની પાછળ
રહેલા ટોકન અને તમારું સબસ્ક્રિપ્શન કેટલું પહેલેથી કવર કરે છે તે સાથે.
તેની નીચે, લગભગ $1,128/મહિનો રિકવરેબલ તરીકે વિભાજિત અને $17,256/મહિનો
કેશ રીયુઝ દ્વારા પહેલેથી બચેલ.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**તે દોરે છે કે મેસેજ કેવી રીતે જવાબ બને છે.**
લાઇવ ફ્લો ડાયાગ્રામ: તમે, જે ચેનલ પર તે આવ્યો, ગેટવે, અત્યારે જવાબ
આપી રહેલો મોડેલ, અને દરેક ટૂલ જેના માટે તેણે હાથ લંબાવ્યો. કામ તેમાંથી
પસાર થાય ત્યારે નોડ્સ ઝગમગે છે.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**મશીન પરનો દરેક એજન્ટ, એક ટેબલમાં.**
તે શું ચલાવે છે, છેલ્લા 24 કલાકમાં અને તેના જીવનકાળ દરમિયાન તેની
કિંમત કેટલી છે, તે છેલ્લે ક્યારે જોવાયો, તેનો માલિક કોણ છે, અને
સબસ્ક્રિપ્શન બિલ કવર કરે છે કે નહીં. અહીં 14 એજન્ટ્સ, 3 સેશન કામ
કરી રહ્યા છે, 13 શાંત.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**તે બતાવે છે કે એક ટર્નનો સમય અને પૈસા ક્યાં ગયા, ટૂલ બાય ટૂલ.**
એક વાસ્તવિક સેશનનો એક ટર્ન: 11.2 મિનિટમાં 11 ટૂલ્સ, $1.16 માટે. દરેક
Bash કૉલ અને મોડેલ કૉલને ટાઇમલાઇન પર પોતાનો બાર મળે છે, જેથી 4.1
મિનિટ ચાલેલો કમાન્ડ અને 226ms ચાલેલો કમાન્ડ એક નજરમાં અલગ પડે.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**તે કામનું મૂલ્યાંકન કરે છે, ફક્ત ખર્ચનું નહીં.**
આ અઠવાડિયે A: 54 ટાસ્ક સાફ પરત આવ્યા, 2 ખરબચડા (rough) ટાસ્કનો ખર્ચ
$48.57 થયો, અને જે રનમાં ન્યાય કરવા માટે ખૂબ ઓછી પ્રવૃત્તિ હતી તેને
જીત તરીકે ગણવાને બદલે ગ્રેડમાંથી બાકાત રાખવામાં આવ્યા. દરેક ખરબચડો
રન તેના ટ્રેસ સાથે લિંક થાય છે.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**તે બતાવે છે કે કોન્ટેક્સ્ટ વિન્ડો કેમ ભરાતી રહે છે.**
છેલ્લા ટર્ન પર 1M-ટોકન વિન્ડોમાંથી 715K, 83.3% પીક, 4 કૉમ્પેક્શન જે
બધા ઓવરફ્લો પર નહીં પણ પ્રોએક્ટિવલી ફાયર થયા, અને તેની પાછળના દરેક
ટર્નનું યુટિલાઇઝેશન.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ડિટેક્શન તમારે કંઈ પણ કન્ફિગર કર્યા વગર ચાલે છે.**
બિલ્ટ-ઇન ડિટેક્ટર્સ ઇન્સ્ટોલથી જ ચાલુ છે: એજન્ટ શાંત થઈ ગયો, ટેલિમેટ્રી
ફીડ બંધ થઈ ગયું, કિંમતનો સ્પાઇક, ટોકન બર્સ્ટ, વધતી ભૂલો, એરર સ્પાઇક,
બજેટ થ્રેશોલ્ડ, થ્રેટ સિગ્નેચર મેચ થયું, સિક્યુરિટી ટૂલ ફાઇન્ડિંગ, સિક્યુરિટી
પોસ્ચર બદલાયું. તેની ઉપર તમારા પોતાના નિયમો વૈકલ્પિક છે.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**જોખમી કૉલ રોકવો ઑપ્ટ-ઇન છે, અને બંધ સ્થિતિમાં શિપ થાય છે.**
રિકર્સિવ ડિલીટ્સ, ફોર્સ પુશીસ, sudo, સિક્રેટ્સ, પેકેજ ઇન્સ્ટોલ્સ અને
આઉટબાઉન્ડ કૉલ્સ દરેકને એક નિયમ મળે છે જે તમે ચાલુ કરી શકો છો. તમે
તેમ ન કરો ત્યાં સુધી, ClawMetry ફક્ત જુએ છે અને કંઈ બદલતું નથી. એકવાર
ચાલુ કર્યા પછી, મેચ થતા કૉલ્સ અહીં (અથવા તમારા ફોન પર) મંજૂરી કે
ઇનકાર માટે રાહ જુએ છે.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

વધુ, દરેક રનટાઇમ પ્રમાણે: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## માન્યતા (Recognition)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## લાઇસન્સ

MIT · [@vivekchand](https://github.com/vivekchand) દ્વારા બનાવેલ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
