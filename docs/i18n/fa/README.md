<!-- i18n-src:bab48eec552f -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**نگاه کن که ایجنت‌ات چطور فکر می‌کند.** رصد بی‌درنگ برای **۱۴ زمان اجرای ایجنت هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۱۰ مورد دیگر. یک داشبورد برای کل ناوگان ایجنت‌های شما.

> 🌐 **این را به این زبان‌ها هم بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر →](docs/i18n/)

یک دستور. بدون تنظیمات. همه‌چیز را خودکار تشخیص می‌دهد.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود و تمام.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## با ۱۴ زمان اجرای ایجنت کار می‌کند

ClawMetry به‌عنوان ابزار رصد OpenClaw شروع شد و اکنون **کل ناوگان ایجنت‌های شما** را در یک داشبورد اندازه‌گیری می‌کند و هر زمان اجرا را روی دستگاه شما به‌صورت خودکار تشخیص می‌دهد:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw و NemoClaw در برنامه متن‌باز رایگان هستند؛ سایر زمان‌های اجرا با ClawMetry Cloud یا لایسنس Pro خودمیزبان فعال می‌شوند. زمان اجرا را از هدر تغییر دهید و هر تب — هزینه، توکن‌ها، ابزارها، ترِیس‌ها — به آن زمان اجرا محدود می‌شود. برای تقسیم دقیق رایگان/پولی، ماتریس ردیف‌ها، ساختار `/api/entitlement` و CLI مربوط به `clawmetry license` به **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** مراجعه کنید.

## چه چیزی به دست می‌آورید

- **Flow** — نمودار زنده و متحرک که نشان می‌دهد پیام‌ها چگونه از میان کانال‌ها، مغز، ابزارها و بازگشت جریان دارند
- **Overview** — بررسی سلامت، نقشه حرارتی فعالیت، شمار نشست‌ها، اطلاعات مدل
- **Usage** — پیگیری توکن و هزینه با تفکیک روزانه/هفتگی/ماهانه
- **Sessions** — نشست‌های فعال ایجنت به همراه مدل، توکن‌ها، آخرین فعالیت
- **Crons** — کارهای زمان‌بندی‌شده با وضعیت، اجرای بعدی، مدت زمان
- **Logs** — پخش زنده لاگ‌ها با رنگ‌بندی
- **Memory** — مرور SOUL.md، MEMORY.md، AGENTS.md، یادداشت‌های روزانه
- **Transcripts** — رابط کاربری حباب چت برای خواندن تاریخچه نشست‌ها
- **Alerts** — سقف بودجه، محرک‌های نرخ خطا، تشخیص آفلاین‌بودن ایجنت؛ مسیریابی به Slack، Discord، PagerDuty، Telegram، ایمیل
- **Approvals** — حذف‌های مخرب، force pushها، جهش‌های پایگاه‌داده، sudo، نصب بسته‌ها و تماس‌های شبکه را پشت یک تأیید یک‌کلیکی محدود کنید

## اسکرین‌شات‌ها

