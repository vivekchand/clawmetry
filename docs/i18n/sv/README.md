<!-- i18n-src:c99ac0512cae -->
> Svenska translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**En agent kan göra hundra verktygsanrop utan att göra framsteg.** ClawMetry
läser sessionsfilerna som dina kodande agenter redan skriver, och samlar tidslinjen,
verktygsanropen och vilken token- och kostnadsdata körtiden exponerar i en enda
vy, så att du kan skilja en lång körning som fungerar från en som har fastnat.

Fungerar med **33 AI-agentkörtider** (AI agent runtimes) — Claude Code, OpenAI Codex, Hermes, OpenClaw och 29 till. En instrumentpanel för hela din agentflotta. ([hela listan](SUPPORTED_RUNTIMES.txt), genererad från katalogen.)

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Ingen konfiguration. Upptäcker allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900**. Ingen konfiguration: den hittar de agentkörtider
du redan har, läser dem skrivskyddat och ändrar ingenting i hur de körs.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Innan du installerar

| | |
|---|---|
| **Vad den gör** | Läser sessionsfilerna och loggarna dina agenter redan skriver. Ingen SDK, ingen kodändring, ingen instrumentering i din app. |
| **Vad du ser** | Sessionstidslinje, uppspelning verktyg för verktyg, uppdelning av tokens och kostnad, samt trajektoriesignaler (loopning, upprepade fel) per körtid. |
| **Vad som är gratis** | `pip install clawmetry` läser **OpenClaw, NVIDIA NemoClaw, Goose och Qwen Code** utan konto, utan nyckel och utan nätverksanrop. De andra 28 — Claude Code, Codex, Cursor och resten — läses av den slutna kompletteringen `clawmetry-pro`, som kommer med den 7-dagars provperioden eller en plan. Se [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) för den exakta uppdelningen. |
| **Hur du börjar** | `pip install clawmetry && clawmetry`, öppna sedan localhost:8900. Inga agenter på den här maskinen än? `clawmetry --sample` öppnas med tre märkta syntetiska sessioner. |
| **Vad som lämnar din maskin** | Inga sessionsdata, om du inte kör `clawmetry connect`. Två saker körs som standard, båda går att stänga av och ingen av dem bär sessionsinnehåll: en anonym installationssignal och en PyPI-versionskontroll. Varje destination finns inventerad i [docs/EGRESS.md](docs/EGRESS.md), återuppbyggd från en nätverksinspelning snarare än från att läsa kommentarer. |

Två begränsningar som är värda att känna till innan du bedömer resultatet: körtider exponerar
väldigt olika data (vissa publicerar ingen kostnad alls — [matrisen](docs/compatibility.md)
visar vilka, per körtid), och att observera en åtgärd är inte samma sak som att kunna
blockera den ([vilka kontroller är verkliga, per körtid](docs/APPROVALS.md)).


## Fungerar med 33 agentkörtider

**Gratis i open source-appen:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**På en betalplan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Varje körtid får samma instrumentpanel. Kör flera samtidigt och
huvudväljaren omfokuserar varje flik till en av dem.

