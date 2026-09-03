<!-- i18n-src:9767c8001c9c -->
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

ఒక్క కమాండ్. జీరో కాన్ఫిగ్. అన్నింటినీ ఆటోమేటిక్‌గా గుర్తిస్తుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది. జీరో కాన్ఫిగ్: మీ దగ్గర ఇప్పటికే ఉన్న ఏజెంట్ రన్‌టైమ్‌లను ఇది కనుగొంటుంది, వాటిని రీడ్-ఓన్లీగా చదువుతుంది, మరియు అవి ఎలా నడుస్తున్నాయో దానిలో ఏమీ మార్చదు.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ఏజెంట్ రన్‌టైమ్‌లతో పనిచేస్తుంది

**ఓపెన్ సోర్స్ యాప్‌లో ఉచితం:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**చెల్లింపు ప్లాన్‌లో:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ప్రతి రన్‌టైమ్‌కు ఒకే డాష్‌బోర్డ్ లభిస్తుంది. ఒకేసారి అనేకం రన్ చేయండి, హెడర్ స్విచర్ ప్రతి ట్యాబ్‌నూ వాటిలో ఒకదానికి రీ-స్కోప్ చేస్తుంది.

SDK మీద మీ సొంత ఏజెంట్‌ని నిర్మించారా? ఇంటర్‌సెప్టర్ దాని LLM కాల్స్‌నూ ట్రాక్ చేస్తుంది. చూడండి [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## మీకు ఏమి లభిస్తుంది

- **సెషన్‌లు & ట్రాన్‌స్క్రిప్ట్‌లు**: ప్రతి ఏజెంట్ ఏమి చేసిందో, ప్రతి టర్న్‌కూ, రీప్లేతో సహా
- **వ్యయం & టోకెన్‌లు**: రన్‌టైమ్, మోడల్, సెషన్ మరియు రోజు వారీగా, anomaly ఫ్లాగ్‌లతో
- **ఫ్లో**: ఛానెల్స్, మోడల్స్ మరియు టూల్స్ ద్వారా కదులుతున్న మెసేజ్‌ల లైవ్ డయాగ్రామ్
- **బ్రెయిన్**: రీజనింగ్ మరియు టూల్-కాల్ ఈవెంట్ స్ట్రీమ్ జరుగుతున్నప్పుడే
- **కాంటెక్స్ట్ బ్లోఅవుట్**: ప్రొవైడర్ ప్రకారం సైజ్ చేయబడిన విండో యుటిలైజేషన్, compaction vs forced overflow, మరియు మనం *చూడలేనిది* ఏమిటో రన్‌టైమ్ వారీగా ఒక మ్యాప్ ([ఎలా](docs/CONTEXT_BLOWOUT.md))
- **మెమరీ & స్కిల్స్**: ప్రతి రన్‌టైమ్ నిజంగా లోడ్ చేసిన ఫైళ్లు మరియు స్కిల్స్
- **హెల్త్ & లాగ్స్**: డిస్క్, మెమరీ, ఎర్రర్ రేట్లు, రేట్ లిమిట్లు, లైవ్ లాగ్ స్ట్రీమ్
- **అలర్ట్‌లు**: బడ్జెట్ క్యాప్‌లు, ఎర్రర్ స్పైక్‌లు, ఏజెంట్-ఆఫ్‌లైన్, Slack, Discord, PagerDuty, Telegram, Email కు రూట్ చేయబడతాయి
- **అప్రూవల్స్**: రిస్కీ టూల్ కాల్స్‌ను అవి రన్ అవ్వక *ముందే* పాజ్ చేసి మీ ఫోన్ నుండి ఆమోదించండి ([ఎలా](docs/APPROVALS.md))

## కాంటెక్స్ట్ బ్లోఅవుట్, మరియు వాచింగ్ ఖర్చు ఎంత

ఏదైనా ఏజెంట్-పోలిక టూల్‌ని నమ్మేముందు సమాధానం చెప్పాల్సిన రెండు ప్రశ్నలు.

**రన్‌టైమ్‌ల మధ్య కాంటెక్స్ట్-విండో బ్లోఅవుట్‌ను ఇది ఎలా హ్యాండిల్ చేస్తుంది?**

యుటిలైజేషన్ శాతం అది దేనితో భాగిస్తుందో అంతే నిజాయితీగా ఉంటుంది. ClawMetry విండోను ప్రొవైడర్ వారీగా, మీరు చదవగలిగే మరియు PR చేయగలిగే [ఒక టేబుల్](clawmetry/context_windows.py) నుండి సైజ్ చేస్తుంది, ఇది Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama మరియు GLM లను కవర్ చేస్తుంది. ఇది 26 రన్‌టైమ్‌లనూ ఒకే వెండర్ కొలబద్దతో కొలవదు. ఇది ముఖ్యం: 300K GPT-5 టర్న్‌ను Anthropic యొక్క 200K కు వ్యతిరేకంగా స్కోర్ చేస్తే ">100%, blown" అని చదవబడుతుంది, కానీ నిజానికి అది GPT-5 యొక్క 400K లో 75% వద్ద ఉంటుంది. అదే కొలబద్ద నిజంగా overflow అయిన 130K DeepSeek టర్న్‌ను సౌకర్యవంతమైన 65% గా దాచేస్తుంది.

ప్రతి విండో దాని మూలాన్ని (provenance) తీసుకువస్తుంది: `model_table`, `explicit_marker`, `observed_floor`, లేదా మనకు మోడల్ తెలియనప్పుడు నిజాయితీగల `default`. ఊహపై ఆధారపడిన గేజ్ ఎప్పుడూ లుక్అప్‌పై ఆధారపడిన దానితో సమానమైన అధికారంతో రెండర్ కాదు.

కొన్ని రన్‌టైమ్‌లలో మాత్రమే ClawMetry compaction ఈవెంట్‌లను చూడగలదు. కాబట్టి `GET /api/context-coverage` ప్రతి రన్‌టైమ్‌కూ, **సున్నా అంటే "క్లీన్‌గా నడిచింది" అని అర్థమా లేదా "మనకు కనిపించడం లేదు" అని అర్థమా** అనేది రిపోర్ట్ చేస్తుంది. నిజంగా బ్లైండ్ అని అర్థం వచ్చే `0` ఆ విషయాన్ని చెప్తుంది.
[పూర్తి వివరాలు](docs/CONTEXT_BLOWOUT.md)

**ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఎంత?**

| పాత్ | మీ ఏజెంట్‌కు జోడించబడింది | డిఫాల్ట్‌గా ఆన్‌గా ఉందా? |
|---|---|---|
| సెషన్-ఫైల్ టెయిలింగ్ (అన్ని 30 రన్‌టైమ్‌లు) | **0**. ప్రత్యేక ప్రాసెస్, మీ ఏజెంట్‌లో ClawMetry కోడ్ ఏమీ లేదు | on |
| HTTP ఇంటర్‌సెప్టర్ (`CLAWMETRY_INTERCEPT=1`) | ప్రతి LLM కాల్‌కు **+0.44 ms**, అంటే 5s కాల్‌లో 0.009% | off |
| Pre-tool హుక్ గేట్ (వార్మ్ కాష్) | ప్రతి గేటెడ్ టూల్ కాల్‌కు **+44 ms**, 36 ms ఇంటర్‌ప్రెటర్ ఫ్లోర్‌పై | off |
| ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీ | ప్రతి LLM కాల్‌కు **+9.7 ms** | off |

డెమన్ హోస్ట్ ఖర్చు: **2,762 ఈవెంట్‌లు/సెకన్** ఇన్జెస్ట్, డిస్క్‌పై **710 బైట్‌లు/ఈవెంట్** (100k ఈవెంట్‌లకు 67.7 MB), మరియు బిజీ ఇన్‌స్టాల్‌పై సస్టెయిన్డ్‌గా **ఒక కోర్‌లో ~12%**. ఆ చివరి సంఖ్య మన స్వంత 5-10% బడ్జెట్‌ను మించిపోయింది, కాబట్టి దీన్ని పేజీ నుండి తీసివేయడానికి బదులు వెంబడించాల్సిన బగ్‌గా ప్రచురించాం.

Apple M2 Pro పై `benchmarks/overhead.py` తో కొలవబడింది. హార్నెస్ ప్రతి కండిషన్‌నూ ప్రత్యేక ప్రాసెస్‌లో రన్ చేస్తుంది, వాటి క్రమాన్ని మార్చుతుంది, మరియు **రౌండ్‌లు దాని సంకేతంపై ఏకీభవించనప్పుడు ఒక సంఖ్యను ప్రింట్ చేయడాన్ని తిరస్కరిస్తుంది**. దీన్ని మీ స్వంత మెషీన్‌పై ఒక్క నిమిషంలో రన్ చేయండి:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

హుక్ గేట్‌లు మరియు ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీతో సహా, ప్రతి పాత్ కొలవబడింది, మరియు హార్నెస్ CI లో Linux, macOS మరియు Windows పై నడుస్తుంది. తెలుసుకోవాల్సిన రెండు ఫలితాలు: ప్రాక్సీకి Windows పై Linux కంటే దాదాపు ఏడు రెట్లు ఎక్కువ ఖర్చవుతుంది, మరియు డెమన్ ప్రస్తుతం ఒక కోర్‌లో దాదాపు 12% సస్టెయిన్ చేస్తోంది, ఇది మన స్వంత 5-10% బడ్జెట్‌ను మించి. రా JSON, పద్ధతి, మరియు ఇంకా కొలవని దానితో సహా [docs/OVERHEAD.md](docs/OVERHEAD.md) లో ఉన్నాయి.

## ప్రైసింగ్

| ప్లాన్ | ఇది ఏమి కవర్ చేస్తుంది | ధర |
|---|---|---|
| **ఉచితం** | OpenClaw + NVIDIA NemoClaw + Goose, పూర్తి డాష్‌బోర్డ్, స్థానికంగా మాత్రమే | $0 |
| **Starter** | పైన పేర్కొన్న ప్రతి ఇతర రన్‌టైమ్, ఫ్లీట్ వ్యూ, క్లౌడ్ సింక్ | నోడ్‌కు $9 / నెల |
| **Pro** | Starter + నియంత్రణ మరియు మూల్యాంకనం: అప్రూవల్స్, టూల్-రిస్క్ పాలసీలు, evals, anomaly detection, cost optimizer, OTel export, tamper-evident ఆడిట్ లాగ్ | నోడ్‌కు $19 / నెల |

వార్షిక ప్లాన్‌లు, Enterprise మరియు ప్రస్తుత సంఖ్యలు
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** వద్ద ఉన్నాయి. Self-hosted లైసెన్స్
కీలు క్లౌడ్ లేకుండానే పనిచేస్తాయి (`clawmetry license`). ఖచ్చితమైన ఉచిత/చెల్లింపు విభజన
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) లో ఉంది.

