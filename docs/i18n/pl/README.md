<!-- i18n-src:12b97259721e -->
> Polski translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Agent może wykonać sto wywołań narzędzi, nie robiąc żadnych postępów.** ClawMetry
odczytuje pliki sesji, które twoje agenty kodujące już zapisują, i umieszcza oś czasu,
wywołania narzędzi oraz wszelkie dane o tokenach i kosztach, jakie udostępnia dany runtime, w jednym
widoku — dzięki czemu możesz odróżnić długo działający proces, który faktycznie działa, od takiego, który utknął.

Działa z **31 runtime'ami agentów AI** — Claude Code, OpenAI Codex, Hermes, OpenClaw i 27 innymi. Jeden dashboard dla całej floty twoich agentów. ([pełna lista](SUPPORTED_RUNTIMES.txt), generowana z katalogu.)

> 🌐 **Przeczytaj to w:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [więcej →](docs/i18n/)

Jedna komenda. Zero konfiguracji. Automatyczne wykrywanie wszystkiego.

```bash
pip install clawmetry && clawmetry
```

Otwiera się pod adresem **http://localhost:8900**. Zero konfiguracji: znajduje runtime'y agentów,
które już masz, odczytuje je w trybie tylko do odczytu i niczego nie zmienia w sposobie ich działania.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Zanim zainstalujesz

