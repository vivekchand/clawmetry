<!-- i18n-src:a855a14295b0 -->
> తెలుగు translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ఒక ఏజెంట్ ఎలాంటి పురోగతి లేకుండానే వందల టూల్ కాల్స్ చేయగలదు.** ClawMetry
మీ కోడింగ్ ఏజెంట్లు ఇప్పటికే రాస్తున్న సెషన్ ఫైళ్లను చదివి, టైమ్‌లైన్,
టూల్ కాల్స్, మరియు రన్‌టైమ్ అందించే టోకెన్ మరియు ఖర్చు డేటాను ఒకే
వీక్షణలో పెడుతుంది — తద్వారా పని జరుగుతున్న సుదీర్ఘ రన్‌ను, ఎక్కడో ఆగిపోయిన
దానితో పోల్చి మీరు గుర్తించగలరు.

**32 AI ఏజెంట్ రన్‌టైమ్‌లతో** పనిచేస్తుంది — Claude Code, OpenAI Codex, Hermes, OpenClaw & మరో 28. మీ మొత్తం ఏజెంట్ ఫ్లీట్‌కు ఒకే డాష్‌బోర్డ్. ([పూర్తి జాబితా](SUPPORTED_RUNTIMES.txt), కేటలాగ్ నుండి జనరేట్ చేయబడింది.)

> 🌐 **దీన్ని ఈ భాషలో చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒకే కమాండ్. జీరో కాన్ఫిగ్. అన్నింటినీ ఆటోమేటిక్‌గా గుర్తిస్తుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది. జీరో కాన్ఫిగ్: ఇది మీ దగ్గర
ఇప్పటికే ఉన్న ఏజెంట్ రన్‌టైమ్‌లను కనుగొని, వాటిని రీడ్-ఓన్లీగా చదువుతుంది, అవి
ఎలా నడుస్తున్నాయో దానిలో ఏమీ మార్చదు.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ఇన్‌స్టాల్ చేయడానికి ముందు

| | |
|---|---|
| **ఇది ఏం చేస్తుంది** | మీ ఏజెంట్లు ఇప్పటికే రాస్తున్న సెషన్ ఫైళ్లు, లాగ్‌లను చదువుతుంది. SDK లేదు, కోడ్ మార్పు లేదు, మీ యాప్‌లో ఇన్‌స్ట్రుమెంటేషన్ లేదు. |
| **మీరు చూసేది** | సెషన్ టైమ్‌లైన్, టూల్-బై-టూల్ రీప్లే, టోకెన్ మరియు ఖర్చు విభజన, మరియు ట్రాజెక్టరీ సిగ్నల్స్ (లూపింగ్, పదే పదే వైఫల్యాలు) — ప్రతి రన్‌టైమ్ కోసం. |
| **ఏది ఉచితం** | `pip install clawmetry` ఖాతా, కీ లేదా నెట్‌వర్క్ కాల్ లేకుండా **OpenClaw, NVIDIA NemoClaw మరియు Goose**ను చదువుతుంది. మిగతా 27 — Claude Code, Codex, Cursor మరియు మిగతావి — క్లోజ్డ్-సోర్స్ `clawmetry-pro` కంపానియన్ ద్వారా చదవబడతాయి, ఇది 7-రోజుల ట్రయల్ లేదా ప్లాన్‌తో వస్తుంది — ఖచ్చితమైన విభజన కోసం [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) చూడండి. |
| **ఎలా ప్రారంభించాలి** | `pip install clawmetry && clawmetry`, తర్వాత localhost:8900 తెరవండి. ఈ మెషీన్‌పై ఇంకా ఏజెంట్లు లేవా? `clawmetry --sample` మూడు లేబుల్ చేయబడిన సింథటిక్ సెషన్లతో తెరుచుకుంటుంది. |
| **మీ మెషీన్ నుండి ఏమి బయటకు వెళుతుంది** | మీరు `clawmetry connect` రన్ చేయకపోతే, ఎలాంటి సెషన్ డేటా బయటకు వెళ్లదు. డిఫాల్ట్‌గా రెండు విషయాలు మాత్రమే జరుగుతాయి, రెండూ ఆప్ట్-అవుట్ చేయదగినవి మరియు వేటిలోనూ సెషన్ కంటెంట్ ఉండదు: అనామక ఇన్‌స్టాల్ పింగ్ మరియు PyPI వెర్షన్ చెక్. ప్రతి గమ్యస్థానం కామెంట్‌లు చదవడం ద్వారా కాకుండా వైర్ క్యాప్చర్ నుండి తిరిగి నిర్మించి [docs/EGRESS.md](docs/EGRESS.md)లో జాబితా చేయబడింది. |

