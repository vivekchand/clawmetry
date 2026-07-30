<!-- i18n-src:9a05336fbdc1 -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ببینید عامل شما چگونه فکر می‌کند.** رصدپذیری بلادرنگ برای **۱۴ ران‌تایم عامل هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۱۰ مورد دیگر. یک داشبورد برای کل ناوگان عامل‌های شما.

> 🌐 **این را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر →](docs/i18n/)

یک دستور. بدون تنظیمات. تشخیص خودکار همه چیز.

```bash
pip install clawmetry && clawmetry
```

در آدرس **http://localhost:8900** باز می‌شود و کارتان تمام است.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## با ۱۴ ران‌تایم عامل کار می‌کند

ClawMetry به عنوان ابزار رصدپذیری برای OpenClaw شروع شد و اکنون **کل ناوگان عامل‌های شما** را در یک داشبورد اندازه‌گیری می‌کند و هر ران‌تایم را روی دستگاه شما به‌طور خودکار تشخیص می‌دهد:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw و NemoClaw در برنامه متن‌باز رایگان هستند؛ ران‌تایم‌های دیگر با ClawMetry Cloud یا یک مجوز Pro خودمیزبان فعال می‌شوند. ران‌تایم را از هدر تغییر دهید و هر تب، هزینه، توکن‌ها، ابزارها، ترِیس‌ها، دوباره روی همان ران‌تایم محدود می‌شود. برای تقسیم دقیق رایگان/پولی، جدول سطوح، ساختار `/api/entitlement` و CLI مربوط به `clawmetry license` به **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** مراجعه کنید.

## چه چیزی به دست می‌آورید

- **Flow** — نمودار انیمیشنی زنده که جریان پیام‌ها را از میان کانال‌ها، مغز، ابزارها و بازگشت نشان می‌دهد
- **Overview** — بررسی سلامت، نقشه حرارتی فعالیت، شمار نشست‌ها، اطلاعات مدل
- **Usage** — پیگیری توکن و هزینه با تفکیک روزانه/هفتگی/ماهانه
- **Sessions** — نشست‌های فعال عامل با مدل، توکن‌ها، آخرین فعالیت
- **Crons** — کارهای زمان‌بندی‌شده با وضعیت، اجرای بعدی، مدت زمان
- **Logs** — پخش زنده لاگ‌ها با رنگ‌بندی
- **Memory** — مرور SOUL.md، MEMORY.md، AGENTS.md، یادداشت‌های روزانه
- **Transcripts** — رابط کاربری حباب‌گفتگو برای خواندن تاریخچه نشست‌ها
- **Alerts** — سقف بودجه، محرک‌های نرخ خطا، تشخیص آفلاین‌بودن عامل؛ مسیردهی به Slack، Discord، PagerDuty، Telegram، Email
- **Approvals** — قرار دادن حذف‌های مخرب، فورس‌پوش‌ها، تغییرات پایگاه‌داده، sudo، نصب بسته‌ها، تماس‌های شبکه پشت یک تأیید تک‌کلیکی

## اسکرین‌شات‌ها

