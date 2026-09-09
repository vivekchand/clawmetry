<!-- i18n-src:61beb8393e2f -->
> తెలుగు translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ఒక ఏజెంట్ ముందుకు పురోగతి లేకుండానే వందల టూల్ కాల్స్ చేయగలదు.** ClawMetry
మీ కోడింగ్ ఏజెంట్లు ఇప్పటికే రాస్తున్న సెషన్ ఫైళ్లను చదివి, టైమ్‌లైన్‌ను,
టూల్ కాల్స్‌ను, రన్‌టైమ్ బహిర్గతం చేసే టోకెన్ మరియు వ్యయ డేటాను ఒకే
వీక్షణలోకి తెస్తుంది — తద్వారా పని చేస్తున్న సుదీర్ఘ రన్‌కు, స్తంభించిన
దానికి మధ్య మీరు తేడా గుర్తించగలరు.

**30 AI ఏజెంట్ రన్‌టైమ్‌లతో** పనిచేస్తుంది — Claude Code, OpenAI Codex, Hermes, OpenClaw & మరో 26. మీ మొత్తం ఏజెంట్ ఫ్లీట్ కోసం ఒకే డాష్‌బోర్డ్. ([పూర్తి జాబితా](SUPPORTED_RUNTIMES.txt), కేటలాగ్ నుండి జనరేట్ చేయబడింది.)

> 🌐 **దీన్ని ఇందులో చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒకే కమాండ్. కాన్ఫిగరేషన్ అవసరం లేదు. ప్రతిదీ స్వయంచాలకంగా గుర్తిస్తుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది. కాన్ఫిగరేషన్ అవసరం లేదు: ఇది
మీ దగ్గర ఇప్పటికే ఉన్న ఏజెంట్ రన్‌టైమ్‌లను కనుగొని, వాటిని రీడ్-ఓన్లీగా
చదువుతుంది, మరియు అవి ఎలా నడుస్తాయో దానిలో ఏమీ మార్చదు.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ఇన్‌స్టాల్ చేయడానికి ముందు

| | |
|---|---|
| **ఇది ఏమి చేస్తుంది** | మీ ఏజెంట్లు ఇప్పటికే రాస్తున్న సెషన్ ఫైళ్లను, లాగ్‌లను చదువుతుంది. SDK లేదు, కోడ్ మార్పు లేదు, మీ యాప్‌లో ఇన్‌స్ట్రుమెంటేషన్ లేదు. |
| **మీరు ఏమి చూస్తారు** | సెషన్ టైమ్‌లైన్, టూల్-బై-టూల్ రీప్లే, టోకెన్ మరియు వ్యయ విభజన, మరియు ట్రాజెక్టరీ సంకేతాలు (లూపింగ్, పునరావృత వైఫల్యాలు) — ప్రతి రన్‌టైమ్ కోసం. |
| **ఏది ఉచితం** | `pip install clawmetry` ఖాతా అవసరం లేకుండా, కీ అవసరం లేకుండా, నెట్‌వర్క్ కాల్ లేకుండా **OpenClaw, NVIDIA NemoClaw మరియు Goose**‌ను చదువుతుంది. మిగతా 27 — Claude Code, Codex, Cursor మరియు మిగిలినవి — క్లోజ్డ్-సోర్స్ `clawmetry-pro` కంపానియన్ ద్వారా చదవబడతాయి, ఇది 7-రోజుల ట్రయల్ లేదా ప్లాన్‌తో వస్తుంది — ఖచ్చితమైన విభజన కోసం [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) చూడండి. |
| **ఎలా ప్రారంభించాలి** | `pip install clawmetry && clawmetry`, తర్వాత localhost:8900 తెరవండి. ఈ మెషీన్‌లో ఇంకా ఏజెంట్లు లేవా? `clawmetry --sample` మూడు లేబుల్ చేయబడిన సింథటిక్ సెషన్‌లతో తెరుచుకుంటుంది. |
| **మీ మెషీన్ నుండి ఏమి బయటకు వెళుతుంది** | మీరు `clawmetry connect` రన్ చేయకపోతే సెషన్ డేటా ఏదీ బయటకు వెళ్లదు. డిఫాల్ట్‌గా రెండు విషయాలు మాత్రమే జరుగుతాయి, రెండూ ఆప్ట్-అవుట్ చేయగలిగేవి మరియు ఏదీ సెషన్ కంటెంట్‌ను కలిగి ఉండదు: అనామక ఇన్‌స్టాల్ పింగ్ మరియు PyPI వెర్షన్ చెక్. ప్రతి గమ్యస్థానం, వ్యాఖ్యల నుండి కాకుండా వైర్ క్యాప్చర్ నుండి తిరిగి నిర్మించబడి, [docs/EGRESS.md](docs/EGRESS.md)లో జాబితా చేయబడింది. |

