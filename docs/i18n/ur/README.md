<!-- i18n-src:c99ac0512cae -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ایک ایجنٹ ترقی کیے بغیر سو ٹول کالز کر سکتا ہے۔** ClawMetry
آپ کے کوڈنگ ایجنٹس کی طرف سے پہلے سے لکھی گئی سیشن فائلوں کو پڑھتا ہے، اور ٹائم لائن،
ٹول کالز، اور رن ٹائم کی طرف سے ظاہر کیے گئے ٹوکن اور لاگت کے ڈیٹا کو ایک
منظر میں رکھتا ہے — تاکہ آپ یہ بتا سکیں کہ کوئی طویل رن کام کر رہا ہے یا پھنس گیا ہے۔

**33 AI ایجنٹ رن ٹائمز** کے ساتھ کام کرتا ہے — Claude Code، OpenAI Codex، Hermes، OpenClaw اور 29 مزید۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ڈیش بورڈ۔ ([مکمل فہرست](SUPPORTED_RUNTIMES.txt)، کیٹلاگ سے تیار کی گئی۔)

> 🌐 **اسے اس زبان میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ کوئی ترتیب نہیں۔ ہر چیز خود بخود معلوم کر لیتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے۔ کوئی ترتیب درکار نہیں: یہ ان ایجنٹ رن ٹائمز کو تلاش کرتا ہے
جو آپ کے پاس پہلے سے موجود ہیں، انہیں صرف پڑھنے کے انداز میں پڑھتا ہے، اور ان کے چلنے کے طریقے میں کچھ تبدیل نہیں کرتا۔

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## انسٹال کرنے سے پہلے

| | |
|---|---|
| **یہ کیا کرتا ہے** | آپ کے ایجنٹس کی طرف سے پہلے سے لکھی گئی سیشن فائلوں اور لاگز کو پڑھتا ہے۔ کوئی SDK نہیں، کوڈ میں کوئی تبدیلی نہیں، آپ کی ایپ میں کوئی انسٹرومینٹیشن نہیں۔ |
| **آپ کیا دیکھتے ہیں** | سیشن ٹائم لائن، ٹول بہ ٹول ری پلے، ٹوکن اور لاگت کی تفصیل، اور ٹریجیکٹری سگنلز (لوپنگ، دہرائی جانے والی ناکامیاں) — ہر رن ٹائم کے لیے۔ |
| **کیا مفت ہے** | `pip install clawmetry` بغیر کسی اکاؤنٹ، کسی کلید، یا نیٹ ورک کال کے **OpenClaw، NVIDIA NemoClaw، Goose اور Qwen Code** کو پڑھتا ہے۔ باقی 28 — Claude Code، Codex، Cursor اور باقی سب — کو بند-سورس `clawmetry-pro` کمپینین پڑھتا ہے، جو 7 دن کے ٹرائل یا کسی پلان کے ساتھ آتا ہے — عین تقسیم کے لیے [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) دیکھیں۔ |
| **شروع کیسے کریں** | `pip install clawmetry && clawmetry`، پھر localhost:8900 کھولیں۔ اس مشین پر ابھی کوئی ایجنٹ نہیں؟ `clawmetry --sample` تین لیبل دار مصنوعی سیشنز کے ساتھ کھلتا ہے۔ |
| **آپ کی مشین سے کیا باہر جاتا ہے** | کوئی سیشن ڈیٹا نہیں، جب تک آپ `clawmetry connect` نہ چلائیں۔ بطور ڈیفالٹ دو چیزیں چلتی ہیں، دونوں آپٹ-آؤٹ اور کوئی بھی سیشن مواد نہیں لے جاتی: ایک گمنام انسٹال پنگ اور ایک PyPI ورژن چیک۔ ہر منزل [docs/EGRESS.md](docs/EGRESS.md) میں درج ہے، جو تبصروں کو پڑھنے کے بجائے وائر کیپچر سے دوبارہ تیار کی گئی ہے۔ |

دو حدود جو نتائج کا فیصلہ کرنے سے پہلے جاننا ضروری ہیں: رن ٹائمز بہت
مختلف ڈیٹا ظاہر کرتے ہیں (کچھ بالکل کوئی لاگت شائع نہیں کرتے — [میٹرکس](docs/compatibility.md)
بتاتا ہے کہ کون سا، ہر رن ٹائم کے لیے)، اور کسی عمل کا مشاہدہ کرنا اسے روکنے کی صلاحیت
جیسا نہیں ہے ([کون سے کنٹرولز حقیقی ہیں، ہر رن ٹائم کے لیے](docs/APPROVALS.md))۔


