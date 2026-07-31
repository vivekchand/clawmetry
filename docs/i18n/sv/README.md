<!-- i18n-src:9a05336fbdc1 -->
> Svenska translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Se din agent tänka.** Realtidsobservabilitet för **14 AI-agentkörmiljöer**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex och 10 till. En instrumentpanel för hela din agentflotta.

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Ingen konfiguration. Upptäcker allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900** och du är klar.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Fungerar med 14 agentkörmiljöer

ClawMetry började som observabilitet för OpenClaw och mäter nu **hela din agentflotta** i en instrumentpanel, och upptäcker automatiskt varje körmiljö på din maskin:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw och NemoClaw är gratis i open source-appen; övriga körmiljöer aktiveras med ClawMetry Cloud eller en självhostad Pro-licens. Byt körmiljö från sidhuvudet, så omfattar varje flik (kostnad, tokens, verktyg, spårningar) den valda körmiljön. Se **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** för den exakta uppdelningen mellan gratis och betalt, nivåmatrisen, formen på `/api/entitlement` och CLI-kommandot `clawmetry license`.

## Vad du får

- **Flow**: Levande animerat diagram som visar meddelanden som flödar genom kanaler, hjärna, verktyg och tillbaka
- **Overview**: Hälsokontroller, aktivitetsvärmekarta, antal sessioner, modellinfo
- **Usage**: Spårning av tokens och kostnader med daglig/vecko-/månadsuppdelning
- **Sessions**: Aktiva agentsessioner med modell, tokens, senaste aktivitet
- **Crons**: Schemalagda jobb med status, nästa körning, varaktighet
- **Logs**: Färgkodad realtidsströmning av loggar
- **Memory**: Bläddra i SOUL.md, MEMORY.md, AGENTS.md, dagliga anteckningar
- **Transcripts**: Chattbubble-gränssnitt för att läsa sessionshistorik
- **Alerts**: Budgettak, utlösare för felfrekvens, upptäckt av offline-agenter; skickas till Slack, Discord, PagerDuty, Telegram, e-post
- **Approvals**: Spärra destruktiva raderingar, force pushes, databasändringar, sudo, paketinstallationer, nätverksanrop bakom ett godkännande med ett klick

## Skärmdumpar