మీరు అవుట్‌పుట్‌ను అంచనా వేయడానికి ముందు తెలుసుకోవాల్సిన రెండు పరిమితులు: రన్‌టైమ్‌లు
చాలా భిన్నమైన డేటాను బహిర్గతం చేస్తాయి (కొన్ని వ్యయాన్ని అస్సలు ప్రచురించవు —
[మాట్రిక్స్](docs/compatibility.md) ఏ రన్‌టైమ్ ఏది చూపిస్తుందో చెబుతుంది), మరియు
ఒక చర్యను గమనించడం దాన్ని నిరోధించగలగడం లాంటిది కాదు
([ఏ నియంత్రణలు నిజమైనవో, ప్రతి రన్‌టైమ్ కోసం](docs/APPROVALS.md)).


## 30 ఏజెంట్ రన్‌టైమ్‌లతో పనిచేస్తుంది

**ఓపెన్ సోర్స్ యాప్‌లో ఉచితం:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**చెల్లింపు ప్లాన్‌లో:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ప్రతి రన్‌టైమ్‌కు అదే డాష్‌బోర్డ్ లభిస్తుంది. అనేకం ఒకేసారి రన్ చేయండి, హెడర్
స్విచర్ ప్రతి ట్యాబ్‌ను వాటిలో ఒకదానికి తిరిగి-స్కోప్ చేస్తుంది.

SDKపై మీ స్వంత ఏజెంట్‌ను నిర్మించారా? ఇంటర్‌సెప్టర్ దాని LLM కాల్స్‌ను కూడా
ట్రాక్ చేస్తుంది. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) చూడండి.

## మీకు ఏమి లభిస్తుంది

- **సెషన్లు & ట్రాన్‌స్క్రిప్ట్‌లు**: ప్రతి ఏజెంట్ ఏమి చేసిందో, టర్న్ బై టర్న్, రీప్లేతో సహా
- **వ్యయం & టోకెన్‌లు**: ప్రతి రన్‌టైమ్, మోడల్, సెషన్ మరియు రోజు కోసం, అనోమలీ ఫ్లాగ్‌లతో
- **ఫ్లో**: ఛానెళ్లు, మోడళ్లు మరియు టూల్స్ ద్వారా కదులుతున్న సందేశాల లైవ్ డయాగ్రామ్
- **బ్రెయిన్**: జరుగుతున్నప్పుడు రీజనింగ్ మరియు టూల్-కాల్ ఈవెంట్ స్ట్రీమ్
- **కాంటెక్స్ట్ బ్లోఅవుట్**: ప్రతి ప్రొవైడర్ కోసం సైజ్ చేయబడిన విండో యుటిలైజేషన్, కాంపాక్షన్ vs బలవంతపు ఓవర్‌ఫ్లో, మరియు మనం *చూడలేనిది* ఏమిటో ప్రతి రన్‌టైమ్ మ్యాప్ ([ఎలా](docs/CONTEXT_BLOWOUT.md))
- **మెమరీ & స్కిల్స్**: ప్రతి రన్‌టైమ్ నిజంగా లోడ్ చేసిన ఫైళ్లు మరియు స్కిల్స్
- **ఆరోగ్యం & లాగ్‌లు**: డిస్క్, మెమరీ, ఎర్రర్ రేట్లు, రేట్ లిమిట్లు, లైవ్ లాగ్ స్ట్రీమ్
- **అలర్ట్‌లు**: బడ్జెట్ క్యాప్‌లు, ఎర్రర్ స్పైక్‌లు, ఏజెంట్-ఆఫ్‌లైన్, Slack, Discord, PagerDuty, Telegram, Emailకు రూట్ చేయబడతాయి
- **ఆమోదాలు**: రిస్కీ టూల్ కాల్స్‌ను అవి రన్ అవ్వక *ముందే* పాజ్ చేసి మీ ఫోన్ నుండి ఆమోదించండి ([ఎలా](docs/APPROVALS.md))