మీరు అవుట్‌పుట్‌ను తీర్పు తీర్చే ముందు తెలుసుకోవాల్సిన రెండు పరిమితులు ఉన్నాయి:
రన్‌టైమ్‌లు చాలా వేర్వేరు డేటాను అందిస్తాయి (కొన్ని ఎలాంటి ఖర్చు ప్రచురించవు —
[ఏ రన్‌టైమ్ ఏమి చేస్తుందో మ్యాట్రిక్స్](docs/compatibility.md) చెబుతుంది), మరియు
ఒక చర్యను గమనించడం అంటే దానిని ఆపగలగడం కాదు
([ఏ కంట్రోల్స్ నిజమైనవో, ప్రతి రన్‌టైమ్ ప్రకారం](docs/APPROVALS.md)).


## 32 ఏజెంట్ రన్‌టైమ్‌లతో పనిచేస్తుంది

**ఓపెన్ సోర్స్ యాప్‌లో ఉచితం:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**చెల్లింపు ప్లాన్‌లో:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ప్రతి రన్‌టైమ్‌కు ఒకే డాష్‌బోర్డ్ లభిస్తుంది. ఒకేసారి అనేకం రన్ చేయండి, హెడర్
స్విచర్ ప్రతి ట్యాబ్‌నూ వాటిలో ఒకదానికి తిరిగి స్కోప్ చేస్తుంది.

SDKలో మీ సొంత ఏజెంట్‌ను నిర్మించారా? ఇంటర్‌సెప్టర్ దాని LLM కాల్స్‌ను కూడా
ట్రాక్ చేస్తుంది. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) చూడండి.

## మీకు ఏమి లభిస్తుంది

- **సెషన్లు & ట్రాన్‌స్క్రిప్ట్‌లు**: ప్రతి ఏజెంట్ ఏమి చేసిందో, టర్న్ బై టర్న్, రీప్లేతో సహా
- **ఖర్చు & టోకెన్లు**: ప్రతి రన్‌టైమ్, మోడల్, సెషన్ మరియు రోజుకు, అనోమలీ ఫ్లాగ్‌లతో
- **ఫ్లో**: ఛానెళ్లు, మోడల్స్ మరియు టూల్స్ ద్వారా కదులుతున్న మెసేజ్‌ల లైవ్ డయాగ్రామ్
- **బ్రెయిన్**: రీజనింగ్ మరియు టూల్-కాల్ ఈవెంట్ స్ట్రీమ్ జరుగుతున్నప్పుడే
- **కాంటెక్స్ట్ బ్లోఅవుట్**: ప్రొవైడర్ ప్రకారం విండో వినియోగం, కంపాక్షన్ vs ఫోర్స్డ్ ఓవర్‌ఫ్లో, అలాగే మనం *చూడలేని* దాని రన్‌టైమ్-వారీ మ్యాప్ ([ఎలా](docs/CONTEXT_BLOWOUT.md))
- **మెమరీ & స్కిల్స్**: ప్రతి రన్‌టైమ్ నిజంగా లోడ్ చేసిన ఫైళ్లు మరియు స్కిల్స్
- **హెల్త్ & లాగ్స్**: డిస్క్, మెమరీ, ఎర్రర్ రేట్లు, రేట్ లిమిట్స్, లైవ్ లాగ్ స్ట్రీమ్
- **అలర్ట్‌లు**: బడ్జెట్ క్యాప్‌లు, ఎర్రర్ స్పైక్‌లు, ఏజెంట్-ఆఫ్‌లైన్, Slack, Discord, PagerDuty, Telegram, Emailకు రూట్ చేయబడతాయి
- **ఆమోదాలు**: రిస్కీ టూల్ కాల్స్‌ను అవి రన్ అవ్వక *ముందే* పాజ్ చేసి మీ ఫోన్ నుండి ఆమోదించండి ([ఎలా](docs/APPROVALS.md))

