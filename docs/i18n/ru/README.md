<!-- i18n-src:8f42d460a973 -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Смотрите, как думает ваш агент.** Наблюдаемость в реальном времени для **14 сред выполнения AI-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 10 других. Единая панель для всего вашего флота агентов.

> 🌐 **Читайте на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Никаких настроек. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**, и всё готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Работает с 14 средами выполнения агентов

ClawMetry начинался как инструмент наблюдаемости для OpenClaw, а теперь измеряет **весь ваш флот агентов** в единой панели, автоматически определяя каждую среду выполнения на вашей машине:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw и NemoClaw доступны бесплатно в приложении с открытым исходным кодом; остальные среды выполнения открываются с ClawMetry Cloud или самостоятельно размещённой лицензией Pro. Переключайте среды выполнения из шапки, и каждая вкладка — стоимость, токены, инструменты, трассировки — пересчитывается для этой среды. См. **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** для точного разделения на бесплатные/платные функции, матрицы уровней, структуры `/api/entitlement` и CLI `clawmetry license`.

## Что вы получаете

- **Flow** — живая анимированная диаграмма, показывающая, как сообщения проходят через каналы, «мозг», инструменты и обратно
- **Overview** — проверки состояния, тепловая карта активности, счётчики сессий, информация о модели
- **Usage** — отслеживание токенов и стоимости с разбивкой по дням/неделям/месяцам
- **Sessions** — активные сессии агента с указанием модели, токенов, последней активности
- **Crons** — запланированные задачи со статусом, временем следующего запуска, длительностью
- **Logs** — цветная потоковая передача логов в реальном времени
- **Memory** — просмотр SOUL.md, MEMORY.md, AGENTS.md, ежедневных заметок
- **Transcripts** — интерфейс в виде чат-пузырей для чтения истории сессий
- **Alerts** — лимиты бюджета, триггеры по частоте ошибок, обнаружение офлайн-состояния агента; маршрутизация в Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — блокировка разрушительных удалений, принудительных push, изменений БД, sudo, установок пакетов, сетевых вызовов до получения подтверждения в один клик

## Скриншоты

### 🧠 Brain — живой поток событий агента
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — использование токенов и сводка по сессиям
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — лента вызовов инструментов в реальном времени
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — разбивка стоимости по моделям и сессиям
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — обозреватель файлов рабочего пространства
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — состояние защищённости и журнал аудита
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — лимиты бюджета, триггеры по частоте ошибок, вебхуки в Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — блокировка рискованных вызовов инструментов до ручного подтверждения; правила защиты на основе политик
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

**Из исходников:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Разработка фронтенда v2

React-приложение v2 находится в `frontend/` и обслуживается по адресу `/v2`, когда
сервер Flask запущен с включённым v2.

При разработке используйте два терминала:

```bash
# Терминал 1: Flask API/сервер на :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Терминал 2: сервер разработки Vite на :5173
cd frontend
nvm use
npm ci
npm run dev
```

Откройте `http://localhost:5173/v2/`. Vite проксирует запросы `/api` на
`http://localhost:8900`, поэтому React-приложение может общаться с локальным сервером Flask
без дополнительной настройки CORS.

Чтобы собрать бандл, который поставляется вместе с пакетом Python:

```bash
cd frontend
npm run build
```

Продакшн-бандл записывается в `clawmetry/static/v2/dist/`.

## Совместимость со средами выполнения / агентами

ClawMetry наблюдает за многими средами выполнения AI-агентов, а не только за OpenClaw. Каждая среда выполнения, отличная от OpenClaw, поставляется со специальным адаптером-читателем, который преобразует её нативный формат сессий в унифицированные структуры ClawMetry; демон загружает их в то же хранилище DuckDB + облачный снапшот с пометкой среды выполнения, а вкладка воспроизведения сессий показывает **переключатель сред выполнения**, если их присутствует больше одной. См. [`docs/compatibility.md`](docs/compatibility.md) для полной матрицы и руководства по добавлению сред выполнения, а также [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) для введения в семейство OpenClaw.

