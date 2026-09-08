<!-- i18n-src:88be2deff5d5 -->
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

**તમારા એજન્ટને વિચારતું જુઓ.** **30 AI એજન્ટ રનટાઇમ્સ** માટે રીઅલ-ટાઇમ ઓબ્ઝર્વેબિલિટી: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex અને બીજા 26. તમારા સમગ્ર એજન્ટ ફ્લીટ માટે એક ડેશબોર્ડ.

> 🌐 **આ ભાષામાં વાંચો:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [વધુ →](docs/i18n/)

એક કમાન્ડ. શૂન્ય કન્ફિગ. બધું જ ઑટો-ડિટેક્ટ થાય છે.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** પર ખૂલે છે. શૂન્ય કન્ફિગ: તમારી પાસે પહેલેથી જ જે એજન્ટ રનટાઇમ્સ છે તેમને તે શોધી કાઢે છે, તેમને ફક્ત-વાંચવા (read-only) માટે વાંચે છે, અને તેઓ કેવી રીતે ચાલે છે તેમાં કંઈ પણ બદલતું નથી.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 એજન્ટ રનટાઇમ્સ સાથે કામ કરે છે

**ઓપન સોર્સ એપમાં મફત:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**પેઇડ પ્લાન પર:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

દરેક રનટાઇમને એક જ ડેશબોર્ડ મળે છે. એકસાથે અનેક ચલાવો અને હેડર સ્વિચર દરેક ટૅબને તેમાંથી કોઈ એક પર ફરીથી સ્કોપ કરી દેશે.

તમારો પોતાનો એજન્ટ SDK પર બનાવ્યો છે? ઇન્ટરસેપ્ટર તેના LLM કૉલ્સ પણ ટ્રૅક કરે છે. જુઓ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## તમને શું મળે છે

- **સેશન્સ અને ટ્રાન્સક્રિપ્ટ્સ**: દરેક એજન્ટે શું કર્યું, ટર્ન બાય ટર્ન, રિપ્લે સાથે
- **ખર્ચ અને ટોકન્સ**: રનટાઇમ, મોડેલ, સેશન અને દિવસ પ્રમાણે, અસામાન્યતા (anomaly) ફ્લેગ્સ સાથે
- **ફ્લો**: ચેનલો, મોડેલો અને ટૂલ્સ મારફતે વહેતા સંદેશાઓનું લાઇવ ડાયાગ્રામ
- **બ્રેઇન**: રિઝનિંગ અને ટૂલ-કૉલ ઇવેન્ટ સ્ટ્રીમ, જેમ જેમ તે થાય તેમ
- **કોન્ટેક્સ્ટ બ્લોઆઉટ**: પ્રોવાઇડર પ્રમાણે માપેલી વિન્ડો યુટિલાઇઝેશન, કોમ્પેક્શન વિરુદ્ધ ફોર્સ્ડ ઓવરફ્લો, ઉપરાંત આપણે શું *જોઈ ન શકીએ* તેનો રનટાઇમ-પ્રમાણેનો નકશો ([કેવી રીતે](docs/CONTEXT_BLOWOUT.md))
- **મેમરી અને સ્કિલ્સ**: દરેક રનટાઇમે ખરેખર જે ફાઇલો અને સ્કિલ્સ લોડ કરી તે
- **હેલ્થ અને લોગ્સ**: ડિસ્ક, મેમરી, એરર દર, રેટ લિમિટ્સ, લાઇવ લોગ સ્ટ્રીમ
- **એલર્ટ્સ**: બજેટ કેપ્સ, એરર સ્પાઇક્સ, એજન્ટ-ઓફલાઇન, Slack, Discord, PagerDuty, Telegram, Email પર રૂટ થાય છે
- **અપ્રૂવલ્સ**: જોખમી ટૂલ કૉલ્સને ચાલે *તે પહેલાં* થોભાવો અને તમારા ફોન પરથી મંજૂર કરો ([કેવી રીતે](docs/APPROVALS.md))

## કોન્ટેક્સ્ટ બ્લોઆઉટ, અને નિરીક્ષણ કરવાનો ખર્ચ

કોઈ પણ એજન્ટ-સરખામણી ટૂલ પર વિશ્વાસ કરતાં પહેલાં જવાબ આપવા યોગ્ય બે પ્રશ્નો.