## కాంటెక్స్ట్ బ్లోఅవుట్, మరియు వాచింగ్ ఖర్చు ఎంత

ఏదైనా ఏజెంట్-పోలిక సాధనాన్ని నమ్మే ముందు సమాధానం చెప్పదగిన రెండు ప్రశ్నలు.

**రన్‌టైమ్‌ల అంతటా కాంటెక్స్ట్-విండో బ్లోఅవుట్‌ను ఇది ఎలా నిర్వహిస్తుంది?**

యుటిలైజేషన్ శాతం అది దేని ద్వారా విభజిస్తుందో అంతే నిజాయితీగా ఉంటుంది. ClawMetry
[మీరు చదవగలిగే మరియు PR చేయగలిగే టేబుల్](clawmetry/context_windows.py) నుండి
ప్రతి ప్రొవైడర్ కోసం విండోను సైజ్ చేస్తుంది, ఇందులో Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama మరియు GLM ఉన్నాయి. ఇది 30 రన్‌టైమ్‌లనూ
ఒకే వెండర్ కొలబద్దతో కొలవదు. అది ముఖ్యం: Anthropic యొక్క 200K తో పోల్చిన
300K GPT-5 టర్న్ ">100%, blown" అని చదవబడుతుంది, నిజానికి అది GPT-5 యొక్క
400K లో 75% వద్ద ఉంటుంది. అదే కొలబద్ద నిజంగా ఓవర్‌ఫ్లో అయిన 130K DeepSeek
టర్న్‌ను సౌకర్యవంతమైన 65%గా దాచిపెడుతుంది.

ప్రతి విండో దాని మూలంతో పంపబడుతుంది: `model_table`, `explicit_marker`,
`observed_floor`, లేదా మనకు మోడల్ తెలియనప్పుడు నిజాయితీగల `default`. ఊహపై
నిర్మించిన గేజ్ ఎప్పుడూ లుకప్‌పై నిర్మించిన దానితో సమానమైన అధికారంతో
రెండర్ కాదు.

కొన్ని రన్‌టైమ్‌లలో మాత్రమే ClawMetry కాంపాక్షన్ ఈవెంట్‌లను చూడగలదు. కాబట్టి
`GET /api/context-coverage` ప్రతి రన్‌టైమ్ కోసం **సున్నా అంటే "క్లీన్‌గా రన్
అయింది" అని అర్థమా లేదా "మనం చూడలేకపోతున్నామా"** అని నివేదిస్తుంది. నిజంగా
బ్లైండ్ అని అర్థం వచ్చే `0` అలాగే చెబుతుంది.
[పూర్తి వివరాలు](docs/CONTEXT_BLOWOUT.md)

**ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఎంత?**

