<!-- i18n-src:48548997be76 -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **12 AI ایجنٹ رن ٹائمز** کے لیے ریئل ٹائم آبزرویبیلیٹی: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور 8 مزید۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ڈیش بورڈ۔

> 🌐 **اسے پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید ←](docs/i18n/)

ایک کمانڈ۔ زیرو کنفیگ۔ سب کچھ خودبخود معلوم کرتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے اور بس۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 12 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

ClawMetry کا آغاز OpenClaw کے لیے آبزرویبیلیٹی کے طور پر ہوا، اور اب یہ آپ کے **پورے ایجنٹ فلیٹ** کو ایک ڈیش بورڈ میں ناپتا ہے، آپ کی مشین پر ہر رن ٹائم کو خودبخود تلاش کرتا ہے:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw اور NemoClaw اوپن سورس ایپ میں مفت ہیں؛ باقی رن ٹائمز ClawMetry Cloud یا سیلف ہوسٹڈ Pro لائسنس کے ساتھ فعال ہوتے ہیں۔ ہیڈر سے رن ٹائم تبدیل کریں اور ہر ٹیب — لاگت، ٹوکن، ٹولز، ٹریسز — اس رن ٹائم پر مرکوز ہو جاتا ہے۔

## آپ کو کیا ملتا ہے

- **Flow** — لائیو اینیمیٹڈ خاکہ جو پیغامات کو چینلز، برین، ٹولز اور واپس بہتے ہوئے دکھاتا ہے
- **Overview** — ہیلتھ چیکس، ایکٹیویٹی ہیٹ میپ، سیشن کاؤنٹس، ماڈل کی معلومات
- **Usage** — روزانہ/ہفتہ وار/ماہانہ تجزیے کے ساتھ ٹوکن اور لاگت کی ٹریکنگ
- **Sessions** — ماڈل، ٹوکن، آخری سرگرمی کے ساتھ فعال ایجنٹ سیشنز
- **Crons** — اسٹیٹس، اگلی بار چلنے کے وقت، دورانیے کے ساتھ شیڈول شدہ کام
- **Logs** — رنگ کوڈڈ ریئل ٹائم لاگ اسٹریمنگ
- **Memory** — SOUL.md، MEMORY.md، AGENTS.md، روزانہ کے نوٹس براؤز کریں
- **Transcripts** — سیشن تاریخ پڑھنے کے لیے چیٹ ببل UI
- **Alerts** — بجٹ کی حدیں، ایرر ریٹ ٹرگرز، ایجنٹ آف لائن کا پتہ لگانا؛ Slack، Discord، PagerDuty، Telegram، Email پر روٹ کرتا ہے
- **Approvals** — تباہ کن ڈیلیٹس، فورس پشز، DB میوٹیشنز، sudo، پیکیج انسٹالز، نیٹ ورک کالز کو ون کلک سائن آف کے پیچھے روکیں

## اسکرین شاٹس

### 🧠 Brain — لائیو ایجنٹ ایونٹ اسٹریم
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ٹوکن استعمال اور سیشن خلاصہ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ریئل ٹائم ٹول کال فیڈ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ماڈل اور سیشن کے حساب سے لاگت کی تفصیل
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ورک اسپیس فائل براؤزر
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — پوسچر اور آڈٹ لاگ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — بجٹ کی حدیں، ایرر ریٹ ٹرگرز، Slack / Discord / PagerDuty / Email پر ویب ہُکس
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — خطرناک ٹول کالز کو دستی سائن آف کے پیچھے روکیں؛ پالیسی پر مبنی تحفظ کے قواعد
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## انسٹال کریں

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

v2 React ایپ `frontend/` میں ہے اور Flask سرور کو v2 فعال کر کے شروع کرنے پر `/v2` پر پیش کی جاتی ہے۔

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

Python پیکیج کے ساتھ آنے والا بنڈل بنانے کے لیے:

```bash
cd frontend
npm run build
```

پروڈکشن بنڈل `clawmetry/static/v2/dist/` میں لکھا جاتا ہے۔

## رن ٹائم / ایجنٹ مطابقت

