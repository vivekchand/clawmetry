<!-- i18n-src:88be2deff5d5 -->
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

**Смотрите, как думает ваш агент.** Наблюдаемость в реальном времени для **30 сред выполнения ИИ-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 26. Единая панель для всего вашего флота агентов.

> 🌐 **Читайте на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Ноль настроек. Автоматическое определение всего.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**. Ноль настроек: находит уже установленные у вас среды выполнения агентов, читает их в режиме только для чтения и ничего не меняет в том, как они работают.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## Работает с 30 средами выполнения агентов

**Бесплатно в open source приложении:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**В платном плане:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Каждая среда выполнения получает одну и ту же панель. Запустите несколько одновременно, и переключатель в шапке будет перенастраивать каждую вкладку на выбранную из них.

Собрали своего агента на базе SDK вместо готовой среды? Перехватчик отслеживает и его вызовы LLM. См. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Что вы получаете

- **Сессии и транскрипты**: что делал каждый агент, ход за ходом, с воспроизведением
- **Стоимость и токены**: по среде выполнения, модели, сессии и дню, с флагами аномалий
- **Flow**: живая диаграмма движения сообщений через каналы, модели и инструменты
- **Brain**: поток событий рассуждений и вызовов инструментов в реальном времени
- **Переполнение контекста**: утилизация окна с учётом конкретного провайдера, сжатие против вынужденного переполнения, плюс карта того, что мы *не можем* увидеть по каждой среде выполнения ([как](docs/CONTEXT_BLOWOUT.md))
- **Память и навыки**: файлы и навыки, которые фактически загрузила каждая среда выполнения
- **Здоровье и логи**: диск, память, частота ошибок, лимиты скорости, поток логов в реальном времени
- **Оповещения**: лимиты бюджета, всплески ошибок, агент офлайн, с маршрутизацией в Slack, Discord, PagerDuty, Telegram, Email
- **Подтверждения**: приостанавливайте рискованные вызовы инструментов *до* их выполнения и подтверждайте их с телефона ([как](docs/APPROVALS.md))

## Переполнение контекста и цена наблюдения

Два вопроса, на которые стоит ответить, прежде чем доверять любому инструменту сравнения агентов.

**Как обрабатывается переполнение контекстного окна между разными средами выполнения?**

Процент утилизации честен ровно настолько, насколько честен знаменатель. ClawMetry определяет размер окна по каждому провайдеру из [таблицы, которую можно прочитать и предложить PR](clawmetry/context_windows.py), охватывающей Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama и GLM. Он не измеряет все 30 сред выполнения одной линейкой от одного поставщика. Это важно: ход на 300K токенов в GPT-5, оценённый по линейке Anthropic в 200K, читается как ">100%, переполнено", хотя на самом деле это 75% от 400K у GPT-5. Та же линейка скрывает реально переполненный ход на 130K в DeepSeek как комфортные 65%.

Каждое окно поставляется со своим происхождением: `model_table`, `explicit_marker`, `observed_floor` или честный `default`, когда модель нам неизвестна. Индикатор, построенный на догадке, никогда не отображается с той же убедительностью, что и построенный на справочной таблице.

ClawMetry способен видеть события сжатия только в некоторых средах выполнения. Поэтому `GET /api/context-coverage` сообщает по каждой среде выполнения, означает ли **ноль "прошло чисто" или "мы слепы"**. Ноль, который на самом деле означает слепоту, так и обозначается. [Подробнее](docs/CONTEXT_BLOWOUT.md)

**Сколько стоит инструментирование?**

| Путь | Добавлено к вашему агенту | По умолчанию? |
|---|---|---|
| Отслеживание файлов сессий (все 30 сред выполнения) | **0**. Отдельный процесс, ни строки кода ClawMetry в вашем агенте | включено |
| HTTP-перехватчик (`CLAWMETRY_INTERCEPT=1`) | **+0,44 мс** на каждый вызов LLM, или 0,009% от вызова длительностью 5 с | выключено |
| Шлюз предварительного хука для инструментов (тёплый кэш) | **+44 мс** на каждый перехваченный вызов инструмента, поверх интерпретаторского минимума в 36 мс | выключено |
| Прокси принудительного применения политик | **+9,7 мс** на каждый вызов LLM | выключено |

