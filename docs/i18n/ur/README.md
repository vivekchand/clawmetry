<!-- i18n-src:191e9094d7fa -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **14 AI ایجنٹ رن ٹائمز** کے لیے ریئل ٹائم آبزروی بیلٹی: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور مزید 10۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ڈیش بورڈ۔

> 🌐 **اسے ان زبانوں میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ صفر کنفیگریشن۔ ہر چیز کو خودکار طور پر پہچانتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے اور بس، کام ہو گیا۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

ClawMetry کا آغاز OpenClaw کے لیے آبزروی بیلٹی کے طور پر ہوا تھا، اور اب یہ آپ کے **پورے ایجنٹ فلیٹ** کو ایک ہی ڈیش بورڈ میں ناپتا ہے، آپ کی مشین پر ہر رن ٹائم کو خودکار طور پر پہچانتے ہوئے:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw اور NemoClaw اوپن سورس ایپ میں مفت ہیں؛ باقی رن ٹائمز ClawMetry Cloud یا سیلف ہوسٹڈ Pro لائسنس کے ساتھ فعال ہوتے ہیں۔ ہیڈر سے رن ٹائم تبدیل کریں اور ہر ٹیب — لاگت، ٹوکنز، ٹولز، ٹریسز — اسی رن ٹائم کے دائرے میں دوبارہ ترتیب پاتا ہے۔ درست مفت/ادا شدہ تقسیم، ٹائر میٹرکس، `/api/entitlement` شکل، اور `clawmetry license` CLI کے لیے **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** دیکھیں۔

## آپ کو کیا ملتا ہے

- **Flow** — ایک لائیو اینیمیٹڈ ڈایاگرام جو چینلز، برین، ٹولز، اور واپس تک پیغامات کے بہاؤ کو دکھاتا ہے
- **Overview** — ہیلتھ چیکس، ایکٹیویٹی ہیٹ میپ، سیشن کاؤنٹس، ماڈل کی معلومات
- **Usage** — روزانہ/ہفتہ وار/ماہانہ تفصیل کے ساتھ ٹوکن اور لاگت کی نگرانی
- **Sessions** — ماڈل، ٹوکنز، آخری سرگرمی کے ساتھ فعال ایجنٹ سیشنز
- **Crons** — سٹیٹس، اگلا رن، دورانیے کے ساتھ شیڈولڈ جابز
- **Logs** — رنگین کوڈڈ ریئل ٹائم لاگ سٹریمنگ
- **Memory** — SOUL.md، MEMORY.md، AGENTS.md، روزانہ نوٹس براؤز کریں
- **Transcripts** — سیشن ہسٹریز پڑھنے کے لیے چیٹ بلبلہ UI
- **Alerts** — بجٹ کیپس، ایرر ریٹ ٹرگرز، ایجنٹ آف لائن کی پہچان؛ Slack، Discord، PagerDuty، Telegram، Email پر روٹ کرتا ہے
- **Approvals** — تباہ کن ڈیلیٹس، فورس پُشز، ڈی بی میوٹیشنز، sudo، پیکیج انسٹالیشنز، نیٹ ورک کالز کو ایک کلک سائن آف کے پیچھے روکیں

## اسکرین شاٹس

