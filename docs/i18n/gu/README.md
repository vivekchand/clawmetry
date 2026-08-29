<!-- i18n-src:d21bea5161e0 -->
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

**તમારા એજન્ટને વિચારતું જુઓ.** **30 AI એજન્ટ રનટાઈમ્સ** માટે રીઅલ-ટાઈમ ઓબ્ઝર્વેબિલિટી: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex અને બીજા 26. તમારા આખા એજન્ટ ફ્લીટ માટે એક જ ડેશબોર્ડ.

> 🌐 **આને આ ભાષામાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. શૂન્ય કન્ફિગ. બધું ઓટો-ડિટેક્ટ થાય છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે. શૂન્ય કન્ફિગ: તમારી પાસે પહેલેથી જે એજન્ટ રનટાઈમ્સ છે તેને શોધી કાઢે છે, તેમને ફક્ત વાંચે છે, અને તેઓ કઈ રીતે ચાલે છે તેમાં કંઈ પણ બદલાવ કરતું નથી.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 એજન્ટ રનટાઈમ્સ સાથે કામ કરે છે

**ઓપન સોર્સ એપમાં મફત:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**પેઇડ પ્લાન પર:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

દરેક રનટાઈમને એ જ ડેશબોર્ડ મળે છે. એકસાથે અનેક રન કરો અને હેડર સ્વિચર દરેક ટૅબને તેમાંથી કોઈપણ એક પર ફરીથી સ્કોપ કરી દે છે.

તમારો પોતાનો એજન્ટ SDK પર બનાવ્યો છે? ઈન્ટરસેપ્ટર તેના LLM કૉલ્સ પણ ટ્રેક કરે છે. જુઓ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## તમને શું મળે છે

- **સેશન્સ અને ટ્રાન્સ્ક્રિપ્ટ્સ**: દરેક એજન્ટે શું કર્યું, ટર્ન-બાય-ટર્ન, રિપ્લે સાથે
- **ખર્ચ અને ટોકન્સ**: રનટાઈમ, મોડેલ, સેશન અને દિવસ પ્રમાણે, અસાધારણતાની નિશાનીઓ સાથે
- **ફ્લો**: ચેનલો, મોડેલો અને ટૂલ્સમાં ફરતા મેસેજોનું લાઈવ ડાયાગ્રામ
- **બ્રેઈન**: રિઝનિંગ અને ટૂલ-કૉલ ઈવેન્ટ સ્ટ્રીમ, જેમ જેમ થાય તેમ
- **કોન્ટેક્સ્ટ બ્લોઆઉટ**: પ્રોવાઈડર પ્રમાણે માપેલી વિન્ડો યુટિલાઈઝેશન, કોમ્પેક્શન વિ. ફોર્સ્ડ ઓવરફ્લો, વત્તા આપણે શું *જોઈ નથી શકતા* તેનો રનટાઈમ-પ્રમાણે નકશો ([કેવી રીતે](docs/CONTEXT_BLOWOUT.md))
- **મેમરી અને સ્કિલ્સ**: દરેક રનટાઈમે ખરેખર જે ફાઈલો અને સ્કિલ્સ લોડ કરી તે
- **હેલ્થ અને લોગ્સ**: ડિસ્ક, મેમરી, એરર રેટ્સ, રેટ લિમિટ્સ, લાઈવ લોગ સ્ટ્રીમ
- **એલર્ટ્સ**: બજેટ કેપ્સ, એરર સ્પાઈક્સ, એજન્ટ-ઑફલાઈન, Slack, Discord, PagerDuty, Telegram, Email પર રૂટ થયેલ
- **અપ્રૂવલ્સ**: જોખમી ટૂલ કૉલ્સને ચાલે *તે પહેલાં* થોભાવો અને તમારા ફોનથી અપ્રૂવ કરો ([કેવી રીતે](docs/APPROVALS.md))

