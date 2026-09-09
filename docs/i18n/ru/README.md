<!-- i18n-src:61beb8393e2f -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Агент может сделать сотню вызовов инструментов, так и не продвинувшись вперёд.** ClawMetry
читает файлы сессий, которые ваши кодирующие агенты уже пишут, и собирает в одном
представлении временную шкалу, вызовы инструментов и все данные о токенах и стоимости,
которые предоставляет runtime, — чтобы вы могли отличить долгий прогон, который работает,
от того, что застрял.

Работает с **30 рантаймами AI-агентов** — Claude Code, OpenAI Codex, Hermes, OpenClaw и ещё 26. Единая панель для всего вашего флота агентов. ([полный список](SUPPORTED_RUNTIMES.txt), сгенерирован из каталога.)

> 🌐 **Читать на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Нулевая настройка. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**. Никакой настройки: приложение находит
уже установленные у вас рантаймы агентов, читает их в режиме только для чтения и
никак не влияет на их работу.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Перед установкой

| | |
|---|---|
| **Что он делает** | Читает файлы сессий и логи, которые ваши агенты уже пишут. Никакого SDK, никаких изменений кода, никакой инструментации в вашем приложении. |
| **Что вы видите** | Временную шкалу сессии, пошаговый повтор вызовов инструментов, разбивку по токенам и стоимости, а также сигналы траектории (зацикливание, повторяющиеся сбои) — по каждому рантайму. |
| **Что бесплатно** | `pip install clawmetry` читает **OpenClaw, NVIDIA NemoClaw и Goose** без аккаунта, без ключа и без сетевых вызовов. Остальные 27 — Claude Code, Codex, Cursor и прочие — читаются закрытым модулем-компаньоном `clawmetry-pro`, который поставляется с 7-дневным пробным периодом или тарифом — точное разделение см. в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Как начать** | `pip install clawmetry && clawmetry`, затем откройте localhost:8900. Ещё нет агентов на этой машине? `clawmetry --sample` откроется с тремя размеченными синтетическими сессиями. |
| **Что покидает вашу машину** | Никакие данные сессий, если только вы не запустите `clawmetry connect`. По умолчанию выполняются две вещи, обе можно отключить, и ни одна не содержит содержимого сессий: анонимный пинг установки и проверка версии на PyPI. Каждый пункт назначения перечислен в [docs/EGRESS.md](docs/EGRESS.md), составлено на основе перехвата трафика, а не чтения комментариев в коде. |

Два ограничения стоит знать перед тем, как судить о результате: рантаймы предоставляют
очень разные данные (некоторые вообще не публикуют стоимость — [матрица](docs/compatibility.md)
показывает, какие именно, по каждому рантайму), и наблюдение за действием — не то же
самое, что возможность его заблокировать ([какие элементы управления реальны, по каждому рантайму](docs/APPROVALS.md)).


## Работает с 30 рантаймами агентов

**Бесплатно в приложении с открытым исходным кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**На платном тарифе:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

У каждого рантайма одна и та же панель. Запустите несколько сразу — переключатель
в шапке перенастраивает каждую вкладку на выбранный.

Собрали своего агента на базе SDK, а не готового рантайма? Перехватчик отслеживает
и его вызовы LLM тоже. См. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Что вы получаете

- **Сессии и транскрипты**: что делал каждый агент, ход за ходом, с повтором
- **Стоимость и токены**: по рантайму, модели, сессии и дню, с флагами аномалий
- **Flow**: живая диаграмма движения сообщений через каналы, модели и инструменты
- **Brain**: поток событий рассуждений и вызовов инструментов в реальном времени
- **Переполнение контекста**: заполненность окна, рассчитанная по провайдеру, сжатие vs. вынужденное переполнение, плюс карта того, что мы *не можем* увидеть по каждому рантайму ([как](docs/CONTEXT_BLOWOUT.md))
- **Память и навыки**: файлы и навыки, которые фактически загрузил каждый рантайм
- **Здоровье и логи**: диск, память, частота ошибок, лимиты запросов, живой поток логов
- **Алерты**: лимиты бюджета, всплески ошибок, оффлайн-агент, доставка в Slack, Discord, PagerDuty, Telegram, Email
- **Подтверждения**: приостановка рискованных вызовов инструментов *до* их выполнения и подтверждение с телефона ([как](docs/APPROVALS.md))

