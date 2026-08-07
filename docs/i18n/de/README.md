<!-- i18n-src:7cfb63716507 -->
> Deutsch translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Sieh deinem Agenten beim Denken zu.** Echtzeit-Observability für **14 KI-Agent-Runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex und 10 weitere. Ein Dashboard für deine gesamte Agentenflotte.

> 🌐 **Lies dies auf:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mehr →](docs/i18n/)

Ein Befehl. Keine Konfiguration. Erkennt alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Öffnet sich unter **http://localhost:8900** und schon bist du fertig.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Funktioniert mit 14 Agent-Runtimes

ClawMetry begann als Observability-Lösung für OpenClaw und erfasst jetzt deine **gesamte Agentenflotte** in einem Dashboard, wobei jede Runtime auf deinem Rechner automatisch erkannt wird:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw und NemoClaw sind in der Open-Source-App kostenlos; die übrigen Runtimes werden mit ClawMetry Cloud oder einer selbst gehosteten Pro-Lizenz freigeschaltet. Wechsle die Runtime über die Kopfzeile, und jeder Tab, Kosten, Tokens, Tools, Traces, bezieht sich dann auf diese Runtime. Siehe **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** für die genaue Aufteilung zwischen kostenlos und kostenpflichtig, die Tier-Matrix, die Form von `/api/entitlement` und die `clawmetry license` CLI.

## Was du bekommst

- **Flow** — Live animiertes Diagramm, das zeigt, wie Nachrichten durch Kanäle, Brain, Tools und wieder zurück fließen
- **Overview** — Health-Checks, Aktivitäts-Heatmap, Sitzungszähler, Modellinformationen
- **Usage** — Token- und Kosten-Tracking mit täglichen/wöchentlichen/monatlichen Aufschlüsselungen
- **Sessions** — Aktive Agenten-Sitzungen mit Modell, Tokens, letzter Aktivität
- **Crons** — Geplante Jobs mit Status, nächstem Lauf, Dauer
- **Logs** — Farbcodiertes Echtzeit-Log-Streaming
- **Memory** — Durchsuche SOUL.md, MEMORY.md, AGENTS.md, tägliche Notizen
- **Transcripts** — Chat-Bubble-UI zum Lesen von Sitzungsverläufen
- **Alerts** — Budgetobergrenzen, Fehlerraten-Trigger, Erkennung von Offline-Agenten; Weiterleitung an Slack, Discord, PagerDuty, Telegram, E-Mail
- **Approvals** — Destruktive Löschvorgänge, Force-Pushes, DB-Mutationen, sudo, Paketinstallationen und Netzwerkaufrufe hinter einer Freigabe mit einem Klick absichern

## Screenshots

