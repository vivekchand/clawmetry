<!-- i18n-src:9767c8001c9c -->
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

**ನಿಮ್ಮ ಏಜೆಂಟ್ ಯೋಚಿಸುವುದನ್ನು ನೋಡಿ.** **30 AI ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳಿಗೆ** ರಿಯಲ್-ಟೈಮ್ ಅಬ್ಸರ್ವೆಬಿಲಿಟಿ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ಮತ್ತು ಇನ್ನೂ 26. ನಿಮ್ಮ ಇಡೀ ಏಜೆಂಟ್ ಫ್ಲೀಟ್‌ಗೆ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್.

> 🌐 **ಇದನ್ನು ಈ ಭಾಷೆಗಳಲ್ಲಿ ಓದಿ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ಇನ್ನಷ್ಟು →](docs/i18n/)

ಒಂದೇ ಕಮಾಂಡ್. ಶೂನ್ಯ ಕಾನ್ಫಿಗ್. ಎಲ್ಲವನ್ನೂ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಪತ್ತೆಹಚ್ಚುತ್ತದೆ.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ನಲ್ಲಿ ತೆರೆಯುತ್ತದೆ. ಶೂನ್ಯ ಕಾನ್ಫಿಗ್: ಇದು ನಿಮ್ಮಲ್ಲಿ ಈಗಾಗಲೇ ಇರುವ ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳನ್ನು ಕಂಡುಹಿಡಿಯುತ್ತದೆ, ಅವುಗಳನ್ನು ಓದು-ಮಾತ್ರ ಆಗಿ ಓದುತ್ತದೆ, ಮತ್ತು ಅವು ಹೇಗೆ ಚಲಿಸುತ್ತವೆ ಎಂಬುದರಲ್ಲಿ ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ಏಜೆಂಟ್ ರನ್‌ಟೈಮ್‌ಗಳೊಂದಿಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ

**ಓಪನ್ ಸೋರ್ಸ್ ಆ್ಯಪ್‌ನಲ್ಲಿ ಉಚಿತ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ಪಾವತಿಸಿದ ಪ್ಲಾನ್‌ನಲ್ಲಿ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೂ ಒಂದೇ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ಸಿಗುತ್ತದೆ. ಒಂದೇ ಸಮಯದಲ್ಲಿ ಹಲವನ್ನು ಚಲಾಯಿಸಿ, ಮತ್ತು ಹೆಡರ್ ಸ್ವಿಚರ್ ಪ್ರತಿ ಟ್ಯಾಬ್‌ನ ವ್ಯಾಪ್ತಿಯನ್ನು ಅವುಗಳಲ್ಲಿ ಒಂದಕ್ಕೆ ಮರುಹೊಂದಿಸುತ್ತದೆ.

SDK ಬಳಸಿ ನಿಮ್ಮದೇ ಆದ ಏಜೆಂಟ್ ನಿರ್ಮಿಸಿದ್ದೀರಾ? ಇಂಟರ್‌ಸೆಪ್ಟರ್ ಅದರ LLM ಕರೆಗಳನ್ನೂ ಟ್ರ್ಯಾಕ್ ಮಾಡುತ್ತದೆ. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ನೋಡಿ.

## ನಿಮಗೆ ಏನು ಸಿಗುತ್ತದೆ

- **ಸೆಷನ್‌ಗಳು ಮತ್ತು ಟ್ರಾನ್ಸ್‌ಕ್ರಿಪ್ಟ್‌ಗಳು**: ಪ್ರತಿ ಏಜೆಂಟ್ ಏನು ಮಾಡಿತು, ಟರ್ನ್‌ಗಟ್ಟಲೆ, ರೀಪ್ಲೇ ಸಮೇತ
- **ವೆಚ್ಚ ಮತ್ತು ಟೋಕನ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್, ಮಾಡೆಲ್, ಸೆಷನ್ ಮತ್ತು ದಿನಕ್ಕೆ, ಅಸಂಗತತೆಯ ಫ್ಲ್ಯಾಗ್‌ಗಳೊಂದಿಗೆ
- **ಫ್ಲೋ**: ಚಾನೆಲ್‌ಗಳು, ಮಾಡೆಲ್‌ಗಳು ಮತ್ತು ಟೂಲ್‌ಗಳ ಮೂಲಕ ಚಲಿಸುವ ಸಂದೇಶಗಳ ಲೈವ್ ಡಯಾಗ್ರಾಂ
- **ಬ್ರೈನ್**: ಸಂಭವಿಸುತ್ತಿರುವಂತೆ ರೀಸನಿಂಗ್ ಮತ್ತು ಟೂಲ್-ಕಾಲ್ ಈವೆಂಟ್ ಸ್ಟ್ರೀಮ್
- **ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್**: ಪ್ರತಿ ಪ್ರೊವೈಡರ್‌ಗೆ ತಕ್ಕಂತೆ ಗಾತ್ರಗೊಳಿಸಿದ ವಿಂಡೋ ಬಳಕೆ, ಕಂಪ್ಯಾಕ್ಷನ್ Vs ಬಲವಂತದ ಓವರ್‌ಫ್ಲೋ, ಜೊತೆಗೆ ನಮಗೆ *ಕಾಣಿಸದ* ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ನಕ್ಷೆ ([ಹೇಗೆ](docs/CONTEXT_BLOWOUT.md))
- **ಮೆಮೊರಿ ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು**: ಪ್ರತಿ ರನ್‌ಟೈಮ್ ನಿಜವಾಗಿ ಲೋಡ್ ಮಾಡಿದ ಫೈಲ್‌ಗಳು ಮತ್ತು ಸ್ಕಿಲ್‌ಗಳು
- **ಆರೋಗ್ಯ ಮತ್ತು ಲಾಗ್‌ಗಳು**: ಡಿಸ್ಕ್, ಮೆಮೊರಿ, ದೋಷ ದರಗಳು, ದರ ಮಿತಿಗಳು, ಲೈವ್ ಲಾಗ್ ಸ್ಟ್ರೀಮ್
- **ಎಚ್ಚರಿಕೆಗಳು**: ಬಜೆಟ್ ಮಿತಿಗಳು, ದೋಷ ಏರಿಕೆಗಳು, ಏಜೆಂಟ್-ಆಫ್‌ಲೈನ್, Slack, Discord, PagerDuty, Telegram, Email ಗೆ ರೂಟ್ ಮಾಡಲಾಗಿದೆ
- **ಅನುಮೋದನೆಗಳು**: ಅಪಾಯಕಾರಿ ಟೂಲ್ ಕರೆಗಳನ್ನು ಅವು ಚಲಿಸುವ *ಮೊದಲು* ವಿರಮಿಸಿ ಮತ್ತು ನಿಮ್ಮ ಫೋನ್‌ನಿಂದ ಅನುಮೋದಿಸಿ ([ಹೇಗೆ](docs/APPROVALS.md))

## ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್, ಮತ್ತು ಮಾನಿಟರಿಂಗ್‌ನ ವೆಚ್ಚ

ಯಾವುದೇ ಏಜೆಂಟ್-ಹೋಲಿಕೆ ಟೂಲ್ ಅನ್ನು ನಂಬುವ ಮೊದಲು ಉತ್ತರಿಸಲು ಯೋಗ್ಯವಾದ ಎರಡು ಪ್ರಶ್ನೆಗಳು.

**ಇದು ರನ್‌ಟೈಮ್‌ಗಳಾದ್ಯಂತ ಕಾಂಟೆಕ್ಸ್ಟ್-ವಿಂಡೋ ಬ್ಲೋಔಟ್ ಅನ್ನು ಹೇಗೆ ನಿಭಾಯಿಸುತ್ತದೆ?**

ಬಳಕೆಯ ಶೇಕಡಾವಾರು ಅದನ್ನು ಯಾವುದರಿಂದ ಭಾಗಿಸಲಾಗಿದೆ ಎಂಬುದಷ್ಟೇ ಪ್ರಾಮಾಣಿಕವಾಗಿರುತ್ತದೆ. ClawMetry
Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama ಮತ್ತು GLM ಅನ್ನು
ಒಳಗೊಂಡ, ನೀವು ಓದಬಹುದಾದ ಮತ್ತು PR ಮಾಡಬಹುದಾದ [ಒಂದು ಟೇಬಲ್](clawmetry/context_windows.py) ನಿಂದ
ಪ್ರತಿ ಪ್ರೊವೈಡರ್‌ಗೆ ತಕ್ಕಂತೆ ವಿಂಡೋವನ್ನು ಗಾತ್ರಗೊಳಿಸುತ್ತದೆ. ಇದು 26 ರನ್‌ಟೈಮ್‌ಗಳನ್ನೆಲ್ಲಾ ಒಬ್ಬ
ವೆಂಡರ್‌ನ ಮಾಪಕದಿಂದ ಅಳೆಯುವುದಿಲ್ಲ. ಅದು ಮುಖ್ಯ: 300K GPT-5 ಟರ್ನ್ ಅನ್ನು Anthropic ನ 200K
ವಿರುದ್ಧ ಅಳೆದಾಗ ">100%, ಬ್ಲೋನ್" ಎಂದು ಓದುತ್ತದೆ, ಆದರೆ ಅದು ನಿಜವಾಗಿ GPT-5 ನ 400K ನ 75%
ನಲ್ಲಿದೆ. ಇದೇ ಮಾಪಕವು ನಿಜವಾಗಿ ಓವರ್‌ಫ್ಲೋ ಆದ 130K DeepSeek ಟರ್ನ್ ಅನ್ನು ಆರಾಮದಾಯಕ 65%
ಎಂದು ಮರೆಮಾಚುತ್ತದೆ.

ಪ್ರತಿ ವಿಂಡೋ ತನ್ನ ಮೂಲ ಸಮೇತ ಬರುತ್ತದೆ: `model_table`, `explicit_marker`,
`observed_floor`, ಅಥವಾ ನಮಗೆ ಮಾಡೆಲ್ ಗೊತ್ತಿಲ್ಲದಿದ್ದಾಗ ಪ್ರಾಮಾಣಿಕ `default`. ಊಹೆಯ ಮೇಲೆ
ನಿರ್ಮಿಸಲಾದ ಗೇಜ್ ಎಂದಿಗೂ ಲುಕಪ್‌ನ ಮೇಲೆ ನಿರ್ಮಿಸಿದ ಒಂದರಷ್ಟೇ ಅಧಿಕಾರದೊಂದಿಗೆ ರೆಂಡರ್ ಆಗುವುದಿಲ್ಲ.

ClawMetry ಗೆ ಕೆಲವು ರನ್‌ಟೈಮ್‌ಗಳಲ್ಲಿ ಮಾತ್ರ ಕಂಪ್ಯಾಕ್ಷನ್ ಈವೆಂಟ್‌ಗಳು ಕಾಣಬಹುದು. ಆದ್ದರಿಂದ
`GET /api/context-coverage` ಪ್ರತಿ ರನ್‌ಟೈಮ್‌ಗೆ, ಒಂದು **ಶೂನ್ಯ ಎಂದರೆ "ಸ್ವಚ್ಛವಾಗಿ ಓಡಿತು"
ಅಥವಾ "ನಾವು ಕುರುಡರು"** ಎಂಬುದನ್ನು ವರದಿ ಮಾಡುತ್ತದೆ. ನಿಜವಾಗಿ ಕುರುಡು ಎಂದರ್ಥವಾಗುವ `0` ಅದನ್ನೇ
ಹೇಳುತ್ತದೆ. [ಪೂರ್ಣ ವಿವರ](docs/CONTEXT_BLOWOUT.md)

**ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ನ ವೆಚ್ಚವೆಷ್ಟು?**

| ಪಥ | ನಿಮ್ಮ ಏಜೆಂಟ್‌ಗೆ ಸೇರಿಸಲಾಗಿದೆ | ಡೀಫಾಲ್ಟ್? |
|---|---|---|
| ಸೆಷನ್-ಫೈಲ್ ಟೇಲಿಂಗ್ (ಎಲ್ಲ 30 ರನ್‌ಟೈಮ್‌ಗಳು) | **0**. ಪ್ರತ್ಯೇಕ ಪ್ರೋಸೆಸ್, ನಿಮ್ಮ ಏಜೆಂಟ್‌ನಲ್ಲಿ ClawMetry ಕೋಡ್ ಇಲ್ಲ | ಆನ್ |
| HTTP ಇಂಟರ್‌ಸೆಪ್ಟರ್ (`CLAWMETRY_INTERCEPT=1`) | ಪ್ರತಿ LLM ಕರೆಗೆ **+0.44 ms**, ಅಥವಾ 5s ಕರೆಯ 0.009% | ಆಫ್ |
| Pre-tool hook gate (ಬೆಚ್ಚಗಿನ ಕ್ಯಾಶ್) | 36 ms ಇಂಟರ್‌ಪ್ರಿಟರ್ ನೆಲದ ಮೇಲೆ, ಪ್ರತಿ ಗೇಟ್ ಮಾಡಿದ ಟೂಲ್ ಕರೆಗೆ **+44 ms** | ಆಫ್ |
| Enforcement proxy | ಪ್ರತಿ LLM ಕರೆಗೆ **+9.7 ms** | ಆಫ್ |

ಡೀಮನ್ ಹೋಸ್ಟ್ ವೆಚ್ಚ: **2,762 ಈವೆಂಟ್‌ಗಳು/ಸೆ** ಇಂಜೆಸ್ಟ್, ಡಿಸ್ಕ್‌ನಲ್ಲಿ **710 ಬೈಟ್‌ಗಳು/ಈವೆಂಟ್**
(100k ಈವೆಂಟ್‌ಗಳಿಗೆ 67.7 MB), ಮತ್ತು ಬ್ಯುಸಿ ಇನ್‌ಸ್ಟಾಲ್‌ನಲ್ಲಿ ನಿರಂತರವಾಗಿ **ಒಂದು ಕೋರ್‌ನ ~12%**.
ಆ ಕೊನೆಯ ಸಂಖ್ಯೆ ನಮ್ಮ ಸ್ವಂತ ನಿಗದಿತ 5-10% ಬಜೆಟ್ ಮೀರಿದೆ, ಆದ್ದರಿಂದ ಅದನ್ನು ಪುಟದಿಂದ
ಬಿಟ್ಟುಬಿಡುವ ಬದಲು ಬೆನ್ನಟ್ಟಬೇಕಾದ ಬಗ್ ಆಗಿ ಪ್ರಕಟಿಸಲಾಗಿದೆ.

Apple M2 Pro ನಲ್ಲಿ `benchmarks/overhead.py` ನೊಂದಿಗೆ ಅಳೆಯಲಾಗಿದೆ. ಈ ಹಾರ್ನೆಸ್ ಪ್ರತಿ
ಸ್ಥಿತಿಯನ್ನು ಪ್ರತ್ಯೇಕ ಪ್ರೋಸೆಸ್‌ನಲ್ಲಿ ಚಲಾಯಿಸುತ್ತದೆ, ಅವುಗಳ ಕ್ರಮವನ್ನು ಪರ್ಯಾಯವಾಗಿ ಬದಲಿಸುತ್ತದೆ,
ಮತ್ತು **ಸುತ್ತುಗಳು ಅದರ ಚಿಹ್ನೆಯ ಬಗ್ಗೆ ಒಪ್ಪದಿದ್ದಾಗ ಸಂಖ್ಯೆಯನ್ನು ಮುದ್ರಿಸಲು ನಿರಾಕರಿಸುತ್ತದೆ**.
ಒಂದು ನಿಮಿಷದಲ್ಲಿ ಇದನ್ನು ನಿಮ್ಮ ಸ್ವಂತ ಯಂತ್ರದಲ್ಲಿ ಚಲಾಯಿಸಿ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

hook gate ಮತ್ತು enforcement proxy ಸೇರಿದಂತೆ ಪ್ರತಿ ಪಥವನ್ನೂ ಅಳೆಯಲಾಗಿದೆ, ಮತ್ತು ಈ ಹಾರ್ನೆಸ್
CI ಯಲ್ಲಿ Linux, macOS ಮತ್ತು Windows ನಲ್ಲಿ ಚಲಿಸುತ್ತದೆ. ತಿಳಿಯಬೇಕಾದ ಎರಡು ಫಲಿತಾಂಶಗಳು: proxy
Windows ನಲ್ಲಿ Linux ಗಿಂತ ಸುಮಾರು ಏಳು ಪಟ್ಟು ಹೆಚ್ಚು ವೆಚ್ಚ ಮಾಡುತ್ತದೆ, ಮತ್ತು ಡೀಮನ್ ಪ್ರಸ್ತುತ
ಒಂದು ಕೋರ್‌ನ ಸುಮಾರು 12% ಅನ್ನು ನಿರಂತರವಾಗಿ ಬಳಸುತ್ತದೆ, ಇದು ನಮ್ಮ ಸ್ವಂತ 5-10% ಬಜೆಟ್
ಮೀರಿದೆ. ರಾ JSON, ವಿಧಾನ, ಮತ್ತು ಇನ್ನೂ ಅಳೆಯಲಾಗದ್ದು [docs/OVERHEAD.md](docs/OVERHEAD.md)
ನಲ್ಲಿದೆ.

