<!-- i18n-src:88be2deff5d5 -->
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

**ನಿಮ್ಮ ಏಜೆಂಟ್ ಯೋಚಿಸುವುದನ್ನು ನೋಡಿ.** **30 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳಿಗೆ** ರಿಯಲ್-ಟೈಮ್ ಅಬ್ಸರ್ವೆಬಿಲಿಟಿ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & ಇನ್ನೂ 26. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.

> 🌐 **ಇದನ್ನು ಈ ಭಾಷೆಗಳಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದೇ ಆದೇಶ. ಶೂನ್ಯ ಕಾನ್ಫಿಗರೇಶನ್. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆಹಚ್ಚುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆಯುತ್ತದೆ. ಶೂನ್ಯ ಕಾನ್ಫಿಗರೇಶನ್: ಇದು ನಿಮ್ಮಲ್ಲಿ ಈಗಾಗಲೇ ಇರುವ ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಪತ್ತೆಹಚ್ಚುತ್ತದೆ, ಅವುಗಳನ್ನು ಓದಲು-ಮಾತ್ರ ಓದುತ್ತದೆ, ಮತ್ತು ಅವು ಹೇಗೆ ಚಲಿಸುತ್ತವೆ ಎಂಬುದರ ಬಗ್ಗೆ ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

**ಓಪನ್ ಸೋರ್ಸ್ ಆ್ಯಪ್‌ನಲ್ಲಿ ಉಚಿತ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ಪಾವತಿಸಿದ ಯೋಜನೆಯಲ್ಲಿ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ಪ್ರತಿಯೊಂದು ರನ್‌ಟೈಮ್‌ಗೂ ಅದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಸಿಗುತ್ತದೆ. ಒಂದೇ ಬಾರಿಗೆ ಹಲವನ್ನು ಚಲಾಯಿಸಿ, ಮತ್ತು ಹೆಡರ್ ಸ್ವಿಚರ್ ಪ್ರತಿ ಟ್ಯಾಬ್‌ನ ವ್ಯಾಪ್ತಿಯನ್ನು ಅವುಗಳಲ್ಲಿ ಒಂದಕ್ಕೆ ಮರುಹೊಂದಿಸುತ್ತದೆ.

SDKಯಲ್ಲಿ ನಿಮ್ಮದೇ ಆದ ಏಜೆಂಟ್ ಅನ್ನು ನಿರ್ಮಿಸಿದ್ದೀರಾ? ಇಂಟರ್‌ಸೆಪ್ಟರ್ ಅದರ LLM ಕರೆಗಳನ್ನೂ ಟ್ರ್ಯಾಕ್ ಮಾಡುತ್ತದೆ. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ನೋಡಿ.

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **ಸೆಷನ್‌ಗಳು & ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು**: ಪ್ರತಿ ಏಜೆಂಟ್ ಏನು ಮಾಡಿತು, ಟರ್ನ್ ಟರ್ನ್ ಆಗಿ, ರೀಪ್ಲೇ ಸಹಿತ
- **ವೆಚ್ಚ & ಟೋಕನ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್, ಮಾಡೆಲ್, ಸೆಷನ್ ಮತ್ತು ದಿನಕ್ಕೆ, ಅಸಂಗತತೆ ಫ್ಲ್ಯಾಗ್‌ಗಳೊಂದಿಗೆ
- **ಫ್ಲೋ**: ಚಾನಲ್‌ಗಳು, ಮಾಡೆಲ್‌ಗಳು ಮತ್ತು ಟೂಲ್‌ಗಳ ಮೂಲಕ ಚಲಿಸುವ ಸಂದೇಶಗಳ ಲೈವ್ ಡಯಾಗ್ರಾಂ
- **ಬ್ರೈನ್**: ಘಟಿಸುತ್ತಿರುವಂತೆಯೇ ರೀಸನಿಂಗ್ ಮತ್ತು ಟೂಲ್-ಕಾಲ್ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್
- **ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್**: ಪ್ರತಿ ಪ್ರೊವೈಡರ್‌ಗೆ ಗಾತ್ರ ನಿಗದಿಪಡಿಸಿದ ವಿಂಡೋ ಬಳಕೆ, ಕಂಪ್ಯಾಕ್ಷನ್ ವರ್ಸಸ್ ಬಲವಂತದ ಓವರ್‌ಫ್ಲೋ, ಜೊತೆಗೆ ನಮಗೆ *ಕಾಣಿಸದಿರುವುದರ* ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ನಕ್ಷೆ ([ಹೇಗೆ](docs/CONTEXT_BLOWOUT.md))
- **ಮೆಮೊರಿ & ಸ್ಕಿಲ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್ ನಿಜವಾಗಿ ಲೋಡ್ ಮಾಡಿದ ಫೈಲ್‌ಗಳು ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು
- **ಆರೋಗ್ಯ & ಲಾಗ್‌ಗಳು**: ಡಿಸ್ಕ್, ಮೆಮೊರಿ, ದೋಷ ದರಗಳು, ದರ ಮಿತಿಗಳು, ಲೈವ್ ಲಾಗ್ ಸ್ಟ್ರೀಮ್
- **ಅಲರ್ಟ್‌ಗಳು**: ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ ಸ್ಪೈಕ್‌ಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್, Slack, Discord, PagerDuty, Telegram, Email ಗೆ ರೂಟ್ ಮಾಡಲಾಗಿದೆ
- **ಅನುಮೋದನೆಗಳು**: ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅವು ಓಡುವ *ಮೊದಲೇ* ವಿರಾಮಗೊಳಿಸಿ ಮತ್ತು ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಅನುಮೋದಿಸಿ ([ಹೇಗೆ](docs/APPROVALS.md))

## ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್, ಮತ್ತು ವೀಕ್ಷಣೆಗೆ ಎಷ್ಟು ವೆಚ್ಚವಾಗುತ್ತದೆ

ಯಾವುದೇ ಏಜೆಂಟ್-ಹೋಲಿಕೆ ಸಾಧನವನ್ನು ನಂಬುವ ಮೊದಲು ಉತ್ತರಿಸಬೇಕಾದ ಎರಡು ಪ್ರಶ್ನೆಗಳು.

**ರನ್‌ಟೈಮ್‌ಗಳಾದ್ಯಂತ ಕಾಂಟೆಕ್ಸ್ಟ್-ವಿಂಡೋ ಬ್ಲೋಔಟ್ ಅನ್ನು ಅದು ಹೇಗೆ ನಿಭಾಯಿಸುತ್ತದೆ?**

ಬಳಕೆಯ ಶೇಕಡಾವಾರು ಪ್ರಮಾಣ ಅದು ಯಾವುದನ್ನು ಭಾಗಿಸುತ್ತದೆ ಎಂಬಷ್ಟೇ ಪ್ರಾಮಾಣಿಕವಾಗಿರುತ್ತದೆ. ClawMetry ನೀವು ಓದಬಹುದಾದ ಮತ್ತು PR ಮಾಡಬಹುದಾದ [ಒಂದು ಟೇಬಲ್‌ನಿಂದ](clawmetry/context_windows.py) ಪ್ರತಿ ಪ್ರೊವೈಡರ್‌ಗೆ ವಿಂಡೋ ಗಾತ್ರವನ್ನು ನಿಗದಿಪಡಿಸುತ್ತದೆ, ಇದು Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama ಮತ್ತು GLM ಅನ್ನು ಒಳಗೊಂಡಿದೆ. ಇದು ಒಂದೇ ವೆಂಡರ್‌ನ ಅಳತೆಗೋಲಿನಿಂದ 30 ರನ್‌ಟೈಮ್‌ಗಳನ್ನೂ ಅಳೆಯುವುದಿಲ್ಲ. ಇದು ಮುಖ್ಯ: 300K GPT-5 ಟರ್ನ್ ಅನ್ನು Anthropic ನ 200K ವಿರುದ್ಧ ಸ್ಕೋರ್ ಮಾಡಿದಾಗ ">100%, ಬ್ಲೋನ್" ಎಂದು ಓದುತ್ತದೆ, ಆದರೆ ವಾಸ್ತವದಲ್ಲಿ ಅದು GPT-5 ನ 400K ಯ 75% ರಷ್ಟಿದೆ. ಅದೇ ಅಳತೆಗೋಲು ನಿಜವಾಗಿ ಓವರ್‌ಫ್ಲೋ ಆದ 130K DeepSeek ಟರ್ನ್ ಅನ್ನು ಆರಾಮದಾಯಕ 65% ಎಂದು ಮರೆಮಾಚುತ್ತದೆ.

ಪ್ರತಿ ವಿಂಡೋ ತನ್ನ ಮೂಲವನ್ನು ಜೊತೆಗೆ ಕಳುಹಿಸುತ್ತದೆ: `model_table`, `explicit_marker`, `observed_floor`, ಅಥವಾ ಮಾಡೆಲ್ ಗೊತ್ತಿಲ್ಲದಿದ್ದಾಗ ಪ್ರಾಮಾಣಿಕ `default`. ಊಹೆಯ ಮೇಲೆ ನಿರ್ಮಿಸಿದ ಗೇಜ್ ಎಂದಿಗೂ ಒಂದು ಲುಕಪ್‌ನ ಮೇಲೆ ನಿರ್ಮಿಸಿದ ಗೇಜ್‌ನಷ್ಟೇ ಅಧಿಕಾರದೊಂದಿಗೆ ರೆಂಡರ್ ಆಗುವುದಿಲ್ಲ.

ClawMetry ಕೆಲವು ರನ್‌ಟೈಮ್‌ಗಳಲ್ಲಿ ಮಾತ್ರ ಕಂಪ್ಯಾಕ್ಷನ್ ಈವೆಂಟ್‌ಗಳನ್ನು ನೋಡಬಲ್ಲದು. ಆದ್ದರಿಂದ `GET /api/context-coverage` ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ, ಶೂನ್ಯ ಎಂಬುದು **"ಸ್ವಚ್ಛವಾಗಿ ಓಡಿತು" ಎಂದೋ ಅಥವಾ "ನಮಗೆ ಕುರುಡಾಗಿದ್ದೇವೆ" ಎಂದೋ** ವರದಿ ಮಾಡುತ್ತದೆ. ನಿಜವಾಗಿಯೂ ಕುರುಡು ಎಂದರ್ಥವಿರುವ `0` ಹಾಗೆಂದೇ ಹೇಳುತ್ತದೆ. [ಪೂರ್ಣ ವಿವರ](docs/CONTEXT_BLOWOUT.md)

**ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ಗೆ ಎಷ್ಟು ವೆಚ್ಚವಾಗುತ್ತದೆ?**

