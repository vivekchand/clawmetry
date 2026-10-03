<!-- i18n-src:c99ac0512cae -->
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
читает файлы сессий, которые ваши кодирующие агенты уже пишут, и собирает в одном
представлении таймлайн, вызовы инструментов и те данные о токенах и стоимости,
которые раскрывает рантайм, чтобы вы могли отличить длительный прогон, который
работает, от того, что застрял.

Работает с **33 рантаймами ИИ-агентов** — Claude Code, OpenAI Codex, Hermes, OpenClaw и ещё 29. Одна панель для всего вашего парка агентов. ([полный список](SUPPORTED_RUNTIMES.txt), сгенерированный из каталога.)

> 🌐 **Читать на:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Без настройки. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**. Без настройки: ClawMetry находит
уже установленные у вас рантаймы агентов, читает их в режиме «только чтение» и
никак не меняет их работу.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Прежде чем устанавливать

| | |
|---|---|
| **Что делает** | Читает файлы сессий и логи, которые ваши агенты уже пишут. Никакого SDK, никаких изменений кода, никакой инструментации в вашем приложении. |
| **Что вы увидите** | Таймлайн сессии, пошаговый повтор вызовов инструментов, разбивку по токенам и стоимости, а также сигналы о траектории (зацикливание, повторяющиеся сбои) — для каждого рантайма. |
| **Что бесплатно** | `pip install clawmetry` читает **OpenClaw, NVIDIA NemoClaw, Goose и Qwen Code** без аккаунта, без ключа и без сетевых запросов. Остальные 28 — Claude Code, Codex, Cursor и прочие — читаются закрытым модулем `clawmetry-pro`, который доступен с 7-дневной пробной версией или по тарифу — точное разделение см. в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md). |
| **Как начать** | `pip install clawmetry && clawmetry`, затем откройте localhost:8900. Ещё нет агентов на этой машине? `clawmetry --sample` откроется с тремя помеченными синтетическими сессиями. |
| **Что покидает вашу машину** | Никакие данные сессий, если вы не запустите `clawmetry connect`. По умолчанию выполняются две вещи, обе можно отключить, и ни одна не содержит содержимого сессий: анонимный пинг установки и проверка версии на PyPI. Каждое направление перечислено в [docs/EGRESS.md](docs/EGRESS.md), составлено заново по перехвату трафика, а не по комментариям в коде. |

Прежде чем оценивать результат, стоит учесть два ограничения: рантаймы раскрывают
очень разные данные (некоторые вообще не публикуют стоимость — [таблица](docs/compatibility.md)
указывает, какие именно, для каждого рантайма), и возможность наблюдать за действием
не то же самое, что возможность его заблокировать ([какие элементы управления реальны, по рантаймам](docs/APPROVALS.md)).


## Работает с 33 рантаймами агентов

**Бесплатно в open source приложении:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**По платному тарифу:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Каждый рантайм получает одну и ту же панель. Запустите несколько одновременно,
и переключатель в шапке перенастроит каждую вкладку на нужный из них.

Собрали своего агента на базе SDK вместо готового рантайма? Перехватчик отслеживает
и его вызовы LLM тоже. См. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Что вы получаете

- **Сессии и транскрипты**: что делал каждый агент, шаг за шагом, с повтором
- **Стоимость и токены**: по рантайму, модели, сессии и дню, с пометками аномалий
- **Flow**: живая диаграмма сообщений, проходящих через каналы, модели и инструменты
- **Brain**: поток событий рассуждений и вызовов инструментов в реальном времени
- **Переполнение контекста**: утилизация окна, рассчитанная по провайдеру, компактизация в сравнении с принудительным переполнением, плюс карта того, чего мы *не видим* по каждому рантайму ([как](docs/CONTEXT_BLOWOUT.md))
- **Память и навыки**: файлы и навыки, которые реально загрузил каждый рантайм
- **Здоровье и логи**: диск, память, частота ошибок, лимиты скорости, живой поток логов
- **Оповещения**: лимиты бюджета, всплески ошибок, выход агента офлайн, маршрутизация в Slack, Discord, PagerDuty, Telegram, Email
- **Подтверждения**: приостановка рискованных вызовов инструментов *перед* их выполнением и подтверждение с телефона ([как](docs/APPROVALS.md))

## Переполнение контекста и во что обходится наблюдение

Два вопроса, на которые стоит ответить, прежде чем доверять любому инструменту сравнения агентов.

**Как это работает с переполнением контекстного окна между разными рантаймами?**

Процент утилизации честен ровно настолько, насколько честен знаменатель. ClawMetry
определяет размер окна по провайдеру из [таблицы, которую можно прочитать и
предложить PR](clawmetry/context_windows.py), охватывающей Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama и GLM. Она не измеряет все 33
рантайма одной линейкой одного вендора. Это важно: ход на 300K токенов у GPT-5,
оценённый по линейке Anthropic на 200K, читается как ">100%, переполнено", хотя
на деле это 75% от 400K у GPT-5. Та же линейка маскирует реально переполненный
ход DeepSeek на 130K как комфортные 65%.

