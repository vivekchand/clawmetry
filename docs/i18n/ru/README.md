<!-- i18n-src:56ff57310588 -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Увидьте, как думает ваш агент.** Наблюдаемость в реальном времени для AI-агентов [OpenClaw](https://github.com/openclaw/openclaw).

> 🌐 **Читать на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [подробнее →](docs/i18n/)

Одна команда. Никакой настройки. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**, и на этом всё.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Что вы получаете

- **Flow** — Живая анимированная диаграмма, показывающая поток сообщений через каналы, мозг, инструменты и обратно
- **Overview** — Проверки работоспособности, тепловая карта активности, счётчики сессий, информация о моделях
- **Usage** — Отслеживание токенов и затрат с разбивкой по дням/неделям/месяцам
- **Sessions** — Активные сессии агентов с моделью, токенами, последней активностью
- **Crons** — Запланированные задания со статусом, следующим запуском, длительностью
- **Logs** — Потоковый вывод логов в реальном времени с цветовой маркировкой
- **Memory** — Просмотр SOUL.md, MEMORY.md, AGENTS.md, ежедневных заметок
- **Transcripts** — Интерфейс в виде чат-пузырей для чтения истории сессий
- **Alerts** — Лимиты бюджета, триггеры по частоте ошибок, обнаружение офлайн-агентов; маршрутизация в Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Поставьте под одобрение в один клик деструктивные удаления, принудительные пуши, изменения БД, sudo, установку пакетов, сетевые вызовы

## Скриншоты

### 🧠 Brain — Живой поток событий агента
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Использование токенов и сводка по сессиям
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Лента вызовов инструментов в реальном времени
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Разбивка затрат по моделям и сессиям
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Браузер файлов рабочего пространства
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Состояние защиты и журнал аудита
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Лимиты бюджета, триггеры по частоте ошибок, веб-хуки в Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Поставьте рискованные вызовы инструментов под ручное одобрение; правила защиты на основе политик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Установка

**Одной строкой (рекомендуется):**
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

Приложение v2 на React находится в `frontend/` и обслуживается по адресу `/v2`, когда
сервер Flask запущен с включённым v2.

Во время разработки используйте два терминала:

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
`http://localhost:8900`, так что приложение на React может общаться с локальным сервером Flask
без дополнительной настройки CORS.

Чтобы собрать бандл, поставляемый с пакетом Python:

```bash
cd frontend
npm run build
```

Продакшен-бандл записывается в `clawmetry/static/v2/dist/`.

## Совместимость со средами выполнения / агентами

ClawMetry наблюдает за многими средами выполнения AI-агентов, не только за OpenClaw. Каждая среда, отличная от OpenClaw, поставляется со специальным адаптером-ридером, который переводит её родной формат сессий в унифицированные форматы ClawMetry; демон загружает их в то же хранилище DuckDB + облачный снапшот, помечая средой выполнения, а вкладка воспроизведения сессий показывает **переключатель сред выполнения**, когда присутствует более одной. Полную матрицу + руководство по добавлению сред выполнения смотрите в [`docs/compatibility.md`](docs/compatibility.md), а вводный материал по семейству OpenClaw — в [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md).

| Среда выполнения / агент | Статус | Примечания |
|---|---|---|
| **OpenClaw** | Нативная | Эталонная среда выполнения, определяется автоматически |
| **PicoClaw** | Бета-адаптер | Плоский `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`). Транскрипты, модель, вызовы инструментов. |
| **NanoClaw** | Бета-адаптер | Посессионный SQLite (`data/v2-sessions`). Транскрипты + счётчики сообщений. |
| **Hermes** | Бета-адаптер | SQLite `~/.hermes/state.db`. Транскрипты, модель, токены/затраты. |
| **Claude Code** | Бета-адаптер | JSONL `~/.claude/projects/.../<id>.jsonl`. Транскрипты, модель, вызовы инструментов + размышления, использование токенов. |
| **Codex** | Бета-адаптер | Rollout JSONL `~/.codex/sessions/...`. Транскрипты, модель, вызовы инструментов, использование токенов. |
| **Cursor** | Бета-адаптер | SQLite `state.vscdb`. Транскрипты чата/композера, модель. |
| **Aider** | Бета-адаптер | `.aider.chat.history.md` для каждого проекта. Транскрипты, модель, счётчики токенов. |
| **Goose** | Бета-адаптер | SQLite `~/.local/share/goose`. Транскрипты, модель, вызовы инструментов, суммарные токены. |