| ಪಥ | ನಿಮ್ಮ ಏಜೆಂಟ್‌ಗೆ ಸೇರಿಸಲಾಗಿದೆ | ಡೀಫಾಲ್ಟ್? |
|---|---|---|
| ಸೆಷನ್-ಫೈಲ್ ಟೈಲಿಂಗ್ (ಎಲ್ಲಾ 30 ರನ್‌ಟೈಮ್‌ಗಳು) | **0**. ಪ್ರತ್ಯೇಕ ಪ್ರಕ್ರಿಯೆ, ನಿಮ್ಮ ಏಜೆಂಟ್‌ನಲ್ಲಿ ClawMetry ಕೋಡ್ ಇಲ್ಲ | ಆನ್ |
| HTTP ಇಂಟರ್‌ಸೆಪ್ಟರ್ (`CLAWMETRY_INTERCEPT=1`) | ಪ್ರತಿ LLM ಕರೆಗೆ **+0.44 ms**, ಅಥವಾ 5s ಕರೆಯ 0.009% | ಆಫ್ |
| ಪ್ರೀ-ಟೂಲ್ ಹುಕ್ ಗೇಟ್ (ವಾರ್ಮ್ ಕ್ಯಾಶ್) | 36 ms ಇಂಟರ್‌ಪ್ರೀಟರ್ ಫ್ಲೋರ್‌ಗಿಂತ ಹೆಚ್ಚಾಗಿ, ಪ್ರತಿ ಗೇಟೆಡ್ ಟೂಲ್ ಕರೆಗೆ **+44 ms** | ಆಫ್ |
| ಎನ್‌ಫೋರ್ಸ್‌ಮೆಂಟ್ ಪ್ರಾಕ್ಸಿ | ಪ್ರತಿ LLM ಕರೆಗೆ **+9.7 ms** | ಆಫ್ |

ಡೀಮನ್ ಹೋಸ್ಟ್ ವೆಚ್ಚ: **2,762 ಈವೆಂಟ್‌ಗಳು/ಸೆಕೆಂಡ್** ಇಂಜೆಸ್ಟ್, ಡಿಸ್ಕ್‌ನಲ್ಲಿ **710 ಬೈಟ್‌ಗಳು/ಈವೆಂಟ್** (100k ಈವೆಂಟ್‌ಗಳಿಗೆ 67.7 MB), ಮತ್ತು ಬ್ಯುಸಿ ಇನ್‌ಸ್ಟಾಲ್‌ನಲ್ಲಿ ನಿರಂತರವಾಗಿ **ಒಂದು ಕೋರ್‌ನ ~12%**. ಆ ಕೊನೆಯ ಸಂಖ್ಯೆ ನಮ್ಮದೇ ಘೋಷಿತ 5-10% ಬಜೆಟ್‌ಗಿಂತ ಹೆಚ್ಚಾಗಿದೆ, ಆದ್ದರಿಂದ ಇದನ್ನು ಪುಟದಿಂದ ತೆಗೆದುಹಾಕುವ ಬದಲು ಬೆನ್ನಟ್ಟಬೇಕಾದ ಬಗ್ ಆಗಿ ಪ್ರಕಟಿಸಲಾಗಿದೆ.

`benchmarks/overhead.py` ಬಳಸಿ Apple M2 Pro ನಲ್ಲಿ ಅಳೆಯಲಾಗಿದೆ. ಈ ಹಾರ್ನೆಸ್ ಪ್ರತಿ ಸ್ಥಿತಿಯನ್ನು ಪ್ರತ್ಯೇಕ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿ ಚಲಾಯಿಸುತ್ತದೆ, ಅವುಗಳ ಕ್ರಮವನ್ನು ಪರ್ಯಾಯಗೊಳಿಸುತ್ತದೆ, ಮತ್ತು **ಸುತ್ತುಗಳು ಅದರ ಚಿಹ್ನೆಯ ಬಗ್ಗೆ ಒಪ್ಪದಿದ್ದಾಗ ಸಂಖ್ಯೆಯನ್ನು ಮುದ್ರಿಸಲು ನಿರಾಕರಿಸುತ್ತದೆ**. ಇದನ್ನು ನಿಮ್ಮದೇ ಯಂತ್ರದಲ್ಲಿ ಒಂದು ನಿಮಿಷದಲ್ಲಿ ಚಲಾಯಿಸಿ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ಹುಕ್ ಗೇಟ್‌ಗಳು ಮತ್ತು ಎನ್‌ಫೋರ್ಸ್‌ಮೆಂಟ್ ಪ್ರಾಕ್ಸಿ ಸೇರಿದಂತೆ ಪ್ರತಿ ಪಥವನ್ನೂ ಅಳೆಯಲಾಗಿದೆ, ಮತ್ತು ಹಾರ್ನೆಸ್ CI ಯಲ್ಲಿ Linux, macOS ಮತ್ತು Windows ನಲ್ಲಿ ಚಲಿಸುತ್ತದೆ. ತಿಳಿದುಕೊಳ್ಳಬೇಕಾದ ಎರಡು ಫಲಿತಾಂಶಗಳು: Linux ಗಿಂತ Windows ನಲ್ಲಿ ಪ್ರಾಕ್ಸಿಗೆ ಸುಮಾರು ಏಳು ಪಟ್ಟು ಹೆಚ್ಚು ವೆಚ್ಚವಾಗುತ್ತದೆ, ಮತ್ತು ಡೀಮನ್ ಪ್ರಸ್ತುತ ನಮ್ಮದೇ 5-10% ಬಜೆಟ್‌ಗಿಂತ ಹೆಚ್ಚಾಗಿ ಒಂದು ಕೋರ್‌ನ ಸುಮಾರು 12% ಅನ್ನು ನಿರಂತರವಾಗಿ ಬಳಸುತ್ತದೆ. ರಾ JSON, ವಿಧಾನ, ಮತ್ತು ಇನ್ನೂ ಅಳೆಯದಿರುವುದು [docs/OVERHEAD.md](docs/OVERHEAD.md) ನಲ್ಲಿವೆ.

