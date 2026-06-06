<!-- i18n-src:48548997be76 -->
> Українська translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Спостерігайте, як ваш агент думає.** Моніторинг у реальному часі для **12 середовищ виконання ШІ-агентів**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex та ще 8. Один дашборд для всього вашого флоту агентів.

> 🌐 **Читати іншими мовами:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [більше →](docs/i18n/)

Одна команда. Нуль налаштувань. Автоматичне визначення всього.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900** — і готово.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Сумісність із 12 середовищами виконання агентів

ClawMetry починався як інструмент спостереження для OpenClaw, а тепер вимірює **весь ваш флот агентів** в одному дашборді, автоматично визначаючи кожне середовище виконання на вашій машині:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw та NemoClaw доступні безкоштовно у версії з відкритим вихідним кодом; решта середовищ виконання активуються з ClawMetry Cloud або за самостійно розгорнутою Pro ліцензією. Перемикайте середовище виконання у заголовку, і кожна вкладка — вартість, токени, інструменти, трасування — перемикається до обраного середовища.

## Що ви отримуєте

- **Flow** — Жива анімована діаграма, що показує потік повідомлень через канали, мозок, інструменти та назад
- **Overview** — Перевірки справності, теплова карта активності, кількість сесій, інформація про модель
- **Usage** — Відстеження токенів і витрат із добовою/тижневою/місячною деталізацією
- **Sessions** — Активні сесії агентів із моделлю, токенами, часом останньої активності
- **Crons** — Заплановані завдання зі статусом, часом наступного запуску, тривалістю
- **Logs** — Кольорове потокове передавання журналів у реальному часі
- **Memory** — Перегляд файлів SOUL.md, MEMORY.md, AGENTS.md, щоденних нотаток
- **Transcripts** — Інтерфейс у вигляді бульбашок чату для читання історії сесій
- **Alerts** — Ліміти бюджету, тригери частоти помилок, виявлення офлайн-агентів; маршрутизація до Slack, Discord, PagerDuty, Telegram, Email
- **Approvals** — Блокування небезпечних видалень, примусових push-операцій, мутацій БД, sudo, встановлення пакунків, мережевих викликів за одним підтвердженням кліком

## Скріншоти

### 🧠 Brain — Живий потік подій агента
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — Використання токенів і зведення сесій
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — Стрічка викликів інструментів у реальному часі
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — Розбивка витрат за моделлю та сесією
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — Файловий браузер робочого простору
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — Стан безпеки та журнал аудиту
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — Ліміти бюджету, тригери частоти помилок, вебхуки до Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — Блокування ризикованих викликів інструментів за ручним підтвердженням; правила захисту на основі політик
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## Встановлення

**Одна команда (рекомендовано):**
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

Застосунок React v2 знаходиться у `frontend/` і доступний за адресою `/v2` під час запуску сервера Flask із увімкненим v2.

Використовуйте два термінали під час розробки:

```bash
# Термінал 1: Flask API/сервер на :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Термінал 2: dev-сервер Vite на :5173
cd frontend
nvm use
npm ci
npm run dev
```

Відкрийте `http://localhost:5173/v2/`. Vite проксіює запити `/api` до `http://localhost:8900`, тож React-застосунок може взаємодіяти з локальним сервером Flask без додаткового налаштування CORS.

Щоб зібрати пакунок, який постачається разом із Python-пакетом:

```bash
cd frontend
npm run build
```

Виробничий пакунок записується до `clawmetry/static/v2/dist/`.

## Сумісність із середовищами виконання / агентами

ClawMetry спостерігає за багатьма середовищами виконання ШІ-агентів, а не лише за OpenClaw. Кожне середовище, відмінне від OpenClaw, постачається зі спеціальним адаптером-читачем, що перекладає його рідний формат сесій у уніфіковані структури ClawMetry; демон завантажує їх у той самий DuckDB-сховище та хмарний знімок, позначаючи середовищем виконання, а вкладка відтворення сесій показує **перемикач середовища виконання**, коли присутнє більше одного. Дивіться [`docs/compatibility.md`](docs/compatibility.md) для повної матриці та інструкції з додавання середовищ виконання, а також [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) для ознайомлення з сімейством OpenClaw.

