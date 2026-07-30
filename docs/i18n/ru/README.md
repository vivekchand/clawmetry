<!-- i18n-src:9a05336fbdc1 -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Смотрите, как думает ваш агент.** Наблюдаемость в реальном времени для **14 сред выполнения ИИ-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 10. Один дашборд для всего вашего флота агентов.

> 🌐 **Читать на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Никакой настройки. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900** — и всё готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Работает с 14 средами выполнения агентов

ClawMetry начинался как инструмент наблюдаемости для OpenClaw, а теперь измеряет **весь ваш флот агентов** в одном дашборде, автоматически определяя каждую среду выполнения на вашей машине:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw и NemoClaw бесплатны в опенсорсном приложении; остальные среды выполнения открываются с ClawMetry Cloud или лицензией Pro для self-hosted развёртывания. Переключайте среды выполнения из шапки — и каждая вкладка (стоимость, токены, инструменты, трассировки) пересчитывается под неё. Точное разделение free/paid, матрицу тарифов, формат `/api/entitlement` и CLI `clawmetry license` смотрите в **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**.

## Что вы получаете

- **Flow** — живая анимированная диаграмма, показывающая, как сообщения проходят через каналы, «мозг», инструменты и обратно
- **Overview** — проверки состояния, тепловая карта активности, счётчики сессий, информация о модели
- **Usage** — учёт токенов и затрат с разбивкой по дням/неделям/месяцам
- **Sessions** — активные сессии агента с указанием модели, токенов, времени последней активности
- **Crons** — запланированные задачи со статусом, временем следующего запуска, длительностью
- **Logs** — цветная потоковая трансляция логов в реальном времени
- **Memory** — просмотр SOUL.md, MEMORY.md, AGENTS.md, ежедневных заметок
- **Transcripts** — интерфейс в виде чата для чтения истории сессий
- **Alerts** — лимиты бюджета, триггеры по частоте ошибок, обнаружение офлайн-агента; отправка в Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — блокировка деструктивных удалений, force push, изменений в БД, sudo, установки пакетов, сетевых вызовов до получения подтверждения в один клик

## Скриншоты

