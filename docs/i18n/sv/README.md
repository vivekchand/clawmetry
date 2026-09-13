<!-- i18n-src:a855a14295b0 -->
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
verktygsanropen och vilken token- och kostnadsdata runtiden än exponerar i en
enda vy, så att du kan skilja en lång körning som fungerar från en som har fastnat.

Fungerar med **32 AI-agentruntider** – Claude Code, OpenAI Codex, Hermes, OpenClaw & 28 till. En instrumentpanel för hela din agentflotta. ([hela listan](SUPPORTED_RUNTIMES.txt), genererad från katalogen.)

> 🌐 **Läs detta på:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [fler →](docs/i18n/)

Ett kommando. Ingen konfiguration. Upptäcker allt automatiskt.

```bash
pip install clawmetry && clawmetry
```

Öppnas på **http://localhost:8900**. Ingen konfiguration: den hittar de agentruntider
du redan har, läser dem skrivskyddat och ändrar inget i hur de körs.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Innan du installerar

| | |
|---|---|
| **Vad den gör** | Läser sessionsfilerna och loggarna dina agenter redan skriver. Ingen SDK, ingen kodändring, ingen instrumentering i din app. |
| **Vad du ser** | Sessionstidslinje, verktyg-för-verktyg-uppspelning, uppdelning av token och kostnad, samt banesignaler (loopar, upprepade fel), per runtime. |
| **Vad som är gratis** | `pip install clawmetry` läser **OpenClaw, NVIDIA NemoClaw och Goose** utan konto, nyckel eller nätverksanrop. De övriga 27 – Claude Code, Codex, Cursor och resten – läses av det slutna kompanjonprogrammet `clawmetry-pro`, som följer med den 7-dagars provperioden eller en plan – se [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) för den exakta uppdelningen. |
| **Hur du börjar** | `pip install clawmetry && clawmetry`, öppna sedan localhost:8900. Inga agenter på den här maskinen ännu? `clawmetry --sample` öppnas med tre märkta syntetiska sessioner. |
| **Vad som lämnar din maskin** | Ingen sessionsdata, om du inte kör `clawmetry connect`. Två saker körs som standard, båda går att stänga av och ingen av dem för med sig sessionsinnehåll: en anonym installationsping och en PyPI-versionskontroll. Varje destination är inventerad i [docs/EGRESS.md](docs/EGRESS.md), återuppbyggd från en trafikinspelning snarare än från att läsa kommentarer. |

Två begränsningar värda att känna till innan du bedömer resultatet: runtider exponerar
mycket olika data (vissa publicerar ingen kostnad alls – [matrisen](docs/compatibility.md)
visar vilka, per runtime), och att observera en handling är inte samma sak som att kunna
blockera den ([vilka kontroller som är riktiga, per runtime](docs/APPROVALS.md)).


## Fungerar med 32 agentruntider

**Gratis i open source-appen:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**På en betalplan:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Varje runtime får samma instrumentpanel. Kör flera samtidigt och rubrikväljaren
byter om varje flik till en av dem.

