<!-- i18n-src:191e9094d7fa -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Наблюдайте за мышлением вашего агента.** Наблюдаемость в реальном времени для **14 сред выполнения AI-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 10 других. Одна панель для всего вашего флота агентов.

> 🌐 **Читайте на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Никакой настройки. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**, и всё готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Работает с 14 средами выполнения агентов

ClawMetry начинался как инструмент наблюдаемости для OpenClaw, а теперь измеряет весь ваш **флот агентов** на одной панели, автоматически обнаруживая каждую среду выполнения на вашей машине:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw и NemoClaw бесплатны в open-source приложении; остальные среды выполнения доступны с ClawMetry Cloud или с self-hosted лицензией Pro. Переключайте среды выполнения из шапки, и каждая вкладка — стоимость, токены, инструменты, трассировки — переключит область на эту среду. Точное разделение free/paid, матрицу тарифов, формат `/api/entitlement` и CLI `clawmetry license` смотрите в **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**.

## Что вы получаете

- **Flow** — живая анимированная диаграмма, показывающая, как сообщения проходят через каналы, "мозг", инструменты и обратно
- **Overview** — проверки состояния, тепловая карта активности, счётчики сессий, информация о модели
- **Usage** — отслеживание токенов и стоимости с разбивкой по дням/неделям/месяцам
- **Sessions** — активные сессии агента с моделью, токенами, временем последней активности
- **Crons** — запланированные задания со статусом, временем следующего запуска, длительностью
- **Logs** — цветная потоковая передача логов в реальном времени
- **Memory** — просмотр SOUL.md, MEMORY.md, AGENTS.md, ежедневных заметок
- **Transcripts** — интерфейс в виде чат-пузырей для чтения истории сессий
- **Alerts** — лимиты бюджета, триггеры по проценту ошибок, обнаружение офлайн-агента; отправка в Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — блокировка деструктивных удалений, force push, изменений БД, sudo, установок пакетов, сетевых вызовов до получения подтверждения в один клик

## Скриншоты

