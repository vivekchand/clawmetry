<!-- i18n-src:12b97259721e -->
> తెలుగు translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ఒక ఏజెంట్ పురోగతి సాధించకుండానే వందల tool calls చేయగలదు.** ClawMetry మీ కోడింగ్ ఏజెంట్లు ఇప్పటికే రాస్తున్న సెషన్ ఫైళ్లను చదివి, టైమ్‌లైన్, tool calls మరియు రన్‌టైమ్ బహిర్గతం చేసే ఎలాంటి టోకెన్ మరియు వ్యయ డేటానైనా ఒకే వీక్షణలో పెడుతుంది — తద్వారా బాగా పనిచేస్తున్న సుదీర్ఘ రన్‌ను, ఎక్కడో ఇరుక్కుపోయిన దానితో పోల్చి మీరు గుర్తించగలరు.

**31 AI ఏజెంట్ రన్‌టైమ్‌లతో** పనిచేస్తుంది — Claude Code, OpenAI Codex, Hermes, OpenClaw & మరో 27. మీ మొత్తం ఏజెంట్ ఫ్లీట్ కోసం ఒకే డాష్‌బోర్డ్. ([పూర్తి జాబితా](SUPPORTED_RUNTIMES.txt), కేటలాగ్ నుండి జనరేట్ చేయబడింది.)

> 🌐 **దీన్ని చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒకే కమాండ్. జీరో కాన్ఫిగ్. ప్రతిదాన్నీ ఆటోమేటిక్‌గా గుర్తిస్తుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది. జీరో కాన్ఫిగ్: మీ దగ్గర ఇప్పటికే ఉన్న ఏజెంట్ రన్‌టైమ్‌లను ఇది కనుగొంటుంది, వాటిని read-only గా చదువుతుంది, మరియు అవి ఎలా నడుస్తున్నాయో దాన్ని ఏమాత్రం మార్చదు.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ఇన్‌స్టాల్ చేసే ముందు

| | |
|---|---|
| **ఇది ఏం చేస్తుంది** | మీ ఏజెంట్లు ఇప్పటికే రాస్తున్న సెషన్ ఫైళ్లను, లాగ్‌లను చదువుతుంది. SDK లేదు, కోడ్ మార్పు లేదు, మీ యాప్‌లో ఎలాంటి instrumentation లేదు. |
| **మీరు చూసేది** | సెషన్ టైమ్‌లైన్, tool-by-tool రీప్లే, టోకెన్ మరియు వ్యయ విభజన, మరియు ట్రాజెక్టరీ సిగ్నల్స్ (looping, పునరావృత వైఫల్యాలు) — రన్‌టైమ్ వారీగా. |
| **ఉచితం ఏది** | `pip install clawmetry` ఖాతా, key, నెట్‌వర్క్ కాల్ ఏమీ లేకుండా **OpenClaw, NVIDIA NemoClaw మరియు Goose** ను చదువుతుంది. మిగతా 27 — Claude Code, Codex, Cursor మరియు మిగిలినవి — క్లోజ్డ్-సోర్స్ `clawmetry-pro` కంపానియన్ ద్వారా చదవబడతాయి, ఇది 7-రోజుల ట్రయల్ లేదా ప్లాన్‌తో వస్తుంది — ఖచ్చితమైన విభజన కోసం [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) చూడండి. |
| **ఎలా మొదలుపెట్టాలి** | `pip install clawmetry && clawmetry`, తర్వాత localhost:8900 తెరవండి. ఈ మెషీన్‌లో ఇంకా ఏజెంట్లు లేవా? `clawmetry --sample` మూడు లేబుల్ చేసిన సింథటిక్ సెషన్‌లతో తెరుచుకుంటుంది. |
| **మీ మెషీన్ నుండి ఏం బయటికి వెళుతుంది** | మీరు `clawmetry connect` రన్ చేయకపోతే, ఎలాంటి సెషన్ డేటా బయటికి వెళ్లదు. డిఫాల్ట్‌గా రెండు విషయాలు మాత్రం రన్ అవుతాయి, రెండూ opt-out చేయదగినవి మరియు సెషన్ కంటెంట్ ఏదీ మోసుకెళ్లనివి: అనామక ఇన్‌స్టాల్ పింగ్ మరియు PyPI వెర్షన్ చెక్. ప్రతి గమ్యస్థానం [docs/EGRESS.md](docs/EGRESS.md)లో జాబితా చేయబడింది, ఇది కామెంట్లు చదవడం కంటే వైర్ క్యాప్చర్ నుండి తిరిగి నిర్మించబడింది. |

