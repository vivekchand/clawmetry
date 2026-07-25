<!-- i18n-src:8f42d460a973 -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**فکر کردن ایجنت خود را ببینید.** قابلیت مشاهده بلادرنگ برای **۱۴ ران‌تایم ایجنت هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۱۰ مورد دیگر. یک داشبورد برای کل ناوگان ایجنت‌های شما.

> 🌐 **این را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر ←](docs/i18n/)

یک دستور. بدون پیکربندی. همه‌چیز را به‌طور خودکار تشخیص می‌دهد.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود و کار تمام است.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## با ۱۴ ران‌تایم ایجنت کار می‌کند

ClawMetry به‌عنوان قابلیت مشاهده برای OpenClaw شروع شد و اکنون **کل ناوگان ایجنت‌های شما** را در یک داشبورد اندازه‌گیری می‌کند و هر ران‌تایم روی دستگاه شما را به‌طور خودکار تشخیص می‌دهد:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw و NemoClaw در اپلیکیشن متن‌باز رایگان هستند؛ سایر ران‌تایم‌ها با ClawMetry Cloud یا لایسنس Pro خودمیزبان فعال می‌شوند. ران‌تایم‌ها را از هدر تغییر دهید و هر تب — هزینه، توکن‌ها، ابزارها، ترِیس‌ها — به آن ران‌تایم محدود می‌شود. برای تقسیم دقیق رایگان/پولی، ماتریس رده‌ها، ساختار `/api/entitlement` و CLI مربوط به `clawmetry license`، به **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** مراجعه کنید.

## چه چیزی به‌دست می‌آورید

- **Flow** — نمودار متحرک زنده که پیام‌های در حال جریان از میان کانال‌ها، مغز، ابزارها و بازگشت آن‌ها را نشان می‌دهد
- **Overview** — بررسی سلامت، نقشه حرارتی فعالیت، شمارش نشست‌ها، اطلاعات مدل
- **Usage** — پیگیری توکن و هزینه با تفکیک روزانه/هفتگی/ماهانه
- **Sessions** — نشست‌های فعال ایجنت به همراه مدل، توکن‌ها، آخرین فعالیت
- **Crons** — کارهای زمان‌بندی‌شده با وضعیت، اجرای بعدی، مدت زمان
- **Logs** — پخش زنده لاگ‌ها با کدگذاری رنگی
- **Memory** — مرور SOUL.md، MEMORY.md، AGENTS.md، یادداشت‌های روزانه
- **Transcripts** — رابط کاربری حباب چت برای خواندن تاریخچه نشست‌ها
- **Alerts** — سقف بودجه، محرک‌های نرخ خطا، تشخیص آفلاین بودن ایجنت؛ مسیریابی به Slack، Discord، PagerDuty، Telegram، ایمیل
- **Approvals** — مسدود کردن حذف‌های مخرب، فورس پوش‌ها، تغییرات پایگاه داده، sudo، نصب بسته‌ها، تماس‌های شبکه‌ای پشت یک تأیید یک‌کلیکی

## اسکرین‌شات‌ها

### 🧠 Brain — جریان زنده رویدادهای ایجنت
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — مصرف توکن و خلاصه نشست
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — فید بلادرنگ فراخوانی ابزارها
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفکیک هزینه بر اساس مدل و نشست
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — مرورگر فایل‌های فضای کاری
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — وضعیت امنیتی و لاگ حسابرسی
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — سقف بودجه، محرک‌های نرخ خطا، وب‌هوک به Slack / Discord / PagerDuty / ایمیل
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — مسدودسازی فراخوانی‌های پرریسک ابزار پشت تأیید دستی؛ قوانین حفاظتی مبتنی بر سیاست
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## نصب

**نصب تک‌خطی (توصیه‌شده):**
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

اپلیکیشن React نسخه v2 در `frontend/` قرار دارد و وقتی سرور Flask با فعال بودن v2
راه‌اندازی شود، در آدرس `/v2` سرو می‌شود.

هنگام توسعه از دو ترمینال استفاده کنید:

```bash
# ترمینال ۱: Flask API/سرور روی :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ترمینال ۲: سرور توسعه Vite روی :5173
cd frontend
nvm use
npm ci
npm run dev
```

آدرس `http://localhost:5173/v2/` را باز کنید. Vite درخواست‌های `/api` را به
`http://localhost:8900` پروکسی می‌کند، بنابراین اپلیکیشن React می‌تواند بدون
تنظیمات اضافی CORS با سرور محلی Flask ارتباط برقرار کند.