### 🧠 Brain — لائیو ایجنٹ ایونٹ سٹریم
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ٹوکن استعمال اور سیشن خلاصہ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ریئل ٹائم ٹول کال فیڈ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ماڈل اور سیشن کے حساب سے لاگت کی تفصیل
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ورک اسپیس فائل براؤزر
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — پوزیشن اور آڈٹ لاگ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — بجٹ کیپس، ایرر ریٹ ٹرگرز، Slack / Discord / PagerDuty / Email کو ویب ہکس
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — خطرناک ٹول کالز کو مینوئل سائن آف کے پیچھے روکیں؛ پالیسی کے تحت تحفظ کے قواعد
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**Claude Code کے لیے ایگزیکیوشن سے پہلے بلاکنگ** — ایک کمانڈ ایک
PreToolUse ہک انسٹال کرتی ہے جو ملتی جلتی ٹول کالز کو ان کے چلنے سے *پہلے*
روکتی ہے اور آپ کے فیصلے کا انتظار کرتی ہے (اپنے فون سے ایک ٹیپ کے ساتھ
[کلاؤڈ پش نوٹیفیکیشنز](https://app.clawmetry.com/push) فعال ہونے پر):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

ایک ڈینائی صرف اس ایک ٹول کال کو بلاک کرتی ہے — ایجنٹ اپنا سیشن برقرار رکھتا ہے اور
کوئی دوسرا طریقہ آزما سکتا ہے۔ آپ کے فون پر منظوری دینا Claude Code کے اپنے
پرمیشن پرومپٹ کو چھوڑ دیتا ہے (آپ پہلے ہی جواب دے چکے ہیں)۔ غیر ملتی ہوئی ٹولز کی
لاگت تقریباً 40ms ہوتی ہے اور وہ Claude Code کے عام پرمیشن فلو میں چلی جاتی ہیں۔
جب Claude Code خود آپ کا انتظار کر رہا ہو تو آپ کو فون پر پش بھی ملتا ہے
(`permission_prompt` / `idle_prompt` نوٹیفیکیشنز)۔

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

## v2 فرنٹ اینڈ ڈیویلپمنٹ

v2 React ایپ `frontend/` میں موجود ہے اور جب Flask
سرور v2 فعال کر کے شروع کیا جائے تو یہ `/v2` پر سرو ہوتی ہے۔

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
`http://localhost:8900` تک پراکسی کرتا ہے، تاکہ React ایپ اضافی CORS سیٹ اپ
کے بغیر مقامی Flask سرور سے بات کر سکے۔

وہ بنڈل بنانے کے لیے جو Python پیکج کے ساتھ شپ ہوتا ہے:

```bash
cd frontend
npm run build
```

پروڈکشن بنڈل `clawmetry/static/v2/dist/` میں لکھا جاتا ہے۔

## رن ٹائم / ایجنٹ مطابقت

ClawMetry بہت سے AI ایجنٹ رن ٹائمز کا مشاہدہ کرتا ہے، نہ صرف OpenClaw کا۔ ہر غیر OpenClaw رن ٹائم ایک مخصوص ریڈر اڈاپٹر کے ساتھ آتا ہے جو اس کے نیٹو سیشن فارمیٹ کو ClawMetry کی متحدہ شکلوں میں تبدیل کرتا ہے؛ ڈیمن انہیں اسی DuckDB اسٹور + کلاؤڈ سنیپ شاٹ میں شامل کرتا ہے، جو رن ٹائم کے ساتھ ٹیگ ہوتا ہے، اور Session replay ٹیب جب ایک سے زیادہ موجود ہوں تو ایک **رن ٹائم سوئچر** دکھاتا ہے۔ مکمل میٹرکس + رن ٹائمز شامل کرنے کی گائیڈ کے لیے [`docs/compatibility.md`](docs/compatibility.md) دیکھیں، اور OpenClaw فیملی کے تعارف کے لیے [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) دیکھیں۔

[Perplexity کا numbat](https://github.com/perplexityai/numbat) ایجنٹ سیکیورٹی ٹول چلا رہے ہیں؟ ClawMetry اس کی تلاشات اور نفاذ کے فیصلوں کو ابتدا ہی سے شامل کرتا ہے — دیکھیں [`docs/NUMBAT.md`](docs/NUMBAT.md)۔

| رن ٹائم / ایجنٹ | حیثیت | نوٹس |
|---|---|---|
| **OpenClaw** | نیٹو | حوالہ رن ٹائم، خودکار طور پر پہچانا جاتا ہے |
| **PicoClaw** | بیٹا اڈاپٹر | فلیٹ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)۔ ٹرانسکرپٹس، ماڈل، ٹول کالز۔ |
| **NanoClaw** | بیٹا اڈاپٹر | فی سیشن SQLite (`data/v2-sessions`)۔ ٹرانسکرپٹس + پیغامات کی گنتی۔ |
| **Hermes** | بیٹا اڈاپٹر | SQLite `~/.hermes/state.db`۔ ٹرانسکرپٹس، ماڈل، ٹوکنز/لاگت۔ |
| **Claude Code** | بیٹا اڈاپٹر | JSONL `~/.claude/projects/.../<id>.jsonl`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز + سوچ، ٹوکن استعمال۔ |
| **Codex** | بیٹا اڈاپٹر | رول آؤٹ JSONL `~/.codex/sessions/...`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Cursor** | بیٹا اڈاپٹر | SQLite `state.vscdb`۔ چیٹ/کمپوزر ٹرانسکرپٹس، ماڈل۔ |
| **Aider** | بیٹا اڈاپٹر | ہر پراجیکٹ کے لیے `.aider.chat.history.md`۔ ٹرانسکرپٹس، ماڈل، ٹوکن گنتی۔ |
| **Goose** | بیٹا اڈاپٹر | SQLite `~/.local/share/goose`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن کل۔ |
| **opencode** | بیٹا اڈاپٹر | SQLite `~/.local/share/opencode`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Qwen Code** | بیٹا اڈاپٹر | JSONL `~/.qwen/projects/.../chats`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Pi** | بیٹا اڈاپٹر | JSONL `~/.pi/agent/sessions`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Deep Agents** | بیٹا اڈاپٹر | SQLite `~/.deepagents/.state/sessions.db`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **n8n** | بیٹا اڈاپٹر | SQLite `~/.n8n/database.sqlite`۔ ورک فلو ایگزیکیوشنز، نوڈ رنز، AI Agent پرومپٹس، ماڈل + ٹوکنز جہاں n8n انہیں ریکارڈ کرتا ہے۔ |
| **Antigravity** | بیٹا اڈاپٹر | `~/.gemini/<flavor>/brain/` کے تحت Brain JSONL۔ گفتگو، ٹول اسٹیپس، سوچ، فی جنریشن Gemini ٹوکن تقسیم + لاگت، بیک گراؤنڈ جنریشن خرچ۔ |

"بیٹا اڈاپٹر" کا مطلب ہے کہ ClawMetry اس رن ٹائم کے حقیقی آن ڈسک فارمیٹ کے لیے ایک ریڈر شپ کرتا ہے، ہر ایک کو حقیقی مشین پر حقیقی انسٹال کے مقابلے میں بنایا اور تصدیق شدہ کیا گیا ہے (دیکھیں `tests/fixtures/runtimes/<rt>/`)۔ اڈاپٹرز ریڈ اونلی ہیں؛ ہر ایک اس بارے میں دیانتدار ہے کہ اس کا رن ٹائم اصل میں کیا محفوظ کرتا ہے (مثلاً PicoClaw/NanoClaw/Cursor ٹوکن لاگت کو ڈسک پر نہیں لکھتے)۔ جب ایک نوڈ پر کئی رن ٹائمز چلتے ہیں، تو رن ٹائم سوئچر سیشنز ویو کو ایک صاف ستھری گہرائی سے جانچ کے لیے ایک تک محدود کر دیتا ہے۔

## کسی بھی SDK ایجنٹ کو ٹریک کریں — آؤٹ لوپ لاگت کی نسبت

اوپر دیے گئے تمام رن ٹائمز سیشنز کو ڈسک پر لکھتے ہیں۔ آپ کا اپنا **پروڈکشن ایجنٹ** — وہ جو آپ نے OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B، یا ایک عام `httpx` لوپ پر بنایا — ایسا نہیں کرتا۔ ClawMetry کا صفر کنفیگریشن انٹرسیپٹر اب بھی `httpx`/`requests` کو مانکی پیچ کر کے اس کی LLM کالز (لاگت، ٹوکنز، لیٹنسی، ایررز) کو پکڑتا ہے:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا `CLAWMETRY_SOURCE=support-agent` انوائرمنٹ ویری ایبل) ہر کال کو ایک **نامزد سورس** کے ساتھ ٹیگ کرتا ہے، تاکہ آپ کا چلایا ہوا ہر پروڈکٹ ڈیش بورڈ کے Overview پر **🔌 آؤٹ لوپ سورسز** کارڈ میں اپنی ایک الگ، لاگت کی نسبت دی جا سکنے والی لائن کے طور پر ظاہر ہو — کالز، پرووائیڈرز، لیٹنسی، فی ایجنٹ ایرر ریٹ۔ کوئی سورس سیٹ نہیں کیا؟ کالز پھر بھی ٹریک ہوتی ہیں؛ کارڈ بس چھپا رہتا ہے۔

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

یہ وہی ڈیٹا لیئر ہے جو رن ٹائم اڈاپٹرز کو کھلاتی ہے (DuckDB → کلاؤڈ سنیپ شاٹ)، لہذا آؤٹ لوپ سورسز باقی سب چیزوں کی طرح، E2E انکرپٹڈ، کلاؤڈ ڈیش بورڈ کے ساتھ ہم آہنگ ہوتے ہیں۔

## OpenTelemetry — پرووائیڈر سے آزاد، اپنے ٹریسز کہیں بھی بھیجیں

ClawMetry **GenAI سیمینٹک کنونشنز** استعمال کرتے ہوئے دونوں سمتوں میں **OpenTelemetry** بولتا ہے، تاکہ آپ کے ایجنٹ ٹریسز کبھی بھی ایک ٹول تک محدود نہ ہوں۔

ہر سیشن — LLM کالز، ٹولز، ذیلی ایجنٹس، ٹوکنز، لاگت — کو کسی بھی کلیکٹر (Datadog، Grafana، Honeycomb، یا آپ کا اپنا OTel Collector) کے لیے OTLP/HTTP GenAI اسپینز کے طور پر **ایکسپورٹ** کریں:

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

آتھ ہیڈرز اور پول انٹرول اختیاری انوائرمنٹ ویریایبلز ہیں:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**انجیسٹ** — بلٹ ان OTLP ریسیور کسی بھی دوسری چیز سے `/v1/traces` اور `/v1/metrics` پر ٹریسز اور میٹرکس قبول کرتا ہے (پروٹو بف انجیسٹ کے لیے `pip install clawmetry[otel]`)۔

آپ کو صفر کنفیگریشن، لوکل فرسٹ ClawMetry ڈیش بورڈ **اور** آپ کی ٹیم جو بھی بیک اینڈ پہلے سے چلاتی ہے اس میں آپ کا ڈیٹا ملتا ہے — کوئی لاک اِن نہیں، انسٹال کرنے کے لیے کوئی دوسرا ایجنٹ نہیں۔

## کنفیگریشن

زیادہ تر لوگوں کو کسی کنفیگریشن کی ضرورت نہیں پڑتی۔ ClawMetry آپ کے ورک اسپیس، لاگز، سیشنز، اور کرونز کو خودکار طور پر پہچانتا ہے۔

اگر آپ کو حسب ضرورت بنانے کی ضرورت ہو:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

تمام آپشنز: `clawmetry --help`

## سپورٹڈ چینلز

ClawMetry آپ کے کنفیگر کیے گئے ہر OpenClaw چینل کے لیے لائیو سرگرمی دکھاتا ہے۔ صرف وہی چینلز جو آپ کے `openclaw.json` میں واقعی سیٹ اپ ہیں Flow ڈایاگرام میں ظاہر ہوتے ہیں — غیر کنفیگرڈ چینلز خودکار طور پر چھپا دیے جاتے ہیں۔

Flow میں کسی بھی چینل نوڈ پر کلک کریں تاکہ آنے والے/جانے والے پیغامات کی گنتی کے ساتھ ایک لائیو چیٹ بلبلہ ویو دیکھ سکیں۔

| چینل | حیثیت | لائیو پاپ اپ | نوٹس |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ مکمل | ✅ | پیغامات، اعداد و شمار، 10 سیکنڈ ریفریش |
| 💬 **iMessage** | ✅ مکمل | ✅ | `~/Library/Messages/chat.db` کو براہ راست پڑھتا ہے |
| 💚 **WhatsApp** | ✅ مکمل | ✅ | WhatsApp Web (Baileys) کے ذریعے |
| 🔵 **Signal** | ✅ مکمل | ✅ | signal-cli کے ذریعے |
| 🟣 **Discord** | ✅ مکمل | ✅ | گلڈ + چینل کی پہچان |
| 🟪 **Slack** | ✅ مکمل | ✅ | ورک اسپیس + چینل کی پہچان |
| 🌐 **Webchat** | ✅ مکمل | ✅ | بلٹ ان ویب UI سیشنز |
| 📡 **IRC** | ✅ مکمل | ✅ | ٹرمینل طرز کا بلبلہ UI |
| 🍏 **BlueBubbles** | ✅ مکمل | ✅ | BlueBubbles REST API کے ذریعے iMessage |
| 🔵 **Google Chat** | ✅ مکمل | ✅ | Chat API ویب ہکس کے ذریعے |
| 🟣 **MS Teams** | ✅ مکمل | ✅ | Teams بوٹ پلگ اِن کے ذریعے |
| 🔷 **Mattermost** | ✅ مکمل | ✅ | سیلف ہوسٹڈ ٹیم چیٹ |
| 🟩 **Matrix** | ✅ مکمل | ✅ | غیر مرکزی، E2EE سپورٹ |
| 🟢 **LINE** | ✅ مکمل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ مکمل | ✅ | غیر مرکزی NIP-04 DMs |
| 🟣 **Twitch** | ✅ مکمل | ✅ | IRC کنکشن کے ذریعے چیٹ |
| 🔷 **Feishu/Lark** | ✅ مکمل | ✅ | ویب سوکٹ ایونٹ سبسکرپشن |
| 🔵 **Zalo** | ✅ مکمل | ✅ | Zalo Bot API |

> **خودکار پہچان:** ClawMetry آپ کا `~/.openclaw/openclaw.json` پڑھتا ہے اور صرف وہی چینلز رینڈر کرتا ہے جو آپ نے واقعی کنفیگر کیے ہیں۔ کسی مینوئل سیٹ اپ کی ضرورت نہیں۔

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

> **نوٹ:** Docker میں چلاتے وقت، اپنے ایجنٹ کی ڈیٹا + لاگ ڈائریکٹریز (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) کو ماؤنٹ کریں تاکہ ClawMetry آپ کا سیٹ اپ خودکار طور پر پہچان سکے۔

## ضروریات

- Python 3.8+
- Flask (pip کے ذریعے خودکار طور پر انسٹال ہو جاتا ہے)
- اسی مشین پر ایک AI ایجنٹ رن ٹائم: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، n8n، یا Antigravity (یا Docker کے لیے ماؤنٹڈ والیومز)
- Linux یا macOS

## NemoClaw / OpenShell سپورٹ

ClawMetry خودکار طور پر [NemoClaw](https://github.com/NVIDIA/NemoClaw) کو پہچانتا ہے — NVIDIA کا انٹرپرائز سیکیورٹی ریپر برائے OpenClaw جو ایجنٹس کو سینڈ باکسڈ OpenShell کنٹینرز کے اندر چلاتا ہے۔

زیادہ تر معاملات میں کسی اضافی کنفیگریشن کی ضرورت نہیں۔ سنک ڈیمن خود بخود سیشن فائلوں کو تلاش کر لیتا ہے چاہے وہ ہوسٹ پر `~/.openclaw/` میں ہوں یا OpenShell کنٹینر کے اندر۔

### یہ کیسے کام کرتا ہے

ClawMetry NemoClaw کو دو طریقوں سے پہچانتا ہے:

1. **بائنری کی پہچان** — `nemoclaw` CLI کی جانچ کرتا ہے اور سینڈ باکس کی معلومات حاصل کرنے کے لیے `nemoclaw status` چلاتا ہے
2. **کنٹینر کی پہچان** — چلتے ہوئے Docker کنٹینرز کو `openshell`، `nemoclaw`، یا `ghcr.io/nvidia/` امیجز کے لیے اسکین کرتا ہے، پھر والیوم ماؤنٹس یا `docker cp` کے ذریعے سیشنز پڑھتا ہے

NemoClaw کنٹینرز سے سنک کی گئی سیشن فائلوں کو کلاؤڈ ڈیش بورڈ میں `runtime=nemoclaw` اور `container_id` میٹا ڈیٹا کے ساتھ ٹیگ کیا جاتا ہے، تاکہ آپ ایک نظر میں انہیں معیاری OpenClaw سیشنز سے الگ بتا سکیں۔

### تجویز کردہ سیٹ اپ: HOST پر سنک ڈیمن

بہترین تجربے کے لیے، ClawMetry کے سنک ڈیمن کو **ہوسٹ مشین** پر چلائیں (سینڈ باکس کے اندر نہیں)۔ یہ NemoClaw نیٹ ورک پالیسی کی پابندیوں سے بچاتا ہے۔

```bash
# On the host (outside the sandbox)
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

اگر آپ کو سنک ڈیمن کو OpenShell سینڈ باکس کے **اندر** چلانا ہی پڑے، تو اپنی NemoClaw نیٹ ورک پالیسی میں یہ ایگریس رول شامل کریں تاکہ یہ ClawMetry ingest API تک پہنچ سکے:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

اس کے ساتھ اپلائی کریں:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### پورٹس اور اینڈ پوائنٹس

| اینڈ پوائنٹ | پورٹ | پروٹوکول | ضروری |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | ہاں (سنک ڈیمن → کلاؤڈ) |
| `localhost:8900` | 8900 | HTTP | ہاں (مقامی ڈیش بورڈ UI) |
| Docker socket (`/var/run/docker.sock`) | — | Unix socket | کنٹینر سیشن کی تلاش کے لیے |

سنک ڈیمن صرف `ingest.clawmetry.com` کو آؤٹ باؤنڈ HTTPS کالز کرتا ہے۔ کسی اِن باؤنڈ پورٹ کی ضرورت نہیں۔

---

## کلاؤڈ ڈیپلائمنٹ

SSH ٹنلز، ریورس پراکسی، اور Docker کے لیے **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** دیکھیں۔

## ٹیسٹنگ

اس پراجیکٹ کی BrowserStack کے ساتھ جانچ کی جاتی ہے۔

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ٹیلی میٹری

ClawMetry گمنام انسٹال لائف سائیکل پنگز
`https://app.clawmetry.com/api/install` کو بھیجتا ہے: نئی مشین پر پہلی بار
`clawmetry` CLI چلانے پر ایک `install` پنگ، نئے ورژن میں اپ گریڈ کے بعد پہلی
رن پر ایک `update` پنگ، اور جب آپ ان ڈیش بورڈ آنبورڈنگ کا انتخاب مکمل کرتے
ہیں تو ایک `onboarded` پنگ۔ ہم اسے حقیقی انسٹالز شمار کرنے کے لیے استعمال
کرتے ہیں (خام PyPI ڈاؤن لوڈ نمبرز تقریباً 98% مررز، CI، اور آٹو اپڈیٹ کے
دوبارہ ڈاؤن لوڈز ہیں) اور یہ جاننے کے لیے کہ کون سے ایجنٹ فریم ورکس اور
ورژنز واقعی استعمال میں ہیں۔

**فی لائف سائیکل ایونٹ فی ورژن زیادہ سے زیادہ ایک POST**، جس میں شامل ہے:

| فیلڈ | مثال | کیوں |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` پر محفوظ رینڈم UUID | ڈیڈوپ؛ گمنام جب تک آپ واضح طور پر Cloud sync کو منسلک نہ کریں (اس کے بعد تصدیق شدہ ڈیمن ہارٹ بیٹ اسے لے جاتا ہے، اس انسٹال کو آپ کے اکاؤنٹ سے جوڑتے ہوئے) |
| `event` | `install` / `update` / `onboarded` | نیا انسٹال بمقابلہ موجودہ کا اپ گریڈ |
| `version` | `0.12.167` | استعمال میں موجود ورژنز |
| `os` / `os_version` | `Darwin` / `25.3.0` | پلیٹ فارم سپورٹ کی ترجیحات |
| `python` | `3.11.15` | Python ورژن سپورٹ میٹرکس |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ہمیں آگے کن ایجنٹس کے ساتھ انضمام کرنا چاہیے |
| `is_ci` / `ci_provider` | `true` / `github_actions` | انسانی انسٹالز کو CI شور سے الگ کرنا |

**ہم کیا نہیں بھیجتے**: IP (کلاؤڈ درخواست سے سرور سائیڈ پر ملک کا کوڈ اخذ
کرتا ہے، پھر IP کو ضائع کر دیتا ہے)، ہوسٹ نیم، یوزر نیم، ورک اسپیس پاتھ،
فائل کا مواد، آپ کی api_key، آپ کا ای میل، کوئی بھی PII یا ورک اسپیس سے
متعلق چیز۔ وائر پے لوڈ [`clawmetry/telemetry.py`](clawmetry/telemetry.py)
میں قابل آڈٹ ہے۔

**آپٹ آؤٹ** (ان میں سے کوئی بھی اسے مستقل طور پر غیر فعال کر دیتا ہے):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

یہاں نیٹ ورک کی ناکامی کبھی بھی `clawmetry` کو چلنے سے نہیں روکتی — پنگ
ڈیمن تھریڈ پر 3 سیکنڈ ٹائم آؤٹ کے ساتھ فائر اینڈ فارگٹ ہے۔

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
  <sub><a href="https://github.com/vivekchand">@vivekchand</a> کی جانب سے بنایا گیا · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ایکو سسٹم کا حصہ</sub>
</p>
