<!-- i18n-src:8f42d460a973 -->
> Українська translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Побачте, як думає ваш агент.** Спостережуваність у реальному часі для **14 середовищ виконання AI-агентів**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex та ще 10 інших. Одна панель для всього вашого флоту агентів.

> 🌐 **Читати цією мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [більше →](docs/i18n/)

Одна команда. Без налаштувань. Автоматичне визначення всього.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**, і все готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Працює з 14 середовищами виконання агентів

ClawMetry починався як інструмент спостережуваності для OpenClaw, а тепер вимірює **весь ваш флот агентів** на одній панелі, автоматично визначаючи кожне середовище виконання на вашій машині:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw і NemoClaw безкоштовні у застосунку з відкритим кодом; інші середовища виконання активуються через ClawMetry Cloud або самостійно розміщену ліцензію Pro. Перемикайте середовища виконання з верхньої панелі, і кожна вкладка — вартість, токени, інструменти, трасування — переорієнтовується на це середовище. Дивіться **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** для точного розподілу безкоштовного/платного, матриці рівнів, форми `/api/entitlement` та CLI `clawmetry license`.

## Що ви отримуєте

- **Flow** — Живий анімований діаграма, що показує потік повідомлень через канали, мозок, інструменти та назад
- **Overview** — Перевірки стану, теплова карта активності, кількість сесій, інформація про модель
- **Usage** — Відстеження токенів і вартості з розбивкою по днях/тижнях/місяцях
- **Sessions** — Активні сесії агента з моделлю, токенами, останньою активністю
- **Crons** — Заплановані завдання зі статусом, наступним запуском, тривалістю
- **Logs** — Кольорове потокове відображення журналів у реальному часі
- **Memory** — Перегляд SOUL.md, MEMORY.md, AGENTS.md, щоденних нотаток
- **Transcripts** — Інтерфейс у вигляді бульбашок чату для читання історії сесій
- **Alerts** — Обмеження бюджету, тригери частоти помилок, виявлення офлайн-агента; маршрутизація до Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Блокування деструктивних видалень, примусових пушів, мутацій БД, sudo, встановлень пакетів, мережевих викликів за одним підтвердженням в один клік

## Скріншоти

### 🧠 Brain — Потік подій агента в реальному часі
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Використання токенів і зведення сесій
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Потік викликів інструментів у реальному часі
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Розбивка вартості за моделлю та сесією
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Оглядач файлів робочого простору
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Стан безпеки та журнал аудиту
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Обмеження бюджету, тригери частоти помилок, вебхуки до Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Блокування ризикованих викликів інструментів за ручним підтвердженням; правила захисту на основі політик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

Застосунок React v2 знаходиться в `frontend/` і обслуговується за адресою `/v2`, коли
сервер Flask запущено з увімкненим v2.

Використовуйте два термінали під час розробки:

```bash
# Термінал 1: Flask API/сервер на :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Термінал 2: сервер розробки Vite на :5173
cd frontend
nvm use
npm ci
npm run dev
```

Відкрийте `http://localhost:5173/v2/`. Vite проксує запити `/api` до
`http://localhost:8900`, тому застосунок React може взаємодіяти з локальним сервером Flask
без додаткового налаштування CORS.

Щоб зібрати пакет, який постачається з пакетом Python:

```bash
cd frontend
npm run build
```

Виробничий пакет записується в `clawmetry/static/v2/dist/`.

## Сумісність середовищ виконання / агентів

ClawMetry спостерігає за багатьма середовищами виконання AI-агентів, не лише за OpenClaw. Кожне середовище виконання, відмінне від OpenClaw, постачається з окремим адаптером-читачем, що перетворює його рідний формат сесії на уніфіковані форми ClawMetry; демон приймає їх у те саме сховище DuckDB + хмарний знімок, позначаючи середовищем виконання, а вкладка відтворення сесії показує **перемикач середовищ виконання**, коли присутнє більше одного. Дивіться [`docs/compatibility.md`](docs/compatibility.md) для повної матриці та посібника з додавання середовищ виконання, а також [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) для введення в сімейство OpenClaw.

| Середовище виконання / агент | Статус | Примітки |
|---|---|---|
| **OpenClaw** | Рідне | Еталонне середовище виконання, визначається автоматично |
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

"Бета-адаптер" означає, що ClawMetry постачає читач для реального формату зберігання даних цього середовища виконання на диску, кожен з яких створено й перевірено на реальному встановленні на реальній машині (див. `tests/fixtures/runtimes/<rt>/`). Адаптери доступні лише для читання; кожен чесно повідомляє про те, що насправді зберігає його середовище виконання (наприклад, PicoClaw/NanoClaw/Cursor не записують вартість токенів на диск). Коли на одному вузлі працює кілька середовищ виконання, перемикач середовищ виконання обмежує перегляд сесій одним для чіткого детального аналізу.

## Відстеження будь-якого SDK-агента — атрибуція вартості поза циклом

Наведені вище середовища виконання записують сесії на диск. Ваш власний **виробничий агент** — той, що ви створили на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B, або звичайному циклі `httpx` — цього не робить. Перехоплювач ClawMetry без налаштування все одно фіксує його виклики LLM (вартість, токени, затримку, помилки), підмінюючи `httpx`/`requests`:

