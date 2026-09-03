<!-- i18n-src:9767c8001c9c -->
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

**ببینید عامل شما چگونه فکر می‌کند.** رصد بلادرنگ برای **۳۰ زمان اجرای عامل هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۲۶ مورد دیگر. یک داشبورد برای کل ناوگان عامل‌های شما.

> 🌐 **این را به زبان‌های دیگر بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر →](docs/i18n/)

یک دستور. بدون تنظیمات. همه‌چیز را به‌طور خودکار تشخیص می‌دهد.

```bash
pip install clawmetry && clawmetry
```

در آدرس **http://localhost:8900** باز می‌شود. بدون تنظیمات: زمان‌های اجرای عاملی که از قبل روی سیستم دارید را پیدا می‌کند، آن‌ها را فقط به‌صورت خواندنی می‌خواند، و هیچ چیزی را در نحوهٔ اجرای آن‌ها تغییر نمی‌دهد.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## با ۳۰ زمان اجرای عامل کار می‌کند

**رایگان در برنامهٔ متن‌باز:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**در طرح پولی:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

هر زمان اجرا همان داشبورد را دریافت می‌کند. چند مورد را هم‌زمان اجرا کنید و کلید تعویض در هدر، هر تب را به یکی از آن‌ها بازتنظیم می‌کند.

عامل خودتان را روی یک SDK ساخته‌اید؟ رهگیر تماس‌های LLM آن را هم ردیابی می‌کند. به [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) نگاه کنید.

## چه چیزی به دست می‌آورید

- **نشست‌ها و رونوشت‌ها**: هر عامل چه کاری انجام داد، نوبت به نوبت، همراه با پخش مجدد
- **هزینه و توکن**: به تفکیک زمان اجرا، مدل، نشست و روز، همراه با پرچم‌های ناهنجاری
- **جریان**: نمودار زندهٔ حرکت پیام‌ها میان کانال‌ها، مدل‌ها و ابزارها
- **مغز**: جریان رویدادهای استدلال و فراخوانی ابزار، همان‌طور که رخ می‌دهند
- **انفجار زمینه**: اندازه‌گیری بهره‌برداری از پنجره به تفکیک هر ارائه‌دهنده، فشرده‌سازی در برابر سرریز اجباری، به‌علاوهٔ نقشه‌ای برای هر زمان اجرا از آنچه *نمی‌توانیم* ببینیم ([چگونه](docs/CONTEXT_BLOWOUT.md))
- **حافظه و مهارت‌ها**: فایل‌ها و مهارت‌هایی که هر زمان اجرا واقعاً بارگذاری کرده است
- **سلامت و لاگ‌ها**: دیسک، حافظه، نرخ خطا، محدودیت‌های نرخ، جریان زندهٔ لاگ
- **هشدارها**: سقف بودجه، جهش خطا، آفلاین‌شدن عامل، ارسال به Slack، Discord، PagerDuty، Telegram، ایمیل
- **تأییدها**: توقف فراخوانی‌های ابزار پرریسک *پیش از* اجرا و تأیید از تلفن همراه ([چگونه](docs/APPROVALS.md))

## انفجار زمینه، و هزینهٔ رصد کردن

دو پرسش که پیش از اعتماد به هر ابزار مقایسهٔ عامل‌ها ارزش پاسخ‌دادن دارند.

**چگونه انفجار پنجرهٔ زمینه را در میان زمان‌های اجرا مدیریت می‌کند؟**