మీరు ఫలితాన్ని అంచనా వేసే ముందు తెలుసుకోవాల్సిన రెండు పరిమితులు: రన్‌టైమ్‌లు చాలా భిన్నమైన డేటాను బహిర్గతం చేస్తాయి (కొన్ని ఏ వ్యయాన్నీ ప్రచురించవు — ఏది ఏమిటో [మ్యాట్రిక్స్](docs/compatibility.md) రన్‌టైమ్ వారీగా చెబుతుంది), మరియు ఒక చర్యను గమనించడం అంటే దాన్ని ఆపగలగడం కాదు ([ఏ నియంత్రణలు నిజమైనవో, రన్‌టైమ్ వారీగా](docs/APPROVALS.md)).


## 31 ఏజెంట్ రన్‌టైమ్‌లతో పనిచేస్తుంది

**ఓపెన్ సోర్స్ యాప్‌లో ఉచితం:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**చెల్లింపు ప్లాన్‌లో:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ప్రతి రన్‌టైమ్‌కు ఒకే డాష్‌బోర్డ్ వస్తుంది. ఒకేసారి అనేకం రన్ చేయండి, హెడర్ స్విచర్ ప్రతి ట్యాబ్‌ను వాటిలో ఒకదానికి తిరిగి స్కోప్ చేస్తుంది.

SDK మీద మీ సొంత ఏజెంట్ నిర్మించుకున్నారా? ఇంటర్‌సెప్టర్ దాని LLM కాల్స్‌ను కూడా ట్రాక్ చేస్తుంది. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) చూడండి.

## మీకు లభించేది

- **సెషన్‌లు & ట్రాన్‌స్క్రిప్ట్‌లు**: ప్రతి ఏజెంట్ ఏం చేసిందో, టర్న్ బై టర్న్, రీప్లేతో సహా
- **వ్యయం & టోకెన్‌లు**: రన్‌టైమ్, మోడల్, సెషన్ మరియు రోజు వారీగా, అనోమలీ ఫ్లాగ్‌లతో సహా
- **ఫ్లో**: ఛానెల్స్, మోడల్స్ మరియు టూల్స్ ద్వారా కదులుతున్న మెసేజ్‌ల లైవ్ డయాగ్రామ్
- **బ్రెయిన్**: జరుగుతున్నప్పుడే రీజనింగ్ మరియు tool-call ఈవెంట్ స్ట్రీమ్
- **కాంటెక్స్ట్ బ్లోఅవుట్**: ప్రొవైడర్ వారీగా సైజ్ చేయబడిన విండో యుటిలైజేషన్, compaction vs forced overflow, ప్లస్ మనం *చూడలేనిది* ఏమిటో రన్‌టైమ్ వారీ మ్యాప్ ([ఎలా](docs/CONTEXT_BLOWOUT.md))
- **మెమరీ & స్కిల్స్**: ప్రతి రన్‌టైమ్ నిజంగా లోడ్ చేసిన ఫైళ్లు మరియు స్కిల్స్
- **హెల్త్ & లాగ్స్**: డిస్క్, మెమరీ, ఎర్రర్ రేట్లు, రేట్ లిమిట్స్, లైవ్ లాగ్ స్ట్రీమ్
- **అలర్ట్స్**: బడ్జెట్ క్యాప్‌లు, ఎర్రర్ స్పైక్‌లు, ఏజెంట్-ఆఫ్‌లైన్, Slack, Discord, PagerDuty, Telegram, Emailకు రూట్ చేయబడతాయి
- **అప్రూవల్స్**: ప్రమాదకరమైన tool calls *రన్ అవడానికి ముందే* పాజ్ చేయండి మరియు మీ ఫోన్ నుండి ఆమోదించండి ([ఎలా](docs/APPROVALS.md))

