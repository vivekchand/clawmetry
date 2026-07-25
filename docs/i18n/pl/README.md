<!-- i18n-src:8f42d460a973 -->
> Polski translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zobacz, jak myśli twój agent.** Obserwowalność w czasie rzeczywistym dla **14 środowisk uruchomieniowych agentów AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex i 10 innych. Jeden pulpit dla całej floty twoich agentów.

> 🌐 **Przeczytaj to w:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [więcej →](docs/i18n/)

Jedna komenda. Zero konfiguracji. Automatyczne wykrywanie wszystkiego.

```bash
pip install clawmetry && clawmetry
```

Otwiera się pod **http://localhost:8900** i to wszystko.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Działa z 14 środowiskami uruchomieniowymi agentów

ClawMetry zaczęło jako narzędzie obserwowalności dla OpenClaw, a teraz mierzy **całą flotę twoich agentów** w jednym pulpicie, automatycznie wykrywając każde środowisko na twojej maszynie:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw i NemoClaw są darmowe w aplikacji open-source; pozostałe środowiska uruchomieniowe odblokowuje się dzięki ClawMetry Cloud lub licencji Pro w wersji self-hosted. Przełącz środowisko z poziomu nagłówka, a każda zakładka - koszty, tokeny, narzędzia, ślady (traces) - zostanie przeskalowana do tego środowiska. Zobacz **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**, aby poznać dokładny podział darmowe/płatne, macierz poziomów, kształt `/api/entitlement` oraz CLI `clawmetry license`.

## Co otrzymujesz

- **Flow** - Animowany diagram na żywo pokazujący przepływ wiadomości przez kanały, mózg (brain), narzędzia i z powrotem
- **Overview** - Kontrole stanu, mapa cieplna aktywności, liczba sesji, informacje o modelu
- **Usage** - Śledzenie tokenów i kosztów z podziałem dziennym/tygodniowym/miesięcznym
- **Sessions** - Aktywne sesje agentów wraz z modelem, tokenami, ostatnią aktywnością
- **Crons** - Zaplanowane zadania ze statusem, następnym uruchomieniem, czasem trwania
- **Logs** - Kolorowe strumieniowanie logów w czasie rzeczywistym
- **Memory** - Przeglądanie SOUL.md, MEMORY.md, AGENTS.md, notatek dziennych
- **Transcripts** - Interfejs dymków czatu do odczytu historii sesji
- **Alerts** - Limity budżetowe, wyzwalacze na podstawie wskaźnika błędów, wykrywanie offline agenta; kierowanie do Slack, Discord, PagerDuty, Telegram, e-mail
- **Approvals** - Blokowanie destrukcyjnych usunięć, wymuszonych pushy, mutacji bazy danych, sudo, instalacji pakietów, połączeń sieciowych za jednym kliknięciem zatwierdzenia

## Zrzuty ekranu

### 🧠 Brain - Strumień zdarzeń agenta na żywo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview - Użycie tokenów i podsumowanie sesji
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow - Kanał wywołań narzędzi w czasie rzeczywistym
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens - Podział kosztów według modelu i sesji
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory - Przeglądarka plików workspace
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security - Postawa bezpieczeństwa i log audytu
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts - Limity budżetowe, wyzwalacze wskaźnika błędów, webhooki do Slack / Discord / PagerDuty / e-mail
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals - Blokowanie ryzykownych wywołań narzędzi za ręcznym zatwierdzeniem; reguły ochrony oparte na polityce
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Instalacja

**Jedna linia (zalecane):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Ze źródła:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Rozwój frontendu v2

Aplikacja v2 w React znajduje się w `frontend/` i jest serwowana pod `/v2`, gdy
serwer Flask jest uruchomiony z włączonym v2.

Podczas pracy nad rozwojem używaj dwóch terminali:

```bash
# Terminal 1: Flask API/serwer na :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: serwer deweloperski Vite na :5173
cd frontend
nvm use
npm ci
npm run dev
```