## કોન્ટેક્સ્ટ બ્લોઆઉટ, અને મોનિટરિંગનો ખર્ચ કેટલો

કોઈપણ એજન્ટ-સરખામણી ટૂલ પર ભરોસો કરતાં પહેલાં જવાબ આપવા લાયક બે પ્રશ્નો.

**તે રનટાઈમ્સમાં કોન્ટેક્સ્ટ-વિન્ડો બ્લોઆઉટ કેવી રીતે હેન્ડલ કરે છે?**

યુટિલાઈઝેશન ટકાવારી એટલી જ પ્રામાણિક હોય છે જેટલો તેને વિભાજિત કરવા વપરાયેલ આંકડો પ્રામાણિક હોય. ClawMetry [એક ટેબલ](clawmetry/context_windows.py) પરથી પ્રોવાઈડર પ્રમાણે વિન્ડોનું માપ કાઢે છે, જેને તમે વાંચી અને PR કરી શકો છો, જેમાં Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama અને GLM આવરી લેવાયેલ છે. તે બધા 26 રનટાઈમ્સને એક જ વેન્ડરના માપદંડથી માપતું નથી. આ મહત્વનું છે: Anthropic ના 200K સામે માપેલો 300K GPT-5 ટર્ન ">100%, બ્લોન" દેખાય છે જ્યારે તે ખરેખર GPT-5 ના 400K ના 75% પર છે. એ જ માપદંડ ખરેખર ઓવરફ્લો થયેલા 130K DeepSeek ટર્નને આરામદાયક 65% તરીકે છુપાવે છે.

દરેક વિન્ડો પોતાનું મૂળ સાથે લઈને આવે છે: `model_table`, `explicit_marker`, `observed_floor`, અથવા જ્યારે આપણને મોડેલ ખબર ન હોય ત્યારે પ્રામાણિક `default`. અંદાજ પર બનેલું ગેજ ક્યારેય લુકઅપ પર બનેલા ગેજ જેટલી જ પ્રામાણિકતાથી રેન્ડર થતું નથી.

ClawMetry ફક્ત કેટલાક રનટાઈમ્સ પર જ કોમ્પેક્શન ઈવેન્ટ્સ જોઈ શકે છે. તેથી `GET /api/context-coverage` દરેક રનટાઈમ માટે જણાવે છે કે **શૂન્યનો અર્થ "સાફ ચાલ્યું" છે કે "આપણને દેખાતું નથી"**. જે `0` ખરેખર બ્લાઈન્ડ સૂચવે છે તે એમ જ કહે છે.
[સંપૂર્ણ વિગત](docs/CONTEXT_BLOWOUT.md)

**ઈન્સ્ટ્રુમેન્ટેશનનો ખર્ચ કેટલો છે?**

| પાથ | તમારા એજન્ટમાં ઉમેરાયું | ડિફૉલ્ટ? |
|---|---|---|
| સેશન-ફાઈલ ટેલિંગ (તમામ 30 રનટાઈમ્સ) | **0**. અલગ પ્રોસેસ, તમારા એજન્ટમાં કોઈ ClawMetry કોડ નથી | on |
| HTTP ઈન્ટરસેપ્ટર (`CLAWMETRY_INTERCEPT=1`) | દરેક LLM કૉલ દીઠ **+0.44 ms**, અથવા 5s ના કૉલના 0.009% | off |
| પ્રી-ટૂલ હૂક ગેટ (વોર્મ કેશ) | 36 ms ના ઈન્ટરપ્રિટર ફ્લોર ઉપર, દરેક ગેટેડ ટૂલ કૉલ દીઠ **+44 ms** | off |
| એન્ફોર્સમેન્ટ પ્રોક્સી | દરેક LLM કૉલ દીઠ **+9.7 ms** | off |

