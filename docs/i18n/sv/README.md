<!-- i18n-src:48548997be76 -->
> Svenska translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Se din agent tänka.** Realtidsobservabilitet för **12 AI-agentmiljöer**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex och 8 till. En instrumentpanel för hela din agentflotta.

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Noll konfiguration. Identifierar allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900** och du är klar.

![Flödesvisualisering](https://clawmetry.com/screenshots/flow.png)

## Fungerar med 12 agentmiljöer

ClawMetry började som observabilitet för OpenClaw och mäter nu din **hela agentflotta** i en instrumentpanel, med automatisk identifiering av varje miljö på din maskin:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw och NemoClaw ingår gratis i öppen källkod-appen; de övriga miljöerna aktiveras med ClawMetry Cloud eller en egenhostad Pro-licens. Byt miljö från sidhuvudet och varje flik -- kostnad, tokens, verktyg, spårningar -- omfokuseras till den miljön.

## Vad du får

- **Flöde** -- Levande animerat diagram som visar meddelanden som flödar genom kanaler, hjärna, verktyg och tillbaka
- **Översikt** -- Hälsokontroller, aktivitetsvärmekartor, sessionsantal, modellinformation
- **Användning** -- Token- och kostnadsspårning med dagliga/vecko-/månadsuppdelningar
- **Sessioner** -- Aktiva agentsessioner med modell, tokens, senaste aktivitet
- **Crons** -- Schemalagda jobb med status, nästa körning, varaktighet
- **Loggar** -- Färgkodad realtidsloggströmning
- **Minne** -- Bläddra i SOUL.md, MEMORY.md, AGENTS.md, dagliga anteckningar
- **Transkript** -- Chattbubbel-gränssnitt för att läsa sessionshistorik
- **Aviseringar** -- Budgettak, felfrekvensutlösare, agentofflinedetektering; vidarebefordrar till Slack, Discord, PagerDuty, Telegram, e-post
- **Godkännanden** -- Spärra destruktiva borttagningar, tvingade pushningar, databasmutationer, sudo, paketinstallationer och nätverksanrop bakom ett enkelt klick

## Skärmdumpar

### 🧠 Hjärna -- Live agenteventsström
![Hjärnfliken](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Översikt -- Tokenanvändning och sessionssammanfattning
![Översiktsfliken](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flöde -- Realtidsflöde av verktygsanrop
![Flödesfliken](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens -- Kostnadsuppdelning per modell och session
![Tokensfliken](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Minne -- Arbetsytefilläsare
![Minnesfliken](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Säkerhet -- Säkerhetsläge och granskningslogg
![Säkerhetsfliken](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Aviseringar -- Budgettak, felfrekvensutlösare, webhooks till Slack / Discord / PagerDuty / e-post
![Aviseringsfliken](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Godkännanden -- Spärra riskfyllda verktygsanrop bakom manuellt godkännande; policybaserade skyddsregler
![Godkännandefliken](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Installera

**Enradskommando (rekommenderas):**
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

## v2 Frontendutveckling

v2 React-appen finns i `frontend/` och serveras på `/v2` när Flask-servern startas med v2 aktiverat.

Använd två terminaler under utveckling:

```bash
# Terminal 1: Flask API/server på :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite-devserver på :5173
cd frontend
nvm use
npm ci
npm run dev
```

Öppna `http://localhost:5173/v2/`. Vite vidarebefordrar `/api`-förfrågningar till `http://localhost:8900`, så React-appen kan kommunicera med den lokala Flask-servern utan extra CORS-konfiguration.

För att bygga det paket som levereras med Python-paketet:

```bash
cd frontend
npm run build
```

Produktionspaketet skrivs till `clawmetry/static/v2/dist/`.

## Miljö- och agentkompatibilitet

ClawMetry observerar många AI-agentmiljöer, inte bara OpenClaw. Varje miljö utöver OpenClaw levereras med en dedikerad läsaradapter som översätter dess ursprungliga sessionsformat till ClawMetrys enhetliga datastrukturer; demonen matar in dem i samma DuckDB-lager och molnögonblicksbild, taggade med miljön, och sessionsspelningsfliken visar en **miljöväxlare** när fler än en är tillgänglig. Se [`docs/compatibility.md`](docs/compatibility.md) för den fullständiga matrisen samt en guide för att lägga till miljöer, och [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) för en introduktion till OpenClaw-familjen.

| Miljö / Agent | Status | Anteckningar |
|---|---|---|
| **OpenClaw** | Inbyggt | Referensmiljö, identifieras automatiskt |
| **PicoClaw** | Beta-adapter | Platt `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transkript, modell, verktygsanrop. |
| **NanoClaw** | Beta-adapter | SQLite per session (`data/v2-sessions`). Transkript och meddelandeantal. |
| **Hermes** | Beta-adapter | SQLite `~/.hermes/state.db`. Transkript, modell, tokens/kostnad. |
| **Claude Code** | Beta-adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkript, modell, verktygsanrop och tänkande, tokenanvändning. |
| **Codex** | Beta-adapter | Rollout JSONL `~/.codex/sessions/...`. Transkript, modell, verktygsanrop, tokenanvändning. |
| **Cursor** | Beta-adapter | SQLite `state.vscdb`. Chatt-/kompositörstranskript, modell. |
| **Aider** | Beta-adapter | `.aider.chat.history.md` per projekt. Transkript, modell, tokenantal. |
| **Goose** | Beta-adapter | SQLite `~/.local/share/goose`. Transkript, modell, verktygsanrop, totala tokens. |
| **opencode** | Beta-adapter | SQLite `~/.local/share/opencode`. Transkript, modell, verktygsanrop, tokens och kostnad. |
| **Qwen Code** | Beta-adapter | JSONL `~/.qwen/projects/.../chats`. Transkript, modell, verktygsanrop, tokenanvändning. |

"Beta-adapter" innebär att ClawMetry levererar en läsare för den miljöns faktiska diskformat, var och en byggd och verifierad mot en riktig installation på en riktig maskin (se `tests/fixtures/runtimes/<rt>/`). Adaptrarna är skrivskyddade; varje adapter är ärlig om vad dess miljö faktiskt lagrar (t.ex. lagrar PicoClaw/NanoClaw/Cursor inte tokenkostnad på disk). När flera miljöer körs på en nod avgränsar miljöväxlaren sessionsvyn till en i taget för en ren djupdykning.

## Spåra valfri SDK-agent -- kostnadstillskrivning utanför loopen

Ovanstående miljöer skriver alla sessioner till disk. Din egen **produktionsagent** -- den du byggde med OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B eller en vanlig `httpx`-loop -- gör det inte. ClawMetrys nollkonfigurationsavlyssnare fångar ändå dess LLM-anrop (kostnad, tokens, latens, fel) genom att monkey-patcha `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (eller miljövariabeln `CLAWMETRY_SOURCE=support-agent`) taggar varje anrop med en **namngiven källa**, så varje produkt du kör visas som sin egen första klassens, kostnadsattribuerbara rad i instrumentpanelens **🔌 Utanför-loop-källor**-kort i Översikten -- anrop, leverantörer, latens, felfrekvens per agent. Ingen källa angiven? Anropen spåras ändå; kortet förblir bara dolt.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Detta är samma datalager som miljöadaptrarna matar in i (DuckDB till molnögonblicksbild), så utanför-loop-källor synkroniseras till molninstrumentpanelen på samma sätt som allt annat, end-to-end-krypterat.

## OpenTelemetry -- leverantörsneutralt, skicka dina spårningar vart som helst

ClawMetry talar **OpenTelemetry** i båda riktningarna och använder **GenAI-semantiska konventioner**, så dina agentspårningar är aldrig låsta till ett verktyg.

**Exportera** varje session -- LLM-anrop, verktyg, underagenter, tokens, kostnad -- som OTLP/HTTP GenAI-spann till valfri insamlare (Datadog, Grafana, Honeycomb eller din egen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Autentiseringsrubriker och pollintervall är valfria miljövariabler:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Mata in** -- den inbyggda OTLP-mottagaren accepterar spårningar och mätvärden från allt annat på `/v1/traces` och `/v1/metrics` (`pip install clawmetry[otel]` för protobuf-inmatning).

Du får den nollkonfigurerade, lokalfirst ClawMetry-instrumentpanelen **och** dina data i vilket backend ditt team redan kör -- ingen inlåsning, ingen andra agent att installera.

## Konfiguration

De flesta behöver ingen konfiguration alls. ClawMetry identifierar automatiskt din arbetsyta, loggar, sessioner och crons.

Om du ändå behöver anpassa:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Alla alternativ: `clawmetry --help`

## Kanaler som stöds

ClawMetry visar liveaktivitet för varje OpenClaw-kanal du har konfigurerad. Endast kanaler som faktiskt är konfigurerade i din `openclaw.json` visas i Flödesdiagrammet -- okonfigurerade döljs automatiskt.

Klicka på en kanalnod i Flödet för att se en livechattpubblvy med inkommande/utgående meddelandeantal.

| Kanal | Status | Live-popup | Anteckningar |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Fullständig | ✅ | Meddelanden, statistik, 10s uppdatering |
| 💬 **iMessage** | ✅ Fullständig | ✅ | Läser `~/Library/Messages/chat.db` direkt |
| 💚 **WhatsApp** | ✅ Fullständig | ✅ | Via WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Fullständig | ✅ | Via signal-cli |
| 🟣 **Discord** | ✅ Fullständig | ✅ | Server- och kanalidentifiering |
| 🟪 **Slack** | ✅ Fullständig | ✅ | Arbetsyta- och kanalidentifiering |
| 🌐 **Webchat** | ✅ Fullständig | ✅ | Inbyggda webbgränssnittssessioner |
| 📡 **IRC** | ✅ Fullständig | ✅ | Terminalstilad bubbelvy |
| 🍏 **BlueBubbles** | ✅ Fullständig | ✅ | iMessage via BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Fullständig | ✅ | Via Chat API-webhooks |
| 🟣 **MS Teams** | ✅ Fullständig | ✅ | Via Teams-bot-plugin |
| 🔷 **Mattermost** | ✅ Fullständig | ✅ | Egenhostad teamchatt |
| 🟩 **Matrix** | ✅ Fullständig | ✅ | Decentraliserat, E2EE-stöd |
| 🟢 **LINE** | ✅ Fullständig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Fullständig | ✅ | Decentraliserade NIP-04 DM:ar |
| 🟣 **Twitch** | ✅ Fullständig | ✅ | Chatt via IRC-anslutning |
| 🔷 **Feishu/Lark** | ✅ Fullständig | ✅ | WebSocket-evenemangsabonnemang |
| 🔵 **Zalo** | ✅ Fullständig | ✅ | Zalo Bot API |

> **Automatisk identifiering:** ClawMetry läser din `~/.openclaw/openclaw.json` och renderar bara de kanaler du faktiskt har konfigurerat. Ingen manuell konfiguration krävs.

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

> **Obs:** När du kör i Docker, montera din agents data- och loggkataloger (t.ex. `~/.openclaw`, `~/.claude`, `~/.codex`) så att ClawMetry kan identifiera din konfiguration automatiskt.

## Krav

- Python 3.8+
- Flask (installeras automatiskt via pip)
- En AI-agentmiljö på samma maskin: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw eller PicoClaw (eller monterade volymer för Docker)
- Linux eller macOS

## NemoClaw / OpenShell-stöd

ClawMetry identifierar automatiskt [NemoClaw](https://github.com/NVIDIA/NemoClaw) -- NVIDIAs företagssäkerhetslager för OpenClaw som kör agenter i sandlådade OpenShell-containers.

Ingen extra konfiguration krävs i de flesta fall. Synkroniseringsdemonen identifierar automatiskt sessionsfiler oavsett om de finns i `~/.openclaw/` på värden eller inuti en OpenShell-container.

### Hur det fungerar

ClawMetry identifierar NemoClaw på två sätt:

1. **Binär identifiering** -- söker efter `nemoclaw`-kommandot och kör `nemoclaw status` för att hämta sandlådeinformation
2. **Containeridentifiering** -- söker igenom körande Docker-containers efter `openshell`-, `nemoclaw`- eller `ghcr.io/nvidia/`-avbildningar och läser sedan sessioner via volymmonteringar eller `docker cp`

Sessionsfiler som synkroniseras från NemoClaw-containers taggas med `runtime=nemoclaw` och `container_id`-metadata i molninstrumentpanelen, så du kan skilja dem från vanliga OpenClaw-sessioner på ett ögonblick.

### Rekommenderad konfiguration: synkroniseringsdemon på VÄRDEN

För bästa upplevelse, kör ClawMetrys synkroniseringsdemon på **värdmaskinen** (inte inuti sandlådan). Detta undviker NemoclawNetverkspolicybegränsningar.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Synkroniseringsdemonen hittar automatiskt sessioner inuti alla körande OpenShell-containers.

### Valfritt: explicit sandlådenamn

Om automatisk identifiering inte fungerar, peka ClawMetry mot rätt sandlåda:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Köra inuti sandlådan (avancerat)

Om du måste köra synkroniseringsdemonen **inuti** OpenShell-sandlådan, lägg till denna utgående regel i din NemoClaw-nätverkspolicy så att den kan nå ClawMetry-inmatnings-API:et:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Ja (synkroniseringsdemon till moln) |
| `localhost:8900` | 8900 | HTTP | Ja (lokal instrumentpanel-UI) |
| Docker-socket (`/var/run/docker.sock`) | -- | Unix-socket | För containerssessionsidentifiering |

Synkroniseringsdemonen gör bara utgående HTTPS-anrop till `ingest.clawmetry.com`. Inga inkommande portar krävs.

---

## Molndistribution

Se **[Molntestningsguiden](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** för SSH-tunnlar, omvänd proxy och Docker.

## Testning

Detta projekt testas med BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetri

ClawMetry skickar ett enda anonymt "första körning"-ping till `https://app.clawmetry.com/api/install` första gången du kör `clawmetry`-kommandot på en ny maskin. Vi använder detta för att räkna installationer (det enda marknadsföringsmåttet vi har för ett öppen källkod-projekt) och för att ta reda på vilka agentramverk våra användare har installerade.

**Exakt en POST per installation**, som innehåller:

| Fält | Exempel | Varför |
|---|---|---|
| `install_id` | slumpmässigt UUID lagrat på `~/.clawmetry/install_id` | deduplicering; inte kopplat till din e-post eller api_key |
| `version` | `0.12.167` | vilka versioner som finns i det vilda |
| `os` / `os_version` | `Darwin` / `25.3.0` | plattformsstödsprioriteringar |
| `python` | `3.11.15` | Python-versionsstödmatris |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | vilka agenter vi bör integrera med härnäst |
| `is_ci` / `ci_provider` | `true` / `github_actions` | separera mänskliga installationer från CI-brus |

**Vad vi INTE skickar**: IP (molnet härleder landskoden på serversidan från förfrågan och raderar sedan IP:t), värdnamn, användarnamn, arbetsytesökväg, filinnehåll, din api_key, din e-post, något PII eller arbetsytespecifikt. Trådnyttolasten är granskningsbar i [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Välj bort** (ett av dessa inaktiverar det permanent):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ett nätverksfel här blockerar aldrig `clawmetry` från att köra -- pingen är avsändnings-och-glöm på en demontråd med en 3 s timeout.

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
  <sub>Byggt av <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Del av <a href="https://github.com/openclaw/openclaw">OpenClaw</a>-ekosystemet</sub>
</p>
