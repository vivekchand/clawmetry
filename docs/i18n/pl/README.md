<!-- i18n-src:88be2deff5d5 -->
> Polski translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zobacz, jak myśli twój agent.** Obserwowalność w czasie rzeczywistym dla **30 środowisk uruchomieniowych agentów AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex i 26 innych. Jeden dashboard dla całej floty twoich agentów.

> 🌐 **Czytaj to w:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [więcej →](docs/i18n/)

Jedna komenda. Zero konfiguracji. Wszystko wykrywane automatycznie.

```bash
pip install clawmetry && clawmetry
```

Otwiera się pod adresem **http://localhost:8900**. Zero konfiguracji: znajduje środowiska uruchomieniowe agentów, które już masz, odczytuje je w trybie tylko do odczytu i niczego nie zmienia w sposobie ich działania.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Współpracuje z 30 środowiskami uruchomieniowymi agentów

**Darmowe w aplikacji open source:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**W planie płatnym:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Każde środowisko uruchomieniowe otrzymuje ten sam dashboard. Uruchom kilka naraz, a przełącznik w nagłówku przeskaluje każdą zakładkę do jednego z nich.

Zbudowałeś własnego agenta na SDK zamiast tego? Interceptor śledzi również jego wywołania LLM. Zobacz [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Co otrzymujesz

- **Sesje i transkrypcje**: co zrobił każdy agent, turę po turze, z odtwarzaniem
- **Koszty i tokeny**: według środowiska uruchomieniowego, modelu, sesji i dnia, z flagami anomalii
- **Flow**: żywy diagram wiadomości przepływających przez kanały, modele i narzędzia
- **Brain**: strumień zdarzeń rozumowania i wywołań narzędzi na żywo
- **Blowout kontekstu**: wykorzystanie okna dopasowane do dostawcy, kompaktowanie kontra wymuszony przepełnienie, oraz mapa tego, czego *nie widzimy* dla każdego środowiska ([jak](docs/CONTEXT_BLOWOUT.md))
- **Pamięć i umiejętności**: pliki i umiejętności, które faktycznie załadowało każde środowisko uruchomieniowe
- **Zdrowie i logi**: dysk, pamięć, wskaźniki błędów, limity szybkości, strumień logów na żywo
- **Alerty**: limity budżetu, skoki błędów, agent offline, kierowane do Slack, Discord, PagerDuty, Telegram, e-mail
- **Zatwierdzenia**: wstrzymaj ryzykowne wywołania narzędzi *zanim* zostaną wykonane i zatwierdź je z telefonu ([jak](docs/APPROVALS.md))

## Blowout kontekstu i ile kosztuje obserwacja

Dwa pytania warte odpowiedzi, zanim zaufasz jakiemukolwiek narzędziu do porównywania agentów.

**Jak radzi sobie z przepełnieniem okna kontekstu w różnych środowiskach uruchomieniowych?**

Procent wykorzystania jest tak uczciwy, jak uczciwa jest wartość, przez którą dzieli. ClawMetry ustala rozmiar okna dla każdego dostawcy na podstawie [tabeli, którą możesz przeczytać i zaproponować w PR](clawmetry/context_windows.py), obejmującej Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama i GLM. Nie mierzy wszystkich 30 środowisk uruchomieniowych jedną miarką jednego dostawcy. To ma znaczenie: tura na 300K w GPT-5 oceniana wobec 200K Anthropic odczytywana jest jako ">100%, przepełniona", podczas gdy w rzeczywistości to 75% z 400K GPT-5. Ta sama miarka ukrywa naprawdę przepełnioną turę 130K DeepSeek jako komfortowe 65%.

Każde okno dostarczane jest z pochodzeniem: `model_table`, `explicit_marker`, `observed_floor`, lub uczciwy `default`, gdy nie znamy modelu. Wskaźnik zbudowany na domysłach nigdy nie wyświetla się z taką samą wiarygodnością jak zbudowany na wyszukaniu.

ClawMetry potrafi zobaczyć zdarzenia kompaktowania tylko w niektórych środowiskach uruchomieniowych. Dlatego `GET /api/context-coverage` zgłasza, dla każdego środowiska, czy **zero oznacza „przebiegło czysto" czy „jesteśmy ślepi"**. `0`, które w rzeczywistości oznacza ślepotę, mówi o tym wprost.
[Pełne szczegóły](docs/CONTEXT_BLOWOUT.md)

**Ile kosztuje instrumentacja?**

| Ścieżka | Dodane do twojego agenta | Domyślnie? |
|---|---|---|
| Śledzenie pliku sesji (wszystkie 30 środowisk) | **0**. Osobny proces, brak kodu ClawMetry w twoim agencie | wł. |
| Interceptor HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0,44 ms** na wywołanie LLM, czyli 0,009% wywołania trwającego 5s | wył. |
| Bramka hooka pre-tool (ciepły cache) | **+44 ms** na bramkowane wywołanie narzędzia, ponad podłogę interpretera wynoszącą 36 ms | wył. |
| Proxy egzekwowania | **+9,7 ms** na wywołanie LLM | wył. |

Koszt hosta demona: **2762 zdarzeń/s** przy ingestii, **710 bajtów/zdarzenie** na dysku
(67,7 MB na 100 tys. zdarzeń), oraz **~12% jednego rdzenia** w sposób ciągły przy zapracowanej instalacji. Ta ostatnia liczba przekracza nasz własny deklarowany budżet 5-10%, więc jest publikowana jako błąd do naprawienia, a nie pomijana na stronie.

Zmierzone na Apple M2 Pro za pomocą `benchmarks/overhead.py`. Uprząż uruchamia każdy warunek w osobnym procesie, zmienia ich kolejność i **odmawia wypisania liczby, gdy rundy nie zgadzają się co do jej znaku**. Uruchom to na własnej maszynie w minutę:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Każda ścieżka jest mierzona, w tym bramki hooków i proxy egzekwowania, a uprząż działa na Linuksie, macOS i Windows w CI. Dwa wyniki warte poznania: proxy kosztuje około siedem razy więcej na Windows niż na Linuksie, a demon obecnie utrzymuje w sposób ciągły około 12% jednego rdzenia, ponad nasz własny budżet 5-10%. Surowy JSON, metoda i to, co wciąż niezmierzone, znajdują się w [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Cennik

| Plan | Co obejmuje | Cena |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, pełny dashboard, tylko lokalnie | $0 |
| **Starter** | Każde inne środowisko uruchomieniowe powyżej, widok floty, synchronizacja w chmurze | 9 USD za węzeł / miesiąc |
| **Pro** | Starter + kontrola i ewaluacja: zatwierdzenia, polityki ryzyka narzędzi, ewaluacje, wykrywanie anomalii, optymalizator kosztów, eksport OTel, dziennik audytu odporny na manipulacje | 19 USD za węzeł / miesiąc |

Plany roczne, Enterprise i aktualne ceny znajdują się na
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Klucze licencyjne do samodzielnego hostowania działają bez chmury (`clawmetry license`). Dokładny podział na free/paid znajduje się
w [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Twoje dane pozostają na twoim komputerze

ClawMetry odczytuje lokalne pliki sesji i logi. **Żadne dane sesji nie opuszczają twojego komputera, chyba że uruchomisz `clawmetry connect`** — żadne prompty, odpowiedzi, argumenty narzędzi, zawartość plików ani linie logów. Gdy się połączysz, migawka jest szyfrowana end-to-end kluczem, który nigdy nie opuszcza twojej maszyny, i odszyfrowywana w twojej przeglądarce. Jeśli węzeł nie ma klucza, przesyłanie jest pomijane zamiast wysyłane jawnym tekstem, i żadna odpowiedź serwera nie może tego wyłączyć.

Dwie rzeczy działają domyślnie przed połączeniem, obie opt-out i żadna nie niesie danych sesji: anonimowy ping instalacyjny i sprawdzenie wersji względem PyPI. Domyślna instalacja wyszukuje też raz twój publiczny adres IP na potrzeby wiersza banera startowego. Każdy cel, co przenosi i jak to wyłączyć, wymienione jest
w [docs/EGRESS.md](docs/EGRESS.md); instalacje samodzielnie hostowane, przekierowane i odizolowane od sieci nie wykonują żadnych opcjonalnych połączeń wychodzących.

Odszyfrowanie odbywa się w twojej przeglądarce, w kodzie, który ci dostarczamy. Kiedyś było to obietnicą; teraz jest czymś, co możesz zweryfikować. Każda linia dotykająca twojego klucza znajduje się w jednym czytelnym pliku, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
który jest dostarczany wewnątrz koła (wheel) i serwowany dosłownie, przypięty za pomocą hasha Subresource Integrity. Aby potwierdzić, że przeglądarka uruchamia to, co opublikowaliśmy:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Czego to nie dowodzi: serwujemy stronę, która ładuje ten plik, więc moglibyśmy zaserwować inną stronę. Hashe integralności chronią cię przed skompromitowanym CDN, nie przed dostawcą. To, co zyskujesz, to fakt, że każda podmiana musi być celowa, widoczna w źródle strony i różna od artefaktu na PyPI, który każdy może pobrać. Samodzielne hostowanie lub pozostanie wyłącznie lokalnie całkowicie usuwa tę zależność.

## Instalacja

```bash
pip install clawmetry     # następnie: clawmetry
```

Albo jedna komenda: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Wymaga Pythona 3.8+ na macOS, Linuksie lub Windows oraz co najmniej jednego środowiska uruchomieniowego agenta na tej samej maszynie. Instrukcje Docker: [docs/DOCKER.md](docs/DOCKER.md).

Albo pozwól, by agent skonfigurował to za ciebie. Umiejętność [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
uczy Claude Code, Codex, Cursor, Gemini CLI, Copilot lub OpenCode, jak zainstalować ClawMetry, zgłosić, co robią i wydają agenci na tej maszynie,
zatrzymać jedną sesję na żądanie oraz wstrzymywać ryzykowne wywołania narzędzi do zatwierdzenia:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Dokumentacja

| | |
|---|---|
| [Zgodność środowisk uruchomieniowych](docs/compatibility.md) | Co odczytuje każdy adapter i jak dodać środowisko uruchomieniowe |
| [Blowout kontekstu](docs/CONTEXT_BLOWOUT.md) | Okna według dostawcy, kompaktowanie kontra przepełnienie, pokrycie dla każdego środowiska |
| [Narzut](docs/OVERHEAD.md) | Ile kosztuje instrumentacja, zmierzone, wraz z uprzężą do odtworzenia |
| [Uprawnienia](docs/ENTITLEMENTS.md) | Free kontra paid, macierz warstw, CLI licencji |
| [Zatwierdzenia i polityki](docs/APPROVALS.md) | Bramkowanie przed wykonaniem, ocena ryzyka, zatwierdzenia z telefonu |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Eksportuj ślady (traces) gdziekolwiek, przyjmuj OTLP z czegokolwiek |
| [Przynieś własnego agenta](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain od początku do końca, z działającymi przykładami |
| [Śledzenie SDK](docs/SDK_TRACKING.md) | Przypisanie kosztów dla agentów zbudowanych samodzielnie |
| [Kanały czatu](docs/CHANNELS.md) | Adaptery czatu pokazywane w Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Konfiguracje NVIDIA NemoClaw w piaskownicy |
| [Docker](docs/DOCKER.md) | Obraz, compose, montowanie woluminów |
| [Architektura](ARCHITECTURE.md) · [Rozwój](docs/DEVELOPMENT.md) | Jak to działa w środku; uruchamianie ze źródeł |
| [Telemetria](docs/TELEMETRY.md) | Anonimowe pingi instalacji i otwarcia desktopu oraz jak je wyłączyć |

## Zrzuty ekranu

Każda liczba poniżej pochodzi z jednej prawdziwej maszyny, w trybie tylko do odczytu, bez niczego przygotowanego wcześniej.

**Mówi ci, kiedy coś jest nie tak, nie tylko co się wydarzyło.**
Dwa banery anomalii na górze: wydatki na poziomie 7x średniej dziennej i skok kosztów 4,2x. Poniżej nich 324 z 667 ostatnich sesji niosących sygnał marnotrawstwa, wyszczególniony według przyczyny.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Pokazuje ci, gdzie poszły pieniądze, w każdym oknie czasowym.**
252,47 USD dzisiaj, 513,15 USD w tym tygodniu, 1312,92 USD w tym miesiącu, każde z tokenami stojącymi za tym i informacją, ile z tego pokrywa już twoja subskrypcja. Poniżej tego, około 1128 USD/mies. wyszczególnione jako odzyskiwalne i 17 256 USD/mies. już zaoszczędzone dzięki ponownemu wykorzystaniu cache'u.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Rysuje, jak wiadomość staje się odpowiedzią.**
Żywy diagram przepływu: ty, kanał, przez który dotarła, gateway, model odpowiadający właśnie teraz i każde narzędzie, po które sięgnął. Węzły podświetlają się, gdy praca przez nie przechodzi.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Każdy agent na maszynie, w jednej tabeli.**
Co uruchamia, ile kosztuje w ciągu ostatnich 24 godzin i w całym okresie życia, kiedy był ostatnio widziany, kto jest jego właścicielem oraz czy subskrypcja pokrywa rachunek. 14 agentów tutaj, 3 sesje w toku, 13 w spoczynku.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Pokazuje, gdzie poszedł czas i pieniądze tury, narzędzie po narzędziu.**
Jedna tura prawdziwej sesji: 11 narzędzi w 11,2 minuty za 1,16 USD. Każde wywołanie Bash i wywołanie modelu otrzymuje własny pasek na osi czasu, więc polecenie, które trwało 4,1 minuty, i to, które trwało 226 ms, są rozróżnialne na pierwszy rzut oka.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Ocenia pracę, nie tylko wydatki.**
Ocena A w tym tygodniu: 54 zadania wróciły czyste, 2 chropowate kosztowały 48,57 USD, a przebiegi z aktywnością zbyt małą, by je ocenić, są pomijane w ocenie zamiast liczyć się jako sukcesy. Każdy chropowaty przebieg linkuje do swojego śladu (trace).

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Pokazuje, dlaczego okno kontekstu wciąż się zapełnia.**
715K z okna 1M tokenów w ostatniej turze, szczyt 83,3%, 4 kompaktowania, które wszystkie odpaliły się proaktywnie, a nie przy przepełnieniu, oraz wykorzystanie każdej tury stojącej za tym.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Wykrywanie działa bez żadnej konfiguracji z twojej strony.**
Wbudowane detektory są włączone od instalacji: agent ucichł, kanał telemetrii przestał działać, skok kosztów, wybuch tokenów, rosnące błędy, skok błędów, próg budżetu, dopasowana sygnatura zagrożenia, wynik narzędzia bezpieczeństwa, zmiana postawy bezpieczeństwa. Twoje własne reguły są opcjonalne, dodatkowo.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Wstrzymywanie ryzykownego wywołania jest opt-in i dostarczane wyłączone.**
Rekurencyjne usuwanie, wymuszone push, sudo, sekrety, instalacje pakietów i wywołania wychodzące — każde otrzymuje regułę, którą możesz włączyć. Dopóki tego nie zrobisz, ClawMetry obserwuje i niczego nie zmienia. Gdy jedna jest włączona, pasujące wywołania czekają tutaj (lub na twoim telefonie) na zatwierdzenie lub odrzucenie.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Więcej, dla każdego środowiska uruchomieniowego: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
