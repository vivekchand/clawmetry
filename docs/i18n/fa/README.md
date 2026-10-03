<!-- i18n-src:c99ac0512cae -->
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
فایل‌های نشستی را که ایجنت‌های کدنویسی شما از قبل می‌نویسند می‌خواند، و خط زمانی،
فراخوانی‌های ابزار و هر داده‌ای از توکن و هزینه که runtime افشا می‌کند را در یک
نمای واحد قرار می‌دهد — تا بتوانید یک اجرای طولانی که در حال پیشرفت است را از اجرایی که گیر کرده تشخیص دهید.

با **۳۳ runtime ایجنت هوش مصنوعی** کار می‌کند — Claude Code، OpenAI Codex، Hermes، OpenClaw و ۲۹ مورد دیگر. یک داشبورد برای کل ناوگان ایجنت‌های شما. ([فهرست کامل](SUPPORTED_RUNTIMES.txt)، که از کاتالوگ تولید شده است.)

> 🌐 **این متن را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر →](docs/i18n/)

یک دستور. بدون پیکربندی. همه‌چیز را به‌طور خودکار تشخیص می‌دهد.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود. بدون پیکربندی: runtimeهای ایجنتی که از قبل دارید را پیدا می‌کند، آن‌ها را فقط-خواندنی می‌خواند، و هیچ‌چیزی را در نحوه‌ی اجرای آن‌ها تغییر نمی‌دهد.

