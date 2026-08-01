<!-- i18n-src:191e9094d7fa -->
> Українська translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Дивіться, як думає ваш агент.** Спостережуваність у реальному часі для **14 середовищ виконання AI-агентів**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex і ще 10 інших. Одна панель для всього вашого флоту агентів.

> 🌐 **Читати цією мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [більше →](docs/i18n/)

Одна команда. Нуль конфігурації. Автоматичне визначення всього.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**, і все готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Працює з 14 середовищами виконання агентів

ClawMetry почався як інструмент спостережуваності для OpenClaw, а тепер обліковує **весь ваш флот агентів** в одній панелі, автоматично виявляючи кожне середовище виконання на вашій машині:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw і NemoClaw безкоштовні у застосунку з відкритим кодом; інші середовища виконання стають доступними разом з ClawMetry Cloud або з самостійно розміщеною ліцензією Pro. Перемикайте середовища виконання в шапці, і кожна вкладка — вартість, токени, інструменти, трасування — переналаштується під це середовище. Точний розподіл безкоштовного/платного, матрицю рівнів, форму `/api/entitlement` та CLI `clawmetry license` дивіться у **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)**.

## Що ви отримуєте

- **Flow** — Живий анімований діаграма, що показує рух повідомлень через канали, brain, інструменти і назад
- **Overview** — Перевірки стану, теплова карта активності, кількість сесій, інформація про модель
- **Usage** — Відстеження токенів і вартості з розбивкою по днях/тижнях/місяцях
- **Sessions** — Активні сесії агента з моделлю, токенами, останньою активністю
- **Crons** — Заплановані завдання зі статусом, наступним запуском, тривалістю
- **Logs** — Кольорове потокове передавання логів у реальному часі
- **Memory** — Перегляд SOUL.md, MEMORY.md, AGENTS.md, щоденних нотаток
- **Transcripts** — Інтерфейс у вигляді чат-бульбашок для читання історій сесій
- **Alerts** — Ліміти бюджету, тригери частоти помилок, виявлення офлайн-стану агента; маршрутизація до Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Блокування деструктивних видалень, force push, мутацій БД, sudo, встановлення пакетів, мережевих викликів за допомогою підтвердження в один клік

## Скріншоти