## Переполнение контекста и во что обходится наблюдение

Два вопроса, на которые стоит ответить, прежде чем доверять любому инструменту сравнения агентов.

**Как это обрабатывает переполнение контекстного окна между рантаймами?**

Процент заполненности честен ровно настолько, насколько честен делитель. ClawMetry
рассчитывает размер окна по каждому провайдеру из [таблицы, которую можно прочитать и
предложить PR](clawmetry/context_windows.py), охватывающей Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama и GLM. Он не измеряет все 30 рантаймов одной
линейкой одного вендора. Это важно: ход на 300K токенов GPT-5, оценённый по линейке
Anthropic в 200K, читается как ">100%, переполнено", хотя на деле это 75% от 400K
у GPT-5. Та же линейка скрывает реально переполненный ход DeepSeek на 130K токенов
как комфортные 65%.

Каждое окно поставляется с указанием происхождения: `model_table`, `explicit_marker`,
`observed_floor` или честный `default`, когда модель неизвестна. Индикатор, построенный
на догадке, никогда не отображается с той же достоверностью, что и построенный на
справочной таблице.

ClawMetry может видеть события сжатия только у некоторых рантаймов. Поэтому
`GET /api/context-coverage` сообщает по каждому рантайму, означает ли **ноль
"прошло чисто" или "мы не видим"**. Ноль, который на самом деле означает "не видим",
так и помечается.
[Подробности](docs/CONTEXT_BLOWOUT.md)

**Во что обходится инструментация?**

| Путь | Добавляется к вашему агенту | По умолчанию? |
|---|---|---|
| Чтение файлов сессий (все 30 рантаймов) | **0**. Отдельный процесс, никакого кода ClawMetry в вашем агенте | включено |
| HTTP-перехватчик (`CLAWMETRY_INTERCEPT=1`) | **+0.44 мс** на вызов LLM, или 0.009% от вызова длиной 5 с | выключено |
| Pre-tool хук-шлюз (тёплый кэш) | **+44 мс** на каждый перехваченный вызов инструмента, сверх базовых 36 мс на запуск интерпретатора | выключено |
| Прокси принудительного контроля | **+9.7 мс** на вызов LLM | выключено |

Стоимость для хоста демона: **2 762 события/сек** на приём, **710 байт/событие** на
диске (67.7 МБ на 100 тыс. событий) и **~12% одного ядра** в устойчивом режиме на
загруженной установке. Последнее число превышает наш собственный бюджет в 5-10%,
поэтому оно опубликовано как баг, который предстоит устранить, а не скрыто со страницы.

Измерено на Apple M2 Pro с помощью `benchmarks/overhead.py`. Стенд запускает каждое
условие в отдельном процессе, чередует их порядок и **отказывается печатать число,
если раунды расходятся по знаку**. Запустите его на своей машине за минуту:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Измеряется каждый путь, включая хук-шлюзы и прокси принудительного контроля,
и стенд запускается в CI на Linux, macOS и Windows. Стоит знать два результата:
прокси на Windows обходится примерно в семь раз дороже, чем на Linux, а демон
сейчас устойчиво занимает около 12% одного ядра, сверх нашего же бюджета в 5-10%.
Необработанный JSON, методика и то, что пока не измерено, — в
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Цены

