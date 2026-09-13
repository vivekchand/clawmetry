<!-- i18n-src:a855a14295b0 -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**قد ينفّذ الوكيل مئة استدعاء أداة دون أن يحرز أي تقدم.** يقرأ ClawMetry
ملفات الجلسات التي تكتبها وكلاء البرمجة لديك أصلاً، ويضع الخط الزمني
واستدعاءات الأدوات وأي بيانات رموز (tokens) وتكلفة تعرضها بيئة التشغيل في واجهة
واحدة، بحيث يمكنك التمييز بين تشغيل طويل يعمل بنجاح وآخر عالق.

يعمل مع **32 بيئة تشغيل لوكلاء الذكاء الاصطناعي** — Claude Code وOpenAI Codex وHermes وOpenClaw و28 غيرها. لوحة تحكم واحدة لأسطول الوكلاء بالكامل. ([القائمة الكاملة](SUPPORTED_RUNTIMES.txt)، مُولَّدة من الكتالوج.)

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بلا إعداد. يكتشف كل شيء تلقائياً.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900**. بلا إعداد: يجد بيئات تشغيل الوكلاء
الموجودة لديك أصلاً، يقرأها بوضع القراءة فقط، ولا يغيّر شيئاً في طريقة عملها.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## قبل أن تثبّت

| | |
|---|---|
| **ماذا يفعل** | يقرأ ملفات الجلسات والسجلات التي تكتبها وكلاؤك أصلاً. لا SDK، ولا تعديل في الكود، ولا أدوات قياس داخل تطبيقك. |
| **ماذا ترى** | الخط الزمني للجلسة، إعادة تشغيل أداة بأداة، تفصيل الرموز والتكلفة، وإشارات المسار (التكرار، الإخفاقات المتكررة) — لكل بيئة تشغيل. |
| **ما هو مجاني** | يقرأ `pip install clawmetry` كلاً من **OpenClaw وNVIDIA NemoClaw وGoose** دون حساب أو مفتاح أو أي اتصال شبكي. أما الـ27 الأخرى — Claude Code وCodex وCursor والباقي — فتُقرأ عبر الإضافة المرافقة مغلقة المصدر `clawmetry-pro`، التي تأتي مع فترة التجربة لسبعة أيام أو مع خطة اشتراك — راجع [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) للتقسيم الدقيق. |
| **كيف تبدأ** | `pip install clawmetry && clawmetry`، ثم افتح localhost:8900. لا وكلاء على هذا الجهاز بعد؟ يفتح `clawmetry --sample` على ثلاث جلسات اصطناعية موسومة. |
| **ما الذي يغادر جهازك** | لا تغادر أي بيانات جلسة، إلا إذا شغّلت `clawmetry connect`. هناك أمران يعملان افتراضياً، كلاهما اختياري (opt-out) ولا يحملان أي محتوى جلسة: نبضة تثبيت مجهولة وفحص إصدار عبر PyPI. كل وجهة مُدرجة في [docs/EGRESS.md](docs/EGRESS.md)، مُعاد بناؤها من التقاط فعلي لحركة الشبكة لا من قراءة التعليقات. |

هناك حدّان يستحقان المعرفة قبل الحكم على المخرجات: تعرض بيئات التشغيل بيانات
مختلفة تماماً (بعضها لا ينشر أي تكلفة على الإطلاق — [الجدول](docs/compatibility.md)
يوضح أيّها، لكل بيئة تشغيل)، ومراقبة إجراء ما ليست كإيقافه
([أي الضوابط حقيقية، لكل بيئة تشغيل](docs/APPROVALS.md)).


## يعمل مع 32 بيئة تشغيل للوكلاء

**مجاني في التطبيق مفتوح المصدر:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**على خطة مدفوعة:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

كل بيئة تشغيل تحصل على نفس لوحة التحكم. شغّل عدة بيئات في آن واحد، وسيعيد
مبدّل الرأس (header) تحديد نطاق كل تبويب لتلك التي تختارها.

