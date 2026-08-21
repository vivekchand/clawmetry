<!-- i18n-src:dc34072b2955 -->
> मराठी translation of [README](../../../README.md), auto-generated from the English source. English is canonical; open a PR against `README.md` for content changes.

# 🦞 ClawMetry

[![PyPI version](https://img.shields.io/pypi/v/clawmetry?color=E5443A&label=version)](https://pypi.org/project/clawmetry/)
[![PyPI Downloads](https://static.pepy.tech/badge/clawmetry)](https://clickpy.clickhouse.com/dashboard/clawmetry)
[![GitHub stars](https://img.shields.io/github/stars/vivekchand/clawmetry?style=flat&color=E5443A)](https://github.com/vivekchand/clawmetry/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<a href="https://www.producthunt.com/products/clawmetry?embed=true&utm_source=badge-top-post-badge&utm_medium=badge&utm_campaign=badge-clawmetry-for-openclaw" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/top-post-badge.svg?post_id=1081207&theme=light&period=daily&t=1771491508782" alt="ClawMetry - #5 Product of the Day on Product Hunt" width="250" height="54" /></a>

**तुमचा एजंट विचार करताना पहा.** **२३ AI एजंट रनटाइम्ससाठी** रिअल-टाइम ऑब्झर्व्हेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी १९. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एकच कमांड. शून्य कॉन्फिगरेशन. सर्वकाही आपोआप शोधले जाते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** येथे उघडते. शून्य कॉन्फिगरेशन: तुमच्याकडे आधीपासून असलेले एजंट रनटाइम्स
ते शोधते, त्यांना फक्त वाचनासाठी (read-only) वाचते आणि ते कसे चालतात यात काहीही बदल करत नाही.

![Flow Visualization](https://clawmetry.com/screenshots/flow.png)

## २३ एजंट रनटाइम्ससोबत काम करते

**ओपन सोर्स अ‍ॅपमध्ये मोफत:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)**

**पेड प्लॅनवर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · **[Aider](https://clawmetry.com/runtimes/aider)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · **[Grok](https://clawmetry.com/runtimes/grok)** · **[QM](https://clawmetry.com/runtimes/qm)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)**

प्रत्येक रनटाइमला तोच डॅशबोर्ड मिळतो. एकाच वेळी अनेक रनटाइम्स चालवा आणि हेडर
स्विचर प्रत्येक टॅबला त्यापैकी एकावर पुन्हा-स्कोप करतो.

एखाद्या SDK वर स्वतःचा एजंट तयार केला आहे? इंटरसेप्टर त्याच्या LLM कॉल्सचाही मागोवा घेतो.
पाहा [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## तुम्हाला काय मिळते

- **सेशन्स आणि ट्रान्सक्रिप्ट्स**: प्रत्येक एजंटने काय केले, टर्न-बाय-टर्न, रिप्लेसह
- **खर्च आणि टोकन्स**: प्रत्येक रनटाइम, मॉडेल, सेशन आणि दिवसानुसार, विसंगती (anomaly) फ्लॅग्ससह
- **फ्लो**: चॅनेल्स, मॉडेल्स आणि टूल्समधून फिरणाऱ्या मेसेजेसचा लाइव्ह आकृती
- **ब्रेन**: घडत असताना रिझनिंग आणि टूल-कॉल इव्हेंट स्ट्रीम
- **मेमरी आणि स्किल्स**: प्रत्येक रनटाइमने प्रत्यक्षात लोड केलेल्या फाइल्स आणि स्किल्स
- **आरोग्य आणि लॉग्स**: डिस्क, मेमरी, एरर रेट्स, रेट लिमिट्स, लाइव्ह लॉग स्ट्रीम
- **अलर्ट्स**: बजेट कॅप्स, एरर स्पाइक्स, एजंट-ऑफलाइन, Slack, Discord, PagerDuty, Telegram, Email कडे रूट केलेले
- **मंजुऱ्या (Approvals)**: जोखमीचे टूल कॉल्स चालण्यापूर्वीच थांबवा आणि तुमच्या फोनवरून मंजूर करा ([कसे](docs/APPROVALS.md))

## किंमत

| प्लॅन | यात काय समाविष्ट आहे | किंमत |
|---|---|---|
| **Free** | OpenClaw + NVIDIA NemoClaw, संपूर्ण डॅशबोर्ड, फक्त लोकल | $0 |
| **Starter** | वरील इतर सर्व रनटाइम्स, फ्लीट व्ह्यू, क्लाउड सिंक | $9 प्रति नोड / महिना |
| **Pro** | Starter + गव्हर्नन्स: मंजुऱ्या, टूल-रिस्क धोरणे, इव्हॅल्स, अ‍ॅनोमली डिटेक्शन, कॉस्ट ऑप्टिमायझर, OTel एक्सपोर्ट | $19 प्रति नोड / महिना |

वार्षिक प्लॅन्स, एंटरप्राइझ आणि सध्याचे आकडे इथे आहेत
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. सेल्फ-होस्टेड लायसन्स
की क्लाउडशिवाय काम करतात (`clawmetry license`). नेमकी फ्री/पेड विभागणी
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) मध्ये आहे.

## तुमचा डेटा तुमच्या मशीनवरच राहतो

ClawMetry लोकल सेशन फाइल्स आणि लॉग्स वाचते. तुम्ही `clawmetry connect` चालवल्याशिवाय
तुमच्या मशीनमधून काहीही बाहेर जात नाही. तेव्हाही स्नॅपशॉट एंड-टू-एंड एन्क्रिप्टेड असतो,
अशा की सह जी कधीही तुमच्या मशीनमधून बाहेर जात नाही आणि तुमच्या ब्राउझरमध्ये डिक्रिप्ट केली जाते.

## इन्स्टॉल करा

```bash
pip install clawmetry     # नंतर: clawmetry
```

किंवा एका-ओळीत: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux किंवा Windows वर Python 3.8+ आणि त्याच मशीनवर किमान एक एजंट रनटाइम
आवश्यक आहे. Docker सूचना: [docs/DOCKER.md](docs/DOCKER.md).

## दस्तऐवजीकरण

| | |
|---|---|
| [रनटाइम सुसंगतता](docs/compatibility.md) | प्रत्येक अ‍ॅडॉप्टर काय वाचतो आणि रनटाइम कसे जोडायचे |
| [Entitlements](docs/ENTITLEMENTS.md) | फ्री विरुद्ध पेड, टियर मॅट्रिक्स, लायसन्स CLI |
| [मंजुऱ्या आणि धोरणे](docs/APPROVALS.md) | प्री-एक्झिक्युशन गेटिंग, रिस्क स्कोअरिंग, फोन मंजुऱ्या |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | कुठेही ट्रेसेस एक्सपोर्ट करा, कोठूनही OTLP इनजेस्ट करा |
| [SDK ट्रॅकिंग](docs/SDK_TRACKING.md) | तुम्ही स्वतः तयार केलेल्या एजंट्ससाठी खर्चाचे श्रेय |
| [चॅट चॅनेल्स](docs/CHANNELS.md) | फ्लोमध्ये दाखवलेले चॅट अ‍ॅडॉप्टर्स |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सँडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज, व्हॉल्यूम माउंट्स |
| [आर्किटेक्चर](ARCHITECTURE.md) · [डेव्हलपमेंट](docs/DEVELOPMENT.md) | आतून हे कसे काम करते; सोर्समधून चालवणे |
| [टेलिमेट्री](docs/TELEMETRY.md) | निनावी इन्स्टॉल आणि डेस्कटॉप-ओपन पिंग्स, आणि त्या कशा बंद करायच्या |

## स्क्रीनशॉट्स

| | |
|---|---|
| ![Overview tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png) | ![Brain tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/brain.png) |
| **Overview**: टोकन्स, सेशन्स, आरोग्य | **Brain**: लाइव्ह एजंट इव्हेंट स्ट्रीम |
| ![Tokens tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/tokens.png) | ![Approvals tab](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png) |
| **खर्च**: मॉडेल आणि सेशननुसार | **मंजुऱ्या**: जोखमीचे टूल कॉल्स गेट करा |

रनटाइमनुसार अधिक: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## Star History

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## License

MIT · निर्मिती [@vivekchand](https://github.com/vivekchand) यांनी · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
