<!-- i18n-src:12b97259721e -->
> ਪੰਜਾਬੀ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ਇੱਕ ਏਜੰਟ ਬਿਨਾਂ ਕਿਸੇ ਤਰੱਕੀ ਦੇ ਸੌ ਟੂਲ ਕਾਲਾਂ ਕਰ ਸਕਦਾ ਹੈ।** ClawMetry
ਤੁਹਾਡੇ ਕੋਡਿੰਗ ਏਜੰਟ ਪਹਿਲਾਂ ਹੀ ਲਿਖੀਆਂ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਟਾਈਮਲਾਈਨ,
ਟੂਲ ਕਾਲਾਂ ਅਤੇ ਰਨਟਾਈਮ ਵੱਲੋਂ ਦਿੱਤਾ ਗਿਆ ਟੋਕਨ ਅਤੇ ਲਾਗਤ ਡਾਟਾ ਇੱਕੋ
ਵਿਊ ਵਿੱਚ ਰੱਖਦਾ ਹੈ — ਤਾਂ ਜੋ ਤੁਸੀਂ ਦੱਸ ਸਕੋ ਕਿ ਕਿਹੜਾ ਲੰਬਾ ਰਨ ਕੰਮ ਕਰ ਰਿਹਾ ਹੈ
ਅਤੇ ਕਿਹੜਾ ਅਟਕਿਆ ਹੋਇਆ ਹੈ।

**31 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ — Claude Code, OpenAI Codex, Hermes, OpenClaw ਅਤੇ 27 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ। ([ਪੂਰੀ ਸੂਚੀ](SUPPORTED_RUNTIMES.txt), ਕੈਟਾਲਾਗ ਤੋਂ ਬਣੀ।)

> 🌐 **ਇਸਨੂੰ ਇਹਨਾਂ ਭਾਸ਼ਾਵਾਂ ਵਿੱਚ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ। ਹਰ ਚੀਜ਼ ਖੁਦ-ਬ-ਖੁਦ ਲੱਭਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 'ਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ: ਇਹ ਉਹ ਏਜੰਟ ਰਨਟਾਈਮ
ਲੱਭ ਲੈਂਦਾ ਹੈ ਜੋ ਤੁਹਾਡੇ ਕੋਲ ਪਹਿਲਾਂ ਤੋਂ ਹਨ, ਉਹਨਾਂ ਨੂੰ ਸਿਰਫ਼ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ
ਉਹ ਕਿਵੇਂ ਚੱਲਦੇ ਹਨ ਉਸ ਵਿੱਚ ਕੁਝ ਨਹੀਂ ਬਦਲਦਾ।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ਇੰਸਟਾਲ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ

| | |
|---|---|
| **ਇਹ ਕੀ ਕਰਦਾ ਹੈ** | ਤੁਹਾਡੇ ਏਜੰਟ ਪਹਿਲਾਂ ਹੀ ਲਿਖੀਆਂ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਅਤੇ ਲੌਗ ਪੜ੍ਹਦਾ ਹੈ। ਕੋਈ SDK ਨਹੀਂ, ਕੋਈ ਕੋਡ ਬਦਲਾਅ ਨਹੀਂ, ਤੁਹਾਡੀ ਐਪ ਵਿੱਚ ਕੋਈ ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਨਹੀਂ। |
| **ਤੁਸੀਂ ਕੀ ਦੇਖਦੇ ਹੋ** | ਸੈਸ਼ਨ ਟਾਈਮਲਾਈਨ, ਟੂਲ-ਦਰ-ਟੂਲ ਰੀਪਲੇਅ, ਟੋਕਨ ਅਤੇ ਲਾਗਤ ਦਾ ਵੇਰਵਾ, ਅਤੇ ਟ੍ਰੈਜੈਕਟਰੀ ਸੰਕੇਤ (ਲੂਪਿੰਗ, ਵਾਰ-ਵਾਰ ਫੇਲ੍ਹ ਹੋਣਾ) — ਹਰ ਰਨਟਾਈਮ ਲਈ। |
| **ਕੀ ਮੁਫ਼ਤ ਹੈ** | `pip install clawmetry` **OpenClaw, NVIDIA NemoClaw ਅਤੇ Goose** ਨੂੰ ਬਿਨਾਂ ਕਿਸੇ ਖਾਤੇ, ਕੁੰਜੀ ਜਾਂ ਨੈੱਟਵਰਕ ਕਾਲ ਦੇ ਪੜ੍ਹਦਾ ਹੈ। ਬਾਕੀ 27 — Claude Code, Codex, Cursor ਅਤੇ ਬਾਕੀ — ਕਲੋਜ਼ਡ-ਸੋਰਸ `clawmetry-pro` ਕੰਪੈਨੀਅਨ ਰਾਹੀਂ ਪੜ੍ਹੇ ਜਾਂਦੇ ਹਨ, ਜੋ 7-ਦਿਨ ਦੇ ਟ੍ਰਾਇਲ ਜਾਂ ਪਲਾਨ ਨਾਲ ਆਉਂਦਾ ਹੈ — ਸਹੀ ਵੰਡ ਲਈ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਦੇਖੋ। |
| **ਕਿਵੇਂ ਸ਼ੁਰੂ ਕਰੀਏ** | `pip install clawmetry && clawmetry`, ਫਿਰ localhost:8900 ਖੋਲ੍ਹੋ। ਇਸ ਮਸ਼ੀਨ 'ਤੇ ਹਾਲੇ ਕੋਈ ਏਜੰਟ ਨਹੀਂ? `clawmetry --sample` ਤਿੰਨ ਲੇਬਲ ਵਾਲੇ ਸਿੰਥੈਟਿਕ ਸੈਸ਼ਨਾਂ ਨਾਲ ਖੁੱਲ੍ਹਦਾ ਹੈ। |
| **ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਕੀ ਬਾਹਰ ਜਾਂਦਾ ਹੈ** | ਕੋਈ ਸੈਸ਼ਨ ਡਾਟਾ ਨਹੀਂ, ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ ਚਲਾਉਂਦੇ। ਦੋ ਚੀਜ਼ਾਂ ਡਿਫੌਲਟ ਤੌਰ 'ਤੇ ਚਲਦੀਆਂ ਹਨ, ਦੋਵੇਂ ਬੰਦ ਕੀਤੀਆਂ ਜਾ ਸਕਦੀਆਂ ਹਨ ਅਤੇ ਕੋਈ ਵੀ ਸੈਸ਼ਨ ਸਮੱਗਰੀ ਨਹੀਂ ਲੈ ਜਾਂਦੀ: ਇੱਕ ਗੁਮਨਾਮ ਇੰਸਟਾਲ ਪਿੰਗ ਅਤੇ ਇੱਕ PyPI ਵਰਜਨ ਚੈੱਕ। ਹਰ ਟਿਕਾਣਾ [docs/EGRESS.md](docs/EGRESS.md) ਵਿੱਚ ਸੂਚੀਬੱਧ ਹੈ, ਜੋ ਟਿੱਪਣੀਆਂ ਪੜ੍ਹ ਕੇ ਨਹੀਂ ਸਗੋਂ ਵਾਇਰ ਕੈਪਚਰ ਤੋਂ ਬਣਾਇਆ ਗਿਆ ਹੈ। |

