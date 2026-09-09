<!-- i18n-src:61beb8393e2f -->
> Svenska translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**En agent kan göra hundra verktygsanrop utan att göra framsteg.** ClawMetry
läser sessionsfilerna som dina kodande agenter redan skriver, och samlar tidslinjen,
verktygsanropen och all token- och kostnadsdata som runtimen exponerar i en
enda vy — så att du kan skilja en lång körning som fungerar från en som har fastnat.

Fungerar med **30 AI-agent-runtimes** — Claude Code, OpenAI Codex, Hermes, OpenClaw & 26 till. En instrumentpanel för hela din agentflotta. ([hela listan](SUPPORTED_RUNTIMES.txt), genererad från katalogen.)

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Ingen konfiguration. Upptäcker allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900**. Ingen konfiguration: den hittar de agent-runtimes
du redan har, läser dem skrivskyddat och ändrar ingenting i hur de körs.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Innan du installerar

| | |
|---|---|
| **Vad den gör** | Läser sessionsfilerna och loggarna dina agenter redan skriver. Ingen SDK, ingen kodändring, ingen instrumentering i din app. |
| **Vad du ser** | Sessionstidslinje, uppspelning verktyg för verktyg, uppdelning av tokens och kostnad, samt banor-signaler (loopar, upprepade fel) — per runtime. |
| **Vad som är gratis** | `pip install clawmetry` läser **OpenClaw, NVIDIA NemoClaw och Goose** utan konto, nyckel eller nätverksanrop. De andra 27 — Claude Code, Codex, Cursor och resten — läses av den slutna följeslagaren `clawmetry-pro`, som ingår i 7-dagarsprovperioden eller en plan — se [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) för den exakta uppdelningen. |
| **Hur du börjar** | `pip install clawmetry && clawmetry`, öppna sedan localhost:8900. Inga agenter på den här maskinen ännu? `clawmetry --sample` öppnas med tre märkta syntetiska sessioner. |
| **Vad som lämnar din maskin** | Ingen sessionsdata, om du inte kör `clawmetry connect`. Två saker körs som standard, båda går att stänga av och ingen av dem innehåller sessionsinnehåll: en anonym installationssignal och en PyPI-versionskontroll. Varje mål är inventerat i [docs/EGRESS.md](docs/EGRESS.md), återuppbyggt från en nätverksinspelning snarare än från att läsa kommentarer. |

Två begränsningar värda att känna till innan du bedömer resultatet: runtimes exponerar
väldigt olika data (vissa publicerar ingen kostnad alls — [matrisen](docs/compatibility.md)
visar vilka, per runtime), och att observera en åtgärd är inte samma sak som att kunna
blockera den ([vilka kontroller som är verkliga, per runtime](docs/APPROVALS.md)).


## Fungerar med 30 agent-runtimes

**Gratis i öppen källkod-appen:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**På en betalplan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Varje runtime får samma instrumentpanel. Kör flera samtidigt och rubrikväxlaren
växlar om varje flik till en av dem.