**એ રનટાઇમ્સમાં કોન્ટેક્સ્ટ-વિન્ડો બ્લોઆઉટને કેવી રીતે હેન્ડલ કરે છે?**

યુટિલાઇઝેશન ટકાવારી ફક્ત એટલી જ પ્રામાણિક હોય છે જેટલી તે જેની સાથે ભાગ કરે છે તે. ClawMetry [એક ટેબલ](clawmetry/context_windows.py) પરથી પ્રોવાઇડર પ્રમાણે વિન્ડોનું કદ નક્કી કરે છે જેને તમે વાંચી શકો છો અને PR કરી શકો છો, જે Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama અને GLM ને આવરી લે છે. તે એક જ વેન્ડરના માપદંડથી બધા 30 રનટાઇમ્સને માપતું નથી. આ મહત્વનું છે: Anthropic ના 200K સામે માપેલો 300K GPT-5 ટર્ન ">100%, બ્લોન" વંચાય છે જ્યારે તે ખરેખર GPT-5 ના 400K નો 75% છે. એ જ માપદંડ ખરેખર ઓવરફ્લો થયેલા 130K DeepSeek ટર્નને 65% ના આરામદાયક આંકડા તરીકે છુપાવે છે.

દરેક વિન્ડો તેની ઉત્પત્તિ (provenance) સાથે આવે છે: `model_table`, `explicit_marker`, `observed_floor`, અથવા જ્યારે આપણને મોડેલ ખબર ન હોય ત્યારે એક પ્રામાણિક `default`. અંદાજ પર બનેલો ગેજ ક્યારેય લુકઅપ પર બનેલા ગેજ જેટલી અધિકૃતતાથી રેન્ડર થતો નથી.

ClawMetry ફક્ત કેટલાક રનટાઇમ્સ પર જ કોમ્પેક્શન ઇવેન્ટ્સ જોઈ શકે છે. તેથી `GET /api/context-coverage` દરેક રનટાઇમ પ્રમાણે જણાવે છે કે **શૂન્યનો અર્થ "ક્લીન ચાલ્યું" છે કે "આપણે અંધ છીએ"**. જે `0` ખરેખર અંધ હોવાનો અર્થ ધરાવે છે તે એમ કહી દે છે. [સંપૂર્ણ વિગત](docs/CONTEXT_BLOWOUT.md)

**ઇન્સ્ટ્રુમેન્ટેશનનો ખર્ચ કેટલો છે?**

| પાથ | તમારા એજન્ટમાં ઉમેરાયું | ડિફોલ્ટ? |
|---|---|---|
| સેશન-ફાઇલ ટેઇલિંગ (બધા 30 રનટાઇમ્સ) | **0**. અલગ પ્રોસેસ, તમારા એજન્ટમાં કોઈ ClawMetry કોડ નથી | on |
| HTTP ઇન્ટરસેપ્ટર (`CLAWMETRY_INTERCEPT=1`) | દરેક LLM કૉલ પર **+0.44 ms**, અથવા 5s ના કૉલના 0.009% | off |
| પ્રી-ટૂલ હૂક ગેટ (વોર્મ કેશ) | 36 ms ના ઇન્ટરપ્રિટર ફ્લોર ઉપર, દરેક ગેટેડ ટૂલ કૉલ પર **+44 ms** | off |
| એન્ફોર્સમેન્ટ પ્રોક્સી | દરેક LLM કૉલ પર **+9.7 ms** | off |

ડેમન હોસ્ટ ખર્ચ: **2,762 ઇવેન્ટ્સ/સેકન્ડ** ઇન્જેસ્ટ, ડિસ્ક પર **710 બાઇટ્સ/ઇવેન્ટ** (100k ઇવેન્ટ્સ દીઠ 67.7 MB), અને એક વ્યસ્ત ઇન્સ્ટોલ પર સતત **એક કોરના ~12%**. છેલ્લો આંકડો આપણા પોતાના જણાવેલા 5-10% ના બજેટ કરતાં વધારે છે, તેથી તેને પાનાં પરથી હટાવવાને બદલે પીછો કરવા યોગ્ય એક બગ તરીકે પ્રકાશિત કરવામાં આવ્યો છે.

