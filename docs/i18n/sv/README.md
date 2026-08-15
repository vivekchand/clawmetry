<!-- i18n-src:c422fb7dd0da -->
> Svenska translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Se din agent tänka.** Realtidsövervakning för **20 AI-agentmiljöer**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex och 16 till. En instrumentpanel för hela din agentflotta.

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Ingen konfiguration. Upptäcker allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900** och du är klar.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Fungerar med 20 agentmiljöer

ClawMetry började som observability för OpenClaw och mäter nu **hela din agentflotta** i en instrumentpanel, med automatisk detektering av varje miljö på din maskin:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw och NemoClaw är gratis i open source-appen; de övriga miljöerna aktiveras med ClawMetry Cloud eller en självhostad Pro-licens. Byt miljö från sidhuvudet, så omfattas varje flik, kostnad, tokens, verktyg, spårningar, om den valda miljön. Se **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** för den exakta gratis-/betaluppdelningen, nivåmatrisen, formen på `/api/entitlement` och CLI-kommandot `clawmetry license`.

## Vad du får

- **Flow** — Levande animerat diagram som visar meddelanden flöda genom kanaler, hjärna, verktyg och tillbaka
- **Overview** — Hälsokontroller, aktivitetsvärmekarta, sessionsantal, modellinformation
- **Usage** — Spårning av tokens och kostnad med dagliga/veckovisa/månatliga uppdelningar
- **Sessions** — Aktiva agentsessioner med modell, tokens, senaste aktivitet
- **Crons** — Schemalagda jobb med status, nästa körning, varaktighet
- **Logs** — Färgkodad realtidslogg-strömning
- **Memory** — Bläddra i SOUL.md, MEMORY.md, AGENTS.md, dagliga anteckningar
- **Transcripts** — Chattbubble-gränssnitt för att läsa sessionshistorik
- **Alerts** — Budgettak, felfrekvens-utlösare, agent-offline-detektering; dirigeras till Slack, Discord, PagerDuty, Telegram, e-post
- **Approvals** — Blockera destruktiva raderingar, force pushes, DB-mutationer, sudo, paketinstallationer, nätverksanrop bakom en enda klicksignering

## Skärmdumpar

### 🧠 Brain — Live-agentens händelseström
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

