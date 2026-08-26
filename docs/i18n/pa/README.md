<!-- i18n-src:c111f32e69a5 -->
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

**ਆਪਣੇ ਏਜੰਟ ਨੂੰ ਸੋਚਦੇ ਵੇਖੋ।** **26 AI ਏਜੰਟ ਰਨਟਾਈਮਾਂ** ਲਈ ਰੀਅਲ-ਟਾਈਮ ਨਿਗਰਾਨੀ: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex ਅਤੇ 22 ਹੋਰ। ਤੁਹਾਡੇ ਪੂਰੇ ਏਜੰਟ ਫਲੀਟ ਲਈ ਇੱਕ ਡੈਸ਼ਬੋਰਡ।

> 🌐 **ਇਸ ਨੂੰ ਇਹਨਾਂ ਭਾਸ਼ਾਵਾਂ ਵਿੱਚ ਪੜ੍ਹੋ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ਹੋਰ →](docs/i18n/)

ਇੱਕ ਕਮਾਂਡ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ। ਸਭ ਕੁਝ ਆਪਣੇ ਆਪ ਲੱਭ ਲੈਂਦਾ ਹੈ।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** 'ਤੇ ਖੁੱਲ੍ਹਦਾ ਹੈ। ਜ਼ੀਰੋ ਕੌਂਫਿਗ: ਇਹ ਤੁਹਾਡੇ ਕੋਲ ਪਹਿਲਾਂ ਤੋਂ ਮੌਜੂਦ
ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨੂੰ ਲੱਭ ਲੈਂਦਾ ਹੈ, ਉਹਨਾਂ ਨੂੰ ਸਿਰਫ਼ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਉਹਨਾਂ ਦੇ ਚੱਲਣ ਦੇ ਤਰੀਕੇ ਵਿੱਚ ਕੁਝ ਨਹੀਂ ਬਦਲਦਾ।

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## 26 ਏਜੰਟ ਰਨਟਾਈਮਾਂ ਨਾਲ ਕੰਮ ਕਰਦਾ ਹੈ

**ਓਪਨ ਸੋਰਸ ਐਪ ਵਿੱਚ ਮੁਫ਼ਤ:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ਭੁਗਤਾਨ ਵਾਲੀ ਯੋਜਨਾ 'ਤੇ:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ਹਰ ਰਨਟਾਈਮ ਨੂੰ ਉਹੀ ਡੈਸ਼ਬੋਰਡ ਮਿਲਦਾ ਹੈ। ਇੱਕੋ ਵੇਲੇ ਕਈ ਚਲਾਓ ਅਤੇ ਹੈਡਰ
ਸਵਿੱਚਰ ਹਰ ਟੈਬ ਨੂੰ ਉਹਨਾਂ ਵਿੱਚੋਂ ਕਿਸੇ ਇੱਕ 'ਤੇ ਮੁੜ-ਸਕੋਪ ਕਰ ਦਿੰਦਾ ਹੈ।