| | |
|---|---|
| **Co robi** | Odczytuje pliki sesji i logi, które twoje agenty już zapisują. Bez SDK, bez zmian w kodzie, bez instrumentacji w twojej aplikacji. |
| **Co widzisz** | Oś czasu sesji, powtórkę narzędzie po narzędziu, podział tokenów i kosztów oraz sygnały trajektorii (zapętlenia, powtarzające się błędy) — dla każdego runtime'u. |
| **Co jest darmowe** | `pip install clawmetry` odczytuje **OpenClaw, NVIDIA NemoClaw i Goose** bez konta, bez klucza i bez połączenia sieciowego. Pozostałe 27 — Claude Code, Codex, Cursor i reszta — jest odczytywanych przez zamknięty komponent towarzyszący `clawmetry-pro`, który jest dostępny w ramach 7-dniowego okresu próbnego lub planu płatnego — dokładny podział znajdziesz w [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Jak zacząć** | `pip install clawmetry && clawmetry`, a następnie otwórz localhost:8900. Nie masz jeszcze żadnych agentów na tej maszynie? `clawmetry --sample` otwiera się z trzema oznaczonymi sesjami syntetycznymi. |
| **Co opuszcza twoją maszynę** | Żadne dane sesji, chyba że uruchomisz `clawmetry connect`. Domyślnie działają dwie rzeczy, obie możliwe do wyłączenia i żadna z nich nie przenosi treści sesji: anonimowy ping instalacyjny oraz sprawdzenie wersji w PyPI. Każdy cel jest spisany w [docs/EGRESS.md](docs/EGRESS.md), odtworzonym na podstawie przechwytu ruchu sieciowego, a nie na podstawie komentarzy w kodzie. |

Warto znać dwa ograniczenia, zanim ocenisz wyniki: runtime'y udostępniają bardzo
różne dane (niektóre w ogóle nie publikują kosztów — [macierz](docs/compatibility.md)
pokazuje, które, dla każdego runtime'u), a obserwowanie akcji to nie to samo, co możliwość
jej zablokowania ([które kontrole są rzeczywiste, dla każdego runtime'u](docs/APPROVALS.md)).


## Działa z 31 runtime'ami agentów

**Darmowe w aplikacji open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**W planie płatnym:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Każdy runtime otrzymuje ten sam dashboard. Uruchom kilka jednocześnie, a przełącznik
w nagłówku przeskaluje każdą zakładkę do jednego z nich.

Zbudowałeś własnego agenta na SDK zamiast tego? Interceptor śledzi też jego wywołania LLM.
Zobacz [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Co otrzymujesz

- **Sesje i transkrypcje**: co zrobił każdy agent, turę po turze, z możliwością odtworzenia
- **Koszty i tokeny**: dla każdego runtime'u, modelu, sesji i dnia, z flagami anomalii
- **Flow**: żywy diagram wiadomości przepływających przez kanały, modele i narzędzia
- **Brain**: strumień zdarzeń rozumowania i wywołań narzędzi na żywo
- **Przepełnienie kontekstu**: wykorzystanie okna dopasowane do dostawcy, kompaktowanie kontra wymuszony overflow, plus mapa dla każdego runtime'u pokazująca, czego *nie widzimy* ([jak](docs/CONTEXT_BLOWOUT.md))
- **Pamięć i umiejętności**: pliki i umiejętności, które faktycznie załadował każdy runtime
- **Zdrowie i logi**: dysk, pamięć, wskaźniki błędów, limity szybkości, strumień logów na żywo
- **Alerty**: limity budżetu, skoki błędów, agent offline, kierowane do Slack, Discord, PagerDuty, Telegram, Email
- **Zatwierdzenia**: wstrzymywanie ryzykownych wywołań narzędzi *przed* ich wykonaniem i zatwierdzanie z telefonu ([jak](docs/APPROVALS.md))

## Przepełnienie kontekstu i koszt obserwacji

Dwa pytania, na które warto odpowiedzieć, zanim zaufasz jakiemukolwiek narzędziu do porównywania agentów.

**Jak radzi sobie z przepełnieniem okna kontekstu w różnych runtime'ach?**

Procent wykorzystania jest tak wiarygodny, jak wartość, przez którą jest dzielony. ClawMetry
dobiera rozmiar okna dla każdego dostawcy na podstawie [tabeli, którą możesz przeczytać i
zaproponować do niej PR](clawmetry/context_windows.py), obejmującej Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama i GLM. Nie mierzy wszystkich 31 runtime'ów
jedną miarą jednego dostawcy. To ma znaczenie: tura 300K GPT-5 oceniana
względem 200K Anthropic czyta się jako ">100%, przepełnione", podczas gdy w rzeczywistości to 75% z
400K GPT-5. Ta sama miara ukrywa naprawdę przepełnioną turę 130K DeepSeek
jako komfortowe 65%.

Każde okno jest dostarczane wraz ze swoim pochodzeniem: `model_table`, `explicit_marker`,
`observed_floor`, albo uczciwe `default`, gdy nie znamy modelu. Wskaźnik zbudowany na
domysłach nigdy nie jest wyświetlany z taką samą wiarygodnością jak ten zbudowany na
konkretnym odczycie.

ClawMetry może zobaczyć zdarzenia kompaktowania tylko w niektórych runtime'ach. Dlatego
`GET /api/context-coverage` raportuje, dla każdego runtime'u, czy **zero oznacza
"przebiegło czysto" czy "jesteśmy ślepi"**. `0`, które faktycznie oznacza ślepotę, mówi o tym wprost.
[Pełny opis](docs/CONTEXT_BLOWOUT.md)

**Ile kosztuje ta instrumentacja?**

| Ścieżka | Dodane do twojego agenta | Domyślnie? |
|---|---|---|
| Śledzenie plików sesji (wszystkie 31 runtime'ów) | **0**. Osobny proces, brak kodu ClawMetry w twoim agencie | włączone |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** na wywołanie LLM, czyli 0,009% wywołania trwającego 5s | wyłączone |
| Bramka hooka pre-tool (ciepły cache) | **+44 ms** na bramkowane wywołanie narzędzia, przy podłodze interpretera wynoszącej 36 ms | wyłączone |
| Proxy egzekwujące | **+9,7 ms** na wywołanie LLM | wyłączone |

Koszt hosta demona: **2762 zdarzenia/s** przy pozyskiwaniu danych, **710 bajtów/zdarzenie** na dysku
(67,7 MB na 100k zdarzeń) oraz **~12% jednego rdzenia** przy stałym obciążeniu na zajętej
instalacji. Ta ostatnia liczba przekracza nasz własny deklarowany budżet 5–10%, więc jest
publikowana jako błąd do naprawienia, a nie pominięta na stronie.

Zmierzone na Apple M2 Pro za pomocą `benchmarks/overhead.py`. Harness uruchamia
każdy scenariusz w osobnym procesie, zmienia ich kolejność i **odmawia wypisania
liczby, gdy rundy nie zgadzają się co do jej znaku**. Uruchom go na własnej
maszynie w minutę:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Każda ścieżka jest mierzona, w tym bramki hooków i proxy egzekwujące,
a harness działa na Linuksie, macOS i Windows w CI. Dwa wyniki, które warto
znać: proxy kosztuje na Windows około siedem razy więcej niż na Linuksie, a
demon obecnie utrzymuje na stałe około 12% jednego rdzenia, przekraczając nasz własny budżet
5–10%. Surowe dane JSON, metoda oraz to, co wciąż nie jest zmierzone, znajdują się w
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Cennik

| Plan | Co obejmuje | Cena |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, pełny dashboard, tylko lokalnie | $0 |
| **Starter** | Każdy inny runtime powyżej, widok floty, synchronizacja w chmurze | 9 $ za węzeł / miesiąc |
| **Pro** | Starter + kontrola i ewaluacja: zatwierdzenia, polityki ryzyka narzędzi, ewaluacje, wykrywanie anomalii, optymalizator kosztów, eksport OTel, dziennik audytowy odporny na manipulacje | 19 $ za węzeł / miesiąc |

Plany roczne, Enterprise i aktualne ceny znajdują się na stronie
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Klucze licencyjne do self-hostingu
działają bez chmury (`clawmetry license`). Dokładny podział na darmowe/płatne znajduje się
w [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Twoje dane pozostają na twojej maszynie

ClawMetry odczytuje lokalne pliki sesji i logi. **Żadne dane sesji nie opuszczają twojej maszyny,
chyba że uruchomisz `clawmetry connect`** — żadnych promptów, odpowiedzi, argumentów narzędzi, zawartości
plików ani linii logów. Gdy już się połączysz, migawka jest szyfrowana end-to-end
kluczem, który nigdy nie opuszcza twojej maszyny, i odszyfrowywana w twojej przeglądarce. Jeśli
węzeł nie ma klucza, przesyłanie jest pomijane zamiast wysyłane jawnym tekstem, i żadna
odpowiedź serwera nie może tego wyłączyć.

Dwie rzeczy działają domyślnie przed połączeniem, obie możliwe do wyłączenia i żadna nie
przenosi danych sesji: anonimowy ping instalacyjny i sprawdzenie wersji w
PyPI. Domyślna instalacja sprawdza też raz twój publiczny adres IP na potrzeby linii banera startowego.
Każdy cel, co przenosi i jak to wyłączyć, jest wymieniony w
[docs/EGRESS.md](docs/EGRESS.md); instalacje self-hosted, przekierowane i odcięte od sieci
w ogóle nie wykonują żadnych opcjonalnych połączeń wychodzących.

Odszyfrowywanie odbywa się w twojej przeglądarce, w kodzie, który ci dostarczamy. Kiedyś było to
obietnicą; teraz jest to coś, co możesz zweryfikować. Każda linia dotykająca twojego klucza
znajduje się w jednym czytelnym pliku, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
który jest dołączony do wheela i serwowany dosłownie, przypięty hashem Subresource
Integrity. Aby potwierdzić, że przeglądarka uruchamia to, co opublikowaliśmy:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Czego to nie dowodzi: to my serwujemy stronę, która ładuje ten plik, więc moglibyśmy
serwować inną stronę. Hashe integralności chronią cię przed skompromitowanym CDN,
a nie przed dostawcą. To, co zyskujesz, to fakt, że każda podmiana musi być
celowa, widoczna w źródle strony i różna od artefaktu na PyPI, który każdy
może pobrać. Self-hosting lub pozostanie wyłącznie lokalnie całkowicie eliminuje tę
zależność.

## Instalacja

```bash
pip install clawmetry     # następnie: clawmetry
```

Albo jednolinijkowiec: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Wymaga Pythona 3.8+ na macOS, Linuksie lub Windows, oraz co najmniej jednego runtime'u agenta na
tej samej maszynie. Instrukcje dla Docker: [docs/DOCKER.md](docs/DOCKER.md).

Albo pozwól agentowi skonfigurować to za ciebie. Umiejętność [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
uczy Claude Code, Codex, Cursor, Gemini CLI, Copilot lub OpenCode, jak
zainstalować ClawMetry, raportować, co robią i ile wydają agenty na maszynie,
zatrzymać jedną sesję na żądanie oraz wstrzymywać ryzykowne wywołania narzędzi do zatwierdzenia:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokumentacja

| | |
|---|---|
| [Kompatybilność runtime'ów](docs/compatibility.md) | Co odczytuje każdy adapter i jak dodać runtime |
| [Przepełnienie kontekstu](docs/CONTEXT_BLOWOUT.md) | Okna dla poszczególnych dostawców, kompaktowanie kontra overflow, pokrycie dla każdego runtime'u |
| [Narzut wydajnościowy](docs/OVERHEAD.md) | Ile kosztuje instrumentacja, zmierzone, wraz z harnessem do reprodukcji |
| [Uprawnienia](docs/ENTITLEMENTS.md) | Darmowe kontra płatne, macierz poziomów, CLI licencji |
| [Zatwierdzenia i polityki](docs/APPROVALS.md) | Bramkowanie przed wykonaniem, ocena ryzyka, zatwierdzenia z telefonu |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Eksportuj ślady wszędzie, przyjmuj OTLP z dowolnego źródła |
| [Podłącz własnego agenta](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain od początku do końca, z działającymi przykładami |
| [Śledzenie SDK](docs/SDK_TRACKING.md) | Przypisywanie kosztów dla agentów zbudowanych samodzielnie |
| [Kanały czatu](docs/CHANNELS.md) | Adaptery czatu pokazywane w Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Piaskownicowe konfiguracje NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Obraz, compose, montowanie woluminów |
| [Architektura](ARCHITECTURE.md) · [Rozwój](docs/DEVELOPMENT.md) | Jak to działa wewnątrz; uruchamianie ze źródeł |
| [Telemetria](docs/TELEMETRY.md) | Anonimowe pingi instalacyjne i otwarcia aplikacji desktopowej oraz jak je wyłączyć |

## Zrzuty ekranu

Każda liczba poniżej pochodzi z jednej prawdziwej maszyny, w trybie tylko do odczytu, bez żadnych sztucznie wprowadzonych danych.

**Mówi ci, kiedy coś jest nie tak, a nie tylko co się wydarzyło.**
Dwa banery anomalii na górze: wydatki na poziomie 7-krotności dziennej średniej oraz
skok kosztów 4,2x. Poniżej nich 324 z 667 ostatnich sesji niosących sygnał
marnotrawstwa, rozbite według przyczyny.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Pokazuje, gdzie poszły pieniądze, w każdym oknie czasowym.**
252,47 $ dzisiaj, 513,15 $ w tym tygodniu, 1312,92 $ w tym miesiącu, każde z tokenami
stojącymi za tym i informacją, ile z tego pokrywa już twoja subskrypcja. Poniżej tego,
około 1128 $/mies. oznaczone jako możliwe do odzyskania i 17 256 $/mies. już zaoszczędzone dzięki
ponownemu wykorzystaniu cache.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Rysuje, jak wiadomość staje się odpowiedzią.**
Żywy diagram przepływu: ty, kanał, którym dotarła, gateway, model
odpowiadający właśnie teraz, oraz każde narzędzie, po które sięgnął. Węzły zapalają się, gdy praca
przez nie przechodzi.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Każdy agent na maszynie, w jednej tabeli.**
Co uruchamia, ile kosztuje w ciągu ostatnich 24 godzin i przez cały okres istnienia, kiedy
był ostatnio widziany, kto jest jego właścicielem i czy subskrypcja pokrywa
rachunek. 14 agentów tutaj, 3 sesje pracujące, 13 nieaktywnych.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Pokazuje, gdzie poszedł czas i pieniądze tury, narzędzie po narzędziu.**
Jedna tura prawdziwej sesji: 11 narzędzi w 11,2 minuty za 1,16 $. Każde wywołanie Bash
i wywołanie modelu ma swój własny pasek na osi czasu, dzięki czemu polecenie, które działało
przez 4,1 minuty, i to, które działało 226 ms, są rozróżnialne na pierwszy rzut oka.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ocenia pracę, a nie tylko wydatki.**
Ocena A w tym tygodniu: 54 zadania wróciły bez zastrzeżeń, 2 trudne kosztowały 48,57 $, a
przebiegi z zbyt małą ilością aktywności, by je ocenić, są pomijane w ocenie, zamiast być liczone jako sukcesy.
Każdy trudny przebieg linkuje do swojego śladu.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Pokazuje, dlaczego okno kontekstu wciąż się zapełnia.**
715K z 1M-tokenowego okna w ostatniej turze, szczyt 83,3%, 4 kompaktowania,
które wszystkie uruchomiły się proaktywnie, a nie w wyniku przepełnienia, oraz wykorzystanie
każdej tury stojącej za tym.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Wykrywanie działa bez żadnej konfiguracji z twojej strony.**
Wbudowane detektory są aktywne od instalacji: agent ucichł, kanał telemetrii
przestał działać, skok kosztów, gwałtowny wzrost tokenów, rosnące błędy, skok błędów, próg
budżetu, dopasowana sygnatura zagrożenia, wynik narzędzia bezpieczeństwa, zmiana postawy
bezpieczeństwa. Twoje własne reguły są opcjonalnym dodatkiem.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Wstrzymywanie ryzykownego wywołania jest opcjonalne i domyślnie wyłączone.**
Rekursywne usuwanie, wymuszone push'e, sudo, sekrety, instalacje pakietów i wywołania
wychodzące — każde z nich ma regułę, którą możesz włączyć. Dopóki tego nie zrobisz, ClawMetry obserwuje i
niczego nie zmienia. Gdy jedna zostanie włączona, pasujące wywołania czekają tutaj (lub na twoim telefonie)
na zatwierdzenie lub odrzucenie.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Więcej, dla poszczególnych runtime'ów: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Wyróżnienia

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
