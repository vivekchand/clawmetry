<!-- i18n-src:8252f6b1d31d -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**شاهد وكيلك وهو يفكّر.** مراقبة فورية لـ **14 بيئة تشغيل لوكلاء الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و10 أخرى. لوحة تحكم واحدة لأسطول وكلائك بالكامل.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بلا إعدادات. يكتشف كل شيء تلقائيًا.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900** وينتهي الأمر.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## يعمل مع 14 بيئة تشغيل للوكلاء

بدأت ClawMetry كأداة مراقبة لـ OpenClaw، والآن تقيس **أسطول وكلائك بالكامل** في لوحة تحكم واحدة، وتكتشف تلقائيًا كل بيئة تشغيل على جهازك:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw وNemoClaw مجانيان في التطبيق مفتوح المصدر؛ أما بقية بيئات التشغيل فتُفعَّل عبر ClawMetry Cloud أو ترخيص Pro ذاتي الاستضافة. بدّل بين بيئات التشغيل من الرأس، وكل تبويب - التكلفة، الرموز، الأدوات، التتبعات - يعيد تحديد نطاقه إلى تلك البيئة. راجع **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** للاطلاع على التقسيم الدقيق بين المجاني والمدفوع، ومصفوفة المستويات، وشكل `/api/entitlement`، وأداة سطر الأوامر `clawmetry license`.

## ما الذي ستحصل عليه

- **Flow** — رسم بياني متحرك حي يعرض تدفق الرسائل عبر القنوات والدماغ والأدوات والعودة
- **Overview** — فحوصات صحية، خريطة حرارية للنشاط، عدد الجلسات، معلومات النموذج
- **Usage** — تتبع الرموز والتكلفة مع تفصيل يومي/أسبوعي/شهري
- **Sessions** — جلسات الوكيل النشطة مع النموذج والرموز وآخر نشاط
- **Crons** — المهام المجدولة مع الحالة، التشغيل التالي، المدة
- **Logs** — بث السجلات الفورية بترميز لوني
- **Memory** — تصفح SOUL.md، MEMORY.md، AGENTS.md، الملاحظات اليومية
- **Transcripts** — واجهة فقاعات دردشة لقراءة سجلات الجلسات
- **Alerts** — حدود ميزانية، محفزات معدل الأخطاء، كشف عدم اتصال الوكيل؛ يوجّه إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **Approvals** — حجب عمليات الحذف المدمّرة، الدفع القسري، تعديلات قاعدة البيانات، sudo، تثبيت الحزم، واستدعاءات الشبكة خلف موافقة بنقرة واحدة

## لقطات شاشة