Byggde du din egen agent med en SDK istället? Interceptorn spårar dess LLM-anrop
också. Se [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Vad du får

- **Sessioner och transkript**: vad varje agent gjorde, tur för tur, med uppspelning
- **Kostnad och tokens**: per runtime, modell, session och dag, med avvikelseflaggor
- **Flöde**: livediagram över meddelanden som rör sig genom kanaler, modeller och verktyg
- **Brain**: reasoning- och verktygsanropsströmmen i realtid
- **Kontextsprängning**: fönsteranvändning storleksanpassad per leverantör, komprimering kontra tvingad överflödning, plus en karta per runtime över vad vi *inte* kan se ([hur](docs/CONTEXT_BLOWOUT.md))
- **Minne och färdigheter**: filerna och färdigheterna varje runtime faktiskt laddade
- **Hälsa och loggar**: disk, minne, felfrekvenser, hastighetsgränser, live-loggström
- **Varningar**: budgettak, feltoppar, agent-offline, dirigerat till Slack, Discord, PagerDuty, Telegram, e-post
- **Godkännanden**: pausa riskfyllda verktygsanrop *innan* de körs och godkänn från din telefon ([hur](docs/APPROVALS.md))

## Kontextsprängning, och vad övervakning kostar

Två frågor värda att besvara innan du litar på något verktyg som jämför agenter.

**Hur hanterar den kontextfönster-sprängning över olika runtider?**

En användningsprocent är bara så ärlig som det den divideras med. ClawMetry
storleksanpassar fönstret per leverantör från [en tabell du kan läsa och
skicka PR till](clawmetry/context_windows.py), som täcker Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama och GLM. Den mäter inte alla 32
runtider med en enda leverantörs linjal. Det spelar roll: en 300K GPT-5-tur
poängsatt mot Anthropics 200K läser ">100 %, sprängt" när den egentligen ligger på 75 % av
GPT-5:s 400K. Samma linjal döljer en genuint överfylld 130K DeepSeek-tur
som en bekväm 65 %.

Varje fönster levereras med sitt ursprung: `model_table`, `explicit_marker`,
`observed_floor`, eller ett ärligt `default` när vi inte känner till modellen. En
mätare byggd på en gissning återges aldrig med samma auktoritet som en byggd på
en uppslagning.

ClawMetry kan bara se komprimeringshändelser på vissa runtider. Så
`GET /api/context-coverage` rapporterar, per runtime, om en **nolla betyder
"körde rent" eller "vi är blinda"**. En `0` som egentligen betyder blind säger det.
[Fullständig information](docs/CONTEXT_BLOWOUT.md)

**Vad kostar instrumenteringen?**

| Väg | Tillagt till din agent | Standard? |
|---|---|---|
| Sessionsfilssvansning (alla 32 runtider) | **0**. Separat process, ingen ClawMetry-kod i din agent | på |
| HTTP-interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** per LLM-anrop, eller 0,009 % av ett 5-sekundersanrop | av |
| Pre-tool hook-gate (varm cache) | **+44 ms** per grindat verktygsanrop, utöver ett tolkgolv på 36 ms | av |
| Genomdrivningsproxy | **+9,7 ms** per LLM-anrop | av |

Daemon-värdkostnad: **2 762 händelser/sek** intag, **710 byte/händelse** på disk
(67,7 MB per 100 000 händelser), och **~12 % av en kärna** ihållande på en upptagen
installation. Det sista talet överskrider vår egen uttalade budget på 5-10 %, så det är
publicerat som en bugg att jaga snarare än utelämnat från sidan.

Uppmätt på en Apple M2 Pro med `benchmarks/overhead.py`. Testramverket kör
varje tillstånd i en separat process, alternerar deras ordning, och **vägrar
att skriva ut ett tal när omgångarna inte är eniga om dess tecken**. Kör det på din egen
maskin på en minut:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Varje väg mäts, inklusive hook-grindarna och genomdrivningsproxyn,
och testramverket körs på Linux, macOS och Windows i CI. Två resultat värda att
känna till: proxyn kostar ungefär sju gånger mer på Windows än på Linux, och
daemonen håller för närvarande ungefär 12 % av en kärna, över vår egen budget på 5-10 %.
Rådatan i JSON, metoden och vad som fortfarande inte är mätt finns i
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Prissättning

| Plan | Vad den täcker | Pris |
|---|---|---|
| **Gratis** | OpenClaw + NVIDIA NemoClaw + Goose, fullständig instrumentpanel, endast lokalt | 0 $ |
| **Starter** | Alla andra runtider ovan, flottvy, molnsynkronisering | 9 $ per nod/månad |
| **Pro** | Starter + kontroll och utvärdering: godkännanden, riskpolicyer för verktyg, utvärderingar, avvikelsedetektering, kostnadsoptimerare, OTel-export, manipuleringssäker granskningslogg | 19 $ per nod/månad |

Årsplaner, Enterprise och de aktuella siffrorna finns på
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Egenhostade licensnycklar
fungerar utan molnet (`clawmetry license`). Den exakta uppdelningen mellan gratis och betalt finns
i [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Din data stannar på din maskin

ClawMetry läser lokala sessionsfiler och loggar. **Ingen sessionsdata lämnar din maskin
om du inte kör `clawmetry connect`** – inga prompter, svar, verktygsargument, filinnehåll
eller loggrader. När du väl ansluter är ögonblicksbilden end-to-end-krypterad
med en nyckel som aldrig lämnar din maskin, och dekrypteras i din webbläsare. Om en
nod saknar nyckel hoppas uppladdningen över istället för att skickas i klartext, och inget
serversvar kan stänga av det.

Två saker körs som standard innan du ansluter, båda går att stänga av och ingen av dem
för med sig sessionsdata: en anonym installationsping och en versionskontroll mot
PyPI. En standardinstallation slår också upp din publika IP-adress en gång för en startbanner-
rad. Varje destination, vad den för med sig och hur man stänger av den listas i
[docs/EGRESS.md](docs/EGRESS.md); egenhostade, omdirigerade och luftgapade installationer
gör inga valfria utgående anrop alls.

Dekrypteringen sker i din webbläsare, i kod vi levererar till dig. Det brukade vara
ett löfte; nu är det något du kan kontrollera. Varje rad som rör din nyckel
finns i en enda läsbar fil, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
som levereras inuti wheel-paketet och serveras ordagrant, fastnålad med ett Subresource
Integrity-hash. För att bekräfta att webbläsaren kör det vi publicerade:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Vad detta inte bevisar: vi serverar sidan som laddar filen, så vi skulle kunna
servera en annan sida. Integritetshash skyddar dig från ett komprometterat CDN,
inte från leverantören. Vad du vinner är att varje substitution måste vara
avsiktlig, synlig i sidkällkoden, och skild från en artefakt på PyPI
som vem som helst kan hämta. Att självhosta eller stanna endast lokalt tar bort
beroendet helt.

## Installera

```bash
pip install clawmetry     # sedan: clawmetry
```

Eller engångskommandot: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Kräver Python 3.8+ på macOS, Linux eller Windows, och minst en agentruntime på
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
| [Kontextsprängning](docs/CONTEXT_BLOWOUT.md) | Fönster per leverantör, komprimering kontra överflöde, täckning per runtime |
| [Overhead](docs/OVERHEAD.md) | Vad instrumentering kostar, uppmätt, med testramverket för att reproducera det |
| [Rättigheter](docs/ENTITLEMENTS.md) | Gratis kontra betalt, nivåmatris, licens-CLI |
| [Godkännanden och policyer](docs/APPROVALS.md) | Grindning före körning, riskpoängsättning, telefongodkännanden |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Exportera spårningar överallt, ta emot OTLP från vad som helst |
| [Ta med din egen agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain från start till slut, med körbara exempel |
| [SDK-spårning](docs/SDK_TRACKING.md) | Kostnadsattribution för agenter du byggde själv |
| [Chattkanaler](docs/CHANNELS.md) | Chattadaptrarna som visas i Flöde |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandlådebaserade NVIDIA NemoClaw-installationer |
| [Docker](docs/DOCKER.md) | Avbildning, compose, volymmonteringar |
| [Arkitektur](ARCHITECTURE.md) · [Utveckling](docs/DEVELOPMENT.md) | Hur det fungerar invändigt; köra från källkod |
| [Telemetri](docs/TELEMETRY.md) | De anonyma installations- och skrivbordsöppningspingarna, och hur man stänger av dem |

## Skärmdumpar

Varje siffra nedan kommer från en riktig maskin, skrivskyddad, utan något förberett.

**Den berättar när något är fel, inte bara vad som hände.**
Två avvikelsebanners högst upp: utgifter som ligger 7x det dagliga genomsnittet, och en
4,2x kostnadstopp. Under dem, 324 av 667 nya sessioner som bär en slöseri-
signal, specificerade efter orsak.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Den visar dig vart pengarna tog vägen, i varje fönster.**
252,47 $ idag, 513,15 $ denna vecka, 1 312,92 $ denna månad, var och en med tokens
bakom sig och hur mycket av det din prenumeration redan täcker. Under det,
cirka 1 128 $/månad specificerat som återvinningsbart och 17 256 $/månad redan sparat
genom cacheåteranvändning.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Den ritar hur ett meddelande blir ett svar.**
Livesflödesdiagrammet: du, kanalen det anlände på, gatewayen, modellen som
svarar just nu, och varje verktyg den tog till. Noder lyser upp när arbete
rör sig genom dem.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Varje agent på maskinen, i en tabell.**
Vad den kör, vad den kostar de senaste 24 timmarna och över sin livstid, när
den senast sågs, vem som äger den, och om en prenumeration täcker
notan. 14 agenter här, 3 sessioner som arbetar, 13 tysta.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Den visar vart en turs tid och pengar tog vägen, verktyg för verktyg.**
En tur från en riktig session: 11 verktyg på 11,2 minuter för 1,16 $. Varje Bash-
anrop och modellanrop får sin egen stapel på tidslinjen, så att kommandot som kördes
i 4,1 minuter och det som kördes på 226 ms skiljs åt med en blick.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Den betygsätter arbetet, inte bara utgifterna.**
Ett A denna vecka: 54 uppgifter kom tillbaka rena, 2 knöliga kostade 48,57 $, och
körningarna med för lite aktivitet för att bedöma lämnas utanför betyget istället för
att räknas som vinster. Varje knölig körning länkar till sin spårning.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Den visar varför kontextfönstret fortsätter att fyllas.**
715K av ett 1M-tokens fönster på den senaste turen, en topp på 83,3 %, 4 komprimeringar
som alla utlöstes proaktivt snarare än vid ett överflöde, och användningen av
varje tur bakom det.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Upptäckt körs utan att du konfigurerar något.**
De inbyggda detektorerna är på från installationen: agenten blev tyst, telemetriflödet
stoppade, kostnadstopp, tokenutbrott, stigande fel, felutbrott, budget-
tröskelvärde, hotsignatur matchad, säkerhetsverktygsfynd, säkerhetsställning
ändrad. Dina egna regler är valfria ovanpå.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Att hålla ett riskfyllt anrop är valbart, och levereras avstängt.**
Rekursiva raderingar, force pushes, sudo, hemligheter, paketinstallationer och utgående
anrop får var och en en regel du kan slå på. Tills du gör det, tittar ClawMetry på
och ändrar ingenting. När en är på, väntar matchande anrop här (eller på din telefon)
på ett godkännande eller avslag.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Mer, per runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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

MIT · Byggd av [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