### 🧠 Brain — جریان زنده رویدادهای ایجنت
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — مصرف توکن و خلاصه نشست
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — فید بی‌درنگ فراخوانی ابزارها
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفکیک هزینه بر اساس مدل و نشست
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — مرورگر فایل‌های فضای کاری
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — وضعیت امنیتی و لاگ ممیزی
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — سقف بودجه، محرک‌های نرخ خطا، وب‌هوک به Slack / Discord / PagerDuty / ایمیل
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — فراخوانی‌های ابزار پرریسک را پشت تأیید دستی محدود کنید؛ قوانین حفاظتی مبتنی بر سیاست
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**مسدودسازی پیش از اجرا برای Claude Code** — یک دستور، یک هوک PreToolUse
نصب می‌کند که فراخوانی‌های ابزار منطبق را *پیش از* اجرا متوقف می‌کند و منتظر
تصمیم شما می‌ماند (یک ضربه از گوشی‌تان با فعال‌بودن
[اعلان‌های فوری ابری](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

یک رد فقط همان یک فراخوانی ابزار را مسدود می‌کند؛ ایجنت نشست خود را حفظ
می‌کند و می‌تواند رویکرد دیگری را امتحان کند. تأیید از گوشی شما، درخواست
مجوز خود Claude Code را رد می‌کند (شما قبلاً پاسخ داده‌اید). ابزارهای
منطبق‌نشده حدود ۴۰ میلی‌ثانیه هزینه دارند و به جریان مجوز معمول Claude Code
باز می‌گردند. همچنین وقتی خود Claude Code منتظر شماست (اعلان‌های
`permission_prompt` / `idle_prompt`) یک اعلان فوری روی گوشی دریافت می‌کنید.

## نصب

**یک‌خطی (پیشنهادی):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**از سورس:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## توسعه فرانت‌اند v2

اپلیکیشن React نسخه v2 در `frontend/` قرار دارد و زمانی که سرور Flask با
فعال‌بودن v2 اجرا شود، در مسیر `/v2` سرو می‌شود.

هنگام توسعه از دو ترمینال استفاده کنید:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

آدرس `http://localhost:5173/v2/` را باز کنید. Vite درخواست‌های `/api` را به
`http://localhost:8900` پروکسی می‌کند، بنابراین اپلیکیشن React می‌تواند بدون
تنظیمات اضافی CORS با سرور محلی Flask ارتباط برقرار کند.

برای ساخت باندلی که همراه بسته Python منتشر می‌شود:

```bash
cd frontend
npm run build
```

باندل نسخه تولید در `clawmetry/static/v2/dist/` نوشته می‌شود.

## سازگاری زمان اجرا / ایجنت

ClawMetry بسیاری از زمان‌های اجرای ایجنت هوش مصنوعی را رصد می‌کند، نه فقط
OpenClaw. هر زمان اجرای غیر از OpenClaw یک آداپتور خوانش اختصاصی دارد که
قالب بومی نشست آن را به شکل‌های یکپارچه ClawMetry ترجمه می‌کند؛ دیمون آن‌ها
را به همان مخزن DuckDB + اسنپ‌شات ابری وارد می‌کند، با برچسب زمان اجرا، و تب
بازپخش نشست وقتی بیش از یکی موجود باشد یک **تعویض‌کننده زمان اجرا** نشان
می‌دهد. برای ماتریس کامل + راهنمای افزودن زمان‌های اجرا به
[`docs/compatibility.md`](docs/compatibility.md) و برای مقدمه خانواده
OpenClaw به [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) مراجعه کنید.

| زمان اجرا / ایجنت | وضعیت | یادداشت‌ها |
|---|---|---|
| **OpenClaw** | بومی | زمان اجرای مرجع، به‌صورت خودکار تشخیص داده می‌شود |
| **PicoClaw** | آداپتور بتا | JSONL مسطح `providers.Message` (`~/.picoclaw/workspace/sessions`). تاریخچه، مدل، فراخوانی ابزار. |
| **NanoClaw** | آداپتور بتا | SQLite به‌ازای هر نشست (`data/v2-sessions`). تاریخچه + شمار پیام‌ها. |
| **Hermes** | آداپتور بتا | SQLite در `~/.hermes/state.db`. تاریخچه، مدل، توکن/هزینه. |
| **Claude Code** | آداپتور بتا | JSONL در `~/.claude/projects/.../<id>.jsonl`. تاریخچه، مدل، فراخوانی ابزار + تفکر، مصرف توکن. |
| **Codex** | آداپتور بتا | JSONL rollout در `~/.codex/sessions/...`. تاریخچه، مدل، فراخوانی ابزار، مصرف توکن. |
| **Cursor** | آداپتور بتا | SQLite `state.vscdb`. تاریخچه چت/کامپوزر، مدل. |
| **Aider** | آداپتور بتا | `.aider.chat.history.md` به‌ازای هر پروژه. تاریخچه، مدل، شمار توکن. |
| **Goose** | آداپتور بتا | SQLite در `~/.local/share/goose`. تاریخچه، مدل، فراخوانی ابزار، مجموع توکن. |
| **opencode** | آداپتور بتا | SQLite در `~/.local/share/opencode`. تاریخچه، مدل، فراخوانی ابزار، توکن + هزینه. |
| **Qwen Code** | آداپتور بتا | JSONL در `~/.qwen/projects/.../chats`. تاریخچه، مدل، فراخوانی ابزار، مصرف توکن. |
| **Pi** | آداپتور بتا | JSONL در `~/.pi/agent/sessions`. تاریخچه، مدل، فراخوانی ابزار، توکن + هزینه. |
| **Deep Agents** | آداپتور بتا | SQLite در `~/.deepagents/.state/sessions.db`. تاریخچه، مدل، فراخوانی ابزار، توکن + هزینه. |

«آداپتور بتا» یعنی ClawMetry یک خواننده برای قالب واقعی روی‌دیسک آن زمان
اجرا ارائه می‌دهد که هرکدام روی یک نصب واقعی روی یک دستگاه واقعی ساخته و
تأیید شده‌اند (به `tests/fixtures/runtimes/<rt>/` مراجعه کنید). آداپتورها
فقط‌خواندنی هستند؛ هرکدام صادقانه بیان می‌کنند که زمان اجرایشان واقعاً چه
چیزی ذخیره می‌کند (مثلاً PicoClaw/NanoClaw/Cursor هزینه توکن را روی دیسک
نمی‌نویسند). وقتی چند زمان اجرا روی یک نود در حال اجرا باشند، تعویض‌کننده
زمان اجرا نمای نشست‌ها را برای بررسی دقیق به یکی محدود می‌کند.

## پیگیری هر ایجنت SDK — انتساب هزینه خارج‌از-حلقه

همه زمان‌های اجرای بالا نشست‌ها را روی دیسک می‌نویسند. **ایجنت تولیدی** خودتان
— همانی که با OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B،
یا یک حلقه ساده `httpx` ساخته‌اید — این کار را نمی‌کند. اینترسپتور بدون
تنظیمات ClawMetry همچنان با پچ‌زدن به `httpx`/`requests` فراخوانی‌های LLM آن
را (هزینه، توکن‌ها، تأخیر، خطاها) ثبت می‌کند:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا متغیر محیطی `CLAWMETRY_SOURCE=support-agent`) هر فراخوانی
را با یک **منبع نام‌گذاری‌شده** برچسب می‌زند، بنابراین هر محصولی که اجرا
می‌کنید به‌عنوان یک ردیف مستقل و قابل‌انتساب از نظر هزینه در کارت
**🔌 منابع خارج‌از-حلقه** داشبورد در تب Overview ظاهر می‌شود — فراخوانی‌ها،
ارائه‌دهندگان، تأخیر، نرخ خطا به‌ازای هر ایجنت. اگر منبعی تنظیم نشده باشد؟
فراخوانی‌ها همچنان ثبت می‌شوند؛ فقط کارت پنهان می‌ماند.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

این همان لایه داده‌ای است که آداپتورهای زمان اجرا آن را تغذیه می‌کنند
(DuckDB ← اسنپ‌شات ابری)، پس منابع خارج‌از-حلقه هم مانند بقیه با رمزنگاری
سرتاسری با داشبورد ابری همگام‌سازی می‌شوند.

## OpenTelemetry — بدون وابستگی به ارائه‌دهنده خاص، ترِیس‌های خود را به هرکجا بفرستید

ClawMetry در هر دو جهت با **OpenTelemetry** صحبت می‌کند و از **قراردادهای
معنایی GenAI** استفاده می‌کند، پس ترِیس‌های ایجنت شما هرگز به یک ابزار قفل
نمی‌شوند.

**صادرات** هر نشست — فراخوانی‌های LLM، ابزارها، زیرایجنت‌ها، توکن‌ها، هزینه —
به‌صورت اسپن‌های OTLP/HTTP GenAI به هر گردآورنده‌ای (Datadog، Grafana،
Honeycomb، یا OTel Collector خودتان):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

هدرهای احراز هویت و بازه نظرسنجی متغیرهای محیطی اختیاری هستند:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**دریافت** — گیرنده داخلی OTLP ترِیس‌ها و متریک‌های هرچیز دیگری را در
`/v1/traces` و `/v1/metrics` می‌پذیرد (برای دریافت protobuf از
`pip install clawmetry[otel]` استفاده کنید).

هم داشبورد بدون تنظیمات و محلی‌محور ClawMetry را دارید **و** داده‌های خود را
در هر بک‌اندی که تیم شما از قبل اجرا می‌کند — بدون قفل‌شدگی، بدون نیاز به
نصب ایجنت دوم.

## پیکربندی

بیشتر افراد به هیچ تنظیماتی نیاز ندارند. ClawMetry فضای کاری، لاگ‌ها،
نشست‌ها و کرون‌های شما را به‌صورت خودکار تشخیص می‌دهد.

اگر نیاز به سفارشی‌سازی دارید:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

همه گزینه‌ها: `clawmetry --help`

## کانال‌های پشتیبانی‌شده

ClawMetry فعالیت زنده هر کانال OpenClaw که پیکربندی کرده‌اید را نشان
می‌دهد. فقط کانال‌هایی که واقعاً در `openclaw.json` شما تنظیم شده‌اند در
نمودار Flow ظاهر می‌شوند؛ کانال‌های پیکربندی‌نشده به‌صورت خودکار مخفی
می‌شوند.

روی هر گره کانال در Flow کلیک کنید تا نمای حباب چت زنده با شمار پیام‌های
ورودی/خروجی را ببینید.

| کانال | وضعیت | پاپ‌آپ زنده | یادداشت‌ها |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ کامل | ✅ | پیام‌ها، آمار، بازآوری هر ۱۰ ثانیه |
| 💬 **iMessage** | ✅ کامل | ✅ | مستقیماً `~/Library/Messages/chat.db` را می‌خواند |
| 💚 **WhatsApp** | ✅ کامل | ✅ | از طریق WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ کامل | ✅ | از طریق signal-cli |
| 🟣 **Discord** | ✅ کامل | ✅ | تشخیص گیلد + کانال |
| 🟪 **Slack** | ✅ کامل | ✅ | تشخیص فضای کاری + کانال |
| 🌐 **Webchat** | ✅ کامل | ✅ | نشست‌های رابط کاربری وب داخلی |
| 📡 **IRC** | ✅ کامل | ✅ | رابط کاربری حباب به سبک ترمینال |
| 🍏 **BlueBubbles** | ✅ کامل | ✅ | iMessage از طریق REST API مربوط به BlueBubbles |
| 🔵 **Google Chat** | ✅ کامل | ✅ | از طریق وب‌هوک‌های Chat API |
| 🟣 **MS Teams** | ✅ کامل | ✅ | از طریق پلاگین بات Teams |
| 🔷 **Mattermost** | ✅ کامل | ✅ | چت تیمی خودمیزبان |
| 🟩 **Matrix** | ✅ کامل | ✅ | غیرمتمرکز، پشتیبانی از E2EE |
| 🟢 **LINE** | ✅ کامل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ کامل | ✅ | پیام‌های مستقیم غیرمتمرکز NIP-04 |
| 🟣 **Twitch** | ✅ کامل | ✅ | چت از طریق اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ کامل | ✅ | اشتراک رویداد از طریق WebSocket |
| 🔵 **Zalo** | ✅ کامل | ✅ | Zalo Bot API |

> **تشخیص خودکار:** ClawMetry فایل `~/.openclaw/openclaw.json` شما را
> می‌خواند و فقط کانال‌هایی را که واقعاً پیکربندی کرده‌اید نمایش می‌دهد.
> نیازی به تنظیم دستی نیست.

## استقرار با Docker

می‌خواهید ClawMetry را در یک کانتینر اجرا کنید؟ مشکلی نیست! 🐳

**شروع سریع با Docker:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**نمونه Docker Compose:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **توجه:** هنگام اجرا در Docker، پوشه‌های داده + لاگ ایجنت خود را مانت کنید
> (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) تا ClawMetry بتواند تنظیمات
> شما را به‌صورت خودکار تشخیص دهد.

## پیش‌نیازها

- Python 3.8+
- Flask (به‌صورت خودکار از طریق pip نصب می‌شود)
- یک زمان اجرای ایجنت هوش مصنوعی روی همان دستگاه: OpenClaw، NVIDIA
  NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code،
  Aider، NanoClaw، PicoClaw، Pi یا Deep Agents (یا حجم‌های مانت‌شده برای
  Docker)
- Linux یا macOS

## پشتیبانی NemoClaw / OpenShell

ClawMetry به‌صورت خودکار [NemoClaw](https://github.com/NVIDIA/NemoClaw) را
تشخیص می‌دهد — پوشش امنیتی سازمانی NVIDIA برای OpenClaw که ایجنت‌ها را درون
کانتینرهای ایزوله‌شده OpenShell اجرا می‌کند.

در بیشتر موارد هیچ تنظیم اضافه‌ای لازم نیست. دیمون همگام‌سازی فایل‌های نشست
را چه در `~/.openclaw/` روی هاست و چه درون یک کانتینر OpenShell به‌صورت
خودکار کشف می‌کند.

### چگونه کار می‌کند

ClawMetry به دو روش NemoClaw را تشخیص می‌دهد:

۱. **تشخیص باینری** — بررسی وجود CLI مربوط به `nemoclaw` و اجرای
`nemoclaw status` برای دریافت اطلاعات سندباکس
۲. **تشخیص کانتینر** — اسکن کانتینرهای در حال اجرای Docker به‌دنبال
تصاویر `openshell`، `nemoclaw` یا `ghcr.io/nvidia/`، سپس خواندن نشست‌ها از
طریق مانت‌های حجمی یا `docker cp`

فایل‌های نشست همگام‌سازی‌شده از کانتینرهای NemoClaw با متادیتای
`runtime=nemoclaw` و `container_id` در داشبورد ابری برچسب می‌خورند، پس
می‌توانید در نگاه اول آن‌ها را از نشست‌های استاندارد OpenClaw تشخیص دهید.

### تنظیمات پیشنهادی: دیمون همگام‌سازی روی HOST

برای بهترین تجربه، دیمون همگام‌سازی ClawMetry را روی **دستگاه هاست** (نه
درون سندباکس) اجرا کنید. این کار محدودیت‌های سیاست شبکه NemoClaw را دور
می‌زند.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

دیمون همگام‌سازی به‌صورت خودکار نشست‌های درون هر کانتینر OpenShell در حال
اجرا را پیدا می‌کند.

### اختیاری: نام صریح سندباکس

اگر تشخیص خودکار کار نکرد، ClawMetry را به سندباکس درست هدایت کنید:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### اجرا درون سندباکس (پیشرفته)

اگر ناچارید دیمون همگام‌سازی را **درون** سندباکس OpenShell اجرا کنید، این
قانون خروجی را به سیاست شبکه NemoClaw خود اضافه کنید تا بتواند به API
دریافت ClawMetry دسترسی داشته باشد:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

با این دستور اعمال کنید:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### پورت‌ها و نقاط پایانی

| نقطه پایانی | پورت | پروتکل | ضروری |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | بله (دیمون همگام‌سازی ← ابر) |
| `localhost:8900` | 8900 | HTTP | بله (رابط داشبورد محلی) |
| سوکت Docker (`/var/run/docker.sock`) | — | سوکت Unix | برای کشف نشست کانتینر |

دیمون همگام‌سازی فقط تماس‌های خروجی HTTPS به `ingest.clawmetry.com` برقرار
می‌کند. هیچ پورت ورودی لازم نیست.

---

## استقرار ابری

برای تونل‌های SSH، پروکسی معکوس و Docker به **[راهنمای تست ابری](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** مراجعه کنید.

## تست

این پروژه با BrowserStack تست می‌شود.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## تله‌متری

ClawMetry اولین باری که CLI مربوط به `clawmetry` را روی یک دستگاه جدید اجرا
می‌کنید، یک پینگ ناشناس «اجرای اول» به
`https://app.clawmetry.com/api/install` ارسال می‌کند. از این برای شمارش
نصب‌ها استفاده می‌کنیم (تنها معیار بازاریابی که برای یک پروژه متن‌باز داریم)
و برای یادگیری اینکه کاربران ما کدام چارچوب‌های ایجنت را نصب کرده‌اند.

**دقیقاً یک POST به‌ازای هر نصب**، شامل:

| فیلد | نمونه | چرا |
|---|---|---|
| `install_id` | UUID تصادفی ذخیره‌شده در `~/.clawmetry/install_id` | حذف تکرار؛ به ایمیل یا api_key شما مرتبط نیست |
| `version` | `0.12.167` | اینکه چه نسخه‌هایی در دنیای واقعی استفاده می‌شوند |
| `os` / `os_version` | `Darwin` / `25.3.0` | اولویت‌های پشتیبانی پلتفرم |
| `python` | `3.11.15` | ماتریس پشتیبانی نسخه Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | اینکه باید با کدام ایجنت‌ها ادغام شویم |
| `is_ci` / `ci_provider` | `true` / `github_actions` | جداسازی نصب‌های انسانی از نویز CI |

**آنچه ارسال نمی‌کنیم**: IP (سرور ابری کد کشور را در سمت سرور از روی درخواست
استخراج می‌کند، سپس IP را دور می‌ریزد)، نام هاست، نام کاربری، مسیر فضای
کاری، محتوای فایل، api_key شما، ایمیل شما، هیچ‌چیز شخصی یا مختص فضای کاری.
بار سیم‌ارسالی در
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) قابل ممیزی است.

**خروج از تله‌متری** (هرکدام از این‌ها به‌طور دائمی آن را غیرفعال می‌کند):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

یک خرابی شبکه در اینجا هرگز اجرای `clawmetry` را مسدود نمی‌کند؛ پینگ
fire-and-forget روی یک ریسه دیمون با مهلت ۳ ثانیه‌ای است.

## تاریخچه ستاره‌ها

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## لایسنس

MIT

---

<p align="center">
  <strong>🦞 نگاه کن که ایجنت‌ات چطور فکر می‌کند</strong><br>
  <sub>ساخته‌شده توسط <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · بخشی از اکوسیستم <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
