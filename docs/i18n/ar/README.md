<!-- i18n-src:8f42d460a973 -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**شاهد وكيلك وهو يفكر.** مراقبة فورية لـ **14 بيئة تشغيل لوكلاء الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و10 أخرى. لوحة تحكم واحدة لأسطول وكلائك بالكامل.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بلا إعداد. يكتشف كل شيء تلقائياً.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900** وانتهى الأمر.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## يعمل مع 14 بيئة تشغيل للوكلاء

بدأ ClawMetry كأداة مراقبة لـ OpenClaw، والآن يقيس **أسطول وكلائك بالكامل** في لوحة تحكم واحدة، مع اكتشاف تلقائي لكل بيئة تشغيل على جهازك:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

بيئتا OpenClaw وNemoClaw مجانيتان في التطبيق مفتوح المصدر؛ أما بيئات التشغيل الأخرى فتُفعَّل عبر ClawMetry Cloud أو ترخيص Pro ذاتي الاستضافة. بدّل بيئات التشغيل من الرأسية وستُعاد تهيئة كل تبويب - التكلفة، الرموز (tokens)، الأدوات، التتبعات - ليتوافق مع تلك البيئة. راجع **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** للتفاصيل الدقيقة حول التقسيم المجاني/المدفوع، ومصفوفة المستويات، وشكل `/api/entitlement`، وأداة سطر الأوامر `clawmetry license`.

## ما الذي ستحصل عليه

- **التدفق (Flow)** - رسم متحرك حي يُظهر الرسائل وهي تتدفق عبر القنوات، والدماغ، والأدوات، ثم العودة
- **نظرة عامة (Overview)** - فحوصات الصحة، خريطة حرارية للنشاط، عدد الجلسات، معلومات النموذج
- **الاستخدام (Usage)** - تتبع الرموز (tokens) والتكلفة مع تفصيل يومي/أسبوعي/شهري
- **الجلسات (Sessions)** - جلسات الوكيل النشطة مع النموذج، والرموز، وآخر نشاط
- **المهام المجدولة (Crons)** - المهام المجدولة مع الحالة، والتشغيل التالي، والمدة
- **السجلات (Logs)** - بث سجلات فوري مُلوَّن
- **الذاكرة (Memory)** - تصفح SOUL.md وMEMORY.md وAGENTS.md والملاحظات اليومية
- **النصوص (Transcripts)** - واجهة فقاعات محادثة لقراءة سجلات الجلسات
- **التنبيهات (Alerts)** - حدود الميزانية، محفزات معدل الأخطاء، كشف انقطاع الوكيل؛ يوجّه إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **الموافقات (Approvals)** - حجب عمليات الحذف المدمرة، والدفع القسري (force pushes)، وتعديلات قواعد البيانات، وsudo، وتثبيت الحزم، والاتصالات الشبكية خلف موافقة بضغطة واحدة

## لقطات شاشة

### 🧠 الدماغ (Brain) - بث أحداث الوكيل الحي
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 نظرة عامة (Overview) - استخدام الرموز وملخص الجلسة
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ التدفق (Flow) - تغذية استدعاءات الأدوات الفورية
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 الرموز (Tokens) - تفصيل التكلفة حسب النموذج والجلسة
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 الذاكرة (Memory) - متصفح ملفات مساحة العمل
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 الأمان (Security) - الوضعية الأمنية وسجل التدقيق
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 التنبيهات (Alerts) - حدود الميزانية، محفزات معدل الأخطاء، ووِبهوكس إلى Slack / Discord / PagerDuty / البريد الإلكتروني
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ الموافقات (Approvals) - حجب استدعاءات الأدوات الخطرة خلف موافقة يدوية؛ قواعد حماية مدعومة بسياسات
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

## تطوير الواجهة الأمامية v2

يعيش تطبيق React الخاص بالإصدار v2 في `frontend/` ويُقدَّم على المسار `/v2` عند
تشغيل خادم Flask مع تفعيل v2.

استخدم طرفيتين (terminals) أثناء التطوير:

```bash
# الطرفية 1: خادم Flask API على المنفذ :8900
CLAWMETRY_V2=1 python3 dashboard.py
```

```bash
# الطرفية 2: خادم Vite للتطوير على المنفذ :5173
cd frontend
nvm use
npm ci
npm run dev
```

افتح `http://localhost:5173/v2/`. يمرر Vite طلبات `/api` عبر بروكسي إلى
`http://localhost:8900`، بحيث يمكن لتطبيق React التواصل مع خادم Flask المحلي
دون إعداد CORS إضافي.

