<!-- i18n-src:48548997be76 -->
> Nederlands translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zie hoe je agent denkt.** Realtime observability voor **12 AI-agent runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex en 8 meer. Één dashboard voor je gehele agentenvloot.

> 🌐 **Lees dit in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [meer →](docs/i18n/)

Één commando. Geen configuratie. Detecteert alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Opent op **http://localhost:8900** en klaar.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Werkt met 12 agent runtimes

ClawMetry begon als observability voor OpenClaw en meet nu je **gehele agentenvloot** in één dashboard, waarbij elke runtime op je machine automatisch wordt gedetecteerd:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw en NemoClaw zijn gratis in de open-source app; de andere runtimes worden actief met ClawMetry Cloud of een zelfgehoste Pro-licentie. Wissel van runtime via de header en elk tabblad past zich aan, inclusief kosten, tokens, tools en traces.

## Wat je krijgt

- **Flow** - Levend geanimeerd diagram dat berichten toont die door kanalen, hersenen, tools en terug stromen
- **Overview** - Gezondheidscontroles, activiteitsheatmap, sessietelling, modelinformatie
- **Usage** - Token- en kostenregistratie met dagelijkse/wekelijkse/maandelijkse uitsplitsingen
- **Sessions** - Actieve agentsessies met model, tokens, laatste activiteit
- **Crons** - Geplande taken met status, volgende uitvoering, duur
- **Logs** - Kleurgecodeerde realtime logstreaming
- **Memory** - Bladeren door SOUL.md, MEMORY.md, AGENTS.md, dagelijkse notities
- **Transcripts** - Chatbelinterface voor het lezen van sessiegeschiedenissen
- **Alerts** - Budgetlimieten, foutfrequentietriggers, detectie van offline agents; stuurt naar Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals** - Gevaarlijke verwijderingen, geforceerde pushes, DB-mutaties, sudo, pakketinstallaties en netwerkaanroepen blokkeren achter eénklikgoedkeuring

## Schermafbeeldingen

### 🧠 Brain - Live agentgebeurtenisstream
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview - Tokengebruik en sessieoverzicht
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow - Realtime toolaanroepfeed
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens - Kostenuitsplitsing per model en sessie
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory - Werkruimtebestandsbrowser
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security - Beveiligingshouding en auditlog
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts - Budgetlimieten, foutfrequentietriggers, webhooks naar Slack / Discord / PagerDuty / e-mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals - Risicovolle toolaanroepen blokkeren achter handmatige goedkeuring; door beleid ondersteunde beveiligingsregels
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Installeren

**Eénregel-installatie (aanbevolen):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Vanuit broncode:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 Frontend-ontwikkeling

De v2 React-app bevindt zich in `frontend/` en wordt geserveerd op `/v2` wanneer de Flask-server wordt gestart met v2 ingeschakeld.

Gebruik twee terminals tijdens het ontwikkelen:

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

Open `http://localhost:5173/v2/`. Vite proxyt `/api`-verzoeken naar `http://localhost:8900`, zodat de React-app met de lokale Flask-server kan communiceren zonder extra CORS-configuratie.

Om de bundel te bouwen die met het Python-pakket wordt meegeleverd:

```bash
cd frontend
npm run build
```

De productiebundel wordt geschreven naar `clawmetry/static/v2/dist/`.

## Runtime- en agentcompatibiliteit

ClawMetry observeert veel AI-agent runtimes, niet alleen OpenClaw. Elke niet-OpenClaw runtime wordt geleverd met een toegewijde lezeradapter die het eigen sessieformaat vertaalt naar de uniforme vormen van ClawMetry; de daemon verwerkt ze in hetzelfde DuckDB-archief en de cloud-snapshot, getagd met de runtime, en het tabblad Sessieherhaling toont een **runtimeschakelaar** wanneer er meer dan één aanwezig is. Zie [`docs/compatibility.md`](docs/compatibility.md) voor de volledige matrix en een handleiding voor het toevoegen van runtimes, en [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) voor de inleiding tot de OpenClaw-familie.

