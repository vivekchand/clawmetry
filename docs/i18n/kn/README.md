<!-- i18n-src:a855a14295b0 -->
> ಕನ್ನಡ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ಒಂದು ಏಜೆಂಟ್ ಪ್ರಗತಿ ಸಾಧಿಸದೆಯೇ ನೂರು ಟೂಲ್ ಕರೆಗಳನ್ನು ಮಾಡಬಹುದು.** ClawMetry ನಿಮ್ಮ ಕೋಡಿಂಗ್ ಏಜೆಂಟ್‌ಗಳು ಈಗಾಗಲೇ ಬರೆಯುವ ಸೆಷನ್ ಫೈಲ್‌ಗಳನ್ನು ಓದುತ್ತದೆ, ಮತ್ತು ಟೈಮ್‌ಲೈನ್, ಟೂಲ್ ಕರೆಗಳು, ಹಾಗೂ ರನ್‌ಟೈಮ್ ಬಹಿರಂಗಪಡಿಸುವ ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚದ ಡೇಟಾವನ್ನು ಒಂದೇ ವೀಕ್ಷಣೆಯಲ್ಲಿ ತರುತ್ತದೆ — ಇದರಿಂದ ಕೆಲಸ ಮಾಡುತ್ತಿರುವ ದೀರ್ಘ ರನ್ ಮತ್ತು ಸಿಲುಕಿಕೊಂಡಿರುವ ರನ್ ನಡುವಿನ ವ್ಯತ್ಯಾಸವನ್ನು ನೀವು ಗುರುತಿಸಬಹುದು.

**32 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ** ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ — Claude Code, OpenAI Codex, Hermes, OpenClaw ಮತ್ತು ಇನ್ನೂ 28. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್. ([ಸಂಪೂರ್ಣ ಪಟ್ಟಿ](SUPPORTED_RUNTIMES.txt), ಕ್ಯಾಟಲಾಗ್‌ನಿಂದ ಉತ್ಪತ್ತಿಯಾಗಿದೆ.)

> 🌐 **ಇದನ್ನು ಇಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದೇ ಕಮಾಂಡ್. ಶೂನ್ಯ ಕಾನ್ಫಿಗರೇಶನ್. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆಯುತ್ತದೆ. ಶೂನ್ಯ ಕಾನ್ಫಿಗರೇಶನ್: ನೀವು ಈಗಾಗಲೇ ಹೊಂದಿರುವ ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಇದು ಕಂಡುಹಿಡಿಯುತ್ತದೆ, ಅವುಗಳನ್ನು ಓದಲು-ಮಾತ್ರ ಓದುತ್ತದೆ, ಮತ್ತು ಅವು ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತವೆ ಎಂಬುದರಲ್ಲಿ ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡುವ ಮೊದಲು

| | |
|---|---|
| **ಇದು ಏನು ಮಾಡುತ್ತದೆ** | ನಿಮ್ಮ ಏಜೆಂಟ್‌ಗಳು ಈಗಾಗಲೇ ಬರೆಯುವ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಮತ್ತು ಲಾಗ್‌ಗಳನ್ನು ಓದುತ್ತದೆ. ಯಾವುದೇ SDK ಇಲ್ಲ, ಕೋಡ್ ಬದಲಾವಣೆ ಇಲ್ಲ, ನಿಮ್ಮ ಅಪ್ಲಿಕೇಶನ್‌ನಲ್ಲಿ ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್ ಇಲ್ಲ. |
| **ನೀವು ಏನನ್ನು ನೋಡುತ್ತೀರಿ** | ಸೆಷನ್ ಟೈಮ್‌ಲೈನ್, ಟೂಲ್-ಬೈ-ಟೂಲ್ ರೀಪ್ಲೇ, ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚದ ವಿಶ್ಲೇಷಣೆ, ಮತ್ತು ಪಥ ಸಂಕೇತಗಳು (ಲೂಪಿಂಗ್, ಪುನರಾವರ್ತಿತ ವೈಫಲ್ಯಗಳು) — ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ. |
| **ಏನು ಉಚಿತ** | `pip install clawmetry` ಯಾವುದೇ ಖಾತೆ, ಕೀ ಅಥವಾ ನೆಟ್‌ವರ್ಕ್ ಕರೆ ಇಲ್ಲದೆ **OpenClaw, NVIDIA NemoClaw ಮತ್ತು Goose** ಅನ್ನು ಓದುತ್ತದೆ. ಇತರ 27 — Claude Code, Codex, Cursor ಮತ್ತು ಉಳಿದವು — ಕ್ಲೋಸ್ಡ್-ಸೋರ್ಸ್ `clawmetry-pro` ಸಂಗಾತಿಯ ಮೂಲಕ ಓದಲ್ಪಡುತ್ತವೆ, ಇದು 7-ದಿನದ ಟ್ರಯಲ್ ಅಥವಾ ಪ್ಲಾನ್‌ನೊಂದಿಗೆ ಬರುತ್ತದೆ — ನಿಖರವಾದ ವಿಭಜನೆಗಾಗಿ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ನೋಡಿ. |
| **ಹೇಗೆ ಪ್ರಾರಂಭಿಸುವುದು** | `pip install clawmetry && clawmetry`, ನಂತರ localhost:8900 ತೆರೆಯಿರಿ. ಈ ಯಂತ್ರದಲ್ಲಿ ಇನ್ನೂ ಯಾವುದೇ ಏಜೆಂಟ್‌ಗಳಿಲ್ಲವೇ? `clawmetry --sample` ಮೂರು ಲೇಬಲ್ ಮಾಡಿದ ಸಿಂಥೆಟಿಕ್ ಸೆಷನ್‌ಗಳ ಮೇಲೆ ತೆರೆಯುತ್ತದೆ. |
| **ನಿಮ್ಮ ಯಂತ್ರದಿಂದ ಏನು ಹೊರಹೋಗುತ್ತದೆ** | ನೀವು `clawmetry connect` ಚಲಾಯಿಸದ ಹೊರತು ಯಾವುದೇ ಸೆಷನ್ ಡೇಟಾ ಇಲ್ಲ. ಡೀಫಾಲ್ಟ್ ಆಗಿ ಎರಡು ವಿಷಯಗಳು ಚಲಿಸುತ್ತವೆ, ಎರಡೂ ಆಪ್ಟ್-ಔಟ್ ಮತ್ತು ಯಾವುದೂ ಸೆಷನ್ ವಿಷಯವನ್ನು ಹೊಂದಿರುವುದಿಲ್ಲ: ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಪಿಂಗ್ ಮತ್ತು PyPI ಆವೃತ್ತಿ ತಪಾಸಣೆ. ಪ್ರತಿಯೊಂದು ಗಮ್ಯಸ್ಥಾನವನ್ನೂ [docs/EGRESS.md](docs/EGRESS.md) ನಲ್ಲಿ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ, ಕಾಮೆಂಟ್‌ಗಳನ್ನು ಓದುವ ಬದಲು ವೈರ್ ಕ್ಯಾಪ್ಚರ್‌ನಿಂದ ಪುನಃ ನಿರ್ಮಿಸಲಾಗಿದೆ. |

