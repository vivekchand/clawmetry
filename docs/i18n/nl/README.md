<!-- i18n-src:c99ac0512cae -->
> Nederlands translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Een agent kan honderd tool calls doen zonder enige voortgang te maken.** ClawMetry
leest de sessiebestanden die je coding agents al schrijven, en brengt de tijdlijn,
de tool calls en welke token- en kostendata de runtime ook maar blootlegt samen in één
overzicht — zodat je een lange run die werkt kunt onderscheiden van een die vastzit.

Werkt met **33 AI agent runtimes** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 29 andere. Één dashboard voor je hele agent-fleet. ([de volledige lijst](SUPPORTED_RUNTIMES.txt), gegenereerd uit de catalogus.)

> 🌐 **Lees dit in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [meer →](docs/i18n/)

Eén commando. Geen configuratie. Detecteert alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Opent op **http://localhost:8900**. Geen configuratie: het vindt de agent runtimes
die je al hebt, leest ze alleen-lezen en verandert niets aan hoe ze draaien.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Voordat je installeert

| | |
|---|---|
| **Wat het doet** | Leest de sessiebestanden en logs die je agents al schrijven. Geen SDK, geen codewijziging, geen instrumentatie in je app. |
| **Wat je ziet** | Sessietijdlijn, tool-voor-tool replay, token- en kostenoverzicht, en trajectsignalen (loops, herhaalde fouten) — per runtime. |
| **Wat gratis is** | `pip install clawmetry` leest **OpenClaw, NVIDIA NemoClaw, Goose en Qwen Code** zonder account, zonder key en zonder netwerkverzoek. De andere 28 — Claude Code, Codex, Cursor en de rest — worden gelezen door de closed-source `clawmetry-pro` companion, die meekomt met de proefperiode van 7 dagen of een abonnement — zie [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) voor de exacte verdeling. |
| **Hoe te starten** | `pip install clawmetry && clawmetry`, open dan localhost:8900. Nog geen agents op deze machine? `clawmetry --sample` opent met drie gelabelde synthetische sessies. |
| **Wat je machine verlaat** | Geen sessiedata, tenzij je `clawmetry connect` draait. Twee dingen draaien wel standaard, beide opt-out en geen van beide draagt sessie-inhoud: een anonieme installatieping en een PyPI-versiecontrole. Elke bestemming is geïnventariseerd in [docs/EGRESS.md](docs/EGRESS.md), opnieuw opgebouwd vanuit een pakketcapture in plaats van vanuit het lezen van commentaar. |

Twee beperkingen die het waard zijn om te kennen voordat je de output beoordeelt: runtimes
leggen zeer verschillende data bloot (sommige publiceren helemaal geen kosten — [de matrix](docs/compatibility.md)
vermeldt welke, per runtime), en het observeren van een actie is niet hetzelfde als in staat zijn
om die te blokkeren ([welke controls echt zijn, per runtime](docs/APPROVALS.md)).


## Werkt met 33 agent runtimes

**Gratis in de open source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**Op een betaald abonnement:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Elke runtime krijgt hetzelfde dashboard. Draai er meerdere tegelijk en de
switcher in de header herschaalt elk tabblad naar één daarvan.