لبناء الحزمة (bundle) التي تُشحن مع حزمة Python:

```bash
cd frontend
npm run build
```

تُكتب حزمة الإنتاج إلى `clawmetry/static/v2/dist/`.

## توافق بيئات التشغيل / الوكلاء

يراقب ClawMetry العديد من بيئات تشغيل وكلاء الذكاء الاصطناعي، وليس OpenClaw فقط. تشحن كل بيئة تشغيل غير OpenClaw مع مهايئ قراءة (reader adapter) مخصص يترجم صيغة الجلسة الأصلية الخاصة بها إلى أشكال ClawMetry الموحدة؛ ويستوعبها الشيطان (daemon) في نفس مخزن DuckDB + لقطة السحابة (cloud snapshot)، موسومة ببيئة التشغيل، ويعرض تبويب إعادة تشغيل الجلسة **مبدّل بيئة تشغيل** عند وجود أكثر من واحدة. راجع [`docs/compatibility.md`](docs/compatibility.md) للاطلاع على المصفوفة الكاملة + دليل لإضافة بيئات تشغيل، و[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) لمقدمة عن عائلة OpenClaw.

| بيئة التشغيل / الوكيل | الحالة | ملاحظات |
|---|---|---|
| **OpenClaw** | أصلية | بيئة التشغيل المرجعية، تُكتشف تلقائياً |
| **PicoClaw** | مهايئ تجريبي (Beta) | JSONL مسطح بصيغة `providers.Message‏` (`~/.picoclaw/workspace/sessions`). النصوص، النموذج، استدعاءات الأدوات. |
| **NanoClaw** | مهايئ تجريبي (Beta) | SQLite لكل جلسة (`data/v2-sessions`). النصوص + عدد الرسائل. |
| **Hermes** | مهايئ تجريبي (Beta) | SQLite ‏`~/.hermes/state.db`. النصوص، النموذج، الرموز/التكلفة. |
| **Claude Code** | مهايئ تجريبي (Beta) | JSONL ‏`~/.claude/projects/.../<id>.jsonl`. النصوص، النموذج، استدعاءات الأدوات + التفكير، استخدام الرموز. |
| **Codex** | مهايئ تجريبي (Beta) | JSONL للتشغيل (Rollout) ‏`~/.codex/sessions/...`. النصوص، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Cursor** | مهايئ تجريبي (Beta) | SQLite ‏`state.vscdb`. نصوص الدردشة/المُركِّب (composer)، النموذج. |
| **Aider** | مهايئ تجريبي (Beta) | ملف `.aider.chat.history.md` لكل مشروع. النصوص، النموذج، عدد الرموز. |
| **Goose** | مهايئ تجريبي (Beta) | SQLite ‏`~/.local/share/goose`. النصوص، النموذج، استدعاءات الأدوات، إجمالي الرموز. |
| **opencode** | مهايئ تجريبي (Beta) | SQLite ‏`~/.local/share/opencode`. النصوص، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Qwen Code** | مهايئ تجريبي (Beta) | JSONL ‏`~/.qwen/projects/.../chats`. النصوص، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Pi** | مهايئ تجريبي (Beta) | JSONL ‏`~/.pi/agent/sessions`. النصوص، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Deep Agents** | مهايئ تجريبي (Beta) | SQLite ‏`~/.deepagents/.state/sessions.db`. النصوص، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |

"مهايئ تجريبي (Beta adapter)" تعني أن ClawMetry يشحن قارئاً لصيغة بيئة التشغيل الفعلية على القرص، مبنياً ومُتحقَّقاً منه مقابل تثبيت حقيقي على جهاز حقيقي (راجع `tests/fixtures/runtimes/<rt>/`). المهايئات للقراءة فقط؛ وكل واحدة منها صريحة بشأن ما تخزّنه بيئة التشغيل فعلياً (مثلاً PicoClaw/NanoClaw/Cursor لا تكتب تكلفة الرموز على القرص). عند تشغيل عدة بيئات تشغيل على عقدة واحدة، يقوم مبدّل بيئة التشغيل بحصر عرض الجلسات على واحدة للتعمق النظيف.

## تتبّع أي وكيل SDK - إسناد التكلفة خارج الحلقة (out-loop)