ನೀವು ಔಟ್‌ಪುಟ್ ಅನ್ನು ನಿರ್ಣಯಿಸುವ ಮೊದಲು ತಿಳಿಯಬೇಕಾದ ಎರಡು ಮಿತಿಗಳು: ರನ್‌ಟೈಮ್‌ಗಳು ಬಹಳ ವಿಭಿನ್ನ ಡೇಟಾವನ್ನು ಬಹಿರಂಗಪಡಿಸುತ್ತವೆ (ಕೆಲವು ಯಾವುದೇ ವೆಚ್ಚವನ್ನೇ ಪ್ರಕಟಿಸುವುದಿಲ್ಲ — [ಮ್ಯಾಟ್ರಿಕ್ಸ್](docs/compatibility.md) ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ ಯಾವುದು ಎಂಬುದನ್ನು ಹೇಳುತ್ತದೆ), ಮತ್ತು ಕ್ರಿಯೆಯನ್ನು ಗಮನಿಸುವುದು ಅದನ್ನು ತಡೆಯಲು ಸಾಧ್ಯವಾಗುವುದಕ್ಕೆ ಸಮಾನವಲ್ಲ ([ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ ಯಾವ ನಿಯಂತ್ರಣಗಳು ನಿಜವಾಗಿವೆ](docs/APPROVALS.md)).


## 32 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

**ಓಪನ್ ಸೋರ್ಸ್ ಅಪ್ಲಿಕೇಶನ್‌ನಲ್ಲಿ ಉಚಿತ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ಪಾವತಿಸಿದ ಪ್ಲಾನ್‌ನಲ್ಲಿ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ಪ್ರತಿಯೊಂದು ರನ್‌ಟೈಮ್‌ಗೂ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಸಿಗುತ್ತದೆ. ಹಲವನ್ನು ಒಟ್ಟಿಗೆ ಚಲಾಯಿಸಿ ಮತ್ತು ಹೆಡರ್ ಸ್ವಿಚರ್ ಪ್ರತಿ ಟ್ಯಾಬ್ ಅನ್ನು ಅವುಗಳಲ್ಲಿ ಒಂದಕ್ಕೆ ಮರುಸ್ಕೋಪ್ ಮಾಡುತ್ತದೆ.

SDK ಬಳಸಿ ನಿಮ್ಮ ಸ್ವಂತ ಏಜೆಂಟ್ ಅನ್ನು ನಿರ್ಮಿಸಿದ್ದೀರಾ? ಇಂಟರ್ಸೆಪ್ಟರ್ ಅದರ LLM ಕರೆಗಳನ್ನೂ ಟ್ರ್ಯಾಕ್ ಮಾಡುತ್ತದೆ. ನೋಡಿ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **ಸೆಷನ್‌ಗಳು ಮತ್ತು ಟ್ರಾನ್ಸ್‌ಸ್ಕ್ರಿಪ್ಟ್‌ಗಳು**: ಪ್ರತಿ ಏಜೆಂಟ್ ಏನು ಮಾಡಿದೆ, ಟರ್ನ್ ಬೈ ಟರ್ನ್, ರೀಪ್ಲೇ ಸಮೇತ
- **ವೆಚ್ಚ ಮತ್ತು ಟೋಕನ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್, ಮಾದರಿ, ಸೆಷನ್ ಮತ್ತು ದಿನಕ್ಕೆ, ಅಸಂಗತತೆಯ ಫ್ಲ್ಯಾಗ್‌ಗಳೊಂದಿಗೆ
- **ಫ್ಲೋ**: ಚಾನೆಲ್‌ಗಳು, ಮಾದರಿಗಳು ಮತ್ತು ಟೂಲ್‌ಗಳ ಮೂಲಕ ಚಲಿಸುವ ಸಂದೇಶಗಳ ಲೈವ್ ಡಯಾಗ್ರಾಂ
- **ಬ್ರೈನ್**: ತರ್ಕ ಮತ್ತು ಟೂಲ್-ಕರೆ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್ ಅದು ಸಂಭವಿಸಿದಂತೆ
- **ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್**: ಪ್ರತಿ ಪೂರೈಕೆದಾರರಿಗೆ ಗಾತ್ರ ನಿಗದಿಪಡಿಸಿದ ವಿಂಡೋ ಬಳಕೆ, ಕಂಪ್ಯಾಕ್ಷನ್ ವರ್ಸಸ್ ಬಲವಂತದ ಓವರ್‌ಫ್ಲೋ, ಜೊತೆಗೆ ನಾವು ಏನನ್ನು *ನೋಡಲಾಗುವುದಿಲ್ಲ* ಎಂಬುದರ ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ನಕ್ಷೆ ([ಹೇಗೆ](docs/CONTEXT_BLOWOUT.md))
- **ಮೆಮೊರಿ ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್ ವಾಸ್ತವವಾಗಿ ಲೋಡ್ ಮಾಡಿದ ಫೈಲ್‌ಗಳು ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು
- **ಆರೋಗ್ಯ ಮತ್ತು ಲಾಗ್‌ಗಳು**: ಡಿಸ್ಕ್, ಮೆಮೊರಿ, ದೋಷ ದರಗಳು, ದರ ಮಿತಿಗಳು, ಲೈವ್ ಲಾಗ್ ಸ್ಟ್ರೀಮ್
- **ಎಚ್ಚರಿಕೆಗಳು**: ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ ಸ್ಪೈಕ್‌ಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್, Slack, Discord, PagerDuty, Telegram, Email ಗೆ ರೂಟ್ ಮಾಡಲಾಗಿದೆ
- **ಅನುಮೋದನೆಗಳು**: ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅವು ಚಲಿಸುವ *ಮೊದಲು* ವಿರಾಮಗೊಳಿಸಿ ಮತ್ತು ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಅನುಮೋದಿಸಿ ([ಹೇಗೆ](docs/APPROVALS.md))

## ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್, ಮತ್ತು ಗಮನಿಸುವುದರ ವೆಚ್ಚ

