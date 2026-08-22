<!-- i18n-src:c111f32e69a5 -->
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

**شاهد وكيلك وهو يفكّر.** مراقبة حية لـ **26 بيئة تشغيل لوكلاء الذكاء الاصطناعي**: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex و22 غيرها. لوحة تحكم واحدة لأسطول وكلائك بالكامل.

> 🌐 **اقرأ هذا بلغة:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [المزيد ←](docs/i18n/)

أمر واحد. بلا إعداد. يكتشف كل شيء تلقائياً.

```bash
pip install clawmetry && clawmetry
```

يفتح على **http://localhost:8900**. بلا إعداد: يعثر على بيئات تشغيل الوكلاء الموجودة لديك بالفعل، يقرأها للقراءة فقط، ولا يغيّر شيئاً في طريقة عملها.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## يعمل مع 26 بيئة تشغيل للوكلاء

**مجاني في التطبيق مفتوح المصدر:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**في خطة مدفوعة:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

كل بيئة تشغيل تحصل على نفس لوحة التحكم. شغّل عدة بيئات في آنٍ واحد، ومبدّل الرأس يعيد توجيه كل تبويب إلى إحداها.

بنيت وكيلك الخاص باستخدام SDK بدلاً من ذلك؟ يتتبّع الـ interceptor استدعاءات النماذج اللغوية الخاصة به أيضاً. راجع [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## ما الذي تحصل عليه

- **الجلسات والنصوص الكاملة**: ما فعله كل وكيل، خطوة بخطوة، مع إعادة تشغيل
- **التكلفة والرموز (tokens)**: لكل بيئة تشغيل ونموذج وجلسة ويوم، مع مؤشرات الشذوذ
- **التدفق (Flow)**: مخطط حي للرسائل وهي تنتقل عبر القنوات والنماذج والأدوات
- **العقل (Brain)**: تدفّق أحداث التفكير واستدعاء الأدوات لحظة حدوثها
- **الذاكرة والمهارات**: الملفات والمهارات التي حمّلتها كل بيئة تشغيل فعلياً
- **الصحة والسجلات**: القرص، الذاكرة، معدلات الأخطاء، حدود المعدل، تدفق سجلات حي
- **التنبيهات**: حدود الميزانية، ارتفاعات الأخطاء، انقطاع الوكيل، موجّهة إلى Slack وDiscord وPagerDuty وTelegram والبريد الإلكتروني
- **الموافقات**: أوقف استدعاءات الأدوات الخطرة *قبل* تنفيذها ووافق عليها من هاتفك ([كيف](docs/APPROVALS.md))

## التسعير

| الخطة | ما تغطيه | السعر |
|---|---|---|
| **مجانية** | OpenClaw + NVIDIA NemoClaw + Goose، لوحة تحكم كاملة، محلية فقط | 0$ |
| **Starter** | كل بيئة تشغيل أخرى مذكورة أعلاه، عرض الأسطول، مزامنة سحابية | 9$ لكل عقدة / شهرياً |
| **Pro** | Starter + الحوكمة: الموافقات، سياسات مخاطر الأدوات، التقييمات، كشف الشذوذ، محسّن التكلفة، تصدير OTel | 19$ لكل عقدة / شهرياً |

الخطط السنوية وخطة Enterprise والأرقام الحالية موجودة على
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. مفاتيح الترخيص الذاتية الاستضافة
تعمل بدون السحابة (`clawmetry license`). التقسيم الدقيق بين المجاني والمدفوع
موجود في [docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md).

## بياناتك تبقى على جهازك

يقرأ ClawMetry ملفات الجلسات والسجلات المحلية. لا يغادر شيء جهازك ما لم
تشغّل `clawmetry connect`. وحتى في تلك الحالة، تكون اللقطة (snapshot) مشفّرة
من طرف إلى طرف بمفتاح لا يغادر جهازك أبداً، ويُفكّ تشفيرها في متصفحك.

## التثبيت

```bash
pip install clawmetry     # ثم: clawmetry
```

أو السطر الواحد: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

يتطلب Python 3.8+ على macOS أو Linux أو Windows، وبيئة تشغيل وكيل واحدة على الأقل
على نفس الجهاز. تعليمات Docker: [docs/DOCKER.md](docs/DOCKER.md).

## التوثيق

| | |
|---|---|
| [توافق بيئات التشغيل](docs/compatibility.md) | ما يقرأه كل محوّل، وكيفية إضافة بيئة تشغيل |
| [الاستحقاقات](docs/ENTITLEMENTS.md) | المجاني مقابل المدفوع، مصفوفة الفئات، واجهة سطر أوامر الترخيص |
| [الموافقات والسياسات](docs/APPROVALS.md) | البوابة قبل التنفيذ، تقييم المخاطر، الموافقات عبر الهاتف |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | صدّر الآثار (traces) إلى أي مكان، استقبل OTLP من أي مصدر |
| [تتبّع الـ SDK](docs/SDK_TRACKING.md) | إسناد التكلفة للوكلاء الذين بنيتهم بنفسك |
| [قنوات الدردشة](docs/CHANNELS.md) | محوّلات الدردشة الظاهرة في Flow |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | إعدادات NVIDIA NemoClaw المعزولة (sandboxed) |
| [Docker](docs/DOCKER.md) | الصورة، compose، تثبيتات المجلدات (volume mounts) |
| [البنية المعمارية](ARCHITECTURE.md) · [التطوير](docs/DEVELOPMENT.md) | كيف يعمل من الداخل؛ التشغيل من المصدر |
| [التتبع (Telemetry)](docs/TELEMETRY.md) | نبضات التثبيت وفتح سطح المكتب المجهولة، وكيفية إيقافها |

## لقطات شاشة

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **نظرة عامة**: الرموز، الجلسات، الصحة | **العقل (Brain)**: تدفق أحداث الوكيل الحي |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **التكلفة**: حسب النموذج والجلسة | **الموافقات**: بوابة استدعاءات الأدوات الخطرة |

المزيد، حسب بيئة التشغيل: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

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
