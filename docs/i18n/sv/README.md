<!-- i18n-src:9767c8001c9c -->
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

**Se din agent tänka.** Realtidsobservabilitet för **30 AI-agentkörtider**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex och 26 till. En instrumentpanel för hela din agentflotta.

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Ingen konfiguration. Upptäcker allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900**. Ingen konfiguration: den hittar de agentkörtider
du redan har, läser dem skrivskyddat och ändrar ingenting i hur de körs.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Fungerar med 30 agentkörtider

**Gratis i open source-appen:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**På en betalplan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Varje körtid får samma instrumentpanel. Kör flera samtidigt så växlar
huvudväxlaren varje flik till en av dem.

Har du byggt din egen agent på ett SDK istället? Interceptorn spårar
dess LLM-anrop också. Se [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Vad du får

- **Sessioner & transkript**: vad varje agent gjorde, tur för tur, med uppspelning
- **Kostnad & tokens**: per körtid, modell, session och dag, med avvikelseflaggor
- **Flöde**: livediagram över meddelanden som rör sig genom kanaler, modeller och verktyg
- **Brain**: resonemangs- och verktygsanropsströmmen i realtid
- **Kontextöverbelastning**: fönsteranvändning skalad per leverantör, komprimering kontra tvingad överflöd, plus en karta per körtid över vad vi *inte* kan se ([hur](docs/CONTEXT_BLOWOUT.md))
- **Minne & skills**: filerna och skills som varje körtid faktiskt laddade
- **Hälsa & loggar**: disk, minne, felfrekvenser, hastighetsgränser, liveloggström
- **Varningar**: budgettak, feltoppar, agent-offline, dirigerat till Slack, Discord, PagerDuty, Telegram, e-post
- **Godkännanden**: pausa riskfyllda verktygsanrop *innan* de körs och godkänn från din telefon ([hur](docs/APPROVALS.md))

## Kontextöverbelastning, och vad övervakning kostar

Två frågor värda att besvara innan du litar på något agentjämförelseverktyg.

**Hur hanterar den kontextfönster-överbelastning över olika körtider?**

En användningsprocent är bara så ärlig som det den divideras med. ClawMetry
skalar fönstret per leverantör från [en tabell du kan läsa och göra en
PR mot](clawmetry/context_windows.py), som täcker Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama och GLM. Den mäter inte alla 26
körtider med en enda leverantörs linjal. Det spelar roll: en 300K GPT-5-tur
mätt mot Anthropics 200K läses som ">100%, överbelastad" när den egentligen
ligger på 75% av GPT-5:s 400K. Samma linjal döljer en genuint överflödad
130K DeepSeek-tur som bekväma 65%.

Varje fönster levereras med sin proveniens: `model_table`, `explicit_marker`,
`observed_floor`, eller en ärlig `default` när vi inte känner till modellen. En
mätare byggd på en gissning renderas aldrig med samma auktoritet som en byggd
på en uppslagning.

ClawMetry kan bara se komprimeringshändelser på vissa körtider. Så
`GET /api/context-coverage` rapporterar, per körtid, om en **nolla betyder
"kördes rent" eller "vi är blinda"**. En `0` som faktiskt betyder blind säger det.
[Fullständig information](docs/CONTEXT_BLOWOUT.md)

**Vad kostar instrumenteringen?**

| Sökväg | Tillagt till din agent | Standard? |
|---|---|---|
| Sessionsfilsavläsning (alla 30 körtider) | **0**. Separat process, ingen ClawMetry-kod i din agent | på |
| HTTP-interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per LLM-anrop, eller 0,009% av ett 5s-anrop | av |
| Pre-tool hook-gate (varm cache) | **+44 ms** per grindat verktygsanrop, över ett 36 ms tolkgolv | av |
| Efterlevnadsproxy | **+9,7 ms** per LLM-anrop | av |

Daemon-värdkostnad: **2 762 händelser/sek** ingest, **710 byte/händelse** på disk
(67,7 MB per 100 000 händelser), och **~12% av en kärna** vid uthållig belastning på
en aktiv installation. Den sista siffran ligger över vår egen angivna 5-10%-budget,
så den publiceras som en bugg att jaga snarare än att utelämnas från sidan.

Mätt på en Apple M2 Pro med `benchmarks/overhead.py`. Testramverket kör
varje förhållande i en separat process, växlar deras ordning, och **vägrar
skriva ut ett tal när omgångarna är oense om dess tecken**. Kör det på din egen
maskin på en minut:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Varje sökväg mäts, inklusive hook-grindarna och efterlevnadsproxyn,
och testramverket körs på Linux, macOS och Windows i CI. Två resultat värda
att känna till: proxyn kostar ungefär sju gånger mer på Windows än på Linux, och
daemonen upprätthåller för närvarande ungefär 12% av en kärna, över vår egen
5-10%-budget. Rådatan i JSON, metoden och vad som fortfarande är omätt finns i
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prissättning

| Plan | Vad den täcker | Pris |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, fullständig instrumentpanel, endast lokalt | $0 |
| **Starter** | Alla andra körtider ovan, flottvy, molnsynkronisering | $9 per nod/månad |
| **Pro** | Starter + kontroll och utvärdering: godkännanden, verktygsriskpolicyer, utvärderingar, avvikelsedetektering, kostnadsoptimerare, OTel-export, manipulationssäker granskningslogg | $19 per nod/månad |

Årsplaner, Enterprise och aktuella siffror finns på
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Egenhostade licensnycklar
fungerar utan molnet (`clawmetry license`). Den exakta gratis/betal-uppdelningen finns
i [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Din data stannar på din maskin

ClawMetry läser lokala sessionsfiler och loggar. **Ingen sessionsdata lämnar din
maskin om du inte kör `clawmetry connect`** — inga prompter, svar, verktygsargument,
filinnehåll eller loggrader. När du väl ansluter är ögonblicksbilden totalsträckskrypterad
med en nyckel som aldrig lämnar din maskin, och dekrypteras i din webbläsare. Om en
nod saknar en nyckel hoppas uppladdningen över istället för att skickas okrypterat, och
inget serversvar kan slå av det.

Två saker körs som standard innan du ansluter, båda opt-out och ingen av dem
bär sessionsdata: en anonym installationsping och en versionskontroll mot
PyPI. En standardinstallation slår också upp din publika IP en gång för en
startbanner-rad. Varje destination, vad den bär och hur man stänger av den finns
listat i [docs/EGRESS.md](docs/EGRESS.md); egenhostade, omdirigerade och
luftgapade installationer gör inga valfria utgående anrop alls.

Dekrypteringen sker i din webbläsare, i kod vi levererar till dig. Det brukade
vara ett löfte; nu är det något du kan kontrollera. Varje rad som rör din nyckel
finns i en läsbar fil, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
som levereras inuti wheel-paketet och serveras ordagrant, fastnålad med en
Subresource Integrity-hash. För att bekräfta att webbläsaren kör det vi publicerade:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Vad detta inte bevisar: vi levererar sidan som laddar filen, så vi skulle kunna
leverera en annan sida. Integritetshashar skyddar dig från ett komprometterat
CDN, inte från leverantören. Det du vinner är att varje utbyte måste vara
avsiktligt, synligt i sidkällkoden, och skilja sig från en artefakt på PyPI
som vem som helst kan hämta. Att självhosta eller stanna endast lokalt
tar bort beroendet helt.

## Installation

```bash
pip install clawmetry     # sedan: clawmetry
```

Eller engångskommandot: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kräver Python 3.8+ på macOS, Linux eller Windows, och minst en agentkörtid på
samma maskin. Docker-instruktioner: [docs/DOCKER.md](docs/DOCKER.md).

## Dokumentation

| | |
|---|---|
| [Körtidskompatibilitet](docs/compatibility.md) | Vad varje adapter läser, och hur man lägger till en körtid |
| [Kontextöverbelastning](docs/CONTEXT_BLOWOUT.md) | Fönster per leverantör, komprimering kontra överflöd, täckning per körtid |
| [Overhead](docs/OVERHEAD.md) | Vad instrumentering kostar, uppmätt, med testramverket för att reproducera det |
| [Rättigheter](docs/ENTITLEMENTS.md) | Gratis kontra betalt, nivåmatris, licens-CLI |
| [Godkännanden & policyer](docs/APPROVALS.md) | Grindning före körning, riskbedömning, telefongodkännanden |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exportera spårningar var som helst, ta emot OTLP från vad som helst |
| [Ta med din egen agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain från början till slut, med körbara exempel |
| [SDK-spårning](docs/SDK_TRACKING.md) | Kostnadsattribuering för agenter du byggt själv |
| [Chattkanaler](docs/CHANNELS.md) | Chattadaptrarna som visas i Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxade NVIDIA NemoClaw-uppsättningar |
| [Docker](docs/DOCKER.md) | Avbild, compose, volymmonteringar |
| [Arkitektur](ARCHITECTURE.md) · [Utveckling](docs/DEVELOPMENT.md) | Hur det fungerar invändigt; köra från källkod |
| [Telemetri](docs/TELEMETRY.md) | De anonyma installations- och skrivbordsöppningspingarna, och hur man stänger av dem |

## Skärmdumpar

Varje siffra nedan kommer från en riktig maskin, skrivskyddad, utan något förberett.

**Den berättar när något är fel, inte bara vad som hände.**
Två avvikelsebanderoller högst upp: förbrukning som ligger på 7x dagsgenomsnittet, och
en 4,2x kostnadstopp. Under dem, 324 av 667 senaste sessioner som bär en
slöserisignal, specificerat efter orsak.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Den visar dig vart pengarna tog vägen, i varje tidsfönster.**
$252,47 idag, $513,15 denna vecka, $1 312,92 denna månad, var och en med tokens
bakom och hur mycket av det din prenumeration redan täcker. Under det,
ungefär $1 128/mån specificerat som återvinningsbart och $17 256/mån redan
sparat genom cacheåteranvändning.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Den ritar hur ett meddelande blir ett svar.**
Livediagrammet för flödet: du, kanalen det anlände på, gatewayen, modellen
som svarar just nu, och varje verktyg den nådde efter. Noder tänds när arbete
rör sig genom dem.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Varje agent på maskinen, i en enda tabell.**
Vad den kör, vad den kostar de senaste 24 timmarna och över sin livstid, när
den senast sågs, vem som äger den, och om en prenumeration täcker
kostnaden. 14 agenter här, 3 sessioner som arbetar, 13 tysta.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Den visar var en turs tid och pengar tog vägen, verktyg för verktyg.**
En tur i en riktig session: 11 verktyg på 11,2 minuter för $1,16. Varje
Bash-anrop och modellanrop får sitt eget stapel på tidslinjen, så kommandot
som kördes i 4,1 minuter och det som kördes i 226 ms kan skiljas åt med en
blick.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Den betygsätter arbetet, inte bara förbrukningen.**
Ett A denna vecka: 54 uppgifter kom tillbaka rena, 2 skrovliga kostade $48,57,
och körningarna med för lite aktivitet för att bedömas lämnas utanför betyget
istället för att räknas som vinster. Varje skrovlig körning länkar till sitt spår.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Den visar varför kontextfönstret fortsätter att fyllas.**
715K av ett 1M-tokens fönster på den senaste turen, en topp på 83,3%, 4
komprimeringar som alla utlöstes proaktivt snarare än vid ett överflöd, och
användningen för varje tur bakom det.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Detektering körs utan att du behöver konfigurera något.**
De inbyggda detektorerna är på från installationen: agenten blev tyst,
telemetriflödet stoppade, kostnadstopp, tokenutbrott, stigande fel,
felfrekvenstopp, budgettröskel, hotsignatur matchad, säkerhetsverktygsfynd,
ändrad säkerhetsställning. Dina egna regler är valfria utöver dessa.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Att hålla tillbaka ett riskfyllt anrop är opt-in, och levereras avstängt.**
Rekursiva raderingar, tvingade pushar, sudo, hemligheter, paketinstallationer
och utgående anrop får var sin regel du kan slå på. Tills du gör det
övervakar ClawMetry och ändrar ingenting. När en väl är på väntar matchande
anrop här (eller på din telefon) på ett godkännande eller avslag.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Fler, per körtid: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
