<!-- i18n-src:a855a14295b0 -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ایک ایجنٹ بغیر کوئی پیش رفت کیے سینکڑوں ٹول کالز کر سکتا ہے۔** ClawMetry
آپ کے کوڈنگ ایجنٹس پہلے سے جو سیشن فائلیں لکھتے ہیں انہیں پڑھتا ہے، اور ٹائم لائن،
ٹول کالز اور رن ٹائم جو بھی ٹوکن اور لاگت کا ڈیٹا ظاہر کرتا ہے اسے ایک ہی
منظر میں پیش کرتا ہے — تاکہ آپ ایک لمبے رن جو کام کر رہا ہے اور ایک جو اٹک گیا ہے، کے درمیان فرق بتا سکیں۔

**32 AI ایجنٹ رن ٹائمز** کے ساتھ کام کرتا ہے — Claude Code، OpenAI Codex، Hermes، OpenClaw اور 28 مزید۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ڈیش بورڈ۔ ([مکمل فہرست](SUPPORTED_RUNTIMES.txt)، کیٹلاگ سے تیار کردہ۔)

> 🌐 **اسے اس زبان میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید ←](docs/i18n/)

ایک کمانڈ۔ صفر کنفیگریشن۔ سب کچھ خودکار طور پر شناخت کرتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے۔ صفر کنفیگریشن: یہ ان ایجنٹ رن ٹائمز کو ڈھونڈتا ہے
جو آپ کے پاس پہلے سے موجود ہیں، انہیں صرف پڑھنے کی حد تک پڑھتا ہے، اور یہ کہ وہ کیسے چلتے ہیں اس میں کچھ نہیں بدلتا۔

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## انسٹال کرنے سے پہلے

| | |
|---|---|
| **یہ کیا کرتا ہے** | ان سیشن فائلوں اور لاگز کو پڑھتا ہے جو آپ کے ایجنٹس پہلے سے لکھتے ہیں۔ کوئی SDK نہیں، کوڈ میں کوئی تبدیلی نہیں، آپ کی ایپ میں کوئی انسٹرومینٹیشن نہیں۔ |
| **آپ کیا دیکھتے ہیں** | سیشن ٹائم لائن، ٹول بہ ٹول ریپلے، ٹوکن اور لاگت کی تفصیل، اور trajectory سگنلز (لوپنگ، بار بار ناکامی) — ہر رن ٹائم کے لیے علیحدہ۔ |
| **مفت کیا ہے** | `pip install clawmetry` کسی اکاؤنٹ، کسی کلید اور کسی نیٹ ورک کال کے بغیر **OpenClaw، NVIDIA NemoClaw اور Goose** کو پڑھتا ہے۔ باقی 27 — Claude Code، Codex، Cursor اور دیگر — کو کلوزڈ سورس `clawmetry-pro` ساتھی پڑھتا ہے، جو 7 دن کے ٹرائل یا کسی پلان کے ساتھ آتا ہے — عین تقسیم کے لیے [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) دیکھیں۔ |
| **شروع کیسے کریں** | `pip install clawmetry && clawmetry`، پھر localhost:8900 کھولیں۔ اس مشین پر ابھی تک کوئی ایجنٹ نہیں؟ `clawmetry --sample` تین لیبل شدہ مصنوعی سیشنز پر کھلتا ہے۔ |
| **آپ کی مشین سے کیا باہر جاتا ہے** | کوئی سیشن ڈیٹا نہیں، جب تک آپ `clawmetry connect` نہ چلائیں۔ دو چیزیں بطور ڈیفالٹ چلتی ہیں، دونوں opt-out ہیں اور کوئی بھی سیشن مواد نہیں لے جاتیں: ایک گمنام انسٹال پنگ اور ایک PyPI ورژن چیک۔ ہر منزل [docs/EGRESS.md](docs/EGRESS.md) میں درج ہے، جو تبصروں کو پڑھنے کے بجائے وائر کیپچر سے دوبارہ تیار کیا گیا ہے۔ |

