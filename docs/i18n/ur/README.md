<!-- i18n-src:8f42d460a973 -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **14 AI ایجنٹ رن ٹائمز** کے لیے ریئل ٹائم آبزروبیلٹی: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور 10 مزید۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ہی ڈیش بورڈ۔

> 🌐 **اسے ان زبانوں میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ کوئی کنفیگریشن نہیں۔ سب کچھ خودکار طریقے سے پتا چل جاتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے اور بس، کام ہو گیا۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 14 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

ClawMetry کا آغاز OpenClaw کے لیے آبزروبیلٹی کے طور پر ہوا تھا، اور اب یہ ایک ہی ڈیش بورڈ میں آپ کے **پورے ایجنٹ فلیٹ** کی پیمائش کرتا ہے، اور آپ کی مشین پر ہر رن ٹائم کو خودکار طور پر شناخت کرتا ہے:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

OpenClaw اور NemoClaw اوپن سورس ایپ میں مفت ہیں؛ باقی رن ٹائمز ClawMetry Cloud یا سیلف ہوسٹڈ Pro لائسنس کے ساتھ فعال ہوتے ہیں۔ ہیڈر سے رن ٹائم تبدیل کریں اور ہر ٹیب — لاگت، ٹوکنز، ٹولز، ٹریسز — اسی رن ٹائم کے دائرے میں دوبارہ ترتیب پا جاتا ہے۔ درست مفت/ادائیگی والی تقسیم، ٹئیر میٹرکس، `/api/entitlement` کی ساخت، اور `clawmetry license` CLI کے لیے **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** ملاحظہ کریں۔

## آپ کو کیا ملتا ہے

- **Flow** — لائیو اینیمیٹڈ ڈایاگرام جو چینلز، برین، ٹولز اور واپس تک پیغامات کے بہاؤ کو دکھاتا ہے
- **Overview** — ہیلتھ چیکس، سرگرمی کا ہیٹ میپ، سیشن گنتی، ماڈل کی معلومات
- **Usage** — روزانہ/ہفتہ وار/ماہانہ تفصیل کے ساتھ ٹوکن اور لاگت کی ٹریکنگ
- **Sessions** — ماڈل، ٹوکنز، آخری سرگرمی کے ساتھ فعال ایجنٹ سیشنز
- **Crons** — اسٹیٹس، اگلے رن، دورانیے کے ساتھ شیڈول شدہ جابز
- **Logs** — رنگ کوڈڈ ریئل ٹائم لاگ سٹریمنگ
- **Memory** — SOUL.md، MEMORY.md، AGENTS.md، روزانہ نوٹس براؤز کریں
- **Transcripts** — سیشن ہسٹری پڑھنے کے لیے چیٹ بلبلہ UI
- **Alerts** — بجٹ کیپس، ایرر ریٹ ٹرگرز، ایجنٹ آف لائن کی شناخت؛ Slack، Discord، PagerDuty، Telegram، ای میل کو روٹ کرتا ہے
- **Approvals** — تباہ کن ڈیلیٹس، فورس پُشز، DB میوٹیشنز، sudo، پیکج انسٹالیشنز، نیٹ ورک کالز کو ایک کلک منظوری کے پیچھے روکیں

## اسکرین شاٹس

### 🧠 Brain — لائیو ایجنٹ ایونٹ سٹریم
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — ٹوکن استعمال اور سیشن خلاصہ
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — ریئل ٹائم ٹول کال فیڈ
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — ماڈل اور سیشن کے لحاظ سے لاگت کی تفصیل
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — ورک اسپیس فائل براؤزر
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — پوزیشن اور آڈٹ لاگ
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — بجٹ کیپس، ایرر ریٹ ٹرگرز، Slack / Discord / PagerDuty / ای میل کو ویب ہکس
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — خطرناک ٹول کالز کو دستی منظوری کے پیچھے روکیں؛ پالیسی پر مبنی حفاظتی قواعد
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## انسٹالیشن

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
سرور v2 فعال کر کے شروع کیا جائے تو `/v2` پر سرو کی جاتی ہے۔

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
`http://localhost:8900` پر پراکسی کرتا ہے، تاکہ React ایپ اضافی
CORS سیٹ اپ کے بغیر لوکل Flask سرور سے بات کر سکے۔

