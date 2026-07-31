<!-- i18n-src:8252f6b1d31d -->
> Polski translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zobacz, jak myśli twój agent.** Obserwowalność w czasie rzeczywistym dla **14 środowisk uruchomieniowych agentów AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex i 10 innych. Jeden dashboard dla całej floty twoich agentów.

> 🌐 **Przeczytaj to w innych językach:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [więcej →](docs/i18n/)

Jedna komenda. Zero konfiguracji. Automatyczne wykrywanie wszystkiego.

```bash
pip install clawmetry && clawmetry
```

Otwiera się pod adresem **http://localhost:8900** i to wszystko.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Działa z 14 środowiskami uruchomieniowymi agentów

ClawMetry zaczęło jako narzędzie obserwowalności dla OpenClaw, a teraz mierzy **całą twoją flotę agentów** w jednym dashboardzie, automatycznie wykrywając każde środowisko uruchomieniowe na twojej maszynie:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw i NemoClaw są darmowe w aplikacji open source; pozostałe środowiska uruchomieniowe odblokowują się dzięki ClawMetry Cloud lub licencji Pro w wersji self-hosted. Przełącz środowisko uruchomieniowe z nagłówka, a każda zakładka, koszty, tokeny, narzędzia, ślady, ponownie ograniczy się do tego środowiska. Zobacz **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**, aby poznać dokładny podział darmowy/płatny, macierz poziomów, kształt `/api/entitlement` oraz CLI `clawmetry license`.

## Co otrzymujesz

- **Flow** — Animowany na żywo diagram pokazujący przepływ wiadomości przez kanały, mózg, narzędzia i z powrotem
- **Overview** — Kontrole stanu, mapa cieplna aktywności, liczba sesji, informacje o modelu
- **Usage** — Śledzenie tokenów i kosztów z podziałem dziennym/tygodniowym/miesięcznym
- **Sessions** — Aktywne sesje agenta z modelem, tokenami, ostatnią aktywnością
- **Crons** — Zaplanowane zadania ze statusem, następnym uruchomieniem, czasem trwania
- **Logs** — Kolorowe strumieniowanie logów w czasie rzeczywistym
- **Memory** — Przeglądanie SOUL.md, MEMORY.md, AGENTS.md, notatek dziennych
- **Transcripts** — Interfejs dymków czatu do odczytu historii sesji
- **Alerts** — Limity budżetowe, wyzwalacze wskaźnika błędów, wykrywanie offline agenta; trasowanie do Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Blokowanie destrukcyjnego usuwania, wymuszonych pushy, mutacji baz danych, sudo, instalacji pakietów, wywołań sieciowych za jednym kliknięciem zatwierdzenia

## Zrzuty ekranu

