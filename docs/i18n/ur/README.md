<!-- i18n-src:6795052055e2 -->
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

**اپنے ایجنٹ کو سوچتے ہوئے دیکھیں۔** **26 AI ایجنٹ رن ٹائمز** کے لیے حقیقی وقت کی مانیٹرنگ: [OpenClaw](https://github.com/openclaw/openclaw)، [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)، Claude Code، OpenAI Codex اور مزید 22۔ آپ کے پورے ایجنٹ فلیٹ کے لیے ایک ہی ڈیش بورڈ۔

> 🌐 **اسے ان زبانوں میں پڑھیں:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [مزید →](docs/i18n/)

ایک کمانڈ۔ کوئی کنفیگریشن نہیں۔ سب کچھ خودکار طور پر معلوم کر لیتا ہے۔

```bash
pip install clawmetry && clawmetry
```

یہ **http://localhost:8900** پر کھلتا ہے۔ کوئی کنفیگریشن درکار نہیں: یہ آپ کے پہلے سے موجود ایجنٹ رن ٹائمز کو ڈھونڈ لیتا ہے، انہیں صرف پڑھنے کے موڈ میں پڑھتا ہے، اور ان کے چلنے کے طریقے میں کوئی تبدیلی نہیں کرتا۔

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 26 ایجنٹ رن ٹائمز کے ساتھ کام کرتا ہے

**اوپن سورس ایپ میں مفت:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**ایک ادا شدہ پلان پر:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

ہر رن ٹائم کو ایک جیسا ڈیش بورڈ ملتا ہے۔ ایک ساتھ کئی چلائیں اور ہیڈر کا سوئچر ہر ٹیب کو ان میں سے کسی ایک کے لیے دوبارہ ترتیب دے دیتا ہے۔

کیا آپ نے کسی SDK پر اپنا خود کا ایجنٹ بنایا ہے؟ انٹرسیپٹر اس کی LLM کالز کو بھی ٹریک کرتا ہے۔ دیکھیں [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)۔

## آپ کو کیا ملتا ہے

- **سیشنز اور ٹرانسکرپٹس**: ہر ایجنٹ نے کیا کیا، باری باری، دوبارہ چلانے (ری پلے) کے ساتھ
- **لاگت اور ٹوکنز**: ہر رن ٹائم، ماڈل، سیشن اور دن کے حساب سے، غیر معمولی نشانات کے ساتھ
- **فلو**: چینلز، ماڈلز اور ٹولز کے درمیان چلنے والے پیغامات کا لائیو ڈایاگرام
- **برین**: استدلال اور ٹول کال کے ایونٹ اسٹریم کو ہوتے ہی دیکھیں
- **میموری اور اسکلز**: وہ فائلیں اور اسکلز جو ہر رن ٹائم نے واقعی لوڈ کیں
- **صحت اور لاگز**: ڈسک، میموری، ایرر ریٹس، ریٹ لمٹس، لائیو لاگ اسٹریم
- **الرٹس**: بجٹ کی حدیں، ایرر میں اضافہ، ایجنٹ آف لائن، جو Slack، Discord، PagerDuty، Telegram، Email پر بھیجے جائیں
- **منظوریاں**: خطرناک ٹول کالز کو چلنے سے *پہلے* روکیں اور اپنے فون سے منظور کریں ([کیسے](docs/APPROVALS.md))

## قیمتیں

| پلان | کیا شامل ہے | قیمت |
|---|---|---|
| **مفت** | OpenClaw + NVIDIA NemoClaw + Goose، مکمل ڈیش بورڈ، صرف لوکل | $0 |
| **اسٹارٹر** | اوپر دیے گئے ہر دوسرے رن ٹائم، فلیٹ ویو، کلاؤڈ سنک | فی نوڈ $9 / ماہ |
| **پرو (Pro)** | اسٹارٹر + گورننس: منظوریاں، ٹول رسک پالیسیاں، ایویلز، غیر معمولی سرگرمی کی تشخیص، لاگت آپٹیمائزر، OTel ایکسپورٹ | فی نوڈ $19 / ماہ |

سالانہ پلانز، انٹرپرائز اور موجودہ قیمتیں یہاں موجود ہیں
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**۔ سیلف ہوسٹڈ لائسنس
کیز کلاؤڈ کے بغیر بھی کام کرتی ہیں (`clawmetry license`)۔ مفت/ادا شدہ کی درست تقسیم
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) میں موجود ہے۔

## آپ کا ڈیٹا آپ کی مشین پر ہی رہتا ہے

ClawMetry مقامی سیشن فائلز اور لاگز کو پڑھتا ہے۔ آپ کے باکس سے کچھ بھی باہر نہیں جاتا جب تک آپ
`clawmetry connect` نہ چلائیں۔ اس کے باوجود سنیپ شاٹ ایک ایسی چابی کے ساتھ اینڈ ٹو اینڈ اینکرپٹڈ ہوتا ہے
جو کبھی آپ کی مشین سے باہر نہیں جاتی، اور آپ کے براؤزر میں ڈیکرپٹ ہوتا ہے۔

## انسٹال کریں

```bash
pip install clawmetry     # پھر: clawmetry
```

یا ایک ہی لائن میں: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS، Linux یا Windows پر Python 3.8+ درکار ہے، اور اسی مشین پر کم از کم ایک ایجنٹ رن ٹائم۔
Docker ہدایات: [docs/DOCKER.md](docs/DOCKER.md)۔

## دستاویزات

| | |
|---|---|
| [رن ٹائم مطابقت](docs/compatibility.md) | ہر ایڈاپٹر کیا پڑھتا ہے، اور رن ٹائم کیسے شامل کریں |
| [Entitlements](docs/ENTITLEMENTS.md) | مفت بمقابلہ ادا شدہ، ٹیئر میٹرکس، لائسنس CLI |
| [منظوریاں اور پالیسیاں](docs/APPROVALS.md) | عمل درآمد سے پہلے کی جانچ، رسک اسکورنگ، فون منظوریاں |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ٹریسز کہیں بھی ایکسپورٹ کریں، کسی بھی چیز سے OTLP اِن جیسٹ کریں |
| [SDK ٹریکنگ](docs/SDK_TRACKING.md) | آپ کے خود بنائے ہوئے ایجنٹس کے لیے لاگت کی نسبت |
| [چیٹ چینلز](docs/CHANNELS.md) | فلو میں دکھائے جانے والے چیٹ ایڈاپٹرز |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | سینڈ باکس شدہ NVIDIA NemoClaw سیٹ اپس |
| [Docker](docs/DOCKER.md) | امیج، کمپوز، والیوم ماؤنٹس |
| [آرکیٹیکچر](ARCHITECTURE.md) · [ڈیولپمنٹ](docs/DEVELOPMENT.md) | یہ اندر سے کیسے کام کرتا ہے؛ سورس سے چلانا |
| [ٹیلی میٹری](docs/TELEMETRY.md) | گمنام انسٹال اور ڈیسک ٹاپ اوپن پنگز، اور انہیں بند کرنے کا طریقہ |

## اسکرین شاٹس

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **جائزہ**: ٹوکنز، سیشنز، صحت | **برین**: لائیو ایجنٹ ایونٹ اسٹریم |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **لاگت**: ماڈل اور سیشن کے حساب سے | **منظوریاں**: خطرناک ٹول کالز کو روکیں |

مزید، ہر رن ٹائم کے حساب سے: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)۔

## Star History

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