## కాంటెక్స్ట్ బ్లోఅవుట్, మరియు గమనించడం వల్ల ఖర్చు ఏమిటి

ఏదైనా agent-comparison టూల్‌ను నమ్మే ముందు సమాధానం చెప్పాల్సిన రెండు ప్రశ్నలు.

**రన్‌టైమ్‌ల మధ్య context-window బ్లోఅవుట్‌ను ఇది ఎలా హ్యాండిల్ చేస్తుంది?**

utilization percentage అనేది అది దేనితో భాగించబడిందో అంతే నిజాయితీగా ఉంటుంది. ClawMetry [మీరు చదవగలిగే మరియు PR చేయగలిగే టేబుల్](clawmetry/context_windows.py) నుండి ప్రొవైడర్ వారీగా విండోను సైజ్ చేస్తుంది, ఇది Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama మరియు GLMను కవర్ చేస్తుంది. ఇది 31 రన్‌టైమ్‌లనూ ఒకే వెండర్ కొలమానంతో కొలవదు. ఇది ముఖ్యమైనది: 300K GPT-5 టర్న్‌ను Anthropic యొక్క 200K తో పోల్చి స్కోర్ చేస్తే, అది నిజంగా GPT-5 యొక్క 400Kలో 75% వద్ద ఉన్నా ">100%, బ్లోన్" అని చదవబడుతుంది. అదే కొలమానం నిజంగా overflow అయిన 130K DeepSeek టర్న్‌ను హాయిగా ఉన్న 65%గా దాచేస్తుంది.

ప్రతి విండో దాని provenance తో వస్తుంది: `model_table`, `explicit_marker`, `observed_floor`, లేదా మనకు మోడల్ తెలియనప్పుడు నిజాయితీగా `default`. ఊహపై నిర్మించిన గేజ్ ఎప్పుడూ lookup పై నిర్మించినంత అధికారంతో రెండర్ కాదు.

కొన్ని రన్‌టైమ్‌లలో మాత్రమే ClawMetry compaction ఈవెంట్‌లను చూడగలదు. కాబట్టి `GET /api/context-coverage` ప్రతి రన్‌టైమ్ కోసం, **సున్నా అంటే "క్లీన్‌గా రన్ అయింది" అని అర్థమా లేదా "మేము గుడ్డిగా ఉన్నాం" అని అర్థమా** అని రిపోర్ట్ చేస్తుంది. నిజంగా గుడ్డిగా ఉన్నట్లు అర్థం వచ్చే `0` అలాగే చెబుతుంది. [పూర్తి వివరాలు](docs/CONTEXT_BLOWOUT.md)

**ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఎంత?**

| పాత్ | మీ ఏజెంట్‌కు జోడించబడింది | డిఫాల్ట్‌గా? |
|---|---|---|
| Session-file tailing (అన్ని 31 రన్‌టైమ్‌లు) | **0**. వేరే ప్రాసెస్, మీ ఏజెంట్‌లో ClawMetry కోడ్ ఏమీ ఉండదు | ఆన్ |
| HTTP ఇంటర్‌సెప్టర్ (`CLAWMETRY_INTERCEPT=1`) | ప్రతి LLM కాల్‌కు **+0.44 ms**, అంటే 5s కాల్‌లో 0.009% | ఆఫ్ |
| Pre-tool hook గేట్ (warm cache) | 36 ms ఇంటర్‌ప్రెటర్ ఫ్లోర్ మీద, గేటెడ్ tool call కు **+44 ms** | ఆఫ్ |
| ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీ | ప్రతి LLM కాల్‌కు **+9.7 ms** | ఆఫ్ |

డెమోన్ హోస్ట్ ఖర్చు: **2,762 events/sec** ingest, డిస్క్ మీద **710 bytes/event** (100k ఈవెంట్లకు 67.7 MB), మరియు బిజీ ఇన్‌స్టాల్‌పై నిరంతరంగా **ఒక కోర్‌లో ~12%**. చివరిది మేము ప్రకటించిన 5-10% బడ్జెట్‌ను మించినది, కాబట్టి దాన్ని పేజీ నుండి తీసివేయడం కంటే వెంబడించాల్సిన బగ్‌గా ప్రచురించాం.

