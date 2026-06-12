<!-- i18n-src:48548997be76 -->
> Polski translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Obserwuj, jak myśli Twój agent.** Obserwowalność w czasie rzeczywistym dla **12 środowisk uruchomieniowych agentów AI**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex i 8 innych. Jeden pulpit nawigacyjny dla całej floty agentów.

> 🌐 **Przeczytaj w:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [więcej →](docs/i18n/)

Jedno polecenie. Zero konfiguracji. Automatyczne wykrywanie wszystkiego.

```bash
pip install clawmetry && clawmetry
```

Otwiera się pod adresem **http://localhost:8900** i gotowe.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Współpraca z 12 środowiskami uruchomieniowymi agentów

ClawMetry powstał jako narzędzie do obserwacji OpenClaw, a teraz mierzy **całą Twoją flotę agentów** w jednym pulpicie nawigacyjnym, automatycznie wykrywając każde środowisko uruchomieniowe na Twoim komputerze:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw i NemoClaw są bezpłatne w aplikacji open-source; pozostałe środowiska uruchomieniowe są dostępne z ClawMetry Cloud lub samodzielnie hostowaną licencją Pro. Przełącz środowisko uruchomieniowe z nagłówka, a każda zakładka — koszty, tokeny, narzędzia, ślady — zmieni zakres do wybranego środowiska.

## Co Otrzymujesz

- **Flow** — Animowany diagram na żywo pokazujący przepływ wiadomości przez kanały, mózg, narzędzia i z powrotem
- **Overview** — Sprawdzanie kondycji, mapa aktywności, liczba sesji, informacje o modelu
- **Usage** — Śledzenie tokenów i kosztów z podziałem na dzień/tydzień/miesiąc
- **Sessions** — Aktywne sesje agenta z modelem, tokenami i ostatnią aktywnością
- **Crons** — Zaplanowane zadania ze statusem, kolejnym uruchomieniem i czasem trwania
- **Logs** — Kolorowe strumieniowanie logów w czasie rzeczywistym
- **Memory** — Przeglądanie plików SOUL.md, MEMORY.md, AGENTS.md i notatek dziennych
- **Transcripts** — Interfejs dymków czatu do czytania historii sesji
- **Alerts** — Limity budżetu, wyzwalacze częstości błędów, wykrywanie offline agenta; przekierowanie do Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Blokowanie destrukcyjnych usunięć, wymuszeń push, mutacji bazy danych, sudo, instalacji pakietów i wywołań sieciowych za pomocą jednego kliknięcia

## Zrzuty ekranu

### 🧠 Brain — Strumień zdarzeń agenta na żywo
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Użycie tokenów i podsumowanie sesji
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Kanał wywołań narzędzi w czasie rzeczywistym
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Podział kosztów według modelu i sesji
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Przeglądarka plików obszaru roboczego
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Poziom bezpieczeństwa i dziennik audytu
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Limity budżetu, wyzwalacze częstości błędów, webhooki do Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Blokowanie ryzykownych wywołań narzędzi za pomocą ręcznego zatwierdzenia; reguły ochrony oparte na zasadach
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Instalacja

**Jednolinijkowe polecenie (zalecane):**
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

Aplikacja React v2 znajduje się w katalogu `frontend/` i jest serwowana pod adresem `/v2` po uruchomieniu serwera Flask z włączoną obsługą v2.

Podczas programowania używaj dwóch terminali:

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

Otwórz `http://localhost:5173/v2/`. Vite przekierowuje żądania `/api` do `http://localhost:8900`, dzięki czemu aplikacja React może komunikować się z lokalnym serwerem Flask bez dodatkowej konfiguracji CORS.

Aby zbudować pakiet dołączany do pakietu Python:

```bash
cd frontend
npm run build
```

Pakiet produkcyjny jest zapisywany w katalogu `clawmetry/static/v2/dist/`.

## Zgodność środowisk uruchomieniowych / agentów

ClawMetry obserwuje wiele środowisk uruchomieniowych agentów AI, nie tylko OpenClaw. Każde środowisko inne niż OpenClaw ma dedykowany adapter odczytujący, który tłumaczy jego natywny format sesji na ujednolicone kształty ClawMetry; demon wczytuje je do tego samego sklepu DuckDB i migawki chmury, oznaczonych środowiskiem uruchomieniowym, a zakładka odtwarzania sesji pokazuje **przełącznik środowiska uruchomieniowego**, gdy jest ich więcej niż jedno. Pełna macierz i przewodnik dodawania środowisk uruchomieniowych znajdują się w [`docs/compatibility.md`](docs/compatibility.md), a wprowadzenie do rodziny OpenClaw w [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md).

