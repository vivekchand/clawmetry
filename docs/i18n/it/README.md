<!-- i18n-src:48548997be76 -->
> Italiano translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Guarda il tuo agente pensare.** Osservabilità in tempo reale per **12 runtime di agenti AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e altri 8. Un'unica dashboard per l'intera flotta di agenti.

> 🌐 **Leggilo in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [altro →](docs/i18n/)

Un solo comando. Zero configurazione. Rileva tutto automaticamente.

```bash
pip install clawmetry && clawmetry
```

Si apre su **http://localhost:8900** e il gioco è fatto.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Compatibile con 12 runtime di agenti

ClawMetry è nato come strumento di osservabilità per OpenClaw e ora monitora l'**intera flotta di agenti** in un'unica dashboard, rilevando automaticamente ogni runtime sulla tua macchina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw e NemoClaw sono gratuiti nell'app open-source; gli altri runtime si attivano con ClawMetry Cloud o una licenza Pro self-hosted. Cambia runtime dall'intestazione e ogni scheda, costi, token, strumenti, tracce, si reimposta su quel runtime.

## Cosa ottieni

- **Flow** — Diagramma animato in tempo reale che mostra i messaggi che scorrono attraverso canali, cervello, strumenti e ritorno
- **Overview** — Controlli di integrità, mappa di calore dell'attività, conteggio sessioni, informazioni sul modello
- **Usage** — Monitoraggio di token e costi con riepiloghi giornalieri, settimanali e mensili
- **Sessions** — Sessioni agente attive con modello, token e ultima attività
- **Crons** — Lavori pianificati con stato, prossima esecuzione e durata
- **Logs** — Streaming di log in tempo reale con codifica a colori
- **Memory** — Sfoglia SOUL.md, MEMORY.md, AGENTS.md e note giornaliere
- **Transcripts** — Interfaccia a fumetti per leggere lo storico delle sessioni
- **Alerts** — Limiti di budget, trigger per tasso di errore, rilevamento agente offline; instrada verso Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Blocca eliminazioni distruttive, push forzati, mutazioni DB, sudo, installazioni di pacchetti e chiamate di rete con approvazione in un clic

## Screenshot

### 🧠 Brain — Stream di eventi agente in tempo reale
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Utilizzo token e riepilogo sessioni
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed chiamate strumenti in tempo reale
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Ripartizione costi per modello e sessione
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Browser dei file del workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura di sicurezza e log di audit
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limiti di budget, trigger per tasso di errore, webhook verso Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blocca le chiamate a strumenti rischiose con approvazione manuale; regole di protezione basate su policy
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Installazione

**One-liner (consigliato):**
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

## Sviluppo frontend v2

L'app React v2 si trova in `frontend/` ed è servita su `/v2` quando il server Flask viene avviato con v2 abilitato.

Usa due terminali durante lo sviluppo:

```bash
# Terminale 1: API/server Flask su :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminale 2: server dev Vite su :5173
cd frontend
nvm use
npm ci
npm run dev
```

Apri `http://localhost:5173/v2/`. Vite fa il proxy delle richieste `/api` verso `http://localhost:8900`, così l'app React può comunicare con il server Flask locale senza ulteriore configurazione CORS.

Per compilare il bundle che viene distribuito con il pacchetto Python:

```bash
cd frontend
npm run build
```

Il bundle di produzione viene scritto in `clawmetry/static/v2/dist/`.

## Compatibilità runtime / agente

ClawMetry osserva molti runtime di agenti AI, non solo OpenClaw. Ogni runtime non-OpenClaw include un adattatore di lettura dedicato che traduce il suo formato di sessione nativo nelle forme unificate di ClawMetry; il daemon le inserisce nello stesso store DuckDB e nello snapshot cloud, etichettate con il runtime, e la scheda di replay delle sessioni mostra un **selettore di runtime** quando ne è presente più di uno. Consulta [`docs/compatibility.md`](docs/compatibility.md) per la matrice completa e una guida all'aggiunta di runtime, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) per l'introduzione alla famiglia OpenClaw.

| Runtime / Agente | Stato | Note |
|---|---|---|
| **OpenClaw** | Nativo | Runtime di riferimento, rilevato automaticamente |
| **PicoClaw** | Adattatore beta | JSONL `providers.Message` flat (`~/.picoclaw/workspace/sessions`). Trascrizioni, modello, chiamate strumenti. |
| **NanoClaw** | Adattatore beta | SQLite per sessione (`data/v2-sessions`). Trascrizioni e conteggi messaggi. |
| **Hermes** | Adattatore beta | SQLite `~/.hermes/state.db`. Trascrizioni, modello, token/costo. |
| **Claude Code** | Adattatore beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Trascrizioni, modello, chiamate strumenti e ragionamento, utilizzo token. |
| **Codex** | Adattatore beta | JSONL rollout `~/.codex/sessions/...`. Trascrizioni, modello, chiamate strumenti, utilizzo token. |
| **Cursor** | Adattatore beta | SQLite `state.vscdb`. Trascrizioni chat/composer, modello. |
| **Aider** | Adattatore beta | `.aider.chat.history.md` per progetto. Trascrizioni, modello, conteggi token. |
| **Goose** | Adattatore beta | SQLite `~/.local/share/goose`. Trascrizioni, modello, chiamate strumenti, totali token. |
| **opencode** | Adattatore beta | SQLite `~/.local/share/opencode`. Trascrizioni, modello, chiamate strumenti, token e costo. |
| **Qwen Code** | Adattatore beta | JSONL `~/.qwen/projects/.../chats`. Trascrizioni, modello, chiamate strumenti, utilizzo token. |

