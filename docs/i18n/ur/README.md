<!-- i18n-src:bab48eec552f -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **14 AI ایجنٹ رن ٹائمز** کے لیے حقیقی وقت میں مشاہدہ: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور 10 مزید۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ڈیش بورڈ۔

> 🌐 **اسے ان زبانوں میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ کوئی کنفیگ نہیں۔ سب کچھ خودکار طریقے سے پتا چل جاتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے اور بس، کام مکمل۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

ClawMetry نے OpenClaw کے لیے مشاہدے کے طور پر آغاز کیا، اور اب یہ آپ کے **پورے ایجنٹ فلیٹ** کو ایک ہی ڈیش بورڈ میں ماپتا ہے، آپ کی مشین پر ہر رن ٹائم کو خودکار طور پر پہچانتے ہوئے:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw اور NemoClaw اوپن سورس ایپ میں مفت ہیں؛ باقی رن ٹائمز ClawMetry Cloud یا سیلف ہوسٹڈ Pro لائسنس کے ساتھ فعال ہوتے ہیں۔ ہیڈر سے رن ٹائم تبدیل کریں اور ہر ٹیب — لاگت، ٹوکنز، ٹولز، ٹریسز — اسی رن ٹائم کے مطابق دوبارہ ترتیب پاتا ہے۔ صحیح مفت/ادائیگی تقسیم، ٹئیر میٹرکس، `/api/entitlement` شکل، اور `clawmetry license` CLI کے لیے **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** دیکھیں۔

## آپ کو کیا ملتا ہے

- **Flow** — چینلز، برین، ٹولز اور واپسی کے راستے میں پیغامات کی گردش دکھانے والا زندہ متحرک خاکہ
- **Overview** — ہیلتھ چیکس، ایکٹیویٹی ہیٹ میپ، سیشن گنتی، ماڈل کی معلومات
- **Usage** — روزانہ/ہفتہ وار/ماہانہ تفصیل کے ساتھ ٹوکن اور لاگت کی نگرانی
- **Sessions** — فعال ایجنٹ سیشنز، ماڈل، ٹوکنز، آخری سرگرمی کے ساتھ
- **Crons** — شیڈول شدہ جابز، حیثیت، اگلی رن، دورانیہ کے ساتھ
- **Logs** — رنگ کوڈڈ ریئل ٹائم لاگ سٹریمنگ
- **Memory** — SOUL.md، MEMORY.md، AGENTS.md، روزانہ نوٹس دیکھیں
- **Transcripts** — سیشن ہسٹری پڑھنے کے لیے چیٹ بلبلا انٹرفیس
- **Alerts** — بجٹ کی حدیں، ایرر ریٹ ٹرگرز، ایجنٹ آف لائن پتہ لگانا؛ Slack، Discord، PagerDuty، Telegram، Email پر روٹ کرتا ہے
- **Approvals** — تباہ کن ڈیلیٹس، فورس پشز، ڈی بی میوٹیشنز، sudo، پیکیج انسٹالیشنز، نیٹ ورک کالز کو ایک کلک منظوری کے پیچھے روکیں

## سکرین شاٹس

