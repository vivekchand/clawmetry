<!-- i18n-src:0e34918f8f2e -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**ببینید عامل هوش مصنوعی شما چگونه فکر می‌کند.** رصدپذیری بلادرنگ برای **۱۴ رانتایم عامل هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۱۰ مورد دیگر. یک داشبورد برای کل ناوگان عامل‌های شما.

> 🌐 **این متن را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر →](docs/i18n/)

یک دستور. بدون پیکربندی. تشخیص خودکار همه‌چیز.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود و کارتان تمام است.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## با ۱۴ رانتایم عامل کار می‌کند

ClawMetry به‌عنوان ابزار رصدپذیری برای OpenClaw شروع شد و اکنون **کل ناوگان عامل‌های شما** را در یک داشبورد اندازه‌گیری می‌کند و هر رانتایم موجود روی سیستم شما را به‌طور خودکار تشخیص می‌دهد:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw و NemoClaw در برنامه متن‌باز رایگان هستند؛ سایر رانتایم‌ها با ClawMetry Cloud یا لایسنس Pro خوداستقرار فعال می‌شوند. رانتایم را از هدر تغییر دهید و هر تب — هزینه، توکن‌ها، ابزارها، ردگیری‌ها — به همان رانتایم محدود می‌شود. برای تفکیک دقیق رایگان/پولی، جدول سطوح، ساختار `/api/entitlement` و رابط خط فرمان `clawmetry license` به **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** مراجعه کنید.

## چه چیزی به‌دست می‌آورید

- **Flow** — نمودار زنده و متحرک که نشان می‌دهد پیام‌ها چگونه از کانال‌ها، مغز (brain)، ابزارها و بازگشت عبور می‌کنند
- **Overview** — بررسی سلامت، نقشه حرارتی فعالیت، شمار جلسات، اطلاعات مدل
- **Usage** — ردیابی توکن و هزینه با تفکیک روزانه/هفتگی/ماهانه
- **Sessions** — جلسات فعال عامل با مدل، توکن‌ها، آخرین فعالیت
- **Crons** — کارهای زمان‌بندی‌شده با وضعیت، اجرای بعدی، مدت زمان
- **Logs** — پخش زنده لاگ با رنگ‌بندی
- **Memory** — مرور SOUL.md، MEMORY.md، AGENTS.md، یادداشت‌های روزانه
- **Transcripts** — رابط کاربری حباب گفتگو برای خواندن تاریخچه جلسات
- **Alerts** — سقف بودجه، محرک‌های نرخ خطا، تشخیص آفلاین‌شدن عامل؛ مسیریابی به Slack، Discord، PagerDuty، Telegram، Email
- **Approvals** — قرار دادن حذف‌های مخرب، force pushها، تغییرات پایگاه داده، sudo، نصب بسته‌ها و تماس‌های شبکه پشت یک تأیید یک‌کلیکی

## تصاویر