### 🧠 Brain — جریان زنده رویدادهای عامل
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — مصرف توکن و خلاصه نشست
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — فید بلادرنگ فراخوانی ابزار
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفکیک هزینه بر اساس مدل و نشست
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — مرورگر فایل‌های فضای کاری
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — وضعیت امنیتی و لاگ ممیزی
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — سقف بودجه، محرک‌های نرخ خطا، وب‌هوک به Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — قرار دادن فراخوانی‌های پرخطر ابزار پشت تأیید دستی؛ قواعد حفاظتی مبتنی بر سیاست
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**مسدودسازی پیش از اجرا برای Claude Code** — یک دستور، هوک PreToolUse را
نصب می‌کند که فراخوانی‌های ابزار منطبق را *پیش از* اجرا متوقف می‌کند و منتظر
تصمیم شما می‌ماند (با فعال بودن [اعلان‌های پوش ابری](https://app.clawmetry.com/push)، یک لمس از گوشی‌تان کافی است):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

یک رد فقط همان یک فراخوانی ابزار را مسدود می‌کند، عامل نشست خود را حفظ می‌کند و
می‌تواند روش دیگری را امتحان کند. تأیید کردن از گوشی شما، پرامپت مجوز خود
Claude Code را نادیده می‌گیرد (چون شما قبلاً پاسخ داده‌اید). ابزارهای منطبق‌نشده
حدود ۴۰ میلی‌ثانیه هزینه دارند و به جریان مجوز عادی Claude Code واگذار می‌شوند.
همچنین وقتی خود Claude Code منتظر شماست، یک پوش به گوشی دریافت می‌کنید (اعلان‌های
`permission_prompt` / `idle_prompt`).

## نصب

**تک‌خطی (پیشنهادی):**
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

## توسعه فرانت‌اند نسخه ۲ (v2)

اپلیکیشن ری‌اکت نسخه ۲ در `frontend/` قرار دارد و زمانی که سرور Flask با
فعال‌بودن v2 راه‌اندازی شود، در مسیر `/v2` سرو می‌شود.

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
`http://localhost:8900` پروکسی می‌کند، بنابراین اپلیکیشن ری‌اکت می‌تواند بدون
تنظیمات اضافی CORS با سرور محلی Flask صحبت کند.

برای ساخت باندلی که همراه بسته پایتون منتشر می‌شود:

```bash
cd frontend
npm run build
```

باندل تولیدی در `clawmetry/static/v2/dist/` نوشته می‌شود.

## سازگاری ران‌تایم / عامل

ClawMetry بسیاری از ران‌تایم‌های عامل هوش مصنوعی را رصد می‌کند، نه فقط OpenClaw.
هر ران‌تایم غیر از OpenClaw یک آداپتور خواننده اختصاصی دارد که قالب بومی نشست آن
را به شکل‌های یکپارچه ClawMetry ترجمه می‌کند؛ دیمون آن‌ها را به همان مخزن DuckDB
و اسنپ‌شات ابری با برچسب ران‌تایم وارد می‌کند، و تب بازپخش نشست وقتی بیش از یک
ران‌تایم وجود داشته باشد یک **سوییچر ران‌تایم** نشان می‌دهد. برای جدول کامل و
راهنمای افزودن ران‌تایم‌ها به [`docs/compatibility.md`](docs/compatibility.md)
و برای معرفی خانواده OpenClaw به [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md)
مراجعه کنید.

| ران‌تایم / عامل | وضعیت | یادداشت‌ها |
|---|---|---|
| **OpenClaw** | بومی | ران‌تایم مرجع، تشخیص خودکار |
| **PicoClaw** | آداپتور بتا | JSONL مسطح `providers.Message` (`~/.picoclaw/workspace/sessions`). رونوشت‌ها، مدل، فراخوانی ابزار. |
| **NanoClaw** | آداپتور بتا | SQLite به ازای هر نشست (`data/v2-sessions`). رونوشت‌ها + شمار پیام. |
| **Hermes** | آداپتور بتا | SQLite در `~/.hermes/state.db`. رونوشت‌ها، مدل، توکن‌ها/هزینه. |
| **Claude Code** | آداپتور بتا | JSONL در `~/.claude/projects/.../<id>.jsonl`. رونوشت‌ها، مدل، فراخوانی ابزار + تفکر، مصرف توکن. |
| **Codex** | آداپتور بتا | JSONL rollout در `~/.codex/sessions/...`. رونوشت‌ها، مدل، فراخوانی ابزار، مصرف توکن. |
| **Cursor** | آداپتور بتا | SQLite در `state.vscdb`. رونوشت چت/کامپوزر، مدل. |
| **Aider** | آداپتور بتا | `.aider.chat.history.md` به ازای هر پروژه. رونوشت‌ها، مدل، شمار توکن. |
| **Goose** | آداپتور بتا | SQLite در `~/.local/share/goose`. رونوشت‌ها، مدل، فراخوانی ابزار، مجموع توکن. |
| **opencode** | آداپتور بتا | SQLite در `~/.local/share/opencode`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Qwen Code** | آداپتور بتا | JSONL در `~/.qwen/projects/.../chats`. رونوشت‌ها، مدل، فراخوانی ابزار، مصرف توکن. |
| **Pi** | آداپتور بتا | JSONL در `~/.pi/agent/sessions`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Deep Agents** | آداپتور بتا | SQLite در `~/.deepagents/.state/sessions.db`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **n8n** | آداپتور بتا | SQLite در `~/.n8n/database.sqlite`. اجراهای گردش‌کار، اجرای نودها، پرامپت‌های AI Agent، مدل + توکن‌ها هرجا که n8n آن‌ها را ثبت کند. |

منظور از «آداپتور بتا» این است که ClawMetry یک خواننده برای قالب واقعی روی‌دیسک
آن ران‌تایم ارائه می‌دهد که در برابر یک نصب واقعی روی یک دستگاه واقعی ساخته و
تأیید شده است (نگاه کنید به `tests/fixtures/runtimes/<rt>/`). آداپتورها فقط‌خواندنی
هستند؛ هرکدام درباره آنچه ران‌تایمش واقعاً ذخیره می‌کند صادق است (مثلاً
PicoClaw/NanoClaw/Cursor هزینه توکن را روی دیسک نمی‌نویسند). وقتی چند ران‌تایم
روی یک نود اجرا شود، سوییچر ران‌تایم نمای نشست‌ها را به یکی محدود می‌کند تا
بررسی عمیق و تمیز ممکن شود.

## پیگیری هر عامل SDK، انتساب هزینه خارج از حلقه

ران‌تایم‌های بالا همگی نشست‌ها را روی دیسک می‌نویسند. **عامل تولیدی** خودتان،
همان که روی OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B یا یک
حلقه ساده `httpx` ساخته‌اید، این کار را نمی‌کند. رهگیر بدون‌تنظیمِ ClawMetry
همچنان فراخوانی‌های LLM آن را (هزینه، توکن‌ها، تأخیر، خطاها) با پچ‌کردن مانکی
روی `httpx`/`requests` ثبت می‌کند:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا متغیر محیطی `CLAWMETRY_SOURCE=support-agent`) هر فراخوانی
را با یک **منبع نام‌گذاری‌شده** برچسب می‌زند، بنابراین هر محصولی که اجرا
می‌کنید به عنوان یک ردیف درجه‌یک و قابل‌انتساب از نظر هزینه در کارت
**🔌 منابع خارج از حلقه** در تب Overview داشبورد نشان داده می‌شود، شامل
فراخوانی‌ها، ارائه‌دهندگان، تأخیر، نرخ خطا به ازای هر عامل. اگر منبعی تنظیم
نکنید؟ فراخوانی‌ها همچنان ثبت می‌شوند؛ فقط کارت پنهان می‌ماند.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

این همان لایه داده‌ای است که آداپتورهای ران‌تایم به آن می‌دهند (DuckDB → اسنپ‌شات
ابری)، بنابراین منابع خارج از حلقه نیز مانند بقیه چیزها با رمزنگاری سرتاسری
با داشبورد ابری همگام می‌شوند.

## OpenTelemetry، بدون وابستگی به فروشنده، ترِیس‌های خود را به هر جا بفرستید

ClawMetry در هر دو جهت به زبان **OpenTelemetry** صحبت می‌کند، با استفاده از
**قراردادهای معنایی GenAI**، بنابراین ترِیس‌های عامل شما هرگز در یک ابزار
قفل نمی‌شوند.

هر نشست، فراخوانی‌های LLM، ابزارها، زیرعامل‌ها، توکن‌ها، هزینه، را به صورت
اسپن‌های GenAI با OTLP/HTTP به هر جمع‌کننده (Datadog، Grafana، Honeycomb، یا
جمع‌کننده OTel خودتان) **صادر** کنید:

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

**دریافت** — گیرنده OTLP داخلی، ترِیس‌ها و متریک‌ها را از هر چیز دیگری در
`/v1/traces` و `/v1/metrics` می‌پذیرد (برای دریافت protobuf از
`pip install clawmetry[otel]` استفاده کنید).

شما هم داشبورد بدون‌تنظیم و محلی‌محورِ ClawMetry را دارید **و** داده‌های خود
را در هر بک‌اندی که تیم‌تان از قبل اجرا می‌کند، بدون قفل‌شدگی، بدون نیاز به
نصب یک عامل دوم.

## پیکربندی

اغلب افراد به هیچ تنظیماتی نیاز ندارند. ClawMetry فضای کاری، لاگ‌ها، نشست‌ها
و cronها را به‌طور خودکار تشخیص می‌دهد.

اگر نیاز به سفارشی‌سازی دارید:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

همه گزینه‌ها: `clawmetry --help`

## کانال‌های پشتیبانی‌شده

ClawMetry فعالیت زنده هر کانال OpenClaw که پیکربندی کرده‌اید را نشان می‌دهد.
فقط کانال‌هایی که واقعاً در `openclaw.json` شما تنظیم شده‌اند در نمودار Flow
ظاهر می‌شوند؛ کانال‌های پیکربندی‌نشده به‌طور خودکار پنهان می‌شوند.

روی هر گره کانال در Flow کلیک کنید تا یک نمای حباب‌گفتگوی زنده با شمار
پیام‌های ورودی/خروجی ببینید.

| کانال | وضعیت | پاپ‌آپ زنده | یادداشت‌ها |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ کامل | ✅ | پیام‌ها، آمار، تازه‌سازی هر ۱۰ ثانیه |
| 💬 **iMessage** | ✅ کامل | ✅ | مستقیماً `~/Library/Messages/chat.db` را می‌خواند |
| 💚 **WhatsApp** | ✅ کامل | ✅ | از طریق WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ کامل | ✅ | از طریق signal-cli |
| 🟣 **Discord** | ✅ کامل | ✅ | تشخیص Guild + کانال |
| 🟪 **Slack** | ✅ کامل | ✅ | تشخیص فضای کاری + کانال |
| 🌐 **Webchat** | ✅ کامل | ✅ | نشست‌های رابط وب داخلی |
| 📡 **IRC** | ✅ کامل | ✅ | رابط حباب به سبک ترمینال |
| 🍏 **BlueBubbles** | ✅ کامل | ✅ | iMessage از طریق REST API مربوط به BlueBubbles |
| 🔵 **Google Chat** | ✅ کامل | ✅ | از طریق وب‌هوک‌های Chat API |
| 🟣 **MS Teams** | ✅ کامل | ✅ | از طریق افزونه بات Teams |
| 🔷 **Mattermost** | ✅ کامل | ✅ | چت تیمی خودمیزبان |
| 🟩 **Matrix** | ✅ کامل | ✅ | غیرمتمرکز، پشتیبانی E2EE |
| 🟢 **LINE** | ✅ کامل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ کامل | ✅ | پیام‌های مستقیم غیرمتمرکز NIP-04 |
| 🟣 **Twitch** | ✅ کامل | ✅ | چت از طریق اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ کامل | ✅ | اشتراک رویداد WebSocket |
| 🔵 **Zalo** | ✅ کامل | ✅ | Zalo Bot API |

> **تشخیص خودکار:** ClawMetry فایل `~/.openclaw/openclaw.json` شما را می‌خواند
> و فقط کانال‌هایی را که واقعاً پیکربندی کرده‌اید نمایش می‌دهد. نیازی به
> تنظیم دستی نیست.

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

> **نکته:** هنگام اجرا در Docker، دایرکتوری‌های داده و لاگ عامل خود (مثلاً
> `~/.openclaw`، `~/.claude`، `~/.codex`) را مانت کنید تا ClawMetry بتواند
> تنظیمات شما را به‌طور خودکار تشخیص دهد.

## پیش‌نیازها

- Python 3.8+
- Flask (به‌طور خودکار از طریق pip نصب می‌شود)
- یک ران‌تایم عامل هوش مصنوعی روی همان دستگاه: OpenClaw، NVIDIA NemoClaw،
  Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider،
  NanoClaw، PicoClaw، Pi، Deep Agents، یا n8n (یا حجم‌های مانت‌شده برای Docker)
- Linux یا macOS

## پشتیبانی NemoClaw / OpenShell

ClawMetry به‌طور خودکار [NemoClaw](https://github.com/NVIDIA/NemoClaw) را
تشخیص می‌دهد، پوشش امنیتی سازمانی NVIDIA برای OpenClaw که عامل‌ها را درون
کانتینرهای ایزوله‌شده OpenShell اجرا می‌کند.

در اغلب موارد نیازی به تنظیمات اضافی نیست. دیمون همگام‌سازی فایل‌های نشست را
چه در `~/.openclaw/` روی میزبان و چه درون یک کانتینر OpenShell به‌طور خودکار
کشف می‌کند.

### چگونه کار می‌کند

ClawMetry به دو روش NemoClaw را تشخیص می‌دهد:

۱. **تشخیص باینری** — بررسی وجود CLI به نام `nemoclaw` و اجرای
   `nemoclaw status` برای دریافت اطلاعات سندباکس
۲. **تشخیص کانتینر** — اسکن کانتینرهای در حال اجرای Docker به دنبال
   ایمیج‌های `openshell`، `nemoclaw`، یا `ghcr.io/nvidia/`، سپس خواندن
   نشست‌ها از طریق مانت‌های حجمی یا `docker cp`

فایل‌های نشست همگام‌سازی‌شده از کانتینرهای NemoClaw با متادیتای
`runtime=nemoclaw` و `container_id` در داشبورد ابری برچسب‌گذاری می‌شوند،
بنابراین می‌توانید آن‌ها را در نگاه اول از نشست‌های استاندارد OpenClaw
تشخیص دهید.

### راه‌اندازی پیشنهادی: دیمون همگام‌سازی روی میزبان

برای بهترین تجربه، دیمون همگام‌سازی ClawMetry را روی **دستگاه میزبان** (نه
درون سندباکس) اجرا کنید. این کار محدودیت‌های سیاست شبکه NemoClaw را دور
می‌زند.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

دیمون همگام‌سازی به‌طور خودکار نشست‌ها را درون هر کانتینر OpenShell در حال
اجرا پیدا می‌کند.

### اختیاری: نام صریح سندباکس

اگر تشخیص خودکار کار نکرد، ClawMetry را به سندباکس درست اشاره دهید:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### اجرا درون سندباکس (پیشرفته)

اگر باید دیمون همگام‌سازی را **درون** سندباکس OpenShell اجرا کنید، این قاعده
خروجی را به سیاست شبکه NemoClaw خود اضافه کنید تا بتواند به API دریافت
ClawMetry دسترسی داشته باشد:

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

| نقطه پایانی | پورت | پروتکل | الزامی |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | بله (دیمون همگام‌سازی → ابر) |
| `localhost:8900` | 8900 | HTTP | بله (رابط داشبورد محلی) |
| سوکت Docker (`/var/run/docker.sock`) | — | سوکت Unix | برای کشف نشست کانتینر |

دیمون همگام‌سازی فقط تماس‌های خروجی HTTPS به `ingest.clawmetry.com` برقرار
می‌کند. هیچ پورت ورودی مورد نیاز نیست.

---

## استقرار ابری

برای تونل‌های SSH، پروکسی معکوس و Docker به **[راهنمای آزمایش ابری](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** مراجعه کنید.

## آزمایش

این پروژه با BrowserStack آزمایش می‌شود.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## تله‌متری

ClawMetry اولین باری که CLI مربوط به `clawmetry` را روی یک دستگاه جدید اجرا
می‌کنید، یک پینگ ناشناس «اولین اجرا» به `https://app.clawmetry.com/api/install`
ارسال می‌کند. از این برای شمارش نصب‌ها (تنها معیار بازاریابی که برای یک پروژه
متن‌باز داریم) و برای فهمیدن اینکه کاربران ما کدام چارچوب‌های عامل را نصب
کرده‌اند استفاده می‌کنیم.

**دقیقاً یک POST به ازای هر نصب**، شامل:

| فیلد | نمونه | چرا |
|---|---|---|
| `install_id` | UUID تصادفی ذخیره‌شده در `~/.clawmetry/install_id` | جلوگیری از تکرار؛ به ایمیل یا api_key شما مرتبط نیست |
| `version` | `0.12.167` | اینکه چه نسخه‌هایی در حال استفاده‌اند |
| `os` / `os_version` | `Darwin` / `25.3.0` | اولویت‌های پشتیبانی از پلتفرم |
| `python` | `3.11.15` | ماتریس پشتیبانی نسخه پایتون |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | با کدام عامل‌ها بعداً باید یکپارچه شویم |
| `is_ci` / `ci_provider` | `true` / `github_actions` | جدا کردن نصب‌های انسانی از نویز CI |

**چیزی که ارسال نمی‌کنیم**: IP (ابر کد کشور را سمت سرور از روی درخواست
استخراج می‌کند و سپس IP را دور می‌ریزد)، نام میزبان، نام کاربری، مسیر فضای
کاری، محتوای فایل، api_key شما، ایمیل شما، هیچ چیز شخصی یا مرتبط با فضای
کاری. بار سیم قابل ممیزی در
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) است.

**انصراف** (هرکدام از این‌ها آن را برای همیشه غیرفعال می‌کند):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

خطای شبکه در اینجا هرگز اجرای `clawmetry` را مسدود نمی‌کند، پینگ روی یک
ریسه دیمون با مهلت ۳ ثانیه به صورت fire-and-forget است.

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
  <strong>🦞 ببینید عامل شما چگونه فکر می‌کند</strong><br>
  <sub>ساخته شده توسط <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · بخشی از اکوسیستم <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