Byggde du din egen agent på en SDK istället? Interceptorn spårar dess LLM-anrop
också. Se [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Vad du får

- **Sessioner & transkript**: vad varje agent gjorde, tur för tur, med uppspelning
- **Kostnad & tokens**: per runtime, modell, session och dag, med avvikelseflaggor
- **Flöde**: livediagram över meddelanden som rör sig genom kanaler, modeller och verktyg
- **Hjärna**: strömmen av resonemang och verktygsanrop i realtid
- **Kontextöverbelastning**: fönsteranvändning dimensionerad per leverantör, komprimering kontra tvingad överflödning, plus en karta per runtime över vad vi *inte* kan se ([hur](docs/CONTEXT_BLOWOUT.md))
- **Minne & färdigheter**: filerna och färdigheterna som varje runtime faktiskt laddade
- **Hälsa & loggar**: disk, minne, felfrekvens, hastighetsgränser, live loggström
- **Varningar**: budgettak, feltoppar, agent-offline, dirigerat till Slack, Discord, PagerDuty, Telegram, e-post
- **Godkännanden**: pausa riskfyllda verktygsanrop *innan* de körs och godkänn från din telefon ([hur](docs/APPROVALS.md))

## Kontextöverbelastning, och vad övervakning kostar

Två frågor värda att besvara innan du litar på något verktyg för agentjämförelse.

**Hur hanterar den kontextfönster-överbelastning mellan runtimes?**

En användningsprocent är bara så ärlig som det den divideras med. ClawMetry
dimensionerar fönstret per leverantör från [en tabell du kan läsa och
skicka en PR till](clawmetry/context_windows.py), som täcker Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama och GLM. Den mäter inte alla 30
runtimes med en enda leverantörs måttstock. Det spelar roll: en 300K GPT-5-tur
jämförd mot Anthropics 200K läses som ">100%, överbelastad" när den egentligen
ligger på 75% av GPT-5:s 400K. Samma måttstock döljer en genuint överbelastad
130K DeepSeek-tur som en bekväm 65%.

Varje fönster levereras med sitt ursprung: `model_table`, `explicit_marker`,
`observed_floor`, eller en ärlig `default` när vi inte känner till modellen. En
mätare byggd på en gissning visas aldrig med samma auktoritet som en byggd på
en uppslagning.

ClawMetry kan bara se komprimeringshändelser på vissa runtimes. Så
`GET /api/context-coverage` rapporterar, per runtime, om en **nolla betyder
"kördes rent" eller "vi är blinda"**. En `0` som faktiskt betyder blind säger det.
[Fullständig information](docs/CONTEXT_BLOWOUT.md)

**Vad kostar instrumenteringen?**

| Väg | Tillagt till din agent | Standard? |
|---|---|---|
| Sessionsfilssvansning (alla 30 runtimes) | **0**. Separat process, ingen ClawMetry-kod i din agent | på |
| HTTP-interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per LLM-anrop, eller 0,009% av ett 5-sekundersanrop | av |
| Pre-tool hook-grind (varm cache) | **+44 ms** per gated verktygsanrop, över ett 36 ms tolkgolv | av |
| Verkställighetsproxy | **+9,7 ms** per LLM-anrop | av |

Kostnad för daemon-värd: **2 762 händelser/sek** inmatning, **710 bytes/händelse**
på disk (67,7 MB per 100k händelser), och **~12% av en kärna** varaktigt vid en
upptagen installation. Det sista talet ligger över vår egen angivna budget på
5-10%, så det publiceras som en bugg att jaga snarare än att utelämnas från sidan.

Mätt på en Apple M2 Pro med `benchmarks/overhead.py`. Testramverket kör varje
tillstånd i en separat process, alternerar deras ordning, och **vägrar att skriva
ut ett tal när omgångarna inte är överens om dess tecken**. Kör det på din egen
maskin på en minut:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Varje väg mäts, inklusive hook-grindarna och verkställighetsproxyn,
och testramverket körs på Linux, macOS och Windows i CI. Två resultat värda
att känna till: proxyn kostar ungefär sju gånger mer på Windows än på Linux, och
daemonen upprätthåller för närvarande cirka 12% av en kärna, över vår egen 5-10%-
budget. Rådatan i JSON, metoden och vad som fortfarande är omätt finns i
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prissättning

| Plan | Vad den täcker | Pris |
|---|---|---|
| **Gratis** | OpenClaw + NVIDIA NemoClaw + Goose, full instrumentpanel, endast lokalt | $0 |
| **Starter** | Alla andra runtimes ovan, flottvy, molnsynkronisering | $9 per nod / månad |
| **Pro** | Starter + kontroll och utvärdering: godkännanden, verktygsriskpolicyer, utvärderingar, avvikelsedetektering, kostnadsoptimerare, OTel-export, manipulationssäker granskningslogg | $19 per nod / månad |

Årliga planer, Enterprise och aktuella priser finns på
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Självhostade licensnycklar
fungerar utan molnet (`clawmetry license`). Den exakta gratis/betald-uppdelningen finns
i [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Din data stannar på din maskin

ClawMetry läser lokala sessionsfiler och loggar. **Ingen sessionsdata lämnar din
maskin om du inte kör `clawmetry connect`** — inga prompter, svar, verktygsargument,
filinnehåll eller loggrader. När du väl ansluter är ögonblicksbilden totalsträckskrypterad
med en nyckel som aldrig lämnar din maskin, och dekrypteras i din webbläsare. Om en
nod saknar en nyckel hoppas uppladdningen över istället för att skickas i klartext, och
inget serversvar kan slå av det.

Två saker körs som standard innan du ansluter, båda går att stänga av och ingen av
dem innehåller sessionsdata: en anonym installationssignal och en versionskontroll mot
PyPI. En standardinstallation slår också upp din publika IP-adress en gång för en
startbanderad. Varje mål, vad det innehåller och hur man stänger av det listas i
[docs/EGRESS.md](docs/EGRESS.md); självhostade, omdirigerade och isolerade installationer
gör inga valfria utgående anrop alls.

Dekrypteringen sker i din webbläsare, i kod vi levererar till dig. Det brukade vara
ett löfte; nu är det något du kan kontrollera. Varje rad som rör din nyckel finns i
en läsbar fil, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
som levereras inuti wheel-paketet och serveras ordagrant, fäst med en Subresource
Integrity-hash. För att bekräfta att webbläsaren kör det vi publicerade:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Vad detta inte bevisar: vi levererar sidan som laddar filen, så vi skulle kunna
leverera en annan sida. Integritetshashar skyddar dig mot ett komprometterat CDN,
inte mot leverantören. Det du vinner är att varje ersättning måste vara avsiktlig,
synlig i sidans källkod, och skiljer sig från en artefakt på PyPI som vem som helst
kan hämta. Att självhosta eller stanna helt lokalt tar bort beroendet helt.

## Installation

```bash
pip install clawmetry     # sedan: clawmetry
```

Eller enradsversionen: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kräver Python 3.8+ på macOS, Linux eller Windows, och minst en agent-runtime på
samma maskin. Docker-instruktioner: [docs/DOCKER.md](docs/DOCKER.md).

Eller låt agenten ställa in det åt dig. Färdigheten [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
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
| [Kontextöverbelastning](docs/CONTEXT_BLOWOUT.md) | Fönster per leverantör, komprimering kontra överflödning, täckning per runtime |
| [Overhead](docs/OVERHEAD.md) | Vad instrumentering kostar, mätt, med testramverket för att återskapa det |
| [Rättigheter](docs/ENTITLEMENTS.md) | Gratis kontra betald, nivåmatris, licens-CLI |
| [Godkännanden & policyer](docs/APPROVALS.md) | Gating före körning, riskbedömning, telefongodkännanden |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exportera spårningar var som helst, ta emot OTLP från vad som helst |
| [Ta med din egen agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain från början till slut, med körbara exempel |
| [SDK-spårning](docs/SDK_TRACKING.md) | Kostnadstillskrivning för agenter du byggt själv |
| [Chattkanaler](docs/CHANNELS.md) | Chattadaptrarna som visas i Flöde |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxade NVIDIA NemoClaw-uppsättningar |
| [Docker](docs/DOCKER.md) | Avbild, compose, volymmonteringar |
| [Arkitektur](ARCHITECTURE.md) · [Utveckling](docs/DEVELOPMENT.md) | Hur det fungerar inuti; köra från källkod |
| [Telemetri](docs/TELEMETRY.md) | De anonyma installations- och skrivbordsöppningssignalerna, och hur man stänger av dem |

## Skärmdumpar

Varje siffra nedan kommer från en verklig maskin, skrivskyddad, utan något förberett.

**Den berättar när något är fel, inte bara vad som hände.**
Två avvikelsebanderoller högst upp: förbrukning som ligger 7x det dagliga genomsnittet,
och en kostnadstopp på 4,2x. Under dem, 324 av 667 senaste sessioner som bär en
slöseri-signal, uppdelat efter orsak.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Den visar dig vart pengarna tog vägen, i varje tidsfönster.**
$252,47 idag, $513,15 denna vecka, $1 312,92 denna månad, var och en med tokensen
bakom och hur mycket av det din prenumeration redan täcker. Under det, cirka
$1 128/mån specificerat som återvinningsbart och $17 256/mån redan sparat genom
cacheåteranvändning.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Den ritar hur ett meddelande blir ett svar.**
Livediagrammet över flödet: du, kanalen det anlände på, gatewayen, modellen
som svarar just nu, och varje verktyg den använde. Noder tänds när arbete
rör sig genom dem.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Varje agent på maskinen, i en enda tabell.**
Vad den kör, vad den kostar de senaste 24 timmarna och under sin livstid, när
den senast sågs, vem som äger den, och om en prenumeration täcker notan. 14
agenter här, 3 sessioner som arbetar, 13 tysta.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Den visar var en turs tid och pengar tog vägen, verktyg för verktyg.**
En tur i en verklig session: 11 verktyg på 11,2 minuter för $1,16. Varje
Bash-anrop och modellanrop får sin egen stapel på tidslinjen, så att kommandot
som körde i 4,1 minuter och det som körde i 226 ms skiljs åt med en blick.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Den betygsätter arbetet, inte bara förbrukningen.**
Ett A denna vecka: 54 uppgifter kom tillbaka rena, 2 knöliga kostade $48,57, och
körningarna med för lite aktivitet för att bedöma lämnas utanför betyget istället
för att räknas som vinster. Varje knölig körning länkar till sin spårning.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Den visar varför kontextfönstret fortsätter att fyllas.**
715K av ett 1M-tokens fönster på den senaste turen, en topp på 83,3%, 4
komprimeringar som alla utlöstes proaktivt snarare än vid en överflödning, och
användningen av varje tur bakom det.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Detektering körs utan att du konfigurerar något.**
De inbyggda detektorerna är på från installationen: agenten blev tyst,
telemetriflödet stoppade, kostnadstopp, tokenutbrott, stigande fel, feltopp,
budgettröskel, hotsignatur matchad, säkerhetsverktygsfynd, säkerhetsstatus ändrad.
Dina egna regler är valfria ovanpå det.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Att hålla ett riskfyllt anrop är valfritt, och levereras avstängt.**
Rekursiva raderingar, tvingade push, sudo, hemligheter, paketinstallationer och
utgående anrop får var och en en regel du kan slå på. Tills du gör det observerar
ClawMetry och ändrar ingenting. Så snart en är påslagen väntar matchande anrop
här (eller på din telefon) på ett godkännande eller avslag.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Fler, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Erkännande

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Stjärnhistorik

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licens

MIT · Byggt av [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
