<!-- i18n-src:02b789586c7d -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Смотрите, как думает ваш агент.** Наблюдаемость в реальном времени для **14 сред выполнения ИИ-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 10 других. Один дашборд для всего вашего флота агентов.

> 🌐 **Читать на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Ноль настроек. Автоматически определяет всё.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**, и всё готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Работает с 14 средами выполнения агентов

ClawMetry начинался как инструмент наблюдаемости для OpenClaw, а теперь измеряет **весь ваш флот агентов** в одном дашборде, автоматически определяя каждую среду выполнения на вашей машине:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw и NemoClaw бесплатны в приложении с открытым исходным кодом; остальные среды выполнения включаются с ClawMetry Cloud или самостоятельно размещённой лицензией Pro. Переключайте среды выполнения в шапке, и каждая вкладка — стоимость, токены, инструменты, трассировки — заново привязывается к этой среде выполнения. См. **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** для точного разделения бесплатного/платного, матрицы тарифов, формы `/api/entitlement` и CLI `clawmetry license`.

## Что вы получаете

- **Flow** — живая анимированная диаграмма, показывающая, как сообщения проходят через каналы, мозг, инструменты и обратно
- **Overview** — проверки состояния, тепловая карта активности, количество сессий, информация о модели
- **Usage** — отслеживание токенов и стоимости с разбивкой по дням/неделям/месяцам
- **Sessions** — активные сессии агента с моделью, токенами, последней активностью
- **Crons** — запланированные задания со статусом, следующим запуском, длительностью
- **Logs** — цветная потоковая передача логов в реальном времени
- **Memory** — просмотр SOUL.md, MEMORY.md, AGENTS.md, ежедневных заметок
- **Transcripts** — интерфейс в виде чата для чтения истории сессий
- **Alerts** — лимиты бюджета, триггеры по частоте ошибок, обнаружение отключения агента; маршрутизация в Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — блокировка деструктивных удалений, принудительных push, изменений в БД, sudo, установок пакетов, сетевых вызовов за одним подтверждением в один клик

## Скриншоты

