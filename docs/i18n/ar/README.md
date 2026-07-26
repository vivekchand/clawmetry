<!-- i18n-src:bab48eec552f -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**شاهد وكيلك وهو يفكّر.** مراقبة فورية لـ **14 بيئة تشغيل لوكلاء الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و10 غيرها. لوحة تحكم واحدة لأسطول الوكلاء بأكمله.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بلا إعداد. يكتشف كل شيء تلقائيًا.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900** وانتهى الأمر.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## يعمل مع 14 بيئة تشغيل للوكلاء

بدأ ClawMetry كأداة مراقبة لـ OpenClaw، والآن يقيس **أسطول الوكلاء بأكمله** في لوحة تحكم واحدة، ويكتشف كل بيئة تشغيل على جهازك تلقائيًا:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents**

كل من OpenClaw وNemoClaw مجانيان في التطبيق مفتوح المصدر؛ أما بيئات التشغيل الأخرى فتُفعَّل مع ClawMetry Cloud أو ترخيص Pro مُستضاف ذاتيًا. بدّل بيئات التشغيل من الرأسية، وكل تبويب — التكلفة، الرموز، الأدوات، التتبعات — يُعاد تحديد نطاقه لتلك البيئة. راجع **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** للتفاصيل الدقيقة لتقسيم المجاني/المدفوع، ومصفوفة المستويات، وشكل `/api/entitlement`، وأداة سطر الأوامر `clawmetry license`.

## ما الذي ستحصل عليه

- **Flow** — رسم بياني متحرك حي يعرض تدفق الرسائل عبر القنوات والدماغ والأدوات والعودة
- **Overview** — فحوصات الصحة، خريطة النشاط الحرارية، عدد الجلسات، معلومات النموذج
- **Usage** — تتبع الرموز والتكلفة مع تفصيل يومي/أسبوعي/شهري
- **Sessions** — جلسات الوكيل النشطة مع النموذج والرموز وآخر نشاط
- **Crons** — المهام المجدولة مع الحالة والتشغيل التالي والمدة
- **Logs** — بث سجلات فوري ملوّن الكود
- **Memory** — تصفّح SOUL.md وMEMORY.md وAGENTS.md والملاحظات اليومية
- **Transcripts** — واجهة فقاعات دردشة لقراءة سجلات الجلسات
- **Alerts** — حدود ميزانية، مشغّلات معدل الأخطاء، اكتشاف انقطاع الوكيل؛ توجَّه إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **Approvals** — يحجب عمليات الحذف المدمّرة، والدفع القسري، وتعديلات قواعد البيانات، وsudo، وتثبيت الحزم، والاتصالات الشبكية خلف موافقة بنقرة واحدة

## لقطات شاشة

