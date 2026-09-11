<!-- i18n-src:12b97259721e -->
> فارسی translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**یک ایجنت می‌تواند صدها فراخوانی ابزار انجام دهد بدون اینکه پیشرفتی حاصل شود.** ClawMetry
فایل‌های نشستی را که ایجنت‌های کدنویسی شما از قبل می‌نویسند می‌خواند، و جدول زمانی،
فراخوانی‌های ابزار و هر داده توکن و هزینه‌ای که runtime در اختیار می‌گذارد را در یک
نما گرد هم می‌آورد — تا بتوانید یک اجرای طولانی که در حال پیشرفت است را از اجرایی که گیر کرده تشخیص دهید.

با **۳۱ runtime ایجنت هوش مصنوعی** کار می‌کند — Claude Code، OpenAI Codex، Hermes، OpenClaw و ۲۷ مورد دیگر. یک داشبورد برای کل ناوگان ایجنت‌های شما. ([فهرست کامل](SUPPORTED_RUNTIMES.txt)، که از کاتالوگ تولید شده است.)

> 🌐 **این را به این زبان‌ها بخوانید:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [بیشتر ←](docs/i18n/)

یک دستور. بدون پیکربندی. تشخیص خودکار همه چیز.

```bash
pip install clawmetry && clawmetry
```

در **http://localhost:8900** باز می‌شود. بدون پیکربندی: runtime‌های ایجنتی که از قبل دارید را پیدا می‌کند، آن‌ها را فقط‌خواندنی می‌خواند، و چیزی در نحوه اجرای آن‌ها تغییر نمی‌دهد.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## قبل از نصب

| | |
|---|---|
| **چه‌کاری انجام می‌دهد** | فایل‌های نشست و لاگ‌هایی که ایجنت‌های شما از قبل می‌نویسند را می‌خواند. بدون SDK، بدون تغییر کد، بدون ابزارسازی درون برنامه شما. |
| **چه چیزی می‌بینید** | جدول زمانی نشست، بازپخش ابزار به ابزار، تفکیک توکن و هزینه، و سیگنال‌های مسیر حرکت (حلقه زدن، شکست‌های تکراری) — بر اساس runtime. |
| **چه چیزی رایگان است** | `pip install clawmetry` بدون نیاز به حساب کاربری، کلید یا فراخوانی شبکه، **OpenClaw، NVIDIA NemoClaw و Goose** را می‌خواند. ۲۷ مورد دیگر — Claude Code، Codex، Cursor و بقیه — توسط افزونه همراه closed-source به نام `clawmetry-pro` خوانده می‌شوند، که همراه با دوره آزمایشی ۷ روزه یا یک پلن ارائه می‌شود — برای تفکیک دقیق به [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) مراجعه کنید. |
| **چگونه شروع کنیم** | `pip install clawmetry && clawmetry`، سپس localhost:8900 را باز کنید. هنوز ایجنتی روی این دستگاه ندارید؟ `clawmetry --sample` با سه نشست مصنوعی برچسب‌گذاری‌شده باز می‌شود. |
| **چه چیزی دستگاه شما را ترک می‌کند** | هیچ داده نشستی، مگر اینکه `clawmetry connect` را اجرا کنید. دو چیز به‌صورت پیش‌فرض اجرا می‌شوند، هر دو opt-out و هیچ‌کدام حامل محتوای نشست نیستند: یک پینگ نصب ناشناس و بررسی نسخه PyPI. هر مقصد در [docs/EGRESS.md](docs/EGRESS.md) فهرست شده، که از یک ضبط بسته‌های شبکه بازسازی شده نه از خواندن کامنت‌ها. |

دو محدودیت که ارزش دانستن قبل از قضاوت درباره خروجی را دارند: runtime‌ها داده‌های
بسیار متفاوتی ارائه می‌دهند (برخی اصلاً هزینه منتشر نمی‌کنند — [ماتریس](docs/compatibility.md)
می‌گوید کدام‌ها، بر اساس runtime)، و مشاهده یک عمل با توانایی مسدود کردن آن یکسان نیست
([کدام کنترل‌ها واقعی هستند، بر اساس runtime](docs/APPROVALS.md)).


## با ۳۱ runtime ایجنت کار می‌کند

**رایگان در برنامه متن‌باز:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**در پلن پولی:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

هر runtime داشبورد یکسانی دریافت می‌کند. چندین را همزمان اجرا کنید و
سوییچر بالای صفحه هر برگه را دوباره به یکی از آن‌ها محدود می‌کند.

