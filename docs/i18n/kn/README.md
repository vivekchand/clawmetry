<!-- i18n-src:c111f32e69a5 -->
> ಕನ್ನಡ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ನಿಮ್ಮ ಏಜೆಂಟ್ ಆಲೋಚಿಸುವುದನ್ನು ನೋಡಿ.** **26 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳಿಗೆ** ರಿಯಲ್-ಟೈಮ್ ಅಬ್ಸರ್ವೆಬಿಲಿಟಿ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ಮತ್ತು ಇನ್ನೂ 22. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.

> 🌐 **ಇದನ್ನು ಈ ಭಾಷೆಗಳಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದೇ ಆದೇಶ. ಶೂನ್ಯ ಕಾನ್ಫಿಗರೇಶನ್. ಎಲ್ಲವನ್ನೂ ತಾನಾಗಿಯೇ ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆಯುತ್ತದೆ. ಶೂನ್ಯ ಕಾನ್ಫಿಗರೇಶನ್: ನಿಮ್ಮಲ್ಲಿ ಈಗಾಗಲೇ ಇರುವ ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಇದು ಪತ್ತೆ ಮಾಡುತ್ತದೆ, ಅವುಗಳನ್ನು ಓದಲು-ಮಾತ್ರ ಓದುತ್ತದೆ, ಮತ್ತು ಅವು ಹೇಗೆ ಚಲಿಸುತ್ತವೆ ಎಂಬುದರಲ್ಲಿ ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ.

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## 26 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

**ಓಪನ್ ಸೋರ್ಸ್ ಆಪ್‌ನಲ್ಲಿ ಉಚಿತ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ಪಾವತಿಸಿದ ಪ್ಲಾನ್‌ನಲ್ಲಿ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ಪ್ರತಿಯೊಂದು ರನ್‌ಟೈಮ್‌ಗೂ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಸಿಗುತ್ತದೆ. ಹಲವನ್ನು ಒಟ್ಟಿಗೆ ಚಲಾಯಿಸಿ, ಮತ್ತು ಹೆಡರ್
ಸ್ವಿಚರ್ ಪ್ರತಿಯೊಂದು ಟ್ಯಾಬ್‌ ಅನ್ನೂ ಅವುಗಳಲ್ಲಿ ಒಂದಕ್ಕೆ ಮರುಹೊಂದಿಸುತ್ತದೆ.

SDK ಬಳಸಿ ನಿಮ್ಮದೇ ಆದ ಏಜೆಂಟ್ ಅನ್ನು ನಿರ್ಮಿಸಿದ್ದೀರಾ? ಇಂಟರ್ಸೆಪ್ಟರ್ ಅದರ LLM ಕರೆಗಳನ್ನೂ
ಟ್ರ್ಯಾಕ್ ಮಾಡುತ್ತದೆ. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ನೋಡಿ.

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **ಸೆಷನ್‌ಗಳು ಮತ್ತು ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು**: ಪ್ರತಿ ಏಜೆಂಟ್ ಏನು ಮಾಡಿತು, ಟರ್ನ್ ಬೈ ಟರ್ನ್, ರೀಪ್ಲೇ ಸಮೇತ
- **ವೆಚ್ಚ ಮತ್ತು ಟೋಕನ್‌ಗಳು**: ರನ್‌ಟೈಮ್, ಮಾದರಿ, ಸೆಷನ್ ಮತ್ತು ದಿನದ ಪ್ರಕಾರ, ಅಸಂಗತತೆ ಗುರುತುಗಳೊಂದಿಗೆ
- **ಫ್ಲೋ**: ಚಾನೆಲ್‌ಗಳು, ಮಾದರಿಗಳು ಮತ್ತು ಟೂಲ್‌ಗಳ ಮೂಲಕ ಚಲಿಸುವ ಸಂದೇಶಗಳ ಲೈವ್ ಡಯಾಗ್ರಾಮ್
- **ಬ್ರೇನ್**: ರೀಸನಿಂಗ್ ಮತ್ತು ಟೂಲ್-ಕರೆಯ ಇವೆಂಟ್ ಸ್ಟ್ರೀಮ್, ಅದು ನಡೆಯುತ್ತಿರುವಂತೆಯೇ
- **ಮೆಮೊರಿ ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್ ನಿಜವಾಗಿಯೂ ಲೋಡ್ ಮಾಡಿದ ಫೈಲ್‌ಗಳು ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು
- **ಆರೋಗ್ಯ ಮತ್ತು ಲಾಗ್‌ಗಳು**: ಡಿಸ್ಕ್, ಮೆಮೊರಿ, ದೋಷ ದರಗಳು, ರೇಟ್ ಲಿಮಿಟ್‌ಗಳು, ಲೈವ್ ಲಾಗ್ ಸ್ಟ್ರೀಮ್
- **ಎಚ್ಚರಿಕೆಗಳು**: ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ ಏರಿಕೆಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್, Slack, Discord, PagerDuty, Telegram, Email ಗೆ ರೂಟ್ ಮಾಡಲಾಗಿದೆ
- **ಅನುಮೋದನೆಗಳು**: ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅವು ಚಲಾಯಿಸುವ *ಮೊದಲೇ* ವಿರಮಿಸಿ ಮತ್ತು ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಅನುಮೋದಿಸಿ ([ಹೇಗೆ](docs/APPROVALS.md))