Apple M2 Pro పై `benchmarks/overhead.py` తో కొలవబడింది. ఈ హార్నెస్ ప్రతి కండిషన్‌ను వేరే ప్రాసెస్‌లో రన్ చేస్తుంది, వాటి క్రమాన్ని మార్చుతుంది, మరియు **రౌండ్లు దాని సంకేతం (sign) పై ఏకీభవించనప్పుడు నంబర్‌ను ప్రింట్ చేయడానికి నిరాకరిస్తుంది**. దాన్ని మీ సొంత మెషీన్‌పై ఒక నిమిషంలో రన్ చేయండి:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

hook గేట్లు మరియు ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీతో సహా ప్రతి పాత్ కొలవబడింది, మరియు హార్నెస్ CIలో Linux, macOS మరియు Windowsపై రన్ అవుతుంది. తెలుసుకోవలసిన రెండు ఫలితాలు: ప్రాక్సీ Linux కంటే Windowsపై దాదాపు ఏడు రెట్లు ఎక్కువ ఖర్చు అవుతుంది, మరియు డెమోన్ ప్రస్తుతం మా స్వంత 5-10% బడ్జెట్‌ను మించి ఒక కోర్‌లో దాదాపు 12%ను నిరంతరం వినియోగిస్తుంది. రా JSON, పద్ధతి, మరియు ఇంకా కొలవని అంశాలు [docs/OVERHEAD.md](docs/OVERHEAD.md)లో ఉన్నాయి.

## ధరలు

| ప్లాన్ | ఇది ఏం కవర్ చేస్తుంది | ధర |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, పూర్తి డాష్‌బోర్డ్, లోకల్ మాత్రమే | $0 |
| **Starter** | పైన ఉన్న ప్రతి ఇతర రన్‌టైమ్, ఫ్లీట్ వ్యూ, క్లౌడ్ సింక్ | నోడ్‌కు నెలకు $9 |
| **Pro** | Starter + నియంత్రణ మరియు మూల్యాంకనం: అప్రూవల్స్, tool-risk పాలసీలు, evals, అనోమలీ డిటెక్షన్, కాస్ట్ ఆప్టిమైజర్, OTel export, tamper-evident ఆడిట్ లాగ్ | నోడ్‌కు నెలకు $19 |

వార్షిక ప్లాన్‌లు, Enterprise మరియు ప్రస్తుత నంబర్లు
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** వద్ద ఉన్నాయి. సెల్ఫ్-హోస్టెడ్ లైసెన్స్
కీలు క్లౌడ్ లేకుండా పనిచేస్తాయి (`clawmetry license`). ఖచ్చితమైన free/paid విభజన
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)లో ఉంది.

## మీ డేటా మీ మెషీన్‌లోనే ఉంటుంది

ClawMetry లోకల్ సెషన్ ఫైళ్లు మరియు లాగ్‌లను చదువుతుంది. **మీరు `clawmetry connect` రన్ చేయకపోతే మీ బాక్స్ నుండి ఎలాంటి సెషన్ డేటా బయటికి వెళ్లదు** — ప్రాంప్ట్‌లు, రిప్లైలు, tool arguments, ఫైల్ కంటెంట్ లేదా లాగ్ లైన్లు ఏవీ కాదు. మీరు కనెక్ట్ చేసినప్పుడు, స్నాప్‌షాట్ ఎప్పుడూ మీ మెషీన్ నుండి బయటికి వెళ్లని కీతో end-to-end encrypt చేయబడుతుంది, మరియు మీ బ్రౌజర్‌లో డిక్రిప్ట్ చేయబడుతుంది. ఒక నోడ్‌కు కీ లేకపోతే, అప్‌లోడ్ ప్లెయిన్‌గా పంపబడకుండా స్కిప్ చేయబడుతుంది, మరియు దీన్ని ఏ సర్వర్ రెస్పాన్స్ కూడా ఆఫ్ చేయలేదు.

