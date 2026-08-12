<!-- i18n-src:7cfb63716507 -->
> Nederlands translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zie hoe je agent denkt.** Realtime observability voor **14 AI-agent-runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex en nog 10 andere. Eén dashboard voor je hele agentenvloot.

> 🌐 **Lees dit in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [meer →](docs/i18n/)

Eén commando. Geen configuratie. Detecteert alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Opent op **http://localhost:8900** en je bent klaar.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Werkt met 14 agent-runtimes

ClawMetry begon als observability voor OpenClaw en meet nu je **hele agentenvloot** in één dashboard, waarbij elke runtime op je machine automatisch wordt gedetecteerd:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw en NemoClaw zijn gratis in de open-source app; de overige runtimes worden vrijgeschakeld met ClawMetry Cloud of een zelf gehoste Pro-licentie. Wissel van runtime via de header, en elke tab (kosten, tokens, tools, traces) past zich aan die runtime aan. Zie **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** voor de exacte verdeling tussen gratis en betaald, de tier-matrix, de vorm van `/api/entitlement` en de `clawmetry license` CLI.

## Wat je krijgt

- **Flow**: live geanimeerd diagram dat toont hoe berichten door kanalen, brain, tools en weer terug stromen
- **Overview**: health checks, activiteits-heatmap, sessieaantallen, modelinformatie
- **Usage**: token- en kostentracking met dagelijkse/wekelijkse/maandelijkse uitsplitsingen
- **Sessions**: actieve agentsessies met model, tokens, laatste activiteit
- **Crons**: geplande taken met status, volgende run, duur
- **Logs**: kleurgecodeerde realtime logstreaming
- **Memory**: blader door SOUL.md, MEMORY.md, AGENTS.md, dagelijkse notities
- **Transcripts**: chatbubbel-UI voor het lezen van sessiegeschiedenissen
- **Alerts**: budgetplafonds, foutpercentage-triggers, detectie van offline agents; stuurt door naar Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals**: beveilig destructieve verwijderingen, force pushes, DB-mutaties, sudo, pakketinstallaties en netwerkoproepen achter een goedkeuring met één klik

## Screenshots