| పాత్ | మీ ఏజెంట్‌కు జోడించబడింది | డిఫాల్ట్? |
|---|---|---|
| సెషన్-ఫైల్ టెయిలింగ్ (అన్ని 30 రన్‌టైమ్‌లు) | **0**. వేరే ప్రాసెస్, మీ ఏజెంట్‌లో ClawMetry కోడ్ లేదు | ఆన్ |
| HTTP ఇంటర్‌సెప్టర్ (`CLAWMETRY_INTERCEPT=1`) | ప్రతి LLM కాల్‌కు **+0.44 ms**, లేదా 5s కాల్‌లో 0.009% | ఆఫ్ |
| ప్రీ-టూల్ హుక్ గేట్ (వార్మ్ క్యాష్) | 36 ms ఇంటర్‌ప్రెటర్ ఫ్లోర్‌పై, ప్రతి గేటెడ్ టూల్ కాల్‌కు **+44 ms** | ఆఫ్ |
| ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీ | ప్రతి LLM కాల్‌కు **+9.7 ms** | ఆఫ్ |

డెమోన్ హోస్ట్ ఖర్చు: **2,762 ఈవెంట్లు/సెకను** ఇంజెస్ట్, డిస్క్‌పై
**710 బైట్లు/ఈవెంట్** (100k ఈవెంట్లకు 67.7 MB), మరియు బిజీ ఇన్‌స్టాల్‌లో
నిలకడగా **~12% ఒక కోర్**. ఆ చివరి సంఖ్య మనం చెప్పిన 5-10% బడ్జెట్ కంటే
ఎక్కువగా ఉంది, కాబట్టి ఇది పేజీ నుండి వదిలేయకుండా వెంటాడాల్సిన బగ్‌గా
ప్రచురించబడింది.

Apple M2 Pro పై `benchmarks/overhead.py`తో కొలవబడింది. హార్నెస్ ప్రతి
కండిషన్‌ను వేరే ప్రాసెస్‌లో రన్ చేస్తుంది, వాటి క్రమాన్ని మారుస్తుంది, మరియు
**రౌండ్‌లు దాని సైన్‌పై విభేదిస్తే సంఖ్యను ముద్రించడానికి నిరాకరిస్తుంది**.
దీన్ని మీ స్వంత మెషీన్‌పై ఒక నిమిషంలో రన్ చేయండి:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

హుక్ గేట్‌లు మరియు ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీతో సహా ప్రతి పాత్ కొలవబడింది,
మరియు హార్నెస్ CIలో Linux, macOS మరియు Windowsపై రన్ అవుతుంది. తెలుసుకోవాల్సిన
రెండు ఫలితాలు: ప్రాక్సీ Windowsపై Linux కంటే దాదాపు ఏడు రెట్లు ఎక్కువ
ఖర్చవుతుంది, మరియు డెమోన్ ప్రస్తుతం ఒక కోర్‌లో సుమారు 12% నిలకడగా ఉపయోగిస్తుంది,
మనం చెప్పిన 5-10% బడ్జెట్ కంటే ఎక్కువ. రా JSON, పద్ధతి, మరియు ఇంకా కొలవని
విషయాలు [docs/OVERHEAD.md](docs/OVERHEAD.md)లో ఉన్నాయి.

## ధరలు

| ప్లాన్ | ఏమి కవర్ చేస్తుంది | ధర |
|---|---|---|
| **ఉచితం** | OpenClaw + NVIDIA NemoClaw + Goose, పూర్తి డాష్‌బోర్డ్, లోకల్ మాత్రమే | $0 |
| **స్టార్టర్** | పైన పేర్కొన్న ప్రతి ఇతర రన్‌టైమ్, ఫ్లీట్ వ్యూ, క్లౌడ్ సింక్ | నోడ్‌కు $9 / నెల |
| **Pro** | స్టార్టర్ + నియంత్రణ మరియు మూల్యాంకనం: ఆమోదాలు, టూల్-రిస్క్ పాలసీలు, ఎవాల్స్, అనోమలీ డిటెక్షన్, కాస్ట్ ఆప్టిమైజర్, OTel ఎగుమతి, టాంపర్-ఎవిడెంట్ ఆడిట్ లాగ్ | నోడ్‌కు $19 / నెల |

