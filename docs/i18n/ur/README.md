<!-- i18n-src:12b97259721e -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**ایک ایجنٹ بغیر کوئی پیش رفت کیے سیکڑوں ٹول کالز کر سکتا ہے۔** ClawMetry
آپ کے کوڈنگ ایجنٹس پہلے سے جو سیشن فائلیں لکھتے ہیں انہیں پڑھتا ہے، اور
ٹائم لائن، ٹول کالز، اور رن ٹائم جو بھی ٹوکن اور لاگت کا ڈیٹا فراہم کرتا ہے
اسے ایک ہی منظر نامے میں پیش کرتا ہے — تاکہ آپ یہ بتا سکیں کہ کون سا طویل
رن کام کر رہا ہے اور کون سا اٹک چکا ہے۔

**31 AI ایجنٹ رن ٹائمز** کے ساتھ کام کرتا ہے — Claude Code، OpenAI Codex، Hermes، OpenClaw اور مزید 27۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ڈیش بورڈ۔ ([مکمل فہرست](SUPPORTED_RUNTIMES.txt)، جو کیٹلاگ سے تیار کی گئی ہے۔)

> 🌐 **اسے ان زبانوں میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ صفر کنفیگریشن۔ سب کچھ خود بخود شناخت کرتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے۔ صفر کنفیگریشن: یہ آپ کے پاس پہلے سے موجود ایجنٹ رن ٹائمز کو تلاش کرتا ہے، انہیں صرف پڑھنے کے موڈ میں پڑھتا ہے، اور ان کے چلنے کے طریقے میں کچھ بھی تبدیل نہیں کرتا۔

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## انسٹال کرنے سے پہلے

| | |
|---|---|
| **یہ کیا کرتا ہے** | آپ کے ایجنٹس پہلے سے جو سیشن فائلیں اور لاگز لکھتے ہیں انہیں پڑھتا ہے۔ کوئی SDK نہیں، کوڈ میں کوئی تبدیلی نہیں، آپ کی ایپ میں کوئی انسٹرومینٹیشن نہیں۔ |
| **آپ کیا دیکھتے ہیں** | سیشن ٹائم لائن، ٹول بہ ٹول ری پلے، ٹوکن اور لاگت کی تفصیل، اور trajectory سگنلز (لوپنگ، بار بار ناکامیاں) — ہر رن ٹائم کے لیے الگ الگ۔ |
| **کیا مفت ہے** | `pip install clawmetry` بغیر کسی اکاؤنٹ، کسی کلید یا کسی نیٹ ورک کال کے **OpenClaw، NVIDIA NemoClaw اور Goose** کو پڑھتا ہے۔ باقی 27 — Claude Code، Codex، Cursor اور دیگر — کلوزڈ سورس `clawmetry-pro` کمپینین کے ذریعے پڑھے جاتے ہیں، جو 7 دن کے ٹرائل یا کسی پلان کے ساتھ آتا ہے — عین تقسیم کے لیے [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) دیکھیں۔ |
| **کیسے شروع کریں** | `pip install clawmetry && clawmetry`، پھر localhost:8900 کھولیں۔ اس مشین پر ابھی کوئی ایجنٹ نہیں؟ `clawmetry --sample` تین لیبل شدہ مصنوعی سیشنز کے ساتھ کھلتا ہے۔ |
| **آپ کی مشین سے کیا باہر جاتا ہے** | کوئی سیشن ڈیٹا نہیں، جب تک آپ `clawmetry connect` نہ چلائیں۔ ڈیفالٹ کے طور پر دو چیزیں چلتی ہیں، دونوں opt-out ہیں اور دونوں میں سے کوئی بھی سیشن مواد نہیں لے جاتی: ایک گمنام انسٹال پنگ اور ایک PyPI ورژن چیک۔ ہر منزل [docs/EGRESS.md](docs/EGRESS.md) میں درج ہے، جو تبصروں کے بجائے وائر کیپچر سے تیار کی گئی ہے۔ |

