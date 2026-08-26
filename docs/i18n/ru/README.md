<!-- i18n-src:c111f32e69a5 -->
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

**Смотрите, как думает ваш агент.** Наблюдаемость в реальном времени для **26 сред выполнения AI-агентов**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex и ещё 22. Единая панель для всего вашего флота агентов.

> 🌐 **Читать на других языках:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [ещё →](docs/i18n/)

Одна команда. Никакой настройки. Всё определяется автоматически.

```bash
pip install clawmetry && clawmetry
```

Открывается по адресу **http://localhost:8900**. Никакой настройки: приложение находит уже установленные у вас среды выполнения агентов, читает их в режиме "только чтение" и никак не влияет на их работу.

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## Работает с 26 средами выполнения агентов

**Бесплатно в open source приложении:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**По платному тарифу:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Для каждой среды выполнения используется одна и та же панель. Можно запускать несколько сразу, а переключатель в шапке заново привязывает каждую вкладку к выбранной среде.

Собрали собственного агента на базе SDK? Перехватчик отслеживает и его вызовы LLM. См. [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Что вы получаете

- **Сессии и транскрипты**: что делал каждый агент, шаг за шагом, с воспроизведением
- **Стоимость и токены**: по средам выполнения, моделям, сессиям и дням, с отметками аномалий
- **Flow**: живая диаграмма движения сообщений через каналы, модели и инструменты
- **Brain**: поток событий рассуждений и вызовов инструментов в реальном времени
- **Память и навыки**: файлы и навыки, которые реально загрузила каждая среда выполнения
- **Здоровье и логи**: диск, память, частота ошибок, лимиты запросов, живой поток логов
- **Оповещения**: лимиты бюджета, всплески ошибок, отключение агента, с маршрутизацией в Slack, Discord, PagerDuty, Telegram, Email
- **Подтверждения**: приостанавливайте рискованные вызовы инструментов *до* их выполнения и подтверждайте их с телефона ([как это работает](docs/APPROVALS.md))

## Тарифы

| Тариф | Что включено | Цена |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, полная панель, только локально | $0 |
| **Starter** | Все остальные среды выполнения из списка выше, обзор флота, синхронизация с облаком | $9 за узел / месяц |
| **Pro** | Starter + управление: подтверждения, политики риска инструментов, оценки (evals), обнаружение аномалий, оптимизатор затрат, экспорт OTel | $19 за узел / месяц |

Годовые тарифы, Enterprise и актуальные цифры смотрите на странице
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключи лицензии для
self-hosted работают без облака (`clawmetry license`). Точное разделение бесплатных и платных функций описано
в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваши данные остаются на вашей машине

ClawMetry читает локальные файлы сессий и логи. Ничего не покидает вашу машину, пока
вы не запустите `clawmetry connect`. Но даже тогда снимок данных шифруется сквозным шифрованием
с ключом, который никогда не покидает вашу машину, и расшифровывается в вашем браузере.

## Установка

```bash
pip install clawmetry     # затем: clawmetry
```

Или однострочник: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Требуется Python 3.8+ на macOS, Linux или Windows и хотя бы одна среда выполнения агентов на
той же машине. Инструкции по Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Документация

| | |
|---|---|
| [Совместимость сред выполнения](docs/compatibility.md) | Что читает каждый адаптер и как добавить новую среду выполнения |
| [Права доступа](docs/ENTITLEMENTS.md) | Бесплатно и платно, матрица тарифов, CLI лицензий |
| [Подтверждения и политики](docs/APPROVALS.md) | Проверка перед выполнением, оценка риска, подтверждения с телефона |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Экспорт трейсов куда угодно, приём OTLP откуда угодно |
| [Трекинг SDK](docs/SDK_TRACKING.md) | Атрибуция затрат для агентов, собранных вами самостоятельно |
| [Чат-каналы](docs/CHANNELS.md) | Чат-адаптеры, отображаемые во Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Изолированные (sandboxed) настройки NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтирование томов |
| [Архитектура](ARCHITECTURE.md) · [Разработка](docs/DEVELOPMENT.md) | Как всё устроено внутри; запуск из исходников |
| [Телеметрия](docs/TELEMETRY.md) | Анонимные пинги установки и открытия десктоп-приложения, и как их отключить |

## Скриншоты

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: токены, сессии, состояние системы | **Агенты** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
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

MIT · Разработано [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
