<!-- i18n-src:8252f6b1d31d -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **14 AI ایجنٹ رن ٹائمز** کے لیے حقیقی وقت کی مانیٹرنگ: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور 10 مزید۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ہی ڈیش بورڈ۔

> 🌐 **اسے ان زبانوں میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ کوئی کنفیگریشن نہیں۔ سب کچھ خودکار طور پر پتا چل جاتا ہے۔

```bash
pip install clawmetry && clawmetry
```

یہ **http://localhost:8900** پر کھلتا ہے اور بس، کام مکمل۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

ClawMetry نے OpenClaw کی مانیٹرنگ کے طور پر آغاز کیا، اور اب یہ آپ کے **پورے ایجنٹ فلیٹ** کو ایک ڈیش بورڈ میں ناپتا ہے، جو آپ کی مشین پر ہر رن ٹائم کا خودکار پتا لگاتا ہے:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw اور NemoClaw اوپن سورس ایپ میں مفت ہیں؛ باقی رن ٹائمز ClawMetry Cloud یا سیلف ہوسٹڈ Pro لائسنس کے ساتھ فعال ہوتے ہیں۔ ہیڈر سے رن ٹائم تبدیل کریں اور ہر ٹیب یعنی لاگت، ٹوکنز، ٹولز، ٹریسز، اسی رن ٹائم کے مطابق دوبارہ ترتیب پاتا ہے۔ درست مفت/معاوضہ تقسیم، ٹئیر میٹرکس، `/api/entitlement` کی ساخت، اور `clawmetry license` CLI کے لیے **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** دیکھیں۔

## آپ کو کیا ملتا ہے

- **Flow** — ایک زندہ متحرک خاکہ جو چینلز، برین، ٹولز، اور واپس تک پیغامات کے بہاؤ کو دکھاتا ہے
- **Overview** — صحت کی جانچ، سرگرمی کا ہیٹ میپ، سیشن کی تعداد، ماڈل کی معلومات
- **Usage** — روزانہ/ہفتہ وار/ماہانہ تفصیل کے ساتھ ٹوکن اور لاگت کی ٹریکنگ
- **Sessions** — ماڈل، ٹوکنز، آخری سرگرمی کے ساتھ فعال ایجنٹ سیشنز
- **Crons** — حیثیت، اگلے رن، دورانیے کے ساتھ شیڈول شدہ جابز
- **Logs** — رنگین حقیقی وقت کی لاگ سٹریمنگ
- **Memory** — SOUL.md، MEMORY.md، AGENTS.md، روزانہ نوٹس براؤز کریں
- **Transcripts** — سیشن کی تاریخ پڑھنے کے لیے چیٹ بلبلہ UI
- **Alerts** — بجٹ کی حدیں، ایرر ریٹ ٹرگرز، ایجنٹ آف لائن کی شناخت؛ Slack، Discord، PagerDuty، Telegram، ای میل کی طرف روٹ کرتا ہے
- **Approvals** — تباہ کن ڈیلیٹس، فورس پشز، ڈیٹا بیس میوٹیشنز، sudo، پیکج انسٹالیشنز، نیٹ ورک کالز کو ایک کلک کی منظوری کے پیچھے روکیں

## سکرین شاٹس

