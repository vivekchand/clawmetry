<!-- i18n-src:d21bea5161e0 -->
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

**ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦਿਆਂ ਦੇਖੋ।** **30 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਲਈ ਰੀਅਲ-ਟਾਈਮ ਆਬਜ਼ਰਵੇਬਿਲਿਟੀ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ਅਤੇ 26 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ।

> 🌐 **ਇਸਨੂੰ ਇਸ ਭਾਸ਼ਾ ਵਿੱਚ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕਾਨਫ਼ਿਗ। ਸਭ ਕੁਝ ਆਪਣੇ-ਆਪ ਲੱਭ ਲੈਂਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 'ਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ। ਜ਼ੀਰੋ ਕਾਨਫ਼ਿਗ: ਇਹ ਉਹ ਏਜੰਟ ਰਨਟਾਈਮ ਲੱਭ ਲੈਂਦਾ ਹੈ
ਜੋ ਤੁਹਾਡੇ ਕੋਲ ਪਹਿਲਾਂ ਹੀ ਹਨ, ਉਹਨਾਂ ਨੂੰ ਸਿਰਫ਼-ਪੜ੍ਹਨ ਲਈ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਉਹਨਾਂ ਦੇ ਚੱਲਣ ਦੇ ਢੰਗ ਵਿੱਚ ਕੁਝ ਵੀ ਨਹੀਂ ਬਦਲਦਾ।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

**ਓਪਨ ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ਭੁਗਤਾਨ ਵਾਲੇ ਪਲਾਨ 'ਤੇ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ਹਰ ਰਨਟਾਈਮ ਨੂੰ ਇੱਕੋ ਡੈਸ਼ਬੋਰਡ ਮਿਲਦਾ ਹੈ। ਇੱਕੋ ਸਮੇਂ ਕਈ ਚਲਾਓ ਅਤੇ ਹੈਡਰ
ਸਵਿੱਚਰ ਹਰ ਟੈਬ ਨੂੰ ਇਹਨਾਂ ਵਿੱਚੋਂ ਕਿਸੇ ਇੱਕ ਲਈ ਮੁੜ-ਸਕੋਪ ਕਰ ਦਿੰਦਾ ਹੈ।

