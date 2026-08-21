<!-- i18n-src:dc34072b2955 -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**فکر کردن ایجنت خود را ببینید.** رصد بلادرنگ برای **۲۳ محیط اجرای ایجنت هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۱۹ مورد دیگر. یک داشبورد برای کل ناوگان ایجنت‌های شما.

> 🌐 **این را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر →](docs/i18n/)

یک دستور. بدون پیکربندی. تشخیص خودکار همه‌چیز.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود. بدون پیکربندی: محیط‌های اجرای ایجنتی که از قبل دارید را پیدا می‌کند، آن‌ها را فقط برای خواندن می‌خواند، و هیچ چیزی را در نحوه اجرای آن‌ها تغییر نمی‌دهد.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## با ۲۳ محیط اجرای ایجنت کار می‌کند

**رایگان در برنامه متن‌باز:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**در طرح پولی:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

هر محیط اجرا همان داشبورد را دریافت می‌کند. چند مورد را همزمان اجرا کنید و کلید انتخاب در هدر، هر تب را دوباره به یکی از آن‌ها محدود می‌کند.

ایجنت خودتان را روی یک SDK ساخته‌اید؟ رهگیر (interceptor) فراخوانی‌های LLM آن را هم ردیابی می‌کند. به [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) مراجعه کنید.

## چه چیزی دریافت می‌کنید

- **جلسات و رونوشت‌ها**: هر ایجنت چه کاری انجام داده، نوبت به نوبت، با قابلیت پخش مجدد
- **هزینه و توکن‌ها**: به تفکیک محیط اجرا، مدل، جلسه و روز، همراه با پرچم‌های ناهنجاری
- **Flow**: نمودار زنده جابه‌جایی پیام‌ها میان کانال‌ها، مدل‌ها و ابزارها
- **Brain**: جریان رویدادهای استدلال و فراخوانی ابزار، لحظه به لحظه
- **حافظه و مهارت‌ها**: فایل‌ها و مهارت‌هایی که هر محیط اجرا واقعاً بارگذاری کرده است
- **سلامت و لاگ‌ها**: دیسک، حافظه، نرخ خطا، محدودیت نرخ، جریان زنده لاگ
- **هشدارها**: سقف بودجه، جهش خطا، آفلاین شدن ایجنت، ارسال به Slack، Discord، PagerDuty، Telegram، ایمیل
- **تأییدیه‌ها (Approvals)**: توقف فراخوانی‌های ابزار پرریسک *پیش از* اجرا و تأیید از گوشی خود ([چگونه](docs/APPROVALS.md))

## قیمت‌گذاری

| طرح | شامل چه چیزی می‌شود | قیمت |
|---|---|---|
| **رایگان** | OpenClaw + NVIDIA NemoClaw، داشبورد کامل، فقط محلی | ۰ دلار |
| **Starter** | تمام محیط‌های اجرای دیگر بالا، نمای ناوگان، همگام‌سازی ابری | ۹ دلار برای هر گره در ماه |
| **Pro** | Starter + حاکمیت: تأییدیه‌ها، سیاست‌های ریسک ابزار، ارزیابی‌ها، تشخیص ناهنجاری، بهینه‌ساز هزینه، خروجی OTel | ۱۹ دلار برای هر گره در ماه |

طرح‌های سالانه، Enterprise و ارقام فعلی در
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** موجود است. کلیدهای مجوز میزبانی‌شده روی سیستم شخصی
بدون نیاز به ابر کار می‌کنند (`clawmetry license`). تفکیک دقیق رایگان/پولی
در [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) آمده است.

## داده‌های شما روی دستگاه شما می‌ماند

ClawMetry فایل‌های جلسه و لاگ‌های محلی را می‌خواند. تا زمانی که
`clawmetry connect` را اجرا نکنید، چیزی از دستگاه شما خارج نمی‌شود. حتی در آن صورت هم، تصویر لحظه‌ای (snapshot) با رمزنگاری سرتاسر (end-to-end)
با کلیدی که هرگز از دستگاه شما خارج نمی‌شود رمزگذاری شده، و در مرورگر شما رمزگشایی می‌شود.

## نصب

```bash
pip install clawmetry     # سپس: clawmetry
```

یا دستور یک‌خطی: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

به Python 3.8+ روی macOS، Linux یا Windows نیاز دارد، و حداقل یک محیط اجرای ایجنت روی
همان دستگاه. راهنمای Docker: [docs/DOCKER.md](docs/DOCKER.md).

## مستندات

| | |
|---|---|
| [سازگاری محیط‌های اجرا](docs/compatibility.md) | هر آداپتور چه چیزی می‌خواند، و چگونه یک محیط اجرا اضافه کنیم |
| [مجوزها (Entitlements)](docs/ENTITLEMENTS.md) | رایگان در برابر پولی، جدول سطوح، CLI مجوز |
| [تأییدیه‌ها و سیاست‌ها](docs/APPROVALS.md) | دروازه‌بانی پیش از اجرا، امتیازدهی ریسک، تأیید از گوشی |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صادرات ردگیری‌ها (traces) به هر جا، دریافت OTLP از هر منبع |
| [ردگیری SDK](docs/SDK_TRACKING.md) | انتساب هزینه برای ایجنت‌هایی که خودتان ساخته‌اید |
| [کانال‌های چت](docs/CHANNELS.md) | آداپتورهای چتی که در Flow نمایش داده می‌شوند |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | راه‌اندازی‌های ایزوله‌شده NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | ایمیج، compose، اتصال حجم‌ها |
| [معماری](ARCHITECTURE.md) · [توسعه](docs/DEVELOPMENT.md) | نحوه عملکرد داخلی؛ اجرا از سورس |
| [تله‌متری](docs/TELEMETRY.md) | پینگ‌های ناشناس نصب و باز شدن دسکتاپ، و نحوه خاموش کردن آن‌ها |

## اسکرین‌شات‌ها

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: توکن‌ها، جلسات، سلامت | **Brain**: جریان زنده رویدادهای ایجنت |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **هزینه**: به تفکیک مدل و جلسه | **تأییدیه‌ها**: دروازه‌بانی فراخوانی‌های ابزار پرریسک |

بیشتر، به تفکیک محیط اجرا: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## تاریخچه ستاره‌ها

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## مجوز

MIT · ساخته شده توسط [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
