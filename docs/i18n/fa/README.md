<!-- i18n-src:a855a14295b0 -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**یک ایجنت می‌تواند صدها فراخوانی ابزار انجام دهد بدون آن‌که پیشرفتی حاصل شود.** ClawMetry
فایل‌های نشستی را که ایجنت‌های کدنویسی شما همین حالا می‌نویسند می‌خوانَد، و خط زمانی،
فراخوانی‌های ابزار و هر داده‌ای از توکن و هزینه که آن ران‌تایم آشکار می‌کند را در یک
نمای واحد قرار می‌دهد — تا بتوانید یک اجرای طولانی که در حال پیشرفت است را از اجرایی که گیر کرده تشخیص دهید.

با **۳۲ ران‌تایم ایجنت هوش مصنوعی** کار می‌کند — Claude Code، OpenAI Codex، Hermes، OpenClaw و ۲۸ مورد دیگر. یک داشبورد برای کل ناوگان ایجنت‌های شما. ([فهرست کامل](SUPPORTED_RUNTIMES.txt)، که از کاتالوگ تولید شده است.)

> 🌐 **این را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر →](docs/i18n/)

یک دستور. بدون پیکربندی. تشخیص خودکار همه چیز.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود. بدون پیکربندی: ران‌تایم‌های ایجنتی را که از قبل دارید پیدا می‌کند، آن‌ها را فقط-خوانده می‌خواند، و هیچ چیزی درباره‌ی نحوه‌ی اجرای آن‌ها را تغییر نمی‌دهد.