ایجنت خودتان را روی یک SDK ساخته‌اید؟ رهگیر (interceptor) فراخوانی‌های LLM آن را هم
ردیابی می‌کند. به [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md) مراجعه کنید.

## چه چیزی به دست می‌آورید

- **نشست‌ها و رونوشت‌ها**: هر ایجنت چه کاری انجام داد، نوبت به نوبت، با بازپخش
- **هزینه و توکن‌ها**: بر اساس runtime، مدل، نشست و روز، همراه با پرچم‌های ناهنجاری
- **جریان**: نمودار زنده پیام‌هایی که از میان کانال‌ها، مدل‌ها و ابزارها عبور می‌کنند
- **مغز**: جریان رویدادهای استدلال و فراخوانی ابزار در همان لحظه رخداد
- **انفجار زمینه (context)**: استفاده از پنجره متناسب با هر ارائه‌دهنده، فشرده‌سازی در برابر سرریز اجباری، به‌علاوه نقشه‌ای بر اساس runtime از آنچه *نمی‌توانیم* ببینیم ([چگونه](docs/CONTEXT_BLOWOUT.md))
- **حافظه و مهارت‌ها**: فایل‌ها و مهارت‌هایی که هر runtime واقعاً بارگذاری کرده
- **سلامت و لاگ‌ها**: دیسک، حافظه، نرخ خطا، محدودیت نرخ، جریان لاگ زنده
- **هشدارها**: سقف بودجه، جهش خطا، آفلاین شدن ایجنت، مسیریابی‌شده به Slack، Discord، PagerDuty، Telegram، ایمیل
- **تأییدها**: توقف فراخوانی‌های ابزار پرریسک *پیش از* اجرا و تأیید از گوشی شما ([چگونه](docs/APPROVALS.md))

## انفجار زمینه (context blowout)، و هزینه نظارت

دو پرسش که ارزش پاسخ دادن پیش از اعتماد به هر ابزار مقایسه ایجنت را دارند.

**چگونه با انفجار پنجره زمینه در میان runtime‌های مختلف برخورد می‌کند؟**

یک درصد بهره‌برداری فقط به‌اندازه صداقت مخرج آن معتبر است. ClawMetry
پنجره را بر اساس هر ارائه‌دهنده از [جدولی که می‌توانید بخوانید و
درخواست تغییر (PR) دهید](clawmetry/context_windows.py) اندازه‌گذاری می‌کند، که Anthropic، OpenAI، Google، xAI،
DeepSeek، Kimi، Qwen، Mistral، Llama و GLM را پوشش می‌دهد. این ابزار هر ۳۱
runtime را با خط‌کش یک فروشنده اندازه‌گیری نمی‌کند. این مهم است: یک نوبت 300K توکنی GPT-5
که در برابر 200K توکنی Anthropic سنجیده شود، ">100%، منفجر شده" خوانده می‌شود درحالی‌که
واقعاً در 75% از 400K توکن GPT-5 قرار دارد. همان خط‌کش یک نوبت 130K توکنی DeepSeek که
واقعاً سرریز شده را به‌عنوان یک 65% راحت پنهان می‌کند.

هر پنجره با منشأ خود ارسال می‌شود: `model_table`، `explicit_marker`،
`observed_floor`، یا یک `default` صادقانه وقتی مدل را نمی‌شناسیم. یک گیج
ساخته‌شده بر پایه حدس هرگز با همان اعتباری که یک گیج ساخته‌شده بر پایه جست‌وجو
دارد رندر نمی‌شود.

ClawMetry فقط می‌تواند رویدادهای فشرده‌سازی را در برخی runtime‌ها ببیند. پس
`GET /api/context-coverage` گزارش می‌دهد، بر اساس runtime، که آیا یک **صفر
یعنی "پاک اجرا شد" یا "ما کور هستیم"**. یک `0` که واقعاً به معنای کور بودن است
این را اعلام می‌کند.
[جزئیات کامل](docs/CONTEXT_BLOWOUT.md)

**ابزارسازی چه هزینه‌ای دارد؟**

| مسیر | افزوده‌شده به ایجنت شما | پیش‌فرض؟ |
|---|---|---|
| دنبال کردن فایل نشست (هر ۳۱ runtime) | **۰**. فرآیند جداگانه، بدون کد ClawMetry در ایجنت شما | روشن |
| رهگیر HTTP (`CLAWMETRY_INTERCEPT=1`) | **+۰.۴۴ میلی‌ثانیه** به ازای هر فراخوانی LLM، یا 0.009% از یک فراخوانی 5 ثانیه‌ای | خاموش |
| دروازه هوک پیش از ابزار (کش گرم) | **+۴۴ میلی‌ثانیه** به ازای هر فراخوانی ابزار دروازه‌بانی‌شده، بر روی کف ۳۶ میلی‌ثانیه‌ای مفسر | خاموش |
| پراکسی اجرا (enforcement) | **+۹.۷ میلی‌ثانیه** به ازای هر فراخوانی LLM | خاموش |