آؤٹ پُٹ کا فیصلہ کرنے سے پہلے دو حدیں جاننا ضروری ہیں: رن ٹائمز بہت
مختلف ڈیٹا ظاہر کرتے ہیں (کچھ بالکل کوئی لاگت شائع نہیں کرتے — [میٹرکس](docs/compatibility.md)
بتاتا ہے کہ کون سا، ہر رن ٹائم کے لیے)، اور کسی عمل کا مشاہدہ کرنا اسے
روکنے کے قابل ہونے جیسا نہیں ہے ([کون سے کنٹرولز حقیقی ہیں، ہر رن ٹائم کے لیے](docs/APPROVALS.md))۔


## 32 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

**اوپن سورس ایپ میں مفت:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ادا شدہ پلان پر:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ہر رن ٹائم کو ایک جیسا ڈیش بورڈ ملتا ہے۔ ایک ساتھ کئی چلائیں اور
ہیڈر سوئچر ہر ٹیب کو ان میں سے کسی ایک پر دوبارہ فوکس کر دیتا ہے۔

کیا آپ نے SDK پر اپنا ایجنٹ خود بنایا ہے؟ انٹرسیپٹر اس کی LLM کالز کو بھی
ٹریک کرتا ہے۔ دیکھیں [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)۔

## آپ کو کیا ملتا ہے

- **سیشنز اور ٹرانسکرپٹس**: ہر ایجنٹ نے کیا کیا، باری بہ باری، ریپلے کے ساتھ
- **لاگت اور ٹوکنز**: ہر رن ٹائم، ماڈل، سیشن اور دن کے لحاظ سے، بے قاعدگی کے نشانات کے ساتھ
- **فلو**: چینلز، ماڈلز اور ٹولز سے گزرنے والے پیغامات کا لائیو ڈایاگرام
- **برین**: استدلال اور ٹول کال کا واقعاتی اسٹریم جیسا کہ یہ ہو رہا ہے
- **کانٹیکسٹ بلو آؤٹ**: فراہم کنندہ کے لحاظ سے ونڈو کا استعمال، compaction بمقابلہ زبردستی اوورفلو، نیز فی رن ٹائم نقشہ کہ ہم کیا *نہیں* دیکھ سکتے ([کیسے](docs/CONTEXT_BLOWOUT.md))
- **میموری اور اسکلز**: وہ فائلیں اور اسکلز جو ہر رن ٹائم نے حقیقتاً لوڈ کیں
- **صحت اور لاگز**: ڈسک، میموری، ایرر ریٹس، ریٹ لمٹس، لائیو لاگ اسٹریم
- **الرٹس**: بجٹ کی حدیں، ایرر اسپائیکس، ایجنٹ-آف لائن، Slack، Discord، PagerDuty، Telegram، Email پر بھیجے گئے
- **منظوریاں**: خطرناک ٹول کالز کو چلنے *سے پہلے* روکیں اور اپنے فون سے منظور کریں ([کیسے](docs/APPROVALS.md))

## کانٹیکسٹ بلو آؤٹ، اور نگرانی کی قیمت

دو سوالات جن کا جواب دینا کسی بھی ایجنٹ موازنہ کرنے والے ٹول پر بھروسہ کرنے سے پہلے قابلِ قدر ہے۔

**یہ رن ٹائمز میں کانٹیکسٹ ونڈو بلو آؤٹ کو کیسے سنبھالتا ہے؟**

استعمال کی فیصد صرف اتنی ہی ایماندار ہوتی ہے جتنی وہ چیز جس سے اسے تقسیم کیا جاتا ہے۔ ClawMetry
ونڈو کا سائز فی فراہم کنندہ [ایک ٹیبل سے طے کرتا ہے جسے آپ پڑھ اور
PR کر سکتے ہیں](clawmetry/context_windows.py)، جو Anthropic، OpenAI، Google، xAI،
DeepSeek، Kimi، Qwen، Mistral، Llama اور GLM کا احاطہ کرتا ہے۔ یہ تمام 32
رن ٹائمز کو ایک ہی فراہم کنندہ کے پیمانے سے نہیں ناپتا۔ یہ اہم ہے: ایک 300K GPT-5 باری
جسے Anthropic کے 200K کے خلاف ناپا جائے وہ ">100%، اڑ گیا" پڑھتا ہے جبکہ حقیقت میں یہ
GPT-5 کے 400K کا 75% ہے۔ وہی پیمانہ ایک حقیقتاً اوورفلو ہو چکی 130K DeepSeek باری کو
ایک آرام دہ 65% کے طور پر چھپا دیتا ہے۔