Otwórz `http://localhost:5173/v2/`. Vite przekierowuje żądania `/api` do
`http://localhost:8900`, dzięki czemu aplikacja React może komunikować się z lokalnym serwerem Flask
bez dodatkowej konfiguracji CORS.

Aby zbudować paczkę, która trafia do pakietu Python:

```bash
cd frontend
npm run build
```

Paczka produkcyjna jest zapisywana w `clawmetry/static/v2/dist/`.

## Zgodność ze środowiskami uruchomieniowymi / agentami

ClawMetry obserwuje wiele środowisk uruchomieniowych agentów AI, nie tylko OpenClaw. Każde środowisko inne niż OpenClaw dostarcza dedykowany adapter odczytu, który tłumaczy jego natywny format sesji na ujednolicone kształty ClawMetry; demon (daemon) wczytuje je do tego samego magazynu DuckDB + migawki chmurowej, oznaczone środowiskiem uruchomieniowym, a zakładka odtwarzania sesji pokazuje **przełącznik środowiska** przy obecności więcej niż jednego. Zobacz [`docs/compatibility.md`](docs/compatibility.md), aby poznać pełną macierz oraz przewodnik dodawania środowisk uruchomieniowych, a także [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md), aby zapoznać się z wprowadzeniem do rodziny OpenClaw.

| Środowisko uruchomieniowe / agent | Status | Uwagi |
|---|---|---|
| **OpenClaw** | Natywne | Referencyjne środowisko uruchomieniowe, wykrywane automatycznie |
| **PicoClaw** | Adapter beta | Płaski JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Transkrypty, model, wywołania narzędzi. |
| **NanoClaw** | Adapter beta | SQLite per sesja (`data/v2-sessions`). Transkrypty + liczba wiadomości. |
| **Hermes** | Adapter beta | SQLite `~/.hermes/state.db`. Transkrypty, model, tokeny/koszty. |
| **Claude Code** | Adapter beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkrypty, model, wywołania narzędzi + myślenie, użycie tokenów. |
| **Codex** | Adapter beta | Rollout JSONL `~/.codex/sessions/...`. Transkrypty, model, wywołania narzędzi, użycie tokenów. |
| **Cursor** | Adapter beta | SQLite `state.vscdb`. Transkrypty czatu/composera, model. |
| **Aider** | Adapter beta | `.aider.chat.history.md` na projekt. Transkrypty, model, liczba tokenów. |
| **Goose** | Adapter beta | SQLite `~/.local/share/goose`. Transkrypty, model, wywołania narzędzi, sumy tokenów. |
| **opencode** | Adapter beta | SQLite `~/.local/share/opencode`. Transkrypty, model, wywołania narzędzi, tokeny + koszty. |
| **Qwen Code** | Adapter beta | JSONL `~/.qwen/projects/.../chats`. Transkrypty, model, wywołania narzędzi, użycie tokenów. |
| **Pi** | Adapter beta | JSONL `~/.pi/agent/sessions`. Transkrypty, model, wywołania narzędzi, tokeny + koszty. |
| **Deep Agents** | Adapter beta | SQLite `~/.deepagents/.state/sessions.db`. Transkrypty, model, wywołania narzędzi, tokeny + koszty. |

„Adapter beta" oznacza, że ClawMetry dostarcza czytnik dla rzeczywistego formatu na dysku danego środowiska uruchomieniowego, z których każdy zbudowano i zweryfikowano na rzeczywistej instalacji na rzeczywistej maszynie (zobacz `tests/fixtures/runtimes/<rt>/`). Adaptery są tylko do odczytu; każdy z nich uczciwie pokazuje, co dane środowisko faktycznie zapisuje (np. PicoClaw/NanoClaw/Cursor nie zapisują kosztu tokenów na dysk). Gdy na jednym węźle działa kilka środowisk uruchomieniowych, przełącznik środowiska zawęża widok sesji do jednego, umożliwiając dokładną analizę.

## Śledzenie dowolnego agenta SDK - atrybucja kosztów spoza pętli (out-loop)