```python
import clawmetry.track            # активувати перехоплювач
clawmetry.track.set_source("support-agent")   # назвати цей продукт

# ...ваш агент працює як зазвичай; кожен виклик LLM тепер відстежується + атрибутується.
```

`set_source()` (або змінна середовища `CLAWMETRY_SOURCE=support-agent`) позначає кожен виклик **іменованим джерелом**, тому кожен продукт, який ви запускаєте, з'являється як власний рядок першого класу з можливістю атрибуції вартості на картці **🔌 Джерела поза циклом** на панелі Overview — виклики, провайдери, затримка, частота помилок для кожного агента. Джерело не встановлено? Виклики все одно відстежуються; картка просто залишається прихованою.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Це той самий шар даних, який живлять адаптери середовищ виконання (DuckDB → хмарний знімок), тому джерела поза циклом синхронізуються з хмарною панеллю так само, як і все інше, з наскрізним шифруванням.

## OpenTelemetry — незалежний від постачальника, надсилайте трасування будь-куди

ClawMetry розмовляє **OpenTelemetry** в обох напрямках, використовуючи **семантичні конвенції GenAI**, тому трасування вашого агента ніколи не прив'язані до одного інструмента.

**Експортуйте** кожну сесію — виклики LLM, інструменти, підагентів, токени, вартість — як проміжки OTLP/HTTP GenAI до будь-якого колектора (Datadog, Grafana, Honeycomb або власний OTel Collector):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# еквівалентно:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

Заголовки автентифікації та інтервал опитування є необов'язковими змінними середовища:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # додаткові HTTP-заголовки
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # секунди (за замовчуванням 60)
```

**Прийом** — вбудований приймач OTLP приймає трасування та метрики з будь-чого іншого за адресами `/v1/traces` і `/v1/metrics` (`pip install clawmetry[otel]` для прийому protobuf).

Ви отримуєте панель ClawMetry без налаштувань, локальну за замовчуванням, **і** ваші дані в будь-якому бекенді, який уже використовує ваша команда — без прив'язки, без другого агента для встановлення.

## Налаштування

Більшості людей не потрібні жодні налаштування. ClawMetry автоматично визначає ваш робочий простір, журнали, сесії та cron-завдання.

Якщо вам все ж потрібно налаштувати:

```bash
clawmetry --port 9000              # Власний порт (за замовчуванням: 8900)
clawmetry --host 127.0.0.1         # Прив'язка лише до localhost
clawmetry --workspace ~/mybot      # Власний шлях до робочого простору
clawmetry --name "Alice"           # Ваше ім'я у візуалізації Flow
```

Усі параметри: `clawmetry --help`

## Підтримувані канали

ClawMetry показує живу активність для кожного каналу OpenClaw, який ви налаштували. У діаграмі Flow з'являються лише ті канали, які фактично налаштовані у вашому `openclaw.json` — неналаштовані автоматично приховуються.

Натисніть на будь-який вузол каналу у Flow, щоб побачити живий вигляд бульбашок чату з кількістю вхідних/вихідних повідомлень.

| Канал | Статус | Живий спливаючий вигляд | Примітки |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Повна | ✅ | Повідомлення, статистика, оновлення кожні 10с |
| 💬 **iMessage** | ✅ Повна | ✅ | Читає `~/Library/Messages/chat.db` напряму |
| 💚 **WhatsApp** | ✅ Повна | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Повна | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Повна | ✅ | Визначення гільдії + каналу |
| 🟪 **Slack** | ✅ Повна | ✅ | Визначення робочого простору + каналу |
| 🌐 **Webchat** | ✅ Повна | ✅ | Вбудовані веб-сесії UI |
| 📡 **IRC** | ✅ Повна | ✅ | Інтерфейс бульбашок у стилі термінала |
| 🍏 **BlueBubbles** | ✅ Повна | ✅ | iMessage через REST API BlueBubbles |
| 🔵 **Google Chat** | ✅ Повна | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Повна | ✅ | Через плагін бота Teams |
| 🔷 **Mattermost** | ✅ Повна | ✅ | Самостійно розміщений командний чат |
| 🟩 **Matrix** | ✅ Повна | ✅ | Децентралізований, підтримка E2EE |
| 🟢 **LINE** | ✅ Повна | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Повна | ✅ | Децентралізовані особисті повідомлення NIP-04 |
| 🟣 **Twitch** | ✅ Повна | ✅ | Чат через з'єднання IRC |
| 🔷 **Feishu/Lark** | ✅ Повна | ✅ | Підписка на події через WebSocket |
| 🔵 **Zalo** | ✅ Повна | ✅ | Zalo Bot API |

> **Автоматичне визначення:** ClawMetry читає ваш `~/.openclaw/openclaw.json` і відображає лише ті канали, які ви фактично налаштували. Ручне налаштування не потрібне.

## Розгортання в Docker

Хочете запустити ClawMetry в контейнері? Немає проблем! 🐳

**Швидкий старт з Docker:**

```bash
# Зібрати образ
docker build -t clawmetry .

