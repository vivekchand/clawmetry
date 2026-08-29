<!-- i18n-src:d21bea5161e0 -->
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

**شاهد وكيلك وهو يفكر.** مراقبة فورية لـ **30 نظام تشغيل لوكلاء الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و26 غيرها. لوحة تحكم واحدة لأسطول وكلائك بأكمله.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بلا إعدادات. يكتشف كل شيء تلقائيًا.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900**. بلا إعدادات: يجد أنظمة تشغيل الوكلاء
الموجودة لديك بالفعل، يقرأها بوضع القراءة فقط، ولا يغيّر شيئًا في طريقة عملها.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## يعمل مع 30 نظام تشغيل للوكلاء

**مجانًا في التطبيق مفتوح المصدر:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**في خطة مدفوعة:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

كل نظام تشغيل يحصل على نفس لوحة التحكم. شغّل عدة أنظمة في آن واحد، ومُبدّل
الرأس يعيد توجيه كل تبويب إلى أحدها.

بنيت وكيلك الخاص باستخدام SDK بدلًا من ذلك؟ المُعترض (interceptor) يتتبع
استدعاءات LLM الخاصة به أيضًا. راجع [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## ما الذي تحصل عليه

- **الجلسات والنصوص المكتوبة**: ما فعله كل وكيل، دورة تلو الأخرى، مع إعادة تشغيل
- **التكلفة والرموز (tokens)**: لكل نظام تشغيل، ونموذج، وجلسة، ويوم، مع إشارات للحالات الشاذة
- **التدفق (Flow)**: مخطط حي للرسائل المتنقلة عبر القنوات والنماذج والأدوات
- **العقل (Brain)**: تدفق أحداث التفكير واستدعاء الأدوات لحظة حدوثها
- **انفجار السياق (Context blowout)**: نافذة الاستخدام محسوبة الحجم لكل مزوّد، مع مقارنة الضغط (compaction) بالفيضان القسري، بالإضافة إلى خريطة لكل نظام تشغيل توضح ما *لا نستطيع* رؤيته ([كيف](docs/CONTEXT_BLOWOUT.md))
- **الذاكرة والمهارات**: الملفات والمهارات التي حمّلها كل نظام تشغيل فعليًا
- **الصحة والسجلات**: القرص، الذاكرة، معدلات الأخطاء، حدود المعدل، تدفق سجلات مباشر
- **التنبيهات**: حدود الميزانية، ارتفاعات الأخطاء، انقطاع الوكيل عن العمل، موجّهة إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **الموافقات**: أوقف استدعاءات الأدوات الخطيرة *قبل* تنفيذها ووافق عليها من هاتفك ([كيف](docs/APPROVALS.md))

## انفجار السياق، وتكلفة المراقبة

سؤالان يستحقان الإجابة قبل أن تثق بأي أداة لمقارنة الوكلاء.

**كيف يتعامل مع انفجار نافذة السياق عبر أنظمة التشغيل المختلفة؟**

نسبة الاستخدام صادقة بقدر صدق المقام الذي تُقسم عليه. يحدد ClawMetry حجم النافذة
لكل مزوّد من [جدول يمكنك قراءته وتقديم طلب سحب (PR) له](clawmetry/context_windows.py)،
يغطي Anthropic وOpenAI وGoogle وxAI وDeepSeek وKimi وQwen وMistral وLlama وGLM.
لا يقيس جميع أنظمة التشغيل الـ26 بمسطرة مزوّد واحد. هذا مهم: دورة GPT-5 بحجم
300 ألف رمز، عند قياسها بمسطرة Anthropic البالغة 200 ألف، تُقرأ على أنها
">100%، منفجرة" بينما هي في الواقع عند 75% من 400 ألف الخاصة بـGPT-5. المسطرة
نفسها تُخفي دورة DeepSeek منفجرة فعليًا بحجم 130 ألف باعتبارها 65% مريحة.

كل نافذة تُشحن مع مصدرها: `model_table` أو `explicit_marker` أو
`observed_floor`، أو `default` صادق عندما لا نعرف النموذج. المقياس المبني
على تخمين لا يُعرض أبدًا بنفس المصداقية التي يُعرض بها المقياس المبني على بحث فعلي.

يستطيع ClawMetry رؤية أحداث الضغط (compaction) في بعض أنظمة التشغيل فقط. لذا
`GET /api/context-coverage` يُبلغ، لكل نظام تشغيل، عمّا إذا كانت **القيمة صفر
تعني "عمل بسلاسة" أو "نحن عمياون"**. الصفر الذي يعني فعليًا العمى يُصرّح بذلك.
[التفاصيل الكاملة](docs/CONTEXT_BLOWOUT.md)

**ما هي تكلفة الأداة نفسها؟**

| المسار | المُضاف إلى وكيلك | افتراضي؟ |
|---|---|---|
| تتبع ملفات الجلسة (كل الأنظمة الـ30) | **صفر**. عملية منفصلة، لا يوجد كود ClawMetry داخل وكيلك | مفعّل |
| المُعترض عبر HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ملي ثانية** لكل استدعاء LLM، أو 0.009% من استدعاء مدته 5 ثوانٍ | معطّل |
| بوابة الخطاف السابق للأداة (ذاكرة تخزين مؤقت دافئة) | **+44 ملي ثانية** لكل استدعاء أداة خاضع للبوابة، فوق أرضية مفسّر مدتها 36 ملي ثانية | معطّل |
| وكيل التطبيق (Enforcement proxy) | **+9.7 ملي ثانية** لكل استدعاء LLM | معطّل |

تكلفة استضافة العفريت (daemon): **2,762 حدثًا/ثانية** استيعابًا،
**710 بايت/حدث** على القرص (67.7 ميجابايت لكل 100 ألف حدث)، و**نحو 12% من نواة
واحدة** بشكل مستمر على تثبيت نشط. هذا الرقم الأخير يتجاوز ميزانيتنا المُعلنة
البالغة 5-10%، لذا يُنشر كخلل يجب ملاحقته بدلًا من إخفائه عن الصفحة.

قِيس على جهاز Apple M2 Pro باستخدام `benchmarks/overhead.py`. يشغّل الإطار كل
حالة في عملية منفصلة، ويُبدّل ترتيبها، و**يرفض طباعة أي رقم عندما تختلف الجولات
في إشارته**. شغّله على جهازك الخاص خلال دقيقة:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

كل مسار مقيس، بما في ذلك بوابات الخطاف ووكيل التطبيق، ويعمل الإطار على Linux
وmacOS وWindows في CI. نتيجتان تستحقان المعرفة: وكيل التطبيق يكلف نحو سبعة
أضعاف على Windows مقارنة بـLinux، والعفريت يحافظ حاليًا على نحو 12% من نواة
واحدة، متجاوزًا ميزانيتنا الخاصة البالغة 5-10%. البيانات الخام بصيغة JSON،
والمنهجية، وما لم يُقَس بعد، موجودة في [docs/OVERHEAD.md](docs/OVERHEAD.md).

## التسعير

| الخطة | ما تغطيه | السعر |
|---|---|---|
| **مجانية** | OpenClaw + NVIDIA NemoClaw + Goose، لوحة تحكم كاملة، محليًا فقط | 0$ |
| **Starter** | كل نظام تشغيل آخر مذكور أعلاه، عرض الأسطول، مزامنة سحابية | 9$ لكل عقدة / شهريًا |
| **Pro** | Starter + التحكم والتقييم: الموافقات، سياسات مخاطر الأدوات، التقييمات، اكتشاف الحالات الشاذة، مُحسّن التكلفة، تصدير OTel، سجل تدقيق مقاوم للعبث | 19$ لكل عقدة / شهريًا |

الخطط السنوية، وخطة Enterprise، والأرقام الحالية موجودة على
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. مفاتيح الترخيص
للاستضافة الذاتية تعمل بدون السحابة (`clawmetry license`). التقسيم الدقيق
بين المجاني والمدفوع موجود في [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## بياناتك تبقى على جهازك

يقرأ ClawMetry ملفات الجلسات والسجلات المحلية. **لا تغادر أي بيانات جلسة جهازك
إلا إذا شغّلت `clawmetry connect`** — لا مطالبات، ولا ردود، ولا وسائط أدوات،
ولا محتويات ملفات، ولا أسطر سجلات. عندما تتصل فعلًا، تُشفّر اللقطة (snapshot)
من طرف إلى طرف بمفتاح لا يغادر جهازك أبدًا، ويُفكّ تشفيرها في متصفحك. إذا لم
يكن لدى عقدة ما مفتاح، يُتخطى الرفع بدلًا من إرساله بنص واضح، ولا يمكن لأي
استجابة من الخادم تعطيل ذلك.

هناك أمران يعملان افتراضيًا قبل أن تتصل، وكلاهما اختياري الإلغاء ولا يحملان
أي بيانات جلسة: نبضة تثبيت مجهولة الهوية وفحص إصدار مقابل PyPI. كما يبحث
التثبيت الافتراضي عن عنوان IP العام الخاص بك مرة واحدة من أجل سطر شعار بدء
التشغيل. كل وجهة، وما تحمله، وكيفية إيقافها، مُدرجة في
[docs/EGRESS.md](docs/EGRESS.md)؛ التثبيتات المستضافة ذاتيًا، والمُعاد توجيهها،
والمعزولة عن الشبكة (air-gapped) لا تُجري أي مكالمات صادرة اختيارية على
الإطلاق.

يحدث فك التشفير في متصفحك، بكود نقدّمه لك نحن. كان هذا وعدًا سابقًا؛ أصبح الآن
شيئًا يمكنك التحقق منه. كل سطر يلامس مفتاحك موجود في ملف واحد قابل للقراءة،
[`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)، يُشحن داخل
حزمة wheel ويُقدَّم كما هو، مثبّتًا بتجزئة سلامة المصدر الفرعي (Subresource
Integrity). للتحقق من أن المتصفح يشغّل ما نشرناه:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ما لا يُثبته ذلك: نحن من يقدّم الصفحة التي تُحمّل الملف، لذا يمكننا نظريًا تقديم
صفحة مختلفة. تجزئات السلامة تحميك من شبكة توصيل محتوى (CDN) مُخترقة، وليس من
المورّد نفسه. ما تكسبه هو أن أي استبدال يجب أن يكون متعمدًا، وظاهرًا في مصدر
الصفحة، ومختلفًا عن نسخة على PyPI يمكن لأي شخص جلبها. الاستضافة الذاتية أو
البقاء محليًا بالكامل يزيل الاعتماد على ذلك تمامًا.

## التثبيت

```bash
pip install clawmetry     # ثم: clawmetry
```

أو السطر الواحد: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

يحتاج Python 3.8+ على macOS أو Linux أو Windows، وعلى الأقل نظام تشغيل وكيل
واحد على نفس الجهاز. تعليمات Docker: [docs/DOCKER.md](docs/DOCKER.md).

## الوثائق

| | |
|---|---|
| [توافق أنظمة التشغيل](docs/compatibility.md) | ما يقرأه كل محوّل، وكيفية إضافة نظام تشغيل |
| [انفجار السياق](docs/CONTEXT_BLOWOUT.md) | النوافذ الخاصة بكل مزوّد، الضغط مقابل الفيضان، التغطية لكل نظام تشغيل |
| [العبء الإضافي](docs/OVERHEAD.md) | تكلفة الأداة، مقيسة، مع الإطار اللازم لإعادة إنتاجها |
| [الاستحقاقات](docs/ENTITLEMENTS.md) | المجاني مقابل المدفوع، مصفوفة الفئات، أداة الترخيص عبر سطر الأوامر |
| [الموافقات والسياسات](docs/APPROVALS.md) | البوابة قبل التنفيذ، تقييم المخاطر، الموافقات عبر الهاتف |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صدّر التتبعات إلى أي مكان، استقبل OTLP من أي مصدر |
| [تتبع SDK](docs/SDK_TRACKING.md) | إسناد التكلفة للوكلاء الذين بنيتهم بنفسك |
| [قنوات الدردشة](docs/CHANNELS.md) | محوّلات الدردشة المعروضة في Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | إعدادات NVIDIA NemoClaw المعزولة (sandboxed) |
| [Docker](docs/DOCKER.md) | الصورة، compose، تركيب الأحجام (volumes) |
| [البنية المعمارية](ARCHITECTURE.md) · [التطوير](docs/DEVELOPMENT.md) | كيف يعمل من الداخل؛ التشغيل من المصدر |
| [القياس عن بُعد](docs/TELEMETRY.md) | نبضات التثبيت المجهولة وفتح سطح المكتب، وكيفية إيقافها |

## لقطات الشاشة

كل رقم أدناه من جهاز حقيقي واحد، بوضع القراءة فقط، بدون أي بيانات مُهيّأة مسبقًا.

**يخبرك عندما يكون هناك خطأ ما، وليس فقط بما حدث.**
راية تنبيه شاذّتان في الأعلى: إنفاق يعمل بمعدل 7 أضعاف المتوسط اليومي، وارتفاع
تكلفة بمقدار 4.2 ضعف. تحتهما، 324 من أصل 667 جلسة حديثة تحمل إشارة هدر، مُصنّفة
حسب السبب.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**يُظهر لك أين ذهبت الأموال، في كل نافذة زمنية.**
252.47$ اليوم، و513.15$ هذا الأسبوع، و1,312.92$ هذا الشهر، كل منها مع الرموز
(tokens) وراءه ومقدار ما يغطيه اشتراكك بالفعل. تحت ذلك، نحو 1,128$/شهر مُصنّفة
كقابلة للاسترداد و17,256$/شهر تم توفيرها بالفعل بواسطة إعادة استخدام ذاكرة
التخزين المؤقت.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**يرسم كيف تتحول الرسالة إلى إجابة.**
مخطط التدفق الحي: أنت، والقناة التي وصلت عبرها، والبوابة، والنموذج الذي يجيب
الآن، وكل أداة استخدمها. تُضاء العقد أثناء تحرك العمل عبرها.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**كل وكيل على الجهاز، في جدول واحد.**
ما يشغّله، وما يكلفه خلال آخر 24 ساعة وعلى مدى عمره، ومتى شوهد آخر مرة، ومن
يملكه، وما إذا كان الاشتراك يغطي الفاتورة. 14 وكيلًا هنا، 3 جلسات تعمل، 13
هادئة.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**يُظهر أين ذهب وقت الدورة ومالها، أداة تلو الأخرى.**
دورة واحدة من جلسة حقيقية: 11 أداة في 11.2 دقيقة مقابل 1.16$. كل استدعاء Bash
واستدعاء نموذج يحصل على شريطه الخاص على الخط الزمني، بحيث يُميّز الأمر الذي
استغرق 4.1 دقائق عن ذلك الذي استغرق 226 ملي ثانية بلمحة سريعة.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**يُقيّم العمل، وليس فقط الإنفاق.**
تقدير A هذا الأسبوع: 54 مهمة عادت نظيفة، ومهمتان صعبتان كلفتا 48.57$، والدورات
التي لا تحمل نشاطًا كافيًا للحكم عليها استُبعدت من التقييم بدلًا من احتسابها
كانتصارات. كل دورة صعبة ترتبط بأثرها.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**يُظهر لماذا تستمر نافذة السياق في الامتلاء.**
715 ألف من نافذة بحجم مليون رمز في الدورة الأخيرة، وذروة 83.3%، و4 عمليات ضغط
(compactions) أُطلقت جميعها استباقيًا وليس عند الفيضان، بالإضافة إلى استخدام
كل دورة وراء ذلك.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**الاكتشاف يعمل دون أن تُعدّ أي شيء.**
أجهزة الكشف المدمجة مفعّلة منذ التثبيت: توقف الوكيل عن العمل، توقف تغذية
القياس عن بُعد، ارتفاع مفاجئ في التكلفة، اندفاع في استهلاك الرموز، ارتفاع
الأخطاء، طفرة أخطاء، تجاوز حد الميزانية، تطابق توقيع تهديد، اكتشاف من أداة
أمنية، تغيّر في وضعية الأمان. قواعدك الخاصة اختيارية فوق ذلك.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**إيقاف استدعاء خطير هو اختياري بالكامل، ويُشحن معطّلًا.**
عمليات الحذف التكراري، والدفع القسري (force push)، وsudo، والأسرار، وتثبيت
الحزم، والاستدعاءات الصادرة، كل منها له قاعدة يمكنك تفعيلها. حتى تفعّلها،
يراقب ClawMetry ولا يغيّر شيئًا. بمجرد تفعيل واحدة، تنتظر الاستدعاءات المطابقة
هنا (أو على هاتفك) للموافقة أو الرفض.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

المزيد، لكل نظام تشغيل: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## تاريخ النجوم

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