هل بنيت وكيلك الخاص فوق SDK بدلاً من ذلك؟ يتتبّع المعترِض (interceptor) استدعاءات
نموذج اللغة الخاصة به أيضاً. راجع [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## ما الذي تحصل عليه

- **الجلسات والنصوص المكتوبة**: ما فعله كل وكيل، دورة بدورة، مع إعادة التشغيل
- **التكلفة والرموز**: لكل بيئة تشغيل ونموذج وجلسة ويوم، مع إشارات للحالات الشاذة
- **التدفّق (Flow)**: رسم بياني حي للرسائل المتنقلة عبر القنوات والنماذج والأدوات
- **العقل (Brain)**: دفق أحداث الاستدلال واستدعاء الأدوات لحظة حدوثها
- **انفجار السياق**: استخدام النافذة محسوباً لكل مزوّد، الضغط (compaction) مقابل الفيض القسري، إضافة خريطة لكل بيئة تشغيل توضح ما *لا* يمكننا رؤيته ([كيف](docs/CONTEXT_BLOWOUT.md))
- **الذاكرة والمهارات**: الملفات والمهارات التي حمّلتها كل بيئة تشغيل فعلياً
- **الصحة والسجلات**: القرص، الذاكرة، معدلات الأخطاء، حدود المعدل، دفق سجلات حي
- **التنبيهات**: حدود الميزانية، ارتفاعات الأخطاء، خروج الوكيل عن الاتصال، موجّهة إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **الموافقات**: أوقف استدعاءات الأدوات الخطرة *قبل* تنفيذها ووافق عليها من هاتفك ([كيف](docs/APPROVALS.md))

## انفجار السياق، وتكلفة المراقبة

سؤالان يستحقان الإجابة قبل أن تثق بأي أداة لمقارنة الوكلاء.

**كيف يتعامل مع انفجار نافذة السياق عبر بيئات التشغيل المختلفة؟**

نسبة الاستخدام لا تكون صادقة إلا بقدر صدق ما تُقسَم عليه. يحدّد ClawMetry
حجم النافذة لكل مزوّد من [جدول يمكنك قراءته وإرسال طلب تعديل له](clawmetry/context_windows.py)،
يغطي Anthropic وOpenAI وGoogle وxAI وDeepSeek وKimi وQwen وMistral وLlama وGLM.
فهو لا يقيس بيئات التشغيل الـ32 كلها بمسطرة مزوّد واحد. وهذا مهم: فدورة GPT-5
بحجم 300K عند قياسها بمسطرة Anthropic البالغة 200K تُقرأ على أنها "أكثر من
100%، انفجرت" بينما هي فعلياً عند 75% من نافذة GPT-5 البالغة 400K. المسطرة
نفسها تخفي دورة DeepSeek منفجرة فعلياً عند 130K على أنها 65% مريحة.

كل نافذة تأتي مع مصدرها: `model_table` أو `explicit_marker` أو
`observed_floor`، أو `default` صادق حين لا نعرف النموذج. لا يُعرَض مقياس
مبني على تخمين بنفس ثقة مقياس مبني على بحث فعلي في الجدول.

لا يستطيع ClawMetry رؤية أحداث الضغط (compaction) إلا في بعض بيئات التشغيل.
لذلك يُبلغ `GET /api/context-coverage`، لكل بيئة تشغيل، عمّا إذا كان
**الصفر يعني "اكتمل التشغيل بسلاسة" أو "نحن عمي عن الرؤية"**. الصفر الذي
يعني فعلياً العمى يُصرَّح به كذلك. [التفاصيل الكاملة](docs/CONTEXT_BLOWOUT.md)

**ما هي تكلفة أدوات القياس؟**

| المسار | يُضاف إلى وكيلك | افتراضي؟ |
|---|---|---|
| تتبّع ملف الجلسة (كل بيئات التشغيل الـ32) | **صفر**. عملية منفصلة، لا يوجد كود ClawMetry داخل وكيلك | مفعّل |
| المعترِض عبر HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0.44 مللي ثانية** لكل استدعاء نموذج لغة، أو 0.009% من استدعاء مدته 5 ثوانٍ | معطّل |
| بوابة الخُطّاف السابق للأداة (ذاكرة تخزين مؤقت دافئة) | **+44 مللي ثانية** لكل استدعاء أداة مضبوط، فوق أرضية مفسِّر مقدارها 36 مللي ثانية | معطّل |
| وكيل التطبيق الإنفاذي (Enforcement proxy) | **+9.7 مللي ثانية** لكل استدعاء نموذج لغة | معطّل |

تكلفة استضافة الخادم الخلفي (daemon): **2,762 حدثاً/ثانية** استيعاباً،
**710 بايت/حدث** على القرص (67.7 ميغابايت لكل 100 ألف حدث)، و**~12% من نواة
واحدة** بشكل مستمر على تثبيت نشط. هذا الرقم الأخير يتجاوز ميزانيتنا المعلنة
البالغة 5-10%، لذا نُشر كخلل يجب ملاحقته لا كأمر أُغفل عن الصفحة.

قِيس على جهاز Apple M2 Pro باستخدام `benchmarks/overhead.py`. يُشغّل الإطار
كل حالة في عملية منفصلة، ويُبدّل ترتيبها، و**يرفض طباعة أي رقم عندما تختلف
الجولات في إشارته**. شغّله على جهازك في أقل من دقيقة:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

كل مسار مقيس، بما في ذلك بوابات الخُطّاف ووكيل التطبيق الإنفاذي، ويعمل
الإطار على Linux وmacOS وWindows ضمن التكامل المستمر (CI). نتيجتان تستحقان
المعرفة: يكلّف الوكيل حوالي سبعة أضعاف على Windows مقارنة بـ Linux، ويستهلك
الخادم الخلفي حالياً حوالي 12% من نواة واحدة، متجاوزاً ميزانيتنا الخاصة
البالغة 5-10%. البيانات الخام بصيغة JSON، والمنهجية، وما لم يُقَس بعد،
موجودة في [docs/OVERHEAD.md](docs/OVERHEAD.md).

## التسعير

| الخطة | ما تشمله | السعر |
|---|---|---|
| **مجانية** | OpenClaw + NVIDIA NemoClaw + Goose، لوحة تحكم كاملة، محلي فقط | 0$ |
| **مبتدئة (Starter)** | كل بيئة تشغيل أخرى أعلاه، عرض الأسطول، مزامنة سحابية | 9$ لكل عقدة / شهرياً |
| **Pro** | Starter + التحكم والتقييم: الموافقات، سياسات مخاطر الأدوات، التقييمات، كشف الحالات الشاذة، محسّن التكلفة، تصدير OTel، سجل تدقيق مقاوم للتلاعب | 19$ لكل عقدة / شهرياً |

الخطط السنوية، خطة المؤسسات، والأرقام الحالية موجودة على
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. مفاتيح الترخيص
للاستضافة الذاتية تعمل دون الحاجة للسحابة (`clawmetry license`). التقسيم
الدقيق بين المجاني والمدفوع موجود في [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## بياناتك تبقى على جهازك

يقرأ ClawMetry ملفات الجلسات والسجلات المحلية. **لا تغادر أي بيانات جلسة
جهازك إلا إذا شغّلت `clawmetry connect`** — لا مطالبات ولا ردود ولا وسائط
أدوات ولا محتوى ملفات ولا أسطر سجلات. عند الاتصال، تُشفَّر اللقطة (snapshot)
من طرف إلى طرف بمفتاح لا يغادر جهازك أبداً، وتُفكّ تشفيرها في متصفحك. إذا لم
يكن لدى عقدة ما مفتاح، يُتخطّى الرفع بدلاً من إرساله دون تشفير، ولا يستطيع أي
رد من الخادم تعطيل ذلك.

هناك أمران يعملان افتراضياً قبل الاتصال، كلاهما اختياري (opt-out) ولا يحملان
بيانات جلسة: نبضة تثبيت مجهولة وفحص إصدار مقابل PyPI. كما يبحث التثبيت
الافتراضي عن عنوان IP العام الخاص بك مرة واحدة من أجل سطر لافتة بدء التشغيل.
كل وجهة، وما تحمله، وكيفية إيقافها مُدرجة في [docs/EGRESS.md](docs/EGRESS.md)؛
التثبيتات ذاتية الاستضافة، أو المُعاد توجيهها، أو المعزولة عن الشبكة (air-gapped)
لا تُجري أي اتصالات صادرة اختيارية على الإطلاق.

يحدث فك التشفير في متصفحك، بكود نقدّمه لك نحن. كان هذا سابقاً وعداً؛ أما الآن
فهو شيء يمكنك التحقق منه. كل سطر يلمس مفتاحك موجود في ملف واحد قابل للقراءة،
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)، يُشحن ضمن الحزمة
(wheel) ويُقدَّم كما هو حرفياً، مثبّتاً بتجزئة سلامة المورد الفرعي (Subresource
Integrity). للتأكد من أن المتصفح يشغّل ما نشرناه فعلاً:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ما لا يثبته ذلك: نحن من يقدّم الصفحة التي تحمّل الملف، لذا يمكننا تقديم صفحة
مختلفة. تجزئات السلامة تحميك من شبكة توصيل محتوى (CDN) مخترقة، لا من المزوّد
نفسه. ما تكسبه هو أن أي استبدال يجب أن يكون متعمّداً، وظاهراً في مصدر الصفحة،
ومختلفاً عن نسخة على PyPI يمكن لأي شخص جلبها. الاستضافة الذاتية أو البقاء محلياً
فقط يزيل هذا الاعتماد تماماً.

## التثبيت

```bash
pip install clawmetry     # ثم: clawmetry
```

أو السطر الواحد: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

يحتاج Python 3.8+ على macOS أو Linux أو Windows، وبيئة تشغيل وكيل واحدة على
الأقل على الجهاز نفسه. تعليمات Docker: [docs/DOCKER.md](docs/DOCKER.md).

أو دع الوكيل يعدّه لك. تعلّم مهارة [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
كلاً من Claude Code وCodex وCursor وGemini CLI وCopilot أو OpenCode كيفية
تثبيت ClawMetry، والإبلاغ عمّا تفعله الوكلاء على الجهاز وما تنفقه، وإيقاف جلسة
واحدة عند الطلب، وحجز استدعاءات الأدوات الخطرة للموافقة عليها:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## التوثيق

| | |
|---|---|
| [توافق بيئات التشغيل](docs/compatibility.md) | ما يقرأه كل محوّل (adapter)، وكيفية إضافة بيئة تشغيل |
| [انفجار السياق](docs/CONTEXT_BLOWOUT.md) | النوافذ لكل مزوّد، الضغط مقابل الفيض، التغطية لكل بيئة تشغيل |
| [العبء (Overhead)](docs/OVERHEAD.md) | تكلفة أدوات القياس، مقاسة، مع الإطار اللازم لإعادة إنتاجها |
| [الاستحقاقات (Entitlements)](docs/ENTITLEMENTS.md) | المجاني مقابل المدفوع، جدول المستويات، واجهة سطر أوامر الترخيص |
| [الموافقات والسياسات](docs/APPROVALS.md) | التصفية قبل التنفيذ، تسجيل المخاطر، الموافقات عبر الهاتف |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صدّر التتبعات إلى أي مكان، واستوعب OTLP من أي مصدر |
| [أحضر وكيلك الخاص](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، وPydantic AI، وLangChain من البداية للنهاية، مع أمثلة قابلة للتشغيل |
| [تتبّع SDK](docs/SDK_TRACKING.md) | إسناد التكلفة للوكلاء الذين بنيتهم بنفسك |
| [قنوات الدردشة](docs/CHANNELS.md) | محوّلات الدردشة المعروضة في Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | إعدادات NVIDIA NemoClaw المعزولة (sandboxed) |
| [Docker](docs/DOCKER.md) | الصورة، والتركيب (compose)، وتوصيلات وحدات التخزين |
| [البنية المعمارية](ARCHITECTURE.md) · [التطوير](docs/DEVELOPMENT.md) | كيف يعمل من الداخل؛ التشغيل من المصدر |
| [القياس عن بُعد](docs/TELEMETRY.md) | نبضات التثبيت المجهولة وفتح سطح المكتب، وكيفية إيقافها |

## لقطات شاشة

كل رقم أدناه من جهاز حقيقي واحد، بوضع القراءة فقط، دون أي بيانات مصطنعة مُدخَلة مسبقاً.

**يخبرك متى يكون هناك خطأ ما، لا فقط بما حدث.**
لافتتان للحالات الشاذة في الأعلى: إنفاق يعمل بمعدل 7 أضعاف المعدل اليومي،
وطفرة تكلفة بمقدار 4.2 ضعف. تحتهما، 324 من أصل 667 جلسة حديثة تحمل إشارة هدر،
مُصنَّفة حسب السبب.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**يريك إلى أين ذهب المال، في كل نافذة زمنية.**
252.47$ اليوم، 513.15$ هذا الأسبوع، 1,312.92$ هذا الشهر، كل منها مع الرموز
الكامنة خلفه ومقدار ما يغطيه اشتراكك بالفعل. تحت ذلك، حوالي 1,128$/شهرياً
مصنّفة كقابلة للاسترداد و17,256$/شهرياً موفَّرة بالفعل عبر إعادة استخدام
التخزين المؤقت.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**يرسم كيف تتحول الرسالة إلى إجابة.**
رسم التدفّق الحي: أنت، والقناة التي وصلت عبرها، والبوابة، والنموذج الذي
يجيب الآن، وكل أداة استعان بها. تُضاء العُقد أثناء تحرّك العمل خلالها.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**كل وكيل على الجهاز، في جدول واحد.**
ما يشغّله، وما يكلّفه خلال الـ24 ساعة الماضية وعلى مدى عمره، وآخر ظهور له،
ومن يملكه، وما إذا كان الاشتراك يغطي الفاتورة. 14 وكيلاً هنا، 3 جلسات تعمل،
13 ساكنة.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**يظهر إلى أين ذهب وقت الدورة ومالها، أداة بأداة.**
دورة واحدة من جلسة حقيقية: 11 أداة في 11.2 دقيقة مقابل 1.16$. يحصل كل
استدعاء Bash واستدعاء نموذج على شريطه الخاص على الخط الزمني، بحيث يمكن التمييز
بلمحة بين الأمر الذي استغرق 4.1 دقائق والآخر الذي استغرق 226 مللي ثانية.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**يقيّم العمل، لا الإنفاق فقط.**
تقدير A هذا الأسبوع: عادت 54 مهمة نظيفة، و2 من المهام الخشنة كلفت 48.57$،
والتشغيلات ذات النشاط القليل جداً بحيث يصعب الحكم عليها استُبعدت من التقدير
بدلاً من احتسابها كإنجازات. يرتبط كل تشغيل خشن بتتبّعه الخاص.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**يوضح سبب استمرار امتلاء نافذة السياق.**
715 ألف من نافذة بحجم مليون رمز في آخر دورة، ذروة 83.3%، و4 عمليات ضغط
أُطلقت جميعها استباقياً لا نتيجة فيض، مع استخدام كل دورة خلف ذلك.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**يعمل الكشف دون أن تُعدّ أي شيء.**
كاشفات مدمجة مفعّلة منذ التثبيت: توقّف الوكيل عن العمل، توقّف تغذية القياس عن
بُعد، طفرة تكلفة، اندفاع في الرموز، ارتفاع الأخطاء، طفرة أخطاء، حد ميزانية،
تطابق توقيع تهديد، نتيجة أداة أمنية، تغيّر في وضعية الأمن. قواعدك الخاصة
اختيارية إضافة على ذلك.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**حجز الاستدعاء الخطر اختياري، ويُشحن معطّلاً.**
الحذف العودي، والدفع القسري (force push)، وsudo، والأسرار، وتثبيت الحزم،
والاستدعاءات الصادرة، لكل منها قاعدة يمكنك تفعيلها. إلى أن تفعل، يراقب
ClawMetry ولا يغيّر شيئاً. بمجرد تفعيل واحدة، تنتظر الاستدعاءات المطابقة هنا
(أو على هاتفك) للموافقة أو الرفض.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

المزيد، لكل بيئة تشغيل: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## التقدير

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## سجل النجوم (Star History)

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## الترخيص

MIT · بُني بواسطة [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
