<!-- i18n-src:56ff57310588 -->
> Deutsch translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Sieh deinem Agenten beim Denken zu.** Echtzeit-Observability für [OpenClaw](https://github.com/openclaw/openclaw) KI-Agenten.

> 🌐 **Lies dies auf:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mehr →](docs/i18n/)

Ein Befehl. Null Konfiguration. Erkennt alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Öffnet sich unter **http://localhost:8900** und du bist fertig.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Was du bekommst

- **Flow** — Live-animiertes Diagramm, das zeigt, wie Nachrichten durch Kanäle, Gehirn, Tools und zurück fließen
- **Overview** — Health-Checks, Aktivitäts-Heatmap, Sitzungsanzahlen, Modellinformationen
- **Usage** — Token- und Kostenverfolgung mit täglichen/wöchentlichen/monatlichen Aufschlüsselungen
- **Sessions** — Aktive Agenten-Sitzungen mit Modell, Tokens, letzter Aktivität
- **Crons** — Geplante Jobs mit Status, nächster Ausführung, Dauer
- **Logs** — Farbcodiertes Log-Streaming in Echtzeit
- **Memory** — Durchsuche SOUL.md, MEMORY.md, AGENTS.md, tägliche Notizen
- **Transcripts** — Chat-Bubble-Oberfläche zum Lesen von Sitzungsverläufen
- **Alerts** — Budget-Obergrenzen, Auslöser bei Fehlerrate, Erkennung offline gegangener Agenten; leitet an Slack, Discord, PagerDuty, Telegram, E-Mail weiter
- **Approvals** — Sichere destruktive Löschvorgänge, Force-Pushes, DB-Mutationen, sudo, Paketinstallationen und Netzwerkaufrufe hinter einer Freigabe mit einem Klick ab

## Screenshots

### 🧠 Brain — Live-Ereignisstrom des Agenten
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token-Nutzung & Sitzungsübersicht
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Echtzeit-Feed der Tool-Aufrufe
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Kostenaufschlüsselung nach Modell & Sitzung
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Datei-Browser für den Workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Sicherheitslage & Audit-Log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budget-Obergrenzen, Auslöser bei Fehlerrate, Webhooks an Slack / Discord / PagerDuty / E-Mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Sichere riskante Tool-Aufrufe hinter manueller Freigabe ab; richtliniengestützte Schutzregeln
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

## Entwicklung des v2-Frontends

Die v2-React-App liegt in `frontend/` und wird unter `/v2` bereitgestellt, wenn der Flask-Server mit aktiviertem v2 gestartet wird.

Nutze beim Entwickeln zwei Terminals:

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

Öffne `http://localhost:5173/v2/`. Vite leitet `/api`-Anfragen an `http://localhost:8900` weiter, sodass die React-App ohne zusätzliche CORS-Einrichtung mit dem lokalen Flask-Server kommunizieren kann.

So baust du das Bundle, das mit dem Python-Paket ausgeliefert wird:

```bash
cd frontend
npm run build
```

Das Produktions-Bundle wird nach `clawmetry/static/v2/dist/` geschrieben.

## Laufzeit-/Agenten-Kompatibilität

ClawMetry beobachtet viele KI-Agenten-Laufzeiten, nicht nur OpenClaw. Jede Laufzeit, die nicht OpenClaw ist, liefert einen dedizierten Reader-Adapter, der ihr natives Sitzungsformat in die vereinheitlichten Formen von ClawMetry übersetzt; der Daemon ingestiert sie in denselben DuckDB-Store + Cloud-Snapshot, getaggt mit der Laufzeit, und der Session-Replay-Tab zeigt einen **Laufzeit-Umschalter**, wenn mehr als eine vorhanden ist. Siehe [`docs/compatibility.md`](docs/compatibility.md) für die vollständige Matrix + eine Anleitung zum Hinzufügen von Laufzeiten und [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) für die Einführung in die OpenClaw-Familie.