درصد بهره‌برداری فقط به‌اندازهٔ صادق‌بودن مخرجش صادق است. ClawMetry اندازهٔ پنجره را به تفکیک هر ارائه‌دهنده از [جدولی که می‌توانید بخوانید و برای آن PR بفرستید](clawmetry/context_windows.py) تعیین می‌کند، که Anthropic، OpenAI، Google، xAI، DeepSeek، Kimi، Qwen، Mistral، Llama و GLM را پوشش می‌دهد. تمام ۲۶ زمان اجرا را با خط‌کش یک فروشنده اندازه‌گیری نمی‌کند. این مهم است: نوبتی ۳۰۰ هزار توکنی از GPT-5 که با معیار ۲۰۰ هزار توکنی Anthropic سنجیده شود، به‌عنوان «بیش از ۱۰۰٪، منفجرشده» خوانده می‌شود، درحالی‌که در واقع ۷۵٪ از ۴۰۰ هزار توکن GPT-5 است. همان خط‌کش، نوبتی ۱۳۰ هزار توکنی از DeepSeek که واقعاً سرریز کرده را به‌عنوان ۶۵٪ راحت پنهان می‌کند.

هر پنجره با منشأ خود ارسال می‌شود: `model_table`، `explicit_marker`، `observed_floor`، یا یک `default` صادقانه وقتی مدل را نمی‌شناسیم. سنجه‌ای که بر پایهٔ حدس ساخته شده هرگز با همان اقتدارِ سنجه‌ای که بر پایهٔ جست‌وجوی جدول ساخته شده نمایش داده نمی‌شود.

ClawMetry فقط در برخی زمان‌های اجرا می‌تواند رویدادهای فشرده‌سازی را ببیند. بنابراین `GET /api/context-coverage` برای هر زمان اجرا گزارش می‌دهد که آیا **صفر به‌معنای «تمیز اجرا شد» است یا «ما نابینا هستیم»**. صفری که واقعاً به‌معنای نابینایی است، همین را می‌گوید. [جزئیات کامل](docs/CONTEXT_BLOWOUT.md)

**ابزارسازی چه هزینه‌ای دارد؟**

| مسیر | افزوده‌شده به عامل شما | پیش‌فرض؟ |
|---|---|---|
| دنبال‌کردن فایل نشست (هر ۳۰ زمان اجرا) | **۰**. فرآیندی جداگانه، بدون کد ClawMetry در عامل شما | روشن |
| رهگیر HTTP (`CLAWMETRY_INTERCEPT=1`) | **+۰٫۴۴ میلی‌ثانیه** به ازای هر فراخوانی LLM، یا ۰٫۰۰۹٪ از یک فراخوانی ۵ ثانیه‌ای | خاموش |
| دروازهٔ هوک پیش از ابزار (کش گرم) | **+۴۴ میلی‌ثانیه** به ازای هر فراخوانی ابزار دروازه‌شده، روی کف ۳۶ میلی‌ثانیه‌ای مفسر | خاموش |
| پروکسی اجرایی | **+۹٫۷ میلی‌ثانیه** به ازای هر فراخوانی LLM | خاموش |

هزینهٔ میزبان دیمن: **۲٬۷۶۲ رویداد در ثانیه** دریافت، **۷۱۰ بایت در رویداد** روی دیسک (۶۷٫۷ مگابایت به ازای هر ۱۰۰ هزار رویداد)، و **~۱۲٪ از یک هسته** به‌طور پایدار روی یک نصب پرمشغله. آن عدد آخر بیش از بودجهٔ اعلام‌شدهٔ خودمان یعنی ۵ تا ۱۰٪ است، پس به‌عنوان یک باگ برای رفع‌کردن منتشر شده، نه اینکه از صفحه حذف شود.

اندازه‌گیری‌شده روی یک Apple M2 Pro با `benchmarks/overhead.py`. این هارنس هر شرایط را در فرآیندی جداگانه اجرا می‌کند، ترتیب آن‌ها را جابه‌جا می‌کند، و **وقتی دورها بر سر علامت عدد توافق ندارند از چاپ آن خودداری می‌کند**. آن را روی دستگاه خودتان در یک دقیقه اجرا کنید:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

