<!-- i18n-src:56ff57310588 -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**شاهد وكيلك وهو يفكّر.** مراقبة فورية لوكلاء الذكاء الاصطناعي في [OpenClaw](https://github.com/openclaw/openclaw).

> 🌐 **اقرأ هذا بـ:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد →](docs/i18n/)

أمر واحد. بلا إعداد. يكتشف كل شيء تلقائيًا.

```bash
pip install clawmetry && clawmetry
```

يُفتح على **http://localhost:8900** وانتهيت.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## ما الذي تحصل عليه

- **Flow** — مخطط متحرك حيّ يُظهر الرسائل وهي تتدفّق عبر القنوات والدماغ والأدوات ثم تعود
- **Overview** — فحوصات الصحة، وخريطة حرارية للنشاط، وعدد الجلسات، ومعلومات النموذج
- **Usage** — تتبّع الرموز (tokens) والتكلفة مع تفصيلات يومية وأسبوعية وشهرية
- **Sessions** — جلسات الوكيل النشطة مع النموذج والرموز وآخر نشاط
- **Crons** — المهام المجدولة مع الحالة، والتشغيل التالي، والمدة
- **Logs** — بثّ فوري للسجلّات مع ترميز لوني
- **Memory** — تصفّح SOUL.md و MEMORY.md و AGENTS.md والملاحظات اليومية
- **Transcripts** — واجهة فقاعات محادثة لقراءة سجلّات الجلسات
- **Alerts** — حدود الميزانية، ومحفّزات معدّل الأخطاء، وكشف توقّف الوكيل؛ توجّه إلى Slack و Discord و PagerDuty و Telegram والبريد الإلكتروني
- **Approvals** — احجب عمليات الحذف المدمّرة، والدفع القسري (force push)، وتعديلات قواعد البيانات، و sudo، وتثبيت الحزم، والمكالمات الشبكية خلف موافقة بنقرة واحدة

## لقطات الشاشة

### 🧠 Brain — بثّ حيّ لأحداث الوكيل
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — استخدام الرموز وملخّص الجلسة
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — موجز فوري لاستدعاءات الأدوات
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفصيل التكلفة حسب النموذج والجلسة
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — متصفّح ملفات مساحة العمل
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — الوضع الأمني وسجلّ التدقيق
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — حدود الميزانية، ومحفّزات معدّل الأخطاء، وخطّافات الويب إلى Slack / Discord / PagerDuty / البريد الإلكتروني
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — احجب استدعاءات الأدوات الخطرة خلف موافقة يدوية؛ قواعد حماية مدعومة بالسياسات
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

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

## تطوير واجهة v2 الأمامية

يعيش تطبيق v2 المبني بـ React في `frontend/` ويُقدَّم على `/v2` عند تشغيل خادم
Flask مع تفعيل v2.

استخدم طرفيتين أثناء التطوير:

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
`http://localhost:8900`، بحيث يستطيع تطبيق React التحدّث إلى خادم Flask المحلّي
دون إعداد CORS إضافي.

لبناء الحزمة التي تُشحن مع حزمة Python:

```bash
cd frontend
npm run build
```

تُكتب حزمة الإنتاج إلى `clawmetry/static/v2/dist/`.

## التوافق مع بيئات التشغيل / الوكلاء