برای ساخت باندلی که همراه بسته پایتون منتشر می‌شود:

```bash
cd frontend
npm run build
```

باندل نهایی در `clawmetry/static/v2/dist/` نوشته می‌شود.

## سازگاری ران‌تایم/ایجنت

ClawMetry بسیاری از ران‌تایم‌های ایجنت هوش مصنوعی را مشاهده می‌کند، نه فقط OpenClaw. هر ران‌تایم غیر از OpenClaw دارای یک آداپتور خواننده اختصاصی است که فرمت بومی نشست آن را به شکل‌های یکپارچه ClawMetry ترجمه می‌کند؛ دیمون آن‌ها را به همان مخزن DuckDB + اسنپ‌شات ابری وارد می‌کند، با برچسب ران‌تایم، و تب بازپخش نشست وقتی بیش از یکی وجود دارد یک **سوییچر ران‌تایم** نشان می‌دهد. برای ماتریس کامل + راهنمای افزودن ران‌تایم‌ها به [`docs/compatibility.md`](docs/compatibility.md) و برای مقدمه‌ای بر خانواده OpenClaw به [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) مراجعه کنید.

| ران‌تایم/ایجنت | وضعیت | یادداشت‌ها |
|---|---|---|
| **OpenClaw** | بومی | ران‌تایم مرجع، تشخیص خودکار |
| **PicoClaw** | آداپتور بتا | JSONL مسطح از نوع `providers.Message` (`~/.picoclaw/workspace/sessions`). رونوشت‌ها، مدل، فراخوانی ابزار. |
| **NanoClaw** | آداپتور بتا | SQLite به‌ازای هر نشست (`data/v2-sessions`). رونوشت‌ها + تعداد پیام‌ها. |
| **Hermes** | آداپتور بتا | SQLite در `~/.hermes/state.db`. رونوشت‌ها، مدل، توکن‌ها/هزینه. |
| **Claude Code** | آداپتور بتا | JSONL در `~/.claude/projects/.../<id>.jsonl`. رونوشت‌ها، مدل، فراخوانی ابزار + تفکر، مصرف توکن. |
| **Codex** | آداپتور بتا | Rollout JSONL در `~/.codex/sessions/...`. رونوشت‌ها، مدل، فراخوانی ابزار، مصرف توکن. |
| **Cursor** | آداپتور بتا | SQLite با نام `state.vscdb`. رونوشت‌های چت/کامپوزر، مدل. |
| **Aider** | آداپتور بتا | `.aider.chat.history.md` به‌ازای هر پروژه. رونوشت‌ها، مدل، شمارش توکن. |
| **Goose** | آداپتور بتا | SQLite در `~/.local/share/goose`. رونوشت‌ها، مدل، فراخوانی ابزار، مجموع توکن‌ها. |
| **opencode** | آداپتور بتا | SQLite در `~/.local/share/opencode`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Qwen Code** | آداپتور بتا | JSONL در `~/.qwen/projects/.../chats`. رونوشت‌ها، مدل، فراخوانی ابزار، مصرف توکن. |
| **Pi** | آداپتور بتا | JSONL در `~/.pi/agent/sessions`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Deep Agents** | آداپتور بتا | SQLite در `~/.deepagents/.state/sessions.db`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |

منظور از «آداپتور بتا» این است که ClawMetry یک خواننده برای فرمت واقعی روی دیسک آن ران‌تایم ارائه می‌دهد، که هرکدام روی یک نصب واقعی روی یک دستگاه واقعی ساخته و تأیید شده‌اند (به `tests/fixtures/runtimes/<rt>/` مراجعه کنید). آداپتورها فقط‌خواندنی هستند؛ هرکدام درباره آنچه ران‌تایمشان واقعاً ذخیره می‌کند صادق‌اند (مثلاً PicoClaw/NanoClaw/Cursor هزینه توکن را روی دیسک نمی‌نویسند). وقتی چند ران‌تایم روی یک نود اجرا می‌شوند، سوییچر ران‌تایم نمای نشست‌ها را به یکی محدود می‌کند تا بررسی دقیق و تمیزی داشته باشید.

## پیگیری هر ایجنت SDK — انتساب هزینه خارج از حلقه

تمام ران‌تایم‌های بالا نشست‌ها را روی دیسک می‌نویسند. **ایجنت تولیدی** خودتان — همانی که با OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B یا یک حلقه ساده `httpx` ساخته‌اید — این کار را نمی‌کند. رهگیر بدون‌پیکربندی ClawMetry همچنان فراخوانی‌های LLM آن را (هزینه، توکن‌ها، تأخیر، خطاها) با مانکی‌پچ کردن `httpx`/`requests` ثبت می‌کند:

