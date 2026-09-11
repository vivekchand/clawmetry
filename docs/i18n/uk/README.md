<!-- i18n-src:12b97259721e -->
> Українська translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Агент може виконати сотню викликів інструментів, так і не досягнувши прогресу.** ClawMetry
читає файли сесій, які ваші кодові агенти вже пишуть, і об'єднує таймлайн,
виклики інструментів і будь-які дані про токени й вартість, які надає рантайм, в одному
вигляді — щоб ви могли відрізнити довгий запуск, що працює, від того, що застряг.

Працює з **31 рантаймом AI-агентів** — Claude Code, OpenAI Codex, Hermes, OpenClaw та ще 27. Одна панель для всього вашого флоту агентів. ([повний список](SUPPORTED_RUNTIMES.txt), згенерований з каталогу.)

> 🌐 **Читати цією мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ще →](docs/i18n/)

Одна команда. Нуль налаштувань. Все визначається автоматично.

```bash
pip install clawmetry && clawmetry
```

Відкривається на **http://localhost:8900**. Нуль налаштувань: він знаходить рантайми агентів,
які у вас вже є, читає їх у режимі лише читання і нічого не змінює в тому, як вони працюють.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Перед встановленням

| | |
|---|---|
| **Що він робить** | Читає файли сесій і логи, які ваші агенти вже пишуть. Жодного SDK, жодних змін коду, жодної інструментації у вашому застосунку. |
| **Що ви побачите** | Таймлайн сесії, покроковий реплей інструментів, розбивку токенів і вартості, а також сигнали траєкторії (зациклення, повторювані збої) — для кожного рантайму. |
| **Що безкоштовно** | `pip install clawmetry` читає **OpenClaw, NVIDIA NemoClaw та Goose** без облікового запису, ключа чи мережевого виклику. Решту 27 — Claude Code, Codex, Cursor та інші — читає компаньйон із закритим кодом `clawmetry-pro`, який доступний з 7-денним пробним періодом або платним планом — точний розподіл дивіться в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Як почати** | `pip install clawmetry && clawmetry`, потім відкрийте localhost:8900. Ще немає агентів на цій машині? `clawmetry --sample` відкриється з трьома позначеними синтетичними сесіями. |
| **Що залишає вашу машину** | Жодні дані сесій, якщо ви не запустите `clawmetry connect`. За замовчуванням виконуються дві речі, обидві можна вимкнути, і жодна не несе вміст сесій: анонімний пінг встановлення та перевірка версії PyPI. Кожен пункт призначення інвентаризовано в [docs/EGRESS.md](docs/EGRESS.md), відновлено з перехоплення трафіку, а не з читання коментарів. |

Два обмеження, які варто знати перед оцінкою результату: рантайми надають дуже
різні дані (деякі взагалі не публікують вартість — [таблиця сумісності](docs/compatibility.md)
показує, які саме, для кожного рантайму), а спостереження за дією не те саме, що можливість
її заблокувати ([які контролі реальні, для кожного рантайму](docs/APPROVALS.md)).


## Працює з 31 рантаймом агентів

**Безкоштовно у застосунку з відкритим кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**На платному плані:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Кожен рантайм отримує однакову панель. Запустіть кілька одночасно, і перемикач у
шапці переналаштує кожну вкладку на один з них.

