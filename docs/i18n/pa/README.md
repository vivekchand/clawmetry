<!-- i18n-src:61beb8393e2f -->
> ਪੰਜਾਬੀ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ਇੱਕ ਏਜੰਟ ਬਿਨਾਂ ਕੋਈ ਤਰੱਕੀ ਕੀਤੇ ਸੌ ਟੂਲ ਕਾਲਾਂ ਕਰ ਸਕਦਾ ਹੈ।** ClawMetry
ਉਹ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਪੜ੍ਹਦਾ ਹੈ ਜੋ ਤੁਹਾਡੇ ਕੋਡਿੰਗ ਏਜੰਟ ਪਹਿਲਾਂ ਹੀ ਲਿਖਦੇ ਹਨ, ਅਤੇ ਟਾਈਮਲਾਈਨ,
ਟੂਲ ਕਾਲਾਂ ਅਤੇ ਰਨਟਾਈਮ ਜੋ ਵੀ ਟੋਕਨ ਤੇ ਲਾਗਤ ਡਾਟਾ ਦਿਖਾਉਂਦਾ ਹੈ, ਉਸਨੂੰ ਇੱਕ
ਵਿਊ ਵਿੱਚ ਪਾਉਂਦਾ ਹੈ — ਤਾਂ ਜੋ ਤੁਸੀਂ ਦੱਸ ਸਕੋ ਕਿ ਇੱਕ ਲੰਬਾ ਰਨ ਕੰਮ ਕਰ ਰਿਹਾ ਹੈ ਜਾਂ ਫਸ ਗਿਆ ਹੈ।

**30 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ — Claude Code, OpenAI Codex, Hermes, OpenClaw ਅਤੇ 26 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ। ([ਪੂਰੀ ਸੂਚੀ](SUPPORTED_RUNTIMES.txt), ਕੈਟਾਲਾਗ ਤੋਂ ਜਨਰੇਟ ਕੀਤੀ ਗਈ।)

> 🌐 **ਇਸਨੂੰ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ। ਸਭ ਕੁਝ ਆਪਣੇ-ਆਪ ਖੋਜ ਲੈਂਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ਉੱਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ: ਇਹ ਉਹ ਏਜੰਟ ਰਨਟਾਈਮ
ਲੱਭ ਲੈਂਦਾ ਹੈ ਜੋ ਤੁਹਾਡੇ ਕੋਲ ਪਹਿਲਾਂ ਹੀ ਹਨ, ਉਹਨਾਂ ਨੂੰ ਸਿਰਫ਼-ਪੜ੍ਹਨ ਲਈ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਇਸ ਗੱਲ ਵਿੱਚ ਕੁਝ ਨਹੀਂ ਬਦਲਦਾ ਕਿ ਉਹ ਕਿਵੇਂ ਚੱਲਦੇ ਹਨ।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ਇੰਸਟਾਲ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ

| | |
|---|---|
| **ਇਹ ਕੀ ਕਰਦਾ ਹੈ** | ਉਹ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਤੇ ਲੌਗ ਪੜ੍ਹਦਾ ਹੈ ਜੋ ਤੁਹਾਡੇ ਏਜੰਟ ਪਹਿਲਾਂ ਹੀ ਲਿਖਦੇ ਹਨ। ਕੋਈ SDK ਨਹੀਂ, ਕੋਈ ਕੋਡ ਤਬਦੀਲੀ ਨਹੀਂ, ਤੁਹਾਡੀ ਐਪ ਵਿੱਚ ਕੋਈ ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਨਹੀਂ। |
| **ਤੁਸੀਂ ਕੀ ਦੇਖਦੇ ਹੋ** | ਸੈਸ਼ਨ ਟਾਈਮਲਾਈਨ, ਟੂਲ-ਦਰ-ਟੂਲ ਰੀਪਲੇ, ਟੋਕਨ ਤੇ ਲਾਗਤ ਬ੍ਰੇਕਡਾਊਨ, ਅਤੇ ਟ੍ਰੈਜੈਕਟਰੀ ਸਿਗਨਲ (ਲੂਪਿੰਗ, ਦੁਹਰਾਈਆਂ ਗਈਆਂ ਅਸਫਲਤਾਵਾਂ) — ਹਰ ਰਨਟਾਈਮ ਲਈ। |
| **ਕੀ ਮੁਫ਼ਤ ਹੈ** | `pip install clawmetry` **OpenClaw, NVIDIA NemoClaw ਅਤੇ Goose** ਨੂੰ ਬਿਨਾਂ ਕਿਸੇ ਖਾਤੇ, ਬਿਨਾਂ ਕੁੰਜੀ ਅਤੇ ਬਿਨਾਂ ਨੈੱਟਵਰਕ ਕਾਲ ਦੇ ਪੜ੍ਹਦਾ ਹੈ। ਬਾਕੀ 27 — Claude Code, Codex, Cursor ਤੇ ਬਾਕੀ — ਕਲੋਜ਼ਡ-ਸੋਰਸ `clawmetry-pro` ਕੰਪੈਨੀਅਨ ਦੁਆਰਾ ਪੜ੍ਹੇ ਜਾਂਦੇ ਹਨ, ਜੋ 7-ਦਿਨ ਦੇ ਟ੍ਰਾਇਲ ਜਾਂ ਕਿਸੇ ਪਲਾਨ ਨਾਲ ਆਉਂਦਾ ਹੈ — ਸਹੀ ਵੰਡ ਲਈ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਦੇਖੋ। |
| **ਕਿਵੇਂ ਸ਼ੁਰੂ ਕਰੀਏ** | `pip install clawmetry && clawmetry`, ਫਿਰ localhost:8900 ਖੋਲ੍ਹੋ। ਇਸ ਮਸ਼ੀਨ ਉੱਤੇ ਹਾਲੇ ਕੋਈ ਏਜੰਟ ਨਹੀਂ ਹੈ? `clawmetry --sample` ਤਿੰਨ ਲੇਬਲ ਵਾਲੇ ਸਿੰਥੈਟਿਕ ਸੈਸ਼ਨਾਂ ਨਾਲ ਖੁੱਲ੍ਹਦਾ ਹੈ। |
| **ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਕੀ ਬਾਹਰ ਜਾਂਦਾ ਹੈ** | ਕੋਈ ਸੈਸ਼ਨ ਡਾਟਾ ਨਹੀਂ, ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ ਚਲਾਉਂਦੇ। ਦੋ ਚੀਜ਼ਾਂ ਡਿਫਾਲਟ ਰੂਪ ਵਿੱਚ ਚੱਲਦੀਆਂ ਹਨ, ਦੋਵੇਂ ਆਪਟ-ਆਊਟ ਕਰਨਯੋਗ ਹਨ ਅਤੇ ਕੋਈ ਵੀ ਸੈਸ਼ਨ ਸਮੱਗਰੀ ਨਹੀਂ ਲੈ ਕੇ ਜਾਂਦੀ: ਇੱਕ ਗੁਮਨਾਮ ਇੰਸਟਾਲ ਪਿੰਗ ਅਤੇ ਇੱਕ PyPI ਵਰਜ਼ਨ ਚੈੱਕ। ਹਰ ਮੰਜ਼ਿਲ [docs/EGRESS.md](docs/EGRESS.md) ਵਿੱਚ ਸੂਚੀਬੱਧ ਹੈ, ਜੋ ਟਿੱਪਣੀਆਂ ਪੜ੍ਹਨ ਦੀ ਬਜਾਏ ਵਾਇਰ ਕੈਪਚਰ ਤੋਂ ਬਣਾਈ ਗਈ ਹੈ। |

