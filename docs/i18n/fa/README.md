<!-- i18n-src:191e9094d7fa -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**تفکر عامل خود را ببینید.** رصدپذیری بلادرنگ برای **۱۴ زمان‌اجرای عامل هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۱۰ مورد دیگر. یک داشبورد برای کل ناوگان عامل‌های شما.

> 🌐 **این را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر ←](docs/i18n/)

یک دستور. بدون پیکربندی. تشخیص خودکار همه چیز.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود و کارتان تمام است.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## با ۱۴ زمان‌اجرای عامل کار می‌کند

ClawMetry به‌عنوان رصدپذیری برای OpenClaw شروع شد و اکنون **کل ناوگان عامل‌های شما** را در یک داشبورد پایش می‌کند و هر زمان‌اجرا را روی دستگاه شما به‌صورت خودکار تشخیص می‌دهد:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw و NemoClaw در اپلیکیشن متن‌باز رایگان هستند؛ سایر زمان‌اجراها با ClawMetry Cloud یا مجوز Pro خودمیزبان فعال می‌شوند. زمان‌اجرا را از سربرگ عوض کنید و هر تب — هزینه، توکن‌ها، ابزارها، ردگیری‌ها — روی همان زمان‌اجرا محدود می‌شود. برای تفکیک دقیق رایگان/پولی، ماتریس رده‌ها، ساختار `/api/entitlement` و ابزار خط فرمان `clawmetry license` به **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** مراجعه کنید.

## چه چیزی به دست می‌آورید

- **Flow** — نمودار متحرک زنده که پیام‌های در حال عبور از کانال‌ها، مغز، ابزارها و بازگشت را نشان می‌دهد
- **Overview** — بررسی سلامت، نقشه حرارتی فعالیت، تعداد نشست‌ها، اطلاعات مدل
- **Usage** — ردیابی توکن و هزینه با تفکیک روزانه/هفتگی/ماهانه
- **Sessions** — نشست‌های فعال عامل با مدل، توکن‌ها، آخرین فعالیت
- **Crons** — کارهای زمان‌بندی‌شده با وضعیت، اجرای بعدی، مدت زمان
- **Logs** — استریم لاگ زنده با کدگذاری رنگی
- **Memory** — مرور SOUL.md، MEMORY.md، AGENTS.md، یادداشت‌های روزانه
- **Transcripts** — رابط کاربری حباب‌گفتگو برای خواندن تاریخچه نشست‌ها
- **Alerts** — سقف بودجه، محرک‌های نرخ خطا، تشخیص آفلاین‌شدن عامل؛ مسیریابی به Slack، Discord، PagerDuty، Telegram، ایمیل
- **Approvals** — قفل‌کردن حذف‌های مخرب، force pushها، تغییرات پایگاه‌داده، sudo، نصب بسته‌ها، فراخوانی‌های شبکه پشت یک تأیید تک‌کلیکی

## اسکرین‌شات‌ها

