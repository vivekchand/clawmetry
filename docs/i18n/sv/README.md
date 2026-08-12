<!-- i18n-src:7cfb63716507 -->
> Svenska translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Se din agent tänka.** Realtidsobservabilitet för **14 AI-agentruntimer**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex och 10 till. En instrumentpanel för hela din agentflotta.

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Ingen konfiguration. Upptäcker allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900** och du är klar.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Fungerar med 14 agentruntimer

ClawMetry började som observabilitet för OpenClaw, och mäter nu **hela din agentflotta** i en instrumentpanel, med automatisk detektering av varje runtime på din maskin:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw och NemoClaw är gratis i öppen källkods-appen; övriga runtimer aktiveras med ClawMetry Cloud eller en självhostad Pro-licens. Växla runtime från sidhuvudet, så räknas varje flik, kostnad, tokens, verktyg, spårningar, om till den runtimen. Se **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** för den exakta gratis/betald-uppdelningen, nivåmatrisen, `/api/entitlement`-formen och `clawmetry license`-CLI:n.

## Vad du får

- **Flow** — Live animerat diagram som visar hur meddelanden flödar genom kanaler, hjärna, verktyg och tillbaka
- **Overview** — Hälsokontroller, aktivitetsvärmekarta, sessionsantal, modellinformation
- **Usage** — Token- och kostnadsspårning med daglig/veckovis/månatlig uppdelning
- **Sessions** — Aktiva agentsessioner med modell, tokens, senaste aktivitet
- **Crons** — Schemalagda jobb med status, nästa körning, varaktighet
- **Logs** — Färgkodad realtidsloggström
- **Memory** — Bläddra i SOUL.md, MEMORY.md, AGENTS.md, dagliga anteckningar
- **Transcripts** — Chattbubbels-UI för att läsa sessionshistorik
- **Alerts** — Budgettak, felfrekvensutlösare, agent-offline-detektering; dirigerar till Slack, Discord, PagerDuty, Telegram, e-post
- **Approvals** — Blockera destruktiva raderingar, tvingade push, databasmutationer, sudo, paketinstallationer, nätverksanrop bakom ett godkännande med ett klick

## Skärmdumpar

