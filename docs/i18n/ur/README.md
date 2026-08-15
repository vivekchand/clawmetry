<!-- i18n-src:c422fb7dd0da -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **20 AI ایجنٹ رن ٹائمز** کے لیے حقیقی وقت میں مشاہدہ: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور 16 مزید۔ آپ کے پورے ایجنٹ بیڑے کے لیے ایک ڈیش بورڈ۔

> 🌐 **اسے ان زبانوں میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ صفر ترتیب۔ ہر چیز کو خود بخود پہچانتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے اور بس، کام مکمل۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 20 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

ClawMetry کا آغاز OpenClaw کے مشاہدے کے طور پر ہوا تھا، اور اب یہ آپ کے **پورے ایجنٹ بیڑے** کو ایک ہی ڈیش بورڈ میں ناپتا ہے، آپ کی مشین پر ہر رن ٹائم کو خود بخود پہچانتے ہوئے:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM** · 🐋 **DeepSeek Harness**

OpenClaw اور NemoClaw اوپن سورس ایپ میں مفت ہیں؛ باقی رن ٹائمز ClawMetry Cloud یا سیلف ہوسٹڈ Pro لائسنس کے ساتھ فعال ہوتے ہیں۔ ہیڈر سے رن ٹائمز کے درمیان سوئچ کریں اور ہر ٹیب — لاگت، ٹوکنز، ٹولز، ٹریسز — اسی رن ٹائم کے مطابق دوبارہ ترتیب پاتا ہے۔ درست مفت/ادا شدہ تقسیم، ٹیئر میٹرکس، `/api/entitlement` شکل، اور `clawmetry license` CLI کے لیے **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** دیکھیں۔

## آپ کو کیا ملتا ہے

- **Flow** — ایک لائیو اینیمیٹڈ ڈایاگرام جو چینلز، برین، ٹولز اور واپس تک بہتے پیغامات کو دکھاتا ہے
- **Overview** — ہیلتھ چیکس، سرگرمی کا ہیٹ میپ، سیشن کاؤنٹس، ماڈل کی معلومات
- **Usage** — روزانہ/ہفتہ وار/ماہانہ تقسیم کے ساتھ ٹوکن اور لاگت کی ٹریکنگ
- **Sessions** — ماڈل، ٹوکنز، آخری سرگرمی کے ساتھ فعال ایجنٹ سیشنز
- **Crons** — حیثیت، اگلا رن، دورانیے کے ساتھ شیڈول شدہ جابز
- **Logs** — رنگین حقیقی وقت لاگ اسٹریمنگ
- **Memory** — SOUL.md، MEMORY.md، AGENTS.md، روزانہ نوٹس براؤز کریں
- **Transcripts** — سیشن کی تاریخ پڑھنے کے لیے چیٹ بلبلہ UI
- **Alerts** — بجٹ کی حدیں، ایرر ریٹ ٹرگرز، ایجنٹ آف لائن کی شناخت؛ Slack، Discord، PagerDuty، Telegram، ای میل کی طرف روٹ کرتا ہے
- **Approvals** — تباہ کن ڈیلیٹس، فورس پُشز، ڈی بی میوٹیشنز، sudo، پیکج انسٹالیشنز، نیٹ ورک کالز کو ایک کلک منظوری کے پیچھے روکیں

## اسکرین شاٹس

