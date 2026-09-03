<!-- i18n-src:9767c8001c9c -->
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

**तुमचा एजंट कसा विचार करतो ते पहा.** **३० AI एजंट रनटाइम्ससाठी** रिअल-टाइम ऑब्झर्वेबिलिटी: [OpenClaw](https://github.com/openclaw/openclaw), [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), Claude Code, OpenAI Codex आणि आणखी २६. तुमच्या संपूर्ण एजंट फ्लीटसाठी एकच डॅशबोर्ड.

> 🌐 **हे यामध्ये वाचा:** [English](README.md) · [简体中文](docs/i18n/zh-CN/README.md) · [日本語](docs/i18n/ja/README.md) · [한국어](docs/i18n/ko/README.md) · [Español](docs/i18n/es/README.md) · [Português (BR)](docs/i18n/pt-BR/README.md) · [Français](docs/i18n/fr/README.md) · [Deutsch](docs/i18n/de/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [العربية](docs/i18n/ar/README.md) · [Русский](docs/i18n/ru/README.md) · [अधिक →](docs/i18n/)

एक कमांड. शून्य कॉन्फिगरेशन. सर्वकाही आपोआप शोधले जाते.

```bash
pip install clawmetry && clawmetry
```

**http://localhost:8900** वर उघडते. शून्य कॉन्फिगरेशन: तुमच्याकडे आधीपासून असलेले एजंट रनटाइम्स ते शोधते,
ते फक्त-वाचनासाठी (read-only) वाचते, आणि ते कसे चालतात यामध्ये काहीही बदलत नाही.

![ClawMetry dashboard: every AI agent runtime on one machine with 24h and lifetime cost per agent](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/hero.png)

## ३० एजंट रनटाइम्ससोबत काम करते

**ओपन सोर्स अ‍ॅपमध्ये मोफत:** 🦞 **[OpenClaw](https://clawmetry.com/runtimes/openclaw)** · 🟩 **[NVIDIA NemoClaw](https://clawmetry.com/nemoclaw)** · 🪿 **[Goose](https://clawmetry.com/runtimes/goose)**

**सशुल्क योजनेवर:** ◆ **[Claude Code](https://clawmetry.com/runtimes/claude-code)** · **[Cursor](https://clawmetry.com/runtimes/cursor)** · 🐙 **[GitHub Copilot](https://clawmetry.com/runtimes/copilot)** · ⬡ **[OpenAI Codex](https://clawmetry.com/runtimes/codex)** · ♊ **[Gemini CLI](https://clawmetry.com/runtimes/gemini-cli)** · 💗 **[Lovable](https://clawmetry.com/runtimes/lovable)** · ⠕ **[Replit Agent](https://clawmetry.com/runtimes/replit)** · 🖇 **[Cline](https://clawmetry.com/runtimes/cline)** · 🙌 **[OpenHands](https://clawmetry.com/runtimes/openhands)** · 🧑‍💼 **[OpenWorker](https://clawmetry.com/runtimes/openworker)** · **[opencode](https://clawmetry.com/runtimes/opencode)** · **[Aider](https://clawmetry.com/runtimes/aider)** · 🔗 **[n8n](https://clawmetry.com/runtimes/n8n)** · ◈ **[Qwen Code](https://clawmetry.com/runtimes/qwen-code)** · 🅳 **[Devin](https://clawmetry.com/runtimes/devin)** · 🪐 **[Antigravity](https://clawmetry.com/runtimes/antigravity)** · **[Grok Build](https://clawmetry.com/runtimes/grok)** · 🤖 **[Grok Bot](https://clawmetry.com/runtimes/grok-bot)** · ⚡ **[Hermes](https://clawmetry.com/runtimes/hermes)** · **[Pi](https://clawmetry.com/runtimes/pi)** · **[Deep Agents](https://clawmetry.com/runtimes/deep-agents)** · 🌙 **[Kimi CLI](https://clawmetry.com/runtimes/kimi)** · 🐋 **[DeepSeek Harness](https://clawmetry.com/runtimes/deepseek-harness)** · 🦾 **[Exo](https://clawmetry.com/runtimes/exo)** · **[NanoClaw](https://clawmetry.com/runtimes/nanoclaw)** · **[PicoClaw](https://clawmetry.com/runtimes/picoclaw)** · **[QM](https://clawmetry.com/runtimes/qm)**

प्रत्येक रनटाइमला तोच डॅशबोर्ड मिळतो. एकाच वेळी अनेक चालवा आणि हेडरमधील स्विचर
प्रत्येक टॅबला त्यांपैकी एकावर पुन्हा-केंद्रित करतो.

तुमचा स्वतःचा एजंट एखाद्या SDK वर तयार केला आहे? इंटरसेप्टर त्याचे LLM कॉल्सदेखील ट्रॅक करतो.
पहा [docs/SDK_TRACKING.md](docs/SDK_TRACKING.md).

## तुम्हाला काय मिळते

- **सेशन्स आणि ट्रान्सक्रिप्ट्स**: प्रत्येक एजंटने काय केले, टप्प्याटप्प्याने, रिप्लेसह
- **खर्च आणि टोकन्स**: रनटाइम, मॉडेल, सेशन आणि दिवसानुसार, विसंगती (anomaly) फ्लॅग्जसह
- **फ्लो**: चॅनेल्स, मॉडेल्स आणि टूल्समधून जाणाऱ्या संदेशांचा लाइव्ह डायग्राम
- **ब्रेन**: घडताक्षणी तर्कशक्ती आणि टूल-कॉल इव्हेंट स्ट्रीम
- **कॉन्टेक्स्ट ब्लोआउट**: प्रत्येक प्रोव्हायडरनुसार विंडो आकारमान, कॉम्पॅक्शन विरुद्ध सक्तीचा ओव्हरफ्लो, तसेच आपण काय *पाहू शकत नाही* याचा प्रत्येक रनटाइमनुसार नकाशा ([कसे](docs/CONTEXT_BLOWOUT.md))
- **मेमरी आणि स्किल्स**: प्रत्येक रनटाइमने प्रत्यक्षात लोड केलेल्या फाइल्स आणि स्किल्स
- **आरोग्य आणि लॉग्स**: डिस्क, मेमरी, त्रुटी दर, रेट लिमिट्स, लाइव्ह लॉग स्ट्रीम
- **अलर्ट्स**: बजेट मर्यादा, त्रुटी वाढ, एजंट-ऑफलाइन, Slack, Discord, PagerDuty, Telegram, Email कडे पाठवले जातात
- **मंजुऱ्या (Approvals)**: जोखमीचे टूल कॉल्स *चालण्याआधी* थांबवा आणि तुमच्या फोनवरून मंजूर करा ([कसे](docs/APPROVALS.md))

## कॉन्टेक्स्ट ब्लोआउट, आणि निरीक्षणाचा खर्च किती

कोणतेही एजंट-तुलना साधन विश्वास ठेवण्याआधी उत्तर देण्यायोग्य असे दोन प्रश्न.

**ते रनटाइम्समध्ये कॉन्टेक्स्ट-विंडो ब्लोआउट कसे हाताळते?**

उपयोगिता टक्केवारी ती ज्याने भागली जाते तितकीच प्रामाणिक असते. ClawMetry प्रत्येक
प्रोव्हायडरनुसार विंडोचा आकार [तुम्ही वाचू आणि PR करू शकता अशा एका टेबलमधून](clawmetry/context_windows.py)
ठरवते, ज्यामध्ये Anthropic, OpenAI, Google, xAI, DeepSeek, Kimi, Qwen, Mistral, Llama
आणि GLM यांचा समावेश आहे. ते सर्व २६ रनटाइम्सना एका विक्रेत्याच्या मोजपट्टीने मोजत नाही.
हे महत्त्वाचे आहे: Anthropic च्या 200K विरुद्ध मोजलेला 300K GPT-5 चा एक टर्न ">100%,
ब्लोन" वाचतो जेव्हा तो प्रत्यक्षात GPT-5 च्या 400K पैकी 75% असतो. तीच मोजपट्टी खरोखर
ओव्हरफ्लो झालेल्या 130K DeepSeek टर्नला आरामदायक 65% म्हणून लपवते.

प्रत्येक विंडो तिच्या स्रोतासह (provenance) येते: `model_table`, `explicit_marker`,
`observed_floor`, किंवा मॉडेल माहीत नसताना प्रामाणिक `default`. अंदाजावर बांधलेला गेज
कधीही लूकअपवर बांधलेल्या गेजइतक्याच अधिकाराने रेंडर होत नाही.

ClawMetry काही रनटाइम्सवरच कॉम्पॅक्शन इव्हेंट्स पाहू शकते. त्यामुळे `GET /api/context-coverage`
प्रत्येक रनटाइमसाठी अहवाल देतो की **शून्य म्हणजे "स्वच्छपणे चालले" की "आपण आंधळे आहोत"**.
जो `0` खरोखर आंधळेपणा दर्शवतो तो तसे सांगतो. [संपूर्ण तपशील](docs/CONTEXT_BLOWOUT.md)

**इन्स्ट्रुमेंटेशनचा खर्च किती?**

| मार्ग | तुमच्या एजंटला जोडले जाणारे | डीफॉल्ट? |
|---|---|---|
| सेशन-फाइल टेलिंग (सर्व ३० रनटाइम्स) | **०**. वेगळी प्रक्रिया, तुमच्या एजंटमध्ये ClawMetry चा कोड नाही | चालू |
| HTTP इंटरसेप्टर (`CLAWMETRY_INTERCEPT=1`) | प्रत्येक LLM कॉलला **+0.44 ms**, म्हणजे 5s कॉलच्या 0.009% | बंद |
| प्री-टूल हुक गेट (वॉर्म कॅशे) | 36 ms च्या इंटरप्रिटर फ्लोअरवर, प्रत्येक गेट केलेल्या टूल कॉलला **+44 ms** | बंद |
| एन्फोर्समेंट प्रॉक्सी | प्रत्येक LLM कॉलला **+9.7 ms** | बंद |

डीमन होस्ट खर्च: **2,762 इव्हेंट्स/सेकंद** इनजेस्ट, डिस्कवर **710 बाइट्स/इव्हेंट**
(100k इव्हेंट्ससाठी 67.7 MB), आणि व्यस्त इन्स्टॉलवर सतत **एका कोरच्या ~12%**. तो शेवटचा
आकडा आमच्याच नमूद केलेल्या 5-10% बजेटपेक्षा जास्त आहे, त्यामुळे पानावरून वगळण्याऐवजी
मागे लागायच्या बगप्रमाणे प्रकाशित केला आहे.

Apple M2 Pro वर `benchmarks/overhead.py` वापरून मोजले आहे. हार्नेस प्रत्येक स्थिती वेगळ्या
प्रोसेसमध्ये चालवतो, त्यांचा क्रम बदलत राहतो, आणि **फेऱ्यांचे चिन्ह (sign) जुळत नसेल तर
आकडा छापण्यास नकार देतो**. एका मिनिटात तुमच्या स्वतःच्या मशीनवर चालवा:

```bash
pip install clawmetry && python -m benchmarks.overhead
```

हुक गेट्स आणि एन्फोर्समेंट प्रॉक्सीसह प्रत्येक मार्ग मोजला जातो, आणि हार्नेस CI मध्ये Linux,
macOS आणि Windows वर चालतो. जाणून घेण्यासारखे दोन निकाल: प्रॉक्सीचा खर्च Windows वर
Linux पेक्षा साधारण सातपट जास्त आहे, आणि डीमन सध्या एका कोरच्या सुमारे 12% सतत वापरतो,
जे आमच्याच 5-10% बजेटपेक्षा जास्त आहे. कच्चा JSON, पद्धत, आणि अजून काय मोजलेले नाही ते
[docs/OVERHEAD.md](docs/OVERHEAD.md) मध्ये आहे.

## किंमत

| योजना | काय समाविष्ट आहे | किंमत |
|---|---|---|
| **मोफत** | OpenClaw + NVIDIA NemoClaw + Goose, संपूर्ण डॅशबोर्ड, फक्त स्थानिक | $0 |
| **स्टार्टर** | वरील इतर सर्व रनटाइम्स, फ्लीट व्ह्यू, क्लाउड सिंक | दरमहा प्रति नोड $9 |
| **Pro** | स्टार्टर + नियंत्रण आणि मूल्यमापन: मंजुऱ्या, टूल-जोखीम धोरणे, इव्हॅल्स, विसंगती शोध, कॉस्ट ऑप्टिमायझर, OTel एक्सपोर्ट, छेडछाड-सिद्ध ऑडिट लॉग | दरमहा प्रति नोड $19 |

वार्षिक योजना, एंटरप्राइझ आणि सद्य आकडे येथे आहेत
**[clawmetry.com/pricing](https://clawmetry.com/pricing)**. सेल्फ-होस्टेड लायसन्स की क्लाउडशिवाय
काम करतात (`clawmetry license`). नेमके मोफत/सशुल्क विभाजन
[docs/ENTITLEMENTS.md](docs/ENTITLEMENTS.md) मध्ये आहे.

## तुमचा डेटा तुमच्याच मशीनवर राहतो

ClawMetry स्थानिक सेशन फाइल्स आणि लॉग्स वाचतो. **तुम्ही `clawmetry connect` चालवल्याशिवाय
कोणताही सेशन डेटा तुमच्या बॉक्सबाहेर जात नाही** — कोणतेही प्रॉम्प्ट्स, उत्तरे, टूल आर्ग्युमेंट्स,
फाइल कंटेंट किंवा लॉग लाइन्स नाहीत. जेव्हा तुम्ही कनेक्ट करता, तेव्हा स्नॅपशॉट तुमच्या मशीनवरून
कधीही न जाणाऱ्या कीने एंड-टू-एंड एन्क्रिप्ट केलेला असतो, आणि तुमच्या ब्राउझरमध्ये डिक्रिप्ट होतो.
जर एखाद्या नोडकडे की नसेल, तर अपलोड उघड्यावर पाठवण्याऐवजी वगळला जातो, आणि कोणताही
सर्व्हर प्रतिसाद ते बंद करू शकत नाही.

कनेक्ट करण्याआधी डीफॉल्टनुसार दोन गोष्टी चालतात, दोन्ही ऑप्ट-आउट करण्यायोग्य आणि दोन्हीमध्ये
सेशन डेटा नसतो: एक अनामिक इन्स्टॉल पिंग आणि PyPI विरुद्ध व्हर्जन तपासणी. डीफॉल्ट इन्स्टॉल
स्टार्टअप बॅनर लाइनसाठी तुमचा सार्वजनिक IP एकदा शोधतो. प्रत्येक गंतव्यस्थान, ते काय वाहून
नेते आणि ते कसे बंद करायचे याची यादी [docs/EGRESS.md](docs/EGRESS.md) मध्ये आहे; सेल्फ-होस्टेड,
पुनर्निर्देशित आणि एअर-गॅप्ड इन्स्टॉल्स कोणतेही विवेकाधीन आउटबाउंड कॉल्स करत नाहीत.

डिक्रिप्शन तुमच्या ब्राउझरमध्ये होते, आम्ही तुम्हाला दिलेल्या कोडमध्ये. आधी हे एक वचन होते;
आता ते तुम्ही तपासू शकता असे काहीतरी आहे. तुमच्या कीला स्पर्श करणारी प्रत्येक ओळ एका
वाचनीय फाइलमध्ये आहे, [`clawmetry/static/js/cm-e2e.js`](clawmetry/static/js/cm-e2e.js),
जी व्हीलच्या आत येते आणि जशीच्या तशी दिली जाते, Subresource Integrity हॅशने पिन केलेली.
ब्राउझर आम्ही प्रकाशित केलेलेच चालवतो याची खात्री करण्यासाठी:

```bash
curl -s https://app.clawmetry.com/static/js/cm-e2e.js -o served.js
pip download --no-deps clawmetry==$(clawmetry --version | tr -d 'a-z ') -d /tmp/cm
unzip -p /tmp/cm/clawmetry-*.whl clawmetry/static/js/cm-e2e.js > published.js
diff served.js published.js && echo identical
```

हे काय सिद्ध करत नाही: ती फाइल लोड करणारे पान आम्हीच देतो, त्यामुळे आम्ही वेगळे पान देऊ
शकतो. इंटिग्रिटी हॅश तुम्हाला तडजोड झालेल्या CDN पासून वाचवतात, विक्रेत्यापासून नाही. तुम्हाला
जे मिळते ते म्हणजे कोणतीही बदली मुद्दाम केलेली, पानाच्या स्रोतात दिसणारी, आणि PyPI वर कोणीही
मिळवू शकेल अशा आर्टिफॅक्टपेक्षा वेगळी असावी लागते. सेल्फ-होस्टिंग किंवा फक्त-स्थानिक राहिल्याने
ही निर्भरता पूर्णपणे नाहीशी होते.

## इन्स्टॉल

```bash
pip install clawmetry     # नंतर: clawmetry
```

किंवा वन-लाइनर: `curl -sSL https://raw.githubusercontent.com/vivekchand/clawmetry/main/install.sh | bash`

macOS, Linux किंवा Windows वर Python 3.8+ आवश्यक आहे, आणि त्याच मशीनवर किमान एक एजंट
रनटाइम असणे आवश्यक आहे. Docker सूचना: [docs/DOCKER.md](docs/DOCKER.md).

## कागदपत्रे (Docs)

| | |
|---|---|
| [Runtime compatibility](docs/compatibility.md) | प्रत्येक अ‍ॅडॅप्टर काय वाचतो, आणि रनटाइम कसा जोडायचा |
| [Context blowout](docs/CONTEXT_BLOWOUT.md) | प्रोव्हायडरनुसार विंडोज, कॉम्पॅक्शन विरुद्ध ओव्हरफ्लो, प्रत्येक रनटाइमनुसार कव्हरेज |
| [Overhead](docs/OVERHEAD.md) | इन्स्ट्रुमेंटेशनचा खर्च किती, मोजलेला, तो पुन्हा तयार करण्याच्या हार्नेससह |
| [Entitlements](docs/ENTITLEMENTS.md) | मोफत विरुद्ध सशुल्क, टियर मॅट्रिक्स, लायसन्स CLI |
| [Approvals & policies](docs/APPROVALS.md) | पूर्व-अंमलबजावणी गेटिंग, जोखीम स्कोअरिंग, फोन मंजुऱ्या |
| [OpenTelemetry](docs/OPENTELEMETRY.md) | ट्रेसेस कुठेही एक्सपोर्ट करा, कुठूनही OTLP इनजेस्ट करा |
| [Bring your own agent](docs/BRING_YOUR_OWN_AGENT.md) | AWS AgentCore, Pydantic AI, LangChain सुरुवातीपासून शेवटपर्यंत, चालवता येण्याजोग्या उदाहरणांसह |
| [SDK tracking](docs/SDK_TRACKING.md) | तुम्ही स्वतः तयार केलेल्या एजंट्ससाठी खर्चाचे श्रेय (attribution) |
| [Chat channels](docs/CHANNELS.md) | फ्लोमध्ये दाखवलेले चॅट अ‍ॅडॅप्टर्स |
| [NemoClaw / OpenShell](docs/NEMOCLAW.md) | सँडबॉक्स्ड NVIDIA NemoClaw सेटअप्स |
| [Docker](docs/DOCKER.md) | इमेज, कंपोज, व्हॉल्यूम माउंट्स |
| [Architecture](ARCHITECTURE.md) · [Development](docs/DEVELOPMENT.md) | आतून हे कसे काम करते; स्रोतापासून चालवणे |
| [Telemetry](docs/TELEMETRY.md) | अनामिक इन्स्टॉल आणि डेस्कटॉप-ओपन पिंग्ज, आणि त्या कशा बंद करायच्या |

## स्क्रीनशॉट्स

खालील प्रत्येक आकडा एका खऱ्या मशीनवरून आहे, फक्त-वाचनासाठी, काहीही आधी भरलेले (seeded) नाही.

**काहीतरी चुकीचे असल्यास ते तुम्हाला सांगते, फक्त काय घडले तेच नाही.**
वर दोन अ‍ॅनोमली बॅनर्स: रोजच्या सरासरीच्या 7 पट खर्च चालू आहे, आणि 4.2 पट कॉस्ट स्पाइक.
त्याखाली, अलीकडील 667 पैकी 324 सेशन्समध्ये कारणानुसार सूचीबद्ध केलेला वेस्ट सिग्नल आहे.

![Overview: spending anomaly and cost spike banners over live agent work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/overview.png)

**पैसे कुठे गेले ते प्रत्येक विंडोमध्ये दाखवते.**
आज $252.47, या आठवड्यात $513.15, या महिन्यात $1,312.92, प्रत्येकामागील टोकन्ससह आणि
तुमची सबस्क्रिप्शन त्यातील किती आधीच कव्हर करते. त्याखाली, सुमारे $1,128/महिना पुनर्प्राप्त
करण्यायोग्य म्हणून सूचीबद्ध आणि कॅशे पुनर्वापरामुळे आधीच वाचलेले $17,256/महिना.

![Cost: today, this week and this month, with an efficiency grade and itemised savings ideas](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/cost.png)

**संदेशाचे उत्तरात कसे रूपांतर होते हे रेखाटते.**
लाइव्ह फ्लो डायग्राम: तुम्ही, तो ज्या चॅनेलवर आला, गेटवे, आत्ता उत्तर देणारा मॉडेल, आणि
त्याने वापरलेले प्रत्येक टूल. काम त्यांच्यामधून जाताना नोड्स उजळतात.

![Flow: live diagram from you through the gateway to the model and its tools](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/flow.png)

**मशीनवरील प्रत्येक एजंट, एका टेबलमध्ये.**
ते काय चालवते, गेल्या 24 तासांत आणि आयुष्यभरात त्याचा खर्च किती, शेवटचे कधी दिसले,
त्याचा मालक कोण, आणि सबस्क्रिप्शन बिल कव्हर करत आहे का. येथे 14 एजंट्स, 3 सेशन्स काम
करत आहेत, 13 शांत आहेत.

![Agents: every runtime on the machine with cost, owner, last seen and current work](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/agents.png)

**एका टर्नचा वेळ आणि पैसा कुठे गेला हे टूल-दर-टूल दाखवते.**
एका खऱ्या सेशनचा एक टर्न: $1.16 मध्ये 11.2 मिनिटांत 11 टूल्स. प्रत्येक Bash कॉल आणि मॉडेल
कॉलला टाइमलाइनवर स्वतःचा बार मिळतो, त्यामुळे 4.1 मिनिटे चाललेली कमांड आणि 226ms चाललेली
कमांड एका दृष्टिक्षेपात वेगळ्या ओळखता येतात.

![Sessions: one agent turn on a timeline, every tool call with its own duration and the turn's cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/sessions.png)

**काम गुणवत्तेनुसार तपासते, फक्त खर्चानुसार नाही.**
या आठवड्यात A: 54 कामे स्वच्छपणे पूर्ण झाली, 2 खडबडीत कामांचा खर्च $48.57 झाला, आणि
न्याय करण्यासाठी खूप कमी हालचाल असलेली रन्स विजय म्हणून मोजण्याऐवजी ग्रेडमधून वगळली आहेत.
प्रत्येक खडबडीत रन तिच्या ट्रेसला जोडलेली आहे.

![Quality: this week's report card with the rough runs and what they cost](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/quality.png)

**कॉन्टेक्स्ट विंडो का भरत राहते हे दाखवते.**
1M-टोकन विंडोपैकी 715K शेवटच्या टर्नवर, 83.3% शिखर, 4 कॉम्पॅक्शन्स जी सर्व ओव्हरफ्लोवर
न होता सक्रियपणे (proactively) घडली, तसेच त्यामागील प्रत्येक टर्नची उपयोगिता.

![Context usage: window utilisation per turn, compaction events and tokens reclaimed](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/context.png)

**तुम्ही काहीही कॉन्फिगर न करता शोध (detection) चालते.**
अंगभूत डिटेक्टर्स इन्स्टॉलपासूनच चालू आहेत: एजंट शांत झाला, टेलिमेट्री फीड थांबला, कॉस्ट
स्पाइक, टोकन बर्स्ट, त्रुटी वाढत आहेत, त्रुटी स्पाइक, बजेट थ्रेशोल्ड, थ्रेट सिग्नेचर जुळले,
सिक्युरिटी टूल फाइंडिंग, सिक्युरिटी पोश्चर बदलले. वर तुमचे स्वतःचे नियम ऐच्छिक आहेत.

![Alerts: built-in detectors plus optional custom rules](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/alerts.png)

**जोखमीचा कॉल थांबवणे ऐच्छिक आहे, आणि बंद अवस्थेत रिलीज होते.**
रिकर्सिव्ह डिलीट्स, फोर्स पुश, sudo, सीक्रेट्स, पॅकेज इन्स्टॉल्स आणि आउटबाउंड कॉल्स
यांपैकी प्रत्येकासाठी तुम्ही चालू करू शकता असा नियम आहे. तुम्ही तो चालू करेपर्यंत, ClawMetry
फक्त पाहते आणि काहीही बदलत नाही. एकदा तो चालू केला की, जुळणारे कॉल्स इथे (किंवा
तुमच्या फोनवर) मंजुरी किंवा नकारासाठी थांबतात.

![Approvals: protection rules for risky tool calls, all off until you enable them](https://raw.githubusercontent.com/vivekchand/clawmetry/main/screenshots/approvals.png)

अधिक, प्रत्येक रनटाइमनुसार: [docs/RUNTIME_SCREENSHOTS.md](docs/RUNTIME_SCREENSHOTS.md).

## स्टार इतिहास (Star History)

<a href="https://www.star-history.com/?repos=vivekchand%2Fclawmetry&type=date&legend=top-left">
 <picture>
 <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&theme=dark&legend=top-left" />
 <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 <img alt="Star History Chart" src="https://api.star-history.com/image?repos=vivekchand/clawmetry&type=date&legend=top-left" />
 </picture>
</a>

## परवाना (License)

MIT · निर्मिती [@vivekchand](https://github.com/vivekchand) यांनी · [clawmetry.com](https://clawmetry.com)

<!-- osai-verify: f3ac716d40002c1ad6dd -->
