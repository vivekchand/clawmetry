<!-- i18n-src:48548997be76 -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**شاهد عميلك وهو يفكر.** مراقبة فورية لـ **12 بيئة تشغيل لعوامل الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw)، و[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، وClaude Code، وOpenAI Codex وغيرها 8. لوحة تحكم واحدة لأسطول عوامل العمل بالكامل.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد →](docs/i18n/)

أمر واحد. بدون إعداد. يكتشف كل شيء تلقائياً.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900** وأنت جاهز.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## يعمل مع 12 بيئة تشغيل للعوامل

بدأ ClawMetry كأداة مراقبة لـ OpenClaw، وأصبح الآن يقيس **أسطول عوامل العمل بأكمله** في لوحة تحكم واحدة، مع الاكتشاف التلقائي لكل بيئة تشغيل على جهازك:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw**

OpenClaw وNemoClaw متاحان مجاناً في التطبيق مفتوح المصدر؛ أما بيئات التشغيل الأخرى فتُفعَّل مع ClawMetry Cloud أو ترخيص Pro ذاتي الاستضافة. يمكنك التبديل بين بيئات التشغيل من الترويسة، وكل تبويب من التكلفة والرموز والأدوات والتتبعات يُحدِّث نطاقه وفقاً لبيئة التشغيل المختارة.

## ما ستحصل عليه

- **Flow** — مخطط متحرك مباشر يُظهر تدفق الرسائل عبر القنوات والدماغ والأدوات والعودة
- **Overview** — فحوصات الصحة وخريطة النشاط الحراري وعدد الجلسات ومعلومات النموذج
- **Usage** — تتبع الرموز والتكاليف مع تفصيل يومي وأسبوعي وشهري
- **Sessions** — جلسات العوامل النشطة مع النموذج والرموز وآخر نشاط
- **Crons** — المهام المجدولة مع الحالة والتشغيل التالي والمدة
- **Logs** — بث السجلات الفورية بالألوان
- **Memory** — تصفح SOUL.md وMEMORY.md وAGENTS.md والملاحظات اليومية
- **Transcripts** — واجهة فقاعات الدردشة لقراءة سجلات الجلسات
- **Alerts** — حدود الميزانية ومحفزات معدل الأخطاء وكشف توقف العوامل؛ مع إرسال إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **Approvals** — تقييد الحذف التدميري ودفع القوة وتعديلات قواعد البيانات وsudo وتثبيت الحزم والمكالمات الشبكية خلف موافقة بنقرة واحدة

## لقطات الشاشة

### 🧠 Brain — بث أحداث العامل المباشر
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — استخدام الرموز وملخص الجلسات
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — تغذية استدعاءات الأدوات في الوقت الفعلي
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفصيل التكلفة حسب النموذج والجلسة
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — متصفح ملفات مساحة العمل
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — الوضع الأمني وسجل التدقيق
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — حدود الميزانية ومحفزات معدل الأخطاء وخطافات الويب إلى Slack / Discord / PagerDuty / Email
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — تقييد استدعاءات الأدوات الخطرة خلف موافقة يدوية؛ قواعد حماية مدعومة بالسياسات
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

## التثبيت

**أمر واحد (موصى به):**
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

## تطوير واجهة المستخدم v2

يقع تطبيق React الخاص بـ v2 في `frontend/` ويُقدَّم على `/v2` عند تشغيل خادم Flask مع تفعيل v2.

استخدم نافذتَي طرفية أثناء التطوير:

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

افتح `http://localhost:5173/v2/`. يُوكّل Vite طلبات `/api` إلى `http://localhost:8900`، مما يتيح لتطبيق React التواصل مع خادم Flask المحلي دون الحاجة إلى إعداد CORS إضافي.

لبناء الحزمة التي تُشحن مع حزمة Python:

```bash
cd frontend
npm run build
```

تُكتب حزمة الإنتاج إلى `clawmetry/static/v2/dist/`.

## توافق بيئات التشغيل والعوامل

يراقب ClawMetry بيئات تشغيل عوامل الذكاء الاصطناعي المتعددة، وليس OpenClaw فحسب. تأتي كل بيئة تشغيل غير OpenClaw مزودة بمحوّل قراءة مخصص يترجم تنسيق جلستها الأصلي إلى الأشكال الموحدة في ClawMetry؛ يستوعبها الخادم الخفي في نفس مخزن DuckDB ولقطة السحابة، مُوسومةً ببيئة التشغيل، وتعرض علامة تبويب إعادة تشغيل الجلسة **محوّل بيئة التشغيل** عند وجود أكثر من واحدة. راجع [`docs/compatibility.md`](docs/compatibility.md) للمصفوفة الكاملة ودليل إضافة بيئات التشغيل، و[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) للتمهيد بعائلة OpenClaw.

