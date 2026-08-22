<!-- i18n-src:6795052055e2 -->
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

**ذهن عامل خود را ببینید.** قابلیت مشاهده در لحظه (real‑time) برای **۲۶ زمان اجرای عامل هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۲۲ مورد دیگر. یک داشبورد برای کل ناوگان عامل‌های شما.

> 🌐 **این را به این زبان‌ها هم بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر →](docs/i18n/)

یک دستور. بدون تنظیمات. تشخیص خودکار همه‌چیز.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود. بدون تنظیمات: زمان‌های اجرای عاملی را که از قبل روی سیستم دارید پیدا می‌کند،
آن‌ها را فقط به‌صورت خواندنی می‌خواند و هیچ تغییری در نحوه اجرای آن‌ها ایجاد نمی‌کند.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## سازگار با ۲۶ زمان اجرای عامل

**رایگان در برنامه متن‌باز:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**در پلن پولی:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

هر زمان اجرا از همان داشبورد استفاده می‌کند. چند مورد را همزمان اجرا کنید و کلید تعویض در هدر
هر تب را به‌سمت یکی از آن‌ها بازتنظیم می‌کند.

عامل خودتان را روی یک SDK ساخته‌اید؟ این interceptor فراخوانی‌های LLM آن را هم ردیابی می‌کند.
به [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) مراجعه کنید.

## چه چیزی به‌دست می‌آورید

- **نشست‌ها و رونوشت‌ها**: اینکه هر عامل چه کاری انجام داده، نوبت‌به‌نوبت، با قابلیت پخش مجدد (replay)
- **هزینه و توکن**: به‌ازای هر زمان اجرا، مدل، نشست و روز، همراه با پرچم‌های ناهنجاری
- **Flow**: نمودار زنده حرکت پیام‌ها میان کانال‌ها، مدل‌ها و ابزارها
- **Brain**: جریان رویدادهای استدلال و فراخوانی ابزار، همان لحظه‌ای که رخ می‌دهند
- **حافظه و مهارت‌ها**: فایل‌ها و مهارت‌هایی که هر زمان اجرا واقعاً بارگذاری کرده
- **سلامت و لاگ‌ها**: دیسک، حافظه، نرخ خطا، محدودیت نرخ، جریان زنده لاگ
- **هشدارها**: سقف بودجه، جهش‌های خطا، آفلاین‌شدن عامل، ارسال به Slack، Discord، PagerDuty، Telegram، ایمیل
- **تأییدها (Approvals)**: توقف فراخوانی‌های ابزار پرریسک *پیش از* اجرا و تأیید آن‌ها از گوشی خود ([نحوه کار](docs/APPROVALS.md))

## قیمت‌گذاری

| پلن | چه چیزی را پوشش می‌دهد | قیمت |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose، داشبورد کامل، فقط محلی | ۰ دلار |
| **Starter** | تمام زمان‌های اجرای دیگر بالا، نمای ناوگان، همگام‌سازی ابری | ۹ دلار به‌ازای هر نود / ماه |
| **Pro** | Starter + حاکمیت (governance): تأییدها، سیاست‌های ریسک ابزار، ارزیابی‌ها، تشخیص ناهنجاری، بهینه‌ساز هزینه، خروجی OTel | ۱۹ دلار به‌ازای هر نود / ماه |

پلن‌های سالانه، Enterprise و اعداد فعلی در
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** موجود است. کلیدهای مجوز خوداستقرار (self‑hosted)
بدون نیاز به ابر کار می‌کنند (`clawmetry license`). تفکیک دقیق رایگان/پولی
در [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) آمده است.

## داده‌های شما روی دستگاه خودتان می‌ماند

ClawMetry فایل‌های نشست و لاگ‌های محلی را می‌خواند. چیزی از دستگاه شما خارج نمی‌شود مگر آنکه
`clawmetry connect` را اجرا کنید. حتی در آن صورت هم، اسنپ‌شات به‌صورت سرتاسر رمزگذاری‌شده (end‑to‑end encrypted)
با کلیدی است که هرگز از دستگاه شما خارج نمی‌شود، و در مرورگر شما رمزگشایی می‌شود.

## نصب

```bash
pip install clawmetry     # سپس: clawmetry
```

یا این دستور تک‌خطی: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

نیازمند Python نسخه ۳.۸ به بالا روی macOS، Linux یا Windows است، و حداقل یک زمان اجرای عامل روی
همان دستگاه. راهنمای Docker: [docs/DOCKER.md](docs/DOCKER.md).

## مستندات

| | |
|---|---|
| [سازگاری زمان‌های اجرا](docs/compatibility.md) | هر آداپتور چه چیزی می‌خواند، و چگونه یک زمان اجرا اضافه کنیم |
| [Entitlements](docs/ENTITLEMENTS.md) | رایگان در برابر پولی، ماتریس ردیف‌ها، CLI مجوز |
| [تأییدها و سیاست‌ها](docs/APPROVALS.md) | دروازه‌بانی پیش از اجرا، امتیازدهی ریسک، تأیید از گوشی |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | خروجی trace به هر جا، دریافت OTLP از هر منبعی |
| [ردیابی SDK](docs/SDK_TRACKING.md) | انتساب هزینه برای عامل‌هایی که خودتان ساخته‌اید |
| [کانال‌های چت](docs/CHANNELS.md) | آداپتورهای چتی که در Flow نمایش داده می‌شوند |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | راه‌اندازی‌های sandbox‑شده NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | ایمیج، compose، mount حجم‌ها |
| [معماری](ARCHITECTURE.md) · [توسعه](docs/DEVELOPMENT.md) | نحوه کارکرد داخلی؛ اجرا از سورس |
| [تله‌متری](docs/TELEMETRY.md) | پینگ‌های ناشناس نصب و باز شدن دسکتاپ، و نحوه خاموش کردن آن‌ها |

## اسکرین‌شات‌ها

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: توکن‌ها، نشست‌ها، سلامت | **Brain**: جریان زنده رویدادهای عامل |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: بر اساس مدل و نشست | **Approvals**: دروازه‌بانی فراخوانی‌های ابزار پرریسک |

موارد بیشتر، به‌ازای هر زمان اجرا: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
