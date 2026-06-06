<!-- i18n-src:48548997be76 -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

** شما را در یک داشبورد اندازه‌گیری می‌کند و هر محیط اجرا را به‌صورت خودکار در دستگاه شما تشخیص می‌دهد:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw و NemoClaw در نسخه متن‌باز رایگان هستند؛ سایر محیط‌های اجرا با ClawMetry Cloud یا مجوز Pro خودمیزبان فعال می‌شوند. محیط‌های اجرا را از هدر تغییر دهید و هر برگه، شامل هزینه، توکن‌ها، ابزارها و ردیابی‌ها، برای آن محیط اجرا مجدداً محدوده‌بندی می‌شود.

## آنچه دریافت می‌کنید

- **Flow**: نمودار متحرک زنده نشان‌دهنده جریان پیام‌ها از طریق کانال‌ها، مغز، ابزارها و بازگشت
- **Overview**: بررسی سلامت، نقشه حرارتی فعالیت، تعداد جلسات، اطلاعات مدل
- **Usage**: ردیابی توکن و هزینه با تفکیک روزانه/هفتگی/ماهانه
- **Sessions**: جلسات فعال عامل با مدل، توکن‌ها، آخرین فعالیت
- **Crons**: کارهای زمان‌بندی‌شده با وضعیت، اجرای بعدی، مدت زمان
- **Logs**: جریان لاگ بلادرنگ با رنگ‌بندی
- **Memory**: مرور SOUL.md، MEMORY.md، AGENTS.md، یادداشت‌های روزانه
- **Transcripts**: رابط کاربری حباب چت برای خواندن تاریخچه جلسات
- **Alerts**: سقف بودجه، محرک‌های نرخ خطا، تشخیص آفلاین بودن عامل؛ ارسال به Slack، Discord، PagerDuty، Telegram، Email
- **Approvals**: کنترل حذف‌های مخرب، پوش‌های اجباری، تغییرات پایگاه داده، sudo، نصب بسته‌ها، فراخوانی‌های شبکه پشت تأیید تک‌کلیکی

## تصاویر

### 🧠 Brain: جریان رویداد زنده عامل
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview: استفاده از توکن و خلاصه جلسه
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow: فید فراخوانی ابزار بلادرنگ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens: تفکیک هزینه بر اساس مدل و جلسه
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory: مرورگر فایل فضای کاری
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security: وضعیت امنیتی و لاگ حسابرسی
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts: سقف بودجه، محرک‌های نرخ خطا، وب‌هوک‌ها به Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals: کنترل فراخوانی‌های ابزار پرخطر پشت تأیید دستی؛ قوانین حفاظتی مبتنی بر سیاست
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

## توسعه فرانت‌اند نسخه v2

اپلیکیشن React نسخه v2 در `frontend/` قرار دارد و زمانی که سرور Flask با فعال بودن v2 راه‌اندازی شود، در `/v2` سرویس‌دهی می‌شود.

در حین توسعه از دو ترمینال استفاده کنید:

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

آدرس `http://localhost:5173/v2/` را باز کنید. Vite درخواست‌های `/api` را به `http://localhost:8900` پروکسی می‌کند، بنابراین اپلیکیشن React می‌تواند بدون تنظیمات اضافی CORS با سرور Flask محلی ارتباط برقرار کند.

برای ساخت باندلی که همراه پکیج Python ارسال می‌شود:

```bash
cd frontend
npm run build
```

باندل تولید در `clawmetry/static/v2/dist/` نوشته می‌شود.

## سازگاری محیط اجرا / عامل