### 🧠 Brain — لائیو ایجنٹ ایونٹ اسٹریم
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ٹوکن استعمال اور سیشن خلاصہ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — حقیقی وقت ٹول کال فیڈ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ماڈل اور سیشن کے حساب سے لاگت کی تقسیم
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ورک اسپیس فائل براؤزر
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — پوزیشن اور آڈٹ لاگ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — بجٹ کی حدیں، ایرر ریٹ ٹرگرز، Slack / Discord / PagerDuty / ای میل کے لیے ویب ہکس
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — خطرناک ٹول کالز کو دستی منظوری کے پیچھے روکیں؛ پالیسی پر مبنی تحفظاتی قواعد
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code کے لیے عمل درآمد سے پہلے روکنا** — ایک کمانڈ ایک
PreToolUse ہک انسٹال کرتی ہے جو میچ ہونے والی ٹول کالز کو *چلنے سے پہلے*
روک دیتی ہے اور آپ کے فیصلے کا انتظار کرتی ہے (اپنے فون سے ایک ٹیپ کے ذریعے
[کلاؤڈ پش نوٹیفیکیشنز](https://app.clawmetry.com/push) فعال ہونے پر):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ایک انکار صرف اس ایک ٹول کال کو روکتا ہے — ایجنٹ اپنا سیشن برقرار رکھتا ہے اور
کوئی اور طریقہ آزما سکتا ہے۔ اپنے فون پر منظوری دینا Claude Code کے اپنے
اجازت والے پرامپٹ کو چھوڑ دیتا ہے (آپ پہلے ہی جواب دے چکے ہیں)۔ نہ ملنے والے ٹولز
تقریباً 40ms لاگت رکھتے ہیں اور Claude Code کے معمول کے اجازتی بہاؤ میں چلے جاتے
ہیں۔ آپ کو فون پش بھی ملتا ہے جب Claude Code خود آپ کا انتظار کر رہا ہو
(`permission_prompt` / `idle_prompt` نوٹیفیکیشنز)۔

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

## v2 فرنٹ اینڈ ڈیویلپمنٹ

v2 React ایپ `frontend/` میں رہتی ہے اور جب Flask
سرور کو v2 فعال کر کے شروع کیا جائے تو `/v2` پر سرو کی جاتی ہے۔

ڈیویلپمنٹ کے دوران دو ٹرمینلز استعمال کریں:

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
`http://localhost:8900` کی طرف پراکسی کرتا ہے، تاکہ React ایپ اضافی CORS
ترتیب کے بغیر مقامی Flask سرور سے بات کر سکے۔

پیکج کے ساتھ شپ ہونے والا بنڈل بنانے کے لیے:

```bash
cd frontend
npm run build
```

پروڈکشن بنڈل `clawmetry/static/v2/dist/` میں لکھا جاتا ہے۔

## رن ٹائم / ایجنٹ مطابقت

ClawMetry صرف OpenClaw ہی نہیں بلکہ بہت سے AI ایجنٹ رن ٹائمز کا مشاہدہ کرتا ہے۔ ہر غیر OpenClaw رن ٹائم ایک مخصوص ریڈر ایڈاپٹر شپ کرتا ہے جو اس کے مقامی سیشن فارمیٹ کو ClawMetry کی متحد شکلوں میں ترجمہ کرتا ہے؛ ڈیمن انہیں رن ٹائم کے ٹیگ کے ساتھ اسی DuckDB اسٹور + کلاؤڈ اسنیپ شاٹ میں شامل کرتا ہے، اور Session ری پلے ٹیب ایک سے زیادہ رن ٹائم موجود ہونے پر **رن ٹائم سوئچر** دکھاتا ہے۔ مکمل میٹرکس + رن ٹائمز شامل کرنے کی گائیڈ کے لیے [`docs/compatibility.md`](docs/compatibility.md) دیکھیں، اور OpenClaw فیملی کے تعارف کے لیے [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) دیکھیں۔

کیا آپ [Perplexity کا numbat](https://github.com/perplexityai/numbat) ایجنٹ سیکیورٹی ٹول چلا رہے ہیں؟ ClawMetry اس کے نتائج اور نفاذ کے فیصلوں کو بغیر کسی اضافی ترتیب کے ضم کر لیتا ہے — دیکھیں [`docs/NUMBAT.md`](docs/NUMBAT.md)۔

| رن ٹائم / ایجنٹ | حیثیت | نوٹس |
|---|---|---|
| **OpenClaw** | نیٹو | حوالہ رن ٹائم، خود بخود پہچانا جاتا ہے |
| **PicoClaw** | بیٹا ایڈاپٹر | فلیٹ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)۔ ٹرانسکرپٹس، ماڈل، ٹول کالز۔ |
| **NanoClaw** | بیٹا ایڈاپٹر | فی سیشن SQLite (`data/v2-sessions`)۔ ٹرانسکرپٹس + پیغامات کی گنتی۔ |
| **Hermes** | بیٹا ایڈاپٹر | SQLite `~/.hermes/state.db`۔ ٹرانسکرپٹس، ماڈل، ٹوکنز/لاگت۔ |
| **Claude Code** | بیٹا ایڈاپٹر | JSONL `~/.claude/projects/.../<id>.jsonl`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز + سوچ، ٹوکن استعمال۔ |
| **Codex** | بیٹا ایڈاپٹر | رول آؤٹ JSONL `~/.codex/sessions/...`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Cursor** | بیٹا ایڈاپٹر | SQLite `state.vscdb`۔ چیٹ/کمپوزر ٹرانسکرپٹس، ماڈل۔ |
| **Aider** | بیٹا ایڈاپٹر | فی پراجیکٹ `.aider.chat.history.md`۔ ٹرانسکرپٹس، ماڈل، ٹوکن کاؤنٹس۔ |
| **Goose** | بیٹا ایڈاپٹر | SQLite `~/.local/share/goose`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن کل۔ |
| **opencode** | بیٹا ایڈاپٹر | SQLite `~/.local/share/opencode`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Qwen Code** | بیٹا ایڈاپٹر | JSONL `~/.qwen/projects/.../chats`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Pi** | بیٹا ایڈاپٹر | JSONL `~/.pi/agent/sessions`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Deep Agents** | بیٹا ایڈاپٹر | SQLite `~/.deepagents/.state/sessions.db`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **n8n** | بیٹا ایڈاپٹر | SQLite `~/.n8n/database.sqlite`۔ ورک فلو ایگزیکیوشنز، نوڈ رنز، AI Agent پرامپٹس، ماڈل + ٹوکنز جہاں n8n انہیں ریکارڈ کرتا ہے۔ |
| **Antigravity** | بیٹا ایڈاپٹر | برین JSONL بذریعہ `~/.gemini/<flavor>/brain/`۔ گفتگو، ٹول اسٹیپس، سوچ، فی جنریشن Gemini ٹوکن تقسیم + لاگت، بیک گراؤنڈ جنریشن خرچ۔ |
| **GitHub Copilot** | بیٹا ایڈاپٹر | Copilot CLI کا `events.jsonl` بذریعہ `~/.copilot/session-state/` + `session-store.db` فی کال استعمال کا لیجر۔ گفتگو، ٹول کالز، ماڈل روٹنگ، کیش سے آگاہ ٹوکن تقسیم، وینڈر کی طرف سے بل کردہ AI کریڈٹ لاگت۔ |
| **Grok** | بیٹا ایڈاپٹر | xAI Grok Build CLI (`~/.grok/bin/grok` کے تحت Rust بائنری): عالمی ایونٹ لاگ `~/.grok/logs/unified.jsonl` + فی سیشن `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`۔ گفتگو، فی باری ٹوکن تقسیم، ماڈل روٹنگ، اور CLI کا آؤٹ باؤنڈ ریپو پے لوڈ جو `~/.grok/upload_queue/` کے تحت اسٹیج ہوتا ہے تاکہ آپ دیکھ سکیں کہ آپ کی مشین سے کیا نکلا۔ |

"بیٹا ایڈاپٹر" کا مطلب ہے کہ ClawMetry اس رن ٹائم کے حقیقی آن ڈسک فارمیٹ کے لیے ایک ریڈر شپ کرتا ہے، ہر ایک حقیقی مشین پر حقیقی انسٹال کے مقابلے میں بنایا اور تصدیق شدہ (دیکھیں `tests/fixtures/runtimes/<rt>/`)۔ ایڈاپٹرز صرف پڑھنے کے لیے ہیں؛ ہر ایک اپنے رن ٹائم کے اصل ذخیرہ کردہ ڈیٹا کے بارے میں دیانتدار ہے (مثلاً PicoClaw/NanoClaw/Cursor ٹوکن لاگت ڈسک پر نہیں لکھتے)۔ جب ایک نوڈ پر متعدد رن ٹائمز چلتے ہیں، تو رن ٹائم سوئچر صاف ستھری گہرائی سے جانچ کے لیے سیشنز کے منظر کو ایک تک محدود کر دیتا ہے۔

## کسی بھی SDK ایجنٹ کو ٹریک کریں — آؤٹ لوپ لاگت انتساب

اوپر بیان کردہ تمام رن ٹائمز سیشنز کو ڈسک پر لکھتے ہیں۔ آپ کا اپنا **پروڈکشن ایجنٹ** — وہ جو آپ نے OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B، یا ایک سادہ `httpx` لوپ پر بنایا ہے — ایسا نہیں کرتا۔ ClawMetry کا صفر ترتیب انٹرسیپٹر پھر بھی `httpx`/`requests` کو مانکی پیچ کر کے اس کی LLM کالز (لاگت، ٹوکنز، لیٹنسی، ایررز) کیپچر کرتا ہے:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا `CLAWMETRY_SOURCE=support-agent` ماحولیاتی متغیر) ہر کال کو ایک **نامزد ماخذ** کے ساتھ ٹیگ کرتا ہے، تاکہ آپ کا چلایا ہر پروڈکٹ ڈیش بورڈ کے Overview پر **🔌 آؤٹ لوپ سورسز** کارڈ میں اپنی الگ، لاگت کے قابل انتساب لائن کے طور پر ظاہر ہو — کالز، پرووائیڈرز، لیٹنسی، فی ایجنٹ ایرر ریٹ۔ کوئی ماخذ سیٹ نہیں کیا؟ کالز پھر بھی ٹریک ہوتی ہیں؛ صرف کارڈ چھپا رہتا ہے۔

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

یہ وہی ڈیٹا لیئر ہے جو رن ٹائم ایڈاپٹرز کو فیڈ کرتی ہے (DuckDB → کلاؤڈ اسنیپ شاٹ)، اس لیے آؤٹ لوپ سورسز باقی سب کچھ کی طرح کلاؤڈ ڈیش بورڈ سے سنک ہوتے ہیں، اینڈ ٹو اینڈ اینکرپٹڈ۔

## OpenTelemetry — وینڈر نیوٹرل، اپنے ٹریسز کہیں بھی بھیجیں

ClawMetry دونوں سمتوں میں **OpenTelemetry** بولتا ہے، **GenAI سیمینٹک کنونشنز** کا استعمال کرتے ہوئے، تاکہ آپ کے ایجنٹ ٹریسز کبھی بھی کسی ایک ٹول میں بند نہ ہوں۔

ہر سیشن کو **برآمد** کریں — LLM کالز، ٹولز، سب ایجنٹس، ٹوکنز، لاگت — کسی بھی کلیکٹر (Datadog، Grafana، Honeycomb، یا آپ کا اپنا OTel Collector) میں OTLP/HTTP GenAI اسپینز کے طور پر:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

اتھ ہیڈرز اور پول انٹرول اختیاری ماحولیاتی متغیرات ہیں:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**درآمد** — بلٹ اِن OTLP وصول کنندہ کسی بھی چیز سے ٹریسز، لاگز، اور میٹرکس قبول کرتا ہے `/v1/traces`، `/v1/logs`، اور `/v1/metrics` پر۔ کسی بھی OpenTelemetry سے لیس ایپ کو اس کی طرف اشارہ کریں:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:8900 OTEL_EXPORTER_OTLP_PROTOCOL=http/json your-app
```

OTLP/JSON ٹریسز اور لاگز عام `pip install clawmetry` پر کام کرتے ہیں، بغیر کسی اضافی چیز کے۔ پروٹوبف انجیسٹ (اور OTLP/JSON میٹرکس) کے لیے `pip install clawmetry[otel]` درکار ہے۔ ایک ایپ جو اپنا `service.name` سیٹ کرتی ہے، رن ٹائم سوئچر میں اپنے ہی ایجنٹ کے طور پر ظاہر ہوتی ہے، اپنی لاگت اور ٹوکنز کے ساتھ۔

آپ کو صفر ترتیب، لوکل فرسٹ ClawMetry ڈیش بورڈ **اور** آپ کی ٹیم جو بھی بیک اینڈ پہلے سے چلا رہی ہے اس میں آپ کا ڈیٹا دونوں ملتے ہیں — کوئی لاک اِن نہیں، دوسرا ایجنٹ انسٹال کرنے کی ضرورت نہیں۔

## ترتیب

زیادہ تر لوگوں کو کسی ترتیب کی ضرورت نہیں۔ ClawMetry آپ کا ورک اسپیس، لاگز، سیشنز، اور crons خود بخود پہچان لیتا ہے۔

اگر آپ کو حسب ضرورت بنانا ہو:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

تمام آپشنز: `clawmetry --help`

## معاون چینلز

ClawMetry آپ کے ترتیب شدہ ہر OpenClaw چینل کے لیے لائیو سرگرمی دکھاتا ہے۔ صرف وہ چینلز جو حقیقت میں آپ کے `openclaw.json` میں سیٹ اپ ہیں Flow ڈایاگرام میں ظاہر ہوتے ہیں — غیر ترتیب شدہ چینلز خود بخود چھپا دیے جاتے ہیں۔

Flow میں کسی بھی چینل نوڈ پر کلک کر کے آنے اور جانے والے پیغامات کی تعداد کے ساتھ لائیو چیٹ بلبلہ ویو دیکھیں۔

| چینل | حیثیت | لائیو پاپ اپ | نوٹس |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ مکمل | ✅ | پیغامات، اعداد و شمار، 10s تازہ کاری |
| 💬 **iMessage** | ✅ مکمل | ✅ | `~/Library/Messages/chat.db` براہ راست پڑھتا ہے |
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

> **خودکار شناخت:** ClawMetry آپ کا `~/.openclaw/openclaw.json` پڑھتا ہے اور صرف وہی چینلز رینڈر کرتا ہے جو آپ نے حقیقت میں ترتیب دیے ہیں۔ کسی دستی سیٹ اپ کی ضرورت نہیں۔

## Docker پر تعیناتی

کیا آپ ClawMetry کو کنٹینر میں چلانا چاہتے ہیں؟ کوئی مسئلہ نہیں! 🐳

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

> **نوٹ:** Docker میں چلاتے وقت، اپنے ایجنٹ کی ڈیٹا + لاگ ڈائریکٹریز (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) کو ماؤنٹ کریں تاکہ ClawMetry آپ کے سیٹ اپ کو خود بخود پہچان سکے۔

## ضروریات

- Python 3.8+
- Flask (pip کے ذریعے خود بخود انسٹال ہوتا ہے)
- ایک ہی مشین پر AI ایجنٹ رن ٹائم: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، n8n، Antigravity، GitHub Copilot، Grok، یا QM (یا Docker کے لیے ماؤنٹ شدہ والیومز)
- Linux یا macOS

## NemoClaw / OpenShell سپورٹ

ClawMetry خود بخود [NemoClaw](https://github.com/NVIDIA/NemoClaw) — OpenClaw کے لیے NVIDIA کا انٹرپرائز سیکیورٹی ریپر جو ایجنٹس کو سینڈ باکسڈ OpenShell کنٹینرز کے اندر چلاتا ہے — کی شناخت کرتا ہے۔

زیادہ تر معاملات میں کسی اضافی ترتیب کی ضرورت نہیں۔ سنک ڈیمن خود بخود سیشن فائلوں کو ڈھونڈ لیتا ہے چاہے وہ ہوسٹ پر `~/.openclaw/` میں ہوں یا OpenShell کنٹینر کے اندر۔

### یہ کیسے کام کرتا ہے

ClawMetry دو طریقوں سے NemoClaw کی شناخت کرتا ہے:

1. **بائنری شناخت** — `nemoclaw` CLI کی موجودگی چیک کرتا ہے اور سینڈ باکس کی معلومات حاصل کرنے کے لیے `nemoclaw status` چلاتا ہے
2. **کنٹینر شناخت** — چلتے ہوئے Docker کنٹینرز کو `openshell`، `nemoclaw`، یا `ghcr.io/nvidia/` امیجز کے لیے اسکین کرتا ہے، پھر والیوم ماؤنٹس یا `docker cp` کے ذریعے سیشنز پڑھتا ہے

NemoClaw کنٹینرز سے سنک شدہ سیشن فائلیں کلاؤڈ ڈیش بورڈ میں `runtime=nemoclaw` اور `container_id` میٹا ڈیٹا کے ساتھ ٹیگ کی جاتی ہیں، تاکہ آپ ایک نظر میں انہیں معیاری OpenClaw سیشنز سے الگ بتا سکیں۔

### تجویز کردہ سیٹ اپ: ہوسٹ پر سنک ڈیمن

بہترین تجربے کے لیے، ClawMetry کا سنک ڈیمن **ہوسٹ مشین** پر چلائیں (سینڈ باکس کے اندر نہیں)۔ یہ NemoClaw کی نیٹ ورک پالیسی کی پابندیوں سے بچاتا ہے۔

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سنک ڈیمن خود بخود کسی بھی چلتے ہوئے OpenShell کنٹینر کے اندر سیشنز ڈھونڈ لے گا۔

### اختیاری: واضح سینڈ باکس نام

اگر خودکار شناخت کام نہ کرے، تو ClawMetry کو صحیح سینڈ باکس کی طرف اشارہ کریں:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### سینڈ باکس کے اندر چلانا (ایڈوانسڈ)

اگر آپ کو سنک ڈیمن **اندر** OpenShell سینڈ باکس میں چلانا ہو، تو اپنی NemoClaw نیٹ ورک پالیسی میں یہ ایگریس رول شامل کریں تاکہ یہ ClawMetry ingest API تک پہنچ سکے:

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

| اینڈ پوائنٹ | پورٹ | پروٹوکول | لازمی |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ہاں (سنک ڈیمن → کلاؤڈ) |
| `localhost:8900` | 8900 | HTTP | ہاں (مقامی ڈیش بورڈ UI) |
| Docker سوکٹ (`/var/run/docker.sock`) | — | یونکس سوکٹ | کنٹینر سیشن دریافت کے لیے |

سنک ڈیمن صرف `ingest.clawmetry.com` کے لیے آؤٹ باؤنڈ HTTPS کالز کرتا ہے۔ کوئی اِن باؤنڈ پورٹس درکار نہیں۔

---

## کلاؤڈ تعیناتی

SSH ٹنلز، ریورس پراکسی، اور Docker کے لیے **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** دیکھیں۔

## ٹیسٹنگ

اس پراجیکٹ کی جانچ BrowserStack کے ساتھ کی جاتی ہے۔

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ٹیلی میٹری

ClawMetry گمنام انسٹال لائف سائیکل پنگز بھیجتا ہے
`https://app.clawmetry.com/api/install` کو: ایک `install` پنگ پہلی
بار جب آپ نئی مشین پر `clawmetry` CLI چلاتے ہیں، ایک `update` پنگ
نئے ورژن میں اپ گریڈ کرنے کے بعد پہلی بار، اور ایک `onboarded`
پنگ جب آپ ڈیش بورڈ کے اندر آن بورڈنگ کا انتخاب مکمل کرتے ہیں۔ ہم اسے
حقیقی انسٹالز شمار کرنے کے لیے استعمال کرتے ہیں (خام PyPI ڈاؤن لوڈ اعداد و شمار
تقریباً 98% میررز، CI، اور خودکار اپ ڈیٹ دوبارہ ڈاؤن لوڈز ہوتے ہیں) اور یہ جاننے کے
لیے کہ کون سے ایجنٹ فریم ورکس اور ورژنز اصل میں استعمال میں ہیں۔

**فی لائف سائیکل ایونٹ فی ورژن زیادہ سے زیادہ ایک POST**، جس میں شامل ہے:

| فیلڈ | مثال | وجہ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` پر محفوظ رینڈم UUID | ڈی ڈپلیکیشن؛ گمنام جب تک آپ واضح طور پر Cloud sync سے کنیکٹ نہ کریں (تصدیق شدہ ڈیمن ہارٹ بیٹ پھر اسے لے جاتا ہے، اس انسٹال کو آپ کے اکاؤنٹ سے جوڑتا ہے) |
| `event` | `install` / `update` / `onboarded` | نئی انسٹال بمقابلہ موجودہ کی اپ گریڈ |
| `version` | `0.12.167` | استعمال میں کون سے ورژنز ہیں |
| `os` / `os_version` | `Darwin` / `25.3.0` | پلیٹ فارم سپورٹ ترجیحات |
| `python` | `3.11.15` | Python ورژن سپورٹ میٹرکس |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ہمیں آگے کن ایجنٹس کے ساتھ ضم ہونا چاہیے |
| `is_ci` / `ci_provider` | `true` / `github_actions` | انسانی انسٹالز کو CI شور سے الگ کرنا |

**ہم کیا نہیں بھیجتے**: IP (کلاؤڈ سرور کی طرف سے درخواست سے ملک کا کوڈ اخذ
کرتا ہے، پھر IP کو مسترد کر دیتا ہے)، ہوسٹ نام، صارف نام، ورک اسپیس
پاتھ، فائل کا مواد، آپ کی api_key، آپ کا ای میل، کوئی بھی ذاتی طور پر
شناخت کے قابل معلومات یا ورک اسپیس سے متعلق چیز۔ وائر پے لوڈ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) میں قابل جانچ ہے۔

**اختیار سے باہر نکلیں** (ان میں سے کوئی بھی ایک اسے مستقل طور پر غیر فعال کر دیتا ہے):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

نیٹ ورک کی ناکامی یہاں کبھی بھی `clawmetry` کو چلنے سے نہیں روکتی — پنگ
ایک ڈیمن تھریڈ پر 3 سیکنڈ کے ٹائم آؤٹ کے ساتھ فائر اینڈ فرگیٹ ہے۔

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
  <sub>تیار کردہ <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ماحولیاتی نظام کا حصہ</sub>
</p>