## కాంటెక్స్ట్ బ్లోఅవుట్, మరియు గమనించడం వల్ల ఖర్చు ఎంత

రన్‌టైమ్‌ల మధ్య పోల్చే ఏ ఏజెంట్ టూల్‌నైనా నమ్మే ముందు రెండు ప్రశ్నలకు
సమాధానం విలువైనది.

**కాంటెక్స్ట్-విండో బ్లోఅవుట్‌ను రన్‌టైమ్‌ల వ్యాప్తంగా ఇది ఎలా నిర్వహిస్తుంది?**

వినియోగ శాతం అది దేనితో భాగించబడిందో దానంత నిజాయితీగా ఉంటుంది. ClawMetry
Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama మరియు
GLMలను కవర్ చేస్తూ, మీరు చదవగలిగే మరియు PR చేయగలిగే [ఒక పట్టిక](clawmetry/context_windows.py)
నుండి ప్రొవైడర్ ప్రకారం విండోను సైజ్ చేస్తుంది. ఇది 32 రన్‌టైమ్‌లనూ ఒకే
వెండర్ కొలబద్దతో కొలవదు. అది ముఖ్యం: Anthropic యొక్క 200Kకు వ్యతిరేకంగా
స్కోర్ చేయబడిన 300K GPT-5 టర్న్, GPT-5 యొక్క 400Kలో నిజంగా 75% వద్ద
ఉన్నప్పటికీ ">100%, బ్లోన్" అని చదవబడుతుంది. అదే కొలబద్ద నిజంగా ఓవర్‌ఫ్లో
అయిన 130K DeepSeek టర్న్‌ను సౌకర్యవంతమైన 65%గా దాచిపెడుతుంది.

ప్రతి విండో దాని మూలాన్ని కూడా షిప్ చేస్తుంది: `model_table`, `explicit_marker`,
`observed_floor`, లేదా మనకు మోడల్ తెలియనప్పుడు నిజాయితీగా ఉండే `default`.
ఊహపై నిర్మించబడిన గేజ్, లుకప్‌పై నిర్మించబడిన దానితో ఎప్పుడూ అదే అధికారంతో
రెండర్ కాదు.

కొన్ని రన్‌టైమ్‌లపై మాత్రమే ClawMetry కంపాక్షన్ ఈవెంట్‌లను చూడగలదు. అందుకే
`GET /api/context-coverage` ప్రతి రన్‌టైమ్ కోసం, **జీరో అంటే "క్లీన్‌గా
రన్ అయింది" అని అర్థమా లేదా "మనం అంధులమా"** అని నివేదిస్తుంది. నిజంగా
అంధత్వాన్ని సూచించే `0` అలానే చెబుతుంది.
[పూర్తి వివరాలు](docs/CONTEXT_BLOWOUT.md)

**ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఎంత?**