వార్షిక ప్లాన్‌లు, Enterprise మరియు ప్రస్తుత సంఖ్యలు
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** వద్ద ఉంటాయి. సెల్ఫ్-హోస్టెడ్
లైసెన్స్ కీలు క్లౌడ్ లేకుండా పనిచేస్తాయి (`clawmetry license`). ఖచ్చితమైన
ఉచిత/చెల్లింపు విభజన [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)లో ఉంది.

## మీ డేటా మీ మెషీన్‌లోనే ఉంటుంది

ClawMetry లోకల్ సెషన్ ఫైళ్లను మరియు లాగ్‌లను చదువుతుంది. **మీరు `clawmetry connect`
రన్ చేయకపోతే మీ బాక్స్ నుండి సెషన్ డేటా ఏదీ బయటకు వెళ్లదు** — ప్రాంప్ట్‌లు, రిప్లైలు,
టూల్ ఆర్గ్యుమెంట్‌లు, ఫైల్ కంటెంట్‌లు లేదా లాగ్ లైన్‌లు ఏవీ కాదు. మీరు కనెక్ట్
చేసినప్పుడు, స్నాప్‌షాట్ మీ మెషీన్ నుండి ఎప్పుడూ బయటకు వెళ్లని కీతో ఎండ్-టు-ఎండ్
ఎన్‌క్రిప్ట్ చేయబడుతుంది, మరియు మీ బ్రౌజర్‌లో డిక్రిప్ట్ చేయబడుతుంది. ఒక నోడ్‌కు
కీ లేకపోతే, అప్‌లోడ్ క్లియర్‌గా పంపే బదులు స్కిప్ చేయబడుతుంది, మరియు ఏ సర్వర్
రెస్పాన్స్ కూడా దాన్ని ఆఫ్ చేయలేదు.

మీరు కనెక్ట్ చేయడానికి ముందు డిఫాల్ట్‌గా రెండు విషయాలు జరుగుతాయి, రెండూ
ఆప్ట్-అవుట్ చేయగలిగేవి మరియు ఏదీ సెషన్ డేటాను కలిగి ఉండదు: అనామక ఇన్‌స్టాల్
పింగ్ మరియు PyPIకి వ్యతిరేకంగా వెర్షన్ చెక్. డిఫాల్ట్ ఇన్‌స్టాల్ కూడా స్టార్టప్
బ్యానర్ లైన్ కోసం మీ పబ్లిక్ IPని ఒకసారి లుకప్ చేస్తుంది. ప్రతి గమ్యస్థానం, అది
ఏమి కలిగి ఉంటుందో మరియు దాన్ని ఎలా ఆఫ్ చేయాలో [docs/EGRESS.md](docs/EGRESS.md)లో
జాబితా చేయబడింది; సెల్ఫ్-హోస్టెడ్, రీపాయింటెడ్ మరియు ఎయిర్-గ్యాప్డ్ ఇన్‌స్టాల్‌లు
ఐచ్ఛిక అవుట్‌బౌండ్ కాల్‌లు ఏవీ చేయవు.

డిక్రిప్షన్ మీ బ్రౌజర్‌లో, మేము మీకు అందించే కోడ్‌లో జరుగుతుంది. అది ఒకప్పుడు
ఒక వాగ్దానం; ఇప్పుడు మీరు తనిఖీ చేయగలిగే విషయం. మీ కీని తాకే ప్రతి లైన్ ఒకే
చదవదగిన ఫైల్‌లో ఉంటుంది, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
ఇది వీల్ లోపల షిప్ అవుతుంది మరియు యథాతథంగా అందించబడుతుంది, Subresource
Integrity హాష్‌తో పిన్ చేయబడింది. బ్రౌజర్ మేము ప్రచురించిన దాన్నే రన్ చేస్తుందని
నిర్ధారించడానికి:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

