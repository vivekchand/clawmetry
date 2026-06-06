<!-- i18n-src:48548997be76 -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Наблюдайте за мышлением агента.** Наблюдаемость в реальном времени для **12 сред выполнения ИИ-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 8. Одна панель управления для всего вашего флота агентов.

> 🌐 **Читать на:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Без настройки. Автоматически определяет всё.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900** — и готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Работает с 12 средами выполнения агентов

ClawMetry начинался как инструмент наблюдаемости для OpenClaw, а теперь измеряет **весь ваш флот агентов** в одной панели управления, автоматически определяя каждую среду выполнения на вашем компьютере:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw и NemoClaw бесплатны в приложении с открытым исходным кодом; остальные среды выполнения активируются с ClawMetry Cloud или самостоятельно размещённой лицензией Pro. Переключайте среды выполнения из заголовка, и каждая вкладка — стоимость, токены, инструменты, трассировки — перефокусируется на выбранную среду.

## Что вы получаете

- **Flow** — Живая анимированная диаграмма, показывающая прохождение сообщений через каналы, мозг, инструменты и обратно
- **Overview** — Проверки работоспособности, тепловая карта активности, количество сессий, информация о моделях
- **Usage** — Отслеживание токенов и стоимости с разбивкой по дням, неделям и месяцам
- **Sessions** — Активные сессии агента с моделью, токенами и последней активностью
- **Crons** — Запланированные задачи со статусом, временем следующего запуска и продолжительностью
- **Logs** — Цветное потоковое логирование в реальном времени
- **Memory** — Просмотр SOUL.md, MEMORY.md, AGENTS.md, ежедневных заметок
- **Transcripts** — Интерфейс в виде чат-пузырей для чтения истории сессий
- **Alerts** — Лимиты бюджета, триггеры по частоте ошибок, обнаружение отключения агента; маршрутизация в Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Блокировка опасных удалений, принудительных push-ов, мутаций БД, sudo, установки пакетов и сетевых вызовов за однокнопочным подтверждением

## Скриншоты

### 🧠 Brain — Живой поток событий агента
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Использование токенов и сводка по сессиям
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Поток вызовов инструментов в реальном времени
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Разбивка стоимости по моделям и сессиям
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Браузер файлов рабочей области
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Состояние безопасности и журнал аудита
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Лимиты бюджета, триггеры частоты ошибок, вебхуки в Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Блокировка рискованных вызовов инструментов за ручным подтверждением; правила защиты на основе политик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

**Из исходного кода:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Разработка фронтенда v2

Приложение v2 на React находится в `frontend/` и доступно по адресу `/v2` при запуске Flask-сервера с включённым v2.

Используйте два терминала в процессе разработки:

```bash
# Терминал 1: Flask API/сервер на :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Терминал 2: Vite dev-сервер на :5173
cd frontend
nvm use
npm ci
npm run dev
```

Откройте `http://localhost:5173/v2/`. Vite проксирует запросы `/api` на `http://localhost:8900`, поэтому React-приложение может обращаться к локальному Flask-серверу без дополнительной настройки CORS.

Чтобы собрать бандл, поставляемый вместе с Python-пакетом:

```bash
cd frontend
npm run build
```

Продакшн-бандл записывается в `clawmetry/static/v2/dist/`.

## Совместимость со средами выполнения / агентами

ClawMetry наблюдает за многими средами выполнения ИИ-агентов, а не только за OpenClaw. Для каждой среды выполнения, отличной от OpenClaw, поставляется специальный адаптер чтения, который преобразует её нативный формат сессий в унифицированные структуры ClawMetry; демон ingests их в одно хранилище DuckDB и облачный снимок с тегом среды выполнения, а вкладка воспроизведения сессий показывает **переключатель сред**, когда присутствует более одной. Полную матрицу совместимости и руководство по добавлению сред см. в [`docs/compatibility.md`](docs/compatibility.md), а введение в семейство OpenClaw — в [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md).

| Среда выполнения / Агент | Статус | Примечания |
|---|---|---|
| **OpenClaw** | Нативная | Эталонная среда, определяется автоматически |
| **PicoClaw** | Бета-адаптер | Плоский JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Транскрипты, модель, вызовы инструментов. |
| **NanoClaw** | Бета-адаптер | SQLite для каждой сессии (`data/v2-sessions`). Транскрипты и количество сообщений. |
| **Hermes** | Бета-адаптер | SQLite `~/.hermes/state.db`. Транскрипты, модель, токены/стоимость. |
| **Claude Code** | Бета-адаптер | JSONL `~/.claude/projects/.../<id>.jsonl`. Транскрипты, модель, вызовы инструментов + рассуждения, использование токенов. |
| **Codex** | Бета-адаптер | Rollout JSONL `~/.codex/sessions/...`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Cursor** | Бета-адаптер | SQLite `state.vscdb`. Транскрипты чата/composer, модель. |
| **Aider** | Бета-адаптер | `.aider.chat.history.md` для каждого проекта. Транскрипты, модель, счётчики токенов. |
| **Goose** | Бета-адаптер | SQLite `~/.local/share/goose`. Транскрипты, модель, вызовы инструментов, общее количество токенов. |
| **opencode** | Бета-адаптер | SQLite `~/.local/share/opencode`. Транскрипты, модель, вызовы инструментов, токены и стоимость. |
| **Qwen Code** | Бета-адаптер | JSONL `~/.qwen/projects/.../chats`. Транскрипты, модель, вызовы инструментов, использование токенов. |