بيئات التشغيل أعلاه جميعها تكتب الجلسات إلى القرص. أما **وكيلك الإنتاجي** الخاص بك - ذلك الذي بنيته على OpenAI Agents SDK، أو LangChain، أو Vercel AI SDK، أو LlamaIndex، أو E2B، أو حلقة `httpx` بسيطة - فلا يفعل ذلك. لا يزال معترض ClawMetry بلا إعداد يلتقط استدعاءات LLM الخاصة به (التكلفة، الرموز، زمن الاستجابة، الأخطاء) عبر تصحيح `httpx`/`requests` بشكل ديناميكي (monkey-patching):

```python
import clawmetry.track            # تفعيل المعترض
clawmetry.track.set_source("support-agent")   # تسمية هذا المنتج

# ...يعمل وكيلك بشكل طبيعي؛ كل استدعاء LLM يُتتبَّع ويُسنَد الآن.
```

تُسمي `set_source()` (أو متغير البيئة `CLAWMETRY_SOURCE=support-agent`) كل استدعاء بـ**مصدر مُسمّى**، بحيث يظهر كل منتج تشغّله كخط مستقل قابل لإسناد التكلفة من الدرجة الأولى في بطاقة **🔌 المصادر خارج الحلقة (Out-loop sources)** الخاصة بلوحة التحكم في تبويب نظرة عامة - الاستدعاءات، والمزودون، وزمن الاستجابة، ومعدل الأخطاء لكل وكيل. لم تُحدّد مصدراً؟ لا تزال الاستدعاءات مُتتبَّعة؛ تبقى البطاقة مخفية فقط.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

هذه هي طبقة البيانات نفسها التي تغذيها مهايئات بيئة التشغيل (DuckDB ← لقطة السحابة)، لذا تتزامن المصادر خارج الحلقة مع لوحة تحكم السحابة تماماً كأي شيء آخر، مع تشفير من طرف إلى طرف (E2E).

## OpenTelemetry - محايد تجاه المزود، أرسل تتبعاتك إلى أي مكان

يتحدث ClawMetry بلغة **OpenTelemetry** في كلا الاتجاهين، مستخدماً **اصطلاحات GenAI الدلالية**، بحيث لا تُحبس تتبعات وكيلك أبداً داخل أداة واحدة.

**التصدير** لكل جلسة - استدعاءات LLM، الأدوات، الوكلاء الفرعيون، الرموز، التكلفة - كتتبعات OTLP/HTTP GenAI إلى أي مُجمِّع (Datadog، أو Grafana، أو Honeycomb، أو مُجمِّع OTel الخاص بك):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# بشكل مكافئ:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

