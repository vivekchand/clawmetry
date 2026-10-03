<!-- i18n-src:c99ac0512cae -->
> Polski translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Agent może wykonać sto wywołań narzędzi bez żadnego postępu.** ClawMetry
odczytuje pliki sesji, które Twoje agenty kodujące już zapisują, i zestawia oś czasu,
wywołania narzędzi oraz wszelkie dane o tokenach i kosztach, jakie udostępnia dany runtime, w jednym
widoku, dzięki czemu możesz odróżnić długi przebieg, który działa, od takiego, który utknął.

Działa z **33 runtime'ami agentów AI** — Claude Code, OpenAI Codex, Hermes, OpenClaw i 29 innych. Jeden dashboard dla całej Twojej floty agentów. ([pełna lista](SUPPORTED_RUNTIMES.txt), generowana z katalogu.)

> 🌐 **Przeczytaj w innych językach:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [więcej →](docs/i18n/)

Jedna komenda. Zero konfiguracji. Automatyczne wykrywanie wszystkiego.

```bash
pip install clawmetry && clawmetry
```

Otwiera się pod adresem **http://localhost:8900**. Zero konfiguracji: narzędzie znajduje
runtime'y agentów, które już masz, odczytuje je w trybie tylko do odczytu i niczego nie zmienia w ich działaniu.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Zanim zainstalujesz