```python
import clawmetry.track            # فعال‌سازی رهگیر
clawmetry.track.set_source("support-agent")   # نام‌گذاری این محصول

# ...ایجنت شما به‌طور معمول اجرا می‌شود؛ اکنون هر فراخوانی LLM ثبت + منتسب می‌شود.
```

`set_source()` (یا متغیر محیطی `CLAWMETRY_SOURCE=support-agent`) هر فراخوانی را با یک **منبع نام‌دار** برچسب‌گذاری می‌کند، بنابراین هر محصولی که اجرا می‌کنید به‌عنوان یک ردیف مستقل و قابل انتساب هزینه در کارت **🔌 منابع خارج از حلقه** داشبورد در Overview نمایش داده می‌شود — فراخوانی‌ها، ارائه‌دهندگان، تأخیر، نرخ خطا به‌ازای هر ایجنت. منبعی تنظیم نشده؟ فراخوانی‌ها همچنان ثبت می‌شوند؛ فقط کارت مخفی می‌ماند.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

این همان لایه داده‌ای است که آداپتورهای ران‌تایم را تغذیه می‌کند (DuckDB → اسنپ‌شات ابری)، بنابراین منابع خارج از حلقه هم مانند بقیه موارد، به‌صورت رمزنگاری‌شده سرتاسری، با ابر همگام‌سازی می‌شوند.

## OpenTelemetry — بدون وابستگی به ارائه‌دهنده، ترِیس‌های خود را به هر جا ارسال کنید

ClawMetry در هر دو جهت با استفاده از **قراردادهای معنایی GenAI** با **OpenTelemetry** صحبت می‌کند، بنابراین ترِیس‌های ایجنت شما هرگز به یک ابزار خاص قفل نمی‌شوند.

**صادرات** هر نشست — فراخوانی‌های LLM، ابزارها، زیرایجنت‌ها، توکن‌ها، هزینه — به‌عنوان اسپن‌های GenAI روی OTLP/HTTP به هر کالکتوری (Datadog، Grafana، Honeycomb یا OTel Collector خودتان):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# معادل آن:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

هدرهای احراز هویت و بازه نظرسنجی متغیرهای محیطی اختیاری هستند:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # هدرهای HTTP اضافی
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # ثانیه (پیش‌فرض ۶۰)
```

**دریافت** — گیرنده داخلی OTLP، ترِیس‌ها و متریک‌ها را از هر منبع دیگری در `/v1/traces` و `/v1/metrics` می‌پذیرد (`pip install clawmetry[otel]` برای دریافت protobuf).

شما هم داشبورد بدون‌پیکربندی و محلی‌محور ClawMetry را دارید **و هم** داده‌های خود را در هر بک‌اندی که تیم شما از قبل اجرا می‌کند — بدون قفل‌شدگی، بدون نیاز به نصب ایجنت دوم.

## پیکربندی

بیشتر افراد به هیچ پیکربندی‌ای نیاز ندارند. ClawMetry فضای کاری، لاگ‌ها، نشست‌ها و کرون‌های شما را به‌طور خودکار تشخیص می‌دهد.

اگر نیاز به شخصی‌سازی دارید:

```bash
clawmetry --port 9000              # پورت سفارشی (پیش‌فرض: 8900)
clawmetry --host 127.0.0.1         # فقط به localhost متصل شود
clawmetry --workspace ~/mybot      # مسیر فضای کاری سفارشی
clawmetry --name "Alice"           # نام شما در نمایش Flow
```

همه گزینه‌ها: `clawmetry --help`

## کانال‌های پشتیبانی‌شده

ClawMetry فعالیت زنده را برای هر کانال OpenClaw که پیکربندی کرده‌اید نشان می‌دهد. فقط کانال‌هایی که واقعاً در `openclaw.json` شما تنظیم شده‌اند در نمودار Flow ظاهر می‌شوند؛ کانال‌های پیکربندی‌نشده به‌طور خودکار مخفی می‌شوند.

روی هر گره کانال در Flow کلیک کنید تا یک نمای حباب چت زنده به همراه شمارش پیام‌های ورودی/خروجی ببینید.

| کانال | وضعیت | پاپ‌آپ زنده | یادداشت‌ها |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ کامل | ✅ | پیام‌ها، آمار، بازخوانی ۱۰ ثانیه‌ای |
| 💬 **iMessage** | ✅ کامل | ✅ | مستقیماً `~/Library/Messages/chat.db` را می‌خواند |
| 💚 **WhatsApp** | ✅ کامل | ✅ | از طریق WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ کامل | ✅ | از طریق signal-cli |
| 🟣 **Discord** | ✅ کامل | ✅ | تشخیص گیلد + کانال |
| 🟪 **Slack** | ✅ کامل | ✅ | تشخیص فضای کاری + کانال |
| 🌐 **Webchat** | ✅ کامل | ✅ | نشست‌های رابط کاربری وب داخلی |
| 📡 **IRC** | ✅ کامل | ✅ | رابط حباب به سبک ترمینال |
| 🍏 **BlueBubbles** | ✅ کامل | ✅ | iMessage از طریق BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ کامل | ✅ | از طریق وب‌هوک‌های Chat API |
| 🟣 **MS Teams** | ✅ کامل | ✅ | از طریق پلاگین بات Teams |
| 🔷 **Mattermost** | ✅ کامل | ✅ | چت تیمی خودمیزبان |
| 🟩 **Matrix** | ✅ کامل | ✅ | غیرمتمرکز، پشتیبانی از E2EE |
| 🟢 **LINE** | ✅ کامل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ کامل | ✅ | پیام‌های خصوصی NIP-04 غیرمتمرکز |
| 🟣 **Twitch** | ✅ کامل | ✅ | چت از طریق اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ کامل | ✅ | اشتراک رویداد WebSocket |
| 🔵 **Zalo** | ✅ کامل | ✅ | Zalo Bot API |

> **تشخیص خودکار:** ClawMetry فایل `~/.openclaw/openclaw.json` شما را می‌خواند و فقط کانال‌هایی را که واقعاً پیکربندی کرده‌اید رندر می‌کند. نیازی به تنظیم دستی نیست.

## استقرار با Docker

می‌خواهید ClawMetry را در یک کانتینر اجرا کنید؟ مشکلی نیست! 🐳

**شروع سریع با Docker:**

```bash
# ساخت ایمیج
docker build -t clawmetry .

