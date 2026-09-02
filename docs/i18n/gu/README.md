<!-- i18n-src:9767c8001c9c -->
> ગુજરાતી translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**તમારા એજન્ટને વિચારતું જુઓ.** **30 AI એજન્ટ રનટાઇમ** માટે રીઅલ-ટાઇમ ઓબ્ઝર્વેબિલિટી: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex અને બીજા 26. તમારા આખા એજન્ટ ફ્લીટ માટે એક જ ડેશબોર્ડ.

> 🌐 **આને આમાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. ઝીરો કન્ફિગ. બધું જાતે જ ડિટેક્ટ કરે છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે. ઝીરો કન્ફિગ: તમારી પાસે પહેલેથી જ જે એજન્ટ રનટાઇમ છે તેને શોધી કાઢે છે, તેમને ફક્ત વાંચે છે (read-only), અને તેમના ચાલવાની રીતમાં કંઈ પણ બદલતું નથી.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 એજન્ટ રનટાઇમ સાથે કામ કરે છે

**ઓપન સોર્સ એપમાં ફ્રી:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**પેઇડ પ્લાનમાં:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

દરેક રનટાઇમને એક જ સરખું ડેશબોર્ડ મળે છે. એકસાથે અનેક ચલાવો અને હેડરનું સ્વિચર દરેક ટેબને તેમાંથી કોઈ એક પર ફરીથી સ્કોપ કરી આપશે.

તમારો પોતાનો એજન્ટ SDK પર બનાવ્યો છે? ઈન્ટરસેપ્ટર તેના LLM કૉલ્સ પણ ટ્રેક કરે છે. જુઓ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## તમને શું મળે છે

- **સેશન્સ અને ટ્રાન્સક્રિપ્ટ્સ**: દરેક એજન્ટે શું કર્યું, ટર્ન બાય ટર્ન, રીપ્લે સાથે
- **કોસ્ટ અને ટોકન્સ**: રનટાઇમ, મોડલ, સેશન અને દિવસ પ્રમાણે, અસામાન્યતાના ફ્લેગ સાથે
- **ફ્લો**: ચેનલ્સ, મોડલ્સ અને ટૂલ્સ વચ્ચે ફરતા મેસેજિસનું લાઇવ ડાયાગ્રામ
- **બ્રેઇન**: રિઝનિંગ અને ટૂલ-કૉલ ઈવેન્ટ સ્ટ્રીમ, જેમ થાય તેમ
- **કોન્ટેક્સ્ટ બ્લોઆઉટ**: પ્રોવાઇડર પ્રમાણે વિન્ડોનું કદ, કોમ્પેક્શન વિરુદ્ધ ફોર્સ્ડ ઓવરફ્લો, ઉપરાંત દરેક રનટાઇમ પ્રમાણે આપણે શું *ન જોઈ શકીએ* તેનો નકશો ([કેવી રીતે](docs/CONTEXT_BLOWOUT.md))
- **મેમરી અને સ્કિલ્સ**: દરેક રનટાઇમે ખરેખર જે ફાઇલ્સ અને સ્કિલ્સ લોડ કરી તે
- **હેલ્થ અને લોગ્સ**: ડિસ્ક, મેમરી, એરર રેટ, રેટ લિમિટ્સ, લાઇવ લોગ સ્ટ્રીમ
- **એલર્ટ્સ**: બજેટ કેપ્સ, એરર સ્પાઇક્સ, એજન્ટ-ઓફલાઇન, Slack, Discord, PagerDuty, Telegram, ઈમેલ પર રૂટ કરેલા
- **એપ્રુવલ્સ**: જોખમી ટૂલ કૉલ્સને ચાલે *તે પહેલાં* અટકાવો અને તમારા ફોનથી એપ્રુવ કરો ([કેવી રીતે](docs/APPROVALS.md))

## કોન્ટેક્સ્ટ બ્લોઆઉટ, અને મોનિટરિંગની કિંમત