Powyższe środowiska uruchomieniowe zapisują sesje na dysk. Twój własny **agent produkcyjny** - ten zbudowany na OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B lub zwykłej pętli `httpx` - tego nie robi. Interceptor ClawMetry działający bez konfiguracji nadal przechwytuje jego wywołania LLM (koszt, tokeny, opóźnienie, błędy), łatając (monkey-patching) `httpx`/`requests`:

```python
import clawmetry.track            # aktywacja interceptora
clawmetry.track.set_source("support-agent")   # nazwanie tego produktu

# ...twój agent działa jak zwykle; każde wywołanie LLM jest teraz śledzone i atrybuowane.
```

`set_source()` (lub zmienna środowiskowa `CLAWMETRY_SOURCE=support-agent`) oznacza każde wywołanie **nazwanym źródłem**, dzięki czemu każdy uruchamiany przez ciebie produkt pojawia się jako własna, w pełni atrybuowana kosztowo linia na karcie **🔌 Źródła spoza pętli (out-loop)** w zakładce Overview - wywołania, dostawcy, opóźnienia, wskaźnik błędów na agenta. Brak ustawionego źródła? Wywołania są nadal śledzone, po prostu karta pozostaje ukryta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

To ta sama warstwa danych, którą zasilają adaptery środowisk uruchomieniowych (DuckDB → migawka chmurowa), więc źródła spoza pętli synchronizują się z pulpitem chmurowym tak samo jak wszystko inne, w sposób szyfrowany E2E.

## OpenTelemetry - neutralne wobec dostawcy, wysyłaj swoje ślady gdziekolwiek chcesz

ClawMetry mówi w obu kierunkach w standardzie **OpenTelemetry**, wykorzystując **konwencje semantyczne GenAI**, dzięki czemu ślady twojego agenta nigdy nie są zamknięte w jednym narzędziu.