## ಬೆಲೆ ನಿಗದಿ

| ಪ್ಲಾನ್ | ಇದು ಏನನ್ನು ಒಳಗೊಳ್ಳುತ್ತದೆ | ಬೆಲೆ |
|---|---|---|
| **ಉಚಿತ** | OpenClaw + NVIDIA NemoClaw + Goose, ಪೂರ್ಣ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್, ಸ್ಥಳೀಯ ಮಾತ್ರ | $0 |
| **Starter** | ಮೇಲಿನ ಪ್ರತಿಯೊಂದು ಇತರ ರನ್‌ಟೈಮ್, ಫ್ಲೀಟ್ ವ್ಯೂ, ಕ್ಲೌಡ್ ಸಿಂಕ್ | ಪ್ರತಿ ನೋಡ್‌ಗೆ $9 / ತಿಂಗಳಿಗೆ |
| **Pro** | Starter + ನಿಯಂತ್ರಣ ಮತ್ತು ಮೌಲ್ಯಮಾಪನ: ಅನುಮೋದನೆಗಳು, ಟೂಲ್-ಅಪಾಯ ನೀತಿಗಳು, evals, ಅಸಂಗತತೆ ಪತ್ತೆ, ವೆಚ್ಚ ಆಪ್ಟಿಮೈಸರ್, OTel ಎಕ್ಸ್‌ಪೋರ್ಟ್, ಟ್ಯಾಂಪರ್-ಎವಿಡೆಂಟ್ ಆಡಿಟ್ ಲಾಗ್ | ಪ್ರತಿ ನೋಡ್‌ಗೆ $19 / ತಿಂಗಳಿಗೆ |

ವಾರ್ಷಿಕ ಪ್ಲಾನ್‌ಗಳು, Enterprise ಮತ್ತು ಪ್ರಸ್ತುತ ಸಂಖ್ಯೆಗಳು
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ನಲ್ಲಿ ಇವೆ. ಸ್ವಯಂ-ಹೋಸ್ಟ್
ಮಾಡಿದ ಲೈಸೆನ್ಸ್ ಕೀಗಳು ಕ್ಲೌಡ್ ಇಲ್ಲದೆಯೂ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತವೆ (`clawmetry license`). ನಿಖರವಾದ
ಉಚಿತ/ಪಾವತಿ ವಿಭಜನೆ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ನಲ್ಲಿದೆ.

## ನಿಮ್ಮ ಡೇಟಾ ನಿಮ್ಮ ಯಂತ್ರದಲ್ಲೇ ಇರುತ್ತದೆ

ClawMetry ಸ್ಥಳೀಯ ಸೆಷನ್ ಫೈಲ್‌ಗಳು ಮತ್ತು ಲಾಗ್‌ಗಳನ್ನು ಓದುತ್ತದೆ. **ನೀವು `clawmetry connect`
ಚಲಾಯಿಸದ ಹೊರತು ಯಾವುದೇ ಸೆಷನ್ ಡೇಟಾ ನಿಮ್ಮ ಬಾಕ್ಸ್‌ನಿಂದ ಹೊರಹೋಗುವುದಿಲ್ಲ** — ಯಾವುದೇ
ಪ್ರಾಂಪ್ಟ್‌ಗಳು, ಪ್ರತ್ಯುತ್ತರಗಳು, ಟೂಲ್ ಆರ್ಗ್ಯುಮೆಂಟ್‌ಗಳು, ಫೈಲ್ ವಿಷಯಗಳು ಅಥವಾ ಲಾಗ್ ಲೈನ್‌ಗಳಿಲ್ಲ.
ನೀವು ಕನೆಕ್ಟ್ ಮಾಡಿದಾಗ, ಸ್ನ್ಯಾಪ್‌ಶಾಟ್ ಎಂದಿಗೂ ನಿಮ್ಮ ಯಂತ್ರವನ್ನು ಬಿಡದ ಕೀಯೊಂದಿಗೆ
ಎಂಡ್-ಟು-ಎಂಡ್ ಎನ್‌ಕ್ರಿಪ್ಟ್ ಆಗುತ್ತದೆ, ಮತ್ತು ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಡಿಕ್ರಿಪ್ಟ್ ಆಗುತ್ತದೆ. ಒಂದು
ನೋಡ್‌ಗೆ ಕೀ ಇಲ್ಲದಿದ್ದರೆ, ಅಪ್‌ಲೋಡ್ ಅನ್ನು ಸ್ಪಷ್ಟವಾಗಿ ಕಳುಹಿಸುವ ಬದಲು ಸ್ಕಿಪ್ ಮಾಡಲಾಗುತ್ತದೆ,
ಮತ್ತು ಯಾವುದೇ ಸರ್ವರ್ ಪ್ರತಿಕ್ರಿಯೆ ಅದನ್ನು ಆಫ್ ಮಾಡಲಾಗುವುದಿಲ್ಲ.

