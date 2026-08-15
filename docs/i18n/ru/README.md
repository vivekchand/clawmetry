<!-- i18n-src:c422fb7dd0da -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Смотрите, как думает ваш агент.** Наблюдаемость в реальном времени для **20 рантаймов ИИ-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 16. Единая панель для всего вашего парка агентов.

> 🌐 **Читать на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Ноль конфигурации. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**, и всё готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Работает с 20 рантаймами агентов

ClawMetry начинался как инструмент наблюдаемости для OpenClaw, а теперь ведёт учёт **всего вашего парка агентов** в единой панели, автоматически определяя каждый рантайм на вашей машине:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw и NemoClaw бесплатны в приложении с открытым исходным кодом; остальные рантаймы становятся доступны с ClawMetry Cloud или с лицензией Pro для самостоятельного хостинга. Переключайте рантаймы из шапки — и каждая вкладка (стоимость, токены, инструменты, трассировки) переключится на область этого рантайма. Подробности о точном разделении бесплатных и платных функций, матрице тарифов, форме `/api/entitlement` и CLI `clawmetry license` см. в **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**.

## Что вы получаете

- **Flow** — живая анимированная диаграмма, показывающая, как сообщения проходят через каналы, "мозг", инструменты и обратно
- **Overview** — проверки состояния, тепловая карта активности, счётчики сессий, информация о моделях
- **Usage** — учёт токенов и стоимости с разбивкой по дням/неделям/месяцам
- **Sessions** — активные сессии агентов с моделью, токенами, временем последней активности
- **Crons** — запланированные задачи со статусом, временем следующего запуска, длительностью
- **Logs** — цветная потоковая передача логов в реальном времени
- **Memory** — просмотр SOUL.md, MEMORY.md, AGENTS.md, ежедневных заметок
- **Transcripts** — интерфейс в виде чата для чтения истории сессий
- **Alerts** — лимиты бюджета, триггеры по частоте ошибок, обнаружение офлайн-агентов; уведомления в Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — блокировка деструктивных удалений, принудительных push, изменений в БД, sudo, установок пакетов, сетевых вызовов до подтверждения в один клик

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