## 33 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

**اوپن سورس ایپ میں مفت:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**ایک پیڈ پلان پر:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ہر رن ٹائم کو ایک ہی ڈیش بورڈ ملتا ہے۔ کئی کو ایک ساتھ چلائیں اور ہیڈر
سوئچر ہر ٹیب کو ان میں سے ایک کے مطابق دوبارہ متعین کر دیتا ہے۔

کیا آپ نے SDK پر اپنا خود کا ایجنٹ بنایا ہے؟ انٹرسیپٹر اس کی LLM کالز بھی
ٹریک کرتا ہے۔ دیکھیں [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)۔

## آپ کو کیا ملتا ہے

- **سیشنز اور ٹرانسکرپٹس**: ہر ایجنٹ نے کیا کیا، موڑ بہ موڑ، ری پلے کے ساتھ
- **لاگت اور ٹوکنز**: ہر رن ٹائم، ماڈل، سیشن اور دن کے لیے، بے قاعدگی کی نشاندہی کے ساتھ
- **فلو**: چینلز، ماڈلز اور ٹولز سے گزرنے والے پیغامات کا لائیو ڈایا گرام
- **برین**: استدلال اور ٹول کال ایونٹ سٹریم جیسے وہ وقوع پذیر ہوتا ہے
- **کانٹیکسٹ بلو آؤٹ**: فراہم کنندہ کے لحاظ سے ونڈو کا استعمال، کمپیکشن بمقابلہ زبردستی اوورفلو، نیز ہر رن ٹائم کا ایک نقشہ جو ظاہر کرتا ہے کہ ہم *کیا نہیں* دیکھ سکتے ([کیسے](docs/CONTEXT_BLOWOUT.md))
- **میموری اور سکلز**: فائلیں اور سکلز جو ہر رن ٹائم نے دراصل لوڈ کیے
- **صحت اور لاگز**: ڈسک، میموری، ایرر ریٹس، ریٹ لمٹس، لائیو لاگ سٹریم
- **الرٹس**: بجٹ کیپس، ایرر اسپائکس، ایجنٹ-آف لائن، جو Slack، Discord، PagerDuty، Telegram، ای میل کو روٹ کیے جاتے ہیں
- **اپروولز**: چلنے سے *پہلے* خطرناک ٹول کالز کو روکیں اور اپنے فون سے منظور کریں ([کیسے](docs/APPROVALS.md))

## کانٹیکسٹ بلو آؤٹ، اور مانیٹرنگ کی قیمت

دو سوالات جن کا جواب کسی بھی ایجنٹ موازنہ ٹول پر بھروسہ کرنے سے پہلے دینا ضروری ہے۔

**یہ رن ٹائمز کے درمیان کانٹیکسٹ-ونڈو بلو آؤٹ کو کیسے سنبھالتا ہے؟**

یوٹیلائزیشن فیصد صرف اتنا ہی سچا ہے جتنا وہ چیز جس سے اسے تقسیم کیا جاتا ہے۔ ClawMetry
ہر فراہم کنندہ کے لیے ونڈو کا سائز [ایک ٹیبل](clawmetry/context_windows.py) سے لیتا ہے جسے آپ پڑھ اور
PR کر سکتے ہیں، جو Anthropic، OpenAI، Google، xAI،
DeepSeek، Kimi، Qwen، Mistral، Llama اور GLM کا احاطہ کرتا ہے۔ یہ تمام 33
رن ٹائمز کو ایک فراہم کنندہ کے پیمانے سے نہیں ناپتا۔ یہ اہم ہے: ایک 300K GPT-5 موڑ
جب Anthropic کے 200K کے خلاف ناپا جائے تو ">100%، اڑ گیا" پڑھتا ہے جب درحقیقت وہ
GPT-5 کے 400K کا 75% ہے۔ وہی پیمانہ ایک حقیقتاً اوورفلو ہوئے 130K DeepSeek موڑ کو
ایک آرام دہ 65% کے طور پر چھپا دیتا ہے۔