هزینه میزبان daemon: **۲٬۷۶۲ رویداد/ثانیه** دریافت (ingest)، **۷۱۰ بایت/رویداد** روی دیسک
(67.7 مگابایت به ازای هر 100 هزار رویداد)، و **~۱۲٪ از یک هسته** به‌صورت پایدار روی
یک نصب پرکار. این عدد آخر بالاتر از بودجه اعلام‌شده ما یعنی 5 تا 10 درصد است، پس
به‌عنوان یک باگ برای دنبال کردن منتشر شده نه اینکه از صفحه حذف شود.

اندازه‌گیری‌شده روی Apple M2 Pro با `benchmarks/overhead.py`. این ابزار
هر شرایط را در یک فرآیند جداگانه اجرا می‌کند، ترتیب آن‌ها را متناوب می‌کند، و
**از چاپ یک عدد وقتی دورها بر سر علامت آن توافق ندارند خودداری می‌کند**. آن را روی
دستگاه خودتان در یک دقیقه اجرا کنید:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

هر مسیر اندازه‌گیری شده، از جمله دروازه‌های هوک و پراکسی اجرا، و این ابزار
روی Linux، macOS و Windows در CI اجرا می‌شود. دو نتیجه که ارزش دانستن دارند: پراکسی
حدود هفت برابر بیشتر روی Windows نسبت به Linux هزینه دارد، و daemon در حال حاضر
حدود 12% از یک هسته را به‌صورت پایدار مصرف می‌کند، بیش از بودجه 5 تا 10 درصدی خودمان.
JSON خام، روش کار، و آنچه هنوز اندازه‌گیری نشده در
[docs/OVERHEAD.md](docs/OVERHEAD.md) موجود است.

## قیمت‌گذاری

| پلن | چه چیزی را پوشش می‌دهد | قیمت |
|---|---|---|
| **رایگان** | OpenClaw + NVIDIA NemoClaw + Goose، داشبورد کامل، فقط محلی | ۰ دلار |
| **Starter** | هر runtime دیگری در بالا، نمای ناوگان، همگام‌سازی ابری | ۹ دلار به ازای هر نود / ماه |
| **Pro** | Starter + کنترل و ارزیابی: تأییدها، سیاست‌های ریسک ابزار، ارزیابی‌ها، تشخیص ناهنجاری، بهینه‌ساز هزینه، خروجی OTel، لاگ حسابرسی مقاوم در برابر دستکاری | ۱۹ دلار به ازای هر نود / ماه |

پلن‌های سالانه، Enterprise و اعداد فعلی در
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** موجود است. کلیدهای
لایسنس self-hosted بدون نیاز به ابر کار می‌کنند (`clawmetry license`). تفکیک دقیق
رایگان/پولی در [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) آمده است.

## داده‌های شما روی دستگاه شما باقی می‌ماند

ClawMetry فایل‌های نشست و لاگ‌های محلی را می‌خواند. **هیچ داده نشستی دستگاه شما را
ترک نمی‌کند مگر اینکه `clawmetry connect` را اجرا کنید** — بدون پرامپت‌ها، پاسخ‌ها،
آرگومان‌های ابزار، محتوای فایل یا خطوط لاگ. وقتی متصل می‌شوید، اسنپ‌شات به‌صورت
سرتاسر رمزنگاری‌شده با کلیدی است که هرگز دستگاه شما را ترک نمی‌کند، و در مرورگر شما
رمزگشایی می‌شود. اگر یک نود کلیدی نداشته باشد، آپلود به‌جای ارسال به‌صورت رمزنگاری‌نشده
نادیده گرفته می‌شود، و هیچ پاسخ سروری نمی‌تواند این را خاموش کند.

دو چیز به‌صورت پیش‌فرض پیش از اتصال شما اجرا می‌شوند، هر دو opt-out و هیچ‌کدام
حامل داده نشست نیستند: یک پینگ نصب ناشناس و بررسی نسخه در برابر PyPI. یک نصب
پیش‌فرض همچنین IP عمومی شما را یک بار برای یک خط بنر آغازین جست‌وجو می‌کند. هر مقصد،
آنچه حمل می‌کند و چگونگی خاموش کردن آن در
[docs/EGRESS.md](docs/EGRESS.md) فهرست شده است؛ نصب‌های self-hosted، تغییرمسیر داده‌شده و
air-gapped هیچ فراخوانی خروجی اختیاری‌ای انجام نمی‌دهند.