ਨਤੀਜੇ ਨੂੰ ਪਰਖਣ ਤੋਂ ਪਹਿਲਾਂ ਜਾਣਨ ਯੋਗ ਦੋ ਸੀਮਾਵਾਂ: ਰਨਟਾਈਮ ਬਹੁਤ
ਵੱਖਰਾ ਡਾਟਾ ਦਿਖਾਉਂਦੇ ਹਨ (ਕੁਝ ਕੋਈ ਲਾਗਤ ਬਿਲਕੁਲ ਨਹੀਂ ਦਿਖਾਉਂਦੇ — [ਮੈਟ੍ਰਿਕਸ](docs/compatibility.md)
ਦੱਸਦਾ ਹੈ ਕਿ ਕਿਹੜਾ, ਹਰ ਰਨਟਾਈਮ ਲਈ), ਅਤੇ ਕਿਸੇ ਕਾਰਵਾਈ ਨੂੰ ਦੇਖਣਾ ਉਸਨੂੰ ਰੋਕਣ ਦੇ
ਸਮਰੱਥ ਹੋਣ ਵਰਗਾ ਨਹੀਂ ਹੈ ([ਕਿਹੜੇ ਕੰਟਰੋਲ ਅਸਲੀ ਹਨ, ਹਰ ਰਨਟਾਈਮ ਲਈ](docs/APPROVALS.md))।


## 30 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

**ਓਪਨ ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ਭੁਗਤਾਨ ਯੋਗ ਪਲਾਨ ਉੱਤੇ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ਹਰ ਰਨਟਾਈਮ ਨੂੰ ਇੱਕੋ ਡੈਸ਼ਬੋਰਡ ਮਿਲਦਾ ਹੈ। ਕਈ ਇੱਕੋ ਸਮੇਂ ਚਲਾਓ ਅਤੇ ਹੈਡਰ
ਸਵਿੱਚਰ ਹਰ ਟੈਬ ਨੂੰ ਇਹਨਾਂ ਵਿੱਚੋਂ ਕਿਸੇ ਇੱਕ ਲਈ ਦੁਬਾਰਾ-ਸਕੋਪ ਕਰ ਦਿੰਦਾ ਹੈ।