કોઈ પણ એજન્ટ-સરખામણી ટૂલ પર ભરોસો કરતાં પહેલાં જવાબ આપવા યોગ્ય બે પ્રશ્નો.

**રનટાઇમ્સ વચ્ચે તે કોન્ટેક્સ્ટ-વિન્ડો બ્લોઆઉટને કેવી રીતે હેન્ડલ કરે છે?**

યુટિલાઇઝેશન ટકાવારી એટલી જ પ્રમાણિક હોય છે જેટલી તેને જેનાથી ભાગવામાં આવે છે તે સંખ્યા હોય. ClawMetry [એક ટેબલ પરથી](clawmetry/context_windows.py) દરેક પ્રોવાઇડર પ્રમાણે વિન્ડોનું કદ નક્કી કરે છે, જેને તમે વાંચી શકો છો અને PR કરી શકો છો — તેમાં Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama અને GLM આવરી લેવાયા છે. તે બધા 26 રનટાઇમને એક જ વેન્ડરના માપદંડથી માપતું નથી. આ મહત્વનું છે: Anthropic ના 200K સામે માપેલો 300K નો GPT-5 ટર્ન ">100%, blown" દેખાય છે જ્યારે ખરેખર તે GPT-5 ના 400K માંથી 75% પર છે. એ જ માપદંડ ખરેખર ઓવરફ્લો થયેલા 130K ના DeepSeek ટર્નને આરામદાયક 65% તરીકે છુપાવે છે.

દરેક વિન્ડો પોતાનું મૂળ સાથે આવે છે: `model_table`, `explicit_marker`, `observed_floor`, અથવા જ્યારે આપણને મોડલ ખબર ન હોય ત્યારે પ્રમાણિક `default`. અંદાજ પર બનેલો ગેજ ક્યારેય લુકઅપ પર બનેલા ગેજ જેટલી સત્તાધિકારીતા સાથે નથી દેખાતો.

ClawMetry કેટલાક રનટાઇમ પર માત્ર કોમ્પેક્શન ઈવેન્ટ્સ જ જોઈ શકે છે. તેથી `GET /api/context-coverage` દરેક રનટાઇમ પ્રમાણે જણાવે છે કે **શૂન્યનો અર્થ "સાફ ચાલ્યું" છે કે "આપણને દેખાતું નથી"**. જે `0` ખરેખર અંધ હોવાનો અર્થ ધરાવે છે તે એમ જ કહે છે.
[સંપૂર્ણ વિગત](docs/CONTEXT_BLOWOUT.md)

**ઇન્સ્ટ્રુમેન્ટેશનની કિંમત શું છે?**

| પાથ | તમારા એજન્ટમાં ઉમેરાયું | ડિફોલ્ટ? |
|---|---|---|
| સેશન-ફાઇલ ટેલિંગ (બધા 30 રનટાઇમ) | **0**. અલગ પ્રોસેસ, તમારા એજન્ટમાં કોઈ ClawMetry કોડ નહીં | ચાલુ |
| HTTP ઈન્ટરસેપ્ટર (`CLAWMETRY_INTERCEPT=1`) | દરેક LLM કૉલ દીઠ **+0.44 ms**, અથવા 5s ના કૉલમાં 0.009% | બંધ |
| પ્રી-ટૂલ હૂક ગેટ (warm cache) | 36 ms ના ઇન્ટરપ્રિટર ફ્લોર ઉપર, દરેક ગેટેડ ટૂલ કૉલ દીઠ **+44 ms** | બંધ |
| એન્ફોર્સમેન્ટ પ્રોક્સી | દરેક LLM કૉલ દીઠ **+9.7 ms** | બંધ |

