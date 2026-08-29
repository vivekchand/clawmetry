<!-- i18n-src:d21bea5161e0 -->
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

Opent op **http://localhost:8900**. Geen configuratie nodig: het vindt de agentruntimes
die je al hebt, leest ze alleen-lezen, en verandert niets aan hoe ze draaien.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Werkt met 30 agentruntimes

**Gratis in de open source app:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**Op een betaald plan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Elke runtime krijgt hetzelfde dashboard. Draai er meerdere tegelijk en de
schakelaar in de header herschaalt elke tab naar een van hen.

Heb je je eigen agent gebouwd op een SDK in plaats daarvan? De interceptor
volgt ook diens LLM-aanroepen. Zie [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Wat je krijgt

- **Sessies & transcripten**: wat elke agent deed, beurt voor beurt, met replay
- **Kosten & tokens**: per runtime, model, sessie en dag, met afwijkingsmeldingen
- **Flow**: live diagram van berichten die door kanalen, modellen en tools bewegen
- **Brain**: de stream van redeneer- en tool-aanroep-events terwijl ze gebeuren
- **Context blowout**: venstergebruik per provider gedimensioneerd, compactie versus geforceerde overflow, plus een per-runtime kaart van wat we *niet* kunnen zien ([hoe](docs/CONTEXT_BLOWOUT.md))
- **Memory & skills**: de bestanden en skills die elke runtime daadwerkelijk laadde
- **Health & logs**: schijf, geheugen, foutpercentages, rate limits, live logstream
- **Alerts**: budgetgrenzen, foutpieken, agent-offline, doorgestuurd naar Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals**: pauzeer riskante tool-aanroepen *voordat* ze draaien en keur ze goed vanaf je telefoon ([hoe](docs/APPROVALS.md))

## Context blowout, en wat het kost om te monitoren

Twee vragen die het waard zijn om te beantwoorden voordat je een tool voor het vergelijken van agents vertrouwt.

**Hoe gaat het om met context-window blowout over runtimes heen?**

Een gebruikspercentage is alleen zo eerlijk als waar het door wordt gedeeld.
ClawMetry dimensioneert het venster per provider vanuit [een tabel die je kunt
lezen en waarvoor je een PR kunt indienen](clawmetry/context_windows.py), die
Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama en GLM
dekt. Het meet niet alle 26 runtimes met de liniaal van één leverancier. Dat
maakt uit: een beurt van 300K bij GPT-5, gescoord tegen Anthropic's 200K,
leest als ">100%, geblazen" terwijl deze eigenlijk op 75% van GPT-5's 400K
zit. Diezelfde liniaal verbergt een daadwerkelijk overvolle DeepSeek-beurt van
130K als een comfortabele 65%.

Elk venster wordt geleverd met zijn herkomst: `model_table`,
`explicit_marker`, `observed_floor`, of een eerlijke `default` wanneer we het
model niet kennen. Een meter gebouwd op een gok wordt nooit met dezelfde
autoriteit weergegeven als één gebouwd op een opzoeking.

ClawMetry kan compactie-events slechts bij sommige runtimes zien. Daarom
rapporteert `GET /api/context-coverage` per runtime of een **nul betekent
"draaide schoon" of "we zijn blind"**. Een `0` die eigenlijk blind betekent
zegt dat ook. [Volledige uitleg](docs/CONTEXT_BLOWOUT.md)

**Wat kost de instrumentatie?**

| Pad | Toegevoegd aan je agent | Standaard? |
|---|---|---|
| Session-file tailing (alle 30 runtimes) | **0**. Apart proces, geen ClawMetry-code in je agent | aan |
| HTTP-interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per LLM-aanroep, oftewel 0,009% van een aanroep van 5s | uit |
| Pre-tool hook gate (warme cache) | **+44 ms** per gegateerde tool-aanroep, boven een interpreter-vloer van 36 ms | uit |
| Handhavingsproxy | **+9,7 ms** per LLM-aanroep | uit |

Kosten van de daemon-host: **2.762 events/sec** ingest, **710 bytes/event** op
schijf (67,7 MB per 100k events), en **~12% van één core** aanhoudend op een
drukke installatie. Dat laatste getal ligt boven ons eigen aangegeven budget
van 5-10%, dus het wordt gepubliceerd als een bug om achteraan te gaan in
plaats van van de pagina te worden weggelaten.

Gemeten op een Apple M2 Pro met `benchmarks/overhead.py`. De testopstelling
draait elke conditie in een apart proces, wisselt hun volgorde af, en
**weigert een getal te printen wanneer de rondes het niet eens zijn over het
teken ervan**. Draai het zelf op je eigen machine binnen een minuut:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Elk pad wordt gemeten, inclusief de hook gates en de handhavingsproxy, en de
testopstelling draait op Linux, macOS en Windows in CI. Twee resultaten die de
moeite waard zijn om te weten: de proxy kost ongeveer zeven keer meer op
Windows dan op Linux, en de daemon houdt momenteel ongeveer 12% van één core
aan, boven ons eigen budget van 5-10%. De ruwe JSON, de methode, en wat nog
niet gemeten is staan in [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prijzen

| Plan | Wat het dekt | Prijs |
|---|---|---|
| **Gratis** | OpenClaw + NVIDIA NemoClaw + Goose, volledig dashboard, alleen lokaal | $0 |
| **Starter** | Elke andere runtime hierboven, vlootoverzicht, cloudsync | $9 per node / maand |
| **Pro** | Starter + controle en evaluatie: approvals, tool-risicobeleid, evals, afwijkingsdetectie, kostenoptimalisatie, OTel-export, manipulatiebestendig auditlog | $19 per node / maand |

Jaarplannen, Enterprise en de actuele prijzen staan op
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Self-hosted
licentiesleutels werken zonder de cloud (`clawmetry license`). De exacte
gratis/betaald-verdeling staat in [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Je data blijft op je eigen machine

ClawMetry leest lokale sessiebestanden en logs. **Er verlaat geen sessiedata
je machine tenzij je `clawmetry connect` uitvoert** — geen prompts,
antwoorden, tool-argumenten, bestandsinhoud of logregels. Wanneer je wel
verbindt, wordt de snapshot end-to-end versleuteld met een sleutel die je
machine nooit verlaat, en ontsleuteld in je browser. Als een node geen sleutel
heeft, wordt de upload overgeslagen in plaats van onversleuteld verzonden, en
geen serverreactie kan dat uitschakelen.

Twee dingen draaien standaard voordat je verbindt, beide opt-out en geen van
beide met sessiedata: een anonieme installatieping en een versiecontrole tegen
PyPI. Een standaardinstallatie zoekt ook eenmalig je publieke IP-adres op voor
een opstartbannerregel. Elke bestemming, wat deze meedraagt en hoe je het
uitschakelt, staat in [docs/EGRESS.md](docs/EGRESS.md); self-hosted,
omgeleide en air-gapped installaties maken helemaal geen optionele uitgaande
aanroepen.

De ontsleuteling gebeurt in je browser, in code die wij aan je leveren. Dat
was voorheen een belofte; nu is het iets dat je kunt controleren. Elke regel
die je sleutel aanraakt, staat in één leesbaar bestand,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), dat wordt
meegeleverd in de wheel en woordelijk wordt geserveerd, vastgepind met een
Subresource Integrity-hash. Om te bevestigen dat de browser draait wat wij
publiceerden:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Wat dit niet bewijst: wij serveren de pagina die het bestand laadt, dus we
zouden een andere pagina kunnen serveren. Integrity-hashes beschermen je tegen
een gecompromitteerde CDN, niet tegen de leverancier. Wat je wint, is dat elke
vervanging opzettelijk moet zijn, zichtbaar in de paginabron, en verschillend
van een artefact op PyPI dat iedereen kan ophalen. Self-hosting of lokaal
blijven verwijdert de afhankelijkheid volledig.

## Installatie

```bash
pip install clawmetry     # daarna: clawmetry
```

Of de one-liner: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Vereist Python 3.8+ op macOS, Linux of Windows, en ten minste één
agentruntime op dezelfde machine. Docker-instructies: [docs/DOCKER.md](docs/DOCKER.md).

## Documentatie

| | |
|---|---|
| [Runtime-compatibiliteit](docs/compatibility.md) | Wat elke adapter leest, en hoe je een runtime toevoegt |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Vensters per provider, compactie versus overflow, dekking per runtime |
| [Overhead](docs/OVERHEAD.md) | Wat instrumentatie kost, gemeten, met de testopstelling om het te reproduceren |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis versus betaald, tiermatrix, license CLI |
| [Approvals & beleid](docs/APPROVALS.md) | Gating vóór uitvoering, risicoscoring, goedkeuring per telefoon |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exporteer traces overal naartoe, neem OTLP in van overal |
| [SDK-tracking](docs/SDK_TRACKING.md) | Kostentoewijzing voor agents die je zelf hebt gebouwd |
| [Chatkanalen](docs/CHANNELS.md) | De chatadapters getoond in Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw-opstellingen |
| [Docker](docs/DOCKER.md) | Image, compose, volume mounts |
| [Architectuur](ARCHITECTURE.md) · [Ontwikkeling](docs/DEVELOPMENT.md) | Hoe het intern werkt; draaien vanuit broncode |
| [Telemetrie](docs/TELEMETRY.md) | De anonieme installatie- en desktop-open-pings, en hoe je ze uitschakelt |

## Screenshots

Elk getal hieronder komt van één echte machine, alleen-lezen, zonder iets
voorgeprepareerd.

**Het vertelt je wanneer er iets mis is, niet alleen wat er gebeurde.**
Twee afwijkingsbanners bovenaan: uitgaven die 7x het dagelijkse gemiddelde
draaien, en een kostenpiek van 4,2x. Daaronder, 324 van de 667 recente
sessies met een verspillingssignaal, uitgesplitst naar oorzaak.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Het laat je zien waar het geld naartoe ging, in elk venster.**
$252,47 vandaag, $513,15 deze week, $1.312,92 deze maand, elk met de tokens
erachter en hoeveel je abonnement daar al van dekt. Daaronder, ongeveer
$1.128/maand uitgesplitst als terugwinbaar en $17.256/maand al bespaard door
cache-hergebruik.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Het tekent hoe een bericht een antwoord wordt.**
Het live flow-diagram: jij, het kanaal waarop het binnenkwam, de gateway, het
model dat nu antwoordt, en elke tool waarnaar het reikte. Nodes lichten op
naarmate het werk erdoorheen beweegt.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Elke agent op de machine, in één tabel.**
Wat hij draait, wat hij kost in de laatste 24 uur en over zijn levensduur,
wanneer hij voor het laatst gezien werd, wie de eigenaar is, en of een
abonnement de rekening dekt. 14 agents hier, 3 sessies aan het werk, 13 stil.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Het laat zien waar de tijd en het geld van een beurt naartoe gingen, tool voor tool.**
Eén beurt van een echte sessie: 11 tools in 11,2 minuten voor $1,16. Elke
Bash-aanroep en modelaanroep krijgt zijn eigen balk op de tijdlijn, zodat het
commando dat 4,1 minuten draaide en het commando dat 226ms draaide in één
oogopslag te onderscheiden zijn.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Het beoordeelt het werk, niet alleen de uitgaven.**
Een A deze week: 54 taken kwamen schoon terug, 2 ruwe kostten $48,57, en de
runs met te weinig activiteit om te beoordelen worden buiten het cijfer
gehouden in plaats van meegeteld als overwinningen. Elke ruwe run linkt naar
zijn trace.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Het laat zien waarom het contextvenster steeds voller raakt.**
715K van een venster van 1M tokens op de laatste beurt, een piek van 83,3%, 4
compacties die allemaal proactief afgingen in plaats van bij een overflow, en
het gebruik van elke beurt erachter.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Detectie draait zonder dat jij iets hoeft te configureren.**
De ingebouwde detectors staan aan vanaf installatie: agent werd stil,
telemetriefeed stopte, kostenpiek, tokenpiek, oplopende fouten, foutpiek,
budgetdrempel, dreigingssignatuur gematcht, beveiligingstool-bevinding,
beveiligingspostuur veranderd. Je eigen regels zijn optioneel bovenop.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Een riskante aanroep vasthouden is opt-in, en wordt uitgeschakeld geleverd.**
Recursieve verwijderingen, force pushes, sudo, secrets, pakketinstallaties en
uitgaande aanroepen krijgen elk een regel die je kunt inschakelen. Totdat je
dat doet, kijkt ClawMetry toe en verandert niets. Zodra er één aan staat,
wachten overeenkomende aanroepen hier (of op je telefoon) op een goedkeuring
of afwijzing.

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
