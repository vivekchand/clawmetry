<!-- i18n-src:88be2deff5d5 -->
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

**Дивіться, як думає ваш агент.** Спостереження в реальному часі для **30 середовищ виконання AI-агентів**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex та ще 26 інших. Одна панель для всього вашого флоту агентів.

> 🌐 **Читати цією мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ще →](docs/i18n/)

Одна команда. Нуль налаштувань. Автоматичне визначення всього.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**. Нуль налаштувань: програма знаходить середовища виконання агентів, які у вас уже є, читає їх у режимі "лише читання" і нічого не змінює в тому, як вони працюють.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Працює з 30 середовищами виконання агентів

**Безкоштовно у застосунку з відкритим кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**У платному плані:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Кожне середовище виконання отримує ту саму панель. Запустіть декілька одночасно, і перемикач у заголовку переналаштовує кожну вкладку на потрібне з них.

Створили власного агента на базі SDK замість готового середовища? Перехоплювач відстежує і його виклики LLM. Дивіться [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Що ви отримуєте

- **Сесії та транскрипти**: що робив кожен агент, крок за кроком, з можливістю відтворення
- **Вартість і токени**: за середовищем виконання, моделлю, сесією та днем, з позначками аномалій
- **Потік (Flow)**: живу діаграму того, як повідомлення рухаються через канали, моделі та інструменти
- **Brain**: потік подій мислення та викликів інструментів у режимі реального часу
- **Перевантаження контексту**: використання вікна, розраховане окремо для кожного провайдера, компактизація проти вимушеного переповнення, а також карта того, чого ми *не бачимо* для кожного середовища виконання ([як це працює](docs/CONTEXT_BLOWOUT.md))
- **Пам'ять і навички**: файли та навички, які фактично завантажило кожне середовище виконання
- **Стан і логи**: диск, пам'ять, частота помилок, ліміти швидкості, потік логів у реальному часі
- **Сповіщення**: обмеження бюджету, сплески помилок, офлайн-агент, з маршрутизацією в Slack, Discord, PagerDuty, Telegram, Email
- **Затвердження**: призупиняйте ризиковані виклики інструментів *до* їх виконання і затверджуйте з телефону ([як це працює](docs/APPROVALS.md))

## Перевантаження контексту, і скільки коштує спостереження

Два питання, на які варто відповісти, перш ніж довіряти будь-якому інструменту порівняння агентів.

**Як воно обробляє перевантаження контекстного вікна між різними середовищами виконання?**

Відсоток використання чесний настільки, наскільки чесним є те, на що він ділиться. ClawMetry визначає розмір вікна для кожного провайдера за [таблицею, яку можна прочитати і надіслати PR](clawmetry/context_windows.py), що охоплює Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama та GLM. Програма не вимірює всі 30 середовищ виконання лінійкою одного вендора. Це важливо: хід на 300K токенів GPT-5, оцінений за міркою Anthropic на 200K, читається як ">100%, перевантажено", тоді як насправді це 75% від 400K GPT-5. Та сама лінійка приховує справді переповнений хід DeepSeek на 130K токенів як комфортні 65%.

Кожне вікно постачається з даними про своє походження: `model_table`, `explicit_marker`, `observed_floor`, або чесне `default`, коли ми не знаємо модель. Індикатор, побудований на здогадці, ніколи не відображається з тим самим авторитетом, що й той, що побудований на пошуку в таблиці.

ClawMetry може бачити події компактизації лише в деяких середовищах виконання. Тож `GET /api/context-coverage` повідомляє для кожного середовища виконання, чи означає нуль **"пройшло чисто" або "ми сліпі"**. `0`, який насправді означає сліпоту, так і повідомляється.
[Повні деталі](docs/CONTEXT_BLOWOUT.md)

**Скільки коштує інструментація?**

| Шлях | Додається до вашого агента | За замовчуванням? |
|---|---|---|
| Читання файлів сесій (усі 30 середовищ виконання) | **0**. Окремий процес, жодного коду ClawMetry у вашому агенті | увімкнено |
| HTTP-перехоплювач (`CLAWMETRY_INTERCEPT=1`) | **+0.44 мс** на виклик LLM, або 0.009% від виклику тривалістю 5с | вимкнено |
| Ворота попереднього хука (тепла кешу) | **+44 мс** на кожен перевірюваний виклик інструменту, понад базові 36 мс інтерпретатора | вимкнено |
| Проксі примусового виконання | **+9.7 мс** на виклик LLM | вимкнено |

Вартість для хоста демона: **2 762 події/сек** прийому, **710 байт/подію** на диску
(67.7 МБ на 100 тис. подій), і **~12% одного ядра** сталого навантаження на завантаженій
інсталяції. Це останнє число перевищує наш власний заявлений бюджет у 5-10%, тому
воно опубліковане як помилка, яку варто виправити, а не приховане зі сторінки.

Виміряно на Apple M2 Pro за допомогою `benchmarks/overhead.py`. Тестовий набір
запускає кожну умову в окремому процесі, чергує їхній порядок і **відмовляється
друкувати число, якщо раунди не збігаються за знаком**. Запустіть його на своїй
власній машині за хвилину:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Виміряно кожен шлях, включно з воротами хуків та проксі примусового виконання,
і тестовий набір запускається на Linux, macOS та Windows у CI. Два результати,
які варто знати: проксі коштує приблизно у сім разів більше на Windows, ніж на
Linux, а демон наразі витримує близько 12% одного ядра, що перевищує наш
власний бюджет 5-10%. Сирі дані JSON, методика та те, що досі не виміряно, —
у [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Ціни

| План | Що охоплює | Ціна |
|---|---|---|
| **Безкоштовний** | OpenClaw + NVIDIA NemoClaw + Goose, повна панель, лише локально | $0 |
| **Starter** | Усі інші середовища виконання вище, огляд флоту, синхронізація з хмарою | $9 за вузол / місяць |
| **Pro** | Starter + контроль та оцінювання: затвердження, політики ризику інструментів, оцінки, виявлення аномалій, оптимізатор витрат, експорт OTel, журнал аудиту, стійкий до підробок | $19 за вузол / місяць |

Річні плани, Enterprise та актуальні ціни — на
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключі ліцензій для
самостійного розміщення працюють без хмари (`clawmetry license`). Точний
розподіл безкоштовного/платного — в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваші дані залишаються на вашому пристрої

ClawMetry читає локальні файли сесій і логи. **Жодні дані сесій не покидають
ваш пристрій, якщо ви не запустите `clawmetry connect`** — жодних підказок,
відповідей, аргументів інструментів, вмісту файлів чи рядків логів. Коли ви
все ж підключаєтесь, знімок даних шифрується наскрізним шифруванням ключем,
який ніколи не покидає вашу машину, і розшифровується у вашому браузері. Якщо
у вузла немає ключа, завантаження пропускається, а не надсилається у
відкритому вигляді, і жодна відповідь сервера не може це вимкнути.

Дві речі виконуються за замовчуванням до підключення, обидві з можливістю
відмови і жодна не несе даних сесій: анонімний пінг встановлення та перевірка
версії проти PyPI. Стандартна інсталяція також один раз перевіряє вашу
публічну IP-адресу для рядка банера при запуску. Кожен пункт призначення, що
він передає і як його вимкнути, перелічено в
[docs/EGRESS.md](docs/EGRESS.md); самостійно розміщені, перенаправлені та
ізольовані від мережі інсталяції не роблять жодних довільних вихідних
викликів взагалі.

Розшифрування відбувається у вашому браузері, у коді, який ми вам надаємо. Раніше
це було обіцянкою; тепер це те, що можна перевірити. Кожен рядок, що
торкається вашого ключа, живе в одному файлі, доступному для читання,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), який
постачається всередині wheel-пакета і подається дослівно, закріплений хешем
Subresource Integrity. Щоб перевірити, що браузер виконує саме те, що ми
опублікували:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чого це не доводить: ми подаємо саму сторінку, яка завантажує цей файл, тож ми
могли б подати іншу сторінку. Хеші цілісності захищають вас від скомпрометованої
CDN, а не від постачальника. Ви отримуєте те, що будь-яка підміна має бути
навмисною, видимою в коді сторінки і відрізнятися від артефакту на PyPI, який
кожен може завантажити. Самостійне розміщення або робота лише в локальному
режимі повністю усуває цю залежність.

## Встановлення

```bash
pip install clawmetry     # потім: clawmetry
```

Або однорядковий скрипт: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Потрібен Python 3.8+ на macOS, Linux або Windows, і хоча б одне середовище
виконання агента на тій самій машині. Інструкції для Docker:
[docs/DOCKER.md](docs/DOCKER.md).

Або нехай агент налаштує все за вас. Навичка
[`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) навчає Claude Code,
Codex, Cursor, Gemini CLI, Copilot або OpenCode встановлювати ClawMetry,
звітувати про те, що роблять і скільки витрачають агенти на машині,
зупиняти одну сесію на запит і затримувати ризиковані виклики інструментів
для затвердження:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Документація

| | |
|---|---|
| [Сумісність середовищ виконання](docs/compatibility.md) | Що читає кожен адаптер і як додати середовище виконання |
| [Перевантаження контексту](docs/CONTEXT_BLOWOUT.md) | Вікна для кожного провайдера, компактизація проти переповнення, покриття для кожного середовища виконання |
| [Накладні витрати](docs/OVERHEAD.md) | Скільки коштує інструментація, виміряно, з тестовим набором для відтворення |
| [Права доступу](docs/ENTITLEMENTS.md) | Безкоштовне проти платного, матриця тарифів, CLI для ліцензій |
| [Затвердження та політики](docs/APPROVALS.md) | Контроль перед виконанням, оцінка ризику, затвердження з телефону |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Експортуйте трейси куди завгодно, приймайте OTLP звідки завгодно |
| [Принесіть власного агента](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain від початку до кінця, з прикладами, які можна запустити |
| [Відстеження SDK](docs/SDK_TRACKING.md) | Атрибуція вартості для агентів, яких ви створили самостійно |
| [Чат-канали](docs/CHANNELS.md) | Адаптери чатів, показані у Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Ізольовані (sandboxed) налаштування NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтування томів |
| [Архітектура](ARCHITECTURE.md) · [Розробка](docs/DEVELOPMENT.md) | Як це працює зсередини; запуск із вихідного коду |
| [Телеметрія](docs/TELEMETRY.md) | Анонімні піни встановлення та відкриття десктопного застосунку, і як їх вимкнути |

## Скриншоти

Кожна цифра нижче — з однієї реальної машини, у режимі лише читання, без жодних підготовлених даних.

**Програма повідомляє, коли щось не так, а не лише що сталося.**
Два банери аномалій зверху: витрати вдвічі більше 7-разового денного середнього
та сплеск вартості у 4.2 рази. Нижче — 324 з 667 останніх сесій, що несуть
сигнал марнотратства, з розбивкою за причиною.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Програма показує, куди пішли гроші, у кожному вікні часу.**
$252.47 сьогодні, $513.15 цього тижня, $1312.92 цього місяця, кожне з
токенами, що стоять за ним, і скільки з цього вже покриває ваша підписка.
Нижче — приблизно $1128/міс, позначені як такі, що можна повернути, і вже
$17256/міс, заощаджені завдяки повторному використанню кешу.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Програма малює, як повідомлення перетворюється на відповідь.**
Жива діаграма потоку: ви, канал, яким прийшло повідомлення, шлюз (gateway),
модель, що відповідає прямо зараз, і кожен інструмент, до якого вона
звернулась. Вузли підсвічуються, коли крізь них проходить робота.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Кожен агент на машині, в одній таблиці.**
Що він виконує, скільки коштує за останні 24 години і за весь час, коли його
востаннє бачили, хто ним володіє, і чи покриває підписка рахунок. Тут 14
агентів, 3 сесії працюють, 13 у спокої.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Програма показує, куди пішов час і гроші ходу, інструмент за інструментом.**
Один хід реальної сесії: 11 інструментів за 11.2 хвилини за $1.16. Кожен
виклик Bash і виклик моделі отримує власний стовпчик на часовій шкалі, тож
команду, що виконувалась 4.1 хвилини, і ту, що виконалась за 226мс, легко
відрізнити з першого погляду.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Програма оцінює роботу, а не лише витрати.**
Оцінка A цього тижня: 54 завдання виконано чисто, 2 складних коштували
$48.57, а прогони із занадто малою активністю для оцінки виключені з оцінки
замість того, щоб рахуватися перемогами. Кожен складний прогін посилається
на свій трейс.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Програма показує, чому контекстне вікно постійно заповнюється.**
715K з 1M-токенового вікна на останньому ході, пік 83.3%, 4 компактизації,
які всі спрацювали проактивно, а не через переповнення, і використання
кожного ходу за ними.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Виявлення працює без будь-яких налаштувань з вашого боку.**
Вбудовані детектори увімкнені одразу після встановлення: агент замовк,
потік телеметрії зупинився, сплеск вартості, сплеск токенів, зростання
кількості помилок, сплеск помилок, поріг бюджету, збіг із сигнатурою
загрози, знахідка інструменту безпеки, зміна стану безпеки. Ваші власні
правила — опціональні, поверх цього.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Затримка ризикованого виклику опціональна і вимкнена за замовчуванням.**
Рекурсивне видалення, примусовий пуш, sudo, секрети, встановлення пакетів
і вихідні виклики — для кожного є правило, яке можна увімкнути. Поки ви
цього не зробили, ClawMetry спостерігає і нічого не змінює. Щойно одне
увімкнено, відповідні виклики чекають тут (або на вашому телефоні) на
затвердження чи відхилення.

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