ਕੀ ਤੁਸੀਂ SDK ਉੱਤੇ ਆਪਣਾ ਖੁਦ ਦਾ ਏਜੰਟ ਬਣਾਇਆ ਹੈ? ਇੰਟਰਸੈਪਟਰ ਇਸਦੀਆਂ LLM ਕਾਲਾਂ
ਵੀ ਟਰੈਕ ਕਰਦਾ ਹੈ। [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ਦੇਖੋ।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **ਸੈਸ਼ਨ ਅਤੇ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ**: ਹਰ ਏਜੰਟ ਨੇ ਕੀ ਕੀਤਾ, ਵਾਰੀ-ਦਰ-ਵਾਰੀ, ਰੀਪਲੇ ਸਮੇਤ
- **ਲਾਗਤ ਅਤੇ ਟੋਕਨ**: ਰਨਟਾਈਮ, ਮਾਡਲ, ਸੈਸ਼ਨ ਅਤੇ ਦਿਨ ਪ੍ਰਤੀ, ਵਿਗਾੜ ਫਲੈਗਾਂ ਸਮੇਤ
- **ਫਲੋ**: ਚੈਨਲਾਂ, ਮਾਡਲਾਂ ਅਤੇ ਟੂਲਾਂ ਵਿੱਚੋਂ ਲੰਘ ਰਹੇ ਸੁਨੇਹਿਆਂ ਦਾ ਲਾਈਵ ਡਾਇਗਰਾਮ
- **ਬ੍ਰੇਨ**: ਤਰਕ ਅਤੇ ਟੂਲ-ਕਾਲ ਈਵੈਂਟ ਸਟ੍ਰੀਮ, ਜਿਵੇਂ ਹੀ ਵਾਪਰਦਾ ਹੈ
- **ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ**: ਪ੍ਰੋਵਾਈਡਰ-ਵਾਰ ਸਾਈਜ਼ ਕੀਤੀ ਗਈ ਵਿੰਡੋ ਵਰਤੋਂ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਜ਼ਬਰਦਸਤੀ ਓਵਰਫਲੋਅ, ਨਾਲ ਹੀ ਹਰ ਰਨਟਾਈਮ ਲਈ ਇੱਕ ਨਕਸ਼ਾ ਕਿ ਅਸੀਂ ਕੀ *ਨਹੀਂ* ਦੇਖ ਸਕਦੇ ([ਕਿਵੇਂ](docs/CONTEXT_BLOWOUT.md))
- **ਮੈਮੋਰੀ ਅਤੇ ਸਕਿੱਲਸ**: ਉਹ ਫਾਈਲਾਂ ਅਤੇ ਸਕਿੱਲਸ ਜੋ ਹਰ ਰਨਟਾਈਮ ਨੇ ਅਸਲ ਵਿੱਚ ਲੋਡ ਕੀਤੇ
- **ਸਿਹਤ ਅਤੇ ਲੌਗ**: ਡਿਸਕ, ਮੈਮੋਰੀ, ਗਲਤੀ ਦਰਾਂ, ਰੇਟ ਲਿਮਿਟ, ਲਾਈਵ ਲੌਗ ਸਟ੍ਰੀਮ
- **ਅਲਰਟ**: ਬਜਟ ਕੈਪ, ਗਲਤੀ ਸਪਾਈਕ, ਏਜੰਟ-ਆਫਲਾਈਨ, Slack, Discord, PagerDuty, Telegram, Email ਨੂੰ ਰੂਟ ਕੀਤੇ
- **ਪ੍ਰਵਾਨਗੀਆਂ**: ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਚੱਲਣ *ਤੋਂ ਪਹਿਲਾਂ* ਰੋਕੋ ਅਤੇ ਆਪਣੇ ਫੋਨ ਤੋਂ ਮਨਜ਼ੂਰੀ ਦਿਓ ([ਕਿਵੇਂ](docs/APPROVALS.md))

## ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ, ਅਤੇ ਦੇਖਣ ਦੀ ਲਾਗਤ ਕੀ ਹੈ

ਕਿਸੇ ਵੀ ਏਜੰਟ-ਤੁਲਨਾ ਟੂਲ ਉੱਤੇ ਭਰੋਸਾ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਜਵਾਬ ਦੇਣ ਲਾਇਕ ਦੋ ਸਵਾਲ।

**ਇਹ ਵੱਖ-ਵੱਖ ਰਨਟਾਈਮਾਂ ਵਿੱਚ ਕੌਂਟੈਕਸਟ-ਵਿੰਡੋ ਬਲੋਆਊਟ ਨੂੰ ਕਿਵੇਂ ਸੰਭਾਲਦਾ ਹੈ?**

ਇੱਕ ਵਰਤੋਂ ਪ੍ਰਤੀਸ਼ਤ ਓਨੀ ਹੀ ਇਮਾਨਦਾਰ ਹੈ ਜਿੰਨਾ ਉਹ ਅੰਕ ਜਿਸ ਨਾਲ ਇਸਨੂੰ ਵੰਡਿਆ ਜਾਂਦਾ ਹੈ। ClawMetry
ਵਿੰਡੋ ਨੂੰ [ਇੱਕ ਟੇਬਲ ਤੋਂ ਪ੍ਰੋਵਾਈਡਰ-ਵਾਰ ਸਾਈਜ਼ ਕਰਦਾ ਹੈ ਜੋ ਤੁਸੀਂ ਪੜ੍ਹ ਸਕਦੇ ਹੋ ਅਤੇ
PR ਕਰ ਸਕਦੇ ਹੋ](clawmetry/context_windows.py), ਜੋ Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama ਅਤੇ GLM ਨੂੰ ਕਵਰ ਕਰਦਾ ਹੈ। ਇਹ ਸਾਰੇ 30
ਰਨਟਾਈਮਾਂ ਨੂੰ ਇੱਕ ਹੀ ਵੈਂਡਰ ਦੇ ਪੈਮਾਨੇ ਨਾਲ ਨਹੀਂ ਮਾਪਦਾ। ਇਹ ਮਾਇਨੇ ਰੱਖਦਾ ਹੈ: ਇੱਕ 300K GPT-5 ਵਾਰੀ
Anthropic ਦੇ 200K ਦੇ ਵਿਰੁੱਧ ਸਕੋਰ ਕੀਤੀ ਜਾਵੇ ਤਾਂ ">100%, ਫਟ ਗਈ" ਪੜ੍ਹੀ ਜਾਂਦੀ ਹੈ ਜਦਕਿ ਇਹ ਅਸਲ ਵਿੱਚ
GPT-5 ਦੇ 400K ਦੇ 75% ਉੱਤੇ ਹੈ। ਉਹੀ ਪੈਮਾਨਾ ਸੱਚਮੁੱਚ ਓਵਰਫਲੋਅ ਹੋਈ 130K DeepSeek ਵਾਰੀ ਨੂੰ
ਇੱਕ ਆਰਾਮਦਾਇਕ 65% ਵਜੋਂ ਲੁਕਾਉਂਦਾ ਹੈ।

ਹਰ ਵਿੰਡੋ ਆਪਣੀ ਪ੍ਰੋਵੇਨੈਂਸ ਨਾਲ ਆਉਂਦੀ ਹੈ: `model_table`, `explicit_marker`,
`observed_floor`, ਜਾਂ ਜਦੋਂ ਅਸੀਂ ਮਾਡਲ ਨਹੀਂ ਜਾਣਦੇ ਤਾਂ ਇੱਕ ਇਮਾਨਦਾਰ `default`। ਇੱਕ
ਅੰਦਾਜ਼ੇ ਉੱਤੇ ਬਣਿਆ ਗੇਜ ਕਦੇ ਵੀ ਲੁੱਕਅੱਪ ਉੱਤੇ ਬਣੇ ਗੇਜ ਵਾਂਗ ਉਸੇ ਭਰੋਸੇ ਨਾਲ ਨਹੀਂ
ਪੇਸ਼ ਹੁੰਦਾ।

ClawMetry ਸਿਰਫ਼ ਕੁਝ ਰਨਟਾਈਮਾਂ ਉੱਤੇ ਕੰਪੈਕਸ਼ਨ ਈਵੈਂਟ ਦੇਖ ਸਕਦਾ ਹੈ। ਇਸ ਲਈ
`GET /api/context-coverage` ਹਰ ਰਨਟਾਈਮ ਲਈ ਰਿਪੋਰਟ ਕਰਦਾ ਹੈ ਕਿ ਕੀ **ਜ਼ੀਰੋ ਦਾ ਮਤਲਬ
"ਸਾਫ਼ ਚੱਲਿਆ" ਹੈ ਜਾਂ "ਅਸੀਂ ਅੰਨ੍ਹੇ ਹਾਂ"**। ਇੱਕ `0` ਜਿਸਦਾ ਅਸਲ ਵਿੱਚ ਮਤਲਬ ਅੰਨ੍ਹਾ ਹੈ, ਇਹ ਦੱਸ ਦਿੰਦਾ ਹੈ।
[ਪੂਰੀ ਜਾਣਕਾਰੀ](docs/CONTEXT_BLOWOUT.md)

**ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਕੀਮਤ ਕੀ ਹੈ?**

| ਰਸਤਾ | ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਜੋੜਿਆ ਗਿਆ | ਡਿਫਾਲਟ? |
|---|---|---|
| ਸੈਸ਼ਨ-ਫਾਈਲ ਟੇਲਿੰਗ (ਸਾਰੇ 30 ਰਨਟਾਈਮ) | **0**। ਵੱਖਰੀ ਪ੍ਰਕਿਰਿਆ, ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਕੋਈ ClawMetry ਕੋਡ ਨਹੀਂ | ਚਾਲੂ |
| HTTP ਇੰਟਰਸੈਪਟਰ (`CLAWMETRY_INTERCEPT=1`) | ਹਰ LLM ਕਾਲ ਲਈ **+0.44 ms**, ਜਾਂ 5s ਕਾਲ ਦਾ 0.009% | ਬੰਦ |
| ਪ੍ਰੀ-ਟੂਲ ਹੁੱਕ ਗੇਟ (ਵਾਰਮ ਕੈਸ਼) | 36 ms ਇੰਟਰਪ੍ਰੇਟਰ ਫਲੋਰ ਤੋਂ ਉੱਪਰ, ਹਰ ਗੇਟ ਕੀਤੀ ਟੂਲ ਕਾਲ ਲਈ **+44 ms** | ਬੰਦ |
| ਲਾਗੂਕਰਨ ਪ੍ਰੌਕਸੀ | ਹਰ LLM ਕਾਲ ਲਈ **+9.7 ms** | ਬੰਦ |

ਡੀਮਨ ਹੋਸਟ ਲਾਗਤ: **2,762 ਈਵੈਂਟ/ਸਕਿੰਟ** ਇਨਜੈਸਟ, **710 ਬਾਈਟ/ਈਵੈਂਟ** ਡਿਸਕ ਉੱਤੇ
(100k ਈਵੈਂਟ ਲਈ 67.7 MB), ਅਤੇ ਇੱਕ ਵਿਅਸਤ ਇੰਸਟਾਲ ਉੱਤੇ ਲਗਾਤਾਰ **ਇੱਕ ਕੋਰ ਦਾ ~12%**। ਇਹ ਆਖਰੀ ਸੰਖਿਆ
ਸਾਡੇ ਖੁਦ ਦੇ ਦੱਸੇ 5-10% ਬਜਟ ਤੋਂ ਵੱਧ ਹੈ, ਇਸ ਲਈ ਇਸਨੂੰ ਸਫ਼ੇ ਤੋਂ ਹਟਾਉਣ ਦੀ ਬਜਾਏ
ਪਿੱਛਾ ਕਰਨ ਵਾਲੇ ਬੱਗ ਵਜੋਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਗਿਆ ਹੈ।

Apple M2 Pro ਉੱਤੇ `benchmarks/overhead.py` ਨਾਲ ਮਾਪਿਆ ਗਿਆ। ਹਾਰਨੈਸ
ਹਰ ਸ਼ਰਤ ਨੂੰ ਵੱਖਰੀ ਪ੍ਰਕਿਰਿਆ ਵਿੱਚ ਚਲਾਉਂਦਾ ਹੈ, ਉਹਨਾਂ ਦੇ ਕ੍ਰਮ ਨੂੰ ਬਦਲਦਾ ਰਹਿੰਦਾ ਹੈ, ਅਤੇ **ਜਦੋਂ
ਗੇੜ ਇਸਦੇ ਚਿੰਨ੍ਹ ਉੱਤੇ ਸਹਿਮਤ ਨਹੀਂ ਹੁੰਦੇ ਤਾਂ ਸੰਖਿਆ ਛਾਪਣ ਤੋਂ ਇਨਕਾਰ ਕਰਦਾ ਹੈ**। ਇਸਨੂੰ ਆਪਣੀ
ਮਸ਼ੀਨ ਉੱਤੇ ਇੱਕ ਮਿੰਟ ਵਿੱਚ ਚਲਾਓ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ਹਰ ਰਸਤਾ ਮਾਪਿਆ ਗਿਆ ਹੈ, ਹੁੱਕ ਗੇਟ ਅਤੇ ਲਾਗੂਕਰਨ ਪ੍ਰੌਕਸੀ ਸਮੇਤ,
ਅਤੇ ਹਾਰਨੈਸ Linux, macOS ਅਤੇ Windows ਉੱਤੇ CI ਵਿੱਚ ਚੱਲਦਾ ਹੈ। ਜਾਣਨ ਯੋਗ ਦੋ ਨਤੀਜੇ: ਪ੍ਰੌਕਸੀ
Windows ਉੱਤੇ Linux ਨਾਲੋਂ ਲਗਭਗ ਸੱਤ ਗੁਣਾ ਵੱਧ ਖਰਚ ਕਰਦੀ ਹੈ, ਅਤੇ ਡੀਮਨ ਹੁਣ ਇੱਕ ਕੋਰ ਦੇ
ਲਗਭਗ 12% ਨੂੰ ਲਗਾਤਾਰ ਬਣਾਏ ਰੱਖਦਾ ਹੈ, ਜੋ ਸਾਡੇ ਖੁਦ ਦੇ 5-10% ਬਜਟ ਤੋਂ ਵੱਧ ਹੈ। ਕੱਚਾ JSON, ਵਿਧੀ, ਅਤੇ ਕੀ ਹਾਲੇ ਵੀ ਮਾਪਿਆ ਨਹੀਂ ਗਿਆ, ਇਹ ਸਭ
[docs/OVERHEAD.md](docs/OVERHEAD.md) ਵਿੱਚ ਹੈ।

## ਕੀਮਤ

| ਪਲਾਨ | ਇਸ ਵਿੱਚ ਕੀ ਸ਼ਾਮਲ ਹੈ | ਕੀਮਤ |
|---|---|---|
| **ਮੁਫ਼ਤ** | OpenClaw + NVIDIA NemoClaw + Goose, ਪੂਰਾ ਡੈਸ਼ਬੋਰਡ, ਸਿਰਫ਼ ਲੋਕਲ | $0 |
| **ਸਟਾਰਟਰ** | ਉੱਪਰ ਦਿੱਤਾ ਹਰ ਹੋਰ ਰਨਟਾਈਮ, ਫਲੀਟ ਵਿਊ, ਕਲਾਊਡ ਸਿੰਕ | $9 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |
| **Pro** | ਸਟਾਰਟਰ + ਕੰਟਰੋਲ ਅਤੇ ਮੁਲਾਂਕਣ: ਪ੍ਰਵਾਨਗੀਆਂ, ਟੂਲ-ਖ਼ਤਰਾ ਨੀਤੀਆਂ, ਈਵਲ, ਵਿਗਾੜ ਖੋਜ, ਲਾਗਤ ਓਪਟੀਮਾਈਜ਼ਰ, OTel ਐਕਸਪੋਰਟ, ਟੈਂਪਰ-ਇਵੀਡੈਂਟ ਆਡਿਟ ਲੌਗ | $19 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |

ਸਾਲਾਨਾ ਪਲਾਨ, Enterprise ਅਤੇ ਮੌਜੂਦਾ ਸੰਖਿਆਵਾਂ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ਉੱਤੇ ਮਿਲਦੀਆਂ ਹਨ। ਸੈਲਫ-ਹੋਸਟਡ ਲਾਇਸੈਂਸ
ਕੁੰਜੀਆਂ ਕਲਾਊਡ ਤੋਂ ਬਿਨਾਂ ਕੰਮ ਕਰਦੀਆਂ ਹਨ (`clawmetry license`)। ਸਹੀ ਮੁਫ਼ਤ/ਭੁਗਤਾਨ ਵੰਡ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਵਿੱਚ ਹੈ।

## ਤੁਹਾਡਾ ਡਾਟਾ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਉੱਤੇ ਹੀ ਰਹਿੰਦਾ ਹੈ

ClawMetry ਲੋਕਲ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਅਤੇ ਲੌਗ ਪੜ੍ਹਦਾ ਹੈ। **ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ `clawmetry connect`
ਨਹੀਂ ਚਲਾਉਂਦੇ, ਕੋਈ ਸੈਸ਼ਨ ਡਾਟਾ ਤੁਹਾਡੇ ਬੌਕਸ ਤੋਂ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦਾ** — ਕੋਈ ਪ੍ਰੌਂਪਟ, ਜਵਾਬ, ਟੂਲ ਆਰਗੂਮੈਂਟ, ਫਾਈਲ
ਸਮੱਗਰੀ ਜਾਂ ਲੌਗ ਲਾਈਨਾਂ ਨਹੀਂ। ਜਦੋਂ ਤੁਸੀਂ ਕਨੈਕਟ ਕਰਦੇ ਹੋ, ਸਨੈਪਸ਼ਾਟ ਇੱਕ ਕੁੰਜੀ ਨਾਲ ਐਂਡ-ਟੂ-ਐਂਡ ਇਨਕ੍ਰਿਪਟਡ
ਹੁੰਦਾ ਹੈ ਜੋ ਕਦੇ ਵੀ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦੀ, ਅਤੇ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਡੀਕ੍ਰਿਪਟ ਹੁੰਦਾ ਹੈ। ਜੇ ਕਿਸੇ
ਨੋਡ ਕੋਲ ਕੁੰਜੀ ਨਹੀਂ ਹੈ, ਤਾਂ ਅਪਲੋਡ ਬਿਨਾਂ ਇਨਕ੍ਰਿਪਸ਼ਨ ਭੇਜੇ ਜਾਣ ਦੀ ਬਜਾਏ ਛੱਡ ਦਿੱਤਾ ਜਾਂਦਾ ਹੈ, ਅਤੇ ਕੋਈ ਵੀ
ਸਰਵਰ ਜਵਾਬ ਇਸਨੂੰ ਬੰਦ ਨਹੀਂ ਕਰ ਸਕਦਾ।

ਕਨੈਕਟ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਦੋ ਚੀਜ਼ਾਂ ਡਿਫਾਲਟ ਰੂਪ ਵਿੱਚ ਚੱਲਦੀਆਂ ਹਨ, ਦੋਵੇਂ ਆਪਟ-ਆਊਟ ਅਤੇ ਕੋਈ ਵੀ
ਸੈਸ਼ਨ ਡਾਟਾ ਨਹੀਂ ਲੈ ਕੇ ਜਾਂਦੀਆਂ: ਇੱਕ ਗੁਮਨਾਮ ਇੰਸਟਾਲ ਪਿੰਗ ਅਤੇ PyPI ਦੇ ਵਿਰੁੱਧ ਇੱਕ ਵਰਜ਼ਨ
ਚੈੱਕ। ਇੱਕ ਡਿਫਾਲਟ ਇੰਸਟਾਲ ਸਟਾਰਟਅੱਪ ਬੈਨਰ ਲਾਈਨ ਲਈ ਇੱਕ ਵਾਰ ਤੁਹਾਡਾ ਜਨਤਕ IP ਵੀ ਲੁੱਕਅੱਪ ਕਰਦਾ ਹੈ। ਹਰ ਮੰਜ਼ਿਲ, ਇਹ ਕੀ ਲੈ ਕੇ ਜਾਂਦੀ ਹੈ ਅਤੇ ਇਸਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰਨਾ ਹੈ, ਇਹ ਸਭ
[docs/EGRESS.md](docs/EGRESS.md) ਵਿੱਚ ਸੂਚੀਬੱਧ ਹੈ; ਸੈਲਫ-ਹੋਸਟਡ, ਰੀਪੌਇੰਟਡ ਅਤੇ ਏਅਰ-ਗੈਪਡ ਇੰਸਟਾਲ
ਬਿਲਕੁਲ ਕੋਈ ਵਿਵੇਕਾਧੀਨ ਬਾਹਰੀ ਕਾਲ ਨਹੀਂ ਕਰਦੇ।

ਡੀਕ੍ਰਿਪਸ਼ਨ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ, ਉਸ ਕੋਡ ਵਿੱਚ ਹੁੰਦੀ ਹੈ ਜੋ ਅਸੀਂ ਤੁਹਾਨੂੰ ਦਿੰਦੇ ਹਾਂ। ਇਹ ਪਹਿਲਾਂ
ਇੱਕ ਵਾਅਦਾ ਸੀ; ਹੁਣ ਇਹ ਅਜਿਹੀ ਚੀਜ਼ ਹੈ ਜੋ ਤੁਸੀਂ ਚੈੱਕ ਕਰ ਸਕਦੇ ਹੋ। ਹਰ ਲਾਈਨ ਜੋ ਤੁਹਾਡੀ ਕੁੰਜੀ ਨੂੰ ਛੂੰਹਦੀ ਹੈ
ਇੱਕ ਪੜ੍ਹਨਯੋਗ ਫਾਈਲ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), ਵਿੱਚ ਰਹਿੰਦੀ ਹੈ,
ਜੋ ਵ੍ਹੀਲ ਦੇ ਅੰਦਰ ਸ਼ਿਪ ਹੁੰਦੀ ਹੈ ਅਤੇ ਜਿਵੇਂ ਦੀ ਤਿਵੇਂ ਸਰਵ ਕੀਤੀ ਜਾਂਦੀ ਹੈ, Subresource
Integrity ਹੈਸ਼ ਨਾਲ ਪਿੰਨ ਕੀਤੀ ਗਈ। ਇਹ ਤਸਦੀਕ ਕਰਨ ਲਈ ਕਿ ਬ੍ਰਾਊਜ਼ਰ ਉਹੀ ਚਲਾਉਂਦਾ ਹੈ ਜੋ ਅਸੀਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਸੀ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ਇਹ ਕੀ ਸਾਬਤ ਨਹੀਂ ਕਰਦਾ: ਅਸੀਂ ਉਹ ਸਫ਼ਾ ਸਰਵ ਕਰਦੇ ਹਾਂ ਜੋ ਫਾਈਲ ਲੋਡ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ ਅਸੀਂ
ਵੱਖਰਾ ਸਫ਼ਾ ਸਰਵ ਕਰ ਸਕਦੇ ਹਾਂ। Integrity ਹੈਸ਼ ਤੁਹਾਨੂੰ ਇੱਕ ਸਮਝੌਤਾ ਕੀਤੇ CDN ਤੋਂ ਬਚਾਉਂਦੇ ਹਨ,
ਵੈਂਡਰ ਤੋਂ ਨਹੀਂ। ਤੁਹਾਨੂੰ ਜੋ ਮਿਲਦਾ ਹੈ ਉਹ ਇਹ ਹੈ ਕਿ ਕੋਈ ਵੀ ਬਦਲਾਵ ਜਾਣਬੁੱਝ ਕੇ, ਸਫ਼ੇ ਦੇ
ਸੋਰਸ ਵਿੱਚ ਦਿਖਣਯੋਗ, ਅਤੇ PyPI ਉੱਤੇ ਮੌਜੂਦ ਆਰਟੀਫੈਕਟ ਤੋਂ ਵੱਖਰਾ ਹੋਣਾ ਚਾਹੀਦਾ ਹੈ
ਜਿਸਨੂੰ ਕੋਈ ਵੀ ਲਿਆ ਸਕਦਾ ਹੈ। ਸੈਲਫ-ਹੋਸਟਿੰਗ ਜਾਂ ਸਿਰਫ਼-ਲੋਕਲ ਰਹਿਣਾ ਇਸ ਨਿਰਭਰਤਾ ਨੂੰ ਪੂਰੀ ਤਰ੍ਹਾਂ
ਹਟਾ ਦਿੰਦਾ ਹੈ।

