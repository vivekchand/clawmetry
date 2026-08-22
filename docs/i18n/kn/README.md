<!-- i18n-src:6795052055e2 -->
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

**ನಿಮ್ಮ ಏಜೆಂಟ್ ಯೋಚಿಸುವುದನ್ನು ನೋಡಿ.** **26 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳಿಗೆ** ರಿಯಲ್-ಟೈಮ್ ಅಬ್ಸರ್ವೆಬಿಲಿಟಿ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ಮತ್ತು ಇನ್ನೂ 22. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.

> 🌐 **ಇದನ್ನು ಈ ಭಾಷೆಗಳಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದೇ ಆದೇಶ. ಶೂನ್ಯ ಕಾನ್ಫಿಗರೇಶನ್. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆಹಚ್ಚುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆಯುತ್ತದೆ. ಶೂನ್ಯ ಕಾನ್ಫಿಗರೇಶನ್: ಇದು ನಿಮ್ಮಲ್ಲಿ ಈಗಾಗಲೇ ಇರುವ ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಕಂಡುಹಿಡಿಯುತ್ತದೆ, ಅವುಗಳನ್ನು ಓದಲು-ಮಾತ್ರ ಆಗಿ ಓದುತ್ತದೆ, ಮತ್ತು ಅವು ಹೇಗೆ ಚಲಿಸುತ್ತವೆ ಎಂಬುದನ್ನು ಏನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 26 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

**ಓಪನ್ ಸೋರ್ಸ್ ಆ್ಯಪ್‌ನಲ್ಲಿ ಉಚಿತ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ಪಾವತಿಸಿದ ಯೋಜನೆಯಲ್ಲಿ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

ಪ್ರತಿಯೊಂದು ರನ್‌ಟೈಮ್‌ಗೂ ಅದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಸಿಗುತ್ತದೆ. ಹಲವಾರನ್ನು ಒಟ್ಟಿಗೆ ಚಲಾಯಿಸಿ, ಹೆಡರ್ ಸ್ವಿಚರ್ ಪ್ರತಿ ಟ್ಯಾಬ್ ಅನ್ನು ಅವುಗಳಲ್ಲಿ ಒಂದಕ್ಕೆ ಮರುಸ್ಕೋಪ್ ಮಾಡುತ್ತದೆ.

SDK ಬಳಸಿ ನಿಮ್ಮದೇ ಆದ ಏಜೆಂಟ್ ಅನ್ನು ನಿರ್ಮಿಸಿದ್ದೀರಾ? ಇಂಟರ್‌ಸೆಪ್ಟರ್ ಅದರ LLM ಕರೆಗಳನ್ನೂ ಟ್ರ್ಯಾಕ್ ಮಾಡುತ್ತದೆ. ನೋಡಿ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **ಸೆಷನ್‌ಗಳು ಮತ್ತು ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು**: ಪ್ರತಿಯೊಂದು ಏಜೆಂಟ್ ಏನು ಮಾಡಿತು, ಟರ್ನ್-ಬೈ-ಟರ್ನ್, ರೀಪ್ಲೇ ಸಮೇತ
- **ವೆಚ್ಚ ಮತ್ತು ಟೋಕನ್‌ಗಳು**: ರನ್‌ಟೈಮ್, ಮಾಡೆಲ್, ಸೆಷನ್ ಮತ್ತು ದಿನದ ಮಟ್ಟದಲ್ಲಿ, ಅಸಂಗತತೆ (anomaly) ಫ್ಲ್ಯಾಗ್‌ಗಳೊಂದಿಗೆ
- **ಫ್ಲೋ**: ಚಾನೆಲ್‌ಗಳು, ಮಾಡೆಲ್‌ಗಳು ಮತ್ತು ಟೂಲ್‌ಗಳ ಮೂಲಕ ಚಲಿಸುವ ಸಂದೇಶಗಳ ಲೈವ್ ಡಯಾಗ್ರಾಮ್
- **ಬ್ರೈನ್**: ರೀಸನಿಂಗ್ ಮತ್ತು ಟೂಲ್-ಕಾಲ್ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್, ಅದು ನಡೆಯುತ್ತಿರುವಂತೆಯೇ
- **ಮೆಮೊರಿ ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್ ನಿಜವಾಗಿ ಲೋಡ್ ಮಾಡಿದ ಫೈಲ್‌ಗಳು ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು
- **ಆರೋಗ್ಯ ಮತ್ತು ಲಾಗ್‌ಗಳು**: ಡಿಸ್ಕ್, ಮೆಮೊರಿ, ದೋಷ ದರಗಳು, ರೇಟ್ ಲಿಮಿಟ್‌ಗಳು, ಲೈವ್ ಲಾಗ್ ಸ್ಟ್ರೀಮ್
- **ಎಚ್ಚರಿಕೆಗಳು**: ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ ಸ್ಪೈಕ್‌ಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್, Slack, Discord, PagerDuty, Telegram, Email ಗೆ ರೂಟ್ ಮಾಡಲಾಗುತ್ತದೆ
- **ಅನುಮೋದನೆಗಳು (Approvals)**: ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅವು ಚಲಿಸುವ *ಮೊದಲೇ* ವಿರಮಿಸಿ ಮತ್ತು ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಅನುಮೋದಿಸಿ ([ಹೇಗೆ](docs/APPROVALS.md))

