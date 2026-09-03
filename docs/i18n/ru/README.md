<!-- i18n-src:9767c8001c9c -->
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

**Смотрите, как думает ваш агент.** Наблюдаемость в реальном времени для **30 сред выполнения ИИ-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 26. Одна панель для всего вашего флота агентов.

> 🌐 **Читать на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Никакой настройки. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**. Никакой настройки: приложение находит уже установленные у вас среды выполнения агентов, читает их только для чтения и ничего не меняет в их работе.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Работает с 30 средами выполнения агентов

**Бесплатно в приложении с открытым исходным кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**По платной подписке:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

У каждой среды выполнения одна и та же панель. Запускайте несколько сразу, и переключатель в шапке будет перенаправлять каждую вкладку на нужную из них.

Собрали своего агента на базе SDK, а не готовой среды? Перехватчик отслеживает и его вызовы LLM. См. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Что вы получаете

- **Сессии и транскрипты**: что делал каждый агент, ход за ходом, с воспроизведением
- **Стоимость и токены**: по среде выполнения, модели, сессии и дню, с флагами аномалий
- **Flow**: диаграмма движения сообщений через каналы, модели и инструменты в реальном времени
- **Brain**: поток событий рассуждений и вызовов инструментов по мере их появления
- **Переполнение контекста**: размер окна с учётом провайдера, сжатие против принудительного переполнения, а также карта по каждой среде выполнения того, что мы *не можем* увидеть ([как](docs/CONTEXT_BLOWOUT.md))
- **Память и навыки**: файлы и навыки, которые фактически загружала каждая среда выполнения
- **Здоровье и логи**: диск, память, частота ошибок, лимиты скорости, живой поток логов
- **Оповещения**: лимиты бюджета, всплески ошибок, отключение агента, отправка в Slack, Discord, PagerDuty, Telegram, Email
- **Подтверждения**: приостановка рискованных вызовов инструментов *до* их выполнения и подтверждение с телефона ([как](docs/APPROVALS.md))

## Переполнение контекста и цена наблюдения

Два вопроса, на которые стоит ответить перед тем, как доверять любому инструменту сравнения агентов.

**Как это обрабатывает переполнение контекстного окна между средами выполнения?**

Процент использования честен ровно настолько, насколько честен знаменатель. ClawMetry определяет размер окна для каждого провайдера по [таблице, которую можно прочитать и предложить исправить через PR](clawmetry/context_windows.py), охватывающей Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama и GLM. Приложение не измеряет все 26 сред выполнения по линейке одного вендора. Это важно: ход на 300K токенов в GPT-5, оценённый по мерке Anthropic в 200K, читается как ">100%, переполнено", хотя на самом деле это 75% от 400K у GPT-5. Та же самая линейка маскирует реально переполненный ход в 130K у DeepSeek как комфортные 65%.

Каждое окно поставляется со своим происхождением: `model_table`, `explicit_marker`, `observed_floor` или честный `default`, когда модель неизвестна. Индикатор, построенный на догадке, никогда не отображается с той же уверенностью, что и построенный на точном значении из таблицы.

ClawMetry может видеть события сжатия только в некоторых средах выполнения. Поэтому `GET /api/context-coverage` сообщает по каждой среде выполнения, означает ли **ноль "прошло чисто" или "мы ничего не видим"**. `0`, который на самом деле означает "не видим", так и указывается. [Подробнее](docs/CONTEXT_BLOWOUT.md)

**Сколько стоит инструментирование?**

| Путь | Добавлено к вашему агенту | По умолчанию? |
|---|---|---|
| Слежение за файлами сессий (все 30 сред выполнения) | **0**. Отдельный процесс, никакого кода ClawMetry в вашем агенте | включено |
| HTTP-перехватчик (`CLAWMETRY_INTERCEPT=1`) | **+0.44 мс** на вызов LLM, или 0.009% от 5-секундного вызова | выключено |
| Шлюз pre-tool hook (тёплый кэш) | **+44 мс** на каждый защищённый вызов инструмента, поверх базового порога интерпретатора в 36 мс | выключено |
| Прокси принуждения | **+9.7 мс** на вызов LLM | выключено |