فیصلہ کرنے سے پہلے جاننے کے لائق دو حدود: رن ٹائمز بہت مختلف ڈیٹا فراہم کرتے ہیں (کچھ بالکل بھی لاگت شائع نہیں کرتے — [میٹرکس](docs/compatibility.md) بتاتا ہے کون سا رن ٹائم کیا دیتا ہے)، اور کسی عمل کا مشاہدہ کرنا اسے روک سکنے کے مترادف نہیں ہے ([ہر رن ٹائم کے لیے کون سے کنٹرولز حقیقی ہیں](docs/APPROVALS.md))۔


## 31 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

**اوپن سورس ایپ میں مفت:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ایک ادا شدہ پلان پر:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ہر رن ٹائم کو ایک جیسا ڈیش بورڈ ملتا ہے۔ ایک ساتھ کئی چلائیں اور ہیڈر سوئچر ہر ٹیب کو ان میں سے کسی ایک کے دائرہ کار میں دوبارہ ترتیب دیتا ہے۔

کیا آپ نے کسی SDK پر اپنا خود کا ایجنٹ بنایا ہے؟ انٹرسیپٹر اس کی LLM کالز کو بھی ٹریک کرتا ہے۔ دیکھیں [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)۔

## آپ کو کیا ملتا ہے

- **سیشنز اور ٹرانسکرپٹس**: ہر ایجنٹ نے کیا کیا، باری بہ باری، ری پلے کے ساتھ
- **لاگت اور ٹوکنز**: رن ٹائم، ماڈل، سیشن اور دن کے لحاظ سے، بے قاعدگی کے نشانات کے ساتھ
- **Flow**: چینلز، ماڈلز اور ٹولز کے ذریعے حرکت کرنے والے پیغامات کا لائیو ڈایاگرام
- **Brain**: reasoning اور ٹول کال ایونٹ سٹریم، جیسے ہی وہ ہوتا ہے
- **Context blowout**: ہر پرووائیڈر کے مطابق ونڈو کا استعمال، compaction بمقابلہ forced overflow، نیز ہر رن ٹائم کا نقشہ کہ ہم *کیا نہیں* دیکھ سکتے ([کیسے](docs/CONTEXT_BLOWOUT.md))
- **Memory اور skills**: وہ فائلیں اور skills جو ہر رن ٹائم نے واقعی لوڈ کیں
- **Health اور logs**: ڈسک، میموری، ایرر ریٹس، ریٹ لمٹس، لائیو لاگ سٹریم
- **Alerts**: بجٹ کی حدیں، ایرر اسپائیکس، ایجنٹ-آف لائن، Slack، Discord، PagerDuty، Telegram، ای میل کی طرف روٹ شدہ
- **Approvals**: خطرناک ٹول کالز کو چلنے سے *پہلے* روکیں اور اپنے فون سے منظور کریں ([کیسے](docs/APPROVALS.md))

## Context blowout، اور نگرانی کی قیمت

کسی بھی ایجنٹ موازنہ ٹول پر اعتماد کرنے سے پہلے جواب دینے کے قابل دو سوالات۔

**یہ مختلف رن ٹائمز میں context-window blowout کو کیسے سنبھالتا ہے؟**

utilization فیصد صرف اتنا ہی ایماندار ہوتا ہے جتنا وہ عدد جس سے اسے تقسیم کیا جاتا ہے۔ ClawMetry ہر پرووائیڈر کے لیے ونڈو کا سائز
[ایک ایسے جدول](clawmetry/context_windows.py) سے لیتا ہے جسے آپ پڑھ اور PR کر سکتے ہیں،
جو Anthropic، OpenAI، Google، xAI، DeepSeek، Kimi، Qwen، Mistral، Llama اور GLM کا احاطہ کرتا ہے۔ یہ تمام 31
رن ٹائمز کو ایک ہی وینڈر کے پیمانے سے نہیں ناپتا۔ یہ اہم ہے: ایک 300K GPT-5 turn جسے
Anthropic کے 200K کے خلاف اسکور کیا جائے وہ ">100%، blown" پڑھتا ہے جبکہ حقیقت میں وہ
GPT-5 کے 400K کا 75% ہے۔ وہی پیمانہ ایک واقعی overflow ہونے والے 130K DeepSeek turn کو
ایک آرام دہ 65% کے طور پر چھپا دیتا ہے۔