| Тариф | Что покрывает | Цена |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, полная панель, только локально | $0 |
| **Starter** | Все остальные рантаймы выше, обзор флота, облачная синхронизация | $9 за узел / месяц |
| **Pro** | Starter + управление и оценка: подтверждения, политики риска инструментов, evals, обнаружение аномалий, оптимизатор затрат, экспорт в OTel, защищённый от подделки журнал аудита | $19 за узел / месяц |

Годовые тарифы, Enterprise и актуальные цены — на
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключи лицензии для
самостоятельного хостинга работают без облака (`clawmetry license`). Точное
разделение бесплатного и платного — в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваши данные остаются на вашей машине

ClawMetry читает локальные файлы сессий и логи. **Никакие данные сессий не покидают
вашу машину, если вы не запустите `clawmetry connect`** — ни промпты, ни ответы, ни
аргументы инструментов, ни содержимое файлов, ни строки логов. Когда вы подключаетесь,
снимок данных шифруется сквозным шифрованием с ключом, который никогда не покидает
вашу машину, и расшифровывается в вашем браузере. Если у узла нет ключа, загрузка
пропускается, а не отправляется в открытом виде, и никакой ответ сервера не может это
отключить.

По умолчанию до подключения выполняются две вещи, обе можно отключить, и ни одна не
несёт данных сессии: анонимный пинг установки и проверка версии на PyPI. Установка
по умолчанию также один раз запрашивает ваш публичный IP для строки баннера при
запуске. Каждый пункт назначения, что он передаёт и как его отключить, перечислено в
[docs/EGRESS.md](docs/EGRESS.md); самостоятельно хостящиеся, перенаправленные и
изолированные от сети установки вообще не делают исходящих вызовов по своей инициативе.

Расшифровка происходит в вашем браузере, в коде, который мы вам предоставляем. Раньше
это было обещанием; теперь это можно проверить. Каждая строка, которая касается вашего
ключа, находится в одном читаемом файле, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
который поставляется внутри wheel-пакета и отдаётся дословно, закреплённый хешем
Subresource Integrity. Чтобы убедиться, что браузер выполняет то, что мы опубликовали:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чего это не доказывает: мы отдаём страницу, которая загружает файл, а значит могли бы
отдать другую страницу. Хеши целостности защищают вас от скомпрометированного CDN, но
не от самого вендора. Что вы получаете — это то, что любая подмена должна быть
намеренной, видимой в исходном коде страницы и отличаться от артефакта на PyPI,
который может проверить кто угодно. Самостоятельный хостинг или работа только локально
полностью убирает эту зависимость.

## Установка

```bash
pip install clawmetry     # затем: clawmetry
```

Или однострочник: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Требуется Python 3.8+ на macOS, Linux или Windows и хотя бы один рантайм агента на
этой же машине. Инструкции по Docker: [docs/DOCKER.md](docs/DOCKER.md).