అది నిరూపించనిది ఏమిటంటే: ఫైల్‌ను లోడ్ చేసే పేజీని మేమే అందిస్తాము, కాబట్టి
మేము వేరే పేజీని అందించగలం. ఇంటిగ్రిటీ హాష్‌లు మిమ్మల్ని రాజీపడిన CDN నుండి
రక్షిస్తాయి, వెండర్ నుండి కాదు. మీకు లభించేది ఏమిటంటే ఏ ప్రత్యామ్నాయం అయినా
ఉద్దేశపూర్వకంగా, పేజీ సోర్స్‌లో కనిపించేలా, మరియు ఎవరైనా ఫెచ్ చేయగలిగే PyPI
ఆర్టిఫాక్ట్ నుండి భిన్నంగా ఉండాలి. సెల్ఫ్-హోస్టింగ్ లేదా లోకల్-ఓన్లీగా
ఉండటం ఈ డిపెండెన్సీని పూర్తిగా తొలగిస్తుంది.

## ఇన్‌స్టాల్

```bash
pip install clawmetry     # తర్వాత: clawmetry
```

లేదా వన్-లైనర్: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux లేదా Windowsపై Python 3.8+ అవసరం, మరియు అదే మెషీన్‌పై కనీసం ఒక
ఏజెంట్ రన్‌టైమ్ అవసరం. Docker సూచనలు: [docs/DOCKER.md](docs/DOCKER.md).

లేదా ఏజెంట్‌నే మీ కోసం సెటప్ చేయనివ్వండి. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
స్కిల్ Claude Code, Codex, Cursor, Gemini CLI, Copilot లేదా OpenCodeకు ClawMetryను
ఇన్‌స్టాల్ చేయడం, మెషీన్‌పై ఏజెంట్లు ఏమి చేస్తున్నాయో మరియు ఎంత ఖర్చు చేస్తున్నాయో
నివేదించడం, అభ్యర్థనపై ఒక సెషన్‌ను ఆపడం, మరియు రిస్కీ టూల్ కాల్‌లను ఆమోదం
కోసం పట్టుకోవడం నేర్పుతుంది:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## డాక్స్

