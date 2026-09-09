<!-- i18n-src:61beb8393e2f -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**یک ایجنت می‌تواند صدها فراخوانی ابزار انجام دهد بدون این‌که هیچ پیشرفتی حاصل شود.** ClawMetry
فایل‌های نشستی را که ایجنت‌های کدنویسی شما همین حالا می‌نویسند می‌خواند، و جدول زمانی،
فراخوانی‌های ابزار و هر داده‌ی توکن و هزینه‌ای را که ران‌تایم افشا می‌کند در یک
نما کنار هم می‌گذارد — تا بتوانید یک اجرای طولانی که در حال پیشرفت است را از اجرایی که گیر کرده تشخیص دهید.

با **۳۰ ران‌تایم ایجنت هوش مصنوعی** کار می‌کند — Claude Code، OpenAI Codex، Hermes، OpenClaw و ۲۶ مورد دیگر. یک داشبورد برای کل ناوگان ایجنت‌های شما. ([فهرست کامل](SUPPORTED_RUNTIMES.txt)، تولید شده از کاتالوگ.)

> 🌐 **این را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر →](docs/i18n/)

یک دستور. بدون پیکربندی. همه‌چیز به‌طور خودکار شناسایی می‌شود.

```bash
pip install clawmetry && clawmetry
```

در آدرس **http://localhost:8900** باز می‌شود. بدون پیکربندی: ران‌تایم‌های ایجنتی را که از قبل روی سیستم شما هستند پیدا می‌کند، آن‌ها را فقط به‌صورت خواندنی می‌خواند، و هیچ تغییری در نحوه‌ی اجرای آن‌ها ایجاد نمی‌کند.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## پیش از نصب

| | |
|---|---|
| **این ابزار چه‌کاری انجام می‌دهد** | فایل‌های نشست و لاگ‌هایی را می‌خواند که ایجنت‌های شما از قبل می‌نویسند. بدون SDK، بدون تغییر کد، بدون ابزارگذاری داخل اپلیکیشن شما. |
| **چه چیزی می‌بینید** | جدول زمانی نشست، بازپخش ابزار به ابزار، تفکیک توکن و هزینه، و سیگنال‌های مسیر حرکتی (حلقه‌زدن، شکست‌های تکراری) — به ازای هر ران‌تایم. |
| **چه چیزی رایگان است** | `pip install clawmetry` ران‌تایم‌های **OpenClaw، NVIDIA NemoClaw و Goose** را بدون نیاز به حساب کاربری، کلید یا هیچ تماس شبکه‌ای می‌خواند. ۲۷ مورد دیگر — Claude Code، Codex، Cursor و بقیه — توسط افزونه‌ی همراه بسته‌منبع `clawmetry-pro` خوانده می‌شوند، که همراه با آزمایش ۷ روزه یا یک طرح اشتراک در دسترس قرار می‌گیرد — برای تفکیک دقیق آن به [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) مراجعه کنید. |
| **نحوه‌ی شروع** | `pip install clawmetry && clawmetry`، سپس localhost:8900 را باز کنید. هنوز روی این سیستم ایجنتی ندارید؟ `clawmetry --sample` روی سه نشست مصنوعیِ برچسب‌گذاری‌شده باز می‌شود. |
| **چه چیزی از سیستم شما خارج می‌شود** | هیچ داده‌ی نشستی، مگر این‌که `clawmetry connect` را اجرا کنید. دو چیز به‌طور پیش‌فرض اجرا می‌شوند، هر دو قابل غیرفعال‌سازی و هیچ‌کدام حامل محتوای نشست نیستند: یک پینگ نصب ناشناس و یک بررسی نسخه از PyPI. هر مقصد در [docs/EGRESS.md](docs/EGRESS.md) فهرست شده، که از روی یک ضبط ترافیک شبکه بازسازی شده نه از روی خواندن کامنت‌ها. |