"Adattatore beta" significa che ClawMetry include un lettore per il formato su disco di quel runtime, ognuno costruito e verificato su un'installazione reale su una macchina reale (vedi `tests/fixtures/runtimes/<rt>/`). Gli adattatori sono di sola lettura; ognuno è onesto riguardo a ciò che il suo runtime effettivamente memorizza su disco (ad esempio PicoClaw/NanoClaw/Cursor non scrivono il costo dei token sul disco). Quando più runtime girano su un nodo, il selettore di runtime circoscrive la vista delle sessioni a uno solo per un'analisi approfondita e ordinata.

## Traccia qualsiasi agente SDK, attribuzione dei costi out-loop

I runtime elencati sopra scrivono tutti le sessioni su disco. Il tuo **agente di produzione**, quello che hai costruito con OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B o un semplice ciclo `httpx`, non lo fa. L'interceptor zero-config di ClawMetry cattura comunque le sue chiamate LLM (costo, token, latenza, errori) applicando monkey-patching a `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (o la variabile d'ambiente `CLAWMETRY_SOURCE=support-agent`) etichetta ogni chiamata con una **sorgente nominata**, così ogni prodotto che esegui appare come la propria riga di prima classe con attribuzione dei costi nella scheda **🔌 Out-loop sources** dell'Overview, con chiamate, provider, latenza e tasso di errore per agente. Nessuna sorgente impostata? Le chiamate vengono comunque tracciate; la scheda rimane semplicemente nascosta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Questo è lo stesso livello di dati che alimentano gli adattatori runtime (DuckDB → snapshot cloud), quindi le sorgenti out-loop si sincronizzano con la dashboard cloud esattamente come tutto il resto, con cifratura end-to-end.

## OpenTelemetry — vendor-neutral, invia le tue tracce ovunque

ClawMetry parla **OpenTelemetry** in entrambe le direzioni, usando le **convenzioni semantiche GenAI**, così le tue tracce degli agenti non sono mai vincolate a un unico strumento.

**Esporta** ogni sessione, chiamate LLM, strumenti, sotto-agenti, token, costo, come span OTLP/HTTP GenAI verso qualsiasi collector (Datadog, Grafana, Honeycomb o il tuo OTel Collector):

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