«Бета-адаптер» означает, что ClawMetry поставляет читатель для реального формата данных на диске этой среды выполнения, каждый из которых создан и проверен на реальной установке на реальной машине (см. `tests/fixtures/runtimes/<rt>/`). Адаптеры доступны только для чтения; каждый честно отражает то, что его среда выполнения действительно записывает на диск (например, PicoClaw, NanoClaw и Cursor не записывают стоимость токенов на диск). Когда на одном узле работают несколько сред выполнения, переключатель сред ограничивает представление сессий одной из них для удобного углублённого анализа.

## Отслеживание любого SDK-агента — атрибуция стоимости вне основного цикла

Перечисленные выше среды выполнения записывают сессии на диск. Ваш собственный **продакшн-агент** — созданный на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B или простом цикле `httpx` — этого не делает. Перехватчик ClawMetry с нулевой настройкой всё равно фиксирует его LLM-вызовы (стоимость, токены, задержку, ошибки) с помощью monkey-patching `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (или переменная окружения `CLAWMETRY_SOURCE=support-agent`) помечает каждый вызов **именованным источником**, поэтому каждый запущенный вами продукт отображается как отдельная строка с атрибуцией стоимости в карточке **🔌 Out-loop sources** на странице Overview — вызовы, провайдеры, задержка, частота ошибок по агенту. Если источник не указан, вызовы всё равно отслеживаются, карточка просто остаётся скрытой.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Это тот же уровень данных, который питают адаптеры сред выполнения (DuckDB → облачный снимок), поэтому внешние источники синхронизируются с облачной панелью управления так же, как и всё остальное, с сквозным шифрованием.

## OpenTelemetry — нейтральный к вендору, отправка трассировок куда угодно

ClawMetry работает с **OpenTelemetry** в обоих направлениях, используя **семантические соглашения GenAI**, поэтому трассировки вашего агента никогда не привязаны к одному инструменту.

**Экспортируйте** каждую сессию — LLM-вызовы, инструменты, под-агенты, токены, стоимость — как OTLP/HTTP GenAI-спаны в любой коллектор (Datadog, Grafana, Honeycomb или ваш собственный OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Заголовки аутентификации и интервал опроса — необязательные переменные окружения:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Приём данных** — встроенный OTLP-приёмник принимает трассировки и метрики от любых источников по адресам `/v1/traces` и `/v1/metrics` (`pip install clawmetry[otel]` для приёма protobuf).

Вы получаете панель управления ClawMetry с нулевой настройкой и приоритетом локального хранения **и** ваши данные в том бэкенде, который уже использует ваша команда — без привязки к вендору, без установки второго агента.

## Настройка

Большинству пользователей настройка не нужна. ClawMetry автоматически определяет вашу рабочую область, логи, сессии и cron-задачи.

Если вам всё же нужна настройка:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Все параметры: `clawmetry --help`

## Поддерживаемые каналы

ClawMetry отображает живую активность для каждого настроенного канала OpenClaw. В диаграмме Flow отображаются только каналы, реально настроенные в вашем `openclaw.json` — ненастроенные скрываются автоматически.

Нажмите на любой узел канала в Flow, чтобы увидеть живой вид чат-пузырей с счётчиками входящих и исходящих сообщений.

| Канал | Статус | Живое всплывающее окно | Примечания |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Полный | ✅ | Сообщения, статистика, обновление каждые 10 с |
| 💬 **iMessage** | ✅ Полный | ✅ | Читает `~/Library/Messages/chat.db` напрямую |
| 💚 **WhatsApp** | ✅ Полный | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Полный | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Полный | ✅ | Определение guild и канала |
| 🟪 **Slack** | ✅ Полный | ✅ | Определение рабочей области и канала |
| 🌐 **Webchat** | ✅ Полный | ✅ | Встроенные сессии веб-интерфейса |
| 📡 **IRC** | ✅ Полный | ✅ | Интерфейс пузырей в стиле терминала |
| 🍏 **BlueBubbles** | ✅ Полный | ✅ | iMessage через BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Полный | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Полный | ✅ | Через плагин Teams bot |
| 🔷 **Mattermost** | ✅ Полный | ✅ | Самостоятельно размещённый командный чат |
| 🟩 **Matrix** | ✅ Полный | ✅ | Децентрализованный, поддержка E2EE |
| 🟢 **LINE** | ✅ Полный | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Полный | ✅ | Децентрализованные NIP-04 DM |
| 🟣 **Twitch** | ✅ Полный | ✅ | Чат через IRC-соединение |
| 🔷 **Feishu/Lark** | ✅ Полный | ✅ | Подписка на события через WebSocket |
| 🔵 **Zalo** | ✅ Полный | ✅ | Zalo Bot API |

> **Автоопределение:** ClawMetry читает ваш `~/.openclaw/openclaw.json` и отображает только реально настроенные каналы. Ручная настройка не требуется.

## Развёртывание с Docker

Хотите запустить ClawMetry в контейнере? Нет проблем! 🐳

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

> **Примечание:** При запуске в Docker примонтируйте директории с данными и логами вашего агента (например, `~/.openclaw`, `~/.claude`, `~/.codex`), чтобы ClawMetry мог автоматически определить вашу конфигурацию.

## Требования

- Python 3.8+
- Flask (устанавливается автоматически через pip)
- Среда выполнения ИИ-агента на том же компьютере: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw или PicoClaw (или примонтированные тома для Docker)
- Linux или macOS

## Поддержка NemoClaw / OpenShell

ClawMetry автоматически определяет [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративную обёртку NVIDIA для OpenClaw, запускающую агентов внутри изолированных контейнеров OpenShell.

В большинстве случаев дополнительная настройка не требуется. Демон синхронизации автоматически обнаруживает файлы сессий независимо от того, находятся ли они в `~/.openclaw/` на хосте или внутри контейнера OpenShell.

### Как это работает

ClawMetry определяет NemoClaw двумя способами:

1. **Обнаружение двоичного файла** — проверяет наличие CLI `nemoclaw` и выполняет `nemoclaw status` для получения информации о песочнице
2. **Обнаружение контейнера** — сканирует запущенные Docker-контейнеры на наличие образов `openshell`, `nemoclaw` или `ghcr.io/nvidia/`, затем читает сессии через монтирование томов или `docker cp`

Файлы сессий, синхронизированные из контейнеров NemoClaw, помечаются метаданными `runtime=nemoclaw` и `container_id` в облачной панели управления, чтобы их можно было с первого взгляда отличить от стандартных сессий OpenClaw.

### Рекомендуемая настройка: демон синхронизации на ХОСТЕ

Для лучшего опыта запускайте демон синхронизации ClawMetry на **хостовой машине** (не внутри песочницы). Это позволяет избежать ограничений сетевой политики NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Демон синхронизации автоматически найдёт сессии внутри любых запущенных контейнеров OpenShell.

### Необязательно: явное указание имени песочницы

Если автообнаружение не работает, укажите ClawMetry нужную песочницу:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Запуск внутри песочницы (для опытных пользователей)

Если вам необходимо запустить демон синхронизации **внутри** песочницы OpenShell, добавьте это правило исходящего трафика в сетевую политику NemoClaw, чтобы он мог достичь API приёма данных ClawMetry:

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

### Порты и конечные точки

| Конечная точка | Порт | Протокол | Обязательно |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Да (демон синхронизации → облако) |
| `localhost:8900` | 8900 | HTTP | Да (локальный интерфейс панели управления) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Для обнаружения сессий в контейнерах |

Демон синхронизации выполняет только исходящие HTTPS-вызовы к `ingest.clawmetry.com`. Входящие порты не требуются.

---

## Облачное развёртывание

См. **[Руководство по тестированию в облаке](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** по SSH-туннелям, обратному прокси и Docker.

## Тестирование

Этот проект тестируется с помощью BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрия

ClawMetry отправляет единственный анонимный пинг «первого запуска» на адрес `https://app.clawmetry.com/api/install` при первом запуске CLI `clawmetry` на новой машине. Мы используем это для подсчёта установок (единственная маркетинговая метрика, доступная нам как OSS-проекту) и для изучения того, какие фреймворки агентов установлены у наших пользователей.