| بيئة التشغيل / العامل | الحالة | ملاحظات |
|---|---|---|
| **OpenClaw** | أصلي | بيئة التشغيل المرجعية، مكتشفة تلقائياً |
| **PicoClaw** | محوّل تجريبي | JSONL بتنسيق `providers.Message` المسطّح (`~/.picoclaw/workspace/sessions`). النصوص والنموذج واستدعاءات الأدوات. |
| **NanoClaw** | محوّل تجريبي | SQLite لكل جلسة (`data/v2-sessions`). النصوص وأعداد الرسائل. |
| **Hermes** | محوّل تجريبي | SQLite في `~/.hermes/state.db`. النصوص والنموذج والرموز/التكلفة. |
| **Claude Code** | محوّل تجريبي | JSONL في `~/.claude/projects/.../<id>.jsonl`. النصوص والنموذج واستدعاءات الأدوات والتفكير واستخدام الرموز. |
| **Codex** | محوّل تجريبي | JSONL للتوزيع في `~/.codex/sessions/...`. النصوص والنموذج واستدعاءات الأدوات واستخدام الرموز. |
| **Cursor** | محوّل تجريبي | SQLite في `state.vscdb`. نصوص الدردشة/المؤلف والنموذج. |
| **Aider** | محوّل تجريبي | `.aider.chat.history.md` لكل مشروع. النصوص والنموذج وأعداد الرموز. |
| **Goose** | محوّل تجريبي | SQLite في `~/.local/share/goose`. النصوص والنموذج واستدعاءات الأدوات وإجمالي الرموز. |
| **opencode** | محوّل تجريبي | SQLite في `~/.local/share/opencode`. النصوص والنموذج واستدعاءات الأدوات والرموز والتكلفة. |
| **Qwen Code** | محوّل تجريبي | JSONL في `~/.qwen/projects/.../chats`. النصوص والنموذج واستدعاءات الأدوات واستخدام الرموز. |

"محوّل تجريبي" يعني أن ClawMetry يأتي مزوداً بقارئ لتنسيق بيئة التشغيل الفعلي على القرص، تم بناء كل منها والتحقق منه مقابل تثبيت حقيقي على جهاز حقيقي (انظر `tests/fixtures/runtimes/<rt>/`). المحوّلات للقراءة فقط؛ وكل منها صريح بشأن ما تخزّنه بيئة تشغيله فعلياً على القرص (مثل PicoClaw/NanoClaw/Cursor لا تكتب تكلفة الرموز على القرص). عند تشغيل عدة بيئات تشغيل على عقدة واحدة، يُضيّق محوّل بيئة التشغيل طريقة عرض الجلسات إلى واحدة للحصول على فحص عميق نظيف.

## تتبع أي عامل SDK خارجي — إسناد التكلفة خارج الحلقة