ہر ونڈو اپنی سند کے ساتھ آتی ہے: `model_table`، `explicit_marker`،
`observed_floor`، یا جب ہمیں ماڈل معلوم نہ ہو تو ایک ایماندار `default`۔ ایک
اندازے پر بنایا گیا گیج کبھی بھی اتنی ہی اتھارٹی کے ساتھ ظاہر نہیں ہوتا
جتنا کہ کسی lookup پر بنایا گیا۔

ClawMetry صرف کچھ رن ٹائمز پر compaction واقعات دیکھ سکتا ہے۔ اس لیے
`GET /api/context-coverage` ہر رن ٹائم کے لیے یہ رپورٹ کرتا ہے کہ آیا **صفر کا مطلب
"صاف چلا" ہے یا "ہم اندھے ہیں"**۔ ایک `0` جس کا حقیقتاً مطلب اندھا پن ہو وہ ایسا ہی
کہتا ہے۔ [مکمل تفصیل](docs/CONTEXT_BLOWOUT.md)

**انسٹرومینٹیشن کی قیمت کیا ہے؟**

| راستہ | آپ کے ایجنٹ میں شامل | ڈیفالٹ؟ |
|---|---|---|
| سیشن فائل ٹیلنگ (تمام 32 رن ٹائمز) | **0**۔ علیحدہ عمل، آپ کے ایجنٹ میں کوئی ClawMetry کوڈ نہیں | آن |
| HTTP انٹرسیپٹر (`CLAWMETRY_INTERCEPT=1`) | فی LLM کال **+0.44 ملی سیکنڈ**، یا 5 سیکنڈ کی کال کا 0.009% | آف |
| Pre-tool hook گیٹ (گرم کیش) | فی gated ٹول کال **+44 ملی سیکنڈ**، 36 ملی سیکنڈ کے انٹرپریٹر فرش کے اوپر | آف |
| Enforcement پراکسی | فی LLM کال **+9.7 ملی سیکنڈ** | آف |

Daemon میزبان لاگت: **2,762 واقعات/سیکنڈ** ingest، **710 بائٹس/واقعہ** ڈسک پر
(67.7 MB فی 100k واقعات)، اور مصروف انسٹال پر مسلسل **~12% ایک کور کا**۔ یہ آخری
عدد ہمارے اپنے اعلان کردہ 5-10% بجٹ سے زیادہ ہے، اس لیے اسے صفحے سے ہٹانے کے بجائے
پیچھا کرنے والے bug کے طور پر شائع کیا گیا ہے۔

Apple M2 Pro پر `benchmarks/overhead.py` کے ساتھ ناپا گیا۔ ہارنیس ہر
حالت کو ایک علیحدہ عمل میں چلاتا ہے، ان کی ترتیب بدلتا رہتا ہے، اور جب راؤنڈز
اس کی علامت پر متفق نہیں ہوتے تو **کوئی عدد چھاپنے سے انکار کرتا ہے**۔ اسے اپنی
مشین پر ایک منٹ میں چلائیں:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ہر راستہ ناپا جاتا ہے، بشمول hook گیٹس اور enforcement پراکسی،
اور ہارنیس CI میں Linux، macOS اور Windows پر چلتا ہے۔ جاننے کے قابل دو نتائج:
پراکسی کی قیمت Windows پر Linux کے مقابلے میں تقریباً سات گنا زیادہ ہے، اور
daemon فی الحال ایک کور کا تقریباً 12% مسلسل برداشت کرتا ہے، جو ہمارے اپنے 5-10%
بجٹ سے زیادہ ہے۔ خام JSON، طریقہ کار، اور جو ابھی تک ناپا نہیں گیا وہ
[docs/OVERHEAD.md](docs/OVERHEAD.md) میں موجود ہے۔

## قیمت