Стоимость хоста демона: **2762 событий/сек** приёма, **710 байт/событие** на диске (67.7 МБ на 100 тыс. событий) и **~12% одного ядра** в устойчивом режиме на загруженной установке. Последнее число превышает наш собственный заявленный бюджет в 5-10%, поэтому оно опубликовано как баг, который нужно устранить, а не скрыто со страницы.

Измерено на Apple M2 Pro с помощью `benchmarks/overhead.py`. Инструмент запускает каждое условие в отдельном процессе, чередует их порядок и **отказывается печатать число, если раунды расходятся в знаке**. Запустите его на своей машине за минуту:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Измерен каждый путь, включая шлюзы hook и прокси принуждения, а инструмент запускается на Linux, macOS и Windows в CI. Стоит знать два результата: прокси стоит примерно в семь раз дороже на Windows, чем на Linux, а демон сейчас устойчиво потребляет около 12% одного ядра, превышая наш собственный бюджет в 5-10%. Необработанный JSON, методика и то, что до сих пор не измерено, находятся в [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Цены

| План | Что включено | Цена |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, полная панель, только локально | $0 |
| **Starter** | Все остальные среды выполнения выше, обзор флота, облачная синхронизация | $9 за узел / месяц |
| **Pro** | Starter + контроль и оценка: подтверждения, политики риска инструментов, оценки (evals), обнаружение аномалий, оптимизатор затрат, экспорт OTel, защищённый от подделки журнал аудита | $19 за узел / месяц |

Годовые планы, Enterprise и актуальные цифры находятся на странице
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключи лицензий для самостоятельного хостинга работают без облака (`clawmetry license`). Точное разделение бесплатного и платного функционала описано в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваши данные остаются на вашей машине

ClawMetry читает локальные файлы сессий и логи. **Никакие данные сессий не покидают вашу машину, пока вы не запустите `clawmetry connect`** — ни подсказки (prompts), ни ответы, ни аргументы инструментов, ни содержимое файлов, ни строки логов. Когда вы подключаетесь, снимок шифруется сквозным шифрованием с ключом, который никогда не покидает вашу машину, и расшифровывается в вашем браузере. Если у узла нет ключа, загрузка пропускается, а не отправляется в открытом виде, и никакой ответ сервера не может это отключить.

Две вещи выполняются по умолчанию до подключения, обе можно отключить, и ни одна не несёт данные сессий: анонимный пинг установки и проверка версии на PyPI. Установка по умолчанию также один раз запрашивает ваш публичный IP для строки баннера при запуске. Каждый пункт назначения, что он несёт и как его отключить, перечислены в [docs/EGRESS.md](docs/EGRESS.md); установки с самостоятельным хостингом, перенаправленные и изолированные от сети (air-gapped) не делают никаких необязательных исходящих вызовов вообще.

Расшифровка происходит в вашем браузере, в коде, который мы вам предоставляем. Раньше это было обещанием; теперь это можно проверить. Каждая строка, которая касается вашего ключа, находится в одном читаемом файле, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), который поставляется внутри wheel-пакета и раздаётся дословно, закреплённый хешем Subresource Integrity. Чтобы убедиться, что браузер выполняет именно то, что мы опубликовали:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чего это не доказывает: страницу, которая загружает файл, раздаём мы сами, поэтому мы теоретически могли бы раздать другую страницу. Хеши целостности защищают вас от скомпрометированной CDN, но не от самого вендора. Что вы получаете взамен: любая подмена должна быть намеренной, видимой в исходном коде страницы и отличаться от артефакта на PyPI, который может проверить кто угодно. Самостоятельный хостинг или использование только локально полностью устраняет эту зависимость.

## Установка

```bash
pip install clawmetry     # затем: clawmetry
```

Или однострочник: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Требуется Python 3.8+ на macOS, Linux или Windows и хотя бы одна среда выполнения агента на той же машине. Инструкции по Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Документация