## మీ డేటా మీ మెషీన్‌లోనే ఉంటుంది

ClawMetry స్థానిక సెషన్ ఫైళ్లు మరియు లాగ్‌లను చదువుతుంది. మీరు `clawmetry connect` రన్ చేయనంత వరకు
**ఏ సెషన్ డేటానూ మీ బాక్స్ నుండి బయటకు పంపదు** — ప్రాంప్ట్‌లు, రిప్లైలు, టూల్ ఆర్గ్యుమెంట్‌లు, ఫైల్
కంటెంట్‌లు లేదా లాగ్ లైన్‌లు ఏమీ లేవు. మీరు connect చేసినప్పుడు, స్నాప్‌షాట్ మీ మెషీన్ నుండి ఎప్పుడూ
బయటకు వెళ్లని కీతో end-to-end encrypted గా ఉంటుంది, మరియు మీ బ్రౌజర్‌లో డిక్రిప్ట్ అవుతుంది. ఒక
నోడ్‌కు కీ లేకపోతే, అప్‌లోడ్ క్లియర్‌గా పంపబడకుండా స్కిప్ చేయబడుతుంది, మరియు దాన్ని ఆఫ్ చేయగల
సర్వర్ రెస్పాన్స్ ఏదీ లేదు.

మీరు connect చేయడానికి ముందు రెండు విషయాలు డిఫాల్ట్‌గా రన్ అవుతాయి, రెండూ opt-out
మరియు ఏదీ సెషన్ డేటాను తీసుకువెళ్లదు: అనానిమస్ ఇన్‌స్టాల్ పింగ్ మరియు PyPI కు వ్యతిరేకంగా వెర్షన్
చెక్. డిఫాల్ట్ ఇన్‌స్టాల్ కూడా స్టార్టప్ బ్యానర్ లైన్ కోసం మీ పబ్లిక్ IP ను ఒకసారి లుకప్ చేస్తుంది.
ప్రతి డెస్టినేషన్, అది ఏమి తీసుకువెళుతుంది మరియు దాన్ని ఎలా ఆఫ్ చేయాలో
[docs/EGRESS.md](docs/EGRESS.md) లో లిస్ట్ చేయబడింది; self-hosted, repointed మరియు air-gapped
ఇన్‌స్టాల్‌లు ఎలాంటి ఐచ్ఛిక అవుట్‌బౌండ్ కాల్‌లు చేయవు.

