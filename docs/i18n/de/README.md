<!-- i18n-src:a855a14295b0 -->
> Deutsch translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Ein Agent kann hundert Tool-Aufrufe machen, ohne dabei voranzukommen.** ClawMetry
liest die Session-Dateien, die deine Coding-Agenten ohnehin schon schreiben, und bringt die Zeitleiste,
die Tool-Aufrufe und alle Token- und Kostendaten, die die Runtime offenlegt, in eine einzige
Ansicht — damit du einen langen, funktionierenden Lauf von einem hängengebliebenen unterscheiden kannst.

Funktioniert mit **32 KI-Agent-Runtimes** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 28 weitere. Ein Dashboard für deine gesamte Agenten-Flotte. ([die vollständige Liste](SUPPORTED_RUNTIMES.txt), generiert aus dem Katalog.)

> 🌐 **Lies dies auf:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mehr →](docs/i18n/)

Ein Befehl. Keine Konfiguration. Erkennt alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Öffnet sich unter **http://localhost:8900**. Keine Konfiguration nötig: Es findet die Agent-Runtimes,
die du bereits hast, liest sie nur lesend aus und ändert nichts daran, wie sie laufen.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Bevor du installierst

| | |
|---|---|
| **Was es tut** | Liest die Session-Dateien und Logs, die deine Agenten ohnehin schon schreiben. Kein SDK, keine Codeänderung, keine Instrumentierung in deiner App. |
| **Was du siehst** | Session-Zeitleiste, Tool-für-Tool-Wiedergabe, Token- und Kostenaufschlüsselung sowie Trajektoriensignale (Schleifen, wiederholte Fehlschläge) — pro Runtime. |
| **Was kostenlos ist** | `pip install clawmetry` liest **OpenClaw, NVIDIA NemoClaw und Goose** ohne Konto, ohne Schlüssel und ohne Netzwerkaufruf. Die anderen 27 — Claude Code, Codex, Cursor und der Rest — werden vom Closed-Source-Begleiter `clawmetry-pro` gelesen, der mit der 7-tägigen Testversion oder einem Plan kommt — siehe [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) für die genaue Aufteilung. |
| **Wie man startet** | `pip install clawmetry && clawmetry`, dann localhost:8900 öffnen. Noch keine Agenten auf dieser Maschine? `clawmetry --sample` öffnet sich mit drei beschrifteten synthetischen Sessions. |
| **Was deine Maschine verlässt** | Keine Session-Daten, außer du führst `clawmetry connect` aus. Standardmäßig laufen zwei Dinge, beide opt-out und keines mit Session-Inhalten: ein anonymer Installations-Ping und eine PyPI-Versionsprüfung. Jedes Ziel ist in [docs/EGRESS.md](docs/EGRESS.md) aufgeführt, erstellt aus einer Netzwerk-Mitschnitt-Analyse statt aus dem Lesen von Kommentaren. |

Zwei Einschränkungen, die es sich zu kennen lohnt, bevor du die Ausgabe beurteilst: Runtimes legen sehr
unterschiedliche Daten offen (manche veröffentlichen überhaupt keine Kosten — [die Matrix](docs/compatibility.md)
zeigt, welche, pro Runtime), und eine Aktion zu beobachten ist nicht dasselbe wie sie
blockieren zu können ([welche Kontrollen real sind, pro Runtime](docs/APPROVALS.md)).


## Funktioniert mit 32 Agent-Runtimes

**Kostenlos in der Open-Source-App:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Im kostenpflichtigen Plan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Jede Runtime bekommt dasselbe Dashboard. Führe mehrere gleichzeitig aus, und der
Umschalter im Header richtet jeden Tab neu auf eine davon aus.