تراقب ClawMetry العديد من بيئات تشغيل وكلاء الذكاء الاصطناعي، وليس OpenClaw فقط. كل بيئة تشغيل غير OpenClaw تأتي مع محوّل قارئ مخصّص يترجم صيغة جلستها الأصلية إلى الأشكال الموحّدة في ClawMetry؛ يستوعبها الخادم الخفي (daemon) في نفس مخزن DuckDB ولقطة السحابة، موسومة ببيئة التشغيل، وتُظهر علامة تبويب إعادة تشغيل الجلسة **مبدّل بيئة التشغيل** عند وجود أكثر من واحدة. راجع [`docs/compatibility.md`](docs/compatibility.md) للمصفوفة الكاملة ودليل إضافة بيئات التشغيل، و [`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) للمقدّمة التمهيدية لعائلة OpenClaw.

| بيئة التشغيل / الوكيل | الحالة | ملاحظات |
|---|---|---|
| **OpenClaw** | أصلية | بيئة التشغيل المرجعية، مكتشَفة تلقائيًا |
| **PicoClaw** | محوّل تجريبي | JSONL مسطّح بصيغة `providers.Message` (`~/.picoclaw/workspace/sessions`). نصوص الجلسات، النموذج، استدعاءات الأدوات. |
| **NanoClaw** | محوّل تجريبي | SQLite لكل جلسة (`data/v2-sessions`). نصوص الجلسات + عدد الرسائل. |
| **Hermes** | محوّل تجريبي | SQLite في `~/.hermes/state.db`. نصوص الجلسات، النموذج، الرموز/التكلفة. |
| **Claude Code** | محوّل تجريبي | JSONL في `~/.claude/projects/.../<id>.jsonl`. نصوص الجلسات، النموذج، استدعاءات الأدوات + التفكير، استخدام الرموز. |
| **Codex** | محوّل تجريبي | JSONL للطرح في `~/.codex/sessions/...`. نصوص الجلسات، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Cursor** | محوّل تجريبي | SQLite في `state.vscdb`. نصوص المحادثة/المؤلّف، النموذج. |
| **Aider** | محوّل تجريبي | `.aider.chat.history.md` لكل مشروع. نصوص الجلسات، النموذج، عدد الرموز. |
| **Goose** | محوّل تجريبي | SQLite في `~/.local/share/goose`. نصوص الجلسات، النموذج، استدعاءات الأدوات، إجمالي الرموز. |

يعني "محوّل تجريبي" أن ClawMetry تأتي بقارئ لصيغة هذه البيئة الفعلية على القرص، كلٌّ منها مبني ومُتحقَّق منه مقابل تثبيت حقيقي على جهاز حقيقي (راجع `tests/fixtures/runtimes/<rt>/`). المحوّلات للقراءة فقط؛ وكلٌّ منها صادق بشأن ما تخزّنه بيئته فعليًا (مثلًا، لا تكتب PicoClaw/NanoClaw/Cursor تكلفة الرموز إلى القرص). عند تشغيل عدّة بيئات على عقدة واحدة، يقصر مبدّل بيئة التشغيل عرض الجلسات على واحدة من أجل تحليل معمّق نظيف.

## OpenTelemetry — محايد تجاه المورّدين، أرسل تتبّعاتك إلى أي مكان

تتحدّث ClawMetry بلغة **OpenTelemetry** في الاتجاهين، مستخدمةً **الاصطلاحات الدلالية لـ GenAI**، بحيث لا تُحبس تتبّعات وكيلك أبدًا في أداة واحدة.

**صدّر** كل جلسة (استدعاءات LLM، والأدوات، والوكلاء الفرعيين، والرموز، والتكلفة) كأطياف (spans) من نوع OTLP/HTTP GenAI إلى أي مُجمّع (Datadog أو Grafana أو Honeycomb أو OTel Collector الخاص بك):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

ترويسات المصادقة وفترة الاستطلاع هي متغيّرات بيئة اختيارية:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**استوعب** — يقبل مستقبِل OTLP المدمج التتبّعات والمقاييس من أي شيء آخر على `/v1/traces` و `/v1/metrics` (نفّذ `pip install clawmetry[otel]` للاستيعاب عبر protobuf).

تحصل على لوحة معلومات ClawMetry المحلّية أولًا وبلا إعداد، **و** على بياناتك في أي خلفية يشغّلها فريقك بالفعل، بلا احتباس، وبلا وكيل ثانٍ تثبّته.

## الإعداد

معظم الناس لا يحتاجون إلى أي إعداد. تكتشف ClawMetry تلقائيًا مساحة عملك، وسجلّاتك، وجلساتك، ومهام cron.

إذا احتجت فعلًا إلى التخصيص:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

كل الخيارات: `clawmetry --help`

## القنوات المدعومة

تُظهر ClawMetry النشاط الحيّ لكل قناة OpenClaw قمت بإعدادها. القنوات التي أُعدّت فعلًا في ملف `openclaw.json` فقط هي التي تظهر في مخطط Flow، أما غير المُعدّة فتُخفى تلقائيًا.

انقر أي عقدة قناة في Flow لرؤية واجهة فقاعات محادثة حيّة مع عدد الرسائل الواردة/الصادرة.

| القناة | الحالة | نافذة منبثقة حيّة | ملاحظات |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ كاملة | ✅ | الرسائل، الإحصاءات، تحديث كل 10 ثوانٍ |
| 💬 **iMessage** | ✅ كاملة | ✅ | يقرأ `~/Library/Messages/chat.db` مباشرة |
| 💚 **WhatsApp** | ✅ كاملة | ✅ | عبر WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ كاملة | ✅ | عبر signal-cli |
| 🟣 **Discord** | ✅ كاملة | ✅ | اكتشاف الخادم (Guild) + القناة |
| 🟪 **Slack** | ✅ كاملة | ✅ | اكتشاف مساحة العمل + القناة |
| 🌐 **Webchat** | ✅ كاملة | ✅ | جلسات واجهة الويب المدمجة |
| 📡 **IRC** | ✅ كاملة | ✅ | واجهة فقاعات بنمط الطرفية |
| 🍏 **BlueBubbles** | ✅ كاملة | ✅ | iMessage عبر واجهة BlueBubbles REST |
| 🔵 **Google Chat** | ✅ كاملة | ✅ | عبر خطّافات Chat API |
| 🟣 **MS Teams** | ✅ كاملة | ✅ | عبر مكوّن بوت Teams |
| 🔷 **Mattermost** | ✅ كاملة | ✅ | دردشة فريق ذاتية الاستضافة |
| 🟩 **Matrix** | ✅ كاملة | ✅ | لامركزية، مع دعم E2EE |
| 🟢 **LINE** | ✅ كاملة | ✅ | واجهة LINE Messaging API |
| ⚡ **Nostr** | ✅ كاملة | ✅ | رسائل خاصة لامركزية NIP-04 |
| 🟣 **Twitch** | ✅ كاملة | ✅ | الدردشة عبر اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ كاملة | ✅ | اشتراك أحداث عبر WebSocket |
| 🔵 **Zalo** | ✅ كاملة | ✅ | واجهة Zalo Bot API |

> **الاكتشاف التلقائي:** تقرأ ClawMetry ملف `~/.openclaw/openclaw.json` ولا تعرض إلا القنوات التي أعددتها فعلًا. لا حاجة لأي إعداد يدوي.

## النشر عبر Docker

تريد تشغيل ClawMetry داخل حاوية؟ لا مشكلة! 🐳

**بداية سريعة مع Docker:**

```bash
# Build the image
docker build -t clawmetry .

# Run with default settings
docker run -p 8900:8900 clawmetry

# Or with your OpenClaw workspace mounted
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

> **ملاحظة:** عند التشغيل داخل Docker، تأكّد من تركيب مساحة عمل OpenClaw ومجلّدات السجلّات حتى تتمكّن ClawMetry من اكتشاف إعدادك تلقائيًا.

## المتطلّبات

- Python 3.8+
- Flask (يُثبَّت تلقائيًا عبر pip)
- OpenClaw يعمل على نفس الجهاز (أو وحدات تخزين مُركَّبة لـ Docker)
- Linux أو macOS

## دعم NemoClaw / OpenShell

تكتشف ClawMetry تلقائيًا [NemoClaw](https://github.com/NVIDIA/NemoClaw)، وهو غلاف NVIDIA الأمني المؤسسي لـ OpenClaw الذي يشغّل الوكلاء داخل حاويات OpenShell معزولة.

لا حاجة إلى أي إعداد إضافي في معظم الحالات. يكتشف الخادم الخفي للمزامنة ملفات الجلسات تلقائيًا سواء كانت موجودة في `~/.openclaw/` على المضيف أو داخل حاوية OpenShell.

### كيف يعمل

تكتشف ClawMetry وجود NemoClaw بطريقتين:

1. **اكتشاف الثنائي** — يبحث عن أداة `nemoclaw` ويشغّل `nemoclaw status` للحصول على معلومات الحاوية المعزولة
2. **اكتشاف الحاوية** — يفحص حاويات Docker العاملة بحثًا عن صور `openshell` أو `nemoclaw` أو `ghcr.io/nvidia/`، ثم يقرأ الجلسات عبر وحدات التخزين المُركَّبة أو `docker cp`

تُوسم ملفات الجلسات المُزامَنة من حاويات NemoClaw ببيانات وصفية `runtime=nemoclaw` و `container_id` في لوحة معلومات السحابة، لتتمكّن من تمييزها عن جلسات OpenClaw القياسية بنظرة واحدة.

### الإعداد الموصى به: الخادم الخفي للمزامنة على المضيف

للحصول على أفضل تجربة، شغّل الخادم الخفي للمزامنة في ClawMetry على **الجهاز المضيف** (وليس داخل الحاوية المعزولة). يتجنّب هذا قيود سياسة شبكة NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سيعثر الخادم الخفي للمزامنة تلقائيًا على الجلسات داخل أي حاويات OpenShell عاملة.

### اختياري: اسم صريح للحاوية المعزولة

إذا لم ينجح الاكتشاف التلقائي، وجّه ClawMetry إلى الحاوية المعزولة الصحيحة:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### التشغيل داخل الحاوية المعزولة (متقدّم)

إذا كان لا بدّ من تشغيل الخادم الخفي للمزامنة **داخل** حاوية OpenShell المعزولة، أضف قاعدة الخروج هذه إلى سياسة شبكة NemoClaw حتى يتمكّن من الوصول إلى واجهة استيعاب ClawMetry:

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

### المنافذ والنقاط الطرفية

| النقطة الطرفية | المنفذ | البروتوكول | مطلوب |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | نعم (الخادم الخفي للمزامنة ← السحابة) |
| `localhost:8900` | 8900 | HTTP | نعم (واجهة لوحة المعلومات المحلّية) |
| مقبس Docker (`/var/run/docker.sock`) | — | مقبس Unix | لاكتشاف جلسات الحاويات |

لا يجري الخادم الخفي للمزامنة إلا مكالمات HTTPS صادرة إلى `ingest.clawmetry.com`. لا حاجة إلى أي منافذ واردة.

---

## النشر السحابي

راجع **[دليل الاختبار السحابي](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** لأنفاق SSH، والوكيل العكسي (reverse proxy)، و Docker.

## الاختبار

يُختبر هذا المشروع بواسطة BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## القياس عن بُعد (Telemetry)

ترسل ClawMetry إشارة "أول تشغيل" واحدة مجهولة الهوية إلى
`https://app.clawmetry.com/api/install` في المرة الأولى التي تشغّل فيها أداة
`clawmetry` على جهاز جديد. نستخدم هذا لإحصاء عمليات التثبيت (مقياس التسويق
الوحيد المتاح لنا في مشروع مفتوح المصدر) ولمعرفة أُطُر عمل الوكلاء التي ثبّتها
مستخدمونا.

**طلب POST واحد بالضبط لكل تثبيت**، يحتوي على:

| الحقل | مثال | السبب |
|---|---|---|
| `install_id` | معرّف UUID عشوائي مخزّن في `~/.clawmetry/install_id` | لإزالة التكرار؛ غير مرتبط ببريدك الإلكتروني أو api_key |
| `version` | `0.12.167` | معرفة الإصدارات المنتشرة |
| `os` / `os_version` | `Darwin` / `25.3.0` | أولويّات دعم المنصّات |
| `python` | `3.11.15` | مصفوفة دعم إصدارات Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | أي الوكلاء ينبغي أن ندمج معهم تاليًا |
| `is_ci` / `ci_provider` | `true` / `github_actions` | فصل عمليات التثبيت البشرية عن ضجيج CI |

**ما الذي لا نرسله**: عنوان IP (تستنتج السحابة رمز البلد على جانب الخادم
من الطلب، ثم تتخلّص من عنوان IP)، أو اسم المضيف، أو اسم المستخدم، أو مسار
مساحة العمل، أو محتويات الملفات، أو api_key الخاص بك، أو بريدك الإلكتروني،
أو أي معلومات تعريف شخصية أو خاصة بمساحة العمل. حمولة الإرسال قابلة للتدقيق في
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**إلغاء الاشتراك** (أيٌّ من هذه يعطّله نهائيًا):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

لا يمنع فشل الشبكة هنا تشغيل `clawmetry` أبدًا: فالإشارة تُرسَل وتُنسى على خيط
خادم خفي بمهلة 3 ثوانٍ.

## سجلّ النجوم

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
  <strong>🦞 شاهد وكيلك وهو يفكّر</strong><br>
  <sub>صُنع بواسطة <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · جزء من منظومة <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
