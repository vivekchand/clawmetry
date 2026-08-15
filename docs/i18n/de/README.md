<!-- i18n-src:c422fb7dd0da -->
> Deutsch translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Sieh zu, wie dein Agent denkt.** Echtzeit-Observability für **20 KI-Agent-Runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex und 16 weitere. Ein Dashboard für deine gesamte Agent-Flotte.

> 🌐 **Lies dies auf:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mehr →](docs/i18n/)

Ein Befehl. Keine Konfiguration. Erkennt alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Öffnet sich unter **http://localhost:8900** und schon ist es fertig.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funktioniert mit 20 Agent-Runtimes

ClawMetry begann als Observability für OpenClaw und erfasst jetzt deine **gesamte Agent-Flotte** in einem Dashboard, indem jede Runtime auf deinem Rechner automatisch erkannt wird:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw und NemoClaw sind in der Open-Source-App kostenlos; die anderen Runtimes werden mit ClawMetry Cloud oder einer selbst gehosteten Pro-Lizenz freigeschaltet. Wechsle die Runtime über den Header, und jeder Tab, Kosten, Tokens, Tools, Traces, bezieht sich neu auf diese Runtime. Siehe **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** für die genaue Aufteilung zwischen kostenlos und kostenpflichtig, die Tier-Matrix, die Form von `/api/entitlement` und die `clawmetry license`-CLI.

## Das bekommst du

- **Flow** — Live animiertes Diagramm, das zeigt, wie Nachrichten durch Kanäle, Brain, Tools und zurück fließen
- **Overview** — Health-Checks, Aktivitäts-Heatmap, Sitzungszähler, Modellinformationen
- **Usage** — Token- und Kostenverfolgung mit täglichen/wöchentlichen/monatlichen Aufschlüsselungen
- **Sessions** — Aktive Agent-Sitzungen mit Modell, Tokens, letzter Aktivität
- **Crons** — Geplante Jobs mit Status, nächstem Lauf, Dauer
- **Logs** — Farbcodiertes Echtzeit-Log-Streaming
- **Memory** — SOUL.md, MEMORY.md, AGENTS.md, tägliche Notizen durchsuchen
- **Transcripts** — Chat-Bubble-UI zum Lesen von Sitzungsverläufen
- **Alerts** — Budgetobergrenzen, Fehlerraten-Trigger, Erkennung von Offline-Agenten; Weiterleitung an Slack, Discord, PagerDuty, Telegram, E-Mail
- **Approvals** — Destruktive Löschvorgänge, Force-Pushes, DB-Mutationen, sudo, Paketinstallationen und Netzwerkaufrufe hinter einer Freigabe mit einem Klick absichern

## Screenshots

