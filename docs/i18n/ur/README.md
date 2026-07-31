<!-- i18n-src:02b789586c7d -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **14 AI ایجنٹ رن ٹائمز** کے لیے ریئل ٹائم آبزرویبیلٹی: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور 10 مزید۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ہی ڈیش بورڈ۔

> 🌐 **اسے اس زبان میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید ←](docs/i18n/)

ایک کمانڈ۔ صفر کنفیگریشن۔ سب کچھ خود بخود پتہ چل جاتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے اور بس، کام مکمل۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

ClawMetry کا آغاز OpenClaw کے لیے آبزرویبیلٹی کے طور پر ہوا تھا، اور اب یہ ایک ہی ڈیش بورڈ میں آپ کے **پورے ایجنٹ فلیٹ** کی پیمائش کرتا ہے، آپ کی مشین پر ہر رن ٹائم کا خود بخود پتہ لگاتے ہوئے:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw اور NemoClaw اوپن سورس ایپ میں مفت ہیں؛ باقی رن ٹائمز ClawMetry Cloud یا سیلف ہوسٹڈ Pro لائسنس کے ساتھ فعال ہوتے ہیں۔ ہیڈر سے رن ٹائم تبدیل کریں اور ہر ٹیب، لاگت، ٹوکنز، ٹولز، ٹریسز، اسی رن ٹائم کے دائرہ کار میں آ جاتا ہے۔ درست مفت/ادا شدہ تقسیم، ٹیئر میٹرکس، `/api/entitlement` شکل، اور `clawmetry license` CLI کے لیے **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** دیکھیں۔

## آپ کو کیا ملتا ہے

- **Flow**: چینلز، برین، ٹولز کے ذریعے بہتے اور واپس آتے پیغامات دکھانے والا لائیو اینیمیٹڈ ڈایاگرام
- **Overview**: ہیلتھ چیکس، ایکٹیویٹی ہیٹ میپ، سیشن گنتی، ماڈل کی معلومات
- **Usage**: روزانہ/ہفتہ وار/ماہانہ تفصیل کے ساتھ ٹوکن اور لاگت ٹریکنگ
- **Sessions**: ماڈل، ٹوکنز، آخری سرگرمی کے ساتھ فعال ایجنٹ سیشنز
- **Crons**: حیثیت، اگلا رن، دورانیہ کے ساتھ شیڈول شدہ jobs
- **Logs**: رنگ کوڈڈ ریئل ٹائم لاگ سٹریمنگ
- **Memory**: SOUL.md، MEMORY.md، AGENTS.md، روزانہ کے نوٹس براؤز کریں
- **Transcripts**: سیشن ہسٹریز پڑھنے کے لیے چیٹ بلبلہ UI
- **Alerts**: بجٹ کیپس، ایرر ریٹ ٹرگرز، ایجنٹ آف لائن شناخت؛ Slack، Discord، PagerDuty، Telegram، Email کی طرف روٹ کرتا ہے
- **Approvals**: تباہ کن ڈیلیٹس، فورس پشز، DB میوٹیشنز، sudo، پیکج انسٹالیشنز، نیٹ ورک کالز کو ون کلک منظوری کے پیچھے روکنا

## سکرین شاٹس

