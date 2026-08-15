<!-- i18n-src:c422fb7dd0da -->
> Nederlands translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zie je agent denken.** Realtime observability voor **20 AI-agentruntimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 16 andere. Eén dashboard voor je hele agentvloot.

> 🌐 **Lees dit in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [meer →](docs/i18n/)

Eén commando. Geen configuratie. Detecteert alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Opent op **http://localhost:8900** en je bent klaar.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Werkt met 20 agentruntimes

ClawMetry begon als observability voor OpenClaw en meet nu je **hele agentvloot** in één dashboard, waarbij elke runtime op je machine automatisch wordt gedetecteerd:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw en NemoClaw zijn gratis in de open-source app; de andere runtimes worden geactiveerd met ClawMetry Cloud of een zelf-gehoste Pro-licentie. Wissel van runtime via de header en elk tabblad, kosten, tokens, tools, traces, herschaalt naar die runtime. Zie **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** voor de exacte gratis/betaalde verdeling, de tiermatrix, de `/api/entitlement`-structuur en de `clawmetry license`-CLI.

## Wat je krijgt

- **Flow** — Live geanimeerd diagram dat berichten toont die door channels, brein, tools en terug stromen
- **Overview** — Gezondheidscontroles, activiteitsheatmap, sessieaantallen, modelinfo
- **Usage** — Token- en kostentracking met dagelijkse/wekelijkse/maandelijkse uitsplitsingen
- **Sessions** — Actieve agentsessies met model, tokens, laatste activiteit
- **Crons** — Geplande taken met status, volgende run, duur
- **Logs** — Kleurgecodeerde realtime logstreaming
- **Memory** — Blader door SOUL.md, MEMORY.md, AGENTS.md, dagelijkse notities
- **Transcripts** — Chatbubbel-UI voor het lezen van sessiegeschiedenissen
- **Alerts** — Budgetlimieten, foutpercentage-triggers, detectie van offline agents; routeert naar Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals** — Blokkeer destructieve verwijderingen, force pushes, DB-mutaties, sudo, pakketinstallaties, netwerkoproepen achter een goedkeuring met één klik

## Screenshots