## ಬೆಲೆ ನಿಗದಿ

| ಯೋಜನೆ | ಇದು ಏನನ್ನು ಒಳಗೊಳ್ಳುತ್ತದೆ | ಬೆಲೆ |
|---|---|---|
| **ಉಚಿತ** | OpenClaw + NVIDIA NemoClaw + Goose, ಪೂರ್ಣ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್, ಸ್ಥಳೀಯ ಮಾತ್ರ | $0 |
| **ಸ್ಟಾರ್ಟರ್** | ಮೇಲಿನ ಪ್ರತಿ ಇತರ ರನ್‌ಟೈಮ್, ಫ್ಲೀಟ್ ವೀಕ್ಷಣೆ, ಕ್ಲೌಡ್ ಸಿಂಕ್ | ಪ್ರತಿ ನೋಡ್‌ಗೆ $9 / ತಿಂಗಳು |
| **Pro** | ಸ್ಟಾರ್ಟರ್ + ನಿಯಂತ್ರಣ ಮತ್ತು ಮೌಲ್ಯಮಾಪನ: ಅನುಮೋದನೆಗಳು, ಟೂಲ್-ರಿಸ್ಕ್ ನೀತಿಗಳು, ಎವಾಲ್‌ಗಳು, ಅಸಂಗತತೆ ಪತ್ತೆ, ವೆಚ್ಚ ಆಪ್ಟಿಮೈಸರ್, OTel ಎಕ್ಸ್‌ಪೋರ್ಟ್, ಟ್ಯಾಂಪರ್-ಎವಿಡೆಂಟ್ ಆಡಿಟ್ ಲಾಗ್ | ಪ್ರತಿ ನೋಡ್‌ಗೆ $19 / ತಿಂಗಳು |