### 🧠 Brain: لائیو ایجنٹ ایونٹ سٹریم
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview: ٹوکن استعمال اور سیشن خلاصہ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow: ریئل ٹائم ٹول کال فیڈ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens: ماڈل اور سیشن کے لحاظ سے لاگت کی تفصیل
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory: ورک اسپیس فائل براؤزر
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security: پوسچر اور آڈٹ لاگ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts: بجٹ کیپس، ایرر ریٹ ٹرگرز، Slack / Discord / PagerDuty / Email کے لیے ویب ہکس
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals: خطرناک ٹول کالز کو دستی منظوری کے پیچھے روکنا؛ پالیسی پر مبنی تحفظ کے اصول
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code کے لیے پری ایگزیکیوشن بلاکنگ**: ایک کمانڈ ایک PreToolUse ہک انسٹال کرتی ہے جو ملتی جلتی ٹول کالز کو ان کے چلنے *سے پہلے* روک دیتی ہے اور آپ کے فیصلے کا انتظار کرتی ہے (اگر [کلاؤڈ پش نوٹیفیکیشنز](https://app.clawmetry.com/push) فعال ہوں تو آپ کے فون سے صرف ایک ٹیپ کافی ہے):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ایک ڈینائے صرف اس ایک ٹول کال کو روکتی ہے، ایجنٹ اپنا سیشن برقرار رکھتا ہے اور کوئی دوسرا طریقہ آزما سکتا ہے۔ اپنے فون پر منظوری دینے سے Claude Code کا اپنا پرمیشن پرامپٹ نظرانداز ہو جاتا ہے (آپ پہلے ہی جواب دے چکے ہیں)۔ نہ ملنے والے ٹولز کی قیمت تقریباً 40ms ہوتی ہے اور وہ Claude Code کے عام پرمیشن فلو میں چلے جاتے ہیں۔ جب Claude Code خود آپ کے جواب کا منتظر ہو تو آپ کو فون پر پش نوٹیفیکیشن بھی ملتا ہے (`permission_prompt` / `idle_prompt` نوٹیفیکیشنز)۔

## انسٹال کریں

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

v2 React ایپ `frontend/` میں موجود ہے اور جب Flask سرور کو v2 فعال کر کے شروع کیا جاتا ہے تو یہ `/v2` پر سرو ہوتی ہے۔

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

`http://localhost:5173/v2/` کھولیں۔ Vite `/api` درخواستوں کو `http://localhost:8900` پر پراکسی کرتا ہے، تاکہ React ایپ اضافی CORS سیٹ اپ کے بغیر مقامی Flask سرور سے بات کر سکے۔

Python پیکج کے ساتھ بھیجے جانے والا بنڈل بنانے کے لیے:

```bash
cd frontend
npm run build
```

پروڈکشن بنڈل `clawmetry/static/v2/dist/` میں لکھا جاتا ہے۔

## رن ٹائم / ایجنٹ مطابقت

ClawMetry صرف OpenClaw ہی نہیں بلکہ بہت سے AI ایجنٹ رن ٹائمز کا مشاہدہ کرتا ہے۔ ہر غیر OpenClaw رن ٹائم کے ساتھ ایک مخصوص ریڈر اڈاپٹر آتا ہے جو اس کے مقامی سیشن فارمیٹ کو ClawMetry کی یکساں شکلوں میں تبدیل کرتا ہے؛ ڈیمن انہیں اسی DuckDB اسٹور + کلاؤڈ سنیپ شاٹ میں شامل کرتا ہے، رن ٹائم کے ساتھ ٹیگ کیا ہوا، اور جب ایک سے زیادہ رن ٹائمز موجود ہوں تو Session replay ٹیب ایک **رن ٹائم سوئچر** دکھاتا ہے۔ مکمل میٹرکس اور رن ٹائمز شامل کرنے کی گائیڈ کے لیے [`docs/compatibility.md`](docs/compatibility.md) دیکھیں، اور OpenClaw فیملی کے تعارف کے لیے [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) دیکھیں۔

| رن ٹائم / ایجنٹ | حیثیت | نوٹس |
|---|---|---|
| **OpenClaw** | نیٹو | حوالہ رن ٹائم، خود بخود پتہ چلایا جاتا ہے |
| **PicoClaw** | بیٹا اڈاپٹر | فلیٹ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)۔ ٹرانسکرپٹس، ماڈل، ٹول کالز۔ |
| **NanoClaw** | بیٹا اڈاپٹر | فی سیشن SQLite (`data/v2-sessions`)۔ ٹرانسکرپٹس + پیغامات کی تعداد۔ |
| **Hermes** | بیٹا اڈاپٹر | SQLite `~/.hermes/state.db`۔ ٹرانسکرپٹس، ماڈل، ٹوکنز/لاگت۔ |
| **Claude Code** | بیٹا اڈاپٹر | JSONL `~/.claude/projects/.../<id>.jsonl`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز + thinking، ٹوکن استعمال۔ |
| **Codex** | بیٹا اڈاپٹر | رول آؤٹ JSONL `~/.codex/sessions/...`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Cursor** | بیٹا اڈاپٹر | SQLite `state.vscdb`۔ چیٹ/کمپوزر ٹرانسکرپٹس، ماڈل۔ |
| **Aider** | بیٹا اڈاپٹر | فی پراجیکٹ `.aider.chat.history.md`۔ ٹرانسکرپٹس، ماڈل، ٹوکن گنتی۔ |
| **Goose** | بیٹا اڈاپٹر | SQLite `~/.local/share/goose`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، کل ٹوکنز۔ |
| **opencode** | بیٹا اڈاپٹر | SQLite `~/.local/share/opencode`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Qwen Code** | بیٹا اڈاپٹر | JSONL `~/.qwen/projects/.../chats`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Pi** | بیٹا اڈاپٹر | JSONL `~/.pi/agent/sessions`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Deep Agents** | بیٹا اڈاپٹر | SQLite `~/.deepagents/.state/sessions.db`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **n8n** | بیٹا اڈاپٹر | SQLite `~/.n8n/database.sqlite`۔ ورک فلو ایگزیکیوشنز، نوڈ رنز، AI Agent پرامپٹس، ماڈل + ٹوکنز جہاں n8n انہیں ریکارڈ کرتا ہے۔ |
| **Antigravity** | بیٹا اڈاپٹر | `~/.gemini/<flavor>/brain/` کے تحت Brain JSONL۔ گفتگو، ٹول اسٹیپس، thinking، فی جنریشن Gemini ٹوکن تقسیم + لاگت، بیک گراؤنڈ جنریشن خرچ۔ |

"بیٹا اڈاپٹر" کا مطلب ہے کہ ClawMetry اس رن ٹائم کے اصل آن ڈسک فارمیٹ کے لیے ایک ریڈر بھیجتا ہے، جسے ایک حقیقی مشین پر ایک حقیقی انسٹال کے خلاف بنایا اور تصدیق کیا گیا ہے (دیکھیں `tests/fixtures/runtimes/<rt>/`)۔ اڈاپٹرز صرف پڑھنے کے لیے ہیں؛ ہر ایک اس بارے میں دیانتدار ہے کہ اس کا رن ٹائم اصل میں کیا محفوظ کرتا ہے (مثلاً PicoClaw/NanoClaw/Cursor ٹوکن لاگت ڈسک پر نہیں لکھتے)۔ جب ایک نوڈ پر کئی رن ٹائمز چل رہے ہوں تو رن ٹائم سوئچر صاف ستھرے گہرے جائزے کے لیے سیشنز ویو کو ایک ہی رن ٹائم تک محدود کر دیتا ہے۔

## کسی بھی SDK ایجنٹ کو ٹریک کریں: آؤٹ لوپ کاسٹ اٹریبیوشن

اوپر دیے گئے تمام رن ٹائمز سیشنز ڈسک پر لکھتے ہیں۔ آپ کا اپنا **پروڈکشن ایجنٹ**، وہ جو آپ نے OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B، یا محض ایک `httpx` لوپ پر بنایا ہے، ایسا نہیں کرتا۔ ClawMetry کا زیرو کنفیگ انٹرسیپٹر پھر بھی `httpx`/`requests` کو مونکی پیچ کر کے اس کی LLM کالز (لاگت، ٹوکنز، لیٹنسی، ایررز) کیپچر کر لیتا ہے:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا `CLAWMETRY_SOURCE=support-agent` env var) ہر کال کو ایک **نامزد سورس** کے ساتھ ٹیگ کرتا ہے، تاکہ آپ کا چلایا ہوا ہر پروڈکٹ Overview پر ڈیش بورڈ کے **🔌 Out-loop sources** کارڈ میں اپنی ایک الگ، کاسٹ اٹریبیوٹ ایبل لائن کے طور پر نظر آئے: کالز، پرووائیڈرز، لیٹنسی، فی ایجنٹ ایرر ریٹ۔ کوئی سورس سیٹ نہیں کیا؟ کالز پھر بھی ٹریک ہوتی رہتی ہیں؛ صرف کارڈ چھپا رہتا ہے۔

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

