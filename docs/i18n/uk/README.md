<!-- i18n-src:9a05336fbdc1 -->
> Українська translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Побачте, як думає ваш агент.** Спостережуваність у реальному часі для **14 середовищ виконання AI-агентів**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex та ще 10 інших. Одна панель для всього вашого флоту агентів.

> 🌐 **Читати цією мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Одна команда. Нуль налаштувань. Автоматично визначає все.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**, і все готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Працює з 14 середовищами виконання агентів

ClawMetry почався як інструмент спостережуваності для OpenClaw, а тепер вимірює **весь ваш флот агентів** на одній панелі, автоматично визначаючи кожне середовище виконання на вашій машині:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw і NemoClaw безкоштовні у застосунку з відкритим кодом; інші середовища виконання вмикаються за допомогою ClawMetry Cloud або ліцензії Pro для самостійного розміщення. Перемикайте середовища виконання з панелі заголовка, і кожна вкладка — вартість, токени, інструменти, трасування — переорієнтовується на це середовище виконання. Дивіться **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** для точного розподілу безкоштовне/платне, матриці рівнів, форми `/api/entitlement` та CLI `clawmetry license`.

## Що ви отримуєте

- **Flow** — Живе анімоване зображення, що показує рух повідомлень через канали, мозок, інструменти і назад
- **Overview** — Перевірки стану, теплова карта активності, кількість сесій, інформація про модель
- **Usage** — Відстеження токенів і вартості з щоденною/щотижневою/щомісячною розбивкою
- **Sessions** — Активні сесії агентів з моделлю, токенами, останньою активністю
- **Crons** — Заплановані завдання зі статусом, наступним запуском, тривалістю
- **Logs** — Кольорове потокове передавання логів у реальному часі
- **Memory** — Перегляд SOUL.md, MEMORY.md, AGENTS.md, щоденних нотаток
- **Transcripts** — Інтерфейс у вигляді чат-бульбашок для читання історій сесій
- **Alerts** — Ліміти бюджету, тригери частоти помилок, виявлення офлайн-стану агента; маршрутизація до Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Блокування деструктивних видалень, примусових пушів, мутацій БД, sudo, встановлення пакетів, мережевих викликів за одноразовим підтвердженням

## Скріншоти