| Runtime / Agent | Status | Notities |
|---|---|---|
| **OpenClaw** | Natief | Referentieruntime, automatisch gedetecteerd |
| **PicoClaw** | Bèta-adapter | Platte `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripties, model, toolaanroepen. |
| **NanoClaw** | Bèta-adapter | Per-sessie SQLite (`data/v2-sessions`). Transcripties en berichtentelling. |
| **Hermes** | Bèta-adapter | SQLite `~/.hermes/state.db`. Transcripties, model, tokens/kosten. |
| **Claude Code** | Bèta-adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripties, model, toolaanroepen en denken, tokengebruik. |
| **Codex** | Bèta-adapter | Rollout JSONL `~/.codex/sessions/...`. Transcripties, model, toolaanroepen, tokengebruik. |
| **Cursor** | Bèta-adapter | SQLite `state.vscdb`. Chat-/componisttranscripties, model. |
| **Aider** | Bèta-adapter | `.aider.chat.history.md` per project. Transcripties, model, tokentelling. |
| **Goose** | Bèta-adapter | SQLite `~/.local/share/goose`. Transcripties, model, toolaanroepen, tokentotalen. |
| **opencode** | Bèta-adapter | SQLite `~/.local/share/opencode`. Transcripties, model, toolaanroepen, tokens en kosten. |
| **Qwen Code** | Bèta-adapter | JSONL `~/.qwen/projects/.../chats`. Transcripties, model, toolaanroepen, tokengebruik. |

"Bèta-adapter" betekent dat ClawMetry een lezer levert voor het echte schijfformaat van die runtime, elk gebouwd en geverifieerd tegen een echte installatie op een echte machine (zie `tests/fixtures/runtimes/<rt>/`). Adapters zijn alleen-lezen; elke adapter is eerlijk over wat zijn runtime daadwerkelijk opslaat (bijv. PicoClaw/NanoClaw/Cursor schrijven geen tokenkosten naar schijf). Wanneer meerdere runtimes op één knooppunt draaien, beperkt de runtimeschakelaar de sessieweergave tot één voor een overzichtelijke verdieping.

## Volg elke SDK-agent - out-loop kostentoewijzing

Alle bovenstaande runtimes schrijven sessies naar schijf. Je eigen **productieagent**, die je hebt gebouwd op de OpenAI Agents SDK, LangChain, de Vercel AI SDK, LlamaIndex, E2B of een eenvoudige `httpx`-lus, doet dat niet. De ClawMetry zero-config interceptor registreert nog steeds zijn LLM-aanroepen (kosten, tokens, latentie, fouten) door `httpx`/`requests` te monkey-patchen:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (of de omgevingsvariabele `CLAWMETRY_SOURCE=support-agent`) voegt aan elke aanroep een **benoemde bron** toe, zodat elk product dat je uitvoert verschijnt als zijn eigen eersteklas, kostentoewijsbare regel in de **🔌 Out-loop sources**-kaart op het Overzicht, met aanroepen, providers, latentie en foutfrequentie per agent. Geen bron ingesteld? De aanroepen worden nog steeds bijgehouden; de kaart blijft gewoon verborgen.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Dit is dezelfde gegevenslaag als die de runtime-adapters voeden (DuckDB → cloud-snapshot), dus out-loop bronnen synchroniseren naar het clouddashboard net als al het andere, E2E-versleuteld.

## OpenTelemetry - leveranciersneutraal, stuur je traces overal naartoe

ClawMetry spreekt **OpenTelemetry** in beide richtingen, met de **GenAI semantische conventies**, zodat je agenttraces nooit gebonden zijn aan één tool.

**Exporteer** elke sessie, inclusief LLM-aanroepen, tools, subagenten, tokens en kosten, als OTLP/HTTP GenAI-spans naar elke collector (Datadog, Grafana, Honeycomb of je eigen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth-headers en pollinginterval zijn optionele omgevingsvariabelen:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ontvangen** - de ingebouwde OTLP-ontvanger accepteert traces en metrische gegevens van alles op `/v1/traces` en `/v1/metrics` (`pip install clawmetry[otel]` voor protobuf-ontvangst).

Je krijgt het zero-config, local-first ClawMetry-dashboard **en** je gegevens in welke backend je team al gebruikt, zonder vendor lock-in en zonder een tweede agent te installeren.

## Configuratie

De meeste mensen hebben geen configuratie nodig. ClawMetry detecteert automatisch je werkruimte, logs, sessies en crons.

Als je toch wilt aanpassen:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Alle opties: `clawmetry --help`

## Ondersteunde kanalen

ClawMetry toont live activiteit voor elk OpenClaw-kanaal dat je hebt geconfigureerd. Alleen kanalen die daadwerkelijk zijn ingesteld in je `openclaw.json` verschijnen in het Flow-diagram; niet-geconfigureerde kanalen worden automatisch verborgen.

Klik op een kanaalknoop in de Flow om een live chatbelweergave te zien met aantallen inkomende en uitgaande berichten.

| Kanaal | Status | Live Popup | Notities |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Volledig | ✅ | Berichten, statistieken, verversing elke 10s |
| 💬 **iMessage** | ✅ Volledig | ✅ | Leest `~/Library/Messages/chat.db` direct |
| 💚 **WhatsApp** | ✅ Volledig | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Volledig | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Volledig | ✅ | Gilde- en kanaaldetectie |
| 🟪 **Slack** | ✅ Volledig | ✅ | Werkruimte- en kanaaldetectie |
| 🌐 **Webchat** | ✅ Volledig | ✅ | Ingebouwde web-UI-sessies |
| 📡 **IRC** | ✅ Volledig | ✅ | Terminalstijl-bubble-UI |
| 🍏 **BlueBubbles** | ✅ Volledig | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Volledig | ✅ | Via Chat API-webhooks |
| 🟣 **MS Teams** | ✅ Volledig | ✅ | Via Teams-bot-plugin |
| 🔷 **Mattermost** | ✅ Volledig | ✅ | Zelfgehoste teamchat |
| 🟩 **Matrix** | ✅ Volledig | ✅ | Gedecentraliseerd, E2EE-ondersteuning |
| 🟢 **LINE** | ✅ Volledig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Volledig | ✅ | Gedecentraliseerde NIP-04 DM's |
| 🟣 **Twitch** | ✅ Volledig | ✅ | Chat via IRC-verbinding |
| 🔷 **Feishu/Lark** | ✅ Volledig | ✅ | WebSocket-gebeurtenisabonnement |
| 🔵 **Zalo** | ✅ Volledig | ✅ | Zalo Bot API |

> **Automatische detectie:** ClawMetry leest je `~/.openclaw/openclaw.json` en toont alleen de kanalen die je daadwerkelijk hebt geconfigureerd. Geen handmatige configuratie vereist.

## Docker-implementatie

Wil je ClawMetry in een container uitvoeren? Geen probleem! 🐳

**Snel starten met Docker:**

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

**Docker Compose voorbeeld:**

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

> **Opmerking:** Wanneer je in Docker uitvoert, koppel dan de data- en logmappen van je agent (bijv. `~/.openclaw`, `~/.claude`, `~/.codex`) zodat ClawMetry je configuratie automatisch kan detecteren.

## Vereisten

- Python 3.8+
- Flask (automatisch geïnstalleerd via pip)
- Een AI-agent runtime op dezelfde machine: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw of PicoClaw (of gekoppelde volumes voor Docker)
- Linux of macOS

## NemoClaw / OpenShell-ondersteuning

ClawMetry detecteert automatisch [NemoClaw](https://github.com/NVIDIA/NemoClaw), NVIDIA's enterprise-beveiligingswrapper voor OpenClaw die agents uitvoert binnen sandboxed OpenShell-containers.

In de meeste gevallen is geen extra configuratie nodig. De syncdaemon ontdekt automatisch sessiebestanden, of ze nu in `~/.openclaw/` op de host staan of in een OpenShell-container.

### Hoe het werkt

ClawMetry detecteert NemoClaw op twee manieren:

1. **Binaire detectie** - controleert op de `nemoclaw` CLI en voert `nemoclaw status` uit om sandboxinformatie te verkrijgen
2. **Containerdetectie** - scant actieve Docker-containers op `openshell`-, `nemoclaw`- of `ghcr.io/nvidia/`-images en leest vervolgens sessies via volume-mounts of `docker cp`

Sessiebestanden die zijn gesynchroniseerd vanuit NemoClaw-containers worden getagd met `runtime=nemoclaw`- en `container_id`-metadata in het clouddashboard, zodat je ze in één oogopslag kunt onderscheiden van standaard OpenClaw-sessies.

### Aanbevolen configuratie: syncdaemon op de HOST

Voor de beste ervaring voer je de syncdaemon van ClawMetry uit op de **hostmachine** (niet binnen de sandbox). Dit vermijdt beperkingen van het NemoClaw-netwerkbeleid.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

De syncdaemon vindt automatisch sessies in alle actieve OpenShell-containers.

### Optioneel: expliciete sandboxnaam

Als automatische detectie niet werkt, wijs ClawMetry naar de juiste sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Uitvoeren binnen de sandbox (gevorderd)

Als je de syncdaemon **binnen** de OpenShell-sandbox moet uitvoeren, voeg dan deze uitgangsregel toe aan je NemoClaw-netwerkbeleid zodat het de ClawMetry ingest-API kan bereiken:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Toepassen met:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Poorten en eindpunten

| Eindpunt | Poort | Protocol | Vereist |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Ja (syncdaemon naar cloud) |
| `localhost:8900` | 8900 | HTTP | Ja (lokale dashboard-UI) |
| Docker-socket (`/var/run/docker.sock`) | — | Unix-socket | Voor containerssessiedetectie |

De syncdaemon maakt alleen uitgaande HTTPS-aanroepen naar `ingest.clawmetry.com`. Er zijn geen inkomende poorten vereist.

---

## Cloud-implementatie

Zie de **[Cloud Test-handleiding](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** voor SSH-tunnels, reverse proxy en Docker.

## Testen

Dit project wordt getest met BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetrie

ClawMetry stuurt een enkele anonieme ping voor de eerste uitvoering naar `https://app.clawmetry.com/api/install` de eerste keer dat je de `clawmetry` CLI op een nieuwe machine uitvoert. We gebruiken dit om installaties te tellen (de enige marketingmaatstaf die we hebben voor een OSS-project) en om te leren welke agentframeworks onze gebruikers hebben geïnstalleerd.

