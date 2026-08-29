<!-- i18n-src:d21bea5161e0 -->
> Українська translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Побачте, як думає ваш агент.** Спостережуваність у реальному часі для **30 середовищ виконання AI-агентів**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex та ще 26. Одна панель для всього вашого флоту агентів.

> 🌐 **Читайте це мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Одна команда. Нуль налаштувань. Все визначається автоматично.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**. Нуль налаштувань: система знаходить середовища виконання агентів,
які у вас уже є, читає їх у режимі лише читання й нічого не змінює в тому, як вони працюють.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Працює з 30 середовищами виконання агентів

**Безкоштовно у застосунку з відкритим кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**У платному тарифі:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Кожне середовище виконання отримує однакову панель. Запускайте кілька одночасно —
перемикач у заголовку переорієнтує кожну вкладку на обране з них.

Створили власного агента на базі SDK? Перехоплювач відстежує й його виклики LLM.
Дивіться [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Що ви отримуєте

- **Сесії та транскрипти**: що робив кожен агент, хід за ходом, із відтворенням
- **Витрати й токени**: за середовищем виконання, моделлю, сесією та днем, із позначками аномалій
- **Flow**: діаграма руху повідомлень через канали, моделі та інструменти в реальному часі
- **Brain**: потік подій міркувань і викликів інструментів у режимі реального часу
- **Переповнення контексту**: використання вікна, розмірене під кожного провайдера, компактизація проти вимушеного переповнення, а також карта того, чого ми *не бачимо* для кожного середовища виконання ([як](docs/CONTEXT_BLOWOUT.md))
- **Пам'ять і навички**: файли та навички, які фактично завантажило кожне середовище виконання
- **Стан і логи**: диск, пам'ять, частота помилок, ліміти швидкості, потік логів у реальному часі
- **Сповіщення**: ліміти бюджету, сплески помилок, офлайн-агент, з маршрутизацією у Slack, Discord, PagerDuty, Telegram, Email
- **Погодження**: призупиняйте ризиковані виклики інструментів *до* їх виконання й погоджуйте з телефону ([як](docs/APPROVALS.md))

## Переповнення контексту та вартість спостереження

Два питання, варті відповіді, перш ніж довіряти будь-якому інструменту порівняння агентів.

**Як це обробляє переповнення вікна контексту між різними середовищами виконання?**

Відсоток використання настільки чесний, наскільки чесне те, на що його ділять. ClawMetry
визначає розмір вікна для кожного провайдера з [таблиці, яку можна прочитати й
запропонувати PR](clawmetry/context_windows.py), що охоплює Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama та GLM. Система не вимірює всі 26
середовищ виконання лінійкою одного постачальника. Це важливо: хід на 300K токенів у GPT-5,
оцінений за міркою Anthropic на 200K, читається як ">100%, переповнено", тоді як насправді
це 75% від 400K GPT-5. Та сама лінійка приховує справді переповнений хід DeepSeek на 130K,
показуючи його як комфортні 65%.

Кожне вікно постачається з походженням значення: `model_table`, `explicit_marker`,
`observed_floor`, або чесний `default`, коли модель невідома. Індикатор, побудований на
здогадці, ніколи не відображається з тим же авторитетом, що й побудований на
довідковій таблиці.

ClawMetry може бачити події компактизації лише в деяких середовищах виконання. Тому
`GET /api/context-coverage` повідомляє, для кожного середовища виконання, чи означає
**нуль "пройшло чисто" чи "ми сліпі"**. `0`, що насправді означає сліпоту, так і повідомляється.
[Детальніше](docs/CONTEXT_BLOWOUT.md)

**Скільки коштує інструментація?**

| Шлях | Додається до вашого агента | За замовчуванням? |
|---|---|---|
| Читання файлів сесій (усі 30 середовищ виконання) | **0**. Окремий процес, без коду ClawMetry у вашому агенті | увімкнено |
| HTTP-перехоплювач (`CLAWMETRY_INTERCEPT=1`) | **+0.44 мс** на виклик LLM, або 0.009% від 5-секундного виклику | вимкнено |
| Хук перед інструментом (тепла кеш-пам'ять) | **+44 мс** на керований виклик інструменту, понад базові 36 мс інтерпретатора | вимкнено |
| Проксі примусового виконання | **+9.7 мс** на виклик LLM | вимкнено |

Вартість для хосту демона: **2 762 подій/с** прийому, **710 байт/подію** на диску
(67.7 МБ на 100 тис. подій), та **~12% одного ядра** у стабільному режимі на завантаженій
інсталяції. Останнє число перевищує наш власний заявлений бюджет у 5-10%, тому воно
опубліковане як баг, який потрібно виправити, а не приховане зі сторінки.

Виміряно на Apple M2 Pro за допомогою `benchmarks/overhead.py`. Тестовий набір запускає
кожну умову в окремому процесі, чергує їх порядок і **відмовляється друкувати число, коли
раунди розходяться щодо його знака**. Запустіть його на власній машині за хвилину:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Виміряно кожен шлях, включно з хуками та проксі примусового виконання,
і тестовий набір працює на Linux, macOS та Windows у CI. Два результати варті уваги:
проксі коштує приблизно у сім разів більше на Windows, ніж на Linux, а демон наразі
стабільно споживає близько 12% одного ядра, що перевищує наш власний бюджет у 5-10%.
Необроблені дані JSON, методологія та те, що досі не виміряно, — у
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Ціни

| Тариф | Що охоплює | Ціна |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, повна панель, лише локально | $0 |
| **Starter** | Усі інші середовища виконання вище, вигляд флоту, синхронізація з хмарою | $9 за вузол / місяць |
| **Pro** | Starter + контроль і оцінка: погодження, політики ризику інструментів, оцінки, виявлення аномалій, оптимізатор витрат, експорт OTel, захищений від підробки журнал аудиту | $19 за вузол / місяць |

Річні тарифи, Enterprise і поточні ціни — на сторінці
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключі ліцензії для власного
хостингу працюють без хмари (`clawmetry license`). Точний розподіл безкоштовних і
платних функцій — у [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваші дані залишаються на вашій машині

ClawMetry читає локальні файли сесій і логи. **Жодні дані сесій не залишають вашу
машину, доки ви не запустите `clawmetry connect`** — жодних запитів, відповідей,
аргументів інструментів, вмісту файлів чи рядків логів. Коли ви підключаєтеся,
знімок шифрується наскрізно ключем, який ніколи не залишає вашу машину, і
розшифровується у вашому браузері. Якщо у вузла немає ключа, завантаження
пропускається, а не надсилається у відкритому вигляді, і жодна відповідь сервера
не може це змінити.

Дві речі все ж виконуються за замовчуванням до підключення, обидві з можливістю
відмови і без даних сесій: анонімний пінг встановлення й перевірка версії щодо
PyPI. Стандартна інсталяція також один раз шукає вашу публічну IP-адресу для
рядка стартового банера. Кожен пункт призначення, що він передає та як його
вимкнути, перелічено в [docs/EGRESS.md](docs/EGRESS.md); самостійно хостовані,
переспрямовані та ізольовані від мережі інсталяції не роблять жодних
довільних вихідних викликів взагалі.

Розшифрування відбувається у вашому браузері, у коді, який ми вам надсилаємо.
Раніше це було обіцянкою; тепер це те, що можна перевірити. Кожен рядок, що
торкається вашого ключа, міститься в одному файлі, доступному для читання —
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
який постачається всередині wheel-пакету й подається дослівно, закріплений
хешем Subresource Integrity. Щоб переконатися, що браузер запускає те, що ми
опублікували:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чого це не доводить: ми подаємо сторінку, яка завантажує цей файл, тож ми могли б
подати іншу сторінку. Хеші цілісності захищають вас від скомпрометованого CDN,
а не від постачальника. Що ви отримуєте — так це те, що будь-яка підміна має
бути навмисною, видимою у вихідному коді сторінки й відрізнятися від артефакту
на PyPI, який будь-хто може завантажити. Самостійний хостинг або робота лише
локально повністю усуває цю залежність.

## Встановлення

```bash
pip install clawmetry     # then: clawmetry
```

Або однорядковий скрипт: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Потрібен Python 3.8+ на macOS, Linux або Windows, і принаймні одне середовище
виконання агента на тій самій машині. Інструкції для Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Документація

| | |
|---|---|
| [Сумісність середовищ виконання](docs/compatibility.md) | Що читає кожен адаптер і як додати середовище виконання |
| [Переповнення контексту](docs/CONTEXT_BLOWOUT.md) | Вікна для кожного провайдера, компактизація проти переповнення, покриття для кожного середовища виконання |
| [Накладні витрати](docs/OVERHEAD.md) | Що коштує інструментація, виміряно, з тестовим набором для відтворення |
| [Права доступу](docs/ENTITLEMENTS.md) | Безкоштовне проти платного, матриця тарифів, CLI для ліцензії |
| [Погодження та політики](docs/APPROVALS.md) | Перевірка перед виконанням, оцінка ризиків, погодження з телефону |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Експортуйте трейси будь-куди, приймайте OTLP звідусіль |
| [Відстеження SDK](docs/SDK_TRACKING.md) | Атрибуція витрат для агентів, які ви створили самостійно |
| [Чат-канали](docs/CHANNELS.md) | Адаптери чату, показані у Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Захищені пісочницею налаштування NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтування томів |
| [Архітектура](ARCHITECTURE.md) · [Розробка](docs/DEVELOPMENT.md) | Як це працює всередині; запуск із вихідного коду |
| [Телеметрія](docs/TELEMETRY.md) | Анонімні піги встановлення й відкриття застосунку, і як їх вимкнути |

## Знімки екрана

Кожне число нижче — з однієї реальної машини, у режимі лише читання, без жодних штучних даних.

**Система повідомляє, коли щось не так, а не лише що сталося.**
Два банери аномалій зверху: витрати на рівні 7x денного середнього і сплеск
витрат у 4.2x. Нижче — 324 з 667 останніх сесій із ознакою марнотратства,
розбитою за причинами.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Система показує, куди пішли гроші, у кожному вікні.**
$252.47 сьогодні, $513.15 цього тижня, $1,312.92 цього місяця, кожне з
токенами позаду й тим, скільки з цього вже покриває ваша підписка. Нижче —
близько $1,128/міс, зазначені як такі, що можна повернути, і $17,256/міс уже
заощаджені завдяки повторному використанню кешу.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Система малює, як повідомлення стає відповіддю.**
Діаграма потоку в реальному часі: ви, канал, яким воно надійшло, шлюз, модель,
що відповідає прямо зараз, і кожен інструмент, до якого вона зверталася. Вузли
підсвічуються, коли робота проходить через них.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Кожен агент на машині, в одній таблиці.**
Що він виконує, скільки коштує за останні 24 години й за весь час, коли його
востаннє бачили, хто ним володіє, і чи покриває рахунок підписка. Тут 14
агентів, 3 сесії працюють, 13 у спокої.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Система показує, куди пішли час і гроші ходу, інструмент за інструментом.**
Один хід реальної сесії: 11 інструментів за 11.2 хвилини за $1.16. Кожен виклик
Bash і виклик моделі отримує власний стовпчик на часовій шкалі, тому команда,
що виконувалася 4.1 хвилини, і та, що виконувалася 226 мс, розрізняються з
першого погляду.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Система оцінює роботу, а не лише витрати.**
Оцінка A цього тижня: 54 завдання виконано чисто, 2 проблемних коштували
$48.57, а прогони з надто малою активністю для оцінки виключаються з оцінки
замість того, щоб рахуватися як успіх. Кожен проблемний прогін посилається на
свій трейс.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Система показує, чому вікно контексту продовжує заповнюватися.**
715K з 1M-токенного вікна на останньому ході, пік 83.3%, 4 компактизації, всі
з яких спрацювали проактивно, а не через переповнення, а також використання
кожного ходу позаду цього.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Виявлення працює без будь-яких налаштувань з вашого боку.**
Вбудовані детектори увімкнені з моменту встановлення: агент замовк, потік
телеметрії зупинився, сплеск витрат, сплеск токенів, зростання помилок,
сплеск помилок, поріг бюджету, збіг сигнатури загрози, знахідка інструменту
безпеки, зміна стану безпеки. Власні правила — опціональні, додатково.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Утримання ризикованого виклику — опціональне, і постачається вимкненим.**
Рекурсивне видалення, примусовий push, sudo, секрети, встановлення пакетів
і вихідні виклики — кожне отримує правило, яке можна увімкнути. Доки ви цього
не зробите, ClawMetry спостерігає й нічого не змінює. Щойно одне увімкнено,
відповідні виклики чекають тут (або на вашому телефоні) на погодження чи
відмову.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Більше, для кожного середовища виконання: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
