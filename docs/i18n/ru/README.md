<!-- i18n-src:0e34918f8f2e -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Наблюдайте за мышлением своего агента.** Наблюдаемость в реальном времени для **14 рантаймов ИИ-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 10 других. Один дашборд для всего вашего флота агентов.

> 🌐 **Читать на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Ноль конфигурации. Автоопределение всего.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900** и всё готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Работает с 14 рантаймами агентов

ClawMetry начинался как инструмент наблюдаемости для OpenClaw, а теперь измеряет метрики **всего вашего флота агентов** в одном дашборде, автоматически определяя каждый рантайм на вашей машине:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw и NemoClaw бесплатны в опенсорсном приложении; остальные рантаймы становятся доступны с ClawMetry Cloud или самостоятельно размещённой лицензией Pro. Переключайте рантаймы в шапке, и каждая вкладка — расходы, токены, инструменты, трассировки — переопределяется под этот рантайм. См. **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** для точного разделения на бесплатное/платное, матрицы тарифов, структуры `/api/entitlement` и CLI `clawmetry license`.

## Что вы получаете

- **Flow** — живая анимированная диаграмма, показывающая, как сообщения проходят через каналы, мозг, инструменты и обратно
- **Overview** — проверки состояния, тепловая карта активности, счётчики сессий, информация о модели
- **Usage** — отслеживание токенов и расходов с разбивкой по дням/неделям/месяцам
- **Sessions** — активные сессии агентов с моделью, токенами, временем последней активности
- **Crons** — запланированные задачи со статусом, временем следующего запуска, длительностью
- **Logs** — цветная потоковая передача логов в реальном времени
- **Memory** — просмотр SOUL.md, MEMORY.md, AGENTS.md, ежедневных заметок
- **Transcripts** — интерфейс в виде чата для чтения истории сессий
- **Alerts** — лимиты бюджета, триггеры по частоте ошибок, обнаружение офлайн-агента; отправка в Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — блокировка деструктивных удалений, принудительных пушей, мутаций БД, sudo, установки пакетов, сетевых вызовов за одним подтверждением в один клик

## Скриншоты