### 🧠 Brain — Live-Event-Stream des Agenten
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Token-Nutzung & Sitzungsübersicht
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Echtzeit-Feed der Tool-Aufrufe
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Kostenaufschlüsselung nach Modell & Sitzung
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Workspace-Datei-Browser
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Sicherheitslage & Audit-Log
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Budgetobergrenzen, Fehlerraten-Trigger, Webhooks zu Slack / Discord / PagerDuty / E-Mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Riskante Tool-Aufrufe hinter manueller Freigabe absichern; richtliniengestützte Schutzregeln
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blockierung vor der Ausführung für Claude Code** — ein Befehl installiert
einen PreToolUse-Hook, der passende Tool-Aufrufe *bevor* sie ausgeführt werden pausiert und auf
deine Entscheidung wartet (mit einem Tipp vom Handy aus möglich, wenn
[Cloud-Push-Benachrichtigungen](https://app.clawmetry.com/push) aktiviert sind):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Eine Ablehnung blockiert nur diesen einen Tool-Aufruf, der Agent behält seine Sitzung und kann
einen anderen Ansatz versuchen. Eine Freigabe per Handy überspringt die eigene
Berechtigungsabfrage von Claude Code (du hast bereits geantwortet). Nicht übereinstimmende Tools kosten ~40ms und
fallen zurück auf den normalen Berechtigungsablauf von Claude Code. Außerdem erhältst du eine
Push-Benachrichtigung, wenn Claude Code selbst auf dich wartet (`permission_prompt` /
`idle_prompt` Benachrichtigungen).

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

Die v2-React-App liegt in `frontend/` und wird unter `/v2` ausgeliefert, wenn der Flask-
Server mit aktiviertem v2 gestartet wird.

Verwende zwei Terminals während der Entwicklung:

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

Öffne `http://localhost:5173/v2/`. Vite leitet `/api`-Anfragen an
`http://localhost:8900` weiter, sodass die React-App mit dem lokalen Flask-Server sprechen kann,
ohne zusätzliche CORS-Konfiguration.

Um das Bundle zu erstellen, das mit dem Python-Paket ausgeliefert wird:

```bash
cd frontend
npm run build
```

Das Produktions-Bundle wird nach `clawmetry/static/v2/dist/` geschrieben.

## Runtime-/Agenten-Kompatibilität

ClawMetry beobachtet viele KI-Agent-Runtimes, nicht nur OpenClaw. Jede Nicht-OpenClaw-Runtime liefert einen dedizierten Reader-Adapter, der ihr natives Sitzungsformat in ClawMetrys einheitliche Datenstrukturen übersetzt; der Daemon nimmt sie in denselben DuckDB-Speicher + Cloud-Snapshot auf, versehen mit der Runtime-Kennzeichnung, und der Session-Replay-Tab zeigt einen **Runtime-Switcher**, sobald mehr als eine Runtime vorhanden ist. Siehe [`docs/compatibility.md`](docs/compatibility.md) für die vollständige Matrix und eine Anleitung zum Hinzufügen von Runtimes sowie [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) für die Einführung in die OpenClaw-Familie.

Nutzt du [Perplexitys numbat](https://github.com/perplexityai/numbat) Agent-Security-Tool? ClawMetry nimmt dessen Ergebnisse und Enforcement-Entscheidungen ohne weitere Einrichtung auf, siehe [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Runtime / Agent | Status | Anmerkungen |
|---|---|---|
| **OpenClaw** | Nativ | Referenz-Runtime, automatisch erkannt |
| **PicoClaw** | Beta-Adapter | Flaches `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Transcripts, Modell, Tool-Aufrufe. |
| **NanoClaw** | Beta-Adapter | SQLite pro Sitzung (`data/v2-sessions`). Transcripts + Nachrichtenzähler. |
| **Hermes** | Beta-Adapter | SQLite `~/.hermes/state.db`. Transcripts, Modell, Tokens/Kosten. |
| **Claude Code** | Beta-Adapter | JSONL `~/.claude/projects/.../<id>.jsonl`. Transcripts, Modell, Tool-Aufrufe + Thinking, Token-Nutzung. |
| **Codex** | Beta-Adapter | Rollout-JSONL `~/.codex/sessions/...`. Transcripts, Modell, Tool-Aufrufe, Token-Nutzung. |
| **Cursor** | Beta-Adapter | SQLite `state.vscdb`. Chat-/Composer-Transcripts, Modell. |
| **Aider** | Beta-Adapter | `.aider.chat.history.md` pro Projekt. Transcripts, Modell, Token-Zähler. |
| **Goose** | Beta-Adapter | SQLite `~/.local/share/goose`. Transcripts, Modell, Tool-Aufrufe, Token-Summen. |
| **opencode** | Beta-Adapter | SQLite `~/.local/share/opencode`. Transcripts, Modell, Tool-Aufrufe, Tokens + Kosten. |
| **Qwen Code** | Beta-Adapter | JSONL `~/.qwen/projects/.../chats`. Transcripts, Modell, Tool-Aufrufe, Token-Nutzung. |
| **Pi** | Beta-Adapter | JSONL `~/.pi/agent/sessions`. Transcripts, Modell, Tool-Aufrufe, Tokens + Kosten. |
| **Deep Agents** | Beta-Adapter | SQLite `~/.deepagents/.state/sessions.db`. Transcripts, Modell, Tool-Aufrufe, Tokens + Kosten. |
| **n8n** | Beta-Adapter | SQLite `~/.n8n/database.sqlite`. Workflow-Ausführungen, Node-Läufe, AI-Agent-Prompts, Modell + Tokens, sofern n8n sie erfasst. |
| **Antigravity** | Beta-Adapter | Brain-JSONL unter `~/.gemini/<flavor>/brain/`. Konversationen, Tool-Schritte, Thinking, Gemini-Token-Aufteilung pro Generierung + Kosten, Hintergrundgenerierungs-Verbrauch. |
| **GitHub Copilot** | Beta-Adapter | Copilot-CLI `events.jsonl` unter `~/.copilot/session-state/` + das `session-store.db` Nutzungsledger pro Aufruf. Konversationen, Tool-Aufrufe, Modell-Routing, Cache-bewusste Token-Aufteilung, vom Anbieter abgerechnete AI-Credit-Kosten. |
| **Grok** | Beta-Adapter | xAIs Grok Build CLI (Rust-Binary unter `~/.grok/bin/grok`): globales Event-Log `~/.grok/logs/unified.jsonl` + `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}` pro Sitzung. Konversationen, Token-Aufteilung pro Turn, Modell-Routing und die ausgehende Repo-Payload der CLI, die unter `~/.grok/upload_queue/` zwischengespeichert wird, damit du sehen kannst, was deinen Rechner verlassen hat. |

"Beta-Adapter" bedeutet, dass ClawMetry einen Reader für das echte On-Disk-Format dieser Runtime liefert, jeweils gebaut und verifiziert anhand einer echten Installation auf einer echten Maschine (siehe `tests/fixtures/runtimes/<rt>/`). Adapter sind read-only; jeder ist ehrlich darüber, was die jeweilige Runtime tatsächlich speichert (z. B. schreiben PicoClaw/NanoClaw/Cursor keine Token-Kosten auf die Festplatte). Laufen mehrere Runtimes auf einem Node, beschränkt der Runtime-Switcher die Sitzungsansicht auf eine für einen sauberen Deep-Dive.

## Beliebigen SDK-Agenten tracken — Out-Loop-Kostenzuordnung

Die oben genannten Runtimes schreiben alle Sitzungen auf die Festplatte. Dein eigener **Produktionsagent** — der, den du mit dem OpenAI Agents SDK, LangChain, dem Vercel AI SDK, LlamaIndex, E2B oder einer schlichten `httpx`-Schleife gebaut hast — tut das nicht. ClawMetrys Zero-Config-Interceptor erfasst dessen LLM-Aufrufe (Kosten, Tokens, Latenz, Fehler) trotzdem, indem er `httpx`/`requests` per Monkey-Patching modifiziert:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (oder die Umgebungsvariable `CLAWMETRY_SOURCE=support-agent`) versieht jeden Aufruf mit einer **benannten Quelle**, sodass jedes von dir betriebene Produkt als eigenständige, kostenmäßig zuordenbare Zeile in der Karte **🔌 Out-Loop-Quellen** im Dashboard unter Overview erscheint — Aufrufe, Anbieter, Latenz, Fehlerrate pro Agent. Keine Quelle gesetzt? Die Aufrufe werden trotzdem getrackt; die Karte bleibt dann einfach ausgeblendet.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Dies ist dieselbe Datenschicht, die auch die Runtime-Adapter speisen (DuckDB → Cloud-Snapshot), sodass Out-Loop-Quellen genauso wie alles andere mit dem Cloud-Dashboard synchronisiert werden, Ende-zu-Ende-verschlüsselt.

## OpenTelemetry — herstellerneutral, sende deine Traces überallhin

ClawMetry spricht **OpenTelemetry** in beide Richtungen, unter Verwendung der **GenAI Semantic Conventions**, sodass deine Agenten-Traces niemals an ein einziges Tool gebunden sind.

**Export** jeder Sitzung — LLM-Aufrufe, Tools, Sub-Agenten, Tokens, Kosten — als OTLP/HTTP-GenAI-Spans an einen beliebigen Collector (Datadog, Grafana, Honeycomb oder deinen eigenen OTel Collector):

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

**Ingest** — der eingebaute OTLP-Receiver nimmt Traces und Metriken von allem anderen unter `/v1/traces` und `/v1/metrics` entgegen (`pip install clawmetry[otel]` für Protobuf-Ingest).

Du bekommst das Zero-Config-, Local-First-ClawMetry-Dashboard **und** deine Daten in dem Backend, das dein Team bereits betreibt — kein Lock-in, kein zweiter zu installierender Agent.

## Konfiguration

Die meisten Leute brauchen keine Konfiguration. ClawMetry erkennt deinen Workspace, Logs, Sitzungen und Crons automatisch.

Falls du doch anpassen möchtest:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Alle Optionen: `clawmetry --help`

## Unterstützte Kanäle

ClawMetry zeigt Live-Aktivität für jeden von dir konfigurierten OpenClaw-Kanal an. Nur Kanäle, die in deiner `openclaw.json` tatsächlich eingerichtet sind, erscheinen im Flow-Diagramm, nicht konfigurierte werden automatisch ausgeblendet.

Klicke auf einen beliebigen Kanal-Node im Flow, um eine Live-Chat-Bubble-Ansicht mit Zählern für eingehende/ausgehende Nachrichten zu sehen.

| Kanal | Status | Live-Popup | Anmerkungen |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Vollständig | ✅ | Nachrichten, Statistiken, 10s Aktualisierung |
| 💬 **iMessage** | ✅ Vollständig | ✅ | Liest `~/Library/Messages/chat.db` direkt |
| 💚 **WhatsApp** | ✅ Vollständig | ✅ | Über WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Vollständig | ✅ | Über signal-cli |
| 🟣 **Discord** | ✅ Vollständig | ✅ | Erkennung von Guild + Kanal |
| 🟪 **Slack** | ✅ Vollständig | ✅ | Erkennung von Workspace + Kanal |
| 🌐 **Webchat** | ✅ Vollständig | ✅ | Sitzungen der eingebauten Web-UI |
| 📡 **IRC** | ✅ Vollständig | ✅ | Terminal-artige Bubble-UI |
| 🍏 **BlueBubbles** | ✅ Vollständig | ✅ | iMessage über BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Vollständig | ✅ | Über Chat-API-Webhooks |
| 🟣 **MS Teams** | ✅ Vollständig | ✅ | Über Teams-Bot-Plugin |
| 🔷 **Mattermost** | ✅ Vollständig | ✅ | Selbst gehosteter Team-Chat |
| 🟩 **Matrix** | ✅ Vollständig | ✅ | Dezentral, mit E2EE-Unterstützung |
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

> **Hinweis:** Wenn du in Docker läufst, binde die Daten- und Log-Verzeichnisse deines Agenten ein (z. B. `~/.openclaw`, `~/.claude`, `~/.codex`), damit ClawMetry dein Setup automatisch erkennen kann.

## Voraussetzungen

- Python 3.8+
- Flask (wird automatisch über pip installiert)
- Eine KI-Agent-Runtime auf demselben Rechner: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok oder QM (oder gemountete Volumes für Docker)
- Linux oder macOS

## NemoClaw-/OpenShell-Unterstützung

ClawMetry erkennt automatisch [NemoClaw](https://github.com/NVIDIA/NemoClaw) — NVIDIAs Enterprise-Sicherheitswrapper für OpenClaw, der Agenten in sandboxed OpenShell-Containern ausführt.

In den meisten Fällen ist keine zusätzliche Konfiguration nötig. Der Sync-Daemon entdeckt Sitzungsdateien automatisch, egal ob sie unter `~/.openclaw/` auf dem Host oder innerhalb eines OpenShell-Containers liegen.

### So funktioniert es

ClawMetry erkennt NemoClaw auf zwei Arten:

1. **Binärerkennung** — prüft auf die `nemoclaw`-CLI und führt `nemoclaw status` aus, um Sandbox-Informationen zu erhalten
2. **Container-Erkennung** — durchsucht laufende Docker-Container nach `openshell`-, `nemoclaw`- oder `ghcr.io/nvidia/`-Images und liest Sitzungen dann über Volume-Mounts oder `docker cp`

Aus NemoClaw-Containern synchronisierte Sitzungsdateien werden im Cloud-Dashboard mit `runtime=nemoclaw` und `container_id`-Metadaten gekennzeichnet, sodass du sie auf einen Blick von Standard-OpenClaw-Sitzungen unterscheiden kannst.

### Empfohlenes Setup: Sync-Daemon auf dem HOST

Für die beste Erfahrung führe ClawMetrys Sync-Daemon auf der **Host-Maschine** aus (nicht innerhalb der Sandbox). Damit umgehst du Einschränkungen durch die NemoClaw-Netzwerkrichtlinie.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Der Sync-Daemon findet Sitzungen innerhalb laufender OpenShell-Container automatisch.

### Optional: expliziter Sandbox-Name

Falls die automatische Erkennung nicht funktioniert, verweise ClawMetry auf die richtige Sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Ausführung innerhalb der Sandbox (fortgeschritten)

Falls du den Sync-Daemon **innerhalb** der OpenShell-Sandbox ausführen musst, füge deiner NemoClaw-Netzwerkrichtlinie diese Egress-Regel hinzu, damit er die ClawMetry-Ingest-API erreichen kann:

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
| Docker-Socket (`/var/run/docker.sock`) | — | Unix-Socket | Für die Container-Sitzungserkennung |

Der Sync-Daemon führt ausschließlich ausgehende HTTPS-Aufrufe zu `ingest.clawmetry.com` aus. Es sind keine eingehenden Ports erforderlich.

---

## Cloud-Deployment

Siehe den **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** für SSH-Tunnel, Reverse-Proxy und Docker.

## Testing

Dieses Projekt wird mit BrowserStack getestet.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetrie

ClawMetry sendet anonyme Install-Lifecycle-Pings an
`https://app.clawmetry.com/api/install`: einen `install`-Ping beim ersten
Ausführen der `clawmetry`-CLI auf einer neuen Maschine, einen `update`-Ping
beim ersten Lauf nach einem Upgrade auf eine neue Version und einen `onboarded`-
Ping, wenn du die Onboarding-Auswahl im Dashboard abschließt. Damit zählen wir
echte Installationen (rohe PyPI-Download-Zahlen bestehen zu ~98% aus Mirrors, CI
und Auto-Update-Re-Downloads) und erfahren, welche Agenten-Frameworks und
-Versionen tatsächlich im Einsatz sind.

**Höchstens ein POST pro Lifecycle-Event pro Version**, mit folgendem Inhalt:

| Feld | Beispiel | Warum |
|---|---|---|
| `install_id` | zufällige UUID, gespeichert unter `~/.clawmetry/install_id` | Deduplizierung; anonym, bis du Cloud-Sync explizit verbindest (der authentifizierte Daemon-Heartbeat trägt sie danach mit und verknüpft diese Installation mit deinem Konto) |
| `event` | `install` / `update` / `onboarded` | Neuinstallation vs. Upgrade einer bestehenden |
| `version` | `0.12.167` | welche Versionen im Einsatz sind |
| `os` / `os_version` | `Darwin` / `25.3.0` | Prioritäten der Plattformunterstützung |
| `python` | `3.11.15` | Unterstützungsmatrix für Python-Versionen |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | mit welchen Agenten wir uns als Nächstes integrieren sollten |
| `is_ci` / `ci_provider` | `true` / `github_actions` | Trennung von menschlichen Installationen und CI-Rauschen |

**Was wir NICHT senden**: IP (die Cloud leitet den Ländercode serverseitig
aus der Anfrage ab und verwirft die IP anschließend), Hostname, Benutzername, Workspace-
Pfad, Dateiinhalte, deinen api_key, deine E-Mail-Adresse, nichts PII-Bezogenes oder
Workspace-Spezifisches. Die Übertragungs-Payload ist auditierbar in
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Opt-out** (jede dieser Optionen deaktiviert es dauerhaft):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Ein Netzwerkfehler blockiert hier niemals das Ausführen von `clawmetry` — der
Ping ist Fire-and-Forget auf einem Daemon-Thread mit 3s Timeout.

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
  <sub>Erstellt von <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Teil des <a href="https://github.com/openclaw/openclaw">OpenClaw</a>-Ökosystems</sub>
</p>
