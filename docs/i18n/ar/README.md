<!-- i18n-src:9a05336fbdc1 -->
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

أمر واحد. بدون إعدادات. يكتشف كل شيء تلقائيًا.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900** وانتهى الأمر.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## يعمل مع 14 بيئة تشغيل وكيل

بدأت ClawMetry كأداة مراقبة لـ OpenClaw، والآن تقيس **أسطول وكلائك بالكامل** في لوحة تحكم واحدة، وتكتشف كل بيئة تشغيل على جهازك تلقائيًا:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n**

OpenClaw وNemoClaw مجانيان في التطبيق مفتوح المصدر؛ بينما تُفعَّل بقية بيئات التشغيل عبر ClawMetry Cloud أو ترخيص Pro مستضاف ذاتيًا. بدّل بيئات التشغيل من الترويسة، وستُعاد كل علامة تبويب — التكلفة، الرموز (tokens)، الأدوات، التتبعات — إلى نطاق تلك البيئة. راجع **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** للاطلاع على التقسيم الدقيق بين المجاني والمدفوع، ومصفوفة الفئات، وشكل `/api/entitlement`، وأداة سطر الأوامر `clawmetry license`.

## ماذا ستحصل عليه

- **التدفق (Flow)** — رسم بياني متحرك حي يوضح تدفق الرسائل عبر القنوات والدماغ والأدوات وعودتها
- **نظرة عامة (Overview)** — فحوصات الصحة، خريطة حرارية للنشاط، عدد الجلسات، معلومات النموذج
- **الاستخدام (Usage)** — تتبع الرموز والتكلفة مع تفصيل يومي/أسبوعي/شهري
- **الجلسات (Sessions)** — جلسات الوكيل النشطة مع النموذج والرموز وآخر نشاط
- **المهام المجدولة (Crons)** — المهام المجدولة مع الحالة، والتشغيل التالي، والمدة
- **السجلات (Logs)** — بث سجلات فوري بترميز لوني
- **الذاكرة (Memory)** — تصفح SOUL.md وMEMORY.md وAGENTS.md والملاحظات اليومية
- **النصوص الكاملة (Transcripts)** — واجهة فقاعات محادثة لقراءة سجلات الجلسات
- **التنبيهات (Alerts)** — سقوف الميزانية، محفزات معدل الأخطاء، اكتشاف عدم اتصال الوكيل؛ تُوجَّه إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **الموافقات (Approvals)** — حجب عمليات الحذف المدمرة، والدفع القسري (force push)، وتعديلات قواعد البيانات، وsudo، وتثبيت الحزم، والاتصالات الشبكية خلف موافقة بنقرة واحدة

## لقطات الشاشة