ਇੰਸਟਾਲ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਦੋ ਸੀਮਾਵਾਂ ਜਾਣਨਾ ਜ਼ਰੂਰੀ ਹੈ ਜਦੋਂ ਤੁਸੀਂ ਨਤੀਜੇ ਦਾ ਮੁਲਾਂਕਣ ਕਰੋ:
ਰਨਟਾਈਮ ਬਹੁਤ ਵੱਖੋ-ਵੱਖਰਾ ਡਾਟਾ ਦਿਖਾਉਂਦੇ ਹਨ (ਕੁਝ ਬਿਲਕੁਲ ਵੀ ਲਾਗਤ ਪ੍ਰਕਾਸ਼ਿਤ ਨਹੀਂ ਕਰਦੇ — [ਮੈਟ੍ਰਿਕਸ](docs/compatibility.md)
ਦੱਸਦਾ ਹੈ ਕਿ ਕਿਹੜਾ, ਹਰ ਰਨਟਾਈਮ ਲਈ), ਅਤੇ ਕਿਸੇ ਕਾਰਵਾਈ ਨੂੰ ਦੇਖਣਾ ਉਸਨੂੰ
ਰੋਕਣ ਦੇ ਸਮਰੱਥ ਹੋਣ ਦੇ ਬਰਾਬਰ ਨਹੀਂ ([ਕਿਹੜੇ ਕੰਟਰੋਲ ਅਸਲੀ ਹਨ, ਹਰ ਰਨਟਾਈਮ ਲਈ](docs/APPROVALS.md))।

## 31 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

**ਓਪਨ ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ਇੱਕ ਭੁਗਤਾਨ ਵਾਲੇ ਪਲਾਨ 'ਤੇ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ਹਰ ਰਨਟਾਈਮ ਨੂੰ ਇੱਕੋ ਡੈਸ਼ਬੋਰਡ ਮਿਲਦਾ ਹੈ। ਇੱਕੋ ਸਮੇਂ ਕਈ ਚਲਾਓ ਅਤੇ
ਹੈਡਰ ਸਵਿੱਚਰ ਹਰ ਟੈਬ ਨੂੰ ਉਹਨਾਂ ਵਿੱਚੋਂ ਇੱਕ 'ਤੇ ਮੁੜ-ਸਕੋਪ ਕਰ ਦਿੰਦਾ ਹੈ।

