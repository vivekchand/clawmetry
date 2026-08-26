<!-- i18n-src:c111f32e69a5 -->
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

**మీ ఏజెంట్ ఆలోచించడం చూడండి.** **26 AI ఏజెంట్ రన్‌టైమ్‌ల**కు రియల్-టైమ్ అబ్జర్వబిలిటీ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & మరో 22. మీ మొత్తం ఏజెంట్ ఫ్లీట్ కోసం ఒకే డాష్‌బోర్డ్.

> 🌐 **దీన్ని ఇందులో చదవండి:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [మరిన్ని →](docs/i18n/)

ఒక్క కమాండ్. జీరో కాన్ఫిగ్. ప్రతిదీ ఆటో-డిటెక్ట్ అవుతుంది.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** వద్ద తెరుచుకుంటుంది. జీరో కాన్ఫిగ్: ఇది మీ దగ్గర ఇప్పటికే ఉన్న ఏజెంట్ రన్‌టైమ్‌లను కనుగొంటుంది, వాటిని రీడ్-ఓన్లీగా చదువుతుంది, మరియు అవి ఎలా నడుస్తున్నాయో దాని గురించి ఏమీ మార్చదు.

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## 26 ఏజెంట్ రన్‌టైమ్‌లతో పని చేస్తుంది

**ఓపెన్ సోర్స్ యాప్‌లో ఉచితం:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**చెల్లింపు ప్లాన్‌లో:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ప్రతి రన్‌టైమ్‌కు ఒకే డాష్‌బోర్డ్ లభిస్తుంది. అనేకం ఒకేసారి రన్ చేయండి, హెడర్ స్విచర్ ప్రతి ట్యాబ్‌ను వాటిలో ఒకదానికి రీ-స్కోప్ చేస్తుంది.

మీరే SDKపై మీ స్వంత ఏజెంట్‌ను నిర్మించారా? ఇంటర్‌సెప్టర్ దాని LLM కాల్స్‌ను కూడా ట్రాక్ చేస్తుంది. చూడండి [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## మీకు ఏమి లభిస్తుంది

- **సెషన్‌లు & ట్రాన్‌స్క్రిప్ట్‌లు**: ప్రతి ఏజెంట్ ఏమి చేసిందో, టర్న్ బై టర్న్, రీప్లేతో సహా
- **వ్యయం & టోకెన్‌లు**: రన్‌టైమ్, మోడల్, సెషన్ మరియు రోజు వారీగా, అనోమలీ ఫ్లాగ్‌లతో
- **ఫ్లో**: ఛానెల్‌లు, మోడల్‌లు మరియు టూల్స్ ద్వారా కదులుతున్న మెసేజ్‌ల లైవ్ డయాగ్రామ్
- **బ్రెయిన్**: జరుగుతున్నప్పుడు రీజనింగ్ మరియు టూల్-కాల్ ఈవెంట్ స్ట్రీమ్
- **మెమరీ & స్కిల్స్**: ప్రతి రన్‌టైమ్ నిజంగా లోడ్ చేసిన ఫైల్‌లు మరియు స్కిల్స్
- **హెల్త్ & లాగ్స్**: డిస్క్, మెమరీ, ఎర్రర్ రేట్‌లు, రేట్ లిమిట్‌లు, లైవ్ లాగ్ స్ట్రీమ్
- **అలర్ట్‌లు**: బడ్జెట్ క్యాప్‌లు, ఎర్రర్ స్పైక్‌లు, ఏజెంట్-ఆఫ్‌లైన్, Slack, Discord, PagerDuty, Telegram, Email‌కు రూట్ చేయబడతాయి
- **అప్రూవల్స్**: రిస్కీ టూల్ కాల్‌లు *రన్ అయ్యే ముందు* పాజ్ చేసి మీ ఫోన్ నుండి ఆమోదించండి ([ఎలా](docs/APPROVALS.md))

## ధరలు

| ప్లాన్ | ఇందులో ఏమి ఉంది | ధర |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, పూర్తి డాష్‌బోర్డ్, లోకల్ మాత్రమే | $0 |
| **Starter** | పైన పేర్కొన్న ప్రతి ఇతర రన్‌టైమ్, ఫ్లీట్ వ్యూ, క్లౌడ్ సింక్ | నోడ్‌కు నెలకు $9 |
| **Pro** | Starter + గవర్నెన్స్: అప్రూవల్స్, టూల్-రిస్క్ పాలసీలు, ఎవాల్స్, అనోమలీ డిటెక్షన్, కాస్ట్ ఆప్టిమైజర్, OTel ఎక్స్‌పోర్ట్ | నోడ్‌కు నెలకు $19 |

వార్షిక ప్లాన్‌లు, Enterprise మరియు ప్రస్తుత సంఖ్యలు
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** వద్ద ఉన్నాయి. సెల్ఫ్-హోస్టెడ్ లైసెన్స్
కీలు క్లౌడ్ లేకుండానే పని చేస్తాయి (`clawmetry license`). ఖచ్చితమైన ఉచిత/చెల్లింపు విభజన
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)లో ఉంది.

