<!-- i18n-src:b22579578775 -->
> Nederlands translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Een agent kan honderd tool-aanroepen doen zonder ook maar iets te bereiken.** ClawMetry
leest de sessiebestanden die je coding agents toch al schrijven en brengt de tijdlijn,
de tool-aanroepen en welke token- en kostengegevens de runtime ook maar prijsgeeft samen in één
overzicht, zodat je een lange run die werkt kunt onderscheiden van een die vastzit.

Werkt met **32 AI-agent runtimes**: Claude Code, OpenAI Codex, Hermes, OpenClaw en 28 andere. Eén dashboard voor je hele agent-vloot. ([de volledige lijst](SUPPORTED_RUNTIMES.txt), gegenereerd uit de catalogus.)

> 🌐 **Lees dit in:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [meer →](docs/i18n/)

Eén commando. Geen configuratie nodig. Detecteert alles automatisch.

```bash
pip install clawmetry && clawmetry
```

Opent op **http://localhost:8900**. Geen configuratie nodig: het vindt de agent runtimes
die je al hebt, leest ze alleen-lezen uit en verandert niets aan de manier waarop ze draaien.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Voordat je installeert

| | |
|---|---|
| **Wat het doet** | Leest de sessiebestanden en logs die je agents toch al schrijven. Geen SDK, geen codewijziging, geen instrumentatie in je app. |
| **Wat je ziet** | Sessietijdlijn, tool-voor-tool replay, uitsplitsing van tokens en kosten, en trajectsignalen (in een lus zitten, herhaalde mislukkingen), per runtime. |
| **Wat gratis is** | `pip install clawmetry` leest **OpenClaw, NVIDIA NemoClaw, Goose en Qwen Code** zonder account, zonder sleutel en zonder netwerkaanroep. De overige 28, waaronder Claude Code, Codex, Cursor en de rest, worden gelezen door de closed-source `clawmetry-pro`-companion, die meekomt met de proefperiode van 7 dagen of een abonnement. Zie [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) voor de exacte verdeling. |
| **Hoe je begint** | `pip install clawmetry && clawmetry`, open daarna localhost:8900. Nog geen agents op deze machine? `clawmetry --sample` opent met drie gelabelde synthetische sessies. |
| **Wat je machine verlaat** | Geen sessiegegevens, tenzij je `clawmetry connect` uitvoert. Twee dingen draaien standaard wel, allebei opt-out en geen van beide met sessie-inhoud: een anonieme installatiemelding en een PyPI-versiecontrole. Elke bestemming staat geïnventariseerd in [docs/EGRESS.md](docs/EGRESS.md), opnieuw opgebouwd vanuit een netwerkcapture in plaats van uit het lezen van commentaar. |

Twee beperkingen die het waard zijn te kennen voordat je de output beoordeelt: runtimes geven
heel verschillende gegevens vrij (sommige publiceren helemaal geen kosten, [de matrix](docs/compatibility.md)
laat zien welke, per runtime), en een actie observeren is niet hetzelfde als hem kunnen
blokkeren ([welke bedieningsmogelijkheden echt zijn, per runtime](docs/APPROVALS.md)).


## Werkt met 33 agent runtimes

**Gratis in de open source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**Bij een betaald abonnement:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Elke runtime krijgt hetzelfde dashboard. Draai er meerdere tegelijk en de
schakelaar in de header past elk tabblad opnieuw aan naar een van hen.

