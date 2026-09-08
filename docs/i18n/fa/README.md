<!-- i18n-src:88be2deff5d5 -->
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

**ببینید عامل هوشمند شما چگونه فکر می‌کند.** رصد بلادرنگ برای **۳۰ زمان اجرای عامل هوش مصنوعی**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و ۲۶ مورد دیگر. یک داشبورد برای کل ناوگان عامل‌های شما.

> 🌐 **این را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر ←](docs/i18n/)

یک دستور. بدون پیکربندی. تشخیص خودکار همه‌چیز.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود. بدون پیکربندی: زمان‌های اجرای عاملی که از قبل دارید را پیدا می‌کند، آن‌ها را فقط برای خواندن می‌خواند و هیچ تغییری در نحوهٔ اجرای آن‌ها ایجاد نمی‌کند.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## با ۳۰ زمان اجرای عامل کار می‌کند

**رایگان در برنامهٔ متن‌باز:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**در طرح پولی:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

هر زمان اجرا داشبورد یکسانی دریافت می‌کند. چند مورد را همزمان اجرا کنید و کلید‌گردان بالای صفحه هر برگه را به یکی از آن‌ها بازتنظیم می‌کند.

عامل خودتان را روی یک SDK ساخته‌اید؟ رهگیر (interceptor) فراخوانی‌های LLM آن را هم دنبال می‌کند. به [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) مراجعه کنید.

## چه چیزی به دست می‌آورید

- **جلسات و رونوشت‌ها**: هر عامل نوبت‌به‌نوبت چه کرده، همراه با پخش مجدد
- **هزینه و توکن**: به تفکیک زمان اجرا، مدل، جلسه و روز، همراه با پرچم‌های ناهنجاری
- **جریان**: نمودار زندهٔ جابه‌جایی پیام‌ها میان کانال‌ها، مدل‌ها و ابزارها
- **مغز**: جریان رویدادهای استدلال و فراخوانی ابزار، همان‌طور که رخ می‌دهد
- **انفجار زمینه (context blowout)**: میزان استفاده از پنجره متناسب با هر ارائه‌دهنده، فشرده‌سازی در برابر سرریز اجباری، به‌علاوهٔ نقشه‌ای برای هر زمان اجرا از آن‌چه که *نمی‌توانیم* ببینیم ([چگونه](docs/CONTEXT_BLOWOUT.md))
- **حافظه و مهارت‌ها**: فایل‌ها و مهارت‌هایی که هر زمان اجرا واقعاً بارگذاری کرده
- **سلامت و گزارش‌ها**: دیسک، حافظه، نرخ خطا، محدودیت نرخ، جریان زندهٔ گزارش
- **هشدارها**: سقف بودجه، جهش‌های خطا، آفلاین‌شدن عامل، ارسال به Slack، Discord، PagerDuty، Telegram، ایمیل
- **تأییدها**: توقف فراخوانی‌های ابزار پرریسک *پیش از* اجرا و تأیید از گوشی شما ([چگونه](docs/APPROVALS.md))

## انفجار زمینه، و هزینهٔ رصد کردن

دو پرسش که پیش از اعتماد به هر ابزار مقایسهٔ عامل ارزش پاسخ‌دادن دارند.

**چگونه با انفجار پنجرهٔ زمینه در میان زمان‌های اجرا برخورد می‌کند؟**

درصد میزان استفاده تنها به‌اندازهٔ صداقتِ مخرجی که بر آن تقسیم می‌شود، صادق است. ClawMetry اندازهٔ پنجره را به تفکیک هر ارائه‌دهنده از [جدولی که می‌توانید بخوانید و برای آن PR بفرستید](clawmetry/context_windows.py) تعیین می‌کند که Anthropic، OpenAI، Google، xAI، DeepSeek، Kimi، Qwen، Mistral، Llama و GLM را پوشش می‌دهد. این ابزار هر ۳۰ زمان اجرا را با خط‌کش یک فروشنده اندازه نمی‌گیرد. این موضوع اهمیت دارد: نوبتی از GPT-5 با ۳۰۰ هزار توکن اگر در برابر ۲۰۰ هزار توکن Anthropic سنجیده شود، «بیش از ۱۰۰٪، منفجرشده» نشان می‌دهد، در حالی که واقعاً فقط ۷۵٪ از ۴۰۰ هزار توکن GPT-5 است. همان خط‌کش یک نوبت واقعاً سرریزشدهٔ ۱۳۰ هزار توکنی DeepSeek را به‌صورت ۶۵٪ راحت پنهان می‌کند.