**Ingest** — il ricevitore OTLP integrato accetta tracce e metriche da qualsiasi altra sorgente su `/v1/traces` e `/v1/metrics` (`pip install clawmetry[otel]` per l'ingest protobuf).

Ottieni la dashboard ClawMetry zero-config e locale **e** i tuoi dati nel backend che il tuo team già utilizza, senza lock-in e senza un secondo agente da installare.

## Configurazione

La maggior parte delle persone non ha bisogno di alcuna configurazione. ClawMetry rileva automaticamente il tuo workspace, i log, le sessioni e i cron.

Se hai bisogno di personalizzare:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Tutte le opzioni: `clawmetry --help`

## Canali supportati

ClawMetry mostra l'attività in tempo reale per ogni canale OpenClaw che hai configurato. Solo i canali effettivamente impostati nel tuo `openclaw.json` appaiono nel diagramma Flow; quelli non configurati vengono nascosti automaticamente.

Clicca su qualsiasi nodo canale nel Flow per vedere una vista a fumetti in tempo reale con i conteggi dei messaggi in entrata e in uscita.

| Canale | Stato | Popup live | Note |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Messaggi, statistiche, aggiornamento ogni 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Legge `~/Library/Messages/chat.db` direttamente |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Rilevamento guild e canale |
| 🟪 **Slack** | ✅ Completo | ✅ | Rilevamento workspace e canale |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessioni UI web integrate |
| 📡 **IRC** | ✅ Completo | ✅ | Interfaccia a fumetti in stile terminale |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage via API REST BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Via webhook API Chat |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Via plugin bot Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat di team self-hosted |
| 🟩 **Matrix** | ✅ Completo | ✅ | Decentralizzato, supporto E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | API Messaggistica LINE |
| ⚡ **Nostr** | ✅ Completo | ✅ | DM NIP-04 decentralizzati |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat via connessione IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Sottoscrizione eventi WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | API Bot Zalo |

> **Rilevamento automatico:** ClawMetry legge il tuo `~/.openclaw/openclaw.json` e mostra solo i canali che hai effettivamente configurato. Non è richiesta alcuna configurazione manuale.

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

**Esempio Docker Compose:**

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

> **Nota:** Quando si esegue in Docker, monta le directory dei dati e dei log del tuo agente (ad es. `~/.openclaw`, `~/.claude`, `~/.codex`) in modo che ClawMetry possa rilevare automaticamente la tua configurazione.

## Requisiti

- Python 3.8+
- Flask (installato automaticamente via pip)
- Un runtime di agente AI sulla stessa macchina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw o PicoClaw (o volumi montati per Docker)
- Linux o macOS

## Supporto NemoClaw / OpenShell

ClawMetry rileva automaticamente [NemoClaw](https://github.com/NVIDIA/NemoClaw), il wrapper di sicurezza enterprise di NVIDIA per OpenClaw che esegue gli agenti all'interno di container OpenShell in sandbox.

Nella maggior parte dei casi non è necessaria alcuna configurazione aggiuntiva. Il daemon di sincronizzazione individua automaticamente i file di sessione sia che si trovino in `~/.openclaw/` sull'host sia all'interno di un container OpenShell.

### Come funziona

ClawMetry rileva NemoClaw in due modi:

1. **Rilevamento del binario** — verifica la presenza della CLI `nemoclaw` ed esegue `nemoclaw status` per ottenere informazioni sulla sandbox
2. **Rilevamento del container** — scansiona i container Docker in esecuzione alla ricerca di immagini `openshell`, `nemoclaw` o `ghcr.io/nvidia/`, poi legge le sessioni tramite mount di volumi o `docker cp`

I file di sessione sincronizzati dai container NemoClaw sono etichettati con i metadati `runtime=nemoclaw` e `container_id` nella dashboard cloud, così puoi distinguerli dalle sessioni OpenClaw standard a colpo d'occhio.

### Configurazione consigliata: daemon di sincronizzazione sull'HOST

Per la migliore esperienza, esegui il daemon di sincronizzazione di ClawMetry sulla **macchina host** (non all'interno della sandbox). Questo evita le restrizioni delle policy di rete di NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Il daemon di sincronizzazione troverà automaticamente le sessioni all'interno di qualsiasi container OpenShell in esecuzione.

### Opzionale: nome sandbox esplicito

Se il rilevamento automatico non funziona, indica a ClawMetry la sandbox corretta:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Esecuzione all'interno della sandbox (avanzato)

Se devi eseguire il daemon di sincronizzazione **all'interno** della sandbox OpenShell, aggiungi questa regola di egress alla tua policy di rete NemoClaw in modo che possa raggiungere l'API di ingest di ClawMetry:

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

| Endpoint | Porta | Protocollo | Necessario |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Sì (daemon sync → cloud) |
| `localhost:8900` | 8900 | HTTP | Sì (UI dashboard locale) |
| Socket Docker (`/var/run/docker.sock`) | — | Socket Unix | Per il rilevamento sessioni dei container |

Il daemon di sincronizzazione effettua solo chiamate HTTPS in uscita verso `ingest.clawmetry.com`. Non sono richieste porte in entrata.

---

## Distribuzione cloud

Consulta la **[Guida al test cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** per tunnel SSH, reverse proxy e Docker.

## Test

Questo progetto viene testato con BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

ClawMetry invia un singolo ping anonimo di "primo avvio" a `https://app.clawmetry.com/api/install` la prima volta che esegui la CLI `clawmetry` su una nuova macchina. Lo usiamo per contare le installazioni (l'unica metrica di marketing che abbiamo per un progetto OSS) e per capire quali framework di agenti hanno installato i nostri utenti.

**Esattamente un POST per installazione**, contenente:

| Campo | Esempio | Perché |
|---|---|---|
| `install_id` | UUID casuale memorizzato in `~/.clawmetry/install_id` | dedup; non collegato alla tua email o api_key |
| `version` | `0.12.167` | quali versioni sono in uso |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorità nel supporto delle piattaforme |
| `python` | `3.11.15` | matrice di supporto versioni Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | con quali agenti dovremmo integrarci prossimamente |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separare le installazioni umane dal rumore CI |

**Cosa NON inviamo**: IP (il cloud deriva il codice paese lato server dalla richiesta, poi scarta l'IP), nome host, nome utente, percorso del workspace, contenuto dei file, la tua api_key, la tua email, qualsiasi dato PII o specifico del workspace. Il payload sulla rete è verificabile in [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Disattiva** (uno qualsiasi di questi la disabilita in modo permanente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Un errore di rete qui non blocca mai l'esecuzione di `clawmetry`; il ping è fire-and-forget su un thread daemon con un timeout di 3 secondi.

## Cronologia delle stelle

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
