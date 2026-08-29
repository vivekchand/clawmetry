<!-- i18n-src:d21bea5161e0 -->
> Русский translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Смотрите, как думает ваш агент.** Наблюдаемость в реальном времени для **30 сред выполнения ИИ-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 26 других. Единая панель для всего вашего флота агентов.

> 🌐 **Читайте на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Никакой настройки. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**. Никакой настройки: система находит
уже установленные у вас среды выполнения агентов, читает их только для чтения и никак не влияет на их работу.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Работает с 30 средами выполнения агентов

**Бесплатно в приложении с открытым исходным кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**По платному тарифу:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Каждая среда выполнения получает одну и ту же панель. Запустите несколько сразу, и переключатель в шапке
перенастроит каждую вкладку на выбранную среду.

Собрали собственного агента на базе SDK вместо готовой среды? Перехватчик отслеживает и его LLM-вызовы тоже.
Подробнее: [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Что вы получаете

- **Сессии и транскрипты**: что делал каждый агент, шаг за шагом, с воспроизведением
- **Стоимость и токены**: по средам выполнения, моделям, сессиям и дням, с флагами аномалий
- **Flow**: живая диаграмма сообщений, проходящих через каналы, модели и инструменты
- **Brain**: поток событий рассуждений и вызовов инструментов в реальном времени
- **Переполнение контекста**: использование окна с учётом провайдера, сжатие против принудительного переполнения, плюс карта того, чего мы *не видим* по каждой среде выполнения ([как это устроено](docs/CONTEXT_BLOWOUT.md))
- **Память и навыки**: файлы и навыки, которые фактически загрузила каждая среда выполнения
- **Здоровье и логи**: диск, память, частота ошибок, лимиты запросов, поток логов в реальном времени
- **Оповещения**: лимиты бюджета, всплески ошибок, офлайн-агент, маршрутизация в Slack, Discord, PagerDuty, Telegram, Email
- **Одобрения**: приостановка рискованных вызовов инструментов *до* их выполнения и одобрение с телефона ([как это устроено](docs/APPROVALS.md))

## Переполнение контекста и во что обходится наблюдение

Два вопроса, на которые стоит ответить, прежде чем доверять любому инструменту сравнения агентов.

**Как система обрабатывает переполнение контекстного окна в разных средах выполнения?**

Процент использования честен ровно настолько, насколько честен знаменатель. ClawMetry
определяет размер окна для каждого провайдера по [таблице, которую можно прочитать и
предложить правку](clawmetry/context_windows.py), охватывающей Anthropic, OpenAI, Google, xAI,
DeepSeek, Kimi, Qwen, Mistral, Llama и GLM. Система не измеряет все 26
сред выполнения одной линейкой одного вендора. Это важно: реплика на 300K токенов в GPT-5, оценённая
по мерке Anthropic в 200K, читается как ">100%, переполнено", хотя на самом деле это 75% от
400K у GPT-5. Та же линейка скрывает реально переполненную реплику DeepSeek на 130K,
показывая её как комфортные 65%.

Каждое окно поставляется с указанием происхождения: `model_table`, `explicit_marker`,
`observed_floor`, либо честное `default`, когда модель неизвестна. Индикатор, построенный
на догадке, никогда не отображается с той же достоверностью, что и построенный
на справочной таблице.

ClawMetry может видеть события сжатия только в некоторых средах выполнения. Поэтому
`GET /api/context-coverage` сообщает по каждой среде выполнения, означает ли **ноль
"прошло чисто" или "мы ничего не видим"**. `0`, который на самом деле означает "не видим", так и говорит.
[Подробности](docs/CONTEXT_BLOWOUT.md)

**Во что обходится инструментирование?**

| Путь | Добавлено к вашему агенту | По умолчанию? |
|---|---|---|
| Слежение за файлами сессий (все 30 сред выполнения) | **0**. Отдельный процесс, никакого кода ClawMetry в вашем агенте | включено |
| HTTP-перехватчик (`CLAWMETRY_INTERCEPT=1`) | **+0.44 мс** на LLM-вызов, или 0.009% от 5-секундного вызова | выключено |
| Шлюз pre-tool hook (тёплый кэш) | **+44 мс** на вызов инструмента под контролем, при базовом уровне интерпретатора в 36 мс | выключено |
| Прокси принудительного применения политик | **+9.7 мс** на LLM-вызов | выключено |

Стоимость хостинга демона: **2762 события/сек** приём, **710 байт/событие** на диске
(67.7 МБ на 100 тыс. событий) и **~12% одного ядра** в устойчивом режиме на загруженной
установке. Последнее число превышает наш заявленный бюджет в 5-10%, поэтому оно
опубликовано как баг, который предстоит устранить, а не скрыто со страницы.

Измерено на Apple M2 Pro с помощью `benchmarks/overhead.py`. Тестовый стенд запускает
каждый вариант в отдельном процессе, чередует их порядок и **отказывается выводить
число, если раунды расходятся по знаку**. Запустите его на своей машине за минуту:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Измерен каждый путь, включая шлюзы hook и прокси принудительного применения политик,
и тестовый стенд работает на Linux, macOS и Windows в CI. Стоит знать два результата:
прокси обходится примерно в семь раз дороже на Windows, чем на Linux, а демон сейчас
устойчиво потребляет около 12% одного ядра, превышая наш собственный бюджет в 5-10%.
Необработанные данные JSON, методика и то, что пока не измерено, находятся в
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## Тарифы

| Тариф | Что включено | Цена |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, полная панель, только локально | $0 |
| **Starter** | Все остальные среды выполнения выше, обзор флота, облачная синхронизация | $9 за узел / месяц |
| **Pro** | Starter + управление и оценка: одобрения, политики риска инструментов, оценки, обнаружение аномалий, оптимизатор стоимости, экспорт OTel, защищённый от подделки журнал аудита | $19 за узел / месяц |

Годовые тарифы, Enterprise и актуальные цены смотрите на
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключи лицензии для самостоятельного
хостинга работают без облака (`clawmetry license`). Точное разделение на бесплатные/платные функции
описано в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваши данные остаются на вашей машине

ClawMetry читает локальные файлы сессий и логи. **Данные сессий не покидают вашу машину,
если вы не запустите `clawmetry connect`** — ни запросы, ни ответы, ни аргументы инструментов,
ни содержимое файлов, ни строки логов. Когда вы всё же подключаетесь, снимок шифруется
сквозным шифрованием с ключом, который никогда не покидает вашу машину, и расшифровывается
в вашем браузере. Если у узла нет ключа, загрузка пропускается вместо отправки в открытом
виде, и никакой ответ сервера не может это отключить.

Две вещи выполняются по умолчанию ещё до подключения, обе можно отключить, и ни одна не несёт
данных сессии: анонимный пинг установки и проверка версии на PyPI. Установка по умолчанию также
один раз запрашивает ваш публичный IP для строки баннера при запуске. Каждый пункт назначения,
что он передаёт и как его отключить, перечислены в
[docs/EGRESS.md](docs/EGRESS.md); установки с самостоятельным хостингом, перенаправленные и изолированные от сети
не делают никаких дискреционных исходящих вызовов вообще.

Расшифровка происходит в вашем браузере, в коде, который мы вам предоставляем. Раньше это было
обещанием; теперь это то, что можно проверить. Каждая строка, которая касается вашего ключа,
находится в одном читаемом файле, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
который поставляется внутри wheel-пакета и отдаётся дословно, закреплённый хешем Subresource
Integrity. Чтобы убедиться, что браузер выполняет именно то, что мы опубликовали:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чего это не доказывает: мы отдаём страницу, которая загружает файл, поэтому мы могли бы
отдать другую страницу. Хеши целостности защищают вас от скомпрометированного CDN,
а не от поставщика. Что вы получаете — это то, что любая подмена должна быть
преднамеренной, видимой в исходном коде страницы и отличаться от артефакта на PyPI,
который любой может скачать. Самостоятельный хостинг или использование только локально
полностью убирает эту зависимость.

## Установка

```bash
pip install clawmetry     # затем: clawmetry
```

Или однострочник: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Требуется Python 3.8+ на macOS, Linux или Windows, а также хотя бы одна среда выполнения агента на
той же машине. Инструкции по Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Документация

| | |
|---|---|
| [Совместимость сред выполнения](docs/compatibility.md) | Что читает каждый адаптер и как добавить среду выполнения |
| [Переполнение контекста](docs/CONTEXT_BLOWOUT.md) | Окна по провайдерам, сжатие против переполнения, покрытие по средам выполнения |
| [Накладные расходы](docs/OVERHEAD.md) | Во что обходится инструментирование, измерено, со стендом для воспроизведения |
| [Права доступа](docs/ENTITLEMENTS.md) | Бесплатное против платного, матрица тарифов, license CLI |
| [Одобрения и политики](docs/APPROVALS.md) | Проверка перед выполнением, оценка риска, одобрения с телефона |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Экспорт трасс куда угодно, приём OTLP откуда угодно |
| [Отслеживание SDK](docs/SDK_TRACKING.md) | Атрибуция стоимости для агентов, которых вы создали сами |
| [Чат-каналы](docs/CHANNELS.md) | Адаптеры чатов, отображаемые во Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Изолированные настройки NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтирование томов |
| [Архитектура](ARCHITECTURE.md) · [Разработка](docs/DEVELOPMENT.md) | Как это устроено внутри; запуск из исходного кода |
| [Телеметрия](docs/TELEMETRY.md) | Анонимные пинги установки и открытия рабочего стола, и как их отключить |

## Скриншоты

Каждое число ниже взято с одной реальной машины, только для чтения, без какой-либо подготовки данных.

**Система сообщает, когда что-то не так, а не просто что произошло.**
Два баннера аномалий вверху: расходы, вдвое-семикратно превышающие среднедневные,
и всплеск стоимости в 4.2 раза. Ниже — 324 из 667 недавних сессий с сигналом
о нерациональных тратах, с разбивкой по причинам.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Система показывает, куда ушли деньги, в любом временном окне.**
$252.47 сегодня, $513.15 за эту неделю, $1312.92 за этот месяц, с указанием токенов
за этим стоящих и того, сколько из этого уже покрывает ваша подписка. Ниже —
около $1128/мес размечено как возвратные потери и $17256/мес уже сэкономлено за счёт
повторного использования кэша.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Система рисует, как сообщение превращается в ответ.**
Живая диаграмма потока: вы, канал, по которому пришло сообщение, шлюз, модель,
отвечающая прямо сейчас, и каждый инструмент, к которому она обратилась. Узлы
подсвечиваются по мере прохождения через них работы.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Каждый агент на машине, в одной таблице.**
Что он выполняет, сколько стоит за последние 24 часа и за всё время, когда его
видели в последний раз, кто им владеет, и покрывает ли счёт подписка. Здесь 14 агентов,
3 сессии в работе, 13 в покое.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Система показывает, куда ушли время и деньги одного цикла, по инструментам.**
Один цикл реальной сессии: 11 инструментов за 11.2 минуты за $1.16. Каждый вызов
Bash и вызов модели получает свою полосу на шкале времени, так что вызов, длившийся
4.1 минуты, и вызов, длившийся 226 мс, различимы с первого взгляда.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Система оценивает работу, а не только расходы.**
Оценка A за эту неделю: 54 задачи выполнены чисто, 2 неудачных обошлись в $48.57,
а прогоны с недостаточной активностью для оценки исключены из оценки, а не засчитаны
как успех. Каждый неудачный прогон ведёт к своей трассе.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Система показывает, почему контекстное окно продолжает заполняться.**
715K из 1M-токенного окна на последнем цикле, пик 83.3%, 4 сжатия, все сработавшие
проактивно, а не из-за переполнения, плюс использование каждого предыдущего цикла.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Обнаружение работает без какой-либо настройки с вашей стороны.**
Встроенные детекторы включены сразу после установки: агент замолчал, поток телеметрии
остановился, всплеск стоимости, всплеск токенов, рост числа ошибок, всплеск ошибок,
порог бюджета, обнаружена сигнатура угрозы, находка средства безопасности, изменение
состояния защищённости. Собственные правила опциональны и добавляются поверх.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Приостановка рискованного вызова включается по желанию и поставляется выключенной.**
Рекурсивное удаление, принудительный push, sudo, секреты, установка пакетов и исходящие
вызовы — для каждого можно включить своё правило. Пока вы этого не сделали, ClawMetry
наблюдает и ничего не меняет. Как только правило включено, подходящие под него вызовы
ждут здесь (или на вашем телефоне) одобрения или отказа.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Больше скриншотов, по средам выполнения: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