### 🧠 Brain — Живой поток событий агента
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Использование токенов и сводка по сессиям
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Лента вызовов инструментов в реальном времени
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Разбивка расходов по модели и сессии
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Обозреватель файлов рабочего пространства
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Состояние защищённости и журнал аудита
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Лимиты бюджета, триггеры по частоте ошибок, вебхуки в Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Блокировка рискованных вызовов инструментов до ручного подтверждения; правила защиты на основе политик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Блокировка перед выполнением для Claude Code** — одна команда устанавливает
хук PreToolUse, который приостанавливает подходящие вызовы инструментов *до* их выполнения и ждёт
вашего решения (одно нажатие с телефона при включённых
[push-уведомлениях облака](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Отказ блокирует только этот один вызов инструмента — агент сохраняет свою сессию и может
попробовать другой подход. Подтверждение с телефона пропускает собственный запрос
разрешения Claude Code (вы уже ответили). Несовпавшие инструменты стоят ~40 мс и
переходят к обычному потоку разрешений Claude Code. Вы также получите push-уведомление на телефон, когда
сам Claude Code ждёт вашего ответа (уведомления `permission_prompt` /
`idle_prompt`).

## Установка

**Однострочная команда (рекомендуется):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**Из исходников:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Разработка фронтенда v2

Приложение React v2 находится в `frontend/` и обслуживается по адресу `/v2`, когда
сервер Flask запущен с включённым v2.

Используйте два терминала во время разработки:

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

Откройте `http://localhost:5173/v2/`. Vite проксирует запросы `/api` на
`http://localhost:8900`, поэтому приложение React может общаться с локальным сервером Flask
без дополнительной настройки CORS.

Чтобы собрать бандл, который поставляется с пакетом Python:

```bash
cd frontend
npm run build
```

Production-бандл записывается в `clawmetry/static/v2/dist/`.

## Совместимость рантаймов / агентов

ClawMetry наблюдает за многими рантаймами ИИ-агентов, а не только за OpenClaw. Каждый рантайм, отличный от OpenClaw, поставляется со специализированным адаптером чтения, который переводит его нативный формат сессий в унифицированные структуры ClawMetry; демон загружает их в то же хранилище DuckDB + облачный снапшот, помечая рантаймом, а вкладка воспроизведения сессии показывает **переключатель рантайма**, если присутствует больше одного. См. [`docs/compatibility.md`](docs/compatibility.md) для полной матрицы + руководства по добавлению рантаймов, и [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) для введения в семейство OpenClaw.

Используете инструмент безопасности агентов [numbat от Perplexity](https://github.com/perplexityai/numbat)? ClawMetry принимает его результаты и решения о принудительном применении из коробки — см. [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Рантайм / агент | Статус | Примечания |
|---|---|---|
| **OpenClaw** | Нативный | Эталонный рантайм, автоопределение |
| **PicoClaw** | Бета-адаптер | Плоский `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Транскрипты, модель, вызовы инструментов. |
| **NanoClaw** | Бета-адаптер | SQLite для каждой сессии (`data/v2-sessions`). Транскрипты + количество сообщений. |
| **Hermes** | Бета-адаптер | SQLite `~/.hermes/state.db`. Транскрипты, модель, токены/расходы. |
| **Claude Code** | Бета-адаптер | JSONL `~/.claude/projects/.../<id>.jsonl`. Транскрипты, модель, вызовы инструментов + размышления, использование токенов. |
| **Codex** | Бета-адаптер | Rollout JSONL `~/.codex/sessions/...`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Cursor** | Бета-адаптер | SQLite `state.vscdb`. Транскрипты чата/композера, модель. |
| **Aider** | Бета-адаптер | `.aider.chat.history.md` на проект. Транскрипты, модель, счётчики токенов. |
| **Goose** | Бета-адаптер | SQLite `~/.local/share/goose`. Транскрипты, модель, вызовы инструментов, итоговые токены. |
| **opencode** | Бета-адаптер | SQLite `~/.local/share/opencode`. Транскрипты, модель, вызовы инструментов, токены + расходы. |
| **Qwen Code** | Бета-адаптер | JSONL `~/.qwen/projects/.../chats`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Pi** | Бета-адаптер | JSONL `~/.pi/agent/sessions`. Транскрипты, модель, вызовы инструментов, токены + расходы. |
| **Deep Agents** | Бета-адаптер | SQLite `~/.deepagents/.state/sessions.db`. Транскрипты, модель, вызовы инструментов, токены + расходы. |
| **n8n** | Бета-адаптер | SQLite `~/.n8n/database.sqlite`. Выполнения рабочих процессов, запуски узлов, промпты AI Agent, модель + токены там, где n8n их фиксирует. |
| **Antigravity** | Бета-адаптер | Brain JSONL в `~/.gemini/<flavor>/brain/`. Диалоги, шаги инструментов, размышления, разбивка токенов Gemini по каждой генерации + расходы, расход фоновой генерации. |
| **GitHub Copilot** | Бета-адаптер | `events.jsonl` Copilot CLI в `~/.copilot/session-state/` + реестр использования по каждому вызову `session-store.db`. Диалоги, вызовы инструментов, маршрутизация модели, разбивка токенов с учётом кэша, расходы в AI-кредитах, выставляемых вендором. |

«Бета-адаптер» означает, что ClawMetry поставляет считыватель для реального формата данных на диске этого рантайма, каждый из которых собран и проверен на реальной установке на реальной машине (см. `tests/fixtures/runtimes/<rt>/`). Адаптеры доступны только для чтения; каждый честно отражает то, что его рантайм реально хранит (например, PicoClaw/NanoClaw/Cursor не записывают стоимость токенов на диск). Когда на одном узле работает несколько рантаймов, переключатель рантайма сужает представление сессий до одного для чистого глубокого анализа.

## Отслеживание любого агента на SDK — атрибуция расходов вне цикла

Все перечисленные выше рантаймы записывают сессии на диск. Ваш собственный **production-агент** — тот, что вы построили на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B или обычном цикле на `httpx` — этого не делает. Перехватчик ClawMetry с нулевой конфигурацией всё равно захватывает его вызовы LLM (расходы, токены, задержку, ошибки) путём monkey-патчинга `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (или переменная окружения `CLAWMETRY_SOURCE=support-agent`) помечает каждый вызов **именованным источником**, поэтому каждый продукт, который вы запускаете, отображается как отдельная полноценная строка с атрибуцией расходов в карточке дашборда **🔌 Источники вне цикла** на вкладке Overview — вызовы, провайдеры, задержка, частота ошибок по каждому агенту. Источник не задан? Вызовы всё равно отслеживаются, карточка просто остаётся скрытой.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Это тот же слой данных, который питают адаптеры рантаймов (DuckDB → облачный снапшот), поэтому источники вне цикла синхронизируются с облачным дашбордом так же, как и всё остальное, со сквозным шифрованием.

## OpenTelemetry — независимо от вендора, отправляйте свои трассировки куда угодно

ClawMetry говорит на **OpenTelemetry** в обоих направлениях, используя **семантические соглашения GenAI**, поэтому трассировки вашего агента никогда не привязаны к одному инструменту.

**Экспортируйте** каждую сессию — вызовы LLM, инструменты, суб-агентов, токены, расходы — в виде спанов OTLP/HTTP GenAI в любой коллектор (Datadog, Grafana, Honeycomb или ваш собственный OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Заголовки авторизации и интервал опроса — необязательные переменные окружения:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Приём** — встроенный приёмник OTLP принимает трассировки и метрики от чего угодно ещё по адресам `/v1/traces` и `/v1/metrics` (`pip install clawmetry[otel]` для приёма protobuf).

Вы получаете дашборд ClawMetry с нулевой конфигурацией, локальный по умолчанию, **и** свои данные в любом бэкенде, который уже использует ваша команда — без привязки к одному вендору, без второго агента для установки.

## Конфигурация

Большинству людей вообще не нужна никакая конфигурация. ClawMetry автоматически определяет ваше рабочее пространство, логи, сессии и cron-задачи.

Если вам всё же нужно настроить:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Все опции: `clawmetry --help`

## Поддерживаемые каналы

ClawMetry показывает живую активность для каждого настроенного вами канала OpenClaw. В диаграмме Flow отображаются только каналы, которые реально настроены в вашем `openclaw.json` — ненастроенные автоматически скрыты.

Кликните на любой узел канала во Flow, чтобы увидеть живое представление в виде чата с количеством входящих/исходящих сообщений.

| Канал | Статус | Живое всплывающее окно | Примечания |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Полная | ✅ | Сообщения, статистика, обновление каждые 10 с |
| 💬 **iMessage** | ✅ Полная | ✅ | Читает `~/Library/Messages/chat.db` напрямую |
| 💚 **WhatsApp** | ✅ Полная | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Полная | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Полная | ✅ | Определение гильдии + канала |
| 🟪 **Slack** | ✅ Полная | ✅ | Определение рабочего пространства + канала |
| 🌐 **Webchat** | ✅ Полная | ✅ | Встроенные сессии веб-интерфейса |
| 📡 **IRC** | ✅ Полная | ✅ | Интерфейс в терминальном стиле |
| 🍏 **BlueBubbles** | ✅ Полная | ✅ | iMessage через REST API BlueBubbles |
| 🔵 **Google Chat** | ✅ Полная | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Полная | ✅ | Через плагин бота Teams |
| 🔷 **Mattermost** | ✅ Полная | ✅ | Самостоятельно размещённый командный чат |
| 🟩 **Matrix** | ✅ Полная | ✅ | Децентрализованный, поддержка E2EE |
| 🟢 **LINE** | ✅ Полная | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Полная | ✅ | Децентрализованные личные сообщения NIP-04 |
| 🟣 **Twitch** | ✅ Полная | ✅ | Чат через соединение IRC |
| 🔷 **Feishu/Lark** | ✅ Полная | ✅ | Подписка на события через WebSocket |
| 🔵 **Zalo** | ✅ Полная | ✅ | Zalo Bot API |

> **Автоопределение:** ClawMetry читает ваш `~/.openclaw/openclaw.json` и отображает только те каналы, которые вы реально настроили. Ручная настройка не требуется.

## Развёртывание в Docker

Хотите запустить ClawMetry в контейнере? Без проблем! 🐳

**Быстрый старт с Docker:**

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

**Пример Docker Compose:**

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

> **Примечание:** При запуске в Docker смонтируйте каталоги данных + логов вашего агента (например, `~/.openclaw`, `~/.claude`, `~/.codex`), чтобы ClawMetry мог автоматически определить вашу настройку.

## Требования

- Python 3.8+
- Flask (устанавливается автоматически через pip)
- Рантайм ИИ-агента на той же машине: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity или GitHub Copilot (либо смонтированные тома для Docker)
- Linux или macOS

## Поддержка NemoClaw / OpenShell

ClawMetry автоматически определяет [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративную обёртку безопасности NVIDIA для OpenClaw, которая запускает агентов внутри изолированных контейнеров OpenShell.

В большинстве случаев дополнительная настройка не требуется. Демон синхронизации автоматически обнаруживает файлы сессий независимо от того, находятся ли они в `~/.openclaw/` на хосте или внутри контейнера OpenShell.

### Как это работает

ClawMetry определяет NemoClaw двумя способами:

1. **Определение по бинарнику** — проверяет наличие CLI `nemoclaw` и запускает `nemoclaw status` для получения информации о песочнице
2. **Определение по контейнеру** — сканирует запущенные контейнеры Docker на предмет образов `openshell`, `nemoclaw` или `ghcr.io/nvidia/`, затем читает сессии через смонтированные тома или `docker cp`

Файлы сессий, синхронизированные из контейнеров NemoClaw, помечаются метаданными `runtime=nemoclaw` и `container_id` в облачном дашборде, чтобы вы могли на глаз отличить их от стандартных сессий OpenClaw.

### Рекомендуемая настройка: демон синхронизации на ХОСТЕ

Для наилучшего опыта запускайте демон синхронизации ClawMetry на **хост-машине** (не внутри песочницы). Это позволяет избежать ограничений сетевой политики NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Демон синхронизации автоматически найдёт сессии внутри любых запущенных контейнеров OpenShell.

### Опционально: явное имя песочницы

Если автоопределение не работает, укажите ClawMetry на нужную песочницу:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Запуск внутри песочницы (продвинутый вариант)

Если вам необходимо запускать демон синхронизации **внутри** песочницы OpenShell, добавьте это правило исходящего трафика в вашу сетевую политику NemoClaw, чтобы он мог достучаться до API приёма ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Примените с помощью:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Порты и точки входа

| Точка входа | Порт | Протокол | Требуется |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Да (демон синхронизации → облако) |
| `localhost:8900` | 8900 | HTTP | Да (локальный интерфейс дашборда) |
| Сокет Docker (`/var/run/docker.sock`) | — | Unix-сокет | Для обнаружения сессий в контейнерах |

Демон синхронизации выполняет только исходящие вызовы HTTPS к `ingest.clawmetry.com`. Входящие порты не требуются.

---

## Развёртывание в облаке

См. **[Руководство по тестированию в облаке](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** для SSH-туннелей, обратного прокси и Docker.

## Тестирование

Этот проект тестируется с помощью BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрия

ClawMetry отправляет анонимные пинги жизненного цикла установки на
`https://app.clawmetry.com/api/install`: один пинг `install` при первом
запуске CLI `clawmetry` на новой машине, один пинг `update`
при первом запуске после обновления до новой версии, и один пинг
`onboarded`, когда вы завершаете выбор в мастере знакомства в дашборде. Мы используем это,
чтобы считать реальные установки (сырые цифры загрузок PyPI примерно на 98% состоят из зеркал, CI
и повторных загрузок автообновления) и узнавать, какие фреймворки агентов и
версии реально используются.

**Не более одного POST-запроса на событие жизненного цикла на версию**, содержащего:

| Поле | Пример | Зачем |
|---|---|---|
| `install_id` | случайный UUID, хранящийся в `~/.clawmetry/install_id` | дедупликация; анонимно, пока вы явно не подключите синхронизацию с облаком (после этого аутентифицированный хартбит демона несёт его, связывая эту установку с вашим аккаунтом) |
| `event` | `install` / `update` / `onboarded` | новая установка или обновление существующей |
| `version` | `0.12.167` | какие версии реально используются |
| `os` / `os_version` | `Darwin` / `25.3.0` | приоритеты поддержки платформ |
| `python` | `3.11.15` | матрица поддержки версий Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | с какими агентами нам стоит интегрироваться дальше |
| `is_ci` / `ci_provider` | `true` / `github_actions` | отделение установок реальными людьми от шума CI |

**Что мы НЕ отправляем**: IP-адрес (облако определяет код страны на стороне сервера
из запроса, затем отбрасывает IP), имя хоста, имя пользователя, путь к рабочему пространству,
содержимое файлов, ваш api_key, ваш email, что-либо личное или относящееся к
рабочему пространству. Полезная нагрузка на проводе доступна для аудита в
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Отказ от участия** (любой из этих способов отключает её навсегда):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Сбой сети здесь никогда не блокирует запуск `clawmetry` — пинг
отправляется по принципу «выстрелил и забыл» в отдельном потоке демона с таймаутом 3 с.

## История звёзд

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Лицензия

MIT

---

<p align="center">
  <strong>🦞 Наблюдайте за мышлением своего агента</strong><br>
  <sub>Создано <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Часть экосистемы <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