ClawMetry صرف OpenClaw نہیں، بلکہ بہت سے AI ایجنٹ رن ٹائمز کا مشاہدہ کرتا ہے۔ ہر غیر OpenClaw رن ٹائم ایک مخصوص ریڈر اڈاپٹر کے ساتھ آتا ہے جو اس کے مقامی سیشن فارمیٹ کو ClawMetry کی یکساں شکلوں میں تبدیل کرتا ہے؛ ڈیمن انہیں اسی DuckDB اسٹور اور کلاؤڈ سنیپ شاٹ میں رن ٹائم ٹیگ کے ساتھ محفوظ کرتا ہے، اور Session ری پلے ٹیب ایک **رن ٹائم سوئچر** دکھاتا ہے جب ایک سے زیادہ موجود ہوں۔ مکمل میٹرکس اور رن ٹائمز شامل کرنے کی گائیڈ کے لیے [`docs/compatibility.md`](docs/compatibility.md) دیکھیں، اور OpenClaw فیملی پرائمر کے لیے [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) دیکھیں۔

| رن ٹائم / ایجنٹ | اسٹیٹس | نوٹس |
|---|---|---|
| **OpenClaw** | Native | ریفرنس رن ٹائم، خودبخود تلاش |
| **PicoClaw** | Beta adapter | فلیٹ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)۔ ٹرانسکرپٹس، ماڈل، ٹول کالز۔ |
| **NanoClaw** | Beta adapter | فی سیشن SQLite (`data/v2-sessions`)۔ ٹرانسکرپٹس اور پیغام کاؤنٹس۔ |
| **Hermes** | Beta adapter | SQLite `~/.hermes/state.db`۔ ٹرانسکرپٹس، ماڈل، ٹوکن/لاگت۔ |
| **Claude Code** | Beta adapter | JSONL `~/.claude/projects/.../<id>.jsonl`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز اور سوچ، ٹوکن استعمال۔ |
| **Codex** | Beta adapter | رول آؤٹ JSONL `~/.codex/sessions/...`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Cursor** | Beta adapter | SQLite `state.vscdb`۔ چیٹ/کمپوزر ٹرانسکرپٹس، ماڈل۔ |
| **Aider** | Beta adapter | فی پروجیکٹ `.aider.chat.history.md`۔ ٹرانسکرپٹس، ماڈل، ٹوکن کاؤنٹس۔ |
| **Goose** | Beta adapter | SQLite `~/.local/share/goose`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن ٹوٹلز۔ |
| **opencode** | Beta adapter | SQLite `~/.local/share/opencode`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن اور لاگت۔ |
| **Qwen Code** | Beta adapter | JSONL `~/.qwen/projects/.../chats`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |

"Beta adapter" کا مطلب ہے کہ ClawMetry اس رن ٹائم کے حقیقی آن ڈسک فارمیٹ کے لیے ریڈر فراہم کرتا ہے، جو ایک حقیقی مشین پر حقیقی انسٹال کے خلاف بنایا اور تصدیق شدہ ہے (دیکھیں `tests/fixtures/runtimes/<rt>/`)۔ اڈاپٹرز صرف پڑھنے والے ہیں؛ ہر ایک اس بارے میں ایمانداری سے بتاتا ہے کہ اس کا رن ٹائم اصل میں کیا ذخیرہ کرتا ہے (مثلاً PicoClaw/NanoClaw/Cursor ڈسک پر ٹوکن لاگت نہیں لکھتے)۔ جب ایک نوڈ پر کئی رن ٹائمز چلتے ہیں تو رن ٹائم سوئچر سیشنز ویو کو صاف گہرائی سے دیکھنے کے لیے ایک پر محدود کر دیتا ہے۔

## کسی بھی SDK ایجنٹ کو ٹریک کریں — آؤٹ لوپ لاگت کی نسبت

اوپر دیے گئے رن ٹائمز سب ڈسک پر سیشنز لکھتے ہیں۔ آپ کا اپنا **پروڈکشن ایجنٹ** جو آپ نے OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B، یا سادہ `httpx` لوپ پر بنایا ہے، ایسا نہیں کرتا۔ ClawMetry کا زیرو کنفیگ انٹرسیپٹر پھر بھی `httpx`/`requests` کو مونکی پیچنگ کر کے اس کی LLM کالز (لاگت، ٹوکن، لیٹنسی، ایررز) کیپچر کرتا ہے:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا `CLAWMETRY_SOURCE=support-agent` انوائرنمنٹ ویریبل) ہر کال کو ایک **نامزد سورس** کے ساتھ ٹیگ کرتا ہے، تاکہ آپ کی چلائی ہوئی ہر پروڈکٹ ڈیش بورڈ کے Overview پر **🔌 Out-loop sources** کارڈ میں اپنی الگ، لاگت قابل نسبت لائن کے طور پر ظاہر ہو۔ کوئی سورس سیٹ نہیں؟ کالز پھر بھی ٹریک ہوتی ہیں؛ کارڈ بس چھپا رہتا ہے۔

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

