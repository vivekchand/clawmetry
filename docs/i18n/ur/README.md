<!-- i18n-src:dc34072b2955 -->
> اردو translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **23 AI ایجنٹ رن ٹائمز** کے لیے ریئل ٹائم آبزرویبلٹی: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور مزید 19۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ہی ڈیش بورڈ۔

> 🌐 **اسے ان زبانوں میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ صفر کنفیگریشن۔ سب کچھ خود بخود پتا لگاتا ہے۔

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** پر کھلتا ہے۔ صفر کنفیگریشن: یہ ان ایجنٹ رن ٹائمز کو ڈھونڈ لیتا ہے جو آپ کے پاس پہلے سے موجود ہیں، انہیں صرف پڑھنے کے انداز میں (read-only) پڑھتا ہے، اور ان کے چلنے کے طریقے میں کچھ تبدیل نہیں کرتا۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 23 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

**اوپن سورس ایپ میں مفت:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**پیڈ پلان پر:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

ہر رن ٹائم کو ایک جیسا ڈیش بورڈ ملتا ہے۔ ایک ساتھ کئی چلائیں اور ہیڈر سوئچر ہر ٹیب کو ان میں سے کسی ایک کے دائرے میں لے آتا ہے۔

اپنا ایجنٹ کسی SDK پر خود بنایا ہے؟ انٹرسیپٹر اس کی LLM کالز کو بھی ٹریک کرتا ہے۔ دیکھیں [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)۔

## آپ کو کیا ملتا ہے

- **سیشنز اور ٹرانسکرپٹس**: ہر ایجنٹ نے کیا کیا، ٹرن بہ ٹرن، ری پلے کے ساتھ
- **لاگت اور ٹوکنز**: ہر رن ٹائم، ماڈل، سیشن اور دن کے لحاظ سے، بے ضابطگی کی نشاندہی کے ساتھ
- **فلو (Flow)**: چینلز، ماڈلز اور ٹولز کے درمیان چلنے والے پیغامات کا لائیو ڈایاگرام
- **برین (Brain)**: استدلال اور ٹول کال ایونٹ اسٹریم، جیسے ہی یہ ہو رہا ہو
- **میموری اور اسکلز**: وہ فائلیں اور اسکلز جو ہر رن ٹائم نے واقعی لوڈ کیں
- **صحت اور لاگز**: ڈسک، میموری، ایرر ریٹس، ریٹ لمٹس، لائیو لاگ اسٹریم
- **الرٹس**: بجٹ کی حدیں، ایرر اسپائیکس، ایجنٹ آف لائن، جو Slack، Discord، PagerDuty، Telegram، Email کی طرف روٹ کیے جاتے ہیں
- **منظوریاں (Approvals)**: خطرناک ٹول کالز کو چلنے سے *پہلے* روکیں اور اپنے فون سے منظور کریں ([کیسے](docs/APPROVALS.md))

## قیمت

| پلان | یہ کیا کور کرتا ہے | قیمت |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw، مکمل ڈیش بورڈ، صرف لوکل | $0 |
| **Starter** | اوپر بیان کردہ ہر دوسرا رن ٹائم، فلیٹ ویو، کلاؤڈ سنک | $9 فی نوڈ / ماہ |
| **Pro** | Starter + گورننس: منظوریاں، ٹول رسک پالیسیاں، ایویلز، بے ضابطگی کی نشاندہی، لاگت آپٹیمائزر، OTel ایکسپورٹ | $19 فی نوڈ / ماہ |

سالانہ پلانز، Enterprise اور موجودہ نمبرز یہاں موجود ہیں
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**۔ سیلف ہوسٹڈ لائسنس
کیز کلاؤڈ کے بغیر بھی کام کرتی ہیں (`clawmetry license`)۔ مفت/پیڈ کی درست تقسیم
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) میں موجود ہے۔

## آپ کا ڈیٹا آپ کی مشین پر ہی رہتا ہے

ClawMetry مقامی سیشن فائلیں اور لاگز پڑھتا ہے۔ آپ کے سسٹم سے کچھ باہر نہیں جاتا جب تک
آپ `clawmetry connect` نہ چلائیں۔ اس صورت میں بھی اسنیپ شاٹ ایک ایسی کلید سے
اینڈ ٹو اینڈ اینکرپٹڈ ہوتا ہے جو کبھی آپ کی مشین سے باہر نہیں جاتی، اور آپ کے براؤزر میں ڈکرپٹ ہوتا ہے۔

## انسٹال

```bash
pip install clawmetry     # then: clawmetry
```

یا ون لائنر: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS، Linux یا Windows پر Python 3.8+ درکار ہے، اور اسی مشین پر کم از کم ایک ایجنٹ
رن ٹائم۔ Docker ہدایات: [docs/DOCKER.md](docs/DOCKER.md)۔

## دستاویزات

| | |
|---|---|
| [رن ٹائم کمپیٹیبلٹی](docs/compatibility.md) | ہر ایڈاپٹر کیا پڑھتا ہے، اور رن ٹائم کیسے شامل کریں |
| [Entitlements](docs/ENTITLEMENTS.md) | مفت بمقابلہ پیڈ، ٹیئر میٹرکس، لائسنس CLI |
| [منظوریاں اور پالیسیاں](docs/APPROVALS.md) | پری ایگزیکیوشن گیٹنگ، رسک اسکورنگ، فون سے منظوریاں |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ٹریسز کہیں بھی ایکسپورٹ کریں، کسی بھی جگہ سے OTLP اِن جیسٹ کریں |
| [SDK ٹریکنگ](docs/SDK_TRACKING.md) | خود بنائے گئے ایجنٹس کے لیے لاگت کی تخصیص |
| [چیٹ چینلز](docs/CHANNELS.md) | Flow میں دکھائے جانے والے چیٹ ایڈاپٹرز |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | سینڈ باکسڈ NVIDIA NemoClaw سیٹ اپس |
| [Docker](docs/DOCKER.md) | امیج، کمپوز، والیوم ماؤنٹس |
| [آرکیٹیکچر](ARCHITECTURE.md) · [ڈویلپمنٹ](docs/DEVELOPMENT.md) | اندر یہ کیسے کام کرتا ہے؛ سورس سے چلانا |
| [ٹیلی میٹری](docs/TELEMETRY.md) | گمنام انسٹال اور ڈیسک ٹاپ اوپن پنگز، اور انہیں کیسے بند کریں |

## اسکرین شاٹس

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **اوورویو**: ٹوکنز، سیشنز، صحت | **برین**: لائیو ایجنٹ ایونٹ اسٹریم |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **لاگت**: ماڈل اور سیشن کے لحاظ سے | **منظوریاں**: خطرناک ٹول کالز کو روکنا |

مزید، ہر رن ٹائم کے لحاظ سے: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)۔

## اسٹار ہسٹری

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## لائسنس

MIT · تیار کردہ [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