Apple M2 Pro પર `benchmarks/overhead.py` વડે માપવામાં આવ્યું. હાર્નેસ દરેક કંડિશનને અલગ પ્રોસેસમાં ચલાવે છે, તેમનો ક્રમ બદલતું રહે છે, અને **જ્યારે રાઉન્ડ્સ તેની નિશાની (sign) પર સહમત ન થાય ત્યારે આંકડો છાપવાનો ઇનકાર કરે છે**. તેને તમારા પોતાના મશીન પર એક મિનિટમાં ચલાવો:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

હૂક ગેટ્સ અને એન્ફોર્સમેન્ટ પ્રોક્સી સહિત દરેક પાથ માપવામાં આવે છે, અને હાર્નેસ CI માં Linux, macOS અને Windows પર ચાલે છે. જાણવા યોગ્ય બે પરિણામો: પ્રોક્સીનો ખર્ચ Windows પર Linux કરતાં લગભગ સાત ગણો વધારે છે, અને ડેમન હાલમાં એક કોરના લગભગ 12% ટકાવી રાખે છે, જે આપણા પોતાના 5-10% બજેટ કરતાં વધારે છે. કાચો JSON, પદ્ધતિ, અને હજુ સુધી શું માપાયું નથી તે [docs/OVERHEAD.md](docs/OVERHEAD.md) માં છે.

## ભાવ નિર્ધારણ (Pricing)

| પ્લાન | તે શું આવરી લે છે | કિંમત |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, સંપૂર્ણ ડેશબોર્ડ, ફક્ત લોકલ | $0 |
| **Starter** | ઉપરોક્ત દરેક બીજું રનટાઇમ, ફ્લીટ વ્યુ, ક્લાઉડ સિંક | $9 પ્રતિ નોડ / મહિનો |
| **Pro** | Starter + કંટ્રોલ અને ઈવેલ્યુએશન: અપ્રૂવલ્સ, ટૂલ-રિસ્ક પોલિસીઝ, ઈવલ્સ, અસામાન્યતા શોધ, કોસ્ટ ઓપ્ટિમાઇઝર, OTel એક્સપોર્ટ, ટેમ્પર-એવિડન્ટ ઓડિટ લોગ | $19 પ્રતિ નોડ / મહિનો |

વાર્ષિક પ્લાન્સ, Enterprise અને વર્તમાન આંકડા **[clawmetry.com/pricing](https://clawmetry.com/pricing)** પર છે. સેલ્ફ-હોસ્ટેડ લાઇસન્સ કીઝ ક્લાઉડ વગર કામ કરે છે (`clawmetry license`). ચોક્કસ ફ્રી/પેઇડ વિભાજન [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) માં છે.

## તમારો ડેટા તમારા મશીન પર જ રહે છે

ClawMetry લોકલ સેશન ફાઇલો અને લોગ્સ વાંચે છે. **જ્યાં સુધી તમે `clawmetry connect` ન ચલાવો ત્યાં સુધી તમારા બોક્સમાંથી કોઈ સેશન ડેટા બહાર જતો નથી** — કોઈ પ્રોમ્પ્ટ્સ, જવાબો, ટૂલ આર્ગ્યુમેન્ટ્સ, ફાઇલ કન્ટેન્ટ કે લોગ લાઇન્સ નહીં. જ્યારે તમે ખરેખર કનેક્ટ કરો છો, ત્યારે સ્નેપશોટ એ કી વડે એન્ડ-ટુ-એન્ડ એન્ક્રિપ્ટેડ હોય છે જે તમારા મશીનમાંથી ક્યારેય બહાર જતી નથી, અને તમારા બ્રાઉઝરમાં ડિક્રિપ્ટ થાય છે. જો કોઈ નોડ પાસે કી ન હોય, તો અપલોડ સ્પષ્ટ રીતે મોકલવાને બદલે છોડી દેવામાં આવે છે, અને કોઈ સર્વર રિસ્પોન્સ તેને બંધ કરી શકતો નથી.

તમે કનેક્ટ કરો તે પહેલાં ડિફોલ્ટ રીતે બે વસ્તુઓ ચાલે છે, બંને ઓપ્ટ-આઉટ છે અને એકેય સેશન ડેટા વહન કરતી નથી: એક અનામી ઇન્સ્ટોલ પિંગ અને PyPI સામે વર્ઝન ચેક. ડિફોલ્ટ ઇન્સ્ટોલ સ્ટાર્ટઅપ બેનર લાઇન માટે એકવાર તમારો પબ્લિક IP પણ લુકઅપ કરે છે. દરેક ડેસ્ટિનેશન, તે શું વહન કરે છે અને તેને કેવી રીતે બંધ કરવું તે [docs/EGRESS.md](docs/EGRESS.md) માં સૂચિબદ્ધ છે; સેલ્ફ-હોસ્ટેડ, રિપોઈન્ટેડ અને એર-ગેપ્ડ ઇન્સ્ટોલ્સ કોઈ પણ મરજિયાત આઉટબાઉન્ડ કૉલ કરતા નથી.

ડિક્રિપ્શન તમારા બ્રાઉઝરમાં થાય છે, અમે તમને પૂરો પાડેલા કોડમાં. તે પહેલાં એક વચન હતું; હવે તે એવી વસ્તુ છે જે તમે ચકાસી શકો છો. તમારી કીને સ્પર્શતી દરેક લાઇન એક વાંચી શકાય તેવી ફાઇલમાં છે, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), જે વ્હીલની અંદર શિપ થાય છે અને Subresource Integrity હેશ સાથે પિન કરેલી, હૂબહૂ સર્વ કરવામાં આવે છે. બ્રાઉઝર અમે પ્રકાશિત કરેલું જ ચલાવે છે તેની ખાતરી કરવા માટે:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

