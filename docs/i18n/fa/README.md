<!-- i18n-src:7cfb63716507 -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**تفکر ایجنت خود را ببینید.** رصد بلادرنگ برای **۱۴ رانتایم ایجنت هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۱۰ مورد دیگر. یک داشبورد برای کل ناوگان ایجنت‌های شما.

> 🌐 **این متن را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر →](docs/i18n/)

یک دستور. بدون پیکربندی. تشخیص خودکار همه‌چیز.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود و کارتان تمام است.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## با ۱۴ رانتایم ایجنت کار می‌کند

ClawMetry به‌عنوان ابزار رصد برای OpenClaw شروع شد و اکنون **کل ناوگان ایجنت‌های شما** را در یک داشبورد اندازه‌گیری می‌کند و هر رانتایم روی دستگاه شما را به‌صورت خودکار تشخیص می‌دهد:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

OpenClaw و NemoClaw در اپلیکیشن متن‌باز رایگان هستند؛ سایر رانتایم‌ها با ClawMetry Cloud یا لایسنس Pro خودمیزبان فعال می‌شوند. رانتایم‌ها را از هدر تغییر دهید و هر تب، هزینه، توکن‌ها، ابزارها، ترِیس‌ها، دوباره به آن رانتایم محدود می‌شود. برای تقسیم دقیق رایگان/پولی، ماتریس سطوح، شکل `/api/entitlement` و CLI مربوط به `clawmetry license`، به **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** مراجعه کنید.

## چه چیزی به دست می‌آورید

- **Flow** — نمودار زنده و متحرکی که نشان می‌دهد پیام‌ها چگونه از میان کانال‌ها، مغز، ابزارها و بازگشت جریان می‌یابند
- **Overview** — بررسی سلامت، نقشه حرارتی فعالیت، تعداد نشست‌ها، اطلاعات مدل
- **Usage** — ردیابی توکن و هزینه با تفکیک روزانه/هفتگی/ماهانه
- **Sessions** — نشست‌های فعال ایجنت به همراه مدل، توکن‌ها، آخرین فعالیت
- **Crons** — کارهای زمان‌بندی‌شده به همراه وضعیت، اجرای بعدی، مدت‌زمان
- **Logs** — استریم لاگ زنده با رمزگذاری رنگی
- **Memory** — مرور SOUL.md، MEMORY.md، AGENTS.md، یادداشت‌های روزانه
- **Transcripts** — رابط کاربری حباب‌گفتگو برای خواندن تاریخچه نشست‌ها
- **Alerts** — سقف بودجه، محرک‌های نرخ خطا، تشخیص آفلاین‌شدن ایجنت؛ مسیریابی به Slack، Discord، PagerDuty، Telegram، ایمیل
- **Approvals** — قرار دادن حذف‌های مخرب، force pushها، تغییرات پایگاه‌داده، sudo، نصب بسته‌ها، تماس‌های شبکه پشت یک تأیید یک‌کلیکی

## اسکرین‌شات‌ها

