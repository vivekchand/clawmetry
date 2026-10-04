<!-- i18n-src:c99ac0512cae -->
> తెలుగు translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ఒక ఏజెంట్ ఎలాంటి పురోగతి సాధించకుండానే వందకొద్దీ టూల్ కాల్స్ చేయగలదు.** ClawMetry
మీ కోడింగ్ ఏజెంట్లు ఇప్పటికే రాసిన సెషన్ ఫైళ్లను చదివి, టైమ్‌లైన్,
టూల్ కాల్స్, మరియు runtime బహిర్గతం చేసే టోకెన్ మరియు ఖర్చు డేటాను అన్నిటినీ ఒకే
వీక్షణలో పెడుతుంది — అంటే పనిచేస్తున్న ఒక దీర్ఘ రన్‌ను, ఎక్కడో ఆగిపోయిన దానితో పోల్చి చూడగలరు.

**33 AI ఏజెంట్ runtime‌లతో** పనిచేస్తుంది — Claude Code, OpenAI Codex, Hermes, OpenClaw & మరో 29. మీ మొత్తం ఏజెంట్ ఫ్లీట్ కోసం ఒకే డాష్‌బోర్డ్. ([పూర్తి జాబితా](SUPPORTED_RUNTIMES.txt), కేటలాగ్ నుండి జనరేట్ చేయబడింది.)

> 🌐 **దీన్ని చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒకే కమాండ్. జీరో కాన్ఫిగ్. అన్నింటినీ ఆటోమేటిక్‌గా గుర్తిస్తుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది. జీరో కాన్ఫిగ్: మీ దగ్గర ఇప్పటికే ఉన్న ఏజెంట్
runtime‌లను అది కనుగొంటుంది, వాటిని read-only గా చదువుతుంది, మరియు అవి ఎలా పనిచేస్తున్నాయో అందులో ఏమీ మార్చదు.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ఇన్‌స్టాల్ చేసే ముందు

| | |
|---|---|
| **ఇది ఏమి చేస్తుంది** | మీ ఏజెంట్లు ఇప్పటికే రాసిన సెషన్ ఫైళ్లు మరియు లాగ్‌లను చదువుతుంది. SDK లేదు, కోడ్ మార్పు లేదు, మీ యాప్‌లో ఇన్‌స్ట్రుమెంటేషన్ లేదు. |
| **మీరు చూసేది** | సెషన్ టైమ్‌లైన్, టూల్-బై-టూల్ రీప్లే, టోకెన్ మరియు ఖర్చు విభజన, మరియు ట్రాజెక్టరీ సిగ్నల్స్ (లూపింగ్, పునరావృత వైఫల్యాలు) — ప్రతి runtime కు వేరువేరుగా. |
| **ఫ్రీ ఏమిటి** | `pip install clawmetry` ఎటువంటి ఖాతా, కీ లేదా నెట్‌వర్క్ కాల్ లేకుండా **OpenClaw, NVIDIA NemoClaw, Goose మరియు Qwen Code** లను చదువుతుంది. మిగతా 28 — Claude Code, Codex, Cursor మరియు ఇతరులు — క్లోజ్డ్-సోర్స్ `clawmetry-pro` కంపానియన్ ద్వారా చదవబడతాయి, ఇది 7-రోజుల ట్రయల్ లేదా ప్లాన్‌తో అందుతుంది — ఖచ్చితమైన విభజన కోసం [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) చూడండి. |
| **ఎలా మొదలుపెట్టాలి** | `pip install clawmetry && clawmetry`, తర్వాత localhost:8900 తెరవండి. ఈ మెషీన్‌లో ఇంకా ఏజెంట్లు లేవా? `clawmetry --sample` మూడు లేబుల్ చేయబడిన సింథటిక్ సెషన్లతో తెరుచుకుంటుంది. |
| **మీ మెషీన్ నుండి ఏమి బయటకు వెళ్తుంది** | మీరు `clawmetry connect` రన్ చేయనంత వరకు ఎటువంటి సెషన్ డేటా బయటకు వెళ్లదు. డిఫాల్ట్‌గా రెండు విషయాలు మాత్రమే జరుగుతాయి, రెండూ opt-out చేయగలిగినవి మరియు సెషన్ కంటెంట్ ఏదీ మోసుకెళ్లనివి: ఒక అనామక ఇన్‌స్టాల్ పింగ్ మరియు PyPI వెర్షన్ చెక్. ప్రతి గమ్యస్థానం [docs/EGRESS.md](docs/EGRESS.md) లో జాబితా చేయబడింది, ఇది కామెంట్లను చదవడం కంటే వైర్ క్యాప్చర్ నుండి తిరిగి నిర్మించబడింది. |

