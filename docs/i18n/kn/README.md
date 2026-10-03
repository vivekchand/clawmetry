<!-- i18n-src:c99ac0512cae -->
> ಕನ್ನಡ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ಒಂದು ಏಜೆಂಟ್ ನೂರು ಟೂಲ್ ಕರೆಗಳನ್ನು ಮಾಡಿದರೂ ಯಾವುದೇ ಪ್ರಗತಿ ಸಾಧಿಸದೆ ಇರಬಹುದು.** ClawMetry
ನಿಮ್ಮ ಕೋಡಿಂಗ್ ಏಜೆಂಟ್‌ಗಳು ಈಗಾಗಲೇ ಬರೆಯುತ್ತಿರುವ ಸೆಷನ್ ಫೈಲ್‌ಗಳನ್ನು ಓದುತ್ತದೆ, ಮತ್ತು ಟೈಮ್‌ಲೈನ್,
ಟೂಲ್ ಕರೆಗಳು, ಹಾಗೂ ರನ್‌ಟೈಮ್ ಬಹಿರಂಗಪಡಿಸುವ ಯಾವುದೇ ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚದ ಡೇಟಾವನ್ನು ಒಂದೇ
ವೀಕ್ಷಣೆಯಲ್ಲಿ ಇಡುತ್ತದೆ — ಇದರಿಂದ ಕೆಲಸ ಮಾಡುತ್ತಿರುವ ದೀರ್ಘ ರನ್ ಮತ್ತು ಸಿಕ್ಕಿಹಾಕಿಕೊಂಡಿರುವ ರನ್ ನಡುವೆ ವ್ಯತ್ಯಾಸ ಗುರುತಿಸಬಹುದು.

**33 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳ** ಜೊತೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ — Claude Code, OpenAI Codex, Hermes, OpenClaw ಮತ್ತು ಇನ್ನೂ 29. ನಿಮ್ಮ ಸಂಪೂರ್ಣ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್. ([ಪೂರ್ಣ ಪಟ್ಟಿ](SUPPORTED_RUNTIMES.txt), ಕ್ಯಾಟಲಾಗ್‌ನಿಂದ ಜನರೇಟ್ ಮಾಡಲಾಗಿದೆ.)

> 🌐 **ಇದನ್ನು ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನೂ ಹೆಚ್ಚು →](docs/i18n/)

ಒಂದು ಕಮಾಂಡ್. ಯಾವುದೇ ಕಾನ್ಫಿಗ್ ಇಲ್ಲ. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆಹಚ್ಚುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆಯುತ್ತದೆ. ಯಾವುದೇ ಕಾನ್ಫಿಗ್ ಇಲ್ಲ: ಇದು ನಿಮ್ಮಲ್ಲಿ ಈಗಾಗಲೇ ಇರುವ
ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಕಂಡುಹಿಡಿಯುತ್ತದೆ, ಅವುಗಳನ್ನು ಓದಲು-ಮಾತ್ರ ಓದುತ್ತದೆ, ಮತ್ತು ಅವು ಹೇಗೆ ಚಲಿಸುತ್ತವೆ ಎಂಬುದರಲ್ಲಿ ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡುವ ಮೊದಲು

| | |
|---|---|
| **ಇದು ಏನು ಮಾಡುತ್ತದೆ** | ನಿಮ್ಮ ಏಜೆಂಟ್‌ಗಳು ಈಗಾಗಲೇ ಬರೆಯುತ್ತಿರುವ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಮತ್ತು ಲಾಗ್‌ಗಳನ್ನು ಓದುತ್ತದೆ. SDK ಇಲ್ಲ, ಕೋಡ್ ಬದಲಾವಣೆ ಇಲ್ಲ, ನಿಮ್ಮ ಅಪ್ಲಿಕೇಶನ್‌ನಲ್ಲಿ ಯಾವುದೇ ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್ ಇಲ್ಲ. |
| **ನೀವು ಏನು ನೋಡುತ್ತೀರಿ** | ಸೆಷನ್ ಟೈಮ್‌ಲೈನ್, ಟೂಲ್-ಬೈ-ಟೂಲ್ ರಿಪ್ಲೇ, ಟೋಕನ್ ಮತ್ತು ವೆಚ್ಚದ ವಿಭಜನೆ, ಮತ್ತು ಟ್ರಜೆಕ್ಟರಿ ಸಿಗ್ನಲ್‌ಗಳು (ಲೂಪಿಂಗ್, ಪುನರಾವರ್ತಿತ ವೈಫಲ್ಯಗಳು) — ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ. |
| **ಏನು ಉಚಿತ** | `pip install clawmetry` ಯಾವುದೇ ಖಾತೆ, ಕೀ ಅಥವಾ ನೆಟ್‌ವರ್ಕ್ ಕರೆ ಇಲ್ಲದೆ **OpenClaw, NVIDIA NemoClaw, Goose ಮತ್ತು Qwen Code** ಅನ್ನು ಓದುತ್ತದೆ. ಇನ್ನುಳಿದ 28 — Claude Code, Codex, Cursor ಮತ್ತು ಇತರವು — ಕ್ಲೋಸ್ಡ್-ಸೋರ್ಸ್ `clawmetry-pro` ಸಹಾಯಕ ಆಪ್‌ನ ಮೂಲಕ ಓದಲಾಗುತ್ತದೆ, ಇದು 7-ದಿನದ ಟ್ರಯಲ್ ಅಥವಾ ಪ್ಲಾನ್‌ನೊಂದಿಗೆ ಬರುತ್ತದೆ — ನಿಖರ ವಿಭಜನೆಗಾಗಿ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ನೋಡಿ. |
| **ಹೇಗೆ ಪ್ರಾರಂಭಿಸುವುದು** | `pip install clawmetry && clawmetry`, ನಂತರ localhost:8900 ತೆರೆಯಿರಿ. ಈ ಯಂತ್ರದಲ್ಲಿ ಇನ್ನೂ ಯಾವುದೇ ಏಜೆಂಟ್‌ಗಳಿಲ್ಲವೇ? `clawmetry --sample` ಮೂರು ಲೇಬಲ್ ಮಾಡಿದ ಸಿಂಥೆಟಿಕ್ ಸೆಷನ್‌ಗಳೊಂದಿಗೆ ತೆರೆಯುತ್ತದೆ. |
| **ನಿಮ್ಮ ಯಂತ್ರದಿಂದ ಏನು ಹೊರಹೋಗುತ್ತದೆ** | ನೀವು `clawmetry connect` ರನ್ ಮಾಡದ ಹೊರತು ಯಾವುದೇ ಸೆಷನ್ ಡೇಟಾ ಇಲ್ಲ. ಡಿಫಾಲ್ಟ್ ಆಗಿ ಎರಡು ವಿಷಯಗಳು ರನ್ ಆಗುತ್ತವೆ, ಎರಡೂ ಆಪ್ಟ್-ಔಟ್ ಮಾಡಬಹುದಾದವು ಮತ್ತು ಯಾವುದೂ ಸೆಷನ್ ಕಂಟೆಂಟ್ ಹೊಂದಿರುವುದಿಲ್ಲ: ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಪಿಂಗ್ ಮತ್ತು PyPI ಆವೃತ್ತಿ ಪರಿಶೀಲನೆ. ಪ್ರತಿ ಗಮ್ಯಸ್ಥಾನವನ್ನು [docs/EGRESS.md](docs/EGRESS.md) ನಲ್ಲಿ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ, ಕಾಮೆಂಟ್‌ಗಳನ್ನು ಓದುವ ಬದಲು ವೈರ್ ಕ್ಯಾಪ್ಚರ್‌ನಿಂದ ಮರುನಿರ್ಮಿಸಲಾಗಿದೆ. |