డిక్రిప్షన్ మీ బ్రౌజర్‌లో, మేము మీకు అందించే కోడ్‌లో జరుగుతుంది. అది ఒకప్పుడు
ఒక వాగ్దానం మాత్రమే; ఇప్పుడు మీరు దాన్ని చెక్ చేయగలిగే విషయం. మీ కీని తాకే ప్రతి లైన్ ఒకే చదవగలిగే
ఫైల్‌లో ఉంది, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
ఇది wheel లోపల షిప్ అవుతుంది మరియు యథాతథంగా సర్వ్ చేయబడుతుంది, ఒక Subresource
Integrity హాష్‌తో పిన్ చేయబడి. బ్రౌజర్ మేము పబ్లిష్ చేసిందే రన్ చేస్తుందని నిర్ధారించుకోవడానికి:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ఇది నిరూపించనిది ఏమిటంటే: ఫైల్‌ను లోడ్ చేసే పేజీని మేమే సర్వ్ చేస్తాము, కాబట్టి మేము వేరే
పేజీని సర్వ్ చేయగలం. Integrity హాష్‌లు మిమ్మల్ని compromised CDN నుండి రక్షిస్తాయి,
వెండర్ నుండి కాదు. మీకు లభించేది ఏమిటంటే ఏదైనా సబ్‌స్టిట్యూషన్ ఉద్దేశపూర్వకంగా, పేజీ సోర్స్‌లో
కనిపించేలా, మరియు ఎవరైనా fetch చేయగల PyPI ఆర్టిఫాక్ట్ నుండి భిన్నంగా ఉండాలి. Self-hosting
లేదా local-only గా ఉండటం ఈ ఆధారపడటాన్ని పూర్తిగా తొలగిస్తుంది.