رمزگشایی در مرورگر شما، در کدی که به شما تحویل می‌دهیم، رخ می‌دهد. این قبلاً
یک وعده بود؛ اکنون چیزی است که می‌توانید بررسی کنید. هر خطی که به کلید شما دست می‌زند
در یک فایل خوانا زندگی می‌کند، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
که درون wheel ارسال می‌شود و عیناً تحویل داده می‌شود، پین‌شده با یک هش Subresource
Integrity. برای تأیید اینکه مرورگر چیزی را که منتشر کردیم اجرا می‌کند:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

چیزی که این ثابت نمی‌کند: ما صفحه‌ای که فایل را بارگذاری می‌کند تحویل می‌دهیم، پس
می‌توانستیم صفحه دیگری تحویل دهیم. هش‌های integrity شما را از یک CDN به‌خطرافتاده
محافظت می‌کنند، نه از فروشنده. چیزی که به دست می‌آورید این است که هر جایگزینی باید
عمدی، در سورس صفحه قابل‌مشاهده، و متفاوت از یک artifact روی PyPI باشد که هرکسی
می‌تواند دریافت کند. self-host کردن یا محلی-فقط ماندن کاملاً این وابستگی را حذف می‌کند.

## نصب

```bash
pip install clawmetry     # سپس: clawmetry
```

یا دستور یک‌خطی: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

به Python 3.8+ روی macOS، Linux یا Windows، و حداقل یک runtime ایجنت روی همان دستگاه
نیاز دارد. دستورالعمل‌های Docker: [docs/DOCKER.md](docs/DOCKER.md).

