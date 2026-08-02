<!-- i18n-src:0e34918f8f2e -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **14 AI ایجنٹ رن ٹائمز** کے لیے حقیقی وقت کی مانیٹرنگ: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور 10 مزید۔ آپ کے پورے ایجنٹ بیڑے کے لیے ایک ہی ڈیش بورڈ۔

> 🌐 **اسے پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ صفر ترتیب۔ سب کچھ خودکار طور پر معلوم ہو جاتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے اور بس، کام مکمل۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

ClawMetry کا آغاز OpenClaw کی مانیٹرنگ کے طور پر ہوا تھا، اور اب یہ آپ کے **پورے ایجنٹ بیڑے** کو ایک ہی ڈیش بورڈ میں ماپتا ہے، آپ کی مشین پر ہر رن ٹائم کو خودکار طور پر معلوم کرتے ہوئے:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw اور NemoClaw اوپن سورس ایپ میں مفت ہیں؛ باقی رن ٹائمز ClawMetry Cloud یا سیلف ہوسٹڈ Pro لائسنس کے ساتھ فعال ہوتے ہیں۔ ہیڈر سے رن ٹائم تبدیل کریں اور ہر ٹیب — لاگت، ٹوکنز، ٹولز، ٹریسز — اسی رن ٹائم کے دائرہ کار میں دوبارہ سیٹ ہو جاتا ہے۔ درست مفت/ادائیگی تقسیم، ٹئیر میٹرکس، `/api/entitlement` شکل، اور `clawmetry license` CLI کے لیے **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** دیکھیں۔

## آپ کو کیا ملتا ہے

- **Flow** — چینلز، برین، ٹولز اور واپس تک پیغامات کے بہاؤ کو دکھانے والا لائیو اینیمیٹڈ ڈایاگرام
- **Overview** — ہیلتھ چیکس، سرگرمی کا ہیٹ میپ، سیشن گنتی، ماڈل کی معلومات
- **Usage** — روزانہ/ہفتہ وار/ماہانہ تفصیلات کے ساتھ ٹوکن اور لاگت کی ٹریکنگ
- **Sessions** — ماڈل، ٹوکنز، آخری سرگرمی کے ساتھ فعال ایجنٹ سیشنز
- **Crons** — حیثیت، اگلی رن، دورانیے کے ساتھ شیڈول شدہ جابز
- **Logs** — رنگ کوڈڈ حقیقی وقت لاگ سٹریمنگ
- **Memory** — SOUL.md، MEMORY.md، AGENTS.md، روزانہ نوٹس براؤز کریں
- **Transcripts** — سیشن ہسٹری پڑھنے کے لیے چیٹ بلبلہ UI
- **Alerts** — بجٹ کیپس، ایرر ریٹ ٹرگرز، ایجنٹ آف لائن کی تشخیص؛ Slack، Discord، PagerDuty، Telegram، Email کی طرف روٹ کرتا ہے
- **Approvals** — تباہ کن حذف، فورس پُش، DB میوٹیشنز، sudo، پیکیج انسٹالز، نیٹ ورک کالز کو ایک کلک منظوری کے پیچھے گیٹ کریں

## اسکرین شاٹس