Hast du deinen eigenen Agenten auf einem SDK gebaut statt darauf? Der Interceptor erfasst auch dessen
LLM-Aufrufe. Siehe [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Was du bekommst

- **Sessions & Transkripte**: was jeder Agent getan hat, Zug um Zug, mit Wiedergabe
- **Kosten & Tokens**: pro Runtime, Modell, Session und Tag, mit Anomalie-Markierungen
- **Flow**: Live-Diagramm der Nachrichten, die durch Kanäle, Modelle und Tools laufen
- **Brain**: der Strom von Reasoning- und Tool-Aufruf-Ereignissen, während er passiert
- **Context Blowout**: Fensterauslastung, angepasst pro Anbieter, Kompaktierung vs. erzwungenes Überlaufen, plus eine Übersicht pro Runtime darüber, was wir *nicht* sehen können ([wie](docs/CONTEXT_BLOWOUT.md))
- **Memory & Skills**: die Dateien und Skills, die jede Runtime tatsächlich geladen hat
- **Health & Logs**: Festplatte, Speicher, Fehlerraten, Rate-Limits, Live-Log-Stream
- **Alerts**: Budgetgrenzen, Fehlerspitzen, Agent-offline, weitergeleitet an Slack, Discord, PagerDuty, Telegram, E-Mail
- **Approvals**: riskante Tool-Aufrufe pausieren, *bevor* sie ausgeführt werden, und von deinem Handy aus genehmigen ([wie](docs/APPROVALS.md))

## Context Blowout, und was das Beobachten kostet

Zwei Fragen, die sich zu beantworten lohnen, bevor du irgendeinem Tool zum Agentenvergleich vertraust.

**Wie geht es mit Context-Window-Blowout über Runtimes hinweg um?**

Ein Auslastungsprozentsatz ist nur so ehrlich wie das, wodurch er geteilt wird. ClawMetry
bemisst das Fenster pro Anbieter anhand [einer Tabelle, die du lesen und
per PR ändern kannst](clawmetry/context_windows.py), die Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama und GLM abdeckt. Es misst nicht alle 32
Runtimes mit dem Lineal eines einzigen Anbieters. Das ist wichtig: Ein 300K-GPT-5-Turn,
bewertet gegen Anthropics 200K, liest sich als ">100%, blown", obwohl er tatsächlich bei 75% von
GPT-5s 400K liegt. Dasselbe Lineal versteckt einen tatsächlich übergelaufenen 130K-DeepSeek-Turn
als komfortable 65%.

Jedes Fenster liefert seine Herkunft mit: `model_table`, `explicit_marker`,
`observed_floor`, oder ein ehrliches `default`, wenn wir das Modell nicht kennen. Eine
Anzeige, die auf einer Vermutung basiert, wird nie mit derselben Autorität dargestellt wie eine, die auf
einem Nachschlagen basiert.

ClawMetry kann Kompaktierungsereignisse nur bei manchen Runtimes sehen. Deshalb meldet
`GET /api/context-coverage` pro Runtime, ob eine **Null bedeutet "sauber gelaufen" oder
"wir sind blind"**. Eine `0`, die eigentlich blind bedeutet, sagt das auch so.
[Vollständige Details](docs/CONTEXT_BLOWOUT.md)

**Was kostet die Instrumentierung?**

| Pfad | Zu deinem Agenten hinzugefügt | Standard? |
|---|---|---|
| Session-Datei-Tailing (alle 32 Runtimes) | **0**. Separater Prozess, kein ClawMetry-Code in deinem Agenten | an |
| HTTP-Interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** pro LLM-Aufruf, oder 0,009% eines 5s-Aufrufs | aus |
| Pre-Tool-Hook-Gate (warmer Cache) | **+44 ms** pro gegatetem Tool-Aufruf, über einem Interpreter-Sockel von 36 ms | aus |
| Enforcement-Proxy | **+9,7 ms** pro LLM-Aufruf | aus |

Daemon-Host-Kosten: **2.762 Ereignisse/Sek.** Ingest, **710 Bytes/Ereignis** auf der Festplatte
(67,7 MB pro 100.000 Ereignisse), und **~12% eines Kerns** dauerhaft bei einer stark ausgelasteten
Installation. Diese letzte Zahl liegt über unserem eigenen angegebenen Budget von 5-10%, deshalb wird sie
als zu behebender Fehler veröffentlicht, statt von der Seite weggelassen zu werden.

Gemessen auf einem Apple M2 Pro mit `benchmarks/overhead.py`. Der Test-Harness führt
jede Bedingung in einem separaten Prozess aus, wechselt ihre Reihenfolge ab und **weigert sich,
eine Zahl auszugeben, wenn die Durchläufe sich beim Vorzeichen widersprechen**. Führe ihn auf deiner eigenen
Maschine in einer Minute aus:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Jeder Pfad wird gemessen, einschließlich der Hook-Gates und des Enforcement-Proxys,
und der Harness läuft in CI unter Linux, macOS und Windows. Zwei Ergebnisse, die es sich zu wissen
lohnt: Der Proxy kostet unter Windows etwa siebenmal mehr als unter Linux, und
der Daemon hält derzeit etwa 12% eines Kerns aufrecht, über unserem eigenen Budget von 5-10%.
Die Rohdaten als JSON, die Methode und was noch ungemessen ist, stehen in
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Preise

| Plan | Was abgedeckt ist | Preis |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, vollständiges Dashboard, nur lokal | $0 |
| **Starter** | Jede andere oben genannte Runtime, Flottenansicht, Cloud-Sync | $9 pro Knoten / Monat |
| **Pro** | Starter + Kontrolle und Auswertung: Approvals, Tool-Risiko-Richtlinien, Evals, Anomalieerkennung, Kostenoptimierer, OTel-Export, manipulationssicheres Audit-Log | $19 pro Knoten / Monat |

Jahrespläne, Enterprise und die aktuellen Zahlen findest du unter
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Selbst gehostete Lizenzschlüssel
funktionieren ohne die Cloud (`clawmetry license`). Die genaue Aufteilung zwischen kostenlos/kostenpflichtig steht
in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Deine Daten bleiben auf deiner Maschine

ClawMetry liest lokale Session-Dateien und Logs. **Keine Session-Daten verlassen deine Maschine,
außer du führst `clawmetry connect` aus** — keine Prompts, Antworten, Tool-Argumente, Dateiinhalte
oder Log-Zeilen. Wenn du dich verbindest, ist der Snapshot Ende-zu-Ende verschlüsselt
mit einem Schlüssel, der deine Maschine nie verlässt, und wird in deinem Browser entschlüsselt. Wenn ein
Knoten keinen Schlüssel hat, wird der Upload übersprungen, statt im Klartext gesendet zu werden, und keine
Server-Antwort kann das abschalten.

Standardmäßig laufen zwei Dinge, bevor du dich verbindest, beide opt-out und keines
trägt Session-Daten: ein anonymer Installations-Ping und eine Versionsprüfung gegen
PyPI. Eine Standardinstallation sucht auch einmal deine öffentliche IP für eine Startbanner-
Zeile nach. Jedes Ziel, was es trägt und wie man es abschaltet, ist aufgeführt in
[docs/EGRESS.md](docs/EGRESS.md); selbst gehostete, umgeleitete und abgeschottete (air-gapped) Installationen
tätigen überhaupt keine optionalen ausgehenden Aufrufe.

Die Entschlüsselung geschieht in deinem Browser, in Code, den wir dir bereitstellen. Das war früher
ein Versprechen; jetzt ist es etwas, das du überprüfen kannst. Jede Zeile, die deinen Schlüssel berührt,
lebt in einer einzigen lesbaren Datei, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
die im Wheel mitgeliefert und wortgetreu ausgeliefert wird, verankert mit einem Subresource-
Integrity-Hash. Um zu bestätigen, dass der Browser das ausführt, was wir veröffentlicht haben:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Was das nicht beweist: Wir liefern die Seite aus, die die Datei lädt, wir könnten also eine
andere Seite ausliefern. Integrity-Hashes schützen dich vor einem kompromittierten CDN,
nicht vor dem Anbieter. Was du gewinnst, ist, dass jede Ersetzung
absichtlich, im Seitenquelltext sichtbar und anders sein müsste als ein Artefakt auf PyPI,
das jeder abrufen kann. Selbst-Hosting oder rein lokales Bleiben entfernt die
Abhängigkeit vollständig.

## Installation

```bash
pip install clawmetry     # dann: clawmetry
```

Oder der Einzeiler: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Benötigt Python 3.8+ unter macOS, Linux oder Windows, und mindestens eine Agent-Runtime auf
derselben Maschine. Docker-Anleitung: [docs/DOCKER.md](docs/DOCKER.md).

Oder lass den Agenten es für dich einrichten. Der Skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
bringt Claude Code, Codex, Cursor, Gemini CLI, Copilot oder OpenCode bei,
ClawMetry zu installieren, zu berichten, was die Agenten auf der Maschine tun und ausgeben,
eine Session auf Anfrage zu stoppen und riskante Tool-Aufrufe zur Genehmigung zurückzuhalten:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokumentation

| | |
|---|---|
| [Runtime-Kompatibilität](docs/compatibility.md) | Was jeder Adapter liest, und wie man eine Runtime hinzufügt |
| [Context Blowout](docs/CONTEXT_BLOWOUT.md) | Fenster pro Anbieter, Kompaktierung vs. Überlauf, Abdeckung pro Runtime |
| [Overhead](docs/OVERHEAD.md) | Was Instrumentierung kostet, gemessen, mit dem Harness zum Nachvollziehen |
| [Entitlements](docs/ENTITLEMENTS.md) | Kostenlos vs. kostenpflichtig, Tier-Matrix, Lizenz-CLI |
| [Approvals & Richtlinien](docs/APPROVALS.md) | Gating vor der Ausführung, Risikobewertung, Genehmigungen per Handy |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Traces überallhin exportieren, OTLP von überall einlesen |
| [Bring your own Agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain End-to-End, mit lauffähigen Beispielen |
| [SDK-Tracking](docs/SDK_TRACKING.md) | Kostenzuordnung für Agenten, die du selbst gebaut hast |
| [Chat-Kanäle](docs/CHANNELS.md) | Die in Flow angezeigten Chat-Adapter |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA-NemoClaw-Setups |
| [Docker](docs/DOCKER.md) | Image, Compose, Volume-Mounts |
| [Architektur](ARCHITECTURE.md) · [Entwicklung](docs/DEVELOPMENT.md) | Wie es intern funktioniert; Ausführung aus dem Quellcode |
| [Telemetrie](docs/TELEMETRY.md) | Die anonymen Installations- und Desktop-Öffnungs-Pings, und wie man sie abschaltet |

## Screenshots

Jede Zahl unten stammt von einer echten Maschine, nur lesend, ohne jegliche Vorbefüllung.

**Es sagt dir, wenn etwas nicht stimmt, nicht nur, was passiert ist.**
Zwei Anomalie-Banner ganz oben: Ausgaben laufen auf dem 7-fachen des Tagesdurchschnitts, und eine
4,2-fache Kostenspitze. Darunter, 324 von 667 letzten Sessions mit einem Verschwendungssignal,
aufgeschlüsselt nach Ursache.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Es zeigt dir, wohin das Geld geflossen ist, in jedem Zeitfenster.**
$252,47 heute, $513,15 diese Woche, $1.312,92 diesen Monat, jeweils mit den Tokens
dahinter und wie viel davon dein Abonnement bereits abdeckt. Darunter, etwa $1.128/Monat
als wiedergewinnbar aufgeschlüsselt und $17.256/Monat bereits durch Cache-Wiederverwendung eingespart.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Es zeichnet, wie aus einer Nachricht eine Antwort wird.**
Das Live-Flow-Diagramm: du, der Kanal, auf dem sie ankam, das Gateway, das Modell,
das gerade antwortet, und jedes Tool, nach dem es gegriffen hat. Knoten leuchten auf, während Arbeit
durch sie hindurchfließt.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Jeder Agent auf der Maschine, in einer Tabelle.**
Was er ausführt, was er in den letzten 24 Stunden und über seine Lebensdauer kostet, wann
er zuletzt gesehen wurde, wem er gehört, und ob ein Abonnement die
Rechnung abdeckt. 14 Agenten hier, 3 Sessions in Arbeit, 13 ruhig.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Es zeigt, wohin die Zeit und das Geld eines Turns geflossen sind, Tool für Tool.**
Ein Turn einer echten Session: 11 Tools in 11,2 Minuten für $1,16. Jeder Bash-
Aufruf und Modellaufruf bekommt seinen eigenen Balken auf der Zeitleiste, sodass der Befehl, der 4,1 Minuten
lief, und der, der 226 ms lief, auf einen Blick unterschieden werden können.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Es bewertet die Arbeit, nicht nur die Ausgaben.**
Ein A diese Woche: 54 Aufgaben kamen sauber zurück, 2 unrunde kosteten $48,57, und die
Läufe mit zu wenig Aktivität zum Beurteilen werden aus der Bewertung ausgeschlossen, statt
als Erfolge gezählt zu werden. Jeder unrunde Lauf verlinkt zu seiner Trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Es zeigt, warum sich das Context-Window immer weiter füllt.**
715K von einem 1M-Token-Fenster im letzten Turn, ein Spitzenwert von 83,3%, 4 Kompaktierungen,
die alle proaktiv statt bei einem Überlauf ausgelöst wurden, sowie die Auslastung von
jedem Turn dahinter.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Die Erkennung läuft, ohne dass du irgendetwas konfigurierst.**
Die eingebauten Detektoren sind ab der Installation aktiv: Agent ist verstummt, Telemetrie-Feed
gestoppt, Kostenspitze, Token-Ausbruch, steigende Fehler, Fehlerspitze, Budget-
Schwelle, Bedrohungssignatur erkannt, Fund eines Sicherheitstools, Sicherheitslage
geändert. Deine eigenen Regeln sind optional zusätzlich möglich.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Das Zurückhalten eines riskanten Aufrufs ist opt-in, und wird deaktiviert ausgeliefert.**
Rekursive Löschungen, Force-Pushes, sudo, Secrets, Paketinstallationen und ausgehende
Aufrufe bekommen jeweils eine Regel, die du aktivieren kannst. Bis du das tust, beobachtet ClawMetry
und ändert nichts. Sobald eine aktiv ist, warten passende Aufrufe hier (oder auf deinem Handy)
auf ein Genehmigen oder Ablehnen.

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
