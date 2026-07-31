<!-- i18n-src:02b789586c7d -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**شاهد وكيلك وهو يفكر.** مراقبة فورية لـ **14 نظام تشغيل لوكلاء الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و10 أنظمة أخرى. لوحة تحكم واحدة لأسطول وكلائك بأكمله.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بلا إعدادات. يكتشف كل شيء تلقائياً.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900** وانتهى الأمر.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## يعمل مع 14 نظام تشغيل للوكلاء

بدأت ClawMetry كأداة مراقبة لـ OpenClaw، والآن تقيس **أسطول وكلائك بأكمله** في لوحة تحكم واحدة، وتكتشف كل نظام تشغيل تلقائياً على جهازك:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw وNemoClaw مجانيان في التطبيق مفتوح المصدر؛ بينما تُفعَّل أنظمة التشغيل الأخرى عبر ClawMetry Cloud أو ترخيص Pro مستضاف ذاتياً. بدّل أنظمة التشغيل من الرأسية، وكل تبويب - التكلفة والرموز والأدوات والتتبعات - يعيد التركيز على نظام التشغيل ذاك. راجع **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** للاطلاع على التقسيم الدقيق بين المجاني والمدفوع، ومصفوفة المستويات، وشكل `/api/entitlement`، وأداة سطر الأوامر `clawmetry license`.

## ما الذي تحصل عليه

- **Flow** - رسم متحرك مباشر يُظهر الرسائل وهي تتدفق عبر القنوات والعقل والأدوات ثم تعود
- **Overview** - فحوصات الصحة، خريطة النشاط الحرارية، عدد الجلسات، معلومات النموذج
- **Usage** - تتبع الرموز والتكلفة مع تفصيل يومي/أسبوعي/شهري
- **Sessions** - جلسات الوكيل النشطة مع النموذج والرموز وآخر نشاط
- **Crons** - المهام المجدولة مع الحالة، التشغيل التالي، المدة
- **Logs** - بث سجلات مباشر مُلوَّن
- **Memory** - تصفح SOUL.md وMEMORY.md وAGENTS.md والملاحظات اليومية
- **Transcripts** - واجهة فقاعات محادثة لقراءة سجلات الجلسات
- **Alerts** - حدود الميزانية، محفزات معدل الأخطاء، اكتشاف انقطاع الوكيل؛ يوجّه إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **Approvals** - حجب عمليات الحذف المدمرة، والدفعات القسرية (force pushes)، وتعديلات قواعد البيانات، وsudo، وتثبيت الحزم، والاتصالات الشبكية خلف موافقة بضغطة واحدة

## لقطات الشاشة