هر پنجره با منشأ خود عرضه می‌شود: `model_table`، `explicit_marker`، `observed_floor`، یا وقتی مدل را نمی‌شناسیم یک `default` صادقانه. گیج‌سنجی که بر پایهٔ حدس ساخته شده هرگز با همان اعتبار گیج‌سنجی که بر پایهٔ جست‌وجو ساخته شده رندر نمی‌شود.

ClawMetry تنها می‌تواند رویدادهای فشرده‌سازی را در برخی زمان‌های اجرا ببیند. بنابراین `GET /api/context-coverage` برای هر زمان اجرا گزارش می‌دهد که آیا **صفر به معنای «بدون مشکل اجرا شد» است یا «ما کور هستیم»**. صفری که واقعاً به معنای کوری است، این را بیان می‌کند. [جزئیات کامل](docs/CONTEXT_BLOWOUT.md)

**ابزارگذاری چه هزینه‌ای دارد؟**

| مسیر | افزوده‌شده به عامل شما | پیش‌فرض؟ |
|---|---|---|
| دنبال‌کردن فایل جلسه (هر ۳۰ زمان اجرا) | **۰**. فرآیندی جدا، بدون کد ClawMetry در عامل شما | روشن |
| رهگیر HTTP (`CLAWMETRY_INTERCEPT=1`) | **+۰٫۴۴ میلی‌ثانیه** به ازای هر فراخوانی LLM، یعنی ۰٫۰۰۹٪ از یک فراخوانی ۵ ثانیه‌ای | خاموش |
| دروازهٔ قلاب پیش‌ابزار (کش گرم) | **+۴۴ میلی‌ثانیه** به ازای هر فراخوانی ابزار دروازه‌بانی‌شده، فراتر از کف ۳۶ میلی‌ثانیه‌ای مفسر | خاموش |
| پروکسی اجرا (enforcement) | **+۹٫۷ میلی‌ثانیه** به ازای هر فراخوانی LLM | خاموش |

هزینهٔ میزبان دیمن: **۲٬۷۶۲ رویداد بر ثانیه** دریافت، **۷۱۰ بایت به ازای هر رویداد** روی دیسک (۶۷٫۷ مگابایت به ازای هر ۱۰۰ هزار رویداد)، و **حدود ۱۲٪ از یک هسته** به‌طور پیوسته روی یک نصب پرمشغله. آن عدد آخر از بودجهٔ اعلام‌شدهٔ خودمان یعنی ۵ تا ۱۰٪ بیشتر است، پس به‌عنوان یک باگ برای دنبال‌کردن منتشر شده، نه چیزی که از صفحه حذف شده باشد.

اندازه‌گیری‌شده روی یک Apple M2 Pro با `benchmarks/overhead.py`. این هارنس هر شرایط را در یک فرآیند جدا اجرا می‌کند، ترتیب آن‌ها را جابه‌جا می‌کند و **از چاپ عددی که دورها دربارهٔ علامتش اختلاف داشته باشند خودداری می‌کند**. آن را روی دستگاه خودتان در یک دقیقه اجرا کنید:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

هر مسیر اندازه‌گیری می‌شود، از جمله دروازه‌های قلاب و پروکسی اجرا، و هارنس روی Linux، macOS و Windows در CI اجرا می‌شود. دو نتیجه که ارزش دانستن دارند: پروکسی روی Windows حدود هفت برابر بیشتر از Linux هزینه دارد، و دیمن در حال حاضر حدود ۱۲٪ از یک هسته را به‌طور پیوسته مصرف می‌کند، فراتر از بودجهٔ ۵ تا ۱۰٪ خودمان. داده‌های خام JSON، روش کار، و آن‌چه هنوز اندازه‌گیری نشده در [docs/OVERHEAD.md](docs/OVERHEAD.md) آمده است.

