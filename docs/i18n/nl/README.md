<!-- i18n-src:9a05336fbdc1 -->
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

Opent op **http://localhost:8900** en klaar is Kees.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Werkt met 14 agentruntimes

ClawMetry begon als observability voor OpenClaw en meet nu je **hele agentvloot** in één dashboard, met automatische detectie van elke runtime op je machine:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw en NemoClaw zijn gratis in de open-source app; de overige runtimes worden geactiveerd met ClawMetry Cloud of een self-hosted Pro-licentie. Wissel van runtime via de header en elk tabblad, kosten, tokens, tools, traces, past zich aan die runtime aan. Zie **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** voor de exacte gratis/betaald-verdeling, de tiermatrix, de vorm van `/api/entitlement` en de `clawmetry license` CLI.

## Wat je krijgt

- **Flow** — Live geanimeerd diagram dat toont hoe berichten door kanalen, brein, tools en terug stromen
- **Overview** — Health checks, activiteitsheatmap, sessietellingen, modelinformatie
- **Usage** — Token- en kostentracking met dag-/week-/maandopsplitsingen
- **Sessions** — Actieve agentsessies met model, tokens, laatste activiteit
- **Crons** — Geplande taken met status, volgende run, duur
- **Logs** — Kleurgecodeerde realtime logstreaming
- **Memory** — Blader door SOUL.md, MEMORY.md, AGENTS.md, dagelijkse notities
- **Transcripts** — Chatbubbel-UI voor het lezen van sessiegeschiedenissen
- **Alerts** — Budgetplafonds, foutpercentagetriggers, agent-offline-detectie; routeert naar Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals** — Blokkeer destructieve verwijderingen, force pushes, DB-mutaties, sudo, pakketinstallaties, netwerkoproepen achter een sign-off met één klik

## Screenshots