### 🔐 Security — состояние защищённости и журнал аудита
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — лимиты бюджета, триггеры по частоте ошибок, вебхуки в Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — блокировка рискованных вызовов инструментов до ручного подтверждения; правила защиты на основе политик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Блокировка до выполнения для Claude Code** — одна команда устанавливает
хук PreToolUse, который приостанавливает подходящие вызовы инструментов *до* их выполнения и ждёт
вашего решения (одно нажатие с телефона при включённых
[облачных push-уведомлениях](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Отказ блокирует только этот конкретный вызов инструмента — сессия агента сохраняется, и он может
попробовать другой подход. Подтверждение с телефона пропускает собственный
запрос разрешения Claude Code (вы уже ответили). Несовпадающие инструменты стоят ~40 мс и
переходят к обычному процессу подтверждения разрешений Claude Code. Вы также получаете push-уведомление на телефон, когда
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

**Из исходного кода:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Разработка фронтенда v2

Приложение React v2 находится в `frontend/` и обслуживается по адресу `/v2`, когда
сервер Flask запущен с включённым v2.

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
`http://localhost:8900`, поэтому приложение React может обращаться к локальному серверу Flask
без дополнительной настройки CORS.

Чтобы собрать бандл, который поставляется вместе с пакетом Python:

```bash
cd frontend
npm run build
```

Продакшн-бандл записывается в `clawmetry/static/v2/dist/`.

## Совместимость рантаймов / агентов

ClawMetry наблюдает за многими рантаймами ИИ-агентов, а не только за OpenClaw. Для каждого рантайма, отличного от OpenClaw, поставляется отдельный адаптер-читатель, который преобразует его нативный формат сессий в унифицированные формы ClawMetry; демон загружает их в то же хранилище DuckDB + облачный снапшот, помечая рантаймом, а вкладка воспроизведения сессий показывает **переключатель рантайма**, когда их присутствует больше одного. Полную матрицу и руководство по добавлению рантаймов см. в [`docs/compatibility.md`](docs/compatibility.md), а азы семейства OpenClaw — в [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md).

Используете инструмент безопасности агентов [Perplexity numbat](https://github.com/perplexityai/numbat)? ClawMetry сразу же принимает его находки и решения по применению политик — см. [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Рантайм / агент | Статус | Примечания |
|---|---|---|
| **OpenClaw** | Нативный | Эталонный рантайм, определяется автоматически |
| **PicoClaw** | Бета-адаптер | Плоский JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Транскрипты, модель, вызовы инструментов. |
| **NanoClaw** | Бета-адаптер | SQLite на сессию (`data/v2-sessions`). Транскрипты + количество сообщений. |
| **Hermes** | Бета-адаптер | SQLite `~/.hermes/state.db`. Транскрипты, модель, токены/стоимость. |
| **Claude Code** | Бета-адаптер | JSONL `~/.claude/projects/.../<id>.jsonl`. Транскрипты, модель, вызовы инструментов + рассуждения, использование токенов. |
| **Codex** | Бета-адаптер | Rollout JSONL `~/.codex/sessions/...`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Cursor** | Бета-адаптер | SQLite `state.vscdb`. Транскрипты чата/composer, модель. |
| **Aider** | Бета-адаптер | `.aider.chat.history.md` на проект. Транскрипты, модель, счётчики токенов. |
| **Goose** | Бета-адаптер | SQLite `~/.local/share/goose`. Транскрипты, модель, вызовы инструментов, итоги по токенам. |
| **opencode** | Бета-адаптер | SQLite `~/.local/share/opencode`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Qwen Code** | Бета-адаптер | JSONL `~/.qwen/projects/.../chats`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Pi** | Бета-адаптер | JSONL `~/.pi/agent/sessions`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Deep Agents** | Бета-адаптер | SQLite `~/.deepagents/.state/sessions.db`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **n8n** | Бета-адаптер | SQLite `~/.n8n/database.sqlite`. Выполнения рабочих процессов, запуски узлов, промпты AI Agent, модель + токены там, где n8n их фиксирует. |
| **Antigravity** | Бета-адаптер | Brain JSONL в `~/.gemini/<flavor>/brain/`. Диалоги, шаги инструментов, рассуждения, разбивка токенов Gemini по каждой генерации + стоимость, расход на фоновую генерацию. |
| **GitHub Copilot** | Бета-адаптер | `events.jsonl` Copilot CLI в `~/.copilot/session-state/` + реестр использования по вызовам `session-store.db`. Диалоги, вызовы инструментов, маршрутизация моделей, разбивка токенов с учётом кеша, стоимость в AI-кредитах, выставляемых поставщиком. |
| **Grok** | Бета-адаптер | xAI Grok Build CLI (бинарник на Rust в `~/.grok/bin/grok`): глобальный журнал событий `~/.grok/logs/unified.jsonl` + пер-сессионные `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. Диалоги, разбивка токенов по репликам, маршрутизация моделей и исходящая полезная нагрузка репозитория CLI, помещаемая в очередь `~/.grok/upload_queue/`, чтобы вы видели, что покинуло вашу машину. |

"Бета-адаптер" означает, что ClawMetry поставляет читатель для реального формата хранения этого рантайма на диске, каждый из которых собран и проверен на реальной установке на реальной машине (см. `tests/fixtures/runtimes/<rt>/`). Адаптеры доступны только для чтения; каждый честно отражает то, что рантайм реально хранит (например, PicoClaw/NanoClaw/Cursor не записывают стоимость токенов на диск). Когда на одном узле работает несколько рантаймов, переключатель рантайма сужает представление сессий до одного для чистого погружения.

## Отслеживание любого SDK-агента — учёт стоимости вне цикла

Все перечисленные выше рантаймы записывают сессии на диск. Ваш собственный **продакшн-агент** — тот, что вы построили на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B или на обычном цикле `httpx` — этого не делает. Интерцептор ClawMetry без конфигурации всё равно перехватывает его LLM-вызовы (стоимость, токены, задержка, ошибки), подменяя `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (или переменная окружения `CLAWMETRY_SOURCE=support-agent`) помечает каждый вызов **именованным источником**, поэтому каждый продукт, который вы запускаете, отображается как отдельная полноценная строка с учётом стоимости на карточке **🔌 Источники вне цикла** вкладки Overview панели — вызовы, поставщики, задержка, частота ошибок по каждому агенту. Источник не задан? Вызовы всё равно отслеживаются, просто карточка остаётся скрытой.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Это тот же слой данных, который питают адаптеры рантаймов (DuckDB → облачный снапшот), поэтому источники вне цикла синхронизируются с облачной панелью так же, как и всё остальное, со сквозным шифрованием.

## OpenTelemetry — независимость от поставщика, отправляйте трассировки куда угодно

ClawMetry говорит на **OpenTelemetry** в обе стороны, используя **семантические соглашения GenAI**, поэтому трассировки вашего агента никогда не привязаны к одному инструменту.

**Экспорт** каждой сессии — вызовы LLM, инструменты, суб-агенты, токены, стоимость — в виде спанов OTLP/HTTP GenAI в любой коллектор (Datadog, Grafana, Honeycomb или ваш собственный OTel Collector):

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

**Приём** — встроенный приёмник OTLP принимает трассировки, логи и метрики от чего угодно ещё по адресам `/v1/traces`, `/v1/logs` и `/v1/metrics`. Направьте на него любое приложение с инструментацией OpenTelemetry:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

Приём трассировок и логов в формате OTLP/JSON работает при обычном `pip install clawmetry`, без дополнений. Приём Protobuf (и метрик OTLP/JSON) требует `pip install clawmetry[otel]`. Приложение, которое задаёт собственное `service.name`, отображается как отдельный агент в переключателе рантайма, со своей стоимостью и токенами.

Вы получаете панель ClawMetry без конфигурации, локальную по умолчанию, **и** свои данные в любом бэкенде, который уже использует ваша команда — без привязки к поставщику, без установки второго агента.

## Конфигурация

Большинству людей конфигурация вообще не нужна. ClawMetry автоматически определяет ваше рабочее пространство, логи, сессии и cron-задачи.

Если вам всё же нужна настройка:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Все опции: `clawmetry --help`

## Поддерживаемые каналы

ClawMetry показывает живую активность для каждого настроенного вами канала OpenClaw. Только каналы, реально настроенные в вашем `openclaw.json`, отображаются на диаграмме Flow — ненастроенные автоматически скрываются.

Нажмите на любой узел канала во Flow, чтобы увидеть живое представление в виде чата со счётчиками входящих/исходящих сообщений.

| Канал | Статус | Живое всплывающее окно | Примечания |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Полностью | ✅ | Сообщения, статистика, обновление раз в 10 с |
| 💬 **iMessage** | ✅ Полностью | ✅ | Читает `~/Library/Messages/chat.db` напрямую |
| 💚 **WhatsApp** | ✅ Полностью | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Полностью | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Полностью | ✅ | Определение гильдии + канала |
| 🟪 **Slack** | ✅ Полностью | ✅ | Определение рабочего пространства + канала |
| 🌐 **Webchat** | ✅ Полностью | ✅ | Встроенные сессии веб-интерфейса |
| 📡 **IRC** | ✅ Полностью | ✅ | Интерфейс в стиле терминала |
| 🍏 **BlueBubbles** | ✅ Полностью | ✅ | iMessage через REST API BlueBubbles |
| 🔵 **Google Chat** | ✅ Полностью | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Полностью | ✅ | Через плагин бота Teams |
| 🔷 **Mattermost** | ✅ Полностью | ✅ | Собственный корпоративный чат |
| 🟩 **Matrix** | ✅ Полностью | ✅ | Децентрализованный, поддержка E2EE |
| 🟢 **LINE** | ✅ Полностью | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Полностью | ✅ | Децентрализованные личные сообщения NIP-04 |
| 🟣 **Twitch** | ✅ Полностью | ✅ | Чат через подключение IRC |
| 🔷 **Feishu/Lark** | ✅ Полностью | ✅ | Подписка на события через WebSocket |
| 🔵 **Zalo** | ✅ Полностью | ✅ | Zalo Bot API |

> **Автоопределение:** ClawMetry читает ваш `~/.openclaw/openclaw.json` и отображает только реально настроенные вами каналы. Ручная настройка не требуется.

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

> **Примечание:** При запуске в Docker смонтируйте каталоги данных и логов вашего агента (например, `~/.openclaw`, `~/.claude`, `~/.codex`), чтобы ClawMetry мог автоматически определить вашу настройку.

## Требования

- Python 3.8+
- Flask (устанавливается автоматически через pip)
- Рантайм ИИ-агента на той же машине: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok или QM (либо смонтированные тома для Docker)
- Linux или macOS

## Поддержка NemoClaw / OpenShell

ClawMetry автоматически определяет [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративную обёртку безопасности NVIDIA для OpenClaw, которая запускает агентов внутри изолированных контейнеров OpenShell.

В большинстве случаев дополнительная настройка не требуется. Демон синхронизации автоматически обнаруживает файлы сессий независимо от того, находятся ли они в `~/.openclaw/` на хосте или внутри контейнера OpenShell.

### Как это работает

ClawMetry определяет NemoClaw двумя способами:

1. **Определение по бинарнику** — проверяет наличие CLI `nemoclaw` и запускает `nemoclaw status` для получения информации о песочнице
2. **Определение по контейнеру** — сканирует запущенные контейнеры Docker на предмет образов `openshell`, `nemoclaw` или `ghcr.io/nvidia/`, затем читает сессии через смонтированные тома или `docker cp`

Файлы сессий, синхронизированные из контейнеров NemoClaw, помечаются метаданными `runtime=nemoclaw` и `container_id` в облачной панели, чтобы вы могли с первого взгляда отличить их от обычных сессий OpenClaw.

### Рекомендуемая настройка: демон синхронизации на ХОСТЕ

Для наилучшего результата запускайте демон синхронизации ClawMetry на **хост-машине** (а не внутри песочницы). Это позволяет избежать ограничений сетевой политики NemoClaw.

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

### Запуск внутри песочницы (для продвинутых)

Если вам необходимо запустить демон синхронизации **внутри** песочницы OpenShell, добавьте это правило исходящего трафика в вашу сетевую политику NemoClaw, чтобы он мог обращаться к API приёма ClawMetry:

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

### Порты и точки доступа

| Точка доступа | Порт | Протокол | Обязательно |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Да (демон синхронизации → облако) |
| `localhost:8900` | 8900 | HTTP | Да (локальный интерфейс панели) |
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
при первом запуске после обновления до новой версии и один пинг `onboarded`,
когда вы завершаете выбор в мастере первого запуска панели. Мы используем это
для подсчёта реальных установок (сырые цифры загрузок PyPI примерно на 98% состоят из зеркал, CI
и повторных загрузок автообновления) и для того, чтобы узнать, какие фреймворки агентов и
версии реально используются.

**Не более одного POST-запроса на событие жизненного цикла на версию**, содержащего:

| Поле | Пример | Зачем |
|---|---|---|
| `install_id` | случайный UUID, хранящийся в `~/.clawmetry/install_id` | дедупликация; анонимно, пока вы явно не подключите синхронизацию с облаком (тогда аутентифицированный heartbeat демона несёт этот идентификатор, связывая эту установку с вашим аккаунтом) |
| `event` | `install` / `update` / `onboarded` | новая установка или обновление существующей |
| `version` | `0.12.167` | какие версии реально используются |
| `os` / `os_version` | `Darwin` / `25.3.0` | приоритеты поддержки платформ |
| `python` | `3.11.15` | матрица поддержки версий Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | с какими агентами нам стоит интегрироваться дальше |
| `is_ci` / `ci_provider` | `true` / `github_actions` | отделение установок реальными людьми от шума CI |

**Чего мы НЕ отправляем**: IP-адрес (облако определяет код страны на стороне сервера
из запроса, а затем отбрасывает IP), имя хоста, имя пользователя, путь к рабочему
пространству, содержимое файлов, ваш api_key, ваш email, что-либо являющееся ПДн или
специфичное для рабочего пространства. Передаваемая нагрузка доступна для аудита в
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Отказаться** (любой из этих вариантов отключает это навсегда):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Сбой сети здесь никогда не блокирует запуск `clawmetry` — пинг
отправляется в фоновом потоке демона по принципу "отправил и забыл" с таймаутом 3 с.

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
