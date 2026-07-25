<!-- i18n-src:8f42d460a973 -->
> Italiano translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Guarda il tuo agente pensare.** Osservabilità in tempo reale per **14 runtime di agenti AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex e altri 10. Un'unica dashboard per l'intera flotta di agenti.

> 🌐 **Leggi questo in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [altre lingue →](docs/i18n/)

Un solo comando. Zero configurazione. Rileva tutto automaticamente.

```bash
pip install clawmetry && clawmetry
```

Si apre su **http://localhost:8900** ed è tutto pronto.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funziona con 14 runtime di agenti

ClawMetry è nato come osservabilità per OpenClaw, e ora monitora **l'intera flotta di agenti** in un'unica dashboard, rilevando automaticamente ogni runtime presente sulla tua macchina:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw e NemoClaw sono gratuiti nell'app open-source; gli altri runtime si attivano con ClawMetry Cloud o con una licenza Pro self-hosted. Passa da un runtime all'altro dall'intestazione e ogni scheda, costo, token, strumenti, tracce, si adatta a quel runtime. Consulta **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** per la suddivisione esatta tra funzionalità gratuite e a pagamento, la matrice dei livelli, la struttura di `/api/entitlement` e la CLI `clawmetry license`.

## Cosa ottieni

- **Flow** — Diagramma animato in tempo reale che mostra i messaggi che scorrono attraverso canali, cervello, strumenti e ritorno
- **Overview** — Controlli di salute, heatmap dell'attività, conteggio sessioni, informazioni sul modello
- **Usage** — Monitoraggio di token e costi con ripartizioni giornaliere/settimanali/mensili
- **Sessions** — Sessioni attive dell'agente con modello, token, ultima attività
- **Crons** — Job pianificati con stato, prossima esecuzione, durata
- **Logs** — Streaming di log in tempo reale con codifica a colori
- **Memory** — Sfoglia SOUL.md, MEMORY.md, AGENTS.md, note giornaliere
- **Transcripts** — Interfaccia a fumetti di chat per leggere la cronologia delle sessioni
- **Alerts** — Limiti di budget, trigger sul tasso di errore, rilevamento agente offline; instrada verso Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Blocca eliminazioni distruttive, force push, mutazioni del database, sudo, installazioni di pacchetti, chiamate di rete dietro un'unica approvazione con un clic

## Screenshot

### 🧠 Brain — Flusso di eventi dell'agente in tempo reale
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Utilizzo dei token e riepilogo sessioni
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Feed delle chiamate agli strumenti in tempo reale
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Ripartizione dei costi per modello e sessione
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Browser dei file dello spazio di lavoro
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postura di sicurezza e registro di controllo
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limiti di budget, trigger sul tasso di errore, webhook verso Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blocca le chiamate agli strumenti rischiose dietro un'approvazione manuale; regole di protezione basate su policy
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

**Dal codice sorgente:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Sviluppo del frontend v2

L'app React v2 si trova in `frontend/` e viene servita su `/v2` quando il
server Flask viene avviato con v2 abilitato.

Usa due terminali durante lo sviluppo:

```bash
# Terminale 1: API/server Flask su :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminale 2: server di sviluppo Vite su :5173
cd frontend
nvm use
npm ci
npm run dev
```

Apri `http://localhost:5173/v2/`. Vite inoltra le richieste `/api` a
`http://localhost:8900`, così l'app React può comunicare con il server Flask
locale senza configurazioni CORS aggiuntive.

Per compilare il bundle che viene distribuito con il pacchetto Python:

```bash
cd frontend
npm run build
```

Il bundle di produzione viene scritto in `clawmetry/static/v2/dist/`.

## Compatibilità con runtime / agenti

ClawMetry osserva molti runtime di agenti AI, non solo OpenClaw. Ogni runtime diverso da OpenClaw include un adattatore di lettura dedicato che traduce il proprio formato nativo di sessione nelle strutture unificate di ClawMetry; il daemon li inserisce nello stesso store DuckDB + snapshot cloud, etichettati con il runtime, e la scheda di replay delle sessioni mostra un **selettore di runtime** quando ne è presente più di uno. Consulta [`docs/compatibility.md`](docs/compatibility.md) per la matrice completa + una guida per aggiungere runtime, e [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) per l'introduzione alla famiglia OpenClaw.