మీరు కనెక్ట్ చేయడానికి ముందు డిఫాల్ట్‌గా రెండు విషయాలు రన్ అవుతాయి, రెండూ opt-out చేయదగినవి మరియు సెషన్ డేటాను మోసుకెళ్లనివి: అనామక ఇన్‌స్టాల్ పింగ్ మరియు PyPIకి వ్యతిరేకంగా వెర్షన్ చెక్. డిఫాల్ట్ ఇన్‌స్టాల్ ఒక స్టార్టప్ బ్యానర్ లైన్ కోసం మీ పబ్లిక్ IPని కూడా ఒకసారి లుక్ అప్ చేస్తుంది. ప్రతి గమ్యస్థానం, అది ఏం మోసుకెళుతుంది, దాన్ని ఎలా స్విచ్ ఆఫ్ చేయాలో అన్నీ
[docs/EGRESS.md](docs/EGRESS.md)లో జాబితా చేయబడ్డాయి; సెల్ఫ్-హోస్టెడ్, రీపాయింటెడ్ మరియు ఎయిర్-గ్యాప్డ్ ఇన్‌స్టాల్‌లు ఎలాంటి ఐచ్ఛిక outbound కాల్స్‌నూ చేయవు.

డిక్రిప్షన్ మీ బ్రౌజర్‌లో, మేము మీకు అందించే కోడ్‌లో జరుగుతుంది. అది ఒకప్పుడు ఒక వాగ్దానం మాత్రమే; ఇప్పుడు మీరు దాన్ని తనిఖీ చేయగలిగే విషయం. మీ కీని తాకే ప్రతి లైనూ ఒకే చదవదగిన ఫైల్‌లో ఉంది, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ఇది wheel లోపల షిప్ అవుతుంది మరియు యథాతథంగా అందించబడుతుంది, Subresource Integrity హాష్‌తో పిన్ చేయబడుతుంది. బ్రౌజర్ మేము ప్రచురించినదాన్నే రన్ చేస్తుందని నిర్ధారించుకోవడానికి:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ఇది నిరూపించనిది: ఈ ఫైల్‌ను లోడ్ చేసే పేజీని మేమే అందిస్తాము, కాబట్టి మేము వేరే పేజీని కూడా అందించగలం. Integrity హాష్‌లు మిమ్మల్ని compromise అయిన CDN నుండి రక్షిస్తాయి, వెండర్ నుండి కాదు. మీకు లభించేది ఏమిటంటే, ఏదైనా substitution ఉద్దేశపూర్వకంగా ఉండాలి, పేజీ సోర్స్‌లో కనిపించాలి, మరియు ఎవరైనా fetch చేయగలిగే PyPIలోని ఆర్టిఫ్యాక్ట్ నుండి భిన్నంగా ఉండాలి. సెల్ఫ్-హోస్టింగ్ లేదా లోకల్-ఓన్లీగా ఉండటం ఈ డిపెండెన్సీని పూర్తిగా తొలగిస్తుంది.

## ఇన్‌స్టాల్

```bash
pip install clawmetry     # తర్వాత: clawmetry
```

లేదా ఒన్-లైనర్: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux లేదా Windowsపై Python 3.8+ అవసరం, మరియు అదే మెషీన్‌పై కనీసం ఒక ఏజెంట్ రన్‌టైమ్ ఉండాలి. Docker సూచనలు: [docs/DOCKER.md](docs/DOCKER.md).