### 🧠 Brain — Strumień zdarzeń agenta na żywo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Zużycie tokenów i podsumowanie sesji
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Kanał wywołań narzędzi w czasie rzeczywistym
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Podział kosztów według modelu i sesji
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Przeglądarka plików obszaru roboczego
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Postawa bezpieczeństwa i dziennik audytu
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limity budżetowe, wyzwalacze wskaźnika błędów, webhooki do Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blokowanie ryzykownych wywołań narzędzi za ręcznym zatwierdzeniem; reguły ochrony oparte na politykach
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blokowanie przed wykonaniem dla Claude Code** — jedna komenda instaluje
hook PreToolUse, który wstrzymuje pasujące wywołania narzędzi *przed* ich uruchomieniem i czeka
na twoją decyzję (jedno dotknięcie z telefonu przy włączonych
[powiadomieniach push w chmurze](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Odmowa blokuje tylko to jedno wywołanie narzędzia, agent zachowuje swoją sesję i może
spróbować innego podejścia. Zatwierdzenie na telefonie pomija własny
prompt uprawnień Claude Code (już odpowiedziałeś). Niedopasowane narzędzia kosztują ~40 ms i
przechodzą do normalnego przepływu uprawnień Claude Code. Otrzymujesz też powiadomienie push na telefon, gdy
sam Claude Code czeka na ciebie (powiadomienia `permission_prompt` /
`idle_prompt`).

## Instalacja

**Jedna komenda (zalecane):**
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

Aplikacja React v2 znajduje się w `frontend/` i jest serwowana pod `/v2`, gdy
serwer Flask jest uruchomiony z włączonym v2.

Podczas developmentu użyj dwóch terminali:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

Otwórz `http://localhost:5173/v2/`. Vite przekierowuje żądania `/api` do
`http://localhost:8900`, więc aplikacja React może komunikować się z lokalnym serwerem Flask
bez dodatkowej konfiguracji CORS.

Aby zbudować paczkę, która trafia do pakietu Pythona:

```bash
cd frontend
npm run build
```

Paczka produkcyjna jest zapisywana w `clawmetry/static/v2/dist/`.

## Zgodność środowisk uruchomieniowych / agentów

ClawMetry obserwuje wiele środowisk uruchomieniowych agentów AI, nie tylko OpenClaw. Każde środowisko inne niż OpenClaw ma dedykowany adapter odczytu, który tłumaczy jego natywny format sesji na ujednolicone kształty ClawMetry; daemon wprowadza je do tego samego magazynu DuckDB + zrzutu w chmurze, oznaczonych środowiskiem uruchomieniowym, a zakładka odtwarzania sesji pokazuje **przełącznik środowiska uruchomieniowego**, gdy obecne jest więcej niż jedno. Zobacz [`docs/compatibility.md`](docs/compatibility.md), aby poznać pełną macierz i przewodnik po dodawaniu środowisk uruchomieniowych, oraz [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md), aby zapoznać się z wprowadzeniem do rodziny OpenClaw.

| Środowisko uruchomieniowe / agent | Status | Uwagi |
|---|---|---|
| **OpenClaw** | Natywne | Referencyjne środowisko uruchomieniowe, wykrywane automatycznie |
| **PicoClaw** | Adapter beta | Płaski JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Transkrypcje, model, wywołania narzędzi. |
| **NanoClaw** | Adapter beta | SQLite na sesję (`data/v2-sessions`). Transkrypcje + liczba wiadomości. |
| **Hermes** | Adapter beta | SQLite `~/.hermes/state.db`. Transkrypcje, model, tokeny/koszt. |
| **Claude Code** | Adapter beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkrypcje, model, wywołania narzędzi + rozumowanie, użycie tokenów. |
| **Codex** | Adapter beta | Rollout JSONL `~/.codex/sessions/...`. Transkrypcje, model, wywołania narzędzi, użycie tokenów. |
| **Cursor** | Adapter beta | SQLite `state.vscdb`. Transkrypcje czatu/composera, model. |
| **Aider** | Adapter beta | `.aider.chat.history.md` na projekt. Transkrypcje, model, liczba tokenów. |
| **Goose** | Adapter beta | SQLite `~/.local/share/goose`. Transkrypcje, model, wywołania narzędzi, sumy tokenów. |
| **opencode** | Adapter beta | SQLite `~/.local/share/opencode`. Transkrypcje, model, wywołania narzędzi, tokeny + koszt. |
| **Qwen Code** | Adapter beta | JSONL `~/.qwen/projects/.../chats`. Transkrypcje, model, wywołania narzędzi, użycie tokenów. |
| **Pi** | Adapter beta | JSONL `~/.pi/agent/sessions`. Transkrypcje, model, wywołania narzędzi, tokeny + koszt. |
| **Deep Agents** | Adapter beta | SQLite `~/.deepagents/.state/sessions.db`. Transkrypcje, model, wywołania narzędzi, tokeny + koszt. |
| **n8n** | Adapter beta | SQLite `~/.n8n/database.sqlite`. Wykonania przepływów pracy, uruchomienia węzłów, prompty AI Agent, model + tokeny tam, gdzie n8n je zapisuje. |

"Adapter beta" oznacza, że ClawMetry dostarcza czytnik dla rzeczywistego formatu danych na dysku tego środowiska uruchomieniowego, każdy zbudowany i zweryfikowany na rzeczywistej instalacji na rzeczywistej maszynie (zobacz `tests/fixtures/runtimes/<rt>/`). Adaptery są tylko do odczytu; każdy uczciwie pokazuje, co jego środowisko uruchomieniowe faktycznie przechowuje (np. PicoClaw/NanoClaw/Cursor nie zapisują kosztu tokenów na dysku). Gdy na jednym węźle działa kilka środowisk uruchomieniowych, przełącznik środowiska ogranicza widok sesji do jednego, dla czystego, dogłębnego przeglądu.

## Śledzenie dowolnego agenta SDK — atrybucja kosztów poza pętlą

Wszystkie powyższe środowiska uruchomieniowe zapisują sesje na dysku. Twój własny **agent produkcyjny**, ten zbudowany na OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B lub zwykłej pętli `httpx`, tego nie robi. Interceptor ClawMetry działający bez konfiguracji nadal przechwytuje jego wywołania LLM (koszt, tokeny, opóźnienie, błędy), łatając w locie `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (lub zmienna środowiskowa `CLAWMETRY_SOURCE=support-agent`) oznacza każde wywołanie **nazwanym źródłem**, więc każdy uruchamiany przez ciebie produkt pojawia się jako własna, pierwszoklasowa linia z możliwością atrybucji kosztów w karcie **🔌 Out-loop sources** na Overview w dashboardzie, wywołania, dostawcy, opóźnienie, wskaźnik błędów na agenta. Brak ustawionego źródła? Wywołania nadal są śledzone, karta po prostu pozostaje ukryta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

To ta sama warstwa danych, którą zasilają adaptery środowisk uruchomieniowych (DuckDB → zrzut w chmurze), więc źródła poza pętlą synchronizują się z dashboardem w chmurze tak samo jak wszystko inne, z szyfrowaniem end-to-end.

## OpenTelemetry — neutralne wobec dostawcy, wysyłaj swoje ślady wszędzie

ClawMetry mówi w obie strony w standardzie **OpenTelemetry**, używając **konwencji semantycznych GenAI**, więc ślady twojego agenta nigdy nie są zablokowane w jednym narzędziu.

**Eksportuj** każdą sesję, wywołania LLM, narzędzia, subagentów, tokeny, koszt, jako ślady OTLP/HTTP GenAI do dowolnego kolektora (Datadog, Grafana, Honeycomb lub własny OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Nagłówki uwierzytelniające i interwał odpytywania to opcjonalne zmienne środowiskowe:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Wprowadzanie** — wbudowany odbiornik OTLP przyjmuje ślady i metryki z czegokolwiek innego pod `/v1/traces` i `/v1/metrics` (`pip install clawmetry[otel]` dla wprowadzania protobuf).

Otrzymujesz dashboard ClawMetry działający bez konfiguracji, lokalnie, **oraz** swoje dane w dowolnym backendzie, którego twój zespół już używa, bez blokady dostawcy, bez drugiego agenta do zainstalowania.

## Konfiguracja

Większość osób nie potrzebuje żadnej konfiguracji. ClawMetry automatycznie wykrywa twój obszar roboczy, logi, sesje i crony.

Jeśli potrzebujesz dostosowania:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Wszystkie opcje: `clawmetry --help`

## Obsługiwane kanały

ClawMetry pokazuje aktywność na żywo dla każdego skonfigurowanego kanału OpenClaw. Tylko kanały faktycznie skonfigurowane w twoim `openclaw.json` pojawiają się na diagramie Flow, nieskonfigurowane są automatycznie ukrywane.

Kliknij dowolny węzeł kanału na Flow, aby zobaczyć widok dymków czatu na żywo z liczbą wiadomości przychodzących/wychodzących.

| Kanał | Status | Podgląd na żywo | Uwagi |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Pełny | ✅ | Wiadomości, statystyki, odświeżanie co 10 s |
| 💬 **iMessage** | ✅ Pełny | ✅ | Odczytuje bezpośrednio `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Pełny | ✅ | Przez WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Pełny | ✅ | Przez signal-cli |
| 🟣 **Discord** | ✅ Pełny | ✅ | Wykrywanie serwera + kanału |
| 🟪 **Slack** | ✅ Pełny | ✅ | Wykrywanie przestrzeni roboczej + kanału |
| 🌐 **Webchat** | ✅ Pełny | ✅ | Wbudowane sesje interfejsu webowego |
| 📡 **IRC** | ✅ Pełny | ✅ | Interfejs dymków w stylu terminala |
| 🍏 **BlueBubbles** | ✅ Pełny | ✅ | iMessage przez BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Pełny | ✅ | Przez webhooki Chat API |
| 🟣 **MS Teams** | ✅ Pełny | ✅ | Przez wtyczkę bota Teams |
| 🔷 **Mattermost** | ✅ Pełny | ✅ | Samodzielnie hostowany czat zespołowy |
| 🟩 **Matrix** | ✅ Pełny | ✅ | Zdecentralizowany, obsługa E2EE |
| 🟢 **LINE** | ✅ Pełny | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Pełny | ✅ | Zdecentralizowane wiadomości prywatne NIP-04 |
| 🟣 **Twitch** | ✅ Pełny | ✅ | Czat przez połączenie IRC |
| 🔷 **Feishu/Lark** | ✅ Pełny | ✅ | Subskrypcja zdarzeń WebSocket |
| 🔵 **Zalo** | ✅ Pełny | ✅ | Zalo Bot API |

> **Automatyczne wykrywanie:** ClawMetry odczytuje twój `~/.openclaw/openclaw.json` i renderuje wyłącznie faktycznie skonfigurowane kanały. Nie jest wymagana ręczna konfiguracja.

## Wdrożenie Docker

Chcesz uruchomić ClawMetry w kontenerze? Żaden problem! 🐳

**Szybki start z Docker:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
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

> **Uwaga:** Podczas uruchamiania w Docker zamontuj katalogi danych i logów swojego agenta (np. `~/.openclaw`, `~/.claude`, `~/.codex`), aby ClawMetry mogło automatycznie wykryć twoją konfigurację.

## Wymagania

- Python 3.8+
- Flask (instalowany automatycznie przez pip)
- Środowisko uruchomieniowe agenta AI na tej samej maszynie: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents lub n8n (lub zamontowane woluminy dla Dockera)
- Linux lub macOS

## Obsługa NemoClaw / OpenShell

ClawMetry automatycznie wykrywa [NemoClaw](https://github.com/NVIDIA/NemoClaw), wrapper bezpieczeństwa klasy enterprise firmy NVIDIA dla OpenClaw, który uruchamia agentów wewnątrz sandboksowanych kontenerów OpenShell.

W większości przypadków nie jest wymagana żadna dodatkowa konfiguracja. Daemon synchronizacji automatycznie odkrywa pliki sesji, niezależnie czy znajdują się w `~/.openclaw/` na hoście, czy wewnątrz kontenera OpenShell.

### Jak to działa

ClawMetry wykrywa NemoClaw na dwa sposoby:

1. **Wykrywanie binarki** — sprawdza obecność CLI `nemoclaw` i uruchamia `nemoclaw status`, aby pobrać informacje o sandboksie
2. **Wykrywanie kontenera** — skanuje uruchomione kontenery Docker w poszukiwaniu obrazów `openshell`, `nemoclaw` lub `ghcr.io/nvidia/`, następnie odczytuje sesje przez zamontowane woluminy lub `docker cp`

Pliki sesji zsynchronizowane z kontenerów NemoClaw są oznaczone metadanymi `runtime=nemoclaw` i `container_id` w dashboardzie chmury, dzięki czemu na pierwszy rzut oka można je odróżnić od standardowych sesji OpenClaw.

### Zalecana konfiguracja: daemon synchronizacji na HOŚCIE

Dla najlepszego doświadczenia uruchom daemon synchronizacji ClawMetry na **maszynie hosta** (nie wewnątrz sandboksa). Pozwala to uniknąć ograniczeń polityki sieciowej NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Daemon synchronizacji automatycznie znajdzie sesje wewnątrz dowolnych uruchomionych kontenerów OpenShell.

### Opcjonalnie: jawna nazwa sandboksa

Jeśli automatyczne wykrywanie nie działa, wskaż ClawMetry właściwy sandboks:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Uruchamianie wewnątrz sandboksa (zaawansowane)

Jeśli musisz uruchomić daemon synchronizacji **wewnątrz** sandboksa OpenShell, dodaj tę regułę ruchu wychodzącego do swojej polityki sieciowej NemoClaw, aby mógł dotrzeć do API wprowadzania danych ClawMetry:

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
| `ingest.clawmetry.com` | 443 | HTTPS | Tak (daemon synchronizacji → chmura) |
| `localhost:8900` | 8900 | HTTP | Tak (lokalny interfejs dashboardu) |
| Gniazdo Dockera (`/var/run/docker.sock`) | — | Gniazdo Unix | Do wykrywania sesji kontenerów |

Daemon synchronizacji wykonuje wyłącznie wywołania wychodzące HTTPS do `ingest.clawmetry.com`. Nie są wymagane żadne porty przychodzące.

---

## Wdrożenie w chmurze

Zobacz **[Przewodnik testowania w chmurze](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)**, aby poznać tunele SSH, reverse proxy i Docker.

## Testowanie

Ten projekt jest testowany za pomocą BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

ClawMetry wysyła anonimowe sygnały cyklu życia instalacji na adres
`https://app.clawmetry.com/api/install`: jeden sygnał `install` przy pierwszym
uruchomieniu CLI `clawmetry` na nowej maszynie, jeden sygnał `update`
przy pierwszym uruchomieniu po aktualizacji do nowej wersji, oraz jeden sygnał `onboarded`,
gdy ukończysz wybór onboardingu w dashboardzie. Używamy tego do
liczenia rzeczywistych instalacji (surowe liczby pobrań PyPI to w ~98% mirrory, CI
oraz ponowne pobrania przy automatycznej aktualizacji) oraz do poznania, które frameworki agentów i
wersje faktycznie są w użyciu.

**Maksymalnie jeden POST na zdarzenie cyklu życia na wersję**, zawierający:

| Pole | Przykład | Dlaczego |
|---|---|---|
| `install_id` | losowy UUID przechowywany w `~/.clawmetry/install_id` | deduplikacja; anonimowe, dopóki jawnie nie połączysz synchronizacji Cloud (uwierzytelniony heartbeat daemona wtedy niesie tę wartość, łącząc tę instalację z twoim kontem) |
| `event` | `install` / `update` / `onboarded` | świeża instalacja vs aktualizacja istniejącej |
| `version` | `0.12.167` | jakie wersje są w użyciu |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorytety wsparcia platform |
| `python` | `3.11.15` | macierz wsparcia wersji Pythona |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | z jakimi agentami powinniśmy integrować się dalej |
| `is_ci` / `ci_provider` | `true` / `github_actions` | oddzielenie instalacji ludzkich od szumu CI |

**Czego NIE wysyłamy**: IP (chmura wyprowadza kod kraju po stronie serwera
z żądania, następnie odrzuca IP), nazwy hosta, nazwy użytkownika, ścieżki obszaru roboczego, zawartości plików, twojego api_key, twojego adresu e-mail, niczego, co jest PII lub
specyficzne dla obszaru roboczego. Ładunek transmisji można zaudytować w
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Rezygnacja** (dowolna z tych opcji wyłącza ją na stałe):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Awaria sieci nigdy nie blokuje uruchomienia `clawmetry`, sygnał jest wysyłany
w trybie fire-and-forget w wątku daemona z limitem czasu 3 s.

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
