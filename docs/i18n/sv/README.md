<!-- i18n-src:02b789586c7d -->
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

ClawMetry började som observabilitet för OpenClaw och mäter nu **hela din agentflotta** i en instrumentpanel, med automatisk upptäckt av varje körmiljö på din maskin:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw och NemoClaw är gratis i det öppna källkodsprogrammet; de övriga körmiljöerna aktiveras med ClawMetry Cloud eller en självhostad Pro-licens. Byt körmiljö från sidhuvudet så anpassas varje flik, kostnad, tokens, verktyg, spårningar, till den körmiljön. Se **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** för exakt uppdelning mellan gratis/betalt, nivåmatris, formen på `/api/entitlement` och `clawmetry license`-CLI:t.

## Vad du får

- **Flow** — Levande animerat diagram som visar meddelanden flöda genom kanaler, hjärna, verktyg och tillbaka
- **Overview** — Hälsokontroller, aktivitetsvärmekarta, sessionsräknare, modellinformation
- **Usage** — Spårning av tokens och kostnad med daglig/vecko/månadsvis uppdelning
- **Sessions** — Aktiva agentsessioner med modell, tokens, senaste aktivitet
- **Crons** — Schemalagda jobb med status, nästa körning, varaktighet
- **Logs** — Färgkodad realtidsloggström
- **Memory** — Bläddra i SOUL.md, MEMORY.md, AGENTS.md, dagliga anteckningar
- **Transcripts** — Chattbubbel-gränssnitt för att läsa sessionshistorik
- **Alerts** — Budgettak, felfrekvensutlösare, upptäckt av offline-agenter; dirigerar till Slack, Discord, PagerDuty, Telegram, e-post
- **Approvals** — Blockera destruktiva raderingar, force push, databasmutationer, sudo, paketinstallationer, nätverksanrop bakom ett klick för godkännande

## Skärmdumpar