## ಬೆಲೆ

| ಪ್ಲಾನ್ | ಇದು ಏನನ್ನು ಒಳಗೊಂಡಿದೆ | ಬೆಲೆ |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, ಪೂರ್ಣ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್, ಸ್ಥಳೀಯ ಮಾತ್ರ | $0 |
| **Starter** | ಮೇಲಿನ ಇತರ ಎಲ್ಲಾ ರನ್‌ಟೈಮ್, ಫ್ಲೀಟ್ ವ್ಯೂ, ಕ್ಲೌಡ್ ಸಿಂಕ್ | ತಿಂಗಳಿಗೆ ಪ್ರತಿ ನೋಡ್‌ಗೆ $9 |
| **Pro** | Starter + ಗವರ್ನೆನ್ಸ್: ಅನುಮೋದನೆಗಳು, ಟೂಲ್-ರಿಸ್ಕ್ ಪಾಲಿಸಿಗಳು, ಇವಾಲ್‌ಗಳು, ಅಸಂಗತತೆ ಪತ್ತೆ, ಕಾಸ್ಟ್ ಆಪ್ಟಿಮೈಜರ್, OTel ಎಕ್ಸ್‌ಪೋರ್ಟ್ | ತಿಂಗಳಿಗೆ ಪ್ರತಿ ನೋಡ್‌ಗೆ $19 |

ವಾರ್ಷಿಕ ಪ್ಲಾನ್‌ಗಳು, Enterprise ಮತ್ತು ಪ್ರಸ್ತುತ ಸಂಖ್ಯೆಗಳು
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ನಲ್ಲಿ ಇವೆ. ಸ್ವಂತ-ಹೋಸ್ಟ್ ಮಾಡಿದ ಲೈಸೆನ್ಸ್
ಕೀಗಳು ಕ್ಲೌಡ್ ಇಲ್ಲದೆಯೇ ಕೆಲಸ ಮಾಡುತ್ತವೆ (`clawmetry license`). ಫ್ರೀ/ಪೇಯ್ಡ್ ವಿಭಜನೆಯ ನಿಖರ ವಿವರ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ನಲ್ಲಿ ಇದೆ.

## ನಿಮ್ಮ ಡೇಟಾ ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲೇ ಇರುತ್ತದೆ

ClawMetry ಸ್ಥಳೀಯ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಮತ್ತು ಲಾಗ್‌ಗಳನ್ನು ಓದುತ್ತದೆ. ನೀವು `clawmetry connect` ಚಲಾಯಿಸದ
ಹೊರತು ಏನೂ ನಿಮ್ಮ ಯಂತ್ರದಿಂದ ಹೊರಗೆ ಹೋಗುವುದಿಲ್ಲ. ಆಗಲೂ ಸ್ನ್ಯಾಪ್‌ಶಾಟ್ ಎಂಡ್-ಟು-ಎಂಡ್ ಎನ್‌ಕ್ರಿಪ್ಟ್
ಆಗಿರುತ್ತದೆ, ನಿಮ್ಮ ಯಂತ್ರವನ್ನು ಎಂದಿಗೂ ಬಿಟ್ಟುಹೋಗದ ಕೀ ಬಳಸಿ, ಮತ್ತು ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಡಿಕ್ರಿಪ್ಟ್ ಆಗುತ್ತದೆ.