ડિમન હોસ્ટ ખર્ચ: **2,762 ઈવેન્ટ્સ/સેકન્ડ** ઈન્જેસ્ટ, ડિસ્ક પર **710 બાઈટ્સ/ઈવેન્ટ** (100k ઈવેન્ટ્સ દીઠ 67.7 MB), અને વ્યસ્ત ઈન્સ્ટોલ પર સતત **એક કોરના ~12%**. છેલ્લો આંકડો આપણા પોતાના જણાવેલા 5-10% ના બજેટ કરતાં વધારે છે, તેથી તેને પાનેથી હટાવવાને બદલે પાછળ પડવા જેવો બગ ગણી પ્રકાશિત કરવામાં આવ્યો છે.

Apple M2 Pro પર `benchmarks/overhead.py` વડે માપેલું. હાર્નેસ દરેક કન્ડિશન અલગ પ્રોસેસમાં ચલાવે છે, તેમનો ક્રમ બદલતું રહે છે, અને **જ્યારે રાઉન્ડ્સ તેની નિશાની (સાઈન) પર અસહમત હોય ત્યારે આંકડો છાપવાની ના પાડે છે**. તેને તમારા પોતાના મશીન પર એક મિનિટમાં ચલાવો:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

હૂક ગેટ્સ અને એન્ફોર્સમેન્ટ પ્રોક્સી સહિત દરેક પાથ માપવામાં આવે છે, અને હાર્નેસ CI માં Linux, macOS અને Windows પર ચાલે છે. જાણવા જેવા બે પરિણામો: Windows પર પ્રોક્સીનો ખર્ચ Linux કરતાં લગભગ સાત ગણો વધારે છે, અને ડિમન હાલમાં એક કોરના લગભગ 12% સતત વાપરે છે, જે આપણા પોતાના 5-10% ના બજેટ કરતાં વધારે છે. કાચો JSON, પદ્ધતિ, અને હજુ સુધી શું માપાયું નથી તે [docs/OVERHEAD.md](docs/OVERHEAD.md) માં છે.

## પ્રાઈસિંગ

| પ્લાન | શું આવરી લે છે | કિંમત |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, સંપૂર્ણ ડેશબોર્ડ, ફક્ત લોકલ | $0 |
| **Starter** | ઉપરના બાકીના તમામ રનટાઈમ્સ, ફ્લીટ વ્યૂ, ક્લાઉડ સિંક | $9 પ્રતિ નોડ / મહિનો |
| **Pro** | Starter + કંટ્રોલ અને ઈવેલ્યુએશન: અપ્રૂવલ્સ, ટૂલ-રિસ્ક પોલિસીઝ, ઈવલ્સ, અસાધારણતા શોધ, કોસ્ટ ઓપ્ટિમાઈઝર, OTel એક્સપોર્ટ, ટેમ્પર-એવિડન્ટ ઓડિટ લોગ | $19 પ્રતિ નોડ / મહિનો |