| Среда выполнения / агент | Статус | Примечания |
|---|---|---|
| **OpenClaw** | Нативная | Эталонная среда выполнения, определяется автоматически |
| **PicoClaw** | Бета-адаптер | Плоский JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Транскрипты, модель, вызовы инструментов. |
| **NanoClaw** | Бета-адаптер | SQLite на сессию (`data/v2-sessions`). Транскрипты + счётчики сообщений. |
| **Hermes** | Бета-адаптер | SQLite `~/.hermes/state.db`. Транскрипты, модель, токены/стоимость. |
| **Claude Code** | Бета-адаптер | JSONL `~/.claude/projects/.../<id>.jsonl`. Транскрипты, модель, вызовы инструментов + размышления, использование токенов. |
| **Codex** | Бета-адаптер | Rollout JSONL `~/.codex/sessions/...`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Cursor** | Бета-адаптер | SQLite `state.vscdb`. Транскрипты чата/composer, модель. |
| **Aider** | Бета-адаптер | `.aider.chat.history.md` для каждого проекта. Транскрипты, модель, счётчики токенов. |
| **Goose** | Бета-адаптер | SQLite `~/.local/share/goose`. Транскрипты, модель, вызовы инструментов, итоговые токены. |
| **opencode** | Бета-адаптер | SQLite `~/.local/share/opencode`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Qwen Code** | Бета-адаптер | JSONL `~/.qwen/projects/.../chats`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Pi** | Бета-адаптер | JSONL `~/.pi/agent/sessions`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Deep Agents** | Бета-адаптер | SQLite `~/.deepagents/.state/sessions.db`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |

«Бета-адаптер» означает, что ClawMetry поставляет читатель реального формата данных на диске для этой среды выполнения, каждый из которых создан и проверен на реальной установке на реальной машине (см. `tests/fixtures/runtimes/<rt>/`). Адаптеры доступны только для чтения; каждый из них честно отражает то, что среда выполнения фактически хранит (например, PicoClaw/NanoClaw/Cursor не записывают стоимость токенов на диск). Когда на одном узле работает несколько сред выполнения, переключатель сред выполнения сужает представление сессий до одной для чистого глубокого анализа.

## Отслеживание любого SDK-агента — учёт стоимости вне цикла

Все перечисленные выше среды выполнения записывают сессии на диск. Ваш собственный **продакшн-агент** — тот, что вы собрали на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B или на обычном цикле `httpx` — этого не делает. Перехватчик ClawMetry с нулевой настройкой всё равно захватывает его вызовы LLM (стоимость, токены, задержка, ошибки), подменяя `httpx`/`requests`:

```python
import clawmetry.track            # активировать перехватчик
clawmetry.track.set_source("support-agent")   # назвать этот продукт

# ...ваш агент работает как обычно; каждый вызов LLM теперь отслеживается + учитывается.
```

`set_source()` (или переменная окружения `CLAWMETRY_SOURCE=support-agent`) помечает каждый вызов **именованным источником**, поэтому каждый продукт, который вы запускаете, отображается как собственная полноценная строка с учётом стоимости в карточке **🔌 Внецикловые источники** на вкладке Overview — вызовы, провайдеры, задержка, частота ошибок для каждого агента. Источник не задан? Вызовы всё равно отслеживаются, просто карточка остаётся скрытой.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Это тот же слой данных, который питают адаптеры сред выполнения (DuckDB → облачный снапшот), поэтому внецикловые источники синхронизируются с облачной панелью так же, как и всё остальное, со сквозным шифрованием.

## OpenTelemetry — независимость от вендора, отправляйте трассировки куда угодно

ClawMetry говорит на языке **OpenTelemetry** в обоих направлениях, используя **семантические соглашения GenAI**, поэтому трассировки вашего агента никогда не привязаны к одному инструменту.

