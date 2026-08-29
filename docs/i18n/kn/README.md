<!-- i18n-src:d21bea5161e0 -->
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

**ನಿಮ್ಮ ಏಜೆಂಟ್ ಯೋಚಿಸುವುದನ್ನು ನೋಡಿ.** **30 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳಿಗೆ** ನೈಜ-ಸಮಯದ ಅಬ್ಸರ್ವಬಿಲಿಟಿ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ಮತ್ತು ಇನ್ನೂ 26. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.

> 🌐 **ಇದನ್ನು ಈ ಭಾಷೆಗಳಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದು ಆದೇಶ. ಸೊನ್ನೆ ಕಾನ್ಫಿಗ್. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆ ಮಾಡುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆಯುತ್ತದೆ. ಸೊನ್ನೆ ಕಾನ್ಫಿಗ್: ನಿಮ್ಮಲ್ಲಿ ಈಗಾಗಲೇ ಇರುವ ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಇದು ಕಂಡುಹಿಡಿಯುತ್ತದೆ, ಅವುಗಳನ್ನು ಓದಲು-ಮಾತ್ರ ಓದುತ್ತದೆ, ಮತ್ತು ಅವು ಹೇಗೆ ಚಲಿಸುತ್ತವೆ ಎಂಬುದರ ಬಗ್ಗೆ ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ

**ಓಪನ್ ಸೋರ್ಸ್ ಆ್ಯಪ್‌ನಲ್ಲಿ ಉಚಿತ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ಪಾವತಿಸಿದ ಯೋಜನೆಯಲ್ಲಿ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ಪ್ರತಿಯೊಂದು ರನ್‌ಟೈಮ್‌ಗೂ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಸಿಗುತ್ತದೆ. ಹಲವನ್ನು ಒಂದೇ ಬಾರಿಗೆ ಚಲಾಯಿಸಿ, ಮತ್ತು ಹೆಡರ್ ಸ್ವಿಚರ್ ಪ್ರತಿ ಟ್ಯಾಬ್‌ ಅನ್ನು ಅವುಗಳಲ್ಲಿ ಒಂದಕ್ಕೆ ಮರುಸ್ಕೋಪ್ ಮಾಡುತ್ತದೆ.

SDK ಬಳಸಿ ನಿಮ್ಮದೇ ಆದ ಏಜೆಂಟ್ ಅನ್ನು ನಿರ್ಮಿಸಿದ್ದೀರಾ? ಇಂಟರ್‌ಸೆಪ್ಟರ್ ಅದರ LLM ಕರೆಗಳನ್ನೂ ಟ್ರ್ಯಾಕ್ ಮಾಡುತ್ತದೆ. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ನೋಡಿ.

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **ಸೆಷನ್‌ಗಳು ಮತ್ತು ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು**: ಪ್ರತಿ ಏಜೆಂಟ್ ಏನು ಮಾಡಿತು, ಟರ್ನ್ ಟರ್ನ್‌ಗೆ, ರೀಪ್ಲೇ ಸಮೇತ
- **ವೆಚ್ಚ ಮತ್ತು ಟೋಕನ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್, ಮಾಡೆಲ್, ಸೆಷನ್ ಮತ್ತು ದಿನಕ್ಕೆ, ಅಸಂಗತತೆಯ ಫ್ಲ್ಯಾಗ್‌ಗಳ ಸಮೇತ
- **ಫ್ಲೋ**: ಚಾನೆಲ್‌ಗಳು, ಮಾಡೆಲ್‌ಗಳು ಮತ್ತು ಟೂಲ್‌ಗಳ ಮೂಲಕ ಚಲಿಸುವ ಸಂದೇಶಗಳ ಲೈವ್ ಡಯಾಗ್ರಾಂ
- **ಬ್ರೈನ್**: ರೀಸನಿಂಗ್ ಮತ್ತು ಟೂಲ್-ಕರೆ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್ ಅದು ಸಂಭವಿಸಿದಂತೆಯೇ
- **ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್**: ಪ್ರತಿ ಪ್ರೊವೈಡರ್‌ಗೆ ಅನುಗುಣವಾಗಿ ಗಾತ್ರ ನಿಗದಿಪಡಿಸಿದ ವಿಂಡೋ ಬಳಕೆ, ಕಂಪ್ಯಾಕ್ಷನ್ vs ಬಲವಂತದ ಓವರ್‌ಫ್ಲೋ, ಜೊತೆಗೆ ನಮಗೆ *ಕಾಣದಿರುವುದು* ಏನು ಎಂಬುದರ ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ನಕ್ಷೆ ([ಹೇಗೆ](docs/CONTEXT_BLOWOUT.md))
- **ಮೆಮೊರಿ ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್ ವಾಸ್ತವವಾಗಿ ಲೋಡ್ ಮಾಡಿದ ಫೈಲ್‌ಗಳು ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು
- **ಆರೋಗ್ಯ ಮತ್ತು ಲಾಗ್‌ಗಳು**: ಡಿಸ್ಕ್, ಮೆಮೊರಿ, ದೋಷ ದರಗಳು, ರೇಟ್ ಲಿಮಿಟ್‌ಗಳು, ಲೈವ್ ಲಾಗ್ ಸ್ಟ್ರೀಮ್
- **ಎಚ್ಚರಿಕೆಗಳು**: ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷದ ಉಲ್ಬಣ, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್, Slack, Discord, PagerDuty, Telegram, Email ಗೆ ರೂಟ್ ಮಾಡಲಾಗಿದೆ
- **ಅನುಮೋದನೆಗಳು**: ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅವು ಚಲಾಯಿಸುವ *ಮೊದಲು* ವಿರಾಮಗೊಳಿಸಿ ಮತ್ತು ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಅನುಮೋದಿಸಿ ([ಹೇಗೆ](docs/APPROVALS.md))

## ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್, ಮತ್ತು ಗಮನಿಸುವುದಕ್ಕೆ ಎಷ್ಟು ವೆಚ್ಚ

ಯಾವುದೇ ಏಜೆಂಟ್-ಹೋಲಿಕೆ ಟೂಲ್ ಅನ್ನು ನಂಬುವ ಮೊದಲು ಉತ್ತರಿಸಬೇಕಾದ ಎರಡು ಪ್ರಶ್ನೆಗಳು.

**ರನ್‌ಟೈಮ್‌ಗಳಾದ್ಯಂತ ಕಾಂಟೆಕ್ಸ್ಟ್-ವಿಂಡೋ ಬ್ಲೋಔಟ್ ಅನ್ನು ಇದು ಹೇಗೆ ನಿಭಾಯಿಸುತ್ತದೆ?**

ಬಳಕೆ ಶೇಕಡಾವಾರು ಎಷ್ಟು ಪ್ರಾಮಾಣಿಕ ಎಂಬುದು ಅದನ್ನು ಯಾವುದರಿಂದ ಭಾಗಿಸಲಾಗುತ್ತದೆ ಎಂಬುದರ ಮೇಲೆ ಅವಲಂಬಿತ. ClawMetry, ನೀವು ಓದಬಹುದಾದ ಮತ್ತು PR ಮಾಡಬಹುದಾದ [ಒಂದು ಟೇಬಲ್‌ನಿಂದ](clawmetry/context_windows.py) ಪ್ರತಿ ಪ್ರೊವೈಡರ್‌ಗೆ ಅನುಗುಣವಾಗಿ ವಿಂಡೋ ಗಾತ್ರ ನಿಗದಿಪಡಿಸುತ್ತದೆ, ಇದು Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama ಮತ್ತು GLM ಅನ್ನು ಒಳಗೊಂಡಿದೆ. ಇದು ಎಲ್ಲಾ 26 ರನ್‌ಟೈಮ್‌ಗಳನ್ನೂ ಒಂದೇ ವೆಂಡರ್‌ನ ಅಳತೆಗೋಲಿನಿಂದ ಅಳೆಯುವುದಿಲ್ಲ. ಇದು ಮುಖ್ಯ: 300K GPT-5 ಟರ್ನ್ ಅನ್ನು Anthropic ನ 200K ಎಂಬುದರ ವಿರುದ್ಧ ಅಂಕಗಳಿಸಿದರೆ ">100%, blown" ಎಂದು ಓದುತ್ತದೆ, ಆದರೆ ಅದು ವಾಸ್ತವವಾಗಿ GPT-5 ನ 400K ಯ 75% ರಷ್ಟಿದೆ. ಅದೇ ಅಳತೆಗೋಲು ನಿಜವಾಗಿಯೂ ಓವರ್‌ಫ್ಲೋ ಆದ 130K DeepSeek ಟರ್ನ್ ಅನ್ನು ಆರಾಮದಾಯಕ 65% ಎಂದು ಮರೆಮಾಚುತ್ತದೆ.

ಪ್ರತಿ ವಿಂಡೋ ತನ್ನ ಮೂಲದ ಜೊತೆಗೆ ಬರುತ್ತದೆ: `model_table`, `explicit_marker`, `observed_floor`, ಅಥವಾ ನಮಗೆ ಮಾಡೆಲ್ ಗೊತ್ತಿಲ್ಲದಿದ್ದಾಗ ಪ್ರಾಮಾಣಿಕ `default`. ಊಹೆಯ ಆಧಾರದ ಮೇಲೆ ನಿರ್ಮಿಸಲಾದ ಗೇಜ್ ಎಂದಿಗೂ ಲುಕ್‌ಅಪ್‌ನ ಆಧಾರದ ಮೇಲೆ ನಿರ್ಮಿಸಲಾದ ಅದೇ ಅಧಿಕಾರದೊಂದಿಗೆ ರೆಂಡರ್ ಆಗುವುದಿಲ್ಲ.

ClawMetry ಕೆಲವು ರನ್‌ಟೈಮ್‌ಗಳಲ್ಲಿ ಮಾತ್ರ ಕಂಪ್ಯಾಕ್ಷನ್ ಈವೆಂಟ್‌ಗಳನ್ನು ನೋಡಬಲ್ಲದು. ಆದ್ದರಿಂದ `GET /api/context-coverage`, ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ, ಸೊನ್ನೆ ಎಂಬುದು **"ಸ್ವಚ್ಛವಾಗಿ ಓಡಿತು" ಎಂದೋ ಅಥವಾ "ನಮಗೆ ಕಾಣುತ್ತಿಲ್ಲ" ಎಂದೋ** ಎಂಬುದನ್ನು ವರದಿ ಮಾಡುತ್ತದೆ. ವಾಸ್ತವವಾಗಿ ಕುರುಡು ಎಂದರ್ಥ ಬರುವ `0` ಆ ಬಗ್ಗೆಯೇ ಹೇಳುತ್ತದೆ. [ಸಂಪೂರ್ಣ ವಿವರ](docs/CONTEXT_BLOWOUT.md)

**ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ನ ವೆಚ್ಚ ಎಷ್ಟು?**

| ಪಥ | ನಿಮ್ಮ ಏಜೆಂಟ್‌ಗೆ ಸೇರಿಸಲಾದದ್ದು | ಡೀಫಾಲ್ಟ್? |
|---|---|---|
| ಸೆಷನ್-ಫೈಲ್ ಟೈಲಿಂಗ್ (ಎಲ್ಲಾ 30 ರನ್‌ಟೈಮ್‌ಗಳು) | **0**. ಪ್ರತ್ಯೇಕ ಪ್ರಕ್ರಿಯೆ, ನಿಮ್ಮ ಏಜೆಂಟ್‌ನಲ್ಲಿ ClawMetry ಕೋಡ್ ಇಲ್ಲ | ಆನ್ |
| HTTP ಇಂಟರ್‌ಸೆಪ್ಟರ್ (`CLAWMETRY_INTERCEPT=1`) | ಪ್ರತಿ LLM ಕರೆಗೆ **+0.44 ms**, ಅಥವಾ 5s ಕರೆಯ 0.009% | ಆಫ್ |
| ಪ್ರೀ-ಟೂಲ್ ಹುಕ್ ಗೇಟ್ (ವಾರ್ಮ್ ಕ್ಯಾಶ್) | 36 ms ಇಂಟರ್‌ಪ್ರಿಟರ್ ನೆಲಗಟ್ಟಿನ ಮೇಲೆ, ಪ್ರತಿ ಗೇಟ್ ಮಾಡಿದ ಟೂಲ್ ಕರೆಗೆ **+44 ms** | ಆಫ್ |
| ಎನ್‌ಫೋರ್ಸ್‌ಮೆಂಟ್ ಪ್ರಾಕ್ಸಿ | ಪ್ರತಿ LLM ಕರೆಗೆ **+9.7 ms** | ಆಫ್ |

ಡೀಮನ್ ಹೋಸ್ಟ್ ವೆಚ್ಚ: **2,762 ಈವೆಂಟ್/ಸೆಕೆಂಡ್** ಇಂಜೆಸ್ಟ್, ಡಿಸ್ಕ್‌ನಲ್ಲಿ **710 ಬೈಟ್/ಈವೆಂಟ್** (100k ಈವೆಂಟ್‌ಗಳಿಗೆ 67.7 MB), ಮತ್ತು ಬ್ಯುಸಿ ಇನ್‌ಸ್ಟಾಲ್‌ನಲ್ಲಿ ಸಸ್ಟೇನ್ಡ್ **ಒಂದು ಕೋರ್‌ನ ~12%**. ಆ ಕೊನೆಯ ಸಂಖ್ಯೆ ನಮ್ಮ ಸ್ವಂತ ಘೋಷಿತ 5-10% ಬಜೆಟ್ ಮೀರಿದೆ, ಆದ್ದರಿಂದ ಅದನ್ನು ಪುಟದಿಂದ ಬಿಡುವ ಬದಲು ಬೆನ್ನಟ್ಟಬೇಕಾದ ಬಗ್ ಎಂದೇ ಪ್ರಕಟಿಸಲಾಗಿದೆ.

Apple M2 Pro ಮೇಲೆ `benchmarks/overhead.py` ಬಳಸಿ ಅಳೆಯಲಾಗಿದೆ. ಹಾರ್ನೆಸ್ ಪ್ರತಿ ಸ್ಥಿತಿಯನ್ನೂ ಪ್ರತ್ಯೇಕ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿ ಚಲಾಯಿಸುತ್ತದೆ, ಅವುಗಳ ಕ್ರಮವನ್ನು ಪರ್ಯಾಯಗೊಳಿಸುತ್ತದೆ, ಮತ್ತು **ಸುತ್ತುಗಳು ಚಿಹ್ನೆಯ ಬಗ್ಗೆ ಒಪ್ಪದಿದ್ದಾಗ ಸಂಖ್ಯೆಯನ್ನು ಮುದ್ರಿಸಲು ನಿರಾಕರಿಸುತ್ತದೆ**. ಇದನ್ನು ನಿಮ್ಮದೇ ಯಂತ್ರದಲ್ಲಿ ಒಂದು ನಿಮಿಷದಲ್ಲಿ ಚಲಾಯಿಸಿ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ಹುಕ್ ಗೇಟ್‌ಗಳು ಮತ್ತು ಎನ್‌ಫೋರ್ಸ್‌ಮೆಂಟ್ ಪ್ರಾಕ್ಸಿ ಸೇರಿದಂತೆ ಪ್ರತಿ ಪಥವನ್ನೂ ಅಳೆಯಲಾಗಿದೆ, ಮತ್ತು ಹಾರ್ನೆಸ್ Linux, macOS ಮತ್ತು Windows ನಲ್ಲಿ CI ನಲ್ಲಿ ಚಲಿಸುತ್ತದೆ. ತಿಳಿದುಕೊಳ್ಳಬೇಕಾದ ಎರಡು ಫಲಿತಾಂಶಗಳು: ಪ್ರಾಕ್ಸಿ Windows ನಲ್ಲಿ Linux ಗಿಂತ ಸುಮಾರು ಏಳು ಪಟ್ಟು ಹೆಚ್ಚು ವೆಚ್ಚವಾಗುತ್ತದೆ, ಮತ್ತು ಡೀಮನ್ ಪ್ರಸ್ತುತ ಒಂದು ಕೋರ್‌ನ ಸುಮಾರು 12% ಅನ್ನು ಸಸ್ಟೇನ್ ಮಾಡುತ್ತದೆ, ಇದು ನಮ್ಮ ಸ್ವಂತ 5-10% ಬಜೆಟ್ ಮೀರಿದೆ. ಕಚ್ಚಾ JSON, ವಿಧಾನ, ಮತ್ತು ಇನ್ನೂ ಅಳೆಯದೇ ಇರುವುದು [docs/OVERHEAD.md](docs/OVERHEAD.md) ನಲ್ಲಿದೆ.