Или пусть агент настроит всё за вас. Навык [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
учит Claude Code, Codex, Cursor, Gemini CLI, Copilot или OpenCode устанавливать
ClawMetry, сообщать, что делают и сколько тратят агенты на машине, останавливать
одну сессию по запросу и приостанавливать рискованные вызовы инструментов до
подтверждения:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Документация

| | |
|---|---|
| [Совместимость рантаймов](docs/compatibility.md) | Что читает каждый адаптер и как добавить рантайм |
| [Переполнение контекста](docs/CONTEXT_BLOWOUT.md) | Окна по каждому провайдеру, сжатие vs. переполнение, покрытие по рантаймам |
| [Издержки](docs/OVERHEAD.md) | Во что обходится инструментация, измерено, со стендом для воспроизведения |
| [Права доступа](docs/ENTITLEMENTS.md) | Бесплатное vs. платное, матрица тарифов, CLI лицензии |
| [Подтверждения и политики](docs/APPROVALS.md) | Проверка перед выполнением, оценка риска, подтверждения с телефона |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Экспорт трасс куда угодно, приём OTLP откуда угодно |
| [Подключите своего агента](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain от начала до конца, с рабочими примерами |
| [Отслеживание через SDK](docs/SDK_TRACKING.md) | Учёт стоимости для агентов, которых вы собрали сами |
| [Чат-каналы](docs/CHANNELS.md) | Адаптеры чатов, отображаемые во Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Изолированные (sandboxed) настройки NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтирование томов |
| [Архитектура](ARCHITECTURE.md) · [Разработка](docs/DEVELOPMENT.md) | Как это устроено внутри; запуск из исходников |
| [Телеметрия](docs/TELEMETRY.md) | Анонимные пинги установки и открытия десктоп-приложения и как их отключить |

## Скриншоты

Каждая цифра ниже — с одной реальной машины, в режиме только для чтения, без какой-либо
подготовки данных.

**Показывает, когда что-то пошло не так, а не только что произошло.**
Два баннера аномалий сверху: расходы, идущие в 7 раз выше среднедневного уровня, и
всплеск стоимости в 4.2 раза. Под ними — 324 из 667 последних сессий с сигналом
о неэффективных тратах, с разбивкой по причинам.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Показывает, куда ушли деньги, за любой период.**
$252.47 сегодня, $513.15 за эту неделю, $1,312.92 за этот месяц, с указанием
стоящих за этим токенов и того, сколько из этого уже покрывает ваша подписка.
Ниже — около $1,128/мес, помеченных как возвратные, и уже сэкономленные $17,256/мес
за счёт повторного использования кэша.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Показывает, как сообщение превращается в ответ.**
Живая диаграмма потока: вы, канал, через который пришло сообщение, шлюз, модель,
отвечающая прямо сейчас, и каждый инструмент, к которому она обратилась. Узлы
загораются по мере прохождения работы через них.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Каждый агент на машине — в одной таблице.**
Что он запускает, сколько стоит за последние 24 часа и за всё время, когда его
видели в последний раз, кто им владеет и покрывает ли счёт подписка. 14 агентов
здесь, 3 сессии в работе, 13 в покое.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Показывает, куда ушли время и деньги хода, инструмент за инструментом.**
Один ход реальной сессии: 11 инструментов за 11.2 минуты за $1.16. Каждый вызов
Bash и вызов модели получает свою полосу на временной шкале, так что вызов,
длившийся 4.1 минуты, и вызов, занявший 226 мс, различимы с первого взгляда.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Оценивает работу, а не только расходы.**
Оценка A за эту неделю: 54 задачи выполнены чисто, 2 сложных обошлись в $48.57,
а прогоны со слишком малой активностью для оценки исключаются из оценки, вместо
того чтобы засчитываться как успех. Каждый сложный прогон ведёт к своей трассе.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Показывает, почему контекстное окно продолжает заполняться.**
715K из 1M-токенного окна на последнем ходу, пик 83.3%, 4 сжатия, все сработавшие
превентивно, а не из-за переполнения, и заполненность каждого хода за этим стоящего.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Обнаружение работает без какой-либо настройки с вашей стороны.**
Встроенные детекторы включены с момента установки: агент замолчал, поток
телеметрии остановился, всплеск стоимости, всплеск токенов, растущие ошибки,
резкий скачок ошибок, порог бюджета, совпадение с сигнатурой угрозы, находка
инструмента безопасности, изменение уровня защищённости. Собственные правила —
опциональное дополнение поверх них.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Приостановка рискованного вызова — опциональна и по умолчанию выключена.**
Рекурсивные удаления, принудительные push, sudo, секреты, установка пакетов и
исходящие вызовы — для каждого своё правило, которое можно включить. Пока вы
этого не сделали, ClawMetry только наблюдает и ничего не меняет. Как только
правило включено, подходящие вызовы ждут здесь (или на вашем телефоне)
подтверждения или отклонения.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Больше скриншотов по каждому рантайму: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Признание

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## История звёзд

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## Лицензия

MIT · Создано [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