| Środowisko / Agent | Status | Uwagi |
|---|---|---|
| **OpenClaw** | Natywne | Referencyjne środowisko uruchomieniowe, automatycznie wykrywane |
| **PicoClaw** | Adapter beta | Płaski JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Transkrypcje, model, wywołania narzędzi. |
| **NanoClaw** | Adapter beta | SQLite per sesja (`data/v2-sessions`). Transkrypcje + liczba wiadomości. |
| **Hermes** | Adapter beta | SQLite `~/.hermes/state.db`. Transkrypcje, model, tokeny/koszt. |
| **Claude Code** | Adapter beta | JSONL `~/.claude/projects/.../<id>.jsonl`. Transkrypcje, model, wywołania narzędzi + myślenie, użycie tokenów. |
| **Codex** | Adapter beta | Rollout JSONL `~/.codex/sessions/...`. Transkrypcje, model, wywołania narzędzi, użycie tokenów. |
| **Cursor** | Adapter beta | SQLite `state.vscdb`. Transkrypcje czatu/kompozytora, model. |
| **Aider** | Adapter beta | `.aider.chat.history.md` per projekt. Transkrypcje, model, liczba tokenów. |
| **Goose** | Adapter beta | SQLite `~/.local/share/goose`. Transkrypcje, model, wywołania narzędzi, łączna liczba tokenów. |
| **opencode** | Adapter beta | SQLite `~/.local/share/opencode`. Transkrypcje, model, wywołania narzędzi, tokeny + koszt. |
| **Qwen Code** | Adapter beta | JSONL `~/.qwen/projects/.../chats`. Transkrypcje, model, wywołania narzędzi, użycie tokenów. |

"Adapter beta" oznacza, że ClawMetry dostarcza czytnik dla rzeczywistego formatu dyskowego danego środowiska uruchomieniowego, zbudowany i zweryfikowany na prawdziwej instalacji na prawdziwej maszynie (patrz `tests/fixtures/runtimes/<rt>/`). Adaptery są tylko do odczytu; każdy jest uczciwy w kwestii tego, co jego środowisko uruchomieniowe faktycznie przechowuje (np. PicoClaw/NanoClaw/Cursor nie zapisują kosztu tokenów na dysku). Gdy kilka środowisk uruchomieniowych działa na jednym węźle, przełącznik środowisk uruchomieniowych ogranicza widok sesji do jednego, umożliwiając przejrzyste zagłębienie się w szczegóły.

## Śledzenie dowolnego agenta SDK — przypisywanie kosztów poza pętlą

