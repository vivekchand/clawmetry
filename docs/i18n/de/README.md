<!-- i18n-src:c99ac0512cae -->
> Deutsch translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Ein Agent kann hundert Tool-Aufrufe tätigen, ohne Fortschritte zu machen.** ClawMetry
liest die Session-Dateien, die eure Coding-Agenten bereits schreiben, und bringt die Zeitleiste,
die Tool-Aufrufe und alle Token- und Kostendaten, die die Runtime bereitstellt, in eine einzige
Ansicht – so könnt ihr einen langen, erfolgreichen Durchlauf von einem unterscheiden, der feststeckt.

Funktioniert mit **33 KI-Agent-Runtimes** – Claude Code, OpenAI Codex, Hermes, OpenClaw & 29 weitere. Ein Dashboard für eure gesamte Agenten-Flotte. ([die vollständige Liste](SUPPORTED_RUNTIMES.txt), aus dem Katalog generiert.)

> 🌐 **Lies dies auf:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [mehr →](docs/i18n/)

Ein Befehl. Keine Konfiguration. Erkennt alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Öffnet sich unter **http://localhost:8900**. Keine Konfiguration: Es findet die Agent-Runtimes,
die ihr bereits habt, liest sie nur lesend ein und ändert nichts an deren Ausführung.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Bevor ihr installiert

| | |
|---|---|
| **Was es tut** | Liest die Session-Dateien und Logs, die eure Agenten bereits schreiben. Kein SDK, keine Codeänderung, keine Instrumentierung in eurer App. |
| **Was ihr seht** | Session-Zeitleiste, Tool-für-Tool-Wiedergabe, Token- und Kostenaufschlüsselung sowie Trajektoriensignale (Schleifen, wiederholte Fehlschläge) – pro Runtime. |
| **Was kostenlos ist** | `pip install clawmetry` liest **OpenClaw, NVIDIA NemoClaw, Goose und Qwen Code** ohne Account, ohne Schlüssel und ohne Netzwerkaufruf. Die anderen 28 – Claude Code, Codex, Cursor und der Rest – werden vom closed-source `clawmetry-pro`-Begleitmodul gelesen, das mit der 7-tägigen Testversion oder einem Plan kommt – die genaue Aufteilung findet ihr in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Wie ihr startet** | `pip install clawmetry && clawmetry`, dann localhost:8900 öffnen. Noch keine Agenten auf dieser Maschine? `clawmetry --sample` öffnet sich mit drei beschrifteten synthetischen Sessions. |
| **Was eure Maschine verlässt** | Keine Session-Daten, außer ihr führt `clawmetry connect` aus. Standardmäßig laufen zwei Dinge, beide opt-out und keines mit Session-Inhalt: ein anonymer Installations-Ping und eine PyPI-Versionsprüfung. Jedes Ziel ist in [docs/EGRESS.md](docs/EGRESS.md) aufgeführt, erstellt aus einem Netzwerk-Mitschnitt statt aus gelesenen Kommentaren. |

Zwei Einschränkungen, die man kennen sollte, bevor man die Ausgabe bewertet: Runtimes legen sehr
unterschiedliche Daten offen (manche veröffentlichen überhaupt keine Kosten – [die Matrix](docs/compatibility.md)
zeigt, welche, pro Runtime), und eine Aktion zu beobachten ist nicht dasselbe wie sie blockieren zu
können ([welche Kontrollen pro Runtime real sind](docs/APPROVALS.md)).


## Funktioniert mit 33 Agent-Runtimes

**Kostenlos in der Open-Source-App:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**In einem kostenpflichtigen Plan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Jede Runtime erhält dasselbe Dashboard. Lasst mehrere gleichzeitig laufen, und der Umschalter in
der Kopfzeile skaliert jeden Tab neu auf eine davon.

