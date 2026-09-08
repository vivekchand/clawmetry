<!-- i18n-src:88be2deff5d5 -->
> Svenska translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Se din agent tänka.** Realtidsobservabilitet för **30 AI-agentruntider**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex & 26 till. En instrumentpanel för hela din agentflotta.

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Ingen konfiguration. Upptäcker allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900**. Ingen konfiguration: den hittar de
agentruntider du redan har, läser dem skrivskyddat och ändrar ingenting i hur de körs.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Fungerar med 30 agentruntider

**Gratis i open source-appen:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**På en betalplan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Varje runtime får samma instrumentpanel. Kör flera samtidigt så växlar rubrikväxlaren
alla flikar till en av dem.

Byggde du din egen agent på ett SDK istället? Interceptorn spårar även dess LLM-anrop.
Se [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Vad du får

- **Sessioner & transkript**: vad varje agent gjorde, tur för tur, med repriser
- **Kostnad & tokens**: per runtime, modell, session och dag, med avvikelsemarkeringar
- **Flöde**: livediagram över meddelanden som rör sig genom kanaler, modeller och verktyg
- **Brain**: strömmen av resonemang och verktygsanrop i realtid
- **Kontextöverbelastning**: fönsterutnyttjande dimensionerat per leverantör, kompaktering vs framtvingad överflöde, plus en karta per runtime över vad vi *inte* kan se ([hur](docs/CONTEXT_BLOWOUT.md))
- **Minne & färdigheter**: filerna och färdigheterna som varje runtime faktiskt laddade
- **Hälsa & loggar**: disk, minne, felfrekvens, hastighetsgränser, direktuppspelad loggström
- **Varningar**: budgettak, feltoppar, agent-offline, dirigerat till Slack, Discord, PagerDuty, Telegram, e-post
- **Godkännanden**: pausa riskfyllda verktygsanrop *innan* de körs och godkänn från din telefon ([hur](docs/APPROVALS.md))

## Kontextöverbelastning, och vad övervakning kostar

Två frågor värda att besvara innan du litar på ett verktyg som jämför agenter.

**Hur hanterar den kontextfönster-överbelastning mellan olika runtider?**

En utnyttjandeprocent är bara lika ärlig som det den divideras med. ClawMetry
dimensionerar fönstret per leverantör från [en tabell du kan läsa och
skicka PR till](clawmetry/context_windows.py), som täcker Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama och GLM. Den mäter inte alla 30
runtider med en enda leverantörs måttstock. Det spelar roll: en 300K GPT-5-tur
bedömd mot Anthropics 200K läses som ">100%, överbelastad" när den egentligen ligger på 75% av
GPT-5:s 400K. Samma måttstock döljer en genuint överbelastad 130K DeepSeek-tur
som en bekväm 65%.

Varje fönster levereras med sin proveniens: `model_table`, `explicit_marker`,
`observed_floor`, eller en ärlig `default` när vi inte känner till modellen. En
mätare byggd på en gissning renderas aldrig med samma auktoritet som en byggd på
en uppslagning.

ClawMetry kan bara se kompakteringshändelser på vissa runtider. Så
`GET /api/context-coverage` rapporterar, per runtime, om en **nolla betyder
"körde rent" eller "vi är blinda"**. En `0` som faktiskt betyder blind säger det.
[Fullständig detalj](docs/CONTEXT_BLOWOUT.md)

**Vad kostar instrumenteringen?**

| Väg | Tillagt till din agent | Standard? |
|---|---|---|
| Sessionsfilsavläsning (alla 30 runtider) | **0**. Separat process, ingen ClawMetry-kod i din agent | på |
| HTTP-interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per LLM-anrop, eller 0,009% av ett 5s-anrop | av |
| Pre-tool-hook-gate (varm cache) | **+44 ms** per grindat verktygsanrop, över ett 36 ms-tolkgolv | av |
| Verkställighetsproxy | **+9,7 ms** per LLM-anrop | av |

Kostnad för daemon-värd: **2 762 händelser/sek** ingest, **710 byte/händelse** på disk
(67,7 MB per 100 000 händelser), och **~12% av en kärna** ihållande på en installation med hög belastning. Den sista siffran ligger över vår egen angivna budget på 5-10%, så den
publiceras som en bugg att jaga snarare än att utelämnas från sidan.

Uppmätt på en Apple M2 Pro med `benchmarks/overhead.py`. Ramverket kör
varje förhållande i en separat process, alternerar deras ordning och **vägrar
skriva ut en siffra när omgångarna är oense om dess tecken**. Kör det på din egen
maskin på en minut:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Varje väg mäts, inklusive hook-grindarna och verkställighetsproxyn,
och ramverket körs på Linux, macOS och Windows i CI. Två resultat värda att
känna till: proxyn kostar ungefär sju gånger mer på Windows än på Linux, och
daemonen upprätthåller för närvarande omkring 12% av en kärna, över vår egen 5-10%-
budget. Rådatan i JSON, metoden och vad som fortfarande är omätt finns i
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prissättning

| Plan | Vad den täcker | Pris |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, fullständig instrumentpanel, endast lokalt | $0 |
| **Starter** | Alla andra runtider ovan, flottvy, molnsynkronisering | $9 per nod/månad |
| **Pro** | Starter + kontroll och utvärdering: godkännanden, verktygsriskpolicyer, utvärderingar, avvikelsedetektering, kostnadsoptimerare, OTel-export, manipulationssäker granskningslogg | $19 per nod/månad |

Årsplaner, Enterprise och de aktuella siffrorna finns på
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Självhostade licens-
nycklar fungerar utan molnet (`clawmetry license`). Den exakta gratis/betald-uppdelningen finns
i [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Din data stannar på din maskin

ClawMetry läser lokala sessionsfiler och loggar. **Ingen sessionsdata lämnar din maskin
såvida du inte kör `clawmetry connect`** — inga prompter, svar, verktygsargument, filinnehåll
eller loggrader. När du väl ansluter är ögonblicksbilden totalsträckskrypterad
med en nyckel som aldrig lämnar din maskin, och dekrypteras i din webbläsare. Om en
nod saknar nyckel hoppas uppladdningen över istället för att skickas i klartext, och ingen
serversvar kan slå av det.

Två saker körs som standard innan du ansluter, båda opt-out och ingen av dem
bär sessionsdata: en anonym installationsping och en versionskontroll mot
PyPI. En standardinstallation slår också upp din publika IP en gång för en startbannerrad.
Varje destination, vad den bär och hur man stänger av den listas i
[docs/EGRESS.md](docs/EGRESS.md); självhostade, omdirigerade och isolerade installationer
gör inga valfria utgående anrop alls.

Dekrypteringen sker i din webbläsare, i kod vi levererar till dig. Det brukade vara
ett löfte; nu är det något du kan kontrollera. Varje rad som rör din nyckel
finns i en läsbar fil, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
som levereras inuti wheel-paketet och serveras ordagrant, fäst med en Subresource
Integrity-hash. För att bekräfta att webbläsaren kör det vi publicerade:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Vad detta inte bevisar: vi levererar sidan som laddar filen, så vi skulle kunna
leverera en annan sida. Integritetshashar skyddar dig från en komprometterad CDN,
inte från leverantören. Det du vinner är att varje substitution måste vara
avsiktlig, synlig i sidans källkod, och skild från en artefakt på PyPI
som vem som helst kan hämta. Att självhosta eller stanna helt lokalt tar bort
beroendet helt.

## Installation

```bash
pip install clawmetry     # sedan: clawmetry
```

Eller enradaren: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kräver Python 3.8+ på macOS, Linux eller Windows, och minst en agentruntid på
samma maskin. Docker-instruktioner: [docs/DOCKER.md](docs/DOCKER.md).

Eller låt agenten sätta upp det åt dig. Färdigheten [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
lär Claude Code, Codex, Cursor, Gemini CLI, Copilot eller OpenCode att
installera ClawMetry, rapportera vad agenterna på maskinen gör och spenderar,
stoppa en session på begäran, och hålla riskfyllda verktygsanrop för godkännande:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokumentation

| | |
|---|---|
| [Runtime-kompatibilitet](docs/compatibility.md) | Vad varje adapter läser, och hur man lägger till en runtime |
| [Kontextöverbelastning](docs/CONTEXT_BLOWOUT.md) | Fönster per leverantör, kompaktering vs överflöde, täckning per runtime |
| [Overhead](docs/OVERHEAD.md) | Vad instrumenteringen kostar, uppmätt, med ramverket för att återskapa det |
| [Rättigheter](docs/ENTITLEMENTS.md) | Gratis vs betalt, nivåmatris, licens-CLI |
| [Godkännanden & policyer](docs/APPROVALS.md) | Grindning före körning, riskbedömning, godkännanden via telefon |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exportera spårningar var som helst, ta emot OTLP från vad som helst |
| [Ta med din egen agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain från start till slut, med körbara exempel |
| [SDK-spårning](docs/SDK_TRACKING.md) | Kostnadsattribuering för agenter du byggt själv |
| [Chattkanaler](docs/CHANNELS.md) | Chattadaptrarna som visas i Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxade NVIDIA NemoClaw-uppsättningar |
| [Docker](docs/DOCKER.md) | Avbildning, compose, volymmonteringar |
| [Arkitektur](ARCHITECTURE.md) · [Utveckling](docs/DEVELOPMENT.md) | Hur det fungerar invändigt; köra från källkod |
| [Telemetri](docs/TELEMETRY.md) | De anonyma installations- och skrivbordsöppning-pingarna, och hur man stänger av dem |

## Skärmdumpar

Varje siffra nedan är från en verklig maskin, skrivskyddad, utan något förberett.

**Den berättar för dig när något är fel, inte bara vad som hände.**
Två avvikelsebanderoller högst upp: förbrukning som löper 7x det dagliga genomsnittet, och en
4,2x kostnadstopp. Under dem, 324 av 667 nyliga sessioner som bär en slöseri-
signal, specificerade efter orsak.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Den visar dig vart pengarna tog vägen, i varje tidsfönster.**
$252,47 idag, $513,15 denna vecka, $1 312,92 denna månad, var och en med tokens
bakom sig och hur mycket av det din prenumeration redan täcker. Under det,
omkring $1 128/mån specificerade som återvinningsbara och $17 256/mån redan sparade genom
cache-återanvändning.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Den ritar upp hur ett meddelande blir ett svar.**
Livet flödesdiagram: dig, kanalen det anlände på, gatewayen, modellen
som svarar just nu, och varje verktyg den tog till. Noder tänds när arbete
rör sig genom dem.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Varje agent på maskinen, i en tabell.**
Vad den kör, vad den kostar under de senaste 24 timmarna och under sin livstid, när
den senast sågs, vem som äger den, och om en prenumeration täcker
notan. 14 agenter här, 3 sessioner i arbete, 13 tysta.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Den visar var en turs tid och pengar tog vägen, verktyg för verktyg.**
En tur i en verklig session: 11 verktyg på 11,2 minuter för $1,16. Varje Bash-
anrop och modellanrop får sin egen stapel på tidslinjen, så kommandot som kördes
i 4,1 minuter och det som kördes på 226 ms skiljs åt vid en blick.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Den betygsätter arbetet, inte bara förbrukningen.**
Ett A denna vecka: 54 uppgifter kom tillbaka rena, 2 grova kostade $48,57, och
körningarna med för lite aktivitet för att bedömas lämnas utanför betyget istället för
att räknas som vinster. Varje grov körning länkar till sin spårning.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Den visar varför kontextfönstret fortsätter fyllas.**
715K av ett 1M-tokens fönster på den senaste turen, en topp på 83,3%, 4 kompakteringar
som alla utlöstes proaktivt snarare än vid ett överflöde, och utnyttjandet av
varje tur bakom det.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Detektering körs utan att du behöver konfigurera något.**
De inbyggda detektorerna är på från installationen: agent blev tyst, telemetriflödet
stannade, kostnadstopp, tokenutbrott, stigande fel, feltoppar, budget-
tröskel, hotsignatur matchad, säkerhetsverktygsfynd, säkerhetsläge
ändrat. Dina egna regler är valfria utöver detta.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Att hålla ett riskfyllt anrop är opt-in, och levereras avstängt.**
Rekursiva raderingar, tvingade pushar, sudo, hemligheter, paketinstallationer och utgående
anrop får var och en en regel du kan slå på. Tills du gör det övervakar ClawMetry och
ändrar ingenting. När en väl är på väntar matchande anrop här (eller på din telefon)
på ett godkännande eller ett avslag.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Mer, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Stjärnhistorik

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licens

MIT · Byggd av [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