Powyższe środowiska uruchomieniowe zapisują sesje na dysku. Twój własny **agent produkcyjny** — zbudowany na OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B lub zwykłej pętli `httpx` — tego nie robi. Interceptor zero-config ClawMetry nadal przechwytuje jego wywołania LLM (koszt, tokeny, opóźnienie, błędy) przez małpie łatanie `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (lub zmienna środowiskowa `CLAWMETRY_SOURCE=support-agent`) oznacza każde wywołanie **nazwanym źródłem**, dzięki czemu każdy uruchamiany przez Ciebie produkt pojawia się jako własna, pierwszorzędna linia z przypisanymi kosztami w karcie **🔌 Źródła poza pętlą** na zakładce Overview — wywołania, dostawcy, opóźnienie, wskaźnik błędów per agent. Brak ustawionego źródła? Wywołania są nadal śledzone; karta pozostaje po prostu ukryta.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Jest to ta sama warstwa danych, którą zasilają adaptery środowisk uruchomieniowych (DuckDB i migawka chmury), więc źródła poza pętlą synchronizują się z pulpitem chmury tak samo jak wszystko inne, z szyfrowaniem end-to-end.

## OpenTelemetry — niezależny od dostawcy, wysyłaj ślady gdziekolwiek chcesz

ClawMetry obsługuje OpenTelemetry w obu kierunkach, używając **konwencji semantycznych GenAI**, dzięki czemu ślady Twojego agenta nigdy nie są uzależnione od jednego narzędzia.

**Eksportuj** każdą sesję — wywołania LLM, narzędzia, pod-agenty, tokeny, koszt — jako zakresy GenAI OTLP/HTTP do dowolnego kolektora (Datadog, Grafana, Honeycomb lub Twój własny OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Nagłówki uwierzytelniania i interwał odpytywania to opcjonalne zmienne środowiskowe:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Wczytywanie** — wbudowany odbiornik OTLP przyjmuje ślady i metryki z dowolnego źródła pod adresami `/v1/traces` i `/v1/metrics` (`pip install clawmetry[otel]` dla wczytywania protobuf).

Otrzymujesz pulpit nawigacyjny ClawMetry zero-config, z priorytetem lokalnym, **oraz** Twoje dane w dowolnym backendzie, który już używa Twój zespół — bez uzależnienia od dostawcy, bez instalowania drugiego agenta.

## Konfiguracja

Większość użytkowników nie potrzebuje żadnej konfiguracji. ClawMetry automatycznie wykrywa Twój obszar roboczy, logi, sesje i crons.

Jeśli potrzebujesz dostosowania:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Wszystkie opcje: `clawmetry --help`

## Obsługiwane kanały

ClawMetry pokazuje aktywność na żywo dla każdego skonfigurowanego kanału OpenClaw. W diagramie Flow pojawiają się tylko kanały faktycznie skonfigurowane w Twoim pliku `openclaw.json` — nieskonfigurowane są automatycznie ukrywane.

Kliknij dowolny węzeł kanału w widoku Flow, aby zobaczyć widok dymków czatu na żywo z liczbą przychodzących i wychodzących wiadomości.

| Kanał | Status | Podgląd na żywo | Uwagi |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Pełny | ✅ | Wiadomości, statystyki, odświeżanie co 10 s |
| 💬 **iMessage** | ✅ Pełny | ✅ | Odczytuje `~/Library/Messages/chat.db` bezpośrednio |
| 💚 **WhatsApp** | ✅ Pełny | ✅ | Przez WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Pełny | ✅ | Przez signal-cli |
| 🟣 **Discord** | ✅ Pełny | ✅ | Wykrywanie serwera i kanału |
| 🟪 **Slack** | ✅ Pełny | ✅ | Wykrywanie obszaru roboczego i kanału |
| 🌐 **Webchat** | ✅ Pełny | ✅ | Sesje wbudowanego interfejsu webowego |
| 📡 **IRC** | ✅ Pełny | ✅ | Interfejs dymków w stylu terminala |
| 🍏 **BlueBubbles** | ✅ Pełny | ✅ | iMessage przez BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Pełny | ✅ | Przez webhooki Chat API |
| 🟣 **MS Teams** | ✅ Pełny | ✅ | Przez wtyczkę bota Teams |
| 🔷 **Mattermost** | ✅ Pełny | ✅ | Samodzielnie hostowany czat zespołowy |
| 🟩 **Matrix** | ✅ Pełny | ✅ | Zdecentralizowany, obsługa E2EE |
| 🟢 **LINE** | ✅ Pełny | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Pełny | ✅ | Zdecentralizowane wiadomości NIP-04 DM |
| 🟣 **Twitch** | ✅ Pełny | ✅ | Czat przez połączenie IRC |
| 🔷 **Feishu/Lark** | ✅ Pełny | ✅ | Subskrypcja zdarzeń WebSocket |
| 🔵 **Zalo** | ✅ Pełny | ✅ | Zalo Bot API |

> **Automatyczne wykrywanie:** ClawMetry odczytuje plik `~/.openclaw/openclaw.json` i renderuje tylko kanały, które faktycznie skonfigurowałeś. Nie jest wymagana ręczna konfiguracja.

## Wdrożenie z Docker

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

> **Uwaga:** Podczas uruchamiania w Docker zamontuj katalogi danych i logów swojego agenta (np. `~/.openclaw`, `~/.claude`, `~/.codex`), aby ClawMetry mógł automatycznie wykryć Twoją konfigurację.

## Wymagania

- Python 3.8+
- Flask (instalowany automatycznie przez pip)
- Środowisko uruchomieniowe agenta AI na tej samej maszynie: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw lub PicoClaw (lub zamontowane wolumeny dla Docker)
- Linux lub macOS

## Obsługa NemoClaw / OpenShell

ClawMetry automatycznie wykrywa [NemoClaw](https://github.com/NVIDIA/NemoClaw) — korporacyjną nakładkę bezpieczeństwa NVIDIA dla OpenClaw, która uruchamia agenty wewnątrz kontenerów OpenShell z piaskownicą.

W większości przypadków nie jest potrzebna żadna dodatkowa konfiguracja. Demon synchronizacji automatycznie odkrywa pliki sesji niezależnie od tego, czy znajdują się w `~/.openclaw/` na hoście, czy wewnątrz kontenera OpenShell.

### Jak to działa

ClawMetry wykrywa NemoClaw na dwa sposoby:

1. **Wykrywanie binarne** — sprawdza obecność CLI `nemoclaw` i uruchamia `nemoclaw status`, aby uzyskać informacje o piaskownicy
2. **Wykrywanie kontenerów** — skanuje uruchomione kontenery Docker w poszukiwaniu obrazów `openshell`, `nemoclaw` lub `ghcr.io/nvidia/`, a następnie odczytuje sesje przez wolumeny lub `docker cp`

Pliki sesji zsynchronizowane z kontenerów NemoClaw są oznaczane metadanymi `runtime=nemoclaw` i `container_id` w pulpicie chmury, dzięki czemu można je od razu odróżnić od standardowych sesji OpenClaw.

### Zalecana konfiguracja: demon synchronizacji na HOŚCIE

Aby uzyskać najlepsze wyniki, uruchom demona synchronizacji ClawMetry na **maszynie hosta** (nie wewnątrz piaskownicy). Pozwala to uniknąć ograniczeń polityki sieciowej NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Demon synchronizacji automatycznie znajdzie sesje wewnątrz wszystkich uruchomionych kontenerów OpenShell.

### Opcjonalnie: jawna nazwa piaskownicy

Jeśli automatyczne wykrywanie nie działa, wskaż ClawMetry właściwą piaskownicę:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Uruchamianie wewnątrz piaskownicy (zaawansowane)

Jeśli musisz uruchomić demona synchronizacji **wewnątrz** piaskownicy OpenShell, dodaj tę regułę ruchu wychodzącego do polityki sieciowej NemoClaw, aby mógł dotrzeć do interfejsu API ingestowania ClawMetry:

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

| Punkt końcowy | Port | Protokół | Wymagany |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Tak (demon synchronizacji do chmury) |
| `localhost:8900` | 8900 | HTTP | Tak (lokalny interfejs pulpitu nawigacyjnego) |
| Gniazdo Docker (`/var/run/docker.sock`) | — | Gniazdo Unix | Do odkrywania sesji kontenerów |

Demon synchronizacji wykonuje wyłącznie wychodzące wywołania HTTPS do `ingest.clawmetry.com`. Nie są wymagane żadne porty przychodzące.

---

## Wdrożenie w chmurze

Zapoznaj się z **[Przewodnikiem testowania w chmurze](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** dotyczącym tuneli SSH, odwrotnego proxy i Docker.

## Testowanie

Ten projekt jest testowany przy użyciu BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Telemetria

ClawMetry wysyła jednorazowy anonimowy ping "pierwsze uruchomienie" do
`https://app.clawmetry.com/api/install` przy pierwszym uruchomieniu
CLI `clawmetry` na nowej maszynie. Używamy tego do zliczania instalacji (jedyna
metryka marketingowa, którą mamy dla projektu OSS) i poznania, które
frameworki agentów mają zainstalowani nasi użytkownicy.