یہ وہی ڈیٹا لیئر ہے جسے رن ٹائم اڈاپٹرز فیڈ کرتے ہیں (DuckDB سے کلاؤڈ سنیپ شاٹ تک)، لہذا آؤٹ لوپ سورسز کلاؤڈ ڈیش بورڈ پر باقی سب چیزوں کی طرح E2E انکرپٹڈ طریقے سے سنک ہوتے ہیں۔

## OpenTelemetry — وینڈر نیوٹرل، اپنے ٹریسز کہیں بھی بھیجیں

ClawMetry **GenAI سیمینٹک کنونشنز** استعمال کرتے ہوئے دونوں سمتوں میں **OpenTelemetry** بولتا ہے، تاکہ آپ کے ایجنٹ ٹریسز کبھی کسی ایک ٹول میں بند نہ ہوں۔

ہر سیشن کو LLM کالز، ٹولز، سب ایجنٹس، ٹوکن، لاگت سمیت OTLP/HTTP GenAI اسپینز کے طور پر کسی بھی کلیکٹر (Datadog، Grafana، Honeycomb، یا آپ کا اپنا OTel Collector) کو **ایکسپورٹ** کریں:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

آتھ ہیڈرز اور پول انٹروال اختیاری انوائرنمنٹ ویریبلز ہیں:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**انجسٹ** — بلٹ ان OTLP ریسیور `/v1/traces` اور `/v1/metrics` پر کسی بھی چیز سے ٹریسز اور میٹرکس قبول کرتا ہے (پروٹو بف انجسٹ کے لیے `pip install clawmetry[otel]`)۔

آپ کو زیرو کنفیگ، لوکل فرسٹ ClawMetry ڈیش بورڈ **اور** آپ کی ٹیم کے پاس پہلے سے چلنے والے کسی بھی بیک اینڈ میں آپ کا ڈیٹا دونوں ملتے ہیں۔ کوئی لاک ان نہیں، انسٹال کرنے کے لیے کوئی دوسرا ایجنٹ نہیں۔

## کنفیگریشن

زیادہ تر لوگوں کو کسی کنفیگ کی ضرورت نہیں۔ ClawMetry آپ کی ورک اسپیس، لاگز، سیشنز اور crons خودبخود تلاش کرتا ہے۔

اگر آپ کو حسب ضرورت بنانے کی ضرورت ہو:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

تمام اختیارات: `clawmetry --help`

## سپورٹ شدہ چینلز

ClawMetry آپ کے ترتیب شدہ ہر OpenClaw چینل کے لیے لائیو سرگرمی دکھاتا ہے۔ صرف وہی چینلز جو آپ کے `openclaw.json` میں اصل میں سیٹ اپ ہیں Flow خاکے میں ظاہر ہوتے ہیں، غیر ترتیب شدہ خودبخود چھپ جاتے ہیں۔

لائیو چیٹ ببل ویو دیکھنے کے لیے Flow میں کسی بھی چینل نوڈ پر کلک کریں جس میں آنے اور جانے والے پیغامات کی تعداد ہو۔