ہر ونڈو اپنی provenance کے ساتھ آتی ہے: `model_table`، `explicit_marker`،
`observed_floor`، یا جب ہمیں ماڈل معلوم نہ ہو تو ایک ایماندار `default`۔ اندازے پر بنایا گیا
گیج کبھی بھی lookup پر بنائے گئے گیج جیسی اتھارٹی کے ساتھ رینڈر نہیں ہوتا۔

ClawMetry کچھ رن ٹائمز پر صرف compaction ایونٹس دیکھ سکتا ہے۔ اس لیے
`GET /api/context-coverage` ہر رن ٹائم کے لیے رپورٹ کرتا ہے کہ **صفر کا مطلب
"صاف چلا" ہے یا "ہمیں نظر نہیں آتا"**۔ ایک `0` جس کا اصل مطلب اندھا پن ہو وہ ایسا ہی کہتا ہے۔
[مکمل تفصیل](docs/CONTEXT_BLOWOUT.md)

**انسٹرومینٹیشن کی قیمت کیا ہے؟**

| راستہ | آپ کے ایجنٹ میں شامل | ڈیفالٹ؟ |
|---|---|---|
| Session-file tailing (تمام 31 رن ٹائمز) | **0**۔ الگ پراسیس، آپ کے ایجنٹ میں کوئی ClawMetry کوڈ نہیں | on |
| HTTP انٹرسیپٹر (`CLAWMETRY_INTERCEPT=1`) | فی LLM کال **+0.44 ms**، یعنی 5s کال کا 0.009% | off |
| Pre-tool hook gate (warm cache) | فی gated ٹول کال **+44 ms**، 36 ms انٹرپریٹر فلور کے اوپر | off |
| Enforcement proxy | فی LLM کال **+9.7 ms** | off |

Daemon host کی قیمت: انجیسٹ **2,762 events/sec**، ڈسک پر **710 bytes/event**
(67.7 MB فی 100k events)، اور مصروف انسٹال پر مسلسل **~12% ایک کور کا**۔ آخری عدد
ہمارے اپنے بیان کردہ 5-10% بجٹ سے زیادہ ہے، اس لیے اسے صفحے سے چھوڑنے کے بجائے
پیچھا کرنے کے قابل بگ کے طور پر شائع کیا گیا ہے۔

Apple M2 Pro پر `benchmarks/overhead.py` سے ماپا گیا۔ ہارنس ہر حالت کو الگ
پراسیس میں چلاتا ہے، ان کی ترتیب بدلتا رہتا ہے، اور **جب راؤنڈز عدد کے sign پر
متفق نہ ہوں تو کوئی نمبر پرنٹ کرنے سے انکار کرتا ہے**۔ اسے اپنی مشین پر ایک منٹ میں چلائیں:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

ہر راستہ ماپا گیا ہے، بشمول hook gates اور enforcement proxy، اور
ہارنس CI میں Linux، macOS اور Windows پر چلتا ہے۔ جاننے کے لائق دو نتائج: proxy
کی قیمت Windows پر Linux کے مقابلے میں تقریباً سات گنا زیادہ ہے، اور daemon فی الحال
ایک کور کا تقریباً 12% مسلسل استعمال کرتا ہے، جو ہمارے اپنے 5-10% بجٹ سے زیادہ ہے۔ خام JSON، طریقہ کار،
اور جو ابھی تک ناپا نہیں گیا وہ [docs/OVERHEAD.md](docs/OVERHEAD.md) میں ہے۔

