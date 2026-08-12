<!-- i18n-src:7cfb63716507 -->
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

Otwiera się pod adresem **http://localhost:8900** i to wszystko.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Działa z 14 środowiskami uruchomieniowymi agentów

ClawMetry zaczęło jako narzędzie obserwowalności dla OpenClaw, a teraz mierzy **całą flotę twoich agentów** w jednym pulpicie, automatycznie wykrywając każde środowisko uruchomieniowe na twojej maszynie:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw i NemoClaw są darmowe w otwartoźródłowej aplikacji; pozostałe środowiska uruchomieniowe uruchamiają się z ClawMetry Cloud lub licencją Pro do samodzielnego hostowania. Przełączaj środowiska uruchomieniowe w nagłówku, a każda zakładka — koszt, tokeny, narzędzia, ślady — dostosuje się do tego środowiska. Zobacz **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**, aby poznać dokładny podział darmowe/płatne, macierz poziomów, kształt `/api/entitlement` oraz CLI `clawmetry license`.

## Co otrzymujesz

- **Flow** — Żywy, animowany diagram pokazujący wiadomości przepływające przez kanały, mózg, narzędzia i z powrotem
- **Overview** — Kontrole stanu, mapa cieplna aktywności, liczba sesji, informacje o modelu
- **Usage** — Śledzenie tokenów i kosztów z podziałem dziennym/tygodniowym/miesięcznym
- **Sessions** — Aktywne sesje agenta z modelem, tokenami, ostatnią aktywnością
- **Crons** — Zaplanowane zadania ze statusem, następnym uruchomieniem, czasem trwania
- **Logs** — Kolorowe strumieniowanie logów w czasie rzeczywistym
- **Memory** — Przeglądanie SOUL.md, MEMORY.md, AGENTS.md, notatek dziennych
- **Transcripts** — Interfejs w formie dymków czatu do odczytu historii sesji
- **Alerts** — Limity budżetowe, wyzwalacze wskaźnika błędów, wykrywanie offline agenta; przekierowanie do Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Blokowanie destrukcyjnych usunięć, wymuszonych push'ów, mutacji baz danych, sudo, instalacji pakietów, połączeń sieciowych za pomocą jednokrotnej autoryzacji

## Zrzuty ekranu

### 🧠 Brain — Strumień zdarzeń agenta na żywo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Wykorzystanie tokenów i podsumowanie sesji
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Kanał wywołań narzędzi w czasie rzeczywistym
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Podział kosztów według modelu i sesji
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Przeglądarka plików obszaru roboczego
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Stan zabezpieczeń i dziennik audytu
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limity budżetowe, wyzwalacze wskaźnika błędów, webhooki do Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blokowanie ryzykownych wywołań narzędzi za ręczną autoryzacją; reguły ochrony oparte na polityce
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

Odmowa blokuje tylko to jedno wywołanie narzędzia — agent zachowuje swoją sesję i może
spróbować innego podejścia. Zatwierdzenie na telefonie pomija własny monit o uprawnienia Claude Code
(już na niego odpowiedziałeś). Niedopasowane narzędzia kosztują ~40ms i
trafiają do normalnego przepływu uprawnień Claude Code. Otrzymujesz również
powiadomienie push na telefon, gdy sam Claude Code czeka na twoją decyzję (powiadomienia
`permission_prompt` / `idle_prompt`).

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

Aplikacja React v2 znajduje się w `frontend/` i jest serwowana pod `/v2`, gdy
serwer Flask jest uruchomiony z włączoną wersją v2.

Podczas developmentu używaj dwóch terminali:

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
`http://localhost:8900`, dzięki czemu aplikacja React może komunikować się z lokalnym serwerem Flask
bez dodatkowej konfiguracji CORS.

Aby zbudować paczkę, która jest dostarczana z pakietem Python:

```bash
cd frontend
npm run build
```

Paczka produkcyjna jest zapisywana w `clawmetry/static/v2/dist/`.

## Kompatybilność środowisk uruchomieniowych / agentów