| Laufzeit / Agent | Status | Hinweise |
|---|---|---|
| **OpenClaw** | Nativ | Referenzlaufzeit, automatisch erkannt |
| **PicoClaw** | Beta-Adapter | Flaches `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transkripte, Modell, Tool-Aufrufe. |
| **NanoClaw** | Beta-Adapter | SQLite pro Sitzung (`data/v2-sessions`). Transkripte + Nachrichtenanzahlen. |
| **Hermes** | Beta-Adapter | SQLite `~/.hermes/state.db`. Transkripte, Modell, Tokens/Kosten. |
| **Claude Code** | Beta-Adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkripte, Modell, Tool-Aufrufe + Thinking, Token-Nutzung. |
| **Codex** | Beta-Adapter | Rollout-JSONL `~/.codex/sessions/...`. Transkripte, Modell, Tool-Aufrufe, Token-Nutzung. |
| **Cursor** | Beta-Adapter | SQLite `state.vscdb`. Chat-/Composer-Transkripte, Modell. |
| **Aider** | Beta-Adapter | `.aider.chat.history.md` pro Projekt. Transkripte, Modell, Token-Anzahlen. |
| **Goose** | Beta-Adapter | SQLite `~/.local/share/goose`. Transkripte, Modell, Tool-Aufrufe, Token-Summen. |

"Beta-Adapter" bedeutet, dass ClawMetry einen Reader für das echte On-Disk-Format dieser Laufzeit ausliefert, jeweils gegen eine echte Installation auf einer echten Maschine gebaut + verifiziert (siehe `tests/fixtures/runtimes/<rt>/`). Adapter sind schreibgeschützt; jeder ist ehrlich darüber, was seine Laufzeit tatsächlich speichert (z. B. schreiben PicoClaw/NanoClaw/Cursor keine Token-Kosten auf die Festplatte). Wenn mehrere Laufzeiten auf einem Knoten laufen, beschränkt der Laufzeit-Umschalter die Sitzungsansicht auf eine einzige für eine saubere Detailanalyse.

## OpenTelemetry — herstellerneutral, sende deine Traces überallhin

ClawMetry spricht **OpenTelemetry** in beide Richtungen und verwendet die **GenAI-Semantikkonventionen**, sodass deine Agenten-Traces niemals an ein einziges Tool gebunden sind.

**Exportiere** jede Sitzung — LLM-Aufrufe, Tools, Sub-Agenten, Tokens, Kosten — als OTLP/HTTP-GenAI-Spans an jeden beliebigen Collector (Datadog, Grafana, Honeycomb oder deinen eigenen OpenTelemetry Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Auth-Header und Poll-Intervall sind optionale Umgebungsvariablen:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Ingest** — der eingebaute OTLP-Empfänger akzeptiert Traces und Metriken von allem anderen unter `/v1/traces` und `/v1/metrics` (`pip install clawmetry[otel]` für Protobuf-Ingest).

Du bekommst das Zero-Config-, Local-First-ClawMetry-Dashboard **und** deine Daten in dem Backend, das dein Team bereits betreibt — kein Lock-in, kein zweiter Agent zu installieren.

## Konfiguration

Die meisten Menschen brauchen keine Konfiguration. ClawMetry erkennt deinen Workspace, Logs, Sitzungen und Crons automatisch.

Falls du doch anpassen musst:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Alle Optionen: `clawmetry --help`

## Unterstützte Kanäle

ClawMetry zeigt Live-Aktivität für jeden OpenClaw-Kanal, den du konfiguriert hast. Nur Kanäle, die tatsächlich in deiner `openclaw.json` eingerichtet sind, erscheinen im Flow-Diagramm — nicht konfigurierte werden automatisch ausgeblendet.

Klicke auf einen beliebigen Kanalknoten im Flow, um eine Live-Chat-Bubble-Ansicht mit eingehenden/ausgehenden Nachrichtenanzahlen zu sehen.

| Kanal | Status | Live-Popup | Hinweise |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Vollständig | ✅ | Nachrichten, Statistiken, Aktualisierung alle 10 s |
| 💬 **iMessage** | ✅ Vollständig | ✅ | Liest `~/Library/Messages/chat.db` direkt |
| 💚 **WhatsApp** | ✅ Vollständig | ✅ | Über WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Vollständig | ✅ | Über signal-cli |
| 🟣 **Discord** | ✅ Vollständig | ✅ | Erkennung von Guild + Kanal |
| 🟪 **Slack** | ✅ Vollständig | ✅ | Erkennung von Workspace + Kanal |
| 🌐 **Webchat** | ✅ Vollständig | ✅ | Eingebaute Web-UI-Sitzungen |
| 📡 **IRC** | ✅ Vollständig | ✅ | Bubble-UI im Terminal-Stil |
| 🍏 **BlueBubbles** | ✅ Vollständig | ✅ | iMessage über BlueBubbles-REST-API |
| 🔵 **Google Chat** | ✅ Vollständig | ✅ | Über Chat-API-Webhooks |
| 🟣 **MS Teams** | ✅ Vollständig | ✅ | Über Teams-Bot-Plugin |
| 🔷 **Mattermost** | ✅ Vollständig | ✅ | Selbstgehosteter Team-Chat |
| 🟩 **Matrix** | ✅ Vollständig | ✅ | Dezentral, E2EE-Unterstützung |
| 🟢 **LINE** | ✅ Vollständig | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Vollständig | ✅ | Dezentrale NIP-04-DMs |
| 🟣 **Twitch** | ✅ Vollständig | ✅ | Chat über IRC-Verbindung |
| 🔷 **Feishu/Lark** | ✅ Vollständig | ✅ | WebSocket-Ereignisabonnement |
| 🔵 **Zalo** | ✅ Vollständig | ✅ | Zalo-Bot-API |

> **Automatische Erkennung:** ClawMetry liest deine `~/.openclaw/openclaw.json` und rendert nur die Kanäle, die du tatsächlich konfiguriert hast. Keine manuelle Einrichtung erforderlich.

## Docker-Bereitstellung

Willst du ClawMetry in einem Container ausführen? Kein Problem! 🐳

**Schnellstart mit Docker:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or with your OpenClaw workspace mounted
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

> **Hinweis:** Wenn du in Docker läufst, stelle sicher, dass du deinen OpenClaw-Workspace und die Log-Verzeichnisse einbindest, damit ClawMetry dein Setup automatisch erkennen kann.

## Anforderungen

- Python 3.8+
- Flask (wird automatisch über pip installiert)
- OpenClaw läuft auf derselben Maschine (oder eingebundene Volumes für Docker)
- Linux oder macOS

## NemoClaw / OpenShell-Unterstützung

ClawMetry erkennt automatisch [NemoClaw](https://github.com/NVIDIA/NemoClaw) — NVIDIAs Enterprise-Sicherheits-Wrapper für OpenClaw, der Agenten in gesandboxten OpenShell-Containern ausführt.

In den meisten Fällen ist keine zusätzliche Konfiguration nötig. Der Sync-Daemon entdeckt Sitzungsdateien automatisch, egal ob sie in `~/.openclaw/` auf dem Host oder in einem OpenShell-Container liegen.

### So funktioniert es

ClawMetry erkennt NemoClaw auf zwei Arten:

1. **Binärerkennung** — prüft auf die `nemoclaw`-CLI und führt `nemoclaw status` aus, um Sandbox-Informationen zu erhalten
2. **Container-Erkennung** — durchsucht laufende Docker-Container nach `openshell`-, `nemoclaw`- oder `ghcr.io/nvidia/`-Images und liest dann Sitzungen über Volume-Mounts oder `docker cp`

Sitzungsdateien, die von NemoClaw-Containern synchronisiert werden, sind im Cloud-Dashboard mit `runtime=nemoclaw`- und `container_id`-Metadaten getaggt, sodass du sie auf einen Blick von standardmäßigen OpenClaw-Sitzungen unterscheiden kannst.

### Empfohlenes Setup: Sync-Daemon auf dem HOST

Für das beste Erlebnis solltest du den Sync-Daemon von ClawMetry auf der **Host-Maschine** ausführen (nicht innerhalb der Sandbox). Das vermeidet die Netzwerkrichtlinien-Beschränkungen von NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Der Sync-Daemon findet automatisch Sitzungen in allen laufenden OpenShell-Containern.

### Optional: expliziter Sandbox-Name

Wenn die automatische Erkennung nicht funktioniert, weise ClawMetry auf die richtige Sandbox hin:

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
| Docker-Socket (`/var/run/docker.sock`) | — | Unix-Socket | Für die Entdeckung von Container-Sitzungen |

Der Sync-Daemon stellt nur ausgehende HTTPS-Aufrufe an `ingest.clawmetry.com`. Es sind keine eingehenden Ports erforderlich.

---

## Cloud-Bereitstellung

Siehe den **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** für SSH-Tunnel, Reverse Proxy und Docker.

## Testen

Dieses Projekt wird mit BrowserStack getestet.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetrie

ClawMetry sendet einen einzigen anonymen "First Run"-Ping an `https://app.clawmetry.com/api/install`, wenn du die `clawmetry`-CLI zum ersten Mal auf einer neuen Maschine ausführst. Wir nutzen dies, um Installationen zu zählen (die einzige Marketing-Metrik, die wir für ein OSS-Projekt haben) und um zu erfahren, welche Agenten-Frameworks unsere Nutzer installiert haben.

