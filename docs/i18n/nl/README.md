<!-- i18n-src:9767c8001c9c -->
> Nederlands translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zie je agent denken.** Realtime observability voor **30 AI-agentruntimes**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 26 andere. Eén dashboard voor je hele agentvloot.

> 🌐 **Lees dit in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [meer →](docs/i18n/)

Eén commando. Geen configuratie. Detecteert alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Opent op **http://localhost:8900**. Geen configuratie: het vindt de agentruntimes
die je al hebt, leest ze read-only en verandert niets aan de manier waarop ze draaien.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Werkt met 30 agentruntimes

**Gratis in de open-source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Op een betaald abonnement:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Elke runtime krijgt hetzelfde dashboard. Draai er meerdere tegelijk en de
switcher in de header herschaalt elk tabblad naar een van hen.

Heb je je eigen agent op een SDK gebouwd in plaats van dit? De interceptor
volgt ook diens LLM-aanroepen. Zie [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Wat je krijgt

- **Sessies & transcripten**: wat elke agent deed, beurt voor beurt, met replay
- **Kosten & tokens**: per runtime, model, sessie en dag, met anomaliemarkeringen
- **Flow**: live diagram van berichten die door kanalen, modellen en tools bewegen
- **Brain**: de stream van redenerings- en tool-aanroep-events terwijl het gebeurt
- **Context blowout**: venstergebruik afgemeten per provider, compactie versus geforceerde overflow, plus een per-runtime overzicht van wat we *niet* kunnen zien ([hoe](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: de bestanden en skills die elke runtime daadwerkelijk laadde
- **Health & logs**: schijf, geheugen, foutpercentages, rate limits, live logstream
- **Alerts**: budgetplafonds, foutpieken, agent-offline, doorgestuurd naar Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals**: pauzeer risicovolle tool-aanroepen *voordat* ze uitgevoerd worden en keur ze goed vanaf je telefoon ([hoe](docs/APPROVALS.md))

## Context blowout, en wat het kost om te kijken

Twee vragen die het waard zijn om te beantwoorden voordat je een willekeurige
agentvergelijkingstool vertrouwt.

**Hoe gaat het om met context-venster blowout tussen runtimes?**

Een gebruikspercentage is alleen zo eerlijk als waar het door deelt. ClawMetry
bepaalt de venstergrootte per provider aan de hand van [een tabel die je kunt
lezen en waarvoor je een PR kunt indienen](clawmetry/context_windows.py), die
Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama en GLM
dekt. Het meet niet alle 30 runtimes met de liniaal van één leverancier. Dat
maakt uit: een 300K GPT-5-beurt gescoord tegen Anthropics 200K leest als
">100%, blown" terwijl deze in werkelijkheid op 75% van GPT-5's 400K zit.
Diezelfde liniaal verbergt een écht overvolle 130K DeepSeek-beurt als een
comfortabele 65%.

Elk venster wordt geleverd met zijn herkomst: `model_table`,
`explicit_marker`, `observed_floor`, of een eerlijke `default` wanneer we het
model niet kennen. Een meter gebouwd op een gok toont zich nooit met dezelfde
autoriteit als een die gebouwd is op een opzoeking.

ClawMetry kan compactie-events maar bij sommige runtimes zien. Daarom
rapporteert `GET /api/context-coverage`, per runtime, of een **nul betekent
"draaide schoon" of "we zijn blind"**. Een `0` die eigenlijk blind betekent,
zegt dat ook. [Volledig detail](docs/CONTEXT_BLOWOUT.md)

**Wat kost de instrumentatie?**

| Pad | Toegevoegd aan je agent | Standaard? |
|---|---|---|
| Session-file tailing (alle 30 runtimes) | **0**. Apart proces, geen ClawMetry-code in je agent | aan |
| HTTP-interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per LLM-aanroep, oftewel 0,009% van een 5s-aanroep | uit |
| Pre-tool hook gate (warme cache) | **+44 ms** per gated tool-aanroep, boven een 36 ms-interpretervloer | uit |
| Enforcement proxy | **+9,7 ms** per LLM-aanroep | uit |

Kosten van de daemon-host: **2.762 events/sec** ingest, **710 bytes/event**
op schijf (67,7 MB per 100k events), en **~12% van één core** aanhoudend op
een druk bezette installatie. Dat laatste getal ligt boven ons eigen
gestelde budget van 5-10%, dus het wordt gepubliceerd als een bug om achteraan
te gaan in plaats van van de pagina weggelaten.

Gemeten op een Apple M2 Pro met `benchmarks/overhead.py`. De testopstelling
draait elke conditie in een apart proces, wisselt hun volgorde af, en
**weigert een getal te printen wanneer de rondes het niet eens zijn over het
teken**. Draai het in een minuut op je eigen machine:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Elk pad wordt gemeten, inclusief de hook gates en de enforcement proxy, en de
testopstelling draait in CI op Linux, macOS en Windows. Twee resultaten die
het waard zijn om te weten: de proxy kost op Windows ongeveer zeven keer
meer dan op Linux, en de daemon houdt momenteel ongeveer 12% van één core
aan, boven ons eigen budget van 5-10%. De ruwe JSON, de methode en wat nog
niet gemeten is, staan in [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prijzen

| Abonnement | Wat het dekt | Prijs |
|---|---|---|
| **Gratis** | OpenClaw + NVIDIA NemoClaw + Goose, volledig dashboard, alleen lokaal | $0 |
| **Starter** | Elke andere runtime hierboven, vlootoverzicht, cloudsynchronisatie | $9 per node / maand |
| **Pro** | Starter + control en evaluatie: approvals, tool-risicobeleid, evals, anomaliedetectie, kostenoptimalisatie, OTel-export, manipulatiebestendig auditlog | $19 per node / maand |

Jaarabonnementen, Enterprise en de actuele prijzen staan op
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Zelf-gehoste
licentiesleutels werken zonder de cloud (`clawmetry license`). De exacte
gratis/betaald-verdeling staat in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Je data blijft op je eigen machine

ClawMetry leest lokale sessiebestanden en logs. **Geen sessiedata verlaat je
machine tenzij je `clawmetry connect` uitvoert** — geen prompts, antwoorden,
tool-argumenten, bestandsinhoud of logregels. Wanneer je wel verbindt, wordt
de snapshot end-to-end versleuteld met een sleutel die je machine nooit
verlaat, en ontsleuteld in je browser. Als een node geen sleutel heeft, wordt
de upload overgeslagen in plaats van onversleuteld verstuurd, en geen
serverreactie kan dat uitschakelen.

Twee dingen draaien wel standaard voordat je verbindt, beide opt-out en geen
van beide met sessiedata: een anonieme installatiemelding en een
versiecontrole tegen PyPI. Een standaardinstallatie zoekt ook eenmalig je
publieke IP op voor een startbanner-regel. Elke bestemming, wat die
meedraagt en hoe je het uitschakelt, staat in
[docs/EGRESS.md](docs/EGRESS.md); zelf-gehoste, omgeleide en air-gapped
installaties doen helemaal geen discretionaire uitgaande aanroepen.

De ontsleuteling gebeurt in je browser, in code die wij je leveren. Dat was
vroeger een belofte; het is nu iets wat je kunt controleren. Elke regel die
je sleutel raakt, staat in één leesbaar bestand,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), dat wordt
meegeleverd in de wheel en letterlijk zo geserveerd wordt, vastgepind met een
Subresource Integrity-hash. Om te bevestigen dat de browser draait wat wij
publiceerden:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Wat dat niet bewijst: wij serveren de pagina die het bestand laadt, dus we
zouden een andere pagina kunnen serveren. Integrity-hashes beschermen je
tegen een gecompromitteerde CDN, niet tegen de leverancier. Wat je wint, is
dat elke vervanging opzettelijk moet zijn, zichtbaar in de paginabron, en
anders dan een artefact op PyPI dat iedereen kan ophalen. Zelf hosten of
alleen lokaal blijven, elimineert de afhankelijkheid volledig.

## Installeren

```bash
pip install clawmetry     # dan: clawmetry
```

Of de one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Vereist Python 3.8+ op macOS, Linux of Windows, en minstens één
agentruntime op dezelfde machine. Docker-instructies:
[docs/DOCKER.md](docs/DOCKER.md).

## Documentatie

| | |
|---|---|
| [Runtime-compatibiliteit](docs/compatibility.md) | Wat elke adapter leest, en hoe je een runtime toevoegt |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Per-provider vensters, compactie versus overflow, per-runtime dekking |
| [Overhead](docs/OVERHEAD.md) | Wat instrumentatie kost, gemeten, met de testopstelling om het te reproduceren |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis versus betaald, tiermatrix, license-CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-executiegating, risicoscoring, telefoongoedkeuringen |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporteer traces overal naartoe, ingest OTLP van overal |
| [Breng je eigen agent mee](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain van begin tot eind, met uitvoerbare voorbeelden |
| [SDK-tracking](docs/SDK_TRACKING.md) | Kostenattributie voor agents die je zelf hebt gebouwd |
| [Chatkanalen](docs/CHANNELS.md) | De chatadapters die in Flow getoond worden |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw-opstellingen |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architectuur](ARCHITECTURE.md) · [Ontwikkeling](docs/DEVELOPMENT.md) | Hoe het intern werkt; vanuit de broncode draaien |
| [Telemetrie](docs/TELEMETRY.md) | De anonieme installatie- en desktop-open-meldingen, en hoe je ze uitschakelt |

## Screenshots

Elk getal hieronder komt van één echte machine, read-only, zonder iets gefingeerd.

**Het vertelt je wanneer er iets mis is, niet alleen wat er gebeurd is.**
Twee anomaliebanners bovenaan: uitgaven die 7x het dagelijkse gemiddelde
lopen, en een piek van 4,2x in kosten. Daaronder, 324 van de 667 recente
sessies met een verspillingssignaal, uitgesplitst per oorzaak.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Het laat je zien waar het geld naartoe ging, in elk venster.**
$252,47 vandaag, $513,15 deze week, $1.312,92 deze maand, elk met de tokens
erachter en hoeveel je abonnement daar al van dekt. Daaronder, ongeveer
$1.128/maand uitgesplitst als terugwinbaar en $17.256/maand al bespaard door
cache-hergebruik.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Het tekent hoe een bericht een antwoord wordt.**
Het live flow-diagram: jij, het kanaal waarop het binnenkwam, de gateway, het
model dat er nu op antwoordt, en elke tool waar het naar reikte. Nodes lichten
op naarmate werk erdoorheen beweegt.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Elke agent op de machine, in één tabel.**
Wat hij draait, wat hij kost in de laatste 24 uur en over zijn levensduur,
wanneer hij voor het laatst gezien is, wie de eigenaar is, en of een
abonnement de rekening dekt. 14 agents hier, 3 sessies aan het werk, 13 stil.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Het laat zien waar de tijd en het geld van een beurt naartoe gingen, tool voor tool.**
Eén beurt van een echte sessie: 11 tools in 11,2 minuten voor $1,16. Elke
Bash-aanroep en modelaanroep krijgt zijn eigen balk op de tijdlijn, zodat het
commando dat 4,1 minuten draaide en dat wat 226ms draaide in één oogopslag
uit elkaar te houden zijn.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Het beoordeelt het werk, niet alleen de uitgaven.**
Een A deze week: 54 taken kwamen schoon terug, 2 ruwe kostten $48,57, en de
runs met te weinig activiteit om te beoordelen worden weggelaten uit het
cijfer in plaats van meegeteld als overwinningen. Elke ruwe run linkt naar
zijn trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Het laat zien waarom het contextvenster maar blijft vollopen.**
715K van een venster van 1M tokens in de laatste beurt, een piek van 83,3%,
4 compacties die allemaal proactief afgingen in plaats van bij een overflow,
en het gebruik van elke beurt daarachter.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Detectie draait zonder dat jij iets hoeft te configureren.**
De ingebouwde detectors staan aan vanaf installatie: agent werd stil,
telemetriefeed stopte, kostenpiek, tokenpiek, oplopende fouten, foutpiek,
budgetdrempel, dreigingssignatuur gematcht, security-tool bevinding,
beveiligingspostuur veranderd. Je eigen regels zijn optioneel daarbovenop.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Een risicovolle aanroep vasthouden is opt-in, en wordt zo uitgeleverd.**
Recursieve deletes, force pushes, sudo, secrets, package-installaties en
uitgaande aanroepen krijgen elk een regel die je kunt aanzetten. Totdat je
dat doet, kijkt ClawMetry toe en verandert er niets. Zodra er één aanstaat,
wachten matchende aanroepen hier (of op je telefoon) op een goedkeuring of
afwijzing.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Meer, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