## ಬೆಲೆ ನಿಗದಿ

| ಯೋಜನೆ | ಇದು ಏನನ್ನು ಒಳಗೊಂಡಿದೆ | ಬೆಲೆ |
|---|---|---|
| **ಉಚಿತ** | OpenClaw + NVIDIA NemoClaw + Goose, ಸಂಪೂರ್ಣ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್, ಸ್ಥಳೀಯ ಮಾತ್ರ | $0 |
| **ಸ್ಟಾರ್ಟರ್** | ಮೇಲಿನ ಪ್ರತಿಯೊಂದು ಇತರ ರನ್‌ಟೈಮ್, ಫ್ಲೀಟ್ ವ್ಯೂ, ಕ್ಲೌಡ್ ಸಿಂಕ್ | ತಿಂಗಳಿಗೆ ನೋಡ್‌ಗೆ $9 |
| **Pro** | ಸ್ಟಾರ್ಟರ್ + ನಿಯಂತ್ರಣ ಮತ್ತು ಮೌಲ್ಯಮಾಪನ: ಅನುಮೋದನೆಗಳು, ಟೂಲ್-ರಿಸ್ಕ್ ನೀತಿಗಳು, ಇವಾಲ್‌ಗಳು, ಅಸಂಗತತೆ ಪತ್ತೆ, ವೆಚ್ಚ ಆಪ್ಟಿಮೈಸರ್, OTel ಎಕ್ಸ್‌ಪೋರ್ಟ್, ಟ್ಯಾಂಪರ್-ಎವಿಡೆಂಟ್ ಆಡಿಟ್ ಲಾಗ್ | ತಿಂಗಳಿಗೆ ನೋಡ್‌ಗೆ $19 |