Habt ihr euren eigenen Agenten auf einem SDK gebaut? Der Interceptor erfasst auch dessen LLM-Aufrufe.
Siehe [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Was ihr bekommt

- **Sessions & Transkripte**: was jeder Agent getan hat, Zug um Zug, mit Wiedergabe
- **Kosten & Token**: pro Runtime, Modell, Session und Tag, mit Anomalie-Markierungen
- **Flow**: Live-Diagramm der Nachrichten, die durch Kanäle, Modelle und Tools fließen
- **Brain**: der Strom von Reasoning- und Tool-Call-Ereignissen, während er passiert
- **Kontext-Überlauf**: Fensterauslastung pro Anbieter dimensioniert, Kompaktierung vs. erzwungener Overflow, plus eine Karte pro Runtime, was wir *nicht* sehen können ([wie](docs/CONTEXT_BLOWOUT.md))
- **Memory & Skills**: die Dateien und Skills, die jede Runtime tatsächlich geladen hat
- **Health & Logs**: Festplatte, Speicher, Fehlerraten, Rate-Limits, Live-Log-Stream
- **Alerts**: Budgetgrenzen, Fehler-Spitzen, Agent-offline, weitergeleitet an Slack, Discord, PagerDuty, Telegram, E-Mail
- **Approvals**: riskante Tool-Aufrufe anhalten, *bevor* sie ausgeführt werden, und vom Telefon aus genehmigen ([wie](docs/APPROVALS.md))

## Kontext-Überlauf, und was das Beobachten kostet

Zwei Fragen, die es wert sind, beantwortet zu werden, bevor ihr irgendeinem Agenten-Vergleichstool vertraut.

**Wie wird Kontextfenster-Überlauf runtimeübergreifend gehandhabt?**

Ein Auslastungsprozentsatz ist nur so ehrlich wie das, wodurch er dividiert. ClawMetry
bemisst das Fenster pro Anbieter anhand [einer Tabelle, die ihr lesen und
per PR ändern könnt](clawmetry/context_windows.py), die Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama und GLM abdeckt. Es misst nicht alle 33
Runtimes mit dem Lineal eines einzigen Anbieters. Das ist wichtig: Ein 300K-GPT-5-Turn,
gegen Anthropics 200K bewertet, liest sich als ">100%, geplatzt", obwohl er tatsächlich bei
75% von GPT-5s 400K liegt. Dasselbe Lineal verbirgt einen wirklich überlaufenen
130K-DeepSeek-Turn als bequeme 65%.

Jedes Fenster wird mit seiner Herkunft ausgeliefert: `model_table`, `explicit_marker`,
`observed_floor`, oder ein ehrliches `default`, wenn wir das Modell nicht kennen. Eine
Anzeige, die auf einer Vermutung aufbaut, wird nie mit derselben Autorität dargestellt wie
eine, die auf einem Nachschlagewert aufbaut.

ClawMetry kann Kompaktierungsereignisse nur bei manchen Runtimes sehen. Also
meldet `GET /api/context-coverage` pro Runtime, ob eine **Null "lief sauber" oder
"wir sind blind" bedeutet**. Eine `0`, die eigentlich blind bedeutet, sagt das auch.
[Vollständige Details](docs/CONTEXT_BLOWOUT.md)

**Was kostet die Instrumentierung?**

| Pfad | Zu eurem Agenten hinzugefügt | Standard? |
|---|---|---|
| Session-Datei-Tailing (alle 33 Runtimes) | **0**. Separater Prozess, kein ClawMetry-Code in eurem Agenten | an |
| HTTP-Interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** pro LLM-Aufruf, bzw. 0,009% eines 5-Sekunden-Aufrufs | aus |
| Pre-Tool-Hook-Gate (warmer Cache) | **+44 ms** pro gegatetem Tool-Aufruf, über einem 36-ms-Interpreter-Sockel | aus |
| Enforcement-Proxy | **+9,7 ms** pro LLM-Aufruf | aus |

Kosten für den Daemon-Host: **2.762 Ereignisse/Sekunde** Ingest, **710 Bytes/Ereignis** auf der
Festplatte (67,7 MB pro 100.000 Ereignisse), und **~12% eines Kerns** nachhaltig bei einer
stark ausgelasteten Installation. Diese letzte Zahl liegt über unserem eigenen angegebenen
5-10%-Budget, also wird sie als Bug veröffentlicht, dem man nachgehen soll, statt sie von der
Seite zu lassen.

Gemessen auf einem Apple M2 Pro mit `benchmarks/overhead.py`. Der Testaufbau führt jede
Bedingung in einem separaten Prozess aus, wechselt deren Reihenfolge ab und **verweigert die
Ausgabe einer Zahl, wenn die Durchläufe sich über deren Vorzeichen uneinig sind**. Führt ihn
in einer Minute auf eurer eigenen Maschine aus:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Jeder Pfad wird gemessen, einschließlich der Hook-Gates und des Enforcement-Proxys,
und der Testaufbau läuft in CI unter Linux, macOS und Windows. Zwei Ergebnisse, die es wert
sind, zu wissen: Der Proxy kostet unter Windows etwa siebenmal mehr als unter Linux, und
der Daemon hält derzeit etwa 12% eines Kerns, über unserem eigenen 5-10%-Budget. Die
Rohdaten im JSON-Format, die Methode und was noch unvermessen ist, stehen in
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Preise

| Plan | Was er abdeckt | Preis |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, vollständiges Dashboard, nur lokal | $0 |
| **Starter** | Jede andere oben genannte Runtime, Flottenansicht, Cloud-Sync | $9 pro Node / Monat |
| **Pro** | Starter + Kontrolle und Bewertung: Approvals, Tool-Risiko-Richtlinien, Evals, Anomalieerkennung, Kostenoptimierer, OTel-Export, manipulationssicheres Audit-Log | $19 pro Node / Monat |

Jahrespläne, Enterprise und die aktuellen Zahlen findet ihr unter
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Self-hosted-Lizenzschlüssel
funktionieren ohne die Cloud (`clawmetry license`). Die genaue Aufteilung zwischen kostenlos
und kostenpflichtig steht in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Eure Daten bleiben auf eurer Maschine

ClawMetry liest lokale Session-Dateien und Logs. **Keine Session-Daten verlassen eure Maschine,
außer ihr führt `clawmetry connect` aus** – keine Prompts, Antworten, Tool-Argumente,
Dateiinhalte oder Log-Zeilen. Wenn ihr euch verbindet, wird der Snapshot Ende-zu-Ende
verschlüsselt mit einem Schlüssel, der eure Maschine nie verlässt, und in eurem Browser
entschlüsselt. Hat ein Node keinen Schlüssel, wird der Upload übersprungen statt im
Klartext gesendet, und keine Server-Antwort kann das abschalten.

Standardmäßig laufen zwei Dinge, bevor ihr euch verbindet, beide opt-out und keines mit
Session-Daten: ein anonymer Installations-Ping und eine Versionsprüfung gegen PyPI. Eine
Standardinstallation schlägt zudem einmalig eure öffentliche IP für eine Startbanner-Zeile
nach. Jedes Ziel, was es überträgt und wie man es abschaltet, ist in
[docs/EGRESS.md](docs/EGRESS.md) aufgeführt; selbst gehostete, umgeleitete und
abgeschottete (air-gapped) Installationen tätigen überhaupt keine optionalen
ausgehenden Aufrufe.

Die Entschlüsselung geschieht in eurem Browser, in Code, den wir euch ausliefern. Das war
früher ein Versprechen; jetzt ist es etwas, das ihr überprüfen könnt. Jede Zeile, die euren
Schlüssel berührt, lebt in einer lesbaren Datei,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), die im Wheel
mitgeliefert und wortgetreu ausgeliefert wird, abgesichert mit einem
Subresource-Integrity-Hash. Um zu bestätigen, dass der Browser das ausführt, was wir
veröffentlicht haben:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Was das nicht beweist: Wir liefern die Seite aus, die die Datei lädt, wir könnten also
eine andere Seite ausliefern. Integrity-Hashes schützen euch vor einem kompromittierten
CDN, nicht vor dem Anbieter. Was ihr gewinnt, ist, dass jede Ersetzung absichtlich,
im Seitenquelltext sichtbar und anders sein muss als ein Artefakt auf PyPI, das jeder
abrufen kann. Selbst zu hosten oder rein lokal zu bleiben beseitigt die Abhängigkeit
vollständig.