ਕੀ ਤੁਸੀਂ SDK 'ਤੇ ਆਪਣਾ ਖੁਦ ਦਾ ਏਜੰਟ ਬਣਾਇਆ ਹੈ? ਇੰਟਰਸੈਪਟਰ ਉਸਦੀਆਂ LLM ਕਾਲਾਂ ਵੀ
ਟ੍ਰੈਕ ਕਰਦਾ ਹੈ। [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ਦੇਖੋ।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **ਸੈਸ਼ਨ ਅਤੇ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ**: ਹਰ ਏਜੰਟ ਨੇ ਕੀ ਕੀਤਾ, ਵਾਰੀ-ਵਾਰੀ, ਰੀਪਲੇਅ ਸਮੇਤ
- **ਲਾਗਤ ਅਤੇ ਟੋਕਨ**: ਹਰ ਰਨਟਾਈਮ, ਮਾਡਲ, ਸੈਸ਼ਨ ਅਤੇ ਦਿਨ ਲਈ, ਅਸਧਾਰਨਤਾ ਦੇ ਫਲੈਗਾਂ ਸਮੇਤ
- **ਫਲੋ**: ਚੈਨਲਾਂ, ਮਾਡਲਾਂ ਅਤੇ ਟੂਲਾਂ ਵਿੱਚੋਂ ਦੀ ਲੰਘ ਰਹੇ ਸੁਨੇਹਿਆਂ ਦਾ ਲਾਈਵ ਡਾਇਗ੍ਰਾਮ
- **ਬ੍ਰੇਨ**: ਜਿਵੇਂ ਹੋ ਰਿਹਾ ਹੈ ਉਵੇਂ ਤਰਕ ਅਤੇ ਟੂਲ-ਕਾਲ ਈਵੈਂਟ ਸਟ੍ਰੀਮ
- **ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ**: ਹਰ ਪ੍ਰੋਵਾਈਡਰ ਲਈ ਵਿੰਡੋ ਵਰਤੋਂ ਦਾ ਆਕਾਰ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਜ਼ਬਰਦਸਤੀ ਓਵਰਫਲੋ, ਨਾਲ ਹੀ ਹਰ ਰਨਟਾਈਮ ਲਈ ਇਹ ਨਕਸ਼ਾ ਕਿ ਅਸੀਂ *ਕੀ ਨਹੀਂ* ਦੇਖ ਸਕਦੇ ([ਕਿਵੇਂ](docs/CONTEXT_BLOWOUT.md))
- **ਮੈਮੋਰੀ ਅਤੇ ਸਕਿੱਲ**: ਉਹ ਫਾਈਲਾਂ ਅਤੇ ਸਕਿੱਲ ਜੋ ਹਰ ਰਨਟਾਈਮ ਨੇ ਅਸਲ ਵਿੱਚ ਲੋਡ ਕੀਤੇ
- **ਸਿਹਤ ਅਤੇ ਲੌਗ**: ਡਿਸਕ, ਮੈਮੋਰੀ, ਗਲਤੀ ਦਰਾਂ, ਰੇਟ ਲਿਮਿਟਾਂ, ਲਾਈਵ ਲੌਗ ਸਟ੍ਰੀਮ
- **ਅਲਰਟ**: ਬਜਟ ਕੈਪ, ਗਲਤੀ ਸਪਾਈਕ, ਏਜੰਟ-ਆਫਲਾਈਨ, Slack, Discord, PagerDuty, Telegram, Email ਨੂੰ ਭੇਜੇ ਜਾਂਦੇ
- **ਪ੍ਰਵਾਨਗੀਆਂ**: ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਚੱਲਣ ਤੋਂ *ਪਹਿਲਾਂ* ਰੋਕੋ ਅਤੇ ਆਪਣੇ ਫ਼ੋਨ ਤੋਂ ਪ੍ਰਵਾਨਗੀ ਦਿਓ ([ਕਿਵੇਂ](docs/APPROVALS.md))

## ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ, ਅਤੇ ਨਿਗਰਾਨੀ ਦੀ ਲਾਗਤ

ਕਿਸੇ ਵੀ ਏਜੰਟ-ਤੁਲਨਾ ਟੂਲ 'ਤੇ ਭਰੋਸਾ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਦੋ ਸਵਾਲਾਂ ਦੇ ਜਵਾਬ ਦੇਣੇ ਜ਼ਰੂਰੀ ਹਨ।

**ਇਹ ਰਨਟਾਈਮਾਂ ਵਿੱਚ ਕੌਂਟੈਕਸਟ-ਵਿੰਡੋ ਬਲੋਆਊਟ ਨੂੰ ਕਿਵੇਂ ਹੈਂਡਲ ਕਰਦਾ ਹੈ?**

ਵਰਤੋਂ ਪ੍ਰਤੀਸ਼ਤ ਓਨਾ ਹੀ ਸਹੀ ਹੁੰਦਾ ਹੈ ਜਿੰਨਾ ਉਹ ਅੰਕ ਜਿਸ ਨਾਲ ਇਸਨੂੰ ਵੰਡਿਆ ਜਾਂਦਾ ਹੈ। ClawMetry
ਵਿੰਡੋ ਦਾ ਆਕਾਰ ਹਰ ਪ੍ਰੋਵਾਈਡਰ ਲਈ [ਇੱਕ ਟੇਬਲ ਤੋਂ ਲੈਂਦਾ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਪੜ੍ਹ ਸਕਦੇ ਹੋ ਅਤੇ
PR ਕਰ ਸਕਦੇ ਹੋ](clawmetry/context_windows.py), ਜੋ Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama ਅਤੇ GLM ਨੂੰ ਕਵਰ ਕਰਦਾ ਹੈ। ਇਹ ਸਾਰੇ 31
ਰਨਟਾਈਮਾਂ ਨੂੰ ਇੱਕ ਹੀ ਵੈਂਡਰ ਦੇ ਪੈਮਾਨੇ ਨਾਲ ਨਹੀਂ ਮਾਪਦਾ। ਇਹ ਮਾਇਨੇ ਰੱਖਦਾ ਹੈ: ਇੱਕ 300K GPT-5
ਵਾਰੀ ਨੂੰ Anthropic ਦੇ 200K ਦੇ ਵਿਰੁੱਧ ਮਾਪਿਆਂ ">100%, ਬਲੋਨ" ਪੜ੍ਹਿਆ ਜਾਂਦਾ ਹੈ ਜਦਕਿ ਇਹ ਅਸਲ ਵਿੱਚ
GPT-5 ਦੇ 400K ਦੇ 75% 'ਤੇ ਹੈ। ਉਹੀ ਪੈਮਾਨਾ ਇੱਕ ਸੱਚਮੁੱਚ ਓਵਰਫਲੋ ਹੋਈ 130K DeepSeek ਵਾਰੀ ਨੂੰ
ਇੱਕ ਆਰਾਮਦਾਇਕ 65% ਦੇ ਤੌਰ 'ਤੇ ਛੁਪਾ ਦਿੰਦਾ ਹੈ।

ਹਰ ਵਿੰਡੋ ਆਪਣੀ ਪ੍ਰੋਵੇਨੈਂਸ ਨਾਲ ਆਉਂਦੀ ਹੈ: `model_table`, `explicit_marker`,
`observed_floor`, ਜਾਂ ਜਦੋਂ ਸਾਨੂੰ ਮਾਡਲ ਨਹੀਂ ਪਤਾ ਤਾਂ ਇੱਕ ਇਮਾਨਦਾਰ `default`। ਅੰਦਾਜ਼ੇ 'ਤੇ
ਬਣਿਆ ਗੇਜ ਕਦੇ ਵੀ ਲੁੱਕਅਪ 'ਤੇ ਬਣੇ ਗੇਜ ਜਿੰਨੇ ਭਰੋਸੇ ਨਾਲ ਨਹੀਂ ਵਿਖਾਈ ਦਿੰਦਾ।

ClawMetry ਕੁਝ ਰਨਟਾਈਮਾਂ 'ਤੇ ਸਿਰਫ਼ ਕੰਪੈਕਸ਼ਨ ਈਵੈਂਟ ਹੀ ਦੇਖ ਸਕਦਾ ਹੈ। ਇਸ ਲਈ
`GET /api/context-coverage` ਹਰ ਰਨਟਾਈਮ ਲਈ ਦੱਸਦਾ ਹੈ ਕਿ ਕੀ ਇੱਕ **ਜ਼ੀਰੋ ਦਾ ਮਤਲਬ
"ਸਾਫ਼ ਚੱਲਿਆ" ਹੈ ਜਾਂ "ਸਾਨੂੰ ਦਿਖਦਾ ਨਹੀਂ"**। ਇੱਕ `0` ਜਿਸਦਾ ਅਸਲ ਵਿੱਚ ਮਤਲਬ ਅੰਨ੍ਹਾ ਹੈ, ਇਹ ਦੱਸਦਾ ਹੈ।
[ਪੂਰੀ ਜਾਣਕਾਰੀ](docs/CONTEXT_BLOWOUT.md)

**ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਕੀ ਲਾਗਤ ਹੈ?**

| ਪਾਥ | ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਜੋੜਿਆ ਗਿਆ | ਡਿਫੌਲਟ? |
|---|---|---|
| ਸੈਸ਼ਨ-ਫਾਈਲ ਟੇਲਿੰਗ (ਸਾਰੇ 31 ਰਨਟਾਈਮ) | **0**। ਵੱਖਰੀ ਪ੍ਰਕਿਰਿਆ, ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਕੋਈ ClawMetry ਕੋਡ ਨਹੀਂ | ਚਾਲੂ |
| HTTP ਇੰਟਰਸੈਪਟਰ (`CLAWMETRY_INTERCEPT=1`) | ਹਰ LLM ਕਾਲ ਲਈ **+0.44 ms**, ਜਾਂ 5s ਦੀ ਕਾਲ ਦਾ 0.009% | ਬੰਦ |
| ਪ੍ਰੀ-ਟੂਲ ਹੁੱਕ ਗੇਟ (ਗਰਮ ਕੈਸ਼) | 36 ms ਦੇ ਇੰਟਰਪ੍ਰੇਟਰ ਫ਼ਲੋਰ ਤੋਂ ਉੱਪਰ, ਹਰ ਗੇਟਿਡ ਟੂਲ ਕਾਲ ਲਈ **+44 ms** | ਬੰਦ |
| ਐਨਫੋਰਸਮੈਂਟ ਪ੍ਰੌਕਸੀ | ਹਰ LLM ਕਾਲ ਲਈ **+9.7 ms** | ਬੰਦ |

ਡੀਮਨ ਹੋਸਟ ਲਾਗਤ: **2,762 ਈਵੈਂਟ/ਸਕਿੰਟ** ਇਨਜੈਸਟ, ਡਿਸਕ 'ਤੇ **710 ਬਾਈਟ/ਈਵੈਂਟ**
(100k ਈਵੈਂਟਾਂ ਲਈ 67.7 MB), ਅਤੇ ਇੱਕ ਵਿਅਸਤ ਇੰਸਟਾਲ 'ਤੇ ਲਗਾਤਾਰ **ਇੱਕ ਕੋਰ ਦਾ ~12%**।
ਇਹ ਆਖ਼ਰੀ ਅੰਕੜਾ ਸਾਡੇ ਦੱਸੇ ਹੋਏ 5-10% ਦੇ ਬਜਟ ਤੋਂ ਉੱਪਰ ਹੈ, ਇਸ ਲਈ ਇਸਨੂੰ
ਲੁਕਾਉਣ ਦੀ ਬਜਾਏ ਲੱਭੇ ਜਾਣ ਵਾਲੇ ਬੱਗ ਵਜੋਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਗਿਆ ਹੈ।

Apple M2 Pro 'ਤੇ `benchmarks/overhead.py` ਨਾਲ ਮਾਪਿਆ ਗਿਆ। ਹਾਰਨੈੱਸ
ਹਰ ਹਾਲਤ ਨੂੰ ਇੱਕ ਵੱਖਰੀ ਪ੍ਰਕਿਰਿਆ ਵਿੱਚ ਚਲਾਉਂਦਾ ਹੈ, ਉਹਨਾਂ ਦਾ ਕ੍ਰਮ ਬਦਲਦਾ ਹੈ, ਅਤੇ
**ਜੇ ਗੇੜ ਚਿੰਨ੍ਹ 'ਤੇ ਸਹਿਮਤ ਨਾ ਹੋਣ ਤਾਂ ਕੋਈ ਅੰਕੜਾ ਨਹੀਂ ਦਿੰਦਾ**। ਇਸਨੂੰ ਆਪਣੀ
ਮਸ਼ੀਨ 'ਤੇ ਇੱਕ ਮਿੰਟ ਵਿੱਚ ਚਲਾਓ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ਹੁੱਕ ਗੇਟਾਂ ਅਤੇ ਐਨਫੋਰਸਮੈਂਟ ਪ੍ਰੌਕਸੀ ਸਮੇਤ ਹਰ ਪਾਥ ਮਾਪਿਆ ਗਿਆ ਹੈ,
ਅਤੇ ਹਾਰਨੈੱਸ CI ਵਿੱਚ Linux, macOS ਅਤੇ Windows 'ਤੇ ਚੱਲਦਾ ਹੈ। ਜਾਣਨਯੋਗ ਦੋ ਨਤੀਜੇ:
ਪ੍ਰੌਕਸੀ ਦੀ ਲਾਗਤ Windows 'ਤੇ Linux ਨਾਲੋਂ ਲਗਭਗ ਸੱਤ ਗੁਣਾ ਵੱਧ ਹੈ, ਅਤੇ
ਡੀਮਨ ਇਸ ਵੇਲੇ ਇੱਕ ਕੋਰ ਦਾ ਲਗਭਗ 12% ਲਗਾਤਾਰ ਵਰਤਦਾ ਹੈ, ਜੋ ਸਾਡੇ ਆਪਣੇ 5-10%
ਬਜਟ ਤੋਂ ਉੱਪਰ ਹੈ। ਕੱਚਾ JSON, ਤਰੀਕਾ, ਅਤੇ ਜੋ ਹਾਲੇ ਨਹੀਂ ਮਾਪਿਆ ਗਿਆ ਉਹ
[docs/OVERHEAD.md](docs/OVERHEAD.md) ਵਿੱਚ ਹੈ।

## ਕੀਮਤ

| ਪਲਾਨ | ਇਹ ਕੀ ਕਵਰ ਕਰਦਾ ਹੈ | ਕੀਮਤ |
|---|---|---|
| **ਮੁਫ਼ਤ** | OpenClaw + NVIDIA NemoClaw + Goose, ਪੂਰਾ ਡੈਸ਼ਬੋਰਡ, ਸਿਰਫ਼ ਲੋਕਲ | $0 |
| **ਸਟਾਰਟਰ** | ਉੱਪਰ ਦੱਸੇ ਬਾਕੀ ਸਾਰੇ ਰਨਟਾਈਮ, ਫਲੀਟ ਵਿਊ, ਕਲਾਊਡ ਸਿੰਕ | $9 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |
| **Pro** | ਸਟਾਰਟਰ + ਕੰਟਰੋਲ ਅਤੇ ਮੁਲਾਂਕਣ: ਪ੍ਰਵਾਨਗੀਆਂ, ਟੂਲ-ਖ਼ਤਰਾ ਨੀਤੀਆਂ, ਈਵਲ, ਅਸਧਾਰਨਤਾ ਖੋਜ, ਲਾਗਤ ਓਪਟੀਮਾਈਜ਼ਰ, OTel ਐਕਸਪੋਰਟ, ਛੇੜਛਾੜ-ਸਬੂਤ ਆਡਿਟ ਲੌਗ | $19 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |

ਸਾਲਾਨਾ ਪਲਾਨ, Enterprise ਅਤੇ ਮੌਜੂਦਾ ਅੰਕੜੇ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** 'ਤੇ ਹਨ। ਸੈਲਫ-ਹੋਸਟਡ ਲਾਈਸੈਂਸ
ਕੁੰਜੀਆਂ ਕਲਾਊਡ ਤੋਂ ਬਿਨਾਂ ਕੰਮ ਕਰਦੀਆਂ ਹਨ (`clawmetry license`)। ਸਹੀ ਮੁਫ਼ਤ/ਭੁਗਤਾਨ ਵੰਡ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਵਿੱਚ ਹੈ।

## ਤੁਹਾਡਾ ਡਾਟਾ ਤੁਹਾਡੀ ਮਸ਼ੀਨ 'ਤੇ ਹੀ ਰਹਿੰਦਾ ਹੈ

ClawMetry ਲੋਕਲ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਅਤੇ ਲੌਗ ਪੜ੍ਹਦਾ ਹੈ। **ਕੋਈ ਸੈਸ਼ਨ ਡਾਟਾ ਤੁਹਾਡੇ ਬਾਕਸ ਤੋਂ ਬਾਹਰ
ਨਹੀਂ ਜਾਂਦਾ ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ ਚਲਾਉਂਦੇ** — ਨਾ ਕੋਈ ਪ੍ਰੌਮਪਟ, ਜਵਾਬ, ਟੂਲ ਆਰਗੂਮੈਂਟ, ਫਾਈਲ
ਸਮੱਗਰੀ ਜਾਂ ਲੌਗ ਲਾਈਨ। ਜਦੋਂ ਤੁਸੀਂ ਕਨੈਕਟ ਕਰਦੇ ਹੋ, ਤਾਂ ਸਨੈਪਸ਼ਾਟ ਇੱਕ ਅਜਿਹੀ ਕੁੰਜੀ ਨਾਲ
ਐਂਡ-ਟੂ-ਐਂਡ ਇਨਕ੍ਰਿਪਟਡ ਹੁੰਦਾ ਹੈ ਜੋ ਕਦੇ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦੀ, ਅਤੇ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ
ਵਿੱਚ ਹੀ ਡੀਕ੍ਰਿਪਟ ਹੁੰਦਾ ਹੈ। ਜੇ ਕਿਸੇ ਨੋਡ ਕੋਲ ਕੁੰਜੀ ਨਹੀਂ ਹੈ, ਤਾਂ ਅਪਲੋਡ ਸਾਫ਼ ਭੇਜਣ ਦੀ ਬਜਾਏ
ਛੱਡ ਦਿੱਤਾ ਜਾਂਦਾ ਹੈ, ਅਤੇ ਕੋਈ ਵੀ ਸਰਵਰ ਜਵਾਬ ਇਸਨੂੰ ਬੰਦ ਨਹੀਂ ਕਰ ਸਕਦਾ।

ਦੋ ਚੀਜ਼ਾਂ ਕਨੈਕਟ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਡਿਫੌਲਟ ਤੌਰ 'ਤੇ ਚਲਦੀਆਂ ਹਨ, ਦੋਵੇਂ ਬੰਦ ਕੀਤੀਆਂ ਜਾ ਸਕਦੀਆਂ ਹਨ ਅਤੇ ਕੋਈ ਵੀ
ਸੈਸ਼ਨ ਡਾਟਾ ਨਹੀਂ ਲੈ ਜਾਂਦੀਆਂ: ਇੱਕ ਗੁਮਨਾਮ ਇੰਸਟਾਲ ਪਿੰਗ ਅਤੇ PyPI ਦੇ ਵਿਰੁੱਧ ਇੱਕ
ਵਰਜਨ ਚੈੱਕ। ਇੱਕ ਡਿਫੌਲਟ ਇੰਸਟਾਲ ਸ਼ੁਰੂਆਤੀ ਬੈਨਰ ਲਾਈਨ ਲਈ ਇੱਕ ਵਾਰ ਤੁਹਾਡੇ ਪਬਲਿਕ IP
ਨੂੰ ਵੀ ਲੁੱਕਅਪ ਕਰਦਾ ਹੈ। ਹਰ ਟਿਕਾਣਾ, ਉਹ ਕੀ ਲੈ ਜਾਂਦਾ ਹੈ ਅਤੇ ਇਸਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰੀਏ, ਸਭ
[docs/EGRESS.md](docs/EGRESS.md) ਵਿੱਚ ਸੂਚੀਬੱਧ ਹੈ; ਸੈਲਫ-ਹੋਸਟਡ, ਰੀਪੌਇੰਟਡ ਅਤੇ ਏਅਰ-ਗੈਪਡ ਇੰਸਟਾਲ
ਬਿਲਕੁਲ ਵੀ ਕੋਈ ਵਿਵੇਕਸ਼ੀਲ ਆਊਟਬਾਊਂਡ ਕਾਲ ਨਹੀਂ ਕਰਦੇ।

ਡੀਕ੍ਰਿਪਸ਼ਨ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ, ਉਸ ਕੋਡ ਵਿੱਚ ਹੁੰਦਾ ਹੈ ਜੋ ਅਸੀਂ ਤੁਹਾਨੂੰ ਦਿੰਦੇ ਹਾਂ। ਇਹ ਪਹਿਲਾਂ
ਇੱਕ ਵਾਅਦਾ ਸੀ; ਹੁਣ ਇਹ ਅਜਿਹੀ ਚੀਜ਼ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਪਰਖ ਸਕਦੇ ਹੋ। ਹਰ ਲਾਈਨ ਜੋ ਤੁਹਾਡੀ ਕੁੰਜੀ ਨੂੰ ਛੂੰਹਦੀ ਹੈ
ਇੱਕ ਪੜ੍ਹਨਯੋਗ ਫਾਈਲ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js) ਵਿੱਚ ਰਹਿੰਦੀ ਹੈ,
ਜੋ wheel ਦੇ ਅੰਦਰ ਭੇਜੀ ਜਾਂਦੀ ਹੈ ਅਤੇ ਜਿਵੇਂ ਦੀ ਤਿਵੇਂ ਸਰਵ ਕੀਤੀ ਜਾਂਦੀ ਹੈ, ਇੱਕ Subresource
Integrity ਹੈਸ਼ ਨਾਲ ਪਿੰਨ ਕੀਤੀ ਹੋਈ। ਇਹ ਪੁਸ਼ਟੀ ਕਰਨ ਲਈ ਕਿ ਬ੍ਰਾਊਜ਼ਰ ਉਹੀ ਚਲਾਉਂਦਾ ਹੈ ਜੋ ਅਸੀਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਹੈ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ਇਹ ਕੀ ਸਾਬਤ ਨਹੀਂ ਕਰਦਾ: ਅਸੀਂ ਉਹ ਪੇਜ ਵੀ ਸਰਵ ਕਰਦੇ ਹਾਂ ਜੋ ਫਾਈਲ ਲੋਡ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ ਅਸੀਂ
ਇੱਕ ਵੱਖਰਾ ਪੇਜ ਵੀ ਸਰਵ ਕਰ ਸਕਦੇ ਹਾਂ। Integrity ਹੈਸ਼ ਤੁਹਾਨੂੰ ਇੱਕ ਸਮਝੌਤਾ ਕੀਤੇ CDN ਤੋਂ ਬਚਾਉਂਦੇ ਹਨ,
ਵੈਂਡਰ ਤੋਂ ਨਹੀਂ। ਜੋ ਤੁਹਾਨੂੰ ਮਿਲਦਾ ਹੈ ਉਹ ਇਹ ਹੈ ਕਿ ਕੋਈ ਵੀ ਬਦਲਾਅ ਜਾਣਬੁੱਝ ਕੇ,
ਪੇਜ ਸੋਰਸ ਵਿੱਚ ਦਿੱਖਣਯੋਗ, ਅਤੇ PyPI 'ਤੇ ਮੌਜੂਦ ਆਰਟੀਫੈਕਟ ਤੋਂ ਵੱਖਰਾ ਹੋਣਾ ਪਵੇਗਾ
ਜਿਸਨੂੰ ਕੋਈ ਵੀ ਪ੍ਰਾਪਤ ਕਰ ਸਕਦਾ ਹੈ। ਸੈਲਫ-ਹੋਸਟਿੰਗ ਜਾਂ ਸਿਰਫ਼ ਲੋਕਲ ਰਹਿਣਾ ਇਸ ਨਿਰਭਰਤਾ ਨੂੰ
ਪੂਰੀ ਤਰ੍ਹਾਂ ਹਟਾ ਦਿੰਦਾ ਹੈ।