### 🧠 Brain — Live agenthändelseström
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Tokenanvändning och sessionssammanfattning
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Realtidsflöde av verktygsanrop
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Kostnadsuppdelning per modell och session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Filbläddrare för arbetsytan
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Säkerhetsläge och granskningslogg
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budgettak, felfrekvensutlösare, webhooks till Slack / Discord / PagerDuty / e-post
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blockera riskfyllda verktygsanrop bakom manuellt godkännande; policybaserade skyddsregler
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blockering före körning för Claude Code** — ett kommando installerar en
PreToolUse-hook som pausar matchande verktygsanrop *innan* de körs och väntar
på ditt beslut (ett tryck från din telefon med
[cloud push-notiser](https://app.clawmetry.com/push) aktiverat):

```bash
clawmetry hooks install     # skriver ~/.claude/settings.json (idempotent)
clawmetry hooks status      # vad som är kopplat + hur många policyer som är aktiva
clawmetry hooks uninstall   # tar bara bort ClawMetrys egna poster
```

Ett nekande blockerar bara det enskilda verktygsanropet, agenten behåller sin session och kan
prova ett annat tillvägagångssätt. Att godkänna från din telefon hoppar över Claude Codes egen
behörighetsprompt (du har redan svarat). Icke-matchande verktyg kostar ~40 ms och
faller igenom till Claude Codes normala behörighetsflöde. Du får också en telefonpush när Claude Code självt
väntar på dig (`permission_prompt`- / `idle_prompt`-notiser).

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

v2 React-appen finns i `frontend/` och serveras på `/v2` när Flask-
servern startas med v2 aktiverat.

Använd två terminaler under utveckling:

```bash
# Terminal 1: Flask API/server på :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev-server på :5173
cd frontend
nvm use
npm ci
npm run dev
```

Öppna `http://localhost:5173/v2/`. Vite vidarebefordrar `/api`-anrop till
`http://localhost:8900`, så React-appen kan kommunicera med den lokala Flask-servern
utan extra CORS-konfiguration.

För att bygga paketet som levereras med Python-paketet:

```bash
cd frontend
npm run build
```

Produktionspaketet skrivs till `clawmetry/static/v2/dist/`.

## Kompatibilitet med körmiljöer/agenter

ClawMetry observerar många AI-agentkörmiljöer, inte bara OpenClaw. Varje körmiljö utöver OpenClaw levereras med en dedikerad läsaradapter som översätter dess ursprungliga sessionsformat till ClawMetrys enhetliga format; daemonen tar in dem i samma DuckDB-lager + molnögonblicksbild, taggade med körmiljön, och Session replay-fliken visar en **körmiljöväxlare** när fler än en finns. Se [`docs/compatibility.md`](docs/compatibility.md) för hela matrisen + en guide för att lägga till körmiljöer, och [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) för en introduktion till OpenClaw-familjen.

| Körmiljö/Agent | Status | Anteckningar |
|---|---|---|
| **OpenClaw** | Inbyggd | Referenskörmiljö, upptäcks automatiskt |
| **PicoClaw** | Betaadapter | Platt `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Utskrifter, modell, verktygsanrop. |
| **NanoClaw** | Betaadapter | SQLite per session (`data/v2-sessions`). Utskrifter + meddelanderäkningar. |
| **Hermes** | Betaadapter | SQLite `~/.hermes/state.db`. Utskrifter, modell, tokens/kostnad. |
| **Claude Code** | Betaadapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Utskrifter, modell, verktygsanrop + tankeprocess, tokenanvändning. |
| **Codex** | Betaadapter | Rollout-JSONL `~/.codex/sessions/...`. Utskrifter, modell, verktygsanrop, tokenanvändning. |
| **Cursor** | Betaadapter | SQLite `state.vscdb`. Chatt-/komposer-utskrifter, modell. |
| **Aider** | Betaadapter | `.aider.chat.history.md` per projekt. Utskrifter, modell, tokenräkningar. |
| **Goose** | Betaadapter | SQLite `~/.local/share/goose`. Utskrifter, modell, verktygsanrop, tokentotaler. |
| **opencode** | Betaadapter | SQLite `~/.local/share/opencode`. Utskrifter, modell, verktygsanrop, tokens + kostnad. |
| **Qwen Code** | Betaadapter | JSONL `~/.qwen/projects/.../chats`. Utskrifter, modell, verktygsanrop, tokenanvändning. |
| **Pi** | Betaadapter | JSONL `~/.pi/agent/sessions`. Utskrifter, modell, verktygsanrop, tokens + kostnad. |
| **Deep Agents** | Betaadapter | SQLite `~/.deepagents/.state/sessions.db`. Utskrifter, modell, verktygsanrop, tokens + kostnad. |
| **n8n** | Betaadapter | SQLite `~/.n8n/database.sqlite`. Arbetsflödeskörningar, nodkörningar, AI Agent-promptar, modell + tokens där n8n registrerar dem. |
| **Antigravity** | Betaadapter | Hjärn-JSONL under `~/.gemini/<flavor>/brain/`. Konversationer, verktygssteg, tankeprocess, per-generering Gemini-tokenuppdelning + kostnad, förbrukning från bakgrundsgenerering. |

"Betaadapter" betyder att ClawMetry levererar en läsare för körmiljöns faktiska format på disk, var och en byggd + verifierad mot en riktig installation på en riktig maskin (se `tests/fixtures/runtimes/<rt>/`). Adaptrarna är skrivskyddade; var och en är ärlig om vad körmiljön faktiskt lagrar (t.ex. skriver PicoClaw/NanoClaw/Cursor inte tokenkostnad till disk). När flera körmiljöer körs på en nod avgränsar körmiljöväxlaren sessionsvyn till en för en ren fördjupning.

## Spåra vilken SDK-agent som helst — attribuering av kostnad utanför loopen

Körmiljöerna ovan skriver alla sessioner till disk. Din egen **produktionsagent**, den du byggde på OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B eller en vanlig `httpx`-loop, gör inte det. ClawMetrys interceptor utan konfiguration fångar ändå dess LLM-anrop (kostnad, tokens, latens, fel) genom att apa fram (monkey-patch) `httpx`/`requests`:

```python
import clawmetry.track            # aktivera interceptorn
clawmetry.track.set_source("support-agent")   # namnge denna produkt

# ...din agent körs som vanligt; varje LLM-anrop spåras och attribueras nu.
```

`set_source()` (eller miljövariabeln `CLAWMETRY_SOURCE=support-agent`) taggar varje anrop med en **namngiven källa**, så varje produkt du kör visas som sin egen förstklassiga, kostnadsattribuerbara rad i instrumentpanelens kort **🔌 Källor utanför loopen** under Overview, anrop, leverantörer, latens, felfrekvens per agent. Ingen källa angiven? Anropen spåras ändå; kortet förblir bara dolt.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Detta är samma datalager som körmiljöadaptrarna matar (DuckDB → molnögonblicksbild), så källor utanför loopen synkroniseras till molninstrumentpanelen precis som allt annat, E2E-krypterat.

## OpenTelemetry — leverantörsneutralt, skicka dina spårningar vart som helst

ClawMetry talar **OpenTelemetry** i båda riktningarna, med **GenAI:s semantiska konventioner**, så att dina agentspårningar aldrig blir låsta till ett enda verktyg.

**Exportera** varje session, LLM-anrop, verktyg, underagenter, tokens, kostnad, som OTLP/HTTP GenAI-spann till valfri insamlare (Datadog, Grafana, Honeycomb eller din egen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# motsvarande:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auktoriseringsrubriker och pollningsintervall är valfria miljövariabler:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP-rubriker
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # sekunder (standard 60)
```

**Inta** — den inbyggda OTLP-mottagaren accepterar spårningar och mätvärden från vad som helst annat på `/v1/traces` och `/v1/metrics` (`pip install clawmetry[otel]` för protobuf-intag).

Du får den konfigurationsfria, lokalt först-instrumentpanelen från ClawMetry **och** din data i vilken backend ditt team redan kör, ingen inlåsning, ingen andra agent att installera.

## Konfiguration

De flesta behöver ingen konfiguration alls. ClawMetry upptäcker automatiskt din arbetsyta, loggar, sessioner och cron-jobb.

Om du behöver anpassa:

```bash
clawmetry --port 9000              # Anpassad port (standard: 8900)
clawmetry --host 127.0.0.1         # Bind endast till localhost
clawmetry --workspace ~/mybot      # Anpassad sökväg till arbetsyta
clawmetry --name "Alice"           # Ditt namn i Flow-visualiseringen
```

Alla alternativ: `clawmetry --help`

## Kanaler som stöds

ClawMetry visar live-aktivitet för varje OpenClaw-kanal du har konfigurerat. Endast kanaler som faktiskt är konfigurerade i din `openclaw.json` visas i Flow-diagrammet, okonfigurerade döljs automatiskt.

Klicka på valfri kanalnod i Flow för att se en live-chattbubbelvy med räknare för inkommande/utgående meddelanden.

| Kanal | Status | Live-popup | Anteckningar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Fullt | ✅ | Meddelanden, statistik, uppdatering var 10:e sekund |
| 💬 **iMessage** | ✅ Fullt | ✅ | Läser `~/Library/Messages/chat.db` direkt |
| 💚 **WhatsApp** | ✅ Fullt | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Fullt | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Fullt | ✅ | Upptäckt av gille + kanal |
| 🟪 **Slack** | ✅ Fullt | ✅ | Upptäckt av arbetsyta + kanal |
| 🌐 **Webchat** | ✅ Fullt | ✅ | Inbyggda webbgränssnittssessioner |
| 📡 **IRC** | ✅ Fullt | ✅ | Terminalliknande bubbelgränssnitt |
| 🍏 **BlueBubbles** | ✅ Fullt | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Fullt | ✅ | Via Chat API-webhooks |
| 🟣 **MS Teams** | ✅ Fullt | ✅ | Via Teams-bottillägg |
| 🔷 **Mattermost** | ✅ Fullt | ✅ | Självhostad teamchatt |
| 🟩 **Matrix** | ✅ Fullt | ✅ | Decentraliserad, stöd för E2EE |
| 🟢 **LINE** | ✅ Fullt | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Fullt | ✅ | Decentraliserade NIP-04-DM |
| 🟣 **Twitch** | ✅ Fullt | ✅ | Chatt via IRC-anslutning |
| 🔷 **Feishu/Lark** | ✅ Fullt | ✅ | WebSocket-händelseprenumeration |
| 🔵 **Zalo** | ✅ Fullt | ✅ | Zalo Bot API |

> **Automatisk upptäckt:** ClawMetry läser din `~/.openclaw/openclaw.json` och renderar bara de kanaler du faktiskt har konfigurerat. Ingen manuell konfiguration krävs.

## Docker-driftsättning

Vill du köra ClawMetry i en container? Inga problem! 🐳

**Snabbstart med Docker:**

```bash
# Bygg avbildningen
docker build -t clawmetry .

# Kör med standardinställningar
docker run -p 8900:8900 clawmetry

# Eller montera din agents datamapp (visas: OpenClaws ~/.openclaw)
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

> **Obs:** När du kör i Docker, montera din agents data- + loggmappar (t.ex. `~/.openclaw`, `~/.claude`, `~/.codex`) så att ClawMetry kan upptäcka din konfiguration automatiskt.

## Krav

- Python 3.8+
- Flask (installeras automatiskt via pip)
- En AI-agentkörmiljö på samma maskin: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n eller Antigravity (eller monterade volymer för Docker)
- Linux eller macOS

## Stöd för NemoClaw / OpenShell

ClawMetry upptäcker automatiskt [NemoClaw](https://github.com/NVIDIA/NemoClaw), NVIDIAs säkerhetsomslag för företag runt OpenClaw som kör agenter i sandlådade OpenShell-containrar.

Ingen extra konfiguration behövs i de flesta fall. Synkroniseringsdaemonen upptäcker automatiskt sessionsfiler oavsett om de finns i `~/.openclaw/` på värden eller inuti en OpenShell-container.

### Hur det fungerar

ClawMetry upptäcker NemoClaw på två sätt:

1. **Binärupptäckt** — kontrollerar om `nemoclaw`-CLI:t finns och kör `nemoclaw status` för att hämta sandlådeinformation
2. **Containerupptäckt** — skannar körande Docker-containrar efter `openshell`, `nemoclaw` eller `ghcr.io/nvidia/`-avbildningar, och läser sedan sessioner via volymmonteringar eller `docker cp`

Sessionsfiler synkroniserade från NemoClaw-containrar taggas med `runtime=nemoclaw` och `container_id`-metadata i molninstrumentpanelen, så att du enkelt kan skilja dem från vanliga OpenClaw-sessioner.

### Rekommenderad konfiguration: synkroniseringsdaemon på VÄRDEN

För bästa upplevelse, kör ClawMetrys synkroniseringsdaemon på **värdmaskinen** (inte inuti sandlådan). Detta undviker NemoClaws nätverkspolicybegränsningar.

```bash
# På värden (utanför sandlådan)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Synkroniseringsdaemonen hittar automatiskt sessioner inuti alla körande OpenShell-containrar.

### Valfritt: uttryckligt sandlådenamn

Om automatisk upptäckt inte fungerar, peka ClawMetry på rätt sandlåda:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Köra inuti sandlådan (avancerat)

Om du måste köra synkroniseringsdaemonen **inuti** OpenShell-sandlådan, lägg till denna utgående regel i din NemoClaw-nätverkspolicy så att den kan nå ClawMetrys intags-API:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Ja (synkroniseringsdaemon → moln) |
| `localhost:8900` | 8900 | HTTP | Ja (lokal instrumentpanel) |
| Docker-uttag (`/var/run/docker.sock`) | — | Unix-uttag | För upptäckt av containersessioner |

Synkroniseringsdaemonen gör bara utgående HTTPS-anrop till `ingest.clawmetry.com`. Inga inkommande portar krävs.

---

## Molndriftsättning

Se **[guiden för molntestning](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** för SSH-tunnlar, omvänd proxy och Docker.

## Testning

Detta projekt testas med BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry skickar anonyma pingar för installationslivscykeln till
`https://app.clawmetry.com/api/install`: en `install`-ping första
gången du kör `clawmetry`-CLI:t på en ny maskin, en `update`-ping
första körningen efter uppgradering till en ny version, och en `onboarded`-
ping när du slutför onboarding-valet i instrumentpanelen. Vi använder detta
för att räkna faktiska installationer (rå PyPI-nedladdningsstatistik är ~98 % speglingar, CI
och automatiska omnedladdningar) och för att lära oss vilka agentramverk och
versioner som faktiskt används.

**Högst en POST per livscykelhändelse och version**, som innehåller:

| Fält | Exempel | Varför |
|---|---|---|
| `install_id` | slumpmässigt UUID lagrat på `~/.clawmetry/install_id` | avduplicering; anonymt tills du uttryckligen ansluter Cloud-synkronisering (den autentiserade daemonens hjärtslag bär då med sig detta, vilket kopplar installationen till ditt konto) |
| `event` | `install` / `update` / `onboarded` | ny installation kontra uppgradering av en befintlig |
| `version` | `0.12.167` | vilka versioner som är i bruk |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioriteringar för plattformsstöd |
| `python` | `3.11.15` | supportmatris för Python-version |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | vilka agenter vi bör integrera med härnäst |
| `is_ci` / `ci_provider` | `true` / `github_actions` | skilja mänskliga installationer från CI-brus |

**Vad vi INTE skickar**: IP (molnet härleder landskoden serversidan
från förfrågan och kasserar sedan IP:n), värdnamn, användarnamn, sökväg till arbetsyta, filinnehåll, din api_key, din e-post, något personuppgiftskänsligt eller
arbetsytespecifikt. Nyttolasten som skickas kan granskas i
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Välj bort** (vilken som helst av dessa inaktiverar det permanent):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per skal
export DO_NOT_TRACK=1                          # W3C-standard för verktygsöverskridande bruk
touch ~/.clawmetry/notelemetry                 # permanent filmarkör
```

Ett nätverksfel här blockerar aldrig `clawmetry` från att köra, pingen
är skicka-och-glöm på en daemon-tråd med 3 sekunders timeout.

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
  <sub>Byggd av <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Del av <a href="https://github.com/openclaw/openclaw">OpenClaw</a>-ekosystemet</sub>
</p>
