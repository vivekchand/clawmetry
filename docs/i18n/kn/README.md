<!-- i18n-src:12b97259721e -->
> ಕನ್ನಡ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ಒಂದು ಏಜೆಂಟ್ ಪ್ರಗತಿ ಸಾಧಿಸದೆಯೇ ನೂರು ಟೂಲ್ ಕರೆಗಳನ್ನು ಮಾಡಬಹುದು.** ClawMetry
ನಿಮ್ಮ ಕೋಡಿಂಗ್ ಏಜೆಂಟ್‌ಗಳು ಈಗಾಗಲೇ ಬರೆಯುವ ಸೆಷನ್ ಫೈಲ್‌ಗಳನ್ನು ಓದುತ್ತದೆ, ಮತ್ತು ಟೈಮ್‌ಲೈನ್,
ಟೂಲ್ ಕರೆಗಳು ಹಾಗೂ ರನ್‌ಟೈಮ್ ಬಹಿರಂಗಪಡಿಸುವ ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚದ ದತ್ತಾಂಶವನ್ನು ಒಂದೇ
ವೀಕ್ಷಣೆಯಲ್ಲಿ ಇಡುತ್ತದೆ — ಇದರಿಂದ ಕೆಲಸ ಮಾಡುತ್ತಿರುವ ದೀರ್ಘ ರನ್ ಮತ್ತು ಸಿಲುಕಿಕೊಂಡಿರುವ
ರನ್ ಅನ್ನು ನೀವು ಪ್ರತ್ಯೇಕಿಸಬಹುದು.

**31 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ** ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ — Claude Code, OpenAI Codex, Hermes, OpenClaw ಮತ್ತು ಇನ್ನೂ 27 ಇತರೆ. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್. ([ಸಂಪೂರ್ಣ ಪಟ್ಟಿ](SUPPORTED_RUNTIMES.txt), ಕ್ಯಾಟಲಾಗ್‌ನಿಂದ ಜನರೇಟ್ ಮಾಡಲಾಗಿದೆ.)

> 🌐 **ಇದನ್ನು ಈ ಭಾಷೆಗಳಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದೇ ಕಮಾಂಡ್. ಸೊನ್ನೆ ಕಾನ್ಫಿಗ್. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆಹಚ್ಚುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆಯುತ್ತದೆ. ಸೊನ್ನೆ ಕಾನ್ಫಿಗ್: ಇದು ನಿಮ್ಮ ಬಳಿ ಈಗಾಗಲೇ ಇರುವ
ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಕಂಡುಹಿಡಿಯುತ್ತದೆ, ಅವುಗಳನ್ನು ರೀಡ್-ಓನ್ಲಿ ಆಗಿ ಓದುತ್ತದೆ, ಮತ್ತು ಅವು
ಹೇಗೆ ಚಲಿಸುತ್ತವೆ ಎಂಬುದರ ಬಗ್ಗೆ ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡುವ ಮೊದಲು

| | |
|---|---|
| **ಇದು ಏನು ಮಾಡುತ್ತದೆ** | ನಿಮ್ಮ ಏಜೆಂಟ್‌ಗಳು ಈಗಾಗಲೇ ಬರೆಯುವ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಮತ್ತು ಲಾಗ್‌ಗಳನ್ನು ಓದುತ್ತದೆ. ಯಾವುದೇ SDK ಇಲ್ಲ, ಕೋಡ್ ಬದಲಾವಣೆ ಇಲ್ಲ, ನಿಮ್ಮ ಅಪ್ಲಿಕೇಶನ್‌ನಲ್ಲಿ ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್ ಇಲ್ಲ. |
| **ನೀವು ಏನನ್ನು ನೋಡುತ್ತೀರಿ** | ಸೆಷನ್ ಟೈಮ್‌ಲೈನ್, ಟೂಲ್-ಬೈ-ಟೂಲ್ ರೀಪ್ಲೇ, ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚದ ವಿಭಜನೆ, ಮತ್ತು ಟ್ರಜೆಕ್ಟರಿ ಸಂಕೇತಗಳು (ಲೂಪಿಂಗ್, ಪುನರಾವರ್ತಿತ ವೈಫಲ್ಯಗಳು) — ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ. |
| **ಏನು ಉಚಿತ** | `pip install clawmetry` **OpenClaw, NVIDIA NemoClaw ಮತ್ತು Goose** ಅನ್ನು ಯಾವುದೇ ಖಾತೆ, ಕೀ ಅಥವಾ ನೆಟ್‌ವರ್ಕ್ ಕರೆ ಇಲ್ಲದೆ ಓದುತ್ತದೆ. ಇತರ 27 — Claude Code, Codex, Cursor ಮತ್ತು ಉಳಿದವು — ಅನ್ನು ಕ್ಲೋಸ್ಡ್-ಸೋರ್ಸ್ `clawmetry-pro` ಕಂಪ್ಯಾನಿಯನ್ ಓದುತ್ತದೆ, ಇದು 7-ದಿನದ ಟ್ರಯಲ್ ಅಥವಾ ಪ್ಲಾನ್‌ನೊಂದಿಗೆ ಬರುತ್ತದೆ — ನಿಖರವಾದ ವಿಭಜನೆಗಾಗಿ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ನೋಡಿ. |
| **ಹೇಗೆ ಪ್ರಾರಂಭಿಸುವುದು** | `pip install clawmetry && clawmetry`, ನಂತರ localhost:8900 ತೆರೆಯಿರಿ. ಈ ಯಂತ್ರದಲ್ಲಿ ಇನ್ನೂ ಯಾವುದೇ ಏಜೆಂಟ್‌ಗಳಿಲ್ಲವೇ? `clawmetry --sample` ಮೂರು ಲೇಬಲ್ ಮಾಡಿದ ಸಿಂಥೆಟಿಕ್ ಸೆಷನ್‌ಗಳೊಂದಿಗೆ ತೆರೆಯುತ್ತದೆ. |
| **ನಿಮ್ಮ ಯಂತ್ರದಿಂದ ಏನು ಹೊರಹೋಗುತ್ತದೆ** | ನೀವು `clawmetry connect` ಚಲಾಯಿಸದ ಹೊರತು ಯಾವುದೇ ಸೆಷನ್ ದತ್ತಾಂಶ ಹೊರಹೋಗುವುದಿಲ್ಲ. ಡೀಫಾಲ್ಟ್ ಆಗಿ ಎರಡು ವಿಷಯಗಳು ನಡೆಯುತ್ತವೆ, ಎರಡೂ ಆಪ್ಟ್-ಔಟ್ ಆಗಿದ್ದು ಯಾವುದೂ ಸೆಷನ್ ವಿಷಯವನ್ನು ಹೊತ್ತೊಯ್ಯುವುದಿಲ್ಲ: ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಪಿಂಗ್ ಮತ್ತು PyPI ಆವೃತ್ತಿ ಪರಿಶೀಲನೆ. ಪ್ರತಿಯೊಂದು ಗಮ್ಯಸ್ಥಾನವನ್ನೂ [docs/EGRESS.md](docs/EGRESS.md) ನಲ್ಲಿ ದಾಖಲಿಸಲಾಗಿದೆ, ಕಾಮೆಂಟ್‌ಗಳನ್ನು ಓದುವ ಬದಲು ವೈರ್ ಕ್ಯಾಪ್ಚರ್‌ನಿಂದ ಮರುನಿರ್ಮಿಸಲಾಗಿದೆ. |