**Precies één POST per installatie**, met:

| Veld | Voorbeeld | Waarom |
|---|---|---|
| `install_id` | willekeurige UUID opgeslagen in `~/.clawmetry/install_id` | deduplicatie; niet gekoppeld aan je e-mail of api_key |
| `version` | `0.12.167` | welke versies er in gebruik zijn |
| `os` / `os_version` | `Darwin` / `25.3.0` | platformondersteuningsprioriteiten |
| `python` | `3.11.15` | Python-versieondersteuningsmatrix |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | welke agents we vervolgens moeten integreren |
| `is_ci` / `ci_provider` | `true` / `github_actions` | menselijke installaties scheiden van CI-ruis |

**Wat we NIET sturen**: IP (de cloud leidt de landcode aan de serverzijde af uit het verzoek en gooit het IP-adres daarna weg), hostnaam, gebruikersnaam, werkruimtepad, bestandsinhoud, je api_key, je e-mailadres of iets wat persoonsgebonden of werkruimtespecifiek is. De netwerklading is controleerbaar in [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Afmelden** (een van deze schakelt het permanent uit):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Een netwerkfout hier blokkeert `clawmetry` nooit om te draaien; de ping is fire-and-forget op een daemonthread met een time-out van 3 seconden.

## Sterrengeschiedenis

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licentie

MIT

---

<p align="center">
  <strong>🦞 Zie hoe je agent denkt</strong><br>
  <sub>Gebouwd door <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Onderdeel van het <a href="https://github.com/openclaw/openclaw">OpenClaw</a>-ecosysteem</sub>
</p>