## قیمت‌گذاری

| طرح | شامل چه چیزی می‌شود | قیمت |
|---|---|---|
| **رایگان** | OpenClaw + NVIDIA NemoClaw + Goose، داشبورد کامل، فقط محلی | ۰ دلار |
| **Starter** | هر زمان اجرای دیگر در بالا، نمای ناوگان، همگام‌سازی ابری | ۹ دلار به ازای هر گره در ماه |
| **Pro** | Starter + کنترل و ارزیابی: تأییدها، سیاست‌های ریسک ابزار، ارزیابی‌ها، تشخیص ناهنجاری، بهینه‌ساز هزینه، خروجی OTel، گزارش ممیزی ضدتغییر | ۱۹ دلار به ازای هر گره در ماه |

طرح‌های سالانه، Enterprise و اعداد فعلی در **[clawmetry.com/pricing](https://clawmetry.com/pricing)** موجود است. کلیدهای مجوز خودمیزبان بدون نیاز به ابر کار می‌کنند (`clawmetry license`). تقسیم دقیق رایگان/پولی در [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) آمده است.

## داده‌های شما روی دستگاه خودتان می‌ماند

ClawMetry فایل‌های جلسه و گزارش‌های محلی را می‌خواند. **هیچ داده‌ای از جلسات از دستگاه شما خارج نمی‌شود مگر این‌که `clawmetry connect` را اجرا کنید** — نه درخواست‌ها، نه پاسخ‌ها، نه آرگومان‌های ابزار، نه محتوای فایل‌ها و نه خطوط گزارش. وقتی متصل می‌شوید، عکس‌لحظه‌ای (snapshot) با رمزنگاری سرتاسر و کلیدی که هرگز از دستگاه شما خارج نمی‌شود رمزنگاری شده و در مرورگر شما رمزگشایی می‌شود. اگر گره‌ای کلید نداشته باشد، بارگذاری به‌جای ارسال به‌صورت رمزنگاری‌نشده، کلاً نادیده گرفته می‌شود، و هیچ پاسخ سروری نمی‌تواند این را خاموش کند.

دو چیز پیش از اتصال شما به‌طور پیش‌فرض اجرا می‌شوند، هر دو انصراف‌پذیر و هیچ‌کدام حامل داده‌های جلسه نیستند: یک پینگ نصب ناشناس و یک بررسی نسخه در برابر PyPI. یک نصب پیش‌فرض همچنین یک‌بار آدرس IP عمومی شما را برای یک خط بنر آغازین جست‌وجو می‌کند. هر مقصد، آن‌چه حمل می‌کند و چگونگی خاموش‌کردن آن در [docs/EGRESS.md](docs/EGRESS.md) فهرست شده است؛ نصب‌های خودمیزبان، تغییرمسیر‌داده‌شده و بدون‌اتصال به شبکه، هیچ فراخوانی خروجی اختیاری‌ای انجام نمی‌دهند.

رمزگشایی در مرورگر شما، در کدی که ما به شما ارائه می‌دهیم، انجام می‌شود. این پیش‌تر یک قول بود؛ اکنون چیزی است که می‌توانید بررسی کنید. هر خطی که به کلید شما دست می‌زند در یک فایل قابل‌خواندن، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)، قرار دارد که درون wheel ارسال می‌شود و عیناً ارائه می‌گردد، پین‌شده با یک هش Subresource Integrity. برای تأیید این‌که مرورگر همان چیزی را اجرا می‌کند که ما منتشر کرده‌ایم:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