ડિમન હોસ્ટ કિંમત: **2,762 events/sec** ઇન્જેસ્ટ, ડિસ્ક પર **710 bytes/event** (100k ઈવેન્ટ્સ દીઠ 67.7 MB), અને વ્યસ્ત ઈન્સ્ટોલ પર સતત **~12% એક કોર**. છેલ્લો આંકડો આપણા પોતાના જાહેર કરેલા 5-10% બજેટ કરતાં વધારે છે, તેથી તેને છુપાવવાને બદલે પીછો કરવા જેવી બગ તરીકે પ્રકાશિત કરવામાં આવ્યો છે.

Apple M2 Pro પર `benchmarks/overhead.py` વડે માપવામાં આવ્યું. હાર્નેસ દરેક કન્ડિશનને અલગ પ્રોસેસમાં ચલાવે છે, તેમનો ક્રમ બદલતું રહે છે, અને **જ્યારે રાઉન્ડ્સ તેની નિશાની પર સહમત ન થાય ત્યારે નંબર છાપવાનો ઈનકાર કરે છે**. તેને તમારા પોતાના મશીન પર એક મિનિટમાં ચલાવો:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

હૂક ગેટ્સ અને એન્ફોર્સમેન્ટ પ્રોક્સી સહિત દરેક પાથ માપવામાં આવ્યો છે, અને હાર્નેસ CI માં Linux, macOS અને Windows પર ચાલે છે. જાણવા જેવા બે પરિણામો: પ્રોક્સીની કિંમત Windows પર Linux કરતાં લગભગ સાત ગણી વધારે છે, અને ડિમન હાલમાં આપણા પોતાના 5-10% બજેટ કરતાં વધુ, એટલે કે લગભગ 12% એક કોર સતત વાપરે છે. કાચો JSON, પદ્ધતિ, અને હજુ સુધી શું માપાયું નથી તે [docs/OVERHEAD.md](docs/OVERHEAD.md) માં છે.

## પ્રાઇસિંગ

| પ્લાન | તેમાં શું આવરી લેવાયું છે | કિંમત |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, સંપૂર્ણ ડેશબોર્ડ, ફક્ત લોકલ | $0 |
| **Starter** | ઉપરોક્ત દરેક બીજું રનટાઇમ, ફ્લીટ વ્યુ, ક્લાઉડ સિંક | $9 પ્રતિ નોડ / મહિનો |
| **Pro** | Starter + કંટ્રોલ અને એવેલ્યુએશન: એપ્રુવલ્સ, ટૂલ-રિસ્ક પોલિસીઝ, evals, અસામાન્યતા શોધ, કોસ્ટ ઓપ્ટિમાઇઝર, OTel એક્સપોર્ટ, ટેમ્પર-એવિડન્ટ ઓડિટ લોગ | $19 પ્રતિ નોડ / મહિનો |

