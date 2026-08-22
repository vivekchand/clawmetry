<!-- i18n-src:6795052055e2 -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/vivekchand/clawmetry/badge)](https://scorecard.dev/viewer/?uri=github.com/vivekchand/clawmetry)
[![Security policy](https://img.shields.io/badge/security-policy-informational)](SECURITY.md)
[![Egress: documented](https://img.shields.io/badge/egress-documented-informational)](docs/EGRESS.md)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**तुमचा एजंट विचार करताना पाहा.** **२६ AI एजंट रनटाइम्स** साठी रिअल-टाइम ऑब्झर्व्हेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी २२. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्व काही स्वयंचलितपणे शोधते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते. शून्य कॉन्फिगरेशन: तुमच्याकडे आधीच असलेले एजंट रनटाइम्स ते शोधते, त्यांना फक्त-वाचनीय (read-only) पद्धतीने वाचते, आणि ते कसे चालतात यात काहीही बदल करत नाही.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## २६ एजंट रनटाइम्ससोबत काम करते

**ओपन सोर्स ॲपमध्ये मोफत:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**सशुल्क प्लॅनवर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)**

प्रत्येक रनटाइमला तोच डॅशबोर्ड मिळतो. एकाच वेळी अनेक चालवा आणि हेडरमधील स्विचर प्रत्येक टॅबला त्यांपैकी एकावर पुन्हा-स्कोप करतो.

SDK वापरून स्वतःचा एजंट तयार केला आहे? इंटरसेप्टर त्याच्या LLM कॉल्सचाही मागोवा घेतो. पाहा [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## तुम्हाला काय मिळते

- **सेशन्स आणि ट्रान्सक्रिप्ट्स**: प्रत्येक एजंटने काय केले, टर्न-दर-टर्न, रिप्लेसह
- **किंमत आणि टोकन्स**: रनटाइम, मॉडेल, सेशन आणि दिवसानुसार, विसंगती (anomaly) फ्लॅग्ससह
- **फ्लो**: चॅनेल्स, मॉडेल्स आणि टूल्समधून जाणाऱ्या मेसेजेसचा लाइव्ह आराखडा
- **ब्रेन**: घडत असताना रिझनिंग आणि टूल-कॉल इव्हेंट स्ट्रीम
- **मेमरी आणि स्किल्स**: प्रत्येक रनटाइमने प्रत्यक्षात लोड केलेल्या फाइल्स आणि स्किल्स
- **हेल्थ आणि लॉग्स**: डिस्क, मेमरी, एरर रेट्स, रेट लिमिट्स, लाइव्ह लॉग स्ट्रीम
- **अलर्ट्स**: बजेट कॅप्स, एरर स्पाइक्स, एजंट-ऑफलाइन, Slack, Discord, PagerDuty, Telegram, Email कडे रूट केलेले
- **अप्रूव्हल्स**: जोखमीचे टूल कॉल्स चालण्याआधीच थांबवा आणि तुमच्या फोनवरून मंजूर करा ([कसे](docs/APPROVALS.md))

## किंमत

| प्लॅन | यामध्ये काय समाविष्ट आहे | किंमत |
|---|---|---|
| **मोफत** | OpenClaw + NVIDIA NemoClaw + Goose, संपूर्ण डॅशबोर्ड, फक्त लोकल | $0 |
| **स्टार्टर** | वरील प्रत्येक इतर रनटाइम, फ्लीट व्ह्यू, क्लाउड सिंक | $9 प्रत्येक नोडसाठी / महिना |
| **Pro** | स्टार्टर + गव्हर्नन्स: अप्रूव्हल्स, टूल-रिस्क पॉलिसीज, इव्हॅल्स, विसंगती शोध, कॉस्ट ऑप्टिमायझर, OTel एक्सपोर्ट | $19 प्रत्येक नोडसाठी / महिना |

वार्षिक प्लॅन्स, एंटरप्राइझ आणि सध्याचे आकडे
**[clawmetry.com/pricing](https://clawmetry.com/pricing)** येथे उपलब्ध आहेत. सेल्फ-होस्टेड लायसन्स
की क्लाउडशिवायही काम करतात (`clawmetry license`). नेमकी मोफत/सशुल्क विभागणी
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) मध्ये आहे.

## तुमचा डेटा तुमच्या मशीनवरच राहतो

ClawMetry लोकल सेशन फाइल्स आणि लॉग्स वाचते. तुम्ही `clawmetry connect` चालवत नाही
तोपर्यंत काहीही तुमच्या मशीनबाहेर जात नाही. तेव्हाही स्नॅपशॉट अशा की सह
एंड-टू-एंड एन्क्रिप्टेड असतो जी कधीही तुमचे मशीन सोडत नाही, आणि तुमच्या ब्राउझरमध्ये डिक्रिप्ट होते.

## इन्स्टॉल करा

```bash
pip install clawmetry     # नंतर: clawmetry
```

किंवा वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux किंवा Windows वर Python 3.8+ आणि त्याच मशीनवर किमान एक एजंट
रनटाइम आवश्यक आहे. Docker सूचना: [docs/DOCKER.md](docs/DOCKER.md).

## डॉक्युमेंटेशन

| | |
|---|---|
| [रनटाइम कंपॅटिबिलिटी](docs/compatibility.md) | प्रत्येक अडॅप्टर काय वाचतो, आणि रनटाइम कसा जोडावा |
| [एंटायटलमेंट्स](docs/ENTITLEMENTS.md) | मोफत वि. सशुल्क, टियर मॅट्रिक्स, लायसन्स CLI |
| [अप्रूव्हल्स आणि पॉलिसीज](docs/APPROVALS.md) | पूर्व-अंमलबजावणी गेटिंग, रिस्क स्कोरिंग, फोन अप्रूव्हल्स |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ट्रेसेस कुठेही एक्सपोर्ट करा, कुठूनही OTLP इनजेस्ट करा |
| [SDK ट्रॅकिंग](docs/SDK_TRACKING.md) | तुम्ही स्वतः तयार केलेल्या एजंट्ससाठी कॉस्ट अट्रिब्युशन |
| [चॅट चॅनेल्स](docs/CHANNELS.md) | Flow मध्ये दिसणारे चॅट अडॅप्टर्स |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सँडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज, व्हॉल्यूम माउंट्स |
| [आर्किटेक्चर](ARCHITECTURE.md) · [डेव्हलपमेंट](docs/DEVELOPMENT.md) | हे आतून कसे काम करते; सोर्समधून चालवणे |
| [टेलिमेट्री](docs/TELEMETRY.md) | निनावी इन्स्टॉल आणि डेस्कटॉप-ओपन पिंग्स, आणि त्या कशा बंद करायच्या |

## स्क्रीनशॉट्स

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: टोकन्स, सेशन्स, हेल्थ | **Brain**: लाइव्ह एजंट इव्हेंट स्ट्रीम |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **Cost**: मॉडेल आणि सेशननुसार | **Approvals**: जोखमीचे टूल कॉल्स गेट करा |

अधिक, प्रत्येक रनटाइमनुसार: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## स्टार हिस्ट्री

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## परवाना

MIT · तयार केले [@vivekchand](https://github.com/vivekchand) यांनी · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