آن‌چه این کار ثابت نمی‌کند: ما صفحه‌ای که این فایل را بارگذاری می‌کند نیز ارائه می‌دهیم، پس می‌توانیم صفحهٔ متفاوتی ارائه دهیم. هش‌های یکپارچگی شما را از یک CDN آسیب‌دیده محافظت می‌کنند، نه از خود فروشنده. آن‌چه به دست می‌آورید این است که هر جایگزینی باید عمدی، در سورس صفحه قابل‌مشاهده، و متفاوت از یک artifact روی PyPI باشد که هرکسی می‌تواند آن را دریافت کند. خودمیزبانی یا ماندن به‌صورت فقط‌محلی این وابستگی را کاملاً حذف می‌کند.

## نصب

```bash
pip install clawmetry     # سپس: clawmetry
```

یا خط فرمان یک‌خطی: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

به Python 3.8+ روی macOS، Linux یا Windows، و حداقل یک زمان اجرای عامل روی همان دستگاه نیاز دارد. دستورالعمل‌های Docker: [docs/DOCKER.md](docs/DOCKER.md).

یا بگذارید عامل آن را برای شما راه‌اندازی کند. مهارت [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md) به Claude Code، Codex، Cursor، Gemini CLI، Copilot یا OpenCode یاد می‌دهد که ClawMetry را نصب کند، گزارش دهد عامل‌های روی دستگاه چه می‌کنند و چه هزینه‌ای دارند، در صورت درخواست یک جلسه را متوقف کند، و فراخوانی‌های ابزار پرریسک را برای تأیید نگه دارد:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## مستندات