## ಬೆಲೆ ನಿಗದಿ

| ಯೋಜನೆ | ಇದು ಏನನ್ನು ಒಳಗೊಳ್ಳುತ್ತದೆ | ಬೆಲೆ |
|---|---|---|
| **ಉಚಿತ (Free)** | OpenClaw + NVIDIA NemoClaw + Goose, ಪೂರ್ಣ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್, ಸ್ಥಳೀಯ ಮಾತ್ರ | $0 |
| **ಸ್ಟಾರ್ಟರ್ (Starter)** | ಮೇಲಿನ ಇತರ ಎಲ್ಲಾ ರನ್‌ಟೈಮ್‌ಗಳು, ಫ್ಲೀಟ್ ವ್ಯೂ, ಕ್ಲೌಡ್ ಸಿಂಕ್ | ಪ್ರತಿ ನೋಡ್‌ಗೆ $9 / ತಿಂಗಳು |
| **Pro** | ಸ್ಟಾರ್ಟರ್ + ಗವರ್ನೆನ್ಸ್: ಅನುಮೋದನೆಗಳು, ಟೂಲ್-ರಿಸ್ಕ್ ನೀತಿಗಳು, ಎವಾಲ್‌ಗಳು, ಅಸಂಗತತೆ ಪತ್ತೆ, ವೆಚ್ಚ ಆಪ್ಟಿಮೈಜರ್, OTel ಎಕ್ಸ್‌ಪೋರ್ಟ್ | ಪ್ರತಿ ನೋಡ್‌ಗೆ $19 / ತಿಂಗಳು |

ವಾರ್ಷಿಕ ಯೋಜನೆಗಳು, Enterprise ಮತ್ತು ಪ್ರಸ್ತುತ ಸಂಖ್ಯೆಗಳು
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ನಲ್ಲಿ ಲಭ್ಯವಿದೆ. ಸ್ವಯಂ-ಹೋಸ್ಟ್ ಮಾಡಿದ ಲೈಸೆನ್ಸ್
ಕೀಗಳು ಕ್ಲೌಡ್ ಇಲ್ಲದೆಯೂ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತವೆ (`clawmetry license`). ನಿಖರವಾದ ಉಚಿತ/ಪಾವತಿ ವಿಭಜನೆ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ನಲ್ಲಿದೆ.

## ನಿಮ್ಮ ಡೇಟಾ ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲಿಯೇ ಉಳಿಯುತ್ತದೆ

ClawMetry ಸ್ಥಳೀಯ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಮತ್ತು ಲಾಗ್‌ಗಳನ್ನು ಓದುತ್ತದೆ. ನೀವು `clawmetry connect` ಚಲಾಯಿಸದ ಹೊರತು
ಯಾವುದೂ ನಿಮ್ಮ ಯಂತ್ರವನ್ನು ಬಿಟ್ಟು ಹೋಗುವುದಿಲ್ಲ. ಆಗಲೂ, ಸ್ನ್ಯಾಪ್‌ಶಾಟ್ ಎಂಡ್-ಟು-ಎಂಡ್ ಎನ್‌ಕ್ರಿಪ್ಟ್ ಆಗಿರುತ್ತದೆ,
ಎಂದಿಗೂ ನಿಮ್ಮ ಯಂತ್ರವನ್ನು ಬಿಟ್ಟುಹೋಗದ ಕೀ ಬಳಸಿ, ಮತ್ತು ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಡಿಕ್ರಿಪ್ಟ್ ಆಗುತ್ತದೆ.