વાર્ષિક પ્લાન્સ, Enterprise અને હાલના આંકડા **[clawmetry.com/pricing](https://clawmetry.com/pricing)** પર છે. સેલ્ફ-હોસ્ટેડ લાયસન્સ કી ક્લાઉડ વગર કામ કરે છે (`clawmetry license`). ચોક્કસ ફ્રી/પેઈડ વિભાજન [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) માં છે.

## તમારો ડેટા તમારા મશીન પર જ રહે છે

ClawMetry લોકલ સેશન ફાઈલો અને લોગ્સ વાંચે છે. **જ્યાં સુધી તમે `clawmetry connect` ચલાવો નહીં ત્યાં સુધી કોઈ સેશન ડેટા તમારા બોક્સમાંથી બહાર જતો નથી** — કોઈ પ્રોમ્પ્ટ્સ, જવાબો, ટૂલ આર્ગ્યુમેન્ટ્સ, ફાઈલ કન્ટેન્ટ કે લોગ લાઈન્સ નહીં. જ્યારે તમે કનેક્ટ કરો છો, ત્યારે સ્નેપશોટ એ ચાવીથી એન્ડ-ટુ-એન્ડ એન્ક્રિપ્ટેડ હોય છે જે ક્યારેય તમારા મશીનમાંથી બહાર જતી નથી, અને તમારા બ્રાઉઝરમાં ડિક્રિપ્ટ થાય છે. જો કોઈ નોડ પાસે ચાવી ન હોય, તો અપલોડ સ્કિપ કરવામાં આવે છે, ખુલ્લામાં મોકલવાને બદલે, અને કોઈ સર્વર જવાબ તેને બંધ કરી શકતો નથી.

તમે કનેક્ટ કરો તે પહેલાં ડિફૉલ્ટ રીતે બે વસ્તુઓ ચાલે છે, બંને ઓપ્ટ-આઉટ કરી શકાય એવી અને બંનેમાં કોઈ સેશન ડેટા હોતો નથી: એક એનોનિમસ ઈન્સ્ટોલ પિંગ અને PyPI સામે વર્ઝન ચેક. ડિફૉલ્ટ ઈન્સ્ટોલ સ્ટાર્ટઅપ બેનર લાઈન માટે તમારો પબ્લિક IP પણ એકવાર જુએ છે. દરેક ડેસ્ટિનેશન, તે શું લઈ જાય છે અને તેને કેવી રીતે બંધ કરવું તે [docs/EGRESS.md](docs/EGRESS.md) માં લિસ્ટ કરેલ છે; સેલ્ફ-હોસ્ટેડ, રિપોઈન્ટેડ અને એર-ગેપ્ડ ઈન્સ્ટોલ્સ કોઈ પણ મરજી મુજબનો આઉટબાઉન્ડ કૉલ કરતા જ નથી.

ડિક્રિપ્શન તમારા બ્રાઉઝરમાં થાય છે, અમે તમને આપેલા કોડમાં. એ પહેલાં એક વચન હતું; હવે એ ચકાસી શકાય એવી બાબત છે. તમારી ચાવીને સ્પર્શતી દરેક લાઈન એક વાંચી શકાય એવી ફાઈલમાં છે, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), જે વ્હીલની અંદર શિપ થાય છે અને શબ્દશઃ સર્વ થાય છે, Subresource Integrity હેશથી પિન કરેલી. બ્રાઉઝર એ જ ચલાવે છે જે અમે પ્રકાશિત કર્યું છે તેની ખાતરી કરવા:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

તે શું સાબિત નથી કરતું: અમે એ પેજ સર્વ કરીએ છીએ જે ફાઈલ લોડ કરે છે, તેથી અમે અલગ પેજ સર્વ કરી શકીએ છીએ. ઈન્ટેગ્રિટી હેશ તમને કોમ્પ્રોમાઈઝ થયેલ CDN થી બચાવે છે, વેન્ડરથી નહીં. તમને જે મળે છે તે એ છે કે કોઈપણ બદલી જાણી જોઈને, પેજ સોર્સમાં દેખાય એ રીતે, અને PyPI પરના આર્ટિફેક્ટ કરતાં અલગ કરવી પડે છે જેને કોઈપણ મેળવી શકે છે. સેલ્ફ-હોસ્ટિંગ કરવાથી અથવા લોકલ-ઓન્લી રહેવાથી આ નિર્ભરતા સંપૂર્ણપણે દૂર થાય છે.

## ઈન્સ્ટોલ

```bash
pip install clawmetry     # પછી: clawmetry
```

અથવા વન-લાઈનર: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux કે Windows પર Python 3.8+ જોઈએ, અને એ જ મશીન પર ઓછામાં ઓછો એક એજન્ટ રનટાઈમ. Docker સૂચનાઓ: [docs/DOCKER.md](docs/DOCKER.md).