رؤوس المصادقة وفترة الاستطلاع هي متغيرات بيئة اختيارية:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # رؤوس HTTP إضافية
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # ثوانٍ (الافتراضي 60)
```

**الاستيعاب (Ingest)** - يقبل مستقبل OTLP المدمج التتبعات والمقاييس من أي مصدر آخر على `/v1/traces` و`/v1/metrics` (`pip install clawmetry[otel]` لاستيعاب protobuf).

تحصل على لوحة تحكم ClawMetry بلا إعداد ومحلية أولاً **و**بياناتك في أي خلفية يستخدمها فريقك بالفعل - بلا حبس (lock-in)، وبلا وكيل ثانٍ يجب تثبيته.

## الإعداد

معظم الناس لا يحتاجون إلى أي إعداد. يكتشف ClawMetry تلقائياً مساحة عملك، وسجلاتك، وجلساتك، ومهامك المجدولة.

إذا احتجت إلى التخصيص:

```bash
clawmetry --port 9000              # منفذ مخصص (الافتراضي: 8900)
clawmetry --host 127.0.0.1         # الربط بالمضيف المحلي فقط
clawmetry --workspace ~/mybot      # مسار مساحة عمل مخصص
clawmetry --name "Alice"           # اسمك في رسم التدفق (Flow)
```

جميع الخيارات: `clawmetry --help`

## القنوات المدعومة

يعرض ClawMetry النشاط الحي لكل قناة OpenClaw مُعدَّة لديك. تظهر في رسم التدفق فقط القنوات المُعدَّة فعلياً في ملف `openclaw.json` الخاص بك - أما غير المُعدَّة فتُخفى تلقائياً.

انقر على أي عقدة قناة في التدفق لرؤية عرض فقاعات محادثة حي مع عدد الرسائل الواردة/الصادرة.

| القناة | الحالة | نافذة منبثقة حية | ملاحظات |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ كاملة | ✅ | الرسائل، الإحصائيات، تحديث كل 10 ثوانٍ |
| 💬 **iMessage** | ✅ كاملة | ✅ | يقرأ `~/Library/Messages/chat.db` مباشرة |
| 💚 **WhatsApp** | ✅ كاملة | ✅ | عبر WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ كاملة | ✅ | عبر signal-cli |
| 🟣 **Discord** | ✅ كاملة | ✅ | اكتشاف السيرفر (Guild) والقناة |
| 🟪 **Slack** | ✅ كاملة | ✅ | اكتشاف مساحة العمل والقناة |
| 🌐 **Webchat** | ✅ كاملة | ✅ | جلسات واجهة الويب المدمجة |
| 📡 **IRC** | ✅ كاملة | ✅ | واجهة فقاعات بأسلوب الطرفية |
| 🍏 **BlueBubbles** | ✅ كاملة | ✅ | iMessage عبر واجهة BlueBubbles REST API |
| 🔵 **Google Chat** | ✅ كاملة | ✅ | عبر وِبهوكس Chat API |
| 🟣 **MS Teams** | ✅ كاملة | ✅ | عبر إضافة بوت Teams |
| 🔷 **Mattermost** | ✅ كاملة | ✅ | دردشة فريق ذاتية الاستضافة |
| 🟩 **Matrix** | ✅ كاملة | ✅ | لامركزية، دعم E2EE |
| 🟢 **LINE** | ✅ كاملة | ✅ | واجهة LINE Messaging API |
| ⚡ **Nostr** | ✅ كاملة | ✅ | رسائل مباشرة لامركزية NIP-04 |
| 🟣 **Twitch** | ✅ كاملة | ✅ | دردشة عبر اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ كاملة | ✅ | اشتراك أحداث WebSocket |
| 🔵 **Zalo** | ✅ كاملة | ✅ | واجهة Zalo Bot API |

> **الاكتشاف التلقائي:** يقرأ ClawMetry ملف `~/.openclaw/openclaw.json` الخاص بك ولا يعرض سوى القنوات التي أعددتها فعلياً. لا حاجة لإعداد يدوي.

## نشر Docker

تريد تشغيل ClawMetry داخل حاوية؟ لا مشكلة! 🐳

**بداية سريعة مع Docker:**

```bash
# بناء الصورة
docker build -t clawmetry .

# التشغيل بالإعدادات الافتراضية
docker run -p 8900:8900 clawmetry

# أو تركيب مجلد بيانات وكيلك (مُوضَّح: مجلد OpenClaw ‏~/.openclaw)
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

> **ملاحظة:** عند التشغيل داخل Docker، ركّب مجلدات بيانات + سجلات وكيلك (مثل `~/.openclaw`، `~/.claude`، `~/.codex`) حتى يتمكن ClawMetry من اكتشاف إعدادك تلقائياً.

## المتطلبات

- Python 3.8+
- Flask (يُثبَّت تلقائياً عبر pip)
- بيئة تشغيل وكيل ذكاء اصطناعي على نفس الجهاز: OpenClaw، أو NVIDIA NemoClaw، أو Claude Code، أو Codex، أو Cursor، أو Goose، أو Hermes، أو opencode، أو Qwen Code، أو Aider، أو NanoClaw، أو PicoClaw، أو Pi، أو Deep Agents (أو أحجام تخزين مُركَّبة (mounted volumes) لـDocker)
- Linux أو macOS

## دعم NemoClaw / OpenShell

