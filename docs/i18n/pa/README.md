<!-- i18n-src:a855a14295b0 -->
> ਪੰਜਾਬੀ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ਕੋਈ ਏਜੰਟ ਬਿਨਾਂ ਕਿਸੇ ਪ੍ਰਗਤੀ ਦੇ ਸੌ ਟੂਲ ਕਾਲਾਂ ਕਰ ਸਕਦਾ ਹੈ।** ClawMetry
ਉਨ੍ਹਾਂ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਨੂੰ ਪੜ੍ਹਦਾ ਹੈ ਜੋ ਤੁਹਾਡੇ ਕੋਡਿੰਗ ਏਜੰਟ ਪਹਿਲਾਂ ਹੀ ਲਿਖਦੇ ਹਨ, ਅਤੇ ਟਾਈਮਲਾਈਨ,
ਟੂਲ ਕਾਲਾਂ ਅਤੇ ਰਨਟਾਈਮ ਵੱਲੋਂ ਦਿਖਾਏ ਜਾਂਦੇ ਟੋਕਨ ਤੇ ਲਾਗਤ ਡਾਟੇ ਨੂੰ ਇੱਕੋ
ਦ੍ਰਿਸ਼ ਵਿੱਚ ਲਿਆਉਂਦਾ ਹੈ — ਜਿਸ ਨਾਲ ਤੁਸੀਂ ਦੱਸ ਸਕਦੇ ਹੋ ਕਿ ਕਿਹੜਾ ਲੰਬਾ ਰਨ ਕੰਮ ਕਰ ਰਿਹਾ ਹੈ ਅਤੇ ਕਿਹੜਾ ਫਸਿਆ ਹੋਇਆ ਹੈ।

**32 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ — Claude Code, OpenAI Codex, Hermes, OpenClaw ਅਤੇ 28 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ। ([ਪੂਰੀ ਸੂਚੀ](SUPPORTED_RUNTIMES.txt), ਕੈਟਾਲਾਗ ਤੋਂ ਜਨਰੇਟ ਕੀਤੀ ਗਈ।)

> 🌐 **ਇਸਨੂੰ ਇਹਨਾਂ ਭਾਸ਼ਾਵਾਂ ਵਿੱਚ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕਾਨਫਿਗ। ਹਰ ਚੀਜ਼ ਆਪਣੇ-ਆਪ ਪਛਾਣਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** ਉੱਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ। ਜ਼ੀਰੋ ਕਾਨਫਿਗ: ਇਹ ਉਹ ਏਜੰਟ ਰਨਟਾਈਮ
ਲੱਭ ਲੈਂਦਾ ਹੈ ਜੋ ਤੁਹਾਡੇ ਕੋਲ ਪਹਿਲਾਂ ਹੀ ਮੌਜੂਦ ਹਨ, ਉਹਨਾਂ ਨੂੰ ਸਿਰਫ਼-ਪੜ੍ਹਨ ਲਈ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਇਸ ਗੱਲ ਵਿੱਚ ਕੁਝ ਵੀ ਨਹੀਂ ਬਦਲਦਾ ਕਿ ਉਹ ਕਿਵੇਂ ਚਲਦੇ ਹਨ।