بيئات التشغيل أعلاه جميعها تكتب الجلسات على القرص. أما **عامل الإنتاج الخاص بك** الذي بنيته على OpenAI Agents SDK أو LangChain أو Vercel AI SDK أو LlamaIndex أو E2B أو حلقة `httpx` بسيطة، فهو لا يفعل ذلك. لا يزال معترض ClawMetry عديم الإعداد يلتقط استدعاءات LLM الخاصة به (التكلفة والرموز والكمون والأخطاء) عن طريق تصحيح `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

تُضيف `set_source()` (أو متغير البيئة `CLAWMETRY_SOURCE=support-agent`) لكل استدعاء وسماً بـ **مصدر مسمى**، لذا يظهر كل منتج تشغّله كسطر خاص به قابل للإسناد من حيث التكلفة في بطاقة **🔌 المصادر الخارجية** في Overview بالنسبة لعدد الاستدعاءات والمزودين والكمون ومعدل الأخطاء لكل عامل. لم يُحدَّد مصدر؟ لا تزال الاستدعاءات مُتتبَّعة؛ تبقى البطاقة فقط مخفية.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

هذه هي نفس طبقة البيانات التي تُغذيها محوّلات بيئة التشغيل (DuckDB ولقطة السحابة)، لذا تتزامن المصادر الخارجية مع لوحة تحكم السحابة مثلها مثل أي شيء آخر، مشفرةً من طرف إلى طرف.

## OpenTelemetry — محايد للبائعين، أرسل تتبعاتك في أي مكان

يتحدث ClawMetry **OpenTelemetry** في كلا الاتجاهين باستخدام **اتفاقيات دلالية GenAI**، لذا لن تُقيَّد تتبعات عاملك بأداة واحدة.

**تصدير** كل جلسة من استدعاءات LLM والأدوات والعوامل الفرعية والرموز والتكلفة كامتدادات OTLP/HTTP GenAI إلى أي جامع (Datadog أو Grafana أو Honeycomb أو OTel Collector الخاص بك):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

رؤوس المصادقة وفاصل الاستطلاع متغيرات بيئة اختيارية:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**استيعاب** — يقبل مستقبل OTLP المدمج التتبعات والمقاييس من أي شيء آخر على `/v1/traces` و`/v1/metrics` (استخدم `pip install clawmetry[otel]` لاستيعاب protobuf).

ستحصل على لوحة تحكم ClawMetry المحلية الأولى بدون إعداد **والـ** بياناتك في أي خلفية يشغّلها فريقك بالفعل، بدون قيود ودون الحاجة لتثبيت عامل ثانٍ.

## الإعداد

معظم الناس لا يحتاجون إلى أي إعداد. يكتشف ClawMetry تلقائياً مساحة عملك والسجلات والجلسات والمهام المجدولة.

إن احتجت إلى تخصيص:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

جميع الخيارات: `clawmetry --help`

## القنوات المدعومة

يعرض ClawMetry النشاط المباشر لكل قناة OpenClaw قمت بإعدادها. تظهر في مخطط Flow فقط القنوات المُعدَّة فعلاً في `openclaw.json` الخاص بك؛ تُخفى تلقائياً القنوات غير المُعدَّة.

انقر على أي عقدة قناة في Flow لعرض طريقة عرض فقاعات الدردشة المباشرة مع أعداد الرسائل الواردة والصادرة.

| القناة | الحالة | نافذة منبثقة مباشرة | ملاحظات |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ كاملة | ✅ | الرسائل والإحصاءات وتحديث كل 10 ثوانٍ |
| 💬 **iMessage** | ✅ كاملة | ✅ | تقرأ `~/Library/Messages/chat.db` مباشرة |
| 💚 **WhatsApp** | ✅ كاملة | ✅ | عبر WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ كاملة | ✅ | عبر signal-cli |
| 🟣 **Discord** | ✅ كاملة | ✅ | اكتشاف المجموعة والقناة |
| 🟪 **Slack** | ✅ كاملة | ✅ | اكتشاف مساحة العمل والقناة |
| 🌐 **Webchat** | ✅ كاملة | ✅ | جلسات واجهة الويب المدمجة |
| 📡 **IRC** | ✅ كاملة | ✅ | واجهة فقاعات بأسلوب الطرفية |
| 🍏 **BlueBubbles** | ✅ كاملة | ✅ | iMessage عبر BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ كاملة | ✅ | عبر خطافات ويب Chat API |
| 🟣 **MS Teams** | ✅ كاملة | ✅ | عبر إضافة بوت Teams |
| 🔷 **Mattermost** | ✅ كاملة | ✅ | دردشة الفريق ذاتية الاستضافة |
| 🟩 **Matrix** | ✅ كاملة | ✅ | لامركزي مع دعم E2EE |
| 🟢 **LINE** | ✅ كاملة | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ كاملة | ✅ | رسائل مباشرة NIP-04 لامركزية |
| 🟣 **Twitch** | ✅ كاملة | ✅ | الدردشة عبر اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ كاملة | ✅ | اشتراك في أحداث WebSocket |
| 🔵 **Zalo** | ✅ كاملة | ✅ | Zalo Bot API |

> **الاكتشاف التلقائي:** يقرأ ClawMetry ملف `~/.openclaw/openclaw.json` ويعرض فقط القنوات التي قمت بإعدادها فعلاً. لا حاجة إلى إعداد يدوي.

## نشر Docker

هل تريد تشغيل ClawMetry في حاوية؟ لا مشكلة! 🐳

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

**مثال على Docker Compose:**

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

> **ملاحظة:** عند التشغيل في Docker، قم بتركيب مجلدات بيانات وسجلات عاملك (مثل `~/.openclaw` و`~/.claude` و`~/.codex`) حتى يتمكن ClawMetry من اكتشاف إعدادك تلقائياً.

## المتطلبات

- Python 3.8+
- Flask (يُثبَّت تلقائياً عبر pip)
- بيئة تشغيل عامل ذكاء اصطناعي على نفس الجهاز: OpenClaw أو NVIDIA NemoClaw أو Claude Code أو Codex أو Cursor أو Goose أو Hermes أو opencode أو Qwen Code أو Aider أو NanoClaw أو PicoClaw (أو وحدات تخزين مركبة لـ Docker)
- Linux أو macOS

## دعم NemoClaw / OpenShell

يكتشف ClawMetry تلقائياً [NemoClaw](https://github.com/NVIDIA/NemoClaw) وهو غلاف أمان NVIDIA المؤسسي لـ OpenClaw الذي يشغّل العوامل داخل حاويات OpenShell معزولة.

لا حاجة إلى إعداد إضافي في معظم الحالات. يكتشف الخادم الخفي للمزامنة ملفات الجلسات تلقائياً سواء كانت في `~/.openclaw/` على المضيف أو داخل حاوية OpenShell.

### كيف يعمل

يكتشف ClawMetry NemoClaw بطريقتين:

1. **اكتشاف الملف التنفيذي** — يتحقق من وجود `nemoclaw` CLI ويشغّل `nemoclaw status` للحصول على معلومات البيئة المعزولة
2. **اكتشاف الحاوية** — يفحص حاويات Docker الجارية بحثاً عن صور `openshell` أو `nemoclaw` أو `ghcr.io/nvidia/`، ثم يقرأ الجلسات عبر تركيب الوحدات أو `docker cp`

تُوسَم ملفات الجلسات المتزامنة من حاويات NemoClaw بـ `runtime=nemoclaw` وبيانات `container_id` الوصفية في لوحة تحكم السحابة، حتى تتمكن من تمييزها عن جلسات OpenClaw القياسية بلمحة.

### الإعداد الموصى به: الخادم الخفي للمزامنة على المضيف

للحصول على أفضل تجربة، شغّل الخادم الخفي للمزامنة في ClawMetry على **جهاز المضيف** (وليس داخل البيئة المعزولة). هذا يتجنب قيود سياسة شبكة NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سيجد الخادم الخفي للمزامنة تلقائياً الجلسات داخل أي حاويات OpenShell جارية.

### اختياري: اسم البيئة المعزولة الصريح

إن لم يعمل الاكتشاف التلقائي، وجّه ClawMetry نحو البيئة المعزولة الصحيحة:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### التشغيل داخل البيئة المعزولة (متقدم)

إن كان لا بد من تشغيل الخادم الخفي للمزامنة **داخل** بيئة OpenShell المعزولة، أضف قاعدة الخروج هذه إلى سياسة شبكة NemoClaw لتمكينه من الوصول إلى واجهة برمجة استيعاب ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

طبّق باستخدام:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### المنافذ ونقاط النهاية

| نقطة النهاية | المنفذ | البروتوكول | مطلوب |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | نعم (الخادم الخفي للمزامنة إلى السحابة) |
| `localhost:8900` | 8900 | HTTP | نعم (واجهة مستخدم لوحة التحكم المحلية) |
| مقبس Docker (`/var/run/docker.sock`) | — | مقبس Unix | لاكتشاف جلسات الحاويات |

يُجري الخادم الخفي للمزامنة استدعاءات HTTPS صادرة فقط إلى `ingest.clawmetry.com`. لا تُتطلب منافذ واردة.

---

## النشر السحابي

راجع **[دليل اختبار السحابة](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** لأنفاق SSH والوكيل العكسي وDocker.

## الاختبار

يُختبَر هذا المشروع باستخدام BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## القياس عن بعد

يُرسل ClawMetry نبضة مجهولة الهوية لـ "أول تشغيل" إلى `https://app.clawmetry.com/api/install` في المرة الأولى التي تشغّل فيها `clawmetry` CLI على جهاز جديد. نستخدم هذا لعدّ عمليات التثبيت (المقياس التسويقي الوحيد لدينا في مشروع مفتوح المصدر) ولمعرفة أطر عمل العوامل المثبتة لدى مستخدمينا.

