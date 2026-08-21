<!-- i18n-src:dc34072b2955 -->
> తెలుగు translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**మీ ఏజెంట్ ఆలోచించడాన్ని చూడండి.** **23 AI ఏజెంట్ రన్‌టైమ్‌ల** కోసం రియల్-టైమ్ అబ్జర్వబిలిటీ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & మరో 19. మీ మొత్తం ఏజెంట్ ఫ్లీట్ కోసం ఒకే డాష్‌బోర్డ్.

> 🌐 **దీన్ని ఈ భాషల్లో చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒకే కమాండ్. జీరో కాన్ఫిగ్. అన్నింటినీ ఆటోమేటిక్‌గా గుర్తిస్తుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది. జీరో కాన్ఫిగ్: మీ దగ్గర ఇప్పటికే ఉన్న ఏజెంట్ రన్‌టైమ్‌లను ఇది కనుగొంటుంది, వాటిని read-only గా చదువుతుంది, మరియు అవి ఎలా నడుస్తున్నాయో అందులో ఏమీ మార్చదు.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 23 ఏజెంట్ రన్‌టైమ్‌లతో పనిచేస్తుంది

**ఓపెన్ సోర్స్ యాప్‌లో ఉచితం:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**చెల్లింపు ప్లాన్‌లో:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

ప్రతి రన్‌టైమ్‌కు ఒకే డాష్‌బోర్డ్ లభిస్తుంది. అనేకం ఒకేసారి రన్ చేయండి, హెడర్ స్విచర్ ప్రతి ట్యాబ్‌ను వాటిలో ఒకదానికి రీ-స్కోప్ చేస్తుంది.

SDK మీద మీ సొంత ఏజెంట్‌ను నిర్మించారా? ఇంటర్‌సెప్టర్ దాని LLM కాల్స్‌ను కూడా ట్రాక్ చేస్తుంది. చూడండి [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## మీకు ఏం లభిస్తుంది

- **సెషన్‌లు & ట్రాన్స్‌క్రిప్ట్‌లు**: ప్రతి ఏజెంట్ ఏం చేసిందో, టర్న్ బై టర్న్, రీప్లేతో సహా
- **ఖర్చు & టోకెన్‌లు**: రన్‌టైమ్, మోడల్, సెషన్ మరియు రోజు వారీగా, అనోమలీ ఫ్లాగ్‌లతో సహా
- **ఫ్లో**: ఛానెల్‌లు, మోడల్‌లు మరియు టూల్స్ మధ్య కదిలే మెసేజ్‌ల లైవ్ డయాగ్రామ్
- **బ్రెయిన్**: జరుగుతున్న సమయంలోనే రీజనింగ్ మరియు టూల్-కాల్ ఈవెంట్ స్ట్రీమ్
- **మెమరీ & స్కిల్స్**: ప్రతి రన్‌టైమ్ నిజంగా లోడ్ చేసిన ఫైల్‌లు మరియు స్కిల్స్
- **హెల్త్ & లాగ్స్**: డిస్క్, మెమరీ, ఎర్రర్ రేట్లు, రేట్ లిమిట్‌లు, లైవ్ లాగ్ స్ట్రీమ్
- **అలర్ట్‌లు**: బడ్జెట్ క్యాప్‌లు, ఎర్రర్ స్పైక్‌లు, ఏజెంట్-ఆఫ్‌లైన్, Slack, Discord, PagerDuty, Telegram, Email కు రూట్ చేయబడతాయి
- **ఆమోదాలు**: రిస్కీ టూల్ కాల్స్‌ను అవి రన్ అయ్యే *ముందే* పాజ్ చేసి, మీ ఫోన్ నుండి ఆమోదించండి ([ఎలా](docs/APPROVALS.md))

## ధరల విధానం

| ప్లాన్ | ఇందులో ఏముంది | ధర |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw, పూర్తి డాష్‌బోర్డ్, లోకల్ మాత్రమే | $0 |
| **Starter** | పైన పేర్కొన్న ప్రతి ఇతర రన్‌టైమ్, ఫ్లీట్ వ్యూ, క్లౌడ్ సింక్ | నెలకు నోడ్‌కు $9 |
| **Pro** | Starter + గవర్నెన్స్: ఆమోదాలు, టూల్-రిస్క్ పాలసీలు, ఎవాల్స్, అనోమలీ డిటెక్షన్, కాస్ట్ ఆప్టిమైజర్, OTel ఎక్స్‌పోర్ట్ | నెలకు నోడ్‌కు $19 |

వార్షిక ప్లాన్‌లు, Enterprise మరియు ప్రస్తుత అంకెలు
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** వద్ద ఉన్నాయి. సెల్ఫ్-హోస్టెడ్ లైసెన్స్
కీలు క్లౌడ్ లేకుండా పనిచేస్తాయి (`clawmetry license`). ఖచ్చితమైన ఉచిత/చెల్లింపు విభజన
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) లో ఉంది.