## ఇన్‌స్టాల్

```bash
pip install clawmetry     # తర్వాత: clawmetry
```

లేదా one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux లేదా Windows పై Python 3.8+ మరియు అదే మెషీన్‌పై కనీసం ఒక ఏజెంట్ రన్‌టైమ్
అవసరం. Docker సూచనలు: [docs/DOCKER.md](docs/DOCKER.md).

## డాక్స్

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ప్రతి అడాప్టర్ ఏమి చదువుతుంది, మరియు రన్‌టైమ్‌ను ఎలా జోడించాలి |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | ప్రొవైడర్-వారీ విండోలు, compaction vs overflow, రన్‌టైమ్-వారీ కవరేజ్ |
| [Overhead](docs/OVERHEAD.md) | ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఎంత, కొలవబడింది, రీప్రొడ్యూస్ చేయడానికి హార్నెస్‌తో |
| [Entitlements](docs/ENTITLEMENTS.md) | ఉచితం vs చెల్లింపు, టైర్ మ్యాట్రిక్స్, లైసెన్స్ CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, రిస్క్ స్కోరింగ్, ఫోన్ అప్రూవల్స్ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ఎక్కడైనా ట్రేసులను ఎక్స్‌పోర్ట్ చేయండి, ఎక్కడి నుండైనా OTLP ఇన్జెస్ట్ చేయండి |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain చివరి వరకూ, రన్ చేయగల ఉదాహరణలతో |
| [SDK tracking](docs/SDK_TRACKING.md) | మీరు స్వయంగా నిర్మించిన ఏజెంట్‌ల కోసం కాస్ట్ అట్రిబ్యూషన్ |
| [Chat channels](docs/CHANNELS.md) | Flow లో చూపిన చాట్ అడాప్టర్‌లు |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw సెటప్‌లు |
| [Docker](docs/DOCKER.md) | ఇమేజ్, compose, వాల్యూమ్ మౌంట్‌లు |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ఇది లోపల ఎలా పనిచేస్తుంది; సోర్స్ నుండి రన్ చేయడం |
| [Telemetry](docs/TELEMETRY.md) | అనానిమస్ ఇన్‌స్టాల్ మరియు desktop-open పింగ్‌లు, వాటిని ఎలా ఆఫ్ చేయాలి |

