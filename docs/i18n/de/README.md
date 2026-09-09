<!-- i18n-src:61beb8393e2f -->
> Deutsch translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Ein Agent kann hundert Tool-Aufrufe machen, ohne Fortschritte zu erzielen.** ClawMetry
liest die Session-Dateien, die deine Coding-Agenten bereits schreiben, und bringt die Timeline,
die Tool-Aufrufe und alle Token- und Kostendaten, die die Runtime offenlegt, in eine
Ansicht — damit du einen langen, funktionierenden Lauf von einem hängenden unterscheiden kannst.

Funktioniert mit **30 KI-Agent-Runtimes** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 26 weitere. Ein Dashboard für deine gesamte Agenten-Flotte. ([die vollständige Liste](SUPPORTED_RUNTIMES.txt), generiert aus dem Katalog.)

> 🌐 **Lies dies in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mehr →](docs/i18n/)

Ein Befehl. Keine Konfiguration. Erkennt alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Öffnet sich unter **http://localhost:8900**. Keine Konfiguration nötig: Es findet die Agent-Runtimes,
die du bereits hast, liest sie nur lesend aus und ändert nichts an ihrer Ausführung.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Vor der Installation

| | |
|---|---|
| **Was es tut** | Liest die Session-Dateien und Logs, die deine Agenten bereits schreiben. Kein SDK, keine Code-Änderung, keine Instrumentierung in deiner App. |
| **Was du siehst** | Session-Timeline, Tool-für-Tool-Replay, Token- und Kostenaufschlüsselung sowie Trajektoriensignale (Schleifen, wiederholte Fehler) — pro Runtime. |
| **Was kostenlos ist** | `pip install clawmetry` liest **OpenClaw, NVIDIA NemoClaw und Goose** ohne Konto, ohne Schlüssel und ohne Netzwerkaufruf. Die anderen 27 — Claude Code, Codex, Cursor und der Rest — werden vom Closed-Source-Begleitprogramm `clawmetry-pro` gelesen, das mit der 7-tägigen Testversion oder einem Plan geliefert wird — siehe [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) für die genaue Aufteilung. |
| **Wie du startest** | `pip install clawmetry && clawmetry`, dann localhost:8900 öffnen. Noch keine Agenten auf dieser Maschine? `clawmetry --sample` öffnet sich mit drei beschrifteten synthetischen Sessions. |
| **Was deine Maschine verlässt** | Keine Session-Daten, außer du führst `clawmetry connect` aus. Standardmäßig laufen zwei Dinge, beide Opt-out und keine trägt Session-Inhalte: ein anonymer Installations-Ping und eine PyPI-Versionsprüfung. Jedes Ziel ist in [docs/EGRESS.md](docs/EGRESS.md) inventarisiert, rekonstruiert aus einer Netzwerk-Aufzeichnung statt aus dem Lesen von Kommentaren. |

Zwei Einschränkungen, die man kennen sollte, bevor man die Ausgabe bewertet: Runtimes legen sehr
unterschiedliche Daten offen (manche veröffentlichen überhaupt keine Kosten — [die Matrix](docs/compatibility.md)
zeigt, welche pro Runtime), und eine Aktion zu beobachten ist nicht dasselbe wie sie
blockieren zu können ([welche Steuerungen pro Runtime real sind](docs/APPROVALS.md)).


## Funktioniert mit 30 Agent-Runtimes

**Kostenlos in der Open-Source-App:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Bei einem kostenpflichtigen Plan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Jede Runtime bekommt dasselbe Dashboard. Führe mehrere gleichzeitig aus, und der Header-
Umschalter fokussiert jeden Tab neu auf eine davon.

