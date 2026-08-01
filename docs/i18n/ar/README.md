<!-- i18n-src:191e9094d7fa -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI Downloads/week](https://static.pepy.tech/badge/clawmetry/week)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**شاهد وكيلك وهو يفكّر.** مراقبة فورية لـ **14 بيئة تشغيل لوكلاء الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw)، و[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، وClaude Code، وOpenAI Codex، وعشرة غيرها. لوحة تحكم واحدة لأسطول وكلائك بالكامل.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بدون إعداد. يكتشف كل شيء تلقائياً.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900** وينتهي الأمر.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## يعمل مع 14 بيئة تشغيل للوكلاء

بدأت ClawMetry كأداة مراقبة لـ OpenClaw، والآن تقيس **أسطول وكلائك بالكامل** في لوحة تحكم واحدة، وتكتشف تلقائياً كل بيئة تشغيل على جهازك:

🦞 **OpenClaw** · 🟩 **NVIDIA NemoClaw** · ◆ **Claude Code** · ⬡ **OpenAI Codex** · **Cursor** · 🪿 **Goose** · ⚡ **Hermes** · **opencode** · ◈ **Qwen Code** · **Aider** · **NanoClaw** · **PicoClaw** · **Pi** · **Deep Agents** · 🔗 **n8n** · 🪐 **Antigravity**

OpenClaw وNemoClaw مجانيان في التطبيق مفتوح المصدر؛ أما بقية بيئات التشغيل فتُفعَّل عبر ClawMetry Cloud أو ترخيص Pro ذاتي الاستضافة. بدّل بيئة التشغيل من الترويسة، وستُعاد كل علامة تبويب، التكلفة والرموز والأدوات والتتبعات، لتنطبق على تلك البيئة. راجع **[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md)** للاطلاع على التقسيم الدقيق بين المجاني والمدفوع، ومصفوفة المستويات، وشكل `/api/entitlement`، وواجهة سطر الأوامر `clawmetry license`.

## ما الذي ستحصل عليه

- **Flow** — رسم بياني متحرك مباشر يُظهر تدفق الرسائل عبر القنوات، والعقل، والأدوات، والعودة
- **Overview** — فحوصات الصحة، خريطة حرارية للنشاط، أعداد الجلسات، معلومات النموذج
- **Usage** — تتبع الرموز والتكلفة مع تفصيل يومي/أسبوعي/شهري
- **Sessions** — جلسات الوكيل النشطة مع النموذج والرموز وآخر نشاط
- **Crons** — المهام المجدولة مع الحالة، وموعد التشغيل التالي، والمدة
- **Logs** — بث سجلات مباشر بترميز لوني
- **Memory** — تصفح SOUL.md وMEMORY.md وAGENTS.md والملاحظات اليومية
- **Transcripts** — واجهة فقاعات دردشة لقراءة سجلات الجلسات
- **Alerts** — حدود الميزانية، محفزات معدل الأخطاء، اكتشاف عدم اتصال الوكيل؛ توجَّه إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **Approvals** — حجب عمليات الحذف الهدامة، والدفع القسري، وتعديلات قواعد البيانات، وsudo، وتثبيت الحزم، والاتصالات الشبكية خلف موافقة بنقرة واحدة

## لقطات شاشة

### 🧠 Brain — بث مباشر لأحداث الوكيل
![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png)

### 📊 Overview — استخدام الرموز وملخص الجلسة
![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

### ⚡ Flow — تغذية مباشرة لاستدعاءات الأدوات
![Flow tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

### 💰 Tokens — تفصيل التكلفة حسب النموذج والجلسة
![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png)

### 🧬 Memory — متصفح ملفات مساحة العمل
![Memory tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/memory.png)

### 🔐 Security — الوضع الأمني وسجل التدقيق
![Security tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/security.png)

### 🚨 Alerts — حدود الميزانية، محفزات معدل الأخطاء، إشعارات ويب إلى Slack / Discord / PagerDuty / البريد الإلكتروني
![Alerts tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

### ✋ Approvals — حجب استدعاءات الأدوات الخطرة خلف موافقة يدوية؛ قواعد حماية مدعومة بسياسات
![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

**حجب ما قبل التنفيذ لـ Claude Code** — أمر واحد يثبّت خطاف
PreToolUse يوقف استدعاءات الأدوات المطابقة *قبل* تشغيلها وينتظر
قرارك (بضغطة واحدة من هاتفك عند تفعيل
[إشعارات الدفع السحابية](https://app.clawmetry.com/push)):

```bash
clawmetry hooks install     # writes ~/.claude/settings.json (idempotent)
clawmetry hooks status      # what's wired + how many policies are active
clawmetry hooks uninstall   # removes only ClawMetry's entries
```

الرفض يحجب استدعاء تلك الأداة فقط، فيحتفظ الوكيل بجلسته ويمكنه
تجربة نهج آخر. الموافقة من هاتفك تتخطى موجه الأذونات الخاص بـ
Claude Code (فأنت أجبت بالفعل). الأدوات غير المطابقة تكلّف نحو 40
مللي ثانية وتمرّ إلى تدفق الأذونات العادي لـ Claude Code. كما
ستحصل على إشعار دفع على هاتفك عندما ينتظرك Claude Code نفسه
(إشعارات `permission_prompt` / `idle_prompt`).

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

افتح `http://localhost:5173/v2/`. يوجّه Vite طلبات `/api` إلى
`http://localhost:8900`، بحيث يستطيع تطبيق React التواصل مع خادم
Flask المحلي دون إعداد CORS إضافي.

لبناء الحزمة التي تُشحن مع حزمة Python:

```bash
cd frontend
npm run build
```

تُكتب الحزمة الإنتاجية في `clawmetry/static/v2/dist/`.

## توافق بيئات التشغيل / الوكلاء

تراقب ClawMetry العديد من بيئات تشغيل وكلاء الذكاء الاصطناعي، وليس OpenClaw فقط. كل بيئة تشغيل غير OpenClaw تأتي مع محوّل قراءة مخصص يترجم صيغة جلساتها الأصلية إلى أشكال ClawMetry الموحّدة؛ يستوعبها العفريت (daemon) في نفس مخزن DuckDB ولقطة السحابة، مع وسم بيئة التشغيل، وتُظهر علامة تبويب إعادة تشغيل الجلسة **مبدّل بيئة تشغيل** عند وجود أكثر من واحدة. راجع [`docs/compatibility.md`](docs/compatibility.md) للمصفوفة الكاملة ودليل إضافة بيئات تشغيل جديدة، و[`docs/RUNTIME_FAMILY.md`](docs/RUNTIME_FAMILY.md) لمقدمة عائلة OpenClaw.

هل تشغّل أداة أمان الوكلاء [numbat من Perplexity](https://github.com/perplexityai/numbat)؟ تستوعب ClawMetry نتائجها وقرارات الإنفاذ الخاصة بها بشكل جاهز، راجع [`docs/NUMBAT.md`](docs/NUMBAT.md).

| بيئة التشغيل / الوكيل | الحالة | ملاحظات |
|---|---|---|
| **OpenClaw** | أصلية | بيئة التشغيل المرجعية، تُكتشف تلقائياً |
| **PicoClaw** | محوّل تجريبي | JSONL مسطّح من نوع `providers.Message` (`~/.picoclaw/workspace/sessions`). سجلات الحوار، النموذج، استدعاءات الأدوات. |
| **NanoClaw** | محوّل تجريبي | SQLite لكل جلسة (`data/v2-sessions`). سجلات الحوار + عدد الرسائل. |
| **Hermes** | محوّل تجريبي | SQLite في `~/.hermes/state.db`. سجلات الحوار، النموذج، الرموز/التكلفة. |
| **Claude Code** | محوّل تجريبي | JSONL في `~/.claude/projects/.../<id>.jsonl`. سجلات الحوار، النموذج، استدعاءات الأدوات + التفكير، استخدام الرموز. |
| **Codex** | محوّل تجريبي | Rollout JSONL في `~/.codex/sessions/...`. سجلات الحوار، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Cursor** | محوّل تجريبي | SQLite `state.vscdb`. سجلات حوار الدردشة/المؤلف، النموذج. |
| **Aider** | محوّل تجريبي | `.aider.chat.history.md` لكل مشروع. سجلات الحوار، النموذج، أعداد الرموز. |
| **Goose** | محوّل تجريبي | SQLite في `~/.local/share/goose`. سجلات الحوار، النموذج، استدعاءات الأدوات، إجمالي الرموز. |
| **opencode** | محوّل تجريبي | SQLite في `~/.local/share/opencode`. سجلات الحوار، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Qwen Code** | محوّل تجريبي | JSONL في `~/.qwen/projects/.../chats`. سجلات الحوار، النموذج، استدعاءات الأدوات، استخدام الرموز. |
| **Pi** | محوّل تجريبي | JSONL في `~/.pi/agent/sessions`. سجلات الحوار، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **Deep Agents** | محوّل تجريبي | SQLite في `~/.deepagents/.state/sessions.db`. سجلات الحوار، النموذج، استدعاءات الأدوات، الرموز + التكلفة. |
| **n8n** | محوّل تجريبي | SQLite في `~/.n8n/database.sqlite`. تنفيذات سير العمل، تشغيلات العقد، مطالبات AI Agent، النموذج + الرموز حيثما يسجّلها n8n. |
| **Antigravity** | محوّل تجريبي | Brain JSONL تحت `~/.gemini/<flavor>/brain/`. المحادثات، خطوات الأدوات، التفكير، تقسيم رموز Gemini لكل توليد + التكلفة، استهلاك التوليد في الخلفية. |

"محوّل تجريبي" تعني أن ClawMetry تشحن قارئاً لصيغة القرص الفعلية لتلك البيئة، وكل واحد منها بُني وتم التحقق منه مقابل تثبيت حقيقي على جهاز حقيقي (راجع `tests/fixtures/runtimes/<rt>/`). المحوّلات للقراءة فقط؛ كل واحد منها صريح بشأن ما تخزّنه بيئة التشغيل فعلياً (مثلاً PicoClaw/NanoClaw/Cursor لا تكتب تكلفة الرموز على القرص). عند تشغيل عدة بيئات تشغيل على عقدة واحدة، يحصر مبدّل بيئة التشغيل عرض الجلسات في واحدة لتعمّق نظيف.

## تتبّع أي وكيل SDK — إسناد التكلفة خارج الحلقة

كل بيئات التشغيل أعلاه تكتب الجلسات على القرص. أما **وكيل الإنتاج** الخاص بك، ذاك الذي بنيته على OpenAI Agents SDK أو LangChain أو Vercel AI SDK أو LlamaIndex أو E2B أو حلقة `httpx` عادية، فلا يفعل ذلك. المعترض بدون إعداد في ClawMetry يلتقط استدعاءات LLM الخاصة به مع ذلك (التكلفة، الرموز، زمن الاستجابة، الأخطاء) عبر تصحيح `httpx`/`requests` بشكل ديناميكي:

```python
import clawmetry.track            # activate the interceptor
clawmetry.track.set_source("support-agent")   # name this product

# ...your agent runs as normal; every LLM call is now tracked + attributed.
```

`set_source()` (أو متغير البيئة `CLAWMETRY_SOURCE=support-agent`) يسم كل استدعاء **بمصدر مسمّى**، بحيث يظهر كل منتج تشغّله كسطر مستقل قابل لإسناد التكلفة في بطاقة **🔌 مصادر خارج الحلقة** في Overview بلوحة التحكم، تشمل الاستدعاءات، والموفّرين، وزمن الاستجابة، ومعدل الأخطاء لكل وكيل. لم تحدد مصدراً؟ الاستدعاءات ما زالت متتبَّعة، والبطاقة فقط تبقى مخفية.

```bash
CLAWMETRY_SOURCE=billing-agent python my_agent.py
```

هذه نفس طبقة البيانات التي تغذّيها محوّلات بيئة التشغيل (DuckDB ← لقطة السحابة)، لذا تتزامن المصادر خارج الحلقة مع لوحة التحكم السحابية كأي شيء آخر، مشفّرة من طرف إلى طرف.

## OpenTelemetry — محايد تجاه الموفّر، أرسل تتبعاتك إلى أي مكان

تتحدث ClawMetry **OpenTelemetry** في كلا الاتجاهين، باستخدام **اصطلاحات GenAI الدلالية**، بحيث لا تُحبس تتبعات وكيلك أبداً داخل أداة واحدة.

**التصدير**: كل جلسة، استدعاءات LLM، الأدوات، الوكلاء الفرعيون، الرموز، التكلفة، كأطياف OTLP/HTTP من نوع GenAI إلى أي جامع (Datadog، Grafana، Honeycomb، أو جامع OTel الخاص بك):

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

**الاستيعاب** — يقبل مستقبل OTLP المدمج التتبعات والمقاييس من أي مصدر آخر عند `/v1/traces` و`/v1/metrics` (`pip install clawmetry[otel]` لاستيعاب protobuf).

تحصل على لوحة تحكم ClawMetry بدون إعداد ومحلية أولاً **و** بياناتك في أي واجهة خلفية يستخدمها فريقك فعلياً، دون حبس، ودون وكيل ثانٍ للتثبيت.

## الإعداد

معظم الناس لا يحتاجون أي إعداد. تكتشف ClawMetry تلقائياً مساحة عملك وسجلاتك وجلساتك والمهام المجدولة.

إن احتجت للتخصيص:

```bash
clawmetry --port 9000              # Custom port (default: 8900)
clawmetry --host 127.0.0.1         # Bind to localhost only
clawmetry --workspace ~/mybot      # Custom workspace path
clawmetry --name "Alice"           # Your name in Flow visualization
```

كل الخيارات: `clawmetry --help`

## القنوات المدعومة

تعرض ClawMetry النشاط المباشر لكل قناة OpenClaw مُعدَّة لديك. فقط القنوات المُعدَّة فعلياً في `openclaw.json` تظهر في رسم Flow البياني؛ غير المُعدَّة تُخفى تلقائياً.

انقر على أي عقدة قناة في Flow لرؤية عرض فقاعات دردشة مباشر مع أعداد الرسائل الواردة والصادرة.

| القناة | الحالة | نافذة مباشرة | ملاحظات |
|---------|--------|------------|-------|
| 📱 **Telegram** | ✅ كامل | ✅ | الرسائل، الإحصاءات، تحديث كل 10 ثوانٍ |
| 💬 **iMessage** | ✅ كامل | ✅ | يقرأ `~/Library/Messages/chat.db` مباشرة |
| 💚 **WhatsApp** | ✅ كامل | ✅ | عبر WhatsApp Web (Baileys) |
| 🔵 **Signal** | ✅ كامل | ✅ | عبر signal-cli |
| 🟣 **Discord** | ✅ كامل | ✅ | اكتشاف الخادم + القناة |
| 🟪 **Slack** | ✅ كامل | ✅ | اكتشاف مساحة العمل + القناة |
| 🌐 **Webchat** | ✅ كامل | ✅ | جلسات واجهة الويب المدمجة |
| 📡 **IRC** | ✅ كامل | ✅ | واجهة فقاعات على طراز الطرفية |
| 🍏 **BlueBubbles** | ✅ كامل | ✅ | iMessage عبر واجهة BlueBubbles REST |
| 🔵 **Google Chat** | ✅ كامل | ✅ | عبر ويب هوكس Chat API |
| 🟣 **MS Teams** | ✅ كامل | ✅ | عبر إضافة بوت Teams |
| 🔷 **Mattermost** | ✅ كامل | ✅ | دردشة فريق ذاتية الاستضافة |
| 🟩 **Matrix** | ✅ كامل | ✅ | لامركزية، دعم E2EE |
| 🟢 **LINE** | ✅ كامل | ✅ | واجهة LINE Messaging API |
| ⚡ **Nostr** | ✅ كامل | ✅ | رسائل مباشرة لامركزية NIP-04 |
| 🟣 **Twitch** | ✅ كامل | ✅ | دردشة عبر اتصال IRC |
| 🔷 **Feishu/Lark** | ✅ كامل | ✅ | اشتراك أحداث WebSocket |
| 🔵 **Zalo** | ✅ كامل | ✅ | واجهة Zalo Bot API |

> **اكتشاف تلقائي:** تقرأ ClawMetry ملف `~/.openclaw/openclaw.json` وتعرض فقط القنوات التي أعددتها فعلياً. لا حاجة لإعداد يدوي.

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

> **ملاحظة:** عند التشغيل داخل Docker، اربط أدلة بيانات وسجلات وكيلك (مثل `~/.openclaw`، `~/.claude`، `~/.codex`) لتتمكن ClawMetry من اكتشاف إعدادك تلقائياً.

## المتطلبات

- Python 3.8+
- Flask (يُثبَّت تلقائياً عبر pip)
- بيئة تشغيل وكيل ذكاء اصطناعي على نفس الجهاز: OpenClaw أو NVIDIA NemoClaw أو Claude Code أو Codex أو Cursor أو Goose أو Hermes أو opencode أو Qwen Code أو Aider أو NanoClaw أو PicoClaw أو Pi أو Deep Agents أو n8n أو Antigravity (أو مجلدات مربوطة لـ Docker)
- Linux أو macOS

## دعم NemoClaw / OpenShell

تكتشف ClawMetry تلقائياً [NemoClaw](https://github.com/NVIDIA/NemoClaw)، غلاف الأمان المؤسسي من NVIDIA لـ OpenClaw الذي يشغّل الوكلاء داخل حاويات OpenShell المعزولة.

لا حاجة لإعداد إضافي في معظم الحالات. يكتشف عفريت المزامنة تلقائياً ملفات الجلسات سواء كانت موجودة في `~/.openclaw/` على المضيف أو داخل حاوية OpenShell.

### كيف يعمل

تكتشف ClawMetry NemoClaw بطريقتين:

1. **اكتشاف ثنائي** — يتحقق من وجود واجهة سطر أوامر `nemoclaw` ويشغّل `nemoclaw status` للحصول على معلومات البيئة المعزولة
2. **اكتشاف الحاويات** — يفحص حاويات Docker الجارية بحثاً عن صور `openshell` أو `nemoclaw` أو `ghcr.io/nvidia/`، ثم يقرأ الجلسات عبر ربط الأحجام أو `docker cp`

تُوسم ملفات الجلسات المُزامنة من حاويات NemoClaw بـ `runtime=nemoclaw` وبيانات وصفية `container_id` في لوحة التحكم السحابية، لتتمكن من تمييزها عن جلسات OpenClaw القياسية بنظرة واحدة.

### الإعداد الموصى به: عفريت المزامنة على المضيف

للحصول على أفضل تجربة، شغّل عفريت المزامنة الخاص بـ ClawMetry على **الجهاز المضيف** (وليس داخل البيئة المعزولة). هذا يتجنّب قيود سياسة الشبكة الخاصة بـ NemoClaw.

```bash
# On the host (outside the sandbox)
pip install clawmetry
clawmetry connect
clawmetry sync
```

سيجد عفريت المزامنة تلقائياً الجلسات داخل أي حاويات OpenShell جارية.

### اختياري: اسم البيئة المعزولة الصريح

إن لم يعمل الاكتشاف التلقائي، وجّه ClawMetry إلى البيئة المعزولة الصحيحة:

```bash
export NEMOCLAW_SANDBOX=my-sandbox-name
clawmetry sync
```

### التشغيل داخل البيئة المعزولة (متقدم)

إن اضطررت لتشغيل عفريت المزامنة **داخل** بيئة OpenShell المعزولة، أضف قاعدة الخروج هذه إلى سياسة شبكة NemoClaw الخاصة بك لتتمكن من الوصول إلى واجهة استيعاب ClawMetry:

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
| `ingest.clawmetry.com` | 443 | HTTPS | نعم (عفريت المزامنة ← السحابة) |
| `localhost:8900` | 8900 | HTTP | نعم (واجهة لوحة التحكم المحلية) |
| مقبس Docker (`/var/run/docker.sock`) | — | مقبس Unix | لاكتشاف جلسات الحاويات |

يقوم عفريت المزامنة فقط بمكالمات HTTPS صادرة إلى `ingest.clawmetry.com`. لا تُطلب منافذ واردة.

---

## النشر السحابي

راجع **[دليل الاختبار السحابي](https://github.com/vivekchand/clawmetry/blob/main/docs/CLOUD_TESTING.md)** لأنفاق SSH، والوكيل العكسي، وDocker.

## الاختبار

يُختبر هذا المشروع باستخدام BrowserStack.

[![BrowserStack](https://img.shields.io/badge/tested%20with-BrowserStack-orange.svg)](https://browserstack.com)

## القياس عن بعد

ترسل ClawMetry إشارات مجهولة لدورة حياة التثبيت إلى
`https://app.clawmetry.com/api/install`: إشارة `install` واحدة عند
أول تشغيل لواجهة سطر الأوامر `clawmetry` على جهاز جديد، وإشارة
`update` واحدة عند أول تشغيل بعد الترقية إلى إصدار جديد، وإشارة
`onboarded` واحدة عند إتمام خيار الإعداد الأولي داخل لوحة التحكم.
نستخدم هذا لعدّ التثبيتات الحقيقية (أرقام تنزيلات PyPI الخام تمثّل
نحو 98% مرايا وCI وإعادة تنزيلات التحديث التلقائي) ولمعرفة أطر
عمل الوكلاء والإصدارات المستخدمة فعلياً.

**بحد أقصى طلب POST واحد لكل حدث دورة حياة لكل إصدار**، يحتوي على:

| الحقل | مثال | السبب |
|---|---|---|
| `install_id` | UUID عشوائي مخزّن في `~/.clawmetry/install_id` | إزالة التكرار؛ مجهول حتى تربط مزامنة Cloud صراحةً (عندها ينبض عفريت المصادقة حاملاً إياه، رابطاً هذا التثبيت بحسابك) |
| `event` | `install` / `update` / `onboarded` | تثبيت جديد مقابل ترقية لتثبيت موجود |
| `version` | `0.12.167` | الإصدارات الموجودة فعلياً |
| `os` / `os_version` | `Darwin` / `25.3.0` | أولويات دعم المنصات |
| `python` | `3.11.15` | مصفوفة دعم إصدارات Python |
| `agent` | `openclaw` / `nemoclaw` / `hermes` / `none` | الوكلاء التي ينبغي أن نتكامل معها لاحقاً |
| `is_ci` / `ci_provider` | `true` / `github_actions` | فصل تثبيتات البشر عن ضوضاء CI |

**ما لا نرسله**: عنوان IP (تشتق السحابة رمز الدولة من الطلب من
جانب الخادم ثم تتجاهل عنوان IP)، اسم المضيف، اسم المستخدم، مسار
مساحة العمل، محتويات الملفات، مفتاح API الخاص بك، بريدك
الإلكتروني، أي شيء شخصي أو خاص بمساحة العمل. حمولة السلك قابلة
للتدقيق في [`clawmetry/telemetry.py`](clawmetry/telemetry.py).

**إلغاء الاشتراك** (أي واحد من هذه يعطّله بشكل دائم):

```bash
export CLAWMETRY_NO_TELEMETRY=1                # per-shell
export DO_NOT_TRACK=1                          # W3C cross-tool standard
touch ~/.clawmetry/notelemetry                 # persistent file marker
```

فشل الشبكة هنا لا يمنع أبداً تشغيل `clawmetry`، فالإشارة تُرسل
دون انتظار على خيط عفريت بمهلة 3 ثوانٍ.

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
  <sub>من بناء <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawmetry.com">clawmetry.com</a> · جزء من منظومة <a href="https://github.com/openclaw/openclaw">OpenClaw</a></sub>
</p>