دو محدودیت که پیش از قضاوت درباره‌ی خروجی ارزش دانستن دارند: ران‌تایم‌ها داده‌های
بسیار متفاوتی را افشا می‌کنند (برخی اصلاً هزینه‌ای منتشر نمی‌کنند — [این جدول](docs/compatibility.md)
مشخص می‌کند کدام‌یک، به ازای هر ران‌تایم)، و مشاهده‌ی یک عمل با توانایی مسدود کردن آن یکسان نیست
([کدام کنترل‌ها واقعی‌اند، به ازای هر ران‌تایم](docs/APPROVALS.md)).


## با ۳۰ ران‌تایم ایجنت کار می‌کند

**رایگان در اپلیکیشن متن‌باز:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**در طرح اشتراک پولی:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

هر ران‌تایم همان داشبورد را دریافت می‌کند. چند مورد را همزمان اجرا کنید و
سوئیچ بالای صفحه دامنه‌ی هر تب را به یکی از آن‌ها محدود می‌کند.

ایجنت خودتان را روی یک SDK ساخته‌اید؟ اینترسپتور فراخوانی‌های LLM آن را هم ردیابی می‌کند.
به [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) مراجعه کنید.

## چه چیزی به‌دست می‌آورید

- **نشست‌ها و متن‌نوشته‌ها**: هر ایجنت چه کاری انجام داد، نوبت به نوبت، همراه با بازپخش
- **هزینه و توکن‌ها**: به ازای ران‌تایم، مدل، نشست و روز، همراه با پرچم‌های ناهنجاری
- **جریان**: نمودار زنده‌ی حرکت پیام‌ها میان کانال‌ها، مدل‌ها و ابزارها
- **مغز**: جریان رویدادهای استدلال و فراخوانی ابزار در همان لحظه‌ی وقوع
- **انفجار زمینه**: بهره‌وری پنجره، متناسب با هر ارائه‌دهنده، فشرده‌سازی در برابر سرریز اجباری، به‌همراه نقشه‌ای به ازای هر ران‌تایم از آنچه نمی‌توانیم ببینیم ([چگونه](docs/CONTEXT_BLOWOUT.md))
- **حافظه و مهارت‌ها**: فایل‌ها و مهارت‌هایی که هر ران‌تایم واقعاً بارگذاری کرده
- **سلامت و لاگ‌ها**: دیسک، حافظه، نرخ خطا، محدودیت‌های نرخ، جریان زنده‌ی لاگ
- **هشدارها**: سقف‌های بودجه، جهش خطا، آفلاین‌شدن ایجنت، مسیریابی‌شده به Slack، Discord، PagerDuty، Telegram، ایمیل
- **تأییدها**: توقف فراخوانی‌های ابزار پرریسک *پیش از* اجرا و تأیید از گوشی شما ([چگونه](docs/APPROVALS.md))

## انفجار زمینه، و هزینه‌ی نظارت

دو پرسش که پیش از اعتماد به هر ابزار مقایسه‌ی ایجنت ارزش پاسخ‌دادن دارند.

**چگونه با انفجار پنجره‌ی زمینه در میان ران‌تایم‌های مختلف برخورد می‌کند؟**

درصد بهره‌وری فقط به اندازه‌ی صداقتِ مخرجی که بر آن تقسیم می‌شود صادقانه است. ClawMetry
اندازه‌ی پنجره را به ازای هر ارائه‌دهنده از [جدولی که می‌توانید بخوانید و
درخواست تغییر بدهید](clawmetry/context_windows.py) تعیین می‌کند، که Anthropic، OpenAI، Google، xAI،
DeepSeek، Kimi، Qwen، Mistral، Llama و GLM را پوشش می‌دهد. هر ۳۰ ران‌تایم را با خط‌کش
یک فروشنده اندازه نمی‌گیرد. این مهم است: یک نوبت ۳۰۰ هزار توکنیِ GPT-5 وقتی در برابر
۲۰۰ هزار توکن Anthropic سنجیده شود «بیش از ۱۰۰٪، منفجرشده» خوانده می‌شود درحالی‌که واقعاً
۷۵٪ از ۴۰۰ هزار توکن GPT-5 است. همان خط‌کش یک نوبت DeepSeek واقعاً سرریزشده در ۱۳۰ هزار توکن را
به‌صورت یک ۶۵٪ راحت پنهان می‌کند.