ہر ونڈو اپنی اصلیت کے ساتھ آتی ہے: `model_table`، `explicit_marker`،
`observed_floor`، یا جب ہم ماڈل نہیں جانتے تو ایک دیانتدار `default`۔ اندازے پر
بنایا گیا گیج کبھی اس اختیار کے ساتھ رینڈر نہیں ہوتا جو ایک لک اپ پر بنا ہو۔

ClawMetry صرف کچھ رن ٹائمز پر کمپیکشن ایونٹس دیکھ سکتا ہے۔ تو
`GET /api/context-coverage` ہر رن ٹائم کے لیے رپورٹ کرتا ہے کہ کیا **صفر کا مطلب
"صاف چلا" ہے یا "ہم اندھے ہیں"**۔ ایک `0` جس کا واقعی مطلب اندھا ہونا ہے وہ یہ بتاتا ہے۔
[مکمل تفصیل](docs/CONTEXT_BLOWOUT.md)

**انسٹرومینٹیشن کی قیمت کیا ہے؟**

| راستہ | آپ کے ایجنٹ میں شامل | ڈیفالٹ؟ |
|---|---|---|
| سیشن-فائل ٹیلنگ (تمام 33 رن ٹائمز) | **0**۔ علیحدہ پراسیس، آپ کے ایجنٹ میں کوئی ClawMetry کوڈ نہیں | آن |
| HTTP انٹرسیپٹر (`CLAWMETRY_INTERCEPT=1`) | ہر LLM کال پر **+0.44 ms**، یا 5s کال کا 0.009% | آف |
| پری-ٹول ہک گیٹ (گرم کیش) | ہر گیٹڈ ٹول کال پر **+44 ms**، 36 ms انٹرپریٹر فلور کے اوپر | آف |
| اینفورسمنٹ پراکسی | ہر LLM کال پر **+9.7 ms** | آف |

ڈیمن ہوسٹ قیمت: **2,762 ایونٹس/سیکنڈ** انجیسٹ، ڈسک پر **710 بائٹس/ایونٹ**
(100k ایونٹس پر 67.7 MB)، اور ایک مصروف انسٹال پر مستقل طور پر **ایک کور کا تقریباً 12%**۔
یہ آخری نمبر ہمارے اپنے بیان کردہ 5-10% بجٹ سے زیادہ ہے، تو اسے صفحہ سے چھوڑنے
کے بجائے ایک ایسے بگ کے طور پر شائع کیا گیا ہے جس کا تعاقب کرنا ہے۔

Apple M2 Pro پر `benchmarks/overhead.py` کے ساتھ ناپا گیا۔ ہارنس
ہر حالت کو علیحدہ پراسیس میں چلاتا ہے، ان کی ترتیب بدلتا ہے، اور **جب راؤنڈز
اس کی علامت پر متفق نہ ہوں تو نمبر پرنٹ کرنے سے انکار کرتا ہے**۔ اسے اپنی اپنی
مشین پر ایک منٹ میں چلائیں:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ہر راستہ ناپا جاتا ہے، بشمول ہک گیٹس اور اینفورسمنٹ پراکسی،
اور ہارنس CI میں Linux، macOS اور Windows پر چلتا ہے۔ جاننے کے قابل دو نتائج: پراکسی
Windows پر Linux کے مقابلے میں تقریباً سات گنا زیادہ قیمت لیتا ہے، اور
ڈیمن فی الحال ایک کور کا تقریباً 12% مستقل طور پر برداشت کرتا ہے، جو ہمارے اپنے 5-10%
بجٹ سے زیادہ ہے۔ خام JSON، طریقہ کار، اور جو کچھ ابھی تک ناپا نہیں گیا وہ
[docs/OVERHEAD.md](docs/OVERHEAD.md) میں ہے۔

## قیمتیں

| پلان | یہ کس کا احاطہ کرتا ہے | قیمت |
|---|---|---|
| **مفت** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code، مکمل ڈیش بورڈ، صرف مقامی | $0 |
| **اسٹارٹر** | اوپر بیان شدہ ہر دوسرا رن ٹائم، فلیٹ ویو، کلاؤڈ سنک | $9 فی نوڈ / مہینہ |
| **Pro** | اسٹارٹر + کنٹرول اور تجزیہ: اپروولز، ٹول-رسک پالیسیاں، ایولز، بے قاعدگی کی نشاندہی، کاسٹ آپٹیمائزر، OTel ایکسپورٹ، ٹیمپر-ایویڈنٹ آڈٹ لاگ | $19 فی نوڈ / مہینہ |