આ જે સાબિત નથી કરતું: અમે એ પેજ સર્વ કરીએ છીએ જે ફાઇલ લોડ કરે છે, તેથી અમે અલગ પેજ સર્વ કરી શકીએ છીએ. ઇન્ટેગ્રિટી હેશ તમને ચેડાં થયેલા CDN થી બચાવે છે, વેન્ડરથી નહીં. તમને જે મળે છે તે એ છે કે કોઈ પણ અવેજી (substitution) ઈરાદાપૂર્વકની, પેજ સોર્સમાં દેખાય તેવી, અને PyPI પરના આર્ટિફેક્ટથી અલગ હોવી જ પડે જેને કોઈ પણ મેળવી શકે છે. સેલ્ફ-હોસ્ટિંગ કરવું અથવા લોકલ-ઓન્લી રહેવું આ નિર્ભરતાને સંપૂર્ણપણે દૂર કરે છે.

## ઇન્સ્ટોલ

```bash
pip install clawmetry     # પછી: clawmetry
```

અથવા વન-લાઈનર: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux કે Windows પર Python 3.8+ જોઈએ, અને એ જ મશીન પર ઓછામાં ઓછું એક એજન્ટ રનટાઇમ. Docker સૂચનાઓ: [docs/DOCKER.md](docs/DOCKER.md).

અથવા એજન્ટને તમારા માટે તે સેટ કરવા દો. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) સ્કિલ Claude Code, Codex, Cursor, Gemini CLI, Copilot અથવા OpenCode ને ClawMetry ઇન્સ્ટોલ કરવાનું, મશીન પરના એજન્ટ્સ શું કરી રહ્યા છે અને શું ખર્ચી રહ્યા છે તે જણાવવાનું, વિનંતી પર એક સેશન બંધ કરવાનું, અને મંજૂરી માટે જોખમી ટૂલ કૉલ્સને રોકી રાખવાનું શીખવે છે:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## દસ્તાવેજો (Docs)

