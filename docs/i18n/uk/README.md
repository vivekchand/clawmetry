<!-- i18n-src:c111f32e69a5 -->
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

**Побачте, як мислить ваш агент.** Спостережуваність у реальному часі для **26 середовищ виконання AI-агентів**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex та ще 22 інших. Одна панель приладів для всього вашого флоту агентів.

> 🌐 **Читати цією мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Одна команда. Нуль налаштувань. Автоматичне визначення всього.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**. Нуль налаштувань: система знаходить середовища виконання агентів, які у вас вже є, читає їх у режимі "тільки читання" й нічого не змінює в тому, як вони працюють.

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## Працює з 26 середовищами виконання агентів

**Безкоштовно у застосунку з відкритим кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**У платному плані:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

Кожне середовище виконання отримує ту саму панель приладів. Запускайте кілька одночасно, і перемикач у заголовку переналаштовує кожну вкладку на потрібне.

Створили власного агента на базі SDK замість готового середовища? Перехоплювач відстежує й його виклики LLM. Дивіться [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Що ви отримуєте

- **Сесії та стенограми**: що робив кожен агент, крок за кроком, із можливістю повторного перегляду
- **Вартість і токени**: за середовищем виконання, моделлю, сесією та днем, з позначками аномалій
- **Flow**: діаграма руху повідомлень через канали, моделі та інструменти в реальному часі
- **Brain**: потік подій міркувань і викликів інструментів у момент їх виникнення
- **Пам'ять і навички**: файли та навички, які фактично завантажило кожне середовище виконання
- **Стан і логи**: диск, пам'ять, рівень помилок, обмеження швидкості, потік логів у реальному часі
- **Сповіщення**: ліміти бюджету, сплески помилок, офлайн-стан агента, з маршрутизацією в Slack, Discord, PagerDuty, Telegram, Email
- **Погодження**: призупиняйте ризиковані виклики інструментів *до* їх виконання й погоджуйте з телефону ([як](docs/APPROVALS.md))

## Ціни

| План | Що покриває | Ціна |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, повна панель приладів, тільки локально | $0 |
| **Starter** | Усі інші середовища виконання вище, огляд флоту, синхронізація з хмарою | $9 за вузол / місяць |
| **Pro** | Starter + управління: погодження, політики ризику інструментів, оцінювання, виявлення аномалій, оптимізатор витрат, експорт OTel | $19 за вузол / місяць |

Річні плани, Enterprise та актуальні ціни доступні на
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключі ліцензії для self-hosted
працюють без хмари (`clawmetry license`). Точний розподіл безкоштовних/платних функцій
у [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваші дані залишаються на вашому пристрої

ClawMetry читає локальні файли сесій і логи. Нічого не залишає ваш пристрій, якщо
ви не виконаєте `clawmetry connect`. Навіть тоді знімок даних наскрізно зашифровано
ключем, який ніколи не залишає вашу машину, і розшифровується у вашому браузері.

## Встановлення

```bash
pip install clawmetry     # then: clawmetry
```

Або одним рядком: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Потрібен Python 3.8+ на macOS, Linux або Windows, а також щонайменше одне середовище виконання агента
на тій самій машині. Інструкції для Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Документація

| | |
|---|---|
| [Сумісність середовищ виконання](docs/compatibility.md) | Що читає кожен адаптер і як додати середовище виконання |
| [Права доступу](docs/ENTITLEMENTS.md) | Безкоштовно проти платно, матриця рівнів, CLI ліцензії |
| [Погодження та політики](docs/APPROVALS.md) | Перевірка перед виконанням, оцінка ризику, погодження з телефону |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Експорт трасувань будь-куди, приймання OTLP звідусіль |
| [Відстеження SDK](docs/SDK_TRACKING.md) | Атрибуція вартості для агентів, які ви створили самостійно |
| [Чат-канали](docs/CHANNELS.md) | Адаптери чатів, показані у Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Пісочниці для NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтування томів |
| [Архітектура](ARCHITECTURE.md) · [Розробка](docs/DEVELOPMENT.md) | Як це працює всередині; запуск із вихідного коду |
| [Телеметрія](docs/TELEMETRY.md) | Анонімні пінги при встановленні та відкритті десктопного застосунку, і як їх вимкнути |

## Скріншоти

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: токени, сесії, стан | **Агенти** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: за моделлю та сесією | **Approvals**: блокування ризикованих викликів інструментів |

Більше, за середовищами виконання: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