| Середовище виконання / Агент | Статус | Примітки |
|---|---|---|
| **OpenClaw** | Рідне | Еталонне середовище виконання, автоматичне визначення |
| **PicoClaw** | Бета-адаптер | Плоский JSONL `providers.Message` (`~/.picoclaw/workspace/sessions`). Транскрипти, модель, виклики інструментів. |
| **NanoClaw** | Бета-адаптер | SQLite для кожної сесії (`data/v2-sessions`). Транскрипти + кількість повідомлень. |
| **Hermes** | Бета-адаптер | SQLite `~/.hermes/state.db`. Транскрипти, модель, токени/вартість. |
| **Claude Code** | Бета-адаптер | JSONL `~/.claude/projects/.../<id>.jsonl`. Транскрипти, модель, виклики інструментів + думки, використання токенів. |
| **Codex** | Бета-адаптер | Rollout JSONL `~/.codex/sessions/...`. Транскрипти, модель, виклики інструментів, використання токенів. |
| **Cursor** | Бета-адаптер | SQLite `state.vscdb`. Транскрипти чату/композитора, модель. |
| **Aider** | Бета-адаптер | `.aider.chat.history.md` для кожного проекту. Транскрипти, модель, кількість токенів. |
| **Goose** | Бета-адаптер | SQLite `~/.local/share/goose`. Транскрипти, модель, виклики інструментів, загальна кількість токенів. |
| **opencode** | Бета-адаптер | SQLite `~/.local/share/opencode`. Транскрипти, модель, виклики інструментів, токени + вартість. |
| **Qwen Code** | Бета-адаптер | JSONL `~/.qwen/projects/.../chats`. Транскрипти, модель, виклики інструментів, використання токенів. |

«Бета-адаптер» означає, що ClawMetry постачає читач для реального формату даних на диску цього середовища, кожен з яких побудований та перевірений на реальному встановленні на реальній машині (див. `tests/fixtures/runtimes/<rt>/`). Адаптери доступні лише для читання; кожен чесно відображає, що насправді зберігає його середовище виконання (наприклад, PicoClaw/NanoClaw/Cursor не записують вартість токенів на диск). Коли кілька середовищ виконання працюють на одному вузлі, перемикач середовища виконання обмежує перегляд сесій одним для зручного заглиблення.

## Відстеження будь-якого SDK-агента — атрибуція витрат поза циклом

