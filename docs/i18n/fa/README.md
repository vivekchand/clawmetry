<!-- i18n-src:c111f32e69a5 -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ببینید عامل هوشمند شما چگونه فکر می‌کند.** رصد بلادرنگ برای **۲۶ محیط اجرای عامل هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۲۲ مورد دیگر. یک داشبورد برای کل ناوگان عامل‌های شما.

> 🌐 **این را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر ←](docs/i18n/)

یک دستور. بدون پیکربندی. تشخیص خودکار همه‌چیز.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود. بدون پیکربندی: محیط‌های اجرای عامل‌هایی را که از قبل دارید پیدا می‌کند، آن‌ها را فقط برای خواندن می‌خواند و هیچ چیزی در نحوه‌ی اجرای آن‌ها تغییر نمی‌دهد.

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## با ۲۶ محیط اجرای عامل کار می‌کند

**رایگان در برنامه‌ی متن‌باز:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**در طرح پولی:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

هر محیط اجرا همان داشبورد را دریافت می‌کند. چند مورد را همزمان اجرا کنید و کلید انتخاب در سربرگ، هر تب را روی یکی از آن‌ها دوباره تنظیم می‌کند.

عامل خودتان را روی یک SDK ساخته‌اید؟ رهگیر (interceptor) فراخوانی‌های LLM آن را هم پیگیری می‌کند. ببینید [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## چه چیزی به دست می‌آورید

- **نشست‌ها و رونوشت‌ها**: هر عامل چه کاری انجام داد، نوبت به نوبت، همراه با پخش مجدد
- **هزینه و توکن‌ها**: بر اساس محیط اجرا، مدل، نشست و روز، همراه با پرچم‌های ناهنجاری
- **جریان (Flow)**: نمودار زنده‌ی حرکت پیام‌ها میان کانال‌ها، مدل‌ها و ابزارها
- **مغز (Brain)**: جریان رویدادهای استدلال و فراخوانی ابزار، همان‌گونه که رخ می‌دهد
- **حافظه و مهارت‌ها**: فایل‌ها و مهارت‌هایی که هر محیط اجرا واقعاً بارگذاری کرده است
- **سلامت و گزارش‌ها (logs)**: دیسک، حافظه، نرخ خطا، محدودیت‌های نرخ، جریان زنده‌ی گزارش
- **هشدارها**: سقف بودجه، جهش خطا، آفلاین‌شدن عامل، ارسال به Slack، Discord، PagerDuty، Telegram، ایمیل
- **تأییدها**: توقف فراخوانی‌های پرریسک ابزار *پیش از* اجرا و تأیید از گوشی خود ([چگونه](docs/APPROVALS.md))

## قیمت‌گذاری

| طرح | چه چیزی را پوشش می‌دهد | قیمت |
|---|---|---|
| **رایگان** | OpenClaw + NVIDIA NemoClaw + Goose، داشبورد کامل، فقط محلی | ۰ دلار |
| **استارتر** | تمام محیط‌های اجرای دیگر بالا، نمای ناوگان، همگام‌سازی ابری | ۹ دلار به ازای هر گره در ماه |
| **Pro** | استارتر + حاکمیت: تأییدها، سیاست‌های ریسک ابزار، ارزیابی‌ها، تشخیص ناهنجاری، بهینه‌ساز هزینه، خروجی OTel | ۱۹ دلار به ازای هر گره در ماه |

طرح‌های سالانه، Enterprise و ارقام فعلی در
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** موجود است. کلیدهای مجوز خودمیزبانی
بدون ابر کار می‌کنند (`clawmetry license`). تفکیک دقیق رایگان/پولی
در [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) آمده است.

## داده‌های شما روی دستگاه خودتان می‌ماند

ClawMetry فایل‌های نشست و گزارش‌های محلی را می‌خواند. تا زمانی که
`clawmetry connect` را اجرا نکنید، چیزی از دستگاه شما خارج نمی‌شود. حتی در آن صورت هم، عکس‌لحظه‌ای (snapshot) با رمزنگاری سرتاسر
با کلیدی که هرگز از دستگاه شما خارج نمی‌شود رمزنگاری شده و در مرورگر شما رمزگشایی می‌شود.

## نصب

```bash
pip install clawmetry     # سپس: clawmetry
```

یا دستور یک‌خطی: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

به Python 3.8+ روی macOS، Linux یا Windows، و حداقل یک محیط اجرای عامل روی
همان دستگاه نیاز دارد. راهنمای Docker: [docs/DOCKER.md](docs/DOCKER.md).

## مستندات

| | |
|---|---|
| [سازگاری محیط‌های اجرا](docs/compatibility.md) | هر تطبیق‌دهنده چه می‌خواند، و چگونه یک محیط اجرا اضافه کنیم |
| [استحقاق‌ها (Entitlements)](docs/ENTITLEMENTS.md) | رایگان در برابر پولی، ماتریس ردیف‌ها، CLI مجوز |
| [تأییدها و سیاست‌ها](docs/APPROVALS.md) | دروازه‌بانی پیش از اجرا، امتیازدهی ریسک، تأیید از گوشی |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ردهای (traces) خود را هرجا خواستید صادر کنید، OTLP را از هر جایی دریافت کنید |
| [ردیابی SDK](docs/SDK_TRACKING.md) | انتساب هزینه برای عامل‌هایی که خودتان ساخته‌اید |
| [کانال‌های چت](docs/CHANNELS.md) | تطبیق‌دهنده‌های چتی که در Flow نمایش داده می‌شوند |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | راه‌اندازی‌های ایزوله‌شده‌ی NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | تصویر (image)، compose، اتصال حجم‌ها (volume mounts) |
| [معماری](ARCHITECTURE.md) · [توسعه](docs/DEVELOPMENT.md) | نحوه‌ی عملکرد داخلی؛ اجرا از سورس |
| [تله‌متری](docs/TELEMETRY.md) | پینگ‌های ناشناس نصب و باز شدن دسکتاپ، و نحوه‌ی غیرفعال کردن آن‌ها |

## اسکرین‌شات‌ها

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **نمای کلی**: توکن‌ها، نشست‌ها، سلامت | **عامل‌ها** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **هزینه**: بر اساس مدل و نشست | **تأییدها**: دروازه‌بانی فراخوانی‌های پرریسک ابزار |

بیشتر، به ازای هر محیط اجرا: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## تاریخچه‌ی ستاره‌ها

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