## ਇੰਸਟਾਲ

```bash
pip install clawmetry     # ਫਿਰ: clawmetry
```

ਜਾਂ ਇੱਕ-ਲਾਈਨਰ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ਜਾਂ Windows 'ਤੇ Python 3.8+ ਦੀ ਲੋੜ ਹੈ, ਅਤੇ ਉਸੇ ਮਸ਼ੀਨ 'ਤੇ ਘੱਟੋ-ਘੱਟ
ਇੱਕ ਏਜੰਟ ਰਨਟਾਈਮ। Docker ਹਦਾਇਤਾਂ: [docs/DOCKER.md](docs/DOCKER.md)।

ਜਾਂ ਏਜੰਟ ਨੂੰ ਤੁਹਾਡੇ ਲਈ ਸੈੱਟਅੱਪ ਕਰਨ ਦਿਓ। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ਸਕਿੱਲ Claude Code, Codex, Cursor, Gemini CLI, Copilot ਜਾਂ OpenCode ਨੂੰ
ClawMetry ਇੰਸਟਾਲ ਕਰਨਾ, ਮਸ਼ੀਨ 'ਤੇ ਏਜੰਟ ਕੀ ਕਰ ਰਹੇ ਹਨ ਅਤੇ ਕਿੰਨਾ ਖਰਚ ਕਰ ਰਹੇ ਹਨ ਦੱਸਣਾ,
ਬੇਨਤੀ 'ਤੇ ਇੱਕ ਸੈਸ਼ਨ ਰੋਕਣਾ, ਅਤੇ ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਪ੍ਰਵਾਨਗੀ ਲਈ ਰੋਕਣਾ ਸਿਖਾਉਂਦਾ ਹੈ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ਦਸਤਾਵੇਜ਼

