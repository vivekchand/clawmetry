<!-- i18n-src:bab48eec552f -->
> Svenska translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Se din agent tänka.** Realtidsobservabilitet för **14 AI-agentmiljöer**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 10 till. En instrumentpanel för hela din agentflotta.

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Ingen konfiguration. Upptäcker allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900** och du är klar.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Fungerar med 14 agentmiljöer

ClawMetry började som observabilitet för OpenClaw, och mäter nu **hela din agentflotta** i en instrumentpanel, med automatisk detektering av varje miljö på din maskin:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw och NemoClaw är gratis i open source-appen; de övriga miljöerna aktiveras med ClawMetry Cloud eller en självhostad Pro-licens. Byt miljö från sidhuvudet så anpassas varje flik – kostnad, tokens, verktyg, spårningar – till den miljön. Se **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** för den exakta gratis/betal-uppdelningen, nivåmatrisen, `/api/entitlement`-formen och `clawmetry license`-CLI:t.

## Vad du får

- **Flow** – Levande animerat diagram som visar meddelanden flöda genom kanaler, hjärna, verktyg och tillbaka
- **Overview** – Hälsokontroller, aktivitetsvärmekarta, sessionsantal, modellinformation
- **Usage** – Token- och kostnadsspårning med dagliga/veckovisa/månatliga uppdelningar
- **Sessions** – Aktiva agentsessioner med modell, tokens, senaste aktivitet
- **Crons** – Schemalagda jobb med status, nästa körning, varaktighet
- **Logs** – Färgkodad strömning av loggar i realtid
- **Memory** – Bläddra i SOUL.md, MEMORY.md, AGENTS.md, dagliga anteckningar
- **Transcripts** – Chattbubbel-gränssnitt för att läsa sessionshistorik
- **Alerts** – Budgettak, felfrekvenstriggers, agent-offline-detektering; skickas till Slack, Discord, PagerDuty, Telegram, e-post
- **Approvals** – Blockera destruktiva raderingar, force pushes, DB-mutationer, sudo, paketinstallationer, nätverksanrop bakom ett engångsklick för godkännande

## Skärmdumpar

