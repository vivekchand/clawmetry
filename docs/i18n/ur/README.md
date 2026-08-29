<!-- i18n-src:d21bea5161e0 -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **30 AI ایجنٹ رن ٹائمز** کے لیے حقیقی وقت کی مشاہداتی سہولت: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور 26 مزید۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ہی ڈیش بورڈ۔

> 🌐 **اسے ان زبانوں میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ صفر کنفیگریشن۔ سب کچھ خودکار طور پر معلوم کرتا ہے۔

```bash
pip install clawmetry && clawmetry
```

یہ **http://localhost:8900** پر کھلتا ہے۔ صفر کنفیگریشن: یہ آپ کے پاس پہلے سے موجود ایجنٹ رن ٹائمز کو ڈھونڈتا ہے، انہیں صرف پڑھنے کے انداز میں پڑھتا ہے، اور ان کے چلنے کے طریقے میں کچھ بھی تبدیل نہیں کرتا۔

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## 30 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

**اوپن سورس ایپ میں مفت:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ادائیگی والے پلان پر:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ہر رن ٹائم کو ایک جیسا ڈیش بورڈ ملتا ہے۔ ایک ساتھ کئی چلائیں اور ہیڈر سوئچر ہر ٹیب کو ان میں سے کسی ایک کے دائرہ کار میں دوبارہ لے آتا ہے۔

اپنا خود کا ایجنٹ کسی SDK پر بنایا ہے؟ انٹرسیپٹر اس کی LLM کالز کو بھی ٹریک کرتا ہے۔ دیکھیں [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)۔

## آپ کو کیا ملتا ہے

- **سیشنز اور ٹرانسکرپٹس**: ہر ایجنٹ نے کیا کیا، باری بہ باری، ری پلے کے ساتھ
- **لاگت اور ٹوکنز**: فی رن ٹائم، ماڈل، سیشن اور دن، بے قاعدگی کی نشاندہی کے ساتھ
- **فلو**: چینلز، ماڈلز اور ٹولز کے درمیان حرکت کرنے والے پیغامات کا زندہ خاکہ
- **برین**: استدلال اور ٹول کال کا ایونٹ سٹریم جیسے جیسے ہوتا ہے
- **کانٹیکسٹ بلو آؤٹ**: فراہم کنندہ کے حساب سے ونڈو کا استعمال، کمپیکشن بمقابلہ جبری اوورفلو، اور ہر رن ٹائم کا نقشہ کہ ہم *کیا نہیں* دیکھ سکتے ([کیسے](docs/CONTEXT_BLOWOUT.md))
- **میموری اور اسکلز**: وہ فائلیں اور اسکلز جو ہر رن ٹائم نے واقعی لوڈ کیے
- **صحت اور لاگز**: ڈسک، میموری، خرابی کی شرح، ریٹ لمٹس، زندہ لاگ سٹریم
- **الرٹس**: بجٹ کیپس، ایرر اسپائیکس، ایجنٹ آف لائن، Slack، Discord، PagerDuty، Telegram، ای میل کی طرف روٹ کیے گئے
- **منظوریاں**: خطرناک ٹول کالز کو چلنے سے *پہلے* روکیں اور اپنے فون سے منظور کریں ([کیسے](docs/APPROVALS.md))

## کانٹیکسٹ بلو آؤٹ، اور نگرانی کی قیمت

دو سوالات جن کا جواب کسی بھی ایجنٹ موازنہ ٹول پر بھروسہ کرنے سے پہلے دینا ضروری ہے۔

**یہ رن ٹائمز میں کانٹیکسٹ ونڈو بلو آؤٹ کو کیسے ہینڈل کرتا ہے؟**

استعمال کا فیصد اتنا ہی درست ہوتا ہے جتنا وہ عدد جس سے اسے تقسیم کیا جاتا ہے۔ ClawMetry ہر فراہم کنندہ کے لیے ونڈو کا سائز ایک [ٹیبل](clawmetry/context_windows.py) سے لیتا ہے جسے آپ پڑھ اور PR کر سکتے ہیں، جو Anthropic، OpenAI، Google، xAI، DeepSeek، Kimi، Qwen، Mistral، Llama اور GLM کا احاطہ کرتا ہے۔ یہ تمام 26 رن ٹائمز کو ایک ہی فراہم کنندہ کے پیمانے سے نہیں ناپتا۔ یہ اہم ہے: ایک 300K GPT-5 ٹرن جب Anthropic کے 200K کے مقابلے میں ناپا جائے تو ">100%، بلوون" پڑھتا ہے جبکہ حقیقت میں یہ GPT-5 کے 400K کا 75% ہے۔ وہی پیمانہ ایک حقیقتاً اوورفلو ہو چکے 130K DeepSeek ٹرن کو آرام دہ 65% کے طور پر چھپا دیتا ہے۔

