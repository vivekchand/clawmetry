<!-- i18n-src:6795052055e2 -->
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

**Смотрите, как думает ваш агент.** Наблюдаемость в реальном времени для **26 сред выполнения AI-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 22. Одна панель для всего вашего флота агентов.

> 🌐 **Читайте на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Без настройки. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**. Без настройки: он находит уже установленные у вас среды выполнения агентов, читает их в режиме "только чтение" и никак не влияет на их работу.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Работает с 26 средами выполнения агентов

**Бесплатно в приложении с открытым исходным кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**В платном тарифе:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

Для каждой среды выполнения используется одна и та же панель. Запускайте сразу несколько сред, и переключатель в шапке будет перенаправлять каждую вкладку на нужную из них.

Создали собственного агента на основе SDK? Перехватчик отслеживает и его вызовы LLM. См. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Что вы получаете

- **Сессии и транскрипты**: что делал каждый агент, ход за ходом, с возможностью повтора
- **Стоимость и токены**: по среде выполнения, модели, сессии и дню, с флагами аномалий
- **Flow**: диаграмма в реальном времени, показывающая движение сообщений через каналы, модели и инструменты
- **Brain**: поток событий рассуждений и вызовов инструментов по мере их появления
- **Память и навыки**: файлы и навыки, которые фактически загрузила каждая среда выполнения
- **Здоровье и логи**: диск, память, частота ошибок, лимиты частоты запросов, живой поток логов
- **Оповещения**: лимиты бюджета, всплески ошибок, оффлайн-агенты, отправка в Slack, Discord, PagerDuty, Telegram, Email
- **Подтверждения (Approvals)**: приостанавливайте рискованные вызовы инструментов *до* их выполнения и подтверждайте их с телефона ([как это работает](docs/APPROVALS.md))

## Тарифы

| Тариф | Что включено | Цена |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, полная панель, только локально | $0 |
| **Starter** | Все остальные среды выполнения из списка выше, вид флота, облачная синхронизация | $9 за узел / месяц |
| **Pro** | Starter + управление: подтверждения, политики риска инструментов, оценки, обнаружение аномалий, оптимизатор затрат, экспорт OTel | $19 за узел / месяц |

Годовые тарифы, Enterprise и актуальные цены смотрите на
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключи лицензии для self-hosted
работают без облака (`clawmetry license`). Точное разделение бесплатных и платных
функций описано в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваши данные остаются на вашем компьютере

ClawMetry читает локальные файлы сессий и логи. Ничего не покидает ваш компьютер,
если вы не запустите `clawmetry connect`. Но даже тогда снимок данных шифруется
end-to-end ключом, который никогда не покидает ваш компьютер, и расшифровывается
в вашем браузере.

## Установка

```bash
pip install clawmetry     # затем: clawmetry
```

Или однострочник: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Требуется Python 3.8+ на macOS, Linux или Windows, а также хотя бы одна среда выполнения агента
на этой же машине. Инструкции для Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Документация

| | |
|---|---|
| [Совместимость сред выполнения](docs/compatibility.md) | Что читает каждый адаптер и как добавить свою среду выполнения |
| [Права доступа](docs/ENTITLEMENTS.md) | Бесплатно и платно, матрица тарифов, лицензионный CLI |
| [Подтверждения и политики](docs/APPROVALS.md) | Контроль перед выполнением, оценка риска, подтверждения с телефона |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Экспорт трасс куда угодно, приём OTLP откуда угодно |
| [Отслеживание SDK](docs/SDK_TRACKING.md) | Атрибуция стоимости для агентов, созданных вами самостоятельно |
| [Чат-каналы](docs/CHANNELS.md) | Адаптеры чатов, отображаемые во Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Изолированные (sandboxed) настройки NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтирование томов |
| [Архитектура](ARCHITECTURE.md) · [Разработка](docs/DEVELOPMENT.md) | Как это устроено внутри; запуск из исходного кода |
| [Телеметрия](docs/TELEMETRY.md) | Анонимные пинги при установке и открытии приложения, и как их отключить |

## Скриншоты

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: токены, сессии, состояние здоровья | **Brain**: живой поток событий агента |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: по моделям и сессиям | **Approvals**: контроль рискованных вызовов инструментов |

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

MIT · Создано [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
