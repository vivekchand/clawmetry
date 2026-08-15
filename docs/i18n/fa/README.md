<!-- i18n-src:c422fb7dd0da -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**تفکر ایجنت خود را ببینید.** رصدپذیری بلادرنگ برای **۲۰ ران‌تایم ایجنت هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۱۶ مورد دیگر. یک داشبورد برای کل ناوگان ایجنت‌های شما.

> 🌐 **این را به زبان‌های دیگر بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر →](docs/i18n/)

یک دستور. بدون پیکربندی. تشخیص خودکار همه چیز.

```bash
pip install clawmetry && clawmetry
```

در آدرس **http://localhost:8900** باز می‌شود و کارتان تمام است.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## با ۲۰ ران‌تایم ایجنت کار می‌کند

ClawMetry به‌عنوان ابزار رصدپذیری برای OpenClaw شروع شد و اکنون **کل ناوگان ایجنت‌های شما** را در یک داشبورد اندازه‌گیری می‌کند و هر ران‌تایم را روی دستگاه شما به‌طور خودکار تشخیص می‌دهد:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw و NemoClaw در اپلیکیشن متن‌باز رایگان هستند؛ سایر ران‌تایم‌ها با ClawMetry Cloud یا لایسنس Pro خوداستقرار فعال می‌شوند. ران‌تایم‌ها را از هدر تغییر دهید و هر تب، هزینه، توکن‌ها، ابزارها، ترِیس‌ها، دوباره روی همان ران‌تایم متمرکز می‌شود. برای تقسیم دقیق رایگان/پولی، ماتریس سطوح، ساختار `/api/entitlement`، و رابط خط فرمان `clawmetry license`، به **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** مراجعه کنید.

## چه چیزی به دست می‌آورید

- **Flow** — نمودار متحرک زنده که نشان می‌دهد پیام‌ها چگونه از کانال‌ها، مغز (brain)، ابزارها و بازگشت عبور می‌کنند
- **Overview** — بررسی سلامت، نقشه حرارتی فعالیت، شمار نشست‌ها، اطلاعات مدل
- **Usage** — پیگیری توکن و هزینه با تفکیک روزانه/هفتگی/ماهانه
- **Sessions** — نشست‌های فعال ایجنت به همراه مدل، توکن‌ها، آخرین فعالیت
- **Crons** — کارهای زمان‌بندی‌شده به همراه وضعیت، اجرای بعدی، مدت زمان
- **Logs** — پخش زنده لاگ‌ها با رنگ‌بندی
- **Memory** — مرور SOUL.md، MEMORY.md، AGENTS.md، یادداشت‌های روزانه
- **Transcripts** — رابط کاربری حباب‌گفتگو برای خواندن تاریخچه نشست‌ها
- **Alerts** — سقف بودجه، محرک‌های نرخ خطا، تشخیص آفلاین‌بودن ایجنت؛ مسیریابی به Slack، Discord، PagerDuty، Telegram، Email
- **Approvals** — قرار دادن حذف‌های مخرب، force pushها، تغییرات پایگاه‌داده، sudo، نصب بسته‌ها، فراخوانی‌های شبکه پشت یک تأیید تک‌کلیکی

## اسکرین‌شات‌ها