Каждое окно поставляется с указанием происхождения данных: `model_table`, `explicit_marker`,
`observed_floor` или честный `default`, когда модель неизвестна. Индикатор,
построенный на догадке, никогда не отображается с той же достоверностью, что и
построенный на справочной таблице.

ClawMetry может видеть события компактизации только на некоторых рантаймах. Поэтому
`GET /api/context-coverage` сообщает по каждому рантайму, означает ли **ноль
«прошло чисто» или «мы слепы»**. Ноль, который на самом деле означает «слепота»,
так и помечается. [Подробнее](docs/CONTEXT_BLOWOUT.md)

**Во что обходится инструментация?**

| Путь | Добавлено к вашему агенту | По умолчанию? |
|---|---|---|
| Чтение файлов сессий «хвостом» (все 33 рантайма) | **0**. Отдельный процесс, кода ClawMetry в вашем агенте нет | включено |
| HTTP-перехватчик (`CLAWMETRY_INTERCEPT=1`) | **+0,44 мс** на вызов LLM, или 0,009% от 5-секундного вызова | выключено |
| Шлюз pre-tool хука (тёплый кэш) | **+44 мс** на вызов инструмента под контролем, сверх базовых 36 мс интерпретатора | выключено |
| Прокси принудительного применения | **+9,7 мс** на вызов LLM | выключено |

Стоимость для хоста демона: приём **2762 событий/сек**, **710 байт/событие** на
диске (67,7 МБ на 100 тыс. событий) и **~12% одного ядра** в устойчивом режиме
при активной установке. Последняя цифра превышает наш собственный заявленный
бюджет в 5-10%, поэтому она опубликована как баг, который нужно устранить, а
не скрыта со страницы.

Измерено на Apple M2 Pro с помощью `benchmarks/overhead.py`. Инструмент запускает
каждый сценарий в отдельном процессе, чередует их порядок и **отказывается
печатать число, если раунды расходятся в знаке**. Запустите его на своей машине
за минуту:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Измеряется каждый путь, включая шлюзы хуков и прокси принудительного применения,
и инструмент запускается в CI на Linux, macOS и Windows. Два результата, о которых
стоит знать: прокси стоит примерно в семь раз дороже на Windows, чем на Linux, а
демон сейчас устойчиво потребляет около 12% одного ядра, сверх нашего собственного
бюджета в 5-10%. Необработанный JSON, методика и то, что пока не измерено,
находятся в [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Цены

| Тариф | Что включает | Цена |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code, полная панель, только локально | $0 |
| **Starter** | Все остальные рантаймы выше, представление парка, облачная синхронизация | $9 за узел / месяц |
| **Pro** | Starter + контроль и оценка: подтверждения, политики риска инструментов, оценки (evals), обнаружение аномалий, оптимизатор стоимости, экспорт OTel, защищённый от подделки журнал аудита | $19 за узел / месяц |

Годовые тарифы, Enterprise и актуальные цены — на странице
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключи лицензии для
самостоятельного хостинга работают без облака (`clawmetry license`). Точное
разделение free/платно — в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваши данные остаются на вашей машине

ClawMetry читает локальные файлы сессий и логи. **Никакие данные сессий не покидают
вашу машину**, если вы не запустите `clawmetry connect` — ни промпты, ни ответы, ни
аргументы инструментов, ни содержимое файлов, ни строки логов. Когда вы всё же
подключаетесь, снимок данных шифруется end-to-end ключом, который никогда не
покидает вашу машину, и расшифровывается в вашем браузере. Если у узла нет ключа,
загрузка пропускается, а не отправляется в открытом виде, и никакой ответ сервера
не может это изменить.

По умолчанию до подключения выполняются две вещи, обе можно отключить, и ни одна
не несёт данные сессий: анонимный пинг установки и проверка версии относительно
PyPI. Установка по умолчанию также один раз запрашивает ваш публичный IP для
строки баннера при запуске. Каждое направление, что оно несёт и как его отключить,
перечислено в [docs/EGRESS.md](docs/EGRESS.md); установки с самостоятельным
хостингом, перенаправленные и изолированные от сети вообще не делают
необязательных исходящих вызовов.

Расшифровка происходит в вашем браузере, в коде, который мы вам передаём. Раньше
это было обещанием; теперь это то, что можно проверить. Каждая строка, которая
касается вашего ключа, находится в одном читаемом файле,
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), который
поставляется внутри wheel-пакета и отдаётся дословно, закреплённый хешем
Subresource Integrity. Чтобы убедиться, что браузер запускает именно то, что
мы опубликовали:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чего это не доказывает: мы же отдаём саму страницу, которая загружает этот файл,
а значит, можем отдать и другую страницу. Хеши целостности защищают вас от
скомпрометированного CDN, но не от самого поставщика. Что вы получаете — так это
то, что любая подмена должна быть намеренной, видимой в исходном коде страницы и
отличаться от артефакта на PyPI, который может скачать кто угодно. Самостоятельный
хостинг или работа только локально полностью устраняет эту зависимость.

## Установка

```bash
pip install clawmetry     # затем: clawmetry
```