**Экспортируйте** каждую сессию — вызовы LLM, инструменты, суб-агенты, токены, стоимость — как span'ы OTLP/HTTP GenAI в любой коллектор (Datadog, Grafana, Honeycomb или ваш собственный OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# эквивалентно:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Заголовки авторизации и интервал опроса — необязательные переменные окружения:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # дополнительные HTTP-заголовки
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # секунды (по умолчанию 60)
```

**Импортируйте** — встроенный приёмник OTLP принимает трассировки и метрики от чего угодно ещё по адресам `/v1/traces` и `/v1/metrics` (`pip install clawmetry[otel]` для приёма protobuf).

Вы получаете панель ClawMetry с нулевой настройкой, работающую в первую очередь локально, **и** свои данные в любом бэкенде, который уже использует ваша команда — без привязки к вендору, без второго агента для установки.

## Конфигурация

Большинству людей не нужна никакая настройка. ClawMetry автоматически определяет ваше рабочее пространство, логи, сессии и cron-задачи.

Если вам всё же нужна настройка:

```bash
clawmetry --port 9000              # Пользовательский порт (по умолчанию: 8900)
clawmetry --host 127.0.0.1         # Привязка только к localhost
clawmetry --workspace ~/mybot      # Пользовательский путь к рабочему пространству
clawmetry --name "Alice"           # Ваше имя на визуализации Flow
```

Все опции: `clawmetry --help`

## Поддерживаемые каналы

ClawMetry показывает активность в реальном времени для каждого настроенного вами канала OpenClaw. В диаграмме Flow отображаются только те каналы, которые действительно настроены в вашем `openclaw.json` — ненастроенные автоматически скрываются.

Нажмите на любой узел канала во Flow, чтобы увидеть живое всплывающее окно чата со счётчиками входящих/исходящих сообщений.

| Канал | Статус | Живое всплывающее окно | Примечания |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Полная | ✅ | Сообщения, статистика, обновление каждые 10 с |
| 💬 **iMessage** | ✅ Полная | ✅ | Читает `~/Library/Messages/chat.db` напрямую |
| 💚 **WhatsApp** | ✅ Полная | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Полная | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Полная | ✅ | Определение гильдии + канала |
| 🟪 **Slack** | ✅ Полная | ✅ | Определение рабочего пространства + канала |
| 🌐 **Webchat** | ✅ Полная | ✅ | Встроенные сессии веб-интерфейса |
| 📡 **IRC** | ✅ Полная | ✅ | Интерфейс в стиле терминала |
| 🍏 **BlueBubbles** | ✅ Полная | ✅ | iMessage через REST API BlueBubbles |
| 🔵 **Google Chat** | ✅ Полная | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Полная | ✅ | Через плагин бота Teams |
| 🔷 **Mattermost** | ✅ Полная | ✅ | Самостоятельно размещаемый командный чат |
| 🟩 **Matrix** | ✅ Полная | ✅ | Децентрализованный, с поддержкой E2EE |
| 🟢 **LINE** | ✅ Полная | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Полная | ✅ | Децентрализованные личные сообщения NIP-04 |
| 🟣 **Twitch** | ✅ Полная | ✅ | Чат через подключение IRC |
| 🔷 **Feishu/Lark** | ✅ Полная | ✅ | Подписка на события через WebSocket |
| 🔵 **Zalo** | ✅ Полная | ✅ | Zalo Bot API |

> **Автоматическое определение:** ClawMetry читает ваш `~/.openclaw/openclaw.json` и отображает только те каналы, которые вы действительно настроили. Ручная настройка не требуется.

## Развёртывание в Docker

Хотите запустить ClawMetry в контейнере? Не проблема! 🐳

**Быстрый старт с Docker:**

```bash
# Сборка образа
docker build -t clawmetry .

# Запуск с настройками по умолчанию
docker run -p 8900:8900 clawmetry

# Или подключите каталог данных вашего агента (показано: ~/.openclaw для OpenClaw)
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

> **Примечание:** При запуске в Docker подключайте каталоги данных и логов вашего агента (например, `~/.openclaw`, `~/.claude`, `~/.codex`), чтобы ClawMetry мог автоматически определить вашу конфигурацию.

## Требования

- Python 3.8+
- Flask (устанавливается автоматически через pip)
- Среда выполнения AI-агента на той же машине: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi или Deep Agents (либо подключённые тома для Docker)
- Linux или macOS

## Поддержка NemoClaw / OpenShell