ಫಲಿತಾಂಶವನ್ನು ನಿರ್ಣಯಿಸುವ ಮೊದಲು ತಿಳಿದುಕೊಳ್ಳಬೇಕಾದ ಎರಡು ಮಿತಿಗಳು: ರನ್‌ಟೈಮ್‌ಗಳು ಬಹಳ
ವಿಭಿನ್ನ ಡೇಟಾವನ್ನು ಬಹಿರಂಗಪಡಿಸುತ್ತವೆ (ಕೆಲವು ಯಾವುದೇ ವೆಚ್ಚವನ್ನು ಪ್ರಕಟಿಸುವುದಿಲ್ಲ — [ಮ್ಯಾಟ್ರಿಕ್ಸ್](docs/compatibility.md)
ಯಾವುದು ಎಂಬುದನ್ನು, ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ ಹೇಳುತ್ತದೆ), ಮತ್ತು ಕ್ರಿಯೆಯನ್ನು ಗಮನಿಸುವುದು ಅದನ್ನು
ತಡೆಯಲು ಸಾಧ್ಯವಾಗುವುದಕ್ಕೆ ಸಮಾನವಲ್ಲ ([ಯಾವ ನಿಯಂತ್ರಣಗಳು ನಿಜ, ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ](docs/APPROVALS.md)).


## 33 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳ ಜೊತೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

**ಓಪನ್ ಸೋರ್ಸ್ ಆಪ್‌ನಲ್ಲಿ ಉಚಿತ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**ಪೇಯ್ಡ್ ಪ್ಲಾನ್‌ನಲ್ಲಿ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ ಅದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಸಿಗುತ್ತದೆ. ಹಲವಾರನ್ನು ಒಂದೇ ಬಾರಿಗೆ ರನ್ ಮಾಡಿ ಮತ್ತು ಹೆಡರ್
ಸ್ವಿಚರ್ ಪ್ರತಿ ಟ್ಯಾಬ್ ಅನ್ನು ಅವುಗಳಲ್ಲಿ ಒಂದಕ್ಕೆ ಮರು-ಸ್ಕೋಪ್ ಮಾಡುತ್ತದೆ.