### 🧠 Brain: Live händelseström för agenten
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview: Tokenanvändning och sessionssammanfattning
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow: Realtidsflöde för verktygsanrop
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens: Kostnadsuppdelning per modell och session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory: Filbläddrare för arbetsytan
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security: Säkerhetsstatus och granskningslogg
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts: Budgettak, utlösare för felfrekvens, webhooks till Slack / Discord / PagerDuty / E-post
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals: Spärra riskfyllda verktygsanrop bakom manuellt godkännande; policybaserade skyddsregler
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blockering före körning för Claude Code**: ett kommando installerar en
PreToolUse-hook som pausar matchande verktygsanrop *innan* de körs och väntar
på ditt beslut (ett tryck från din telefon med
[cloud-push-notiser](https://app.clawmetry.com/push) aktiverat):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Ett avslag blockerar bara det specifika verktygsanropet: agenten behåller
sin session och kan försöka en annan metod. Att godkänna från telefonen
hoppar över Claude Codes egen behörighetsprompt (du har redan svarat).
Ej matchade verktyg kostar ~40 ms och faller igenom till Claude Codes
normala behörighetsflöde. Du får också en push-notis till telefonen när
Claude Code själv väntar på dig (`permission_prompt` / `idle_prompt`-notiser).

## Installation

**Enradare (rekommenderas):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Från källkod:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2-frontendutveckling

v2 React-appen finns i `frontend/` och serveras på `/v2` när Flask-servern
startas med v2 aktiverat.

Använd två terminaler under utveckling:

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

Öppna `http://localhost:5173/v2/`. Vite skickar `/api`-förfrågningar vidare
till `http://localhost:8900`, så React-appen kan prata med den lokala
Flask-servern utan extra CORS-konfiguration.

För att bygga paketet som levereras med Python-paketet:

```bash
cd frontend
npm run build
```

Produktionspaketet skrivs till `clawmetry/static/v2/dist/`.

## Kompatibilitet för körmiljöer/agenter

ClawMetry observerar många AI-agentkörmiljöer, inte bara OpenClaw. Varje körmiljö utöver OpenClaw levereras med en dedikerad läsaradapter som översätter dess ursprungliga sessionsformat till ClawMetrys enhetliga format; demonen matar in dem i samma DuckDB-lager plus molnögonblicksbild, taggade med körmiljön, och fliken Session replay visar en **körmiljöväxlare** när fler än en finns. Se [`docs/compatibility.md`](docs/compatibility.md) för den fullständiga matrisen plus en guide för att lägga till körmiljöer, och [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) för grundintroduktionen till OpenClaw-familjen.

| Runtime / Agent | Status | Notes |
|---|---|---|
| **OpenClaw** | Inbyggd | Referenskörmiljö, upptäcks automatiskt |
| **PicoClaw** | Betaadapter | Platt `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transkript, modell, verktygsanrop. |
| **NanoClaw** | Betaadapter | SQLite per session (`data/v2-sessions`). Transkript + antal meddelanden. |
| **Hermes** | Betaadapter | SQLite `~/.hermes/state.db`. Transkript, modell, tokens/kostnad. |
| **Claude Code** | Betaadapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkript, modell, verktygsanrop + tankeprocess, tokenanvändning. |
| **Codex** | Betaadapter | Rollout-JSONL `~/.codex/sessions/...`. Transkript, modell, verktygsanrop, tokenanvändning. |
| **Cursor** | Betaadapter | SQLite `state.vscdb`. Chatt-/composer-transkript, modell. |
| **Aider** | Betaadapter | `.aider.chat.history.md` per projekt. Transkript, modell, antal tokens. |
| **Goose** | Betaadapter | SQLite `~/.local/share/goose`. Transkript, modell, verktygsanrop, totalt antal tokens. |
| **opencode** | Betaadapter | SQLite `~/.local/share/opencode`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **Qwen Code** | Betaadapter | JSONL `~/.qwen/projects/.../chats`. Transkript, modell, verktygsanrop, tokenanvändning. |
| **Pi** | Betaadapter | JSONL `~/.pi/agent/sessions`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **Deep Agents** | Betaadapter | SQLite `~/.deepagents/.state/sessions.db`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **n8n** | Betaadapter | SQLite `~/.n8n/database.sqlite`. Arbetsflödeskörningar, nodkörningar, AI Agent-prompter, modell + tokens där n8n registrerar dem. |

"Betaadapter" betyder att ClawMetry levererar en läsare för den körmiljöns verkliga format på disk, var och en byggd och verifierad mot en riktig installation på en riktig maskin (se `tests/fixtures/runtimes/<rt>/`). Adaptrarna är skrivskyddade; var och en är ärlig om vad dess körmiljö faktiskt lagrar (t.ex. skriver PicoClaw/NanoClaw/Cursor inte tokenkostnad till disk). När flera körmiljöer körs på en nod avgränsar körmiljöväxlaren sessionsvyn till en, för en ren fördjupning.

## Spåra vilken SDK-agent som helst: kostnadsattribuering utanför loopen

Alla körmiljöer ovan skriver sessioner till disk. Din egen **produktionsagent**, den du byggde med OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B eller en enkel `httpx`-loop, gör inte det. ClawMetrys interceptor utan konfiguration fångar ändå dess LLM-anrop (kostnad, tokens, latens, fel) genom att monkey-patcha `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (eller miljövariabeln `CLAWMETRY_SOURCE=support-agent`) taggar varje anrop med en **namngiven källa**, så att varje produkt du kör visas som en egen förstklassig, kostnadsattribuerbar rad i instrumentpanelens kort **🔌 Out-loop sources** på Overview: anrop, leverantörer, latens, felfrekvens per agent. Ingen källa angiven? Anropen spåras ändå; kortet förblir bara dolt.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Detta är samma datalager som körmiljöadaptrarna matar (DuckDB → molnögonblicksbild), så out-loop-källor synkroniseras till molninstrumentpanelen precis som allt annat, E2E-krypterat.

## OpenTelemetry: leverantörsneutralt, skicka dina spårningar vart som helst

ClawMetry pratar **OpenTelemetry** i båda riktningarna, med hjälp av **GenAI:s semantiska konventioner**, så att dina agentspårningar aldrig blir låsta till ett enda verktyg.

**Exportera** varje session, LLM-anrop, verktyg, subagenter, tokens, kostnad, som OTLP/HTTP GenAI-spans till valfri insamlare (Datadog, Grafana, Honeycomb eller din egen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Autentiseringshuvuden och pollningsintervall är valfria miljövariabler:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Inmatning**: den inbyggda OTLP-mottagaren tar emot spårningar och mätvärden från vad som helst annat på `/v1/traces` och `/v1/metrics` (`pip install clawmetry[otel]` för protobuf-inmatning).

Du får ClawMetrys instrumentpanel utan konfiguration och lokal-först **och** dina data i vilken backend ditt team än redan använder, ingen inlåsning, ingen andra agent att installera.

## Konfiguration

De flesta behöver ingen konfiguration alls. ClawMetry upptäcker automatiskt din arbetsyta, loggar, sessioner och cron-jobb.

Om du ändå behöver anpassa:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Alla alternativ: `clawmetry --help`

## Kanaler som stöds

ClawMetry visar live-aktivitet för varje OpenClaw-kanal du har konfigurerat. Endast kanaler som faktiskt är inställda i din `openclaw.json` visas i Flow-diagrammet; okonfigurerade kanaler döljs automatiskt.

Klicka på valfri kanalnod i Flow för att se en live chattbubble-vy med antal inkommande/utgående meddelanden.

| Kanal | Status | Live-popup | Anteckningar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Fullständig | ✅ | Meddelanden, statistik, uppdatering var 10:e sekund |
| 💬 **iMessage** | ✅ Fullständig | ✅ | Läser `~/Library/Messages/chat.db` direkt |
| 💚 **WhatsApp** | ✅ Fullständig | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Fullständig | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Fullständig | ✅ | Upptäckt av gilden + kanal |
| 🟪 **Slack** | ✅ Fullständig | ✅ | Upptäckt av arbetsyta + kanal |
| 🌐 **Webchat** | ✅ Fullständig | ✅ | Inbyggda sessioner i webbgränssnittet |
| 📡 **IRC** | ✅ Fullständig | ✅ | Bubble-gränssnitt i terminalstil |
| 🍏 **BlueBubbles** | ✅ Fullständig | ✅ | iMessage via BlueBubbles REST-API |
| 🔵 **Google Chat** | ✅ Fullständig | ✅ | Via webhooks i Chat API |
| 🟣 **MS Teams** | ✅ Fullständig | ✅ | Via Teams-bot-plugin |
| 🔷 **Mattermost** | ✅ Fullständig | ✅ | Självhostad teamchatt |
| 🟩 **Matrix** | ✅ Fullständig | ✅ | Decentraliserad, stöd för E2EE |
| 🟢 **LINE** | ✅ Fullständig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Fullständig | ✅ | Decentraliserade NIP-04-DM |
| 🟣 **Twitch** | ✅ Fullständig | ✅ | Chatt via IRC-anslutning |
| 🔷 **Feishu/Lark** | ✅ Fullständig | ✅ | Händelseprenumeration via WebSocket |
| 🔵 **Zalo** | ✅ Fullständig | ✅ | Zalo Bot API |

> **Automatisk upptäckt:** ClawMetry läser din `~/.openclaw/openclaw.json` och renderar bara de kanaler du faktiskt har konfigurerat. Ingen manuell installation krävs.

## Docker-distribution

Vill du köra ClawMetry i en container? Inga problem! 🐳

**Snabbstart med Docker:**

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

**Exempel med Docker Compose:**

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

> **Obs:** När du kör i Docker, montera agentens data- och loggkataloger (t.ex. `~/.openclaw`, `~/.claude`, `~/.codex`) så att ClawMetry kan upptäcka din konfiguration automatiskt.

## Krav

- Python 3.8+
- Flask (installeras automatiskt via pip)
- En AI-agentkörmiljö på samma maskin: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents eller n8n (eller monterade volymer för Docker)
- Linux eller macOS

## Stöd för NemoClaw/OpenShell

ClawMetry upptäcker automatiskt [NemoClaw](https://github.com/NVIDIA/NemoClaw), NVIDIAs säkerhetsomslag för företag runt OpenClaw som kör agenter inuti sandlådade OpenShell-containrar.

I de flesta fall behövs ingen extra konfiguration. Synkroniseringsdemonen upptäcker automatiskt sessionsfiler oavsett om de finns i `~/.openclaw/` på värden eller inuti en OpenShell-container.

### Så här fungerar det

ClawMetry upptäcker NemoClaw på två sätt:

1. **Binärupptäckt**: kontrollerar om CLI:t `nemoclaw` finns och kör `nemoclaw status` för att hämta sandlådeinformation
2. **Containerupptäckt**: söker igenom körande Docker-containrar efter avbildningarna `openshell`, `nemoclaw` eller `ghcr.io/nvidia/`, och läser sedan sessioner via monterade volymer eller `docker cp`

Sessionsfiler som synkroniseras från NemoClaw-containrar taggas med metadatan `runtime=nemoclaw` och `container_id` i molninstrumentpanelen, så att du snabbt kan skilja dem från vanliga OpenClaw-sessioner.

### Rekommenderad konfiguration: synkroniseringsdemon på VÄRDEN

För bästa upplevelse bör du köra ClawMetrys synkroniseringsdemon på **värdmaskinen** (inte inuti sandlådan). Detta undviker NemoClaws nätverkspolicybegränsningar.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Synkroniseringsdemonen hittar automatiskt sessioner inuti alla körande OpenShell-containrar.

### Valfritt: explicit sandlådenamn

Om automatisk upptäckt inte fungerar, peka ClawMetry mot rätt sandlåda:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Köra inuti sandlådan (avancerat)

Om du måste köra synkroniseringsdemonen **inuti** OpenShell-sandlådan, lägg till den här utgående regeln (egress) i din NemoClaw-nätverkspolicy så att den kan nå ClawMetrys inmatnings-API:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Tillämpa med:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Portar och slutpunkter

| Slutpunkt | Port | Protokoll | Krävs |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Ja (synkroniseringsdemon → moln) |
| `localhost:8900` | 8900 | HTTP | Ja (lokalt instrumentpanelsgränssnitt) |
| Docker-socket (`/var/run/docker.sock`) | - | Unix-socket | För upptäckt av containersessioner |

Synkroniseringsdemonen gör bara utgående HTTPS-anrop till `ingest.clawmetry.com`. Inga inkommande portar krävs.

---

## Molndistribution

Se **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** för SSH-tunnlar, omvänd proxy och Docker.

## Testning

Det här projektet testas med BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry skickar en enda anonym "första körning"-ping till
`https://app.clawmetry.com/api/install` första gången du kör CLI:t
`clawmetry` på en ny maskin. Vi använder detta för att räkna installationer
(det enda marknadsföringsmått vi har för ett OSS-projekt) och för att ta
reda på vilka agentramverk våra användare har installerat.

**Exakt en POST per installation**, som innehåller:

| Fält | Exempel | Varför |
|---|---|---|
| `install_id` | slumpmässig UUID som lagras i `~/.clawmetry/install_id` | avdubblering; kopplas inte till din e-post eller api_key |
| `version` | `0.12.167` | vilka versioner som är i bruk |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioriteringar för plattformsstöd |
| `python` | `3.11.15` | supportmatris för Python-versioner |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | vilka agenter vi bör integrera med härnäst |
| `is_ci` / `ci_provider` | `true` / `github_actions` | skilja mänskliga installationer från CI-brus |

**Det vi INTE skickar**: IP (molnet härleder landskoden server-side från
förfrågan och kasserar sedan IP-adressen), värdnamn, användarnamn, sökväg
till arbetsytan, filinnehåll, din api_key, din e-post, eller något som är
PII eller arbetsytespecifikt. Nyttolasten som skickas kan granskas i
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Välja bort** (valfri av dessa inaktiverar det permanent):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ett nätverksfel här blockerar aldrig `clawmetry` från att köras: pingen
skickas iväg utan att vänta på svar (fire-and-forget) i en demontråd med
en timeout på 3 sekunder.

## Stjärnhistorik

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licens

MIT

---

<p align="center">
  <strong>🦞 Se din agent tänka</strong><br>
  <sub>Byggd av <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · En del av <a href="https://github.com/openclaw/openclaw">OpenClaw</a>-ekosystemet</sub>
</p>