ವಾರ್ಷಿಕ ಯೋಜನೆಗಳು, ಎಂಟರ್‌ಪ್ರೈಸ್ ಮತ್ತು ಪ್ರಸ್ತುತ ಸಂಖ್ಯೆಗಳು **[clawmetry.com/pricing](https://clawmetry.com/pricing)** ನಲ್ಲಿ ಇವೆ. ಸ್ವಯಂ-ಹೋಸ್ಟ್ ಮಾಡಿದ ಲೈಸೆನ್ಸ್ ಕೀಗಳು ಕ್ಲೌಡ್ ಇಲ್ಲದೆಯೂ ಕೆಲಸ ಮಾಡುತ್ತವೆ (`clawmetry license`). ಉಚಿತ/ಪಾವತಿಸಿದ ವಿಭಜನೆಯ ನಿಖರ ವಿವರ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ನಲ್ಲಿದೆ.

## ನಿಮ್ಮ ಡೇಟಾ ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲಿಯೇ ಇರುತ್ತದೆ

ClawMetry ಸ್ಥಳೀಯ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಮತ್ತು ಲಾಗ್‌ಗಳನ್ನು ಓದುತ್ತದೆ. **ನೀವು `clawmetry connect` ಅನ್ನು ಚಲಾಯಿಸದ ಹೊರತು ನಿಮ್ಮ ಪೆಟ್ಟಿಗೆಯಿಂದ ಯಾವುದೇ ಸೆಷನ್ ಡೇಟಾ ಹೊರಗೆ ಹೋಗುವುದಿಲ್ಲ** — ಯಾವುದೇ ಪ್ರಾಂಪ್ಟ್‌ಗಳು, ಪ್ರತ್ಯುತ್ತರಗಳು, ಟೂಲ್ ಆರ್ಗ್ಯುಮೆಂಟ್‌ಗಳು, ಫೈಲ್ ವಿಷಯಗಳು ಅಥವಾ ಲಾಗ್ ಸಾಲುಗಳಲ್ಲ. ನೀವು ಕನೆಕ್ಟ್ ಮಾಡಿದಾಗ, ಸ್ನ್ಯಾಪ್‌ಶಾಟ್ ಅನ್ನು ನಿಮ್ಮ ಯಂತ್ರವನ್ನು ಎಂದಿಗೂ ಬಿಡದ ಕೀ ಮೂಲಕ ಎಂಡ್-ಟು-ಎಂಡ್ ಎನ್‌ಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗುತ್ತದೆ, ಮತ್ತು ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಡಿಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗುತ್ತದೆ. ಒಂದು ನೋಡ್‌ಗೆ ಕೀ ಇಲ್ಲದಿದ್ದರೆ, ಅಪ್‌ಲೋಡ್ ಅನ್ನು ಸ್ಪಷ್ಟ ಪಠ್ಯದಲ್ಲಿ ಕಳುಹಿಸುವ ಬದಲು ಬಿಟ್ಟುಬಿಡಲಾಗುತ್ತದೆ, ಮತ್ತು ಯಾವುದೇ ಸರ್ವರ್ ಪ್ರತಿಕ್ರಿಯೆಯೂ ಅದನ್ನು ಆಫ್ ಮಾಡಲಾರದು.

ನೀವು ಕನೆಕ್ಟ್ ಮಾಡುವ ಮೊದಲು ಡೀಫಾಲ್ಟ್ ಆಗಿ ಎರಡು ವಿಷಯಗಳು ಚಲಿಸುತ್ತವೆ, ಎರಡೂ ಆಪ್ಟ್-ಔಟ್ ಮತ್ತು ಯಾವುದೂ ಸೆಷನ್ ಡೇಟಾ ಹೊತ್ತೊಯ್ಯುವುದಿಲ್ಲ: ಒಂದು ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಪಿಂಗ್ ಮತ್ತು PyPI ವಿರುದ್ಧ ಒಂದು ಆವೃತ್ತಿ ಪರಿಶೀಲನೆ. ಡೀಫಾಲ್ಟ್ ಇನ್‌ಸ್ಟಾಲ್ ಒಂದು ಸ್ಟಾರ್ಟ್‌ಅಪ್ ಬ್ಯಾನರ್ ಸಾಲಿಗಾಗಿ ನಿಮ್ಮ ಸಾರ್ವಜನಿಕ IP ಅನ್ನು ಒಮ್ಮೆ ಹುಡುಕುತ್ತದೆ. ಪ್ರತಿ ಗಮ್ಯಸ್ಥಾನ, ಅದು ಏನನ್ನು ಹೊತ್ತೊಯ್ಯುತ್ತದೆ ಮತ್ತು ಅದನ್ನು ಹೇಗೆ ಆಫ್ ಮಾಡುವುದು ಎಂಬುದನ್ನು [docs/EGRESS.md](docs/EGRESS.md) ನಲ್ಲಿ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ; ಸ್ವಯಂ-ಹೋಸ್ಟ್ ಮಾಡಿದ, ಮರುನಿರ್ದೇಶಿಸಿದ ಮತ್ತು ಏರ್-ಗ್ಯಾಪ್ಡ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು ಯಾವುದೇ ಐಚ್ಛಿಕ ಔಟ್‌ಬೌಂಡ್ ಕರೆಗಳನ್ನು ಮಾಡುವುದಿಲ್ಲ.

ಡಿಕ್ರಿಪ್ಷನ್ ನಾವು ನಿಮಗೆ ನೀಡುವ ಕೋಡ್‌ನಲ್ಲಿ, ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ನಡೆಯುತ್ತದೆ. ಅದು ಹಿಂದೆ ಒಂದು ವಾಗ್ದಾನವಾಗಿತ್ತು; ಈಗ ಅದು ನೀವು ಪರಿಶೀಲಿಸಬಹುದಾದ ಸಂಗತಿ. ನಿಮ್ಮ ಕೀಯನ್ನು ಸ್ಪರ್ಶಿಸುವ ಪ್ರತಿ ಸಾಲೂ ಒಂದೇ ಓದಬಹುದಾದ ಫೈಲ್‌ನಲ್ಲಿ ವಾಸಿಸುತ್ತದೆ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ಇದು wheel ಒಳಗೆ ಸಾಗಿಸಲ್ಪಡುತ್ತದೆ ಮತ್ತು ಸಬ್‌ರಿಸೋರ್ಸ್ ಇಂಟೆಗ್ರಿಟಿ ಹ್ಯಾಶ್‌ನೊಂದಿಗೆ ಪಿನ್ ಮಾಡಿ ಯಥಾವತ್ತಾಗಿ ಸರ್ವ್ ಮಾಡಲಾಗುತ್ತದೆ. ಬ್ರೌಸರ್ ನಾವು ಪ್ರಕಟಿಸಿದ್ದನ್ನೇ ಚಲಾಯಿಸುತ್ತದೆ ಎಂದು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಲು:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ಇದು ಸಾಬೀತುಪಡಿಸದ್ದು ಏನೆಂದರೆ: ಫೈಲ್ ಲೋಡ್ ಮಾಡುವ ಪುಟವನ್ನು ನಾವೇ ಸರ್ವ್ ಮಾಡುತ್ತೇವೆ, ಆದ್ದರಿಂದ ನಾವು ಬೇರೆ ಪುಟವನ್ನೂ ಸರ್ವ್ ಮಾಡಬಹುದು. ಇಂಟೆಗ್ರಿಟಿ ಹ್ಯಾಶ್‌ಗಳು ರಾಜಿಯಾದ CDN ನಿಂದ ನಿಮ್ಮನ್ನು ರಕ್ಷಿಸುತ್ತವೆ, ಆದರೆ ವೆಂಡರ್‌ನಿಂದ ಅಲ್ಲ. ನೀವು ಗಳಿಸುವುದೇನೆಂದರೆ ಯಾವುದೇ ಬದಲಿ ಉದ್ದೇಶಪೂರ್ವಕವಾಗಿರಬೇಕು, ಪುಟದ ಮೂಲದಲ್ಲಿ ಗೋಚರಿಸಬೇಕು, ಮತ್ತು ಯಾರಾದರೂ ಪಡೆಯಬಹುದಾದ PyPI ಯಲ್ಲಿನ ಆರ್ಟಿಫ್ಯಾಕ್ಟ್‌ಗಿಂತ ಭಿನ್ನವಾಗಿರಬೇಕು. ಸ್ವಯಂ-ಹೋಸ್ಟಿಂಗ್ ಅಥವಾ ಸ್ಥಳೀಯ-ಮಾತ್ರ ಉಳಿಯುವುದು ಈ ಅವಲಂಬನೆಯನ್ನೇ ತೆಗೆದುಹಾಕುತ್ತದೆ.

## ಇನ್‌ಸ್ಟಾಲ್

```bash
pip install clawmetry     # ನಂತರ: clawmetry
```

ಅಥವಾ ಒಂದು-ಸಾಲಿನ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ಅಥವಾ Windows ನಲ್ಲಿ Python 3.8+ ಬೇಕು, ಮತ್ತು ಅದೇ ಯಂತ್ರದಲ್ಲಿ ಕನಿಷ್ಠ ಒಂದು ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್ ಬೇಕು. Docker ಸೂಚನೆಗಳು: [docs/DOCKER.md](docs/DOCKER.md).

## ಡಾಕ್ಸ್

| | |
|---|---|
| [ರನ್‌ಟೈಮ್ ಹೊಂದಾಣಿಕೆ](docs/compatibility.md) | ಪ್ರತಿ ಅಡಾಪ್ಟರ್ ಏನನ್ನು ಓದುತ್ತದೆ, ಮತ್ತು ರನ್‌ಟೈಮ್ ಸೇರಿಸುವುದು ಹೇಗೆ |
| [ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್](docs/CONTEXT_BLOWOUT.md) | ಪ್ರತಿ-ಪ್ರೊವೈಡರ್ ವಿಂಡೋಗಳು, ಕಂಪ್ಯಾಕ್ಷನ್ vs ಓವರ್‌ಫ್ಲೋ, ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ಕವರೇಜ್ |
| [ಓವರ್‌ಹೆಡ್](docs/OVERHEAD.md) | ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ನ ವೆಚ್ಚ, ಅಳೆಯಲಾಗಿದೆ, ಅದನ್ನು ಪುನರುತ್ಪಾದಿಸುವ ಹಾರ್ನೆಸ್ ಸಮೇತ |
| [ಎಂಟೈಟಲ್‌ಮೆಂಟ್‌ಗಳು](docs/ENTITLEMENTS.md) | ಉಚಿತ vs ಪಾವತಿಸಿದ, ಟಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, ಲೈಸೆನ್ಸ್ CLI |
| [ಅನುಮೋದನೆಗಳು ಮತ್ತು ನೀತಿಗಳು](docs/APPROVALS.md) | ಪೂರ್ವ-ಕಾರ್ಯಗತಗೊಳಿಸುವ ಗೇಟಿಂಗ್, ಅಪಾಯದ ಸ್ಕೋರಿಂಗ್, ಫೋನ್ ಅನುಮೋದನೆಗಳು |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಲ್ಲಿಗಾದರೂ ಎಕ್ಸ್‌ಪೋರ್ಟ್ ಮಾಡಿ, ಯಾವುದರಿಂದಲಾದರೂ OTLP ಇಂಜೆಸ್ಟ್ ಮಾಡಿ |
| [SDK ಟ್ರ್ಯಾಕಿಂಗ್](docs/SDK_TRACKING.md) | ನೀವೇ ನಿರ್ಮಿಸಿದ ಏಜೆಂಟ್‌ಗಳಿಗೆ ವೆಚ್ಚ ಗುಣಾರೋಪಣೆ |
| [ಚಾಟ್ ಚಾನೆಲ್‌ಗಳು](docs/CHANNELS.md) | ಫ್ಲೋನಲ್ಲಿ ತೋರಿಸಿದ ಚಾಟ್ ಅಡಾಪ್ಟರ್‌ಗಳು |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಡಿದ NVIDIA NemoClaw ಸೆಟಪ್‌ಗಳು |
| [Docker](docs/DOCKER.md) | ಇಮೇಜ್, ಕಂಪೋಸ್, ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು |
| [ಆರ್ಕಿಟೆಕ್ಚರ್](ARCHITECTURE.md) · [ಡೆವಲಪ್‌ಮೆಂಟ್](docs/DEVELOPMENT.md) | ಒಳಗೆ ಇದು ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ; ಮೂಲದಿಂದ ಚಲಾಯಿಸುವುದು |
| [ಟೆಲಿಮೆಟ್ರಿ](docs/TELEMETRY.md) | ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಮತ್ತು ಡೆಸ್ಕ್‌ಟಾಪ್-ಓಪನ್ ಪಿಂಗ್‌ಗಳು, ಮತ್ತು ಅವುಗಳನ್ನು ಆಫ್ ಮಾಡುವುದು ಹೇಗೆ |

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

ಕೆಳಗಿನ ಪ್ರತಿಯೊಂದು ಸಂಖ್ಯೆಯೂ ಒಂದು ನಿಜವಾದ ಯಂತ್ರದಿಂದ, ಓದಲು-ಮಾತ್ರ, ಏನನ್ನೂ ಬಿತ್ತದೆ.

**ಏನಾದರೂ ತಪ್ಪಾದಾಗ ಅದು ನಿಮಗೆ ತಿಳಿಸುತ್ತದೆ, ಕೇವಲ ಏನಾಯಿತು ಎಂಬುದನ್ನಲ್ಲ.**
ಮೇಲ್ಭಾಗದಲ್ಲಿ ಎರಡು ಅಸಂಗತತೆ ಬ್ಯಾನರ್‌ಗಳು: ದೈನಂದಿನ ಸರಾಸರಿಗಿಂತ 7 ಪಟ್ಟು ಹೆಚ್ಚು ಖರ್ಚು, ಮತ್ತು 4.2x ವೆಚ್ಚ ಉಲ್ಬಣ. ಅವುಗಳ ಕೆಳಗೆ, ಇತ್ತೀಚಿನ 667 ಸೆಷನ್‌ಗಳಲ್ಲಿ 324 ಪೋಲಿ ಸಂಕೇತವನ್ನು ಹೊತ್ತೊಯ್ಯುತ್ತಿವೆ, ಕಾರಣದ ಮೂಲಕ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ಪ್ರತಿ ವಿಂಡೋನಲ್ಲಿ ಹಣ ಎಲ್ಲಿಗೆ ಹೋಯಿತು ಎಂಬುದನ್ನು ಇದು ತೋರಿಸುತ್ತದೆ.**
ಇಂದು $252.47, ಈ ವಾರ $513.15, ಈ ತಿಂಗಳು $1,312.92, ಪ್ರತಿಯೊಂದರ ಹಿಂದಿನ ಟೋಕನ್‌ಗಳು ಮತ್ತು ನಿಮ್ಮ ಚಂದಾದಾರಿಕೆ ಈಗಾಗಲೇ ಎಷ್ಟನ್ನು ಒಳಗೊಂಡಿದೆ ಎಂಬುದರ ಸಮೇತ. ಅದರ ಕೆಳಗೆ, ಸುಮಾರು $1,128/ತಿಂಗಳು ಮರುಪಡೆಯಬಹುದಾದದ್ದು ಎಂದು ಮತ್ತು ಕ್ಯಾಶ್ ಮರುಬಳಕೆಯಿಂದ ಈಗಾಗಲೇ $17,256/ತಿಂಗಳು ಉಳಿಸಲಾಗಿದೆ ಎಂದು ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ಸಂದೇಶ ಒಂದು ಉತ್ತರವಾಗಿ ಹೇಗೆ ಬದಲಾಗುತ್ತದೆ ಎಂಬುದನ್ನು ಇದು ಚಿತ್ರಿಸುತ್ತದೆ.**
ಲೈವ್ ಫ್ಲೋ ಡಯಾಗ್ರಾಂ: ನೀವು, ಅದು ಆಗಮಿಸಿದ ಚಾನೆಲ್, ಗೇಟ್‌ವೇ, ಈಗ ಉತ್ತರಿಸುತ್ತಿರುವ ಮಾಡೆಲ್, ಮತ್ತು ಅದು ತಲುಪಿದ ಪ್ರತಿ ಟೂಲ್. ಕೆಲಸ ಅವುಗಳ ಮೂಲಕ ಚಲಿಸುತ್ತಿದ್ದಂತೆ ನೋಡ್‌ಗಳು ಬೆಳಗುತ್ತವೆ.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ಯಂತ್ರದಲ್ಲಿನ ಪ್ರತಿ ಏಜೆಂಟ್, ಒಂದೇ ಟೇಬಲ್‌ನಲ್ಲಿ.**
ಅದು ಏನನ್ನು ಚಲಾಯಿಸುತ್ತದೆ, ಕಳೆದ 24 ಗಂಟೆಗಳಲ್ಲಿ ಮತ್ತು ಜೀವಿತಾವಧಿಯಲ್ಲಿ ಅದರ ವೆಚ್ಚ ಏನು, ಅದನ್ನು ಕೊನೆಯದಾಗಿ ಯಾವಾಗ ನೋಡಲಾಯಿತು, ಅದನ್ನು ಯಾರು ಹೊಂದಿದ್ದಾರೆ, ಮತ್ತು ಚಂದಾದಾರಿಕೆ ಬಿಲ್ ಅನ್ನು ಒಳಗೊಂಡಿದೆಯೇ. ಇಲ್ಲಿ 14 ಏಜೆಂಟ್‌ಗಳು, 3 ಸೆಷನ್‌ಗಳು ಕೆಲಸ ಮಾಡುತ್ತಿವೆ, 13 ಸ್ತಬ್ಧವಾಗಿವೆ.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ಒಂದು ಟರ್ನ್‌ನ ಸಮಯ ಮತ್ತು ಹಣ ಎಲ್ಲಿಗೆ ಹೋಯಿತು ಎಂಬುದನ್ನು, ಟೂಲ್ ಮೂಲಕ ಟೂಲ್, ಇದು ತೋರಿಸುತ್ತದೆ.**
ನಿಜವಾದ ಸೆಷನ್‌ನ ಒಂದು ಟರ್ನ್: $1.16 ಗೆ 11.2 ನಿಮಿಷಗಳಲ್ಲಿ 11 ಟೂಲ್‌ಗಳು. ಪ್ರತಿ Bash ಕರೆ ಮತ್ತು ಮಾಡೆಲ್ ಕರೆ ಟೈಮ್‌ಲೈನ್‌ನಲ್ಲಿ ತನ್ನದೇ ಆದ ಬಾರ್ ಪಡೆಯುತ್ತದೆ, ಆದ್ದರಿಂದ 4.1 ನಿಮಿಷಗಳ ಕಾಲ ಚಲಿಸಿದ ಆದೇಶ ಮತ್ತು 226ms ಚಲಿಸಿದ ಆದೇಶವನ್ನು ಒಂದೇ ನೋಟದಲ್ಲಿ ಪ್ರತ್ಯೇಕಿಸಬಹುದು.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ಇದು ಕೆಲಸವನ್ನು ದರ್ಜೆ ಮಾಡುತ್ತದೆ, ಕೇವಲ ಖರ್ಚನ್ನಲ್ಲ.**
ಈ ವಾರ ಒಂದು A: 54 ಕೆಲಸಗಳು ಸ್ವಚ್ಛವಾಗಿ ಮರಳಿ ಬಂದವು, 2 ಒರಟಾದವು $48.57 ವೆಚ್ಚವಾಯಿತು, ಮತ್ತು ನಿರ್ಣಯಿಸಲು ತೀರಾ ಕಡಿಮೆ ಚಟುವಟಿಕೆ ಹೊಂದಿರುವ ರನ್‌ಗಳನ್ನು ಗೆಲುವುಗಳಂತೆ ಎಣಿಸುವ ಬದಲು ದರ್ಜೆಯಿಂದ ಹೊರಗಿಡಲಾಗಿದೆ. ಪ್ರತಿ ಒರಟಾದ ರನ್ ತನ್ನ ಟ್ರೇಸ್‌ಗೆ ಲಿಂಕ್ ಮಾಡುತ್ತದೆ.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ಕಾಂಟೆಕ್ಸ್ಟ್ ವಿಂಡೋ ಏಕೆ ತುಂಬುತ್ತಲೇ ಇರುತ್ತದೆ ಎಂಬುದನ್ನು ಇದು ತೋರಿಸುತ್ತದೆ.**
ಇತ್ತೀಚಿನ ಟರ್ನ್‌ನಲ್ಲಿ 1M-ಟೋಕನ್ ವಿಂಡೋದ 715K, 83.3% ಶಿಖರ, ಎಲ್ಲಾ ಓವರ್‌ಫ್ಲೋನಲ್ಲಿ ಬದಲಾಗಿ ಪ್ರೊಆಕ್ಟಿವ್ ಆಗಿ ಫೈರ್ ಆದ 4 ಕಂಪ್ಯಾಕ್ಷನ್‌ಗಳು, ಜೊತೆಗೆ ಅದರ ಹಿಂದಿನ ಪ್ರತಿ ಟರ್ನ್‌ನ ಬಳಕೆ.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ನೀವು ಏನನ್ನೂ ಕಾನ್ಫಿಗರ್ ಮಾಡದೆಯೇ ಪತ್ತೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ.**
ಇನ್‌ಸ್ಟಾಲ್‌ನಿಂದಲೇ ಬಿಲ್ಟ್-ಇನ್ ಡಿಟೆಕ್ಟರ್‌ಗಳು ಆನ್ ಆಗಿವೆ: ಏಜೆಂಟ್ ಸ್ತಬ್ಧವಾಯಿತು, ಟೆಲಿಮೆಟ್ರಿ ಫೀಡ್ ನಿಂತಿತು, ವೆಚ್ಚ ಉಲ್ಬಣ, ಟೋಕನ್ ಸ್ಫೋಟ, ದೋಷಗಳು ಏರುತ್ತಿವೆ, ದೋಷ ಉಲ್ಬಣ, ಬಜೆಟ್ ಮಿತಿ, ಬೆದರಿಕೆ ಸಿಗ್ನೇಚರ್ ಹೊಂದಾಣಿಕೆಯಾಯಿತು, ಭದ್ರತಾ ಟೂಲ್ ಶೋಧ, ಭದ್ರತಾ ಸ್ಥಿತಿ ಬದಲಾಯಿತು. ಅದರ ಮೇಲೆ ನಿಮ್ಮದೇ ನಿಯಮಗಳು ಐಚ್ಛಿಕ.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ಅಪಾಯಕಾರಿ ಕರೆಯನ್ನು ಹಿಡಿದಿಡುವುದು ಆಪ್ಟ್-ಇನ್, ಮತ್ತು ಆಫ್ ಆಗಿ ಸಾಗಿಸಲಾಗುತ್ತದೆ.**
ಪುನರಾವರ್ತಿತ ಡಿಲೀಟ್‌ಗಳು, ಫೋರ್ಸ್ ಪುಶ್‌ಗಳು, sudo, ಸೀಕ್ರೆಟ್‌ಗಳು, ಪ್ಯಾಕೇಜ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು ಮತ್ತು ಔಟ್‌ಬೌಂಡ್ ಕರೆಗಳು ಪ್ರತಿಯೊಂದೂ ನೀವು ಆನ್ ಮಾಡಬಹುದಾದ ನಿಯಮವನ್ನು ಹೊಂದಿವೆ. ನೀವು ಮಾಡುವವರೆಗೆ, ClawMetry ಗಮನಿಸುತ್ತದೆ ಮತ್ತು ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ. ಒಂದನ್ನು ಆನ್ ಮಾಡಿದ ನಂತರ, ಹೊಂದಾಣಿಕೆಯಾಗುವ ಕರೆಗಳು ಒಪ್ಪಿಗೆ ಅಥವಾ ನಿರಾಕರಣೆಗಾಗಿ ಇಲ್ಲಿ (ಅಥವಾ ನಿಮ್ಮ ಫೋನ್‌ನಲ್ಲಿ) ಕಾಯುತ್ತವೆ.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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
