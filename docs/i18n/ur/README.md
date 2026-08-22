<!-- i18n-src:c111f32e69a5 -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے دیکھیں۔** **26 AI ایجنٹ رن ٹائمز** کے لیے حقیقی وقت میں مشاہدہ: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور 22 مزید۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ڈیش بورڈ۔

> 🌐 **اسے ان زبانوں میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [more →](docs/i18n/)

ایک کمانڈ۔ زیرو کنفیگ۔ سب کچھ خود بخود پتہ لگاتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے۔ زیرو کنفیگ: یہ آپ کے پہلے سے موجود ایجنٹ رن ٹائمز کو تلاش کرتا ہے، انہیں صرف پڑھنے کے موڈ میں پڑھتا ہے، اور ان کے چلنے کے طریقے میں کوئی تبدیلی نہیں کرتا۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 26 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

**اوپن سورس ایپ میں مفت:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ادائیگی والے پلان پر:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

ہر رن ٹائم کو ایک جیسا ڈیش بورڈ ملتا ہے۔ ایک ساتھ کئی چلائیں اور ہیڈر سوئچر ہر ٹیب کو ان میں سے کسی ایک کے دائرہ کار میں دوبارہ ترتیب دیتا ہے۔

اس کے بجائے SDK پر اپنا ایجنٹ بنایا ہے؟ انٹرسیپٹر اس کی LLM کالز کو بھی ٹریک کرتا ہے۔ دیکھیں [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)۔

## آپ کو کیا ملتا ہے

- **سیشنز اور ٹرانسکرپٹس**: ہر ایجنٹ نے کیا کیا، ٹرن بہ ٹرن، ری پلے کے ساتھ
- **لاگت اور ٹوکنز**: فی رن ٹائم، ماڈل، سیشن اور دن، بے قاعدگی کے نشانات کے ساتھ
- **فلو**: چینلز، ماڈلز اور ٹولز کے ذریعے حرکت کرنے والے پیغامات کا لائیو ڈایاگرام
- **برین**: استدلال اور ٹول کال ایونٹ سٹریم، جیسے ہی یہ ہوتا ہے
- **میموری اور اسکلز**: وہ فائلیں اور اسکلز جو ہر رن ٹائم نے واقعتاً لوڈ کیں
- **ہیلتھ اور لاگز**: ڈسک، میموری، ایرر ریٹس، ریٹ لمٹس، لائیو لاگ سٹریم
- **الرٹس**: بجٹ کیپس، ایرر اسپائیکس، ایجنٹ آف لائن، Slack، Discord، PagerDuty، Telegram، Email کی طرف روٹ کیے گئے
- **منظوریاں**: خطرناک ٹول کالز کو چلنے *سے پہلے* روکیں اور اپنے فون سے منظور کریں ([کیسے](docs/APPROVALS.md))

## قیمتیں

| پلان | یہ کیا شامل کرتا ہے | قیمت |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose، مکمل ڈیش بورڈ، صرف مقامی | $0 |
| **Starter** | اوپر دیے گئے باقی تمام رن ٹائمز، فلیٹ ویو، کلاؤڈ سنک | $9 فی نوڈ / ماہ |
| **Pro** | Starter + گورننس: منظوریاں، ٹول رسک پالیسیاں، ایویلز، بے قاعدگی کی نشاندہی، لاگت آپٹیمائزر، OTel ایکسپورٹ | $19 فی نوڈ / ماہ |

سالانہ پلانز، انٹرپرائز اور موجودہ اعداد و شمار یہاں موجود ہیں
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**۔ سیلف ہوسٹڈ لائسنس
کیز کلاؤڈ کے بغیر کام کرتی ہیں (`clawmetry license`)۔ مفت/ادائیگی کی درست تقسیم
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) میں ہے۔

## آپ کا ڈیٹا آپ کی مشین پر ہی رہتا ہے

ClawMetry مقامی سیشن فائلیں اور لاگز پڑھتا ہے۔ جب تک آپ `clawmetry connect`
نہیں چلاتے، آپ کے سسٹم سے کچھ بھی باہر نہیں جاتا۔ اس صورت میں بھی سنیپ شاٹ ایک
ایسی کلید کے ساتھ اینڈ ٹو اینڈ اینکرپٹڈ ہوتا ہے جو کبھی آپ کی مشین سے باہر نہیں
جاتی، اور آپ کے براؤزر میں ڈی کرپٹ ہوتا ہے۔

## انسٹال

```bash
pip install clawmetry     # then: clawmetry
```

یا ون لائنر: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS، Linux یا Windows پر Python 3.8+ اور اسی مشین پر کم از کم ایک ایجنٹ
رن ٹائم درکار ہے۔ Docker ہدایات: [docs/DOCKER.md](docs/DOCKER.md)۔

## دستاویزات

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | ہر ایڈاپٹر کیا پڑھتا ہے، اور رن ٹائم کیسے شامل کریں |
| [Entitlements](docs/ENTITLEMENTS.md) | مفت بمقابلہ ادائیگی، ٹیئر میٹرکس، لائسنس CLI |
| [Approvals & policies](docs/APPROVALS.md) | ایگزیکیوشن سے پہلے گیٹنگ، رسک اسکورنگ، فون سے منظوریاں |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ٹریسز کہیں بھی ایکسپورٹ کریں، کہیں سے بھی OTLP ان جیسٹ کریں |
| [SDK tracking](docs/SDK_TRACKING.md) | آپ کے خود بنائے ہوئے ایجنٹس کے لیے لاگت کی وابستگی |
| [Chat channels](docs/CHANNELS.md) | فلو میں دکھائے گئے چیٹ ایڈاپٹرز |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | سینڈ باکسڈ NVIDIA NemoClaw سیٹ اپس |
| [Docker](docs/DOCKER.md) | امیج، کمپوز، والیوم ماؤنٹس |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | یہ اندر سے کیسے کام کرتا ہے؛ سورس سے چلانا |
| [Telemetry](docs/TELEMETRY.md) | گمنام انسٹال اور ڈیسک ٹاپ اوپن پنگز، اور انہیں کیسے بند کریں |

## اسکرین شاٹس

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: ٹوکنز، سیشنز، ہیلتھ | **Brain**: لائیو ایجنٹ ایونٹ سٹریم |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: ماڈل اور سیشن کے لحاظ سے | **Approvals**: خطرناک ٹول کالز کو گیٹ کریں |

فی رن ٹائم مزید: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)۔

## اسٹار ہسٹری

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## لائسنس

MIT · [@vivekchand](https://github.com/vivekchand) کی جانب سے بنایا گیا · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
