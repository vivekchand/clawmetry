<!-- i18n-src:48548997be76 -->
> Deutsch translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Beobachte, wie dein Agent denkt.** Echtzeit-Observability für **12 KI-Agenten-Laufzeitumgebungen**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex und 8 weitere. Ein Dashboard für deine gesamte Agenten-Flotte.

> 🌐 **Lies dies auf:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mehr →](docs/i18n/)

Ein Befehl. Keine Konfiguration. Erkennt alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Öffnet sich unter **http://localhost:8900** und das war's.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Kompatibel mit 12 Agenten-Laufzeitumgebungen

ClawMetry begann als Observability-Tool für OpenClaw und misst jetzt deine **gesamte Agenten-Flotte** in einem Dashboard, wobei jede Laufzeitumgebung auf deinem Rechner automatisch erkannt wird:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw und NemoClaw sind in der Open-Source-App kostenlos verfügbar; die anderen Laufzeitumgebungen werden mit ClawMetry Cloud oder einer selbst gehosteten Pro-Lizenz freigeschaltet. Wechsle die Laufzeitumgebung über den Header, und jeder Tab - Kosten, Tokens, Tools, Traces - schränkt sich auf diese Laufzeitumgebung ein.

## Was du bekommst

- **Flow** - Animiertes Live-Diagramm, das den Nachrichtenfluss durch Kanäle, Brain, Tools und zurück zeigt
- **Overview** - Gesundheitsprüfungen, Aktivitäts-Heatmap, Sitzungsanzahl, Modellinformationen
- **Usage** - Token- und Kostenverfolgung mit täglichen, wöchentlichen und monatlichen Aufschlüsselungen
- **Sessions** - Aktive Agenten-Sitzungen mit Modell, Tokens und letzter Aktivität
- **Crons** - Geplante Aufgaben mit Status, nächster Ausführung und Dauer
- **Logs** - Farbcodiertes Echtzeit-Log-Streaming
- **Memory** - SOUL.md, MEMORY.md, AGENTS.md und tägliche Notizen durchsuchen
- **Transcripts** - Chat-Blasen-Oberfläche zum Lesen von Sitzungsverläufen
- **Alerts** - Budgetlimits, Fehlerquoten-Auslöser, Erkennung von Agenten-Ausfällen; leitet weiter an Slack, Discord, PagerDuty, Telegram, E-Mail
- **Approvals** - Gefährliche Löschvorgänge, Force-Pushes, DB-Mutationen, sudo, Paketinstallationen und Netzwerkaufrufe hinter einer Einzel-Klick-Freigabe sichern

## Screenshots

### 🧠 Brain - Live-Agenten-Ereignisstrom
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview - Token-Nutzung & Sitzungsübersicht
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow - Echtzeit-Tool-Aufruf-Feed
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens - Kostenaufschlüsselung nach Modell & Sitzung
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory - Arbeitsbereich-Dateibrowser
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security - Sicherheitsstatus & Prüfprotokoll
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts - Budgetlimits, Fehlerquoten-Auslöser, Webhooks für Slack / Discord / PagerDuty / E-Mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals - Riskante Tool-Aufrufe hinter manueller Freigabe sichern; richtliniengestützte Schutzregeln
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

Die v2-React-App befindet sich in `frontend/` und wird unter `/v2` bereitgestellt, wenn der Flask-Server mit aktiviertem v2 gestartet wird.

Verwende zwei Terminals während der Entwicklung:

```bash
# Terminal 1: Flask-API/Server auf :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite-Dev-Server auf :5173
cd frontend
nvm use
npm ci
npm run dev
```

Öffne `http://localhost:5173/v2/`. Vite leitet `/api`-Anfragen an `http://localhost:8900` weiter, sodass die React-App mit dem lokalen Flask-Server kommunizieren kann, ohne zusätzliche CORS-Konfiguration.

Um das Bundle zu bauen, das mit dem Python-Paket ausgeliefert wird:

```bash
cd frontend
npm run build
```

Das Produktions-Bundle wird nach `clawmetry/static/v2/dist/` geschrieben.

## Laufzeitumgebung / Agenten-Kompatibilität

ClawMetry beobachtet viele KI-Agenten-Laufzeitumgebungen, nicht nur OpenClaw. Jede Nicht-OpenClaw-Laufzeitumgebung wird mit einem dedizierten Lese-Adapter ausgeliefert, der ihr natives Sitzungsformat in die einheitlichen Formen von ClawMetry übersetzt; der Daemon nimmt sie in denselben DuckDB-Store und Cloud-Snapshot auf, mit der Laufzeitumgebung getaggt, und der Sitzungs-Wiedergabe-Tab zeigt einen **Laufzeitumgebungs-Umschalter**, wenn mehr als eine vorhanden ist. Siehe [`docs/compatibility.md`](docs/compatibility.md) für die vollständige Matrix sowie eine Anleitung zum Hinzufügen von Laufzeitumgebungen, und [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) für eine Einführung in die OpenClaw-Familie.

