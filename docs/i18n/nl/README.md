<!-- i18n-src:8252f6b1d31d -->
> Nederlands translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zie je agent denken.** Realtime observability voor **14 AI-agentruntimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 10 andere. Eén dashboard voor je hele agentvloot.

> 🌐 **Lees dit in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [meer →](docs/i18n/)

Eén commando. Geen configuratie. Detecteert alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Opent op **http://localhost:8900** en je bent klaar.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Werkt met 14 agentruntimes

ClawMetry begon als observability voor OpenClaw en meet nu je **hele agentvloot** in één dashboard, en detecteert automatisch elke runtime op je machine:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw en NemoClaw zijn gratis in de open-source app; de andere runtimes worden geactiveerd met ClawMetry Cloud of een zelf-gehoste Pro-licentie. Wissel van runtime via de header en elk tabblad, kosten, tokens, tools, traces, past zich automatisch aan die runtime aan. Zie **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** voor de exacte gratis/betaald-verdeling, de tiermatrix, de vorm van `/api/entitlement` en de `clawmetry license` CLI.

## Wat je krijgt

- **Flow** — Live geanimeerd diagram dat berichten toont die door kanalen, brein, tools en terug stromen
- **Overview** — Gezondheidschecks, activiteits-heatmap, sessieaantallen, modelinformatie
- **Usage** — Token- en kostentracking met dagelijkse/wekelijkse/maandelijkse uitsplitsingen
- **Sessions** — Actieve agentsessies met model, tokens, laatste activiteit
- **Crons** — Geplande taken met status, volgende run, duur
- **Logs** — Kleurgecodeerde realtime logstreaming
- **Memory** — Blader door SOUL.md, MEMORY.md, AGENTS.md, dagelijkse notities
- **Transcripts** — Chatbubbel-UI voor het lezen van sessiegeschiedenissen
- **Alerts** — Budgetlimieten, foutpercentage-triggers, detectie van offline agents; routeert naar Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals** — Blokkeer destructieve verwijderingen, force pushes, DB-mutaties, sudo, pakketinstallaties, netwerkoproepen achter eenmalige goedkeuring

## Screenshots