ਕਿਸੇ SDK 'ਤੇ ਆਪਣਾ ਹੀ ਏਜੰਟ ਬਣਾਇਆ ਹੈ? ਇੰਟਰਸੈਪਟਰ ਇਸਦੀਆਂ LLM ਕਾਲਾਂ ਵੀ ਟਰੈਕ ਕਰਦਾ ਹੈ।
[docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ਦੇਖੋ।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **ਸੈਸ਼ਨ ਅਤੇ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ**: ਹਰ ਏਜੰਟ ਨੇ ਕੀ ਕੀਤਾ, ਵਾਰੀ-ਵਾਰੀ, ਰੀਪਲੇਅ ਸਮੇਤ
- **ਲਾਗਤ ਅਤੇ ਟੋਕਨ**: ਰਨਟਾਈਮ, ਮਾਡਲ, ਸੈਸ਼ਨ ਅਤੇ ਦਿਨ ਦੇ ਹਿਸਾਬ ਨਾਲ, ਅਨੌਮਲੀ ਫਲੈਗਾਂ ਸਮੇਤ
- **ਫਲੋ**: ਚੈਨਲਾਂ, ਮਾਡਲਾਂ ਅਤੇ ਟੂਲਾਂ ਵਿੱਚੋਂ ਲੰਘਦੇ ਸੁਨੇਹਿਆਂ ਦਾ ਲਾਈਵ ਡਾਇਗ੍ਰਾਮ
- **ਬ੍ਰੇਨ**: ਹੁੰਦੇ ਹੀ ਰੀਜ਼ਨਿੰਗ ਅਤੇ ਟੂਲ-ਕਾਲ ਈਵੈਂਟ ਸਟ੍ਰੀਮ
- **ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ**: ਪ੍ਰੋਵਾਈਡਰ ਹਿਸਾਬ ਨਾਲ ਵਿੰਡੋ ਯੂਟਿਲਾਈਜ਼ੇਸ਼ਨ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਜ਼ਬਰਦਸਤੀ ਓਵਰਫਲੋਅ, ਨਾਲ ਹੀ ਹਰ ਰਨਟਾਈਮ ਲਈ ਇਹ ਨਕਸ਼ਾ ਕਿ ਅਸੀਂ ਕੀ *ਨਹੀਂ* ਦੇਖ ਸਕਦੇ ([ਕਿਵੇਂ](docs/CONTEXT_BLOWOUT.md))
- **ਮੈਮੋਰੀ ਅਤੇ ਸਕਿੱਲ**: ਉਹ ਫਾਈਲਾਂ ਅਤੇ ਸਕਿੱਲ ਜੋ ਹਰ ਰਨਟਾਈਮ ਨੇ ਅਸਲ ਵਿੱਚ ਲੋਡ ਕੀਤੀਆਂ
- **ਸਿਹਤ ਅਤੇ ਲੌਗ**: ਡਿਸਕ, ਮੈਮੋਰੀ, ਗ਼ਲਤੀ ਦਰਾਂ, ਰੇਟ ਲਿਮਿਟ, ਲਾਈਵ ਲੌਗ ਸਟ੍ਰੀਮ
- **ਅਲਰਟ**: ਬਜਟ ਕੈਪ, ਗ਼ਲਤੀ ਦੇ ਵਾਧੇ, ਏਜੰਟ-ਆਫ਼ਲਾਈਨ, Slack, Discord, PagerDuty, Telegram, Email ਨੂੰ ਭੇਜੇ ਜਾਣ ਵਾਲੇ
- **ਮਨਜ਼ੂਰੀਆਂ (Approvals)**: ਜੋਖਮ ਭਰੀਆਂ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਚੱਲਣ ਤੋਂ *ਪਹਿਲਾਂ* ਰੋਕੋ ਅਤੇ ਆਪਣੇ ਫ਼ੋਨ ਤੋਂ ਮਨਜ਼ੂਰ ਕਰੋ ([ਕਿਵੇਂ](docs/APPROVALS.md))

## ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ, ਅਤੇ ਨਿਗਰਾਨੀ ਦੀ ਲਾਗਤ

ਕਿਸੇ ਵੀ ਏਜੰਟ-ਤੁਲਨਾ ਟੂਲ 'ਤੇ ਭਰੋਸਾ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਦੋ ਸਵਾਲਾਂ ਦੇ ਜਵਾਬ ਦੇਣੇ ਬਣਦੇ ਹਨ।

**ਇਹ ਰਨਟਾਈਮਾਂ ਵਿੱਚ ਕੌਂਟੈਕਸਟ-ਵਿੰਡੋ ਬਲੋਆਊਟ ਨੂੰ ਕਿਵੇਂ ਸੰਭਾਲਦਾ ਹੈ?**

ਯੂਟਿਲਾਈਜ਼ੇਸ਼ਨ ਪ੍ਰਤੀਸ਼ਤ ਓਨਾ ਹੀ ਸੱਚਾ ਹੁੰਦਾ ਹੈ ਜਿੰਨਾ ਇਹ ਜਿਸ ਅੰਕ ਨਾਲ ਵੰਡਿਆ ਜਾਂਦਾ ਹੈ। ClawMetry
[ਇੱਕ ਟੇਬਲ ਤੋਂ ਜਿਸਨੂੰ ਤੁਸੀਂ ਪੜ੍ਹ ਅਤੇ PR ਕਰ ਸਕਦੇ ਹੋ](clawmetry/context_windows.py) ਪ੍ਰੋਵਾਈਡਰ ਹਿਸਾਬ ਨਾਲ ਵਿੰਡੋ ਦਾ ਆਕਾਰ ਤੈਅ ਕਰਦਾ ਹੈ,
ਜੋ Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama ਅਤੇ GLM ਨੂੰ ਕਵਰ ਕਰਦਾ ਹੈ। ਇਹ ਸਾਰੀਆਂ 26
ਰਨਟਾਈਮਾਂ ਨੂੰ ਇੱਕੋ ਵੈਂਡਰ ਦੇ ਸਕੇਲ ਨਾਲ ਨਹੀਂ ਮਾਪਦਾ। ਇਹ ਗੱਲ ਮਾਅਨੇ ਰੱਖਦੀ ਹੈ: 300K GPT-5 ਵਾਰੀ ਨੂੰ
Anthropic ਦੇ 200K ਦੇ ਵਿਰੁੱਧ ਪਰਖਿਆ ਜਾਵੇ ਤਾਂ ">100%, blown" ਪੜ੍ਹਦਾ ਹੈ ਜਦਕਿ ਅਸਲ ਵਿੱਚ ਇਹ
GPT-5 ਦੇ 400K ਵਿੱਚੋਂ 75% 'ਤੇ ਹੈ। ਉਹੀ ਸਕੇਲ ਇੱਕ ਅਸਲ ਵਿੱਚ ਓਵਰਫਲੋਅ ਹੋਈ 130K DeepSeek
ਵਾਰੀ ਨੂੰ ਆਰਾਮਦਾਇਕ 65% ਵਜੋਂ ਲੁਕਾ ਦਿੰਦਾ ਹੈ।

ਹਰ ਵਿੰਡੋ ਆਪਣੇ ਸਰੋਤ ਸਮੇਤ ਆਉਂਦੀ ਹੈ: `model_table`, `explicit_marker`,
`observed_floor`, ਜਾਂ ਜਦੋਂ ਸਾਨੂੰ ਮਾਡਲ ਦਾ ਪਤਾ ਨਹੀਂ ਹੁੰਦਾ ਤਾਂ ਇੱਕ ਇਮਾਨਦਾਰ `default`। ਅੰਦਾਜ਼ੇ 'ਤੇ ਬਣਿਆ
ਗੇਜ ਕਦੇ ਵੀ ਲੁਕਅੱਪ 'ਤੇ ਬਣੇ ਗੇਜ ਵਾਂਗ ਭਰੋਸੇਯੋਗ ਦਿਖਾਈ ਨਹੀਂ ਦਿੰਦਾ।

ClawMetry ਸਿਰਫ਼ ਕੁਝ ਰਨਟਾਈਮਾਂ 'ਤੇ ਹੀ ਕੰਪੈਕਸ਼ਨ ਈਵੈਂਟ ਦੇਖ ਸਕਦਾ ਹੈ। ਇਸ ਲਈ
`GET /api/context-coverage` ਹਰ ਰਨਟਾਈਮ ਲਈ ਦੱਸਦਾ ਹੈ ਕਿ ਕੀ **ਇੱਕ 0 ਦਾ ਮਤਲਬ "ਸਾਫ਼ ਚੱਲਿਆ" ਹੈ ਜਾਂ
"ਅਸੀਂ ਅੰਨ੍ਹੇ ਹਾਂ"**। ਇੱਕ `0` ਜਿਸਦਾ ਅਸਲ ਮਤਲਬ ਅੰਨ੍ਹਾ ਹੋਣਾ ਹੈ, ਓਹੀ ਦੱਸਦਾ ਹੈ।
[ਪੂਰੀ ਜਾਣਕਾਰੀ](docs/CONTEXT_BLOWOUT.md)

**ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਲਾਗਤ ਕਿੰਨੀ ਹੈ?**

| ਰਸਤਾ | ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਸ਼ਾਮਲ | ਡਿਫ਼ਾਲਟ? |
|---|---|---|
| ਸੈਸ਼ਨ-ਫਾਈਲ ਟੇਲਿੰਗ (ਸਾਰੀਆਂ 30 ਰਨਟਾਈਮਾਂ) | **0**। ਵੱਖਰੀ ਪ੍ਰੋਸੈੱਸ, ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਕੋਈ ClawMetry ਕੋਡ ਨਹੀਂ | ਚਾਲੂ |
| HTTP ਇੰਟਰਸੈਪਟਰ (`CLAWMETRY_INTERCEPT=1`) | ਹਰ LLM ਕਾਲ 'ਤੇ **+0.44 ms**, ਜਾਂ 5s ਕਾਲ ਦਾ 0.009% | ਬੰਦ |
| ਪ੍ਰੀ-ਟੂਲ ਹੁੱਕ ਗੇਟ (warm cache) | ਹਰ ਗੇਟਿਡ ਟੂਲ ਕਾਲ 'ਤੇ **+44 ms**, 36 ms ਦੇ ਇੰਟਰਪ੍ਰੇਟਰ ਫ਼ਲੋਰ ਤੋਂ ਉੱਪਰ | ਬੰਦ |
| ਐਨਫੋਰਸਮੈਂਟ ਪ੍ਰੌਕਸੀ | ਹਰ LLM ਕਾਲ 'ਤੇ **+9.7 ms** | ਬੰਦ |

ਡੈਮਨ ਹੋਸਟ ਲਾਗਤ: **2,762 events/sec** ਇਨਜੈਸਟ, ਡਿਸਕ 'ਤੇ **710 bytes/event**
(100k ਈਵੈਂਟਾਂ ਲਈ 67.7 MB), ਅਤੇ ਵਿਅਸਤ ਇੰਸਟਾਲ 'ਤੇ **ਇੱਕ ਕੋਰ ਦਾ ~12%** ਲਗਾਤਾਰ। ਇਹ ਆਖ਼ਰੀ
ਅੰਕੜਾ ਸਾਡੇ ਆਪਣੇ ਦੱਸੇ 5-10% ਬਜਟ ਤੋਂ ਵੱਧ ਹੈ, ਇਸ ਲਈ ਇਸਨੂੰ ਪੰਨੇ ਤੋਂ ਲੁਕਾਉਣ ਦੀ ਬਜਾਏ
ਇੱਕ ਬੱਗ ਵਜੋਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਗਿਆ ਹੈ ਜਿਸਦਾ ਪਿੱਛਾ ਕਰਨਾ ਹੈ।

Apple M2 Pro 'ਤੇ `benchmarks/overhead.py` ਨਾਲ ਮਾਪਿਆ ਗਿਆ। ਇਹ ਹਾਰਨੈੱਸ ਹਰ ਹਾਲਤ ਨੂੰ
ਵੱਖਰੀ ਪ੍ਰੋਸੈੱਸ ਵਿੱਚ ਚਲਾਉਂਦਾ ਹੈ, ਉਹਨਾਂ ਦਾ ਕ੍ਰਮ ਬਦਲਦਾ ਰਹਿੰਦਾ ਹੈ, ਅਤੇ **ਜਦੋਂ ਗੇੜ ਉਸ ਦੇ ਚਿੰਨ੍ਹ 'ਤੇ ਸਹਿਮਤ ਨਹੀਂ ਹੁੰਦੇ ਤਾਂ
ਅੰਕੜਾ ਛਾਪਣ ਤੋਂ ਇਨਕਾਰ ਕਰ ਦਿੰਦਾ ਹੈ**। ਇਸਨੂੰ ਆਪਣੀ ਖ਼ੁਦ ਦੀ ਮਸ਼ੀਨ 'ਤੇ ਇੱਕ ਮਿੰਟ ਵਿੱਚ ਚਲਾਓ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ਹਰ ਰਸਤਾ ਮਾਪਿਆ ਗਿਆ ਹੈ, ਹੁੱਕ ਗੇਟਾਂ ਅਤੇ ਐਨਫੋਰਸਮੈਂਟ ਪ੍ਰੌਕਸੀ ਸਮੇਤ,
ਅਤੇ ਹਾਰਨੈੱਸ CI ਵਿੱਚ Linux, macOS ਅਤੇ Windows 'ਤੇ ਚੱਲਦਾ ਹੈ। ਜਾਣਨ ਲਾਇਕ ਦੋ ਨਤੀਜੇ: ਪ੍ਰੌਕਸੀ ਦੀ ਲਾਗਤ
Windows 'ਤੇ Linux ਨਾਲੋਂ ਲਗਭਗ ਸੱਤ ਗੁਣਾ ਹੈ, ਅਤੇ ਡੈਮਨ ਇਸ ਸਮੇਂ ਇੱਕ ਕੋਰ ਦਾ ਲਗਭਗ 12% ਲਗਾਤਾਰ
ਵਰਤਦਾ ਹੈ, ਜੋ ਸਾਡੇ ਆਪਣੇ 5-10% ਬਜਟ ਤੋਂ ਵੱਧ ਹੈ। ਕੱਚਾ JSON, ਤਰੀਕਾ, ਅਤੇ ਜੋ ਹਾਲੇ ਮਾਪਿਆ ਨਹੀਂ ਗਿਆ ਉਹ
[docs/OVERHEAD.md](docs/OVERHEAD.md) ਵਿੱਚ ਹੈ।

## ਕੀਮਤ

| ਪਲਾਨ | ਇਹ ਕੀ ਕਵਰ ਕਰਦਾ ਹੈ | ਕੀਮਤ |
|---|---|---|
| **ਮੁਫ਼ਤ** | OpenClaw + NVIDIA NemoClaw + Goose, ਪੂਰਾ ਡੈਸ਼ਬੋਰਡ, ਸਿਰਫ਼ ਲੋਕਲ | $0 |
| **ਸਟਾਰਟਰ** | ਉੱਪਰ ਦੱਸੀ ਹਰ ਹੋਰ ਰਨਟਾਈਮ, ਫਲੀਟ ਵਿਊ, ਕਲਾਊਡ ਸਿੰਕ | $9 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |
| **Pro** | ਸਟਾਰਟਰ + ਕੰਟਰੋਲ ਅਤੇ ਮੁਲਾਂਕਣ: ਮਨਜ਼ੂਰੀਆਂ, ਟੂਲ-ਜੋਖਮ ਨੀਤੀਆਂ, evals, ਅਨੌਮਲੀ ਪਛਾਣ, ਕੌਸਟ ਓਪਟੀਮਾਈਜ਼ਰ, OTel ਐਕਸਪੋਰਟ, ਟੈਂਪਰ-ਏਵੀਡੈਂਟ ਆਡਿਟ ਲੌਗ | $19 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |

ਸਲਾਨਾ ਪਲਾਨ, Enterprise ਅਤੇ ਮੌਜੂਦਾ ਅੰਕੜੇ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** 'ਤੇ ਹਨ। ਸੈਲਫ਼-ਹੋਸਟਡ ਲਾਇਸੈਂਸ
ਕੁੰਜੀਆਂ ਕਲਾਊਡ ਬਿਨਾਂ ਵੀ ਕੰਮ ਕਰਦੀਆਂ ਹਨ (`clawmetry license`)। ਸਹੀ ਮੁਫ਼ਤ/ਭੁਗਤਾਨ ਵੰਡ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਵਿੱਚ ਹੈ।

## ਤੁਹਾਡਾ ਡਾਟਾ ਤੁਹਾਡੀ ਮਸ਼ੀਨ 'ਤੇ ਹੀ ਰਹਿੰਦਾ ਹੈ

ClawMetry ਲੋਕਲ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਅਤੇ ਲੌਗ ਪੜ੍ਹਦਾ ਹੈ। **ਕੋਈ ਸੈਸ਼ਨ ਡਾਟਾ ਤੁਹਾਡੇ ਬਾਕਸ ਤੋਂ ਬਾਹਰ
ਨਹੀਂ ਜਾਂਦਾ ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ ਚਲਾਉਂਦੇ** — ਕੋਈ ਪ੍ਰੌਮਪਟ, ਜਵਾਬ, ਟੂਲ ਆਰਗੂਮੈਂਟ, ਫਾਈਲ
ਸਮੱਗਰੀ ਜਾਂ ਲੌਗ ਲਾਈਨ ਨਹੀਂ। ਜਦੋਂ ਤੁਸੀਂ ਕਨੈਕਟ ਕਰਦੇ ਹੋ, ਤਾਂ ਸਨੈਪਸ਼ਾਟ ਇੱਕ ਕੁੰਜੀ ਨਾਲ ਐਂਡ-ਟੂ-ਐਂਡ ਇਨਕ੍ਰਿਪਟਡ ਹੁੰਦਾ ਹੈ
ਜੋ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਕਦੇ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦੀ, ਅਤੇ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਡਿਕ੍ਰਿਪਟ ਕੀਤਾ ਜਾਂਦਾ ਹੈ। ਜੇ ਕਿਸੇ
ਨੋਡ ਕੋਲ ਕੁੰਜੀ ਨਹੀਂ ਹੈ, ਤਾਂ ਅਪਲੋਡ ਖੁੱਲ੍ਹੇ ਵਿੱਚ ਭੇਜਣ ਦੀ ਬਜਾਏ ਛੱਡ ਦਿੱਤਾ ਜਾਂਦਾ ਹੈ, ਅਤੇ ਕੋਈ ਵੀ
ਸਰਵਰ ਜਵਾਬ ਇਸਨੂੰ ਬੰਦ ਨਹੀਂ ਕਰ ਸਕਦਾ।

ਤੁਹਾਡੇ ਕਨੈਕਟ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਦੋ ਚੀਜ਼ਾਂ ਡਿਫ਼ਾਲਟ ਤੌਰ 'ਤੇ ਚੱਲਦੀਆਂ ਹਨ, ਦੋਵੇਂ opt-out ਅਤੇ
ਕੋਈ ਵੀ ਸੈਸ਼ਨ ਡਾਟਾ ਨਹੀਂ ਲੈ ਕੇ ਜਾਂਦੀਆਂ: ਇੱਕ ਅਗਿਆਤ ਇੰਸਟਾਲ ਪਿੰਗ ਅਤੇ PyPI ਦੇ ਵਿਰੁੱਧ ਇੱਕ ਵਰਜ਼ਨ
ਜਾਂਚ। ਡਿਫ਼ਾਲਟ ਇੰਸਟਾਲ ਸਟਾਰਟਅੱਪ ਬੈਨਰ ਲਾਈਨ ਲਈ ਇੱਕ ਵਾਰ ਤੁਹਾਡਾ ਪਬਲਿਕ IP ਵੀ ਲੱਭਦਾ ਹੈ। ਹਰ
ਮੰਜ਼ਿਲ, ਇਹ ਕੀ ਲੈ ਕੇ ਜਾਂਦੀ ਹੈ ਅਤੇ ਇਸਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰਨਾ ਹੈ
[docs/EGRESS.md](docs/EGRESS.md) ਵਿੱਚ ਸੂਚੀਬੱਧ ਹੈ; ਸੈਲਫ਼-ਹੋਸਟਡ, ਰੀ-ਪੌਇੰਟਡ ਅਤੇ ਏਅਰ-ਗੈਪਡ ਇੰਸਟਾਲ
ਕੋਈ ਵੀ ਆਪਣੀ ਮਰਜ਼ੀ ਵਾਲੀ ਬਾਹਰੀ ਕਾਲ ਨਹੀਂ ਕਰਦੇ।

ਡਿਕ੍ਰਿਪਸ਼ਨ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ, ਸਾਡੇ ਵੱਲੋਂ ਦਿੱਤੇ ਕੋਡ ਵਿੱਚ ਹੁੰਦੀ ਹੈ। ਇਹ ਪਹਿਲਾਂ ਇੱਕ
ਵਾਅਦਾ ਹੁੰਦਾ ਸੀ; ਹੁਣ ਇਹ ਕੁਝ ਹੈ ਜੋ ਤੁਸੀਂ ਜਾਂਚ ਸਕਦੇ ਹੋ। ਹਰ ਲਾਈਨ ਜੋ ਤੁਹਾਡੀ ਕੁੰਜੀ ਨੂੰ ਛੂਹਦੀ ਹੈ
ਇੱਕ ਪੜ੍ਹਨਯੋਗ ਫਾਈਲ ਵਿੱਚ ਹੈ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
ਜੋ wheel ਦੇ ਅੰਦਰ ਭੇਜੀ ਜਾਂਦੀ ਹੈ ਅਤੇ ਜਿਵੇਂ ਦੀ ਤਿਵੇਂ ਪਰੋਸੀ ਜਾਂਦੀ ਹੈ, Subresource
Integrity ਹੈਸ਼ ਨਾਲ ਪਿੰਨ ਕੀਤੀ ਹੋਈ। ਇਹ ਪੁਸ਼ਟੀ ਕਰਨ ਲਈ ਕਿ ਬ੍ਰਾਊਜ਼ਰ ਉਹੀ ਚਲਾਉਂਦਾ ਹੈ ਜੋ ਅਸੀਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ਇਹ ਕੀ ਸਾਬਤ ਨਹੀਂ ਕਰਦਾ: ਅਸੀਂ ਉਹ ਪੰਨਾ ਪਰੋਸਦੇ ਹਾਂ ਜੋ ਇਸ ਫਾਈਲ ਨੂੰ ਲੋਡ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ ਅਸੀਂ
ਵੱਖਰਾ ਪੰਨਾ ਵੀ ਪਰੋਸ ਸਕਦੇ ਹਾਂ। Integrity ਹੈਸ਼ ਤੁਹਾਨੂੰ ਕਿਸੇ ਖ਼ਰਾਬ ਹੋਏ CDN ਤੋਂ ਬਚਾਉਂਦੇ ਹਨ,
ਵੈਂਡਰ ਤੋਂ ਨਹੀਂ। ਤੁਹਾਨੂੰ ਜੋ ਮਿਲਦਾ ਹੈ ਉਹ ਇਹ ਹੈ ਕਿ ਕੋਈ ਵੀ ਬਦਲਾਅ ਜਾਣਬੁੱਝ ਕੇ ਕੀਤਾ ਜਾਣਾ ਚਾਹੀਦਾ ਹੈ,
ਪੰਨੇ ਦੇ ਸੋਰਸ ਵਿੱਚ ਦਿਖਾਈ ਦਿੰਦਾ ਹੈ, ਅਤੇ PyPI 'ਤੇ ਮੌਜੂਦ ਆਰਟੀਫੈਕਟ ਤੋਂ ਵੱਖਰਾ ਹੁੰਦਾ ਹੈ ਜਿਸਨੂੰ ਕੋਈ ਵੀ
ਲੈ ਸਕਦਾ ਹੈ। ਸੈਲਫ਼-ਹੋਸਟਿੰਗ ਜਾਂ ਸਿਰਫ਼-ਲੋਕਲ ਰਹਿਣਾ ਇਸ ਨਿਰਭਰਤਾ ਨੂੰ ਪੂਰੀ ਤਰ੍ਹਾਂ ਹਟਾ ਦਿੰਦਾ ਹੈ।

## ਇੰਸਟਾਲ

```bash
pip install clawmetry     # ਫਿਰ: clawmetry
```

ਜਾਂ ਇੱਕ-ਲਾਈਨਰ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ਜਾਂ Windows 'ਤੇ Python 3.8+ ਚਾਹੀਦਾ ਹੈ, ਅਤੇ ਉਸੇ ਮਸ਼ੀਨ 'ਤੇ ਘੱਟੋ-ਘੱਟ ਇੱਕ ਏਜੰਟ
ਰਨਟਾਈਮ। Docker ਹਿਦਾਇਤਾਂ: [docs/DOCKER.md](docs/DOCKER.md)।

## ਡੌਕਸ

| | |
|---|---|
| [ਰਨਟਾਈਮ ਅਨੁਕੂਲਤਾ](docs/compatibility.md) | ਹਰ ਅਡੈਪਟਰ ਕੀ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਰਨਟਾਈਮ ਕਿਵੇਂ ਸ਼ਾਮਲ ਕਰੀਏ |
| [ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ](docs/CONTEXT_BLOWOUT.md) | ਪ੍ਰੋਵਾਈਡਰ ਹਿਸਾਬ ਵਿੰਡੋਆਂ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਓਵਰਫਲੋਅ, ਹਰ-ਰਨਟਾਈਮ ਕਵਰੇਜ |
| [ਓਵਰਹੈੱਡ](docs/OVERHEAD.md) | ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਲਾਗਤ ਕੀ ਹੈ, ਮਾਪੀ ਗਈ, ਦੁਬਾਰਾ ਬਣਾਉਣ ਲਈ ਹਾਰਨੈੱਸ ਸਮੇਤ |
| [Entitlements](docs/ENTITLEMENTS.md) | ਮੁਫ਼ਤ ਬਨਾਮ ਭੁਗਤਾਨ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, ਲਾਇਸੈਂਸ CLI |
| [ਮਨਜ਼ੂਰੀਆਂ ਅਤੇ ਨੀਤੀਆਂ](docs/APPROVALS.md) | ਪ੍ਰੀ-ਐਗਜ਼ੀਕਿਊਸ਼ਨ ਗੇਟਿੰਗ, ਜੋਖਮ ਸਕੋਰਿੰਗ, ਫ਼ੋਨ ਮਨਜ਼ੂਰੀਆਂ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ਟਰੇਸ ਕਿਤੇ ਵੀ ਐਕਸਪੋਰਟ ਕਰੋ, ਕਿਤੋਂ ਵੀ OTLP ਇੰਜੈਸਟ ਕਰੋ |
| [SDK ਟਰੈਕਿੰਗ](docs/SDK_TRACKING.md) | ਤੁਹਾਡੇ ਆਪਣੇ ਬਣਾਏ ਏਜੰਟਾਂ ਲਈ ਲਾਗਤ ਦਾ ਹਿਸਾਬ |
| [ਚੈਟ ਚੈਨਲ](docs/CHANNELS.md) | Flow ਵਿੱਚ ਦਿਖਾਏ ਗਏ ਚੈਟ ਅਡੈਪਟਰ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ਸੈਂਡਬੌਕਸਡ NVIDIA NemoClaw ਸੈੱਟਅੱਪ |
| [Docker](docs/DOCKER.md) | ਇਮੇਜ, compose, ਵਾਲਿਊਮ ਮਾਊਂਟ |
| [ਆਰਕੀਟੈਕਚਰ](ARCHITECTURE.md) · [ਡਿਵੈਲਪਮੈਂਟ](docs/DEVELOPMENT.md) | ਇਹ ਅੰਦਰੋਂ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ; ਸੋਰਸ ਤੋਂ ਚਲਾਉਣਾ |
| [ਟੈਲੀਮੈਟਰੀ](docs/TELEMETRY.md) | ਅਗਿਆਤ ਇੰਸਟਾਲ ਅਤੇ ਡੈਸਕਟੌਪ-ਓਪਨ ਪਿੰਗ, ਅਤੇ ਉਹਨਾਂ ਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰੀਏ |

## ਸਕਰੀਨਸ਼ਾਟ

ਹੇਠਾਂ ਦਿੱਤਾ ਹਰ ਅੰਕੜਾ ਇੱਕ ਅਸਲੀ ਮਸ਼ੀਨ ਤੋਂ ਹੈ, ਸਿਰਫ਼-ਪੜ੍ਹਨ ਲਈ, ਬਿਨਾਂ ਕੁਝ ਸੈੱਟ ਕੀਤੇ।

**ਇਹ ਦੱਸਦਾ ਹੈ ਜਦੋਂ ਕੁਝ ਗ਼ਲਤ ਹੋਵੇ, ਸਿਰਫ਼ ਕੀ ਹੋਇਆ ਓਹੀ ਨਹੀਂ।**
ਸਿਖਰ 'ਤੇ ਦੋ ਅਨੌਮਲੀ ਬੈਨਰ: ਖਰਚ ਰੋਜ਼ਾਨਾ ਔਸਤ ਤੋਂ 7 ਗੁਣਾ ਚੱਲ ਰਿਹਾ, ਅਤੇ 4.2 ਗੁਣਾ
ਲਾਗਤ ਦਾ ਵਾਧਾ। ਉਹਨਾਂ ਦੇ ਹੇਠਾਂ, 667 ਹਾਲੀਆ ਸੈਸ਼ਨਾਂ ਵਿੱਚੋਂ 324 ਵਿੱਚ ਬਰਬਾਦੀ ਦਾ ਸੰਕੇਤ ਦਿਖ ਰਿਹਾ ਹੈ,
ਕਾਰਨ ਹਿਸਾਬ ਨਾਲ ਵੰਡਿਆ ਹੋਇਆ।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਹਰ ਵਿੰਡੋ ਵਿੱਚ।**
ਅੱਜ $252.47, ਇਸ ਹਫ਼ਤੇ $513.15, ਇਸ ਮਹੀਨੇ $1,312.92, ਹਰ ਇੱਕ ਦੇ ਪਿੱਛੇ ਦੇ ਟੋਕਨ ਅਤੇ ਇਸ ਦਾ ਕਿੰਨਾ ਹਿੱਸਾ
ਤੁਹਾਡਾ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਪਹਿਲਾਂ ਹੀ ਕਵਰ ਕਰਦਾ ਹੈ, ਸਮੇਤ। ਉਸ ਤੋਂ ਹੇਠਾਂ, ਲਗਭਗ $1,128/ਮਹੀਨਾ ਮੁੜ ਪ੍ਰਾਪਤ ਕੀਤੇ ਜਾਣ ਯੋਗ ਵਜੋਂ
ਸੂਚੀਬੱਧ ਅਤੇ ਕੈਸ਼ੇ ਦੇ ਦੁਬਾਰਾ ਇਸਤੇਮਾਲ ਨਾਲ ਪਹਿਲਾਂ ਹੀ ਬਚਾਏ ਗਏ $17,256/ਮਹੀਨਾ।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਸੁਨੇਹਾ ਜਵਾਬ ਕਿਵੇਂ ਬਣਦਾ ਹੈ।**
ਲਾਈਵ ਫਲੋ ਡਾਇਗ੍ਰਾਮ: ਤੁਸੀਂ, ਉਹ ਚੈਨਲ ਜਿਸ 'ਤੇ ਇਹ ਆਇਆ, ਗੇਟਵੇ, ਹੁਣੇ ਜਵਾਬ ਦੇ ਰਿਹਾ ਮਾਡਲ, ਅਤੇ ਹਰ
ਟੂਲ ਜਿਸਨੂੰ ਇਸਨੇ ਵਰਤਿਆ। ਜਿਵੇਂ-ਜਿਵੇਂ ਕੰਮ ਇਹਨਾਂ ਵਿੱਚੋਂ ਲੰਘਦਾ ਹੈ, ਨੋਡ ਜਗਦੇ ਹਨ।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ਮਸ਼ੀਨ 'ਤੇ ਹਰ ਏਜੰਟ, ਇੱਕ ਟੇਬਲ ਵਿੱਚ।**
ਇਹ ਕੀ ਚਲਾਉਂਦਾ ਹੈ, ਪਿਛਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ਅਤੇ ਪੂਰੇ ਜੀਵਨ ਕਾਲ ਵਿੱਚ ਇਸਦੀ ਲਾਗਤ ਕੀ ਹੈ, ਇਹ ਆਖ਼ਰੀ ਵਾਰ
ਕਦੋਂ ਦੇਖਿਆ ਗਿਆ, ਕੌਣ ਇਸਦਾ ਮਾਲਕ ਹੈ, ਅਤੇ ਕੀ ਕੋਈ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਬਿੱਲ ਕਵਰ ਕਰ ਰਿਹਾ ਹੈ। ਇੱਥੇ 14 ਏਜੰਟ,
3 ਸੈਸ਼ਨ ਕੰਮ ਕਰ ਰਹੇ, 13 ਸ਼ਾਂਤ।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਵਾਰੀ ਦਾ ਸਮਾਂ ਅਤੇ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਟੂਲ ਦਰ ਟੂਲ।**
ਇੱਕ ਅਸਲੀ ਸੈਸ਼ਨ ਦੀ ਇੱਕ ਵਾਰੀ: 11.2 ਮਿੰਟਾਂ ਵਿੱਚ $1.16 ਲਈ 11 ਟੂਲ। ਹਰ Bash
ਕਾਲ ਅਤੇ ਮਾਡਲ ਕਾਲ ਨੂੰ ਟਾਈਮਲਾਈਨ 'ਤੇ ਆਪਣਾ ਬਾਰ ਮਿਲਦਾ ਹੈ, ਤਾਂ ਜੋ 4.1 ਮਿੰਟ ਚੱਲੀ ਕਮਾਂਡ ਅਤੇ 226ms
ਚੱਲੀ ਕਮਾਂਡ ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਵੱਖ ਦੱਸੀਆਂ ਜਾ ਸਕਣ।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ਇਹ ਕੰਮ ਨੂੰ ਗਰੇਡ ਕਰਦਾ ਹੈ, ਸਿਰਫ਼ ਖਰਚ ਨੂੰ ਨਹੀਂ।**
ਇਸ ਹਫ਼ਤੇ ਇੱਕ A: 54 ਕੰਮ ਸਾਫ਼ ਵਾਪਸ ਆਏ, 2 ਖਰਾਬ ਵਾਲਿਆਂ ਦੀ ਲਾਗਤ $48.57 ਰਹੀ, ਅਤੇ ਜਿਹਨਾਂ
ਰਨ ਵਿੱਚ ਨਿਰਣਾ ਕਰਨ ਲਈ ਬਹੁਤ ਘੱਟ ਗਤੀਵਿਧੀ ਹੈ ਉਹਨਾਂ ਨੂੰ ਜਿੱਤ ਵਜੋਂ ਗਿਣਨ ਦੀ ਬਜਾਏ ਗਰੇਡ ਤੋਂ ਬਾਹਰ ਰੱਖਿਆ ਗਿਆ ਹੈ। ਹਰ
ਖਰਾਬ ਰਨ ਆਪਣੇ ਟਰੇਸ ਨਾਲ ਲਿੰਕ ਕਰਦਾ ਹੈ।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਕੌਂਟੈਕਸਟ ਵਿੰਡੋ ਵਾਰ-ਵਾਰ ਕਿਉਂ ਭਰ ਜਾਂਦੀ ਹੈ।**
ਆਖ਼ਰੀ ਵਾਰੀ 'ਤੇ 1M-ਟੋਕਨ ਵਿੰਡੋ ਵਿੱਚੋਂ 715K, 83.3% ਦਾ ਸਿਖਰ, 4 ਕੰਪੈਕਸ਼ਨ ਜੋ ਸਾਰੇ ਓਵਰਫਲੋਅ ਦੀ ਬਜਾਏ
ਪਹਿਲਾਂ ਤੋਂ ਹੀ ਚੱਲੇ, ਨਾਲ ਹੀ ਹਰ ਵਾਰੀ ਦੇ ਪਿੱਛੇ ਦੀ ਯੂਟਿਲਾਈਜ਼ੇਸ਼ਨ।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ਖੋਜ ਬਿਨਾਂ ਤੁਹਾਡੇ ਕੁਝ ਕਾਨਫ਼ਿਗਰ ਕੀਤਿਆਂ ਚੱਲਦੀ ਹੈ।**
ਬਿਲਟ-ਇਨ ਡਿਟੈਕਟਰ ਇੰਸਟਾਲ ਤੋਂ ਹੀ ਚਾਲੂ ਹਨ: ਏਜੰਟ ਸ਼ਾਂਤ ਹੋ ਗਿਆ, ਟੈਲੀਮੈਟਰੀ ਫੀਡ
ਰੁਕ ਗਈ, ਲਾਗਤ ਦਾ ਵਾਧਾ, ਟੋਕਨ ਦਾ ਵਾਧਾ, ਗ਼ਲਤੀਆਂ ਵਧ ਰਹੀਆਂ, ਗ਼ਲਤੀਆਂ ਦਾ ਵਾਧਾ, ਬਜਟ
ਥ੍ਰੈਸ਼ਹੋਲਡ, ਥ੍ਰੈਟ ਸਿਗਨੇਚਰ ਮੇਲ ਖਾਧਾ, ਸੁਰੱਖਿਆ ਟੂਲ ਦੀ ਖੋਜ, ਸੁਰੱਖਿਆ ਸਥਿਤੀ
ਬਦਲੀ। ਤੁਹਾਡੇ ਆਪਣੇ ਨਿਯਮ ਇਸ ਦੇ ਉੱਪਰ ਵਿਕਲਪਿਕ ਹਨ।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ਜੋਖਮ ਭਰੀ ਕਾਲ ਨੂੰ ਰੋਕਣਾ ਵਿਕਲਪਿਕ ਹੈ, ਅਤੇ ਬੰਦ ਹੀ ਭੇਜਿਆ ਜਾਂਦਾ ਹੈ।**
Recursive delete, force push, sudo, secrets, package install ਅਤੇ ਬਾਹਰੀ
ਕਾਲਾਂ ਵਿੱਚੋਂ ਹਰ ਇੱਕ ਲਈ ਇੱਕ ਨਿਯਮ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਚਾਲੂ ਕਰ ਸਕਦੇ ਹੋ। ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ ਅਜਿਹਾ ਨਹੀਂ ਕਰਦੇ, ClawMetry ਦੇਖਦਾ
ਹੈ ਅਤੇ ਕੁਝ ਨਹੀਂ ਬਦਲਦਾ। ਇੱਕ ਵਾਰ ਚਾਲੂ ਹੋਣ 'ਤੇ, ਮੇਲ ਖਾਂਦੀਆਂ ਕਾਲਾਂ ਇੱਥੇ (ਜਾਂ ਤੁਹਾਡੇ ਫ਼ੋਨ 'ਤੇ)
ਮਨਜ਼ੂਰੀ ਜਾਂ ਇਨਕਾਰ ਲਈ ਉਡੀਕ ਕਰਦੀਆਂ ਹਨ।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ਹੋਰ, ਹਰ ਰਨਟਾਈਮ ਹਿਸਾਬ ਨਾਲ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## ਸਟਾਰ ਇਤਿਹਾਸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ਲਾਇਸੈਂਸ

MIT · [@vivekchand](https://github.com/vivekchand) ਵੱਲੋਂ ਬਣਾਇਆ ਗਿਆ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
