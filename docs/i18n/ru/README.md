<!-- i18n-src:bab48eec552f -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Смотрите, как думает ваш агент.** Наблюдаемость в реальном времени для **14 сред выполнения ИИ-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 10. Одна панель для всего вашего парка агентов.

> 🌐 **Читать на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Никакой настройки. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается на **http://localhost:8900**, и всё готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Работает с 14 средами выполнения агентов

ClawMetry начиналась как инструмент наблюдаемости для OpenClaw, а теперь измеряет **весь ваш парк агентов** на одной панели, автоматически определяя каждую среду выполнения на вашей машине:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw и NemoClaw бесплатны в приложении с открытым исходным кодом; остальные среды выполнения становятся доступны с ClawMetry Cloud или самостоятельно размещённой лицензией Pro. Переключайте среды выполнения из шапки, и каждая вкладка — стоимость, токены, инструменты, трассировки — пересчитывается под неё. Точное разделение на бесплатное/платное, матрицу уровней, форму `/api/entitlement` и CLI `clawmetry license` см. в **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**.

## Что вы получаете

- **Flow** — живая анимированная диаграмма, показывающая, как сообщения проходят через каналы, «мозг», инструменты и обратно
- **Overview** — проверки состояния, тепловая карта активности, количество сессий, информация о модели
- **Usage** — отслеживание токенов и стоимости с разбивкой по дням/неделям/месяцам
- **Sessions** — активные сессии агента с указанием модели, токенов, времени последней активности
- **Crons** — запланированные задачи со статусом, временем следующего запуска, длительностью
- **Logs** — потоковая передача логов в реальном времени с цветовой разметкой
- **Memory** — просмотр SOUL.md, MEMORY.md, AGENTS.md, ежедневных заметок
- **Transcripts** — интерфейс в виде чата для чтения истории сессий
- **Alerts** — лимиты бюджета, срабатывания по частоте ошибок, обнаружение недоступности агента; отправка в Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — блокировка деструктивных удалений, принудительных push, изменений в БД, sudo, установки пакетов и сетевых вызовов до получения подтверждения в один клик

## Скриншоты