يكتشف ClawMetry تلقائياً [NemoClaw](https://github.com/NVIDIA/NemoClaw) - غلاف الأمان المؤسسي من NVIDIA لـOpenClaw الذي يُشغِّل الوكلاء داخل حاويات OpenShell المعزولة (sandboxed).

لا حاجة إلى إعداد إضافي في معظم الحالات. يكتشف شيطان المزامنة (sync daemon) تلقائياً ملفات الجلسات سواء كانت موجودة في `~/.openclaw/` على المضيف أو داخل حاوية OpenShell.

### كيف يعمل

يكتشف ClawMetry NemoClaw بطريقتين:

1. **اكتشاف ثنائي (Binary detection)** - يتحقق من وجود واجهة سطر الأوامر `nemoclaw` ويشغّل `nemoclaw status` للحصول على معلومات الصندوق الرملي (sandbox)
2. **اكتشاف الحاوية** - يفحص حاويات Docker قيد التشغيل بحثاً عن صور `openshell`، أو `nemoclaw`، أو `ghcr.io/nvidia/`، ثم يقرأ الجلسات عبر أحجام تخزين مُركَّبة أو `docker cp`

تُوسَم ملفات الجلسات المُزامَنة من حاويات NemoClaw بـ `runtime=nemoclaw` وبيانات وصفية `container_id` في لوحة تحكم السحابة، حتى تتمكن من تمييزها عن جلسات OpenClaw القياسية بنظرة سريعة.

### الإعداد الموصى به: شيطان المزامنة على المضيف

للحصول على أفضل تجربة، شغّل شيطان المزامنة الخاص بـClawMetry على **الجهاز المضيف** (وليس داخل الصندوق الرملي). هذا يتجنب قيود سياسة شبكة NemoClaw.

```bash
# على المضيف (خارج الصندوق الرملي)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سيجد شيطان المزامنة تلقائياً الجلسات داخل أي حاويات OpenShell قيد التشغيل.

### اختياري: اسم صندوق رملي صريح

إذا لم يعمل الاكتشاف التلقائي، وجّه ClawMetry إلى الصندوق الرملي الصحيح:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### التشغيل داخل الصندوق الرملي (متقدم)

إذا اضطررت إلى تشغيل شيطان المزامنة **داخل** الصندوق الرملي OpenShell، أضف قاعدة الخروج (egress) هذه إلى سياسة شبكة NemoClaw حتى يتمكن من الوصول إلى واجهة استيعاب ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

طبّق بالأمر:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### المنافذ والنقاط الطرفية

| النقطة الطرفية | المنفذ | البروتوكول | مطلوب |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | نعم (شيطان المزامنة ← السحابة) |
| `localhost:8900` | 8900 | HTTP | نعم (واجهة لوحة التحكم المحلية) |
| مقبس Docker (`/var/run/docker.sock`) | — | مقبس Unix | لاكتشاف جلسات الحاوية |

يقوم شيطان المزامنة بإجراء استدعاءات HTTPS صادرة فقط إلى `ingest.clawmetry.com`. لا حاجة لأي منافذ واردة.

---

## النشر على السحابة

راجع **[دليل اختبار السحابة](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** لأنفاق SSH، والبروكسي العكسي، وDocker.

## الاختبار

هذا المشروع مُختبَر باستخدام BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## القياس عن بُعد (Telemetry)

يرسل ClawMetry نبضة "تشغيل أول" مجهولة واحدة إلى
`https://app.clawmetry.com/api/install` في المرة الأولى التي تُشغِّل فيها واجهة سطر الأوامر
`clawmetry` على جهاز جديد. نستخدم هذا لإحصاء عمليات التثبيت (المقياس التسويقي
الوحيد الذي نملكه لمشروع مفتوح المصدر) ولمعرفة أطر عمل الوكلاء التي ثبّتها مستخدمونا.

**طلب POST واحد بالضبط لكل تثبيت**، يحتوي على:

| الحقل | مثال | السبب |
|---|---|---|
| `install_id` | UUID عشوائي مُخزَّن في `~/.clawmetry/install_id` | لمنع التكرار؛ غير مرتبط ببريدك الإلكتروني أو مفتاح API |
| `version` | `0.12.167` | ما هي الإصدارات المنتشرة |
| `os` / `os_version` | `Darwin` / `25.3.0` | أولويات دعم المنصات |
| `python` | `3.11.15` | مصفوفة دعم إصدارات Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | ما هي الوكلاء التي يجب أن نتكامل معها لاحقاً |
| `is_ci` / `ci_provider` | `true` / `github_actions` | فصل عمليات التثبيت البشرية عن ضوضاء CI |

**ما لا نرسله**: عنوان IP (تشتق السحابة رمز البلد من جانب الخادم من الطلب، ثم تتخلص من عنوان IP)، اسم المضيف، اسم المستخدم، مسار مساحة العمل، محتويات الملفات، مفتاح API الخاص بك، بريدك الإلكتروني، أو أي شيء يتعلق بالهوية الشخصية أو خاص بمساحة العمل. حمولة النقل قابلة للتدقيق في
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**إلغاء الاشتراك** (أي واحد من هذه يعطّله بشكل دائم):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # لكل جلسة طرفية
export DO_NOT_TRACK=1                          # معيار W3C المشترك بين الأدوات
touch ~/.clawmetry/notelemetry                 # علامة ملف دائمة
```

فشل الشبكة هنا لا يمنع أبداً تشغيل `clawmetry` - فالنبضة تُرسَل وتُنسى (fire-and-forget)
على خيط (thread) شيطاني بمهلة 3 ثوانٍ.

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