### 🧠 Brain — بث حي لأحداث الوكيل
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — استخدام الرموز وملخص الجلسات
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — تغذية استدعاء الأدوات الفورية
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفصيل التكلفة حسب النموذج والجلسة
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — متصفح ملفات مساحة العمل
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — الوضعية الأمنية وسجل التدقيق
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — حدود الميزانية، محفزات معدل الأخطاء، ووصلات ويب إلى Slack / Discord / PagerDuty / البريد الإلكتروني
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — حجب استدعاءات الأدوات الخطرة خلف موافقة يدوية؛ قواعد حماية مدعومة بسياسات
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**الحجب قبل التنفيذ لـ Claude Code** — أمر واحد يثبّت خطاف
PreToolUse يوقف استدعاءات الأدوات المطابقة *قبل* تشغيلها وينتظر
قرارك (بنقرة واحدة من هاتفك عند تفعيل
[إشعارات الدفع السحابية](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

الرفض يحجب استدعاء تلك الأداة فقط - يحتفظ الوكيل بجلسته ويمكنه
تجربة نهج آخر. الموافقة من هاتفك تتخطى موجّه الأذونات الخاص بـ Claude Code
(أنت أجبت بالفعل). الأدوات غير المطابقة تكلّف حوالي 40 مللي ثانية
وتمر عبر تدفق الأذونات المعتاد لـ Claude Code. تحصل أيضًا على إشعار دفع على هاتفك عندما ينتظرك Claude Code نفسه (إشعارات `permission_prompt` /
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

تطبيق React الخاص بالإصدار v2 موجود في `frontend/` ويُخدَّم على
`/v2` عند تشغيل خادم Flask مع تفعيل v2.

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
`http://localhost:8900`، بحيث يمكن لتطبيق React التواصل مع خادم Flask
المحلي دون إعداد CORS إضافي.

لبناء الحزمة التي تُشحن مع حزمة Python:

```bash
cd frontend
npm run build
```

تُكتب الحزمة الإنتاجية في `clawmetry/static/v2/dist/`.

## توافق بيئات التشغيل / الوكلاء

تراقب ClawMetry العديد من بيئات تشغيل وكلاء الذكاء الاصطناعي، وليس فقط OpenClaw. كل بيئة تشغيل غير OpenClaw تأتي مع محوّل قراءة مخصص يترجم صيغة الجلسة الأصلية إلى الأشكال الموحّدة لـ ClawMetry؛ يقوم الخادم الخلفي بإدخالها في نفس مخزن DuckDB + اللقطة السحابية، مع وسم بيئة التشغيل، ويعرض تبويب إعادة تشغيل الجلسة **مبدّل بيئة تشغيل** عند وجود أكثر من واحدة. راجع [`docs/compatibility.md`](docs/compatibility.md) للمصفوفة الكاملة + دليل إضافة بيئات تشغيل، و[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) لمقدمة عائلة OpenClaw.

| بيئة التشغيل / الوكيل | الحالة | ملاحظات |
|---|---|---|
| **OpenClaw** | أصلي | بيئة التشغيل المرجعية، تُكتشف تلقائيًا |
| **PicoClaw** | محوّل تجريبي | JSONL مسطّح لـ `providers.Message` (`~/.picoclaw/workspace/sessions`). نصوص، نموذج، استدعاءات أدوات. |
| **NanoClaw** | محوّل تجريبي | SQLite لكل جلسة (`data/v2-sessions`). نصوص + عدد الرسائل. |
| **Hermes** | محوّل تجريبي | SQLite في `~/.hermes/state.db`. نصوص، نموذج، رموز/تكلفة. |
| **Claude Code** | محوّل تجريبي | JSONL في `~/.claude/projects/.../<id>.jsonl`. نصوص، نموذج، استدعاءات أدوات + تفكير، استخدام الرموز. |
| **Codex** | محوّل تجريبي | Rollout JSONL في `~/.codex/sessions/...`. نصوص، نموذج، استدعاءات أدوات، استخدام الرموز. |
| **Cursor** | محوّل تجريبي | SQLite `state.vscdb`. نصوص دردشة/تحرير، نموذج. |
| **Aider** | محوّل تجريبي | `.aider.chat.history.md` لكل مشروع. نصوص، نموذج، عدد الرموز. |
| **Goose** | محوّل تجريبي | SQLite في `~/.local/share/goose`. نصوص، نموذج، استدعاءات أدوات، إجمالي الرموز. |
| **opencode** | محوّل تجريبي | SQLite في `~/.local/share/opencode`. نصوص، نموذج، استدعاءات أدوات، رموز + تكلفة. |
| **Qwen Code** | محوّل تجريبي | JSONL في `~/.qwen/projects/.../chats`. نصوص، نموذج، استدعاءات أدوات، استخدام الرموز. |
| **Pi** | محوّل تجريبي | JSONL في `~/.pi/agent/sessions`. نصوص، نموذج، استدعاءات أدوات، رموز + تكلفة. |
| **Deep Agents** | محوّل تجريبي | SQLite في `~/.deepagents/.state/sessions.db`. نصوص، نموذج، استدعاءات أدوات، رموز + تكلفة. |
| **n8n** | محوّل تجريبي | SQLite في `~/.n8n/database.sqlite`. تنفيذات سير العمل، تشغيلات العقد، مطالبات وكيل الذكاء الاصطناعي، النموذج + الرموز حيث يسجّلها n8n. |

"محوّل تجريبي" يعني أن ClawMetry تشحن قارئًا لصيغة القرص الفعلية لبيئة التشغيل تلك، وكل واحد مبني ومُتحقَّق منه مقابل تثبيت حقيقي على جهاز حقيقي (راجع `tests/fixtures/runtimes/<rt>/`). المحوّلات للقراءة فقط؛ وكل واحد منها صادق بشأن ما تخزّنه بيئة التشغيل فعليًا (مثلًا PicoClaw/NanoClaw/Cursor لا تكتب تكلفة الرموز على القرص). عند تشغيل عدة بيئات تشغيل على عقدة واحدة، يقصر مبدّل بيئة التشغيل عرض الجلسات على واحدة للتعمق النظيف.

## تتبّع أي وكيل SDK — إسناد التكلفة خارج الحلقة

بيئات التشغيل أعلاه جميعها تكتب الجلسات على القرص. وكيلك **الإنتاجي** الخاص - الذي بنيته على OpenAI Agents SDK، أو LangChain، أو Vercel AI SDK، أو LlamaIndex، أو E2B، أو حلقة `httpx` بسيطة - لا يفعل ذلك. المعترض الخالي من الإعدادات في ClawMetry ما زال يلتقط استدعاءات النموذج اللغوي الخاصة به (التكلفة، الرموز، زمن الاستجابة، الأخطاء) عبر تصحيح `httpx`/`requests` أثناء التشغيل:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (أو متغير البيئة `CLAWMETRY_SOURCE=support-agent`) يسم كل استدعاء بـ **مصدر مسمّى**، بحيث يظهر كل منتج تشغّله كسطر مستقل قابل لإسناد التكلفة في بطاقة **🔌 المصادر خارج الحلقة** في لوحة التحكم في تبويب Overview - الاستدعاءات، الموفّرون، زمن الاستجابة، معدل الأخطاء لكل وكيل. لم يُحدَّد مصدر؟ ما زالت الاستدعاءات تُتبّع، وتبقى البطاقة مخفية فقط.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

هذه هي نفس طبقة البيانات التي تغذيها محوّلات بيئات التشغيل (DuckDB ← اللقطة السحابية)، لذا تتزامن المصادر خارج الحلقة مع لوحة التحكم السحابية مثل كل شيء آخر، مشفّرة من طرف إلى طرف.

## OpenTelemetry — محايد تجاه الموفّر، أرسل تتبعاتك إلى أي مكان

تتحدث ClawMetry لغة **OpenTelemetry** في كلا الاتجاهين، باستخدام **اصطلاحات GenAI الدلالية**، بحيث لا تُحبس تتبعات وكيلك أبدًا داخل أداة واحدة.

**التصدير**: كل جلسة - استدعاءات النموذج اللغوي، الأدوات، الوكلاء الفرعيون، الرموز، التكلفة - كـ نطاقات OTLP/HTTP GenAI إلى أي جامع (Datadog، Grafana، Honeycomb، أو جامع OTel الخاص بك):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

رؤوس المصادقة وفاصل الاستقصاء متغيرات بيئة اختيارية:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**الاستيراد** - يستقبل مستقبِل OTLP المدمج التتبعات والمقاييس من أي مصدر آخر على `/v1/traces` و`/v1/metrics` (`pip install clawmetry[otel]` لاستيراد protobuf).

تحصل على لوحة تحكم ClawMetry الخالية من الإعدادات والمحلية أولًا **و** بياناتك في أي نظام خلفي يستخدمه فريقك بالفعل - بلا قيود، وبلا وكيل ثانٍ للتثبيت.

## الإعدادات

معظم الناس لا يحتاجون إلى أي إعدادات. تكتشف ClawMetry تلقائيًا مساحة عملك وسجلاتك وجلساتك ومهامك المجدولة.

إذا احتجت إلى التخصيص:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

كل الخيارات: `clawmetry --help`

## القنوات المدعومة

تعرض ClawMetry النشاط الحي لكل قناة OpenClaw قمت بإعدادها. القنوات المُعدَّة فعليًا في `openclaw.json` الخاص بك فقط هي التي تظهر في رسم Flow البياني - القنوات غير المُعدَّة تُخفى تلقائيًا.

انقر على أي عقدة قناة في Flow لرؤية عرض فقاعات دردشة حي مع عدّاد الرسائل الواردة/الصادرة.

| القناة | الحالة | نافذة حية منبثقة | ملاحظات |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ كامل | ✅ | رسائل، إحصائيات، تحديث كل 10 ثوانٍ |
| 💬 **iMessage** | ✅ كامل | ✅ | يقرأ `~/Library/Messages/chat.db` مباشرة |
| 💚 **WhatsApp** | ✅ كامل | ✅ | عبر WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ كامل | ✅ | عبر signal-cli |
| 🟣 **Discord** | ✅ كامل | ✅ | كشف الخوادم + القنوات |
| 🟪 **Slack** | ✅ كامل | ✅ | كشف مساحة العمل + القنوات |
| 🌐 **Webchat** | ✅ كامل | ✅ | جلسات واجهة الويب المدمجة |
| 📡 **IRC** | ✅ كامل | ✅ | واجهة فقاعات بنمط الطرفية |
| 🍏 **BlueBubbles** | ✅ كامل | ✅ | iMessage عبر واجهة BlueBubbles REST |
| 🔵 **Google Chat** | ✅ كامل | ✅ | عبر ويب هوكس Chat API |
| 🟣 **MS Teams** | ✅ كامل | ✅ | عبر إضافة بوت Teams |
| 🔷 **Mattermost** | ✅ كامل | ✅ | دردشة فريق ذاتية الاستضافة |
| 🟩 **Matrix** | ✅ كامل | ✅ | لامركزي، دعم E2EE |
| 🟢 **LINE** | ✅ كامل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ كامل | ✅ | رسائل مباشرة لامركزية NIP-04 |
| 🟣 **Twitch** | ✅ كامل | ✅ | دردشة عبر اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ كامل | ✅ | اشتراك أحداث WebSocket |
| 🔵 **Zalo** | ✅ كامل | ✅ | Zalo Bot API |

> **الكشف التلقائي:** تقرأ ClawMetry ملف `~/.openclaw/openclaw.json` الخاص بك وتعرض فقط القنوات التي أعددتها فعليًا. لا حاجة لإعداد يدوي.

## النشر عبر Docker

تريد تشغيل ClawMetry في حاوية؟ لا مشكلة! 🐳

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

> **ملاحظة:** عند التشغيل داخل Docker، اربط أدلة بيانات وسجلات وكيلك (مثل `~/.openclaw`، `~/.claude`، `~/.codex`) حتى تتمكن ClawMetry من اكتشاف إعدادك تلقائيًا.

## المتطلبات

- Python 3.8+
- Flask (يُثبَّت تلقائيًا عبر pip)
- بيئة تشغيل وكيل ذكاء اصطناعي على نفس الجهاز: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، أو n8n (أو أحجام مثبَّتة لـ Docker)
- Linux أو macOS

## دعم NemoClaw / OpenShell

تكتشف ClawMetry تلقائيًا [NemoClaw](https://github.com/NVIDIA/NemoClaw) - غلاف الأمان المؤسسي من NVIDIA لـ OpenClaw الذي يشغّل الوكلاء داخل حاويات OpenShell المعزولة.

لا حاجة لإعدادات إضافية في معظم الحالات. يكتشف الخادم الخلفي للمزامنة تلقائيًا ملفات الجلسات سواء كانت موجودة في `~/.openclaw/` على المضيف أو داخل حاوية OpenShell.

### كيف يعمل

تكتشف ClawMetry NemoClaw بطريقتين:

1. **كشف عبر الملف التنفيذي** — يتحقق من وجود أداة سطر الأوامر `nemoclaw` ويشغّل `nemoclaw status` للحصول على معلومات الصندوق المعزول
2. **كشف عبر الحاوية** — يفحص حاويات Docker العاملة بحثًا عن صور `openshell` أو `nemoclaw` أو `ghcr.io/nvidia/`، ثم يقرأ الجلسات عبر أحجام مثبَّتة أو `docker cp`

تُوسَم ملفات الجلسات المُزامَنة من حاويات NemoClaw بـ `runtime=nemoclaw` وبيانات وصفية `container_id` في لوحة التحكم السحابية، بحيث يمكنك تمييزها عن جلسات OpenClaw القياسية بنظرة واحدة.

### الإعداد الموصى به: خادم المزامنة على المضيف

للحصول على أفضل تجربة، شغّل خادم المزامنة الخاص بـ ClawMetry على **الجهاز المضيف** (وليس داخل الصندوق المعزول). هذا يتجنب قيود سياسة شبكة NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سيجد خادم المزامنة تلقائيًا الجلسات داخل أي حاويات OpenShell عاملة.

### اختياري: اسم صندوق معزول صريح

إذا لم يعمل الكشف التلقائي، وجّه ClawMetry إلى الصندوق المعزول الصحيح:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### التشغيل داخل الصندوق المعزول (متقدم)

إذا كان عليك تشغيل خادم المزامنة **داخل** صندوق OpenShell المعزول، أضف قاعدة الخروج هذه إلى سياسة شبكة NemoClaw الخاصة بك حتى يتمكن من الوصول إلى واجهة استيراد ClawMetry:

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
| `ingest.clawmetry.com` | 443 | HTTPS | نعم (خادم المزامنة ← السحابة) |
| `localhost:8900` | 8900 | HTTP | نعم (لوحة التحكم المحلية) |
| مقبس Docker (`/var/run/docker.sock`) | — | مقبس Unix | لاكتشاف جلسات الحاويات |

خادم المزامنة يجري فقط استدعاءات HTTPS صادرة إلى `ingest.clawmetry.com`. لا حاجة لمنافذ واردة.

---

## النشر السحابي

راجع **[دليل اختبار السحابة](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** لأنفاق SSH، الوكيل العكسي، وDocker.

## الاختبار

يُختبَر هذا المشروع باستخدام BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## القياس عن بُعد

ترسل ClawMetry إشعارات مجهولة الهوية لدورة حياة التثبيت إلى
`https://app.clawmetry.com/api/install`: إشعار `install` واحد في المرة
الأولى التي تشغّل فيها أداة سطر الأوامر `clawmetry` على جهاز جديد، وإشعار
`update` واحد عند أول تشغيل بعد الترقية إلى إصدار جديد، وإشعار
`onboarded` واحد عند إكمال خيار الإعداد داخل لوحة التحكم. نستخدم هذا
لعدّ التثبيتات الحقيقية (أرقام تنزيلات PyPI الخام مصدرها حوالي 98% مرايا وCI
وإعادة تنزيلات التحديث التلقائي) ولمعرفة أطر الوكلاء
والإصدارات المستخدمة فعليًا في الواقع.

**بحد أقصى POST واحد لكل حدث دورة حياة لكل إصدار**، يحتوي على:

| الحقل | مثال | السبب |
|---|---|---|
| `install_id` | UUID عشوائي مخزّن في `~/.clawmetry/install_id` | إزالة التكرار؛ مجهول الهوية حتى تربط مزامنة Cloud صراحةً (نبضة قلب الخادم المصادَق عليها تحمل حينها هذا المعرّف، لربط هذا التثبيت بحسابك) |
| `event` | `install` / `update` / `onboarded` | تثبيت جديد مقابل ترقية لتثبيت موجود |
| `version` | `0.12.167` | الإصدارات المستخدمة فعليًا |
| `os` / `os_version` | `Darwin` / `25.3.0` | أولويات دعم المنصات |
| `python` | `3.11.15` | مصفوفة دعم إصدارات Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | الوكلاء التي يجب أن نتكامل معها بعد ذلك |
| `is_ci` / `ci_provider` | `true` / `github_actions` | فصل التثبيتات البشرية عن ضوضاء CI |

**ما لا نرسله**: عنوان IP (تستنتج السحابة رمز الدولة من جانب الخادم
من الطلب، ثم تتخلص من عنوان IP)، اسم المضيف، اسم المستخدم، مسار مساحة
العمل، محتوى الملفات، مفتاح API الخاص بك، بريدك الإلكتروني، أو أي شيء
شخصي أو خاص بمساحة العمل. حمولة البيانات على الشبكة قابلة للتدقيق في
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**إلغاء الاشتراك** (أي واحد من هذه يعطّله بشكل دائم):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

فشل الشبكة هنا لا يمنع أبدًا تشغيل `clawmetry` - الإشعار
يُرسَل دون انتظار على خيط خلفي بمهلة 3 ثوانٍ.

## سجل النجوم

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
  <strong>🦞 شاهد وكيلك وهو يفكّر</strong><br>
  <sub>بُني بواسطة <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · جزء من نظام <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
