<!-- i18n-src:9767c8001c9c -->
> ਪੰਜਾਬੀ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦਿਆਂ ਵੇਖੋ।** **30 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਲਈ ਰੀਅਲ-ਟਾਈਮ ਓਬਜ਼ਰਵੇਬਿਲਿਟੀ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ਅਤੇ 26 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ।

> 🌐 **ਇਸਨੂੰ ਇਹਨਾਂ ਭਾਸ਼ਾਵਾਂ ਵਿੱਚ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ। ਸਭ ਕੁਝ ਆਪਣੇ ਆਪ ਪਛਾਣਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 'ਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ: ਇਹ ਉਹ ਏਜੰਟ ਰਨਟਾਈਮ ਲੱਭ ਲੈਂਦਾ ਹੈ ਜੋ ਤੁਹਾਡੇ ਕੋਲ ਪਹਿਲਾਂ ਤੋਂ ਹੀ ਮੌਜੂਦ ਹਨ, ਉਹਨਾਂ ਨੂੰ ਸਿਰਫ਼ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਉਹਨਾਂ ਦੇ ਚੱਲਣ ਦੇ ਤਰੀਕੇ ਵਿੱਚ ਕੁਝ ਵੀ ਨਹੀਂ ਬਦਲਦਾ।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

**ਓਪਨ ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ਪੇਡ ਪਲਾਨ 'ਤੇ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ਹਰ ਰਨਟਾਈਮ ਨੂੰ ਇੱਕੋ ਜਿਹਾ ਡੈਸ਼ਬੋਰਡ ਮਿਲਦਾ ਹੈ। ਇੱਕੋ ਸਮੇਂ ਕਈ ਚਲਾਓ ਅਤੇ ਹੈਡਰ ਸਵਿੱਚਰ ਹਰ ਟੈਬ ਨੂੰ ਉਹਨਾਂ ਵਿੱਚੋਂ ਇੱਕ ਵੱਲ ਦੁਬਾਰਾ ਸਕੋਪ ਕਰ ਦਿੰਦਾ ਹੈ।

ਕੀ ਤੁਸੀਂ ਕਿਸੇ SDK 'ਤੇ ਆਪਣਾ ਖੁਦ ਦਾ ਏਜੰਟ ਬਣਾਇਆ ਹੈ? ਇੰਟਰਸੈਪਟਰ ਉਸ ਦੀਆਂ LLM ਕਾਲਾਂ ਨੂੰ ਵੀ ਟਰੈਕ ਕਰਦਾ ਹੈ। ਵੇਖੋ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **ਸੈਸ਼ਨ ਅਤੇ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ**: ਹਰੇਕ ਏਜੰਟ ਨੇ ਕੀ ਕੀਤਾ, ਵਾਰੀ-ਵਾਰੀ, ਰੀਪਲੇ ਸਮੇਤ
- **ਲਾਗਤ ਅਤੇ ਟੋਕਨ**: ਹਰ ਰਨਟਾਈਮ, ਮਾਡਲ, ਸੈਸ਼ਨ ਅਤੇ ਦਿਨ ਲਈ, ਅਸੰਗਤੀ ਦੇ ਸੰਕੇਤਾਂ ਸਮੇਤ
- **ਫਲੋ**: ਚੈਨਲਾਂ, ਮਾਡਲਾਂ ਅਤੇ ਟੂਲਾਂ ਵਿੱਚੋਂ ਲੰਘਦੇ ਸੁਨੇਹਿਆਂ ਦਾ ਲਾਈਵ ਡਾਇਗ੍ਰਾਮ
- **ਬ੍ਰੇਨ**: ਜਿਵੇਂ ਹੀ ਹੁੰਦਾ ਹੈ, ਰੀਜ਼ਨਿੰਗ ਅਤੇ ਟੂਲ-ਕਾਲ ਈਵੈਂਟ ਸਟ੍ਰੀਮ
- **ਕੰਟੈਕਸਟ ਬਲੋਆਉਟ**: ਹਰ ਪ੍ਰੋਵਾਈਡਰ ਮੁਤਾਬਕ ਵਿੰਡੋ ਦਾ ਆਕਾਰ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਜ਼ਬਰਦਸਤੀ ਓਵਰਫਲੋ, ਨਾਲ ਹੀ ਹਰ ਰਨਟਾਈਮ ਲਈ ਇਹ ਨਕਸ਼ਾ ਕਿ ਅਸੀਂ *ਕੀ ਨਹੀਂ* ਦੇਖ ਸਕਦੇ ([ਕਿਵੇਂ](docs/CONTEXT_BLOWOUT.md))
- **ਮੈਮਰੀ ਅਤੇ ਸਕਿੱਲਸ**: ਉਹ ਫਾਈਲਾਂ ਅਤੇ ਸਕਿੱਲਸ ਜੋ ਹਰ ਰਨਟਾਈਮ ਨੇ ਅਸਲ ਵਿੱਚ ਲੋਡ ਕੀਤੇ
- **ਸਿਹਤ ਅਤੇ ਲੌਗ**: ਡਿਸਕ, ਮੈਮਰੀ, ਗਲਤੀ ਦਰਾਂ, ਰੇਟ ਲਿਮਿਟ, ਲਾਈਵ ਲੌਗ ਸਟ੍ਰੀਮ
- **ਅਲਰਟ**: ਬਜਟ ਕੈਪ, ਐਰਰ ਸਪਾਈਕ, ਏਜੰਟ-ਔਫਲਾਈਨ, Slack, Discord, PagerDuty, Telegram, ਈਮੇਲ ਵੱਲ ਭੇਜੇ ਜਾਂਦੇ
- **ਅਪਰੂਵਲਸ**: ਜੋਖਮ ਭਰੀਆਂ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਚੱਲਣ ਤੋਂ *ਪਹਿਲਾਂ* ਰੋਕੋ ਅਤੇ ਆਪਣੇ ਫੋਨ ਤੋਂ ਪ੍ਰਵਾਨਗੀ ਦਿਓ ([ਕਿਵੇਂ](docs/APPROVALS.md))