### 🧠 Brain — زندہ ایجنٹ ایونٹ سٹریم
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ٹوکن استعمال اور سیشن خلاصہ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — حقیقی وقت ٹول کال فیڈ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ماڈل اور سیشن کے حساب سے لاگت کی تفصیل
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ورک اسپیس فائل براؤزر
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — پوزیشن اور آڈٹ لاگ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — بجٹ کی حدیں، ایرر ریٹ ٹرگرز، Slack / Discord / PagerDuty / Email کے لیے ویب ہکس
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — خطرناک ٹول کالز کو دستی منظوری کے پیچھے روکیں؛ پالیسی پر مبنی تحفظ کے قواعد
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code کے لیے پری ایگزیکیوشن بلاکنگ** — ایک کمانڈ ایک
PreToolUse ہک انسٹال کرتی ہے جو مماثل ٹول کالز کو ان کے چلنے *سے پہلے* روک دیتی ہے اور آپ کے فیصلے کا انتظار کرتی ہے (آپ کے فون سے ایک ٹیپ کے ساتھ
[کلاؤڈ پش نوٹیفیکیشنز](https://app.clawmetry.com/push) فعال ہونے پر):

```bash
clawmetry hooks install     # ~/.claude/settings.json لکھتا ہے (idempotent)
clawmetry hooks status      # کیا وائرڈ ہے + کتنی پالیسیاں فعال ہیں
clawmetry hooks uninstall   # صرف ClawMetry کی اندراجات ہٹاتا ہے
```

ایک انکار صرف اس ایک ٹول کال کو روکتا ہے — ایجنٹ اپنا سیشن برقرار رکھتا ہے اور
کوئی اور طریقہ آزما سکتا ہے۔ آپ کے فون پر منظوری دینا Claude Code کی اپنی
اجازت کے پرامپٹ کو چھوڑ دیتا ہے (آپ پہلے ہی جواب دے چکے ہیں)۔ غیر مماثل ٹولز کی قیمت ~40ms ہوتی ہے اور
Claude Code کے عام اجازت کے بہاؤ میں چلے جاتے ہیں۔ جب Claude Code خود آپ کا انتظار کر رہا ہو تو آپ کو فون پش بھی ملتا ہے (`permission_prompt` /
`idle_prompt` نوٹیفیکیشنز)۔

## انسٹال

**ون لائنر (تجویز کردہ):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**سورس سے:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 فرنٹ اینڈ ڈویلپمنٹ

v2 React ایپ `frontend/` میں موجود ہے اور جب Flask
سرور v2 فعال کر کے شروع کیا جاتا ہے تو `/v2` پر سرو ہوتی ہے۔

ڈویلپمنٹ کے دوران دو ٹرمینلز استعمال کریں:

```bash
# ٹرمینل 1: :8900 پر Flask API/سرور
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# ٹرمینل 2: :5173 پر Vite ڈیو سرور
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` کھولیں۔ Vite `/api` درخواستوں کو
`http://localhost:8900` کی طرف پراکسی کرتا ہے، تاکہ React ایپ اضافی CORS سیٹ اپ کے بغیر مقامی Flask سرور سے بات کر سکے۔

Python پیکج کے ساتھ شپ ہونے والا بنڈل بنانے کے لیے:

```bash
cd frontend
npm run build
```

پروڈکشن بنڈل `clawmetry/static/v2/dist/` میں لکھا جاتا ہے۔

## رن ٹائم / ایجنٹ مطابقت

ClawMetry صرف OpenClaw ہی نہیں، بلکہ بہت سے AI-ایجنٹ رن ٹائمز کا مشاہدہ کرتا ہے۔ ہر غیر-OpenClaw رن ٹائم کے لیے ایک وقف شدہ ریڈر اڈاپٹر شپ ہوتا ہے جو اس کی مقامی سیشن فارمیٹ کو ClawMetry کی متحدہ شکلوں میں ترجمہ کرتا ہے؛ ڈیمن انہیں اسی DuckDB سٹور + کلاؤڈ سنیپ شاٹ میں ضم کرتا ہے، رن ٹائم کے ساتھ ٹیگ کیا ہوا، اور جب ایک سے زیادہ رن ٹائمز موجود ہوں تو Session replay ٹیب ایک **رن ٹائم سوئچر** دکھاتا ہے۔ مکمل میٹرکس + رن ٹائمز شامل کرنے کی گائیڈ کے لیے [`docs/compatibility.md`](docs/compatibility.md) دیکھیں، اور OpenClaw-فیملی پرائمر کے لیے [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) دیکھیں۔

| رن ٹائم / ایجنٹ | حیثیت | نوٹس |
|---|---|---|
| **OpenClaw** | نیٹو | حوالہ رن ٹائم، خودکار طور پر پتا چلتا ہے |
| **PicoClaw** | بیٹا اڈاپٹر | فلیٹ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)۔ ٹرانسکرپٹس، ماڈل، ٹول کالز۔ |
| **NanoClaw** | بیٹا اڈاپٹر | فی سیشن SQLite (`data/v2-sessions`)۔ ٹرانسکرپٹس + پیغام گنتی۔ |
| **Hermes** | بیٹا اڈاپٹر | SQLite `~/.hermes/state.db`۔ ٹرانسکرپٹس، ماڈل، ٹوکنز/لاگت۔ |
| **Claude Code** | بیٹا اڈاپٹر | JSONL `~/.claude/projects/.../<id>.jsonl`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز + تھنکنگ، ٹوکن استعمال۔ |
| **Codex** | بیٹا اڈاپٹر | رول آؤٹ JSONL `~/.codex/sessions/...`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Cursor** | بیٹا اڈاپٹر | SQLite `state.vscdb`۔ چیٹ/کمپوزر ٹرانسکرپٹس، ماڈل۔ |
| **Aider** | بیٹا اڈاپٹر | ہر پروجیکٹ کے لیے `.aider.chat.history.md`۔ ٹرانسکرپٹس، ماڈل، ٹوکن گنتی۔ |
| **Goose** | بیٹا اڈاپٹر | SQLite `~/.local/share/goose`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن ٹوٹل۔ |
| **opencode** | بیٹا اڈاپٹر | SQLite `~/.local/share/opencode`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Qwen Code** | بیٹا اڈاپٹر | JSONL `~/.qwen/projects/.../chats`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Pi** | بیٹا اڈاپٹر | JSONL `~/.pi/agent/sessions`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Deep Agents** | بیٹا اڈاپٹر | SQLite `~/.deepagents/.state/sessions.db`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |

"بیٹا اڈاپٹر" کا مطلب ہے کہ ClawMetry اس رن ٹائم کی حقیقی آن-ڈسک فارمیٹ کے لیے ایک ریڈر شپ کرتا ہے، ہر ایک کو حقیقی مشین پر حقیقی انسٹال کے خلاف بنایا اور تصدیق کیا گیا (`tests/fixtures/runtimes/<rt>/` دیکھیں)۔ اڈاپٹرز صرف پڑھنے کے قابل ہیں؛ ہر ایک اپنے رن ٹائم کے اصل میں محفوظ کردہ ڈیٹا کے بارے میں دیانتدار ہے (مثلاً PicoClaw/NanoClaw/Cursor ٹوکن لاگت ڈسک پر نہیں لکھتے)۔ جب ایک نوڈ پر کئی رن ٹائمز چل رہے ہوں، تو رن ٹائم سوئچر سیشنز کے منظر کو صاف گہرے مطالعے کے لیے ایک تک محدود کرتا ہے۔

## کسی بھی SDK ایجنٹ کو ٹریک کریں — آؤٹ-لوپ لاگت کی وابستگی

اوپر دیے گئے تمام رن ٹائمز سیشنز کو ڈسک پر لکھتے ہیں۔ آپ کا اپنا **پروڈکشن ایجنٹ** — وہ جو آپ نے OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B، یا ایک سادہ `httpx` لوپ پر بنایا — ایسا نہیں کرتا۔ ClawMetry کا زیرو-کنفیگ انٹرسیپٹر پھر بھی `httpx`/`requests` کو مانکی پیچ کر کے اس کی LLM کالز (لاگت، ٹوکنز، لیٹنسی، ایررز) پکڑتا ہے:

```python
import clawmetry.track            # انٹرسیپٹر فعال کریں
clawmetry.track.set_source("support-agent")   # اس پروڈکٹ کا نام رکھیں

# ...آپ کا ایجنٹ عام طور پر چلتا ہے؛ ہر LLM کال اب ٹریک اور منسوب ہو رہی ہے۔
```

`set_source()` (یا `CLAWMETRY_SOURCE=support-agent` env var) ہر کال کو ایک **نامزد سورس** کے ساتھ ٹیگ کرتا ہے، تاکہ آپ کا چلایا ہوا ہر پروڈکٹ ڈیش بورڈ کے Overview پر **🔌 آؤٹ-لوپ سورسز** کارڈ میں اپنی الگ، لاگت-منسوب کرنے کے قابل لائن کے طور پر نظر آئے — ہر ایجنٹ کے لیے کالز، فراہم کنندگان، لیٹنسی، ایرر ریٹ۔ کوئی سورس سیٹ نہیں کیا؟ کالز پھر بھی ٹریک ہوتی ہیں؛ بس کارڈ چھپا رہتا ہے۔

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

یہ وہی ڈیٹا لیئر ہے جو رن ٹائم اڈاپٹرز کو فیڈ کرتی ہے (DuckDB → کلاؤڈ سنیپ شاٹ)، اس لیے آؤٹ-لوپ سورسز باقی سب چیزوں کی طرح ہی کلاؤڈ ڈیش بورڈ سے سنک ہوتے ہیں، E2E-انکرپٹڈ۔

## OpenTelemetry — وینڈر-نیوٹرل، اپنے ٹریسز کہیں بھی بھیجیں

ClawMetry دونوں سمتوں میں **OpenTelemetry** بولتا ہے، **GenAI سیمنٹک کنونشنز** استعمال کرتے ہوئے، تاکہ آپ کے ایجنٹ ٹریسز کبھی بھی ایک ٹول تک محدود نہ رہیں۔

ہر سیشن — LLM کالز، ٹولز، سب-ایجنٹس، ٹوکنز، لاگت — کو کسی بھی کلیکٹر (Datadog، Grafana، Honeycomb، یا آپ کا اپنا OTel Collector) میں OTLP/HTTP GenAI اسپینز کے طور پر **ایکسپورٹ** کریں:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# مساوی طور پر:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

آتھ ہیڈرز اور پول انٹرول اختیاری env vars ہیں:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # اضافی HTTP ہیڈرز
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # سیکنڈز (ڈیفالٹ 60)
```

**Ingest** — بلٹ-اِن OTLP وصول کنندہ `/v1/traces` اور `/v1/metrics` پر کسی بھی دوسری چیز سے ٹریسز اور میٹرکس قبول کرتا ہے (protobuf ingest کے لیے `pip install clawmetry[otel]`)۔

آپ کو زیرو-کنفیگ، لوکل-فرسٹ ClawMetry ڈیش بورڈ **اور** آپ کا ڈیٹا جس بھی بیک اینڈ پر آپ کی ٹیم پہلے سے چلا رہی ہے، دونوں ملتے ہیں — نہ کوئی لاک-اِن، نہ دوسرا ایجنٹ انسٹال کرنے کی ضرورت۔

## کنفیگریشن

زیادہ تر لوگوں کو کسی کنفیگ کی ضرورت نہیں۔ ClawMetry آپ کا ورک اسپیس، لاگز، سیشنز، اور کرونز خودکار طور پر پہچانتا ہے۔

اگر آپ کو حسب ضرورت بنانے کی ضرورت ہے:

```bash
clawmetry --port 9000              # حسب ضرورت پورٹ (ڈیفالٹ: 8900)
clawmetry --host 127.0.0.1         # صرف لوکل ہوسٹ سے بائنڈ کریں
clawmetry --workspace ~/mybot      # حسب ضرورت ورک اسپیس پاتھ
clawmetry --name "Alice"           # Flow ویژولائزیشن میں آپ کا نام
```

تمام آپشنز: `clawmetry --help`

## معاون چینلز

ClawMetry آپ کے کنفیگر کیے گئے ہر OpenClaw چینل کے لیے زندہ سرگرمی دکھاتا ہے۔ صرف وہی چینلز جو آپ کے `openclaw.json` میں واقعی سیٹ اپ ہیں Flow خاکے میں ظاہر ہوتے ہیں — غیر کنفیگر شدہ خودکار طور پر چھپے رہتے ہیں۔

Flow میں کسی بھی چینل نوڈ پر کلک کر کے آنے والے/جانے والے پیغامات کی گنتی کے ساتھ ایک زندہ چیٹ بلبلا منظر دیکھیں۔

| چینل | حیثیت | زندہ پاپ اپ | نوٹس |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ مکمل | ✅ | پیغامات، اعداد و شمار، 10s ریفریش |
| 💬 **iMessage** | ✅ مکمل | ✅ | `~/Library/Messages/chat.db` براہ راست پڑھتا ہے |
| 💚 **WhatsApp** | ✅ مکمل | ✅ | WhatsApp Web (Baileys) کے ذریعے |
| 🔵 **Signal** | ✅ مکمل | ✅ | signal-cli کے ذریعے |
| 🟣 **Discord** | ✅ مکمل | ✅ | Guild + چینل کی پہچان |
| 🟪 **Slack** | ✅ مکمل | ✅ | ورک اسپیس + چینل کی پہچان |
| 🌐 **Webchat** | ✅ مکمل | ✅ | بلٹ-اِن ویب UI سیشنز |
| 📡 **IRC** | ✅ مکمل | ✅ | ٹرمینل طرز کا بلبلا UI |
| 🍏 **BlueBubbles** | ✅ مکمل | ✅ | BlueBubbles REST API کے ذریعے iMessage |
| 🔵 **Google Chat** | ✅ مکمل | ✅ | Chat API ویب ہکس کے ذریعے |
| 🟣 **MS Teams** | ✅ مکمل | ✅ | Teams بوٹ پلگ اِن کے ذریعے |
| 🔷 **Mattermost** | ✅ مکمل | ✅ | سیلف ہوسٹڈ ٹیم چیٹ |
| 🟩 **Matrix** | ✅ مکمل | ✅ | غیر مرکزی، E2EE سپورٹ |
| 🟢 **LINE** | ✅ مکمل | ✅ | LINE میسجنگ API |
| ⚡ **Nostr** | ✅ مکمل | ✅ | غیر مرکزی NIP-04 DMs |
| 🟣 **Twitch** | ✅ مکمل | ✅ | IRC کنکشن کے ذریعے چیٹ |
| 🔷 **Feishu/Lark** | ✅ مکمل | ✅ | WebSocket ایونٹ سبسکرپشن |
| 🔵 **Zalo** | ✅ مکمل | ✅ | Zalo Bot API |

> **خودکار پہچان:** ClawMetry آپ کا `~/.openclaw/openclaw.json` پڑھتا ہے اور صرف وہی چینلز رینڈر کرتا ہے جو آپ نے واقعی کنفیگر کیے ہیں۔ کسی دستی سیٹ اپ کی ضرورت نہیں۔

## Docker تعیناتی

ایک کنٹینر میں ClawMetry چلانا چاہتے ہیں؟ کوئی مسئلہ نہیں! 🐳

**Docker کے ساتھ فوری آغاز:**

```bash
# امیج بنائیں
docker build -t clawmetry .

# ڈیفالٹ سیٹنگز کے ساتھ چلائیں
docker run -p 8900:8900 clawmetry

# یا اپنے ایجنٹ کا ڈیٹا ڈائریکٹری ماؤنٹ کریں (دکھایا گیا: OpenClaw کا ~/.openclaw)
docker run -p 8900:8900 \
  -v ~/.openclaw:/root/.openclaw \
  -v /tmp/moltbot:/tmp/moltbot \
  clawmetry
```

**Docker Compose مثال:**

```yaml
version: '3.8'
services:
  clawmetry:
    build: .
    ports:
      - "8900:8900"
    volumes:
      - ~/.openclaw:/root/.openclaw:ro
      - /tmp/moltbot:/tmp/moltbot:ro
    restart: unless-stopped
```

> **نوٹ:** Docker میں چلاتے وقت، اپنے ایجنٹ کا ڈیٹا + لاگ ڈائریکٹریز (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) ماؤنٹ کریں تاکہ ClawMetry آپ کا سیٹ اپ خودکار طور پر پہچان سکے۔

## ضروریات

- Python 3.8+
- Flask (pip کے ذریعے خودکار طور پر انسٹال ہوتا ہے)
- ایک ہی مشین پر ایک AI ایجنٹ رن ٹائم: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، یا Deep Agents (یا Docker کے لیے ماؤنٹ شدہ والیومز)
- Linux یا macOS

## NemoClaw / OpenShell سپورٹ

ClawMetry خودکار طور پر [NemoClaw](https://github.com/NVIDIA/NemoClaw) کو پہچانتا ہے — NVIDIA کا انٹرپرائز سیکیورٹی ریپر جو OpenClaw کے لیے ہے اور ایجنٹس کو سینڈ باکسڈ OpenShell کنٹینرز کے اندر چلاتا ہے۔

زیادہ تر معاملات میں کسی اضافی کنفیگریشن کی ضرورت نہیں۔ سنک ڈیمن سیشن فائلوں کو خودکار طور پر دریافت کرتا ہے چاہے وہ ہوسٹ پر `~/.openclaw/` میں ہوں یا OpenShell کنٹینر کے اندر۔

### یہ کیسے کام کرتا ہے

ClawMetry NemoClaw کو دو طریقوں سے پہچانتا ہے:

1. **بائنری کی پہچان** — `nemoclaw` CLI کی جانچ کرتا ہے اور سینڈ باکس کی معلومات حاصل کرنے کے لیے `nemoclaw status` چلاتا ہے
2. **کنٹینر کی پہچان** — `openshell`، `nemoclaw`، یا `ghcr.io/nvidia/` امیجز کے لیے چلتے ہوئے Docker کنٹینرز کو اسکین کرتا ہے، پھر والیوم ماؤنٹس یا `docker cp` کے ذریعے سیشنز پڑھتا ہے

NemoClaw کنٹینرز سے سنک شدہ سیشن فائلوں کو کلاؤڈ ڈیش بورڈ میں `runtime=nemoclaw` اور `container_id` میٹا ڈیٹا کے ساتھ ٹیگ کیا جاتا ہے، تاکہ آپ انہیں معیاری OpenClaw سیشنز سے ایک نظر میں الگ کر سکیں۔

### تجویز کردہ سیٹ اپ: ہوسٹ پر سنک ڈیمن

بہترین تجربے کے لیے، ClawMetry کا سنک ڈیمن **ہوسٹ مشین** پر چلائیں (سینڈ باکس کے اندر نہیں)۔ اس سے NemoClaw نیٹ ورک پالیسی کی پابندیوں سے بچا جا سکتا ہے۔

```bash
# ہوسٹ پر (سینڈ باکس کے باہر)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سنک ڈیمن خودکار طور پر کسی بھی چلتے ہوئے OpenShell کنٹینر کے اندر سیشنز تلاش کر لے گا۔

### اختیاری: واضح سینڈ باکس نام

اگر خودکار پہچان کام نہ کرے، تو ClawMetry کو صحیح سینڈ باکس کی طرف اشارہ کریں:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### سینڈ باکس کے اندر چلانا (ایڈوانسڈ)

اگر آپ کو سنک ڈیمن OpenShell سینڈ باکس کے **اندر** چلانا ضروری ہو، تو اپنی NemoClaw نیٹ ورک پالیسی میں یہ ایگریس رول شامل کریں تاکہ یہ ClawMetry ingest API تک پہنچ سکے:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

اس کے ساتھ لاگو کریں:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### پورٹس اور اینڈ پوائنٹس

| اینڈ پوائنٹ | پورٹ | پروٹوکول | ضروری |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ہاں (سنک ڈیمن → کلاؤڈ) |
| `localhost:8900` | 8900 | HTTP | ہاں (لوکل ڈیش بورڈ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | کنٹینر سیشن دریافت کے لیے |

سنک ڈیمن صرف `ingest.clawmetry.com` کو آؤٹ باؤنڈ HTTPS کالز کرتا ہے۔ کوئی اِن باؤنڈ پورٹس درکار نہیں۔

---

## کلاؤڈ تعیناتی

SSH ٹنلز، ریورس پراکسی، اور Docker کے لیے **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** دیکھیں۔

## ٹیسٹنگ

یہ پروجیکٹ BrowserStack کے ساتھ ٹیسٹ کیا گیا ہے۔

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ٹیلی میٹری

جب آپ نئی مشین پر پہلی بار `clawmetry` CLI چلاتے ہیں تو ClawMetry
ایک واحد گمنام "فرسٹ رن" پنگ `https://app.clawmetry.com/api/install` کو بھیجتا ہے۔ ہم اسے انسٹالز گننے کے لیے استعمال کرتے ہیں (ایک اوپن سورس پروجیکٹ کے لیے ہمارے پاس واحد مارکیٹنگ میٹرک) اور یہ جاننے کے لیے کہ ہمارے صارفین نے کون سے
ایجنٹ فریم ورکس انسٹال کر رکھے ہیں۔

**فی انسٹال بالکل ایک POST**، جس میں شامل ہے:

| فیلڈ | مثال | وجہ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` پر محفوظ کردہ بے ترتیب UUID | ڈیڈوپ؛ آپ کے ای میل یا api_key سے منسلک نہیں |
| `version` | `0.12.167` | کون سے ورژنز استعمال میں ہیں |
| `os` / `os_version` | `Darwin` / `25.3.0` | پلیٹ فارم سپورٹ کی ترجیحات |
| `python` | `3.11.15` | Python ورژن سپورٹ میٹرکس |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ہمیں آگے کن ایجنٹس کے ساتھ ضم ہونا چاہیے |
| `is_ci` / `ci_provider` | `true` / `github_actions` | انسانی انسٹالز کو CI شور سے الگ کرنا |

**ہم کیا نہیں بھیجتے**: IP (کلاؤڈ سرور سائیڈ پر درخواست سے ملک کا کوڈ اخذ کرتا ہے، پھر IP کو ضائع کر دیتا ہے)، ہوسٹ نام، صارف نام، ورک اسپیس
پاتھ، فائل کا مواد، آپ کا api_key، آپ کا ای میل، کوئی بھی PII یا
ورک اسپیس سے متعلق چیز۔ وائر پے لوڈ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) میں قابل آڈٹ ہے۔

**آپٹ آؤٹ** (ان میں سے کوئی ایک اسے مستقل طور پر غیر فعال کر دیتا ہے):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # فی-شیل
export DO_NOT_TRACK=1                          # W3C کراس-ٹول معیار
touch ~/.clawmetry/notelemetry                 # مستقل فائل مارکر
```

یہاں نیٹ ورک کی ناکامی کبھی بھی `clawmetry` کو چلنے سے نہیں روکتی — پنگ
ایک ڈیمن تھریڈ پر 3 سیکنڈ ٹائم آؤٹ کے ساتھ فائر-اینڈ-فارگیٹ ہے۔

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## لائسنس

MIT

---

<p align="center">
  <strong>🦞 اپنے ایجنٹ کو سوچتے ہوئے دیکھیں</strong><br>
  <sub>بنایا از <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ایکو سسٹم کا حصہ</sub>
</p>