વાર્ષિક પ્લાન, Enterprise અને હાલના આંકડા **[clawmetry.com/pricing](https://clawmetry.com/pricing)** પર ઉપલબ્ધ છે. સેલ્ફ-હોસ્ટેડ લાયસન્સ કીઓ ક્લાઉડ વગર પણ કામ કરે છે (`clawmetry license`). ફ્રી/પેઇડનું ચોક્કસ વિભાજન [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) માં છે.

## તમારો ડેટા તમારા મશીન પર જ રહે છે

ClawMetry લોકલ સેશન ફાઇલો અને લોગ વાંચે છે. **જ્યાં સુધી તમે `clawmetry connect` ન ચલાવો ત્યાં સુધી કોઈ સેશન ડેટા તમારા બોક્સમાંથી બહાર જતો નથી** — કોઈ પ્રોમ્પ્ટ્સ, જવાબો, ટૂલ આર્ગ્યુમેન્ટ્સ, ફાઇલ કન્ટેન્ટ કે લોગ લાઇન નહીં. જ્યારે તમે કનેક્ટ કરો છો, ત્યારે સ્નેપશોટ એ કીથી એન્ડ-ટુ-એન્ડ એન્ક્રિપ્ટેડ હોય છે જે તમારા મશીનમાંથી ક્યારેય બહાર જતી નથી, અને તમારા બ્રાઉઝરમાં ડિક્રિપ્ટ થાય છે. જો કોઈ નોડ પાસે કી ન હોય, તો અપલોડ ક્લિયર ટેક્સ્ટમાં મોકલવાને બદલે છોડી દેવાય છે, અને કોઈ સર્વર જવાબ તેને બંધ ન કરી શકે.

તમે કનેક્ટ કરો તે પહેલાં ડિફોલ્ટ રીતે બે વસ્તુઓ ચાલે છે, બંને ઓપ્ટ-આઉટ છે અને બંનેમાં કોઈ સેશન ડેટા સામેલ નથી: એક એનોનિમસ ઈન્સ્ટોલ પિંગ અને PyPI સામે વર્ઝન ચેક. ડિફોલ્ટ ઇન્સ્ટોલ સ્ટાર્ટઅપ બેનર લાઇન માટે તમારો પબ્લિક IP પણ એક વાર જુએ છે. દરેક ડેસ્ટિનેશન, તે શું ધરાવે છે અને તેને કેવી રીતે બંધ કરવું તેની યાદી [docs/EGRESS.md](docs/EGRESS.md) માં છે; સેલ્ફ-હોસ્ટેડ, રીપોઇન્ટેડ અને એર-ગેપ્ડ ઈન્સ્ટોલ કોઈ પણ સ્વૈચ્છિક આઉટબાઉન્ડ કૉલ કરતા નથી.

ડિક્રિપ્શન તમારા બ્રાઉઝરમાં થાય છે, એવા કોડમાં જે અમે તમને પીરસીએ છીએ. પહેલાં આ ફક્ત વચન હતું; હવે એ ચકાસી શકાય તેવી બાબત છે. તમારી કીને સ્પર્શતી દરેક લાઈન એક જ વાંચી શકાય તેવી ફાઇલમાં છે, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), જે wheel ની અંદર શિપ થાય છે અને Subresource Integrity હેશ સાથે પિન કરીને, જેમનું તેમ પીરસવામાં આવે છે. બ્રાઉઝર અમે પ્રકાશિત કરેલું જ ચલાવે છે તેની ખાતરી કરવા માટે:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

આ શું સાબિત નથી કરતું: અમે એ પેજ પણ પીરસીએ છીએ જે આ ફાઇલ લોડ કરે છે, તેથી અમે અલગ પેજ પણ પીરસી શકીએ. ઈન્ટેગ્રિટી હેશ તમને કોમ્પ્રોમાઇઝ થયેલા CDN થી બચાવે છે, વેન્ડરથી નહીં. તમને જે ફાયદો મળે છે તે એ છે કે કોઈ પણ અદલાબદલી ઈરાદાપૂર્વકની, પેજ સોર્સમાં દેખાય તેવી, અને PyPI પરના આર્ટિફેક્ટ કરતાં અલગ હોવી જોઈએ જેને કોઈ પણ ફેચ કરી શકે. સેલ્ફ-હોસ્ટિંગ કરવાથી કે ફક્ત લોકલ રહેવાથી આ આધારિતતા સંપૂર્ણપણે દૂર થાય છે.

## ઇન્સ્ટોલ

```bash
pip install clawmetry     # પછી: clawmetry
```

અથવા વન-લાઇનર: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux કે Windows પર Python 3.8+ જોઈએ, અને એ જ મશીન પર ઓછામાં ઓછું એક એજન્ટ રનટાઇમ. Docker સૂચનાઓ: [docs/DOCKER.md](docs/DOCKER.md).

