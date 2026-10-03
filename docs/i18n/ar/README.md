<!-- i18n-src:c99ac0512cae -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**يمكن للوكيل إجراء مئات استدعاءات الأدوات دون تحقيق أي تقدّم حقيقي.** تقرأ ClawMetry
ملفات الجلسات التي تكتبها وكلاء الترميز لديك فعلًا، وتضع الخط الزمني،
واستدعاءات الأدوات، وأي بيانات رموز وتكلفة يعرضها وقت التشغيل في عرض واحد —
بحيث يمكنك التمييز بين تشغيل طويل يعمل بنجاح وآخر عالق.

يعمل مع **33 نظام تشغيل لوكلاء الذكاء الاصطناعي** — Claude Code، OpenAI Codex، Hermes، OpenClaw وأكثر من 29 آخرين. لوحة تحكم واحدة لكل أسطول الوكلاء لديك. ([القائمة الكاملة](SUPPORTED_RUNTIMES.txt)، مولّدة من الكتالوج.)

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد →](docs/i18n/)

أمر واحد. بلا أي إعداد. يكتشف كل شيء تلقائيًا.

```bash
pip install clawmetry && clawmetry
```

يُفتح على **http://localhost:8900**. بلا إعداد: يجد أنظمة التشغيل الخاصة بالوكلاء
الموجودة لديك فعلًا، ويقرأها بوضع القراءة فقط، ولا يغيّر أي شيء في طريقة عملها.

![لوحة تحكم ClawMetry: كل نظام تشغيل لوكيل ذكاء اصطناعي على جهاز واحد مع التكلفة خلال 24 ساعة والتكلفة الإجمالية لكل وكيل](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## قبل أن تُثبّت

| | |
|---|---|
| **ما الذي تفعله** | تقرأ ملفات الجلسات والسجلات التي تكتبها وكلاؤك فعلًا. بلا SDK، بلا تغيير في الكود، بلا أي قياس (instrumentation) داخل تطبيقك. |
| **ما الذي تراه** | الخط الزمني للجلسة، إعادة تشغيل الأداة تلو الأخرى، تفصيل الرموز والتكلفة، وإشارات المسار (التكرار اللولبي، الفشل المتكرر) — لكل نظام تشغيل. |
| **ما هو مجاني** | يقرأ `pip install clawmetry` كلًا من **OpenClaw وNVIDIA NemoClaw وGoose وQwen Code** بلا حساب وبلا مفتاح وبلا أي اتصال شبكي. أما الـ28 الأخرى — Claude Code وCodex وCursor وبقية الأنظمة — فتُقرأ عبر مكوّن `clawmetry-pro` المغلق المصدر، الذي يأتي مع فترة التجربة لسبعة أيام أو مع خطة اشتراك — راجع [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) للتفصيل الدقيق. |
| **كيف تبدأ** | `pip install clawmetry && clawmetry`، ثم افتح localhost:8900. لا توجد وكلاء على هذا الجهاز بعد؟ يفتح `clawmetry --sample` على ثلاث جلسات تجريبية موسومة بوضوح. |
| **ما الذي يغادر جهازك** | لا تغادر أي بيانات جلسات، إلا إذا شغّلت `clawmetry connect`. هناك أمران يعملان تلقائيًا بشكل افتراضي، وكلاهما قابل لإيقافه ولا يحمل أي محتوى جلسة: نبضة تثبيت مجهولة الهوية وفحص إصدار على PyPI. كل وجهة مُفصّلة في [docs/EGRESS.md](docs/EGRESS.md)، وأُعيد بناؤها من تحليل حركة الشبكة الفعلية لا من قراءة التعليقات في الكود. |

قيدان يستحقان المعرفة قبل الحكم على المخرجات: أنظمة التشغيل تعرض بيانات
مختلفة جدًا (بعضها لا ينشر أي تكلفة على الإطلاق — [المصفوفة](docs/compatibility.md)
تبيّن أيّها، لكل نظام تشغيل)، ومراقبة إجراء ما ليست كمنع تنفيذه
([أي الضوابط حقيقية فعليًا، لكل نظام تشغيل](docs/APPROVALS.md)).


## يعمل مع 33 نظام تشغيل للوكلاء

**مجاني في التطبيق مفتوح المصدر:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)**

