<!-- i18n-src:c111f32e69a5 -->
> Italiano translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Guarda il tuo agente pensare.** Osservabilità in tempo reale per **26 runtime di agenti AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e altri 22. Un'unica dashboard per l'intera flotta di agenti.

> 🌐 **Leggi questo in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [altro →](docs/i18n/)

Un comando. Zero configurazione. Rileva tutto automaticamente.

```bash
pip install clawmetry && clawmetry
```

Si apre su **http://localhost:8900**. Zero configurazione: trova i runtime di agenti
che hai già, li legge in sola lettura e non cambia nulla nel loro funzionamento.

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## Funziona con 26 runtime di agenti

**Gratis nell'app open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Su un piano a pagamento:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Ogni runtime ha la stessa dashboard. Esegui più runtime contemporaneamente e il
selettore nell'intestazione riporta ogni scheda al contesto di uno di essi.

Hai costruito il tuo agente su un SDK invece? L'interceptor traccia anche le sue
chiamate LLM. Vedi [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Cosa ottieni

- **Sessioni e trascrizioni**: cosa ha fatto ogni agente, turno per turno, con replay
- **Costi e token**: per runtime, modello, sessione e giorno, con segnalazioni di anomalie
- **Flow**: diagramma live dei messaggi che passano tra canali, modelli e strumenti
- **Brain**: il flusso di eventi di ragionamento e chiamate agli strumenti in tempo reale
- **Memoria e skill**: i file e le skill effettivamente caricati da ogni runtime
- **Salute e log**: disco, memoria, tassi di errore, rate limit, stream di log in diretta
- **Alert**: limiti di budget, picchi di errore, agente offline, instradati a Slack, Discord, PagerDuty, Telegram, Email
- **Approvazioni**: metti in pausa le chiamate a strumenti rischiose *prima* che vengano eseguite e approvale dal tuo telefono ([come](docs/APPROVALS.md))

## Prezzi

| Piano | Cosa copre | Prezzo |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, dashboard completa, solo locale | $0 |
| **Starter** | Tutti gli altri runtime sopra elencati, vista flotta, sincronizzazione cloud | $9 per nodo / mese |
| **Pro** | Starter + governance: approvazioni, policy di rischio degli strumenti, valutazioni, rilevamento anomalie, ottimizzatore dei costi, esportazione OTel | $19 per nodo / mese |

I piani annuali, Enterprise e le cifre attuali sono disponibili su
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Le chiavi di licenza
self-hosted funzionano senza il cloud (`clawmetry license`). La suddivisione
esatta tra gratuito e a pagamento è in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## I tuoi dati restano sulla tua macchina

ClawMetry legge file di sessione e log locali. Niente lascia il tuo computer a
meno che tu non esegua `clawmetry connect`. Anche in quel caso, lo snapshot è
crittografato end-to-end con una chiave che non lascia mai la tua macchina, e
viene decrittografato nel tuo browser.

## Installazione

```bash
pip install clawmetry     # poi: clawmetry
```

Oppure il one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Richiede Python 3.8+ su macOS, Linux o Windows, e almeno un runtime di agente
sulla stessa macchina. Istruzioni Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Documentazione

| | |
|---|---|
| [Compatibilità dei runtime](docs/compatibility.md) | Cosa legge ogni adattatore, e come aggiungere un runtime |
| [Entitlement](docs/ENTITLEMENTS.md) | Gratuito vs a pagamento, matrice dei livelli, CLI delle licenze |
| [Approvazioni e policy](docs/APPROVALS.md) | Controllo pre-esecuzione, valutazione del rischio, approvazioni da telefono |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Esporta trace ovunque, ingerisci OTLP da qualsiasi fonte |
| [Tracciamento SDK](docs/SDK_TRACKING.md) | Attribuzione dei costi per gli agenti che hai costruito tu stesso |
| [Canali chat](docs/CHANNELS.md) | Gli adattatori chat mostrati in Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurazioni sandbox di NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Immagine, compose, mount dei volumi |
| [Architettura](ARCHITECTURE.md) · [Sviluppo](docs/DEVELOPMENT.md) | Come funziona internamente; esecuzione dal codice sorgente |
| [Telemetria](docs/TELEMETRY.md) | I ping anonimi di installazione e apertura desktop, e come disattivarli |

## Screenshot

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: token, sessioni, salute | **Agenti** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Costi**: per modello e sessione | **Approvazioni**: blocca le chiamate a strumenti rischiose |

Altri screenshot, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Cronologia delle stelle

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licenza

MIT · Creato da [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