## మీ డేటా మీ మెషీన్‌లోనే ఉంటుంది

ClawMetry లోకల్ సెషన్ ఫైల్‌లు మరియు లాగ్‌లను చదువుతుంది. మీరు `clawmetry connect` రన్ చేయనంత
వరకు మీ బాక్స్ నుండి ఏమీ బయటకు వెళ్లదు. అప్పుడు కూడా స్నాప్‌షాట్ మీ మెషీన్‌ను ఎప్పుడూ
వదిలిపెట్టని కీతో ఎండ్-టు-ఎండ్ ఎన్‌క్రిప్ట్ చేయబడుతుంది మరియు మీ బ్రౌజర్‌లో డిక్రిప్ట్ చేయబడుతుంది.

## ఇన్‌స్టాల్

```bash
pip install clawmetry     # తర్వాత: clawmetry
```

లేదా ఒకే లైన్: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux లేదా Windows లో Python 3.8+ అవసరం, మరియు అదే మెషీన్‌లో కనీసం ఒక ఏజెంట్
రన్‌టైమ్ ఉండాలి. Docker సూచనలు: [docs/DOCKER.md](docs/DOCKER.md).

## డాక్యుమెంటేషన్

| | |
|---|---|
| [రన్‌టైమ్ కంపాటిబిలిటీ](docs/compatibility.md) | ప్రతి అడాప్టర్ ఏం చదువుతుంది, మరియు రన్‌టైమ్‌ను ఎలా జోడించాలి |
| [ఎంటైటిల్‌మెంట్స్](docs/ENTITLEMENTS.md) | ఉచితం vs చెల్లింపు, టైర్ మ్యాట్రిక్స్, లైసెన్స్ CLI |
| [ఆమోదాలు & పాలసీలు](docs/APPROVALS.md) | ప్రీ-ఎగ్జిక్యూషన్ గేటింగ్, రిస్క్ స్కోరింగ్, ఫోన్ ఆమోదాలు |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ఎక్కడికైనా ట్రేసులు ఎక్స్‌పోర్ట్ చేయండి, ఎక్కడి నుండైనా OTLP ఇన్జెస్ట్ చేయండి |
| [SDK ట్రాకింగ్](docs/SDK_TRACKING.md) | మీరే నిర్మించిన ఏజెంట్‌ల కోసం ఖర్చు అట్రిబ్యూషన్ |
| [చాట్ ఛానెల్స్](docs/CHANNELS.md) | ఫ్లోలో చూపించే చాట్ అడాప్టర్లు |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | సాండ్‌బాక్స్డ్ NVIDIA NemoClaw సెటప్‌లు |
| [Docker](docs/DOCKER.md) | ఇమేజ్, కంపోజ్, వాల్యూమ్ మౌంట్‌లు |
| [ఆర్కిటెక్చర్](ARCHITECTURE.md) · [డెవలప్‌మెంట్](docs/DEVELOPMENT.md) | ఇది లోపల ఎలా పనిచేస్తుంది; సోర్స్ నుండి రన్ చేయడం |
| [టెలిమెట్రీ](docs/TELEMETRY.md) | అనామక ఇన్‌స్టాల్ మరియు డెస్క్‌టాప్-ఓపెన్ పింగ్‌లు, వాటిని ఎలా ఆపేయాలి |

## స్క్రీన్‌షాట్‌లు

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **అవలోకనం**: టోకెన్‌లు, సెషన్‌లు, హెల్త్ | **బ్రెయిన్**: లైవ్ ఏజెంట్ ఈవెంట్ స్ట్రీమ్ |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **ఖర్చు**: మోడల్ మరియు సెషన్ వారీగా | **ఆమోదాలు**: రిస్కీ టూల్ కాల్స్‌ను గేట్ చేయడం |

మరిన్ని, రన్‌టైమ్ వారీగా: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star చరిత్ర

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