### 🧠 Brain — Live agenthändelseström
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Tokenanvändning och sessionssammanfattning
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Verktygsanrop i realtid
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Kostnadsuppdelning per modell och session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Filbläddrare för arbetsyta
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Säkerhetsläge och granskningslogg
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budgettak, felfrekvensutlösare, webhooks till Slack / Discord / PagerDuty / e-post
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blockera riskabla verktygsanrop bakom manuellt godkännande; policybaserade skyddsregler
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blockering före körning för Claude Code** — ett kommando installerar en
PreToolUse-hook som pausar matchande verktygsanrop *innan* de körs och väntar
på ditt beslut (ett tryck från din telefon med
[molnets push-notiser](https://app.clawmetry.com/push) aktiverade):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Ett avslag blockerar bara det enskilda verktygsanropet, agenten behåller sin
session och kan prova en annan metod. Att godkänna från telefonen hoppar över
Claude Codes eget behörighetsprompt (du har redan svarat). Omatchade verktyg
kostar ~40 ms och faller igenom till Claude Codes normala behörighetsflöde.
Du får också ett push-meddelande till telefonen när Claude Code själv väntar
på dig (`permission_prompt`- / `idle_prompt`-notiser).

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

## v2 Frontend-utveckling

v2 React-appen finns i `frontend/` och serveras på `/v2` när Flask-servern
startas med v2 aktiverat.

Använd två terminaler under utveckling:

```bash
# Terminal 1: Flask API/server på :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server på :5173
cd frontend
nvm use
npm ci
npm run dev
```

Öppna `http://localhost:5173/v2/`. Vite proxar `/api`-förfrågningar till
`http://localhost:8900`, så React-appen kan prata med den lokala Flask-servern
utan extra CORS-konfiguration.

För att bygga bundeln som levereras med Python-paketet:

```bash
cd frontend
npm run build
```

Produktionsbundeln skrivs till `clawmetry/static/v2/dist/`.

## Runtime-/agentkompatibilitet

ClawMetry observerar många AI-agentruntimer, inte bara OpenClaw. Varje runtime som inte är OpenClaw levereras med en dedikerad läsaradapter som översätter dess ursprungliga sessionsformat till ClawMetrys enhetliga format; daemonen läser in dem i samma DuckDB-lager + molnsnapshot, taggade med runtimen, och fliken Session replay visar en **runtime-växlare** när fler än en finns. Se [`docs/compatibility.md`](docs/compatibility.md) för den fullständiga matrisen + en guide för att lägga till runtimer, och [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) för en introduktion till OpenClaw-familjen.

Kör du [Perplexitys numbat](https://github.com/perplexityai/numbat)-verktyg för agentsäkerhet? ClawMetry läser in dess resultat och åtgärdsbeslut direkt, se [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime/agent | Status | Anteckningar |
|---|---|---|
| **OpenClaw** | Ursprunglig | Referensruntime, upptäcks automatiskt |
| **PicoClaw** | Betaadapter | Platt `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transkript, modell, verktygsanrop. |
| **NanoClaw** | Betaadapter | SQLite per session (`data/v2-sessions`). Transkript + meddelandeantal. |
| **Hermes** | Betaadapter | SQLite `~/.hermes/state.db`. Transkript, modell, tokens/kostnad. |
| **Claude Code** | Betaadapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkript, modell, verktygsanrop + tankeprocess, tokenanvändning. |
| **Codex** | Betaadapter | Rollout-JSONL `~/.codex/sessions/...`. Transkript, modell, verktygsanrop, tokenanvändning. |
| **Cursor** | Betaadapter | SQLite `state.vscdb`. Chatt-/composer-transkript, modell. |
| **Aider** | Betaadapter | `.aider.chat.history.md` per projekt. Transkript, modell, tokenantal. |
| **Goose** | Betaadapter | SQLite `~/.local/share/goose`. Transkript, modell, verktygsanrop, tokensummor. |
| **opencode** | Betaadapter | SQLite `~/.local/share/opencode`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **Qwen Code** | Betaadapter | JSONL `~/.qwen/projects/.../chats`. Transkript, modell, verktygsanrop, tokenanvändning. |
| **Pi** | Betaadapter | JSONL `~/.pi/agent/sessions`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **Deep Agents** | Betaadapter | SQLite `~/.deepagents/.state/sessions.db`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **n8n** | Betaadapter | SQLite `~/.n8n/database.sqlite`. Arbetsflödeskörningar, nodkörningar, AI Agent-prompter, modell + tokens där n8n registrerar dem. |
| **Antigravity** | Betaadapter | Brain-JSONL under `~/.gemini/<flavor>/brain/`. Konversationer, verktygssteg, tankeprocess, per-genereringsuppdelning av Gemini-tokens + kostnad, förbrukning från bakgrundsgenerering. |
| **GitHub Copilot** | Betaadapter | Copilot CLI:s `events.jsonl` under `~/.copilot/session-state/` + `session-store.db`-huvudboken per anrop. Konversationer, verktygsanrop, modellrouting, cache-medveten tokenuppdelning, leverantörsfakturerad AI-kreditkostnad. |
| **Grok** | Betaadapter | xAI Grok Build CLI (Rust-binär under `~/.grok/bin/grok`): global händelselogg `~/.grok/logs/unified.jsonl` + per-session `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Konversationer, tokenuppdelning per tur, modellrouting, och CLI:ns utgående repo-nyttolast som mellanlagras under `~/.grok/upload_queue/` så du kan se vad som lämnade din maskin. |

"Betaadapter" betyder att ClawMetry levererar en läsare för den runtimens
faktiska format på disk, var och en byggd + verifierad mot en riktig
installation på en riktig maskin (se `tests/fixtures/runtimes/<rt>/`).
Adaptrarna är skrivskyddade; var och en är ärlig om vad dess runtime
faktiskt lagrar (t.ex. skriver PicoClaw/NanoClaw/Cursor inte tokenkostnad
till disk). När flera runtimer körs på en nod avgränsar runtime-växlaren
sessionsvyn till en för en ren fördjupning.

## Spåra vilken SDK-agent som helst, kostnadsattribuering utanför loopen

Runtimerna ovan skriver alla sessioner till disk. Din egen
**produktionsagent**, den du byggde på OpenAI Agents SDK, LangChain, Vercel
AI SDK, LlamaIndex, E2B, eller en vanlig `httpx`-loop, gör inte det.
ClawMetrys konfigurationsfria interceptor fångar ändå dess LLM-anrop
(kostnad, tokens, latens, fel) genom att apa-patcha `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (eller miljövariabeln `CLAWMETRY_SOURCE=support-agent`) taggar
varje anrop med en **namngiven källa**, så varje produkt du kör visas som en
egen förstklassig, kostnadsattribuerbar rad i instrumentpanelens
**🔌 Out-loop sources**-kort på Overview, anrop, leverantörer, latens,
felfrekvens per agent. Ingen källa angiven? Anropen spåras ändå, kortet
förblir bara dolt.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Detta är samma datalager som runtime-adaptrarna matar (DuckDB → molnsnapshot),
så out-loop-källor synkas till molninstrumentpanelen precis som allt annat,
E2E-krypterat.

## OpenTelemetry, leverantörsneutralt, skicka dina spårningar var som helst

ClawMetry talar **OpenTelemetry** i båda riktningarna, med hjälp av
**GenAI-semantikkonventionerna**, så dina agentspårningar blir aldrig
inlåsta i ett enda verktyg.

**Exportera** varje session, LLM-anrop, verktyg, underagenter, tokens,
kostnad, som OTLP/HTTP GenAI-spans till valfri insamlare (Datadog, Grafana,
Honeycomb, eller din egen OTel Collector):

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

**Inmatning** — den inbyggda OTLP-mottagaren tar emot spårningar och mätvärden
från allt annat på `/v1/traces` och `/v1/metrics` (`pip install
clawmetry[otel]` för protobuf-inmatning).

Du får den konfigurationsfria, lokalt först-instrumentpanelen från ClawMetry
**och** dina data i vilken backend ditt team redan kör, ingen inlåsning,
ingen andra agent att installera.

## Konfiguration

De flesta behöver ingen konfiguration alls. ClawMetry upptäcker automatiskt
din arbetsyta, loggar, sessioner och cron-jobb.

Om du behöver anpassa:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Alla alternativ: `clawmetry --help`

## Kanaler som stöds

ClawMetry visar live-aktivitet för varje OpenClaw-kanal du har konfigurerat.
Endast kanaler som faktiskt är konfigurerade i din `openclaw.json` visas i
Flow-diagrammet, okonfigurerade döljs automatiskt.

Klicka på valfri kanalnod i Flow för att se en live-chattbubbelvy med
antal inkommande/utgående meddelanden.

| Kanal | Status | Live-popup | Anteckningar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Fullständig | ✅ | Meddelanden, statistik, uppdatering var 10:e sekund |
| 💬 **iMessage** | ✅ Fullständig | ✅ | Läser `~/Library/Messages/chat.db` direkt |
| 💚 **WhatsApp** | ✅ Fullständig | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Fullständig | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Fullständig | ✅ | Detektering av server + kanal |
| 🟪 **Slack** | ✅ Fullständig | ✅ | Detektering av arbetsyta + kanal |
| 🌐 **Webchat** | ✅ Fullständig | ✅ | Inbyggda webb-UI-sessioner |
| 📡 **IRC** | ✅ Fullständig | ✅ | Terminalstil bubbel-UI |
| 🍏 **BlueBubbles** | ✅ Fullständig | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Fullständig | ✅ | Via Chat API-webhooks |
| 🟣 **MS Teams** | ✅ Fullständig | ✅ | Via Teams-bot-plugin |
| 🔷 **Mattermost** | ✅ Fullständig | ✅ | Självhostad teamchatt |
| 🟩 **Matrix** | ✅ Fullständig | ✅ | Decentraliserat, E2EE-stöd |
| 🟢 **LINE** | ✅ Fullständig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Fullständig | ✅ | Decentraliserade NIP-04-DM |
| 🟣 **Twitch** | ✅ Fullständig | ✅ | Chatt via IRC-anslutning |
| 🔷 **Feishu/Lark** | ✅ Fullständig | ✅ | WebSocket-händelseprenumeration |
| 🔵 **Zalo** | ✅ Fullständig | ✅ | Zalo Bot API |

> **Automatisk detektering:** ClawMetry läser din `~/.openclaw/openclaw.json`
> och renderar bara de kanaler du faktiskt har konfigurerat. Ingen manuell
> konfiguration krävs.

## Docker-driftsättning

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

> **Obs:** När du kör i Docker, montera din agents data- och loggkataloger
> (t.ex. `~/.openclaw`, `~/.claude`, `~/.codex`) så att ClawMetry kan
> upptäcka din konfiguration automatiskt.

## Krav

- Python 3.8+
- Flask (installeras automatiskt via pip)
- En AI-agentruntime på samma maskin: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, eller QM (eller monterade volymer för Docker)
- Linux eller macOS

## NemoClaw-/OpenShell-stöd

ClawMetry upptäcker automatiskt [NemoClaw](https://github.com/NVIDIA/NemoClaw),
NVIDIAs säkerhetsomslag för företag runt OpenClaw som kör agenter inuti
sandboxade OpenShell-containrar.

Ingen extra konfiguration behövs i de flesta fall. Sync-daemonen upptäcker
automatiskt sessionsfiler oavsett om de finns i `~/.openclaw/` på värden
eller inuti en OpenShell-container.

### Hur det fungerar

ClawMetry upptäcker NemoClaw på två sätt:

1. **Binärdetektering** — kontrollerar om `nemoclaw`-CLI:n finns och kör `nemoclaw status` för sandboxinformation
2. **Containerdetektering** — söker igenom körande Docker-containrar efter `openshell`-, `nemoclaw`- eller `ghcr.io/nvidia/`-avbildningar, och läser sedan sessioner via volymmonteringar eller `docker cp`

Sessionsfiler som synkas från NemoClaw-containrar taggas med `runtime=nemoclaw`
och `container_id`-metadata i molninstrumentpanelen, så du kan skilja dem från
vanliga OpenClaw-sessioner med ett ögonkast.

### Rekommenderad konfiguration: sync-daemon på VÄRDEN

För bästa upplevelse, kör ClawMetrys sync-daemon på **värdmaskinen** (inte
inuti sandboxen). Detta undviker NemoClaws nätverkspolicybegränsningar.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Sync-daemonen hittar automatiskt sessioner inuti alla körande
OpenShell-containrar.

### Valfritt: explicit sandboxnamn

Om automatisk detektering inte fungerar, peka ClawMetry mot rätt sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Att köra inuti sandboxen (avancerat)

Om du måste köra sync-daemonen **inuti** OpenShell-sandboxen, lägg till denna
utgående regel i din NemoClaw-nätverkspolicy så att den kan nå
ClawMetrys inmatnings-API:

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
| `localhost:8900` | 8900 | HTTP | Ja (lokal instrumentpanels-UI) |
| Docker-socket (`/var/run/docker.sock`) | — | Unix-socket | För containersessionsupptäckt |

Sync-daemonen gör bara utgående HTTPS-anrop till `ingest.clawmetry.com`.
Inga inkommande portar krävs.

---

## Molndriftsättning

Se **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** för SSH-tunnlar, reverse proxy och Docker.

## Testning

Detta projekt testas med BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry skickar anonyma installationslivscykelpingar till
`https://app.clawmetry.com/api/install`: en `install`-ping första gången du
kör `clawmetry`-CLI:n på en ny maskin, en `update`-ping vid första körningen
efter uppgradering till en ny version, och en `onboarded`-ping när du slutför
onboarding-valet i instrumentpanelen. Vi använder detta för att räkna riktiga
installationer (rådata från PyPI-nedladdningar är ~98 % speglar, CI och
automatiska omnedladdningar) och för att lära oss vilka agentramverk och
versioner som faktiskt används.

**Högst en POST per livscykelhändelse per version**, innehållande:

| Fält | Exempel | Varför |
|---|---|---|
| `install_id` | slumpmässig UUID lagrad på `~/.clawmetry/install_id` | avdubblering; anonym tills du uttryckligen ansluter Cloud-synk (den autentiserade daemon-hjärtslagen bär då med sig detta och länkar denna installation till ditt konto) |
| `event` | `install` / `update` / `onboarded` | ny installation kontra uppgradering av en befintlig |
| `version` | `0.12.167` | vilka versioner som är i bruk |
| `os` / `os_version` | `Darwin` / `25.3.0` | plattformsprioriteringar för stöd |
| `python` | `3.11.15` | Python-versionsstödmatris |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | vilka agenter vi bör integrera med härnäst |
| `is_ci` / `ci_provider` | `true` / `github_actions` | skiljer mänskliga installationer från CI-brus |

**Vad vi INTE skickar**: IP (molnet härleder landskoden server-side från
förfrågan och kasserar sedan IP-adressen), värdnamn, användarnamn,
arbetsytesökväg, filinnehåll, din api_key, din e-postadress, något PII
eller arbetsytespecifikt. Nyttolasten går att granska i
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Avaktivera** (vilken som helst av dessa inaktiverar det permanent):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ett nätverksfel här blockerar aldrig `clawmetry` från att köras, pingen är
"fire-and-forget" på en daemon-tråd med en timeout på 3 sekunder.

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