ఫలితాలను అంచనా వేయడానికి ముందు తెలుసుకోవలసిన రెండు పరిమితులు: runtime‌లు చాలా
వేరువేరు డేటాను బహిర్గతం చేస్తాయి (కొన్ని ఎటువంటి ఖర్చును ప్రచురించవు — [మ్యాట్రిక్స్](docs/compatibility.md)
ప్రతి runtime కు ఏది వర్తిస్తుందో చెబుతుంది), మరియు ఒక చర్యను గమనించడం అంటే దాన్ని
ఆపగలగడం కాదు ([ప్రతి runtime కు ఏ కంట్రోల్స్ నిజమైనవి](docs/APPROVALS.md)).


## 33 ఏజెంట్ runtime‌లతో పనిచేస్తుంది

**ఓపెన్ సోర్స్ యాప్‌లో ఫ్రీ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**పెయిడ్ ప్లాన్‌లో:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ప్రతి runtime కు ఒకే డాష్‌బోర్డ్ లభిస్తుంది. ఒకేసారి అనేకం రన్ చేయండి, మరియు హెడర్
స్విచ్చర్ ప్రతి ట్యాబ్‌ను వాటిలో ఒకదానికి రీ-స్కోప్ చేస్తుంది.

మీరు SDK పై మీ స్వంత ఏజెంట్‌ను నిర్మించారా? ఇంటర్‌సెప్టర్ దాని LLM కాల్స్‌ను కూడా
ట్రాక్ చేస్తుంది. చూడండి [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## మీకు ఏమి లభిస్తుంది

- **సెషన్లు & ట్రాన్స్‌క్రిప్ట్‌లు**: ప్రతి ఏజెంట్ ఏమి చేసింది, టర్న్ బై టర్న్, రీప్లేతో సహా
- **ఖర్చు & టోకెన్లు**: runtime, మోడల్, సెషన్ మరియు రోజు ప్రకారం, అనామలీ ఫ్లాగ్‌లతో
- **ఫ్లో**: ఛానెల్స్, మోడల్స్ మరియు టూల్స్ ద్వారా కదులుతున్న మెసేజ్‌ల లైవ్ డయాగ్రామ్
- **బ్రెయిన్**: అది జరుగుతున్నప్పుడే రీజనింగ్ మరియు టూల్-కాల్ ఈవెంట్ స్ట్రీమ్
- **కాంటెక్స్ట్ బ్లోఅవుట్**: ప్రతి ప్రొవైడర్‌కు తగినట్లుగా విండో వినియోగం, compaction vs forced overflow, మరియు మనం *చూడలేనిది* ఏమిటో runtime-వారీ మ్యాప్ ([ఎలా](docs/CONTEXT_BLOWOUT.md))
- **మెమొరీ & స్కిల్స్**: ప్రతి runtime నిజంగా లోడ్ చేసిన ఫైళ్లు మరియు స్కిల్స్
- **ఆరోగ్యం & లాగ్‌లు**: డిస్క్, మెమొరీ, ఎర్రర్ రేట్లు, రేట్ లిమిట్స్, లైవ్ లాగ్ స్ట్రీమ్
- **అలర్ట్‌లు**: బడ్జెట్ కాప్స్, ఎర్రర్ స్పైక్‌లు, agent-offline, Slack, Discord, PagerDuty, Telegram, Email కు రూట్ చేయబడినవి
- **అప్రూవల్స్**: రిస్కీ టూల్ కాల్స్‌ను అవి *రన్ అయ్యేముందు* పాజ్ చేసి మీ ఫోన్ నుండి ఆమోదించండి ([ఎలా](docs/APPROVALS.md))

## కాంటెక్స్ట్ బ్లోఅవుట్, మరియు పర్యవేక్షణ ఖర్చు ఎంత

ఏదైనా ఏజెంట్-పోలిక టూల్‌ను నమ్మే ముందు సమాధానం చెప్పదగిన రెండు ప్రశ్నలు.

**runtime‌ల మధ్య కాంటెక్స్ట్-విండో బ్లోఅవుట్‌ను ఇది ఎలా హ్యాండిల్ చేస్తుంది?**

ఒక యుటిలైజేషన్ శాతం అది ఏ సంఖ్యతో భాగిస్తుందో అంతే నిజాయితీగా ఉంటుంది. ClawMetry
విండోను Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama
మరియు GLM కవర్ చేసే, మీరు చదవగలిగే మరియు PR చేయగలిగే [ఒక టేబుల్](clawmetry/context_windows.py)
నుండి ప్రతి ప్రొవైడర్‌కు తగినట్లుగా సైజ్ చేస్తుంది. ఇది అన్ని 33 runtime‌లను ఒక
వెండర్ స్కేల్‌తో కొలవదు. అది ముఖ్యమైనది: Anthropic యొక్క 200K తో పోల్చి స్కోర్ చేసిన
300K GPT-5 టర్న్ ">100%, blown" అని చూపిస్తుంది, నిజానికి ఇది GPT-5 యొక్క 400K లో 75%
మాత్రమే. అదే స్కేల్ నిజంగా overflow అయిన 130K DeepSeek టర్న్‌ను సౌకర్యవంతమైన 65%గా
దాచిపెడుతుంది.

ప్రతి విండో తన మూలాధారంతో వస్తుంది: `model_table`, `explicit_marker`,
`observed_floor`, లేదా మనకు మోడల్ తెలియనప్పుడు నిజాయితీగా `default`. ఒక గెస్‌పై
నిర్మించిన గేజ్ ఎప్పుడూ ఒక lookup పై నిర్మించిన దానంత అధికారంతో రెండర్ అవదు.

ClawMetry కొన్ని runtime‌లలో compaction ఈవెంట్లను మాత్రమే చూడగలదు. కాబట్టి
`GET /api/context-coverage` ప్రతి runtime కోసం, ఒక zero అంటే **"క్లీన్‌గా రన్ అయింది"
లేదా "మనకు కనిపించడం లేదు"** అని రిపోర్ట్ చేస్తుంది. నిజంగా blind అని అర్థం వచ్చే `0` అది
అలా అని చెబుతుంది. [పూర్తి వివరాలు](docs/CONTEXT_BLOWOUT.md)

**ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఎంత?**

| పాత్ | మీ ఏజెంట్‌కు జోడించింది | డిఫాల్ట్? |
|---|---|---|
| సెషన్-ఫైల్ టెయిలింగ్ (అన్ని 33 runtime‌లు) | **0**. వేరే ప్రాసెస్, మీ ఏజెంట్‌లో ClawMetry కోడ్ ఉండదు | on |
| HTTP ఇంటర్‌సెప్టర్ (`CLAWMETRY_INTERCEPT=1`) | ప్రతి LLM కాల్‌కు **+0.44 ms**, లేదా 5s కాల్‌లో 0.009% | off |
| ప్రీ-టూల్ హుక్ గేట్ (వార్మ్ క్యాష్) | 36 ms ఇంటర్‌ప్రెటర్ ఫ్లోర్ పై, గేటెడ్ టూల్ కాల్‌కు **+44 ms** | off |
| ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీ | ప్రతి LLM కాల్‌కు **+9.7 ms** | off |

డేమన్ హోస్ట్ ఖర్చు: ingest కు **2,762 events/sec**, డిస్క్‌పై **710 bytes/event**
(100k ఈవెంట్లకు 67.7 MB), మరియు busy ఇన్‌స్టాల్‌పై నిలకడగా **ఒక కోర్‌లో ~12%**.
ఆ చివరి సంఖ్య మన స్వంత 5-10% బడ్జెట్ కంటే ఎక్కువ, కాబట్టి ఇది పేజీ నుండి తొలగించకుండా
వెంటాడవలసిన బగ్‌గా ప్రచురించబడింది.

Apple M2 Pro పై `benchmarks/overhead.py` తో కొలవబడింది. ఈ harness ప్రతి
కండిషన్‌ను వేరే ప్రాసెస్‌లో రన్ చేస్తుంది, వాటి క్రమాన్ని మారుస్తుంది, మరియు రౌండ్లు దాని
సైన్‌పై ఏకీభవించకపోతే **ఒక సంఖ్యను ప్రింట్ చేయడానికి నిరాకరిస్తుంది**. దీన్ని మీ స్వంత
మెషీన్‌పై ఒక నిమిషంలో రన్ చేయండి:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

హుక్ గేట్లు మరియు ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీతో సహా ప్రతి పాత్ కొలవబడింది, మరియు ఈ
harness CI లో Linux, macOS మరియు Windows పై రన్ అవుతుంది. తెలుసుకోవలసిన రెండు
ఫలితాలు: Windows పై ప్రాక్సీ Linux కంటే దాదాపు ఏడు రెట్లు ఎక్కువ ఖర్చు అవుతుంది, మరియు
డేమన్ ఇప్పుడు ఒక కోర్‌లో దాదాపు 12% నిలకడగా వాడుతుంది, ఇది మన స్వంత 5-10% బడ్జెట్
కంటే ఎక్కువ. రా JSON, పద్ధతి, మరియు ఇంకా కొలవని దాని వివరాలు
[docs/OVERHEAD.md](docs/OVERHEAD.md) లో ఉన్నాయి.

## ప్రైసింగ్

| ప్లాన్ | ఇది ఏమి కవర్ చేస్తుంది | ధర |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, పూర్తి డాష్‌బోర్డ్, లోకల్ మాత్రమే | $0 |
| **Starter** | పై మిగిలిన ప్రతి runtime, fleet వీక్షణ, cloud sync | నోడ్‌కు $9 / నెల |
| **Pro** | Starter + కంట్రోల్ మరియు ఎవాల్యుయేషన్: అప్రూవల్స్, టూల్-రిస్క్ పాలసీలు, evals, అనామలీ డిటెక్షన్, కాస్ట్ ఆప్టిమైజర్, OTel ఎక్స్‌పోర్ట్, tamper-evident audit log | నోడ్‌కు $19 / నెల |

వార్షిక ప్లాన్‌లు, Enterprise మరియు ప్రస్తుత సంఖ్యలు
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** లో ఉన్నాయి. సెల్ఫ్-హోస్టెడ్
లైసెన్స్ కీలు cloud లేకుండా పనిచేస్తాయి (`clawmetry license`). ఖచ్చితమైన free/paid
విభజన [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) లో ఉంది.

## మీ డేటా మీ మెషీన్‌లోనే ఉంటుంది

ClawMetry లోకల్ సెషన్ ఫైళ్లు మరియు లాగ్‌లను చదువుతుంది. **మీరు `clawmetry connect`
రన్ చేయనంత వరకు ఎటువంటి సెషన్ డేటా మీ బాక్స్ నుండి బయటకు వెళ్లదు** — ఎటువంటి ప్రాంప్ట్‌లు,
ప్రతిస్పందనలు, టూల్ ఆర్గ్యుమెంట్‌లు, ఫైల్ కంటెంట్‌లు లేదా లాగ్ లైన్‌లు కాదు. మీరు కనెక్ట్
చేసినప్పుడు, ఆ స్నాప్‌షాట్ మీ మెషీన్ నుండి ఎప్పుడూ బయటకు వెళ్లని కీతో end-to-end
encrypted అయి ఉంటుంది, మరియు మీ బ్రౌజర్‌లో డీక్రిప్ట్ చేయబడుతుంది. ఒక నోడ్‌కు కీ లేకపోతే,
ఆ అప్‌లోడ్ స్కిప్ చేయబడుతుంది, క్లియర్‌లో పంపబడదు, మరియు ఎటువంటి సర్వర్ రెస్పాన్స్ దాన్ని
ఆఫ్ చేయలేదు.

మీరు కనెక్ట్ చేయడానికి ముందు డిఫాల్ట్‌గా రెండు విషయాలు జరుగుతాయి, రెండూ opt-out
చేయగలిగినవి మరియు సెషన్ డేటా మోసుకెళ్లనివి: ఒక అనామక ఇన్‌స్టాల్ పింగ్ మరియు PyPI కు
వ్యతిరేకంగా ఒక వెర్షన్ చెక్. డిఫాల్ట్ ఇన్‌స్టాల్ ఒక startup banner లైన్ కోసం మీ పబ్లిక్
IP ని కూడా ఒకసారి చూస్తుంది. ప్రతి గమ్యస్థానం, అది ఏమి మోసుకెళుతుంది మరియు దాన్ని ఎలా
ఆఫ్ చేయాలో [docs/EGRESS.md](docs/EGRESS.md) లో జాబితా చేయబడింది; సెల్ఫ్-హోస్టెడ్,
repointed మరియు air-gapped ఇన్‌స్టాల్‌లు ఎటువంటి discretionary outbound కాల్స్ చేయవు.

డీక్రిప్షన్ మీ బ్రౌజర్‌లో జరుగుతుంది, మేము మీకు అందించే కోడ్‌లో. ఇది ఒకప్పుడు ఒక వాగ్దానం
మాత్రమే; ఇప్పుడు మీరు చెక్ చేయగలిగే విషయం. మీ కీని తాకే ప్రతి లైన్ ఒక చదవగలిగే ఫైల్‌లో ఉంది,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ఇది wheel లోపల
షిప్ అవుతుంది మరియు Subresource Integrity హాష్‌తో పిన్ చేయబడి, ఖచ్చితంగా అదే రూపంలో
సర్వ్ చేయబడుతుంది. బ్రౌజర్ మేము ప్రచురించిన దాన్నే రన్ చేస్తుందని నిర్ధారించుకోవడానికి:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ఇది నిరూపించనిది: ఆ ఫైల్‌ను లోడ్ చేసే పేజీని మేమే సర్వ్ చేస్తాము, కాబట్టి మేము వేరే
పేజీని సర్వ్ చేయగలము. Integrity హాష్‌లు compromised CDN నుండి మిమ్మల్ని రక్షిస్తాయి,
వెండర్ నుండి కాదు. మీకు లభించేది ఏమిటంటే, ఏదైనా substitution ఉద్దేశపూర్వకంగా,
పేజీ సోర్స్‌లో కనిపించేలా, మరియు ఎవరైనా fetch చేయగలిగే PyPI ఆర్టిఫాక్ట్ నుండి
వేరుగా ఉండాలి. సెల్ఫ్-హోస్టింగ్ లేదా లోకల్-మాత్రమే ఉండటం ఈ డిపెండెన్సీని పూర్తిగా
తొలగిస్తుంది.

## ఇన్‌స్టాల్

```bash
pip install clawmetry     # then: clawmetry
```

లేదా ఒన్-లైనర్: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux లేదా Windows పై Python 3.8+ అవసరం, మరియు అదే మెషీన్‌పై కనీసం ఒక
ఏజెంట్ runtime అవసరం. Docker సూచనలు: [docs/DOCKER.md](docs/DOCKER.md).

లేదా ఏజెంట్‌నే దాన్ని మీ కోసం సెటప్ చేయనివ్వండి. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
స్కిల్ Claude Code, Codex, Cursor, Gemini CLI, Copilot లేదా OpenCode కు
ClawMetry ఇన్‌స్టాల్ చేయడం, మెషీన్‌పై ఏజెంట్లు ఏమి చేస్తున్నాయో మరియు ఎంత ఖర్చు
చేస్తున్నాయో రిపోర్ట్ చేయడం, అభ్యర్థనపై ఒక సెషన్‌ను ఆపడం, మరియు రిస్కీ టూల్ కాల్స్‌ను
ఆమోదం కోసం పట్టుకోవడం నేర్పిస్తుంది:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## డాక్స్

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ప్రతి అడాప్టర్ ఏమి చదువుతుంది, మరియు ఒక runtime ను ఎలా జోడించాలి |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | ప్రొవైడర్-వారీ విండోలు, compaction vs overflow, runtime-వారీ కవరేజ్ |
| [Overhead](docs/OVERHEAD.md) | ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఎంత, కొలవబడింది, దాన్ని రిప్రొడ్యూస్ చేసే harness తో |
| [Entitlements](docs/ENTITLEMENTS.md) | Free vs paid, tier మ్యాట్రిక్స్, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution గేటింగ్, రిస్క్ స్కోరింగ్, ఫోన్ అప్రూవల్స్ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ఎక్కడైనా traces ఎక్స్‌పోర్ట్ చేయండి, ఎక్కడి నుండైనా OTLP ingest చేయండి |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ఎండ్ టు ఎండ్, రన్ చేయగలిగే ఉదాహరణలతో |
| [SDK tracking](docs/SDK_TRACKING.md) | మీరు స్వయంగా నిర్మించిన ఏజెంట్లకు కాస్ట్ అట్రిబ్యూషన్ |
| [Chat channels](docs/CHANNELS.md) | Flow లో చూపబడే చాట్ అడాప్టర్లు |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw సెటప్‌లు |
| [Docker](docs/DOCKER.md) | ఇమేజ్, compose, వాల్యూమ్ మౌంట్‌లు |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ఇది లోపల ఎలా పనిచేస్తుంది; సోర్స్ నుండి రన్ చేయడం |
| [Telemetry](docs/TELEMETRY.md) | అనామక ఇన్‌స్టాల్ మరియు desktop-open పింగ్‌లు, మరియు వాటిని ఎలా ఆఫ్ చేయాలి |

## స్క్రీన్‌షాట్‌లు

దిగువ ప్రతి సంఖ్య ఒక రియల్ మెషీన్ నుండి, read-only గా, ఏమీ seed చేయకుండా తీసుకోబడింది.

**ఏదైనా తప్పు జరిగినప్పుడు ఇది మీకు చెబుతుంది, కేవలం ఏమి జరిగిందో మాత్రమే కాదు.**
పైన రెండు అనామలీ బ్యానర్‌లు: రోజువారీ సగటు కంటే 7x ఖర్చు, మరియు 4.2x కాస్ట్ స్పైక్.
వాటి కింద, waste సిగ్నల్ మోసుకున్న 667 తాజా సెషన్లలో 324, కారణాల వారీగా జాబితా
చేయబడింది.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**డబ్బు ఎక్కడికి వెళ్లిందో ఇది మీకు ప్రతి విండోలో చూపిస్తుంది.**
ఈరోజు $252.47, ఈ వారం $513.15, ఈ నెల $1,312.92, వీటి వెనుక ఉన్న టోకెన్‌లతో
మరియు మీ సబ్‌స్క్రిప్షన్ ఎంత కవర్ చేస్తుందో దానితో. దాని కింద, దాదాపు $1,128/నెల
recoverable గా జాబితా చేయబడింది మరియు cache reuse ద్వారా ఇప్పటికే $17,256/నెల
ఆదా చేయబడింది.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ఒక మెసేజ్ ఎలా ఒక సమాధానంగా మారుతుందో ఇది చిత్రీకరిస్తుంది.**
లైవ్ ఫ్లో డయాగ్రామ్: మీరు, అది వచ్చిన ఛానెల్, గేట్‌వే, ఇప్పుడు సమాధానం చెబుతున్న
మోడల్, మరియు అది ఉపయోగించిన ప్రతి టూల్. పని వాటి ద్వారా కదులుతున్నప్పుడు నోడ్‌లు
వెలుగుతాయి.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**మెషీన్‌పై ఉన్న ప్రతి ఏజెంట్, ఒకే టేబుల్‌లో.**
అది ఏమి రన్ చేస్తుంది, గత 24 గంటల్లో మరియు దాని జీవితకాలంలో ఎంత ఖర్చు అవుతుంది,
చివరిసారి ఎప్పుడు కనిపించింది, దాన్ని ఎవరు ఓన్ చేస్తారు, మరియు ఒక సబ్‌స్క్రిప్షన్ ఆ
బిల్‌ను కవర్ చేస్తుందా. ఇక్కడ 14 ఏజెంట్లు, 3 సెషన్లు పనిచేస్తున్నాయి, 13 నిశ్శబ్దంగా ఉన్నాయి.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ఒక టర్న్ యొక్క సమయం మరియు డబ్బు ఎక్కడికి వెళ్లిందో, టూల్ బై టూల్, ఇది చూపిస్తుంది.**
ఒక రియల్ సెషన్ యొక్క ఒక టర్న్: $1.16 కు 11.2 నిమిషాల్లో 11 టూల్స్. ప్రతి Bash
కాల్ మరియు మోడల్ కాల్‌కు టైమ్‌లైన్‌పై దాని స్వంత బార్ ఉంటుంది, కాబట్టి 4.1 నిమిషాలు
రన్ అయిన కమాండ్ మరియు 226ms రన్ అయినది ఒక చూపులోనే వేరుగా తెలుస్తాయి.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ఇది కేవలం ఖర్చును మాత్రమే కాదు, పనిని కూడా గ్రేడ్ చేస్తుంది.**
ఈ వారం ఒక A: 54 టాస్క్‌లు క్లీన్‌గా పూర్తయ్యాయి, 2 కష్టమైనవి $48.57 ఖర్చు అయ్యాయి,
మరియు గ్రేడ్ చేయడానికి చాలా తక్కువ యాక్టివిటీ ఉన్న రన్‌లను గెలుపులుగా లెక్కించకుండా
గ్రేడ్ నుండి తీసివేయబడింది. ప్రతి కష్టమైన రన్ దాని ట్రేస్‌కు లింక్ అవుతుంది.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**కాంటెక్స్ట్ విండో ఎందుకు నిండిపోతూ ఉంటుందో ఇది చూపిస్తుంది.**
చివరి టర్న్‌లో 1M-టోకెన్ విండోలో 715K, 83.3% పీక్, overflow పై కాకుండా
proactive గా ఫైర్ అయిన 4 compactions, మరియు వాటి వెనుక ఉన్న ప్రతి టర్న్ యొక్క
utilisation.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**మీరు ఏమీ కాన్ఫిగర్ చేయకుండానే డిటెక్షన్ రన్ అవుతుంది.**
ఇన్‌స్టాల్ నుండే బిల్ట్-ఇన్ డిటెక్టర్లు ఆన్‌లో ఉంటాయి: ఏజెంట్ నిశ్శబ్దమైంది, టెలిమెట్రీ
ఫీడ్ ఆగిపోయింది, కాస్ట్ స్పైక్, టోకెన్ బర్స్ట్, ఎర్రర్లు పెరుగుతున్నాయి, ఎర్రర్ స్పైక్,
బడ్జెట్ థ్రెషోల్డ్, threat signature మ్యాచ్ అయింది, సెక్యూరిటీ టూల్ ఫైండింగ్, సెక్యూరిటీ
పోస్చర్ మారింది. దానిపై మీ స్వంత రూల్స్ ఆప్షనల్.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**రిస్కీ కాల్‌ను పట్టుకోవడం opt-in, మరియు ఆఫ్‌గా షిప్ అవుతుంది.**
Recursive deletes, force pushes, sudo, సీక్రెట్‌లు, పాకేజ్ ఇన్‌స్టాల్‌లు మరియు
outbound కాల్‌లకు ప్రతిదానికీ మీరు ఆన్ చేయగలిగే రూల్ ఉంటుంది. మీరు చేసేంత వరకు,
ClawMetry చూస్తుంది, ఏమీ మార్చదు. ఒకటి ఆన్ అయ్యాక, మ్యాచ్ అయ్యే కాల్స్ ఇక్కడ (లేదా
మీ ఫోన్‌పై) ఆమోదం లేదా తిరస్కరణ కోసం వేచి ఉంటాయి.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

మరిన్ని, runtime వారీగా: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## గుర్తింపు

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## లైసెన్స్

MIT · [@vivekchand](https://github.com/vivekchand) చే నిర్మించబడింది · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