| Runtime / Agente | Stato | Note |
|---|---|---|
| **OpenClaw** | Nativo | Runtime di riferimento, rilevato automaticamente |
| **PicoClaw** | Adattatore beta | JSONL piatto `providers.Message` (`~/.picoclaw/workspace/sessions`). Trascrizioni, modello, chiamate agli strumenti. |
| **NanoClaw** | Adattatore beta | SQLite per sessione (`data/v2-sessions`). Trascrizioni + conteggio messaggi. |
| **Hermes** | Adattatore beta | SQLite `~/.hermes/state.db`. Trascrizioni, modello, token/costo. |
| **Claude Code** | Adattatore beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Trascrizioni, modello, chiamate agli strumenti + ragionamento, utilizzo token. |
| **Codex** | Adattatore beta | Rollout JSONL `~/.codex/sessions/...`. Trascrizioni, modello, chiamate agli strumenti, utilizzo token. |
| **Cursor** | Adattatore beta | SQLite `state.vscdb`. Trascrizioni di chat/composer, modello. |
| **Aider** | Adattatore beta | `.aider.chat.history.md` per progetto. Trascrizioni, modello, conteggio token. |
| **Goose** | Adattatore beta | SQLite `~/.local/share/goose`. Trascrizioni, modello, chiamate agli strumenti, totali token. |
| **opencode** | Adattatore beta | SQLite `~/.local/share/opencode`. Trascrizioni, modello, chiamate agli strumenti, token + costo. |
| **Qwen Code** | Adattatore beta | JSONL `~/.qwen/projects/.../chats`. Trascrizioni, modello, chiamate agli strumenti, utilizzo token. |
| **Pi** | Adattatore beta | JSONL `~/.pi/agent/sessions`. Trascrizioni, modello, chiamate agli strumenti, token + costo. |
| **Deep Agents** | Adattatore beta | SQLite `~/.deepagents/.state/sessions.db`. Trascrizioni, modello, chiamate agli strumenti, token + costo. |

"Adattatore beta" significa che ClawMetry fornisce un lettore per il formato reale su disco di quel runtime, ciascuno costruito e verificato su un'installazione reale su una macchina reale (vedi `tests/fixtures/runtimes/<rt>/`). Gli adattatori sono di sola lettura; ciascuno è onesto su ciò che il proprio runtime effettivamente memorizza (ad es. PicoClaw/NanoClaw/Cursor non scrivono il costo dei token su disco). Quando più runtime sono in esecuzione su un nodo, il selettore di runtime limita la vista delle sessioni a uno solo per un'analisi approfondita pulita.

## Traccia qualsiasi agente SDK — attribuzione dei costi out-loop

I runtime sopra elencati scrivono tutti le sessioni su disco. Il tuo **agente di produzione** personale, quello che hai costruito con l'OpenAI Agents SDK, LangChain, il Vercel AI SDK, LlamaIndex, E2B, o un semplice loop `httpx`, non lo fa. L'interceptor a configurazione zero di ClawMetry cattura comunque le sue chiamate LLM (costo, token, latenza, errori) applicando il monkey-patching a `httpx`/`requests`:

```python
import clawmetry.track            # attiva l'interceptor
clawmetry.track.set_source("support-agent")   # nomina questo prodotto

# ...il tuo agente funziona normalmente; ogni chiamata LLM ora viene tracciata + attribuita.
```