| پلان | یہ کیا احاطہ کرتا ہے | قیمت |
|---|---|---|
| **مفت** | OpenClaw + NVIDIA NemoClaw + Goose، مکمل ڈیش بورڈ، صرف مقامی | $0 |
| **Starter** | مندرجہ بالا ہر دوسرا رن ٹائم، فلیٹ ویو، cloud sync | $9 فی نوڈ / ماہ |
| **Pro** | Starter + کنٹرول اور تشخیص: منظوریاں، ٹول-رسک پالیسیاں، evals، بے قاعدگی کی شناخت، لاگت آپٹیمائزر، OTel ایکسپورٹ، چھیڑ چھاڑ سے محفوظ آڈٹ لاگ | $19 فی نوڈ / ماہ |

سالانہ پلانز، Enterprise اور موجودہ نمبرز
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** پر موجود ہیں۔ سیلف ہوسٹڈ لائسنس
کیز بغیر cloud کے کام کرتی ہیں (`clawmetry license`)۔ عین مفت/ادا شدہ تقسیم
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) میں ہے۔

## آپ کا ڈیٹا آپ کی مشین پر رہتا ہے

ClawMetry مقامی سیشن فائلیں اور لاگز پڑھتا ہے۔ **کوئی سیشن ڈیٹا آپ کے باکس سے باہر نہیں جاتا
جب تک آپ `clawmetry connect` نہ چلائیں** — کوئی پرامپٹس، جوابات، ٹول دلائل، فائل
مواد یا لاگ لائنیں نہیں۔ جب آپ کنیکٹ کرتے ہیں، snapshot اینڈ-ٹو-اینڈ انکرپٹڈ ہوتا ہے
ایک ایسی کلید کے ساتھ جو کبھی آپ کی مشین سے باہر نہیں جاتی، اور آپ کے براؤزر میں ڈکرپٹ ہوتی ہے۔ اگر کسی
نوڈ کے پاس کوئی کلید نہیں ہے، تو اپلوڈ سادہ حالت میں بھیجے جانے کے بجائے چھوڑ دیا جاتا ہے، اور کوئی
سرور جواب اسے بند نہیں کر سکتا۔

دو چیزیں کنیکٹ کرنے سے پہلے بطور ڈیفالٹ چلتی ہیں، دونوں opt-out اور کوئی بھی سیشن ڈیٹا
نہیں لے جاتیں: ایک گمنام انسٹال پنگ اور PyPI کے خلاف ایک ورژن چیک۔ ایک ڈیفالٹ انسٹال آپ کے
پبلک IP کو بھی ایک بار startup بینر لائن کے لیے تلاش کرتا ہے۔ ہر منزل، وہ کیا لے جاتی ہے اور اسے کیسے بند کیا جائے
[docs/EGRESS.md](docs/EGRESS.md) میں درج ہے؛ سیلف ہوسٹڈ، ری پوائنٹڈ اور ایئر-گیپڈ انسٹالز
کوئی بھی صوابدیدی آؤٹ باؤنڈ کالز نہیں کرتیں۔

ڈکرپشن آپ کے براؤزر میں، ہمارے دیے گئے کوڈ میں ہوتا ہے۔ یہ پہلے
ایک وعدہ تھا؛ اب یہ کچھ ایسا ہے جسے آپ چیک کر سکتے ہیں۔ ہر لائن جو آپ کی کلید کو چھوتی ہے
ایک قابلِ پڑھ فائل میں رہتی ہے، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
جو wheel کے اندر شپ ہوتی ہے اور من و عن پیش کی جاتی ہے، ایک Subresource
Integrity ہیش کے ساتھ pinned۔ یہ تصدیق کرنے کے لیے کہ براؤزر وہی چلاتا ہے جو ہم نے شائع کیا ہے:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

یہ کیا ثابت نہیں کرتا: ہم وہ صفحہ پیش کرتے ہیں جو فائل لوڈ کرتا ہے، اس لیے ہم
ایک مختلف صفحہ پیش کر سکتے تھے۔ Integrity ہیشز آپ کو ایک compromised CDN سے
بچاتی ہیں، وینڈر سے نہیں۔ آپ کو جو حاصل ہوتا ہے وہ یہ ہے کہ کوئی بھی تبدیلی جان بوجھ کر،
صفحے کے سورس میں نظر آنے والی، اور PyPI پر موجود artifact سے مختلف ہونی چاہیے
جسے کوئی بھی حاصل کر سکتا ہے۔ سیلف ہوسٹنگ یا صرف مقامی رہنا اس انحصار کو
مکمل طور پر ختم کر دیتا ہے۔

