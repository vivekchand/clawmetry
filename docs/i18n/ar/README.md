<!-- i18n-src:88be2deff5d5 -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**شاهد وكيلك وهو يفكّر.** رصد فوري لأداء **30 بيئة تشغيل لوكلاء الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و26 أخرى. لوحة تحكّم واحدة لكامل أسطول وكلائك.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [أكثر →](docs/i18n/)

أمر واحد. بلا إعداد. يكتشف كل شيء تلقائيًا.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900**. بلا إعداد: يجد بيئات تشغيل الوكلاء الموجودة لديك مسبقًا،
يقرأها للقراءة فقط، ولا يغيّر شيئًا في طريقة تشغيلها.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## يعمل مع 30 بيئة تشغيل للوكلاء

**مجاني في التطبيق مفتوح المصدر:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**في خطة مدفوعة:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

كل بيئة تشغيل تحصل على نفس لوحة التحكّم. شغّل عدة بيئات في آنٍ واحد، ومُبدّل الرأس
يعيد تحديد نطاق كل تبويب على واحدة منها.

بنيت وكيلك الخاص على SDK بدلًا من ذلك؟ المُعترِض (interceptor) يتتبّع استدعاءات نموذج
اللغة الخاصة به أيضًا. راجع [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## ما الذي تحصل عليه

- **الجلسات والنصوص الكاملة**: ما قام به كل وكيل، دورة بدورة، مع إعادة تشغيل (replay)
- **التكلفة والرموز (tokens)**: لكل بيئة تشغيل، ونموذج، وجلسة، ويوم، مع إشارات الشذوذ
- **التدفّق (Flow)**: رسم بياني حي لحركة الرسائل عبر القنوات والنماذج والأدوات
- **العقل (Brain)**: تيار أحداث الاستدلال واستدعاء الأدوات لحظة حدوثه
- **انفجار السياق**: استخدام نافذة السياق مُحجّم حسب المزوّد، الضغط (compaction) مقابل الفائض القسري، إضافة إلى خريطة لكل بيئة تشغيل توضّح ما *لا* يمكننا رؤيته ([كيف](docs/CONTEXT_BLOWOUT.md))
- **الذاكرة والمهارات**: الملفات والمهارات التي حمّلتها كل بيئة تشغيل فعليًا
- **الصحة والسجلات**: القرص، الذاكرة، معدلات الأخطاء، حدود المعدل (rate limits)، تيار سجلات حي
- **التنبيهات**: حدود الموازنة، ارتفاعات الأخطاء، انقطاع الوكيل عن الاتصال، موجّهة إلى Slack أو Discord أو PagerDuty أو Telegram أو البريد الإلكتروني
- **الموافقات**: إيقاف استدعاءات الأدوات الخطرة *قبل* تنفيذها والموافقة عليها من هاتفك ([كيف](docs/APPROVALS.md))

## انفجار السياق، وتكلفة الرصد

سؤالان يستحقّان الإجابة قبل أن تثق بأي أداة لمقارنة الوكلاء.

**كيف يتعامل مع انفجار نافذة السياق عبر بيئات التشغيل المختلفة؟**

نسبة استخدام لا تكون صادقة إلا بمقدار صدق ما تُقسَم عليه. يُحدّد ClawMetry حجم النافذة
لكل مزوّد من [جدول يمكنك قراءته وتقديم طلب سحب (PR) بشأنه](clawmetry/context_windows.py)،
يشمل Anthropic وOpenAI وGoogle وxAI وDeepSeek وKimi وQwen وMistral وLlama وGLM. فهو لا
يقيس كل بيئات التشغيل الثلاثين بمقياس مزوّد واحد. وهذا مهم: دورة بـ 300 ألف رمز على GPT‑5،
عند قياسها بمقياس Anthropic البالغ 200 ألف، تُقرَأ على أنها ">100%، منفجرة" بينما هي في
الواقع عند 75% من نافذة GPT‑5 البالغة 400 ألف. وذلك المقياس نفسه يُخفي دورة DeepSeek
منفجرة فعليًا عند 130 ألف رمز على أنها 65% مريحة.

كل نافذة تأتي مع مصدرها: `model_table`، أو `explicit_marker`، أو `observed_floor`، أو
`default` صادق عندما لا نعرف النموذج. مقياس (gauge) مبني على تخمين لا يُعرَض أبدًا
بنفس مصداقية مقياس مبني على بحث في جدول.

لا يستطيع ClawMetry رؤية أحداث الضغط (compaction) إلا في بعض بيئات التشغيل. لذلك يُقدّم
`GET /api/context-coverage` تقريرًا، لكل بيئة تشغيل، عن كون **الصفر يعني "عمل بلا مشاكل"
أم "نحن عمياء"**. الصفر الذي يعني في الواقع "عمياء" يقول ذلك بصراحة.
[التفصيل الكامل](docs/CONTEXT_BLOWOUT.md)

**ما الذي تكلّفه الأداة القياسية (instrumentation)؟**

| المسار | ما يُضاف إلى وكيلك | مفعّل افتراضيًا؟ |
|---|---|---|
| تتبّع ملف الجلسة (tailing، كل الـ30 بيئة تشغيل) | **0**. عملية منفصلة، لا كود ClawMetry داخل وكيلك | نعم |
| المُعترِض عبر HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0.44 مللي ثانية** لكل استدعاء نموذج لغة، أو 0.009% من استدعاء مدته 5 ثوان | لا |
| بوابة الخطّاف السابق للأداة (ذاكرة تخزين دافئة) | **+44 مللي ثانية** لكل استدعاء أداة مُراقَب، فوق حد أدنى للمُفسِّر (interpreter) قدره 36 مللي ثانية | لا |
| بروكسي التطبيق (enforcement proxy) | **+9.7 مللي ثانية** لكل استدعاء نموذج لغة | لا |

تكلفة استضافة الخادم الخلفي (daemon): استيعاب **2,762 حدثًا/ثانية**، **710 بايت/حدث**
على القرص (67.7 ميجابايت لكل 100 ألف حدث)، و**نحو 12% من نواة واحدة** بشكل مستمر على
تثبيت نشط. هذا الرقم الأخير يتجاوز موازنتنا المُعلَنة البالغة 5-10%، لذا نُنشره كخطأ
يجب تعقّبه بدلًا من إخفائه عن الصفحة.

قِيست على Apple M2 Pro باستخدام `benchmarks/overhead.py`. يشغّل الأداة كل حالة في
عملية منفصلة، ويُبدّل ترتيبها، و**يرفض طباعة رقم عندما تختلف الجولات في إشارته**.
شغّلها على جهازك الخاص في دقيقة واحدة:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

كل مسار مُقاس، بما في ذلك بوابات الخطّاف وبروكسي التطبيق، والأداة تعمل على Linux
وmacOS وWindows في CI. نتيجتان تستحقّان المعرفة: البروكسي يكلّف نحو سبع مرات أكثر على
Windows مقارنة بـ Linux، والخادم الخلفي يستهلك حاليًا نحو 12% من نواة واحدة، متجاوزًا
موازنتنا الخاصة البالغة 5-10%. البيانات الخام بصيغة JSON، والمنهجية، وما لا يزال غير
مقاس، موجودة في [docs/OVERHEAD.md](docs/OVERHEAD.md).

## التسعير

| الخطة | ما تشمله | السعر |
|---|---|---|
| **مجانية** | OpenClaw + NVIDIA NemoClaw + Goose، لوحة تحكّم كاملة، محلية فقط | 0$ |
| **Starter** | كل بيئة تشغيل أخرى مذكورة أعلاه، عرض الأسطول (fleet view)، مزامنة سحابية | 9$ لكل عقدة / شهريًا |
| **Pro** | Starter + التحكّم والتقييم: الموافقات، سياسات خطورة الأدوات، التقييمات (evals)، اكتشاف الشذوذ، مُحسّن التكلفة، تصدير OTel، سجل تدقيق مقاوم للعبث | 19$ لكل عقدة / شهريًا |

الخطط السنوية، خطة Enterprise، والأرقام الحالية موجودة في
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. مفاتيح الترخيص للاستضافة
الذاتية تعمل بدون السحابة (`clawmetry license`). التقسيم الدقيق بين المجاني والمدفوع
موجود في [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## بياناتك تبقى على جهازك

يقرأ ClawMetry ملفات الجلسات والسجلات محليًا. **لا تُغادر أي بيانات جلسة جهازك إطلاقًا
إلا إذا شغّلت `clawmetry connect`** — لا مطالبات (prompts)، ولا ردود، ولا مُعطيات
استدعاء الأدوات، ولا محتوى الملفات، ولا سطور السجلات. وعند الاتصال، تكون اللقطة
(snapshot) مشفّرة من طرف إلى طرف بمفتاح لا يُغادر جهازك مطلقًا، ويتم فكّ تشفيرها في
متصفحك. إذا لم تملك عقدة ما مفتاحًا، يُتخطّى الرفع بدلًا من إرساله بشكل غير مشفّر،
ولا يمكن لأي استجابة من الخادم تعطيل ذلك.

هناك أمران يعملان افتراضيًا قبل الاتصال، وكلاهما اختياري الإلغاء ولا يحمل أي منهما
بيانات جلسة: نبضة تثبيت مجهولة الهوية وفحص إصدار مقابل PyPI. كما يبحث التثبيت
الافتراضي عن عنوان IP العام لديك مرة واحدة لعرضه في سطر لافتة عند بدء التشغيل. كل
وجهة، وما تحمله، وكيفية إيقافها، مُدرَجة في [docs/EGRESS.md](docs/EGRESS.md)؛ التثبيتات
المُستضافة ذاتيًا، أو المُعاد توجيهها، أو المعزولة تمامًا عن الشبكة، لا تقوم بأي
استدعاءات صادرة اختيارية على الإطلاق.

يحدث فكّ التشفير في متصفحك، بكود نقدّمه لك. كان ذلك في السابق مجرّد وعد؛ أما الآن
فهو أمر يمكنك التحقّق منه. كل سطر يلامس مفتاحك موجود في ملف واحد قابل للقراءة،
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)، والذي يُشحَن ضمن الحزمة
(wheel) ويُقدَّم حرفيًا، مثبّتًا بتجزئة سلامة المصدر الفرعي (Subresource Integrity).
للتأكّد من أن المتصفح يشغّل ما نشرناه:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ما لا يُثبته ذلك: نحن الذين نقدّم الصفحة التي تحمّل الملف، فيمكننا نظريًا تقديم صفحة
مختلفة. تجزئات السلامة تحميك من شبكة توصيل محتوى مخترقة، لا من المزوّد نفسه. ما تحصل
عليه هو أن أي استبدال يجب أن يكون متعمّدًا، ومرئيًا في مصدر الصفحة، ومختلفًا عن أداة
منشورة على PyPI يمكن لأي شخص جلبها. الاستضافة الذاتية أو البقاء محليًا بالكامل يزيل
هذا الاعتماد كليًا.

## التثبيت

```bash
pip install clawmetry     # ثم: clawmetry
```

أو السطر الواحد: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

يحتاج Python 3.8+ على macOS أو Linux أو Windows، وعلى الأقل بيئة تشغيل وكيل واحدة
على نفس الجهاز. تعليمات Docker: [docs/DOCKER.md](docs/DOCKER.md).

أو اجعل الوكيل يُهيّئه لك. مهارة [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
تُعلّم Claude Code أو Codex أو Cursor أو Gemini CLI أو Copilot أو OpenCode كيفية
تثبيت ClawMetry، والإبلاغ عن ما تقوم به الوكلاء على الجهاز وما تنفقه، وإيقاف جلسة واحدة
عند الطلب، وتعليق استدعاءات الأدوات الخطرة للموافقة عليها:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## الوثائق

| | |
|---|---|
| [توافق بيئات التشغيل](docs/compatibility.md) | ما يقرأه كل محوّل (adapter)، وكيفية إضافة بيئة تشغيل |
| [انفجار السياق](docs/CONTEXT_BLOWOUT.md) | نوافذ خاصة بكل مزوّد، الضغط مقابل الفائض، تغطية لكل بيئة تشغيل |
| [الحمل الزائد (Overhead)](docs/OVERHEAD.md) | ما تكلّفه الأداة القياسية، مقاسة، مع الأداة اللازمة لإعادة إنتاجها |
| [الاستحقاقات (Entitlements)](docs/ENTITLEMENTS.md) | المجاني مقابل المدفوع، مصفوفة الفئات، أداة سطر الأوامر للترخيص |
| [الموافقات والسياسات](docs/APPROVALS.md) | التحقّق قبل التنفيذ، تقييم الخطورة، الموافقات من الهاتف |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | تصدير التتبّعات (traces) إلى أي مكان، واستيعاب OTLP من أي مصدر |
| [أحضر وكيلك الخاص](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، وPydantic AI، وLangChain من طرف إلى طرف، مع أمثلة قابلة للتشغيل |
| [تتبّع SDK](docs/SDK_TRACKING.md) | نسب التكلفة للوكلاء الذين بنيتهم بنفسك |
| [قنوات الدردشة](docs/CHANNELS.md) | محوّلات الدردشة المعروضة في التدفّق (Flow) |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | إعدادات NVIDIA NemoClaw المعزولة (sandboxed) |
| [Docker](docs/DOCKER.md) | الصورة، compose، تركيبات الحجوم (volume mounts) |
| [البنية المعمارية](ARCHITECTURE.md) · [التطوير](docs/DEVELOPMENT.md) | كيفية عمله من الداخل؛ التشغيل من المصدر |
| [القياس عن بُعد (Telemetry)](docs/TELEMETRY.md) | نبضات التثبيت المجهولة الهوية ونبضات فتح تطبيق سطح المكتب، وكيفية إيقافها |

## لقطات شاشة

كل رقم أدناه من جهاز حقيقي واحد، للقراءة فقط، بدون أي بيانات مُلقّنة مسبقًا.

**يُنبّهك عندما يكون هناك خطأ ما، وليس فقط ما حدث.**
لافتتا شذوذ في الأعلى: إنفاق يسير بمعدّل 7 أضعاف المتوسط اليومي، وارتفاع تكلفة بمعدّل
4.2x. تحتها، 324 من أصل 667 جلسة أخيرة تحمل إشارة هدر، مُصنّفة بحسب السبب.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**يُظهر لك إلى أين ذهب المال، في كل نافذة زمنية.**
252.47$ اليوم، و513.15$ هذا الأسبوع، و1,312.92$ هذا الشهر، كلٌ مع الرموز خلفه ومقدار
ما تُغطّيه اشتراكك من ذلك مسبقًا. تحت ذلك، نحو 1,128$/شهريًا مُصنّفة كقابلة للاستعادة
و17,256$/شهريًا تم توفيرها فعليًا بإعادة استخدام الذاكرة المؤقتة (cache).

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**يرسم كيف تتحوّل رسالة إلى إجابة.**
رسم التدفّق الحي: أنت، والقناة التي وصلت عبرها، والبوابة (gateway)، والنموذج الذي
يجيب الآن، وكل أداة استخدمها. تُضيء العُقَد بينما يتحرّك العمل خلالها.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**كل وكيل على الجهاز، في جدول واحد.**
ما الذي يُشغّله، وما تكلفته في آخر 24 ساعة وعلى مدى عمره الكامل، وآخر مرّة شُوهد فيها،
ومن يملكه، وهل يُغطّي اشتراك ما هذه الفاتورة. 14 وكيلًا هنا، 3 جلسات تعمل، و13 صامتة.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**يُظهر أين ذهب وقت الدورة ومالها، أداةً بأداة.**
دورة واحدة من جلسة حقيقية: 11 أداة في 11.2 دقيقة بتكلفة 1.16$. كل استدعاء Bash
واستدعاء نموذج يحصل على شريطه الخاص على الخط الزمني، بحيث يُفرَّق بنظرة واحدة بين
الأمر الذي استغرق 4.1 دقائق والآخر الذي استغرق 226 مللي ثانية.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**يُقيّم العمل، وليس مجرّد الإنفاق.**
تقدير A هذا الأسبوع: 54 مهمة عادت نظيفة، ومهمّتان صعبتان كلّفتا 48.57$، والدورات
التي لا تحتوي على نشاط كافٍ للحكم عليها تُستثنى من التقدير بدلًا من عدّها كنجاحات.
كل دورة صعبة ترتبط بتتبّعها (trace).

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**يُظهر لماذا تستمرّ نافذة السياق في الامتلاء.**
715 ألف رمز من نافذة مقدارها مليون رمز في آخر دورة، وقمة عند 83.3%، و4 عمليات ضغط
(compaction) أُطلِقت جميعها بشكل استباقي وليس عند حدوث فائض، مع نسبة استخدام كل دورة
سابقة.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**الاكتشاف يعمل دون أن تُهيّئ أي شيء.**
أدوات الاكتشاف المدمجة مفعّلة منذ التثبيت: الوكيل توقّف عن الاستجابة، انقطاع تيار
القياس عن بُعد، ارتفاع مفاجئ في التكلفة، دفعة رموز مفاجئة، تصاعد في الأخطاء، ارتفاع
مفاجئ في الأخطاء، تجاوز حدّ الموازنة، تطابق توقيع تهديد، اكتشاف من أداة أمنية، تغيّر
في وضع الأمان. قواعدك الخاصة اختيارية فوق ذلك.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**تعليق استدعاء خطر هو اختياري بالانضمام، ويُشحن مُعطّلًا.**
الحذف المتكرّر (recursive deletes)، والدفع القسري (force pushes)، وsudo، والأسرار،
وتثبيتات الحزم، والاستدعاءات الصادرة، كلٌّ منها يحصل على قاعدة يمكنك تفعيلها. حتى
تفعّلها، يرصد ClawMetry فقط ولا يغيّر شيئًا. وبعد تفعيل قاعدة، تنتظر الاستدعاءات
المطابقة هنا (أو على هاتفك) للموافقة أو الرفض.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

المزيد، لكل بيئة تشغيل: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## تاريخ النجوم (Star History)

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
