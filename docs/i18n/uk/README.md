<!-- i18n-src:c99ac0512cae -->
> Українська translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Агент може зробити сотню викликів інструментів без жодного просування вперед.** ClawMetry
читає файли сесій, які ваші кодувальні агенти вже пишуть, і зводить разом таймлайн,
виклики інструментів та будь-які дані про токени й вартість, які розкриває середовище виконання, в одному
вигляді — щоб ви могли відрізнити довгий запуск, що працює, від того, що застряг.

Працює з **33 середовищами виконання AI-агентів** — Claude Code, OpenAI Codex, Hermes, OpenClaw та ще 29 інших. Одна панель для всього вашого флоту агентів. ([повний список](SUPPORTED_RUNTIMES.txt), згенерований з каталогу.)

> 🌐 **Читайте це мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [більше →](docs/i18n/)

Одна команда. Нуль налаштувань. Автоматично визначає все.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**. Нуль налаштувань: інструмент знаходить середовища виконання агентів,
які у вас вже є, читає їх у режимі лише читання і нічого не змінює в тому, як вони працюють.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Перед встановленням

| | |
|---|---|
| **Що він робить** | Читає файли сесій і журнали, які ваші агенти вже пишуть. Жодного SDK, жодних змін у коді, жодної інструментації у вашому застосунку. |
| **Що ви бачите** | Таймлайн сесії, покроковий відтворений перегляд інструментів, розбивку токенів і вартості, а також сигнали траєкторії (циклічність, повторювані збої) — для кожного середовища виконання. |
| **Що безкоштовно** | `pip install clawmetry` читає **OpenClaw, NVIDIA NemoClaw, Goose та Qwen Code** без облікового запису, ключа чи мережевого викликy. Решту 28 — Claude Code, Codex, Cursor та інші — читає закритий компаньйон `clawmetry-pro`, який надається з 7-денним пробним періодом або за планом — точний розподіл дивіться в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Як почати** | `pip install clawmetry && clawmetry`, потім відкрийте localhost:8900. Немає агентів на цій машині ще? `clawmetry --sample` відкриється з трьома позначеними синтетичними сесіями. |
| **Що залишає вашу машину** | Жодні дані сесій, якщо ви не запустите `clawmetry connect`. За замовчуванням виконуються дві речі, обидві можна вимкнути, і жодна не несе вмісту сесій: анонімний пінг установки та перевірка версії на PyPI. Кожне призначення занесено в опис у [docs/EGRESS.md](docs/EGRESS.md), відновлене на основі перехоплення трафіку, а не з читання коментарів. |

Два обмеження, про які варто знати перед тим, як оцінювати результат: середовища виконання розкривають дуже
різні дані (деякі не публікують вартість взагалі — [матриця](docs/compatibility.md)
показує, які саме, для кожного середовища виконання), а спостереження за дією не те саме, що здатність
її блокувати ([які засоби керування реальні, для кожного середовища виконання](docs/APPROVALS.md)).


## Працює з 33 середовищами виконання агентів

**Безкоштовно у застосунку з відкритим кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**На платному плані:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Кожне середовище виконання отримує однакову панель. Запускайте декілька одночасно, і перемикач
у заголовку перенацілить кожну вкладку на одне з них.

