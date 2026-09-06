<!-- i18n-src:88be2deff5d5 -->
> Deutsch translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Sieh zu, wie dein Agent denkt.** Echtzeit-Observability für **30 KI-Agent-Runtimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex und 26 weitere. Ein Dashboard für deine gesamte Agenten-Flotte.

> 🌐 **Lies dies auf:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mehr →](docs/i18n/)

Ein Befehl. Keine Konfiguration. Erkennt alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Öffnet sich unter **http://localhost:8900**. Keine Konfiguration nötig: Es findet die Agent-Runtimes, die du bereits hast, liest sie nur lesend aus und ändert nichts daran, wie sie laufen.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Funktioniert mit 30 Agent-Runtimes

**Kostenlos in der Open-Source-App:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Auf einem kostenpflichtigen Plan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Jede Runtime bekommt dasselbe Dashboard. Läuft mehrere gleichzeitig, skaliert der Umschalter im Header jeden Tab auf eine davon um.

Hast du deinen eigenen Agenten mit einem SDK gebaut statt mit einer Runtime? Der Interceptor verfolgt auch dessen LLM-Aufrufe. Siehe [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Was du bekommst

- **Sitzungen & Transkripte**: was jeder Agent getan hat, Zug um Zug, mit Wiedergabe
- **Kosten & Tokens**: pro Runtime, Modell, Sitzung und Tag, mit Anomalie-Markierungen
- **Flow**: Live-Diagramm der Nachrichten, die durch Kanäle, Modelle und Tools fließen
- **Brain**: der Strom der Reasoning- und Tool-Aufruf-Ereignisse in Echtzeit
- **Context-Blowout**: pro Anbieter dimensionierte Fenster-Auslastung, Kompaktierung vs. erzwungener Überlauf, plus eine Übersicht pro Runtime, was wir *nicht* sehen können ([wie](docs/CONTEXT_BLOWOUT.md))
- **Memory & Skills**: die Dateien und Skills, die jede Runtime tatsächlich geladen hat
- **Health & Logs**: Speicherplatz, Arbeitsspeicher, Fehlerraten, Rate-Limits, Live-Log-Stream
- **Alerts**: Budgetgrenzen, Fehlerspitzen, Agent-offline, weitergeleitet an Slack, Discord, PagerDuty, Telegram, E-Mail
- **Freigaben**: riskante Tool-Aufrufe *vor* der Ausführung pausieren und vom Handy aus freigeben ([wie](docs/APPROVALS.md))

## Context-Blowout, und was das Beobachten kostet

Zwei Fragen, die es wert sind, geklärt zu werden, bevor du irgendeinem Tool zum Agenten-Vergleich vertraust.

**Wie wird Context-Window-Blowout über verschiedene Runtimes hinweg behandelt?**

Ein Auslastungsprozentsatz ist nur so ehrlich wie das, wodurch er geteilt wird. ClawMetry bemisst das Fenster pro Anbieter anhand [einer Tabelle, die du lesen und per PR ändern kannst](clawmetry/context_windows.py), die Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama und GLM abdeckt. Es misst nicht alle 30 Runtimes mit dem Lineal eines einzigen Anbieters. Das ist wichtig: Ein 300K-GPT-5-Turn, gemessen an Anthropics 200K, liest sich als ">100%, blown", obwohl er tatsächlich bei 75% von GPT-5s 400K liegt. Dasselbe Lineal versteckt einen wirklich übergelaufenen 130K-DeepSeek-Turn als komfortable 65%.

Jedes Fenster wird mit seiner Herkunft ausgeliefert: `model_table`, `explicit_marker`, `observed_floor`, oder ein ehrliches `default`, wenn wir das Modell nicht kennen. Eine Anzeige, die auf einer Vermutung basiert, wird niemals mit derselben Autorität dargestellt wie eine, die auf einem Nachschlagewert basiert.

ClawMetry kann Kompaktierungs-Ereignisse nur bei manchen Runtimes sehen. Deshalb meldet `GET /api/context-coverage` pro Runtime, ob eine **Null bedeutet "sauber gelaufen" oder "wir sind blind"**. Eine `0`, die eigentlich blind bedeutet, sagt das auch so. [Vollständige Details](docs/CONTEXT_BLOWOUT.md)

**Was kostet die Instrumentierung?**

| Pfad | Zusätzlich für deinen Agenten | Standard? |
|---|---|---|
| Session-Datei-Tailing (alle 30 Runtimes) | **0**. Separater Prozess, kein ClawMetry-Code in deinem Agenten | an |
| HTTP-Interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** pro LLM-Aufruf, bzw. 0,009% eines 5s-Aufrufs | aus |
| Pre-Tool-Hook-Gate (warmer Cache) | **+44 ms** pro gegatetem Tool-Aufruf, über einer 36-ms-Interpreter-Grundlast | aus |
| Enforcement-Proxy | **+9,7 ms** pro LLM-Aufruf | aus |

Kosten für den Daemon-Host: **2.762 Ereignisse/Sek.** Ingest, **710 Bytes/Ereignis** auf der Festplatte (67,7 MB pro 100.000 Ereignisse), und **~12% eines Kerns** dauerhaft bei einer stark ausgelasteten Installation. Diese letzte Zahl liegt über unserem eigenen erklärten Budget von 5-10%, weshalb sie als zu behebender Fehler veröffentlicht wird, statt sie von der Seite zu lassen.

Gemessen auf einem Apple M2 Pro mit `benchmarks/overhead.py`. Der Test-Harness führt jede Bedingung in einem separaten Prozess aus, wechselt deren Reihenfolge ab und **verweigert die Ausgabe einer Zahl, wenn sich die Durchläufe im Vorzeichen widersprechen**. Führe ihn in einer Minute auf deiner eigenen Maschine aus:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Jeder Pfad wird gemessen, einschließlich der Hook-Gates und des Enforcement-Proxys, und der Harness läuft in CI unter Linux, macOS und Windows. Zwei Ergebnisse, die man kennen sollte: Der Proxy kostet unter Windows etwa siebenmal mehr als unter Linux, und der Daemon nutzt derzeit dauerhaft etwa 12% eines Kerns, über unserem eigenen 5-10%-Budget. Die Rohdaten als JSON, die Methode und was noch nicht gemessen ist, stehen in [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Preise

| Plan | Was er abdeckt | Preis |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, volles Dashboard, nur lokal | $0 |
| **Starter** | Jede weitere oben genannte Runtime, Flottenansicht, Cloud-Sync | $9 pro Node / Monat |
| **Pro** | Starter plus Steuerung und Evaluation: Freigaben, Tool-Risikorichtlinien, Evals, Anomalieerkennung, Kostenoptimierer, OTel-Export, manipulationssicheres Audit-Log | $19 pro Node / Monat |

Jahrespläne, Enterprise und die aktuellen Zahlen findest du unter
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Selbst gehostete Lizenzschlüssel funktionieren ohne die Cloud (`clawmetry license`). Die genaue Aufteilung zwischen kostenlos und kostenpflichtig steht in
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Deine Daten bleiben auf deinem Rechner

ClawMetry liest lokale Sitzungsdateien und Logs. **Es verlassen keine Sitzungsdaten deine Maschine, es sei denn, du führst `clawmetry connect` aus** — keine Prompts, Antworten, Tool-Argumente, Dateiinhalte oder Log-Zeilen. Wenn du dich verbindest, wird der Snapshot Ende-zu-Ende verschlüsselt mit einem Schlüssel, der deine Maschine nie verlässt, und in deinem Browser entschlüsselt. Wenn ein Node keinen Schlüssel hat, wird der Upload übersprungen statt unverschlüsselt gesendet, und keine Server-Antwort kann das abschalten.

Zwei Dinge laufen standardmäßig bereits, bevor du dich verbindest, beide opt-out und keines mit Sitzungsdaten: ein anonymer Installations-Ping und eine Versionsprüfung gegen PyPI. Eine Standardinstallation schlägt außerdem einmalig deine öffentliche IP für eine Start-Banner-Zeile nach. Jedes Ziel, was es überträgt und wie man es abschaltet, ist aufgelistet in
[docs/EGRESS.md](docs/EGRESS.md); selbst gehostete, umgeleitete und abgeschottete (air-gapped) Installationen tätigen überhaupt keine optionalen ausgehenden Aufrufe.

Die Entschlüsselung findet in deinem Browser statt, in Code, den wir dir liefern. Das war früher ein Versprechen; jetzt ist es etwas, das du überprüfen kannst. Jede Zeile, die deinen Schlüssel berührt, befindet sich in einer einzigen lesbaren Datei, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), die im Wheel enthalten ist und unverändert ausgeliefert wird, gepinnt mit einem Subresource-Integrity-Hash. Um zu prüfen, dass der Browser das ausführt, was wir veröffentlicht haben:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Was das nicht beweist: Wir liefern die Seite aus, die die Datei lädt, also könnten wir auch eine andere Seite ausliefern. Integrity-Hashes schützen dich vor einem kompromittierten CDN, nicht vor dem Anbieter selbst. Was du gewinnst, ist, dass jede Manipulation absichtlich, im Seitenquelltext sichtbar und anders sein muss als ein Artefakt auf PyPI, das jeder abrufen kann. Selbst-Hosting oder eine reine Lokal-Installation beseitigt die Abhängigkeit vollständig.

## Installation

```bash
pip install clawmetry     # dann: clawmetry
```

Oder der Einzeiler: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Benötigt Python 3.8+ unter macOS, Linux oder Windows, und mindestens eine Agent-Runtime auf derselben Maschine. Docker-Anleitung: [docs/DOCKER.md](docs/DOCKER.md).

Oder lass den Agenten die Einrichtung für dich übernehmen. Der [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)-Skill bringt Claude Code, Codex, Cursor, Gemini CLI, Copilot oder OpenCode bei, ClawMetry zu installieren, zu berichten, was die Agenten auf der Maschine gerade tun und ausgeben, eine Sitzung auf Anfrage zu stoppen und riskante Tool-Aufrufe zur Freigabe zurückzuhalten:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokumentation

| | |
|---|---|
| [Runtime-Kompatibilität](docs/compatibility.md) | Was jeder Adapter liest, und wie man eine Runtime hinzufügt |
| [Context-Blowout](docs/CONTEXT_BLOWOUT.md) | Fenster pro Anbieter, Kompaktierung vs. Überlauf, Abdeckung pro Runtime |
| [Overhead](docs/OVERHEAD.md) | Was Instrumentierung kostet, gemessen, mit dem Harness zum Reproduzieren |
| [Entitlements](docs/ENTITLEMENTS.md) | Kostenlos vs. kostenpflichtig, Tier-Matrix, Lizenz-CLI |
| [Freigaben & Richtlinien](docs/APPROVALS.md) | Gating vor der Ausführung, Risikobewertung, Freigaben vom Handy |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Traces überallhin exportieren, OTLP von überall einlesen |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end-to-end, mit lauffähigen Beispielen |
| [SDK-Tracking](docs/SDK_TRACKING.md) | Kostenzuordnung für selbst gebaute Agenten |
| [Chat-Kanäle](docs/CHANNELS.md) | Die im Flow angezeigten Chat-Adapter |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed-Setups für NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Image, Compose, Volume-Mounts |
| [Architektur](ARCHITECTURE.md) · [Entwicklung](docs/DEVELOPMENT.md) | Wie es intern funktioniert; Ausführen aus dem Quellcode |
| [Telemetrie](docs/TELEMETRY.md) | Die anonymen Installations- und Desktop-Öffnungs-Pings, und wie man sie abschaltet |

## Screenshots

Jede Zahl unten stammt von einer echten Maschine, nur lesend, ohne irgendetwas vorab einzupflanzen.

**Es sagt dir, wenn etwas falsch läuft, nicht nur, was passiert ist.**
Zwei Anomalie-Banner oben: Ausgaben laufen beim 7-Fachen des Tagesdurchschnitts, und eine 4,2-fache Kostenspitze. Darunter, 324 von 667 aktuellen Sitzungen tragen ein Verschwendungssignal, aufgeschlüsselt nach Ursache.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Es zeigt dir, wohin das Geld geflossen ist, in jedem Zeitfenster.**
$252,47 heute, $513,15 diese Woche, $1.312,92 diesen Monat, jeweils mit den zugrunde liegenden Tokens und wie viel davon dein Abonnement bereits abdeckt. Darunter etwa $1.128/Monat als rückgewinnbar aufgeschlüsselt und bereits $17.256/Monat durch Cache-Wiederverwendung eingespart.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Es zeichnet auf, wie aus einer Nachricht eine Antwort wird.**
Das Live-Flow-Diagramm: du, der Kanal, über den sie eingegangen ist, das Gateway, das gerade antwortende Modell und jedes Tool, auf das es zugegriffen hat. Knoten leuchten auf, während die Arbeit durch sie hindurch fließt.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Jeder Agent auf der Maschine, in einer einzigen Tabelle.**
Was er ausführt, was er in den letzten 24 Stunden und über seine gesamte Lebensdauer gekostet hat, wann er zuletzt gesehen wurde, wem er gehört, und ob ein Abonnement die Rechnung deckt. 14 Agenten hier, 3 Sitzungen aktiv, 13 ruhig.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Es zeigt, wo die Zeit und das Geld eines Turns hingeflossen sind, Tool für Tool.**
Ein Turn einer echten Sitzung: 11 Tools in 11,2 Minuten für $1,16. Jeder Bash-Aufruf und jeder Modellaufruf bekommt seinen eigenen Balken auf der Zeitleiste, sodass der Befehl, der 4,1 Minuten lief, und der, der 226 ms lief, auf einen Blick unterscheidbar sind.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Es bewertet die Arbeit, nicht nur die Ausgaben.**
Ein A diese Woche: 54 Aufgaben kamen sauber zurück, 2 unsaubere kosteten $48,57, und die Läufe mit zu wenig Aktivität, um sie zu beurteilen, werden nicht in die Bewertung einbezogen, statt als Erfolge gezählt zu werden. Jeder unsaubere Lauf verlinkt zu seiner Trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Es zeigt, warum sich das Context-Window immer weiter füllt.**
715K von einem 1M-Token-Fenster beim letzten Turn, ein Höchststand von 83,3%, 4 Kompaktierungen, die alle proaktiv ausgelöst wurden statt bei einem Überlauf, und die Auslastung jedes dahinterliegenden Turns.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Die Erkennung läuft, ohne dass du irgendetwas konfigurierst.**
Die eingebauten Detektoren sind ab der Installation aktiv: Agent wurde still, Telemetrie-Feed gestoppt, Kostenspitze, Token-Burst, steigende Fehlerraten, Fehlerspitze, Budgetgrenze, erkannte Bedrohungssignatur, Fund eines Sicherheitstools, geänderte Sicherheitslage. Eigene Regeln sind optional zusätzlich möglich.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Das Zurückhalten eines riskanten Aufrufs ist opt-in und standardmäßig deaktiviert.**
Rekursive Löschungen, Force-Pushes, sudo, Secrets, Paketinstallationen und ausgehende Aufrufe bekommen jeweils eine Regel, die du aktivieren kannst. Bis du das tust, beobachtet ClawMetry nur und ändert nichts. Sobald eine aktiviert ist, warten passende Aufrufe hier (oder auf deinem Handy) auf eine Freigabe oder Ablehnung.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Mehr, pro Runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star-Verlauf

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Lizenz

MIT · Erstellt von [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