ಯಾವುದೇ ಏಜೆಂಟ್-ಹೋಲಿಕೆ ಟೂಲ್ ಅನ್ನು ನಂಬುವ ಮೊದಲು ಉತ್ತರಿಸಬೇಕಾದ ಎರಡು ಪ್ರಶ್ನೆಗಳು.

**ಇದು ರನ್‌ಟೈಮ್‌ಗಳಾದ್ಯಂತ ಕಾಂಟೆಕ್ಸ್ಟ್-ವಿಂಡೋ ಬ್ಲೋಔಟ್ ಅನ್ನು ಹೇಗೆ ನಿಭಾಯಿಸುತ್ತದೆ?**

ಬಳಕೆಯ ಶೇಕಡಾವಾರು ಪ್ರಮಾಣವು ಅದನ್ನು ಯಾವುದರಿಂದ ಭಾಗಿಸಲಾಗಿದೆ ಎಂಬುದರಷ್ಟೇ ಪ್ರಾಮಾಣಿಕವಾಗಿರುತ್ತದೆ. ClawMetry ಪ್ರತಿ ಪೂರೈಕೆದಾರರಿಗೆ ವಿಂಡೋ ಗಾತ್ರವನ್ನು ನೀವು ಓದಿ PR ಮಾಡಬಹುದಾದ [ಒಂದು ಟೇಬಲ್](clawmetry/context_windows.py) ನಿಂದ ನಿಗದಿಪಡಿಸುತ್ತದೆ, ಇದು Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama ಮತ್ತು GLM ಅನ್ನು ಒಳಗೊಂಡಿದೆ. ಇದು ಎಲ್ಲಾ 32 ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಒಂದೇ ವೆಂಡರ್‌ನ ಅಳತೆಗೋಲಿನಿಂದ ಅಳೆಯುವುದಿಲ್ಲ. ಇದು ಮುಖ್ಯ: ಒಂದು 300K GPT-5 ಟರ್ನ್ ಅನ್ನು Anthropic ನ 200K ವಿರುದ್ಧ ಸ್ಕೋರ್ ಮಾಡಿದಾಗ ">100%, ಬ್ಲೋನ್" ಎಂದು ಓದುತ್ತದೆ, ಆದರೆ ಅದು ವಾಸ್ತವವಾಗಿ GPT-5 ನ 400K ನ 75% ರಷ್ಟಿದೆ. ಅದೇ ಅಳತೆಗೋಲು ನಿಜವಾಗಿ ಓವರ್‌ಫ್ಲೋ ಆಗಿರುವ 130K DeepSeek ಟರ್ನ್ ಅನ್ನು ಆರಾಮದಾಯಕ 65% ಎಂದು ಮರೆಮಾಚುತ್ತದೆ.

ಪ್ರತಿ ವಿಂಡೋ ಅದರ ಮೂಲದೊಂದಿಗೆ ಬರುತ್ತದೆ: `model_table`, `explicit_marker`, `observed_floor`, ಅಥವಾ ನಮಗೆ ಮಾದರಿ ತಿಳಿದಿಲ್ಲದಿದ್ದಾಗ ಪ್ರಾಮಾಣಿಕ `default`. ಊಹೆಯ ಮೇಲೆ ನಿರ್ಮಿಸಲಾದ ಗೇಜ್ ಎಂದಿಗೂ ಲುಕ್‌ಅಪ್‌ನ ಮೇಲೆ ನಿರ್ಮಿಸಲಾದ ಒಂದರಂತೆ ಅದೇ ಅಧಿಕಾರದೊಂದಿಗೆ ರೆಂಡರ್ ಆಗುವುದಿಲ್ಲ.

ClawMetry ಕೆಲವು ರನ್‌ಟೈಮ್‌ಗಳಲ್ಲಿ ಮಾತ್ರ ಕಂಪ್ಯಾಕ್ಷನ್ ಈವೆಂಟ್‌ಗಳನ್ನು ನೋಡಬಲ್ಲದು. ಆದ್ದರಿಂದ `GET /api/context-coverage` ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ ವರದಿ ಮಾಡುತ್ತದೆ, **ಶೂನ್ಯ ಎಂದರೆ "ಸ್ವಚ್ಛವಾಗಿ ಓಡಿತು" ಅಥವಾ "ನಮಗೆ ಕುರುಡಾಗಿದೆ"** ಎಂಬುದನ್ನು. ವಾಸ್ತವವಾಗಿ ಕುರುಡಾಗಿದೆ ಎಂದರ್ಥ ಮಾಡುವ `0` ಹಾಗೆಯೇ ಹೇಳುತ್ತದೆ.
[ಸಂಪೂರ್ಣ ವಿವರ](docs/CONTEXT_BLOWOUT.md)

**ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ಗೆ ಎಷ್ಟು ವೆಚ್ಚವಾಗುತ್ತದೆ?**

| ಪಥ | ನಿಮ್ಮ ಏಜೆಂಟ್‌ಗೆ ಸೇರಿಸಲಾಗಿದೆ | ಡೀಫಾಲ್ಟ್? |
|---|---|---|
| ಸೆಷನ್-ಫೈಲ್ ಟೈಲಿಂಗ್ (ಎಲ್ಲಾ 32 ರನ್‌ಟೈಮ್‌ಗಳು) | **0**. ಪ್ರತ್ಯೇಕ ಪ್ರಕ್ರಿಯೆ, ನಿಮ್ಮ ಏಜೆಂಟ್‌ನಲ್ಲಿ ClawMetry ಕೋಡ್ ಇಲ್ಲ | ಆನ್ |
| HTTP ಇಂಟರ್ಸೆಪ್ಟರ್ (`CLAWMETRY_INTERCEPT=1`) | ಪ್ರತಿ LLM ಕರೆಗೆ **+0.44 ms**, ಅಥವಾ 5s ಕರೆಯ 0.009% | ಆಫ್ |
| ಪ್ರೀ-ಟೂಲ್ ಹುಕ್ ಗೇಟ್ (ಬೆಚ್ಚಗಿನ ಕ್ಯಾಶ್) | 36 ms ಇಂಟರ್ಪ್ರಿಟರ್ ಫ್ಲೋರ್‌ಗಿಂತ ಪ್ರತಿ ಗೇಟೆಡ್ ಟೂಲ್ ಕರೆಗೆ **+44 ms** | ಆಫ್ |
| ಎನ್‌ಫೋರ್ಸ್‌ಮೆಂಟ್ ಪ್ರಾಕ್ಸಿ | ಪ್ರತಿ LLM ಕರೆಗೆ **+9.7 ms** | ಆಫ್ |