ಔಟ್‌ಪುಟ್ ಅನ್ನು ನಿರ್ಣಯಿಸುವ ಮೊದಲು ತಿಳಿದುಕೊಳ್ಳಬೇಕಾದ ಎರಡು ಮಿತಿಗಳಿವೆ: ರನ್‌ಟೈಮ್‌ಗಳು ಬಹಳ
ವಿಭಿನ್ನ ದತ್ತಾಂಶವನ್ನು ಬಹಿರಂಗಪಡಿಸುತ್ತವೆ (ಕೆಲವು ಯಾವುದೇ ವೆಚ್ಚವನ್ನೂ ಪ್ರಕಟಿಸುವುದಿಲ್ಲ —
ಯಾವುದು ಎಂಬುದನ್ನು [ಮ್ಯಾಟ್ರಿಕ್ಸ್](docs/compatibility.md) ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ ಹೇಳುತ್ತದೆ), ಮತ್ತು
ಒಂದು ಕ್ರಿಯೆಯನ್ನು ವೀಕ್ಷಿಸುವುದು ಅದನ್ನು ತಡೆಯುವ ಸಾಮರ್ಥ್ಯದಂತೆಯೇ ಅಲ್ಲ ([ಯಾವ ನಿಯಂತ್ರಣಗಳು
ನಿಜವಾಗಿವೆ, ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ](docs/APPROVALS.md)).


## 31 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

**ಓಪನ್ ಸೋರ್ಸ್ ಅಪ್ಲಿಕೇಶನ್‌ನಲ್ಲಿ ಉಚಿತ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ಪಾವತಿಸಿದ ಪ್ಲಾನ್‌ನಲ್ಲಿ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ಪ್ರತಿಯೊಂದು ರನ್‌ಟೈಮ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಸಿಗುತ್ತದೆ. ಒಂದೇ ಬಾರಿಗೆ ಹಲವನ್ನು ಚಲಾಯಿಸಿ,
ಹೆಡರ್ ಸ್ವಿಚರ್ ಪ್ರತಿ ಟ್ಯಾಬ್ ಅನ್ನು ಅವುಗಳಲ್ಲಿ ಒಂದಕ್ಕೆ ಮರುಸ್ಕೋಪ್ ಮಾಡುತ್ತದೆ.

SDK ಬಳಸಿ ನಿಮ್ಮ ಸ್ವಂತ ಏಜೆಂಟ್ ಅನ್ನು ನಿರ್ಮಿಸಿದ್ದೀರಾ? ಇಂಟರ್‌ಸೆಪ್ಟರ್ ಅದರ LLM ಕರೆಗಳನ್ನೂ
ಟ್ರ್ಯಾಕ್ ಮಾಡುತ್ತದೆ. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ನೋಡಿ.

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **ಸೆಷನ್‌ಗಳು ಮತ್ತು ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು**: ಪ್ರತಿ ಏಜೆಂಟ್ ಏನು ಮಾಡಿತು, ಸರದಿಯಿಂದ ಸರದಿಗೆ, ರೀಪ್ಲೇ ಸಹಿತ
- **ವೆಚ್ಚ ಮತ್ತು ಟೋಕನ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್, ಮಾಡೆಲ್, ಸೆಷನ್ ಮತ್ತು ದಿನಕ್ಕೆ, ಅಸಂಗತತೆ ಫ್ಲ್ಯಾಗ್‌ಗಳೊಂದಿಗೆ
- **ಫ್ಲೋ**: ಚಾನೆಲ್‌ಗಳು, ಮಾಡೆಲ್‌ಗಳು ಮತ್ತು ಟೂಲ್‌ಗಳ ಮೂಲಕ ಚಲಿಸುವ ಸಂದೇಶಗಳ ಲೈವ್ ಡಯಾಗ್ರಾಂ
- **ಬ್ರೈನ್**: ರೀಸನಿಂಗ್ ಮತ್ತು ಟೂಲ್-ಕರೆ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್ ಅದು ನಡೆಯುತ್ತಿರುವಂತೆ
- **ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್**: ಪ್ರೊವೈಡರ್ ಪ್ರಕಾರ ಗಾತ್ರ ಹೊಂದಿಸಿದ ವಿಂಡೋ ಬಳಕೆ, ಕಂಪ್ಯಾಕ್ಷನ್ ವರ್ಸಸ್ ಬಲವಂತದ ಓವರ್‌ಫ್ಲೋ, ಜೊತೆಗೆ ನಾವು *ನೋಡಲಾಗದ* ವಿಷಯದ ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ನಕ್ಷೆ ([ಹೇಗೆ](docs/CONTEXT_BLOWOUT.md))
- **ಮೆಮೊರಿ ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್ ವಾಸ್ತವವಾಗಿ ಲೋಡ್ ಮಾಡಿದ ಫೈಲ್‌ಗಳು ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು
- **ಆರೋಗ್ಯ ಮತ್ತು ಲಾಗ್‌ಗಳು**: ಡಿಸ್ಕ್, ಮೆಮೊರಿ, ದೋಷ ದರಗಳು, ದರ ಮಿತಿಗಳು, ಲೈವ್ ಲಾಗ್ ಸ್ಟ್ರೀಮ್
- **ಎಚ್ಚರಿಕೆಗಳು**: ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ ಸ್ಪೈಕ್‌ಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್, Slack, Discord, PagerDuty, Telegram, Email ಗೆ ರೂಟ್ ಮಾಡಲಾಗಿದೆ
- **ಅನುಮೋದನೆಗಳು**: ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅವು ಚಲಿಸುವ *ಮೊದಲೇ* ವಿರಾಮಗೊಳಿಸಿ ಮತ್ತು ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಅನುಮೋದಿಸಿ ([ಹೇಗೆ](docs/APPROVALS.md))

## ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್, ಮತ್ತು ವೀಕ್ಷಣೆಯ ವೆಚ್ಚ ಏನು

ಯಾವುದೇ ಏಜೆಂಟ್-ಹೋಲಿಕೆ ಟೂಲ್ ಅನ್ನು ನಂಬುವ ಮೊದಲು ಉತ್ತರಿಸಬೇಕಾದ ಎರಡು ಪ್ರಶ್ನೆಗಳು.

**ಇದು ರನ್‌ಟೈಮ್‌ಗಳಾದ್ಯಂತ ಕಾಂಟೆಕ್ಸ್ಟ್-ವಿಂಡೋ ಬ್ಲೋಔಟ್ ಅನ್ನು ಹೇಗೆ ನಿಭಾಯಿಸುತ್ತದೆ?**

ಬಳಕೆಯ ಶೇಕಡಾವಾರು ಪ್ರಮಾಣ ಅದು ಯಾವುದನ್ನು ಭಾಗಿಸುತ್ತದೆ ಎಂಬುದರಷ್ಟೇ ಪ್ರಾಮಾಣಿಕವಾಗಿದೆ.
ClawMetry ವಿಂಡೋವನ್ನು ನೀವು ಓದಬಹುದಾದ ಮತ್ತು PR ಮಾಡಬಹುದಾದ [ಒಂದು ಟೇಬಲ್](clawmetry/context_windows.py)
ನಿಂದ ಪ್ರೊವೈಡರ್ ಪ್ರಕಾರ ಗಾತ್ರ ಹೊಂದಿಸುತ್ತದೆ, ಇದು Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama ಮತ್ತು GLM ಅನ್ನು ಒಳಗೊಂಡಿದೆ. ಇದು ಎಲ್ಲಾ 31
ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಒಂದೇ ಮಾರಾಟಗಾರನ ಅಳತೆಗೋಲಿನಿಂದ ಅಳೆಯುವುದಿಲ್ಲ. ಇದು ಮುಖ್ಯ: 300K
GPT-5 ಸರದಿಯನ್ನು Anthropic ನ 200K ವಿರುದ್ಧ ಸ್ಕೋರ್ ಮಾಡಿದರೆ ">100%, ಸ್ಫೋಟಗೊಂಡಿದೆ"
ಎಂದು ಓದುತ್ತದೆ, ವಾಸ್ತವದಲ್ಲಿ ಅದು GPT-5 ನ 400K ಯ 75% ರಷ್ಟಿದೆ. ಅದೇ ಅಳತೆಗೋಲು
ನಿಜವಾಗಿಯೂ ಓವರ್‌ಫ್ಲೋ ಆದ 130K DeepSeek ಸರದಿಯನ್ನು ಆರಾಮದಾಯಕ 65% ಆಗಿ ಮರೆಮಾಡುತ್ತದೆ.

ಪ್ರತಿ ವಿಂಡೋ ತನ್ನ ಮೂಲದ ಜೊತೆಗೆ ಬರುತ್ತದೆ: `model_table`, `explicit_marker`,
`observed_floor`, ಅಥವಾ ನಮಗೆ ಮಾಡೆಲ್ ಗೊತ್ತಿಲ್ಲದಿದ್ದಾಗ ಪ್ರಾಮಾಣಿಕ `default`. ಊಹೆಯ
ಮೇಲೆ ನಿರ್ಮಿಸಿದ ಗೇಜ್ ಎಂದಿಗೂ ಲುಕಪ್ ಮೇಲೆ ನಿರ್ಮಿಸಿದ ಒಂದೇ ಅಧಿಕಾರದೊಂದಿಗೆ ರೆಂಡರ್
ಆಗುವುದಿಲ್ಲ.

ClawMetry ಕೆಲವು ರನ್‌ಟೈಮ್‌ಗಳಲ್ಲಿ ಮಾತ್ರ ಕಂಪ್ಯಾಕ್ಷನ್ ಈವೆಂಟ್‌ಗಳನ್ನು ನೋಡಬಲ್ಲದು. ಆದ್ದರಿಂದ
`GET /api/context-coverage` ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ, ಸೊನ್ನೆ ಎಂದರೆ **"ಸ್ವಚ್ಛವಾಗಿ ಓಡಿತು"
ಎಂದೋ "ನಾವು ಕುರುಡಾಗಿದ್ದೇವೆ" ಎಂದೋ** ಎಂಬುದನ್ನು ವರದಿ ಮಾಡುತ್ತದೆ. ವಾಸ್ತವವಾಗಿ ಕುರುಡು
ಎಂದರ್ಥವಿರುವ `0` ಹಾಗೆಂದೇ ಹೇಳುತ್ತದೆ. [ಪೂರ್ಣ ವಿವರ](docs/CONTEXT_BLOWOUT.md)

**ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ನ ವೆಚ್ಚ ಎಷ್ಟು?**

| ಪಥ | ನಿಮ್ಮ ಏಜೆಂಟ್‌ಗೆ ಸೇರಿಸಲಾಗಿದೆ | ಡೀಫಾಲ್ಟ್? |
|---|---|---|
| ಸೆಷನ್-ಫೈಲ್ ಟೈಲಿಂಗ್ (ಎಲ್ಲಾ 31 ರನ್‌ಟೈಮ್‌ಗಳು) | **0**. ಪ್ರತ್ಯೇಕ ಪ್ರಕ್ರಿಯೆ, ನಿಮ್ಮ ಏಜೆಂಟ್‌ನಲ್ಲಿ ಯಾವುದೇ ClawMetry ಕೋಡ್ ಇಲ್ಲ | ಆನ್ |
| HTTP ಇಂಟರ್‌ಸೆಪ್ಟರ್ (`CLAWMETRY_INTERCEPT=1`) | ಪ್ರತಿ LLM ಕರೆಗೆ **+0.44 ms**, ಅಥವಾ 5s ಕರೆಯ 0.009% | ಆಫ್ |
| ಪ್ರೀ-ಟೂಲ್ ಹುಕ್ ಗೇಟ್ (ವಾರ್ಮ್ ಕ್ಯಾಶ್) | 36 ms ಇಂಟರ್ಪ್ರೀಟರ್ ಫ್ಲೋರ್‌ಗಿಂತ ಹೆಚ್ಚಾಗಿ, ಪ್ರತಿ ಗೇಟೆಡ್ ಟೂಲ್ ಕರೆಗೆ **+44 ms** | ಆಫ್ |
| ಎನ್‌ಫೋರ್ಸ್‌ಮೆಂಟ್ ಪ್ರಾಕ್ಸಿ | ಪ್ರತಿ LLM ಕರೆಗೆ **+9.7 ms** | ಆಫ್ |