SDK ಬಳಸಿ ನಿಮ್ಮದೇ ಏಜೆಂಟ್ ನಿರ್ಮಿಸಿದ್ದೀರಾ? ಇಂಟರ್‌ಸೆಪ್ಟರ್ ಅದರ LLM ಕರೆಗಳನ್ನೂ ಟ್ರ್ಯಾಕ್ ಮಾಡುತ್ತದೆ.
[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ನೋಡಿ.

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **ಸೆಷನ್‌ಗಳು ಮತ್ತು ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು**: ಪ್ರತಿ ಏಜೆಂಟ್ ಏನು ಮಾಡಿತು, ಟರ್ನ್ ಬೈ ಟರ್ನ್, ರಿಪ್ಲೇ ಜೊತೆಗೆ
- **ವೆಚ್ಚ ಮತ್ತು ಟೋಕನ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್, ಮಾಡೆಲ್, ಸೆಷನ್ ಮತ್ತು ದಿನಕ್ಕೆ, ಅನಾಮಲಿ ಫ್ಲ್ಯಾಗ್‌ಗಳೊಂದಿಗೆ
- **ಫ್ಲೋ**: ಚಾನೆಲ್‌ಗಳು, ಮಾಡೆಲ್‌ಗಳು ಮತ್ತು ಟೂಲ್‌ಗಳ ಮೂಲಕ ಹರಿಯುವ ಸಂದೇಶಗಳ ಲೈವ್ ರೇಖಾಚಿತ್ರ
- **ಬ್ರೈನ್**: ನಡೆಯುತ್ತಿರುವಂತೆ ತಾರ್ಕಿಕತೆ ಮತ್ತು ಟೂಲ್-ಕರೆ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್
- **ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್**: ಪ್ರತಿ ಪ್ರೊವೈಡರ್‌ಗೆ ಗಾತ್ರ ನಿಗದಿ ಮಾಡಲಾದ ವಿಂಡೋ ಬಳಕೆ, ಕಾಂಪ್ಯಾಕ್ಷನ್ ವರ್ಸಸ್ ಫೋರ್ಸ್ಡ್ ಓವರ್‌ಫ್ಲೋ, ಜೊತೆಗೆ ನಮಗೆ *ಕಾಣಿಸದ* ವಿಷಯಗಳ ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ಮ್ಯಾಪ್ ([ಹೇಗೆ](docs/CONTEXT_BLOWOUT.md))
- **ಮೆಮೊರಿ ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್ ನಿಜವಾಗಿ ಲೋಡ್ ಮಾಡಿದ ಫೈಲ್‌ಗಳು ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು
- **ಹೆಲ್ತ್ ಮತ್ತು ಲಾಗ್‌ಗಳು**: ಡಿಸ್ಕ್, ಮೆಮೊರಿ, ಎರರ್ ದರಗಳು, ರೇಟ್ ಲಿಮಿಟ್‌ಗಳು, ಲೈವ್ ಲಾಗ್ ಸ್ಟ್ರೀಮ್
- **ಅಲರ್ಟ್‌ಗಳು**: ಬಜೆಟ್ ಮಿತಿಗಳು, ಎರರ್ ಸ್ಪೈಕ್‌ಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್, Slack, Discord, PagerDuty, Telegram, ಇಮೇಲ್‌ಗೆ ರೂಟ್ ಮಾಡಲಾಗಿದೆ
- **ಅನುಮೋದನೆಗಳು**: ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅವು ಚಲಿಸುವ *ಮೊದಲು* ಪಾಸ್ ಮಾಡಿ ಮತ್ತು ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಅನುಮೋದಿಸಿ ([ಹೇಗೆ](docs/APPROVALS.md))

## ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್, ಮತ್ತು ಗಮನಿಸುವುದರ ವೆಚ್ಚ

ಯಾವುದೇ ಏಜೆಂಟ್-ಹೋಲಿಕೆ ಟೂಲ್ ಅನ್ನು ನಂಬುವ ಮೊದಲು ಉತ್ತರಿಸಬೇಕಾದ ಎರಡು ಪ್ರಶ್ನೆಗಳು.

**ರನ್‌ಟೈಮ್‌ಗಳಾದ್ಯಂತ ಕಾಂಟೆಕ್ಸ್ಟ್-ವಿಂಡೋ ಬ್ಲೋಔಟ್ ಅನ್ನು ಇದು ಹೇಗೆ ನಿರ್ವಹಿಸುತ್ತದೆ?**

ಬಳಕೆಯ ಶೇಕಡಾವಾರು ಪ್ರಮಾಣವು ಅದು ಯಾವುದರಿಂದ ಭಾಗಿಸುತ್ತದೆ ಎಂಬುದಕ್ಕೆ ಮಾತ್ರ ಪ್ರಾಮಾಣಿಕವಾಗಿರುತ್ತದೆ. ClawMetry
[ಓದಬಹುದಾದ ಮತ್ತು PR ಮಾಡಬಹುದಾದ ಟೇಬಲ್‌ನಿಂದ](clawmetry/context_windows.py)
ಪ್ರತಿ ಪ್ರೊವೈಡರ್‌ಗೆ ವಿಂಡೋ ಗಾತ್ರ ನಿಗದಿ ಮಾಡುತ್ತದೆ, ಇದು Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama ಮತ್ತು GLM ಅನ್ನು ಒಳಗೊಂಡಿದೆ. ಇದು ಎಲ್ಲಾ 33
ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಒಂದೇ ವೆಂಡರ್‌ನ ಸ್ಕೇಲ್‌ನಲ್ಲಿ ಅಳೆಯುವುದಿಲ್ಲ. ಇದು ಮುಖ್ಯ: Anthropic ನ 200K ಗೆ ಹೋಲಿಸಿ ಲೆಕ್ಕ ಹಾಕಿದ
300K GPT-5 ಟರ್ನ್ ">100%, ಬ್ಲೋನ್" ಎಂದು ಓದುತ್ತದೆ, ಆದರೆ ಅದು ನಿಜವಾಗಿಯೂ GPT-5 ನ 400K ನ 75% ನಲ್ಲಿದೆ.
ಅದೇ ಸ್ಕೇಲ್ ನಿಜವಾಗಿ ಓವರ್‌ಫ್ಲೋ ಆಗಿರುವ 130K DeepSeek ಟರ್ನ್ ಅನ್ನು ಅನುಕೂಲಕರ 65% ಎಂದು ಮರೆಮಾಡುತ್ತದೆ.

ಪ್ರತಿ ವಿಂಡೋ ಅದರ ಮೂಲವನ್ನು ಹೊಂದಿದ್ದು ಬರುತ್ತದೆ: `model_table`, `explicit_marker`,
`observed_floor`, ಅಥವಾ ನಮಗೆ ಮಾಡೆಲ್ ತಿಳಿಯದಿದ್ದಾಗ ಪ್ರಾಮಾಣಿಕ `default`. ಅಂದಾಜಿನ ಮೇಲೆ
ನಿರ್ಮಿಸಲಾದ ಗೇಜ್ ಎಂದಿಗೂ ಲುಕ್‌ಅಪ್‌ನ ಮೇಲೆ ನಿರ್ಮಿಸಲಾದ ಅದೇ ಅಧಿಕಾರದಿಂದ ರೆಂಡರ್ ಆಗುವುದಿಲ್ಲ.

ClawMetry ಕೆಲವು ರನ್‌ಟೈಮ್‌ಗಳಲ್ಲಿ ಮಾತ್ರ ಕಾಂಪ್ಯಾಕ್ಷನ್ ಈವೆಂಟ್‌ಗಳನ್ನು ನೋಡಬಲ್ಲದು. ಆದ್ದರಿಂದ
`GET /api/context-coverage` ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ, ಒಂದು ಶೂನ್ಯ **"ಕ್ಲೀನ್ ಆಗಿ ರನ್ ಆಯಿತು" ಎಂದರ್ಥವೋ
ಅಥವಾ "ನಮಗೆ ಕಾಣಿಸುತ್ತಿಲ್ಲ" ಎಂದರ್ಥವೋ** ಎಂಬುದನ್ನು ವರದಿ ಮಾಡುತ್ತದೆ. ನಿಜವಾಗಿ ಕುರುಡಾಗಿರುವುದನ್ನು
ಅರ್ಥೈಸುವ `0` ಹಾಗೆಯೇ ಹೇಳುತ್ತದೆ.
[ಪೂರ್ಣ ವಿವರ](docs/CONTEXT_BLOWOUT.md)

**ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ನ ವೆಚ್ಚ ಎಷ್ಟು?**

| ಪಾತ್ | ನಿಮ್ಮ ಏಜೆಂಟ್‌ಗೆ ಸೇರಿಸಲಾಗಿದೆ | ಡಿಫಾಲ್ಟ್? |
|---|---|---|
| ಸೆಷನ್-ಫೈಲ್ ಟೈಲಿಂಗ್ (ಎಲ್ಲಾ 33 ರನ್‌ಟೈಮ್‌ಗಳು) | **0**. ಪ್ರತ್ಯೇಕ ಪ್ರಕ್ರಿಯೆ, ನಿಮ್ಮ ಏಜೆಂಟ್‌ನಲ್ಲಿ ಯಾವುದೇ ClawMetry ಕೋಡ್ ಇಲ್ಲ | ಆನ್ |
| HTTP ಇಂಟರ್‌ಸೆಪ್ಟರ್ (`CLAWMETRY_INTERCEPT=1`) | ಪ್ರತಿ LLM ಕರೆಗೆ **+0.44 ms**, ಅಥವಾ 5s ಕರೆಯ 0.009% | ಆಫ್ |
| ಪ್ರೀ-ಟೂಲ್ ಹುಕ್ ಗೇಟ್ (ವಾರ್ಮ್ ಕ್ಯಾಶ್) | 36 ms ಇಂಟರ್‌ಪ್ರೆಟರ್ ಫ್ಲೋರ್‌ಗಿಂತ ಹೆಚ್ಚು, ಪ್ರತಿ ಗೇಟೆಡ್ ಟೂಲ್ ಕರೆಗೆ **+44 ms** | ಆಫ್ |
| ಜಾರಿ ಪ್ರಾಕ್ಸಿ | ಪ್ರತಿ LLM ಕರೆಗೆ **+9.7 ms** | ಆಫ್ |

ಡೀಮನ್ ಹೋಸ್ಟ್ ವೆಚ್ಚ: ಇಂಜೆಸ್ಟ್‌ಗೆ **2,762 ಈವೆಂಟ್‌ಗಳು/ಸೆಕೆಂಡ್**, ಡಿಸ್ಕ್‌ನಲ್ಲಿ **ಈವೆಂಟ್‌ಗೆ 710 ಬೈಟ್‌ಗಳು**
(1,00,000 ಈವೆಂಟ್‌ಗಳಿಗೆ 67.7 MB), ಮತ್ತು ಕಾರ್ಯನಿರತ ಇನ್‌ಸ್ಟಾಲ್‌ನಲ್ಲಿ ನಿರಂತರವಾಗಿ **ಒಂದು ಕೋರ್‌ನ ~12%**.
ಆ ಕೊನೆಯ ಸಂಖ್ಯೆ ನಮ್ಮದೇ ಹೇಳಿದ 5-10% ಬಜೆಟ್‌ಗಿಂತ ಹೆಚ್ಚು, ಆದ್ದರಿಂದ ಅದನ್ನು ಪುಟದಿಂದ
ಬಿಟ್ಟುಬಿಡುವ ಬದಲು ಬೆನ್ನುಹತ್ತಬೇಕಾದ ಬಗ್ ಎಂದು ಪ್ರಕಟಿಸಲಾಗಿದೆ.

Apple M2 Pro ನಲ್ಲಿ `benchmarks/overhead.py` ಬಳಸಿ ಅಳೆಯಲಾಗಿದೆ. ಹಾರ್ನೆಸ್ ಪ್ರತಿ
ಸ್ಥಿತಿಯನ್ನು ಪ್ರತ್ಯೇಕ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿ ರನ್ ಮಾಡುತ್ತದೆ, ಅವುಗಳ ಕ್ರಮವನ್ನು ಪರ್ಯಾಯಿಸುತ್ತದೆ, ಮತ್ತು
**ರೌಂಡ್‌ಗಳು ಅದರ ಚಿಹ್ನೆಯ ಬಗ್ಗೆ ಅಸಮ್ಮತಿ ಹೊಂದಿದಾಗ ಸಂಖ್ಯೆಯನ್ನು ಮುದ್ರಿಸಲು ನಿರಾಕರಿಸುತ್ತದೆ**.
ಇದನ್ನು ನಿಮ್ಮ ಸ್ವಂತ ಯಂತ್ರದಲ್ಲಿ ಒಂದು ನಿಮಿಷದಲ್ಲಿ ರನ್ ಮಾಡಿ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ಪ್ರತಿ ಪಾತ್ ಅನ್ನು ಅಳೆಯಲಾಗಿದೆ, ಹುಕ್ ಗೇಟ್‌ಗಳು ಮತ್ತು ಜಾರಿ ಪ್ರಾಕ್ಸಿ ಸೇರಿದಂತೆ,
ಮತ್ತು ಹಾರ್ನೆಸ್ CI ನಲ್ಲಿ Linux, macOS ಮತ್ತು Windows ನಲ್ಲಿ ರನ್ ಆಗುತ್ತದೆ. ತಿಳಿಯಬೇಕಾದ ಎರಡು
ಫಲಿತಾಂಶಗಳು: ಪ್ರಾಕ್ಸಿ Windows ನಲ್ಲಿ Linux ಗಿಂತ ಸುಮಾರು ಏಳು ಪಟ್ಟು ಹೆಚ್ಚು ವೆಚ್ಚವಾಗುತ್ತದೆ,
ಮತ್ತು ಡೀಮನ್ ಪ್ರಸ್ತುತ ಒಂದು ಕೋರ್‌ನ ಸುಮಾರು 12% ಅನ್ನು ನಿರಂತರವಾಗಿ ಉಳಿಸಿಕೊಳ್ಳುತ್ತದೆ, ನಮ್ಮದೇ
5-10% ಬಜೆಟ್‌ಗಿಂತ ಹೆಚ್ಚು. ಕಚ್ಚಾ JSON, ವಿಧಾನ, ಮತ್ತು ಇನ್ನೂ ಅಳೆಯದಿರುವುದು
[docs/OVERHEAD.md](docs/OVERHEAD.md) ನಲ್ಲಿದೆ.

## ಬೆಲೆ ನಿಗದಿ

| ಪ್ಲಾನ್ | ಇದು ಏನನ್ನು ಒಳಗೊಂಡಿದೆ | ಬೆಲೆ |
|---|---|---|
| **ಉಚಿತ** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, ಪೂರ್ಣ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್, ಸ್ಥಳೀಯ ಮಾತ್ರ | $0 |
| **ಸ್ಟಾರ್ಟರ್** | ಇತರ ಎಲ್ಲಾ ರನ್‌ಟೈಮ್‌ಗಳು, ಫ್ಲೀಟ್ ವೀಕ್ಷಣೆ, ಕ್ಲೌಡ್ ಸಿಂಕ್ | ತಿಂಗಳಿಗೆ ಪ್ರತಿ ನೋಡ್‌ಗೆ $9 |
| **Pro** | ಸ್ಟಾರ್ಟರ್ + ನಿಯಂತ್ರಣ ಮತ್ತು ಮೌಲ್ಯಮಾಪನ: ಅನುಮೋದನೆಗಳು, ಟೂಲ್-ರಿಸ್ಕ್ ಪಾಲಿಸಿಗಳು, ಇವಾಲ್‌ಗಳು, ಅನಾಮಲಿ ಪತ್ತೆ, ವೆಚ್ಚ ಆಪ್ಟಿಮೈಜರ್, OTel ಎಕ್ಸ್‌ಪೋರ್ಟ್, ಟ್ಯಾಂಪರ್-ಎವಿಡೆಂಟ್ ಆಡಿಟ್ ಲಾಗ್ | ತಿಂಗಳಿಗೆ ಪ್ರತಿ ನೋಡ್‌ಗೆ $19 |

ವಾರ್ಷಿಕ ಪ್ಲಾನ್‌ಗಳು, Enterprise ಮತ್ತು ಪ್ರಸ್ತುತ ಸಂಖ್ಯೆಗಳು
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ನಲ್ಲಿವೆ. ಸ್ವಯಂ-ಹೋಸ್ಟ್ ಮಾಡಲಾದ ಲೈಸೆನ್ಸ್
ಕೀಗಳು ಕ್ಲೌಡ್ ಇಲ್ಲದೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತವೆ (`clawmetry license`). ನಿಖರ ಉಚಿತ/ಪೇಯ್ಡ್ ವಿಭಜನೆ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ನಲ್ಲಿದೆ.

## ನಿಮ್ಮ ಡೇಟಾ ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲಿಯೇ ಇರುತ್ತದೆ

ClawMetry ಸ್ಥಳೀಯ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಮತ್ತು ಲಾಗ್‌ಗಳನ್ನು ಓದುತ್ತದೆ. **ನೀವು `clawmetry connect`
ರನ್ ಮಾಡದ ಹೊರತು ಯಾವುದೇ ಸೆಷನ್ ಡೇಟಾ ನಿಮ್ಮ ಬಾಕ್ಸ್‌ನಿಂದ ಹೊರಹೋಗುವುದಿಲ್ಲ** — ಯಾವುದೇ ಪ್ರಾಂಪ್ಟ್‌ಗಳು,
ಪ್ರತಿಕ್ರಿಯೆಗಳು, ಟೂಲ್ ಆರ್ಗ್ಯುಮೆಂಟ್‌ಗಳು, ಫೈಲ್ ಕಂಟೆಂಟ್‌ಗಳು ಅಥವಾ ಲಾಗ್ ಸಾಲುಗಳು ಇಲ್ಲ. ನೀವು
ಕನೆಕ್ಟ್ ಮಾಡಿದಾಗ, ಸ್ನ್ಯಾಪ್‌ಶಾಟ್ ಅನ್ನು ನಿಮ್ಮ ಯಂತ್ರವನ್ನು ಎಂದಿಗೂ ಬಿಡದ ಕೀ ಬಳಸಿ ಎಂಡ್-ಟು-ಎಂಡ್
ಎನ್‌ಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗುತ್ತದೆ, ಮತ್ತು ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಡಿಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗುತ್ತದೆ. ಒಂದು ನೋಡ್‌ಗೆ
ಕೀ ಇಲ್ಲದಿದ್ದರೆ, ಸ್ಪಷ್ಟವಾಗಿ ಕಳುಹಿಸುವ ಬದಲು ಅಪ್‌ಲೋಡ್ ಅನ್ನು ಸ್ಕಿಪ್ ಮಾಡಲಾಗುತ್ತದೆ, ಮತ್ತು
ಯಾವುದೇ ಸರ್ವರ್ ಪ್ರತಿಕ್ರಿಯೆ ಅದನ್ನು ಆಫ್ ಮಾಡಲು ಸಾಧ್ಯವಿಲ್ಲ.

ನೀವು ಕನೆಕ್ಟ್ ಮಾಡುವ ಮೊದಲು ಡಿಫಾಲ್ಟ್ ಆಗಿ ಎರಡು ವಿಷಯಗಳು ರನ್ ಆಗುತ್ತವೆ, ಎರಡೂ ಆಪ್ಟ್-ಔಟ್
ಮಾಡಬಹುದಾದವು ಮತ್ತು ಯಾವುದೂ ಸೆಷನ್ ಡೇಟಾ ಹೊಂದಿರುವುದಿಲ್ಲ: ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಪಿಂಗ್ ಮತ್ತು
PyPI ವಿರುದ್ಧ ಆವೃತ್ತಿ ಪರಿಶೀಲನೆ. ಡಿಫಾಲ್ಟ್ ಇನ್‌ಸ್ಟಾಲ್ ಆರಂಭಿಕ ಬ್ಯಾನರ್ ಸಾಲಿಗಾಗಿ ನಿಮ್ಮ
ಸಾರ್ವಜನಿಕ IP ಅನ್ನು ಒಮ್ಮೆ ಲುಕ್‌ಅಪ್ ಮಾಡುತ್ತದೆ. ಪ್ರತಿ ಗಮ್ಯಸ್ಥಾನ, ಅದು ಏನನ್ನು ಒಯ್ಯುತ್ತದೆ ಮತ್ತು
ಅದನ್ನು ಹೇಗೆ ಆಫ್ ಮಾಡುವುದು ಎಂಬುದನ್ನು [docs/EGRESS.md](docs/EGRESS.md) ನಲ್ಲಿ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ;
ಸ್ವಯಂ-ಹೋಸ್ಟ್ ಮಾಡಲಾದ, ಮರುನಿರ್ದೇಶಿಸಲಾದ ಮತ್ತು ಏರ್-ಗ್ಯಾಪ್ಡ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು ಯಾವುದೇ
ಅಗತ್ಯ-ಆಧಾರಿತ ಔಟ್‌ಬೌಂಡ್ ಕರೆಗಳನ್ನು ಮಾಡುವುದಿಲ್ಲ.

ಡಿಕ್ರಿಪ್ಷನ್ ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ, ನಾವು ನಿಮಗೆ ಒದಗಿಸುವ ಕೋಡ್‌ನಲ್ಲಿ ನಡೆಯುತ್ತದೆ. ಇದು
ಮೊದಲು ಒಂದು ಭರವಸೆಯಾಗಿತ್ತು; ಇದು ಈಗ ನೀವು ಪರಿಶೀಲಿಸಬಹುದಾದ ಸಂಗತಿಯಾಗಿದೆ. ನಿಮ್ಮ ಕೀಯನ್ನು
ಸ್ಪರ್ಶಿಸುವ ಪ್ರತಿ ಸಾಲು ಒಂದೇ ಓದಬಹುದಾದ ಫೈಲ್‌ನಲ್ಲಿದೆ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
ಇದು ವೀಲ್‌ನಲ್ಲಿ ಹಡಗಿನಲ್ಲಿ ಬರುತ್ತದೆ ಮತ್ತು ಯಥಾರ್ಥವಾಗಿ ಸರ್ವ್ ಮಾಡಲಾಗುತ್ತದೆ, ಸಬ್‌ರಿಸೋರ್ಸ್
ಇಂಟೆಗ್ರಿಟಿ ಹ್ಯಾಶ್‌ನೊಂದಿಗೆ ಪಿನ್ ಮಾಡಲಾಗಿದೆ. ಬ್ರೌಸರ್ ನಾವು ಪ್ರಕಟಿಸಿದುದನ್ನೇ ರನ್ ಮಾಡುತ್ತದೆ ಎಂದು
ದೃಢೀಕರಿಸಲು:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ಇದು ಏನನ್ನು ಸಾಬೀತುಪಡಿಸುವುದಿಲ್ಲ: ಫೈಲ್ ಅನ್ನು ಲೋಡ್ ಮಾಡುವ ಪುಟವನ್ನು ನಾವೇ ಸರ್ವ್ ಮಾಡುತ್ತೇವೆ,
ಆದ್ದರಿಂದ ನಾವು ಬೇರೆ ಪುಟವನ್ನು ಸರ್ವ್ ಮಾಡಬಹುದಿತ್ತು. ಇಂಟೆಗ್ರಿಟಿ ಹ್ಯಾಶ್‌ಗಳು ನಿಮ್ಮನ್ನು
ಅಪಾಯಕಾರಿ CDN ನಿಂದ ರಕ್ಷಿಸುತ್ತವೆ, ವೆಂಡರ್‌ನಿಂದ ಅಲ್ಲ. ನಿಮಗೆ ಸಿಗುವುದೇನೆಂದರೆ ಯಾವುದೇ
ಬದಲಿಗೆ ಉದ್ದೇಶಪೂರ್ವಕವಾಗಿರಬೇಕು, ಪುಟದ ಮೂಲದಲ್ಲಿ ಗೋಚರಿಸಬೇಕು, ಮತ್ತು ಯಾರಾದರೂ ಪಡೆಯಬಹುದಾದ
PyPI ಮೇಲಿನ ಆರ್ಟಿಫ್ಯಾಕ್ಟ್‌ಗಿಂತ ಭಿನ್ನವಾಗಿರಬೇಕು. ಸ್ವಯಂ-ಹೋಸ್ಟಿಂಗ್ ಅಥವಾ ಸ್ಥಳೀಯವಾಗಿ ಮಾತ್ರ
ಉಳಿಯುವುದು ಈ ಅವಲಂಬನೆಯನ್ನು ಸಂಪೂರ್ಣವಾಗಿ ತೆಗೆದುಹಾಕುತ್ತದೆ.

## ಇನ್‌ಸ್ಟಾಲ್

```bash
pip install clawmetry     # ನಂತರ: clawmetry
```

ಅಥವಾ ಒನ್-ಲೈನರ್: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ಅಥವಾ Windows ನಲ್ಲಿ Python 3.8+ ಬೇಕು, ಮತ್ತು ಅದೇ ಯಂತ್ರದಲ್ಲಿ ಕನಿಷ್ಠ
ಒಂದು ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್ ಬೇಕು. Docker ಸೂಚನೆಗಳು: [docs/DOCKER.md](docs/DOCKER.md).

ಅಥವಾ ಏಜೆಂಟ್ ಅದನ್ನು ನಿಮಗಾಗಿ ಸೆಟಪ್ ಮಾಡಲಿ. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ಸ್ಕಿಲ್ Claude Code, Codex, Cursor, Gemini CLI, Copilot ಅಥವಾ OpenCode ಗೆ ClawMetry
ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡುವುದನ್ನು, ಯಂತ್ರದಲ್ಲಿರುವ ಏಜೆಂಟ್‌ಗಳು ಏನು ಮಾಡುತ್ತಿವೆ ಮತ್ತು ಖರ್ಚು ಮಾಡುತ್ತಿವೆ
ಎಂಬುದನ್ನು ವರದಿ ಮಾಡುವುದನ್ನು, ವಿನಂತಿಯ ಮೇಲೆ ಒಂದು ಸೆಷನ್ ಅನ್ನು ನಿಲ್ಲಿಸುವುದನ್ನು, ಮತ್ತು
ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅನುಮೋದನೆಗಾಗಿ ಹಿಡಿದಿಟ್ಟುಕೊಳ್ಳುವುದನ್ನು ಕಲಿಸುತ್ತದೆ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ದಾಖಲೆಗಳು

| | |
|---|---|
| [ರನ್‌ಟೈಮ್ ಹೊಂದಾಣಿಕೆ](docs/compatibility.md) | ಪ್ರತಿ ಅಡಾಪ್ಟರ್ ಏನು ಓದುತ್ತದೆ, ಮತ್ತು ರನ್‌ಟೈಮ್ ಅನ್ನು ಹೇಗೆ ಸೇರಿಸುವುದು |
| [ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್](docs/CONTEXT_BLOWOUT.md) | ಪ್ರತಿ-ಪ್ರೊವೈಡರ್ ವಿಂಡೋಗಳು, ಕಾಂಪ್ಯಾಕ್ಷನ್ ವರ್ಸಸ್ ಓವರ್‌ಫ್ಲೋ, ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ಕವರೇಜ್ |
| [ಓವರ್‌ಹೆಡ್](docs/OVERHEAD.md) | ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ನ ಅಳೆಯಲಾದ ವೆಚ್ಚ, ಅದನ್ನು ಪುನರ್ನಿರ್ಮಿಸುವ ಹಾರ್ನೆಸ್‌ನೊಂದಿಗೆ |
| [ಅರ್ಹತೆಗಳು](docs/ENTITLEMENTS.md) | ಉಚಿತ ವರ್ಸಸ್ ಪೇಯ್ಡ್, ಟಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, ಲೈಸೆನ್ಸ್ CLI |
| [ಅನುಮೋದನೆಗಳು ಮತ್ತು ಪಾಲಿಸಿಗಳು](docs/APPROVALS.md) | ಪೂರ್ವ-ಎಕ್ಸಿಕ್ಯೂಶನ್ ಗೇಟಿಂಗ್, ರಿಸ್ಕ್ ಸ್ಕೋರಿಂಗ್, ಫೋನ್ ಅನುಮೋದನೆಗಳು |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ಎಲ್ಲಿಯಾದರೂ ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಕ್ಸ್‌ಪೋರ್ಟ್ ಮಾಡಿ, ಎಲ್ಲಿಂದಾದರೂ OTLP ಇಂಜೆಸ್ಟ್ ಮಾಡಿ |
| [ನಿಮ್ಮ ಸ್ವಂತ ಏಜೆಂಟ್ ತರಿಸಿ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ಕೊನೆಯಿಂದ ಕೊನೆಗೆ, ರನ್ ಮಾಡಬಹುದಾದ ಉದಾಹರಣೆಗಳೊಂದಿಗೆ |
| [SDK ಟ್ರ್ಯಾಕಿಂಗ್](docs/SDK_TRACKING.md) | ನೀವೇ ನಿರ್ಮಿಸಿದ ಏಜೆಂಟ್‌ಗಳಿಗೆ ವೆಚ್ಚ ಗುಣಲಕ್ಷಣ |
| [ಚಾಟ್ ಚಾನೆಲ್‌ಗಳು](docs/CHANNELS.md) | ಫ್ಲೋನಲ್ಲಿ ತೋರಿಸಲಾದ ಚಾಟ್ ಅಡಾಪ್ಟರ್‌ಗಳು |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಡಲಾದ NVIDIA NemoClaw ಸೆಟಪ್‌ಗಳು |
| [Docker](docs/DOCKER.md) | ಇಮೇಜ್, ಕಂಪೋಸ್, ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು |
| [ಆರ್ಕಿಟೆಕ್ಚರ್](ARCHITECTURE.md) · [ಡೆವಲಪ್‌ಮೆಂಟ್](docs/DEVELOPMENT.md) | ಇದು ಒಳಗೆ ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ; ಮೂಲದಿಂದ ರನ್ ಮಾಡುವುದು |
| [ಟೆಲಿಮೆಟ್ರಿ](docs/TELEMETRY.md) | ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಮತ್ತು ಡೆಸ್ಕ್‌ಟಾಪ್-ಓಪನ್ ಪಿಂಗ್‌ಗಳು, ಮತ್ತು ಅವುಗಳನ್ನು ಹೇಗೆ ಆಫ್ ಮಾಡುವುದು |

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

ಕೆಳಗಿನ ಪ್ರತಿ ಸಂಖ್ಯೆಯೂ ಒಂದು ನಿಜವಾದ ಯಂತ್ರದಿಂದ, ಓದಲು-ಮಾತ್ರ, ಏನೂ ಬೀಜ ಬಿತ್ತದೆ ಪಡೆದದ್ದು.

**ಏನಾಯಿತು ಎಂಬುದನ್ನು ಮಾತ್ರವಲ್ಲ, ಏನೋ ತಪ್ಪಾಗಿದೆ ಎಂದು ಇದು ನಿಮಗೆ ಹೇಳುತ್ತದೆ.**
ಮೇಲ್ಭಾಗದಲ್ಲಿ ಎರಡು ಅನಾಮಲಿ ಬ್ಯಾನರ್‌ಗಳು: ಖರ್ಚು ದಿನದ ಸರಾಸರಿಯ 7 ಪಟ್ಟು ಚಲಿಸುತ್ತಿದೆ, ಮತ್ತು
4.2 ಪಟ್ಟು ವೆಚ್ಚ ಸ್ಪೈಕ್. ಅವುಗಳ ಕೆಳಗೆ, ಕಾರಣದ ಮೂಲಕ ವಿಭಜಿಸಲಾದ 667 ಇತ್ತೀಚಿನ ಸೆಷನ್‌ಗಳಲ್ಲಿ
324 ವೇಸ್ಟ್ ಸಿಗ್ನಲ್ ಹೊಂದಿವೆ.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ಪ್ರತಿ ವಿಂಡೋದಲ್ಲಿ ಹಣ ಎಲ್ಲಿ ಹೋಯಿತು ಎಂಬುದನ್ನು ಇದು ನಿಮಗೆ ತೋರಿಸುತ್ತದೆ.**
ಇಂದು $252.47, ಈ ವಾರ $513.15, ಈ ತಿಂಗಳು $1,312.92, ಪ್ರತಿಯೊಂದೂ ಅದರ ಹಿಂದಿನ ಟೋಕನ್‌ಗಳೊಂದಿಗೆ
ಮತ್ತು ನಿಮ್ಮ ಸಬ್ಸ್ಕ್ರಿಪ್ಷನ್ ಈಗಾಗಲೇ ಎಷ್ಟು ಒಳಗೊಂಡಿದೆ ಎಂಬುದರೊಂದಿಗೆ. ಅದರ ಕೆಳಗೆ, ಸುಮಾರು
$1,128/ಮಾಸ ಮರುಪಡೆಯಬಹುದಾದ ಎಂದು ವಿಭಜಿಸಲಾಗಿದೆ ಮತ್ತು $17,256/ಮಾಸ ಈಗಾಗಲೇ ಕ್ಯಾಶ್ ಪುನರ್ಬಳಕೆಯಿಂದ
ಉಳಿಸಲಾಗಿದೆ.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ಸಂದೇಶ ಹೇಗೆ ಉತ್ತರವಾಗುತ್ತದೆ ಎಂಬುದನ್ನು ಇದು ಚಿತ್ರಿಸುತ್ತದೆ.**
ಲೈವ್ ಫ್ಲೋ ರೇಖಾಚಿತ್ರ: ನೀವು, ಅದು ಬಂದ ಚಾನೆಲ್, ಗೇಟ್‌ವೇ, ಈಗ ಉತ್ತರಿಸುತ್ತಿರುವ ಮಾಡೆಲ್, ಮತ್ತು
ಅದು ಬಳಸಿದ ಪ್ರತಿ ಟೂಲ್. ಕೆಲಸ ಅವುಗಳ ಮೂಲಕ ಹರಿಯುತ್ತಿದ್ದಂತೆ ನೋಡ್‌ಗಳು ಬೆಳಗುತ್ತವೆ.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ಯಂತ್ರದಲ್ಲಿರುವ ಪ್ರತಿ ಏಜೆಂಟ್, ಒಂದೇ ಟೇಬಲ್‌ನಲ್ಲಿ.**
ಅದು ಏನು ರನ್ ಮಾಡುತ್ತದೆ, ಕಳೆದ 24 ಗಂಟೆಗಳಲ್ಲಿ ಮತ್ತು ಅದರ ಜೀವಿತಾವಧಿಯಲ್ಲಿ ಅದರ ವೆಚ್ಚ ಎಷ್ಟು,
ಅದನ್ನು ಕೊನೆಯ ಬಾರಿ ಯಾವಾಗ ನೋಡಲಾಗಿತ್ತು, ಅದನ್ನು ಯಾರು ಹೊಂದಿದ್ದಾರೆ, ಮತ್ತು ಸಬ್ಸ್ಕ್ರಿಪ್ಷನ್
ಬಿಲ್ ಅನ್ನು ಕವರ್ ಮಾಡುತ್ತಿದೆಯೇ. ಇಲ್ಲಿ 14 ಏಜೆಂಟ್‌ಗಳು, 3 ಸೆಷನ್‌ಗಳು ಕೆಲಸ ಮಾಡುತ್ತಿವೆ, 13
ಶಾಂತವಾಗಿವೆ.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ಟರ್ನ್‌ನ ಸಮಯ ಮತ್ತು ಹಣ ಎಲ್ಲಿ ಹೋಯಿತು ಎಂಬುದನ್ನು ಟೂಲ್ ಬೈ ಟೂಲ್ ಇದು ತೋರಿಸುತ್ತದೆ.**
ನಿಜವಾದ ಸೆಷನ್‌ನ ಒಂದು ಟರ್ನ್: $1.16 ಗೆ 11.2 ನಿಮಿಷಗಳಲ್ಲಿ 11 ಟೂಲ್‌ಗಳು. ಪ್ರತಿ Bash ಕರೆ ಮತ್ತು
ಮಾಡೆಲ್ ಕರೆ ಟೈಮ್‌ಲೈನ್‌ನಲ್ಲಿ ತನ್ನದೇ ಬಾರ್ ಹೊಂದಿದ್ದು, ಆದ್ದರಿಂದ 4.1 ನಿಮಿಷಗಳ ಕಾಲ ರನ್ ಆದ
ಕಮಾಂಡ್ ಮತ್ತು 226ms ಕಾಲ ರನ್ ಆದದ್ದನ್ನು ಒಂದೇ ನೋಟದಲ್ಲಿ ಬೇರೆ ಬೇರೆಯಾಗಿ ಹೇಳಬಹುದು.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ಇದು ಕೆಲಸವನ್ನು ಗ್ರೇಡ್ ಮಾಡುತ್ತದೆ, ಖರ್ಚನ್ನು ಮಾತ್ರವಲ್ಲ.**
ಈ ವಾರ A: 54 ಕೆಲಸಗಳು ಸ್ವಚ್ಛವಾಗಿ ಹಿಂತಿರುಗಿದವು, 2 ಕಠಿಣ ಕೆಲಸಗಳು $48.57 ವೆಚ್ಚ ಮಾಡಿದವು,
ಮತ್ತು ನಿರ್ಣಯಿಸಲು ಸಾಕಷ್ಟು ಚಟುವಟಿಕೆ ಇಲ್ಲದ ರನ್‌ಗಳನ್ನು ಗೆಲುವುಗಳೆಂದು ಎಣಿಸುವ ಬದಲು ಗ್ರೇಡ್‌ನಿಂದ
ಬಿಟ್ಟುಬಿಡಲಾಗಿದೆ. ಪ್ರತಿ ಕಠಿಣ ರನ್ ಅದರ ಟ್ರೇಸ್‌ಗೆ ಲಿಂಕ್ ಆಗುತ್ತದೆ.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ಕಾಂಟೆಕ್ಸ್ಟ್ ವಿಂಡೋ ಏಕೆ ತುಂಬುತ್ತಲೇ ಇರುತ್ತದೆ ಎಂಬುದನ್ನು ಇದು ತೋರಿಸುತ್ತದೆ.**
ಇತ್ತೀಚಿನ ಟರ್ನ್‌ನಲ್ಲಿ 1M-ಟೋಕನ್ ವಿಂಡೋದ 715K, 83.3% ಪೀಕ್, ಓವರ್‌ಫ್ಲೋಗಿಂತ ಪ್ರೋಆಕ್ಟಿವ್ ಆಗಿ
ಎಲ್ಲಾ 4 ಫೈರ್ ಆದ ಕಾಂಪ್ಯಾಕ್ಷನ್‌ಗಳು, ಮತ್ತು ಅದರ ಹಿಂದಿನ ಪ್ರತಿ ಟರ್ನ್‌ನ ಬಳಕೆ.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ನೀವು ಏನನ್ನೂ ಕಾನ್ಫಿಗರ್ ಮಾಡದೆ ಪತ್ತೆಹಚ್ಚುವಿಕೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ.**
ಅಂತರ್ನಿರ್ಮಿತ ಡಿಟೆಕ್ಟರ್‌ಗಳು ಇನ್‌ಸ್ಟಾಲ್‌ನಿಂದ ಆನ್ ಆಗಿವೆ: ಏಜೆಂಟ್ ಶಾಂತವಾಯಿತು, ಟೆಲಿಮೆಟ್ರಿ ಫೀಡ್
ನಿಲ್ಲಿಸಿತು, ವೆಚ್ಚ ಸ್ಪೈಕ್, ಟೋಕನ್ ಬರ್ಸ್ಟ್, ಎರರ್‌ಗಳು ಹೆಚ್ಚುತ್ತಿವೆ, ಎರರ್ ಸ್ಪೈಕ್, ಬಜೆಟ್
ಮಿತಿ, ಬೆದರಿಕೆ ಸಿಗ್ನೇಚರ್ ಹೊಂದಾಣಿಕೆಯಾಯಿತು, ಸೆಕ್ಯುರಿಟಿ ಟೂಲ್ ಶೋಧನೆ, ಸೆಕ್ಯುರಿಟಿ ಸ್ಥಿತಿ
ಬದಲಾಯಿತು. ನಿಮ್ಮ ಸ್ವಂತ ನಿಯಮಗಳು ಇದರ ಮೇಲೆ ಐಚ್ಛಿಕ.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ಅಪಾಯಕಾರಿ ಕರೆಯನ್ನು ಹಿಡಿದಿಟ್ಟುಕೊಳ್ಳುವುದು ಆಪ್ಟ್-ಇನ್, ಮತ್ತು ಆಫ್ ಆಗಿ ಹಡಗಿಗೆ ಬರುತ್ತದೆ.**
ಪುನರಾವರ್ತಿತ ಡಿಲೀಟ್‌ಗಳು, ಫೋರ್ಸ್ ಪುಶ್‌ಗಳು, sudo, ಸೀಕ್ರೆಟ್‌ಗಳು, ಪ್ಯಾಕೇಜ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು ಮತ್ತು
ಔಟ್‌ಬೌಂಡ್ ಕರೆಗಳು ಪ್ರತಿಯೊಂದೂ ನೀವು ಆನ್ ಮಾಡಬಹುದಾದ ನಿಯಮವನ್ನು ಹೊಂದಿವೆ. ನೀವು ಹಾಗೆ ಮಾಡುವವರೆಗೆ,
ClawMetry ಗಮನಿಸುತ್ತದೆ ಮತ್ತು ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ. ಒಂದು ಆನ್ ಆದ ನಂತರ, ಹೊಂದಾಣಿಕೆಯಾಗುವ
ಕರೆಗಳು ಇಲ್ಲಿ (ಅಥವಾ ನಿಮ್ಮ ಫೋನ್‌ನಲ್ಲಿ) ಅನುಮೋದನೆ ಅಥವಾ ನಿರಾಕರಣೆಗಾಗಿ ಕಾಯುತ್ತವೆ.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ಇನ್ನೂ ಹೆಚ್ಚು, ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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

## ಲೈಸೆನ್ಸ್

MIT · [@vivekchand](https://github.com/vivekchand) ಅವರಿಂದ ನಿರ್ಮಿಸಲಾಗಿದೆ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