### 🧠 Brain — لائیو ایجنٹ ایونٹ اسٹریم
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ٹوکن استعمال اور سیشن کا خلاصہ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — حقیقی وقت کی ٹول کال فیڈ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ماڈل اور سیشن کے لحاظ سے لاگت کی تفصیل
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ورک اسپیس فائل براؤزر
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — پوزیشن اور آڈٹ لاگ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — بجٹ کی حدیں، ایرر ریٹ ٹرگرز، Slack / Discord / PagerDuty / ای میل کے ویب ہکس
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — خطرناک ٹول کالز کو دستی منظوری کے پیچھے روکیں؛ پالیسی کی حمایت یافتہ حفاظتی قواعد
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code کے لیے عمل درآمد سے پہلے کی روک تھام** — ایک کمانڈ ایک
PreToolUse ہک انسٹال کرتی ہے جو میچ کرنے والی ٹول کالز کو ان کے چلنے *سے پہلے* روک دیتی ہے اور آپ کے
فیصلے کا انتظار کرتی ہے (فون سے ایک ٹیپ میں، جب
[کلاؤڈ پش نوٹیفیکیشنز](https://app.clawmetry.com/push) فعال ہوں):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ایک انکار صرف اس ایک ٹول کال کو روکتا ہے، ایجنٹ اپنا سیشن برقرار رکھتا ہے اور
کوئی اور طریقہ آزما سکتا ہے۔ اپنے فون پر منظوری دینا Claude Code کے اپنے
پرمیشن پرامپٹ کو نظرانداز کر دیتا ہے (آپ پہلے ہی جواب دے چکے ہیں)۔ نہ ملنے والے ٹولز کی قیمت تقریباً 40ms
ہوتی ہے اور وہ Claude Code کے معمول کے پرمیشن فلو میں چلے جاتے ہیں۔ آپ کو فون پر پش نوٹیفیکیشن اس وقت بھی ملتا ہے جب Claude Code خود آپ کا انتظار کر رہا ہو (`permission_prompt` /
`idle_prompt` نوٹیفیکیشنز)۔

## انسٹال

**ایک لائن (تجویز کردہ):**
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

v2 ری ایکٹ ایپ `frontend/` میں موجود ہے اور جب v2 فعال ہو کر
Flask سرور شروع کیا جائے تو یہ `/v2` پر سرو ہوتی ہے۔

ڈویلپمنٹ کے دوران دو ٹرمینلز استعمال کریں:

```bash
# Terminal 1: Flask API/server on :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# Terminal 2: Vite dev server on :5173
cd frontend
nvm use
npm ci
npm run dev
```

`http://localhost:5173/v2/` کھولیں۔ Vite `/api` درخواستوں کو
`http://localhost:8900` کی طرف پراکسی کرتا ہے، اس لیے ری ایکٹ ایپ اضافی
CORS سیٹ اپ کے بغیر مقامی Flask سرور سے بات کر سکتی ہے۔

پائتھون پیکج کے ساتھ شپ ہونے والا بنڈل بنانے کے لیے:

```bash
cd frontend
npm run build
```

پروڈکشن بنڈل `clawmetry/static/v2/dist/` میں لکھا جاتا ہے۔

## رن ٹائم / ایجنٹ کی ہم آہنگی

ClawMetry صرف OpenClaw ہی نہیں بلکہ بہت سے AI-ایجنٹ رن ٹائمز کی نگرانی کرتا ہے۔ ہر غیر-OpenClaw رن ٹائم ایک وقف شدہ ریڈر ایڈاپٹر بھیجتا ہے جو اس رن ٹائم کے مقامی سیشن فارمیٹ کو ClawMetry کی متحدہ اشکال میں تبدیل کرتا ہے؛ ڈیمن انہیں اسی DuckDB اسٹور + کلاؤڈ اسنیپ شاٹ میں شامل کرتا ہے، جو رن ٹائم کے ساتھ ٹیگ کیا جاتا ہے، اور جب ایک سے زیادہ رن ٹائمز موجود ہوں تو Session replay ٹیب ایک **رن ٹائم سوئچر** دکھاتا ہے۔ مکمل میٹرکس + رن ٹائمز شامل کرنے کی گائیڈ کے لیے [`docs/compatibility.md`](docs/compatibility.md) اور OpenClaw-فیملی کے تعارف کے لیے [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) دیکھیں۔

| رن ٹائم / ایجنٹ | حیثیت | نوٹس |
|---|---|---|
| **OpenClaw** | مقامی | حوالہ رن ٹائم، خودکار پتا لگایا جاتا ہے |
| **PicoClaw** | بیٹا ایڈاپٹر | فلیٹ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)۔ ٹرانسکرپٹس، ماڈل، ٹول کالز۔ |
| **NanoClaw** | بیٹا ایڈاپٹر | فی سیشن SQLite (`data/v2-sessions`)۔ ٹرانسکرپٹس + پیغامات کی گنتی۔ |
| **Hermes** | بیٹا ایڈاپٹر | SQLite `~/.hermes/state.db`۔ ٹرانسکرپٹس، ماڈل، ٹوکنز/لاگت۔ |
| **Claude Code** | بیٹا ایڈاپٹر | JSONL `~/.claude/projects/.../<id>.jsonl`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز + تھنکنگ، ٹوکن استعمال۔ |
| **Codex** | بیٹا ایڈاپٹر | رول آؤٹ JSONL `~/.codex/sessions/...`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Cursor** | بیٹا ایڈاپٹر | SQLite `state.vscdb`۔ چیٹ/کمپوزر ٹرانسکرپٹس، ماڈل۔ |
| **Aider** | بیٹا ایڈاپٹر | فی پراجیکٹ `.aider.chat.history.md`۔ ٹرانسکرپٹس، ماڈل، ٹوکن کی گنتی۔ |
| **Goose** | بیٹا ایڈاپٹر | SQLite `~/.local/share/goose`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، کل ٹوکنز۔ |
| **opencode** | بیٹا ایڈاپٹر | SQLite `~/.local/share/opencode`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Qwen Code** | بیٹا ایڈاپٹر | JSONL `~/.qwen/projects/.../chats`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Pi** | بیٹا ایڈاپٹر | JSONL `~/.pi/agent/sessions`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Deep Agents** | بیٹا ایڈاپٹر | SQLite `~/.deepagents/.state/sessions.db`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **n8n** | بیٹا ایڈاپٹر | SQLite `~/.n8n/database.sqlite`۔ ورک فلو ایگزیکیوشنز، نوڈ رنز، AI Agent پرامپٹس، ماڈل + ٹوکنز جہاں n8n انہیں ریکارڈ کرتا ہے۔ |

"بیٹا ایڈاپٹر" کا مطلب ہے کہ ClawMetry اس رن ٹائم کے حقیقی آن ڈسک فارمیٹ کے لیے ایک ریڈر بھیجتا ہے، ہر ایک کو ایک حقیقی مشین پر حقیقی انسٹال کے خلاف بنایا اور تصدیق کیا گیا ہے (دیکھیں `tests/fixtures/runtimes/<rt>/`)۔ ایڈاپٹرز صرف پڑھنے کے لیے ہیں؛ ہر ایک اس بارے میں دیانتدار ہے کہ اس کا رن ٹائم اصل میں کیا ذخیرہ کرتا ہے (مثلاً PicoClaw/NanoClaw/Cursor ٹوکن کی لاگت ڈسک پر نہیں لکھتے)۔ جب ایک نوڈ پر کئی رن ٹائمز چلتے ہوں، تو رن ٹائم سوئچر sessions ویو کو ایک صاف ڈیپ ڈائیو کے لیے ایک ہی رن ٹائم تک محدود کر دیتا ہے۔

## کسی بھی SDK ایجنٹ کو ٹریک کریں — آؤٹ-لوپ لاگت کی نسبت

اوپر دیے گئے رن ٹائمز سب سیشنز کو ڈسک پر لکھتے ہیں۔ آپ کا اپنا **پروڈکشن ایجنٹ** — جو آپ نے OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B، یا ایک عام `httpx` لوپ پر بنایا ہے — ایسا نہیں کرتا۔ ClawMetry کا زیرو-کنفیگ انٹرسیپٹر `httpx`/`requests` کو مانکی-پیچ کر کے پھر بھی اس کی LLM کالز (لاگت، ٹوکنز، لیٹنسی، ایررز) کیپچر کرتا ہے:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا `CLAWMETRY_SOURCE=support-agent` ماحولیاتی ویری ایبل) ہر کال کو ایک **نامزد سورس** کے ساتھ ٹیگ کرتا ہے، اس لیے آپ کا چلایا ہوا ہر پروڈکٹ Overview کے **🔌 آؤٹ-لوپ سورسز** کارڈ میں اپنی الگ، لاگت کی نسبت والی لائن کے طور پر ظاہر ہوتا ہے — فی ایجنٹ کالز، پرووائیڈرز، لیٹنسی، ایرر ریٹ۔ اگر کوئی سورس سیٹ نہ کیا جائے؟ کالز اب بھی ٹریک ہوتی رہتی ہیں، بس کارڈ چھپا رہتا ہے۔

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