Python پیکج کے ساتھ شپ ہونے والا بنڈل بنانے کے لیے:

```bash
cd frontend
npm run build
```

پروڈکشن بنڈل `clawmetry/static/v2/dist/` میں لکھا جاتا ہے۔

## رن ٹائم / ایجنٹ کمپیٹیبلٹی

ClawMetry صرف OpenClaw ہی نہیں بلکہ کئی AI ایجنٹ رن ٹائمز کا مشاہدہ کرتا ہے۔ ہر غیر OpenClaw رن ٹائم ایک مخصوص ریڈر ایڈاپٹر فراہم کرتا ہے جو اس کے نیٹو سیشن فارمیٹ کو ClawMetry کی متحد شکلوں میں تبدیل کرتا ہے؛ ڈیمن انہیں رن ٹائم کے ٹیگ کے ساتھ اسی DuckDB اسٹور + کلاؤڈ اسنیپ شاٹ میں شامل کرتا ہے، اور Session replay ٹیب ایک سے زیادہ رن ٹائمز موجود ہونے پر **رن ٹائم سوئچر** دکھاتا ہے۔ مکمل میٹرکس + رن ٹائمز شامل کرنے کے رہنما کے لیے [`docs/compatibility.md`](docs/compatibility.md)، اور OpenClaw فیملی کے تعارف کے لیے [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) دیکھیں۔

| رن ٹائم / ایجنٹ | حیثیت | نوٹس |
|---|---|---|
| **OpenClaw** | نیٹو | حوالہ رن ٹائم، خودکار شناخت |
| **PicoClaw** | بیٹا ایڈاپٹر | فلیٹ `providers.Message` JSONL (`~/.picoclaw/workspace/sessions`)۔ ٹرانسکرپٹس، ماڈل، ٹول کالز۔ |
| **NanoClaw** | بیٹا ایڈاپٹر | فی سیشن SQLite (`data/v2-sessions`)۔ ٹرانسکرپٹس + پیغامات کی گنتی۔ |
| **Hermes** | بیٹا ایڈاپٹر | SQLite `~/.hermes/state.db`۔ ٹرانسکرپٹس، ماڈل، ٹوکنز/لاگت۔ |
| **Claude Code** | بیٹا ایڈاپٹر | JSONL `~/.claude/projects/.../<id>.jsonl`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز + سوچ، ٹوکن استعمال۔ |
| **Codex** | بیٹا ایڈاپٹر | Rollout JSONL `~/.codex/sessions/...`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Cursor** | بیٹا ایڈاپٹر | SQLite `state.vscdb`۔ چیٹ/کمپوزر ٹرانسکرپٹس، ماڈل۔ |
| **Aider** | بیٹا ایڈاپٹر | ہر پراجیکٹ کے لیے `.aider.chat.history.md`۔ ٹرانسکرپٹس، ماڈل، ٹوکن گنتی۔ |
| **Goose** | بیٹا ایڈاپٹر | SQLite `~/.local/share/goose`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، کل ٹوکنز۔ |
| **opencode** | بیٹا ایڈاپٹر | SQLite `~/.local/share/opencode`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Qwen Code** | بیٹا ایڈاپٹر | JSONL `~/.qwen/projects/.../chats`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکن استعمال۔ |
| **Pi** | بیٹا ایڈاپٹر | JSONL `~/.pi/agent/sessions`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |
| **Deep Agents** | بیٹا ایڈاپٹر | SQLite `~/.deepagents/.state/sessions.db`۔ ٹرانسکرپٹس، ماڈل، ٹول کالز، ٹوکنز + لاگت۔ |