یہ وہی ڈیٹا لیئر ہے جسے رن ٹائم اڈاپٹرز فیڈ کرتے ہیں (DuckDB → کلاؤڈ سنیپ شاٹ)، لہٰذا آؤٹ لوپ سورسز بھی باقی سب کچھ کی طرح کلاؤڈ ڈیش بورڈ سے سنک ہوتے ہیں، E2E انکرپٹڈ۔

## OpenTelemetry: وینڈر نیوٹرل، اپنے ٹریسز کہیں بھی بھیجیں

ClawMetry دونوں سمتوں میں **OpenTelemetry** بولتا ہے، **GenAI سیمینٹک کنونشنز** استعمال کرتے ہوئے، تاکہ آپ کے ایجنٹ ٹریسز کبھی بھی کسی ایک ٹول تک محدود نہ ہوں۔

**ایکسپورٹ**: ہر سیشن، LLM کالز، ٹولز، سب ایجنٹس، ٹوکنز، لاگت، کو کسی بھی کلیکٹر (Datadog، Grafana، Honeycomb، یا آپ کا اپنا OTel Collector) کے لیے OTLP/HTTP GenAI اسپینز کے طور پر بھیجیں:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

آتھ ہیڈرز اور پول انٹرول اختیاری env vars ہیں:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**انجیسٹ**: بلٹ اِن OTLP ریسیور `/v1/traces` اور `/v1/metrics` پر کسی بھی دوسری چیز سے ٹریسز اور میٹرکس قبول کرتا ہے (پروٹو بف انجیسٹ کے لیے `pip install clawmetry[otel]`)۔