### 🧠 Brain — Потік подій агента в реальному часі
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Використання токенів та підсумок сесій
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Потік викликів інструментів у реальному часі
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Розбивка вартості за моделлю та сесією
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Переглядач файлів робочого простору
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Стан безпеки та журнал аудиту
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Ліміти бюджету, тригери частоти помилок, вебхуки в Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Блокування ризикованих викликів інструментів за ручним підтвердженням; правила захисту на основі політик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Блокування перед виконанням для Claude Code** — одна команда встановлює
хук PreToolUse, який призупиняє відповідні виклики інструментів *перед* їх виконанням і чекає
вашого рішення (одним дотиком з телефону з увімкненими
[push-сповіщеннями хмари](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Відмова блокує лише той один виклик інструменту — агент зберігає свою сесію і може
спробувати інший підхід. Підтвердження з телефону пропускає власний
запит на дозвіл Claude Code (ви вже відповіли). Незіставлені інструменти коштують ~40мс і
переходять до звичайного процесу дозволів Claude Code. Ви також отримуєте push на телефон, коли
Claude Code сам очікує на вас (сповіщення `permission_prompt` /
`idle_prompt`).

## Встановлення

**Однорядковий скрипт (рекомендовано):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**З вихідного коду:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Розробка фронтенду v2

React-застосунок v2 знаходиться в `frontend/` і подається за адресою `/v2`, коли
сервер Flask запущено з увімкненим v2.

Використовуйте два термінали під час розробки:

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

Відкрийте `http://localhost:5173/v2/`. Vite проксує запити `/api` до
`http://localhost:8900`, тому React-застосунок може взаємодіяти з локальним сервером Flask
без додаткового налаштування CORS.

Щоб зібрати пакунок, який постачається з пакетом Python:

```bash
cd frontend
npm run build
```

Продакшн-пакунок записується в `clawmetry/static/v2/dist/`.

## Сумісність середовищ виконання / агентів

ClawMetry спостерігає за багатьма середовищами виконання AI-агентів, а не лише за OpenClaw. Кожне середовище виконання, відмінне від OpenClaw, постачається з окремим адаптером-читачем, який перетворює його рідний формат сесій у уніфіковані форми ClawMetry; демон приймає їх у те саме сховище DuckDB + хмарний знімок, позначений середовищем виконання, а вкладка відтворення сесії показує **перемикач середовищ виконання**, коли присутнє більше одного. Дивіться [`docs/compatibility.md`](docs/compatibility.md) для повної матриці + посібника з додавання середовищ виконання, та [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) для основ родини OpenClaw.

| Середовище виконання / агент | Статус | Примітки |
|---|---|---|
| **OpenClaw** | Рідне | Еталонне середовище виконання, автоматичне визначення |
| **PicoClaw** | Бета-адаптер | Плоский JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Транскрипти, модель, виклики інструментів. |
| **NanoClaw** | Бета-адаптер | SQLite для кожної сесії (`data/v2-sessions`). Транскрипти + кількість повідомлень. |
| **Hermes** | Бета-адаптер | SQLite `~/.hermes/state.db`. Транскрипти, модель, токени/вартість. |
| **Claude Code** | Бета-адаптер | JSONL `~/.claude/projects/.../<id>.jsonl`. Транскрипти, модель, виклики інструментів + міркування, використання токенів. |
| **Codex** | Бета-адаптер | Rollout JSONL `~/.codex/sessions/...`. Транскрипти, модель, виклики інструментів, використання токенів. |
| **Cursor** | Бета-адаптер | SQLite `state.vscdb`. Транскрипти чату/композера, модель. |
| **Aider** | Бета-адаптер | `.aider.chat.history.md` для кожного проєкту. Транскрипти, модель, кількість токенів. |
| **Goose** | Бета-адаптер | SQLite `~/.local/share/goose`. Транскрипти, модель, виклики інструментів, загальна кількість токенів. |
| **opencode** | Бета-адаптер | SQLite `~/.local/share/opencode`. Транскрипти, модель, виклики інструментів, токени + вартість. |
| **Qwen Code** | Бета-адаптер | JSONL `~/.qwen/projects/.../chats`. Транскрипти, модель, виклики інструментів, використання токенів. |
| **Pi** | Бета-адаптер | JSONL `~/.pi/agent/sessions`. Транскрипти, модель, виклики інструментів, токени + вартість. |
| **Deep Agents** | Бета-адаптер | SQLite `~/.deepagents/.state/sessions.db`. Транскрипти, модель, виклики інструментів, токени + вартість. |
| **n8n** | Бета-адаптер | SQLite `~/.n8n/database.sqlite`. Виконання робочих процесів, запуски вузлів, підказки AI Agent, модель + токени там, де n8n їх фіксує. |

"Бета-адаптер" означає, що ClawMetry постачає читач для реального формату на диску цього середовища виконання, кожен з яких створено + перевірено на реальному встановленні на реальній машині (див. `tests/fixtures/runtimes/<rt>/`). Адаптери доступні лише для читання; кожен чесно повідомляє про те, що насправді зберігає його середовище виконання (наприклад, PicoClaw/NanoClaw/Cursor не записують вартість токенів на диск). Коли на одному вузлі працює кілька середовищ виконання, перемикач середовищ виконання звужує перегляд сесій до одного для чіткого детального аналізу.

## Відстеження будь-якого SDK-агента — атрибуція вартості поза циклом

Усі перелічені вище середовища виконання записують сесії на диск. Ваш власний **продакшн-агент** — той, що ви створили на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B або звичайному циклі `httpx` — не робить цього. Безконфігураційний перехоплювач ClawMetry все одно захоплює його виклики LLM (вартість, токени, затримку, помилки), використовуючи monkey-patching для `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (або змінна середовища `CLAWMETRY_SOURCE=support-agent`) позначає кожен виклик **іменованим джерелом**, тож кожен продукт, який ви запускаєте, з'являється як власний повноцінний, атрибутований за вартістю рядок на картці **🔌 Out-loop sources** на панелі Overview — виклики, провайдери, затримка, частота помилок для кожного агента. Джерело не встановлено? Виклики все одно відстежуються; картка просто залишається прихованою.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Це той самий шар даних, який живлять адаптери середовищ виконання (DuckDB → хмарний знімок), тож джерела поза циклом синхронізуються з хмарною панеллю так само, як і все інше, з наскрізним шифруванням.

## OpenTelemetry — незалежно від постачальника, надсилайте свої трасування будь-куди

ClawMetry розмовляє **OpenTelemetry** в обох напрямках, використовуючи **семантичні конвенції GenAI**, тож трасування вашого агента ніколи не прив'язані до одного інструменту.

**Експортуйте** кожну сесію — виклики LLM, інструменти, підагенти, токени, вартість — у вигляді спанів OTLP/HTTP GenAI до будь-якого колектора (Datadog, Grafana, Honeycomb або власного OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Заголовки автентифікації та інтервал опитування є опціональними змінними середовища:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Приймайте** — вбудований приймач OTLP приймає трасування та метрики з будь-чого іншого за адресами `/v1/traces` та `/v1/metrics` (`pip install clawmetry[otel]` для прийому protobuf).

Ви отримуєте безконфігураційну, локальну за замовчуванням панель ClawMetry **і** ваші дані в тому бекенді, який вже використовує ваша команда — без прив'язки до постачальника, без другого агента для встановлення.

## Налаштування

Більшості людей не потрібне жодне налаштування. ClawMetry автоматично визначає ваш робочий простір, логи, сесії та cron-завдання.

Якщо вам все ж потрібно налаштувати:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Усі опції: `clawmetry --help`

## Підтримувані канали

ClawMetry показує активність у реальному часі для кожного каналу OpenClaw, який у вас налаштований. У діаграмі Flow з'являються лише канали, які дійсно налаштовані у вашому `openclaw.json` — неналаштовані автоматично приховуються.

Натисніть на будь-який вузол каналу у Flow, щоб побачити перегляд чат-бульбашок у реальному часі з лічильниками вхідних/вихідних повідомлень.

| Канал | Статус | Живий спливаючий перегляд | Примітки |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Повна | ✅ | Повідомлення, статистика, оновлення кожні 10с |
| 💬 **iMessage** | ✅ Повна | ✅ | Читає `~/Library/Messages/chat.db` напряму |
| 💚 **WhatsApp** | ✅ Повна | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Повна | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Повна | ✅ | Виявлення гільдії + каналу |
| 🟪 **Slack** | ✅ Повна | ✅ | Виявлення робочого простору + каналу |
| 🌐 **Webchat** | ✅ Повна | ✅ | Вбудовані веб-сесії UI |
| 📡 **IRC** | ✅ Повна | ✅ | Інтерфейс бульбашок у стилі терміналу |
| 🍏 **BlueBubbles** | ✅ Повна | ✅ | iMessage через BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Повна | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Повна | ✅ | Через плагін бота Teams |
| 🔷 **Mattermost** | ✅ Повна | ✅ | Командний чат із самостійним розміщенням |
| 🟩 **Matrix** | ✅ Повна | ✅ | Децентралізований, підтримка E2EE |
| 🟢 **LINE** | ✅ Повна | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Повна | ✅ | Децентралізовані NIP-04 DM |
| 🟣 **Twitch** | ✅ Повна | ✅ | Чат через з'єднання IRC |
| 🔷 **Feishu/Lark** | ✅ Повна | ✅ | Підписка на події через WebSocket |
| 🔵 **Zalo** | ✅ Повна | ✅ | Zalo Bot API |

> **Автоматичне визначення:** ClawMetry читає ваш `~/.openclaw/openclaw.json` і відображає лише ті канали, які ви дійсно налаштували. Ручне налаштування не потрібне.

## Розгортання в Docker

Хочете запустити ClawMetry в контейнері? Без проблем! 🐳

**Швидкий старт з Docker:**

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

**Приклад Docker Compose:**

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

> **Примітка:** Під час роботи в Docker змонтуйте каталоги даних + логів вашого агента (наприклад, `~/.openclaw`, `~/.claude`, `~/.codex`), щоб ClawMetry міг автоматично визначити ваше налаштування.

## Вимоги

- Python 3.8+
- Flask (встановлюється автоматично через pip)
- Середовище виконання AI-агента на тій самій машині: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents або n8n (або змонтовані томи для Docker)
- Linux або macOS

## Підтримка NemoClaw / OpenShell

ClawMetry автоматично виявляє [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративну обгортку безпеки NVIDIA для OpenClaw, яка запускає агентів всередині ізольованих контейнерів OpenShell.

У більшості випадків додаткове налаштування не потрібне. Демон синхронізації автоматично виявляє файли сесій незалежно від того, знаходяться вони в `~/.openclaw/` на хості чи всередині контейнера OpenShell.

### Як це працює

ClawMetry виявляє NemoClaw двома способами:

1. **Виявлення бінарного файлу** — перевіряє наявність CLI `nemoclaw` та запускає `nemoclaw status` для отримання інформації про пісочницю
2. **Виявлення контейнера** — сканує запущені Docker-контейнери на предмет образів `openshell`, `nemoclaw` або `ghcr.io/nvidia/`, потім читає сесії через змонтовані томи або `docker cp`

Файли сесій, синхронізовані з контейнерів NemoClaw, позначаються метаданими `runtime=nemoclaw` та `container_id` у хмарній панелі, тож ви можете легко відрізнити їх від стандартних сесій OpenClaw.

### Рекомендоване налаштування: демон синхронізації на ХОСТІ

Для найкращого досвіду запускайте демон синхронізації ClawMetry на **хост-машині** (а не всередині пісочниці). Це дозволяє уникнути обмежень мережевої політики NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Демон синхронізації автоматично знайде сесії всередині будь-яких запущених контейнерів OpenShell.

### Опціонально: явна назва пісочниці

Якщо автоматичне визначення не спрацьовує, вкажіть ClawMetry на потрібну пісочницю:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Запуск всередині пісочниці (для досвідчених користувачів)

Якщо вам необхідно запустити демон синхронізації **всередині** пісочниці OpenShell, додайте це правило вихідного трафіку до вашої мережевої політики NemoClaw, щоб він міг досягти API прийому ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

Застосуйте за допомогою:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### Порти та кінцеві точки

| Кінцева точка | Порт | Протокол | Обов'язково |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Так (демон синхронізації → хмара) |
| `localhost:8900` | 8900 | HTTP | Так (локальна панель UI) |
| Сокет Docker (`/var/run/docker.sock`) | — | Unix-сокет | Для виявлення сесій контейнерів |

Демон синхронізації робить лише вихідні виклики HTTPS до `ingest.clawmetry.com`. Вхідні порти не потрібні.

---

## Розгортання в хмарі

Дивіться **[Посібник з тестування хмари](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** щодо SSH-тунелів, зворотного проксі та Docker.

## Тестування

Цей проєкт тестується за допомогою BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрія

ClawMetry надсилає єдиний анонімний пінг "перший запуск" на
`https://app.clawmetry.com/api/install` при першому запуску CLI
`clawmetry` на новій машині. Ми використовуємо це для підрахунку встановлень (це
єдина маркетингова метрика, яку ми маємо для проєкту з відкритим кодом) та щоб дізнатися, які
фреймворки агентів встановили наші користувачі.

**Рівно один POST на встановлення**, що містить:

| Поле | Приклад | Навіщо |
|---|---|---|
| `install_id` | випадковий UUID, збережений у `~/.clawmetry/install_id` | дедублікація; не пов'язаний з вашою електронною поштою чи api_key |
| `version` | `0.12.167` | які версії використовуються |
| `os` / `os_version` | `Darwin` / `25.3.0` | пріоритети підтримки платформ |
| `python` | `3.11.15` | матриця підтримки версій Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | з якими агентами нам варто інтегруватися далі |
| `is_ci` / `ci_provider` | `true` / `github_actions` | відокремлення людських встановлень від шуму CI |

**Що ми НЕ надсилаємо**: IP (хмара визначає код країни на стороні сервера
з запиту, потім відкидає IP), ім'я хосту, ім'я користувача, шлях робочого простору, вміст
файлів, ваш api_key, вашу електронну пошту, будь-що персональне чи специфічне для
робочого простору. Корисне навантаження, що передається, доступне для аудиту в
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Відмовитися** (будь-яке з цих назавжди вимикає телеметрію):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Мережевий збій тут ніколи не блокує роботу `clawmetry` — пінг
надсилається без очікування відповіді у фоновому потоці з тайм-аутом 3 с.

## Історія зірок

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Ліцензія

MIT

---

<p align="center">
  <strong>🦞 Побачте, як думає ваш агент</strong><br>
  <sub>Створено <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Частина екосистеми <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
