<!-- i18n-src:12b97259721e -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**Агент может сделать сотню вызовов инструментов и не продвинуться ни на шаг.** ClawMetry
читает файлы сессий, которые ваши кодирующие агенты уже пишут, и собирает таймлайн,
вызовы инструментов и любые данные о токенах и стоимости, которые предоставляет среда выполнения, в одном
представлении — так вы можете отличить долгий запуск, который работает, от того, который застрял.

Работает с **31 средой выполнения ИИ-агентов** — Claude Code, OpenAI Codex, Hermes, OpenClaw и ещё 27. Единая панель для всего вашего парка агентов. ([полный список](SUPPORTED_RUNTIMES.txt), сгенерирован из каталога.)

> 🌐 **Читайте на:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Никакой настройки. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**. Никакой настройки: приложение находит уже установленные у вас
среды выполнения агентов, читает их в режиме «только чтение» и никак не меняет их работу.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Перед установкой

| | |
|---|---|
| **Что делает** | Читает файлы сессий и логи, которые ваши агенты уже пишут. Никакого SDK, никаких изменений в коде, никакой инструментации в вашем приложении. |
| **Что вы увидите** | Таймлайн сессии, пошаговый повтор инструментов, разбивку по токенам и стоимости, а также сигналы траектории (зацикливание, повторяющиеся сбои) — по каждой среде выполнения. |
| **Что бесплатно** | `pip install clawmetry` читает **OpenClaw, NVIDIA NemoClaw и Goose** без аккаунта, ключа и сетевых обращений. Остальные 27 — Claude Code, Codex, Cursor и другие — читаются закрытым компаньоном `clawmetry-pro`, который доступен с 7-дневным пробным периодом или по тарифу — точное разделение см. в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Как начать** | `pip install clawmetry && clawmetry`, затем откройте localhost:8900. Ещё нет агентов на этой машине? `clawmetry --sample` откроется с тремя размеченными синтетическими сессиями. |
| **Что покидает вашу машину** | Никакие данные сессий, если вы не запустите `clawmetry connect`. По умолчанию выполняются два действия, оба можно отключить, и ни одно не передаёт содержимое сессий: анонимный пинг об установке и проверка версии на PyPI. Каждый пункт назначения перечислен в [docs/EGRESS.md](docs/EGRESS.md), составлено на основе перехвата трафика, а не чтения комментариев в коде. |

Стоит знать два ограничения, прежде чем оценивать результат: среды выполнения предоставляют очень
разные данные (некоторые вообще не публикуют стоимость — [таблица совместимости](docs/compatibility.md)
показывает, какие именно, по каждой среде выполнения), и наблюдение за действием не то же самое, что возможность
заблокировать его ([какие элементы управления реально работают, по каждой среде выполнения](docs/APPROVALS.md)).


## Работает с 31 средой выполнения агентов

**Бесплатно в open source приложении:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**По платному тарифу:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Каждая среда выполнения получает одну и ту же панель. Запустите несколько одновременно, и
переключатель в шапке будет перенастраивать каждую вкладку на выбранную из них.

Собрали собственного агента на базе SDK? Перехватчик отслеживает и его вызовы LLM
тоже. См. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Что вы получаете

- **Сессии и транскрипты**: что делал каждый агент, ход за ходом, с повтором
- **Стоимость и токены**: по среде выполнения, модели, сессии и дню, с флагами аномалий
- **Flow**: живая диаграмма сообщений, проходящих через каналы, модели и инструменты
- **Brain**: поток событий рассуждений и вызовов инструментов в реальном времени
- **Переполнение контекста**: использование окна, рассчитанное для каждого провайдера, сжатие против принудительного переполнения, а также карта того, что мы *не можем* видеть по каждой среде выполнения ([как](docs/CONTEXT_BLOWOUT.md))
- **Память и навыки**: файлы и навыки, которые реально загружала каждая среда выполнения
- **Здоровье и логи**: диск, память, частота ошибок, лимиты запросов, живой поток логов
- **Оповещения**: лимиты бюджета, всплески ошибок, агент офлайн, доставка в Slack, Discord, PagerDuty, Telegram, Email
- **Подтверждения**: приостановка рискованных вызовов инструментов *до* их выполнения и подтверждение с телефона ([как](docs/APPROVALS.md))