**Ровно один POST на установку**, содержащий:

| Поле | Пример | Зачем |
|---|---|---|
| `install_id` | случайный UUID, хранящийся в `~/.clawmetry/install_id` | дедупликация; не связан с вашей почтой или api_key |
| `version` | `0.12.167` | какие версии используются |
| `os` / `os_version` | `Darwin` / `25.3.0` | приоритеты поддержки платформ |
| `python` | `3.11.15` | матрица поддержки версий Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | с какими агентами нам следует интегрироваться в первую очередь |
| `is_ci` / `ci_provider` | `true` / `github_actions` | разделение установок пользователями и CI-шумом |

**Что мы НЕ отправляем**: IP (облако определяет код страны на стороне сервера из запроса, затем удаляет IP), имя хоста, имя пользователя, путь к рабочей области, содержимое файлов, ваш api_key, вашу электронную почту, любые персональные данные или специфичные для рабочей области данные. Передаваемые данные можно проверить в [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Отказ** (любой из вариантов отключает телеметрию навсегда):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Сетевой сбой здесь никогда не блокирует запуск `clawmetry` — пинг отправляется в режиме «выстрелил и забыл» в отдельном потоке демона с таймаутом 3 с.

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
  <strong>🦞 Наблюдайте за мышлением агента</strong><br>
  <sub>Создано <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Часть экосистемы <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