## Docs

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | દરેક એડેપ્ટર શું વાંચે છે, અને રનટાઇમ કેવી રીતે ઉમેરવું |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | પ્રોવાઇડર-પ્રમાણે વિન્ડોઝ, કોમ્પેક્શન વિરુદ્ધ ઓવરફ્લો, રનટાઇમ-પ્રમાણે કવરેજ |
| [Overhead](docs/OVERHEAD.md) | ઇન્સ્ટ્રુમેન્ટેશનની કિંમત શું છે, માપેલી, તેને ફરીથી ઉત્પન્ન કરવાના હાર્નેસ સાથે |
| [Entitlements](docs/ENTITLEMENTS.md) | Free vs paid, ટાયર મેટ્રિક્સ, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | પ્રી-એક્ઝિક્યુશન ગેટિંગ, રિસ્ક સ્કોરિંગ, ફોન એપ્રુવલ્સ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ટ્રેસ ગમે ત્યાં એક્સપોર્ટ કરો, ગમે ત્યાંથી OTLP ઇન્જેસ્ટ કરો |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain સંપૂર્ણપણે, ચલાવી શકાય તેવા ઉદાહરણો સાથે |
| [SDK tracking](docs/SDK_TRACKING.md) | તમે જાતે બનાવેલા એજન્ટ્સ માટે કોસ્ટ એટ્રિબ્યુશન |
| [Chat channels](docs/CHANNELS.md) | Flow માં દેખાતા ચેટ એડેપ્ટર્સ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | સેન્ડબોક્સ્ડ NVIDIA NemoClaw સેટઅપ |
| [Docker](docs/DOCKER.md) | ઈમેજ, કમ્પોઝ, વોલ્યુમ માઉન્ટ |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | અંદર તે કેવી રીતે કામ કરે છે; સોર્સમાંથી ચલાવવું |
| [Telemetry](docs/TELEMETRY.md) | એનોનિમસ ઈન્સ્ટોલ અને ડેસ્કટોપ-ઓપન પિંગ્સ, અને તેમને કેવી રીતે બંધ કરવા |

## સ્ક્રીનશોટ્સ

નીચેનો દરેક આંકડો એક વાસ્તવિક મશીન પરથી છે, રીડ-ઓન્લી, કંઈ પણ સીડ કર્યા વગર.