«Бета-адаптер» означает, что ClawMetry поставляет ридер для реального дискового формата этой среды выполнения, каждый из которых собран и проверен на реальной установке на реальной машине (см. `tests/fixtures/runtimes/<rt>/`). Адаптеры работают только на чтение; каждый честно сообщает, что именно его среда выполнения действительно хранит (например, PicoClaw/NanoClaw/Cursor не записывают стоимость токенов на диск). Когда на одном узле работают несколько сред выполнения, переключатель сред ограничивает представление сессий одной из них для удобного детального изучения.

## OpenTelemetry — без привязки к вендору, отправляйте трассировки куда угодно

ClawMetry говорит на **OpenTelemetry** в обоих направлениях, используя **семантические соглашения GenAI**, поэтому трассировки ваших агентов никогда не привязаны к одному инструменту.

**Экспортируйте** каждую сессию — вызовы LLM, инструменты, субагенты, токены, затраты — как OTLP/HTTP-спаны GenAI в любой коллектор (Datadog, Grafana, Honeycomb или ваш собственный OTel Collector):

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

**Приём** — встроенный приёмник OTLP принимает трассировки и метрики от чего угодно по адресам `/v1/traces` и `/v1/metrics` (`pip install clawmetry[otel]` для приёма в формате protobuf).

Вы получаете локальную панель ClawMetry без настройки **и** свои данные в любом бэкенде, который уже использует ваша команда — без привязки к вендору, без необходимости устанавливать второго агента.

## Конфигурация

Большинству людей конфигурация не нужна. ClawMetry автоматически определяет ваше рабочее пространство, логи, сессии и cron-задания.

Если вам всё же нужно что-то настроить:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Все опции: `clawmetry --help`

## Поддерживаемые каналы

ClawMetry показывает активность в реальном времени для каждого настроенного вами канала OpenClaw. В диаграмме Flow появляются только те каналы, которые действительно настроены в вашем `openclaw.json`, — ненастроенные автоматически скрываются.

Нажмите на любой узел канала во Flow, чтобы увидеть представление чата в реальном времени со счётчиками входящих/исходящих сообщений.

| Канал | Статус | Живое всплывающее окно | Примечания |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Полная | ✅ | Сообщения, статистика, обновление каждые 10 с |
| 💬 **iMessage** | ✅ Полная | ✅ | Читает `~/Library/Messages/chat.db` напрямую |
| 💚 **WhatsApp** | ✅ Полная | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Полная | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Полная | ✅ | Определение сервера + канала |
| 🟪 **Slack** | ✅ Полная | ✅ | Определение рабочего пространства + канала |
| 🌐 **Webchat** | ✅ Полная | ✅ | Сессии встроенного веб-интерфейса |
| 📡 **IRC** | ✅ Полная | ✅ | Интерфейс пузырей в стиле терминала |
| 🍏 **BlueBubbles** | ✅ Полная | ✅ | iMessage через REST API BlueBubbles |
| 🔵 **Google Chat** | ✅ Полная | ✅ | Через веб-хуки Chat API |
| 🟣 **MS Teams** | ✅ Полная | ✅ | Через плагин-бот Teams |
| 🔷 **Mattermost** | ✅ Полная | ✅ | Самостоятельно размещаемый командный чат |
| 🟩 **Matrix** | ✅ Полная | ✅ | Децентрализованный, поддержка E2EE |
| 🟢 **LINE** | ✅ Полная | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Полная | ✅ | Децентрализованные личные сообщения NIP-04 |
| 🟣 **Twitch** | ✅ Полная | ✅ | Чат через подключение IRC |
| 🔷 **Feishu/Lark** | ✅ Полная | ✅ | Подписка на события через WebSocket |
| 🔵 **Zalo** | ✅ Полная | ✅ | Zalo Bot API |

> **Автоопределение:** ClawMetry читает ваш `~/.openclaw/openclaw.json` и отображает только те каналы, которые вы действительно настроили. Ручная настройка не требуется.

## Развёртывание в Docker

Хотите запустить ClawMetry в контейнере? Без проблем! 🐳

**Быстрый старт с Docker:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or with your OpenClaw workspace mounted
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

> **Примечание:** При запуске в Docker обязательно смонтируйте ваше рабочее пространство OpenClaw и каталоги логов, чтобы ClawMetry мог автоматически определить вашу конфигурацию.

## Требования