Или одной командой: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Требуется Python 3.8+ на macOS, Linux или Windows, и хотя бы один рантайм агента
на той же машине. Инструкции по Docker: [docs/DOCKER.md](docs/DOCKER.md).

Или пусть агент настроит всё за вас. Навык [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
учит Claude Code, Codex, Cursor, Gemini CLI, Copilot или OpenCode устанавливать
ClawMetry, сообщать, чем заняты и сколько тратят агенты на этой машине,
останавливать сессию по запросу и удерживать рискованные вызовы инструментов
для подтверждения:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Документация

| | |
|---|---|
| [Совместимость рантаймов](docs/compatibility.md) | Что читает каждый адаптер и как добавить рантайм |
| [Переполнение контекста](docs/CONTEXT_BLOWOUT.md) | Окна по провайдерам, компактизация в сравнении с переполнением, покрытие по рантаймам |
| [Накладные расходы](docs/OVERHEAD.md) | Во что обходится инструментация, измерено, с инструментом для воспроизведения |
| [Права доступа](docs/ENTITLEMENTS.md) | Бесплатно против платно, матрица тарифов, CLI лицензии |
| [Подтверждения и политики](docs/APPROVALS.md) | Контроль перед выполнением, оценка риска, подтверждения с телефона |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Экспорт трейсов куда угодно, приём OTLP откуда угодно |
| [Подключите своего агента](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain от начала до конца, с рабочими примерами |
| [Отслеживание через SDK](docs/SDK_TRACKING.md) | Атрибуция стоимости для агентов, которых вы собрали сами |
| [Чат-каналы](docs/CHANNELS.md) | Адаптеры чатов, отображаемые во Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Изолированные (sandboxed) настройки NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтирование томов |
| [Архитектура](ARCHITECTURE.md) · [Разработка](docs/DEVELOPMENT.md) | Как это устроено изнутри; запуск из исходников |
| [Телеметрия](docs/TELEMETRY.md) | Анонимные пинги установки и открытия десктоп-приложения, и как их отключить |

## Скриншоты

Каждая цифра ниже взята с одной реальной машины, в режиме «только чтение», без каких-либо подготовленных данных.

**Показывает, когда что-то не так, а не просто что произошло.**
Два баннера аномалий сверху: расход, в 7 раз превышающий среднесуточный, и
всплеск стоимости в 4,2 раза. Под ними — 324 из 667 недавних сессий с сигналом
о непродуктивных тратах, с разбивкой по причинам.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Показывает, куда ушли деньги, в любом временном окне.**
$252,47 сегодня, $513,15 за эту неделю, $1312,92 за этот месяц, с токенами,
стоящими за каждой цифрой, и тем, сколько из этого уже покрывает ваша подписка.
Ниже — около $1128/мес, помеченных как возместимые, и уже $17 256/мес,
сэкономленных за счёт повторного использования кэша.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Показывает, как сообщение становится ответом.**
Живая диаграмма потока: вы, канал, по которому пришло сообщение, шлюз, модель,
отвечающая прямо сейчас, и каждый инструмент, к которому она обратилась. Узлы
подсвечиваются по мере прохождения через них работы.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Каждый агент на машине в одной таблице.**
Что он выполняет, сколько стоил за последние 24 часа и за всё время, когда его
видели в последний раз, кто им владеет и покрывает ли счёт подписка. Здесь 14
агентов, 3 сессии в работе, 13 в простое.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Показывает, на что ушли время и деньги хода, инструмент за инструментом.**
Один ход реальной сессии: 11 инструментов за 11,2 минуты за $1,16. Каждый вызов
Bash и каждый вызов модели получает свой столбец на таймлайне, поэтому команда,
выполнявшаяся 4,1 минуты, и та, что заняла 226 мс, различимы с первого взгляда.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Оценивает работу, а не только расходы.**
Оценка «A» за эту неделю: 54 задачи выполнены чисто, 2 проблемные обошлись в
$48,57, а прогоны с недостаточной активностью для оценки исключены из оценки
вместо того, чтобы засчитываться как успех. Каждый проблемный прогон ведёт к
своему трейсу.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Показывает, почему контекстное окно продолжает заполняться.**
715K из окна в 1M токенов на последнем ходу, пик 83,3%, 4 компактизации,
все сработавшие превентивно, а не из-за переполнения, и утилизация каждого
предшествующего хода.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Обнаружение работает без какой-либо настройки с вашей стороны.**
Встроенные детекторы включены сразу после установки: агент замолчал, поток
телеметрии прервался, всплеск стоимости, всплеск токенов, рост ошибок, скачок
ошибок, порог бюджета, совпадение сигнатуры угрозы, находка инструмента
безопасности, изменение состояния защищённости. Ваши собственные правила —
опционально поверх этого.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Удержание рискованного вызова включается по желанию и поставляется выключенным.**
Рекурсивное удаление, принудительный push, sudo, секреты, установка пакетов и
исходящие вызовы — для каждого есть правило, которое можно включить. Пока вы
этого не сделали, ClawMetry наблюдает и ничего не меняет. Как только правило
включено, подходящие под него вызовы ждут здесь (или на вашем телефоне)
подтверждения или отказа.

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