| | |
|---|---|
| [రన్‌టైమ్ కంపాటిబిలిటీ](docs/compatibility.md) | ప్రతి అడాప్టర్ ఏమి చదువుతుంది, మరియు రన్‌టైమ్‌ను ఎలా జోడించాలి |
| [కాంటెక్స్ట్ బ్లోఅవుట్](docs/CONTEXT_BLOWOUT.md) | ప్రతి-ప్రొవైడర్ విండోలు, కాంపాక్షన్ vs ఓవర్‌ఫ్లో, ప్రతి-రన్‌టైమ్ కవరేజ్ |
| [ఓవర్‌హెడ్](docs/OVERHEAD.md) | ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఎంత, కొలవబడింది, దాన్ని రీప్రొడ్యూస్ చేయడానికి హార్నెస్‌తో సహా |
| [ఎంటైటిల్‌మెంట్‌లు](docs/ENTITLEMENTS.md) | ఉచితం vs చెల్లింపు, టైర్ మాట్రిక్స్, లైసెన్స్ CLI |
| [ఆమోదాలు & పాలసీలు](docs/APPROVALS.md) | ప్రీ-ఎగ్జిక్యూషన్ గేటింగ్, రిస్క్ స్కోరింగ్, ఫోన్ ఆమోదాలు |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ట్రేసులను ఎక్కడికైనా ఎగుమతి చేయండి, దేని నుండైనా OTLP ఇంజెస్ట్ చేయండి |
| [మీ స్వంత ఏజెంట్‌ను తీసుకురండి](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain చివరి నుండి చివరి వరకు, రన్ చేయగల ఉదాహరణలతో |
| [SDK ట్రాకింగ్](docs/SDK_TRACKING.md) | మీరు స్వయంగా నిర్మించిన ఏజెంట్‌ల కోసం వ్యయ ఆపాదన |
| [చాట్ ఛానెళ్లు](docs/CHANNELS.md) | Flowలో చూపబడిన చాట్ అడాప్టర్లు |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | సాండ్‌బాక్స్డ్ NVIDIA NemoClaw సెటప్‌లు |
| [Docker](docs/DOCKER.md) | ఇమేజ్, కంపోజ్, వాల్యూమ్ మౌంట్‌లు |
| [ఆర్కిటెక్చర్](ARCHITECTURE.md) · [డెవలప్‌మెంట్](docs/DEVELOPMENT.md) | ఇది లోపల ఎలా పనిచేస్తుంది; సోర్స్ నుండి రన్ చేయడం |
| [టెలిమెట్రీ](docs/TELEMETRY.md) | అనామక ఇన్‌స్టాల్ మరియు డెస్క్‌టాప్-ఓపెన్ పింగ్‌లు, మరియు వాటిని ఎలా ఆఫ్ చేయాలి |

## స్క్రీన్‌షాట్‌లు

క్రింద ప్రతి సంఖ్య ఒక నిజమైన మెషీన్ నుండి, రీడ్-ఓన్లీగా, ఏదీ సీడ్ చేయకుండా వచ్చింది.

**ఏదో తప్పు జరిగినప్పుడు ఇది మీకు చెబుతుంది, కేవలం ఏమి జరిగిందో మాత్రమే కాదు.**
పైన రెండు అనోమలీ బ్యానర్లు: రోజువారీ సగటు కంటే 7x ఎక్కువ ఖర్చు నడుస్తోంది,
మరియు 4.2x వ్యయ స్పైక్. వాటి క్రింద, ఇటీవలి 667 సెషన్‌లలో 324 వేస్ట్ సిగ్నల్‌ను
మోస్తున్నాయి, కారణం వారీగా జాబితా చేయబడింది.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**డబ్బు ఎక్కడికి వెళ్లిందో ఇది ప్రతి విండోలో మీకు చూపిస్తుంది.**
ఈరోజు $252.47, ఈ వారం $513.15, ఈ నెల $1,312.92, ప్రతిదానిలో దాని వెనుక ఉన్న
టోకెన్‌లతో మరియు మీ సబ్‌స్క్రిప్షన్ ఇప్పటికే ఎంత కవర్ చేస్తుందో. దాని క్రింద,
నెలకు సుమారు $1,128 రికవర్ చేయదగినదిగా అంశాలవారీగా, మరియు క్యాష్ రీయూజ్ ద్వారా
నెలకు ఇప్పటికే $17,256 ఆదా చేయబడింది.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ఒక సందేశం ఎలా సమాధానంగా మారుతుందో ఇది గీస్తుంది.**
లైవ్ ఫ్లో డయాగ్రామ్: మీరు, అది వచ్చిన ఛానెల్, గేట్‌వే, ప్రస్తుతం సమాధానం
ఇస్తున్న మోడల్, మరియు అది చేరుకున్న ప్రతి టూల్. పని వాటి గుండా కదులుతున్నప్పుడు
నోడ్‌లు వెలిగిపోతాయి.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**మెషీన్‌పై ఉన్న ప్రతి ఏజెంట్, ఒకే టేబుల్‌లో.**
అది ఏమి రన్ చేస్తుంది, గత 24 గంటల్లో మరియు దాని లైఫ్‌టైమ్‌లో దాని ఖర్చు ఎంత,
చివరిసారి ఎప్పుడు కనిపించింది, దాని యజమాని ఎవరు, మరియు సబ్‌స్క్రిప్షన్
బిల్‌ను కవర్ చేస్తుందా. ఇక్కడ 14 ఏజెంట్లు, 3 సెషన్లు పనిచేస్తున్నాయి, 13
నిశ్శబ్దంగా ఉన్నాయి.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ఒక టర్న్ యొక్క సమయం మరియు డబ్బు ఎక్కడికి వెళ్లాయో ఇది టూల్ బై టూల్ చూపిస్తుంది.**
ఒక నిజమైన సెషన్ యొక్క ఒక టర్న్: $1.16కి 11.2 నిమిషాల్లో 11 టూల్స్. ప్రతి Bash
కాల్ మరియు మోడల్ కాల్‌కు టైమ్‌లైన్‌పై దాని స్వంత బార్ లభిస్తుంది, కాబట్టి
4.1 నిమిషాలు రన్ అయిన కమాండ్‌ను, 226ms రన్ అయిన దాన్నుండి ఒక్క చూపులో
వేరు చేయవచ్చు.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ఇది పనిని గ్రేడ్ చేస్తుంది, కేవలం ఖర్చును మాత్రమే కాదు.**
ఈ వారం ఒక A: 54 టాస్క్‌లు క్లీన్‌గా వచ్చాయి, 2 కఠినమైనవి $48.57 ఖర్చయ్యాయి,
మరియు తీర్పు చెప్పడానికి తగినంత యాక్టివిటీ లేని రన్‌లు గెలుపులుగా లెక్కించే
బదులు గ్రేడ్ నుండి మినహాయించబడ్డాయి. ప్రతి కఠినమైన రన్ దాని ట్రేస్‌కు లింక్
అవుతుంది.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**కాంటెక్స్ట్ విండో ఎందుకు నిండుతూనే ఉందో ఇది చూపిస్తుంది.**
తాజా టర్న్‌లో 1M-టోకెన్ విండోలో 715K, 83.3% పీక్, ఓవర్‌ఫ్లోపై కాకుండా అన్నీ
ప్రోయాక్టివ్‌గా జరిగిన 4 కాంపాక్షన్‌లు, మరియు దాని వెనుక ఉన్న ప్రతి టర్న్
యొక్క యుటిలైజేషన్.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**మీరు ఏదీ కాన్ఫిగర్ చేయకుండానే డిటెక్షన్ నడుస్తుంది.**
బిల్ట్-ఇన్ డిటెక్టర్లు ఇన్‌స్టాల్ నుండే ఆన్‌లో ఉంటాయి: ఏజెంట్ నిశ్శబ్దంగా
మారింది, టెలిమెట్రీ ఫీడ్ ఆగింది, వ్యయ స్పైక్, టోకెన్ బర్స్ట్, ఎర్రర్లు
పెరుగుతున్నాయి, ఎర్రర్ స్పైక్, బడ్జెట్ థ్రెషోల్డ్, థ్రెట్ సిగ్నేచర్ మ్యాచ్
అయింది, సెక్యూరిటీ టూల్ ఫైండింగ్, సెక్యూరిటీ పోశ్చర్ మారింది. మీ స్వంత
నియమాలు దీనిపై ఐచ్ఛికం.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**రిస్కీ కాల్‌ను పట్టుకోవడం ఆప్ట్-ఇన్, మరియు ఆఫ్‌గా షిప్ అవుతుంది.**
రికర్సివ్ డిలీట్‌లు, ఫోర్స్ పుష్‌లు, sudo, సీక్రెట్‌లు, ప్యాకేజీ ఇన్‌స్టాల్‌లు
మరియు అవుట్‌బౌండ్ కాల్‌లు ప్రతిదానికి మీరు ఆన్ చేయగల నియమం ఉంటుంది. మీరు
అలా చేసేవరకు, ClawMetry గమనిస్తుంది మరియు ఏమీ మార్చదు. ఒకటి ఆన్ చేసిన తర్వాత,
మ్యాచ్ అయ్యే కాల్‌లు ఇక్కడ (లేదా మీ ఫోన్‌పై) ఆమోదం లేదా తిరస్కరణ కోసం
వేచి ఉంటాయి.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

మరిన్ని, ప్రతి రన్‌టైమ్ కోసం: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## గుర్తింపు

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