**તે તમને જણાવે છે કે ક્યારે કંઈક ખોટું છે, ફક્ત શું થયું તે નહીં.**
ટોચ પર બે અસામાન્યતા બેનર: રોજિંદા સરેરાશ કરતાં 7 ગણો ખર્ચ ચાલી રહ્યો છે, અને 4.2 ગણો કોસ્ટ સ્પાઇક. તેમની નીચે, તાજેતરના 667 માંથી 324 સેશન્સ કારણ પ્રમાણે વર્ગીકૃત, વેસ્ટ સિગ્નલ ધરાવે છે.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**તે તમને દરેક વિન્ડોમાં પૈસા ક્યાં ગયા તે બતાવે છે.**
આજે $252.47, આ અઠવાડિયે $513.15, આ મહિને $1,312.92, દરેકની પાછળના ટોકન્સ સાથે અને તમારું સબસ્ક્રિપ્શન તેમાંથી કેટલું પહેલેથી કવર કરે છે. તેની નીચે, લગભગ $1,128/મહિનો રિકવરેબલ તરીકે વર્ગીકૃત અને cache reuse વડે પહેલેથી $17,256/મહિનો બચત.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**તે દોરી બતાવે છે કે મેસેજ કેવી રીતે જવાબ બને છે.**
લાઇવ ફ્લો ડાયાગ્રામ: તમે, જે ચેનલ પર તે આવ્યું, ગેટવે, હમણાં જવાબ આપી રહેલું મોડલ, અને દરેક ટૂલ જેને તેણે વાપર્યું. કામ તેમના મારફતે ફરે ત્યારે નોડ્સ ઝળકે છે.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**મશીન પરના દરેક એજન્ટ, એક જ ટેબલમાં.**
તે શું ચલાવે છે, છેલ્લા 24 કલાકમાં અને તેની આખી જિંદગીમાં તેની કિંમત શું છે, તેને છેલ્લે ક્યારે જોવાયો, તેનો માલિક કોણ છે, અને શું સબસ્ક્રિપ્શન બિલ કવર કરી રહ્યું છે. અહીં 14 એજન્ટ્સ, 3 સેશન્સ કામ કરી રહ્યાં છે, 13 શાંત.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**તે બતાવે છે કે એક ટર્નનો સમય અને પૈસા ટૂલ-બાય-ટૂલ ક્યાં ગયા.**
એક વાસ્તવિક સેશનનો એક ટર્ન: $1.16 માટે 11.2 મિનિટમાં 11 ટૂલ્સ. દરેક Bash કૉલ અને મોડલ કૉલને ટાઈમલાઈન પર પોતાનો બાર મળે છે, જેથી 4.1 મિનિટ ચાલેલો કમાન્ડ અને 226ms ચાલેલો કમાન્ડ એક નજરમાં અલગ પડે.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**તે કામને ગ્રેડ કરે છે, ફક્ત ખર્ચને નહીં.**
આ અઠવાડિયે A: 54 ટાસ્ક ચોખ્ખા પાછા આવ્યા, 2 ખરબચડા ટાસ્કની કિંમત $48.57 હતી, અને જે રન અભિપ્રાય આપવા માટે પૂરતી પ્રવૃત્તિ ધરાવતા નથી તેમને જીત ગણવાને બદલે ગ્રેડમાંથી બાકાત રખાયા છે. દરેક ખરબચડો રન પોતાના ટ્રેસ સાથે લિંક છે.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**તે બતાવે છે કે કોન્ટેક્સ્ટ વિન્ડો કેમ સતત ભરાતી રહે છે.**
છેલ્લા ટર્ન પર 1M-ટોકન વિન્ડોમાંથી 715K, 83.3% ની ટોચ, 4 કોમ્પેક્શન જે બધા ઓવરફ્લો પર નહીં પણ પ્રોએક્ટિવલી ફાયર થયા, ઉપરાંત તેની પાછળના દરેક ટર્નનું યુટિલાઇઝેશન.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ડિટેક્શન તમારે કંઈ પણ કન્ફિગર કર્યા વગર ચાલે છે.**
ઈન્સ્ટોલથી જ બિલ્ટ-ઈન ડિટેક્ટર્સ ચાલુ છે: એજન્ટ શાંત થઈ ગયો, ટેલિમેટ્રી ફીડ બંધ થઈ ગયો, કોસ્ટ સ્પાઇક, ટોકન બર્સ્ટ, વધતી ભૂલો, એરર સ્પાઇક, બજેટ થ્રેશોલ્ડ, ધમકીની સિગ્નેચર મેચ થઈ, સિક્યુરિટી ટૂલ ફાઇન્ડિંગ, સિક્યુરિટી પોસ્ચર બદલાયું. તમારા પોતાના નિયમો તેની ઉપર વૈકલ્પિક છે.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**જોખમી કૉલને રોકવું ઓપ્ટ-ઈન છે, અને બંધ સ્થિતિમાં શિપ થાય છે.**
રિકર્સિવ ડિલીટ્સ, ફોર્સ પુશ, sudo, સિક્રેટ્સ, પેકેજ ઇન્સ્ટોલ અને આઉટબાઉન્ડ કૉલ્સ, દરેકને એક નિયમ મળે છે જેને તમે ચાલુ કરી શકો છો. જ્યાં સુધી તમે ન કરો ત્યાં સુધી, ClawMetry ફક્ત જુએ છે અને કંઈ પણ બદલતું નથી. એક વાર ચાલુ કર્યા પછી, મેચ થતા કૉલ્સ અહીં (અથવા તમારા ફોન પર) એપ્રુવ કે ડિનાય માટે રાહ જુએ છે.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

વધુ, દરેક રનટાઇમ પ્રમાણે: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## સ્ટાર હિસ્ટ્રી

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## લાયસન્સ

MIT · [@vivekchand](https://github.com/vivekchand) દ્વારા બનાવવામાં આવ્યું · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
