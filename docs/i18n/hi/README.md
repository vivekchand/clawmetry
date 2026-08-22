<!-- i18n-src:6795052055e2 -->
> हिन्दी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**देखिए आपका एजेंट कैसे सोचता है।** **26 AI एजेंट रनटाइम** के लिए रीयल-टाइम ऑब्ज़र्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 22 अन्य। आपके पूरे एजेंट फ्लीट के लिए एक डैशबोर्ड।

> 🌐 **इसे इस भाषा में पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड। ज़ीरो कॉन्फ़िग। सब कुछ अपने आप डिटेक्ट करता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है। ज़ीरो कॉन्फ़िग: यह उन एजेंट रनटाइम को ढूंढ लेता है जो
आपके पास पहले से हैं, उन्हें केवल रीड-ओनली मोड में पढ़ता है, और उनके चलने के तरीके में कोई बदलाव नहीं करता।

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## 26 एजेंट रनटाइम के साथ काम करता है

**ओपन सोर्स ऐप में मुफ़्त:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**पेड प्लान में:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

हर रनटाइम को एक जैसा डैशबोर्ड मिलता है। एक साथ कई चलाएँ और हेडर
स्विचर हर टैब को उनमें से किसी एक पर फिर से स्कोप कर देता है।

इसके बजाय किसी SDK पर अपना खुद का एजेंट बनाया है? इंटरसेप्टर उसकी
LLM कॉल्स को भी ट्रैक करता है। देखें [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## आपको क्या मिलता है

- **सेशन और ट्रांसक्रिप्ट**: हर एजेंट ने क्या किया, टर्न दर टर्न, रीप्ले के साथ
- **लागत और टोकन**: प्रति रनटाइम, मॉडल, सेशन और दिन, एनोमली फ़्लैग के साथ
- **Flow**: चैनलों, मॉडलों और टूल्स के बीच चलते संदेशों का लाइव डायग्राम
- **Brain**: रीज़निंग और टूल-कॉल इवेंट स्ट्रीम, जैसे जैसे यह होता है
- **मेमोरी और स्किल्स**: वे फ़ाइलें और स्किल्स जो हर रनटाइम ने वास्तव में लोड कीं
- **हेल्थ और लॉग्स**: डिस्क, मेमोरी, एरर रेट, रेट लिमिट, लाइव लॉग स्ट्रीम
- **अलर्ट**: बजट कैप, एरर स्पाइक, एजेंट-ऑफ़लाइन, Slack, Discord, PagerDuty, Telegram, Email पर भेजे गए
- **अप्रूवल्स**: जोखिम भरी टूल कॉल्स को चलने *से पहले* रोकें और अपने फ़ोन से अप्रूव करें ([कैसे](docs/APPROVALS.md))

## कीमत

| Plan | इसमें क्या शामिल है | कीमत |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, पूरा डैशबोर्ड, केवल लोकल | $0 |
| **Starter** | ऊपर बताए गए बाकी सभी रनटाइम, फ्लीट व्यू, क्लाउड सिंक | $9 प्रति नोड / महीना |
| **Pro** | Starter + गवर्नेंस: अप्रूवल्स, टूल-रिस्क पॉलिसी, इवैल्स, एनोमली डिटेक्शन, कॉस्ट ऑप्टिमाइज़र, OTel एक्सपोर्ट | $19 प्रति नोड / महीना |

वार्षिक प्लान, Enterprise और मौजूदा आंकड़े यहाँ मिलेंगे
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**। सेल्फ़-होस्टेड लाइसेंस
कीज़ बिना क्लाउड के भी काम करती हैं (`clawmetry license`)। फ्री/पेड का सटीक विभाजन
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) में है।

## आपका डेटा आपकी मशीन पर ही रहता है

ClawMetry लोकल सेशन फ़ाइलें और लॉग्स पढ़ता है। जब तक आप `clawmetry connect`
नहीं चलाते, तब तक आपकी मशीन से कुछ भी बाहर नहीं जाता। तब भी स्नैपशॉट एंड-टू-एंड
एन्क्रिप्टेड होता है, ऐसी कुंजी के साथ जो कभी आपकी मशीन से बाहर नहीं जाती, और इसे
आपके ब्राउज़र में डिक्रिप्ट किया जाता है।

## इंस्टॉल

```bash
pip install clawmetry     # then: clawmetry
```

या वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux या Windows पर Python 3.8+ चाहिए, और उसी मशीन पर कम से कम एक एजेंट
रनटाइम चाहिए। Docker के निर्देश: [docs/DOCKER.md](docs/DOCKER.md)।

## दस्तावेज़

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | हर एडॉप्टर क्या पढ़ता है, और रनटाइम कैसे जोड़ें |
| [Entitlements](docs/ENTITLEMENTS.md) | फ्री बनाम पेड, टियर मैट्रिक्स, लाइसेंस CLI |
| [Approvals & policies](docs/APPROVALS.md) | प्री-एक्ज़िक्यूशन गेटिंग, रिस्क स्कोरिंग, फ़ोन अप्रूवल्स |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ट्रेस कहीं भी एक्सपोर्ट करें, किसी भी जगह से OTLP इनजेस्ट करें |
| [SDK tracking](docs/SDK_TRACKING.md) | आपके खुद बनाए एजेंट्स के लिए कॉस्ट एट्रिब्यूशन |
| [Chat channels](docs/CHANNELS.md) | Flow में दिखाए गए चैट एडॉप्टर |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सैंडबॉक्स्ड NVIDIA NemoClaw सेटअप |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज़, वॉल्यूम माउंट |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | यह अंदर से कैसे काम करता है; सोर्स से कैसे चलाएँ |
| [Telemetry](docs/TELEMETRY.md) | गुमनाम इंस्टॉल और डेस्कटॉप-ओपन पिंग्स, और उन्हें कैसे बंद करें |

## स्क्रीनशॉट

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: टोकन, सेशन, हेल्थ | **Brain**: लाइव एजेंट इवेंट स्ट्रीम |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: मॉडल और सेशन के अनुसार | **Approvals**: जोखिम भरी टूल कॉल्स को गेट करें |

प्रति रनटाइम और अधिक: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## स्टार हिस्ट्री

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## लाइसेंस

MIT · [@vivekchand](https://github.com/vivekchand) द्वारा बनाया गया · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
