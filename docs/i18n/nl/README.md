<!-- i18n-src:c111f32e69a5 -->
> Nederlands translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zie je agent denken.** Realtime observability voor **26 AI-agentruntimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 22 andere. Eén dashboard voor je hele agentvloot.

> 🌐 **Lees dit in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [meer →](docs/i18n/)

Eén commando. Zonder configuratie. Detecteert alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Opent op **http://localhost:8900**. Zonder configuratie: het vindt de agentruntimes
die je al hebt, leest ze alleen-lezen uit en verandert niets aan hoe ze draaien.

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## Werkt met 26 agentruntimes

**Gratis in de open source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Bij een betaald abonnement:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Elke runtime krijgt hetzelfde dashboard. Draai er meerdere tegelijk en de
schakelaar in de header herschaalt elk tabblad naar een van hen.

Heb je je eigen agent gebouwd met een SDK? De interceptor volgt ook diens
LLM-aanroepen. Zie [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Wat je krijgt

- **Sessies & transcripten**: wat elke agent deed, beurt voor beurt, met replay
- **Kosten & tokens**: per runtime, model, sessie en dag, met afwijkingsmeldingen
- **Flow**: live diagram van berichten die door kanalen, modellen en tools bewegen
- **Brain**: de stream van redeneer- en tool-aanroepgebeurtenissen, live
- **Memory & skills**: de bestanden en skills die elke runtime daadwerkelijk laadde
- **Health & logs**: schijf, geheugen, foutpercentages, rate limits, live logstream
- **Alerts**: budgetgrenzen, foutpieken, agent-offline, doorgestuurd naar Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals**: pauzeer risicovolle tool-aanroepen *voordat* ze uitgevoerd worden en keur ze goed vanaf je telefoon ([hoe](docs/APPROVALS.md))

## Prijzen

| Abonnement | Wat het omvat | Prijs |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, volledig dashboard, alleen lokaal | $0 |
| **Starter** | Elke andere runtime hierboven, vlootweergave, cloudsynchronisatie | $9 per node / maand |
| **Pro** | Starter + governance: approvals, tool-risicobeleid, evaluaties, afwijkingsdetectie, kostenoptimalisatie, OTel-export | $19 per node / maand |

Jaarabonnementen, Enterprise en de actuele bedragen staan op
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Self-hosted licentiesleutels
werken zonder de cloud (`clawmetry license`). De exacte gratis/betaald-verdeling staat
in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Je data blijft op je eigen machine

ClawMetry leest lokale sessiebestanden en logs. Er verlaat niets je machine tenzij
je `clawmetry connect` uitvoert. Zelfs dan is de snapshot end-to-end versleuteld
met een sleutel die je machine nooit verlaat, en wordt deze in je browser ontsleuteld.

## Installeren

```bash
pip install clawmetry     # daarna: clawmetry
```

Of de one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Vereist Python 3.8+ op macOS, Linux of Windows, en ten minste één agentruntime op
dezelfde machine. Docker-instructies: [docs/DOCKER.md](docs/DOCKER.md).

## Documentatie

| | |
|---|---|
| [Runtime-compatibiliteit](docs/compatibility.md) | Wat elke adapter uitleest, en hoe je een runtime toevoegt |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis versus betaald, tiermatrix, licentie-CLI |
| [Approvals & beleid](docs/APPROVALS.md) | Voorafgaande controle, risicoscoring, goedkeuring vanaf je telefoon |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporteer traces overal naartoe, importeer OTLP van overal |
| [SDK-tracking](docs/SDK_TRACKING.md) | Kostentoewijzing voor agents die je zelf hebt gebouwd |
| [Chatkanalen](docs/CHANNELS.md) | De chatadapters die in Flow worden getoond |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Gesandboxte NVIDIA NemoClaw-opstellingen |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architectuur](ARCHITECTURE.md) · [Ontwikkeling](docs/DEVELOPMENT.md) | Hoe het intern werkt; draaien vanuit de broncode |
| [Telemetrie](docs/TELEMETRY.md) | De anonieme installatie- en desktop-open-pings, en hoe je ze uitschakelt |

## Schermafbeeldingen

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: tokens, sessies, health | **Agents** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: per model en sessie | **Approvals**: risicovolle tool-aanroepen afschermen |

Meer, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licentie

MIT · Gebouwd door [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
