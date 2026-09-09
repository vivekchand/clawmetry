<!-- i18n-src:61beb8393e2f -->
> Українська translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Агент може зробити сотню викликів інструментів, так і не досягнувши прогресу.** ClawMetry
читає файли сесій, які ваші кодуючі агенти вже пишуть, і збирає хронологію,
виклики інструментів та будь-які дані про токени й вартість, які надає runtime, в одному
вигляді — щоб ви могли відрізнити довгий запуск, який працює, від того, що застряг.

Працює з **30 runtime для AI-агентів** — Claude Code, OpenAI Codex, Hermes, OpenClaw та ще 26. Одна панель для всього вашого флоту агентів. ([повний список](SUPPORTED_RUNTIMES.txt), згенерований з каталогу.)

> 🌐 **Читайте це мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ще →](docs/i18n/)

Одна команда. Нуль налаштувань. Все виявляється автоматично.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**. Нуль налаштувань: він знаходить runtime-и агентів,
які у вас уже є, читає їх лише для читання і нічого не змінює в тому, як вони працюють.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Перед встановленням

| | |
|---|---|
| **Що він робить** | Читає файли сесій та логи, які ваші агенти вже пишуть. Жодного SDK, жодних змін коду, жодної інструментації у вашому застосунку. |
| **Що ви бачите** | Хронологію сесії, покроковий replay інструментів, розбивку токенів і вартості, а також сигнали траєкторії (зациклення, повторні збої) — по кожному runtime. |
| **Що безкоштовно** | `pip install clawmetry` читає **OpenClaw, NVIDIA NemoClaw та Goose** без облікового запису, ключа чи мережевих викликів. Решту 27 — Claude Code, Codex, Cursor та інші — читає закритий компаньйон `clawmetry-pro`, який доступний у 7-денному пробному періоді або на платному плані — точний поділ дивіться в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Як почати** | `pip install clawmetry && clawmetry`, потім відкрийте localhost:8900. Ще немає агентів на цій машині? `clawmetry --sample` відкриється з трьома позначеними синтетичними сесіями. |
| **Що залишає вашу машину** | Жодні дані сесій, якщо ви не запустите `clawmetry connect`. За замовчуванням виконуються дві дії, обидві можна вимкнути, і жодна не містить вмісту сесій: анонімний пінг встановлення та перевірка версії на PyPI. Кожен пункт призначення описано в [docs/EGRESS.md](docs/EGRESS.md), відновлено з перехоплення трафіку, а не з коментарів у коді. |

Варто знати два обмеження перед оцінкою результатів: runtime-и надають дуже
різні дані (деякі взагалі не публікують вартість — [матриця](docs/compatibility.md)
показує, які саме, по кожному runtime), а спостереження за дією не те саме, що можливість
її заблокувати ([які елементи керування реальні, по кожному runtime](docs/APPROVALS.md)).


## Працює з 30 runtime агентів

**Безкоштовно у застосунку з відкритим кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**На платному плані:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Кожен runtime отримує ту саму панель. Запускайте декілька одночасно, і перемикач
у заголовку переналаштує кожну вкладку під один із них.

