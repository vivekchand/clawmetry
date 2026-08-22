<!-- i18n-src:6795052055e2 -->
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

**ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦੇ ਹੋਏ ਦੇਖੋ।** **26 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਲਈ ਰੀਅਲ-ਟਾਈਮ ਆਬਜ਼ਰਵੇਬਿਲਿਟੀ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ਅਤੇ 22 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ।

> 🌐 **ਇਸਨੂੰ ਇਹਨਾਂ ਭਾਸ਼ਾਵਾਂ ਵਿੱਚ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ। ਸਭ ਕੁਝ ਆਪਣੇ-ਆਪ ਖੋਜਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 'ਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ: ਇਹ ਉਹਨਾਂ ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨੂੰ ਲੱਭ ਲੈਂਦਾ ਹੈ ਜੋ ਤੁਹਾਡੇ ਕੋਲ ਪਹਿਲਾਂ ਤੋਂ ਹਨ, ਉਹਨਾਂ ਨੂੰ ਸਿਰਫ਼-ਪੜ੍ਹਨ (read-only) ਲਈ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਉਹਨਾਂ ਦੇ ਚੱਲਣ ਦੇ ਤਰੀਕੇ ਵਿੱਚ ਕੁਝ ਵੀ ਨਹੀਂ ਬਦਲਦਾ।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 26 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

**ਓਪਨ ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ਭੁਗਤਾਨ ਵਾਲੀ ਯੋਜਨਾ 'ਤੇ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

ਹਰ ਰਨਟਾਈਮ ਨੂੰ ਇੱਕੋ ਜਿਹਾ ਡੈਸ਼ਬੋਰਡ ਮਿਲਦਾ ਹੈ। ਕਈਆਂ ਨੂੰ ਇੱਕੋ ਵੇਲੇ ਚਲਾਓ ਅਤੇ ਹੈਡਰ ਸਵਿੱਚਰ ਹਰ ਟੈਬ ਦਾ ਸਕੋਪ ਉਹਨਾਂ ਵਿੱਚੋਂ ਕਿਸੇ ਇੱਕ ਲਈ ਬਦਲ ਦਿੰਦਾ ਹੈ।

ਕੀ ਤੁਸੀਂ ਕਿਸੇ SDK 'ਤੇ ਆਪਣਾ ਖੁਦ ਦਾ ਏਜੰਟ ਬਣਾਇਆ ਹੈ? ਇੰਟਰਸੈਪਟਰ ਉਸਦੇ LLM ਕਾਲਾਂ ਨੂੰ ਵੀ ਟਰੈਕ ਕਰਦਾ ਹੈ। ਦੇਖੋ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **ਸੈਸ਼ਨ ਅਤੇ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ**: ਹਰ ਏਜੰਟ ਨੇ ਕੀ ਕੀਤਾ, ਵਾਰੀ-ਵਾਰੀ, ਰੀਪਲੇਅ ਦੇ ਨਾਲ
- **ਲਾਗਤ ਅਤੇ ਟੋਕਨ**: ਹਰ ਰਨਟਾਈਮ, ਮਾਡਲ, ਸੈਸ਼ਨ ਅਤੇ ਦਿਨ ਮੁਤਾਬਕ, ਅਸਾਧਾਰਨਤਾ ਫਲੈਗਾਂ ਦੇ ਨਾਲ
- **Flow**: ਚੈਨਲਾਂ, ਮਾਡਲਾਂ ਅਤੇ ਟੂਲਾਂ ਵਿੱਚੋਂ ਲੰਘ ਰਹੇ ਸੁਨੇਹਿਆਂ ਦਾ ਲਾਈਵ ਚਿੱਤਰ
- **Brain**: ਤਰਕ ਅਤੇ ਟੂਲ-ਕਾਲ ਈਵੈਂਟ ਸਟ੍ਰੀਮ, ਜਿਵੇਂ ਇਹ ਵਾਪਰ ਰਹੀ ਹੋਵੇ
- **ਮੈਮੋਰੀ ਅਤੇ ਸਕਿੱਲਾਂ**: ਹਰ ਰਨਟਾਈਮ ਨੇ ਅਸਲ ਵਿੱਚ ਕਿਹੜੀਆਂ ਫਾਈਲਾਂ ਅਤੇ ਸਕਿੱਲਾਂ ਲੋਡ ਕੀਤੀਆਂ
- **ਸਿਹਤ ਅਤੇ ਲੌਗ**: ਡਿਸਕ, ਮੈਮੋਰੀ, ਗਲਤੀ ਦਰਾਂ, ਰੇਟ ਲਿਮਿਟਾਂ, ਲਾਈਵ ਲੌਗ ਸਟ੍ਰੀਮ
- **ਅਲਰਟ**: ਬਜਟ ਸੀਮਾਵਾਂ, ਗਲਤੀ ਵਾਧੇ, ਏਜੰਟ-ਆਫਲਾਈਨ, Slack, Discord, PagerDuty, Telegram, Email ਵੱਲ ਭੇਜੇ ਜਾਂਦੇ ਹਨ
- **ਮਨਜ਼ੂਰੀਆਂ**: ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਚੱਲਣ ਤੋਂ *ਪਹਿਲਾਂ* ਰੋਕੋ ਅਤੇ ਆਪਣੇ ਫੋਨ ਤੋਂ ਮਨਜ਼ੂਰ ਕਰੋ ([ਕਿਵੇਂ](docs/APPROVALS.md))