## Переполнение контекста и цена наблюдения

Два вопроса, на которые стоит ответить, прежде чем доверять любому инструменту сравнения агентов.

**Как обрабатывается переполнение контекстного окна между разными средами выполнения?**

Процент использования честен ровно настолько, насколько честен знаменатель, на который его делят. ClawMetry
подбирает размер окна для каждого провайдера по [таблице, которую можно прочитать и
отправить PR](clawmetry/context_windows.py), охватывающей Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama и GLM. Инструмент не измеряет все 31 среду выполнения
линейкой одного вендора. Это важно: ход на 300K токенов в GPT-5, оценённый по линейке
Anthropic в 200K, читается как ">100%, переполнено", хотя на самом деле это 75% от
400K у GPT-5. Та же линейка скрывает реально переполненный ход на 130K в DeepSeek,
показывая комфортные 65%.

Каждое окно поставляется со своим происхождением: `model_table`, `explicit_marker`,
`observed_floor` или честный `default`, когда модель неизвестна. Индикатор, построенный на
догадке, никогда не отображается с тем же уровнем достоверности, что и построенный на
таблице соответствий.

ClawMetry может видеть события сжатия только у части сред выполнения. Поэтому
`GET /api/context-coverage` сообщает по каждой среде выполнения, означает ли **ноль
«прошло чисто» или «мы не видим»**. Ноль, который на самом деле означает слепоту, так и говорит.
[Подробнее](docs/CONTEXT_BLOWOUT.md)

**Сколько стоит инструментация?**

| Путь | Добавлено к вашему агенту | По умолчанию? |
|---|---|---|
| Чтение файлов сессий (все 31 среды выполнения) | **0**. Отдельный процесс, никакого кода ClawMetry в вашем агенте | включено |
| HTTP-перехватчик (`CLAWMETRY_INTERCEPT=1`) | **+0.44 мс** на вызов LLM, или 0.009% от вызова длительностью 5 с | выключено |
| Шлюз хука до вызова инструмента (тёплый кэш) | **+44 мс** на каждый перехваченный вызов инструмента, сверх базового порога интерпретатора в 36 мс | выключено |
| Прокси принудительного применения | **+9.7 мс** на вызов LLM | выключено |

Стоимость для хоста демона: **2762 события/с** при приёме, **710 байт/событие** на диске
(67.7 МБ на 100 тыс. событий) и **~12% одного ядра** в устойчивом режиме на активной
установке. Последнее значение превышает заявленный нами бюджет в 5-10%, поэтому оно
опубликовано как баг, который предстоит исправить, а не скрыто со страницы.

Измерено на Apple M2 Pro с помощью `benchmarks/overhead.py`. Стенд запускает
каждое условие в отдельном процессе, чередует их порядок и **отказывается печатать
число, если раунды расходятся в его знаке**. Запустите его на своей машине за минуту:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Измерен каждый путь, включая шлюзы хуков и прокси принудительного применения,
и стенд работает на Linux, macOS и Windows в CI. Стоит знать два результата: прокси
стоит примерно в семь раз дороже на Windows, чем на Linux, а демон в настоящее время
устойчиво потребляет около 12% одного ядра, что превышает наш собственный бюджет
в 5-10%. Необработанные данные JSON, методика и то, что пока не измерено, находятся в
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Тарифы