లేదా ఏజెంట్‌నే మీ కోసం సెటప్ చేయనివ్వండి. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
స్కిల్ Claude Code, Codex, Cursor, Gemini CLI, Copilot లేదా OpenCodeకు
ClawMetryను ఇన్‌స్టాల్ చేయడం, మెషీన్‌పై ఏజెంట్లు ఏం చేస్తున్నాయో మరియు ఎంత ఖర్చు చేస్తున్నాయో రిపోర్ట్ చేయడం,
అభ్యర్థనపై ఒక సెషన్‌ను ఆపడం, మరియు ప్రమాదకరమైన tool calls‌ను ఆమోదం కోసం నిలిపి ఉంచడం నేర్పిస్తుంది:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## డాక్స్

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ప్రతి అడాప్టర్ ఏం చదువుతుంది, మరియు రన్‌టైమ్‌ను ఎలా జోడించాలి |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | ప్రొవైడర్ వారీ విండోలు, compaction vs overflow, రన్‌టైమ్ వారీ కవరేజ్ |
| [Overhead](docs/OVERHEAD.md) | ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఏమిటో, కొలవబడింది, దాన్ని రిప్రొడ్యూస్ చేసే హార్నెస్‌తో సహా |
| [Entitlements](docs/ENTITLEMENTS.md) | Free vs paid, tier matrix, లైసెన్స్ CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution గేటింగ్, రిస్క్ స్కోరింగ్, ఫోన్ అప్రూవల్స్ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ఎక్కడికైనా ట్రేస్‌లు ఎక్స్‌పోర్ట్ చేయండి, దేని నుండైనా OTLP ఇన్‌జెస్ట్ చేయండి |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ఎండ్ టు ఎండ్, రన్ చేయదగిన ఉదాహరణలతో సహా |
| [SDK tracking](docs/SDK_TRACKING.md) | మీరు స్వయంగా నిర్మించిన ఏజెంట్ల కోసం కాస్ట్ అట్రిబ్యూషన్ |
| [Chat channels](docs/CHANNELS.md) | ఫ్లోలో చూపించే చాట్ అడాప్టర్లు |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw సెటప్‌లు |
| [Docker](docs/DOCKER.md) | ఇమేజ్, compose, వాల్యూమ్ మౌంట్‌లు |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | లోపల ఇది ఎలా పనిచేస్తుంది; సోర్స్ నుండి రన్ చేయడం |
| [Telemetry](docs/TELEMETRY.md) | అనామక ఇన్‌స్టాల్ మరియు desktop-open పింగ్‌లు, వాటిని ఎలా ఆఫ్ చేయాలి |

## స్క్రీన్‌షాట్‌లు

కింద ఉన్న ప్రతి నంబర్ ఒక నిజమైన మెషీన్ నుండి, read-only గా, ఏమీ సీడ్ చేయకుండా వచ్చినదే.