### 🧠 Brain — جریان زنده رویدادهای ایجنت
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — خلاصه مصرف توکن و نشست‌ها
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — فید بلادرنگ فراخوانی ابزارها
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفکیک هزینه بر اساس مدل و نشست
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — مرورگر فایل‌های فضای کاری
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — وضعیت امنیتی و گزارش ممیزی
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — سقف بودجه، محرک‌های نرخ خطا، وب‌هوک‌ها به Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — قرار دادن فراخوانی‌های پرریسک ابزار پشت تأیید دستی؛ قوانین حفاظتی مبتنی بر خط‌مشی
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**مسدودسازی پیش از اجرا برای Claude Code** — یک دستور، هوک PreToolUse را نصب می‌کند
که فراخوانی‌های ابزار منطبق را *پیش از* اجرا متوقف کرده و منتظر تصمیم شما می‌ماند
(با فعال‌بودن [اعلان‌های فشاری ابری](https://app.clawmetry.com/push)، فقط یک لمس از گوشی‌تان کافی است):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

یک رد فقط همان یک فراخوانی ابزار را مسدود می‌کند، ایجنت نشست خود را حفظ می‌کند
و می‌تواند رویکرد دیگری را امتحان کند. تأیید از طریق گوشی، درخواست مجوز خود Claude Code
را نادیده می‌گیرد (چون شما قبلاً پاسخ داده‌اید). ابزارهای نامنطبق حدود ۴۰ میلی‌ثانیه هزینه دارند
و به جریان مجوز عادی Claude Code منتقل می‌شوند. همچنین وقتی خود Claude Code منتظر پاسخ شماست
(اعلان‌های `permission_prompt` / `idle_prompt`) یک پوش روی گوشی دریافت می‌کنید.

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

## توسعه فرانت‌اند نسخه ۲ (v2)

اپلیکیشن React نسخه ۲ در `frontend/` قرار دارد و وقتی سرور Flask با فعال‌بودن v2
اجرا شود، در مسیر `/v2` سرو می‌شود.

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
`http://localhost:8900` پروکسی می‌کند، بنابراین اپلیکیشن React می‌تواند بدون تنظیمات
اضافی CORS با سرور محلی Flask ارتباط برقرار کند.

برای ساخت باندلی که همراه بسته پایتون ارسال می‌شود:

```bash
cd frontend
npm run build
```

باندل نهایی در مسیر `clawmetry/static/v2/dist/` نوشته می‌شود.

## سازگاری ران‌تایم / ایجنت

ClawMetry بسیاری از ران‌تایم‌های ایجنت هوش مصنوعی را رصد می‌کند، نه فقط OpenClaw. هر ران‌تایم غیر از OpenClaw یک آداپتور خواننده اختصاصی دارد که فرمت نشست بومی آن را به شکل‌های یکپارچه ClawMetry ترجمه می‌کند؛ دیمن (daemon) آن‌ها را با برچسب ران‌تایم به همان مخزن DuckDB و اسنپ‌شات ابری وارد می‌کند، و تب بازپخش نشست وقتی بیش از یک ران‌تایم حضور داشته باشد یک **سوئیچر ران‌تایم** نشان می‌دهد. برای ماتریس کامل + راهنمای افزودن ران‌تایم‌ها به [`docs/compatibility.md`](docs/compatibility.md) و برای مقدمه خانواده OpenClaw به [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) مراجعه کنید.

آیا ابزار امنیت ایجنت [numbat از پرپلکسیتی](https://github.com/perplexityai/numbat) را اجرا می‌کنید؟ ClawMetry یافته‌ها و تصمیمات اجرایی آن را بدون نیاز به تنظیمات اضافی وارد می‌کند؛ به [`docs/NUMBAT.md`](docs/NUMBAT.md) مراجعه کنید.

| ران‌تایم / ایجنت | وضعیت | یادداشت‌ها |
|---|---|---|
| **OpenClaw** | بومی | ران‌تایم مرجع، تشخیص خودکار |
| **PicoClaw** | آداپتور بتا | JSONL تخت `providers.Message`‏ (`~/.picoclaw/workspace/sessions`). رونوشت‌ها، مدل، فراخوانی ابزار. |
| **NanoClaw** | آداپتور بتا | SQLite به‌ازای هر نشست (`data/v2-sessions`). رونوشت‌ها + شمار پیام‌ها. |
| **Hermes** | آداپتور بتا | SQLite در `~/.hermes/state.db`. رونوشت‌ها، مدل، توکن/هزینه. |
| **Claude Code** | آداپتور بتا | JSONL در `~/.claude/projects/.../<id>.jsonl`. رونوشت‌ها، مدل، فراخوانی ابزار + تفکر، مصرف توکن. |
| **Codex** | آداپتور بتا | Rollout JSONL در `~/.codex/sessions/...`. رونوشت‌ها، مدل، فراخوانی ابزار، مصرف توکن. |
| **Cursor** | آداپتور بتا | SQLite `state.vscdb`. رونوشت‌های چت/کامپوزر، مدل. |
| **Aider** | آداپتور بتا | `.aider.chat.history.md` به‌ازای هر پروژه. رونوشت‌ها، مدل، شمار توکن. |
| **Goose** | آداپتور بتا | SQLite در `~/.local/share/goose`. رونوشت‌ها، مدل، فراخوانی ابزار، مجموع توکن‌ها. |
| **opencode** | آداپتور بتا | SQLite در `~/.local/share/opencode`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Qwen Code** | آداپتور بتا | JSONL در `~/.qwen/projects/.../chats`. رونوشت‌ها، مدل، فراخوانی ابزار، مصرف توکن. |
| **Pi** | آداپتور بتا | JSONL در `~/.pi/agent/sessions`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **Deep Agents** | آداپتور بتا | SQLite در `~/.deepagents/.state/sessions.db`. رونوشت‌ها، مدل، فراخوانی ابزار، توکن‌ها + هزینه. |
| **n8n** | آداپتور بتا | SQLite در `~/.n8n/database.sqlite`. اجراهای گردش‌کار، اجرای نودها، پرامپت‌های AI Agent، مدل + توکن‌ها در جایی که n8n آن‌ها را ثبت می‌کند. |
| **Antigravity** | آداپتور بتا | Brain JSONL زیر `~/.gemini/<flavor>/brain/`. مکالمات، مراحل ابزار، تفکر، تفکیک توکن Gemini به‌ازای هر تولید + هزینه، مصرف تولید در پس‌زمینه. |
| **GitHub Copilot** | آداپتور بتا | Copilot CLI `events.jsonl` زیر `~/.copilot/session-state/` + دفتر مصرف به‌ازای هر فراخوانی `session-store.db`. مکالمات، فراخوانی ابزار، مسیریابی مدل، تفکیک توکن آگاه از کش، هزینه اعتبار هوش مصنوعی صورت‌حساب‌شده توسط فروشنده. |
| **Grok** | آداپتور بتا | xAI Grok Build CLI (باینری Rust زیر `~/.grok/bin/grok`): گزارش رویداد سراسری `~/.grok/logs/unified.jsonl` + `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}` به‌ازای هر نشست. مکالمات، تفکیک توکن به‌ازای هر نوبت، مسیریابی مدل، و محموله خروجی مخزن CLI که در `~/.grok/upload_queue/` قرار می‌گیرد تا ببینید چه چیزی از دستگاه شما خارج شده است. |

"آداپتور بتا" به این معناست که ClawMetry یک خواننده برای فرمت واقعی روی‌دیسک آن ران‌تایم ارائه می‌دهد که هر کدام روی یک نصب واقعی روی یک دستگاه واقعی ساخته و تأیید شده‌اند (به `tests/fixtures/runtimes/<rt>/` مراجعه کنید). آداپتورها فقط‌خواندنی هستند؛ هرکدام درباره آنچه واقعاً ران‌تایمش ذخیره می‌کند صادق است (مثلاً PicoClaw/NanoClaw/Cursor هزینه توکن را روی دیسک نمی‌نویسند). وقتی چند ران‌تایم روی یک نود اجرا می‌شوند، سوئیچر ران‌تایم نمای نشست‌ها را برای بررسی دقیق به یکی محدود می‌کند.

## پیگیری هر ایجنت SDK — انتساب هزینه خارج‌از‌حلقه

همه ران‌تایم‌های بالا نشست‌ها را روی دیسک می‌نویسند. **ایجنت تولیدی** شما، همان که با OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B، یا یک حلقه ساده `httpx` ساخته‌اید، این کار را نمی‌کند. رهگیر بدون‌پیکربندی ClawMetry همچنان با پچ‌زدن مانکی‌پچ `httpx`/`requests` فراخوانی‌های LLM آن (هزینه، توکن‌ها، تأخیر، خطاها) را ثبت می‌کند:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا متغیر محیطی `CLAWMETRY_SOURCE=support-agent`) هر فراخوانی را با یک **منبع نام‌گذاری‌شده** برچسب می‌زند، بنابراین هر محصولی که اجرا می‌کنید به‌عنوان یک خط درجه‌یک و قابل‌انتساب هزینه در کارت **🔌 منابع خارج‌از‌حلقه** داشبورد در تب Overview ظاهر می‌شود؛ فراخوانی‌ها، ارائه‌دهندگان، تأخیر، نرخ خطا به‌ازای هر ایجنت. منبعی تنظیم نشده؟ فراخوانی‌ها همچنان پیگیری می‌شوند؛ فقط کارت پنهان می‌ماند.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

این همان لایه داده‌ای است که آداپتورهای ران‌تایم آن را تغذیه می‌کنند (DuckDB ← اسنپ‌شات ابری)، بنابراین منابع خارج‌از‌حلقه هم مانند بقیه اطلاعات، رمزنگاری‌شده سرتاسر، به داشبورد ابری همگام می‌شوند.

## OpenTelemetry — بدون وابستگی به فروشنده، ترِیس‌های خود را به هر جا بفرستید

ClawMetry با استفاده از **قراردادهای معنایی GenAI**، در هر دو جهت با **OpenTelemetry** صحبت می‌کند، بنابراین ترِیس‌های ایجنت شما هرگز به یک ابزار قفل نمی‌شوند.

**صادرات** هر نشست، فراخوانی‌های LLM، ابزارها، زیرایجنت‌ها، توکن‌ها، هزینه، به‌صورت اسپن‌های OTLP/HTTP GenAI به هر کالکتوری (Datadog، Grafana، Honeycomb، یا کالکتور OTel خودتان):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

هدرهای احراز هویت و بازه نظرسنجی، متغیرهای محیطی اختیاری هستند:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**دریافت** — گیرنده داخلی OTLP، ترِیس‌ها، لاگ‌ها و متریک‌ها را از هر منبع دیگری در `/v1/traces`، `/v1/logs`، و `/v1/metrics` می‌پذیرد. هر برنامه دارای ابزارگذاری OpenTelemetry را به آن اشاره دهید:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

ترِیس‌ها و لاگ‌های OTLP/JSON روی یک `pip install clawmetry` ساده کار می‌کنند، بدون افزونه. دریافت Protobuf (و متریک‌های OTLP/JSON) به `pip install clawmetry[otel]` نیاز دارد. برنامه‌ای که `service.name` خودش را تنظیم کند، به‌عنوان ایجنت مستقل خودش در سوئیچر ران‌تایم، همراه با هزینه و توکن‌های خود، ظاهر می‌شود.

هم داشبورد بدون‌پیکربندی و محلی‌محور ClawMetry را دارید **و هم** داده‌های خود را در هر بک‌اندی که تیم شما از قبل اجرا می‌کند، بدون قفل‌شدن، بدون نیاز به نصب ایجنت دوم.

## پیکربندی

بیشتر افراد به هیچ پیکربندی نیاز ندارند. ClawMetry فضای کاری، لاگ‌ها، نشست‌ها و کرون‌های شما را به‌طور خودکار تشخیص می‌دهد.

اگر نیاز به شخصی‌سازی دارید:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

همه گزینه‌ها: `clawmetry --help`

## کانال‌های پشتیبانی‌شده

ClawMetry فعالیت زنده هر کانال OpenClaw که پیکربندی کرده‌اید را نشان می‌دهد. فقط کانال‌هایی که واقعاً در `openclaw.json` شما تنظیم شده‌اند در نمودار Flow ظاهر می‌شوند؛ کانال‌های پیکربندی‌نشده به‌طور خودکار پنهان می‌شوند.

روی هر گره کانال در Flow کلیک کنید تا نمای زنده حباب‌گفتگو همراه با شمار پیام‌های ورودی/خروجی را ببینید.

| کانال | وضعیت | پاپ‌آپ زنده | یادداشت‌ها |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ کامل | ✅ | پیام‌ها، آمار، بازخوانی هر ۱۰ ثانیه |
| 💬 **iMessage** | ✅ کامل | ✅ | مستقیماً `~/Library/Messages/chat.db` را می‌خواند |
| 💚 **WhatsApp** | ✅ کامل | ✅ | از طریق WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ کامل | ✅ | از طریق signal-cli |
| 🟣 **Discord** | ✅ کامل | ✅ | تشخیص گیلد + کانال |
| 🟪 **Slack** | ✅ کامل | ✅ | تشخیص فضای کاری + کانال |
| 🌐 **Webchat** | ✅ کامل | ✅ | نشست‌های رابط کاربری وب داخلی |
| 📡 **IRC** | ✅ کامل | ✅ | رابط کاربری حباب به سبک ترمینال |
| 🍏 **BlueBubbles** | ✅ کامل | ✅ | iMessage از طریق BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ کامل | ✅ | از طریق وب‌هوک‌های Chat API |
| 🟣 **MS Teams** | ✅ کامل | ✅ | از طریق افزونه بات Teams |
| 🔷 **Mattermost** | ✅ کامل | ✅ | چت تیمی خوداستقرار |
| 🟩 **Matrix** | ✅ کامل | ✅ | غیرمتمرکز، پشتیبانی E2EE |
| 🟢 **LINE** | ✅ کامل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ کامل | ✅ | پیام مستقیم غیرمتمرکز NIP-04 |
| 🟣 **Twitch** | ✅ کامل | ✅ | چت از طریق اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ کامل | ✅ | اشتراک رویداد WebSocket |
| 🔵 **Zalo** | ✅ کامل | ✅ | Zalo Bot API |

> **تشخیص خودکار:** ClawMetry فایل `~/.openclaw/openclaw.json` شما را می‌خواند و فقط کانال‌هایی که واقعاً پیکربندی کرده‌اید را رندر می‌کند. نیازی به تنظیم دستی نیست.

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

> **نکته:** هنگام اجرا در Docker، دایرکتوری‌های داده + لاگ ایجنت خود (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) را مانت کنید تا ClawMetry بتواند تنظیمات شما را به‌طور خودکار تشخیص دهد.

## پیش‌نیازها

- Python 3.8+
- Flask (به‌طور خودکار از طریق pip نصب می‌شود)
- یک ران‌تایم ایجنت هوش مصنوعی روی همان دستگاه: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، n8n، Antigravity، GitHub Copilot، Grok، یا QM (یا حجم‌های مانت‌شده برای Docker)
- Linux یا macOS

## پشتیبانی NemoClaw / OpenShell

ClawMetry به‌طور خودکار [NemoClaw](https://github.com/NVIDIA/NemoClaw) را تشخیص می‌دهد؛ پوشش امنیتی سازمانی NVIDIA برای OpenClaw که ایجنت‌ها را درون کانتینرهای ایزوله‌شده OpenShell اجرا می‌کند.

در بیشتر موارد نیازی به پیکربندی اضافی نیست. دیمن همگام‌سازی به‌طور خودکار فایل‌های نشست را کشف می‌کند، چه در `~/.openclaw/` روی میزبان باشند و چه درون یک کانتینر OpenShell.

### چگونه کار می‌کند

ClawMetry از دو راه NemoClaw را تشخیص می‌دهد:

1. **تشخیص باینری** — بررسی وجود CLI با نام `nemoclaw` و اجرای `nemoclaw status` برای دریافت اطلاعات سندباکس
2. **تشخیص کانتینر** — اسکن کانتینرهای در حال اجرای Docker برای یافتن تصاویر `openshell`، `nemoclaw`، یا `ghcr.io/nvidia/`، سپس خواندن نشست‌ها از طریق مانت حجم یا `docker cp`

فایل‌های نشست همگام‌شده از کانتینرهای NemoClaw با متادیتای `runtime=nemoclaw` و `container_id` در داشبورد ابری برچسب‌گذاری می‌شوند تا بتوانید آن‌ها را در نگاه اول از نشست‌های استاندارد OpenClaw تشخیص دهید.

### تنظیمات پیشنهادی: دیمن همگام‌سازی روی HOST

برای بهترین تجربه، دیمن همگام‌سازی ClawMetry را روی **دستگاه میزبان** (نه درون سندباکس) اجرا کنید. این کار محدودیت‌های خط‌مشی شبکه NemoClaw را دور می‌زند.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

دیمن همگام‌سازی به‌طور خودکار نشست‌ها را درون هر کانتینر OpenShell در حال اجرا پیدا می‌کند.

### اختیاری: نام سندباکس صریح

اگر تشخیص خودکار کار نکرد، ClawMetry را به سندباکس درست هدایت کنید:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### اجرا درون سندباکس (پیشرفته)

اگر باید دیمن همگام‌سازی را **درون** سندباکس OpenShell اجرا کنید، این قانون خروج (egress) را به خط‌مشی شبکه NemoClaw خود اضافه کنید تا بتواند به API دریافت ClawMetry دسترسی پیدا کند:

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
| `localhost:8900` | 8900 | HTTP | بله (رابط کاربری داشبورد محلی) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | برای کشف نشست کانتینر |

دیمن همگام‌سازی فقط تماس‌های HTTPS خروجی به `ingest.clawmetry.com` برقرار می‌کند. هیچ پورت ورودی لازم نیست.

---

## استقرار ابری

برای تونل‌های SSH، پروکسی معکوس، و Docker به **[راهنمای تست ابری](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** مراجعه کنید.

## آزمایش

این پروژه با BrowserStack آزمایش می‌شود.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## تله‌متری

ClawMetry پینگ‌های ناشناس چرخه‌عمر نصب را به
`https://app.clawmetry.com/api/install` ارسال می‌کند: یک پینگ `install` در اولین باری
که CLI با نام `clawmetry` را روی دستگاه جدید اجرا می‌کنید، یک پینگ `update` در اولین
اجرا پس از ارتقا به نسخه جدید، و یک پینگ `onboarded` هنگام تکمیل انتخاب راه‌اندازی اولیه
درون داشبورد. از این برای شمارش نصب‌های واقعی استفاده می‌کنیم (اعداد خام دانلود از PyPI
حدود ۹۸٪ مربوط به میرورها، CI، و دانلود مجدد به‌روزرسانی خودکار هستند) و برای یادگیری
اینکه کدام چارچوب‌ها و نسخه‌های ایجنت واقعاً در حال استفاده هستند.

**حداکثر یک POST به‌ازای هر رویداد چرخه‌عمر به‌ازای هر نسخه**، شامل:

| فیلد | نمونه | چرا |
|---|---|---|
| `install_id` | UUID تصادفی ذخیره‌شده در `~/.clawmetry/install_id` | جلوگیری از تکرار؛ ناشناس تا زمانی که صراحتاً همگام‌سازی Cloud را متصل کنید (سپس ضربان قلب دیمن احرازهویت‌شده آن را حمل می‌کند و این نصب را به حساب شما پیوند می‌دهد) |
| `event` | `install` / `update` / `onboarded` | نصب تازه در برابر ارتقای یک نصب موجود |
| `version` | `0.12.167` | اینکه چه نسخه‌هایی در حال استفاده هستند |
| `os` / `os_version` | `Darwin` / `25.3.0` | اولویت‌های پشتیبانی پلتفرم |
| `python` | `3.11.15` | ماتریس پشتیبانی نسخه پایتون |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | با کدام ایجنت‌ها بعداً باید یکپارچه شویم |
| `is_ci` / `ci_provider` | `true` / `github_actions` | جداسازی نصب‌های انسانی از نویز CI |

**چیزی که ارسال نمی‌کنیم**: IP (سرور ابری کد کشور را سمت‌سرور از درخواست استخراج می‌کند
و سپس IP را دور می‌ریزد)، نام میزبان، نام کاربری، مسیر فضای کاری، محتوای فایل، کلید API شما،
ایمیل شما، هرگونه اطلاعات شخصی یا مختص فضای کاری. محموله سیم قابل ممیزی است در
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**انصراف** (هر یک از این موارد به‌طور دائمی آن را غیرفعال می‌کند):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

خرابی شبکه در اینجا هرگز اجرای `clawmetry` را مسدود نمی‌کند؛ پینگ روی یک ریسه دیمن
با مهلت ۳ ثانیه‌ای و به‌صورت شلیک‌و‌فراموش ارسال می‌شود.

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