ClawMetry obserwuje wiele środowisk uruchomieniowych agentów AI, nie tylko OpenClaw. Każde środowisko inne niż OpenClaw wysyła dedykowany adapter odczytu, który tłumaczy natywny format sesji na ujednolicone kształty ClawMetry; demon pobiera je do tego samego magazynu DuckDB + migawki w chmurze, oznaczone środowiskiem uruchomieniowym, a zakładka odtwarzania sesji pokazuje **przełącznik środowiska uruchomieniowego**, gdy obecne jest więcej niż jedno. Zobacz [`docs/compatibility.md`](docs/compatibility.md), aby poznać pełną macierz + przewodnik dodawania środowisk uruchomieniowych, oraz [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) po wprowadzenie do rodziny OpenClaw.

Używasz narzędzia bezpieczeństwa agentów [numbat firmy Perplexity](https://github.com/perplexityai/numbat)? ClawMetry od razu obsługuje jego wyniki i decyzje egzekwowania — zobacz [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Środowisko / Agent | Status | Uwagi |
|---|---|---|
| **OpenClaw** | Natywne | Referencyjne środowisko uruchomieniowe, wykrywane automatycznie |
| **PicoClaw** | Adapter beta | Płaski JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Transkrypcje, model, wywołania narzędzi. |
| **NanoClaw** | Adapter beta | SQLite na sesję (`data/v2-sessions`). Transkrypcje + liczba wiadomości. |
| **Hermes** | Adapter beta | SQLite `~/.hermes/state.db`. Transkrypcje, model, tokeny/koszt. |
| **Claude Code** | Adapter beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkrypcje, model, wywołania narzędzi + myślenie, wykorzystanie tokenów. |
| **Codex** | Adapter beta | Rollout JSONL `~/.codex/sessions/...`. Transkrypcje, model, wywołania narzędzi, wykorzystanie tokenów. |
| **Cursor** | Adapter beta | SQLite `state.vscdb`. Transkrypcje czatu/kompozytora, model. |
| **Aider** | Adapter beta | `.aider.chat.history.md` na projekt. Transkrypcje, model, liczba tokenów. |
| **Goose** | Adapter beta | SQLite `~/.local/share/goose`. Transkrypcje, model, wywołania narzędzi, sumy tokenów. |
| **opencode** | Adapter beta | SQLite `~/.local/share/opencode`. Transkrypcje, model, wywołania narzędzi, tokeny + koszt. |
| **Qwen Code** | Adapter beta | JSONL `~/.qwen/projects/.../chats`. Transkrypcje, model, wywołania narzędzi, wykorzystanie tokenów. |
| **Pi** | Adapter beta | JSONL `~/.pi/agent/sessions`. Transkrypcje, model, wywołania narzędzi, tokeny + koszt. |
| **Deep Agents** | Adapter beta | SQLite `~/.deepagents/.state/sessions.db`. Transkrypcje, model, wywołania narzędzi, tokeny + koszt. |
| **n8n** | Adapter beta | SQLite `~/.n8n/database.sqlite`. Wykonania przepływów pracy, uruchomienia węzłów, prompty AI Agent, model + tokeny tam, gdzie n8n je rejestruje. |
| **Antigravity** | Adapter beta | Brain JSONL pod `~/.gemini/<flavor>/brain/`. Konwersacje, kroki narzędzi, myślenie, podział tokenów Gemini na generację + koszt, zużycie generacji w tle. |
| **GitHub Copilot** | Adapter beta | Copilot CLI `events.jsonl` pod `~/.copilot/session-state/` + rejestr wykorzystania na wywołanie `session-store.db`. Konwersacje, wywołania narzędzi, routing modelu, podział tokenów z uwzględnieniem cache, koszt kredytów AI rozliczanych przez dostawcę. |
| **Grok** | Adapter beta | xAI Grok Build CLI (binarka Rust pod `~/.grok/bin/grok`): globalny dziennik zdarzeń `~/.grok/logs/unified.jsonl` + `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}` na sesję. Konwersacje, podział tokenów na turę, routing modelu oraz wychodzący ładunek repozytorium CLI umieszczany w `~/.grok/upload_queue/`, dzięki czemu widać, co opuściło twoją maszynę. |

"Adapter beta" oznacza, że ClawMetry dostarcza czytnik dla rzeczywistego formatu dyskowego danego środowiska uruchomieniowego, każdy zbudowany i zweryfikowany na rzeczywistej instalacji na rzeczywistej maszynie (zobacz `tests/fixtures/runtimes/<rt>/`). Adaptery są tylko do odczytu; każdy jest szczery co do tego, co dane środowisko faktycznie przechowuje (np. PicoClaw/NanoClaw/Cursor nie zapisują kosztu tokenów na dysku). Gdy na jednym węźle działa kilka środowisk uruchomieniowych, przełącznik środowiska ogranicza widok sesji do jednego, aby umożliwić dokładną analizę.

## Śledzenie dowolnego agenta SDK — atrybucja kosztów spoza pętli

Powyższe środowiska uruchomieniowe zapisują sesje na dysku. Twój własny **produkcyjny agent** — zbudowany na OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B lub zwykłej pętli `httpx` — tego nie robi. Interceptor ClawMetry działający bez konfiguracji nadal przechwytuje jego wywołania LLM (koszt, tokeny, opóźnienie, błędy), łatając na bieżąco `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (lub zmienna środowiskowa `CLAWMETRY_SOURCE=support-agent`) oznacza każde wywołanie **nazwanym źródłem**, dzięki czemu każdy uruchamiany przez ciebie produkt pojawia się jako własna, w pełni atrybucyjna linia kosztowa na karcie **🔌 Źródła spoza pętli** w Overview na pulpicie — wywołania, dostawcy, opóźnienie, wskaźnik błędów na agenta. Nie ustawiono źródła? Wywołania i tak są śledzone; karta po prostu pozostaje ukryta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

To ta sama warstwa danych, którą zasilają adaptery środowisk uruchomieniowych (DuckDB → migawka w chmurze), więc źródła spoza pętli synchronizują się z pulpitem w chmurze tak samo jak wszystko inne, w pełni szyfrowane end-to-end.

## OpenTelemetry — neutralne wobec dostawcy, wysyłaj swoje ślady gdziekolwiek

ClawMetry mówi w obu kierunkach w standardzie **OpenTelemetry**, wykorzystując **konwencje semantyczne GenAI**, dzięki czemu ślady twojego agenta nigdy nie są zablokowane w jednym narzędziu.

**Eksportuj** każdą sesję — wywołania LLM, narzędzia, subagentów, tokeny, koszt — jako ślady OTLP/HTTP GenAI do dowolnego kolektora (Datadog, Grafana, Honeycomb lub własny OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Nagłówki autoryzacyjne i interwał odpytywania to opcjonalne zmienne środowiskowe:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Pobieraj** — wbudowany odbiornik OTLP przyjmuje ślady i metryki z dowolnego innego źródła pod `/v1/traces` i `/v1/metrics` (`pip install clawmetry[otel]` dla przyjmowania protobuf).

Otrzymujesz zarówno pulpit ClawMetry działający bez konfiguracji, lokalnie od podstaw, **jak i** swoje dane w dowolnym backendzie, którego już używa twój zespół — bez blokady dostawcy, bez konieczności instalowania drugiego agenta.

## Konfiguracja

Większość osób nie potrzebuje żadnej konfiguracji. ClawMetry automatycznie wykrywa twój obszar roboczy, logi, sesje i zadania cron.

Jeśli jednak chcesz coś dostosować:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Wszystkie opcje: `clawmetry --help`

## Obsługiwane kanały

ClawMetry pokazuje aktywność na żywo dla każdego skonfigurowanego przez ciebie kanału OpenClaw. Na diagramie Flow pojawiają się tylko kanały faktycznie skonfigurowane w twoim `openclaw.json` — nieskonfigurowane są automatycznie ukrywane.

Kliknij dowolny węzeł kanału na diagramie Flow, aby zobaczyć widok dymków czatu na żywo z liczbą przychodzących/wychodzących wiadomości.

| Kanał | Status | Podgląd na żywo | Uwagi |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Pełny | ✅ | Wiadomości, statystyki, odświeżanie co 10s |
| 💬 **iMessage** | ✅ Pełny | ✅ | Odczytuje bezpośrednio `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Pełny | ✅ | Przez WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Pełny | ✅ | Przez signal-cli |
| 🟣 **Discord** | ✅ Pełny | ✅ | Wykrywanie serwera + kanału |
| 🟪 **Slack** | ✅ Pełny | ✅ | Wykrywanie przestrzeni roboczej + kanału |
| 🌐 **Webchat** | ✅ Pełny | ✅ | Sesje wbudowanego interfejsu webowego |
| 📡 **IRC** | ✅ Pełny | ✅ | Interfejs dymków w stylu terminala |
| 🍏 **BlueBubbles** | ✅ Pełny | ✅ | iMessage przez REST API BlueBubbles |
| 🔵 **Google Chat** | ✅ Pełny | ✅ | Przez webhooki Chat API |
| 🟣 **MS Teams** | ✅ Pełny | ✅ | Przez wtyczkę bota Teams |
| 🔷 **Mattermost** | ✅ Pełny | ✅ | Samodzielnie hostowany czat zespołowy |
| 🟩 **Matrix** | ✅ Pełny | ✅ | Zdecentralizowany, obsługa E2EE |
| 🟢 **LINE** | ✅ Pełny | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Pełny | ✅ | Zdecentralizowane wiadomości prywatne NIP-04 |
| 🟣 **Twitch** | ✅ Pełny | ✅ | Czat przez połączenie IRC |
| 🔷 **Feishu/Lark** | ✅ Pełny | ✅ | Subskrypcja zdarzeń WebSocket |
| 🔵 **Zalo** | ✅ Pełny | ✅ | Zalo Bot API |

> **Automatyczne wykrywanie:** ClawMetry odczytuje twój `~/.openclaw/openclaw.json` i renderuje wyłącznie kanały, które faktycznie skonfigurowałeś. Ręczna konfiguracja nie jest wymagana.

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

> **Uwaga:** Podczas uruchamiania w Dockerze zamontuj katalogi danych + logów swojego agenta (np. `~/.openclaw`, `~/.claude`, `~/.codex`), aby ClawMetry mogło automatycznie wykryć twoją konfigurację.

## Wymagania

- Python 3.8+
- Flask (instalowany automatycznie przez pip)
- Środowisko uruchomieniowe agenta AI na tej samej maszynie: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok lub QM (albo zamontowane woluminy dla Dockera)
- Linux lub macOS

## Obsługa NemoClaw / OpenShell

ClawMetry automatycznie wykrywa [NemoClaw](https://github.com/NVIDIA/NemoClaw) — korporacyjną osłonę bezpieczeństwa NVIDIA dla OpenClaw, która uruchamia agentów wewnątrz izolowanych kontenerów OpenShell.

W większości przypadków nie jest wymagana dodatkowa konfiguracja. Demon synchronizacji automatycznie wykrywa pliki sesji, niezależnie od tego, czy znajdują się w `~/.openclaw/` na hoście, czy wewnątrz kontenera OpenShell.

### Jak to działa

ClawMetry wykrywa NemoClaw na dwa sposoby:

1. **Wykrywanie binarki** — sprawdza obecność CLI `nemoclaw` i uruchamia `nemoclaw status`, aby uzyskać informacje o piaskownicy
2. **Wykrywanie kontenera** — skanuje uruchomione kontenery Docker w poszukiwaniu obrazów `openshell`, `nemoclaw` lub `ghcr.io/nvidia/`, a następnie odczytuje sesje przez zamontowane woluminy lub `docker cp`

Pliki sesji zsynchronizowane z kontenerów NemoClaw są oznaczane metadanymi `runtime=nemoclaw` i `container_id` w pulpicie chmurowym, dzięki czemu można je na pierwszy rzut oka odróżnić od standardowych sesji OpenClaw.

### Zalecana konfiguracja: demon synchronizacji na HOŚCIE

Dla najlepszego doświadczenia uruchom demona synchronizacji ClawMetry na **maszynie hosta** (nie wewnątrz piaskownicy). Pozwala to uniknąć ograniczeń polityki sieciowej NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Demon synchronizacji automatycznie znajdzie sesje wewnątrz każdego uruchomionego kontenera OpenShell.

### Opcjonalnie: jawna nazwa piaskownicy

Jeśli automatyczne wykrywanie nie działa, wskaż ClawMetry właściwą piaskownicę:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Uruchamianie wewnątrz piaskownicy (zaawansowane)

Jeśli musisz uruchomić demona synchronizacji **wewnątrz** piaskownicy OpenShell, dodaj tę regułę ruchu wychodzącego do swojej polityki sieciowej NemoClaw, aby mógł dotrzeć do API przyjmowania danych ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Zastosuj poleceniem:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Porty i punkty końcowe

| Punkt końcowy | Port | Protokół | Wymagane |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Tak (demon synchronizacji → chmura) |
| `localhost:8900` | 8900 | HTTP | Tak (lokalny interfejs pulpitu) |
| Gniazdo Docker (`/var/run/docker.sock`) | — | Gniazdo Unix | Do wykrywania sesji w kontenerach |

Demon synchronizacji wykonuje wyłącznie wychodzące połączenia HTTPS do `ingest.clawmetry.com`. Żadne porty przychodzące nie są wymagane.

---

## Wdrożenie w chmurze

Zobacz **[Przewodnik testowania w chmurze](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** dotyczący tuneli SSH, reverse proxy i Dockera.

## Testowanie

Ten projekt jest testowany za pomocą BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

ClawMetry wysyła anonimowe sygnały cyklu życia instalacji do
`https://app.clawmetry.com/api/install`: jeden sygnał `install` przy pierwszym
uruchomieniu CLI `clawmetry` na nowej maszynie, jeden sygnał `update`
przy pierwszym uruchomieniu po aktualizacji do nowej wersji oraz jeden sygnał
`onboarded`, gdy ukończysz wybór wdrożenia w pulpicie. Wykorzystujemy to
do liczenia rzeczywistych instalacji (surowe liczby pobrań z PyPI to w ~98% mirrory, CI
i ponowne pobrania przy automatycznej aktualizacji) oraz aby dowiedzieć się, które frameworki agentów i
wersje są faktycznie w użyciu.

**Maksymalnie jeden POST na zdarzenie cyklu życia na wersję**, zawierający:

| Pole | Przykład | Dlaczego |
|---|---|---|
| `install_id` | losowy UUID zapisany w `~/.clawmetry/install_id` | deduplikacja; anonimowe, dopóki jawnie nie połączysz synchronizacji z Chmurą (uwierzytelniony sygnał demona przenosi wtedy tę wartość, łącząc tę instalację z twoim kontem) |
| `event` | `install` / `update` / `onboarded` | świeża instalacja vs aktualizacja istniejącej |
| `version` | `0.12.167` | jakie wersje są w użyciu |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorytety wsparcia platform |
| `python` | `3.11.15` | macierz wsparcia wersji Pythona |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | z jakimi agentami powinniśmy zintegrować się dalej |
| `is_ci` / `ci_provider` | `true` / `github_actions` | oddzielenie instalacji ludzkich od szumu CI |

**Czego NIE wysyłamy**: adresu IP (chmura wyznacza kod kraju po stronie serwera
na podstawie żądania, a następnie odrzuca IP), nazwy hosta, nazwy użytkownika, ścieżki obszaru
roboczego, zawartości plików, twojego api_key, twojego adresu e-mail, niczego, co jest PII lub
specyficzne dla obszaru roboczego. Ładunek transmisji można sprawdzić w pliku
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Rezygnacja** (dowolna z poniższych opcji wyłącza to trwale):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Awaria sieci nigdy nie blokuje uruchomienia `clawmetry` — sygnał jest wysyłany
w trybie fire-and-forget w wątku demona z limitem czasu 3 s.

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