### 🧠 Brain — Живой поток событий агента
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Использование токенов и сводка по сессиям
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Лента вызовов инструментов в реальном времени
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Разбивка стоимости по моделям и сессиям
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Браузер файлов рабочего пространства
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Состояние безопасности и журнал аудита
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Лимиты бюджета, триггеры по проценту ошибок, вебхуки в Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Блокировка рискованных вызовов инструментов до ручного подтверждения; правила защиты на основе политик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Блокировка перед выполнением для Claude Code** — одна команда устанавливает
хук PreToolUse, который приостанавливает подходящие вызовы инструментов *до* их выполнения и ждёт
вашего решения (одно нажатие с телефона при включённых
[облачных push-уведомлениях](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Отказ блокирует только этот один вызов инструмента — сессия агента сохраняется, и он может
попробовать другой подход. Подтверждение с телефона пропускает собственный
запрос разрешения Claude Code (вы уже ответили). Несовпавшие инструменты стоят ~40 мс и
проходят через обычный поток разрешений Claude Code. Вы также получите push на телефон, когда сам Claude Code
ожидает вашего ответа (уведомления `permission_prompt` /
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

## Разработка v2 Frontend

Приложение v2 на React находится в `frontend/` и обслуживается по адресу `/v2`, когда
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

Чтобы собрать бандл, который поставляется вместе с Python-пакетом:

```bash
cd frontend
npm run build
```

Продакшн-бандл записывается в `clawmetry/static/v2/dist/`.

## Совместимость сред выполнения / агентов

ClawMetry наблюдает за многими средами выполнения AI-агентов, а не только за OpenClaw. Каждая среда выполнения, отличная от OpenClaw, поставляется со специальным адаптером-читателем, который переводит её нативный формат сессий в унифицированные форматы ClawMetry; демон вносит их в то же хранилище DuckDB + облачный снапшот, помечая средой выполнения, а вкладка воспроизведения сессии показывает **переключатель среды выполнения**, когда присутствует более одной. Полную матрицу и руководство по добавлению сред выполнения смотрите в [`docs/compatibility.md`](docs/compatibility.md), а вводную информацию по семейству OpenClaw — в [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md).

Используете инструмент безопасности агентов [numbat от Perplexity](https://github.com/perplexityai/numbat)? ClawMetry принимает его находки и решения по применению политик "из коробки" — см. [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Среда выполнения / агент | Статус | Примечания |
|---|---|---|
| **OpenClaw** | Нативная | Эталонная среда выполнения, обнаруживается автоматически |
| **PicoClaw** | Бета-адаптер | Плоский JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Транскрипты, модель, вызовы инструментов. |
| **NanoClaw** | Бета-адаптер | SQLite на сессию (`data/v2-sessions`). Транскрипты + счётчики сообщений. |
| **Hermes** | Бета-адаптер | SQLite `~/.hermes/state.db`. Транскрипты, модель, токены/стоимость. |
| **Claude Code** | Бета-адаптер | JSONL `~/.claude/projects/.../<id>.jsonl`. Транскрипты, модель, вызовы инструментов + размышления, использование токенов. |
| **Codex** | Бета-адаптер | Rollout JSONL `~/.codex/sessions/...`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Cursor** | Бета-адаптер | SQLite `state.vscdb`. Транскрипты чата/composer, модель. |
| **Aider** | Бета-адаптер | `.aider.chat.history.md` на проект. Транскрипты, модель, количество токенов. |
| **Goose** | Бета-адаптер | SQLite `~/.local/share/goose`. Транскрипты, модель, вызовы инструментов, итоговые токены. |
| **opencode** | Бета-адаптер | SQLite `~/.local/share/opencode`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Qwen Code** | Бета-адаптер | JSONL `~/.qwen/projects/.../chats`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Pi** | Бета-адаптер | JSONL `~/.pi/agent/sessions`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Deep Agents** | Бета-адаптер | SQLite `~/.deepagents/.state/sessions.db`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **n8n** | Бета-адаптер | SQLite `~/.n8n/database.sqlite`. Выполнения рабочих процессов, запуски узлов, промпты AI Agent, модель + токены там, где n8n их фиксирует. |
| **Antigravity** | Бета-адаптер | Brain JSONL в `~/.gemini/<flavor>/brain/`. Диалоги, шаги инструментов, размышления, разбивка токенов Gemini по каждой генерации + стоимость, расход фоновой генерации. |

"Бета-адаптер" означает, что ClawMetry поставляет читатель для реального формата на диске этой среды выполнения, каждый из которых собран и проверен на реальной установке на реальной машине (см. `tests/fixtures/runtimes/<rt>/`). Адаптеры доступны только для чтения; каждый честен в отношении того, что его среда выполнения на самом деле хранит (например, PicoClaw/NanoClaw/Cursor не записывают стоимость токенов на диск). Когда на одном узле работает несколько сред выполнения, переключатель среды выполнения ограничивает область просмотра сессий одной средой для чистого детального анализа.

## Отслеживание любого SDK-агента — атрибуция стоимости вне контура

Все среды выполнения, перечисленные выше, записывают сессии на диск. Ваш собственный **продакшн-агент** — тот, что вы построили на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B или на обычном цикле `httpx`, — этого не делает. Zero-config перехватчик ClawMetry всё равно захватывает его LLM-вызовы (стоимость, токены, задержка, ошибки) путём monkey-patching `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (или переменная окружения `CLAWMETRY_SOURCE=support-agent`) помечает каждый вызов **именованным источником**, поэтому каждый продукт, который вы запускаете, отображается как отдельная полноценная строка с атрибуцией стоимости в карточке **🔌 Внешние источники (Out-loop sources)** на вкладке Overview панели — вызовы, провайдеры, задержка, процент ошибок для каждого агента. Источник не задан? Вызовы всё равно отслеживаются, просто карточка остаётся скрытой.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Это тот же слой данных, которым питаются адаптеры сред выполнения (DuckDB → облачный снапшот), поэтому внешние источники синхронизируются с облачной панелью так же, как и всё остальное, со сквозным шифрованием (E2E).

## OpenTelemetry — не привязано к вендору, отправляйте трассировки куда угодно

ClawMetry говорит на языке **OpenTelemetry** в обоих направлениях, используя **семантические соглашения GenAI**, поэтому трассировки ваших агентов никогда не привязаны к одному инструменту.

**Экспортируйте** каждую сессию — вызовы LLM, инструменты, суб-агентов, токены, стоимость — как спаны OTLP/HTTP GenAI в любой коллектор (Datadog, Grafana, Honeycomb или ваш собственный OTel Collector):

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

Вы получаете панель ClawMetry с нулевой настройкой, работающую локально, **и** свои данные в любом бэкенде, который уже использует ваша команда — никакой привязки к одному вендору, никакого второго агента для установки.

## Настройка

Большинству людей не нужна какая-либо настройка. ClawMetry автоматически определяет ваше рабочее пространство, логи, сессии и cron-задания.

Если вам всё же нужна кастомизация:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Все опции: `clawmetry --help`

## Поддерживаемые каналы

ClawMetry показывает живую активность для каждого канала OpenClaw, который у вас настроен. В диаграмме Flow отображаются только те каналы, которые реально настроены в вашем `openclaw.json` — ненастроенные автоматически скрываются.

Нажмите на любой узел канала во Flow, чтобы увидеть представление с живыми чат-пузырями и счётчиками входящих/исходящих сообщений.

| Канал | Статус | Живое всплывающее окно | Примечания |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Полностью | ✅ | Сообщения, статистика, обновление каждые 10с |
| 💬 **iMessage** | ✅ Полностью | ✅ | Читает `~/Library/Messages/chat.db` напрямую |
| 💚 **WhatsApp** | ✅ Полностью | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Полностью | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Полностью | ✅ | Определение гильдии + канала |
| 🟪 **Slack** | ✅ Полностью | ✅ | Определение рабочего пространства + канала |
| 🌐 **Webchat** | ✅ Полностью | ✅ | Встроенные сессии веб-интерфейса |
| 📡 **IRC** | ✅ Полностью | ✅ | Интерфейс в стиле терминала с пузырями |
| 🍏 **BlueBubbles** | ✅ Полностью | ✅ | iMessage через BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Полностью | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Полностью | ✅ | Через плагин бота Teams |
| 🔷 **Mattermost** | ✅ Полностью | ✅ | Self-hosted корпоративный чат |
| 🟩 **Matrix** | ✅ Полностью | ✅ | Децентрализованный, поддержка E2EE |
| 🟢 **LINE** | ✅ Полностью | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Полностью | ✅ | Децентрализованные личные сообщения NIP-04 |
| 🟣 **Twitch** | ✅ Полностью | ✅ | Чат через подключение IRC |
| 🔷 **Feishu/Lark** | ✅ Полностью | ✅ | Подписка на события через WebSocket |
| 🔵 **Zalo** | ✅ Полностью | ✅ | Zalo Bot API |

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

> **Примечание:** При запуске в Docker смонтируйте каталоги данных + логов вашего агента (например, `~/.openclaw`, `~/.claude`, `~/.codex`), чтобы ClawMetry мог автоматически определить вашу конфигурацию.

## Требования

- Python 3.8+
- Flask (устанавливается автоматически через pip)
- Среда выполнения AI-агента на той же машине: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n или Antigravity (либо смонтированные тома для Docker)
- Linux или macOS

## Поддержка NemoClaw / OpenShell

ClawMetry автоматически определяет [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративную обёртку безопасности NVIDIA для OpenClaw, которая запускает агентов внутри изолированных контейнеров OpenShell.

В большинстве случаев дополнительная настройка не требуется. Демон синхронизации автоматически обнаруживает файлы сессий, независимо от того, находятся ли они в `~/.openclaw/` на хосте или внутри контейнера OpenShell.

### Как это работает

ClawMetry обнаруживает NemoClaw двумя способами:

1. **Определение по бинарному файлу** — проверяет наличие CLI `nemoclaw` и запускает `nemoclaw status`, чтобы получить информацию о песочнице
2. **Определение по контейнеру** — сканирует запущенные Docker-контейнеры на предмет образов `openshell`, `nemoclaw` или `ghcr.io/nvidia/`, а затем читает сессии через смонтированные тома или `docker cp`

Файлы сессий, синхронизированные из контейнеров NemoClaw, помечаются метаданными `runtime=nemoclaw` и `container_id` в облачной панели, поэтому вы можете сразу отличить их от стандартных сессий OpenClaw.

### Рекомендуемая настройка: демон синхронизации на ХОСТЕ

Для лучшего опыта запускайте демон синхронизации ClawMetry на **хост-машине** (не внутри песочницы). Это позволяет избежать ограничений сетевой политики NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Демон синхронизации автоматически найдёт сессии внутри любых запущенных контейнеров OpenShell.

### Опционально: явное указание имени песочницы

Если автоопределение не работает, укажите ClawMetry нужную песочницу:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Запуск внутри песочницы (продвинутый вариант)

Если вам необходимо запускать демон синхронизации **внутри** песочницы OpenShell, добавьте это правило исходящего трафика в вашу сетевую политику NemoClaw, чтобы он мог обращаться к API приёма данных ClawMetry:

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

| Точка входа | Порт | Протокол | Обязательно |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Да (демон синхронизации → облако) |
| `localhost:8900` | 8900 | HTTP | Да (локальный интерфейс панели) |
| Docker-сокет (`/var/run/docker.sock`) | — | Unix socket | Для обнаружения сессий контейнеров |

Демон синхронизации выполняет только исходящие HTTPS-вызовы к `ingest.clawmetry.com`. Входящие порты не требуются.

---

## Облачное развёртывание

См. **[Руководство по тестированию в облаке](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** для SSH-туннелей, обратного прокси и Docker.

## Тестирование

Этот проект тестируется с помощью BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрия

ClawMetry отправляет анонимные пинги жизненного цикла установки на
`https://app.clawmetry.com/api/install`: один пинг `install` при первом
запуске CLI `clawmetry` на новой машине, один пинг `update`
при первом запуске после обновления до новой версии, и один пинг `onboarded`,
когда вы завершаете выбор в процессе онбординга панели. Мы используем это,
чтобы считать реальные установки (сырые цифры загрузок PyPI примерно на 98% состоят из зеркал, CI
и повторных загрузок автообновления) и узнавать, какие среды выполнения агентов и
версии реально используются.

**Не более одного POST-запроса на событие жизненного цикла на версию**, содержащего:

| Поле | Пример | Зачем |
|---|---|---|
| `install_id` | случайный UUID, хранящийся в `~/.clawmetry/install_id` | дедупликация; анонимно, пока вы явно не подключите синхронизацию Cloud (после этого аутентифицированный heartbeat демона переносит его, связывая эту установку с вашим аккаунтом) |
| `event` | `install` / `update` / `onboarded` | новая установка против обновления существующей |
| `version` | `0.12.167` | какие версии используются |
| `os` / `os_version` | `Darwin` / `25.3.0` | приоритеты поддержки платформ |
| `python` | `3.11.15` | матрица поддержки версий Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | с какими агентами нам стоит интегрироваться дальше |
| `is_ci` / `ci_provider` | `true` / `github_actions` | отделение установок людьми от шума CI |

**Что мы НЕ отправляем**: IP-адрес (облако определяет код страны на стороне сервера
из запроса, затем отбрасывает IP), имя хоста, имя пользователя, путь к рабочему пространству, содержимое файлов, ваш api_key, ваш email, что-либо личное (PII) или
специфичное для рабочего пространства. Полезная нагрузка на проводе доступна для аудита в
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Отказаться** (любой из этих способов отключает телеметрию навсегда):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Сбой сети здесь никогда не блокирует запуск `clawmetry` — пинг
отправляется по принципу fire-and-forget в отдельном потоке демона с таймаутом 3 с.

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
  <strong>🦞 Наблюдайте за мышлением вашего агента</strong><br>
  <sub>Создано <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Часть экосистемы <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