## ਇੰਸਟਾਲ

```bash
pip install clawmetry     # ਫਿਰ: clawmetry
```

ਜਾਂ ਇੱਕ-ਲਾਈਨਰ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ਜਾਂ Windows ਉੱਤੇ Python 3.8+ ਦੀ ਲੋੜ ਹੈ, ਅਤੇ ਉਸੇ ਮਸ਼ੀਨ ਉੱਤੇ ਘੱਟੋ-ਘੱਟ ਇੱਕ ਏਜੰਟ ਰਨਟਾਈਮ। Docker ਹਦਾਇਤਾਂ: [docs/DOCKER.md](docs/DOCKER.md)।

ਜਾਂ ਏਜੰਟ ਨੂੰ ਤੁਹਾਡੇ ਲਈ ਸੈੱਟ ਅੱਪ ਕਰਨ ਦਿਓ। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ਸਕਿੱਲ Claude Code, Codex, Cursor, Gemini CLI, Copilot ਜਾਂ OpenCode ਨੂੰ
ClawMetry ਇੰਸਟਾਲ ਕਰਨਾ, ਮਸ਼ੀਨ ਉੱਤੇ ਏਜੰਟ ਕੀ ਕਰ ਰਹੇ ਹਨ ਅਤੇ ਕਿੰਨਾ ਖਰਚ ਕਰ ਰਹੇ ਹਨ ਦੀ ਰਿਪੋਰਟ ਕਰਨਾ,
ਬੇਨਤੀ ਉੱਤੇ ਇੱਕ ਸੈਸ਼ਨ ਰੋਕਣਾ, ਅਤੇ ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਪ੍ਰਵਾਨਗੀ ਲਈ ਰੋਕਣਾ ਸਿਖਾਉਂਦੀ ਹੈ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ਦਸਤਾਵੇਜ਼