# Запустити з налаштуваннями за замовчуванням
docker run -p 8900:8900 clawmetry

# Або підключити каталог даних вашого агента (показано: ~/.openclaw для OpenClaw)
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

> **Примітка:** Під час роботи в Docker підключіть каталоги даних + журналів вашого агента (наприклад, `~/.openclaw`, `~/.claude`, `~/.codex`), щоб ClawMetry міг автоматично визначити ваше налаштування.

## Вимоги

- Python 3.8+
- Flask (встановлюється автоматично через pip)
- Середовище виконання AI-агента на тій самій машині: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw, PicoClaw, Pi або Deep Agents (або підключені томи для Docker)
- Linux або macOS

## Підтримка NemoClaw / OpenShell

ClawMetry автоматично визначає [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративну обгортку безпеки NVIDIA для OpenClaw, яка запускає агентів у ізольованих контейнерах OpenShell.

У більшості випадків додаткове налаштування не потрібне. Демон синхронізації автоматично виявляє файли сесій незалежно від того, чи знаходяться вони в `~/.openclaw/` на хості, чи всередині контейнера OpenShell.

### Як це працює

ClawMetry виявляє NemoClaw двома способами:

1. **Виявлення бінарного файлу** — перевіряє наявність CLI `nemoclaw` і запускає `nemoclaw status`, щоб отримати інформацію про пісочницю
2. **Виявлення контейнера** — сканує запущені контейнери Docker на наявність образів `openshell`, `nemoclaw` або `ghcr.io/nvidia/`, а потім читає сесії через підключені томи або `docker cp`

Файли сесій, синхронізовані з контейнерів NemoClaw, позначаються метаданими `runtime=nemoclaw` та `container_id` у хмарній панелі, тому ви можете відрізнити їх від стандартних сесій OpenClaw одним поглядом.

### Рекомендоване налаштування: демон синхронізації на ХОСТІ

Для найкращого досвіду запускайте демон синхронізації ClawMetry на **хост-машині** (не всередині пісочниці). Це дозволяє уникнути обмежень мережевої політики NemoClaw.

```bash
# На хості (поза пісочницею)
pip install clawmetry
clawmetry connect
clawmetry sync
```

Демон синхронізації автоматично знайде сесії всередині будь-яких запущених контейнерів OpenShell.

### Необов'язково: явна назва пісочниці

Якщо автоматичне визначення не працює, вкажіть ClawMetry на потрібну пісочницю:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Запуск всередині пісочниці (розширено)

Якщо вам необхідно запустити демон синхронізації **всередині** пісочниці OpenShell, додайте це правило вихідного трафіку до вашої мережевої політики NemoClaw, щоб він міг дістатися API прийому ClawMetry:

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
| `localhost:8900` | 8900 | HTTP | Так (локальний UI панелі) |
| Сокет Docker (`/var/run/docker.sock`) | — | Unix-сокет | Для виявлення сесій контейнера |

Демон синхронізації здійснює лише вихідні виклики HTTPS до `ingest.clawmetry.com`. Вхідні порти не потрібні.

---

## Хмарне розгортання

Дивіться **[Посібник з тестування хмари](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** для тунелів SSH, зворотного проксі та Docker.

## Тестування

Цей проєкт тестується за допомогою BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрія

ClawMetry надсилає один анонімний пінг "першого запуску" на
`https://app.clawmetry.com/api/install` під час першого запуску CLI
`clawmetry` на новій машині. Ми використовуємо це для підрахунку встановлень (єдина
маркетингова метрика, яку ми маємо для проєкту з відкритим кодом) і щоб дізнатися, які
агентські фреймворки встановили наші користувачі.

**Рівно один POST на встановлення**, що містить:

| Поле | Приклад | Навіщо |
|---|---|---|
| `install_id` | випадковий UUID, що зберігається у `~/.clawmetry/install_id` | дедуплікація; не пов'язано з вашою поштою чи api_key |
| `version` | `0.12.167` | які версії використовуються |
| `os` / `os_version` | `Darwin` / `25.3.0` | пріоритети підтримки платформ |
| `python` | `3.11.15` | матриця підтримки версій Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | з якими агентами нам слід інтегруватися далі |
| `is_ci` / `ci_provider` | `true` / `github_actions` | відокремлення людських встановлень від шуму CI |

**Що ми НЕ надсилаємо**: IP (хмара визначає код країни на стороні сервера
з запиту, а потім відкидає IP), ім'я хоста, ім'я користувача, шлях
робочого простору, вміст файлів, ваш api_key, вашу пошту, будь-що
особисте чи специфічне для робочого простору. Дані пакета можна перевірити в
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Відмовитися** (будь-що одне з цього назавжди вимикає це):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # для окремого шелу
export DO_NOT_TRACK=1                          # міжінструментальний стандарт W3C
touch ~/.clawmetry/notelemetry                 # постійна файлова позначка
```

Мережевий збій тут ніколи не блокує роботу `clawmetry` — пінг
відправляється у фоновому потоці з тайм-аутом 3с за принципом "запустив і забув".

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