ClawMetry بسیاری از محیط‌های اجرای عامل هوش مصنوعی را مشاهده می‌کند، نه فقط OpenClaw. هر محیط اجرای غیر از OpenClaw با یک آداپتور خواننده اختصاصی ارائه می‌شود که فرمت جلسه بومی آن را به اشکال یکپارچه ClawMetry ترجمه می‌کند؛ دیمن آن‌ها را با برچسب محیط اجرا به همان ذخیره DuckDB و عکس‌فوری ابری وارد می‌کند، و برگه پخش مجدد جلسه یک **سوئیچر محیط اجرا** را زمانی که بیش از یک مورد وجود دارد نشان می‌دهد. برای ماتریس کامل و راهنمای افزودن محیط‌های اجرا به [`docs/compatibility.md`](docs/compatibility.md) مراجعه کنید، و برای مقدمه خانواده OpenClaw به [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) مراجعه کنید.

| محیط اجرا / عامل | وضعیت | یادداشت‌ها |
|---|---|---|
| **OpenClaw** | بومی | محیط اجرای مرجع، خودکار تشخیص داده می‌شود |
| **PicoClaw** | آداپتور بتا | JSONL مسطح `providers.Message` (`~/.picoclaw/workspace/sessions`). رونوشت‌ها، مدل، فراخوانی‌های ابزار. |
| **NanoClaw** | آداپتور بتا | SQLite هر جلسه (`data/v2-sessions`). رونوشت‌ها و تعداد پیام‌ها. |
| **Hermes** | آداپتور بتا | SQLite `~/.hermes/state.db`. رونوشت‌ها، مدل، توکن‌ها/هزینه. |
| **Claude Code** | آداپتور بتا | JSONL `~/.claude/projects/.../<id>.jsonl`. رونوشت‌ها، مدل، فراخوانی‌های ابزار و تفکر، استفاده از توکن. |
| **Codex** | آداپتور بتا | JSONL Rollout `~/.codex/sessions/...`. رونوشت‌ها، مدل، فراخوانی‌های ابزار، استفاده از توکن. |
| **Cursor** | آداپتور بتا | SQLite `state.vscdb`. رونوشت‌های چت/کامپوزر، مدل. |
| **Aider** | آداپتور بتا | `.aider.chat.history.md` برای هر پروژه. رونوشت‌ها، مدل، تعداد توکن‌ها. |
| **Goose** | آداپتور بتا | SQLite `~/.local/share/goose`. رونوشت‌ها، مدل، فراخوانی‌های ابزار، مجموع توکن‌ها. |
| **opencode** | آداپتور بتا | SQLite `~/.local/share/opencode`. رونوشت‌ها، مدل، فراخوانی‌های ابزار، توکن‌ها و هزینه. |
| **Qwen Code** | آداپتور بتا | JSONL `~/.qwen/projects/.../chats`. رونوشت‌ها، مدل، فراخوانی‌های ابزار، استفاده از توکن. |

«آداپتور بتا» به این معناست که ClawMetry یک خواننده برای فرمت واقعی روی دیسک آن محیط اجرا ارائه می‌دهد که هرکدام در برابر یک نصب واقعی روی یک دستگاه واقعی ساخته و تأیید شده‌اند (به `tests/fixtures/runtimes/<rt>/` مراجعه کنید). آداپتورها فقط‌خواندنی هستند؛ هر کدام در مورد آنچه محیط اجرا واقعاً ذخیره می‌کند صادقانه عمل می‌کند (مثلاً PicoClaw/NanoClaw/Cursor هزینه توکن را روی دیسک نمی‌نویسند). وقتی چندین محیط اجرا روی یک گره اجرا می‌شوند، سوئیچر محیط اجرا نمای جلسات را به یکی محدود می‌کند تا بررسی عمیق تمیزی داشته باشید.

## ردیابی هر عامل SDK: انتساب هزینه خارج از حلقه