![داشبورد ClawMetry: هر ران‌تایم ایجنت هوش مصنوعی روی یک دستگاه با هزینه‌ی ۲۴ ساعته و مادام‌العمر برای هر ایجنت](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## پیش از نصب

| | |
|---|---|
| **چه کاری انجام می‌دهد** | فایل‌های نشست و لاگ‌هایی را که ایجنت‌های شما از قبل می‌نویسند می‌خوانَد. بدون SDK، بدون تغییر کد، بدون ابزارگذاری در اپلیکیشن شما. |
| **چه چیزی می‌بینید** | خط زمانی نشست، بازپخش ابزار به ابزار، تفکیک توکن و هزینه، و سیگنال‌های مسیر حرکت (حلقه زدن، شکست‌های تکراری) — به تفکیک هر ران‌تایم. |
| **چه چیزی رایگان است** | `pip install clawmetry`، **OpenClaw، NVIDIA NemoClaw و Goose** را بدون حساب کاربری، بدون کلید و بدون هیچ تماس شبکه‌ای می‌خواند. ۲۷ مورد دیگر — Claude Code، Codex، Cursor و باقی — توسط افزونه‌ی بسته‌منبع همراه `clawmetry-pro` خوانده می‌شوند، که همراه با دوره‌ی آزمایشی ۷ روزه یا یک پلن ارائه می‌شود — برای تفکیک دقیق آن به [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) مراجعه کنید. |
| **چگونه شروع کنیم** | `pip install clawmetry && clawmetry`، سپس localhost:8900 را باز کنید. هنوز هیچ ایجنتی روی این دستگاه ندارید؟ `clawmetry --sample` با سه نشست ساختگی برچسب‌گذاری‌شده باز می‌شود. |
| **چه چیزی از دستگاه شما خارج می‌شود** | هیچ داده‌ی نشستی، مگر آن‌که `clawmetry connect` را اجرا کنید. دو چیز به‌طور پیش‌فرض اجرا می‌شوند، هر دو قابل غیرفعال‌سازی و هیچ‌کدام حامل محتوای نشست: یک پینگ ناشناس نصب و یک بررسی نسخه‌ی PyPI. هر مقصد در [docs/EGRESS.md](docs/EGRESS.md) فهرست شده است، که از یک ضبط ترافیک شبکه بازسازی شده تا از خواندن کامنت‌ها. |

دو محدودیت که پیش از قضاوت درباره‌ی خروجی خوب است بدانید: ران‌تایم‌ها داده‌های بسیار
متفاوتی آشکار می‌کنند (برخی هیچ هزینه‌ای منتشر نمی‌کنند — [این جدول](docs/compatibility.md)
می‌گوید کدام‌ها، به تفکیک هر ران‌تایم)، و مشاهده‌ی یک عمل با توانایی مسدود کردن آن یکسان نیست
([کدام کنترل‌ها واقعی‌اند، به تفکیک هر ران‌تایم](docs/APPROVALS.md)).


## با ۳۲ ران‌تایم ایجنت کار می‌کند

**رایگان در اپلیکیشن متن‌باز:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**در یک پلن پرداختی:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

هر ران‌تایم همان داشبورد را دریافت می‌کند. چند مورد را همزمان اجرا کنید و
سوئیچر بالای صفحه دامنه‌ی هر تب را به یکی از آن‌ها محدود می‌کند.

ایجنت خودتان را روی یک SDK ساخته‌اید به‌جای این‌ها؟ رهگیر (interceptor) فراخوانی‌های LLM آن را هم ردیابی می‌کند.
به [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) مراجعه کنید.

## چه چیزی به دست می‌آورید

- **نشست‌ها و رونوشت‌ها**: هر ایجنت چه کاری انجام داد، نوبت به نوبت، با قابلیت بازپخش
- **هزینه و توکن**: به تفکیک ران‌تایم، مدل، نشست و روز، همراه با پرچم‌های ناهنجاری
- **جریان (Flow)**: نمودار زنده‌ی حرکت پیام‌ها میان کانال‌ها، مدل‌ها و ابزارها
- **مغز (Brain)**: جریان رویدادهای استدلال و فراخوانی ابزار همان‌طور که اتفاق می‌افتد
- **انفجار زمینه (Context blowout)**: میزان استفاده از پنجره‌ی زمینه متناسب با هر ارائه‌دهنده، فشرده‌سازی در برابر سرریز اجباری، به‌همراه نگاشتی به تفکیک هر ران‌تایم از آنچه *نمی‌توانیم* ببینیم ([چگونه](docs/CONTEXT_BLOWOUT.md))
- **حافظه و مهارت‌ها**: فایل‌ها و مهارت‌هایی که هر ران‌تایم واقعاً بارگذاری کرده است
- **سلامت و لاگ‌ها**: دیسک، حافظه، نرخ خطا، محدودیت‌های نرخ، جریان زنده‌ی لاگ
- **هشدارها**: سقف‌های بودجه، افزایش ناگهانی خطا، آفلاین شدن ایجنت، مسیریابی شده به Slack، Discord، PagerDuty، Telegram، ایمیل
- **تأییدیه‌ها (Approvals)**: توقف فراخوانی‌های ابزار پرخطر *پیش از* اجرای آن‌ها و تأیید از گوشی شما ([چگونه](docs/APPROVALS.md))

## انفجار زمینه، و هزینه‌ی رصد کردن آن

دو پرسش که ارزش پاسخ دادن دارند پیش از آن‌که به هر ابزار مقایسه‌ی ایجنت‌ها اعتماد کنید.

**چگونه انفجار پنجره‌ی زمینه را در میان ران‌تایم‌های مختلف مدیریت می‌کند؟**

درصد استفاده تنها به‌اندازه‌ی صداقت مخرجی که بر آن تقسیم می‌شود صادقانه است. ClawMetry
اندازه‌ی پنجره را به تفکیک هر ارائه‌دهنده از [جدولی که می‌توانید بخوانید و برایش PR ارسال
کنید](clawmetry/context_windows.py) تعیین می‌کند، که Anthropic، OpenAI، Google، xAI،
DeepSeek، Kimi، Qwen، Mistral، Llama و GLM را پوشش می‌دهد. تمام ۳۲ ران‌تایم را با خط‌کش
یک فروشنده نمی‌سنجد. این اهمیت دارد: یک نوبت ۳۰۰ هزار توکنی GPT-5 که در برابر ۲۰۰ هزار
توکنی Anthropic سنجیده شود ">100%, blown" نمایش می‌دهد در حالی که واقعاً در ۷۵٪ از ۴۰۰
هزار توکنی GPT-5 قرار دارد. همان خط‌کش یک نوبت ۱۳۰ هزار توکنی DeepSeek را که واقعاً
سرریز شده است به‌صورت ۶۵٪ راحت پنهان می‌کند.

هر پنجره با منشأ خودش ارسال می‌شود: `model_table`، `explicit_marker`،
`observed_floor`، یا یک `default` صادقانه وقتی مدل را نمی‌شناسیم. یک نمایشگر عددی
که بر اساس یک تخمین ساخته شده است هرگز با همان اعتبار یکی که بر اساس یک جست‌وجوی واقعی
ساخته شده رندر نمی‌شود.

ClawMetry فقط روی برخی ران‌تایم‌ها می‌تواند رویدادهای فشرده‌سازی را ببیند. به همین دلیل
`GET /api/context-coverage` به تفکیک هر ران‌تایم گزارش می‌دهد که آیا یک **صفر به معنای
«بدون مشکل اجرا شد» است یا «ما نابینا هستیم»**. صفری که واقعاً به معنای نابینایی است
این را می‌گوید. [جزئیات کامل](docs/CONTEXT_BLOWOUT.md)

**ابزارگذاری چه هزینه‌ای دارد؟**

| مسیر | افزوده‌شده به ایجنت شما | پیش‌فرض؟ |
|---|---|---|
| دنبال‌کردن فایل نشست (هر ۳۲ ران‌تایم) | **۰**. فرآیندی جدا، بدون کد ClawMetry در ایجنت شما | فعال |
| رهگیر HTTP (`CLAWMETRY_INTERCEPT=1`) | **+۰.۴۴ میلی‌ثانیه** برای هر فراخوانی LLM، یا ۰.۰۰۹٪ از یک فراخوانی ۵ ثانیه‌ای | غیرفعال |
| دروازه‌ی هوک پیش از ابزار (کش گرم) | **+۴۴ میلی‌ثانیه** برای هر فراخوانی ابزار دروازه‌شده، بر روی یک کف تفسیرگر ۳۶ میلی‌ثانیه‌ای | غیرفعال |
| پروکسی اجرایی (enforcement proxy) | **+۹.۷ میلی‌ثانیه** برای هر فراخوانی LLM | غیرفعال |

هزینه‌ی میزبان دیمن: **۲,۷۶۲ رویداد بر ثانیه** دریافت، **۷۱۰ بایت به‌ازای هر رویداد**
روی دیسک (۶۷.۷ مگابایت به‌ازای هر ۱۰۰ هزار رویداد)، و **حدود ۱۲٪ از یک هسته** به‌طور
پیوسته روی یک نصب پرمشغله. آن عدد آخر بیش از بودجه‌ی اعلام‌شده‌ی خود ما یعنی ۵ تا ۱۰٪ است،
پس به‌عنوان یک باگ برای دنبال کردن منتشر می‌شود، نه چیزی که از صفحه حذف شده باشد.

اندازه‌گیری‌شده روی یک Apple M2 Pro با `benchmarks/overhead.py`. این هارنس هر شرایط را در
یک فرآیند جدا اجرا می‌کند، ترتیب آن‌ها را عوض می‌کند، و **از چاپ یک عدد وقتی که دورها در
علامتِ آن اختلاف داشته باشند خودداری می‌کند**. آن را روی دستگاه خودتان در یک دقیقه اجرا کنید:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

هر مسیر اندازه‌گیری می‌شود، از جمله دروازه‌های هوک و پروکسی اجرایی،
و هارنس روی Linux، macOS و Windows در CI اجرا می‌شود. دو نتیجه که ارزش دانستن دارند: پروکسی
روی Windows حدود هفت برابر بیشتر از Linux هزینه دارد، و دیمن در حال حاضر حدود ۱۲٪ از
یک هسته را به‌طور پیوسته مصرف می‌کند، بیش از بودجه‌ی ۵ تا ۱۰٪ خودمان. JSON خام، روش کار،
و آنچه هنوز اندازه‌گیری نشده در [docs/OVERHEAD.md](docs/OVERHEAD.md) آمده است.

## قیمت‌گذاری

| پلن | چه چیزی را پوشش می‌دهد | قیمت |
|---|---|---|
| **رایگان** | OpenClaw + NVIDIA NemoClaw + Goose، داشبورد کامل، فقط محلی | $0 |
| **Starter** | هر ران‌تایم دیگر در بالا، نمای ناوگان، همگام‌سازی ابری | ۹ دلار به‌ازای هر نود / ماه |
| **Pro** | Starter به‌همراه کنترل و ارزیابی: تأییدیه‌ها، سیاست‌های ریسک ابزار، ارزیابی‌ها، تشخیص ناهنجاری، بهینه‌ساز هزینه، خروجی OTel، لاگ حسابرسی ضدتغییر | ۱۹ دلار به‌ازای هر نود / ماه |

پلن‌های سالانه، Enterprise و اعداد فعلی در
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** قرار دارند. کلیدهای مجوز
خودمیزبان بدون ابر کار می‌کنند (`clawmetry license`). تفکیک دقیق رایگان/پرداختی در
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) آمده است.