Byggt din egen agent på en SDK istället? Interceptorn spårar dess LLM-anrop
också. Se [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Vad du får

- **Sessioner & transkript**: vad varje agent gjorde, tur för tur, med uppspelning
- **Kostnad & tokens**: per körtid, modell, session och dag, med avvikelseflaggor
- **Flöde**: live-diagram över meddelanden som rör sig genom kanaler, modeller och verktyg
- **Brain**: resonemangs- och verktygsanropsströmmen i realtid
- **Kontextöverbelastning**: fönsteranvändning dimensionerad per leverantör, komprimering mot tvingad överflöde, plus en karta per körtid över vad vi *inte* kan se ([hur](docs/CONTEXT_BLOWOUT.md))
- **Minne & färdigheter**: filerna och färdigheterna varje körtid faktiskt laddade
- **Hälsa & loggar**: disk, minne, felfrekvens, hastighetsgränser, live-loggström
- **Varningar**: budgettak, felspikar, agent-offline, dirigerade till Slack, Discord, PagerDuty, Telegram, e-post
- **Godkännanden**: pausa riskabla verktygsanrop *innan* de körs och godkänn från din telefon ([hur](docs/APPROVALS.md))

## Kontextöverbelastning, och vad övervakning kostar

Två frågor som är värda att besvara innan du litar på något verktyg för agentjämförelse.

**Hur hanterar den kontextfönsteröverbelastning över körtider?**

En utnyttjandeprocent är bara så ärlig som det den delas med. ClawMetry
dimensionerar fönstret per leverantör från [en tabell du kan läsa och
skicka PR till](clawmetry/context_windows.py), som täcker Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama och GLM. Den mäter inte alla 33
körtider med en leverantörs linjal. Det spelar roll: en 300K GPT-5-tur
bedömd mot Anthropics 200K läses som ">100%, överbelastad" när den egentligen är vid 75% av
GPT-5:s 400K. Samma linjal gömmer en genuint överbelastad 130K DeepSeek-tur
som en bekväm 65%.

Varje fönster levereras med sin proveniens: `model_table`, `explicit_marker`,
`observed_floor`, eller en ärlig `default` när vi inte känner till modellen. En
mätare byggd på en gissning renderas aldrig med samma auktoritet som en byggd på
en uppslagning.

ClawMetry kan bara se komprimeringshändelser på vissa körtider. Så
`GET /api/context-coverage` rapporterar, per körtid, om en **nolla betyder
"körde rent" eller "vi är blinda"**. En `0` som faktiskt betyder blind säger så.
[Fullständiga detaljer](docs/CONTEXT_BLOWOUT.md)

**Vad kostar instrumenteringen?**

| Väg | Tillagt till din agent | Standard? |
|---|---|---|
| Sessionsfilsövervakning (alla 33 körtider) | **0**. Separat process, ingen ClawMetry-kod i din agent | på |
| HTTP-interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per LLM-anrop, eller 0,009% av ett 5s-anrop | av |
| Pre-tool hook-gate (varm cache) | **+44 ms** per grindat verktygsanrop, över ett golv på 36 ms för tolken | av |
| Verkställighetsproxy | **+9,7 ms** per LLM-anrop | av |

Daemon-värdkostnad: **2 762 händelser/sek** inmatning, **710 byte/händelse** på disk
(67,7 MB per 100 000 händelser), och **~12% av en kärna** sammanhängande på en
belastad installation. Den sista siffran ligger över vår egen uttalade budget på 5-10%, så den
publiceras som en bugg att jaga snarare än att utelämnas från sidan.

Uppmätt på en Apple M2 Pro med `benchmarks/overhead.py`. Testriggen kör
varje tillstånd i en separat process, alternerar deras ordning, och **vägrar
skriva ut en siffra när omgångarna är oense om dess tecken**. Kör den på din egen
maskin på en minut:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Varje väg är uppmätt, inklusive hook-grindarna och verkställighetsproxyn,
och testriggen körs på Linux, macOS och Windows i CI. Två resultat som är värda att
känna till: proxyn kostar ungefär sju gånger mer på Windows än på Linux, och
daemonen håller just nu omkring 12% av en kärna, över vår egen budget på 5-10%.
Rådata i JSON, metoden och vad som fortfarande är omätt finns i
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prissättning

| Plan | Vad den täcker | Pris |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, fullständig instrumentpanel, endast lokalt | 0 USD |
| **Starter** | Alla andra körtider ovan, flottvy, molnsynkronisering | 9 USD per nod / månad |
| **Pro** | Starter + kontroll och utvärdering: godkännanden, verktygsriskpolicyer, utvärderingar, avvikelsedetektering, kostnadsoptimerare, OTel-export, manipulationssäker revisionslogg | 19 USD per nod / månad |

Årsplaner, Enterprise och de aktuella siffrorna finns på
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Självhostade licensnycklar
fungerar utan molnet (`clawmetry license`). Den exakta uppdelningen mellan gratis och betalt finns
i [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Dina data stannar på din maskin

ClawMetry läser lokala sessionsfiler och loggar. **Inga sessionsdata lämnar din maskin
om du inte kör `clawmetry connect`** — inga prompter, svar, verktygsargument, filinnehåll
eller loggrader. När du väl ansluter är ögonblicksbilden end-to-end-krypterad
med en nyckel som aldrig lämnar din maskin, och dekrypteras i din webbläsare. Om en
nod inte har någon nyckel hoppas uppladdningen över snarare än skickas i klartext, och inget
serversvar kan stänga av det.

Två saker körs som standard innan du ansluter, båda går att stänga av och ingen av dem
bär sessionsdata: en anonym installationssignal och en versionskontroll mot
PyPI. En standardinstallation slår även upp din publika IP en gång för en startbanner-
rad. Varje destination, vad den bär och hur du stänger av den listas i
[docs/EGRESS.md](docs/EGRESS.md); självhostade, omdirigerade och luftgapade installationer
gör inga valfria utgående anrop alls.

Dekrypteringen sker i din webbläsare, i kod vi levererar till dig. Det brukade vara
ett löfte; nu är det något du kan kontrollera. Varje rad som rör din nyckel
finns i en läsbar fil, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
som skeppas inuti wheel-paketet och levereras ordagrant, pinnad med en Subresource
Integrity-hash. För att bekräfta att webbläsaren körs med vad vi publicerat:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Vad detta inte bevisar: vi levererar sidan som laddar filen, så vi skulle kunna
leverera en annan sida. Integritetshashar skyddar dig från en komprometterad CDN,
inte från leverantören. Vad du vinner är att varje substitution måste vara
avsiktlig, synlig i sidans källkod, och skilja sig från en artefakt på PyPI
som vem som helst kan hämta. Att självhosta eller stanna lokalt tar bort
beroendet helt.

## Installation

```bash
pip install clawmetry     # sedan: clawmetry
```

Eller en-radaren: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kräver Python 3.8+ på macOS, Linux eller Windows, och minst en agentkörtid på
samma maskin. Docker-instruktioner: [docs/DOCKER.md](docs/DOCKER.md).

Eller låt agenten sätta upp det åt dig. Färdigheten [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
lär Claude Code, Codex, Cursor, Gemini CLI, Copilot eller OpenCode att
installera ClawMetry, rapportera vad agenterna på maskinen gör och spenderar,
stoppa en session på begäran, och hålla riskabla verktygsanrop för godkännande:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokumentation

| | |
|---|---|
| [Körtidskompatibilitet](docs/compatibility.md) | Vad varje adapter läser, och hur man lägger till en körtid |
| [Kontextöverbelastning](docs/CONTEXT_BLOWOUT.md) | Fönster per leverantör, komprimering mot överflöde, täckning per körtid |
| [Overhead](docs/OVERHEAD.md) | Vad instrumentering kostar, uppmätt, med testriggen för att återskapa det |
| [Entitlements](docs/ENTITLEMENTS.md) | Gratis mot betalt, nivåmatris, licens-CLI |
| [Godkännanden & policyer](docs/APPROVALS.md) | Grindning före körning, riskbedömning, godkännanden via telefon |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exportera spår var som helst, mata in OTLP från vad som helst |
| [Ta med din egen agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain från början till slut, med körbara exempel |
| [SDK-spårning](docs/SDK_TRACKING.md) | Kostnadsattribuering för agenter du byggt själv |
| [Chattkanaler](docs/CHANNELS.md) | Chattadaptrarna som visas i Flöde |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandlådade NVIDIA NemoClaw-uppsättningar |
| [Docker](docs/DOCKER.md) | Avbildning, compose, volymmonteringar |
| [Arkitektur](ARCHITECTURE.md) · [Utveckling](docs/DEVELOPMENT.md) | Hur det fungerar invändigt; köra från källkod |
| [Telemetri](docs/TELEMETRY.md) | De anonyma installations- och skrivbordsöppningssignalerna, och hur man stänger av dem |

## Skärmdumpar

Varje siffra nedan är från en verklig maskin, skrivskyddad, utan något förberett.

**Den talar om när något är fel, inte bara vad som hände.**
Två avvikelsebanderoller högst upp: utgifter som löper 7 gånger dagsgenomsnittet, och en
4,2 gångers kostnadsspik. Under dem, 324 av 667 senaste sessioner som bär en
slöserisignal, uppdelad efter orsak.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Den visar dig var pengarna gick, i varje tidsfönster.**
252,47 USD idag, 513,15 USD denna vecka, 1 312,92 USD denna månad, varje med tokens
bakom det och hur mycket av det ditt abonnemang redan täcker. Under det,
omkring 1 128 USD/mån uppdelat som återvinningsbart och 17 256 USD/mån redan sparat av
cacheåteranvändning.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Den ritar hur ett meddelande blir ett svar.**
Live-flödesdiagrammet: du, kanalen det anlände på, gatewayen, modellen
som svarar just nu, och varje verktyg den tog till. Noder lyser upp när arbete
rör sig genom dem.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Varje agent på maskinen, i en tabell.**
Vad den kör, vad den kostar de senaste 24 timmarna och under sin livstid, när
den senast sågs, vem som äger den, och om ett abonnemang täcker
notan. 14 agenter här, 3 sessioner arbetar, 13 tysta.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Den visar var en turs tid och pengar gick, verktyg för verktyg.**
En tur i en verklig session: 11 verktyg på 11,2 minuter för 1,16 USD. Varje Bash-
anrop och modellanrop får sitt eget stapel på tidslinjen, så att kommandot som kördes
i 4,1 minuter och det som kördes i 226 ms skiljs åt med en snabb blick.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Den betygsätter arbetet, inte bara utgifterna.**
Ett A denna vecka: 54 uppgifter kom tillbaka rena, 2 ojämna kostade 48,57 USD, och
körningarna med för lite aktivitet för att bedöma lämnas utanför betyget istället för
att räknas som vinster. Varje ojämn körning länkar till sitt spår.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Den visar varför kontextfönstret fortsätter fyllas.**
715K av ett 1M-tokens fönster på den senaste turen, en topp på 83,3%, 4 komprimeringar
som alla utlöstes proaktivt snarare än vid ett överflöde, och användningen av
varje tur bakom det.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Detektering körs utan att du konfigurerar något.**
De inbyggda detektorerna är på från installationen: agenten blev tyst, telemetriflödet
stoppade, kostnadsspik, tokenstöt, fel som klättrar, felspik, budget-
tröskel, hotsignatur matchad, säkerhetsverktygsfynd, säkerhetsläge
ändrat. Dina egna regler är valfria utöver det.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Att hålla ett riskabelt anrop är valfritt, och levereras avstängt.**
Rekursiva borttagningar, force push, sudo, hemligheter, paketinstallationer och utgående
anrop får var sin regel du kan slå på. Tills du gör det observerar ClawMetry och
ändrar ingenting. När en är på väntar matchande anrop här (eller på din telefon)
på ett godkännande eller avslag.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Fler, per körtid: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