| | |
|---|---|
| [રનટાઇમ સુસંગતતા](docs/compatibility.md) | દરેક એડેપ્ટર શું વાંચે છે, અને રનટાઇમ કેવી રીતે ઉમેરવું |
| [કોન્ટેક્સ્ટ બ્લોઆઉટ](docs/CONTEXT_BLOWOUT.md) | પ્રોવાઇડર-પ્રમાણેની વિન્ડોઝ, કોમ્પેક્શન વિરુદ્ધ ઓવરફ્લો, રનટાઇમ-પ્રમાણેનું કવરેજ |
| [ઓવરહેડ](docs/OVERHEAD.md) | ઇન્સ્ટ્રુમેન્ટેશનનો ખર્ચ કેટલો છે, માપેલો, તેને પુનઃઉત્પન્ન કરવા માટેના હાર્નેસ સાથે |
| [એન્ટાઇટલમેન્ટ્સ](docs/ENTITLEMENTS.md) | ફ્રી વિરુદ્ધ પેઇડ, ટિયર મેટ્રિક્સ, લાઇસન્સ CLI |
| [અપ્રૂવલ્સ અને પોલિસીઝ](docs/APPROVALS.md) | પ્રી-એક્ઝિક્યુશન ગેટિંગ, રિસ્ક સ્કોરિંગ, ફોન અપ્રૂવલ્સ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ટ્રેસ ગમે ત્યાં એક્સપોર્ટ કરો, ગમે ત્યાંથી OTLP ઈન્જેસ્ટ કરો |
| [તમારો પોતાનો એજન્ટ લાવો](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain સંપૂર્ણપણે, ચલાવી શકાય તેવા ઉદાહરણો સાથે |
| [SDK ટ્રેકિંગ](docs/SDK_TRACKING.md) | તમે જાતે બનાવેલા એજન્ટ્સ માટે ખર્ચનું એટ્રિબ્યુશન |
| [ચેટ ચેનલ્સ](docs/CHANNELS.md) | Flow માં દેખાડેલા ચેટ એડેપ્ટર્સ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | સેન્ડબોક્સ કરેલા NVIDIA NemoClaw સેટઅપ્સ |
| [Docker](docs/DOCKER.md) | ઇમેજ, કમ્પોઝ, વોલ્યુમ માઉન્ટ્સ |
| [આર્કિટેક્ચર](ARCHITECTURE.md) · [ડેવલપમેન્ટ](docs/DEVELOPMENT.md) | અંદરથી તે કેવી રીતે કામ કરે છે; સોર્સમાંથી ચલાવવું |
| [ટેલિમેટ્રી](docs/TELEMETRY.md) | અનામી ઇન્સ્ટોલ અને ડેસ્કટોપ-ઓપન પિંગ્સ, અને તેમને કેવી રીતે બંધ કરવા |

## સ્ક્રીનશોટ્સ

નીચેનો દરેક આંકડો એક વાસ્તવિક મશીન પરથી, ફક્ત-વાંચવા (read-only) માટે, કંઈ પણ સીડ કર્યા વગર છે.

**તે તમને જણાવે છે કે ક્યારે કંઈક ખોટું છે, ફક્ત શું થયું તે નહીં.**
ટોચ પર બે અસામાન્યતા બેનર્સ: દૈનિક સરેરાશના 7 ગણા ખર્ચ, અને 4.2 ગણો કોસ્ટ સ્પાઇક. તેમની નીચે, તાજેતરના 667 સેશન્સમાંથી 324 વેસ્ટ સિગ્નલ ધરાવે છે, કારણ પ્રમાણે વિભાજિત.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**તે તમને દરેક વિન્ડોમાં પૈસા ક્યાં ગયા તે દેખાડે છે.**
આજે $252.47, આ અઠવાડિયે $513.15, આ મહિને $1,312.92, દરેકની પાછળના ટોકન્સ સાથે અને તમારું સબસ્ક્રિપ્શન તેમાંથી કેટલું પહેલેથી કવર કરે છે તે સાથે. તેની નીચે, લગભગ $1,128/મહિનો પુનઃપ્રાપ્ય તરીકે વિભાજિત અને કેશ પુનઃઉપયોગ દ્વારા પહેલેથી બચાવેલા $17,256/મહિનો.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**તે દોરી બતાવે છે કે એક સંદેશો કેવી રીતે જવાબ બને છે.**
લાઇવ ફ્લો ડાયાગ્રામ: તમે, જે ચેનલ પર તે આવ્યો તે, ગેટવે, અત્યારે જવાબ આપી રહેલો મોડેલ, અને દરેક ટૂલ જેને તેણે પકડ્યું. જેમ જેમ કામ તેમની મારફતે ખસે છે તેમ નોડ્સ ઝગમગે છે.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**મશીન પરના દરેક એજન્ટ, એક જ ટેબલમાં.**
તે શું ચલાવે છે, છેલ્લા 24 કલાકમાં અને તેના જીવનકાળ દરમિયાન તેનો ખર્ચ કેટલો છે, તેને છેલ્લે ક્યારે જોવામાં આવ્યો, તેનો માલિક કોણ છે, અને શું સબસ્ક્રિપ્શન બિલ કવર કરી રહ્યું છે. અહીં 14 એજન્ટ્સ, 3 સેશન કામ કરી રહ્યા છે, 13 શાંત.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**તે દેખાડે છે કે એક ટર્નનો સમય અને પૈસા ક્યાં ગયા, ટૂલ પ્રમાણે.**
એક વાસ્તવિક સેશનનો એક ટર્ન: $1.16 માટે 11.2 મિનિટમાં 11 ટૂલ્સ. દરેક Bash કૉલ અને મોડેલ કૉલને ટાઇમલાઇન પર પોતાનો બાર મળે છે, જેથી 4.1 મિનિટ ચાલેલા કમાન્ડ અને 226ms ચાલેલા કમાન્ડને એક નજરમાં અલગ પાડી શકાય.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**તે ફક્ત ખર્ચ જ નહીં, કામનું ગ્રેડિંગ કરે છે.**
આ અઠવાડિયે એક A: 54 કાર્યો સ્વચ્છ પાછા આવ્યા, 2 ખરબચડા (rough) કાર્યોનો ખર્ચ $48.57 થયો, અને જજ કરવા માટે ખૂબ ઓછી પ્રવૃત્તિ ધરાવતા રન વિજય તરીકે ગણવાને બદલે ગ્રેડમાંથી બાકાત રાખવામાં આવ્યા. દરેક ખરબચડો રન તેના ટ્રેસ સાથે લિંક કરે છે.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**તે દેખાડે છે કે કોન્ટેક્સ્ટ વિન્ડો કેમ ભરાતી રહે છે.**
છેલ્લા ટર્ન પર 1M-ટોકન વિન્ડોમાંથી 715K, 83.3% ની ટોચ, 4 કોમ્પેક્શન્સ જે બધા ઓવરફ્લો પર નહીં પણ પ્રો-એક્ટિવલી ફાયર થયા, અને તેની પાછળના દરેક ટર્નનું યુટિલાઇઝેશન.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**તમે કંઈ પણ કન્ફિગર કર્યા વગર ડિટેક્શન ચાલે છે.**
બિલ્ટ-ઇન ડિટેક્ટર્સ ઇન્સ્ટોલથી જ ચાલુ છે: એજન્ટ શાંત થઈ ગયો, ટેલિમેટ્રી ફીડ બંધ થઈ ગયો, કોસ્ટ સ્પાઇક, ટોકન બર્સ્ટ, એરર્સ વધી રહ્યા છે, એરર સ્પાઇક, બજેટ થ્રેશોલ્ડ, થ્રેટ સિગ્નેચર મેચ થયું, સિક્યુરિટી ટૂલ ફાઇન્ડિંગ, સિક્યુરિટી પોસ્ચર બદલાયું. તેની ઉપર તમારા પોતાના નિયમો વૈકલ્પિક છે.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**જોખમી કૉલને રોકી રાખવું ઓપ્ટ-ઇન છે, અને બંધ સ્થિતિમાં શિપ થાય છે.**
રિકર્સિવ ડિલિટ્સ, ફોર્સ પુશ્સ, sudo, સિક્રેટ્સ, પેકેજ ઇન્સ્ટોલ્સ અને આઉટબાઉન્ડ કૉલ્સ દરેકને એક નિયમ મળે છે જેને તમે ચાલુ કરી શકો છો. જ્યાં સુધી તમે તેમ ન કરો ત્યાં સુધી, ClawMetry જુએ છે અને કંઈ પણ બદલતું નથી. એકવાર એક ચાલુ થાય, પછી મેચ થતા કૉલ્સ મંજૂરી કે નામંજૂરી માટે અહીં (અથવા તમારા ફોન પર) રાહ જુએ છે.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

વધુ, રનટાઇમ પ્રમાણે: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## સ્ટાર ઇતિહાસ

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