یا بگذارید ایجنت آن را برای شما راه‌اندازی کند. مهارت [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
به Claude Code، Codex، Cursor، Gemini CLI، Copilot یا OpenCode یاد می‌دهد که
ClawMetry را نصب کند، آنچه ایجنت‌های روی دستگاه انجام می‌دهند و خرج می‌کنند را گزارش دهد،
یک نشست را در صورت درخواست متوقف کند، و فراخوانی‌های ابزار پرریسک را برای تأیید نگه دارد:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## مستندات

| | |
|---|---|
| [سازگاری runtime](docs/compatibility.md) | هر آداپتور چه چیزی می‌خواند، و چگونه یک runtime اضافه کنیم |
| [انفجار زمینه](docs/CONTEXT_BLOWOUT.md) | پنجره‌ها بر اساس ارائه‌دهنده، فشرده‌سازی در برابر سرریز، پوشش بر اساس runtime |
| [سربار](docs/OVERHEAD.md) | ابزارسازی چه هزینه‌ای دارد، اندازه‌گیری‌شده، همراه با ابزاری برای بازتولید آن |
| [مجوزها](docs/ENTITLEMENTS.md) | رایگان در برابر پولی، ماتریس سطح، CLI لایسنس |
| [تأییدها و سیاست‌ها](docs/APPROVALS.md) | دروازه‌بانی پیش از اجرا، امتیازدهی ریسک، تأییدهای گوشی |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | خروجی trace به هرجا، دریافت OTLP از هرچیزی |
| [ایجنت خودتان را بیاورید](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، Pydantic AI، LangChain سرتاسر، با نمونه‌های قابل‌اجرا |
| [ردیابی SDK](docs/SDK_TRACKING.md) | انتساب هزینه برای ایجنت‌هایی که خودتان ساخته‌اید |
| [کانال‌های چت](docs/CHANNELS.md) | آداپتورهای چت نمایش‌داده‌شده در Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | تنظیمات sandboxed NVIDIA NemoClaw |
| [Docker](docs/DOCKER.md) | تصویر، compose، مونت‌های حجم |
| [معماری](ARCHITECTURE.md) · [توسعه](docs/DEVELOPMENT.md) | چگونگی کارکرد درونی؛ اجرا از سورس |
| [تله‌متری](docs/TELEMETRY.md) | پینگ‌های نصب ناشناس و باز شدن دسکتاپ، و چگونگی خاموش کردن آن‌ها |

## اسکرین‌شات‌ها

هر عدد در زیر از یک دستگاه واقعی، فقط‌خواندنی، بدون هیچ‌چیز seed‌شده است.

**به شما می‌گوید چه زمانی چیزی اشتباه است، نه فقط چه اتفاقی افتاده.**
دو بنر ناهنجاری در بالا: هزینه‌ای که ۷ برابر میانگین روزانه در حال اجراست، و
یک جهش هزینه ۴.۲ برابری. زیر آن‌ها، ۳۲۴ از ۶۶۷ نشست اخیر حامل یک سیگنال
اتلاف، تفکیک‌شده بر اساس علت.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**به شما نشان می‌دهد پول کجا رفت، در هر بازه زمانی.**
۲۵۲.۴۷ دلار امروز، ۵۱۳.۱۵ دلار این هفته، ۱٬۳۱۲.۹۲ دلار این ماه، هرکدام همراه با
توکن‌های پشت آن‌ها و اینکه اشتراک شما در حال حاضر چقدر از آن را پوشش می‌دهد. زیر آن،
حدود ۱٬۱۲۸ دلار در ماه به‌عنوان قابل‌بازیافت تفکیک‌شده و ۱۷٬۲۵۶ دلار در ماه که از قبل
با استفاده مجدد از کش صرفه‌جویی شده.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**نحوه تبدیل یک پیام به پاسخ را ترسیم می‌کند.**
نمودار جریان زنده: شما، کانالی که از آن رسید، gateway، مدلی که همین الان
پاسخ می‌دهد، و هر ابزاری که به دنبال آن رفت. گره‌ها با عبور کار از میان آن‌ها
روشن می‌شوند.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**هر ایجنت روی دستگاه، در یک جدول.**
چه چیزی اجرا می‌کند، چه هزینه‌ای در ۲۴ ساعت گذشته و در طول عمر خود دارد، آخرین بار
چه زمانی دیده شده، چه کسی مالک آن است، و آیا یک اشتراک هزینه را پوشش می‌دهد. ۱۴
ایجنت اینجا، ۳ نشست در حال کار، ۱۳ ساکت.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**نشان می‌دهد زمان و پول یک نوبت کجا رفت، ابزار به ابزار.**
یک نوبت از یک نشست واقعی: ۱۱ ابزار در ۱۱.۲ دقیقه به قیمت ۱.۱۶ دلار. هر فراخوانی
Bash و فراخوانی مدل نوار زمانی خودش را روی جدول زمانی می‌گیرد، پس دستوری که ۴.۱
دقیقه اجرا شد و دستوری که ۲۲۶ میلی‌ثانیه اجرا شد در یک نگاه از هم تشخیص داده می‌شوند.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**کار را نمره می‌دهد، نه فقط هزینه را.**
یک A این هفته: ۵۴ وظیفه تمیز برگشتند، ۲ وظیفه ناهموار ۴۸.۵۷ دلار هزینه داشتند، و
اجراهایی که فعالیت خیلی کمی برای قضاوت داشتند از نمره کنار گذاشته شدند به‌جای
اینکه به‌عنوان برد شمرده شوند. هر اجرای ناهموار به trace خودش لینک می‌شود.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**نشان می‌دهد چرا پنجره زمینه (context) همچنان پر می‌شود.**
۷۱۵K توکن از پنجره ۱ میلیون توکنی در آخرین نوبت، اوج ۸۳.۳٪، ۴ فشرده‌سازی که
همگی پیشگیرانه شلیک شدند نه در پی سرریز، به‌علاوه بهره‌برداری هر نوبت پشت آن.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**تشخیص بدون هیچ پیکربندی از سوی شما اجرا می‌شود.**
تشخیص‌دهنده‌های داخلی از زمان نصب روشن هستند: ایجنت ساکت شد، فید تله‌متری
متوقف شد، جهش هزینه، انفجار توکن، خطاهای در حال افزایش، جهش خطا، آستانه بودجه،
امضای تهدید تطبیق‌یافته، یافته ابزار امنیتی، تغییر وضعیت امنیتی. قوانین
خودتان به‌صورت اختیاری روی آن اضافه می‌شوند.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**نگه داشتن یک فراخوانی پرریسک اختیاری است، و به‌صورت خاموش عرضه می‌شود.**
حذف‌های بازگشتی، force push، sudo، اسرار، نصب بسته و فراخوانی‌های خروجی هرکدام
قانونی دارند که می‌توانید روشن کنید. تا زمانی که این کار را نکنید، ClawMetry
نظاره می‌کند و چیزی را تغییر نمی‌دهد. وقتی یکی را روشن کردید، فراخوانی‌های
منطبق اینجا (یا روی گوشی شما) منتظر تأیید یا رد می‌مانند.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

بیشتر، بر اساس runtime: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## قدردانی‌ها

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## تاریخچه ستاره

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