`set_source()` (o la variabile d'ambiente `CLAWMETRY_SOURCE=support-agent`) etichetta ogni chiamata con una **sorgente nominata**, così ogni prodotto che esegui appare come una riga di prima classe, attribuibile per costo, nella scheda **🔌 Out-loop sources** della dashboard su Overview, chiamate, provider, latenza, tasso di errore per agente. Nessuna sorgente impostata? Le chiamate vengono comunque tracciate; la scheda resta semplicemente nascosta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Questo è lo stesso livello di dati alimentato dagli adattatori di runtime (DuckDB → snapshot cloud), quindi le sorgenti out-loop si sincronizzano con la dashboard cloud come tutto il resto, con crittografia end-to-end.

## OpenTelemetry — indipendente dal fornitore, invia le tue tracce ovunque

ClawMetry parla **OpenTelemetry** in entrambe le direzioni, usando le **convenzioni semantiche GenAI**, così le tracce del tuo agente non sono mai bloccate su un unico strumento.

**Esporta** ogni sessione, chiamate LLM, strumenti, sotto-agenti, token, costo, come span GenAI OTLP/HTTP verso qualsiasi collector (Datadog, Grafana, Honeycomb, o il tuo OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalentemente:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Gli header di autenticazione e l'intervallo di polling sono variabili d'ambiente opzionali:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # header HTTP aggiuntivi
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # secondi (predefinito 60)
```

**Ingestione** — il receiver OTLP integrato accetta tracce e metriche da qualsiasi altra fonte su `/v1/traces` e `/v1/metrics` (`pip install clawmetry[otel]` per l'ingestione protobuf).

Ottieni la dashboard ClawMetry a configurazione zero e local-first **e** i tuoi dati nel backend che il tuo team già usa, senza lock-in, senza un secondo agente da installare.

## Configurazione

La maggior parte delle persone non ha bisogno di alcuna configurazione. ClawMetry rileva automaticamente il tuo spazio di lavoro, i log, le sessioni e i cron.

Se hai bisogno di personalizzare:

```bash
clawmetry --port 9000              # Porta personalizzata (predefinita: 8900)
clawmetry --host 127.0.0.1         # Vincola solo a localhost
clawmetry --workspace ~/mybot      # Percorso personalizzato dello spazio di lavoro
clawmetry --name "Alice"           # Il tuo nome nella visualizzazione Flow
```

Tutte le opzioni: `clawmetry --help`

## Canali supportati

ClawMetry mostra l'attività in tempo reale per ogni canale OpenClaw che hai configurato. Solo i canali effettivamente configurati nel tuo `openclaw.json` appaiono nel diagramma Flow, quelli non configurati sono nascosti automaticamente.

Fai clic su un nodo canale qualsiasi nel Flow per vedere una vista a fumetti di chat in tempo reale con conteggi dei messaggi in entrata/in uscita.

| Canale | Stato | Popup dal vivo | Note |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Completo | ✅ | Messaggi, statistiche, aggiornamento ogni 10s |
| 💬 **iMessage** | ✅ Completo | ✅ | Legge direttamente `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Completo | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Completo | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Completo | ✅ | Rilevamento gilda + canale |
| 🟪 **Slack** | ✅ Completo | ✅ | Rilevamento workspace + canale |
| 🌐 **Webchat** | ✅ Completo | ✅ | Sessioni dell'interfaccia web integrata |
| 📡 **IRC** | ✅ Completo | ✅ | Interfaccia a fumetti in stile terminale |
| 🍏 **BlueBubbles** | ✅ Completo | ✅ | iMessage tramite API REST BlueBubbles |
| 🔵 **Google Chat** | ✅ Completo | ✅ | Via webhook API Chat |
| 🟣 **MS Teams** | ✅ Completo | ✅ | Via plugin bot Teams |
| 🔷 **Mattermost** | ✅ Completo | ✅ | Chat di team self-hosted |
| 🟩 **Matrix** | ✅ Completo | ✅ | Decentralizzato, supporto E2EE |
| 🟢 **LINE** | ✅ Completo | ✅ | API di messaggistica LINE |
| ⚡ **Nostr** | ✅ Completo | ✅ | DM decentralizzati NIP-04 |
| 🟣 **Twitch** | ✅ Completo | ✅ | Chat tramite connessione IRC |
| 🔷 **Feishu/Lark** | ✅ Completo | ✅ | Sottoscrizione eventi WebSocket |
| 🔵 **Zalo** | ✅ Completo | ✅ | API Bot Zalo |

> **Rilevamento automatico:** ClawMetry legge il tuo `~/.openclaw/openclaw.json` e visualizza solo i canali che hai effettivamente configurato. Non è richiesta alcuna configurazione manuale.

## Distribuzione con Docker

Vuoi eseguire ClawMetry in un container? Nessun problema! 🐳

**Avvio rapido con Docker:**

```bash
# Compila l'immagine
docker build -t clawmetry .

# Esegui con le impostazioni predefinite
docker run -p 8900:8900 clawmetry

# Oppure monta la directory dati del tuo agente (mostrato: ~/.openclaw di OpenClaw)
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

> **Nota:** Quando esegui in Docker, monta le directory dati + log del tuo agente (ad es. `~/.openclaw`, `~/.claude`, `~/.codex`) così ClawMetry può rilevare automaticamente la tua configurazione.

## Requisiti

- Python 3.8+
- Flask (installato automaticamente via pip)
- Un runtime di agente AI sulla stessa macchina: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, o Deep Agents (o volumi montati per Docker)
- Linux o macOS

## Supporto NemoClaw / OpenShell

ClawMetry rileva automaticamente [NemoClaw](https://github.com/NVIDIA/NemoClaw), il wrapper di sicurezza enterprise di NVIDIA per OpenClaw che esegue gli agenti all'interno di container OpenShell sandboxati.

Nella maggior parte dei casi non è necessaria alcuna configurazione aggiuntiva. Il daemon di sincronizzazione individua automaticamente i file di sessione, sia che risiedano in `~/.openclaw/` sull'host, sia all'interno di un container OpenShell.

### Come funziona

ClawMetry rileva NemoClaw in due modi:

1. **Rilevamento binario** — verifica la presenza della CLI `nemoclaw` ed esegue `nemoclaw status` per ottenere informazioni sulla sandbox
2. **Rilevamento container** — analizza i container Docker in esecuzione alla ricerca di immagini `openshell`, `nemoclaw`, o `ghcr.io/nvidia/`, quindi legge le sessioni tramite mount di volumi o `docker cp`

I file di sessione sincronizzati dai container NemoClaw sono etichettati con `runtime=nemoclaw` e metadati `container_id` nella dashboard cloud, così puoi distinguerli a colpo d'occhio dalle sessioni OpenClaw standard.

### Configurazione consigliata: daemon di sincronizzazione sull'HOST

Per la migliore esperienza, esegui il daemon di sincronizzazione di ClawMetry sulla **macchina host** (non all'interno della sandbox). Questo evita le restrizioni delle policy di rete di NemoClaw.

```bash
# Sull'host (fuori dalla sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Il daemon di sincronizzazione troverà automaticamente le sessioni all'interno di qualsiasi container OpenShell in esecuzione.

### Opzionale: nome esplicito della sandbox

Se il rilevamento automatico non funziona, indica a ClawMetry la sandbox corretta:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Esecuzione all'interno della sandbox (avanzato)

Se devi eseguire il daemon di sincronizzazione **all'interno** della sandbox OpenShell, aggiungi questa regola di egress alla tua policy di rete NemoClaw in modo che possa raggiungere l'API di ingestione di ClawMetry:

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

Il daemon di sincronizzazione effettua solo chiamate HTTPS in uscita verso `ingest.clawmetry.com`. Non è richiesta alcuna porta in entrata.

---

## Distribuzione Cloud

Consulta la **[Guida al Testing Cloud](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** per tunnel SSH, reverse proxy e Docker.

## Testing

Questo progetto è testato con BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

ClawMetry invia un singolo ping anonimo di "primo avvio" a
`https://app.clawmetry.com/api/install` la prima volta che esegui la CLI
`clawmetry` su una nuova macchina. Usiamo questo dato per contare le
installazioni (l'unica metrica di marketing che abbiamo per un progetto OSS)
e per capire quali framework di agenti i nostri utenti hanno installato.

**Esattamente un POST per installazione**, contenente:

| Campo | Esempio | Perché |
|---|---|---|
| `install_id` | UUID casuale memorizzato in `~/.clawmetry/install_id` | deduplicazione; non collegato alla tua email o api_key |
| `version` | `0.12.167` | quali versioni sono in circolazione |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorità di supporto delle piattaforme |
| `python` | `3.11.15` | matrice di supporto delle versioni Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | con quali agenti dovremmo integrarci in futuro |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separare le installazioni umane dal rumore CI |

**Cosa NON inviamo**: IP (il cloud deriva il codice paese lato server
dalla richiesta, poi scarta l'IP), hostname, nome utente, percorso dello
spazio di lavoro, contenuto dei file, la tua api_key, la tua email, nulla
di PII o specifico dello spazio di lavoro. Il payload trasmesso è
verificabile in [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Disattivazione** (una qualsiasi di queste la disabilita permanentemente):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per singola shell
export DO_NOT_TRACK=1                          # standard cross-tool W3C
touch ~/.clawmetry/notelemetry                 # marcatore di file persistente
```

Un errore di rete qui non blocca mai l'esecuzione di `clawmetry`, il ping è
fire-and-forget su un thread daemon con un timeout di 3 s.

## Cronologia stelle

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
  <sub>Realizzato da <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Parte dell'ecosistema <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