ਕੀ ਤੁਸੀਂ SDK ਵਰਤ ਕੇ ਆਪਣਾ ਖੁਦ ਦਾ ਏਜੰਟ ਬਣਾਇਆ ਹੈ? ਇੰਟਰਸੈਪਟਰ ਇਸ ਦੀਆਂ LLM ਕਾਲਾਂ ਨੂੰ
ਵੀ ਟਰੈਕ ਕਰਦਾ ਹੈ। ਵੇਖੋ [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## ਤੁਹਾਨੂੰ ਕੀ ਮਿਲਦਾ ਹੈ

- **ਸੈਸ਼ਨ ਅਤੇ ਟ੍ਰਾਂਸਕ੍ਰਿਪਟ**: ਹਰੇਕ ਏਜੰਟ ਨੇ ਕੀ ਕੀਤਾ, ਮੋੜ-ਦਰ-ਮੋੜ, ਰੀਪਲੇ ਸਮੇਤ
- **ਲਾਗਤ ਅਤੇ ਟੋਕਨ**: ਰਨਟਾਈਮ, ਮਾਡਲ, ਸੈਸ਼ਨ ਅਤੇ ਦਿਨ ਦੇ ਹਿਸਾਬ ਨਾਲ, ਅਸਧਾਰਨਤਾ ਫਲੈਗਾਂ ਸਮੇਤ
- **ਫਲੋ**: ਚੈਨਲਾਂ, ਮਾਡਲਾਂ ਅਤੇ ਟੂਲਾਂ ਵਿਚਕਾਰ ਲੰਘ ਰਹੇ ਸੁਨੇਹਿਆਂ ਦਾ ਲਾਈਵ ਡਾਇਗ੍ਰਾਮ
- **ਬ੍ਰੇਨ**: ਵਾਪਰਦੇ ਸਮੇਂ ਦਾ ਰੀਜ਼ਨਿੰਗ ਅਤੇ ਟੂਲ-ਕਾਲ ਈਵੈਂਟ ਸਟ੍ਰੀਮ
- **ਮੈਮਰੀ ਅਤੇ ਸਕਿੱਲਾਂ**: ਉਹ ਫਾਈਲਾਂ ਅਤੇ ਸਕਿੱਲਾਂ ਜੋ ਹਰੇਕ ਰਨਟਾਈਮ ਨੇ ਅਸਲ ਵਿੱਚ ਲੋਡ ਕੀਤੀਆਂ
- **ਸਿਹਤ ਅਤੇ ਲਾਗ**: ਡਿਸਕ, ਮੈਮਰੀ, ਗਲਤੀ ਦਰਾਂ, ਰੇਟ ਲਿਮਿਟਾਂ, ਲਾਈਵ ਲਾਗ ਸਟ੍ਰੀਮ
- **ਅਲਰਟ**: ਬਜਟ ਹੱਦਾਂ, ਗਲਤੀ ਵਾਧੇ, ਏਜੰਟ-ਆਫਲਾਈਨ, Slack, Discord, PagerDuty, Telegram, Email ਵੱਲ ਰੂਟ ਕੀਤੇ
- **ਮਨਜ਼ੂਰੀਆਂ**: ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਚੱਲਣ ਤੋਂ *ਪਹਿਲਾਂ* ਰੋਕੋ ਅਤੇ ਆਪਣੇ ਫ਼ੋਨ ਤੋਂ ਮਨਜ਼ੂਰ ਕਰੋ ([ਕਿਵੇਂ](docs/APPROVALS.md))

## ਕੀਮਤ

| ਯੋਜਨਾ | ਇਸ ਵਿੱਚ ਕੀ ਸ਼ਾਮਲ ਹੈ | ਕੀਮਤ |
|---|---|---|
| **ਮੁਫ਼ਤ** | OpenClaw + NVIDIA NemoClaw + Goose, ਪੂਰਾ ਡੈਸ਼ਬੋਰਡ, ਸਿਰਫ਼ ਲੋਕਲ | $0 |
| **ਸਟਾਰਟਰ** | ਉੱਪਰ ਦੱਸਿਆ ਹਰ ਹੋਰ ਰਨਟਾਈਮ, ਫਲੀਟ ਵਿਊ, ਕਲਾਊਡ ਸਿੰਕ | $9 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |
| **Pro** | ਸਟਾਰਟਰ + ਗਵਰਨੈਂਸ: ਮਨਜ਼ੂਰੀਆਂ, ਟੂਲ-ਜੋਖਮ ਨੀਤੀਆਂ, ਮੁਲਾਂਕਣ, ਅਸਧਾਰਨਤਾ ਖੋਜ, ਲਾਗਤ ਅਨੁਕੂਲਕ, OTel ਐਕਸਪੋਰਟ | $19 ਪ੍ਰਤੀ ਨੋਡ / ਮਹੀਨਾ |

ਸਾਲਾਨਾ ਯੋਜਨਾਵਾਂ, Enterprise ਅਤੇ ਮੌਜੂਦਾ ਅੰਕੜੇ
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** 'ਤੇ ਮਿਲਦੇ ਹਨ। ਸੈਲਫ-ਹੋਸਟਡ ਲਾਈਸੈਂਸ
ਕੁੰਜੀਆਂ ਕਲਾਊਡ ਤੋਂ ਬਿਨਾਂ ਵੀ ਕੰਮ ਕਰਦੀਆਂ ਹਨ (`clawmetry license`)। ਮੁਫ਼ਤ/ਭੁਗਤਾਨ ਦੀ ਸਹੀ ਵੰਡ
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) ਵਿੱਚ ਹੈ।

## ਤੁਹਾਡਾ ਡਾਟਾ ਤੁਹਾਡੀ ਮਸ਼ੀਨ 'ਤੇ ਹੀ ਰਹਿੰਦਾ ਹੈ

ClawMetry ਲੋਕਲ ਸੈਸ਼ਨ ਫਾਈਲਾਂ ਅਤੇ ਲਾਗ ਪੜ੍ਹਦਾ ਹੈ। ਜਦੋਂ ਤੱਕ ਤੁਸੀਂ `clawmetry connect` ਨਹੀਂ
ਚਲਾਉਂਦੇ, ਕੁਝ ਵੀ ਤੁਹਾਡੇ ਬਾਕਸ ਤੋਂ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦਾ। ਉਦੋਂ ਵੀ, ਸਨੈਪਸ਼ਾਟ ਇੱਕ ਅਜਿਹੀ ਕੁੰਜੀ ਨਾਲ
ਐਂਡ-ਟੂ-ਐਂਡ ਇਨਕ੍ਰਿਪਟਡ ਹੁੰਦਾ ਹੈ ਜੋ ਕਦੇ ਤੁਹਾਡੀ ਮਸ਼ੀਨ ਤੋਂ ਬਾਹਰ ਨਹੀਂ ਜਾਂਦੀ, ਅਤੇ ਤੁਹਾਡੇ
ਬ੍ਰਾਊਜ਼ਰ ਵਿੱਚ ਡੀਕ੍ਰਿਪਟ ਕੀਤਾ ਜਾਂਦਾ ਹੈ।