## ಇನ್‌ಸ್ಟಾಲ್

```bash
pip install clawmetry     # ನಂತರ: clawmetry
```

ಅಥವಾ ಒಂದೇ ಸಾಲಿನ ಆದೇಶ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ಅಥವಾ Windows ನಲ್ಲಿ Python 3.8+ ಅಗತ್ಯವಿದೆ, ಮತ್ತು ಅದೇ ಯಂತ್ರದಲ್ಲಿ ಕನಿಷ್ಠ ಒಂದು ಏಜೆಂಟ್
ರನ್‌ಟೈಮ್ ಇರಬೇಕು. Docker ಸೂಚನೆಗಳು: [docs/DOCKER.md](docs/DOCKER.md).

## ದಸ್ತಾವೇಜುಗಳು

| | |
|---|---|
| [ರನ್‌ಟೈಮ್ ಹೊಂದಾಣಿಕೆ](docs/compatibility.md) | ಪ್ರತಿ ಅಡಾಪ್ಟರ್ ಏನನ್ನು ಓದುತ್ತದೆ, ಮತ್ತು ರನ್‌ಟೈಮ್ ಸೇರಿಸುವುದು ಹೇಗೆ |
| [ಎಂಟೈಟಲ್‌ಮೆಂಟ್‌ಗಳು](docs/ENTITLEMENTS.md) | ಉಚಿತ vs ಪಾವತಿ, ಟಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, ಲೈಸೆನ್ಸ್ CLI |
| [ಅನುಮೋದನೆಗಳು ಮತ್ತು ನೀತಿಗಳು](docs/APPROVALS.md) | ಪೂರ್ವ-ಕಾರ್ಯಗತಗೊಳಿಸುವಿಕೆ ಗೇಟಿಂಗ್, ರಿಸ್ಕ್ ಸ್ಕೋರಿಂಗ್, ಫೋನ್ ಅನುಮೋದನೆಗಳು |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ಎಲ್ಲಿಯಾದರೂ ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಕ್ಸ್‌ಪೋರ್ಟ್ ಮಾಡಿ, ಎಲ್ಲಿಂದಲಾದರೂ OTLP ಅನ್ನು ಇಂಜೆಸ್ಟ್ ಮಾಡಿ |
| [SDK ಟ್ರ್ಯಾಕಿಂಗ್](docs/SDK_TRACKING.md) | ನೀವೇ ನಿರ್ಮಿಸಿದ ಏಜೆಂಟ್‌ಗಳಿಗೆ ವೆಚ್ಚ ಅಟ್ರಿಬ್ಯೂಷನ್ |
| [ಚಾಟ್ ಚಾನೆಲ್‌ಗಳು](docs/CHANNELS.md) | ಫ್ಲೋನಲ್ಲಿ ತೋರಿಸಲಾದ ಚಾಟ್ ಅಡಾಪ್ಟರ್‌ಗಳು |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಡಿದ NVIDIA NemoClaw ಸೆಟಪ್‌ಗಳು |
| [Docker](docs/DOCKER.md) | ಇಮೇಜ್, ಕಂಪೋಸ್, ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು |
| [ಆರ್ಕಿಟೆಕ್ಚರ್](ARCHITECTURE.md) · [ಡೆವಲಪ್‌ಮೆಂಟ್](docs/DEVELOPMENT.md) | ಇದು ಒಳಗೆ ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ; ಮೂಲದಿಂದ ಚಲಾಯಿಸುವುದು |
| [ಟೆಲಿಮೆಟ್ರಿ](docs/TELEMETRY.md) | ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಮತ್ತು ಡೆಸ್ಕ್‌ಟಾಪ್-ಓಪನ್ ಪಿಂಗ್‌ಗಳು, ಮತ್ತು ಅವುಗಳನ್ನು ಆಫ್ ಮಾಡುವುದು ಹೇಗೆ |

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: ಟೋಕನ್‌ಗಳು, ಸೆಷನ್‌ಗಳು, ಆರೋಗ್ಯ | **Brain**: ಲೈವ್ ಏಜೆಂಟ್ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್ |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: ಮಾಡೆಲ್ ಮತ್ತು ಸೆಷನ್ ಪ್ರಕಾರ | **Approvals**: ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಗೇಟ್ ಮಾಡಿ |

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

MIT · [@vivekchand](https://github.com/vivekchand) ಇವರಿಂದ ನಿರ್ಮಿಸಲಾಗಿದೆ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