هر پنجره با منشأ خود عرضه می‌شود: `model_table`، `explicit_marker`،
`observed_floor`، یا یک `default` صادقانه وقتی مدل را نمی‌شناسیم. یک گیج ساخته‌شده بر
اساس حدس هرگز با همان اعتبار یک گیج ساخته‌شده بر اساس جست‌وجوی جدول رندر نمی‌شود.

ClawMetry فقط در برخی ران‌تایم‌ها می‌تواند رویدادهای فشرده‌سازی را ببیند. بنابراین
`GET /api/context-coverage` به ازای هر ران‌تایم گزارش می‌دهد که آیا یک **صفر به معنای
«تمیز اجرا شد» است یا «ما کور هستیم»**. صفری که واقعاً به معنای کوری است همین را می‌گوید.
[جزئیات کامل](docs/CONTEXT_BLOWOUT.md)

**ابزارگذاری چه هزینه‌ای دارد؟**

| مسیر | افزوده‌شده به ایجنت شما | پیش‌فرض؟ |
|---|---|---|
| دنبال‌کردن فایل نشست (هر ۳۰ ران‌تایم) | **۰**. فرآیندی جداگانه، بدون کد ClawMetry داخل ایجنت شما | روشن |
| اینترسپتور HTTP (`CLAWMETRY_INTERCEPT=1`) | **۰٫۴۴ میلی‌ثانیه** به ازای هر فراخوانی LLM، یا ۰٫۰۰۹٪ از یک فراخوانی ۵ ثانیه‌ای | خاموش |
| دروازه‌ی هوک پیش از ابزار (کش گرم) | **۴۴+ میلی‌ثانیه** به ازای هر فراخوانی ابزارِ دروازه‌بانی‌شده، روی یک کف مفسر ۳۶ میلی‌ثانیه‌ای | خاموش |
| پروکسی اجرا | **۹٫۷+ میلی‌ثانیه** به ازای هر فراخوانی LLM | خاموش |

هزینه‌ی میزبانِ دیمن: **۲٬۷۶۲ رویداد/ثانیه** جذب، **۷۱۰ بایت/رویداد** روی دیسک
(۶۷٫۷ مگابایت به ازای هر ۱۰۰ هزار رویداد)، و **حدود ۱۲٪ از یک هسته** به‌صورت پایدار روی
یک نصب پرمشغله. این عدد آخر از بودجه‌ی ۵ تا ۱۰٪ خودمان بیشتر است، پس به‌عنوان یک باگ
که باید دنبال شود منتشر می‌شود نه این‌که از صفحه حذف شود.

اندازه‌گیری‌شده روی یک Apple M2 Pro با `benchmarks/overhead.py`. این ابزار هر حالت را در
یک فرآیند جداگانه اجرا می‌کند، ترتیب آن‌ها را جابه‌جا می‌کند، و **از چاپ عددی خودداری می‌کند
وقتی دورها در علامتِ آن توافق ندارند**. آن را در یک دقیقه روی سیستم خودتان اجرا کنید:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

هر مسیر اندازه‌گیری شده، از جمله دروازه‌های هوک و پروکسی اجرا، و این ابزار
روی Linux، macOS و Windows در CI اجرا می‌شود. دو نتیجه که ارزش دانستن دارند: پروکسی
روی Windows حدود هفت برابر بیشتر از Linux هزینه دارد، و دیمن هم‌اکنون به‌طور پایدار
حدود ۱۲٪ از یک هسته را مصرف می‌کند، که بیش از بودجه‌ی ۵ تا ۱۰٪ خودمان است. داده‌ی خام JSON، روش،
و آنچه هنوز اندازه‌گیری نشده در [docs/OVERHEAD.md](docs/OVERHEAD.md) آمده است.

## قیمت‌گذاری