| Тариф | Что включено | Цена |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, полная панель, только локально | $0 |
| **Starter** | Все остальные среды выполнения из списка выше, обзор парка, облачная синхронизация | $9 за узел / месяц |
| **Pro** | Starter + управление и оценка: подтверждения, политики риска инструментов, оценки (evals), обнаружение аномалий, оптимизатор затрат, экспорт OTel, защищённый от подделки журнал аудита | $19 за узел / месяц |

Годовые тарифы, Enterprise и актуальные цены — на странице
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключи лицензии для
самостоятельного хостинга работают без облака (`clawmetry license`). Точное разделение
бесплатного и платного — в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваши данные остаются на вашей машине

ClawMetry читает локальные файлы сессий и логи. **Никакие данные сессий не покидают вашу
машину, если вы не запустите `clawmetry connect`** — ни подсказки, ни ответы, ни аргументы
инструментов, ни содержимое файлов, ни строки логов. Когда вы всё же подключаетесь, снимок
данных шифруется end-to-end ключом, который никогда не покидает вашу машину, и расшифровывается
в вашем браузере. Если у узла нет ключа, загрузка пропускается, а не отправляется в открытом
виде, и никакой ответ сервера не может это отключить.

По умолчанию до подключения выполняются две вещи, обе можно отключить, и ни одна не
передаёт данные сессий: анонимный пинг об установке и проверка версии на PyPI. Установка по
умолчанию также один раз запрашивает ваш публичный IP для строки баннера при запуске. Каждый
пункт назначения, что он передаёт и как его отключить, перечислены в
[docs/EGRESS.md](docs/EGRESS.md); установки с самостоятельным хостингом, изменённым адресом
назначения и изолированные от сети не выполняют никаких необязательных исходящих вызовов вовсе.

Расшифровка происходит в вашем браузере, в коде, который мы вам предоставляем. Раньше это было
просто обещанием; теперь это можно проверить. Каждая строка, которая касается вашего ключа,
находится в одном читаемом файле, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
который поставляется внутри wheel-пакета и отдаётся дословно, закреплённый хэшем Subresource
Integrity. Чтобы убедиться, что браузер выполняет именно то, что мы опубликовали:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чего это не доказывает: мы сами отдаём страницу, которая загружает этот файл, а значит могли бы
отдать другую страницу. Хэши целостности защищают вас от скомпрометированного CDN, но не от
вендора. Что вы получаете — это то, что любая подмена должна быть преднамеренной, видимой в
исходном коде страницы и отличаться от артефакта на PyPI, который может получить кто угодно.
Самостоятельный хостинг или работа только локально полностью устраняет эту зависимость.

## Установка

```bash
pip install clawmetry     # затем: clawmetry
```

Или однострочник: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Требуется Python 3.8+ на macOS, Linux или Windows, и хотя бы одна среда выполнения агента на
той же машине. Инструкции по Docker: [docs/DOCKER.md](docs/DOCKER.md).