ClawMetry автоматически определяет [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративную обёртку безопасности NVIDIA для OpenClaw, которая запускает агентов внутри изолированных контейнеров OpenShell.

В большинстве случаев дополнительная настройка не требуется. Демон синхронизации автоматически обнаруживает файлы сессий независимо от того, находятся ли они в `~/.openclaw/` на хосте или внутри контейнера OpenShell.

### Как это работает

ClawMetry определяет NemoClaw двумя способами:

1. **Определение по бинарному файлу** — проверяет наличие CLI `nemoclaw` и запускает `nemoclaw status`, чтобы получить информацию о песочнице
2. **Определение по контейнеру** — сканирует запущенные контейнеры Docker на предмет образов `openshell`, `nemoclaw` или `ghcr.io/nvidia/`, затем читает сессии через подключённые тома или `docker cp`

Файлы сессий, синхронизированные из контейнеров NemoClaw, помечаются метаданными `runtime=nemoclaw` и `container_id` в облачной панели, чтобы вы могли отличить их от стандартных сессий OpenClaw с первого взгляда.

### Рекомендуемая настройка: демон синхронизации на ХОСТЕ

Для наилучшего опыта запускайте демон синхронизации ClawMetry на **хост-машине** (а не внутри песочницы). Это позволяет избежать ограничений сетевой политики NemoClaw.

```bash
# На хосте (вне песочницы)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Демон синхронизации автоматически найдёт сессии внутри любых запущенных контейнеров OpenShell.

### Опционально: явное имя песочницы

Если автоматическое определение не работает, укажите ClawMetry нужную песочницу:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Запуск внутри песочницы (для продвинутых пользователей)

Если вам необходимо запускать демон синхронизации **внутри** песочницы OpenShell, добавьте это правило исходящего трафика в вашу сетевую политику NemoClaw, чтобы он мог обращаться к API приёма ClawMetry:

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

### Порты и эндпоинты

| Эндпоинт | Порт | Протокол | Требуется |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Да (демон синхронизации → облако) |
| `localhost:8900` | 8900 | HTTP | Да (локальный интерфейс панели) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Для обнаружения сессий контейнера |

Демон синхронизации выполняет только исходящие вызовы HTTPS к `ingest.clawmetry.com`. Входящие порты не требуются.

---

## Облачное развёртывание

См. **[Руководство по тестированию в облаке](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** для SSH-туннелей, обратного прокси и Docker.

## Тестирование

Этот проект тестируется с помощью BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрия

ClawMetry отправляет один анонимный пинг «первого запуска» на
`https://app.clawmetry.com/api/install` при первом запуске CLI
`clawmetry` на новой машине. Мы используем это для подсчёта установок (единственной
маркетинговой метрики, доступной для проекта с открытым исходным кодом) и чтобы узнать, какие
фреймворки агентов установлены у наших пользователей.

**Ровно один POST-запрос на установку**, содержащий:

| Поле | Пример | Зачем |
|---|---|---|
| `install_id` | случайный UUID, сохранённый в `~/.clawmetry/install_id` | дедупликация; не привязан к вашей почте или api_key |
| `version` | `0.12.167` | какие версии используются в реальности |
| `os` / `os_version` | `Darwin` / `25.3.0` | приоритеты поддержки платформ |
| `python` | `3.11.15` | матрица поддержки версий Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | с какими агентами нам следует интегрироваться дальше |
| `is_ci` / `ci_provider` | `true` / `github_actions` | отделение установок реальными людьми от шума CI |

**Что мы НЕ отправляем**: IP-адрес (облако определяет код страны на стороне сервера
из запроса, а затем отбрасывает IP), имя хоста, имя пользователя, путь к рабочему
пространству, содержимое файлов, ваш api_key, вашу почту, что-либо содержащее личные данные или
специфичное для рабочего пространства. Формат передаваемых данных можно проверить в
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Отказаться** (любой из этих способов отключает телеметрию навсегда):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # для текущей оболочки
export DO_NOT_TRACK=1                          # кросс-инструментальный стандарт W3C
touch ~/.clawmetry/notelemetry                 # постоянный файловый маркер
```

Сбой сети здесь никогда не блокирует запуск `clawmetry` — пинг
отправляется по принципу «выстрелил и забыл» в фоновом потоке с тайм-аутом 3 с.

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
  <sub>Создано <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · часть экосистемы <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