همه محیط‌های اجرای بالا جلسات را روی دیسک می‌نویسند. **عامل تولیدی** خودتان، آنی که روی OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B یا یک حلقه ساده `httpx` ساخته‌اید، این کار را نمی‌کند. رهگیر بدون پیکربندی ClawMetry همچنان فراخوانی‌های LLM آن را (هزینه، توکن‌ها، تأخیر، خطاها) از طریق monkey-patching `httpx`/`requests` ضبط می‌کند:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا متغیر محیطی `CLAWMETRY_SOURCE=support-agent`) هر فراخوانی را با یک **منبع نامگذاری‌شده** برچسب می‌زند، بنابراین هر محصولی که اجرا می‌کنید به‌عنوان یک خط درجه یک قابل انتساب به هزینه در کارت **🔌 Out-loop sources** در بخش Overview داشبورد نشان داده می‌شود که شامل فراخوانی‌ها، ارائه‌دهندگان، تأخیر و نرخ خطا به ازای هر عامل است. منبعی تنظیم نشده؟ فراخوانی‌ها همچنان ردیابی می‌شوند؛ کارت فقط پنهان می‌ماند.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

این همان لایه داده‌ای است که آداپتورهای محیط اجرا به آن تغذیه می‌کنند (DuckDB به عکس‌فوری ابری)، بنابراین منابع خارج از حلقه مانند سایر موارد، با رمزنگاری سرتاسر، با داشبورد ابری همگام‌سازی می‌شوند.

## OpenTelemetry: بدون وابستگی به فروشنده، ردیابی‌های خود را به هر جایی ارسال کنید

ClawMetry در هر دو جهت با **OpenTelemetry** ارتباط برقرار می‌کند و از **قراردادهای معنایی GenAI** استفاده می‌کند، بنابراین ردیابی‌های عامل شما هرگز به یک ابزار وابسته نمی‌شوند.

**صادر کنید** هر جلسه را، شامل فراخوانی‌های LLM، ابزارها، زیرعامل‌ها، توکن‌ها و هزینه، به‌عنوان span های GenAI OTLP/HTTP به هر جمع‌آوری‌کننده‌ای (Datadog، Grafana، Honeycomb یا OTel Collector خودتان):

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

**دریافت**: گیرنده OTLP داخلی، ردیابی‌ها و متریک‌ها را از هر چیز دیگری در `/v1/traces` و `/v1/metrics` می‌پذیرد (`pip install clawmetry[otel]` برای دریافت protobuf).

داشبورد ClawMetry بدون پیکربندی و محلی‌اول را **و** داده‌های خود را در هر بک‌اندی که تیم شما از قبل اجرا می‌کند دریافت می‌کنید. بدون وابستگی، بدون نیاز به نصب عامل دوم.

## پیکربندی

اکثر افراد به هیچ پیکربندی نیاز ندارند. ClawMetry فضای کاری، لاگ‌ها، جلسات و cron های شما را به‌صورت خودکار تشخیص می‌دهد.

اگر نیاز به سفارشی‌سازی دارید:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

همه گزینه‌ها: `clawmetry --help`

## کانال‌های پشتیبانی‌شده

ClawMetry فعالیت زنده برای هر کانال OpenClaw که پیکربندی کرده‌اید نشان می‌دهد. تنها کانال‌هایی که واقعاً در `openclaw.json` شما تنظیم شده‌اند در نمودار Flow ظاهر می‌شوند و کانال‌های پیکربندی‌نشده به‌صورت خودکار پنهان می‌شوند.

روی هر گره کانال در Flow کلیک کنید تا نمای حباب چت زنده با تعداد پیام‌های ورودی/خروجی را ببینید.