### 🧠 Brain – Livesände agenthändelser
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview – Tokenanvändning & sessionssammanfattning
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow – Verktygsanropsflöde i realtid
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens – Kostnadsuppdelning per modell & session
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory – Filbläddrare för arbetsytan
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security – Säkerhetsläge & granskningslogg
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts – Budgettak, felfrekvenstriggers, webhooks till Slack / Discord / PagerDuty / e-post
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals – Blockera riskfyllda verktygsanrop bakom manuellt godkännande; policybaserade skyddsregler
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blockering före körning för Claude Code** – ett kommando installerar
en PreToolUse-hook som pausar matchande verktygsanrop *innan* de körs och väntar
på ditt beslut (ett tryck från din telefon med
[cloud push-notiser](https://app.clawmetry.com/push) aktiverat):

```bash
clawmetry hooks install     # skriver ~/.claude/settings.json (idempotent)
clawmetry hooks status      # vad som är kopplat + hur många policyer som är aktiva
clawmetry hooks uninstall   # tar bort endast ClawMetrys poster
```

En avvisning blockerar bara det enskilda verktygsanropet – agenten behåller sin session och kan
försöka på ett annat sätt. Att godkänna från din telefon hoppar över Claude Codes egen
behörighetsprompt (du har redan svarat). Otillhörande verktyg kostar ~40 ms och
faller igenom till Claude Codes normala behörighetsflöde. Du får också en push till telefonen när Claude Code
själv väntar på dig (`permission_prompt` / `idle_prompt`-notiser).

## Installation

**Ett kommando (rekommenderas):**
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
`http://localhost:8900`, så React-appen kan prata med den lokala Flask-servern
utan extra CORS-konfiguration.

För att bygga paketet som levereras med Python-paketet:

```bash
cd frontend
npm run build
```

Produktionspaketet skrivs till `clawmetry/static/v2/dist/`.

## Kompatibilitet med miljöer / agenter

ClawMetry observerar många AI-agentmiljöer, inte bara OpenClaw. Varje miljö utöver OpenClaw levereras med en dedikerad läsaradapter som översätter dess ursprungliga sessionsformat till ClawMetrys enhetliga former; daemonen tar in dem i samma DuckDB-lager + molnögonblicksbild, taggade med miljön, och fliken Session replay visar en **miljöväxlare** när fler än en förekommer. Se [`docs/compatibility.md`](docs/compatibility.md) för den fullständiga matrisen + en guide för att lägga till miljöer, och [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) för grundgenomgången av OpenClaw-familjen.

| Miljö / Agent | Status | Anteckningar |
|---|---|---|
| **OpenClaw** | Inbyggd | Referensmiljö, upptäcks automatiskt |
| **PicoClaw** | Betaadapter | Platt `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transkript, modell, verktygsanrop. |
| **NanoClaw** | Betaadapter | SQLite per session (`data/v2-sessions`). Transkript + meddelandeantal. |
| **Hermes** | Betaadapter | SQLite `~/.hermes/state.db`. Transkript, modell, tokens/kostnad. |
| **Claude Code** | Betaadapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkript, modell, verktygsanrop + tankeprocess, tokenanvändning. |
| **Codex** | Betaadapter | Rollout-JSONL `~/.codex/sessions/...`. Transkript, modell, verktygsanrop, tokenanvändning. |
| **Cursor** | Betaadapter | SQLite `state.vscdb`. Chatt-/composer-transkript, modell. |
| **Aider** | Betaadapter | `.aider.chat.history.md` per projekt. Transkript, modell, tokenantal. |
| **Goose** | Betaadapter | SQLite `~/.local/share/goose`. Transkript, modell, verktygsanrop, tokentotal. |
| **opencode** | Betaadapter | SQLite `~/.local/share/opencode`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **Qwen Code** | Betaadapter | JSONL `~/.qwen/projects/.../chats`. Transkript, modell, verktygsanrop, tokenanvändning. |
| **Pi** | Betaadapter | JSONL `~/.pi/agent/sessions`. Transkript, modell, verktygsanrop, tokens + kostnad. |
| **Deep Agents** | Betaadapter | SQLite `~/.deepagents/.state/sessions.db`. Transkript, modell, verktygsanrop, tokens + kostnad. |

"Betaadapter" betyder att ClawMetry levererar en läsare för den miljöns verkliga on-disk-format, var och en byggd + verifierad mot en verklig installation på en verklig maskin (se `tests/fixtures/runtimes/<rt>/`). Adaptrarna är skrivskyddade; var och en är ärlig om vad dess miljö faktiskt lagrar (t.ex. skriver PicoClaw/NanoClaw/Cursor inte tokenkostnad till disk). När flera miljöer körs på en nod avgränsar miljöväxlaren sessionsvyn till en för en ren djupdykning.

## Spåra vilken SDK-agent som helst – kostnadsattribuering utanför loopen

Miljöerna ovan skriver alla sessioner till disk. Din egen **produktionsagent** – den du byggde på OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B eller en vanlig `httpx`-loop – gör inte det. ClawMetrys interceptor utan konfiguration fångar ändå dess LLM-anrop (kostnad, tokens, latens, fel) genom att apa-patcha `httpx`/`requests`:

```python
import clawmetry.track            # aktivera interceptorn
clawmetry.track.set_source("support-agent")   # namnge denna produkt

# ...din agent körs som vanligt; varje LLM-anrop spåras nu + attribueras.
```

`set_source()` (eller miljövariabeln `CLAWMETRY_SOURCE=support-agent`) taggar varje anrop med en **namngiven källa**, så varje produkt du kör dyker upp som en egen förstklassig, kostnadsattribuerbar rad i instrumentpanelens kort **🔌 Out-loop sources** på Overview – anrop, leverantörer, latens, felfrekvens per agent. Ingen källa angiven? Anropen spåras ändå, kortet förblir bara dolt.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Detta är samma datalager som miljöadaptrarna matar (DuckDB → molnögonblicksbild), så out-loop-källor synkroniseras till molninstrumentpanelen precis som allt annat, ände-till-ände-krypterat.

## OpenTelemetry – leverantörsneutralt, skicka dina spårningar vart som helst

ClawMetry talar **OpenTelemetry** i båda riktningarna, med hjälp av **GenAI-semantikkonventionerna**, så dina agentspårningar blir aldrig inlåsta i ett enda verktyg.

**Exportera** varje session – LLM-anrop, verktyg, underagenter, tokens, kostnad – som OTLP/HTTP GenAI-spans till valfri insamlare (Datadog, Grafana, Honeycomb, eller din egen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# motsvarande:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Autentiseringsrubriker och pollningsintervall är valfria miljövariabler:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP-rubriker
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # sekunder (standard 60)
```

**Inta** – den inbyggda OTLP-mottagaren tar emot spårningar och mätvärden från vad som helst annat på `/v1/traces` och `/v1/metrics` (`pip install clawmetry[otel]` för protobuf-intag).

Du får den konfigurationsfria, lokalt förstahandsprioriterade ClawMetry-instrumentpanelen **och** dina data i vilken backend ditt team redan kör – ingen inlåsning, ingen andra agent att installera.

## Konfiguration

De flesta behöver ingen konfiguration alls. ClawMetry upptäcker automatiskt din arbetsyta, loggar, sessioner och crons.

Om du behöver anpassa:

```bash
clawmetry --port 9000              # Anpassad port (standard: 8900)
clawmetry --host 127.0.0.1         # Bind endast till localhost
clawmetry --workspace ~/mybot      # Anpassad sökväg till arbetsyta
clawmetry --name "Alice"           # Ditt namn i Flow-visualiseringen
```

Alla alternativ: `clawmetry --help`

## Kanaler som stöds

ClawMetry visar liveaktivitet för varje OpenClaw-kanal du har konfigurerat. Endast kanaler som faktiskt är inställda i din `openclaw.json` visas i Flow-diagrammet – okonfigurerade döljs automatiskt.

Klicka på valfri kanalnod i Flow för att se en livechattbubbelvy med antal inkommande/utgående meddelanden.

| Kanal | Status | Live-popup | Anteckningar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Fullständigt | ✅ | Meddelanden, statistik, uppdatering var 10:e sekund |
| 💬 **iMessage** | ✅ Fullständigt | ✅ | Läser `~/Library/Messages/chat.db` direkt |
| 💚 **WhatsApp** | ✅ Fullständigt | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Fullständigt | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Fullständigt | ✅ | Detektering av gille + kanal |
| 🟪 **Slack** | ✅ Fullständigt | ✅ | Detektering av arbetsyta + kanal |
| 🌐 **Webchat** | ✅ Fullständigt | ✅ | Inbyggda webbgränssnittssessioner |
| 📡 **IRC** | ✅ Fullständigt | ✅ | Terminalstil bubbel-gränssnitt |
| 🍏 **BlueBubbles** | ✅ Fullständigt | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Fullständigt | ✅ | Via Chat API-webhooks |
| 🟣 **MS Teams** | ✅ Fullständigt | ✅ | Via Teams-bot-plugin |
| 🔷 **Mattermost** | ✅ Fullständigt | ✅ | Självhostad teamchatt |
| 🟩 **Matrix** | ✅ Fullständigt | ✅ | Decentraliserad, stöd för E2EE |
| 🟢 **LINE** | ✅ Fullständigt | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Fullständigt | ✅ | Decentraliserade NIP-04 DM |
| 🟣 **Twitch** | ✅ Fullständigt | ✅ | Chatt via IRC-anslutning |
| 🔷 **Feishu/Lark** | ✅ Fullständigt | ✅ | WebSocket-händelseprenumeration |
| 🔵 **Zalo** | ✅ Fullständigt | ✅ | Zalo Bot API |

> **Automatisk detektering:** ClawMetry läser din `~/.openclaw/openclaw.json` och visar endast de kanaler du faktiskt har konfigurerat. Ingen manuell inställning krävs.

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

> **Obs:** När du kör i Docker, montera din agents data- + loggkataloger (t.ex. `~/.openclaw`, `~/.claude`, `~/.codex`) så att ClawMetry kan upptäcka din konfiguration automatiskt.

## Krav

- Python 3.8+
- Flask (installeras automatiskt via pip)
- En AI-agentmiljö på samma maskin: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi eller Deep Agents (eller monterade volymer för Docker)
- Linux eller macOS

## Stöd för NemoClaw / OpenShell

ClawMetry upptäcker automatiskt [NemoClaw](https://github.com/NVIDIA/NemoClaw) – NVIDIAs enterprise-säkerhetsomslag för OpenClaw som kör agenter inuti sandlådade OpenShell-containrar.

Ingen extra konfiguration behövs i de flesta fall. Synkroniseringsdaemonen upptäcker automatiskt sessionsfiler oavsett om de finns i `~/.openclaw/` på värden eller inuti en OpenShell-container.

### Så fungerar det

ClawMetry upptäcker NemoClaw på två sätt:

1. **Binärdetektering** – kontrollerar `nemoclaw`-CLI:t och kör `nemoclaw status` för att hämta sandlådeinformation
2. **Containerdetektering** – skannar körande Docker-containrar efter `openshell`-, `nemoclaw`- eller `ghcr.io/nvidia/`-avbildningar, och läser sedan sessioner via volymmonteringar eller `docker cp`

Sessionsfiler synkroniserade från NemoClaw-containrar taggas med `runtime=nemoclaw` och metadata för `container_id` i molninstrumentpanelen, så du kan skilja dem från vanliga OpenClaw-sessioner med en snabb blick.

### Rekommenderad konfiguration: synkroniseringsdaemon på VÄRDEN

För bästa upplevelse, kör ClawMetrys synkroniseringsdaemon på **värdmaskinen** (inte inuti sandlådan). Detta undviker NemoClaws nätverkspolicybegränsningar.

```bash
# På värden (utanför sandlådan)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Synkroniseringsdaemonen hittar automatiskt sessioner inuti alla körande OpenShell-containrar.

### Valfritt: explicit sandlådenamn

Om automatisk detektering inte fungerar, peka ClawMetry mot rätt sandlåda:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Köra inuti sandlådan (avancerat)

Om du måste köra synkroniseringsdaemonen **inuti** OpenShell-sandlådan, lägg till denna utgående regel i din NemoClaw-nätverkspolicy så att den kan nå ClawMetrys ingest-API:

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

ClawMetry skickar en enda anonym "första körning"-ping till
`https://app.clawmetry.com/api/install` första gången du kör
`clawmetry`-CLI:t på en ny maskin. Vi använder detta för att räkna installationer (den
enda marknadsföringsmätvärdet vi har för ett OSS-projekt) och för att lära oss vilka
agentramverk våra användare har installerat.

**Exakt en POST per installation**, innehållande:

| Fält | Exempel | Varför |
|---|---|---|
| `install_id` | slumpmässig UUID lagrad på `~/.clawmetry/install_id` | avdubbling; inte kopplat till din e-post eller api_key |
| `version` | `0.12.167` | vilka versioner som är i omlopp |
| `os` / `os_version` | `Darwin` / `25.3.0` | plattformsprioriteringar för stöd |
| `python` | `3.11.15` | Python-versionens supportmatris |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | vilka agenter vi bör integrera med härnäst |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separera mänskliga installationer från CI-brus |

**Vad vi INTE skickar**: IP (molnet härleder landskoden serversidan
från förfrågan och kastar sedan bort IP:n), värdnamn, användarnamn, sökväg till arbetsyta, filinnehåll, din api_key, din e-post, något PII eller
arbetsytespecifikt. Nätverkspayloaden är granskningsbar i
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Avanmäl dig** (vilket som helst av dessa inaktiverar det permanent):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per skal
export DO_NOT_TRACK=1                          # W3C-standard för flera verktyg
touch ~/.clawmetry/notelemetry                 # permanent filmarkör
```

Ett nätverksfel här blockerar aldrig `clawmetry` från att köras – pingen
är skicka-och-glöm på en daemon-tråd med en timeout på 3 sekunder.

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