هر مسیر اندازه‌گیری می‌شود، از جمله دروازه‌های هوک و پروکسی اجرایی، و این هارنس در CI روی Linux، macOS و Windows اجرا می‌شود. دو نتیجه که ارزش دانستن دارد: پروکسی روی Windows تقریباً هفت برابر بیشتر از Linux هزینه دارد، و دیمن هم‌اکنون به‌طور پایدار حدود ۱۲٪ از یک هسته را مصرف می‌کند، که بیش از بودجهٔ ۵ تا ۱۰٪ خودمان است. داده‌های خام JSON، روش کار، و آنچه هنوز اندازه‌گیری نشده در [docs/OVERHEAD.md](docs/OVERHEAD.md) است.

## قیمت‌گذاری

| طرح | چه چیزی را پوشش می‌دهد | قیمت |
|---|---|---|
| **رایگان** | OpenClaw + NVIDIA NemoClaw + Goose، داشبورد کامل، فقط محلی | $0 |
| **Starter** | تمام زمان‌های اجرای دیگر بالا، نمای ناوگان، همگام‌سازی ابری | $9 به ازای هر گره در ماه |
| **Pro** | Starter به‌علاوهٔ کنترل و ارزیابی: تأییدها، سیاست‌های ریسک ابزار، ارزیابی‌ها، تشخیص ناهنجاری، بهینه‌ساز هزینه، خروجی OTel، لاگ حسابرسی ضدتغییر | $19 به ازای هر گره در ماه |

طرح‌های سالانه، Enterprise و اعداد فعلی در
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** موجود است. کلیدهای مجوز خوداستقرار
بدون نیاز به ابر کار می‌کنند (`clawmetry license`). تقسیم دقیق رایگان/پولی
در [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) آمده است.

## داده‌های شما روی دستگاه شما می‌ماند

ClawMetry فایل‌های نشست و لاگ‌های محلی را می‌خواند. **هیچ داده‌ای از نشست از دستگاه شما خارج نمی‌شود
مگر آنکه `clawmetry connect` را اجرا کنید** — نه پرامپت‌ها، پاسخ‌ها، آرگومان‌های ابزار، محتوای فایل
یا خطوط لاگ. وقتی متصل می‌شوید، اسنپ‌شات با رمزنگاری سرتاسری
با کلیدی که هرگز از دستگاه شما خارج نمی‌شود رمزگذاری می‌شود، و در مرورگر شما رمزگشایی می‌شود. اگر
گره‌ای کلیدی نداشته باشد، بارگذاری نادیده گرفته می‌شود به‌جای ارسال به‌صورت رمزنگاری‌نشده، و هیچ
پاسخ سروری نمی‌تواند این را خاموش کند.

دو چیز به‌طور پیش‌فرض پیش از اتصال شما اجرا می‌شوند، هر دو اختیاری (opt-out) و هیچ‌کدام
حامل داده‌های نشست: یک پینگ نصب ناشناس و یک بررسی نسخه در برابر
PyPI. یک نصب پیش‌فرض همچنین یک‌بار IP عمومی شما را برای یک خط بنر آغازین
جست‌وجو می‌کند. هر مقصد، آنچه حمل می‌کند و نحوهٔ خاموش‌کردن آن در
[docs/EGRESS.md](docs/EGRESS.md) فهرست شده است؛ نصب‌های خوداستقرار، تغییرمسیریافته و ایزوله
هیچ تماس خروجی اختیاری‌ای انجام نمی‌دهند.

رمزگشایی در مرورگر شما رخ می‌دهد، در کدی که ما به شما ارائه می‌دهیم. این قبلاً
یک وعده بود؛ اکنون چیزی است که می‌توانید بررسی کنید. هر خطی که با کلید شما سروکار دارد
در یک فایل قابل‌خواندن قرار دارد، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
که درون wheel ارسال می‌شود و عیناً همان‌طور که هست ارائه می‌شود، با یک هش Subresource
Integrity سنجاق‌شده. برای تأیید اینکه مرورگر همان چیزی را اجرا می‌کند که ما منتشر کرده‌ایم:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

