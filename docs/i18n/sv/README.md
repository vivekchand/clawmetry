<!-- i18n-src:8f42d460a973 -->
> Svenska translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Se hur din agent tänker.** Realtidsobservabilitet för **14 AI-agentruntimer**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex och 10 till. En enda instrumentpanel för hela din agentflotta.

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Ingen konfiguration. Upptäcker allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900** och du är klar.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Fungerar med 14 agentruntimer

ClawMetry började som observabilitet för OpenClaw, och mäter nu **hela din agentflotta** i en instrumentpanel, med automatisk upptäckt av varje runtime på din maskin:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw och NemoClaw är gratis i appen med öppen källkod; övriga runtimer aktiveras med ClawMetry Cloud eller en självhostad Pro-licens. Byt runtime från sidhuvudet, så anpassar sig varje flik, kostnad, tokens, verktyg, spårningar, till den runtimen. Se **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** för den exakta uppdelningen mellan gratis och betalt, nivåmatrisen, `/api/entitlement`-formatet och `clawmetry license`-CLI:t.

## Vad du får

- **Flow** — Levande animerat diagram som visar meddelanden som flödar genom kanaler, hjärna, verktyg och tillbaka
- **Overview** — Hälsokontroller, aktivitetsvärmekarta, sessionsantal, modellinfo
- **Usage** — Token- och kostnadsspårning med daglig/vecko-/månadsuppdelning
- **Sessions** — Aktiva agentsessioner med modell, tokens, senaste aktivitet
- **Crons** — Schemalagda jobb med status, nästa körning, varaktighet
- **Logs** — Färgkodad realtidsloggströmning
- **Memory** — Bläddra i SOUL.md, MEMORY.md, AGENTS.md, dagliga anteckningar
- **Transcripts** — Chattbubbelgränssnitt för att läsa sessionshistorik
- **Alerts** — Budgettak, felfrekvensutlösare, upptäckt av offline-agenter; skickar till Slack, Discord, PagerDuty, Telegram, e-post
- **Approvals** — Blockera destruktiva raderingar, force pushar, DB-mutationer, sudo, paketinstallationer, nätverksanrop bakom ett godkännande med ett klick

## Skärmbilder

### 🧠 Brain — Levande ström av agenthändelser
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Tokenanvändning och sessionssammanfattning
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Realtidsflöde av verktygsanrop
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Kostnadsuppdelning per modell och session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Filbläddrare för arbetsyta
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Säkerhetsläge och granskningslogg
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budgettak, felfrekvensutlösare, webhooks till Slack / Discord / PagerDuty / E-post
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blockera riskabla verktygsanrop bakom manuellt godkännande; policybaserade skyddsregler
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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
# Terminal 2: Vite-utvecklingsserver på :5173
cd frontend
nvm use
npm ci
npm run dev
```

Öppna `http://localhost:5173/v2/`. Vite vidarebefordrar `/api`-förfrågningar till
`http://localhost:8900`, så React-appen kan kommunicera med den lokala Flask-servern
utan extra CORS-konfiguration.

För att bygga paketet som levereras med Python-paketet:

```bash
cd frontend
npm run build
```

Produktionspaketet skrivs till `clawmetry/static/v2/dist/`.

## Kompatibilitet med runtimer/agenter

ClawMetry observerar många AI-agentruntimer, inte bara OpenClaw. Varje runtime som inte är OpenClaw levereras med en dedikerad läsaradapter som översätter dess ursprungliga sessionsformat till ClawMetrys enhetliga former; daemonen matar in dem i samma DuckDB-lager + molnsnapshot, taggade med runtimen, och fliken Session replay visar en **runtime-växlare** när fler än en finns. Se [`docs/compatibility.md`](docs/compatibility.md) för den fullständiga matrisen + en guide för att lägga till runtimer, och [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) för grundkursen om OpenClaw-familjen.

