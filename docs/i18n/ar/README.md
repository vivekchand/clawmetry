<!-- i18n-src:0e34918f8f2e -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**شاهد وكيلك وهو يفكّر.** مراقبة فورية لـ **14 بيئة تشغيل لوكلاء الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و10 غيرها. لوحة تحكم واحدة لكامل أسطول وكلائك.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بلا إعدادات. يكتشف كل شيء تلقائيًا.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900** وانتهى الأمر.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## يعمل مع 14 بيئة تشغيل للوكلاء

بدأت ClawMetry كأداة مراقبة لـ OpenClaw، والآن تقيس **أسطول وكلائك بأكمله** في لوحة تحكم واحدة، وتكتشف كل بيئة تشغيل على جهازك تلقائيًا:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity** · 🐙 **GitHub Copilot**

OpenClaw وNemoClaw مجانيان في التطبيق مفتوح المصدر؛ بينما تُفعَّل بقية بيئات التشغيل عبر ClawMetry Cloud أو ترخيص Pro ذاتي الاستضافة. بدّل بين بيئات التشغيل من الترويسة، وستُعاد كل تبويبة (التكلفة، الرموز، الأدوات، التتبعات) لتتمحور حول بيئة التشغيل تلك. راجع **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** لمعرفة التقسيم الدقيق بين المجاني والمدفوع، ومصفوفة المستويات، وشكل `/api/entitlement`، وأداة سطر الأوامر `clawmetry license`.

## ماذا ستحصل عليه

- **Flow** — رسم بياني متحرك حي يعرض تدفق الرسائل عبر القنوات والدماغ والأدوات ثم عودتها
- **Overview** — فحوصات الصحة، خريطة النشاط الحرارية، عدد الجلسات، معلومات النموذج
- **Usage** — تتبع الرموز والتكلفة مع تفصيل يومي/أسبوعي/شهري
- **Sessions** — جلسات الوكيل النشطة مع النموذج والرموز وآخر نشاط
- **Crons** — المهام المجدولة مع الحالة وموعد التشغيل التالي والمدة
- **Logs** — بث سجلات فورية بترميز لوني
- **Memory** — تصفح SOUL.md وMEMORY.md وAGENTS.md والملاحظات اليومية
- **Transcripts** — واجهة فقاعات محادثة لقراءة سجلات الجلسات
- **Alerts** — حدود الميزانية، محفزات معدل الأخطاء، اكتشاف انقطاع الوكيل؛ يوجَّه إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **Approvals** — حجب عمليات الحذف المدمرة، والدفع القسري، وتعديلات قواعد البيانات، وsudo، وتثبيت الحزم، والاتصالات الشبكية خلف موافقة بنقرة واحدة

## لقطات شاشة