# اجرا با تنظیمات پیش‌فرض
docker run -p 8900:8900 clawmetry

# یا مانت کردن دایرکتوری داده ایجنت خود (نمونه: ~/.openclaw مربوط به OpenClaw)
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

> **نکته:** هنگام اجرا در Docker، دایرکتوری‌های داده + لاگ ایجنت خود (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) را مانت کنید تا ClawMetry بتواند تنظیمات شما را به‌طور خودکار تشخیص دهد.

## پیش‌نیازها

- Python 3.8+
- Flask (به‌طور خودکار از طریق pip نصب می‌شود)
- یک ران‌تایم ایجنت هوش مصنوعی روی همان دستگاه: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi یا Deep Agents (یا وُلوم‌های مانت‌شده برای Docker)
- Linux یا macOS

## پشتیبانی از NemoClaw / OpenShell

ClawMetry به‌طور خودکار [NemoClaw](https://github.com/NVIDIA/NemoClaw) را تشخیص می‌دهد — پوشش امنیتی سازمانی NVIDIA برای OpenClaw که ایجنت‌ها را داخل کانتینرهای ایزوله‌شده OpenShell اجرا می‌کند.

در بیشتر موارد نیازی به پیکربندی اضافی نیست. دیمون همگام‌سازی فایل‌های نشست را چه در `~/.openclaw/` روی هاست و چه داخل یک کانتینر OpenShell به‌طور خودکار کشف می‌کند.

### نحوه کار

ClawMetry به دو روش NemoClaw را تشخیص می‌دهد:

۱. **تشخیص باینری** — بررسی وجود CLI با نام `nemoclaw` و اجرای `nemoclaw status` برای دریافت اطلاعات سندباکس
۲. **تشخیص کانتینر** — اسکن کانتینرهای در حال اجرای Docker برای ایمیج‌های `openshell`، `nemoclaw` یا `ghcr.io/nvidia/`، سپس خواندن نشست‌ها از طریق مانت‌های وُلوم یا `docker cp`

فایل‌های نشست همگام‌سازی‌شده از کانتینرهای NemoClaw با متادیتای `runtime=nemoclaw` و `container_id` در داشبورد ابری برچسب‌گذاری می‌شوند، بنابراین می‌توانید آن‌ها را با یک نگاه از نشست‌های استاندارد OpenClaw تشخیص دهید.

### تنظیمات پیشنهادی: دیمون همگام‌سازی روی هاست

برای بهترین تجربه، دیمون همگام‌سازی ClawMetry را روی **دستگاه هاست** (نه داخل سندباکس) اجرا کنید. این کار از محدودیت‌های سیاست شبکه NemoClaw جلوگیری می‌کند.

```bash
# روی هاست (خارج از سندباکس)
pip install clawmetry
clawmetry connect
clawmetry sync
```

دیمون همگام‌سازی به‌طور خودکار نشست‌های داخل هر کانتینر OpenShell در حال اجرا را پیدا می‌کند.

### اختیاری: نام صریح سندباکس

اگر تشخیص خودکار کار نکرد، ClawMetry را به سندباکس درست هدایت کنید:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### اجرا داخل سندباکس (پیشرفته)

اگر باید دیمون همگام‌سازی را **داخل** سندباکس OpenShell اجرا کنید، این قانون خروجی را به سیاست شبکه NemoClaw خود اضافه کنید تا بتواند به API دریافت داده ClawMetry دسترسی پیدا کند:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

اعمال کنید با:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### پورت‌ها و اندپوینت‌ها

| اندپوینت | پورت | پروتکل | مورد نیاز |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | بله (دیمون همگام‌سازی ← ابر) |
| `localhost:8900` | 8900 | HTTP | بله (رابط کاربری داشبورد محلی) |
| سوکت Docker (`/var/run/docker.sock`) | — | سوکت Unix | برای کشف نشست‌های کانتینر |

دیمون همگام‌سازی فقط تماس‌های خروجی HTTPS به `ingest.clawmetry.com` برقرار می‌کند. هیچ پورت ورودی‌ای لازم نیست.

---

## استقرار ابری

برای تونل‌های SSH، پروکسی معکوس و Docker، به **[راهنمای تست ابری](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** مراجعه کنید.

## تست

این پروژه با BrowserStack تست شده است.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## تله‌متری

ClawMetry اولین باری که CLI با نام `clawmetry` را روی یک دستگاه جدید اجرا می‌کنید،
یک پینگ ناشناس "اجرای اول" به `https://app.clawmetry.com/api/install`
ارسال می‌کند. ما از این داده برای شمارش نصب‌ها (تنها معیار بازاریابی که برای
یک پروژه متن‌باز داریم) و برای فهمیدن اینکه کاربرانمان کدام فریمورک‌های
ایجنت را نصب کرده‌اند استفاده می‌کنیم.

**دقیقاً یک POST به‌ازای هر نصب**، شامل:

| فیلد | نمونه | دلیل |
|---|---|---|
| `install_id` | UUID تصادفی ذخیره‌شده در `~/.clawmetry/install_id` | حذف تکرار؛ به ایمیل یا api_key شما مرتبط نیست |
| `version` | `0.12.167` | اینکه چه نسخه‌هایی در حال استفاده هستند |
| `os` / `os_version` | `Darwin` / `25.3.0` | اولویت‌های پشتیبانی پلتفرم |
| `python` | `3.11.15` | ماتریس پشتیبانی نسخه پایتون |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | اینکه با کدام ایجنت‌ها باید ادغام بعدی را انجام دهیم |
| `is_ci` / `ci_provider` | `true` / `github_actions` | جدا کردن نصب‌های انسانی از نویز CI |

**آنچه ارسال نمی‌کنیم**: آی‌پی (سرور ابری کد کشور را سمت سرور از روی درخواست
استخراج می‌کند و سپس آی‌پی را دور می‌ریزد)، نام میزبان، نام کاربری، مسیر
فضای کاری، محتوای فایل، api_key شما، ایمیل شما، هرچیز شخصی یا مختص فضای
کاری. بار داده (wire payload) در
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) قابل حسابرسی است.

**غیرفعال‌سازی** (هرکدام از این‌ها آن را به‌طور دائمی غیرفعال می‌کند):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # به‌ازای هر شل
export DO_NOT_TRACK=1                          # استاندارد بین‌ابزاری W3C
touch ~/.clawmetry/notelemetry                 # نشانگر فایل دائمی
```

خرابی شبکه در اینجا هرگز مانع اجرای `clawmetry` نمی‌شود — پینگ به‌صورت
fire-and-forget روی یک ترد دیمون با تایم‌اوت ۳ ثانیه‌ای انجام می‌شود.

## تاریخچه ستاره‌ها

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## مجوز

MIT

---

<p align="center">
  <strong>🦞 فکر کردن ایجنت خود را ببینید</strong><br>
  <sub>ساخته‌شده توسط <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · بخشی از اکوسیستم <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