ವಾರ್ಷಿಕ ಯೋಜನೆಗಳು, ಎಂಟರ್‌ಪ್ರೈಸ್ ಮತ್ತು ಪ್ರಸ್ತುತ ಸಂಖ್ಯೆಗಳು **[clawmetry.com/pricing](https://clawmetry.com/pricing)** ನಲ್ಲಿ ಇವೆ. ಸ್ವಯಂ-ಹೋಸ್ಟೆಡ್ ಲೈಸೆನ್ಸ್ ಕೀಗಳು ಕ್ಲೌಡ್ ಇಲ್ಲದೆಯೇ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತವೆ (`clawmetry license`). ನಿಖರವಾದ ಉಚಿತ/ಪಾವತಿ ವಿಭಜನೆ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ನಲ್ಲಿದೆ.

## ನಿಮ್ಮ ಡೇಟಾ ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲಿಯೇ ಇರುತ್ತದೆ

ClawMetry ಸ್ಥಳೀಯ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಮತ್ತು ಲಾಗ್‌ಗಳನ್ನು ಓದುತ್ತದೆ. **ನೀವು `clawmetry connect` ಚಲಾಯಿಸದ ಹೊರತು ಯಾವುದೇ ಸೆಷನ್ ಡೇಟಾ ನಿಮ್ಮ ಪೆಟ್ಟಿಗೆಯಿಂದ ಹೊರಹೋಗುವುದಿಲ್ಲ** — ಯಾವುದೇ ಪ್ರಾಂಪ್ಟ್‌ಗಳು, ಪ್ರತ್ಯುತ್ತರಗಳು, ಟೂಲ್ ಆರ್ಗ್ಯುಮೆಂಟ್‌ಗಳು, ಫೈಲ್ ಕಂಟೆಂಟ್ ಅಥವಾ ಲಾಗ್ ಲೈನ್‌ಗಳಿಲ್ಲ. ನೀವು ಕನೆಕ್ಟ್ ಮಾಡಿದಾಗ, ಸ್ನ್ಯಾಪ್‌ಶಾಟ್ ಅನ್ನು ನಿಮ್ಮ ಯಂತ್ರವನ್ನು ಎಂದಿಗೂ ಬಿಡದ ಕೀಯೊಂದಿಗೆ ಎಂಡ್-ಟು-ಎಂಡ್ ಎನ್‌ಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗುತ್ತದೆ, ಮತ್ತು ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಡಿಕ್ರಿಪ್ಟ್ ಮಾಡಲಾಗುತ್ತದೆ. ಒಂದು ನೋಡ್‌ಗೆ ಕೀ ಇಲ್ಲದಿದ್ದರೆ, ಅಪ್‌ಲೋಡ್ ಅನ್ನು ಸ್ಪಷ್ಟ ರೂಪದಲ್ಲಿ ಕಳುಹಿಸುವ ಬದಲು ಸ್ಕಿಪ್ ಮಾಡಲಾಗುತ್ತದೆ, ಮತ್ತು ಯಾವುದೇ ಸರ್ವರ್ ಪ್ರತಿಕ್ರಿಯೆಯು ಅದನ್ನು ಆಫ್ ಮಾಡಲಾರದು.

ನೀವು ಕನೆಕ್ಟ್ ಮಾಡುವ ಮೊದಲು ಎರಡು ವಿಷಯಗಳು ಡೀಫಾಲ್ಟ್ ಆಗಿ ಚಲಿಸುತ್ತವೆ, ಎರಡೂ ಆಪ್ಟ್-ಔಟ್ ಮಾಡಬಹುದಾದವು ಮತ್ತು ಯಾವುದೂ ಸೆಷನ್ ಡೇಟಾ ಹೊತ್ತಿಲ್ಲ: ಒಂದು ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಪಿಂಗ್ ಮತ್ತು PyPI ವಿರುದ್ಧ ಆವೃತ್ತಿ ಪರಿಶೀಲನೆ. ಡೀಫಾಲ್ಟ್ ಇನ್‌ಸ್ಟಾಲ್ ಸಹ ಆರಂಭದ ಬ್ಯಾನರ್ ಸಾಲಿಗಾಗಿ ನಿಮ್ಮ ಸಾರ್ವಜನಿಕ IP ಅನ್ನು ಒಮ್ಮೆ ನೋಡುತ್ತದೆ. ಪ್ರತಿ ಗಮ್ಯಸ್ಥಾನ, ಅದು ಏನನ್ನು ಹೊತ್ತೊಯ್ಯುತ್ತದೆ ಮತ್ತು ಅದನ್ನು ಹೇಗೆ ಆಫ್ ಮಾಡುವುದು ಎಂಬುದು [docs/EGRESS.md](docs/EGRESS.md) ನಲ್ಲಿ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ; ಸ್ವಯಂ-ಹೋಸ್ಟೆಡ್, ಮರುನಿರ್ದೇಶಿತ ಮತ್ತು ಏರ್-ಗ್ಯಾಪ್ಡ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು ಯಾವುದೇ ಐಚ್ಛಿಕ ಔಟ್‌ಬೌಂಡ್ ಕರೆಗಳನ್ನು ಮಾಡುವುದಿಲ್ಲ.

ಡಿಕ್ರಿಪ್ಷನ್ ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ, ನಾವು ನಿಮಗೆ ನೀಡುವ ಕೋಡ್‌ನಲ್ಲಿ ನಡೆಯುತ್ತದೆ. ಇದು ಹಿಂದೆ ಒಂದು ಭರವಸೆಯಾಗಿತ್ತು; ಈಗ ಅದು ನೀವು ಪರಿಶೀಲಿಸಬಹುದಾದ ವಿಷಯ. ನಿಮ್ಮ ಕೀಯನ್ನು ಸ್ಪರ್ಶಿಸುವ ಪ್ರತಿ ಸಾಲೂ ಒಂದೇ ಓದಬಹುದಾದ ಫೈಲ್‌ನಲ್ಲಿ ವಾಸಿಸುತ್ತದೆ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ಇದು wheel ಒಳಗೆ ಶಿಪ್ ಆಗುತ್ತದೆ ಮತ್ತು ಸಬ್‌ರಿಸೋರ್ಸ್ ಇಂಟೆಗ್ರಿಟಿ ಹ್ಯಾಶ್‌ನೊಂದಿಗೆ ಪಿನ್ ಮಾಡಿ ಯಥಾವತ್ತಾಗಿ ಸರ್ವ್ ಮಾಡಲಾಗುತ್ತದೆ. ಬ್ರೌಸರ್ ನಾವು ಪ್ರಕಟಿಸಿದ್ದನ್ನೇ ಚಲಾಯಿಸುತ್ತದೆ ಎಂದು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಲು:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ಅದು ಏನನ್ನು ಸಾಬೀತುಪಡಿಸುವುದಿಲ್ಲ: ಫೈಲ್ ಅನ್ನು ಲೋಡ್ ಮಾಡುವ ಪುಟವನ್ನೂ ನಾವೇ ಸರ್ವ್ ಮಾಡುತ್ತೇವೆ, ಆದ್ದರಿಂದ ನಾವು ಬೇರೊಂದು ಪುಟವನ್ನು ಸರ್ವ್ ಮಾಡಬಹುದು. ಇಂಟೆಗ್ರಿಟಿ ಹ್ಯಾಶ್‌ಗಳು ರಾಜಿಯಾದ CDN ನಿಂದ ನಿಮ್ಮನ್ನು ರಕ್ಷಿಸುತ್ತವೆ, ಆದರೆ ವೆಂಡರ್‌ನಿಂದ ಅಲ್ಲ. ನೀವು ಗಳಿಸುವುದೇನೆಂದರೆ, ಯಾವುದೇ ಪರ್ಯಾಯೀಕರಣ ಉದ್ದೇಶಪೂರ್ವಕವಾಗಿರಬೇಕು, ಪುಟ ಮೂಲದಲ್ಲಿ ಗೋಚರಿಸುತ್ತದೆ, ಮತ್ತು ಯಾರಾದರೂ ಪಡೆಯಬಹುದಾದ PyPI ಯಲ್ಲಿನ ಆರ್ಟಿಫ್ಯಾಕ್ಟ್‌ಗಿಂತ ಭಿನ್ನವಾಗಿರುತ್ತದೆ. ಸ್ವಯಂ-ಹೋಸ್ಟಿಂಗ್ ಅಥವಾ ಸ್ಥಳೀಯ-ಮಾತ್ರ ಇರುವುದು ಈ ಅವಲಂಬನೆಯನ್ನು ಸಂಪೂರ್ಣವಾಗಿ ತೆಗೆದುಹಾಕುತ್ತದೆ.

## ಇನ್‌ಸ್ಟಾಲ್

```bash
pip install clawmetry     # ನಂತರ: clawmetry
```

ಅಥವಾ ಒಂದೇ ಸಾಲಿನ ಆದೇಶ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ಅಥವಾ Windows ನಲ್ಲಿ Python 3.8+ ಬೇಕು, ಮತ್ತು ಅದೇ ಯಂತ್ರದಲ್ಲಿ ಕನಿಷ್ಠ ಒಂದು ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್ ಬೇಕು. Docker ಸೂಚನೆಗಳು: [docs/DOCKER.md](docs/DOCKER.md).

ಅಥವಾ ಏಜೆಂಟ್‌ಗೆ ಅದನ್ನು ನಿಮಗಾಗಿ ಸೆಟಪ್ ಮಾಡಲು ಬಿಡಿ. [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) ಸ್ಕಿಲ್ Claude Code, Codex, Cursor, Gemini CLI, Copilot ಅಥವಾ OpenCode ಗೆ ClawMetry ಅನ್ನು ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಲು, ಯಂತ್ರದ ಮೇಲಿನ ಏಜೆಂಟ್‌ಗಳು ಏನು ಮಾಡುತ್ತಿವೆ ಮತ್ತು ಎಷ್ಟು ಖರ್ಚು ಮಾಡುತ್ತಿವೆ ಎಂದು ವರದಿ ಮಾಡಲು, ಕೋರಿಕೆಯ ಮೇರೆಗೆ ಒಂದು ಸೆಷನ್ ಅನ್ನು ನಿಲ್ಲಿಸಲು, ಮತ್ತು ಅನುಮೋದನೆಗಾಗಿ ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಹಿಡಿದಿಡಲು ಕಲಿಸುತ್ತದೆ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ಡಾಕ್ಸ್

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ಪ್ರತಿ ಅಡಾಪ್ಟರ್ ಏನು ಓದುತ್ತದೆ, ಮತ್ತು ಒಂದು ರನ್‌ಟೈಮ್ ಅನ್ನು ಹೇಗೆ ಸೇರಿಸುವುದು |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | ಪ್ರತಿ-ಪ್ರೊವೈಡರ್ ವಿಂಡೋಗಳು, ಕಂಪ್ಯಾಕ್ಷನ್ ವರ್ಸಸ್ ಓವರ್‌ಫ್ಲೋ, ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ಕವರೇಜ್ |
| [Overhead](docs/OVERHEAD.md) | ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ಗೆ ಎಷ್ಟು ವೆಚ್ಚವಾಗುತ್ತದೆ, ಅಳೆದದ್ದು, ಅದನ್ನು ಮರುಉತ್ಪಾದಿಸುವ ಹಾರ್ನೆಸ್‌ನೊಂದಿಗೆ |
| [Entitlements](docs/ENTITLEMENTS.md) | ಉಚಿತ ವರ್ಸಸ್ ಪಾವತಿ, ಟಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, ಲೈಸೆನ್ಸ್ CLI |
| [Approvals & policies](docs/APPROVALS.md) | ಪೂರ್ವ-ಎಕ್ಸಿಕ್ಯೂಶನ್ ಗೇಟಿಂಗ್, ರಿಸ್ಕ್ ಸ್ಕೋರಿಂಗ್, ಫೋನ್ ಅನುಮೋದನೆಗಳು |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಲ್ಲಿಯಾದರೂ ಎಕ್ಸ್‌ಪೋರ್ಟ್ ಮಾಡಿ, ಯಾವುದರಿಂದಲಾದರೂ OTLP ಇಂಜೆಸ್ಟ್ ಮಾಡಿ |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ಅಂತ್ಯದಿಂದ ಅಂತ್ಯದವರೆಗೆ, ಚಲಾಯಿಸಬಹುದಾದ ಉದಾಹರಣೆಗಳೊಂದಿಗೆ |
| [SDK tracking](docs/SDK_TRACKING.md) | ನೀವೇ ನಿರ್ಮಿಸಿದ ಏಜೆಂಟ್‌ಗಳಿಗೆ ವೆಚ್ಚ ಆರೋಪಣೆ |
| [Chat channels](docs/CHANNELS.md) | ಫ್ಲೋನಲ್ಲಿ ತೋರಿಸಲಾದ ಚಾಟ್ ಅಡಾಪ್ಟರ್‌ಗಳು |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಡಿದ NVIDIA NemoClaw ಸೆಟಪ್‌ಗಳು |
| [Docker](docs/DOCKER.md) | ಇಮೇಜ್, ಕಂಪೋಸ್, ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | ಇದು ಒಳಗಿನಿಂದ ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ; ಮೂಲದಿಂದ ಚಲಾಯಿಸುವುದು |
| [Telemetry](docs/TELEMETRY.md) | ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಮತ್ತು ಡೆಸ್ಕ್‌ಟಾಪ್-ಓಪನ್ ಪಿಂಗ್‌ಗಳು, ಮತ್ತು ಅವುಗಳನ್ನು ಆಫ್ ಮಾಡುವುದು ಹೇಗೆ |

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

ಕೆಳಗಿನ ಪ್ರತಿ ಸಂಖ್ಯೆಯೂ ಒಂದು ನಿಜವಾದ ಯಂತ್ರದಿಂದ, ಓದಲು-ಮಾತ್ರ, ಏನನ್ನೂ ಬಿತ್ತದೆ.

**ಏನಾಯಿತು ಎಂಬುದನ್ನಷ್ಟೇ ಅಲ್ಲ, ಏನೋ ತಪ್ಪಾಗಿದೆ ಎಂದೂ ಅದು ನಿಮಗೆ ತಿಳಿಸುತ್ತದೆ.**
ಮೇಲ್ಭಾಗದಲ್ಲಿ ಎರಡು ಅಸಂಗತತೆ ಬ್ಯಾನರ್‌ಗಳು: ದೈನಂದಿನ ಸರಾಸರಿಯ 7 ಪಟ್ಟು ಖರ್ಚು ಓಡುತ್ತಿರುವುದು, ಮತ್ತು 4.2x ವೆಚ್ಚ ಸ್ಪೈಕ್. ಅವುಗಳ ಕೆಳಗೆ, ಇತ್ತೀಚಿನ 667 ಸೆಷನ್‌ಗಳಲ್ಲಿ 324 ವ್ಯರ್ಥ ಸಂಕೇತವನ್ನು ಹೊತ್ತಿವೆ, ಕಾರಣದ ಪ್ರಕಾರ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ಪ್ರತಿ ವಿಂಡೋದಲ್ಲಿ ಹಣ ಎಲ್ಲಿ ಹೋಯಿತು ಎಂದು ಅದು ತೋರಿಸುತ್ತದೆ.**
ಇಂದು $252.47, ಈ ವಾರ $513.15, ಈ ತಿಂಗಳು $1,312.92, ಪ್ರತಿಯೊಂದೂ ಅದರ ಹಿಂದಿನ ಟೋಕನ್‌ಗಳು ಮತ್ತು ನಿಮ್ಮ ಚಂದಾದಾರಿಕೆ ಈಗಾಗಲೇ ಎಷ್ಟನ್ನು ಒಳಗೊಂಡಿದೆ ಎಂಬುದರೊಂದಿಗೆ. ಅದರ ಕೆಳಗೆ, ಸುಮಾರು $1,128/ತಿಂಗಳು ಮರುಪಡೆಯಬಹುದಾದ ಎಂದು ಮತ್ತು ಕ್ಯಾಶ್ ಮರುಬಳಕೆಯಿಂದ ಈಗಾಗಲೇ $17,256/ತಿಂಗಳು ಉಳಿತಾಯ ಮಾಡಲಾಗಿದೆ ಎಂದು ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ಒಂದು ಸಂದೇಶ ಹೇಗೆ ಉತ್ತರವಾಗುತ್ತದೆ ಎಂಬುದನ್ನು ಇದು ಚಿತ್ರಿಸುತ್ತದೆ.**
ಲೈವ್ ಫ್ಲೋ ಡಯಾಗ್ರಾಂ: ನೀವು, ಅದು ಬಂದ ಚಾನಲ್, ಗೇಟ್‌ವೇ, ಈಗ ಉತ್ತರಿಸುತ್ತಿರುವ ಮಾಡೆಲ್, ಮತ್ತು ಅದು ಬಳಸಿದ ಪ್ರತಿ ಟೂಲ್. ಕೆಲಸ ಅವುಗಳ ಮೂಲಕ ಚಲಿಸುತ್ತಿದ್ದಂತೆ ನೋಡ್‌ಗಳು ಬೆಳಗುತ್ತವೆ.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ಯಂತ್ರದಲ್ಲಿನ ಪ್ರತಿ ಏಜೆಂಟ್, ಒಂದೇ ಟೇಬಲ್‌ನಲ್ಲಿ.**
ಅದು ಏನನ್ನು ಚಲಾಯಿಸುತ್ತದೆ, ಕಳೆದ 24 ಗಂಟೆಗಳಲ್ಲಿ ಮತ್ತು ಅದರ ಜೀವಿತಾವಧಿಯಲ್ಲಿ ಅದಕ್ಕೆ ಎಷ್ಟು ವೆಚ್ಚವಾಗುತ್ತದೆ, ಅದನ್ನು ಕೊನೆಯದಾಗಿ ಯಾವಾಗ ನೋಡಲಾಯಿತು, ಅದನ್ನು ಯಾರು ಹೊಂದಿದ್ದಾರೆ, ಮತ್ತು ಚಂದಾದಾರಿಕೆ ಬಿಲ್ ಅನ್ನು ಒಳಗೊಂಡಿದೆಯೇ. ಇಲ್ಲಿ 14 ಏಜೆಂಟ್‌ಗಳು, 3 ಸೆಷನ್‌ಗಳು ಕೆಲಸ ಮಾಡುತ್ತಿವೆ, 13 ಸ್ತಬ್ಧವಾಗಿವೆ.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ಒಂದು ಟರ್ನ್‌ನ ಸಮಯ ಮತ್ತು ಹಣ ಎಲ್ಲಿ ಹೋಯಿತು ಎಂದು ಇದು ಟೂಲ್ ಮೂಲಕ ಟೂಲ್ ತೋರಿಸುತ್ತದೆ.**
ಒಂದು ನಿಜವಾದ ಸೆಷನ್‌ನ ಒಂದು ಟರ್ನ್: $1.16 ಗೆ 11.2 ನಿಮಿಷಗಳಲ್ಲಿ 11 ಟೂಲ್‌ಗಳು. ಪ್ರತಿ Bash ಕರೆ ಮತ್ತು ಮಾಡೆಲ್ ಕರೆಗೆ ಟೈಮ್‌ಲೈನ್‌ನಲ್ಲಿ ತನ್ನದೇ ಬಾರ್ ಸಿಗುತ್ತದೆ, ಆದ್ದರಿಂದ 4.1 ನಿಮಿಷಗಳ ಕಾಲ ಓಡಿದ ಆದೇಶ ಮತ್ತು 226ms ಕಾಲ ಓಡಿದ ಆದೇಶ ಒಂದೇ ನೋಟದಲ್ಲಿ ಬೇರ್ಪಟ್ಟು ಕಾಣಿಸುತ್ತವೆ.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ಇದು ಕೇವಲ ಖರ್ಚನ್ನಲ್ಲ, ಕೆಲಸವನ್ನೂ ಗ್ರೇಡ್ ಮಾಡುತ್ತದೆ.**
ಈ ವಾರ ಒಂದು A: 54 ಟಾಸ್ಕ್‌ಗಳು ಸ್ವಚ್ಛವಾಗಿ ಹಿಂತಿರುಗಿದವು, 2 ಒರಟಾದವು $48.57 ವೆಚ್ಚವಾಯಿತು, ಮತ್ತು ಗ್ರೇಡ್ ಮಾಡಲು ಸಾಕಷ್ಟು ಚಟುವಟಿಕೆ ಇಲ್ಲದ ರನ್‌ಗಳನ್ನು ವಿಜಯಗಳಾಗಿ ಎಣಿಸುವ ಬದಲು ಹೊರಗಿಡಲಾಗಿದೆ. ಪ್ರತಿ ಒರಟಾದ ರನ್ ಅದರ ಟ್ರೇಸ್‌ಗೆ ಲಿಂಕ್ ಮಾಡುತ್ತದೆ.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ಕಾಂಟೆಕ್ಸ್ಟ್ ವಿಂಡೋ ಏಕೆ ತುಂಬುತ್ತಲೇ ಇರುತ್ತದೆ ಎಂದು ಇದು ತೋರಿಸುತ್ತದೆ.**
ಇತ್ತೀಚಿನ ಟರ್ನ್‌ನಲ್ಲಿ 1M-ಟೋಕನ್ ವಿಂಡೋದ 715K, 83.3% ಪೀಕ್, ಓವರ್‌ಫ್ಲೋ ಬದಲಿಗೆ ಎಲ್ಲವೂ ಪೂರ್ವಭಾವಿಯಾಗಿ ಪ್ರಚೋದಿಸಿದ 4 ಕಂಪ್ಯಾಕ್ಷನ್‌ಗಳು, ಮತ್ತು ಅದರ ಹಿಂದಿನ ಪ್ರತಿ ಟರ್ನ್‌ನ ಬಳಕೆ.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ನೀವು ಏನನ್ನೂ ಕಾನ್ಫಿಗರ್ ಮಾಡದೆಯೇ ಪತ್ತೆಹಚ್ಚುವಿಕೆ ನಡೆಯುತ್ತದೆ.**
ಅಂತರ್ನಿರ್ಮಿತ ಡಿಟೆಕ್ಟರ್‌ಗಳು ಇನ್‌ಸ್ಟಾಲ್‌ನಿಂದಲೇ ಆನ್ ಆಗಿವೆ: ಏಜೆಂಟ್ ಶಾಂತವಾಯಿತು, ಟೆಲಿಮೆಟ್ರಿ ಫೀಡ್ ನಿಂತಿತು, ವೆಚ್ಚ ಸ್ಪೈಕ್, ಟೋಕನ್ ಬರ್ಸ್ಟ್, ಏರುತ್ತಿರುವ ದೋಷಗಳು, ದೋಷ ಸ್ಪೈಕ್, ಬಜೆಟ್ ಮಿತಿ, ಥ್ರೆಟ್ ಸಿಗ್ನೇಚರ್ ಹೊಂದಾಣಿಕೆಯಾಯಿತು, ಭದ್ರತಾ ಟೂಲ್ ಶೋಧನೆ, ಭದ್ರತಾ ಸ್ಥಿತಿ ಬದಲಾಯಿತು. ನಿಮ್ಮದೇ ನಿಯಮಗಳು ಮೇಲಿನದಾಗಿ ಐಚ್ಛಿಕ.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ಅಪಾಯಕಾರಿ ಕರೆಯನ್ನು ಹಿಡಿದಿಡುವುದು ಆಪ್ಟ್-ಇನ್, ಮತ್ತು ಆಫ್ ಆಗಿ ಶಿಪ್ ಆಗುತ್ತದೆ.**
ರೀಕರ್ಸಿವ್ ಡಿಲೀಟ್‌ಗಳು, ಫೋರ್ಸ್ ಪುಶ್‌ಗಳು, sudo, ರಹಸ್ಯಗಳು, ಪ್ಯಾಕೇಜ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು ಮತ್ತು ಔಟ್‌ಬೌಂಡ್ ಕರೆಗಳಿಗೆ ಪ್ರತಿಯೊಂದಕ್ಕೂ ನೀವು ಆನ್ ಮಾಡಬಹುದಾದ ನಿಯಮ ಸಿಗುತ್ತದೆ. ನೀವು ಆನ್ ಮಾಡುವವರೆಗೆ, ClawMetry ವೀಕ್ಷಿಸುತ್ತದೆ ಮತ್ತು ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ. ಒಮ್ಮೆ ಒಂದನ್ನು ಆನ್ ಮಾಡಿದರೆ, ಹೊಂದಾಣಿಕೆಯಾಗುವ ಕರೆಗಳು ಅನುಮೋದನೆ ಅಥವಾ ನಿರಾಕರಣೆಗಾಗಿ ಇಲ್ಲಿ (ಅಥವಾ ನಿಮ್ಮ ಫೋನ್‌ನಲ್ಲಿ) ಕಾಯುತ್ತವೆ.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ಇನ್ನಷ್ಟು, ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## ಸ್ಟಾರ್ ಇತಿಹಾಸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ಲೈಸೆನ್ಸ್

MIT · [@vivekchand](https://github.com/vivekchand) ನಿಂದ ನಿರ್ಮಿಸಲಾಗಿದೆ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