| | |
|---|---|
| [Совместимость сред выполнения](docs/compatibility.md) | Что читает каждый адаптер и как добавить среду выполнения |
| [Переполнение контекста](docs/CONTEXT_BLOWOUT.md) | Окна по провайдерам, сжатие против переполнения, покрытие по каждой среде выполнения |
| [Накладные расходы](docs/OVERHEAD.md) | Что стоит инструментирование, измерено, с инструментом для воспроизведения |
| [Права доступа (Entitlements)](docs/ENTITLEMENTS.md) | Бесплатное против платного, матрица тарифов, CLI для лицензий |
| [Подтверждения и политики](docs/APPROVALS.md) | Предварительная проверка выполнения, оценка риска, подтверждения с телефона |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Экспорт трасс куда угодно, приём OTLP откуда угодно |
| [Подключите своего агента](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain от начала до конца, с рабочими примерами |
| [Отслеживание через SDK](docs/SDK_TRACKING.md) | Атрибуция затрат для агентов, которых вы собрали сами |
| [Чат-каналы](docs/CHANNELS.md) | Адаптеры чатов, отображаемые во Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Изолированные (sandboxed) настройки NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтирование томов |
| [Архитектура](ARCHITECTURE.md) · [Разработка](docs/DEVELOPMENT.md) | Как это устроено внутри; запуск из исходников |
| [Телеметрия](docs/TELEMETRY.md) | Анонимные пинги установки и открытия десктопа, и как их отключить |

## Скриншоты

Каждая цифра ниже взята с одной реальной машины, только для чтения, без каких-либо подготовленных данных.

**Приложение сообщает, когда что-то не так, а не просто что произошло.**
Два баннера аномалий сверху: расход, идущий в 7 раз выше среднедневного, и всплеск стоимости в 4.2 раза. Под ними 324 из 667 последних сессий несут сигнал о потерях, с разбивкой по причинам.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Приложение показывает, куда ушли деньги, в любом временном окне.**
$252.47 сегодня, $513.15 за эту неделю, $1312.92 за этот месяц, каждая цифра с токенами за ней и с тем, сколько из этого уже покрывает ваша подписка. Ниже примерно $1128/мес отмечено как то, что можно вернуть, и $17256/мес уже сэкономлено за счёт повторного использования кэша.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Приложение показывает, как сообщение превращается в ответ.**
Живая диаграмма потока: вы, канал, по которому пришло сообщение, шлюз, модель, отвечающая прямо сейчас, и каждый инструмент, к которому она обратилась. Узлы загораются по мере прохождения работы через них.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Каждый агент на машине в одной таблице.**
Что он выполняет, во что обходится за последние 24 часа и за всё время, когда его видели в последний раз, кто им владеет и покрывает ли подписка счёт. Здесь 14 агентов, 3 сессии в работе, 13 в тишине.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Приложение показывает, на что ушли время и деньги хода, по каждому инструменту отдельно.**
Один ход реальной сессии: 11 инструментов за 11.2 минуты за $1.16. Каждый вызов Bash и вызов модели получает свою полосу на временной шкале, так что вызов, работавший 4.1 минуты, и вызов, работавший 226 мс, различимы с первого взгляда.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Приложение оценивает работу, а не только расходы.**
Оценка A за эту неделю: 54 задачи выполнены чисто, 2 неудачные обошлись в $48.57, а прогоны со слишком малой активностью для оценки исключаются из оценки, вместо того чтобы засчитываться как успех. Каждый неудачный прогон ведёт к своей трассе.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Приложение показывает, почему контекстное окно продолжает заполняться.**
715K из окна на 1M токенов на последнем ходу, пик 83.3%, 4 сжатия, все сработавшие проактивно, а не при переполнении, а также использование каждого предыдущего хода.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Обнаружение работает без какой-либо настройки с вашей стороны.**
Встроенные детекторы включены с момента установки: агент замолчал, поток телеметрии остановился, всплеск стоимости, всплеск токенов, растущее число ошибок, скачок ошибок, порог бюджета, обнаружена сигнатура угрозы, находка инструмента безопасности, изменение состояния безопасности. Ваши собственные правила опциональны и добавляются поверх.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Приостановка рискованного вызова опциональна и по умолчанию отключена.**
Рекурсивное удаление, принудительный push, sudo, секреты, установка пакетов и исходящие вызовы — для каждого есть правило, которое можно включить. Пока вы этого не сделали, ClawMetry наблюдает и ничего не меняет. Как только правило включено, соответствующие вызовы ожидают здесь (или на вашем телефоне) подтверждения или отклонения.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Больше, по каждой среде выполнения: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