Перелічені вище середовища виконання записують сесії на диск. Ваш власний **виробничий агент** — той, що ви побудували на OpenAI Agents SDK, LangChain, Vercel AI SDK, LlamaIndex, E2B або простому циклі `httpx` — цього не робить. Перехоплювач ClawMetry з нульовим налаштуванням все одно фіксує його виклики LLM (вартість, токени, затримку, помилки) шляхом підміни `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (або змінна середовища `CLAWMETRY_SOURCE=support-agent`) позначає кожен виклик **іменованим джерелом**, тому кожен запущений вами продукт відображається як окремий рядок із атрибуцією витрат у картці **🔌 Out-loop sources** на Overview — виклики, постачальники, затримка, частота помилок на агента. Немає встановленого джерела? Виклики все одно відстежуються; картка просто залишається прихованою.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

Це той самий рівень даних, що живлять адаптери середовищ виконання (DuckDB → хмарний знімок), тому джерела поза циклом синхронізуються з хмарним дашбордом так само, як і все інше, із наскрізним шифруванням.

## OpenTelemetry — нейтральний до постачальника, надсилайте трасування куди завгодно

ClawMetry підтримує **OpenTelemetry** в обох напрямках, використовуючи **семантичні конвенції GenAI**, тому трасування вашого агента ніколи не прив'язані до одного інструменту.

**Експортуйте** кожну сесію — виклики LLM, інструменти, суб-агенти, токени, вартість — як OTLP/HTTP GenAI-відрізки до будь-якого колектора (Datadog, Grafana, Honeycomb або ваш власний OTel Collector):

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

**Прийом** — вбудований OTLP-приймач приймає трасування та метрики від будь-чого іншого за адресами `/v1/traces` та `/v1/metrics` (`pip install clawmetry[otel]` для прийому protobuf).

Ви отримуєте дашборд ClawMetry з нульовим налаштуванням і локальним пріоритетом **та** ваші дані у будь-якому бекенді, який вже використовує ваша команда — без прив'язки до постачальника, без встановлення другого агента.

## Налаштування

Більшості людей ніякого налаштування не потрібно. ClawMetry автоматично визначає ваш робочий простір, журнали, сесії та cron-завдання.

Якщо вам все ж потрібно налаштувати:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

Усі параметри: `clawmetry --help`

## Підтримувані канали

ClawMetry показує живу активність для кожного налаштованого вами каналу OpenClaw. У діаграмі Flow відображаються лише ті канали, що насправді налаштовані у вашому `openclaw.json` — ненастроєні автоматично приховуються.

Натисніть будь-який вузол каналу у Flow, щоб побачити живий перегляд у вигляді бульбашок чату з кількістю вхідних/вихідних повідомлень.

| Канал | Статус | Живий попап | Примітки |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ Повний | ✅ | Повідомлення, статистика, оновлення кожні 10 с |
| 💬 **iMessage** | ✅ Повний | ✅ | Читає `~/Library/Messages/chat.db` напряму |
| 💚 **WhatsApp** | ✅ Повний | ✅ | Через WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ Повний | ✅ | Через signal-cli |
| 🟣 **Discord** | ✅ Повний | ✅ | Визначення гільдії та каналу |
| 🟪 **Slack** | ✅ Повний | ✅ | Визначення робочого простору та каналу |
| 🌐 **Webchat** | ✅ Повний | ✅ | Вбудовані сесії веб-інтерфейсу |
| 📡 **IRC** | ✅ Повний | ✅ | Інтерфейс бульбашок у стилі терміналу |
| 🍏 **BlueBubbles** | ✅ Повний | ✅ | iMessage через BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ Повний | ✅ | Через вебхуки Chat API |
| 🟣 **MS Teams** | ✅ Повний | ✅ | Через плагін бота Teams |
| 🔷 **Mattermost** | ✅ Повний | ✅ | Самостійно розгорнутий командний чат |
| 🟩 **Matrix** | ✅ Повний | ✅ | Децентралізований, підтримка E2EE |
| 🟢 **LINE** | ✅ Повний | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ Повний | ✅ | Децентралізовані NIP-04 DM |
| 🟣 **Twitch** | ✅ Повний | ✅ | Чат через IRC-з'єднання |
| 🔷 **Feishu/Lark** | ✅ Повний | ✅ | Підписка на події через WebSocket |
| 🔵 **Zalo** | ✅ Повний | ✅ | Zalo Bot API |

> **Автоматичне визначення:** ClawMetry читає ваш `~/.openclaw/openclaw.json` і відображає лише ті канали, що ви справді налаштували. Ручне налаштування не потрібне.

## Розгортання у Docker

Хочете запустити ClawMetry у контейнері? Немає проблем! 🐳

**Швидкий старт із Docker:**

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

> **Примітка:** При запуску у Docker підключайте каталоги з даними та журналами вашого агента (наприклад, `~/.openclaw`, `~/.claude`, `~/.codex`), щоб ClawMetry міг автоматично визначити ваше налаштування.

## Вимоги

- Python 3.8+
- Flask (встановлюється автоматично через pip)
- Середовище виконання ШІ-агента на тій самій машині: OpenClaw, NVIDIA NemoClaw, Claude Code, Codex, Cursor, Goose, Hermes, opencode, Qwen Code, Aider, NanoClaw або PicoClaw (або підключені томи для Docker)
- Linux або macOS

## Підтримка NemoClaw / OpenShell

ClawMetry автоматично визначає [NemoClaw](https://github.com/NVIDIA/NemoClaw) — корпоративну обгортку безпеки NVIDIA для OpenClaw, що запускає агентів усередині ізольованих контейнерів OpenShell.

У більшості випадків додаткового налаштування не потрібно. Демон синхронізації автоматично знаходить файли сесій незалежно від того, чи знаходяться вони у `~/.openclaw/` на хості або всередині контейнера OpenShell.

### Як це працює

ClawMetry визначає NemoClaw двома способами:

1. **Визначення бінарного файлу** — перевіряє наявність CLI `nemoclaw` і запускає `nemoclaw status` для отримання інформації про пісочницю
2. **Визначення контейнера** — сканує запущені контейнери Docker на наявність образів `openshell`, `nemoclaw` або `ghcr.io/nvidia/`, а потім читає сесії через підключені томи або `docker cp`

Файли сесій, синхронізовані з контейнерів NemoClaw, позначаються метаданими `runtime=nemoclaw` та `container_id` у хмарному дашборді, тому ви можете з першого погляду відрізнити їх від стандартних сесій OpenClaw.

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

Якщо автоматичне визначення не спрацьовує, вкажіть ClawMetry правильну пісочницю:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### Запуск усередині пісочниці (розширений варіант)

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

### Порти та точки входу

| Точка входу | Порт | Протокол | Обов'язково |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | Так (демон синхронізації → хмара) |
| `localhost:8900` | 8900 | HTTP | Так (локальний UI дашборду) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | Для виявлення сесій у контейнерах |

Демон синхронізації здійснює лише вихідні HTTPS-виклики до `ingest.clawmetry.com`. Вхідні порти не потрібні.

---

## Хмарне розгортання

Дивіться **[Посібник із хмарного тестування](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** для SSH-тунелів, зворотного проксі та Docker.

## Тестування

Цей проект тестується за допомогою BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## Телеметрія

ClawMetry надсилає один анонімний ping «перший запуск» на адресу
`https://app.clawmetry.com/api/install` під час першого запуску CLI
`clawmetry` на новій машині. Ми використовуємо це для підрахунку встановлень (єдина маркетингова метрика, доступна для OSS-проекту) та щоб дізнатися, які фреймворки агентів встановлені у наших користувачів.