**في خطة مدفوعة:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · 🏛️ **[OpenExecutive](https://clawmetry.com/runtimes/openexecutive)** · ⠿ **[OpenDots](https://clawmetry.com/runtimes/opendots)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

يحصل كل نظام تشغيل على نفس لوحة التحكم. شغّل عدة أنظمة في الوقت نفسه، وسيعيد
مُبدّل العناوين توجيه كل تبويب لأحدها.

بنيت وكيلك الخاص على SDK بدلًا من ذلك؟ يتتبّع المُعترِض (interceptor) استدعاءات
نموذج اللغة لديه أيضًا. راجع [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## ما الذي تحصل عليه

- **الجلسات والمحادثات النصية**: ماذا فعل كل وكيل، دورةً بدورة، مع إعادة التشغيل
- **التكلفة والرموز**: لكل نظام تشغيل ونموذج وجلسة ويوم، مع إشارات الشذوذ
- **التدفق (Flow)**: رسم تخطيطي مباشر للرسائل المتحركة عبر القنوات والنماذج والأدوات
- **العقل (Brain)**: تدفق أحداث الاستدلال واستدعاء الأدوات لحظة حدوثه
- **انفجار السياق**: استخدام النافذة محسوبًا لكل مزوّد، التضام (compaction) مقابل الفائض القسري، بالإضافة إلى خريطة لكل نظام تشغيل توضّح ما *لا* يمكننا رؤيته ([كيف](docs/CONTEXT_BLOWOUT.md))
- **الذاكرة والمهارات**: الملفات والمهارات التي حمّلها كل نظام تشغيل فعليًا
- **الصحة والسجلات**: القرص، الذاكرة، معدلات الأخطاء، حدود المعدل، تدفق السجلات المباشر
- **التنبيهات**: حدود الموازنة، ارتفاعات الأخطاء، انقطاع الوكيل، موجّهة إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **الموافقات**: إيقاف استدعاءات الأدوات الخطرة *قبل* تنفيذها والموافقة من هاتفك ([كيف](docs/APPROVALS.md))

## انفجار السياق، وتكلفة المراقبة

سؤالان يستحقان الإجابة قبل أن تثق بأي أداة مقارنة بين الوكلاء.

**كيف تتعامل مع انفجار نافذة السياق عبر أنظمة التشغيل المختلفة؟**

نسبة الاستخدام لا تكون صادقة إلا بمقدار صدق المقام الذي تُقسَم عليه. تحدّد
ClawMetry حجم النافذة لكل مزوّد من [جدول يمكنك قراءته وتقديم طلب سحب
(PR) له](clawmetry/context_windows.py)، يغطي Anthropic وOpenAI وGoogle وxAI
وDeepSeek وKimi وQwen وMistral وLlama وGLM. فهي لا تقيس جميع أنظمة التشغيل
الـ33 بمسطرة مزوّد واحد. وهذا أمر مهم: دورة بحجم 300K من GPT-5 مُقاسة
بمسطرة Anthropic البالغة 200K تُقرأ على أنها ">100%، منفجرة" بينما هي في
الحقيقة عند 75% من حدّ GPT-5 البالغ 400K. وتخفي نفس المسطرة دورة DeepSeek
منفجرة فعليًا بحجم 130K وتُظهرها كنسبة مريحة قدرها 65%.

تأتي كل نافذة مع مصدرها: `model_table` أو `explicit_marker` أو
`observed_floor`، أو `default` صادق عندما لا نعرف النموذج. المقياس المبني
على تخمين لا يُعرَض بنفس الموثوقية التي يُعرَض بها مقياس مبنيّ على بحث فعلي.

لا يمكن لـClawMetry رؤية أحداث التضام (compaction) إلا على بعض أنظمة
التشغيل. لذا فإن `GET /api/context-coverage` يبيّن، لكل نظام تشغيل، إن كان
**الصفر يعني "اكتمل التشغيل بسلاسة" أو "نحن عاجزون عن الرؤية"**. الصفر
الذي يعني فعليًا العجز عن الرؤية يصرّح بذلك.
[التفاصيل الكاملة](docs/CONTEXT_BLOWOUT.md)

**ما هي تكلفة القياس (instrumentation)؟**

| المسار | المُضاف إلى وكيلك | افتراضي؟ |
|---|---|---|
| تتبّع ملف الجلسة (33 نظام تشغيل جميعًا) | **0**. عملية منفصلة، بلا أي كود من ClawMetry داخل وكيلك | مفعّل |
| المُعترِض HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0.44 مللي ثانية** لكل استدعاء نموذج لغة، أو 0.009% من استدعاء مدته 5 ثوان | معطّل |
| بوابة الخطّاف قبل الأداة (ذاكرة تخزين مؤقت دافئة) | **+44 مللي ثانية** لكل استدعاء أداة مُراقَب، فوق حد مفسِّر مقداره 36 مللي ثانية | معطّل |
| وكيل التطبيق (proxy) للتنفيذ | **+9.7 مللي ثانية** لكل استدعاء نموذج لغة | معطّل |

تكلفة استضافة الخدمة اليومية (daemon): استيعاب **2,762 حدثًا/ثانية**،
و**710 بايت لكل حدث** على القرص (67.7 ميغابايت لكل 100 ألف حدث)، و**نحو
12% من نواة واحدة** بشكل مستمر على تثبيت نشِط. هذا الرقم الأخير يتجاوز
موازنتنا المعلنة البالغة 5-10%، لذا يُنشَر كخلل يجب تتبّعه بدلًا من حذفه
من الصفحة.

قُيس على جهاز Apple M2 Pro باستخدام `benchmarks/overhead.py`. يشغّل هذا
الإطار كل حالة في عملية منفصلة، ويبدّل ترتيبها، و**يرفض طباعة أي رقم عندما
تتعارض الجولات في إشارته**. شغّله على جهازك الخاص في دقيقة واحدة:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

يُقاس كل مسار، بما في ذلك بوابات الخطّاف ووكيل التنفيذ، ويعمل الإطار على
Linux وmacOS وWindows في CI. نتيجتان تستحقان المعرفة: تكلّف وكيل التطبيق
تقريبًا سبع مرات أكثر على Windows مقارنة بـLinux، وتستمر الخدمة اليومية
حاليًا على استخدام نحو 12% من نواة واحدة، متجاوزة موازنتنا البالغة 5-10%.
البيانات الخام بصيغة JSON، والطريقة، وما لم يُقاس بعد موجودة في
[docs/OVERHEAD.md](docs/OVERHEAD.md).

## التسعير

| الخطة | ما تشمله | السعر |
|---|---|---|
| **مجانية** | OpenClaw + NVIDIA NemoClaw + Goose + Qwen Code، لوحة تحكم كاملة، محليًا فقط | 0$ |
| **Starter** | كل نظام تشغيل آخر مذكور أعلاه، عرض الأسطول، مزامنة سحابية | 9$ لكل عقدة / شهريًا |
| **Pro** | Starter + التحكم والتقييم: الموافقات، سياسات خطورة الأدوات، التقييمات، كشف الشذوذ، مُحسِّن التكلفة، تصدير OTel، سجل تدقيق مضاد للتلاعب | 19$ لكل عقدة / شهريًا |

الخطط السنوية وخطة Enterprise والأرقام الحالية موجودة على
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. مفاتيح الترخيص
المُستضافة ذاتيًا تعمل بلا الحاجة للسحابة (`clawmetry license`). التفصيل
الدقيق للمجاني والمدفوع موجود في [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## بياناتك تبقى على جهازك

تقرأ ClawMetry ملفات الجلسات والسجلات المحلية. **لا تغادر أي بيانات جلسة
جهازك إلا إذا شغّلت `clawmetry connect`** — لا مُحفّزات (prompts)، لا ردود،
لا وسائط أدوات، لا محتوى ملفات أو سطور سجلات. وعندما تتصل، تُشفَّر اللقطة
(snapshot) تشفيرًا تامًا من طرف إلى طرف بمفتاح لا يغادر جهازك مطلقًا،
ويُفكّ تشفيرها في متصفحك. إذا لم تملك عقدة ما مفتاحًا، يُتجاوَز الرفع بدلًا
من إرساله بشكل مكشوف، ولا يمكن لأي استجابة من الخادم إيقاف ذلك.

هناك أمران يعملان تلقائيًا بشكل افتراضي قبل الاتصال، وكلاهما قابل لإيقافه
ولا يحمل أي بيانات جلسة: نبضة تثبيت مجهولة الهوية وفحص إصدار مقابل PyPI.
يبحث التثبيت الافتراضي أيضًا عن عنوان IP العام الخاص بك مرة واحدة لسطر
شعار بدء التشغيل. كل وجهة، وما تحمله، وكيفية إيقافها مذكورة في
[docs/EGRESS.md](docs/EGRESS.md)؛ التثبيتات المستضافة ذاتيًا، وذات التوجيه
المعاد، والمعزولة عن الشبكة لا تقوم بأي اتصالات خارجية اختيارية على
الإطلاق.

يحدث فكّ التشفير في متصفحك، في كود نقدّمه لك نحن. كان هذا وعدًا في السابق؛
أما الآن فهو شيء يمكنك التحقق منه. كل سطر يتعامل مع مفتاحك موجود في ملف
واحد يمكن قراءته، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
يُشحَن داخل الـwheel ويُقدَّم كما هو حرفيًا، مُثبَّتًا بتجزئة Subresource
Integrity. للتأكد من أن المتصفح يشغّل ما نشرناه فعليًا:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ما لا يثبته ذلك: نحن نقدّم الصفحة التي تحمّل الملف، بحيث يمكننا تقديم صفحة
مختلفة. تجزئات التكامل تحميك من شبكة توصيل محتوى (CDN) مخترقة، لا من
المزوّد نفسه. ما تكسبه هو أن أي استبدال يجب أن يكون متعمدًا، وظاهرًا في
مصدر الصفحة، ومختلفًا عن النسخة المنشورة على PyPI التي يمكن لأي شخص جلبها.
الاستضافة الذاتية أو البقاء محليًا فقط يزيل هذا الاعتماد كليًا.

## التثبيت

```bash
pip install clawmetry     # ثم: clawmetry
```

أو السطر الواحد: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

يحتاج Python 3.8+ على macOS أو Linux أو Windows، وعلى الأقل نظام تشغيل
وكيل واحد على نفس الجهاز. تعليمات Docker: [docs/DOCKER.md](docs/DOCKER.md).

أو اترك الوكيل يثبّته لك. تعلّم مهارة [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
كلًا من Claude Code وCodex وCursor وGemini CLI وCopilot أو OpenCode كيفية
تثبيت ClawMetry، والإبلاغ عن ما تفعله الوكلاء على الجهاز وما تنفقه، وإيقاف
جلسة واحدة عند الطلب، وتعليق استدعاءات الأدوات الخطرة بانتظار الموافقة:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## الوثائق

| | |
|---|---|
| [توافق أنظمة التشغيل](docs/compatibility.md) | ما يقرأه كل مكيّف (adapter)، وكيفية إضافة نظام تشغيل |
| [انفجار السياق](docs/CONTEXT_BLOWOUT.md) | النوافذ لكل مزوّد، التضام مقابل الفائض، التغطية لكل نظام تشغيل |
| [الحمل الزائد (Overhead)](docs/OVERHEAD.md) | تكلفة القياس، مقاسة فعليًا، مع الإطار اللازم لإعادة إنتاجها |
| [الاستحقاقات](docs/ENTITLEMENTS.md) | المجاني مقابل المدفوع، مصفوفة المستويات، واجهة سطر أوامر الترخيص |
| [الموافقات والسياسات](docs/APPROVALS.md) | البوابة قبل التنفيذ، تصنيف الخطورة، الموافقات من الهاتف |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صدّر الآثار (traces) إلى أي مكان، واستوعب OTLP من أي مصدر |
| [إحضار وكيلك الخاص](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore وPydantic AI وLangChain من البداية إلى النهاية، مع أمثلة قابلة للتشغيل |
| [تتبّع SDK](docs/SDK_TRACKING.md) | إسناد التكلفة للوكلاء الذين بنيتهم بنفسك |
| [قنوات الدردشة](docs/CHANNELS.md) | مكيّفات الدردشة المعروضة في التدفق (Flow) |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | إعدادات NVIDIA NemoClaw المعزولة (sandboxed) |
| [Docker](docs/DOCKER.md) | الصورة، compose، ربط الأحجام |
| [البنية المعمارية](ARCHITECTURE.md) · [التطوير](docs/DEVELOPMENT.md) | كيف تعمل من الداخل؛ التشغيل من المصدر |
| [التليمتري](docs/TELEMETRY.md) | نبضات التثبيت وفتح سطح المكتب المجهولة الهوية، وكيفية إيقافها |

## لقطات شاشة

كل رقم أدناه مأخوذ من جهاز حقيقي واحد، بوضع القراءة فقط، بلا أي بيانات
مُدرَجة مسبقًا.

**تُخبرك عندما يكون هناك خطأ ما، لا فقط بما حدث.**
شريطا شذوذ في الأعلى: إنفاق يسير بمعدل 7 أضعاف المتوسط اليومي، وارتفاع
تكلفة بمقدار 4.2 أضعاف. تحتهما، 324 من 667 جلسة حديثة تحمل إشارة هدر،
مُصنّفة حسب السبب.

![نظرة عامة: شريطا شذوذ الإنفاق وارتفاع التكلفة فوق عمل وكيل مباشر](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**تُظهر لك إلى أين ذهبت الأموال، في كل نافذة زمنية.**
252.47$ اليوم، و513.15$ هذا الأسبوع، و1,312.92$ هذا الشهر، كلّ منها مع
الرموز المسؤولة عنه وكمّ ما يغطيه اشتراكك فعليًا. تحت ذلك، نحو 1,128$/شهريًا
مُصنّفة كقابلة للاسترداد، و17,256$/شهريًا تم توفيرها فعليًا بإعادة استخدام
التخزين المؤقت (cache).

![التكلفة: اليوم والأسبوع والشهر، مع تقييم كفاءة وأفكار توفير مُصنّفة](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ترسم كيف تتحول الرسالة إلى إجابة.**
الرسم التخطيطي المباشر للتدفق: أنت، والقناة التي وصلت عبرها، والبوابة،
والنموذج الذي يجيب الآن، وكل أداة توجّه إليها. تضيء العُقَد كلما تحرّك
العمل عبرها.

![التدفق: رسم تخطيطي مباشر منك عبر البوابة إلى النموذج وأدواته](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**كل وكيل على الجهاز، في جدول واحد.**
ما يشغّله، وما يكلّفه خلال آخر 24 ساعة وعلى مدى عمره، وآخر مرة شوهد فيها،
ومن يملكه، وما إذا كان اشتراك يغطي الفاتورة. 14 وكيلًا هنا، 3 جلسات تعمل،
13 هادئة.

![الوكلاء: كل نظام تشغيل على الجهاز مع التكلفة والمالك وآخر مرة شوهد والعمل الحالي](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**تُظهر إلى أين ذهب وقت الدورة ومالها، أداةً تلو الأخرى.**
دورة واحدة من جلسة حقيقية: 11 أداة في 11.2 دقيقة بتكلفة 1.16$. يحصل كل
استدعاء Bash واستدعاء نموذج على شريطه الخاص على الخط الزمني، بحيث يمكن
التمييز بنظرة واحدة بين الأمر الذي استمر 4.1 دقائق والآخر الذي استمر 226
مللي ثانية.

![الجلسات: دورة واحدة لوكيل على خط زمني، كل استدعاء أداة بمدته الخاصة وتكلفة الدورة](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**تُقيّم العمل، لا الإنفاق فقط.**
تقدير A هذا الأسبوع: 54 مهمة عادت نظيفة، ومهمتان صعبتان كلّفتا 48.57$،
والتشغيلات ذات النشاط القليل جدًا بحيث لا يمكن تقييمها تُستثنى من التقدير
بدلًا من حسابها كانتصارات. كل تشغيل صعب يرتبط بأثره (trace) الخاص.

![الجودة: تقرير الأداء لهذا الأسبوع مع التشغيلات الصعبة وتكلفتها](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**تُظهر لماذا تستمر نافذة السياق في الامتلاء.**
715 ألف رمز من نافذة بحجم مليون رمز في آخر دورة، وقمّة بلغت 83.3%، و4
عمليات تضام (compactions) جميعها انطلقت بشكل استباقي بدلًا من استجابةً
لفائض، بالإضافة إلى استخدام كل دورة سابقة.

![استخدام السياق: استخدام النافذة لكل دورة، أحداث التضام والرموز المُستعادة](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**يعمل الكشف بلا أي إعداد منك.**
كاشفات مدمجة مفعّلة منذ التثبيت: الوكيل أصبح صامتًا، توقّف تغذية التليمتري،
ارتفاع التكلفة، دفعة رموز مفاجئة، تصاعد الأخطاء، ارتفاع الأخطاء، تجاوز حد
الموازنة، تطابق توقيع تهديد، نتيجة أداة أمنية، تغيّر الوضع الأمني. قواعدك
الخاصة اختيارية فوق ذلك.

![التنبيهات: كاشفات مدمجة بالإضافة إلى قواعد مخصصة اختيارية](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**تعليق استدعاء خطر اختياري، ويُشحَن مُعطَّلًا.**
الحذف التكراري، الدفع القسري (force push)، sudo، الأسرار، تثبيت الحزم،
والاستدعاءات الصادرة تحصل كل منها على قاعدة يمكنك تفعيلها. حتى تفعّلها،
تراقب ClawMetry ولا تغيّر شيئًا. وحالما تُفعَّل واحدة، تنتظر الاستدعاءات
المطابقة هنا (أو على هاتفك) موافقة أو رفضًا.

![الموافقات: قواعد حماية لاستدعاءات الأدوات الخطرة، جميعها معطّلة حتى تفعّلها](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

المزيد، لكل نظام تشغيل: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## التقدير

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>


## سجل النجوم

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