![داشبورد ClawMetry: هر runtime ایجنت هوش مصنوعی روی یک دستگاه با هزینه ۲۴ ساعته و مادام‌العمر هر ایجنت](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## پیش از نصب

| | |
|---|---|
| **چه کاری انجام می‌دهد** | فایل‌های نشست و لاگ‌هایی را می‌خواند که ایجنت‌های شما از قبل می‌نویسند. بدون SDK، بدون تغییر کد، بدون ابزارسازی در برنامه‌ی شما. |
| **چه چیزی می‌بینید** | خط زمانی نشست، بازپخش ابزار به ابزار، تفکیک توکن و هزینه، و سیگنال‌های مسیر حرکتی (حلقه زدن، شکست‌های تکراری) — به ازای هر runtime. |
| **چه چیزی رایگان است** | `pip install clawmetry` بدون نیاز به حساب کاربری، کلید یا تماس شبکه‌ای، **OpenClaw، NVIDIA NemoClaw، Goose و Qwen Code** را می‌خواند. ۲۸ مورد دیگر — Claude Code، Codex، Cursor و بقیه — توسط افزونه‌ی همراه کد-بسته‌ی `clawmetry-pro` خوانده می‌شوند، که همراه با دوره‌ی آزمایشی ۷ روزه یا یک پلن ارائه می‌شود — برای تفکیک دقیق به [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) مراجعه کنید. |
| **نحوه‌ی شروع** | `pip install clawmetry && clawmetry`، سپس localhost:8900 را باز کنید. هنوز هیچ ایجنتی روی این دستگاه ندارید؟ `clawmetry --sample` با سه نشست مصنوعی برچسب‌گذاری‌شده باز می‌شود. |
| **چه چیزی از دستگاه شما خارج می‌شود** | هیچ داده‌ی نشستی، مگر این‌که `clawmetry connect` را اجرا کنید. دو چیز به‌طور پیش‌فرض اجرا می‌شوند، هر دو قابل غیرفعال‌سازی و هیچ‌کدام حامل محتوای نشست نیستند: یک پینگ نصب ناشناس و یک بررسی نسخه در PyPI. هر مقصد در [docs/EGRESS.md](docs/EGRESS.md) فهرست شده است، که از یک ضبط ترافیک شبکه بازسازی شده نه از خواندن کامنت‌ها. |

دو محدودیت که پیش از قضاوت درباره‌ی خروجی ارزش دانستن دارند: runtimeها داده‌های بسیار
متفاوتی افشا می‌کنند (برخی اصلاً هزینه‌ای منتشر نمی‌کنند — [جدول تطبیق](docs/compatibility.md)
می‌گوید کدام‌ها، به ازای هر runtime)، و مشاهده‌ی یک عمل با توانایی مسدودسازی آن یکسان نیست
([کدام کنترل‌ها واقعی هستند، به ازای هر runtime](docs/APPROVALS.md)).


## با ۳۳ runtime ایجنت کار می‌کند

**رایگان در اپلیکیشن متن‌باز:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**در یک پلن پرداختی:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

هر runtime داشبورد یکسانی دریافت می‌کند. چندین مورد را هم‌زمان اجرا کنید و تعویض‌کننده‌ی هدر
هر تب را مجدداً به یکی از آن‌ها محدود می‌کند.

ایجنت خودتان را روی یک SDK ساخته‌اید؟ interceptor فراخوانی‌های LLM آن را هم ردیابی می‌کند.
به [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) مراجعه کنید.

## چه چیزی به دست می‌آورید

- **نشست‌ها و رونوشت‌ها**: هر ایجنت چه کاری انجام داده، نوبت به نوبت، همراه با بازپخش
- **هزینه و توکن‌ها**: به ازای runtime، مدل، نشست و روز، همراه با نشانه‌های ناهنجاری
- **Flow**: نمودار زنده‌ی پیام‌هایی که از میان کانال‌ها، مدل‌ها و ابزارها حرکت می‌کنند
- **Brain**: جریان رویدادهای استدلال و فراخوانی ابزار به‌محض وقوع
- **انفجار زمینه (Context blowout)**: مصرف پنجره‌ی زمینه که به ازای هر ارائه‌دهنده اندازه‌گذاری شده، فشرده‌سازی در برابر سرریز اجباری، به‌همراه نگاشتی به ازای هر runtime از آنچه *نمی‌توانیم* ببینیم ([چگونه](docs/CONTEXT_BLOWOUT.md))
- **حافظه و مهارت‌ها**: فایل‌ها و مهارت‌هایی که هر runtime واقعاً بارگذاری کرده است
- **سلامت و لاگ‌ها**: دیسک، حافظه، نرخ خطا، محدودیت‌های نرخ، جریان زنده‌ی لاگ
- **هشدارها**: سقف‌های بودجه، جهش‌های خطا، آفلاین‌شدن ایجنت، که به Slack، Discord، PagerDuty، Telegram، Email مسیردهی می‌شوند
- **تأییدها (Approvals)**: توقف فراخوانی‌های ابزار پرخطر *پیش از* اجرا و تأیید آن‌ها از گوشی شما ([چگونه](docs/APPROVALS.md))

## انفجار زمینه، و هزینه‌ی نظارت

دو پرسش که پیش از اعتماد به هر ابزار مقایسه‌ی ایجنت ارزش پاسخ‌دادن دارند.

**چگونه انفجار پنجره‌ی زمینه را در میان runtimeها مدیریت می‌کند؟**

درصد مصرف فقط به اندازه‌ی مخرجی که بر آن تقسیم می‌شود صادقانه است. ClawMetry
اندازه‌ی پنجره را به ازای هر ارائه‌دهنده از [جدولی که می‌توانید بخوانید و
برای آن PR بزنید](clawmetry/context_windows.py) تعیین می‌کند، که Anthropic، OpenAI، Google، xAI،
DeepSeek، Kimi، Qwen، Mistral، Llama و GLM را پوشش می‌دهد. تمام ۳۳
runtime را با خط‌کش یک فروشنده اندازه‌گیری نمی‌کند. این مهم است: یک نوبت ۳۰۰K در GPT-5
که در برابر ۲۰۰K متعلق به Anthropic سنجیده شود «بیش از ۱۰۰٪، منفجرشده» خوانده می‌شود در حالی که
در واقع ۷۵٪ از ۴۰۰K متعلق به GPT-5 است. همان خط‌کش یک نوبت ۱۳۰K DeepSeek را که واقعاً سرریز شده
به‌عنوان ۶۵٪ آسوده پنهان می‌کند.

هر پنجره با منشأ خود ارسال می‌شود: `model_table`، `explicit_marker`،
`observed_floor`، یا یک `default` صادقانه زمانی که مدل را نمی‌شناسیم. یک
گیج ساخته‌شده بر پایه‌ی یک حدس هرگز با همان اعتباری که یک گیج ساخته‌شده بر پایه‌ی
یک جست‌وجو دارد ارائه نمی‌شود.

ClawMetry فقط می‌تواند رویدادهای فشرده‌سازی را در برخی runtimeها ببیند. بنابراین
`GET /api/context-coverage` به ازای هر runtime گزارش می‌دهد که آیا یک **صفر به معنای
"بدون مشکل اجرا شد" یا "ما نابینا هستیم"** است. صفری که واقعاً به معنای نابینایی است همین را می‌گوید.
[جزئیات کامل](docs/CONTEXT_BLOWOUT.md)

**ابزارسازی چه هزینه‌ای دارد؟**

| مسیر | به ایجنت شما افزوده می‌شود | پیش‌فرض؟ |
|---|---|---|
| دنبال‌کردن فایل نشست (هر ۳۳ runtime) | **۰**. فرآیندی جداگانه، بدون کد ClawMetry در ایجنت شما | فعال |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **۰٫۴۴ میلی‌ثانیه+** به ازای هر فراخوانی LLM، یا ۰٫۰۰۹٪ از یک فراخوانی ۵ ثانیه‌ای | غیرفعال |
| دروازه‌ی قلاب پیش-ابزار (کش گرم) | **۴۴ میلی‌ثانیه+** به ازای هر فراخوانی ابزار دروازه‌بانی‌شده، روی یک کف مفسر ۳۶ میلی‌ثانیه‌ای | غیرفعال |
| پراکسی اجرایی (enforcement) | **۹٫۷ میلی‌ثانیه+** به ازای هر فراخوانی LLM | غیرفعال |

هزینه‌ی میزبان daemon: **۲٬۷۶۲ رویداد در ثانیه** جذب، **۷۱۰ بایت در رویداد** روی دیسک
(۶۷٫۷ مگابایت به ازای هر ۱۰۰ هزار رویداد)، و **~۱۲٪ از یک هسته** به‌طور پایدار روی یک
نصب پرمشغله. آن عدد آخر بیش از بودجه‌ی اعلام‌شده‌ی ۵ تا ۱۰٪ ماست، بنابراین
به‌عنوان یک باگ که باید دنبال شود منتشر می‌شود نه آن‌که از صفحه حذف شود.

اندازه‌گیری‌شده روی یک Apple M2 Pro با `benchmarks/overhead.py`. این هارنس هر
شرایط را در یک فرآیند جداگانه اجرا می‌کند، ترتیب آن‌ها را عوض می‌کند، و **از چاپ یک عدد
زمانی که نوبت‌ها در علامتش توافق ندارند خودداری می‌کند**. آن را در دستگاه خودتان در یک دقیقه اجرا کنید:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

هر مسیر اندازه‌گیری شده است، از جمله دروازه‌های قلاب و پراکسی اجرایی،
و این هارنس روی Linux، macOS و Windows در CI اجرا می‌شود. دو نتیجه که ارزش
دانستن دارند: پراکسی روی Windows حدود هفت برابر بیشتر از Linux هزینه دارد، و
daemon در حال حاضر حدود ۱۲٪ از یک هسته را حفظ می‌کند، بیش از بودجه‌ی ۵ تا ۱۰٪
خودمان. JSON خام، روش، و آنچه هنوز اندازه‌گیری نشده در
[docs/OVERHEAD.md](docs/OVERHEAD.md) آمده است.

## قیمت‌گذاری

| پلن | چه چیزی را پوشش می‌دهد | قیمت |
|---|---|---|
| **رایگان** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code، داشبورد کامل، فقط محلی | ۰ دلار |
| **Starter** | هر runtime دیگری که در بالا آمده، نمای ناوگان، همگام‌سازی ابری | ۹ دلار به ازای هر نود / ماه |
| **Pro** | Starter + کنترل و ارزیابی: تأییدها، سیاست‌های ریسک ابزار، ارزیابی‌ها، تشخیص ناهنجاری، بهینه‌ساز هزینه، صادرات OTel، لاگ حسابرسی ضدِ دستکاری | ۱۹ دلار به ازای هر نود / ماه |

پلن‌های سالانه، نسخه‌ی Enterprise و اعداد فعلی در
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** قرار دارند. کلیدهای لایسنس خود-میزبان
بدون نیاز به ابری کار می‌کنند (`clawmetry license`). تفکیک دقیق رایگان/پرداختی
در [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) آمده است.

## داده‌های شما روی دستگاه شما باقی می‌ماند

ClawMetry فایل‌های نشست و لاگ‌های محلی را می‌خواند. **هیچ داده‌ی نشستی از دستگاه شما خارج
نمی‌شود مگر این‌که `clawmetry connect` را اجرا کنید** — نه دستورها، پاسخ‌ها، آرگومان‌های ابزار، محتوای
فایل یا خطوط لاگ. هنگامی که متصل می‌شوید، snapshot به‌صورت رمزگذاری‌شده‌ی سرتاسری
با کلیدی که هرگز از دستگاه شما خارج نمی‌شود رمزگذاری می‌شود، و در مرورگر شما رمزگشایی می‌شود. اگر یک
نود کلیدی نداشته باشد، بارگذاری نادیده گرفته می‌شود به جای ارسال به‌صورت آشکار، و هیچ
پاسخ سروری نمی‌تواند این را خاموش کند.

دو چیز به‌طور پیش‌فرض پیش از اتصال اجرا می‌شوند، هر دو قابل غیرفعال‌سازی و هیچ‌کدام
حامل داده‌ی نشست نیستند: یک پینگ نصب ناشناس و یک بررسی نسخه در برابر
PyPI. یک نصب پیش‌فرض همچنین یک بار آی‌پی عمومی شما را برای خط بنر شروع جست‌وجو می‌کند. هر مقصد، چه چیزی حمل می‌کند و چگونه آن را خاموش کنید در
[docs/EGRESS.md](docs/EGRESS.md) فهرست شده است؛ نصب‌های خود-میزبان، تغییرمسیر‌داده‌شده و ایزوله از شبکه
هیچ تماس خروجی اختیاری انجام نمی‌دهند.

رمزگشایی در مرورگر شما اتفاق می‌افتد، در کدی که به شما ارائه می‌دهیم. این قبلاً
یک وعده بود؛ اکنون چیزی است که می‌توانید بررسی کنید. هر خطی که با کلید شما تماس دارد
در یک فایل خوانا قرار دارد، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
که در داخل wheel ارسال می‌شود و عیناً سرو می‌شود، با یک هش Subresource
Integrity مهر و موم شده. برای تأیید اینکه مرورگر همان چیزی را اجرا می‌کند که منتشر کرده‌ایم:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

آنچه این امر ثابت نمی‌کند: ما صفحه‌ای را سرو می‌کنیم که فایل را بارگذاری می‌کند، بنابراین می‌توانیم
صفحه‌ی متفاوتی سرو کنیم. هش‌های یکپارچگی از شما در برابر یک CDN دچار نفوذ محافظت می‌کنند،
نه در برابر فروشنده. آنچه به دست می‌آورید این است که هر جایگزینی باید
عمدی باشد، در منبع صفحه قابل مشاهده باشد، و با یک artifact روی PyPI که هرکسی
می‌تواند آن را دریافت کند متفاوت باشد. خود-میزبانی یا باقی‌ماندن فقط-محلی این وابستگی را
به‌طور کامل حذف می‌کند.

## نصب

```bash
pip install clawmetry     # سپس: clawmetry
```

یا دستور تک‌خطی: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

به Python 3.8+ روی macOS، Linux یا Windows، و حداقل یک runtime ایجنت روی
همان دستگاه نیاز دارد. دستورالعمل‌های Docker: [docs/DOCKER.md](docs/DOCKER.md).

یا بگذارید ایجنت آن را برای شما راه‌اندازی کند. مهارت [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
به Claude Code، Codex، Cursor، Gemini CLI، Copilot یا OpenCode می‌آموزد که
ClawMetry را نصب کند، آنچه ایجنت‌های روی دستگاه در حال انجام و هزینه‌کردنش هستند را گزارش دهد،
یک نشست را طبق درخواست متوقف کند، و فراخوانی‌های ابزار پرخطر را برای تأیید نگه دارد:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## اسناد

| | |
|---|---|
| [تطبیق runtime](docs/compatibility.md) | هر آداپتور چه چیزی را می‌خواند، و چگونه یک runtime اضافه کنیم |
| [انفجار زمینه](docs/CONTEXT_BLOWOUT.md) | پنجره‌ها به ازای هر ارائه‌دهنده، فشرده‌سازی در برابر سرریز، پوشش به ازای هر runtime |
| [سربار (Overhead)](docs/OVERHEAD.md) | هزینه‌ی ابزارسازی چقدر است، اندازه‌گیری‌شده، همراه با هارنس برای بازتولید آن |
| [حق‌دسترسی‌ها (Entitlements)](docs/ENTITLEMENTS.md) | رایگان در برابر پرداختی، ماتریس سطح، CLI لایسنس |
| [تأییدها و سیاست‌ها](docs/APPROVALS.md) | دروازه‌بانی پیش از اجرا، نمره‌دهی ریسک، تأیید از گوشی |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صادرات ردیابی‌ها به هر جا، جذب OTLP از هر منبع |
| [ایجنت خود را بیاورید](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، Pydantic AI، LangChain از ابتدا تا انتها، همراه با نمونه‌های اجراشدنی |
| [ردیابی SDK](docs/SDK_TRACKING.md) | انتساب هزینه برای ایجنت‌هایی که خودتان ساخته‌اید |
| [کانال‌های چت](docs/CHANNELS.md) | آداپتورهای چت نشان‌داده‌شده در Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | راه‌اندازی‌های ایزوله‌ی NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | ایمیج، compose، volume mountها |
| [معماری](ARCHITECTURE.md) · [توسعه](docs/DEVELOPMENT.md) | نحوه‌ی کار داخلی آن؛ اجرا از سورس |
| [تله‌متری](docs/TELEMETRY.md) | پینگ‌های نصب ناشناس و باز-شدن دسکتاپ، و چگونگی خاموش‌کردن آن‌ها |

## اسکرین‌شات‌ها

هر عددی در زیر از یک دستگاه واقعی، فقط-خواندنی، بدون هیچ‌چیز از پیش کاشته‌شده است.

**به شما می‌گوید وقتی چیزی اشتباه است، نه فقط آنچه اتفاق افتاده.**
دو بنر ناهنجاری در بالا: هزینه‌ای که ۷ برابر میانگین روزانه در حال اجراست، و یک
جهش هزینه‌ی ۴٫۲ برابری. زیر آن‌ها، ۳۲۴ از ۶۶۷ نشست اخیر حامل یک سیگنال
هدررفت، به تفکیک علت.

![نمای کلی: بنرهای ناهنجاری هزینه و جهش هزینه بر فراز کار زنده‌ی ایجنت](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**به شما نشان می‌دهد پول کجا رفته، در هر بازه‌ی زمانی.**
۲۵۲٫۴۷ دلار امروز، ۵۱۳٫۱۵ دلار این هفته، ۱٬۳۱۲٫۹۲ دلار این ماه، هرکدام همراه با توکن‌های
پشت آن و چقدر از آن از قبل توسط اشتراک شما پوشش داده شده است. زیر آن، حدود
۱٬۱۲۸ دلار در ماه به‌عنوان قابل‌بازیابی تفکیک‌شده و ۱۷٬۲۵۶ دلار در ماه که از قبل
با استفاده‌ی مجدد از کش صرفه‌جویی شده است.

![هزینه: امروز، این هفته و این ماه، همراه با یک درجه‌ی کارایی و ایده‌های صرفه‌جویی تفکیک‌شده](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ترسیم می‌کند که یک پیام چگونه به پاسخ تبدیل می‌شود.**
نمودار جریان زنده: شما، کانالی که از طریق آن وارد شده، gateway، مدلی که
همین حالا پاسخ می‌دهد، و هر ابزاری که به آن دسترسی پیدا کرده است. گره‌ها روشن می‌شوند
زمانی که کار از طریق آن‌ها حرکت می‌کند.

![Flow: نمودار زنده از شما از طریق gateway به مدل و ابزارهای آن](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**هر ایجنت روی دستگاه، در یک جدول.**
چه چیزی اجرا می‌کند، چقدر در ۲۴ ساعت گذشته و در طول عمرش هزینه داشته، چه زمانی
آخرین بار دیده شده، چه کسی آن را مالکیت می‌کند، و آیا یک اشتراک هزینه را پوشش می‌دهد.
۱۴ ایجنت در اینجا، ۳ نشست در حال کار، ۱۳ ساکت.

![ایجنت‌ها: هر runtime روی دستگاه همراه با هزینه، مالک، آخرین بازدید و کار فعلی](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**نشان می‌دهد زمان و پول یک نوبت ابزار به ابزار کجا رفته.**
یک نوبت از یک نشست واقعی: ۱۱ ابزار در ۱۱٫۲ دقیقه برای ۱٫۱۶ دلار. هر فراخوانی
Bash و فراخوانی مدل نوار زمانی خود را در خط زمانی دریافت می‌کند، بنابراین دستوری که ۴٫۱
دقیقه اجرا شد و آن که ۲۲۶ میلی‌ثانیه اجرا شد در یک نگاه از هم تفکیک می‌شوند.

![نشست‌ها: یک نوبت ایجنت روی یک خط زمانی، هر فراخوانی ابزار با مدت زمان خودش و هزینه‌ی نوبت](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**کار را نمره‌گذاری می‌کند، نه فقط هزینه را.**
یک A در این هفته: ۵۴ وظیفه تمیز برگشتند، ۲ موردِ ناهموار ۴۸٫۵۷ دلار هزینه داشتند، و
اجراهایی که فعالیت بسیار کمی برای قضاوت داشتند به جای شمارش به‌عنوان برد، از نمره‌دهی
کنار گذاشته شده‌اند. هر اجرای ناهموار به trace خودش متصل می‌شود.

![کیفیت: کارنامه‌ی این هفته با اجراهای ناهموار و هزینه‌ی آن‌ها](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**نشان می‌دهد چرا پنجره‌ی زمینه مدام در حال پرشدن است.**
۷۱۵K از یک پنجره‌ی ۱M توکنی در آخرین نوبت، یک اوج ۸۳٫۳٪، ۴ فشرده‌سازی
که همگی به‌طور پیش‌کنشی به‌جای سرریز شلیک شده‌اند، و میزان مصرف هر نوبت پشت آن.

![مصرف زمینه: مصرف پنجره به ازای هر نوبت، رویدادهای فشرده‌سازی و توکن‌های بازپس‌گرفته‌شده](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**تشخیص بدون نیاز به پیکربندی توسط شما اجرا می‌شود.**
آشکارسازهای درون‌ساخته از زمان نصب فعال هستند: ایجنت ساکت شد، فید تله‌متری
متوقف شد، جهش هزینه، انفجار توکن، خطاهای رو به افزایش، جهش خطا، آستانه‌ی
بودجه، امضای تهدید تطبیق‌یافته، یافته‌ی ابزار امنیتی، وضعیت امنیتی تغییریافته. قوانین
خودتان به‌صورت اختیاری روی این‌ها اضافه می‌شوند.

![هشدارها: آشکارسازهای درون‌ساخته به‌همراه قوانین دلخواه اختیاری](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**نگه‌داشتن یک فراخوانی پرخطر اختیاری است، و بدون آن ارسال می‌شود.**
حذف‌های بازگشتی، force pushها، sudo، اطلاعات محرمانه، نصب پکیج‌ها و فراخوانی‌های
خروجی هرکدام یک قانون دریافت می‌کنند که می‌توانید فعال کنید. تا زمانی که این کار را
نکنید، ClawMetry تماشا می‌کند و چیزی را تغییر نمی‌دهد. وقتی یکی فعال شود، فراخوانی‌های
تطبیق‌یافته اینجا (یا روی گوشی شما) برای تأیید یا رد منتظر می‌مانند.

![تأییدها: قوانین حفاظتی برای فراخوانی‌های ابزار پرخطر، همگی غیرفعال تا زمانی که آن‌ها را فعال کنید](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

بیشتر، به ازای هر runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