### 🧠 Brain — بث حي لأحداث الوكيل
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — استخدام الرموز وملخص الجلسات
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — بث فوري لاستدعاءات الأدوات
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفصيل التكلفة حسب النموذج والجلسة
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — متصفح ملفات مساحة العمل
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — الوضع الأمني وسجل التدقيق
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — حدود الميزانية، محفزات معدل الأخطاء، واستدعاءات ويب إلى Slack / Discord / PagerDuty / البريد الإلكتروني
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — حجب استدعاءات الأدوات الخطرة خلف موافقة يدوية؛ قواعد حماية مدعومة بسياسات
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**حجب ما قبل التنفيذ لـ Claude Code** — أمر واحد يثبّت
خطاف PreToolUse يوقف استدعاءات الأدوات المطابقة *قبل* تشغيلها وينتظر
قرارك (بنقرة واحدة من هاتفك عند تفعيل
[إشعارات الدفع السحابية](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

الرفض يحجب فقط استدعاء تلك الأداة الواحد، ويحتفظ الوكيل بجلسته ويمكنه
تجربة نهج آخر. الموافقة من هاتفك تتخطى مطالبة الأذونات الخاصة بـ Claude Code
(فأنت أجبت بالفعل). استدعاءات الأدوات غير المطابقة تكلف نحو 40 مللي ثانية
وتمر إلى تدفق الأذونات العادي لـ Claude Code. ستحصل أيضًا على إشعار دفع
على هاتفك عندما يكون Claude Code نفسه بانتظارك (إشعارات
`permission_prompt` / `idle_prompt`).

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

تطبيق React v2 موجود في `frontend/` ويُقدَّم على `/v2` عند تشغيل
خادم Flask مع تفعيل v2.

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
`http://localhost:8900`، حتى يتمكن تطبيق React من التواصل مع خادم
Flask المحلي دون إعدادات CORS إضافية.

لبناء الحزمة التي تُشحن مع حزمة Python:

```bash
cd frontend
npm run build
```

تُكتب حزمة الإنتاج في `clawmetry/static/v2/dist/`.

## توافق بيئات التشغيل / الوكلاء

تراقب ClawMetry العديد من بيئات تشغيل وكلاء الذكاء الاصطناعي، وليس فقط OpenClaw. تشحن كل بيئة تشغيل غير OpenClaw محول قراءة مخصص يترجم صيغة جلسته الأصلية إلى أشكال ClawMetry الموحّدة؛ ويستوعبها الخفي (daemon) في نفس مخزن DuckDB + اللقطة السحابية، موسومة ببيئة التشغيل، وتُظهر تبويبة إعادة تشغيل الجلسة **مبدّل بيئة تشغيل** عند وجود أكثر من واحدة. راجع [`docs/compatibility.md`](docs/compatibility.md) للمصفوفة الكاملة + دليل إضافة بيئات تشغيل، و[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) لمقدمة عائلة OpenClaw.

هل تشغّل أداة [numbat](https://github.com/perplexityai/numbat) الخاصة بـ Perplexity لأمن الوكلاء؟ تستوعب ClawMetry نتائجها وقرارات الإنفاذ الخاصة بها جاهزة دون إعداد، راجع [`docs/NUMBAT.md`](docs/NUMBAT.md).

| بيئة التشغيل / الوكيل | الحالة | ملاحظات |
|---|---|---|
| **OpenClaw** | أصلية | بيئة التشغيل المرجعية، تُكتشف تلقائيًا |
| **PicoClaw** | محول تجريبي | ملف JSONL مسطح من نوع `providers.Message` (`~/.picoclaw/workspace/sessions`). سجلات المحادثة، النموذج، استدعاءات الأدوات. |
| **NanoClaw** | محول تجريبي | SQLite لكل جلسة (`data/v2-sessions`). سجلات المحادثة + عدد الرسائل. |
| **Hermes** | محول تجريبي | SQLite في `~/.hermes/state.db`. سجلات المحادثة، النموذج، الرموز/التكلفة. |
| **Claude Code** | محول تجريبي | JSONL في `~/.claude/projects/.../<id>.jsonl`. سجلات المحادثة، النموذج، استدعاءات الأدوات + التفكير، استخدام الرموز. |
| **Codex** | محول تجريبي | JSONL للتنفيذ في `~/.codex/sessions/...`. سجلات المحادثة، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Cursor** | محول تجريبي | SQLite `state.vscdb`. سجلات محادثة/composer، النموذج. |
| **Aider** | محول تجريبي | `.aider.chat.history.md` لكل مشروع. سجلات المحادثة، النموذج، عدد الرموز. |
| **Goose** | محول تجريبي | SQLite في `~/.local/share/goose`. سجلات المحادثة، النموذج، استدعاءات الأدوات، إجمالي الرموز. |
| **opencode** | محول تجريبي | SQLite في `~/.local/share/opencode`. سجلات المحادثة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Qwen Code** | محول تجريبي | JSONL في `~/.qwen/projects/.../chats`. سجلات المحادثة، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Pi** | محول تجريبي | JSONL في `~/.pi/agent/sessions`. سجلات المحادثة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Deep Agents** | محول تجريبي | SQLite في `~/.deepagents/.state/sessions.db`. سجلات المحادثة، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **n8n** | محول تجريبي | SQLite في `~/.n8n/database.sqlite`. تنفيذات سير العمل، تشغيلات العقد، مطالبات AI Agent، النموذج + الرموز حيثما يسجّلها n8n. |
| **Antigravity** | محول تجريبي | JSONL للدماغ ضمن `~/.gemini/<flavor>/brain/`. المحادثات، خطوات الأدوات، التفكير، تفصيل رموز Gemini لكل توليد + التكلفة، استهلاك التوليد الخلفي. |
| **GitHub Copilot** | محول تجريبي | ملف `events.jsonl` الخاص بـ Copilot CLI تحت `~/.copilot/session-state/` + دفتر استخدام كل استدعاء `session-store.db`. المحادثات، استدعاءات الأدوات، توجيه النموذج، تفصيل الرموز الواعي بالتخزين المؤقت، التكلفة المفوترة من المزود كأرصدة ذكاء اصطناعي. |

يعني "محول تجريبي" أن ClawMetry تشحن قارئًا لصيغة القرص الفعلية لبيئة التشغيل تلك، وكل واحد منها مبني ومُتحقّق منه مقابل تثبيت حقيقي على جهاز حقيقي (راجع `tests/fixtures/runtimes/<rt>/`). المحولات للقراءة فقط؛ وكل واحد منها صادق بشأن ما تخزّنه بيئة التشغيل فعليًا (مثلًا PicoClaw/NanoClaw/Cursor لا تكتب تكلفة الرموز على القرص). عند تشغيل عدة بيئات تشغيل على عقدة واحدة، يقصر مبدّل بيئة التشغيل عرض الجلسات على واحدة للتعمق بوضوح.

## تتبّع أي وكيل SDK — إسناد التكلفة خارج الحلقة

بيئات التشغيل أعلاه جميعها تكتب الجلسات على القرص. **وكيل الإنتاج** الخاص بك، ذلك الذي بنيته على OpenAI Agents SDK أو LangChain أو Vercel AI SDK أو LlamaIndex أو E2B أو حلقة `httpx` عادية، لا يفعل ذلك. لا يزال معترض ClawMetry بلا إعدادات يلتقط استدعاءات النموذج اللغوي الخاصة به (التكلفة، الرموز، زمن الاستجابة، الأخطاء) عبر تصحيح `httpx`/`requests` القردي (monkey-patching):

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

تسم `set_source()` (أو متغيّر البيئة `CLAWMETRY_SOURCE=support-agent`) كل استدعاء بـ **مصدر مسمّى**، بحيث يظهر كل منتج تشغّله كسطر مستقل يمكن إسناد تكلفته في بطاقة **🔌 المصادر خارج الحلقة** الخاصة بلوحة تحكم Overview، وتشمل الاستدعاءات والمزودين وزمن الاستجابة ومعدل الأخطاء لكل وكيل. لم يُحدَّد مصدر؟ لا تزال الاستدعاءات تُتَبَّع، لكن البطاقة تبقى مخفية فقط.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

هذه نفس طبقة البيانات التي تغذّيها محولات بيئة التشغيل (DuckDB ← اللقطة السحابية)، لذا تُزامَن المصادر خارج الحلقة إلى لوحة التحكم السحابية مثل كل شيء آخر، مشفّرة من طرف إلى طرف.

## OpenTelemetry — محايدة تجاه المزوّد، أرسل تتبعاتك إلى أي مكان

تتحدث ClawMetry لغة **OpenTelemetry** في كلا الاتجاهين، باستخدام **اصطلاحات GenAI الدلالية**، لذا لن تُحبَس تتبعات وكيلك أبدًا في أداة واحدة.

**تصدير** كل جلسة، استدعاءات النموذج اللغوي، الأدوات، الوكلاء الفرعيين، الرموز، التكلفة، كنطاقات OTLP/HTTP GenAI إلى أي مُجمِّع (Datadog، Grafana، Honeycomb، أو مُجمِّع OTel الخاص بك):

```bash
clawmetry --otel-export http://localhost:4318/v1/traces
# equivalently:
CLAWMETRY_OTEL_EXPORT_ENDPOINT=http://localhost:4318/v1/traces clawmetry
```

رؤوس المصادقة وفترة الاستطلاع اختياريان كمتغيرات بيئة:

```bash
CLAWMETRY_OTEL_EXPORT_HEADERS='{"X-API-Key":"…"}'   # extra HTTP headers
CLAWMETRY_OTEL_EXPORT_INTERVAL=60                    # seconds (default 60)
```

**الاستيعاب** — يقبل مستقبل OTLP المدمج التتبعات والمقاييس من أي مصدر آخر على `/v1/traces` و`/v1/metrics` (`pip install clawmetry[otel]` لاستيعاب protobuf).

تحصل على لوحة تحكم ClawMetry بلا إعدادات ومحلية أولًا **و** بياناتك في أي واجهة خلفية يستخدمها فريقك بالفعل، بلا قيود، وبلا وكيل ثانٍ للتثبيت.

## الإعدادات

معظم الناس لا يحتاجون أي إعدادات. تكتشف ClawMetry مساحة عملك وسجلاتك وجلساتك ومهامك المجدولة تلقائيًا.

إذا احتجت إلى التخصيص:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

جميع الخيارات: `clawmetry --help`

## القنوات المدعومة

تعرض ClawMetry النشاط الحي لكل قناة OpenClaw معدّة لديك. تظهر في مخطط Flow فقط القنوات المُعدّة فعليًا في ملف `openclaw.json` الخاص بك، وتُخفى القنوات غير المعدّة تلقائيًا.

انقر على أي عقدة قناة في Flow لرؤية عرض فقاعات محادثة حي مع عدّاد الرسائل الواردة والصادرة.

| القناة | الحالة | نافذة منبثقة حية | ملاحظات |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ كاملة | ✅ | الرسائل، الإحصاءات، تحديث كل 10 ثوانٍ |
| 💬 **iMessage** | ✅ كاملة | ✅ | تقرأ `~/Library/Messages/chat.db` مباشرة |
| 💚 **WhatsApp** | ✅ كاملة | ✅ | عبر WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ كاملة | ✅ | عبر signal-cli |
| 🟣 **Discord** | ✅ كاملة | ✅ | اكتشاف الخادم + القناة |
| 🟪 **Slack** | ✅ كاملة | ✅ | اكتشاف مساحة العمل + القناة |
| 🌐 **Webchat** | ✅ كاملة | ✅ | جلسات واجهة الويب المدمجة |
| 📡 **IRC** | ✅ كاملة | ✅ | واجهة فقاعات بنمط الطرفية |
| 🍏 **BlueBubbles** | ✅ كاملة | ✅ | iMessage عبر واجهة BlueBubbles REST |
| 🔵 **Google Chat** | ✅ كاملة | ✅ | عبر webhooks الخاصة بـ Chat API |
| 🟣 **MS Teams** | ✅ كاملة | ✅ | عبر إضافة بوت Teams |
| 🔷 **Mattermost** | ✅ كاملة | ✅ | دردشة فريق ذاتية الاستضافة |
| 🟩 **Matrix** | ✅ كاملة | ✅ | لامركزية، تدعم التشفير من طرف إلى طرف |
| 🟢 **LINE** | ✅ كاملة | ✅ | LINE Messaging API |
| ⚡ **Nostr** | ✅ كاملة | ✅ | رسائل خاصة لامركزية NIP-04 |
| 🟣 **Twitch** | ✅ كاملة | ✅ | دردشة عبر اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ كاملة | ✅ | اشتراك أحداث WebSocket |
| 🔵 **Zalo** | ✅ كاملة | ✅ | Zalo Bot API |

> **الاكتشاف التلقائي:** تقرأ ClawMetry ملف `~/.openclaw/openclaw.json` الخاص بك وتعرض فقط القنوات التي أعددتها فعليًا. لا حاجة لإعداد يدوي.

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

> **ملاحظة:** عند التشغيل داخل Docker، اربط أدلة بيانات وسجلات وكيلك (مثل `~/.openclaw`، `~/.claude`، `~/.codex`) حتى تتمكن ClawMetry من اكتشاف إعدادك تلقائيًا.

## المتطلبات

- Python 3.8+
- Flask (تُثبَّت تلقائيًا عبر pip)
- بيئة تشغيل وكيل ذكاء اصطناعي على نفس الجهاز: OpenClaw، NVIDIA NemoClaw، Claude Code، Codex، Cursor، Goose، Hermes، opencode، Qwen Code، Aider، NanoClaw، PicoClaw، Pi، Deep Agents، n8n، Antigravity، أو GitHub Copilot (أو أحجام مُركَّبة لـ Docker)
- Linux أو macOS

## دعم NemoClaw / OpenShell

تكتشف ClawMetry تلقائيًا [NemoClaw](https://github.com/NVIDIA/NemoClaw)، غلاف الأمان المؤسسي من NVIDIA لـ OpenClaw الذي يشغّل الوكلاء داخل حاويات OpenShell المعزولة (sandboxed).

لا حاجة لإعدادات إضافية في معظم الحالات. يكتشف الخفي (daemon) للمزامنة تلقائيًا ملفات الجلسات سواء كانت موجودة في `~/.openclaw/` على المضيف أو داخل حاوية OpenShell.

### كيف يعمل

تكتشف ClawMetry NemoClaw بطريقتين:

1. **اكتشاف ثنائي** — يتحقق من وجود أداة سطر الأوامر `nemoclaw` ويشغّل `nemoclaw status` للحصول على معلومات الصندوق المعزول
2. **اكتشاف الحاويات** — يفحص حاويات Docker قيد التشغيل بحثًا عن صور `openshell` أو `nemoclaw` أو `ghcr.io/nvidia/`، ثم يقرأ الجلسات عبر أحجام مُركَّبة أو `docker cp`

تُوسَم ملفات الجلسات المُزامنة من حاويات NemoClaw بـ `runtime=nemoclaw` وبيانات وصفية `container_id` في لوحة التحكم السحابية، حتى تتمكن من تمييزها عن جلسات OpenClaw القياسية بنظرة سريعة.

### الإعداد الموصى به: خفي المزامنة على المضيف

للحصول على أفضل تجربة، شغّل خفي (daemon) المزامنة الخاص بـ ClawMetry على **الجهاز المضيف** (وليس داخل الصندوق المعزول). هذا يتجنب قيود سياسة الشبكة الخاصة بـ NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سيجد خفي المزامنة تلقائيًا الجلسات داخل أي حاويات OpenShell قيد التشغيل.

### اختياري: اسم صندوق معزول صريح

إذا لم يعمل الاكتشاف التلقائي، وجّه ClawMetry إلى الصندوق المعزول الصحيح:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### التشغيل داخل الصندوق المعزول (متقدم)

إذا كان يجب عليك تشغيل خفي المزامنة **داخل** صندوق OpenShell المعزول، أضف قاعدة الخروج (egress) هذه إلى سياسة شبكة NemoClaw الخاصة بك حتى يتمكن من الوصول إلى واجهة استيعاب ClawMetry:

```yaml
# nemoclaw-policy.yaml
network:
  egress:
    - host: ingest.clawmetry.com
      port: 443
      protocol: https
```

طبّقها باستخدام:

```bash
nemoclaw policy apply --file nemoclaw-policy.yaml
```

### المنافذ ونقاط النهاية

| نقطة النهاية | المنفذ | البروتوكول | مطلوب |
|---|---|---|---|
| `ingest.clawmetry.com` | 443 | HTTPS | نعم (خفي المزامنة ← السحابة) |
| `localhost:8900` | 8900 | HTTP | نعم (واجهة لوحة التحكم المحلية) |
| مقبس Docker (`/var/run/docker.sock`) | — | مقبس Unix | لاكتشاف جلسات الحاويات |

يقوم خفي المزامنة فقط باستدعاءات HTTPS صادرة إلى `ingest.clawmetry.com`. لا تُطلب أي منافذ واردة.

---

## النشر السحابي

راجع **[دليل اختبار السحابة](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** لأنفاق SSH، والوكيل العكسي (reverse proxy)، وDocker.

## الاختبار

يُختبر هذا المشروع باستخدام BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## القياس عن بُعد (Telemetry)

ترسل ClawMetry إشعارات مجهولة الهوية لدورة حياة التثبيت إلى
`https://app.clawmetry.com/api/install`: إشعار `install` واحد عند أول
تشغيل لأداة سطر الأوامر `clawmetry` على جهاز جديد، وإشعار `update` واحد
عند أول تشغيل بعد الترقية إلى إصدار جديد، وإشعار `onboarded` واحد عند
إكمالك لاختيار الإعداد التمهيدي داخل لوحة التحكم. نستخدم هذا لعدّ
التثبيتات الحقيقية (أرقام تنزيلات PyPI الخام مضللة بنسبة ~98% بسبب
المرايا وCI وإعادة التنزيلات التلقائية للتحديث) ولمعرفة أطر عمل
وإصدارات الوكلاء الموجودة فعليًا قيد الاستخدام.

**حد أقصى POST واحد لكل حدث دورة حياة لكل إصدار**، ويحتوي على:

| الحقل | مثال | السبب |
|---|---|---|
| `install_id` | UUID عشوائي مخزّن في `~/.clawmetry/install_id` | إزالة التكرار؛ مجهول الهوية حتى تربط Cloud sync صراحةً (عندئذٍ يحمل نبض الخفي المصادق هذا المعرّف، ليربط هذا التثبيت بحسابك) |
| `event` | `install` / `update` / `onboarded` | تثبيت جديد مقابل ترقية تثبيت موجود |
| `version` | `0.12.167` | ما الإصدارات المستخدمة فعليًا |
| `os` / `os_version` | `Darwin` / `25.3.0` | أولويات دعم المنصات |
| `python` | `3.11.15` | مصفوفة دعم إصدارات Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | مع أي وكلاء يجب أن ندمج لاحقًا |
| `is_ci` / `ci_provider` | `true` / `github_actions` | فصل التثبيتات البشرية عن ضوضاء CI |

**ما لا نرسله**: عنوان IP (تشتق السحابة رمز الدولة من جانب الخادم من
الطلب ثم تتجاهل عنوان IP)، اسم المضيف، اسم المستخدم، مسار مساحة العمل،
محتوى الملفات، مفتاح API الخاص بك، بريدك الإلكتروني، أو أي معلومات
تعريف شخصية أو خاصة بمساحة العمل. الحمولة المرسلة قابلة للتدقيق في
[`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**إلغاء الاشتراك** (أي واحد من هذه يعطّله بشكل دائم):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

فشل الشبكة هنا لا يمنع أبدًا تشغيل `clawmetry`، فالإشعار يُرسَل دون
انتظار على خيط خفي بمهلة 3 ثوانٍ.

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