### 🧠 Brain — Потік подій агента в реальному часі
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Використання токенів і зведення сесій
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Потік викликів інструментів у реальному часі
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Розбивка вартості за моделлю та сесією
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Переглядач файлів робочого простору
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Стан безпеки та журнал аудиту
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Ліміти бюджету, тригери частоти помилок, вебхуки до Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Блокування ризикованих викликів інструментів до ручного підтвердження; правила захисту на основі політик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Блокування перед виконанням для Claude Code** — одна команда встановлює
хук PreToolUse, який призупиняє відповідні виклики інструментів *перед* їх виконанням і чекає
вашого рішення (один дотик з телефону з увімкненими
[push-сповіщеннями хмари](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

Відмова блокує лише цей один виклик інструменту — агент зберігає свою сесію і може
спробувати інший підхід. Підтвердження з телефону пропускає власний запит на дозвіл
Claude Code (ви вже відповіли). Невідповідні інструменти коштують ~40 мс і
переходять до звичайного потоку дозволів Claude Code. Ви також отримуєте push-сповіщення на телефон, коли
сам Claude Code очікує на вас (сповіщення `permission_prompt` /
`idle_prompt`).

## Встановлення

**Однорядковий варіант (рекомендовано):**
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

Застосунок React v2 знаходиться в `frontend/` і подається за адресою `/v2`, коли
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
`http://localhost:8900`, тож застосунок React може взаємодіяти з локальним сервером Flask
без додаткового налаштування CORS.

Щоб зібрати пакунок, який постачається разом з пакетом Python:

```bash
cd frontend
npm run build
```

Продакшн-збірка записується у `clawmetry/static/v2/dist/`.

## Сумісність із середовищами виконання / агентами

ClawMetry спостерігає за багатьма середовищами виконання AI-агентів, а не лише за OpenClaw. Кожне середовище виконання, відмінне від OpenClaw, постачається з окремим адаптером-читачем, який перетворює нативний формат сесій цього середовища на уніфіковані форми ClawMetry; демон завантажує їх у те саме сховище DuckDB + хмарний знімок, позначаючи середовище виконання, а вкладка повторного відтворення сесії показує **перемикач середовищ виконання**, коли присутнє більше одного. Повну матрицю + посібник з додавання середовищ виконання дивіться в [`docs/compatibility.md`](docs/compatibility.md), а вступ до сімейства OpenClaw — у [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md).

Використовуєте інструмент безпеки агентів [Perplexity numbat](https://github.com/perplexityai/numbat)? ClawMetry за замовчуванням приймає його результати та рішення щодо застосування політик — дивіться [`docs/NUMBAT.md`](docs/NUMBAT.md).

| Середовище виконання / агент | Статус | Примітки |
|---|---|---|
| **OpenClaw** | Нативний | Еталонне середовище виконання, виявляється автоматично |
| **PicoClaw** | Бета-адаптер | Плаский JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Транскрипти, модель, виклики інструментів. |
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
| **n8n** | Бета-адаптер | SQLite `~/.n8n/database.sqlite`. Виконання робочих процесів, запуски вузлів, підказки AI Agent, модель + токени там, де n8n їх записує. |
| **Antigravity** | Бета-адаптер | Brain JSONL у `~/.gemini/<flavor>/brain/`. Розмови, кроки інструментів, міркування, розбивка токенів Gemini для кожної генерації + вартість, витрати фонової генерації. |

"Бета-адаптер" означає, що ClawMetry постачає читач для реального формату на диску цього середовища виконання, кожен з яких створено та перевірено на реальному встановленні на реальній машині (див. `tests/fixtures/runtimes/<rt>/`). Адаптери доступні лише для читання; кожен чесно повідомляє про те, що насправді зберігає це середовище виконання (наприклад, PicoClaw/NanoClaw/Cursor не записують вартість токенів на диск). Коли на одному вузлі працює кілька середовищ виконання, перемикач середовищ виконання обмежує перегляд сесій одним для чіткого поглибленого аналізу.

## Відстеження будь-якого агента SDK — атрибуція вартості поза циклом

Усі перелічені вище середовища виконання записують сесії на диск. Ваш власний **продакшн-агент** — той, що ви створили на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B або звичайному циклі `httpx` — цього не робить. Перехоплювач ClawMetry з нульовою конфігурацією все одно фіксує його виклики LLM (вартість, токени, затримку, помилки), підмінюючи `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (або змінна середовища `CLAWMETRY_SOURCE=support-agent`) позначає кожен виклик **іменованим джерелом**, тож кожен продукт, який ви запускаєте, з'являється як власна повноцінна лінія з можливістю атрибуції вартості в картці панелі **🔌 Out-loop sources** на Overview — виклики, провайдери, затримка, частота помилок для кожного агента. Джерело не вказано? Виклики все одно відстежуються, картка просто залишається прихованою.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Це той самий рівень даних, який живлять адаптери середовищ виконання (DuckDB → хмарний знімок), тож джерела поза циклом синхронізуються з хмарною панеллю так само, як і все інше, з наскрізним шифруванням.

## OpenTelemetry — незалежність від постачальника, надсилайте свої трасування куди завгодно

ClawMetry розмовляє **OpenTelemetry** в обох напрямках, використовуючи **семантичні угоди GenAI**, тож трасування вашого агента ніколи не прив'язані до одного інструменту.

**Експортуйте** кожну сесію — виклики LLM, інструменти, підагенти, токени, вартість — як OTLP/HTTP GenAI spans до будь-якого колектора (Datadog, Grafana, Honeycomb або власний OTel Collector):

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

**Приймайте** — вбудований приймач OTLP приймає трасування та метрики з будь-якого джерела за адресами `/v1/traces` і `/v1/metrics` (`pip install clawmetry[otel]` для прийому protobuf).

Ви отримуєте панель ClawMetry з нульовою конфігурацією, орієнтовану на локальну роботу, **і** свої дані в будь-якому бекенді, який уже використовує ваша команда — без прив'язки до постачальника, без другого агента для встановлення.

## Конфігурація

Більшості людей не потрібна жодна конфігурація. ClawMetry автоматично визначає ваш робочий простір, логи, сесії та cron-завдання.

Якщо вам все ж потрібно налаштувати:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Усі опції: `clawmetry --help`

## Підтримувані канали

ClawMetry показує активність у реальному часі для кожного каналу OpenClaw, який у вас налаштований. У діаграмі Flow з'являються лише ті канали, які дійсно налаштовані у вашому `openclaw.json` — неналаштовані автоматично приховуються.

Натисніть на будь-який вузол каналу у Flow, щоб побачити перегляд у вигляді живих чат-бульбашок з кількістю вхідних/вихідних повідомлень.

| Канал | Статус | Живий спливаючий перегляд | Примітки |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Повна | ✅ | Повідомлення, статистика, оновлення кожні 10с |
| 💬 **iMessage** | ✅ Повна | ✅ | Читає `~/Library/Messages/chat.db` напряму |
| 💚 **WhatsApp** | ✅ Повна | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Повна | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Повна | ✅ | Виявлення гільдії + каналу |
| 🟪 **Slack** | ✅ Повна | ✅ | Виявлення робочого простору + каналу |
| 🌐 **Webchat** | ✅ Повна | ✅ | Вбудовані сесії веб-інтерфейсу |
| 📡 **IRC** | ✅ Повна | ✅ | Інтерфейс бульбашок у стилі термінала |
| 🍏 **BlueBubbles** | ✅ Повна | ✅ | iMessage через BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Повна | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Повна | ✅ | Через плагін бота Teams |
| 🔷 **Mattermost** | ✅ Повна | ✅ | Самостійно розміщений командний чат |
| 🟩 **Matrix** | ✅ Повна | ✅ | Децентралізовано, підтримка E2EE |
| 🟢 **LINE** | ✅ Повна | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Повна | ✅ | Децентралізовані NIP-04 DM |
| 🟣 **Twitch** | ✅ Повна | ✅ | Чат через з'єднання IRC |
| 🔷 **Feishu/Lark** | ✅ Повна | ✅ | Підписка на події через WebSocket |
| 🔵 **Zalo** | ✅ Повна | ✅ | Zalo Bot API |

> **Автоматичне виявлення:** ClawMetry читає ваш `~/.openclaw/openclaw.json` і відображає лише ті канали, які ви дійсно налаштували. Ручне налаштування не потрібне.

## Розгортання Docker

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

> **Примітка:** Під час запуску в Docker змонтуйте каталоги даних + логів вашого агента (наприклад, `~/.openclaw`, `~/.claude`, `~/.codex`), щоб ClawMetry міг автоматично визначити ваше налаштування.

## Вимоги

- Python 3.8+
- Flask (встановлюється автоматично через pip)
- Середовище виконання AI-агента на тій самій машині: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi, Deep Agents, n8n або Antigravity (або змонтовані томи для Docker)
- Linux або macOS

## Підтримка NemoClaw / OpenShell

ClawMetry автоматично виявляє [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративну оболонку безпеки NVIDIA для OpenClaw, яка запускає агентів усередині ізольованих контейнерів OpenShell.

У більшості випадків додаткова конфігурація не потрібна. Демон синхронізації автоматично виявляє файли сесій незалежно від того, чи знаходяться вони в `~/.openclaw/` на хості, чи всередині контейнера OpenShell.

### Як це працює

ClawMetry виявляє NemoClaw двома способами:

1. **Виявлення бінарного файлу** — перевіряє наявність CLI `nemoclaw` і запускає `nemoclaw status`, щоб отримати інформацію про пісочницю
2. **Виявлення контейнера** — сканує запущені контейнери Docker на предмет образів `openshell`, `nemoclaw` або `ghcr.io/nvidia/`, а потім читає сесії через змонтовані томи або `docker cp`

Файли сесій, синхронізовані з контейнерів NemoClaw, позначаються метаданими `runtime=nemoclaw` і `container_id` у хмарній панелі, тож ви можете відрізнити їх від стандартних сесій OpenClaw з першого погляду.

### Рекомендоване налаштування: демон синхронізації на ХОСТІ

Для найкращого досвіду запускайте демон синхронізації ClawMetry на **хостовій машині** (не всередині пісочниці). Це дозволяє уникнути обмежень мережевої політики NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Демон синхронізації автоматично знайде сесії всередині будь-яких запущених контейнерів OpenShell.

### Необов'язково: явна назва пісочниці

Якщо автоматичне виявлення не спрацьовує, вкажіть ClawMetry потрібну пісочницю:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Запуск усередині пісочниці (для досвідчених користувачів)

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
| `localhost:8900` | 8900 | HTTP | Так (локальний інтерфейс панелі) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Для виявлення сесій контейнера |

Демон синхронізації виконує лише вихідні виклики HTTPS до `ingest.clawmetry.com`. Вхідні порти не потрібні.

---

## Розгортання в хмарі

Дивіться **[Посібник з тестування хмари](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** щодо тунелів SSH, зворотного проксі та Docker.

## Тестування

Цей проєкт тестується за допомогою BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрія

ClawMetry надсилає анонімні пінги життєвого циклу встановлення на
`https://app.clawmetry.com/api/install`: один пінг `install` під час першого
запуску CLI `clawmetry` на новій машині, один пінг `update`
під час першого запуску після оновлення до нової версії, і один пінг
`onboarded`, коли ви завершуєте вибір ознайомлення в панелі. Ми використовуємо це,
щоб рахувати реальні встановлення (сирі числа завантажень PyPI на ~98% складаються з дзеркал, CI
та повторних завантажень автооновлення), а також щоб дізнаватися, які фреймворки агентів і
версії дійсно використовуються.

**Максимум один POST-запит для кожної події життєвого циклу для кожної версії**, що містить:

| Поле | Приклад | Навіщо |
|---|---|---|
| `install_id` | випадковий UUID, збережений у `~/.clawmetry/install_id` | дедуплікація; анонімний, доки ви явно не підключите синхронізацію Cloud (тоді автентифікований heartbeat демона несе його, пов'язуючи це встановлення з вашим обліковим записом) |
| `event` | `install` / `update` / `onboarded` | нове встановлення чи оновлення наявного |
| `version` | `0.12.167` | які версії використовуються |
| `os` / `os_version` | `Darwin` / `25.3.0` | пріоритети підтримки платформ |
| `python` | `3.11.15` | матриця підтримки версій Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | з якими агентами нам слід інтегруватися далі |
| `is_ci` / `ci_provider` | `true` / `github_actions` | відокремлення людських встановлень від шуму CI |

**Що ми НЕ надсилаємо**: IP (хмара визначає код країни на стороні сервера
з запиту, потім відкидає IP), ім'я хоста, ім'я користувача, шлях до робочого простору, вміст файлів,
ваш api_key, вашу електронну пошту, будь-що персональне або специфічне для робочого простору. Корисне навантаження
можна перевірити в [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Відмовитися** (будь-який з цих способів вимикає це назавжди):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Збій мережі тут ніколи не блокує роботу `clawmetry` — пінг
є fire-and-forget у потоці демона з тайм-аутом 3 с.

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
  <strong>🦞 Дивіться, як думає ваш агент</strong><br>
  <sub>Створено <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Частина екосистеми <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