ಡೀಮನ್ ಹೋಸ್ಟ್ ವೆಚ್ಚ: **2,762 ಈವೆಂಟ್‌ಗಳು/ಸೆಕೆಂಡು** ಇಂಜೆಸ್ಟ್, ಡಿಸ್ಕ್‌ನಲ್ಲಿ **710 ಬೈಟ್‌ಗಳು/ಈವೆಂಟ್** (100k ಈವೆಂಟ್‌ಗಳಿಗೆ 67.7 MB), ಮತ್ತು ಬ್ಯುಸಿ ಇನ್‌ಸ್ಟಾಲ್‌ನಲ್ಲಿ ಸಸ್ಟೇನ್ಡ್ ಆಗಿ **ಒಂದು ಕೋರ್‌ನ ~12%**. ಆ ಕೊನೆಯ ಸಂಖ್ಯೆ ನಮ್ಮದೇ ಘೋಷಿತ 5-10% ಬಜೆಟ್‌ಗಿಂತ ಹೆಚ್ಚಿದೆ, ಆದ್ದರಿಂದ ಇದನ್ನು ಪುಟದಿಂದ ಬಿಟ್ಟುಬಿಡುವ ಬದಲು ಬೆನ್ನಟ್ಟಬೇಕಾದ ಬಗ್ ಆಗಿ ಪ್ರಕಟಿಸಲಾಗಿದೆ.

Apple M2 Pro ನಲ್ಲಿ `benchmarks/overhead.py` ಬಳಸಿ ಅಳೆಯಲಾಗಿದೆ. ಹಾರ್ನೆಸ್ ಪ್ರತಿ ಸ್ಥಿತಿಯನ್ನು ಪ್ರತ್ಯೇಕ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿ ಚಲಾಯಿಸುತ್ತದೆ, ಅವುಗಳ ಕ್ರಮವನ್ನು ಪರ್ಯಾಯವಾಗಿ ಬದಲಾಯಿಸುತ್ತದೆ, ಮತ್ತು **ಸುತ್ತುಗಳು ಅದರ ಚಿಹ್ನೆಯ ಬಗ್ಗೆ ಒಪ್ಪದಿದ್ದಾಗ ಸಂಖ್ಯೆಯನ್ನು ಮುದ್ರಿಸಲು ನಿರಾಕರಿಸುತ್ತದೆ**. ಒಂದು ನಿಮಿಷದಲ್ಲಿ ನಿಮ್ಮ ಸ್ವಂತ ಯಂತ್ರದಲ್ಲಿ ಇದನ್ನು ಚಲಾಯಿಸಿ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ಪ್ರತಿ ಪಥವನ್ನೂ ಅಳೆಯಲಾಗುತ್ತದೆ, ಹುಕ್ ಗೇಟ್‌ಗಳು ಮತ್ತು ಎನ್‌ಫೋರ್ಸ್‌ಮೆಂಟ್ ಪ್ರಾಕ್ಸಿ ಸೇರಿದಂತೆ, ಮತ್ತು ಹಾರ್ನೆಸ್ CI ನಲ್ಲಿ Linux, macOS ಮತ್ತು Windows ನಲ್ಲಿ ಚಲಾಯಿಸುತ್ತದೆ. ತಿಳಿಯಬೇಕಾದ ಎರಡು ಫಲಿತಾಂಶಗಳು: Windows ನಲ್ಲಿ ಪ್ರಾಕ್ಸಿ Linux ಗಿಂತ ಸುಮಾರು ಏಳು ಪಟ್ಟು ಹೆಚ್ಚು ವೆಚ್ಚ ಮಾಡುತ್ತದೆ, ಮತ್ತು ಡೀಮನ್ ಪ್ರಸ್ತುತ ಒಂದು ಕೋರ್‌ನ ಸುಮಾರು 12% ಅನ್ನು ಸಸ್ಟೇನ್ ಮಾಡುತ್ತದೆ, ನಮ್ಮದೇ 5-10% ಬಜೆಟ್‌ಗಿಂತ ಹೆಚ್ಚು. ಕಚ್ಚಾ JSON, ವಿಧಾನ, ಮತ್ತು ಇನ್ನೂ ಅಳೆಯದಿರುವುದು [docs/OVERHEAD.md](docs/OVERHEAD.md) ನಲ್ಲಿದೆ.

## ಬೆಲೆ ನಿಗದಿ

| ಪ್ಲಾನ್ | ಇದು ಏನನ್ನು ಒಳಗೊಳ್ಳುತ್ತದೆ | ಬೆಲೆ |
|---|---|---|
| **ಉಚಿತ** | OpenClaw + NVIDIA NemoClaw + Goose, ಸಂಪೂರ್ಣ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್, ಸ್ಥಳೀಯ ಮಾತ್ರ | $0 |
| **ಸ್ಟಾರ್ಟರ್** | ಮೇಲಿನ ಪ್ರತಿಯೊಂದು ಇತರ ರನ್‌ಟೈಮ್, ಫ್ಲೀಟ್ ವೀಕ್ಷಣೆ, ಕ್ಲೌಡ್ ಸಿಂಕ್ | ತಿಂಗಳಿಗೆ ಪ್ರತಿ ನೋಡ್‌ಗೆ $9 |
| **Pro** | ಸ್ಟಾರ್ಟರ್ + ನಿಯಂತ್ರಣ ಮತ್ತು ಮೌಲ್ಯಮಾಪನ: ಅನುಮೋದನೆಗಳು, ಟೂಲ್-ಅಪಾಯ ನೀತಿಗಳು, ಮೌಲ್ಯಮಾಪನಗಳು, ಅಸಂಗತತೆ ಪತ್ತೆ, ವೆಚ್ಚ ಆಪ್ಟಿಮೈಜರ್, OTel ಎಕ್ಸ್‌ಪೋರ್ಟ್, ಟ್ಯಾಂಪರ್-ಎವಿಡೆಂಟ್ ಆಡಿಟ್ ಲಾಗ್ | ತಿಂಗಳಿಗೆ ಪ್ರತಿ ನೋಡ್‌ಗೆ $19 |

ವಾರ್ಷಿಕ ಪ್ಲಾನ್‌ಗಳು, Enterprise ಮತ್ತು ಪ್ರಸ್ತುತ ಸಂಖ್ಯೆಗಳು
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ನಲ್ಲಿ ಇವೆ. ಸ್ವಯಂ-ಹೋಸ್ಟೆಡ್ ಲೈಸೆನ್ಸ್
ಕೀಗಳು ಕ್ಲೌಡ್ ಇಲ್ಲದೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತವೆ (`clawmetry license`). ನಿಖರವಾದ ಉಚಿತ/ಪಾವತಿಸಿದ ವಿಭಜನೆ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ನಲ್ಲಿದೆ.