"بیٹا ایڈاپٹر" کا مطلب ہے کہ ClawMetry اس رن ٹائم کے حقیقی آن ڈسک فارمیٹ کے لیے ایک ریڈر فراہم کرتا ہے، جو ہر ایک حقیقی مشین پر حقیقی انسٹال کے خلاف بنایا اور تصدیق شدہ ہے (دیکھیں `tests/fixtures/runtimes/<rt>/`)۔ ایڈاپٹرز صرف پڑھنے کے لیے ہیں؛ ہر ایک اس بارے میں دیانتدار ہے کہ اس کا رن ٹائم اصل میں کیا اسٹور کرتا ہے (مثلاً PicoClaw/NanoClaw/Cursor ٹوکن لاگت کو ڈسک پر نہیں لکھتے)۔ جب ایک نوڈ پر کئی رن ٹائمز چل رہے ہوں، تو رن ٹائم سوئچر واضح گہرائی سے جائزے کے لیے sessions ویو کو ایک تک محدود کر دیتا ہے۔

## کسی بھی SDK ایجنٹ کو ٹریک کریں — آؤٹ لوپ لاگت کی تخصیص

اوپر دیے گئے تمام رن ٹائمز سیشنز کو ڈسک پر لکھتے ہیں۔ آپ کا اپنا **پروڈکشن ایجنٹ** — وہ جو آپ نے OpenAI Agents SDK، LangChain، Vercel AI SDK، LlamaIndex، E2B، یا سادہ `httpx` لوپ پر بنایا ہے — ایسا نہیں کرتا۔ ClawMetry کا زیرو کنفیگ انٹرسیپٹر پھر بھی `httpx`/`requests` کو مانکی پیچ کر کے اس کی LLM کالز (لاگت، ٹوکنز، لیٹنسی، ایررز) کیپچر کرتا ہے:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (یا `CLAWMETRY_SOURCE=support-agent` ماحولیاتی متغیر) ہر کال کو ایک **نامزد ماخذ** کے ساتھ ٹیگ کرتا ہے، تاکہ آپ کا چلایا گیا ہر پروڈکٹ ڈیش بورڈ کے Overview پر موجود **🔌 آؤٹ لوپ ماخذ** کارڈ میں اپنی الگ، لاگت کے لحاظ سے قابل تخصیص لائن کے طور پر ظاہر ہو — فی ایجنٹ کالز، پرووائیڈرز، لیٹنسی، ایرر ریٹ۔ کوئی ماخذ سیٹ نہیں کیا؟ کالز پھر بھی ٹریک ہوتی ہیں؛ صرف کارڈ چھپا رہتا ہے۔

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

یہ وہی ڈیٹا لیئر ہے جسے رن ٹائم ایڈاپٹرز فیڈ کرتے ہیں (DuckDB → کلاؤڈ اسنیپ شاٹ)، اس لیے آؤٹ لوپ ماخذ باقی سب چیزوں کی طرح، E2E انکرپٹڈ کلاؤڈ ڈیش بورڈ کے ساتھ سنک ہوتے ہیں۔

## OpenTelemetry — وینڈر نیوٹرل، اپنے ٹریسز کہیں بھی بھیجیں

ClawMetry دونوں سمتوں میں **OpenTelemetry** بولتا ہے، **GenAI سیمینٹک کنونشنز** کا استعمال کرتے ہوئے، تاکہ آپ کے ایجنٹ ٹریسز کبھی بھی صرف ایک ٹول تک محدود نہ ہوں۔

ہر سیشن — LLM کالز، ٹولز، سب ایجنٹس، ٹوکنز، لاگت — کو **ایکسپورٹ** کریں OTLP/HTTP GenAI اسپینز کے طور پر کسی بھی کلیکٹر کو (Datadog، Grafana، Honeycomb، یا آپ کا اپنا OTel Collector):

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

