<!-- i18n-src:dc34072b2955 -->
> Українська translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**Дивіться, як думає ваш агент.** Спостережуваність у реальному часі для **23 середовищ виконання AI-агентів**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex та ще 19 інших. Одна панель для всього вашого флоту агентів.

> 🌐 **Читати цією мовою:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

Одна команда. Без налаштувань. Автоматично визначає все.

```bash
pip install clawmetry && clawmetry
```

Відкривається за адресою **http://localhost:8900**. Без налаштувань: система знаходить середовища виконання агентів, які у вас вже є, читає їх у режимі лише для читання і нічого не змінює в тому, як вони працюють.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## Працює з 23 середовищами виконання агентів

**Безкоштовно у застосунку з відкритим кодом:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**У платному плані:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

Кожне середовище виконання отримує ту саму панель. Запускайте кілька одночасно, і перемикач у заголовку переналаштовує кожну вкладку під потрібне з них.

Створили власного агента на базі SDK замість цього? Перехоплювач відстежує і його виклики LLM теж. Дивіться [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## Що ви отримуєте

- **Сесії та транскрипти**: що робив кожен агент, крок за кроком, з можливістю відтворення
- **Вартість і токени**: за середовищем виконання, моделлю, сесією та днем, з позначками аномалій
- **Flow**: діаграма руху повідомлень у реальному часі через канали, моделі та інструменти
- **Brain**: потік подій міркувань і викликів інструментів у момент, коли вони відбуваються
- **Пам'ять і навички**: файли та навички, які фактично завантажило кожне середовище виконання
- **Стан і логи**: диск, пам'ять, частота помилок, ліміти запитів, потік логів у реальному часі
- **Сповіщення**: ліміти бюджету, сплески помилок, офлайн-агент, з маршрутизацією у Slack, Discord, PagerDuty, Telegram, Email
- **Затвердження**: призупиняйте ризиковані виклики інструментів *до* їх виконання і затверджуйте з телефону ([як](docs/APPROVALS.md))

## Ціни

| План | Що охоплює | Ціна |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw, повна панель, лише локально | $0 |
| **Starter** | Усі інші середовища виконання вище, огляд флоту, хмарна синхронізація | $9 за вузол / місяць |
| **Pro** | Starter + керування: затвердження, політики ризику інструментів, оцінювання, виявлення аномалій, оптимізатор витрат, експорт OTel | $19 за вузол / місяць |

Річні плани, Enterprise і актуальні ціни знаходяться на сторінці
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. Ключі ліцензії для самостійного розміщення
працюють без хмари (`clawmetry license`). Точний поділ безкоштовного/платного
описано в [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## Ваші дані залишаються на вашій машині

ClawMetry читає локальні файли сесій і логи. Нічого не покидає вашу машину, якщо
ви не запустите `clawmetry connect`. Навіть тоді знімок даних шифрується наскрізно
ключем, який ніколи не залишає вашу машину, і розшифровується у вашому браузері.

## Встановлення

```bash
pip install clawmetry     # then: clawmetry
```

Або однорядковою командою: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

Потрібен Python 3.8+ на macOS, Linux або Windows, і хоча б одне середовище виконання агента на
тій самій машині. Інструкції для Docker: [docs/DOCKER.md](docs/DOCKER.md).

## Документація

| | |
|---|---|
| [Сумісність середовищ виконання](docs/compatibility.md) | Що читає кожен адаптер і як додати середовище виконання |
| [Права доступу](docs/ENTITLEMENTS.md) | Безкоштовне проти платного, матриця рівнів, ліцензійний CLI |
| [Затвердження та політики](docs/APPROVALS.md) | Перевірка перед виконанням, оцінка ризику, затвердження з телефону |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | Експортуйте трейси куди завгодно, приймайте OTLP звідки завгодно |
| [Відстеження SDK](docs/SDK_TRACKING.md) | Атрибуція витрат для агентів, які ви створили самостійно |
| [Чат-канали](docs/CHANNELS.md) | Адаптери чатів, показані у Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Пісочниці для налаштувань NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | Образ, compose, монтування томів |
| [Архітектура](ARCHITECTURE.md) · [Розробка](docs/DEVELOPMENT.md) | Як це працює всередині; запуск із вихідного коду |
| [Телеметрія](docs/TELEMETRY.md) | Анонімні пінги встановлення та відкриття на робочому столі, і як їх вимкнути |

## Скріншоти

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: токени, сесії, стан | **Brain**: потік подій агента у реальному часі |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: за моделлю та сесією | **Approvals**: контроль ризикованих викликів інструментів |

Більше, за середовищем виконання: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
