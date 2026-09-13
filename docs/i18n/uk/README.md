<!-- i18n-src:a855a14295b0 -->
> Українська translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Агент може виконати сотню викликів інструментів, так і не просунувшись уперед.** ClawMetry
читає файли сесій, які ваші кодувальні агенти вже пишуть, і збирає хронологію,
виклики інструментів та будь-які дані про токени й вартість, які надає рантайм, в одному
вигляді — щоб ви могли відрізнити довгий прогін, який працює, від того, що застряг.

Працює з **32 рантаймами AI-агентів** — Claude Code, OpenAI Codex, Hermes, OpenClaw та ще 28. Одна панель для всього вашого флоту агентів. ([повний список](SUPPORTED_RUNTIMES.txt), згенерований із каталогу.)

> 🌐 **Читайте це мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ще →](docs/i18n/)

Одна команда. Нуль налаштувань. Автоматично виявляє все.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**. Нуль налаштувань: він знаходить рантайми
агентів, які у вас вже є, читає їх лише для читання і нічого не змінює в тому, як вони працюють.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Перш ніж встановлювати

| | |
|---|---|
| **Що він робить** | Читає файли сесій та логи, які ваші агенти вже пишуть. Жодного SDK, жодних змін коду, жодної інструментації у вашому застосунку. |
| **Що ви бачите** | Хронологію сесії, покроковий реплей інструментів, розбивку токенів і вартості, а також сигнали траєкторії (зациклення, повторювані збої) — для кожного рантайму. |
| **Що безкоштовно** | `pip install clawmetry` читає **OpenClaw, NVIDIA NemoClaw та Goose** без облікового запису, ключа чи мережевого виклику. Інші 27 — Claude Code, Codex, Cursor та решта — читаються закритим доповненням `clawmetry-pro`, яке з'являється з 7-денним пробним періодом або платним планом — точний поділ дивіться в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Як почати** | `pip install clawmetry && clawmetry`, потім відкрийте localhost:8900. Немає ще агентів на цій машині? `clawmetry --sample` відкриється з трьома позначеними синтетичними сесіями. |
| **Що залишає вашу машину** | Жодні дані сесій, якщо ви не запустите `clawmetry connect`. За замовчуванням виконуються дві речі, обидві можна вимкнути, і жодна не містить вмісту сесій: анонімний пінг встановлення та перевірка версії на PyPI. Кожен пункт призначення інвентаризовано в [docs/EGRESS.md](docs/EGRESS.md), відтворено за захопленим трафіком, а не за коментарями в коді. |

Варто знати два обмеження, перш ніж оцінювати результат: рантайми надають дуже
різні дані (деякі взагалі не публікують вартість — [матриця](docs/compatibility.md)
показує, які саме, для кожного рантайму), а спостереження за дією не те саме, що можливість
заблокувати її ([які засоби керування реальні, для кожного рантайму](docs/APPROVALS.md)).


## Працює з 32 рантаймами агентів

**Безкоштовно у застосунку з відкритим кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**У платному плані:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Кожен рантайм отримує однакову панель. Запустіть кілька одночасно, і перемикач
у заголовку переналаштує кожну вкладку на один із них.