| طرح | چه چیزی را پوشش می‌دهد | قیمت |
|---|---|---|
| **رایگان** | OpenClaw + NVIDIA NemoClaw + Goose، داشبورد کامل، فقط محلی | ۰ دلار |
| **Starter** | هر ران‌تایم دیگری در بالا، نمای ناوگان، همگام‌سازی ابری | ۹ دلار به ازای هر گره / ماه |
| **Pro** | Starter + کنترل و ارزیابی: تأییدها، سیاست‌های ریسک ابزار، ارزیابی‌ها، تشخیص ناهنجاری، بهینه‌ساز هزینه، خروجی OTel، لاگ ممیزی ضدتغییر | ۱۹ دلار به ازای هر گره / ماه |

طرح‌های سالانه، Enterprise و ارقام فعلی در
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** موجودند. کلیدهای لایسنس
میزبانی‌شده‌ی خودتان بدون ابر کار می‌کنند (`clawmetry license`). تفکیک دقیق رایگان/پولی
در [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) آمده است.

## داده‌های شما روی سیستم شما باقی می‌مانند

ClawMetry فایل‌های نشست و لاگ‌های محلی را می‌خواند. **هیچ داده‌ی نشستی از سیستم شما خارج نمی‌شود
مگر این‌که `clawmetry connect` را اجرا کنید** — نه پرامپت‌ها، نه پاسخ‌ها، نه آرگومان‌های ابزار، نه محتوای
فایل و نه خطوط لاگ. وقتی متصل می‌شوید، عکسِ لحظه‌ای با رمزنگاری سرتاسر و با کلیدی که هرگز از
سیستم شما خارج نمی‌شود رمزگذاری شده، و در مرورگر شما رمزگشایی می‌شود. اگر یک گره کلیدی نداشته باشد،
بارگذاری نادیده گرفته می‌شود به‌جای این‌که به‌صورت باز ارسال شود، و هیچ پاسخ سروری نمی‌تواند این را خاموش کند.

دو چیز به‌طور پیش‌فرض پیش از اتصال اجرا می‌شوند، هر دو قابل غیرفعال‌سازی و هیچ‌کدام حامل داده‌ی
نشستی نیستند: یک پینگ نصب ناشناس و یک بررسی نسخه در برابر PyPI. یک نصب پیش‌فرض همچنین یک‌بار
آدرس IP عمومی شما را برای خط بنر شروع جست‌وجو می‌کند. هر مقصد، چه چیزی حمل می‌کند و چگونه
خاموش می‌شود در [docs/EGRESS.md](docs/EGRESS.md) فهرست شده است؛ نصب‌های میزبانی‌شده‌ی خودتان،
هدایت‌شده‌ی مجدد و ایزوله از شبکه هیچ تماس خروجی اختیاری‌ای انجام نمی‌دهند.

رمزگشایی در مرورگر شما رخ می‌دهد، در کدی که به شما تحویل می‌دهیم. این قبلاً یک وعده بود؛
اکنون چیزی است که می‌توانید بررسی کنید. هر خطی که با کلید شما سروکار دارد در یک فایل قابل‌خواندن
زندگی می‌کند، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
که داخل wheel عرضه می‌شود و عیناً همان‌طور که هست ارائه می‌شود، با یک هش Subresource
Integrity پین شده. برای تأیید این‌که مرورگر همان چیزی را اجرا می‌کند که ما منتشر کرده‌ایم:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

چیزی که این ثابت نمی‌کند: ما همان صفحه‌ای را ارائه می‌دهیم که فایل را بارگذاری می‌کند، پس می‌توانیم
صفحه‌ی دیگری ارائه دهیم. هش‌های Integrity شما را از یک CDN دستکاری‌شده محافظت می‌کنند،
نه از خود فروشنده. آنچه به‌دست می‌آورید این است که هر جایگزینی باید عمدی، در سورس صفحه
قابل‌مشاهده، و متفاوت از یک artifact روی PyPI باشد که هرکسی می‌تواند آن را دریافت کند. میزبانی خودتان
یا ماندن به‌صورت فقط‌محلی این وابستگی را کاملاً از بین می‌برد.

