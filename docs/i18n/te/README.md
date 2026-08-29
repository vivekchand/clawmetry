<!-- i18n-src:d21bea5161e0 -->
> తెలుగు translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**మీ ఏజెంట్ ఆలోచించడాన్ని చూడండి.** **30 AI ఏజెంట్ రన్‌టైమ్‌ల** కోసం రియల్-టైమ్ అబ్జర్వబిలిటీ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & మరో 26. మీ మొత్తం ఏజెంట్ ఫ్లీట్ కోసం ఒకే డాష్‌బోర్డ్.

> 🌐 **దీన్ని ఈ భాషల్లో చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒక్క కమాండ్. జీరో కాన్ఫిగ్. ప్రతిదాన్ని ఆటో-డిటెక్ట్ చేస్తుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది. జీరో కాన్ఫిగ్: మీ దగ్గర ఇప్పటికే ఉన్న ఏజెంట్ రన్‌టైమ్‌లను ఇది కనుగొంటుంది, వాటిని read-only గా చదువుతుంది, మరియు అవి ఎలా నడుస్తాయో దాన్ని ఎలాంటి మార్పు చేయదు.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ఏజెంట్ రన్‌టైమ్‌లతో పనిచేస్తుంది

**ఓపెన్ సోర్స్ యాప్‌లో ఉచితం:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**చెల్లింపు ప్లాన్‌లో:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ప్రతి రన్‌టైమ్‌కు ఒకే డాష్‌బోర్డ్ లభిస్తుంది. ఒకేసారి అనేకం రన్ చేయండి, హెడర్ స్విచర్ ప్రతి ట్యాబ్‌ను వాటిలో ఒకదానికి రీ-స్కోప్ చేస్తుంది.