## ਕੀਮਤ

| ਯੋਜਨਾ | ਇਸ ਵਿੱਚ ਕੀ ਸ਼ਾਮਲ ਹੈ | ਕੀਮਤ |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, ਪੂਰਾ ਡੈਸ਼ਬੋਰਡ, ਸਿਰਫ਼ ਲੋਕਲ | $0 |
| **Starter** | ਉੱਪਰ ਦੱਸੇ ਹੋਰ ਸਾਰੇ ਰਨਟਾਈਮ, ਫਲੀਟ ਵਿਊ, ਕਲਾਊਡ ਸਿੰਕ | $9 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |
| **Pro** | Starter + ਗਵਰਨੈਂਸ: ਮਨਜ਼ੂਰੀਆਂ, ਟੂਲ-ਰਿਸਕ ਪਾਲਿਸੀਆਂ, ਮੁਲਾਂਕਣ, ਅਸਾਧਾਰਨਤਾ ਖੋਜ, ਲਾਗਤ ਓਪਟੀਮਾਈਜ਼ਰ, OTel ਐਕਸਪੋਰਟ | $19 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |

ਸਾਲਾਨਾ ਯੋਜਨਾਵਾਂ, Enterprise ਅਤੇ ਮੌਜੂਦਾ ਅੰਕੜੇ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** 'ਤੇ ਮੌਜੂਦ ਹਨ। ਸੈਲਫ-ਹੋਸਟਡ ਲਾਇਸੰਸ
ਕੁੰਜੀਆਂ ਕਲਾਊਡ ਤੋਂ ਬਿਨਾਂ ਵੀ ਕੰਮ ਕਰਦੀਆਂ ਹਨ (`clawmetry license`)। ਮੁਫ਼ਤ/ਭੁਗਤਾਨ ਦੀ ਸਹੀ ਵੰਡ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਵਿੱਚ ਹੈ।

## ਤੁਹਾਡਾ ਡਾਟਾ ਤੁਹਾਡੀ ਮਸ਼ੀਨ 'ਤੇ ਹੀ ਰਹਿੰਦਾ ਹੈ

ClawMetry ਲੋਕਲ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਅਤੇ ਲੌਗ ਪੜ੍ਹਦਾ ਹੈ। ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ ਚਲਾਉਂਦੇ, ਤੁਹਾਡੇ ਬਾਕਸ ਤੋਂ ਕੁਝ ਵੀ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦਾ। ਉਦੋਂ ਵੀ ਸਨੈਪਸ਼ਾਟ ਇੱਕ ਅਜਿਹੀ ਕੁੰਜੀ ਨਾਲ end-to-end ਇਨਕ੍ਰਿਪਟਡ ਹੁੰਦਾ ਹੈ ਜੋ ਕਦੇ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦੀ, ਅਤੇ ਤੁਹਾਡੇ ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਹੀ ਡਿਕ੍ਰਿਪਟ ਹੁੰਦਾ ਹੈ।

## ਸਥਾਪਨਾ (Install)

```bash
pip install clawmetry     # ਫਿਰ: clawmetry
```

ਜਾਂ ਵਨ-ਲਾਈਨਰ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