### 🚨 Alerts — Budgettak, felfrekvens-utlösare, webhooks till Slack / Discord / PagerDuty / e-post
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blockera riskfyllda verktygsanrop bakom manuell signering; policybaserade skyddsregler
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blockering före körning för Claude Code** — ett kommando installerar en
PreToolUse-hook som pausar matchande verktygsanrop *innan* de körs och väntar
på ditt beslut (ett tryck från din telefon med
[molnpushnotiser](https://app.clawmetry.com/push) aktiverade):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Ett avslag blockerar bara det enskilda verktygsanropet, agenten behåller sin session och kan
prova ett annat tillvägagångssätt. Att godkänna på telefonen hoppar över Claude Codes egen
behörighetsprompt (du har redan svarat). Icke-matchande verktyg kostar ~40 ms och
faller igenom till Claude Codes normala behörighetsflöde. Du får också en telefonpush när Claude Code självt väntar på dig (`permission_prompt`- /
`idle_prompt`-notiser).

## Installation

**En rad (rekommenderas):**
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

Öppna `http://localhost:5173/v2/`. Vite proxar `/api`-anrop till
`http://localhost:8900`, så React-appen kan kommunicera med den lokala Flask-servern
utan extra CORS-konfiguration.

För att bygga den bundle som levereras med Python-paketet:

```bash
cd frontend
npm run build
```

Produktionsbundlen skrivs till `clawmetry/static/v2/dist/`.

## Kompatibilitet med miljöer/agenter

ClawMetry observerar många AI-agentmiljöer, inte bara OpenClaw. Varje miljö utöver OpenClaw levereras med en dedikerad läsaradapter som översätter dess ursprungliga sessionsformat till ClawMetrys enhetliga format; daemonen matar in dem i samma DuckDB-lager + molninstantavbild, taggade med miljön, och fliken Session replay visar en **miljöväxlare** när fler än en finns. Se [`docs/compatibility.md`](docs/compatibility.md) för den fullständiga matrisen + en guide till hur man lägger till miljöer, och [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) för en introduktion till OpenClaw-familjen.

Kör du [Perplexitys numbat](https://github.com/perplexityai/numbat) agentsäkerhetsverktyg? ClawMetry tar emot dess resultat och tillämpningsbeslut direkt ur lådan, se [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Miljö/agent | Status | Anteckningar |
|---|---|---|
| **OpenClaw** | Inbyggd | Referensmiljö, upptäcks automatiskt |
| **PicoClaw** | Beta-adapter | Platt `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transkript, modell, verktygsanrop. |
| **NanoClaw** | Beta-adapter | SQLite per session (`data/v2-sessions`). Transkript + meddelandeantal. |
| **Hermes** | Beta-adapter | SQLite `~/.hermes/state.db`. Transkript, modell, tokens/kostnad. |
| **Claude Code** | Beta-adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkript, modell, verktygsanrop + tankeprocess, tokenanvändning. |
| **Codex** | Beta-adapter | Rollout-JSONL `~/.codex/sessions/...`. Transkript, modell, verktygsanrop, tokenanvändning. |
| **Cursor** | Beta-adapter | SQLite `state.vscdb`. Chatt-/composer-transkript, modell. |
| **Aider** | Beta-adapter | `.aider.chat.history.md` per projekt. Transkript, modell, tokenantal. |
| **Goose** | Beta-adapter | SQLite `~/.local/share/goose`. Transkript, modell, verktygsanrop, tokentotaler. |
| **opencode** | Beta-adapter | SQLite `~/.local/share/opencode`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **Qwen Code** | Beta-adapter | JSONL `~/.qwen/projects/.../chats`. Transkript, modell, verktygsanrop, tokenanvändning. |
| **Pi** | Beta-adapter | JSONL `~/.pi/agent/sessions`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **Deep Agents** | Beta-adapter | SQLite `~/.deepagents/.state/sessions.db`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **n8n** | Beta-adapter | SQLite `~/.n8n/database.sqlite`. Arbetsflödeskörningar, nodkörningar, AI Agent-prompter, modell + tokens där n8n registrerar dem. |
| **Antigravity** | Beta-adapter | Brain-JSONL under `~/.gemini/<flavor>/brain/`. Konversationer, verktygssteg, tankeprocess, per-generation Gemini-tokenuppdelning + kostnad, bakgrundsgenereringsförbrukning. |
| **GitHub Copilot** | Beta-adapter | Copilot CLI:s `events.jsonl` under `~/.copilot/session-state/` + `session-store.db`-liggaren för användning per anrop. Konversationer, verktygsanrop, modellroutning, cache-medveten tokenuppdelning, leverantörsfakturerad AI-kreditkostnad. |
| **Grok** | Beta-adapter | xAI Grok Build CLI (Rust-binär under `~/.grok/bin/grok`): global händelselogg `~/.grok/logs/unified.jsonl` + per session `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Konversationer, tokenuppdelning per tur, modellroutning, och CLI:ns utgående repo-nyttolast lagrad under `~/.grok/upload_queue/` så du kan se vad som lämnat din maskin. |

"Beta-adapter" innebär att ClawMetry levererar en läsare för den miljöns faktiska format på disk, var och en byggd + verifierad mot en riktig installation på en riktig maskin (se `tests/fixtures/runtimes/<rt>/`). Adaptrarna är skrivskyddade; var och en är ärlig om vad dess miljö faktiskt lagrar (t.ex. skriver PicoClaw/NanoClaw/Cursor inte tokenkostnad till disk). När flera miljöer körs på en nod avgränsar miljöväxlaren sessionsvyn till en för en ren djupdykning.

## Spåra vilken SDK-agent som helst, kostnadsattribuering utanför loopen

Miljöerna ovan skriver alla sessioner till disk. Din egen **produktionsagent** — den du byggde på OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, eller en vanlig `httpx`-loop — gör det inte. ClawMetrys konfigurationsfria interceptor fångar ändå dess LLM-anrop (kostnad, tokens, latens, fel) genom att monkey-patcha `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (eller miljövariabeln `CLAWMETRY_SOURCE=support-agent`) taggar varje anrop med en **namngiven källa**, så varje produkt du kör dyker upp som sin egen förstklassiga, kostnadsattribuerbara rad i instrumentpanelens kort **🔌 Out-loop sources** på Overview, anrop, leverantörer, latens, felfrekvens per agent. Ingen källa angiven? Anropen spåras ändå, kortet förblir bara dolt.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Detta är samma datalager som miljöadaptrarna matar (DuckDB → molninstantavbild), så out-loop-källor synkroniseras till molninstrumentpanelen precis som allt annat, ände-till-ände-krypterat.

## OpenTelemetry, leverantörsneutralt, skicka dina spårningar vart som helst

ClawMetry talar **OpenTelemetry** i båda riktningarna, med **GenAI-semantiska konventioner**, så dina agentspårningar blir aldrig inlåsta i ett enda verktyg.

**Exportera** varje session — LLM-anrop, verktyg, undersagenter, tokens, kostnad — som OTLP/HTTP GenAI-spans till valfri samlare (Datadog, Grafana, Honeycomb, eller din egen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Autentiseringshuvuden och pollintervall är valfria miljövariabler:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ta emot** — den inbyggda OTLP-mottagaren tar emot spårningar, loggar och mätvärden från vad som helst annat på `/v1/traces`, `/v1/logs` och `/v1/metrics`. Peka valfri OpenTelemetry-instrumenterad app mot den:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON-spårningar och loggar fungerar med en vanlig `pip install clawmetry`, inga tillägg krävs. Protobuf-mottagning (och OTLP/JSON-mätvärden) kräver `pip install clawmetry[otel]`. En app som anger sitt eget `service.name` visas som sin egen agent i miljöväxlaren, med sin kostnad och sina tokens.

Du får den konfigurationsfria, lokalt-först ClawMetry-instrumentpanelen **och** dina data i vilken backend ditt team redan kör, ingen inlåsning, ingen andra agent att installera.

## Konfiguration

De flesta behöver ingen konfiguration alls. ClawMetry upptäcker automatiskt din arbetsyta, loggar, sessioner och cron-jobb.

Om du behöver anpassa:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Alla alternativ: `clawmetry --help`

## Kanaler som stöds

ClawMetry visar live-aktivitet för varje OpenClaw-kanal du har konfigurerat. Endast kanaler som faktiskt är konfigurerade i din `openclaw.json` visas i Flow-diagrammet, okonfigurerade döljs automatiskt.

Klicka på valfri kanalnod i Flow för att se en live chattbubblevy med antal inkommande/utgående meddelanden.

| Kanal | Status | Live-popup | Anteckningar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Fullständig | ✅ | Meddelanden, statistik, 10 s uppdatering |
| 💬 **iMessage** | ✅ Fullständig | ✅ | Läser `~/Library/Messages/chat.db` direkt |
| 💚 **WhatsApp** | ✅ Fullständig | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Fullständig | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Fullständig | ✅ | Detektering av gilde + kanal |
| 🟪 **Slack** | ✅ Fullständig | ✅ | Detektering av arbetsyta + kanal |
| 🌐 **Webchat** | ✅ Fullständig | ✅ | Inbyggda webbgränssnitt-sessioner |
| 📡 **IRC** | ✅ Fullständig | ✅ | Terminalliknande bubbelgränssnitt |
| 🍏 **BlueBubbles** | ✅ Fullständig | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Fullständig | ✅ | Via Chat API-webhooks |
| 🟣 **MS Teams** | ✅ Fullständig | ✅ | Via Teams-bottillägg |
| 🔷 **Mattermost** | ✅ Fullständig | ✅ | Självhostad teamchatt |
| 🟩 **Matrix** | ✅ Fullständig | ✅ | Decentraliserad, stöd för E2EE |
| 🟢 **LINE** | ✅ Fullständig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Fullständig | ✅ | Decentraliserade NIP-04-DM |
| 🟣 **Twitch** | ✅ Fullständig | ✅ | Chatt via IRC-anslutning |
| 🔷 **Feishu/Lark** | ✅ Fullständig | ✅ | WebSocket-händelseprenumeration |
| 🔵 **Zalo** | ✅ Fullständig | ✅ | Zalo Bot API |

> **Automatisk detektering:** ClawMetry läser din `~/.openclaw/openclaw.json` och renderar bara de kanaler du faktiskt har konfigurerat. Ingen manuell konfiguration krävs.

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

**Docker Compose-exempel:**

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

> **Obs:** När du kör i Docker, montera din agents data- och loggkataloger (t.ex. `~/.openclaw`, `~/.claude`, `~/.codex`) så att ClawMetry kan upptäcka din konfiguration automatiskt.

## Krav

- Python 3.8+
- Flask (installeras automatiskt via pip)
- En AI-agentmiljö på samma maskin: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, eller QM (eller monterade volymer för Docker)
- Linux eller macOS

## NemoClaw/OpenShell-stöd

ClawMetry upptäcker automatiskt [NemoClaw](https://github.com/NVIDIA/NemoClaw), NVIDIAs säkerhetsomslag för företag runt OpenClaw som kör agenter inuti sandboxade OpenShell-containrar.

Ingen extra konfiguration behövs i de flesta fall. Sync-daemonen upptäcker automatiskt sessionsfiler oavsett om de finns i `~/.openclaw/` på värden eller inuti en OpenShell-container.

### Så fungerar det

ClawMetry upptäcker NemoClaw på två sätt:

1. **Binärdetektering** — kontrollerar om `nemoclaw`-CLI:t finns och kör `nemoclaw status` för att hämta sandboxinformation
2. **Containerdetektering** — skannar körande Docker-containrar efter `openshell`-, `nemoclaw`- eller `ghcr.io/nvidia/`-avbildningar, och läser sedan sessioner via volymmonteringar eller `docker cp`

Sessionsfiler synkroniserade från NemoClaw-containrar taggas med `runtime=nemoclaw` och `container_id`-metadata i molninstrumentpanelen, så du kan skilja dem från vanliga OpenClaw-sessioner med en blick.

### Rekommenderad konfiguration: sync-daemon på VÄRDEN

För bästa upplevelse, kör ClawMetrys sync-daemon på **värdmaskinen** (inte inuti sandboxen). Detta undviker NemoClaws nätverkspolicybegränsningar.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Sync-daemonen hittar automatiskt sessioner inuti alla körande OpenShell-containrar.

### Valfritt: uttryckligt sandboxnamn

Om automatisk detektering inte fungerar, peka ClawMetry mot rätt sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Att köra inuti sandboxen (avancerat)

Om du måste köra sync-daemonen **inuti** OpenShell-sandboxen, lägg till denna utgående regel i din NemoClaw-nätverkspolicy så att den kan nå ClawMetrys ingest-API:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Ja (sync-daemon → moln) |
| `localhost:8900` | 8900 | HTTP | Ja (lokal instrumentpanel-UI) |
| Docker-sockel (`/var/run/docker.sock`) | — | Unix-sockel | För upptäckt av containersessioner |

Sync-daemonen gör bara utgående HTTPS-anrop till `ingest.clawmetry.com`. Inga inkommande portar krävs.

---

## Molndistribution

Se **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** för SSH-tunnlar, omvänd proxy och Docker.

## Testning

Detta projekt testas med BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry skickar anonyma pingar för installationslivscykeln till
`https://app.clawmetry.com/api/install`: en `install`-ping första
gången du kör `clawmetry`-CLI:t på en ny maskin, en `update`-ping
första körningen efter en uppgradering till en ny version, och en `onboarded`-
ping när du slutför onboarding-valet i instrumentpanelen. Vi använder detta
för att räkna faktiska installationer (rå PyPI-nedladdningsstatistik är ~98 % speglingar, CI
och automatiska nedladdningar vid uppdatering) och för att lära oss vilka agentramverk och
versioner som faktiskt används.

**Högst en POST per livscykelhändelse per version**, innehållande:

| Fält | Exempel | Varför |
|---|---|---|
| `install_id` | slumpmässig UUID lagrad i `~/.clawmetry/install_id` | avdubblering; anonymt tills du uttryckligen ansluter Cloud-synk (den autentiserade daemonens hjärtslag bär då med det, och länkar denna installation till ditt konto) |
| `event` | `install` / `update` / `onboarded` | ny installation vs uppgradering av en befintlig |
| `version` | `0.12.167` | vilka versioner som används |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioriteringar för plattformsstöd |
| `python` | `3.11.15` | supportmatris för Python-version |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | vilka agenter vi bör integrera med härnäst |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separerar mänskliga installationer från CI-brus |

**Vad vi INTE skickar**: IP (molnet härleder landskoden server-side
från förfrågan och kasserar sedan IP:n), värdnamn, användarnamn, sökväg till arbetsyta, filinnehåll, din api_key, din e-post, något som är PII eller
specifikt för arbetsytan. Nyttolasten som skickas kan granskas i
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Avaktivera** (valfri av dessa inaktiverar det permanent):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ett nätverksfel här blockerar aldrig `clawmetry` från att köra, pingen
är fire-and-forget på en daemon-tråd med en timeout på 3 s.

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