### 🧠 Brain — استریم زنده رویدادهای عامل
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — استفاده از توکن و خلاصه نشست
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — فید بلادرنگ فراخوانی ابزار
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفکیک هزینه بر اساس مدل و نشست
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — مرورگر فایل فضای کاری
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — وضعیت امنیتی و گزارش ممیزی
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — سقف بودجه، محرک‌های نرخ خطا، وب‌هوک به Slack / Discord / PagerDuty / ایمیل
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — قفل‌کردن فراخوانی‌های ابزار پرخطر پشت تأیید دستی؛ قوانین حفاظتی متکی بر سیاست
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**مسدودسازی پیش از اجرا برای Claude Code** — یک دستور یک هوک PreToolUse
نصب می‌کند که فراخوانی‌های ابزار منطبق را *پیش از* اجرا متوقف می‌کند و منتظر
تصمیم شما می‌ماند (یک ضربه از گوشی‌تان با فعال‌بودن
[اعلان‌های فشاری کلود](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

یک رد فقط همان یک فراخوانی ابزار را مسدود می‌کند — عامل نشست خود را حفظ می‌کند و
می‌تواند رویکرد دیگری را امتحان کند. تأیید از روی گوشی، درخواست مجوز داخلی
Claude Code را نادیده می‌گیرد (چون قبلاً پاسخ داده‌اید). ابزارهای منطبق‌نشده
حدود ۴۰ میلی‌ثانیه هزینه دارند و به جریان مجوز عادی Claude Code سقوط می‌کنند.
همچنین وقتی خود Claude Code منتظر شماست (اعلان‌های `permission_prompt` /
`idle_prompt`) یک اعلان فشاری روی گوشی دریافت می‌کنید.

## نصب

**یک‌خطی (توصیه‌شده):**
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

مسیر `http://localhost:5173/v2/` را باز کنید. Vite درخواست‌های `/api` را به
`http://localhost:8900` پروکسی می‌کند تا اپلیکیشن React بتواند بدون تنظیمات
CORS اضافی با سرور محلی Flask ارتباط برقرار کند.

برای ساخت باندلی که همراه بسته پایتون منتشر می‌شود:

```bash
cd frontend
npm run build
```

باندل تولیدی در `clawmetry/static/v2/dist/` نوشته می‌شود.

## سازگاری زمان‌اجرا / عامل

ClawMetry بسیاری از زمان‌اجراهای عامل هوش مصنوعی را رصد می‌کند، نه فقط
OpenClaw. هر زمان‌اجرای غیر از OpenClaw یک آداپتور خواننده اختصاصی دارد که
قالب نشست بومی آن را به شکل‌های یکپارچه ClawMetry ترجمه می‌کند؛ دیمون آن‌ها
را با برچسب زمان‌اجرا به همان مخزن DuckDB + عکس فوری ابری وارد می‌کند، و تب
پخش نشست وقتی بیش از یک زمان‌اجرا وجود دارد یک **تعویض‌کننده زمان‌اجرا**
نشان می‌دهد. برای ماتریس کامل + راهنمای افزودن زمان‌اجراهای جدید به
[`docs/compatibility.md`](docs/compatibility.md) و برای مقدمه خانواده
OpenClaw به [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) مراجعه کنید.

آیا ابزار امنیتی عامل [numbat از Perplexity](https://github.com/perplexityai/numbat)
را اجرا می‌کنید؟ ClawMetry یافته‌ها و تصمیمات اجرایی آن را بدون هیچ تنظیمی
دریافت می‌کند — به [`docs/NUMBAT.md`](docs/NUMBAT.md) مراجعه کنید.

| زمان‌اجرا / عامل | وضعیت | یادداشت‌ها |
|---|---|---|
| **OpenClaw** | بومی | زمان‌اجرای مرجع، تشخیص خودکار |
| **PicoClaw** | آداپتور بتا | JSONL مسطح `providers.Message` (`~/.picoclaw/workspace/sessions`). تاریخچه گفتگو، مدل، فراخوانی ابزار. |
| **NanoClaw** | آداپتور بتا | SQLite هر نشست (`data/v2-sessions`). تاریخچه گفتگو + تعداد پیام. |
| **Hermes** | آداپتور بتا | SQLite در `~/.hermes/state.db`. تاریخچه گفتگو، مدل، توکن‌ها/هزینه. |
| **Claude Code** | آداپتور بتا | JSONL در `~/.claude/projects/.../<id>.jsonl`. تاریخچه گفتگو، مدل، فراخوانی ابزار + تفکر، مصرف توکن. |
| **Codex** | آداپتور بتا | JSONL rollout در `~/.codex/sessions/...`. تاریخچه گفتگو، مدل، فراخوانی ابزار، مصرف توکن. |
| **Cursor** | آداپتور بتا | SQLite `state.vscdb`. تاریخچه گفتگو/کامپوزر، مدل. |
| **Aider** | آداپتور بتا | فایل `.aider.chat.history.md` در هر پروژه. تاریخچه گفتگو، مدل، شمارش توکن. |
| **Goose** | آداپتور بتا | SQLite در `~/.local/share/goose`. تاریخچه گفتگو، مدل، فراخوانی ابزار، مجموع توکن‌ها. |
| **opencode** | آداپتور بتا | SQLite در `~/.local/share/opencode`. تاریخچه گفتگو، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Qwen Code** | آداپتور بتا | JSONL در `~/.qwen/projects/.../chats`. تاریخچه گفتگو، مدل، فراخوانی ابزار، مصرف توکن. |
| **Pi** | آداپتور بتا | JSONL در `~/.pi/agent/sessions`. تاریخچه گفتگو، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Deep Agents** | آداپتور بتا | SQLite در `~/.deepagents/.state/sessions.db`. تاریخچه گفتگو، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **n8n** | آداپتور بتا | SQLite در `~/.n8n/database.sqlite`. اجرای گردش‌کار، اجرای نودها، پرامپت‌های AI Agent، مدل + توکن‌ها در جایی که n8n آن‌ها را ثبت کند. |
| **Antigravity** | آداپتور بتا | JSONL مغز در `~/.gemini/<flavor>/brain/`. مکالمات، مراحل ابزار، تفکر، تفکیک توکن Gemini به‌ازای هر تولید + هزینه، مصرف تولید در پس‌زمینه. |

«آداپتور بتا» یعنی ClawMetry یک خواننده برای قالب واقعی روی دیسک آن زمان‌اجرا
عرضه می‌کند، که هرکدام روی یک نصب واقعی روی یک دستگاه واقعی ساخته و تأیید
شده‌اند (به `tests/fixtures/runtimes/<rt>/` مراجعه کنید). آداپتورها فقط‌خواندنی
هستند؛ هرکدام درباره آنچه زمان‌اجرای مربوطه واقعاً ذخیره می‌کند صادق است (مثلاً
PicoClaw/NanoClaw/Cursor هزینه توکن را روی دیسک نمی‌نویسند). وقتی چند
زمان‌اجرا روی یک نود اجرا می‌شوند، تعویض‌کننده زمان‌اجرا نمای نشست‌ها را برای
بررسی دقیق تمیز به یکی محدود می‌کند.

## ردیابی هر عامل SDK — انتساب هزینه خارج از حلقه

زمان‌اجراهای بالا همگی نشست‌ها را روی دیسک می‌نویسند. **عامل تولیدی** خودتان —
همانی که با OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B، یا
یک حلقه ساده `httpx` ساخته‌اید — این کار را نمی‌کند. رهگیر بدون‌پیکربندی
ClawMetry همچنان فراخوانی‌های LLM آن را (هزینه، توکن‌ها، تأخیر، خطاها) با
monkey-patch کردن `httpx`/`requests` ثبت می‌کند:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا متغیر محیطی `CLAWMETRY_SOURCE=support-agent`) هر فراخوانی
را با یک **منبع نام‌گذاری‌شده** برچسب می‌زند، تا هر محصولی که اجرا می‌کنید
به‌عنوان یک خط مستقل و قابل‌انتساب هزینه در کارت **🔌 منابع خارج از حلقه**
داشبورد در تب Overview ظاهر شود — فراخوانی‌ها، ارائه‌دهندگان، تأخیر، نرخ خطا
به‌ازای هر عامل. منبعی تنظیم نشده؟ فراخوانی‌ها همچنان ردیابی می‌شوند؛ فقط کارت
پنهان می‌ماند.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

این همان لایه داده‌ای است که آداپتورهای زمان‌اجرا تغذیه می‌کنند (DuckDB ←
عکس فوری ابری)، بنابراین منابع خارج از حلقه هم مانند بقیه، به‌صورت
رمزنگاری‌شده سرتاسری، با داشبورد ابری همگام می‌شوند.

## OpenTelemetry — بی‌طرف نسبت به فروشنده، ردگیری‌های خود را به هر جا بفرستید

ClawMetry در هر دو جهت با **OpenTelemetry** صحبت می‌کند، با استفاده از
**قراردادهای معنایی GenAI**، بنابراین ردگیری‌های عامل شما هرگز به یک ابزار
قفل نمی‌شوند.

**صادرات** هر نشست — فراخوانی‌های LLM، ابزارها، زیرعامل‌ها، توکن‌ها، هزینه —
به‌صورت اسپن‌های OTLP/HTTP GenAI به هر جمع‌کننده‌ای (Datadog، Grafana،
Honeycomb، یا OTel Collector خودتان):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

هدرهای احراز هویت و فاصله نظرسنجی متغیرهای محیطی اختیاری هستند:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**دریافت** — گیرنده داخلی OTLP، ردگیری‌ها و متریک‌ها را از هر منبع دیگری در
`/v1/traces` و `/v1/metrics` می‌پذیرد (برای دریافت protobuf، `pip install
clawmetry[otel]` را نصب کنید).

هم داشبورد بدون‌پیکربندی و محلی‌محور ClawMetry را دارید و هم داده‌های خود را
در هر بک‌اندی که تیم‌تان از قبل استفاده می‌کند — بدون قفل‌شدگی، بدون نیاز به
نصب عامل دومی.

## پیکربندی

اکثر افراد به هیچ پیکربندی‌ای نیاز ندارند. ClawMetry فضای کاری، لاگ‌ها،
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

ClawMetry فعالیت زنده هر کانال OpenClaw که پیکربندی کرده‌اید را نشان می‌دهد.
فقط کانال‌هایی که واقعاً در `openclaw.json` شما تنظیم شده‌اند در نمودار Flow
ظاهر می‌شوند؛ کانال‌های پیکربندی‌نشده به‌طور خودکار پنهان می‌شوند.

روی هر نود کانال در Flow کلیک کنید تا نمای زنده حباب‌گفتگو با شمارش پیام‌های
ورودی/خروجی را ببینید.

| کانال | وضعیت | پاپ‌آپ زنده | یادداشت‌ها |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ کامل | ✅ | پیام‌ها، آمار، بازخوانی ۱۰ ثانیه‌ای |
| 💬 **iMessage** | ✅ کامل | ✅ | مستقیماً `~/Library/Messages/chat.db` را می‌خواند |
| 💚 **WhatsApp** | ✅ کامل | ✅ | از طریق WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ کامل | ✅ | از طریق signal-cli |
| 🟣 **Discord** | ✅ کامل | ✅ | تشخیص گیلد + کانال |
| 🟪 **Slack** | ✅ کامل | ✅ | تشخیص فضای کاری + کانال |
| 🌐 **Webchat** | ✅ کامل | ✅ | نشست‌های رابط کاربری وب داخلی |
| 📡 **IRC** | ✅ کامل | ✅ | رابط حباب سبک ترمینال |
| 🍏 **BlueBubbles** | ✅ کامل | ✅ | iMessage از طریق BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ کامل | ✅ | از طریق وب‌هوک‌های Chat API |
| 🟣 **MS Teams** | ✅ کامل | ✅ | از طریق افزونه بات Teams |
| 🔷 **Mattermost** | ✅ کامل | ✅ | چت تیمی خودمیزبان |
| 🟩 **Matrix** | ✅ کامل | ✅ | غیرمتمرکز، پشتیبانی E2EE |
| 🟢 **LINE** | ✅ کامل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ کامل | ✅ | پیام‌های خصوصی غیرمتمرکز NIP-04 |
| 🟣 **Twitch** | ✅ کامل | ✅ | چت از طریق اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ کامل | ✅ | اشتراک رویداد WebSocket |
| 🔵 **Zalo** | ✅ کامل | ✅ | Zalo Bot API |

> **تشخیص خودکار:** ClawMetry فایل `~/.openclaw/openclaw.json` شما را
> می‌خواند و فقط کانال‌هایی را که واقعاً پیکربندی کرده‌اید رندر می‌کند. هیچ
> تنظیم دستی لازم نیست.

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

> **توجه:** هنگام اجرا در Docker، دایرکتوری‌های داده + لاگ عامل خود را (مثلاً
> `~/.openclaw`، `~/.claude`، `~/.codex`) مانت کنید تا ClawMetry بتواند تنظیمات
> شما را به‌صورت خودکار تشخیص دهد.

## پیش‌نیازها

- Python 3.8+
- Flask (به‌صورت خودکار از طریق pip نصب می‌شود)
- یک زمان‌اجرای عامل هوش مصنوعی روی همان دستگاه: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، n8n یا Antigravity (یا وُلوم‌های مانت‌شده برای Docker)
- لینوکس یا macOS

## پشتیبانی NemoClaw / OpenShell

ClawMetry به‌صورت خودکار [NemoClaw](https://github.com/NVIDIA/NemoClaw) —
لایه امنیتی سازمانی NVIDIA برای OpenClaw که عامل‌ها را داخل کانتینرهای
sandbox شده OpenShell اجرا می‌کند — را تشخیص می‌دهد.

در اکثر موارد نیازی به پیکربندی اضافی نیست. دیمون همگام‌سازی به‌صورت خودکار
فایل‌های نشست را کشف می‌کند، چه در `~/.openclaw/` روی هاست باشند و چه داخل
یک کانتینر OpenShell.

### چگونه کار می‌کند

ClawMetry به دو روش NemoClaw را تشخیص می‌دهد:

1. **تشخیص باینری** — بررسی وجود ابزار خط فرمان `nemoclaw` و اجرای
   `nemoclaw status` برای دریافت اطلاعات sandbox
2. **تشخیص کانتینر** — اسکن کانتینرهای در حال اجرای Docker برای یافتن
   ایمیج‌های `openshell`، `nemoclaw` یا `ghcr.io/nvidia/`، سپس خواندن نشست‌ها
   از طریق مانت وُلوم یا `docker cp`

فایل‌های نشست همگام‌سازی‌شده از کانتینرهای NemoClaw با متادیتای
`runtime=nemoclaw` و `container_id` در داشبورد ابری برچسب‌گذاری می‌شوند، تا
بتوانید آن‌ها را در نگاه اول از نشست‌های استاندارد OpenClaw تشخیص دهید.

### راه‌اندازی توصیه‌شده: دیمون همگام‌سازی روی هاست

برای بهترین تجربه، دیمون همگام‌سازی ClawMetry را روی **دستگاه هاست** (نه
داخل sandbox) اجرا کنید. این کار محدودیت‌های سیاست شبکه NemoClaw را دور
می‌زند.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

دیمون همگام‌سازی به‌صورت خودکار نشست‌ها را داخل هر کانتینر OpenShell در حال
اجرا پیدا می‌کند.

### اختیاری: نام صریح sandbox

اگر تشخیص خودکار کار نکرد، ClawMetry را به sandbox درست هدایت کنید:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### اجرا داخل sandbox (پیشرفته)

اگر باید دیمون همگام‌سازی را **داخل** sandbox OpenShell اجرا کنید، این قانون
egress را به سیاست شبکه NemoClaw خود اضافه کنید تا بتواند به API دریافت
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

| نقطه پایانی | پورت | پروتکل | ضروری |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | بله (دیمون همگام‌سازی ← ابر) |
| `localhost:8900` | 8900 | HTTP | بله (رابط داشبورد محلی) |
| سوکت Docker (`/var/run/docker.sock`) | — | سوکت یونیکس | برای کشف نشست کانتینر |

دیمون همگام‌سازی فقط تماس‌های HTTPS خروجی به `ingest.clawmetry.com` برقرار
می‌کند. هیچ پورت ورودی لازم نیست.

---

## استقرار ابری

برای تونل‌های SSH، پروکسی معکوس و Docker به **[راهنمای تست ابری](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** مراجعه کنید.

## تست

این پروژه با BrowserStack تست می‌شود.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## تله‌متری

ClawMetry پینگ‌های ناشناس چرخه‌حیات نصب را به
`https://app.clawmetry.com/api/install` ارسال می‌کند: یک پینگ `install` در
اولین بار اجرای خط فرمان `clawmetry` روی یک دستگاه جدید، یک پینگ `update`
در اولین اجرا پس از ارتقا به نسخه جدید، و یک پینگ `onboarded` در زمان تکمیل
انتخاب راه‌اندازی داخل داشبورد. از این برای شمارش نصب‌های واقعی استفاده
می‌کنیم (اعداد خام دانلود PyPI حدود ۹۸٪ آینه‌سازها، CI و دانلودهای مجدد
به‌روزرسانی خودکار هستند) و برای اینکه بدانیم کدام چارچوب‌ها و نسخه‌های
عامل واقعاً در دنیای واقعی استفاده می‌شوند.

**حداکثر یک POST به‌ازای هر رویداد چرخه‌حیات به‌ازای هر نسخه**، شامل:

| فیلد | مثال | چرا |
|---|---|---|
| `install_id` | UUID تصادفی ذخیره‌شده در `~/.clawmetry/install_id` | جلوگیری از تکرار؛ ناشناس تا زمانی که صریحاً همگام‌سازی Cloud را متصل کنید (سپس heartbeat احرازهویت‌شده دیمون آن را حمل می‌کند و این نصب را به حساب شما پیوند می‌دهد) |
| `event` | `install` / `update` / `onboarded` | نصب تازه در برابر ارتقای نصب موجود |
| `version` | `0.12.167` | چه نسخه‌هایی در دنیای واقعی هستند |
| `os` / `os_version` | `Darwin` / `25.3.0` | اولویت‌های پشتیبانی از پلتفرم |
| `python` | `3.11.15` | ماتریس پشتیبانی نسخه پایتون |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | با کدام عامل‌ها باید بعداً یکپارچه شویم |
| `is_ci` / `ci_provider` | `true` / `github_actions` | جدا کردن نصب‌های انسانی از نویز CI |

**چیزی که ارسال نمی‌کنیم**: IP (سرور ابری کد کشور را در سمت سرور از روی
درخواست استخراج می‌کند، سپس IP را دور می‌ریزد)، نام میزبان، نام کاربری،
مسیر فضای کاری، محتوای فایل، کلید API شما، ایمیل شما، یا هر چیز شخصی یا
مختص فضای کاری. بار وایر در
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) قابل بازرسی است.

**غیرفعال‌سازی** (هر یک از موارد زیر آن را برای همیشه غیرفعال می‌کند):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

قطعی شبکه در اینجا هرگز مانع اجرای `clawmetry` نمی‌شود — این پینگ روی یک
رشته دیمون با مهلت زمانی ۳ ثانیه‌ای و به‌صورت fire-and-forget انجام می‌شود.

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
  <strong>🦞 تفکر عامل خود را ببینید</strong><br>
  <sub>ساخته‌شده توسط <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · بخشی از اکوسیستم <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