| کانال | وضعیت | پاپ‌آپ زنده | یادداشت‌ها |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ کامل | ✅ | پیام‌ها، آمار، بازخوانی ۱۰ ثانیه |
| 💬 **iMessage** | ✅ کامل | ✅ | مستقیماً `~/Library/Messages/chat.db` را می‌خواند |
| 💚 **WhatsApp** | ✅ کامل | ✅ | از طریق WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ کامل | ✅ | از طریق signal-cli |
| 🟣 **Discord** | ✅ کامل | ✅ | تشخیص Guild و کانال |
| 🟪 **Slack** | ✅ کامل | ✅ | تشخیص Workspace و کانال |
| 🌐 **Webchat** | ✅ کامل | ✅ | جلسات رابط وب داخلی |
| 📡 **IRC** | ✅ کامل | ✅ | رابط حباب به سبک ترمینال |
| 🍏 **BlueBubbles** | ✅ کامل | ✅ | iMessage از طریق BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ کامل | ✅ | از طریق وب‌هوک‌های Chat API |
| 🟣 **MS Teams** | ✅ کامل | ✅ | از طریق افزونه Teams bot |
| 🔷 **Mattermost** | ✅ کامل | ✅ | چت تیمی خودمیزبان |
| 🟩 **Matrix** | ✅ کامل | ✅ | غیرمتمرکز، پشتیبانی از E2EE |
| 🟢 **LINE** | ✅ کامل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ کامل | ✅ | پیام‌های مستقیم غیرمتمرکز NIP-04 |
| 🟣 **Twitch** | ✅ کامل | ✅ | چت از طریق اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ کامل | ✅ | اشتراک رویداد WebSocket |
| 🔵 **Zalo** | ✅ کامل | ✅ | Zalo Bot API |

> **تشخیص خودکار:** ClawMetry فایل `~/.openclaw/openclaw.json` شما را می‌خواند و تنها کانال‌هایی را که واقعاً پیکربندی کرده‌اید نمایش می‌دهد. هیچ تنظیم دستی لازم نیست.

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

**مثال Docker Compose:**

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

> **توجه:** هنگام اجرا در Docker، دایرکتوری‌های داده و لاگ عامل خود را (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) مانت کنید تا ClawMetry بتواند تنظیمات شما را به‌صورت خودکار تشخیص دهد.

## پیش‌نیازها

- Python 3.8+
- Flask (به‌صورت خودکار از طریق pip نصب می‌شود)
- یک محیط اجرای عامل هوش مصنوعی در همان دستگاه: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw یا PicoClaw (یا volumeهای مانت‌شده برای Docker)
- Linux یا macOS

## پشتیبانی از NemoClaw / OpenShell