| Runtime/agent | Status | Anteckningar |
|---|---|---|
| **OpenClaw** | Inbyggd | Referensruntime, upptäcks automatiskt |
| **PicoClaw** | Betaadapter | Platt `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transkript, modell, verktygsanrop. |
| **NanoClaw** | Betaadapter | SQLite per session (`data/v2-sessions`). Transkript + meddelandeantal. |
| **Hermes** | Betaadapter | SQLite `~/.hermes/state.db`. Transkript, modell, tokens/kostnad. |
| **Claude Code** | Betaadapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkript, modell, verktygsanrop + tankeprocess, tokenanvändning. |
| **Codex** | Betaadapter | Rollout-JSONL `~/.codex/sessions/...`. Transkript, modell, verktygsanrop, tokenanvändning. |
| **Cursor** | Betaadapter | SQLite `state.vscdb`. Chatt-/composer-transkript, modell. |
| **Aider** | Betaadapter | `.aider.chat.history.md` per projekt. Transkript, modell, tokenantal. |
| **Goose** | Betaadapter | SQLite `~/.local/share/goose`. Transkript, modell, verktygsanrop, tokentotaler. |
| **opencode** | Betaadapter | SQLite `~/.local/share/opencode`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **Qwen Code** | Betaadapter | JSONL `~/.qwen/projects/.../chats`. Transkript, modell, verktygsanrop, tokenanvändning. |
| **Pi** | Betaadapter | JSONL `~/.pi/agent/sessions`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **Deep Agents** | Betaadapter | SQLite `~/.deepagents/.state/sessions.db`. Transkript, modell, verktygsanrop, tokens + kostnad. |

"Betaadapter" betyder att ClawMetry levererar en läsare för den runtimens faktiska format på disk, var och en byggd och verifierad mot en riktig installation på en riktig maskin (se `tests/fixtures/runtimes/<rt>/`). Adaptrarna är skrivskyddade; var och en är ärlig om vad dess runtime faktiskt lagrar (t.ex. skriver PicoClaw/NanoClaw/Cursor inte tokenkostnad till disk). När flera runtimer körs på en nod avgränsar runtime-växlaren sessionsvyn till en för en tydlig fördjupning.

## Spåra vilken SDK-agent som helst, out-loop-kostnadsattribuering

Runtimerna ovan skriver alla sessioner till disk. Din egen **produktionsagent**, den du byggde på OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, eller en vanlig `httpx`-loop, gör inte det. ClawMetrys konfigurationsfria interceptor fångar ändå dess LLM-anrop (kostnad, tokens, latens, fel) genom att monkey-patcha `httpx`/`requests`:

```python
import clawmetry.track            # aktivera interceptorn
clawmetry.track.set_source("support-agent")   # namnge denna produkt

# ...din agent körs som vanligt; varje LLM-anrop spåras och attribueras nu.
```

`set_source()` (eller miljövariabeln `CLAWMETRY_SOURCE=support-agent`) taggar varje anrop med en **namngiven källa**, så varje produkt du kör visas som sin egen förstklassiga, kostnadsattribuerbara rad i instrumentpanelens kort **🔌 Out-loop sources** på Overview, anrop, leverantörer, latens, felfrekvens per agent. Ingen källa angiven? Anropen spåras ändå, kortet döljs bara.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Detta är samma datalager som runtime-adaptrarna matar (DuckDB → molnsnapshot), så out-loop-källor synkroniseras till molninstrumentpanelen precis som allt annat, ände-till-ände-krypterat.

## OpenTelemetry, leverantörsneutralt, skicka dina spårningar vart som helst

ClawMetry talar **OpenTelemetry** i båda riktningarna, med hjälp av **GenAI-semantikkonventionerna**, så dina agentspårningar är aldrig låsta till ett enda verktyg.

**Exportera** varje session, LLM-anrop, verktyg, subagenter, tokens, kostnad, som OTLP/HTTP GenAI-spans till valfri insamlare (Datadog, Grafana, Honeycomb, eller din egen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# motsvarande:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Autentiseringsheaders och pollningsintervall är valfria miljövariabler:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP-headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # sekunder (standard 60)
```