| | |
|---|---|
| **Co to robi** | Odczytuje pliki sesji i logi, które Twoje agenty już zapisują. Żadnego SDK, żadnej zmiany kodu, żadnej instrumentacji w Twojej aplikacji. |
| **Co zobaczysz** | Oś czasu sesji, odtwarzanie narzędzie-po-narzędziu, podział tokenów i kosztów oraz sygnały trajektorii (zapętlenia, powtarzające się błędy) — dla każdego runtime'u. |
| **Co jest darmowe** | `pip install clawmetry` czyta **OpenClaw, NVIDIA NemoClaw, Goose i Qwen Code** bez konta, bez klucza i bez żadnego połączenia sieciowego. Pozostałe 28 — Claude Code, Codex, Cursor i reszta — jest odczytywanych przez zamknięty dodatek `clawmetry-pro`, który dostępny jest wraz z 7-dniowym okresem próbnym lub planem płatnym — dokładny podział znajdziesz w [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Jak zacząć** | `pip install clawmetry && clawmetry`, a następnie otwórz localhost:8900. Nie masz jeszcze żadnych agentów na tej maszynie? `clawmetry --sample` otwiera się z trzema oznaczonymi, syntetycznymi sesjami. |
| **Co opuszcza Twoją maszynę** | Żadne dane sesji, chyba że uruchomisz `clawmetry connect`. Domyślnie działają dwie rzeczy, obie opcjonalne (opt-out) i żadna z nich nie niesie treści sesji: anonimowy ping instalacyjny oraz sprawdzenie wersji w PyPI. Każdy cel jest wymieniony w [docs/EGRESS.md](docs/EGRESS.md), odtworzony na podstawie przechwytu ruchu sieciowego, a nie na podstawie komentarzy w kodzie. |

Warto znać dwa ograniczenia, zanim ocenisz wyniki: runtime'y udostępniają bardzo
różne dane (niektóre w ogóle nie publikują kosztów — [macierz](docs/compatibility.md)
pokazuje które, dla każdego runtime'u), a obserwowanie akcji to nie to samo co możliwość
jej zablokowania ([które kontrolki są realne, dla każdego runtime'u](docs/APPROVALS.md)).


## Działa z 33 runtime'ami agentów

**Darmowe w aplikacji open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**W planie płatnym:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Każdy runtime otrzymuje ten sam dashboard. Uruchom kilka naraz, a przełącznik
w nagłówku przeskaluje każdą zakładkę do jednego z nich.

Zbudowałeś własnego agenta na SDK zamiast gotowego runtime'u? Interceptor śledzi
również jego wywołania LLM. Zobacz [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Co otrzymujesz

- **Sesje i transkrypcje**: co zrobił każdy agent, turę po turze, z odtwarzaniem
- **Koszt i tokeny**: dla każdego runtime'u, modelu, sesji i dnia, z flagami anomalii
- **Flow**: diagram na żywo pokazujący przepływ wiadomości przez kanały, modele i narzędzia
- **Brain**: strumień zdarzeń rozumowania i wywołań narzędzi w czasie rzeczywistym
- **Context blowout**: wykorzystanie okna kontekstu liczone dla każdego dostawcy osobno, kompaktowanie kontra wymuszone przepełnienie, plus mapa tego, czego *nie widzimy* dla każdego runtime'u ([jak to działa](docs/CONTEXT_BLOWOUT.md))
- **Pamięć i umiejętności**: pliki i umiejętności faktycznie wczytane przez każdy runtime
- **Zdrowie i logi**: dysk, pamięć, wskaźniki błędów, limity szybkości, strumień logów na żywo
- **Alerty**: limity budżetu, skoki błędów, agent offline, wysyłane do Slack, Discord, PagerDuty, Telegram, Email
- **Zatwierdzenia**: wstrzymywanie ryzykownych wywołań narzędzi *zanim* się wykonają i zatwierdzanie ich z telefonu ([jak to działa](docs/APPROVALS.md))

## Context blowout i koszt obserwacji

Dwa pytania, na które warto odpowiedzieć, zanim zaufasz jakiemukolwiek narzędziu porównującemu agentów.

**Jak radzimy sobie z przepełnieniem okna kontekstu w różnych runtime'ach?**

Procent wykorzystania jest wiarygodny tylko wtedy, gdy wiadomo, przez co się go dzieli. ClawMetry
ustala rozmiar okna dla każdego dostawcy na podstawie [tabeli, którą możesz przeczytać i
zgłosić do niej PR](clawmetry/context_windows.py), obejmującej Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama i GLM. Nie mierzymy wszystkich 33
runtime'ów jedną, cudzą miarką. To ma znaczenie: tura 300K GPT-5 oceniana
według limitu 200K Anthropic odczytywana jest jako ">100%, przepełnione", gdy w rzeczywistości
to 75% z 400K GPT-5. Ta sama miarka ukrywa naprawdę przepełnioną turę 130K DeepSeek
jako komfortowe 65%.

Każde okno przychodzi z informacją o pochodzeniu: `model_table`, `explicit_marker`,
`observed_floor` lub uczciwe `default`, gdy nie znamy modelu. Wskaźnik zbudowany
na domysłach nigdy nie jest wyświetlany z tą samą wiarygodnością co ten zbudowany
na odczycie z tabeli.

ClawMetry może widzieć zdarzenia kompaktowania tylko w niektórych runtime'ach. Dlatego
`GET /api/context-coverage` raportuje, dla każdego runtime'u, czy **zero oznacza
"przebiegło czysto" czy "jesteśmy ślepi"**. `0`, które w rzeczywistości oznacza ślepotę, mówi o tym wprost.
[Pełne informacje](docs/CONTEXT_BLOWOUT.md)

**Ile kosztuje instrumentacja?**

| Ścieżka | Dodane do Twojego agenta | Domyślnie? |
|---|---|---|
| Śledzenie plików sesji (wszystkie 33 runtime'y) | **0**. Oddzielny proces, zero kodu ClawMetry w Twoim agencie | włączone |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** na wywołanie LLM, czyli 0,009% czasu wywołania trwającego 5 s | wyłączone |
| Bramka pre-tool hook (ciepły cache) | **+44 ms** na bramkowane wywołanie narzędzia, ponad podłogę 36 ms interpretera | wyłączone |
| Proxy egzekwujące | **+9,7 ms** na wywołanie LLM | wyłączone |

Koszt hosta demona: **2762 zdarzeń/s** przy wczytywaniu, **710 bajtów/zdarzenie** na dysku
(67,7 MB na 100 tys. zdarzeń) oraz **~12% jednego rdzenia** w sposób ciągły przy obciążonej
instalacji. Ta ostatnia liczba przekracza nasz deklarowany budżet 5-10%, więc jest
opublikowana jako błąd do naprawienia, a nie pominięta na stronie.

Zmierzone na Apple M2 Pro za pomocą `benchmarks/overhead.py`. Zestaw testów uruchamia
każdy scenariusz w osobnym procesie, zamienia ich kolejność i **odmawia wypisania
liczby, gdy wyniki rund różnią się co do znaku**. Uruchom go na własnej
maszynie w minutę:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Każda ścieżka jest mierzona, w tym bramki hooków i proxy egzekwujące,
a zestaw testów działa na Linuksie, macOS i Windowsie w CI. Dwa warte poznania wyniki:
proxy kosztuje około siedem razy więcej na Windowsie niż na Linuksie, a
demon aktualnie zużywa stale około 12% jednego rdzenia, czyli więcej niż nasz
własny budżet 5-10%. Surowe dane JSON, metodologia i to, co nadal nie jest zmierzone, znajdują się w
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Cennik

| Plan | Co obejmuje | Cena |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, pełny dashboard, tylko lokalnie | 0 $ |
| **Starter** | Wszystkie pozostałe runtime'y powyżej, widok floty, synchronizacja z chmurą | 9 $ za węzeł / miesiąc |
| **Pro** | Starter + kontrola i ocena: zatwierdzenia, polityki ryzyka narzędzi, ewaluacje, wykrywanie anomalii, optymalizator kosztów, eksport OTel, dziennik audytu odporny na manipulacje | 19 $ za węzeł / miesiąc |

Plany roczne, Enterprise i aktualne ceny znajdują się na stronie
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Klucze licencji dla instalacji
własnej (self-hosted) działają bez chmury (`clawmetry license`). Dokładny podział na
darmowe/płatne znajduje się w [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Twoje dane pozostają na Twojej maszynie

ClawMetry odczytuje lokalne pliki sesji i logi. **Żadne dane sesji nie opuszczają Twojej maszyny,
chyba że uruchomisz `clawmetry connect`** — żadnych promptów, odpowiedzi, argumentów narzędzi, zawartości
plików ani linii logów. Gdy już się połączysz, migawka jest szyfrowana end-to-end
kluczem, który nigdy nie opuszcza Twojej maszyny, a odszyfrowywana jest w Twojej przeglądarce. Jeśli
węzeł nie ma klucza, przesyłanie jest pomijane, zamiast wysyłać dane jawnym tekstem, i żadna
odpowiedź serwera nie może tego wyłączyć.

Domyślnie, zanim się połączysz, działają dwie rzeczy, obie opcjonalne (opt-out) i żadna
nie niesie danych sesji: anonimowy ping instalacyjny oraz sprawdzenie wersji względem
PyPI. Domyślna instalacja sprawdza też raz Twój publiczny adres IP na potrzeby linii powitalnej
przy starcie. Każdy cel, jego zawartość i sposób wyłączenia są wymienione w
[docs/EGRESS.md](docs/EGRESS.md); instalacje self-hosted, przekierowane oraz odizolowane od sieci (air-gapped)
nie wykonują żadnych opcjonalnych połączeń wychodzących.

Odszyfrowywanie odbywa się w Twojej przeglądarce, w kodzie, który Ci dostarczamy. Kiedyś było to
obietnicą; teraz jest to coś, co możesz sprawdzić. Każda linia dotykająca Twojego klucza
znajduje się w jednym czytelnym pliku, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
który jest dołączany do pakietu wheel i serwowany bez zmian, przypięty hashem Subresource
Integrity. Aby potwierdzić, że przeglądarka uruchamia to, co opublikowaliśmy:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Czego to nie dowodzi: to my serwujemy stronę, która wczytuje ten plik, więc moglibyśmy
serwować inną stronę. Hashe Integrity chronią Cię przed skompromitowanym CDN,
nie przed dostawcą. Zyskujesz to, że jakakolwiek podmiana musi być
celowa, widoczna w źródle strony i różna od artefaktu w PyPI,
który każdy może pobrać. Samodzielny hosting lub pozostanie tylko lokalnie całkowicie usuwa
tę zależność.

## Instalacja

```bash
pip install clawmetry     # następnie: clawmetry
```

Lub jedna komenda: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Wymaga Python 3.8+ na macOS, Linuksie lub Windowsie oraz przynajmniej jednego runtime'u agenta na
tej samej maszynie. Instrukcje dla Docker: [docs/DOCKER.md](docs/DOCKER.md).

Albo pozwól agentowi skonfigurować to za Ciebie. Umiejętność [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
uczy Claude Code, Codex, Cursor, Gemini CLI, Copilot lub OpenCode, jak
zainstalować ClawMetry, raportować, co robią i ile wydają agenty na danej maszynie,
zatrzymać wybraną sesję na żądanie oraz wstrzymywać ryzykowne wywołania narzędzi do zatwierdzenia:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokumentacja

| | |
|---|---|
| [Zgodność runtime'ów](docs/compatibility.md) | Co odczytuje każdy adapter i jak dodać nowy runtime |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | Okna dla poszczególnych dostawców, kompaktowanie kontra przepełnienie, pokrycie dla każdego runtime'u |
| [Overhead](docs/OVERHEAD.md) | Ile kosztuje instrumentacja, zmierzone, wraz z zestawem testów do reprodukcji |
| [Entitlements](docs/ENTITLEMENTS.md) | Darmowe kontra płatne, macierz planów, CLI licencji |
| [Zatwierdzenia i polityki](docs/APPROVALS.md) | Bramkowanie przed wykonaniem, ocena ryzyka, zatwierdzenia z telefonu |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Eksportuj ślady dokądkolwiek, przyjmuj OTLP z czegokolwiek |
| [Podłącz własnego agenta](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain od początku do końca, z działającymi przykładami |
| [Śledzenie SDK](docs/SDK_TRACKING.md) | Przypisanie kosztów dla agentów zbudowanych samodzielnie |
| [Kanały czatu](docs/CHANNELS.md) | Adaptery czatu widoczne w Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Konfiguracje NVIDIA NemoClaw w piaskownicy |
| [Docker](docs/DOCKER.md) | Obraz, compose, montowanie wolumenów |
| [Architektura](ARCHITECTURE.md) · [Rozwój](docs/DEVELOPMENT.md) | Jak to działa od środka; uruchamianie ze źródeł |
| [Telemetria](docs/TELEMETRY.md) | Anonimowe pingi instalacji i otwarcia aplikacji desktopowej oraz jak je wyłączyć |

## Zrzuty ekranu

Każda liczba poniżej pochodzi z jednej prawdziwej maszyny, w trybie tylko do odczytu, bez żadnych danych podstawionych na potrzeby demo.

**Mówi Ci, kiedy coś jest nie tak, a nie tylko co się wydarzyło.**
Dwa banery anomalii na górze: wydatki 7 razy wyższe niż dzienna średnia oraz
4,2-krotny skok kosztów. Poniżej nich 324 z 667 ostatnich sesji niosących sygnał
marnotrawstwa, rozbite według przyczyny.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Pokazuje, dokąd poszły pieniądze, w każdym oknie czasowym.**
252,47 $ dzisiaj, 513,15 $ w tym tygodniu, 1312,92 $ w tym miesiącu, każda kwota wraz z tokenami
stojącymi za nią i tym, ile z tego pokrywa już Twoja subskrypcja. Poniżej około
1128 $/miesiąc oznaczone jako możliwe do odzyskania oraz 17 256 $/miesiąc już zaoszczędzone dzięki
ponownemu wykorzystaniu cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Pokazuje, jak wiadomość staje się odpowiedzią.**
Diagram przepływu na żywo: Ty, kanał, przez który wiadomość przyszła, bramka, model
odpowiadający w danej chwili i każde narzędzie, po które sięgnął. Węzły zapalają się w miarę
przepływu pracy przez nie.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Każdy agent na maszynie, w jednej tabeli.**
Co uruchamia, ile kosztuje w ciągu ostatnich 24 godzin i w całym okresie działania, kiedy
był ostatnio widziany, kto jest jego właścicielem i czy subskrypcja pokrywa
rachunek. 14 agentów tutaj, 3 sesje w trakcie pracy, 13 nieaktywnych.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Pokazuje, na co poszedł czas i pieniądze w danej turze, narzędzie po narzędziu.**
Jedna tura prawdziwej sesji: 11 narzędzi w 11,2 minuty za 1,16 $. Każde wywołanie Bash
i każde wywołanie modelu ma swój pasek na osi czasu, dzięki czemu polecenie, które trwało
4,1 minuty, łatwo odróżnić od tego, które trwało 226 ms.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ocenia jakość pracy, a nie tylko wydatki.**
Ocena A w tym tygodniu: 54 zadania wróciły czyste, 2 trudniejsze kosztowały 48,57 $,
a przebiegi z aktywnością zbyt małą, by je ocenić, są pomijane w ocenie zamiast
liczyć się jako sukcesy. Każdy trudniejszy przebieg linkuje do swojego śladu.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Pokazuje, dlaczego okno kontekstu wciąż się zapełnia.**
715K z 1M-tokenowego okna w ostatniej turze, szczyt 83,3%, 4 kompaktowania,
które wszystkie uruchomiły się proaktywnie, a nie z powodu przepełnienia, oraz wykorzystanie
każdej tury, która do tego doprowadziła.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Wykrywanie działa bez żadnej konfiguracji z Twojej strony.**
Wbudowane detektory są włączone od momentu instalacji: agent zamilkł, strumień telemetrii
się zatrzymał, skok kosztów, zryw tokenów, rosnące błędy, skok błędów, próg
budżetu, dopasowana sygnatura zagrożenia, wynik narzędzia bezpieczeństwa, zmieniona postawa
bezpieczeństwa. Twoje własne reguły są opcjonalnym dodatkiem.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Wstrzymywanie ryzykownego wywołania jest opcjonalne i domyślnie wyłączone.**
Rekurencyjne usuwanie, wymuszone push, sudo, sekrety, instalacje pakietów i połączenia
wychodzące — każde ma regułę, którą możesz włączyć. Dopóki tego nie zrobisz, ClawMetry obserwuje i
niczego nie zmienia. Gdy już jedną włączysz, pasujące wywołania czekają tutaj (lub na Twoim telefonie)
na zatwierdzenie lub odrzucenie.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Więcej, dla każdego runtime'u: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
