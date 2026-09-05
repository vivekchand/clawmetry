<!-- i18n-src:88be2deff5d5 -->
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

**ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦੇ ਵੇਖੋ।** **30 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਲਈ ਰੀਅਲ-ਟਾਈਮ ਓਬਜ਼ਰਵੇਬਿਲਿਟੀ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ਅਤੇ 26 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਹੀ ਡੈਸ਼ਬੋਰਡ।

> 🌐 **ਇਹ ਇਹਨਾਂ ਭਾਸ਼ਾਵਾਂ ਵਿੱਚ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕਾਨਫ਼ਿਗ। ਸਭ ਕੁਝ ਆਪਣੇ ਆਪ ਪਛਾਣ ਲੈਂਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 'ਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ। ਜ਼ੀਰੋ ਕਾਨਫ਼ਿਗ: ਇਹ ਉਹਨਾਂ ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨੂੰ ਲੱਭ ਲੈਂਦਾ ਹੈ ਜੋ ਤੁਹਾਡੇ ਕੋਲ ਪਹਿਲਾਂ ਹੀ ਹਨ, ਉਹਨਾਂ ਨੂੰ ਸਿਰਫ਼ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਇਹ ਕਿਵੇਂ ਚੱਲਦੇ ਹਨ ਇਸ ਬਾਰੇ ਕੁਝ ਨਹੀਂ ਬਦਲਦਾ।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

**ਓਪਨ ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ਭੁਗਤਾਨ ਵਾਲੀ ਯੋਜਨਾ 'ਤੇ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ਹਰੇਕ ਰਨਟਾਈਮ ਨੂੰ ਇੱਕੋ ਜਿਹਾ ਡੈਸ਼ਬੋਰਡ ਮਿਲਦਾ ਹੈ। ਇੱਕੋ ਸਮੇਂ ਕਈ ਚਲਾਓ ਅਤੇ ਹੈਡਰ ਸਵਿੱਚਰ ਹਰੇਕ ਟੈਬ ਨੂੰ ਉਹਨਾਂ ਵਿੱਚੋਂ ਕਿਸੇ ਇੱਕ ਲਈ ਮੁੜ-ਸਕੋਪ ਕਰ ਦਿੰਦਾ ਹੈ।

SDK ਨਾਲ ਆਪਣਾ ਖੁਦ ਦਾ ਏਜੰਟ ਬਣਾਇਆ ਹੈ? ਇੰਟਰਸੈਪਟਰ ਇਸਦੇ LLM ਕਾਲਾਂ ਨੂੰ ਵੀ ਟਰੈਕ ਕਰਦਾ ਹੈ। ਵੇਖੋ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **ਸੈਸ਼ਨ ਅਤੇ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ**: ਹਰੇਕ ਏਜੰਟ ਨੇ ਕੀ ਕੀਤਾ, ਵਾਰੀ-ਵਾਰੀ, ਰੀਪਲੇ ਨਾਲ
- **ਲਾਗਤ ਅਤੇ ਟੋਕਨ**: ਰਨਟਾਈਮ, ਮਾਡਲ, ਸੈਸ਼ਨ ਅਤੇ ਦਿਨ ਪ੍ਰਤੀ, ਅਨਿਯਮਿਤਤਾ ਦੇ ਨਿਸ਼ਾਨਾਂ ਨਾਲ
- **ਫਲੋ**: ਚੈਨਲਾਂ, ਮਾਡਲਾਂ ਅਤੇ ਟੂਲਾਂ ਵਿੱਚੋਂ ਲੰਘਦੇ ਸੁਨੇਹਿਆਂ ਦਾ ਲਾਈਵ ਚਿੱਤਰ
- **ਬ੍ਰੇਨ**: ਜਿਵੇਂ-ਜਿਵੇਂ ਹੁੰਦਾ ਹੈ, ਤਰਕ ਅਤੇ ਟੂਲ-ਕਾਲ ਈਵੈਂਟ ਸਟ੍ਰੀਮ
- **ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ**: ਹਰੇਕ ਪ੍ਰੋਵਾਈਡਰ ਮੁਤਾਬਕ ਵਿੰਡੋ ਵਰਤੋਂ ਦਾ ਆਕਾਰ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਜ਼ਬਰਦਸਤੀ ਓਵਰਫਲੋ, ਨਾਲ ਹੀ ਹਰੇਕ ਰਨਟਾਈਮ ਲਈ ਇਹ ਨਕਸ਼ਾ ਕਿ ਅਸੀਂ *ਕੀ ਨਹੀਂ* ਦੇਖ ਸਕਦੇ ([ਕਿਵੇਂ](docs/CONTEXT_BLOWOUT.md))
- **ਮੈਮਰੀ ਅਤੇ ਸਕਿੱਲਾਂ**: ਹਰੇਕ ਰਨਟਾਈਮ ਨੇ ਅਸਲ ਵਿੱਚ ਕਿਹੜੀਆਂ ਫ਼ਾਈਲਾਂ ਅਤੇ ਸਕਿੱਲਾਂ ਲੋਡ ਕੀਤੀਆਂ
- **ਸਿਹਤ ਅਤੇ ਲਾਗ**: ਡਿਸਕ, ਮੈਮਰੀ, ਗਲਤੀ ਦਰਾਂ, ਰੇਟ ਲਿਮਿਟਾਂ, ਲਾਈਵ ਲਾਗ ਸਟ੍ਰੀਮ
- **ਅਲਰਟ**: ਬਜਟ ਕੈਪ, ਗਲਤੀ ਵਾਧੇ, ਏਜੰਟ-ਆਫ਼ਲਾਈਨ, Slack, Discord, PagerDuty, Telegram, Email ਨੂੰ ਭੇਜੇ ਜਾਂਦੇ
- **ਮਨਜ਼ੂਰੀਆਂ**: ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਚੱਲਣ ਤੋਂ *ਪਹਿਲਾਂ* ਰੋਕੋ ਅਤੇ ਆਪਣੇ ਫੋਨ ਤੋਂ ਮਨਜ਼ੂਰ ਕਰੋ ([ਕਿਵੇਂ](docs/APPROVALS.md))

## ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ, ਅਤੇ ਨਿਗਰਾਨੀ ਦੀ ਕੀਮਤ

ਕਿਸੇ ਵੀ ਏਜੰਟ-ਤੁਲਨਾ ਟੂਲ 'ਤੇ ਭਰੋਸਾ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਜਵਾਬ ਦੇਣ ਯੋਗ ਦੋ ਸਵਾਲ।

**ਇਹ ਰਨਟਾਈਮਾਂ ਵਿੱਚ ਕੌਂਟੈਕਸਟ-ਵਿੰਡੋ ਬਲੋਆਊਟ ਨੂੰ ਕਿਵੇਂ ਸੰਭਾਲਦਾ ਹੈ?**

ਵਰਤੋਂ ਦੀ ਪ੍ਰਤੀਸ਼ਤਤਾ ਓਨੀ ਹੀ ਇਮਾਨਦਾਰ ਹੁੰਦੀ ਹੈ ਜਿੰਨਾ ਉਹ ਅੰਕੜਾ ਜਿਸ ਨਾਲ ਇਸਨੂੰ ਵੰਡਿਆ ਜਾਂਦਾ ਹੈ। ClawMetry [ਇੱਕ ਟੇਬਲ](clawmetry/context_windows.py) ਤੋਂ ਹਰੇਕ ਪ੍ਰੋਵਾਈਡਰ ਮੁਤਾਬਕ ਵਿੰਡੋ ਦਾ ਆਕਾਰ ਤੈਅ ਕਰਦਾ ਹੈ, ਜਿਸਨੂੰ ਤੁਸੀਂ ਪੜ੍ਹ ਸਕਦੇ ਹੋ ਅਤੇ PR ਕਰ ਸਕਦੇ ਹੋ, ਜੋ Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama ਅਤੇ GLM ਨੂੰ ਕਵਰ ਕਰਦਾ ਹੈ। ਇਹ ਸਾਰੇ 30 ਰਨਟਾਈਮਾਂ ਨੂੰ ਇੱਕੋ ਵੈਂਡਰ ਦੇ ਸਕੇਲ ਨਾਲ ਨਹੀਂ ਮਾਪਦਾ। ਇਹ ਮਾਇਨੇ ਰੱਖਦਾ ਹੈ: 300K GPT-5 ਵਾਰੀ ਨੂੰ Anthropic ਦੇ 200K ਦੇ ਖਿਲਾਫ਼ ਸਕੋਰ ਕਰਨ 'ਤੇ ">100%, ਬਲੋਨ" ਪੜ੍ਹਦਾ ਹੈ ਜਦੋਂ ਕਿ ਇਹ ਅਸਲ ਵਿੱਚ GPT-5 ਦੇ 400K ਦਾ 75% ਹੈ। ਇਹੀ ਸਕੇਲ ਇੱਕ ਅਸਲ ਵਿੱਚ ਓਵਰਫਲੋ ਹੋਈ 130K DeepSeek ਵਾਰੀ ਨੂੰ ਇੱਕ ਆਰਾਮਦਾਇਕ 65% ਵਜੋਂ ਲੁਕਾ ਦਿੰਦਾ ਹੈ।

ਹਰੇਕ ਵਿੰਡੋ ਆਪਣੇ ਸਰੋਤ ਨਾਲ ਆਉਂਦੀ ਹੈ: `model_table`, `explicit_marker`, `observed_floor`, ਜਾਂ ਜਦੋਂ ਸਾਨੂੰ ਮਾਡਲ ਦਾ ਪਤਾ ਨਹੀਂ ਹੁੰਦਾ ਤਾਂ ਇੱਕ ਇਮਾਨਦਾਰ `default`। ਅੰਦਾਜ਼ੇ 'ਤੇ ਬਣਿਆ ਗੇਜ ਕਦੇ ਵੀ ਇੱਕ ਲੁੱਕਅੱਪ 'ਤੇ ਬਣੇ ਗੇਜ ਵਾਂਗ ਭਰੋਸੇਯੋਗ ਨਹੀਂ ਦਿਖਦਾ।

ClawMetry ਕੁਝ ਰਨਟਾਈਮਾਂ 'ਤੇ ਹੀ ਕੰਪੈਕਸ਼ਨ ਈਵੈਂਟ ਦੇਖ ਸਕਦਾ ਹੈ। ਇਸ ਲਈ `GET /api/context-coverage` ਹਰੇਕ ਰਨਟਾਈਮ ਲਈ ਦੱਸਦਾ ਹੈ ਕਿ ਕੀ ਇੱਕ **ਜ਼ੀਰੋ ਦਾ ਮਤਲਬ "ਸਾਫ਼ ਚੱਲਿਆ" ਹੈ ਜਾਂ "ਸਾਨੂੰ ਦਿਖਦਾ ਨਹੀਂ"**। ਇੱਕ `0` ਜਿਸਦਾ ਅਸਲ ਵਿੱਚ ਮਤਲਬ ਅੰਨ੍ਹਾ ਹੈ, ਉਹ ਇਹ ਦੱਸਦਾ ਹੈ। [ਪੂਰੀ ਜਾਣਕਾਰੀ](docs/CONTEXT_BLOWOUT.md)

**ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਲਾਗਤ ਕੀ ਹੈ?**

| ਰਾਹ | ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਸ਼ਾਮਲ | ਡਿਫ਼ਾਲਟ? |
|---|---|---|
| ਸੈਸ਼ਨ-ਫ਼ਾਈਲ ਟੇਲਿੰਗ (ਸਾਰੇ 30 ਰਨਟਾਈਮ) | **0**। ਅਲੱਗ ਪ੍ਰੋਸੈੱਸ, ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਕੋਈ ClawMetry ਕੋਡ ਨਹੀਂ | ਚਾਲੂ |
| HTTP ਇੰਟਰਸੈਪਟਰ (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** ਪ੍ਰਤੀ LLM ਕਾਲ, ਜਾਂ 5s ਕਾਲ ਦਾ 0.009% | ਬੰਦ |
| ਪ੍ਰੀ-ਟੂਲ ਹੁੱਕ ਗੇਟ (ਗਰਮ ਕੈਸ਼) | **+44 ms** ਪ੍ਰਤੀ ਗੇਟਿਡ ਟੂਲ ਕਾਲ, 36 ms ਇੰਟਰਪ੍ਰੇਟਰ ਫ਼ਲੋਰ ਤੋਂ ਉੱਪਰ | ਬੰਦ |
| ਇਨਫੋਰਸਮੈਂਟ ਪ੍ਰੌਕਸੀ | **+9.7 ms** ਪ੍ਰਤੀ LLM ਕਾਲ | ਬੰਦ |

ਡੀਮਨ ਹੋਸਟ ਲਾਗਤ: **2,762 ਈਵੈਂਟ/ਸੈਕਿੰਡ** ਇੰਜੈਸਟ, ਡਿਸਕ 'ਤੇ **710 ਬਾਈਟ/ਈਵੈਂਟ** (100k ਈਵੈਂਟਾਂ ਪ੍ਰਤੀ 67.7 MB), ਅਤੇ ਇੱਕ ਵਿਅਸਤ ਇੰਸਟਾਲ 'ਤੇ **ਲਗਾਤਾਰ ਇੱਕ ਕੋਰ ਦਾ ~12%**। ਉਹ ਆਖ਼ਰੀ ਅੰਕੜਾ ਸਾਡੇ ਆਪਣੇ ਦੱਸੇ 5-10% ਬਜਟ ਤੋਂ ਵੱਧ ਹੈ, ਇਸ ਲਈ ਇਸਨੂੰ ਪੰਨੇ ਤੋਂ ਹਟਾਉਣ ਦੀ ਬਜਾਏ ਪਿੱਛਾ ਕਰਨ ਵਾਲੇ ਇੱਕ ਬੱਗ ਵਜੋਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਗਿਆ ਹੈ।

Apple M2 Pro 'ਤੇ `benchmarks/overhead.py` ਨਾਲ ਮਾਪਿਆ ਗਿਆ। ਹਾਰਨੈੱਸ ਹਰੇਕ ਸਥਿਤੀ ਨੂੰ ਇੱਕ ਵੱਖਰੇ ਪ੍ਰੋਸੈੱਸ ਵਿੱਚ ਚਲਾਉਂਦਾ ਹੈ, ਉਹਨਾਂ ਦੇ ਕ੍ਰਮ ਨੂੰ ਬਦਲਦਾ ਹੈ, ਅਤੇ **ਜਦੋਂ ਗੇੜ ਇਸਦੇ ਚਿੰਨ੍ਹ 'ਤੇ ਅਸਹਿਮਤ ਹੁੰਦੇ ਹਨ ਤਾਂ ਅੰਕੜਾ ਛਾਪਣ ਤੋਂ ਇਨਕਾਰ ਕਰਦਾ ਹੈ**। ਇਸਨੂੰ ਆਪਣੀ ਖੁਦ ਦੀ ਮਸ਼ੀਨ 'ਤੇ ਇੱਕ ਮਿੰਟ ਵਿੱਚ ਚਲਾਓ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ਹਰ ਰਾਹ ਮਾਪਿਆ ਗਿਆ ਹੈ, ਹੁੱਕ ਗੇਟਾਂ ਅਤੇ ਇਨਫੋਰਸਮੈਂਟ ਪ੍ਰੌਕਸੀ ਸਮੇਤ, ਅਤੇ ਹਾਰਨੈੱਸ CI ਵਿੱਚ Linux, macOS ਅਤੇ Windows 'ਤੇ ਚੱਲਦਾ ਹੈ। ਜਾਣਨ ਯੋਗ ਦੋ ਨਤੀਜੇ: Windows 'ਤੇ ਪ੍ਰੌਕਸੀ ਦੀ ਲਾਗਤ Linux ਨਾਲੋਂ ਲਗਭਗ ਸੱਤ ਗੁਣਾ ਵੱਧ ਹੈ, ਅਤੇ ਡੀਮਨ ਇਸ ਵੇਲੇ ਇੱਕ ਕੋਰ ਦਾ ਲਗਭਗ 12% ਬਰਕਰਾਰ ਰੱਖਦਾ ਹੈ, ਜੋ ਸਾਡੇ ਆਪਣੇ 5-10% ਬਜਟ ਤੋਂ ਵੱਧ ਹੈ। ਕੱਚਾ JSON, ਵਿਧੀ, ਅਤੇ ਹਾਲੇ ਕੀ ਨਹੀਂ ਮਾਪਿਆ ਗਿਆ, ਇਹ ਸਭ [docs/OVERHEAD.md](docs/OVERHEAD.md) ਵਿੱਚ ਹੈ।

## ਕੀਮਤ

| ਯੋਜਨਾ | ਕੀ ਕਵਰ ਹੁੰਦਾ ਹੈ | ਕੀਮਤ |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, ਪੂਰਾ ਡੈਸ਼ਬੋਰਡ, ਸਿਰਫ਼ ਲੋਕਲ | $0 |
| **Starter** | ਉੱਪਰ ਦਿੱਤਾ ਹਰੇਕ ਹੋਰ ਰਨਟਾਈਮ, ਫਲੀਟ ਵਿਊ, ਕਲਾਊਡ ਸਿੰਕ | $9 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |
| **Pro** | Starter + ਕੰਟਰੋਲ ਅਤੇ ਮੁਲਾਂਕਣ: ਮਨਜ਼ੂਰੀਆਂ, ਟੂਲ-ਜੋਖਮ ਨੀਤੀਆਂ, ਮੁਲਾਂਕਣ, ਅਨਿਯਮਿਤਤਾ ਖੋਜ, ਲਾਗਤ ਅਨੁਕੂਲਕ, OTel ਐਕਸਪੋਰਟ, ਟੈਂਪਰ-ਐਵੀਡੈਂਟ ਆਡਿਟ ਲਾਗ | $19 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |

ਸਲਾਨਾ ਯੋਜਨਾਵਾਂ, Enterprise ਅਤੇ ਮੌਜੂਦਾ ਅੰਕੜੇ **[clawmetry.com/pricing](https://clawmetry.com/pricing)** 'ਤੇ ਮਿਲਦੇ ਹਨ। ਸੈਲਫ਼-ਹੋਸਟਡ ਲਾਇਸੰਸ ਕੁੰਜੀਆਂ ਕਲਾਊਡ ਬਿਨਾਂ ਵੀ ਕੰਮ ਕਰਦੀਆਂ ਹਨ (`clawmetry license`)। ਸਹੀ ਮੁਫ਼ਤ/ਭੁਗਤਾਨ ਵੰਡ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਵਿੱਚ ਹੈ।

## ਤੁਹਾਡਾ ਡਾਟਾ ਤੁਹਾਡੀ ਮਸ਼ੀਨ 'ਤੇ ਹੀ ਰਹਿੰਦਾ ਹੈ

ClawMetry ਲੋਕਲ ਸੈਸ਼ਨ ਫ਼ਾਈਲਾਂ ਅਤੇ ਲਾਗ ਪੜ੍ਹਦਾ ਹੈ। **ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ ਚਲਾਉਂਦੇ, ਕੋਈ ਵੀ ਸੈਸ਼ਨ ਡਾਟਾ ਤੁਹਾਡੇ ਬਾਕਸ ਤੋਂ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦਾ** — ਕੋਈ ਪ੍ਰੌਂਪਟ, ਜਵਾਬ, ਟੂਲ ਆਰਗਿਊਮੈਂਟ, ਫ਼ਾਈਲ ਸਮੱਗਰੀ ਜਾਂ ਲਾਗ ਲਾਈਨਾਂ ਨਹੀਂ। ਜਦੋਂ ਤੁਸੀਂ ਕਨੈਕਟ ਕਰਦੇ ਹੋ, ਸਨੈਪਸ਼ਾਟ ਇੱਕ ਕੁੰਜੀ ਨਾਲ ਐਂਡ-ਟੂ-ਐਂਡ ਇਨਕ੍ਰਿਪਟਡ ਹੁੰਦਾ ਹੈ ਜੋ ਕਦੇ ਵੀ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦੀ, ਅਤੇ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਡੀਕ੍ਰਿਪਟ ਹੁੰਦਾ ਹੈ। ਜੇ ਕਿਸੇ ਨੋਡ ਕੋਲ ਕੁੰਜੀ ਨਹੀਂ ਹੈ, ਤਾਂ ਅੱਪਲੋਡ ਸਾਫ਼ ਭੇਜੇ ਜਾਣ ਦੀ ਬਜਾਏ ਛੱਡ ਦਿੱਤਾ ਜਾਂਦਾ ਹੈ, ਅਤੇ ਕੋਈ ਵੀ ਸਰਵਰ ਜਵਾਬ ਇਸਨੂੰ ਬੰਦ ਨਹੀਂ ਕਰ ਸਕਦਾ।

ਕਨੈਕਟ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਦੋ ਚੀਜ਼ਾਂ ਡਿਫ਼ਾਲਟ ਵਜੋਂ ਚੱਲਦੀਆਂ ਹਨ, ਦੋਵੇਂ ਔਪਟ-ਆਊਟ ਅਤੇ ਦੋਵਾਂ ਵਿੱਚ ਕੋਈ ਸੈਸ਼ਨ ਡਾਟਾ ਨਹੀਂ: ਇੱਕ ਗੁਮਨਾਮ ਇੰਸਟਾਲ ਪਿੰਗ ਅਤੇ PyPI ਦੇ ਖਿਲਾਫ਼ ਇੱਕ ਵਰਜ਼ਨ ਜਾਂਚ। ਇੱਕ ਡਿਫ਼ਾਲਟ ਇੰਸਟਾਲ ਸਟਾਰਟਅੱਪ ਬੈਨਰ ਲਾਈਨ ਲਈ ਤੁਹਾਡਾ ਪਬਲਿਕ IP ਵੀ ਇੱਕ ਵਾਰ ਲੱਭਦਾ ਹੈ। ਹਰੇਕ ਟਿਕਾਣਾ, ਉਹ ਕੀ ਲੈ ਕੇ ਜਾਂਦਾ ਹੈ ਅਤੇ ਇਸਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰਨਾ ਹੈ, ਇਹ [docs/EGRESS.md](docs/EGRESS.md) ਵਿੱਚ ਸੂਚੀਬੱਧ ਹੈ; ਸੈਲਫ਼-ਹੋਸਟਡ, ਰੀਪੁਆਇੰਟਿਡ ਅਤੇ ਏਅਰ-ਗੈਪਡ ਇੰਸਟਾਲ ਕੋਈ ਵੀ ਸਵੈ-ਇੱਛਤ ਬਾਹਰੀ ਕਾਲ ਨਹੀਂ ਕਰਦੇ।

ਡੀਕ੍ਰਿਪਸ਼ਨ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ, ਸਾਡੇ ਵੱਲੋਂ ਦਿੱਤੇ ਕੋਡ ਵਿੱਚ ਹੁੰਦਾ ਹੈ। ਇਹ ਪਹਿਲਾਂ ਸਿਰਫ਼ ਇੱਕ ਵਾਅਦਾ ਸੀ; ਹੁਣ ਇਹ ਕੁਝ ਅਜਿਹਾ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਜਾਂਚ ਸਕਦੇ ਹੋ। ਹਰ ਲਾਈਨ ਜੋ ਤੁਹਾਡੀ ਕੁੰਜੀ ਨੂੰ ਛੂੰਹਦੀ ਹੈ ਇੱਕ ਪੜ੍ਹਨਯੋਗ ਫ਼ਾਈਲ ਵਿੱਚ ਰਹਿੰਦੀ ਹੈ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ਜੋ wheel ਦੇ ਅੰਦਰ ਸ਼ਾਮਲ ਹੁੰਦੀ ਹੈ ਅਤੇ ਹੂ-ਬਹੂ ਪਰੋਸੀ ਜਾਂਦੀ ਹੈ, ਇੱਕ Subresource Integrity ਹੈਸ਼ ਨਾਲ ਪਿੰਨ ਕੀਤੀ। ਇਹ ਪੁਸ਼ਟੀ ਕਰਨ ਲਈ ਕਿ ਬ੍ਰਾਊਜ਼ਰ ਉਹੀ ਚਲਾਉਂਦਾ ਹੈ ਜੋ ਅਸੀਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਹੈ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ਇਸ ਤੋਂ ਇਹ ਸਾਬਤ ਨਹੀਂ ਹੁੰਦਾ: ਅਸੀਂ ਉਹ ਪੰਨਾ ਪਰੋਸਦੇ ਹਾਂ ਜੋ ਫ਼ਾਈਲ ਲੋਡ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ ਅਸੀਂ ਇੱਕ ਵੱਖਰਾ ਪੰਨਾ ਪਰੋਸ ਸਕਦੇ ਹਾਂ। ਇੰਟੈਗ੍ਰਿਟੀ ਹੈਸ਼ ਤੁਹਾਨੂੰ ਇੱਕ ਸਮਝੌਤਾ ਕੀਤੇ CDN ਤੋਂ ਬਚਾਉਂਦੇ ਹਨ, ਵੈਂਡਰ ਤੋਂ ਨਹੀਂ। ਤੁਹਾਨੂੰ ਜੋ ਮਿਲਦਾ ਹੈ ਉਹ ਇਹ ਹੈ ਕਿ ਕੋਈ ਵੀ ਬਦਲਾਵ ਜਾਣ-ਬੁੱਝ ਕੇ ਹੋਣਾ ਪਵੇਗਾ, ਪੰਨੇ ਦੇ ਸੋਰਸ ਵਿੱਚ ਦਿਖਾਈ ਦੇਵੇਗਾ, ਅਤੇ PyPI 'ਤੇ ਮੌਜੂਦ ਇੱਕ ਆਰਟੀਫੈਕਟ ਤੋਂ ਵੱਖਰਾ ਹੋਵੇਗਾ ਜਿਸਨੂੰ ਕੋਈ ਵੀ ਲਿਆ ਸਕਦਾ ਹੈ। ਸੈਲਫ਼-ਹੋਸਟਿੰਗ ਜਾਂ ਸਿਰਫ਼ ਲੋਕਲ ਰਹਿਣਾ ਇਸ ਨਿਰਭਰਤਾ ਨੂੰ ਪੂਰੀ ਤਰ੍ਹਾਂ ਹਟਾ ਦਿੰਦਾ ਹੈ।

## ਇੰਸਟਾਲ

```bash
pip install clawmetry     # ਫਿਰ: clawmetry
```

ਜਾਂ ਇੱਕ-ਲਾਈਨਰ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ਜਾਂ Windows 'ਤੇ Python 3.8+ ਦੀ ਲੋੜ ਹੈ, ਅਤੇ ਇੱਕੋ ਮਸ਼ੀਨ 'ਤੇ ਘੱਟੋ-ਘੱਟ ਇੱਕ ਏਜੰਟ ਰਨਟਾਈਮ। Docker ਹਦਾਇਤਾਂ: [docs/DOCKER.md](docs/DOCKER.md)।

ਜਾਂ ਏਜੰਟ ਨੂੰ ਤੁਹਾਡੇ ਲਈ ਸੈੱਟ ਅੱਪ ਕਰਨ ਦਿਓ। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) ਸਕਿੱਲ Claude Code, Codex, Cursor, Gemini CLI, Copilot ਜਾਂ OpenCode ਨੂੰ ਸਿਖਾਉਂਦੀ ਹੈ ਕਿ ClawMetry ਨੂੰ ਕਿਵੇਂ ਇੰਸਟਾਲ ਕਰਨਾ ਹੈ, ਮਸ਼ੀਨ 'ਤੇ ਏਜੰਟ ਕੀ ਕਰ ਰਹੇ ਹਨ ਅਤੇ ਖਰਚ ਕਰ ਰਹੇ ਹਨ ਇਸਦੀ ਰਿਪੋਰਟ ਦੇਣੀ ਹੈ, ਬੇਨਤੀ 'ਤੇ ਇੱਕ ਸੈਸ਼ਨ ਰੋਕਣਾ ਹੈ, ਅਤੇ ਮਨਜ਼ੂਰੀ ਲਈ ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਰੋਕ ਕੇ ਰੱਖਣਾ ਹੈ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ਦਸਤਾਵੇਜ਼

| | |
|---|---|
| [ਰਨਟਾਈਮ ਅਨੁਕੂਲਤਾ](docs/compatibility.md) | ਹਰੇਕ ਅਡੈਪਟਰ ਕੀ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਇੱਕ ਰਨਟਾਈਮ ਕਿਵੇਂ ਜੋੜਨਾ ਹੈ |
| [ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ](docs/CONTEXT_BLOWOUT.md) | ਪ੍ਰੋਵਾਈਡਰ-ਦਰ-ਪ੍ਰੋਵਾਈਡਰ ਵਿੰਡੋਜ਼, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਓਵਰਫਲੋ, ਰਨਟਾਈਮ-ਦਰ-ਰਨਟਾਈਮ ਕਵਰੇਜ |
| [ਓਵਰਹੈੱਡ](docs/OVERHEAD.md) | ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਲਾਗਤ ਕੀ ਹੈ, ਮਾਪੀ ਗਈ, ਇਸਨੂੰ ਦੁਹਰਾਉਣ ਲਈ ਹਾਰਨੈੱਸ ਨਾਲ |
| [ਹੱਕਦਾਰੀ](docs/ENTITLEMENTS.md) | ਮੁਫ਼ਤ ਬਨਾਮ ਭੁਗਤਾਨ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, ਲਾਇਸੰਸ CLI |
| [ਮਨਜ਼ੂਰੀਆਂ ਅਤੇ ਨੀਤੀਆਂ](docs/APPROVALS.md) | ਪ੍ਰੀ-ਐਗਜ਼ੀਕਿਊਸ਼ਨ ਗੇਟਿੰਗ, ਜੋਖਮ ਸਕੋਰਿੰਗ, ਫੋਨ ਮਨਜ਼ੂਰੀਆਂ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ਕਿਤੇ ਵੀ ਟਰੇਸ ਐਕਸਪੋਰਟ ਕਰੋ, ਕਿਸੇ ਵੀ ਥਾਂ ਤੋਂ OTLP ਇੰਜੈਸਟ ਕਰੋ |
| [ਆਪਣਾ ਏਜੰਟ ਲਿਆਓ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ਪੂਰੇ ਵਿਸਥਾਰ ਨਾਲ, ਚਲਾਉਣਯੋਗ ਉਦਾਹਰਣਾਂ ਨਾਲ |
| [SDK ਟਰੈਕਿੰਗ](docs/SDK_TRACKING.md) | ਤੁਹਾਡੇ ਖੁਦ ਬਣਾਏ ਏਜੰਟਾਂ ਲਈ ਲਾਗਤ ਵੰਡ |
| [ਚੈਟ ਚੈਨਲ](docs/CHANNELS.md) | ਫਲੋ ਵਿੱਚ ਦਿਖਾਏ ਗਏ ਚੈਟ ਅਡੈਪਟਰ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ਸੈਂਡਬਾਕਸਡ NVIDIA NemoClaw ਸੈੱਟਅੱਪ |
| [Docker](docs/DOCKER.md) | ਇਮੇਜ, ਕੰਪੋਜ਼, ਵਾਲੀਅਮ ਮਾਊਂਟ |
| [ਆਰਕੀਟੈਕਚਰ](ARCHITECTURE.md) · [ਵਿਕਾਸ](docs/DEVELOPMENT.md) | ਇਹ ਅੰਦਰੋਂ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ; ਸੋਰਸ ਤੋਂ ਚਲਾਉਣਾ |
| [ਟੈਲੀਮੈਟਰੀ](docs/TELEMETRY.md) | ਗੁਮਨਾਮ ਇੰਸਟਾਲ ਅਤੇ ਡੈਸਕਟਾਪ-ਓਪਨ ਪਿੰਗ, ਅਤੇ ਉਹਨਾਂ ਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰਨਾ ਹੈ |

## ਸਕਰੀਨਸ਼ਾਟ

ਹੇਠਾਂ ਦਿੱਤਾ ਹਰੇਕ ਅੰਕੜਾ ਇੱਕ ਅਸਲ ਮਸ਼ੀਨ ਤੋਂ ਹੈ, ਸਿਰਫ਼ ਪੜ੍ਹਨ ਲਈ, ਕੁਝ ਵੀ ਬੀਜਿਆ ਨਹੀਂ ਗਿਆ।

**ਇਹ ਤੁਹਾਨੂੰ ਦੱਸਦਾ ਹੈ ਜਦੋਂ ਕੁਝ ਗਲਤ ਹੁੰਦਾ ਹੈ, ਸਿਰਫ਼ ਕੀ ਹੋਇਆ ਇਹ ਹੀ ਨਹੀਂ।**
ਸਿਖਰ 'ਤੇ ਦੋ ਅਨਿਯਮਿਤਤਾ ਬੈਨਰ: ਖਰਚ ਰੋਜ਼ਾਨਾ ਔਸਤ ਦਾ 7x ਚੱਲ ਰਿਹਾ ਹੈ, ਅਤੇ ਇੱਕ 4.2x ਲਾਗਤ ਵਾਧਾ। ਉਹਨਾਂ ਦੇ ਹੇਠਾਂ, 667 ਹਾਲੀਆ ਸੈਸ਼ਨਾਂ ਵਿੱਚੋਂ 324 ਵਿੱਚ ਬਰਬਾਦੀ ਦਾ ਸੰਕੇਤ ਹੈ, ਕਾਰਨ ਮੁਤਾਬਕ ਵੰਡਿਆ।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ਇਹ ਤੁਹਾਨੂੰ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਹਰ ਵਿੰਡੋ ਵਿੱਚ।**
ਅੱਜ $252.47, ਇਸ ਹਫ਼ਤੇ $513.15, ਇਸ ਮਹੀਨੇ $1,312.92, ਹਰੇਕ ਦੇ ਪਿੱਛੇ ਟੋਕਨਾਂ ਸਮੇਤ ਅਤੇ ਤੁਹਾਡੀ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਪਹਿਲਾਂ ਹੀ ਕਿੰਨਾ ਕਵਰ ਕਰਦੀ ਹੈ। ਇਸ ਤੋਂ ਹੇਠਾਂ, ਲਗਭਗ $1,128/ਮਹੀਨਾ ਮੁੜ-ਪ੍ਰਾਪਤ ਕਰਨ ਯੋਗ ਵਜੋਂ ਸੂਚੀਬੱਧ ਅਤੇ ਕੈਸ਼ ਮੁੜ-ਵਰਤੋਂ ਰਾਹੀਂ ਪਹਿਲਾਂ ਹੀ ਬਚਾਏ ਗਏ $17,256/ਮਹੀਨਾ।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ਇਹ ਦਰਸਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਸੁਨੇਹਾ ਜਵਾਬ ਕਿਵੇਂ ਬਣਦਾ ਹੈ।**
ਲਾਈਵ ਫਲੋ ਚਿੱਤਰ: ਤੁਸੀਂ, ਉਹ ਚੈਨਲ ਜਿੱਥੇ ਇਹ ਆਇਆ, ਗੇਟਵੇ, ਹੁਣੇ ਜਵਾਬ ਦੇ ਰਿਹਾ ਮਾਡਲ, ਅਤੇ ਹਰੇਕ ਟੂਲ ਜਿਸ ਤੱਕ ਇਹ ਪਹੁੰਚਿਆ। ਜਿਵੇਂ-ਜਿਵੇਂ ਕੰਮ ਉਹਨਾਂ ਵਿੱਚੋਂ ਲੰਘਦਾ ਹੈ, ਨੋਡ ਜਗਦੇ ਹਨ।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ਮਸ਼ੀਨ 'ਤੇ ਹਰੇਕ ਏਜੰਟ, ਇੱਕ ਹੀ ਟੇਬਲ ਵਿੱਚ।**
ਇਹ ਕੀ ਚਲਾਉਂਦਾ ਹੈ, ਪਿਛਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ਅਤੇ ਆਪਣੀ ਪੂਰੀ ਉਮਰ ਵਿੱਚ ਇਸਦੀ ਲਾਗਤ ਕੀ ਹੈ, ਇਹ ਆਖ਼ਰੀ ਵਾਰ ਕਦੋਂ ਦੇਖਿਆ ਗਿਆ, ਇਸਦਾ ਮਾਲਕ ਕੌਣ ਹੈ, ਅਤੇ ਕੀ ਬਿੱਲ ਨੂੰ ਕੋਈ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਕਵਰ ਕਰ ਰਹੀ ਹੈ। ਇੱਥੇ 14 ਏਜੰਟ, 3 ਸੈਸ਼ਨ ਕੰਮ ਕਰ ਰਹੇ, 13 ਸ਼ਾਂਤ।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਕਿਸੇ ਵਾਰੀ ਦਾ ਸਮਾਂ ਅਤੇ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਟੂਲ-ਦਰ-ਟੂਲ।**
ਇੱਕ ਅਸਲ ਸੈਸ਼ਨ ਦੀ ਇੱਕ ਵਾਰੀ: 11.2 ਮਿੰਟਾਂ ਵਿੱਚ 11 ਟੂਲ, $1.16 ਵਿੱਚ। ਹਰੇਕ Bash ਕਾਲ ਅਤੇ ਮਾਡਲ ਕਾਲ ਨੂੰ ਟਾਈਮਲਾਈਨ 'ਤੇ ਆਪਣੀ ਖੁਦ ਦੀ ਬਾਰ ਮਿਲਦੀ ਹੈ, ਇਸ ਲਈ ਜੋ ਕਮਾਂਡ 4.1 ਮਿੰਟਾਂ ਲਈ ਚੱਲੀ ਅਤੇ ਜੋ 226ms ਲਈ ਚੱਲੀ, ਦੋਵੇਂ ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਵੱਖਰੀਆਂ ਦਿਖਦੀਆਂ ਹਨ।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ਇਹ ਕੰਮ ਨੂੰ ਗਰੇਡ ਕਰਦਾ ਹੈ, ਸਿਰਫ਼ ਖਰਚ ਨੂੰ ਨਹੀਂ।**
ਇਸ ਹਫ਼ਤੇ A: 54 ਕੰਮ ਸਾਫ਼ ਵਾਪਸ ਆਏ, 2 ਖਰਾਬ ਕੰਮਾਂ ਦੀ ਲਾਗਤ $48.57 ਸੀ, ਅਤੇ ਜਿਹੜੇ ਰਨ ਗਰੇਡ ਕਰਨ ਲਈ ਬਹੁਤ ਘੱਟ ਸਰਗਰਮੀ ਵਾਲੇ ਸਨ ਉਹਨਾਂ ਨੂੰ ਜਿੱਤ ਵਜੋਂ ਗਿਣੇ ਜਾਣ ਦੀ ਬਜਾਏ ਬਾਹਰ ਛੱਡ ਦਿੱਤਾ ਗਿਆ। ਹਰੇਕ ਖਰਾਬ ਰਨ ਆਪਣੇ ਟਰੇਸ ਨਾਲ ਜੁੜਿਆ ਹੋਇਆ ਹੈ।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਕੌਂਟੈਕਸਟ ਵਿੰਡੋ ਕਿਉਂ ਲਗਾਤਾਰ ਭਰਦੀ ਰਹਿੰਦੀ ਹੈ।**
ਆਖ਼ਰੀ ਵਾਰੀ ਵਿੱਚ 1M-ਟੋਕਨ ਵਿੰਡੋ ਦੇ 715K, 83.3% ਦਾ ਸਿਖਰ, 4 ਕੰਪੈਕਸ਼ਨ ਜੋ ਸਾਰੇ ਓਵਰਫਲੋ ਦੀ ਬਜਾਏ ਸਰਗਰਮੀ ਨਾਲ ਹੋਏ, ਨਾਲ ਹੀ ਇਸਦੇ ਪਿੱਛੇ ਹਰੇਕ ਵਾਰੀ ਦੀ ਵਰਤੋਂ।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ਖੋਜ ਤੁਹਾਡੇ ਬਿਨਾਂ ਕੁਝ ਕਾਨਫ਼ਿਗਰ ਕੀਤੇ ਚੱਲਦੀ ਹੈ।**
ਬਿਲਟ-ਇਨ ਡਿਟੈਕਟਰ ਇੰਸਟਾਲ ਤੋਂ ਹੀ ਚਾਲੂ ਹਨ: ਏਜੰਟ ਸ਼ਾਂਤ ਹੋ ਗਿਆ, ਟੈਲੀਮੈਟਰੀ ਫੀਡ ਰੁਕ ਗਈ, ਲਾਗਤ ਵਾਧਾ, ਟੋਕਨ ਬਰਸਟ, ਗਲਤੀਆਂ ਵਧ ਰਹੀਆਂ, ਗਲਤੀ ਵਾਧਾ, ਬਜਟ ਹੱਦ, ਧਮਕੀ ਦਸਤਖ਼ਤ ਮਿਲਿਆ, ਸੁਰੱਖਿਆ ਟੂਲ ਖੋਜ, ਸੁਰੱਖਿਆ ਸਥਿਤੀ ਬਦਲੀ। ਤੁਹਾਡੇ ਖੁਦ ਦੇ ਨਿਯਮ ਇਸ ਉੱਪਰ ਵਿਕਲਪਿਕ ਹਨ।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ਖ਼ਤਰਨਾਕ ਕਾਲ ਨੂੰ ਰੋਕਣਾ ਔਪਟ-ਇਨ ਹੈ, ਅਤੇ ਬੰਦ ਭੇਜਿਆ ਜਾਂਦਾ ਹੈ।**
ਰੀਕਰਸਿਵ ਡਿਲੀਟ, ਫੋਰਸ ਪੁਸ਼, sudo, ਸੀਕ੍ਰੇਟ, ਪੈਕੇਜ ਇੰਸਟਾਲ ਅਤੇ ਬਾਹਰੀ ਕਾਲਾਂ ਹਰੇਕ ਨੂੰ ਇੱਕ ਨਿਯਮ ਮਿਲਦਾ ਹੈ ਜੋ ਤੁਸੀਂ ਚਾਲੂ ਕਰ ਸਕਦੇ ਹੋ। ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ ਨਹੀਂ ਕਰਦੇ, ClawMetry ਦੇਖਦਾ ਹੈ ਅਤੇ ਕੁਝ ਨਹੀਂ ਬਦਲਦਾ। ਇੱਕ ਵਾਰ ਚਾਲੂ ਹੋਣ 'ਤੇ, ਮੇਲ ਖਾਂਦੀਆਂ ਕਾਲਾਂ ਇੱਥੇ (ਜਾਂ ਤੁਹਾਡੇ ਫੋਨ 'ਤੇ) ਮਨਜ਼ੂਰੀ ਜਾਂ ਇਨਕਾਰ ਲਈ ਉਡੀਕ ਕਰਦੀਆਂ ਹਨ।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ਹੋਰ, ਹਰੇਕ ਰਨਟਾਈਮ ਲਈ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## ਸਟਾਰ ਇਤਿਹਾਸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ਲਾਇਸੰਸ

MIT · [@vivekchand](https://github.com/vivekchand) ਵੱਲੋਂ ਬਣਾਇਆ ਗਿਆ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