ਇਸਨੂੰ macOS, Linux ਜਾਂ Windows 'ਤੇ Python 3.8+ ਦੀ ਲੋੜ ਹੈ, ਅਤੇ ਉਸੇ ਮਸ਼ੀਨ 'ਤੇ ਘੱਟੋ-ਘੱਟ
ਇੱਕ ਏਜੰਟ ਰਨਟਾਈਮ ਦੀ। Docker ਹਦਾਇਤਾਂ: [docs/DOCKER.md](docs/DOCKER.md)।

## ਦਸਤਾਵੇਜ਼ (Docs)

| | |
|---|---|
| [ਰਨਟਾਈਮ ਅਨੁਕੂਲਤਾ](docs/compatibility.md) | ਹਰ ਅਡੈਪਟਰ ਕੀ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਨਵਾਂ ਰਨਟਾਈਮ ਕਿਵੇਂ ਜੋੜਨਾ ਹੈ |
| [Entitlements](docs/ENTITLEMENTS.md) | ਮੁਫ਼ਤ ਬਨਾਮ ਭੁਗਤਾਨ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, ਲਾਇਸੰਸ CLI |
| [ਮਨਜ਼ੂਰੀਆਂ ਅਤੇ ਪਾਲਿਸੀਆਂ](docs/APPROVALS.md) | ਚੱਲਣ ਤੋਂ ਪਹਿਲਾਂ ਗੇਟਿੰਗ, ਰਿਸਕ ਸਕੋਰਿੰਗ, ਫੋਨ ਮਨਜ਼ੂਰੀਆਂ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ਟਰੇਸ ਕਿਤੇ ਵੀ ਐਕਸਪੋਰਟ ਕਰੋ, ਕਿਤਿਓਂ ਵੀ OTLP ਇੰਜੈਸਟ ਕਰੋ |
| [SDK ਟ੍ਰੈਕਿੰਗ](docs/SDK_TRACKING.md) | ਤੁਹਾਡੇ ਖੁਦ ਬਣਾਏ ਏਜੰਟਾਂ ਲਈ ਲਾਗਤ ਅਟ੍ਰਿਬਿਊਸ਼ਨ |
| [ਚੈਟ ਚੈਨਲ](docs/CHANNELS.md) | Flow ਵਿੱਚ ਦਿਖਾਏ ਜਾਂਦੇ ਚੈਟ ਅਡੈਪਟਰ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ਸੈਂਡਬਾਕਸਡ NVIDIA NemoClaw ਸੈੱਟਅੱਪ |
| [Docker](docs/DOCKER.md) | ਇਮੇਜ, compose, ਵਾਲੀਊਮ ਮਾਊਂਟ |
| [ਆਰਕੀਟੈਕਚਰ](ARCHITECTURE.md) · [ਵਿਕਾਸ](docs/DEVELOPMENT.md) | ਇਹ ਅੰਦਰੋਂ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ; ਸੋਰਸ ਤੋਂ ਚਲਾਉਣਾ |
| [ਟੈਲੀਮੈਟਰੀ](docs/TELEMETRY.md) | ਅਗਿਆਤ ਸਥਾਪਨਾ ਅਤੇ ਡੈਸਕਟਾਪ-ਓਪਨ ਪਿੰਗ, ਅਤੇ ਇਹਨਾਂ ਨੂੰ ਬੰਦ ਕਿਵੇਂ ਕਰਨਾ ਹੈ |

## ਸਕ੍ਰੀਨਸ਼ਾਟ

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: ਟੋਕਨ, ਸੈਸ਼ਨ, ਸਿਹਤ | **Brain**: ਲਾਈਵ ਏਜੰਟ ਈਵੈਂਟ ਸਟ੍ਰੀਮ |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **ਲਾਗਤ**: ਮਾਡਲ ਅਤੇ ਸੈਸ਼ਨ ਮੁਤਾਬਕ | **ਮਨਜ਼ੂਰੀਆਂ**: ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਰੋਕਣਾ |

ਹੋਰ, ਹਰ ਰਨਟਾਈਮ ਮੁਤਾਬਕ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## ਲਾਇਸੰਸ

MIT · [@vivekchand](https://github.com/vivekchand) ਦੁਆਰਾ ਬਣਾਇਆ ਗਿਆ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
