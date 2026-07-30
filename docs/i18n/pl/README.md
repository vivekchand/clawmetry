<!-- i18n-src:9a05336fbdc1 -->
> Polski translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Zobacz, jak myśli twój agent.** Obserwowalność w czasie rzeczywistym dla **14 środowisk uruchomieniowych agentów AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex i 10 innych. Jeden dashboard dla całej twojej floty agentów.

> 🌐 **Czytaj w innych językach:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [więcej →](docs/i18n/)

Jedna komenda. Zero konfiguracji. Wykrywa wszystko automatycznie.

```bash
pip install clawmetry && clawmetry
```

Otwiera się pod adresem **http://localhost:8900** i to wszystko.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Działa z 14 środowiskami uruchomieniowymi agentów

ClawMetry zaczęło jako narzędzie do obserwowalności OpenClaw, a teraz mierzy **całą twoją flotę agentów** w jednym dashboardzie, automatycznie wykrywając każde środowisko uruchomieniowe na twojej maszynie:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw i NemoClaw są darmowe w aplikacji open source; pozostałe środowiska uruchomieniowe odblokowują się dzięki ClawMetry Cloud lub licencji Pro w wersji self-hosted. Przełącz środowiska uruchomieniowe z poziomu nagłówka, a każda karta — koszty, tokeny, narzędzia, ślady (traces) — ponownie dopasuje zakres do tego środowiska. Zobacz **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**, aby poznać dokładny podział darmowe/płatne, macierz poziomów, kształt `/api/entitlement` oraz CLI `clawmetry license`.

## Co otrzymujesz

- **Flow** — Animowany diagram na żywo pokazujący wiadomości przepływające przez kanały, mózg (brain), narzędzia i z powrotem
- **Overview** — Kontrole stanu, mapa cieplna aktywności, liczba sesji, informacje o modelu
- **Usage** — Śledzenie tokenów i kosztów z podziałem dziennym/tygodniowym/miesięcznym
- **Sessions** — Aktywne sesje agenta z modelem, tokenami, ostatnią aktywnością
- **Crons** — Zaplanowane zadania ze statusem, następnym uruchomieniem, czasem trwania
- **Logs** — Kolorowe strumieniowanie logów w czasie rzeczywistym
- **Memory** — Przeglądanie plików SOUL.md, MEMORY.md, AGENTS.md, notatek dziennych
- **Transcripts** — Interfejs dymków czatu do czytania historii sesji
- **Alerts** — Limity budżetowe, wyzwalacze wskaźnika błędów, wykrywanie offline agenta; kierowanie do Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Blokowanie niszczących usunięć, wymuszonych pushy, mutacji baz danych, sudo, instalacji pakietów, połączeń sieciowych za jednym kliknięciem zatwierdzenia

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