### 🧠 Brain — поток событий агента в реальном времени
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — использование токенов и сводка по сессиям
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — лента вызовов инструментов в реальном времени
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — разбивка стоимости по моделям и сессиям
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — обозреватель файлов рабочего пространства
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — состояние безопасности и журнал аудита
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — лимиты бюджета, триггеры по частоте ошибок, вебхуки в Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — блокировка рискованных вызовов инструментов за ручным подтверждением; правила защиты на основе политик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Блокировка перед выполнением для Claude Code** — одна команда устанавливает
хук PreToolUse, который приостанавливает подходящие вызовы инструментов *перед* их выполнением и ждёт
вашего решения (одно нажатие с телефона при включённых
[push-уведомлениях облака](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Отказ блокирует только этот один вызов инструмента — агент сохраняет свою сессию и может
попробовать другой подход. Одобрение с телефона пропускает собственный запрос на разрешение
Claude Code (вы уже ответили). Несовпадающие инструменты стоят ~40 мс и
переходят в обычный поток разрешений Claude Code. Вы также получаете push-уведомление на телефон, когда
сам Claude Code ждёт вас (уведомления `permission_prompt` /
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

**Из исходного кода:**
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

Чтобы собрать пакет, который поставляется с пакетом Python:

```bash
cd frontend
npm run build
```

Продакшн-сборка записывается в `clawmetry/static/v2/dist/`.

## Совместимость сред выполнения / агентов

ClawMetry наблюдает за многими средами выполнения ИИ-агентов, а не только за OpenClaw. Каждая среда выполнения, кроме OpenClaw, поставляется со специальным адаптером-читателем, который преобразует её нативный формат сессий в унифицированные форматы ClawMetry; демон загружает их в то же хранилище DuckDB + облачный снимок, помечая их средой выполнения, а вкладка воспроизведения сессий показывает **переключатель сред выполнения**, если присутствует более одной. См. [`docs/compatibility.md`](docs/compatibility.md) для полной матрицы + руководство по добавлению сред выполнения, и [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) для введения в семейство OpenClaw.

| Среда выполнения / агент | Статус | Примечания |
|---|---|---|
| **OpenClaw** | Нативная | Эталонная среда выполнения, определяется автоматически |
| **PicoClaw** | Бета-адаптер | Плоский JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Транскрипты, модель, вызовы инструментов. |
| **NanoClaw** | Бета-адаптер | SQLite для каждой сессии (`data/v2-sessions`). Транскрипты + количество сообщений. |
| **Hermes** | Бета-адаптер | SQLite `~/.hermes/state.db`. Транскрипты, модель, токены/стоимость. |
| **Claude Code** | Бета-адаптер | JSONL `~/.claude/projects/.../<id>.jsonl`. Транскрипты, модель, вызовы инструментов + размышления, использование токенов. |
| **Codex** | Бета-адаптер | Rollout JSONL `~/.codex/sessions/...`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Cursor** | Бета-адаптер | SQLite `state.vscdb`. Транскрипты чата/composer, модель. |
| **Aider** | Бета-адаптер | `.aider.chat.history.md` для каждого проекта. Транскрипты, модель, счётчики токенов. |
| **Goose** | Бета-адаптер | SQLite `~/.local/share/goose`. Транскрипты, модель, вызовы инструментов, общее число токенов. |
| **opencode** | Бета-адаптер | SQLite `~/.local/share/opencode`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Qwen Code** | Бета-адаптер | JSONL `~/.qwen/projects/.../chats`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Pi** | Бета-адаптер | JSONL `~/.pi/agent/sessions`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Deep Agents** | Бета-адаптер | SQLite `~/.deepagents/.state/sessions.db`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **n8n** | Бета-адаптер | SQLite `~/.n8n/database.sqlite`. Выполнения workflow, запуски узлов, подсказки AI Agent, модель + токены там, где n8n их фиксирует. |
| **Antigravity** | Бета-адаптер | Brain JSONL в `~/.gemini/<flavor>/brain/`. Диалоги, шаги инструментов, размышления, разбивка токенов Gemini по каждой генерации + стоимость, расход на фоновую генерацию. |

«Бета-адаптер» означает, что ClawMetry поставляет читатель для реального формата этой среды выполнения на диске, каждый из которых собран и проверен на реальной установке на реальной машине (см. `tests/fixtures/runtimes/<rt>/`). Адаптеры доступны только для чтения; каждый честен в отношении того, что реально хранит его среда выполнения (например, PicoClaw/NanoClaw/Cursor не записывают стоимость токенов на диск). Когда на одном узле работает несколько сред выполнения, переключатель сред выполнения ограничивает представление сессий одной средой для чистого глубокого анализа.

## Отслеживание любого SDK-агента — атрибуция затрат вне цикла

Все среды выполнения выше записывают сессии на диск. Ваш собственный **продакшн-агент** — тот, что вы построили на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B или на простом цикле `httpx` — этого не делает. Интерцептор ClawMetry без настройки всё равно захватывает его вызовы LLM (стоимость, токены, задержка, ошибки), подменяя `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (или переменная окружения `CLAWMETRY_SOURCE=support-agent`) помечает каждый вызов **именованным источником**, так что каждый продукт, который вы запускаете, отображается как отдельная полноценная строка с учётом стоимости в карточке **🔌 Внециклевые источники** на вкладке Overview дашборда — вызовы, провайдеры, задержка, частота ошибок для каждого агента. Источник не задан? Вызовы всё равно отслеживаются, карточка просто остаётся скрытой.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Это тот же слой данных, который питает адаптеры сред выполнения (DuckDB → облачный снимок), поэтому внециклевые источники синхронизируются с облачным дашбордом так же, как и всё остальное, со сквозным шифрованием.

## OpenTelemetry — независимость от поставщика, отправляйте свои трассировки куда угодно

ClawMetry говорит на **OpenTelemetry** в обоих направлениях, используя **семантические соглашения GenAI**, поэтому трассировки вашего агента никогда не привязаны к одному инструменту.

**Экспорт** каждой сессии — вызовы LLM, инструменты, суб-агенты, токены, стоимость — в виде спанов OTLP/HTTP GenAI в любой коллектор (Datadog, Grafana, Honeycomb или ваш собственный OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Заголовки авторизации и интервал опроса являются опциональными переменными окружения:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Приём** — встроенный приёмник OTLP принимает трассировки и метрики от чего угодно ещё по адресам `/v1/traces` и `/v1/metrics` (`pip install clawmetry[otel]` для приёма protobuf).

Вы получаете дашборд ClawMetry без настройки, локальный по умолчанию, **и** свои данные в любом бэкенде, который уже использует ваша команда — без привязки к поставщику, без второго агента для установки.

## Конфигурация

Большинству людей вообще не нужна никакая настройка. ClawMetry автоматически определяет ваше рабочее пространство, логи, сессии и cron-задания.

Если вам всё же нужно что-то настроить:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Все опции: `clawmetry --help`

## Поддерживаемые каналы

ClawMetry показывает активность в реальном времени для каждого настроенного вами канала OpenClaw. Только каналы, которые действительно настроены в вашем `openclaw.json`, отображаются на диаграмме Flow — ненастроенные автоматически скрываются.

Нажмите на любой узел канала на диаграмме Flow, чтобы увидеть всплывающее окно чата в реальном времени со счётчиками входящих/исходящих сообщений.

| Канал | Статус | Живое всплывающее окно | Примечания |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Полная | ✅ | Сообщения, статистика, обновление каждые 10 с |
| 💬 **iMessage** | ✅ Полная | ✅ | Читает `~/Library/Messages/chat.db` напрямую |
| 💚 **WhatsApp** | ✅ Полная | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Полная | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Полная | ✅ | Определение гильдии + канала |
| 🟪 **Slack** | ✅ Полная | ✅ | Определение рабочего пространства + канала |
| 🌐 **Webchat** | ✅ Полная | ✅ | Встроенные веб-сессии |
| 📡 **IRC** | ✅ Полная | ✅ | Интерфейс в стиле терминала |
| 🍏 **BlueBubbles** | ✅ Полная | ✅ | iMessage через REST API BlueBubbles |
| 🔵 **Google Chat** | ✅ Полная | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Полная | ✅ | Через плагин бота Teams |
| 🔷 **Mattermost** | ✅ Полная | ✅ | Самостоятельно размещённый командный чат |
| 🟩 **Matrix** | ✅ Полная | ✅ | Децентрализованный, поддержка E2EE |
| 🟢 **LINE** | ✅ Полная | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Полная | ✅ | Децентрализованные личные сообщения NIP-04 |
| 🟣 **Twitch** | ✅ Полная | ✅ | Чат через подключение IRC |
| 🔷 **Feishu/Lark** | ✅ Полная | ✅ | Подписка на события через WebSocket |
| 🔵 **Zalo** | ✅ Полная | ✅ | Zalo Bot API |

> **Автоопределение:** ClawMetry читает ваш `~/.openclaw/openclaw.json` и отображает только те каналы, которые вы действительно настроили. Ручная настройка не требуется.

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

> **Примечание:** При запуске в Docker подключите каталоги данных + логов вашего агента (например, `~/.openclaw`, `~/.claude`, `~/.codex`), чтобы ClawMetry мог автоматически определить вашу настройку.

## Требования

- Python 3.8+
- Flask (устанавливается автоматически через pip)
- Среда выполнения ИИ-агента на той же машине: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n или Antigravity (или подключённые тома для Docker)
- Linux или macOS

## Поддержка NemoClaw / OpenShell

ClawMetry автоматически определяет [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративную обёртку безопасности NVIDIA для OpenClaw, которая запускает агентов внутри изолированных контейнеров OpenShell.

В большинстве случаев дополнительная настройка не требуется. Демон синхронизации автоматически обнаруживает файлы сессий независимо от того, находятся ли они в `~/.openclaw/` на хосте или внутри контейнера OpenShell.

### Как это работает

ClawMetry определяет NemoClaw двумя способами:

1. **Определение по бинарнику** — проверяет наличие CLI `nemoclaw` и запускает `nemoclaw status`, чтобы получить информацию о песочнице
2. **Определение по контейнеру** — сканирует запущенные контейнеры Docker на предмет образов `openshell`, `nemoclaw` или `ghcr.io/nvidia/`, затем читает сессии через подключённые тома или `docker cp`

Файлы сессий, синхронизированные из контейнеров NemoClaw, помечаются метаданными `runtime=nemoclaw` и `container_id` в облачном дашборде, так что вы можете отличить их от стандартных сессий OpenClaw с первого взгляда.

### Рекомендуемая настройка: демон синхронизации на ХОСТЕ

Для наилучшего впечатления запускайте демон синхронизации ClawMetry на **хост-машине** (а не внутри песочницы). Это позволяет избежать ограничений сетевой политики NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Демон синхронизации автоматически найдёт сессии внутри любых запущенных контейнеров OpenShell.

### Опционально: явное имя песочницы

Если автоопределение не работает, укажите ClawMetry нужную песочницу:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Запуск внутри песочницы (продвинутый вариант)

Если вам нужно запустить демон синхронизации **внутри** песочницы OpenShell, добавьте это правило исходящего трафика в вашу сетевую политику NemoClaw, чтобы он мог обращаться к API приёма ClawMetry:

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
| `localhost:8900` | 8900 | HTTP | Да (локальный интерфейс дашборда) |
| Сокет Docker (`/var/run/docker.sock`) | — | Unix-сокет | Для обнаружения сессий в контейнерах |

Демон синхронизации выполняет только исходящие вызовы HTTPS к `ingest.clawmetry.com`. Входящие порты не требуются.

---

## Развёртывание в облаке

См. **[руководство по тестированию в облаке](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** для SSH-туннелей, обратного прокси и Docker.

## Тестирование

Этот проект тестируется с помощью BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрия

ClawMetry отправляет анонимные пинги о жизненном цикле установки на
`https://app.clawmetry.com/api/install`: один пинг `install` при первом
запуске CLI `clawmetry` на новой машине, один пинг `update`
при первом запуске после обновления до новой версии, и один пинг `onboarded`,
когда вы завершаете выбор при первом знакомстве в дашборде. Мы используем это,
чтобы подсчитать реальные установки (необработанные цифры загрузок PyPI на ~98% состоят из зеркал, CI
и повторных загрузок при автообновлении), а также узнать, какие фреймворки агентов и
версии реально используются.

**Максимум один POST-запрос на событие жизненного цикла на версию**, содержащий:

| Поле | Пример | Зачем |
|---|---|---|
| `install_id` | случайный UUID, хранящийся в `~/.clawmetry/install_id` | дедупликация; анонимно, пока вы явно не подключите облачную синхронизацию (после этого аутентифицированный heartbeat демона несёт этот идентификатор, связывая эту установку с вашим аккаунтом) |
| `event` | `install` / `update` / `onboarded` | новая установка или обновление существующей |
| `version` | `0.12.167` | какие версии используются |
| `os` / `os_version` | `Darwin` / `25.3.0` | приоритеты поддержки платформ |
| `python` | `3.11.15` | матрица поддержки версий Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | с какими агентами нам стоит интегрироваться дальше |
| `is_ci` / `ci_provider` | `true` / `github_actions` | отделение установок реальными людьми от шума CI |

**Чего мы НЕ отправляем**: IP (облако определяет код страны на стороне сервера
из запроса, затем отбрасывает IP), имя хоста, имя пользователя, путь к рабочему
пространству, содержимое файлов, ваш api_key, вашу почту, ничего личного или
относящегося к рабочему пространству. Передаваемая полезная нагрузка доступна для проверки в
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Отказаться** (любой из этих способов отключает её навсегда):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Сбой сети здесь никогда не блокирует работу `clawmetry` — пинг
отправляется в режиме fire-and-forget в потоке демона с тайм-аутом 3 с.

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