![ClawMetry ਡੈਸ਼ਬੋਰਡ: ਇੱਕੋ ਮਸ਼ੀਨ ਉੱਤੇ ਹਰ AI ਏਜੰਟ ਰਨਟਾਈਮ, 24 ਘੰਟੇ ਅਤੇ ਜੀਵਨ-ਭਰ ਦੀ ਲਾਗਤ ਹਰ ਏਜੰਟ ਲਈ](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ਇੰਸਟਾਲ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ

| | |
|---|---|
| **ਇਹ ਕੀ ਕਰਦਾ ਹੈ** | ਉਹ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਅਤੇ ਲੌਗ ਪੜ੍ਹਦਾ ਹੈ ਜੋ ਤੁਹਾਡੇ ਏਜੰਟ ਪਹਿਲਾਂ ਹੀ ਲਿਖਦੇ ਹਨ। ਕੋਈ SDK ਨਹੀਂ, ਕੋਈ ਕੋਡ ਬਦਲਾਅ ਨਹੀਂ, ਤੁਹਾਡੇ ਐਪ ਵਿੱਚ ਕੋਈ ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਨਹੀਂ। |
| **ਤੁਸੀਂ ਕੀ ਦੇਖਦੇ ਹੋ** | ਸੈਸ਼ਨ ਟਾਈਮਲਾਈਨ, ਟੂਲ-ਦਰ-ਟੂਲ ਰੀਪਲੇ, ਟੋਕਨ ਤੇ ਲਾਗਤ ਦਾ ਵੇਰਵਾ, ਅਤੇ ਟ੍ਰੈਜੈਕਟਰੀ ਸਿਗਨਲ (ਲੂਪਿੰਗ, ਦੁਹਰਾਈਆਂ ਗਈਆਂ ਅਸਫਲਤਾਵਾਂ) — ਹਰ ਰਨਟਾਈਮ ਲਈ। |
| **ਕੀ ਮੁਫ਼ਤ ਹੈ** | `pip install clawmetry` **OpenClaw, NVIDIA NemoClaw ਅਤੇ Goose** ਨੂੰ ਬਿਨਾਂ ਕਿਸੇ ਖਾਤੇ, ਬਿਨਾਂ ਕਿਸੇ ਕੀ ਅਤੇ ਬਿਨਾਂ ਕਿਸੇ ਨੈੱਟਵਰਕ ਕਾਲ ਦੇ ਪੜ੍ਹਦਾ ਹੈ। ਬਾਕੀ 27 — Claude Code, Codex, Cursor ਅਤੇ ਬਾਕੀ ਦੇ — ਕਲੋਜ਼ਡ-ਸੋਰਸ `clawmetry-pro` ਸਾਥੀ ਦੁਆਰਾ ਪੜ੍ਹੇ ਜਾਂਦੇ ਹਨ, ਜੋ 7-ਦਿਨ ਦੀ ਟ੍ਰਾਇਲ ਜਾਂ ਕਿਸੇ ਪਲਾਨ ਨਾਲ ਆਉਂਦਾ ਹੈ — ਸਹੀ ਵੰਡ ਲਈ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਦੇਖੋ। |
| **ਕਿਵੇਂ ਸ�਼ੁਰੂ ਕਰੀਏ** | `pip install clawmetry && clawmetry`, ਫਿਰ localhost:8900 ਖੋਲ੍ਹੋ। ਇਸ ਮਸ਼ੀਨ ਉੱਤੇ ਹਾਲੇ ਕੋਈ ਏਜੰਟ ਨਹੀਂ? `clawmetry --sample` ਤਿੰਨ ਲੇਬਲ ਵਾਲੇ ਸਿੰਥੈਟਿਕ ਸੈਸ਼ਨਾਂ ਨਾਲ ਖੁੱਲ੍ਹਦਾ ਹੈ। |
| **ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਕੀ ਬਾਹਰ ਜਾਂਦਾ ਹੈ** | ਕੋਈ ਸੈਸ਼ਨ ਡਾਟਾ ਨਹੀਂ, ਜਦ ਤੱਕ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ ਚਲਾਉਂਦੇ। ਦੋ ਚੀਜ਼ਾਂ ਪਹਿਲਾਂ ਤੋਂ ਹੀ ਚੱਲਦੀਆਂ ਹਨ, ਦੋਵੇਂ ਓਪਟ-ਆਊਟ ਹਨ ਅਤੇ ਕੋਈ ਵੀ ਸੈਸ਼ਨ ਸਮੱਗਰੀ ਨਹੀਂ ਲੈ ਜਾਂਦੀਆਂ: ਇੱਕ ਅਗਿਆਤ ਇੰਸਟਾਲ ਪਿੰਗ ਅਤੇ ਇੱਕ PyPI ਵਰਜ਼ਨ ਚੈਕ। ਹਰ ਟਿਕਾਣਾ [docs/EGRESS.md](docs/EGRESS.md) ਵਿੱਚ ਸੂਚੀਬੱਧ ਹੈ, ਜੋ ਟਿੱਪਣੀਆਂ ਪੜ੍ਹ ਕੇ ਨਹੀਂ ਸਗੋਂ ਵਾਇਰ ਕੈਪਚਰ ਤੋਂ ਦੁਬਾਰਾ ਬਣਾਇਆ ਗਿਆ ਹੈ। |

ਨਤੀਜਿਆਂ ਬਾਰੇ ਫ਼ੈਸਲਾ ਲੈਣ ਤੋਂ ਪਹਿਲਾਂ ਦੋ ਸੀਮਾਵਾਂ ਜਾਣਨੀਆਂ ਜ�਼ਰੂਰੀ ਹਨ: ਰਨਟਾਈਮ ਬਹੁਤ
ਵੱਖੋ-ਵੱਖਰਾ ਡਾਟਾ ਦਿਖਾਉਂਦੇ ਹਨ (ਕੁਝ ਕੋਈ ਵੀ ਲਾਗਤ ਪ੍ਰਕਾਸ਼ਿਤ ਨਹੀਂ ਕਰਦੇ — [ਮੈਟ੍ਰਿਕਸ](docs/compatibility.md)
ਦੱਸਦਾ ਹੈ ਕਿ ਕਿਹੜਾ, ਹਰ ਰਨਟਾਈਮ ਲਈ), ਅਤੇ ਕਿਸੇ ਕਾਰਵਾਈ ਨੂੰ ਦੇਖਣਾ ਉਸਨੂੰ ਰੋਕਣ ਦੀ ਸਮਰਥਾ ਹੋਣ
ਦੇ ਬਰਾਬਰ ਨਹੀਂ ਹੈ ([ਕਿਹੜੇ ਕੰਟਰੋਲ ਅਸਲੀ ਹਨ, ਹਰ ਰਨਟਾਈਮ ਲਈ](docs/APPROVALS.md))।


## 32 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

**ਓਪਨ ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ਭੁਗਤਾਨ ਵਾਲੇ ਪਲਾਨ ਉੱਤੇ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ਹਰ ਰਨਟਾਈਮ ਨੂੰ ਇੱਕੋ ਜਿਹਾ ਡੈਸ਼ਬੋਰਡ ਮਿਲਦਾ ਹੈ। ਇੱਕੋ ਸਮੇਂ ਕਈ ਚਲਾਓ ਅਤੇ ਹੈਡਰ
ਸਵਿੱਚਰ ਹਰ ਟੈਬ ਨੂੰ ਉਹਨਾਂ ਵਿੱਚੋਂ ਕਿਸੇ ਇੱਕ ਵੱਲ ਦੁਬਾਰਾ ਸਕੋਪ ਕਰ ਦਿੰਦਾ ਹੈ।

ਕੀ ਤੁਸੀਂ SDK ਦੀ ਵਰਤੋਂ ਕਰਕੇ ਆਪਣਾ ਖੁਦ ਦਾ ਏਜੰਟ ਬਣਾਇਆ ਹੈ? ਇੰਟਰਸੈਪਟਰ ਉਸਦੀਆਂ LLM ਕਾਲਾਂ
ਦਾ ਵੀ ਟਰੈਕ ਰੱਖਦਾ ਹੈ। ਦੇਖੋ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **ਸੈਸ਼ਨ ਅਤੇ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ**: ਹਰ ਏਜੰਟ ਨੇ ਕੀ ਕੀਤਾ, ਵਾਰੀ-ਵਾਰੀ, ਰੀਪਲੇ ਨਾਲ
- **ਲਾਗਤ ਤੇ ਟੋਕਨ**: ਹਰ ਰਨਟਾਈਮ, ਮਾਡਲ, ਸੈਸ਼ਨ ਅਤੇ ਦਿਨ ਦੇ ਹਿਸਾਬ ਨਾਲ, ਅਨੌਮਲੀ ਫਲੈਗਾਂ ਨਾਲ
- **ਫਲੋ**: ਚੈਨਲਾਂ, ਮਾਡਲਾਂ ਅਤੇ ਟੂਲਾਂ ਵਿਚਕਾਰ ਚੱਲ ਰਹੇ ਸੁਨੇਹਿਆਂ ਦਾ ਲਾਈਵ ਚਿੱਤਰ
- **ਬ੍ਰੇਨ**: ਰੀਜ਼ਨਿੰਗ ਅਤੇ ਟੂਲ-ਕਾਲ ਈਵੈਂਟ ਸਟ੍ਰੀਮ, ਜਿਵੇਂ ਹੀ ਇਹ ਵਾਪਰਦਾ ਹੈ
- **ਕਾਂਟੈਕਸਟ ਬਲੋਆਊਟ**: ਹਰ ਪ੍ਰੋਵਾਈਡਰ ਲਈ ਸਹੀ ਆਕਾਰ ਵਾਲੀ ਵਿੰਡੋ ਵਰਤੋਂ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਜ�਼ੋਰਦਾਰ ਓਵਰਫਲੋ, ਨਾਲ ਹੀ ਹਰ ਰਨਟਾਈਮ ਲਈ ਇਹ ਦੱਸਦਾ ਨਕਸ਼ਾ ਕਿ ਅਸੀਂ ਕੀ *ਨਹੀਂ* ਦੇਖ ਸਕਦੇ ([ਕਿਵੇਂ](docs/CONTEXT_BLOWOUT.md))
- **ਮੈਮਰੀ ਅਤੇ ਹੁਨਰ**: ਉਹ ਫਾਈਲਾਂ ਅਤੇ ਹੁਨਰ ਜਿਹੜੇ ਹਰ ਰਨਟਾਈਮ ਨੇ ਅਸਲ ਵਿੱਚ ਲੋਡ ਕੀਤੇ
- **ਸਿਹਤ ਅਤੇ ਲੌਗ**: ਡਿਸਕ, ਮੈਮਰੀ, ਗਲਤੀ ਦਰਾਂ, ਰੇਟ ਲਿਮਟ, ਲਾਈਵ ਲੌਗ ਸਟ੍ਰੀਮ
- **ਅਲਰਟ**: ਬਜਟ ਸੀਮਾਵਾਂ, ਗਲਤੀ ਵਾਧਾ, ਏਜੰਟ-ਆਫਲਾਈਨ, Slack, Discord, PagerDuty, Telegram, Email ਵੱਲ ਰੂਟ ਕੀਤੇ ਗਏ
- **ਮਨਜ਼ੂਰੀਆਂ**: ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਚੱਲਣ *ਤੋਂ ਪਹਿਲਾਂ* ਰੋਕੋ ਅਤੇ ਆਪਣੇ ਫ਼ੋਨ ਤੋਂ ਮਨਜ਼ੂਰ ਕਰੋ ([ਕਿਵੇਂ](docs/APPROVALS.md))

## ਕਾਂਟੈਕਸਟ ਬਲੋਆਊਟ, ਅਤੇ ਦੇਖਣ ਦੀ ਲਾਗਤ ਕੀ ਹੈ

ਕਿਸੇ ਵੀ ਏਜੰਟ-ਤੁਲਨਾ ਟੂਲ ਉੱਤੇ ਭਰੋਸਾ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਜਵਾਬ ਦੇਣ ਲਾਇਕ ਦੋ ਸਵਾਲ।

**ਇਹ ਰਨਟਾਈਮਾਂ ਵਿੱਚ ਕਾਂਟੈਕਸਟ-ਵਿੰਡੋ ਬਲੋਆਊਟ ਨੂੰ ਕਿਵੇਂ ਸੰਭਾਲਦਾ ਹੈ?**

ਇੱਕ ਵਰਤੋਂ ਪ੍ਰਤੀਸ਼ਤ ਓਨਾ ਹੀ ਸੱਚਾ ਹੁੰਦਾ ਹੈ ਜਿੰਨਾ ਉਹ ਸੰਖਿਆ ਜਿਸ ਨਾਲ ਇਸਨੂੰ ਵੰਡਿਆ ਜਾਂਦਾ ਹੈ। ClawMetry
ਹਰ ਪ੍ਰੋਵਾਈਡਰ ਲਈ ਵਿੰਡੋ ਦਾ ਆਕਾਰ [ਇੱਕ ਸਾਰਣੀ ਤੋਂ ਲੈਂਦਾ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਪੜ੍ਹ ਸਕਦੇ ਹੋ ਅਤੇ
PR ਕਰ ਸਕਦੇ ਹੋ](clawmetry/context_windows.py), ਜੋ Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama ਅਤੇ GLM ਨੂੰ ਕਵਰ ਕਰਦੀ ਹੈ। ਇਹ ਸਾਰੇ 32
ਰਨਟਾਈਮਾਂ ਨੂੰ ਇੱਕੋ ਵੈਂਡਰ ਦੇ ਪੈਮਾਨੇ ਨਾਲ ਨਹੀਂ ਮਾਪਦਾ। ਇਸ ਦਾ ਮਹੱਤਵ ਹੈ: ਇੱਕ 300K GPT-5
ਵਾਰੀ ਨੂੰ Anthropic ਦੇ 200K ਦੇ ਵਿਰੁੱਧ ਸਕੋਰ ਕਰਨ ਨਾਲ ">100%, ਬਲੋਨ" ਦਿਖਾਈ ਦਿੰਦਾ ਹੈ
ਜਦਕਿ ਅਸਲ ਵਿੱਚ ਇਹ GPT-5 ਦੇ 400K ਦੇ 75% ਉੱਤੇ ਹੈ। ਇਹੀ ਪੈਮਾਨਾ ਇੱਕ ਸੱਚਮੁੱਚ ਓਵਰਫਲੋ ਹੋਈ
130K DeepSeek ਵਾਰੀ ਨੂੰ ਇੱਕ ਆਰਾਮਦਾਇਕ 65% ਵਜੋਂ ਲੁਕਾ ਦਿੰਦਾ ਹੈ।

ਹਰ ਵਿੰਡੋ ਆਪਣੇ ਸਰੋਤ ਨਾਲ ਆਉਂਦੀ ਹੈ: `model_table`, `explicit_marker`,
`observed_floor`, ਜਾਂ ਜਦੋਂ ਸਾਨੂੰ ਮਾਡਲ ਬਾਰੇ ਨਹੀਂ ਪਤਾ ਤਾਂ ਇੱਕ ਸੱਚਾ `default`। ਅੰਦਾਜ਼ੇ
ਉੱਤੇ ਬਣਿਆ ਗੇਜ ਕਦੇ ਵੀ ਲੁੱਕਅੱਪ ਉੱਤੇ ਬਣੇ ਗੇਜ ਵਾਂਗ ਭਰੋਸੇਯੋਗ ਦਿਖ ਕੇ ਨਹੀਂ ਦਿਖਾਈ ਦਿੰਦਾ।

ClawMetry ਸਿਰਫ਼ ਕੁਝ ਰਨਟਾਈਮਾਂ ਉੱਤੇ ਕੰਪੈਕਸ਼ਨ ਈਵੈਂਟ ਦੇਖ ਸਕਦਾ ਹੈ। ਇਸ ਲਈ
`GET /api/context-coverage` ਹਰ ਰਨਟਾਈਮ ਲਈ ਰਿਪੋਰਟ ਕਰਦਾ ਹੈ ਕਿ ਕੀ **ਜ਼ੀਰੋ ਦਾ ਮਤਲਬ
"ਸਾਫ਼ ਚੱਲਿਆ" ਹੈ ਜਾਂ "ਸਾਨੂੰ ਦਿਖਦਾ ਨਹੀਂ"**। ਇੱਕ `0` ਜਿਸਦਾ ਅਸਲ ਵਿੱਚ ਮਤਲਬ ਦਿਖਦਾ ਨਹੀਂ ਹੈ, ਇਹ ਸਾਫ਼ ਦੱਸਦਾ ਹੈ।
[ਪੂਰੀ ਜਾਣਕਾਰੀ](docs/CONTEXT_BLOWOUT.md)

**ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਲਾਗਤ ਕੀ ਹੈ?**

| ਰਸਤਾ | ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਜੋੜਿਆ ਗਿਆ | ਡਿਫਾਲਟ? |
|---|---|---|
| ਸੈਸ਼ਨ-ਫਾਈਲ ਟੇਲਿੰਗ (ਸਾਰੇ 32 ਰਨਟਾਈਮ) | **0**। ਵੱਖਰੀ ਪ੍ਰੋਸੈਸ, ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਕੋਈ ClawMetry ਕੋਡ ਨਹੀਂ | ਚਾਲੂ |
| HTTP ਇੰਟਰਸੈਪਟਰ (`CLAWMETRY_INTERCEPT=1`) | ਹਰ LLM ਕਾਲ ਲਈ **+0.44 ms**, ਜਾਂ 5s ਕਾਲ ਦਾ 0.009% | ਬੰਦ |
| ਪ੍ਰੀ-ਟੂਲ ਹੁੱਕ ਗੇਟ (ਗਰਮ ਕੈਸ਼) | ਹਰ ਗੇਟਿਡ ਟੂਲ ਕਾਲ ਲਈ **+44 ms**, 36 ms ਦੇ ਇੰਟਰਪ੍ਰੇਟਰ ਫਲੋਰ ਤੋਂ ਉੱਪਰ | ਬੰਦ |
| ਲਾਗੂਕਰਨ ਪ੍ਰੌਕਸੀ | ਹਰ LLM ਕਾਲ ਲਈ **+9.7 ms** | ਬੰਦ |

ਡੈਮਨ ਹੋਸਟ ਲਾਗਤ: **2,762 ਈਵੈਂਟ/ਸੈਕਿੰਡ** ਇੰਜੈਸਟ, ਡਿਸਕ ਉੱਤੇ **710 ਬਾਈਟ/ਈਵੈਂਟ**
(100k ਈਵੈਂਟਾਂ ਲਈ 67.7 MB), ਅਤੇ ਇੱਕ ਵਿਅਸਤ ਇੰਸਟਾਲ ਉੱਤੇ ਲਗਾਤਾਰ **ਇੱਕ ਕੋਰ ਦਾ ~12%**। ਇਹ ਆਖਰੀ
ਸੰਖਿਆ ਸਾਡੇ ਖੁਦ ਦੇ ਦੱਸੇ ਗਏ 5-10% ਬਜਟ ਤੋਂ ਵੱਧ ਹੈ, ਇਸ ਲਈ ਇਸਨੂੰ ਪੰਨੇ ਤੋਂ ਹਟਾਏ ਜਾਣ ਦੇ ਬਦਲੇ
ਇੱਕ ਬੱਗ ਵਜੋਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਗਿਆ ਹੈ ਜਿਸਦਾ ਹੱਲ ਲੱਭਿਆ ਜਾਣਾ ਹੈ।

Apple M2 Pro ਉੱਤੇ `benchmarks/overhead.py` ਨਾਲ ਮਾਪਿਆ ਗਿਆ। ਹਾਰਨੈੱਸ ਹਰ
ਹਾਲਤ ਨੂੰ ਇੱਕ ਵੱਖਰੀ ਪ੍ਰੋਸੈਸ ਵਿੱਚ ਚਲਾਉਂਦਾ ਹੈ, ਉਹਨਾਂ ਦਾ ਕ੍ਰਮ ਬਦਲਦਾ ਰਹਿੰਦਾ ਹੈ, ਅਤੇ **ਜਦੋਂ
ਦੌਰ ਇਸਦੇ ਚਿੰਨ੍ਹ ਉੱਤੇ ਅਸਹਿਮਤ ਹੁੰਦੇ ਹਨ ਤਾਂ ਕੋਈ ਸੰਖਿਆ ਪ੍ਰਿੰਟ ਕਰਨ ਤੋਂ ਇਨਕਾਰ ਕਰਦਾ ਹੈ**। ਇਸਨੂੰ
ਆਪਣੀ ਹੀ ਮਸ਼ੀਨ ਉੱਤੇ ਇੱਕ ਮਿੰਟ ਵਿੱਚ ਚਲਾਓ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ਹਰ ਰਸਤਾ ਮਾਪਿਆ ਗਿਆ ਹੈ, ਹੁੱਕ ਗੇਟਾਂ ਅਤੇ ਲਾਗੂਕਰਨ ਪ੍ਰੌਕਸੀ ਸਮੇਤ,
ਅਤੇ ਹਾਰਨੈੱਸ CI ਵਿੱਚ Linux, macOS ਅਤੇ Windows ਉੱਤੇ ਚੱਲਦਾ ਹੈ। ਜਾਣਨ ਲਾਇਕ ਦੋ ਨਤੀਜੇ:
Windows ਉੱਤੇ ਪ੍ਰੌਕਸੀ ਦੀ ਲਾਗਤ Linux ਨਾਲੋਂ ਲਗਭਗ ਸੱਤ ਗੁਣਾ ਵੱਧ ਹੈ, ਅਤੇ
ਡੈਮਨ ਹੁਣ ਇੱਕ ਕੋਰ ਦਾ ਲਗਭਗ 12% ਲਗਾਤਾਰ ਵਰਤਦਾ ਹੈ, ਜੋ ਸਾਡੇ ਖੁਦ ਦੇ 5-10% ਬਜਟ ਤੋਂ
ਵੱਧ ਹੈ। ਕੱਚਾ JSON, ਤਰੀਕਾ, ਅਤੇ ਜੋ ਹਾਲੇ ਵੀ ਨਹੀਂ ਮਾਪਿਆ ਗਿਆ, ਸਭ
[docs/OVERHEAD.md](docs/OVERHEAD.md) ਵਿੱਚ ਹਨ।

## ਕੀਮਤ

| ਪਲਾਨ | ਇਹ ਕੀ ਕਵਰ ਕਰਦਾ ਹੈ | ਕੀਮਤ |
|---|---|---|
| **ਮੁਫ਼ਤ** | OpenClaw + NVIDIA NemoClaw + Goose, ਪੂਰਾ ਡੈਸ਼ਬੋਰਡ, ਸਿਰਫ਼ ਲੋਕਲ | $0 |
| **ਸਟਾਰਟਰ** | ਉਪਰੋਕਤ ਹਰ ਹੋਰ ਰਨਟਾਈਮ, ਫਲੀਟ ਦ੍ਰਿਸ਼, ਕਲਾਊਡ ਸਿੰਕ | $9 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |
| **Pro** | ਸਟਾਰਟਰ + ਕੰਟਰੋਲ ਅਤੇ ਮੁਲਾਂਕਣ: ਮਨਜ਼ੂਰੀਆਂ, ਟੂਲ-ਖ਼ਤਰਾ ਨੀਤੀਆਂ, ਮੁਲਾਂਕਣ, ਅਨੌਮਲੀ ਖੋਜ, ਲਾਗਤ ਓਪਟੀਮਾਈਜ਼ਰ, OTel ਐਕਸਪੋਰਟ, ਟੈਂਪਰ-ਇਵੀਡੈਂਟ ਆਡਿਟ ਲੌਗ | $19 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |

ਸਾਲਾਨਾ ਪਲਾਨ, Enterprise ਅਤੇ ਮੌਜੂਦਾ ਸੰਖਿਆਵਾਂ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** ਉੱਤੇ ਮੌਜੂਦ ਹਨ। ਸੈਲਫ-ਹੋਸਟਡ ਲਾਈਸੈਂਸ
ਕੀਆਂ ਕਲਾਊਡ ਤੋਂ ਬਿਨਾਂ ਕੰਮ ਕਰਦੀਆਂ ਹਨ (`clawmetry license`)। ਸਹੀ ਮੁਫ਼ਤ/ਭੁਗਤਾਨ ਵੰਡ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਵਿੱਚ ਹੈ।

## ਤੁਹਾਡਾ ਡਾਟਾ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਉੱਤੇ ਹੀ ਰਹਿੰਦਾ ਹੈ

ClawMetry ਲੋਕਲ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਅਤੇ ਲੌਗ ਪੜ੍ਹਦਾ ਹੈ। **ਜਦ ਤੱਕ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ
ਚਲਾਉਂਦੇ, ਤੁਹਾਡੇ ਬਾਕਸ ਤੋਂ ਕੋਈ ਸੈਸ਼ਨ ਡਾਟਾ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦਾ** — ਕੋਈ ਪ੍ਰੌਮਪਟ, ਜਵਾਬ, ਟੂਲ ਆਰਗਿਊਮੈਂਟ, ਫਾਈਲ
ਸਮੱਗਰੀ ਜਾਂ ਲੌਗ ਲਾਈਨਾਂ ਨਹੀਂ। ਜਦੋਂ ਤੁਸੀਂ ਕਨੈਕਟ ਕਰਦੇ ਹੋ, ਸਨੈਪਸ਼ਾਟ ਇੱਕ ਅਜਿਹੀ ਕੀ ਨਾਲ
ਐਂਡ-ਟੂ-ਐਂਡ ਏਨਕ੍ਰਿਪਟਡ ਹੁੰਦਾ ਹੈ ਜੋ ਕਦੇ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦੀ, ਅਤੇ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ
ਵਿੱਚ ਡੀਕ੍ਰਿਪਟ ਹੁੰਦਾ ਹੈ। ਜੇ ਕਿਸੇ ਨੋਡ ਕੋਲ ਕੋਈ ਕੀ ਨਹੀਂ ਹੈ, ਅੱਪਲੋਡ ਸਾਫ਼ ਭੇਜਣ ਦੇ ਬਦਲੇ
ਛੱਡ ਦਿੱਤਾ ਜਾਂਦਾ ਹੈ, ਅਤੇ ਕੋਈ ਵੀ ਸਰਵਰ ਜਵਾਬ ਇਸਨੂੰ ਬੰਦ ਨਹੀਂ ਕਰ ਸਕਦਾ।

ਕਨੈਕਟ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਦੋ ਚੀਜ਼ਾਂ ਪਹਿਲਾਂ ਤੋਂ ਹੀ ਚੱਲਦੀਆਂ ਹਨ, ਦੋਵੇਂ ਓਪਟ-ਆਊਟ ਹਨ ਅਤੇ ਕੋਈ ਵੀ
ਸੈਸ਼ਨ ਡਾਟਾ ਨਹੀਂ ਲੈ ਜਾਂਦੀਆਂ: ਇੱਕ ਅਗਿਆਤ ਇੰਸਟਾਲ ਪਿੰਗ ਅਤੇ PyPI ਦੇ ਵਿਰੁੱਧ ਇੱਕ ਵਰਜ਼ਨ
ਚੈਕ। ਇੱਕ ਡਿਫਾਲਟ ਇੰਸਟਾਲ ਸ਼ੁਰੂਆਤੀ ਬੈਨਰ ਲਾਈਨ ਲਈ ਇੱਕ ਵਾਰ ਤੁਹਾਡਾ ਪਬਲਿਕ IP ਵੀ ਲੱਭਦਾ ਹੈ।
ਹਰ ਟਿਕਾਣਾ, ਇਹ ਕੀ ਲੈ ਜਾਂਦਾ ਹੈ ਅਤੇ ਇਸਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰੀਏ, ਇਹ ਸਭ
[docs/EGRESS.md](docs/EGRESS.md) ਵਿੱਚ ਸੂਚੀਬੱਧ ਹੈ; ਸੈਲਫ-ਹੋਸਟਡ, ਰੀਪੌਇੰਟਡ ਅਤੇ ਏਅਰ-ਗੈਪਡ ਇੰਸਟਾਲ
ਬਿਲਕੁਲ ਕੋਈ ਵੀ ਸਵੈ-ਇੱਛਤ ਬਾਹਰੀ ਕਾਲ ਨਹੀਂ ਕਰਦੇ।

ਡੀਕ੍ਰਿਪਸ਼ਨ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਹੁੰਦੀ ਹੈ, ਉਸ ਕੋਡ ਨਾਲ ਜੋ ਅਸੀਂ ਤੁਹਾਨੂੰ ਦਿੰਦੇ ਹਾਂ। ਇਹ ਪਹਿਲਾਂ
ਇੱਕ ਵਾਅਦਾ ਸੀ; ਹੁਣ ਇਹ ਕੁਝ ਅਜਿਹਾ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਖੁਦ ਜਾਂਚ ਸਕਦੇ ਹੋ। ਹਰ ਲਾਈਨ ਜੋ ਤੁਹਾਡੀ ਕੀ ਨੂੰ
ਛੂੰਹਦੀ ਹੈ, ਇੱਕੋ ਪੜ੍ਹਨਯੋਗ ਫਾਈਲ ਵਿੱਚ ਹੈ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
ਜੋ wheel ਦੇ ਅੰਦਰ ਸ਼ਿੱਪ ਹੁੰਦੀ ਹੈ ਅਤੇ ਸ਼ਬਦ-ਦਰ-ਸ਼ਬਦ ਸਰਵ ਕੀਤੀ ਜਾਂਦੀ ਹੈ, ਇੱਕ Subresource
Integrity ਹੈਸ਼ ਨਾਲ ਪਿੰਨ ਕੀਤੀ ਗਈ। ਇਹ ਪੁਸ਼ਟੀ ਕਰਨ ਲਈ ਕਿ ਬ੍ਰਾਊਜ਼ਰ ਓਹੀ ਚਲਾ ਰਿਹਾ ਹੈ ਜੋ ਅਸੀਂ
ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਹੈ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ਇਹ ਕੀ ਸਾਬਤ ਨਹੀਂ ਕਰਦਾ: ਅਸੀਂ ਉਹ ਪੰਨਾ ਸਰਵ ਕਰਦੇ ਹਾਂ ਜੋ ਇਸ ਫਾਈਲ ਨੂੰ ਲੋਡ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ
ਅਸੀਂ ਇੱਕ ਵੱਖਰਾ ਪੰਨਾ ਵੀ ਸਰਵ ਕਰ ਸਕਦੇ ਹਾਂ। Integrity ਹੈਸ਼ ਤੁਹਾਨੂੰ ਇੱਕ ਖ਼ਰਾਬ ਹੋਏ CDN
ਤੋਂ ਬਚਾਉਂਦੇ ਹਨ, ਵੈਂਡਰ ਤੋਂ ਨਹੀਂ। ਤੁਹਾਨੂੰ ਜੋ ਮਿਲਦਾ ਹੈ ਉਹ ਇਹ ਹੈ ਕਿ ਕੋਈ ਵੀ ਬਦਲੀ
ਜਾਣ-ਬੁਝ ਕੇ, ਪੰਨੇ ਦੇ ਸੋਰਸ ਵਿੱਚ ਦਿਖਾਈ ਦੇਣ ਵਾਲੀ, ਅਤੇ PyPI ਉੱਤੇ ਮੌਜੂਦ ਉਸ ਆਰਟੀਫੈਕਟ ਤੋਂ
ਵੱਖਰੀ ਹੋਣੀ ਚਾਹੀਦੀ ਹੈ ਜਿਸਨੂੰ ਕੋਈ ਵੀ ਪ੍ਰਾਪਤ ਕਰ ਸਕਦਾ ਹੈ। ਸੈਲਫ-ਹੋਸਟਿੰਗ ਜਾਂ ਸਿਰਫ਼-ਲੋਕਲ ਰਹਿਣਾ
ਇਸ ਨਿਰਭਰਤਾ ਨੂੰ ਪੂਰੀ ਤਰ੍ਹਾਂ ਹਟਾ ਦਿੰਦਾ ਹੈ।

## ਇੰਸਟਾਲ

```bash
pip install clawmetry     # ਫਿਰ: clawmetry
```

ਜਾਂ ਵਨ-ਲਾਈਨਰ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ਜਾਂ Windows ਉੱਤੇ Python 3.8+ ਦੀ ਲੋੜ ਹੈ, ਅਤੇ ਇੱਕੋ ਮਸ਼ੀਨ ਉੱਤੇ
ਘੱਟੋ-ਘੱਟ ਇੱਕ ਏਜੰਟ ਰਨਟਾਈਮ। Docker ਹਦਾਇਤਾਂ: [docs/DOCKER.md](docs/DOCKER.md)।

ਜਾਂ ਏਜੰਟ ਨੂੰ ਤੁਹਾਡੇ ਲਈ ਇਸਨੂੰ ਸੈਟ ਅੱਪ ਕਰਨ ਦਿਓ। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ਹੁਨਰ Claude Code, Codex, Cursor, Gemini CLI, Copilot ਜਾਂ OpenCode ਨੂੰ ਸਿਖਾਉਂਦਾ ਹੈ ਕਿ
ClawMetry ਕਿਵੇਂ ਇੰਸਟਾਲ ਕਰਨਾ ਹੈ, ਮਸ਼ੀਨ ਉੱਤੇ ਏਜੰਟ ਕੀ ਕਰ ਰਹੇ ਹਨ ਅਤੇ ਖਰਚ ਕਰ ਰਹੇ ਹਨ ਇਸਦੀ
ਰਿਪੋਰਟ ਕਿਵੇਂ ਦੇਣੀ ਹੈ, ਬੇਨਤੀ ਉੱਤੇ ਇੱਕ ਸੈਸ਼ਨ ਕਿਵੇਂ ਰੋਕਣਾ ਹੈ, ਅਤੇ ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ
ਮਨਜ਼ੂਰੀ ਲਈ ਕਿਵੇਂ ਰੋਕਣਾ ਹੈ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ਦਸਤਾਵੇਜ਼

| | |
|---|---|
| [ਰਨਟਾਈਮ ਕੰਪੈਟੀਬਿਲਟੀ](docs/compatibility.md) | ਹਰ ਅਡੈਪਟਰ ਕੀ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਇੱਕ ਰਨਟਾਈਮ ਕਿਵੇਂ ਜੋੜੀਏ |
| [ਕਾਂਟੈਕਸਟ ਬਲੋਆਊਟ](docs/CONTEXT_BLOWOUT.md) | ਪ੍ਰਤੀ-ਪ੍ਰੋਵਾਈਡਰ ਵਿੰਡੋ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਓਵਰਫਲੋ, ਪ੍ਰਤੀ-ਰਨਟਾਈਮ ਕਵਰੇਜ |
| [ਓਵਰਹੈੱਡ](docs/OVERHEAD.md) | ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਲਾਗਤ, ਮਾਪੀ ਗਈ, ਇਸਨੂੰ ਦੁਬਾਰਾ ਪੈਦਾ ਕਰਨ ਵਾਲੇ ਹਾਰਨੈੱਸ ਨਾਲ |
| [ਹੱਕਦਾਰੀਆਂ](docs/ENTITLEMENTS.md) | ਮੁਫ਼ਤ ਬਨਾਮ ਭੁਗਤਾਨ, ਟਾਇਰ ਮੈਟ੍ਰਿਕਸ, ਲਾਈਸੈਂਸ CLI |
| [ਮਨਜ਼ੂਰੀਆਂ ਅਤੇ ਨੀਤੀਆਂ](docs/APPROVALS.md) | ਪ੍ਰੀ-ਐਗਜ਼ੀਕਿਊਸ਼ਨ ਗੇਟਿੰਗ, ਖ਼ਤਰਾ ਸਕੋਰਿੰਗ, ਫ਼ੋਨ ਮਨਜ਼ੂਰੀਆਂ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ਟਰੇਸ ਕਿਤੇ ਵੀ ਐਕਸਪੋਰਟ ਕਰੋ, ਕਿਸੇ ਵੀ ਥਾਂ ਤੋਂ OTLP ਇੰਜੈਸਟ ਕਰੋ |
| [ਆਪਣਾ ਖੁਦ ਦਾ ਏਜੰਟ ਲਿਆਓ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ਸ਼ੁਰੂ ਤੋਂ ਅੰਤ ਤੱਕ, ਚਲਾਉਣਯੋਗ ਉਦਾਹਰਣਾਂ ਨਾਲ |
| [SDK ਟਰੈਕਿੰਗ](docs/SDK_TRACKING.md) | ਖੁਦ ਬਣਾਏ ਏਜੰਟਾਂ ਲਈ ਲਾਗਤ ਵੰਡ |
| [ਚੈਟ ਚੈਨਲ](docs/CHANNELS.md) | ਫਲੋ ਵਿੱਚ ਦਿਖਾਏ ਚੈਟ ਅਡੈਪਟਰ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ਸੈਂਡਬਾਕਸਡ NVIDIA NemoClaw ਸੈੱਟਅੱਪ |
| [Docker](docs/DOCKER.md) | ਇਮੇਜ, ਕੰਪੋਜ਼, ਵਾਲਿਊਮ ਮਾਊਂਟ |
| [ਆਰਕੀਟੈਕਚਰ](ARCHITECTURE.md) · [ਵਿਕਾਸ](docs/DEVELOPMENT.md) | ਅੰਦਰ ਇਹ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ; ਸੋਰਸ ਤੋਂ ਚਲਾਉਣਾ |
| [ਟੈਲੀਮੈਟਰੀ](docs/TELEMETRY.md) | ਅਗਿਆਤ ਇੰਸਟਾਲ ਅਤੇ ਡੈਸਕਟਾਪ-ਓਪਨ ਪਿੰਗ, ਅਤੇ ਉਹਨਾਂ ਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰੀਏ |

## ਸਕ੍ਰੀਨਸ਼ਾਟ

ਹੇਠਾਂ ਦਿੱਤਾ ਹਰ ਅੰਕੜਾ ਇੱਕ ਅਸਲੀ ਮਸ਼ੀਨ ਤੋਂ ਹੈ, ਸਿਰਫ਼-ਪੜ੍ਹਨ ਲਈ, ਬਿਨਾਂ ਕੁਝ ਵੀ ਬਣਾਏ ਹੋਏ।

**ਇਹ ਤੁਹਾਨੂੰ ਦੱਸਦਾ ਹੈ ਜਦੋਂ ਕੁਝ ਗ਼ਲਤ ਹੁੰਦਾ ਹੈ, ਨਾ ਸਿਰਫ਼ ਕੀ ਹੋਇਆ।**
ਸਿਖਰ ਉੱਤੇ ਦੋ ਅਨੌਮਲੀ ਬੈਨਰ: ਖਰਚ ਰੋਜ਼ਾਨਾ ਔਸਤ ਦਾ 7 ਗੁਣਾ ਚੱਲ ਰਿਹਾ ਹੈ, ਅਤੇ ਇੱਕ
4.2x ਲਾਗਤ ਵਾਧਾ। ਉਹਨਾਂ ਦੇ ਹੇਠਾਂ, ਹਾਲੀਆ 667 ਸੈਸ਼ਨਾਂ ਵਿੱਚੋਂ 324 ਵਿੱਚ ਬਰਬਾਦੀ
ਸਿਗਨਲ ਮੌਜੂਦ ਹੈ, ਕਾਰਨ ਦੇ ਹਿਸਾਬ ਨਾਲ ਵੰਡਿਆ ਹੋਇਆ।

![ਓਵਰਵਿਊ: ਲਾਈਵ ਏਜੰਟ ਕੰਮ ਉੱਤੇ ਖਰਚ ਅਨੌਮਲੀ ਅਤੇ ਲਾਗਤ ਵਾਧਾ ਬੈਨਰ](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ਇਹ ਤੁਹਾਨੂੰ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਹਰ ਵਿੰਡੋ ਵਿੱਚ।**
ਅੱਜ $252.47, ਇਸ ਹਫ਼ਤੇ $513.15, ਇਸ ਮਹੀਨੇ $1,312.92, ਹਰ ਇੱਕ ਦੇ ਪਿੱਛੇ ਦੇ
ਟੋਕਨ ਨਾਲ ਅਤੇ ਇਹ ਕਿ ਤੁਹਾਡੀ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਪਹਿਲਾਂ ਹੀ ਇਸਦਾ ਕਿੰਨਾ ਹਿੱਸਾ ਕਵਰ ਕਰਦੀ ਹੈ। ਉਸਦੇ
ਹੇਠਾਂ, ਲਗਭਗ $1,128/ਮਹੀਨਾ ਮੁੜ-ਪ੍ਰਾਪਤ ਕਰਨ ਯੋਗ ਵਜੋਂ ਵੰਡਿਆ ਹੋਇਆ ਅਤੇ ਕੈਸ਼ ਦੁਬਾਰਾ
ਵਰਤੋਂ ਨਾਲ ਪਹਿਲਾਂ ਹੀ ਬਚਾਏ ਗਏ $17,256/ਮਹੀਨਾ।

![ਲਾਗਤ: ਅੱਜ, ਇਸ ਹਫ਼ਤੇ ਅਤੇ ਇਸ ਮਹੀਨੇ, ਇੱਕ ਕੁਸ਼ਲਤਾ ਗ੍ਰੇਡ ਅਤੇ ਵੰਡੇ ਹੋਏ ਬਚਤ ਵਿਚਾਰਾਂ ਨਾਲ](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ਇਹ ਦਰਸਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਸੁਨੇਹਾ ਕਿਵੇਂ ਇੱਕ ਜਵਾਬ ਬਣਦਾ ਹੈ।**
ਲਾਈਵ ਫਲੋ ਚਿੱਤਰ: ਤੁਸੀਂ, ਉਹ ਚੈਨਲ ਜਿਸ ਉੱਤੇ ਇਹ ਆਇਆ, ਗੇਟਵੇ, ਹੁਣੇ ਜਵਾਬ ਦੇ ਰਿਹਾ
ਮਾਡਲ, ਅਤੇ ਹਰ ਟੂਲ ਜਿਸ ਤੱਕ ਇਹ ਪਹੁੰਚਿਆ। ਨੋਡ ਉਦੋਂ ਜਗ ਉੱਠਦੇ ਹਨ ਜਦੋਂ ਕੰਮ ਉਹਨਾਂ ਵਿੱਚੋਂ
ਲੰਘਦਾ ਹੈ।

![ਫਲੋ: ਤੁਹਾਡੇ ਤੋਂ ਗੇਟਵੇ ਰਾਹੀਂ ਮਾਡਲ ਅਤੇ ਇਸਦੇ ਟੂਲਾਂ ਤੱਕ ਲਾਈਵ ਚਿੱਤਰ](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ਮਸ਼ੀਨ ਉੱਤੇ ਹਰ ਏਜੰਟ, ਇੱਕੋ ਸਾਰਣੀ ਵਿੱਚ।**
ਇਹ ਕੀ ਚਲਾਉਂਦਾ ਹੈ, ਪਿਛਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ਅਤੇ ਇਸਦੇ ਜੀਵਨ-ਭਰ ਵਿੱਚ ਇਸਦੀ ਲਾਗਤ ਕੀ ਹੈ, ਇਹ
ਆਖਰੀ ਵਾਰ ਕਦੋਂ ਦੇਖਿਆ ਗਿਆ, ਇਸਦਾ ਮਾਲਕ ਕੌਣ ਹੈ, ਅਤੇ ਕੀ ਕੋਈ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਬਿੱਲ ਕਵਰ ਕਰ ਰਹੀ
ਹੈ। ਇੱਥੇ 14 ਏਜੰਟ, 3 ਸੈਸ਼ਨ ਕੰਮ ਕਰ ਰਹੇ, 13 ਸ਼ਾਂਤ।

![ਏਜੰਟ: ਮਸ਼ੀਨ ਉੱਤੇ ਹਰ ਰਨਟਾਈਮ ਲਾਗਤ, ਮਾਲਕ, ਆਖਰੀ ਵਾਰ ਦੇਖੇ ਜਾਣ ਅਤੇ ਮੌਜੂਦਾ ਕੰਮ ਨਾਲ](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਵਾਰੀ ਦਾ ਸਮਾਂ ਅਤੇ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਟੂਲ-ਦਰ-ਟੂਲ।**
ਇੱਕ ਅਸਲੀ ਸੈਸ਼ਨ ਦੀ ਇੱਕ ਵਾਰੀ: 11.2 ਮਿੰਟਾਂ ਵਿੱਚ $1.16 ਲਈ 11 ਟੂਲ। ਹਰ Bash
ਕਾਲ ਅਤੇ ਮਾਡਲ ਕਾਲ ਨੂੰ ਟਾਈਮਲਾਈਨ ਉੱਤੇ ਆਪਣਾ ਬਾਰ ਮਿਲਦਾ ਹੈ, ਇਸ ਲਈ 4.1 ਮਿੰਟ ਚੱਲੀ
ਕਮਾਂਡ ਅਤੇ 226ms ਚੱਲੀ ਕਮਾਂਡ ਵਿੱਚ ਇੱਕ ਨਜ਼ਰ ਨਾਲ ਫ਼ਰਕ ਪਤਾ ਲੱਗ ਜਾਂਦਾ ਹੈ।

![ਸੈਸ਼ਨ: ਇੱਕ ਏਜੰਟ ਵਾਰੀ ਟਾਈਮਲਾਈਨ ਉੱਤੇ, ਹਰ ਟੂਲ ਕਾਲ ਆਪਣੀ ਮਿਆਦ ਅਤੇ ਵਾਰੀ ਦੀ ਲਾਗਤ ਨਾਲ](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ਇਹ ਕੰਮ ਦੀ ਗ੍ਰੇਡਿੰਗ ਕਰਦਾ ਹੈ, ਨਾ ਸਿਰਫ਼ ਖਰਚ ਦੀ।**
ਇਸ ਹਫ਼ਤੇ A: 54 ਕੰਮ ਸਾਫ਼ ਵਾਪਸ ਆਏ, 2 ਖ਼ਰਾਬ ਕੰਮਾਂ ਦੀ ਲਾਗਤ $48.57 ਹੋਈ, ਅਤੇ ਓਹ
ਰਨ ਜਿਹਨਾਂ ਵਿੱਚ ਨਿਰਣਾ ਕਰਨ ਲਈ ਬਹੁਤ ਘੱਟ ਗਤੀਵਿਧੀ ਸੀ ਉਹਨਾਂ ਨੂੰ ਜਿੱਤ ਵਜੋਂ ਗਿਣੇ ਜਾਣ ਦੇ ਬਦਲੇ
ਗ੍ਰੇਡ ਵਿੱਚੋਂ ਬਾਹਰ ਛੱਡ ਦਿੱਤਾ ਗਿਆ। ਹਰ ਖ਼ਰਾਬ ਰਨ ਆਪਣੇ ਟਰੇਸ ਨਾਲ ਜੁੜਦਾ ਹੈ।

![ਗੁਣਵੱਤਾ: ਖ਼ਰਾਬ ਰਨਾਂ ਅਤੇ ਉਹਨਾਂ ਦੀ ਲਾਗਤ ਨਾਲ ਇਸ ਹਫ਼ਤੇ ਦਾ ਰਿਪੋਰਟ ਕਾਰਡ](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਕਾਂਟੈਕਸਟ ਵਿੰਡੋ ਕਿਉਂ ਭਰਦੀ ਰਹਿੰਦੀ ਹੈ।**
ਆਖਰੀ ਵਾਰੀ ਵਿੱਚ 1M-ਟੋਕਨ ਵਿੰਡੋ ਦੇ 715K, 83.3% ਦਾ ਸਿਖਰ, 4 ਕੰਪੈਕਸ਼ਨ ਜੋ ਸਭ
ਓਵਰਫਲੋ ਉੱਤੇ ਨਹੀਂ ਸਗੋਂ ਸਰਗਰਮੀ ਨਾਲ ਪਹਿਲਾਂ ਹੀ ਚੱਲੇ, ਅਤੇ ਇਸਦੇ ਪਿੱਛੇ ਹਰ ਵਾਰੀ ਦੀ ਵਰਤੋਂ।

![ਕਾਂਟੈਕਸਟ ਵਰਤੋਂ: ਹਰ ਵਾਰੀ ਦੀ ਵਿੰਡੋ ਵਰਤੋਂ, ਕੰਪੈਕਸ਼ਨ ਈਵੈਂਟ ਅਤੇ ਮੁੜ-ਪ੍ਰਾਪਤ ਕੀਤੇ ਟੋਕਨ](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ਖੋਜ ਬਿਨਾਂ ਤੁਹਾਡੇ ਕੁਝ ਵੀ ਕਾਨਫਿਗਰ ਕੀਤੇ ਚੱਲਦੀ ਹੈ।**
ਬਿਲਟ-ਇਨ ਡਿਟੈਕਟਰ ਇੰਸਟਾਲ ਤੋਂ ਹੀ ਚਾਲੂ ਹਨ: ਏਜੰਟ ਸ਼ਾਂਤ ਹੋ ਗਿਆ, ਟੈਲੀਮੈਟਰੀ ਫੀਡ
ਰੁਕ ਗਈ, ਲਾਗਤ ਵਾਧਾ, ਟੋਕਨ ਵਾਧਾ, ਗਲਤੀਆਂ ਵਧ ਰਹੀਆਂ, ਗਲਤੀ ਵਾਧਾ, ਬਜਟ
ਸੀਮਾ, ਖ਼ਤਰਾ ਦਸਤਖ਼ਤ ਮਿਲਿਆ, ਸੁਰੱਖਿਆ ਟੂਲ ਖੋਜ, ਸੁਰੱਖਿਆ ਸਥਿਤੀ
ਬਦਲੀ। ਤੁਹਾਡੇ ਖੁਦ ਦੇ ਨਿਯਮ ਇਸਦੇ ਉੱਪਰ ਵਿਕਲਪਿਕ ਹਨ।

![ਅਲਰਟ: ਬਿਲਟ-ਇਨ ਡਿਟੈਕਟਰ ਨਾਲ ਵਿਕਲਪਿਕ ਕਸਟਮ ਨਿਯਮ](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ਖ਼ਤਰਨਾਕ ਕਾਲ ਨੂੰ ਰੋਕਣਾ ਓਪਟ-ਇਨ ਹੈ, ਅਤੇ ਬੰਦ ਹੀ ਸ਼ਿੱਪ ਹੁੰਦਾ ਹੈ।**
ਰੀਕਰਸਿਵ ਡਿਲੀਟ, ਫੋਰਸ ਪੁਸ਼, sudo, ਭੇਦ, ਪੈਕੇਜ ਇੰਸਟਾਲ ਅਤੇ ਬਾਹਰੀ
ਕਾਲਾਂ ਵਿੱਚੋਂ ਹਰ ਇੱਕ ਨੂੰ ਇੱਕ ਨਿਯਮ ਮਿਲਦਾ ਹੈ ਜੋ ਤੁਸੀਂ ਚਾਲੂ ਕਰ ਸਕਦੇ ਹੋ। ਜਦ ਤੱਕ ਤੁਸੀਂ ਨਹੀਂ
ਕਰਦੇ, ClawMetry ਦੇਖਦਾ ਹੈ ਅਤੇ ਕੁਝ ਨਹੀਂ ਬਦਲਦਾ। ਇੱਕ ਵਾਰ ਚਾਲੂ ਹੋਣ ਤੇ, ਮਿਲਦੀਆਂ ਕਾਲਾਂ
ਇੱਥੇ (ਜਾਂ ਤੁਹਾਡੇ ਫ਼ੋਨ ਉੱਤੇ) ਮਨਜ਼ੂਰੀ ਜਾਂ ਇਨਕਾਰ ਲਈ ਉਡੀਕ ਕਰਦੀਆਂ ਹਨ।

![ਮਨਜ਼ੂਰੀਆਂ: ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਲਈ ਸੁਰੱਖਿਆ ਨਿਯਮ, ਜਿਹਨਾਂ ਨੂੰ ਤੁਸੀਂ ਚਾਲੂ ਕਰੋ ਉਦੋਂ ਤੱਕ ਸਭ ਬੰਦ](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

ਹੋਰ, ਹਰ ਰਨਟਾਈਮ ਲਈ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## ਮਾਨਤਾ

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