| Laufzeitumgebung / Agent | Status | Hinweise |
|---|---|---|
| **OpenClaw** | Nativ | Referenz-Laufzeitumgebung, automatisch erkannt |
| **PicoClaw** | Beta-Adapter | Flaches `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transkripte, Modell, Tool-Aufrufe. |
| **NanoClaw** | Beta-Adapter | SQLite pro Sitzung (`data/v2-sessions`). Transkripte und Nachrichtenanzahl. |
| **Hermes** | Beta-Adapter | SQLite `~/.hermes/state.db`. Transkripte, Modell, Tokens/Kosten. |
| **Claude Code** | Beta-Adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkripte, Modell, Tool-Aufrufe und Denkvorgänge, Token-Nutzung. |
| **Codex** | Beta-Adapter | Rollout-JSONL `~/.codex/sessions/...`. Transkripte, Modell, Tool-Aufrufe, Token-Nutzung. |
| **Cursor** | Beta-Adapter | SQLite `state.vscdb`. Chat-/Composer-Transkripte, Modell. |
| **Aider** | Beta-Adapter | `.aider.chat.history.md` pro Projekt. Transkripte, Modell, Token-Anzahl. |
| **Goose** | Beta-Adapter | SQLite `~/.local/share/goose`. Transkripte, Modell, Tool-Aufrufe, Token-Gesamtzahl. |
| **opencode** | Beta-Adapter | SQLite `~/.local/share/opencode`. Transkripte, Modell, Tool-Aufrufe, Tokens und Kosten. |
| **Qwen Code** | Beta-Adapter | JSONL `~/.qwen/projects/.../chats`. Transkripte, Modell, Tool-Aufrufe, Token-Nutzung. |

"Beta-Adapter" bedeutet, dass ClawMetry einen Lesezugriff für das reale On-Disk-Format dieser Laufzeitumgebung bereitstellt, der jeweils auf einer echten Installation auf einem echten Rechner erstellt und verifiziert wurde (siehe `tests/fixtures/runtimes/<rt>/`). Adapter sind schreibgeschützt; jeder gibt ehrlich an, was seine Laufzeitumgebung tatsächlich speichert (z.B. schreiben PicoClaw/NanoClaw/Cursor keine Token-Kosten auf die Festplatte). Wenn mehrere Laufzeitumgebungen auf einem Knoten laufen, schränkt der Laufzeitumgebungs-Umschalter die Sitzungsansicht für eine saubere Detailansicht auf eine ein.

## Beliebige SDK-Agenten verfolgen - Out-Loop-Kostenzuordnung

Die oben genannten Laufzeitumgebungen schreiben alle Sitzungen auf die Festplatte. Dein eigener **Produktionsagent** - derjenige, den du auf dem OpenAI Agents SDK, LangChain, dem Vercel AI SDK, LlamaIndex, E2B oder einer einfachen `httpx`-Schleife aufgebaut hast - tut das nicht. Der Zero-Config-Interceptor von ClawMetry erfasst dennoch seine LLM-Aufrufe (Kosten, Tokens, Latenz, Fehler) durch Monkey-Patching von `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (oder die Umgebungsvariable `CLAWMETRY_SOURCE=support-agent`) versieht jeden Aufruf mit einer **benannten Quelle**, sodass jedes Produkt, das du betreibst, als eigene, kostenzuordenbare Zeile in der Karte **🔌 Out-Loop-Quellen** auf der Overview-Seite des Dashboards erscheint - Aufrufe, Anbieter, Latenz, Fehlerquote pro Agent. Keine Quelle angegeben? Die Aufrufe werden trotzdem erfasst; die Karte bleibt einfach ausgeblendet.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Dies ist dieselbe Datenschicht, die die Laufzeit-Adapter speisen (DuckDB zu Cloud-Snapshot), sodass Out-Loop-Quellen genauso wie alles andere mit E2E-Verschlüsselung in das Cloud-Dashboard synchronisiert werden.

## OpenTelemetry - anbieterneutral, sende deine Traces überallhin

ClawMetry spricht **OpenTelemetry** in beide Richtungen unter Verwendung der **GenAI-Semantikkonventionen**, sodass deine Agenten-Traces niemals an ein einziges Tool gebunden sind.