| | |
|---|---|
| [سازگاری زمان اجرا](docs/compatibility.md) | هر آداپتور چه چیزی می‌خواند، و چگونه یک زمان اجرا اضافه کنیم |
| [انفجار زمینه](docs/CONTEXT_BLOWOUT.md) | پنجره‌ها به تفکیک ارائه‌دهنده، فشرده‌سازی در برابر سرریز، پوشش به تفکیک زمان اجرا |
| [سربار (Overhead)](docs/OVERHEAD.md) | هزینهٔ ابزارگذاری، اندازه‌گیری‌شده، همراه با هارنس برای بازتولید آن |
| [حقوق (Entitlements)](docs/ENTITLEMENTS.md) | رایگان در برابر پولی، ماتریس رده، CLI مجوز |
| [تأییدها و سیاست‌ها](docs/APPROVALS.md) | دروازه‌بانی پیش از اجرا، امتیازدهی ریسک، تأیید از گوشی |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صادرات ردگیری‌ها به هرجا، دریافت OTLP از هرچیز |
| [عامل خودتان را بیاورید](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، Pydantic AI، LangChain سرتاسر، همراه با نمونه‌های قابل‌اجرا |
| [رهگیری SDK](docs/SDK_TRACKING.md) | تخصیص هزینه برای عامل‌هایی که خودتان ساخته‌اید |
| [کانال‌های چت](docs/CHANNELS.md) | آداپتورهای چت که در «جریان» نشان داده می‌شوند |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | راه‌اندازی‌های sandbox شدهٔ NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | تصویر، compose، اتصال‌های volume |
| [معماری](ARCHITECTURE.md) · [توسعه](docs/DEVELOPMENT.md) | چگونگی عملکرد داخلی؛ اجرا از سورس |
| [تله‌متری](docs/TELEMETRY.md) | پینگ‌های ناشناس نصب و بازکردن دسکتاپ، و چگونگی خاموش‌کردن آن‌ها |

## تصاویر صفحه

هر عددی که در زیر می‌بینید از یک دستگاه واقعی است، فقط برای خواندن، بدون هیچ داده‌ای که از پیش کاشته شده باشد.

**به شما می‌گوید چه زمانی چیزی اشتباه است، نه فقط چه اتفاقی افتاده.**
دو بنر ناهنجاری در بالا: هزینه‌ای که ۷ برابر میانگین روزانه در حال اجراست، و یک جهش هزینهٔ ۴٫۲ برابری. زیر آن‌ها، ۳۲۴ از ۶۶۷ جلسهٔ اخیر که سیگنال اتلاف دارند، به تفکیک علت.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**به شما نشان می‌دهد پول کجا رفته، در هر بازهٔ زمانی.**
۲۵۲٫۴۷ دلار امروز، ۵۱۳٫۱۵ دلار این هفته، ۱٬۳۱۲٫۹۲ دلار این ماه، هرکدام همراه با توکن‌های پشت آن‌ها و این‌که اشتراک شما هم‌اکنون چقدر از آن را پوشش می‌دهد. زیر آن، حدود ۱٬۱۲۸ دلار در ماه به‌صورت قابل‌بازیابی و ۱۷٬۲۵۶ دلار در ماه که از قبل با استفادهٔ مجدد از کش صرفه‌جویی شده، به تفکیک آمده است.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**نحوهٔ تبدیل یک پیام به پاسخ را ترسیم می‌کند.**
نمودار جریان زنده: شما، کانالی که پیام از آن رسیده، دروازه، مدلی که همین حالا پاسخ می‌دهد، و هر ابزاری که به آن دست زده است. با حرکت کار در طول آن‌ها، گره‌ها روشن می‌شوند.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**هر عامل روی دستگاه، در یک جدول.**
چه اجرا می‌کند، در ۲۴ ساعت گذشته و در طول عمرش چه هزینه‌ای دارد، آخرین‌بار کی دیده شده، مالک آن کیست، و آیا یک اشتراک هزینه را پوشش می‌دهد. اینجا ۱۴ عامل، ۳ جلسه در حال کار، ۱۳ ساکت.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**نشان می‌دهد زمان و پول یک نوبت، ابزار به ابزار، کجا رفته.**
یک نوبت از یک جلسهٔ واقعی: ۱۱ ابزار در ۱۱٫۲ دقیقه به قیمت ۱٫۱۶ دلار. هر فراخوانی Bash و فراخوانی مدل نوار زمانی خودش را روی جدول زمانی دارد، پس فرمانی که ۴٫۱ دقیقه اجرا شده و آن‌که ۲۲۶ میلی‌ثانیه اجرا شده در یک نگاه از هم متمایز می‌شوند.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**کار را نمره می‌دهد، نه فقط هزینه را.**
یک نمرهٔ A در این هفته: ۵۴ وظیفه تمیز برگشتند، ۲ مورد ناهموار ۴۸٫۵۷ دلار هزینه داشتند، و اجراهایی که فعالیت کافی برای قضاوت ندارند به‌جای شمرده‌شدن به‌عنوان برد، از نمره کنار گذاشته می‌شوند. هر اجرای ناهموار به ردگیری خودش پیوند دارد.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**نشان می‌دهد چرا پنجرهٔ زمینه پیوسته پر می‌شود.**
۷۱۵ هزار توکن از پنجرهٔ یک‌میلیون‌توکنی در آخرین نوبت، اوج ۸۳٫۳٪، ۴ فشرده‌سازی که همگی به‌صورت پیش‌دستانه فعال شدند نه در پی سرریز، به‌علاوهٔ میزان استفادهٔ هر نوبت پشت آن.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**تشخیص بدون هیچ پیکربندی از سوی شما کار می‌کند.**
تشخیص‌دهنده‌های داخلی از لحظهٔ نصب فعال هستند: ساکت‌شدن عامل، قطع‌شدن فید تله‌متری، جهش هزینه، انفجار توکن، افزایش خطاها، جهش خطا، آستانهٔ بودجه، تطبیق امضای تهدید، یافتهٔ ابزار امنیتی، تغییر وضعیت امنیتی. قوانین خودتان اختیاری و روی این‌ها افزوده می‌شوند.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**نگه‌داشتن یک فراخوانی پرریسک اختیاری است، و از پیش خاموش عرضه می‌شود.**
حذف‌های بازگشتی، push اجباری، sudo، اطلاعات محرمانه، نصب بسته‌ها و فراخوانی‌های خروجی، هرکدام قانونی دارند که می‌توانید روشن کنید. تا زمانی که این کار را نکنید، ClawMetry فقط تماشا می‌کند و هیچ تغییری نمی‌دهد. وقتی یکی را روشن کنید، فراخوانی‌های منطبق اینجا (یا روی گوشی شما) منتظر تأیید یا رد می‌مانند.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

بیشتر، به تفکیک زمان اجرا: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