| چینل | اسٹیٹس | لائیو پاپ اپ | نوٹس |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ مکمل | ✅ | پیغامات، اعداد و شمار، 10 سیکنڈ ریفریش |
| 💬 **iMessage** | ✅ مکمل | ✅ | براہ راست `~/Library/Messages/chat.db` پڑھتا ہے |
| 💚 **WhatsApp** | ✅ مکمل | ✅ | WhatsApp Web (Baileys) کے ذریعے |
| 🔵 **Signal** | ✅ مکمل | ✅ | signal-cli کے ذریعے |
| 🟣 **Discord** | ✅ مکمل | ✅ | گلڈ اور چینل کا پتہ لگانا |
| 🟪 **Slack** | ✅ مکمل | ✅ | ورک اسپیس اور چینل کا پتہ لگانا |
| 🌐 **Webchat** | ✅ مکمل | ✅ | بلٹ ان ویب UI سیشنز |
| 📡 **IRC** | ✅ مکمل | ✅ | ٹرمینل اسٹائل ببل UI |
| 🍏 **BlueBubbles** | ✅ مکمل | ✅ | BlueBubbles REST API کے ذریعے iMessage |
| 🔵 **Google Chat** | ✅ مکمل | ✅ | Chat API ویب ہُکس کے ذریعے |
| 🟣 **MS Teams** | ✅ مکمل | ✅ | Teams بوٹ پلگ ان کے ذریعے |
| 🔷 **Mattermost** | ✅ مکمل | ✅ | سیلف ہوسٹڈ ٹیم چیٹ |
| 🟩 **Matrix** | ✅ مکمل | ✅ | غیر مرکزی، E2EE سپورٹ |
| 🟢 **LINE** | ✅ مکمل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ مکمل | ✅ | غیر مرکزی NIP-04 DMs |
| 🟣 **Twitch** | ✅ مکمل | ✅ | IRC کنکشن کے ذریعے چیٹ |
| 🔷 **Feishu/Lark** | ✅ مکمل | ✅ | WebSocket ایونٹ سبسکرپشن |
| 🔵 **Zalo** | ✅ مکمل | ✅ | Zalo Bot API |

> **خودکار پتہ لگانا:** ClawMetry آپ کا `~/.openclaw/openclaw.json` پڑھتا ہے اور صرف وہی چینلز رینڈر کرتا ہے جو آپ نے اصل میں ترتیب دیے ہیں۔ دستی سیٹ اپ کی ضرورت نہیں۔

## Docker تعیناتی

کیا ClawMetry کو کنٹینر میں چلانا چاہتے ہیں؟ کوئی مسئلہ نہیں! 🐳

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

> **نوٹ:** Docker میں چلاتے وقت، اپنے ایجنٹ کی ڈیٹا اور لاگ ڈائریکٹریز (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) ماؤنٹ کریں تاکہ ClawMetry آپ کا سیٹ اپ خودبخود تلاش کر سکے۔

## ضروریات

- Python 3.8+
- Flask (pip کے ذریعے خودبخود انسٹال)
- ایک ہی مشین پر AI ایجنٹ رن ٹائم: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، یا PicoClaw (یا Docker کے لیے ماؤنٹڈ والیومز)
- Linux یا macOS

## NemoClaw / OpenShell سپورٹ