**Inmatning** — den inbyggda OTLP-mottagaren tar emot spårningar och mätvärden från vad som helst annat på `/v1/traces` och `/v1/metrics` (`pip install clawmetry[otel]` för protobuf-inmatning).

Du får den konfigurationsfria, lokala ClawMetry-instrumentpanelen **och** dina data i vilken backend ditt team redan kör, ingen inlåsning, ingen andra agent att installera.

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

ClawMetry visar levande aktivitet för varje OpenClaw-kanal du har konfigurerat. Endast kanaler som faktiskt är uppsatta i din `openclaw.json` visas i Flow-diagrammet, okonfigurerade döljs automatiskt.

Klicka på valfri kanalnod i Flow för att se en levande chattbubbelvy med räknare för inkommande/utgående meddelanden.

| Kanal | Status | Levande popup | Anteckningar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Fullständig | ✅ | Meddelanden, statistik, uppdatering var 10:e sekund |
| 💬 **iMessage** | ✅ Fullständig | ✅ | Läser `~/Library/Messages/chat.db` direkt |
| 💚 **WhatsApp** | ✅ Fullständig | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Fullständig | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Fullständig | ✅ | Upptäckt av gilde + kanal |
| 🟪 **Slack** | ✅ Fullständig | ✅ | Upptäckt av arbetsyta + kanal |
| 🌐 **Webchat** | ✅ Fullständig | ✅ | Inbyggda webbgränssnitt-sessioner |
| 📡 **IRC** | ✅ Fullständig | ✅ | Terminalstil bubbelgränssnitt |
| 🍏 **BlueBubbles** | ✅ Fullständig | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Fullständig | ✅ | Via Chat API-webhooks |
| 🟣 **MS Teams** | ✅ Fullständig | ✅ | Via Teams-bot-plugin |
| 🔷 **Mattermost** | ✅ Fullständig | ✅ | Självhostad teamchatt |
| 🟩 **Matrix** | ✅ Fullständig | ✅ | Decentraliserad, stöd för E2EE |
| 🟢 **LINE** | ✅ Fullständig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Fullständig | ✅ | Decentraliserade NIP-04 DM:s |
| 🟣 **Twitch** | ✅ Fullständig | ✅ | Chatt via IRC-anslutning |
| 🔷 **Feishu/Lark** | ✅ Fullständig | ✅ | WebSocket-händelseprenumeration |
| 🔵 **Zalo** | ✅ Fullständig | ✅ | Zalo Bot API |

> **Automatisk upptäckt:** ClawMetry läser din `~/.openclaw/openclaw.json` och renderar endast de kanaler du faktiskt har konfigurerat. Ingen manuell inställning krävs.

## Docker-driftsättning

Vill du köra ClawMetry i en container? Inga problem! 🐳

**Snabbstart med Docker:**

```bash
# Bygg avbildningen
docker build -t clawmetry .

# Kör med standardinställningar
docker run -p 8900:8900 clawmetry

# Eller montera din agents datakatalog (visas: OpenClaws ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Exempel på Docker Compose:**

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

> **Obs:** När du kör i Docker, montera din agents data- och loggkataloger (t.ex. `~/.openclaw`, `~/.claude`, `~/.codex`) så att ClawMetry kan upptäcka din uppsättning automatiskt.

## Krav

- Python 3.8+
- Flask (installeras automatiskt via pip)
- En AI-agentruntime på samma maskin: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, eller Deep Agents (eller monterade volymer för Docker)
- Linux eller macOS

## Stöd för NemoClaw/OpenShell

ClawMetry upptäcker automatiskt [NemoClaw](https://github.com/NVIDIA/NemoClaw), NVIDIAs säkerhetswrapper för företag för OpenClaw som kör agenter inuti sandlådade OpenShell-containrar.

Ingen extra konfiguration krävs i de flesta fall. Synkroniseringsdaemonen upptäcker automatiskt sessionsfiler oavsett om de finns i `~/.openclaw/` på värden eller inuti en OpenShell-container.

### Hur det fungerar

ClawMetry upptäcker NemoClaw på två sätt:

1. **Binärupptäckt** — kontrollerar `nemoclaw`-CLI:t och kör `nemoclaw status` för att hämta sandlådeinformation
2. **Containerupptäckt** — skannar körande Docker-containrar efter `openshell`-, `nemoclaw`- eller `ghcr.io/nvidia/`-avbildningar, och läser sedan sessioner via volymmonteringar eller `docker cp`

Sessionsfiler som synkroniseras från NemoClaw-containrar taggas med `runtime=nemoclaw` och `container_id`-metadata i molninstrumentpanelen, så du kan skilja dem från vanliga OpenClaw-sessioner på ett ögonkast.

### Rekommenderad uppsättning: synkroniseringsdaemon på VÄRDEN

För bästa upplevelse, kör ClawMetrys synkroniseringsdaemon på **värdmaskinen** (inte inuti sandlådan). Detta undviker NemoClaws nätverkspolicybegränsningar.

```bash
# På värden (utanför sandlådan)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Synkroniseringsdaemonen hittar automatiskt sessioner inuti alla körande OpenShell-containrar.