## Installation

```bash
pip install clawmetry     # dann: clawmetry
```

Oder der Einzeiler: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Benötigt Python 3.8+ auf macOS, Linux oder Windows, und mindestens eine Agent-Runtime auf
derselben Maschine. Docker-Anleitung: [docs/DOCKER.md](docs/DOCKER.md).

Oder lasst den Agenten es für euch einrichten. Der [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)-
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
| [Kontext-Überlauf](docs/CONTEXT_BLOWOUT.md) | Fenster pro Anbieter, Kompaktierung vs. Overflow, Abdeckung pro Runtime |
| [Overhead](docs/OVERHEAD.md) | Was Instrumentierung kostet, gemessen, mit dem Testaufbau zum Reproduzieren |
| [Entitlements](docs/ENTITLEMENTS.md) | Kostenlos vs. kostenpflichtig, Tier-Matrix, Lizenz-CLI |
| [Approvals & Richtlinien](docs/APPROVALS.md) | Vorausführungs-Gating, Risikobewertung, Genehmigungen per Telefon |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Traces überallhin exportieren, OTLP von überall ingestieren |
| [Bringt euren eigenen Agenten mit](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain Ende-zu-Ende, mit ausführbaren Beispielen |
| [SDK-Tracking](docs/SDK_TRACKING.md) | Kostenzuordnung für selbst gebaute Agenten |
| [Chat-Kanäle](docs/CHANNELS.md) | Die in Flow angezeigten Chat-Adapter |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw-Setups |
| [Docker](docs/DOCKER.md) | Image, Compose, Volume-Mounts |
| [Architektur](ARCHITECTURE.md) · [Entwicklung](docs/DEVELOPMENT.md) | Wie es innen funktioniert; Ausführung aus dem Quellcode |
| [Telemetrie](docs/TELEMETRY.md) | Die anonymen Installations- und Desktop-Öffnungs-Pings, und wie man sie abschaltet |

## Screenshots

Jede Zahl unten stammt von einer echten Maschine, nur lesend, ohne irgendetwas vorzugeben.

**Es sagt euch, wenn etwas nicht stimmt, nicht nur, was passiert ist.**
Zwei Anomalie-Banner oben: Ausgaben laufen beim 7-fachen des Tagesdurchschnitts, und eine
4,2-fache Kostenspitze. Darunter 324 von 667 aktuellen Sessions mit einem Verschwendungssignal,
aufgeschlüsselt nach Ursache.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Es zeigt euch, wohin das Geld floss, in jedem Zeitfenster.**
$252,47 heute, $513,15 diese Woche, $1.312,92 diesen Monat, jeweils mit den dahinterliegenden
Token und wie viel davon euer Abonnement bereits abdeckt. Darunter etwa $1.128/Monat,
aufgeschlüsselt als wiedergewinnbar, und $17.256/Monat, die bereits durch Cache-Wiederverwendung
gespart wurden.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Es zeichnet, wie eine Nachricht zu einer Antwort wird.**
Das Live-Flow-Diagramm: ihr, der Kanal, auf dem sie ankam, das Gateway, das Modell, das gerade
antwortet, und jedes Tool, nach dem es gegriffen hat. Knoten leuchten auf, während Arbeit durch
sie hindurch fließt.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Jeder Agent auf der Maschine, in einer Tabelle.**
Was er ausführt, was er in den letzten 24 Stunden und über seine gesamte Laufzeit kostet, wann er
zuletzt gesehen wurde, wem er gehört, und ob ein Abonnement die Rechnung abdeckt. 14 Agenten hier,
3 Sessions arbeiten, 13 ruhig.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Es zeigt, wohin Zeit und Geld eines Turns gingen, Tool für Tool.**
Ein Turn einer echten Session: 11 Tools in 11,2 Minuten für $1,16. Jeder Bash-Aufruf und
Modellaufruf erhält seinen eigenen Balken auf der Zeitleiste, sodass der Befehl, der 4,1 Minuten
lief, und der, der 226 ms lief, auf einen Blick unterschieden werden.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Es bewertet die Arbeit, nicht nur die Ausgaben.**
Ein A diese Woche: 54 Aufgaben kamen saubergestellt zurück, 2 holprige kosteten $48,57, und die
Durchläufe mit zu wenig Aktivität, um sie zu bewerten, werden aus der Benotung ausgeschlossen,
statt als Gewinne gezählt zu werden. Jeder holprige Durchlauf verlinkt zu seiner Trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Es zeigt, warum sich das Kontextfenster immer weiter füllt.**
715K von einem 1M-Token-Fenster beim letzten Turn, ein Spitzenwert von 83,3%, 4 Kompaktierungen,
die alle proaktiv statt bei einem Overflow ausgelöst wurden, und die Auslastung jedes
dahinterliegenden Turns.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Erkennung läuft, ohne dass ihr irgendetwas konfiguriert.**
Die eingebauten Detektoren sind ab der Installation an: Agent wurde still, Telemetrie-Feed
gestoppt, Kostenspitze, Token-Burst, steigende Fehler, Fehlerspitze, Budgetschwelle,
Bedrohungssignatur erkannt, Sicherheitstool-Befund, Sicherheitslage geändert. Eure eigenen Regeln
sind optional zusätzlich dazu.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Das Zurückhalten eines riskanten Aufrufs ist opt-in, und wird standardmäßig abgeschaltet
ausgeliefert.**
Rekursive Löschungen, Force-Pushes, sudo, Secrets, Paketinstallationen und ausgehende Aufrufe
erhalten jeweils eine Regel, die ihr einschalten könnt. Bis ihr das tut, beobachtet ClawMetry
nur und ändert nichts. Sobald eine eingeschaltet ist, warten passende Aufrufe hier (oder auf
eurem Telefon) auf eine Genehmigung oder Ablehnung.

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