Створили власного агента на базі SDK? Перехоплювач відстежує і його виклики LLM
також. Дивіться [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Що ви отримуєте

- **Сесії та транскрипти**: що робив кожен агент, крок за кроком, з реплеєм
- **Вартість і токени**: для кожного рантайму, моделі, сесії та дня, з позначками аномалій
- **Потік**: живу діаграму повідомлень, що рухаються через канали, моделі та інструменти
- **Мозок**: потік подій міркувань і викликів інструментів у режимі реального часу
- **Розрив контексту**: використання вікна, розраховане для кожного провайдера, компактизація проти вимушеного переповнення, а також мапа того, чого ми *не бачимо* для кожного рантайму ([як](docs/CONTEXT_BLOWOUT.md))
- **Пам'ять і навички**: файли та навички, які кожен рантайм фактично завантажив
- **Здоров'я і логи**: диск, пам'ять, частота помилок, ліміти швидкості, потік логів у реальному часі
- **Сповіщення**: бюджетні ліміти, сплески помилок, агент офлайн, з маршрутизацією до Slack, Discord, PagerDuty, Telegram, Email
- **Погодження**: призупиняйте ризиковані виклики інструментів *перед* їх виконанням і погоджуйте з телефону ([як](docs/APPROVALS.md))

## Розрив контексту та вартість спостереження

Два питання, на які варто відповісти, перш ніж довіряти будь-якому інструменту порівняння агентів.

**Як він обробляє розрив контекстного вікна для різних рантаймів?**

Відсоток використання чесний настільки, наскільки чесний дільник. ClawMetry
визначає розмір вікна для кожного провайдера з [таблиці, яку можна прочитати і
подати PR](clawmetry/context_windows.py), що охоплює Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama та GLM. Він не вимірює всі 32
рантайми однією лінійкою одного постачальника. Це важливо: хід на 300 тис. GPT-5,
оцінений за міркою Anthropic на 200 тис., читається як ">100%, зірвано", тоді як насправді
це 75% від 400 тис. GPT-5. Та сама лінійка приховує справді переповнений хід
DeepSeek на 130 тис. як комфортні 65%.

Кожне вікно постачається зі своїм походженням: `model_table`, `explicit_marker`,
`observed_floor` або чесний `default`, коли модель невідома. Індикатор, побудований
на здогадці, ніколи не відображається з тим самим авторитетом, що й побудований на
довіднику.

ClawMetry може бачити події компактизації лише для деяких рантаймів. Тому
`GET /api/context-coverage` повідомляє для кожного рантайму, чи означає **нуль
"пройшло чисто" чи "ми сліпі"**. `0`, який насправді означає сліпоту, так і зазначається.
[Детальніше](docs/CONTEXT_BLOWOUT.md)

**У що обходиться інструментація?**

| Шлях | Додано до вашого агента | За замовчуванням? |
|---|---|---|
| Відстеження файлів сесій (усі 32 рантайми) | **0**. Окремий процес, жодного коду ClawMetry у вашому агенті | увімкнено |
| HTTP-перехоплювач (`CLAWMETRY_INTERCEPT=1`) | **+0,44 мс** на виклик LLM, або 0,009% від 5-секундного виклику | вимкнено |
| Ворота попереднього хука інструменту (тепла кеш-пам'ять) | **+44 мс** на кожен ворітний виклик інструменту, поверх базових 36 мс інтерпретатора | вимкнено |
| Проксі примусового застосування | **+9,7 мс** на виклик LLM | вимкнено |

Вартість хосту демона: **2762 події/сек** на прийом, **710 байт/подію** на диску
(67,7 МБ на 100 тис. подій), і **~12% одного ядра** сталого навантаження на завантаженій
інсталяції. Це останнє число перевищує наш власний заявлений бюджет у 5-10%, тому
опубліковано як баг, який потрібно виправити, а не приховано зі сторінки.

Виміряно на Apple M2 Pro за допомогою `benchmarks/overhead.py`. Тестовий стенд запускає
кожну умову в окремому процесі, чергує їхній порядок і **відмовляється друкувати
число, коли раунди розходяться щодо його знаку**. Запустіть його на власній
машині за хвилину:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Виміряно кожен шлях, включно з воротами хуків і проксі примусового застосування,
а тестовий стенд запускається на Linux, macOS і Windows у CI. Два результати, які
варто знати: проксі коштує приблизно у сім разів більше на Windows, ніж на Linux,
а демон наразі стабільно споживає близько 12% одного ядра, що перевищує наш власний
бюджет у 5-10%. Необроблений JSON, метод і те, що досі не виміряно, знаходяться в
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Ціни

| План | Що охоплює | Ціна |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, повна панель, лише локально | $0 |
| **Starter** | Усі інші рантайми вище, вигляд флоту, хмарна синхронізація | $9 за вузол/місяць |
| **Pro** | Starter + керування й оцінювання: погодження, політики ризику інструментів, оцінки, виявлення аномалій, оптимізатор вартості, експорт OTel, захищений від підробки журнал аудиту | $19 за вузол/місяць |

Річні плани, Enterprise та актуальні ціни знаходяться на сторінці
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключі ліцензії для самостійного
хостингу працюють без хмари (`clawmetry license`). Точний поділ безкоштовно/платно
знаходиться в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваші дані залишаються на вашій машині

ClawMetry читає локальні файли сесій та логи. **Жодні дані сесій не залишають ваш пристрій,
якщо ви не запустите `clawmetry connect`** — жодних запитів, відповідей, аргументів
інструментів, вмісту файлів чи рядків логів. Коли ви таки підключаєтеся, знімок стану
шифрується наскрізним шифруванням із ключем, який ніколи не залишає вашу машину, і
розшифровується у вашому браузері. Якщо у вузла немає ключа, завантаження пропускається,
а не надсилається у відкритому вигляді, і жодна відповідь сервера не може це вимкнути.

Дві речі виконуються за замовчуванням до підключення, обидві можна вимкнути, і жодна
не містить даних сесії: анонімний пінг встановлення та перевірка версії відносно PyPI.
Стандартна інсталяція також один раз перевіряє вашу публічну IP-адресу для рядка
банера при запуску. Кожне призначення, що воно містить і як його вимкнути, перелічено
в [docs/EGRESS.md](docs/EGRESS.md); інсталяції із самостійним хостингом, перенаправленням
та ізольовані від мережі не роблять жодних довільних вихідних викликів взагалі.

Розшифрування відбувається у вашому браузері, у коді, який ми вам надсилаємо. Раніше
це було обіцянкою; тепер це можна перевірити. Кожен рядок, що торкається вашого ключа,
живе в одному файлі, який можна прочитати, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
який постачається всередині wheel-пакета і подається дослівно, закріплений хешем
Subresource Integrity. Щоб підтвердити, що браузер виконує саме те, що ми опублікували:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чого це не доводить: ми подаємо сторінку, яка завантажує цей файл, тож ми могли б
подати іншу сторінку. Хеші цілісності захищають вас від скомпрометованого CDN,
а не від постачальника. Ви отримуєте те, що будь-яка підміна має бути навмисною,
видимою у вихідному коді сторінки і відрізнятися від артефакту на PyPI, який будь-хто
може завантажити. Самостійний хостинг або робота лише локально повністю усуває цю
залежність.

## Встановлення

```bash
pip install clawmetry     # then: clawmetry
```

Або однорядкова команда: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Потрібен Python 3.8+ на macOS, Linux або Windows, і принаймні один рантайм агента
на тій самій машині. Інструкції для Docker: [docs/DOCKER.md](docs/DOCKER.md).

Або нехай агент налаштує це за вас. Навичка [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
навчає Claude Code, Codex, Cursor, Gemini CLI, Copilot або OpenCode встановлювати
ClawMetry, повідомляти, що роблять і на що витрачають агенти на цій машині,
зупиняти одну сесію на запит і затримувати ризиковані виклики інструментів для погодження:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Документація

| | |
|---|---|
| [Сумісність рантаймів](docs/compatibility.md) | Що читає кожен адаптер і як додати рантайм |
| [Розрив контексту](docs/CONTEXT_BLOWOUT.md) | Вікна для кожного провайдера, компактизація проти переповнення, покриття для кожного рантайму |
| [Накладні витрати](docs/OVERHEAD.md) | Скільки коштує інструментація, виміряно, зі стендом для відтворення |
| [Права доступу](docs/ENTITLEMENTS.md) | Безкоштовно проти платно, матриця рівнів, CLI ліцензій |
| [Погодження та політики](docs/APPROVALS.md) | Контроль перед виконанням, оцінка ризиків, погодження з телефону |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Експортуйте трейси куди завгодно, приймайте OTLP звідки завгодно |
| [Принесіть власного агента](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain від початку до кінця, з робочими прикладами |
| [Відстеження SDK](docs/SDK_TRACKING.md) | Розподіл вартості для агентів, яких ви створили самостійно |
| [Чат-канали](docs/CHANNELS.md) | Адаптери чатів, показані у Потоці |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Ізольовані налаштування NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтування томів |
| [Архітектура](ARCHITECTURE.md) · [Розробка](docs/DEVELOPMENT.md) | Як це працює всередині; запуск із вихідного коду |
| [Телеметрія](docs/TELEMETRY.md) | Анонімні пінги встановлення та відкриття десктопного застосунку, і як їх вимкнути |

## Скріншоти

Кожне число нижче взято з однієї реальної машини, лише для читання, без жодних штучних даних.

**Він повідомляє, коли щось не так, а не лише що сталося.**
Два банери аномалій зверху: витрати, що йдуть у 7 разів вище середньодобового рівня,
і сплеск вартості у 4,2 рази. Нижче — 324 з 667 останніх сесій із сигналом марнотратства,
розкладеним за причинами.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Він показує, куди пішли гроші, у кожному вікні часу.**
$252,47 сьогодні, $513,15 цього тижня, $1312,92 цього місяця, кожне з відповідними
токенами і тим, скільки з цього вже покриває ваша підписка. Нижче — близько
$1128/міс, позначені як такі, що можна повернути, і вже $17 256/міс заощаджено
завдяки повторному використанню кешу.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Він малює, як повідомлення перетворюється на відповідь.**
Жива діаграма потоку: ви, канал, яким воно надійшло, шлюз, модель,
яка відповідає прямо зараз, і кожен інструмент, до якого вона зверталася. Вузли
підсвічуються, коли робота проходить через них.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Кожен агент на машині, в одній таблиці.**
Що він виконує, скільки коштує за останні 24 години і за весь час, коли його
востаннє бачили, хто його власник, і чи покриває рахунок підписка. Тут 14 агентів,
3 сесії працюють, 13 тихі.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Він показує, куди пішов час і гроші кроку, інструмент за інструментом.**
Один хід реальної сесії: 11 інструментів за 11,2 хвилини за $1,16. Кожен виклик
Bash і виклик моделі отримує власну смугу на хронологічній шкалі, тож команду,
яка виконувалась 4,1 хвилини, і ту, що виконувалась 226 мс, легко відрізнити на
перший погляд.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Він оцінює саму роботу, а не лише витрати.**
Оцінка A цього тижня: 54 завдання виконано чисто, 2 складні коштували $48,57, а
прогони з надто малою активністю, щоб їх оцінити, виключені з оцінки, а не
зараховані як успіх. Кожен складний прогін веде до свого трейсу.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Він показує, чому контекстне вікно постійно заповнюється.**
715 тис. з вікна на 1 млн токенів на останньому ході, пік 83,3%, 4 компактизації,
всі спрацювали проактивно, а не через переповнення, і використання кожного ходу
за ними.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Виявлення працює без будь-якого налаштування з вашого боку.**
Вбудовані детектори увімкнені з моменту встановлення: агент затих, потік
телеметрії зупинився, сплеск вартості, сплеск токенів, зростання кількості помилок,
сплеск помилок, поріг бюджету, збіг сигнатури загрози, знахідка інструменту безпеки,
зміна стану безпеки. Власні правила є опційним доповненням.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Затримка ризикованого виклику — опційна і йде вимкненою.**
Рекурсивне видалення, примусовий пуш, sudo, секрети, встановлення пакетів і вихідні
виклики — кожен отримує правило, яке можна увімкнути. Поки ви цього не зробите,
ClawMetry лише спостерігає і нічого не змінює. Щойно одне увімкнено, відповідні
виклики чекають тут (або на вашому телефоні) на погодження чи відмову.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Більше, для кожного рантайму: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Визнання

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Історія зірок

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Ліцензія

MIT · Створено [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
