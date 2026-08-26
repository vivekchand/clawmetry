<!-- i18n-src:c111f32e69a5 -->
> Deutsch translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Sieh, wie dein Agent denkt.** Echtzeit-Observability für **26 KI-Agenten-Laufzeiten**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex und 24 weitere. Ein Dashboard für deine gesamte Agentenflotte.

> 🌐 **Lies dies auf:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mehr →](docs/i18n/)

Ein Befehl. Keine Konfiguration. Erkennt alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Öffnet sich unter **http://localhost:8900**. Keine Konfiguration nötig: Es findet die Agenten-Laufzeiten,
die du bereits hast, liest sie nur lesend aus und ändert nichts an ihrer Ausführung.

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## Funktioniert mit 26 Agenten-Laufzeiten

**Kostenlos in der Open-Source-App:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**In einem kostenpflichtigen Plan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Jede Laufzeit erhält dasselbe Dashboard. Führe mehrere gleichzeitig aus, und der Umschalter
in der Kopfzeile richtet jeden Tab neu auf eine davon aus.

Hast du deinen eigenen Agenten mit einem SDK gebaut? Der Interceptor erfasst auch dessen LLM-Aufrufe.
Siehe [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Was du bekommst

- **Sitzungen & Transkripte**: was jeder Agent getan hat, Zug um Zug, mit Wiedergabe
- **Kosten & Tokens**: pro Laufzeit, Modell, Sitzung und Tag, mit Anomalie-Markierungen
- **Flow**: Live-Diagramm der Nachrichten, die durch Kanäle, Modelle und Tools fließen
- **Brain**: der Strom von Reasoning- und Tool-Aufruf-Ereignissen in Echtzeit
- **Memory & Skills**: die Dateien und Skills, die jede Laufzeit tatsächlich geladen hat
- **Health & Logs**: Speicherplatz, Arbeitsspeicher, Fehlerraten, Ratenbegrenzungen, Live-Log-Stream
- **Alerts**: Budgetgrenzen, Fehlerspitzen, Agent-offline, weitergeleitet an Slack, Discord, PagerDuty, Telegram, E-Mail
- **Approvals**: riskante Tool-Aufrufe pausieren, *bevor* sie ausgeführt werden, und von deinem Handy aus genehmigen ([wie](docs/APPROVALS.md))

## Preise

| Plan | Was er abdeckt | Preis |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, vollständiges Dashboard, nur lokal | $0 |
| **Starter** | Alle weiteren oben genannten Laufzeiten, Flottenansicht, Cloud-Sync | 9 $ pro Node / Monat |
| **Pro** | Starter + Governance: Approvals, Tool-Risiko-Richtlinien, Evals, Anomalieerkennung, Kostenoptimierer, OTel-Export | 19 $ pro Node / Monat |

Jahrespläne, Enterprise und die aktuellen Zahlen findest du unter
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Selbst gehostete Lizenzschlüssel
funktionieren ohne Cloud (`clawmetry license`). Die genaue Aufteilung zwischen kostenlos und kostenpflichtig steht
in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Deine Daten bleiben auf deinem Rechner

ClawMetry liest lokale Sitzungsdateien und Logs. Nichts verlässt deinen Rechner, es sei denn,
du führst `clawmetry connect` aus. Selbst dann ist der Snapshot Ende-zu-Ende verschlüsselt
mit einem Schlüssel, der deinen Rechner nie verlässt, und wird in deinem Browser entschlüsselt.

## Installation

```bash
pip install clawmetry     # dann: clawmetry
```

Oder der Einzeiler: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Benötigt Python 3.8+ unter macOS, Linux oder Windows sowie mindestens eine Agenten-Laufzeit auf
demselben Rechner. Docker-Anleitung: [docs/DOCKER.md](docs/DOCKER.md).

## Dokumentation

| | |
|---|---|
| [Laufzeit-Kompatibilität](docs/compatibility.md) | Was jeder Adapter liest und wie man eine Laufzeit hinzufügt |
| [Entitlements](docs/ENTITLEMENTS.md) | Kostenlos vs. kostenpflichtig, Tier-Matrix, Lizenz-CLI |
| [Approvals & Richtlinien](docs/APPROVALS.md) | Gating vor der Ausführung, Risikobewertung, Genehmigungen per Handy |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Traces überallhin exportieren, OTLP von überall einlesen |
| [SDK-Tracking](docs/SDK_TRACKING.md) | Kostenzuordnung für selbst gebaute Agenten |
| [Chat-Kanäle](docs/CHANNELS.md) | Die im Flow angezeigten Chat-Adapter |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw-Setups |
| [Docker](docs/DOCKER.md) | Image, Compose, Volume-Mounts |
| [Architektur](ARCHITECTURE.md) · [Entwicklung](docs/DEVELOPMENT.md) | Wie es intern funktioniert; Ausführung aus dem Quellcode |
| [Telemetrie](docs/TELEMETRY.md) | Die anonymen Install- und Desktop-Öffnungs-Pings und wie man sie abschaltet |

## Screenshots

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: Tokens, Sitzungen, Health | **Agenten** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: nach Modell und Sitzung | **Approvals**: riskante Tool-Aufrufe absichern |

Mehr, pro Laufzeit: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star-Verlauf

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Lizenz

MIT · Erstellt von [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