## ಇನ್‌ಸ್ಟಾಲ್

```bash
pip install clawmetry     # ನಂತರ: clawmetry
```

ಅಥವಾ ಒಂದೇ ಸಾಲಿನ ಆದೇಶ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ಅಥವಾ Windows ನಲ್ಲಿ Python 3.8+ ಬೇಕು, ಮತ್ತು ಅದೇ ಯಂತ್ರದಲ್ಲಿ ಕನಿಷ್ಠ ಒಂದು ಏಜೆಂಟ್
ರನ್‌ಟೈಮ್ ಬೇಕು. Docker ಸೂಚನೆಗಳು: [docs/DOCKER.md](docs/DOCKER.md).

## ಡಾಕ್ಸ್

| | |
|---|---|
| [ರನ್‌ಟೈಮ್ ಹೊಂದಾಣಿಕೆ](docs/compatibility.md) | ಪ್ರತಿ ಅಡಾಪ್ಟರ್ ಏನನ್ನು ಓದುತ್ತದೆ, ಮತ್ತು ಒಂದು ರನ್‌ಟೈಮ್ ಅನ್ನು ಹೇಗೆ ಸೇರಿಸುವುದು |
| [ಎಂಟೈಟಲ್‌ಮೆಂಟ್‌ಗಳು](docs/ENTITLEMENTS.md) | Free vs paid, ಟಿಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, license CLI |
| [ಅನುಮೋದನೆಗಳು ಮತ್ತು ಪಾಲಿಸಿಗಳು](docs/APPROVALS.md) | ಪೂರ್ವ-ಎಕ್ಸಿಕ್ಯೂಷನ್ ಗೇಟಿಂಗ್, ರಿಸ್ಕ್ ಸ್ಕೋರಿಂಗ್, ಫೋನ್ ಅನುಮೋದನೆಗಳು |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ಎಲ್ಲಿಗಾದರೂ ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಕ್ಸ್‌ಪೋರ್ಟ್ ಮಾಡಿ, ಎಲ್ಲಿಂದಲಾದರೂ OTLP ಇಂಜೆಸ್ಟ್ ಮಾಡಿ |
| [SDK ಟ್ರ್ಯಾಕಿಂಗ್](docs/SDK_TRACKING.md) | ನೀವೇ ನಿರ್ಮಿಸಿದ ಏಜೆಂಟ್‌ಗಳಿಗೆ ವೆಚ್ಚ ಆಟ್ರಿಬ್ಯೂಷನ್ |
| [ಚಾಟ್ ಚಾನೆಲ್‌ಗಳು](docs/CHANNELS.md) | ಫ್ಲೋನಲ್ಲಿ ತೋರಿಸಲಾದ ಚಾಟ್ ಅಡಾಪ್ಟರ್‌ಗಳು |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಡಲಾದ NVIDIA NemoClaw ಸೆಟಪ್‌ಗಳು |
| [Docker](docs/DOCKER.md) | ಇಮೇಜ್, ಕಂಪೋಸ್, ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು |
| [ಆರ್ಕಿಟೆಕ್ಚರ್](ARCHITECTURE.md) · [ಡೆವಲಪ್‌ಮೆಂಟ್](docs/DEVELOPMENT.md) | ಇದು ಒಳಗೆ ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ; ಮೂಲದಿಂದ ಚಲಾಯಿಸುವುದು |
| [ಟೆಲಿಮೆಟ್ರಿ](docs/TELEMETRY.md) | ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಮತ್ತು ಡೆಸ್ಕ್‌ಟಾಪ್-ಓಪನ್ ಪಿಂಗ್‌ಗಳು, ಮತ್ತು ಅವುಗಳನ್ನು ಆಫ್ ಮಾಡುವುದು ಹೇಗೆ |

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: ಟೋಕನ್‌ಗಳು, ಸೆಷನ್‌ಗಳು, ಆರೋಗ್ಯ | **ಏಜೆಂಟ್‌ಗಳು** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: ಮಾದರಿ ಮತ್ತು ಸೆಷನ್ ಪ್ರಕಾರ | **Approvals**: ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಗೇಟ್ ಮಾಡಿ |

ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ ಇನ್ನಷ್ಟು: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## ಸ್ಟಾರ್ ಇತಿಹಾಸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ಲೈಸೆನ್ಸ್

MIT · ನಿರ್ಮಿಸಿದವರು [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