**Eksportuj** każdą sesję - wywołania LLM, narzędzia, subagentów, tokeny, koszty - jako ślady OTLP/HTTP GenAI do dowolnego kolektora (Datadog, Grafana, Honeycomb lub własny OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# równoważnie:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Nagłówki uwierzytelniające i interwał odpytywania są opcjonalnymi zmiennymi środowiskowymi:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # dodatkowe nagłówki HTTP
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # sekundy (domyślnie 60)
```

**Wczytywanie (ingest)** - wbudowany odbiornik OTLP przyjmuje ślady i metryki z czegokolwiek innego pod `/v1/traces` i `/v1/metrics` (`pip install clawmetry[otel]` dla wczytywania protobuf).

Otrzymujesz zarówno pulpit ClawMetry działający bez konfiguracji i lokalnie, jak i swoje dane w dowolnym zapleczu, którego już używa twój zespół - bez uzależnienia od dostawcy, bez potrzeby instalowania drugiego agenta.

## Konfiguracja

Większość osób nie potrzebuje żadnej konfiguracji. ClawMetry automatycznie wykrywa twój workspace, logi, sesje i zadania cron.

Jeśli jednak potrzebujesz dostosowania:

```bash
clawmetry --port 9000              # Niestandardowy port (domyślnie: 8900)
clawmetry --host 127.0.0.1         # Powiązanie tylko z localhost
clawmetry --workspace ~/mybot      # Niestandardowa ścieżka workspace
clawmetry --name "Alice"           # Twoje imię w wizualizacji Flow
```

Wszystkie opcje: `clawmetry --help`

## Obsługiwane kanały

ClawMetry pokazuje aktywność na żywo dla każdego skonfigurowanego przez ciebie kanału OpenClaw. Na diagramie Flow pojawiają się tylko kanały faktycznie skonfigurowane w twoim `openclaw.json` - nieskonfigurowane są automatycznie ukrywane.

Kliknij dowolny węzeł kanału w Flow, aby zobaczyć widok dymków czatu na żywo z licznikami wiadomości przychodzących/wychodzących.

| Kanał | Status | Wyskakujące okno na żywo | Uwagi |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Pełne | ✅ | Wiadomości, statystyki, odświeżanie co 10s |
| 💬 **iMessage** | ✅ Pełne | ✅ | Odczytuje bezpośrednio `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Pełne | ✅ | Przez WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Pełne | ✅ | Przez signal-cli |
| 🟣 **Discord** | ✅ Pełne | ✅ | Wykrywanie serwera i kanału |
| 🟪 **Slack** | ✅ Pełne | ✅ | Wykrywanie workspace i kanału |
| 🌐 **Webchat** | ✅ Pełne | ✅ | Wbudowane sesje interfejsu webowego |
| 📡 **IRC** | ✅ Pełne | ✅ | Interfejs dymków w stylu terminala |
| 🍏 **BlueBubbles** | ✅ Pełne | ✅ | iMessage przez REST API BlueBubbles |
| 🔵 **Google Chat** | ✅ Pełne | ✅ | Przez webhooki Chat API |
| 🟣 **MS Teams** | ✅ Pełne | ✅ | Przez wtyczkę bota Teams |
| 🔷 **Mattermost** | ✅ Pełne | ✅ | Samodzielnie hostowany czat zespołowy |
| 🟩 **Matrix** | ✅ Pełne | ✅ | Zdecentralizowany, wsparcie E2EE |
| 🟢 **LINE** | ✅ Pełne | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Pełne | ✅ | Zdecentralizowane wiadomości bezpośrednie NIP-04 |
| 🟣 **Twitch** | ✅ Pełne | ✅ | Czat przez połączenie IRC |
| 🔷 **Feishu/Lark** | ✅ Pełne | ✅ | Subskrypcja zdarzeń WebSocket |
| 🔵 **Zalo** | ✅ Pełne | ✅ | Zalo Bot API |

> **Automatyczne wykrywanie:** ClawMetry odczytuje twój `~/.openclaw/openclaw.json` i renderuje tylko te kanały, które faktycznie skonfigurowałeś. Nie jest wymagana ręczna konfiguracja.

## Wdrożenie Docker

Chcesz uruchomić ClawMetry w kontenerze? Żaden problem! 🐳

**Szybki start z Docker:**

```bash
# Zbuduj obraz
docker build -t clawmetry .

# Uruchom z domyślnymi ustawieniami
docker run -p 8900:8900 clawmetry

# Lub zamontuj katalog danych swojego agenta (pokazano: ~/.openclaw dla OpenClaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Przykład Docker Compose:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **Uwaga:** Podczas uruchamiania w Dockerze zamontuj katalogi danych i logów swojego agenta (np. `~/.openclaw`, `~/.claude`, `~/.codex`), aby ClawMetry mogło automatycznie wykryć twoją konfigurację.

## Wymagania

- Python 3.8+
- Flask (instalowany automatycznie przez pip)
- Środowisko uruchomieniowe agenta AI na tej samej maszynie: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi lub Deep Agents (albo zamontowane woluminy dla Dockera)
- Linux lub macOS

## Wsparcie NemoClaw / OpenShell

ClawMetry automatycznie wykrywa [NemoClaw](https://github.com/NVIDIA/NemoClaw) - opakowanie bezpieczeństwa klasy enterprise firmy NVIDIA dla OpenClaw, które uruchamia agentów wewnątrz izolowanych kontenerów OpenShell.

W większości przypadków nie jest wymagana dodatkowa konfiguracja. Demon synchronizacji automatycznie odnajduje pliki sesji niezależnie od tego, czy znajdują się w `~/.openclaw/` na hoście, czy wewnątrz kontenera OpenShell.

### Jak to działa

ClawMetry wykrywa NemoClaw na dwa sposoby:

1. **Wykrywanie binarne** - sprawdza obecność CLI `nemoclaw` i uruchamia `nemoclaw status`, aby uzyskać informacje o sandboxie
2. **Wykrywanie kontenerów** - skanuje działające kontenery Docker w poszukiwaniu obrazów `openshell`, `nemoclaw` lub `ghcr.io/nvidia/`, a następnie odczytuje sesje przez zamontowane woluminy lub `docker cp`

Pliki sesji zsynchronizowane z kontenerów NemoClaw są oznaczane metadanymi `runtime=nemoclaw` i `container_id` w pulpicie chmurowym, dzięki czemu można je odróżnić na pierwszy rzut oka od standardowych sesji OpenClaw.

### Zalecana konfiguracja: demon synchronizacji na HOŚCIE

Dla najlepszego doświadczenia uruchom demon synchronizacji ClawMetry na **maszynie hosta** (nie wewnątrz sandboxa). Pozwala to uniknąć ograniczeń polityki sieciowej NemoClaw.

```bash
# Na hoście (poza sandboxem)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Demon synchronizacji automatycznie odnajdzie sesje wewnątrz działających kontenerów OpenShell.

### Opcjonalnie: jawna nazwa sandboxa

Jeśli automatyczne wykrywanie nie działa, wskaż ClawMetry właściwy sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Uruchamianie wewnątrz sandboxa (zaawansowane)

Jeśli musisz uruchomić demon synchronizacji **wewnątrz** sandboxa OpenShell, dodaj tę regułę ruchu wychodzącego do swojej polityki sieciowej NemoClaw, aby mógł on dotrzeć do API ingestu ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Zastosuj za pomocą:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Porty i punkty końcowe

| Punkt końcowy | Port | Protokół | Wymagane |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Tak (demon synchronizacji → chmura) |
| `localhost:8900` | 8900 | HTTP | Tak (lokalny interfejs pulpitu) |
| Gniazdo Dockera (`/var/run/docker.sock`) | — | Gniazdo Unix | Do wykrywania sesji w kontenerach |

Demon synchronizacji wykonuje wyłącznie wychodzące połączenia HTTPS do `ingest.clawmetry.com`. Żadne porty przychodzące nie są wymagane.

---

## Wdrożenie w chmurze

Zobacz **[Przewodnik testowania w chmurze](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**, aby dowiedzieć się o tunelach SSH, reverse proxy i Dockerze.

## Testowanie

Ten projekt jest testowany za pomocą BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

ClawMetry wysyła pojedynczy anonimowy sygnał „pierwszego uruchomienia" do
`https://app.clawmetry.com/api/install` przy pierwszym uruchomieniu CLI
`clawmetry` na nowej maszynie. Wykorzystujemy to do liczenia instalacji (jedynej
metryki marketingowej, jaką mamy dla projektu OSS) oraz do poznania, jakie
frameworki agentów mają zainstalowane nasi użytkownicy.

**Dokładnie jeden POST na instalację**, zawierający:

| Pole | Przykład | Dlaczego |
|---|---|---|
| `install_id` | losowy UUID zapisany w `~/.clawmetry/install_id` | deduplikacja; niepowiązane z twoim e-mailem ani api_key |
| `version` | `0.12.167` | jakie wersje są w użyciu |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorytety wsparcia platform |
| `python` | `3.11.15` | macierz wsparcia wersji Pythona |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | z jakimi agentami powinniśmy integrować się dalej |
| `is_ci` / `ci_provider` | `true` / `github_actions` | oddzielenie instalacji ludzkich od szumu CI |

**Czego NIE wysyłamy**: adresu IP (chmura wyprowadza kod kraju po stronie
serwera z żądania, a następnie odrzuca IP), nazwy hosta, nazwy użytkownika,
ścieżki workspace, zawartości plików, twojego api_key, twojego e-maila,
niczego, co byłoby PII lub specyficzne dla workspace. Ładunek transmisji
można zweryfikować w [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Rezygnacja** (dowolna z poniższych opcji wyłącza ją na stałe):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # dla danej powłoki
export DO_NOT_TRACK=1                          # standard W3C obowiązujący we wszystkich narzędziach
touch ~/.clawmetry/notelemetry                 # trwały znacznik plikowy
```

Błąd sieci nigdy nie blokuje działania `clawmetry` - sygnał jest wysyłany
w trybie fire-and-forget w osobnym wątku demona, z limitem czasu 3 s.

## Historia gwiazdek

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Licencja

MIT

---

<p align="center">
  <strong>🦞 Zobacz, jak myśli twój agent</strong><br>
  <sub>Stworzone przez <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Część ekosystemu <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