### ✋ Approvals — Blokowanie ryzykownych wywołań narzędzi za ręcznym zatwierdzeniem; reguły ochrony oparte na polityce
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Blokowanie przed wykonaniem dla Claude Code** — jedna komenda instaluje
hook PreToolUse, który wstrzymuje pasujące wywołania narzędzi *zanim* zostaną uruchomione i czeka
na twoją decyzję (jedno dotknięcie z telefonu przy włączonych
[powiadomieniach push w chmurze](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Odmowa blokuje tylko to jedno wywołanie narzędzia — agent zachowuje swoją sesję i może
spróbować innego podejścia. Zatwierdzenie na telefonie pomija własny
monit uprawnień Claude Code (już na niego odpowiedziałeś). Niedopasowane narzędzia kosztują ~40 ms i
przechodzą do normalnego przepływu uprawnień Claude Code. Otrzymasz też powiadomienie push na telefon, gdy
sam Claude Code czeka na ciebie (powiadomienia `permission_prompt` /
`idle_prompt`).

## Instalacja

**Jedna linijka (zalecane):**
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
# Terminal 1: Flask API/server na :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: serwer deweloperski Vite na :5173
cd frontend
nvm use
npm ci
npm run dev
```

Otwórz `http://localhost:5173/v2/`. Vite przekazuje żądania `/api` do
`http://localhost:8900`, dzięki czemu aplikacja React może komunikować się z lokalnym serwerem Flask
bez dodatkowej konfiguracji CORS.

Aby zbudować paczkę dołączaną do pakietu Python:

```bash
cd frontend
npm run build
```

Paczka produkcyjna zapisywana jest w `clawmetry/static/v2/dist/`.

## Zgodność środowisk uruchomieniowych / agentów

ClawMetry obserwuje wiele środowisk uruchomieniowych agentów AI, nie tylko OpenClaw. Każde środowisko inne niż OpenClaw ma dedykowany adapter odczytu, który tłumaczy jego natywny format sesji na ujednolicone kształty ClawMetry; demon wczytuje je do tego samego magazynu DuckDB i migawki w chmurze, oznaczone środowiskiem uruchomieniowym, a karta powtórki sesji pokazuje **przełącznik środowiska** gdy obecne jest więcej niż jedno. Zobacz [`docs/compatibility.md`](docs/compatibility.md) po pełną macierz i przewodnik dodawania środowisk oraz [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) po wprowadzenie do rodziny OpenClaw.

| Środowisko / Agent | Status | Uwagi |
|---|---|---|
| **OpenClaw** | Natywne | Środowisko referencyjne, wykrywane automatycznie |
| **PicoClaw** | Adapter beta | Płaski JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Transkrypcje, model, wywołania narzędzi. |
| **NanoClaw** | Adapter beta | SQLite per sesja (`data/v2-sessions`). Transkrypcje + liczba wiadomości. |
| **Hermes** | Adapter beta | SQLite `~/.hermes/state.db`. Transkrypcje, model, tokeny/koszt. |
| **Claude Code** | Adapter beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkrypcje, model, wywołania narzędzi + myślenie, zużycie tokenów. |
| **Codex** | Adapter beta | Rollout JSONL `~/.codex/sessions/...`. Transkrypcje, model, wywołania narzędzi, zużycie tokenów. |
| **Cursor** | Adapter beta | SQLite `state.vscdb`. Transkrypcje czatu/kompozytora, model. |
| **Aider** | Adapter beta | `.aider.chat.history.md` per projekt. Transkrypcje, model, liczba tokenów. |
| **Goose** | Adapter beta | SQLite `~/.local/share/goose`. Transkrypcje, model, wywołania narzędzi, sumy tokenów. |
| **opencode** | Adapter beta | SQLite `~/.local/share/opencode`. Transkrypcje, model, wywołania narzędzi, tokeny + koszt. |
| **Qwen Code** | Adapter beta | JSONL `~/.qwen/projects/.../chats`. Transkrypcje, model, wywołania narzędzi, zużycie tokenów. |
| **Pi** | Adapter beta | JSONL `~/.pi/agent/sessions`. Transkrypcje, model, wywołania narzędzi, tokeny + koszt. |
| **Deep Agents** | Adapter beta | SQLite `~/.deepagents/.state/sessions.db`. Transkrypcje, model, wywołania narzędzi, tokeny + koszt. |
| **n8n** | Adapter beta | SQLite `~/.n8n/database.sqlite`. Wykonania przepływów pracy, uruchomienia węzłów, podpowiedzi AI Agent, model + tokeny tam, gdzie n8n je rejestruje. |

„Adapter beta" oznacza, że ClawMetry dostarcza czytnik dla rzeczywistego formatu na dysku danego środowiska, każdy zbudowany i zweryfikowany na prawdziwej instalacji na prawdziwej maszynie (zobacz `tests/fixtures/runtimes/<rt>/`). Adaptery są tylko do odczytu; każdy jest szczery co do tego, co dane środowisko faktycznie przechowuje (np. PicoClaw/NanoClaw/Cursor nie zapisują kosztu tokenów na dysk). Gdy na jednym węźle działa kilka środowisk, przełącznik środowiska zawęża widok sesji do jednego, dla czystego, dogłębnego przeglądu.

## Śledzenie dowolnego agenta SDK — atrybucja kosztów poza pętlą

Powyższe środowiska uruchomieniowe zapisują sesje na dysk. Twój własny **agent produkcyjny** — ten zbudowany na OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, lub na zwykłej pętli `httpx` — tego nie robi. Interceptor ClawMetry z zerową konfiguracją nadal przechwytuje jego wywołania LLM (koszt, tokeny, opóźnienie, błędy), łatając w locie `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (lub zmienna środowiskowa `CLAWMETRY_SOURCE=support-agent`) oznacza każde wywołanie **nazwanym źródłem**, dzięki czemu każdy prowadzony przez ciebie produkt pojawia się jako własna, w pełni atrybutowalna kosztowo linia na karcie **🔌 Out-loop sources** w Overview — wywołania, dostawcy, opóźnienie, wskaźnik błędów per agent. Nie ustawiono źródła? Wywołania nadal są śledzone; karta po prostu pozostaje ukryta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

To ta sama warstwa danych, którą zasilają adaptery środowisk (DuckDB → migawka w chmurze), więc źródła poza pętlą synchronizują się z dashboardem w chmurze tak samo jak wszystko inne, w pełni szyfrowane end-to-end.

## OpenTelemetry — neutralne wobec dostawcy, wysyłaj swoje ślady gdziekolwiek

ClawMetry mówi **OpenTelemetry** w obu kierunkach, używając **konwencji semantycznych GenAI**, dzięki czemu ślady twojego agenta nigdy nie są zamknięte w jednym narzędziu.

**Eksportuj** każdą sesję — wywołania LLM, narzędzia, subagentów, tokeny, koszt — jako ślady OTLP/HTTP GenAI do dowolnego kolektora (Datadog, Grafana, Honeycomb, lub twój własny OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Nagłówki uwierzytelniające i interwał odpytywania są opcjonalnymi zmiennymi środowiskowymi:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Wczytuj** — wbudowany odbiornik OTLP przyjmuje ślady i metryki z czegokolwiek innego pod `/v1/traces` i `/v1/metrics` (`pip install clawmetry[otel]` dla odczytu protobuf).

Otrzymujesz zarówno lokalny dashboard ClawMetry z zerową konfiguracją, **jak i** swoje dane w dowolnym backendzie, którego już używa twój zespół — bez uzależnienia od dostawcy, bez instalowania drugiego agenta.

## Konfiguracja

Większość osób nie potrzebuje żadnej konfiguracji. ClawMetry automatycznie wykrywa twój obszar roboczy, logi, sesje i cron-y.

Jeśli jednak potrzebujesz dostosowania:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Wszystkie opcje: `clawmetry --help`

## Obsługiwane kanały

ClawMetry pokazuje aktywność na żywo dla każdego skonfigurowanego kanału OpenClaw. Na diagramie Flow pojawiają się tylko kanały faktycznie skonfigurowane w twoim `openclaw.json` — nieskonfigurowane są automatycznie ukrywane.

Kliknij dowolny węzeł kanału w Flow, aby zobaczyć widok dymków czatu na żywo z licznikami wiadomości przychodzących/wychodzących.

| Kanał | Status | Popup na żywo | Uwagi |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Pełne | ✅ | Wiadomości, statystyki, odświeżanie co 10 s |
| 💬 **iMessage** | ✅ Pełne | ✅ | Odczytuje bezpośrednio `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ Pełne | ✅ | Przez WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Pełne | ✅ | Przez signal-cli |
| 🟣 **Discord** | ✅ Pełne | ✅ | Wykrywanie serwera i kanału |
| 🟪 **Slack** | ✅ Pełne | ✅ | Wykrywanie obszaru roboczego i kanału |
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
| 🔷 **Feishu/Lark** | ✅ Pełne | ✅ | Subskrypcja zdarzeń przez WebSocket |
| 🔵 **Zalo** | ✅ Pełne | ✅ | Zalo Bot API |

> **Automatyczne wykrywanie:** ClawMetry odczytuje twój plik `~/.openclaw/openclaw.json` i renderuje tylko kanały, które faktycznie skonfigurowałeś. Ręczna konfiguracja nie jest wymagana.

## Wdrożenie w Docker

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

> **Uwaga:** Podczas uruchamiania w Dockerze zamontuj katalogi danych i logów swojego agenta (np. `~/.openclaw`, `~/.claude`, `~/.codex`), aby ClawMetry mogło automatycznie wykryć twoją konfigurację.

## Wymagania

- Python 3.8+
- Flask (instalowany automatycznie przez pip)
- Środowisko uruchomieniowe agenta AI na tej samej maszynie: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents lub n8n (lub zamontowane woluminy dla Dockera)
- Linux lub macOS

## Wsparcie dla NemoClaw / OpenShell

ClawMetry automatycznie wykrywa [NemoClaw](https://github.com/NVIDIA/NemoClaw) — korporacyjną nakładkę bezpieczeństwa NVIDIA dla OpenClaw, uruchamiającą agentów wewnątrz odizolowanych kontenerów OpenShell.

W większości przypadków nie jest wymagana dodatkowa konfiguracja. Demon synchronizacji automatycznie odkrywa pliki sesji, niezależnie od tego, czy znajdują się w `~/.openclaw/` na hoście, czy wewnątrz kontenera OpenShell.

### Jak to działa

ClawMetry wykrywa NemoClaw na dwa sposoby:

1. **Wykrywanie binarne** — sprawdza obecność CLI `nemoclaw` i uruchamia `nemoclaw status`, aby uzyskać informacje o sandboxie
2. **Wykrywanie kontenera** — skanuje uruchomione kontenery Docker w poszukiwaniu obrazów `openshell`, `nemoclaw` lub `ghcr.io/nvidia/`, a następnie odczytuje sesje przez zamontowane woluminy lub `docker cp`

Pliki sesji zsynchronizowane z kontenerów NemoClaw są oznaczane metadanymi `runtime=nemoclaw` i `container_id` w dashboardzie chmurowym, dzięki czemu można je łatwo odróżnić od standardowych sesji OpenClaw na pierwszy rzut oka.

### Zalecana konfiguracja: demon synchronizacji na HOŚCIE

Dla najlepszego doświadczenia uruchom demon synchronizacji ClawMetry na **maszynie hosta** (nie wewnątrz sandboxa). Pozwala to uniknąć ograniczeń polityki sieciowej NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Demon synchronizacji automatycznie znajdzie sesje wewnątrz dowolnych uruchomionych kontenerów OpenShell.

### Opcjonalnie: jawna nazwa sandboxa

Jeśli automatyczne wykrywanie nie działa, wskaż ClawMetry właściwy sandbox:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Uruchamianie wewnątrz sandboxa (zaawansowane)

Jeśli musisz uruchomić demon synchronizacji **wewnątrz** sandboxa OpenShell, dodaj tę regułę ruchu wychodzącego do swojej polityki sieciowej NemoClaw, aby mógł dotrzeć do API ingestu ClawMetry:

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

| Punkt końcowy | Port | Protokół | Wymagany |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Tak (demon synchronizacji → chmura) |
| `localhost:8900` | 8900 | HTTP | Tak (lokalny interfejs dashboardu) |
| Gniazdo Dockera (`/var/run/docker.sock`) | — | Gniazdo Unix | Do wykrywania sesji w kontenerach |

Demon synchronizacji wykonuje wyłącznie wychodzące połączenia HTTPS do `ingest.clawmetry.com`. Żadne porty przychodzące nie są wymagane.

---

## Wdrożenie w chmurze

Zobacz **[Przewodnik testowania w chmurze](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** dotyczący tuneli SSH, reverse proxy i Dockera.

## Testowanie

Ten projekt jest testowany za pomocą BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

ClawMetry wysyła pojedynczy anonimowy ping „pierwszego uruchomienia" do
`https://app.clawmetry.com/api/install` przy pierwszym uruchomieniu CLI
`clawmetry` na nowej maszynie. Wykorzystujemy to do liczenia instalacji (jedyna
metryka marketingowa, jaką mamy dla projektu OSS) oraz do poznania, jakie
środowiska agentów mają zainstalowane nasi użytkownicy.

**Dokładnie jeden POST na instalację**, zawierający:

| Pole | Przykład | Dlaczego |
|---|---|---|
| `install_id` | losowy UUID przechowywany w `~/.clawmetry/install_id` | deduplikacja; niepowiązany z twoim e-mailem ani api_key |
| `version` | `0.12.167` | jakie wersje są w użyciu |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorytety wsparcia platform |
| `python` | `3.11.15` | macierz wsparcia wersji Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | z jakimi agentami powinniśmy integrować się dalej |
| `is_ci` / `ci_provider` | `true` / `github_actions` | oddzielenie instalacji ludzkich od szumu CI |

**Czego NIE wysyłamy**: adresu IP (chmura wyprowadza kod kraju po stronie
serwera z żądania, a następnie odrzuca IP), nazwy hosta, nazwy użytkownika,
ścieżki obszaru roboczego, zawartości plików, twojego api_key, twojego e-maila,
niczego, co jest PII lub specyficzne dla obszaru roboczego. Payload
przesyłany jest w pełni jawny do audytu w
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Rezygnacja** (dowolne z poniższych wyłącza ją na stałe):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Awaria sieci nigdy nie blokuje uruchomienia `clawmetry` — ping działa
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
