<!-- i18n-src:6795052055e2 -->
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

**Побачте, як думає ваш агент.** Спостережуваність у реальному часі для **26 середовищ виконання ШІ-агентів**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex та ще 22. Одна панель для всього вашого флоту агентів.

> 🌐 **Читати цією мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Одна команда. Нуль налаштувань. Автоматичне визначення всього.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**. Нуль налаштувань: програма знаходить середовища виконання агентів,
які у вас уже є, читає їх лише для перегляду й нічого не змінює в тому, як вони працюють.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Працює з 26 середовищами виконання агентів

**Безкоштовно у застосунку з відкритим кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**У платному тарифі:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

Кожне середовище виконання отримує однакову панель. Запускайте декілька одночасно, і перемикач у заголовку
переналаштовує кожну вкладку на одне з них.

Створили власного агента на базі SDK? Перехоплювач також відстежує його виклики LLM.
Дивіться [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Що ви отримуєте

- **Сесії та транскрипти**: що робив кожен агент, хід за ходом, із повтором
- **Вартість і токени**: за середовищем виконання, моделлю, сесією та днем, із позначками аномалій
- **Flow**: діаграма руху повідомлень через канали, моделі та інструменти в реальному часі
- **Brain**: потік подій міркувань і викликів інструментів у міру їх появи
- **Пам'ять і навички**: файли та навички, які фактично завантажило кожне середовище виконання
- **Стан і журнали**: диск, пам'ять, частота помилок, обмеження швидкості, потік журналів у реальному часі
- **Сповіщення**: ліміти бюджету, сплески помилок, офлайн-агент, надсилаються у Slack, Discord, PagerDuty, Telegram, Email
- **Затвердження**: призупиняйте ризиковані виклики інструментів *до* їх виконання і затверджуйте з телефону ([як](docs/APPROVALS.md))

## Ціни

| Тариф | Що покриває | Ціна |
|---|---|---|
| **Безкоштовний** | OpenClaw + NVIDIA NemoClaw + Goose, повна панель, лише локально | $0 |
| **Starter** | Усі інші середовища виконання вище, огляд флоту, синхронізація з хмарою | $9 за вузол/місяць |
| **Pro** | Starter + керування: затвердження, політики ризику інструментів, оцінювання, виявлення аномалій, оптимізатор витрат, експорт OTel | $19 за вузол/місяць |

Річні тарифи, Enterprise і актуальні ціни доступні на
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключі ліцензії для самостійного розміщення
працюють без хмари (`clawmetry license`). Точний поділ безкоштовних/платних функцій описано
в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваші дані залишаються на вашій машині

ClawMetry читає локальні файли сесій і журнали. Нічого не залишає вашу машину, якщо
ви не запустите `clawmetry connect`. Навіть тоді знімок даних наскрізно зашифрований
ключем, який ніколи не залишає вашу машину, і розшифровується у вашому браузері.

## Встановлення

```bash
pip install clawmetry     # потім: clawmetry
```

Або в один рядок: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Потрібен Python 3.8+ на macOS, Linux або Windows, і принаймні одне середовище виконання агента
на тій самій машині. Інструкції для Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Документація

| | |
|---|---|
| [Сумісність середовищ виконання](docs/compatibility.md) | Що читає кожен адаптер і як додати середовище виконання |
| [Права доступу](docs/ENTITLEMENTS.md) | Безкоштовне vs платне, матриця тарифів, CLI ліцензії |
| [Затвердження та політики](docs/APPROVALS.md) | Перевірка перед виконанням, оцінка ризику, затвердження з телефону |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Експортуйте трейси будь-куди, приймайте OTLP звідусіль |
| [Відстеження SDK](docs/SDK_TRACKING.md) | Атрибуція вартості для агентів, які ви створили самостійно |
| [Чат-канали](docs/CHANNELS.md) | Чат-адаптери, показані у Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Ізольовані (sandboxed) налаштування NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтування томів |
| [Архітектура](ARCHITECTURE.md) · [Розробка](docs/DEVELOPMENT.md) | Як це працює всередині; запуск із вихідного коду |
| [Телеметрія](docs/TELEMETRY.md) | Анонімні пінги встановлення та відкриття на десктопі, і як їх вимкнути |

## Знімки екрана

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: токени, сесії, стан | **Brain**: потік подій агента в реальному часі |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Вартість**: за моделлю та сесією | **Затвердження**: контроль ризикованих викликів інструментів |

Більше знімків, за середовищем виконання: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
