<!-- i18n-src:61beb8393e2f -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**يمكن لوكيل ذكي أن يجري مئة استدعاء أداة دون أن يحرز أي تقدم.** يقرأ ClawMetry
ملفات الجلسات التي تكتبها وكلاء البرمجة لديك أصلاً، ويجمع الجدول الزمني،
واستدعاءات الأدوات، وأي بيانات رموز وتكلفة تكشف عنها بيئة التشغيل في عرض واحد
حتى تتمكن من التمييز بين تشغيل طويل يعمل بشكل صحيح وآخر عالق.

يعمل مع **30 بيئة تشغيل لوكلاء ذكاء اصطناعي** — Claude Code وOpenAI Codex وHermes وOpenClaw و26 أخرى. لوحة تحكم واحدة لأسطول الوكلاء لديك بأكمله. ([القائمة الكاملة](SUPPORTED_RUNTIMES.txt)، مُولّدة من الكتالوج.)

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بلا إعدادات. يكتشف كل شيء تلقائياً.

```bash
pip install clawmetry && clawmetry
```

يُفتح على **http://localhost:8900**. بلا إعدادات: يجد بيئات تشغيل الوكلاء
الموجودة لديك أصلاً، ويقرأها للقراءة فقط، ولا يغيّر شيئاً في طريقة عملها.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## قبل أن تُثبّت

| | |
|---|---|
| **ماذا يفعل** | يقرأ ملفات الجلسات والسجلات التي تكتبها وكلاؤك أصلاً. بلا SDK، وبلا تغيير في الكود، وبلا أي أداة قياس داخل تطبيقك. |
| **ماذا ترى** | جدول زمني للجلسة، إعادة تشغيل أداة بأداة، تفصيل للرموز والتكلفة، وإشارات المسار (التكرار، الإخفاقات المتكررة) — لكل بيئة تشغيل. |
| **ما هو مجاني** | يقرأ `pip install clawmetry` كلاً من **OpenClaw وNVIDIA NemoClaw وGoose** بدون حساب أو مفتاح أو أي اتصال شبكي. أما الـ27 الأخرى — Claude Code وCodex وCursor والباقي — فتُقرأ عبر إضافة `clawmetry-pro` مغلقة المصدر، التي تأتي مع فترة التجربة لسبعة أيام أو مع خطة اشتراك — راجع [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) للتفاصيل الدقيقة للتقسيم. |
| **كيف تبدأ** | `pip install clawmetry && clawmetry`، ثم افتح localhost:8900. لا توجد وكلاء على هذا الجهاز بعد؟ يفتح `clawmetry --sample` على ثلاث جلسات اصطناعية موسومة. |
| **ماذا يغادر جهازك** | لا تغادر أي بيانات جلسة، ما لم تُشغّل `clawmetry connect`. هناك أمران يعملان افتراضياً، كلاهما اختياري إلغاؤه ولا يحمل أي منهما محتوى الجلسة: نبضة تثبيت مجهولة الهوية وفحص إصدار عبر PyPI. كل وجهة موثّقة في [docs/EGRESS.md](docs/EGRESS.md)، أُعيد بناؤها من التقاط سلكي فعلي وليس من قراءة التعليقات. |

هناك حدّان يستحقان المعرفة قبل الحكم على المخرجات: بيئات التشغيل تكشف عن
بيانات مختلفة جداً (بعضها لا ينشر أي تكلفة على الإطلاق — [الجدول المقارن](docs/compatibility.md)
يوضح أيها، لكل بيئة تشغيل)، ومراقبة إجراء ما ليست كإيقافه
([أي أدوات التحكم حقيقية فعلاً، لكل بيئة تشغيل](docs/APPROVALS.md)).


## يعمل مع 30 بيئة تشغيل للوكلاء

**مجاني في التطبيق مفتوح المصدر:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**على خطة مدفوعة:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

كل بيئة تشغيل تحصل على نفس لوحة التحكم. شغّل عدة بيئات في آن واحد، وسيعيد
المُبدّل في الترويسة توجيه كل تبويب لتركز على واحدة منها.