### 🧠 Brain — بث أحداث الوكيل الحي
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — استخدام الرموز وملخص الجلسة
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — بث استدعاءات الأدوات في الوقت الفعلي
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفصيل التكلفة حسب النموذج والجلسة
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — متصفح ملفات مساحة العمل
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — الوضع الأمني وسجل التدقيق
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — حدود الميزانية، مشغّلات معدل الأخطاء، ووصلات ويب إلى Slack / Discord / PagerDuty / البريد الإلكتروني
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — احجب استدعاءات الأدوات الخطرة خلف موافقة يدوية؛ قواعد حماية مدعومة بسياسات
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**الحجب قبل التنفيذ لـ Claude Code** — أمر واحد يثبّت
خطاف PreToolUse يوقف استدعاءات الأدوات المطابقة *قبل* تشغيلها وينتظر
قرارك (بنقرة واحدة من هاتفك عند تفعيل
[إشعارات الدفع السحابية](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

الرفض يحجب استدعاء الأداة الواحد فقط، ويحتفظ الوكيل بجلسته ويمكنه
تجربة نهج آخر. الموافقة من هاتفك تتخطى مطالبة الإذن الخاصة بـ Claude Code
نفسها (فأنت أجبت بالفعل). الأدوات غير المطابقة تكلّف نحو 40 مللي ثانية
وتمر إلى تدفق إذن Claude Code العادي. ستحصل أيضًا على إشعار دفع للهاتف
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

تطبيق React الخاص بالإصدار v2 موجود في `frontend/` ويُقدَّم على المسار `/v2`
عند تشغيل خادم Flask مع تفعيل v2.

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

افتح `http://localhost:5173/v2/`. يقوم Vite بتمرير طلبات `/api`
إلى `http://localhost:8900`، لذا يمكن لتطبيق React التحدث إلى خادم Flask
المحلي دون إعداد CORS إضافي.

لبناء الحزمة التي تُشحن مع حزمة Python:

```bash
cd frontend
npm run build
```

تُكتب الحزمة الإنتاجية إلى `clawmetry/static/v2/dist/`.

## توافق بيئات التشغيل / الوكلاء

يراقب ClawMetry العديد من بيئات تشغيل وكلاء الذكاء الاصطناعي، وليس فقط OpenClaw. كل بيئة تشغيل غير OpenClaw تأتي مع محوّل قراءة مخصص يترجم صيغة جلساتها الأصلية إلى أشكال ClawMetry الموحّدة؛ يستوعبها المُشغّل الخلفي في مخزن DuckDB نفسه + اللقطة السحابية، موسومة ببيئة التشغيل، ويعرض تبويب إعادة تشغيل الجلسة **محوّل بيئة تشغيل** عند وجود أكثر من واحدة. راجع [`docs/compatibility.md`](docs/compatibility.md) للمصفوفة الكاملة + دليل إضافة بيئات تشغيل، و[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) لمقدمة عائلة OpenClaw.

| بيئة التشغيل / الوكيل | الحالة | ملاحظات |
|---|---|---|
| **OpenClaw** | أصلي | بيئة التشغيل المرجعية، تُكتشف تلقائيًا |
| **PicoClaw** | محوّل تجريبي | JSONL مسطّح من نوع `providers.Message` (`~/.picoclaw/workspace/sessions`). سجلات، نموذج، استدعاءات أدوات. |
| **NanoClaw** | محوّل تجريبي | SQLite لكل جلسة (`data/v2-sessions`). سجلات + عدد الرسائل. |
| **Hermes** | محوّل تجريبي | SQLite `~/.hermes/state.db`. سجلات، نموذج، رموز/تكلفة. |
| **Claude Code** | محوّل تجريبي | JSONL `~/.claude/projects/.../<id>.jsonl`. سجلات، نموذج، استدعاءات أدوات + تفكير، استخدام الرموز. |
| **Codex** | محوّل تجريبي | Rollout JSONL `~/.codex/sessions/...`. سجلات، نموذج، استدعاءات أدوات، استخدام الرموز. |
| **Cursor** | محوّل تجريبي | SQLite `state.vscdb`. سجلات دردشة/محرر، نموذج. |
| **Aider** | محوّل تجريبي | `.aider.chat.history.md` لكل مشروع. سجلات، نموذج، عدد الرموز. |
| **Goose** | محوّل تجريبي | SQLite `~/.local/share/goose`. سجلات، نموذج، استدعاءات أدوات، إجمالي الرموز. |
| **opencode** | محوّل تجريبي | SQLite `~/.local/share/opencode`. سجلات، نموذج، استدعاءات أدوات، رموز + تكلفة. |
| **Qwen Code** | محوّل تجريبي | JSONL `~/.qwen/projects/.../chats`. سجلات، نموذج، استدعاءات أدوات، استخدام الرموز. |
| **Pi** | محوّل تجريبي | JSONL `~/.pi/agent/sessions`. سجلات، نموذج، استدعاءات أدوات، رموز + تكلفة. |
| **Deep Agents** | محوّل تجريبي | SQLite `~/.deepagents/.state/sessions.db`. سجلات، نموذج، استدعاءات أدوات، رموز + تكلفة. |

"محوّل تجريبي" يعني أن ClawMetry يشحن قارئًا للصيغة الفعلية على القرص لبيئة التشغيل تلك، كل منها مبني ومُتحقق منه مقابل تثبيت حقيقي على جهاز حقيقي (راجع `tests/fixtures/runtimes/<rt>/`). المحوّلات للقراءة فقط؛ وكل منها صريح بشأن ما تخزّنه بيئة التشغيل فعليًا (مثلًا PicoClaw/NanoClaw/Cursor لا تكتب تكلفة الرموز على القرص). عند تشغيل عدة بيئات تشغيل على عقدة واحدة، يحدد محوّل بيئة التشغيل نطاق عرض الجلسات لواحدة منها من أجل استكشاف عميق ونظيف.

## تتبّع أي وكيل SDK — إسناد التكلفة خارج الحلقة

بيئات التشغيل أعلاه جميعها تكتب الجلسات على القرص. أما **وكيلك الإنتاجي** الخاص بك — الذي بنيته على OpenAI Agents SDK، أو LangChain، أو Vercel AI SDK، أو LlamaIndex، أو E2B، أو حلقة `httpx` عادية — فلا يفعل ذلك. لا يزال معترض ClawMetry بلا إعداد يلتقط استدعاءات LLM الخاصة به (التكلفة، الرموز، زمن الاستجابة، الأخطاء) عبر تصحيح `httpx`/`requests` أثناء التشغيل:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (أو متغيّر البيئة `CLAWMETRY_SOURCE=support-agent`) يسم كل استدعاء بـ**مصدر مُسمّى**، بحيث يظهر كل منتج تشغّله كسطر مستقل قابل لإسناد التكلفة في بطاقة **🔌 المصادر خارج الحلقة** بلوحة التحكم في تبويب Overview — الاستدعاءات، المزوّدون، زمن الاستجابة، معدل الأخطاء لكل وكيل. لم تحدد مصدرًا؟ لا تزال الاستدعاءات تُتتبّع؛ فقط تبقى البطاقة مخفية.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

هذه هي طبقة البيانات نفسها التي تغذّيها محوّلات بيئة التشغيل (DuckDB ← اللقطة السحابية)، لذا تتزامن المصادر خارج الحلقة مع لوحة التحكم السحابية مثل كل شيء آخر، مشفّرة من طرف إلى طرف.

## OpenTelemetry — محايد تجاه المزوّد، أرسل تتبعاتك إلى أي مكان

يتحدث ClawMetry **OpenTelemetry** في كلا الاتجاهين، باستخدام **اتفاقيات GenAI الدلالية**، بحيث لا تُحبس تتبعات وكيلك أبدًا داخل أداة واحدة.

**التصدير** لكل جلسة — استدعاءات LLM، الأدوات، الوكلاء الفرعيون، الرموز، التكلفة — كامتدادات GenAI عبر OTLP/HTTP إلى أي مُجمِّع (Datadog، Grafana، Honeycomb، أو مُجمِّع OTel الخاص بك):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

رؤوس المصادقة وفاصل الاستطلاع اختياريان كمتغيّرات بيئة:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**الاستيعاب** — يقبل مستقبل OTLP المدمج التتبعات والمقاييس من أي مكان آخر على `/v1/traces` و`/v1/metrics` (`pip install clawmetry[otel]` لاستيعاب protobuf).

تحصل على لوحة تحكم ClawMetry بلا إعداد ومحلية الأولوية **وعلى** بياناتك في أي خلفية يشغّلها فريقك بالفعل، بلا قيود، وبلا وكيل ثانٍ للتثبيت.

## الإعداد

معظم الناس لا يحتاجون إلى أي إعداد. يكتشف ClawMetry مساحة عملك وسجلاتك وجلساتك ومهامك المجدولة تلقائيًا.

إذا احتجت إلى التخصيص:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

كل الخيارات: `clawmetry --help`

## القنوات المدعومة

يعرض ClawMetry النشاط الحي لكل قناة OpenClaw مُعدّة لديك. فقط القنوات المُعدّة فعليًا في ملف `openclaw.json` الخاص بك تظهر في رسم Flow البياني؛ أما غير المُعدّة فتُخفى تلقائيًا.

انقر على أي عقدة قناة في Flow لرؤية عرض فقاعات دردشة حي مع عدد الرسائل الواردة/الصادرة.

| القناة | الحالة | نافذة حية منبثقة | ملاحظات |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ كامل | ✅ | رسائل، إحصاءات، تحديث كل 10 ثوانٍ |
| 💬 **iMessage** | ✅ كامل | ✅ | يقرأ `~/Library/Messages/chat.db` مباشرة |
| 💚 **WhatsApp** | ✅ كامل | ✅ | عبر WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ كامل | ✅ | عبر signal-cli |
| 🟣 **Discord** | ✅ كامل | ✅ | اكتشاف الخادم + القناة |
| 🟪 **Slack** | ✅ كامل | ✅ | اكتشاف مساحة العمل + القناة |
| 🌐 **Webchat** | ✅ كامل | ✅ | جلسات واجهة الويب المدمجة |
| 📡 **IRC** | ✅ كامل | ✅ | واجهة فقاعات بطراز الطرفية |
| 🍏 **BlueBubbles** | ✅ كامل | ✅ | iMessage عبر واجهة BlueBubbles REST |
| 🔵 **Google Chat** | ✅ كامل | ✅ | عبر وصلات ويب Chat API |
| 🟣 **MS Teams** | ✅ كامل | ✅ | عبر إضافة Teams bot |
| 🔷 **Mattermost** | ✅ كامل | ✅ | دردشة فريق مُستضافة ذاتيًا |
| 🟩 **Matrix** | ✅ كامل | ✅ | لامركزية، دعم E2EE |
| 🟢 **LINE** | ✅ كامل | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ كامل | ✅ | رسائل مباشرة لامركزية NIP-04 |
| 🟣 **Twitch** | ✅ كامل | ✅ | دردشة عبر اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ كامل | ✅ | اشتراك أحداث WebSocket |
| 🔵 **Zalo** | ✅ كامل | ✅ | Zalo Bot API |

> **الاكتشاف التلقائي:** يقرأ ClawMetry ملف `~/.openclaw/openclaw.json` الخاص بك ويعرض فقط القنوات التي أعددتها فعليًا. لا حاجة لأي إعداد يدوي.

## النشر عبر Docker

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

> **ملاحظة:** عند التشغيل داخل Docker، اربط أدلة بيانات وسجلات وكيلك (مثل `~/.openclaw`، `~/.claude`، `~/.codex`) حتى يتمكن ClawMetry من اكتشاف إعدادك تلقائيًا.

## المتطلبات

- Python 3.8+
- Flask (يُثبَّت تلقائيًا عبر pip)
- بيئة تشغيل وكيل ذكاء اصطناعي على الجهاز نفسه: OpenClaw، أو NVIDIA NemoClaw، أو Claude Code، أو Codex، أو Cursor، أو Goose، أو Hermes، أو opencode، أو Qwen Code، أو Aider، أو NanoClaw، أو PicoClaw، أو Pi، أو Deep Agents (أو مجلدات مُركَّبة لـ Docker)
- Linux أو macOS

## دعم NemoClaw / OpenShell

يكتشف ClawMetry تلقائيًا [NemoClaw](https://github.com/NVIDIA/NemoClaw)، غلاف الأمان المؤسسي من NVIDIA لـ OpenClaw الذي يشغّل الوكلاء داخل حاويات OpenShell المعزولة.

لا حاجة لإعداد إضافي في معظم الحالات. يكتشف المُشغّل الخلفي للمزامنة ملفات الجلسات تلقائيًا سواء كانت موجودة في `~/.openclaw/` على المضيف أو داخل حاوية OpenShell.

### كيف يعمل

يكتشف ClawMetry NemoClaw بطريقتين:

1. **اكتشاف ثنائي** — يتحقق من وجود أداة سطر أوامر `nemoclaw` ويشغّل `nemoclaw status` للحصول على معلومات الصندوق المعزول
2. **اكتشاف الحاوية** — يفحص حاويات Docker العاملة بحثًا عن صور `openshell` أو `nemoclaw` أو `ghcr.io/nvidia/`، ثم يقرأ الجلسات عبر مجلدات مُركَّبة أو `docker cp`

تُوسم ملفات الجلسات المُزامنة من حاويات NemoClaw بـ `runtime=nemoclaw` وبيانات وصفية `container_id` في لوحة التحكم السحابية، حتى تتمكن من تمييزها عن جلسات OpenClaw القياسية بنظرة سريعة.

### الإعداد المُوصى به: مُشغّل المزامنة على المضيف

لأفضل تجربة، شغّل مُشغّل المزامنة الخلفي الخاص بـ ClawMetry على **الجهاز المضيف** (وليس داخل الصندوق المعزول). هذا يتجنب قيود سياسة شبكة NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سيجد مُشغّل المزامنة الجلسات تلقائيًا داخل أي حاويات OpenShell عاملة.

### اختياري: اسم صندوق معزول صريح

إذا لم يعمل الاكتشاف التلقائي، وجّه ClawMetry إلى الصندوق المعزول الصحيح:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### التشغيل داخل الصندوق المعزول (متقدم)

إذا اضطررت لتشغيل مُشغّل المزامنة **داخل** صندوق OpenShell المعزول، أضف قاعدة الخروج هذه إلى سياسة شبكة NemoClaw حتى يتمكن من الوصول إلى واجهة استيعاب ClawMetry:

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
| `ingest.clawmetry.com` | 443 | HTTPS | نعم (مُشغّل المزامنة ← السحابة) |
| `localhost:8900` | 8900 | HTTP | نعم (واجهة لوحة التحكم المحلية) |
| مقبس Docker (`/var/run/docker.sock`) | — | مقبس Unix | لاكتشاف جلسات الحاوية |

يقوم مُشغّل المزامنة فقط بإجراء استدعاءات HTTPS صادرة إلى `ingest.clawmetry.com`. لا حاجة إلى أي منافذ واردة.

---

## النشر السحابي

راجع **[دليل الاختبار السحابي](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** لأنفاق SSH، والوكيل العكسي، وDocker.

## الاختبار

يُختبر هذا المشروع باستخدام BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## القياس عن بُعد

يرسل ClawMetry نبضة "تشغيل أول" واحدة مجهولة الهوية إلى
`https://app.clawmetry.com/api/install` عند أول تشغيل لأمر
`clawmetry` على جهاز جديد. نستخدم هذا لإحصاء التثبيتات (المقياس
التسويقي الوحيد الذي لدينا لمشروع مفتوح المصدر) ولمعرفة أطر عمل
الوكلاء التي ثبّتها مستخدمونا.

**طلب POST واحد بالضبط لكل تثبيت**، يحتوي على:

| الحقل | مثال | السبب |
|---|---|---|
| `install_id` | UUID عشوائي مخزّن في `~/.clawmetry/install_id` | إزالة التكرار؛ غير مرتبط ببريدك الإلكتروني أو مفتاح API |
| `version` | `0.12.167` | معرفة الإصدارات المنتشرة |
| `os` / `os_version` | `Darwin` / `25.3.0` | أولويات دعم المنصات |
| `python` | `3.11.15` | مصفوفة دعم إصدارات Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | مع أي وكلاء ينبغي أن نتكامل بعد ذلك |
| `is_ci` / `ci_provider` | `true` / `github_actions` | فصل تثبيتات البشر عن ضوضاء CI |

**ما لا نرسله**: عنوان IP (تشتق السحابة رمز البلد من جانب الخادم
من الطلب، ثم تتجاهل عنوان IP)، اسم المضيف، اسم المستخدم، مسار مساحة
العمل، محتويات الملفات، مفتاح API الخاص بك، بريدك الإلكتروني، أي معلومات
شخصية أو خاصة بمساحة العمل. الحمولة السلكية قابلة للتدقيق في
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**إلغاء الاشتراك** (أي واحد من هذه يُعطّله بشكل دائم):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

فشل الشبكة هنا لا يمنع أبدًا `clawmetry` من العمل؛ فالنبضة
مُرسلة دون انتظار على خيط مستقل بمهلة 3 ثوانٍ.

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
  <sub>بُني بواسطة <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · جزء من منظومة <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