Стоимость для хоста демона: **2762 событий/с** на приём, **710 байт/событие** на диске (67,7 МБ на 100 тыс. событий) и **~12% одного ядра** в устойчивом режиме на загруженной установке. Последнее число превышает наш собственный заявленный бюджет в 5-10%, поэтому оно опубликовано как баг, который нужно устранить, а не скрыто со страницы.

Измерено на Apple M2 Pro с помощью `benchmarks/overhead.py`. Стенд запускает каждое условие в отдельном процессе, чередует их порядок и **отказывается печатать число, если раунды расходятся в его знаке**. Запустите его на своей машине за минуту:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

Измерен каждый путь, включая шлюзы хуков и прокси принудительного применения политик, и стенд работает в CI на Linux, macOS и Windows. Стоит знать два результата: прокси стоит примерно в семь раз дороже на Windows, чем на Linux, а демон в настоящее время устойчиво потребляет около 12% одного ядра, что превышает наш собственный бюджет в 5-10%. Необработанные данные JSON, методика и то, что пока не измерено, находятся в [docs/OVERHEAD.md](docs/OVERHEAD.md).

## Тарифы

| Тариф | Что включено | Цена |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, полная панель, только локально | $0 |
| **Starter** | Все остальные среды выполнения из списка выше, представление флота, синхронизация с облаком | $9 за узел / месяц |
| **Pro** | Starter + управление и оценка: подтверждения, политики риска инструментов, оценки (evals), обнаружение аномалий, оптимизатор затрат, экспорт в OTel, защищённый от подделки журнал аудита | $19 за узел / месяц |

Годовые тарифы, Enterprise и актуальные цифры находятся на странице
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключи лицензии для самостоятельного хостинга работают без облака (`clawmetry license`). Точное разделение бесплатных и платных функций описано в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваши данные остаются на вашей машине

ClawMetry читает локальные файлы сессий и логи. **Никакие данные сессий не покидают вашу машину, пока вы не запустите `clawmetry connect`** — ни запросы, ни ответы, ни аргументы инструментов, ни содержимое файлов, ни строки логов. Когда вы всё же подключаетесь, снимок шифруется сквозным шифрованием ключом, который никогда не покидает вашу машину, и расшифровывается в вашем браузере. Если у узла нет ключа, загрузка пропускается, а не отправляется в открытом виде, и никакой ответ сервера не может это отключить.

Две вещи по умолчанию выполняются ещё до подключения, обе можно отключить, и ни одна не несёт данных сессий: анонимный пинг об установке и проверка версии на PyPI. Установка по умолчанию также один раз запрашивает ваш публичный IP для строки баннера при запуске. Каждый пункт назначения, что он передаёт и как его отключить, перечислены в [docs/EGRESS.md](docs/EGRESS.md); самостоятельные, перенаправленные и изолированные (air-gapped) установки вообще не делают никаких необязательных исходящих вызовов.

Расшифровка происходит в вашем браузере, в коде, который мы вам предоставляем. Раньше это было обещанием; теперь это можно проверить. Каждая строка, касающаяся вашего ключа, находится в одном читаемом файле, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js), который поставляется внутри wheel-пакета и отдаётся дословно, закреплённый хешем Subresource Integrity. Чтобы убедиться, что браузер выполняет именно то, что мы опубликовали:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

Чего это не доказывает: мы отдаём страницу, которая загружает этот файл, а значит, могли бы отдать другую страницу. Хеши целостности защищают вас от скомпрометированного CDN, но не от самого поставщика. Что вы получаете — так это то, что любая подмена должна быть преднамеренной, видимой в исходном коде страницы и отличающейся от артефакта на PyPI, который может проверить кто угодно. Самостоятельный хостинг или работа только локально полностью устраняет эту зависимость.

## Установка

```bash
pip install clawmetry     # затем: clawmetry
```

Или одной строкой: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Требуется Python 3.8+ на macOS, Linux или Windows и хотя бы одна среда выполнения агента на той же машине. Инструкции по Docker: [docs/DOCKER.md](docs/DOCKER.md).