ClawMetry خودبخود [NemoClaw](https://github.com/NVIDIA/NemoClaw) کا پتہ لگاتا ہے، جو OpenClaw کے لیے NVIDIA کا انٹرپرائز سیکیورٹی ریپر ہے جو ایجنٹس کو سینڈ باکسڈ OpenShell کنٹینرز کے اندر چلاتا ہے۔

زیادہ تر صورتوں میں کوئی اضافی کنفیگریشن کی ضرورت نہیں۔ سنک ڈیمن سیشن فائلز خودبخود تلاش کرتا ہے چاہے وہ میزبان پر `~/.openclaw/` میں ہوں یا OpenShell کنٹینر کے اندر۔

### یہ کیسے کام کرتا ہے

ClawMetry دو طریقوں سے NemoClaw کا پتہ لگاتا ہے:

1. **بائنری کا پتہ لگانا** — `nemoclaw` CLI کی جانچ کرتا ہے اور سینڈ باکس کی معلومات حاصل کرنے کے لیے `nemoclaw status` چلاتا ہے
2. **کنٹینر کا پتہ لگانا** — چلتے ہوئے Docker کنٹینرز میں `openshell`، `nemoclaw`، یا `ghcr.io/nvidia/` امیجز اسکین کرتا ہے، پھر والیوم ماؤنٹس یا `docker cp` کے ذریعے سیشنز پڑھتا ہے

NemoClaw کنٹینرز سے سنک شدہ سیشن فائلز کلاؤڈ ڈیش بورڈ میں `runtime=nemoclaw` اور `container_id` میٹا ڈیٹا کے ساتھ ٹیگ ہوتی ہیں، تاکہ آپ انہیں معیاری OpenClaw سیشنز سے فوری طور پر الگ کر سکیں۔

### تجویز کردہ سیٹ اپ: HOST پر سنک ڈیمن

بہترین تجربے کے لیے، ClawMetry کا سنک ڈیمن **میزبان مشین** پر چلائیں (سینڈ باکس کے اندر نہیں)۔ اس سے NemoClaw نیٹ ورک پالیسی کی پابندیوں سے بچا جاتا ہے۔

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سنک ڈیمن خودبخود کسی بھی چلتے ہوئے OpenShell کنٹینرز کے اندر سیشنز تلاش کرے گا۔

### اختیاری: واضح سینڈ باکس نام

اگر خودکار پتہ لگانا کام نہ کرے تو ClawMetry کو صحیح سینڈ باکس کی طرف اشارہ کریں:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### سینڈ باکس کے اندر چلانا (اعلی درجہ)

اگر آپ کو سنک ڈیمن **OpenShell سینڈ باکس کے اندر** چلانا ضروری ہو تو اپنی NemoClaw نیٹ ورک پالیسی میں یہ ایگریس رول شامل کریں تاکہ یہ ClawMetry انجسٹ API تک پہنچ سکے:

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
| `ingest.clawmetry.com` | 443 | HTTPS | ہاں (سنک ڈیمن سے کلاؤڈ) |
| `localhost:8900` | 8900 | HTTP | ہاں (مقامی ڈیش بورڈ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | کنٹینر سیشن دریافت کے لیے |

سنک ڈیمن صرف `ingest.clawmetry.com` کو آؤٹ باؤنڈ HTTPS کالز کرتا ہے۔ کوئی ان باؤنڈ پورٹ درکار نہیں۔

---

## کلاؤڈ تعیناتی

SSH ٹنلز، ریورس پراکسی اور Docker کے لیے **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** دیکھیں۔

## ٹیسٹنگ

یہ پروجیکٹ BrowserStack کے ساتھ ٹیسٹ کیا گیا ہے۔

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ٹیلی میٹری

ClawMetry ایک نئی مشین پر پہلی بار `clawmetry` CLI چلانے پر `https://app.clawmetry.com/api/install` کو ایک گمنام "پہلی بار چلانے" پنگ بھیجتا ہے۔ ہم اسے انسٹالز گننے (ایک OSS پروجیکٹ کے لیے ہمارا واحد مارکیٹنگ میٹرک) اور یہ جاننے کے لیے استعمال کرتے ہیں کہ ہمارے صارفین کے پاس کون سے ایجنٹ فریم ورکس انسٹال ہیں۔

**فی انسٹال بالکل ایک POST**، جس میں شامل ہے:

| فیلڈ | مثال | کیوں |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` میں محفوظ بے ترتیب UUID | ڈپلیکیشن سے بچاؤ؛ آپ کے ای میل یا api_key سے منسلک نہیں |
| `version` | `0.12.167` | جنگل میں کون سے ورژن ہیں |
| `os` / `os_version` | `Darwin` / `25.3.0` | پلیٹ فارم سپورٹ کی ترجیحات |
| `python` | `3.11.15` | Python ورژن سپورٹ میٹرکس |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ہمیں اگلے کس ایجنٹ کے ساتھ انضمام کرنا چاہیے |
| `is_ci` / `ci_provider` | `true` / `github_actions` | انسانی انسٹالز کو CI شور سے الگ کریں |

**ہم کیا نہیں بھیجتے**: IP (کلاؤڈ درخواست سے صرف ملک کا کوڈ اخذ کرتا ہے، پھر IP ضائع کر دیتا ہے)، hostname، username، ورک اسپیس پاتھ، فائل مواد، آپ کا api_key، آپ کا ای میل، کوئی PII یا ورک اسپیس مخصوص چیز۔ وائر پے لوڈ [`clawmetry/telemetry.py`](clawmetry/telemetry.py) میں قابل آڈٹ ہے۔

**آپٹ آؤٹ** (ان میں سے کوئی ایک مستقل طور پر غیر فعال کر دیتا ہے):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

یہاں نیٹ ورک کی ناکامی کبھی `clawmetry` کو چلنے سے نہیں روکتی — پنگ 3 سیکنڈ ٹائم آؤٹ کے ساتھ ایک ڈیمن تھریڈ پر فائر اینڈ فارگیٹ ہے۔

## ستاروں کی تاریخ

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> کی طرف سے بنایا گیا · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ایکو سسٹم کا حصہ</sub>
</p>