چیزی که این کار ثابت نمی‌کند: ما صفحه‌ای که این فایل را بارگذاری می‌کند نیز ارائه می‌دهیم، پس
می‌توانستیم صفحهٔ متفاوتی ارائه دهیم. هش‌های یکپارچگی شما را در برابر یک CDN آلوده محافظت
می‌کنند، نه در برابر خود فروشنده. آنچه به دست می‌آورید این است که هر جایگزینی باید
عمدی، در سورس صفحه قابل‌مشاهده، و متفاوت از یک artifact روی PyPI باشد
که هرکسی می‌تواند آن را دریافت کند. خوداستقرار یا ماندن فقط‌محلی این وابستگی را
به‌طور کامل حذف می‌کند.

## نصب

```bash
pip install clawmetry     # سپس: clawmetry
```

یا این دستور یک‌خطی: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

به Python 3.8+ روی macOS، Linux یا Windows، و حداقل یک زمان اجرای عامل روی
همان دستگاه نیاز دارد. دستورالعمل‌های Docker: [docs/DOCKER.md](docs/DOCKER.md).

## مستندات

| | |
|---|---|
| [سازگاری زمان اجرا](docs/compatibility.md) | هر آداپتور چه چیزی را می‌خواند، و چگونه یک زمان اجرا اضافه کنیم |
| [انفجار زمینه](docs/CONTEXT_BLOWOUT.md) | پنجره‌ها به تفکیک هر ارائه‌دهنده، فشرده‌سازی در برابر سرریز، پوشش به تفکیک هر زمان اجرا |
| [سربار](docs/OVERHEAD.md) | هزینهٔ ابزارسازی، اندازه‌گیری‌شده، همراه با هارنس برای بازتولید آن |
| [استحقاق‌ها](docs/ENTITLEMENTS.md) | رایگان در برابر پولی، ماتریس ردهٔ سرویس، خط فرمان مجوز |
| [تأییدها و سیاست‌ها](docs/APPROVALS.md) | دروازه‌بانی پیش از اجرا، امتیازدهی ریسک، تأیید از تلفن |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صدور trace به هر جا، دریافت OTLP از هر چیز |
| [عامل خودتان را بیاورید](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، Pydantic AI، LangChain از ابتدا تا انتها، همراه با نمونه‌های قابل‌اجرا |
| [ردیابی SDK](docs/SDK_TRACKING.md) | انتساب هزینه برای عامل‌هایی که خودتان ساخته‌اید |
| [کانال‌های چت](docs/CHANNELS.md) | آداپتورهای چت نمایش‌داده‌شده در Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | راه‌اندازی‌های ایزوله‌شدهٔ NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | تصویر، compose، اتصال volume |
| [معماری](ARCHITECTURE.md) · [توسعه](docs/DEVELOPMENT.md) | نحوهٔ کارکرد درونی آن؛ اجرا از سورس |
| [تله‌متری](docs/TELEMETRY.md) | پینگ‌های ناشناس نصب و باز‌شدن دسکتاپ، و نحوهٔ خاموش‌کردن آن‌ها |

## اسکرین‌شات‌ها

هر عدد در زیر از یک دستگاه واقعی است، فقط‌خواندنی، بدون هیچ داده‌ای که از پیش کاشته شده باشد.

**به شما می‌گوید چه زمانی چیزی اشتباه است، نه فقط چه اتفاقی افتاد.**
دو بنر ناهنجاری در بالا: هزینهٔ در حال اجرا ۷ برابر میانگین روزانه، و یک
جهش هزینهٔ ۴٫۲ برابری. زیر آن‌ها، ۳۲۴ از ۶۶۷ نشست اخیر حامل یک
سیگنال هدررفت، به‌تفکیک علت.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**به شما نشان می‌دهد پول کجا رفت، در هر بازه.**
$۲۵۲٫۴۷ امروز، $۵۱۳٫۱۵ این هفته، $۱٬۳۱۲٫۹۲ این ماه، هرکدام همراه با توکن‌های
پشت آن‌ها و اینکه اشتراک شما چقدر از آن را از قبل پوشش می‌دهد. زیر آن، حدود
$۱٬۱۲۸ در ماه به‌عنوان قابل‌بازیافت فهرست‌شده و $۱۷٬۲۵۶ در ماه از قبل با استفادهٔ مجدد
از کش صرفه‌جویی شده.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**نشان می‌دهد یک پیام چگونه به پاسخ تبدیل می‌شود.**
نمودار جریان زنده: شما، کانالی که پیام روی آن وارد شد، دروازه، مدلی که
هم‌اکنون پاسخ می‌دهد، و هر ابزاری که به سراغش رفت. گره‌ها با حرکت کار
از میان آن‌ها روشن می‌شوند.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**هر عامل روی دستگاه، در یک جدول.**
چه چیزی اجرا می‌کند، در ۲۴ ساعت گذشته و در طول عمرش چه هزینه‌ای دارد، چه زمانی
آخرین‌بار دیده شد، مالک آن کیست، و آیا یک اشتراک صورت‌حساب را پوشش می‌دهد. ۱۴ عامل اینجا،
۳ نشست در حال کار، ۱۳ ساکت.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**نشان می‌دهد زمان و پول یک نوبت به کجا رفت، ابزار به ابزار.**
یک نوبت از یک نشست واقعی: ۱۱ ابزار در ۱۱٫۲ دقیقه به قیمت $۱٫۱۶. هر
فراخوانی Bash و فراخوانی مدل نوار زمانی خودش را در جدول زمانی دارد، پس دستوری
که ۴٫۱ دقیقه اجرا شد و آنی که ۲۲۶ میلی‌ثانیه اجرا شد در یک نگاه از هم جدا می‌شوند.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**کار را نمره می‌دهد، نه فقط هزینه را.**
یک A در این هفته: ۵۴ وظیفه تمیز برگشتند، ۲ مورد ناهموار $۴۸٫۵۷ هزینه داشتند، و
اجراهایی که فعالیت خیلی کمی برای قضاوت داشتند از نمره‌دهی کنار گذاشته شدند به‌جای اینکه
به‌عنوان برد شمرده شوند. هر اجرای ناهموار به ردیابی خودش پیوند دارد.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**نشان می‌دهد چرا پنجرهٔ زمینه مدام پر می‌شود.**
۷۱۵ هزار از یک پنجرهٔ ۱ میلیون توکنی در آخرین نوبت، یک اوج ۸۳٫۳٪، ۴ فشرده‌سازی
که همگی به‌صورت پیش‌دستانه شلیک شدند نه در پی سرریز، به‌علاوهٔ بهره‌برداری
هر نوبت پشت آن.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**تشخیص بدون هیچ تنظیمی از سوی شما اجرا می‌شود.**
تشخیص‌گرهای داخلی از زمان نصب روشن هستند: عامل ساکت شد، خوراک تله‌متری
متوقف شد، جهش هزینه، انفجار توکن، خطاهای رو به افزایش، جهش خطا، آستانهٔ
بودجه، امضای تهدید مطابقت‌یافته، یافتهٔ ابزار امنیتی، تغییر وضعیت امنیتی.
قوانین خودتان اختیاری و افزونه بر این‌ها هستند.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**نگه‌داشتن یک فراخوانی پرریسک اختیاری است، و به‌صورت خاموش ارسال می‌شود.**
حذف‌های بازگشتی، force push، sudo، اطلاعات محرمانه، نصب بسته‌ها و تماس‌های
خروجی هرکدام قانونی دارند که می‌توانید روشن کنید. تا وقتی این کار را نکنید، ClawMetry
تماشا می‌کند و هیچ چیزی را تغییر نمی‌دهد. وقتی یکی روشن شود، فراخوانی‌های
منطبق اینجا (یا روی تلفن شما) برای تأیید یا رد منتظر می‌مانند.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

بیشتر، به تفکیک هر زمان اجرا: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## تاریخچهٔ ستاره‌ها

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## مجوز

MIT · ساخته‌شده توسط [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
