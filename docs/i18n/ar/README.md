<!-- i18n-src:6795052055e2 -->
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

**شاهد وكيلك وهو يفكر.** مراقبة فورية لـ **26 بيئة تشغيل لوكلاء الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex و22 غيرها. لوحة تحكم واحدة لأسطول وكلائك بأكمله.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بلا إعدادات. يكتشف كل شيء تلقائيًا.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900**. بلا إعدادات: يجد بيئات تشغيل الوكلاء الموجودة لديك بالفعل،
ويقرأها للقراءة فقط، ولا يغيّر أي شيء في طريقة عملها.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## يعمل مع 26 بيئة تشغيل للوكلاء

**مجانًا في التطبيق مفتوح المصدر:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**في خطة مدفوعة:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

كل بيئة تشغيل تحصل على نفس لوحة التحكم. شغّل عدة بيئات في آن واحد وسيعيد
مُبدّل الرأس نطاق كل تبويب إلى واحدة منها.

هل بنيت وكيلك الخاص باستخدام SDK بدلًا من ذلك؟ يتتبع المعترض (interceptor) استدعاءات
نموذج اللغة الكبير الخاصة به أيضًا. راجع [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## ما الذي تحصل عليه

- **الجلسات والنصوص**: ما فعله كل وكيل، دورًا بعد دور، مع إعادة التشغيل
- **التكلفة والرموز (tokens)**: لكل بيئة تشغيل ونموذج وجلسة ويوم، مع إشارات للحالات الشاذة
- **التدفق (Flow)**: رسم بياني حي للرسائل المتحركة عبر القنوات والنماذج والأدوات
- **العقل (Brain)**: تدفق أحداث التفكير واستدعاء الأدوات لحظة حدوثها
- **الذاكرة والمهارات**: الملفات والمهارات التي حمّلتها كل بيئة تشغيل فعليًا
- **الصحة والسجلات**: القرص، الذاكرة، معدلات الأخطاء، حدود المعدل، تدفق السجلات الحي
- **التنبيهات**: حدود الميزانية، ارتفاعات الأخطاء، توقف الوكيل عن العمل، موجّهة إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **الموافقات**: أوقف استدعاءات الأدوات الخطيرة *قبل* تنفيذها ووافق عليها من هاتفك ([كيف](docs/APPROVALS.md))

## التسعير

| الخطة | ما تغطيه | السعر |
|---|---|---|
| **مجانية** | OpenClaw + NVIDIA NemoClaw + Goose، لوحة تحكم كاملة، محليًا فقط | 0 دولار |
| **Starter** | كل بيئة تشغيل أخرى مذكورة أعلاه، عرض الأسطول، مزامنة سحابية | 9 دولارات لكل عقدة / شهر |
| **Pro** | Starter + الحوكمة: الموافقات، سياسات مخاطر الأدوات، التقييمات، اكتشاف الحالات الشاذة، محسّن التكلفة، تصدير OTel | 19 دولارًا لكل عقدة / شهر |

الخطط السنوية وخطة Enterprise والأرقام الحالية موجودة على
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. مفاتيح الترخيص للاستضافة الذاتية
تعمل بدون السحابة (`clawmetry license`). التقسيم الدقيق بين المجاني والمدفوع موجود
في [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## بياناتك تبقى على جهازك

يقرأ ClawMetry ملفات الجلسات والسجلات المحلية. لا يغادر أي شيء جهازك ما لم
تُشغّل `clawmetry connect`. وحتى في تلك الحالة، تكون اللقطة مشفّرة من طرف إلى طرف
بمفتاح لا يغادر جهازك أبدًا، ويُفك تشفيرها في متصفحك.

## التثبيت

```bash
pip install clawmetry     # ثم: clawmetry
```

أو السطر الواحد: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

يتطلب Python 3.8+ على macOS أو Linux أو Windows، وبيئة تشغيل وكيل واحدة على الأقل على
نفس الجهاز. تعليمات Docker: [docs/DOCKER.md](docs/DOCKER.md).

## الوثائق

| | |
|---|---|
| [توافق بيئات التشغيل](docs/compatibility.md) | ما يقرأه كل محوّل، وكيفية إضافة بيئة تشغيل |
| [الصلاحيات](docs/ENTITLEMENTS.md) | مجاني مقابل مدفوع، مصفوفة المستويات، واجهة سطر أوامر الترخيص |
| [الموافقات والسياسات](docs/APPROVALS.md) | التحقق قبل التنفيذ، تسجيل نقاط المخاطر، الموافقات عبر الهاتف |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صدّر التتبعات إلى أي مكان، واستوعب OTLP من أي مصدر |
| [تتبع SDK](docs/SDK_TRACKING.md) | إسناد التكلفة للوكلاء الذين بنيتهم بنفسك |
| [قنوات الدردشة](docs/CHANNELS.md) | محوّلات الدردشة الظاهرة في Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | إعدادات NVIDIA NemoClaw المعزولة (Sandboxed) |
| [Docker](docs/DOCKER.md) | الصورة، compose، تركيبات وحدات التخزين |
| [البنية المعمارية](ARCHITECTURE.md) · [التطوير](docs/DEVELOPMENT.md) | كيف يعمل من الداخل؛ التشغيل من المصدر |
| [القياس عن بُعد](docs/TELEMETRY.md) | إشعارات التثبيت وفتح سطح المكتب المجهولة، وكيفية إيقافها |

## لقطات شاشة

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **نظرة عامة**: الرموز، الجلسات، الصحة | **العقل**: تدفق أحداث الوكيل الحي |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **التكلفة**: حسب النموذج والجلسة | **الموافقات**: حجب استدعاءات الأدوات الخطيرة |

المزيد، لكل بيئة تشغيل: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## سجل النجوم

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