ہر ونڈو اپنی ماخذیت کے ساتھ آتی ہے: `model_table`، `explicit_marker`، `observed_floor`، یا جب ہمیں ماڈل معلوم نہ ہو تو ایک ایماندار `default`۔ اندازے پر بنایا گیا گیج کبھی بھی لُک اپ پر بنائے گئے گیج جتنی اتھارٹی کے ساتھ نہیں دکھایا جاتا۔

ClawMetry صرف کچھ رن ٹائمز پر کمپیکشن ایونٹس دیکھ سکتا ہے۔ اس لیے `GET /api/context-coverage` ہر رن ٹائم کے لیے یہ رپورٹ کرتا ہے کہ آیا **صفر کا مطلب "صاف چلا" ہے یا "ہم اندھے ہیں"**۔ ایک `0` جس کا اصل مطلب اندھا پن ہے، وہ ایسا ہی بتاتا ہے۔
[مکمل تفصیل](docs/CONTEXT_BLOWOUT.md)

**انسٹرومینٹیشن کی قیمت کیا ہے؟**

| راستہ | آپ کے ایجنٹ میں شامل | ڈیفالٹ؟ |
|---|---|---|
| سیشن فائل ٹیلنگ (تمام 30 رن ٹائمز) | **0**۔ الگ پراسیس، آپ کے ایجنٹ میں کوئی ClawMetry کوڈ نہیں | آن |
| HTTP انٹرسیپٹر (`CLAWMETRY_INTERCEPT=1`) | فی LLM کال **+0.44 ms**، یا 5s کال کا 0.009% | آف |
| پری ٹول ہک گیٹ (وارم کیش) | فی گیٹڈ ٹول کال **+44 ms**، 36 ms انٹرپریٹر فلور کے اوپر | آف |
| اینفورسمنٹ پراکسی | فی LLM کال **+9.7 ms** | آف |

ڈیمن ہوسٹ لاگت: **2,762 events/sec** انجیسٹ، ڈسک پر **710 bytes/event** (67.7 MB فی 100 ہزار ایونٹس)، اور ایک مصروف انسٹال پر مسلسل **~12% ایک کور کا**۔ یہ آخری عدد ہمارے اپنے بیان کردہ 5-10% بجٹ سے زیادہ ہے، اس لیے اسے صفحے سے ہٹانے کے بجائے پیچھا کرنے کے قابل ایک بگ کے طور پر شائع کیا گیا ہے۔

Apple M2 Pro پر `benchmarks/overhead.py` کے ساتھ ناپا گیا۔ ہارنیس ہر کنڈیشن کو الگ پراسیس میں چلاتا ہے، ان کی ترتیب کو بدلتا رہتا ہے، اور **جب راؤنڈز کسی عدد کی علامت پر متفق نہ ہوں تو اسے چھاپنے سے انکار کر دیتا ہے**۔ اسے اپنی مشین پر ایک منٹ میں چلائیں:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ہر راستہ ناپا گیا ہے، بشمول ہک گیٹس اور اینفورسمنٹ پراکسی، اور ہارنیس CI میں Linux، macOS اور Windows پر چلتا ہے۔ جاننے کے لائق دو نتائج: پراکسی کی قیمت Windows پر Linux کے مقابلے میں تقریباً سات گنا زیادہ ہے، اور ڈیمن فی الحال ایک کور کا تقریباً 12% مسلسل استعمال کرتا ہے، جو ہمارے اپنے 5-10% بجٹ سے زیادہ ہے۔ خام JSON، طریقہ کار، اور ابھی تک نہ ناپی گئی چیزیں [docs/OVERHEAD.md](docs/OVERHEAD.md) میں موجود ہیں۔