## દસ્તાવેજો

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | દરેક એડપ્ટર શું વાંચે છે, અને રનટાઈમ કેવી રીતે ઉમેરવો |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | પ્રોવાઈડર-પ્રમાણે વિન્ડોઝ, કોમ્પેક્શન વિ. ઓવરફ્લો, રનટાઈમ-પ્રમાણે કવરેજ |
| [Overhead](docs/OVERHEAD.md) | ઈન્સ્ટ્રુમેન્ટેશનનો ખર્ચ કેટલો, માપેલો, તેને ફરીથી ઉત્પન્ન કરવાના હાર્નેસ સાથે |
| [Entitlements](docs/ENTITLEMENTS.md) | ફ્રી વિ. પેઈડ, ટાયર મેટ્રિક્સ, લાયસન્સ CLI |
| [Approvals & policies](docs/APPROVALS.md) | પ્રી-એક્ઝિક્યુશન ગેટિંગ, રિસ્ક સ્કોરિંગ, ફોન અપ્રૂવલ્સ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ટ્રેસ ગમે ત્યાં એક્સપોર્ટ કરો, ગમે ત્યાંથી OTLP ઈન્જેસ્ટ કરો |
| [SDK tracking](docs/SDK_TRACKING.md) | તમે જાતે બનાવેલા એજન્ટ્સ માટે ખર્ચ એટ્રિબ્યુશન |
| [Chat channels](docs/CHANNELS.md) | Flow માં દેખાડેલા ચેટ એડપ્ટર્સ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | સેન્ડબોક્સ્ડ NVIDIA NemoClaw સેટઅપ્સ |
| [Docker](docs/DOCKER.md) | ઈમેજ, કમ્પોઝ, વોલ્યુમ માઉન્ટ્સ |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | અંદરથી તે કેવી રીતે કામ કરે છે; સોર્સમાંથી ચલાવવું |
| [Telemetry](docs/TELEMETRY.md) | એનોનિમસ ઈન્સ્ટોલ અને ડેસ્કટોપ-ઓપન પિંગ્સ, અને તેમને કેવી રીતે બંધ કરવા |

## સ્ક્રીનશોટ્સ

નીચેનો દરેક આંકડો એક વાસ્તવિક મશીન પરથી છે, ફક્ત વાંચીને, કંઈ પણ સીડ કર્યા વગર.