ನೀವು ಕನೆಕ್ಟ್ ಮಾಡುವ ಮೊದಲೇ ಡೀಫಾಲ್ಟ್ ಆಗಿ ಚಲಿಸುವ ಎರಡು ವಿಷಯಗಳಿವೆ, ಎರಡೂ ಆಪ್ಟ್-ಔಟ್ ಮತ್ತು
ಯಾವುದೂ ಸೆಷನ್ ಡೇಟಾ ಒಯ್ಯುವುದಿಲ್ಲ: ಒಂದು ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಪಿಂಗ್ ಮತ್ತು PyPI ವಿರುದ್ಧ ಒಂದು
ವರ್ಷನ್ ಚೆಕ್. ಡೀಫಾಲ್ಟ್ ಇನ್‌ಸ್ಟಾಲ್ ಸ್ಟಾರ್ಟ್‌ಅಪ್ ಬ್ಯಾನರ್ ಲೈನ್‌ಗಾಗಿ ನಿಮ್ಮ ಸಾರ್ವಜನಿಕ IP
ಅನ್ನೂ ಒಮ್ಮೆ ಹುಡುಕುತ್ತದೆ. ಪ್ರತಿ ಗಮ್ಯಸ್ಥಾನ, ಅದು ಏನನ್ನು ಒಯ್ಯುತ್ತದೆ ಮತ್ತು ಅದನ್ನು ಹೇಗೆ
ಆಫ್ ಮಾಡುವುದು ಎಂಬುದೆಲ್ಲಾ [docs/EGRESS.md](docs/EGRESS.md) ನಲ್ಲಿ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ; ಸ್ವಯಂ-
ಹೋಸ್ಟ್ ಮಾಡಿದ, ಮರುನಿರ್ದೇಶಿಸಿದ ಮತ್ತು ಏರ್-ಗ್ಯಾಪ್ಡ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು ಯಾವುದೇ ಸ್ವಇಚ್ಛೆಯ
ಔಟ್‌ಬೌಂಡ್ ಕರೆಗಳನ್ನೂ ಮಾಡುವುದಿಲ್ಲ.

ಡಿಕ್ರಿಪ್ಶನ್ ನಿಮ್ಮ ಬ್ರೌಸರ್‌ನಲ್ಲಿ, ನಾವು ನಿಮಗೆ ಒದಗಿಸುವ ಕೋಡ್‌ನಲ್ಲಿ ಸಂಭವಿಸುತ್ತದೆ. ಇದು ಮೊದಲು
ಒಂದು ಭರವಸೆ ಆಗಿತ್ತು; ಈಗ ಇದು ನೀವು ಪರಿಶೀಲಿಸಬಹುದಾದ ವಿಷಯ. ನಿಮ್ಮ ಕೀ ಮುಟ್ಟುವ ಪ್ರತಿ ಸಾಲೂ
ಒಂದೇ ಓದಬಹುದಾದ ಫೈಲ್‌ನಲ್ಲಿ ವಾಸಿಸುತ್ತದೆ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
ಇದು wheel ಒಳಗೆ ಶಿಪ್ ಆಗುತ್ತದೆ ಮತ್ತು ಯಥಾವತ್ ಆಗಿ ಸರ್ವ್ ಆಗುತ್ತದೆ, Subresource Integrity
ಹ್ಯಾಶ್‌ನೊಂದಿಗೆ ಪಿನ್ ಮಾಡಲಾಗಿದೆ. ಬ್ರೌಸರ್ ನಾವು ಪ್ರಕಟಿಸಿದ್ದನ್ನೇ ಚಲಾಯಿಸುತ್ತದೆ ಎಂದು
ದೃಢೀಕರಿಸಲು:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ಅದು ಸಾಬೀತುಪಡಿಸದಿರುವುದು: ಫೈಲ್ ಲೋಡ್ ಮಾಡುವ ಪುಟವನ್ನೂ ನಾವೇ ಸರ್ವ್ ಮಾಡುತ್ತೇವೆ, ಆದ್ದರಿಂದ
ನಾವು ಬೇರೆ ಪುಟವನ್ನೂ ಸರ್ವ್ ಮಾಡಬಹುದಿತ್ತು. Integrity ಹ್ಯಾಶ್‌ಗಳು ನಿಮ್ಮನ್ನು ಒಂದು ರಾಜಿಯಾದ
CDN ನಿಂದ ರಕ್ಷಿಸುತ್ತವೆ, ವೆಂಡರ್‌ನಿಂದಲ್ಲ. ನೀವು ಪಡೆಯುವುದೇನೆಂದರೆ ಯಾವುದೇ ಬದಲಾವಣೆ ಉದ್ದೇಶಪೂರ್ವಕ,
ಪುಟದ ಮೂಲದಲ್ಲಿ ಗೋಚರ, ಮತ್ತು ಯಾರಾದರೂ ಪಡೆಯಬಹುದಾದ PyPI ಯ ಆರ್ಟಿಫ್ಯಾಕ್ಟ್‌ಗಿಂತ ಭಿನ್ನವಾಗಿರಬೇಕು
ಎಂಬುದೇ. ಸ್ವಯಂ-ಹೋಸ್ಟಿಂಗ್ ಅಥವಾ ಸ್ಥಳೀಯ-ಮಾತ್ರ ಇರುವುದು ಈ ಅವಲಂಬನೆಯನ್ನೇ ತೆಗೆದುಹಾಕುತ್ತದೆ.

## ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಿ

```bash
pip install clawmetry     # ನಂತರ: clawmetry
```