**طلب POST واحد بالضبط لكل تثبيت**، يحتوي على:

| الحقل | مثال | السبب |
|---|---|---|
| `install_id` | UUID عشوائي مخزّن في `~/.clawmetry/install_id` | إزالة التكرار؛ غير مرتبط بالبريد الإلكتروني أو api_key |
| `version` | `0.12.167` | معرفة الإصدارات المنتشرة |
| `os` / `os_version` | `Darwin` / `25.3.0` | أولويات دعم المنصات |
| `python` | `3.11.15` | مصفوفة دعم إصدارات Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | معرفة العوامل التي يجب التكامل معها أولاً |
| `is_ci` / `ci_provider` | `true` / `github_actions` | فصل عمليات التثبيت البشرية عن ضوضاء CI |

**ما لا نُرسله**: عنوان IP (تستخلص السحابة رمز الدولة من جانب الخادم من الطلب ثم تتجاهل IP)، واسم المضيف، واسم المستخدم، ومسار مساحة العمل، ومحتويات الملفات، وapi_key الخاص بك، والبريد الإلكتروني، وأي معلومات شخصية أو خاصة بمساحة العمل. يمكن تدقيق الحمولة الفعلية في [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**إلغاء الاشتراك** (أي من هذه الخيارات يُعطّله نهائياً):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

فشل الشبكة هنا لن يمنع تشغيل `clawmetry` أبداً؛ النبضة تُرسَل وتُنسى على خيط خفي بمهلة 3 ثوانٍ.

## سجل النجوم

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## الرخصة

MIT

---

<p align="center">
  <strong>🦞 شاهد عميلك وهو يفكر</strong><br>
  <sub>بُني بواسطة <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · جزء من منظومة <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