## ನಿಮ್ಮ ಡೇಟಾ ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲಿಯೇ ಇರುತ್ತದೆ

ClawMetry ಸ್ಥಳೀಯ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಮತ್ತು ಲಾಗ್‌ಗಳನ್ನು ಓದುತ್ತದೆ. ನೀವು `clawmetry connect` ಚಲಾಯಿಸದ ಹೊರತು **ಯಾವುದೇ ಸೆಷನ್ ಡೇಟಾ ನಿಮ್ಮ ಬಾಕ್ಸ್‌ನಿಂದ ಹೊರಹೋಗುವುದಿಲ್ಲ** — ಯಾವುದೇ ಪ್ರಾಂಪ್ಟ್‌ಗಳು, ಪ್ರತ್ಯುತ್ತರಗಳು, ಟೂಲ್ ಆರ್ಗ್ಯುಮೆಂಟ್‌ಗಳು, ಫೈಲ್
ವಿಷಯಗಳು ಅಥವಾ ಲಾಗ್ ಸಾಲುಗಳಿಲ್ಲ. ನೀವು ಸಂಪರ್ಕಿಸಿದಾಗ, ಸ್ನ್ಯಾಪ್‌ಶಾಟ್ ಎಂಡ್-ಟು-ಎಂಡ್ ಎನ್‌ಕ್ರಿಪ್ಟ್ ಆಗಿರುತ್ತದೆ
ನಿಮ್ಮ ಯಂತ್ರವನ್ನು ಎಂದಿಗೂ ಬಿಡದ ಕೀಯೊಂದಿಗೆ, ಮತ್ತು ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಡಿಕ್ರಿಪ್ಟ್ ಆಗುತ್ತದೆ. ಒಂದು
ನೋಡ್‌ಗೆ ಕೀ ಇಲ್ಲದಿದ್ದರೆ, ಅಪ್‌ಲೋಡ್ ಅನ್ನು ಸ್ಪಷ್ಟವಾಗಿ ಕಳುಹಿಸುವ ಬದಲು ಬಿಟ್ಟುಬಿಡಲಾಗುತ್ತದೆ, ಮತ್ತು ಯಾವುದೇ
ಸರ್ವರ್ ಪ್ರತಿಕ್ರಿಯೆಯು ಅದನ್ನು ಆಫ್ ಮಾಡಲು ಸಾಧ್ಯವಿಲ್ಲ.

ನೀವು ಸಂಪರ್ಕಿಸುವ ಮೊದಲು ಡೀಫಾಲ್ಟ್ ಆಗಿ ಎರಡು ವಿಷಯಗಳು ಚಲಿಸುತ್ತವೆ, ಎರಡೂ ಆಪ್ಟ್-ಔಟ್ ಮತ್ತು ಯಾವುದೂ
ಸೆಷನ್ ಡೇಟಾವನ್ನು ಹೊಂದಿರುವುದಿಲ್ಲ: ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಪಿಂಗ್ ಮತ್ತು PyPI ವಿರುದ್ಧ ಆವೃತ್ತಿ
ತಪಾಸಣೆ. ಡೀಫಾಲ್ಟ್ ಇನ್‌ಸ್ಟಾಲ್ ಪ್ರಾರಂಭಿಕ ಬ್ಯಾನರ್ ಸಾಲಿಗಾಗಿ ನಿಮ್ಮ ಸಾರ್ವಜನಿಕ IP ಅನ್ನೂ ಒಮ್ಮೆ ನೋಡುತ್ತದೆ.
ಪ್ರತಿಯೊಂದು ಗಮ್ಯಸ್ಥಾನ, ಅದು ಏನನ್ನು ಹೊಂದಿದೆ ಮತ್ತು ಅದನ್ನು ಹೇಗೆ ಆಫ್ ಮಾಡುವುದು ಎಂಬುದನ್ನು
[docs/EGRESS.md](docs/EGRESS.md) ನಲ್ಲಿ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ; ಸ್ವಯಂ-ಹೋಸ್ಟೆಡ್, ಮರುನಿರ್ದೇಶಿತ ಮತ್ತು ಏರ್-ಗ್ಯಾಪ್ಡ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು
ಯಾವುದೇ ವಿವೇಚನಾಧಿಕಾರದ ಔಟ್‌ಬೌಂಡ್ ಕರೆಗಳನ್ನು ಮಾಡುವುದಿಲ್ಲ.

ಡಿಕ್ರಿಪ್ಶನ್ ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ, ನಾವು ನಿಮಗೆ ನೀಡುವ ಕೋಡ್‌ನಲ್ಲಿ ನಡೆಯುತ್ತದೆ. ಇದು ಹಿಂದೆ
ಒಂದು ಭರವಸೆಯಾಗಿತ್ತು; ಈಗ ಇದನ್ನು ನೀವು ಪರಿಶೀಲಿಸಬಹುದಾದ ಸಂಗತಿಯಾಗಿದೆ. ನಿಮ್ಮ ಕೀಯನ್ನು ಮುಟ್ಟುವ ಪ್ರತಿ ಸಾಲು
ಒಂದೇ ಓದಬಹುದಾದ ಫೈಲ್‌ನಲ್ಲಿ ಇರುತ್ತದೆ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
ಇದು ವೀಲ್ ಒಳಗೆ ಸಾಗಿಸಲ್ಪಡುತ್ತದೆ ಮತ್ತು ವರ್ಬಾಟಿಮ್ ಆಗಿ ಸೇವೆ ಸಲ್ಲಿಸಲಾಗುತ್ತದೆ, Subresource
Integrity ಹ್ಯಾಶ್‌ನೊಂದಿಗೆ ಪಿನ್ ಮಾಡಲಾಗಿದೆ. ಬ್ರೌಸರ್ ನಾವು ಪ್ರಕಟಿಸಿದ್ದನ್ನೇ ಚಲಾಯಿಸುತ್ತದೆ ಎಂದು ದೃಢಪಡಿಸಲು:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ಅದು ಸಾಬೀತುಪಡಿಸದಿರುವುದು: ಫೈಲ್ ಅನ್ನು ಲೋಡ್ ಮಾಡುವ ಪುಟವನ್ನು ನಾವು ಸೇವೆ ಸಲ್ಲಿಸುತ್ತೇವೆ, ಆದ್ದರಿಂದ ನಾವು ಬೇರೆ
ಪುಟವನ್ನು ಸೇವೆ ಸಲ್ಲಿಸಬಹುದು. ಇಂಟೆಗ್ರಿಟಿ ಹ್ಯಾಶ್‌ಗಳು ರಾಜಿಯಾದ CDN ನಿಂದ ನಿಮ್ಮನ್ನು ರಕ್ಷಿಸುತ್ತವೆ,
ಮಾರಾಟಗಾರರಿಂದ ಅಲ್ಲ. ನೀವು ಗಳಿಸುವುದೇನೆಂದರೆ ಯಾವುದೇ ಬದಲಿಯು ಉದ್ದೇಶಪೂರ್ವಕವಾಗಿರಬೇಕು, ಪುಟದ ಮೂಲದಲ್ಲಿ
ಗೋಚರಿಸಬೇಕು, ಮತ್ತು ಯಾರಾದರೂ ಪಡೆಯಬಹುದಾದ PyPI ಯಲ್ಲಿನ ಆರ್ಟಿಫ್ಯಾಕ್ಟ್‌ಗಿಂತ ಭಿನ್ನವಾಗಿರಬೇಕು ಎಂಬುದೇ. ಸ್ವಯಂ-ಹೋಸ್ಟಿಂಗ್ ಅಥವಾ ಸ್ಥಳೀಯ-ಮಾತ್ರ ಉಳಿಯುವುದು
ಈ ಅವಲಂಬನೆಯನ್ನು ಸಂಪೂರ್ಣವಾಗಿ ತೆಗೆದುಹಾಕುತ್ತದೆ.