**Рівно один POST на встановлення**, що містить:

| Поле | Приклад | Навіщо |
|---|---|---|
| `install_id` | випадковий UUID, збережений у `~/.clawmetry/install_id` | дедублікація; не пов'язаний з вашою поштою або api_key |
| `version` | `0.12.167` | які версії використовуються |
| `os` / `os_version` | `Darwin` / `25.3.0` | пріоритети підтримки платформ |
| `python` | `3.11.15` | матриця підтримки версій Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | з якими агентами нам варто інтегруватись далі |
| `is_ci` / `ci_provider` | `true` / `github_actions` | відокремлення реальних встановлень від CI |

**Що ми НЕ надсилаємо**: IP (хмара визначає код країни на стороні сервера із запиту, а потім відкидає IP), ім'я хоста, ім'я користувача, шлях до робочого простору, вміст файлів, ваш api_key, вашу пошту, будь-які персональні дані або дані, специфічні для робочого простору. Вміст, що передається по мережі, можна перевірити у
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**Відмова** (будь-який із варіантів вимикає її назавжди):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

Збій мережі тут ніколи не блокує запуск `clawmetry` — ping надсилається без очікування відповіді у фоновому потоці з таймаутом 3 с.

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
  <strong>🦞 Спостерігайте, як ваш агент думає</strong><br>
  <sub>Створено <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · Частина екосистеми <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