### 🧠 Brain — Live-Ereignisstrom des Agenten
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token-Nutzung & Sitzungsübersicht
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Echtzeit-Feed der Tool-Aufrufe
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Kostenaufschlüsselung nach Modell & Sitzung
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Workspace-Dateibrowser
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Sicherheitslage & Audit-Log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budgetobergrenzen, Fehlerraten-Trigger, Webhooks zu Slack / Discord / PagerDuty / E-Mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Riskante Tool-Aufrufe hinter manueller Freigabe absichern; richtliniengestützte Schutzregeln
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blockierung vor der Ausführung für Claude Code** — ein Befehl installiert
einen PreToolUse-Hook, der passende Tool-Aufrufe pausiert, *bevor* sie
ausgeführt werden, und auf deine Entscheidung wartet (ein Tap von deinem
Handy aus, wenn
[Cloud-Push-Benachrichtigungen](https://app.clawmetry.com/push) aktiviert sind):

```bash
clawmetry hooks install     # schreibt ~/.claude/settings.json (idempotent)
clawmetry hooks status      # was verdrahtet ist + wie viele Richtlinien aktiv sind
clawmetry hooks uninstall   # entfernt nur die Einträge von ClawMetry
```

Ein Deny blockiert nur diesen einen Tool-Aufruf, der Agent behält seine
Sitzung und kann einen anderen Ansatz versuchen. Eine Freigabe auf deinem
Handy überspringt Claude Codes eigenen Berechtigungsdialog (du hast ihn
bereits beantwortet). Nicht passende Tools kosten ~40ms und fallen zurück
in Claude Codes normalen Berechtigungsablauf. Außerdem bekommst du eine
Push-Benachrichtigung, wenn Claude Code selbst auf dich wartet
(`permission_prompt`- / `idle_prompt`-Benachrichtigungen).

## Installation

**Einzeiler (empfohlen):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Aus dem Quellcode:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2-Frontend-Entwicklung

Die v2-React-App befindet sich in `frontend/` und wird unter `/v2`
bereitgestellt, wenn der Flask-Server mit aktiviertem v2 gestartet wird.

Verwende während der Entwicklung zwei Terminals:

```bash
# Terminal 1: Flask-API/-Server auf :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite-Dev-Server auf :5173
cd frontend
nvm use
npm ci
npm run dev
```

Öffne `http://localhost:5173/v2/`. Vite leitet `/api`-Anfragen an
`http://localhost:8900` weiter, sodass die React-App ohne zusätzliches
CORS-Setup mit dem lokalen Flask-Server sprechen kann.

Um das Bundle zu erstellen, das mit dem Python-Paket ausgeliefert wird:

```bash
cd frontend
npm run build
```

Das Produktions-Bundle wird nach `clawmetry/static/v2/dist/` geschrieben.

## Runtime-/Agent-Kompatibilität

ClawMetry beobachtet viele KI-Agent-Runtimes, nicht nur OpenClaw. Jede Nicht-OpenClaw-Runtime bringt einen eigenen Reader-Adapter mit, der ihr natives Sitzungsformat in die einheitlichen Datenformen von ClawMetry übersetzt; der Daemon nimmt sie in denselben DuckDB-Speicher + Cloud-Snapshot auf, versehen mit der Runtime-Kennzeichnung, und der Session-Replay-Tab zeigt einen **Runtime-Umschalter**, sobald mehr als eine Runtime vorhanden ist. Siehe [`docs/compatibility.md`](docs/compatibility.md) für die vollständige Matrix + eine Anleitung zum Hinzufügen von Runtimes, und [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) für die Einführung in die OpenClaw-Familie.

Nutzt du [Perplexitys numbat](https://github.com/perplexityai/numbat) Agent-Sicherheitstool? ClawMetry nimmt dessen Befunde und Enforcement-Entscheidungen ohne Zusatzaufwand auf, siehe [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Status | Hinweise |
|---|---|---|
| **OpenClaw** | Nativ | Referenz-Runtime, automatisch erkannt |
| **PicoClaw** | Beta-Adapter | Flaches `providers.Message`-JSONL (`~/.picoclaw/workspace/sessions`). Transkripte, Modell, Tool-Aufrufe. |
| **NanoClaw** | Beta-Adapter | SQLite pro Sitzung (`data/v2-sessions`). Transkripte + Nachrichtenzähler. |
| **Hermes** | Beta-Adapter | SQLite `~/.hermes/state.db`. Transkripte, Modell, Tokens/Kosten. |
| **Claude Code** | Beta-Adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkripte, Modell, Tool-Aufrufe + Denkprozess, Token-Nutzung. |
| **Codex** | Beta-Adapter | Rollout-JSONL `~/.codex/sessions/...`. Transkripte, Modell, Tool-Aufrufe, Token-Nutzung. |
| **Cursor** | Beta-Adapter | SQLite `state.vscdb`. Chat-/Composer-Transkripte, Modell. |
| **Aider** | Beta-Adapter | `.aider.chat.history.md` pro Projekt. Transkripte, Modell, Token-Zähler. |
| **Goose** | Beta-Adapter | SQLite `~/.local/share/goose`. Transkripte, Modell, Tool-Aufrufe, Token-Gesamtsummen. |
| **opencode** | Beta-Adapter | SQLite `~/.local/share/opencode`. Transkripte, Modell, Tool-Aufrufe, Tokens + Kosten. |
| **Qwen Code** | Beta-Adapter | JSONL `~/.qwen/projects/.../chats`. Transkripte, Modell, Tool-Aufrufe, Token-Nutzung. |
| **Pi** | Beta-Adapter | JSONL `~/.pi/agent/sessions`. Transkripte, Modell, Tool-Aufrufe, Tokens + Kosten. |
| **Deep Agents** | Beta-Adapter | SQLite `~/.deepagents/.state/sessions.db`. Transkripte, Modell, Tool-Aufrufe, Tokens + Kosten. |
| **n8n** | Beta-Adapter | SQLite `~/.n8n/database.sqlite`. Workflow-Ausführungen, Node-Läufe, AI-Agent-Prompts, Modell + Tokens, sofern n8n sie erfasst. |
| **Antigravity** | Beta-Adapter | Brain-JSONL unter `~/.gemini/<flavor>/brain/`. Konversationen, Tool-Schritte, Denkprozess, Gemini-Token-Aufteilung pro Generierung + Kosten, Verbrauch durch Hintergrundgenerierung. |
| **GitHub Copilot** | Beta-Adapter | Copilot-CLI `events.jsonl` unter `~/.copilot/session-state/` + das `session-store.db`-Nutzungsledger pro Aufruf. Konversationen, Tool-Aufrufe, Modell-Routing, cache-bewusste Token-Aufteilung, vom Anbieter abgerechnete AI-Credit-Kosten. |
| **Grok** | Beta-Adapter | xAI Grok Build CLI (Rust-Binary unter `~/.grok/bin/grok`): globales Ereignisprotokoll `~/.grok/logs/unified.jsonl` + `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}` pro Sitzung. Konversationen, Token-Aufteilung pro Turn, Modell-Routing und die ausgehende Repo-Payload der CLI, bereitgestellt unter `~/.grok/upload_queue/`, damit du sehen kannst, was deinen Rechner verlassen hat. |

"Beta-Adapter" bedeutet, dass ClawMetry einen Reader für das echte On-Disk-Format dieser Runtime mitbringt, jeweils gebaut und gegen eine echte Installation auf einer echten Maschine verifiziert (siehe `tests/fixtures/runtimes/<rt>/`). Adapter sind nur lesend; jeder ist ehrlich darüber, was seine Runtime tatsächlich speichert (z. B. schreiben PicoClaw/NanoClaw/Cursor keine Token-Kosten auf die Festplatte). Wenn mehrere Runtimes auf einem Node laufen, grenzt der Runtime-Umschalter die Sitzungsansicht für eine übersichtliche Detailanalyse auf eine ein.

## Jeden SDK-Agenten verfolgen — Out-Loop-Kostenattribution

Die oben genannten Runtimes schreiben alle Sitzungen auf die Festplatte. Dein eigener **Produktionsagent** — der, den du mit dem OpenAI Agents SDK, LangChain, dem Vercel AI SDK, LlamaIndex, E2B oder einer einfachen `httpx`-Schleife gebaut hast — tut das nicht. Der zero-config Interceptor von ClawMetry erfasst dessen LLM-Aufrufe (Kosten, Tokens, Latenz, Fehler) trotzdem, indem er `httpx`/`requests` per Monkey-Patching versieht:

```python
import clawmetry.track            # aktiviert den Interceptor
clawmetry.track.set_source("support-agent")   # dieses Produkt benennen

# ...dein Agent läuft wie gewohnt; jeder LLM-Aufruf wird jetzt verfolgt + zugeordnet.
```

`set_source()` (oder die Umgebungsvariable `CLAWMETRY_SOURCE=support-agent`) markiert jeden Aufruf mit einer **benannten Quelle**, sodass jedes von dir betriebene Produkt als eigene, kostenmäßig zuordenbare Zeile in der Karte **🔌 Out-loop sources** auf Overview im Dashboard erscheint, mit Aufrufen, Anbietern, Latenz, Fehlerrate pro Agent. Keine Quelle gesetzt? Die Aufrufe werden trotzdem erfasst, die Karte bleibt nur verborgen.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Dies ist dieselbe Datenschicht, die auch die Runtime-Adapter speist (DuckDB → Cloud-Snapshot), sodass Out-loop-Quellen genau wie alles andere mit dem Cloud-Dashboard synchronisiert werden, Ende-zu-Ende-verschlüsselt.

## OpenTelemetry — anbieterneutral, sende deine Traces überallhin

ClawMetry spricht **OpenTelemetry** in beide Richtungen, unter Verwendung der **GenAI Semantic Conventions**, sodass deine Agent-Traces niemals an ein einziges Tool gebunden sind.

**Export** jeder Sitzung — LLM-Aufrufe, Tools, Sub-Agenten, Tokens, Kosten — als OTLP/HTTP-GenAI-Spans an jeden Collector (Datadog, Grafana, Honeycomb oder deinen eigenen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# äquivalent dazu:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth-Header und Poll-Intervall sind optionale Umgebungsvariablen:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # zusätzliche HTTP-Header
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # Sekunden (Standard 60)
```

**Ingest** — der eingebaute OTLP-Receiver nimmt Traces, Logs und Metriken von allem anderen unter `/v1/traces`, `/v1/logs` und `/v1/metrics` entgegen. Richte jede mit OpenTelemetry instrumentierte App darauf aus:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON-Traces und -Logs funktionieren mit einem einfachen `pip install clawmetry`, ohne Extras. Protobuf-Ingest (und OTLP/JSON-Metriken) benötigt `pip install clawmetry[otel]`. Eine App, die ihren eigenen `service.name` setzt, erscheint als eigener Agent im Runtime-Umschalter, mit ihren eigenen Kosten und Tokens.

Du bekommst das zero-config, lokal-first ClawMetry-Dashboard **und** deine Daten in dem Backend, das dein Team bereits nutzt, kein Lock-in, kein zweiter Agent zum Installieren.

## Konfiguration

Die meisten Leute brauchen keine Konfiguration. ClawMetry erkennt automatisch deinen Workspace, deine Logs, Sitzungen und Crons.

Falls du dennoch anpassen musst:

```bash
clawmetry --port 9000              # Benutzerdefinierter Port (Standard: 8900)
clawmetry --host 127.0.0.1         # Nur an localhost binden
clawmetry --workspace ~/mybot      # Benutzerdefinierter Workspace-Pfad
clawmetry --name "Alice"           # Dein Name in der Flow-Visualisierung
```

Alle Optionen: `clawmetry --help`

## Unterstützte Kanäle

ClawMetry zeigt Live-Aktivität für jeden konfigurierten OpenClaw-Kanal. Nur Kanäle, die tatsächlich in deiner `openclaw.json` eingerichtet sind, erscheinen im Flow-Diagramm, nicht konfigurierte werden automatisch ausgeblendet.

Klicke auf einen beliebigen Kanal-Knoten im Flow, um eine Live-Chat-Bubble-Ansicht mit Zählern für eingehende/ausgehende Nachrichten zu sehen.

| Kanal | Status | Live-Popup | Hinweise |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Vollständig | ✅ | Nachrichten, Statistiken, Aktualisierung alle 10s |
| 💬 **iMessage** | ✅ Vollständig | ✅ | Liest `~/Library/Messages/chat.db` direkt |
| 💚 **WhatsApp** | ✅ Vollständig | ✅ | Über WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Vollständig | ✅ | Über signal-cli |
| 🟣 **Discord** | ✅ Vollständig | ✅ | Guild- + Kanal-Erkennung |
| 🟪 **Slack** | ✅ Vollständig | ✅ | Workspace- + Kanal-Erkennung |
| 🌐 **Webchat** | ✅ Vollständig | ✅ | Eingebaute Web-UI-Sitzungen |
| 📡 **IRC** | ✅ Vollständig | ✅ | Terminal-artige Bubble-UI |
| 🍏 **BlueBubbles** | ✅ Vollständig | ✅ | iMessage über BlueBubbles-REST-API |
| 🔵 **Google Chat** | ✅ Vollständig | ✅ | Über Chat-API-Webhooks |
| 🟣 **MS Teams** | ✅ Vollständig | ✅ | Über Teams-Bot-Plugin |
| 🔷 **Mattermost** | ✅ Vollständig | ✅ | Selbst gehosteter Team-Chat |
| 🟩 **Matrix** | ✅ Vollständig | ✅ | Dezentral, E2EE-Unterstützung |
| 🟢 **LINE** | ✅ Vollständig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Vollständig | ✅ | Dezentrale NIP-04-DMs |
| 🟣 **Twitch** | ✅ Vollständig | ✅ | Chat über IRC-Verbindung |
| 🔷 **Feishu/Lark** | ✅ Vollständig | ✅ | WebSocket-Event-Subscription |
| 🔵 **Zalo** | ✅ Vollständig | ✅ | Zalo Bot API |

> **Automatische Erkennung:** ClawMetry liest deine `~/.openclaw/openclaw.json` und rendert nur die Kanäle, die du tatsächlich konfiguriert hast. Keine manuelle Einrichtung erforderlich.

## Docker-Deployment

Möchtest du ClawMetry in einem Container betreiben? Kein Problem! 🐳

**Schnellstart mit Docker:**

```bash
# Das Image bauen
docker build -t clawmetry .

# Mit Standardeinstellungen ausführen
docker run -p 8900:8900 clawmetry

# Oder das Datenverzeichnis deines Agenten einbinden (gezeigt: OpenClaws ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Docker-Compose-Beispiel:**

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

> **Hinweis:** Wenn du in Docker läufst, binde die Daten- + Log-Verzeichnisse deines Agenten ein (z. B. `~/.openclaw`, `~/.claude`, `~/.codex`), damit ClawMetry dein Setup automatisch erkennen kann.

## Voraussetzungen

- Python 3.8+
- Flask (wird automatisch über pip installiert)
- Eine KI-Agent-Runtime auf demselben Rechner: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok oder QM (oder eingebundene Volumes für Docker)
- Linux oder macOS

## NemoClaw-/OpenShell-Unterstützung

ClawMetry erkennt automatisch [NemoClaw](https://github.com/NVIDIA/NemoClaw) — NVIDIAs Enterprise-Sicherheits-Wrapper für OpenClaw, der Agenten in sandboxed OpenShell-Containern ausführt.

In den meisten Fällen ist keine zusätzliche Konfiguration erforderlich. Der Sync-Daemon entdeckt Sitzungsdateien automatisch, egal ob sie auf dem Host in `~/.openclaw/` oder innerhalb eines OpenShell-Containers liegen.

### So funktioniert es

ClawMetry erkennt NemoClaw auf zwei Arten:

1. **Binärerkennung** — prüft auf die `nemoclaw`-CLI und führt `nemoclaw status` aus, um Sandbox-Informationen zu erhalten
2. **Container-Erkennung** — scannt laufende Docker-Container nach `openshell`-, `nemoclaw`- oder `ghcr.io/nvidia/`-Images und liest Sitzungen dann über Volume-Mounts oder `docker cp`

Sitzungsdateien, die von NemoClaw-Containern synchronisiert werden, sind im Cloud-Dashboard mit `runtime=nemoclaw` und `container_id`-Metadaten gekennzeichnet, damit du sie auf einen Blick von Standard-OpenClaw-Sitzungen unterscheiden kannst.

### Empfohlenes Setup: Sync-Daemon auf dem HOST

Für die beste Erfahrung solltest du den Sync-Daemon von ClawMetry auf der **Host-Maschine** ausführen (nicht innerhalb der Sandbox). So vermeidest du Einschränkungen durch NemoClaws Netzwerkrichtlinien.

```bash
# Auf dem Host (außerhalb der Sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Der Sync-Daemon findet automatisch Sitzungen innerhalb aller laufenden OpenShell-Container.

### Optional: expliziter Sandbox-Name

Falls die automatische Erkennung nicht funktioniert, verweise ClawMetry auf die richtige Sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Ausführung innerhalb der Sandbox (fortgeschritten)

Wenn du den Sync-Daemon **innerhalb** der OpenShell-Sandbox ausführen musst, füge diese Egress-Regel zu deiner NemoClaw-Netzwerkrichtlinie hinzu, damit er die ClawMetry-Ingest-API erreichen kann:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Anwenden mit:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Ports und Endpunkte

| Endpunkt | Port | Protokoll | Erforderlich |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Ja (Sync-Daemon → Cloud) |
| `localhost:8900` | 8900 | HTTP | Ja (lokale Dashboard-UI) |
| Docker-Socket (`/var/run/docker.sock`) | — | Unix-Socket | Für die Erkennung von Container-Sitzungen |

Der Sync-Daemon macht nur ausgehende HTTPS-Aufrufe an `ingest.clawmetry.com`. Es sind keine eingehenden Ports erforderlich.

---

## Cloud-Deployment

Siehe den **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** für SSH-Tunnel, Reverse-Proxy und Docker.

## Testing

Dieses Projekt wird mit BrowserStack getestet.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetrie

ClawMetry sendet anonyme Install-Lifecycle-Pings an
`https://app.clawmetry.com/api/install`: einen `install`-Ping beim
ersten Ausführen der `clawmetry`-CLI auf einer neuen Maschine, einen
`update`-Ping beim ersten Lauf nach einem Upgrade auf eine neue
Version, und einen `onboarded`-Ping, wenn du die Onboarding-Auswahl im
Dashboard abschließt. Wir nutzen das, um echte Installationen zu
zählen (rohe PyPI-Download-Zahlen bestehen zu ~98 % aus Mirrors, CI und
automatischen Update-Neuherunterladungen) und um zu erfahren, welche
Agenten-Frameworks und Versionen tatsächlich im Einsatz sind.

**Höchstens ein POST pro Lifecycle-Ereignis und Version**, mit folgendem Inhalt:

| Feld | Beispiel | Warum |
|---|---|---|
| `install_id` | zufällige UUID, gespeichert unter `~/.clawmetry/install_id` | Deduplizierung; anonym, bis du explizit Cloud-Sync verbindest (der authentifizierte Daemon-Heartbeat trägt sie dann und verknüpft diese Installation mit deinem Konto) |
| `event` | `install` / `update` / `onboarded` | Neuinstallation vs. Upgrade einer bestehenden |
| `version` | `0.12.167` | welche Versionen im Einsatz sind |
| `os` / `os_version` | `Darwin` / `25.3.0` | Prioritäten bei der Plattformunterstützung |
| `python` | `3.11.15` | Unterstützungsmatrix für Python-Versionen |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | mit welchen Agenten wir uns als Nächstes integrieren sollten |
| `is_ci` / `ci_provider` | `true` / `github_actions` | menschliche Installationen von CI-Rauschen trennen |

**Was wir NICHT senden**: IP (die Cloud leitet den Ländercode
serverseitig aus der Anfrage ab und verwirft dann die IP), Hostname,
Benutzername, Workspace-Pfad, Dateiinhalte, deinen api_key, deine
E-Mail, irgendetwas PII- oder workspace-spezifisches. Die
Übertragungs-Payload ist einsehbar in
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Opt-out** (jede dieser Optionen deaktiviert es dauerhaft):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # pro Shell
export DO_NOT_TRACK=1                          # W3C-übergreifender Standard
touch ~/.clawmetry/notelemetry                 # dauerhafte Dateimarkierung
```

Ein Netzwerkfehler blockiert hier niemals die Ausführung von
`clawmetry` — der Ping läuft fire-and-forget in einem Daemon-Thread mit
einem Timeout von 3 Sekunden.

## Star-Verlauf

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Lizenz

MIT

---

<p align="center">
  <strong>🦞 Sieh zu, wie dein Agent denkt</strong><br>
  <sub>Erstellt von <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Teil des <a href="https://github.com/openclaw/openclaw">OpenClaw</a>-Ökosystems</sub>
</p>