Створили власного агента на базі SDK замість цього? Інтерсептор відстежує і його виклики LLM
теж. Дивіться [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Що ви отримуєте

- **Сесії та транскрипти**: що робив кожен агент, крок за кроком, із відтворенням
- **Вартість і токени**: за середовищем виконання, моделлю, сесією та днем, з позначками аномалій
- **Потік (Flow)**: діаграма повідомлень у реальному часі, які проходять через канали, моделі та інструменти
- **Brain**: потік подій міркування та викликів інструментів у режимі реального часу
- **Переповнення контексту**: використання вікна з розміром під кожного провайдера, компактизація проти форсованого переповнення, плюс карта того, що ми *не можемо* бачити для кожного середовища виконання ([як](docs/CONTEXT_BLOWOUT.md))
- **Пам'ять і навички**: файли та навички, які фактично завантажило кожне середовище виконання
- **Здоров'я та журнали**: диск, пам'ять, частота помилок, обмеження швидкості, потік журналів у реальному часі
- **Сповіщення**: бюджетні обмеження, стрибки помилок, агент офлайн, маршрутизовані в Slack, Discord, PagerDuty, Telegram, Email
- **Погодження**: ставити на пауза ризиковані виклики інструментів *до* їх виконання та погоджувати з телефону ([як](docs/APPROVALS.md))

## Переповнення контексту та вартість спостереження

Два питання, на які варто відповісти перед тим, як довіряти будь-якому інструменту порівняння агентів.

**Як він обробляє переповнення контекстного вікна між різними середовищами виконання?**

Відсоток використання чесний настільки, наскільки чесне те, на що він ділить. ClawMetry
визначає розмір вікна для кожного провайдера з [таблиці, яку можна прочитати і
подати PR](clawmetry/context_windows.py), що охоплює Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama та GLM. Він не вимірює всі 33
середовища виконання однією лінійкою одного постачальника. Це важливо: хід на 300K токенів GPT-5,
оцінений за лінійкою Anthropic на 200K, читається як ">100%, переповнено", тоді як насправді це 75% від
400K для GPT-5. Та ж лінійка приховує справді переповнений хід DeepSeek на 130K
як комфортні 65%.

Кожне вікно постачається з власним походженням: `model_table`, `explicit_marker`,
`observed_floor`, або чесне `default`, коли ми не знаємо модель. Індикатор, побудований на припущенні,
ніколи не відображається з тим самим авторитетом, що й той, що побудований на
пошуку в таблиці.

ClawMetry може бачити події компактизації лише в деяких середовищах виконання. Тому
`GET /api/context-coverage` повідомляє, для кожного середовища виконання, чи означає нуль
"пройшло чисто", чи "ми не бачимо". Нуль, який насправді означає "не бачимо", так і повідомляється.
[Детальніше](docs/CONTEXT_BLOWOUT.md)

**Скільки коштує інструментація?**

| Шлях | Додано до вашого агента | За замовчуванням? |
|---|---|---|
| Читання файлів сесій (всі 33 середовища виконання) | **0**. Окремий процес, жодного коду ClawMetry у вашому агенті | увімкнено |
| HTTP-інтерсептор (`CLAWMETRY_INTERCEPT=1`) | **+0,44 мс** на кожен виклик LLM, або 0,009% від виклику на 5с | вимкнено |
| Хук перед інструментом (теплий кеш) | **+44 мс** на кожен контрольований виклик інструменту, понад базові 36 мс інтерпретатора | вимкнено |
| Проксі примусового виконання | **+9,7 мс** на кожен виклик LLM | вимкнено |

Вартість хост-демона: **2762 події/с** надходження, **710 байт/подію** на диску
(67,7 МБ на 100 тис. подій), і **~12% одного ядра** стабільно на завантаженій
установці. Останнє число перевищує наш власний заявлений бюджет 5-10%, тому воно
опубліковане як помилка для усунення, а не прибране зі сторінки.

Виміряно на Apple M2 Pro за допомогою `benchmarks/overhead.py`. Тестовий набір запускає
кожну умову в окремому процесі, чергує їхній порядок і **відмовляється
друкувати число, коли раунди не збігаються за знаком**. Запустіть його на своїй
машині за хвилину:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Вимірюється кожен шлях, включно з хуками перехоплення і проксі примусового виконання,
і тестовий набір запускається на Linux, macOS та Windows у CI. Два результати, про які варто
знати: проксі коштує приблизно в сім разів більше на Windows, ніж на Linux, і
демон наразі стабільно споживає близько 12% одного ядра, понад наш власний бюджет
5-10%. Необроблений JSON, методика та те, що ще не виміряно, знаходяться в
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Ціни

| План | Що покриває | Ціна |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, повна панель, лише локально | $0 |
| **Starter** | Усі інші середовища виконання вище, вигляд флоту, синхронізація з хмарою | $9 за вузол / місяць |
| **Pro** | Starter + контроль і оцінка: погодження, політики ризику інструментів, оцінки (evals), виявлення аномалій, оптимізатор вартості, експорт OTel, журнал аудиту, захищений від підробки | $19 за вузол / місяць |

Річні плани, Enterprise та актуальні ціни знаходяться на сторінці
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Самостійно розміщені ліцензійні
ключі працюють без хмари (`clawmetry license`). Точний розподіл безкоштовного/платного — в
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваші дані залишаються на вашій машині

ClawMetry читає локальні файли сесій і журнали. **Жодні дані сесій не залишають вашу машину,
якщо ви не запустите `clawmetry connect`** — жодних промптів, відповідей, аргументів інструментів, вмісту
файлів чи рядків журналу. Коли ви підключаєтеся, знімок шифрується наскрізним шифруванням
ключем, який ніколи не залишає вашу машину, і розшифровується у вашому браузері. Якщо у
вузла немає ключа, завантаження пропускається, а не надсилається у відкритому вигляді, і жодна
відповідь сервера не може це вимкнути.

Дві речі виконуються за замовчуванням до підключення, обидві можна вимкнути, і жодна не
несе дані сесій: анонімний пінг установки та перевірка версії на
PyPI. Стандартна установка також один раз шукає вашу публічну IP-адресу для рядка банера
при запуску. Кожне призначення, що воно несе та як його вимкнути, перелічено в
[docs/EGRESS.md](docs/EGRESS.md); самостійно розміщені, перенаправлені та ізольовані від мережі установки
не роблять жодних довільних вихідних викликів взагалі.

Розшифрування відбувається у вашому браузері, в коді, який ми вам надаємо. Раніше це було
обіцянкою; тепер це те, що можна перевірити. Кожен рядок, що торкається вашого ключа,
знаходиться в одному читабельному файлі, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
який постачається всередині wheel-пакета і подається без змін, закріплений хешем Subresource
Integrity. Щоб підтвердити, що браузер виконує те, що ми опублікували:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чого це не доводить: ми подаємо сторінку, яка завантажує файл, тож ми могли б
подати іншу сторінку. Хеші цілісності захищають вас від скомпрометованого CDN,
а не від постачальника. Що ви отримуєте — це те, що будь-яка підміна має бути
навмисною, видимою в джерелі сторінки, і відрізнятися від артефакту на PyPI,
який будь-хто може завантажити. Самостійне розміщення або робота лише локально повністю усуває
цю залежність.

## Встановлення

```bash
pip install clawmetry     # потім: clawmetry
```

Або однорядковий скрипт: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Потребує Python 3.8+ на macOS, Linux або Windows, та хоча б одне середовище виконання агента на
тій самій машині. Інструкції для Docker: [docs/DOCKER.md](docs/DOCKER.md).

Або дозвольте агенту налаштувати це за вас. Навичка [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
навчає Claude Code, Codex, Cursor, Gemini CLI, Copilot або OpenCode
встановлювати ClawMetry, повідомляти про те, що роблять і витрачають агенти на машині,
зупиняти одну сесію на запит і затримувати ризиковані виклики інструментів для погодження:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Документація

| | |
|---|---|
| [Сумісність середовищ виконання](docs/compatibility.md) | Що читає кожен адаптер, і як додати середовище виконання |
| [Переповнення контексту](docs/CONTEXT_BLOWOUT.md) | Вікна для кожного провайдера, компактизація проти переповнення, покриття для кожного середовища виконання |
| [Накладні витрати](docs/OVERHEAD.md) | Скільки коштує інструментація, вимірено, з тестовим набором для відтворення |
| [Права доступу (Entitlements)](docs/ENTITLEMENTS.md) | Безкоштовне проти платного, матриця рівнів, CLI ліцензій |
| [Погодження та політики](docs/APPROVALS.md) | Контроль перед виконанням, оцінка ризику, погодження з телефону |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Експортуйте трейси будь-куди, приймайте OTLP звідки завгодно |
| [Підключіть власного агента](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain наскрізно, з прикладами, що запускаються |
| [Відстеження SDK](docs/SDK_TRACKING.md) | Атрибуція вартості для агентів, які ви створили самостійно |
| [Чат-канали](docs/CHANNELS.md) | Адаптери чату, показані в Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Ізольовані (sandboxed) налаштування NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтування томів |
| [Архітектура](ARCHITECTURE.md) · [Розробка](docs/DEVELOPMENT.md) | Як це працює всередині; запуск із джерела |
| [Телеметрія](docs/TELEMETRY.md) | Анонімні пінги установки та відкриття на робочому столі, і як їх вимкнути |

## Скриншоти

Кожне число нижче взято з однієї реальної машини, у режимі лише читання, без жодних штучних даних.

**Він повідомляє, коли щось не так, а не лише те, що сталося.**
Два банери аномалій наверху: витрати, що перевищують середньодобові у 7 разів, та
стрибок вартості у 4,2 рази. Нижче — 324 з 667 останніх сесій несуть сигнал
марнотратства, з деталізацією за причинами.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Він показує, куди пішли гроші, у кожному періоді.**
$252,47 сьогодні, $513,15 цього тижня, $1312,92 цього місяця, кожне з токенами
за цим та тим, скільки з цього вже покриває ваша підписка. Нижче —
близько $1128/місяць, деталізовані як відновлювані, та $17 256/місяць вже заощаджені
завдяки повторному використанню кешу.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Він малює, як повідомлення перетворюється на відповідь.**
Діаграма потоку в реальному часі: ви, канал, яким воно надійшло, гейтвей, модель,
що відповідає прямо зараз, та кожен інструмент, до якого вона зверталася. Вузли
загоряються, коли робота проходить через них.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Кожен агент на машині, в одній таблиці.**
Що він виконує, скільки коштує за останні 24 години та за весь час, коли
його бачили останнього разу, хто ним володіє, і чи покриває рахунок підписка. 14 агентів тут,
3 сесії працюють, 13 тихі.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Він показує, куди пішов час і гроші одного ходу, інструмент за інструментом.**
Один хід реальної сесії: 11 інструментів за 11,2 хвилини за $1,16. Кожен виклик Bash
і виклик моделі отримує власну смужку на таймлайні, тож команда, яка працювала
4,1 хвилини, і та, що тривала 226 мс, помітні відразу.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Він оцінює роботу, а не лише витрати.**
Оцінка A цього тижня: 54 завдання виконано чисто, 2 проблемних коштували $48,57, а
запуски з надто малою активністю для оцінки виключені з оцінки, замість того,
щоб рахуватися як успіхи. Кожен проблемний запуск посилається на свій трейс.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Він показує, чому контекстне вікно продовжує заповнюватися.**
715 тис. з 1 млн токенів вікна на останньому ході, пік 83,3%, 4 компактизації,
усі з яких запустилися проактивно, а не через переповнення, та використання
кожного ходу за цим.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Виявлення працює без будь-яких налаштувань з вашого боку.**
Вбудовані детектори увімкнені з моменту встановлення: агент замовк, потік телеметрії
зупинився, стрибок вартості, спалах токенів, помилки зростають, спалах помилок, бюджетний
порог, збіг сигнатури загрози, знахідка інструменту безпеки, зміна стану безпеки.
Ваші власні правила додаються опційно поверх цього.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Затримка ризикованого виклику опційна і за замовчуванням вимкнена.**
Рекурсивне видалення, примусовий push, sudo, секрети, встановлення пакетів та вихідні
виклики — кожен має правило, яке можна увімкнути. Поки ви цього не зробите, ClawMetry
лише спостерігає і нічого не змінює. Коли одне увімкнено, відповідні виклики чекають тут
(або на вашому телефоні) на погодження чи відмову.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Більше, для кожного середовища виконання: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