SDK పై మీ స్వంత ఏజెంట్‌ను నిర్మించారా? ఇంటర్‌సెప్టర్ దాని LLM కాల్స్‌ను కూడా ట్రాక్ చేస్తుంది. చూడండి [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## మీకు లభించేవి

- **సెషన్‌లు & ట్రాన్స్‌స్క్రిప్ట్‌లు**: ప్రతి ఏజెంట్ ఏం చేసిందో, టర్న్ బై టర్న్, రీప్లేతో సహా
- **ఖర్చు & టోకెన్‌లు**: రన్‌టైమ్, మోడల్, సెషన్ మరియు రోజు వారీగా, ఎనామలీ ఫ్లాగ్‌లతో సహా
- **ఫ్లో**: ఛానెల్‌లు, మోడల్స్ మరియు టూల్స్ ద్వారా కదులుతున్న మెసేజ్‌ల లైవ్ డయాగ్రామ్
- **బ్రెయిన్**: జరుగుతున్న సమయంలోనే రీజనింగ్ మరియు టూల్-కాల్ ఈవెంట్ స్ట్రీమ్
- **కాంటెక్స్ట్ బ్లోఅవుట్**: ప్రొవైడర్ వారీగా సైజ్ చేయబడిన విండో యుటిలైజేషన్, కంపాక్షన్ vs ఫోర్స్డ్ ఓవర్‌ఫ్లో, అలాగే మనం *చూడలేనిది* ఏమిటో రన్‌టైమ్ వారీ మ్యాప్ ([ఎలా](docs/CONTEXT_BLOWOUT.md))
- **మెమరీ & స్కిల్స్**: ప్రతి రన్‌టైమ్ నిజంగా లోడ్ చేసిన ఫైల్‌లు మరియు స్కిల్స్
- **హెల్త్ & లాగ్స్**: డిస్క్, మెమరీ, ఎర్రర్ రేట్‌లు, రేట్ లిమిట్‌లు, లైవ్ లాగ్ స్ట్రీమ్
- **అలర్ట్‌లు**: బడ్జెట్ క్యాప్‌లు, ఎర్రర్ స్పైక్‌లు, ఏజెంట్-ఆఫ్‌లైన్, Slack, Discord, PagerDuty, Telegram, Email కు రూట్ చేయబడతాయి
- **అప్రూవల్స్**: రిస్కీ టూల్ కాల్స్‌ను అవి రన్ అయ్యే *ముందు* పాజ్ చేసి మీ ఫోన్ నుండి ఆమోదించండి ([ఎలా](docs/APPROVALS.md))

## కాంటెక్స్ట్ బ్లోఅవుట్, మరియు మానిటరింగ్ ఖర్చు ఎంత

ఏదైనా ఏజెంట్-పోలిక టూల్‌ను నమ్మేముందు జవాబు చెప్పదగిన రెండు ప్రశ్నలు.

**రన్‌టైమ్‌ల వ్యాప్తంగా కాంటెక్స్ట్-విండో బ్లోఅవుట్‌ను ఇది ఎలా హ్యాండిల్ చేస్తుంది?**

యుటిలైజేషన్ పర్సెంటేజ్ అనేది అది దేనితో భాగిస్తుందో దాని కంటే నిజాయితీగా ఉండదు. ClawMetry, మీరు చదవగలిగే మరియు PR చేయగలిగే [ఒక టేబుల్](clawmetry/context_windows.py) నుండి ప్రొవైడర్ వారీగా విండోను సైజ్ చేస్తుంది, ఇందులో Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama మరియు GLM ఉన్నాయి. ఇది 26 రన్‌టైమ్‌లనూ ఒకే వెండర్ కొలమానంతో కొలవదు. ఇది ముఖ్యం: Anthropic యొక్క 200K తో పోల్చినప్పుడు 300K GPT-5 టర్న్ ">100%, blown" గా కనిపిస్తుంది, కానీ నిజానికి అది GPT-5 యొక్క 400K లో 75% వద్ద ఉంటుంది. అదే కొలమానం నిజంగా ఓవర్‌ఫ్లో అయిన 130K DeepSeek టర్న్‌ను సౌకర్యవంతమైన 65% గా దాచేస్తుంది.

ప్రతి విండో దాని మూలాన్ని (provenance) తెలియజేస్తుంది: `model_table`, `explicit_marker`, `observed_floor`, లేదా మనకు మోడల్ తెలియనప్పుడు నిజాయితీగా ఒక `default`. ఊహపై నిర్మించిన గేజ్‌కు లుక్అప్ ఆధారంగా నిర్మించినంత అధికారం ఎన్నడూ ఉండదు.

ClawMetry కొన్ని రన్‌టైమ్‌లలో మాత్రమే కంపాక్షన్ ఈవెంట్‌లను చూడగలదు. కాబట్టి `GET /api/context-coverage`, ప్రతి రన్‌టైమ్‌కూ, **జీరో అంటే "క్లీన్‌గా రన్ అయింది" అని అర్థమా లేక "మనకు కనిపించడం లేదు" అని అర్థమా** అనేది రిపోర్ట్ చేస్తుంది. నిజంగా బ్లైండ్ అని అర్థమయ్యే `0` అలానే చెబుతుంది. [పూర్తి వివరాలు](docs/CONTEXT_BLOWOUT.md)

**ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఎంత?**

| పాత్ | మీ ఏజెంట్‌కు జోడించబడేది | డిఫాల్ట్‌గా ఉందా? |
|---|---|---|
| సెషన్-ఫైల్ టెయిలింగ్ (30 రన్‌టైమ్‌లు అన్నీ) | **0**. వేరే ప్రాసెస్, మీ ఏజెంట్‌లో ClawMetry కోడ్ ఉండదు | ఆన్ |
| HTTP ఇంటర్‌సెప్టర్ (`CLAWMETRY_INTERCEPT=1`) | ప్రతి LLM కాల్‌కు **+0.44 ms**, అంటే 5s కాల్‌లో 0.009% | ఆఫ్ |
| Pre-tool hook గేట్ (వార్మ్ కాచే) | 36 ms ఇంటర్‌ప్రెటర్ ఫ్లోర్ పైన, ప్రతి గేటెడ్ టూల్ కాల్‌కు **+44 ms** | ఆఫ్ |
| ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీ | ప్రతి LLM కాల్‌కు **+9.7 ms** | ఆఫ్ |

డెమోన్ హోస్ట్ ఖర్చు: **2,762 events/sec** ఇంజెస్ట్, డిస్క్ పై **710 bytes/event** (100k ఈవెంట్‌లకు 67.7 MB), మరియు బిజీ ఇన్‌స్టాల్‌లో సస్టెయిన్డ్‌గా **~12% ఒక కోర్**. ఆ చివరి సంఖ్య మన స్వంత పేర్కొన్న 5-10% బడ్జెట్ కంటే ఎక్కువ, కాబట్టి దీన్ని పేజీ నుండి వదిలేయకుండా వెంటాడాల్సిన బగ్‌గా ప్రచురించాం.

Apple M2 Pro పై `benchmarks/overhead.py` తో కొలవబడింది. హార్నెస్ ప్రతి కండిషన్‌ను వేరే ప్రాసెస్‌లో రన్ చేస్తుంది, వాటి క్రమాన్ని మారుస్తుంది, మరియు **రౌండ్‌లు దాని సంకేతంపై (sign) ఏకీభవించనప్పుడు సంఖ్యను ప్రింట్ చేయడానికి నిరాకరిస్తుంది**. దీన్ని మీ స్వంత మెషీన్ పై ఒక నిమిషంలో రన్ చేయండి:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

hook గేట్‌లు మరియు ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీతో సహా ప్రతి పాత్ కొలవబడింది, మరియు హార్నెస్ CI లో Linux, macOS మరియు Windows పై రన్ అవుతుంది. తెలుసుకోవాల్సిన రెండు ఫలితాలు: Windows పై ప్రాక్సీ Linux కంటే దాదాపు ఏడు రెట్లు ఖర్చవుతుంది, మరియు డెమోన్ ప్రస్తుతం ఒక కోర్‌లో దాదాపు 12% సస్టెయిన్ చేస్తుంది, ఇది మన స్వంత 5-10% బడ్జెట్ కంటే ఎక్కువ. రా JSON, పద్ధతి, మరియు ఇంకా కొలవని విషయాలు [docs/OVERHEAD.md](docs/OVERHEAD.md) లో ఉన్నాయి.

## ప్రైసింగ్

| ప్లాన్ | ఇందులో ఏమి ఉంటుంది | ధర |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, పూర్తి డాష్‌బోర్డ్, లోకల్ మాత్రమే | $0 |
| **Starter** | పైన పేర్కొన్న మిగతా అన్ని రన్‌టైమ్‌లు, ఫ్లీట్ వ్యూ, క్లౌడ్ సింక్ | $9 per node / month |
| **Pro** | Starter + కంట్రోల్ మరియు ఎవాల్యుయేషన్: అప్రూవల్స్, టూల్-రిస్క్ పాలసీలు, evals, ఎనామలీ డిటెక్షన్, కాస్ట్ ఆప్టిమైజర్, OTel ఎక్స్‌పోర్ట్, tamper-evident ఆడిట్ లాగ్ | $19 per node / month |

వార్షిక ప్లాన్‌లు, Enterprise మరియు ప్రస్తుత సంఖ్యలు **[clawmetry.com/pricing](https://clawmetry.com/pricing)** లో ఉన్నాయి. సెల్ఫ్-హోస్టెడ్ లైసెన్స్ కీలు క్లౌడ్ లేకుండానే పనిచేస్తాయి (`clawmetry license`). ఖచ్చితమైన ఉచిత/చెల్లింపు విభజన [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) లో ఉంది.

## మీ డేటా మీ మెషీన్‌లోనే ఉంటుంది

ClawMetry లోకల్ సెషన్ ఫైల్‌లు మరియు లాగ్‌లను చదువుతుంది. **మీరు `clawmetry connect` రన్ చేయకుండా ఏ సెషన్ డేటా మీ బాక్స్ నుండి బయటకు వెళ్లదు** — ప్రాంప్ట్‌లు, రిప్లైలు, టూల్ ఆర్గ్యుమెంట్‌లు, ఫైల్ కంటెంట్‌లు లేదా లాగ్ లైన్‌లు లేవు. మీరు కనెక్ట్ చేసినప్పుడు, స్నాప్‌షాట్ మీ మెషీన్ నుండి ఎన్నడూ బయటకు వెళ్లని కీతో end-to-end ఎన్‌క్రిప్ట్ చేయబడుతుంది, మరియు మీ బ్రౌజర్‌లో డిక్రిప్ట్ అవుతుంది. ఒక నోడ్‌కు కీ లేకపోతే, అప్‌లోడ్ క్లియర్‌గా పంపే బదులు స్కిప్ చేయబడుతుంది, మరియు ఏ సర్వర్ రెస్పాన్స్ కూడా దీన్ని ఆఫ్ చేయలేదు.

మీరు కనెక్ట్ అవ్వకముందే డిఫాల్ట్‌గా రెండు విషయాలు రన్ అవుతాయి, రెండూ ఆప్ట్-అవుట్ మరియు ఏదీ సెషన్ డేటాను కలిగి ఉండదు: ఒక అనానిమస్ ఇన్‌స్టాల్ పింగ్ మరియు PyPI కు వెర్షన్ చెక్. డిఫాల్ట్ ఇన్‌స్టాల్ కూడా స్టార్టప్ బ్యానర్ లైన్ కోసం మీ పబ్లిక్ IP ని ఒకసారి లుక్అప్ చేస్తుంది. ప్రతి డెస్టినేషన్, అది ఏమి కలిగి ఉంటుంది మరియు దాన్ని ఎలా ఆఫ్ చేయాలో [docs/EGRESS.md](docs/EGRESS.md) లో లిస్ట్ చేయబడింది; సెల్ఫ్-హోస్టెడ్, రీపాయింటెడ్ మరియు ఎయిర్-గ్యాప్డ్ ఇన్‌స్టాల్‌లు ఎలాంటి డిస్క్రెషనరీ అవుట్‌బౌండ్ కాల్స్ చేయవు.

డిక్రిప్షన్ మేము మీకు అందించే కోడ్‌లో, మీ బ్రౌజర్‌లో జరుగుతుంది. అది ఒకప్పుడు ఒక వాగ్దానం మాత్రమే; ఇప్పుడు మీరు దాన్ని చెక్ చేయగల విషయం. మీ కీని తాకే ప్రతి లైన్ ఒకే చదవదగిన ఫైల్‌లో ఉంది, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ఇది wheel లోపల షిప్ అవుతుంది మరియు యథాతథంగా అందించబడుతుంది, ఒక Subresource Integrity హాష్‌తో పిన్ చేయబడి. బ్రౌజర్ మేము ప్రచురించినదాన్నే రన్ చేస్తుందని నిర్ధారించుకోవడానికి:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ఇది నిరూపించనిది ఏమిటంటే: ఫైల్‌ను లోడ్ చేసే పేజీని కూడా మేమే అందిస్తాము, కాబట్టి మేము వేరే పేజీని అందించే అవకాశం ఉంది. ఇంటిగ్రిటీ హాష్‌లు మిమ్మల్ని compromised CDN నుండి కాపాడతాయి, వెండర్ నుండి కాదు. మీకు లభించేదేమంటే, ఏదైనా ప్రత్యామ్నాయం ఉద్దేశపూర్వకంగా, పేజీ సోర్స్‌లో కనిపించేలా, మరియు ఎవరైనా ఫెచ్ చేయగల PyPI ఆర్టిఫాక్ట్ నుండి భిన్నంగా ఉండాలి. సెల్ఫ్-హోస్టింగ్ చేయడం లేదా లోకల్-మాత్రమే ఉండటం ఈ డిపెండెన్సీని పూర్తిగా తొలగిస్తుంది.

## ఇన్‌స్టాల్

```bash
pip install clawmetry     # then: clawmetry
```

లేదా వన్-లైనర్: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux లేదా Windows పై Python 3.8+ కావాలి, మరియు అదే మెషీన్‌పై కనీసం ఒక ఏజెంట్ రన్‌టైమ్ ఉండాలి. Docker సూచనలు: [docs/DOCKER.md](docs/DOCKER.md).

## డాక్స్

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ప్రతి అడాప్టర్ ఏమి చదువుతుంది, మరియు ఒక రన్‌టైమ్‌ను ఎలా జోడించాలి |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | ప్రొవైడర్ వారీ విండోలు, కంపాక్షన్ vs ఓవర్‌ఫ్లో, రన్‌టైమ్ వారీ కవరేజ్ |
| [Overhead](docs/OVERHEAD.md) | ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఏమిటో, కొలవబడింది, రీప్రొడ్యూస్ చేయడానికి హార్నెస్‌తో సహా |
| [Entitlements](docs/ENTITLEMENTS.md) | ఉచితం vs చెల్లింపు, టైర్ మ్యాట్రిక్స్, లైసెన్స్ CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution గేటింగ్, రిస్క్ స్కోరింగ్, ఫోన్ అప్రూవల్స్ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ట్రేసులను ఎక్కడికైనా ఎక్స్‌పోర్ట్ చేయండి, దేనినుండైనా OTLP ఇంజెస్ట్ చేయండి |
| [SDK tracking](docs/SDK_TRACKING.md) | మీరే నిర్మించిన ఏజెంట్‌ల కోసం కాస్ట్ అట్రిబ్యూషన్ |
| [Chat channels](docs/CHANNELS.md) | Flow లో చూపబడే చాట్ అడాప్టర్‌లు |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw సెటప్‌లు |
| [Docker](docs/DOCKER.md) | ఇమేజ్, compose, వాల్యూమ్ మౌంట్‌లు |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ఇది లోపల ఎలా పనిచేస్తుంది; సోర్స్ నుండి రన్ చేయడం |
| [Telemetry](docs/TELEMETRY.md) | అనానిమస్ ఇన్‌స్టాల్ మరియు డెస్క్‌టాప్-ఓపెన్ పింగ్‌లు, మరియు వాటిని ఎలా ఆఫ్ చేయాలి |

## స్క్రీన్‌షాట్‌లు

క్రింద ఉన్న ప్రతి సంఖ్య ఒక నిజమైన మెషీన్ నుండి, read-only గా, ఏమీ సీడ్ చేయకుండా తీసుకోబడింది.

**ఏదో తప్పు జరిగినప్పుడు మాత్రమే కాకుండా, తప్పు జరిగిందని కూడా ఇది మీకు చెబుతుంది.**
పైన రెండు ఎనామలీ బ్యానర్‌లు: రోజువారీ సగటు కంటే 7x ఖర్చు నడుస్తోంది, మరియు 4.2x కాస్ట్ స్పైక్. వాటి క్రింద, 667 ఇటీవలి సెషన్‌లలో 324, వేస్ట్ సిగ్నల్ కలిగి ఉన్నాయని, కారణం వారీగా జాబితా చేయబడ్డాయి.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**డబ్బు ఎక్కడికి వెళ్లిందో ప్రతి విండోలో ఇది మీకు చూపిస్తుంది.**
ఈరోజు $252.47, ఈవారం $513.15, ఈనెల $1,312.92, ప్రతిదానికీ దాని వెనుక ఉన్న టోకెన్‌లు మరియు మీ సబ్‌స్క్రిప్షన్ ఇప్పటికే ఎంత కవర్ చేస్తుందో దానితో సహా. దాని క్రింద, రికవరబుల్‌గా జాబితా చేయబడిన సుమారు $1,128/mo మరియు కాచే రీయూజ్ ద్వారా ఇప్పటికే సేవ్ చేయబడిన $17,256/mo.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ఒక మెసేజ్ ఎలా ఒక సమాధానంగా మారుతుందో ఇది గీస్తుంది.**
లైవ్ ఫ్లో డయాగ్రామ్: మీరు, అది వచ్చిన ఛానెల్, గేట్‌వే, ప్రస్తుతం సమాధానం ఇస్తున్న మోడల్, మరియు అది చేరుకున్న ప్రతి టూల్. పని వాటి గుండా కదులుతున్నప్పుడు నోడ్‌లు వెలుగుతాయి.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**మెషీన్‌లోని ప్రతి ఏజెంట్, ఒకే టేబుల్‌లో.**
అది ఏమి రన్ చేస్తుంది, గత 24 గంటల్లో మరియు దాని లైఫ్‌టైమ్‌లో దాని ఖర్చు ఎంత, అది చివరిగా ఎప్పుడు కనిపించింది, దాన్ని ఎవరు ఓన్ చేస్తారు, మరియు ఒక సబ్‌స్క్రిప్షన్ బిల్‌ను కవర్ చేస్తుందో లేదో. ఇక్కడ 14 ఏజెంట్‌లు, 3 సెషన్‌లు పని చేస్తున్నాయి, 13 నిశ్శబ్దంగా ఉన్నాయి.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ఒక టర్న్ యొక్క సమయం మరియు డబ్బు ఎక్కడికి వెళ్లిందో, టూల్ వారీగా ఇది చూపిస్తుంది.**
ఒక నిజమైన సెషన్ యొక్క ఒక టర్న్: $1.16 కు 11.2 నిమిషాల్లో 11 టూల్స్. ప్రతి Bash కాల్ మరియు మోడల్ కాల్‌కు టైమ్‌లైన్‌పై దాని స్వంత బార్ లభిస్తుంది, కాబట్టి 4.1 నిమిషాలు నడిచిన కమాండ్ మరియు 226ms నడిచిన కమాండ్‌ను ఒక్క చూపులోనే వేరు చేయవచ్చు.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ఇది ఖర్చును మాత్రమే కాకుండా, పనిని కూడా గ్రేడ్ చేస్తుంది.**
ఈవారం ఒక A: 54 టాస్క్‌లు క్లీన్‌గా వచ్చాయి, 2 రఫ్ వన్‌లు $48.57 ఖర్చయ్యాయి, మరియు జడ్జ్ చేయడానికి చాలా తక్కువ యాక్టివిటీ ఉన్న రన్‌లు గెలుపులుగా లెక్కించే బదులు గ్రేడ్ నుండి బయటపెట్టబడ్డాయి. ప్రతి రఫ్ రన్ దాని ట్రేస్‌కు లింక్ చేయబడుతుంది.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**కాంటెక్స్ట్ విండో ఎందుకు నిండుతూనే ఉందో ఇది చూపిస్తుంది.**
తాజా టర్న్‌లో 1M-టోకెన్ విండోలో 715K, 83.3% పీక్, ఓవర్‌ఫ్లోపై కాకుండా అన్నీ proactively ఫైర్ అయిన 4 కంపాక్షన్‌లు, మరియు దాని వెనుక ప్రతి టర్న్ యొక్క యుటిలైజేషన్.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**మీరు ఏమీ కాన్ఫిగర్ చేయకుండానే డిటెక్షన్ నడుస్తుంది.**
బిల్ట్-ఇన్ డిటెక్టర్‌లు ఇన్‌స్టాల్ నుండే ఆన్‌లో ఉన్నాయి: ఏజెంట్ నిశ్శబ్దమైంది, టెలిమెట్రీ ఫీడ్ ఆగిపోయింది, కాస్ట్ స్పైక్, టోకెన్ బరస్ట్, ఎర్రర్‌లు పెరుగుతున్నాయి, ఎర్రర్ స్పైక్, బడ్జెట్ థ్రెషోల్డ్, థ్రెట్ సిగ్నేచర్ మ్యాచ్ అయింది, సెక్యూరిటీ టూల్ ఫైండింగ్, సెక్యూరిటీ పోశ్చర్ మారింది. మీ స్వంత రూల్స్ దీనిపైన ఆప్షనల్‌గా ఉంటాయి.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**రిస్కీ కాల్‌ను హోల్డ్ చేయడం ఆప్ట్-ఇన్, మరియు ఆఫ్‌గా షిప్ అవుతుంది.**
Recursive డిలీట్‌లు, ఫోర్స్ పుష్‌లు, sudo, సీక్రెట్‌లు, ప్యాకేజీ ఇన్‌స్టాల్‌లు మరియు అవుట్‌బౌండ్ కాల్స్ ప్రతిదానికీ మీరు ఆన్ చేయగల ఒక రూల్ ఉంది. మీరు ఆన్ చేసేవరకు, ClawMetry గమనిస్తుంది, ఏమీ మార్చదు. ఒకటి ఆన్ అయిన తర్వాత, మ్యాచ్ అయ్యే కాల్‌లు ఇక్కడ (లేదా మీ ఫోన్‌లో) ఆమోదం లేదా తిరస్కరణ కోసం వేచి ఉంటాయి.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

మరిన్ని, రన్‌టైమ్ వారీగా: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## స్టార్ హిస్టరీ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## లైసెన్స్

MIT · నిర్మించినవారు [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