سالانہ پلانز، انٹرپرائز اور موجودہ نمبرز
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** پر موجود ہیں۔ سیلف-ہوسٹڈ لائسنس
کیز کلاؤڈ کے بغیر کام کرتی ہیں (`clawmetry license`)۔ عین مفت/پیڈ تقسیم
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) میں ہے۔

## آپ کا ڈیٹا آپ کی مشین پر رہتا ہے

ClawMetry مقامی سیشن فائلیں اور لاگز پڑھتا ہے۔ **کوئی سیشن ڈیٹا آپ کے باکس سے باہر نہیں جاتا
جب تک آپ `clawmetry connect` نہ چلائیں** — کوئی پرامپٹس، جوابات، ٹول آرگیومنٹس، فائل
مواد یا لاگ لائنز نہیں۔ جب آپ کنیکٹ کرتے ہیں، تو سنیپ شاٹ ایسی کلید کے ساتھ اینڈ-ٹو-اینڈ
انکرپٹڈ ہوتا ہے جو کبھی آپ کی مشین سے باہر نہیں جاتی، اور آپ کے براؤزر میں ڈکرپٹ ہوتا ہے۔ اگر کسی
نوڈ کے پاس کوئی کلید نہیں، تو اپ لوڈ بغیر انکرپشن بھیجے جانے کے بجائے چھوڑ دیا جاتا ہے، اور
کوئی سرور جواب اسے بند نہیں کر سکتا۔

دو چیزیں آپ کے کنیکٹ کرنے سے پہلے بطور ڈیفالٹ چلتی ہیں، دونوں آپٹ-آؤٹ اور کوئی بھی
سیشن ڈیٹا نہیں لے جاتیں: ایک گمنام انسٹال پنگ اور PyPI کے خلاف ایک ورژن چیک۔ ایک
ڈیفالٹ انسٹال اسٹارٹ اپ بینر لائن کے لیے آپ کا پبلک IP بھی ایک بار دیکھتا ہے۔ ہر منزل، وہ کیا
لے جاتی ہے اور اسے کیسے بند کیا جائے
[docs/EGRESS.md](docs/EGRESS.md) میں درج ہے؛ سیلف-ہوسٹڈ، دوبارہ پوائنٹ شدہ اور ایئر-گیپڈ انسٹالیشنز
کوئی اختیاری آؤٹ باؤنڈ کالز بالکل نہیں کرتیں۔

ڈکرپشن آپ کے براؤزر میں، ہمارے فراہم کردہ کوڈ میں ہوتا ہے۔ یہ پہلے
ایک وعدہ تھا؛ اب یہ کچھ ایسا ہے جسے آپ چیک کر سکتے ہیں۔ ہر لائن جو آپ کی کلید کو چھوتی ہے
ایک پڑھنے کے قابل فائل میں رہتی ہے، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
جو وہیل کے اندر شپ ہوتی ہے اور لفظ بہ لفظ سرو کی جاتی ہے، جو ایک Subresource
Integrity ہیش کے ساتھ پن کی گئی ہے۔ یہ تصدیق کرنے کے لیے کہ براؤزر وہی چلاتا ہے جو ہم نے شائع کیا:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

یہ کیا ثابت نہیں کرتا: ہم وہ صفحہ سرو کرتے ہیں جو فائل لوڈ کرتا ہے، تو ہم
ایک مختلف صفحہ سرو کر سکتے تھے۔ انٹیگریٹی ہیشز آپ کو ایک سمجھوتہ شدہ CDN سے بچاتی ہیں،
فروخت کنندہ سے نہیں۔ آپ کو جو حاصل ہوتا ہے وہ یہ ہے کہ کوئی بھی تبدیلی جان بوجھ کر، صفحہ
کے سورس میں نظر آنے والی، اور PyPI پر موجود ایک آرٹی فیکٹ سے مختلف ہونی چاہیے جسے کوئی بھی
حاصل کر سکتا ہے۔ سیلف-ہوسٹنگ یا صرف مقامی رہنا اس انحصار کو مکمل طور پر ختم کر دیتا ہے۔

## انسٹال کریں

```bash
pip install clawmetry     # پھر: clawmetry
```