| పాత్ | మీ ఏజెంట్‌కు జోడించబడింది | డిఫాల్ట్‌గా? |
|---|---|---|
| సెషన్-ఫైల్ టెయిలింగ్ (అన్ని 32 రన్‌టైమ్‌లు) | **0**. ప్రత్యేక ప్రాసెస్, మీ ఏజెంట్‌లో ClawMetry కోడ్ లేదు | ఆన్ |
| HTTP ఇంటర్‌సెప్టర్ (`CLAWMETRY_INTERCEPT=1`) | ప్రతి LLM కాల్‌కు **+0.44 ms**, లేదా 5s కాల్‌లో 0.009% | ఆఫ్ |
| ప్రీ-టూల్ హుక్ గేట్ (వార్మ్ క్యాష్) | 36 ms ఇంటర్‌ప్రిటర్ ఫ్లోర్‌పై, ప్రతి గేటెడ్ టూల్ కాల్‌కు **+44 ms** | ఆఫ్ |
| ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీ | ప్రతి LLM కాల్‌కు **+9.7 ms** | ఆఫ్ |

డెమోన్ హోస్ట్ ఖర్చు: **2,762 events/sec** ఇన్‌జెస్ట్, డిస్క్‌పై **710
bytes/event** (100k ఈవెంట్‌లకు 67.7 MB), మరియు బిజీ ఇన్‌స్టాల్‌పై నిరంతరంగా
**~12% ఆఫ్ వన్ కోర్**. ఆ చివరి సంఖ్య మన స్వంత 5-10% బడ్జెట్‌ను మించిపోయింది,
కాబట్టి పేజీ నుండి తీసివేయడం కంటే వెంబడించాల్సిన బగ్‌గా ప్రచురించబడింది.

Apple M2 Proపై `benchmarks/overhead.py`తో కొలవబడింది. హార్నెస్ ప్రతి
కండిషన్‌ను ప్రత్యేక ప్రాసెస్‌లో రన్ చేస్తుంది, వాటి క్రమాన్ని మార్చుతుంది,
మరియు **రౌండ్‌లు దాని సంకేతంపై విభేదిస్తే సంఖ్యను ప్రింట్ చేయడానికి
నిరాకరిస్తుంది**. దీన్ని మీ సొంత మెషీన్‌పై ఒక నిమిషంలో రన్ చేయండి:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

హుక్ గేట్లు మరియు ఎన్‌ఫోర్స్‌మెంట్ ప్రాక్సీతో సహా ప్రతి పాత్ కొలవబడుతుంది,
మరియు హార్నెస్ CIలో Linux, macOS మరియు Windowsపై రన్ అవుతుంది. తెలుసుకోవాల్సిన
రెండు ఫలితాలు: Windowsపై ప్రాక్సీ Linux కంటే దాదాపు ఏడు రెట్లు ఎక్కువ
ఖర్చవుతుంది, మరియు డెమోన్ ప్రస్తుతం మన స్వంత 5-10% బడ్జెట్‌పై, ఒక కోర్‌లో
సుమారు 12%ను నిరంతరంగా ఉపయోగిస్తుంది. రా JSON, పద్ధతి, మరియు ఇంకా
కొలవని విషయాలు [docs/OVERHEAD.md](docs/OVERHEAD.md)లో ఉన్నాయి.

## ధరలు

| ప్లాన్ | ఏమి కవర్ చేస్తుంది | ధర |
|---|---|---|
| **ఉచితం** | OpenClaw + NVIDIA NemoClaw + Goose, పూర్తి డాష్‌బోర్డ్, లోకల్ మాత్రమే | $0 |
| **స్టార్టర్** | పైన ఉన్న ప్రతి ఇతర రన్‌టైమ్, ఫ్లీట్ వ్యూ, క్లౌడ్ సింక్ | నోడ్‌కు $9 / నెలకు |
| **Pro** | స్టార్టర్ + కంట్రోల్ మరియు మూల్యాంకనం: ఆమోదాలు, టూల్-రిస్క్ పాలసీలు, ఎవాల్స్, అనోమలీ డిటెక్షన్, కాస్ట్ ఆప్టిమైజర్, OTel ఎక్స్‌పోర్ట్, టాంపర్-ఎవిడెంట్ ఆడిట్ లాగ్ | నోడ్‌కు $19 / నెలకు |

