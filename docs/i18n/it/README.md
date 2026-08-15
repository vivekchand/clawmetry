<!-- i18n-src:c422fb7dd0da -->
> Italiano translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Guarda il tuo agente pensare.** Osservabilità in tempo reale per **20 runtime di agenti AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e altri 16. Un'unica dashboard per l'intera flotta di agenti.

> 🌐 **Leggi questo in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [altre →](docs/i18n/)

Un comando. Zero configurazione. Rileva tutto automaticamente.

```bash
pip install clawmetry && clawmetry
```

Si apre su **http://localhost:8900** ed è fatta.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funziona con 20 runtime di agenti

ClawMetry è nato come strumento di osservabilità per OpenClaw, e ora misura l'**intera flotta di agenti** in un'unica dashboard, rilevando automaticamente ogni runtime presente sulla tua macchina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw e NemoClaw sono gratuiti nell'app open source; gli altri runtime si attivano con ClawMetry Cloud o con una licenza Pro self-hosted. Cambia runtime dall'intestazione e ogni scheda, costi, token, strumenti, tracce, si riadatta a quel runtime. Consulta **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** per la ripartizione esatta gratuita/a pagamento, la matrice dei livelli, la struttura di `/api/entitlement` e la CLI `clawmetry license`.

## Cosa ottieni

- **Flow** — Diagramma animato dal vivo che mostra i messaggi che scorrono attraverso canali, brain, strumenti e ritorno
- **Overview** — Controlli di stato, mappa di calore dell'attività, conteggio sessioni, informazioni sul modello
- **Usage** — Monitoraggio di token e costi con suddivisioni giornaliere/settimanali/mensili
- **Sessions** — Sessioni agente attive con modello, token, ultima attività
- **Crons** — Job pianificati con stato, prossima esecuzione, durata
- **Logs** — Streaming di log in tempo reale a colori
- **Memory** — Sfoglia SOUL.md, MEMORY.md, AGENTS.md, note giornaliere
- **Transcripts** — Interfaccia a fumetti di chat per leggere lo storico delle sessioni
- **Alerts** — Limiti di budget, trigger su tasso di errore, rilevamento agente offline; instrada verso Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Blocca eliminazioni distruttive, force push, mutazioni di database, sudo, installazioni di pacchetti, chiamate di rete dietro un'approvazione con un solo clic

## Screenshot