## قیمتیں

| پلان | یہ کیا احاطہ کرتا ہے | قیمت |
|---|---|---|
| **مفت** | OpenClaw + NVIDIA NemoClaw + Goose، مکمل ڈیش بورڈ، صرف لوکل | $0 |
| **اسٹارٹر** | اوپر دیے گئے ہر دوسرے رن ٹائم، فلیٹ ویو، کلاؤڈ سنک | $9 فی نوڈ / مہینہ |
| **Pro** | اسٹارٹر + کنٹرول اور جانچ: منظوریاں، ٹول رسک پالیسیاں، ایویلز، بے قاعدگی کی شناخت، کاسٹ آپٹیمائزر، OTel ایکسپورٹ، ٹیمپر ایویڈنٹ آڈٹ لاگ | $19 فی نوڈ / مہینہ |

سالانہ پلانز، انٹرپرائز اور موجودہ اعداد و شمار
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** پر موجود ہیں۔ سیلف ہوسٹڈ لائسنس
کیز کلاؤڈ کے بغیر بھی کام کرتی ہیں (`clawmetry license`)۔ مفت/ادائیگی کی درست تقسیم
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) میں موجود ہے۔

## آپ کا ڈیٹا آپ کی مشین پر ہی رہتا ہے

ClawMetry مقامی سیشن فائلیں اور لاگز پڑھتا ہے۔ **آپ کے `clawmetry connect` چلانے تک کوئی سیشن ڈیٹا آپ کے
باکس سے باہر نہیں جاتا** — نہ پرامپٹس، نہ جوابات، نہ ٹول آرگیومنٹس، نہ فائل
مواد اور نہ ہی لاگ لائنز۔ جب آپ کنیکٹ کرتے ہیں، تو سنیپ شاٹ ایسی چابی کے ساتھ
اینڈ ٹو اینڈ انکرپٹڈ ہوتا ہے جو کبھی آپ کی مشین سے باہر نہیں جاتی، اور آپ کے
براؤزر میں ڈی کرپٹ ہوتا ہے۔ اگر کسی نوڈ کے پاس چابی نہ ہو، تو اپ لوڈ صاف
متن میں بھیجنے کے بجائے چھوڑ دیا جاتا ہے، اور کوئی سرور جواب اسے بند نہیں کر سکتا۔

دو چیزیں کنیکٹ کرنے سے پہلے ہی ڈیفالٹ کے طور پر چلتی ہیں، دونوں آپٹ آؤٹ اور
کوئی بھی سیشن ڈیٹا نہیں لے جاتیں: ایک گمنام انسٹال پنگ اور PyPI کے خلاف ایک
ورژن چیک۔ ایک ڈیفالٹ انسٹال آغازی بینر لائن کے لیے آپ کا پبلک IP بھی ایک بار
تلاش کرتا ہے۔ ہر منزل، وہ کیا لے جاتی ہے اور اسے کیسے بند کیا جائے، سب کچھ
[docs/EGRESS.md](docs/EGRESS.md) میں درج ہے؛ سیلف ہوسٹڈ، ری پوائنٹڈ اور ایئر گیپڈ
انسٹالز کوئی اختیاری آؤٹ باؤنڈ کالز بالکل نہیں کرتیں۔

ڈی کرپشن آپ کے براؤزر میں، ہمارے فراہم کردہ کوڈ میں ہوتی ہے۔ یہ پہلے ایک
وعدہ تھا؛ اب یہ ایک ایسی چیز ہے جسے آپ چیک کر سکتے ہیں۔ آپ کی چابی کو چھونے
والی ہر لائن ایک قابلِ مطالعہ فائل، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
میں موجود ہے، جو وہیل کے اندر شپ ہوتی ہے اور بعینہ سرو کی جاتی ہے، ایک
سب ریسورس انٹیگریٹی ہیش کے ساتھ پن کی گئی۔ یہ تصدیق کرنے کے لیے کہ براؤزر
وہی چلاتا ہے جو ہم نے شائع کیا:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