## ಇನ್‌ಸ್ಟಾಲ್

```bash
pip install clawmetry     # ನಂತರ: clawmetry
```

ಅಥವಾ ಒನ್-ಲೈನರ್: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ಅಥವಾ Windows ನಲ್ಲಿ Python 3.8+ ಬೇಕು, ಮತ್ತು ಅದೇ ಯಂತ್ರದಲ್ಲಿ ಕನಿಷ್ಠ ಒಂದು ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್ ಬೇಕು.
Docker ಸೂಚನೆಗಳು: [docs/DOCKER.md](docs/DOCKER.md).

ಅಥವಾ ಏಜೆಂಟ್ ಅನ್ನೇ ಅದನ್ನು ನಿಮಗಾಗಿ ಸೆಟಪ್ ಮಾಡಲು ಬಿಡಿ. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ಸ್ಕಿಲ್ Claude Code, Codex, Cursor, Gemini CLI, Copilot ಅಥವಾ OpenCode ಗೆ
ClawMetry ಅನ್ನು ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಲು, ಯಂತ್ರದಲ್ಲಿನ ಏಜೆಂಟ್‌ಗಳು ಏನು ಮಾಡುತ್ತಿವೆ ಮತ್ತು ಖರ್ಚು ಮಾಡುತ್ತಿವೆ ಎಂಬುದನ್ನು ವರದಿ ಮಾಡಲು,
ವಿನಂತಿಯ ಮೇಲೆ ಒಂದು ಸೆಷನ್ ಅನ್ನು ನಿಲ್ಲಿಸಲು, ಮತ್ತು ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅನುಮೋದನೆಗಾಗಿ ಹಿಡಿದಿಟ್ಟುಕೊಳ್ಳಲು ಕಲಿಸುತ್ತದೆ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ದಸ್ತಾವೇಜುಗಳು