- Python 3.8+
- Flask (устанавливается автоматически через pip)
- OpenClaw, работающий на той же машине (или смонтированные тома для Docker)
- Linux или macOS

## Поддержка NemoClaw / OpenShell

ClawMetry автоматически определяет [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративную защитную оболочку NVIDIA для OpenClaw, которая запускает агентов внутри изолированных контейнеров OpenShell.

В большинстве случаев дополнительная настройка не требуется. Демон синхронизации автоматически обнаруживает файлы сессий независимо от того, находятся ли они в `~/.openclaw/` на хосте или внутри контейнера OpenShell.

### Как это работает

ClawMetry определяет NemoClaw двумя способами:

1. **Определение по бинарнику** — проверяет наличие CLI `nemoclaw` и запускает `nemoclaw status`, чтобы получить информацию о песочнице
2. **Определение по контейнерам** — сканирует запущенные контейнеры Docker на наличие образов `openshell`, `nemoclaw` или `ghcr.io/nvidia/`, затем читает сессии через смонтированные тома или `docker cp`

Файлы сессий, синхронизированные из контейнеров NemoClaw, помечаются метаданными `runtime=nemoclaw` и `container_id` в облачной панели, так что вы с первого взгляда отличите их от стандартных сессий OpenClaw.

### Рекомендуемая настройка: демон синхронизации на ХОСТЕ

Для наилучшего опыта запускайте демон синхронизации ClawMetry на **хост-машине** (а не внутри песочницы). Это позволяет избежать ограничений сетевой политики NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Демон синхронизации автоматически найдёт сессии внутри любых запущенных контейнеров OpenShell.

### Опционально: явное имя песочницы

Если автоопределение не сработало, укажите ClawMetry на нужную песочницу:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Запуск внутри песочницы (для продвинутых)

Если вам необходимо запускать демон синхронизации **внутри** песочницы OpenShell, добавьте это правило исходящего трафика в вашу сетевую политику NemoClaw, чтобы он мог достучаться до API приёма ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Применить с помощью:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Порты и конечные точки

| Конечная точка | Порт | Протокол | Обязательно |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Да (демон синхронизации → облако) |
| `localhost:8900` | 8900 | HTTP | Да (локальный интерфейс панели) |
| Docker socket (`/var/run/docker.sock`) | — | Unix-сокет | Для обнаружения сессий в контейнерах |

Демон синхронизации делает только исходящие HTTPS-вызовы к `ingest.clawmetry.com`. Входящие порты не требуются.

---

## Развёртывание в облаке

Смотрите **[Руководство по тестированию в облаке](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** для SSH-туннелей, обратного прокси и Docker.

## Тестирование

Этот проект тестируется с помощью BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрия

ClawMetry отправляет один анонимный пинг «первого запуска» на
`https://app.clawmetry.com/api/install` при первом запуске CLI
`clawmetry` на новой машине. Мы используем это, чтобы считать установки (это
единственная маркетинговая метрика, которая у нас есть для OSS-проекта), и чтобы узнать, какие
агентные фреймворки установлены у наших пользователей.

**Ровно один POST на установку**, содержащий:

| Поле | Пример | Зачем |
|---|---|---|
| `install_id` | случайный UUID, хранящийся в `~/.clawmetry/install_id` | дедупликация; не связан с вашей почтой или api_key |
| `version` | `0.12.167` | какие версии встречаются в реальном мире |
| `os` / `os_version` | `Darwin` / `25.3.0` | приоритеты поддержки платформ |
| `python` | `3.11.15` | матрица поддержки версий Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | с какими агентами нам стоит интегрироваться дальше |
| `is_ci` / `ci_provider` | `true` / `github_actions` | отделить установки людей от шума CI |

**Что мы НЕ отправляем**: IP (облако определяет код страны на стороне сервера
из запроса, затем отбрасывает IP), имя хоста, имя пользователя, путь к рабочему
пространству, содержимое файлов, ваш api_key, вашу почту, любые персональные данные или
данные, специфичные для рабочего пространства. Передаваемый по сети пакет можно проверить в
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Отказаться** (любое из этого отключает телеметрию навсегда):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Сетевой сбой здесь никогда не блокирует запуск `clawmetry` — пинг
отправляется по принципу «отправил и забыл» в потоке-демоне с тайм-аутом 3 с.

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
  <strong>🦞 Увидьте, как думает ваш агент</strong><br>
  <sub>Создано <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Часть экосистемы <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