### 🧠 Brain — جریان زنده رویدادهای ایجنت
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — مصرف توکن و خلاصه نشست
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — خوراک زنده فراخوانی ابزار
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفکیک هزینه بر اساس مدل و نشست
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — مرورگر فایل فضای کاری
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — وضعیت امنیتی و لاگ ممیزی
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — سقف بودجه، محرک‌های نرخ خطا، وب‌هوک به Slack / Discord / PagerDuty / ایمیل
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — قرار دادن فراخوانی‌های ابزار پرریسک پشت تأیید دستی؛ قوانین حفاظتی مبتنی بر سیاست
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**مسدودسازی پیش از اجرا برای Claude Code** — یک دستور، هوک PreToolUse را نصب می‌کند
که فراخوانی‌های ابزار منطبق را *پیش از* اجرا متوقف می‌کند و منتظر تصمیم شما می‌ماند
(با یک ضربه از گوشی‌تان، اگر
[اعلان‌های فشاری ابری](https://app.clawmetry.com/push) فعال باشد):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

یک رد کردن (deny) فقط همان یک فراخوانی ابزار را مسدود می‌کند؛ ایجنت نشست خود را حفظ می‌کند و می‌تواند
رویکرد دیگری را امتحان کند. تأیید کردن از گوشی، پیام مجوز خود Claude Code را دور می‌زند
(چون شما از قبل پاسخ داده‌اید). ابزارهای بی‌تطابق حدود ۴۰ میلی‌ثانیه هزینه دارند و
به روند مجوز عادی Claude Code برمی‌گردند. همچنین وقتی خود Claude Code منتظر شماست، یک پوش به گوشی
دریافت می‌کنید (اعلان‌های `permission_prompt` / `idle_prompt`).

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

## توسعه فرانت‌اند نسخه ۲

اپلیکیشن React نسخه ۲ در `frontend/` قرار دارد و وقتی سرور Flask با فعال‌سازی نسخه ۲
راه‌اندازی شود، در مسیر `/v2` سرو می‌شود.

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
`http://localhost:8900` پروکسی می‌کند، بنابراین اپلیکیشن React می‌تواند بدون تنظیم CORS اضافه
با سرور محلی Flask ارتباط برقرار کند.

برای ساخت باندلی که همراه بسته پایتون منتشر می‌شود:

```bash
cd frontend
npm run build
```

باندل تولیدی در `clawmetry/static/v2/dist/` نوشته می‌شود.

## سازگاری رانتایم / ایجنت

ClawMetry رانتایم‌های متعدد ایجنت هوش مصنوعی را رصد می‌کند، نه فقط OpenClaw. هر رانتایم غیر از OpenClaw یک آداپتور خواندن اختصاصی دارد که قالب بومی نشست آن را به شکل‌های یکپارچه ClawMetry تبدیل می‌کند؛ دیمون داده‌ها را در همان مخزن DuckDB + اسنپ‌شات ابری وارد می‌کند و با برچسب رانتایم علامت‌گذاری می‌کند، و تب پخش نشست وقتی بیش از یک رانتایم وجود داشته باشد یک **سوئیچر رانتایم** نشان می‌دهد. برای ماتریس کامل + راهنمای افزودن رانتایم به [`docs/compatibility.md`](docs/compatibility.md) و برای مقدمه خانواده OpenClaw به [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) مراجعه کنید.

ابزار امنیت ایجنت [numbat از Perplexity](https://github.com/perplexityai/numbat) را اجرا می‌کنید؟ ClawMetry یافته‌ها و تصمیمات اعمال قوانین آن را بلافاصله دریافت می‌کند؛ به [`docs/NUMBAT.md`](docs/NUMBAT.md) مراجعه کنید.

| رانتایم / ایجنت | وضعیت | یادداشت‌ها |
|---|---|---|
| **OpenClaw** | بومی | رانتایم مرجع، تشخیص خودکار |
| **PicoClaw** | آداپتور بتا | JSONL مسطح `providers.Message` (`~/.picoclaw/workspace/sessions`). رونوشت‌ها، مدل، فراخوانی ابزار. |
| **NanoClaw** | آداپتور بتا | SQLite به‌ازای هر نشست (`data/v2-sessions`). رونوشت‌ها + تعداد پیام. |
| **Hermes** | آداپتور بتا | SQLite در `~/.hermes/state.db`. رونوشت‌ها، مدل، توکن‌ها/هزینه. |
| **Claude Code** | آداپتور بتا | JSONL در `~/.claude/projects/.../<id>.jsonl`. رونوشت‌ها، مدل، فراخوانی ابزار + تفکر، مصرف توکن. |
| **Codex** | آداپتور بتا | JSONL رول‌اوت در `~/.codex/sessions/...`. رونوشت‌ها، مدل، فراخوانی ابزار، مصرف توکن. |
| **Cursor** | آداپتور بتا | SQLite در `state.vscdb`. رونوشت‌های چت/کامپوزر، مدل. |
| **Aider** | آداپتور بتا | `.aider.chat.history.md` به‌ازای هر پروژه. رونوشت‌ها، مدل، شمارش توکن. |
| **Goose** | آداپتور بتا | SQLite در `~/.local/share/goose`. رونوشت‌ها، مدل، فراخوانی ابزار، مجموع توکن. |
| **opencode** | آداپتور بتا | SQLite در `~/.local/share/opencode`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Qwen Code** | آداپتور بتا | JSONL در `~/.qwen/projects/.../chats`. رونوشت‌ها، مدل، فراخوانی ابزار، مصرف توکن. |
| **Pi** | آداپتور بتا | JSONL در `~/.pi/agent/sessions`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Deep Agents** | آداپتور بتا | SQLite در `~/.deepagents/.state/sessions.db`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **n8n** | آداپتور بتا | SQLite در `~/.n8n/database.sqlite`. اجراهای گردش‌کار، اجراهای نود، پرامپت‌های AI Agent، مدل + توکن‌ها در جایی که n8n ثبت می‌کند. |
| **Antigravity** | آداپتور بتا | JSONL مغز زیر `~/.gemini/<flavor>/brain/`. مکالمات، مراحل ابزار، تفکر، تفکیک توکن Gemini به‌ازای هر تولید + هزینه، مصرف تولید پس‌زمینه. |
| **GitHub Copilot** | آداپتور بتا | `events.jsonl` مربوط به Copilot CLI زیر `~/.copilot/session-state/` + دفتر مصرف به‌ازای هر فراخوانی `session-store.db`. مکالمات، فراخوانی ابزار، مسیریابی مدل، تفکیک توکن آگاه از کش، هزینه اعتبار AI محاسبه‌شده توسط فروشنده. |
| **Grok** | آداپتور بتا | xAI Grok Build CLI (باینری Rust زیر `~/.grok/bin/grok`): لاگ رویداد سراسری `~/.grok/logs/unified.jsonl` + به‌ازای هر نشست `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. مکالمات، تفکیک توکن به‌ازای هر نوبت، مسیریابی مدل، و بار خروجی repo این CLI که در `~/.grok/upload_queue/` قرار می‌گیرد تا ببینید چه چیزی از دستگاه شما خارج شده است. |

«آداپتور بتا» یعنی ClawMetry یک خواننده برای قالب واقعی روی‌دیسک آن رانتایم ارائه می‌دهد که هر کدام روی یک نصب واقعی و یک دستگاه واقعی ساخته و تأیید شده‌اند (به `tests/fixtures/runtimes/<rt>/` مراجعه کنید). آداپتورها فقط‌خواندنی هستند؛ هرکدام صادقانه بیان می‌کنند رانتایم‌شان واقعاً چه چیزی ذخیره می‌کند (مثلاً PicoClaw/NanoClaw/Cursor هزینه توکن را روی دیسک نمی‌نویسند). وقتی چند رانتایم روی یک نود اجرا می‌شوند، سوئیچر رانتایم نمای نشست‌ها را به یکی محدود می‌کند تا بررسی دقیق تمیزی داشته باشید.

## ردیابی هر ایجنت SDK — انتساب هزینه خارج از حلقه

رانتایم‌های بالا همگی نشست‌ها را روی دیسک می‌نویسند. **ایجنت تولیدی** خودتان، همانی که روی OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B یا یک حلقه ساده `httpx` ساخته‌اید، این کار را نمی‌کند. رهگیر بدون پیکربندی ClawMetry همچنان با پچ‌کردن مانکی `httpx`/`requests`، فراخوانی‌های LLM آن را (هزینه، توکن‌ها، تأخیر، خطاها) ضبط می‌کند:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا متغیر محیطی `CLAWMETRY_SOURCE=support-agent`) هر فراخوانی را با یک **منبع نام‌گذاری‌شده** برچسب می‌زند، بنابراین هر محصولی که اجرا می‌کنید به‌عنوان یک خط مستقل و قابل انتساب هزینه در کارت **🔌 منابع خارج از حلقه** داشبورد در Overview نمایش داده می‌شود: فراخوانی‌ها، ارائه‌دهندگان، تأخیر، نرخ خطا به‌ازای هر ایجنت. منبعی تنظیم نشده؟ فراخوانی‌ها همچنان ردیابی می‌شوند؛ فقط کارت پنهان می‌ماند.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

این همان لایه داده‌ای است که آداپتورهای رانتایم را تغذیه می‌کند (DuckDB ← اسنپ‌شات ابری)، بنابراین منابع خارج از حلقه هم مانند بقیه، با رمزگذاری سرتاسری، با ابر همگام‌سازی می‌شوند.

## OpenTelemetry — بدون وابستگی به فروشنده، ترِیس‌های خود را به هرکجا بفرستید

ClawMetry با استفاده از **قراردادهای معنایی GenAI**، در هر دو جهت **OpenTelemetry** صحبت می‌کند، بنابراین ترِیس‌های ایجنت شما هرگز قفل‌شده در یک ابزار نمی‌مانند.

**صادرات** هر نشست، فراخوانی‌های LLM، ابزارها، زیرایجنت‌ها، توکن‌ها، هزینه، به‌عنوان اسپن‌های GenAI با OTLP/HTTP به هر کالکتوری (Datadog، Grafana، Honeycomb، یا OTel Collector خودتان):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

هدرهای احراز هویت و فاصله نظرسنجی، متغیرهای محیطی اختیاری هستند:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**دریافت** — گیرنده داخلی OTLP، ترِیس‌ها و متریک‌ها را از هر منبع دیگری در `/v1/traces` و `/v1/metrics` می‌پذیرد (برای دریافت protobuf از `pip install clawmetry[otel]` استفاده کنید).

هم داشبورد بدون پیکربندی و محلی‌محور ClawMetry را دارید **و** هم داده‌های خود را در هر بک‌اندی که تیم‌تان از قبل استفاده می‌کند؛ بدون قفل‌شدگی، بدون نصب ایجنت دوم.

## پیکربندی

اکثر افراد به هیچ پیکربندی‌ای نیاز ندارند. ClawMetry فضای کاری، لاگ‌ها، نشست‌ها و کرون‌های شما را به‌صورت خودکار تشخیص می‌دهد.

اگر نیاز به شخصی‌سازی دارید:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

همه گزینه‌ها: `clawmetry --help`

## کانال‌های پشتیبانی‌شده

ClawMetry فعالیت زنده هر کانال OpenClaw که پیکربندی کرده‌اید را نشان می‌دهد. فقط کانال‌هایی که واقعاً در `openclaw.json` شما تنظیم شده‌اند در نمودار Flow ظاهر می‌شوند؛ کانال‌های پیکربندی‌نشده به‌صورت خودکار پنهان می‌مانند.

روی هر نود کانال در Flow کلیک کنید تا نمای زنده حباب‌گفتگو با تعداد پیام‌های ورودی/خروجی را ببینید.

| کانال | وضعیت | پاپ‌آپ زنده | یادداشت‌ها |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ کامل | ✅ | پیام‌ها، آمار، تازه‌سازی هر ۱۰ ثانیه |
| 💬 **iMessage** | ✅ کامل | ✅ | خواندن مستقیم `~/Library/Messages/chat.db` |
| 💚 **WhatsApp** | ✅ کامل | ✅ | از طریق WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ کامل | ✅ | از طریق signal-cli |
| 🟣 **Discord** | ✅ کامل | ✅ | تشخیص گیلد + کانال |
| 🟪 **Slack** | ✅ کامل | ✅ | تشخیص فضای کاری + کانال |
| 🌐 **Webchat** | ✅ کامل | ✅ | نشست‌های رابط وب داخلی |
| 📡 **IRC** | ✅ کامل | ✅ | رابط حباب سبک ترمینال |
| 🍏 **BlueBubbles** | ✅ کامل | ✅ | iMessage از طریق BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ کامل | ✅ | از طریق وب‌هوک‌های Chat API |
| 🟣 **MS Teams** | ✅ کامل | ✅ | از طریق افزونه بات Teams |
| 🔷 **Mattermost** | ✅ کامل | ✅ | چت تیمی خودمیزبان |
| 🟩 **Matrix** | ✅ کامل | ✅ | غیرمتمرکز، پشتیبانی E2EE |
| 🟢 **LINE** | ✅ کامل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ کامل | ✅ | پیام مستقیم غیرمتمرکز NIP-04 |
| 🟣 **Twitch** | ✅ کامل | ✅ | چت از طریق اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ کامل | ✅ | اشتراک رویداد WebSocket |
| 🔵 **Zalo** | ✅ کامل | ✅ | Zalo Bot API |

> **تشخیص خودکار:** ClawMetry فایل `~/.openclaw/openclaw.json` شما را می‌خواند و فقط کانال‌هایی که واقعاً پیکربندی کرده‌اید را رندر می‌کند. نیازی به تنظیم دستی نیست.

## استقرار Docker

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

> **نکته:** هنگام اجرا در Docker، دایرکتوری‌های داده + لاگ ایجنت خود را مانت کنید (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) تا ClawMetry بتواند تنظیمات شما را به‌صورت خودکار تشخیص دهد.

## پیش‌نیازها

- Python 3.8+
- Flask (به‌صورت خودکار از طریق pip نصب می‌شود)
- یک رانتایم ایجنت هوش مصنوعی روی همان دستگاه: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، n8n، Antigravity، GitHub Copilot، Grok، یا QM (یا حجم‌های مانت‌شده برای Docker)
- Linux یا macOS

## پشتیبانی NemoClaw / OpenShell

ClawMetry به‌صورت خودکار [NemoClaw](https://github.com/NVIDIA/NemoClaw) را تشخیص می‌دهد؛ لایه امنیتی سازمانی NVIDIA برای OpenClaw که ایجنت‌ها را درون کانتینرهای ایزوله‌شده OpenShell اجرا می‌کند.

در بیشتر موارد نیازی به پیکربندی اضافه نیست. دیمون همگام‌سازی به‌صورت خودکار فایل‌های نشست را پیدا می‌کند، چه در `~/.openclaw/` روی هاست باشند و چه درون یک کانتینر OpenShell.

### چگونه کار می‌کند

ClawMetry به دو روش NemoClaw را تشخیص می‌دهد:

1. **تشخیص باینری** — بررسی وجود CLI با نام `nemoclaw` و اجرای `nemoclaw status` برای دریافت اطلاعات سندباکس
2. **تشخیص کانتینر** — اسکن کانتینرهای در حال اجرای Docker برای تصاویر `openshell`، `nemoclaw` یا `ghcr.io/nvidia/`، سپس خواندن نشست‌ها از طریق مانت والیوم یا `docker cp`

فایل‌های نشست همگام‌سازی‌شده از کانتینرهای NemoClaw با متادیتای `runtime=nemoclaw` و `container_id` در داشبورد ابری برچسب‌گذاری می‌شوند، تا بتوانید آن‌ها را در یک نگاه از نشست‌های استاندارد OpenClaw تشخیص دهید.

### تنظیمات پیشنهادی: دیمون همگام‌سازی روی HOST

برای بهترین تجربه، دیمون همگام‌سازی ClawMetry را روی **دستگاه هاست** (نه درون سندباکس) اجرا کنید. این کار از محدودیت‌های سیاست شبکه NemoClaw جلوگیری می‌کند.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

دیمون همگام‌سازی به‌صورت خودکار نشست‌ها را درون هر کانتینر OpenShell در حال اجرا پیدا می‌کند.

### اختیاری: نام سندباکس صریح

اگر تشخیص خودکار کار نکرد، ClawMetry را به‌سمت سندباکس درست هدایت کنید:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### اجرا درون سندباکس (پیشرفته)

اگر باید دیمون همگام‌سازی را **درون** سندباکس OpenShell اجرا کنید، این قانون خروجی (egress) را به سیاست شبکه NemoClaw خود اضافه کنید تا بتواند به API دریافت ClawMetry دسترسی داشته باشد:

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
| `ingest.clawmetry.com` | 443 | HTTPS | بله (دیمون همگام‌سازی ← ابر) |
| `localhost:8900` | 8900 | HTTP | بله (رابط داشبورد محلی) |
| سوکت Docker (`/var/run/docker.sock`) | — | سوکت یونیکس | برای تشخیص نشست کانتینر |

دیمون همگام‌سازی فقط تماس‌های HTTPS خروجی به `ingest.clawmetry.com` برقرار می‌کند. هیچ پورت ورودی لازم نیست.

---

## استقرار ابری

برای تونل‌های SSH، پروکسی معکوس و Docker به **[راهنمای تست ابری](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** مراجعه کنید.

## تست

این پروژه با BrowserStack تست شده است.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## تله‌متری

ClawMetry پینگ‌های ناشناس چرخه‌حیات نصب را به
`https://app.clawmetry.com/api/install` ارسال می‌کند: یک پینگ `install` در اولین
اجرای CLI به نام `clawmetry` روی یک دستگاه جدید، یک پینگ `update` در
اولین اجرا پس از ارتقا به نسخه جدید، و یک پینگ `onboarded` هنگامی که
گزینه راه‌اندازی اولیه درون داشبورد را کامل می‌کنید. از این برای شمارش نصب‌های واقعی
استفاده می‌کنیم (اعداد خام دانلود PyPI حدود ۹۸٪ آینه‌ها، CI و
دانلودهای مجدد به‌روزرسانی خودکار هستند) و برای فهمیدن اینکه کدام چارچوب‌ها و
نسخه‌های ایجنت واقعاً در حال استفاده هستند.

**حداکثر یک POST به‌ازای هر رویداد چرخه‌حیات به‌ازای هر نسخه**، شامل:

| فیلد | نمونه | چرا |
|---|---|---|
| `install_id` | UUID تصادفی ذخیره‌شده در `~/.clawmetry/install_id` | حذف تکرار؛ ناشناس تا زمانی که صراحتاً همگام‌سازی ابری را متصل کنید (سپس ضربان قلب احراز هویت‌شده دیمون آن را حمل می‌کند و این نصب را به حساب شما پیوند می‌دهد) |
| `event` | `install` / `update` / `onboarded` | نصب تازه در برابر ارتقای نصب موجود |
| `version` | `0.12.167` | چه نسخه‌هایی در حال استفاده‌اند |
| `os` / `os_version` | `Darwin` / `25.3.0` | اولویت‌های پشتیبانی پلتفرم |
| `python` | `3.11.15` | ماتریس پشتیبانی نسخه پایتون |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | با کدام ایجنت‌ها باید بعداً یکپارچه شویم |
| `is_ci` / `ci_provider` | `true` / `github_actions` | جدا کردن نصب‌های انسانی از نویز CI |

**آنچه ارسال نمی‌کنیم**: IP (ابر کد کشور را سمت سرور از درخواست استخراج می‌کند
و سپس IP را دور می‌ریزد)، نام هاست، نام کاربری، مسیر فضای کاری، محتوای فایل، api_key
شما، ایمیل شما، و هیچ‌چیز PII یا خاص فضای کاری. بار داده روی سیم
در [`clawmetry/telemetry.py`](clawmetry/telemetry.py) قابل ممیزی است.

**عدم مشارکت** (هرکدام از این‌ها آن را برای همیشه غیرفعال می‌کند):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

خرابی شبکه در اینجا هرگز مانع اجرای `clawmetry` نمی‌شود؛ پینگ به‌صورت
شلیک‌و‌فراموش روی یک نخ دیمون با مهلت ۳ ثانیه ارسال می‌شود.

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
  <strong>🦞 تفکر ایجنت خود را ببینید</strong><br>
  <sub>ساخته‌شده توسط <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · بخشی از اکوسیستم <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