**Exportiere** jede Sitzung - LLM-Aufrufe, Tools, Unteragenten, Tokens, Kosten - als OTLP/HTTP-GenAI-Spans an einen beliebigen Collector (Datadog, Grafana, Honeycomb oder deinen eigenen OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth-Header und Abfrageintervall sind optionale Umgebungsvariablen:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Aufnahme** - der eingebaute OTLP-Empfänger nimmt Traces und Metriken von beliebigen Quellen unter `/v1/traces` und `/v1/metrics` entgegen (`pip install clawmetry[otel]` für Protobuf-Aufnahme).

Du bekommst das Zero-Config-, Local-First-ClawMetry-Dashboard **und** deine Daten in jedem Backend, das dein Team bereits betreibt - keine Anbieterbindung, kein zweiter Agent zum Installieren.

## Konfiguration

Die meisten Nutzer benötigen keine Konfiguration. ClawMetry erkennt deinen Arbeitsbereich, Logs, Sitzungen und crons automatisch.

Wenn du dennoch anpassen möchtest:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Alle Optionen: `clawmetry --help`

## Unterstützte Kanäle

ClawMetry zeigt Live-Aktivität für jeden OpenClaw-Kanal, den du konfiguriert hast. Nur Kanäle, die tatsächlich in deiner `openclaw.json` eingerichtet sind, erscheinen im Flow-Diagramm - nicht konfigurierte werden automatisch ausgeblendet.

Klicke auf einen beliebigen Kanal-Knoten im Flow, um eine Live-Chat-Blasen-Ansicht mit ein- und ausgehenden Nachrichtenanzahlen zu sehen.

| Kanal | Status | Live-Popup | Hinweise |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Vollständig | ✅ | Nachrichten, Statistiken, 10-Sekunden-Aktualisierung |
| 💬 **iMessage** | ✅ Vollständig | ✅ | Liest `~/Library/Messages/chat.db` direkt |
| 💚 **WhatsApp** | ✅ Vollständig | ✅ | Über WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Vollständig | ✅ | Über signal-cli |
| 🟣 **Discord** | ✅ Vollständig | ✅ | Guild- und Kanal-Erkennung |
| 🟪 **Slack** | ✅ Vollständig | ✅ | Workspace- und Kanal-Erkennung |
| 🌐 **Webchat** | ✅ Vollständig | ✅ | Eingebaute Web-UI-Sitzungen |
| 📡 **IRC** | ✅ Vollständig | ✅ | Terminal-artige Blasen-Oberfläche |
| 🍏 **BlueBubbles** | ✅ Vollständig | ✅ | iMessage über BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Vollständig | ✅ | Über Chat-API-Webhooks |
| 🟣 **MS Teams** | ✅ Vollständig | ✅ | Über Teams-Bot-Plugin |
| 🔷 **Mattermost** | ✅ Vollständig | ✅ | Selbst gehosteter Team-Chat |
| 🟩 **Matrix** | ✅ Vollständig | ✅ | Dezentralisiert, E2EE-Unterstützung |
| 🟢 **LINE** | ✅ Vollständig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Vollständig | ✅ | Dezentralisierte NIP-04-DMs |
| 🟣 **Twitch** | ✅ Vollständig | ✅ | Chat über IRC-Verbindung |
| 🔷 **Feishu/Lark** | ✅ Vollständig | ✅ | WebSocket-Ereignisabonnement |
| 🔵 **Zalo** | ✅ Vollständig | ✅ | Zalo Bot API |

> **Automatische Erkennung:** ClawMetry liest deine `~/.openclaw/openclaw.json` und stellt nur die Kanäle dar, die du tatsächlich konfiguriert hast. Keine manuelle Einrichtung erforderlich.

## Docker-Deployment

Möchtest du ClawMetry in einem Container betreiben? Kein Problem! 🐳

**Schnellstart mit Docker:**

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

**Docker Compose-Beispiel:**

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

> **Hinweis:** Wenn du Docker verwendest, mounte die Daten- und Log-Verzeichnisse deines Agenten (z.B. `~/.openclaw`, `~/.claude`, `~/.codex`), damit ClawMetry dein Setup automatisch erkennen kann.

## Anforderungen

- Python 3.8+
- Flask (automatisch über pip installiert)
- Eine KI-Agenten-Laufzeitumgebung auf demselben Rechner: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw oder PicoClaw (oder eingebundene Volumes für Docker)
- Linux oder macOS

## NemoClaw / OpenShell-Unterstützung

ClawMetry erkennt [NemoClaw](https://github.com/NVIDIA/NemoClaw) automatisch - NVIDIAs Enterprise-Sicherheitshülle für OpenClaw, die Agenten in isolierten OpenShell-Containern ausführt.

In den meisten Fällen ist keine zusätzliche Konfiguration erforderlich. Der Sync-Daemon findet Sitzungsdateien automatisch, egal ob sie in `~/.openclaw/` auf dem Host oder innerhalb eines OpenShell-Containers liegen.

### Funktionsweise

ClawMetry erkennt NemoClaw auf zwei Wegen:

1. **Binär-Erkennung** - prüft auf die `nemoclaw`-CLI und führt `nemoclaw status` aus, um Sandbox-Informationen zu erhalten
2. **Container-Erkennung** - scannt laufende Docker-Container nach `openshell`-, `nemoclaw`- oder `ghcr.io/nvidia/`-Images und liest dann Sitzungen über Volume-Mounts oder `docker cp`

Aus NemoClaw-Containern synchronisierte Sitzungsdateien werden im Cloud-Dashboard mit `runtime=nemoclaw` und `container_id`-Metadaten getaggt, sodass du sie auf einen Blick von Standard-OpenClaw-Sitzungen unterscheiden kannst.

### Empfohlene Einrichtung: Sync-Daemon auf dem HOST

Für die beste Erfahrung führe den Sync-Daemon von ClawMetry auf dem **Host-Rechner** aus (nicht innerhalb der Sandbox). Dies vermeidet NemoClaw-Netzwerkrichtlinien-Einschränkungen.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Der Sync-Daemon findet automatisch Sitzungen innerhalb aller laufenden OpenShell-Container.

### Optional: expliziter Sandbox-Name

Falls die automatische Erkennung nicht funktioniert, weise ClawMetry auf die richtige Sandbox hin:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Ausführung innerhalb der Sandbox (fortgeschritten)

Wenn du den Sync-Daemon **innerhalb** der OpenShell-Sandbox betreiben musst, füge diese Ausgangsregel zu deiner NemoClaw-Netzwerkrichtlinie hinzu, damit er die ClawMetry-Ingest-API erreichen kann:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Ja (Sync-Daemon zu Cloud) |
| `localhost:8900` | 8900 | HTTP | Ja (lokale Dashboard-Oberfläche) |
| Docker-Socket (`/var/run/docker.sock`) | - | Unix-Socket | Für Container-Sitzungserkennung |

Der Sync-Daemon führt nur ausgehende HTTPS-Aufrufe an `ingest.clawmetry.com` durch. Es sind keine eingehenden Ports erforderlich.

---

## Cloud-Deployment

Siehe den **[Cloud-Testleitfaden](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** für SSH-Tunnel, Reverse-Proxy und Docker.

## Tests

Dieses Projekt wird mit BrowserStack getestet.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetrie

ClawMetry sendet beim ersten Ausführen der `clawmetry`-CLI auf einem neuen Rechner einen einmaligen anonymen "Erstinstallations"-Ping an `https://app.clawmetry.com/api/install`. Wir nutzen dies, um Installationen zu zählen (die einzige Marketing-Kennzahl, die wir für ein Open-Source-Projekt haben) und um zu erfahren, welche Agenten-Frameworks unsere Nutzer installiert haben.

**Genau ein POST pro Installation**, der Folgendes enthält:

| Feld | Beispiel | Warum |
|---|---|---|
| `install_id` | zufällige UUID, gespeichert unter `~/.clawmetry/install_id` | Deduplizierung; nicht mit deiner E-Mail oder deinem api_key verknüpft |
| `version` | `0.12.167` | welche Versionen im Umlauf sind |
| `os` / `os_version` | `Darwin` / `25.3.0` | Plattform-Support-Prioritäten |
| `python` | `3.11.15` | Python-Versions-Supportmatrix |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | mit welchen Agenten wir uns als nächstes integrieren sollten |
| `is_ci` / `ci_provider` | `true` / `github_actions` | menschliche Installationen von CI-Rauschen trennen |

**Was wir NICHT senden**: IP (die Cloud leitet den Ländercode serverseitig aus der Anfrage ab und verwirft dann die IP), Hostname, Benutzername, Arbeitsbereichspfad, Dateiinhalte, dein api_key, deine E-Mail-Adresse, nichts Personenbezogenes oder Arbeitsbereichsspezifisches. Die übertragene Nutzlast ist in [`clawmetry/telemetry.py`](clawmetry/telemetry.py) nachvollziehbar.

**Deaktivieren** (jede dieser Optionen deaktiviert es dauerhaft):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ein Netzwerkfehler hier blockiert niemals den Start von `clawmetry` - der Ping wird in einem Daemon-Thread ohne Rückmeldung mit einem Timeout von 3 Sekunden gesendet.

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
  <strong>🦞 Beobachte, wie dein Agent denkt</strong><br>
  <sub>Erstellt von <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Teil des <a href="https://github.com/openclaw/openclaw">OpenClaw</a>-Ökosystems</sub>
</p>