آپ کو زیرو کنفیگ، لوکل فرسٹ ClawMetry ڈیش بورڈ **اور** آپ کا ڈیٹا اس بیک اینڈ میں بھی ملتا ہے جو آپ کی ٹیم پہلے سے چلا رہی ہے، نہ کوئی لاک اِن، نہ کوئی دوسرا ایجنٹ انسٹال کرنے کی ضرورت۔

## کنفیگریشن

زیادہ تر لوگوں کو کسی کنفیگریشن کی ضرورت نہیں ہوتی۔ ClawMetry آپ کے ورک اسپیس، لاگز، سیشنز، اور crons کا خود بخود پتہ لگا لیتا ہے۔

اگر آپ کو حسب ضرورت بنانے کی ضرورت ہو تو:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

تمام آپشنز: `clawmetry --help`

## سپورٹڈ چینلز

ClawMetry آپ کے کنفیگر کردہ ہر OpenClaw چینل کے لیے لائیو سرگرمی دکھاتا ہے۔ صرف وہ چینلز جو واقعی آپ کے `openclaw.json` میں سیٹ اپ ہیں Flow ڈایاگرام میں نظر آتے ہیں، غیر کنفیگرڈ چینلز خود بخود چھپ جاتے ہیں۔

آنے والے/جانے والے پیغامات کی تعداد کے ساتھ لائیو چیٹ بلبلہ ویو دیکھنے کے لیے Flow میں کسی بھی چینل نوڈ پر کلک کریں۔

| چینل | حیثیت | لائیو پاپ اپ | نوٹس |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ مکمل | ✅ | پیغامات، اعداد و شمار، 10s ریفریش |
| 💬 **iMessage** | ✅ مکمل | ✅ | `~/Library/Messages/chat.db` کو براہ راست پڑھتا ہے |
| 💚 **WhatsApp** | ✅ مکمل | ✅ | WhatsApp Web (Baileys) کے ذریعے |
| 🔵 **Signal** | ✅ مکمل | ✅ | signal-cli کے ذریعے |
| 🟣 **Discord** | ✅ مکمل | ✅ | گلڈ + چینل کی شناخت |
| 🟪 **Slack** | ✅ مکمل | ✅ | ورک اسپیس + چینل کی شناخت |
| 🌐 **Webchat** | ✅ مکمل | ✅ | بلٹ اِن ویب UI سیشنز |
| 📡 **IRC** | ✅ مکمل | ✅ | ٹرمینل طرز کا بلبلہ UI |
| 🍏 **BlueBubbles** | ✅ مکمل | ✅ | BlueBubbles REST API کے ذریعے iMessage |
| 🔵 **Google Chat** | ✅ مکمل | ✅ | Chat API ویب ہکس کے ذریعے |
| 🟣 **MS Teams** | ✅ مکمل | ✅ | Teams بوٹ پلگ اِن کے ذریعے |
| 🔷 **Mattermost** | ✅ مکمل | ✅ | سیلف ہوسٹڈ ٹیم چیٹ |
| 🟩 **Matrix** | ✅ مکمل | ✅ | غیر مرکزی، E2EE سپورٹ |
| 🟢 **LINE** | ✅ مکمل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ مکمل | ✅ | غیر مرکزی NIP-04 DMs |
| 🟣 **Twitch** | ✅ مکمل | ✅ | IRC کنکشن کے ذریعے چیٹ |
| 🔷 **Feishu/Lark** | ✅ مکمل | ✅ | WebSocket ایونٹ سبسکرپشن |
| 🔵 **Zalo** | ✅ مکمل | ✅ | Zalo Bot API |