**انجیسٹ** — بلٹ ان OTLP ریسیور `/v1/traces` اور `/v1/metrics` پر کسی بھی دوسری چیز سے ٹریسز اور میٹرکس قبول کرتا ہے (پروٹو بف انجیسٹ کے لیے `pip install clawmetry[otel]`)۔

آپ کو زیرو کنفیگ، لوکل فرسٹ ClawMetry ڈیش بورڈ **اور** آپ کا ڈیٹا آپ کی ٹیم کے پہلے سے چلائے جانے والے کسی بھی بیک اینڈ میں ملتا ہے — نہ کوئی لاک اِن، نہ کوئی دوسرا ایجنٹ انسٹال کرنے کی ضرورت۔

## کنفیگریشن

زیادہ تر لوگوں کو کسی کنفیگریشن کی ضرورت نہیں۔ ClawMetry آپ کے ورک اسپیس، لاگز، سیشنز، اور کرونز کو خودکار طریقے سے شناخت کرتا ہے۔

اگر آپ کو کسٹمائز کرنے کی ضرورت ہو:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

تمام آپشنز: `clawmetry --help`

## معاون چینلز

ClawMetry آپ کے کنفیگر کردہ ہر OpenClaw چینل کے لیے لائیو سرگرمی دکھاتا ہے۔ صرف وہ چینلز جو آپ کے `openclaw.json` میں واقعی سیٹ اپ ہیں Flow ڈایاگرام میں ظاہر ہوتے ہیں — غیر کنفیگر شدہ چینلز خودکار طور پر چھپا دیے جاتے ہیں۔

Flow میں کسی بھی چینل نوڈ پر کلک کریں تاکہ آنے والے/جانے والے پیغامات کی گنتی کے ساتھ لائیو چیٹ بلبلہ ویو دیکھ سکیں۔

| چینل | حیثیت | لائیو پاپ اپ | نوٹس |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ مکمل | ✅ | پیغامات، اعداد و شمار، 10 سیکنڈ ریفریش |
| 💬 **iMessage** | ✅ مکمل | ✅ | `~/Library/Messages/chat.db` براہ راست پڑھتا ہے |
| 💚 **WhatsApp** | ✅ مکمل | ✅ | WhatsApp Web (Baileys) کے ذریعے |
| 🔵 **Signal** | ✅ مکمل | ✅ | signal-cli کے ذریعے |
| 🟣 **Discord** | ✅ مکمل | ✅ | گِلڈ + چینل شناخت |
| 🟪 **Slack** | ✅ مکمل | ✅ | ورک اسپیس + چینل شناخت |
| 🌐 **Webchat** | ✅ مکمل | ✅ | بلٹ اِن ویب UI سیشنز |
| 📡 **IRC** | ✅ مکمل | ✅ | ٹرمینل طرز بلبلہ UI |
| 🍏 **BlueBubbles** | ✅ مکمل | ✅ | BlueBubbles REST API کے ذریعے iMessage |
| 🔵 **Google Chat** | ✅ مکمل | ✅ | Chat API ویب ہکس کے ذریعے |
| 🟣 **MS Teams** | ✅ مکمل | ✅ | Teams بوٹ پلگ ان کے ذریعے |
| 🔷 **Mattermost** | ✅ مکمل | ✅ | سیلف ہوسٹڈ ٹیم چیٹ |
| 🟩 **Matrix** | ✅ مکمل | ✅ | ڈی سینٹرلائزڈ، E2EE سپورٹ |
| 🟢 **LINE** | ✅ مکمل | ✅ | LINE میسجنگ API |
| ⚡ **Nostr** | ✅ مکمل | ✅ | ڈی سینٹرلائزڈ NIP-04 DMs |
| 🟣 **Twitch** | ✅ مکمل | ✅ | IRC کنکشن کے ذریعے چیٹ |
| 🔷 **Feishu/Lark** | ✅ مکمل | ✅ | ویب ساکٹ ایونٹ سبسکرپشن |
| 🔵 **Zalo** | ✅ مکمل | ✅ | Zalo بوٹ API |

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