Или позвольте агенту настроить всё за вас. Навык [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
учит Claude Code, Codex, Cursor, Gemini CLI, Copilot или OpenCode устанавливать ClawMetry,
сообщать, что делают и сколько тратят агенты на машине, останавливать сессию по запросу и
удерживать рискованные вызовы инструментов для подтверждения:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Документация

| | |
|---|---|
| [Совместимость сред выполнения](docs/compatibility.md) | Что читает каждый адаптер и как добавить среду выполнения |
| [Переполнение контекста](docs/CONTEXT_BLOWOUT.md) | Окна для каждого провайдера, сжатие против переполнения, покрытие по средам выполнения |
| [Накладные расходы](docs/OVERHEAD.md) | Сколько стоит инструментация, измерено, со стендом для воспроизведения |
| [Права доступа](docs/ENTITLEMENTS.md) | Бесплатное против платного, матрица тарифов, CLI для лицензий |
| [Подтверждения и политики](docs/APPROVALS.md) | Проверка перед выполнением, оценка риска, подтверждения с телефона |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Экспорт трасс куда угодно, приём OTLP откуда угодно |
| [Подключите своего агента](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain от начала до конца, с рабочими примерами |
| [Отслеживание через SDK](docs/SDK_TRACKING.md) | Атрибуция стоимости для агентов, которых вы создали сами |
| [Чат-каналы](docs/CHANNELS.md) | Адаптеры чатов, показанные во Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Изолированные (sandboxed) настройки NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтирование томов |
| [Архитектура](ARCHITECTURE.md) · [Разработка](docs/DEVELOPMENT.md) | Как всё устроено внутри; запуск из исходников |
| [Телеметрия](docs/TELEMETRY.md) | Анонимные пинги при установке и открытии десктопного приложения, и как их отключить |

## Скриншоты

Каждое число ниже — с одной реальной машины, в режиме «только чтение», без каких-либо подготовленных данных.

**Инструмент сообщает, когда что-то не так, а не просто что произошло.**
Два баннера аномалий вверху: расходы идут в 7 раз выше среднего дневного показателя и
всплеск стоимости в 4.2 раза. Ниже — 324 из 667 недавних сессий с признаком потерь,
разбитые по причинам.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Инструмент показывает, куда ушли деньги, за любой период.**
$252.47 сегодня, $513.15 за эту неделю, $1312.92 за этот месяц, с указанием токенов
за этим и того, сколько из этого уже покрывает ваша подписка. Ниже — около $1128/мес
отмечено как то, что можно сэкономить, и $17256/мес уже сэкономлено за счёт повторного
использования кэша.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Инструмент показывает, как сообщение превращается в ответ.**
Живая диаграмма потока: вы, канал, по которому пришло сообщение, шлюз, модель,
отвечающая прямо сейчас, и каждый инструмент, к которому она обращалась. Узлы
подсвечиваются по мере прохождения работы через них.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Каждый агент на машине — в одной таблице.**
Что запущено, сколько это стоило за последние 24 часа и за всё время, когда его видели
в последний раз, кому он принадлежит и покрывает ли счёт подписка. Здесь 14 агентов,
3 сессии работают, 13 неактивны.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Инструмент показывает, куда ушли время и деньги хода, по каждому инструменту.**
Один ход реальной сессии: 11 инструментов за 11.2 минуты за $1.16. Каждый вызов Bash
и каждый вызов модели получает свою полосу на таймлайне, так что команда, выполнявшаяся
4.1 минуты, и та, что выполнялась 226 мс, различимы с первого взгляда.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Инструмент оценивает работу, а не только расходы.**
Оценка A за эту неделю: 54 задачи выполнены чисто, 2 проблемных стоили $48.57, а
запуски со слишком малой активностью для оценки исключаются из итоговой оценки, а не
засчитываются как успех. Каждый проблемный запуск ведёт к своей трассе.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Инструмент показывает, почему контекстное окно продолжает заполняться.**
715K из 1M-токенного окна на последнем ходу, пик 83.3%, 4 сжатия, все сработали
проактивно, а не из-за переполнения, а также использование каждого предшествующего хода.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Обнаружение работает без какой-либо настройки с вашей стороны.**
Встроенные детекторы включены с момента установки: агент замолчал, поток телеметрии
остановился, всплеск стоимости, всплеск токенов, растущее число ошибок, скачок ошибок,
порог бюджета, совпадение сигнатуры угрозы, находка инструмента безопасности, изменение
состояния безопасности. Собственные правила — опциональное дополнение поверх этого.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Удержание рискованного вызова — опционально и отключено по умолчанию.**
Рекурсивное удаление, принудительный push, sudo, секреты, установка пакетов и исходящие
вызовы — для каждого можно включить своё правило. Пока вы этого не сделали, ClawMetry
наблюдает и ничего не меняет. Как только правило включено, совпадающие вызовы ждут здесь
(или на вашем телефоне) подтверждения или отклонения.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Больше — по каждой среде выполнения: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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

MIT · Разработано [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