## داده‌های شما روی دستگاه شما می‌مانند

ClawMetry فایل‌های نشست و لاگ‌های محلی را می‌خواند. **هیچ داده‌ی نشستی از دستگاه شما خارج
نمی‌شود مگر آن‌که `clawmetry connect` را اجرا کنید** — نه پرامپت‌ها، پاسخ‌ها، آرگومان‌های
ابزار، محتوای فایل یا خطوط لاگ. وقتی متصل می‌شوید، تصویر لحظه‌ای (snapshot) با رمزگذاری
سرتاسری و کلیدی که هرگز از دستگاه شما خارج نمی‌شود رمزگذاری می‌شود، و در مرورگر شما رمزگشایی
می‌شود. اگر یک نود کلیدی نداشته باشد، بارگذاری نادیده گرفته می‌شود به‌جای ارسال به‌صورت رمزگشوده،
و هیچ پاسخ سرور نمی‌تواند این را خاموش کند.

دو چیز به‌طور پیش‌فرض پیش از اتصال اجرا می‌شوند، هر دو قابل غیرفعال‌سازی و هیچ‌کدام حامل
داده‌ی نشستی: یک پینگ ناشناس نصب و یک بررسی نسخه در برابر PyPI. یک نصب پیش‌فرض همچنین IP
عمومی شما را یک بار برای خط بنر آغازین جست‌وجو می‌کند. هر مقصد، محتوای آن و نحوه‌ی خاموش
کردنش در [docs/EGRESS.md](docs/EGRESS.md) فهرست شده است؛ نصب‌های خودمیزبان، بازتغییرمسیر‌شده
و ایزوله (air-gapped) هیچ فراخوانی اختیاری به بیرون انجام نمی‌دهند.