هل بنيت وكيلك الخاص باستخدام SDK بدلاً من ذلك؟ يتتبّع المُعترض (interceptor)
استدعاءات النموذج اللغوي الخاصة به أيضاً. راجع [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## ماذا تحصل عليه

- **الجلسات والنصوص**: ماذا فعل كل وكيل، دورة بدورة، مع إعادة التشغيل
- **التكلفة والرموز**: لكل بيئة تشغيل ونموذج وجلسة ويوم، مع أعلام الشذوذ
- **التدفق (Flow)**: رسم تخطيطي حي للرسائل وهي تنتقل عبر القنوات والنماذج والأدوات
- **العقل (Brain)**: تدفق أحداث الاستدلال واستدعاء الأدوات لحظة وقوعه
- **انفجار السياق**: استخدام نافذة السياق بحجم محسوب لكل مزوّد، والتمييز بين الضغط (compaction) والتجاوز القسري، إضافة لخريطة لكل بيئة تشغيل توضّح ما *لا* يمكننا رؤيته ([كيف](docs/CONTEXT_BLOWOUT.md))
- **الذاكرة والمهارات**: الملفات والمهارات التي حمّلتها فعلياً كل بيئة تشغيل
- **الصحة والسجلات**: القرص، الذاكرة، معدلات الأخطاء، حدود المعدل، تدفق سجلات حي
- **التنبيهات**: حدود الميزانية، ارتفاعات الأخطاء، توقف الوكيل عن العمل، موجّهة إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **الموافقات**: إيقاف استدعاءات الأدوات المحفوفة بالمخاطر *قبل* تنفيذها والموافقة عليها من هاتفك ([كيف](docs/APPROVALS.md))

## انفجار السياق، وما تكلفه المراقبة

سؤالان يستحقان الإجابة قبل أن تثق بأي أداة لمقارنة الوكلاء.

**كيف يتعامل مع انفجار نافذة السياق عبر بيئات التشغيل المختلفة؟**

نسبة الاستخدام لا تكون صادقة إلا بقدر صدق المقام الذي تُقسم عليه. يحدد
ClawMetry حجم النافذة لكل مزوّد من [جدول يمكنك قراءته وإرسال طلب سحب
(PR) بشأنه](clawmetry/context_windows.py)، يغطي Anthropic وOpenAI وGoogle وxAI
وDeepSeek وKimi وQwen وMistral وLlama وGLM. فهو لا يقيس بيئات التشغيل الثلاثين
كلها بمسطرة مزوّد واحد. وهذا مهم: فدورة بحجم 300 ألف رمز على GPT-5 عند قياسها
بمقياس Anthropic البالغ 200 ألف تُقرأ على أنها "أكثر من 100%، منفجرة" بينما هي
فعلياً عند 75% من الـ400 ألف الخاصة بـ GPT-5. المسطرة نفسها تُخفي دورة DeepSeek
منفجرة فعلياً عند 130 ألف رمز على أنها 65% مريحة.

كل نافذة تأتي بمصدرها: `model_table` أو `explicit_marker` أو
`observed_floor`، أو `default` صادق حين لا نعرف النموذج. مقياس مبني على تخمين
لا يُعرض أبداً بنفس المصداقية التي يُعرض بها مقياس مبني على بحث فعلي.

لا يستطيع ClawMetry رؤية أحداث الضغط (compaction) إلا في بعض بيئات التشغيل.
لذا يُبلغ `GET /api/context-coverage`، لكل بيئة تشغيل، عمّا إذا كان **الصفر
يعني "اشتغل بسلاسة" أو "نحن عمياً"**. الصفر الذي يعني فعلياً "أعمى" يُصرّح بذلك.
[التفاصيل الكاملة](docs/CONTEXT_BLOWOUT.md)

**ما الذي تكلّفه أداة القياس؟**

| المسار | المُضاف إلى وكيلك | افتراضي؟ |
|---|---|---|
| متابعة ملف الجلسة (كل بيئات التشغيل الـ30) | **صفر**. عملية منفصلة، بدون كود ClawMetry داخل وكيلك | نعم |
| المُعترض عبر HTTP (`CLAWMETRY_INTERCEPT=1`) | **0.44+ مللي ثانية** لكل استدعاء نموذج، أو 0.009% من استدعاء مدته 5 ثوانٍ | لا |
| بوابة الخُطّاف السابق للأداة (ذاكرة تخزين مؤقت دافئة) | **44+ مللي ثانية** لكل استدعاء أداة مُراقَب، فوق أرضية مُفسِّر مدتها 36 مللي ثانية | لا |
| وكيل التنفيذ (proxy) | **9.7+ مللي ثانية** لكل استدعاء نموذج | لا |

تكلفة استضافة العفريت (daemon): **2,762 حدثاً/ثانية** استيعاباً،
**710 بايتاً/حدث** على القرص (67.7 ميغابايت لكل 100 ألف حدث)، و**نحو 12% من
نواة واحدة** بشكل مستمر على تثبيت نشط. هذا الرقم الأخير يتجاوز الميزانية
المعلنة من قِبَلنا والبالغة 5-10%، لذا يُنشر كخلل يجب ملاحقته وليس تركه خارج
الصفحة.

قِيس على جهاز Apple M2 Pro باستخدام `benchmarks/overhead.py`. يُشغّل الإطار كل
حالة في عملية منفصلة، ويُبدّل ترتيبها، **ويرفض طباعة رقم عندما تختلف الجولات
على إشارته**. شغّله على جهازك في دقيقة واحدة:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

كل مسار مقيس، بما في ذلك بوابات الخُطّاف ووكيل التنفيذ، ويُشغَّل الإطار على
Linux وmacOS وWindows في CI. نتيجتان تستحقان المعرفة: يكلّف وكيل التنفيذ نحو
سبعة أضعاف على Windows مقارنة بـ Linux، ويستمر العفريت حالياً باستهلاك نحو 12%
من نواة واحدة، متجاوزاً ميزانيتنا المعلنة البالغة 5-10%. البيانات الخام بصيغة
JSON، والمنهجية، وما لم يُقَس بعد، موجودة في [docs/OVERHEAD.md](docs/OVERHEAD.md).

## التسعير

| الخطة | ما تغطيه | السعر |
|---|---|---|
| **مجانية** | OpenClaw + NVIDIA NemoClaw + Goose، لوحة تحكم كاملة، محلية فقط | 0$ |
| **مبتدئة (Starter)** | كل بيئة تشغيل أخرى مذكورة أعلاه، عرض الأسطول، مزامنة سحابية | 9$ لكل عقدة / شهرياً |
| **احترافية (Pro)** | Starter + التحكم والتقييم: الموافقات، سياسات مخاطر الأدوات، التقييمات، كشف الشذوذ، مُحسّن التكلفة، تصدير OTel، سجل تدقيق مقاوم للعبث | 19$ لكل عقدة / شهرياً |

الخطط السنوية، والمؤسسات، والأرقام الحالية موجودة على
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. مفاتيح الترخيص
للاستضافة الذاتية تعمل بدون السحابة (`clawmetry license`). التقسيم الدقيق بين
المجاني والمدفوع في [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## بياناتك تبقى على جهازك

يقرأ ClawMetry ملفات الجلسات والسجلات المحلية. **لا تغادر أي بيانات جلسة جهازك
ما لم تُشغّل `clawmetry connect`** — لا مطالبات (prompts) ولا ردود ولا وسائط
أدوات ولا محتوى ملفات ولا أسطر سجلات. وعندما تتصل فعلاً، تُشفّر اللقطة
تشفيراً طرفياً كاملاً (end-to-end) بمفتاح لا يغادر جهازك أبداً، ويُفكّ تشفيرها
في متصفحك. إذا لم تملك عقدة ما مفتاحاً، يُتخطّى الرفع بدلاً من إرساله دون
تشفير، ولا يستطيع أي رد من الخادم إيقاف ذلك.

هناك أمران يعملان افتراضياً قبل أن تتصل، كلاهما اختياري إلغاؤه ولا يحمل أي
منهما بيانات الجلسة: نبضة تثبيت مجهولة الهوية وفحص إصدار مقابل PyPI. كما يبحث
التثبيت الافتراضي عن عنوان IP العام الخاص بك مرة واحدة من أجل سطر شعار عند
بدء التشغيل. كل وجهة، وما تحمله، وكيفية إيقافها، مذكورة في
[docs/EGRESS.md](docs/EGRESS.md)؛ التثبيتات ذاتية الاستضافة، أو المُعاد
توجيهها، أو المعزولة عن الشبكة، لا تجري أي اتصالات صادرة اختيارية على
الإطلاق.

يحدث فك التشفير في متصفحك، في كود نقدّمه لك نحن. كان هذا في السابق وعداً؛
أما الآن فهو أمر يمكنك التحقق منه. كل سطر يلمس مفتاحك موجود في ملف واحد قابل
للقراءة، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
يُشحن داخل الـ wheel ويُقدَّم كما هو حرفياً، مثبّتاً بتجزئة سلامة المصدر
الفرعي (Subresource Integrity). للتأكد من أن المتصفح يشغّل ما نشرناه فعلاً:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ما لا يثبته ذلك: نحن من يقدّم الصفحة التي تحمّل الملف، لذا يمكننا أن نقدّم
صفحة مختلفة. تجزئات السلامة تحميك من شبكة توصيل محتوى مُخترقة، لا من المزوّد
نفسه. ما تكسبه هو أن أي استبدال يجب أن يكون متعمداً، ومرئياً في مصدر الصفحة،
ومختلفاً عن قطعة برمجية على PyPI يمكن لأي شخص جلبها. الاستضافة الذاتية أو
البقاء محلياً فقط يزيل هذا الاعتماد كلياً.

## التثبيت

```bash
pip install clawmetry     # ثم: clawmetry
```

أو السطر الواحد: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

يتطلب Python 3.8+ على macOS أو Linux أو Windows، وبيئة تشغيل وكيل واحدة على
الأقل على نفس الجهاز. تعليمات Docker: [docs/DOCKER.md](docs/DOCKER.md).

أو دع الوكيل يُعِدّه لك. تُعلّم مهارة [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
كلاً من Claude Code وCodex وCursor وGemini CLI وCopilot أو OpenCode كيفية
تثبيت ClawMetry، والإبلاغ عمّا تفعله الوكلاء على الجهاز وما تنفقه، وإيقاف جلسة
واحدة عند الطلب، وتعليق استدعاءات الأدوات المحفوفة بالمخاطر بانتظار الموافقة:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## الوثائق

| | |
|---|---|
| [توافق بيئات التشغيل](docs/compatibility.md) | ما الذي يقرأه كل محوّل (adapter)، وكيفية إضافة بيئة تشغيل |
| [انفجار السياق](docs/CONTEXT_BLOWOUT.md) | النوافذ لكل مزوّد، الضغط (compaction) مقابل التجاوز، التغطية لكل بيئة تشغيل |
| [التكلفة الإضافية (Overhead)](docs/OVERHEAD.md) | ما تكلّفه أداة القياس، مقيسة فعلياً، مع الإطار اللازم لإعادة إنتاجها |
| [الاستحقاقات (Entitlements)](docs/ENTITLEMENTS.md) | المجاني مقابل المدفوع، جدول المستويات، واجهة سطر أوامر الترخيص |
| [الموافقات والسياسات](docs/APPROVALS.md) | التحقق قبل التنفيذ، تقييم المخاطر، الموافقات عبر الهاتف |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | تصدير الآثار (traces) إلى أي مكان، واستيعاب OTLP من أي مصدر |
| [أحضر وكيلك الخاص](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، وPydantic AI، وLangChain من البداية إلى النهاية، مع أمثلة قابلة للتشغيل |
| [تتبّع SDK](docs/SDK_TRACKING.md) | إسناد التكلفة للوكلاء الذين بنيتهم بنفسك |
| [قنوات الدردشة](docs/CHANNELS.md) | محوّلات الدردشة المعروضة في التدفق (Flow) |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | إعدادات NVIDIA NemoClaw المعزولة (sandboxed) |
| [Docker](docs/DOCKER.md) | الصورة، والتركيب (compose)، وتوصيلات وحدات التخزين |
| [البنية المعمارية](ARCHITECTURE.md) · [التطوير](docs/DEVELOPMENT.md) | كيف يعمل من الداخل؛ التشغيل من المصدر |
| [القياس عن بُعد (Telemetry)](docs/TELEMETRY.md) | نبضات التثبيت المجهولة وفتح سطح المكتب، وكيفية إيقافها |

## لقطات الشاشة

كل رقم أدناه من جهاز حقيقي واحد، للقراءة فقط، بدون أي بيانات مزروعة مسبقاً.

**يخبرك متى يكون هناك خطأ ما، وليس فقط بما حدث.**
شريطا شذوذ في الأعلى: إنفاق يسير بمعدل 7 أضعاف المتوسط اليومي، وارتفاع مفاجئ
في التكلفة بمقدار 4.2 ضعف. تحتهما، 324 من أصل 667 جلسة حديثة تحمل إشارة هدر،
مُصنّفة حسب السبب.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**يُظهر لك أين ذهب المال، في كل نافذة زمنية.**
252.47$ اليوم، و513.15$ هذا الأسبوع، و1,312.92$ هذا الشهر، كل منها مع الرموز
وراءه ومقدار ما يغطيه اشتراكك بالفعل. تحت ذلك، نحو 1,128$/شهرياً مُصنّفة
كقابلة للاسترداد و17,256$/شهرياً موفَّرة بالفعل عبر إعادة استخدام ذاكرة
التخزين المؤقت.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**يرسم كيف تتحوّل الرسالة إلى إجابة.**
الرسم التخطيطي الحي للتدفق: أنت، والقناة التي وصلت عبرها، والبوابة (gateway)،
والنموذج الذي يجيب الآن، وكل أداة استخدمها. تُضاء العُقَد بينما يتحرك العمل
عبرها.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**كل وكيل على الجهاز، في جدول واحد.**
ما يشغّله، وما يكلّفه في الـ24 ساعة الماضية وعلى مدى عمره، ومتى شوهد آخر مرة،
ومن يملكه، وهل يغطي اشتراك ما الفاتورة. 14 وكيلاً هنا، 3 جلسات تعمل، و13 هادئة.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**يُظهر أين ذهب وقت الدورة ومالها، أداةً بأداة.**
دورة واحدة من جلسة حقيقية: 11 أداة في 11.2 دقيقة مقابل 1.16$. يحصل كل استدعاء
Bash واستدعاء نموذج على شريطه الخاص في الجدول الزمني، بحيث يُميَّز الأمر الذي
استغرق 4.1 دقيقة عن الذي استغرق 226 مللي ثانية بلمحة واحدة.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**يُقيّم جودة العمل، لا الإنفاق فقط.**
تقدير A هذا الأسبوع: 54 مهمة عادت نظيفة، ومهمتان صعبتان كلفتا 48.57$، وتُستبعد
الدورات ذات النشاط القليل جداً لتقييمها من التقدير بدلاً من احتسابها كنجاحات.
كل دورة صعبة ترتبط بأثرها (trace).

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**يُظهر لماذا تستمر نافذة السياق بالامتلاء.**
715 ألف رمز من أصل نافذة مليون رمز في آخر دورة، وذروة 83.3%، و4 عمليات ضغط
(compaction) أُطلقت جميعها استباقياً وليس عند تجاوز فعلي، مع استخدام كل دورة
وراء ذلك.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**الكشف يعمل دون أن تُعِدّ شيئاً.**
أدوات الكشف المدمجة تعمل منذ التثبيت: توقف الوكيل عن الاستجابة، توقف تغذية
القياس عن بُعد، ارتفاع مفاجئ في التكلفة، اندفاع في استهلاك الرموز، تصاعد
الأخطاء، ارتفاع مفاجئ في الأخطاء، تجاوز حد الميزانية، تطابق توقيع تهديد، نتيجة
من أداة أمنية، تغيّر في الوضع الأمني. قواعدك الخاصة اختيارية فوق ذلك.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**تعليق الاستدعاء المحفوف بالمخاطر اختياري، ويُشحن مُوقَفاً.**
عمليات الحذف التكراري، والدفع القسري (force push)، وsudo، والأسرار، وتثبيت
الحزم، والاتصالات الصادرة، لكل منها قاعدة يمكنك تفعيلها. إلى أن تفعل ذلك،
يراقب ClawMetry فقط ولا يغيّر شيئاً. وبمجرد تفعيل واحدة، تنتظر الاستدعاءات
المطابقة هنا (أو على هاتفك) للموافقة أو الرفض.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

المزيد، لكل بيئة تشغيل: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## تقدير واعتراف

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## تاريخ النجوم

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## الترخيص

MIT · بناه [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