### 🧠 الدماغ (Brain) — بث حي لأحداث الوكيل
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 نظرة عامة (Overview) — استخدام الرموز وملخص الجلسات
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ التدفق (Flow) — تغذية استدعاءات الأدوات الفورية
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 الرموز (Tokens) — تفصيل التكلفة حسب النموذج والجلسة
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 الذاكرة (Memory) — متصفح ملفات مساحة العمل
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 الأمان (Security) — الوضعية الأمنية وسجل التدقيق
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 التنبيهات (Alerts) — سقوف الميزانية، محفزات معدل الأخطاء، ووصلات ويب إلى Slack / Discord / PagerDuty / البريد الإلكتروني
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ الموافقات (Approvals) — حجب استدعاءات الأدوات الخطيرة خلف موافقة يدوية؛ قواعد حماية مدعومة بسياسات
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**الحجب قبل التنفيذ لـ Claude Code** — أمر واحد يثبّت
خطاف PreToolUse يوقف استدعاءات الأدوات المطابقة *قبل* تنفيذها وينتظر
قرارك (بنقرة واحدة من هاتفك عند تفعيل
[إشعارات الدفع السحابية](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

الرفض يحجب استدعاء تلك الأداة فقط — يحتفظ الوكيل بجلسته ويمكنه
تجربة نهج آخر. الموافقة من هاتفك تتجاوز نافذة إذن Claude Code
الخاصة (لأنك أجبت بالفعل). الأدوات غير المطابقة تكلف نحو 40 مللي ثانية
وتمر إلى تدفق إذن Claude Code العادي. تحصل أيضًا على إشعار دفع على
هاتفك عندما ينتظرك Claude Code نفسه (إشعارات `permission_prompt` /
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

افتح `http://localhost:5173/v2/`. يعيد Vite توجيه طلبات `/api` إلى
`http://localhost:8900`، بحيث يتمكن تطبيق React من التواصل مع خادم
Flask المحلي دون إعدادات CORS إضافية.

لبناء الحزمة التي تُشحن مع حزمة Python:

```bash
cd frontend
npm run build
```

تُكتب الحزمة الإنتاجية إلى `clawmetry/static/v2/dist/`.

## توافق بيئات التشغيل / الوكلاء

تراقب ClawMetry العديد من بيئات تشغيل وكلاء الذكاء الاصطناعي، وليس OpenClaw فقط. كل بيئة تشغيل غير OpenClaw تأتي مزودة بمحول قراءة مخصص يترجم صيغة جلساتها الأصلية إلى الأشكال الموحدة لـ ClawMetry؛ يقوم العفريت (daemon) بإدخالها في نفس مخزن DuckDB ولقطة السحابة، مع وسمها ببيئة التشغيل، وتُظهر علامة تبويب إعادة تشغيل الجلسة **مبدّل بيئة تشغيل** عند وجود أكثر من واحدة. راجع [`docs/compatibility.md`](docs/compatibility.md) للاطلاع على المصفوفة الكاملة + دليل لإضافة بيئات تشغيل جديدة، و[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) للتمهيد حول عائلة OpenClaw.

| بيئة التشغيل / الوكيل | الحالة | ملاحظات |
|---|---|---|
| **OpenClaw** | أصلية | بيئة التشغيل المرجعية، تُكتشف تلقائيًا |
| **PicoClaw** | محول تجريبي | JSONL مسطّح من `providers.Message` (`~/.picoclaw/workspace/sessions`). نصوص كاملة، النموذج، استدعاءات الأدوات. |
| **NanoClaw** | محول تجريبي | SQLite لكل جلسة (`data/v2-sessions`). نصوص كاملة + عدد الرسائل. |
| **Hermes** | محول تجريبي | SQLite في `~/.hermes/state.db`. نصوص كاملة، النموذج، الرموز/التكلفة. |
| **Claude Code** | محول تجريبي | JSONL في `~/.claude/projects/.../<id>.jsonl`. نصوص كاملة، النموذج، استدعاءات الأدوات + التفكير، استخدام الرموز. |
| **Codex** | محول تجريبي | JSONL لعمليات التشغيل (rollout) في `~/.codex/sessions/...`. نصوص كاملة، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Cursor** | محول تجريبي | SQLite `state.vscdb`. نصوص الدردشة/المؤلف، النموذج. |
| **Aider** | محول تجريبي | `.aider.chat.history.md` لكل مشروع. نصوص كاملة، النموذج، عدد الرموز. |
| **Goose** | محول تجريبي | SQLite في `~/.local/share/goose`. نصوص كاملة، النموذج، استدعاءات الأدوات، إجمالي الرموز. |
| **opencode** | محول تجريبي | SQLite في `~/.local/share/opencode`. نصوص كاملة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Qwen Code** | محول تجريبي | JSONL في `~/.qwen/projects/.../chats`. نصوص كاملة، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Pi** | محول تجريبي | JSONL في `~/.pi/agent/sessions`. نصوص كاملة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Deep Agents** | محول تجريبي | SQLite في `~/.deepagents/.state/sessions.db`. نصوص كاملة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **n8n** | محول تجريبي | SQLite في `~/.n8n/database.sqlite`. عمليات تنفيذ سير العمل، تشغيلات العُقد، مطالبات AI Agent، النموذج + الرموز حيثما يسجلها n8n. |

"محول تجريبي" تعني أن ClawMetry تشحن قارئًا لصيغة القرص الفعلية الخاصة ببيئة التشغيل تلك، وكل واحد منها مبني ومُتحقَّق منه مقابل تثبيت حقيقي على جهاز حقيقي (راجع `tests/fixtures/runtimes/<rt>/`). المحولات للقراءة فقط؛ وكل واحد منها صريح بشأن ما تخزّنه بيئة التشغيل فعليًا (مثلًا PicoClaw/NanoClaw/Cursor لا تكتب تكلفة الرموز على القرص). عند تشغيل عدة بيئات تشغيل على عقدة واحدة، يحصر مبدّل بيئة التشغيل عرض الجلسات في واحدة لتعمّق نظيف.

## تتبّع أي وكيل SDK — إسناد التكلفة خارج الحلقة (out-loop)

بيئات التشغيل أعلاه تكتب جميعها الجلسات إلى القرص. أما **وكيل الإنتاج** الخاص بك — الذي بنيته على OpenAI Agents SDK، أو LangChain، أو Vercel AI SDK، أو LlamaIndex، أو E2B، أو حلقة `httpx` عادية — فلا يفعل ذلك. لا يزال محول ClawMetry بدون إعدادات (zero-config) يلتقط استدعاءات LLM الخاصة به (التكلفة، الرموز، زمن الاستجابة، الأخطاء) عبر التصحيح الديناميكي (monkey-patching) لـ `httpx`/`requests`:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

تقوم `set_source()` (أو متغيّر البيئة `CLAWMETRY_SOURCE=support-agent`) بوسم كل استدعاء **بمصدر مسمّى**، بحيث يظهر كل منتج تشغّله كسطر مستقل من الدرجة الأولى قابل لإسناد التكلفة في بطاقة **🔌 المصادر خارج الحلقة** الخاصة بلوحة التحكم في علامة تبويب النظرة العامة — الاستدعاءات، مزودو الخدمة، زمن الاستجابة، معدل الأخطاء لكل وكيل. لم تحدد مصدرًا؟ لا تزال الاستدعاءات تُتتبّع، والبطاقة فقط تبقى مخفية.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

هذه هي طبقة البيانات نفسها التي تغذيها محولات بيئة التشغيل (DuckDB ← لقطة سحابية)، لذا فإن المصادر خارج الحلقة تُزامَن مع لوحة التحكم السحابية تمامًا مثل أي شيء آخر، مع تشفير من طرف إلى طرف.

## OpenTelemetry — محايد تجاه المزوّد، أرسل تتبعاتك إلى أي مكان

تتحدث ClawMetry بلغة **OpenTelemetry** في كلا الاتجاهين، باستخدام **اصطلاحات GenAI الدلالية**، لذا فإن تتبعات وكيلك لا تُحبَس أبدًا داخل أداة واحدة.

**التصدير**: كل جلسة — استدعاءات LLM، الأدوات، الوكلاء الفرعيون، الرموز، التكلفة — كامتدادات OTLP/HTTP GenAI إلى أي جامع (Datadog، Grafana، Honeycomb، أو جامع OTel الخاص بك):

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

**الاستيعاب (Ingest)** — يقبل مستقبل OTLP المدمج التتبعات والمقاييس من أي مصدر آخر على `/v1/traces` و`/v1/metrics` (`pip install clawmetry[otel]` لاستيعاب protobuf).

تحصل على لوحة تحكم ClawMetry بدون إعدادات ومحلية أولًا **و** بياناتك في أي نظام خلفي يستخدمه فريقك بالفعل — بدون حبس، وبدون وكيل ثانٍ للتثبيت.

## الإعدادات

معظم الناس لا يحتاجون أي إعدادات. تكتشف ClawMetry تلقائيًا مساحة عملك، والسجلات، والجلسات، والمهام المجدولة.

إذا احتجت للتخصيص:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

كل الخيارات: `clawmetry --help`

## القنوات المدعومة

تُظهر ClawMetry النشاط الحي لكل قناة OpenClaw قمت بإعدادها. تظهر في رسم التدفق (Flow) فقط القنوات المُعدّة فعليًا في ملف `openclaw.json` الخاص بك؛ أما القنوات غير المُعدّة فتُخفى تلقائيًا.

انقر على أي عقدة قناة في التدفق لرؤية عرض فقاعات دردشة حي مع عدد الرسائل الواردة والصادرة.

| القناة | الحالة | نافذة منبثقة حية | ملاحظات |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ كاملة | ✅ | رسائل، إحصائيات، تحديث كل 10 ثوانٍ |
| 💬 **iMessage** | ✅ كاملة | ✅ | تقرأ `~/Library/Messages/chat.db` مباشرة |
| 💚 **WhatsApp** | ✅ كاملة | ✅ | عبر WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ كاملة | ✅ | عبر signal-cli |
| 🟣 **Discord** | ✅ كاملة | ✅ | اكتشاف الخادم (guild) + القناة |
| 🟪 **Slack** | ✅ كاملة | ✅ | اكتشاف مساحة العمل + القناة |
| 🌐 **Webchat** | ✅ كاملة | ✅ | جلسات واجهة الويب المدمجة |
| 📡 **IRC** | ✅ كاملة | ✅ | واجهة فقاعات بنمط طرفية (terminal) |
| 🍏 **BlueBubbles** | ✅ كاملة | ✅ | iMessage عبر واجهة BlueBubbles REST |
| 🔵 **Google Chat** | ✅ كاملة | ✅ | عبر ويب هوكس Chat API |
| 🟣 **MS Teams** | ✅ كاملة | ✅ | عبر إضافة بوت Teams |
| 🔷 **Mattermost** | ✅ كاملة | ✅ | دردشة فريق مستضافة ذاتيًا |
| 🟩 **Matrix** | ✅ كاملة | ✅ | لامركزية، دعم E2EE |
| 🟢 **LINE** | ✅ كاملة | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ كاملة | ✅ | رسائل مباشرة لامركزية NIP-04 |
| 🟣 **Twitch** | ✅ كاملة | ✅ | دردشة عبر اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ كاملة | ✅ | اشتراك أحداث WebSocket |
| 🔵 **Zalo** | ✅ كاملة | ✅ | Zalo Bot API |

> **الاكتشاف التلقائي:** تقرأ ClawMetry ملف `~/.openclaw/openclaw.json` الخاص بك ولا تعرض إلا القنوات التي أعددتها فعليًا. لا حاجة لأي إعداد يدوي.

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

> **ملاحظة:** عند التشغيل داخل Docker، اربط أدلة بيانات وسجلات وكيلك (مثل `~/.openclaw`، `~/.claude`، `~/.codex`) حتى تتمكن ClawMetry من اكتشاف إعداداتك تلقائيًا.

## المتطلبات

- Python 3.8+
- Flask (يُثبّت تلقائيًا عبر pip)
- بيئة تشغيل وكيل ذكاء اصطناعي على نفس الجهاز: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، أو n8n (أو مجلدات مربوطة (mounted volumes) لـ Docker)
- Linux أو macOS

## دعم NemoClaw / OpenShell

تكتشف ClawMetry تلقائيًا [NemoClaw](https://github.com/NVIDIA/NemoClaw) — غلاف الأمان المؤسسي من NVIDIA لـ OpenClaw الذي يشغّل الوكلاء داخل حاويات OpenShell المعزولة (sandboxed).

لا حاجة لأي إعداد إضافي في معظم الحالات. يكتشف عفريت المزامنة (sync daemon) تلقائيًا ملفات الجلسات سواء كانت موجودة في `~/.openclaw/` على المضيف أو داخل حاوية OpenShell.

### كيف يعمل

تكتشف ClawMetry NemoClaw بطريقتين:

1. **اكتشاف عبر الملف الثنائي** — يتحقق من وجود أداة سطر الأوامر `nemoclaw` ويشغّل `nemoclaw status` للحصول على معلومات الصندوق المعزول (sandbox)
2. **اكتشاف عبر الحاوية** — يفحص حاويات Docker قيد التشغيل بحثًا عن صور `openshell` أو `nemoclaw` أو `ghcr.io/nvidia/`، ثم يقرأ الجلسات عبر مجلدات مربوطة أو `docker cp`

تُوسَم ملفات الجلسات المُزامنة من حاويات NemoClaw بـ `runtime=nemoclaw` وبيانات وصفية `container_id` في لوحة التحكم السحابية، حتى تتمكن من تمييزها عن جلسات OpenClaw القياسية بنظرة واحدة.

### الإعداد الموصى به: عفريت المزامنة على المضيف (HOST)

للحصول على أفضل تجربة، شغّل عفريت المزامنة الخاص بـ ClawMetry على **الجهاز المضيف** (وليس داخل الصندوق المعزول). هذا يتجنّب قيود سياسة شبكة NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سيجد عفريت المزامنة تلقائيًا الجلسات داخل أي حاويات OpenShell قيد التشغيل.

### اختياري: اسم صريح للصندوق المعزول

إذا لم يعمل الاكتشاف التلقائي، وجّه ClawMetry إلى الصندوق المعزول الصحيح:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### التشغيل داخل الصندوق المعزول (متقدم)

إذا كان يجب عليك تشغيل عفريت المزامنة **داخل** الصندوق المعزول OpenShell، أضف قاعدة الخروج (egress) هذه إلى سياسة شبكة NemoClaw الخاصة بك حتى يتمكن من الوصول إلى واجهة استيعاب ClawMetry (ingest API):

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

طبّقها بواسطة:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### المنافذ ونقاط النهاية

| نقطة النهاية | المنفذ | البروتوكول | مطلوب |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | نعم (عفريت المزامنة ← السحابة) |
| `localhost:8900` | 8900 | HTTP | نعم (واجهة لوحة التحكم المحلية) |
| مقبس Docker (`/var/run/docker.sock`) | — | مقبس Unix | لاكتشاف جلسات الحاوية |

عفريت المزامنة يجري فقط استدعاءات HTTPS صادرة إلى `ingest.clawmetry.com`. لا تُطلب أي منافذ واردة.

---

## النشر السحابي

راجع **[دليل اختبار السحابة](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** لأنفاق SSH، والوكيل العكسي (reverse proxy)، وDocker.

## الاختبار

يُختبر هذا المشروع باستخدام BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## القياس عن بُعد (Telemetry)

ترسل ClawMetry نبضة "تشغيل أول" مجهولة واحدة إلى
`https://app.clawmetry.com/api/install` عند أول تشغيل لأداة سطر الأوامر
`clawmetry` على جهاز جديد. نستخدم هذا لعدّ التثبيتات (المقياس
التسويقي الوحيد الذي نملكه لمشروع مفتوح المصدر) ولمعرفة أطر عمل
الوكلاء التي ثبّتها مستخدمونا.

**عملية POST واحدة بالضبط لكل تثبيت**، تحتوي على:

| الحقل | مثال | السبب |
|---|---|---|
| `install_id` | UUID عشوائي مخزّن في `~/.clawmetry/install_id` | إزالة التكرار؛ غير مرتبط ببريدك الإلكتروني أو api_key |
| `version` | `0.12.167` | معرفة الإصدارات المنتشرة |
| `os` / `os_version` | `Darwin` / `25.3.0` | أولويات دعم المنصات |
| `python` | `3.11.15` | مصفوفة دعم إصدارات Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | أي وكلاء يجب أن ندمج معهم لاحقًا |
| `is_ci` / `ci_provider` | `true` / `github_actions` | فصل التثبيتات البشرية عن ضجيج CI |

**ما لا نرسله**: عنوان IP (تشتق السحابة رمز البلد من الطلب من جهة
الخادم، ثم تتجاهل عنوان IP)، اسم المضيف، اسم المستخدم، مسار مساحة
العمل، محتويات الملفات، api_key الخاص بك، بريدك الإلكتروني، أو أي
معلومات شخصية أو خاصة بمساحة العمل. الحمولة (payload) المرسلة قابلة
للتدقيق في [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**إلغاء الاشتراك** (أي واحد مما يلي يعطّله بشكل دائم):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

فشل الشبكة هنا لا يمنع أبدًا تشغيل `clawmetry` — النبضة تُرسل بدون
انتظار (fire-and-forget) في خيط عفريت (daemon thread) بمهلة 3 ثوانٍ.

## تاريخ النجوم (Star History)

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