### 🧠 Brain — Live agent-eventstream
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Tokengebruik & sessiesamenvatting
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Realtime feed van tool-calls
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Kostenopsplitsing per model & sessie
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Bestandsbrowser voor de workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postuur & auditlog
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budgetplafonds, foutpercentagetriggers, webhooks naar Slack / Discord / PagerDuty / e-mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blokkeer risicovolle tool-calls achter handmatige goedkeuring; beleidsgestuurde beschermingsregels
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blokkering vóór uitvoering voor Claude Code** — één commando installeert een
PreToolUse-hook die overeenkomende tool-calls pauzeert *voordat* ze draaien en op
jouw beslissing wacht (één tik vanaf je telefoon met
[cloud-pushmeldingen](https://app.clawmetry.com/push) ingeschakeld):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Een weigering blokkeert alleen die ene tool-call, de agent behoudt zijn sessie en kan
een andere aanpak proberen. Goedkeuren op je telefoon slaat Claude Codes eigen
permissieprompt over (je hebt al geantwoord). Niet-overeenkomende tools kosten ~40ms en
vallen terug op Claude Codes normale permissieflow. Je krijgt ook een pushmelding op je
telefoon wanneer Claude Code zelf op jou wacht (`permission_prompt`- /
`idle_prompt`-meldingen).

## Installatie

**Eén regel (aanbevolen):**
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

De v2 React-app bevindt zich in `frontend/` en wordt geserveerd op `/v2` wanneer de
Flask-server is gestart met v2 ingeschakeld.

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

Open `http://localhost:5173/v2/`. Vite proxyt `/api`-verzoeken naar
`http://localhost:8900`, zodat de React-app met de lokale Flask-server kan praten
zonder extra CORS-configuratie.

Om de bundel te bouwen die met het Python-pakket wordt meegeleverd:

```bash
cd frontend
npm run build
```

De productiebundel wordt weggeschreven naar `clawmetry/static/v2/dist/`.

## Compatibiliteit met runtimes/agents

ClawMetry observeert veel AI-agentruntimes, niet alleen OpenClaw. Elke niet-OpenClaw-runtime levert een eigen reader-adapter die het native sessieformaat vertaalt naar ClawMetry's uniforme vormen; de daemon neemt ze op in dezelfde DuckDB-store + cloud-snapshot, getagd met de runtime, en het tabblad Session replay toont een **runtimewisselaar** wanneer er meer dan één aanwezig is. Zie [`docs/compatibility.md`](docs/compatibility.md) voor de volledige matrix + een handleiding voor het toevoegen van runtimes, en [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) voor de inleiding tot de OpenClaw-familie.

| Runtime / Agent | Status | Notities |
|---|---|---|
| **OpenClaw** | Native | Referentieruntime, automatisch gedetecteerd |
| **PicoClaw** | Beta-adapter | Platte `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripten, model, tool-calls. |
| **NanoClaw** | Beta-adapter | SQLite per sessie (`data/v2-sessions`). Transcripten + berichttellingen. |
| **Hermes** | Beta-adapter | SQLite `~/.hermes/state.db`. Transcripten, model, tokens/kosten. |
| **Claude Code** | Beta-adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripten, model, tool-calls + denkstappen, tokengebruik. |
| **Codex** | Beta-adapter | Rollout-JSONL `~/.codex/sessions/...`. Transcripten, model, tool-calls, tokengebruik. |
| **Cursor** | Beta-adapter | SQLite `state.vscdb`. Chat-/composer-transcripten, model. |
| **Aider** | Beta-adapter | `.aider.chat.history.md` per project. Transcripten, model, tokentellingen. |
| **Goose** | Beta-adapter | SQLite `~/.local/share/goose`. Transcripten, model, tool-calls, totaal aantal tokens. |
| **opencode** | Beta-adapter | SQLite `~/.local/share/opencode`. Transcripten, model, tool-calls, tokens + kosten. |
| **Qwen Code** | Beta-adapter | JSONL `~/.qwen/projects/.../chats`. Transcripten, model, tool-calls, tokengebruik. |
| **Pi** | Beta-adapter | JSONL `~/.pi/agent/sessions`. Transcripten, model, tool-calls, tokens + kosten. |
| **Deep Agents** | Beta-adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripten, model, tool-calls, tokens + kosten. |
| **n8n** | Beta-adapter | SQLite `~/.n8n/database.sqlite`. Workflow-executies, node-runs, AI Agent-prompts, model + tokens waar n8n die registreert. |

"Beta-adapter" betekent dat ClawMetry een reader levert voor het echte, op-schijf-formaat van die runtime, elk gebouwd + geverifieerd tegen een echte installatie op een echte machine (zie `tests/fixtures/runtimes/<rt>/`). Adapters zijn alleen-lezen; elk is eerlijk over wat de betreffende runtime daadwerkelijk opslaat (bijv. PicoClaw/NanoClaw/Cursor schrijven geen tokenkosten naar schijf). Wanneer er meerdere runtimes op één node draaien, beperkt de runtimewisselaar de sessieweergave tot één, voor een overzichtelijke deep-dive.

## Volg elke SDK-agent — out-loop kostentoerekening

De runtimes hierboven schrijven allemaal sessies naar schijf. Jouw eigen **productieagent** — degene die je hebt gebouwd op de OpenAI Agents SDK, LangChain, de Vercel AI SDK, LlamaIndex, E2B, of een gewone `httpx`-loop — doet dat niet. ClawMetry's zero-config interceptor vangt zijn LLM-calls (kosten, tokens, latency, fouten) nog steeds op door `httpx`/`requests` te monkey-patchen:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (of de omgevingsvariabele `CLAWMETRY_SOURCE=support-agent`) tagt elke call met een **benoemde bron**, zodat elk product dat je draait als eigen, volwaardig, kostentoerekenbaar item verschijnt in de kaart **🔌 Out-loop sources** van het dashboard op Overview, calls, providers, latency, foutpercentage per agent. Geen bron ingesteld? De calls worden nog steeds bijgehouden; de kaart blijft dan gewoon verborgen.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Dit is dezelfde datalaag die de runtime-adapters voeden (DuckDB → cloud-snapshot), dus out-loop sources synchroniseren met het clouddashboard net als al het andere, E2E-versleuteld.

## OpenTelemetry — leveranciersneutraal, stuur je traces overal naartoe

ClawMetry spreekt **OpenTelemetry** in beide richtingen, met de **GenAI semantic conventions**, zodat je agenttraces nooit vastzitten aan één tool.

**Exporteer** elke sessie — LLM-calls, tools, sub-agents, tokens, kosten — als OTLP/HTTP GenAI-spans naar elke collector (Datadog, Grafana, Honeycomb, of je eigen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth-headers en poll-interval zijn optionele omgevingsvariabelen:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** — de ingebouwde OTLP-receiver accepteert traces en metrics van alles anders op `/v1/traces` en `/v1/metrics` (`pip install clawmetry[otel]` voor protobuf-ingest).

Je krijgt het zero-config, local-first ClawMetry-dashboard **en** je data in welke backend je team ook al gebruikt, geen lock-in, geen tweede agent om te installeren.

## Configuratie

De meeste mensen hebben geen configuratie nodig. ClawMetry detecteert automatisch je workspace, logs, sessies en crons.

Als je toch wilt aanpassen:

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
| 🌐 **Webchat** | ✅ Volledig | ✅ | Ingebouwde webUI-sessies |
| 📡 **IRC** | ✅ Volledig | ✅ | Terminal-stijl bubbel-UI |
| 🍏 **BlueBubbles** | ✅ Volledig | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Volledig | ✅ | Via Chat API-webhooks |
| 🟣 **MS Teams** | ✅ Volledig | ✅ | Via Teams-botplug-in |
| 🔷 **Mattermost** | ✅ Volledig | ✅ | Zelfgehoste teamchat |
| 🟩 **Matrix** | ✅ Volledig | ✅ | Gedecentraliseerd, E2EE-ondersteuning |
| 🟢 **LINE** | ✅ Volledig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Volledig | ✅ | Gedecentraliseerde NIP-04 DM's |
| 🟣 **Twitch** | ✅ Volledig | ✅ | Chat via IRC-verbinding |
| 🔷 **Feishu/Lark** | ✅ Volledig | ✅ | WebSocket-eventabonnement |
| 🔵 **Zalo** | ✅ Volledig | ✅ | Zalo Bot API |

> **Automatische detectie:** ClawMetry leest je `~/.openclaw/openclaw.json` en toont alleen de kanalen die je daadwerkelijk hebt geconfigureerd. Geen handmatige instelling nodig.

## Docker-implementatie

Wil je ClawMetry in een container draaien? Geen probleem! 🐳

**Snelle start met Docker:**

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

**Voorbeeld van Docker Compose:**

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

> **Opmerking:** Wanneer je in Docker draait, mount dan de data- en logmappen van je agent (bijv. `~/.openclaw`, `~/.claude`, `~/.codex`) zodat ClawMetry je opstelling automatisch kan detecteren.

## Vereisten

- Python 3.8+
- Flask (automatisch geïnstalleerd via pip)
- Een AI-agentruntime op dezelfde machine: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents of n8n (of gemounte volumes voor Docker)
- Linux of macOS

## NemoClaw / OpenShell-ondersteuning

ClawMetry detecteert automatisch [NemoClaw](https://github.com/NVIDIA/NemoClaw) — NVIDIA's enterprise-beveiligingswrapper voor OpenClaw die agents draait binnen gesandboxte OpenShell-containers.

In de meeste gevallen is geen extra configuratie nodig. De sync-daemon ontdekt automatisch sessiebestanden, of ze zich nu bevinden in `~/.openclaw/` op de host of binnen een OpenShell-container.

### Hoe het werkt

ClawMetry detecteert NemoClaw op twee manieren:

1. **Binaire detectie** — controleert op de `nemoclaw`-CLI en draait `nemoclaw status` om sandbox-informatie op te halen
2. **Containerdetectie** — scant draaiende Docker-containers op `openshell`, `nemoclaw` of `ghcr.io/nvidia/`-images, en leest vervolgens sessies via volume-mounts of `docker cp`

Sessiebestanden die vanuit NemoClaw-containers worden gesynchroniseerd, krijgen `runtime=nemoclaw` en `container_id`-metadata in het clouddashboard, zodat je ze op het eerste gezicht kunt onderscheiden van standaard OpenClaw-sessies.

### Aanbevolen opzet: sync-daemon op de HOST

Voor de beste ervaring draai je ClawMetry's sync-daemon op de **hostmachine** (niet binnen de sandbox). Dit vermijdt netwerkbeleidsbeperkingen van NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

De sync-daemon vindt automatisch sessies binnen elke draaiende OpenShell-container.

### Optioneel: expliciete sandboxnaam

Als automatische detectie niet werkt, wijs ClawMetry dan naar de juiste sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Draaien binnen de sandbox (geavanceerd)

Als je de sync-daemon **binnen** de OpenShell-sandbox moet draaien, voeg dan deze egress-regel toe aan je NemoClaw-netwerkbeleid zodat hij bij de ClawMetry-ingest-API kan komen:

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
| Docker-socket (`/var/run/docker.sock`) | — | Unix-socket | Voor containersessie-detectie |

De sync-daemon doet alleen uitgaande HTTPS-calls naar `ingest.clawmetry.com`. Er zijn geen inkomende poorten vereist.

---

## Cloud-implementatie

Zie de **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** voor SSH-tunnels, reverse proxy en Docker.

## Testen

Dit project wordt getest met BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetrie

ClawMetry stuurt één anonieme "first run"-ping naar
`https://app.clawmetry.com/api/install` de eerste keer dat je de
`clawmetry` CLI op een nieuwe machine draait. We gebruiken dit om installaties te
tellen (de enige marketingmetriek die we hebben voor een OSS-project) en om te
leren welke agentframeworks onze gebruikers hebben geïnstalleerd.

**Precies één POST per installatie**, met:

| Veld | Voorbeeld | Waarom |
|---|---|---|
| `install_id` | willekeurige UUID opgeslagen in `~/.clawmetry/install_id` | deduplicatie; niet gekoppeld aan je e-mail of api_key |
| `version` | `0.12.167` | welke versies er in omloop zijn |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioriteiten voor platformondersteuning |
| `python` | `3.11.15` | ondersteuningsmatrix voor Python-versies |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | met welke agents we ons vervolgens moeten integreren |
| `is_ci` / `ci_provider` | `true` / `github_actions` | scheiding tussen menselijke installaties en CI-ruis |

**Wat we NIET versturen**: IP (de cloud leidt de landcode serverzijde af
uit het verzoek en verwijdert vervolgens het IP), hostnaam, gebruikersnaam, workspacepad,
bestandsinhoud, je api_key, je e-mail, of iets dat PII of
workspace-specifiek is. De payload op de lijn is te controleren in
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Afmelden** (elk van deze schakelt het permanent uit):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Een netwerkstoring blokkeert hier nooit het draaien van `clawmetry` — de
ping is fire-and-forget op een daemon-thread met een timeout van 3 s.

## Star History

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