### 🧠 Brain - بث أحداث الوكيل المباشر
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview - استخدام الرموز وملخص الجلسات
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow - تغذية استدعاءات الأدوات الفورية
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens - تفصيل التكلفة حسب النموذج والجلسة
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory - متصفح ملفات مساحة العمل
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security - الوضع الأمني وسجل التدقيق
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts - حدود الميزانية، محفزات معدل الأخطاء، خطافات الويب إلى Slack / Discord / PagerDuty / البريد الإلكتروني
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals - حجب استدعاءات الأدوات الخطرة خلف موافقة يدوية؛ قواعد حماية مدعومة بسياسات
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**الحجب قبل التنفيذ لـ Claude Code** - أمر واحد يثبّت خطاف
PreToolUse يوقف استدعاءات الأدوات المطابقة *قبل* تشغيلها وينتظر
قرارك (بلمسة واحدة من هاتفك عند تفعيل
[إشعارات الدفع السحابية](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

الرفض يحجب استدعاء تلك الأداة الواحدة فقط - يحتفظ الوكيل بجلسته ويمكنه
تجربة نهج آخر. الموافقة من هاتفك تتخطى موجّه الإذن الخاص بـ Claude Code
(فأنت أجبت بالفعل). استدعاءات الأدوات غير المطابقة تكلّف نحو 40 مللي ثانية
وتمر عبر تدفق الإذن العادي في Claude Code. كما تحصل على إشعار دفع على هاتفك
عندما ينتظرك Claude Code نفسه (إشعارات `permission_prompt` /
`idle_prompt`).

## التثبيت

**سطر واحد (موصى به):**
```bash
curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash
```

**pip:**
```bash
pip install clawmetry
clawmetry
```

**من المصدر:**
```bash
git clone https://github.com/vivekchand/clawmetry.git
cd clawmetry && pip install flask && python3 dashboard.py
```

## تطوير الواجهة الأمامية v2

تطبيق React الخاص بالإصدار v2 موجود في `frontend/` ويُقدَّم على
`/v2` عند تشغيل خادم Flask مع تفعيل v2.

استخدم طرفيتين (terminals) أثناء التطوير:

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

افتح `http://localhost:5173/v2/`. يقوم Vite بتمرير طلبات `/api` إلى
`http://localhost:8900`، حتى يتمكن تطبيق React من التواصل مع خادم Flask
المحلي دون إعدادات CORS إضافية.

لبناء الحزمة التي تُشحن مع حزمة Python:

```bash
cd frontend
npm run build
```

تُكتب الحزمة الإنتاجية إلى `clawmetry/static/v2/dist/`.

## توافق أنظمة التشغيل / الوكلاء

تراقب ClawMetry العديد من أنظمة تشغيل وكلاء الذكاء الاصطناعي، وليس فقط OpenClaw. كل نظام تشغيل غير OpenClaw يأتي مع محوّل قراءة مخصص يترجم صيغة جلساته الأصلية إلى أشكال ClawMetry الموحدة؛ يستوعبها الشيطان (daemon) في مخزن DuckDB نفسه + اللقطة السحابية، موسومة بنظام التشغيل، ويعرض تبويب إعادة تشغيل الجلسة **مبدّل أنظمة تشغيل** عند وجود أكثر من نظام واحد. راجع [`docs/compatibility.md`](docs/compatibility.md) للاطلاع على المصفوفة الكاملة + دليل لإضافة أنظمة تشغيل، و[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) لمقدمة عائلة OpenClaw.

| نظام التشغيل / الوكيل | الحالة | ملاحظات |
|---|---|---|
| **OpenClaw** | أصلي | نظام التشغيل المرجعي، يُكتشف تلقائياً |
| **PicoClaw** | محوّل تجريبي | JSONL مسطّح لـ `providers.Message` (`~/.picoclaw/workspace/sessions`). سجلات المحادثة، النموذج، استدعاءات الأدوات. |
| **NanoClaw** | محوّل تجريبي | SQLite لكل جلسة (`data/v2-sessions`). سجلات المحادثة + عدد الرسائل. |
| **Hermes** | محوّل تجريبي | SQLite في `~/.hermes/state.db`. سجلات المحادثة، النموذج، الرموز/التكلفة. |
| **Claude Code** | محوّل تجريبي | JSONL في `~/.claude/projects/.../<id>.jsonl`. سجلات المحادثة، النموذج، استدعاءات الأدوات + التفكير، استخدام الرموز. |
| **Codex** | محوّل تجريبي | Rollout JSONL في `~/.codex/sessions/...`. سجلات المحادثة، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Cursor** | محوّل تجريبي | SQLite لـ `state.vscdb`. سجلات محادثة/composer، النموذج. |
| **Aider** | محوّل تجريبي | `.aider.chat.history.md` لكل مشروع. سجلات المحادثة، النموذج، عدد الرموز. |
| **Goose** | محوّل تجريبي | SQLite في `~/.local/share/goose`. سجلات المحادثة، النموذج، استدعاءات الأدوات، إجمالي الرموز. |
| **opencode** | محوّل تجريبي | SQLite في `~/.local/share/opencode`. سجلات المحادثة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Qwen Code** | محوّل تجريبي | JSONL في `~/.qwen/projects/.../chats`. سجلات المحادثة، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Pi** | محوّل تجريبي | JSONL في `~/.pi/agent/sessions`. سجلات المحادثة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Deep Agents** | محوّل تجريبي | SQLite في `~/.deepagents/.state/sessions.db`. سجلات المحادثة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **n8n** | محوّل تجريبي | SQLite في `~/.n8n/database.sqlite`. تنفيذات سير العمل، تشغيلات العقد، مطالبات AI Agent، النموذج + الرموز حيثما يسجلها n8n. |
| **Antigravity** | محوّل تجريبي | Brain JSONL تحت `~/.gemini/<flavor>/brain/`. المحادثات، خطوات الأدوات، التفكير، تقسيم رموز Gemini لكل توليد + التكلفة، استهلاك التوليد في الخلفية. |

"محوّل تجريبي" تعني أن ClawMetry تقدّم قارئاً لصيغة نظام التشغيل الفعلية على القرص، وكل واحد منها بُني + جرى التحقق منه مقابل تثبيت حقيقي على جهاز حقيقي (راجع `tests/fixtures/runtimes/<rt>/`). المحوّلات للقراءة فقط؛ وكل واحد منها صادق بشأن ما يخزّنه نظام التشغيل فعلياً (مثلاً PicoClaw/NanoClaw/Cursor لا تكتب تكلفة الرموز إلى القرص). عند تشغيل عدة أنظمة تشغيل على عقدة واحدة، يعيد مبدّل أنظمة التشغيل تركيز عرض الجلسات على نظام واحد للتعمق بشكل واضح.

## تتبع أي وكيل SDK - إسناد التكلفة خارج الحلقة

أنظمة التشغيل أعلاه جميعها تكتب الجلسات إلى القرص. لكن **وكيل الإنتاج** الخاص بك - ذاك الذي بنيته على OpenAI Agents SDK أو LangChain أو Vercel AI SDK أو LlamaIndex أو E2B أو مجرد حلقة `httpx` عادية - لا يفعل ذلك. لا يزال محوِّل ClawMetry بلا إعدادات يلتقط استدعاءات LLM الخاصة به (التكلفة، الرموز، زمن الاستجابة، الأخطاء) عبر تصحيح `httpx`/`requests` أثناء التشغيل (monkey-patching):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (أو متغير البيئة `CLAWMETRY_SOURCE=support-agent`) يسم كل استدعاء بـ**مصدر مُسمّى**، لذا يظهر كل منتج تشغّله كسطر مستقل قابل لإسناد التكلفة له في بطاقة **🔌 المصادر خارج الحلقة** في تبويب Overview بلوحة التحكم - الاستدعاءات، المزودون، زمن الاستجابة، معدل الأخطاء لكل وكيل. لم تحدد مصدراً؟ لا تزال الاستدعاءات مُتتبَّعة؛ فقط تبقى البطاقة مخفية.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

هذه طبقة البيانات نفسها التي تغذيها محوّلات أنظمة التشغيل (DuckDB ← اللقطة السحابية)، لذا تتزامن المصادر خارج الحلقة مع لوحة التحكم السحابية مثل أي شيء آخر، مشفّرة تشفيراً تاماً بين الطرفين (E2E).

## OpenTelemetry - محايد للمزوّد، أرسل تتبعاتك إلى أي مكان

تتحدث ClawMetry **OpenTelemetry** في كلا الاتجاهين، باستخدام **اتفاقيات GenAI الدلالية**، لذا لن تُقفل تتبعات وكيلك على أداة واحدة أبداً.

**التصدير**: كل جلسة - استدعاءات LLM، الأدوات، الوكلاء الفرعيون، الرموز، التكلفة - كتتبعات OTLP/HTTP GenAI إلى أي مجمّع (Datadog أو Grafana أو Honeycomb أو مجمّع OTel الخاص بك):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

رؤوس المصادقة وفاصل الاستطلاع اختياريان كمتغيرات بيئة:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**الاستيعاب** - مستقبِل OTLP المدمج يقبل التتبعات والمقاييس من أي مكان آخر عند `/v1/traces` و`/v1/metrics` (`pip install clawmetry[otel]` لاستيعاب protobuf).

تحصل على لوحة تحكم ClawMetry بلا إعدادات، محلية الأولوية، **وعلى** بياناتك في أي نظام خلفي يستخدمه فريقك بالفعل - بلا ارتباط إجباري، وبلا وكيل ثانٍ للتثبيت.

## الإعدادات

معظم الناس لا يحتاجون أي إعدادات. تكتشف ClawMetry تلقائياً مساحة عملك وسجلاتك وجلساتك ومهامك المجدولة.

إن احتجت للتخصيص:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

جميع الخيارات: `clawmetry --help`

## القنوات المدعومة

تعرض ClawMetry النشاط المباشر لكل قناة OpenClaw قمت بإعدادها. فقط القنوات المُعدَّة فعلياً في ملف `openclaw.json` الخاص بك تظهر في مخطط Flow - القنوات غير المُعدَّة تُخفى تلقائياً.

انقر أي عقدة قناة في Flow لرؤية عرض فقاعات محادثة مباشر مع عدادات الرسائل الواردة/الصادرة.

| القناة | الحالة | نافذة منبثقة مباشرة | ملاحظات |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ كاملة | ✅ | الرسائل، الإحصاءات، تحديث كل 10 ثوانٍ |
| 💬 **iMessage** | ✅ كاملة | ✅ | تقرأ `~/Library/Messages/chat.db` مباشرة |
| 💚 **WhatsApp** | ✅ كاملة | ✅ | عبر WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ كاملة | ✅ | عبر signal-cli |
| 🟣 **Discord** | ✅ كاملة | ✅ | اكتشاف السيرفر (guild) + القناة |
| 🟪 **Slack** | ✅ كاملة | ✅ | اكتشاف مساحة العمل + القناة |
| 🌐 **Webchat** | ✅ كاملة | ✅ | جلسات واجهة الويب المدمجة |
| 📡 **IRC** | ✅ كاملة | ✅ | واجهة فقاعات بأسلوب الطرفية |
| 🍏 **BlueBubbles** | ✅ كاملة | ✅ | iMessage عبر واجهة BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ كاملة | ✅ | عبر خطافات ويب Chat API |
| 🟣 **MS Teams** | ✅ كاملة | ✅ | عبر إضافة بوت Teams |
| 🔷 **Mattermost** | ✅ كاملة | ✅ | دردشة فريق مستضافة ذاتياً |
| 🟩 **Matrix** | ✅ كاملة | ✅ | لامركزية، دعم E2EE |
| 🟢 **LINE** | ✅ كاملة | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ كاملة | ✅ | رسائل خاصة لامركزية NIP-04 |
| 🟣 **Twitch** | ✅ كاملة | ✅ | الدردشة عبر اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ كاملة | ✅ | اشتراك أحداث WebSocket |
| 🔵 **Zalo** | ✅ كاملة | ✅ | Zalo Bot API |

> **الاكتشاف التلقائي:** تقرأ ClawMetry ملف `~/.openclaw/openclaw.json` الخاص بك وتعرض فقط القنوات التي أعددتها فعلياً. لا حاجة لإعداد يدوي.

## نشر Docker

تريد تشغيل ClawMetry داخل حاوية؟ لا مشكلة! 🐳

**بداية سريعة مع Docker:**

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

**مثال Docker Compose:**

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

> **ملاحظة:** عند التشغيل داخل Docker، اربط أدلة بيانات وسجلات وكيلك (مثل `~/.openclaw` و`~/.claude` و`~/.codex`) حتى تتمكن ClawMetry من اكتشاف إعدادك تلقائياً.

## المتطلبات

- Python 3.8+
- Flask (يُثبَّت تلقائياً عبر pip)
- نظام تشغيل وكيل ذكاء اصطناعي على الجهاز نفسه: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، n8n، أو Antigravity (أو مجلدات مثبّتة (mounted volumes) لـ Docker)
- Linux أو macOS

## دعم NemoClaw / OpenShell

تكتشف ClawMetry تلقائياً [NemoClaw](https://github.com/NVIDIA/NemoClaw) - غلاف الأمان المؤسسي من NVIDIA لـ OpenClaw الذي يشغّل الوكلاء داخل حاويات OpenShell معزولة (sandboxed).

لا حاجة لإعدادات إضافية في معظم الحالات. يكتشف شيطان (daemon) المزامنة تلقائياً ملفات الجلسات سواء كانت موجودة في `~/.openclaw/` على المضيف أو داخل حاوية OpenShell.

### كيف يعمل

تكتشف ClawMetry NemoClaw بطريقتين:

1. **اكتشاف عبر الملف التنفيذي** - تتحقق من وجود سطر أوامر `nemoclaw` وتشغّل `nemoclaw status` للحصول على معلومات البيئة المعزولة
2. **اكتشاف عبر الحاوية** - تفحص حاويات Docker العاملة بحثاً عن صور `openshell` أو `nemoclaw` أو `ghcr.io/nvidia/`، ثم تقرأ الجلسات عبر أدلة مثبّتة (volume mounts) أو `docker cp`

ملفات الجلسات المُزامنة من حاويات NemoClaw تُوسم بـ `runtime=nemoclaw` وبيانات وصفية `container_id` في لوحة التحكم السحابية، حتى تتمكن من تمييزها عن جلسات OpenClaw القياسية بلمحة واحدة.

### الإعداد الموصى به: شيطان المزامنة على المضيف

للحصول على أفضل تجربة، شغّل شيطان المزامنة الخاص بـ ClawMetry على **الجهاز المضيف** (وليس داخل البيئة المعزولة). هذا يتجنب قيود سياسة الشبكة الخاصة بـ NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سيجد شيطان المزامنة تلقائياً الجلسات داخل أي حاويات OpenShell قيد التشغيل.

### اختياري: اسم صريح للبيئة المعزولة

إن لم يعمل الاكتشاف التلقائي، وجّه ClawMetry إلى البيئة المعزولة الصحيحة:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### التشغيل داخل البيئة المعزولة (متقدم)

إن كان عليك تشغيل شيطان المزامنة **داخل** البيئة المعزولة لـ OpenShell، أضف قاعدة الخروج (egress) هذه إلى سياسة شبكة NemoClaw حتى يتمكن من الوصول إلى واجهة استيعاب ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

طبّقها بـ:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### المنافذ ونقاط النهاية

| نقطة النهاية | المنفذ | البروتوكول | مطلوب |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | نعم (شيطان المزامنة ← السحابة) |
| `localhost:8900` | 8900 | HTTP | نعم (لوحة التحكم المحلية) |
| مقبس Docker (`/var/run/docker.sock`) | — | مقبس Unix | لاكتشاف جلسات الحاوية |

شيطان المزامنة يجري فقط استدعاءات HTTPS صادرة إلى `ingest.clawmetry.com`. لا تُطلب منافذ واردة.

---

## النشر السحابي

راجع **[دليل اختبار السحابة](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** لأنفاق SSH، والوكيل العكسي (reverse proxy)، وDocker.

## الاختبار

هذا المشروع يُختبر باستخدام BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## القياس عن بُعد (Telemetry)

ترسل ClawMetry إشعارات مجهولة الهوية عن دورة حياة التثبيت إلى
`https://app.clawmetry.com/api/install`: إشعار `install` واحد في أول
مرة تشغّل فيها سطر أوامر `clawmetry` على جهاز جديد، وإشعار `update`
واحد في أول تشغيل بعد الترقية إلى إصدار جديد، وإشعار `onboarded`
واحد عند إتمام خيار الإعداد الأولي داخل لوحة التحكم. نستخدم هذا
لإحصاء التثبيتات الحقيقية (أرقام تنزيل PyPI الخام تعكس نحو 98٪ مرايا
(mirrors) وCI وإعادة تنزيلات التحديث التلقائي) ولمعرفة أطر عمل الوكلاء
والإصدارات الفعلية المستخدمة فعلياً.

**بحد أقصى طلب POST واحد لكل حدث دورة حياة لكل إصدار**، يحتوي على:

| الحقل | مثال | السبب |
|---|---|---|
| `install_id` | UUID عشوائي مخزّن في `~/.clawmetry/install_id` | إزالة التكرار؛ مجهول الهوية حتى تربط مزامنة Cloud صراحة (نبضة قلب الشيطان (daemon) المصادَقة عليها تحمل حينها هذا المعرّف، مما يربط هذا التثبيت بحسابك) |
| `event` | `install` / `update` / `onboarded` | تثبيت جديد مقابل ترقية تثبيت موجود |
| `version` | `0.12.167` | ما الإصدارات المستخدمة فعلياً |
| `os` / `os_version` | `Darwin` / `25.3.0` | أولويات دعم المنصات |
| `python` | `3.11.15` | مصفوفة دعم إصدارات Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | مع أي وكلاء ينبغي أن نتكامل تالياً |
| `is_ci` / `ci_provider` | `true` / `github_actions` | فصل تثبيتات البشر عن ضجيج CI |

**ما لا نرسله**: عنوان IP (تستخرج السحابة رمز البلد من الطلب من
جانب الخادم ثم تتجاهل عنوان IP)، اسم المضيف، اسم المستخدم، مسار
مساحة العمل، محتوى الملفات، مفتاح API الخاص بك، بريدك الإلكتروني،
أي شيء شخصي أو خاص بمساحة العمل. حمولة الاتصال (wire payload) قابلة
للتدقيق في
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**إلغاء التفعيل** (أي واحدة من هذه تعطّله بشكل دائم):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

فشل الشبكة هنا لا يمنع `clawmetry` أبداً من العمل - الإشعار يُرسل
دون انتظار رد (fire-and-forget) على خيط شيطان (daemon thread) بمهلة 3 ثوانٍ.

## تاريخ النجوم

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## الترخيص

MIT

---

<p align="center">
  <strong>🦞 شاهد وكيلك وهو يفكر</strong><br>
  <sub>بُني بواسطة <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · جزء من منظومة <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