### Valfritt: explicit sandlådenamn

Om automatisk upptäckt inte fungerar, peka ClawMetry mot rätt sandlåda:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Körning inuti sandlådan (avancerat)

Om du måste köra synkroniseringsdaemonen **inuti** OpenShell-sandlådan, lägg till denna utgående regel i din NemoClaw-nätverkspolicy så att den kan nå ClawMetrys inmatnings-API:

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
| `localhost:8900` | 8900 | HTTP | Ja (lokalt instrumentpanelsgränssnitt) |
| Docker-socket (`/var/run/docker.sock`) | — | Unix-socket | För upptäckt av containersessioner |

Synkroniseringsdaemonen gör endast utgående HTTPS-anrop till `ingest.clawmetry.com`. Inga inkommande portar krävs.

---

## Molndriftsättning

Se **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** för SSH-tunnlar, omvänd proxy och Docker.

## Testning

Detta projekt testas med BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry skickar en enda anonym "första körning"-signal till
`https://app.clawmetry.com/api/install` första gången du kör
`clawmetry`-CLI:t på en ny maskin. Vi använder detta för att räkna installationer (det
enda marknadsföringsmått vi har för ett OSS-projekt) och för att lära oss vilka
agentramverk våra användare har installerat.

**Exakt en POST per installation**, som innehåller:

| Fält | Exempel | Varför |
|---|---|---|
| `install_id` | slumpmässig UUID lagrad på `~/.clawmetry/install_id` | avdubblering; inte kopplad till din e-post eller api_key |
| `version` | `0.12.167` | vilka versioner som är i omlopp |
| `os` / `os_version` | `Darwin` / `25.3.0` | prioriteringar för plattformsstöd |
| `python` | `3.11.15` | matris för Python-versionsstöd |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | vilka agenter vi bör integrera med härnäst |
| `is_ci` / `ci_provider` | `true` / `github_actions` | skilja mänskliga installationer från CI-brus |

**Vad vi INTE skickar**: IP (molnet härleder landskoden serversidan
från förfrågan, och kasserar sedan IP:n), värdnamn, användarnamn, sökväg till arbetsyta,
filinnehåll, din api_key, din e-post, något PII eller
arbetsyterelaterat. Nätverkspaketet kan granskas i
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Välj bort** (vilken som helst av dessa inaktiverar det permanent):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per skal
export DO_NOT_TRACK=1                          # W3C-standard för flera verktyg
touch ~/.clawmetry/notelemetry                 # permanent filmarkör
```

Ett nätverksfel här blockerar aldrig `clawmetry` från att köras, signalen
är skjut-och-glöm på en daemon-tråd med en tidsgräns på 3 sekunder.

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
  <strong>🦞 Se hur din agent tänker</strong><br>
  <sub>Byggd av <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · En del av <a href="https://github.com/openclaw/openclaw">OpenClaw</a>-ekosystemet</sub>
</p>