یا ون-لائنر: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS، Linux یا Windows پر Python 3.8+ درکار ہے، اور اسی مشین پر کم از کم ایک ایجنٹ
رن ٹائم۔ Docker ہدایات: [docs/DOCKER.md](docs/DOCKER.md)۔

یا ایجنٹ کو خود اس کی ترتیب کرنے دیں۔ [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
سکل Claude Code، Codex، Cursor، Gemini CLI، Copilot یا OpenCode کو
ClawMetry انسٹال کرنا، مشین پر موجود ایجنٹس کیا کر رہے ہیں اور خرچ کر رہے ہیں وہ رپورٹ کرنا،
درخواست پر ایک سیشن روکنا، اور منظوری کے لیے خطرناک ٹول کالز روکنا سکھاتی ہے:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## دستاویزات

| | |
|---|---|
| [رن ٹائم موافقت](docs/compatibility.md) | ہر ایڈاپٹر کیا پڑھتا ہے، اور رن ٹائم کیسے شامل کریں |
| [کانٹیکسٹ بلو آؤٹ](docs/CONTEXT_BLOWOUT.md) | فراہم کنندہ کے لحاظ سے ونڈوز، کمپیکشن بمقابلہ اوورفلو، ہر رن ٹائم کوریج |
| [اووررہیڈ](docs/OVERHEAD.md) | انسٹرومینٹیشن کی قیمت کیا ہے، ناپی گئی، اسے دوبارہ پیدا کرنے کے ہارنس کے ساتھ |
| [انٹائٹلمنٹس](docs/ENTITLEMENTS.md) | مفت بمقابلہ پیڈ، ٹیئر میٹرکس، لائسنس CLI |
| [اپروولز اور پالیسیاں](docs/APPROVALS.md) | پری-ایگزیکیوشن گیٹنگ، رسک سکورنگ، فون اپروولز |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | کہیں بھی ٹریسز ایکسپورٹ کریں، کسی بھی چیز سے OTLP انجیسٹ کریں |
| [اپنا خود کا ایجنٹ لائیں](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، Pydantic AI، LangChain سرے سے سرے تک، چلانے کے قابل مثالوں کے ساتھ |
| [SDK ٹریکنگ](docs/SDK_TRACKING.md) | ان ایجنٹس کے لیے لاگت کی تخصیص جو آپ نے خود بنائے |
| [چیٹ چینلز](docs/CHANNELS.md) | فلو میں دکھائے گئے چیٹ ایڈاپٹرز |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | سینڈ باکسڈ NVIDIA NemoClaw سیٹ اپس |
| [Docker](docs/DOCKER.md) | امیج، کمپوز، والیوم ماؤنٹس |
| [آرکیٹیکچر](ARCHITECTURE.md) · [ڈیولپمنٹ](docs/DEVELOPMENT.md) | اندر یہ کیسے کام کرتا ہے؛ سورس سے چلانا |
| [ٹیلی میٹری](docs/TELEMETRY.md) | گمنام انسٹال اور ڈیسک ٹاپ-اوپن پنگز، اور انہیں کیسے بند کریں |

## اسکرین شاٹس

نیچے دیا گیا ہر نمبر ایک حقیقی مشین سے ہے، صرف پڑھنے کے انداز میں، بغیر کسی چیز کو بیج کیے۔

**یہ آپ کو بتاتا ہے کہ کب کچھ غلط ہے، نہ صرف کیا ہوا۔**
اوپر دو بے قاعدگی بینرز: خرچ روزانہ اوسط کا 7x چل رہا ہے، اور ایک
4.2x لاگت کا اضافہ۔ ان کے نیچے، حالیہ 667 سیشنز میں سے 324 میں ضیاع کا
سگنل موجود ہے، وجہ کے مطابق درجہ بند۔

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**یہ آپ کو دکھاتا ہے کہ پیسہ کہاں گیا، ہر ونڈو میں۔**
آج $252.47، اس ہفتے $513.15، اس مہینے $1,312.92، ہر ایک کے پیچھے کے ٹوکنز کے ساتھ
اور آپ کی سبسکرپشن اس میں سے کتنا پہلے ہی احاطہ کرتی ہے۔ اس کے نیچے، تقریباً
$1,128/مہینہ بازیافت کے قابل کے طور پر درجہ بند اور کیش کے دوبارہ استعمال سے پہلے ہی
بچائے گئے $17,256/مہینہ۔

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**یہ دکھاتا ہے کہ ایک پیغام جواب کیسے بنتا ہے۔**
لائیو فلو ڈایا گرام: آپ، وہ چینل جس پر یہ آیا، گیٹ وے، جو ماڈل
ابھی جواب دے رہا ہے، اور ہر ٹول جس کی طرف اس نے ہاتھ بڑھایا۔ جیسے جیسے کام
ان سے گزرتا ہے نوڈز روشن ہوتے ہیں۔

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**مشین پر ہر ایجنٹ، ایک ٹیبل میں۔**
یہ کیا چلاتا ہے، گزشتہ 24 گھنٹوں میں اور اپنی پوری زندگی میں اس کی قیمت کیا ہے، جب
یہ آخری بار دیکھا گیا، کس کی ملکیت ہے، اور کیا کوئی سبسکرپشن بل کا احاطہ کر رہی ہے۔ یہاں 14 ایجنٹس، 3 سیشنز کام کر رہے ہیں، 13 خاموش۔

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**یہ دکھاتا ہے کہ ایک موڑ کا وقت اور پیسہ کہاں گیا، ٹول بہ ٹول۔**
ایک حقیقی سیشن کا ایک موڑ: 11.2 منٹ میں $1.16 کے لیے 11 ٹولز۔ ہر Bash
کال اور ماڈل کال کو ٹائم لائن پر اپنا بار ملتا ہے، تو جو کمانڈ 4.1 منٹ تک چلی
اور جو 226ms تک چلی انہیں ایک نظر میں الگ بتایا جا سکتا ہے۔

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**یہ کام کو درجہ دیتا ہے، نہ صرف خرچ کو۔**
اس ہفتے ایک A: 54 ٹاسکس صاف واپس آئے، 2 ناہموار والوں کی قیمت $48.57 تھی، اور
وہ رنز جن میں فیصلہ کرنے کے لیے بہت کم سرگرمی تھی انہیں فتح کے طور پر شمار کرنے کے بجائے
درجہ بندی سے باہر رکھا گیا ہے۔ ہر ناہموار رن اپنے ٹریس سے منسلک ہے۔

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**یہ دکھاتا ہے کہ کانٹیکسٹ ونڈو کیوں بھرتی رہتی ہے۔**
تازہ ترین موڑ پر 1M-ٹوکن ونڈو میں سے 715K، 83.3% کی چوٹی، 4 کمپیکشنز
جو سب اوورفلو کے بجائے فعال طور پر فائر ہوئے، اور اس کے پیچھے ہر موڑ کا استعمال۔

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**آپ کی طرف سے کوئی ترتیب کیے بغیر تشخیص چلتی ہے۔**
بلٹ-اِن ڈیٹیکٹرز انسٹال سے ہی آن ہیں: ایجنٹ خاموش ہو گیا، ٹیلی میٹری فیڈ
رک گئی، لاگت میں اضافہ، ٹوکن برسٹ، بڑھتی ہوئی ایرر، ایرر اسپائک، بجٹ
حد، خطرے کا دستخط ملا، سیکیورٹی ٹول کی تلاش، سیکیورٹی پوزیشن
تبدیل ہوئی۔ آپ کے اپنے قواعد اوپر اختیاری ہیں۔

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**خطرناک کال روکنا آپٹ-ان ہے، اور بند حالت میں شپ ہوتا ہے۔**
ری کرسیو ڈیلیٹس، فورس پشز، sudo، سیکرٹس، پیکیج انسٹالز اور آؤٹ باؤنڈ
کالز میں سے ہر ایک کو ایک قاعدہ ملتا ہے جسے آپ آن کر سکتے ہیں۔ جب تک آپ ایسا نہیں کرتے، ClawMetry دیکھتا ہے
اور کچھ تبدیل نہیں کرتا۔ ایک بار آن ہونے پر، میچ ہونے والی کالز منظوری یا انکار کے لیے
یہاں (یا آپ کے فون پر) انتظار کرتی ہیں۔

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

مزید، ہر رن ٹائم کے لیے: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)۔

## پہچان

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## سٹار ہسٹری

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## لائسنس

MIT · [@vivekchand](https://github.com/vivekchand) کی طرف سے بنایا گیا · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
