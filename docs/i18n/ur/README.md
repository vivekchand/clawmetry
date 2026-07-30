<!-- i18n-src:9a05336fbdc1 -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **14 AI ایجنٹ رن ٹائمز** کے لیے حقیقی وقت کی مشاہداتی سہولت: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور مزید 10۔ آپ کے پورے ایجنٹ بیڑے کے لیے ایک ڈیش بورڈ۔

> 🌐 **اسے پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ کوئی ترتیب نہیں۔ ہر چیز خودکار طور پر شناخت ہوتی ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے اور بس، کام مکمل۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

ClawMetry کا آغاز OpenClaw کے لیے مشاہداتی سہولت کے طور پر ہوا تھا، اور اب یہ آپ کے **پورے ایجنٹ بیڑے** کو ایک ہی ڈیش بورڈ میں ناپتا ہے، آپ کی مشین پر ہر رن ٹائم کو خودکار طور پر شناخت کرتے ہوئے:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw اور NemoClaw اوپن سورس ایپ میں مفت ہیں؛ باقی رن ٹائمز ClawMetry Cloud یا خود میزبانی شدہ Pro لائسنس کے ساتھ فعال ہوتے ہیں۔ ہیڈر سے رن ٹائم تبدیل کریں اور ہر ٹیب — لاگت، ٹوکنز، ٹولز، ٹریسز — اسی رن ٹائم کے دائرہ کار میں دوبارہ ترتیب پاتا ہے۔ درست مفت/ادائیگی تقسیم، ٹیئر میٹرکس، `/api/entitlement` کی شکل، اور `clawmetry license` CLI کے لیے **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** دیکھیں۔

## آپ کو کیا ملتا ہے

- **Flow** — پیغامات کو چینلز، برین، ٹولز کے ذریعے اور واپس بہتے ہوئے دکھانے والا زندہ متحرک خاکہ
- **Overview** — صحت کی جانچ، سرگرمی کا ہیٹ میپ، سیشن گنتی، ماڈل کی معلومات
- **Usage** — روزانہ/ہفتہ وار/ماہانہ تقسیم کے ساتھ ٹوکن اور لاگت کی ٹریکنگ
- **Sessions** — ماڈل، ٹوکنز، آخری سرگرمی کے ساتھ فعال ایجنٹ سیشنز
- **Crons** — حیثیت، اگلی رن، دورانیے کے ساتھ شیڈول شدہ کام
- **Logs** — رنگ کوڈ شدہ حقیقی وقت لاگ سٹریمنگ
- **Memory** — SOUL.md، MEMORY.md، AGENTS.md، روزانہ نوٹس براؤز کریں
- **Transcripts** — سیشن کی تاریخ پڑھنے کے لیے چیٹ بلبلہ UI
- **Alerts** — بجٹ کی حد، ایرر ریٹ کے ٹرگرز، ایجنٹ آف لائن کی شناخت؛ Slack، Discord، PagerDuty، Telegram، Email پر روٹ کرتا ہے
- **Approvals** — تباہ کن ڈیلیٹس، فورس پُشز، ڈی بی میوٹیشنز، sudo، پیکیج انسٹالز، نیٹ ورک کالز کو ایک کلک سائن آف کے پیچھے روکیں

## اسکرین شاٹس