یہ کیا ثابت نہیں کرتا: ہم وہ صفحہ سرو کرتے ہیں جو فائل کو لوڈ کرتا ہے، تو ہم
ایک مختلف صفحہ بھی سرو کر سکتے ہیں۔ انٹیگریٹی ہیشز آپ کو ایک سمجھوتہ شدہ CDN
سے بچاتے ہیں، وینڈر سے نہیں۔ آپ کو جو حاصل ہوتا ہے وہ یہ ہے کہ کسی بھی متبادل
کو جان بوجھ کر، صفحے کے سورس میں نظر آنے والا، اور PyPI پر موجود ایک ایسے
آرٹیفیکٹ سے مختلف ہونا پڑے گا جسے کوئی بھی حاصل کر سکتا ہے۔ سیلف ہوسٹنگ یا
صرف لوکل رہنا اس انحصار کو مکمل طور پر ختم کر دیتا ہے۔

## انسٹال

```bash
pip install clawmetry     # پھر: clawmetry
```

یا ایک لائنر: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS، Linux یا Windows پر Python 3.8+ اور اسی مشین پر کم از کم ایک ایجنٹ
رن ٹائم درکار ہے۔ Docker ہدایات: [docs/DOCKER.md](docs/DOCKER.md)۔

## دستاویزات

| | |
|---|---|
| [رن ٹائم مطابقت](docs/compatibility.md) | ہر ایڈاپٹر کیا پڑھتا ہے، اور رن ٹائم کیسے شامل کریں |
| [کانٹیکسٹ بلو آؤٹ](docs/CONTEXT_BLOWOUT.md) | فراہم کنندہ کے حساب سے ونڈوز، کمپیکشن بمقابلہ اوورفلو، فی رن ٹائم کوریج |
| [اووَرہیڈ](docs/OVERHEAD.md) | انسٹرومینٹیشن کی قیمت کیا ہے، ناپی گئی، اسے دوبارہ پیدا کرنے کے ہارنیس کے ساتھ |
| [اہلیت](docs/ENTITLEMENTS.md) | مفت بمقابلہ ادائیگی، ٹیئر میٹرکس، لائسنس CLI |
| [منظوریاں اور پالیسیاں](docs/APPROVALS.md) | پری ایگزیکیوشن گیٹنگ، رسک اسکورنگ، فون منظوریاں |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | کہیں بھی ٹریسز ایکسپورٹ کریں، کہیں سے بھی OTLP انجیسٹ کریں |
| [SDK ٹریکنگ](docs/SDK_TRACKING.md) | آپ کے اپنے بنائے ہوئے ایجنٹس کے لیے کاسٹ اٹریبیوشن |
| [چیٹ چینلز](docs/CHANNELS.md) | فلو میں دکھائے گئے چیٹ ایڈاپٹرز |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | سینڈ باکسڈ NVIDIA NemoClaw سیٹ اپس |
| [Docker](docs/DOCKER.md) | امیج، کمپوز، والیوم ماؤنٹس |
| [آرکیٹیکچر](ARCHITECTURE.md) · [ڈیویلپمنٹ](docs/DEVELOPMENT.md) | یہ اندر سے کیسے کام کرتا ہے؛ سورس سے چلانا |
| [ٹیلی میٹری](docs/TELEMETRY.md) | گمنام انسٹال اور ڈیسک ٹاپ اوپن پنگز، اور انہیں کیسے بند کریں |

## اسکرین شاٹس

نیچے موجود ہر عدد ایک حقیقی مشین سے ہے، صرف پڑھنے کے انداز میں، بغیر کسی سیڈنگ کے۔

