<!-- i18n-src:c111f32e69a5 -->
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

**अपने एजेंट को सोचते हुए देखें।** **26 AI एजेंट रनटाइम** के लिए रीयल-टाइम ऑब्ज़र्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex और 24 अन्य। आपके पूरे एजेंट फ्लीट के लिए एक ही डैशबोर्ड।

> 🌐 **इसे इन भाषाओं में पढ़ें:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [और →](docs/i18n/)

एक कमांड। शून्य कॉन्फ़िगरेशन। सब कुछ अपने आप पहचान लेता है।

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** पर खुलता है। शून्य कॉन्फ़िगरेशन: यह आपके पास पहले से मौजूद एजेंट रनटाइम को ढूंढ लेता है, उन्हें केवल पढ़ने के लिए एक्सेस करता है, और उनके चलने के तरीके में कुछ भी नहीं बदलता।

![ClawMetry: a Claude Code agent working right now, with cost, health and every other runtime on the machine](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

## 26 एजेंट रनटाइम के साथ काम करता है

**ओपन सोर्स ऐप में मुफ़्त:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**पेड प्लान पर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok](https://clawmetry.com/runtimes/grok)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

हर रनटाइम को एक जैसा डैशबोर्ड मिलता है। एक साथ कई चलाएँ और हेडर स्विचर हर टैब को उनमें से किसी एक पर फिर से स्कोप कर देता है।

किसी SDK पर अपना खुद का एजेंट बनाया है? इंटरसेप्टर उसकी LLM कॉल्स को भी ट्रैक करता है। देखें [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md)।

## आपको क्या मिलता है

- **सेशन और ट्रांसक्रिप्ट**: हर एजेंट ने क्या किया, टर्न दर टर्न, रिप्ले के साथ
- **लागत और टोकन**: रनटाइम, मॉडल, सेशन और दिन के हिसाब से, एनोमली फ़्लैग्स के साथ
- **फ्लो**: चैनलों, मॉडलों और टूल्स के बीच चलते संदेशों का लाइव डायग्राम
- **ब्रेन**: होते ही रीज़निंग और टूल-कॉल इवेंट स्ट्रीम
- **मेमोरी और स्किल्स**: वे फ़ाइलें और स्किल्स जिन्हें हर रनटाइम ने वास्तव में लोड किया
- **हेल्थ और लॉग्स**: डिस्क, मेमोरी, एरर दरें, रेट लिमिट, लाइव लॉग स्ट्रीम
- **अलर्ट**: बजट कैप, एरर स्पाइक, एजेंट-ऑफ़लाइन, Slack, Discord, PagerDuty, Telegram, Email पर रूटेड
- **अप्रूवल**: जोखिम भरे टूल कॉल्स को चलने *से पहले* रोकें और अपने फोन से अप्रूव करें ([कैसे](docs/APPROVALS.md))

## मूल्य निर्धारण

| प्लान | यह क्या कवर करता है | कीमत |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw + Goose, पूरा डैशबोर्ड, केवल लोकल | $0 |
| **Starter** | ऊपर बताया गया हर अन्य रनटाइम, फ्लीट व्यू, क्लाउड सिंक | $9 प्रति नोड / माह |
| **Pro** | Starter + गवर्नेंस: अप्रूवल, टूल-रिस्क पॉलिसी, इवैल्स, एनोमली डिटेक्शन, कॉस्ट ऑप्टिमाइज़र, OTel एक्सपोर्ट | $19 प्रति नोड / माह |

वार्षिक प्लान, एंटरप्राइज़ और मौजूदा आँकड़े यहाँ हैं
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**। सेल्फ़-होस्टेड लाइसेंस
कीज़ बिना क्लाउड के काम करती हैं (`clawmetry license`)। मुफ़्त/पेड का सटीक बँटवारा
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) में है।

## आपका डेटा आपकी मशीन पर ही रहता है

ClawMetry लोकल सेशन फ़ाइलें और लॉग पढ़ता है। जब तक आप `clawmetry connect`
न चलाएँ, कुछ भी आपके सिस्टम से बाहर नहीं जाता। तब भी स्नैपशॉट एक ऐसी की (key) से
एंड-टू-एंड एन्क्रिप्टेड होता है जो कभी आपकी मशीन से बाहर नहीं जाती, और आपके ब्राउज़र में डिक्रिप्ट होता है।

## इंस्टॉल करें

```bash
pip install clawmetry     # फिर: clawmetry
```

या वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux या Windows पर Python 3.8+ चाहिए, और उसी मशीन पर कम से कम एक एजेंट
रनटाइम होना चाहिए। Docker निर्देश: [docs/DOCKER.md](docs/DOCKER.md)।

## दस्तावेज़

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | हर एडाप्टर क्या पढ़ता है, और रनटाइम कैसे जोड़ें |
| [Entitlements](docs/ENTITLEMENTS.md) | मुफ़्त बनाम पेड, टियर मैट्रिक्स, लाइसेंस CLI |
| [Approvals & policies](docs/APPROVALS.md) | प्री-एक्ज़ीक्यूशन गेटिंग, रिस्क स्कोरिंग, फ़ोन अप्रूवल |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | कहीं भी ट्रेस एक्सपोर्ट करें, कहीं से भी OTLP इनजेस्ट करें |
| [SDK tracking](docs/SDK_TRACKING.md) | खुद बनाए एजेंट्स के लिए कॉस्ट अट्रिब्यूशन |
| [Chat channels](docs/CHANNELS.md) | Flow में दिखने वाले चैट एडाप्टर |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सैंडबॉक्स्ड NVIDIA NemoClaw सेटअप |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज़, वॉल्यूम माउंट |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | यह अंदर कैसे काम करता है; सोर्स से चलाना |
| [Telemetry](docs/TELEMETRY.md) | अनाम इंस्टॉल और डेस्कटॉप-ओपन पिंग्स, और उन्हें कैसे बंद करें |

## स्क्रीनशॉट

| | |
|---|---|
| ![Overview: spending anomaly banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Agents: every AI agent runtime on the machine with 24h and lifetime cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png) |
| **Overview**: टोकन, सेशन, हेल्थ | **एजेंट** |
| ![Cost: today, this week and this month with an efficiency grade](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png) | ![Approvals: protection rules holding risky tool calls for sign-off](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: मॉडल और सेशन के अनुसार | **Approvals**: जोखिम भरे टूल कॉल्स को गेट करें |

रनटाइम के अनुसार और भी: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md)।

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## License

MIT · निर्माता [@vivekchand](https://github.com/vivekchand) · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
