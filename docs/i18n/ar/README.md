<!-- i18n-src:12b97259721e -->
> العربية translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

**يمكن لوكيل أن ينفّذ مئات من استدعاءات الأدوات دون أن يحقق أي تقدم.** تقرأ ClawMetry ملفات الجلسات التي تكتبها وكلاء الترميز لديك بالفعل، وتضع المخطط الزمني، واستدعاءات الأدوات، وأي بيانات عن الرموز (tokens) والتكلفة يكشف عنها بيئة التشغيل في عرض واحد — بحيث يمكنك التمييز بين تشغيل طويل يعمل بنجاح وآخر متعطّل.

يعمل مع **31 بيئة تشغيل لوكلاء الذكاء الاصطناعي** — Claude Code، OpenAI Codex، Hermes، OpenClaw و27 أخرى. لوحة تحكم واحدة لكل أسطول وكلائك. ([القائمة الكاملة](SUPPORTED_RUNTIMES.txt)، مُولَّدة من الكتالوج.)

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد →](docs/i18n/)

أمر واحد. بلا أي إعداد. يكتشف كل شيء تلقائيًا.

```bash
pip install clawmetry && clawmetry
```

يُفتح على **http://localhost:8900**. بلا أي إعداد: يجد بيئات تشغيل الوكلاء الموجودة لديك بالفعل، يقرأها بصلاحية قراءة فقط، ولا يغيّر شيئًا في طريقة عملها.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## قبل أن تُثبّت

| | |
|---|---|
| **ماذا تفعل** | تقرأ ملفات الجلسات والسجلات التي تكتبها وكلاؤك بالفعل. لا SDK، ولا تعديل في الكود، ولا أي أداة قياس مضمّنة في تطبيقك. |
| **ما الذي تراه** | المخطط الزمني للجلسة، إعادة تشغيل أداة بأداة، تفصيل الرموز والتكلفة، وإشارات المسار (التكرار، الفشل المتكرر) — لكل بيئة تشغيل. |
| **ما هو مجاني** | `pip install clawmetry` يقرأ **OpenClaw و NVIDIA NemoClaw و Goose** بلا حساب، بلا مفتاح وبلا أي استدعاء شبكي. أما الـ27 الأخرى — Claude Code و Codex و Cursor وما تبقّى — فتُقرأ عبر الإضافة المغلقة المصدر `clawmetry-pro`، التي تأتي مع النسخة التجريبية لمدة 7 أيام أو مع خطة اشتراك — انظر [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) للتقسيم الدقيق. |
| **كيف تبدأ** | `pip install clawmetry && clawmetry`، ثم افتح localhost:8900. لا توجد وكلاء على هذا الجهاز بعد؟ `clawmetry --sample` يفتح على ثلاث جلسات تجريبية موسومة. |
| **ما الذي يغادر جهازك** | لا تغادر أي بيانات جلسة جهازك، إلا إذا شغّلت `clawmetry connect`. يوجد أمران يعملان بشكل افتراضي، كلاهما يمكن إلغاؤه (opt-out) ولا يحمل أي منهما محتوى الجلسة: نبضة تثبيت مجهولة الهوية وفحص إصدار عبر PyPI. كل وجهة موثّقة في [docs/EGRESS.md](docs/EGRESS.md)، أُعيد بناؤها من تحليل حركة الشبكة لا من قراءة التعليقات. |

هناك حدّان يستحقان المعرفة قبل الحكم على المخرجات: بيئات التشغيل تكشف عن بيانات مختلفة جدًا (بعضها لا يُصدر أي تكلفة على الإطلاق — [المصفوفة](docs/compatibility.md) توضّح أيّها، لكل بيئة تشغيل)، ومراقبة إجراء ما لا تعني القدرة على منعه ([أيّ عناصر التحكم حقيقية، لكل بيئة تشغيل](docs/APPROVALS.md)).


## تعمل مع 31 بيئة تشغيل للوكلاء