رمزگشایی در مرورگر شما، در کدی که ما به شما ارائه می‌دهیم، اتفاق می‌افتد. این قبلاً یک
وعده بود؛ حالا چیزی است که می‌توانید بررسی کنید. هر خطی که به کلید شما دست می‌زند در یک فایل
قابل‌خوانش قرار دارد، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
که در داخل wheel ارسال می‌شود و عیناً سرو می‌شود، با یک هش Subresource Integrity پین شده.
برای تأیید این‌که مرورگر همان چیزی را اجرا می‌کند که ما منتشر کرده‌ایم:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

چیزی که این ثابت نمی‌کند: ما صفحه‌ای که آن فایل را بارگذاری می‌کند را سرو می‌کنیم، پس
می‌توانستیم صفحه‌ی دیگری سرو کنیم. هش‌های Integrity شما را از یک CDN مختل‌شده محافظت می‌کنند،
نه از فروشنده. چیزی که به دست می‌آورید این است که هر جایگزینی باید عمدی، در سورس صفحه
قابل‌مشاهده، و متفاوت از یک artifact روی PyPI باشد که هرکسی می‌تواند آن را دریافت کند.
خودمیزبانی یا ماندن فقط-محلی این وابستگی را کاملاً حذف می‌کند.

## نصب

```bash
pip install clawmetry     # سپس: clawmetry
```

یا دستور یک‌خطی: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

به Python نسخه‌ی ۳.۸ به بالا روی macOS، Linux یا Windows، و حداقل یک ران‌تایم ایجنت روی
همان دستگاه نیاز دارد. دستورالعمل‌های Docker: [docs/DOCKER.md](docs/DOCKER.md).