ಡೀಮನ್ ಹೋಸ್ಟ್ ವೆಚ್ಚ: **2,762 ಈವೆಂಟ್‌ಗಳು/ಸೆಕೆಂಡ್** ಇಂಜೆಸ್ಟ್, ಡಿಸ್ಕ್‌ನಲ್ಲಿ **710 ಬೈಟ್‌ಗಳು/ಈವೆಂಟ್**
(100k ಈವೆಂಟ್‌ಗಳಿಗೆ 67.7 MB), ಮತ್ತು ಬಿಜಿ ಇನ್‌ಸ್ಟಾಲ್‌ನಲ್ಲಿ ನಿರಂತರವಾಗಿ **ಒಂದು ಕೋರ್‌ನ
~12%**. ಆ ಕೊನೆಯ ಸಂಖ್ಯೆ ನಮ್ಮದೇ ಘೋಷಿತ 5-10% ಬಜೆಟ್‌ಗಿಂತ ಹೆಚ್ಚಾಗಿದೆ, ಆದ್ದರಿಂದ ಇದನ್ನು
ಪುಟದಿಂದ ಬಿಟ್ಟುಬಿಡುವ ಬದಲು ಬೆನ್ನಟ್ಟಬೇಕಾದ ಬಗ್ ಆಗಿ ಪ್ರಕಟಿಸಲಾಗಿದೆ.

Apple M2 Pro ನಲ್ಲಿ `benchmarks/overhead.py` ಬಳಸಿ ಅಳೆಯಲಾಗಿದೆ. ಹಾರ್ನೆಸ್ ಪ್ರತಿ
ಸ್ಥಿತಿಯನ್ನೂ ಪ್ರತ್ಯೇಕ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿ ಚಲಾಯಿಸುತ್ತದೆ, ಅವುಗಳ ಕ್ರಮವನ್ನು ಬದಲಾಯಿಸುತ್ತದೆ, ಮತ್ತು
**ಸುತ್ತುಗಳು ಅದರ ಚಿಹ್ನೆಯ ಬಗ್ಗೆ ಒಪ್ಪದಿದ್ದಾಗ ಸಂಖ್ಯೆಯನ್ನು ಮುದ್ರಿಸಲು ನಿರಾಕರಿಸುತ್ತದೆ**.
ಇದನ್ನು ನಿಮ್ಮ ಸ್ವಂತ ಯಂತ್ರದಲ್ಲಿ ಒಂದು ನಿಮಿಷದಲ್ಲಿ ಚಲಾಯಿಸಿ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ಹುಕ್ ಗೇಟ್‌ಗಳು ಮತ್ತು ಎನ್‌ಫೋರ್ಸ್‌ಮೆಂಟ್ ಪ್ರಾಕ್ಸಿ ಸೇರಿದಂತೆ ಪ್ರತಿ ಪಥವನ್ನೂ ಅಳೆಯಲಾಗುತ್ತದೆ,
ಮತ್ತು ಹಾರ್ನೆಸ್ CI ನಲ್ಲಿ Linux, macOS ಮತ್ತು Windows ನಲ್ಲಿ ಚಲಿಸುತ್ತದೆ. ತಿಳಿದುಕೊಳ್ಳಬೇಕಾದ
ಎರಡು ಫಲಿತಾಂಶಗಳು: ಪ್ರಾಕ್ಸಿ Windows ನಲ್ಲಿ Linux ಗಿಂತ ಸುಮಾರು ಏಳು ಪಟ್ಟು ಹೆಚ್ಚು ವೆಚ್ಚ
ಮಾಡುತ್ತದೆ, ಮತ್ತು ಡೀಮನ್ ಪ್ರಸ್ತುತ ಒಂದು ಕೋರ್‌ನ ಸುಮಾರು 12% ಅನ್ನು ನಿರಂತರವಾಗಿ
ಉಳಿಸಿಕೊಳ್ಳುತ್ತದೆ, ನಮ್ಮದೇ 5-10% ಬಜೆಟ್‌ಗಿಂತ ಹೆಚ್ಚಾಗಿ. ಕಚ್ಚಾ JSON, ವಿಧಾನ, ಮತ್ತು
ಇನ್ನೂ ಅಳೆಯದಿರುವುದು [docs/OVERHEAD.md](docs/OVERHEAD.md) ನಲ್ಲಿದೆ.

## ಬೆಲೆ ನಿಗದಿ

| ಪ್ಲಾನ್ | ಇದು ಏನನ್ನು ಒಳಗೊಂಡಿದೆ | ಬೆಲೆ |
|---|---|---|
| **ಉಚಿತ** | OpenClaw + NVIDIA NemoClaw + Goose, ಪೂರ್ಣ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್, ಸ್ಥಳೀಯ ಮಾತ್ರ | $0 |
| **ಸ್ಟಾರ್ಟರ್** | ಮೇಲಿನ ಪ್ರತಿಯೊಂದು ಇತರೆ ರನ್‌ಟೈಮ್, ಫ್ಲೀಟ್ ವೀಕ್ಷಣೆ, ಕ್ಲೌಡ್ ಸಿಂಕ್ | ಪ್ರತಿ ನೋಡ್‌ಗೆ $9 / ತಿಂಗಳು |
| **Pro** | ಸ್ಟಾರ್ಟರ್ + ನಿಯಂತ್ರಣ ಮತ್ತು ಮೌಲ್ಯಮಾಪನ: ಅನುಮೋದನೆಗಳು, ಟೂಲ್-ಅಪಾಯ ನೀತಿಗಳು, ಮೌಲ್ಯಮಾಪನಗಳು, ಅಸಂಗತತೆ ಪತ್ತೆ, ವೆಚ್ಚ ಆಪ್ಟಿಮೈಜರ್, OTel ಎಕ್ಸ್‌ಪೋರ್ಟ್, ಟ್ಯಾಂಪರ್-ಎವಿಡೆಂಟ್ ಆಡಿಟ್ ಲಾಗ್ | ಪ್ರತಿ ನೋಡ್‌ಗೆ $19 / ತಿಂಗಳು |

ವಾರ್ಷಿಕ ಪ್ಲಾನ್‌ಗಳು, Enterprise ಮತ್ತು ಪ್ರಸ್ತುತ ಸಂಖ್ಯೆಗಳು
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ನಲ್ಲಿ ಇವೆ. ಸ್ವಯಂ-ಹೋಸ್ಟ್
ಮಾಡಿದ ಲೈಸೆನ್ಸ್ ಕೀಗಳು ಕ್ಲೌಡ್ ಇಲ್ಲದೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತವೆ (`clawmetry license`). ನಿಖರವಾದ
ಉಚಿತ/ಪಾವತಿಸಿದ ವಿಭಜನೆ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ನಲ್ಲಿದೆ.