## انسٹال

```bash
pip install clawmetry     # پھر: clawmetry
```

یا ون-لائنر: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS، Linux یا Windows پر Python 3.8+ اور اسی مشین پر کم از کم ایک ایجنٹ
رن ٹائم درکار ہے۔ Docker ہدایات: [docs/DOCKER.md](docs/DOCKER.md)۔

یا ایجنٹ کو آپ کے لیے سیٹ اپ کرنے دیں۔ [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
اسکل Claude Code، Codex، Cursor، Gemini CLI، Copilot یا OpenCode کو
ClawMetry انسٹال کرنا، مشین پر موجود ایجنٹس کیا کر رہے ہیں اور کیا خرچ کر رہے ہیں اس کی رپورٹ کرنا،
درخواست پر ایک سیشن روکنا، اور خطرناک ٹول کالز کو منظوری کے لیے روک کر رکھنا سکھاتی ہے:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## دستاویزات

| | |
|---|---|
| [رن ٹائم مطابقت](docs/compatibility.md) | ہر adapter کیا پڑھتا ہے، اور رن ٹائم کیسے شامل کیا جائے |
| [کانٹیکسٹ بلو آؤٹ](docs/CONTEXT_BLOWOUT.md) | فی فراہم کنندہ ونڈوز، compaction بمقابلہ overflow، فی رن ٹائم coverage |
| [Overhead](docs/OVERHEAD.md) | انسٹرومینٹیشن کی قیمت کیا ہے، ناپی گئی، اور اسے دوبارہ پیدا کرنے کا ہارنیس |
| [Entitlements](docs/ENTITLEMENTS.md) | مفت بمقابلہ ادا شدہ، ٹئیر میٹرکس، license CLI |
| [منظوریاں اور پالیسیاں](docs/APPROVALS.md) | Pre-execution gating، رسک اسکورنگ، فون منظوریاں |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | کہیں بھی traces ایکسپورٹ کریں، کسی بھی چیز سے OTLP ingest کریں |
| [اپنا ایجنٹ لائیں](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، Pydantic AI، LangChain مکمل طور پر، چلانے کے قابل مثالوں کے ساتھ |
| [SDK ٹریکنگ](docs/SDK_TRACKING.md) | آپ کے خود بنائے ایجنٹس کے لیے لاگت کا انتساب |
| [چیٹ چینلز](docs/CHANNELS.md) | Flow میں دکھائے گئے چیٹ adapters |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw سیٹ اپس |
| [Docker](docs/DOCKER.md) | Image، compose، volume mounts |
| [آرکیٹیکچر](ARCHITECTURE.md) · [ڈیولپمنٹ](docs/DEVELOPMENT.md) | یہ اندر سے کیسے کام کرتا ہے؛ سورس سے چلانا |
| [ٹیلی میٹری](docs/TELEMETRY.md) | گمنام انسٹال اور desktop-open پنگز، اور انہیں کیسے بند کیا جائے |

## اسکرین شاٹس

نیچے دیا گیا ہر عدد ایک حقیقی مشین سے ہے، صرف پڑھنے کی حد تک، بغیر کچھ سیڈ کیے۔

**یہ آپ کو بتاتا ہے کہ کب کچھ غلط ہے، نہ صرف یہ کہ کیا ہوا۔**
اوپر دو anomaly بینرز: خرچ روزانہ اوسط سے 7 گنا چل رہا ہے، اور ایک
4.2 گنا لاگت کی اسپائیک۔ ان کے نیچے، حالیہ 667 سیشنز میں سے 324 میں فضلے کا
اشارہ موجود ہے، وجہ کے لحاظ سے تفصیل کے ساتھ۔

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**یہ آپ کو دکھاتا ہے کہ پیسہ کہاں گیا، ہر ونڈو میں۔**
آج $252.47، اس ہفتے $513.15، اس مہینے $1,312.92، ہر ایک اس کے پیچھے موجود
ٹوکنز کے ساتھ اور یہ کہ آپ کی سبسکرپشن پہلے سے کتنا احاطہ کرتی ہے۔ اس کے نیچے،
تقریباً $1,128/ماہ recoverable کے طور پر تفصیل سے اور پہلے ہی $17,256/ماہ
کیش reuse سے بچائے گئے۔

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**یہ کھینچتا ہے کہ ایک پیغام کیسے جواب بنتا ہے۔**
لائیو فلو ڈایاگرام: آپ، وہ چینل جس پر یہ پہنچا، gateway، ماڈل
جو ابھی جواب دے رہا ہے، اور ہر ٹول جس تک اس نے رسائی حاصل کی۔ Nodes روشن ہو جاتے ہیں جیسے کام
ان سے گزرتا ہے۔

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**مشین پر ہر ایجنٹ، ایک ٹیبل میں۔**
یہ کیا چلاتا ہے، پچھلے 24 گھنٹوں میں اور اپنی پوری زندگی میں اس کی لاگت کیا ہے، کب
یہ آخری بار دیکھا گیا، کس کا ہے، اور کیا کوئی سبسکرپشن بل کا احاطہ کر رہی ہے۔ یہاں 14 ایجنٹس،
3 سیشنز کام کر رہے ہیں، 13 خاموش۔

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**یہ دکھاتا ہے کہ ایک باری کا وقت اور پیسہ کہاں گیا، ٹول بہ ٹول۔**
ایک حقیقی سیشن کی ایک باری: $1.16 میں 11.2 منٹ میں 11 ٹولز۔ ہر Bash
کال اور ماڈل کال کو ٹائم لائن پر اپنی الگ بار ملتی ہے، تاکہ وہ کمانڈ جو
4.1 منٹ تک چلی اور وہ جو 226ms تک چلی، ایک نظر میں الگ پہچانی جا سکیں۔

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**یہ کام کو گریڈ دیتا ہے، صرف خرچ کو نہیں۔**
اس ہفتے ایک A: 54 کام صاف واپس آئے، 2 مشکل کاموں کی قیمت $48.57 رہی، اور
وہ رنز جن میں فیصلہ کرنے کے لیے بہت کم سرگرمی تھی انہیں جیت کے طور پر شمار کرنے کے بجائے
گریڈ سے باہر رکھا گیا۔ ہر مشکل رن اپنے trace سے لنک ہوتا ہے۔

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**یہ دکھاتا ہے کہ کانٹیکسٹ ونڈو کیوں بھرتی رہتی ہے۔**
تازہ ترین باری میں 1M-ٹوکن ونڈو میں سے 715K، 83.3% کی چوٹی، 4 compactions
جو سب پرو-ایکٹیو طور پر چلیں نہ کہ کسی overflow پر، نیز اس کے پیچھے ہر باری کا استعمال۔

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**شناخت آپ کے کچھ بھی کنفیگر کیے بغیر چلتی ہے۔**
built-in ڈیٹیکٹرز انسٹال سے ہی آن ہیں: ایجنٹ خاموش ہو گیا، ٹیلی میٹری فیڈ
رک گئی، لاگت کی اسپائیک، ٹوکن برسٹ، بڑھتے ایررز، ایرر اسپائیک، بجٹ
حد، خطرے کا نشان ملا، سیکیورٹی ٹول کی تلاش، سیکیورٹی پوزیشن
تبدیل ہوئی۔ آپ کے اپنے قواعد اوپر سے اختیاری ہیں۔

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**خطرناک کال کو روکنا opt-in ہے، اور بند شپ ہوتا ہے۔**
Recursive deletes، force pushes، sudo، secrets، package installs اور آؤٹ باؤنڈ
کالز میں سے ہر ایک کے لیے ایک قاعدہ ہے جسے آپ آن کر سکتے ہیں۔ جب تک آپ نہ کریں، ClawMetry
دیکھتا رہتا ہے اور کچھ نہیں بدلتا۔ ایک بار آن ہونے پر، ملتی جلتی کالیں یہاں
(یا آپ کے فون پر) منظوری یا انکار کے لیے انتظار کرتی ہیں۔

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

مزید، فی رن ٹائم: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)۔

## پہچان

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## Star History

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