### 🧠 Brain — Flusso di eventi dell'agente dal vivo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Utilizzo dei token e riepilogo sessioni
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed delle chiamate agli strumenti in tempo reale
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Ripartizione dei costi per modello e sessione
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Browser dei file dello spazio di lavoro
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura di sicurezza e registro di audit
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limiti di budget, trigger su tasso di errore, webhook verso Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blocca le chiamate agli strumenti rischiose dietro approvazione manuale; regole di protezione basate su policy
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blocco pre-esecuzione per Claude Code** — un comando installa un
hook PreToolUse che mette in pausa le chiamate agli strumenti corrispondenti *prima* che vengano eseguite e attende
la tua decisione (un tocco dal telefono con le
[notifiche push cloud](https://app.clawmetry.com/push) attivate):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Un rifiuto blocca solo quella singola chiamata allo strumento, l'agente mantiene la sua sessione e può
provare un altro approccio. Approvare dal telefono salta il prompt di
autorizzazione nativo di Claude Code (hai già risposto). Gli strumenti non corrispondenti costano circa 40ms e
ricadono nel normale flusso di autorizzazione di Claude Code. Ricevi anche una notifica push sul telefono quando Claude Code stesso è in attesa di una tua decisione (notifiche
`permission_prompt` / `idle_prompt`).

## Installazione

**Comando singolo (consigliato):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Dal sorgente:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Sviluppo del frontend v2

L'app React v2 risiede in `frontend/` ed è servita su `/v2` quando il
server Flask viene avviato con v2 abilitato.

Usa due terminali durante lo sviluppo:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

Apri `http://localhost:5173/v2/`. Vite instrada le richieste `/api` verso
`http://localhost:8900`, così l'app React può comunicare con il server Flask locale
senza bisogno di configurazioni CORS aggiuntive.

Per compilare il bundle distribuito con il pacchetto Python:

```bash
cd frontend
npm run build
```

Il bundle di produzione viene scritto in `clawmetry/static/v2/dist/`.

## Compatibilità di runtime / agenti

ClawMetry osserva molti runtime di agenti AI, non solo OpenClaw. Ogni runtime diverso da OpenClaw dispone di un adattatore di lettura dedicato che traduce il suo formato nativo di sessione nelle forme unificate di ClawMetry; il daemon li ingerisce nello stesso archivio DuckDB + snapshot cloud, taggati con il runtime, e la scheda Session replay mostra un **selettore di runtime** quando ne è presente più di uno. Consulta [`docs/compatibility.md`](docs/compatibility.md) per la matrice completa e una guida per aggiungere runtime, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) per un'introduzione alla famiglia OpenClaw.

Usi lo strumento di sicurezza per agenti [numbat di Perplexity](https://github.com/perplexityai/numbat)? ClawMetry ne ingerisce i risultati e le decisioni di enforcement pronte all'uso, vedi [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agente | Stato | Note |
|---|---|---|
| **OpenClaw** | Nativo | Runtime di riferimento, rilevato automaticamente |
| **PicoClaw** | Adattatore beta | JSONL flat `providers.Message` (`~/.picoclaw/workspace/sessions`). Transcript, modello, chiamate agli strumenti. |
| **NanoClaw** | Adattatore beta | SQLite per sessione (`data/v2-sessions`). Transcript + conteggio messaggi. |
| **Hermes** | Adattatore beta | SQLite `~/.hermes/state.db`. Transcript, modello, token/costo. |
| **Claude Code** | Adattatore beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcript, modello, chiamate agli strumenti + thinking, utilizzo dei token. |
| **Codex** | Adattatore beta | Rollout JSONL `~/.codex/sessions/...`. Transcript, modello, chiamate agli strumenti, utilizzo dei token. |
| **Cursor** | Adattatore beta | SQLite `state.vscdb`. Transcript di chat/composer, modello. |
| **Aider** | Adattatore beta | `.aider.chat.history.md` per progetto. Transcript, modello, conteggi dei token. |
| **Goose** | Adattatore beta | SQLite `~/.local/share/goose`. Transcript, modello, chiamate agli strumenti, totali dei token. |
| **opencode** | Adattatore beta | SQLite `~/.local/share/opencode`. Transcript, modello, chiamate agli strumenti, token + costo. |
| **Qwen Code** | Adattatore beta | JSONL `~/.qwen/projects/.../chats`. Transcript, modello, chiamate agli strumenti, utilizzo dei token. |
| **Pi** | Adattatore beta | JSONL `~/.pi/agent/sessions`. Transcript, modello, chiamate agli strumenti, token + costo. |
| **Deep Agents** | Adattatore beta | SQLite `~/.deepagents/.state/sessions.db`. Transcript, modello, chiamate agli strumenti, token + costo. |
| **n8n** | Adattatore beta | SQLite `~/.n8n/database.sqlite`. Esecuzioni di workflow, esecuzioni dei nodi, prompt AI Agent, modello + token dove n8n li registra. |
| **Antigravity** | Adattatore beta | Brain JSONL sotto `~/.gemini/<flavor>/brain/`. Conversazioni, passaggi degli strumenti, thinking, suddivisione dei token Gemini per generazione + costo, consumo delle generazioni in background. |
| **GitHub Copilot** | Adattatore beta | `events.jsonl` della Copilot CLI sotto `~/.copilot/session-state/` + il registro di utilizzo per chiamata `session-store.db`. Conversazioni, chiamate agli strumenti, instradamento del modello, suddivisione dei token con consapevolezza della cache, costo in crediti AI fatturato dal vendor. |
| **Grok** | Adattatore beta | xAI Grok Build CLI (binario Rust sotto `~/.grok/bin/grok`): log eventi globale `~/.grok/logs/unified.jsonl` + `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}` per sessione. Conversazioni, suddivisione dei token per turno, instradamento del modello, e il payload in uscita del repo inviato dalla CLI e messo in coda sotto `~/.grok/upload_queue/` così puoi vedere cosa è uscito dalla tua macchina. |

"Adattatore beta" significa che ClawMetry distribuisce un lettore per il formato reale su disco di quel runtime, ciascuno costruito e verificato su un'installazione reale su una macchina reale (vedi `tests/fixtures/runtimes/<rt>/`). Gli adattatori sono di sola lettura; ognuno è onesto su cosa il suo runtime effettivamente memorizza (ad es. PicoClaw/NanoClaw/Cursor non scrivono il costo dei token su disco). Quando più runtime girano su un nodo, il selettore di runtime limita la vista delle sessioni a uno solo per un approfondimento pulito.

## Traccia qualsiasi agente SDK — attribuzione dei costi out-loop

I runtime sopra elencati scrivono tutti le sessioni su disco. Il tuo **agente di produzione** personale, quello costruito su OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, o un semplice ciclo `httpx`, non lo fa. L'interceptor a configurazione zero di ClawMetry cattura comunque le sue chiamate LLM (costo, token, latenza, errori) tramite monkey-patching di `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (o la variabile d'ambiente `CLAWMETRY_SOURCE=support-agent`) etichetta ogni chiamata con una **sorgente nominata**, così ogni prodotto che esegui appare come una propria linea di prim'ordine, attribuibile per costo, nella scheda **🔌 Out-loop sources** della dashboard su Overview, chiamate, provider, latenza, tasso di errore per agente. Nessuna sorgente impostata? Le chiamate vengono comunque tracciate, la scheda rimane semplicemente nascosta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Questo è lo stesso livello di dati alimentato dagli adattatori di runtime (DuckDB → snapshot cloud), quindi le sorgenti out-loop si sincronizzano con la dashboard cloud come tutto il resto, con crittografia E2E.

## OpenTelemetry — neutrale rispetto al vendor, invia le tue tracce ovunque

ClawMetry parla **OpenTelemetry** in entrambe le direzioni, usando le **convenzioni semantiche GenAI**, così le tracce del tuo agente non sono mai vincolate a un solo strumento.

**Esporta** ogni sessione, chiamate LLM, strumenti, sub-agenti, token, costo, come span GenAI OTLP/HTTP verso qualsiasi collector (Datadog, Grafana, Honeycomb, o il tuo OTel Collector personale):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Gli header di autenticazione e l'intervallo di polling sono variabili d'ambiente opzionali:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** — il receiver OTLP integrato accetta tracce, log e metriche da qualsiasi altra fonte su `/v1/traces`, `/v1/logs` e `/v1/metrics`. Punta qualsiasi app strumentata con OpenTelemetry verso di esso:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

Le tracce e i log OTLP/JSON funzionano su un semplice `pip install clawmetry`, senza extra. L'ingest Protobuf (e le metriche OTLP/JSON) richiede `pip install clawmetry[otel]`. Un'app che imposta il proprio `service.name` appare come un proprio agente nel selettore di runtime, con il suo costo e i suoi token.

Ottieni la dashboard ClawMetry a configurazione zero e local-first **e** i tuoi dati nel backend che il tuo team già usa, senza vincoli, senza un secondo agente da installare.

## Configurazione

La maggior parte delle persone non ha bisogno di alcuna configurazione. ClawMetry rileva automaticamente il tuo spazio di lavoro, i log, le sessioni e i cron.

Se devi personalizzare:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Tutte le opzioni: `clawmetry --help`

## Canali supportati

ClawMetry mostra l'attività dal vivo per ogni canale OpenClaw che hai configurato. Solo i canali effettivamente configurati nel tuo `openclaw.json` appaiono nel diagramma Flow, quelli non configurati vengono nascosti automaticamente.

Clicca su qualsiasi nodo canale nel Flow per vedere una vista dal vivo a fumetti di chat con conteggi dei messaggi in entrata/uscita.

| Canale | Stato | Popup dal vivo | Note |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Messaggi, statistiche, aggiornamento ogni 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Legge direttamente `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Tramite WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Tramite signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Rilevamento guild + canale |
| 🟪 **Slack** | ✅ Completo | ✅ | Rilevamento workspace + canale |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessioni dell'interfaccia web integrata |
| 📡 **IRC** | ✅ Completo | ✅ | Interfaccia a fumetti in stile terminale |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage tramite BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Tramite webhook Chat API |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Tramite plugin bot Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat di team self-hosted |
| 🟩 **Matrix** | ✅ Completo | ✅ | Decentralizzato, supporto E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Completo | ✅ | DM decentralizzati NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat tramite connessione IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Sottoscrizione eventi WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | Zalo Bot API |

> **Rilevamento automatico:** ClawMetry legge il tuo `~/.openclaw/openclaw.json` e visualizza solo i canali che hai effettivamente configurato. Nessuna configurazione manuale richiesta.

## Distribuzione con Docker

Vuoi eseguire ClawMetry in un container? Nessun problema! 🐳

**Avvio rapido con Docker:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Esempio di Docker Compose:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **Nota:** Quando esegui in Docker, monta le directory di dati + log del tuo agente (ad es. `~/.openclaw`, `~/.claude`, `~/.codex`) così ClawMetry può rilevare automaticamente la tua configurazione.

## Requisiti

- Python 3.8+
- Flask (installato automaticamente tramite pip)
- Un runtime di agente AI sulla stessa macchina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, o QM (oppure volumi montati per Docker)
- Linux o macOS

## Supporto NemoClaw / OpenShell

ClawMetry rileva automaticamente [NemoClaw](https://github.com/NVIDIA/NemoClaw), il wrapper di sicurezza enterprise di NVIDIA per OpenClaw che esegue gli agenti all'interno di container OpenShell sandboxati.

Nella maggior parte dei casi non è necessaria alcuna configurazione aggiuntiva. Il daemon di sincronizzazione scopre automaticamente i file di sessione, sia che si trovino in `~/.openclaw/` sull'host sia all'interno di un container OpenShell.

### Come funziona

ClawMetry rileva NemoClaw in due modi:

1. **Rilevamento del binario** — verifica la presenza della CLI `nemoclaw` ed esegue `nemoclaw status` per ottenere informazioni sulla sandbox
2. **Rilevamento del container** — analizza i container Docker in esecuzione alla ricerca di immagini `openshell`, `nemoclaw`, o `ghcr.io/nvidia/`, poi legge le sessioni tramite volumi montati o `docker cp`

I file di sessione sincronizzati dai container NemoClaw sono taggati con metadati `runtime=nemoclaw` e `container_id` nella dashboard cloud, così puoi distinguerli a colpo d'occhio dalle sessioni OpenClaw standard.

### Configurazione consigliata: daemon di sincronizzazione sull'HOST

Per la migliore esperienza, esegui il daemon di sincronizzazione di ClawMetry sulla **macchina host** (non all'interno della sandbox). Questo evita le restrizioni della policy di rete di NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Il daemon di sincronizzazione troverà automaticamente le sessioni all'interno di qualsiasi container OpenShell in esecuzione.

### Opzionale: nome esplicito della sandbox

Se il rilevamento automatico non funziona, indirizza ClawMetry verso la sandbox corretta:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Esecuzione all'interno della sandbox (avanzato)

Se devi eseguire il daemon di sincronizzazione **all'interno** della sandbox OpenShell, aggiungi questa regola di egress alla tua policy di rete NemoClaw così può raggiungere l'API di ingest di ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Applica con:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Porte ed endpoint

| Endpoint | Porta | Protocollo | Richiesto |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Sì (daemon di sincronizzazione → cloud) |
| `localhost:8900` | 8900 | HTTP | Sì (interfaccia dashboard locale) |
| Socket Docker (`/var/run/docker.sock`) | — | Socket Unix | Per il rilevamento delle sessioni nei container |

Il daemon di sincronizzazione effettua solo chiamate HTTPS in uscita verso `ingest.clawmetry.com`. Nessuna porta in ingresso è richiesta.

---

## Distribuzione Cloud

Consulta la **[Guida ai test Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** per tunnel SSH, reverse proxy e Docker.

## Test

Questo progetto è testato con BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

ClawMetry invia ping anonimi sul ciclo di vita dell'installazione a
`https://app.clawmetry.com/api/install`: un ping `install` la prima
volta che esegui la CLI `clawmetry` su una nuova macchina, un ping `update`
alla prima esecuzione dopo l'aggiornamento a una nuova versione, e un ping `onboarded`
quando completi la scelta di onboarding nella dashboard. Usiamo questo
per contare le installazioni reali (i numeri grezzi di download da PyPI sono per circa il 98% mirror, CI
e ridownload da auto-aggiornamento) e per capire quali framework di agenti e
versioni sono realmente diffusi.

**Al massimo una POST per evento del ciclo di vita per versione**, contenente:

| Campo | Esempio | Perché |
|---|---|---|
| `install_id` | UUID casuale memorizzato in `~/.clawmetry/install_id` | deduplicazione; anonimo finché non colleghi esplicitamente la sincronizzazione Cloud (il battito cardiaco autenticato del daemon porta poi con sé questo dato, collegando questa installazione al tuo account) |
| `event` | `install` / `update` / `onboarded` | installazione nuova rispetto ad aggiornamento di una esistente |
| `version` | `0.12.167` | quali versioni sono in circolazione |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorità di supporto per piattaforma |
| `python` | `3.11.15` | matrice di supporto delle versioni Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | con quali agenti dovremmo integrarci successivamente |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separa le installazioni umane dal rumore del CI |

**Cosa NON inviamo**: IP (il cloud deriva il codice del paese lato server
dalla richiesta, poi scarta l'IP), hostname, nome utente, percorso dello spazio di lavoro, contenuto dei file, la tua api_key, la tua email, nulla di personale o specifico dello spazio di lavoro. Il payload sulla rete è verificabile in
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Disattivazione** (una qualsiasi di queste la disabilita permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Un errore di rete qui non blocca mai l'esecuzione di `clawmetry`: il
ping è "fire-and-forget" su un thread daemon con un timeout di 3s.

## Cronologia delle Star

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licenza

MIT

---

<p align="center">
  <strong>🦞 Guarda il tuo agente pensare</strong><br>
  <sub>Creato da <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Parte dell'ecosistema <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