## قیمتیں

| پلان | یہ کیا کور کرتا ہے | قیمت |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose، مکمل ڈیش بورڈ، صرف مقامی | $0 |
| **Starter** | اوپر کے باقی تمام رن ٹائمز، فلیٹ ویو، cloud sync | $9 فی node / مہینہ |
| **Pro** | Starter + کنٹرول اور تشخیص: approvals، tool-risk policies، evals، anomaly detection، cost optimizer، OTel export، tamper-evident audit log | $19 فی node / مہینہ |

سالانہ پلانز، Enterprise اور موجودہ قیمتیں
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** پر موجود ہیں۔ Self-hosted لائسنس
کیز بغیر cloud کے کام کرتی ہیں (`clawmetry license`)۔ عین مفت/ادا شدہ تقسیم
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) میں ہے۔

## آپ کا ڈیٹا آپ کی مشین پر ہی رہتا ہے

ClawMetry مقامی سیشن فائلیں اور لاگز پڑھتا ہے۔ **جب تک آپ `clawmetry connect` نہ چلائیں
کوئی سیشن ڈیٹا آپ کے باکس سے باہر نہیں جاتا** — کوئی prompts، replies، tool arguments، فائل
مواد یا لاگ لائنیں نہیں۔ جب آپ کنیکٹ کرتے ہیں، تو snapshot ایک ایسی کلید کے ساتھ end-to-end
encrypted ہوتا ہے جو کبھی آپ کی مشین سے باہر نہیں جاتی، اور آپ کے براؤزر میں decrypt ہوتا ہے۔ اگر کسی
node کے پاس کوئی کلید نہیں، تو اپ لوڈ کو صاف حالت میں بھیجنے کے بجائے چھوڑ دیا جاتا ہے، اور کوئی
سرور جواب اسے بند نہیں کر سکتا۔

کنیکٹ کرنے سے پہلے ڈیفالٹ کے طور پر دو چیزیں چلتی ہیں، دونوں opt-out ہیں اور دونوں میں سے
کوئی بھی سیشن ڈیٹا نہیں لے جاتی: ایک گمنام انسٹال پنگ اور PyPI کے خلاف ایک ورژن چیک۔ ایک ڈیفالٹ
انسٹال آپ کا عوامی IP بھی ایک بار startup بینر لائن کے لیے تلاش کرتا ہے۔ ہر منزل، وہ کیا لے جاتی ہے اور اسے کیسے بند کیا جائے
[docs/EGRESS.md](docs/EGRESS.md) میں درج ہے؛ self-hosted، دوبارہ pointed اور air-gapped انسٹالز
کوئی اختیاری outbound کالز بالکل نہیں کرتیں۔

Decryption آپ کے براؤزر میں، ہمارے فراہم کردہ کوڈ میں ہوتا ہے۔ یہ پہلے ایک وعدہ تھا؛ اب یہ کچھ ایسا ہے
جسے آپ چیک کر سکتے ہیں۔ ہر لائن جو آپ کی کلید کو چھوتی ہے ایک قابل مطالعہ فائل میں رہتی ہے،
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
جو wheel کے اندر شپ ہوتی ہے اور من و عن پیش کی جاتی ہے، Subresource
Integrity ہیش کے ساتھ pinned۔ یہ تصدیق کرنے کے لیے کہ براؤزر وہی چلاتا ہے جو ہم نے شائع کیا:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