ClawMetry به‌صورت خودکار [NemoClaw](https://github.com/NVIDIA/NemoClaw) را تشخیص می‌دهد، پوشش امنیتی سازمانی NVIDIA برای OpenClaw که عامل‌ها را داخل کانتینرهای OpenShell جعبه‌شن اجرا می‌کند.

در اکثر موارد هیچ پیکربندی اضافی لازم نیست. دیمن همگام‌سازی فایل‌های جلسه را به‌صورت خودکار کشف می‌کند، چه در `~/.openclaw/` روی میزبان باشند چه داخل یک کانتینر OpenShell.

### نحوه کارکرد

ClawMetry به دو روش NemoClaw را تشخیص می‌دهد:

1. **تشخیص باینری**: وجود CLI `nemoclaw` را بررسی می‌کند و `nemoclaw status` را برای دریافت اطلاعات جعبه‌شن اجرا می‌کند
2. **تشخیص کانتینر**: کانتینرهای Docker در حال اجرا را برای تصاویر `openshell`، `nemoclaw` یا `ghcr.io/nvidia/` اسکن می‌کند، سپس جلسات را از طریق مانت‌های volume یا `docker cp` می‌خواند

فایل‌های جلسه همگام‌سازی‌شده از کانتینرهای NemoClaw با متادیتای `runtime=nemoclaw` و `container_id` در داشبورد ابری برچسب‌گذاری می‌شوند، بنابراین می‌توانید آن‌ها را در یک نگاه از جلسات استاندارد OpenClaw تشخیص دهید.

### تنظیم توصیه‌شده: دیمن همگام‌سازی روی میزبان

برای بهترین تجربه، دیمن همگام‌سازی ClawMetry را روی **دستگاه میزبان** (نه داخل جعبه‌شن) اجرا کنید. این کار از محدودیت‌های سیاست شبکه NemoClaw اجتناب می‌کند.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

دیمن همگام‌سازی به‌صورت خودکار جلسات را داخل هر کانتینر OpenShell در حال اجرا پیدا می‌کند.

### اختیاری: نام صریح جعبه‌شن

اگر تشخیص خودکار کار نکرد، ClawMetry را به جعبه‌شن درست هدایت کنید:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### اجرا داخل جعبه‌شن (پیشرفته)

اگر باید دیمن همگام‌سازی را **داخل** جعبه‌شن OpenShell اجرا کنید، این قانون خروجی را به سیاست شبکه NemoClaw خود اضافه کنید تا بتواند به API ورودی ClawMetry دسترسی داشته باشد:

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

### پورت‌ها و اندپوینت‌ها

| اندپوینت | پورت | پروتکل | الزامی |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | بله (دیمن همگام‌سازی به ابر) |
| `localhost:8900` | 8900 | HTTP | بله (رابط کاربری داشبورد محلی) |
| سوکت Docker (`/var/run/docker.sock`) | — | Unix socket | برای کشف جلسات کانتینر |

دیمن همگام‌سازی تنها فراخوانی‌های HTTPS خروجی به `ingest.clawmetry.com` انجام می‌دهد. هیچ پورت ورودی لازم نیست.

---

## استقرار ابری

برای تونل‌های SSH، پراکسی معکوس و Docker به **[راهنمای تست ابری](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** مراجعه کنید.

## آزمایش

این پروژه با BrowserStack آزمایش شده است.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## تله‌متری

ClawMetry اولین باری که CLI `clawmetry` را روی یک دستگاه جدید اجرا می‌کنید، یک ping ناشناس «اولین اجرا» به
`https://app.clawmetry.com/api/install` ارسال می‌کند. از این برای شمارش نصب‌ها (تنها متریک بازاریابی که برای یک پروژه OSS داریم) و برای یادگیری اینکه کاربران ما کدام چارچوب‌های عامل را نصب کرده‌اند استفاده می‌کنیم.

**دقیقاً یک POST به ازای هر نصب**، شامل:

| فیلد | مثال | دلیل |
|---|---|---|
| `install_id` | UUID تصادفی ذخیره‌شده در `~/.clawmetry/install_id` | حذف تکراری؛ به ایمیل یا api_key شما مرتبط نیست |
| `version` | `0.12.167` | چه نسخه‌هایی در دسترس هستند |
| `os` / `os_version` | `Darwin` / `25.3.0` | اولویت‌های پشتیبانی از پلتفرم |
| `python` | `3.11.15` | ماتریس پشتیبانی از نسخه Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | با کدام عامل‌ها باید بعداً یکپارچه شویم |
| `is_ci` / `ci_provider` | `true` / `github_actions` | جدا کردن نصب‌های انسانی از نویز CI |

**آنچه ارسال نمی‌کنیم**: IP (ابر کد کشور را سمت سرور از درخواست استخراج می‌کند، سپس IP را دور می‌اندازد)، hostname، نام کاربری، مسیر فضای کاری، محتویات فایل، api_key شما، ایمیل شما، هر چیز PII یا مربوط به فضای کاری. بار wire در [`clawmetry/telemetry.py`](clawmetry/telemetry.py) قابل بررسی است.

**انصراف** (هر یک از این‌ها آن را به‌طور دائمی غیرفعال می‌کند):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

خرابی شبکه در اینجا هرگز مانع اجرای `clawmetry` نمی‌شود. ping به‌صورت fire-and-forget روی یک thread دیمن با تایم‌اوت ۳ ثانیه اجرا می‌شود.

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
  <sub>ساخته شده توسط <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · بخشی از اکوسیستم <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