یہ وہی ڈیٹا لیئر ہے جو رن ٹائم ایڈاپٹرز کو کھلاتی ہے (DuckDB → کلاؤڈ اسنیپ شاٹ)، اس لیے آؤٹ-لوپ سورسز بھی باقی سب کچھ کی طرح، اینڈ-ٹو-اینڈ خفیہ کاری کے ساتھ، کلاؤڈ ڈیش بورڈ کے ساتھ ہم آہنگ ہوتے ہیں۔

## OpenTelemetry — وینڈر-نیوٹرل، اپنے ٹریسز کہیں بھی بھیجیں

ClawMetry دونوں سمتوں میں **OpenTelemetry** بولتا ہے، **GenAI سیمینٹک کنونشنز** استعمال کرتے ہوئے، تاکہ آپ کے ایجنٹ ٹریسز کبھی بھی ایک ہی ٹول تک محدود نہ ہوں۔

ہر سیشن کو **ایکسپورٹ** کریں — LLM کالز، ٹولز، سب-ایجنٹس، ٹوکنز، لاگت — کسی بھی کلیکٹر (Datadog، Grafana، Honeycomb، یا اپنے خود کے OTel Collector) کو OTLP/HTTP GenAI اسپینز کے طور پر:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

اتھ ہیڈرز اور پول انٹرول اختیاری ماحولیاتی ویری ایبلز ہیں:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**ان جیسٹ** — بلٹ-اِن OTLP ریسیور `/v1/traces` اور `/v1/metrics` پر کہیں اور سے ٹریسز اور میٹرکس قبول کرتا ہے (پروٹو بف ان جیسٹ کے لیے `pip install clawmetry[otel]`)۔

