<!-- i18n-src:7cfb63716507 -->
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

أمر واحد. بلا إعداد. يكتشف كل شيء تلقائياً.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900** وانتهى الأمر.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## يعمل مع 14 بيئة تشغيل للوكلاء

بدأت ClawMetry كأداة مراقبة لـ OpenClaw، والآن تقيس **أسطول وكلائك بالكامل** في لوحة تحكم واحدة، وتكتشف كل بيئة تشغيل على جهازك تلقائياً:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot** · **Grok** · **QM**

بيئتا OpenClaw وNemoClaw مجانيتان في التطبيق مفتوح المصدر؛ بينما تُفعَّل بقية بيئات التشغيل مع ClawMetry Cloud أو ترخيص Pro ذاتي الاستضافة. بدّل بين بيئات التشغيل من الترويسة، وكل تبويب - التكلفة والرموز والأدوات والتتبعات - يعاد تحديد نطاقه لتلك البيئة. راجع **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** للاطلاع على التقسيم الدقيق بين المجاني والمدفوع، ومصفوفة المستويات، وشكل `/api/entitlement`، وأداة سطر الأوامر `clawmetry license`.

## ما الذي ستحصل عليه

- **Flow** - رسم بياني متحرك حي يعرض تدفق الرسائل عبر القنوات والدماغ والأدوات وعودتها
- **Overview** - فحوصات الصحة، خريطة النشاط الحرارية، عدد الجلسات، معلومات النموذج
- **Usage** - تتبع الرموز والتكلفة مع تفصيل يومي/أسبوعي/شهري
- **Sessions** - جلسات الوكيل النشطة مع النموذج والرموز وآخر نشاط
- **Crons** - المهام المجدولة مع الحالة، التشغيل التالي، المدة
- **Logs** - بث سجلات فوري مرمّز بالألوان
- **Memory** - تصفح SOUL.md وMEMORY.md وAGENTS.md والملاحظات اليومية
- **Transcripts** - واجهة فقاعات محادثة لقراءة سجلات الجلسات
- **Alerts** - حدود الميزانية، محفزات معدل الأخطاء، اكتشاف عدم اتصال الوكيل؛ توجَّه إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **Approvals** - حجب عمليات الحذف المدمّرة، الدفع القسري، تعديلات قواعد البيانات، sudo، تثبيت الحزم، والاتصالات الشبكية خلف موافقة بنقرة واحدة

## لقطات شاشة