## మీ డేటా మీ మెషీన్‌లోనే ఉంటుంది

ClawMetry లోకల్ సెషన్ ఫైల్‌లు మరియు లాగ్‌లను చదువుతుంది. మీరు `clawmetry connect`
రన్ చేస్తే తప్ప మీ బాక్స్ నుండి ఏదీ బయటకు వెళ్లదు. అప్పుడు కూడా స్నాప్‌షాట్ మీ మెషీన్‌ను
ఎప్పుడూ వదిలిపెట్టని కీతో ఎండ్-టు-ఎండ్ ఎన్‌క్రిప్ట్ చేయబడి, మీ బ్రౌజర్‌లో డిక్రిప్ట్ చేయబడుతుంది.

## ఇన్‌స్టాల్

```bash
pip install clawmetry     # తర్వాత: clawmetry
```

లేదా ఒక్క లైన్‌లో: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux లేదా Windowsలో Python 3.8+ అవసరం, మరియు అదే మెషీన్‌లో కనీసం
ఒక ఏజెంట్ రన్‌టైమ్ ఉండాలి. Docker సూచనలు: [docs/DOCKER.md](docs/DOCKER.md).

## డాక్స్

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ప్రతి అడాప్టర్ ఏమి చదువుతుంది, మరియు రన్‌టైమ్‌ను ఎలా జోడించాలి |
| [Entitlements](docs/ENTITLEMENTS.md) | Free vs paid, టైర్ మ్యాట్రిక్స్, లైసెన్స్ CLI |
| [Approvals & policies](docs/APPROVALS.md) | ప్రీ-ఎగ్జిక్యూషన్ గేటింగ్, రిస్క్ స్కోరింగ్, ఫోన్ అప్రూవల్స్ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ట్రేస్‌లను ఎక్కడికైనా ఎక్స్‌పోర్ట్ చేయండి, ఎక్కడి నుండైనా OTLP ఇన్‌జెస్ట్ చేయండి |
| [SDK tracking](docs/SDK_TRACKING.md) | మీరే నిర్మించిన ఏజెంట్‌ల కోసం కాస్ట్ అట్రిబ్యూషన్ |
| [Chat channels](docs/CHANNELS.md) | ఫ్లోలో చూపబడే చాట్ అడాప్టర్‌లు |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | శాండ్‌బాక్స్‌డ్ NVIDIA NemoClaw సెటప్‌లు |
| [Docker](docs/DOCKER.md) | ఇమేజ్, కంపోజ్, వాల్యూమ్ మౌంట్‌లు |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ఇది లోపల ఎలా పని చేస్తుంది; సోర్స్ నుండి రన్ చేయడం |
| [Telemetry](docs/TELEMETRY.md) | అనామక ఇన్‌స్టాల్ మరియు డెస్క్‌టాప్-ఓపెన్ పింగ్‌లు, మరియు వాటిని ఎలా ఆఫ్ చేయాలి |

## స్క్రీన్‌షాట్‌లు

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: టోకెన్‌లు, సెషన్‌లు, హెల్త్ | **ఏజెంట్లు** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: మోడల్ మరియు సెషన్ వారీగా | **Approvals**: రిస్కీ టూల్ కాల్‌లను గేట్ చేయడం |

రన్‌టైమ్ వారీగా మరిన్ని: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