آپ کو زیرو-کنفیگ، لوکل-فرسٹ ClawMetry ڈیش بورڈ **اور** آپ کی ٹیم پہلے سے چلانے والے کسی بھی بیک اینڈ میں آپ کا ڈیٹا ملتا ہے — نہ کوئی لاک-اِن، نہ کوئی دوسرا ایجنٹ انسٹال کرنے کی ضرورت۔

## کنفیگریشن

زیادہ تر لوگوں کو کسی کنفیگ کی ضرورت نہیں۔ ClawMetry خود بخود آپ کے ورک اسپیس، لاگز، سیشنز، اور crons کا پتا لگا لیتا ہے۔

اگر آپ کو کسٹمائز کرنے کی ضرورت ہو:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

تمام آپشنز: `clawmetry --help`

## معاون چینلز

ClawMetry آپ کے کنفیگر کردہ ہر OpenClaw چینل کے لیے لائیو سرگرمی دکھاتا ہے۔ صرف وہی چینلز جو آپ کے `openclaw.json` میں واقعی سیٹ اپ ہیں Flow خاکے میں ظاہر ہوتے ہیں؛ غیر کنفیگر شدہ چینلز خودکار طور پر چھپے رہتے ہیں۔

Flow میں کسی بھی چینل نوڈ پر کلک کریں تاکہ آنے والے/جانے والے پیغامات کی گنتی کے ساتھ ایک لائیو چیٹ بلبلہ ویو دیکھ سکیں۔

| چینل | حیثیت | لائیو پاپ اپ | نوٹس |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ مکمل | ✅ | پیغامات، اعداد و شمار، 10s ریفریش |
| 💬 **iMessage** | ✅ مکمل | ✅ | `~/Library/Messages/chat.db` براہ راست پڑھتا ہے |
| 💚 **WhatsApp** | ✅ مکمل | ✅ | WhatsApp Web (Baileys) کے ذریعے |
| 🔵 **Signal** | ✅ مکمل | ✅ | signal-cli کے ذریعے |
| 🟣 **Discord** | ✅ مکمل | ✅ | Guild + چینل کی شناخت |
| 🟪 **Slack** | ✅ مکمل | ✅ | Workspace + چینل کی شناخت |
| 🌐 **Webchat** | ✅ مکمل | ✅ | بلٹ-اِن ویب UI سیشنز |
| 📡 **IRC** | ✅ مکمل | ✅ | ٹرمینل طرز کا بلبلہ UI |
| 🍏 **BlueBubbles** | ✅ مکمل | ✅ | BlueBubbles REST API کے ذریعے iMessage |
| 🔵 **Google Chat** | ✅ مکمل | ✅ | Chat API webhooks کے ذریعے |
| 🟣 **MS Teams** | ✅ مکمل | ✅ | Teams bot پلگ اِن کے ذریعے |
| 🔷 **Mattermost** | ✅ مکمل | ✅ | سیلف-ہوسٹڈ ٹیم چیٹ |
| 🟩 **Matrix** | ✅ مکمل | ✅ | غیر مرکزی، E2EE سپورٹ |
| 🟢 **LINE** | ✅ مکمل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ مکمل | ✅ | غیر مرکزی NIP-04 DMs |
| 🟣 **Twitch** | ✅ مکمل | ✅ | IRC کنکشن کے ذریعے چیٹ |
| 🔷 **Feishu/Lark** | ✅ مکمل | ✅ | WebSocket ایونٹ سبسکرپشن |
| 🔵 **Zalo** | ✅ مکمل | ✅ | Zalo Bot API |