Heb je je eigen agent op een SDK gebouwd in plaats hiervan? De interceptor volgt ook
diens LLM-calls. Zie [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Wat je krijgt

- **Sessies & transcripten**: wat elke agent deed, beurt voor beurt, met replay
- **Kosten & tokens**: per runtime, model, sessie en dag, met anomalie-markeringen
- **Flow**: live diagram van berichten die door channels, modellen en tools bewegen
- **Brain**: de stream van redeneer- en tool-call-events zoals die gebeurt
- **Context blowout**: windowgebruik op maat per provider, compactie versus gedwongen overflow, plus een per-runtime kaart van wat we *niet* kunnen zien ([hoe](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: de bestanden en skills die elke runtime daadwerkelijk laadde
- **Health & logs**: schijf, geheugen, foutpercentages, rate limits, live logstream
- **Alerts**: budgetplafonds, foutpieken, agent-offline, doorgestuurd naar Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals**: pauzeer risicovolle tool calls *voordat* ze draaien en keur ze goed vanaf je telefoon ([hoe](docs/APPROVALS.md))

## Context blowout, en wat observeren kost

Twee vragen die het waard zijn te beantwoorden voordat je enige tool voor agent-vergelijking vertrouwt.

**Hoe gaat het om met context-window blowout tussen runtimes?**

Een gebruikspercentage is maar zo eerlijk als waardoor het deelt. ClawMetry
bepaalt de windowgrootte per provider aan de hand van [een tabel die je kunt lezen en
PR'en](clawmetry/context_windows.py), die Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama en GLM omvat. Het meet niet alle 33
runtimes met de liniaal van één leverancier. Dat is belangrijk: een beurt van 300K bij GPT-5
afgezet tegen Anthropics 200K leest als ">100%, overschreden" terwijl het in werkelijkheid op 75% van
GPT-5's 400K zit. Dezelfde liniaal verbergt een werkelijk overvolle beurt van 130K bij DeepSeek
als een comfortabele 65%.

Elk window wordt geleverd met zijn herkomst: `model_table`, `explicit_marker`,
`observed_floor`, of een eerlijke `default` wanneer we het model niet kennen. Een
meter gebouwd op een gok verschijnt nooit met hetzelfde gezag als één gebouwd op een
opzoeking.

ClawMetry kan compactie-events alleen bij sommige runtimes zien. Daarom rapporteert
`GET /api/context-coverage` per runtime of een **nul betekent "draaide schoon"
of "we zijn blind"**. Een `0` die eigenlijk blind betekent, zegt dat ook.
[Volledige details](docs/CONTEXT_BLOWOUT.md)

**Wat kost de instrumentatie?**

| Pad | Toegevoegd aan je agent | Standaard? |
|---|---|---|
| Session-file tailing (alle 33 runtimes) | **0**. Apart proces, geen ClawMetry-code in je agent | aan |
| HTTP-interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per LLM-call, of 0,009% van een call van 5s | uit |
| Pre-tool hook gate (warme cache) | **+44 ms** per gatekeepte tool call, boven een interpreter-bodem van 36 ms | uit |
| Enforcement proxy | **+9,7 ms** per LLM-call | uit |

Kosten van de daemon-host: **2.762 events/sec** ingest, **710 bytes/event** op
schijf (67,7 MB per 100k events), en **~12% van één core** sustained op een druk
bezette installatie. Dat laatste getal ligt boven ons eigen gestelde budget van 5-10%,
dus het wordt gepubliceerd als een bug om achteraan te gaan in plaats van van de pagina weggehouden.

Gemeten op een Apple M2 Pro met `benchmarks/overhead.py`. De harness draait
elke conditie in een apart proces, wisselt de volgorde af en **weigert
een getal te printen wanneer de rondes het niet eens zijn over het teken ervan**. Draai het op je eigen
machine in een minuut:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Elk pad wordt gemeten, inclusief de hook gates en de enforcement proxy,
en de harness draait op Linux, macOS en Windows in CI. Twee resultaten die het waard
zijn te weten: de proxy kost ongeveer zeven keer meer op Windows dan op Linux, en
de daemon draait momenteel sustained op ongeveer 12% van één core, boven ons eigen budget
van 5-10%. De ruwe JSON, de methode, en wat nog niet gemeten is staan in
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prijzen

| Plan | Wat het omvat | Prijs |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, volledig dashboard, alleen lokaal | $0 |
| **Starter** | Elke andere runtime hierboven, fleet-overzicht, cloud sync | $9 per node / maand |
| **Pro** | Starter + control en evaluatie: approvals, tool-risicobeleid, evals, anomaliedetectie, kostenoptimalisatie, OTel-export, tamper-evident auditlog | $19 per node / maand |

Jaarplannen, Enterprise en de actuele prijzen staan op
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Self-hosted license
keys werken zonder de cloud (`clawmetry license`). De exacte verdeling tussen gratis en betaald staat
in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Je data blijft op je machine

ClawMetry leest lokale sessiebestanden en logs. **Er verlaat geen sessiedata je machine
tenzij je `clawmetry connect` draait** — geen prompts, antwoorden, tool-argumenten, bestands-
inhoud of logregels. Wanneer je wél connect, is de snapshot end-to-end versleuteld
met een key die je machine nooit verlaat, en wordt die ontsleuteld in je browser. Als een
node geen key heeft, wordt de upload overgeslagen in plaats van onversleuteld verzonden, en
geen serverrespons kan dat uitschakelen.

Twee dingen draaien wel standaard voordat je connect, beide opt-out en geen van beide
draagt sessiedata: een anonieme installatieping en een versiecontrole tegen
PyPI. Een standaardinstallatie zoekt ook één keer je publieke IP op voor een startbanner-
regel. Elke bestemming, wat die bevat en hoe je het uitschakelt staat vermeld in
[docs/EGRESS.md](docs/EGRESS.md); self-hosted, omgeleide en air-gapped installaties
doen helemaal geen discretionaire uitgaande calls.

De ontsleuteling gebeurt in je browser, in code die wij je leveren. Dat was ooit
een belofte; het is nu iets dat je kunt controleren. Elke regel die je key aanraakt
staat in één leesbaar bestand, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
dat meegeleverd wordt in de wheel en letterlijk zo wordt geserveerd, vastgepind met een Subresource
Integrity-hash. Om te bevestigen dat de browser draait wat wij publiceerden:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Wat dat niet bewijst: wij serveren de pagina die het bestand laadt, dus we zouden een
andere pagina kunnen serveren. Integrity-hashes beschermen je tegen een gecompromitteerde CDN,
niet tegen de leverancier. Wat je wint is dat elke vervanging opzettelijk moet zijn,
zichtbaar in de paginabron, en anders dan een artefact op PyPI
dat iedereen kan ophalen. Self-hosten of lokaal-only blijven verwijdert de
afhankelijkheid volledig.

## Installeren

```bash
pip install clawmetry     # dan: clawmetry
```

Of de one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Vereist Python 3.8+ op macOS, Linux of Windows, en minstens één agent runtime op
dezelfde machine. Docker-instructies: [docs/DOCKER.md](docs/DOCKER.md).

Of laat de agent het voor je opzetten. De [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
skill leert Claude Code, Codex, Cursor, Gemini CLI, Copilot of OpenCode om
ClawMetry te installeren, te rapporteren wat de agents op de machine doen en uitgeven,
op verzoek een sessie te stoppen, en risicovolle tool calls vast te houden voor goedkeuring:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Documentatie

| | |
|---|---|
| [Runtime-compatibiliteit](docs/compatibility.md) | Wat elke adapter leest, en hoe je een runtime toevoegt |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Per-provider windows, compactie versus overflow, per-runtime dekking |
| [Overhead](docs/OVERHEAD.md) | Wat instrumentatie kost, gemeten, met de harness om het te reproduceren |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis versus betaald, tiermatrix, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating, risicoscoring, telefoongoedkeuringen |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporteer traces overal naartoe, ingest OTLP vanuit alles |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain end-to-end, met uitvoerbare voorbeelden |
| [SDK tracking](docs/SDK_TRACKING.md) | Kostentoewijzing voor agents die je zelf hebt gebouwd |
| [Chat channels](docs/CHANNELS.md) | De chatadapters die in Flow worden getoond |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Gesandboxte NVIDIA NemoClaw-opstellingen |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architectuur](ARCHITECTURE.md) · [Ontwikkeling](docs/DEVELOPMENT.md) | Hoe het intern werkt; vanaf de bron draaien |
| [Telemetrie](docs/TELEMETRY.md) | De anonieme installatie- en desktop-open-pings, en hoe je ze uitschakelt |

## Screenshots

Elk getal hieronder komt van één echte machine, alleen-lezen, zonder dat er iets gesimuleerd is.

**Het vertelt je wanneer er iets mis is, niet alleen wat er is gebeurd.**
Twee anomaliebanners bovenaan: uitgaven die 7x het dagelijkse gemiddelde draaien, en een
piek van 4,2x in kosten. Daaronder, 324 van de 667 recente sessies met een verspillingssignaal,
uitgesplitst per oorzaak.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Het laat je zien waar het geld naartoe ging, in elk venster.**
$252,47 vandaag, $513,15 deze week, $1.312,92 deze maand, elk met de tokens
erachter en hoeveel daarvan je abonnement al dekt. Daaronder, ongeveer $1.128/maand
uitgesplitst als recupereerbaar en $17.256/maand al bespaard door
cache-herbruik.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Het tekent hoe een bericht een antwoord wordt.**
Het live flow-diagram: jij, het channel waarop het aankwam, de gateway, het model
dat nu antwoordt, en elke tool waarnaar het reikte. Nodes lichten op terwijl werk
erdoorheen beweegt.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Elke agent op de machine, in één tabel.**
Wat hij draait, wat hij kost in de laatste 24 uur en over zijn hele levensduur, wanneer
hij laatst gezien is, wie hem beheert, en of een abonnement de rekening dekt.
14 agents hier, 3 sessies aan het werk, 13 stil.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Het laat zien waar de tijd en het geld van een beurt naartoe gingen, tool voor tool.**
Eén beurt van een echte sessie: 11 tools in 11,2 minuten voor $1,16. Elke Bash-
call en modelcall krijgt zijn eigen balk op de tijdlijn, zodat het commando dat 4,1
minuten draaide en het ene dat 226ms draaide op het eerste gezicht uit elkaar te houden zijn.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Het beoordeelt het werk, niet alleen de uitgaven.**
Een A deze week: 54 taken kwamen schoon terug, 2 ruwe kostten $48,57, en de
runs met te weinig activiteit om te beoordelen worden weggelaten uit het cijfer in plaats van
als winst meegerekend te worden. Elke ruwe run linkt naar zijn trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Het laat zien waarom het context-window steeds voller raakt.**
715K van een window van 1M tokens op de laatste beurt, een piek van 83,3%, 4 compacties
die allemaal proactief afgingen in plaats van bij een overflow, en de bezetting van
elke beurt erachter.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Detectie draait zonder dat jij iets configureert.**
De ingebouwde detectoren staan aan vanaf installatie: agent werd stil, telemetriefeed
stopte, kostenpiek, tokenpiek, oplopende fouten, foutpiek, budget-
drempel, dreigingssignatuur gematcht, bevinding van security-tool, security-houding
veranderd. Je eigen regels zijn optioneel daarbovenop.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Een risicovolle call vasthouden is opt-in, en wordt uitgeleverd.**
Recursieve deletes, force pushes, sudo, secrets, package-installaties en uitgaande
calls krijgen elk een regel die je kunt aanzetten. Totdat je dat doet, kijkt ClawMetry toe
en verandert niets. Zodra er één aan staat, wachten matchende calls hier (of op je telefoon)
op een goedkeuring of afwijzing.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Meer, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Erkenning

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licentie

MIT · Gebouwd door [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