Створили власного агента на базі SDK замість цього? Перехоплювач також відстежує його виклики LLM.
Дивіться [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Що ви отримуєте

- **Сесії й транскрипти**: що робив кожен агент, хід за ходом, з реплеєм
- **Вартість і токени**: за рантаймом, моделлю, сесією та днем, з позначками аномалій
- **Потік (Flow)**: діаграма руху повідомлень через канали, моделі та інструменти в реальному часі
- **Мозок (Brain)**: потік подій міркувань і викликів інструментів у реальному часі
- **Перевантаження контексту**: використання вікна, розраховане для кожного провайдера, компактизація проти вимушеного переповнення, а також карта того, чого ми *не бачимо* для кожного рантайму ([як](docs/CONTEXT_BLOWOUT.md))
- **Пам'ять і навички**: файли й навички, які реально завантажив кожен рантайм
- **Стан і логи**: диск, пам'ять, частота помилок, ліміти швидкості, потік логів у реальному часі
- **Сповіщення**: ліміти бюджету, сплески помилок, агент офлайн, з маршрутизацією в Slack, Discord, PagerDuty, Telegram, Email
- **Затвердження**: призупиняйте ризиковані виклики інструментів *до* їх виконання і затверджуйте з телефону ([як](docs/APPROVALS.md))

## Перевантаження контексту та вартість спостереження

Два питання, на які варто відповісти, перш ніж довіряти будь-якому інструменту порівняння агентів.

**Як він обробляє перевантаження контекстного вікна між рантаймами?**

Відсоток використання чесний лише настільки, наскільки чесним є те, на що його ділять. ClawMetry
розраховує розмір вікна для кожного провайдера з [таблиці, яку можна прочитати і
надіслати PR](clawmetry/context_windows.py), що охоплює Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama та GLM. Він не вимірює всі 31 рантайм
однією лінійкою одного постачальника. Це важливо: хід на 300K токенів GPT-5, оцінений
за лінійкою Anthropic на 200K, читається як ">100%, перевантажено", хоча насправді це 75% від
400K вікна GPT-5. Та сама лінійка приховує справді перевантажений хід DeepSeek на 130K
як комфортні 65%.

Кожне вікно постачається з інформацією про походження: `model_table`, `explicit_marker`,
`observed_floor` або чесний `default`, коли модель невідома. Індикатор, побудований на
здогадці, ніколи не відображається з такою ж авторитетністю, як побудований на
пошуку в таблиці.

ClawMetry може бачити події компактизації лише для деяких рантаймів. Тому
`GET /api/context-coverage` повідомляє для кожного рантайму, чи означає **нуль
"пройшло чисто" чи "ми сліпі"**. `0`, який насправді означає сліпоту, так і зазначається.
[Детальніше](docs/CONTEXT_BLOWOUT.md)

**Скільки коштує інструментація?**

| Шлях | Додано до вашого агента | За замовчуванням? |
|---|---|---|
| Читання файлів сесій (усі 31 рантайми) | **0**. Окремий процес, жодного коду ClawMetry у вашому агенті | увімкнено |
| HTTP-перехоплювач (`CLAWMETRY_INTERCEPT=1`) | **+0.44 мс** на виклик LLM, або 0.009% від 5-секундного виклику | вимкнено |
| Ворота попереднього хука (теплий кеш) | **+44 мс** на контрольований виклик інструменту, понад базові 36 мс інтерпретатора | вимкнено |
| Проксі примусового виконання | **+9.7 мс** на виклик LLM | вимкнено |

Вартість для хоста демона: **2762 події/сек** прийому, **710 байт/подію** на диску
(67.7 МБ на 100 тис. подій) і **~12% одного ядра** стабільно на завантаженому
встановленні. Це останнє число перевищує наш власний заявлений бюджет 5-10%, тому
воно опубліковане як баг, який ще треба виправити, а не приховане зі сторінки.

Виміряно на Apple M2 Pro за допомогою `benchmarks/overhead.py`. Тестовий набір запускає
кожну умову в окремому процесі, чергує їхній порядок і **відмовляється друкувати
число, якщо раунди розходяться щодо його знака**. Запустіть його на своїй власній
машині за хвилину:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Виміряно кожен шлях, включно з воротами хуків і проксі примусового виконання,
і тестовий набір запускається на Linux, macOS та Windows у CI. Два результати варто
знати: проксі коштує приблизно в сім разів дорожче на Windows, ніж на Linux, а
демон наразі стабільно споживає близько 12% одного ядра, що перевищує наш власний бюджет
5-10%. Необроблений JSON, метод і те, що ще не виміряно, знаходяться в
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Ціни

| План | Що охоплює | Ціна |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, повна панель, лише локально | $0 |
| **Starter** | Усі інші рантайми вище, огляд флоту, синхронізація з хмарою | $9 за вузол / місяць |
| **Pro** | Starter + контроль і оцінка: затвердження, політики ризику інструментів, оцінки, виявлення аномалій, оптимізатор витрат, експорт OTel, журнал аудиту, стійкий до підробок | $19 за вузол / місяць |

Річні плани, Enterprise і актуальні числа знаходяться на
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключі ліцензій для
самостійного хостингу працюють без хмари (`clawmetry license`). Точний розподіл
безкоштовного/платного описано в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваші дані залишаються на вашій машині

ClawMetry читає локальні файли сесій і логи. **Жодні дані сесій не залишають ваш пристрій,
якщо ви не запустите `clawmetry connect`** — жодних запитів, відповідей, аргументів
інструментів, вмісту файлів чи рядків логів. Коли ви все ж підключаєтеся, знімок
шифрується наскрізно (end-to-end) ключем, який ніколи не залишає вашу машину, і
розшифровується у вашому браузері. Якщо вузол не має ключа, завантаження
пропускається, а не надсилається у відкритому вигляді, і жодна відповідь сервера
не може це змінити.

За замовчуванням до підключення виконуються дві речі, обидві можна вимкнути, і жодна
не несе дані сесій: анонімний пінг встановлення і перевірка версії відносно
PyPI. Стандартне встановлення також один раз шукає вашу публічну IP-адресу для
рядка банера при запуску. Кожне призначення, що воно несе і як його вимкнути, перераховано в
[docs/EGRESS.md](docs/EGRESS.md); встановлення для самостійного хостингу, з перенаправленням і
ізольовані від мережі не роблять жодних додаткових вихідних викликів.

Розшифрування відбувається у вашому браузері, у коді, який ми вам надаємо. Раніше це
було обіцянкою; тепер це те, що можна перевірити. Кожен рядок, що торкається вашого ключа,
знаходиться в одному файлі, який можна прочитати, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
який постачається всередині wheel-пакета і подається дослівно, закріплений хешем Subresource
Integrity. Щоб підтвердити, що браузер виконує те, що ми опублікували:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чого це не доводить: ми подаємо сторінку, яка завантажує файл, тож ми могли б
подати іншу сторінку. Хеші цілісності захищають вас від скомпрометованого CDN,
а не від постачальника. Ви отримуєте те, що будь-яка підміна має бути
навмисною, видимою в коді сторінки і відрізнятися від артефакту на PyPI,
який будь-хто може завантажити. Самостійний хостинг або робота лише локально
повністю усуває цю залежність.

## Встановлення

```bash
pip install clawmetry     # потім: clawmetry
```

Або одним рядком: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Потрібен Python 3.8+ на macOS, Linux або Windows, і хоча б один рантайм агента на
тій самій машині. Інструкції для Docker: [docs/DOCKER.md](docs/DOCKER.md).

Або нехай агент налаштує все за вас. Навичка [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
навчає Claude Code, Codex, Cursor, Gemini CLI, Copilot або OpenCode
встановлювати ClawMetry, звітувати про те, що роблять і скільки витрачають агенти на машині,
зупиняти сесію на запит і затримувати ризиковані виклики інструментів для затвердження:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Документація

| | |
|---|---|
| [Сумісність рантаймів](docs/compatibility.md) | Що читає кожен адаптер і як додати рантайм |
| [Перевантаження контексту](docs/CONTEXT_BLOWOUT.md) | Вікна для кожного провайдера, компактизація проти переповнення, покриття для кожного рантайму |
| [Накладні витрати](docs/OVERHEAD.md) | Скільки коштує інструментація, виміряно, з тестовим набором для відтворення |
| [Права доступу](docs/ENTITLEMENTS.md) | Безкоштовне проти платного, матриця рівнів, CLI ліцензій |
| [Затвердження і політики](docs/APPROVALS.md) | Контроль перед виконанням, оцінка ризику, затвердження з телефону |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Експортуйте трейси куди завгодно, приймайте OTLP звідки завгодно |
| [Приведіть власного агента](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain від початку до кінця, з робочими прикладами |
| [Відстеження SDK](docs/SDK_TRACKING.md) | Атрибуція вартості для агентів, які ви створили самостійно |
| [Чат-канали](docs/CHANNELS.md) | Адаптери чату, показані у Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Ізольовані (sandboxed) налаштування NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтування томів |
| [Архітектура](ARCHITECTURE.md) · [Розробка](docs/DEVELOPMENT.md) | Як це працює всередині; запуск з вихідного коду |
| [Телеметрія](docs/TELEMETRY.md) | Анонімні пінги встановлення й відкриття десктоп-застосунку, і як їх вимкнути |

## Скріншоти

Кожне число нижче взято з однієї реальної машини, у режимі лише читання, без жодних штучних даних.

**Він повідомляє вам, коли щось не так, а не просто що сталося.**
Два банери аномалій зверху: витрати вдвічі (7x) вищі за середньодобові та
сплеск вартості в 4.2 рази. Нижче — 324 з 667 останніх сесій, що несуть
сигнал марнотратства, з розбивкою за причинами.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Він показує, куди пішли гроші, у будь-якому вікні.**
$252.47 сьогодні, $513.15 цього тижня, $1312.92 цього місяця, кожне з токенами
за цим і тим, скільки з цього вже покриває ваша підписка. Нижче — приблизно
$1128/міс, зазначені як такі, що можна повернути, і $17256/міс, вже заощаджені
завдяки повторному використанню кешу.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Він показує, як повідомлення стає відповіддю.**
Діаграма потоку в реальному часі: ви, канал, яким воно надійшло, шлюз, модель,
що відповідає прямо зараз, і кожен інструмент, до якого вона зверталася. Вузли
підсвічуються по мірі проходження роботи через них.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Кожен агент на машині, в одній таблиці.**
Що він запускає, скільки коштує за останні 24 години і за весь час, коли
його востаннє бачили, хто ним володіє, і чи покриває рахунок підписка. Тут
14 агентів, 3 сесії працюють, 13 у спокої.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Він показує, куди пішов час і гроші ходу, інструмент за інструментом.**
Один хід реальної сесії: 11 інструментів за 11.2 хвилини за $1.16. Кожен виклик
Bash і виклик моделі отримує власний стовпчик на таймлайні, тож команда, яка
виконувалась 4.1 хвилини, і та, що виконалась за 226мс, помітно відрізняються з першого погляду.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Він оцінює роботу, а не лише витрати.**
Оцінка A цього тижня: 54 завдання виконано чисто, 2 складні коштували $48.57, а
запуски з недостатньою активністю для оцінки виключені з оцінки замість того,
щоб зараховуватися як успіх. Кожен складний запуск посилається на свій трейс.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Він показує, чому контекстне вікно постійно заповнюється.**
715K з вікна на 1M токенів на останньому ході, пік 83.3%, 4 компактизації,
всі спрацювали проактивно, а не через переповнення, і використання
кожного ходу за цим.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Виявлення працює без будь-яких налаштувань з вашого боку.**
Вбудовані детектори активні з моменту встановлення: агент замовк, потік
телеметрії зупинився, сплеск вартості, сплеск токенів, зростання помилок,
сплеск помилок, поріг бюджету, збіг сигнатури загрози, знахідка інструменту
безпеки, зміна стану безпеки. Ваші власні правила — опціональне доповнення.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Утримання ризикованого виклику — опціональне і вимкнене за замовчуванням.**
Рекурсивне видалення, примусовий push, sudo, секрети, встановлення пакетів і вихідні
виклики — кожен отримує правило, яке можна увімкнути. Поки ви цього не зробили,
ClawMetry спостерігає і нічого не змінює. Щойно правило увімкнено, відповідні виклики
чекають тут (або на вашому телефоні) на затвердження чи відхилення.

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