> **خودکار شناخت:** ClawMetry آپ کا `~/.openclaw/openclaw.json` پڑھتا ہے اور صرف وہی چینلز رینڈر کرتا ہے جو آپ نے واقعی کنفیگر کیے ہیں۔ کسی دستی سیٹ اپ کی ضرورت نہیں۔

## Docker ڈپلائمنٹ

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

> **نوٹ:** Docker میں چلاتے وقت، اپنے ایجنٹ کی ڈیٹا + لاگ ڈائریکٹریز (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) کو ماؤنٹ کریں تاکہ ClawMetry آپ کے سیٹ اپ کا خود بخود پتہ لگا سکے۔

## تقاضے

- Python 3.8+
- Flask (pip کے ذریعے خود بخود انسٹال ہوتا ہے)
- اسی مشین پر ایک AI ایجنٹ رن ٹائم: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، n8n، یا Antigravity (یا Docker کے لیے ماؤنٹڈ والیومز)
- Linux یا macOS

## NemoClaw / OpenShell سپورٹ

ClawMetry خود بخود [NemoClaw](https://github.com/NVIDIA/NemoClaw) کا پتہ لگاتا ہے: NVIDIA کا OpenClaw کے لیے انٹرپرائز سکیورٹی ریپر جو ایجنٹس کو سینڈ باکسڈ OpenShell کنٹینرز کے اندر چلاتا ہے۔

زیادہ تر معاملات میں کسی اضافی کنفیگریشن کی ضرورت نہیں ہوتی۔ سنک ڈیمن سیشن فائلوں کو خود بخود دریافت کر لیتا ہے، چاہے وہ ہوسٹ پر `~/.openclaw/` میں ہوں یا کسی OpenShell کنٹینر کے اندر۔

### یہ کیسے کام کرتا ہے

ClawMetry دو طریقوں سے NemoClaw کا پتہ لگاتا ہے:

1. **بائنری شناخت**: `nemoclaw` CLI کی موجودگی چیک کرتا ہے اور سینڈ باکس کی معلومات حاصل کرنے کے لیے `nemoclaw status` چلاتا ہے
2. **کنٹینر شناخت**: چلتے ہوئے Docker کنٹینرز کو `openshell`، `nemoclaw`، یا `ghcr.io/nvidia/` امیجز کے لیے اسکین کرتا ہے، پھر والیوم ماؤنٹس یا `docker cp` کے ذریعے سیشنز پڑھتا ہے

NemoClaw کنٹینرز سے سنک کی گئی سیشن فائلوں کو کلاؤڈ ڈیش بورڈ میں `runtime=nemoclaw` اور `container_id` میٹا ڈیٹا کے ساتھ ٹیگ کیا جاتا ہے، تاکہ آپ انہیں معیاری OpenClaw سیشنز سے ایک نظر میں الگ پہچان سکیں۔

### تجویز کردہ سیٹ اپ: HOST پر سنک ڈیمن

بہترین تجربے کے لیے، ClawMetry کا سنک ڈیمن **ہوسٹ مشین** پر چلائیں (سینڈ باکس کے اندر نہیں)۔ اس سے NemoClaw کی نیٹ ورک پالیسی پابندیوں سے بچا جا سکتا ہے۔

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سنک ڈیمن کسی بھی چلتے ہوئے OpenShell کنٹینر کے اندر موجود سیشنز کو خود بخود ڈھونڈ لے گا۔

### اختیاری: واضح سینڈ باکس نام

اگر خودکار شناخت کام نہ کرے، تو ClawMetry کو صحیح سینڈ باکس کی طرف اشارہ کریں:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### سینڈ باکس کے اندر چلانا (ایڈوانسڈ)

اگر آپ کو سنک ڈیمن **OpenShell سینڈ باکس کے اندر** چلانا ضروری ہو، تو اپنی NemoClaw نیٹ ورک پالیسی میں یہ ایگریس رول شامل کریں تاکہ یہ ClawMetry انجیسٹ API تک پہنچ سکے:

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
| `localhost:8900` | 8900 | HTTP | ہاں (مقامی ڈیش بورڈ UI) |
| Docker socket (`/var/run/docker.sock`) | - | Unix socket | کنٹینر سیشن دریافت کے لیے |

سنک ڈیمن صرف `ingest.clawmetry.com` کو آؤٹ باؤنڈ HTTPS کالز کرتا ہے۔ کسی ان باؤنڈ پورٹ کی ضرورت نہیں۔

---

## کلاؤڈ ڈپلائمنٹ

SSH ٹنلز، ریورس پراکسی، اور Docker کے لیے **[کلاؤڈ ٹیسٹنگ گائیڈ](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** دیکھیں۔

## ٹیسٹنگ

اس پراجیکٹ کی جانچ BrowserStack کے ساتھ کی جاتی ہے۔

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ٹیلی میٹری

ClawMetry گمنام انسٹال لائف سائیکل پنگز
`https://app.clawmetry.com/api/install` پر بھیجتا ہے: ایک `install` پنگ
جب آپ پہلی بار کسی نئی مشین پر `clawmetry` CLI چلاتے ہیں، ایک `update`
پنگ نئے ورژن میں اپ گریڈ کرنے کے بعد پہلی بار چلانے پر، اور ایک
`onboarded` پنگ جب آپ ان ڈیش بورڈ آن بورڈنگ چوائس مکمل کرتے ہیں۔ ہم
یہ حقیقی انسٹالز کی گنتی کرنے کے لیے استعمال کرتے ہیں (خام PyPI ڈاؤن
لوڈ نمبرز تقریباً 98% مررز، CI، اور آٹو اپ ڈیٹ ری ڈاؤن لوڈز ہوتے ہیں)
اور یہ جاننے کے لیے کہ کون سے ایجنٹ فریم ورکس اور ورژنز واقعی استعمال
میں ہیں۔

**فی ورژن فی لائف سائیکل ایونٹ زیادہ سے زیادہ ایک POST**، جس میں شامل ہے:

| فیلڈ | مثال | وجہ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` پر محفوظ رینڈم UUID | ڈی ڈپلیکیشن؛ گمنام رہتا ہے جب تک آپ واضح طور پر Cloud sync سے جوڑیں (اس کے بعد تصدیق شدہ ڈیمن ہارٹ بیٹ اسے لے جاتا ہے، اس انسٹال کو آپ کے اکاؤنٹ سے جوڑتے ہوئے) |
| `event` | `install` / `update` / `onboarded` | تازہ انسٹال بمقابلہ موجودہ کا اپ گریڈ |
| `version` | `0.12.167` | استعمال میں کون سے ورژنز ہیں |
| `os` / `os_version` | `Darwin` / `25.3.0` | پلیٹ فارم سپورٹ ترجیحات |
| `python` | `3.11.15` | Python ورژن سپورٹ میٹرکس |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | آگے ہمیں کن ایجنٹس کے ساتھ انٹیگریٹ کرنا چاہیے |
| `is_ci` / `ci_provider` | `true` / `github_actions` | انسانی انسٹالز کو CI شور سے الگ کرنا |

**ہم کیا نہیں بھیجتے**: IP (کلاؤڈ درخواست سے سرور سائیڈ پر ملک کا
کوڈ اخذ کرتا ہے، پھر IP کو ضائع کر دیتا ہے)، ہوسٹ نیم، یوزر نیم،
ورک اسپیس پاتھ، فائل کا مواد، آپ کی api_key، آپ کا ای میل، کوئی بھی
PII یا ورک اسپیس مخصوص چیز۔ وائر پے لوڈ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) میں قابل آڈٹ ہے۔

**آپٹ آؤٹ** (ان میں سے کوئی ایک اسے مستقل طور پر غیر فعال کر دیتا ہے):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

یہاں نیٹ ورک کی ناکامی کبھی بھی `clawmetry` کو چلنے سے نہیں روکتی:
پنگ ایک ڈیمن تھریڈ پر 3 s ٹائم آؤٹ کے ساتھ فائر اینڈ فرگیٹ ہوتی ہے۔

## اسٹار ہسٹری

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