## స్క్రీన్‌షాట్‌లు

కింద ఉన్న ప్రతి సంఖ్యా ఒక నిజమైన మెషీన్ నుండి, రీడ్-ఓన్లీగా, ఏమీ సీడ్ చేయకుండా వచ్చింది.

**ఏదో తప్పు జరిగినప్పుడు ఇది మీకు చెప్తుంది, కేవలం ఏమి జరిగిందో మాత్రమే కాదు.**
పైభాగంలో రెండు anomaly బ్యానర్‌లు: రోజువారీ సగటుకు 7x వ్యయం నడుస్తోంది, మరియు
4.2x కాస్ట్ స్పైక్. వాటి కింద, waste సిగ్నల్ మోస్తున్న 667 ఇటీవలి సెషన్‌లలో 324, కారణం
వారీగా విభజించబడి.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**డబ్బు ఎక్కడికి వెళ్లిందో ప్రతి విండోలో ఇది మీకు చూపిస్తుంది.**
ఈరోజు $252.47, ఈ వారం $513.15, ఈ నెల $1,312.92, ప్రతిదాని వెనుక ఉన్న టోకెన్‌లతో
మరియు మీ సబ్‌స్క్రిప్షన్ ఇప్పటికే ఎంత కవర్ చేస్తుందో దానితో సహా. దాని కింద, దాదాపు
$1,128/నెల recoverable గా విభజించబడింది మరియు cache reuse ద్వారా ఇప్పటికే $17,256/నెల
సేవ్ చేయబడింది.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ఒక మెసేజ్ ఎలా సమాధానంగా మారుతుందో ఇది చూపిస్తుంది.**
లైవ్ ఫ్లో డయాగ్రామ్: మీరు, అది వచ్చిన ఛానెల్, గేట్‌వే, ప్రస్తుతం సమాధానం ఇస్తున్న
మోడల్, మరియు అది ఉపయోగించిన ప్రతి టూల్. పని వాటి గుండా కదులుతున్నప్పుడు నోడ్‌లు
వెలుగుతాయి.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**మెషీన్‌పై ప్రతి ఏజెంట్, ఒకే టేబుల్‌లో.**
అది ఏమి రన్ చేస్తుంది, గత 24 గంటల్లో మరియు దాని జీవితకాలంలో దాని ఖర్చు ఎంత, అది చివరిగా
ఎప్పుడు కనిపించింది, దాన్ని ఎవరు యాజమాన్యం చేస్తారు, మరియు సబ్‌స్క్రిప్షన్ బిల్‌ను కవర్
చేస్తోందా. ఇక్కడ 14 ఏజెంట్‌లు, 3 సెషన్‌లు పనిచేస్తున్నాయి, 13 నిశ్శబ్దంగా ఉన్నాయి.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ఒక టర్న్ యొక్క సమయం మరియు డబ్బు ఎక్కడికి వెళ్లాయో, టూల్ వారీగా ఇది చూపిస్తుంది.**
ఒక నిజమైన సెషన్‌లో ఒక టర్న్: 11.2 నిమిషాల్లో 11 టూల్స్, $1.16 కు. ప్రతి Bash
కాల్‌కు మరియు మోడల్ కాల్‌కు టైమ్‌లైన్‌పై దాని స్వంత బార్ లభిస్తుంది, కాబట్టి 4.1 నిమిషాలు
నడిచిన కమాండ్ మరియు 226ms నడిచింది ఒక చూపులోనే వేరుగా గుర్తించబడతాయి.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ఇది పనిని గ్రేడ్ చేస్తుంది, కేవలం ఖర్చును మాత్రమే కాదు.**
ఈ వారం ఒక A: 54 టాస్క్‌లు క్లీన్‌గా వచ్చాయి, 2 రఫ్ వి $48.57 ఖర్చయ్యాయి, మరియు
జడ్జ్ చేయడానికి చాలా తక్కువ యాక్టివిటీ ఉన్న రన్‌లు గెలుపులుగా లెక్కించబడకుండా గ్రేడ్ నుండి
మినహాయించబడ్డాయి. ప్రతి రఫ్ రన్ దాని ట్రేస్‌కు లింక్ అవుతుంది.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**కాంటెక్స్ట్ విండో ఎందుకు నిండుతూనే ఉందో ఇది చూపిస్తుంది.**
తాజా టర్న్‌లో 1M-టోకెన్ విండోలో 715K, 83.3% పీక్, overflow వద్ద కాకుండా proactive గా
ఫైర్ అయిన 4 compaction లు, మరియు దాని వెనుక ఉన్న ప్రతి టర్న్ యొక్క utilisation.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**మీరు ఏమీ కాన్ఫిగర్ చేయకుండానే డిటెక్షన్ నడుస్తుంది.**
బిల్ట్-ఇన్ డిటెక్టర్‌లు ఇన్‌స్టాల్ నుండే ఆన్‌లో ఉంటాయి: ఏజెంట్ నిశ్శబ్దమైంది, టెలిమెట్రీ ఫీడ్
ఆగిపోయింది, కాస్ట్ స్పైక్, టోకెన్ బర్స్ట్, పెరుగుతున్న ఎర్రర్‌లు, ఎర్రర్ స్పైక్, బడ్జెట్
థ్రెషోల్డ్, threat signature మ్యాచ్ అయింది, సెక్యూరిటీ టూల్ ఫైండింగ్, సెక్యూరిటీ postura
మారింది. మీ స్వంత రూల్స్ దానిపై ఐచ్ఛికం.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**రిస్కీ కాల్‌ను హోల్డ్ చేయడం opt-in, మరియు ఆఫ్‌గా షిప్ అవుతుంది.**
Recursive deletes, force pushes, sudo, secrets, package installs మరియు అవుట్‌బౌండ్
కాల్స్ ప్రతిదానికీ మీరు ఆన్ చేయగల ఒక రూల్ ఉంటుంది. మీరు అలా చేసేంత వరకు, ClawMetry గమనిస్తుంది
మరియు ఏమీ మార్చదు. ఒకటి ఆన్ అయ్యాక, మ్యాచ్ అయ్యే కాల్స్ ఇక్కడ (లేదా మీ ఫోన్‌పై) approve
లేదా deny కోసం వేచి ఉంటాయి.

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