**કંઈક ખોટું હોય ત્યારે તે તમને જણાવે છે, ફક્ત શું થયું તે નહીં.**
ટોચ પર બે અસાધારણતાના બેનર: રોજિંદા સરેરાશ કરતાં 7x ખર્ચ ચાલી રહ્યો છે, અને 4.2x કોસ્ટ સ્પાઈક. તેમની નીચે, તાજેતરના 667 સેશન્સમાંથી 324 માં કચરાની નિશાની છે, કારણ પ્રમાણે અલગ પાડેલી.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**પૈસા ક્યાં ગયા તે તે તમને દરેક વિન્ડોમાં બતાવે છે.**
આજે $252.47, આ અઠવાડિયે $513.15, આ મહિને $1,312.92, દરેકની પાછળના ટોકન્સ સાથે અને તમારું સબસ્ક્રિપ્શન તેમાંથી કેટલું પહેલેથી કવર કરે છે તે સાથે. તેની નીચે, લગભગ $1,128/મહિનો પુનઃપ્રાપ્ય તરીકે અલગ પાડેલો અને કેશ પુનઃઉપયોગથી પહેલેથી બચેલા $17,256/મહિનો.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**મેસેજ કેવી રીતે જવાબ બને છે તે તે દોરી બતાવે છે.**
લાઈવ ફ્લો ડાયાગ્રામ: તમે, જે ચેનલ પર તે આવ્યો, ગેટવે, અત્યારે જવાબ આપી રહેલો મોડેલ, અને દરેક ટૂલ જેની પાસે તે પહોંચ્યો. કામ તેમનામાંથી પસાર થાય તેમ નોડ્સ પ્રકાશિત થાય છે.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**મશીન પરનો દરેક એજન્ટ, એક જ ટેબલમાં.**
તે શું ચલાવે છે, છેલ્લા 24 કલાકમાં અને તેના જીવનકાળમાં તેનો ખર્ચ કેટલો, છેલ્લે ક્યારે જોવાયો, તેનો માલિક કોણ છે, અને શું સબસ્ક્રિપ્શન બિલ કવર કરી રહ્યું છે. અહીં 14 એજન્ટ્સ, 3 સેશન્સ કામ કરી રહ્યા છે, 13 શાંત.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**એક ટર્નનો સમય અને પૈસા ટૂલ-બાય-ટૂલ ક્યાં ગયા તે તે બતાવે છે.**
એક વાસ્તવિક સેશનનો એક ટર્ન: 11.2 મિનિટમાં 11 ટૂલ્સ, $1.16 માટે. દરેક Bash કૉલ અને મોડેલ કૉલને ટાઈમલાઈન પર પોતાનો બાર મળે છે, જેથી 4.1 મિનિટ ચાલેલો કમાન્ડ અને 226ms ચાલેલો કમાન્ડ એક નજરમાં અલગ પડે.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**તે કામને ગ્રેડ કરે છે, ફક્ત ખર્ચને નહીં.**
આ અઠવાડિયે A: 54 ટાસ્ક સાફ પાછા આવ્યા, 2 ખરબચડા (rough) ટાસ્કનો ખર્ચ $48.57 થયો, અને જે રન્સનું મૂલ્યાંકન કરવા માટે પૂરતી પ્રવૃત્તિ નથી તેમને જીત તરીકે ગણવાને બદલે ગ્રેડમાંથી બહાર રાખવામાં આવ્યા છે. દરેક ખરબચડું રન તેના ટ્રેસ સાથે લિંક થાય છે.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**કોન્ટેક્સ્ટ વિન્ડો કેમ ભરાતી રહે છે તે તે બતાવે છે.**
છેલ્લા ટર્ન પર 1M-ટોકનની વિન્ડોમાંથી 715K, 83.3% પીક, 4 કોમ્પેક્શન જે બધા ઓવરફ્લો પર નહીં પણ પ્રો-એક્ટિવલી ફાયર થયા, અને તેની પાછળના દરેક ટર્નનું યુટિલાઈઝેશન.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**તમારે કંઈ પણ કન્ફિગર કર્યા વગર ડિટેક્શન ચાલે છે.**
બિલ્ટ-ઈન ડિટેક્ટર્સ ઈન્સ્ટોલથી જ ચાલુ છે: એજન્ટ શાંત થઈ ગયો, ટેલિમેટ્રી ફીડ બંધ થઈ ગયો, કોસ્ટ સ્પાઈક, ટોકન બર્સ્ટ, એરર્સ વધી રહ્યા છે, એરર સ્પાઈક, બજેટ થ્રેશોલ્ડ, થ્રેટ સિગ્નેચર મેચ થયું, સિક્યુરિટી ટૂલ ફાઈન્ડિંગ, સિક્યુરિટી પોસ્ચર બદલાયું. તમારા પોતાના નિયમો તેની ઉપર વૈકલ્પિક છે.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**જોખમી કૉલ રોકવું ઓપ્ટ-ઈન છે, અને ડિફૉલ્ટ રીતે બંધ શિપ થાય છે.**
રિકર્સિવ ડિલીટ, ફોર્સ પુશ, sudo, સિક્રેટ્સ, પેકેજ ઈન્સ્ટોલ્સ અને આઉટબાઉન્ડ કૉલ્સ, દરેકને એક નિયમ મળે છે જેને તમે ચાલુ કરી શકો છો. જ્યાં સુધી તમે તે ના કરો, ClawMetry જુએ છે અને કંઈ પણ બદલતું નથી. એકવાર એક ચાલુ કરો, પછી મેચ થતા કૉલ્સ અહીં (અથવા તમારા ફોન પર) અપ્રૂવ કે ડિનાય માટે રાહ જુએ છે.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

વધુ, રનટાઈમ પ્રમાણે: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