### 🧠 Brain — جریان زنده رویدادهای عامل
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — مصرف توکن و خلاصه جلسات
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — فید بلادرنگ فراخوانی ابزارها
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفکیک هزینه بر اساس مدل و جلسه
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — مرورگر فایل‌های فضای کاری
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — وضعیت امنیتی و لاگ ممیزی
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — سقف بودجه، محرک‌های نرخ خطا، وب‌هوک به Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — قرار دادن فراخوانی‌های ابزار پرریسک پشت تأیید دستی؛ قوانین حفاظتی مبتنی بر سیاست
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**مسدودسازی پیش از اجرا برای Claude Code** — یک دستور، یک هوک
PreToolUse نصب می‌کند که فراخوانی‌های ابزار منطبق را *پیش از* اجرا متوقف کرده
و منتظر تصمیم شما می‌ماند (با یک ضربه از گوشی‌تان، در صورت فعال بودن
[اعلان‌های پوش ابری](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

یک رد فقط همان یک فراخوانی ابزار را مسدود می‌کند؛ عامل جلسه خود را حفظ می‌کند
و می‌تواند رویکرد دیگری را امتحان کند. تأیید از طریق گوشی، درخواست مجوز
خودِ Claude Code را رد می‌کند (شما قبلاً پاسخ داده‌اید). ابزارهای منطبق‌نشده
حدود ۴۰ میلی‌ثانیه هزینه دارند و به جریان مجوز عادی Claude Code واگذار
می‌شوند. همچنین وقتی خودِ Claude Code منتظر شماست، یک پوش گوشی دریافت
می‌کنید (اعلان‌های `permission_prompt` / `idle_prompt`).

## نصب

**تک‌خطی (توصیه‌شده):**
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

## توسعه فرانت‌اند نسخه ۲

برنامه React نسخه ۲ در `frontend/` قرار دارد و زمانی که سرور Flask با
فعال بودن نسخه ۲ راه‌اندازی شود، در مسیر `/v2` سرو می‌شود.

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

آدرس `http://localhost:5173/v2/` را باز کنید. Vite درخواست‌های `/api`
را به `http://localhost:8900` پروکسی می‌کند، بنابراین برنامه React
می‌تواند بدون نیاز به تنظیمات اضافی CORS با سرور محلی Flask ارتباط
برقرار کند.

برای ساخت باندلی که همراه بسته پایتون ارسال می‌شود:

```bash
cd frontend
npm run build
```

باندل نهایی در `clawmetry/static/v2/dist/` نوشته می‌شود.

## سازگاری رانتایم / عامل

ClawMetry بسیاری از رانتایم‌های عامل هوش مصنوعی را رصد می‌کند، نه فقط
OpenClaw. هر رانتایم غیر از OpenClaw دارای یک آداپتور خواننده اختصاصی
است که قالب بومی جلسات آن را به شکل‌های یکپارچه ClawMetry ترجمه می‌کند؛
دیمن این‌ها را در همان مخزن DuckDB و اسنپ‌شات ابری، با برچسب رانتایم،
دریافت می‌کند و تب بازپخش جلسه، در صورت وجود بیش از یک رانتایم، یک
**سوئیچ رانتایم** نشان می‌دهد. برای جدول کامل + راهنمای افزودن رانتایم‌ها
به [`docs/compatibility.md`](docs/compatibility.md) و برای مقدمه خانواده
OpenClaw به [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) مراجعه
کنید.

آیا ابزار امنیت عامل [numbat از Perplexity](https://github.com/perplexityai/numbat)
را اجرا می‌کنید؟ ClawMetry یافته‌ها و تصمیمات اجرایی آن را بدون نیاز به
تنظیمات اضافی دریافت می‌کند؛ به [`docs/NUMBAT.md`](docs/NUMBAT.md) مراجعه
کنید.

| رانتایم / عامل | وضعیت | یادداشت‌ها |
|---|---|---|
| **OpenClaw** | بومی | رانتایم مرجع، تشخیص خودکار |
| **PicoClaw** | آداپتور بتا | JSONL مسطح `providers.Message` (`~/.picoclaw/workspace/sessions`). رونوشت‌ها، مدل، فراخوانی ابزار. |
| **NanoClaw** | آداپتور بتا | SQLite به‌ازای هر جلسه (`data/v2-sessions`). رونوشت‌ها + شمار پیام. |
| **Hermes** | آداپتور بتا | SQLite در `~/.hermes/state.db`. رونوشت‌ها، مدل، توکن/هزینه. |
| **Claude Code** | آداپتور بتا | JSONL در `~/.claude/projects/.../<id>.jsonl`. رونوشت‌ها، مدل، فراخوانی ابزار + تفکر، مصرف توکن. |
| **Codex** | آداپتور بتا | Rollout JSONL در `~/.codex/sessions/...`. رونوشت‌ها، مدل، فراخوانی ابزار، مصرف توکن. |
| **Cursor** | آداپتور بتا | SQLite `state.vscdb`. رونوشت‌های چت/کامپوزر، مدل. |
| **Aider** | آداپتور بتا | `.aider.chat.history.md` به‌ازای هر پروژه. رونوشت‌ها، مدل، شمار توکن. |
| **Goose** | آداپتور بتا | SQLite در `~/.local/share/goose`. رونوشت‌ها، مدل، فراخوانی ابزار، مجموع توکن. |
| **opencode** | آداپتور بتا | SQLite در `~/.local/share/opencode`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Qwen Code** | آداپتور بتا | JSONL در `~/.qwen/projects/.../chats`. رونوشت‌ها، مدل، فراخوانی ابزار، مصرف توکن. |
| **Pi** | آداپتور بتا | JSONL در `~/.pi/agent/sessions`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Deep Agents** | آداپتور بتا | SQLite در `~/.deepagents/.state/sessions.db`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **n8n** | آداپتور بتا | SQLite در `~/.n8n/database.sqlite`. اجراهای گردش‌کار، اجرای گره‌ها، پرامپت‌های AI Agent، مدل + توکن‌ها در مواردی که n8n آن‌ها را ثبت می‌کند. |
| **Antigravity** | آداپتور بتا | JSONL مغز در `~/.gemini/<flavor>/brain/`. گفتگوها، مراحل ابزار، تفکر، تفکیک توکن Gemini به‌ازای هر تولید + هزینه، مصرف تولید پس‌زمینه. |
| **GitHub Copilot** | آداپتور بتا | `events.jsonl` مربوط به Copilot CLI در `~/.copilot/session-state/` + دفتر مصرف `session-store.db` به‌ازای هر فراخوانی. گفتگوها، فراخوانی ابزار، مسیریابی مدل، تفکیک توکن آگاه از کش، هزینه اعتبار هوش مصنوعی صورتحساب‌شده توسط فروشنده. |

منظور از «آداپتور بتا» این است که ClawMetry یک خواننده برای قالب واقعی
روی دیسک آن رانتایم ارائه می‌دهد که هر کدام روی یک نصب واقعی روی یک
دستگاه واقعی ساخته و تأیید شده‌اند (به `tests/fixtures/runtimes/<rt>/`
مراجعه کنید). آداپتورها فقط‌خواندنی هستند؛ هر کدام درباره آنچه رانتایمش
واقعاً روی دیسک ذخیره می‌کند صادق است (مثلاً PicoClaw/NanoClaw/Cursor
هزینه توکن را روی دیسک نمی‌نویسند). وقتی چند رانتایم روی یک نود اجرا
می‌شوند، سوئیچ رانتایم نمای جلسات را به یکی محدود می‌کند تا بررسی دقیق و
تمیز باشد.

## ردیابی هر عامل SDK — انتساب هزینه خارج از حلقه

همه رانتایم‌های بالا جلسات را روی دیسک می‌نویسند. **عامل تولیدی** خودتان
— همان که روی OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex،
E2B یا یک حلقه ساده `httpx` ساخته‌اید — این کار را نمی‌کند. رهگیر
بدون‌پیکربندی ClawMetry همچنان با وصله کردن (monkey-patching) `httpx`/`requests`،
فراخوانی‌های LLM آن را ثبت می‌کند (هزینه، توکن‌ها، تأخیر، خطاها):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا متغیر محیطی `CLAWMETRY_SOURCE=support-agent`) هر
فراخوانی را با یک **منبع نام‌گذاری‌شده** برچسب می‌زند، بنابراین هر
محصولی که اجرا می‌کنید در کارت **🔌 منابع خارج از حلقه** تب Overview
داشبورد به‌عنوان یک خط مستقل و قابل انتساب هزینه ظاهر می‌شود — فراخوانی‌ها،
ارائه‌دهندگان، تأخیر، نرخ خطا به‌ازای هر عامل. اگر منبعی تنظیم نشده باشد؟
فراخوانی‌ها همچنان ثبت می‌شوند؛ فقط کارت پنهان می‌ماند.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

این همان لایه داده‌ای است که آداپتورهای رانتایم آن را تغذیه می‌کنند
(DuckDB → اسنپ‌شات ابری)، بنابراین منابع خارج از حلقه هم مانند بقیه موارد
به داشبورد ابری همگام‌سازی می‌شوند، با رمزنگاری سرتاسری.

## OpenTelemetry — بدون وابستگی به فروشنده خاص، ردگیری‌های خود را به هرجا ارسال کنید

ClawMetry با استفاده از **قراردادهای معنایی GenAI**، در هر دو جهت به
**OpenTelemetry** صحبت می‌کند، بنابراین ردگیری‌های عامل شما هرگز به یک
ابزار خاص قفل نمی‌شوند.

**صادرات** هر جلسه — فراخوانی‌های LLM، ابزارها، زیرعامل‌ها، توکن‌ها،
هزینه — به‌صورت اسپن‌های OTLP/HTTP GenAI به هر کالکتوری (Datadog، Grafana،
Honeycomb، یا OTel Collector خودتان):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

هدرهای احراز هویت و فاصله زمانی نظرسنجی، متغیرهای محیطی اختیاری هستند:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**دریافت** — گیرنده داخلی OTLP، ردگیری‌ها و متریک‌ها را از هر منبع
دیگری در `/v1/traces` و `/v1/metrics` می‌پذیرد (برای دریافت protobuf،
`pip install clawmetry[otel]`).

هم داشبورد بدون‌پیکربندی و محلی‌محور ClawMetry را دارید **و هم** داده‌های
خود را در هر بک‌اندی که تیمتان از قبل استفاده می‌کند — بدون قفل‌شدگی،
بدون نیاز به نصب عامل دوم.

## پیکربندی

بیشتر افراد به هیچ پیکربندی‌ای نیاز ندارند. ClawMetry فضای کاری، لاگ‌ها،
جلسات و کرون‌های شما را به‌طور خودکار تشخیص می‌دهد.

اگر نیاز به سفارشی‌سازی دارید:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

تمام گزینه‌ها: `clawmetry --help`

## کانال‌های پشتیبانی‌شده

ClawMetry فعالیت زنده را برای هر کانال OpenClaw که پیکربندی کرده‌اید
نشان می‌دهد. فقط کانال‌هایی که واقعاً در `openclaw.json` شما تنظیم
شده‌اند در نمودار Flow ظاهر می‌شوند؛ کانال‌های پیکربندی‌نشده به‌طور
خودکار پنهان می‌مانند.

روی هر گره کانال در Flow کلیک کنید تا نمای زنده حباب گفتگو را با
شمارش پیام‌های ورودی/خروجی ببینید.

| کانال | وضعیت | پاپ‌آپ زنده | یادداشت‌ها |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ کامل | ✅ | پیام‌ها، آمار، تازه‌سازی ۱۰ ثانیه‌ای |
| 💬 **iMessage** | ✅ کامل | ✅ | خواندن مستقیم `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ کامل | ✅ | از طریق WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ کامل | ✅ | از طریق signal-cli |
| 🟣 **Discord** | ✅ کامل | ✅ | تشخیص گیلد + کانال |
| 🟪 **Slack** | ✅ کامل | ✅ | تشخیص فضای کاری + کانال |
| 🌐 **Webchat** | ✅ کامل | ✅ | جلسات رابط وب داخلی |
| 📡 **IRC** | ✅ کامل | ✅ | رابط حباب به‌سبک ترمینال |
| 🍏 **BlueBubbles** | ✅ کامل | ✅ | iMessage از طریق BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ کامل | ✅ | از طریق وب‌هوک‌های Chat API |
| 🟣 **MS Teams** | ✅ کامل | ✅ | از طریق افزونه بات Teams |
| 🔷 **Mattermost** | ✅ کامل | ✅ | چت تیمی خوداستقرار |
| 🟩 **Matrix** | ✅ کامل | ✅ | غیرمتمرکز، پشتیبانی E2EE |
| 🟢 **LINE** | ✅ کامل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ کامل | ✅ | پیام‌های مستقیم غیرمتمرکز NIP-04 |
| 🟣 **Twitch** | ✅ کامل | ✅ | چت از طریق اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ کامل | ✅ | اشتراک رویداد WebSocket |
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

> **توجه:** هنگام اجرا در Docker، دایرکتوری‌های داده و لاگ عامل خود
> (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) را مانت کنید تا
> ClawMetry بتواند تنظیمات شما را به‌طور خودکار تشخیص دهد.

## نیازمندی‌ها

- Python 3.8+
- Flask (به‌طور خودکار از طریق pip نصب می‌شود)
- یک رانتایم عامل هوش مصنوعی روی همان دستگاه: OpenClaw، NVIDIA NemoClaw،
  Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider،
  NanoClaw، PicoClaw، Pi، Deep Agents، n8n، Antigravity یا GitHub Copilot
  (یا وُلوم‌های مانت‌شده برای Docker)
- لینوکس یا macOS

## پشتیبانی NemoClaw / OpenShell

ClawMetry به‌طور خودکار [NemoClaw](https://github.com/NVIDIA/NemoClaw) را
تشخیص می‌دهد — پوشش امنیتی سازمانی NVIDIA برای OpenClaw که عامل‌ها را
درون کانتینرهای ایزوله‌شده OpenShell اجرا می‌کند.

در بیشتر موارد نیازی به پیکربندی اضافی نیست. دیمن همگام‌سازی به‌طور
خودکار فایل‌های جلسه را کشف می‌کند، چه در `~/.openclaw/` روی میزبان
باشند و چه درون یک کانتینر OpenShell.

### نحوه کار

ClawMetry به دو روش NemoClaw را تشخیص می‌دهد:

1. **تشخیص باینری** — بررسی وجود ابزار خط فرمان `nemoclaw` و اجرای
   `nemoclaw status` برای دریافت اطلاعات سندباکس
2. **تشخیص کانتینر** — اسکن کانتینرهای در حال اجرای Docker برای یافتن
   تصاویر `openshell`، `nemoclaw` یا `ghcr.io/nvidia/`، سپس خواندن
   جلسات از طریق مانت وُلوم یا `docker cp`

فایل‌های جلسه همگام‌سازی‌شده از کانتینرهای NemoClaw با متادیتای
`runtime=nemoclaw` و `container_id` در داشبورد ابری برچسب‌گذاری
می‌شوند، تا بتوانید آن‌ها را از جلسات استاندارد OpenClaw به‌سرعت
تشخیص دهید.

### تنظیم پیشنهادی: دیمن همگام‌سازی روی میزبان (HOST)

برای بهترین تجربه، دیمن همگام‌سازی ClawMetry را روی **دستگاه میزبان**
(نه درون سندباکس) اجرا کنید. این کار از محدودیت‌های سیاست شبکه NemoClaw
جلوگیری می‌کند.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

دیمن همگام‌سازی به‌طور خودکار جلسات درون هر کانتینر OpenShell در حال
اجرا را پیدا می‌کند.

### اختیاری: نام صریح سندباکس

اگر تشخیص خودکار کار نکرد، ClawMetry را به سندباکس درست هدایت کنید:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### اجرا درون سندباکس (پیشرفته)

اگر باید دیمن همگام‌سازی را **درون** سندباکس OpenShell اجرا کنید، این
قانون خروجی (egress) را به سیاست شبکه NemoClaw خود اضافه کنید تا بتواند
به API دریافت ClawMetry دسترسی داشته باشد:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

اعمال با:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### پورت‌ها و نقاط پایانی

| نقطه پایانی | پورت | پروتکل | ضروری |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | بله (دیمن همگام‌سازی ← ابر) |
| `localhost:8900` | 8900 | HTTP | بله (رابط داشبورد محلی) |
| سوکت Docker (`/var/run/docker.sock`) | — | سوکت یونیکس | برای کشف جلسه کانتینر |

دیمن همگام‌سازی فقط تماس‌های خروجی HTTPS به `ingest.clawmetry.com`
برقرار می‌کند. هیچ پورت ورودی‌ای لازم نیست.

---

## استقرار ابری

برای تونل‌های SSH، پروکسی معکوس و Docker به **[راهنمای تست ابری](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** مراجعه کنید.

## تست

این پروژه با BrowserStack تست می‌شود.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## تله‌متری

ClawMetry پینگ‌های ناشناس چرخه حیات نصب را به
`https://app.clawmetry.com/api/install` ارسال می‌کند: یک پینگ `install`
در اولین باری که CLI ابزار `clawmetry` را روی دستگاه جدید اجرا می‌کنید،
یک پینگ `update` در اولین اجرا پس از ارتقا به نسخه جدید، و یک پینگ
`onboarded` هنگامی که انتخاب فرآیند آشناسازی درون داشبورد را تکمیل
می‌کنید. از این برای شمارش نصب‌های واقعی استفاده می‌کنیم (اعداد خام
دانلود PyPI حدود ۹۸٪ آینه‌ها، CI و دانلودهای مجدد به‌روزرسانی خودکار
هستند) و برای فهمیدن اینکه کدام چارچوب‌ها و نسخه‌های عامل واقعاً در
حال استفاده هستند.

**حداکثر یک POST به‌ازای هر رویداد چرخه حیات به‌ازای هر نسخه**، شامل:

| فیلد | مثال | دلیل |
|---|---|---|
| `install_id` | UUID تصادفی ذخیره‌شده در `~/.clawmetry/install_id` | جلوگیری از تکرار؛ ناشناس تا زمانی که به‌طور صریح همگام‌سازی ابری را متصل کنید (سپس ضربان قلب احراز‌هویت‌شده دیمن آن را حمل می‌کند و این نصب را به حساب شما پیوند می‌دهد) |
| `event` | `install` / `update` / `onboarded` | نصب تازه در برابر ارتقای نصب موجود |
| `version` | `0.12.167` | اینکه کدام نسخه‌ها در حال استفاده هستند |
| `os` / `os_version` | `Darwin` / `25.3.0` | اولویت‌بندی پشتیبانی از پلتفرم |
| `python` | `3.11.15` | ماتریس پشتیبانی نسخه پایتون |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | با کدام عامل‌ها باید در آینده یکپارچه شویم |
| `is_ci` / `ci_provider` | `true` / `github_actions` | تفکیک نصب‌های انسانی از نویز CI |

**چیزی که ارسال نمی‌کنیم**: IP (سرور ابری کد کشور را سمت سرور از روی
درخواست استخراج می‌کند و سپس IP را دور می‌ریزد)، نام میزبان، نام
کاربری، مسیر فضای کاری، محتوای فایل، api_key شما، ایمیل شما، یا هر
چیز شخصی یا مختص فضای کاری. بار داده روی سیم در
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) قابل ممیزی است.

**انصراف** (هر یک از این‌ها آن را برای همیشه غیرفعال می‌کند):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

قطعی شبکه در اینجا هرگز مانع اجرای `clawmetry` نمی‌شود؛ پینگ روی یک
رشته دیمن با مهلت ۳ ثانیه‌ای، به‌صورت شلیک‌و‌فراموش ارسال می‌شود.

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
  <strong>🦞 ببینید عامل هوش مصنوعی شما چگونه فکر می‌کند</strong><br>
  <sub>ساخته‌شده توسط <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · بخشی از اکوسیستم <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