## ਕੰਟੈਕਸਟ ਬਲੋਆਉਟ, ਅਤੇ ਨਿਗਰਾਨੀ ਦੀ ਲਾਗਤ

ਕਿਸੇ ਵੀ ਏਜੰਟ-ਤੁਲਨਾ ਟੂਲ 'ਤੇ ਭਰੋਸਾ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਜਵਾਬ ਦੇਣ ਯੋਗ ਦੋ ਸਵਾਲ।

**ਇਹ ਰਨਟਾਈਮਾਂ ਵਿੱਚ ਕੰਟੈਕਸਟ-ਵਿੰਡੋ ਬਲੋਆਉਟ ਨੂੰ ਕਿਵੇਂ ਸੰਭਾਲਦਾ ਹੈ?**

ਯੂਟੀਲਾਈਜ਼ੇਸ਼ਨ ਪ੍ਰਤੀਸ਼ਤ ਓਨੀ ਹੀ ਇਮਾਨਦਾਰ ਹੁੰਦੀ ਹੈ ਜਿੰਨੀ ਉਸ ਸੰਖਿਆ ਦੀ ਜਿਸ ਨਾਲ ਇਹ ਭਾਗ ਕਰਦੀ ਹੈ। ClawMetry ਹਰ ਪ੍ਰੋਵਾਈਡਰ ਲਈ ਵਿੰਡੋ ਦਾ ਆਕਾਰ [ਇੱਕ ਟੇਬਲ](clawmetry/context_windows.py) ਤੋਂ ਲੈਂਦਾ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਪੜ੍ਹ ਸਕਦੇ ਹੋ ਅਤੇ PR ਕਰ ਸਕਦੇ ਹੋ, ਜੋ Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama ਅਤੇ GLM ਨੂੰ ਕਵਰ ਕਰਦਾ ਹੈ। ਇਹ ਸਾਰੇ 26 ਰਨਟਾਈਮਾਂ ਨੂੰ ਇੱਕੋ ਵੈਂਡਰ ਦੇ ਸਕੇਲ ਨਾਲ ਨਹੀਂ ਮਾਪਦਾ। ਇਹ ਮਾਇਨੇ ਰੱਖਦਾ ਹੈ: Anthropic ਦੇ 200K ਦੇ ਖਿਲਾਫ਼ ਗਿਣਿਆ ਗਿਆ 300K GPT-5 ਟਰਨ ">100%, ਬਲੋਨ" ਪੜ੍ਹਿਆ ਜਾਂਦਾ ਹੈ ਜਦੋਂ ਕਿ ਇਹ ਅਸਲ ਵਿੱਚ GPT-5 ਦੇ 400K ਦਾ 75% ਹੈ। ਇਹੀ ਸਕੇਲ ਇੱਕ ਸੱਚਮੁੱਚ ਓਵਰਫਲੋ ਹੋਏ 130K DeepSeek ਟਰਨ ਨੂੰ ਇੱਕ ਆਰਾਮਦਾਇਕ 65% ਵਜੋਂ ਲੁਕਾਉਂਦਾ ਹੈ।

ਹਰ ਵਿੰਡੋ ਆਪਣੇ ਸਰੋਤ ਸਮੇਤ ਭੇਜੀ ਜਾਂਦੀ ਹੈ: `model_table`, `explicit_marker`, `observed_floor`, ਜਾਂ ਜਦੋਂ ਸਾਨੂੰ ਮਾਡਲ ਪਤਾ ਨਹੀਂ ਹੁੰਦਾ ਤਾਂ ਇੱਕ ਇਮਾਨਦਾਰ `default`। ਇੱਕ ਅੰਦਾਜ਼ੇ 'ਤੇ ਬਣਿਆ ਗੇਜ ਕਦੇ ਵੀ ਲੁਕਅੱਪ 'ਤੇ ਬਣੇ ਗੇਜ ਵਾਂਗ ਭਰੋਸੇਯੋਗ ਨਹੀਂ ਦਿਖਦਾ।

ClawMetry ਸਿਰਫ਼ ਕੁਝ ਰਨਟਾਈਮਾਂ 'ਤੇ ਹੀ ਕੰਪੈਕਸ਼ਨ ਈਵੈਂਟ ਦੇਖ ਸਕਦਾ ਹੈ। ਇਸ ਲਈ `GET /api/context-coverage` ਹਰ ਰਨਟਾਈਮ ਲਈ ਦੱਸਦਾ ਹੈ ਕਿ ਕੀ **ਜ਼ੀਰੋ ਦਾ ਮਤਲਬ ਹੈ "ਸਾਫ਼ ਚੱਲਿਆ" ਜਾਂ "ਸਾਨੂੰ ਦਿਖਦਾ ਨਹੀਂ"**। ਜਿਹੜਾ `0` ਅਸਲ ਵਿੱਚ ਅੰਨ੍ਹੇਪਣ ਦਾ ਮਤਲਬ ਰੱਖਦਾ ਹੈ, ਉਹ ਇਹ ਦੱਸਦਾ ਹੈ। [ਪੂਰੀ ਜਾਣਕਾਰੀ](docs/CONTEXT_BLOWOUT.md)

**ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਕੀਮਤ ਕੀ ਹੈ?**

| ਪਾਥ | ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਜੋੜਿਆ ਗਿਆ | ਡਿਫੌਲਟ? |
|---|---|---|
| ਸੈਸ਼ਨ-ਫਾਈਲ ਟੇਲਿੰਗ (ਸਾਰੇ 30 ਰਨਟਾਈਮ) | **0**। ਵੱਖਰੀ ਪ੍ਰਕਿਰਿਆ, ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਕੋਈ ClawMetry ਕੋਡ ਨਹੀਂ | ਚਾਲੂ |
| HTTP ਇੰਟਰਸੈਪਟਰ (`CLAWMETRY_INTERCEPT=1`) | ਹਰ LLM ਕਾਲ 'ਤੇ **+0.44 ms**, ਜਾਂ 5s ਕਾਲ ਦਾ 0.009% | ਬੰਦ |
| ਪ੍ਰੀ-ਟੂਲ ਹੁੱਕ ਗੇਟ (ਵਾਰਮ ਕੈਸ਼) | ਹਰ ਗੇਟਿਡ ਟੂਲ ਕਾਲ 'ਤੇ **+44 ms**, 36 ms ਇੰਟਰਪ੍ਰੇਟਰ ਫਲੋਰ ਤੋਂ ਉੱਪਰ | ਬੰਦ |
| ਐਨਫੋਰਸਮੈਂਟ ਪ੍ਰੌਕਸੀ | ਹਰ LLM ਕਾਲ 'ਤੇ **+9.7 ms** | ਬੰਦ |

ਡੈਮਨ ਹੋਸਟ ਲਾਗਤ: **2,762 ਈਵੈਂਟ/ਸੈਕਿੰਡ** ਇੰਜੈਸਟ, ਡਿਸਕ 'ਤੇ **710 ਬਾਈਟ/ਈਵੈਂਟ** (100k ਈਵੈਂਟਾਂ ਲਈ 67.7 MB), ਅਤੇ ਇੱਕ ਵਿਅਸਤ ਇੰਸਟਾਲ 'ਤੇ ਲਗਾਤਾਰ **ਇੱਕ ਕੋਰ ਦਾ ~12%**। ਉਹ ਆਖਰੀ ਸੰਖਿਆ ਸਾਡੇ ਖੁਦ ਦੇ ਦੱਸੇ 5-10% ਬਜਟ ਤੋਂ ਵੱਧ ਹੈ, ਇਸ ਲਈ ਇਸਨੂੰ ਪੇਜ ਤੋਂ ਹਟਾਉਣ ਦੀ ਬਜਾਏ ਪਿੱਛਾ ਕਰਨ ਲਈ ਇੱਕ ਬੱਗ ਵਜੋਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਗਿਆ ਹੈ।

Apple M2 Pro 'ਤੇ `benchmarks/overhead.py` ਨਾਲ ਮਾਪਿਆ ਗਿਆ। ਹਾਰਨੈੱਸ ਹਰੇਕ ਸਥਿਤੀ ਨੂੰ ਇੱਕ ਵੱਖਰੀ ਪ੍ਰਕਿਰਿਆ ਵਿੱਚ ਚਲਾਉਂਦਾ ਹੈ, ਉਹਨਾਂ ਦੇ ਕ੍ਰਮ ਨੂੰ ਬਦਲਦਾ ਹੈ, ਅਤੇ **ਜਦੋਂ ਰਾਊਂਡ ਇਸਦੇ ਚਿੰਨ੍ਹ 'ਤੇ ਅਸਹਿਮਤ ਹੁੰਦੇ ਹਨ ਤਾਂ ਸੰਖਿਆ ਛਾਪਣ ਤੋਂ ਇਨਕਾਰ ਕਰਦਾ ਹੈ**। ਇਸਨੂੰ ਆਪਣੀ ਖੁਦ ਦੀ ਮਸ਼ੀਨ 'ਤੇ ਇੱਕ ਮਿੰਟ ਵਿੱਚ ਚਲਾਓ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ਹਰ ਪਾਥ ਮਾਪਿਆ ਗਿਆ ਹੈ, ਹੁੱਕ ਗੇਟਾਂ ਅਤੇ ਐਨਫੋਰਸਮੈਂਟ ਪ੍ਰੌਕਸੀ ਸਮੇਤ, ਅਤੇ ਹਾਰਨੈੱਸ CI ਵਿੱਚ Linux, macOS ਅਤੇ Windows 'ਤੇ ਚੱਲਦਾ ਹੈ। ਜਾਣਨ ਯੋਗ ਦੋ ਨਤੀਜੇ: ਪ੍ਰੌਕਸੀ ਦੀ ਲਾਗਤ Windows 'ਤੇ Linux ਨਾਲੋਂ ਲਗਭਗ ਸੱਤ ਗੁਣਾ ਵੱਧ ਹੈ, ਅਤੇ ਡੈਮਨ ਵਰਤਮਾਨ ਵਿੱਚ ਇੱਕ ਕੋਰ ਦਾ ਲਗਭਗ 12% ਲਗਾਤਾਰ ਵਰਤਦਾ ਹੈ, ਜੋ ਸਾਡੇ ਖੁਦ ਦੇ 5-10% ਬਜਟ ਤੋਂ ਵੱਧ ਹੈ। ਕੱਚਾ JSON, ਵਿਧੀ, ਅਤੇ ਹੁਣ ਤੱਕ ਜੋ ਨਹੀਂ ਮਾਪਿਆ ਗਿਆ ਉਹ [docs/OVERHEAD.md](docs/OVERHEAD.md) ਵਿੱਚ ਹੈ।

