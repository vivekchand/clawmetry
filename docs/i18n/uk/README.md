<!-- i18n-src:c422fb7dd0da -->
> Українська translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Дивіться, як мислить ваш агент.** Спостережуваність у реальному часі для **20 середовищ виконання AI-агентів**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex та ще 16 інших. Одна панель для всього вашого флоту агентів.

> 🌐 **Читайте цю сторінку іншими мовами:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Одна команда. Нуль налаштувань. Автоматично визначає все.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**, і на цьому все.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Працює з 20 середовищами виконання агентів

ClawMetry почалася як інструмент спостережуваності для OpenClaw, а тепер вимірює **весь ваш флот агентів** в одній панелі, автоматично визначаючи кожне середовище виконання на вашій машині:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw і NemoClaw безкоштовні у застосунку з відкритим кодом; інші середовища виконання стають доступними з ClawMetry Cloud або самостійно розміщеною ліцензією Pro. Перемикайте середовища виконання з панелі заголовка, і кожна вкладка — вартість, токени, інструменти, трасування — перемасштабується під це середовище виконання. Дивіться **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** для точного розподілу безкоштовне/платне, матриці рівнів, структури `/api/entitlement` та CLI `clawmetry license`.

## Що ви отримуєте

- **Flow** — Живий анімований діаграма, що показує рух повідомлень через канали, мозок, інструменти та назад
- **Overview** — Перевірки стану, теплова карта активності, кількість сесій, інформація про модель
- **Usage** — Відстеження токенів і вартості з щоденною/щотижневою/щомісячною розбивкою
- **Sessions** — Активні сесії агента з моделлю, токенами, останньою активністю
- **Crons** — Заплановані завдання зі статусом, наступним запуском, тривалістю
- **Logs** — Кольорове потокове передавання логів у реальному часі
- **Memory** — Перегляд SOUL.md, MEMORY.md, AGENTS.md, щоденних нотаток
- **Transcripts** — Інтерфейс у вигляді чат-бульбашок для читання історії сесій
- **Alerts** — Ліміти бюджету, тригери частоти помилок, виявлення офлайн-агента; маршрутизація до Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Блокування деструктивних видалень, примусових пушів, мутацій БД, sudo, встановлень пакетів, мережевих викликів за одним підтвердженням

## Скріншоти

