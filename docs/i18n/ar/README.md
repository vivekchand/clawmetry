<!-- i18n-src:9767c8001c9c -->
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

**شاهد وكيلك وهو يفكر.** مراقبة فورية لـ **30 بيئة تشغيل لوكلاء الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw)‏، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)‏، Claude Code‏، OpenAI Codex و26 غيرها. لوحة تحكم واحدة لأسطول وكلائك بأكمله.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بلا إعداد. يكتشف كل شيء تلقائيًا.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900**. بلا إعداد: يجد بيئات تشغيل الوكلاء الموجودة لديك بالفعل، يقرأها للقراءة فقط، ولا يغيّر شيئًا في طريقة عملها.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## يعمل مع 30 بيئة تشغيل للوكلاء

**مجانًا في التطبيق مفتوح المصدر:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**في خطة مدفوعة:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

تحصل كل بيئة تشغيل على نفس لوحة التحكم. شغّل عدة بيئات في آن واحد، ويعيد مُبدّل الرأس تحديد نطاق كل تبويب لواحدة منها.

هل بنيت وكيلك الخاص باستخدام SDK بدلًا من ذلك؟ يتتبع المعترض (interceptor) استدعاءات نموذج اللغة الخاصة به أيضًا. راجع [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## ما الذي تحصل عليه

- **الجلسات والنصوص**: ما قام به كل وكيل، دورة بدورة، مع إعادة التشغيل
- **التكلفة والرموز**: لكل بيئة تشغيل، ونموذج، وجلسة، ويوم، مع إشارات الشذوذ
- **التدفق (Flow)**: مخطط حي للرسائل وهي تتحرك عبر القنوات والنماذج والأدوات
- **العقل (Brain)**: تدفق أحداث التفكير واستدعاء الأدوات لحظة حدوثه
- **انفجار السياق**: استغلال نافذة السياق مُقاسة حسب المزوّد، الضغط (compaction) مقابل الفيض القسري، بالإضافة إلى خريطة لكل بيئة تشغيل توضح ما *لا* يمكننا رؤيته ([كيف](docs/CONTEXT_BLOWOUT.md))
- **الذاكرة والمهارات**: الملفات والمهارات التي حمّلتها كل بيئة تشغيل فعليًا
- **الصحة والسجلات**: القرص، الذاكرة، معدلات الأخطاء، حدود المعدل، تدفق سجل حي
- **التنبيهات**: حدود الميزانية، ارتفاعات الأخطاء، عدم اتصال الوكيل، موجّهة إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **الموافقات**: أوقف استدعاءات الأدوات الخطرة *قبل* تنفيذها ووافق عليها من هاتفك ([كيف](docs/APPROVALS.md))

## انفجار السياق، وتكلفة المراقبة

سؤالان يستحقان الإجابة قبل أن تثق بأي أداة لمقارنة الوكلاء.

**كيف يتعامل مع انفجار نافذة السياق عبر بيئات التشغيل؟**

نسبة الاستغلال صادقة بقدر صدق ما تُقسَّم عليه. يحدد ClawMetry حجم النافذة لكل مزوّد من [جدول يمكنك قراءته وإرسال طلب سحب له](clawmetry/context_windows.py)، ويغطي Anthropic وOpenAI وGoogle وxAI وDeepSeek وKimi وQwen وMistral وLlama وGLM. فهو لا يقيس جميع بيئات التشغيل الـ26 بمسطرة مزوّد واحد. هذا مهم: دورة GPT-5 بحجم 300 ألف رمز عند قياسها بمسطرة Anthropic البالغة 200 ألف تُقرأ على أنها ">100%، منفجرة" بينما هي في الواقع عند 75% من الـ400 ألف الخاصة بـ GPT-5. المسطرة نفسها تُخفي دورة DeepSeek منفجرة فعليًا بحجم 130 ألفًا وتظهرها كأنها 65% مريحة.

كل نافذة تأتي مع مصدرها: `model_table`، أو `explicit_marker`، أو `observed_floor`، أو `default` صادق عندما لا نعرف النموذج. مقياس مبني على تخمين لا يظهر بنفس مصداقية مقياس مبني على بحث فعلي.

لا يستطيع ClawMetry رؤية أحداث الضغط (compaction) إلا في بعض بيئات التشغيل. لذلك يُبلغ `GET /api/context-coverage`، لكل بيئة تشغيل، عمّا إذا كان **الصفر يعني "عملت بسلاسة" أو "نحن عميان"**. الصفر الذي يعني فعليًا العمى يُصرَّح بذلك.
[التفاصيل الكاملة](docs/CONTEXT_BLOWOUT.md)

**ما هي تكلفة الأداة نفسها؟**

| المسار | المُضاف إلى وكيلك | افتراضي؟ |
|---|---|---|
| متابعة ملف الجلسة (كل الـ30 بيئة تشغيل) | **0**. عملية منفصلة، بلا أي كود من ClawMetry في وكيلك | مفعّل |
| معترض HTTP (`CLAWMETRY_INTERCEPT=1`) | **+0.44 مللي ثانية** لكل استدعاء نموذج لغة، أو 0.009% من استدعاء مدته 5 ثوانٍ | معطّل |
| بوابة الخطاف قبل الأداة (ذاكرة تخزين مؤقت دافئة) | **+44 مللي ثانية** لكل استدعاء أداة مُبوَّب، فوق حد أرضية مفسّر 36 مللي ثانية | معطّل |
| وكيل التنفيذ (proxy) | **+9.7 مللي ثانية** لكل استدعاء نموذج لغة | معطّل |

تكلفة استضافة العفريت (daemon): **2,762 حدثًا/ثانية** استيعابًا، **710 بايت/حدث** على القرص (67.7 ميغابايت لكل 100 ألف حدث)، و**نحو 12% من نواة واحدة** بشكل مستمر على تثبيت مزدحم. هذا الرقم الأخير يتجاوز ميزانيتنا المُعلنة البالغة 5-10%، لذلك يُنشر كخطأ يجب ملاحقته بدلًا من إغفاله عن الصفحة.

قِيس على جهاز Apple M2 Pro باستخدام `benchmarks/overhead.py`. يُشغّل الإطار كل حالة في عملية منفصلة، ويُبدّل ترتيبها، و**يرفض طباعة رقم عندما تختلف الجولات في إشارته**. شغّله على جهازك الخاص في دقيقة واحدة:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

كل مسار مقيس، بما في ذلك بوابات الخطاف ووكيل التنفيذ، ويعمل الإطار على Linux وmacOS وWindows في CI. نتيجتان تستحقان المعرفة: تكلفة الوكيل (proxy) أعلى بنحو سبعة أضعاف على Windows مقارنة بـ Linux، ويستهلك العفريت حاليًا نحو 12% من نواة واحدة، متجاوزًا ميزانيتنا الخاصة البالغة 5-10%. البيانات الخام بصيغة JSON، والمنهجية، وما لم يُقاس بعد، موجودة في [docs/OVERHEAD.md](docs/OVERHEAD.md).

## التسعير

| الخطة | ما تغطيه | السعر |
|---|---|---|
| **مجانية** | OpenClaw + NVIDIA NemoClaw + Goose، لوحة تحكم كاملة، محليًا فقط | 0$ |
| **مبتدئة (Starter)** | كل بيئة تشغيل أخرى مذكورة أعلاه، عرض الأسطول، مزامنة سحابية | 9$ لكل عقدة / شهريًا |
| **Pro** | Starter + التحكم والتقييم: الموافقات، سياسات مخاطر الأدوات، التقييمات، كشف الشذوذ، مُحسِّن التكلفة، تصدير OTel، سجل تدقيق مقاوم للعبث | 19$ لكل عقدة / شهريًا |

الخطط السنوية والمؤسسات والأرقام الحالية موجودة على
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. مفاتيح الترخيص للاستضافة الذاتية تعمل دون السحابة (`clawmetry license`). التقسيم الدقيق بين المجاني والمدفوع موجود في [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## بياناتك تبقى على جهازك

يقرأ ClawMetry ملفات الجلسات والسجلات المحلية. **لا تغادر بيانات الجلسة جهازك
إلا إذا شغّلت `clawmetry connect`** — لا مطالبات، ولا ردود، ولا وسائط أدوات، ولا محتوى ملفات ولا أسطر سجلات. عند الاتصال، تُشفّر اللقطة تشفيرًا شاملًا (end-to-end) بمفتاح لا يغادر جهازك أبدًا، ويُفك تشفيرها في متصفحك. إذا لم تمتلك عقدة مفتاحًا، يُتخطى الرفع بدلًا من إرساله بشكل غير مشفّر، ولا يمكن لأي استجابة من الخادم تغيير ذلك.

هناك أمران يعملان افتراضيًا قبل الاتصال، كلاهما اختياري (opt-out) ولا يحمل أي منهما بيانات جلسة: نبضة تثبيت مجهولة الهوية وفحص إصدار مقابل PyPI. كما يبحث التثبيت الافتراضي عن عنوان IP العام الخاص بك مرة واحدة لسطر شعار بدء التشغيل. كل وجهة، وما تحمله، وكيفية إيقافها مذكورة في
[docs/EGRESS.md](docs/EGRESS.md)؛ التثبيتات المستضافة ذاتيًا، أو المُعاد توجيهها، أو المعزولة عن الشبكة، لا تُجري أي مكالمات صادرة اختيارية على الإطلاق.

يحدث فك التشفير في متصفحك، بواسطة كود نُقدّمه لك. كان هذا وعدًا في السابق؛ أما الآن فهو شيء يمكنك التحقق منه. كل سطر يلمس مفتاحك موجود في ملف واحد يمكن قراءته، [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js)، الذي يُشحن داخل الحزمة (wheel) ويُقدَّم كما هو، مثبّتًا بتجزئة سلامة موارد فرعية (Subresource Integrity). للتأكد من أن المتصفح يشغّل ما نشرناه:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

ما لا يثبته ذلك: نحن من يقدّم الصفحة التي تحمّل الملف، لذا يمكننا تقديم صفحة مختلفة. تجزئات السلامة تحميك من شبكة توصيل محتوى (CDN) مخترقة، وليس من المزوّد نفسه. ما تكسبه هو أن أي استبدال يجب أن يكون متعمدًا، ومرئيًا في مصدر الصفحة، ومختلفًا عن نسخة على PyPI يمكن لأي شخص جلبها. الاستضافة الذاتية أو البقاء محليًا فقط يزيل هذا الاعتماد تمامًا.

## التثبيت

```bash
pip install clawmetry     # ثم: clawmetry
```

أو السطر الواحد: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

يتطلب Python 3.8+ على macOS أو Linux أو Windows، وبيئة تشغيل وكيل واحدة على الأقل على نفس الجهاز. تعليمات Docker: [docs/DOCKER.md](docs/DOCKER.md).

## الوثائق

| | |
|---|---|
| [توافق بيئات التشغيل](docs/compatibility.md) | ما يقرأه كل مُحوِّل، وكيفية إضافة بيئة تشغيل |
| [انفجار السياق](docs/CONTEXT_BLOWOUT.md) | النوافذ حسب المزوّد، الضغط مقابل الفيض، التغطية لكل بيئة تشغيل |
| [النفقات العامة (Overhead)](docs/OVERHEAD.md) | ما تكلفه الأداة، مقيسًا، مع الإطار اللازم لإعادة إنتاجه |
| [الاستحقاقات](docs/ENTITLEMENTS.md) | المجاني مقابل المدفوع، مصفوفة المستويات، أداة الترخيص CLI |
| [الموافقات والسياسات](docs/APPROVALS.md) | البوابة قبل التنفيذ، تسجيل المخاطر، الموافقات عبر الهاتف |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | تصدير التتبعات إلى أي مكان، استيعاب OTLP من أي مصدر |
| [أحضر وكيلك الخاص](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore، Pydantic AI، LangChain من البداية إلى النهاية، مع أمثلة قابلة للتشغيل |
| [تتبع SDK](docs/SDK_TRACKING.md) | إسناد التكلفة للوكلاء الذين بنيتهم بنفسك |
| [قنوات الدردشة](docs/CHANNELS.md) | مُحوّلات الدردشة المعروضة في التدفق (Flow) |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | إعدادات NVIDIA NemoClaw المعزولة (sandboxed) |
| [Docker](docs/DOCKER.md) | الصورة، compose، تحميلات الأحجام |
| [البنية المعمارية](ARCHITECTURE.md) · [التطوير](docs/DEVELOPMENT.md) | كيف يعمل داخليًا؛ التشغيل من الشيفرة المصدرية |
| [القياس عن بُعد](docs/TELEMETRY.md) | نبضات التثبيت المجهولة الهوية وفتح سطح المكتب، وكيفية إيقافها |

## لقطات الشاشة

كل رقم أدناه من جهاز حقيقي واحد، للقراءة فقط، دون أي بيانات مزروعة مسبقًا.

**تخبرك عندما يكون هناك خطأ، وليس فقط بما حدث.**
لافتتا شذوذ في الأعلى: إنفاق يسير بمعدل 7 أضعاف المتوسط اليومي، وارتفاع تكلفة بمقدار 4.2 ضعف. تحتهما، 324 من أصل 667 جلسة حديثة تحمل إشارة هدر، مفصّلة حسب السبب.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**تُظهر لك أين ذهبت الأموال، في كل نافذة زمنية.**
252.47$ اليوم، 513.15$ هذا الأسبوع، 1,312.92$ هذا الشهر، كل منها مع الرموز الكامنة خلفها ومقدار ما يغطيه اشتراكك بالفعل. تحت ذلك، نحو 1,128$/شهريًا مُصنَّفة كقابلة للاسترداد و17,256$/شهريًا موفَّرة بالفعل عبر إعادة استخدام الذاكرة المؤقتة.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**ترسم كيف تتحول الرسالة إلى إجابة.**
مخطط التدفق الحي: أنت، والقناة التي وصلت عبرها، والبوابة، والنموذج الذي يجيب الآن، وكل أداة استعان بها. تُضاء العُقد وهي تنتقل العمل عبرها.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**كل وكيل على الجهاز، في جدول واحد.**
ما يشغّله، وما يكلّفه في آخر 24 ساعة وعلى مدى عمره، ومتى شوهد آخر مرة، ومن يملكه، وما إذا كان اشتراك ما يغطي الفاتورة. 14 وكيلًا هنا، 3 جلسات تعمل، 13 هادئة.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**تُظهر أين ذهب وقت الدورة ومالها، أداة بأداة.**
دورة واحدة من جلسة حقيقية: 11 أداة في 11.2 دقيقة مقابل 1.16$. يحصل كل استدعاء Bash واستدعاء نموذج على شريطه الخاص على الخط الزمني، بحيث يُميَّز الأمر الذي استغرق 4.1 دقائق عن ذلك الذي استغرق 226 مللي ثانية بلمحة واحدة.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**تُقيّم العمل، وليس مجرد الإنفاق.**
تقدير A هذا الأسبوع: 54 مهمة عادت نظيفة، ومهمتان صعبتان كلفتا 48.57$، والدورات ذات النشاط القليل جدًا للحكم عليها استُبعدت من التقدير بدلًا من احتسابها كانتصارات. كل دورة صعبة ترتبط بتتبعها.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**تُظهر لماذا تستمر نافذة السياق بالامتلاء.**
715 ألفًا من نافذة مليون رمز في آخر دورة، ذروة 83.3%، و4 عمليات ضغط (compaction) أُطلقت جميعها بشكل استباقي وليس عند حدوث فيض، مع استغلال كل دورة خلف ذلك.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**يعمل الكشف دون أن تُعِدّ أي شيء.**
الكاشفات المدمجة مفعّلة منذ التثبيت: الوكيل أصبح صامتًا، توقف تدفق القياس عن بُعد، ارتفاع مفاجئ في التكلفة، اندفاع في الرموز، تصاعد الأخطاء، ارتفاع مفاجئ في الأخطاء، حد الميزانية، توقيع تهديد مطابق، نتيجة من أداة أمنية، تغيّر في وضع الأمان. قواعدك الخاصة اختيارية فوق ذلك.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**إيقاف استدعاء خطر هو اختيار، ويُشحن معطَّلًا.**
عمليات الحذف التكراري، والدفع القسري (force push)، وsudo، والأسرار، وتثبيتات الحزم، والمكالمات الصادرة تحصل كل منها على قاعدة يمكنك تفعيلها. حتى تفعّلها، يراقب ClawMetry ولا يغيّر شيئًا. بمجرد تفعيل واحدة، تنتظر المكالمات المطابقة هنا (أو على هاتفك) للموافقة أو الرفض.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

المزيد، لكل بيئة تشغيل: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