## ਇੰਸਟਾਲ ਕਰੋ

```bash
pip install clawmetry     # ਫਿਰ: clawmetry
```

ਜਾਂ ਇੱਕ-ਲਾਈਨਰ: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux ਜਾਂ Windows 'ਤੇ Python 3.8+ ਅਤੇ ਉਸੇ ਮਸ਼ੀਨ 'ਤੇ ਘੱਟੋ-ਘੱਟ ਇੱਕ ਏਜੰਟ ਰਨਟਾਈਮ
ਲੋੜੀਂਦਾ ਹੈ। Docker ਹਦਾਇਤਾਂ: [docs/DOCKER.md](docs/DOCKER.md)।

## ਦਸਤਾਵੇਜ਼

| | |
|---|---|
| [ਰਨਟਾਈਮ ਅਨੁਕੂਲਤਾ](docs/compatibility.md) | ਹਰੇਕ ਅਡੈਪਟਰ ਕੀ ਪੜ੍ਹਦਾ ਹੈ, ਅਤੇ ਇੱਕ ਰਨਟਾਈਮ ਕਿਵੇਂ ਜੋੜਨਾ ਹੈ |
| [Entitlements](docs/ENTITLEMENTS.md) | ਮੁਫ਼ਤ ਬਨਾਮ ਭੁਗਤਾਨ, ਟੀਅਰ ਮੈਟ੍ਰਿਕਸ, ਲਾਈਸੈਂਸ CLI |
| [ਮਨਜ਼ੂਰੀਆਂ ਅਤੇ ਨੀਤੀਆਂ](docs/APPROVALS.md) | ਪ੍ਰੀ-ਐਕਜ਼ੀਕਿਊਸ਼ਨ ਗੇਟਿੰਗ, ਜੋਖਮ ਸਕੋਰਿੰਗ, ਫ਼ੋਨ ਮਨਜ਼ੂਰੀਆਂ |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ਟਰੇਸ ਕਿਤੇ ਵੀ ਐਕਸਪੋਰਟ ਕਰੋ, ਕਿਸੇ ਵੀ ਥਾਂ ਤੋਂ OTLP ਇੰਜੈਸਟ ਕਰੋ |
| [SDK ਟਰੈਕਿੰਗ](docs/SDK_TRACKING.md) | ਤੁਹਾਡੇ ਖੁਦ ਬਣਾਏ ਏਜੰਟਾਂ ਲਈ ਲਾਗਤ ਵੰਡ |
| [ਚੈਟ ਚੈਨਲ](docs/CHANNELS.md) | Flow ਵਿੱਚ ਦਿਖਾਏ ਗਏ ਚੈਟ ਅਡੈਪਟਰ |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | ਸੈਂਡਬੌਕਸਡ NVIDIA NemoClaw ਸੈੱਟਅੱਪ |
| [Docker](docs/DOCKER.md) | ਇਮੇਜ, ਕੰਪੋਜ਼, ਵਾਲਿਊਮ ਮਾਊਂਟ |
| [ਆਰਕੀਟੈਕਚਰ](ARCHITECTURE.md) · [ਵਿਕਾਸ](docs/DEVELOPMENT.md) | ਇਹ ਅੰਦਰੋਂ ਕਿਵੇਂ ਕੰਮ ਕਰਦਾ ਹੈ; ਸੋਰਸ ਤੋਂ ਚਲਾਉਣਾ |
| [ਟੈਲੀਮੈਟਰੀ](docs/TELEMETRY.md) | ਅਗਿਆਤ ਇੰਸਟਾਲ ਅਤੇ ਡੈਸਕਟੌਪ-ਓਪਨ ਪਿੰਗ, ਅਤੇ ਉਹਨਾਂ ਨੂੰ ਬੰਦ ਕਿਵੇਂ ਕਰਨਾ ਹੈ |

## ਸਕ੍ਰੀਨਸ਼ਾਟ

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: ਟੋਕਨ, ਸੈਸ਼ਨ, ਸਿਹਤ | **ਏਜੈਂਟ** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **ਲਾਗਤ**: ਮਾਡਲ ਅਤੇ ਸੈਸ਼ਨ ਅਨੁਸਾਰ | **ਮਨਜ਼ੂਰੀਆਂ**: ਖ਼ਤਰਨਾਕ ਟੂਲ ਕਾਲਾਂ ਨੂੰ ਗੇਟ ਕਰੋ |

ਹੋਰ, ਰਨਟਾਈਮ ਅਨੁਸਾਰ: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

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