## ನಿಮ್ಮ ದತ್ತಾಂಶ ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲೇ ಇರುತ್ತದೆ

ClawMetry ಸ್ಥಳೀಯ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಮತ್ತು ಲಾಗ್‌ಗಳನ್ನು ಓದುತ್ತದೆ. ನೀವು
**`clawmetry connect` ಚಲಾಯಿಸದ ಹೊರತು ಯಾವುದೇ ಸೆಷನ್ ದತ್ತಾಂಶ ನಿಮ್ಮ ಬಾಕ್ಸ್‌ನಿಂದ
ಹೊರಹೋಗುವುದಿಲ್ಲ** — ಯಾವುದೇ ಪ್ರಾಂಪ್ಟ್‌ಗಳು, ಪ್ರತಿಕ್ರಿಯೆಗಳು, ಟೂಲ್ ಆರ್ಗ್ಯುಮೆಂಟ್‌ಗಳು, ಫೈಲ್
ವಿಷಯಗಳು ಅಥವಾ ಲಾಗ್ ಸಾಲುಗಳಿಲ್ಲ. ನೀವು ಸಂಪರ್ಕಿಸಿದಾಗ, ಸ್ನ್ಯಾಪ್‌ಶಾಟ್ ಅನ್ನು ನಿಮ್ಮ ಯಂತ್ರವನ್ನು
ಎಂದಿಗೂ ಬಿಟ್ಟುಹೋಗದ ಕೀಯೊಂದಿಗೆ ಎಂಡ್-ಟು-ಎಂಡ್ ಎನ್‌ಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗುತ್ತದೆ, ಮತ್ತು ನಿಮ್ಮ
ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಡಿಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗುತ್ತದೆ. ಒಂದು ನೋಡ್‌ಗೆ ಕೀ ಇಲ್ಲದಿದ್ದರೆ, ಅಪ್‌ಲೋಡ್ ಅನ್ನು
ಸ್ಪಷ್ಟವಾಗಿ ಕಳುಹಿಸುವ ಬದಲು ಬಿಟ್ಟುಬಿಡಲಾಗುತ್ತದೆ, ಮತ್ತು ಯಾವುದೇ ಸರ್ವರ್ ಪ್ರತಿಕ್ರಿಯೆ ಅದನ್ನು
ಆಫ್ ಮಾಡಲಾಗುವುದಿಲ್ಲ.

ಸಂಪರ್ಕಿಸುವ ಮೊದಲು ಡೀಫಾಲ್ಟ್ ಆಗಿ ಎರಡು ವಿಷಯಗಳು ನಡೆಯುತ್ತವೆ, ಎರಡೂ ಆಪ್ಟ್-ಔಟ್ ಆಗಿದ್ದು
ಯಾವುದೂ ಸೆಷನ್ ದತ್ತಾಂಶವನ್ನು ಹೊತ್ತೊಯ್ಯುವುದಿಲ್ಲ: ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಪಿಂಗ್ ಮತ್ತು PyPI
ವಿರುದ್ಧ ಆವೃತ್ತಿ ಪರಿಶೀಲನೆ. ಡೀಫಾಲ್ಟ್ ಇನ್‌ಸ್ಟಾಲ್ ಸ್ಟಾರ್ಟಪ್ ಬ್ಯಾನರ್ ಸಾಲಿಗಾಗಿ ನಿಮ್ಮ ಸಾರ್ವಜನಿಕ
IP ಅನ್ನೂ ಒಮ್ಮೆ ಹುಡುಕುತ್ತದೆ. ಪ್ರತಿ ಗಮ್ಯಸ್ಥಾನ, ಅದು ಏನನ್ನು ಹೊತ್ತೊಯ್ಯುತ್ತದೆ ಮತ್ತು ಅದನ್ನು
ಹೇಗೆ ಆಫ್ ಮಾಡುವುದು ಎಂಬುದನ್ನು [docs/EGRESS.md](docs/EGRESS.md) ನಲ್ಲಿ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ;
ಸ್ವಯಂ-ಹೋಸ್ಟ್ ಮಾಡಿದ, ಮರುನಿರ್ದೇಶಿಸಿದ ಮತ್ತು ಏರ್-ಗ್ಯಾಪ್ ಮಾಡಿದ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು ಯಾವುದೇ
ವಿವೇಚನಾ ಔಟ್‌ಬೌಂಡ್ ಕರೆಗಳನ್ನು ಮಾಡುವುದಿಲ್ಲ.

ಡಿಕ್ರಿಪ್ಶನ್ ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ, ನಾವು ನಿಮಗೆ ಒದಗಿಸುವ ಕೋಡ್‌ನಲ್ಲಿ ನಡೆಯುತ್ತದೆ. ಅದು ಹಿಂದೆ
ಒಂದು ವಾಗ್ದಾನವಾಗಿತ್ತು; ಈಗ ಅದು ನೀವು ಪರಿಶೀಲಿಸಬಹುದಾದ ಸಂಗತಿ. ನಿಮ್ಮ ಕೀಯನ್ನು ಸ್ಪರ್ಶಿಸುವ
ಪ್ರತಿ ಸಾಲೂ ಒಂದೇ ಓದಬಹುದಾದ ಫೈಲ್‌ನಲ್ಲಿ ವಾಸಿಸುತ್ತದೆ,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ಇದು ವೀಲ್ ಒಳಗೆ
ರವಾನೆಯಾಗುತ್ತದೆ ಮತ್ತು ಸಬ್‌ರಿಸೋರ್ಸ್ ಇಂಟೆಗ್ರಿಟಿ ಹ್ಯಾಶ್‌ನೊಂದಿಗೆ ಪಿನ್ ಮಾಡಿ ಯಥಾವತ್ತಾಗಿ
ಸೇವೆ ಸಲ್ಲಿಸಲಾಗುತ್ತದೆ. ಬ್ರೌಸರ್ ನಾವು ಪ್ರಕಟಿಸಿದ್ದನ್ನೇ ಚಲಾಯಿಸುತ್ತದೆ ಎಂದು ದೃಢೀಕರಿಸಲು:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ಇದು ಏನನ್ನು ಸಾಬೀತುಪಡಿಸುವುದಿಲ್ಲ: ಫೈಲ್ ಲೋಡ್ ಮಾಡುವ ಪುಟವನ್ನೂ ನಾವೇ ಸೇವೆ ಸಲ್ಲಿಸುತ್ತೇವೆ,
ಆದ್ದರಿಂದ ನಾವು ಬೇರೆ ಪುಟವನ್ನೂ ಸೇವೆ ಸಲ್ಲಿಸಬಹುದು. ಇಂಟೆಗ್ರಿಟಿ ಹ್ಯಾಶ್‌ಗಳು ನಿಮ್ಮನ್ನು ರಾಜಿಯಾದ
CDN ನಿಂದ ರಕ್ಷಿಸುತ್ತವೆ, ಮಾರಾಟಗಾರನಿಂದ ಅಲ್ಲ. ನೀವು ಗಳಿಸುವುದೇನೆಂದರೆ ಯಾವುದೇ ಪ್ರತಿಸ್ಥಾಪನೆ
ಉದ್ದೇಶಪೂರ್ವಕವಾಗಿರಬೇಕು, ಪುಟದ ಮೂಲದಲ್ಲಿ ಗೋಚರವಾಗಿರಬೇಕು, ಮತ್ತು ಯಾರಾದರೂ ಪಡೆಯಬಹುದಾದ
PyPI ಯಲ್ಲಿನ ಆರ್ಟಿಫ್ಯಾಕ್ಟ್‌ಗಿಂತ ಭಿನ್ನವಾಗಿರಬೇಕು. ಸ್ವಯಂ-ಹೋಸ್ಟಿಂಗ್ ಅಥವಾ ಸ್ಥಳೀಯ-ಮಾತ್ರ
ಉಳಿಯುವುದು ಈ ಅವಲಂಬನೆಯನ್ನೇ ಸಂಪೂರ್ಣವಾಗಿ ತೆಗೆದುಹಾಕುತ್ತದೆ.

## ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಿ

```bash
pip install clawmetry     # ನಂತರ: clawmetry
```

ಅಥವಾ ಒಂದೇ-ಸಾಲಿನ ಆವೃತ್ತಿ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ಅಥವಾ Windows ನಲ್ಲಿ Python 3.8+ ಬೇಕು, ಮತ್ತು ಅದೇ ಯಂತ್ರದಲ್ಲಿ ಕನಿಷ್ಠ
ಒಂದು ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್ ಬೇಕು. Docker ಸೂಚನೆಗಳು: [docs/DOCKER.md](docs/DOCKER.md).

ಅಥವಾ ಏಜೆಂಟ್ ಅನ್ನೇ ಅದನ್ನು ನಿಮಗಾಗಿ ಸೆಟಪ್ ಮಾಡಲು ಬಿಡಿ. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ಸ್ಕಿಲ್ Claude Code, Codex, Cursor, Gemini CLI, Copilot ಅಥವಾ OpenCode ಗೆ ClawMetry
ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಲು, ಯಂತ್ರದಲ್ಲಿನ ಏಜೆಂಟ್‌ಗಳು ಏನು ಮಾಡುತ್ತಿವೆ ಮತ್ತು ಎಷ್ಟು ಖರ್ಚು ಮಾಡುತ್ತಿವೆ
ಎಂಬುದನ್ನು ವರದಿ ಮಾಡಲು, ವಿನಂತಿಯ ಮೇರೆಗೆ ಒಂದು ಸೆಷನ್ ಅನ್ನು ನಿಲ್ಲಿಸಲು, ಮತ್ತು ಅಪಾಯಕಾರಿ
ಟೂಲ್ ಕರೆಗಳನ್ನು ಅನುಮೋದನೆಗಾಗಿ ಹಿಡಿದಿಟ್ಟುಕೊಳ್ಳಲು ಕಲಿಸುತ್ತದೆ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ದಾಖಲೆಗಳು