వార్షిక ప్లాన్‌లు, ఎంటర్‌ప్రైజ్ మరియు ప్రస్తుత సంఖ్యలు
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** వద్ద ఉన్నాయి.
సెల్ఫ్-హోస్టెడ్ లైసెన్స్ కీలు క్లౌడ్ లేకుండా పనిచేస్తాయి (`clawmetry
license`). ఖచ్చితమైన ఉచిత/చెల్లింపు విభజన
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)లో ఉంది.

## మీ డేటా మీ మెషీన్‌లోనే ఉంటుంది

ClawMetry లోకల్ సెషన్ ఫైళ్లు మరియు లాగ్‌లను చదువుతుంది. **మీరు `clawmetry
connect` రన్ చేయకపోతే మీ బాక్స్ నుండి ఎలాంటి సెషన్ డేటా బయటకు వెళ్లదు** —
ప్రాంప్ట్‌లు, రిప్లైలు, టూల్ ఆర్గ్యుమెంట్‌లు, ఫైల్ కంటెంట్‌లు లేదా లాగ్
లైన్‌లు కూడా కాదు. మీరు కనెక్ట్ చేసినప్పుడు, స్నాప్‌షాట్ మీ మెషీన్ నుండి
ఎప్పుడూ బయటకు వెళ్లని కీతో ఎండ్-టు-ఎండ్ ఎన్‌క్రిప్ట్ చేయబడుతుంది, మరియు మీ
బ్రౌజర్‌లో డిక్రిప్ట్ చేయబడుతుంది. ఒక నోడ్‌కు కీ లేకపోతే, అప్‌లోడ్
ప్లెయిన్‌గా పంపబడకుండా స్కిప్ చేయబడుతుంది, మరియు ఏ సర్వర్ రెస్పాన్స్ కూడా
దాన్ని ఆఫ్ చేయలేదు.

మీరు కనెక్ట్ చేయడానికి ముందు రెండు విషయాలు డిఫాల్ట్‌గా జరుగుతాయి, రెండూ
ఆప్ట్-అవుట్ చేయదగినవి మరియు వేటిలోనూ సెషన్ డేటా ఉండదు: అనామక ఇన్‌స్టాల్
పింగ్ మరియు PyPIకి వ్యతిరేకంగా వెర్షన్ చెక్. డిఫాల్ట్ ఇన్‌స్టాల్ కూడా
స్టార్టప్ బ్యానర్ లైన్ కోసం మీ పబ్లిక్ IPని ఒకసారి లుక్ అప్ చేస్తుంది.
ప్రతి గమ్యస్థానం, అది ఏమి కలిగి ఉంది మరియు దాన్ని ఎలా ఆఫ్ చేయాలో
[docs/EGRESS.md](docs/EGRESS.md)లో జాబితా చేయబడింది; సెల్ఫ్-హోస్టెడ్,
రీపాయింటెడ్ మరియు ఎయిర్-గ్యాప్డ్ ఇన్‌స్టాల్‌లు ఎలాంటి విచక్షణాధికార
అవుట్‌బౌండ్ కాల్స్ చేయవు.

డిక్రిప్షన్ మీ బ్రౌజర్‌లో, మేము మీకు అందించే కోడ్‌లో జరుగుతుంది. అది ఒకప్పుడు
ఒక వాగ్దానం; ఇప్పుడు మీరు తనిఖీ చేయగల విషయం. మీ కీని తాకే ప్రతి లైన్ ఒకే
చదవగలిగే ఫైల్‌లో ఉంది,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), అది వీల్
లోపల షిప్ అవుతుంది మరియు సబ్‌రిసోర్స్ ఇంటిగ్రిటీ హాష్‌తో పిన్ చేయబడి
యథాతథంగా అందించబడుతుంది. బ్రౌజర్ మేము ప్రచురించిన దాన్నే రన్ చేస్తుందని
నిర్ధారించడానికి:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