### 🧠 Brain — لائیو ایجنٹ ایونٹ سٹریم
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ٹوکن استعمال اور سیشن کا خلاصہ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — حقیقی وقت ٹول کال فیڈ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ماڈل اور سیشن کے لحاظ سے لاگت کی تفصیل
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ورک اسپیس فائل براؤزر
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — پوزیشن اور آڈٹ لاگ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — بجٹ کیپس، ایرر ریٹ ٹرگرز، Slack / Discord / PagerDuty / Email کے لیے ویب ہکس
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — خطرناک ٹول کالز کو دستی منظوری کے پیچھے گیٹ کریں؛ پالیسی کی بنیاد پر تحفظ کے قواعد
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code کے لیے پری ایگزیکیوشن بلاکنگ** — ایک کمانڈ ایک
PreToolUse ہک انسٹال کرتی ہے جو مماثل ٹول کالز کو چلنے سے *پہلے* روک دیتی ہے اور آپ کے فیصلے کا انتظار کرتی ہے
(آپ کے فون سے ایک ٹیپ کے ساتھ اگر
[کلاؤڈ پُش نوٹیفیکیشنز](https://app.clawmetry.com/push) فعال ہوں):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

انکار صرف اسی ایک ٹول کال کو بلاک کرتا ہے — ایجنٹ اپنا سیشن برقرار رکھتا ہے اور
کوئی اور طریقہ آزما سکتا ہے۔ اپنے فون پر منظوری دینا Claude Code کے اپنے
اجازت کے پرومپٹ کو نظرانداز کر دیتا ہے (آپ پہلے ہی جواب دے چکے ہیں)۔ غیر مماثل ٹولز پر تقریباً 40ms لاگت آتی ہے اور وہ
Claude Code کے عام اجازت کے بہاؤ میں چلے جاتے ہیں۔ آپ کو فون پر پُش نوٹیفیکیشن بھی ملتا ہے جب Claude Code خود
آپ کا انتظار کر رہا ہو (`permission_prompt` / `idle_prompt` اطلاعات)۔

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

## v2 فرنٹ اینڈ ڈویلپمنٹ

v2 React ایپ `frontend/` میں موجود ہے اور `/v2` پر سرو کی جاتی ہے جب Flask
سرور v2 فعال کے ساتھ شروع کیا جاتا ہے۔

ڈویلپ کرتے وقت دو ٹرمینلز استعمال کریں:

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
`http://localhost:8900` کی طرف پراکسی کرتا ہے، تاکہ React ایپ اضافی CORS ترتیب کے بغیر
مقامی Flask سرور سے بات کر سکے۔

Python پیکج کے ساتھ شپ ہونے والا بنڈل بنانے کے لیے:

```bash
cd frontend
npm run build
```

پروڈکشن بنڈل `clawmetry/static/v2/dist/` میں لکھا جاتا ہے۔

## رن ٹائم / ایجنٹ مطابقت

ClawMetry صرف OpenClaw ہی نہیں بلکہ بہت سے AI ایجنٹ رن ٹائمز کو مانیٹر کرتا ہے۔ ہر غیر OpenClaw رن ٹائم ایک مخصوص ریڈر اڈاپٹر بھیجتا ہے جو اس کے مقامی سیشن فارمیٹ کو ClawMetry کی متحد شکلوں میں تبدیل کرتا ہے؛ ڈیمن انہیں اسی DuckDB سٹور + کلاؤڈ سنیپ شاٹ میں شامل کرتا ہے، رن ٹائم کے ٹیگ کے ساتھ، اور Session replay ٹیب ایک سے زیادہ رن ٹائمز موجود ہونے پر **رن ٹائم سوئچر** دکھاتا ہے۔ مکمل میٹرکس + رن ٹائمز شامل کرنے کی گائیڈ کے لیے [`docs/compatibility.md`](docs/compatibility.md) دیکھیں، اور OpenClaw فیملی کے تعارف کے لیے [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) دیکھیں۔

[Perplexity کا numbat](https://github.com/perplexityai/numbat) ایجنٹ سیکیورٹی ٹول چلا رہے ہیں؟ ClawMetry اس کی تلاش اور نفاذ کے فیصلوں کو باکس سے باہر ہی شامل کرتا ہے — [`docs/NUMBAT.md`](docs/NUMBAT.md) دیکھیں۔

| رن ٹائم / ایجنٹ | حیثیت | نوٹس |
|---|---|---|
| **OpenClaw** | مقامی | حوالہ رن ٹائم، خودکار طور پر معلوم |
| **PicoClaw** | بیٹا اڈاپٹر | فلیٹ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)۔ ٹرانسکرپٹس، ماڈل، ٹول کالز۔ |
| **NanoClaw** | بیٹا اڈاپٹر | فی سیشن SQLite (`data/v2-sessions`)۔ ٹرانسکرپٹس + پیغامات کی گنتی۔ |
| **Hermes** | بیٹا اڈاپٹر | SQLite `~/.hermes/state.db`۔ ٹرانسکرپٹس، ماڈل، ٹوکنز/لاگت۔ |
| **Claude Code** | بیٹا اڈاپٹر | JSONL `~/.claude/projects/.../<id>.jsonl`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز + تھنکنگ، ٹوکن استعمال۔ |
| **Codex** | بیٹا اڈاپٹر | رول آؤٹ JSONL `~/.codex/sessions/...`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Cursor** | بیٹا اڈاپٹر | SQLite `state.vscdb`۔ چیٹ/کمپوزر ٹرانسکرپٹس، ماڈل۔ |
| **Aider** | بیٹا اڈاپٹر | فی پراجیکٹ `.aider.chat.history.md`۔ ٹرانسکرپٹس، ماڈل، ٹوکن گنتی۔ |
| **Goose** | بیٹا اڈاپٹر | SQLite `~/.local/share/goose`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، کل ٹوکنز۔ |
| **opencode** | بیٹا اڈاپٹر | SQLite `~/.local/share/opencode`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Qwen Code** | بیٹا اڈاپٹر | JSONL `~/.qwen/projects/.../chats`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Pi** | بیٹا اڈاپٹر | JSONL `~/.pi/agent/sessions`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Deep Agents** | بیٹا اڈاپٹر | SQLite `~/.deepagents/.state/sessions.db`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **n8n** | بیٹا اڈاپٹر | SQLite `~/.n8n/database.sqlite`۔ ورک فلو ایگزیکیوشنز، نوڈ رنز، AI Agent پرومپٹس، جہاں n8n ریکارڈ کرتا ہے وہاں ماڈل + ٹوکنز۔ |
| **Antigravity** | بیٹا اڈاپٹر | `~/.gemini/<flavor>/brain/` کے تحت برین JSONL۔ گفتگو، ٹول اسٹیپس، تھنکنگ، فی جنریشن Gemini ٹوکن تقسیم + لاگت، بیک گراؤنڈ جنریشن خرچ۔ |
| **GitHub Copilot** | بیٹا اڈاپٹر | `~/.copilot/session-state/` کے تحت Copilot CLI کی `events.jsonl` + `session-store.db` فی کال استعمال کی لیجر۔ گفتگو، ٹول کالز، ماڈل روٹنگ، کیش سے آگاہ ٹوکن تقسیم، وینڈر بلڈ AI کریڈٹ لاگت۔ |

"بیٹا اڈاپٹر" کا مطلب ہے کہ ClawMetry اس رن ٹائم کے حقیقی آن ڈسک فارمیٹ کے لیے ایک ریڈر بھیجتا ہے، ہر ایک حقیقی مشین پر حقیقی انسٹال کے خلاف بنایا اور تصدیق شدہ ہے (دیکھیں `tests/fixtures/runtimes/<rt>/`)۔ اڈاپٹرز صرف پڑھنے کے قابل ہیں؛ ہر ایک اس بارے میں دیانتدار ہے کہ اس کا رن ٹائم حقیقت میں کیا اسٹور کرتا ہے (مثلاً PicoClaw/NanoClaw/Cursor ٹوکن لاگت ڈسک پر نہیں لکھتے)۔ جب ایک نوڈ پر کئی رن ٹائمز چلتے ہیں تو رن ٹائم سوئچر سیشنز کے منظر کو صاف ستھری گہری غوطہ زنی کے لیے ایک تک محدود کر دیتا ہے۔

## کسی بھی SDK ایجنٹ کو ٹریک کریں — آؤٹ لوپ لاگت کی تخصیص

اوپر دیے گئے تمام رن ٹائمز اپنے سیشنز ڈسک پر لکھتے ہیں۔ آپ کا اپنا **پروڈکشن ایجنٹ** — وہ جو آپ نے OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B، یا ایک سادہ `httpx` لوپ پر بنایا ہے — ایسا نہیں کرتا۔ ClawMetry کا صفر ترتیب انٹرسیپٹر پھر بھی اس کے LLM کالز (لاگت، ٹوکنز، تاخیر، ایررز) کو `httpx`/`requests` پر بندر پیوند لگا کر پکڑ لیتا ہے:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا `CLAWMETRY_SOURCE=support-agent` ماحولیاتی متغیر) ہر کال کو ایک **نامزد ماخذ** کے ساتھ ٹیگ کرتا ہے، تاکہ آپ کا چلایا ہوا ہر پروڈکٹ ڈیش بورڈ کے Overview پر **🔌 آؤٹ لوپ ذرائع** کارڈ میں اپنی خود کی، لاگت سے منسوب کی جا سکنے والی لائن کے طور پر ظاہر ہو — فی ایجنٹ کالز، فراہم کنندگان، تاخیر، ایرر ریٹ۔ کوئی ماخذ سیٹ نہیں کیا؟ کالز پھر بھی ٹریک ہوتی ہیں؛ کارڈ بس چھپا رہتا ہے۔

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

یہ وہی ڈیٹا لیئر ہے جو رن ٹائم اڈاپٹرز کو فیڈ کرتی ہے (DuckDB → کلاؤڈ سنیپ شاٹ)، اس لیے آؤٹ لوپ ذرائع کلاؤڈ ڈیش بورڈ سے اسی طرح سنک ہوتے ہیں جیسے باقی سب کچھ، اینڈ ٹو اینڈ خفیہ کاری کے ساتھ۔

## OpenTelemetry — وینڈر نیوٹرل، اپنے ٹریسز کہیں بھی بھیجیں

ClawMetry دونوں سمتوں میں **OpenTelemetry** بولتا ہے، **GenAI سیمینٹک کنونشنز** استعمال کرتے ہوئے، تاکہ آپ کے ایجنٹ ٹریسز کبھی بھی ایک ٹول تک محدود نہ ہوں۔

ہر سیشن — LLM کالز، ٹولز، سب ایجنٹس، ٹوکنز، لاگت — کو کسی بھی کلیکٹر (Datadog، Grafana، Honeycomb، یا آپ کا اپنا OTel Collector) کے لیے OTLP/HTTP GenAI اسپینز کے طور پر **ایکسپورٹ** کریں:

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

**Ingest** — بلٹ اِن OTLP ریسیور کسی بھی اور جگہ سے `/v1/traces` اور `/v1/metrics` پر ٹریسز اور میٹرکس قبول کرتا ہے (protobuf ingest کے لیے `pip install clawmetry[otel]`)۔

آپ کو صفر ترتیب، مقامی اول ClawMetry ڈیش بورڈ **اور** آپ کی ٹیم کے پہلے سے چلائے جانے والے کسی بھی بیک اینڈ میں آپ کا ڈیٹا ملتا ہے — کوئی لاک اِن نہیں، دوسرا ایجنٹ انسٹال کرنے کی ضرورت نہیں۔

## ترتیب

زیادہ تر لوگوں کو کسی ترتیب کی ضرورت نہیں۔ ClawMetry آپ کا ورک اسپیس، لاگز، سیشنز، اور کرونز خودکار طور پر معلوم کر لیتا ہے۔

اگر آپ کو حسب ضرورت بنانے کی ضرورت ہو:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

تمام آپشنز: `clawmetry --help`

## معاون چینلز

ClawMetry ہر OpenClaw چینل کے لیے لائیو سرگرمی دکھاتا ہے جو آپ نے ترتیب دیا ہو۔ صرف وہی چینلز جو حقیقت میں آپ کے `openclaw.json` میں سیٹ اپ ہیں Flow ڈایاگرام میں ظاہر ہوتے ہیں — غیر ترتیب شدہ چینلز خودکار طور پر چھپے رہتے ہیں۔

Flow میں کسی بھی چینل نوڈ پر کلک کریں تاکہ آنے والے/جانے والے پیغامات کی گنتی کے ساتھ لائیو چیٹ بلبلہ منظر دیکھ سکیں۔

| چینل | حیثیت | لائیو پاپ اپ | نوٹس |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ مکمل | ✅ | پیغامات، اعداد و شمار، 10s ریفریش |
| 💬 **iMessage** | ✅ مکمل | ✅ | `~/Library/Messages/chat.db` براہ راست پڑھتا ہے |
| 💚 **WhatsApp** | ✅ مکمل | ✅ | WhatsApp Web (Baileys) کے ذریعے |
| 🔵 **Signal** | ✅ مکمل | ✅ | signal-cli کے ذریعے |
| 🟣 **Discord** | ✅ مکمل | ✅ | گلڈ + چینل کی تشخیص |
| 🟪 **Slack** | ✅ مکمل | ✅ | ورک اسپیس + چینل کی تشخیص |
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

> **خودکار تشخیص:** ClawMetry آپ کا `~/.openclaw/openclaw.json` پڑھتا ہے اور صرف وہی چینلز رینڈر کرتا ہے جو آپ نے حقیقت میں ترتیب دیے ہیں۔ کسی دستی سیٹ اپ کی ضرورت نہیں۔

## Docker تعیناتی

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

> **نوٹ:** Docker میں چلاتے وقت، اپنے ایجنٹ کے ڈیٹا + لاگ ڈائریکٹریز (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) کو ماؤنٹ کریں تاکہ ClawMetry آپ کا سیٹ اپ خودکار طور پر معلوم کر سکے۔

## ضروریات

- Python 3.8+
- Flask (pip کے ذریعے خودکار طور پر انسٹال ہوتا ہے)
- ایک AI ایجنٹ رن ٹائم اسی مشین پر: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، n8n، Antigravity، یا GitHub Copilot (یا Docker کے لیے ماؤنٹ شدہ والیومز)
- Linux یا macOS

## NemoClaw / OpenShell سپورٹ

ClawMetry خودکار طور پر [NemoClaw](https://github.com/NVIDIA/NemoClaw) کا پتہ لگاتا ہے — NVIDIA کا انٹرپرائز سیکیورٹی ریپر برائے OpenClaw جو ایجنٹس کو سینڈ باکسڈ OpenShell کنٹینرز کے اندر چلاتا ہے۔

زیادہ تر معاملات میں کسی اضافی ترتیب کی ضرورت نہیں۔ سنک ڈیمن خودکار طور پر سیشن فائلوں کو دریافت کرتا ہے چاہے وہ ہوسٹ پر `~/.openclaw/` میں ہوں یا OpenShell کنٹینر کے اندر۔

### یہ کیسے کام کرتا ہے

ClawMetry دو طریقوں سے NemoClaw کا پتہ لگاتا ہے:

1. **بائنری تشخیص** — `nemoclaw` CLI کی جانچ کرتا ہے اور سینڈ باکس کی معلومات حاصل کرنے کے لیے `nemoclaw status` چلاتا ہے
2. **کنٹینر تشخیص** — چلتے ہوئے Docker کنٹینرز کو `openshell`، `nemoclaw`، یا `ghcr.io/nvidia/` امیجز کے لیے اسکین کرتا ہے، پھر والیوم ماؤنٹس یا `docker cp` کے ذریعے سیشنز پڑھتا ہے

NemoClaw کنٹینرز سے سنک شدہ سیشن فائلوں کو کلاؤڈ ڈیش بورڈ میں `runtime=nemoclaw` اور `container_id` میٹا ڈیٹا کے ساتھ ٹیگ کیا جاتا ہے، تاکہ آپ انہیں معیاری OpenClaw سیشنز سے ایک نظر میں الگ بتا سکیں۔

### تجویز کردہ سیٹ اپ: HOST پر سنک ڈیمن

بہترین تجربے کے لیے، ClawMetry کا سنک ڈیمن **ہوسٹ مشین** پر چلائیں (سینڈ باکس کے اندر نہیں)۔ اس سے NemoClaw نیٹ ورک پالیسی کی پابندیوں سے بچا جا سکتا ہے۔

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سنک ڈیمن خودکار طور پر کسی بھی چلتے ہوئے OpenShell کنٹینرز کے اندر سیشنز تلاش کر لے گا۔

### اختیاری: واضح سینڈ باکس نام

اگر خودکار تشخیص کام نہ کرے، تو ClawMetry کو صحیح سینڈ باکس کی طرف اشارہ کریں:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### سینڈ باکس کے اندر چلانا (اعلیٰ درجے کا)

اگر آپ کو سنک ڈیمن **OpenShell سینڈ باکس کے اندر** چلانا ضروری ہو، تو یہ ایگرس رول اپنی NemoClaw نیٹ ورک پالیسی میں شامل کریں تاکہ یہ ClawMetry ingest API تک پہنچ سکے:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

ان سے اپلائی کریں:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### پورٹس اور اینڈ پوائنٹس

| اینڈ پوائنٹ | پورٹ | پروٹوکول | ضروری |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ہاں (سنک ڈیمن → کلاؤڈ) |
| `localhost:8900` | 8900 | HTTP | ہاں (مقامی ڈیش بورڈ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | کنٹینر سیشن دریافت کے لیے |

سنک ڈیمن صرف `ingest.clawmetry.com` کو آؤٹ باؤنڈ HTTPS کالز کرتا ہے۔ کسی اِن باؤنڈ پورٹس کی ضرورت نہیں۔

---

## کلاؤڈ تعیناتی

SSH ٹنلز، ریورس پراکسی، اور Docker کے لیے **[کلاؤڈ ٹیسٹنگ گائیڈ](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** دیکھیں۔

## ٹیسٹنگ

یہ پراجیکٹ BrowserStack کے ساتھ ٹیسٹ کیا گیا ہے۔

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ٹیلی میٹری

ClawMetry گمنام انسٹال لائف سائیکل پنگز `https://app.clawmetry.com/api/install`
کو بھیجتا ہے: ایک `install` پنگ پہلی بار جب آپ کسی نئی مشین پر `clawmetry` CLI چلاتے ہیں، ایک `update` پنگ
نئے ورژن میں اپ گریڈ کرنے کے بعد پہلی رن پر، اور ایک `onboarded`
پنگ جب آپ ڈیش بورڈ کے اندر آن بورڈنگ کا انتخاب مکمل کرتے ہیں۔ ہم اسے حقیقی انسٹالز گننے کے لیے استعمال کرتے ہیں
(خام PyPI ڈاؤن لوڈ نمبرز ~98% میررز، CI، اور
آٹو اپ ڈیٹ دوبارہ ڈاؤن لوڈز ہیں) اور یہ جاننے کے لیے کہ کون سے ایجنٹ فریم ورک اور
ورژنز حقیقت میں استعمال ہو رہے ہیں۔

**فی لائف سائیکل ایونٹ فی ورژن زیادہ سے زیادہ ایک POST**، جس میں شامل ہے:

| فیلڈ | مثال | وجہ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` پر اسٹور کردہ رینڈم UUID | ڈی ڈپلیکیشن؛ گمنام جب تک آپ واضح طور پر Cloud sync کنیکٹ نہ کریں (اس کے بعد تصدیق شدہ ڈیمن ہارٹ بیٹ اسے لے کر چلتا ہے، اس انسٹال کو آپ کے اکاؤنٹ سے جوڑتا ہے) |
| `event` | `install` / `update` / `onboarded` | نیا انسٹال بمقابلہ موجودہ کا اپ گریڈ |
| `version` | `0.12.167` | حقیقت میں کون سے ورژنز استعمال ہو رہے ہیں |
| `os` / `os_version` | `Darwin` / `25.3.0` | پلیٹ فارم سپورٹ کی ترجیحات |
| `python` | `3.11.15` | Python ورژن سپورٹ میٹرکس |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ہمیں آگے کن ایجنٹس کے ساتھ انضمام کرنا چاہیے |
| `is_ci` / `ci_provider` | `true` / `github_actions` | انسانی انسٹالز کو CI شور سے الگ کرنا |

**ہم کیا نہیں بھیجتے**: IP (کلاؤڈ درخواست سے سرور سائیڈ پر ملک کا کوڈ اخذ کرتا ہے،
پھر IP ضائع کر دیتا ہے)، ہوسٹ نام، صارف نام، ورک اسپیس
پاتھ، فائل کا مواد، آپ کی api_key، آپ کا ای میل، کوئی بھی PII یا
ورک اسپیس مخصوص چیز۔ وائر پے لوڈ کی تصدیق
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) میں کی جا سکتی ہے۔

**آپٹ آؤٹ** (ان میں سے کوئی بھی ایک اسے مستقل طور پر غیر فعال کر دیتا ہے):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

یہاں نیٹ ورک کی ناکامی کبھی بھی `clawmetry` کو چلنے سے نہیں روکتی — یہ
پنگ ایک ڈیمن تھریڈ پر 3 سیکنڈ ٹائم آؤٹ کے ساتھ فائر اینڈ فارگیٹ ہے۔

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
  <sub>تعمیر کردہ <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ایکو سسٹم کا حصہ</sub>
</p>