Или позвольте агенту настроить всё за вас. Навык [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
учит Claude Code, Codex, Cursor, Gemini CLI, Copilot или OpenCode устанавливать ClawMetry, сообщать, что делают и на что тратят агенты на машине, останавливать конкретную сессию по запросу и удерживать рискованные вызовы инструментов для подтверждения:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Документация

| | |
|---|---|
| [Совместимость сред выполнения](docs/compatibility.md) | Что читает каждый адаптер и как добавить новую среду выполнения |
| [Переполнение контекста](docs/CONTEXT_BLOWOUT.md) | Окна по провайдерам, сжатие против переполнения, покрытие по каждой среде выполнения |
| [Накладные расходы](docs/OVERHEAD.md) | Сколько стоит инструментирование, измерено, со стендом для воспроизведения |
| [Права доступа](docs/ENTITLEMENTS.md) | Бесплатно против платно, матрица тарифов, CLI лицензии |
| [Подтверждения и политики](docs/APPROVALS.md) | Проверка перед выполнением, оценка риска, подтверждения с телефона |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Экспорт трасс куда угодно, приём OTLP откуда угодно |
| [Подключите своего агента](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain от начала до конца, с рабочими примерами |
| [Отслеживание через SDK](docs/SDK_TRACKING.md) | Атрибуция затрат для агентов, которых вы создали сами |
| [Каналы чата](docs/CHANNELS.md) | Адаптеры чатов, отображаемые во Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Изолированные (sandboxed) настройки NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтирование томов |
| [Архитектура](ARCHITECTURE.md) · [Разработка](docs/DEVELOPMENT.md) | Как это устроено внутри; запуск из исходников |
| [Телеметрия](docs/TELEMETRY.md) | Анонимные пинги установки и открытия десктоп-приложения и как их отключить |

## Скриншоты

Каждая цифра ниже — с одной реальной машины, в режиме только для чтения, без какой-либо предварительной подготовки данных.

**Панель сообщает, когда что-то не так, а не просто что произошло.**
Два баннера аномалий вверху: расходы, в 7 раз превышающие среднесуточные, и всплеск стоимости в 4,2 раза. Ниже — 324 из 667 недавних сессий с признаком расточительности, с разбивкой по причинам.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**Показывает, куда ушли деньги, в любом временном окне.**
$252,47 сегодня, $513,15 за эту неделю, $1312,92 за этот месяц, с указанием токенов за каждой цифрой и тем, сколько из этого уже покрывает ваша подписка. Ниже — около $1128/мес, отмеченных как возместимые, и уже сэкономленные $17 256/мес за счёт повторного использования кэша.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**Показывает, как сообщение превращается в ответ.**
Живая диаграмма потока: вы, канал, по которому пришло сообщение, шлюз, модель, отвечающая прямо сейчас, и каждый инструмент, к которому она обратилась. Узлы подсвечиваются по мере прохождения через них работы.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**Каждый агент на машине — в одной таблице.**
Что он выполняет, сколько стоил за последние 24 часа и за всё время, когда его видели в последний раз, кто им владеет, и покрывает ли подписка счёт. Здесь 14 агентов, 3 сессии работают, 13 бездействуют.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**Показывает, куда ушли время и деньги хода, по каждому инструменту.**
Один ход реальной сессии: 11 инструментов за 11,2 минуты за $1,16. Каждый вызов Bash и вызов модели получает свою полосу на временной шкале, так что команда, выполнявшаяся 4,1 минуты, и та, что выполнялась 226 мс, различимы с первого взгляда.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**Оценивает работу, а не только расходы.**
Оценка A за эту неделю: 54 задачи завершились чисто, 2 неудачные обошлись в $48,57, а прогоны со слишком малой активностью для оценки исключены из оценки, а не засчитаны как успехи. Каждый неудачный прогон ведёт к своей трассе.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**Показывает, почему контекстное окно продолжает заполняться.**
715K из 1M-токенового окна на последнем ходу, пик 83,3%, 4 сжатия, которые все сработали проактивно, а не при переполнении, и утилизация каждого предшествующего хода.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Обнаружение работает без какой-либо настройки с вашей стороны.**
Встроенные детекторы включены с момента установки: агент замолчал, поток телеметрии остановился, всплеск стоимости, всплеск токенов, растущее число ошибок, всплеск ошибок, превышение бюджетного порога, обнаружена сигнатура угрозы, срабатывание инструмента безопасности, изменение состояния безопасности. Собственные правила — опциональное дополнение поверх них.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**Удержание рискованного вызова включается по желанию и поставляется отключённым.**
Для рекурсивных удалений, принудительных push, sudo, секретов, установки пакетов и исходящих вызовов есть отдельное правило, которое можно включить. Пока вы этого не сделаете, ClawMetry наблюдает и ничего не меняет. После включения совпадающие вызовы ожидают здесь (или на вашем телефоне) подтверждения или отклонения.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

Больше скриншотов по каждой среде выполнения: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