### 🧠 Brain — Live agent-eventstream
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Tokengebruik & sessiesamenvatting
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Realtime feed van tool-aanroepen
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Kostenuitsplitsing per model & sessie
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Bestandsverkenner voor de workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postuur & auditlog
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budgetlimieten, foutpercentage-triggers, webhooks naar Slack / Discord / PagerDuty / e-mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blokkeer risicovolle tool-aanroepen achter handmatige goedkeuring; beleidsgestuurde beschermingsregels
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blokkering vóór uitvoering voor Claude Code** — één commando installeert een
PreToolUse-hook die overeenkomende tool-aanroepen pauzeert *voordat* ze worden uitgevoerd en
wacht op jouw beslissing (één tik vanaf je telefoon met
[cloud-pushmeldingen](https://app.clawmetry.com/push) ingeschakeld):

```bash
clawmetry hooks install     # schrijft ~/.claude/settings.json (idempotent)
clawmetry hooks status      # wat is aangesloten + hoeveel beleidsregels actief zijn
clawmetry hooks uninstall   # verwijdert alleen de items van ClawMetry
```

Een weigering blokkeert alleen die ene tool-aanroep; de agent behoudt zijn sessie en kan
een andere aanpak proberen. Goedkeuren op je telefoon slaat de eigen
toestemmingsprompt van Claude Code over (je hebt al geantwoord). Niet-overeenkomende tools kosten ~40ms en
vallen terug op de normale toestemmingsflow van Claude Code. Je krijgt ook een pushmelding op je telefoon wanneer Claude Code zelf op jou wacht (`permission_prompt`- /
`idle_prompt`-meldingen).

## Installeren

**One-liner (aanbevolen):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Vanuit de broncode:**
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

Open `http://localhost:5173/v2/`. Vite proxyt `/api`-verzoeken naar
`http://localhost:8900`, zodat de React-app met de lokale Flask-server kan praten
zonder extra CORS-configuratie.

Om de bundel te bouwen die met het Python-pakket wordt uitgeleverd:

```bash
cd frontend
npm run build
```

De productiebundel wordt weggeschreven naar `clawmetry/static/v2/dist/`.

## Runtime-/agentcompatibiliteit

ClawMetry observeert veel AI-agentruntimes, niet alleen OpenClaw. Elke niet-OpenClaw-runtime levert een specifieke reader-adapter die het native sessieformaat vertaalt naar de uniforme structuren van ClawMetry; de daemon neemt ze op in dezelfde DuckDB-store + cloudsnapshot, getagd met de runtime, en het tabblad Session replay toont een **runtime-schakelaar** wanneer er meer dan één aanwezig is. Zie [`docs/compatibility.md`](docs/compatibility.md) voor de volledige matrix + een handleiding voor het toevoegen van runtimes, en [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) voor de inleiding tot de OpenClaw-familie.

Gebruik je [Perplexity's numbat](https://github.com/perplexityai/numbat) agent-securitytool? ClawMetry neemt de bevindingen en handhavingsbeslissingen daarvan standaard op; zie [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / agent | Status | Notities |
|---|---|---|
| **OpenClaw** | Native | Referentieruntime, automatisch gedetecteerd |
| **PicoClaw** | Beta-adapter | Platte `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, model, tool-aanroepen. |
| **NanoClaw** | Beta-adapter | SQLite per sessie (`data/v2-sessions`). Transcripts + berichttellingen. |
| **Hermes** | Beta-adapter | SQLite `~/.hermes/state.db`. Transcripts, model, tokens/kosten. |
| **Claude Code** | Beta-adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, model, tool-aanroepen + denkstappen, tokengebruik. |
| **Codex** | Beta-adapter | Rollout-JSONL `~/.codex/sessions/...`. Transcripts, model, tool-aanroepen, tokengebruik. |
| **Cursor** | Beta-adapter | SQLite `state.vscdb`. Chat-/composer-transcripts, model. |
| **Aider** | Beta-adapter | `.aider.chat.history.md` per project. Transcripts, model, tokentellingen. |
| **Goose** | Beta-adapter | SQLite `~/.local/share/goose`. Transcripts, model, tool-aanroepen, tokentotalen. |
| **opencode** | Beta-adapter | SQLite `~/.local/share/opencode`. Transcripts, model, tool-aanroepen, tokens + kosten. |
| **Qwen Code** | Beta-adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, model, tool-aanroepen, tokengebruik. |
| **Pi** | Beta-adapter | JSONL `~/.pi/agent/sessions`. Transcripts, model, tool-aanroepen, tokens + kosten. |
| **Deep Agents** | Beta-adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, model, tool-aanroepen, tokens + kosten. |
| **n8n** | Beta-adapter | SQLite `~/.n8n/database.sqlite`. Workflow-uitvoeringen, node-runs, AI Agent-prompts, model + tokens waar n8n die vastlegt. |
| **Antigravity** | Beta-adapter | Brain-JSONL onder `~/.gemini/<flavor>/brain/`. Gesprekken, toolstappen, denkstappen, Gemini-tokenverdeling per generatie + kosten, verbruik van achtergrondgeneraties. |
| **GitHub Copilot** | Beta-adapter | Copilot CLI `events.jsonl` onder `~/.copilot/session-state/` + het `session-store.db`-gebruiksregister per aanroep. Gesprekken, tool-aanroepen, modelroutering, cache-bewuste tokenverdeling, door de leverancier gefactureerde AI-creditkosten. |
| **Grok** | Beta-adapter | xAI Grok Build CLI (Rust-binary onder `~/.grok/bin/grok`): globaal eventlog `~/.grok/logs/unified.jsonl` + sessie-specifiek `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Gesprekken, tokenverdeling per beurt, modelroutering, en de uitgaande repo-payload van de CLI die wordt opgeslagen onder `~/.grok/upload_queue/` zodat je kunt zien wat je machine heeft verlaten. |

"Beta-adapter" betekent dat ClawMetry een reader levert voor het echte on-disk-formaat van die runtime, elk gebouwd + geverifieerd tegen een echte installatie op een echte machine (zie `tests/fixtures/runtimes/<rt>/`). Adapters zijn alleen-lezen; elk is eerlijk over wat de bijbehorende runtime daadwerkelijk opslaat (bijv. PicoClaw/NanoClaw/Cursor schrijven geen tokenkosten naar schijf). Wanneer er meerdere runtimes op één node draaien, beperkt de runtime-schakelaar de sessieweergave tot één, voor een overzichtelijke deep-dive.

## Volg elke SDK-agent — kostentoewijzing buiten de loop

De bovenstaande runtimes schrijven allemaal sessies naar schijf. Jouw eigen **productieagent**, degene die je hebt gebouwd op de OpenAI Agents SDK, LangChain, de Vercel AI SDK, LlamaIndex, E2B, of een simpele `httpx`-loop, doet dat niet. De zero-config-interceptor van ClawMetry vangt de LLM-aanroepen ervan toch op (kosten, tokens, latency, fouten) door `httpx`/`requests` te monkeypatchen:

```python
import clawmetry.track            # activeer de interceptor
clawmetry.track.set_source("support-agent")   # geef dit product een naam

# ...je agent draait gewoon; elke LLM-aanroep wordt nu getrackt + toegewezen.
```

`set_source()` (of de omgevingsvariabele `CLAWMETRY_SOURCE=support-agent`) tagt elke aanroep met een **benoemde bron**, zodat elk product dat je draait verschijnt als een eigen, volwaardig, kosten-toewijsbaar item in de kaart **🔌 Out-loop sources** van het dashboard op Overview, aanroepen, providers, latency, foutpercentage per agent. Geen bron ingesteld? De aanroepen worden nog steeds getrackt; de kaart blijft dan alleen verborgen.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Dit is dezelfde datalaag die de runtime-adapters voeden (DuckDB → cloudsnapshot), dus out-loop-bronnen synchroniseren net als al het andere naar het clouddashboard, end-to-end versleuteld.

## OpenTelemetry — leveranciersneutraal, stuur je traces overal naartoe

ClawMetry spreekt **OpenTelemetry** in beide richtingen, met de **GenAI semantic conventions**, zodat je agenttraces nooit vastzitten aan één tool.

**Exporteer** elke sessie, LLM-aanroepen, tools, sub-agents, tokens, kosten, als OTLP/HTTP GenAI-spans naar elke collector (Datadog, Grafana, Honeycomb, of je eigen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalent:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth-headers en pollinterval zijn optionele omgevingsvariabelen:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP-headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconden (standaard 60)
```

**Ingest** — de ingebouwde OTLP-ontvanger accepteert traces, logs en metrics van alles anders op `/v1/traces`, `/v1/logs` en `/v1/metrics`. Wijs elke OpenTelemetry-geïnstrumenteerde app ernaartoe:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON-traces en -logs werken op een gewone `pip install clawmetry`, zonder extra's. Protobuf-ingest (en OTLP/JSON-metrics) heeft `pip install clawmetry[otel]` nodig. Een app die zijn eigen `service.name` instelt, verschijnt als eigen agent in de runtime-schakelaar, met zijn eigen kosten en tokens.

Je krijgt het zero-config, local-first ClawMetry-dashboard **én** je data in welk backend je team ook al gebruikt; geen lock-in, geen tweede agent om te installeren.

## Configuratie

De meeste mensen hebben geen configuratie nodig. ClawMetry detecteert automatisch je workspace, logs, sessies en crons.

Als je toch wilt aanpassen:

```bash
clawmetry --port 9000              # Aangepaste poort (standaard: 8900)
clawmetry --host 127.0.0.1         # Alleen aan localhost binden
clawmetry --workspace ~/mybot      # Aangepast workspace-pad
clawmetry --name "Alice"           # Jouw naam in de Flow-visualisatie
```

Alle opties: `clawmetry --help`

## Ondersteunde channels

ClawMetry toont live activiteit voor elk OpenClaw-channel dat je hebt geconfigureerd. Alleen channels die daadwerkelijk zijn ingesteld in je `openclaw.json` verschijnen in het Flow-diagram; niet-geconfigureerde worden automatisch verborgen.

Klik op een channel-node in de Flow om een live chatbubbelweergave te zien met tellingen van inkomende/uitgaande berichten.

| Channel | Status | Live pop-up | Notities |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Volledig | ✅ | Berichten, statistieken, verversing elke 10s |
| 💬 **iMessage** | ✅ Volledig | ✅ | Leest `~/Library/Messages/chat.db` rechtstreeks |
| 💚 **WhatsApp** | ✅ Volledig | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Volledig | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Volledig | ✅ | Detectie van guild + channel |
| 🟪 **Slack** | ✅ Volledig | ✅ | Detectie van workspace + channel |
| 🌐 **Webchat** | ✅ Volledig | ✅ | Ingebouwde web-UI-sessies |
| 📡 **IRC** | ✅ Volledig | ✅ | Bubbel-UI in terminalstijl |
| 🍏 **BlueBubbles** | ✅ Volledig | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Volledig | ✅ | Via Chat API-webhooks |
| 🟣 **MS Teams** | ✅ Volledig | ✅ | Via Teams-botplugin |
| 🔷 **Mattermost** | ✅ Volledig | ✅ | Zelf-gehoste teamchat |
| 🟩 **Matrix** | ✅ Volledig | ✅ | Gedecentraliseerd, E2EE-ondersteuning |
| 🟢 **LINE** | ✅ Volledig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Volledig | ✅ | Gedecentraliseerde NIP-04-DM's |
| 🟣 **Twitch** | ✅ Volledig | ✅ | Chat via IRC-verbinding |
| 🔷 **Feishu/Lark** | ✅ Volledig | ✅ | WebSocket-eventabonnement |
| 🔵 **Zalo** | ✅ Volledig | ✅ | Zalo Bot API |

> **Automatische detectie:** ClawMetry leest je `~/.openclaw/openclaw.json` en toont alleen de channels die je daadwerkelijk hebt geconfigureerd. Geen handmatige instelling nodig.

## Docker-implementatie

Wil je ClawMetry in een container draaien? Geen probleem! 🐳

**Snelstart met Docker:**

```bash
# Bouw de image
docker build -t clawmetry .

# Draai met standaardinstellingen
docker run -p 8900:8900 clawmetry

# Of mount de datamap van je agent (getoond: OpenClaw's ~/.openclaw)
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

> **Let op:** Mount bij het draaien in Docker de data- en logmappen van je agent (bijv. `~/.openclaw`, `~/.claude`, `~/.codex`) zodat ClawMetry je opstelling automatisch kan detecteren.

## Vereisten

- Python 3.8+
- Flask (automatisch geïnstalleerd via pip)
- Een AI-agentruntime op dezelfde machine: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, of QM (of gemounte volumes voor Docker)
- Linux of macOS

## NemoClaw-/OpenShell-ondersteuning

ClawMetry detecteert automatisch [NemoClaw](https://github.com/NVIDIA/NemoClaw), NVIDIA's enterprise-securitywrapper voor OpenClaw die agents laat draaien binnen gesandboxte OpenShell-containers.

In de meeste gevallen is geen extra configuratie nodig. De sync-daemon ontdekt automatisch sessiebestanden, of ze nu op de host in `~/.openclaw/` staan of binnen een OpenShell-container.

### Hoe het werkt

ClawMetry detecteert NemoClaw op twee manieren:

1. **Binary-detectie** — controleert op de `nemoclaw`-CLI en voert `nemoclaw status` uit om sandbox-info op te halen
2. **Containerdetectie** — scant draaiende Docker-containers op `openshell`-, `nemoclaw`- of `ghcr.io/nvidia/`-images, en leest vervolgens sessies via volume-mounts of `docker cp`

Sessiebestanden die vanuit NemoClaw-containers zijn gesynchroniseerd, worden in het clouddashboard getagd met `runtime=nemoclaw` en `container_id`-metadata, zodat je ze in één oogopslag kunt onderscheiden van standaard OpenClaw-sessies.

### Aanbevolen opzet: sync-daemon op de HOST

Voor de beste ervaring draai je de sync-daemon van ClawMetry op de **hostmachine** (niet binnen de sandbox). Dit voorkomt beperkingen door het netwerkbeleid van NemoClaw.

```bash
# Op de host (buiten de sandbox)
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

Als je de sync-daemon **binnen** de OpenShell-sandbox moet draaien, voeg dan deze egress-regel toe aan je NemoClaw-netwerkbeleid zodat deze de ingest-API van ClawMetry kan bereiken:

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

De sync-daemon doet alleen uitgaande HTTPS-aanroepen naar `ingest.clawmetry.com`. Er zijn geen inkomende poorten vereist.

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
bij de eerste run na een upgrade naar een nieuwe versie, en één `onboarded`-
ping wanneer je de onboardingkeuze in het dashboard voltooit. We gebruiken dit
om echte installaties te tellen (ruwe PyPI-downloadcijfers bestaan voor ~98% uit mirrors, CI,
en herdownloads door automatische updates) en om te leren welke agentframeworks en
versies daadwerkelijk in gebruik zijn.

**Hoogstens één POST per lifecycle-event per versie**, met de volgende inhoud:

| Veld | Voorbeeld | Waarom |
|---|---|---|
| `install_id` | willekeurige UUID opgeslagen in `~/.clawmetry/install_id` | deduplicatie; anoniem totdat je expliciet Cloud sync koppelt (de geverifieerde daemon-heartbeat draagt dan mee, waardoor deze installatie aan je account wordt gekoppeld) |
| `event` | `install` / `update` / `onboarded` | nieuwe installatie versus upgrade van een bestaande |
| `version` | `0.12.167` | welke versies in gebruik zijn |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioriteiten voor platformondersteuning |
| `python` | `3.11.15` | ondersteuningsmatrix voor Python-versies |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | met welke agents we hierna moeten integreren |
| `is_ci` / `ci_provider` | `true` / `github_actions` | menselijke installaties scheiden van CI-ruis |

**Wat we NIET versturen**: IP (de cloud leidt de landcode serverzijde
af uit het verzoek en verwerpt vervolgens het IP), hostnaam, gebruikersnaam, workspacepad,
bestandsinhoud, je api_key, je e-mailadres, iets wat persoonsgegevens bevat of
workspace-specifiek is. De payload op de lijn is controleerbaar in
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Afmelden** (elk van deze schakelt het permanent uit):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per shell
export DO_NOT_TRACK=1                          # W3C cross-tool-standaard
touch ~/.clawmetry/notelemetry                 # permanente bestandsmarkering
```

Een netwerkstoring blokkeert hier nooit het draaien van `clawmetry`; de
ping is fire-and-forget op een daemonthread met een timeout van 3s.

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