Hast du deinen eigenen Agenten auf einem SDK aufgebaut? Der Interceptor verfolgt auch dessen LLM-Aufrufe.
Siehe [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Was du bekommst

- **Sessions & Transkripte**: was jeder Agent getan hat, Zug für Zug, mit Replay
- **Kosten & Tokens**: pro Runtime, Modell, Session und Tag, mit Anomalie-Markierungen
- **Flow**: Live-Diagramm der Nachrichten, die durch Kanäle, Modelle und Tools laufen
- **Brain**: der Reasoning- und Tool-Call-Ereignisstrom in Echtzeit
- **Context-Blowout**: Fenster-Auslastung passend pro Anbieter dimensioniert, Kompaktierung vs. erzwungener Überlauf, plus eine pro-Runtime-Übersicht dessen, was wir *nicht* sehen können ([wie](docs/CONTEXT_BLOWOUT.md))
- **Memory & Skills**: die Dateien und Skills, die jede Runtime tatsächlich geladen hat
- **Health & Logs**: Speicherplatz, RAM, Fehlerraten, Rate-Limits, Live-Log-Stream
- **Alerts**: Budgetgrenzen, Fehlerspitzen, Agent-offline, weitergeleitet an Slack, Discord, PagerDuty, Telegram, E-Mail
- **Approvals**: riskante Tool-Aufrufe pausieren, *bevor* sie ausgeführt werden, und vom Handy aus genehmigen ([wie](docs/APPROVALS.md))

## Context-Blowout, und was das Beobachten kostet

Zwei Fragen, die es wert sind, beantwortet zu werden, bevor man einem Agenten-Vergleichstool vertraut.

**Wie geht es mit Context-Window-Blowout über Runtimes hinweg um?**

Ein Auslastungsprozentsatz ist nur so ehrlich wie das, wodurch er geteilt wird. ClawMetry
bemisst das Fenster pro Anbieter anhand [einer Tabelle, die du lesen und
per PR ändern kannst](clawmetry/context_windows.py), die Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama und GLM abdeckt. Es misst nicht alle 30
Runtimes mit dem Lineal eines einzigen Anbieters. Das ist wichtig: Ein 300K-GPT-5-Turn,
bewertet anhand von Anthropics 200K, liest sich als ">100%, geplatzt", obwohl er tatsächlich bei 75% von
GPT-5s 400K liegt. Dasselbe Lineal verschleiert einen tatsächlich überlaufenen 130K-DeepSeek-Turn
als komfortable 65%.

Jedes Fenster wird mit seiner Herkunft ausgeliefert: `model_table`, `explicit_marker`,
`observed_floor`, oder ein ehrliches `default`, wenn wir das Modell nicht kennen. Eine
Anzeige, die auf einer Vermutung basiert, wird niemals mit derselben Autorität dargestellt wie eine, die auf einer
Nachschlage-Tabelle basiert.

ClawMetry kann Kompaktierungsereignisse nur bei manchen Runtimes sehen. Deshalb meldet
`GET /api/context-coverage` pro Runtime, ob eine **Null bedeutet "lief saubereren durch" oder "wir sind blind"**. Eine `0`, die tatsächlich blind bedeutet, sagt das auch.
[Vollständige Details](docs/CONTEXT_BLOWOUT.md)

**Was kostet die Instrumentierung?**

| Pfad | Zu deinem Agenten hinzugefügt | Standard? |
|---|---|---|
| Session-Datei-Tailing (alle 30 Runtimes) | **0**. Separater Prozess, kein ClawMetry-Code in deinem Agenten | an |
| HTTP-Interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** pro LLM-Aufruf, bzw. 0,009% eines 5s-Aufrufs | aus |
| Pre-Tool-Hook-Gate (warmer Cache) | **+44 ms** pro gegatetem Tool-Aufruf, über einem 36-ms-Interpreter-Sockel | aus |
| Enforcement-Proxy | **+9,7 ms** pro LLM-Aufruf | aus |

Kosten für den Daemon-Host: **2.762 Ereignisse/Sek.** Ingest, **710 Bytes/Ereignis** auf der Festplatte
(67,7 MB pro 100.000 Ereignisse), und **~12% eines Kerns** dauerhaft bei einer stark ausgelasteten
Installation. Diese letzte Zahl liegt über unserem eigenen angegebenen 5-10%-Budget, deshalb wird sie
als Bug veröffentlicht, dem man nachjagen sollte, statt sie von der Seite zu lassen.

Gemessen auf einem Apple M2 Pro mit `benchmarks/overhead.py`. Der Test-Harness führt
jede Bedingung in einem separaten Prozess aus, wechselt deren Reihenfolge ab und **verweigert
die Ausgabe einer Zahl, wenn die Durchläufe sich über ihr Vorzeichen uneinig sind**. Führe ihn auf deiner eigenen
Maschine in einer Minute aus:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Jeder Pfad wird gemessen, einschließlich der Hook-Gates und des Enforcement-Proxys,
und der Harness läuft in CI unter Linux, macOS und Windows. Zwei Ergebnisse, die man kennen sollte: Der
Proxy kostet unter Windows etwa siebenmal mehr als unter Linux, und
der Daemon hält derzeit etwa 12% eines Kerns aufrecht, über unserem eigenen 5-10%-
Budget. Die Rohdaten als JSON, die Methode und was noch ungemessen ist, stehen in
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Preise

| Plan | Was er abdeckt | Preis |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, vollständiges Dashboard, nur lokal | $0 |
| **Starter** | Jede andere oben genannte Runtime, Flotten-Ansicht, Cloud-Sync | $9 pro Node / Monat |
| **Pro** | Starter plus Steuerung und Bewertung: Approvals, Tool-Risiko-Richtlinien, Evals, Anomalie-Erkennung, Kostenoptimierer, OTel-Export, manipulationssicheres Audit-Log | $19 pro Node / Monat |

Jahrespläne, Enterprise und die aktuellen Preise stehen unter
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Self-hosted Lizenzschlüssel
funktionieren ohne die Cloud (`clawmetry license`). Die genaue Aufteilung zwischen kostenlos und kostenpflichtig steht
in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Deine Daten bleiben auf deiner Maschine

ClawMetry liest lokale Session-Dateien und Logs. **Keine Session-Daten verlassen deine Maschine,
außer du führst `clawmetry connect` aus** — keine Prompts, Antworten, Tool-Argumente, Dateiinhalte
oder Log-Zeilen. Wenn du dich verbindest, ist der Snapshot Ende-zu-Ende verschlüsselt
mit einem Schlüssel, der deine Maschine nie verlässt, und wird in deinem Browser entschlüsselt. Wenn ein
Node keinen Schlüssel hat, wird der Upload übersprungen, statt im Klartext gesendet zu werden, und keine
Server-Antwort kann das abschalten.

Standardmäßig laufen zwei Dinge, bevor du dich verbindest, beide Opt-out und keine
trägt Session-Daten: ein anonymer Installations-Ping und eine Versionsprüfung gegen
PyPI. Eine Standard-Installation schlägt auch einmalig deine öffentliche IP für eine Startbanner-
Zeile nach. Jedes Ziel, was es trägt und wie man es abschaltet, ist aufgelistet in
[docs/EGRESS.md](docs/EGRESS.md); selbst gehostete, umgeleitete und abgeschottete (air-gapped) Installationen
tätigen überhaupt keine optionalen ausgehenden Aufrufe.

Die Entschlüsselung findet in deinem Browser statt, in Code, den wir dir servieren. Das war früher
ein Versprechen; jetzt ist es etwas, das du überprüfen kannst. Jede Zeile, die deinen Schlüssel berührt,
liegt in einer lesbaren Datei, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
die im Wheel mitgeliefert und unverändert serviert wird, gepinnt mit einem Subresource-
Integrity-Hash. Um zu bestätigen, dass der Browser das ausführt, was wir veröffentlicht haben:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Was das nicht beweist: Wir servieren die Seite, die die Datei lädt, wir könnten also
eine andere Seite servieren. Integrity-Hashes schützen dich vor einem kompromittierten CDN,
nicht vor dem Anbieter. Was du gewinnst, ist, dass jede Substitution
absichtlich, sichtbar im Seitenquelltext und anders sein muss als ein Artefakt auf PyPI,
das jeder abrufen kann. Self-Hosting oder das Bleiben rein lokal entfernt
die Abhängigkeit vollständig.

## Installation

```bash
pip install clawmetry     # dann: clawmetry
```

Oder der Einzeiler: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Benötigt Python 3.8+ unter macOS, Linux oder Windows, und mindestens eine Agent-Runtime auf
derselben Maschine. Docker-Anleitung: [docs/DOCKER.md](docs/DOCKER.md).

Oder lass es den Agenten für dich einrichten. Der [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)-
Skill bringt Claude Code, Codex, Cursor, Gemini CLI, Copilot oder OpenCode dazu,
ClawMetry zu installieren, zu berichten, was die Agenten auf der Maschine tun und ausgeben,
eine Session auf Anfrage zu stoppen und riskante Tool-Aufrufe zur Genehmigung zurückzuhalten:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokumentation

| | |
|---|---|
| [Runtime-Kompatibilität](docs/compatibility.md) | Was jeder Adapter liest, und wie man eine Runtime hinzufügt |
| [Context-Blowout](docs/CONTEXT_BLOWOUT.md) | Fenster pro Anbieter, Kompaktierung vs. Überlauf, Abdeckung pro Runtime |
| [Overhead](docs/OVERHEAD.md) | Was Instrumentierung kostet, gemessen, mit dem Harness zur Reproduktion |
| [Entitlements](docs/ENTITLEMENTS.md) | Kostenlos vs. kostenpflichtig, Tier-Matrix, Lizenz-CLI |
| [Approvals & Richtlinien](docs/APPROVALS.md) | Gating vor der Ausführung, Risikobewertung, Genehmigungen per Telefon |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Traces überallhin exportieren, OTLP von überallher einlesen |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain durchgängig, mit ausführbaren Beispielen |
| [SDK-Tracking](docs/SDK_TRACKING.md) | Kostenzuordnung für Agenten, die du selbst gebaut hast |
| [Chat-Kanäle](docs/CHANNELS.md) | Die im Flow angezeigten Chat-Adapter |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw-Setups |
| [Docker](docs/DOCKER.md) | Image, Compose, Volume-Mounts |
| [Architektur](ARCHITECTURE.md) · [Entwicklung](docs/DEVELOPMENT.md) | Wie es innen funktioniert; aus dem Quellcode ausführen |
| [Telemetrie](docs/TELEMETRY.md) | Die anonymen Installations- und Desktop-Öffnen-Pings, und wie man sie abschaltet |

## Screenshots

Jede Zahl unten stammt von einer echten Maschine, nur lesend, ohne irgendetwas vorab zu seeden.

**Es sagt dir, wenn etwas nicht stimmt, nicht nur, was passiert ist.**
Zwei Anomalie-Banner oben: Ausgaben laufen bei 7x dem Tagesdurchschnitt, und ein
4,2x-Kostenanstieg. Darunter, 324 von 667 aktuellen Sessions, die ein Verschwendungssignal
tragen, aufgeschlüsselt nach Ursache.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Es zeigt dir, wohin das Geld ging, in jedem Zeitfenster.**
$252,47 heute, $513,15 diese Woche, $1.312,92 diesen Monat, jeweils mit den dahinterliegenden
Tokens und wie viel davon dein Abo bereits abdeckt. Darunter, etwa $1.128/Monat
aufgeschlüsselt als wiedergewinnbar und $17.256/Monat bereits durch Cache-Wiederverwendung
gespart.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Es zeichnet, wie eine Nachricht zu einer Antwort wird.**
Das Live-Flow-Diagramm: du, der Kanal, auf dem sie eintraf, das Gateway, das Modell,
das gerade antwortet, und jedes Tool, nach dem es griff. Knoten leuchten auf, während Arbeit
durch sie hindurchläuft.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Jeder Agent auf der Maschine, in einer Tabelle.**
Was er ausführt, was er in den letzten 24 Stunden und über seine Lebensdauer kostet, wann
er zuletzt gesehen wurde, wem er gehört, und ob ein Abo die
Rechnung abdeckt. 14 Agenten hier, 3 Sessions arbeitend, 13 ruhig.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Es zeigt, wohin die Zeit und das Geld eines Turns gingen, Tool für Tool.**
Ein Turn einer echten Session: 11 Tools in 11,2 Minuten für $1,16. Jeder Bash-
Aufruf und Modellaufruf bekommt seinen eigenen Balken auf der Timeline, damit der Befehl, der 4,1
Minuten lief, und der, der 226ms lief, auf einen Blick unterschieden werden können.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Es bewertet die Arbeit, nicht nur die Ausgaben.**
Ein A diese Woche: 54 Aufgaben kamen saubereren zurück, 2 grobe kosteten $48,57, und die
Läufe mit zu wenig Aktivität, um beurteilt zu werden, werden aus der Bewertung ausgeschlossen, statt
als Erfolge gezählt zu werden. Jeder grobe Lauf verlinkt zu seinem Trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Es zeigt, warum das Context-Window immer wieder vollläuft.**
715K von einem 1M-Token-Fenster im letzten Turn, ein 83,3%-Peak, 4 Kompaktierungen,
die alle proaktiv statt bei einem Überlauf ausgelöst wurden, sowie die Auslastung
jedes vorherigen Turns.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Erkennung läuft, ohne dass du irgendetwas konfigurierst.**
Die eingebauten Detektoren sind ab der Installation aktiv: Agent wurde ruhig, Telemetrie-Feed
gestoppt, Kostenanstieg, Token-Burst, steigende Fehler, Fehlerspitze, Budget-
Schwellenwert, Bedrohungssignatur erkannt, Sicherheitstool-Fund, Sicherheitslage
verändert. Deine eigenen Regeln sind optional zusätzlich.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Das Zurückhalten eines riskanten Aufrufs ist Opt-in, und wird standardmäßig ausgeliefert.**
Rekursive Löschungen, Force-Pushes, sudo, Secrets, Paketinstallationen und ausgehende
Aufrufe bekommen jeweils eine Regel, die du aktivieren kannst. Bis du das tust, beobachtet ClawMetry und
ändert nichts. Sobald eine aktiviert ist, warten übereinstimmende Aufrufe hier (oder auf deinem Telefon)
auf eine Genehmigung oder Ablehnung.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Mehr, pro Runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Anerkennung

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


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