Створили власного агента на базі SDK замість цього? Перехоплювач відстежує і його
виклики LLM теж. Дивіться [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Що ви отримуєте

- **Сесії та транскрипти**: що робив кожен агент, хід за ходом, з можливістю replay
- **Вартість і токени**: по runtime, моделі, сесії та дню, з позначками аномалій
- **Flow**: жива діаграма руху повідомлень через канали, моделі та інструменти
- **Brain**: потік подій міркувань і викликів інструментів у реальному часі
- **Переповнення контексту**: використання вікна, розраховане під кожного постачальника, компакція проти вимушеного переповнення, плюс карта того, що ми *не можемо* побачити по кожному runtime ([як](docs/CONTEXT_BLOWOUT.md))
- **Пам'ять і навички**: файли та навички, які фактично завантажив кожен runtime
- **Здоров'я та логи**: диск, пам'ять, частота помилок, ліміти запитів, потік логів у реальному часі
- **Сповіщення**: ліміти бюджету, сплески помилок, агент офлайн, з маршрутизацією в Slack, Discord, PagerDuty, Telegram, Email
- **Погодження**: призупиняйте ризиковані виклики інструментів *до* їх виконання і погоджуйте з телефону ([як](docs/APPROVALS.md))

## Переповнення контексту та вартість спостереження

Два питання, на які варто відповісти перед тим, як довіряти будь-якому інструменту порівняння агентів.

**Як він обробляє переповнення контекстного вікна між runtime-ами?**

Відсоток використання настільки чесний, наскільки чесний знаменник. ClawMetry
визначає розмір вікна для кожного постачальника з [таблиці, яку можна прочитати й
запропонувати PR](clawmetry/context_windows.py), що охоплює Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama та GLM. Він не вимірює всі 30
runtime-ів однією лінійкою одного постачальника. Це важливо: хід на 300K токенів у GPT-5,
оцінений за міркою Anthropic на 200K, читається як ">100%, переповнено", хоча насправді це 75% від
400K у GPT-5. Та сама лінійка приховує справді переповнений хід DeepSeek на 130K,
показуючи його як комфортні 65%.

Кожне вікно постачається з походженням: `model_table`, `explicit_marker`,
`observed_floor` або чесний `default`, коли модель невідома. Індикатор, побудований
на здогадці, ніколи не відображається з тим самим авторитетом, що й побудований на
довіднику.

ClawMetry може бачити події компакції лише в деяких runtime-ах. Тому
`GET /api/context-coverage` повідомляє по кожному runtime, чи означає нуль
"пройшло чисто" або "ми сліпі". Нуль, який насправді означає сліпоту, так і каже.
[Детальніше](docs/CONTEXT_BLOWOUT.md)

**Скільки коштує інструментація?**

| Шлях | Додано до вашого агента | За замовчуванням? |
|---|---|---|
| Читання файлу сесії (всі 30 runtime-ів) | **0**. Окремий процес, жодного коду ClawMetry у вашому агенті | увімкнено |
| HTTP-перехоплювач (`CLAWMETRY_INTERCEPT=1`) | **+0,44 мс** на виклик LLM, або 0,009% від 5-секундного виклику | вимкнено |
| Ворота pre-tool hook (тепла кеш-пам'ять) | **+44 мс** на кожен перевірений виклик інструмента, понад базові 36 мс інтерпретатора | вимкнено |
| Проксі примусового виконання | **+9,7 мс** на виклик LLM | вимкнено |

Вартість для хоста демона: **2 762 подій/сек** прийому, **710 байт/подію** на диску
(67,7 МБ на 100 тис. подій), і **~12% одного ядра** стабільно на завантаженій
інсталяції. Це останнє число перевищує наш власний заявлений бюджет 5–10%, тому
опубліковано як баг для усунення, а не приховано зі сторінки.

Виміряно на Apple M2 Pro за допомогою `benchmarks/overhead.py`. Тестовий стенд запускає
кожну умову в окремому процесі, чергує їхній порядок і **відмовляється друкувати
число, коли раунди розходяться в його знаку**. Запустіть його на власній
машині за хвилину:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Виміряно кожен шлях, включно з воротами hook та проксі примусового виконання,
і тестовий стенд працює на Linux, macOS та Windows у CI. Варто знати два результати:
проксі коштує приблизно в сім разів більше на Windows, ніж на Linux, а
демон наразі стабільно споживає близько 12% одного ядра, понад наш власний бюджет 5–10%.
Необроблений JSON, методологія та те, що досі не виміряно, — в
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Ціни

| План | Що покриває | Ціна |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, повна панель, лише локально | $0 |
| **Starter** | Усі інші runtime-и вище, огляд флоту, синхронізація з хмарою | $9 за вузол / місяць |
| **Pro** | Starter + керування й оцінка: погодження, політики ризику інструментів, evals, виявлення аномалій, оптимізатор вартості, експорт OTel, журнал аудиту із захистом від підробки | $19 за вузол / місяць |

Річні плани, Enterprise та актуальні ціни — на
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключі ліцензій для самостійного розміщення
працюють без хмари (`clawmetry license`). Точний поділ безкоштовного/платного —
в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваші дані залишаються на вашій машині

ClawMetry читає локальні файли сесій та логи. **Жодні дані сесій не залишають вашу машину,
якщо ви не запустите `clawmetry connect`** — жодних запитів, відповідей, аргументів інструментів, вмісту файлів
чи рядків логів. Коли ви підключаєтесь, знімок шифрується наскрізно
ключем, який ніколи не залишає вашу машину, і розшифровується у вашому браузері. Якщо
у вузла немає ключа, завантаження пропускається, а не надсилається у відкритому вигляді, і жодна
відповідь сервера не може це вимкнути.

За замовчуванням до підключення виконуються дві дії, обидві можна вимкнути, і жодна не містить
даних сесій: анонімний пінг встановлення та перевірка версії на
PyPI. Стандартна інсталяція також один раз перевіряє вашу публічну IP-адресу для рядка
банера при запуску. Кожен пункт призначення, що він містить і як його вимкнути, перелічено в
[docs/EGRESS.md](docs/EGRESS.md); інсталяції із самостійним розміщенням, переспрямовані та ізольовані
не роблять жодних довільних вихідних викликів.

Розшифрування відбувається у вашому браузері, у коді, який ми вам надаємо. Раніше це було
обіцянкою; тепер це можна перевірити. Кожен рядок, що торкається вашого ключа,
знаходиться в одному читабельному файлі, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
який постачається всередині wheel-пакета і подається без змін, закріплений хешем Subresource
Integrity. Щоб підтвердити, що браузер виконує саме те, що ми опублікували:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чого це не доводить: ми подаємо сторінку, яка завантажує файл, тож ми могли б
подати іншу сторінку. Хеші цілісності захищають вас від скомпрометованого CDN,
а не від постачальника. Ви отримуєте те, що будь-яка підміна має бути
навмисною, видимою у вихідному коді сторінки та відрізнятися від артефакту на PyPI,
який будь-хто може завантажити. Самостійне розміщення або робота лише локально
повністю усуває цю залежність.

## Встановлення

```bash
pip install clawmetry     # потім: clawmetry
```

Або однорядковий варіант: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Потрібен Python 3.8+ на macOS, Linux чи Windows, і хоча б один runtime агента на
тій самій машині. Інструкції для Docker: [docs/DOCKER.md](docs/DOCKER.md).

Або дозвольте агенту налаштувати все за вас. Навичка [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
навчає Claude Code, Codex, Cursor, Gemini CLI, Copilot чи OpenCode
встановлювати ClawMetry, повідомляти, що роблять і скільки витрачають агенти на машині,
зупиняти сесію за запитом і затримувати ризиковані виклики інструментів для погодження:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Документація

| | |
|---|---|
| [Сумісність runtime](docs/compatibility.md) | Що читає кожен адаптер і як додати runtime |
| [Переповнення контексту](docs/CONTEXT_BLOWOUT.md) | Вікна для кожного постачальника, компакція проти переповнення, покриття по runtime |
| [Накладні витрати](docs/OVERHEAD.md) | Скільки коштує інструментація, виміряно, з тестовим стендом для відтворення |
| [Права доступу](docs/ENTITLEMENTS.md) | Безкоштовне проти платного, матриця рівнів, CLI ліцензій |
| [Погодження та політики](docs/APPROVALS.md) | Контроль перед виконанням, оцінка ризику, погодження з телефону |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Експортуйте трейси куди завгодно, приймайте OTLP звідки завгодно |
| [Принесіть власного агента](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain від початку до кінця, з робочими прикладами |
| [Відстеження SDK](docs/SDK_TRACKING.md) | Атрибуція вартості для агентів, яких ви створили самі |
| [Чат-канали](docs/CHANNELS.md) | Адаптери чату, показані у Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Ізольовані налаштування NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтування томів |
| [Архітектура](ARCHITECTURE.md) · [Розробка](docs/DEVELOPMENT.md) | Як це працює всередині; запуск із вихідного коду |
| [Телеметрія](docs/TELEMETRY.md) | Анонімні пінги встановлення й відкриття десктопного застосунку, і як їх вимкнути |

## Знімки екрана

Кожне число нижче — з однієї реальної машини, лише для читання, нічого не підготовлено штучно.

**Він повідомляє, коли щось не так, а не лише що сталося.**
Два банери аномалій зверху: витрати в 7 разів вище середньоденних та
сплеск вартості в 4,2 рази. Нижче — 324 з 667 останніх сесій із сигналом
марнотратства, розбитим за причинами.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Він показує, куди пішли гроші, у будь-якому вікні.**
$252,47 сьогодні, $513,15 цього тижня, $1 312,92 цього місяця, кожне з токенами
за цим і скільки з цього вже покриває ваша підписка. Нижче — приблизно
$1 128/міс, розписаних як таких, що можна повернути, і $17 256/міс, уже заощаджених
завдяки повторному використанню кешу.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Він малює, як повідомлення перетворюється на відповідь.**
Жива діаграма flow: ви, канал, яким воно надійшло, шлюз, модель,
яка відповідає прямо зараз, і кожен інструмент, до якого вона зверталася. Вузли підсвічуються,
коли крізь них проходить робота.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Кожен агент на машині — в одній таблиці.**
Що він виконує, скільки коштує за останні 24 години та за весь час, коли
його востаннє бачили, хто ним володіє і чи покриває витрати підписка. 14 агентів тут,
3 сесії працюють, 13 тихі.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Він показує, куди пішов час і гроші ходу, інструмент за інструментом.**
Один хід реальної сесії: 11 інструментів за 11,2 хвилини за $1,16. Кожен виклик Bash
і виклик моделі отримує свою смугу на хронології, тож команда, що виконувалась
4,1 хвилини, і та, що виконалась за 226 мс, помітні з одного погляду.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Він оцінює роботу, а не лише витрати.**
Оцінка "A" цього тижня: 54 завдання виконано чисто, 2 складних коштували $48,57, а
запуски з надто малою активністю для оцінки виключені з підсумку замість того, щоб
рахуватися як успіх. Кожен складний запуск веде до свого трейсу.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Він показує, чому контекстне вікно продовжує заповнюватися.**
715 тис. з вікна на 1 млн токенів на останньому ході, пік 83,3%, 4 компакції,
що всі спрацювали проактивно, а не через переповнення, і використання
кожного ходу за цим.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Виявлення працює без будь-яких налаштувань з вашого боку.**
Вбудовані детектори увімкнені з моменту встановлення: агент замовк, потік телеметрії
зупинився, сплеск вартості, сплеск токенів, зростання помилок, сплеск помилок, поріг
бюджету, збіг сигнатури загрози, знахідка інструменту безпеки, зміна стану безпеки.
Ваші власні правила — опційно, поверх цього.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Затримка ризикованого виклику — опційна і постачається вимкненою.**
Рекурсивне видалення, примусовий push, sudo, секрети, встановлення пакетів і вихідні
виклики — кожен отримує правило, яке можна увімкнути. Поки ви цього не зробите, ClawMetry спостерігає і
нічого не змінює. Щойно одне увімкнено, відповідні виклики чекають тут (або на вашому телефоні)
на погодження чи відмову.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Більше, по кожному runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
