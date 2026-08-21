<!-- i18n-src:6795052055e2 -->
> Svenska translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Se din agent tänka.** Realtidsobservabilitet för **26 AI-agentruntimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex och 22 till. En instrumentpanel för hela din agentflotta.

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Ingen konfiguration. Upptäcker allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900**. Ingen konfiguration: den hittar de agentruntimes
du redan har, läser dem skrivskyddat och ändrar inget i hur de körs.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Fungerar med 26 agentruntimes

**Gratis i open source-appen:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**På en betalplan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

Alla runtimes får samma instrumentpanel. Kör flera samtidigt så
omfångsbestämmer huvudväxlaren om varje flik till en av dem.

Byggde du din egen agent på ett SDK istället? Interceptorn spårar dess LLM-anrop
också. Se [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Vad du får

- **Sessioner och transkript**: vad varje agent gjorde, tur för tur, med repris
- **Kostnad och tokens**: per runtime, modell, session och dag, med avvikelseflaggor
- **Flow**: livediagram över meddelanden som rör sig genom kanaler, modeller och verktyg
- **Brain**: strömmen av resonemang- och verktygsanropshändelser i realtid
- **Minne och skills**: filerna och skills varje runtime faktiskt laddade
- **Hälsa och loggar**: disk, minne, felfrekvenser, hastighetsgränser, livelogg-ström
- **Larm**: budgettak, feltoppar, agent-offline, skickas till Slack, Discord, PagerDuty, Telegram, E-post
- **Godkännanden**: pausa riskfyllda verktygsanrop *innan* de körs och godkänn från din telefon ([hur](docs/APPROVALS.md))

## Prissättning

| Plan | Vad den täcker | Pris |
|---|---|---|
| **Gratis** | OpenClaw + NVIDIA NemoClaw + Goose, full instrumentpanel, endast lokalt | $0 |
| **Starter** | Alla andra runtimes ovan, flottvy, molnsynkronisering | $9 per nod / månad |
| **Pro** | Starter + styrning: godkännanden, verktygsriskpolicyer, utvärderingar, avvikelsedetektering, kostnadsoptimerare, OTel-export | $19 per nod / månad |

Årsplaner, Enterprise och de aktuella priserna finns på
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Egenhostade licensnycklar
fungerar utan molnet (`clawmetry license`). Den exakta gratis/betal-uppdelningen finns
i [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Din data stannar på din maskin

ClawMetry läser lokala sessionsfiler och loggar. Inget lämnar din maskin om du inte
kör `clawmetry connect`. Även då är ögonblicksbilden totalsträckskrypterad
med en nyckel som aldrig lämnar din maskin, och dekrypteras i din webbläsare.

## Installation

```bash
pip install clawmetry     # sedan: clawmetry
```

Eller enradaren: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kräver Python 3.8+ på macOS, Linux eller Windows, och minst en agentruntime på
samma maskin. Docker-instruktioner: [docs/DOCKER.md](docs/DOCKER.md).

## Dokumentation

| | |
|---|---|
| [Runtime-kompatibilitet](docs/compatibility.md) | Vad varje adapter läser, och hur man lägger till en runtime |
| [Rättigheter](docs/ENTITLEMENTS.md) | Gratis vs betalt, nivåmatris, licens-CLI |
| [Godkännanden och policyer](docs/APPROVALS.md) | Förhandsgranskning innan körning, riskbedömning, godkännanden via telefon |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exportera spårningar var som helst, ingest OTLP från vad som helst |
| [SDK-spårning](docs/SDK_TRACKING.md) | Kostnadsattribuering för agenter du byggt själv |
| [Chattkanaler](docs/CHANNELS.md) | Chattadaptrarna som visas i Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandlådade NVIDIA NemoClaw-uppsättningar |
| [Docker](docs/DOCKER.md) | Avbildning, compose, volymmonteringar |
| [Arkitektur](ARCHITECTURE.md) · [Utveckling](docs/DEVELOPMENT.md) | Hur det fungerar inuti; köra från källkod |
| [Telemetri](docs/TELEMETRY.md) | De anonyma installations- och skrivbordsöppningspingarna, och hur man stänger av dem |

## Skärmbilder

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Översikt**: tokens, sessioner, hälsa | **Brain**: liveström av agenthändelser |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Kostnad**: efter modell och session | **Godkännanden**: gate riskfyllda verktygsanrop |

Fler, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Stjärnhistorik

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licens

MIT · Byggd av [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