### 🧠 Brain: live event-stream van de agent
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview: tokengebruik & sessieoverzicht
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow: realtime tool-call-feed
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens: kostenuitsplitsing per model & sessie
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory: workspace-bestandsbrowser
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security: postuur & auditlog
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts: budgetplafonds, foutpercentage-triggers, webhooks naar Slack / Discord / PagerDuty / e-mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals: beveilig risicovolle tool-calls achter handmatige goedkeuring; op beleid gebaseerde beschermingsregels
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blokkeren vóór uitvoering voor Claude Code**: één commando installeert
een PreToolUse-hook die overeenkomende tool-calls pauzeert *voordat* ze worden uitgevoerd en wacht op
jouw beslissing (met één tik vanaf je telefoon als
[cloud-pushmeldingen](https://app.clawmetry.com/push) zijn ingeschakeld):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Een weigering blokkeert alleen die ene tool-call: de agent behoudt zijn sessie en kan
een andere aanpak proberen. Goedkeuren via je telefoon slaat de eigen
permissieprompt van Claude Code over (je hebt immers al geantwoord). Tools die niet overeenkomen kosten ~40ms en
vallen terug op de normale permissieflow van Claude Code. Je krijgt ook een
pushmelding op je telefoon wanneer Claude Code zelf op jou wacht (`permission_prompt` /
`idle_prompt` meldingen).

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

**Vanuit de broncode:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2-frontend-ontwikkeling

De v2 React-app bevindt zich in `frontend/` en wordt geserveerd op `/v2` wanneer de Flask-
server met v2 ingeschakeld wordt gestart.

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

Open `http://localhost:5173/v2/`. Vite stuurt `/api`-aanvragen door naar
`http://localhost:8900`, zodat de React-app met de lokale Flask-server kan communiceren
zonder extra CORS-configuratie.

Om de bundle te bouwen die met het Python-pakket wordt meegeleverd:

```bash
cd frontend
npm run build
```

De productiebundel wordt weggeschreven naar `clawmetry/static/v2/dist/`.

## Runtime-/agentcompatibiliteit

ClawMetry observeert veel AI-agent-runtimes, niet alleen OpenClaw. Elke niet-OpenClaw-runtime levert een eigen reader-adapter die het native sessieformaat vertaalt naar de uniforme datastructuren van ClawMetry; de daemon neemt ze op in dezelfde DuckDB-opslag + cloud-snapshot, gelabeld met de runtime, en de Session replay-tab toont een **runtime-switcher** zodra er meer dan één aanwezig is. Zie [`docs/compatibility.md`](docs/compatibility.md) voor de volledige matrix plus een handleiding voor het toevoegen van runtimes, en [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) voor de inleiding tot de OpenClaw-familie.

Gebruik je de agent-security-tool [numbat van Perplexity](https://github.com/perplexityai/numbat)? ClawMetry neemt de bevindingen en handhavingsbeslissingen ervan out of the box op, zie [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Status | Opmerkingen |
|---|---|---|
| **OpenClaw** | Native | Referentie-runtime, automatisch gedetecteerd |
| **PicoClaw** | Bèta-adapter | Platte `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, model, tool-calls. |
| **NanoClaw** | Bèta-adapter | SQLite per sessie (`data/v2-sessions`). Transcripts + berichtaantallen. |
| **Hermes** | Bèta-adapter | SQLite `~/.hermes/state.db`. Transcripts, model, tokens/kosten. |
| **Claude Code** | Bèta-adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, model, tool-calls + thinking, tokengebruik. |
| **Codex** | Bèta-adapter | Rollout-JSONL `~/.codex/sessions/...`. Transcripts, model, tool-calls, tokengebruik. |
| **Cursor** | Bèta-adapter | SQLite `state.vscdb`. Chat-/composer-transcripts, model. |
| **Aider** | Bèta-adapter | `.aider.chat.history.md` per project. Transcripts, model, tokenaantallen. |
| **Goose** | Bèta-adapter | SQLite `~/.local/share/goose`. Transcripts, model, tool-calls, tokentotalen. |
| **opencode** | Bèta-adapter | SQLite `~/.local/share/opencode`. Transcripts, model, tool-calls, tokens + kosten. |
| **Qwen Code** | Bèta-adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, model, tool-calls, tokengebruik. |
| **Pi** | Bèta-adapter | JSONL `~/.pi/agent/sessions`. Transcripts, model, tool-calls, tokens + kosten. |
| **Deep Agents** | Bèta-adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, model, tool-calls, tokens + kosten. |
| **n8n** | Bèta-adapter | SQLite `~/.n8n/database.sqlite`. Workflow-uitvoeringen, node-runs, AI Agent-prompts, model + tokens waar n8n die vastlegt. |
| **Antigravity** | Bèta-adapter | Brain-JSONL onder `~/.gemini/<flavor>/brain/`. Conversaties, toolstappen, thinking, Gemini-tokensplitsing per generatie + kosten, verbruik van achtergrondgeneraties. |
| **GitHub Copilot** | Bèta-adapter | Copilot CLI `events.jsonl` onder `~/.copilot/session-state/` + het `session-store.db` gebruiksregister per aanroep. Conversaties, tool-calls, modelroutering, cache-bewuste tokensplitsing, door de leverancier gefactureerde AI-creditkosten. |
| **Grok** | Bèta-adapter | xAI Grok Build CLI (Rust-binary onder `~/.grok/bin/grok`): globaal event-log `~/.grok/logs/unified.jsonl` + per sessie `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Conversaties, tokensplitsing per beurt, modelroutering, en de uitgaande repo-payload van de CLI die tijdelijk wordt opgeslagen onder `~/.grok/upload_queue/`, zodat je kunt zien wat je machine heeft verlaten. |

"Bèta-adapter" betekent dat ClawMetry een reader levert voor het echte schijfformaat van die runtime, elk gebouwd en geverifieerd tegen een echte installatie op een echte machine (zie `tests/fixtures/runtimes/<rt>/`). Adapters zijn alleen-lezen; elke adapter is eerlijk over wat de bijbehorende runtime daadwerkelijk opslaat (bijvoorbeeld: PicoClaw/NanoClaw/Cursor schrijven geen tokenkosten naar schijf). Wanneer meerdere runtimes op één node draaien, beperkt de runtime-switcher de sessieweergave tot één runtime voor een overzichtelijke deep-dive.

## Elke SDK-agent tracken: out-loop-kostentoewijzing

De runtimes hierboven schrijven allemaal sessies naar schijf. Je eigen **productieagent** (degene die je hebt gebouwd op de OpenAI Agents SDK, LangChain, de Vercel AI SDK, LlamaIndex, E2B, of een simpele `httpx`-loop) doet dat niet. De zero-config interceptor van ClawMetry legt de LLM-aanroepen ervan (kosten, tokens, latentie, fouten) toch vast door `httpx`/`requests` te monkeypatchen:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (of de omgevingsvariabele `CLAWMETRY_SOURCE=support-agent`) labelt elke aanroep met een **benoemde bron**, zodat elk product dat je draait als een eigen, kostentoewijsbare regel verschijnt in de kaart **🔌 Out-loop sources** op Overview in het dashboard: aanroepen, providers, latentie, foutpercentage per agent. Geen bron ingesteld? De aanroepen worden nog steeds getrackt; de kaart blijft dan gewoon verborgen.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Dit is dezelfde datalaag die de runtime-adapters voeden (DuckDB → cloud-snapshot), dus out-loop-bronnen synchroniseren met het clouddashboard net als al het andere, end-to-end versleuteld.

## OpenTelemetry: leveranciersneutraal, stuur je traces overal naartoe

ClawMetry spreekt **OpenTelemetry** in beide richtingen, met gebruik van de **GenAI semantic conventions**, zodat je agenttraces nooit vastzitten aan één tool.

**Exporteer** elke sessie (LLM-aanroepen, tools, sub-agents, tokens, kosten) als OTLP/HTTP GenAI-spans naar elke collector (Datadog, Grafana, Honeycomb, of je eigen OTel Collector):

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

**Ingest**: de ingebouwde OTLP-ontvanger accepteert traces en metrics van al het andere op `/v1/traces` en `/v1/metrics` (`pip install clawmetry[otel]` voor protobuf-ingest).

Je krijgt het zero-config, local-first ClawMetry-dashboard **en** je data in welke backend je team ook al draait, zonder lock-in, zonder een tweede agent te installeren.

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

ClawMetry toont live activiteit voor elk OpenClaw-kanaal dat je hebt geconfigureerd. Alleen kanalen die daadwerkelijk zijn ingesteld in je `openclaw.json` verschijnen in het Flow-diagram; niet-geconfigureerde kanalen worden automatisch verborgen.

Klik op een willekeurige kanaalnode in de Flow om een live chatbubbelweergave te zien met aantallen inkomende/uitgaande berichten.

| Kanaal | Status | Live pop-up | Opmerkingen |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Volledig | ✅ | Berichten, statistieken, 10s verversing |
| 💬 **iMessage** | ✅ Volledig | ✅ | Leest `~/Library/Messages/chat.db` rechtstreeks |
| 💚 **WhatsApp** | ✅ Volledig | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Volledig | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Volledig | ✅ | Detectie van guild + kanaal |
| 🟪 **Slack** | ✅ Volledig | ✅ | Detectie van workspace + kanaal |
| 🌐 **Webchat** | ✅ Volledig | ✅ | Sessies van de ingebouwde web-UI |
| 📡 **IRC** | ✅ Volledig | ✅ | Terminalachtige bubbel-UI |
| 🍏 **BlueBubbles** | ✅ Volledig | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Volledig | ✅ | Via Chat API-webhooks |
| 🟣 **MS Teams** | ✅ Volledig | ✅ | Via Teams-botplugin |
| 🔷 **Mattermost** | ✅ Volledig | ✅ | Zelf gehoste teamchat |
| 🟩 **Matrix** | ✅ Volledig | ✅ | Gedecentraliseerd, met E2EE-ondersteuning |
| 🟢 **LINE** | ✅ Volledig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Volledig | ✅ | Gedecentraliseerde NIP-04-DM's |
| 🟣 **Twitch** | ✅ Volledig | ✅ | Chat via IRC-verbinding |
| 🔷 **Feishu/Lark** | ✅ Volledig | ✅ | WebSocket-eventabonnement |
| 🔵 **Zalo** | ✅ Volledig | ✅ | Zalo Bot API |

> **Automatische detectie:** ClawMetry leest je `~/.openclaw/openclaw.json` en toont alleen de kanalen die je daadwerkelijk hebt geconfigureerd. Geen handmatige instelling nodig.

## Docker-deployment

Wil je ClawMetry in een container draaien? Geen probleem! 🐳

**Snelstart met Docker:**

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

> **Let op:** wanneer je in Docker draait, mount dan de data- en logmappen van je agent (bijv. `~/.openclaw`, `~/.claude`, `~/.codex`) zodat ClawMetry je setup automatisch kan detecteren.

## Vereisten

- Python 3.8+
- Flask (wordt automatisch geïnstalleerd via pip)
- Een AI-agent-runtime op dezelfde machine: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, of QM (of gemounte volumes voor Docker)
- Linux of macOS

## NemoClaw-/OpenShell-ondersteuning

ClawMetry detecteert automatisch [NemoClaw](https://github.com/NVIDIA/NemoClaw), NVIDIA's enterprise-securitywrapper voor OpenClaw die agents laat draaien binnen sandboxed OpenShell-containers.

In de meeste gevallen is geen extra configuratie nodig. De sync-daemon ontdekt sessiebestanden automatisch, of ze zich nu in `~/.openclaw/` op de host bevinden of binnen een OpenShell-container.

### Hoe het werkt

ClawMetry detecteert NemoClaw op twee manieren:

1. **Binaire detectie**: controleert op de `nemoclaw` CLI en voert `nemoclaw status` uit om sandboxinformatie op te halen
2. **Containerdetectie**: scant draaiende Docker-containers op `openshell`-, `nemoclaw`- of `ghcr.io/nvidia/`-images en leest sessies vervolgens via volume-mounts of `docker cp`

Sessiebestanden die gesynchroniseerd worden vanuit NemoClaw-containers krijgen in het clouddashboard de metadata `runtime=nemoclaw` en `container_id`, zodat je ze in één oogopslag kunt onderscheiden van standaard OpenClaw-sessies.

### Aanbevolen setup: sync-daemon op de HOST

Voor de beste ervaring draai je de sync-daemon van ClawMetry op de **hostmachine** (niet binnen de sandbox). Zo vermijd je beperkingen van het NemoClaw-netwerkbeleid.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

De sync-daemon vindt automatisch sessies binnen alle draaiende OpenShell-containers.

### Optioneel: expliciete sandboxnaam

Als automatische detectie niet werkt, wijs ClawMetry dan naar de juiste sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Draaien binnen de sandbox (geavanceerd)

Als je de sync-daemon **binnen** de OpenShell-sandbox moet draaien, voeg dan deze egress-regel toe aan je NemoClaw-netwerkbeleid zodat deze de ClawMetry ingest-API kan bereiken:

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
| Docker-socket (`/var/run/docker.sock`) | n.v.t. | Unix-socket | Voor het ontdekken van containersessies |

De sync-daemon doet alleen uitgaande HTTPS-aanroepen naar `ingest.clawmetry.com`. Er zijn geen inkomende poorten vereist.

---

## Cloud-deployment

Zie de **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** voor SSH-tunnels, reverse proxy en Docker.

## Testen

Dit project wordt getest met BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetrie

ClawMetry stuurt anonieme install-lifecycle-pings naar
`https://app.clawmetry.com/api/install`: één `install`-ping de eerste keer
dat je de `clawmetry`-CLI op een nieuwe machine uitvoert, één `update`-ping
bij de eerste run na het upgraden naar een nieuwe versie, en één `onboarded`-
ping wanneer je de onboardingkeuze in het dashboard voltooit. Hiermee tellen we
echte installaties (ruwe PyPI-downloadcijfers bestaan voor ~98% uit mirrors, CI
en auto-update-herdownloads) en komen we te weten welke agentframeworks en
versies daadwerkelijk in gebruik zijn.

**Maximaal één POST per lifecycle-event per versie**, met de volgende inhoud:

| Veld | Voorbeeld | Waarom |
|---|---|---|
| `install_id` | willekeurige UUID, opgeslagen op `~/.clawmetry/install_id` | deduplicatie; anoniem totdat je expliciet Cloud sync verbindt (de geauthenticeerde daemon-heartbeat draagt het dan mee en koppelt deze installatie aan je account) |
| `event` | `install` / `update` / `onboarded` | nieuwe installatie versus upgrade van een bestaande |
| `version` | `0.12.167` | welke versies in gebruik zijn |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioriteiten voor platformondersteuning |
| `python` | `3.11.15` | ondersteuningsmatrix voor Python-versies |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | met welke agents we hierna moeten integreren |
| `is_ci` / `ci_provider` | `true` / `github_actions` | menselijke installaties scheiden van CI-ruis |

**Wat we NIET versturen**: IP-adres (de cloud leidt de landcode serverside
af uit het verzoek en verwerpt daarna het IP-adres), hostname, gebruikersnaam, workspace-
pad, bestandsinhoud, je api_key, je e-mailadres, of iets anders dat persoonsgegevens bevat of
workspace-specifiek is. De payload die over de lijn gaat is controleerbaar in
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Afmelden** (elk van deze opties schakelt het permanent uit):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Een netwerkfout blokkeert hier nooit het draaien van `clawmetry`: de
ping is fire-and-forget op een daemon-thread met een timeout van 3 seconden.

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
  <strong>🦞 Zie hoe je agent denkt</strong><br>
  <sub>Gebouwd door <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Onderdeel van het <a href="https://github.com/openclaw/openclaw">OpenClaw</a>-ecosysteem</sub>
</p>