ಅಥವಾ ಒಂದೇ ಸಾಲಿನ ಆದೇಶ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ಅಥವಾ Windows ನಲ್ಲಿ Python 3.8+ ಮತ್ತು ಅದೇ ಯಂತ್ರದಲ್ಲಿ ಕನಿಷ್ಠ ಒಂದು ಏಜೆಂಟ್
ರನ್‌ಟೈಮ್ ಬೇಕು. Docker ಸೂಚನೆಗಳು: [docs/DOCKER.md](docs/DOCKER.md).

## ದಾಖಲೆಗಳು

| | |
|---|---|
| [ರನ್‌ಟೈಮ್ ಹೊಂದಾಣಿಕೆ](docs/compatibility.md) | ಪ್ರತಿ ಅಡಾಪ್ಟರ್ ಏನನ್ನು ಓದುತ್ತದೆ, ಮತ್ತು ರನ್‌ಟೈಮ್ ಸೇರಿಸುವುದು ಹೇಗೆ |
| [ಕಾಂಟೆಕ್ಸ್ಟ್ ಬ್ಲೋಔಟ್](docs/CONTEXT_BLOWOUT.md) | ಪ್ರತಿ-ಪ್ರೊವೈಡರ್ ವಿಂಡೋಗಳು, ಕಂಪ್ಯಾಕ್ಷನ್ Vs ಓವರ್‌ಫ್ಲೋ, ಪ್ರತಿ-ರನ್‌ಟೈಮ್ ಕವರೇಜ್ |
| [ಓವರ್‌ಹೆಡ್](docs/OVERHEAD.md) | ಇನ್‌ಸ್ಟ್ರುಮೆಂಟೇಶನ್‌ನ ವೆಚ್ಚ, ಅಳೆಯಲಾಗಿದೆ, ಮರುಉತ್ಪಾದಿಸಲು ಹಾರ್ನೆಸ್‌ನೊಂದಿಗೆ |
| [Entitlements](docs/ENTITLEMENTS.md) | ಉಚಿತ Vs ಪಾವತಿ, ಟಯರ್ ಮ್ಯಾಟ್ರಿಕ್ಸ್, ಲೈಸೆನ್ಸ್ CLI |
| [ಅನುಮೋದನೆಗಳು ಮತ್ತು ನೀತಿಗಳು](docs/APPROVALS.md) | ಪೂರ್ವ-ನಿರ್ವಹಣಾ ಗೇಟಿಂಗ್, ಅಪಾಯ ಸ್ಕೋರಿಂಗ್, ಫೋನ್ ಅನುಮೋದನೆಗಳು |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ಎಲ್ಲಿಯಾದರೂ ಟ್ರೇಸ್‌ಗಳನ್ನು ಎಕ್ಸ್‌ಪೋರ್ಟ್ ಮಾಡಿ, ಎಲ್ಲಿಂದಲಾದರೂ OTLP ಇಂಜೆಸ್ಟ್ ಮಾಡಿ |
| [ನಿಮ್ಮದೇ ಏಜೆಂಟ್ ತನ್ನಿ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ಪೂರ್ಣವಾಗಿ, ಚಲಾಯಿಸಬಹುದಾದ ಉದಾಹರಣೆಗಳೊಂದಿಗೆ |
| [SDK ಟ್ರ್ಯಾಕಿಂಗ್](docs/SDK_TRACKING.md) | ನೀವೇ ನಿರ್ಮಿಸಿದ ಏಜೆಂಟ್‌ಗಳಿಗೆ ವೆಚ್ಚ ಆಟ್ರಿಬ್ಯೂಷನ್ |
| [ಚಾಟ್ ಚಾನೆಲ್‌ಗಳು](docs/CHANNELS.md) | Flow ನಲ್ಲಿ ತೋರಿಸಲಾದ ಚಾಟ್ ಅಡಾಪ್ಟರ್‌ಗಳು |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ಸ್ಯಾಂಡ್‌ಬಾಕ್ಸ್ ಮಾಡಿದ NVIDIA NemoClaw ಸೆಟಪ್‌ಗಳು |
| [Docker](docs/DOCKER.md) | ಇಮೇಜ್, compose, ವಾಲ್ಯೂಮ್ ಮೌಂಟ್‌ಗಳು |
| [ವಾಸ್ತುಶಿಲ್ಪ](ARCHITECTURE.md) · [ಅಭಿವೃದ್ಧಿ](docs/DEVELOPMENT.md) | ಇದು ಒಳಗಡೆ ಹೇಗೆ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತದೆ; ಮೂಲದಿಂದ ಚಲಾಯಿಸುವುದು |
| [ಟೆಲಿಮೆಟ್ರಿ](docs/TELEMETRY.md) | ಅನಾಮಧೇಯ ಇನ್‌ಸ್ಟಾಲ್ ಮತ್ತು ಡೆಸ್ಕ್‌ಟಾಪ್-ಓಪನ್ ಪಿಂಗ್‌ಗಳು, ಮತ್ತು ಅವುಗಳನ್ನು ಆಫ್ ಮಾಡುವುದು ಹೇಗೆ |

## ಸ್ಕ್ರೀನ್‌ಶಾಟ್‌ಗಳು

ಕೆಳಗಿನ ಪ್ರತಿ ಸಂಖ್ಯೆಯೂ ಒಂದು ನಿಜವಾದ ಯಂತ್ರದಿಂದ, ಓದು-ಮಾತ್ರ, ಏನೂ ಬಿತ್ತದೆ.

**ಏನೋ ತಪ್ಪಾಗಿದೆ ಎಂದು ಇದು ನಿಮಗೆ ಹೇಳುತ್ತದೆ, ಕೇವಲ ಏನಾಯಿತು ಎಂದಷ್ಟೇ ಅಲ್ಲ.**
ಮೇಲ್ಭಾಗದಲ್ಲಿ ಎರಡು ಅಸಂಗತತೆ ಬ್ಯಾನರ್‌ಗಳು: ದೈನಂದಿನ ಸರಾಸರಿಯ 7x ವೆಚ್ಚ ಚಲಿಸುತ್ತಿದೆ, ಮತ್ತು
4.2x ವೆಚ್ಚ ಏರಿಕೆ. ಅವುಗಳ ಕೆಳಗೆ, ಇತ್ತೀಚಿನ 667 ಸೆಷನ್‌ಗಳಲ್ಲಿ 324 ಒಂದು ವ್ಯರ್ಥ ಸಂಕೇತ
ಒಯ್ಯುತ್ತಿವೆ, ಕಾರಣದಿಂದ ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ಹಣ ಎಲ್ಲಿ ಹೋಯಿತು ಎಂದು ಪ್ರತಿ ವಿಂಡೋನಲ್ಲೂ ಇದು ನಿಮಗೆ ತೋರಿಸುತ್ತದೆ.**
ಇಂದು $252.47, ಈ ವಾರ $513.15, ಈ ತಿಂಗಳು $1,312.92, ಪ್ರತಿಯೊಂದರ ಹಿಂದಿನ ಟೋಕನ್‌ಗಳೊಂದಿಗೆ
ಮತ್ತು ಅದರಲ್ಲಿ ಎಷ್ಟನ್ನು ನಿಮ್ಮ ಚಂದಾದಾರಿಕೆ ಈಗಾಗಲೇ ಒಳಗೊಂಡಿದೆ ಎಂಬುದರೊಂದಿಗೆ. ಅದರ ಕೆಳಗೆ,
ಸುಮಾರು $1,128/ತಿಂಗಳು ಮರುಪಡೆಯಬಹುದಾದ ಎಂದು ಪಟ್ಟಿ ಮಾಡಲಾಗಿದೆ ಮತ್ತು ಕ್ಯಾಶ್ ಮರುಬಳಕೆಯಿಂದ
ಈಗಾಗಲೇ ಉಳಿಸಿದ $17,256/ತಿಂಗಳು.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ಒಂದು ಸಂದೇಶ ಹೇಗೆ ಉತ್ತರವಾಗುತ್ತದೆ ಎಂದು ಇದು ಚಿತ್ರಿಸುತ್ತದೆ.**
ಲೈವ್ ಫ್ಲೋ ಡಯಾಗ್ರಾಂ: ನೀವು, ಅದು ಬಂದ ಚಾನೆಲ್, ಗೇಟ್‌ವೇ, ಈಗ ಉತ್ತರಿಸುತ್ತಿರುವ ಮಾಡೆಲ್, ಮತ್ತು
ಅದು ತಲುಪಿದ ಪ್ರತಿ ಟೂಲ್. ಕೆಲಸ ಅವುಗಳ ಮೂಲಕ ಚಲಿಸುತ್ತಿದ್ದಂತೆ ನೋಡ್‌ಗಳು ಬೆಳಗುತ್ತವೆ.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ಯಂತ್ರದ ಮೇಲಿನ ಪ್ರತಿ ಏಜೆಂಟ್, ಒಂದೇ ಟೇಬಲ್‌ನಲ್ಲಿ.**
ಅದು ಏನನ್ನು ಚಲಾಯಿಸುತ್ತದೆ, ಕಳೆದ 24 ಗಂಟೆಗಳಲ್ಲಿ ಮತ್ತು ತನ್ನ ಜೀವಿತಾವಧಿಯಲ್ಲಿ ಅದರ ವೆಚ್ಚವೆಷ್ಟು,
ಅದನ್ನು ಕೊನೆಯ ಬಾರಿ ಯಾವಾಗ ಕಂಡಿತು, ಯಾರ ಒಡೆತನದಲ್ಲಿದೆ, ಮತ್ತು ಒಂದು ಚಂದಾದಾರಿಕೆ ಬಿಲ್
ಅನ್ನು ಒಳಗೊಂಡಿದೆಯೇ. ಇಲ್ಲಿ 14 ಏಜೆಂಟ್‌ಗಳು, 3 ಸೆಷನ್‌ಗಳು ಕೆಲಸ ಮಾಡುತ್ತಿವೆ, 13 ಶಾಂತವಾಗಿವೆ.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ಒಂದು ಟರ್ನ್‌ನ ಸಮಯ ಮತ್ತು ಹಣ ಎಲ್ಲಿ ಹೋಯಿತು ಎಂದು, ಟೂಲ್‌ವೈಸ್, ಇದು ತೋರಿಸುತ್ತದೆ.**
ಒಂದು ನಿಜವಾದ ಸೆಷನ್‌ನ ಒಂದು ಟರ್ನ್: $1.16 ಗೆ 11.2 ನಿಮಿಷಗಳಲ್ಲಿ 11 ಟೂಲ್‌ಗಳು. ಪ್ರತಿ Bash
ಕರೆ ಮತ್ತು ಮಾಡೆಲ್ ಕರೆಗೂ ಟೈಮ್‌ಲೈನ್‌ನಲ್ಲಿ ತನ್ನದೇ ಬಾರ್ ಸಿಗುತ್ತದೆ, ಆದ್ದರಿಂದ 4.1 ನಿಮಿಷ
ಚಲಿಸಿದ ಕಮಾಂಡ್ ಮತ್ತು 226ms ಚಲಿಸಿದ್ದನ್ನು ಒಂದೇ ನೋಟದಲ್ಲಿ ಬೇರ್ಪಡಿಸಬಹುದು.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ಇದು ಕೆಲಸಕ್ಕೆ ಗ್ರೇಡ್ ನೀಡುತ್ತದೆ, ಕೇವಲ ವೆಚ್ಚಕ್ಕಲ್ಲ.**
ಈ ವಾರ ಒಂದು A: 54 ಕಾರ್ಯಗಳು ಸ್ವಚ್ಛವಾಗಿ ಮರಳಿ ಬಂದವು, 2 ಒರಟಾದವು $48.57 ವೆಚ್ಚ ಮಾಡಿದವು,
ಮತ್ತು ತೀರ್ಪು ನೀಡಲು ಸಾಕಷ್ಟು ಚಟುವಟಿಕೆ ಇಲ್ಲದ ರನ್‌ಗಳನ್ನು ಗೆಲುವುಗಳಾಗಿ ಎಣಿಸುವ ಬದಲು
ಗ್ರೇಡ್‌ನಿಂದ ಬಿಟ್ಟುಬಿಡಲಾಗಿದೆ. ಪ್ರತಿ ಒರಟಾದ ರನ್ ತನ್ನ ಟ್ರೇಸ್‌ಗೆ ಲಿಂಕ್ ಮಾಡುತ್ತದೆ.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ಕಾಂಟೆಕ್ಸ್ಟ್ ವಿಂಡೋ ಏಕೆ ನಿರಂತರವಾಗಿ ತುಂಬುತ್ತಿದೆ ಎಂದು ಇದು ತೋರಿಸುತ್ತದೆ.**
ಇತ್ತೀಚಿನ ಟರ್ನ್‌ನಲ್ಲಿ 1M-ಟೋಕನ್ ವಿಂಡೋನ 715K, 83.3% ಪೀಕ್, ಓವರ್‌ಫ್ಲೋ ಬದಲಿಗೆ ಎಲ್ಲಾ 4
ಕಂಪ್ಯಾಕ್ಷನ್‌ಗಳೂ ಪೂರ್ವಭಾವಿಯಾಗಿಯೇ ಪ್ರಚೋದಿಸಲ್ಪಟ್ಟವು, ಜೊತೆಗೆ ಅದರ ಹಿಂದಿನ ಪ್ರತಿ ಟರ್ನ್‌ನ
ಬಳಕೆ.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ಪತ್ತೆಹಚ್ಚುವಿಕೆ ನೀವು ಏನನ್ನೂ ಕಾನ್ಫಿಗರ್ ಮಾಡದೆಯೇ ಚಲಿಸುತ್ತದೆ.**
ಬಿಲ್ಟ್-ಇನ್ ಡಿಟೆಕ್ಟರ್‌ಗಳು ಇನ್‌ಸ್ಟಾಲ್‌ನಿಂದಲೇ ಆನ್ ಆಗಿವೆ: ಏಜೆಂಟ್ ಶಾಂತವಾಯಿತು, ಟೆಲಿಮೆಟ್ರಿ
ಫೀಡ್ ನಿಂತಿತು, ವೆಚ್ಚ ಏರಿಕೆ, ಟೋಕನ್ ಸ್ಫೋಟ, ದೋಷಗಳು ಏರುತ್ತಿವೆ, ದೋಷ ಏರಿಕೆ, ಬಜೆಟ್ ಮಿತಿ,
ಬೆದರಿಕೆ ಸಹಿ ಹೊಂದಾಣಿಕೆಯಾಯಿತು, ಭದ್ರತಾ ಟೂಲ್ ಶೋಧನೆ, ಭದ್ರತಾ ಸ್ಥಿತಿ ಬದಲಾಯಿತು. ನಿಮ್ಮ ಸ್ವಂತ
ನಿಯಮಗಳು ಇವುಗಳ ಮೇಲೆ ಐಚ್ಛಿಕ.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ಅಪಾಯಕಾರಿ ಕರೆಯನ್ನು ಹಿಡಿದಿಡುವುದು ಆಪ್ಟ್-ಇನ್, ಮತ್ತು ಆಫ್ ಆಗಿ ಶಿಪ್ ಆಗುತ್ತದೆ.**
ರೀಕರ್ಸಿವ್ ಡಿಲೀಟ್‌ಗಳು, force push, sudo, ಸೀಕ್ರೆಟ್‌ಗಳು, ಪ್ಯಾಕೇಜ್ ಇನ್‌ಸ್ಟಾಲ್‌ಗಳು ಮತ್ತು
ಔಟ್‌ಬೌಂಡ್ ಕರೆಗಳಿಗೆ ಪ್ರತಿಯೊಂದಕ್ಕೂ ನೀವು ಆನ್ ಮಾಡಬಹುದಾದ ನಿಯಮ ಸಿಗುತ್ತದೆ. ನೀವು ಮಾಡುವವರೆಗೂ,
ClawMetry ವೀಕ್ಷಿಸುತ್ತದೆ ಮತ್ತು ಏನನ್ನೂ ಬದಲಾಯಿಸುವುದಿಲ್ಲ. ಒಂದನ್ನು ಆನ್ ಮಾಡಿದ ಮೇಲೆ,
ಹೊಂದಾಣಿಕೆಯಾಗುವ ಕರೆಗಳು ಇಲ್ಲಿ (ಅಥವಾ ನಿಮ್ಮ ಫೋನ್‌ನಲ್ಲಿ) ಅನುಮೋದನೆ ಅಥವಾ ನಿರಾಕರಣೆಗಾಗಿ
ಕಾಯುತ್ತವೆ.

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

MIT · ನಿರ್ಮಿಸಿದವರು [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
