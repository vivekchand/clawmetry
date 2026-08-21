<!-- i18n-src:6795052055e2 -->
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

**Guarda il tuo agente pensare.** Osservabilità in tempo reale per **26 runtime di agenti AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e altri 22. Un'unica dashboard per tutta la tua flotta di agenti.

> 🌐 **Leggi questo in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [altre →](docs/i18n/)

Un solo comando. Nessuna configurazione. Rileva automaticamente tutto.

```bash
pip install clawmetry && clawmetry
```

Si apre su **http://localhost:8900**. Zero configurazione: trova i runtime di agenti
che hai già, li legge in sola lettura e non cambia nulla nel loro funzionamento.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funziona con 26 runtime di agenti

**Gratis nell'app open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Su un piano a pagamento:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

Ogni runtime ottiene la stessa dashboard. Eseguine più di uno contemporaneamente e il
selettore nell'header riporterà ogni scheda su uno di essi.

Hai costruito il tuo agente su un SDK invece? L'interceptor traccia anche le sue
chiamate LLM. Vedi [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Cosa ottieni

- **Sessioni e trascrizioni**: cosa ha fatto ogni agente, turno per turno, con replay
- **Costi e token**: per runtime, modello, sessione e giorno, con segnalazione di anomalie
- **Flow**: diagramma in tempo reale dei messaggi che si muovono tra canali, modelli e strumenti
- **Brain**: il flusso di eventi di ragionamento e chiamate agli strumenti mentre accade
- **Memoria e skill**: i file e le skill che ogni runtime ha effettivamente caricato
- **Salute e log**: disco, memoria, tassi di errore, rate limit, stream dei log in tempo reale
- **Alert**: limiti di budget, picchi di errore, agente offline, instradati verso Slack, Discord, PagerDuty, Telegram, Email
- **Approvazioni**: metti in pausa le chiamate a strumenti rischiose *prima* che vengano eseguite e approvale dal telefono ([come](docs/APPROVALS.md))

## Prezzi

| Piano | Cosa copre | Prezzo |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, dashboard completa, solo locale | $0 |
| **Starter** | Tutti gli altri runtime sopra elencati, vista flotta, sincronizzazione cloud | $9 per nodo / mese |
| **Pro** | Starter + governance: approvazioni, policy sul rischio degli strumenti, valutazioni, rilevamento anomalie, ottimizzatore dei costi, esportazione OTel | $19 per nodo / mese |

I piani annuali, Enterprise e i numeri aggiornati si trovano su
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Le chiavi di licenza
self-hosted funzionano senza il cloud (`clawmetry license`). La suddivisione esatta
tra gratuito e a pagamento è in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## I tuoi dati restano sulla tua macchina

ClawMetry legge i file di sessione locali e i log. Nulla lascia la tua macchina a meno
che tu non esegua `clawmetry connect`. E anche in quel caso, lo snapshot è cifrato
end-to-end con una chiave che non lascia mai la tua macchina, e viene decifrato nel
tuo browser.

## Installazione

```bash
pip install clawmetry     # poi: clawmetry
```

Oppure il comando singolo: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Richiede Python 3.8+ su macOS, Linux o Windows, e almeno un runtime di agente sulla
stessa macchina. Istruzioni Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Documentazione

| | |
|---|---|
| [Compatibilità dei runtime](docs/compatibility.md) | Cosa legge ogni adattatore, e come aggiungere un runtime |
| [Entitlement](docs/ENTITLEMENTS.md) | Gratuito vs a pagamento, matrice dei livelli, CLI delle licenze |
| [Approvazioni e policy](docs/APPROVALS.md) | Blocco pre-esecuzione, valutazione del rischio, approvazioni da telefono |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Esporta tracce ovunque, ingerisci OTLP da qualsiasi cosa |
| [Tracciamento SDK](docs/SDK_TRACKING.md) | Attribuzione dei costi per gli agenti che hai costruito tu stesso |
| [Canali di chat](docs/CHANNELS.md) | Gli adattatori di chat mostrati in Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Configurazioni sandboxed di NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Immagine, compose, mount dei volumi |
| [Architettura](ARCHITECTURE.md) · [Sviluppo](docs/DEVELOPMENT.md) | Come funziona internamente; eseguire dal sorgente |
| [Telemetria](docs/TELEMETRY.md) | I ping anonimi di installazione e apertura desktop, e come disattivarli |

## Screenshot

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: token, sessioni, salute | **Brain**: flusso di eventi dell'agente in tempo reale |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Costo**: per modello e sessione | **Approvazioni**: blocca le chiamate a strumenti rischiose |

Altri, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