**یہ آپ کو بتاتا ہے کہ کب کچھ غلط ہے، نہ کہ صرف یہ کہ کیا ہوا۔**
اوپر دو بے قاعدگی بینرز: خرچ روزانہ اوسط سے 7 گنا چل رہا ہے، اور ایک
4.2x لاگت کا اضافہ۔ ان کے نیچے، حالیہ 667 سیشنز میں سے 324 ضیاع کی
علامت لیے ہوئے ہیں، وجہ کے حساب سے الگ الگ درج۔

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**یہ آپ کو دکھاتا ہے کہ پیسہ کہاں گیا، ہر ونڈو میں۔**
آج $252.47، اس ہفتے $513.15، اس مہینے $1,312.92، ہر ایک کے پیچھے ٹوکنز
اور آپ کا سبسکرپشن پہلے سے کتنا احاطہ کرتا ہے۔ اس کے نیچے، تقریباً
$1,128/ماہ قابلِ بازیافت کے طور پر درج، اور $17,256/ماہ پہلے ہی
کیش ری یوز سے بچائے گئے۔

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**یہ دکھاتا ہے کہ ایک پیغام کیسے جواب بنتا ہے۔**
زندہ فلو خاکہ: آپ، وہ چینل جس پر یہ پہنچا، گیٹ وے، ابھی جواب دینے والا
ماڈل، اور ہر ٹول جسے اس نے استعمال کیا۔ کام آگے بڑھنے کے ساتھ ساتھ نوڈز
روشن ہوتے ہیں۔

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**مشین پر موجود ہر ایجنٹ، ایک ہی ٹیبل میں۔**
یہ کیا چلاتا ہے، پچھلے 24 گھنٹوں اور اپنی پوری زندگی میں اس کی لاگت کیا ہے،
آخری بار کب دیکھا گیا، اس کا مالک کون ہے، اور کیا کوئی سبسکرپشن بل کا احاطہ
کر رہی ہے۔ یہاں 14 ایجنٹس، 3 سیشنز کام کر رہے ہیں، 13 خاموش۔

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**یہ دکھاتا ہے کہ ایک ٹرن کا وقت اور پیسہ کہاں گیا، ٹول بہ ٹول۔**
ایک حقیقی سیشن کا ایک ٹرن: 11 ٹولز، 11.2 منٹ میں، $1.16 کے عوض۔ ہر Bash
کال اور ماڈل کال کو ٹائم لائن پر اپنا بار ملتا ہے، تاکہ وہ کمانڈ جو 4.1
منٹ چلی اور وہ جو 226ms چلی، ایک نظر میں پہچانی جا سکیں۔

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**یہ کام کو گریڈ دیتا ہے، نہ کہ صرف خرچ کو۔**
اس ہفتے ایک A: 54 کام صاف طور پر مکمل ہوئے، 2 مشکل کاموں کی قیمت $48.57
رہی، اور جن رنز میں فیصلہ کرنے کے لیے کافی سرگرمی نہیں تھی انہیں جیت شمار
کرنے کے بجائے گریڈ سے باہر رکھا گیا ہے۔ ہر مشکل رن اپنے ٹریس سے منسلک ہے۔

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**یہ دکھاتا ہے کہ کانٹیکسٹ ونڈو کیوں بھرتی رہتی ہے۔**
تازہ ترین ٹرن پر 1M ٹوکن ونڈو میں سے 715K، 83.3% کی چوٹی، 4 کمپیکشنز
جو سب اوورفلو کے بجائے فعال طور پر چلیں، اور اس کے پیچھے ہر ٹرن کا استعمال۔

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**شناخت آپ کے کچھ بھی کنفیگر کیے بغیر چلتی ہے۔**
بلٹ ان ڈیٹیکٹرز انسٹال سے ہی آن ہیں: ایجنٹ خاموش ہو گیا، ٹیلی میٹری فیڈ
رک گئی، لاگت میں اضافہ، ٹوکن برسٹ، بڑھتی خرابیاں، ایرر اسپائیک، بجٹ حد،
خطرے کا دستخط ملا، سیکیورٹی ٹول کی تلاش، سیکیورٹی پوزیشن میں تبدیلی۔
آپ کے اپنے قواعد اوپر سے اختیاری ہیں۔

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**خطرناک کال کو روکنا آپٹ اِن ہے، اور بند حالت میں شپ ہوتا ہے۔**
ری کرسِو ڈیلیٹس، فورس پُشز، sudo، رازداری، پیکیج انسٹالز اور آؤٹ باؤنڈ کالز
میں سے ہر ایک کو ایک قاعدہ ملتا ہے جسے آپ آن کر سکتے ہیں۔ جب تک آپ ایسا
نہیں کرتے، ClawMetry دیکھتا رہتا ہے اور کچھ نہیں بدلتا۔ ایک بار آن ہونے کے
بعد، مماثل کالز یہاں (یا آپ کے فون پر) منظوری یا انکار کے لیے انتظار کرتی ہیں۔

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

مزید، فی رن ٹائم: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)۔

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## لائسنس

MIT · [@vivekchand](https://github.com/vivekchand) کی جانب سے تیار کردہ · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