### 🧠 Brain — Живой поток событий агента
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Использование токенов и сводка по сессиям
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Лента вызовов инструментов в реальном времени
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Разбивка затрат по модели и сессии
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Просмотр файлов рабочего пространства
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Состояние безопасности и журнал аудита
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Лимиты бюджета, триггеры по частоте ошибок, вебхуки в Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Блокировка рискованных вызовов инструментов до ручного подтверждения; правила защиты на основе политик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Блокировка перед выполнением для Claude Code** — одна команда устанавливает
хук PreToolUse, который приостанавливает подходящие вызовы инструментов *перед* их выполнением и ждёт
вашего решения (один тап с телефона при включённых
[облачных push-уведомлениях](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Отказ блокирует только этот конкретный вызов инструмента — агент сохраняет сессию и может
попробовать другой подход. Подтверждение с телефона пропускает собственный
запрос разрешения Claude Code (вы уже ответили). Несовпавшие инструменты обходятся примерно в 40 мс и
переходят к обычному процессу разрешений Claude Code. Вы также получаете push на телефон, когда сам Claude Code
ждёт вашего решения (уведомления `permission_prompt` /
`idle_prompt`).

## Установка

**Однострочник (рекомендуется):**
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

Приложение v2 на React находится в `frontend/` и обслуживается по адресу `/v2`, когда
Flask-сервер запущен с включённым v2.

При разработке используйте два терминала:

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
`http://localhost:8900`, поэтому React-приложение может обращаться к локальному Flask-серверу
без дополнительной настройки CORS.

Чтобы собрать бандл, который поставляется вместе с Python-пакетом:

```bash
cd frontend
npm run build
```

Продакшн-бандл записывается в `clawmetry/static/v2/dist/`.

## Совместимость сред выполнения / агентов

ClawMetry наблюдает за множеством сред выполнения ИИ-агентов, а не только за OpenClaw. Каждая среда выполнения, отличная от OpenClaw, поставляется с собственным адаптером-читателем, который переводит её нативный формат сессий в унифицированные форматы ClawMetry; демон загружает их в то же хранилище DuckDB + облачный снапшот с пометкой среды выполнения, а вкладка воспроизведения сессий показывает **переключатель сред выполнения**, когда их присутствует больше одной. Полную матрицу и руководство по добавлению сред выполнения смотрите в [`docs/compatibility.md`](docs/compatibility.md), а вводный материал по семейству OpenClaw — в [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md).

| Среда выполнения / агент | Статус | Примечания |
|---|---|---|
| **OpenClaw** | Нативная | Эталонная среда выполнения, определяется автоматически |
| **PicoClaw** | Бета-адаптер | Плоский JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Транскрипты, модель, вызовы инструментов. |
| **NanoClaw** | Бета-адаптер | SQLite на каждую сессию (`data/v2-sessions`). Транскрипты + количество сообщений. |
| **Hermes** | Бета-адаптер | SQLite `~/.hermes/state.db`. Транскрипты, модель, токены/стоимость. |
| **Claude Code** | Бета-адаптер | JSONL `~/.claude/projects/.../<id>.jsonl`. Транскрипты, модель, вызовы инструментов + размышления, использование токенов. |
| **Codex** | Бета-адаптер | Rollout JSONL `~/.codex/sessions/...`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Cursor** | Бета-адаптер | SQLite `state.vscdb`. Транскрипты чата/композера, модель. |
| **Aider** | Бета-адаптер | `.aider.chat.history.md` на каждый проект. Транскрипты, модель, счётчики токенов. |
| **Goose** | Бета-адаптер | SQLite `~/.local/share/goose`. Транскрипты, модель, вызовы инструментов, итоговые токены. |
| **opencode** | Бета-адаптер | SQLite `~/.local/share/opencode`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Qwen Code** | Бета-адаптер | JSONL `~/.qwen/projects/.../chats`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Pi** | Бета-адаптер | JSONL `~/.pi/agent/sessions`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Deep Agents** | Бета-адаптер | SQLite `~/.deepagents/.state/sessions.db`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **n8n** | Бета-адаптер | SQLite `~/.n8n/database.sqlite`. Выполнения workflow, запуски узлов, промпты AI Agent, модель + токены там, где n8n их фиксирует. |

«Бета-адаптер» означает, что ClawMetry поставляет читатель для реального формата этой среды выполнения на диске, каждый из которых собран и проверен на реальной установке на реальной машине (см. `tests/fixtures/runtimes/<rt>/`). Адаптеры только для чтения; каждый честно отражает то, что его среда выполнения действительно хранит (например, PicoClaw/NanoClaw/Cursor не записывают стоимость токенов на диск). Когда на одном узле работает несколько сред выполнения, переключатель сред выполнения сужает представление сессий до одной для чистого детального анализа.

## Отслеживание любого SDK-агента — атрибуция затрат вне цикла

Все перечисленные выше среды выполнения записывают сессии на диск. Ваш собственный **продакшн-агент** — тот, что вы построили на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B или обычном цикле на `httpx` — этого не делает. Zero-config-перехватчик ClawMetry всё равно захватывает его LLM-вызовы (стоимость, токены, задержка, ошибки), подменяя методы `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (или переменная окружения `CLAWMETRY_SOURCE=support-agent`) помечает каждый вызов **именованным источником**, поэтому каждый продукт, который вы запускаете, отображается как отдельная полноценная строка с атрибуцией затрат в карточке дашборда **🔌 Внешние источники (out-loop)** на вкладке Overview — вызовы, провайдеры, задержка, частота ошибок по каждому агенту. Источник не задан? Вызовы всё равно отслеживаются, просто карточка остаётся скрытой.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Это тот же слой данных, который питают адаптеры сред выполнения (DuckDB → облачный снапшот), поэтому внешние источники синхронизируются с облачным дашбордом так же, как и всё остальное, со сквозным шифрованием (E2E).

## OpenTelemetry — независимо от вендора, отправляйте свои трассировки куда угодно

ClawMetry говорит на языке **OpenTelemetry** в обе стороны, используя **семантические соглашения GenAI**, поэтому трассировки вашего агента никогда не привязаны к одному инструменту.

**Экспорт** каждой сессии — вызовы LLM, инструменты, суб-агенты, токены, стоимость — в виде спанов OTLP/HTTP GenAI в любой коллектор (Datadog, Grafana, Honeycomb или ваш собственный OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Заголовки авторизации и интервал опроса задаются необязательными переменными окружения:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Приём** — встроенный приёмник OTLP принимает трассировки и метрики от чего угодно ещё по адресам `/v1/traces` и `/v1/metrics` (`pip install clawmetry[otel]` для приёма protobuf).

Вы получаете zero-config, локальный по умолчанию дашборд ClawMetry **и** свои данные в любом бэкенде, который уже использует ваша команда — никакой привязки к вендору, никакого второго агента для установки.

## Конфигурация

Большинству людей не нужна никакая настройка. ClawMetry автоматически определяет ваше рабочее пространство, логи, сессии и cron-задачи.

Если всё же нужна кастомизация:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Все опции: `clawmetry --help`

## Поддерживаемые каналы

ClawMetry показывает живую активность для каждого настроенного у вас канала OpenClaw. На диаграмме Flow отображаются только каналы, реально настроенные в вашем `openclaw.json` — ненастроенные автоматически скрываются.

Кликните по любому узлу канала на Flow, чтобы увидеть живой вид чат-бабблов с количеством входящих/исходящих сообщений.

| Канал | Статус | Живой попап | Примечания |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Полная | ✅ | Сообщения, статистика, обновление каждые 10с |
| 💬 **iMessage** | ✅ Полная | ✅ | Читает `~/Library/Messages/chat.db` напрямую |
| 💚 **WhatsApp** | ✅ Полная | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Полная | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Полная | ✅ | Определение гильдии + канала |
| 🟪 **Slack** | ✅ Полная | ✅ | Определение workspace + канала |
| 🌐 **Webchat** | ✅ Полная | ✅ | Встроенные веб-сессии |
| 📡 **IRC** | ✅ Полная | ✅ | Интерфейс в стиле терминала |
| 🍏 **BlueBubbles** | ✅ Полная | ✅ | iMessage через BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Полная | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Полная | ✅ | Через плагин Teams-бота |
| 🔷 **Mattermost** | ✅ Полная | ✅ | Самостоятельно размещённый корпоративный чат |
| 🟩 **Matrix** | ✅ Полная | ✅ | Децентрализованный, поддержка E2EE |
| 🟢 **LINE** | ✅ Полная | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Полная | ✅ | Децентрализованные личные сообщения NIP-04 |
| 🟣 **Twitch** | ✅ Полная | ✅ | Чат через подключение IRC |
| 🔷 **Feishu/Lark** | ✅ Полная | ✅ | Подписка на события через WebSocket |
| 🔵 **Zalo** | ✅ Полная | ✅ | Zalo Bot API |

> **Автоопределение:** ClawMetry читает ваш `~/.openclaw/openclaw.json` и отображает только те каналы, которые вы реально настроили. Ручная настройка не требуется.

## Развёртывание в Docker

Хотите запустить ClawMetry в контейнере? Не проблема! 🐳

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

> **Примечание:** При запуске в Docker смонтируйте директории данных и логов вашего агента (например, `~/.openclaw`, `~/.claude`, `~/.codex`), чтобы ClawMetry мог автоматически определить вашу конфигурацию.

## Требования

- Python 3.8+
- Flask (устанавливается автоматически через pip)
- Среда выполнения ИИ-агента на той же машине: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents или n8n (либо смонтированные тома для Docker)
- Linux или macOS

## Поддержка NemoClaw / OpenShell

ClawMetry автоматически определяет [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративную обёртку безопасности NVIDIA для OpenClaw, которая запускает агентов внутри изолированных контейнеров OpenShell.

В большинстве случаев дополнительная настройка не требуется. Демон синхронизации автоматически находит файлы сессий независимо от того, находятся ли они в `~/.openclaw/` на хосте или внутри контейнера OpenShell.

### Как это работает

ClawMetry определяет NemoClaw двумя способами:

1. **Определение по бинарнику** — проверяет наличие CLI `nemoclaw` и запускает `nemoclaw status`, чтобы получить информацию о песочнице
2. **Определение по контейнеру** — сканирует запущенные Docker-контейнеры на наличие образов `openshell`, `nemoclaw` или `ghcr.io/nvidia/`, затем читает сессии через смонтированные тома или `docker cp`

Файлы сессий, синхронизированные из контейнеров NemoClaw, помечаются в облачном дашборде метаданными `runtime=nemoclaw` и `container_id`, чтобы вы могли на глаз отличить их от стандартных сессий OpenClaw.

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

Если автоопределение не сработало, укажите ClawMetry нужную песочницу:

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

Примените командой:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Порты и эндпоинты

| Эндпоинт | Порт | Протокол | Обязательно |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Да (демон синхронизации → облако) |
| `localhost:8900` | 8900 | HTTP | Да (локальный интерфейс дашборда) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Для обнаружения сессий контейнеров |

Демон синхронизации выполняет только исходящие HTTPS-вызовы к `ingest.clawmetry.com`. Входящие порты не требуются.

---

## Облачное развёртывание

Смотрите **[Руководство по тестированию в облаке](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** для SSH-туннелей, обратного прокси и Docker.

## Тестирование

Этот проект тестируется с помощью BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрия

ClawMetry отправляет один анонимный пинг «первый запуск» на
`https://app.clawmetry.com/api/install` при первом запуске CLI
`clawmetry` на новой машине. Мы используем это, чтобы считать установки (единственная
маркетинговая метрика, доступная для OSS-проекта) и узнавать, какие
фреймворки агентов установлены у наших пользователей.

**Ровно один POST-запрос на установку**, содержащий:

| Поле | Пример | Зачем |
|---|---|---|
| `install_id` | случайный UUID, сохранённый в `~/.clawmetry/install_id` | дедупликация; не связан с вашим email или api_key |
| `version` | `0.12.167` | какие версии используются «в дикой природе» |
| `os` / `os_version` | `Darwin` / `25.3.0` | приоритеты поддержки платформ |
| `python` | `3.11.15` | матрица поддержки версий Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | с какими агентами нам стоит интегрироваться дальше |
| `is_ci` / `ci_provider` | `true` / `github_actions` | отделение установок людьми от шума CI |

**Чего мы НЕ отправляем**: IP-адрес (облако вычисляет код страны на стороне сервера
из запроса, а затем отбрасывает IP), имя хоста, имя пользователя, путь рабочего пространства,
содержимое файлов, ваш api_key, ваш email, что-либо личное (PII) или
специфичное для рабочего пространства. Передаваемые данные можно проверить в
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Отказаться** (любой из этих способов отключает телеметрию навсегда):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Сбой сети здесь никогда не блокирует запуск `clawmetry` — пинг
отправляется в режиме «выстрелил и забыл» в отдельном потоке-демоне с таймаутом 3 с.

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
  <strong>🦞 Смотрите, как думает ваш агент</strong><br>
  <sub>Создано <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Часть экосистемы <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