یہ کیا ثابت نہیں کرتا: ہم وہ صفحہ فراہم کرتے ہیں جو فائل کو لوڈ کرتا ہے، لہٰذا ہم کوئی مختلف
صفحہ پیش کر سکتے تھے۔ Integrity ہیشز آپ کو ایک compromised CDN سے بچاتی ہیں،
وینڈر سے نہیں۔ آپ کو جو حاصل ہوتا ہے وہ یہ ہے کہ کوئی بھی تبدیلی جان بوجھ کر، صفحے کے سورس میں
نظر آنے والی، اور PyPI پر موجود artifact سے مختلف ہونی چاہیے جسے کوئی بھی حاصل کر سکتا ہے۔ Self-hosting
یا صرف مقامی رہنا اس انحصار کو مکمل طور پر ختم کر دیتا ہے۔

## انسٹال

```bash
pip install clawmetry     # پھر: clawmetry
```

یا ایک-لائنر: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS، Linux یا Windows پر Python 3.8+ کی ضرورت ہے، اور اسی مشین پر کم از کم ایک ایجنٹ
رن ٹائم۔ Docker ہدایات: [docs/DOCKER.md](docs/DOCKER.md)۔

یا ایجنٹ کو خود آپ کے لیے سیٹ اپ کرنے دیں۔ [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
skill، Claude Code، Codex، Cursor، Gemini CLI، Copilot یا OpenCode کو سکھاتی ہے کہ کیسے
ClawMetry انسٹال کریں، مشین پر موجود ایجنٹس کیا کر رہے ہیں اور خرچ کر رہے ہیں اس کی رپورٹ دیں،
درخواست پر ایک سیشن روکیں، اور منظوری کے لیے خطرناک ٹول کالز روک کر رکھیں:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## Docs

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ہر adapter کیا پڑھتا ہے، اور ایک رن ٹائم کیسے شامل کریں |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | فی-پرووائیڈر ونڈوز، compaction بمقابلہ overflow، فی-رن ٹائم coverage |
| [Overhead](docs/OVERHEAD.md) | انسٹرومینٹیشن کی قیمت کیا ہے، ماپی گئی، اسے دوبارہ پیش کرنے والے harness کے ساتھ |
| [Entitlements](docs/ENTITLEMENTS.md) | مفت بمقابلہ ادا شدہ، tier میٹرکس، لائسنس CLI |
| [Approvals & policies](docs/APPROVALS.md) | Pre-execution gating، risk scoring، فون پر منظوریاں |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | کہیں بھی traces export کریں، کسی بھی چیز سے OTLP ingest کریں |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، Pydantic AI، LangChain سرے سے سرے تک، چلنے والی مثالوں کے ساتھ |
| [SDK tracking](docs/SDK_TRACKING.md) | آپ نے خود بنائے ہوئے ایجنٹس کے لیے لاگت کی نسبت |
| [Chat channels](docs/CHANNELS.md) | Flow میں دکھائے گئے chat adapters |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | Sandboxed NVIDIA NemoClaw سیٹ اپس |
| [Docker](docs/DOCKER.md) | Image، compose، volume mounts |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | یہ اندر سے کیسے کام کرتا ہے؛ سورس سے چلانا |
| [Telemetry](docs/TELEMETRY.md) | گمنام انسٹال اور desktop-open pings، اور انہیں کیسے بند کریں |

## اسکرین شاٹس

نیچے دیا گیا ہر عدد ایک حقیقی مشین سے ہے، صرف پڑھنے کے موڈ میں، بغیر کسی seeded ڈیٹا کے۔

**یہ آپ کو بتاتا ہے کہ کب کچھ غلط ہے، صرف یہ نہیں کہ کیا ہوا۔**
اوپر دو anomaly banners: خرچ روزانہ اوسط سے 7 گنا چل رہا ہے، اور ایک
4.2x cost spike۔ ان کے نیچے، حالیہ 667 سیشنز میں سے 324 waste سگنل لیے ہوئے ہیں، وجہ کے مطابق درج۔

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**یہ آپ کو دکھاتا ہے کہ پیسہ کہاں گیا، ہر ونڈو میں۔**
آج $252.47، اس ہفتے $513.15، اس مہینے $1,312.92، ہر ایک کے پیچھے ٹوکنز اور
آپ کی سبسکرپشن پہلے سے کتنا کور کرتی ہے کے ساتھ۔ اس کے نیچے، تقریباً $1,128/mo قابل بازیافت کے طور پر
اور $17,256/mo cache reuse سے پہلے ہی بچائے گئے کے طور پر itemised۔

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**یہ دکھاتا ہے کہ ایک پیغام کیسے جواب بنتا ہے۔**
لائیو flow ڈایاگرام: آپ، وہ چینل جس پر یہ آیا، gateway، ابھی جواب دینے والا ماڈل،
اور ہر وہ ٹول جس تک اس نے رسائی حاصل کی۔ Nodes روشن ہوتے ہیں جیسے جیسے کام ان سے گزرتا ہے۔

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**مشین پر ہر ایجنٹ، ایک ہی جدول میں۔**
یہ کیا چلاتا ہے، پچھلے 24 گھنٹوں اور اپنی پوری زندگی میں اس کی قیمت کتنی ہے، آخری بار
کب دیکھا گیا، مالک کون ہے، اور کیا کوئی سبسکرپشن بل کور کر رہی ہے۔ یہاں 14 ایجنٹس، 3 سیشنز کام کر رہے،
13 خاموش۔

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**یہ دکھاتا ہے کہ ایک turn کا وقت اور پیسہ کہاں گیا، ٹول بہ ٹول۔**
ایک حقیقی سیشن کا ایک turn: 11.2 منٹ میں 11 ٹولز، $1.16 میں۔ ہر Bash
کال اور ماڈل کال کو ٹائم لائن پر اپنا بار ملتا ہے، تاکہ وہ کمانڈ جو 4.1 منٹ تک چلی
اور وہ جو 226ms چلی، ایک نظر میں الگ پہچانی جا سکیں۔

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**یہ کام کی درجہ بندی کرتا ہے، صرف خرچ کی نہیں۔**
اس ہفتے ایک A: 54 tasks صاف واپس آئے، 2 کھردرے کی قیمت $48.57 رہی، اور
جن runs میں درجہ بندی کے لیے کافی سرگرمی نہیں تھی انہیں فتح شمار کرنے کے بجائے درجہ بندی سے خارج
رکھا گیا۔ ہر کھردرا run اپنے trace سے لنک کرتا ہے۔

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**یہ دکھاتا ہے کہ context window کیوں بھرتا رہتا ہے۔**
تازہ ترین turn پر 1M-token ونڈو میں سے 715K، 83.3% peak، 4 compactions
جو سب overflow کے بجائے proactively فائر ہوئیں، اور اس کے پیچھے ہر turn کا utilisation۔

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**Detection آپ کے کچھ کنفیگر کیے بغیر چلتی ہے۔**
built-in detectors انسٹال کے وقت سے ہی on ہیں: ایجنٹ خاموش ہو گیا، telemetry feed
رک گئی، cost spike، token burst، بڑھتی ہوئی errors، error spike، بجٹ
threshold، threat signature میچ ہوئی، سیکیورٹی ٹول کی تلاش، سیکیورٹی کرنسی
تبدیل ہوئی۔ آپ کے اپنے rules اوپر سے اختیاری ہیں۔

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**کسی خطرناک کال کو روکنا opt-in ہے، اور بند حالت میں شپ ہوتا ہے۔**
Recursive deletes، force pushes، sudo، secrets، package installs اور outbound
کالز میں سے ہر ایک کو ایک rule ملتا ہے جسے آپ آن کر سکتے ہیں۔ جب تک آپ ایسا نہ کریں، ClawMetry دیکھتا رہتا ہے
اور کچھ تبدیل نہیں کرتا۔ ایک بار آن ہونے پر، میچ کرنے والی کالز یہاں (یا آپ کے فون پر) منظوری یا
مسترد کیے جانے کا انتظار کرتی ہیں۔

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

## License

MIT · بنایا از [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