Heb je je eigen agent op een SDK gebouwd in plaats daarvan? De interceptor volgt ook
diens LLM-aanroepen. Zie [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Wat je krijgt

- **Sessies & transcripten**: wat elke agent deed, beurt voor beurt, met replay
- **Kosten & tokens**: per runtime, model, sessie en dag, met afwijkingsmarkeringen
- **Flow**: live diagram van berichten die door kanalen, modellen en tools bewegen
- **Brain**: de stream van redenerings- en tool-aanroep-gebeurtenissen, live
- **Context-overloop**: venstergebruik geschaald per provider, compactie versus geforceerde overloop, plus een per-runtime overzicht van wat we *niet* kunnen zien ([hoe](docs/CONTEXT_BLOWOUT.md))
- **Geheugen & vaardigheden**: de bestanden en vaardigheden die elke runtime daadwerkelijk laadde
- **Gezondheid & logs**: schijf, geheugen, foutpercentages, rate limits, live logstream
- **Meldingen**: budgetplafonds, foutpieken, agent-offline, doorgestuurd naar Slack, Discord, PagerDuty, Telegram, e-mail
- **Goedkeuringen**: pauzeer risicovolle tool-aanroepen *voordat* ze uitgevoerd worden en keur ze goed vanaf je telefoon ([hoe](docs/APPROVALS.md))

## Context-overloop, en wat monitoren kost

Twee vragen die het waard zijn om te beantwoorden voordat je een agent-vergelijkingstool vertrouwt.

**Hoe gaat het om met context-window-overloop tussen runtimes?**

Een gebruikspercentage is alleen zo eerlijk als waar het door gedeeld wordt. ClawMetry
schaalt het venster per provider op basis van [een tabel die je kunt lezen en waar je een
PR op kunt indienen](clawmetry/context_windows.py), die Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama en GLM dekt. Het meet niet alle 33
runtimes met de liniaal van één leverancier. Dat maakt uit: een beurt van 300K GPT-5-tokens
afgezet tegen Anthropics 200K leest als ">100%, overlopen" terwijl deze eigenlijk op 75% van
GPT-5's 400K zit. Diezelfde liniaal verbergt een daadwerkelijk overlopen beurt van 130K
DeepSeek-tokens als een comfortabele 65%.

Elk venster wordt geleverd met zijn herkomst: `model_table`, `explicit_marker`,
`observed_floor`, of een eerlijke `default` wanneer we het model niet kennen. Een
meter gebouwd op een gok wordt nooit weergegeven met hetzelfde gezag als een die op een
opzoeking gebouwd is.

ClawMetry kan compactiegebeurtenissen bij sommige runtimes zien, bij andere niet. Daarom
rapporteert `GET /api/context-coverage`, per runtime, of een **nul betekent "verliep
schoon" of "we zijn blind"**. Een `0` die eigenlijk blind betekent, zegt dat ook.
[Volledige details](docs/CONTEXT_BLOWOUT.md)

**Wat kost de instrumentatie?**

| Pad | Toegevoegd aan je agent | Standaard? |
|---|---|---|
| Sessiebestand-tailing (alle 33 runtimes) | **0**. Apart proces, geen ClawMetry-code in je agent | aan |
| HTTP-interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per LLM-aanroep, oftewel 0,009% van een aanroep van 5s | uit |
| Pre-tool hook-gate (warme cache) | **+44 ms** per gecontroleerde tool-aanroep, boven een interpreter-basis van 36 ms | uit |
| Handhavingsproxy | **+9,7 ms** per LLM-aanroep | uit |

Kosten voor de daemon-host: **2.762 gebeurtenissen/sec** ingest, **710 bytes/gebeurtenis** op
schijf (67,7 MB per 100k gebeurtenissen), en **~12% van één core** aanhoudend op een drukke
installatie. Dat laatste getal ligt boven ons eigen doel van 5-10%, dus het wordt
gepubliceerd als een bug om achteraan te jagen in plaats van van de pagina weggelaten.

Gemeten op een Apple M2 Pro met `benchmarks/overhead.py`. De testopstelling draait
elke conditie in een apart proces, wisselt hun volgorde af, en **weigert een getal te
tonen wanneer de rondes het niet eens zijn over het teken**. Draai het zelf op je eigen
machine in een minuut:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Elk pad wordt gemeten, inclusief de hook-gates en de handhavingsproxy,
en de testopstelling draait in CI op Linux, macOS en Windows. Twee resultaten die het waard
zijn om te weten: de proxy kost ongeveer zeven keer zoveel op Windows als op Linux, en
de daemon houdt momenteel ongeveer 12% van één core aan, boven ons eigen budget van
5-10%. De ruwe JSON, de methode, en wat nog niet gemeten is, staan in
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prijzen

| Abonnement | Wat het dekt | Prijs |
|---|---|---|
| **Gratis** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, volledig dashboard, alleen lokaal | $0 |
| **Starter** | Elke andere runtime hierboven, vlootoverzicht, cloudsynchronisatie | $9 per node / maand |
| **Pro** | Starter + besturing en evaluatie: goedkeuringen, tool-risicobeleid, evaluaties, afwijkingsdetectie, kostenoptimalisator, OTel-export, manipulatiebestendig auditlogboek | $19 per node / maand |

Jaarabonnementen, Enterprise en de actuele bedragen staan op
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Self-hosted licentiesleutels
werken zonder de cloud (`clawmetry license`). De exacte gratis/betaald-verdeling staat
in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Je gegevens blijven op je machine

ClawMetry leest lokale sessiebestanden en logs. **Er verlaten geen sessiegegevens je machine
tenzij je `clawmetry connect` uitvoert**, geen prompts, antwoorden, tool-argumenten,
bestandsinhoud of logregels. Wanneer je wel verbindt, is de snapshot end-to-end versleuteld
met een sleutel die je machine nooit verlaat, en wordt hij ontsleuteld in je browser. Als een
node geen sleutel heeft, wordt de upload overgeslagen in plaats van onversleuteld verstuurd, en
geen enkele serverreactie kan dat uitschakelen.

Twee dingen draaien standaard wel voordat je verbindt, allebei opt-out en geen van beide
met sessiegegevens: een anonieme installatiemelding en een versiecontrole tegen PyPI.
Een standaardinstallatie zoekt ook eenmalig je publieke IP-adres op voor een startbanierregel.
Elke bestemming, wat hij bevat en hoe je hem uitschakelt, staat vermeld in
[docs/EGRESS.md](docs/EGRESS.md); self-hosted, omgeleide en air-gapped installaties
doen helemaal geen optionele uitgaande aanroepen.

De ontsleuteling gebeurt in je browser, in code die wij je aanleveren. Dat was vroeger
een belofte; nu is het iets wat je kunt controleren. Elke regel die je sleutel aanraakt
staat in één leesbaar bestand, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
dat wordt meegeleverd in de wheel en woordelijk wordt geserveerd, vastgezet met een
Subresource-Integrity-hash. Om te bevestigen dat de browser draait wat wij hebben
gepubliceerd:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Wat dit niet bewijst: wij serveren de pagina die het bestand laadt, dus we zouden een
andere pagina kunnen serveren. Integrity-hashes beschermen je tegen een
gecompromitteerd CDN, niet tegen de leverancier. Wat je wint, is dat elke vervanging
opzettelijk moet zijn, zichtbaar in de paginabron, en afwijkend van een artefact op PyPI
dat iedereen kan ophalen. Self-hosting of alleen lokaal blijven, verwijdert die
afhankelijkheid volledig.

## Installeren

```bash
pip install clawmetry     # daarna: clawmetry
```

Of de one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Vereist Python 3.8+ op macOS, Linux of Windows, en minstens één agent runtime op
dezelfde machine. Docker-instructies: [docs/DOCKER.md](docs/DOCKER.md).

Of laat de agent het voor je instellen. De skill [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
leert Claude Code, Codex, Cursor, Gemini CLI, Copilot of OpenCode om
ClawMetry te installeren, te rapporteren wat de agents op de machine doen en uitgeven,
op verzoek een sessie te stoppen, en risicovolle tool-aanroepen aan te houden voor goedkeuring:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Documentatie

| | |
|---|---|
| [Runtime-compatibiliteit](docs/compatibility.md) | Wat elke adapter leest, en hoe je een runtime toevoegt |
| [Context-overloop](docs/CONTEXT_BLOWOUT.md) | Vensters per provider, compactie versus overloop, dekking per runtime |
| [Overhead](docs/OVERHEAD.md) | Wat instrumentatie kost, gemeten, met de testopstelling om het te reproduceren |
| [Rechten](docs/ENTITLEMENTS.md) | Gratis versus betaald, tiermatrix, licentie-CLI |
| [Goedkeuringen & beleid](docs/APPROVALS.md) | Controle vóór uitvoering, risicoscoring, goedkeuring via telefoon |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporteer traces overal naartoe, neem OTLP overal vandaan op |
| [Breng je eigen agent mee](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain van begin tot eind, met uitvoerbare voorbeelden |
| [SDK-tracking](docs/SDK_TRACKING.md) | Kostentoewijzing voor agents die je zelf gebouwd hebt |
| [Chatkanalen](docs/CHANNELS.md) | De chatadapters die in Flow worden getoond |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Gesandboxte NVIDIA NemoClaw-opstellingen |
| [Docker](docs/DOCKER.md) | Image, compose, volume-mounts |
| [Architectuur](ARCHITECTURE.md) · [Ontwikkeling](docs/DEVELOPMENT.md) | Hoe het intern werkt; draaien vanuit de broncode |
| [Telemetrie](docs/TELEMETRY.md) | De anonieme installatie- en desktop-open-meldingen, en hoe je ze uitschakelt |

## Screenshots

Elk getal hieronder komt van één echte machine, alleen-lezen, zonder dat er iets is voorgezaaid.

**Het vertelt je wanneer er iets mis is, niet alleen wat er is gebeurd.**
Twee afwijkingsbanners bovenaan: uitgaven die 7x het dagelijkse gemiddelde bedragen, en een
piek van 4,2x in kosten. Daaronder, 324 van de 667 recente sessies met een
verspillingssignaal, uitgesplitst naar oorzaak.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Het laat je zien waar het geld naartoe ging, in elk venster.**
$252,47 vandaag, $513,15 deze week, $1.312,92 deze maand, elk met de tokens
erachter en hoeveel daarvan je abonnement al dekt. Daaronder, ongeveer $1.128/maand
uitgesplitst als terugwinbaar en $17.256/maand al bespaard door cache-hergebruik.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Het tekent hoe een bericht een antwoord wordt.**
Het live flow-diagram: jij, het kanaal waarop het binnenkwam, de gateway, het model
dat op dit moment antwoordt, en elke tool die het aangreep. Knooppunten lichten op
naarmate werk erdoorheen beweegt.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Elke agent op de machine, in één tabel.**
Wat hij draait, wat hij kost in de laatste 24 uur en over zijn hele levensduur, wanneer
hij het laatst is gezien, wie de eigenaar is, en of een abonnement de rekening dekt. 14
agents hier, 3 sessies aan het werk, 13 stil.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Het laat zien waar de tijd en het geld van een beurt naartoe gingen, tool voor tool.**
Eén beurt van een echte sessie: 11 tools in 11,2 minuten voor $1,16. Elke Bash-aanroep
en modelaanroep krijgt zijn eigen balk op de tijdlijn, zodat het commando dat 4,1 minuten
liep en het commando dat 226ms liep in één oogopslag te onderscheiden zijn.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Het beoordeelt het werk, niet alleen de uitgaven.**
Een A deze week: 54 taken kwamen schoon terug, 2 ruwe kostten $48,57, en de
runs met te weinig activiteit om te beoordelen worden buiten de beoordeling gelaten
in plaats van als overwinningen geteld. Elke ruwe run linkt naar zijn trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Het laat zien waarom het contextvenster maar blijft vollopen.**
715K van een venster van 1M tokens op de laatste beurt, een piek van 83,3%, 4 compacties
die allemaal proactief afgingen in plaats van bij een overloop, en het gebruik van
elke beurt erachter.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Detectie werkt zonder dat jij iets hoeft te configureren.**
De ingebouwde detectors staan vanaf installatie aan: agent werd stil, telemetriefeed
stopte, kostenpiek, tokenpiek, oplopende fouten, foutpiek, budgetdrempel,
dreigingssignatuur gevonden, bevinding van beveiligingstool, veranderde
beveiligingshouding. Je eigen regels zijn optioneel daarbovenop.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Een risicovolle aanroep vasthouden is opt-in, en wordt uitgeschakeld verzonden.**
Recursieve verwijderingen, force pushes, sudo, geheimen, pakketinstallaties en uitgaande
aanroepen krijgen elk een regel die je kunt inschakelen. Totdat je dat doet, kijkt
ClawMetry toe en verandert niets. Zodra er één aan staat, wachten overeenkomende
aanroepen hier (of op je telefoon) op goedkeuring of afwijzing.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Meer, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Erkenning

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star-geschiedenis

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