### 🧠 Brain — زندہ ایجنٹ ایونٹ سٹریم
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ٹوکن استعمال اور سیشن خلاصہ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — حقیقی وقت ٹول کال فیڈ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ماڈل اور سیشن کے لحاظ سے لاگت کی تقسیم
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ورک اسپیس فائل براؤزر
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — پوزیشن اور آڈٹ لاگ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — بجٹ کی حدیں، ایرر ریٹ کے ٹرگرز، Slack / Discord / PagerDuty / Email کے لیے ویب ہکس
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — خطرناک ٹول کالز کو دستی سائن آف کے پیچھے روکیں؛ پالیسی کی حمایت یافتہ حفاظتی قواعد
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code کے لیے عملدرآمد سے پہلے بلاکنگ** — ایک کمانڈ ایک
PreToolUse ہک انسٹال کرتی ہے جو مماثل ٹول کالز کو چلنے *سے پہلے* روک دیتی ہے اور آپ کے فیصلے کا انتظار کرتی ہے (
[کلاؤڈ پش نوٹیفیکیشنز](https://app.clawmetry.com/push) فعال ہونے پر آپ کے فون سے ایک ٹیپ کے ساتھ):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

انکار صرف اسی ایک ٹول کال کو روکتا ہے — ایجنٹ اپنا سیشن برقرار رکھتا ہے اور
کوئی اور طریقہ آزما سکتا ہے۔ آپ کے فون پر منظوری دینا Claude Code کے اپنے
اجازت کے پرامپٹ کو چھوڑ دیتا ہے (آپ پہلے ہی جواب دے چکے ہیں)۔ غیر مماثل ٹولز کی قیمت تقریباً 40ms ہوتی ہے اور
Claude Code کے عام اجازت کے بہاؤ میں چلی جاتی ہیں۔ آپ کو فون پش بھی ملتا ہے جب Claude Code خود
آپ کا انتظار کر رہا ہو (`permission_prompt` /
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

**ماخذ سے:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## v2 فرنٹ اینڈ ڈیولپمنٹ

v2 React ایپ `frontend/` میں موجود ہے اور جب Flask
سرور v2 فعال کرکے شروع کیا جائے تو `/v2` پر پیش کی جاتی ہے۔

ڈیولپمنٹ کے دوران دو ٹرمینلز استعمال کریں:

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

`http://localhost:5173/v2/` کھولیں۔ Vite `/api` کی درخواستوں کو
`http://localhost:8900` پر پراکسی کرتا ہے، تاکہ React ایپ اضافی CORS ترتیب کے
بغیر مقامی Flask سرور سے بات کر سکے۔

پیکیج کے ساتھ آنے والا بنڈل بنانے کے لیے:

```bash
cd frontend
npm run build
```

پروڈکشن بنڈل `clawmetry/static/v2/dist/` میں لکھا جاتا ہے۔

## رن ٹائم / ایجنٹ مطابقت

ClawMetry بہت سے AI ایجنٹ رن ٹائمز کا مشاہدہ کرتا ہے، صرف OpenClaw کا نہیں۔ ہر غیر-OpenClaw رن ٹائم کے ساتھ ایک مخصوص ریڈر ایڈاپٹر آتا ہے جو اس کے مقامی سیشن فارمیٹ کو ClawMetry کی متحد شکلوں میں تبدیل کرتا ہے؛ ڈیمن انہیں اسی DuckDB اسٹور + کلاؤڈ سنیپ شاٹ میں شامل کرتا ہے، جو رن ٹائم کے ساتھ ٹیگ شدہ ہوتا ہے، اور Session replay ٹیب ایک **رن ٹائم سوئچر** دکھاتا ہے جب ایک سے زیادہ موجود ہوں۔ مکمل میٹرکس + رن ٹائم شامل کرنے کی رہنمائی کے لیے [`docs/compatibility.md`](docs/compatibility.md) اور OpenClaw فیملی کے تعارف کے لیے [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) دیکھیں۔

| رن ٹائم / ایجنٹ | حیثیت | نوٹس |
|---|---|---|
| **OpenClaw** | مقامی | حوالہ رن ٹائم، خودکار شناخت شدہ |
| **PicoClaw** | بیٹا ایڈاپٹر | فلیٹ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)۔ ٹرانسکرپٹس، ماڈل، ٹول کالز۔ |
| **NanoClaw** | بیٹا ایڈاپٹر | فی سیشن SQLite (`data/v2-sessions`)۔ ٹرانسکرپٹس + پیغام کی گنتی۔ |
| **Hermes** | بیٹا ایڈاپٹر | SQLite `~/.hermes/state.db`۔ ٹرانسکرپٹس، ماڈل، ٹوکنز/لاگت۔ |
| **Claude Code** | بیٹا ایڈاپٹر | JSONL `~/.claude/projects/.../<id>.jsonl`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز + تھنکنگ، ٹوکن استعمال۔ |
| **Codex** | بیٹا ایڈاپٹر | رول آؤٹ JSONL `~/.codex/sessions/...`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Cursor** | بیٹا ایڈاپٹر | SQLite `state.vscdb`۔ چیٹ/کمپوزر ٹرانسکرپٹس، ماڈل۔ |
| **Aider** | بیٹا ایڈاپٹر | فی پراجیکٹ `.aider.chat.history.md`۔ ٹرانسکرپٹس، ماڈل، ٹوکن گنتی۔ |
| **Goose** | بیٹا ایڈاپٹر | SQLite `~/.local/share/goose`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن کل۔ |
| **opencode** | بیٹا ایڈاپٹر | SQLite `~/.local/share/opencode`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Qwen Code** | بیٹا ایڈاپٹر | JSONL `~/.qwen/projects/.../chats`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Pi** | بیٹا ایڈاپٹر | JSONL `~/.pi/agent/sessions`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Deep Agents** | بیٹا ایڈاپٹر | SQLite `~/.deepagents/.state/sessions.db`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **n8n** | بیٹا ایڈاپٹر | SQLite `~/.n8n/database.sqlite`۔ ورک فلو ایگزیکیوشنز، نوڈ رنز، AI Agent پرامپٹس، ماڈل + ٹوکنز جہاں n8n انہیں ریکارڈ کرتا ہے۔ |

"بیٹا ایڈاپٹر" کا مطلب ہے کہ ClawMetry اس رن ٹائم کے حقیقی آن ڈسک فارمیٹ کے لیے ایک ریڈر فراہم کرتا ہے، ہر ایک کو حقیقی مشین پر ایک حقیقی انسٹال کے خلاف بنایا اور تصدیق شدہ کیا گیا ہے (دیکھیں `tests/fixtures/runtimes/<rt>/`)۔ ایڈاپٹرز صرف پڑھنے کے قابل ہیں؛ ہر ایک اس بارے میں دیانتدار ہے کہ اس کا رن ٹائم حقیقت میں کیا محفوظ کرتا ہے (مثلاً PicoClaw/NanoClaw/Cursor ٹوکن لاگت کو ڈسک پر نہیں لکھتے)۔ جب ایک نوڈ پر کئی رن ٹائمز چل رہے ہوں، تو رن ٹائم سوئچر سیشنز ویو کو صاف گہرائی سے جائزے کے لیے ایک تک محدود کر دیتا ہے۔

## کسی بھی SDK ایجنٹ کو ٹریک کریں — آؤٹ-لوپ لاگت انتساب

اوپر دیے گئے رن ٹائمز سبھی سیشنز کو ڈسک پر لکھتے ہیں۔ آپ کا اپنا **پروڈکشن ایجنٹ** — وہ جو آپ نے OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B، یا ایک سادہ `httpx` لوپ پر بنایا — ایسا نہیں کرتا۔ ClawMetry کا زیرو-کنفگ انٹرسیپٹر پھر بھی `httpx`/`requests` کو مانکی پیچ کرکے اس کی LLM کالز (لاگت، ٹوکنز، لیٹنسی، ایررز) حاصل کرتا ہے:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا `CLAWMETRY_SOURCE=support-agent` ماحولیاتی متغیر) ہر کال کو ایک **نامزد ذریعے** کے ساتھ ٹیگ کرتا ہے، تاکہ آپ کا چلایا ہوا ہر پروڈکٹ ڈیش بورڈ کے Overview پر موجود **🔌 آؤٹ-لوپ ذرائع** کارڈ میں اپنی خود کی، لاگت کے لحاظ سے منسوب کی جانے والی لائن کے طور پر ظاہر ہو — فی ایجنٹ کالز، پرووائیڈرز، لیٹنسی، ایرر ریٹ۔ کوئی ذریعہ سیٹ نہیں کیا؟ کالز پھر بھی ٹریک ہوتی ہیں؛ کارڈ صرف چھپا رہتا ہے۔

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

یہ وہی ڈیٹا لیئر ہے جسے رن ٹائم ایڈاپٹرز کھلاتے ہیں (DuckDB → کلاؤڈ سنیپ شاٹ)، تو آؤٹ-لوپ ذرائع باقی سب کچھ کی طرح کلاؤڈ ڈیش بورڈ سے سنک ہوتے ہیں، مکمل طور پر انکرپٹڈ (E2E)۔

## OpenTelemetry — وینڈر نیوٹرل، اپنے ٹریسز کہیں بھی بھیجیں

ClawMetry دونوں سمتوں میں **OpenTelemetry** بولتا ہے، **GenAI سیمنٹک کنونشنز** استعمال کرتے ہوئے، تاکہ آپ کے ایجنٹ ٹریسز کبھی ایک ٹول تک محدود نہ ہوں۔

ہر سیشن — LLM کالز، ٹولز، سب-ایجنٹس، ٹوکنز، لاگت — کو OTLP/HTTP GenAI اسپینز کے طور پر کسی بھی کلیکٹر (Datadog، Grafana، Honeycomb، یا آپ کا اپنا OTel Collector) میں **ایکسپورٹ** کریں:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

آتھ ہیڈرز اور پول انٹرول اختیاری ماحولیاتی متغیرات ہیں:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**اِنجیسٹ** — بلٹ اِن OTLP ریسیور ٹریسز اور میٹرکس کسی بھی اور جگہ سے `/v1/traces` اور `/v1/metrics` پر قبول کرتا ہے (protobuf اِنجیسٹ کے لیے `pip install clawmetry[otel]`)۔

آپ کو زیرو-کنفگ، لوکل-فرسٹ ClawMetry ڈیش بورڈ **اور** آپ کے ڈیٹا کا وہ بیک اینڈ جو آپ کی ٹیم پہلے ہی چلا رہی ہے — نہ کوئی لاک اِن، نہ دوسرا ایجنٹ انسٹال کرنے کی ضرورت۔

## ترتیب

زیادہ تر لوگوں کو کسی ترتیب کی ضرورت نہیں ہوتی۔ ClawMetry آپ کے ورک اسپیس، لاگز، سیشنز، اور کرونز کو خودکار طور پر شناخت کرتا ہے۔

اگر آپ کو حسب ضرورت بنانے کی ضرورت ہو:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

تمام اختیارات: `clawmetry --help`

## معاون چینلز

ClawMetry آپ کے کنفیگر کردہ ہر OpenClaw چینل کے لیے زندہ سرگرمی دکھاتا ہے۔ صرف وہی چینلز جو آپ کے `openclaw.json` میں واقعی سیٹ اپ ہیں Flow ڈایاگرام میں ظاہر ہوتے ہیں — غیر کنفیگر شدہ چینلز خودکار طور پر چھپے رہتے ہیں۔

Flow میں کسی بھی چینل نوڈ پر کلک کریں تاکہ آنے والے/جانے والے پیغامات کی گنتی کے ساتھ زندہ چیٹ بلبلہ ویو دیکھ سکیں۔

| چینل | حیثیت | زندہ پاپ اپ | نوٹس |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ مکمل | ✅ | پیغامات، اعداد و شمار، 10s ریفریش |
| 💬 **iMessage** | ✅ مکمل | ✅ | `~/Library/Messages/chat.db` براہ راست پڑھتا ہے |
| 💚 **WhatsApp** | ✅ مکمل | ✅ | WhatsApp Web (Baileys) کے ذریعے |
| 🔵 **Signal** | ✅ مکمل | ✅ | signal-cli کے ذریعے |
| 🟣 **Discord** | ✅ مکمل | ✅ | گلڈ + چینل کی شناخت |
| 🟪 **Slack** | ✅ مکمل | ✅ | ورک اسپیس + چینل کی شناخت |
| 🌐 **Webchat** | ✅ مکمل | ✅ | بلٹ اِن ویب UI سیشنز |
| 📡 **IRC** | ✅ مکمل | ✅ | ٹرمینل طرز کی بلبلہ UI |
| 🍏 **BlueBubbles** | ✅ مکمل | ✅ | BlueBubbles REST API کے ذریعے iMessage |
| 🔵 **Google Chat** | ✅ مکمل | ✅ | Chat API ویب ہکس کے ذریعے |
| 🟣 **MS Teams** | ✅ مکمل | ✅ | Teams بوٹ پلگ اِن کے ذریعے |
| 🔷 **Mattermost** | ✅ مکمل | ✅ | خود میزبانی شدہ ٹیم چیٹ |
| 🟩 **Matrix** | ✅ مکمل | ✅ | غیر مرکزی، E2EE سپورٹ |
| 🟢 **LINE** | ✅ مکمل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ مکمل | ✅ | غیر مرکزی NIP-04 DMs |
| 🟣 **Twitch** | ✅ مکمل | ✅ | IRC کنکشن کے ذریعے چیٹ |
| 🔷 **Feishu/Lark** | ✅ مکمل | ✅ | WebSocket ایونٹ سبسکرپشن |
| 🔵 **Zalo** | ✅ مکمل | ✅ | Zalo Bot API |

> **خودکار شناخت:** ClawMetry آپ کا `~/.openclaw/openclaw.json` پڑھتا ہے اور صرف وہی چینلز رینڈر کرتا ہے جو آپ نے واقعی کنفیگر کیے ہیں۔ کسی دستی سیٹ اپ کی ضرورت نہیں۔

## Docker تعیناتی

کنٹینر میں ClawMetry چلانا چاہتے ہیں؟ کوئی مسئلہ نہیں! 🐳

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

> **نوٹ:** Docker میں چلاتے وقت، اپنے ایجنٹ کی ڈیٹا + لاگ ڈائریکٹریز (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) کو ماؤنٹ کریں تاکہ ClawMetry آپ کے سیٹ اپ کو خودکار طور پر شناخت کر سکے۔

## ضروریات

- Python 3.8+
- Flask (pip کے ذریعے خودکار طور پر انسٹال ہوتا ہے)
- اسی مشین پر ایک AI ایجنٹ رن ٹائم: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، یا n8n (یا Docker کے لیے ماؤنٹ کردہ والیومز)
- Linux یا macOS

## NemoClaw / OpenShell سپورٹ

ClawMetry خودکار طور پر [NemoClaw](https://github.com/NVIDIA/NemoClaw) کی شناخت کرتا ہے — OpenClaw کے لیے NVIDIA کا انٹرپرائز سیکورٹی ریپر جو ایجنٹس کو سینڈ باکسڈ OpenShell کنٹینرز کے اندر چلاتا ہے۔

زیادہ تر معاملات میں کسی اضافی ترتیب کی ضرورت نہیں ہوتی۔ سنک ڈیمن سیشن فائلوں کو خودکار طور پر دریافت کرتا ہے چاہے وہ ہوسٹ پر `~/.openclaw/` میں ہوں یا کسی OpenShell کنٹینر کے اندر۔

### یہ کیسے کام کرتا ہے

ClawMetry دو طریقوں سے NemoClaw کی شناخت کرتا ہے:

1. **بائنری شناخت** — `nemoclaw` CLI کی جانچ کرتا ہے اور سینڈ باکس کی معلومات حاصل کرنے کے لیے `nemoclaw status` چلاتا ہے
2. **کنٹینر شناخت** — چلنے والے Docker کنٹینرز کو `openshell`، `nemoclaw`، یا `ghcr.io/nvidia/` امیجز کے لیے سکین کرتا ہے، پھر والیوم ماؤنٹس یا `docker cp` کے ذریعے سیشنز پڑھتا ہے

NemoClaw کنٹینرز سے سنک شدہ سیشن فائلوں کو کلاؤڈ ڈیش بورڈ میں `runtime=nemoclaw` اور `container_id` میٹا ڈیٹا کے ساتھ ٹیگ کیا جاتا ہے، تاکہ آپ انہیں معیاری OpenClaw سیشنز سے ایک نظر میں الگ پہچان سکیں۔

### تجویز کردہ سیٹ اپ: سنک ڈیمن ہوسٹ پر

بہترین تجربے کے لیے، ClawMetry کا سنک ڈیمن **ہوسٹ مشین** پر چلائیں (سینڈ باکس کے اندر نہیں)۔ یہ NemoClaw نیٹ ورک پالیسی کی پابندیوں سے بچاتا ہے۔

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سنک ڈیمن خودکار طور پر کسی بھی چلنے والے OpenShell کنٹینرز کے اندر سیشنز تلاش کر لے گا۔

### اختیاری: واضح سینڈ باکس نام

اگر خودکار شناخت کام نہ کرے، تو ClawMetry کو صحیح سینڈ باکس کی طرف اشارہ کریں:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### سینڈ باکس کے اندر چلانا (ایڈوانسڈ)

اگر آپ کو سنک ڈیمن **اندر** OpenShell سینڈ باکس میں چلانا ضروری ہو، تو اپنی NemoClaw نیٹ ورک پالیسی میں یہ ایگریس رول شامل کریں تاکہ یہ ClawMetry ingest API تک پہنچ سکے:

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
| Docker ساکٹ (`/var/run/docker.sock`) | — | Unix ساکٹ | کنٹینر سیشن دریافت کے لیے |

سنک ڈیمن صرف `ingest.clawmetry.com` پر آؤٹ باؤنڈ HTTPS کالز کرتا ہے۔ کسی اِن باؤنڈ پورٹ کی ضرورت نہیں۔

---

## کلاؤڈ تعیناتی

SSH ٹنلز، ریورس پراکسی، اور Docker کے لیے **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** دیکھیں۔

## ٹیسٹنگ

اس پراجیکٹ کی ٹیسٹنگ BrowserStack کے ساتھ کی جاتی ہے۔

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ٹیلی میٹری

ClawMetry ایک واحد گمنام "پہلی رن" پنگ
`https://app.clawmetry.com/api/install` کو اس وقت بھیجتا ہے جب آپ نئی مشین پر
`clawmetry` CLI پہلی بار چلاتے ہیں۔ ہم اسے انسٹالز گننے کے لیے استعمال کرتے ہیں (
یہ ایک OSS پراجیکٹ کے لیے واحد مارکیٹنگ میٹرک ہے) اور یہ جاننے کے لیے کہ
ہمارے صارفین نے کون سے ایجنٹ فریم ورکس انسٹال کر رکھے ہیں۔

**ہر انسٹال پر بالکل ایک POST**، جس میں شامل ہے:

| فیلڈ | مثال | وجہ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` پر محفوظ رینڈم UUID | ڈیڈوپ؛ آپ کے ای میل یا api_key سے منسلک نہیں |
| `version` | `0.12.167` | کون سے ورژنز استعمال میں ہیں |
| `os` / `os_version` | `Darwin` / `25.3.0` | پلیٹ فارم سپورٹ ترجیحات |
| `python` | `3.11.15` | Python ورژن سپورٹ میٹرکس |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ہمیں اگلے کن ایجنٹس کے ساتھ انٹیگریٹ کرنا چاہیے |
| `is_ci` / `ci_provider` | `true` / `github_actions` | انسانی انسٹالز کو CI شور سے الگ کرنا |

**ہم کیا نہیں بھیجتے**: IP (کلاؤڈ سرور سائیڈ پر درخواست سے ملک کا کوڈ اخذ کرتا ہے، پھر
IP کو ضائع کر دیتا ہے)، ہوسٹ نیم، یوزر نیم، ورک اسپیس
پاتھ، فائل کا مواد، آپ کا api_key، آپ کا ای میل، کچھ بھی PII یا
ورک اسپیس مخصوص۔ وائر پے لوڈ کی آڈٹ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) میں کی جا سکتی ہے۔

**آپٹ آؤٹ** (ان میں سے کوئی ایک اسے مستقل طور پر غیر فعال کر دیتا ہے):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

یہاں نیٹ ورک کی ناکامی کبھی بھی `clawmetry` کو چلنے سے نہیں روکتی — یہ
پنگ ایک ڈیمن تھریڈ پر فائر اینڈ فارگٹ ہے جس کا ٹائم آؤٹ 3 سیکنڈ ہے۔

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> کی جانب سے تیار کردہ · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ماحولیاتی نظام کا حصہ</sub>
</p>
