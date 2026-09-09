<!-- i18n-src:61beb8393e2f -->
> Polski translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Agent może wykonać sto wywołań narzędzi, nie robiąc żadnego postępu.** ClawMetry
odczytuje pliki sesji, które Twoje agenty kodujące już zapisują, i zestawia oś czasu,
wywołania narzędzi oraz wszelkie dane o tokenach i kosztach udostępniane przez runtime
w jednym widoku — dzięki czemu odróżnisz długi przebieg, który działa, od takiego, który utknął.

Działa z **30 runtime'ami agentów AI** — Claude Code, OpenAI Codex, Hermes, OpenClaw i 26 innych. Jeden pulpit dla całej Twojej floty agentów. ([pełna lista](SUPPORTED_RUNTIMES.txt), generowana z katalogu.)

> 🌐 **Przeczytaj to w:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [więcej →](docs/i18n/)

Jedna komenda. Zero konfiguracji. Wszystko wykrywane automatycznie.

```bash
pip install clawmetry && clawmetry
```

Otwiera się pod adresem **http://localhost:8900**. Zero konfiguracji: znajduje runtime'y
agentów, które już masz, odczytuje je w trybie tylko do odczytu i niczego nie zmienia w sposobie ich działania.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Zanim zainstalujesz

| | |
|---|---|
| **Co to robi** | Odczytuje pliki sesji i logi, które Twoje agenty już zapisują. Żadnego SDK, żadnej zmiany w kodzie, żadnej instrumentacji w Twojej aplikacji. |
| **Co zobaczysz** | Oś czasu sesji, odtwarzanie krok po kroku dla każdego narzędzia, podział tokenów i kosztów oraz sygnały trajektorii (zapętlenia, powtarzające się błędy) — dla każdego runtime'u. |
| **Co jest darmowe** | `pip install clawmetry` odczytuje **OpenClaw, NVIDIA NemoClaw i Goose** bez konta, klucza czy jakiegokolwiek połączenia sieciowego. Pozostałe 27 — Claude Code, Codex, Cursor i reszta — są odczytywane przez zamknięty dodatek `clawmetry-pro`, dostępny w ramach 7-dniowego okresu próbnego lub planu — dokładny podział znajdziesz w [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Jak zacząć** | `pip install clawmetry && clawmetry`, następnie otwórz localhost:8900. Nie masz jeszcze żadnych agentów na tej maszynie? `clawmetry --sample` otwiera się z trzema oznaczonymi sesjami syntetycznymi. |
| **Co opuszcza Twoją maszynę** | Żadne dane sesji, chyba że uruchomisz `clawmetry connect`. Domyślnie działają dwie rzeczy, obie opt-out i żadna nie zawiera treści sesji: anonimowy ping instalacyjny oraz sprawdzenie wersji w PyPI. Każdy cel jest spisany w [docs/EGRESS.md](docs/EGRESS.md), odtworzony na podstawie przechwytu ruchu sieciowego, a nie na podstawie komentarzy w kodzie. |

Warto znać dwa ograniczenia, zanim ocenisz wyniki: runtime'y udostępniają bardzo
różne dane (niektóre w ogóle nie publikują kosztów — [macierz](docs/compatibility.md)
pokazuje, które, dla każdego runtime'u), a obserwowanie akcji to nie to samo, co możliwość
jej zablokowania ([które kontrolki są realne, dla każdego runtime'u](docs/APPROVALS.md)).


## Działa z 30 runtime'ami agentów

**Darmowe w aplikacji open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**W planie płatnym:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Każdy runtime dostaje ten sam pulpit. Uruchom kilka naraz, a przełącznik w nagłówku
przeskaluje każdą zakładkę do wybranego z nich.

Zbudowałeś własnego agenta na SDK zamiast tego? Interceptor śledzi też jego wywołania LLM.
Zobacz [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Co otrzymujesz

- **Sesje i transkrypty**: co zrobił każdy agent, turę po turze, z odtwarzaniem
- **Koszty i tokeny**: dla każdego runtime'u, modelu, sesji i dnia, z flagami anomalii
- **Flow**: diagram na żywo pokazujący ruch wiadomości przez kanały, modele i narzędzia
- **Brain**: strumień zdarzeń rozumowania i wywołań narzędzi na żywo
- **Context blowout**: wykorzystanie okna kontekstu dopasowane do dostawcy, kompaktowanie kontra wymuszony przepełnienie, plus mapa tego, czego *nie widzimy* dla każdego runtime'u ([jak](docs/CONTEXT_BLOWOUT.md))
- **Pamięć i umiejętności**: pliki i umiejętności faktycznie załadowane przez każdy runtime
- **Zdrowie i logi**: dysk, pamięć, wskaźniki błędów, limity zapytań, strumień logów na żywo
- **Alerty**: limity budżetu, skoki błędów, agent offline, kierowane do Slack, Discord, PagerDuty, Telegram, Email
- **Zatwierdzenia**: wstrzymywanie ryzykownych wywołań narzędzi *przed* ich uruchomieniem i zatwierdzanie z telefonu ([jak](docs/APPROVALS.md))

## Context blowout i to, co kosztuje obserwowanie

Dwa pytania, na które warto odpowiedzieć, zanim zaufasz jakiemukolwiek narzędziu do porównywania agentów.

**Jak radzi sobie z przepełnieniem okna kontekstu w różnych runtime'ach?**

Procent wykorzystania jest tak wiarygodny, jak wartość, przez którą jest dzielony. ClawMetry
dobiera rozmiar okna dla każdego dostawcy na podstawie [tabeli, którą możesz przeczytać i
zaproponować do niej PR](clawmetry/context_windows.py), obejmującej Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama i GLM. Nie mierzy wszystkich 30 runtime'ów
jedną miarką jednego dostawcy. To ma znaczenie: tura 300K GPT-5 oceniona
względem 200K Anthropic pokazuje ">100%, przepełnione", podczas gdy w rzeczywistości to 75% z
400K GPT-5. Ta sama miarka ukrywa faktycznie przepełnioną turę 130K DeepSeek
jako komfortowe 65%.

Każde okno ma podane swoje pochodzenie: `model_table`, `explicit_marker`,
`observed_floor` lub uczciwy `default`, gdy nie znamy modelu. Wskaźnik zbudowany na
domysłach nigdy nie jest wyświetlany z taką samą pewnością, jak ten zbudowany na
odczycie z tabeli.

ClawMetry może zobaczyć zdarzenia kompaktowania tylko w niektórych runtime'ach. Dlatego
`GET /api/context-coverage` raportuje, dla każdego runtime'u, czy **zero oznacza
"przebiegło czysto", czy "jesteśmy ślepi"**. `0`, które faktycznie oznacza ślepotę, jest tak opisane.
[Pełne szczegóły](docs/CONTEXT_BLOWOUT.md)

**Ile kosztuje instrumentacja?**

| Ścieżka | Dodane do Twojego agenta | Domyślnie? |
|---|---|---|
| Śledzenie plików sesji (wszystkie 30 runtime'ów) | **0**. Osobny proces, żadnego kodu ClawMetry w Twoim agencie | włączone |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** na wywołanie LLM, czyli 0,009% wywołania trwającego 5s | wyłączone |
| Bramka hooka pre-tool (rozgrzana pamięć podręczna) | **+44 ms** na bramkowane wywołanie narzędzia, ponad 36 ms podłogi interpretera | wyłączone |
| Proxy egzekwujące | **+9,7 ms** na wywołanie LLM | wyłączone |

Koszt hosta demona: **2762 zdarzenia/s** przyjmowane, **710 bajtów/zdarzenie** na dysku
(67,7 MB na 100 tys. zdarzeń) oraz **~12% jednego rdzenia** utrzymywane przy zajętej
instalacji. Ta ostatnia liczba przekracza nasz własny deklarowany budżet 5-10%, więc
publikujemy ją jako błąd do naprawienia, a nie pomijamy na stronie.

Zmierzone na Apple M2 Pro za pomocą `benchmarks/overhead.py`. Framework uruchamia
każdy wariant w osobnym procesie, zmienia kolejność ich uruchamiania i **odmawia
wydrukowania liczby, gdy rundy nie zgadzają się co do jej znaku**. Uruchom go na własnej
maszynie w minutę:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Każda ścieżka jest zmierzona, w tym bramki hooków i proxy egzekwujące,
a framework działa na Linuksie, macOS i Windowsie w CI. Dwa wyniki warte poznania: proxy
kosztuje na Windowsie około siedmiokrotnie więcej niż na Linuksie, a demon obecnie
utrzymuje około 12% jednego rdzenia, ponad nasz własny budżet 5-10%. Surowy JSON,
metoda i to, co wciąż nie jest zmierzone, znajdują się w
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Cennik

| Plan | Co obejmuje | Cena |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, pełny pulpit, tylko lokalnie | 0 USD |
| **Starter** | Każdy inny runtime powyżej, widok floty, synchronizacja z chmurą | 9 USD za węzeł / miesiąc |
| **Pro** | Starter + kontrola i ewaluacja: zatwierdzenia, polityki ryzyka narzędzi, ewaluacje, wykrywanie anomalii, optymalizator kosztów, eksport OTel, dziennik audytu odporny na manipulację | 19 USD za węzeł / miesiąc |

Plany roczne, Enterprise i aktualne ceny znajdują się na
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Klucze licencyjne self-hosted
działają bez chmury (`clawmetry license`). Dokładny podział darmowe/płatne znajdziesz
w [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Twoje dane pozostają na Twojej maszynie

ClawMetry odczytuje lokalne pliki sesji i logi. **Żadne dane sesji nie opuszczają Twojej maszyny,
chyba że uruchomisz `clawmetry connect`** — żadnych promptów, odpowiedzi, argumentów narzędzi, treści
plików ani linii logów. Gdy już się połączysz, migawka jest szyfrowana end-to-end
kluczem, który nigdy nie opuszcza Twojej maszyny, i odszyfrowywana w Twojej przeglądarce. Jeśli
węzeł nie ma klucza, przesyłanie jest pomijane, zamiast być wysyłane jawnym tekstem, i żadna
odpowiedź serwera nie może tego wyłączyć.

Domyślnie, zanim się połączysz, działają dwie rzeczy, obie opt-out i żadna nie
niosąca danych sesji: anonimowy ping instalacyjny i sprawdzenie wersji względem
PyPI. Domyślna instalacja sprawdza też raz Twój publiczny adres IP na potrzeby linii
banera startowego. Każdy cel, to co przenosi i jak to wyłączyć, jest wymienione w
[docs/EGRESS.md](docs/EGRESS.md); instalacje self-hosted, przekierowane i odizolowane od sieci
nie wykonują żadnych opcjonalnych połączeń wychodzących.

Odszyfrowywanie odbywa się w Twojej przeglądarce, w kodzie, który Ci dostarczamy. Kiedyś było to
tylko obietnicą; teraz jest to coś, co możesz sprawdzić. Każda linia dotykająca Twojego klucza
znajduje się w jednym czytelnym pliku, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
który jest dołączony do wheela i serwowany dosłownie, przypięty skrótem Subresource
Integrity. Aby potwierdzić, że przeglądarka uruchamia to, co opublikowaliśmy:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Czego to nie dowodzi: to my serwujemy stronę, która ładuje ten plik, więc moglibyśmy
serwować inną stronę. Skróty integralności chronią przed skompromitowanym CDN,
nie przed dostawcą. Zyskujesz to, że każda podmiana musi być
celowa, widoczna w źródle strony i różna od artefaktu w PyPI,
który każdy może pobrać. Self-hosting lub pozostanie wyłącznie lokalnie całkowicie
usuwa tę zależność.

## Instalacja

```bash
pip install clawmetry     # następnie: clawmetry
```

Albo jednolinijkowiec: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Wymaga Pythona 3.8+ na macOS, Linuksie lub Windowsie oraz przynajmniej jednego runtime'u agenta na
tej samej maszynie. Instrukcje Docker: [docs/DOCKER.md](docs/DOCKER.md).

Albo pozwól agentowi skonfigurować to za Ciebie. Umiejętność [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
uczy Claude Code, Codex, Cursor, Gemini CLI, Copilot lub OpenCode, jak
zainstalować ClawMetry, zgłaszać, co robią i wydają agenty na tej maszynie,
zatrzymywać jedną sesję na żądanie i wstrzymywać ryzykowne wywołania narzędzi do zatwierdzenia:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokumentacja

| | |
|---|---|
| [Kompatybilność runtime'ów](docs/compatibility.md) | Co odczytuje każdy adapter i jak dodać runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Okna dla każdego dostawcy, kompaktowanie kontra przepełnienie, pokrycie dla każdego runtime'u |
| [Overhead](docs/OVERHEAD.md) | Ile kosztuje instrumentacja, zmierzone, z frameworkiem do odtworzenia |
| [Uprawnienia](docs/ENTITLEMENTS.md) | Darmowe kontra płatne, macierz poziomów, CLI licencji |
| [Zatwierdzenia i polityki](docs/APPROVALS.md) | Bramkowanie przed wykonaniem, ocena ryzyka, zatwierdzenia z telefonu |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Eksportuj ślady wszędzie, przyjmuj OTLP z dowolnego źródła |
| [Podłącz własnego agenta](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain od początku do końca, z uruchamialnymi przykładami |
| [Śledzenie SDK](docs/SDK_TRACKING.md) | Przypisywanie kosztów dla agentów zbudowanych samodzielnie |
| [Kanały czatu](docs/CHANNELS.md) | Adaptery czatu pokazywane w Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Konfiguracje NVIDIA NemoClaw w piaskownicy |
| [Docker](docs/DOCKER.md) | Obraz, compose, montowanie woluminów |
| [Architektura](ARCHITECTURE.md) · [Rozwój](docs/DEVELOPMENT.md) | Jak to działa wewnątrz; uruchamianie ze źródeł |
| [Telemetria](docs/TELEMETRY.md) | Anonimowe pingi instalacji i otwarcia desktopu oraz jak je wyłączyć |

## Zrzuty ekranu

Każda liczba poniżej pochodzi z jednej prawdziwej maszyny, tylko do odczytu, bez żadnych danych zaszczepionych na potrzeby demonstracji.

**Informuje, kiedy coś jest nie tak, nie tylko co się wydarzyło.**
Dwa banery anomalii na górze: wydatki na poziomie 7x średniej dziennej i
skok kosztów 4,2x. Poniżej nich 324 z 667 ostatnich sesji niosących sygnał
marnotrawstwa, rozpisane według przyczyny.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Pokazuje, gdzie poszły pieniądze, w każdym oknie czasowym.**
252,47 USD dzisiaj, 513,15 USD w tym tygodniu, 1312,92 USD w tym miesiącu, każde z tokenami
stojącymi za tym i tym, ile z tego pokrywa już Twoja subskrypcja. Poniżej tego,
około 1128 USD/mies. rozpisane jako możliwe do odzyskania i 17 256 USD/mies. już zaoszczędzone
dzięki ponownemu użyciu pamięci podręcznej.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Rysuje, jak wiadomość staje się odpowiedzią.**
Diagram flow na żywo: Ty, kanał, którym wiadomość przyszła, gateway, model
odpowiadający w danej chwili i każde narzędzie, po które sięgnął. Węzły rozświetlają się
w miarę przepływu pracy przez nie.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Każdy agent na maszynie, w jednej tabeli.**
Co uruchamia, ile kosztuje w ostatnich 24 godzinach i przez cały okres istnienia, kiedy
był ostatnio widziany, kto jest jego właścicielem i czy subskrypcja pokrywa
rachunek. 14 agentów tutaj, 3 sesje pracujące, 13 cichych.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Pokazuje, gdzie poszedł czas i pieniądze tury, narzędzie po narzędziu.**
Jedna tura prawdziwej sesji: 11 narzędzi w 11,2 minuty za 1,16 USD. Każde wywołanie Bash
i wywołanie modelu ma swój własny pasek na osi czasu, dzięki czemu polecenie, które trwało
4,1 minuty, i to, które trwało 226 ms, są rozróżnialne na pierwszy rzut oka.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ocenia pracę, nie tylko wydatki.**
Ocena A w tym tygodniu: 54 zadania wróciły czyste, 2 trudne kosztowały 48,57 USD, a
przebiegi z za małą ilością aktywności do oceny są pomijane w ocenie, zamiast być liczone jako sukcesy.
Każdy trudny przebieg linkuje do swojego śladu.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Pokazuje, dlaczego okno kontekstu ciągle się zapełnia.**
715K z 1M-tokenowego okna w ostatniej turze, szczyt 83,3%, 4 kompaktowania,
które wszystkie zadziałały proaktywnie, a nie przy przepełnieniu, oraz wykorzystanie
każdej tury stojącej za tym.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Wykrywanie działa bez żadnej konfiguracji z Twojej strony.**
Wbudowane detektory są aktywne od instalacji: agent ucichł, kanał telemetrii
zatrzymał się, skok kosztów, przypływ tokenów, rosnące błędy, skok błędów, próg
budżetu, dopasowana sygnatura zagrożenia, wynik narzędzia bezpieczeństwa, zmiana postawy
bezpieczeństwa. Twoje własne reguły są opcjonalne, dodatkowo.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Wstrzymywanie ryzykownego wywołania jest opcjonalne i domyślnie wyłączone.**
Rekurencyjne usuwanie, wymuszone push'e, sudo, sekrety, instalacje pakietów i wywołania
wychodzące — każde z nich ma regułę, którą możesz włączyć. Dopóki tego nie zrobisz, ClawMetry
obserwuje i niczego nie zmienia. Gdy jedna jest włączona, pasujące wywołania czekają tutaj (lub na Twoim telefonie)
na zatwierdzenie lub odrzucenie.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Więcej, dla poszczególnych runtime'ów: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Uznanie

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Historia gwiazdek

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licencja

MIT · Stworzone przez [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