**مجانية في التطبيق مفتوح المصدر:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**في خطة مدفوعة:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · 🎭 **[Muse Code](https://clawmetry.com/runtimes/muse-code)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

كل بيئة تشغيل تحصل على لوحة التحكم نفسها. شغّل عدّة بيئات في آنٍ واحد، ومحوّل الرأس يعيد تحديد نطاق كل تبويب لواحدة منها.

بنيت وكيلك الخاص على SDK بدلًا من ذلك؟ أداة الاعتراض (interceptor) تتتبّع استدعاءات LLM الخاصة به أيضًا. انظر [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## ما الذي تحصل عليه

- **الجلسات والنصوص (transcripts)**: ما فعله كل وكيل، دورًا بدور، مع إعادة التشغيل
- **التكلفة والرموز**: لكل بيئة تشغيل، موديل، جلسة ويوم، مع إشارات الشذوذ
- **التدفق (Flow)**: مخطط مباشر للرسائل المتحركة عبر القنوات والموديلات والأدوات
- **العقل (Brain)**: تدفق أحداث الاستدلال واستدعاء الأدوات كما يحدث
- **انفجار السياق**: استخدام النافذة مُحجَّم لكل مزوّد، التضغيط (compaction) مقابل الفائض القسري، بالإضافة إلى خريطة لكل بيئة تشغيل توضّح ما *لا* نستطيع رؤيته ([كيف](docs/CONTEXT_BLOWOUT.md))
- **الذاكرة والمهارات**: الملفات والمهارات التي حمّلتها كل بيئة تشغيل بالفعل
- **الصحة والسجلات**: القرص، الذاكرة، معدلات الأخطاء، حدود المعدّل، تدفق السجلات المباشر
- **التنبيهات**: حدود الموازنة، ارتفاعات الأخطاء، خروج الوكيل عن الاتصال، موجّهة إلى Slack، Discord، PagerDuty، Telegram، البريد الإلكتروني
- **الموافقات**: إيقاف استدعاءات الأدوات الخطرة *قبل* تنفيذها والموافقة عليها من هاتفك ([كيف](docs/APPROVALS.md))

## انفجار السياق، وما تكلفه المراقبة

سؤالان يستحقان الإجابة قبل أن تثق بأي أداة مقارنة بين الوكلاء.

**كيف تتعامل مع انفجار نافذة السياق عبر بيئات التشغيل المختلفة؟**

نسبة الاستخدام صادقة بقدر ما يكون المقام الذي تُقسَّم عليه صادقًا. تحدّد ClawMetry حجم النافذة لكل مزوّد من [جدول يمكنك قراءته وتقديم طلب دمج (PR) له](clawmetry/context_windows.py)، يشمل Anthropic و OpenAI و Google و xAI و DeepSeek و Kimi و Qwen و Mistral و Llama و GLM. لا تقيس الـ31 بيئة تشغيل كلها بمسطرة مزوّد واحد. هذا مهم: دور بحجم 300 ألف رمز في GPT-5 يُقاس بمقياس Anthropic البالغ 200 ألف يُقرأ ">100%، منفجر" بينما هو في الحقيقة عند 75% من 400 ألف الخاصة بـ GPT-5. نفس المسطرة تخفي دورًا فعليًا منفجرًا بحجم 130 ألف في DeepSeek كأنه 65% مريحة.

كل نافذة تأتي مع مصدرها: `model_table`، أو `explicit_marker`، أو `observed_floor`، أو `default` صادق عندما لا نعرف الموديل. مقياس مبني على تخمين لا يُعرض بنفس سلطة مقياس مبني على بحث فعلي.

لا تستطيع ClawMetry رؤية أحداث التضغيط (compaction) إلا في بعض بيئات التشغيل. لذلك يُقدّم `GET /api/context-coverage` تقريرًا، لكل بيئة تشغيل، عن كون **الصفر يعني "اكتمل بنجاح" أو "نحن عاجزون عن الرؤية"**. صفر يعني فعليًا العجز عن الرؤية يُفصَح عنه كذلك.
[التفاصيل الكاملة](docs/CONTEXT_BLOWOUT.md)

**ما الذي تكلّفه أداة القياس؟**

| المسار | ما يُضاف إلى وكيلك | افتراضي؟ |
|---|---|---|
| تتبّع ملفات الجلسة (كل الـ31 بيئة تشغيل) | **صفر**. عملية مستقلة، بلا أي كود لـ ClawMetry داخل وكيلك | مُفعّل |
| أداة الاعتراض عبر HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ملي ثانية** لكل استدعاء LLM، أو 0.009% من استدعاء مدته 5 ثوانٍ | مُعطَّل |
| بوابة الخطاف قبل الأداة (ذاكرة تخزين مؤقت دافئة) | **+44 ملي ثانية** لكل استدعاء أداة خاضع للبوابة، فوق حدّ مفسِّر قدره 36 ملي ثانية | مُعطَّل |
| وكيل التطبيق (proxy) للفرض | **+9.7 ملي ثانية** لكل استدعاء LLM | مُعطَّل |

تكلفة استضافة الخدمة الخلفية (daemon): **2,762 حدثًا/ثانية** استيعابًا، **710 بايت/حدث** على القرص (67.7 ميغابايت لكل 100 ألف حدث)، و**نحو 12% من نواة واحدة** مستمرة على تثبيت نشط. هذا الرقم الأخير يتجاوز موازنتنا المعلنة البالغة 5-10%، فهو منشور كخلل يجب تتبّعه وليس مُسقطًا من الصفحة.

قِيس على Apple M2 Pro باستخدام `benchmarks/overhead.py`. يُشغّل الجهاز كل حالة في عملية منفصلة، يبدّل ترتيبها، و**يرفض طباعة رقم عندما تتعارض الجولات في علامته (الزيادة أو النقصان)**. شغّله على جهازك الخاص في دقيقة واحدة:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

يُقاس كل مسار، بما فيه بوابات الخطاف ووكيل التطبيق للفرض، ويُشغَّل الجهاز على Linux و macOS و Windows في CI. نتيجتان تستحقان المعرفة: تكلفة وكيل التطبيق أعلى بنحو سبع مرات على Windows مقارنة بـ Linux، والخدمة الخلفية تستهلك حاليًا نحو 12% من نواة واحدة، متجاوزة موازنتنا البالغة 5-10%. البيانات الخام بصيغة JSON، والمنهجية، وما لم يُقاس بعد موجودة في [docs/OVERHEAD.md](docs/OVERHEAD.md).

## التسعير

| الخطة | ما تغطيه | السعر |
|---|---|---|
| **مجانية** | OpenClaw + NVIDIA NemoClaw + Goose، لوحة تحكم كاملة، محلية فقط | $0 |
| **Starter** | كل بيئة تشغيل أخرى أعلاه، عرض الأسطول، مزامنة سحابية | 9$ لكل عقدة / شهريًا |
| **Pro** | Starter + التحكم والتقييم: الموافقات، سياسات خطورة الأدوات، التقييمات، اكتشاف الشذوذ، مُحسِّن التكلفة، تصدير OTel، سجل تدقيق مضاد للتلاعب | 19$ لكل عقدة / شهريًا |

الخطط السنوية، خطة Enterprise والأرقام الحالية موجودة على
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. مفاتيح الترخيص المُستضافة ذاتيًا تعمل دون الحاجة إلى السحابة (`clawmetry license`). التقسيم الدقيق بين المجاني والمدفوع موجود في [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## بياناتك تبقى على جهازك

تقرأ ClawMetry ملفات الجلسات والسجلات المحلية. **لا تغادر أي بيانات جلسة صندوقك
إلا إذا شغّلت `clawmetry connect`** — لا مطالبات (prompts)، ولا ردود، ولا وسائط أدوات، ولا محتوى ملفات
أو سطور سجلات. عندما تتصل فعلًا، تكون اللقطة مشفّرة من طرف إلى طرف
بمفتاح لا يغادر جهازك أبدًا، ويُفكّ تشفيرها في متصفحك. إذا كانت إحدى
العقد بلا مفتاح، يُتجاوَز الرفع بدلًا من إرساله دون تشفير، ولا يمكن
لأي استجابة خادم تعطيل ذلك.

يوجد أمران يعملان بشكل افتراضي قبل الاتصال، كلاهما يمكن إلغاؤه (opt-out) ولا يحمل أي منهما
بيانات الجلسة: نبضة تثبيت مجهولة الهوية وفحص إصدار مقابل
PyPI. التثبيت الافتراضي يبحث أيضًا عن عنوان IP العام الخاص بك مرة واحدة لسطر
لافتة بدء التشغيل. كل وجهة، وما تحمله وكيفية تعطيلها مذكورة في
[docs/EGRESS.md](docs/EGRESS.md)؛ التثبيتات المُستضافة ذاتيًا، المُعاد توجيهها والمنعزلة عن الشبكة
لا تقوم بأي استدعاءات صادرة اختيارية على الإطلاق.

يحدث فكّ التشفير في متصفحك، في كود نقدّمه لك. كان هذا وعدًا في السابق؛
أصبح الآن أمرًا يمكنك التحقق منه. كل سطر يتعامل مع مفتاحك
موجود في ملف واحد قابل للقراءة، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)،
الذي يُشحن داخل الحزمة (wheel) ويُقدَّم حرفيًا، مُثبّتًا بتجزئة سلامة المصدر الفرعي
(Subresource Integrity). للتأكد من أن المتصفح يُشغّل ما نشرناه:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ما لا يثبته ذلك: نحن نقدّم الصفحة التي تُحمّل الملف، فيمكننا أن نقدّم
صفحة مختلفة. تجزئات السلامة تحميك من شبكة توصيل محتوى (CDN) مُخترقة،
لا من المزوّد نفسه. ما تحصل عليه هو أن أي استبدال يجب أن يكون
متعمَّدًا، مرئيًا في مصدر الصفحة، ومختلفًا عن أداة منشورة على PyPI
يمكن لأي شخص جلبها. الاستضافة الذاتية أو البقاء محليًا بالكامل يزيل
هذا الاعتماد تمامًا.

## التثبيت

```bash
pip install clawmetry     # ثم: clawmetry
```

أو السطر الواحد: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

يتطلب Python 3.8+ على macOS أو Linux أو Windows، وعلى الأقل بيئة تشغيل وكيل واحدة على
الجهاز نفسه. تعليمات Docker: [docs/DOCKER.md](docs/DOCKER.md).

أو اجعل الوكيل يُثبّته لك. مهارة [`agent-kill-switch`](skills/agent-kill-switch/SKILL.md)
تعلّم Claude Code أو Codex أو Cursor أو Gemini CLI أو Copilot أو OpenCode
تثبيت ClawMetry، والإبلاغ عن ما تفعله وتنفقه الوكلاء على الجهاز،
وإيقاف جلسة واحدة عند الطلب، وإيقاف استدعاءات الأدوات الخطرة لانتظار الموافقة:

```bash
npx skills add vivekchand/clawmetry --skill agent-kill-switch
```

## الوثائق

| | |
|---|---|
| [توافق بيئات التشغيل](docs/compatibility.md) | ما تقرأه كل إضافة، وكيفية إضافة بيئة تشغيل |
| [انفجار السياق](docs/CONTEXT_BLOWOUT.md) | النوافذ لكل مزوّد، التضغيط مقابل الفائض، التغطية لكل بيئة تشغيل |
| [الحمل الزائد (Overhead)](docs/OVERHEAD.md) | ما تكلّفه أداة القياس، مُقاسة، مع الأداة اللازمة لإعادة إنتاجها |
| [الاستحقاقات (Entitlements)](docs/ENTITLEMENTS.md) | المجاني مقابل المدفوع، مصفوفة الفئات، أداة سطر أوامر الترخيص |
| [الموافقات والسياسات](docs/APPROVALS.md) | الفحص قبل التنفيذ، تسجيل درجة الخطورة، الموافقات عبر الهاتف |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صدّر المسارات (traces) إلى أي مكان، استوعب OTLP من أي مصدر |
| [اجلب وكيلك الخاص](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، Pydantic AI، LangChain من البداية للنهاية، مع أمثلة قابلة للتشغيل |
| [تتبّع SDK](docs/SDK_TRACKING.md) | إسناد التكلفة للوكلاء التي بنيتها بنفسك |
| [قنوات الدردشة](docs/CHANNELS.md) | إضافات الدردشة المعروضة في التدفق (Flow) |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | إعدادات NVIDIA NemoClaw المعزولة (sandboxed) |
| [Docker](docs/DOCKER.md) | الصورة، التركيب (compose)، تركيب وحدات التخزين |
| [البنية](ARCHITECTURE.md) · [التطوير](docs/DEVELOPMENT.md) | كيف تعمل من الداخل؛ التشغيل من المصدر |
| [التلمتري (Telemetry)](docs/TELEMETRY.md) | نبضات التثبيت المجهولة الهوية وفتح سطح المكتب، وكيفية تعطيلها |

## لقطات الشاشة

كل رقم أدناه من جهاز حقيقي واحد، بصلاحية قراءة فقط، دون أي تمهيد (seeding).

**تُخبرك عندما يكون هناك خطأ، لا فقط بما حدث.**
لافتتا شذوذ في الأعلى: إنفاق يعمل بمعدل 7 أضعاف المتوسط اليومي، وارتفاع
تكلفة بمعدل 4.2 ضعف. تحتهما، 324 من أصل 667 جلسة حديثة تحمل إشارة
هدر، مُفصَّلة بحسب السبب.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**تُظهر لك إلى أين ذهب المال، في كل نافذة زمنية.**
252.47$ اليوم، 513.15$ هذا الأسبوع، 1,312.92$ هذا الشهر، كل منها مع الرموز
التي خلفه وكم منها تغطّيه اشتراكك بالفعل. تحت ذلك، نحو 1,128$/شهريًا
مُفصَّلة كقابلة للاستعادة و17,256$/شهريًا موفّرة فعليًا عبر إعادة استخدام
التخزين المؤقت (cache).

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ترسم كيف تتحوّل الرسالة إلى إجابة.**
مخطط التدفق المباشر: أنت، القناة التي وصلت عبرها، البوابة (gateway)، الموديل
الذي يجيب الآن، وكل أداة استخدمها. العُقَد تُضيء بينما يتحرك العمل خلالها.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**كل وكيل على الجهاز، في جدول واحد.**
ما الذي يشغّله، كلفته خلال آخر 24 ساعة وعلى مدى عمره، آخر مرة شُوهد
فيها، من يملكه، وهل يغطّي اشتراك ما فاتورته. 14 وكيلًا هنا، 3 جلسات
تعمل، 13 هادئة.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**تُظهر إلى أين ذهب وقت ومال الدور، أداة بأداة.**
دور واحد من جلسة حقيقية: 11 أداة في 11.2 دقيقة بتكلفة 1.16$. كل استدعاء
Bash واستدعاء موديل يحصل على شريطه الخاص على المخطط الزمني، بحيث يُميَّز
الأمر الذي استمر 4.1 دقائق عن الذي استمر 226 ملي ثانية بنظرة واحدة.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**تُقيّم جودة العمل، لا الإنفاق فقط.**
درجة A هذا الأسبوع: 54 مهمة عادت نظيفة، مهمتان صعبتان كلّفتا 48.57$،
والتشغيلات التي لم يكن فيها نشاط كافٍ للحكم عليها استُبعدت من الدرجة
بدلًا من حسابها كانتصارات. كل تشغيل صعب يرتبط بمساره (trace).

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**تُظهر لماذا تستمر نافذة السياق في الامتلاء.**
715 ألف من نافذة بحجم مليون رمز في الدور الأخير، قمّة 83.3%، 4 عمليات
تضغيط أُطلقت جميعها بشكل استباقي وليس عند الفائض، واستخدام كل دور
خلفها.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**يعمل الاكتشاف دون أن تُعدّ أي شيء.**
أدوات الاكتشاف المدمجة مُفعّلة من التثبيت: الوكيل أصبح صامتًا، توقّف تغذية
التلمتري، ارتفاع التكلفة، انفجار الرموز، ارتفاع الأخطاء تدريجيًا، ارتفاع حادّ
في الأخطاء، تجاوز حدّ الموازنة، تطابق توقيع تهديد، نتيجة أداة أمنية، تغيّر
في وضعية الأمان. قواعدك الخاصة اختيارية فوق ذلك.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**إيقاف استدعاء خطر اختياري، ويُشحن مُعطَّلًا.**
الحذف التكراري، الدفع القسري (force push)، sudo، الأسرار، تثبيت الحِزَم
والاستدعاءات الصادرة، كل منها يحصل على قاعدة يمكنك تفعيلها. إلى أن تفعلها،
تراقب ClawMetry ولا تغيّر شيئًا. بعد تفعيل واحدة، تنتظر الاستدعاءات المطابقة هنا
(أو على هاتفك) للموافقة أو الرفض.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

المزيد، لكل بيئة تشغيل: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## التقدير

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

MIT · بُني من قِبل [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