### 🧠 Brain — поток событий агента в реальном времени
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — использование токенов и сводка по сессиям
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — лента вызовов инструментов в реальном времени
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — разбивка стоимости по моделям и сессиям
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — обозреватель файлов рабочей области
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — состояние защищённости и журнал аудита
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — лимиты бюджета, срабатывания по частоте ошибок, вебхуки в Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — блокировка рискованных вызовов инструментов до ручного подтверждения; правила защиты на основе политик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Блокировка перед выполнением для Claude Code** — одна команда устанавливает
хук PreToolUse, который приостанавливает подходящие под правило вызовы инструментов *до* их выполнения и ждёт вашего
решения (один тап с телефона при включённых
[push уведомлениях в облаке](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Отказ блокирует только этот один вызов инструмента, агент сохраняет свою сессию и может
попробовать другой подход. Подтверждение с телефона пропускает собственный запрос
на разрешение Claude Code (вы уже ответили). Несовпавшие инструменты стоят ~40 мс и
проходят через обычный процесс разрешений Claude Code. Вы также получаете push на телефон, когда сам Claude Code
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

**Из исходного кода:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Разработка фронтенда v2

Приложение v2 на React находится в `frontend/` и раздаётся по адресу `/v2`, если
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
`http://localhost:8900`, поэтому приложению на React не требуется дополнительная настройка CORS
для обращения к локальному серверу Flask.

Чтобы собрать бандл, который поставляется вместе с Python-пакетом:

```bash
cd frontend
npm run build
```

Готовый к продакшену бандл записывается в `clawmetry/static/v2/dist/`.

## Совместимость со средами выполнения / агентами

ClawMetry наблюдает за многими средами выполнения ИИ-агентов, а не только за OpenClaw. Для каждой среды выполнения, кроме OpenClaw, поставляется отдельный адаптер чтения, который преобразует её нативный формат сессий в унифицированные форматы ClawMetry; демон загружает их в то же хранилище DuckDB и облачный снапшот, помечая тегом среды выполнения, а вкладка воспроизведения сессии показывает **переключатель среды выполнения**, если их присутствует больше одной. Полную матрицу и руководство по добавлению сред выполнения см. в [`docs/compatibility.md`](docs/compatibility.md), а введение по семейству OpenClaw — в [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md).

| Среда выполнения / агент | Статус | Примечания |
|---|---|---|
| **OpenClaw** | Нативная | Эталонная среда выполнения, определяется автоматически |
| **PicoClaw** | Бета-адаптер | Плоский JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Транскрипты, модель, вызовы инструментов. |
| **NanoClaw** | Бета-адаптер | SQLite для каждой сессии (`data/v2-sessions`). Транскрипты + количество сообщений. |
| **Hermes** | Бета-адаптер | SQLite `~/.hermes/state.db`. Транскрипты, модель, токены/стоимость. |
| **Claude Code** | Бета-адаптер | JSONL `~/.claude/projects/.../<id>.jsonl`. Транскрипты, модель, вызовы инструментов + рассуждения, использование токенов. |
| **Codex** | Бета-адаптер | Rollout JSONL `~/.codex/sessions/...`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Cursor** | Бета-адаптер | SQLite `state.vscdb`. Транскрипты чата/composer, модель. |
| **Aider** | Бета-адаптер | `.aider.chat.history.md` на проект. Транскрипты, модель, количество токенов. |
| **Goose** | Бета-адаптер | SQLite `~/.local/share/goose`. Транскрипты, модель, вызовы инструментов, суммарные токены. |
| **opencode** | Бета-адаптер | SQLite `~/.local/share/opencode`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Qwen Code** | Бета-адаптер | JSONL `~/.qwen/projects/.../chats`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Pi** | Бета-адаптер | JSONL `~/.pi/agent/sessions`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |
| **Deep Agents** | Бета-адаптер | SQLite `~/.deepagents/.state/sessions.db`. Транскрипты, модель, вызовы инструментов, токены + стоимость. |

«Бета-адаптер» означает, что ClawMetry поставляет модуль чтения реального формата хранения данных этой среды выполнения на диске, каждый из которых собран и проверен на реальной установке на реальной машине (см. `tests/fixtures/runtimes/<rt>/`). Адаптеры доступны только для чтения; каждый честно отражает то, что среда выполнения реально хранит (например, PicoClaw/NanoClaw/Cursor не записывают стоимость токенов на диск). Когда на одном узле работает несколько сред выполнения, переключатель сред выполнения ограничивает представление сессий одной из них для удобного глубокого анализа.

## Отслеживание любого агента на базе SDK — атрибуция стоимости вне цикла

Все перечисленные выше среды выполнения записывают сессии на диск. Ваш собственный **продакшен-агент** — тот, что вы собрали на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B или на обычном цикле `httpx`, — этого не делает. Zero-config перехватчик ClawMetry всё равно фиксирует его вызовы LLM (стоимость, токены, задержка, ошибки), выполняя monkey-patching `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (или переменная окружения `CLAWMETRY_SOURCE=support-agent`) помечает каждый вызов **именованным источником**, поэтому каждый продукт, который вы запускаете, отображается как отдельная строка первого класса с возможностью атрибуции стоимости в карточке **🔌 Out-loop sources** на вкладке Overview панели: вызовы, провайдеры, задержка, частота ошибок на каждого агента. Источник не задан? Вызовы всё равно отслеживаются, просто карточка остаётся скрытой.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Это тот же слой данных, который питают адаптеры сред выполнения (DuckDB → облачный снапшот), поэтому источники вне цикла синхронизируются с облачной панелью так же, как и всё остальное, со сквозным шифрованием.

## OpenTelemetry — независимо от вендора, отправляйте свои трассировки куда угодно

ClawMetry говорит на языке **OpenTelemetry** в обе стороны, используя **семантические соглашения GenAI**, поэтому трассировки вашего агента никогда не привязаны к одному инструменту.

**Экспортируйте** каждую сессию — вызовы LLM, инструменты, суб-агентов, токены, стоимость — в виде спанов OTLP/HTTP GenAI в любой коллектор (Datadog, Grafana, Honeycomb или ваш собственный OTel Collector):

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

**Принимайте** — встроенный приёмник OTLP принимает трассировки и метрики от чего угодно ещё по адресам `/v1/traces` и `/v1/metrics` (для приёма protobuf выполните `pip install clawmetry[otel]`).

Вы получаете zero-config, локальную по умолчанию панель ClawMetry **и** свои данные в любом бэкенде, который уже использует ваша команда, без привязки к одному поставщику и без необходимости устанавливать второго агента.

## Настройка

Большинству людей не требуется никакая настройка. ClawMetry автоматически определяет вашу рабочую область, логи, сессии и cron-задачи.

Если вам всё же нужна настройка:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Все параметры: `clawmetry --help`

## Поддерживаемые каналы

ClawMetry показывает живую активность для каждого настроенного у вас канала OpenClaw. На диаграмме Flow отображаются только те каналы, которые действительно настроены в вашем `openclaw.json`, ненастроенные автоматически скрываются.

Нажмите на любой узел канала на диаграмме Flow, чтобы увидеть представление чата в реальном времени с количеством входящих/исходящих сообщений.

| Канал | Статус | Живое всплывающее окно | Примечания |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Полностью | ✅ | Сообщения, статистика, обновление каждые 10 с |
| 💬 **iMessage** | ✅ Полностью | ✅ | Читает `~/Library/Messages/chat.db` напрямую |
| 💚 **WhatsApp** | ✅ Полностью | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Полностью | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Полностью | ✅ | Определение гильдии + канала |
| 🟪 **Slack** | ✅ Полностью | ✅ | Определение рабочего пространства + канала |
| 🌐 **Webchat** | ✅ Полностью | ✅ | Встроенные сессии веб-интерфейса |
| 📡 **IRC** | ✅ Полностью | ✅ | Интерфейс в стиле терминала |
| 🍏 **BlueBubbles** | ✅ Полностью | ✅ | iMessage через BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Полностью | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Полностью | ✅ | Через плагин бота Teams |
| 🔷 **Mattermost** | ✅ Полностью | ✅ | Самостоятельно размещённый корпоративный чат |
| 🟩 **Matrix** | ✅ Полностью | ✅ | Децентрализованный, поддержка E2EE |
| 🟢 **LINE** | ✅ Полностью | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Полностью | ✅ | Децентрализованные личные сообщения NIP-04 |
| 🟣 **Twitch** | ✅ Полностью | ✅ | Чат через подключение IRC |
| 🔷 **Feishu/Lark** | ✅ Полностью | ✅ | Подписка на события через WebSocket |
| 🔵 **Zalo** | ✅ Полностью | ✅ | Zalo Bot API |

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

> **Примечание:** При запуске в Docker смонтируйте каталоги данных и логов вашего агента (например, `~/.openclaw`, `~/.claude`, `~/.codex`), чтобы ClawMetry мог автоматически определить вашу конфигурацию.

## Требования

- Python 3.8+
- Flask (устанавливается автоматически через pip)
- Среда выполнения ИИ-агента на той же машине: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi или Deep Agents (либо смонтированные тома для Docker)
- Linux или macOS

## Поддержка NemoClaw / OpenShell

ClawMetry автоматически определяет [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративную обёртку безопасности NVIDIA для OpenClaw, которая запускает агентов внутри изолированных контейнеров OpenShell.

В большинстве случаев дополнительная настройка не требуется. Демон синхронизации автоматически обнаруживает файлы сессий независимо от того, находятся ли они в `~/.openclaw/` на хосте или внутри контейнера OpenShell.

### Как это работает

ClawMetry определяет NemoClaw двумя способами:

1. **Определение по бинарному файлу** — проверяет наличие CLI `nemoclaw` и запускает `nemoclaw status`, чтобы получить информацию о песочнице
2. **Определение по контейнеру** — сканирует запущенные Docker-контейнеры на предмет образов `openshell`, `nemoclaw` или `ghcr.io/nvidia/`, затем читает сессии через смонтированные тома или `docker cp`

Файлы сессий, синхронизированные из контейнеров NemoClaw, помечаются метаданными `runtime=nemoclaw` и `container_id` в облачной панели, чтобы вы могли с первого взгляда отличить их от обычных сессий OpenClaw.

### Рекомендуемая настройка: демон синхронизации на ХОСТЕ

Для наилучшего опыта запускайте демон синхронизации ClawMetry на **хост-машине** (а не внутри песочницы). Это позволяет избежать ограничений сетевой политики NemoClaw.

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

Если вам необходимо запустить демон синхронизации **внутри** песочницы OpenShell, добавьте это правило исходящего трафика в вашу сетевую политику NemoClaw, чтобы он мог обращаться к API приёма данных ClawMetry:

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

| Точка доступа | Порт | Протокол | Требуется |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Да (демон синхронизации → облако) |
| `localhost:8900` | 8900 | HTTP | Да (локальный интерфейс панели) |
| Docker-сокет (`/var/run/docker.sock`) | — | Unix socket | Для обнаружения сессий в контейнерах |

Демон синхронизации выполняет только исходящие вызовы HTTPS к `ingest.clawmetry.com`. Входящие порты не требуются.

---

## Развёртывание в облаке

См. **[Руководство по тестированию в облаке](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** по SSH-туннелям, обратному прокси и Docker.

## Тестирование

Этот проект тестируется с помощью BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрия

ClawMetry отправляет одиночный анонимный пинг «первого запуска» на
`https://app.clawmetry.com/api/install` при первом запуске CLI
`clawmetry` на новой машине. Мы используем это, чтобы считать установки (единственная
маркетинговая метрика, которая есть у проекта с открытым исходным кодом), и узнавать, какие
агентные фреймворки установлены у наших пользователей.

**Ровно один POST-запрос на установку**, содержащий:

| Поле | Пример | Зачем |
|---|---|---|
| `install_id` | случайный UUID, хранящийся в `~/.clawmetry/install_id` | дедупликация; не связан с вашей почтой или api_key |
| `version` | `0.12.167` | какие версии используются в реальности |
| `os` / `os_version` | `Darwin` / `25.3.0` | приоритеты поддержки платформ |
| `python` | `3.11.15` | матрица поддержки версий Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | с какими агентами нам стоит интегрироваться в первую очередь |
| `is_ci` / `ci_provider` | `true` / `github_actions` | отделение установок людьми от шума CI |

**Что мы НЕ отправляем**: IP-адрес (облако определяет код страны на стороне сервера
из запроса, затем отбрасывает IP), имя хоста, имя пользователя, путь к
рабочей области, содержимое файлов, ваш api_key, вашу почту, что-либо личное или
специфичное для рабочей области. Передаваемая полезная нагрузка доступна для проверки в
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Отказаться** (любой из вариантов отключает телеметрию навсегда):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Сбой сети здесь никогда не блокирует запуск `clawmetry`, пинг
отправляется в фоновом потоке без ожидания ответа, с таймаутом 3 с.

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