## ਕੀਮਤ

| ਪਲਾਨ | ਇਹ ਕੀ ਕਵਰ ਕਰਦਾ ਹੈ | ਕੀਮਤ |
|---|---|---|
| **ਮੁਫ਼ਤ** | OpenClaw + NVIDIA NemoClaw + Goose, ਪੂਰਾ ਡੈਸ਼ਬੋਰਡ, ਸਿਰਫ਼ ਲੋਕਲ | $0 |
| **ਸਟਾਰਟਰ** | ਉੱਪਰ ਦੱਸੇ ਹਰ ਦੂਜੇ ਰਨਟਾਈਮ, ਫਲੀਟ ਵਿਊ, ਕਲਾਊਡ ਸਿੰਕ | $9 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |
| **Pro** | ਸਟਾਰਟਰ + ਕੰਟਰੋਲ ਅਤੇ ਮੁਲਾਂਕਣ: ਅਪਰੂਵਲਸ, ਟੂਲ-ਜੋਖਮ ਨੀਤੀਆਂ, ਈਵਲ, ਅਸੰਗਤੀ ਖੋਜ, ਲਾਗਤ ਓਪਟੀਮਾਈਜ਼ਰ, OTel ਐਕਸਪੋਰਟ, ਛੇੜਛਾੜ-ਸਬੂਤ ਆਡਿਟ ਲੌਗ | $19 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |

ਸਾਲਾਨਾ ਪਲਾਨ, Enterprise ਅਤੇ ਮੌਜੂਦਾ ਸੰਖਿਆਵਾਂ **[clawmetry.com/pricing](https://clawmetry.com/pricing)** 'ਤੇ ਹਨ। ਸੈਲਫ-ਹੋਸਟਿਡ ਲਾਈਸੈਂਸ ਕੁੰਜੀਆਂ ਕਲਾਊਡ ਤੋਂ ਬਿਨਾਂ ਵੀ ਕੰਮ ਕਰਦੀਆਂ ਹਨ (`clawmetry license`)। ਸਹੀ ਮੁਫ਼ਤ/ਪੇਡ ਵੰਡ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਵਿੱਚ ਹੈ।

## ਤੁਹਾਡਾ ਡੇਟਾ ਤੁਹਾਡੀ ਮਸ਼ੀਨ 'ਤੇ ਹੀ ਰਹਿੰਦਾ ਹੈ

ClawMetry ਲੋਕਲ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਅਤੇ ਲੌਗ ਪੜ੍ਹਦਾ ਹੈ। **ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ ਚਲਾਉਂਦੇ, ਕੋਈ ਸੈਸ਼ਨ ਡੇਟਾ ਤੁਹਾਡੇ ਬਾਕਸ ਤੋਂ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦਾ** — ਕੋਈ ਪ੍ਰੌਮਪਟ, ਜਵਾਬ, ਟੂਲ ਆਰਗੂਮੈਂਟ, ਫਾਈਲ ਸਮੱਗਰੀ ਜਾਂ ਲੌਗ ਲਾਈਨ ਨਹੀਂ। ਜਦੋਂ ਤੁਸੀਂ ਕਨੈਕਟ ਕਰਦੇ ਹੋ, ਤਾਂ ਸਨੈਪਸ਼ਾਟ ਨੂੰ ਇੱਕ ਕੁੰਜੀ ਨਾਲ ਐਂਡ-ਟੂ-ਐਂਡ ਐਨਕ੍ਰਿਪਟ ਕੀਤਾ ਜਾਂਦਾ ਹੈ ਜੋ ਕਦੇ ਵੀ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਨਹੀਂ ਛੱਡਦੀ, ਅਤੇ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਡੀਕ੍ਰਿਪਟ ਕੀਤਾ ਜਾਂਦਾ ਹੈ। ਜੇ ਕਿਸੇ ਨੋਡ ਕੋਲ ਕੁੰਜੀ ਨਹੀਂ ਹੈ, ਤਾਂ ਅਪਲੋਡ ਨੂੰ ਸਾਫ਼ ਭੇਜਣ ਦੀ ਬਜਾਏ ਛੱਡ ਦਿੱਤਾ ਜਾਂਦਾ ਹੈ, ਅਤੇ ਕੋਈ ਵੀ ਸਰਵਰ ਜਵਾਬ ਇਸਨੂੰ ਬੰਦ ਨਹੀਂ ਕਰ ਸਕਦਾ।

ਕਨੈਕਟ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਡਿਫੌਲਟ ਤੌਰ 'ਤੇ ਦੋ ਚੀਜ਼ਾਂ ਚੱਲਦੀਆਂ ਹਨ, ਦੋਵੇਂ ਆਪਟ-ਆਊਟ ਅਤੇ ਕੋਈ ਵੀ ਸੈਸ਼ਨ ਡੇਟਾ ਨਹੀਂ ਲਿਜਾਂਦੀਆਂ: ਇੱਕ ਗੁਮਨਾਮ ਇੰਸਟਾਲ ਪਿੰਗ ਅਤੇ PyPI ਦੇ ਖਿਲਾਫ਼ ਇੱਕ ਵਰਜ਼ਨ ਚੈੱਕ। ਇੱਕ ਡਿਫੌਲਟ ਇੰਸਟਾਲ ਸਟਾਰਟਅੱਪ ਬੈਨਰ ਲਾਈਨ ਲਈ ਤੁਹਾਡਾ ਪਬਲਿਕ IP ਵੀ ਇੱਕ ਵਾਰ ਲੱਭਦਾ ਹੈ। ਹਰ ਮੰਜ਼ਿਲ, ਇਹ ਕੀ ਲਿਜਾਂਦੀ ਹੈ ਅਤੇ ਇਸਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰਨਾ ਹੈ, [docs/EGRESS.md](docs/EGRESS.md) ਵਿੱਚ ਸੂਚੀਬੱਧ ਹੈ; ਸੈਲਫ-ਹੋਸਟਿਡ, ਰੀਪੁਆਇੰਟਿਡ ਅਤੇ ਏਅਰ-ਗੈਪਡ ਇੰਸਟਾਲ ਬਿਲਕੁਲ ਕੋਈ ਵੀ ਸਵੈ-ਇੱਛਤ ਬਾਹਰੀ ਕਾਲ ਨਹੀਂ ਕਰਦੇ।

ਡੀਕ੍ਰਿਪਸ਼ਨ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਹੁੰਦੀ ਹੈ, ਉਸ ਕੋਡ ਵਿੱਚ ਜੋ ਅਸੀਂ ਤੁਹਾਨੂੰ ਦਿੰਦੇ ਹਾਂ। ਇਹ ਪਹਿਲਾਂ ਇੱਕ ਵਾਅਦਾ ਸੀ; ਹੁਣ ਇਹ ਅਜਿਹੀ ਚੀਜ਼ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਜਾਂਚ ਸਕਦੇ ਹੋ। ਹਰ ਲਾਈਨ ਜੋ ਤੁਹਾਡੀ ਕੁੰਜੀ ਨੂੰ ਛੂੰਹਦੀ ਹੈ, ਇੱਕ ਪੜ੍ਹਨਯੋਗ ਫਾਈਲ ਵਿੱਚ ਰਹਿੰਦੀ ਹੈ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ਜੋ ਵ੍ਹੀਲ ਦੇ ਅੰਦਰ ਭੇਜੀ ਜਾਂਦੀ ਹੈ ਅਤੇ ਸ਼ਬਦ-ਦਰ-ਸ਼ਬਦ ਸਰਵ ਕੀਤੀ ਜਾਂਦੀ ਹੈ, ਇੱਕ Subresource Integrity ਹੈਸ਼ ਨਾਲ ਪਿੰਨ ਕੀਤੀ ਗਈ। ਇਹ ਪੁਸ਼ਟੀ ਕਰਨ ਲਈ ਕਿ ਬ੍ਰਾਊਜ਼ਰ ਉਹੀ ਚਲਾਉਂਦਾ ਹੈ ਜੋ ਅਸੀਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ਇਹ ਕੀ ਸਾਬਤ ਨਹੀਂ ਕਰਦਾ: ਅਸੀਂ ਉਹ ਪੇਜ ਸਰਵ ਕਰਦੇ ਹਾਂ ਜੋ ਫਾਈਲ ਲੋਡ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ ਅਸੀਂ ਇੱਕ ਵੱਖਰਾ ਪੇਜ ਸਰਵ ਕਰ ਸਕਦੇ ਹਾਂ। ਇੰਟੈਗ੍ਰਿਟੀ ਹੈਸ਼ ਤੁਹਾਨੂੰ ਇੱਕ ਖ਼ਰਾਬ CDN ਤੋਂ ਬਚਾਉਂਦੇ ਹਨ, ਵੈਂਡਰ ਤੋਂ ਨਹੀਂ। ਤੁਹਾਨੂੰ ਜੋ ਮਿਲਦਾ ਹੈ ਉਹ ਇਹ ਹੈ ਕਿ ਕਿਸੇ ਵੀ ਬਦਲਾਅ ਨੂੰ ਜਾਣਬੁੱਝ ਕੇ, ਪੇਜ ਸੋਰਸ ਵਿੱਚ ਦਿਖਣਯੋਗ, ਅਤੇ PyPI 'ਤੇ ਮੌਜੂਦ ਕਿਸੇ ਵੀ ਵਿਅਕਤੀ ਦੁਆਰਾ ਪ੍ਰਾਪਤ ਕੀਤੇ ਜਾ ਸਕਣ ਵਾਲੇ ਆਰਟੀਫੈਕਟ ਤੋਂ ਵੱਖਰਾ ਹੋਣਾ ਪੈਂਦਾ ਹੈ। ਸੈਲਫ-ਹੋਸਟਿੰਗ ਜਾਂ ਸਿਰਫ਼ ਲੋਕਲ ਰਹਿਣਾ ਇਸ ਨਿਰਭਰਤਾ ਨੂੰ ਪੂਰੀ ਤਰ੍ਹਾਂ ਹਟਾ ਦਿੰਦਾ ਹੈ।

## ਇੰਸਟਾਲ

```bash
pip install clawmetry     # ਫਿਰ: clawmetry
```

ਜਾਂ ਇੱਕ-ਲਾਈਨਰ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ਜਾਂ Windows 'ਤੇ Python 3.8+ ਦੀ ਲੋੜ ਹੈ, ਅਤੇ ਉਸੇ ਮਸ਼ੀਨ 'ਤੇ ਘੱਟੋ-ਘੱਟ ਇੱਕ ਏਜੰਟ ਰਨਟਾਈਮ। Docker ਹਦਾਇਤਾਂ: [docs/DOCKER.md](docs/DOCKER.md)।

## ਦਸਤਾਵੇਜ਼

| | |
|---|---|
| [ਰਨਟਾਈਮ ਅਨੁਕੂਲਤਾ](docs/compatibility.md) | ਹਰ ਅਡੈਪਟਰ ਕੀ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਇੱਕ ਰਨਟਾਈਮ ਕਿਵੇਂ ਜੋੜਿਆ ਜਾਵੇ |
| [ਕੰਟੈਕਸਟ ਬਲੋਆਉਟ](docs/CONTEXT_BLOWOUT.md) | ਹਰ-ਪ੍ਰੋਵਾਈਡਰ ਵਿੰਡੋ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਓਵਰਫਲੋ, ਹਰ-ਰਨਟਾਈਮ ਕਵਰੇਜ |
| [ਓਵਰਹੈੱਡ](docs/OVERHEAD.md) | ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਮਾਪੀ ਗਈ ਕੀਮਤ, ਇਸਨੂੰ ਦੁਬਾਰਾ ਪੈਦਾ ਕਰਨ ਲਈ ਹਾਰਨੈੱਸ ਸਮੇਤ |
| [ਐਨਟਾਈਟਲਮੈਂਟਸ](docs/ENTITLEMENTS.md) | ਮੁਫ਼ਤ ਬਨਾਮ ਪੇਡ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, ਲਾਈਸੈਂਸ CLI |
| [ਅਪਰੂਵਲਸ ਅਤੇ ਨੀਤੀਆਂ](docs/APPROVALS.md) | ਪ੍ਰੀ-ਐਗਜ਼ੀਕਿਊਸ਼ਨ ਗੇਟਿੰਗ, ਜੋਖਮ ਸਕੋਰਿੰਗ, ਫੋਨ ਅਪਰੂਵਲ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ਕਿਤੇ ਵੀ ਟਰੇਸ ਐਕਸਪੋਰਟ ਕਰੋ, ਕਿਸੇ ਵੀ ਥਾਂ ਤੋਂ OTLP ਇੰਜੈਸਟ ਕਰੋ |
| [ਆਪਣਾ ਖੁਦ ਦਾ ਏਜੰਟ ਲਿਆਓ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ਪੂਰੀ ਤਰ੍ਹਾਂ, ਚਲਾਉਣਯੋਗ ਉਦਾਹਰਣਾਂ ਸਮੇਤ |
| [SDK ਟਰੈਕਿੰਗ](docs/SDK_TRACKING.md) | ਤੁਹਾਡੇ ਖੁਦ ਦੇ ਬਣਾਏ ਏਜੰਟਾਂ ਲਈ ਲਾਗਤ ਐਟ੍ਰੀਬਿਊਸ਼ਨ |
| [ਚੈਟ ਚੈਨਲ](docs/CHANNELS.md) | ਫਲੋ ਵਿੱਚ ਦਿਖਾਏ ਗਏ ਚੈਟ ਅਡੈਪਟਰ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ਸੈਂਡਬਾਕਸਡ NVIDIA NemoClaw ਸੈਟਅੱਪ |
| [Docker](docs/DOCKER.md) | ਇਮੇਜ, ਕੰਪੋਜ਼, ਵਾਲਿਊਮ ਮਾਊਂਟ |
| [ਆਰਕੀਟੈਕਚਰ](ARCHITECTURE.md) · [ਡਿਵੈਲਪਮੈਂਟ](docs/DEVELOPMENT.md) | ਅੰਦਰੋਂ ਇਹ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ; ਸੋਰਸ ਤੋਂ ਚਲਾਉਣਾ |
| [ਟੈਲੀਮੈਟਰੀ](docs/TELEMETRY.md) | ਗੁਮਨਾਮ ਇੰਸਟਾਲ ਅਤੇ ਡੈਸਕਟੌਪ-ਓਪਨ ਪਿੰਗ, ਅਤੇ ਉਹਨਾਂ ਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰਨਾ ਹੈ |

## ਸਕ੍ਰੀਨਸ਼ਾਟ

ਹੇਠਾਂ ਦਿੱਤੀ ਹਰ ਸੰਖਿਆ ਇੱਕ ਅਸਲੀ ਮਸ਼ੀਨ ਤੋਂ ਹੈ, ਸਿਰਫ਼ ਪੜ੍ਹਨਯੋਗ, ਕੁਝ ਵੀ ਬੀਜੇ ਬਿਨਾਂ।

**ਇਹ ਤੁਹਾਨੂੰ ਦੱਸਦਾ ਹੈ ਕਿ ਕੁਝ ਗਲਤ ਕਦੋਂ ਹੈ, ਸਿਰਫ਼ ਕੀ ਹੋਇਆ ਇਹ ਨਹੀਂ।**
ਉੱਪਰ ਦੋ ਅਸੰਗਤੀ ਬੈਨਰ: ਖਰਚਾ ਰੋਜ਼ਾਨਾ ਔਸਤ ਤੋਂ 7 ਗੁਣਾ ਚੱਲ ਰਿਹਾ, ਅਤੇ 4.2 ਗੁਣਾ ਲਾਗਤ ਸਪਾਈਕ। ਉਹਨਾਂ ਦੇ ਹੇਠਾਂ, 667 ਹਾਲੀਆ ਸੈਸ਼ਨਾਂ ਵਿੱਚੋਂ 324 ਵਿੱਚ ਬਰਬਾਦੀ ਦਾ ਸੰਕੇਤ, ਕਾਰਨ ਮੁਤਾਬਕ ਵੰਡਿਆ ਗਿਆ।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ਇਹ ਤੁਹਾਨੂੰ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਹਰ ਵਿੰਡੋ ਵਿੱਚ।**
ਅੱਜ $252.47, ਇਸ ਹਫ਼ਤੇ $513.15, ਇਸ ਮਹੀਨੇ $1,312.92, ਹਰ ਇੱਕ ਦੇ ਪਿੱਛੇ ਦੇ ਟੋਕਨ ਅਤੇ ਤੁਹਾਡੀ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਪਹਿਲਾਂ ਹੀ ਇਸਦਾ ਕਿੰਨਾ ਹਿੱਸਾ ਕਵਰ ਕਰਦੀ ਹੈ, ਸਮੇਤ। ਉਸ ਤੋਂ ਹੇਠਾਂ, ਲਗਭਗ $1,128/ਮਹੀਨਾ ਰਿਕਵਰੇਬਲ ਵਜੋਂ ਸੂਚੀਬੱਧ ਅਤੇ ਕੈਸ਼ ਰੀਯੂਜ਼ ਨਾਲ ਪਹਿਲਾਂ ਹੀ ਬਚਾਏ ਗਏ $17,256/ਮਹੀਨਾ।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ਇਹ ਦਰਸਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਸੁਨੇਹਾ ਜਵਾਬ ਕਿਵੇਂ ਬਣਦਾ ਹੈ।**
ਲਾਈਵ ਫਲੋ ਡਾਇਗ੍ਰਾਮ: ਤੁਸੀਂ, ਉਹ ਚੈਨਲ ਜਿਸ 'ਤੇ ਇਹ ਆਇਆ, ਗੇਟਵੇ, ਹੁਣੇ ਜਵਾਬ ਦੇ ਰਿਹਾ ਮਾਡਲ, ਅਤੇ ਹਰ ਟੂਲ ਜਿਸ ਲਈ ਇਹ ਪਹੁੰਚਿਆ। ਕੰਮ ਅੱਗੇ ਵਧਣ ਦੇ ਨਾਲ ਨੋਡ ਜਗਦੇ ਹਨ।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ਮਸ਼ੀਨ 'ਤੇ ਹਰ ਏਜੰਟ, ਇੱਕ ਟੇਬਲ ਵਿੱਚ।**
ਇਹ ਕੀ ਚਲਾਉਂਦਾ ਹੈ, ਪਿਛਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ਅਤੇ ਇਸਦੇ ਪੂਰੇ ਜੀਵਨ ਕਾਲ ਵਿੱਚ ਇਸਦੀ ਕੀਮਤ ਕੀ ਹੈ, ਇਹ ਆਖਰੀ ਵਾਰ ਕਦੋਂ ਵੇਖਿਆ ਗਿਆ, ਇਸਦਾ ਮਾਲਕ ਕੌਣ ਹੈ, ਅਤੇ ਕੀ ਕੋਈ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਬਿੱਲ ਕਵਰ ਕਰ ਰਹੀ ਹੈ। ਇੱਥੇ 14 ਏਜੰਟ, 3 ਸੈਸ਼ਨ ਕੰਮ ਕਰ ਰਹੇ, 13 ਸ਼ਾਂਤ।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਵਾਰੀ ਦਾ ਸਮਾਂ ਅਤੇ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਟੂਲ-ਦਰ-ਟੂਲ।**
ਇੱਕ ਅਸਲੀ ਸੈਸ਼ਨ ਦੀ ਇੱਕ ਵਾਰੀ: 11.2 ਮਿੰਟਾਂ ਵਿੱਚ 11 ਟੂਲ, $1.16 ਲਈ। ਹਰ Bash ਕਾਲ ਅਤੇ ਮਾਡਲ ਕਾਲ ਨੂੰ ਟਾਈਮਲਾਈਨ 'ਤੇ ਆਪਣੀ ਖੁਦ ਦੀ ਬਾਰ ਮਿਲਦੀ ਹੈ, ਇਸ ਲਈ ਜਿਹੜੀ ਕਮਾਂਡ 4.1 ਮਿੰਟ ਚੱਲੀ ਅਤੇ ਜਿਹੜੀ 226ms ਚੱਲੀ, ਉਹਨਾਂ ਨੂੰ ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਵੱਖ ਪਛਾਣਿਆ ਜਾ ਸਕਦਾ ਹੈ।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ਇਹ ਕੰਮ ਨੂੰ ਗ੍ਰੇਡ ਕਰਦਾ ਹੈ, ਸਿਰਫ਼ ਖਰਚੇ ਨੂੰ ਨਹੀਂ।**
ਇਸ ਹਫ਼ਤੇ A: 54 ਟਾਸਕ ਸਾਫ਼ ਵਾਪਸ ਆਏ, 2 ਮੁਸ਼ਕਲ ਵਾਲਿਆਂ ਦੀ ਕੀਮਤ $48.57 ਪਈ, ਅਤੇ ਜਿਹੜੇ ਰਨ ਜੱਜ ਕਰਨ ਲਈ ਬਹੁਤ ਘੱਟ ਗਤੀਵਿਧੀ ਵਾਲੇ ਸਨ ਉਹਨਾਂ ਨੂੰ ਜਿੱਤ ਵਜੋਂ ਗਿਣਨ ਦੀ ਬਜਾਏ ਗ੍ਰੇਡ ਤੋਂ ਬਾਹਰ ਛੱਡ ਦਿੱਤਾ ਗਿਆ। ਹਰੇਕ ਮੁਸ਼ਕਲ ਰਨ ਆਪਣੇ ਟਰੇਸ ਨਾਲ ਲਿੰਕ ਕਰਦਾ ਹੈ।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਕੰਟੈਕਸਟ ਵਿੰਡੋ ਕਿਉਂ ਭਰਦੀ ਰਹਿੰਦੀ ਹੈ।**
ਆਖਰੀ ਵਾਰੀ 'ਤੇ 1M-ਟੋਕਨ ਵਿੰਡੋ ਵਿੱਚੋਂ 715K, 83.3% ਦੀ ਸਿਖਰ, 4 ਕੰਪੈਕਸ਼ਨ ਜੋ ਸਾਰੀਆਂ ਓਵਰਫਲੋ 'ਤੇ ਨਹੀਂ ਸਗੋਂ ਪ੍ਰੋਐਕਟਿਵ ਤੌਰ 'ਤੇ ਚੱਲੀਆਂ, ਨਾਲ ਹੀ ਇਸਦੇ ਪਿੱਛੇ ਹਰ ਵਾਰੀ ਦੀ ਯੂਟੀਲਾਈਜ਼ੇਸ਼ਨ।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ਪਛਾਣ ਤੁਹਾਡੇ ਕੁਝ ਵੀ ਕੌਂਫਿਗਰ ਕੀਤੇ ਬਿਨਾਂ ਚੱਲਦੀ ਹੈ।**
ਬਿਲਟ-ਇਨ ਡਿਟੈਕਟਰ ਇੰਸਟਾਲ ਤੋਂ ਹੀ ਚਾਲੂ ਹਨ: ਏਜੰਟ ਚੁੱਪ ਹੋ ਗਿਆ, ਟੈਲੀਮੈਟਰੀ ਫੀਡ ਬੰਦ ਹੋ ਗਈ, ਲਾਗਤ ਸਪਾਈਕ, ਟੋਕਨ ਬਰਸਟ, ਗਲਤੀਆਂ ਵਧ ਰਹੀਆਂ, ਐਰਰ ਸਪਾਈਕ, ਬਜਟ ਥ੍ਰੈਸ਼ਹੋਲਡ, ਥ੍ਰੈਟ ਸਿਗਨੇਚਰ ਮੇਲ ਖਾਧਾ, ਸਿਕਿਓਰਿਟੀ ਟੂਲ ਫਾਈਂਡਿੰਗ, ਸਿਕਿਓਰਿਟੀ ਪੋਸਚਰ ਬਦਲਿਆ। ਤੁਹਾਡੇ ਖੁਦ ਦੇ ਨਿਯਮ ਇਸ ਉੱਤੇ ਵਿਕਲਪਿਕ ਹਨ।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ਜੋਖਮ ਭਰੀ ਕਾਲ ਨੂੰ ਰੋਕਣਾ ਆਪਟ-ਇਨ ਹੈ, ਅਤੇ ਬੰਦ ਭੇਜਿਆ ਜਾਂਦਾ ਹੈ।**
ਰੀਕਰਸਿਵ ਡਿਲੀਟ, ਫੋਰਸ ਪੁਸ਼, sudo, ਸੀਕ੍ਰੇਟ, ਪੈਕੇਜ ਇੰਸਟਾਲ ਅਤੇ ਬਾਹਰੀ ਕਾਲਾਂ ਨੂੰ ਹਰੇਕ ਨੂੰ ਇੱਕ ਨਿਯਮ ਮਿਲਦਾ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਚਾਲੂ ਕਰ ਸਕਦੇ ਹੋ। ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ ਇਹ ਨਹੀਂ ਕਰਦੇ, ClawMetry ਦੇਖਦਾ ਹੈ ਅਤੇ ਕੁਝ ਨਹੀਂ ਬਦਲਦਾ। ਇੱਕ ਵਾਰ ਚਾਲੂ ਹੋ ਜਾਣ 'ਤੇ, ਮੇਲ ਖਾਂਦੀਆਂ ਕਾਲਾਂ ਇੱਥੇ (ਜਾਂ ਤੁਹਾਡੇ ਫੋਨ 'ਤੇ) ਪ੍ਰਵਾਨਗੀ ਜਾਂ ਇਨਕਾਰ ਲਈ ਉਡੀਕ ਕਰਦੀਆਂ ਹਨ।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ਹੋਰ, ਹਰ ਰਨਟਾਈਮ ਮੁਤਾਬਕ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## ਸਟਾਰ ਇਤਿਹਾਸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ਲਾਈਸੈਂਸ

MIT · [@vivekchand](https://github.com/vivekchand) ਦੁਆਰਾ ਬਣਾਇਆ ਗਿਆ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