یا اجازه دهید ایجنت آن را برای شما راه‌اندازی کند. مهارت [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
به Claude Code، Codex، Cursor، Gemini CLI، Copilot یا OpenCode می‌آموزد که
ClawMetry را نصب کنند، گزارش دهند ایجنت‌های روی دستگاه چه کاری انجام می‌دهند و چه هزینه‌ای
دارند، یک نشست را به درخواست متوقف کنند، و فراخوانی‌های ابزار پرخطر را برای تأیید نگه دارند:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## مستندات

| | |
|---|---|
| [سازگاری ران‌تایم](docs/compatibility.md) | چه چیزی هر آداپتور می‌خواند، و چگونه یک ران‌تایم اضافه کنیم |
| [انفجار زمینه](docs/CONTEXT_BLOWOUT.md) | پنجره‌ها به تفکیک هر ارائه‌دهنده، فشرده‌سازی در برابر سرریز، پوشش به تفکیک هر ران‌تایم |
| [سربار (Overhead)](docs/OVERHEAD.md) | ابزارگذاری چه هزینه‌ای دارد، اندازه‌گیری‌شده، همراه با هارنس برای بازتولید آن |
| [استحقاق‌ها (Entitlements)](docs/ENTITLEMENTS.md) | رایگان در برابر پرداختی، جدول ردیف‌بندی، CLI مجوز |
| [تأییدیه‌ها و سیاست‌ها](docs/APPROVALS.md) | دروازه‌گذاری پیش از اجرا، امتیازدهی ریسک، تأییدیه‌های تلفن |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صادرات ردگیری‌ها به هر جا، دریافت OTLP از هر چیز |
| [ایجنت خودتان را بیاورید](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، Pydantic AI، LangChain به‌طور کامل، با مثال‌های اجراپذیر |
| [ردگیری SDK](docs/SDK_TRACKING.md) | نسبت‌دهی هزینه برای ایجنت‌هایی که خودتان ساخته‌اید |
| [کانال‌های چت](docs/CHANNELS.md) | آداپتورهای چتی که در Flow نشان داده می‌شوند |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | راه‌اندازی‌های ایزوله‌شده‌ی NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | ایمیج، compose، اتصال volume |
| [معماری](ARCHITECTURE.md) · [توسعه](docs/DEVELOPMENT.md) | چگونگی کار درونی آن؛ اجرا از سورس |
| [تله‌متری](docs/TELEMETRY.md) | پینگ‌های ناشناس نصب و باز شدن دسکتاپ، و چگونگی خاموش کردن آن‌ها |

## اسکرین‌شات‌ها

هر عدد در زیر از یک دستگاه واقعی است، فقط-خوانده، بدون هیچ داده‌ی ساخته‌شده.

**به شما می‌گوید چه زمانی چیزی اشتباه است، نه فقط چه اتفاقی افتاده.**
دو بنر ناهنجاری در بالا: هزینه‌ای که ۷ برابر میانگین روزانه در جریان است، و یک افزایش
ناگهانی هزینه‌ی ۴.۲ برابری. زیر آن‌ها، ۳۲۴ از ۶۶۷ نشست اخیر که سیگنال هدررفت دارند،
به تفکیک علت فهرست شده‌اند.

![نمای کلی: بنرهای ناهنجاری هزینه و افزایش ناگهانی هزینه بر روی کار زنده‌ی ایجنت](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**به شما نشان می‌دهد پول کجا رفت، در هر بازه‌ی زمانی.**
۲۵۲.۴۷ دلار امروز، ۵۱۳.۱۵ دلار این هفته، ۱٬۳۱۲.۹۲ دلار این ماه، هر یک با توکن‌های
پشتش و مقدار پوشش‌داده‌شده توسط اشتراک شما. زیر آن، حدود ۱٬۱۲۸ دلار در ماه به‌عنوان قابل‌بازیافت
فهرست شده و ۱۷٬۲۵۶ دلار در ماه که هم‌اکنون با استفاده مجدد از کش صرفه‌جویی شده است.

![هزینه: امروز، این هفته و این ماه، همراه با یک رتبه‌ی کارایی و ایده‌های صرفه‌جویی فهرست‌شده](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**نشان می‌دهد چگونه یک پیام به پاسخ تبدیل می‌شود.**
نمودار جریان زنده: شما، کانالی که پیام از آن رسیده، gateway، مدلی که همین حالا پاسخ می‌دهد،
و هر ابزاری که سراغش رفته. گره‌ها با حرکت کار از میان آن‌ها روشن می‌شوند.

![جریان: نمودار زنده از شما از میان gateway به مدل و ابزارهای آن](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**هر ایجنت روی دستگاه، در یک جدول واحد.**
چه چیزی اجرا می‌کند، در ۲۴ ساعت گذشته و در طول عمرش چه هزینه‌ای دارد، آخرین بار چه زمانی
دیده شده، مالک آن کیست، و آیا یک اشتراک صورتحساب را می‌پوشاند. ۱۴ ایجنت در اینجا، ۳ نشست
در حال کار، ۱۳ آرام.

![ایجنت‌ها: هر ران‌تایم روی دستگاه با هزینه، مالک، آخرین بازدید و کار جاری](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**نشان می‌دهد زمان و پول یک نوبت کجا صرف شده، ابزار به ابزار.**
یک نوبت از یک نشست واقعی: ۱۱ ابزار در ۱۱.۲ دقیقه به قیمت ۱.۱۶ دلار. هر فراخوانی Bash
و فراخوانی مدل نوار زمانی خودش را در خط زمانی دارد، پس فرمانی که ۴.۱ دقیقه اجرا شده و آنی
که ۲۲۶ میلی‌ثانیه اجرا شده در یک نگاه از هم متمایز می‌شوند.

![نشست‌ها: یک نوبت ایجنت روی خط زمانی، هر فراخوانی ابزار با مدت زمان خودش و هزینه‌ی نوبت](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**کار را نمره‌دهی می‌کند، نه فقط هزینه را.**
یک A این هفته: ۵۴ وظیفه تمیز بازگشتند، ۲ مورد ناهموار ۴۸.۵۷ دلار هزینه داشتند، و اجراهایی
که فعالیت کافی برای قضاوت ندارند به‌جای شمرده‌شدن به‌عنوان برد، از نمره‌گذاری حذف می‌شوند.
هر اجرای ناهموار به ردگیری خودش لینک می‌شود.

![کیفیت: کارنامه‌ی این هفته با اجراهای ناهموار و هزینه‌ی آن‌ها](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**نشان می‌دهد چرا پنجره‌ی زمینه پیوسته پر می‌شود.**
۷۱۵ هزار توکن از یک پنجره‌ی یک میلیون توکنی در آخرین نوبت، یک اوج ۸۳.۳٪، ۴ فشرده‌سازی
که همگی به‌صورت پیش‌کنشانه به‌جای سرریز فعال شدند، و میزان استفاده‌ی هر نوبت پیش از آن.

![استفاده‌ی زمینه: میزان استفاده از پنجره به‌ازای هر نوبت، رویدادهای فشرده‌سازی و توکن‌های بازپس‌گرفته‌شده](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**تشخیص بدون هیچ پیکربندی از سمت شما اجرا می‌شود.**
تشخیص‌گرهای درونی از لحظه‌ی نصب فعال‌اند: ایجنت ساکت شد، خوراک تله‌متری متوقف شد،
افزایش ناگهانی هزینه، انفجار توکن، افزایش خطاها، افزایش ناگهانی خطا، آستانه‌ی بودجه،
تطبیق امضای تهدید، یافته‌ی ابزار امنیتی، تغییر وضعیت امنیتی. قواعد خودتان اختیاری و
افزوده بر این‌ها هستند.

![هشدارها: تشخیص‌گرهای درونی به‌همراه قواعد اختیاری سفارشی](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**نگه داشتن یک فراخوانی پرخطر اختیاری است، و غیرفعال ارسال می‌شود.**
حذف‌های بازگشتی، force push، sudo، اطلاعات محرمانه، نصب پکیج‌ها و فراخوانی‌های خروجی
هر یک قاعده‌ای دارند که می‌توانید فعال کنید. تا زمانی که این کار را نکنید، ClawMetry
نظارت می‌کند و هیچ چیزی را تغییر نمی‌دهد. وقتی یکی فعال شود، فراخوانی‌های منطبق در اینجا
(یا روی گوشی شما) برای تأیید یا رد منتظر می‌مانند.

![تأییدیه‌ها: قواعد محافظتی برای فراخوانی‌های ابزار پرخطر، همه غیرفعال تا زمانی که فعالشان کنید](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

بیشتر، به تفکیک هر ران‌تایم: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## قدردانی‌ها

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