అది ఏమి నిరూపించదు: ఫైల్‌ను లోడ్ చేసే పేజీని మేమే అందిస్తాము, కాబట్టి మేము
వేరే పేజీని అందించగలుగుతాము. ఇంటిగ్రిటీ హాష్‌లు మిమ్మల్ని రాజీపడిన CDN
నుండి రక్షిస్తాయి, వెండర్ నుండి కాదు. మీకు లభించేది ఏమిటంటే, ఏదైనా
ప్రత్యామ్నాయం ఉద్దేశపూర్వకంగా, పేజీ సోర్స్‌లో కనిపించేలా, మరియు ఎవరైనా
తీసుకోగలిగే PyPI ఆర్టిఫ్యాక్ట్ నుండి భిన్నంగా ఉండాలి. సెల్ఫ్-హోస్టింగ్
లేదా లోకల్-ఓన్లీగా ఉండటం ఈ ఆధారపడటాన్ని పూర్తిగా తొలగిస్తుంది.

## ఇన్‌స్టాల్ చేయడం

```bash
pip install clawmetry     # తర్వాత: clawmetry
```

లేదా వన్-లైనర్: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux లేదా Windowsపై Python 3.8+ అవసరం, మరియు అదే మెషీన్‌పై కనీసం
ఒక ఏజెంట్ రన్‌టైమ్ ఉండాలి. Docker సూచనలు: [docs/DOCKER.md](docs/DOCKER.md).

లేదా ఏజెంట్‌నే మీ కోసం సెటప్ చేయనివ్వండి.
[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) స్కిల్ Claude Code,
Codex, Cursor, Gemini CLI, Copilot లేదా OpenCodeకు ClawMetryను
ఇన్‌స్టాల్ చేయడం, మెషీన్‌పై ఏజెంట్‌లు ఏమి చేస్తున్నాయో మరియు ఎంత ఖర్చు
చేస్తున్నాయో నివేదించడం, అభ్యర్థనపై ఒక సెషన్‌ను ఆపడం, మరియు రిస్కీ టూల్
కాల్స్‌ను ఆమోదం కోసం ఆపి ఉంచడం నేర్పిస్తుంది:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## డాక్స్