| | |
|---|---|
| [ਰਨਟਾਈਮ ਅਨੁਕੂਲਤਾ](docs/compatibility.md) | ਹਰ ਅਡੈਪਟਰ ਕੀ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਇੱਕ ਰਨਟਾਈਮ ਕਿਵੇਂ ਜੋੜੀਏ |
| [ਕੌਂਟੈਕਸਟ ਬਲੋਆਊਟ](docs/CONTEXT_BLOWOUT.md) | ਹਰ-ਪ੍ਰੋਵਾਈਡਰ ਵਿੰਡੋ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਓਵਰਫਲੋ, ਹਰ-ਰਨਟਾਈਮ ਕਵਰੇਜ |
| [ਓਵਰਹੈੱਡ](docs/OVERHEAD.md) | ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਕੀ ਲਾਗਤ ਹੈ, ਮਾਪੀ ਗਈ, ਦੁਹਰਾਉਣ ਲਈ ਹਾਰਨੈੱਸ ਸਮੇਤ |
| [ਹੱਕਦਾਰੀਆਂ](docs/ENTITLEMENTS.md) | ਮੁਫ਼ਤ ਬਨਾਮ ਭੁਗਤਾਨ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, ਲਾਈਸੈਂਸ CLI |
| [ਪ੍ਰਵਾਨਗੀਆਂ ਅਤੇ ਨੀਤੀਆਂ](docs/APPROVALS.md) | ਐਗਜ਼ੀਕਿਊਸ਼ਨ ਤੋਂ ਪਹਿਲਾਂ ਗੇਟਿੰਗ, ਜੋਖਮ ਸਕੋਰਿੰਗ, ਫ਼ੋਨ ਪ੍ਰਵਾਨਗੀਆਂ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ਕਿਤੇ ਵੀ ਟਰੇਸ ਐਕਸਪੋਰਟ ਕਰੋ, ਕਿਸੇ ਵੀ ਥਾਂ ਤੋਂ OTLP ਇਨਜੈਸਟ ਕਰੋ |
| [ਆਪਣਾ ਖੁਦ ਦਾ ਏਜੰਟ ਲਿਆਓ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ਸ਼ੁਰੂ ਤੋਂ ਅੰਤ ਤੱਕ, ਚਲਾਉਣਯੋਗ ਉਦਾਹਰਣਾਂ ਸਮੇਤ |
| [SDK ਟ੍ਰੈਕਿੰਗ](docs/SDK_TRACKING.md) | ਤੁਹਾਡੇ ਖੁਦ ਬਣਾਏ ਏਜੰਟਾਂ ਲਈ ਲਾਗਤ ਦਾ ਹਿਸਾਬ |
| [ਚੈਟ ਚੈਨਲ](docs/CHANNELS.md) | Flow ਵਿੱਚ ਦਿਖਾਏ ਗਏ ਚੈਟ ਅਡੈਪਟਰ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ਸੈਂਡਬੌਕਸਡ NVIDIA NemoClaw ਸੈੱਟਅੱਪ |
| [Docker](docs/DOCKER.md) | ਇਮੇਜ, compose, ਵਾਲਿਊਮ ਮਾਊਂਟ |
| [ਆਰਕੀਟੈਕਚਰ](ARCHITECTURE.md) · [ਵਿਕਾਸ](docs/DEVELOPMENT.md) | ਇਹ ਅੰਦਰੋਂ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ; ਸੋਰਸ ਤੋਂ ਚਲਾਉਣਾ |
| [ਟੈਲੀਮੈਟਰੀ](docs/TELEMETRY.md) | ਗੁਮਨਾਮ ਇੰਸਟਾਲ ਅਤੇ ਡੈਸਕਟੌਪ-ਓਪਨ ਪਿੰਗ, ਅਤੇ ਇਹਨਾਂ ਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰੀਏ |

## ਸਕਰੀਨਸ਼ਾਟ

ਹੇਠਾਂ ਦਿੱਤਾ ਹਰ ਅੰਕੜਾ ਇੱਕ ਅਸਲੀ ਮਸ਼ੀਨ ਤੋਂ ਹੈ, ਸਿਰਫ਼ ਪੜ੍ਹਨ ਲਈ, ਬਿਨਾਂ ਕਿਸੇ ਬਣਾਵਟੀ ਡਾਟੇ ਦੇ।

**ਇਹ ਤੁਹਾਨੂੰ ਦੱਸਦਾ ਹੈ ਜਦੋਂ ਕੁਝ ਗਲਤ ਹੁੰਦਾ ਹੈ, ਸਿਰਫ਼ ਇਹ ਨਹੀਂ ਕਿ ਕੀ ਹੋਇਆ।**
ਸਿਖਰ 'ਤੇ ਦੋ ਅਸਧਾਰਨਤਾ ਬੈਨਰ: ਖਰਚ ਰੋਜ਼ਾਨਾ ਔਸਤ ਦਾ 7 ਗੁਣਾ ਚੱਲ ਰਿਹਾ ਹੈ, ਅਤੇ ਇੱਕ
4.2 ਗੁਣਾ ਲਾਗਤ ਵਾਧਾ। ਉਹਨਾਂ ਦੇ ਹੇਠਾਂ, 667 ਹਾਲੀਆ ਸੈਸ਼ਨਾਂ ਵਿੱਚੋਂ 324, ਇੱਕ ਬਰਬਾਦੀ
ਸੰਕੇਤ ਲੈ ਕੇ, ਕਾਰਨ ਅਨੁਸਾਰ ਸੂਚੀਬੱਧ।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ਇਹ ਤੁਹਾਨੂੰ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਹਰ ਵਿੰਡੋ ਵਿੱਚ।**
ਅੱਜ $252.47, ਇਸ ਹਫ਼ਤੇ $513.15, ਇਸ ਮਹੀਨੇ $1,312.92, ਹਰ ਇੱਕ ਦੇ ਪਿੱਛੇ ਟੋਕਨ ਅਤੇ
ਤੁਹਾਡੀ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਪਹਿਲਾਂ ਹੀ ਕਿੰਨਾ ਕਵਰ ਕਰਦੀ ਹੈ ਸਮੇਤ। ਉਸ ਹੇਠਾਂ, ਲਗਭਗ $1,128/ਮਹੀਨਾ
ਰਿਕਵਰੇਬਲ ਵਜੋਂ ਸੂਚੀਬੱਧ ਅਤੇ ਕੈਸ਼ ਦੁਬਾਰਾ ਵਰਤੋਂ ਨਾਲ ਪਹਿਲਾਂ ਹੀ ਬਚਾਏ ਗਏ $17,256/ਮਹੀਨਾ।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਸੁਨੇਹਾ ਕਿਵੇਂ ਜਵਾਬ ਬਣਦਾ ਹੈ।**
ਲਾਈਵ ਫਲੋ ਡਾਇਗ੍ਰਾਮ: ਤੁਸੀਂ, ਉਹ ਚੈਨਲ ਜਿਸ ਤੇ ਇਹ ਪਹੁੰਚਿਆ, ਗੇਟਵੇ, ਹੁਣੇ ਜਵਾਬ ਦੇ ਰਿਹਾ
ਮਾਡਲ, ਅਤੇ ਹਰ ਟੂਲ ਜੋ ਇਸਨੇ ਵਰਤਿਆ। ਨੋਡ ਜਗਮਗਾ ਉੱਠਦੇ ਹਨ ਜਦੋਂ ਕੰਮ ਉਹਨਾਂ ਵਿੱਚੋਂ
ਲੰਘਦਾ ਹੈ।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ਮਸ਼ੀਨ 'ਤੇ ਹਰ ਏਜੰਟ, ਇੱਕੋ ਟੇਬਲ ਵਿੱਚ।**
ਇਹ ਕੀ ਚਲਾਉਂਦਾ ਹੈ, ਪਿਛਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ਅਤੇ ਆਪਣੇ ਪੂਰੇ ਸਮੇਂ ਵਿੱਚ ਕਿੰਨਾ ਖਰਚ ਹੋਇਆ, ਇਹ
ਆਖ਼ਰੀ ਵਾਰ ਕਦੋਂ ਦੇਖਿਆ ਗਿਆ, ਇਸਦਾ ਮਾਲਕ ਕੌਣ ਹੈ, ਅਤੇ ਕੀ ਇੱਕ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਬਿੱਲ ਕਵਰ ਕਰ ਰਹੀ ਹੈ।
ਇੱਥੇ 14 ਏਜੰਟ, 3 ਸੈਸ਼ਨ ਕੰਮ ਕਰ ਰਹੇ, 13 ਸ਼ਾਂਤ।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਵਾਰੀ ਦਾ ਸਮਾਂ ਅਤੇ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਟੂਲ-ਦਰ-ਟੂਲ।**
ਇੱਕ ਅਸਲੀ ਸੈਸ਼ਨ ਦੀ ਇੱਕ ਵਾਰੀ: $1.16 ਵਿੱਚ 11.2 ਮਿੰਟਾਂ ਵਿੱਚ 11 ਟੂਲ। ਹਰ Bash
ਕਾਲ ਅਤੇ ਮਾਡਲ ਕਾਲ ਨੂੰ ਟਾਈਮਲਾਈਨ 'ਤੇ ਆਪਣੀ ਬਾਰ ਮਿਲਦੀ ਹੈ, ਤਾਂ ਜੋ 4.1 ਮਿੰਟ ਚੱਲੀ
ਕਮਾਂਡ ਅਤੇ 226ms ਚੱਲੀ ਕਮਾਂਡ ਵਿੱਚ ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਫਰਕ ਦੱਸਿਆ ਜਾ ਸਕੇ।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ਇਹ ਕੰਮ ਦਾ ਦਰਜਾ ਦਿੰਦਾ ਹੈ, ਸਿਰਫ਼ ਖਰਚ ਦਾ ਨਹੀਂ।**
ਇਸ ਹਫ਼ਤੇ ਇੱਕ A: 54 ਕੰਮ ਸਾਫ਼ ਵਾਪਸ ਆਏ, 2 ਮੁਸ਼ਕਿਲ ਵਾਲਿਆਂ ਦੀ ਕੀਮਤ $48.57 ਰਹੀ, ਅਤੇ
ਮੁਲਾਂਕਣ ਲਈ ਬਹੁਤ ਘੱਟ ਗਤੀਵਿਧੀ ਵਾਲੇ ਰਨ ਜਿੱਤ ਵਜੋਂ ਗਿਣੇ ਜਾਣ ਦੀ ਬਜਾਏ ਦਰਜੇ ਤੋਂ ਬਾਹਰ ਰੱਖੇ ਗਏ। ਹਰ
ਮੁਸ਼ਕਿਲ ਰਨ ਆਪਣੇ ਟਰੇਸ ਨਾਲ ਜੁੜਿਆ ਹੈ।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਕੌਂਟੈਕਸਟ ਵਿੰਡੋ ਕਿਉਂ ਭਰਦੀ ਰਹਿੰਦੀ ਹੈ।**
ਆਖ਼ਰੀ ਵਾਰੀ 'ਤੇ 1M-ਟੋਕਨ ਵਿੰਡੋ ਵਿੱਚੋਂ 715K, 83.3% ਦੀ ਸਿਖਰ, 4 ਕੰਪੈਕਸ਼ਨ
ਜੋ ਸਾਰੇ ਓਵਰਫਲੋ ਦੀ ਬਜਾਏ ਪਹਿਲਾਂ ਤੋਂ ਹੀ ਚੱਲੇ, ਅਤੇ ਇਸਦੇ ਪਿੱਛੇ ਹਰ ਵਾਰੀ ਦੀ ਵਰਤੋਂ।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ਖੋਜ ਬਿਨਾਂ ਤੁਹਾਡੇ ਕੁਝ ਕੌਂਫਿਗਰ ਕੀਤੇ ਚੱਲਦੀ ਹੈ।**
ਬਿਲਟ-ਇਨ ਖੋਜੀ ਇੰਸਟਾਲ ਤੋਂ ਹੀ ਚਾਲੂ ਹਨ: ਏਜੰਟ ਚੁੱਪ ਹੋ ਗਿਆ, ਟੈਲੀਮੈਟਰੀ ਫੀਡ
ਰੁਕ ਗਈ, ਲਾਗਤ ਵਾਧਾ, ਟੋਕਨ ਬਰਸਟ, ਵੱਧ ਰਹੀਆਂ ਗਲਤੀਆਂ, ਗਲਤੀ ਵਾਧਾ, ਬਜਟ
ਸੀਮਾ, ਖ਼ਤਰੇ ਦਾ ਸਿਗਨੇਚਰ ਮਿਲਿਆ, ਸੁਰੱਖਿਆ ਟੂਲ ਖੋਜ, ਸੁਰੱਖਿਆ ਸਥਿਤੀ
ਬਦਲੀ। ਤੁਹਾਡੇ ਖੁਦ ਦੇ ਨਿਯਮ ਇਸ ਤੋਂ ਉੱਪਰ ਵਿਕਲਪਿਕ ਹਨ।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ਖ਼ਤਰਨਾਕ ਕਾਲ ਨੂੰ ਰੋਕਣਾ ਵਿਕਲਪਿਕ ਹੈ, ਅਤੇ ਬੰਦ ਭੇਜਿਆ ਜਾਂਦਾ ਹੈ।**
ਰਿਕਰਸਿਵ ਡਿਲੀਟ, ਫੋਰਸ ਪੁਸ਼, sudo, ਸੀਕ੍ਰੇਟਸ, ਪੈਕੇਜ ਇੰਸਟਾਲ ਅਤੇ ਬਾਹਰ ਜਾਣ ਵਾਲੀਆਂ
ਕਾਲਾਂ ਵਿੱਚੋਂ ਹਰ ਇੱਕ ਲਈ ਇੱਕ ਨਿਯਮ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਚਾਲੂ ਕਰ ਸਕਦੇ ਹੋ। ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ ਅਜਿਹਾ ਨਹੀਂ ਕਰਦੇ,
ClawMetry ਦੇਖਦਾ ਰਹਿੰਦਾ ਹੈ ਅਤੇ ਕੁਝ ਨਹੀਂ ਬਦਲਦਾ। ਇੱਕ ਵਾਰ ਚਾਲੂ ਹੋਣ 'ਤੇ, ਮਿਲਦੀਆਂ-ਜੁਲਦੀਆਂ ਕਾਲਾਂ
ਇੱਥੇ (ਜਾਂ ਤੁਹਾਡੇ ਫ਼ੋਨ 'ਤੇ) ਪ੍ਰਵਾਨਗੀ ਜਾਂ ਇਨਕਾਰ ਲਈ ਉਡੀਕ ਕਰਦੀਆਂ ਹਨ।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ਹੋਰ, ਹਰ ਰਨਟਾਈਮ ਲਈ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## ਮਾਨਤਾ

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star History

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