> **خودکار شناخت:** ClawMetry آپ کا `~/.openclaw/openclaw.json` پڑھتا ہے اور صرف وہی چینلز رینڈر کرتا ہے جو آپ نے واقعی کنفیگر کیے ہیں۔ کسی دستی سیٹ اپ کی ضرورت نہیں۔

## Docker ڈیپلائمنٹ

ClawMetry کو کنٹینر میں چلانا چاہتے ہیں؟ کوئی مسئلہ نہیں! 🐳

**Docker کے ساتھ فوری آغاز:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or mount your agent's data dir (shown: OpenClaw's ~/.openclaw)
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

> **نوٹ:** Docker میں چلاتے وقت، اپنے ایجنٹ کی ڈیٹا + لاگ ڈائریکٹریز (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) کو ماؤنٹ کریں تاکہ ClawMetry آپ کا سیٹ اپ خود بخود پتا لگا سکے۔

## ضروریات

- Python 3.8+
- Flask (pip کے ذریعے خود بخود انسٹال ہوتا ہے)
- ایک AI ایجنٹ رن ٹائم اسی مشین پر: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، یا n8n (یا Docker کے لیے ماؤنٹڈ والیومز)
- Linux یا macOS

## NemoClaw / OpenShell سپورٹ

ClawMetry خود بخود [NemoClaw](https://github.com/NVIDIA/NemoClaw) کا پتا لگاتا ہے — یہ NVIDIA کا انٹرپرائز سیکیورٹی ریپر ہے جو OpenClaw کے لیے ہے اور ایجنٹس کو سینڈ باکسڈ OpenShell کنٹینرز کے اندر چلاتا ہے۔

زیادہ تر صورتوں میں کسی اضافی کنفیگریشن کی ضرورت نہیں۔ سنک ڈیمن خود بخود سیشن فائلوں کو دریافت کرتا ہے چاہے وہ ہوسٹ پر `~/.openclaw/` میں ہوں یا کسی OpenShell کنٹینر کے اندر۔

### یہ کیسے کام کرتا ہے

ClawMetry دو طریقوں سے NemoClaw کا پتا لگاتا ہے:

1. **بائنری کی شناخت** — `nemoclaw` CLI کی جانچ کرتا ہے اور سینڈ باکس کی معلومات حاصل کرنے کے لیے `nemoclaw status` چلاتا ہے
2. **کنٹینر کی شناخت** — چلتے ہوئے Docker کنٹینرز کو `openshell`، `nemoclaw`، یا `ghcr.io/nvidia/` امیجز کے لیے اسکین کرتا ہے، پھر والیوم ماؤنٹس یا `docker cp` کے ذریعے سیشنز پڑھتا ہے

NemoClaw کنٹینرز سے سنک شدہ سیشن فائلوں کو کلاؤڈ ڈیش بورڈ میں `runtime=nemoclaw` اور `container_id` میٹا ڈیٹا کے ساتھ ٹیگ کیا جاتا ہے، تاکہ آپ انہیں معیاری OpenClaw سیشنز سے فوری طور پر الگ پہچان سکیں۔

### تجویز کردہ سیٹ اپ: HOST پر سنک ڈیمن

بہترین تجربے کے لیے، ClawMetry کا سنک ڈیمن **ہوسٹ مشین** پر چلائیں (سینڈ باکس کے اندر نہیں)۔ اس سے NemoClaw کی نیٹ ورک پالیسی کی پابندیوں سے بچا جا سکتا ہے۔

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سنک ڈیمن کسی بھی چلتے ہوئے OpenShell کنٹینر کے اندر سیشنز کو خود بخود ڈھونڈ لے گا۔

### اختیاری: واضح سینڈ باکس نام

اگر خودکار شناخت کام نہ کرے، تو ClawMetry کو صحیح سینڈ باکس کی طرف اشارہ کریں:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### سینڈ باکس کے اندر چلانا (ایڈوانسڈ)

اگر آپ کو سنک ڈیمن **سینڈ باکس کے اندر** چلانا ضروری ہو، تو اپنی NemoClaw نیٹ ورک پالیسی میں یہ ایگریس رول شامل کریں تاکہ یہ ClawMetry ingest API تک پہنچ سکے:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

اس طرح لاگو کریں:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### پورٹس اور اینڈ پوائنٹس

| اینڈ پوائنٹ | پورٹ | پروٹوکول | ضروری |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ہاں (سنک ڈیمن → کلاؤڈ) |
| `localhost:8900` | 8900 | HTTP | ہاں (مقامی ڈیش بورڈ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | کنٹینر سیشن کی دریافت کے لیے |

سنک ڈیمن صرف `ingest.clawmetry.com` کو آؤٹ باؤنڈ HTTPS کالز کرتا ہے۔ کوئی ان باؤنڈ پورٹس درکار نہیں۔

---

## کلاؤڈ ڈیپلائمنٹ

SSH ٹنلز، ریورس پراکسی، اور Docker کے لیے **[کلاؤڈ ٹیسٹنگ گائیڈ](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** دیکھیں۔

## ٹیسٹنگ

یہ پراجیکٹ BrowserStack کے ساتھ ٹیسٹ کیا جاتا ہے۔

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ٹیلی میٹری

ClawMetry گمنام install-lifecycle پنگز
`https://app.clawmetry.com/api/install` کو بھیجتا ہے: ایک نئی مشین پر پہلی بار
`clawmetry` CLI چلانے پر ایک `install` پنگ، ایک نئے ورژن میں اپ گریڈ کرنے کے بعد پہلی
رن پر ایک `update` پنگ، اور جب آپ ان-ڈیش بورڈ آن بورڈنگ کا انتخاب مکمل کرتے ہیں تو ایک
`onboarded` پنگ۔ ہم اسے حقیقی انسٹالز گننے کے لیے استعمال کرتے ہیں (خام PyPI ڈاؤن لوڈ
تعداد تقریباً 98% میررز، CI، اور آٹو-اپ ڈیٹ ری-ڈاؤن لوڈز کی ہوتی ہے) اور یہ جاننے کے لیے کہ
عملی طور پر کون سے ایجنٹ فریم ورکس اور ورژنز استعمال ہو رہے ہیں۔

**فی لائف سائیکل ایونٹ فی ورژن زیادہ سے زیادہ ایک POST**، جس میں شامل ہے:

| فیلڈ | مثال | کیوں |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` پر محفوظ رینڈم UUID | ڈی ڈپلیکیشن؛ گمنام جب تک آپ واضح طور پر Cloud sync سے منسلک نہ ہوں (اس کے بعد authenticated ڈیمن heartbeat اسے لے جاتا ہے، اس انسٹال کو آپ کے اکاؤنٹ سے جوڑتا ہے) |
| `event` | `install` / `update` / `onboarded` | نیا انسٹال بمقابلہ موجودہ کا اپ گریڈ |
| `version` | `0.12.167` | کون سے ورژنز استعمال میں ہیں |
| `os` / `os_version` | `Darwin` / `25.3.0` | پلیٹ فارم سپورٹ کی ترجیحات |
| `python` | `3.11.15` | Python ورژن سپورٹ میٹرکس |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ہمیں آگے کن ایجنٹس کے ساتھ انٹیگریٹ کرنا چاہیے |
| `is_ci` / `ci_provider` | `true` / `github_actions` | انسانی انسٹالز کو CI شور سے الگ کرنا |

**ہم کیا نہیں بھیجتے**: IP (کلاؤڈ سرور کی سائیڈ پر درخواست سے ملک کا کوڈ نکالتا ہے،
پھر IP کو ضائع کر دیتا ہے)، ہوسٹ نیم، یوزر نیم، ورک اسپیس
پاتھ، فائل کا مواد، آپ کی api_key، آپ کی ای میل، کوئی بھی PII یا
ورک اسپیس سے متعلق چیز۔ وائر پے لوڈ کی
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) میں آڈٹ کی جا سکتی ہے۔

**آپٹ آؤٹ** (ان میں سے کوئی بھی ایک اسے مستقل طور پر غیر فعال کر دیتا ہے):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

یہاں ایک نیٹ ورک ناکامی کبھی بھی `clawmetry` کو چلنے سے نہیں روکتی؛ یہ
پنگ ایک ڈیمن تھریڈ پر فائر-اینڈ-فارگیٹ ہے جس کا ٹائم آؤٹ 3 سیکنڈ ہے۔

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
  <sub>بنایا گیا <a href="https://github.com/vivekchand">@vivekchand</a> کی طرف سے · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ایکو سسٹم کا حصہ</sub>
</p>
