<!-- i18n-src:c99ac0512cae -->
> ਪੰਜਾਬੀ translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ਇੱਕ ਏਜੰਟ ਬਿਨਾਂ ਕੋਈ ਤਰੱਕੀ ਕੀਤੇ ਸੌ ਟੂਲ ਕਾਲਾਂ ਕਰ ਸਕਦਾ ਹੈ।** ClawMetry
ਤੁਹਾਡੇ ਕੋਡਿੰਗ ਏਜੰਟਾਂ ਵੱਲੋਂ ਪਹਿਲਾਂ ਹੀ ਲਿਖੀਆਂ ਗਈਆਂ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਨੂੰ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ
ਟਾਈਮਲਾਈਨ, ਟੂਲ ਕਾਲਾਂ ਅਤੇ ਰਨਟਾਈਮ ਵੱਲੋਂ ਦਿੱਤੇ ਜਾਂਦੇ ਕਿਸੇ ਵੀ ਟੋਕਨ ਅਤੇ ਕੀਮਤ ਡੇਟਾ ਨੂੰ
ਇੱਕ ਹੀ ਵਿਊ ਵਿੱਚ ਪਾ ਦਿੰਦਾ ਹੈ — ਤਾਂ ਜੋ ਤੁਸੀਂ ਇੱਕ ਲੰਮੀ ਚੱਲ ਰਹੀ ਰਨ ਜੋ ਕੰਮ ਕਰ ਰਹੀ ਹੈ ਨੂੰ
ਉਸ ਤੋਂ ਵੱਖ ਕਰ ਸਕੋ ਜੋ ਅਟਕ ਗਈ ਹੈ।

**33 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ — Claude Code, OpenAI Codex, Hermes, OpenClaw ਅਤੇ 29 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ। ([ਪੂਰੀ ਸੂਚੀ](SUPPORTED_RUNTIMES.txt), ਕੈਟਾਲਾਗ ਤੋਂ ਤਿਆਰ ਕੀਤੀ ਗਈ।)

> 🌐 **ਇਹ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਕੋਈ ਕਨਫਿਗ ਨਹੀਂ। ਸਭ ਕੁਝ ਆਪਣੇ-ਆਪ ਪਛਾਣਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 'ਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ। ਕੋਈ ਕਨਫਿਗ ਨਹੀਂ: ਇਹ ਉਹ ਏਜੰਟ ਰਨਟਾਈਮ ਲੱਭ ਲੈਂਦਾ ਹੈ
ਜੋ ਤੁਹਾਡੇ ਕੋਲ ਪਹਿਲਾਂ ਹੀ ਹਨ, ਉਹਨਾਂ ਨੂੰ ਸਿਰਫ਼-ਪੜ੍ਹਨ ਲਈ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਇਸ ਗੱਲ ਵਿੱਚ ਕੁਝ ਵੀ ਨਹੀਂ
ਬਦਲਦਾ ਕਿ ਉਹ ਕਿਵੇਂ ਚੱਲਦੇ ਹਨ।

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ਇੰਸਟਾਲ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ

| | |
|---|---|
| **ਇਹ ਕੀ ਕਰਦਾ ਹੈ** | ਉਹ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਅਤੇ ਲਾਗਾਂ ਪੜ੍ਹਦਾ ਹੈ ਜੋ ਤੁਹਾਡੇ ਏਜੰਟ ਪਹਿਲਾਂ ਹੀ ਲਿਖਦੇ ਹਨ। ਕੋਈ SDK ਨਹੀਂ, ਕੋਈ ਕੋਡ ਤਬਦੀਲੀ ਨਹੀਂ, ਤੁਹਾਡੀ ਐਪ ਵਿੱਚ ਕੋਈ ਇੰਸਟਰੂਮੈਂਟੇਸ਼ਨ ਨਹੀਂ। |
| **ਤੁਸੀਂ ਕੀ ਦੇਖਦੇ ਹੋ** | ਸੈਸ਼ਨ ਟਾਈਮਲਾਈਨ, ਟੂਲ-ਦਰ-ਟੂਲ ਰੀਪਲੇ, ਟੋਕਨ ਅਤੇ ਕੀਮਤ ਦਾ ਵੇਰਵਾ, ਅਤੇ ਟ੍ਰੈਜੈਕਟਰੀ ਸਿਗਨਲ (ਲੂਪਿੰਗ, ਦੁਹਰਾਈ ਜਾਣ ਵਾਲੀ ਅਸਫਲਤਾ) — ਹਰ ਰਨਟਾਈਮ ਲਈ। |
| **ਕੀ ਮੁਫ਼ਤ ਹੈ** | `pip install clawmetry` **OpenClaw, NVIDIA NemoClaw, Goose ਅਤੇ Qwen Code** ਨੂੰ ਬਿਨਾਂ ਕਿਸੇ ਖਾਤੇ, ਬਿਨਾਂ ਕੁੰਜੀ ਅਤੇ ਬਿਨਾਂ ਨੈੱਟਵਰਕ ਕਾਲ ਦੇ ਪੜ੍ਹਦਾ ਹੈ। ਬਾਕੀ 28 — Claude Code, Codex, Cursor ਅਤੇ ਬਾਕੀ — ਨੂੰ ਕਲੋਜ਼ਡ-ਸੋਰਸ `clawmetry-pro` ਕੰਪੈਨੀਅਨ ਵੱਲੋਂ ਪੜ੍ਹਿਆ ਜਾਂਦਾ ਹੈ, ਜੋ 7-ਦਿਨਾਂ ਟ੍ਰਾਇਲ ਜਾਂ ਕਿਸੇ ਪਲਾਨ ਨਾਲ ਆਉਂਦਾ ਹੈ — ਸਹੀ ਵੰਡ ਲਈ [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਦੇਖੋ। |
| **ਕਿਵੇਂ ਸ਼ੁਰੂ ਕਰੀਏ** | `pip install clawmetry && clawmetry`, ਫਿਰ localhost:8900 ਖੋਲ੍ਹੋ। ਇਸ ਮਸ਼ੀਨ 'ਤੇ ਅਜੇ ਕੋਈ ਏਜੰਟ ਨਹੀਂ? `clawmetry --sample` ਤਿੰਨ ਲੇਬਲਡ ਸਿੰਥੈਟਿਕ ਸੈਸ਼ਨਾਂ 'ਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ। |
| **ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਕੀ ਬਾਹਰ ਜਾਂਦਾ ਹੈ** | ਕੋਈ ਸੈਸ਼ਨ ਡੇਟਾ ਨਹੀਂ, ਜੇ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ ਚਲਾਉਂਦੇ। ਮੂਲ ਰੂਪ ਵਿੱਚ ਦੋ ਚੀਜ਼ਾਂ ਚੱਲਦੀਆਂ ਹਨ, ਦੋਵੇਂ ਆਪਟ-ਆਉਟ ਅਤੇ ਕੋਈ ਵੀ ਸੈਸ਼ਨ ਸਮੱਗਰੀ ਨਹੀਂ ਲੈ ਜਾਂਦੀ: ਇੱਕ ਅਨਾਮਿਕ ਇੰਸਟਾਲ ਪਿੰਗ ਅਤੇ ਇੱਕ PyPI ਵਰਜ਼ਨ ਜਾਂਚ। ਹਰ ਮੰਜ਼ਿਲ [docs/EGRESS.md](docs/EGRESS.md) ਵਿੱਚ ਸੂਚੀਬੱਧ ਹੈ, ਜੋ ਟਿੱਪਣੀਆਂ ਪੜ੍ਹਨ ਦੀ ਬਜਾਏ ਇੱਕ ਵਾਇਰ ਕੈਪਚਰ ਤੋਂ ਦੁਬਾਰਾ ਬਣਾਈ ਗਈ ਹੈ। |

ਨਤੀਜੇ ਦਾ ਨਿਰਣਾ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਜਾਣਨ ਯੋਗ ਦੋ ਸੀਮਾਵਾਂ: ਰਨਟਾਈਮ ਬਹੁਤ
ਵੱਖਰਾ ਡੇਟਾ ਦਿਖਾਉਂਦੇ ਹਨ (ਕੁਝ ਕੋਈ ਕੀਮਤ ਬਿਲਕੁਲ ਨਹੀਂ ਦਿਖਾਉਂਦੇ — [ਮੈਟ੍ਰਿਕਸ](docs/compatibility.md)
ਦੱਸਦਾ ਹੈ ਕਿ ਹਰ ਰਨਟਾਈਮ ਲਈ ਕੀ ਹੈ), ਅਤੇ ਕਿਸੇ ਕਾਰਵਾਈ ਨੂੰ ਦੇਖਣਾ ਉਸ ਨੂੰ ਰੋਕਣ ਦੀ
ਸਮਰੱਥਾ ਵਾਂਗ ਨਹੀਂ ਹੈ ([ਕਿਹੜੇ ਕੰਟਰੋਲ ਅਸਲੀ ਹਨ, ਹਰ ਰਨਟਾਈਮ ਲਈ](docs/APPROVALS.md))।


## 33 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

**ਓਪਨ ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**ਕਿਸੇ ਭੁਗਤਾਨ ਵਾਲੇ ਪਲਾਨ 'ਤੇ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ਹਰ ਰਨਟਾਈਮ ਨੂੰ ਇੱਕੋ ਡੈਸ਼ਬੋਰਡ ਮਿਲਦਾ ਹੈ। ਇੱਕੋ ਵੇਲੇ ਕਈ ਚਲਾਓ ਅਤੇ ਹੈਡਰ
ਸਵਿੱਚਰ ਹਰ ਟੈਬ ਨੂੰ ਉਹਨਾਂ ਵਿੱਚੋਂ ਇੱਕ ਲਈ ਦੁਬਾਰਾ-ਸਕੋਪ ਕਰ ਦਿੰਦਾ ਹੈ।

ਆਪਣਾ ਏਜੰਟ ਕਿਸੇ SDK 'ਤੇ ਬਣਾਇਆ ਹੈ? ਇੰਟਰਸੈਪਟਰ ਉਸਦੀਆਂ LLM ਕਾਲਾਂ ਵੀ
ਟਰੈਕ ਕਰਦਾ ਹੈ। [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) ਦੇਖੋ।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **ਸੈਸ਼ਨ ਅਤੇ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ**: ਹਰ ਏਜੰਟ ਨੇ ਕੀ ਕੀਤਾ, ਵਾਰੀ-ਦਰ-ਵਾਰੀ, ਰੀਪਲੇ ਦੇ ਨਾਲ
- **ਕੀਮਤ ਅਤੇ ਟੋਕਨ**: ਰਨਟਾਈਮ, ਮਾਡਲ, ਸੈਸ਼ਨ ਅਤੇ ਦਿਨ ਦੇ ਹਿਸਾਬ ਨਾਲ, ਅਸਾਧਾਰਨਤਾ ਫਲੈਗਾਂ ਨਾਲ
- **ਫਲੋ**: ਚੈਨਲਾਂ, ਮਾਡਲਾਂ ਅਤੇ ਟੂਲਾਂ ਵਿੱਚੋਂ ਲੰਘ ਰਹੇ ਸੁਨੇਹਿਆਂ ਦਾ ਲਾਈਵ ਡਾਇਆਗ੍ਰਾਮ
- **ਬ੍ਰੇਨ**: ਜਿਵੇਂ ਹੁੰਦਾ ਹੈ, ਰੀਜ਼ਨਿੰਗ ਅਤੇ ਟੂਲ-ਕਾਲ ਈਵੈਂਟ ਸਟ੍ਰੀਮ
- **ਕੰਟੈਕਸਟ ਬਲੋਆਉਟ**: ਹਰ ਪ੍ਰੋਵਾਈਡਰ ਲਈ ਵਿੰਡੋ ਉਪਯੋਗਤਾ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਜ਼ੋਰੀ ਓਵਰਫਲੋ, ਨਾਲ ਹੀ ਹਰ ਰਨਟਾਈਮ ਲਈ ਇਹ ਨਕਸ਼ਾ ਕਿ ਅਸੀਂ *ਕੀ ਨਹੀਂ* ਦੇਖ ਸਕਦੇ ([ਕਿਵੇਂ](docs/CONTEXT_BLOWOUT.md))
- **ਮੈਮਰੀ ਅਤੇ ਸਕਿੱਲ**: ਉਹ ਫਾਈਲਾਂ ਅਤੇ ਸਕਿੱਲ ਜੋ ਹਰ ਰਨਟਾਈਮ ਨੇ ਅਸਲ ਵਿੱਚ ਲੋਡ ਕੀਤੇ
- **ਸਿਹਤ ਅਤੇ ਲਾਗ**: ਡਿਸਕ, ਮੈਮਰੀ, ਐਰਰ ਰੇਟ, ਰੇਟ ਲਿਮਟ, ਲਾਈਵ ਲਾਗ ਸਟ੍ਰੀਮ
- **ਅਲਰਟ**: ਬਜਟ ਕੈਪ, ਐਰਰ ਸਪਾਈਕ, ਏਜੰਟ-ਆਫਲਾਈਨ, Slack, Discord, PagerDuty, Telegram, Email ਨੂੰ ਰੂਟ ਕੀਤੇ
- **ਅਪਰੂਵਲ**: ਜੋਖਮ ਭਰੀਆਂ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਚੱਲਣ ਤੋਂ *ਪਹਿਲਾਂ* ਰੋਕੋ ਅਤੇ ਆਪਣੇ ਫੋਨ ਤੋਂ ਮਨਜ਼ੂਰ ਕਰੋ ([ਕਿਵੇਂ](docs/APPROVALS.md))

## ਕੰਟੈਕਸਟ ਬਲੋਆਉਟ, ਅਤੇ ਦੇਖਣ ਦੀ ਕੀਮਤ

ਕਿਸੇ ਵੀ ਏਜੰਟ-ਤੁਲਨਾ ਟੂਲ 'ਤੇ ਭਰੋਸਾ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਜਵਾਬ ਦੇਣ ਯੋਗ ਦੋ ਸਵਾਲ।

**ਇਹ ਵੱਖ-ਵੱਖ ਰਨਟਾਈਮਾਂ ਵਿੱਚ ਕੰਟੈਕਸਟ-ਵਿੰਡੋ ਬਲੋਆਉਟ ਨੂੰ ਕਿਵੇਂ ਸੰਭਾਲਦਾ ਹੈ?**

ਉਪਯੋਗਤਾ ਪ੍ਰਤੀਸ਼ਤ ਸਿਰਫ਼ ਉਸੇ ਹੱਦ ਤੱਕ ਇਮਾਨਦਾਰ ਹੈ ਜਿੰਨਾ ਉਹ ਭਾਜਕ ਹੈ। ClawMetry
ਹਰ ਪ੍ਰੋਵਾਈਡਰ ਲਈ [ਇੱਕ ਟੇਬਲ ਜਿਸ ਨੂੰ ਤੁਸੀਂ ਪੜ੍ਹ ਸਕਦੇ ਹੋ ਅਤੇ PR ਕਰ ਸਕਦੇ ਹੋ](clawmetry/context_windows.py)
ਤੋਂ ਵਿੰਡੋ ਦਾ ਆਕਾਰ ਤੈਅ ਕਰਦਾ ਹੈ, ਜੋ Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama ਅਤੇ GLM ਨੂੰ ਕਵਰ ਕਰਦਾ ਹੈ। ਇਹ ਸਾਰੇ 33
ਰਨਟਾਈਮਾਂ ਨੂੰ ਇੱਕ ਹੀ ਵੈਂਡਰ ਦੇ ਸਕੇਲ ਨਾਲ ਨਹੀਂ ਮਾਪਦਾ। ਇਹ ਗੱਲ ਮਹੱਤਵ ਰੱਖਦੀ ਹੈ: ਇੱਕ
300K GPT-5 ਵਾਰੀ ਨੂੰ Anthropic ਦੇ 200K ਦੇ ਵਿਰੁੱਧ ਪੜ੍ਹਿਆ ਜਾਵੇ ਤਾਂ ">100%, ਬਲੋਨ"
ਪੜ੍ਹਿਆ ਜਾਂਦਾ ਹੈ ਜਦੋਂ ਕਿ ਇਹ ਅਸਲ ਵਿੱਚ GPT-5 ਦੇ 400K ਦਾ 75% ਹੈ। ਉਹੀ ਸਕੇਲ ਇੱਕ ਸੱਚਮੁੱਚ
ਓਵਰਫਲੋਡ 130K DeepSeek ਵਾਰੀ ਨੂੰ ਇੱਕ ਆਰਾਮਦਾਇਕ 65% ਵਜੋਂ ਲੁਕਾ ਦਿੰਦਾ ਹੈ।

ਹਰ ਵਿੰਡੋ ਆਪਣੀ ਉਤਪਤੀ ਦੇ ਨਾਲ ਆਉਂਦੀ ਹੈ: `model_table`, `explicit_marker`,
`observed_floor`, ਜਾਂ ਇੱਕ ਇਮਾਨਦਾਰ `default` ਜਦੋਂ ਸਾਨੂੰ ਮਾਡਲ ਨਹੀਂ ਪਤਾ। ਕਿਸੇ
ਅਨੁਮਾਨ 'ਤੇ ਬਣਿਆ ਗੇਜ ਕਦੇ ਵੀ ਕਿਸੇ ਲੁਕ-ਅੱਪ 'ਤੇ ਬਣੇ ਗੇਜ ਜਿੰਨੀ ਅਧਿਕਾਰਤਾ ਨਾਲ
ਨਹੀਂ ਦਿਖਦਾ।

ClawMetry ਕੁਝ ਰਨਟਾਈਮਾਂ 'ਤੇ ਹੀ ਕੰਪੈਕਸ਼ਨ ਈਵੈਂਟ ਦੇਖ ਸਕਦਾ ਹੈ। ਇਸ ਲਈ
`GET /api/context-coverage` ਹਰ ਰਨਟਾਈਮ ਲਈ ਰਿਪੋਰਟ ਕਰਦਾ ਹੈ ਕਿ ਕੀ ਇੱਕ **ਜ਼ੀਰੋ ਦਾ ਮਤਲਬ
"ਸਾਫ਼ ਚੱਲਿਆ" ਹੈ ਜਾਂ "ਸਾਨੂੰ ਨਹੀਂ ਦਿਖਦਾ"**। ਇੱਕ `0` ਜਿਸਦਾ ਅਸਲ ਵਿੱਚ ਮਤਲਬ
ਅੰਨ੍ਹਾਪਣ ਹੈ ਉਹ ਇਹ ਕਹਿੰਦਾ ਹੈ।
[ਪੂਰੀ ਜਾਣਕਾਰੀ](docs/CONTEXT_BLOWOUT.md)

**ਇੰਸਟ੍ਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਕੀਮਤ ਕੀ ਹੈ?**

| ਪਾਥ | ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਜੋੜਿਆ ਗਿਆ | ਮੂਲ? |
|---|---|---|
| ਸੈਸ਼ਨ-ਫਾਈਲ ਟੇਲਿੰਗ (ਸਾਰੇ 33 ਰਨਟਾਈਮ) | **0**। ਵੱਖਰੀ ਪ੍ਰਕਿਰਿਆ, ਤੁਹਾਡੇ ਏਜੰਟ ਵਿੱਚ ਕੋਈ ClawMetry ਕੋਡ ਨਹੀਂ | ਚਾਲੂ |
| HTTP ਇੰਟਰਸੈਪਟਰ (`CLAWMETRY_INTERCEPT=1`) | ਹਰ LLM ਕਾਲ ਲਈ **+0.44 ms**, ਜਾਂ 5s ਕਾਲ ਦਾ 0.009% | ਬੰਦ |
| ਪ੍ਰੀ-ਟੂਲ ਹੁੱਕ ਗੇਟ (ਵਾਰਮ ਕੈਸ਼) | ਹਰ ਗੇਟਿਡ ਟੂਲ ਕਾਲ ਲਈ **+44 ms**, 36 ms ਇੰਟਰਪ੍ਰੈਟਰ ਫਲੋਰ ਤੋਂ ਵੱਧ | ਬੰਦ |
| ਐਨਫੋਰਸਮੈਂਟ ਪ੍ਰੌਕਸੀ | ਹਰ LLM ਕਾਲ ਲਈ **+9.7 ms** | ਬੰਦ |

ਡੈਮਨ ਹੋਸਟ ਕੀਮਤ: **2,762 ਈਵੈਂਟ/ਸੈਕਿੰਡ** ਇੰਜੈਸਟ, ਡਿਸਕ 'ਤੇ **710 ਬਾਈਟ/ਈਵੈਂਟ**
(100k ਈਵੈਂਟਾਂ ਲਈ 67.7 MB), ਅਤੇ ਕਿਸੇ ਰੁੱਝੇ ਹੋਏ ਇੰਸਟਾਲ 'ਤੇ **ਇੱਕ ਕੋਰ ਦੇ ਲਗਭਗ 12%**
ਟਿਕਿਆ ਹੋਇਆ। ਉਹ ਆਖਰੀ ਅੰਕ ਸਾਡੇ ਆਪਣੇ ਬਿਆਨ ਕੀਤੇ 5-10% ਬਜਟ ਤੋਂ ਵੱਧ ਹੈ, ਇਸ ਲਈ ਇਸਨੂੰ
ਪੇਜ ਤੋਂ ਛੁਪਾਉਣ ਦੀ ਬਜਾਏ ਪਿੱਛਾ ਕਰਨ ਲਈ ਇੱਕ ਬੱਗ ਵਜੋਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਗਿਆ ਹੈ।

Apple M2 Pro 'ਤੇ `benchmarks/overhead.py` ਨਾਲ ਮਾਪਿਆ ਗਿਆ। ਹਾਰਨੈਸ
ਹਰ ਹਾਲਤ ਨੂੰ ਵੱਖਰੀ ਪ੍ਰਕਿਰਿਆ ਵਿੱਚ ਚਲਾਉਂਦਾ ਹੈ, ਉਹਨਾਂ ਦੇ ਕ੍ਰਮ ਨੂੰ ਬਦਲਦਾ ਹੈ, ਅਤੇ **ਜਦੋਂ
ਰਾਊਂਡ ਉਸਦੇ ਸਾਈਨ 'ਤੇ ਅਸਹਿਮਤ ਹੁੰਦੇ ਹਨ ਤਾਂ ਕੋਈ ਅੰਕ ਛਾਪਣ ਤੋਂ ਇਨਕਾਰ ਕਰ ਦਿੰਦਾ ਹੈ**। ਇਸਨੂੰ
ਆਪਣੀ ਮਸ਼ੀਨ 'ਤੇ ਇੱਕ ਮਿੰਟ ਵਿੱਚ ਚਲਾਓ:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ਹਰ ਪਾਥ ਮਾਪਿਆ ਗਿਆ ਹੈ, ਜਿਸ ਵਿੱਚ ਹੁੱਕ ਗੇਟ ਅਤੇ ਐਨਫੋਰਸਮੈਂਟ ਪ੍ਰੌਕਸੀ ਵੀ ਸ਼ਾਮਲ ਹਨ,
ਅਤੇ ਹਾਰਨੈਸ CI ਵਿੱਚ Linux, macOS ਅਤੇ Windows 'ਤੇ ਚੱਲਦਾ ਹੈ। ਜਾਣਨ ਯੋਗ ਦੋ ਨਤੀਜੇ:
ਪ੍ਰੌਕਸੀ ਦੀ ਕੀਮਤ Windows 'ਤੇ Linux ਨਾਲੋਂ ਲਗਭਗ ਸੱਤ ਗੁਣਾ ਵੱਧ ਹੈ, ਅਤੇ
ਡੈਮਨ ਇਸ ਵੇਲੇ ਇੱਕ ਕੋਰ ਦੇ ਲਗਭਗ 12% ਨੂੰ ਟਿਕਾਉਂਦਾ ਹੈ, ਜੋ ਸਾਡੇ ਆਪਣੇ 5-10% ਬਜਟ ਤੋਂ
ਵੱਧ ਹੈ। ਕੱਚਾ JSON, ਤਰੀਕਾ, ਅਤੇ ਜੋ ਅਜੇ ਵੀ ਨਾ-ਮਾਪਿਆ ਹੈ ਉਹ
[docs/OVERHEAD.md](docs/OVERHEAD.md) ਵਿੱਚ ਹਨ।

## ਕੀਮਤ

| ਪਲਾਨ | ਕੀ ਕਵਰ ਕਰਦਾ ਹੈ | ਕੀਮਤ |
|---|---|---|
| **ਮੁਫ਼ਤ** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, ਪੂਰਾ ਡੈਸ਼ਬੋਰਡ, ਸਿਰਫ਼ ਲੋਕਲ | $0 |
| **ਸਟਾਰਟਰ** | ਉੱਪਰ ਦੱਸੇ ਹਰ ਹੋਰ ਰਨਟਾਈਮ, ਫਲੀਟ ਵਿਊ, ਕਲਾਉਡ ਸਿੰਕ | $9 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |
| **Pro** | ਸਟਾਰਟਰ + ਕੰਟਰੋਲ ਅਤੇ ਇਵੈਲੂਏਸ਼ਨ: ਅਪਰੂਵਲ, ਟੂਲ-ਰਿਸਕ ਪਾਲਿਸੀਆਂ, ਇਵਲਸ, ਐਨੋਮਲੀ ਡਿਟੈਕਸ਼ਨ, ਕੌਸਟ ਆਪਟੀਮਾਈਜ਼ਰ, OTel ਐਕਸਪੋਰਟ, ਟੈਂਪਰ-ਇਵੀਡੈਂਟ ਆਡਿਟ ਲਾਗ | $19 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |

ਸਲਾਨਾ ਪਲਾਨ, Enterprise ਅਤੇ ਮੌਜੂਦਾ ਅੰਕ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** 'ਤੇ ਹਨ। ਸੈਲਫ-ਹੋਸਟਡ ਲਾਇਸੈਂਸ
ਕੁੰਜੀਆਂ ਕਲਾਉਡ ਤੋਂ ਬਿਨਾਂ ਕੰਮ ਕਰਦੀਆਂ ਹਨ (`clawmetry license`)। ਸਟੀਕ ਮੁਫ਼ਤ/ਭੁਗਤਾਨ ਵੰਡ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਵਿੱਚ ਹੈ।

## ਤੁਹਾਡਾ ਡੇਟਾ ਤੁਹਾਡੀ ਮਸ਼ੀਨ 'ਤੇ ਹੀ ਰਹਿੰਦਾ ਹੈ

ClawMetry ਲੋਕਲ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਅਤੇ ਲਾਗ ਪੜ੍ਹਦਾ ਹੈ। **ਜੇ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ
ਚਲਾਉਂਦੇ ਤਾਂ ਕੋਈ ਵੀ ਸੈਸ਼ਨ ਡੇਟਾ ਤੁਹਾਡੇ ਬਾਕਸ ਤੋਂ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦਾ** — ਕੋਈ ਪ੍ਰੌਮਪਟ,
ਜਵਾਬ, ਟੂਲ ਆਰਗੂਮੈਂਟ, ਫਾਈਲ ਸਮੱਗਰੀ ਜਾਂ ਲਾਗ ਲਾਈਨ ਨਹੀਂ। ਜਦੋਂ ਤੁਸੀਂ ਕਨੈਕਟ ਕਰਦੇ ਹੋ,
ਸਨੈਪਸ਼ਾਟ ਇੱਕ ਕੁੰਜੀ ਨਾਲ ਐਂਡ-ਟੂ-ਐਂਡ ਇਨਕ੍ਰਿਪਟਡ ਹੁੰਦਾ ਹੈ ਜੋ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਕਦੇ ਬਾਹਰ
ਨਹੀਂ ਜਾਂਦੀ, ਅਤੇ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਡੀਕ੍ਰਿਪਟ ਹੁੰਦਾ ਹੈ। ਜੇ ਕਿਸੇ ਨੋਡ ਕੋਲ ਕੋਈ ਕੁੰਜੀ
ਨਹੀਂ ਹੈ, ਤਾਂ ਅੱਪਲੋਡ ਸਾਫ਼ ਟੈਕਸਟ ਵਿੱਚ ਭੇਜਣ ਦੀ ਬਜਾਏ ਛੱਡ ਦਿੱਤਾ ਜਾਂਦਾ ਹੈ, ਅਤੇ ਕੋਈ
ਸਰਵਰ ਜਵਾਬ ਇਸਨੂੰ ਬੰਦ ਨਹੀਂ ਕਰ ਸਕਦਾ।

ਕਨੈਕਟ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਮੂਲ ਰੂਪ ਵਿੱਚ ਦੋ ਚੀਜ਼ਾਂ ਚੱਲਦੀਆਂ ਹਨ, ਦੋਵੇਂ ਆਪਟ-ਆਉਟ ਅਤੇ
ਕੋਈ ਵੀ ਸੈਸ਼ਨ ਡੇਟਾ ਨਹੀਂ ਲੈ ਜਾਂਦੀ: ਇੱਕ ਅਨਾਮਿਕ ਇੰਸਟਾਲ ਪਿੰਗ ਅਤੇ PyPI ਦੇ ਵਿਰੁੱਧ
ਇੱਕ ਵਰਜ਼ਨ ਜਾਂਚ। ਇੱਕ ਮੂਲ ਇੰਸਟਾਲ ਸ਼ੁਰੂਆਤੀ ਬੈਨਰ ਲਾਈਨ ਲਈ ਤੁਹਾਡੇ ਪਬਲਿਕ IP ਨੂੰ ਵੀ
ਇੱਕ ਵਾਰ ਲੁਕ-ਅੱਪ ਕਰਦਾ ਹੈ। ਹਰ ਮੰਜ਼ਿਲ, ਉਹ ਕੀ ਲੈ ਜਾਂਦੀ ਹੈ ਅਤੇ ਉਸਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰਨਾ ਹੈ
[docs/EGRESS.md](docs/EGRESS.md) ਵਿੱਚ ਸੂਚੀਬੱਧ ਹੈ; ਸੈਲਫ-ਹੋਸਟਡ, ਰੀ-ਪੌਇੰਟਡ ਅਤੇ
ਏਅਰ-ਗੈਪਡ ਇੰਸਟਾਲ ਬਿਲਕੁਲ ਕੋਈ ਵੀ ਵਿਵੇਕਸ਼ੀਲ ਬਾਹਰੀ ਕਾਲ ਨਹੀਂ ਕਰਦੇ।

ਡੀਕ੍ਰਿਪਸ਼ਨ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਹੁੰਦੀ ਹੈ, ਉਸ ਕੋਡ ਵਿੱਚ ਜੋ ਅਸੀਂ ਤੁਹਾਨੂੰ ਦਿੰਦੇ ਹਾਂ। ਇਹ
ਪਹਿਲਾਂ ਇੱਕ ਵਾਅਦਾ ਸੀ; ਹੁਣ ਇਹ ਉਹ ਚੀਜ਼ ਹੈ ਜੋ ਤੁਸੀਂ ਜਾਂਚ ਸਕਦੇ ਹੋ। ਹਰ ਲਾਈਨ ਜੋ ਤੁਹਾਡੀ ਕੁੰਜੀ
ਨੂੰ ਛੂਹਦੀ ਹੈ ਇੱਕ ਪੜ੍ਹਣਯੋਗ ਫਾਈਲ ਵਿੱਚ ਰਹਿੰਦੀ ਹੈ, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
ਜੋ wheel ਦੇ ਅੰਦਰ ਭੇਜੀ ਜਾਂਦੀ ਹੈ ਅਤੇ ਉਸੀ ਰੂਪ ਵਿੱਚ ਪ੍ਰਦਾਨ ਕੀਤੀ ਜਾਂਦੀ ਹੈ, ਇੱਕ
Subresource Integrity ਹੈਸ਼ ਨਾਲ ਪਿੰਨਡ। ਇਹ ਪੁਸ਼ਟੀ ਕਰਨ ਲਈ ਕਿ ਬ੍ਰਾਊਜ਼ਰ ਉਹੀ ਚਲਾਉਂਦਾ ਹੈ
ਜੋ ਅਸੀਂ ਪ੍ਰਕਾਸ਼ਿਤ ਕੀਤਾ ਹੈ:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ਇਹ ਕੀ ਸਾਬਤ ਨਹੀਂ ਕਰਦਾ: ਅਸੀਂ ਉਹ ਪੇਜ ਭੇਜਦੇ ਹਾਂ ਜੋ ਫਾਈਲ ਲੋਡ ਕਰਦਾ ਹੈ, ਇਸ ਲਈ ਅਸੀਂ
ਵੱਖਰਾ ਪੇਜ ਭੇਜ ਸਕਦੇ ਸੀ। Integrity ਹੈਸ਼ ਤੁਹਾਨੂੰ ਇੱਕ ਸਮਝੌਤਾ ਕੀਤੇ CDN ਤੋਂ ਸੁਰੱਖਿਅਤ
ਕਰਦੇ ਹਨ, ਨਾ ਕਿ ਵੈਂਡਰ ਤੋਂ। ਤੁਹਾਨੂੰ ਜੋ ਮਿਲਦਾ ਹੈ ਉਹ ਇਹ ਹੈ ਕਿ ਕੋਈ ਵੀ ਬਦਲਵੀਂ ਸਮੱਗਰੀ
ਜਾਣ-ਬੁਝ ਕੇ ਹੋਵੇਗੀ, ਪੇਜ ਸੋਰਸ ਵਿੱਚ ਦਿੱਖਣਯੋਗ ਹੋਵੇਗੀ, ਅਤੇ PyPI 'ਤੇ ਕਿਸੇ ਵੀ ਵੱਲੋਂ
ਲਿਆਂਦੀ ਜਾ ਸਕਣ ਵਾਲੀ ਕਲਾਕ੍ਰਿਤੀ ਤੋਂ ਵੱਖਰੀ ਹੋਵੇਗੀ। ਸੈਲਫ-ਹੋਸਟਿੰਗ ਜਾਂ ਸਿਰਫ਼-ਲੋਕਲ ਰਹਣਾ
ਇਸ ਨਿਰਭਰਤਾ ਨੂੰ ਪੂਰੀ ਤਰ੍ਹਾਂ ਖਤਮ ਕਰ ਦਿੰਦਾ ਹੈ।

## ਇੰਸਟਾਲ

```bash
pip install clawmetry     # ਫਿਰ: clawmetry
```

ਜਾਂ ਇੱਕ-ਲਾਈਨਰ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ਜਾਂ Windows 'ਤੇ Python 3.8+ ਦੀ ਲੋੜ ਹੈ, ਅਤੇ ਉਸੀ ਮਸ਼ੀਨ 'ਤੇ ਘੱਟੋ-ਘੱਟ
ਇੱਕ ਏਜੰਟ ਰਨਟਾਈਮ। Docker ਹਦਾਇਤਾਂ: [docs/DOCKER.md](docs/DOCKER.md)।

ਜਾਂ ਏਜੰਟ ਨੂੰ ਤੁਹਾਡੇ ਲਈ ਇਹ ਸੈਟਅੱਪ ਕਰਨ ਦਿਓ। [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
ਸਕਿੱਲ Claude Code, Codex, Cursor, Gemini CLI, Copilot ਜਾਂ OpenCode ਨੂੰ ClawMetry
ਇੰਸਟਾਲ ਕਰਨਾ, ਮਸ਼ੀਨ 'ਤੇ ਏਜੰਟ ਕੀ ਕਰ ਰਹੇ ਹਨ ਅਤੇ ਕਿੰਨਾ ਖਰਚ ਕਰ ਰਹੇ ਹਨ ਇਹ ਰਿਪੋਰਟ ਕਰਨਾ,
ਬੇਨਤੀ 'ਤੇ ਇੱਕ ਸੈਸ਼ਨ ਰੋਕਣਾ, ਅਤੇ ਜੋਖਮ ਭਰੀਆਂ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਮਨਜ਼ੂਰੀ ਲਈ ਰੋਕ ਕੇ ਰੱਖਣਾ
ਸਿਖਾਉਂਦੀ ਹੈ:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## ਦਸਤਾਵੇਜ਼

| | |
|---|---|
| [ਰਨਟਾਈਮ ਕੰਪੈਟੀਬਿਲਿਟੀ](docs/compatibility.md) | ਹਰ ਅਡੈਪਟਰ ਕੀ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਇੱਕ ਰਨਟਾਈਮ ਕਿਵੇਂ ਜੋੜਨਾ ਹੈ |
| [ਕੰਟੈਕਸਟ ਬਲੋਆਉਟ](docs/CONTEXT_BLOWOUT.md) | ਹਰ-ਪ੍ਰੋਵਾਈਡਰ ਵਿੰਡੋ, ਕੰਪੈਕਸ਼ਨ ਬਨਾਮ ਓਵਰਫਲੋ, ਹਰ-ਰਨਟਾਈਮ ਕਵਰੇਜ |
| [ਓਵਰਹੈੱਡ](docs/OVERHEAD.md) | ਇੰਸਟ੍ਰੂਮੈਂਟੇਸ਼ਨ ਦੀ ਕੀਮਤ ਕੀ ਹੈ, ਮਾਪੀ ਗਈ, ਇਸਨੂੰ ਦੁਬਾਰਾ ਬਣਾਉਣ ਲਈ ਹਾਰਨੈਸ ਨਾਲ |
| [ਐਨਟਾਈਟਲਮੈਂਟ](docs/ENTITLEMENTS.md) | ਮੁਫ਼ਤ ਬਨਾਮ ਭੁਗਤਾਨ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, ਲਾਇਸੈਂਸ CLI |
| [ਅਪਰੂਵਲ ਅਤੇ ਪਾਲਿਸੀਆਂ](docs/APPROVALS.md) | ਪ੍ਰੀ-ਐਗਜ਼ੈਕਿਊਸ਼ਨ ਗੇਟਿੰਗ, ਰਿਸਕ ਸਕੋਰਿੰਗ, ਫੋਨ ਅਪਰੂਵਲ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ਕਿਤੇ ਵੀ ਟਰੇਸ ਐਕਸਪੋਰਟ ਕਰੋ, ਕਿਤੋਂ ਵੀ OTLP ਇੰਜੈਸਟ ਕਰੋ |
| [ਆਪਣਾ ਏਜੰਟ ਲਿਆਓ](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain ਅੰਤ ਤੋਂ ਅੰਤ ਤੱਕ, ਚਲਾਉਣਯੋਗ ਉਦਾਹਰਣਾਂ ਨਾਲ |
| [SDK ਟਰੈਕਿੰਗ](docs/SDK_TRACKING.md) | ਤੁਹਾਡੇ ਆਪਣੇ ਬਣਾਏ ਏਜੰਟਾਂ ਲਈ ਕੀਮਤ ਐਟ੍ਰੀਬਿਊਸ਼ਨ |
| [ਚੈਟ ਚੈਨਲ](docs/CHANNELS.md) | Flow ਵਿੱਚ ਦਿਖਾਏ ਗਏ ਚੈਟ ਅਡੈਪਟਰ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ਸੈਂਡਬਾਕਸਡ NVIDIA NemoClaw ਸੈਟਅੱਪ |
| [Docker](docs/DOCKER.md) | ਇਮੇਜ, ਕੰਪੋਜ਼, ਵੌਲਿਊਮ ਮਾਊਂਟ |
| [ਆਰਕੀਟੈਕਚਰ](ARCHITECTURE.md) · [ਡਿਵੈਲਪਮੈਂਟ](docs/DEVELOPMENT.md) | ਇਹ ਅੰਦਰੋਂ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ; ਸੋਰਸ ਤੋਂ ਚਲਾਉਣਾ |
| [ਟੈਲੀਮੈਟਰੀ](docs/TELEMETRY.md) | ਅਨਾਮਿਕ ਇੰਸਟਾਲ ਅਤੇ ਡੈਸਕਟੌਪ-ਓਪਨ ਪਿੰਗ, ਅਤੇ ਉਨ੍ਹਾਂ ਨੂੰ ਕਿਵੇਂ ਬੰਦ ਕਰਨਾ ਹੈ |

## ਸਕ੍ਰੀਨਸ਼ਾਟ

ਹੇਠਾਂ ਹਰ ਅੰਕ ਇੱਕ ਅਸਲੀ ਮਸ਼ੀਨ ਤੋਂ ਹੈ, ਸਿਰਫ਼-ਪੜ੍ਹਨ ਲਈ, ਕੁਝ ਵੀ ਬੀਜਿਆ ਨਹੀਂ ਗਿਆ।

**ਇਹ ਤੁਹਾਨੂੰ ਦੱਸਦਾ ਹੈ ਜਦੋਂ ਕੁਝ ਗਲਤ ਹੁੰਦਾ ਹੈ, ਨਾ ਸਿਰਫ਼ ਕੀ ਹੋਇਆ।**
ਸਿਖਰ 'ਤੇ ਦੋ ਅਸਾਧਾਰਨਤਾ ਬੈਨਰ: ਖਰਚ ਰੋਜ਼ਾਨਾ ਔਸਤ ਨਾਲੋਂ 7 ਗੁਣਾ ਚੱਲ ਰਿਹਾ ਹੈ, ਅਤੇ
4.2x ਕੀਮਤ ਸਪਾਈਕ। ਉਹਨਾਂ ਦੇ ਹੇਠਾਂ, 667 ਤਾਜ਼ਾ ਸੈਸ਼ਨਾਂ ਵਿੱਚੋਂ 324 ਕਿਸੇ ਬਰਬਾਦੀ ਸਿਗਨਲ
ਨੂੰ ਲੈ ਕੇ, ਕਾਰਨ ਅਨੁਸਾਰ ਵੰਡੇ ਹੋਏ।

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**ਇਹ ਤੁਹਾਨੂੰ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਹਰ ਵਿੰਡੋ ਵਿੱਚ।**
ਅੱਜ $252.47, ਇਸ ਹਫ਼ਤੇ $513.15, ਇਸ ਮਹੀਨੇ $1,312.92, ਹਰ ਇੱਕ ਦੇ ਪਿੱਛੇ ਦੇ ਟੋਕਨਾਂ
ਅਤੇ ਤੁਹਾਡਾ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਇਸ ਵਿੱਚੋਂ ਕਿੰਨਾ ਪਹਿਲਾਂ ਹੀ ਕਵਰ ਕਰਦਾ ਹੈ ਦੇ ਨਾਲ। ਉਸ ਤੋਂ ਹੇਠਾਂ,
ਲਗਭਗ $1,128/ਮਹੀਨਾ ਨੂੰ ਰਿਕਵਰੇਬਲ ਵਜੋਂ ਵੇਰਵੇ ਨਾਲ ਦਿੱਤਾ ਗਿਆ ਹੈ ਅਤੇ ਕੈਸ਼ ਮੁੜ-ਵਰਤੋਂ
ਨਾਲ $17,256/ਮਹੀਨਾ ਪਹਿਲਾਂ ਹੀ ਬਚਾਏ ਜਾ ਚੁੱਕੇ ਹਨ।

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਸੁਨੇਹਾ ਕਿਵੇਂ ਜਵਾਬ ਬਣਦਾ ਹੈ।**
ਲਾਈਵ ਫਲੋ ਡਾਇਆਗ੍ਰਾਮ: ਤੁਸੀਂ, ਉਹ ਚੈਨਲ ਜਿਸ 'ਤੇ ਇਹ ਆਇਆ, ਗੇਟਵੇ, ਜਵਾਬ ਦੇ ਰਿਹਾ ਮਾਡਲ
ਹੁਣੇ, ਅਤੇ ਹਰ ਟੂਲ ਜਿਸਨੂੰ ਇਸਨੇ ਵਰਤਿਆ। ਕੰਮ ਉਹਨਾਂ ਵਿੱਚੋਂ ਲੰਘਣ ਵੇਲੇ ਨੋਡ ਜਗ ਉੱਠਦੇ ਹਨ।

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**ਮਸ਼ੀਨ 'ਤੇ ਹਰ ਏਜੰਟ, ਇੱਕ ਟੇਬਲ ਵਿੱਚ।**
ਇਹ ਕੀ ਚਲਾਉਂਦਾ ਹੈ, ਪਿਛਲੇ 24 ਘੰਟਿਆਂ ਵਿੱਚ ਅਤੇ ਆਪਣੀ ਉਮਰ ਭਰ ਵਿੱਚ ਇਸਦੀ ਕੀ ਕੀਮਤ ਹੈ,
ਆਖਰੀ ਵਾਰ ਕਦੋਂ ਦੇਖਿਆ ਗਿਆ, ਕੌਣ ਇਸਦਾ ਮਾਲਕ ਹੈ, ਅਤੇ ਕੀ ਕੋਈ ਸਬਸਕ੍ਰਿਪਸ਼ਨ ਬਿੱਲ ਕਵਰ
ਕਰ ਰਹੀ ਹੈ। ਇੱਥੇ 14 ਏਜੰਟ, 3 ਸੈਸ਼ਨ ਕੰਮ ਕਰ ਰਹੇ, 13 ਸ਼ਾਂਤ।

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਇੱਕ ਵਾਰੀ ਦਾ ਸਮਾਂ ਅਤੇ ਪੈਸਾ ਕਿੱਥੇ ਗਿਆ, ਟੂਲ-ਦਰ-ਟੂਲ।**
ਇੱਕ ਅਸਲੀ ਸੈਸ਼ਨ ਦੀ ਇੱਕ ਵਾਰੀ: 11.2 ਮਿੰਟਾਂ ਵਿੱਚ 11 ਟੂਲ $1.16 ਵਿੱਚ। ਹਰ Bash
ਕਾਲ ਅਤੇ ਮਾਡਲ ਕਾਲ ਨੂੰ ਟਾਈਮਲਾਈਨ 'ਤੇ ਆਪਣੀ ਖੁਦ ਦੀ ਬਾਰ ਮਿਲਦੀ ਹੈ, ਤਾਂ ਜੋ 4.1 ਮਿੰਟ
ਚੱਲੀ ਕਮਾਂਡ ਅਤੇ 226ms ਚੱਲੀ ਕਮਾਂਡ ਨੂੰ ਇੱਕ ਨਜ਼ਰ ਵਿੱਚ ਵੱਖ ਕੀਤਾ ਜਾ ਸਕੇ।

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**ਇਹ ਕੰਮ ਨੂੰ ਗ੍ਰੇਡ ਦਿੰਦਾ ਹੈ, ਨਾ ਸਿਰਫ਼ ਖਰਚ ਨੂੰ।**
ਇਸ ਹਫ਼ਤੇ A: 54 ਕੰਮ ਸਾਫ਼ ਵਾਪਸ ਆਏ, 2 ਖਰਾਬ ਕੰਮਾਂ ਦੀ ਕੀਮਤ $48.57 ਪਈ, ਅਤੇ ਉਹ
ਰਨ ਜਿਨ੍ਹਾਂ ਵਿੱਚ ਨਿਰਣਾ ਕਰਨ ਲਈ ਬਹੁਤ ਘੱਟ ਸਰਗਰਮੀ ਸੀ ਉਹਨਾਂ ਨੂੰ ਜਿੱਤ ਵਜੋਂ ਗਿਣਣ ਦੀ
ਬਜਾਏ ਗ੍ਰੇਡ ਤੋਂ ਬਾਹਰ ਛੱਡ ਦਿੱਤਾ ਗਿਆ। ਹਰ ਖਰਾਬ ਰਨ ਆਪਣੇ ਟ੍ਰੇਸ ਨਾਲ ਜੁੜਦੀ ਹੈ।

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**ਇਹ ਦਿਖਾਉਂਦਾ ਹੈ ਕਿ ਕੰਟੈਕਸਟ ਵਿੰਡੋ ਕਿਉਂ ਭਰਦੀ ਰਹਿੰਦੀ ਹੈ।**
ਤਾਜ਼ਾ ਵਾਰੀ 'ਤੇ 1M-ਟੋਕਨ ਵਿੰਡੋ ਵਿੱਚੋਂ 715K, 83.3% ਦਾ ਸਿਖਰ, 4 ਕੰਪੈਕਸ਼ਨ
ਜੋ ਸਾਰੇ ਓਵਰਫਲੋ 'ਤੇ ਨਹੀਂ ਸਗੋਂ ਪਹਿਲਾਂ ਹੀ ਚਲਾਏ ਗਏ, ਅਤੇ ਉਸਦੇ ਪਿੱਛੇ ਹਰ ਵਾਰੀ ਦੀ
ਉਪਯੋਗਤਾ।

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**ਡਿਟੈਕਸ਼ਨ ਤੁਹਾਡੇ ਕੁਝ ਵੀ ਕਨਫਿਗਰ ਕੀਤੇ ਬਿਨਾਂ ਚੱਲਦਾ ਹੈ।**
ਬਿਲਟ-ਇਨ ਡਿਟੈਕਟਰ ਇੰਸਟਾਲ ਤੋਂ ਹੀ ਚਾਲੂ ਹਨ: ਏਜੰਟ ਸ਼ਾਂਤ ਹੋ ਗਿਆ, ਟੈਲੀਮੈਟਰੀ ਫੀਡ
ਰੁਕ ਗਈ, ਕੀਮਤ ਸਪਾਈਕ, ਟੋਕਨ ਬਰਸਟ, ਵਧ ਰਹੀਆਂ ਐਰਰਾਂ, ਐਰਰ ਸਪਾਈਕ, ਬਜਟ
ਥ੍ਰੈਸ਼ਹੋਲਡ, ਮੈਚ ਹੋਈ ਥਰੈਟ ਸਿਗਨੇਚਰ, ਸਿਕਿਓਰਿਟੀ ਟੂਲ ਫਾਈਂਡਿੰਗ, ਸਿਕਿਓਰਿਟੀ
ਪੋਸਚਰ ਬਦਲੀ। ਤੁਹਾਡੇ ਆਪਣੇ ਨਿਯਮ ਉੱਪਰ ਆਪਸ਼ਨਲ ਹਨ।

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**ਕਿਸੇ ਜੋਖਮ ਭਰੀ ਕਾਲ ਨੂੰ ਰੋਕਣਾ ਆਪਟ-ਇਨ ਹੈ, ਅਤੇ ਬੰਦ ਭੇਜਿਆ ਜਾਂਦਾ ਹੈ।**
ਰਿਕਰਸਿਵ ਡਿਲੀਟ, ਫੋਰਸ ਪੁਸ਼, sudo, ਸੀਕ੍ਰੇਟ, ਪੈਕੇਜ ਇੰਸਟਾਲ ਅਤੇ ਬਾਹਰੀ
ਕਾਲਾਂ ਨੂੰ ਹਰ ਇੱਕ ਨੂੰ ਇੱਕ ਨਿਯਮ ਮਿਲਦਾ ਹੈ ਜਿਸਨੂੰ ਤੁਸੀਂ ਚਾਲੂ ਕਰ ਸਕਦੇ ਹੋ। ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ
ਨਹੀਂ ਕਰਦੇ, ClawMetry ਦੇਖਦਾ ਹੈ ਅਤੇ ਕੁਝ ਨਹੀਂ ਬਦਲਦਾ। ਇੱਕ ਵਾਰ ਚਾਲੂ ਹੋਣ 'ਤੇ,
ਮੈਚ ਹੋਈਆਂ ਕਾਲਾਂ ਇੱਥੇ (ਜਾਂ ਤੁਹਾਡੇ ਫੋਨ 'ਤੇ) ਮਨਜ਼ੂਰੀ ਜਾਂ ਇਨਕਾਰ ਲਈ ਉਡੀਕਦੀਆਂ ਹਨ।

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

## ਲਾਇਸੈਂਸ

MIT · [@vivekchand](https://github.com/vivekchand) ਵੱਲੋਂ ਬਣਾਇਆ ਗਿਆ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