**Dokładnie jeden POST na instalację**, zawierający:

| Pole | Przykład | Dlaczego |
|---|---|---|
| `install_id` | losowy UUID przechowywany w `~/.clawmetry/install_id` | deduplikacja; nie powiązany z Twoim emailem ani api_key |
| `version` | `0.12.167` | jakie wersje są w użyciu |
| `os` / `os_version` | `Darwin` / `25.3.0` | priorytety obsługi platform |
| `python` | `3.11.15` | macierz obsługi wersji Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | z jakimi agentami powinniśmy integrować się w następnej kolejności |
| `is_ci` / `ci_provider` | `true` / `github_actions` | oddzielenie instalacji użytkowników od szumu CI |

**Czego NIE wysyłamy**: IP (chmura pobiera kod kraju po stronie serwera
z żądania, a następnie odrzuca IP), nazwa hosta, nazwa użytkownika, ścieżka
obszaru roboczego, zawartość plików, Twój api_key, Twój email, jakiekolwiek
dane osobowe lub specyficzne dla obszaru roboczego. Dane przesyłane przez sieć
są możliwe do skontrolowania w
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Rezygnacja** (każda z poniższych opcji wyłącza to na stałe):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Błąd sieci nigdy nie blokuje uruchomienia `clawmetry` — ping jest wysyłany
w stylu fire-and-forget w wątku demona z limitem czasu 3 s.

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
  <strong>🦞 Obserwuj, jak myśli Twój agent</strong><br>
  <sub>Stworzone przez <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Część ekosystemu <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