| | |
|---|---|
| [ರನ್‌ಟೈಮ್ ಹೊಂದಾಣಿಕೆ](docs/compatibility.md) | ಪ್ರತಿ ಅಡಾಪ್ಟರ್ ಏನನ್ನು ಓದುತ್ತದೆ, ಮತ್ತು ರನ್‌ಟೈಮ್ ಸೇರಿಸುವುದು ಹೇಗೆ |
| [ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್](docs/CONTEXT_BLOWOUT.md) | ಪ್ರತಿ-ಪ್ರೊವೈಡರ್ ವಿಂಡೋಗಳು, ಕಂಪ್ಯಾಕ್ಷನ್ ವರ್ಸಸ್ ಓವರ್‌ಫ್ಲೋ, ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ಕವರೇಜ್ |
| [ಓವರ್‌ಹೆಡ್](docs/OVERHEAD.md) | ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ನ ವೆಚ್ಚ ಏನು, ಅಳೆಯಲಾಗಿದೆ, ಅದನ್ನು ಮರುಉತ್ಪಾದಿಸುವ ಹಾರ್ನೆಸ್‌ನೊಂದಿಗೆ |
| [ಎಂಟೈಟಲ್‌ಮೆಂಟ್‌ಗಳು](docs/ENTITLEMENTS.md) | ಉಚಿತ ವರ್ಸಸ್ ಪಾವತಿಸಿದ, ಟಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, ಲೈಸೆನ್ಸ್ CLI |
| [ಅನುಮೋದನೆಗಳು ಮತ್ತು ನೀತಿಗಳು](docs/APPROVALS.md) | ಪ್ರೀ-ಎಕ್ಸಿಕ್ಯೂಶನ್ ಗೇಟಿಂಗ್, ಅಪಾಯ ಸ್ಕೋರಿಂಗ್, ಫೋನ್ ಅನುಮೋದನೆಗಳು |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ಎಲ್ಲಿಯಾದರೂ ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಕ್ಸ್‌ಪೋರ್ಟ್ ಮಾಡಿ, ಎಲ್ಲಿಂದಲಾದರೂ OTLP ಇಂಜೆಸ್ಟ್ ಮಾಡಿ |
| [ನಿಮ್ಮ ಸ್ವಂತ ಏಜೆಂಟ್ ತನ್ನಿ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ಸಂಪೂರ್ಣವಾಗಿ, ಚಲಾಯಿಸಬಹುದಾದ ಉದಾಹರಣೆಗಳೊಂದಿಗೆ |
| [SDK ಟ್ರ್ಯಾಕಿಂಗ್](docs/SDK_TRACKING.md) | ನೀವೇ ನಿರ್ಮಿಸಿದ ಏಜೆಂಟ್‌ಗಳಿಗೆ ವೆಚ್ಚ ಗುಣಾತ್ಮಕತೆ |
| [ಚಾಟ್ ಚಾನೆಲ್‌ಗಳು](docs/CHANNELS.md) | ಫ್ಲೋನಲ್ಲಿ ತೋರಿಸಲಾದ ಚಾಟ್ ಅಡಾಪ್ಟರ್‌ಗಳು |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಡಿದ NVIDIA NemoClaw ಸೆಟಪ್‌ಗಳು |
| [Docker](docs/DOCKER.md) | ಇಮೇಜ್, ಕಂಪೋಸ್, ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು |
| [ಆರ್ಕಿಟೆಕ್ಚರ್](ARCHITECTURE.md) · [ಡೆವಲಪ್‌ಮೆಂಟ್](docs/DEVELOPMENT.md) | ಇದು ಒಳಗೆ ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ; ಮೂಲದಿಂದ ಚಲಾಯಿಸುವುದು |
| [ಟೆಲಿಮೆಟ್ರಿ](docs/TELEMETRY.md) | ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಮತ್ತು ಡೆಸ್ಕ್‌ಟಾಪ್-ಓಪನ್ ಪಿಂಗ್‌ಗಳು, ಮತ್ತು ಅವುಗಳನ್ನು ಆಫ್ ಮಾಡುವುದು ಹೇಗೆ |

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

ಕೆಳಗಿನ ಪ್ರತಿ ಸಂಖ್ಯೆಯೂ ಒಂದು ನೈಜ ಯಂತ್ರದಿಂದ, ರೀಡ್-ಓನ್ಲಿ ಆಗಿ, ಏನನ್ನೂ ಬಿತ್ತದೆ ಬಂದಿದೆ.

**ಏನಾದರೂ ತಪ್ಪಾದಾಗ ಅದು ನಿಮಗೆ ಹೇಳುತ್ತದೆ, ಕೇವಲ ಏನಾಯಿತು ಎಂಬುದನ್ನಷ್ಟೇ ಅಲ್ಲ.**
ಮೇಲ್ಭಾಗದಲ್ಲಿ ಎರಡು ಅಸಂಗತತೆ ಬ್ಯಾನರ್‌ಗಳು: ದೈನಂದಿನ ಸರಾಸರಿಯ 7 ಪಟ್ಟು ಖರ್ಚು ಚಲಿಸುತ್ತಿದೆ,
ಮತ್ತು 4.2 ಪಟ್ಟು ವೆಚ್ಚ ಏರಿಕೆ. ಅವುಗಳ ಕೆಳಗೆ, ಇತ್ತೀಚಿನ 667 ಸೆಷನ್‌ಗಳಲ್ಲಿ 324, ಕಾರಣದಿಂದ
ಪಟ್ಟಿ ಮಾಡಲಾದ, ವ್ಯರ್ಥ ಸಂಕೇತವನ್ನು ಹೊತ್ತಿವೆ.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ಇದು ಪ್ರತಿ ವಿಂಡೋದಲ್ಲಿ ಹಣ ಎಲ್ಲಿಗೆ ಹೋಯಿತು ಎಂಬುದನ್ನು ತೋರಿಸುತ್ತದೆ.**
ಇಂದು $252.47, ಈ ವಾರ $513.15, ಈ ತಿಂಗಳು $1,312.92, ಪ್ರತಿಯೊಂದೂ ಅದರ ಹಿಂದಿನ
ಟೋಕನ್‌ಗಳೊಂದಿಗೆ ಮತ್ತು ನಿಮ್ಮ ಸಬ್‌ಸ್ಕ್ರಿಪ್ಷನ್ ಈಗಾಗಲೇ ಎಷ್ಟನ್ನು ಒಳಗೊಂಡಿದೆ ಎಂಬುದರೊಂದಿಗೆ.
ಅದರ ಕೆಳಗೆ, ಸುಮಾರು $1,128/ತಿಂಗಳು ಮರುಪಡೆಯಬಹುದಾದುದಾಗಿ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ ಮತ್ತು ಕ್ಯಾಶ್
ಮರುಬಳಕೆಯಿಂದ ಈಗಾಗಲೇ $17,256/ತಿಂಗಳು ಉಳಿಸಲಾಗಿದೆ.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ಒಂದು ಸಂದೇಶ ಹೇಗೆ ಉತ್ತರವಾಗುತ್ತದೆ ಎಂಬುದನ್ನು ಇದು ಚಿತ್ರಿಸುತ್ತದೆ.**
ಲೈವ್ ಫ್ಲೋ ಡಯಾಗ್ರಾಂ: ನೀವು, ಅದು ಬಂದ ಚಾನೆಲ್, ಗೇಟ್‌ವೇ, ಈಗ ಉತ್ತರಿಸುತ್ತಿರುವ ಮಾಡೆಲ್,
ಮತ್ತು ಅದು ತಲುಪಿದ ಪ್ರತಿ ಟೂಲ್. ಕೆಲಸ ಅವುಗಳ ಮೂಲಕ ಚಲಿಸುತ್ತಿದ್ದಂತೆ ನೋಡ್‌ಗಳು ಬೆಳಗುತ್ತವೆ.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ಯಂತ್ರದಲ್ಲಿನ ಪ್ರತಿ ಏಜೆಂಟ್, ಒಂದೇ ಟೇಬಲ್‌ನಲ್ಲಿ.**
ಅದು ಏನನ್ನು ಚಲಾಯಿಸುತ್ತದೆ, ಕಳೆದ 24 ಗಂಟೆಗಳಲ್ಲಿ ಮತ್ತು ತನ್ನ ಜೀವಿತಾವಧಿಯಲ್ಲಿ ಅದು ಎಷ್ಟು
ಖರ್ಚು ಮಾಡುತ್ತದೆ, ಅದನ್ನು ಕೊನೆಯದಾಗಿ ಯಾವಾಗ ನೋಡಲಾಯಿತು, ಯಾರು ಅದನ್ನು ಹೊಂದಿದ್ದಾರೆ,
ಮತ್ತು ಸಬ್‌ಸ್ಕ್ರಿಪ್ಷನ್ ಬಿಲ್ ಅನ್ನು ಆವರಿಸುತ್ತಿದೆಯೇ ಎಂಬುದನ್ನು. ಇಲ್ಲಿ 14 ಏಜೆಂಟ್‌ಗಳು, 3
ಸೆಷನ್‌ಗಳು ಕೆಲಸ ಮಾಡುತ್ತಿವೆ, 13 ಮೌನವಾಗಿವೆ.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ಒಂದು ಸರದಿಯ ಸಮಯ ಮತ್ತು ಹಣ ಎಲ್ಲಿಗೆ ಹೋಯಿತು ಎಂಬುದನ್ನು ಇದು ಟೂಲ್-ಬೈ-ಟೂಲ್ ತೋರಿಸುತ್ತದೆ.**
ಒಂದು ನೈಜ ಸೆಷನ್‌ನ ಒಂದು ಸರದಿ: $1.16 ಗೆ 11.2 ನಿಮಿಷಗಳಲ್ಲಿ 11 ಟೂಲ್‌ಗಳು. ಪ್ರತಿ Bash
ಕರೆ ಮತ್ತು ಮಾಡೆಲ್ ಕರೆಗೆ ಟೈಮ್‌ಲೈನ್‌ನಲ್ಲಿ ತನ್ನದೇ ಬಾರ್ ಸಿಗುತ್ತದೆ, ಆದ್ದರಿಂದ 4.1 ನಿಮಿಷ
ಚಲಿಸಿದ ಕಮಾಂಡ್ ಮತ್ತು 226ms ಚಲಿಸಿದ ಕಮಾಂಡ್ ಒಂದೇ ನೋಟಕ್ಕೆ ಪ್ರತ್ಯೇಕಿಸಲಾಗುತ್ತದೆ.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ಇದು ಕೇವಲ ಖರ್ಚನ್ನಷ್ಟೇ ಅಲ್ಲ, ಕೆಲಸವನ್ನೂ ಗ್ರೇಡ್ ಮಾಡುತ್ತದೆ.**
ಈ ವಾರ A: 54 ಕಾರ್ಯಗಳು ಸ್ವಚ್ಛವಾಗಿ ಮರಳಿ ಬಂದವು, 2 ಒರಟಾದವು $48.57 ಖರ್ಚಾದವು, ಮತ್ತು
ನಿರ್ಣಯಿಸಲು ಸಾಕಷ್ಟು ಚಟುವಟಿಕೆ ಇಲ್ಲದ ರನ್‌ಗಳನ್ನು ಗೆಲುವುಗಳೆಂದು ಎಣಿಸುವ ಬದಲು ಗ್ರೇಡ್‌ನಿಂದ
ಹೊರಗಿಡಲಾಗಿದೆ. ಪ್ರತಿ ಒರಟಾದ ರನ್ ತನ್ನ ಟ್ರೇಸ್‌ಗೆ ಲಿಂಕ್ ಆಗುತ್ತದೆ.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ಕಾಂಟೆಕ್ಸ್ಟ್ ವಿಂಡೋ ಏಕೆ ತುಂಬುತ್ತಲೇ ಇರುತ್ತದೆ ಎಂಬುದನ್ನು ಇದು ತೋರಿಸುತ್ತದೆ.**
ಇತ್ತೀಚಿನ ಸರದಿಯಲ್ಲಿ 1M-ಟೋಕನ್ ವಿಂಡೋದ 715K, 83.3% ಗರಿಷ್ಠ, ಓವರ್‌ಫ್ಲೋ ಬದಲಿಗೆ ಎಲ್ಲಾ
4 ಕಂಪ್ಯಾಕ್ಷನ್‌ಗಳೂ ಪೂರ್ವಭಾವಿಯಾಗಿ ಫೈರ್ ಆದವು, ಜೊತೆಗೆ ಅದರ ಹಿಂದಿನ ಪ್ರತಿ ಸರದಿಯ ಬಳಕೆ.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ನೀವು ಏನನ್ನೂ ಕಾನ್ಫಿಗರ್ ಮಾಡದೆಯೇ ಪತ್ತೆಹಚ್ಚುವಿಕೆ ಚಲಿಸುತ್ತದೆ.**
ಇನ್‌ಬಿಲ್ಟ್ ಡಿಟೆಕ್ಟರ್‌ಗಳು ಇನ್‌ಸ್ಟಾಲ್‌ನಿಂದಲೇ ಆನ್ ಆಗಿವೆ: ಏಜೆಂಟ್ ಮೌನವಾಯಿತು, ಟೆಲಿಮೆಟ್ರಿ ಫೀಡ್
ನಿಂತಿತು, ವೆಚ್ಚ ಏರಿಕೆ, ಟೋಕನ್ ಸ್ಫೋಟ, ದೋಷಗಳು ಏರುತ್ತಿವೆ, ದೋಷ ಏರಿಕೆ, ಬಜೆಟ್ ಮಿತಿ,
ಬೆದರಿಕೆ ಸಹಿ ಹೊಂದಾಣಿಕೆಯಾಗಿದೆ, ಭದ್ರತಾ ಟೂಲ್ ಸಂಶೋಧನೆ, ಭದ್ರತಾ ಭಂಗಿ ಬದಲಾಗಿದೆ. ಇವುಗಳ
ಮೇಲೆ ನಿಮ್ಮ ಸ್ವಂತ ನಿಯಮಗಳು ಐಚ್ಛಿಕ.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ಅಪಾಯಕಾರಿ ಕರೆಯನ್ನು ಹಿಡಿದಿಟ್ಟುಕೊಳ್ಳುವುದು ಆಪ್ಟ್-ಇನ್ ಆಗಿದೆ, ಮತ್ತು ಆಫ್ ಆಗಿಯೇ ಬರುತ್ತದೆ.**
ರಿಕರ್ಸಿವ್ ಡಿಲೀಟ್‌ಗಳು, ಫೋರ್ಸ್ ಪುಶ್‌ಗಳು, sudo, ಸೀಕ್ರೆಟ್‌ಗಳು, ಪ್ಯಾಕೇಜ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು ಮತ್ತು
ಔಟ್‌ಬೌಂಡ್ ಕರೆಗಳು ಪ್ರತಿಯೊಂದೂ ನೀವು ಆನ್ ಮಾಡಬಹುದಾದ ನಿಯಮವನ್ನು ಪಡೆಯುತ್ತವೆ. ನೀವು
ಮಾಡುವವರೆಗೂ, ClawMetry ವೀಕ್ಷಿಸುತ್ತದೆ ಮತ್ತು ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ. ಒಮ್ಮೆ ಒಂದು
ಆನ್ ಆದ ಮೇಲೆ, ಹೊಂದಾಣಿಕೆಯಾಗುವ ಕರೆಗಳು ಇಲ್ಲಿ (ಅಥವಾ ನಿಮ್ಮ ಫೋನ್‌ನಲ್ಲಿ) ಅನುಮೋದನೆ ಅಥವಾ
ನಿರಾಕರಣೆಗಾಗಿ ಕಾಯುತ್ತವೆ.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ಹೆಚ್ಚು, ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## ಮನ್ನಣೆ

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## ಸ್ಟಾರ್ ಇತಿಹಾಸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ಲೈಸೆನ್ಸ್

MIT · [@vivekchand](https://github.com/vivekchand) ರಿಂದ ನಿರ್ಮಿಸಲಾಗಿದೆ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