| | |
|---|---|
| [రన్‌టైమ్ కాంపాటిబిలిటీ](docs/compatibility.md) | ప్రతి అడాప్టర్ ఏమి చదువుతుంది, మరియు రన్‌టైమ్‌ను ఎలా జోడించాలి |
| [కాంటెక్స్ట్ బ్లోఅవుట్](docs/CONTEXT_BLOWOUT.md) | ప్రొవైడర్-వారీ విండోలు, కంపాక్షన్ vs ఓవర్‌ఫ్లో, రన్‌టైమ్-వారీ కవరేజ్ |
| [ఓవర్‌హెడ్](docs/OVERHEAD.md) | ఇన్‌స్ట్రుమెంటేషన్ ఖర్చు ఎంత, కొలవబడింది, రిప్రొడ్యూస్ చేయడానికి హార్నెస్‌తో సహా |
| [ఎన్‌టైటిల్‌మెంట్‌లు](docs/ENTITLEMENTS.md) | ఉచితం vs చెల్లింపు, టైర్ మ్యాట్రిక్స్, లైసెన్స్ CLI |
| [ఆమోదాలు & పాలసీలు](docs/APPROVALS.md) | ప్రీ-ఎగ్జిక్యూషన్ గేటింగ్, రిస్క్ స్కోరింగ్, ఫోన్ ఆమోదాలు |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ఎక్కడైనా ట్రేసులను ఎక్స్‌పోర్ట్ చేయండి, ఎక్కడి నుండైనా OTLPను ఇన్‌జెస్ట్ చేయండి |
| [మీ సొంత ఏజెంట్‌ను తీసుకురండి](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ఎండ్ టు ఎండ్, రన్ చేయగల ఉదాహరణలతో |
| [SDK ట్రాకింగ్](docs/SDK_TRACKING.md) | మీరు స్వయంగా నిర్మించిన ఏజెంట్‌ల కోసం ఖర్చు అట్రిబ్యూషన్ |
| [చాట్ ఛానెళ్లు](docs/CHANNELS.md) | Flowలో చూపిన చాట్ అడాప్టర్లు |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | శాండ్‌బాక్స్డ్ NVIDIA NemoClaw సెటప్‌లు |
| [Docker](docs/DOCKER.md) | ఇమేజ్, కంపోజ్, వాల్యూమ్ మౌంట్‌లు |
| [ఆర్కిటెక్చర్](ARCHITECTURE.md) · [డెవలప్‌మెంట్](docs/DEVELOPMENT.md) | ఇది లోపల ఎలా పనిచేస్తుంది; సోర్స్ నుండి రన్ చేయడం |
| [టెలిమెట్రీ](docs/TELEMETRY.md) | అనామక ఇన్‌స్టాల్ మరియు డెస్క్‌టాప్-ఓపెన్ పింగ్‌లు, మరియు వాటిని ఎలా ఆఫ్ చేయాలి |

## స్క్రీన్‌షాట్‌లు

క్రింద ఉన్న ప్రతి సంఖ్య ఒక నిజమైన మెషీన్ నుండి, రీడ్-ఓన్లీగా, దేనినీ
సీడ్ చేయకుండా తీసుకోబడింది.

**ఏదో తప్పు జరిగినప్పుడు ఇది మీకు చెబుతుంది, కేవలం ఏమి జరిగిందో మాత్రమే కాదు.**
పైన రెండు అనోమలీ బ్యానర్‌లు: రోజువారీ సగటు కంటే 7 రెట్లు ఖర్చు, మరియు 4.2x
కాస్ట్ స్పైక్. వాటి క్రింద, ఇటీవలి 667 సెషన్‌లలో 324 వేస్ట్ సిగ్నల్‌ను
కలిగి ఉన్నాయి, కారణం వారీగా వర్గీకరించబడ్డాయి.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**డబ్బు ఎక్కడికి వెళ్లిందో ప్రతి విండోలో ఇది మీకు చూపిస్తుంది.**
ఈరోజు $252.47, ఈ వారం $513.15, ఈ నెల $1,312.92, ప్రతిదానికి వెనుక ఉన్న
టోకెన్‌లు మరియు మీ సబ్‌స్క్రిప్షన్ ఇప్పటికే ఎంత కవర్ చేస్తుందో సహా. దాని
క్రింద, సుమారు $1,128/నెలకు రికవరబుల్‌గా వర్గీకరించబడింది మరియు క్యాష్
రీయూజ్ ద్వారా ఇప్పటికే $17,256/నెలకు ఆదా చేయబడింది.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ఒక మెసేజ్ ఎలా జవాబుగా మారుతుందో ఇది గీస్తుంది.**
లైవ్ ఫ్లో డయాగ్రామ్: మీరు, అది వచ్చిన ఛానెల్, గేట్‌వే, ప్రస్తుతం జవాబిస్తున్న
మోడల్, మరియు అది వినియోగించిన ప్రతి టూల్. పని వాటి గుండా కదులుతున్నప్పుడు
నోడ్‌లు వెలిగిపోతాయి.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**మెషీన్‌పై ఉన్న ప్రతి ఏజెంట్, ఒకే పట్టికలో.**
అది ఏమి రన్ చేస్తుంది, గత 24 గంటల్లో మరియు దాని లైఫ్‌టైమ్‌లో దాని ఖర్చు
ఎంత, అది చివరిసారి ఎప్పుడు కనిపించింది, దానిని ఎవరు కలిగి ఉన్నారు, మరియు
సబ్‌స్క్రిప్షన్ బిల్‌ను కవర్ చేస్తుందా. ఇక్కడ 14 ఏజెంట్‌లు, 3 సెషన్‌లు
పనిచేస్తున్నాయి, 13 నిశ్శబ్దంగా ఉన్నాయి.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ఒక టర్న్ యొక్క సమయం మరియు డబ్బు ఎక్కడికి వెళ్లిందో, టూల్ బై టూల్ ఇది చూపిస్తుంది.**
ఒక నిజమైన సెషన్ యొక్క ఒక టర్న్: 11.2 నిమిషాల్లో $1.16కు 11 టూల్స్. ప్రతి
Bash కాల్ మరియు మోడల్ కాల్‌కు టైమ్‌లైన్‌పై దాని స్వంత బార్ లభిస్తుంది,
కాబట్టి 4.1 నిమిషాలు నడిచిన కమాండ్ మరియు 226ms నడిచిన దానిని ఒక్క
చూపులోనే గుర్తించవచ్చు.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**కేవలం ఖర్చునే కాదు, పనినీ ఇది గ్రేడ్ చేస్తుంది.**
ఈ వారం Aగ్రేడ్: 54 టాస్క్‌లు క్లీన్‌గా తిరిగి వచ్చాయి, 2 కఠినమైనవి $48.57
ఖర్చు చేశాయి, మరియు తీర్పు చెప్పడానికి తగినంత యాక్టివిటీ లేని రన్‌లు
విజయాలుగా లెక్కించబడకుండా గ్రేడ్ నుండి మినహాయించబడ్డాయి. ప్రతి కఠినమైన
రన్ దాని ట్రేస్‌కు లింక్ చేస్తుంది.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**కాంటెక్స్ట్ విండో ఎందుకు నిండిపోతూనే ఉందో ఇది చూపిస్తుంది.**
తాజా టర్న్‌లో 1M-టోకెన్ విండోలో 715K, 83.3% పీక్, ఓవర్‌ఫ్లోపై కాకుండా
అన్నీ ప్రోయాక్టివ్‌గా ఫైర్ అయిన 4 కంపాక్షన్‌లు, మరియు దాని వెనుక ప్రతి
టర్న్ యొక్క వినియోగం.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**మీరు ఏమీ కాన్ఫిగర్ చేయకుండానే డిటెక్షన్ రన్ అవుతుంది.**
ఇన్‌స్టాల్ నుండే బిల్ట్-ఇన్ డిటెక్టర్లు ఆన్‌లో ఉన్నాయి: ఏజెంట్ నిశ్శబ్దమైంది,
టెలిమెట్రీ ఫీడ్ ఆగింది, కాస్ట్ స్పైక్, టోకెన్ బర్స్ట్, పెరుగుతున్న
ఎర్రర్‌లు, ఎర్రర్ స్పైక్, బడ్జెట్ థ్రెషోల్డ్, థ్రెట్ సిగ్నేచర్ మ్యాచ్
అయింది, సెక్యూరిటీ టూల్ ఫైండింగ్, సెక్యూరిటీ పోశ్చర్ మారింది. మీ సొంత
రూల్స్ దీనిపైన ఆప్షనల్‌గా ఉంటాయి.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**రిస్కీ కాల్‌ను ఆపి ఉంచడం ఆప్ట్-ఇన్, మరియు ఆఫ్‌గా షిప్ అవుతుంది.**
రికర్సివ్ డిలీట్‌లు, ఫోర్స్ పుష్‌లు, sudo, సీక్రెట్‌లు, ప్యాకేజీ
ఇన్‌స్టాల్‌లు మరియు అవుట్‌బౌండ్ కాల్‌లు ప్రతిదానికి మీరు ఆన్ చేయగల
రూల్ లభిస్తుంది. మీరు అలా చేసేవరకు, ClawMetry గమనిస్తుంది, ఏమీ
మార్చదు. ఒకటి ఆన్ అయిన తర్వాత, మ్యాచ్ అయిన కాల్స్ ఇక్కడ (లేదా మీ
ఫోన్‌పై) ఆమోదం లేదా తిరస్కరణ కోసం వేచి ఉంటాయి.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

మరిన్ని, రన్‌టైమ్ వారీగా: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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

MIT · [@vivekchand](https://github.com/vivekchand) చే నిర్మించబడింది · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
