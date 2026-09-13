<!-- i18n-src:a855a14295b0 -->
> Nederlands translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Een agent kan honderd tool calls doen zonder vooruitgang te boeken.** ClawMetry
leest de sessiebestanden die je coding agents toch al schrijven, en brengt de tijdlijn,
de tool calls en welke token- en kostengegevens de runtime ook maar blootgeeft samen in één
overzicht — zodat je een lange run die werkt kunt onderscheiden van een die vastzit.

Werkt met **32 AI-agentruntimes** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 28 meer. Eén dashboard voor je hele agentvloot. ([de volledige lijst](SUPPORTED_RUNTIMES.txt), gegenereerd uit de catalogus.)

> 🌐 **Lees dit in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [meer →](docs/i18n/)

Eén commando. Geen configuratie. Detecteert alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Opent op **http://localhost:8900**. Geen configuratie nodig: het vindt de agentruntimes
die je al hebt, leest ze alleen-lezen, en verandert niets aan hoe ze draaien.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Voordat je installeert

| | |
|---|---|
| **Wat het doet** | Leest de sessiebestanden en logs die je agents toch al schrijven. Geen SDK, geen codewijziging, geen instrumentatie in je app. |
| **Wat je ziet** | Sessietijdlijn, tool-voor-tool replay, uitsplitsing van tokens en kosten, en trajectsignalen (loops, herhaalde fouten) — per runtime. |
| **Wat gratis is** | `pip install clawmetry` leest **OpenClaw, NVIDIA NemoClaw en Goose** zonder account, zonder sleutel en zonder netwerkverbinding. De andere 27 — Claude Code, Codex, Cursor en de rest — worden gelezen door de closed-source `clawmetry-pro`-companion, die meekomt met de proefperiode van 7 dagen of een abonnement — zie [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) voor de exacte verdeling. |
| **Hoe te beginnen** | `pip install clawmetry && clawmetry`, open daarna localhost:8900. Nog geen agents op deze machine? `clawmetry --sample` opent met drie gelabelde synthetische sessies. |
| **Wat je machine verlaat** | Geen sessiegegevens, tenzij je `clawmetry connect` uitvoert. Twee dingen draaien standaard wel, allebei opt-out en geen van beide met sessie-inhoud: een anonieme installatiemelding en een PyPI-versiecontrole. Elke bestemming staat geïnventariseerd in [docs/EGRESS.md](docs/EGRESS.md), opnieuw opgebouwd vanuit een netwerkcapture in plaats van op basis van commentaar in de code. |

Twee beperkingen die het waard zijn om te kennen voordat je de output beoordeelt: runtimes geven zeer
verschillende gegevens vrij (sommige publiceren helemaal geen kosten — [de matrix](docs/compatibility.md)
laat zien welke, per runtime), en een actie waarnemen is niet hetzelfde als hem kunnen
blokkeren ([welke controles echt zijn, per runtime](docs/APPROVALS.md)).


## Werkt met 32 agentruntimes

**Gratis in de opensource-app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Op een betaald abonnement:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Elke runtime krijgt hetzelfde dashboard. Draai er meerdere tegelijk en de schakelaar
in de header herschaalt elk tabblad naar één ervan.