## نصب

```bash
pip install clawmetry     # سپس: clawmetry
```

یا دستور تک‌خطی: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

به Python 3.8+ روی macOS، Linux یا Windows نیاز دارد، و حداقل یک ران‌تایم ایجنت روی
همان سیستم. دستورالعمل‌های Docker: [docs/DOCKER.md](docs/DOCKER.md).

یا بگذارید ایجنت آن را برای شما راه‌اندازی کند. مهارت [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
به Claude Code، Codex، Cursor، Gemini CLI، Copilot یا OpenCode یاد می‌دهد که
ClawMetry را نصب کند، گزارش دهد ایجنت‌های روی سیستم چه‌کار می‌کنند و چقدر خرج می‌کنند،
یک نشست را با درخواست متوقف کند، و فراخوانی‌های ابزار پرریسک را برای تأیید نگه دارد:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## مستندات

| | |
|---|---|
| [سازگاری ران‌تایم](docs/compatibility.md) | هر آداپتور چه چیزی را می‌خواند، و چگونه یک ران‌تایم اضافه کنیم |
| [انفجار زمینه](docs/CONTEXT_BLOWOUT.md) | پنجره‌ها به ازای هر ارائه‌دهنده، فشرده‌سازی در برابر سرریز، پوشش به ازای هر ران‌تایم |
| [سربار](docs/OVERHEAD.md) | ابزارگذاری چه هزینه‌ای دارد، اندازه‌گیری‌شده، همراه با ابزار برای بازتولید آن |
| [استحقاق‌ها](docs/ENTITLEMENTS.md) | رایگان در برابر پولی، جدول ردیف‌ها، CLI لایسنس |
| [تأییدها و سیاست‌ها](docs/APPROVALS.md) | دروازه‌بانی پیش از اجرا، امتیازدهی ریسک، تأییدهای گوشی |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صادرات ردها به هر جا، جذب OTLP از هر چیزی |
| [ایجنت خودتان را بیاورید](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، Pydantic AI، LangChain سرتاسر، همراه با مثال‌های قابل‌اجرا |
| [ردیابی SDK](docs/SDK_TRACKING.md) | انتساب هزینه برای ایجنت‌هایی که خودتان ساخته‌اید |
| [کانال‌های چت](docs/CHANNELS.md) | آداپتورهای چتی که در Flow نشان داده می‌شوند |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | راه‌اندازی‌های سندباکس‌شده‌ی NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | ایمیج، compose، mount حجم‌ها |
| [معماری](ARCHITECTURE.md) · [توسعه](docs/DEVELOPMENT.md) | چگونگی کارکرد درونی؛ اجرا از سورس |
| [تله‌متری](docs/TELEMETRY.md) | پینگ‌های ناشناس نصب و بازکردن دسکتاپ، و چگونگی خاموش‌کردن آن‌ها |

## اسکرین‌شات‌ها

هر عدد در زیر از یک سیستم واقعی است، فقط‌خواندنی، بدون هیچ داده‌ی دستکاری‌شده‌ای.

**به شما می‌گوید چه زمانی چیزی اشتباه است، نه فقط چه اتفاقی افتاده.**
دو بنر ناهنجاری در بالا: هزینه‌ای که ۷ برابر میانگین روزانه در حال اجراست، و یک
جهش هزینه‌ی ۴٫۲ برابری. زیر آن‌ها، ۳۲۴ از ۶۶۷ نشست اخیر حامل یک سیگنال هدررفت،
تفکیک‌شده بر اساس علت.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**به شما نشان می‌دهد پول کجا رفته، در هر بازه‌ی زمانی.**
۲۵۲٫۴۷ دلار امروز، ۵۱۳٫۱۵ دلار این هفته، ۱٬۳۱۲٫۹۲ دلار این ماه، هرکدام همراه با
توکن‌های پشت آن و این‌که چقدر از آن را اشتراک شما پیش‌تر پوشش می‌دهد. زیر آن، حدود
۱٬۱۲۸ دلار در ماه به‌عنوان قابل‌بازیابی تفکیک‌شده و ۱۷٬۲۵۶ دلار در ماه که پیش‌تر با استفاده‌ی
مجدد از کش صرفه‌جویی شده.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**نشان می‌دهد یک پیام چگونه به یک پاسخ تبدیل می‌شود.**
نمودار جریان زنده: شما، کانالی که پیام از آن رسیده، گیت‌وی، مدلی که هم‌اکنون
پاسخ می‌دهد، و هر ابزاری که به سراغش رفته. گره‌ها هنگام عبور کار از میان آن‌ها روشن می‌شوند.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**هر ایجنت روی سیستم، در یک جدول.**
چه چیزی اجرا می‌کند، در ۲۴ ساعت گذشته و در طول عمرش چه هزینه‌ای دارد، آخرین بار
چه زمانی دیده شده، مالک آن کیست، و آیا یک اشتراک هزینه‌اش را پوشش می‌دهد. اینجا ۱۴ ایجنت،
۳ نشست در حال کار، ۱۳ مورد بی‌کار.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**نشان می‌دهد زمان و پول یک نوبت کجا صرف شده، ابزار به ابزار.**
یک نوبت از یک نشست واقعی: ۱۱ ابزار در ۱۱٫۲ دقیقه برای ۱٫۱۶ دلار. هر فراخوانی Bash
و هر فراخوانی مدل نوار زمانی مخصوص خودش را دارد، پس دستوری که ۴٫۱ دقیقه طول کشیده
و آن‌که ۲۲۶ میلی‌ثانیه طول کشیده در یک نگاه از هم متمایز می‌شوند.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**کار را نمره می‌دهد، نه فقط هزینه را.**
یک A در این هفته: ۵۴ وظیفه تمیز برگشتند، ۲ مورد ناهموار ۴۸٫۵۷ دلار هزینه داشتند،
و اجراهایی که فعالیت خیلی کمی برای قضاوت دارند به‌جای این‌که به‌عنوان برد شمرده شوند
از نمره کنار گذاشته می‌شوند. هر اجرای ناهموار به رد خودش لینک می‌شود.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**نشان می‌دهد چرا پنجره‌ی زمینه دائماً پر می‌شود.**
۷۱۵ هزار از یک پنجره‌ی ۱ میلیون توکنی در آخرین نوبت، اوج ۸۳٫۳٪، ۴ فشرده‌سازی
که همگی به‌صورت پیشگیرانه فعال شدند نه در پی سرریز، به‌همراه بهره‌وری هر نوبت پشت آن.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**تشخیص بدون نیاز به پیکربندی توسط شما اجرا می‌شود.**
تشخیص‌گرهای داخلی از لحظه‌ی نصب فعال‌اند: ایجنت ساکت شد، جریان تله‌متری متوقف
شد، جهش هزینه، انفجار توکن، افزایش خطاها، جهش خطا، آستانه‌ی بودجه، تطبیق امضای تهدید،
یافته‌ی ابزار امنیتی، تغییر وضعیت امنیتی. قوانین خودتان نیز به‌صورت اختیاری روی آن‌ها اضافه می‌شوند.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**نگه‌داشتن یک فراخوانی پرریسک اختیاری است، و به‌صورت خاموش عرضه می‌شود.**
حذف‌های بازگشتی، force pushها، sudo، اطلاعات محرمانه، نصب بسته‌ها و فراخوانی‌های
خروجی هرکدام قانونی دارند که می‌توانید فعال کنید. تا وقتی این کار را نکنید، ClawMetry
تماشا می‌کند و هیچ چیزی را تغییر نمی‌دهد. وقتی یکی فعال شود، فراخوانی‌های منطبق اینجا
(یا روی گوشی شما) منتظر تأیید یا رد می‌مانند.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

بیشتر، به ازای هر ران‌تایم: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## قدردانی

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## تاریخچه‌ی ستاره‌ها

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
