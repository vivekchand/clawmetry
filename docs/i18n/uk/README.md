<!-- i18n-src:9767c8001c9c -->
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

**Дивіться, як думає ваш агент.** Спостережуваність у реальному часі для **30 середовищ виконання AI-агентів**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex та ще 26 інших. Одна панель для всього вашого флоту агентів.

> 🌐 **Читайте цією мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Одна команда. Нуль налаштувань. Автоматичне визначення всього.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**. Нуль налаштувань: система знаходить середовища виконання агентів, які у вас уже є, читає їх лише для читання і нічого не змінює в тому, як вони працюють.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Працює з 30 середовищами виконання агентів

**Безкоштовно у застосунку з відкритим кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**На платному плані:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Кожне середовище виконання отримує однакову панель. Запускайте кілька одночасно, і перемикач у шапці перенаправляє кожну вкладку на потрібне з них.

Створили власного агента на базі SDK? Перехоплювач відстежує і його виклики LLM. Дивіться [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Що ви отримуєте

- **Сесії та транскрипти**: що робив кожен агент, хід за ходом, з можливістю відтворення
- **Вартість і токени**: у розрізі середовища виконання, моделі, сесії та дня, з позначками аномалій
- **Потік (Flow)**: діаграма в реальному часі, що показує рух повідомлень через канали, моделі та інструменти
- **Мозок (Brain)**: потік подій міркувань та викликів інструментів у момент їх виникнення
- **Перевищення контексту**: використання вікна, розраховане окремо для кожного провайдера, компакція проти вимушеного переповнення, а також мапа того, чого ми *не бачимо* для кожного середовища виконання ([як це працює](docs/CONTEXT_BLOWOUT.md))
- **Пам'ять і навички**: файли та навички, які фактично завантажило кожне середовище виконання
- **Стан системи і логи**: диск, пам'ять, частота помилок, ліміти швидкості, потік логів у реальному часі
- **Сповіщення**: ліміти бюджету, сплески помилок, офлайн-агент, з маршрутизацією в Slack, Discord, PagerDuty, Telegram, Email
- **Погодження**: призупиняйте ризиковані виклики інструментів *до* їх виконання і погоджуйте зі свого телефону ([як це працює](docs/APPROVALS.md))

## Перевищення контексту та вартість спостереження

Два питання, на які варто отримати відповідь перед тим, як довіритися будь-якому інструменту порівняння агентів.

**Як система обробляє перевищення вікна контексту між різними середовищами виконання?**

Відсоток використання настільки чесний, наскільки чесним є те, на що його ділять. ClawMetry розраховує розмір вікна для кожного провайдера на основі [таблиці, яку можна прочитати і надіслати PR](clawmetry/context_windows.py), що охоплює Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama та GLM. Система не вимірює всі 26 середовищ виконання однією лінійкою одного постачальника. Це важливо: хід на 300K токенів у GPT-5, оцінений за міркою Anthropic на 200K, читається як ">100%, перевищено", хоча насправді це 75% від 400K у GPT-5. Та сама лінійка приховує справді переповнений хід DeepSeek на 130K, показуючи його як комфортні 65%.

Кожне вікно постачається з інформацією про походження: `model_table`, `explicit_marker`, `observed_floor` або чесне `default`, коли модель невідома. Індикатор, побудований на здогадці, ніколи не відображається з такою ж авторитетністю, як побудований на пошуку в таблиці.

ClawMetry може бачити події компакції лише для деяких середовищ виконання. Тому `GET /api/context-coverage` повідомляє, для кожного середовища виконання, чи означає **нуль "пройшло чисто" чи "ми сліпі"**. `0`, який насправді означає "сліпий", так і зазначається. [Детальніше](docs/CONTEXT_BLOWOUT.md)

**У що обходиться інструментування?**

| Шлях | Додано до вашого агента | За замовчуванням? |
|---|---|---|
| Читання файлів сесій (усі 30 середовищ виконання) | **0**. Окремий процес, жодного коду ClawMetry у вашому агенті | увімкнено |
| HTTP-перехоплювач (`CLAWMETRY_INTERCEPT=1`) | **+0,44 мс** на виклик LLM, або 0,009% від 5-секундного виклику | вимкнено |
| Шлюз попереднього хука інструменту (тепле кешування) | **+44 мс** на кожен перехоплений виклик інструменту, понад базові 36 мс інтерпретатора | вимкнено |
| Проксі примусового виконання | **+9,7 мс** на виклик LLM | вимкнено |

Вартість для хоста демона: **2 762 події/сек** прийому, **710 байт/подія** на диску (67,7 МБ на 100 тис. подій) і **~12% одного ядра** у сталому режимі на завантаженій інсталяції. Це останнє число перевищує наш власний заявлений бюджет у 5-10%, тому воно опубліковане як помилка, яку варто виправити, а не приховане.

Виміряно на Apple M2 Pro за допомогою `benchmarks/overhead.py`. Тестовий стенд запускає кожну умову в окремому процесі, чергує їх порядок і **відмовляється друкувати число, якщо раунди розходяться в знаку**. Запустіть це на своїй машині за хвилину:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Виміряно кожен шлях, включно з шлюзами хуків та проксі примусового виконання, і тестовий стенд працює на Linux, macOS та Windows у CI. Два результати, про які варто знати: проксі коштує приблизно у сім разів дорожче на Windows, ніж на Linux, а демон наразі стабільно споживає близько 12% одного ядра, що перевищує наш власний бюджет у 5-10%. Необроблені дані JSON, методика та те, що досі не виміряно, є в [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Ціни

| План | Що охоплює | Ціна |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, повна панель, лише локально | $0 |
| **Starter** | Усі інші середовища виконання вище, огляд флоту, хмарна синхронізація | $9 за вузол / місяць |
| **Pro** | Starter + керування та оцінювання: погодження, політики ризику інструментів, оцінки, виявлення аномалій, оптимізатор витрат, експорт OTel, захищений від підробки журнал аудиту | $19 за вузол / місяць |

Річні плани, Enterprise та актуальні числа доступні на сторінці
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключі ліцензії для самостійного хостингу працюють без хмари (`clawmetry license`). Точний розподіл безкоштовних і платних функцій наведено в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваші дані залишаються на вашій машині

ClawMetry читає локальні файли сесій та логи. **Жодні дані сесії не покидають вашу машину, доки ви не запустите `clawmetry connect`** — жодних запитів, відповідей, аргументів інструментів, вмісту файлів чи рядків логів. Коли ви підключаєтеся, знімок стану шифрується наскрізно ключем, який ніколи не залишає вашу машину, і розшифровується у вашому браузері. Якщо у вузла немає ключа, завантаження пропускається, а не надсилається у відкритому вигляді, і жодна відповідь сервера не може це змінити.

Дві речі виконуються за замовчуванням до підключення, обидві можна вимкнути, і жодна не передає дані сесії: анонімний пінг встановлення та перевірка версії на PyPI. Стандартна інсталяція також один раз перевіряє вашу публічну IP-адресу для рядка банера при запуску. Кожен пункт призначення, що він передає і як його вимкнути, перелічено в [docs/EGRESS.md](docs/EGRESS.md); самостійно розміщені, переспрямовані та ізольовані від мережі інсталяції взагалі не роблять жодних необов'язкових вихідних викликів.

Розшифрування відбувається у вашому браузері, у коді, який ми вам надаємо. Раніше це було обіцянкою; тепер це можна перевірити. Кожен рядок, що стосується вашого ключа, міститься в одному читабельному файлі, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), який постачається всередині wheel-пакету і подається дослівно, закріплений хешем Subresource Integrity. Щоб переконатися, що браузер виконує саме те, що ми опублікували:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чого це не доводить: ми надаємо сторінку, яка завантажує цей файл, тож ми могли б надавати іншу сторінку. Хеші цілісності захищають вас від скомпрометованого CDN, але не від постачальника. Що ви отримуєте: будь-яка підміна має бути навмисною, видимою у вихідному коді сторінки і відрізнятися від артефакту на PyPI, який будь-хто може завантажити. Самостійний хостинг або робота лише локально повністю усуває цю залежність.

## Встановлення

```bash
pip install clawmetry     # then: clawmetry
```

Або однорядковий варіант: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Потрібен Python 3.8+ на macOS, Linux або Windows, а також щонайменше одне середовище виконання агента на тій самій машині. Інструкції для Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Документація

| | |
|---|---|
| [Сумісність середовищ виконання](docs/compatibility.md) | Що читає кожен адаптер і як додати нове середовище виконання |
| [Перевищення контексту](docs/CONTEXT_BLOWOUT.md) | Вікна для кожного провайдера, компакція проти переповнення, покриття для кожного середовища виконання |
| [Накладні витрати](docs/OVERHEAD.md) | У що обходиться інструментування, виміряно, зі стендом для відтворення |
| [Права доступу](docs/ENTITLEMENTS.md) | Безкоштовне проти платного, матриця рівнів, CLI ліцензії |
| [Погодження та політики](docs/APPROVALS.md) | Контроль перед виконанням, оцінка ризиків, погодження з телефону |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Експортуйте трейси будь-куди, приймайте OTLP звідусіль |
| [Підключіть власного агента](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain від початку до кінця, з прикладами, які можна запустити |
| [Відстеження SDK](docs/SDK_TRACKING.md) | Атрибуція вартості для агентів, які ви створили самі |
| [Чат-канали](docs/CHANNELS.md) | Адаптери чатів, показані у Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Ізольовані (sandboxed) конфігурації NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтування томів |
| [Архітектура](ARCHITECTURE.md) · [Розробка](docs/DEVELOPMENT.md) | Як це працює зсередини; запуск із вихідного коду |
| [Телеметрія](docs/TELEMETRY.md) | Анонімні пінги встановлення та відкриття робочого столу, і як їх вимкнути |

## Знімки екрана

Кожне число нижче отримано з однієї реальної машини, лише для читання, без жодних штучних даних.

**Система повідомляє, коли щось не так, а не лише те, що сталося.**
Два банери аномалій вгорі: витрати перевищують середньодобові у 7 разів і сплеск вартості у 4,2 рази. Нижче — 324 із 667 останніх сесій із сигналом марнотратства, розбитим за причинами.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Система показує, куди пішли гроші, у будь-якому періоді.**
$252,47 сьогодні, $513,15 цього тижня, $1 312,92 цього місяця, кожне число з відповідними токенами і тим, яку частину вже покриває ваша підписка. Нижче — близько $1 128/міс, позначених як такі, що можна повернути, і $17 256/міс, уже заощаджених завдяки повторному використанню кешу.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Система показує, як повідомлення перетворюється на відповідь.**
Діаграма потоку в реальному часі: ви, канал, яким надійшло повідомлення, шлюз, модель, що відповідає прямо зараз, і кожен інструмент, до якого вона зверталася. Вузли підсвічуються, коли крізь них проходить робота.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Кожен агент на машині, в одній таблиці.**
Що він виконує, скільки коштує за останні 24 години і за весь час існування, коли його бачили востаннє, хто ним володіє, і чи покриває підписка рахунок. Тут 14 агентів, 3 сесії працюють, 13 у стані спокою.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Система показує, куди пішли час і гроші за хід, інструмент за інструментом.**
Один хід реальної сесії: 11 інструментів за 11,2 хвилини за $1,16. Кожен виклик Bash і кожен виклик моделі отримує власну смугу на часовій шкалі, тож команду, яка виконувалась 4,1 хвилини, і ту, що виконувалась 226 мс, легко відрізнити з першого погляду.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Система оцінює роботу, а не лише витрати.**
Оцінка A цього тижня: 54 завдання виконано без нарікань, 2 проблемні коштували $48,57, а прогони з надто малою активністю для оцінки виключено з підрахунку замість того, щоб зараховувати їх як успішні. Кожен проблемний прогін посилається на свій трейс.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Система показує, чому вікно контексту постійно заповнюється.**
715K із вікна на 1M токенів на останньому ході, пік 83,3%, 4 компакції, всі спрацювали проактивно, а не через переповнення, а також використання кожного ходу, що стоїть за цим.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Виявлення працює без будь-яких налаштувань з вашого боку.**
Вбудовані детектори активні одразу після встановлення: агент замовк, потік телеметрії зупинився, сплеск вартості, сплеск токенів, зростання помилок, сплеск помилок, поріг бюджету, збіг із сигнатурою загрози, знахідка інструмента безпеки, зміна стану безпеки. Власні правила є опціональним доповненням.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Затримка ризикованого виклику вмикається за бажанням і постачається вимкненою.**
Рекурсивне видалення, примусовий push, sudo, секрети, встановлення пакетів і вихідні виклики — для кожного є правило, яке можна увімкнути. Доки ви цього не зробите, ClawMetry лише спостерігає і нічого не змінює. Щойно правило увімкнено, відповідні виклики очікують тут (або на вашому телефоні) на погодження чи відмову.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Більше знімків, для кожного середовища виконання: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