Zelf een agent op een SDK gebouwd? De interceptor volgt ook de LLM-calls daarvan.
Zie [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Wat je krijgt

- **Sessies & transcripten**: wat elke agent deed, beurt voor beurt, met replay
- **Kosten & tokens**: per runtime, model, sessie en dag, met afwijkingsmeldingen
- **Flow**: live diagram van berichten die door kanalen, modellen en tools bewegen
- **Brain**: de stream van redeneer- en tool-call-events terwijl het gebeurt
- **Context blowout**: venstergebruik afgemeten per provider, compactie versus geforceerde overflow, plus een per-runtime overzicht van wat we *niet* kunnen zien ([hoe](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: de bestanden en skills die elke runtime daadwerkelijk laadde
- **Health & logs**: schijf, geheugen, foutpercentages, rate limits, live logstream
- **Alerts**: budgetlimieten, foutpieken, agent-offline, doorgestuurd naar Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals**: pauzeer risicovolle tool calls *voordat* ze worden uitgevoerd en keur ze goed vanaf je telefoon ([hoe](docs/APPROVALS.md))

## Context blowout, en wat monitoren kost

Twee vragen die het waard zijn om te beantwoorden voordat je enige tool vertrouwt die agents vergelijkt.

**Hoe gaat het om met context-window blowout over verschillende runtimes heen?**

Een gebruikspercentage is maar zo eerlijk als waardoor het deelt. ClawMetry
bepaalt de venstergrootte per provider aan de hand van [een tabel die je kunt lezen en
er een PR voor kunt indienen](clawmetry/context_windows.py), met dekking voor Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama en GLM. Het meet niet alle 32
runtimes met de meetlat van één leverancier. Dat is belangrijk: een beurt van 300K tokens bij GPT-5
afgezet tegen Anthropics 200K leest als ">100%, geblazen" terwijl het eigenlijk op 75% van
GPT-5's 400K zit. Diezelfde meetlat verbergt een daadwerkelijk overvolle DeepSeek-beurt van 130K
als een comfortabele 65%.

Elk venster komt met zijn herkomst: `model_table`, `explicit_marker`,
`observed_floor`, of een eerlijke `default` wanneer we het model niet kennen. Een
meter gebouwd op een gok toont zich nooit met hetzelfde gezag als één gebouwd op
een opzoeking.

ClawMetry kan compactie-events maar op sommige runtimes zien. Dus
`GET /api/context-coverage` rapporteert, per runtime, of een **nul betekent
"draaide schoon" of "we zijn blind"**. Een `0` die eigenlijk blind betekent, zegt dat ook.
[Volledige details](docs/CONTEXT_BLOWOUT.md)

**Wat kost de instrumentatie?**

| Pad | Toegevoegd aan je agent | Standaard? |
|---|---|---|
| Session-file tailing (alle 32 runtimes) | **0**. Apart proces, geen ClawMetry-code in je agent | aan |
| HTTP-interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per LLM-call, oftewel 0,009% van een call van 5s | uit |
| Pre-tool hook gate (warme cache) | **+44 ms** per gate-gecontroleerde tool call, boven een interpreter-basis van 36 ms | uit |
| Enforcement proxy | **+9,7 ms** per LLM-call | uit |

Kosten voor het daemon-hostproces: **2.762 events/sec** inname, **710 bytes/event** op schijf
(67,7 MB per 100k events), en **~12% van één core** aanhoudend op een drukke
installatie. Dat laatste getal ligt boven ons eigen gestelde budget van 5-10%, dus het wordt
gepubliceerd als een bug om achterna te jagen in plaats van van de pagina weggelaten.

Gemeten op een Apple M2 Pro met `benchmarks/overhead.py`. De testopstelling voert
elke conditie in een apart proces uit, wisselt hun volgorde af, en **weigert
een getal af te drukken wanneer de rondes het niet eens zijn over het teken ervan**. Voer het uit op je eigen
machine in een minuut:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Elk pad wordt gemeten, inclusief de hook gates en de enforcement proxy,
en de testopstelling draait in CI op Linux, macOS en Windows. Twee resultaten die het waard zijn om te
kennen: de proxy kost ongeveer zeven keer meer op Windows dan op Linux, en
de daemon houdt momenteel ongeveer 12% van één core aan, boven ons eigen budget van 5-10%.
De ruwe JSON, de methode, en wat nog niet gemeten is, staan in
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prijzen

| Plan | Wat het dekt | Prijs |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, volledig dashboard, alleen lokaal | $0 |
| **Starter** | Elke andere runtime hierboven, vlootoverzicht, cloud sync | $9 per node / maand |
| **Pro** | Starter + controle en evaluatie: approvals, tool-risicobeleid, evals, afwijkingsdetectie, kostenoptimalisatie, OTel-export, manipulatiebestendig auditlog | $19 per node / maand |

Jaarabonnementen, Enterprise en de actuele bedragen staan op
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Self-hosted licentiesleutels
werken zonder de cloud (`clawmetry license`). De exacte verdeling tussen gratis en betaald staat
in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Je data blijft op je machine

ClawMetry leest lokale sessiebestanden en logs. **Er verlaten geen sessiegegevens je machine
tenzij je `clawmetry connect` uitvoert** — geen prompts, antwoorden, tool-argumenten, bestandsinhoud
of logregels. Wanneer je wel verbindt, is de snapshot end-to-end versleuteld
met een sleutel die je machine nooit verlaat, en wordt hij ontsleuteld in je browser. Als een
node geen sleutel heeft, wordt de upload overgeslagen in plaats van onversleuteld verstuurd, en geen
serverreactie kan dat uitschakelen.

Twee dingen draaien standaard voordat je verbindt, allebei opt-out en geen van beide
bevat sessiegegevens: een anonieme installatiemelding en een versiecontrole tegen
PyPI. Een standaardinstallatie zoekt ook eenmalig je publieke IP op voor een banner-regel bij het
opstarten. Elke bestemming, wat ze bevat en hoe je hem uitschakelt, staat vermeld in
[docs/EGRESS.md](docs/EGRESS.md); self-hosted, herconfigureerde en air-gapped installaties
doen helemaal geen optionele uitgaande calls.

De ontsleuteling gebeurt in je browser, in code die wij aan je leveren. Dat was vroeger
een belofte; nu is het iets dat je kunt controleren. Elke regel die met je sleutel in aanraking komt
staat in één leesbaar bestand, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
dat wordt meegeleverd in de wheel en woordelijk wordt geserveerd, vastgezet met een Subresource
Integrity-hash. Om te bevestigen dat de browser draait wat wij hebben gepubliceerd:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Wat dit niet bewijst: wij serveren de pagina die het bestand laadt, dus we zouden een
andere pagina kunnen serveren. Integrity-hashes beschermen je tegen een gecompromitteerde CDN,
niet tegen de leverancier. Wat je wint is dat elke vervanging opzettelijk moet zijn,
zichtbaar in de paginabron, en anders dan een artefact op PyPI
dat iedereen kan ophalen. Self-hosting of lokaal blijven verwijdert de
afhankelijkheid volledig.

## Installeren

```bash
pip install clawmetry     # daarna: clawmetry
```

Of de one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Vereist Python 3.8+ op macOS, Linux of Windows, en minstens één agentruntime op
dezelfde machine. Docker-instructies: [docs/DOCKER.md](docs/DOCKER.md).

Of laat de agent het voor je instellen. De skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
leert Claude Code, Codex, Cursor, Gemini CLI, Copilot of OpenCode om
ClawMetry te installeren, te rapporteren wat de agents op de machine doen en uitgeven,
op verzoek een sessie te stoppen, en risicovolle tool calls vast te houden voor goedkeuring:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Documentatie

| | |
|---|---|
| [Runtime-compatibiliteit](docs/compatibility.md) | Wat elke adapter leest, en hoe je een runtime toevoegt |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Vensters per provider, compactie versus overflow, dekking per runtime |
| [Overhead](docs/OVERHEAD.md) | Wat instrumentatie kost, gemeten, met de testopstelling om het te reproduceren |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis versus betaald, tiermatrix, license CLI |
| [Approvals & policies](docs/APPROVALS.md) | Controle vooraf op uitvoering, risicoscoring, goedkeuringen per telefoon |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporteer traces overal naartoe, neem OTLP van overal in |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain van begin tot eind, met uitvoerbare voorbeelden |
| [SDK tracking](docs/SDK_TRACKING.md) | Kostentoerekening voor agents die je zelf hebt gebouwd |
| [Chatkanalen](docs/CHANNELS.md) | De chatadapters die in Flow worden getoond |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw-opstellingen |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architectuur](ARCHITECTURE.md) · [Ontwikkeling](docs/DEVELOPMENT.md) | Hoe het intern werkt; draaien vanaf de broncode |
| [Telemetrie](docs/TELEMETRY.md) | De anonieme installatie- en desktop-open-meldingen, en hoe je ze uitschakelt |

## Screenshots

Elk getal hieronder komt van één echte machine, alleen-lezen, met niets vooraf ingevuld.

**Het vertelt je wanneer er iets mis is, niet alleen wat er is gebeurd.**
Twee afwijkingsbanners bovenaan: uitgaven die 7x het dagelijkse gemiddelde bedragen, en een
piek van 4,2x in kosten. Daaronder, 324 van de 667 recente sessies met een verspillingssignaal,
uitgesplitst naar oorzaak.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Het laat je zien waar het geld naartoe ging, in elk tijdvenster.**
$252,47 vandaag, $513,15 deze week, $1.312,92 deze maand, elk met de tokens
erachter en hoeveel je abonnement daar al van dekt. Daaronder, ongeveer $1.128/maand
uitgesplitst als terugwinbaar en $17.256/maand al bespaard door
cache-hergebruik.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Het tekent hoe een bericht een antwoord wordt.**
Het live flow-diagram: jij, het kanaal waarop het binnenkwam, de gateway, het model
dat op dit moment antwoordt, en elke tool waar het naar reikte. Nodes lichten op terwijl werk
erdoorheen beweegt.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Elke agent op de machine, in één tabel.**
Wat hij draait, wat hij kost in de laatste 24 uur en over zijn hele levensduur, wanneer
hij voor het laatst is gezien, wie de eigenaar is, en of een abonnement de rekening
dekt. 14 agents hier, 3 sessies aan het werk, 13 stil.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Het laat zien waar de tijd en het geld van een beurt naartoe gingen, tool voor tool.**
Eén beurt van een echte sessie: 11 tools in 11,2 minuten voor $1,16. Elke Bash-call
en modelcall krijgt zijn eigen balk op de tijdlijn, zodat het commando dat 4,1 minuten
liep en dat wat 226ms liep in één oogopslag van elkaar te onderscheiden zijn.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Het beoordeelt het werk, niet alleen de uitgaven.**
Een A deze week: 54 taken kwamen schoon terug, 2 ruwe kostten $48,57, en de
runs met te weinig activiteit om te beoordelen worden buiten het cijfer gehouden in plaats van
als overwinningen te worden meegeteld. Elke ruwe run linkt naar zijn trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Het laat zien waarom het contextvenster maar blijft vollopen.**
715K van een venster van 1M tokens bij de laatste beurt, een piek van 83,3%, 4 compacties
die allemaal proactief afgingen in plaats van bij een overflow, en het gebruik van
elke beurt daarachter.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Detectie draait zonder dat je iets hoeft te configureren.**
De ingebouwde detectors staan aan vanaf de installatie: agent werd stil, telemetriefeed
stopte, kostenpiek, tokenpiek, oplopende fouten, foutpiek, budget
overschreden, dreigingssignatuur gevonden, bevinding van een beveiligingstool, veranderde
beveiligingshouding. Je eigen regels zijn optioneel daarbovenop.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Een risicovolle call vasthouden is opt-in, en wordt uitgeschakeld verzonden.**
Recursieve deletes, force pushes, sudo, secrets, package-installaties en uitgaande
calls krijgen elk een regel die je kunt inschakelen. Tot je dat doet, kijkt ClawMetry toe
en verandert het niets. Zodra er één aanstaat, wachten overeenkomende calls hier (of op je telefoon)
op goedkeuring of afwijzing.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Meer, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Erkenning

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Stergeschiedenis

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