| | |
|---|---|
| [ਰਨਟਾਈਮ ਅਨੁਕੂਲਤਾ](docs/compatibility.md) | ਹਰ ਅਡੈਪਟਰ ਕੀ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਇੱਕ ਰਨਟਾਈਮ ਕਿਵੇਂ ਜੋੜਨਾ ਹੈ |
| [ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ](docs/CONTEXT_BLOWOUT.md) | ਪ੍ਰੋਵਾਈਡਰ-ਵਾਰ ਵਿੰਡੋ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਓਵਰਫਲੋਅ, ਰਨਟਾਈਮ-ਵਾਰ ਕਵਰੇਜ |
| [ਓਵਰਹੈੱਡ](docs/OVERHEAD.md) | ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਲਾਗਤ ਕੀ ਹੈ, ਮਾਪੀ ਗਈ, ਇਸਨੂੰ ਦੁਬਾਰਾ ਪੈਦਾ ਕਰਨ ਲਈ ਹਾਰਨੈਸ ਸਮੇਤ |
| [ਹੱਕਦਾਰੀਆਂ](docs/ENTITLEMENTS.md) | ਮੁਫ਼ਤ ਬਨਾਮ ਭੁਗਤਾਨ ਯੋਗ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, ਲਾਇਸੈਂਸ CLI |
| [ਪ੍ਰਵਾਨਗੀਆਂ ਅਤੇ ਨੀਤੀਆਂ](docs/APPROVALS.md) | ਪ੍ਰੀ-ਐਗਜ਼ੀਕਿਊਸ਼ਨ ਗੇਟਿੰਗ, ਖ਼ਤਰਾ ਸਕੋਰਿੰਗ, ਫੋਨ ਪ੍ਰਵਾਨਗੀਆਂ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ਕਿਤੇ ਵੀ ਟਰੇਸ ਐਕਸਪੋਰਟ ਕਰੋ, ਕਿਸੇ ਵੀ ਥਾਂ ਤੋਂ OTLP ਇਨਜੈਸਟ ਕਰੋ |
| [ਆਪਣਾ ਏਜੰਟ ਲਿਆਓ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ਸ਼ੁਰੂ ਤੋਂ ਅੰਤ ਤੱਕ, ਚਲਾਉਣਯੋਗ ਉਦਾਹਰਣਾਂ ਸਮੇਤ |
| [SDK ਟਰੈਕਿੰਗ](docs/SDK_TRACKING.md) | ਤੁਹਾਡੇ ਖੁਦ ਦੇ ਬਣਾਏ ਏਜੰਟਾਂ ਲਈ ਲਾਗਤ ਐਟ੍ਰੀਬਿਊਸ਼ਨ |
| [ਚੈਟ ਚੈਨਲ](docs/CHANNELS.md) | ਫਲੋ ਵਿੱਚ ਦਿਖਾਏ ਗਏ ਚੈਟ ਅਡੈਪਟਰ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ਸੈਂਡਬਾਕਸਡ NVIDIA NemoClaw ਸੈੱਟਅੱਪ |
| [Docker](docs/DOCKER.md) | ਇਮੇਜ, ਕੰਪੋਜ਼, ਵਾਲੀਅਮ ਮਾਊਂਟ |
| [ਆਰਕੀਟੈਕਚਰ](ARCHITECTURE.md) · [ਵਿਕਾਸ](docs/DEVELOPMENT.md) | ਅੰਦਰੋਂ ਇਹ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ; ਸੋਰਸ ਤੋਂ ਚਲਾਉਣਾ |
| [ਟੈਲੀਮੈਟਰੀ](docs/TELEMETRY.md) | ਗੁਮਨਾਮ ਇੰਸਟਾਲ ਅਤੇ ਡੈਸਕਟਾਪ-ਓਪਨ ਪਿੰਗ, ਅਤੇ ਇਹਨਾਂ ਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰਨਾ ਹੈ |

## ਸਕ੍ਰੀਨਸ਼ਾਟ

ਹੇਠਾਂ ਦਿੱਤਾ ਹਰ ਅੰਕੜਾ ਇੱਕ ਅਸਲੀ ਮਸ਼ੀਨ ਤੋਂ ਹੈ, ਸਿਰਫ਼-ਪੜ੍ਹਨ ਲਈ, ਬਿਨਾਂ ਕੁਝ ਬੀਜੇ।

**ਇਹ ਦੱਸਦਾ ਹੈ ਕਿ ਕਦੋਂ ਕੁਝ ਗਲਤ ਹੈ, ਸਿਰਫ਼ ਕੀ ਹੋਇਆ ਇਹ ਨਹੀਂ।**
ਸਿਖਰ ਉੱਤੇ ਦੋ ਵਿਗਾੜ ਬੈਨਰ: ਖਰਚ ਰੋਜ਼ਾਨਾ ਔਸਤ ਦਾ 7 ਗੁਣਾ ਚੱਲ ਰਿਹਾ ਹੈ, ਅਤੇ ਇੱਕ
4.2 ਗੁਣਾ ਲਾਗਤ ਸਪਾਈਕ। ਉਹਨਾਂ ਦੇ ਹੇਠਾਂ, ਹਾਲ ਹੀ ਦੇ 667 ਸੈਸ਼ਨਾਂ ਵਿੱਚੋਂ 324 ਵਿੱਚ
ਬਰਬਾਦੀ ਸਿਗਨਲ ਹੈ, ਕਾਰਨ ਦੇ ਹਿਸਾਬ ਨਾਲ ਸੂਚੀਬੱਧ।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ਇਹ ਤੁਹਾਨੂੰ ਦਿਖਾਉਂਦਾ ਹੈ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਹਰ ਵਿੰਡੋ ਵਿੱਚ।**
ਅੱਜ $252.47, ਇਸ ਹਫ਼ਤੇ $513.15, ਇਸ ਮਹੀਨੇ $1,312.92, ਹਰ ਇੱਕ ਪਿੱਛੇ
ਟੋਕਨਾਂ ਸਮੇਤ ਅਤੇ ਤੁਹਾਡੀ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਪਹਿਲਾਂ ਹੀ ਕਿੰਨਾ ਕਵਰ ਕਰਦੀ ਹੈ। ਉਸ ਹੇਠਾਂ, ਲਗਭਗ $1,128/ਮਹੀਨਾ
ਰਿਕਵਰੇਬਲ ਵਜੋਂ ਸੂਚੀਬੱਧ ਅਤੇ ਕੈਸ਼ ਦੁਬਾਰਾ ਵਰਤੋਂ ਨਾਲ ਪਹਿਲਾਂ ਹੀ $17,256/ਮਹੀਨਾ ਬਚਾਏ ਗਏ।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਸੁਨੇਹਾ ਕਿਵੇਂ ਜਵਾਬ ਬਣਦਾ ਹੈ।**
ਲਾਈਵ ਫਲੋ ਡਾਇਗਰਾਮ: ਤੁਸੀਂ, ਉਹ ਚੈਨਲ ਜਿਸ ਉੱਤੇ ਇਹ ਪਹੁੰਚਿਆ, ਗੇਟਵੇ, ਹੁਣੇ
ਜਵਾਬ ਦੇ ਰਿਹਾ ਮਾਡਲ, ਅਤੇ ਹਰ ਟੂਲ ਜਿਸ ਲਈ ਇਸਨੇ ਹੱਥ ਵਧਾਇਆ। ਕੰਮ ਲੰਘਦੇ ਸਮੇਂ
ਨੋਡ ਰੌਸ਼ਨ ਹੁੰਦੇ ਹਨ।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ਮਸ਼ੀਨ ਉੱਤੇ ਹਰ ਏਜੰਟ, ਇੱਕ ਟੇਬਲ ਵਿੱਚ।**
ਇਹ ਕੀ ਚਲਾਉਂਦਾ ਹੈ, ਪਿਛਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ਅਤੇ ਆਪਣੇ ਪੂਰੇ ਸਮੇਂ ਵਿੱਚ ਕੀ ਖਰਚ ਹੋਇਆ, ਕਦੋਂ
ਆਖਰੀ ਵਾਰ ਦੇਖਿਆ ਗਿਆ, ਇਸਦਾ ਮਾਲਕ ਕੌਣ ਹੈ, ਅਤੇ ਕੀ ਕੋਈ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਬਿੱਲ ਨੂੰ ਕਵਰ ਕਰ ਰਹੀ ਹੈ। ਇੱਥੇ 14 ਏਜੰਟ, 3 ਸੈਸ਼ਨ ਕੰਮ ਕਰ ਰਹੇ, 13 ਸ਼ਾਂਤ।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਵਾਰੀ ਦਾ ਸਮਾਂ ਅਤੇ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਟੂਲ-ਦਰ-ਟੂਲ।**
ਇੱਕ ਅਸਲੀ ਸੈਸ਼ਨ ਦੀ ਇੱਕ ਵਾਰੀ: $1.16 ਵਿੱਚ 11.2 ਮਿੰਟਾਂ ਵਿੱਚ 11 ਟੂਲ। ਹਰ Bash
ਕਾਲ ਅਤੇ ਮਾਡਲ ਕਾਲ ਨੂੰ ਟਾਈਮਲਾਈਨ ਉੱਤੇ ਆਪਣੀ ਬਾਰ ਮਿਲਦੀ ਹੈ, ਇਸ ਲਈ ਜਿਹੜੀ ਕਮਾਂਡ
4.1 ਮਿੰਟ ਚੱਲੀ ਅਤੇ ਜਿਹੜੀ 226ms ਚੱਲੀ, ਦੋਵੇਂ ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਵੱਖਰੀਆਂ ਦੱਸੀਆਂ ਜਾਂਦੀਆਂ ਹਨ।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ਇਹ ਕੰਮ ਨੂੰ ਗ੍ਰੇਡ ਕਰਦਾ ਹੈ, ਸਿਰਫ਼ ਖਰਚ ਨੂੰ ਨਹੀਂ।**
ਇਸ ਹਫ਼ਤੇ ਇੱਕ A: 54 ਕੰਮ ਸਾਫ਼ ਵਾਪਸ ਆਏ, 2 ਰੁੱਖੇ ਰਨਾਂ ਦੀ ਕੀਮਤ $48.57 ਰਹੀ, ਅਤੇ
ਬਹੁਤ ਘੱਟ ਗਤੀਵਿਧੀ ਵਾਲੇ ਰਨ, ਜਿੰਨ੍ਹਾਂ ਦਾ ਨਿਰਣਾ ਨਹੀਂ ਕੀਤਾ ਜਾ ਸਕਦਾ, ਜਿੱਤਾਂ ਵਜੋਂ ਗਿਣੇ ਜਾਣ ਦੀ ਬਜਾਏ ਗ੍ਰੇਡ ਵਿੱਚੋਂ ਬਾਹਰ ਛੱਡ ਦਿੱਤੇ ਜਾਂਦੇ ਹਨ। ਹਰ ਰੁੱਖਾ ਰਨ ਆਪਣੇ ਟਰੇਸ ਨਾਲ ਲਿੰਕ ਹੁੰਦਾ ਹੈ।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਕੌਂਟੈਕਸਟ ਵਿੰਡੋ ਲਗਾਤਾਰ ਕਿਉਂ ਭਰਦੀ ਰਹਿੰਦੀ ਹੈ।**
1M-ਟੋਕਨ ਵਿੰਡੋ ਵਿੱਚੋਂ 715K ਆਖਰੀ ਵਾਰੀ ਉੱਤੇ, 83.3% ਦੀ ਸਿਖਰ, 4 ਕੰਪੈਕਸ਼ਨ
ਜੋ ਸਭ ਓਵਰਫਲੋਅ ਦੀ ਬਜਾਏ ਪ੍ਰੋਐਕਟਿਵ ਤੌਰ ਤੇ ਫਾਇਰ ਹੋਈਆਂ, ਅਤੇ ਉਸ ਪਿੱਛੇ ਹਰ ਵਾਰੀ ਦੀ ਵਰਤੋਂ।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ਖੋਜ ਬਿਨਾਂ ਤੁਹਾਡੇ ਕੁਝ ਕੌਂਫਿਗਰ ਕੀਤੇ ਚੱਲਦੀ ਹੈ।**
ਬਿਲਟ-ਇਨ ਡਿਟੈਕਟਰ ਇੰਸਟਾਲ ਤੋਂ ਹੀ ਚਾਲੂ ਹਨ: ਏਜੰਟ ਸ਼ਾਂਤ ਹੋ ਗਿਆ, ਟੈਲੀਮੈਟਰੀ ਫੀਡ
ਬੰਦ ਹੋ ਗਈ, ਲਾਗਤ ਸਪਾਈਕ, ਟੋਕਨ ਬਰਸਟ, ਵਧਦੀਆਂ ਗਲਤੀਆਂ, ਗਲਤੀ ਸਪਾਈਕ, ਬਜਟ
ਥ੍ਰੈਸ਼ਹੋਲਡ, ਖ਼ਤਰਾ ਦਸਤਖਤ ਮੇਲ ਖਾਧਾ, ਸੁਰੱਖਿਆ ਟੂਲ ਖੋਜ, ਸੁਰੱਖਿਆ ਸਥਿਤੀ
ਬਦਲੀ। ਤੁਹਾਡੇ ਖੁਦ ਦੇ ਨਿਯਮ ਇਸ ਉੱਤੇ ਵਿਕਲਪਿਕ ਹਨ।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ਖ਼ਤਰਨਾਕ ਕਾਲ ਨੂੰ ਰੋਕਣਾ ਆਪਟ-ਇਨ ਹੈ, ਅਤੇ ਬੰਦ ਭੇਜਿਆ ਜਾਂਦਾ ਹੈ।**
ਰੀਕਰਸਿਵ ਡਿਲੀਟ, ਫੋਰਸ ਪੁਸ਼, sudo, ਗੁਪਤ ਜਾਣਕਾਰੀ, ਪੈਕੇਜ ਇੰਸਟਾਲ ਅਤੇ ਬਾਹਰ ਜਾਣ ਵਾਲੀਆਂ
ਕਾਲਾਂ ਹਰ ਇੱਕ ਨੂੰ ਇੱਕ ਨਿਯਮ ਮਿਲਦਾ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਚਾਲੂ ਕਰ ਸਕਦੇ ਹੋ। ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ ਨਹੀਂ ਕਰਦੇ, ClawMetry ਦੇਖਦਾ ਹੈ ਅਤੇ
ਕੁਝ ਨਹੀਂ ਬਦਲਦਾ। ਇੱਕ ਵਾਰ ਚਾਲੂ ਹੋ ਜਾਵੇ, ਮੇਲ ਖਾਂਦੀਆਂ ਕਾਲਾਂ ਇੱਥੇ (ਜਾਂ ਤੁਹਾਡੇ ਫੋਨ ਉੱਤੇ)
ਮਨਜ਼ੂਰੀ ਜਾਂ ਇਨਕਾਰ ਲਈ ਉਡੀਕ ਕਰਦੀਆਂ ਹਨ।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ਹੋਰ, ਰਨਟਾਈਮ-ਵਾਰ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## ਪਛਾਣ

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star ਇਤਿਹਾਸ

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ਲਾਇਸੈਂਸ

MIT · [@vivekchand](https://github.com/vivekchand) ਦੁਆਰਾ ਬਣਾਇਆ ਗਿਆ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