> **نوٹ:** Docker میں چلاتے وقت، اپنے ایجنٹ کی ڈیٹا + لاگ ڈائریکٹریز ماؤنٹ کریں (مثلاً `~/.openclaw`، `~/.claude`، `~/.codex`) تاکہ ClawMetry آپ کے سیٹ اپ کو خودکار طور پر شناخت کر سکے۔

## ضروریات

- Python 3.8+
- Flask (pip کے ذریعے خودکار طور پر انسٹال ہوتا ہے)
- ایک ہی مشین پر AI ایجنٹ رن ٹائم: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، یا Deep Agents (یا Docker کے لیے ماؤنٹ شدہ والیومز)
- Linux یا macOS

## NemoClaw / OpenShell سپورٹ

ClawMetry خودکار طور پر [NemoClaw](https://github.com/NVIDIA/NemoClaw) کی شناخت کرتا ہے — NVIDIA کا انٹرپرائز سیکورٹی ریپر جو OpenClaw کے لیے ہے اور ایجنٹس کو سینڈ باکسڈ OpenShell کنٹینرز کے اندر چلاتا ہے۔

زیادہ تر صورتوں میں کسی اضافی کنفیگریشن کی ضرورت نہیں۔ سنک ڈیمن خودکار طور پر سیشن فائلیں دریافت کرتا ہے چاہے وہ ہوسٹ پر `~/.openclaw/` میں ہوں یا OpenShell کنٹینر کے اندر۔

### یہ کیسے کام کرتا ہے

ClawMetry دو طریقوں سے NemoClaw کی شناخت کرتا ہے:

1. **بائنری شناخت** — `nemoclaw` CLI کی موجودگی چیک کرتا ہے اور سینڈ باکس معلومات حاصل کرنے کے لیے `nemoclaw status` چلاتا ہے
2. **کنٹینر شناخت** — چلنے والے Docker کنٹینرز کو `openshell`، `nemoclaw`، یا `ghcr.io/nvidia/` امیجز کے لیے اسکین کرتا ہے، پھر والیوم ماؤنٹس یا `docker cp` کے ذریعے سیشنز پڑھتا ہے

NemoClaw کنٹینرز سے سنک شدہ سیشن فائلوں کو کلاؤڈ ڈیش بورڈ میں `runtime=nemoclaw` اور `container_id` میٹا ڈیٹا کے ساتھ ٹیگ کیا جاتا ہے، تاکہ آپ ایک نظر میں انہیں معیاری OpenClaw سیشنز سے الگ کر سکیں۔

### تجویز کردہ سیٹ اپ: HOST پر سنک ڈیمن

بہترین تجربے کے لیے، ClawMetry کا سنک ڈیمن سینڈ باکس کے اندر نہیں بلکہ **ہوسٹ مشین** پر چلائیں۔ اس سے NemoClaw کی نیٹ ورک پالیسی کی پابندیوں سے بچا جا سکتا ہے۔

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سنک ڈیمن خودکار طور پر کسی بھی چلنے والے OpenShell کنٹینرز کے اندر موجود سیشنز تلاش کر لے گا۔

### اختیاری: واضح سینڈ باکس نام

اگر خودکار شناخت کام نہ کرے، تو ClawMetry کو صحیح سینڈ باکس کی طرف اشارہ کریں:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### سینڈ باکس کے اندر چلانا (ایڈوانسڈ)

اگر آپ کو سنک ڈیمن OpenShell سینڈ باکس کے **اندر** چلانا ضروری ہو، تو اپنی NemoClaw نیٹ ورک پالیسی میں یہ ایگریس رول شامل کریں تاکہ یہ ClawMetry انجیسٹ API تک رسائی حاصل کر سکے:

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
| `ingest.clawmetry.com` | 443 | HTTPS | جی ہاں (سنک ڈیمن → کلاؤڈ) |
| `localhost:8900` | 8900 | HTTP | جی ہاں (لوکل ڈیش بورڈ UI) |
| Docker ساکٹ (`/var/run/docker.sock`) | — | Unix ساکٹ | کنٹینر سیشن دریافت کے لیے |

سنک ڈیمن صرف `ingest.clawmetry.com` کو آؤٹ باؤنڈ HTTPS کالز کرتا ہے۔ کسی اِن باؤنڈ پورٹ کی ضرورت نہیں۔

---

## کلاؤڈ ڈیپلائمنٹ

SSH ٹنلز، ریورس پراکسی، اور Docker کے لیے **[Cloud Testing Guide](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** دیکھیں۔

## ٹیسٹنگ

اس پراجیکٹ کی جانچ BrowserStack کے ساتھ کی جاتی ہے۔

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## ٹیلی میٹری

ClawMetry ایک ہی گمنام "پہلی بار چلنے" کا پنگ
`https://app.clawmetry.com/api/install` پر اس وقت بھیجتا ہے جب آپ پہلی بار
نئی مشین پر `clawmetry` CLI چلاتے ہیں۔ ہم اسے انسٹالز شمار کرنے کے لیے استعمال کرتے ہیں (ایک
OSS پراجیکٹ کے لیے ہمارے پاس واحد مارکیٹنگ میٹرک ہے) اور یہ جاننے کے لیے کہ ہمارے
صارفین نے کون سے ایجنٹ فریم ورکس انسٹال کیے ہوئے ہیں۔

**فی انسٹال بالکل ایک POST**، جس میں شامل ہے:

| فیلڈ | مثال | وجہ |
|---|---|---|
| `install_id` | `~/.clawmetry/install_id` پر محفوظ رینڈم UUID | ڈی ڈپلیکیشن؛ آپ کے ای میل یا api_key سے منسلک نہیں |
| `version` | `0.12.167` | یہ جاننا کہ کون سے ورژنز استعمال میں ہیں |
| `os` / `os_version` | `Darwin` / `25.3.0` | پلیٹ فارم سپورٹ کی ترجیحات |
| `python` | `3.11.15` | Python ورژن سپورٹ میٹرکس |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | یہ کہ ہمیں آگے کن ایجنٹس کو انٹیگریٹ کرنا چاہیے |
| `is_ci` / `ci_provider` | `true` / `github_actions` | انسانی انسٹالز کو CI شور سے الگ کرنا |

**ہم کیا نہیں بھیجتے**: IP (کلاؤڈ سرور کی جانب سے درخواست سے ملک کا کوڈ اخذ کرتا ہے،
پھر IP کو ضائع کر دیتا ہے)، ہوسٹ نیم، صارف نام، ورک اسپیس
پاتھ، فائل کا مواد، آپ کا api_key، آپ کا ای میل، کوئی بھی PII یا
ورک اسپیس سے متعلق چیز۔ وائر پے لوڈ
[`clawmetry/telemetry.py`](clawmetry/telemetry.py) میں قابل جانچ ہے۔

**اختیاری اخراج** (ان میں سے کوئی بھی ایک اسے مستقل طور پر غیر فعال کر دیتا ہے):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

یہاں نیٹ ورک کی ناکامی کبھی بھی `clawmetry` کے چلنے میں رکاوٹ نہیں بنتی — یہ
پنگ ڈیمن تھریڈ پر 3 سیکنڈ ٹائم آؤٹ کے ساتھ فائر اینڈ فرگیٹ ہے۔

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
  <sub>تیار کردہ <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ایکو سسٹم کا حصہ</sub>
</p>