**ఏదో తప్పు జరిగినప్పుడు ఇది మీకు చెబుతుంది, కేవలం ఏం జరిగిందో మాత్రమే కాదు.**
పైన రెండు అనోమలీ బ్యానర్లు: రోజువారీ సగటు కంటే 7x ఎక్కువ వ్యయం జరుగుతోంది, మరియు 4.2x కాస్ట్ స్పైక్. వాటి కింద, 667 ఇటీవలి సెషన్లలో 324 waste సిగ్నల్‌ను మోస్తున్నాయి, కారణం వారీగా వర్గీకరించబడ్డాయి.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**డబ్బు ఎక్కడికి వెళ్లిందో, ప్రతి విండోలోనూ ఇది మీకు చూపిస్తుంది.**
ఈరోజు $252.47, ఈ వారం $513.15, ఈ నెల $1,312.92, ఒక్కొక్కటి దాని వెనుక ఉన్న టోకెన్‌లతో మరియు మీ సబ్‌స్క్రిప్షన్ ఇప్పటికే ఎంత కవర్ చేస్తుందో దానితో సహా. దాని కింద, రికవర్ చేయదగినదిగా వర్గీకరించబడిన సుమారు $1,128/నెల మరియు cache reuse ద్వారా ఇప్పటికే ఆదా చేసిన $17,256/నెల.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ఒక సందేశం ఎలా సమాధానంగా మారుతుందో ఇది గీస్తుంది.**
లైవ్ ఫ్లో డయాగ్రామ్: మీరు, అది వచ్చిన ఛానెల్, గేట్‌వే, ప్రస్తుతం సమాధానం చెబుతున్న మోడల్, మరియు అది ఉపయోగించిన ప్రతి టూల్. పని వాటి గుండా కదులుతున్నప్పుడు నోడ్‌లు వెలుగుతాయి.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**మెషీన్‌పై ఉన్న ప్రతి ఏజెంట్, ఒకే టేబుల్‌లో.**
అది ఏం రన్ చేస్తుంది, గత 24 గంటల్లో మరియు దాని జీవితకాలంలో దాని ఖర్చు ఎంత, అది చివరిగా ఎప్పుడు కనిపించింది, దాన్ని ఎవరు యజమాని అయ్యి ఉన్నారు, మరియు బిల్‌ను ఒక సబ్‌స్క్రిప్షన్ కవర్ చేస్తుందా. ఇక్కడ 14 ఏజెంట్లు, 3 సెషన్లు పనిచేస్తున్నాయి, 13 నిశ్శబ్దంగా ఉన్నాయి.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ఒక టర్న్ యొక్క సమయం మరియు డబ్బు ఎక్కడికి వెళ్లాయో, టూల్ వారీగా ఇది చూపిస్తుంది.**
ఒక నిజమైన సెషన్ యొక్క ఒక టర్న్: $1.16కి 11.2 నిమిషాల్లో 11 టూల్స్. ప్రతి Bash కాల్ మరియు మోడల్ కాల్‌కు టైమ్‌లైన్‌పై దాని స్వంత బార్ ఉంటుంది, కాబట్టి 4.1 నిమిషాలు రన్ అయిన కమాండ్‌ను, 226ms రన్ అయిన దానితో ఒక్క చూపులోనే వేరు చేయవచ్చు.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ఇది పనిని గ్రేడ్ చేస్తుంది, కేవలం ఖర్చును కాదు.**
ఈ వారం ఒక A గ్రేడ్: 54 టాస్క్‌లు క్లీన్‌గా తిరిగి వచ్చాయి, 2 కఠినమైనవి $48.57 ఖర్చు చేశాయి, మరియు గ్రేడ్ చేయడానికి తగినంత యాక్టివిటీ లేని రన్‌లను విజయాలుగా లెక్కించకుండా వదిలివేయబడ్డాయి. ప్రతి కఠినమైన రన్ దాని ట్రేస్‌కు లింక్ చేయబడింది.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**కాంటెక్స్ట్ విండో ఎందుకు నిండిపోతూనే ఉందో ఇది చూపిస్తుంది.**
తాజా టర్న్‌లో 1M-టోకెన్ విండోలో 715K, 83.3% పీక్, 4 compactions, ఇవన్నీ overflow మీద కాకుండా proactive గా ఫైర్ అయ్యాయి, దాని వెనుక ఉన్న ప్రతి టర్న్ యొక్క utilization తో సహా.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**మీరు ఏమీ కాన్ఫిగర్ చేయకుండానే డిటెక్షన్ నడుస్తుంది.**
బిల్ట్-ఇన్ డిటెక్టర్లు ఇన్‌స్టాల్ నుండే ఆన్‌లో ఉంటాయి: ఏజెంట్ నిశ్శబ్దమైంది, టెలిమెట్రీ ఫీడ్ ఆగిపోయింది, కాస్ట్ స్పైక్, టోకెన్ బర్స్ట్, ఎర్రర్లు పెరుగుతున్నాయి, ఎర్రర్ స్పైక్, బడ్జెట్ థ్రెషోల్డ్, threat signature మ్యాచ్ అయింది, సెక్యూరిటీ టూల్ ఫైండింగ్, సెక్యూరిటీ posture మారింది. మీ సొంత రూల్స్ దీనిపైన ఐచ్ఛికం.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ప్రమాదకరమైన కాల్‌ను నిలిపి ఉంచడం opt-in, మరియు డిఫాల్ట్‌గా ఆఫ్‌లో ఉంటుంది.**
Recursive deletes, force pushes, sudo, secrets, package installs మరియు outbound కాల్స్ ప్రతి దానికీ మీరు ఆన్ చేయగలిగే ఒక రూల్ ఉంటుంది. మీరు అలా చేసేవరకు, ClawMetry గమనిస్తుంది కానీ ఏమీ మార్చదు. ఒకటి ఆన్ అయిన తర్వాత, మ్యాచ్ అయ్యే కాల్స్ ఇక్కడ (లేదా మీ ఫోన్‌లో) approve లేదా deny కోసం వేచి ఉంటాయి.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

మరిన్ని, రన్‌టైమ్ వారీగా: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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

MIT · నిర్మించినవారు [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