| | |
|---|---|
| [ರನ್‌ಟೈಮ್ ಹೊಂದಾಣಿಕೆ](docs/compatibility.md) | ಪ್ರತಿ ಅಡಾಪ್ಟರ್ ಏನನ್ನು ಓದುತ್ತದೆ, ಮತ್ತು ರನ್‌ಟೈಮ್ ಅನ್ನು ಹೇಗೆ ಸೇರಿಸುವುದು |
| [ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್](docs/CONTEXT_BLOWOUT.md) | ಪ್ರತಿ-ಪೂರೈಕೆದಾರ ವಿಂಡೋಗಳು, ಕಂಪ್ಯಾಕ್ಷನ್ ವರ್ಸಸ್ ಓವರ್‌ಫ್ಲೋ, ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ಕವರೇಜ್ |
| [ಓವರ್‌ಹೆಡ್](docs/OVERHEAD.md) | ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ಗೆ ಎಷ್ಟು ವೆಚ್ಚ, ಅಳೆಯಲಾಗಿದೆ, ಅದನ್ನು ಪುನರುತ್ಪಾದಿಸುವ ಹಾರ್ನೆಸ್‌ನೊಂದಿಗೆ |
| [ಎಂಟೈಟಲ್‌ಮೆಂಟ್‌ಗಳು](docs/ENTITLEMENTS.md) | ಉಚಿತ ವರ್ಸಸ್ ಪಾವತಿಸಿದ, ಟಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, ಲೈಸೆನ್ಸ್ CLI |
| [ಅನುಮೋದನೆಗಳು ಮತ್ತು ನೀತಿಗಳು](docs/APPROVALS.md) | ಪ್ರೀ-ಎಕ್ಸಿಕ್ಯೂಷನ್ ಗೇಟಿಂಗ್, ಅಪಾಯ ಸ್ಕೋರಿಂಗ್, ಫೋನ್ ಅನುಮೋದನೆಗಳು |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಲ್ಲಿಯಾದರೂ ಎಕ್ಸ್‌ಪೋರ್ಟ್ ಮಾಡಿ, ಯಾವುದರಿಂದಲಾದರೂ OTLP ಇಂಜೆಸ್ಟ್ ಮಾಡಿ |
| [ನಿಮ್ಮ ಸ್ವಂತ ಏಜೆಂಟ್ ತನ್ನಿ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ಅಂತ್ಯದಿಂದ ಅಂತ್ಯದವರೆಗೆ, ಚಲಾಯಿಸಬಹುದಾದ ಉದಾಹರಣೆಗಳೊಂದಿಗೆ |
| [SDK ಟ್ರ್ಯಾಕಿಂಗ್](docs/SDK_TRACKING.md) | ನೀವೇ ನಿರ್ಮಿಸಿದ ಏಜೆಂಟ್‌ಗಳಿಗೆ ವೆಚ್ಚ ಗುಣಲಕ್ಷಣ |
| [ಚಾಟ್ ಚಾನೆಲ್‌ಗಳು](docs/CHANNELS.md) | ಫ್ಲೋನಲ್ಲಿ ತೋರಿಸಲಾದ ಚಾಟ್ ಅಡಾಪ್ಟರ್‌ಗಳು |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ಡ್ NVIDIA NemoClaw ಸೆಟಪ್‌ಗಳು |
| [Docker](docs/DOCKER.md) | ಇಮೇಜ್, ಕಂಪೋಸ್, ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು |
| [ಆರ್ಕಿಟೆಕ್ಚರ್](ARCHITECTURE.md) · [ಡೆವಲಪ್‌ಮೆಂಟ್](docs/DEVELOPMENT.md) | ಒಳಗೆ ಇದು ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ; ಮೂಲದಿಂದ ಚಲಾಯಿಸುವುದು |
| [ಟೆಲಿಮೆಟ್ರಿ](docs/TELEMETRY.md) | ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಮತ್ತು ಡೆಸ್ಕ್‌ಟಾಪ್-ಓಪನ್ ಪಿಂಗ್‌ಗಳು, ಮತ್ತು ಅವುಗಳನ್ನು ಹೇಗೆ ಆಫ್ ಮಾಡುವುದು |

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

ಕೆಳಗಿನ ಪ್ರತಿಯೊಂದು ಸಂಖ್ಯೆಯೂ ಒಂದು ನೈಜ ಯಂತ್ರದಿಂದ, ಓದಲು-ಮಾತ್ರ, ಏನನ್ನೂ ಬಿತ್ತದೆ.

**ಏನಾದರೂ ತಪ್ಪಾದಾಗ ಅದು ನಿಮಗೆ ಹೇಳುತ್ತದೆ, ಕೇವಲ ಏನಾಯಿತು ಎಂಬುದನ್ನಲ್ಲ.**
ಮೇಲ್ಭಾಗದಲ್ಲಿ ಎರಡು ಅಸಂಗತತೆ ಬ್ಯಾನರ್‌ಗಳು: ದೈನಂದಿನ ಸರಾಸರಿಗಿಂತ 7 ಪಟ್ಟು ಖರ್ಚು, ಮತ್ತು
4.2 ಪಟ್ಟು ವೆಚ್ಚ ಸ್ಪೈಕ್. ಅವುಗಳ ಕೆಳಗೆ, ಇತ್ತೀಚಿನ 667 ಸೆಷನ್‌ಗಳಲ್ಲಿ 324 ಒಂದು ವ್ಯರ್ಥ
ಸಂಕೇತವನ್ನು ಹೊಂದಿದ್ದು, ಕಾರಣದ ಪ್ರಕಾರ ವಿಂಗಡಿಸಲಾಗಿದೆ.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ಹಣ ಎಲ್ಲಿ ಹೋಯಿತು ಎಂಬುದನ್ನು ಇದು ನಿಮಗೆ ತೋರಿಸುತ್ತದೆ, ಪ್ರತಿ ವಿಂಡೋನಲ್ಲಿ.**
ಇಂದು $252.47, ಈ ವಾರ $513.15, ಈ ತಿಂಗಳು $1,312.92, ಪ್ರತಿಯೊಂದರ ಹಿಂದಿನ ಟೋಕನ್‌ಗಳೊಂದಿಗೆ ಮತ್ತು ನಿಮ್ಮ ಚಂದಾದಾರಿಕೆ ಈಗಾಗಲೇ ಎಷ್ಟನ್ನು ಒಳಗೊಳ್ಳುತ್ತದೆ ಎಂಬುದರೊಂದಿಗೆ. ಅದರ ಕೆಳಗೆ,
ಮರುಪಡೆಯಬಹುದಾದದ್ದು ಎಂದು ಪಟ್ಟಿ ಮಾಡಲಾದ ಸುಮಾರು $1,128/ತಿಂಗಳು ಮತ್ತು ಕ್ಯಾಶ್ ಮರುಬಳಕೆಯಿಂದ ಈಗಾಗಲೇ ಉಳಿಸಲಾದ $17,256/ತಿಂಗಳು.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ಒಂದು ಸಂದೇಶ ಹೇಗೆ ಉತ್ತರವಾಗುತ್ತದೆ ಎಂಬುದನ್ನು ಇದು ಬಿಡಿಸುತ್ತದೆ.**
ಲೈವ್ ಫ್ಲೋ ಡಯಾಗ್ರಾಂ: ನೀವು, ಅದು ಬಂದ ಚಾನೆಲ್, ಗೇಟ್‌ವೇ, ಈಗ ಉತ್ತರಿಸುತ್ತಿರುವ
ಮಾದರಿ, ಮತ್ತು ಅದು ತಲುಪಿದ ಪ್ರತಿ ಟೂಲ್. ಕೆಲಸ ಅವುಗಳ ಮೂಲಕ ಚಲಿಸುತ್ತಿದ್ದಂತೆ ನೋಡ್‌ಗಳು ಬೆಳಗುತ್ತವೆ.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ಯಂತ್ರದಲ್ಲಿನ ಪ್ರತಿ ಏಜೆಂಟ್, ಒಂದೇ ಟೇಬಲ್‌ನಲ್ಲಿ.**
ಅದು ಏನನ್ನು ಚಲಾಯಿಸುತ್ತದೆ, ಕಳೆದ 24 ಗಂಟೆಗಳಲ್ಲಿ ಮತ್ತು ಅದರ ಜೀವಿತಾವಧಿಯಲ್ಲಿ ಅದಕ್ಕೆ ಎಷ್ಟು ವೆಚ್ಚವಾಗುತ್ತದೆ, ಯಾವಾಗ
ಅದನ್ನು ಕೊನೆಯದಾಗಿ ನೋಡಲಾಗಿತ್ತು, ಯಾರು ಅದನ್ನು ಹೊಂದಿದ್ದಾರೆ, ಮತ್ತು ಚಂದಾದಾರಿಕೆ ಬಿಲ್ ಅನ್ನು ಕವರ್ ಮಾಡುತ್ತಿದೆಯೇ. ಇಲ್ಲಿ 14 ಏಜೆಂಟ್‌ಗಳು, 3 ಸೆಷನ್‌ಗಳು ಕೆಲಸ ಮಾಡುತ್ತಿವೆ, 13 ಶಾಂತವಾಗಿವೆ.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ಒಂದು ಟರ್ನ್‌ನ ಸಮಯ ಮತ್ತು ಹಣ ಎಲ್ಲಿ ಹೋಯಿತು ಎಂಬುದನ್ನು ಇದು ತೋರಿಸುತ್ತದೆ, ಟೂಲ್ ಬೈ ಟೂಲ್.**
ಒಂದು ನೈಜ ಸೆಷನ್‌ನ ಒಂದು ಟರ್ನ್: $1.16 ಗೆ 11.2 ನಿಮಿಷಗಳಲ್ಲಿ 11 ಟೂಲ್‌ಗಳು. ಪ್ರತಿ Bash
ಕರೆ ಮತ್ತು ಮಾದರಿ ಕರೆಗೆ ಟೈಮ್‌ಲೈನ್‌ನಲ್ಲಿ ತನ್ನದೇ ಬಾರ್ ಸಿಗುತ್ತದೆ, ಆದ್ದರಿಂದ 4.1 ನಿಮಿಷಗಳ ಕಾಲ ಚಲಿಸಿದ ಕಮಾಂಡ್ ಮತ್ತು 226ms ಕಾಲ ಚಲಿಸಿದ್ದನ್ನು ಒಂದೇ ನೋಟದಲ್ಲಿ ಗುರುತಿಸಬಹುದು.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ಇದು ಕೆಲಸವನ್ನು ಗ್ರೇಡ್ ಮಾಡುತ್ತದೆ, ಕೇವಲ ಖರ್ಚನ್ನಲ್ಲ.**
ಈ ವಾರ A: 54 ಕಾರ್ಯಗಳು ಸ್ವಚ್ಛವಾಗಿ ಹಿಂತಿರುಗಿದವು, 2 ಒರಟಾದವು $48.57 ವೆಚ್ಚವಾಯಿತು, ಮತ್ತು
ನಿರ್ಣಯಿಸಲು ತುಂಬಾ ಕಡಿಮೆ ಚಟುವಟಿಕೆ ಇರುವ ರನ್‌ಗಳನ್ನು ಗೆಲುವುಗಳಾಗಿ ಎಣಿಸುವ ಬದಲು ಗ್ರೇಡ್‌ನಿಂದ ಹೊರಗಿಡಲಾಗಿದೆ. ಪ್ರತಿ ಒರಟಾದ ರನ್ ಅದರ ಟ್ರೇಸ್‌ಗೆ ಲಿಂಕ್ ಆಗುತ್ತದೆ.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ಕಾಂಟೆಕ್ಸ್ಟ್ ವಿಂಡೋ ಏಕೆ ತುಂಬುತ್ತಲೇ ಇರುತ್ತದೆ ಎಂಬುದನ್ನು ಇದು ತೋರಿಸುತ್ತದೆ.**
ಇತ್ತೀಚಿನ ಟರ್ನ್‌ನಲ್ಲಿ 1M-ಟೋಕನ್ ವಿಂಡೋನ 715K, 83.3% ಶಿಖರ, 4 ಕಂಪ್ಯಾಕ್ಷನ್‌ಗಳು
ಎಲ್ಲವೂ ಓವರ್‌ಫ್ಲೋ ಬದಲಿಗೆ ಪ್ರೊಆಕ್ಟಿವ್ ಆಗಿ ಪ್ರಚೋದಿತವಾದವು, ಜೊತೆಗೆ ಅದರ ಹಿಂದಿನ ಪ್ರತಿ ಟರ್ನ್‌ನ ಬಳಕೆ.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ನೀವು ಏನನ್ನೂ ಕಾನ್ಫಿಗರ್ ಮಾಡದೆಯೇ ಪತ್ತೆಹಚ್ಚುವಿಕೆ ಚಲಿಸುತ್ತದೆ.**
ಅಂತರ್ನಿರ್ಮಿತ ಡಿಟೆಕ್ಟರ್‌ಗಳು ಇನ್‌ಸ್ಟಾಲ್‌ನಿಂದಲೇ ಆನ್ ಆಗಿವೆ: ಏಜೆಂಟ್ ಶಾಂತವಾಯಿತು, ಟೆಲಿಮೆಟ್ರಿ ಫೀಡ್
ನಿಂತಿತು, ವೆಚ್ಚ ಸ್ಪೈಕ್, ಟೋಕನ್ ಬರ್ಸ್ಟ್, ಏರುತ್ತಿರುವ ದೋಷಗಳು, ದೋಷ ಸ್ಪೈಕ್, ಬಜೆಟ್
ಮಿತಿ, ಬೆದರಿಕೆ ಸಹಿ ಹೊಂದಿಕೆಯಾಯಿತು, ಭದ್ರತಾ ಟೂಲ್ ಶೋಧನೆ, ಭದ್ರತಾ ಸ್ಥಿತಿ
ಬದಲಾಯಿತು. ಇವುಗಳ ಮೇಲೆ ನಿಮ್ಮ ಸ್ವಂತ ನಿಯಮಗಳು ಐಚ್ಛಿಕ.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ಅಪಾಯಕಾರಿ ಕರೆಯನ್ನು ಹಿಡಿದಿಟ್ಟುಕೊಳ್ಳುವುದು ಆಪ್ಟ್-ಇನ್, ಮತ್ತು ಆಫ್ ಆಗಿಯೇ ಸಾಗಿಸಲಾಗುತ್ತದೆ.**
ಪುನರಾವರ್ತಿತ ಡಿಲೀಟ್‌ಗಳು, ಫೋರ್ಸ್ ಪುಶ್‌ಗಳು, sudo, ರಹಸ್ಯಗಳು, ಪ್ಯಾಕೇಜ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು ಮತ್ತು ಔಟ್‌ಬೌಂಡ್
ಕರೆಗಳು ಪ್ರತಿಯೊಂದೂ ನೀವು ಆನ್ ಮಾಡಬಹುದಾದ ನಿಯಮವನ್ನು ಪಡೆಯುತ್ತವೆ. ನೀವು ಹಾಗೆ ಮಾಡುವವರೆಗೆ, ClawMetry ಗಮನಿಸುತ್ತದೆ ಮತ್ತು
ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ. ಒಂದನ್ನು ಆನ್ ಮಾಡಿದ ನಂತರ, ಹೊಂದಿಕೆಯಾಗುವ ಕರೆಗಳು ಅನುಮೋದನೆ ಅಥವಾ ನಿರಾಕರಣೆಗಾಗಿ ಇಲ್ಲಿ (ಅಥವಾ ನಿಮ್ಮ ಫೋನ್‌ನಲ್ಲಿ) ಕಾಯುತ್ತವೆ.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ಇನ್ನಷ್ಟು, ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## ಮಾನ್ಯತೆ

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## ಸ್ಟಾರ್ ಇತಿಹಾಸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ಪರವಾನಗಿ

MIT · [@vivekchand](https://github.com/vivekchand) ರವರಿಂದ ನಿರ್ಮಿಸಲಾಗಿದೆ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