**Genau ein POST pro Installation**, der Folgendes enthält:

| Feld | Beispiel | Warum |
|---|---|---|
| `install_id` | zufällige UUID, gespeichert unter `~/.clawmetry/install_id` | Deduplizierung; nicht mit deiner E-Mail oder deinem api_key verknüpft |
| `version` | `0.12.167` | welche Versionen im Umlauf sind |
| `os` / `os_version` | `Darwin` / `25.3.0` | Prioritäten der Plattformunterstützung |
| `python` | `3.11.15` | Support-Matrix der Python-Version |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | mit welchen Agenten wir als Nächstes integrieren sollten |
| `is_ci` / `ci_provider` | `true` / `github_actions` | menschliche Installationen vom CI-Rauschen trennen |

**Was wir NICHT senden**: IP (die Cloud leitet den Ländercode serverseitig aus der Anfrage ab und verwirft dann die IP), Hostname, Benutzername, Workspace-Pfad, Dateiinhalte, deinen api_key, deine E-Mail, irgendetwas Personenbezogenes oder Workspace-Spezifisches. Die Wire-Payload ist in [`clawmetry/telemetry.py`](clawmetry/telemetry.py) prüfbar.

**Abmelden** (jede einzelne dieser Optionen deaktiviert es dauerhaft):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ein Netzwerkfehler hier blockiert niemals die Ausführung von `clawmetry` — der Ping ist "fire-and-forget" auf einem Daemon-Thread mit einem Timeout von 3 s.

## Star History

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
  <strong>🦞 Sieh deinem Agenten beim Denken zu</strong><br>
  <sub>Gebaut von <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Teil des <a href="https://github.com/openclaw/openclaw">OpenClaw</a>-Ökosystems</sub>
</p>