### 🧠 Brain - بث حي لأحداث الوكيل
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview - استخدام الرموز وملخص الجلسة
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow - تغذية فورية لاستدعاءات الأدوات
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
PreToolUse الذي يوقف استدعاءات الأدوات المطابقة *قبل* تشغيلها وينتظر
قرارك (نقرة واحدة من هاتفك مع تفعيل
[إشعارات الدفع السحابية](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

الرفض يحجب استدعاء تلك الأداة الواحدة فقط - يحتفظ الوكيل بجلسته ويمكنه
تجربة نهج آخر. الموافقة من هاتفك تتخطى نافذة الأذونات الخاصة بـ Claude Code
نفسها (لأنك أجبت بالفعل). الأدوات غير المطابقة تكلّف نحو 40 مللي ثانية
وتمر عبر تدفق الأذونات العادي لـ Claude Code. كما تحصل على إشعار دفع على
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

تطبيق React الخاص بالإصدار v2 موجود في `frontend/` ويُقدَّم على المسار `/v2` عند
تشغيل خادم Flask مع تفعيل v2.

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

افتح `http://localhost:5173/v2/`. يقوم Vite بتوجيه طلبات `/api` إلى
`http://localhost:8900`، بحيث يمكن لتطبيق React التواصل مع خادم Flask المحلي
دون إعداد CORS إضافي.

لبناء الحزمة التي تُشحن مع حزمة بايثون:

```bash
cd frontend
npm run build
```

تُكتَب الحزمة الإنتاجية إلى `clawmetry/static/v2/dist/`.

## توافق بيئات التشغيل / الوكلاء

تراقب ClawMetry العديد من بيئات تشغيل وكلاء الذكاء الاصطناعي، وليس OpenClaw فقط. كل بيئة تشغيل غير OpenClaw تأتي بمحوّل قراءة مخصص يترجم صيغة الجلسة الأصلية الخاصة بها إلى الأشكال الموحدة لـ ClawMetry؛ يستوعبها الخادم الخلفي في نفس مخزن DuckDB + اللقطة السحابية، مع وسمها ببيئة التشغيل، ويعرض تبويب إعادة تشغيل الجلسة **محدّد بيئة تشغيل** عند وجود أكثر من واحدة. راجع [`docs/compatibility.md`](docs/compatibility.md) للاطلاع على المصفوفة الكاملة + دليل إضافة بيئات تشغيل جديدة، و[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) لمقدمة عائلة OpenClaw.

هل تشغّل أداة [numbat](https://github.com/perplexityai/numbat) الأمنية للوكلاء من Perplexity؟ تستوعب ClawMetry نتائجها وقرارات الإنفاذ الخاصة بها جاهزة للاستخدام - راجع [`docs/NUMBAT.md`](docs/NUMBAT.md).

| بيئة التشغيل / الوكيل | الحالة | ملاحظات |
|---|---|---|
| **OpenClaw** | أصلية | بيئة التشغيل المرجعية، تُكتشف تلقائياً |
| **PicoClaw** | محوّل تجريبي | JSONL مسطح بصيغة `providers.Message` (‏`~/.picoclaw/workspace/sessions`‏). سجلات المحادثة، النموذج، استدعاءات الأدوات. |
| **NanoClaw** | محوّل تجريبي | SQLite لكل جلسة (‏`data/v2-sessions`‏). سجلات المحادثة + عدد الرسائل. |
| **Hermes** | محوّل تجريبي | SQLite على `~/.hermes/state.db`. سجلات المحادثة، النموذج، الرموز/التكلفة. |
| **Claude Code** | محوّل تجريبي | JSONL على `~/.claude/projects/.../<id>.jsonl`. سجلات المحادثة، النموذج، استدعاءات الأدوات + التفكير، استخدام الرموز. |
| **Codex** | محوّل تجريبي | JSONL خاص بالتشغيل على `~/.codex/sessions/...`. سجلات المحادثة، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Cursor** | محوّل تجريبي | SQLite بصيغة `state.vscdb`. سجلات محادثة/composer، النموذج. |
| **Aider** | محوّل تجريبي | ملف `.aider.chat.history.md` لكل مشروع. سجلات المحادثة، النموذج، عدد الرموز. |
| **Goose** | محوّل تجريبي | SQLite على `~/.local/share/goose`. سجلات المحادثة، النموذج، استدعاءات الأدوات، إجمالي الرموز. |
| **opencode** | محوّل تجريبي | SQLite على `~/.local/share/opencode`. سجلات المحادثة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Qwen Code** | محوّل تجريبي | JSONL على `~/.qwen/projects/.../chats`. سجلات المحادثة، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Pi** | محوّل تجريبي | JSONL على `~/.pi/agent/sessions`. سجلات المحادثة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Deep Agents** | محوّل تجريبي | SQLite على `~/.deepagents/.state/sessions.db`. سجلات المحادثة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **n8n** | محوّل تجريبي | SQLite على `~/.n8n/database.sqlite`. تنفيذات سير العمل، تشغيلات العُقد، مطالبات AI Agent، النموذج + الرموز حيثما يسجّلها n8n. |
| **Antigravity** | محوّل تجريبي | Brain JSONL تحت `~/.gemini/<flavor>/brain/`. المحادثات، خطوات الأدوات، التفكير، تقسيم رموز Gemini لكل توليد + التكلفة، استهلاك التوليد في الخلفية. |
| **GitHub Copilot** | محوّل تجريبي | ملف `events.jsonl` الخاص بـ Copilot CLI تحت `~/.copilot/session-state/` + سجل استخدام `session-store.db` لكل استدعاء. المحادثات، استدعاءات الأدوات، توجيه النموذج، تقسيم الرموز المدرك للتخزين المؤقت، التكلفة المفوترة عبر رصيد الذكاء الاصطناعي للمورّد. |
| **Grok** | محوّل تجريبي | Grok Build CLI من xAI (ثنائي Rust تحت `~/.grok/bin/grok`)‏: سجل أحداث عام على `~/.grok/logs/unified.jsonl` + لكل جلسة `~/.grok/sessions/<enc-cwd>/<uuid>/{events.jsonl,summary.json}`. المحادثات، تقسيم الرموز لكل دور، توجيه النموذج، وحمولة المستودع الصادرة من الأداة والمخزَّنة مؤقتاً تحت `~/.grok/upload_queue/` بحيث يمكنك رؤية ما غادر جهازك. |

"محوّل تجريبي" تعني أن ClawMetry تشحن قارئاً لصيغة القرص الفعلية لبيئة التشغيل تلك، مبنياً ومُتحقَّقاً منه على تثبيت حقيقي على جهاز حقيقي (راجع `tests/fixtures/runtimes/<rt>/`). المحوّلات للقراءة فقط؛ وكل واحد منها صريح بشأن ما تخزّنه بيئة التشغيل فعلياً (مثلاً PicoClaw/NanoClaw/Cursor لا تكتب تكلفة الرموز إلى القرص). عند تشغيل عدة بيئات تشغيل على عقدة واحدة، يُحدد محدّد بيئة التشغيل نطاق عرض الجلسات لواحدة منها لتعمّق نظيف.

## تتبّع أي وكيل SDK - إسناد التكلفة خارج الحلقة

بيئات التشغيل أعلاه جميعها تكتب الجلسات إلى القرص. **وكيل الإنتاج** الخاص بك - الذي بنيته على OpenAI Agents SDK أو LangChain أو Vercel AI SDK أو LlamaIndex أو E2B أو حلقة `httpx` عادية - لا يفعل ذلك. لا يزال محوّل ClawMetry بلا إعداد يلتقط استدعاءات LLM الخاصة به (التكلفة، الرموز، زمن الاستجابة، الأخطاء) عن طريق تصحيح `httpx`/`requests` بشكل قردي:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

تقوم `set_source()` (أو متغير البيئة `CLAWMETRY_SOURCE=support-agent`) بوسم كل استدعاء **بمصدر مسمّى**، بحيث يظهر كل منتج تشغّله كسطر مستقل قابل لإسناد التكلفة في بطاقة **🔌 المصادر خارج الحلقة** في تبويب Overview بلوحة التحكم - الاستدعاءات والمزوّدون وزمن الاستجابة ومعدل الأخطاء لكل وكيل. لم تحدد مصدراً؟ تظل الاستدعاءات متتبَّعة، وتبقى البطاقة مخفية فقط.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

هذه هي نفس طبقة البيانات التي تغذّيها محوّلات بيئة التشغيل (DuckDB ← اللقطة السحابية)، لذا تتزامن المصادر خارج الحلقة مع لوحة التحكم السحابية مثل كل شيء آخر، بتشفير من طرف إلى طرف.

## OpenTelemetry - محايد تجاه المورّد، أرسل تتبعاتك إلى أي مكان

تتحدث ClawMetry **OpenTelemetry** في الاتجاهين، باستخدام **اتفاقيات GenAI الدلالية**، بحيث لا تُحبس تتبعات وكيلك أبداً داخل أداة واحدة.

**التصدير**: كل جلسة - استدعاءات LLM، الأدوات، الوكلاء الفرعيون، الرموز، التكلفة - كـ نطاقات GenAI عبر OTLP/HTTP إلى أي جامع (Datadog أو Grafana أو Honeycomb أو جامع OTel الخاص بك):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

رؤوس المصادقة وفترة الاستطلاع اختيارية عبر متغيرات البيئة:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**الاستيعاب** - يقبل مستقبل OTLP المدمج التتبعات والمقاييس من أي مصدر آخر على `/v1/traces` و`/v1/metrics` (ثبّت `pip install clawmetry[otel]` لاستيعاب protobuf).

تحصل على لوحة تحكم ClawMetry بلا إعداد ومحلية أولاً **و** بياناتك في أي خادم خلفي يستخدمه فريقك بالفعل - بلا احتكار، وبلا وكيل ثانٍ للتثبيت.

## الإعداد

معظم الأشخاص لا يحتاجون لأي إعداد. تكتشف ClawMetry تلقائياً مساحة عملك وسجلاتك وجلساتك ومهامك المجدولة.

إذا كنت بحاجة للتخصيص:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

جميع الخيارات: `clawmetry --help`

## القنوات المدعومة

تعرض ClawMetry النشاط الحي لكل قناة OpenClaw قمت بإعدادها. تظهر في مخطط Flow فقط القنوات المُعدَّة فعلياً في ملف `openclaw.json` الخاص بك - أما غير المُعدَّة فتُخفى تلقائياً.

انقر على أي عقدة قناة في Flow لرؤية عرض فقاعات محادثة حي مع عدّاد الرسائل الواردة/الصادرة.

| القناة | الحالة | نافذة حية | ملاحظات |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ كاملة | ✅ | الرسائل، الإحصاءات، تحديث كل 10 ثوان |
| 💬 **iMessage** | ✅ كاملة | ✅ | تقرأ `~/Library/Messages/chat.db` مباشرة |
| 💚 **WhatsApp** | ✅ كاملة | ✅ | عبر WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ كاملة | ✅ | عبر signal-cli |
| 🟣 **Discord** | ✅ كاملة | ✅ | اكتشاف الخادم + القناة |
| 🟪 **Slack** | ✅ كاملة | ✅ | اكتشاف مساحة العمل + القناة |
| 🌐 **Webchat** | ✅ كاملة | ✅ | جلسات واجهة الويب المدمجة |
| 📡 **IRC** | ✅ كاملة | ✅ | واجهة فقاعات بنمط الطرفية |
| 🍏 **BlueBubbles** | ✅ كاملة | ✅ | iMessage عبر واجهة BlueBubbles REST |
| 🔵 **Google Chat** | ✅ كاملة | ✅ | عبر خطافات ويب Chat API |
| 🟣 **MS Teams** | ✅ كاملة | ✅ | عبر إضافة بوت Teams |
| 🔷 **Mattermost** | ✅ كاملة | ✅ | دردشة فريق ذاتية الاستضافة |
| 🟩 **Matrix** | ✅ كاملة | ✅ | لا مركزية، دعم E2EE |
| 🟢 **LINE** | ✅ كاملة | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ كاملة | ✅ | رسائل مباشرة لا مركزية NIP-04 |
| 🟣 **Twitch** | ✅ كاملة | ✅ | دردشة عبر اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ كاملة | ✅ | اشتراك أحداث WebSocket |
| 🔵 **Zalo** | ✅ كاملة | ✅ | Zalo Bot API |

> **الاكتشاف التلقائي:** تقرأ ClawMetry ملف `~/.openclaw/openclaw.json` الخاص بك وتعرض فقط القنوات التي أعددتها فعلياً. لا حاجة لإعداد يدوي.

## نشر Docker

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

> **ملاحظة:** عند التشغيل داخل Docker، اربط دلائل بيانات وسجلات وكيلك (مثل `~/.openclaw`، `~/.claude`، `~/.codex`) حتى تتمكن ClawMetry من اكتشاف إعدادك تلقائياً.

## المتطلبات

- بايثون 3.8+
- Flask (يُثبَّت تلقائياً عبر pip)
- بيئة تشغيل لوكيل ذكاء اصطناعي على نفس الجهاز: OpenClaw أو NVIDIA NemoClaw أو Claude Code أو Codex أو Cursor أو Goose أو Hermes أو opencode أو Qwen Code أو Aider أو NanoClaw أو PicoClaw أو Pi أو Deep Agents أو n8n أو Antigravity أو GitHub Copilot أو Grok أو QM (أو أحجام مثبَّتة لـ Docker)
- لينكس أو macOS

## دعم NemoClaw / OpenShell

تكتشف ClawMetry تلقائياً [NemoClaw](https://github.com/NVIDIA/NemoClaw) - غلاف الأمان المؤسسي من NVIDIA لـ OpenClaw الذي يشغّل الوكلاء داخل حاويات OpenShell المعزولة.

لا حاجة لإعداد إضافي في معظم الحالات. يكتشف الخادم الخلفي للمزامنة ملفات الجلسات تلقائياً سواء كانت موجودة في `~/.openclaw/` على المضيف أو داخل حاوية OpenShell.

### كيف يعمل

تكتشف ClawMetry NemoClaw بطريقتين:

1. **اكتشاف الثنائي** - يتحقق من وجود أداة سطر الأوامر `nemoclaw` ويشغّل `nemoclaw status` للحصول على معلومات الصندوق الرملي
2. **اكتشاف الحاوية** - يفحص حاويات Docker العاملة بحثاً عن صور `openshell` أو `nemoclaw` أو `ghcr.io/nvidia/`، ثم يقرأ الجلسات عبر أحجام مثبَّتة أو `docker cp`

تُوسَم ملفات الجلسات المُزامنة من حاويات NemoClaw بـ `runtime=nemoclaw` وبيانات وصفية `container_id` في لوحة التحكم السحابية، حتى تتمكن من تمييزها عن جلسات OpenClaw القياسية للوهلة الأولى.

### الإعداد الموصى به: خادم المزامنة على المضيف

للحصول على أفضل تجربة، شغّل خادم المزامنة الخاص بـ ClawMetry على **الجهاز المضيف** (وليس داخل الصندوق الرملي). هذا يتجنب قيود سياسة شبكة NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سيجد خادم المزامنة تلقائياً الجلسات داخل أي حاويات OpenShell عاملة.

### اختياري: اسم صندوق رملي صريح

إذا لم يعمل الاكتشاف التلقائي، وجّه ClawMetry إلى الصندوق الرملي الصحيح:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### التشغيل داخل الصندوق الرملي (متقدم)

إذا كان عليك تشغيل خادم المزامنة **داخل** صندوق OpenShell الرملي، أضف قاعدة الخروج هذه إلى سياسة شبكة NemoClaw الخاصة بك حتى يتمكن من الوصول إلى واجهة استيعاب ClawMetry:

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
| `ingest.clawmetry.com` | 443 | HTTPS | نعم (خادم المزامنة ← السحابة) |
| `localhost:8900` | 8900 | HTTP | نعم (واجهة لوحة التحكم المحلية) |
| مقبس Docker (‏`/var/run/docker.sock`‏) | — | مقبس يونكس | لاكتشاف جلسات الحاوية |

يقوم خادم المزامنة بإجراء استدعاءات HTTPS صادرة فقط إلى `ingest.clawmetry.com`. لا حاجة لأي منافذ واردة.

---

## النشر السحابي

راجع **[دليل اختبار السحابة](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** لأنفاق SSH، والوكيل العكسي، وDocker.

## الاختبار

يُختبَر هذا المشروع باستخدام BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## القياس عن بُعد

ترسل ClawMetry إشارات تنبيه مجهولة لدورة حياة التثبيت إلى
`https://app.clawmetry.com/api/install`: إشارة `install` واحدة أول
مرة تشغّل فيها سطر أوامر `clawmetry` على جهاز جديد، وإشارة `update`
واحدة عند أول تشغيل بعد الترقية إلى إصدار جديد، وإشارة `onboarded`
واحدة عند إكمال خيار الإعداد داخل لوحة التحكم. نستخدم هذا لعدّ
التثبيتات الحقيقية (أرقام تنزيل PyPI الخام هي بنسبة ~98% مرايا،
وCI، وإعادة تنزيلات التحديث التلقائي) ولمعرفة أطر عمل الوكلاء
وإصداراتها المستخدمة فعلياً في الواقع.

**حد أقصى POST واحد لكل حدث دورة حياة لكل إصدار**، ويحتوي على:

| الحقل | مثال | السبب |
|---|---|---|
| `install_id` | UUID عشوائي مخزَّن في `~/.clawmetry/install_id` | إزالة التكرار؛ مجهول حتى تربط Cloud sync صراحة (نبضة قلب الخادم الموثّقة تحمل عندها المعرّف، رابطةً هذا التثبيت بحسابك) |
| `event` | `install` / `update` / `onboarded` | تثبيت جديد مقابل ترقية لتثبيت موجود |
| `version` | `0.12.167` | الإصدارات المستخدمة فعلياً |
| `os` / `os_version` | `Darwin` / `25.3.0` | أولويات دعم المنصة |
| `python` | `3.11.15` | مصفوفة دعم إصدار بايثون |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | مع أي وكلاء يجب أن نتكامل تالياً |
| `is_ci` / `ci_provider` | `true` / `github_actions` | فصل تثبيتات البشر عن ضجيج CI |

**ما لا نرسله**: عنوان IP (تشتق السحابة رمز البلد من جانب الخادم
من الطلب، ثم تتجاهل عنوان IP)، اسم المضيف، اسم المستخدم، مسار مساحة
العمل، محتويات الملفات، مفتاح API الخاص بك، بريدك الإلكتروني، أي
معلومات تعريف شخصية أو خاصة بمساحة العمل. الحمولة السلكية قابلة
للتدقيق في [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**إلغاء الاشتراك** (أي واحد من هذه يعطّله بشكل دائم):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

فشل الشبكة هنا لا يمنع أبداً تشغيل `clawmetry` - الإشارة تُرسَل بدون
انتظار على خيط خلفي بمهلة 3 ثوان.

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
  <strong>🦞 شاهد وكيلك وهو يفكّر</strong><br>
  <sub>بُني بواسطة <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · جزء من نظام <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