### 🧠 Brain — Live agent-eventstream
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Tokengebruik & sessiesamenvatting
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Realtime tool-call feed
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Kostenuitsplitsing per model & sessie
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Werkruimte-bestandsbrowser
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Beveiligingshouding & auditlog
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budgetlimieten, foutpercentage-triggers, webhooks naar Slack / Discord / PagerDuty / E-mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blokkeer risicovolle tool-calls achter handmatige goedkeuring; beleidsgebaseerde beschermingsregels
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blokkering vóór uitvoering voor Claude Code** — één commando installeert een
PreToolUse-hook die overeenkomende tool-calls pauzeert *voordat* ze worden uitgevoerd en wacht
op jouw beslissing (één tik vanaf je telefoon met
[cloud-pushmeldingen](https://app.clawmetry.com/push) ingeschakeld):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Een weigering blokkeert alleen die ene tool-call, de agent behoudt zijn sessie en kan
een andere aanpak proberen. Goedkeuren op je telefoon slaat de eigen
toestemmingsprompt van Claude Code over (je hebt al geantwoord). Niet-overeenkomende tools kosten ~40ms en
vallen terug op de normale toestemmingsflow van Claude Code. Je krijgt ook een pushmelding op je telefoon wanneer Claude Code zelf
op je wacht (`permission_prompt`- / `idle_prompt`-meldingen).

## Installatie

**One-liner (aanbevolen):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Vanaf de broncode:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 Frontend-ontwikkeling

De v2 React-app bevindt zich in `frontend/` en wordt geserveerd op `/v2` wanneer de Flask-
server wordt gestart met v2 ingeschakeld.

Gebruik twee terminals tijdens het ontwikkelen:

```bash
# Terminal 1: Flask API/server op :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server op :5173
cd frontend
nvm use
npm ci
npm run dev
```

Open `http://localhost:5173/v2/`. Vite stuurt `/api`-verzoeken door naar
`http://localhost:8900`, zodat de React-app met de lokale Flask-server kan praten
zonder extra CORS-configuratie.

Om de bundel te bouwen die met het Python-pakket wordt meegeleverd:

```bash
cd frontend
npm run build
```

De productiebundel wordt geschreven naar `clawmetry/static/v2/dist/`.

## Runtime-/agentcompatibiliteit

ClawMetry observeert veel AI-agentruntimes, niet alleen OpenClaw. Elke niet-OpenClaw-runtime levert een eigen reader-adapter die het native sessieformaat vertaalt naar ClawMetry's uniforme vormen; de daemon neemt ze op in dezelfde DuckDB-store + cloud-snapshot, getagd met de runtime, en het tabblad Session replay toont een **runtime-schakelaar** wanneer er meer dan één aanwezig is. Zie [`docs/compatibility.md`](docs/compatibility.md) voor de volledige matrix + een gids voor het toevoegen van runtimes, en [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) voor de OpenClaw-familie-inleiding.

| Runtime / Agent | Status | Notities |
|---|---|---|
| **OpenClaw** | Native | Referentie-runtime, automatisch gedetecteerd |
| **PicoClaw** | Bèta-adapter | Platte `providers.Message`-JSONL (`~/.picoclaw/workspace/sessions`). Transcripten, model, tool-calls. |
| **NanoClaw** | Bèta-adapter | SQLite per sessie (`data/v2-sessions`). Transcripten + berichtaantallen. |
| **Hermes** | Bèta-adapter | SQLite `~/.hermes/state.db`. Transcripten, model, tokens/kosten. |
| **Claude Code** | Bèta-adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripten, model, tool-calls + denkstappen, tokengebruik. |
| **Codex** | Bèta-adapter | Rollout-JSONL `~/.codex/sessions/...`. Transcripten, model, tool-calls, tokengebruik. |
| **Cursor** | Bèta-adapter | SQLite `state.vscdb`. Chat-/composer-transcripten, model. |
| **Aider** | Bèta-adapter | `.aider.chat.history.md` per project. Transcripten, model, tokentellingen. |
| **Goose** | Bèta-adapter | SQLite `~/.local/share/goose`. Transcripten, model, tool-calls, tokentotalen. |
| **opencode** | Bèta-adapter | SQLite `~/.local/share/opencode`. Transcripten, model, tool-calls, tokens + kosten. |
| **Qwen Code** | Bèta-adapter | JSONL `~/.qwen/projects/.../chats`. Transcripten, model, tool-calls, tokengebruik. |
| **Pi** | Bèta-adapter | JSONL `~/.pi/agent/sessions`. Transcripten, model, tool-calls, tokens + kosten. |
| **Deep Agents** | Bèta-adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripten, model, tool-calls, tokens + kosten. |
| **n8n** | Bèta-adapter | SQLite `~/.n8n/database.sqlite`. Workflow-uitvoeringen, node-runs, AI Agent-prompts, model + tokens waar n8n die vastlegt. |

"Bèta-adapter" betekent dat ClawMetry een reader levert voor het echte on-disk-formaat van die runtime, elk gebouwd + geverifieerd tegen een echte installatie op een echte machine (zie `tests/fixtures/runtimes/<rt>/`). Adapters zijn alleen-lezen; elk is eerlijk over wat de runtime daadwerkelijk opslaat (bijv. PicoClaw/NanoClaw/Cursor schrijven geen tokenkosten naar schijf). Wanneer meerdere runtimes op één node draaien, beperkt de runtime-schakelaar de sessieweergave tot één voor een overzichtelijke deep-dive.

## Volg elke SDK-agent — out-loop kostentoewijzing

De bovenstaande runtimes schrijven allemaal sessies naar schijf. Jouw eigen **productieagent**, degene die je hebt gebouwd op de OpenAI Agents SDK, LangChain, de Vercel AI SDK, LlamaIndex, E2B, of een eenvoudige `httpx`-lus, doet dat niet. ClawMetry's zero-config interceptor legt de LLM-calls ervan (kosten, tokens, latentie, fouten) toch vast door `httpx`/`requests` te monkey-patchen:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (of de omgevingsvariabele `CLAWMETRY_SOURCE=support-agent`) tagt elke call met een **benoemde bron**, zodat elk product dat je draait als eigen, kosten-toewijsbare eersteklas regel verschijnt in de kaart **🔌 Out-loop sources** van het dashboard op Overview, calls, providers, latentie, foutpercentage per agent. Geen bron ingesteld? De calls worden nog steeds bijgehouden; de kaart blijft dan gewoon verborgen.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Dit is dezelfde datalaag die de runtime-adapters voeden (DuckDB → cloud-snapshot), dus out-loop sources synchroniseren naar het clouddashboard net als al het andere, E2E-versleuteld.

## OpenTelemetry — leveranciersneutraal, stuur je traces overal naartoe

ClawMetry spreekt **OpenTelemetry** in beide richtingen, met de **GenAI semantic conventions**, zodat je agenttraces nooit vastzitten aan één tool.

**Exporteer** elke sessie, LLM-calls, tools, sub-agents, tokens, kosten, als OTLP/HTTP GenAI-spans naar elke collector (Datadog, Grafana, Honeycomb, of je eigen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth-headers en pollinterval zijn optionele omgevingsvariabelen:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ontvang** — de ingebouwde OTLP-ontvanger accepteert traces en metrics van alles anders op `/v1/traces` en `/v1/metrics` (`pip install clawmetry[otel]` voor protobuf-ingest).

Je krijgt het zero-config, local-first ClawMetry-dashboard **en** je data in welke backend je team ook al gebruikt, geen lock-in, geen tweede agent om te installeren.

## Configuratie

De meeste mensen hebben geen configuratie nodig. ClawMetry detecteert automatisch je werkruimte, logs, sessies en crons.

Als je toch iets wilt aanpassen:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Alle opties: `clawmetry --help`

## Ondersteunde kanalen

ClawMetry toont live activiteit voor elk OpenClaw-kanaal dat je hebt geconfigureerd. Alleen kanalen die daadwerkelijk zijn ingesteld in je `openclaw.json` verschijnen in het Flow-diagram, niet-geconfigureerde kanalen worden automatisch verborgen.

Klik op een kanaalnode in de Flow om een live chatbubbelweergave te zien met tellingen van inkomende/uitgaande berichten.

| Kanaal | Status | Live pop-up | Notities |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Volledig | ✅ | Berichten, statistieken, 10s-verversing |
| 💬 **iMessage** | ✅ Volledig | ✅ | Leest `~/Library/Messages/chat.db` rechtstreeks |
| 💚 **WhatsApp** | ✅ Volledig | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Volledig | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Volledig | ✅ | Guild- + kanaaldetectie |
| 🟪 **Slack** | ✅ Volledig | ✅ | Workspace- + kanaaldetectie |
| 🌐 **Webchat** | ✅ Volledig | ✅ | Ingebouwde web-UI-sessies |
| 📡 **IRC** | ✅ Volledig | ✅ | Terminal-stijl bubbel-UI |
| 🍏 **BlueBubbles** | ✅ Volledig | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Volledig | ✅ | Via Chat API-webhooks |
| 🟣 **MS Teams** | ✅ Volledig | ✅ | Via Teams-botplugin |
| 🔷 **Mattermost** | ✅ Volledig | ✅ | Zelf-gehoste teamchat |
| 🟩 **Matrix** | ✅ Volledig | ✅ | Gedecentraliseerd, E2EE-ondersteuning |
| 🟢 **LINE** | ✅ Volledig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Volledig | ✅ | Gedecentraliseerde NIP-04 DM's |
| 🟣 **Twitch** | ✅ Volledig | ✅ | Chat via IRC-verbinding |
| 🔷 **Feishu/Lark** | ✅ Volledig | ✅ | WebSocket-eventabonnement |
| 🔵 **Zalo** | ✅ Volledig | ✅ | Zalo Bot API |

> **Automatische detectie:** ClawMetry leest je `~/.openclaw/openclaw.json` en rendert alleen de kanalen die je daadwerkelijk hebt geconfigureerd. Geen handmatige instelling vereist.

## Docker-implementatie

Wil je ClawMetry in een container draaien? Geen probleem! 🐳

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

**Docker Compose-voorbeeld:**

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

> **Opmerking:** Wanneer je in Docker draait, koppel dan de data- + logmappen van je agent (bijv. `~/.openclaw`, `~/.claude`, `~/.codex`) zodat ClawMetry je opzet automatisch kan detecteren.

## Vereisten

- Python 3.8+
- Flask (automatisch geïnstalleerd via pip)
- Een AI-agentruntime op dezelfde machine: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, of n8n (of gekoppelde volumes voor Docker)
- Linux of macOS

## NemoClaw-/OpenShell-ondersteuning

ClawMetry detecteert automatisch [NemoClaw](https://github.com/NVIDIA/NemoClaw), NVIDIA's enterprise-beveiligingswrapper voor OpenClaw die agents laat draaien binnen gesandboxte OpenShell-containers.

In de meeste gevallen is er geen extra configuratie nodig. De sync-daemon ontdekt automatisch sessiebestanden, of ze zich nu bevinden in `~/.openclaw/` op de host of binnen een OpenShell-container.

### Hoe het werkt

ClawMetry detecteert NemoClaw op twee manieren:

1. **Binaire detectie** — controleert op de `nemoclaw`-CLI en voert `nemoclaw status` uit om sandbox-informatie op te halen
2. **Containerdetectie** — scant draaiende Docker-containers op `openshell`-, `nemoclaw`- of `ghcr.io/nvidia/`-images, en leest vervolgens sessies via volume-mounts of `docker cp`

Sessiebestanden die vanuit NemoClaw-containers worden gesynchroniseerd, worden getagd met `runtime=nemoclaw` en `container_id`-metadata in het clouddashboard, zodat je ze op het eerste gezicht kunt onderscheiden van standaard OpenClaw-sessies.

### Aanbevolen opzet: sync-daemon op de HOST

Voor de beste ervaring draai je de sync-daemon van ClawMetry op de **hostmachine** (niet binnen de sandbox). Dit voorkomt beperkingen van het NemoClaw-netwerkbeleid.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

De sync-daemon vindt automatisch sessies binnen elke draaiende OpenShell-container.

### Optioneel: expliciete sandboxnaam

Als automatische detectie niet werkt, wijs je ClawMetry naar de juiste sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Draaien binnen de sandbox (geavanceerd)

Als je de sync-daemon **binnen** de OpenShell-sandbox moet draaien, voeg dan deze egress-regel toe aan je NemoClaw-netwerkbeleid zodat deze de ClawMetry-ingest-API kan bereiken:

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

### Poorten en endpoints

| Endpoint | Poort | Protocol | Vereist |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Ja (sync-daemon → cloud) |
| `localhost:8900` | 8900 | HTTP | Ja (lokale dashboard-UI) |
| Docker-socket (`/var/run/docker.sock`) | — | Unix-socket | Voor detectie van containersessies |

De sync-daemon maakt alleen uitgaande HTTPS-oproepen naar `ingest.clawmetry.com`. Er zijn geen inkomende poorten vereist.

---

## Cloud-implementatie

Zie de **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** voor SSH-tunnels, reverse proxy en Docker.

## Testen

Dit project wordt getest met BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetrie

ClawMetry stuurt anonieme install-lifecycle-pings naar
`https://app.clawmetry.com/api/install`: één `install`-ping de eerste
keer dat je de `clawmetry`-CLI op een nieuwe machine draait, één `update`-ping
bij de eerste run na het upgraden naar een nieuwe versie, en één `onboarded`-
ping wanneer je de onboarding-keuze in het dashboard voltooit. We gebruiken dit
om echte installaties te tellen (ruwe PyPI-downloadcijfers zijn ~98% mirrors, CI,
en heruploads door automatische updates) en om te leren welke agentframeworks en
versies daadwerkelijk in gebruik zijn.

**Maximaal één POST per lifecycle-event per versie**, met daarin:

| Veld | Voorbeeld | Waarom |
|---|---|---|
| `install_id` | willekeurige UUID opgeslagen in `~/.clawmetry/install_id` | deduplicatie; anoniem totdat je expliciet Cloud sync verbindt (de geauthenticeerde daemon-heartbeat draagt het dan mee, waardoor deze installatie aan je account wordt gekoppeld) |
| `event` | `install` / `update` / `onboarded` | nieuwe installatie versus upgrade van een bestaande |
| `version` | `0.12.167` | welke versies er in gebruik zijn |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioriteiten voor platformondersteuning |
| `python` | `3.11.15` | ondersteuningsmatrix voor Python-versies |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | met welke agents we vervolgens moeten integreren |
| `is_ci` / `ci_provider` | `true` / `github_actions` | menselijke installaties scheiden van CI-ruis |

**Wat we NIET versturen**: IP (de cloud leidt de landcode serverzijde af
uit het verzoek en verwerpt vervolgens het IP), hostnaam, gebruikersnaam, werkruimtepad, bestandsinhoud, je api_key, je e-mailadres, of iets anders dat PII of
werkruimtespecifiek is. De payload is controleerbaar in
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Afmelden** (elk van deze schakelt het permanent uit):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Een netwerkfout hier blokkeert `clawmetry` nooit om te draaien, de
ping is fire-and-forget op een daemonthread met een timeout van 3 s.

## Star-geschiedenis

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
  <strong>🦞 Zie je agent denken</strong><br>
  <sub>Gebouwd door <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Onderdeel van het <a href="https://github.com/openclaw/openclaw">OpenClaw</a>-ecosysteem</sub>
</p>