### 🧠 Brain — Потік подій живого агента
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Використання токенів і зведення сесій
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Потік викликів інструментів у реальному часі
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Розбивка вартості за моделлю та сесією
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Оглядач файлів робочого простору
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Стан захищеності та журнал аудиту
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Ліміти бюджету, тригери частоти помилок, вебхуки до Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Блокування ризикованих викликів інструментів за ручним підтвердженням; правила захисту на основі політик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Блокування перед виконанням для Claude Code** — одна команда встановлює
хук PreToolUse, який призупиняє відповідні виклики інструментів *до* їхнього виконання і чекає
на ваше рішення (одне натискання з телефону з увімкненими
[хмарними push-сповіщеннями](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Відмова блокує лише цей один виклик інструменту — агент зберігає свою сесію і може
спробувати інший підхід. Схвалення з телефону пропускає власний
запит на дозвіл Claude Code (ви вже відповіли). Невідповідні інструменти коштують ~40 мс і
переходять до звичайного потоку дозволів Claude Code. Ви також отримуєте push-сповіщення на телефон, коли Claude Code сам
очікує на вас (сповіщення `permission_prompt` / `idle_prompt`).

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

**Із джерельного коду:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## Розробка фронтенду v2

React-застосунок v2 знаходиться в `frontend/` і обслуговується за адресою `/v2`, коли
сервер Flask запущено з увімкненим v2.

Під час розробки використовуйте два термінали:

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

Щоб зібрати пакет, який постачається з Python-пакетом:

```bash
cd frontend
npm run build
```

Продакшн-збірка записується в `clawmetry/static/v2/dist/`.

## Сумісність середовищ виконання / агентів

ClawMetry спостерігає за багатьма середовищами виконання AI-агентів, а не лише за OpenClaw. Кожне середовище виконання, відмінне від OpenClaw, постачається з окремим адаптером-читачем, який перетворює його рідний формат сесії у уніфіковані структури ClawMetry; демон приймає їх у те саме сховище DuckDB + хмарний знімок, позначені відповідним середовищем виконання, а вкладка повтору сесії показує **перемикач середовища виконання**, коли їх присутньо більше одного. Дивіться [`docs/compatibility.md`](docs/compatibility.md) для повної матриці + посібника з додавання середовищ виконання, і [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) для базового ознайомлення з родиною OpenClaw.

Використовуєте інструмент безпеки агентів [Perplexity numbat](https://github.com/perplexityai/numbat)? ClawMetry приймає його висновки та рішення щодо примусового виконання "з коробки" — дивіться [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Середовище виконання / агент | Статус | Примітки |
|---|---|---|
| **OpenClaw** | Нативне | Еталонне середовище виконання, визначається автоматично |
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
| **Antigravity** | Бета-адаптер | Brain JSONL у `~/.gemini/<flavor>/brain/`. Розмови, кроки інструментів, міркування, розбивка токенів Gemini для кожної генерації + вартість, витрати фонової генерації. |
| **GitHub Copilot** | Бета-адаптер | `events.jsonl` Copilot CLI у `~/.copilot/session-state/` + журнал використання `session-store.db` для кожного виклику. Розмови, виклики інструментів, маршрутизація моделі, розбивка токенів з урахуванням кешу, вартість у AI-кредитах, що виставляються постачальником. |
| **Grok** | Бета-адаптер | xAI Grok Build CLI (бінарник на Rust у `~/.grok/bin/grok`): глобальний журнал подій `~/.grok/logs/unified.jsonl` + `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}` для кожної сесії. Розмови, розбивка токенів для кожного ходу, маршрутизація моделі, та вихідне навантаження репозиторію CLI, що зберігається в `~/.grok/upload_queue/`, щоб ви бачили, що залишило вашу машину. |

"Бета-адаптер" означає, що ClawMetry постачає читач для реального формату на диску цього середовища виконання, кожен з яких створено + перевірено на реальному встановленні на реальній машині (дивіться `tests/fixtures/runtimes/<rt>/`). Адаптери доступні лише для читання; кожен чесно відображає те, що його середовище виконання фактично зберігає (наприклад, PicoClaw/NanoClaw/Cursor не записують вартість токенів на диск). Коли на одному вузлі працює кілька середовищ виконання, перемикач середовища виконання обмежує перегляд сесій одним для чіткого глибокого аналізу.

## Відстеження будь-якого SDK-агента — атрибуція вартості поза циклом

Усі середовища виконання вище записують сесії на диск. Ваш власний **продакшн-агент** — той, що ви створили на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, або на звичайному циклі `httpx` — цього не робить. Безконфігураційний перехоплювач ClawMetry все одно фіксує його LLM-виклики (вартість, токени, затримку, помилки), використовуючи monkey-patching для `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (або змінна середовища `CLAWMETRY_SOURCE=support-agent`) позначає кожен виклик **іменованим джерелом**, тож кожен продукт, який ви запускаєте, з'являється як власний повноцінний рядок з можливістю атрибуції вартості в картці панелі **🔌 Джерела поза циклом** на вкладці Overview — виклики, постачальники, затримка, частота помилок для кожного агента. Джерело не вказано? Виклики все одно відстежуються, картка просто залишається прихованою.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Це той самий шар даних, який живлять адаптери середовищ виконання (DuckDB → хмарний знімок), тому джерела поза циклом синхронізуються з хмарною панеллю так само, як і все інше, з наскрізним шифруванням.

## OpenTelemetry — нейтральний до постачальника, надсилайте трасування куди завгодно

ClawMetry розмовляє мовою **OpenTelemetry** в обидва боки, використовуючи **семантичні конвенції GenAI**, тож трасування вашого агента ніколи не будуть прив'язані до одного інструменту.

**Експортуйте** кожну сесію — виклики LLM, інструменти, підагенти, токени, вартість — як спани OTLP/HTTP GenAI до будь-якого колектора (Datadog, Grafana, Honeycomb або власного OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Заголовки автентифікації та інтервал опитування є необов'язковими змінними середовища:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**Приймайте** — вбудований приймач OTLP приймає трасування, логи та метрики від будь-чого іншого за адресами `/v1/traces`, `/v1/logs` та `/v1/metrics`. Направте будь-який застосунок, інструментований OpenTelemetry, на нього:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

Трасування та логи OTLP/JSON працюють на звичайному `pip install clawmetry`, без додаткових пакетів. Приймання Protobuf (та метрики OTLP/JSON) потребує `pip install clawmetry[otel]`. Застосунок, що встановлює власне `service.name`, з'являється як окремий агент у перемикачі середовищ виконання, зі своєю вартістю та токенами.

Ви отримуєте безконфігураційну, локально-орієнтовану панель ClawMetry **і** ваші дані в будь-якому бекенді, який вже використовує ваша команда — без прив'язки до постачальника, без другого агента для встановлення.

## Налаштування

Більшості людей не потрібне жодне налаштування. ClawMetry автоматично визначає ваш робочий простір, логи, сесії та cron-завдання.

Якщо вам все ж потрібно щось налаштувати:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Усі опції: `clawmetry --help`

## Підтримувані канали

ClawMetry показує активність у реальному часі для кожного каналу OpenClaw, який у вас налаштований. У діаграмі Flow з'являються лише канали, які дійсно налаштовані у вашому `openclaw.json` — неналаштовані автоматично приховуються.

Клацніть на будь-якому вузлі каналу у Flow, щоб побачити живий перегляд у вигляді чат-бульбашок з кількістю вхідних/вихідних повідомлень.

| Канал | Статус | Живий спливаючий перегляд | Примітки |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Повна | ✅ | Повідомлення, статистика, оновлення кожні 10с |
| 💬 **iMessage** | ✅ Повна | ✅ | Читає `~/Library/Messages/chat.db` безпосередньо |
| 💚 **WhatsApp** | ✅ Повна | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Повна | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Повна | ✅ | Визначення гільдії + каналу |
| 🟪 **Slack** | ✅ Повна | ✅ | Визначення робочого простору + каналу |
| 🌐 **Webchat** | ✅ Повна | ✅ | Вбудовані сесії веб-інтерфейсу |
| 📡 **IRC** | ✅ Повна | ✅ | Інтерфейс у стилі термінальних бульбашок |
| 🍏 **BlueBubbles** | ✅ Повна | ✅ | iMessage через REST API BlueBubbles |
| 🔵 **Google Chat** | ✅ Повна | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Повна | ✅ | Через плагін бота Teams |
| 🔷 **Mattermost** | ✅ Повна | ✅ | Самостійно розміщений командний чат |
| 🟩 **Matrix** | ✅ Повна | ✅ | Децентралізований, з підтримкою E2EE |
| 🟢 **LINE** | ✅ Повна | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Повна | ✅ | Децентралізовані NIP-04 DM |
| 🟣 **Twitch** | ✅ Повна | ✅ | Чат через з'єднання IRC |
| 🔷 **Feishu/Lark** | ✅ Повна | ✅ | Підписка на події через WebSocket |
| 🔵 **Zalo** | ✅ Повна | ✅ | Zalo Bot API |

> **Автоматичне визначення:** ClawMetry читає ваш `~/.openclaw/openclaw.json` і рендерить лише ті канали, які ви дійсно налаштували. Ручне налаштування не потрібне.

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

> **Примітка:** При запуску в Docker змонтуйте директорії даних + логів вашого агента (наприклад, `~/.openclaw`, `~/.claude`, `~/.codex`), щоб ClawMetry могла автоматично визначити ваше налаштування.

## Вимоги

- Python 3.8+
- Flask (встановлюється автоматично через pip)
- Середовище виконання AI-агента на тій самій машині: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n, Antigravity, GitHub Copilot, Grok, або QM (або змонтовані томи для Docker)
- Linux або macOS

## Підтримка NemoClaw / OpenShell

ClawMetry автоматично визначає [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративну обгортку безпеки NVIDIA для OpenClaw, яка запускає агентів всередині ізольованих (sandboxed) контейнерів OpenShell.

У більшості випадків додаткове налаштування не потрібне. Демон синхронізації автоматично виявляє файли сесій незалежно від того, чи знаходяться вони в `~/.openclaw/` на хості, чи всередині контейнера OpenShell.

### Як це працює

ClawMetry визначає NemoClaw двома способами:

1. **Визначення бінарника** — перевіряє наявність CLI `nemoclaw` і запускає `nemoclaw status`, щоб отримати інформацію про пісочницю
2. **Визначення контейнера** — сканує запущені Docker-контейнери на предмет образів `openshell`, `nemoclaw`, або `ghcr.io/nvidia/`, потім читає сесії через змонтовані томи або `docker cp`

Файли сесій, синхронізовані з контейнерів NemoClaw, позначаються метаданими `runtime=nemoclaw` та `container_id` у хмарній панелі, тож ви можете відрізнити їх від звичайних сесій OpenClaw з першого погляду.

### Рекомендоване налаштування: демон синхронізації на ХОСТІ

Для найкращого досвіду запускайте демон синхронізації ClawMetry на **хост-машині** (не всередині пісочниці). Це дозволяє уникнути обмежень мережевої політики NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Демон синхронізації автоматично знайде сесії всередині будь-яких запущених контейнерів OpenShell.

### Необов'язково: явна назва пісочниці

Якщо автоматичне визначення не працює, вкажіть ClawMetry потрібну пісочницю:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Запуск всередині пісочниці (для досвідчених користувачів)

Якщо вам потрібно запустити демон синхронізації **всередині** пісочниці OpenShell, додайте це правило вихідного трафіку до вашої мережевої політики NemoClaw, щоб він міг досягти API прийому ClawMetry:

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
| `localhost:8900` | 8900 | HTTP | Так (локальний інтерфейс панелі) |
| Сокет Docker (`/var/run/docker.sock`) | — | Unix socket | Для виявлення сесій контейнера |

Демон синхронізації робить лише вихідні виклики HTTPS до `ingest.clawmetry.com`. Вхідні порти не потрібні.

---

## Хмарне розгортання

Дивіться **[Посібник з тестування в хмарі](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** для SSH-тунелів, зворотного проксі та Docker.

## Тестування

Цей проєкт тестується за допомогою BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрія

ClawMetry надсилає анонімні пінги про життєвий цикл встановлення на
`https://app.clawmetry.com/api/install`: один пінг `install` під час
першого запуску CLI `clawmetry` на новій машині, один пінг `update`
при першому запуску після оновлення до нової версії, і один пінг
`onboarded`, коли ви завершуєте вибір ознайомлення в панелі. Ми використовуємо це,
щоб порахувати реальні встановлення (сирі цифри завантажень PyPI на ~98% складаються з дзеркал, CI
та повторних завантажень при автооновленні) і дізнатися, які фреймворки агентів та
версії дійсно використовуються.

**Не більше одного POST-запиту на подію життєвого циклу для кожної версії**, що містить:

| Поле | Приклад | Навіщо |
|---|---|---|
| `install_id` | випадковий UUID, збережений у `~/.clawmetry/install_id` | дедублікація; анонімний, доки ви явно не підключите хмарну синхронізацію (тоді автентифікований heartbeat демона несе його, зв'язуючи це встановлення з вашим обліковим записом) |
| `event` | `install` / `update` / `onboarded` | нове встановлення чи оновлення існуючого |
| `version` | `0.12.167` | які версії використовуються |
| `os` / `os_version` | `Darwin` / `25.3.0` | пріоритети підтримки платформ |
| `python` | `3.11.15` | матриця підтримки версій Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | з якими агентами нам слід інтегруватися далі |
| `is_ci` / `ci_provider` | `true` / `github_actions` | відокремити людські встановлення від шуму CI |

**Що ми НЕ надсилаємо**: IP (хмара визначає код країни на стороні сервера
з запиту, а потім відкидає IP), ім'я хоста, ім'я користувача, шлях робочого простору,
вміст файлів, ваш api_key, вашу електронну пошту, будь-що персональне чи специфічне для
робочого простору. Мережевий пакет даних можна перевірити в
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Відмовитися** (будь-який з цих способів вимикає це назавжди):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Збій мережі тут ніколи не блокує роботу `clawmetry` — пінг
надсилається без очікування відповіді (fire-and-forget) у потоці демона з тайм-аутом 3 с.

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
  <strong>🦞 Дивіться, як мислить ваш агент</strong><br>
  <sub>Створено <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Частина екосистеми <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
